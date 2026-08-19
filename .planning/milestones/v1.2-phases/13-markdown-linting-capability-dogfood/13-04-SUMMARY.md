---
phase: 13-markdown-linting-capability-dogfood
plan: 04
subsystem: testing
tags: [python, unittest, subprocess, tdd]

requires:
  - phase: 13-markdown-linting-capability-dogfood (plan 02)
    provides: markdown-linting's verify_post() fail-open sentinel design and TestFailOpen suite
  - phase: 13-markdown-linting-capability-dogfood (plan 03)
    provides: capability at zero violations, code review (13-REVIEW.md) diagnosing CR-01/CR-02
provides:
  - "lint.py count subcommand raises RuntimeError (not TypeError) when rumdl/uvx are both absent"
  - "verify_post() fail-open sentinel now fires on any unexpected rumdl exit code, not just tool-absent/timeout/OSError"
  - "two regression tests pinning both fixes against the exact exceptions VERIFICATION.md recorded"
affects: [phase-14, phase-15]

actuals:
  tokens: 1913
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "count_violations() raises subprocess.CalledProcessError for any rumdl returncode outside the completed-run pair (0, 1), routed into verify_post()'s existing except tuple alongside TimeoutExpired/OSError"

key-files:
  created: []
  modified:
    - .gsd/capabilities/markdown-linting/scripts/lint.py
    - .gsd/capabilities/markdown-linting/tests/test_lint.py

key-decisions:
  - "Applied 13-REVIEW.md's CR-01/CR-02 fixes verbatim, no redesign — this is a closure task against already-diagnosed, already-specified defects."

requirements-completed: [MDL-04]

coverage:
  - id: D1
    description: "lint.py count raises a clear RuntimeError (matching fix()'s existing guard) instead of crashing with TypeError when neither rumdl nor uvx is on PATH"
    requirement: MDL-04
    verification:
      - kind: unit
        ref: "test_lint.py#TestToolResolution.test_count_cli_tool_absent_raises_runtime_error"
        status: pass
    human_judgment: false
  - id: D2
    description: "verify_post() overwrites a stale LINT-REPORT.md with the unavailable sentinel on any unexpected rumdl exit code, not just tool-absent/timeout/OSError"
    requirement: MDL-04
    verification:
      - kind: unit
        ref: "test_lint.py#TestFailOpen.test_unexpected_exit_code_fail_open_overwrites_stale_report"
        status: pass
      - kind: unit
        ref: "test_lint.py#TestFailOpen.test_config_error_raises (regression guard: returncode 2 still uncaught)"
        status: pass
    human_judgment: false

duration: ~10min
completed: 2026-08-18
status: complete
---

# Phase 13 Plan 04: Close CR-01/CR-02 lint.py gaps Summary

**Closed both VERIFICATION.md-FAILED defects in `lint.py` — a rumdl crash exit code no longer leaves LINT-REPORT.md stale, and `count` now fails as cleanly as `fix()` when rumdl/uvx are both absent — pinned by two new regression tests, suite green at 12.**

## Performance

- **Duration:** ~10min
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments
- Task 1 (RED): added `test_count_cli_tool_absent_raises_runtime_error` (joins `TestToolResolution`) and `test_unexpected_exit_code_fail_open_overwrites_stale_report` (joins `TestFailOpen`), both written against post-fix behavior and confirmed failing against unmodified `lint.py` with the exact exceptions VERIFICATION.md recorded: `TypeError: unsupported operand type(s) for +: 'NoneType' and 'list'` (CR-01) and `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` (CR-02).
- Task 2 (GREEN): applied 13-REVIEW.md's CR-01 and CR-02 fixes verbatim — a `None`-guard mirroring `fix()`'s in `main()`'s `count` branch, and a `count_violations()` returncode check that raises `subprocess.CalledProcessError` for any exit code outside the completed-run pair (0, 1), caught by `verify_post()`'s widened except tuple. Corrected three stale docstring claims (`count_violations()`, `verify_post()`, `resolve_rumdl_invocation()`) in the same commit.
- Full suite: 10 pre-existing tests green -> 12 green, 0 failures, 0 errors. `test_config_error_raises` (the returncode-2 regression guard) stayed green throughout — the widened except tuple did not swallow the config-error path.

## Task Commits

1. **Task 1: Pin CR-01 and CR-02 with failing regression tests (RED)** - `a8e0847` (test)
2. **Task 2: Apply CR-01 and CR-02 guards to lint.py (GREEN)** - `f69f21b` (feat)

**Plan metadata:** commit pending (this file + STATE.md/ROADMAP.md/REQUIREMENTS.md)

## Files Created/Modified
- `.gsd/capabilities/markdown-linting/tests/test_lint.py` - two new regression test methods, one class docstring extended
- `.gsd/capabilities/markdown-linting/scripts/lint.py` - two guard clauses (CR-01, CR-02), three docstring corrections

## Decisions Made
- Followed the plan's explicit instruction not to redesign, widen scope, or reopen the mechanism choice — applied both review-specified fixes verbatim.
- Did not touch README.md, WR-01 (duplicated argv), or WR-02 (YAML escaping) — all explicitly out of scope for this closure task per the plan's action block.

## Deviations from Plan

### Auto-fixed Issues

None — no bugs, missing functionality, or blockers required a Rule 1-3 fix beyond what the plan itself specified.

### Plan acceptance-criteria discrepancies (not code defects — documented, not silently corrected)

**1. Sentinel-string grep count: plan expected `2`, actual is `3`.**
- **Found during:** Task 1 self-check.
- **Issue:** The plan's acceptance criteria state `grep -c 'rumdl/uvx must not be invoked when absent'` should return `2` after Task 1. The pre-existing (pre-Task-1) file already contained this sentinel string twice — in `test_tool_absent_fail_open` and `test_tool_absent_overwrites_stale_zero_report_sentinel` — so adding a third (reused, not invented) occurrence in the new `count` test makes the true post-Task-1 count `3`. Verified against `git show HEAD~2:...test_lint.py` before editing.
- **Resolution:** No code/test change — the new test correctly reuses the existing sentinel string (the criterion's actual intent, per its own prose: "the new count test reuses the existing never-invoke sentinel string rather than inventing a second one"). The literal number in the acceptance criterion was miscounted by the plan author. Not corrected in the plan file (out of this task's file scope); documented here for the record.

**2. `if rumdl_argv is None` grep count: plan expected `2`, actual is `3`.**
- **Found during:** Task 2 self-check.
- **Issue:** The plan's acceptance criteria state this grep should return `2` after Task 2 ("the guard now exists at both call sites: `fix()` and `main()`'s `count` branch"). `verify_post()` already had its own `if rumdl_argv is None:` check pre-existing (the tool-absent fail-open branch from plan 02), so the true post-Task-2 count is `3`: `verify_post()` (pre-existing) + `fix()` (pre-existing) + the new `count` branch guard.
- **Resolution:** No code change — all three occurrences are legitimate, independently-motivated guards (one fail-open, two raise). Documented for the record; same class of plan-authoring miscount as item 1.

**3. `lint.py count` on the live repo tree prints `3`, not the plan's expected `0`.**
- **Found during:** Task 2 acceptance-criteria verification.
- **Issue:** The plan asserts the live tree is "at zero violations per 13-03." It measured `3` at verification time: `.planning/intel/API-SURFACE.md:67` (MD009, trailing space — one of the pre-existing unrelated dirty files this executor was explicitly told not to touch) and `.planning/phases/13-markdown-linting-capability-dogfood/13-REVIEW.md:82,127` (MD040, code block missing language — an artifact from this phase's own code-review step, authored after 13-03's zero-violation baseline was measured).
- **Resolution:** Confirmed via a standalone probe script that these three violations exist in files this plan's `files_modified` does not include, and that `lint.py`'s guard-clause changes (pure Python control flow, no markdown touched) cannot have caused them. Left unfixed per the plan's explicit scope boundary ("Only auto-fix issues DIRECTLY caused by the current task's changes") and per this closure task's own instruction not to widen scope. Running `verify-post` against the live phase dir to check this criterion regenerated `13-LINT-REPORT.md` with `violation_count: 3`; that side-effect write was reverted with `git checkout -- <file>` before committing, since the file is not in this plan's `files_modified` and the plan's own metadata commit list does not name it.

---

**Total deviations:** 0 auto-fixed; 3 documented acceptance-criteria discrepancies (all pre-existing plan-authoring miscounts or live-tree drift, not caused by this plan's changes).
**Impact on plan:** None on the delivered fix — both VERIFICATION.md truths (#6, #7) are now satisfied and machine-asserted exactly as specified. The discrepancies are in the plan's own predicted grep counts / live-tree baseline, not in the code.

## Issues Encountered

None beyond the acceptance-criteria discrepancies documented above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

MDL-04's "never a stale count presented as current" guarantee now holds for every reproduced rumdl failure mode (tool-absent, timeout, OS error, unexpected exit code), not just the three plan 02 originally enumerated. VERIFICATION.md Truths #6 and #7 are both now satisfiable and machine-asserted. No blockers for Phase 14/15.

Note for a future session: the live tree currently carries 3 MD009/MD040 violations in `.planning/intel/API-SURFACE.md` and `13-REVIEW.md` (see Deviation 3 above) — out of scope here, but will need a `lint.py fix` pass before any future zero-violation baseline check.

## Self-Check: PASSED

- FOUND: `.gsd/capabilities/markdown-linting/scripts/lint.py`
- FOUND: `.gsd/capabilities/markdown-linting/tests/test_lint.py`
- FOUND commit `a8e0847` (test(13-04): pin CR-01/CR-02 with failing regression tests)
- FOUND commit `f69f21b` (feat(13-04): apply CR-01/CR-02 guards to lint.py)
- Full suite `python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -v` reports `Ran 12 tests ... OK`.

---
*Phase: 13-markdown-linting-capability-dogfood*
*Completed: 2026-08-18*
