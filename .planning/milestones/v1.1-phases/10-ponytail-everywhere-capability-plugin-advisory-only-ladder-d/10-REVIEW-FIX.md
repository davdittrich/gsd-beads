---
phase: 10-ponytail-everywhere-capability-plugin-advisory-only-ladder-d
fixed_at: 2026-08-17T00:00:00Z
review_path: .planning/phases/10-ponytail-everywhere-capability-plugin-advisory-only-ladder-d/10-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 10: Code Review Fix Report

**Fixed at:** 2026-08-17T00:00:00Z
**Source review:** .planning/phases/10-ponytail-everywhere-capability-plugin-advisory-only-ladder-d/10-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3 (critical + warning; `fix_scope: critical_warning`)
- Fixed: 3
- Skipped: 0

## Fixed Issues

### CR-01: Unquoted multi-word command variable breaks `gsd_tools()` and silently overrides an explicit `ponytail.enabled: false` whenever the resolved path contains a space

**Files modified:** `ponytail-everywhere/hooks/gsd-tools.sh`, `ponytail-everywhere/tests/test-session-start.sh`
**Commit:** `da2f3c8`
**Applied fix:** Rewrote `gsd_tools()`'s resolver to store the resolved `node <path>`/`gsd-tools` invocation as a bash array (`_GSD_TOOLS_ARGS`) instead of a single joined string, and expand it with `"${_GSD_TOOLS_ARGS[@]}"` at call time — eliminating the IFS word-split that broke whenever the git toplevel or `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` path contained a space. Added a new regression case (case 11) to `tests/test-session-start.sh` that points `CLAUDE_CONFIG_DIR` at a symlinked fixture path containing a literal space and asserts `ponytail.enabled: false` still produces zero stdout bytes and exit 0. Verified the regression test is genuine (not a false-positive pass) by temporarily reverting the source fix and confirming case 11 — and only case 11 — fails; restored the fix and re-ran the full suite (11/11 pass).

### WR-01: `gsd_tools`/`config-get` fail-open masks *any* upstream error, not just a missing key — an unrelated failure silently re-enables the capability

**Files modified:** `ponytail-everywhere/hooks/session-start.sh`
**Commit:** `fc273ff`
**Applied fix:** Split the single `|| echo true` / `|| echo full` fallback into an exit-status check. Exit 127 (the `gsd_tools` binary itself is unavailable, per CR-01's `return 127`) still falls back to the hardcoded defaults (`enabled=true`, `level=full`) — this is the "outside a gsd-core project" case and preserves current graceful behavior there. Any other non-zero exit (corrupt config, `node` crash, permissions error) now logs a one-line diagnostic to stderr and fails closed: `ENABLED=false`, suppressing the banner rather than defaulting it on. `LEVEL` failures other than 127 also log to stderr but keep the `full` default (level only controls verbosity of an already-suppressed-or-shown banner, not the enable/disable toggle, so no fail-closed behavior is needed there). Verified manually with a scratch project containing an unparsable `.planning/config.json`: stdout is empty, exit is 0, stderr carries the diagnostic — confirming the toggle no longer silently overrides an explicit `ponytail.enabled: false` semantics on real errors. Full 11-case test suite still passes.

### WR-02: Unguarded `cd` in test harness risks assertions silently running against the real repo instead of the scratch dir

**Files modified:** `ponytail-everywhere/tests/test-session-start.sh`
**Commit:** `321a5bf`
**Applied fix:** Added `|| { echo "FAIL: ..."; exit 1; }` guards to both unchecked `cd` calls (`mk_scratch`'s `cd "$SCRATCH"` and `run_and_cleanup`'s `cd "$REPO_ROOT"`), applied exactly as the reviewer's suggested diff. Verified `bash -n` syntax check passes and the full test suite still runs and passes (10/10 at the time of this fix, before CR-01's case 11 was added).

## Skipped Issues

None — all in-scope findings were fixed.

---

_Fixed: 2026-08-17T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
