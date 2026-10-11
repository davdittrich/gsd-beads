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
HOOK="$REPO_ROOT/hooks/session-start.sh"

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
export CLAUDE_PLUGIN_ROOT="$REPO_ROOT"

run_hook() {
  ( cd "$WORKDIR" && bash "$HOOK" ) >"$SCRATCH/stdout" 2>"$SCRATCH/stderr"
  local _status=$?
  [ "$_status" -eq 0 ] || fail "$WORKDIR: hook exited $_status: $(cat "$SCRATCH/stderr")"
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

# Stub plugin root: the real session-start.sh plus an auto-install stub that
# prints its install notice on stdout, as the real one does on success.
STUB_ROOT="$SCRATCH/stub-plugin"
mkdir -p "$STUB_ROOT/hooks" "$STUB_ROOT/.agents/skills/beads"
cp "$HOOK" "$STUB_ROOT/hooks/session-start.sh"
cp "$REPO_ROOT/.agents/skills/beads/PRIME.md" "$STUB_ROOT/.agents/skills/beads/PRIME.md"
printf '%s\n' '#!/usr/bin/env bash' 'echo "Auto-installed capability: beads (user scope)"' \
  > "$STUB_ROOT/hooks/capability-auto-install.sh"

# Case 4: hook stdout is the bd prime JSON and nothing else.
WORKDIR="$SCRATCH/case4"
mkdir -p "$WORKDIR/.beads"
CLAUDE_PLUGIN_ROOT="$STUB_ROOT" run_hook
[ "$(cat "$SCRATCH/stdout")" = '{"stub":"bd prime"}' ] \
  || fail "case4: stdout is not exactly the bd prime JSON: $(cat "$SCRATCH/stdout")"
grep -qx 'Auto-installed capability: beads (user scope)' "$SCRATCH/stderr" \
  || fail "case4: install notice did not reach stderr"
pass "case4: install notice goes to stderr, stdout carries only hook JSON"

# Case 5: .beads is a symlink to a directory outside the repo -> no write.
WORKDIR="$SCRATCH/case5"
OUTSIDE="$SCRATCH/case5-outside"
mkdir -p "$WORKDIR" "$OUTSIDE"
ln -s "$OUTSIDE" "$WORKDIR/.beads"
CLAUDE_PLUGIN_ROOT="$STUB_ROOT" run_hook
[ ! -e "$OUTSIDE/PRIME.md" ] || fail "case5: PRIME.md written through symlinked .beads"
pass "case5: symlinked .beads is never written through"

# Case 6: no bd on PATH -> exit 0 silently instead of exec failing with 127.
WORKDIR="$SCRATCH/case6"
NOBD_BIN="$SCRATCH/nobd-bin"
mkdir -p "$WORKDIR/.beads" "$NOBD_BIN"
ln -s "$(command -v bash)" "$NOBD_BIN/bash"
ln -s "$(command -v cp)" "$NOBD_BIN/cp"
PATH="$NOBD_BIN" CLAUDE_PLUGIN_ROOT="$STUB_ROOT" run_hook
[ ! -s "$SCRATCH/stdout" ] || fail "case6: stdout not empty without bd: $(cat "$SCRATCH/stdout")"
pass "case6: missing bd exits 0 with empty stdout"

# Case 7: SessionStart has an explicit timeout covering the bounded lock wait.
python3 -I - "$REPO_ROOT/hooks/hooks.json" <<'PY' || fail "case7: SessionStart timeout missing or below 60s"
import json, sys
hooks = json.load(open(sys.argv[1]))["hooks"]["SessionStart"]
timeouts = [h.get("timeout") for group in hooks for h in group["hooks"]]
sys.exit(0 if timeouts and all(isinstance(v, int) and v >= 60 for v in timeouts) else 1)
PY
pass "case7: SessionStart hook declares an explicit timeout"

# Claude Code shows exit-0 hook stderr only in its debug log; a
# systemMessage is shown to the user.
CONSENT_ROOT="$SCRATCH/consent-plugin"
mkdir -p "$CONSENT_ROOT/hooks" "$CONSENT_ROOT/.agents/skills/beads"
cp "$HOOK" "$CONSENT_ROOT/hooks/session-start.sh"
cp "$REPO_ROOT/.agents/skills/beads/PRIME.md" "$CONSENT_ROOT/.agents/skills/beads/PRIME.md"
# session-start.sh matches the installer's consent line by its prefix; take
# that prefix from the installer itself so a reworded line fails here.
CONSENT_PREFIX="$(grep -oF 'capability-auto-install: $CAP_ID needs your consent before install; run: ' \
  "$REPO_ROOT/hooks/capability-auto-install.sh" | head -n 1)"
[ -n "$CONSENT_PREFIX" ] || fail "consent prefix literal missing from capability-auto-install.sh"
CONSENT_PREFIX="${CONSENT_PREFIX/\$CAP_ID/beads}"
grep -qF "\"$CONSENT_PREFIX\"*)" "$HOOK" || fail "session-start.sh does not match the installer's consent prefix"
CONSENT_LINE="${CONSENT_PREFIX}bash /p/hooks/capability-auto-install.sh --consent beads"
printf '%s\n' '#!/usr/bin/env bash' "echo '$CONSENT_LINE' >&2" > "$CONSENT_ROOT/hooks/capability-auto-install.sh"
check_consent_json() {
  python3 -I -c '
import json, sys
out = json.load(open(sys.argv[1]))
message = out.get("systemMessage", "")
assert "bash /p/hooks/capability-auto-install.sh --consent beads" in message, message
assert "yourself" in message and "agent" in message, message
assert out.get("stub") == sys.argv[2] or (sys.argv[2] == "" and set(out) == {"systemMessage"}), out
' "$SCRATCH/stdout" "$1"
}

# Case 8: a consent request reaches the user as systemMessage beside bd's JSON.
WORKDIR="$SCRATCH/case8"
mkdir -p "$WORKDIR/.beads"
CLAUDE_PLUGIN_ROOT="$CONSENT_ROOT" run_hook
check_consent_json "bd prime" || fail "case8: stdout is not bd JSON plus the consent systemMessage: $(cat "$SCRATCH/stdout")"
grep -qxF "$CONSENT_LINE" "$SCRATCH/stderr" || fail "case8: consent line no longer on stderr"
pass "case8: consent command reaches the user as systemMessage, stdout stays one JSON object"

# Case 9: without bd the consent request is still one JSON object.
WORKDIR="$SCRATCH/case9"
mkdir -p "$WORKDIR/.beads"
ln -s "$(command -v python3)" "$NOBD_BIN/python3"
PATH="$NOBD_BIN" CLAUDE_PLUGIN_ROOT="$CONSENT_ROOT" run_hook
check_consent_json "" || fail "case9: stdout is not the consent systemMessage alone: $(cat "$SCRATCH/stdout")"
pass "case9: consent systemMessage is emitted without bd"

echo "ALL PASS"
