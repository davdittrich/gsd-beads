#!/usr/bin/env bash
# Stdlib-only smoke test (N5): no framework, no fixtures dir. Every case runs
# against a scratch plugin root + scratch GSD_HOME under mktemp -d, with a
# stub `gsd-tools` on PATH -- no real capability install ever occurs and this
# repo's own real $HOME/.gsd/ is never touched.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/plugins/beads-lifecycle/hooks/capability-auto-install.sh"

fail() { echo "FAIL: $1"; exit 1; }
pass() { echo "PASS: $1"; }

trap '[ -n "${SCRATCH:-}" ] && rm -rf "$SCRATCH" 2>/dev/null' EXIT

# setup <stub-exit-status>
# Builds a scratch plugin root with a fake .gsd/capabilities/beads/ bundle, a
# scratch GSD_HOME (so the sidecar state file never touches the real $HOME),
# and a stub `gsd-tools` executable that logs its argv and exits with the
# given status. Sets SCRATCH, PLUGIN_DIR, BUNDLE_DIR, GSD_HOME, BIN_DIR,
# STUB_LOG, STATE_FILE.
setup() {
  SCRATCH="$(mktemp -d)"
  PLUGIN_DIR="$SCRATCH/plugin"
  BUNDLE_DIR="$PLUGIN_DIR/.gsd/capabilities/beads"
  mkdir -p "$BUNDLE_DIR"
  printf '{"id":"beads"}\n' > "$BUNDLE_DIR/capability.json"

  GSD_HOME="$SCRATCH/home"
  mkdir -p "$GSD_HOME"
  STATE_FILE="$GSD_HOME/.gsd/capability-auto-install-beads.hash"

  BIN_DIR="$SCRATCH/bin"
  mkdir -p "$BIN_DIR"
  STUB_LOG="$SCRATCH/stub.log"
  : > "$STUB_LOG"
  local stub_status="${1:-0}"
  cat > "$BIN_DIR/gsd-tools" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$STUB_LOG"
exit $stub_status
STUB
  chmod +x "$BIN_DIR/gsd-tools"

  STDOUT_FILE="$SCRATCH/stdout"
  STDERR_FILE="$SCRATCH/stderr"
}

teardown() {
  rm -rf "$SCRATCH" 2>/dev/null
}

# run_script <capability-id> -- invokes SCRIPT with the stub gsd-tools first
# on PATH, capturing stdout/stderr to STDOUT_FILE/STDERR_FILE and STATUS.
run_script() {
  PATH="$BIN_DIR:$PATH" CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" \
    bash "$SCRIPT" "$1" >"$STDOUT_FILE" 2>"$STDERR_FILE"
  STATUS=$?
}

### Cases 1-3: happy-path lifecycle (Task 1 behavior) ###
setup 0

# Case 1: first run, no prior sidecar state -> installs once, prints notice.
run_script beads
[ "$STATUS" -eq 0 ] || fail "case1: exit status $STATUS, expected 0"
[ "$(cat "$STDOUT_FILE")" = "Auto-installed capability: beads (user scope)" ] \
  || fail "case1: stdout notice mismatch: $(cat "$STDOUT_FILE")"
[ "$(wc -l < "$STUB_LOG")" -eq 1 ] || fail "case1: stub invoked $(wc -l < "$STUB_LOG") times, expected 1"
grep -qF "$BUNDLE_DIR" "$STUB_LOG" || fail "case1: stub argv missing absolute bundle path"
grep -q 'capability' "$STUB_LOG" || fail "case1: stub argv missing 'capability'"
grep -q 'install' "$STUB_LOG" || fail "case1: stub argv missing 'install'"
grep -q -- '--yes' "$STUB_LOG" || fail "case1: stub argv missing '--yes'"
grep -q 'global' "$STUB_LOG" || fail "case1: stub argv missing 'global' scope value"
[ -f "$STATE_FILE" ] || fail "case1: sidecar state file not created"
pass "case1: first-run auto-install prints notice, installs once, writes sidecar"

# Case 2: unchanged rerun -> completely silent, zero new invocations.
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case2: exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case2: stdout not empty on unchanged rerun"
[ -z "$(cat "$STDERR_FILE")" ] || fail "case2: stderr not empty on unchanged rerun"
[ "$(wc -l < "$STUB_LOG")" -eq "$PREV_LOG_LINES" ] || fail "case2: install invoked on unchanged rerun"
pass "case2: unchanged rerun is silent and invokes install zero times"

# Case 3: bundle edit -> re-grant with a fresh notice.
printf 'edit\n' >> "$BUNDLE_DIR/capability.json"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case3: exit status $STATUS, expected 0"
[ "$(cat "$STDOUT_FILE")" = "Auto-installed capability: beads (user scope)" ] \
  || fail "case3: stdout notice mismatch after edit: $(cat "$STDOUT_FILE")"
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 1)) ] \
  || fail "case3: stub invoked $(wc -l < "$STUB_LOG") times after edit, expected $((PREV_LOG_LINES + 1))"
pass "case3: bundle edit re-grants with a fresh notice"

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
PLUGIN_DIR="$SCRATCH/plugin"
BUNDLE_DIR="$PLUGIN_DIR/.gsd/capabilities/beads"
mkdir -p "$BUNDLE_DIR"
printf '{"id":"beads"}\n' > "$BUNDLE_DIR/capability.json"
GSD_HOME="$SCRATCH/home"
mkdir -p "$GSD_HOME"
STATE_FILE="$GSD_HOME/.gsd/capability-auto-install-beads.hash"
CONFIG_DIR="$SCRATCH/no-gsd-core-here"
mkdir -p "$CONFIG_DIR"
WORKDIR="$SCRATCH/workdir"
mkdir -p "$WORKDIR"
STDOUT_FILE="$SCRATCH/stdout"
STDERR_FILE="$SCRATCH/stderr"
(
  cd "$WORKDIR" && \
  PATH="/usr/bin:/bin" CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" \
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
PARITY_PLUGIN="$PARITY_ROOT/plugin"
PARITY_BUNDLE="$PARITY_PLUGIN/.gsd/capabilities/beads"
mkdir -p "$PARITY_BUNDLE"
printf '{"id":"beads"}\n' > "$PARITY_BUNDLE/capability.json"
PARITY_BIN="$PARITY_ROOT/bin"
mkdir -p "$PARITY_BIN"
PARITY_STUB_LOG="$PARITY_ROOT/stub.log"
: > "$PARITY_STUB_LOG"
cat > "$PARITY_BIN/gsd-tools" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$PARITY_STUB_LOG"
exit 0
STUB
chmod +x "$PARITY_BIN/gsd-tools"

CWD_A="$PARITY_ROOT/cwd-a"; mkdir -p "$CWD_A"
CWD_B="$PARITY_ROOT/cwd-b"; mkdir -p "$CWD_B"
GSD_HOME_A="$PARITY_ROOT/home-a"; mkdir -p "$GSD_HOME_A"
GSD_HOME_B="$PARITY_ROOT/home-b"; mkdir -p "$GSD_HOME_B"

OUT_SET_FILE="$PARITY_ROOT/out-set"
ERR_SET_FILE="$PARITY_ROOT/err-set"
# Run 1: CLAUDE_PLUGIN_ROOT exported explicitly.
(
  cd "$CWD_A" && \
  PATH="$PARITY_BIN:$PATH" CLAUDE_PLUGIN_ROOT="$PARITY_PLUGIN" GSD_HOME="$GSD_HOME_A" \
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
  PATH="$PARITY_BIN:$PATH" GSD_HOME="$GSD_HOME_B" \
    env -u CLAUDE_PLUGIN_ROOT bash "$PARITY_SCRIPT_COPY" beads >"$OUT_UNSET_FILE" 2>"$ERR_UNSET_FILE"
)
STATUS_UNSET=$?
[ "$STATUS_UNSET" -eq 0 ] || fail "case6: CLAUDE_PLUGIN_ROOT-unset run exited $STATUS_UNSET, expected 0"

[ "$(cat "$OUT_SET_FILE")" = "$(cat "$OUT_UNSET_FILE")" ] || fail "case6: stdout differs between CLAUDE_PLUGIN_ROOT set/unset runs"
[ "$(cat "$ERR_SET_FILE")" = "$(cat "$ERR_UNSET_FILE")" ] || fail "case6: stderr differs between CLAUDE_PLUGIN_ROOT set/unset runs"
[ "$(wc -l < "$PARITY_STUB_LOG")" -eq 2 ] || fail "case6: expected exactly 2 stub invocations across both runs, got $(wc -l < "$PARITY_STUB_LOG")"
pass "case6: CLAUDE_PLUGIN_ROOT set vs. derived-from-\$0 produce byte-identical output"
rm -rf "$PARITY_ROOT" 2>/dev/null

echo "ALL PASS"
exit 0
