---
phase: 16-beads-issue-content-parity
fixed_at: 2026-08-19T00:45:00Z
review_path: .planning/phases/16-beads-issue-content-parity/16-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 16: Code Review Fix Report

**Fixed at:** 2026-08-19T00:45:00Z
**Source review:** .planning/phases/16-beads-issue-content-parity/16-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (Critical + Warning; IN-01 excluded per `--fix` default scope)
- Fixed: 4
- Skipped: 0

## Fixed Issues

### CR-01: `resolve_issue` writes an explicitly empty `bd` description for every checkpoint-typed task, silently failing D-06 for a real task type

**Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`, `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
**Commit:** `ade3468`
**Applied fix:** Applied the review's option (a) (a real renderer, not just the empty-guard fallback). Added `<decision>`/`<context>`/`<options>`/`<selection-prompt>`/`<what-built>`/`<how-to-verify>`/`<resume-signal>` regexes and populated them in `parse_plan()`'s task dict. Added `_checkpoint_task_description(task)`, mirroring `_task_description`'s "## section, only when non-empty" shape but reading the checkpoint field set. `resolve_issue` now dispatches to it for any `checkpoint:*`-typed task and, as a second line of defense, only appends `-d` when the rendered description is non-empty (matching `resolve_epic`'s existing discipline). Added `TestCheckpointTaskDescription` (3 unit tests) and a `TestCreateIssues` integration test exercising `resolve_issue`'s create path on a checkpoint task end-to-end, closing the review's noted coverage gap.

### CR-02: `check_execute_plan_patch()`'s new call site in `create_issues` sits outside the function's fail-open guard, risking orphaned bd issues on failure

**Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`, `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
**Commit:** `c4f4c55`
**Applied fix:** Applied the review's stated alternative fix: hardened `check_execute_plan_patch()` itself with a `try/except (OSError, UnicodeDecodeError)` around its `.read_text()` call, degrading to the same "cannot verify" exit code (`1`) the missing-file case already returns, rather than wrapping the `create_issues` call site. This is the root-cause fix — `check_execute_plan_patch()` never raises for these exception classes now, so `plan_path.write_text(...)` (the `<beads-id>` writeback) always runs regardless of the patch file's readability. Added a unit test for the degrade path plus a real (un-mocked) integration test proving `create_issues` still writes the `<beads-id>` back to PLAN.md when `execute-plan.md` contains invalid UTF-8 bytes.

### WR-01: `get_milestone_bullet` uses unanchored substring containment, risking a false match against an unrelated bullet

**Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`, `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
**Commit:** `c91311e`
**Applied fix:** Adapted the review's suggested fix rather than applying it literally — the review's literal `^-\s*\**{milestone}\b` anchor would not match this project's real ROADMAP.md bullet shape (`- ✅ **v1.0 milestone** — ...`, emoji before the bold marker). Replaced the bare `milestone in line` containment with a token-boundary regex (`(?<![\w.]){re.escape(milestone)}(?![\w.])`) that rejects a match immediately followed/preceded by a word character or `.` — so `"v1"` cannot match inside `"v1.0"`/`"v1.1"`/`"v1.2"` — while still matching real bullets regardless of leading emoji/bold decoration. Added a substring-collision regression test and a real-ROADMAP-bullet-shape test.

### WR-02: `check_execute_plan_patch()` has no I/O error handling, breaking the file's otherwise-consistent B6 fail-open discipline

**Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`, `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
**Commit:** `93ba3ce`
**Applied fix:** Applied the same guard to `check_shipmd_patch()` (its pre-existing, previously-unguarded sibling) for consistency with `check_execute_plan_patch()`'s CR-02 fix — both functions now degrade to "cannot verify" on `(OSError, UnicodeDecodeError)` instead of raising, matching every other artifact-adjacent filesystem read in this module (`collect_all_task_files`, `resolve_milestone_epic`, etc.). Added a matching unit test for the degrade path.

## Skipped Issues

None — all 4 in-scope findings were fixed.

## Verification

Full suite run in the isolated worktree (`gsd-reviewfix/16-1765884`, fast-forwarded onto `main`):

```
python3 -m pytest plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py -q
134 passed
```

125 tests in the pre-fix baseline; 9 new tests added across the 4 fixes (3 for CR-01's checkpoint renderer, 1 CR-01 integration test, 2 for WR-01's anchored match, 2 for CR-02's degrade path, 1 for WR-02's degrade path).

**Note:** IN-01 (docstring gap) was intentionally excluded — Info-severity findings are out of scope for this `--fix` run (no `--all` flag).

---

_Fixed: 2026-08-19T00:45:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
