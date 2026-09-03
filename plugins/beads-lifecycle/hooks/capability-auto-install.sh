#!/usr/bin/env bash
# Vendored auto-install hook (D-05: vendored copy per plugin, not shared at
# runtime).
#
# Detects bundle drift via a whole-directory hash and re-grants the
# capability at global ("user") scope on every SessionStart (D-01..D-03).
# Never aborts the session: no `set -e`.
set -u

CAP_ID="${1:-}"

# Defense in depth (ASVS V5): call sites only ever pass a hard-coded literal,
# but validate the id shape gsd-core itself enforces before it reaches any
# path construction.
[[ "$CAP_ID" =~ ^[a-z][a-z0-9-]*$ ]] || exit 0

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BUNDLE_DIR="$PLUGIN_ROOT/.gsd/capabilities/$CAP_ID"
[ -d "$BUNDLE_DIR" ] || exit 0

# Hash an explicitly bounded tree as type-tagged, length-prefixed relative
# paths plus file bytes. Relative framing avoids absolute-root drift and
# concatenation collisions.
canonical_tree_hash() {
  python3 - "$@" 9>&- 2>/dev/null <<'PY'
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

# Reconcile only the runtime that loaded this plugin. An explicit validated
# runtime wins; otherwise the installed plugin cache must identify one owner.
CODEX_CONFIG_ROOT="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_CONFIG_ROOT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ACTIVE_RUNTIME="${GSD_RUNTIME:-}"
case "$ACTIVE_RUNTIME" in
  codex|claude) ;;
  "")
    CODEX_OWNER=0
    CLAUDE_OWNER=0
    [[ "$PLUGIN_ROOT/" == "$CODEX_CONFIG_ROOT"/plugins/* ]] && CODEX_OWNER=1
    [[ "$PLUGIN_ROOT/" == "$CLAUDE_CONFIG_ROOT"/plugins/* ]] && CLAUDE_OWNER=1
    if [ "$CODEX_OWNER" -eq 1 ] && [ "$CLAUDE_OWNER" -eq 0 ]; then
      ACTIVE_RUNTIME="codex"
    elif [ "$CODEX_OWNER" -eq 0 ] && [ "$CLAUDE_OWNER" -eq 1 ]; then
      ACTIVE_RUNTIME="claude"
    else
      echo "capability-auto-install: runtime selection failed for $CAP_ID; projection not recorded" >&2
      exit 0
    fi
    ;;
  *)
    echo "capability-auto-install: runtime selection failed for $CAP_ID; projection not recorded" >&2
    exit 0
    ;;
esac

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
  SKILLS_ROOT="$($GSD_TOOLS query skills-root "$ACTIVE_RUNTIME" --raw 2>/dev/null)"
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
  python3 - "$LOCK_PATH" "$0" "$CAP_ID" "$SKILLS_ROOT" 8>&2 2>/dev/null <<'PY'
import errno
import fcntl
import os
import stat
import sys

lock_path, hook_path, capability_id, skills_root = sys.argv[1:]
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
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        if error.errno in (errno.EACCES, errno.EAGAIN):
            raise SystemExit(75)
        raise SystemExit(76)
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
    os.execvpe("bash", ["bash", hook_path, capability_id], environment)
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
  python3 - "$LOCK_PATH" 9 2>/dev/null <<'PY' || LOCK_CHILD_STATUS=$?
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

SELECTED_SKILL_NAMES="$(python3 - "$BUNDLE_DIR/capability.json" 9>&- 2>/dev/null <<'PY'
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

gsd_tools() {
  "$GSD_TOOLS" "$@" 9>&-
}

# Native surface application overwrites retained names before pruning. Guard
# same-name collisions so only an absent destination or this capability's own
# marker can reach that writer; unmarked user content remains untouched.
guard_skill_ownership() {
  local _skills_root _stem _dest _marker
  _skills_root="$SKILLS_ROOT"
  for _stem in $SELECTED_SKILL_NAMES; do
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
  python3 - "$BUNDLE_DIR/capability.json" "$SKILLS_ROOT" \
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
    for declaration in re.findall(r'^python3 "\$SYNC_PY" (.+)$', text, re.MULTILINE):
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
        [sys.executable, str(sync_path), *prefix, "--help"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(21)
retired = subprocess.run(
    [sys.executable, str(sync_path), "execute-plan", "--help"],
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
  for _stem in $SELECTED_SKILL_NAMES; do
    _paths+=("gsd-$_stem")
  done
  canonical_tree_hash "$SKILLS_ROOT" "${_paths[@]}"
}

ledger_has_current_row() {
  python3 - "$LEDGER" "$ACTIVE_RUNTIME" "$SOURCE_GENERATION" \
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
  python3 - "$LEDGER" 9>&- 2>/dev/null <<'PY'
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
  python3 - "$LEDGER" "$LEGACY_STATE_FILE" "$ACTIVE_RUNTIME" \
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
  && [ "$SELECTED_STATUS" -eq 0 ] && ledger_has_current_row; then
  exit 0
fi

# Spec is always the absolute bundle dir (Pattern 2) -- a relative spec would
# resolve against the end user's cwd, not the plugin. Prose "user scope"
# (D-01) maps to the CLI's literal --scope global value (Pitfall 1).
if ! guard_skill_ownership; then
  echo "capability-auto-install: destination ownership check failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
fi

gsd_tools capability install "$BUNDLE_DIR" --scope global --yes >/dev/null 2>&1
INSTALL_STATUS=$?

if [ "$INSTALL_STATUS" -eq 0 ]; then
  INSTALLED_GENERATION="$(canonical_tree_hash "$INSTALLED_BUNDLE")"
  if [ "$?" -ne 0 ] || [ "$INSTALLED_GENERATION" != "$SOURCE_GENERATION" ]; then
    echo "capability-auto-install: installed generation verification failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
    exit 0
  fi
  GSD_RUNTIME="$ACTIVE_RUNTIME" gsd_tools capability set "$CAP_ID" --runtime "$ACTIVE_RUNTIME" --scope global --config-dir "$RUNTIME_CONFIG_DIR" >/dev/null 2>&1
  RECONCILE_STATUS=$?
  if [ "$RECONCILE_STATUS" -eq 0 ]; then
    verify_selected_projection
    VERIFY_STATUS=$?
    if [ "$VERIFY_STATUS" -eq 21 ]; then
      echo "capability-auto-install: selected command contract verification failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
      exit 0
    elif [ "$VERIFY_STATUS" -ne 0 ]; then
      echo "capability-auto-install: selected projection verification failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
      exit 0
    fi
    SELECTED_FINGERPRINT="$(selected_fingerprint)"
    if [ "$?" -ne 0 ] || [[ ! "$SELECTED_FINGERPRINT" =~ ^[0-9a-f]{64}$ ]]; then
      echo "capability-auto-install: selected projection verification failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
      exit 0
    fi
    FINAL_INSTALLED_GENERATION="$(canonical_tree_hash "$INSTALLED_BUNDLE")"
    if [ "$?" -ne 0 ] || [ "$FINAL_INSTALLED_GENERATION" != "$INSTALLED_GENERATION" ]; then
      echo "capability-auto-install: installed generation verification failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
      exit 0
    fi
    FINAL_SELECTED_FINGERPRINT="$(selected_fingerprint)"
    if [ "$?" -ne 0 ] || [ "$FINAL_SELECTED_FINGERPRINT" != "$SELECTED_FINGERPRINT" ]; then
      echo "capability-auto-install: selected projection verification failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
      exit 0
    fi
    if publish_ledger; then
      printf 'Auto-installed capability: %s (user scope)\n' "$CAP_ID"
    else
      echo "capability-auto-install: ledger publish failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
    fi
  else
    echo "capability-auto-install: capability set failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  fi
else
  echo "capability-auto-install: capability install failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
fi

exit 0
