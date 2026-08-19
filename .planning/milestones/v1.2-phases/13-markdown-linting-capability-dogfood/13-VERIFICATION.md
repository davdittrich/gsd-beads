---
phase: 13-markdown-linting-capability-dogfood
verified: 2026-08-18T14:35:00Z
status: passed
score: 7/7 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 6/7
  gaps_closed:
    - "Truth #1 (MDL-01) — 'reports 0 violations against .planning/+README.md+CLAUDE.md' regression. Fixed by commit 3eb0154 (blank line inserted below the '## Issues Encountered' heading in 13-04-SUMMARY.md; API-SURFACE.md's stray trailing space was independently reverted and is now byte-identical to its last committed state at 866d071). Live re-run of `lint.py count` this session returns 0, confirmed twice (direct CLI invocation and a live `verify-post` run, reverted afterward)."
  gaps_remaining: []
  regressions: []
---

# Phase 13: markdown-linting capability (dogfood) Verification Report

**Phase Goal:** This repo's own lifecycle measures and reports `.planning/` markdown quality, and
the first live proof exists that a generic `ship:pre` gate fires for a capId other than `security`
/ `broken-windows`.
**Verified:** 2026-08-18T14:35:00Z
**Status:** passed
**Re-verification:** Yes — final pass, after commit `3eb0154` closed the last remaining gap
(Truth #1 / MDL-01 regression) found in the prior `gaps_found` (6/7) pass.

## Goal Achievement

This is the third and final verification pass for Phase 13. The first pass (5/7) found two FAILED
truths (CR-01, CR-02), both closed by plan 13-04. The second pass (6/7) confirmed those two
closures live-reproduced, but found a new regression: Truth #1's "0 violations" claim no longer
held (2 violations, from an out-of-scope trailing-space drift in `API-SURFACE.md` and a
self-inflicted missing-blank-line MD022 violation in 13-04's own SUMMARY.md). Both were fixed
directly in commit `3eb0154` ("fix(13): strip trailing space + missing blank line, restore 0 lint
violations"). This pass independently re-runs every truth from the ground up rather than trusting
that fix.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | MDL-01: curated rumdl config with always-explicit `--config` reports 0 violations against `.planning/`+`README.md`+`CLAUDE.md`; README names all 7 enabled + 3 disabled rules with reasons and a freshly measured, date+sha-stamped markdownlint-cli2 divergence disclosure | ✓ VERIFIED (gap closed, live re-run) | Live `python3 .gsd/capabilities/markdown-linting/scripts/lint.py count` (combined scope, no args = full curated target set) → stdout `0`, exit 0, this session. Independently re-confirmed via a live `verify-post` run against the real phase dir: regenerated `13-LINT-REPORT.md` with `violation_count: 0` (only the `generated_at` timestamp differed from the committed report — reverted with `git checkout --` after the check, working tree left clean). `git diff 866d071 -- .planning/intel/API-SURFACE.md` returns empty (byte-identical, trailing space reverted). Commit `3eb0154` diff shows exactly one line inserted (blank line under the `## Issues Encountered` heading in 13-04-SUMMARY.md, fixing MD022). README documentation half unchanged since 13-03 (commit `599b221`). |
| 2 | MDL-02: after a real `verify:post` run, `LINT-REPORT.md` exists with `violation_count` matching a hand-run `rumdl` count, and carries the "regenerated every step, never hand-edited" banner | ✓ VERIFIED (regression check) | Live `verify-post` run this session regenerated the report with `violation_count: 0`, matching the hand-run `lint.py count` result (`0`) exactly. Banner (`> Regenerated every step. Do not hand-edit.`) and frontmatter shape unchanged. Report reverted to its prior committed state (`generated_at` timestamp only) after the check. |
| 3 | MDL-03 (SC3): installed `ship.md` confirmed to contain the generic gate-dispatch marker before trust; live `gsd_run check predicate` smoke test against a synthetic report shows the gate satisfied at `violation_count:0` and unsatisfied at `violation_count:7` | ✓ VERIFIED (regression check) | `grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' ~/.claude/gsd-core/workflows/ship.md` → `2` (re-confirmed live this session). `13-GATE-SMOKE-TEST.md` content re-read this session — predicate JSON, two-case smoke test transcript unchanged since 13-03. |
| 4 | MDL-03 (SC4): the gate is advisory — a phase with a nonzero `LINT-REPORT.md` count still ships, with a visible warning naming the count | ✓ VERIFIED (regression check) | `capability.json`'s `gates[0].blocking` is `false` (re-confirmed via direct read this session: `"blocking": false` at line 62, description at line 32 explicitly states "advises (never blocks -- MDL-05 defers blocking to v2)"). No commit has touched the gate definition since 13-03. |
| 5 | MDL-04 (SC5): with `rumdl` removed from PATH, one visible notice, exit 0, no hang, and no stale `LINT-REPORT.md` presented as current | ✓ VERIFIED (regression check) | `test_tool_absent_fail_open` and `test_tool_absent_overwrites_stale_zero_report_sentinel` both pass in this session's live full-suite run (12/12 green, re-run below). |
| 6 | The capability's own documented no-stale-report guarantee (plan 02 `must_haves.prohibitions`; `TestFailOpen`'s class docstring: "the report is never left stale/untouched") holds for **any** rumdl subprocess failure, not just the tool-absent/timeout/OSError cases the tests cover | ✓ VERIFIED (regression check) | `test_unexpected_exit_code_fail_open_overwrites_stale_report` passes in this session's live 12/12 run — no code in this path has changed since the prior pass's independent live reproduction (mocked `CalledProcessError` overwrote a stale `violation_count: 0` report with `unavailable`). |
| 7 | `lint.py`'s documented `count` CLI subcommand degrades safely (no unhandled exception) when both `rumdl` and `uvx` are absent from PATH, matching the guard its sibling `fix` subcommand already has | ✓ VERIFIED (regression check) | `test_count_cli_tool_absent_raises_runtime_error` passes in this session's live 12/12 run — no code in this path has changed since the prior pass's independent live reproduction. |

**Score:** 7/7 truths verified (6 confirmed by regression check, 1 newly re-closed and independently re-reproduced this session).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gsd/capabilities/markdown-linting/capability.json` | id/config/steps/gates manifest | ✓ VERIFIED | Unchanged since 13-03; re-confirmed `blocking: false` and predicate shape this session. |
| `.gsd/capabilities/markdown-linting/config/.rumdl.toml` | curated 7-rule allowlist, no `disable` key | ✓ VERIFIED | Unchanged since 13-01/13-03. |
| `.gsd/capabilities/markdown-linting/scripts/lint.py` | stdlib-only wrapper: `resolve_rumdl_invocation`, `count_violations`, `verify_post`, `fix`, CLI subcommands | ✓ VERIFIED | Unchanged since the prior pass's confirmed fix (CR-01/CR-02 both fixed, still live-reproduced this session via the full test run). |
| `.gsd/capabilities/markdown-linting/tests/test_lint.py` + fixtures | stdlib unittest suite, MDL-01/02/04 coverage | ✓ VERIFIED | 12 tests, `python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -v` → `Ran 12 tests ... OK`, re-run live this session, all green. |
| `.gsd/capabilities/markdown-linting/README.md` | ruleset, install tiers, artifact-path rationale, dated divergence disclosure | ✓ VERIFIED | Unchanged since 13-03 (commit `599b221`); no drift. |
| `{phase_dir}/13-LINT-REPORT.md` | generated artifact | ✓ VERIFIED | Committed content reads `violation_count: 0`, and this session's live regeneration reproduces the same `0` (only the timestamp differs) — no longer stale relative to the live tree. |
| `13-GATE-SMOKE-TEST.md` | recorded gate-proof transcript (SC3/SC4/SC5) | ✓ VERIFIED | Unchanged since 13-03; content re-confirmed this session. |
| `13-REVIEW.md` (re-review) | CR-01/CR-02 confirmed fixed by independent code review | ✓ VERIFIED | Unchanged since the prior pass; re-review confirms both fixes, documents 3 non-blocking Warnings (WR-01/02/03) in code the gap-closure diff did not touch — none reopen CR-01/CR-02. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `capability.json` `steps[]` `verify:post` | `markdown-linting-report` skill → `lint.py verify-post` → `{phase_dir}/13-LINT-REPORT.md` | Live run this session | ✓ WIRED | Regenerates the report correctly, now honestly reporting `violation_count: 0` against the live (fixed) tree — the recompute-every-run pipeline is not hardcoding a stale number in either direction. |
| `count_violations()` unexpected exit code | `subprocess.CalledProcessError` | `verify_post()`'s widened except tuple | ✓ WIRED | Unchanged since the prior pass; regression-confirmed via `test_unexpected_exit_code_fail_open_overwrites_stale_report` in this session's live run. |
| `resolve_rumdl_invocation() -> None` | `main()`'s `count` branch guard | `RuntimeError`, never `None + list` | ✓ WIRED | Unchanged since the prior pass; regression-confirmed via `test_count_cli_tool_absent_raises_runtime_error` in this session's live run. |
| `$HOME/.claude/gsd-core/workflows/ship.md` step 8 | generic non-security/broken-windows gate dispatch | Direct grep this session | ✓ WIRED | Marker present (2 occurrences), unchanged. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `13-LINT-REPORT.md` | `violation_count` | `len(json.loads(subprocess.run(rumdl ... --output-format json).stdout))` | Yes — live rumdl run over the real tree, confirmed this session to correctly report the current `0`-violation state (post-fix), matching the hand-run `lint.py count` result | ✓ FLOWING |
| ship:pre gate decision | `GATE_RESULT.block` | generic evaluator reading `LINT-REPORT.md` frontmatter | Unchanged since 13-03, not re-tested this session (no code change in this path) | ✓ FLOWING (regression check only) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full lint scope reports 0 violations (gap closure check) | `lint.py count` (combined scope) | `0` | ✓ PASS (regression fixed) |
| `verify-post` independently reproduces the same 0-count | `lint.py verify-post {phase_dir}` | `LINT-REPORT.md regenerated: 0 violation(s)`, diff shows only `generated_at` timestamp change vs committed | ✓ PASS |
| `API-SURFACE.md` restored to last-committed state | `git diff 866d071 -- .planning/intel/API-SURFACE.md` | empty diff | ✓ PASS |
| Regression suite green at 12 | `python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -v` | `Ran 12 tests ... OK` | ✓ PASS |
| ship.md generic dispatch marker present | `grep -c '...v1' ship.md` | `2` | ✓ PASS |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` convention for this phase; `tests/test_lint.py` serves the equivalent role and was run above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| MDL-01 | 13-01, 13-03, (fix: this session's commit `3eb0154`) | Curated MD0XX ruleset, always-explicit `--config`, 0 violations on real tree, README divergence disclosure | ✓ SATISFIED | Truth #1 — live tree now at 0 violations, confirmed twice this session. |
| MDL-02 | 13-01, 13-02 | `verify:post` fragment reports the violation count, `onError: skip` | ✓ SATISFIED | Truth #2; mechanism correctly reports the current (now-zero) count. |
| MDL-03 | 13-01, 13-03 | `ship:pre` gate reads violation count, advisory by default | ✓ SATISFIED | Truths #3, #4; unchanged since 13-03. |
| MDL-04 | 13-02, 13-03, 13-04 | `rumdl` absent degrades to a no-op with one visible notice | ✓ SATISFIED | Truths #5, #6, #7 — including both previously-FAILED closure items from plan 13-04, live-verified again this session. |

No orphaned requirements: REQUIREMENTS.md's Traceability table maps exactly MDL-01..04 to Phase 13,
all four accounted for above. `MDL-05` is explicitly v2/deferred (not in Phase 13's scope).

**Note (non-blocking, informational):** `REQUIREMENTS.md` itself still shows MDL-01/02/03 as
unchecked `[ ]` and "Gaps Found" in its Traceability table (only MDL-04 is `[x]`/"Complete") — this
is stale from the prior `gaps_found` pass (commit `bf8afc1` explicitly reverted a premature
"Complete" mark) and has not been updated to reflect this pass's `passed` result. Updating
REQUIREMENTS.md's checkboxes/traceability table is a `/gsd-ship`-time bookkeeping action, not a
verifier action — flagged here so it is not missed at ship time, not treated as a gap.

### Anti-Patterns Found

None in this session's live re-check. `git diff 866d071 -- .planning/intel/API-SURFACE.md` is
empty (trailing space reverted) and commit `3eb0154`'s single-line diff shows the missing blank
line restored in `13-04-SUMMARY.md`. No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` debt
markers found in `lint.py`/`test_lint.py` (unchanged since the prior pass's grep). The three
pre-existing `WR-01`/`WR-02`/`WR-03` warnings from `13-REVIEW.md`'s re-review remain open as
non-blocking, out-of-scope advisories (untested `fix()` returncode/stderr handling,
`verify_post()`'s except tuple not covering `json.JSONDecodeError`, `fix()` zero test coverage) —
none reopen CR-01/CR-02 and none touch MDL-01..04's must-haves.

### Human Verification Required

None. All findings are machine-reproduced, not judgment calls.

### Gaps Summary

No gaps remain. This pass closes the final outstanding regression from the prior `gaps_found`
(6/7) verification: Truth #1 (MDL-01)'s "0 violations" claim, broken by (a) a stray trailing space
in `.planning/intel/API-SURFACE.md` from an unrelated `intel api-surface` run, and (b) a missing
blank line below a heading in `13-04-SUMMARY.md` (MD022), is restored — commit `3eb0154` fixed
both, and this session independently re-measured `0` violations twice (direct `lint.py count` and
a live `verify-post` run), confirmed `API-SURFACE.md` is byte-identical to its last-committed
state, and re-ran the full 12-test suite green. Combined with the previously-confirmed CR-01/CR-02
closures (Truths #6/#7, unchanged and reconfirmed this session) and the unchanged gate-dispatch
proof (Truths #3/#4), all 7 must-have truths now hold. The phase goal — this repo's own lifecycle
measuring and reporting `.planning/` markdown quality, plus the first live proof that a generic
`ship:pre` gate fires for a capId other than `security`/`broken-windows` — is achieved.

---

_Verified: 2026-08-18T14:35:00Z_
_Verifier: Claude (gsd-verifier)_
