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
  python3 - "$@" <<'PY'
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
for relative in sorted(entries):
    path = entries[relative]
    name = os.fsencode(relative)
    kind = b"d" if path.is_dir() else b"f"
    digest.update(kind + len(name).to_bytes(8, "big") + name)
    if kind == b"f":
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big") + data)
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

SKILLS_ROOT="$($GSD_TOOLS query skills-root "$ACTIVE_RUNTIME" --raw 2>/dev/null)"
SKILLS_ROOT_STATUS=$?
if [ "$SKILLS_ROOT_STATUS" -ne 0 ] || [ "$SKILLS_ROOT" != "$EXPECTED_SKILLS_ROOT" ]; then
  echo "capability-auto-install: skills-root query failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
fi

SELECTED_SKILL_NAMES="$(python3 - "$BUNDLE_DIR/capability.json" <<'PY'
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
  "$GSD_TOOLS" "$@"
}

STATE_DIR="${GSD_HOME:-$HOME}/.gsd"
INSTALLED_BUNDLE="$STATE_DIR/capabilities/$CAP_ID"
LEDGER="$STATE_DIR/capability-auto-install-$CAP_ID.projections"
LEGACY_STATE_FILE="$STATE_DIR/capability-auto-install-$CAP_ID.hash"

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
      [ -f "$_marker" ] && [ "$(cat "$_marker" 2>/dev/null)" = "$CAP_ID" ] || return 1
    fi
  done
}

verify_selected_projection() {
  python3 - "$BUNDLE_DIR/capability.json" "$SKILLS_ROOT" \
    "${GSD_HOME:-$HOME}/.gsd/capabilities/$CAP_ID/scripts/sync.py" "$CAP_ID" <<'PY'
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
    "$INSTALLED_GENERATION" "$SELECTED_FINGERPRINT" <<'PY'
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

publish_ledger() {
  local _tmp="$LEDGER.$$" _legacy_tmp="$LEGACY_STATE_FILE.$$"
  python3 - "$LEDGER" "$_tmp" "$ACTIVE_RUNTIME" "$INSTALLED_GENERATION" \
    "$SELECTED_FINGERPRINT" <<'PY'
import pathlib
import re
import sys

ledger, target = map(pathlib.Path, sys.argv[1:3])
runtime, generation, fingerprint = sys.argv[3:]
pattern = re.compile(r"projection-v2 (claude|codex) ([0-9a-f]{64}) ([0-9a-f]{64})")
rows = {}
try:
    old_rows = ledger.read_text().splitlines() if ledger.is_file() and not ledger.is_symlink() else []
    for row in old_rows:
        match = pattern.fullmatch(row)
        if match and match.group(2) == generation and match.group(1) != runtime:
            rows[match.group(1)] = row
    rows[runtime] = f"projection-v2 {runtime} {generation} {fingerprint}"
    target.write_text("".join(f"{rows[key]}\n" for key in sorted(rows)))
except OSError:
    raise SystemExit(1)
PY
  [ "$?" -eq 0 ] || return 1

  if [ -e "$LEGACY_STATE_FILE" ] || [ -L "$LEGACY_STATE_FILE" ]; then
    [ -f "$LEGACY_STATE_FILE" ] && [ ! -L "$LEGACY_STATE_FILE" ] || return 1
    mv -f "$LEGACY_STATE_FILE" "$_legacy_tmp" 2>/dev/null || return 1
  fi
  if ! mv -f "$_tmp" "$LEDGER" 2>/dev/null; then
    [ ! -e "$_legacy_tmp" ] || mv -f "$_legacy_tmp" "$LEGACY_STATE_FILE" 2>/dev/null
    return 1
  fi
  rm -f "$_legacy_tmp" 2>/dev/null
}

process_identity() {
  local _pid="$1" _stat _remainder _identity _ps_output
  [[ "$_pid" =~ ^[1-9][0-9]*$ ]] || return 1
  _stat=""
  if [ -r "${GSD_AUTO_INSTALL_PROC_ROOT:-/proc}/$_pid/stat" ]; then
    IFS= read -r _stat < "${GSD_AUTO_INSTALL_PROC_ROOT:-/proc}/$_pid/stat" || _stat=""
    _remainder="${_stat##*) }"
    if [ -n "$_stat" ] && [ "$_remainder" != "$_stat" ]; then
      set -- $_remainder
      if [ "$#" -ge 20 ] && [[ "${20}" =~ ^[0-9]+$ ]]; then
        printf '%s\n' "${20}"
        return 0
      fi
    fi
  fi

  command -v ps >/dev/null 2>&1 || return 1
  _ps_output="$(ps -o lstart= -p "$_pid" 2>/dev/null)" || return 1
  _identity="$(printf '%s\n' "$_ps_output" | awk '
    NF { count += 1; line = $0 }
    END {
      if (count != 1) exit 1
      sub(/^[[:space:]]+/, "", line)
      sub(/[[:space:]]+$/, "", line)
      if (line == "") exit 1
      print line
    }
  ')" || return 1
  [ -n "$_identity" ] || return 1
  printf '%s\n' "$_identity"
}

release_projection_lock() {
  local _current
  [ "${LOCK_OWNED:-0}" -eq 1 ] || return 0
  _current="$(readlink "$LOCK_PATH" 2>/dev/null)" || return 0
  if [ "$_current" = "$OWNER_TOKEN" ]; then
    rm -f "$LOCK_PATH" 2>/dev/null
    LOCK_OWNED=0
  fi
}

mkdir -p "$STATE_DIR" 2>/dev/null || {
  echo "capability-auto-install: ledger publish failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  exit 0
}
SELF_IDENTITY="$(process_identity "$$")"
if [ "$?" -ne 0 ] || [ -z "$SELF_IDENTITY" ]; then
  echo "capability-auto-install: process identity unavailable for $CAP_ID; projection not recorded" >&2
  exit 0
fi
OWNER_TOKEN="$$:$SELF_IDENTITY"
LOCK_PATH="$LEDGER.lock"
LOCK_OWNED=0
if ln -s "$OWNER_TOKEN" "$LOCK_PATH" 2>/dev/null; then
  LOCK_OWNED=1
else
  CONTENDER_TOKEN="$(readlink "$LOCK_PATH" 2>/dev/null)"
  STALE_LOCK=0
  if [[ "$CONTENDER_TOKEN" =~ ^([1-9][0-9]*):(.*)$ ]]; then
    CONTENDER_PID="${BASH_REMATCH[1]}"
    RECORDED_IDENTITY="${BASH_REMATCH[2]}"
    CONTENDER_IDENTITY="$(process_identity "$CONTENDER_PID")"
    CONTENDER_STATUS=$?
    if [ "$CONTENDER_STATUS" -eq 0 ] && [ "$CONTENDER_IDENTITY" = "$RECORDED_IDENTITY" ]; then
      echo "capability-auto-install: projection transaction busy for $CAP_ID; projection not recorded" >&2
      exit 0
    elif [ "$CONTENDER_STATUS" -eq 0 ]; then
      STALE_LOCK=1
    elif [ "${GSD_AUTO_INSTALL_PROC_ROOT:-/proc}" = "/proc" ] \
      && [ ! -e "/proc/$CONTENDER_PID" ]; then
      STALE_LOCK=1
    elif kill -0 "$CONTENDER_PID" 2>/dev/null; then
      echo "capability-auto-install: projection transaction busy for $CAP_ID; projection not recorded" >&2
      exit 0
    else
      echo "capability-auto-install: projection transaction busy for $CAP_ID; projection not recorded" >&2
      exit 0
    fi
  else
    STALE_LOCK=1
  fi

  QUARANTINE="$LOCK_PATH.stale.$$.$RANDOM"
  if [ "$STALE_LOCK" -ne 1 ] || ! mv -f "$LOCK_PATH" "$QUARANTINE" 2>/dev/null; then
    echo "capability-auto-install: projection lock recovery failed for $CAP_ID; projection not recorded" >&2
    exit 0
  fi
  QUARANTINED_TOKEN="$(readlink "$QUARANTINE" 2>/dev/null)"
  if [ "$QUARANTINED_TOKEN" != "$CONTENDER_TOKEN" ]; then
    echo "capability-auto-install: projection lock recovery failed for $CAP_ID; projection not recorded" >&2
    exit 0
  fi
  if ! ln -s "$OWNER_TOKEN" "$LOCK_PATH" 2>/dev/null; then
    echo "capability-auto-install: projection lock recovery failed for $CAP_ID; projection not recorded" >&2
    exit 0
  fi
  LOCK_OWNED=1
  if [ "$(readlink "$QUARANTINE" 2>/dev/null)" != "$CONTENDER_TOKEN" ]; then
    release_projection_lock
    echo "capability-auto-install: projection lock recovery failed for $CAP_ID; projection not recorded" >&2
    exit 0
  fi
  rm -f "$QUARANTINE" 2>/dev/null
fi
trap 'release_projection_lock' EXIT
trap 'exit 0' HUP INT TERM

SOURCE_GENERATION="$(canonical_tree_hash "$BUNDLE_DIR")"
SOURCE_STATUS=$?
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
    mkdir -p "$STATE_DIR" 2>/dev/null
    if publish_ledger; then
      printf 'Auto-installed capability: %s (user scope)\n' "$CAP_ID"
    else
      rm -f "$LEDGER.$$" "$LEGACY_STATE_FILE.$$" 2>/dev/null
      echo "capability-auto-install: ledger publish failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
    fi
  else
    echo "capability-auto-install: capability set failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  fi
else
  echo "capability-auto-install: capability install failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
fi

exit 0
