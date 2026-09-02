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

# Portable hash tool selection (Assumption A3: macOS ships no sha256sum).
if command -v sha256sum >/dev/null 2>&1; then
  HASH_CMD=(sha256sum)
elif command -v shasum >/dev/null 2>&1; then
  HASH_CMD=(shasum -a 256)
else
  exit 0
fi

# Whole-bundle-directory hash (D-03): LC_ALL=C-sorted list of every path
# under the bundle (files AND directories, so an added empty directory is
# caught -- Assumption A1) followed by the concatenated contents of the
# sorted regular files.
bundle_hash() {
  {
    find "$BUNDLE_DIR" \( -type f -o -type d \) | LC_ALL=C sort
    find "$BUNDLE_DIR" -type f | LC_ALL=C sort | while IFS= read -r _f; do cat "$_f"; done
  } | "${HASH_CMD[@]}" | awk '{print $1}'
}

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

STATE_VERSION="projection-v1"

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

# One sidecar per capability, with one line per runtime. A successful Codex
# projection must not make Claude skip its own update, or vice versa. Legacy
# raw-hash content matches no versioned line and is replaced on first success.
STATE_FILE="${GSD_HOME:-$HOME}/.gsd/capability-auto-install-$CAP_ID.hash"
NEW_HASH="$(bundle_hash)"
NEW_STATE="$STATE_VERSION $ACTIVE_RUNTIME $NEW_HASH"
if [ -r "$STATE_FILE" ] && grep -qxF "$NEW_STATE" "$STATE_FILE" 2>/dev/null; then
  exit 0
fi

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
    mkdir -p "$(dirname "$STATE_FILE")" 2>/dev/null
    STATE_TMP="$STATE_FILE.$$"
    {
      [ ! -r "$STATE_FILE" ] || awk -v runtime="$ACTIVE_RUNTIME" \
        '$1 == "projection-v1" && $2 != runtime { print }' "$STATE_FILE"
      printf '%s\n' "$NEW_STATE"
    } > "$STATE_TMP" 2>/dev/null && mv -f "$STATE_TMP" "$STATE_FILE" 2>/dev/null
    STATE_STATUS=$?
    if [ "$STATE_STATUS" -eq 0 ]; then
      printf 'Auto-installed capability: %s (user scope)\n' "$CAP_ID"
    else
      rm -f "$STATE_TMP" 2>/dev/null
      echo "capability-auto-install: state update failed for $CAP_ID (exit $STATE_STATUS)" >&2
    fi
  else
    echo "capability-auto-install: capability set failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
  fi
else
  echo "capability-auto-install: capability install failed for $CAP_ID on $ACTIVE_RUNTIME; projection not recorded" >&2
fi

exit 0
