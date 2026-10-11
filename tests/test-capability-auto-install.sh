#!/usr/bin/env bash
# Stdlib-only smoke test (N5): no framework, no fixtures dir. Every case runs
# against scratch plugin/runtime roots. Focused cases use a stub runtime-owned
# `gsd-tools.cjs`; the final `/dev/shm` case uses the active/current CLI. This
# repo's own real $HOME/.gsd/ is never touched.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/hooks/capability-auto-install.sh"
REAL_PYTHON="$(command -v python3)"
GSD_CORE_REPO="${GSD_CORE_REPO:-$REPO_ROOT/../gsd-core}"
ACTIVE_CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
ACTIVE_GSD_TOOLS="$ACTIVE_CODEX_HOME/gsd-core/bin/gsd-tools.cjs"

fail() { echo "FAIL: $1"; exit 1; }
pass() { echo "PASS: $1"; }

# The repo root is the plugin root; only this allowlist is the capability bundle.
BUNDLE_ALLOWLIST=(capability.json scripts skills fragments GSD-CORE-PATCH.md)
copy_allowlist() {
  local _entry
  mkdir -p "$2"
  for _entry in "${BUNDLE_ALLOWLIST[@]}"; do
    cp -rP "$1/$_entry" "$2/$_entry" || return 1
  done
  find "$2" -name __pycache__ -type d -prune -exec rm -rf {} +
}
# Dev-only content a plugin root carries that the hook must never install.
plant_noise() {
  mkdir -p "$1/tests" "$1/scripts/__pycache__"
  printf 'noise\n' > "$1/tests/noise.txt"
  printf 'noise\n' > "$1/scripts/__pycache__/noise.pyc"
}
make_plugin_root() {
  copy_allowlist "$REPO_ROOT" "$1" && plant_noise "$1"
}

if command -v sha256sum >/dev/null 2>&1; then
  TEST_HASH_CMD=(sha256sum)
else
  TEST_HASH_CMD=(shasum -a 256)
fi

# Spy cases patch the hook's own python processes. -I ignores PYTHONPATH,
# but a venv's site-packages still loads under -I, so the python3 wrapper
# execs this venv with the hook's argv untouched; its sitecustomize runs the
# case's spy only when GSD_TEST_SPY_SITE names one.
SPY_VENV="$(mktemp -d)"
trap '[ -n "${SCRATCH:-}" ] && rm -rf "$SCRATCH" 2>/dev/null; rm -rf "$SPY_VENV"' EXIT
"$REAL_PYTHON" -m venv --without-pip "$SPY_VENV" || fail "spy venv creation failed"
cat > "$("$SPY_VENV/bin/python3" -I -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/sitecustomize.py" <<'PY'
import os

_spy_site = os.environ.get("GSD_TEST_SPY_SITE", "")
if _spy_site:
    _spy_path = os.path.join(_spy_site, "sitecustomize.py")
    with open(_spy_path, encoding="utf-8") as _stream:
        exec(compile(_stream.read(), _spy_path, "exec"), {"__name__": "gsd_test_spy"})
PY

# setup <stub-exit-status>
# Builds a scratch plugin root (root-manifest layout, plus dev-only noise), a
# scratch GSD_HOME (so the sidecar state file never touches the real $HOME),
# and a stub runtime-owned `gsd-tools.cjs` that logs its argv and exits with the
# given status. Sets SCRATCH, PLUGIN_DIR, BUNDLE_DIR, GSD_HOME, BIN_DIR,
# STUB_LOG, STATE_FILE, SKILLS_ROOT.
setup() {
  SCRATCH="$(mktemp -d)"
  CODEX_HOME="$SCRATCH/.codex"
  CLAUDE_CONFIG_DIR="$SCRATCH/.claude"
  PLUGIN_DIR="$CODEX_HOME/plugins/cache/gsd-beads/beads-lifecycle/test"
  BUNDLE_DIR="$PLUGIN_DIR"
  make_plugin_root "$PLUGIN_DIR"

  GSD_HOME="$SCRATCH/home"
  mkdir -p "$GSD_HOME"
  INSTALLED_BUNDLE="$GSD_HOME/.gsd/capabilities/beads"
  copy_allowlist "$BUNDLE_DIR" "$INSTALLED_BUNDLE"
  STATE_FILE="$GSD_HOME/.gsd/capability-auto-install-beads.projections"
  LEGACY_STATE_FILE="$GSD_HOME/.gsd/capability-auto-install-beads.hash"
  SKILLS_ROOT="$SCRATCH/.agents/skills"
  CLAUDE_SKILLS_ROOT="$SCRATCH/.claude/skills"
  mkdir -p "$SKILLS_ROOT" "$CLAUDE_SKILLS_ROOT"

  BIN_DIR="$CODEX_HOME/gsd-core/bin"
  mkdir -p "$BIN_DIR"
  TEST_BIN="$SCRATCH/test-bin"
  mkdir -p "$TEST_BIN"
  # Every case runs the hook's argv as is (-I included) on the spy venv.
  cat > "$TEST_BIN/python3" <<SHIM
#!/usr/bin/env bash
exec "$SPY_VENV/bin/python3" "\$@"
SHIM
  chmod +x "$TEST_BIN/python3"
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
case "\$*" in
  "capability install "*)
    if [ -n "\${STUB_REQUIRE_CONSENT:-}" ] && [[ "\$*" != *" --yes"* ]]; then
      printf '%s\n' '{"status":"aborted","requiresConsent":true,"scope":"global"}'
      exit 1
    fi
    _p="\$3"
    # Like gsd-core, a consented install copies the source bundle into place.
    if [ -n "\${STUB_REQUIRE_CONSENT:-}\${STUB_COPY_INSTALL:-}" ]; then
      rm -rf "$INSTALLED_BUNDLE" && cp -R "\$_p" "$INSTALLED_BUNDLE" || exit 1
    fi
    if [ -d "\$_p" ]; then
      printf '%s\n' "\$_p" > "$SCRATCH/staged.path"
      LC_ALL=C ls -A "\$_p" | tr '\n' ' ' > "$SCRATCH/staged.ls"
      find "\$_p" \( -name __pycache__ -o -name tests \) > "$SCRATCH/staged.noise"
    fi ;;
esac
# Enabled state persists like gsd-core: set without a flag keeps it.
case "\$*" in
  "capability state --runtime "*" --raw")
    [ -z "\${STUB_STATE_FAIL:-}" ] || exit 1
    _enabled="\$(cat "$SCRATCH/enabled" 2>/dev/null || echo true)"
    printf '{"capabilities":[{"id":"beads","enabled":%s}]}\n' "\$_enabled"
    exit 0 ;;
  "capability set beads --disable "*) echo false > "$SCRATCH/enabled" ;;
  "capability set beads --enable "*) echo true > "$SCRATCH/enabled" ;;
esac
exit $stub_status
STUB
  chmod +x "$BIN_DIR/gsd-tools.cjs"
  mkdir -p "$CLAUDE_CONFIG_DIR/gsd-core/bin"
  cp -f "$BIN_DIR/gsd-tools.cjs" "$CLAUDE_CONFIG_DIR/gsd-core/bin/gsd-tools.cjs"

  STDOUT_FILE="$SCRATCH/stdout"
  STDERR_FILE="$SCRATCH/stderr"
  TEST_PYTHONPATH=""
  TEST_SPY_SITE=""
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
  copy_allowlist "$BUNDLE_DIR" "$INSTALLED_BUNDLE"
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
    PYTHONPATH="${TEST_PYTHONPATH:-}" GSD_TEST_SPY_SITE="${TEST_SPY_SITE:-}" R1_LOCK_SPY_LOG="${R1_LOCK_SPY_LOG:-}" \
    R2_PUBLISH_SPY_LOG="${R2_PUBLISH_SPY_LOG:-}" R2_LEGACY_PATH="${R2_LEGACY_PATH:-}" \
    R2_LEDGER_PATH="${R2_LEDGER_PATH:-}" PYTHONDONTWRITEBYTECODE=1 \
    R2_REPLACE_FAIL="${R2_REPLACE_FAIL:-}" R2_REPLACE_READY="${R2_REPLACE_READY:-}" \
    R2_REPLACE_RELEASE="${R2_REPLACE_RELEASE:-}" PATH="$TEST_BIN:/usr/bin:/bin" \
    GSD_AUTO_INSTALL_LOCK_WAIT_SECONDS="${LOCK_WAIT_SECONDS:-0}" \
    bash "$SCRIPT" "$@" >"$STDOUT_FILE" 2>"$STDERR_FILE"
  STATUS=$?
}

### Slice 1: compatibility, runtime mapping, and exact native argv ###
python3 - "$REPO_ROOT/capability.json" \
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
grep -Eq '^capability install /[^ ]+ --scope global$' "$STUB_LOG" \
  || fail "case1: stub argv missing absolute staged bundle path (or auto-consented)"
[ "$(cat "$SCRATCH/staged.ls")" = "GSD-CORE-PATCH.md capability.json fragments scripts skills " ] \
  || fail "case1: staged bundle is not exactly the allowlist: $(cat "$SCRATCH/staged.ls")"
[ ! -s "$SCRATCH/staged.noise" ] || fail "case1: staged bundle contains tests/ or __pycache__"
case "$(cat "$SCRATCH/staged.path")" in "$PLUGIN_DIR"*) fail "case1: install source is inside the plugin root" ;; esac
# R28: gsd-core records the install path as the ledger source that
# `capability update` re-fetches, so it must be a stable path that outlives
# the hook and holds exactly the installed allowlist.
STABLE_SOURCE="$GSD_HOME/.gsd/capability-auto-install-beads.source/beads"
[ "$(cat "$SCRATCH/staged.path")" = "$STABLE_SOURCE" ] \
  || fail "case1: install source is not the stable source path: $(cat "$SCRATCH/staged.path")"
[ "$(fixture_tree_hash "$STABLE_SOURCE")" = "$(fixture_tree_hash "$INSTALLED_BUNDLE")" ] \
  || fail "case1: stable source does not persist the installed allowlist"
[ -z "$(find "$GSD_HOME/.gsd" -maxdepth 1 -name '.capability-auto-install-beads.stage.*')" ] \
  || fail "case1: temporary staging directory leaked after exit"
grep -q 'capability' "$STUB_LOG" || fail "case1: stub argv missing 'capability'"
grep -q 'install' "$STUB_LOG" || fail "case1: stub argv missing 'install'"
! grep -q -- '--yes' "$STUB_LOG" || fail "case1: hook auto-consented with --yes"
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

### Case 2a (R28): a missing stable source re-records it once ###
# Installs made before R28 recorded a since-deleted temp dir as the source.
rm -rf "$GSD_HOME/.gsd/capability-auto-install-beads.source"
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
run_script beads
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 3)) ] \
  || fail "case2a: missing stable source did not trigger a reinstall"
[ -f "$GSD_HOME/.gsd/capability-auto-install-beads.source/beads/capability.json" ] \
  || fail "case2a: stable source was not republished"
pass "case2a: a missing stable source triggers one reinstall from the stable path"

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

### Case 3b (R23): GSD_RUNTIME cannot override plugin-cache ownership ###
# A --plugin-dir working tree or a mismatched runtime must not install
# uncommitted content machine-wide just because GSD_RUNTIME is set.
setup 0
seed_selected "$CLAUDE_SKILLS_ROOT"
export GSD_RUNTIME=claude
run_script beads
unset GSD_RUNTIME
[ "$STATUS" -eq 0 ] || fail "case3b: exit status $STATUS, expected 0"
[ "$(wc -l < "$STUB_LOG")" -eq 0 ] || fail "case3b: runtime mismatch reached gsd-tools"
grep -q 'runtime selection failed' "$STDERR_FILE" || fail "case3b: missing mismatch diagnostic"
CUSTOM_PLUGIN="$SCRATCH/worktree-plugin"
make_plugin_root "$CUSTOM_PLUGIN"
PLUGIN_DIR="$CUSTOM_PLUGIN"
BUNDLE_DIR="$CUSTOM_PLUGIN"
export GSD_RUNTIME=codex
run_script beads
unset GSD_RUNTIME
[ "$(wc -l < "$STUB_LOG")" -eq 0 ] || fail "case3b: GSD_RUNTIME let an uncached plugin dir install"
pass "case3b: GSD_RUNTIME never bypasses the plugin-cache ownership check"
teardown

### Case 3f (R23): ownership is decided on the resolved plugin path ###
setup 0
seed_selected "$SKILLS_ROOT"
OUTSIDE_PLUGIN="$SCRATCH/outside-plugin"
make_plugin_root "$OUTSIDE_PLUGIN"
ln -s "$OUTSIDE_PLUGIN" "$CODEX_HOME/plugins/linked"
PLUGIN_DIR="$CODEX_HOME/plugins/linked"
BUNDLE_DIR="$OUTSIDE_PLUGIN"
run_script beads
[ "$(wc -l < "$STUB_LOG")" -eq 0 ] || fail "case3f: symlinked plugin root outside the cache was trusted"
grep -q 'runtime selection failed' "$STDERR_FILE" || fail "case3f: missing ownership diagnostic"
pass "case3f: a cache-path symlink to an outside tree is not runtime-owned"
teardown

### Case 3g (R23): relative or missing home roots fail closed ###
for _var in HOME GSD_HOME CODEX_HOME CLAUDE_CONFIG_DIR; do
  setup 0
  seed_selected "$SKILLS_ROOT"
  case "$_var" in
    HOME) _home=relative-home; _gsd="$GSD_HOME"; _codex="$CODEX_HOME"; _claude="$CLAUDE_CONFIG_DIR" ;;
    GSD_HOME) _home="$SCRATCH"; _gsd=relative-gsd; _codex="$CODEX_HOME"; _claude="$CLAUDE_CONFIG_DIR" ;;
    CODEX_HOME) _home="$SCRATCH"; _gsd="$GSD_HOME"; _codex=relative-codex; _claude="$CLAUDE_CONFIG_DIR" ;;
    CLAUDE_CONFIG_DIR) _home="$SCRATCH"; _gsd="$GSD_HOME"; _codex="$CODEX_HOME"; _claude=relative-claude ;;
  esac
  ( cd "$SCRATCH" && HOME="$_home" GSD_HOME="$_gsd" CODEX_HOME="$_codex" CLAUDE_CONFIG_DIR="$_claude" \
      CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" PATH="$TEST_BIN:/usr/bin:/bin" bash "$SCRIPT" beads ) \
    >"$STDOUT_FILE" 2>"$STDERR_FILE"
  [ "$?" -eq 0 ] || fail "case3g: $_var relative: nonzero exit"
  [ "$(wc -l < "$STUB_LOG")" -eq 0 ] || fail "case3g: relative $_var reached gsd-tools"
  [ ! -e "$SCRATCH/relative-gsd" ] && [ ! -e "$SCRATCH/relative-home" ] \
    || fail "case3g: relative $_var created state under cwd"
  grep -q 'must be absolute' "$STDERR_FILE" || fail "case3g: relative $_var: missing diagnostic"
  teardown
done
setup 0
( cd "$SCRATCH" && env -u HOME GSD_HOME="$GSD_HOME" CODEX_HOME="$CODEX_HOME" \
    CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" \
    PATH="$TEST_BIN:/usr/bin:/bin" bash "$SCRIPT" beads ) >"$STDOUT_FILE" 2>"$STDERR_FILE"
[ "$?" -eq 0 ] || fail "case3g: unset HOME aborted the hook"
[ "$(wc -l < "$STUB_LOG")" -eq 0 ] || fail "case3g: unset HOME reached gsd-tools"
teardown
pass "case3g: relative or unset HOME/GSD_HOME/CODEX_HOME/CLAUDE_CONFIG_DIR fail closed"

### Case 3h (R23/RS1): consent is never automatic; --consent installs under the lock ###
# The stable source is what `capability update` re-fetches, so until the user
# consents it must keep its previous bytes (or stay absent).
for _prior in present absent; do
  setup 0
  seed_selected "$SKILLS_ROOT"
  # Installed bytes differ from the bundle: the install is genuinely needed.
  printf 'x' >> "$INSTALLED_BUNDLE/GSD-CORE-PATCH.md"
  PRIOR_SOURCE="$GSD_HOME/.gsd/capability-auto-install-beads.source/beads"
  if [ "$_prior" = present ]; then
    mkdir -p "$PRIOR_SOURCE"
    printf 'previous\n' > "$PRIOR_SOURCE/previous.marker"
  fi
  export STUB_REQUIRE_CONSENT=1
  run_script beads
  [ "$STATUS" -eq 0 ] || fail "case3h($_prior): exit status $STATUS, expected 0"
  ! grep -q -- '--yes' "$STUB_LOG" || fail "case3h($_prior): hook passed --yes"
  ! grep -q '^capability set' "$STUB_LOG" || fail "case3h($_prior): consent-blocked install reached capability set"
  [ -z "$(cat "$STDOUT_FILE")" ] || fail "case3h($_prior): consent block wrote stdout"
  [ "$(cat "$STDERR_FILE")" = "capability-auto-install: beads needs your consent before install; run: bash $PLUGIN_DIR/hooks/capability-auto-install.sh --consent beads" ] \
    || fail "case3h($_prior): consent message is not the single consent-mode command: $(cat "$STDERR_FILE")"
  if [ "$_prior" = present ]; then
    [ "$(LC_ALL=C ls -A "$PRIOR_SOURCE")" = previous.marker ] \
      && [ "$(cat "$PRIOR_SOURCE/previous.marker")" = previous ] \
      || fail "case3h: consent block changed the stable source"
  else
    [ ! -e "$GSD_HOME/.gsd/capability-auto-install-beads.source" ] \
      || fail "case3h: consent block created the stable source"
  fi
  [ ! -e "$STATE_FILE" ] || fail "case3h($_prior): consent-blocked install recorded a ledger row"
  [ -z "$(find "$GSD_HOME/.gsd" -maxdepth 1 -name '.capability-auto-install-beads.*')" ] \
    || fail "case3h($_prior): temporary directories leaked"
  run_script --consent beads
  unset STUB_REQUIRE_CONSENT
  [ "$STATUS" -eq 0 ] || fail "case3h($_prior): consent run exit status $STATUS, expected 0"
  [ "$(grep -c -- "^capability install $PRIOR_SOURCE --scope global --yes\$" "$STUB_LOG")" -eq 1 ] \
    || fail "case3h($_prior): consent run did not install the stable source with --yes once: $(cat "$STUB_LOG")"
  [ "$(cat "$STDOUT_FILE")" = "Auto-installed capability: beads (user scope)" ] && [ -z "$(cat "$STDERR_FILE")" ] \
    || fail "case3h($_prior): consent run did not complete: $(cat "$STDERR_FILE")"
  cmp -s "$PLUGIN_DIR/GSD-CORE-PATCH.md" "$PRIOR_SOURCE/GSD-CORE-PATCH.md" \
    && [ ! -e "$PRIOR_SOURCE/previous.marker" ] \
    || fail "case3h($_prior): consent run did not publish the candidate as the stable source"
  [ -f "$STATE_FILE" ] || fail "case3h($_prior): consent run recorded no ledger row"
  teardown
done
pass "case3h: consent is never automatic, leaves the stable source untouched, and --consent installs"

### Case 3i (V4/S4): consent already given converges instead of re-asking ###
# The user consented outside the hook: installed bytes now equal the
# bundle, but a bare install still answers requiresConsent. Re-asking every
# SessionStart was a dead end; the hook must project and record instead.
setup 0
seed_selected "$SKILLS_ROOT"
export STUB_REQUIRE_CONSENT=1
run_script beads
unset STUB_REQUIRE_CONSENT
[ "$STATUS" -eq 0 ] || fail "case3i: exit status $STATUS, expected 0"
! grep -q -- '--yes' "$STUB_LOG" || fail "case3i: hook passed --yes"
grep -qx "capability set beads --runtime codex --scope global --config-dir $CODEX_HOME" "$STUB_LOG" \
  || fail "case3i: consented install never reached capability set: $(cat "$STDERR_FILE")"
[ -f "$STATE_FILE" ] || fail "case3i: consented install did not record a ledger row: $(cat "$STDERR_FILE")"
[ "$(cat "$STDOUT_FILE")" = "Auto-installed capability: beads (user scope)" ] \
  || fail "case3i: converged install did not print the notice: $(cat "$STDOUT_FILE")"
[ -z "$(cat "$STDERR_FILE")" ] \
  || fail "case3i: converged install still asked for consent: $(cat "$STDERR_FILE")"
PREV_LOG_LINES="$(wc -l < "$STUB_LOG")"
STUB_REQUIRE_CONSENT=1 run_script beads
[ -z "$(cat "$STDERR_FILE")" ] || fail "case3i: converged rerun re-asked for consent: $(cat "$STDERR_FILE")"
[ "$(wc -l < "$STUB_LOG")" -eq $((PREV_LOG_LINES + 1)) ] || fail "case3i: converged rerun invoked a native writer"
pass "case3i: an already-consented install converges and stops re-asking"
teardown

### Case 3j (V4/N10): a failed install never leaves an unverified recorded source ###
# gsd-core records the stable source path; `capability update` re-fetches it.
# A failed install must leave the previous source bytes there, or none.
for _prior in present absent; do
  setup 1
  seed_selected "$SKILLS_ROOT"
  printf 'x' >> "$INSTALLED_BUNDLE/GSD-CORE-PATCH.md"
  PRIOR_SOURCE="$GSD_HOME/.gsd/capability-auto-install-beads.source/beads"
  if [ "$_prior" = present ]; then
    mkdir -p "$PRIOR_SOURCE"
    printf 'previous\n' > "$PRIOR_SOURCE/previous.marker"
  fi
  run_script beads
  [ "$STATUS" -eq 0 ] || fail "case3j($_prior): exit status $STATUS, expected 0"
  grep -q 'capability install failed' "$STDERR_FILE" || fail "case3j($_prior): install failure not reported: $(cat "$STDERR_FILE")"
  if [ "$_prior" = present ]; then
    [ "$(cat "$PRIOR_SOURCE/previous.marker" 2>/dev/null)" = previous ] \
      || fail "case3j: previous source was not restored after a failed install"
    [ ! -e "$PRIOR_SOURCE/capability.json" ] || fail "case3j: unverified candidate left at the recorded source"
  else
    [ ! -e "$GSD_HOME/.gsd/capability-auto-install-beads.source" ] \
      || fail "case3j: unverified candidate left at the recorded source"
  fi
  [ -z "$(find "$GSD_HOME/.gsd" -maxdepth 1 -name '.capability-auto-install-beads.*')" ] \
    || fail "case3j($_prior): temporary directories leaked: $(find "$GSD_HOME/.gsd" -maxdepth 1 -name '.capability-auto-install-beads.*')"
  teardown
done
pass "case3j: a failed install restores the previous stable source"

### Case 3k (V4/N5): the selected-command contract check runs isolated python ###
setup 0
seed_selected "$SKILLS_ROOT"
N5_SITE="$SCRATCH/n5-site"
N5_CANARY="$SCRATCH/n5.canary"
mkdir -p "$N5_SITE"
printf '%s\n' 'import sys' \
  "if '--help' in getattr(sys, 'orig_argv', []): open('$N5_CANARY', 'a').write(' '.join(sys.orig_argv) + '\\n')" \
  > "$N5_SITE/sitecustomize.py"
TEST_PYTHONPATH="$N5_SITE"
run_script beads
TEST_PYTHONPATH=""
[ -f "$STATE_FILE" ] || fail "case3k: hook did not reach ledger publish: $(cat "$STDERR_FILE")"
[ ! -e "$N5_CANARY" ] || fail "case3k: contract check imported PYTHONPATH code: $(cat "$N5_CANARY")"
pass "case3k: the selected-command contract check ignores PYTHONPATH"
teardown

### Case 3l (V4/S8): a failed state query still lets the hook undo its own rollback ###
setup 0
seed_selected "$SKILLS_ROOT"
printf '\npython3 "$SYNC_PY" execute-plan\n' >> "$SKILLS_ROOT/gsd-beads-recall/SKILL.md"
STUB_STATE_FAIL=1 run_script beads
grep -qx "capability set beads --disable --runtime codex --scope global --config-dir $CODEX_HOME" "$STUB_LOG" \
  || fail "case3l: failed verification was not rolled back"
[ -f "$GSD_HOME/.gsd/capability-auto-install-beads.codex.disabled" ] \
  || fail "case3l: rollback after a failed state query wrote no re-enable marker"
seed_selected "$SKILLS_ROOT"
run_script beads
grep -qx "capability set beads --enable --runtime codex --scope global --config-dir $CODEX_HOME" "$STUB_LOG" \
  || fail "case3l: hook-disabled capability was never re-enabled: $(cat "$STDERR_FILE")"
[ -f "$STATE_FILE" ] || fail "case3l: re-enabled install did not converge: $(cat "$STDERR_FILE")"
pass "case3l: a state-query failure cannot leave the capability disabled forever"
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
[ "$(tail -n 1 "$STUB_LOG")" = "capability set beads --disable --runtime codex --scope global --config-dir $CODEX_HOME" ] \
  || fail "case3d: failed verification left the new bundle enabled"
pass "case3d: selected command verification rejects retired execute-plan"
teardown

### Case 3e (R1): stdlib-named modules planted in cwd never run in hook python ###
# `python3 -`/`python3 -c` put cwd first on sys.path, so a cloned repo's
# json.py would run inside the SessionStart hook and the task resolver.
setup 0
seed_selected "$SKILLS_ROOT"
PLANT_DIR="$SCRATCH/planted-cwd"
CANARY="$SCRATCH/planted.canary"
mkdir -p "$PLANT_DIR"
for _mod in json pathlib hashlib fcntl errno stat tempfile shlex subprocess; do
  printf 'open(%s, "a").write("%s\\n")\n' "'$CANARY'" "$_mod" > "$PLANT_DIR/$_mod.py"
done
cd "$PLANT_DIR" || fail "case3e: cannot enter planted cwd"
run_script beads
cd "$REPO_ROOT" || fail "case3e: cannot leave planted cwd"
[ "$STATUS" -eq 0 ] || fail "case3e: exit status $STATUS, expected 0"
[ -f "$STATE_FILE" ] || fail "case3e: hook did not reach ledger publish: $(cat "$STDERR_FILE")"
[ ! -e "$CANARY" ] || fail "case3e: hook imported planted cwd modules: $(tr '\n' ' ' < "$CANARY")"
RESOLVER_HOME="$SCRATCH/resolver-home"
mkdir -p "$RESOLVER_HOME/.gsd/capabilities/beads/scripts"
printf 'import sys\nprint("resolved", sys.argv[-1])\n' \
  > "$RESOLVER_HOME/.gsd/capabilities/beads/scripts/sync.py"
printf '%s\n' \
  'import json, subprocess, sys' \
  'invoke = json.load(open(sys.argv[1]))["taskContentResolver"]["invoke"]' \
  'args = [a.replace("{{id}}", "bd-1") for a in invoke["args"]]' \
  'sys.exit(subprocess.run([invoke["binary"], *args]).returncode)' \
  > "$SCRATCH/resolver-launch.py"
RESOLVER_OUT="$(cd "$PLANT_DIR" && GSD_HOME="$RESOLVER_HOME" PATH="/usr/bin:/bin" \
  "$REAL_PYTHON" -I "$SCRATCH/resolver-launch.py" "$REPO_ROOT/capability.json" 2>&1)"
[ "$RESOLVER_OUT" = "resolved bd-1" ] || fail "case3e: resolver did not reach sync.py: $RESOLVER_OUT"
[ ! -e "$CANARY" ] || fail "case3e: task resolver imported planted cwd modules: $(tr '\n' ' ' < "$CANARY")"
# V4/N3: a relative or empty GSD_HOME resolves against cwd, i.e. the repo.
mkdir -p "$PLANT_DIR/.gsd/capabilities/beads/scripts"
printf 'print("planted")\n' > "$PLANT_DIR/.gsd/capabilities/beads/scripts/sync.py"
for _gsd_home in . ""; do
  RESOLVER_OUT="$(cd "$PLANT_DIR" && HOME="$RESOLVER_HOME" GSD_HOME="$_gsd_home" PATH="/usr/bin:/bin" \
    "$REAL_PYTHON" -I "$SCRATCH/resolver-launch.py" "$REPO_ROOT/capability.json" 2>&1)"
  [ "$RESOLVER_OUT" = "resolved bd-1" ] \
    || fail "case3e: GSD_HOME='$_gsd_home' resolver ran a cwd-relative sync.py: $RESOLVER_OUT"
done
pass "case3e: planted cwd modules never run in hook or resolver python"
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
BUNDLE_DIR="$PLUGIN_DIR"
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
# Same fixed plugin/bundle dir for both runs (the staging path is random and never printed); each
# run gets its own fresh GSD_HOME so both see "no prior hash" and both print
# the notice. Each run's cwd is a scratch dir that is not the plugin root.
PARITY_ROOT="$(mktemp -d)"
PARITY_PLUGIN="$PARITY_ROOT/.codex/plugins/cache/gsd-beads/beads-lifecycle/test"
PARITY_BUNDLE="$PARITY_PLUGIN"
make_plugin_root "$PARITY_BUNDLE"
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
copy_allowlist "$PARITY_BUNDLE" "$GSD_HOME_A/.gsd/capabilities/beads"
copy_allowlist "$PARITY_BUNDLE" "$GSD_HOME_B/.gsd/capabilities/beads"

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
make_plugin_root "$CLAUDE_PLUGIN"
printf 'beads\n' > "$CLAUDE_SKILLS_ROOT/gsd-beads-recall/.gsd-capability-skill"
PLUGIN_DIR="$CLAUDE_PLUGIN"
BUNDLE_DIR="$CLAUDE_PLUGIN"
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
BUNDLE_DIR="$PLUGIN_DIR"
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
# Enabled state persists like gsd-core: set without a flag keeps it.
case "\$*" in
  "capability state --runtime "*" --raw")
    [ -z "\${STUB_STATE_FAIL:-}" ] || exit 1
    _enabled="\$(cat "$SCRATCH/enabled" 2>/dev/null || echo true)"
    printf '{"capabilities":[{"id":"beads","enabled":%s}]}\n' "\$_enabled"
    exit 0 ;;
  "capability set beads --disable "*) echo false > "$SCRATCH/enabled" ;;
  "capability set beads --enable "*) echo true > "$SCRATCH/enabled" ;;
esac
exit 0
STUB
chmod +x "$BIN_DIR/gsd-tools.cjs"
seed_selected "$SKILLS_ROOT"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case8: exit status $STATUS, expected 0"
[ "$(wc -l < "$STUB_LOG")" -eq 5 ] || fail "case8: expected root validation, install, surface, state, and rollback invocations"
grep -q 'capability set failed' "$STDERR_FILE" || fail "case8: missing projection-failure diagnostic"
[ "$(tail -n 1 "$STUB_LOG")" = "capability set beads --disable --runtime codex --scope global --config-dir $CODEX_HOME" ] \
  || fail "case8: half-install was not rolled back with capability set --disable"
grep -q 'capability disabled' "$STDERR_FILE" || fail "case8: rollback not reported"
[ -f "$GSD_HOME/.gsd/capability-auto-install-beads.codex.disabled" ] \
  || fail "case8: hook did not record that it disabled the capability"
[ ! -e "$STATE_FILE" ] || fail "case8: sidecar was created despite surface failure"
[ "$(cat "$LEGACY_STATE_FILE")" = legacy-retry-sentinel ] || fail "case8: failed migration changed legacy retry state"
pass "case8: projection failure warns, retries later, and never records false convergence"
teardown

### Case 8b (R22): the hook re-enables only what it disabled itself ###
setup 0
seed_selected "$SKILLS_ROOT"
printf '\n' >> "$BUNDLE_DIR/capability.json"
sync_installed_fixture
mkdir -p "$GSD_HOME/.gsd"
: > "$GSD_HOME/.gsd/capability-auto-install-beads.codex.disabled"
run_script beads
grep -qx "capability set beads --enable --runtime codex --scope global --config-dir $CODEX_HOME" "$STUB_LOG" \
  || fail "case8b: hook-disabled capability was not re-enabled on the next install"
[ ! -e "$GSD_HOME/.gsd/capability-auto-install-beads.codex.disabled" ] \
  || fail "case8b: re-enable marker survived a converged install"
[ -f "$STATE_FILE" ] || fail "case8b: re-enabled install did not converge"
pass "case8b: a hook rollback is undone by the next converged install"
teardown

### Case 8e (R22): a user's own --disable is never rolled back or re-enabled ###
setup 0
seed_selected "$SKILLS_ROOT"
printf '%s\n' false > "$SCRATCH/enabled"
# A user-disabled capability is unprojected, so verification fails.
rm -rf "$SKILLS_ROOT"/gsd-beads-*
run_script beads
run_script beads
! grep -Eq -- '--(enable|disable)' "$STUB_LOG" || fail "case8e: hook changed a user-disabled capability: $(grep -E -- '--(enable|disable)' "$STUB_LOG")"
[ ! -e "$GSD_HOME/.gsd/capability-auto-install-beads.codex.disabled" ] \
  || fail "case8e: hook recorded a rollback for a user-disabled capability"
grep -q 'disabled by the user' "$STDERR_FILE" || fail "case8e: missing user-disabled note: $(cat "$STDERR_FILE")"
pass "case8e: a user-disabled capability stays disabled with no marker"
teardown

### Case 8c (R22): an installed newer version is never downgraded ###
for _installed_version in 9.9.9 not-a-version; do
  setup 0
  seed_selected "$SKILLS_ROOT"
  "$REAL_PYTHON" -I -c 'import json,sys; p=sys.argv[1]; m=json.load(open(p)); m["version"]=sys.argv[2]; open(p,"w").write(json.dumps(m))' \
    "$INSTALLED_BUNDLE/capability.json" "$_installed_version"
  run_script beads
  [ "$STATUS" -eq 0 ] || fail "case8c: exit status $STATUS, expected 0"
  ! grep -q '^capability install' "$STUB_LOG" || fail "case8c: installed $_installed_version was replaced by an older bundle"
  grep -q 'refusing to replace' "$STDERR_FILE" || fail "case8c: $_installed_version: missing downgrade diagnostic"
  teardown
done
pass "case8c: a newer or unparsable installed version blocks reinstall"

### Case 8d (R22): a held lock is waited for, boundedly ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
: > "$STATE_FILE.lock"
"$REAL_PYTHON" -I -c 'import fcntl,os,sys,time; fd=os.open(sys.argv[1],os.O_RDWR); fcntl.flock(fd,fcntl.LOCK_EX); open(sys.argv[2],"w").close(); time.sleep(1)' \
  "$STATE_FILE.lock" "$SCRATCH/held" &
HOLDER_PID=$!
until [ -e "$SCRATCH/held" ]; do sleep 0.05; done
LOCK_WAIT_SECONDS=10 run_script beads
wait "$HOLDER_PID"
[ -z "$(cat "$STDERR_FILE")" ] || fail "case8d: waiter gave up on a briefly held lock: $(cat "$STDERR_FILE")"
[ -f "$STATE_FILE" ] || fail "case8d: waiter did not complete after the lock was released"
rm -f "$STATE_FILE" "$SCRATCH/held"
"$REAL_PYTHON" -I -c 'import fcntl,os,sys,time; fd=os.open(sys.argv[1],os.O_RDWR); fcntl.flock(fd,fcntl.LOCK_EX); open(sys.argv[2],"w").close(); time.sleep(5)' \
  "$STATE_FILE.lock" "$SCRATCH/held" &
HOLDER_PID=$!
until [ -e "$SCRATCH/held" ]; do sleep 0.05; done
WAIT_START=$SECONDS
LOCK_WAIT_SECONDS=1 run_script beads
WAIT_ELAPSED=$((SECONDS - WAIT_START))
kill "$HOLDER_PID" 2>/dev/null; wait "$HOLDER_PID" 2>/dev/null
grep -q 'projection transaction busy' "$STDERR_FILE" || fail "case8d: bounded wait did not report busy"
[ "$WAIT_ELAPSED" -ge 1 ] && [ "$WAIT_ELAPSED" -le 3 ] || fail "case8d: bounded wait took ${WAIT_ELAPSED}s, expected about 1s"
[ ! -e "$STATE_FILE" ] || fail "case8d: timed-out waiter published"
pass "case8d: a held lock is waited for up to the bound, then reported busy"
teardown

### Case 8i (RS13): equal versions with different content do not flip between runtimes ###
# Both runtimes share one installed bundle. The real CLI overwrites it at an
# equal version, so without a policy every runtime switch reinstalls.
for _claude_cache in older newer; do
  setup 0
  seed_selected "$SKILLS_ROOT"
  seed_selected "$CLAUDE_SKILLS_ROOT"
  export STUB_COPY_INSTALL=1
  CODEX_PLUGIN_DIR="$PLUGIN_DIR"
  CLAUDE_PLUGIN_DIR="$CLAUDE_CONFIG_DIR/plugins/cache/gsd-beads/beads-lifecycle/test"
  make_plugin_root "$CLAUDE_PLUGIN_DIR"
  printf '\nclaude cache content\n' >> "$CLAUDE_PLUGIN_DIR/GSD-CORE-PATCH.md"
  touch -d '2001-01-01' "$CODEX_PLUGIN_DIR/capability.json"
  if [ "$_claude_cache" = older ]; then
    touch -d '2000-01-01' "$CLAUDE_PLUGIN_DIR/capability.json"
  else
    touch -d '2099-01-01' "$CLAUDE_PLUGIN_DIR/capability.json"
  fi
  PLUGIN_DIR="$CODEX_PLUGIN_DIR"
  run_script beads
  [ -f "$STATE_FILE" ] || fail "case8i($_claude_cache): first codex run did not converge: $(cat "$STDERR_FILE")"
  CHANGES=0
  KEEPS=0
  LAST_GENERATION="$(fixture_tree_hash "$INSTALLED_BUNDLE")"
  for _runtime in claude codex claude codex; do
    if [ "$_runtime" = claude ]; then PLUGIN_DIR="$CLAUDE_PLUGIN_DIR"; else PLUGIN_DIR="$CODEX_PLUGIN_DIR"; fi
    run_script beads
    [ "$STATUS" -eq 0 ] || fail "case8i($_claude_cache): $_runtime exit status $STATUS"
    ! grep -v 'keeping the installed' "$STDERR_FILE" | grep -q . \
      || fail "case8i($_claude_cache): $_runtime run failed: $(cat "$STDERR_FILE")"
    KEEPS=$((KEEPS + $(grep -c 'keeping the installed' "$STDERR_FILE")))
    _generation="$(fixture_tree_hash "$INSTALLED_BUNDLE")"
    [ "$_generation" = "$LAST_GENERATION" ] || CHANGES=$((CHANGES + 1))
    LAST_GENERATION="$_generation"
  done
  unset STUB_COPY_INSTALL
  PLUGIN_DIR="$CODEX_PLUGIN_DIR"
  if [ "$_claude_cache" = older ]; then
    [ "$CHANGES" -eq 0 ] && [ "$KEEPS" -eq 1 ] \
      || fail "case8i(older): installed bundle changed $CHANGES times, kept $KEEPS times; expected 0 and 1"
  else
    [ "$CHANGES" -eq 1 ] && [ "$KEEPS" -eq 1 ] \
      || fail "case8i(newer): installed bundle changed $CHANGES times, kept $KEEPS times; expected 1 and 1"
  fi
  teardown
done
pass "case8i: equal versions with different content keep the other runtime's verified install unless this cache is newer"

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
ACTIVE_SYNC="$REPO_ROOT/scripts/sync.py"
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
declared = re.findall(r'^python3 (?:-I )?"\$SYNC_PY" (.+)$', skill_path.read_text(), re.MULTILINE)
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
make_plugin_root "$CUSTOM_PLUGIN"
PLUGIN_DIR="$CUSTOM_PLUGIN"
BUNDLE_DIR="$CUSTOM_PLUGIN"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case11: exit status $STATUS, expected 0"
[ "$(wc -l < "$STUB_LOG")" -eq 0 ] || fail "case11: unknown runtime invoked gsd-tools"
grep -q 'runtime selection failed' "$STDERR_FILE" \
  || fail "case11: missing unknown-runtime diagnostic"
pass "case11: unknown custom root fails closed without guessing a runtime"
teardown

### Case 12: forged locked-child state cannot bypass a live kernel owner ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
: > "$STATE_FILE.lock"
READY_FIFO="$SCRATCH/forged-ready.fifo"
RELEASE_FIFO="$SCRATCH/forged-release.fifo"
mkfifo "$READY_FIFO" "$RELEASE_FIFO"
$REAL_PYTHON - "$STATE_FILE.lock" "$READY_FIFO" "$RELEASE_FIFO" <<'PY' &
import fcntl
import os
import sys

fd = os.open(sys.argv[1], os.O_RDWR)
fcntl.flock(fd, fcntl.LOCK_EX)
with open(sys.argv[2], "w", encoding="utf-8") as stream:
    stream.write("ready\n")
with open(sys.argv[3], "r", encoding="utf-8") as stream:
    stream.readline()
os.close(fd)
PY
LOCK_HOLDER_PID=$!
IFS= read -r READY_SIGNAL < "$READY_FIFO"
[ "$READY_SIGNAL" = ready ] || fail "case12: real lock holder did not reach the rendezvous"
HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" GSD_RUNTIME="" \
  GSD_AUTO_INSTALL_LOCK_FD=9 GSD_AUTO_INSTALL_SKILLS_ROOT="$SKILLS_ROOT" \
  PYTHONDONTWRITEBYTECODE=1 PATH="$TEST_BIN:/usr/bin:/bin" \
  bash "$SCRIPT" beads 9<> "$STATE_FILE.lock" >"$STDOUT_FILE" 2>"$STDERR_FILE"
STATUS=$?
printf '%s\n' release > "$RELEASE_FIFO"
wait "$LOCK_HOLDER_PID"
[ "$STATUS" -eq 0 ] || fail "case12: forged child exit status $STATUS, expected 0"
[ -z "$(cat "$STDOUT_FILE")" ] || fail "case12: forged locked-child state emitted stdout"
[ "$(cat "$STDERR_FILE")" = 'capability-auto-install: projection transaction busy for beads; projection not recorded' ] \
  || fail "case12: forged locked-child state bypassed the live kernel owner"
[ "$(wc -l < "$STUB_LOG")" -eq 0 ] || fail "case12: forged locked-child state reached gsd-tools"
[ ! -e "$STATE_FILE" ] || fail "case12: forged locked-child state published a receipt"
pass "case12: forged locked-child state cannot bypass a live kernel owner"
teardown

### Case 12a: acquisition is one kernel lock confirmed across same-process re-exec ###
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

import sys
_append(f"isolated:{sys.flags.isolated}")
fcntl.flock = _flock
os.set_inheritable = _set_inheritable
os.execvpe = _execvpe
PY
R1_LOCK_SPY_LOG="$SCRATCH/lock-spy.log"
TEST_SPY_SITE="$SPY_DIR"
run_script beads
[ "$STATUS" -eq 0 ] || fail "case12a: exit status $STATUS, expected 0"
[ -f "$STATE_FILE.lock" ] && [ ! -L "$STATE_FILE.lock" ] \
  || fail "case12a: lock path is not a persistent regular file"
[ "$(grep -cx 'flock:6' "$R1_LOCK_SPY_LOG")" -eq 2 ] \
  || fail "case12a: wrapper acquisition and locked-child confirmation were not both nonblocking exclusive flock calls"
[ "$(grep -cx 'inheritable:1' "$R1_LOCK_SPY_LOG")" -eq 1 ] \
  || fail "case12a: acquired descriptor was not made inheritable once"
[ "$(grep -cx 'execvpe:bash' "$R1_LOCK_SPY_LOG")" -eq 1 ] \
  || fail "case12a: acquisition did not re-exec the hook in the same process"
grep -qx 'isolated:1' "$R1_LOCK_SPY_LOG" && ! grep -q '^isolated:0' "$R1_LOCK_SPY_LOG" \
  || fail "case12a: spy did not run under the hook's real -I flag"
pass "case12a: one kernel lock is acquired then confirmed across same-process hook re-exec"
teardown

### Case 12b: uncontended forged descriptor acquires before projection ###
setup 0
seed_selected "$SKILLS_ROOT"
mkdir -p "$(dirname "$STATE_FILE")"
: > "$STATE_FILE.lock"
SPY_DIR="$SCRATCH/forged-lock-spy"
mkdir -p "$SPY_DIR"
cat > "$SPY_DIR/sitecustomize.py" <<'PY'
import fcntl
import os

_log_path = os.environ["R1_LOCK_SPY_LOG"]
_real_flock = fcntl.flock

def _flock(fd, operation):
    with open(_log_path, "a", encoding="utf-8") as stream:
        stream.write(f"flock:{operation}\n")
    return _real_flock(fd, operation)

fcntl.flock = _flock
PY
R1_LOCK_SPY_LOG="$SCRATCH/forged-lock-spy.log"
HOME="$SCRATCH" CODEX_HOME="$CODEX_HOME" CLAUDE_CONFIG_DIR="$CLAUDE_CONFIG_DIR" \
  CLAUDE_PLUGIN_ROOT="$PLUGIN_DIR" GSD_HOME="$GSD_HOME" GSD_RUNTIME="" \
  GSD_AUTO_INSTALL_LOCK_FD=9 GSD_AUTO_INSTALL_SKILLS_ROOT="$SKILLS_ROOT" \
  GSD_TEST_SPY_SITE="$SPY_DIR" R1_LOCK_SPY_LOG="$R1_LOCK_SPY_LOG" PYTHONDONTWRITEBYTECODE=1 \
  PATH="$TEST_BIN:/usr/bin:/bin" bash "$SCRIPT" beads 9<> "$STATE_FILE.lock" \
  >"$STDOUT_FILE" 2>"$STDERR_FILE"
STATUS=$?
[ "$STATUS" -eq 0 ] || fail "case12b: forged child exit status $STATUS, expected 0"
[ "$(grep -cx 'flock:6' "$R1_LOCK_SPY_LOG")" -eq 1 ] \
  || fail "case12b: uncontended forged descriptor did not acquire one nonblocking exclusive flock"
[ -z "$(cat "$STDERR_FILE")" ] || fail "case12b: uncontended forged descriptor emitted stderr"
[ -f "$STATE_FILE" ] || fail "case12b: uncontended forged descriptor did not complete projection"
pass "case12b: uncontended forged descriptor acquires before projection"
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
if [[ "\$*" == 'capability install '*' --scope global' ]]; then
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
# The contender is the same bundle loaded by the other runtime's plugin cache.
CODEX_PLUGIN_DIR="$PLUGIN_DIR"
PLUGIN_DIR="$CLAUDE_CONFIG_DIR/plugins/cache/gsd-beads/beads-lifecycle/test"
make_plugin_root "$PLUGIN_DIR"
run_script beads
PLUGIN_DIR="$CODEX_PLUGIN_DIR"
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
if [[ "\$*" == 'capability install '*' --scope global' ]]; then
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
  TEST_SPY_SITE="$PUBLISH_SPY_DIR"
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
if [ "\$1" = -I ] && [ "\${2:-}" = - ] && [ "\${3:-}" = "$SKILLS_ROOT" ]; then
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
  GSD_TEST_SPY_SITE="$TEST_SPY_SITE" PYTHONDONTWRITEBYTECODE=1 \
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
    "ref: ceed559fd437b037755249e6e36ee36d0d785852",
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
copy_allowlist "$REPO_ROOT" "$GENERATION_B"
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
copy_allowlist "$GENERATION_B" "$REAL_PLUGIN_ROOT" && plant_noise "$REAL_PLUGIN_ROOT"
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
grep -Eq '^capability install /[^ ]+ --scope global$' "$REAL_SPY_LOG" \
  || fail "case24: real hook install argv differed"
! grep -qF "capability install $REAL_PLUGIN_ROOT" "$REAL_SPY_LOG" \
  || fail "case24: real hook installed from the plugin root, not a staged allowlist"
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
    for declaration in re.findall(r'^python3 (?:-I )?"\$SYNC_PY" (.+)$', text, re.MULTILINE):
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
real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT" \
  capability update beads --scope global --yes > "$REAL_ROOT/update.log" 2>&1 \
  || fail "case24: capability update cannot re-fetch the recorded source: $(cat "$REAL_ROOT/update.log")"
# R22 rollback contract on the real CLI: --disable unprojects the selected
# skills and --enable restores them.
real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT" \
  capability set beads --disable --runtime codex --scope global --config-dir "$ACTUAL_CODEX" \
  > "$REAL_ROOT/disable.log" 2>&1 || fail "case24: real rollback disable failed: $(cat "$REAL_ROOT/disable.log")"
[ ! -e "$ACTUAL_SKILLS_ROOT/gsd-beads-sync" ] || fail "case24: real disable left the selected skills projected"
# The hook's rollback reads exactly this shape to tell a user's --disable apart.
REAL_STATE="$(real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT" \
  capability state --runtime codex --config-dir "$ACTUAL_CODEX" --raw 2>/dev/null)"
printf '%s' "$REAL_STATE" | $REAL_PYTHON -I -c 'import json,sys; c=[c for c in json.load(sys.stdin)["capabilities"] if c.get("id")=="beads"]; sys.exit(0 if [x.get("enabled") for x in c]==[False] else 1)' \
  || fail "case24: real capability state does not report beads enabled=false after --disable"
real_cli "$ACTUAL_CODEX" "$ACTUAL_HOME" "$ACTUAL_CLAUDE" "$ACTUAL_PROJECT" \
  capability set beads --enable --runtime codex --scope global --config-dir "$ACTUAL_CODEX" \
  > "$REAL_ROOT/enable.log" 2>&1 || fail "case24: real re-enable failed: $(cat "$REAL_ROOT/enable.log")"
[ -f "$ACTUAL_SKILLS_ROOT/gsd-beads-sync/SKILL.md" ] || fail "case24: real re-enable did not restore the selected skills"

### Case 24b (RS1): real CLI consent: the printed command is the only way in ###
# A declared hook makes gsd-core's evaluateInstallTrust set requiresConsent.
# The user runs the printed command literally, from a plain shell: no
# CLAUDE_PLUGIN_ROOT, no GSD_RUNTIME.
CONSENT_CODEX="$REAL_ROOT/consent/.codex"
CONSENT_HOME="$REAL_ROOT/consent/home"
CONSENT_CLAUDE="$REAL_ROOT/consent/.claude"
CONSENT_PROJECT="$REAL_ROOT/consent/project"
prepare_current_runtime "$CONSENT_CODEX" "$CONSENT_HOME" "$CONSENT_CLAUDE" "$CONSENT_PROJECT"
CONSENT_PLUGIN="$CONSENT_CODEX/plugins/cache/gsd-beads/beads-lifecycle/current"
copy_allowlist "$GENERATION_B" "$CONSENT_PLUGIN" && plant_noise "$CONSENT_PLUGIN"
mkdir -p "$CONSENT_PLUGIN/hooks" && cp -f "$SCRIPT" "$CONSENT_PLUGIN/hooks/capability-auto-install.sh"
$REAL_PYTHON -I -c 'import json,sys; p=sys.argv[1]; m=json.load(open(p)); m["hooks"]=[{"event":"SessionStart","script":"scripts/sync.py"}]; open(p,"w").write(json.dumps(m,indent=2)+"\n")' \
  "$CONSENT_PLUGIN/capability.json"
CONSENT_REAL_TOOLS="$CONSENT_CODEX/gsd-core/bin/gsd-tools-real.cjs"
CONSENT_SPY_LOG="$REAL_ROOT/consent-spy.log"
cp -f "$CONSENT_CODEX/gsd-core/bin/gsd-tools.cjs" "$CONSENT_REAL_TOOLS"
cat > "$CONSENT_CODEX/gsd-core/bin/gsd-tools.cjs" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$CONSENT_SPY_LOG"
exec "$CONSENT_REAL_TOOLS" "\$@"
STUB
chmod +x "$CONSENT_CODEX/gsd-core/bin/gsd-tools.cjs" "$CONSENT_REAL_TOOLS"
CONSENT_SOURCE="$CONSENT_HOME/.gsd/capability-auto-install-beads.source"
CONSENT_LEDGER="$CONSENT_HOME/.gsd/capability-auto-install-beads.projections"
consent_session() {
  : > "$CONSENT_SPY_LOG"
  (
    cd "$CONSENT_PROJECT" || exit 1
    env TMPDIR="$REAL_TMP" HOME="$CONSENT_HOME" GSD_HOME="$CONSENT_HOME" \
      CODEX_HOME="$CONSENT_CODEX" CLAUDE_CONFIG_DIR="$CONSENT_CLAUDE" \
      CLAUDE_PLUGIN_ROOT="$CONSENT_PLUGIN" GSD_RUNTIME=codex \
      bash "$CONSENT_PLUGIN/hooks/capability-auto-install.sh" beads
  ) > "$REAL_HOOK_OUT" 2> "$REAL_HOOK_ERR"
}
consent_by_user() {
  local _command
  _command="$(sed -n 's/^capability-auto-install: beads needs your consent before install; run: //p' "$REAL_HOOK_ERR")"
  [ "$_command" = "bash $CONSENT_PLUGIN/hooks/capability-auto-install.sh --consent beads" ] \
    || fail "case24b: printed command is not the consent mode: $(cat "$REAL_HOOK_ERR")"
  : > "$CONSENT_SPY_LOG"
  (
    cd "$CONSENT_PROJECT" || exit 1
    env -u CLAUDE_PLUGIN_ROOT -u GSD_RUNTIME TMPDIR="$REAL_TMP" HOME="$CONSENT_HOME" \
      GSD_HOME="$CONSENT_HOME" CODEX_HOME="$CONSENT_CODEX" CLAUDE_CONFIG_DIR="$CONSENT_CLAUDE" \
      bash -c "$_command"
  ) > "$REAL_HOOK_OUT" 2> "$REAL_HOOK_ERR"
}
for _round in first-install update; do
  if [ "$_round" = update ]; then
    printf '\nconsent round two\n' >> "$CONSENT_PLUGIN/GSD-CORE-PATCH.md"
  fi
  SOURCE_BEFORE="absent"
  [ ! -e "$CONSENT_SOURCE" ] || SOURCE_BEFORE="$(fixture_tree_hash "$CONSENT_SOURCE")"
  INSTALLED_BEFORE="absent"
  [ ! -e "$CONSENT_HOME/.gsd/capabilities/beads" ] \
    || INSTALLED_BEFORE="$(fixture_tree_hash "$CONSENT_HOME/.gsd/capabilities/beads")"
  consent_session
  [ -z "$(cat "$REAL_HOOK_OUT")" ] || fail "case24b($_round): consent block wrote stdout"
  [ "$(wc -l < "$REAL_HOOK_ERR")" -eq 1 ] || fail "case24b($_round): expected one consent line: $(cat "$REAL_HOOK_ERR")"
  grep -Eq '^capability install /[^ ]+ --scope global$' "$CONSENT_SPY_LOG" \
    || fail "case24b($_round): session did not ask the real CLI without --yes"
  ! grep -q -- '--yes' "$CONSENT_SPY_LOG" || fail "case24b($_round): session passed --yes"
  ! grep -q '^capability set' "$CONSENT_SPY_LOG" || fail "case24b($_round): session reached capability set"
  SOURCE_AFTER="absent"
  [ ! -e "$CONSENT_SOURCE" ] || SOURCE_AFTER="$(fixture_tree_hash "$CONSENT_SOURCE")"
  [ "$SOURCE_AFTER" = "$SOURCE_BEFORE" ] || fail "case24b($_round): stable source changed before consent"
  INSTALLED_AFTER="absent"
  [ ! -e "$CONSENT_HOME/.gsd/capabilities/beads" ] \
    || INSTALLED_AFTER="$(fixture_tree_hash "$CONSENT_HOME/.gsd/capabilities/beads")"
  [ "$INSTALLED_AFTER" = "$INSTALLED_BEFORE" ] || fail "case24b($_round): installed bundle changed before consent"
  consent_by_user
  [ "$(cat "$REAL_HOOK_OUT")" = 'Auto-installed capability: beads (user scope)' ] && [ -z "$(cat "$REAL_HOOK_ERR")" ] \
    || fail "case24b($_round): consent run failed: $(cat "$REAL_HOOK_ERR")"
  [ "$(grep -c -- '--yes' "$CONSENT_SPY_LOG")" -eq 1 ] \
    && grep -qx "capability install $CONSENT_SOURCE/beads --scope global --yes" "$CONSENT_SPY_LOG" \
    || fail "case24b($_round): consent run did not install the stable source with --yes once: $(cat "$CONSENT_SPY_LOG")"
  cmp -s "$CONSENT_PLUGIN/GSD-CORE-PATCH.md" "$CONSENT_HOME/.gsd/capabilities/beads/GSD-CORE-PATCH.md" \
    || fail "case24b($_round): consent run did not install the candidate"
  grep -q '^projection-v2 codex ' "$CONSENT_LEDGER" || fail "case24b($_round): consent run recorded no ledger row"
  consent_session
  [ -z "$(cat "$REAL_HOOK_OUT")" ] && [ -z "$(cat "$REAL_HOOK_ERR")" ] \
    || fail "case24b($_round): the session after consent was not silent: $(cat "$REAL_HOOK_ERR")"
done
pass "case24b: real CLI requires consent, leaves the stable source untouched until the printed --consent command, then converges"

EVIDENCE_ROOT="$ACTUAL_SKILLS_ROOT"
rm -rf "$REAL_ROOT"
[ ! -e "$REAL_ROOT" ] || fail "case24: bounded real scratch was not removed"
SCRATCH=""
pass "case24: floor=$FLOOR_SHA package=$FLOOR_PACKAGE current=$ACTIVE_IDENTITY_KEY public-root=$EVIDENCE_ROOT stale-a=repaired commands=$COMMAND_PREFIXES sibling=preserved oracle=matched no-skip scratch=clean"

echo "ALL PASS"
exit 0
