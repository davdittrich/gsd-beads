#!/usr/bin/env bash
# Stdlib-only smoke test (N5): no framework, no fixtures dir. Every case runs
# against a scratch plugin root + scratch GSD_HOME under mktemp -d, with a
# stub `gsd-tools` on PATH -- no real capability install ever occurs and this
# repo's own real $HOME/.gsd/ is never touched.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/hooks/capability-auto-install.sh"

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

echo "ALL PASS"
exit 0
