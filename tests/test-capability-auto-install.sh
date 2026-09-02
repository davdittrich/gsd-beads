#!/usr/bin/env bash
# Stdlib-only smoke test (N5): no framework, no fixtures dir. Every case runs
# against a scratch plugin root + scratch GSD_HOME under mktemp -d, with a
# stub runtime-owned `gsd-tools.cjs` -- no real capability install ever occurs and this
# repo's own real $HOME/.gsd/ is never touched.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/plugins/beads-lifecycle/hooks/capability-auto-install.sh"

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

teardown() {
  rm -rf "$SCRATCH" 2>/dev/null
}

# run_script <capability-id> -- invokes SCRIPT with the stub active-runtime tool,
# capturing stdout/stderr to STDOUT_FILE/STDERR_FILE and STATUS.
run_script() {
  HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" GSD_RUNTIME="${GSD_RUNTIME:-}" \
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

echo "ALL PASS"
exit 0
