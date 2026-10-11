#!/usr/bin/env bash
# Vendored auto-install hook (D-05: vendored copy per plugin, not shared at
# runtime).
#
# Detects bundle drift via a whole-directory hash and re-grants the
# capability at global ("user") scope on every SessionStart (D-01..D-03).
# Never aborts the session: no `set -e`.
set -u

# `--consent <id>` is the command the hook prints when gsd-core requires
# consent: the same flow under the same lock, with the user's --yes.
HOOK_ARGS=("$@")
CONSENT=0
if [ "${1:-}" = --consent ]; then
  CONSENT=1
  shift
fi
CAP_ID="${1:-}"

# Defense in depth (ASVS V5): call sites only ever pass a hard-coded literal,
# but validate the id shape gsd-core itself enforces before it reaches any
# path construction.
[[ "$CAP_ID" =~ ^[a-z][a-z0-9-]*$ ]] || exit 0

# Resolved physical path: ownership below is a prefix test, so a cache-path
# symlink into an arbitrary tree must not inherit the cache's trust. An
# unresolvable root is empty and stops here, never becoming "/capability.json".
PLUGIN_ROOT="$(cd -P "${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}" 2>/dev/null && pwd -P)"
[ -n "$PLUGIN_ROOT" ] || exit 0
# The plugin root is the capability root (root-manifest layout), but it also
# carries dev-only content (tests/, .git, caches). Only an allowlist is ever
# hashed or installed; it is staged below, once the transaction lock is held.
[ -f "$PLUGIN_ROOT/capability.json" ] || exit 0
BUNDLE_ALLOWLIST=(capability.json scripts skills fragments GSD-CORE-PATCH.md)

# Hash an explicitly bounded tree as type-tagged, length-prefixed relative
# paths plus file bytes. Relative framing avoids absolute-root drift and
# concatenation collisions.
canonical_tree_hash() {
  python3 -I - "$@" 9>&- 2>/dev/null <<'PY'
import hashlib
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
requested = sys.argv[2:] or ["."]
entries = {}
try:
    for requested_name in requested:
        start = root / requested_name
        if not start.exists() or start.is_symlink():
            raise ValueError
        candidates = [start]
        if start.is_dir():
            candidates.extend(start.rglob("*"))
        for path in candidates:
            if path.is_symlink() or not (path.is_dir() or path.is_file()):
                raise ValueError
            relative = path.relative_to(root).as_posix()
            entries[relative] = path
except (OSError, ValueError):
    raise SystemExit(1)

digest = hashlib.sha256()
try:
    for relative in sorted(entries):
        path = entries[relative]
        name = os.fsencode(relative)
        kind = b"d" if path.is_dir() else b"f"
        digest.update(kind + len(name).to_bytes(8, "big") + name)
        if kind == b"f":
            data = path.read_bytes()
            digest.update(len(data).to_bytes(8, "big") + data)
except OSError:
    raise SystemExit(1)
print(digest.hexdigest())
PY
}

STATE_VERSION="projection-v2"

# Every root below decides where machine-wide state lands; a relative one
# would resolve inside whatever repo the session opened in.
for _root_var in HOME GSD_HOME CODEX_HOME CLAUDE_CONFIG_DIR; do
  _root_value="${!_root_var:-}"
  if [ "$_root_var" = HOME ] || [ -n "$_root_value" ]; then
    case "$_root_value" in
      /?*) ;;
      *)
        echo "capability-auto-install: $_root_var must be absolute for $CAP_ID; projection not recorded" >&2
        exit 0
        ;;
    esac
  fi
done

# Reconcile only the runtime that loaded this plugin: the installed plugin
# cache must identify exactly one owner. GSD_RUNTIME may only confirm that
# owner, never replace it, so a --plugin-dir working tree never installs.
CODEX_CONFIG_ROOT="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_CONFIG_ROOT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CODEX_OWNER=0
CLAUDE_OWNER=0
_codex_physical="$(cd -P "$CODEX_CONFIG_ROOT" 2>/dev/null && pwd -P)"
_claude_physical="$(cd -P "$CLAUDE_CONFIG_ROOT" 2>/dev/null && pwd -P)"
[ -n "$_codex_physical" ] && [[ "$PLUGIN_ROOT/" == "$_codex_physical"/plugins/* ]] && CODEX_OWNER=1
[ -n "$_claude_physical" ] && [[ "$PLUGIN_ROOT/" == "$_claude_physical"/plugins/* ]] && CLAUDE_OWNER=1
ACTIVE_RUNTIME=""
if [ "$CODEX_OWNER" -eq 1 ] && [ "$CLAUDE_OWNER" -eq 0 ]; then
  ACTIVE_RUNTIME="codex"
elif [ "$CODEX_OWNER" -eq 0 ] && [ "$CLAUDE_OWNER" -eq 1 ]; then
  ACTIVE_RUNTIME="claude"
fi
if [ -z "$ACTIVE_RUNTIME" ] || [ "${GSD_RUNTIME:-$ACTIVE_RUNTIME}" != "$ACTIVE_RUNTIME" ]; then
  echo "capability-auto-install: runtime selection failed for $CAP_ID; projection not recorded" >&2
  exit 0
fi

case "$ACTIVE_RUNTIME" in
  codex)
    RUNTIME_CONFIG_DIR="$CODEX_CONFIG_ROOT"
    EXPECTED_SKILLS_ROOT="$HOME/.agents/skills"
    ;;
  claude)
    RUNTIME_CONFIG_DIR="$CLAUDE_CONFIG_ROOT"
    EXPECTED_SKILLS_ROOT="$CLAUDE_CONFIG_ROOT/skills"
    ;;
esac

# Use only the selected runtime's public CLI and skills-root query. This avoids
# accidentally projecting through a repository checkout, PATH shim, or sibling
# runtime installation.
GSD_TOOLS="$RUNTIME_CONFIG_DIR/gsd-core/bin/gsd-tools.cjs"
if [ ! -x "$GSD_TOOLS" ]; then
  echo "capability-auto-install: gsd-tools resolution failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
fi

if [ -n "${GSD_AUTO_INSTALL_LOCK_FD:-}" ]; then
  SKILLS_ROOT="${GSD_AUTO_INSTALL_SKILLS_ROOT:-}"
  SKILLS_ROOT_STATUS=0
else
  SKILLS_ROOT="$("$GSD_TOOLS" query skills-root "$ACTIVE_RUNTIME" --raw 2>/dev/null)"
  SKILLS_ROOT_STATUS=$?
fi
if [ "$SKILLS_ROOT_STATUS" -ne 0 ] || [ "$SKILLS_ROOT" != "$EXPECTED_SKILLS_ROOT" ]; then
  echo "capability-auto-install: skills-root query failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
fi

STATE_DIR="${GSD_HOME:-$HOME}/.gsd"
INSTALLED_BUNDLE="$STATE_DIR/capabilities/$CAP_ID"
LEDGER="$STATE_DIR/capability-auto-install-$CAP_ID.projections"
LEGACY_STATE_FILE="$STATE_DIR/capability-auto-install-$CAP_ID.hash"
LOCK_PATH="$LEDGER.lock"

mkdir -p "$STATE_DIR" 2>/dev/null || {
  echo "capability-auto-install: projection lock failed for $CAP_ID; projection not recorded" >&2
  exit 0
}

if [ -z "${GSD_AUTO_INSTALL_LOCK_FD:-}" ]; then
  python3 -I - "$LOCK_PATH" "$0" "$SKILLS_ROOT" "${HOOK_ARGS[@]}" 8>&2 2>/dev/null <<'PY'
import errno
import fcntl
import os
import stat
import sys
import time

lock_path, hook_path, skills_root, *hook_args = sys.argv[1:]
# Bounded wait: a concurrent session finishes its install before this one
# proceeds to bd prime, yet a wedged holder never stalls SessionStart past
# 30s. The override exists for tests and can only shorten the bound.
try:
    wait_seconds = min(30.0, max(0.0, float(os.environ.get("GSD_AUTO_INSTALL_LOCK_WAIT_SECONDS", "30"))))
except ValueError:
    wait_seconds = 30.0
try:
    flags = os.O_RDWR | os.O_CREAT | os.O_NONBLOCK | os.O_NOFOLLOW
except AttributeError:
    raise SystemExit(76)

try:
    fd = os.open(lock_path, flags, 0o600)
except OSError:
    raise SystemExit(76)

try:
    descriptor = os.fstat(fd)
    path_entry = os.stat(lock_path, follow_symlinks=False)
    valid = (
        stat.S_ISREG(descriptor.st_mode)
        and stat.S_ISREG(path_entry.st_mode)
        and descriptor.st_dev == path_entry.st_dev
        and descriptor.st_ino == path_entry.st_ino
        and descriptor.st_uid == os.geteuid()
        and descriptor.st_nlink == 1
    )
    if not valid:
        raise SystemExit(76)
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError as error:
            if error.errno not in (errno.EACCES, errno.EAGAIN):
                raise SystemExit(76)
            if time.monotonic() >= deadline:
                raise SystemExit(75)
        time.sleep(0.1)
    path_entry = os.stat(lock_path, follow_symlinks=False)
    if (
        not stat.S_ISREG(path_entry.st_mode)
        or descriptor.st_dev != path_entry.st_dev
        or descriptor.st_ino != path_entry.st_ino
    ):
        raise SystemExit(76)
    if fd != 9:
        os.dup2(fd, 9)
        os.close(fd)
    os.set_inheritable(9, True)
    environment = os.environ.copy()
    environment["GSD_AUTO_INSTALL_LOCK_FD"] = "9"
    environment["GSD_AUTO_INSTALL_SKILLS_ROOT"] = skills_root
    os.dup2(8, 2)
    os.close(8)
    os.execvpe("bash", ["bash", hook_path, *hook_args], environment)
except SystemExit:
    raise
except BaseException:
    raise SystemExit(76)
PY
  LOCK_STATUS=$?
  if [ "$LOCK_STATUS" -eq 75 ]; then
    echo "capability-auto-install: projection transaction busy for $CAP_ID; projection not recorded" >&2
  elif [ "$LOCK_STATUS" -ne 0 ]; then
    echo "capability-auto-install: projection lock failed for $CAP_ID; projection not recorded" >&2
  fi
  exit 0
fi

LOCK_CHILD_STATUS=0
if [ "$GSD_AUTO_INSTALL_LOCK_FD" != 9 ]; then
  LOCK_CHILD_STATUS=76
else
  python3 -I - "$LOCK_PATH" 9 2>/dev/null <<'PY' || LOCK_CHILD_STATUS=$?
import errno
import fcntl
import os
import stat
import sys

try:
    path_entry = os.stat(sys.argv[1], follow_symlinks=False)
    fd = int(sys.argv[2])
    descriptor = os.fstat(fd)
except (OSError, TypeError, ValueError):
    raise SystemExit(76)
if (
    not stat.S_ISREG(path_entry.st_mode)
    or not stat.S_ISREG(descriptor.st_mode)
    or path_entry.st_dev != descriptor.st_dev
    or path_entry.st_ino != descriptor.st_ino
    or descriptor.st_uid != os.geteuid()
    or descriptor.st_nlink != 1
):
    raise SystemExit(76)
try:
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError as error:
    if error.errno in (errno.EACCES, errno.EAGAIN):
        raise SystemExit(75)
    raise SystemExit(76)
PY
fi
if [ "$LOCK_CHILD_STATUS" -ne 0 ]; then
  if [ "$LOCK_CHILD_STATUS" -eq 75 ]; then
    echo "capability-auto-install: projection transaction busy for $CAP_ID; projection not recorded" >&2
  else
    echo "capability-auto-install: projection lock failed for $CAP_ID; projection not recorded" >&2
  fi
  exit 0
fi
unset GSD_AUTO_INSTALL_LOCK_FD GSD_AUTO_INSTALL_SKILLS_ROOT

# The stable path gsd-core records as the ledger source that `capability
# update` re-fetches (R28).
SOURCE_PARENT="$STATE_DIR/capability-auto-install-$CAP_ID.source"
SOURCE_DIR="$SOURCE_PARENT/$CAP_ID"

# Only a lock holder creates stage/prev dirs and its EXIT trap removes them,
# so any found while holding the lock leaked from a killed holder: no pid or
# age test is needed. A leaked prev holds the source that was recorded before
# the killed install. Unless the stable source already equals the installed
# bundle (the install completed), it goes back, so unconsented candidate
# bytes are never left recorded; a missing stable source just forces a
# fresh publish below. Equal needs both hashes to succeed: two failures
# print the same empty string. An empty prev means no source was recorded
# before, so restoring it removes the stable source.
for _leaked_prev in "$STATE_DIR/.capability-auto-install-$CAP_ID.prev."*; do
  [ -d "$_leaked_prev" ] && [ ! -L "$_leaked_prev" ] || continue
  if [ -e "$_leaked_prev/source" ] || [ -L "$_leaked_prev/source" ]; then
    [ -d "$_leaked_prev/source" ] && [ ! -L "$_leaked_prev/source" ] || continue
  fi
  if ! _source_hash="$(canonical_tree_hash "$SOURCE_DIR")" \
    || ! _installed_hash="$(canonical_tree_hash "$INSTALLED_BUNDLE")" \
    || [ "$_source_hash" != "$_installed_hash" ]; then
    rm -rf "$SOURCE_PARENT" 2>/dev/null
    { [ ! -d "$_leaked_prev/source" ] && [ ! -e "$SOURCE_PARENT" ]; } \
      || mv "$_leaked_prev/source" "$SOURCE_PARENT" 2>/dev/null || {
      echo "capability-auto-install: stale source restore failed for $CAP_ID; projection not recorded" >&2
      exit 0
    }
  fi
done
rm -rf "$STATE_DIR/.capability-auto-install-$CAP_ID.stage."* \
  "$STATE_DIR/.capability-auto-install-$CAP_ID.prev."* 2>/dev/null

# Stage the allowlist into a private temp dir (mktemp -d is 0700) and run every
# hash/verify step against it. cp -P keeps symlinks as symlinks so the hash and
# ownership checks below still reject them. The stage sits in STATE_DIR so it
# can be renamed to SOURCE_DIR.
STAGE_DIR="$(mktemp -d "$STATE_DIR/.capability-auto-install-$CAP_ID.stage.XXXXXX" 2>/dev/null)" \
  && [ -d "$STAGE_DIR" ] || STAGE_DIR=""
PREV_SOURCE=""
trap '[ -n "$STAGE_DIR" ] && rm -rf "$STAGE_DIR"; [ -n "$PREV_SOURCE" ] && rm -rf "$PREV_SOURCE"' EXIT
BUNDLE_DIR="$STAGE_DIR/$CAP_ID"
STAGE_OK=0
if [ -n "$STAGE_DIR" ] && mkdir "$BUNDLE_DIR" 2>/dev/null; then
  STAGE_OK=1
  for _entry in "${BUNDLE_ALLOWLIST[@]}"; do
    if [ -e "$PLUGIN_ROOT/$_entry" ] || [ -L "$PLUGIN_ROOT/$_entry" ]; then
      cp -RP "$PLUGIN_ROOT/$_entry" "$BUNDLE_DIR/$_entry" 2>/dev/null || STAGE_OK=0
    fi
  done
  find "$BUNDLE_DIR" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
fi
if [ "$STAGE_OK" -ne 1 ]; then
  echo "capability-auto-install: bundle staging failed for $CAP_ID; projection not recorded" >&2
  exit 0
fi

SELECTED_SKILL_NAMES="$(python3 -I - "$BUNDLE_DIR/capability.json" 9>&- 2>/dev/null <<'PY'
import json
import pathlib
import re
import sys

try:
    skills = json.loads(pathlib.Path(sys.argv[1]).read_text())["skills"]
except (OSError, KeyError, TypeError, json.JSONDecodeError):
    raise SystemExit(1)
if not isinstance(skills, list) or not skills:
    raise SystemExit(1)
for skill in skills:
    if not isinstance(skill, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", skill):
        raise SystemExit(1)
if len(skills) != len(set(skills)):
    raise SystemExit(1)
print("\n".join(skills))
PY
)"
SELECTED_SKILL_STATUS=$?
if [ "$SELECTED_SKILL_STATUS" -ne 0 ] || [ -z "$SELECTED_SKILL_NAMES" ]; then
  echo "capability-auto-install: selected projection verification failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
fi
# Read once into an array and reuse it everywhere below -- each name is
# already validated (`[a-z][a-z0-9-]*`, no glob/IFS characters possible) by
# the python3 block above, so unquoted `for _stem in $SELECTED_SKILL_NAMES`
# was already safe, but an array avoids relying on that invariant twice.
readarray -t SELECTED_SKILL_ARR <<<"$SELECTED_SKILL_NAMES"

gsd_tools() {
  "$GSD_TOOLS" "$@" 9>&-
}

# Native surface application overwrites retained names before pruning. Guard
# same-name collisions so only an absent destination or this capability's own
# marker can reach that writer; unmarked user content remains untouched.
guard_skill_ownership() {
  local _skills_root _stem _dest _marker
  _skills_root="$SKILLS_ROOT"
  for _stem in "${SELECTED_SKILL_ARR[@]}"; do
    [ -d "$BUNDLE_DIR/skills/$_stem" ] && [ ! -L "$BUNDLE_DIR/skills/$_stem" ] || return 1
    _dest="$_skills_root/gsd-$_stem"
    _marker="$_dest/.gsd-capability-skill"
    if [ -e "$_dest" ] || [ -L "$_dest" ]; then
      [ -d "$_dest" ] && [ ! -L "$_dest" ] || return 1
      [ -f "$_marker" ] && [ ! -L "$_marker" ] \
        && [ "$(cat "$_marker" 9>&- 2>/dev/null)" = "$CAP_ID" ] || return 1
    fi
  done
}

verify_selected_projection() {
  python3 -I - "$BUNDLE_DIR/capability.json" "$SKILLS_ROOT" \
    "${GSD_HOME:-$HOME}/.gsd/capabilities/$CAP_ID/scripts/sync.py" "$CAP_ID" 9>&- 2>/dev/null <<'PY'
import json
import pathlib
import re
import shlex
import subprocess
import sys

manifest_path, skills_root, sync_path = map(pathlib.Path, sys.argv[1:4])
capability_id = sys.argv[4]
try:
    skills = json.loads(manifest_path.read_text())["skills"]
except (OSError, KeyError, TypeError, json.JSONDecodeError):
    raise SystemExit(20)
if not sync_path.is_file() or sync_path.is_symlink():
    raise SystemExit(20)

commands = set()
for stem in skills:
    selected = skills_root / f"gsd-{stem}"
    marker = selected / ".gsd-capability-skill"
    skill_file = selected / "SKILL.md"
    if (
        not selected.is_dir()
        or selected.is_symlink()
        or not marker.is_file()
        or marker.is_symlink()
        or marker.read_text().rstrip("\n") != capability_id
        or not skill_file.is_file()
        or skill_file.is_symlink()
    ):
        raise SystemExit(20)
    text = skill_file.read_text()
    if "execute-plan" in text:
        raise SystemExit(21)
    for declaration in re.findall(r'^python3 (?:-I )?"\$SYNC_PY" (.+)$', text, re.MULTILINE):
        prefix = []
        for token in shlex.split(declaration):
            if "<" in token or "[" in token:
                break
            if not re.fullmatch(r"[a-z][a-z0-9-]*", token):
                raise SystemExit(21)
            prefix.append(token)
        if not prefix:
            raise SystemExit(21)
        commands.add(tuple(prefix))
if not commands:
    raise SystemExit(21)
for prefix in sorted(commands):
    result = subprocess.run(
        [sys.executable, "-I", str(sync_path), *prefix, "--help"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(21)
retired = subprocess.run(
    [sys.executable, "-I", str(sync_path), "execute-plan", "--help"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
)
if retired.returncode == 0:
    raise SystemExit(21)
PY
}

selected_fingerprint() {
  local _stem _paths=()
  for _stem in "${SELECTED_SKILL_ARR[@]}"; do
    _paths+=("gsd-$_stem")
  done
  canonical_tree_hash "$SKILLS_ROOT" "${_paths[@]}"
}

ledger_has_current_row() {
  python3 -I - "$LEDGER" "$ACTIVE_RUNTIME" "$SOURCE_GENERATION" \
    "$INSTALLED_GENERATION" "$SELECTED_FINGERPRINT" 9>&- 2>/dev/null <<'PY'
import pathlib
import re
import sys

ledger = pathlib.Path(sys.argv[1])
runtime, source_generation, installed_generation, selected_fingerprint = sys.argv[2:]
if source_generation != installed_generation or not ledger.is_file() or ledger.is_symlink():
    raise SystemExit(1)
rows = ledger.read_text().splitlines()
pattern = re.compile(r"projection-v2 (claude|codex) ([0-9a-f]{64}) ([0-9a-f]{64})")
if len(rows) > 2 or rows != sorted(set(rows)):
    raise SystemExit(1)
parsed = [pattern.fullmatch(row) for row in rows]
if not all(parsed):
    raise SystemExit(1)
expected = f"projection-v2 {runtime} {installed_generation} {selected_fingerprint}"
raise SystemExit(0 if expected in rows else 1)
PY
}

ledger_target_is_safe() {
  python3 -I - "$LEDGER" 9>&- 2>/dev/null <<'PY'
import os
import stat
import sys

path = sys.argv[1]
try:
    metadata = os.lstat(path)
except FileNotFoundError:
    raise SystemExit(0)
except OSError:
    raise SystemExit(1)
if (
    not stat.S_ISREG(metadata.st_mode)
    or metadata.st_uid != os.geteuid()
    or metadata.st_nlink != 1
):
    raise SystemExit(1)
PY
}

publish_ledger() {
  python3 -I - "$LEDGER" "$LEGACY_STATE_FILE" "$ACTIVE_RUNTIME" \
    "$INSTALLED_GENERATION" "$SELECTED_FINGERPRINT" 9>&- 2>/dev/null <<'PY'
import os
import pathlib
import re
import stat
import sys
import tempfile

ledger, legacy = map(pathlib.Path, sys.argv[1:3])
runtime, generation, fingerprint = sys.argv[3:]
pattern = re.compile(r"projection-v2 (claude|codex) ([0-9a-f]{64}) ([0-9a-f]{64})")
rows = {}


def read_existing_rows():
    flags = os.O_RDONLY | os.O_NONBLOCK
    try:
        flags |= os.O_NOFOLLOW
    except AttributeError:
        raise OSError
    try:
        descriptor = os.open(ledger, flags)
    except FileNotFoundError:
        return []
    try:
        metadata = os.fstat(descriptor)
        path_metadata = os.stat(ledger, follow_symlinks=False)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or not stat.S_ISREG(path_metadata.st_mode)
            or metadata.st_dev != path_metadata.st_dev
            or metadata.st_ino != path_metadata.st_ino
            or metadata.st_uid != os.geteuid()
            or metadata.st_nlink != 1
        ):
            raise OSError
        with os.fdopen(descriptor, encoding="utf-8") as stream:
            descriptor = -1
            return stream.read().splitlines()
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def target_is_safe():
    try:
        metadata = os.lstat(ledger)
    except FileNotFoundError:
        return True
    return (
        stat.S_ISREG(metadata.st_mode)
        and metadata.st_uid == os.geteuid()
        and metadata.st_nlink == 1
    )


def cleanup_temporary(path, identity):
    if path is None:
        return
    try:
        metadata = os.lstat(path)
        if (
            stat.S_ISREG(metadata.st_mode)
            and (metadata.st_dev, metadata.st_ino) == identity
        ):
            os.unlink(path)
    except OSError:
        pass


temporary_path = None
temporary_identity = None
try:
    for row in read_existing_rows():
        match = pattern.fullmatch(row)
        if match and match.group(2) == generation and match.group(1) != runtime:
            rows[match.group(1)] = row
    rows[runtime] = f"projection-v2 {runtime} {generation} {fingerprint}"
    serialized = "".join(f"{rows[key]}\n" for key in sorted(rows))
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=ledger.parent,
        prefix=f".{ledger.name}.",
        delete=False,
    ) as stream:
        temporary_path = pathlib.Path(stream.name)
        metadata = os.fstat(stream.fileno())
        temporary_identity = (metadata.st_dev, metadata.st_ino)
        stream.write(serialized)
        stream.flush()
        os.fsync(stream.fileno())
    if not target_is_safe():
        raise OSError
    os.replace(temporary_path, ledger)
    temporary_path = None
except (OSError, UnicodeError):
    cleanup_temporary(temporary_path, temporary_identity)
    raise SystemExit(1)

try:
    metadata = os.lstat(legacy)
except OSError:
    metadata = None
if (
    metadata is not None
    and stat.S_ISREG(metadata.st_mode)
    and not stat.S_ISLNK(metadata.st_mode)
    and metadata.st_uid == os.geteuid()
    and metadata.st_nlink == 1
):
    try:
        os.unlink(legacy)
    except OSError:
        pass
PY
}

if ! ledger_target_is_safe; then
  echo "capability-auto-install: ledger publish failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
fi

SOURCE_GENERATION="$(canonical_tree_hash "$BUNDLE_DIR")"
SOURCE_STATUS=$?
if [ "$SOURCE_STATUS" -ne 0 ]; then
  echo "capability-auto-install: source generation verification failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
fi
INSTALLED_GENERATION="$(canonical_tree_hash "$INSTALLED_BUNDLE")"
INSTALLED_STATUS=$?
SELECTED_FINGERPRINT="$(selected_fingerprint)"
SELECTED_STATUS=$?
if [ "$SOURCE_STATUS" -eq 0 ] && [ "$INSTALLED_STATUS" -eq 0 ] \
  && [ "$SELECTED_STATUS" -eq 0 ] && [ -d "$SOURCE_DIR" ] && [ ! -L "$SOURCE_PARENT" ] \
  && ledger_has_current_row; then
  exit 0
fi

# Spec is always the absolute bundle dir (Pattern 2) -- a relative spec would
# resolve against the end user's cwd, not the plugin. Prose "user scope"
# (D-01) maps to the CLI's literal --scope global value (Pitfall 1).
# Refuse a downgrade: two runtimes' plugin caches can carry different
# bundle versions and share one global install, which would otherwise flip
# on every runtime switch. An unparsable installed version fails closed.
# At an equal version with different bytes, keep the installed bundle only
# on positive evidence that it is the other runtime's verified projection
# (its ledger row records these bytes) and this plugin cache
# is not newer. Cache mtime is the time the runtime extracted that plugin
# version; the installed copy's mtime is its install time. Anything else,
# drift included, is replaced. This narrows the ticket's "ours or older"
# rule, which read literally never repairs drift: an install always leaves
# the installed copy newer than the cache it came from. A kept bundle is still
# set, verified and recorded for this runtime: the other runtime's install
# and set never project this runtime's skills root.
KEPT=0
if [ -e "$INSTALLED_BUNDLE/capability.json" ] || [ -L "$INSTALLED_BUNDLE/capability.json" ]; then
  python3 -I - "$BUNDLE_DIR/capability.json" "$INSTALLED_BUNDLE/capability.json" \
    "$PLUGIN_ROOT/capability.json" "$LEDGER" "$ACTIVE_RUNTIME" "$SOURCE_GENERATION" \
    "$INSTALLED_GENERATION" 9>&- 2>/dev/null <<'PY'
import json
import os
import pathlib
import re
import sys

def version(path):
    path = pathlib.Path(path)
    if path.is_symlink():
        raise ValueError
    value = json.loads(path.read_text())["version"]
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(\.[0-9]+)*", value):
        raise ValueError
    return tuple(int(part) for part in value.split("."))

try:
    source, installed = version(sys.argv[1]), version(sys.argv[2])
except (OSError, KeyError, TypeError, ValueError):
    raise SystemExit(1)
if source != installed:
    raise SystemExit(0 if source > installed else 1)
plugin_manifest, ledger, runtime, source_generation, installed_generation = sys.argv[3:]
if source_generation == installed_generation:
    raise SystemExit(0)
try:
    rows = pathlib.Path(ledger).read_text().splitlines() if not pathlib.Path(ledger).is_symlink() else []
    cache_newer = os.stat(plugin_manifest).st_mtime_ns > os.lstat(sys.argv[2]).st_mtime_ns
except OSError:
    raise SystemExit(0)
recorders = {
    match.group(1)
    for match in map(re.compile(r"projection-v2 (claude|codex) ([0-9a-f]{64}) [0-9a-f]{64}").fullmatch, rows)
    if match and match.group(2) == installed_generation
}
raise SystemExit(2 if recorders - {runtime} and not cache_newer else 0)
PY
  GUARD_STATUS=$?
  if [ "$GUARD_STATUS" -eq 1 ]; then
    echo "capability-auto-install: refusing to replace a newer or unreadable installed $CAP_ID with this bundle on $ACTIVE_RUNTIME; projection not recorded" >&2
    exit 0
  elif [ "$GUARD_STATUS" -eq 2 ]; then
    # Log once per kept generation: this repeats every SessionStart until a
    # plugin update, and a repeated line would teach the user to ignore it.
    KEPT_MARKER="$STATE_DIR/capability-auto-install-$CAP_ID.$ACTIVE_RUNTIME.kept"
    if [ -L "$KEPT_MARKER" ] || [ "$(cat "$KEPT_MARKER" 2>/dev/null)" != "$INSTALLED_GENERATION" ]; then
      echo "capability-auto-install: keeping the installed $CAP_ID the other runtime verified, which differs from this older equal-version bundle on $ACTIVE_RUNTIME; projecting the installed bundle" >&2
      rm -f "$KEPT_MARKER" 2>/dev/null
      ( set -C; printf '%s\n' "$INSTALLED_GENERATION" > "$KEPT_MARKER" ) 2>/dev/null
    fi
    KEPT=1
    BUNDLE_DIR="$INSTALLED_BUNDLE"
    SOURCE_GENERATION="$INSTALLED_GENERATION"
    ledger_has_current_row && exit 0
  elif [ "$GUARD_STATUS" -ne 0 ]; then
    echo "capability-auto-install: version check failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
    exit 0
  fi
fi

if ! guard_skill_ownership; then
  echo "capability-auto-install: destination ownership check failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
fi

# gsd-core records SOURCE_DIR as the source `capability update` re-fetches,
# so the install must run from there -- but a failed install must not leave
# unverified bytes recorded. Park the previous source until the install
# outcome is known; restore_source puts it back (or removes the candidate
# when there was none). A symlinked source is never kept or restored. A kept
# bundle skips all of this: the stable source is the other runtime's.
INSTALL_STATUS=0
if [ "$KEPT" -eq 0 ]; then
# The prev dir exists even with no source to park: left empty, it tells the
# sweep that a killed holder's swapped-in candidate must go.
PREV_SOURCE="$(mktemp -d "$STATE_DIR/.capability-auto-install-$CAP_ID.prev.XXXXXX" 2>/dev/null)" || PREV_SOURCE=""
if [ -z "$PREV_SOURCE" ] || { [ -d "$SOURCE_PARENT" ] && [ ! -L "$SOURCE_PARENT" ] \
  && ! mv "$SOURCE_PARENT" "$PREV_SOURCE/source" 2>/dev/null; }; then
  echo "capability-auto-install: stable source publish failed for $CAP_ID; projection not recorded" >&2
  exit 0
fi
restore_source() {
  rm -rf "$SOURCE_PARENT" 2>/dev/null
  [ ! -d "$PREV_SOURCE/source" ] || mv "$PREV_SOURCE/source" "$SOURCE_PARENT" 2>/dev/null
}
rm -rf "$SOURCE_PARENT" 2>/dev/null
if [ -e "$SOURCE_PARENT" ] || [ -L "$SOURCE_PARENT" ] || ! mv "$STAGE_DIR" "$SOURCE_PARENT" 2>/dev/null; then
  restore_source
  echo "capability-auto-install: stable source publish failed for $CAP_ID; projection not recorded" >&2
  exit 0
fi
STAGE_DIR=""
BUNDLE_DIR="$SOURCE_DIR"

# --yes only in consent mode: consent to an executable surface is the
# user's, not a SessionStart side effect. gsd-core reports the block as a
# JSON envelope. When the installed bytes already equal the candidate, the
# consent was already given: project and record rather than re-ask every
# SessionStart; the success path re-verifies the generation. Otherwise the
# stable source goes back to its previous bytes, because `capability update`
# re-fetches it and must never pick up bytes the user has not consented to.
CONSENT_FLAG=()
[ "$CONSENT" -eq 0 ] || CONSENT_FLAG=(--yes)
INSTALL_OUTPUT="$(gsd_tools capability install "$BUNDLE_DIR" --scope global ${CONSENT_FLAG[@]+"${CONSENT_FLAG[@]}"} 2>/dev/null)"
INSTALL_STATUS=$?
if [ "$INSTALL_STATUS" -ne 0 ] && [ "$CONSENT" -eq 0 ] && printf '%s' "$INSTALL_OUTPUT" | python3 -I -c '
import json, sys
try:
    envelope = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
sys.exit(0 if isinstance(envelope, dict) and envelope.get("requiresConsent") is True else 1)
' 9>&- 2>/dev/null; then
  if [ "$INSTALLED_STATUS" -ne 0 ] || [ "$INSTALLED_GENERATION" != "$SOURCE_GENERATION" ]; then
    restore_source
    printf -v CONSENT_COMMAND 'bash %q --consent %q' "$PLUGIN_ROOT/hooks/capability-auto-install.sh" "$CAP_ID"
    echo "capability-auto-install: $CAP_ID needs your consent before install; run: $CONSENT_COMMAND" >&2
    exit 0
  fi
  INSTALL_STATUS=0
fi
fi # KEPT -eq 0

# A failure after install leaves the new bundle live but unverified: disable
# it, record that the hook did so, and name the command that undoes it. The
# marker is written unless the capability was confirmed disabled, so a user's
# own --disable (which also fails verification: nothing is projected) is
# never re-enabled, while a failed state query cannot strand it disabled.
# `set` without a flag preserves enabled state, so the state query here
# still reflects the user's choice.
DISABLED_MARKER="$STATE_DIR/capability-auto-install-$CAP_ID.$ACTIVE_RUNTIME.disabled"
roll_back() {
  local _enabled
  _enabled="$(GSD_RUNTIME="$ACTIVE_RUNTIME" gsd_tools capability state --runtime "$ACTIVE_RUNTIME" \
      --config-dir "$RUNTIME_CONFIG_DIR" --raw 2>/dev/null | python3 -I -c '
import json, sys
try:
    found = [c.get("enabled") for c in json.load(sys.stdin)["capabilities"] if c.get("id") == sys.argv[1]]
except (ValueError, KeyError, TypeError, AttributeError):
    found = []
print({(True,): "true", (False,): "false"}.get(tuple(found), "unknown"))
' "$CAP_ID" 9>&- 2>/dev/null)"
  if [ "$_enabled" = false ]; then
    echo "capability-auto-install: $1 for $CAP_ID on $ACTIVE_RUNTIME; left as disabled by the user; projection not recorded" >&2
    exit 0
  fi
  if GSD_RUNTIME="$ACTIVE_RUNTIME" gsd_tools capability set "$CAP_ID" --disable --runtime "$ACTIVE_RUNTIME" \
      --scope global --config-dir "$RUNTIME_CONFIG_DIR" >/dev/null 2>&1; then
    rm -f "$DISABLED_MARKER" 2>/dev/null
    ( set -C; : > "$DISABLED_MARKER" ) 2>/dev/null
    echo "capability-auto-install: $1 for $CAP_ID on $ACTIVE_RUNTIME; capability disabled (re-enable: $GSD_TOOLS capability set $CAP_ID --enable --runtime $ACTIVE_RUNTIME --scope global --config-dir $RUNTIME_CONFIG_DIR); projection not recorded" >&2
  else
    echo "capability-auto-install: $1 for $CAP_ID on $ACTIVE_RUNTIME; rollback failed, capability may be half-installed; projection not recorded" >&2
  fi
  exit 0
}

if [ "$INSTALL_STATUS" -eq 0 ]; then
  INSTALLED_GENERATION="$(canonical_tree_hash "$INSTALLED_BUNDLE")"
  if [ "$?" -ne 0 ] || [ "$INSTALLED_GENERATION" != "$SOURCE_GENERATION" ]; then
    roll_back "installed generation verification failed"
  fi
  # Re-enable only a capability this hook disabled itself (rollback below);
  # a user's own --disable carries no marker and stays disabled.
  SET_ENABLE=()
  [ -f "$DISABLED_MARKER" ] && [ ! -L "$DISABLED_MARKER" ] && SET_ENABLE=(--enable)
  GSD_RUNTIME="$ACTIVE_RUNTIME" gsd_tools capability set "$CAP_ID" ${SET_ENABLE[@]+"${SET_ENABLE[@]}"} --runtime "$ACTIVE_RUNTIME" --scope global --config-dir "$RUNTIME_CONFIG_DIR" >/dev/null 2>&1
  RECONCILE_STATUS=$?
  if [ "$RECONCILE_STATUS" -eq 0 ]; then
    verify_selected_projection
    VERIFY_STATUS=$?
    if [ "$VERIFY_STATUS" -eq 21 ]; then
      roll_back "selected command contract verification failed"
    elif [ "$VERIFY_STATUS" -ne 0 ]; then
      roll_back "selected projection verification failed"
    fi
    SELECTED_FINGERPRINT="$(selected_fingerprint)"
    if [ "$?" -ne 0 ] || [[ ! "$SELECTED_FINGERPRINT" =~ ^[0-9a-f]{64}$ ]]; then
      roll_back "selected projection verification failed"
    fi
    FINAL_INSTALLED_GENERATION="$(canonical_tree_hash "$INSTALLED_BUNDLE")"
    if [ "$?" -ne 0 ] || [ "$FINAL_INSTALLED_GENERATION" != "$INSTALLED_GENERATION" ]; then
      roll_back "installed generation verification failed"
    fi
    FINAL_SELECTED_FINGERPRINT="$(selected_fingerprint)"
    if [ "$?" -ne 0 ] || [ "$FINAL_SELECTED_FINGERPRINT" != "$SELECTED_FINGERPRINT" ]; then
      roll_back "selected projection verification failed"
    fi
    rm -f "$DISABLED_MARKER" 2>/dev/null
    if publish_ledger; then
      printf 'Auto-installed capability: %s (user scope)\n' "$CAP_ID"
    else
      echo "capability-auto-install: ledger publish failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
    fi
  else
    roll_back "capability set failed"
  fi
else
  restore_source
  echo "capability-auto-install: capability install failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
fi

exit 0
