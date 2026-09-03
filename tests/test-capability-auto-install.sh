#!/usr/bin/env bash
# Stdlib-only smoke test (N5): no framework, no fixtures dir. Every case runs
# against scratch plugin/runtime roots. Focused cases use a stub runtime-owned
# `gsd-tools.cjs`; the final `/dev/shm` case uses the active/current CLI. This
# repo's own real $HOME/.gsd/ is never touched.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/plugins/beads-lifecycle/hooks/capability-auto-install.sh"
REAL_PYTHON="$(command -v python3)"
GSD_CORE_REPO="${GSD_CORE_REPO:-$REPO_ROOT/../gsd-core}"
ACTIVE_CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
ACTIVE_GSD_TOOLS="$ACTIVE_CODEX_HOME/gsd-core/bin/gsd-tools.cjs"

fail() { echo "FAIL: $1"; exit 1; }
pass() { echo "PASS: $1"; }

if command -v sha256sum >/dev/null 2>&1; then
  TEST_HASH_CMD=(sha256sum)
else
  TEST_HASH_CMD=(shasum -a 256)
fi

trap '[ -n "${SCRATCH:-}" ] && rm -rf "$SCRATCH" 2>/dev/null' EXIT

# setup <stub-exit-status>
# Builds a scratch plugin root with a fake .gsd/capabilities/beads/ bundle, a
# scratch GSD_HOME (so the sidecar state file never touches the real $HOME),
# and a stub runtime-owned `gsd-tools.cjs` that logs its argv and exits with the
# given status. Sets SCRATCH, PLUGIN_DIR, BUNDLE_DIR, GSD_HOME, BIN_DIR,
# STUB_LOG, STATE_FILE, SKILLS_ROOT.
setup() {
  SCRATCH="$(mktemp -d)"
  CODEX_HOME="$SCRATCH/.codex"
  CLAUDE_CONFIG_DIR="$SCRATCH/.claude"
  PLUGIN_DIR="$CODEX_HOME/plugins/cache/gsd-beads/beads-lifecycle/test"
  BUNDLE_DIR="$PLUGIN_DIR/.gsd/capabilities/beads"
  mkdir -p "$(dirname "$BUNDLE_DIR")"
  cp -rf "$REPO_ROOT/plugins/beads-lifecycle/.gsd/capabilities/beads" "$BUNDLE_DIR"

  GSD_HOME="$SCRATCH/home"
  mkdir -p "$GSD_HOME"
  INSTALLED_BUNDLE="$GSD_HOME/.gsd/capabilities/beads"
  mkdir -p "$(dirname "$INSTALLED_BUNDLE")"
  cp -rf "$BUNDLE_DIR" "$INSTALLED_BUNDLE"
  STATE_FILE="$GSD_HOME/.gsd/capability-auto-install-beads.projections"
  LEGACY_STATE_FILE="$GSD_HOME/.gsd/capability-auto-install-beads.hash"
  SKILLS_ROOT="$SCRATCH/.agents/skills"
  CLAUDE_SKILLS_ROOT="$SCRATCH/.claude/skills"
  mkdir -p "$SKILLS_ROOT" "$CLAUDE_SKILLS_ROOT"

  BIN_DIR="$CODEX_HOME/gsd-core/bin"
  mkdir -p "$BIN_DIR"
  TEST_BIN="$SCRATCH/test-bin"
  mkdir -p "$TEST_BIN"
  STUB_LOG="$SCRATCH/stub.log"
  : > "$STUB_LOG"
  local stub_status="${1:-0}"
  cat > "$BIN_DIR/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$STUB_LOG"
case "\$*" in
  *"--runtime codex"*) [ "\${GSD_RUNTIME:-}" = "codex" ] || exit 64 ;;
  *"--runtime claude"*) [ "\${GSD_RUNTIME:-}" = "claude" ] || exit 64 ;;
esac
if [ "\$*" = "query skills-root codex --raw" ]; then
  printf '%s\n' "$SKILLS_ROOT"
  exit 0
elif [ "\$*" = "query skills-root claude --raw" ]; then
  printf '%s\n' "$CLAUDE_SKILLS_ROOT"
  exit 0
elif [ "\$*" = "capability set beads --runtime codex --scope global --config-dir $CODEX_HOME" ]; then
  _target="$SKILLS_ROOT"
elif [ "\$*" = "capability set beads --runtime claude --scope global --config-dir $CLAUDE_CONFIG_DIR" ]; then
  _target="$CLAUDE_SKILLS_ROOT"
else
  _target=""
fi
exit $stub_status
STUB
  chmod +x "$BIN_DIR/gsd-tools.cjs"
  mkdir -p "$CLAUDE_CONFIG_DIR/gsd-core/bin"
  cp -f "$BIN_DIR/gsd-tools.cjs" "$CLAUDE_CONFIG_DIR/gsd-core/bin/gsd-tools.cjs"

  STDOUT_FILE="$SCRATCH/stdout"
  STDERR_FILE="$SCRATCH/stderr"
  TEST_PYTHONPATH=""
  R1_LOCK_SPY_LOG=""
  R2_PUBLISH_SPY_LOG=""
  R2_LEGACY_PATH=""
  R2_LEDGER_PATH=""
  R2_REPLACE_FAIL=""
  R2_REPLACE_READY=""
  R2_REPLACE_RELEASE=""
}

seed_selected() {
  local _root="$1" _source _dest
  for _source in "$BUNDLE_DIR"/skills/*; do
    _dest="$_root/gsd-$(basename "$_source")"
    rm -rf "$_dest"
    cp -rf "$_source" "$_dest"
    printf '%s\n' beads > "$_dest/.gsd-capability-skill"
  done
}

sync_installed_fixture() {
  rm -rf "$INSTALLED_BUNDLE"
  cp -rf "$BUNDLE_DIR" "$INSTALLED_BUNDLE"
}

fixture_tree_hash() {
  "$REAL_PYTHON" - "$@" <<'PY'
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
            entries[path.relative_to(root).as_posix()] = path
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

teardown() {
  rm -rf "$SCRATCH" 2>/dev/null
}

# run_script <capability-id> -- invokes SCRIPT with the stub active-runtime tool,
# capturing stdout/stderr to STDOUT_FILE/STDERR_FILE and STATUS.
run_script() {
  HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" GSD_RUNTIME="${GSD_RUNTIME:-}" \
    PYTHONPATH="${TEST_PYTHONPATH:-}" R1_LOCK_SPY_LOG="${R1_LOCK_SPY_LOG:-}" \
    R2_PUBLISH_SPY_LOG="${R2_PUBLISH_SPY_LOG:-}" R2_LEGACY_PATH="${R2_LEGACY_PATH:-}" \
    R2_LEDGER_PATH="${R2_LEDGER_PATH:-}" PYTHONDONTWRITEBYTECODE=1 \
    R2_REPLACE_FAIL="${R2_REPLACE_FAIL:-}" R2_REPLACE_READY="${R2_REPLACE_READY:-}" \
    R2_REPLACE_RELEASE="${R2_REPLACE_RELEASE:-}" PATH="$TEST_BIN:/usr/bin:/bin" \
    bash "$SCRIPT" "$1" >"$STDOUT_FILE" 2>"$STDERR_FILE"
  STATUS=$?
}

### Slice 1: compatibility, runtime mapping, and exact native argv ###
python3 - "$REPO_ROOT/plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json" \
  "$REPO_ROOT/README.md" <<'PY'
import json
import pathlib
import sys

manifest_path, readme_path = map(pathlib.Path, sys.argv[1:])
manifest = json.loads(manifest_path.read_text())
if manifest["engines"]["gsd"] != ">=1.10.0":
    raise SystemExit("manifest does not require gsd-core >=1.10.0")
if "gsd-core >= 1.10.0" not in readme_path.read_text():
    raise SystemExit("README does not state gsd-core >= 1.10.0")
PY
setup 0
seed_selected "$SKILLS_ROOT"

# Case 1: first run, no prior sidecar state -> installs once, prints notice.
run_script beads
[ "$STATUS" -eq 0 ] || fail "case1: exit status $STATUS, expected 0"
[ "$(cat "$STDOUT_FILE")" = "Auto-installed capability: beads (user scope)" ] \
  || fail "case1: stdout notice mismatch: $(cat "$STDOUT_FILE")"
[ "$(wc -l < "$STUB_LOG")" -eq 3 ] || fail "case1: stub invoked $(wc -l < "$STUB_LOG") times, expected 3"
grep -qx 'query skills-root codex --raw' "$STUB_LOG" \
  || fail "case1: public Codex skills-root query was not invoked"
grep -qF "$BUNDLE_DIR" "$STUB_LOG" || fail "case1: stub argv missing absolute bundle path"
grep -q 'capability' "$STUB_LOG" || fail "case1: stub argv missing 'capability'"
grep -q 'install' "$STUB_LOG" || fail "case1: stub argv missing 'install'"
grep -q -- '--yes' "$STUB_LOG" || fail "case1: stub argv missing '--yes'"
grep -q 'global' "$STUB_LOG" || fail "case1: stub argv missing 'global' scope value"
grep -qx "capability set beads --runtime codex --scope global --config-dir $CODEX_HOME" "$STUB_LOG" \
  || fail "case1: native codex surface materialization was not invoked"
[ -f "$SKILLS_ROOT/gsd-beads-recall/.gsd-capability-skill" ] \
  || fail "case1: current-layout install did not project the recall skill"
[ -f "$STATE_FILE" ] || fail "case1: sidecar state file not created"
python3 - "$STATE_FILE" <<'PY'
import pathlib
import re
import sys

rows = pathlib.Path(sys.argv[1]).read_text().splitlines()
if len(rows) != 1 or not re.fullmatch(r"projection-v2 codex [0-9a-f]{64} [0-9a-f]{64}", rows[0]):
    raise SystemExit(f"invalid projection ledger: {rows!r}")
PY
pass "case1: first-run auto-install prints notice, installs once, writes sidecar"

# Case 2: unchanged rerun -> completely silent, zero native writer invocations.
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case2: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case2: stdout not empty on unchanged rerun"
[ -z "$(cat "$STDERR_FILE")" ] || fail "case2: stderr not empty on unchanged rerun"
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 1)) ] || fail "case2: unchanged rerun invoked a native writer"
[ "$(tail -n 1 "$STUB_LOG")" = 'query skills-root codex --raw' ] || fail "case2: unchanged rerun did more than validate its destination"
pass "case2: unchanged rerun is silent and invokes native writers zero times"

### Case 2b: selected-surface drift invalidates the fingerprint fast path ###
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
printf '\n' >> "$SKILLS_ROOT/gsd-beads-status/SKILL.md"
run_script beads
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 3)) ] \
  || fail "case2b: selected fingerprint drift did not invoke both native writers"
pass "case2b: observed selected-surface drift invalidates the fast path"

# Case 3: bundle edit -> re-grant with a fresh notice.
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
printf '\n' >> "$BUNDLE_DIR/capability.json"
sync_installed_fixture
run_script beads
[ "$STATUS" -eq 0 ] || fail "case3: exit status $STATUS, expected 0"
[ "$(cat "$STDOUT_FILE")" = "Auto-installed capability: beads (user scope)" ] \
  || fail "case3: stdout notice mismatch after edit: $(cat "$STDOUT_FILE")"
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 3)) ] \
  || fail "case3: stub invoked $(wc -l < "$STUB_LOG") times after edit, expected $((PREV_LOG_LINES + 3))"
pass "case3: bundle edit re-grants with a fresh notice"

teardown

### Case 3b: a validated explicit runtime overrides plugin-owner fallback ###
setup 0
seed_selected "$CLAUDE_SKILLS_ROOT"
export GSD_RUNTIME=claude
run_script beads
unset GSD_RUNTIME
grep -qx 'query skills-root claude --raw' "$STUB_LOG" \
  || fail "case3b: explicit Claude runtime did not select the Claude skills-root query"
grep -qx "capability set beads --runtime claude --scope global --config-dir $CLAUDE_CONFIG_DIR" "$STUB_LOG" \
  || fail "case3b: explicit Claude runtime did not select the Claude config root"
pass "case3b: validated explicit runtime selects exactly one runtime/config/destination"
teardown

### Case 3c: a noncanonical queried root blocks both native mutations ###
setup 0
cat > "$BIN_DIR/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$STUB_LOG"
[ "\$*" != "query skills-root codex --raw" ] || printf '%s\n' "$SCRATCH/wrong-skills-root"
exit 0
STUB
chmod +x "$BIN_DIR/gsd-tools.cjs"
run_script beads
[ "$(wc -l < "$STUB_LOG")" -eq 1 ] || fail "case3c: noncanonical root reached a native mutation"
grep -q 'skills-root query failed' "$STDERR_FILE" || fail "case3c: missing skills-root diagnostic"
[ ! -e "$STATE_FILE" ] || fail "case3c: noncanonical root wrote convergence state"
pass "case3c: noncanonical public skills root blocks install and set"
teardown

### Case 3d: a retired selected command prevents certification after native set ###
setup 0
seed_selected "$SKILLS_ROOT"
printf '\npython3 "$SYNC_PY" execute-plan\n' >> "$SKILLS_ROOT/gsd-beads-recall/SKILL.md"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case3d: exit status $STATUS, expected 0"
grep -q 'selected command contract verification failed' "$STDERR_FILE" \
  || fail "case3d: retired selected command was certified"
[ ! -e "$STATE_FILE" ] || fail "case3d: sidecar recorded an invalid selected command"
pass "case3d: selected command verification rejects retired execute-plan"
teardown

### Case 4: install-failure path (D-04, CAP-05) -- stub gsd-tools exits 1 ###
setup 1
run_script beads
[ "$STATUS" -eq 0 ] || fail "case4: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case4: stdout carried a notice on install failure"
CASE4_STDERR="$(cat "$STDERR_FILE")"
[ "$(wc -l < "$STDERR_FILE")" -eq 1 ] || fail "case4: stderr line count $(wc -l < "$STDERR_FILE"), expected 1"
echo "$CASE4_STDERR" | grep -q 'beads' || fail "case4: stderr does not name the capability id"
[ ! -e "$STATE_FILE" ] || fail "case4: sidecar state file was created despite install failure"
pass "case4: install-failure path warns once, exits 0, writes no sidecar"
teardown

### Case 5: no-tool path (exit 127) -- gsd-tools unresolvable by any branch ###
SCRATCH="$(mktemp -d)"
PLUGIN_DIR="$SCRATCH/.codex/plugins/cache/gsd-beads/beads-lifecycle/test"
BUNDLE_DIR="$PLUGIN_DIR/.gsd/capabilities/beads"
mkdir -p "$BUNDLE_DIR"
printf '{"id":"beads"}\n' > "$BUNDLE_DIR/capability.json"
GSD_HOME="$SCRATCH/home"
mkdir -p "$GSD_HOME"
STATE_FILE="$GSD_HOME/.gsd/capability-auto-install-beads.projections"
LEGACY_STATE_FILE="$GSD_HOME/.gsd/capability-auto-install-beads.hash"
CONFIG_DIR="$SCRATCH/no-gsd-core-here"
mkdir -p "$CONFIG_DIR"
WORKDIR="$SCRATCH/workdir"
mkdir -p "$WORKDIR"
STDOUT_FILE="$SCRATCH/stdout"
STDERR_FILE="$SCRATCH/stderr"
(
  cd "$WORKDIR" && \
  HOME="$SCRATCH" PATH="/usr/bin:/bin" \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" \
    CLAUDE_CONFIG_DIR="$CONFIG_DIR" \
    bash "$SCRIPT" beads >"$STDOUT_FILE" 2>"$STDERR_FILE"
)
STATUS=$?
[ "$STATUS" -eq 0 ] || fail "case5: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case5: stdout carried a notice with no gsd-tools resolvable"
CASE5_STDERR="$(cat "$STDERR_FILE")"
[ "$(wc -l < "$STDERR_FILE")" -eq 1 ] || fail "case5: stderr line count $(wc -l < "$STDERR_FILE"), expected 1"
[ "$CASE5_STDERR" != "$CASE4_STDERR" ] || fail "case5: no-tool stderr text matches install-failure stderr text (must be distinguishable)"
[ ! -e "$STATE_FILE" ] || fail "case5: sidecar state file was created despite no gsd-tools"
pass "case5: no-tool path warns once with distinct text, exits 0, writes no sidecar"
rm -rf "$SCRATCH" 2>/dev/null

### Case 6: plugin-root resolution parity (Pitfall 3) ###
# Same fixed plugin/bundle dir for both runs (byte-identical stub argv); each
# run gets its own fresh GSD_HOME so both see "no prior hash" and both print
# the notice. Each run's cwd is a scratch dir that is not the plugin root.
PARITY_ROOT="$(mktemp -d)"
PARITY_PLUGIN="$PARITY_ROOT/.codex/plugins/cache/gsd-beads/beads-lifecycle/test"
PARITY_BUNDLE="$PARITY_PLUGIN/.gsd/capabilities/beads"
mkdir -p "$(dirname "$PARITY_BUNDLE")"
cp -rf "$REPO_ROOT/plugins/beads-lifecycle/.gsd/capabilities/beads" "$PARITY_BUNDLE"
PARITY_CODEX_HOME="$PARITY_ROOT/.codex"
PARITY_BIN="$PARITY_CODEX_HOME/gsd-core/bin"
mkdir -p "$PARITY_BIN"
PARITY_STUB_LOG="$PARITY_ROOT/stub.log"
: > "$PARITY_STUB_LOG"
cat > "$PARITY_BIN/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$PARITY_STUB_LOG"
case "\$*" in
  *"--runtime codex"*) [ "\${GSD_RUNTIME:-}" = "codex" ] || exit 64 ;;
esac
[ "\$*" != "query skills-root codex --raw" ] || printf '%s\n' "$PARITY_ROOT/.agents/skills"
exit 0
STUB
chmod +x "$PARITY_BIN/gsd-tools.cjs"
mkdir -p "$PARITY_ROOT/.agents/skills"
for _source in "$PARITY_BUNDLE"/skills/*; do
  _dest="$PARITY_ROOT/.agents/skills/gsd-$(basename "$_source")"
  cp -rf "$_source" "$_dest"
  printf '%s\n' beads > "$_dest/.gsd-capability-skill"
done

CWD_A="$PARITY_ROOT/cwd-a"; mkdir -p "$CWD_A"
CWD_B="$PARITY_ROOT/cwd-b"; mkdir -p "$CWD_B"
GSD_HOME_A="$PARITY_ROOT/home-a"; mkdir -p "$GSD_HOME_A"
GSD_HOME_B="$PARITY_ROOT/home-b"; mkdir -p "$GSD_HOME_B"
mkdir -p "$GSD_HOME_A/.gsd/capabilities" "$GSD_HOME_B/.gsd/capabilities"
cp -rf "$PARITY_BUNDLE" "$GSD_HOME_A/.gsd/capabilities/beads"
cp -rf "$PARITY_BUNDLE" "$GSD_HOME_B/.gsd/capabilities/beads"

OUT_SET_FILE="$PARITY_ROOT/out-set"
ERR_SET_FILE="$PARITY_ROOT/err-set"
# Run 1: CLAUDE_PLUGIN_ROOT exported explicitly.
(
  cd "$CWD_A" && \
  HOME="$PARITY_ROOT" CODEX_HOME="$PARITY_CODEX_HOME" \
    CLAUDE_PLUGIN_ROOT="$PARITY_PLUGIN" GSD_HOME="$GSD_HOME_A" \
    bash "$SCRIPT" beads >"$OUT_SET_FILE" 2>"$ERR_SET_FILE"
)
STATUS_SET=$?
[ "$STATUS_SET" -eq 0 ] || fail "case6: CLAUDE_PLUGIN_ROOT-set run exited $STATUS_SET, expected 0"

PARITY_SCRIPT_COPY="$PARITY_PLUGIN/hooks/capability-auto-install.sh"
mkdir -p "$PARITY_PLUGIN/hooks"
cp "$SCRIPT" "$PARITY_SCRIPT_COPY"
OUT_UNSET_FILE="$PARITY_ROOT/out-unset"
ERR_UNSET_FILE="$PARITY_ROOT/err-unset"
(
  cd "$CWD_B" && \
  HOME="$PARITY_ROOT" CODEX_HOME="$PARITY_CODEX_HOME" \
    GSD_HOME="$GSD_HOME_B" \
    env -u CLAUDE_PLUGIN_ROOT bash "$PARITY_SCRIPT_COPY" beads >"$OUT_UNSET_FILE" 2>"$ERR_UNSET_FILE"
)
STATUS_UNSET=$?
[ "$STATUS_UNSET" -eq 0 ] || fail "case6: CLAUDE_PLUGIN_ROOT-unset run exited $STATUS_UNSET, expected 0"

[ "$(cat "$OUT_SET_FILE")" = "$(cat "$OUT_UNSET_FILE")" ] || fail "case6: stdout differs between CLAUDE_PLUGIN_ROOT set/unset runs"
[ "$(cat "$ERR_SET_FILE")" = "$(cat "$ERR_UNSET_FILE")" ] || fail "case6: stderr differs between CLAUDE_PLUGIN_ROOT set/unset runs"
[ "$(wc -l < "$PARITY_STUB_LOG")" -eq 6 ] || fail "case6: expected exactly 6 stub invocations across both runs, got $(wc -l < "$PARITY_STUB_LOG")"
pass "case6: CLAUDE_PLUGIN_ROOT set vs. derived-from-\$0 produce byte-identical output"
rm -rf "$PARITY_ROOT" 2>/dev/null

### Case 7: legacy raw-hash sidecar forces one reconciliation, then converges ###
setup 0
seed_selected "$SKILLS_ROOT"
LEGACY_HASH="$({
  find "$BUNDLE_DIR" \( -type f -o -type d \) | LC_ALL=C sort
  find "$BUNDLE_DIR" -type f | LC_ALL=C sort | while IFS= read -r _f; do cat "$_f"; done
} | "${TEST_HASH_CMD[@]}" | awk '{print $1}')"
mkdir -p "$(dirname "$STATE_FILE")"
printf '%s\n' "$LEGACY_HASH" > "$LEGACY_STATE_FILE"
mkdir -p "$SKILLS_ROOT/gsd-user-owned" \
  "$SKILLS_ROOT/plain-user-skill" "$SKILLS_ROOT/gsd-other-plugin" \
  "$CLAUDE_SKILLS_ROOT/gsd-beads-recall"
printf 'user-owned\n' > "$SKILLS_ROOT/gsd-user-owned/SKILL.md"
printf 'plain-user\n' > "$SKILLS_ROOT/plain-user-skill/SKILL.md"
printf 'other\n' > "$SKILLS_ROOT/gsd-other-plugin/.gsd-capability-skill"
printf 'other-plugin\n' > "$SKILLS_ROOT/gsd-other-plugin/SKILL.md"
printf 'other-runtime-stale\n' > "$CLAUDE_SKILLS_ROOT/gsd-beads-recall/SKILL.md"
USER_OWNED_BEFORE="$(cksum "$SKILLS_ROOT/gsd-user-owned/SKILL.md")"
PLAIN_USER_BEFORE="$(cksum "$SKILLS_ROOT/plain-user-skill/SKILL.md")"
OTHER_PLUGIN_BEFORE="$(find "$SKILLS_ROOT/gsd-other-plugin" -type f -exec cksum {} + | LC_ALL=C sort | cksum)"
OTHER_RUNTIME_BEFORE="$(cksum "$CLAUDE_SKILLS_ROOT/gsd-beads-recall/SKILL.md")"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case7: exit status $STATUS, expected 0"
[ "$(wc -l < "$STUB_LOG")" -eq 3 ] || fail "case7: legacy sidecar did not trigger root validation and native reconciliation"
[ -f "$STATE_FILE" ] || fail "case7: convergence sidecar was not written"
[ ! -e "$LEGACY_STATE_FILE" ] || fail "case7: verified v2 publication retained the legacy receipt"
grep -Eq "^projection-v2 codex [0-9a-f]{64} [0-9a-f]{64}$" "$STATE_FILE" || fail "case7: codex convergence record missing"
grep -qx "capability set beads --runtime codex --scope global --config-dir $CODEX_HOME" "$STUB_LOG" \
  || fail "case7: stale projection was not delegated to native reconciliation"
! grep -q 'check-patch execute-plan' "$SKILLS_ROOT/gsd-beads-recall/SKILL.md" \
  || fail "case7: retired execute-plan command remains selected after reconciliation"
[ "$USER_OWNED_BEFORE" = "$(cksum "$SKILLS_ROOT/gsd-user-owned/SKILL.md")" ] \
  || fail "case7: user-owned skill changed"
[ "$PLAIN_USER_BEFORE" = "$(cksum "$SKILLS_ROOT/plain-user-skill/SKILL.md")" ] \
  || fail "case7: non-gsd skill changed"
[ "$OTHER_PLUGIN_BEFORE" = "$(find "$SKILLS_ROOT/gsd-other-plugin" -type f -exec cksum {} + | LC_ALL=C sort | cksum)" ] \
  || fail "case7: other capability skill changed"
[ "$OTHER_RUNTIME_BEFORE" = "$(cksum "$CLAUDE_SKILLS_ROOT/gsd-beads-recall/SKILL.md")" ] \
  || fail "case7: other-runtime state changed"
PROJECTED_TREE_BEFORE="$(find "$SKILLS_ROOT" -type f -exec cksum {} + | LC_ALL=C sort | cksum)"
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
run_script beads
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 1)) ] || fail "case7: migrated sidecar invoked a native writer"
[ "$(tail -n 1 "$STUB_LOG")" = 'query skills-root codex --raw' ] || fail "case7: migrated sidecar did more than validate its destination"
[ "$PROJECTED_TREE_BEFORE" = "$(find "$SKILLS_ROOT" -type f -exec cksum {} + | LC_ALL=C sort | cksum)" ] \
  || fail "case7: repeated update changed the projected tree"

CLAUDE_PLUGIN="$SCRATCH/.claude/plugins/cache/gsd-beads/beads-lifecycle/test"
mkdir -p "$CLAUDE_PLUGIN/.gsd/capabilities"
cp -rf "$REPO_ROOT/plugins/beads-lifecycle/.gsd/capabilities/beads" "$CLAUDE_PLUGIN/.gsd/capabilities/beads"
printf 'beads\n' > "$CLAUDE_SKILLS_ROOT/gsd-beads-recall/.gsd-capability-skill"
PLUGIN_DIR="$CLAUDE_PLUGIN"
BUNDLE_DIR="$CLAUDE_PLUGIN/.gsd/capabilities/beads"
seed_selected "$CLAUDE_SKILLS_ROOT"
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
run_script beads
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 3)) ] \
  || fail "case7: codex convergence incorrectly suppressed claude reconciliation"
grep -qx "capability set beads --runtime claude --scope global --config-dir $CLAUDE_CONFIG_DIR" "$STUB_LOG" \
  || fail "case7: native claude surface materialization was not invoked"
grep -Eq "^projection-v2 codex [0-9a-f]{64} [0-9a-f]{64}$" "$STATE_FILE" || fail "case7: codex convergence record was lost"
grep -Eq "^projection-v2 claude [0-9a-f]{64} [0-9a-f]{64}$" "$STATE_FILE" || fail "case7: claude convergence record missing"
[ "$(sed -n '1p' "$STATE_FILE")" != "$(sed -n '2p' "$STATE_FILE")" ] || fail "case7: ledger contains duplicate rows"
[ "$(sed -n '1p' "$STATE_FILE" | cut -d' ' -f2)" = claude ] || fail "case7: ledger is not sorted by runtime"
[ "$(sed -n '2p' "$STATE_FILE" | cut -d' ' -f2)" = codex ] || fail "case7: ledger is not sorted by runtime"
! grep -q 'check-patch execute-plan' "$CLAUDE_SKILLS_ROOT/gsd-beads-recall/SKILL.md" \
  || fail "case7: claude stale projection remained selected"

PLUGIN_DIR="$CODEX_HOME/plugins/cache/gsd-beads/beads-lifecycle/test"
BUNDLE_DIR="$PLUGIN_DIR/.gsd/capabilities/beads"
printf '\n' >> "$BUNDLE_DIR/capability.json"
sync_installed_fixture
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
run_script beads
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 3)) ] \
  || fail "case7: changed global generation did not reconcile Codex"
[ "$(wc -l < "$STATE_FILE")" -eq 1 ] || fail "case7: changed generation retained a stale runtime row"
grep -Eq "^projection-v2 codex [0-9a-f]{64} [0-9a-f]{64}$" "$STATE_FILE" \
  || fail "case7: changed generation did not publish the completed Codex row"
pass "case7: legacy sidecar reconciles once per runtime and each runtime converges"
teardown

### Case 8: install success plus surface failure leaves no converged sidecar ###
setup 0
mkdir -p "$(dirname "$LEGACY_STATE_FILE")"
printf '%s\n' legacy-retry-sentinel > "$LEGACY_STATE_FILE"
cat > "$BIN_DIR/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$STUB_LOG"
[ "\$*" != "capability set beads --runtime codex --scope global --config-dir $CODEX_HOME" ] \
  || [ "\${GSD_RUNTIME:-}" = "codex" ] \
  || exit 64
[ "\$*" = "capability set beads --runtime codex --scope global --config-dir $CODEX_HOME" ] && exit 1
[ "\$*" = "query skills-root codex --raw" ] && printf '%s\n' "$SKILLS_ROOT"
exit 0
STUB
chmod +x "$BIN_DIR/gsd-tools.cjs"
seed_selected "$SKILLS_ROOT"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case8: exit status $STATUS, expected 0"
[ "$(wc -l < "$STUB_LOG")" -eq 3 ] || fail "case8: expected root validation, install, and surface invocations"
grep -q 'capability set failed' "$STDERR_FILE" || fail "case8: missing projection-failure diagnostic"
[ ! -e "$STATE_FILE" ] || fail "case8: sidecar was created despite surface failure"
[ "$(cat "$LEGACY_STATE_FILE")" = legacy-retry-sentinel ] || fail "case8: failed migration changed legacy retry state"
pass "case8: projection failure warns, retries later, and never records false convergence"
teardown

### Case 9: an unmarked same-name user skill is preserved and blocks convergence ###
setup 0
rm -rf "$SKILLS_ROOT/gsd-beads-recall"
mkdir -p "$SKILLS_ROOT/gsd-beads-recall"
printf 'user-owned same-name\n' > "$SKILLS_ROOT/gsd-beads-recall/SKILL.md"
SAME_NAME_BEFORE="$(cksum "$SKILLS_ROOT/gsd-beads-recall/SKILL.md")"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case9: exit status $STATUS, expected 0"
[ "$SAME_NAME_BEFORE" = "$(cksum "$SKILLS_ROOT/gsd-beads-recall/SKILL.md")" ] \
  || fail "case9: unmarked same-name user skill changed"
[ "$(wc -l < "$STUB_LOG")" -eq 1 ] || fail "case9: ownership conflict reached a native mutation"
grep -q 'destination ownership check failed' "$STDERR_FILE" \
  || fail "case9: missing ownership diagnostic"
[ ! -e "$STATE_FILE" ] || fail "case9: sidecar recorded convergence over a user-owned collision"
pass "case9: same-name user-owned skill is preserved and convergence fails closed"
teardown

### Case 10: every command declared by the selected recall skill is accepted ###
ACTIVE_SYNC="$REPO_ROOT/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py"
setup 0
seed_selected "$SKILLS_ROOT"
run_script beads
SELECTED_RECALL="$SKILLS_ROOT/gsd-beads-recall/SKILL.md"
! grep -q 'check-patch execute-plan' "$SELECTED_RECALL" \
  || fail "case10: selected recall skill declares retired execute-plan"
python3 - "$ACTIVE_SYNC" "$SELECTED_RECALL" <<'PY'
import pathlib
import re
import shlex
import subprocess
import sys

sync_py, skill_path = map(pathlib.Path, sys.argv[1:])
declared = re.findall(r'^python3 "\$SYNC_PY" (.+)$', skill_path.read_text(), re.MULTILINE)
if not declared:
    raise SystemExit("selected recall skill declares no sync.py commands")
for command in declared:
    prefix = []
    for token in shlex.split(command):
        if "<" in token or "[" in token:
            break
        prefix.append(token)
    result = subprocess.run(
        [sys.executable, str(sync_py), *prefix, "--help"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"active CLI rejected {prefix!r}: {result.stderr}")
PY
pass "case10: every selected recall command is accepted by the active capability CLI"
teardown

### Case 11: an unidentifiable custom plugin root fails closed ###
setup 0
CUSTOM_PLUGIN="$SCRATCH/custom-plugin-root"
mkdir -p "$CUSTOM_PLUGIN/.gsd/capabilities"
cp -rf "$REPO_ROOT/plugins/beads-lifecycle/.gsd/capabilities/beads" "$CUSTOM_PLUGIN/.gsd/capabilities/beads"
PLUGIN_DIR="$CUSTOM_PLUGIN"
BUNDLE_DIR="$CUSTOM_PLUGIN/.gsd/capabilities/beads"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case11: exit status $STATUS, expected 0"
[ "$(wc -l < "$STUB_LOG")" -eq 0 ] || fail "case11: unknown runtime invoked gsd-tools"
grep -q 'runtime selection failed' "$STDERR_FILE" \
  || fail "case11: missing unknown-runtime diagnostic"
pass "case11: unknown custom root fails closed without guessing a runtime"
teardown

### Case 12: acquisition is one kernel flock inherited across same-process re-exec ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
: > "$STATE_FILE.lock"
SPY_DIR="$SCRATCH/lock-spy"
mkdir -p "$SPY_DIR"
cat > "$SPY_DIR/sitecustomize.py" <<'PY'
import fcntl
import os

_log_path = os.environ["R1_LOCK_SPY_LOG"]
_real_flock = fcntl.flock
_real_set_inheritable = os.set_inheritable
_real_execvpe = os.execvpe

def _append(value):
    with open(_log_path, "a", encoding="utf-8") as stream:
        stream.write(value + "\n")

def _flock(fd, operation):
    _append(f"flock:{operation}")
    return _real_flock(fd, operation)

def _set_inheritable(fd, inheritable):
    _append(f"inheritable:{int(inheritable)}")
    return _real_set_inheritable(fd, inheritable)

def _execvpe(file, args, env):
    _append(f"execvpe:{file}")
    return _real_execvpe(file, args, env)

fcntl.flock = _flock
os.set_inheritable = _set_inheritable
os.execvpe = _execvpe
PY
R1_LOCK_SPY_LOG="$SCRATCH/lock-spy.log"
TEST_PYTHONPATH="$SPY_DIR"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case12: exit status $STATUS, expected 0"
[ -f "$STATE_FILE.lock" ] && [ ! -L "$STATE_FILE.lock" ] \
  || fail "case12: lock path is not a persistent regular file"
[ "$(grep -cx 'flock:6' "$R1_LOCK_SPY_LOG")" -eq 1 ] \
  || fail "case12: acquisition did not perform exactly one nonblocking exclusive flock"
[ "$(grep -cx 'inheritable:1' "$R1_LOCK_SPY_LOG")" -eq 1 ] \
  || fail "case12: acquired descriptor was not made inheritable once"
[ "$(grep -cx 'execvpe:bash' "$R1_LOCK_SPY_LOG")" -eq 1 ] \
  || fail "case12: acquisition did not re-exec the hook in the same process"
pass "case12: one kernel flock spans same-process hook re-exec"
teardown

### Case 13: symlink lock targets fail closed without native writes ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
LOCK_SENTINEL="$SCRATCH/lock-sentinel"
printf '%s\n' preserved > "$LOCK_SENTINEL"
ln -s "$LOCK_SENTINEL" "$STATE_FILE.lock"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case13: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case13: unsafe lock emitted stdout"
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: projection lock failed for beads; projection not recorded' ] \
  || fail "case13: unsafe symlink diagnostic was not fixed and bounded"
[ "$(wc -l < "$STUB_LOG")" -eq 1 ] || fail "case13: unsafe lock reached a native writer"
[ -L "$STATE_FILE.lock" ] && [ "$(cat "$LOCK_SENTINEL")" = preserved ] \
  || fail "case13: unsafe lock target was changed"
pass "case13: symlink lock targets fail closed"
teardown

### Case 14: non-regular lock targets fail closed without native writes ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$STATE_FILE.lock"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case14: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case14: unsafe lock emitted stdout"
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: projection lock failed for beads; projection not recorded' ] \
  || fail "case14: non-regular lock diagnostic was not fixed and bounded"
[ "$(wc -l < "$STUB_LOG")" -eq 1 ] || fail "case14: unsafe lock reached a native writer"
[ -d "$STATE_FILE.lock" ] || fail "case14: unsafe lock directory was changed"
pass "case14: non-regular lock targets fail closed"
teardown

### Case 15: one regular kernel lock serializes cross-runtime hook writers ###
setup 0
seed_selected "$SKILLS_ROOT"
seed_selected "$CLAUDE_SKILLS_ROOT"
READY_FIFO="$SCRATCH/ready.fifo"
RELEASE_FIFO="$SCRATCH/release.fifo"
mkfifo "$READY_FIFO" "$RELEASE_FIFO"
cat > "$BIN_DIR/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$STUB_LOG"
if [ "\$*" = 'query skills-root codex --raw' ]; then printf '%s\n' "$SKILLS_ROOT"; exit 0; fi
if [ "\$*" = 'query skills-root claude --raw' ]; then printf '%s\n' "$CLAUDE_SKILLS_ROOT"; exit 0; fi
if [ "\$*" = 'capability install $BUNDLE_DIR --scope global --yes' ]; then
  printf '%s\n' ready > "$READY_FIFO"
  IFS= read -r _release < "$RELEASE_FIFO"
fi
exit 0
STUB
chmod +x "$BIN_DIR/gsd-tools.cjs"
cp -f "$BIN_DIR/gsd-tools.cjs" "$CLAUDE_CONFIG_DIR/gsd-core/bin/gsd-tools.cjs"
HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" \
  PATH="$TEST_BIN:/usr/bin:/bin" bash "$SCRIPT" beads >"$SCRATCH/first.out" 2>"$SCRATCH/first.err" &
FIRST_HOOK_PID=$!
IFS= read -r READY_SIGNAL < "$READY_FIFO"
[ "$READY_SIGNAL" = ready ] || fail "case15: first hook did not reach the deterministic rendezvous"
[ -f "$STATE_FILE.lock" ] && [ ! -L "$STATE_FILE.lock" ] \
  || fail "case15: live owner did not hold a regular lock file"
WRITERS_BEFORE="$(grep -Ec '^capability (install|set)' "$STUB_LOG")"
export GSD_RUNTIME=claude
run_script beads
unset GSD_RUNTIME
[ "$STATUS" -eq 0 ] || fail "case15: contender exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case15: contender emitted stdout"
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: projection transaction busy for beads; projection not recorded' ] \
  || fail "case15: contender diagnostic was not fixed and bounded"
[ "$(grep -Ec '^capability (install|set)' "$STUB_LOG")" -eq "$WRITERS_BEFORE" ] \
  || fail "case15: live contender reached a native writer"
printf '%s\n' release > "$RELEASE_FIFO"
wait "$FIRST_HOOK_PID"
[ -f "$STATE_FILE.lock" ] && [ ! -L "$STATE_FILE.lock" ] \
  || fail "case15: completed owner did not preserve the regular lock inode"
run_script beads
[ -z "$(cat "$STDOUT_FILE")" ] && [ -z "$(cat "$STDERR_FILE")" ] \
  || fail "case15: later invocation did not converge silently"
pass "case15: kernel lock serializes runtime participants without polling"
teardown

### Case 16: SIGKILL releases the inherited hook lock without stale recovery ###
setup 0
seed_selected "$SKILLS_ROOT"
CRASH_READY_FIFO="$SCRATCH/crash-ready.fifo"
CRASH_RELEASE_FIFO="$SCRATCH/crash-release.fifo"
CRASH_PID_FIFO="$SCRATCH/crash-pid.fifo"
CRASH_ONCE="$SCRATCH/crash-once"
CRASH_FD_LEAK="$SCRATCH/crash-fd-leak"
mkfifo "$CRASH_READY_FIFO" "$CRASH_RELEASE_FIFO" "$CRASH_PID_FIFO"
cat > "$BIN_DIR/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$STUB_LOG"
if [ "\$*" = 'query skills-root codex --raw' ]; then printf '%s\n' "$SKILLS_ROOT"; exit 0; fi
if [ "\$*" = 'capability install $BUNDLE_DIR --scope global --yes' ]; then
  "$REAL_PYTHON" - "$CRASH_FD_LEAK" <<'PY'
import os
import pathlib
import sys

try:
    os.fstat(9)
except OSError:
    pass
else:
    pathlib.Path(sys.argv[1]).write_text("leaked\n")
PY
  if [ ! -e "$CRASH_ONCE" ]; then
    : > "$CRASH_ONCE"
    printf '%s\n' ready > "$CRASH_READY_FIFO"
    IFS= read -r _release < "$CRASH_RELEASE_FIFO"
  fi
fi
exit 0
STUB
chmod +x "$BIN_DIR/gsd-tools.cjs"
HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" \
  PATH="$TEST_BIN:/usr/bin:/bin" "$REAL_PYTHON" - "$SCRIPT" "$CRASH_PID_FIFO" \
  "$SCRATCH/crash.out" "$SCRATCH/crash.err" <<'PY' &
import os
import subprocess
import sys

script, pid_fifo, stdout_path, stderr_path = sys.argv[1:]
with open(stdout_path, "w") as stdout, open(stderr_path, "w") as stderr:
    process = subprocess.Popen(
        ["bash", script, "beads"],
        env=os.environ.copy(),
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
    )
    with open(pid_fifo, "w") as stream:
        stream.write(f"{process.pid}\n")
    raise SystemExit(process.wait())
PY
CRASH_LAUNCHER_PID=$!
IFS= read -r CRASH_HOOK_PID < "$CRASH_PID_FIFO"
IFS= read -r CRASH_READY < "$CRASH_READY_FIFO"
[ "$CRASH_READY" = ready ] || fail "case16: holder did not reach the deterministic rendezvous"
LOCK_ID_BEFORE="$("$REAL_PYTHON" -c 'import os,sys; s=os.stat(sys.argv[1]); print(f"{s.st_dev}:{s.st_ino}")' "$STATE_FILE.lock")"
kill -KILL -- "-$CRASH_HOOK_PID"
wait "$CRASH_LAUNCHER_PID" 2>/dev/null || true
run_script beads
[ "$STATUS" -eq 0 ] || fail "case16: invocation after SIGKILL exited $STATUS"
[ "$(cat "$STDOUT_FILE")" = 'Auto-installed capability: beads (user scope)' ] \
  || fail "case16: kernel did not release the hook lock after SIGKILL"
[ ! -e "$CRASH_FD_LEAK" ] || fail "case16: native writer inherited the hook lock descriptor"
[ -f "$STATE_FILE.lock" ] && [ ! -L "$STATE_FILE.lock" ] \
  || fail "case16: post-crash lock path is not a persistent regular file"
LOCK_ID_AFTER="$("$REAL_PYTHON" -c 'import os,sys; s=os.stat(sys.argv[1]); print(f"{s.st_dev}:{s.st_ino}")' "$STATE_FILE.lock")"
[ "$LOCK_ID_AFTER" = "$LOCK_ID_BEFORE" ] \
  || fail "case16: crash recovery replaced the persistent lock inode"
[ -z "$(find "$(dirname "$STATE_FILE")" -maxdepth 1 -name '*.stale.*' -print)" ] \
  || fail "case16: crash path created stale recovery artifacts"
pass "case16: SIGKILL releases the hook lock without stale recovery"
teardown

### Case 17: hostile Python/helper failure emits one fixed lock diagnostic ###
setup 0
seed_selected "$SKILLS_ROOT"
cat > "$TEST_BIN/python3" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' 'Traceback: hostile helper detail' '/secret/helper/path' >&2
exit 77
STUB
chmod +x "$TEST_BIN/python3"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case17: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case17: hostile helper emitted stdout"
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: projection lock failed for beads; projection not recorded' ] \
  || fail "case17: hostile helper detail escaped the fixed diagnostic"
[ "$(wc -l < "$STUB_LOG")" -eq 1 ] || fail "case17: lock helper failure reached a native writer"
pass "case17: hostile lock-helper output is bounded"
teardown

install_publish_spy() {
  PUBLISH_SPY_DIR="$SCRATCH/publish-spy"
  mkdir -p "$PUBLISH_SPY_DIR"
  R2_PUBLISH_SPY_LOG="$SCRATCH/publish-spy.log"
  R2_LEGACY_PATH="$LEGACY_STATE_FILE"
  R2_LEDGER_PATH="$STATE_FILE"
  TEST_PYTHONPATH="$PUBLISH_SPY_DIR"
  cat > "$PUBLISH_SPY_DIR/sitecustomize.py" <<'PY'
import os
import pathlib
import stat
import tempfile

_log_path = os.environ.get("R2_PUBLISH_SPY_LOG", "")
_ledger_path = os.environ.get("R2_LEDGER_PATH", "")
_real_fsync = os.fsync
_real_replace = os.replace
_real_temporary = tempfile.NamedTemporaryFile
_temp_identity = None


def _append(*fields):
    if not _log_path:
        return
    with open(_log_path, "a", encoding="utf-8") as stream:
        stream.write("\t".join(map(str, fields)) + "\n")


class _TemporaryProxy:
    def __init__(self, handle):
        self._handle = handle

    def __enter__(self):
        self._handle.__enter__()
        return self

    def __exit__(self, *args):
        return self._handle.__exit__(*args)

    def __getattr__(self, name):
        return getattr(self._handle, name)

    def flush(self):
        _append("flush", self._handle.name)
        return self._handle.flush()


def _temporary(*args, **kwargs):
    global _temp_identity
    handle = _real_temporary(*args, **kwargs)
    metadata = os.fstat(handle.fileno())
    _temp_identity = (metadata.st_dev, metadata.st_ino)
    _append("temp", handle.name, kwargs.get("dir", ""), kwargs.get("delete"), metadata.st_dev, metadata.st_ino)
    return _TemporaryProxy(handle)


def _fsync(fd):
    metadata = os.fstat(fd)
    if _temp_identity == (metadata.st_dev, metadata.st_ino):
        _append("fsync", fd)
    return _real_fsync(fd)


def _replace(source, destination):
    if os.fspath(destination) != _ledger_path:
        return _real_replace(source, destination)
    legacy_path = os.environ.get("R2_LEGACY_PATH", "")
    legacy = pathlib.Path(legacy_path) if legacy_path else None
    if legacy is None or not legacy.exists() or legacy.is_symlink():
        legacy_value = "unsafe-or-absent"
    else:
        legacy_value = legacy.read_bytes().hex()
    source_stat = os.lstat(source)
    _append(
        "replace",
        source,
        destination,
        legacy_value,
        stat.S_ISREG(source_stat.st_mode),
        source_stat.st_dev,
        source_stat.st_ino,
    )
    ready = os.environ.get("R2_REPLACE_READY", "")
    release = os.environ.get("R2_REPLACE_RELEASE", "")
    if ready and release:
        with open(ready, "w", encoding="utf-8") as stream:
            stream.write("ready\n")
        with open(release, "r", encoding="utf-8") as stream:
            stream.readline()
    if os.environ.get("R2_REPLACE_FAIL") == "1":
        raise OSError("hostile replacement failure\n/secret/replacement/path")
    return _real_replace(source, destination)


tempfile.NamedTemporaryFile = _temporary
os.fsync = _fsync
os.replace = _replace
PY
}

### Case 18: a symlink ownership marker blocks native mutation ###
setup 0
seed_selected "$SKILLS_ROOT"
MARKER_PATH="$SKILLS_ROOT/gsd-beads-recall/.gsd-capability-skill"
MARKER_TARGET="$SCRATCH/marker-target"
printf '%s\n' beads > "$MARKER_TARGET"
rm -f "$MARKER_PATH"
ln -s "$MARKER_TARGET" "$MARKER_PATH"
DESTINATION_BEFORE="$("${TEST_HASH_CMD[@]}" "$SKILLS_ROOT/gsd-beads-recall/SKILL.md")"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case18: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case18: symlink marker emitted stdout"
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: destination ownership check failed for beads on codex; projection not recorded' ] \
  || fail "case18: symlink marker did not produce the fixed ownership diagnostic"
[ "$(grep -Ec '^capability (install|set)' "$STUB_LOG")" -eq 0 ] \
  || fail "case18: symlink marker reached a native writer"
[ ! -e "$STATE_FILE" ] || fail "case18: symlink marker wrote convergence state"
[ -L "$MARKER_PATH" ] && [ "$(readlink "$MARKER_PATH")" = "$MARKER_TARGET" ] \
  || fail "case18: symlink ownership marker was changed"
[ "$(cat "$MARKER_TARGET")" = beads ] || fail "case18: marker target bytes changed"
[ "$("${TEST_HASH_CMD[@]}" "$SKILLS_ROOT/gsd-beads-recall/SKILL.md")" = "$DESTINATION_BEFORE" ] \
  || fail "case18: destination bytes changed"
pass "case18: symlink ownership marker fails closed before native mutation"
teardown

### Case 19: secure publisher orders tempfile, fsync, replace, then legacy cleanup ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
printf '%s\n' prior-canonical > "$STATE_FILE"
printf '%s\n' legacy-before > "$LEGACY_STATE_FILE"
install_publish_spy
run_script beads
[ "$STATUS" -eq 0 ] || fail "case19: exit status $STATUS, expected 0"
[ "$(cat "$STDOUT_FILE")" = 'Auto-installed capability: beads (user scope)' ] \
  || fail "case19: secure publication did not complete"
[ -z "$(cat "$STDERR_FILE")" ] || fail "case19: secure publication emitted stderr"
"$REAL_PYTHON" - "$R2_PUBLISH_SPY_LOG" "$STATE_FILE" "$LEGACY_STATE_FILE" <<'PY'
import pathlib
import re
import sys

log_path, ledger_path, legacy_path = map(pathlib.Path, sys.argv[1:])
lines = log_path.read_text().splitlines()
temps = [line.split("\t") for line in lines if line.startswith("temp\t")]
flushes = [line for line in lines if line.startswith("flush\t")]
fsyncs = [line for line in lines if line.startswith("fsync\t")]
replaces = [line.split("\t") for line in lines if line.startswith("replace\t")]
if len(temps) != 1 or len(flushes) != 1 or len(fsyncs) != 1 or len(replaces) != 1:
    raise SystemExit(f"unexpected publisher spy calls: {lines!r}")
if [line.split("\t", 1)[0] for line in lines] != ["temp", "flush", "fsync", "replace"]:
    raise SystemExit(f"publisher operation order is wrong: {lines!r}")
temp_name, temp_dir = pathlib.Path(temps[0][1]), pathlib.Path(temps[0][2])
source, destination, legacy_hex = pathlib.Path(replaces[0][1]), pathlib.Path(replaces[0][2]), replaces[0][3]
if temp_dir != ledger_path.parent or temp_name.parent != ledger_path.parent or temps[0][3] != "False":
    raise SystemExit("secure temporary was not created safely in the ledger directory")
if replaces[0][4] != "True" or temps[0][4:6] != replaces[0][5:7]:
    raise SystemExit("os.replace source was not the spied regular tempfile inode")
if source != temp_name or destination != ledger_path:
    raise SystemExit("os.replace did not publish the secure temporary to the ledger")
if re.fullmatch(re.escape(ledger_path.name) + r"\.\d+", temp_name.name):
    raise SystemExit("publisher retained a predictable PID-suffixed name")
if legacy_hex != b"legacy-before\n".hex():
    raise SystemExit("legacy bytes were not intact at os.replace")
if temp_name.exists() or legacy_path.exists():
    raise SystemExit("successful publication left temporary or eligible legacy state")
PY
pass "case19: secure publisher flushes and replaces before legacy cleanup"
teardown

### Case 20: replacement failure preserves canonical and legacy bytes ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
printf '%s\n' canonical-before > "$STATE_FILE"
printf '%s\n' legacy-before > "$LEGACY_STATE_FILE"
install_publish_spy
R2_REPLACE_FAIL=1
run_script beads
[ "$STATUS" -eq 0 ] || fail "case20: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case20: failed replacement emitted stdout"
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: ledger publish failed for beads on codex; projection not recorded' ] \
  || fail "case20: replacement failure diagnostic exposed helper detail"
[ "$(cat "$STATE_FILE")" = canonical-before ] \
  || fail "case20: replacement failure changed canonical bytes"
[ "$(cat "$LEGACY_STATE_FILE")" = legacy-before ] \
  || fail "case20: replacement failure changed legacy bytes"
FAILED_TEMP="$(awk -F '\t' '$1 == "temp" { print $2 }' "$R2_PUBLISH_SPY_LOG")"
[ -n "$FAILED_TEMP" ] && [ ! -e "$FAILED_TEMP" ] \
  || fail "case20: replacement failure left its secure temporary"
pass "case20: replacement failure preserves both receipts and cleans its temporary"
teardown

### Case 21: nonregular canonical ledger targets are rejected unchanged ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
LEDGER_SENTINEL="$SCRATCH/ledger-sentinel"
printf '%s\n' sentinel > "$LEDGER_SENTINEL"
ln -s "$LEDGER_SENTINEL" "$STATE_FILE"
run_script beads
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: ledger publish failed for beads on codex; projection not recorded' ] \
  || fail "case21: canonical symlink was not rejected"
[ "$(grep -Ec '^capability (install|set)' "$STUB_LOG")" -eq 0 ] \
  || fail "case21: canonical symlink reached a native writer"
[ -L "$STATE_FILE" ] && [ "$(cat "$LEDGER_SENTINEL")" = sentinel ] \
  || fail "case21: canonical symlink or target changed"
teardown

setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$STATE_FILE"
run_script beads
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: ledger publish failed for beads on codex; projection not recorded' ] \
  || fail "case21: canonical directory was not rejected"
[ "$(grep -Ec '^capability (install|set)' "$STUB_LOG")" -eq 0 ] \
  || fail "case21: canonical directory reached a native writer"
[ -d "$STATE_FILE" ] && [ -z "$(find "$STATE_FILE" -mindepth 1 -maxdepth 1 -print)" ] \
  || fail "case21: canonical directory changed"
teardown

setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
mkfifo "$STATE_FILE"
run_script beads
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: ledger publish failed for beads on codex; projection not recorded' ] \
  || fail "case21: canonical FIFO was not rejected"
[ "$(grep -Ec '^capability (install|set)' "$STUB_LOG")" -eq 0 ] \
  || fail "case21: canonical FIFO reached a native writer"
[ -p "$STATE_FILE" ] || fail "case21: canonical FIFO changed"
pass "case21: nonregular canonical ledger targets fail closed"
teardown

### Case 21b: unsafe legacy state remains untouched after canonical success ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
LEGACY_SENTINEL="$SCRATCH/legacy-sentinel"
printf '%s\n' legacy-target > "$LEGACY_SENTINEL"
ln -s "$LEGACY_SENTINEL" "$LEGACY_STATE_FILE"
install_publish_spy
run_script beads
[ "$(cat "$STDOUT_FILE")" = 'Auto-installed capability: beads (user scope)' ] \
  || fail "case21b: unsafe legacy state blocked canonical publication"
[ -z "$(cat "$STDERR_FILE")" ] || fail "case21b: unsafe legacy state emitted stderr"
[ -L "$LEGACY_STATE_FILE" ] && [ "$(cat "$LEGACY_SENTINEL")" = legacy-target ] \
  || fail "case21b: unsafe legacy state or target changed"
pass "case21b: unsafe legacy state remains untouched after canonical success"
teardown

install_fingerprint_rendezvous_python() {
  READY_FIFO="$SCRATCH/fingerprint-ready.fifo"
  RELEASE_FIFO="$SCRATCH/fingerprint-release.fifo"
  PYTHON_COUNT="$SCRATCH/fingerprint-count"
  mkfifo "$READY_FIFO" "$RELEASE_FIFO"
  cat > "$TEST_BIN/python3" <<STUB
#!/usr/bin/env bash
if [ "\$1" = - ] && [ "\${2:-}" = "$SKILLS_ROOT" ]; then
  _count=0
  [ ! -f "$PYTHON_COUNT" ] || _count="\$(cat "$PYTHON_COUNT")"
  _count=\$((_count + 1))
  printf '%s\n' "\$_count" > "$PYTHON_COUNT"
  if [ "\$_count" -eq 2 ]; then
    "$REAL_PYTHON" "\$@" > "$SCRATCH/fingerprint-result"
    _status=\$?
    printf '%s\n' ready > "$READY_FIFO"
    IFS= read -r _release < "$RELEASE_FIFO"
    cat "$SCRATCH/fingerprint-result"
    exit "\$_status"
  fi
fi
exec "$REAL_PYTHON" "\$@"
STUB
  chmod +x "$TEST_BIN/python3"
}

### Case 22: an external installed-generation writer blocks publication ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
PRIOR_LEDGER="projection-v2 claude $(printf 'a%.0s' {1..64}) $(printf 'b%.0s' {1..64})"
printf '%s\n' "$PRIOR_LEDGER" > "$STATE_FILE"
printf '%s\n' legacy-preserved > "$LEGACY_STATE_FILE"
install_fingerprint_rendezvous_python
HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" \
  PATH="$TEST_BIN:/usr/bin:/bin" bash "$SCRIPT" beads >"$SCRATCH/external.out" 2>"$SCRATCH/external.err" &
EXTERNAL_HOOK_PID=$!
IFS= read -r READY_SIGNAL < "$READY_FIFO"
[ "$READY_SIGNAL" = ready ] || fail "case22: fingerprint rendezvous failed"
printf '\n' >> "$INSTALLED_BUNDLE/capability.json"
printf '%s\n' release > "$RELEASE_FIFO"
wait "$EXTERNAL_HOOK_PID"
grep -q 'installed generation verification failed' "$SCRATCH/external.err" \
  || fail "case22: external installed-generation drift was certified"
[ "$(cat "$STATE_FILE")" = "$PRIOR_LEDGER" ] \
  || fail "case22: external generation drift changed the prior ledger"
[ "$(cat "$LEGACY_STATE_FILE")" = legacy-preserved ] \
  || fail "case22: external generation drift changed legacy retry state"
pass "case22: final installed-generation recheck rejects an external writer"
teardown

### Case 23: an external selected-surface writer blocks publication ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
PRIOR_LEDGER="projection-v2 claude $(printf 'c%.0s' {1..64}) $(printf 'd%.0s' {1..64})"
printf '%s\n' "$PRIOR_LEDGER" > "$STATE_FILE"
printf '%s\n' legacy-preserved > "$LEGACY_STATE_FILE"
install_fingerprint_rendezvous_python
HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" \
  PATH="$TEST_BIN:/usr/bin:/bin" bash "$SCRIPT" beads >"$SCRATCH/external.out" 2>"$SCRATCH/external.err" &
EXTERNAL_HOOK_PID=$!
IFS= read -r READY_SIGNAL < "$READY_FIFO"
[ "$READY_SIGNAL" = ready ] || fail "case23: fingerprint rendezvous failed"
printf '\n' >> "$SKILLS_ROOT/gsd-beads-status/SKILL.md"
printf '%s\n' release > "$RELEASE_FIFO"
wait "$EXTERNAL_HOOK_PID"
grep -q 'selected projection verification failed' "$SCRATCH/external.err" \
  || fail "case23: external selected-surface drift was certified"
[ "$(cat "$STATE_FILE")" = "$PRIOR_LEDGER" ] \
  || fail "case23: external selected drift changed the prior ledger"
[ "$(cat "$LEGACY_STATE_FILE")" = legacy-preserved ] \
  || fail "case23: external selected drift changed legacy retry state"
pass "case23: final selected-fingerprint recheck rejects an external writer"
teardown

### Case 23b: a writer after final observation is repaired on next SessionStart ###
setup 0
seed_selected "$SKILLS_ROOT"
install_publish_spy
R2_REPLACE_READY="$SCRATCH/replace-ready.fifo"
R2_REPLACE_RELEASE="$SCRATCH/replace-release.fifo"
mkfifo "$R2_REPLACE_READY" "$R2_REPLACE_RELEASE"
cat > "$BIN_DIR/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$STUB_LOG"
if [ "\$*" = 'query skills-root codex --raw' ]; then
  printf '%s\n' "$SKILLS_ROOT"
  exit 0
fi
if [ "\$*" = 'capability set beads --runtime codex --scope global --config-dir $CODEX_HOME' ]; then
  cp -f "$BUNDLE_DIR/skills/beads-status/SKILL.md" "$SKILLS_ROOT/gsd-beads-status/SKILL.md"
fi
exit 0
STUB
chmod +x "$BIN_DIR/gsd-tools.cjs"
HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" \
  PYTHONPATH="$TEST_PYTHONPATH" PYTHONDONTWRITEBYTECODE=1 \
  R2_PUBLISH_SPY_LOG="$R2_PUBLISH_SPY_LOG" R2_LEGACY_PATH="$R2_LEGACY_PATH" \
  R2_LEDGER_PATH="$R2_LEDGER_PATH" R2_REPLACE_READY="$R2_REPLACE_READY" \
  R2_REPLACE_RELEASE="$R2_REPLACE_RELEASE" PATH="$TEST_BIN:/usr/bin:/bin" \
  bash "$SCRIPT" beads >"$SCRATCH/after-final.out" 2>"$SCRATCH/after-final.err" &
AFTER_FINAL_HOOK_PID=$!
REPLACE_READY="$("$REAL_PYTHON" - "$R2_REPLACE_READY" <<'PY'
import os
import select
import sys

descriptor = os.open(sys.argv[1], os.O_RDWR | os.O_NONBLOCK)
try:
    readable, _, _ = select.select([descriptor], [], [], 10)
    if not readable:
        raise SystemExit(1)
    print(os.read(descriptor, 64).decode().strip())
finally:
    os.close(descriptor)
PY
)"
if [ "$?" -ne 0 ]; then
  kill "$AFTER_FINAL_HOOK_PID" 2>/dev/null || true
  wait "$AFTER_FINAL_HOOK_PID" 2>/dev/null || true
  fail "case23b: publisher did not reach the bounded replace barrier"
fi
[ "$REPLACE_READY" = ready ] || fail "case23b: publisher did not reach the replace barrier"
printf '\n# direct writer after final observation\n' >> "$SKILLS_ROOT/gsd-beads-status/SKILL.md"
printf '%s\n' release > "$R2_REPLACE_RELEASE"
wait "$AFTER_FINAL_HOOK_PID"
[ "$(cat "$SCRATCH/after-final.out")" = 'Auto-installed capability: beads (user scope)' ] \
  || fail "case23b: after-observation publication did not complete"
[ -z "$(cat "$SCRATCH/after-final.err")" ] \
  || fail "case23b: after-observation publication emitted stderr"
STALE_LEDGER_FINGERPRINT="$(awk '{print $4}' "$STATE_FILE")"
MUTATED_FINGERPRINT="$(fixture_tree_hash "$SKILLS_ROOT" \
  gsd-beads-recall gsd-beads-status gsd-beads-sync gsd-beads-migrate-todos)"
[ "$STALE_LEDGER_FINGERPRINT" != "$MUTATED_FINGERPRINT" ] \
  || fail "case23b: post-observation mutation did not invalidate the published row"
WRITERS_BEFORE="$(grep -Ec '^capability (install|set)' "$STUB_LOG")"
REPLACES_BEFORE_REPAIR="$(grep -c '^replace' "$R2_PUBLISH_SPY_LOG")"
R2_REPLACE_READY=""
R2_REPLACE_RELEASE=""
run_script beads
[ "$(cat "$STDOUT_FILE")" = 'Auto-installed capability: beads (user scope)' ] \
  || fail "case23b: next SessionStart did not repair the direct-writer race"
[ "$(grep -Ec '^capability (install|set)' "$STUB_LOG")" -eq $((WRITERS_BEFORE + 2)) ] \
  || fail "case23b: next SessionStart did not invoke both native writers"
cmp -s "$BUNDLE_DIR/skills/beads-status/SKILL.md" "$SKILLS_ROOT/gsd-beads-status/SKILL.md" \
  || fail "case23b: next SessionStart did not restore selected bytes"
[ "$(grep -c '^replace' "$R2_PUBLISH_SPY_LOG")" -eq $((REPLACES_BEFORE_REPAIR + 1)) ] \
  || fail "case23b: next SessionStart did not republish the repaired receipt"
REPAIRED_FINGERPRINT="$(fixture_tree_hash "$SKILLS_ROOT" \
  gsd-beads-recall gsd-beads-status gsd-beads-sync gsd-beads-migrate-todos)"
[ "$(awk '{print $4}' "$STATE_FILE")" = "$REPAIRED_FINGERPRINT" ] \
  || fail "case23b: repaired receipt does not match the restored selected surface"
WRITERS_AFTER_REPAIR="$(grep -Ec '^capability (install|set)' "$STUB_LOG")"
REPLACES_AFTER_REPAIR="$(grep -c '^replace' "$R2_PUBLISH_SPY_LOG")"
run_script beads
[ -z "$(cat "$STDOUT_FILE")" ] && [ -z "$(cat "$STDERR_FILE")" ] \
  || fail "case23b: repaired state did not converge silently"
[ "$(grep -Ec '^capability (install|set)' "$STUB_LOG")" -eq "$WRITERS_AFTER_REPAIR" ] \
  || fail "case23b: repaired rerun invoked a native writer"
[ "$(grep -c '^replace' "$R2_PUBLISH_SPY_LOG")" -eq "$REPLACES_AFTER_REPAIR" ] \
  || fail "case23b: repaired rerun republished the receipt"
pass "case23b: post-observation external drift is invalidated and repaired next start"
teardown

### Case 24a: CI pins and proves the current public runtime before smoke ###
CI_WORKFLOW="$REPO_ROOT/.github/workflows/ci.yml"
$REAL_PYTHON - "$CI_WORKFLOW" <<'PY' \
  || fail "case24a: CI does not provision and prove the pinned gsd-core 1.12.0 runtime before smoke"
import pathlib
import sys

text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
ordered = (
    "repository: open-gsd/gsd-core",
    "ref: v1.12.0",
    "fetch-depth: 0",
    "path: .ci/gsd-core",
    "@opengsd/gsd-core@1.12.0",
    "--codex --global --config-dir",
    "runtime-identity --raw",
    '"packageName":"@opengsd/gsd-core"',
    '"version":"1.12.0"',
    "GSD_CORE_REPO=",
    "bash tests/test-capability-auto-install.sh",
)
positions = tuple(text.find(token) for token in ordered)
if -1 in positions or positions != tuple(sorted(positions)):
    raise SystemExit(1)
PY
pass "case24a: CI pins and proves gsd-core 1.12.0 before the smoke harness"

### Case 24: immutable floor provenance plus real current two-capability proof ###
REAL_ROOT="$(mktemp -d /dev/shm/gsd-beads-210-real.XXXXXX)" \
  || fail "case24: could not allocate bounded /dev/shm scratch"
SCRATCH="$REAL_ROOT"
REAL_TMP="$REAL_ROOT/tmp"
mkdir -p "$REAL_TMP"

[ -d "$GSD_CORE_REPO/.git" ] || fail "case24: gsd-core source repository is unavailable"
[ -x "$ACTIVE_GSD_TOOLS" ] || fail "case24: active/current gsd-tools is unavailable"
FLOOR_SHA="$(git -C "$GSD_CORE_REPO" rev-parse 'v1.10.0^{commit}' 2>/dev/null)" \
  || fail "case24: official v1.10.0 tag is unavailable"
[ "$FLOOR_SHA" = "68a04ccf8ef74803bdb651e12c3b85b218bbccdf" ] \
  || fail "case24: official v1.10.0 tag peeled to $FLOOR_SHA"
FLOOR_PACKAGE_FILE="$REAL_ROOT/floor-package.json"
git -C "$GSD_CORE_REPO" show "$FLOOR_SHA:package.json" > "$FLOOR_PACKAGE_FILE" 2>/dev/null \
  || fail "case24: official v1.10.0 package metadata is unavailable"
FLOOR_PACKAGE="$($REAL_PYTHON - "$FLOOR_PACKAGE_FILE" <<'PY'
import json
import pathlib
import sys

metadata = json.loads(pathlib.Path(sys.argv[1]).read_text())
print(f"{metadata.get('name')}@{metadata.get('version')}")
PY
)" || fail "case24: official v1.10.0 package metadata is invalid"
[ "$FLOOR_PACKAGE" = "@opengsd/gsd-core@1.10.0" ] \
  || fail "case24: official floor package is $FLOOR_PACKAGE"

ACTIVE_IDENTITY="$($ACTIVE_GSD_TOOLS runtime-identity --raw 2>/dev/null)" \
  || fail "case24: active/current runtime identity failed"
ACTIVE_IDENTITY_KEY="$(printf '%s' "$ACTIVE_IDENTITY" | "$REAL_PYTHON" -c '
import json, sys
identity = json.load(sys.stdin)
print("{}@{}".format(identity.get("packageName"), identity.get("version")))
')" || fail "case24: active/current runtime identity was not JSON"
[ "$ACTIVE_IDENTITY_KEY" = "@opengsd/gsd-core@1.12.0" ] \
  || fail "case24: active/current runtime is $ACTIVE_IDENTITY_KEY"
ACTIVE_PUBLIC_ROOT="$($ACTIVE_GSD_TOOLS query skills-root codex --raw 2>/dev/null)" \
  || fail "case24: active/current public skills-root query failed"
[ -n "$ACTIVE_PUBLIC_ROOT" ] || fail "case24: active/current public skills-root was empty"

CURRENT_ARCHIVE="$REAL_ROOT/current-gsd-core.tar"
git -C "$GSD_CORE_REPO" archive --format=tar --output="$CURRENT_ARCHIVE" HEAD \
  || fail "case24: could not archive the current gsd-core source"

prepare_current_runtime() {
  local _config_root="$1" _home_root="$2" _claude_root="$3" _project_root="$4"
  mkdir -p "$_config_root" "$_home_root" "$_claude_root" "$_project_root/.planning"
  tar -xf "$CURRENT_ARCHIVE" -C "$_config_root" \
    || fail "case24: could not materialize current gsd-core source"
  cp -rf "$ACTIVE_CODEX_HOME/gsd-core/bin" "$_config_root/gsd-core/" \
    || fail "case24: could not overlay the active/current compiled CLI"
  cp -f "$ACTIVE_CODEX_HOME/gsd-core/VERSION" "$_config_root/gsd-core/VERSION" \
    || fail "case24: could not copy the active/current version marker"
  printf '{}\n' > "$_project_root/.planning/config.json"
}

real_cli() {
  local _config_root="$1" _home_root="$2" _claude_root="$3" _project_root="$4"
  shift 4
  (
    cd "$_project_root" || exit 1
    env TMPDIR="$REAL_TMP" HOME="$_home_root" GSD_HOME="$_home_root" \
      CODEX_HOME="$_config_root" CLAUDE_CONFIG_DIR="$_claude_root" \
      "$_config_root/gsd-core/bin/gsd-tools.cjs" "$@"
  )
}

ACTUAL_CODEX="$REAL_ROOT/actual/.codex"
ACTUAL_HOME="$REAL_ROOT/actual/home"
ACTUAL_CLAUDE="$REAL_ROOT/actual/.claude"
ACTUAL_PROJECT="$REAL_ROOT/actual/project"
ORACLE_CODEX="$REAL_ROOT/oracle/.codex"
ORACLE_HOME="$REAL_ROOT/oracle/home"
ORACLE_CLAUDE="$REAL_ROOT/oracle/.claude"
ORACLE_PROJECT="$REAL_ROOT/oracle/project"
prepare_current_runtime "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT"
prepare_current_runtime "$ORACLE_CODEX" "$ORACLE_HOME" "$ORACLE_CLAUDE" "$ORACLE_PROJECT"

FIXTURE_IDENTITY="$(real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" \
  "$ACTUAL_PROJECT" runtime-identity --raw 2>/dev/null)" \
  || fail "case24: isolated current runtime identity failed"
[ "$FIXTURE_IDENTITY" = "$ACTIVE_IDENTITY" ] \
  || fail "case24: isolated current runtime identity differs from active/current"
ACTUAL_SKILLS_ROOT="$(real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" \
  "$ACTUAL_PROJECT" query skills-root codex --raw 2>/dev/null)" \
  || fail "case24: isolated real public skills-root query failed"
[ "$ACTUAL_SKILLS_ROOT" = "$ACTUAL_HOME/.agents/skills" ] \
  || fail "case24: isolated real public skills-root is noncanonical"
ORACLE_SKILLS_ROOT="$(real_cli "$ORACLE_CODEX" "$ORACLE_HOME" "$ORACLE_CLAUDE" \
  "$ORACLE_PROJECT" query skills-root codex --raw 2>/dev/null)" \
  || fail "case24: oracle real public skills-root query failed"
[ "$ORACLE_SKILLS_ROOT" = "$ORACLE_HOME/.agents/skills" ] \
  || fail "case24: oracle real public skills-root is noncanonical"

GENERATION_B="$REAL_ROOT/generation-b"
GENERATION_A="$REAL_ROOT/generation-a"
SIBLING_BUNDLE="$REAL_ROOT/phase22-sibling"
cp -rf "$REPO_ROOT/plugins/beads-lifecycle/.gsd/capabilities/beads" "$GENERATION_B"
cp -rf "$GENERATION_B" "$GENERATION_A"
$REAL_PYTHON - "$GENERATION_A/capability.json" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
manifest = json.loads(path.read_text())
manifest["version"] = "0.6.1"
path.write_text(json.dumps(manifest, indent=2) + "\n")
PY
printf '\npython3 "$SYNC_PY" check-patch execute-plan\n' \
  >> "$GENERATION_A/skills/beads-recall/SKILL.md"
mkdir -p "$SIBLING_BUNDLE/skills/phase22-sibling"
$REAL_PYTHON - "$SIBLING_BUNDLE/capability.json" <<'PY'
import json
import pathlib
import sys

manifest = {
    "id": "phase22-sibling",
    "role": "feature",
    "version": "1.0.0",
    "title": "Phase 22 sibling",
    "description": "Real sibling preservation fixture.",
    "tier": "full",
    "requires": [],
    "engines": {"gsd": ">=1.10.0"},
    "runtimeCompat": {"supported": ["*"], "unsupported": []},
    "skills": ["phase22-sibling"],
    "agents": [],
    "hooks": [],
    "config": {},
    "steps": [],
    "contributions": [],
    "gates": [],
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(manifest, indent=2) + "\n")
PY
printf '%s\n' '---' 'name: gsd-phase22-sibling' \
  'description: Genuine sibling preservation fixture.' '---' '' '# Sibling' \
  > "$SIBLING_BUNDLE/skills/phase22-sibling/SKILL.md"

REAL_SETUP_LOG="$REAL_ROOT/native-setup.log"
: > "$REAL_SETUP_LOG"
real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT" \
  capability install "$SIBLING_BUNDLE" --scope global --yes >> "$REAL_SETUP_LOG" 2>&1 \
  || fail "case24: real sibling install failed"
real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT" \
  capability install "$GENERATION_A" --scope global --yes >> "$REAL_SETUP_LOG" 2>&1 \
  || fail "case24: real generation-A install failed"
real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT" \
  capability set phase22-sibling --runtime codex --scope global --config-dir "$ACTUAL_CODEX" \
  >> "$REAL_SETUP_LOG" 2>&1 || fail "case24: real sibling set failed"
real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT" \
  capability set beads --runtime codex --scope global --config-dir "$ACTUAL_CODEX" \
  >> "$REAL_SETUP_LOG" 2>&1 || fail "case24: real generation-A set failed"

ORACLE_LOG="$REAL_ROOT/oracle.log"
: > "$ORACLE_LOG"
real_cli "$ORACLE_CODEX" "$ORACLE_HOME" "$ORACLE_CLAUDE" "$ORACLE_PROJECT" \
  capability install "$SIBLING_BUNDLE" --scope global --yes >> "$ORACLE_LOG" 2>&1 \
  || fail "case24: oracle sibling install failed"
real_cli "$ORACLE_CODEX" "$ORACLE_HOME" "$ORACLE_CLAUDE" "$ORACLE_PROJECT" \
  capability install "$GENERATION_B" --scope global --yes >> "$ORACLE_LOG" 2>&1 \
  || fail "case24: oracle generation-B install failed"
real_cli "$ORACLE_CODEX" "$ORACLE_HOME" "$ORACLE_CLAUDE" "$ORACLE_PROJECT" \
  capability set phase22-sibling --runtime codex --scope global --config-dir "$ORACLE_CODEX" \
  >> "$ORACLE_LOG" 2>&1 || fail "case24: oracle sibling set failed"
real_cli "$ORACLE_CODEX" "$ORACLE_HOME" "$ORACLE_CLAUDE" "$ORACLE_PROJECT" \
  capability set beads --runtime codex --scope global --config-dir "$ORACLE_CODEX" \
  >> "$ORACLE_LOG" 2>&1 || fail "case24: oracle generation-B set failed"

# The native transform embeds the runtime config root in one selected skill.
# Normalize only that independently produced fixture-local prefix before the
# byte-for-byte comparison; no raw installed skill supplies expected output.
EXPECTED_SKILLS_ROOT="$REAL_ROOT/oracle-normalized"
mkdir -p "$EXPECTED_SKILLS_ROOT"
cp -rf "$ORACLE_SKILLS_ROOT/." "$EXPECTED_SKILLS_ROOT/"
$REAL_PYTHON - "$EXPECTED_SKILLS_ROOT" "$ORACLE_CODEX" "$ACTUAL_CODEX" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
old, new = (value.encode() for value in sys.argv[2:])
for path in root.rglob("*"):
    if path.is_symlink():
        raise SystemExit("transformed oracle contains a symlink")
    if path.is_file():
        data = path.read_bytes()
        path.write_bytes(data.replace(old, new))
PY

SELECTED_PATHS=(
  gsd-beads-sync
  gsd-beads-status
  gsd-beads-recall
  gsd-beads-migrate-todos
)
for _selected_path in "${SELECTED_PATHS[@]}"; do
  [ -d "$ACTUAL_SKILLS_ROOT/$_selected_path" ] \
    || fail "case24: generation-A selected tree is incomplete"
  [ -d "$EXPECTED_SKILLS_ROOT/$_selected_path" ] \
    || fail "case24: transformed oracle is incomplete"
done
[ -d "$ACTUAL_SKILLS_ROOT/gsd-phase22-sibling" ] \
  || fail "case24: actual genuine sibling projection is missing"
[ -d "$ORACLE_SKILLS_ROOT/gsd-phase22-sibling" ] \
  || fail "case24: oracle genuine sibling projection is missing"

ACTUAL_LEDGER="$ACTUAL_HOME/.gsd/capability-auto-install-beads.projections"
ACTUAL_LEGACY="$ACTUAL_HOME/.gsd/capability-auto-install-beads.hash"
ACTUAL_INSTALLED="$ACTUAL_HOME/.gsd/capabilities/beads"
GENERATION_A_HASH="$(fixture_tree_hash "$ACTUAL_INSTALLED")" \
  || fail "case24: could not hash installed generation A"
GENERATION_A_SELECTED="$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT" "${SELECTED_PATHS[@]}")" \
  || fail "case24: could not hash selected generation A"
GENERATION_B_SELECTED="$(fixture_tree_hash "$EXPECTED_SKILLS_ROOT" "${SELECTED_PATHS[@]}")" \
  || fail "case24: could not hash transformed generation B"
[ "$GENERATION_A_SELECTED" != "$GENERATION_B_SELECTED" ] \
  || fail "case24: generation A selected fingerprint is not genuinely stale"
grep -q 'check-patch execute-plan' "$ACTUAL_SKILLS_ROOT/gsd-beads-recall/SKILL.md" \
  || fail "case24: generation A lacks the retired selected command"
printf 'projection-v2 codex %s %s\n' "$GENERATION_A_HASH" "$GENERATION_A_SELECTED" \
  > "$ACTUAL_LEDGER"
printf '%s\n' legacy-generation-a > "$ACTUAL_LEGACY"

mkdir -p "$ACTUAL_SKILLS_ROOT/plain-user-skill"
printf '%s\n' plain-user-bytes > "$ACTUAL_SKILLS_ROOT/plain-user-skill/note"
mkdir -p "$ACTUAL_HOME/unrelated"
printf '%s\n' unrelated-bytes > "$ACTUAL_HOME/unrelated/note"
mkdir -p "$ACTUAL_CLAUDE/skills/gsd-beads-recall"
printf '%s\n' unmarked-same-name-user-bytes \
  > "$ACTUAL_CLAUDE/skills/gsd-beads-recall/SKILL.md"
PLAIN_BEFORE="$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT/plain-user-skill")"
UNRELATED_BEFORE="$(fixture_tree_hash "$ACTUAL_HOME/unrelated")"
UNSELECTED_BEFORE="$(fixture_tree_hash "$ACTUAL_CLAUDE/skills")"
SIBLING_BEFORE="$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT/gsd-phase22-sibling")"

REAL_PLUGIN_ROOT="$ACTUAL_CODEX/plugins/cache/gsd-beads/beads-lifecycle/current"
mkdir -p "$REAL_PLUGIN_ROOT/.gsd/capabilities"
cp -rf "$GENERATION_B" "$REAL_PLUGIN_ROOT/.gsd/capabilities/beads"
REAL_GSD_TOOLS="$ACTUAL_CODEX/gsd-core/bin/gsd-tools-real.cjs"
REAL_SPY_LOG="$REAL_ROOT/real-spy.log"
cp -f "$ACTUAL_CODEX/gsd-core/bin/gsd-tools.cjs" "$REAL_GSD_TOOLS"
cat > "$ACTUAL_CODEX/gsd-core/bin/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$REAL_SPY_LOG"
exec "$REAL_GSD_TOOLS" "\$@"
STUB
chmod +x "$ACTUAL_CODEX/gsd-core/bin/gsd-tools.cjs" "$REAL_GSD_TOOLS"
: > "$REAL_SPY_LOG"

REAL_HOOK_OUT="$REAL_ROOT/hook.out"
REAL_HOOK_ERR="$REAL_ROOT/hook.err"
(
  cd "$ACTUAL_PROJECT" || exit 1
  env TMPDIR="$REAL_TMP" HOME="$ACTUAL_HOME" GSD_HOME="$ACTUAL_HOME" \
    CODEX_HOME="$ACTUAL_CODEX" CLAUDE_CONFIG_DIR="$ACTUAL_CLAUDE" \
    CLAUDE_PLUGIN_ROOT="$REAL_PLUGIN_ROOT" GSD_RUNTIME=codex \
    bash "$SCRIPT" beads
) > "$REAL_HOOK_OUT" 2> "$REAL_HOOK_ERR"
REAL_HOOK_STATUS=$?
[ "$REAL_HOOK_STATUS" -eq 0 ] || fail "case24: real hook exited $REAL_HOOK_STATUS"
[ "$(cat "$REAL_HOOK_OUT")" = 'Auto-installed capability: beads (user scope)' ] \
  || fail "case24: real hook did not report generation-B reconciliation"
[ -z "$(cat "$REAL_HOOK_ERR")" ] \
  || fail "case24: real hook emitted: $(cat "$REAL_HOOK_ERR")"
[ "$(wc -l < "$REAL_SPY_LOG")" -eq 3 ] \
  || fail "case24: real hook invoked the current CLI an unexpected number of times"
grep -qx 'query skills-root codex --raw' "$REAL_SPY_LOG" \
  || fail "case24: real hook omitted the public skills-root query"
grep -qx "capability install $REAL_PLUGIN_ROOT/.gsd/capabilities/beads --scope global --yes" \
  "$REAL_SPY_LOG" || fail "case24: real hook install argv differed"
grep -qx "capability set beads --runtime codex --scope global --config-dir $ACTUAL_CODEX" \
  "$REAL_SPY_LOG" || fail "case24: real hook set argv differed"

for _selected_path in "${SELECTED_PATHS[@]}"; do
  ACTUAL_SELECTED_HASH="$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT/$_selected_path")"
  ORACLE_SELECTED_HASH="$(fixture_tree_hash "$EXPECTED_SKILLS_ROOT/$_selected_path")"
  [ "$ACTUAL_SELECTED_HASH" = "$ORACLE_SELECTED_HASH" ] \
    || fail "case24: $_selected_path differs from the current transformed oracle"
  [ "$(cat "$ACTUAL_SKILLS_ROOT/$_selected_path/.gsd-capability-skill")" = beads ] \
    || fail "case24: $_selected_path has the wrong owner"
done
ACTUAL_SIBLING_HASH="$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT/gsd-phase22-sibling")"
ORACLE_SIBLING_HASH="$(fixture_tree_hash "$EXPECTED_SKILLS_ROOT/gsd-phase22-sibling")"
[ "$ACTUAL_SIBLING_HASH" = "$ORACLE_SIBLING_HASH" ] \
  || fail "case24: genuine sibling differs from the transformed oracle"
[ "$(cat "$ACTUAL_SKILLS_ROOT/gsd-phase22-sibling/.gsd-capability-skill")" = phase22-sibling ] \
  || fail "case24: genuine sibling owner changed"
[ "$ACTUAL_SIBLING_HASH" = "$SIBLING_BEFORE" ] \
  || fail "case24: Beads reconciliation changed the genuine sibling"

COMMAND_PREFIXES="$($REAL_PYTHON - "$GENERATION_B/capability.json" "$ACTUAL_SKILLS_ROOT" \
  "$ACTUAL_INSTALLED/scripts/sync.py" <<'PY'
import json
import pathlib
import re
import shlex
import subprocess
import sys

manifest_path = pathlib.Path(sys.argv[1])
skills_root = pathlib.Path(sys.argv[2])
sync_path = pathlib.Path(sys.argv[3])
skills = json.loads(manifest_path.read_text())["skills"]
commands = set()
observed_skills = set()
for skill in skills:
    text = (skills_root / f"gsd-{skill}" / "SKILL.md").read_text()
    if "execute-plan" in text:
        raise SystemExit("retired execute-plan remains selected")
    for declaration in re.findall(r'^python3 "\$SYNC_PY" (.+)$', text, re.MULTILINE):
        prefix = []
        for token in shlex.split(declaration):
            if "<" in token or "[" in token:
                break
            if not re.fullmatch(r"[a-z][a-z0-9-]*", token):
                raise SystemExit(f"unsafe selected command token: {token}")
            prefix.append(token)
        if not prefix:
            raise SystemExit(f"missing selected command for {skill}")
        commands.add(tuple(prefix))
        observed_skills.add(skill)
if observed_skills != set(skills):
    raise SystemExit(f"selected command declarations incomplete: {sorted(observed_skills)}")
for prefix in sorted(commands):
    result = subprocess.run(
        [sys.executable, str(sync_path), *prefix, "--help"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"selected command rejected: {' '.join(prefix)}")
retired = subprocess.run(
    [sys.executable, str(sync_path), "execute-plan", "--help"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
)
if retired.returncode == 0:
    raise SystemExit("retired execute-plan was accepted")
print(",".join(" ".join(prefix) for prefix in sorted(commands)))
PY
)" || fail "case24: selected installed CLI contract failed"
[ -n "$COMMAND_PREFIXES" ] || fail "case24: no selected command prefixes were exercised"

[ ! -e "$ACTUAL_LEGACY" ] && [ ! -L "$ACTUAL_LEGACY" ] \
  || fail "case24: legacy generation-A state was not replaced"
GENERATION_B_HASH="$(fixture_tree_hash "$ACTUAL_INSTALLED")"
GENERATION_B_SELECTED="$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT" "${SELECTED_PATHS[@]}")"
EXPECTED_LEDGER="projection-v2 codex $GENERATION_B_HASH $GENERATION_B_SELECTED"
[ "$(cat "$ACTUAL_LEDGER")" = "$EXPECTED_LEDGER" ] \
  || fail "case24: shared v2 ledger is not the canonical generation-B row"
[ "$GENERATION_A_HASH" != "$GENERATION_B_HASH" ] \
  || fail "case24: generation A and B fixture hashes are identical"
grep -q "$GENERATION_A_HASH" "$ACTUAL_LEDGER" \
  && fail "case24: stale generation-A ledger row survived invalidation"
[ "$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT/plain-user-skill")" = "$PLAIN_BEFORE" ] \
  || fail "case24: plain user skill changed"
[ "$(fixture_tree_hash "$ACTUAL_HOME/unrelated")" = "$UNRELATED_BEFORE" ] \
  || fail "case24: unrelated bytes changed"
[ "$(fixture_tree_hash "$ACTUAL_CLAUDE/skills")" = "$UNSELECTED_BEFORE" ] \
  || fail "case24: unselected runtime or same-name user bytes changed"

SELECTED_BEFORE_REPEAT="$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT")"
LEDGER_BEFORE_REPEAT="$(fixture_tree_hash "$(dirname "$ACTUAL_LEDGER")" \
  "$(basename "$ACTUAL_LEDGER")")"
(
  cd "$ACTUAL_PROJECT" || exit 1
  env TMPDIR="$REAL_TMP" HOME="$ACTUAL_HOME" GSD_HOME="$ACTUAL_HOME" \
    CODEX_HOME="$ACTUAL_CODEX" CLAUDE_CONFIG_DIR="$ACTUAL_CLAUDE" \
    CLAUDE_PLUGIN_ROOT="$REAL_PLUGIN_ROOT" GSD_RUNTIME=codex \
    bash "$SCRIPT" beads
) > "$REAL_HOOK_OUT" 2> "$REAL_HOOK_ERR"
REAL_REPEAT_STATUS=$?
[ "$REAL_REPEAT_STATUS" -eq 0 ] || fail "case24: real repeat exited $REAL_REPEAT_STATUS"
[ -z "$(cat "$REAL_HOOK_OUT")" ] && [ -z "$(cat "$REAL_HOOK_ERR")" ] \
  || fail "case24: real repeat was not silent"
[ "$(wc -l < "$REAL_SPY_LOG")" -eq 4 ] \
  || fail "case24: real repeat invoked a native writer"
[ "$(tail -n 1 "$REAL_SPY_LOG")" = 'query skills-root codex --raw' ] \
  || fail "case24: real repeat did more than validate its public destination"
[ "$(fixture_tree_hash "$ACTUAL_SKILLS_ROOT")" = "$SELECTED_BEFORE_REPEAT" ] \
  || fail "case24: real repeat changed the selected tree"
[ "$(fixture_tree_hash "$(dirname "$ACTUAL_LEDGER")" \
  "$(basename "$ACTUAL_LEDGER")")" = "$LEDGER_BEFORE_REPEAT" ] \
  || fail "case24: real repeat changed the shared ledger"

EVIDENCE_ROOT="$ACTUAL_SKILLS_ROOT"
rm -rf "$REAL_ROOT"
[ ! -e "$REAL_ROOT" ] || fail "case24: bounded real scratch was not removed"
SCRATCH=""
pass "case24: floor=$FLOOR_SHA package=$FLOOR_PACKAGE current=$ACTIVE_IDENTITY_KEY public-root=$EVIDENCE_ROOT stale-a=repaired commands=$COMMAND_PREFIXES sibling=preserved oracle=matched no-skip scratch=clean"

echo "ALL PASS"
exit 0
