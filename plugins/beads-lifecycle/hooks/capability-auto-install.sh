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
  local _skills_root _source _stem _dest _marker
  _skills_root="$SKILLS_ROOT"
  for _source in "$BUNDLE_DIR"/skills/*; do
    [ -d "$_source" ] || continue
    _stem="$(basename "$_source")"
    [[ "$_stem" =~ ^[a-z][a-z0-9-]*$ ]] || return 1
    _dest="$_skills_root/gsd-$_stem"
    _marker="$_dest/.gsd-capability-skill"
    if [ -e "$_dest" ] || [ -L "$_dest" ]; then
      [ -d "$_dest" ] && [ ! -L "$_dest" ] || return 1
      [ -f "$_marker" ] && [ "$(cat "$_marker" 2>/dev/null)" = "$CAP_ID" ] || return 1
    fi
  done
}

# Spec is always the absolute bundle dir (Pattern 2) -- a relative spec would
# resolve against the end user's cwd, not the plugin. Prose "user scope"
# (D-01) maps to the CLI's literal --scope global value (Pitfall 1).
gsd_tools capability install "$BUNDLE_DIR" --scope global --yes >/dev/null 2>&1
INSTALL_STATUS=$?

if [ "$INSTALL_STATUS" -eq 0 ]; then
  guard_skill_ownership && \
    GSD_RUNTIME="$ACTIVE_RUNTIME" gsd_tools capability set "$CAP_ID" --runtime "$ACTIVE_RUNTIME" --scope global --config-dir "$RUNTIME_CONFIG_DIR" >/dev/null 2>&1
  RECONCILE_STATUS=$?
  if [ "$RECONCILE_STATUS" -eq 0 ]; then
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
    echo "capability-auto-install: skill projection reconciliation failed for $CAP_ID (exit $RECONCILE_STATUS)" >&2
  fi
elif [ "$INSTALL_STATUS" -eq 127 ]; then
  # D-04: deliberate divergence from this repo's usual silent `|| true`
  # fail-open convention -- this path is unattended, so silence would leave
  # a capability permanently inactive with nobody the wiser. Do not "fix"
  # this back to silent. Do NOT write STATE_FILE, so the next session retries.
  echo "capability-auto-install: gsd-tools not found; $CAP_ID not installed" >&2
else
  # D-04, same rationale as above -- install command ran and failed.
  echo "capability-auto-install: capability install failed for $CAP_ID (exit $INSTALL_STATUS)" >&2
fi

exit 0
