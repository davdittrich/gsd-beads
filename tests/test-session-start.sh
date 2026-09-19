#!/usr/bin/env bash
# Stdlib-only smoke test (N5): no framework, no fixtures dir. Covers the
# self-heal guard's symlink hardening (review finding) -- `[ ! -e "$DEST" ]`
# alone follows symlinks and reports false for a *dangling* one, so a
# planted dangling symlink at .beads/PRIME.md used to pass the guard and
# reach `cp`. On this machine's GNU coreutils `cp`, that alone is already
# refused (verified separately) -- case2 below is a behavioral contract
# test (DEST is never written through), not proof this exact `cp` was ever
# exploitable; the added `[ ! -L "$DEST" ]` guard is portability
# defense-in-depth for a `cp` that doesn't share that default (BusyBox,
# some BSD builds).
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/plugins/beads-lifecycle/hooks/session-start.sh"

fail() { echo "FAIL: $1"; exit 1; }
pass() { echo "PASS: $1"; }

SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# A stub `bd` on PATH: capability-auto-install.sh already fails closed with
# no real gsd-tools present, and `bd prime --hook-json` is the hook's own
# final `exec`, so it must exist for the script to run to completion.
BIN_DIR="$SCRATCH/bin"
mkdir -p "$BIN_DIR"
cat >"$BIN_DIR/bd" <<'SH'
#!/usr/bin/env bash
echo '{"stub":"bd prime"}'
SH
chmod +x "$BIN_DIR/bd"
export PATH="$BIN_DIR:$PATH"
export CLAUDE_PLUGIN_ROOT="$REPO_ROOT/plugins/beads-lifecycle"

run_hook() {
  ( cd "$WORKDIR" && bash "$HOOK" ) >"$SCRATCH/stdout" 2>"$SCRATCH/stderr"
}

# Case 1: no DEST yet -> self-heal copies the shipped PRIME.md.
WORKDIR="$SCRATCH/case1"
mkdir -p "$WORKDIR/.beads"
run_hook
[ -f "$WORKDIR/.beads/PRIME.md" ] || fail "case1: PRIME.md was not written when absent"
[ -s "$WORKDIR/.beads/PRIME.md" ] || fail "case1: PRIME.md written empty"
pass "case1: self-heal copies PRIME.md when DEST is absent"

# Case 2: DEST is a dangling symlink -> must NOT be written through.
WORKDIR="$SCRATCH/case2"
mkdir -p "$WORKDIR/.beads"
TARGET="$SCRATCH/case2-target-outside-beads"
ln -s "$TARGET" "$WORKDIR/.beads/PRIME.md"
run_hook
[ -L "$WORKDIR/.beads/PRIME.md" ] || fail "case2: symlink at DEST was replaced"
[ ! -e "$TARGET" ] || fail "case2: cp wrote through the dangling symlink to $TARGET"
pass "case2: dangling symlink at DEST is left untouched, not written through"

# Case 3: DEST is a real file already -> untouched (pre-existing contract).
WORKDIR="$SCRATCH/case3"
mkdir -p "$WORKDIR/.beads"
echo "existing content" > "$WORKDIR/.beads/PRIME.md"
run_hook
[ "$(cat "$WORKDIR/.beads/PRIME.md")" = "existing content" ] \
  || fail "case3: existing real PRIME.md was overwritten"
pass "case3: existing real PRIME.md is left untouched"

echo "ALL PASS"
