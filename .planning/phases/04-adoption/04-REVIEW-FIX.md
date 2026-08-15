---
phase: 04-adoption
fixed_at: 2026-08-15T22:44:48Z
review_path: .planning/phases/04-adoption/04-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-08-15T22:44:48Z
**Source review:** .planning/phases/04-adoption/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (critical + warning; `fix_scope=critical_warning` excludes IN-01)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: `resolve_milestone_epic` crashes uncaught when `STATE.md` is missing

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`
**Commit:** `b2aea19`
**Applied fix:** Added an existence check on `state_path` in `resolve_milestone_epic` before
calling `milestone_epic_title`; raises `RuntimeError` on a missing `STATE.md` instead of letting
`Path.read_text` raise `FileNotFoundError` uncaught. This routes through `create_issues`'s existing
`except RuntimeError` fail-open catch (B6/D-08), matching the file's established error taxonomy
(the review's "more consistent with the rest of the file's error taxonomy" alternative, rather than
returning an empty-title fallback string).

### CR-02: `read_epic_per` crashes on a malformed (but validly-parsed) `config.json`

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`
**Commit:** `72a0164`
**Applied fix:** Guarded `cfg.get("beads", {})` and the subsequent `.get("epic_per", "phase")`
with `isinstance(..., dict)` checks, so a `config.json` where `beads` is a non-dict (e.g.
`{"beads": true}`) degrades to `"phase"` instead of raising `AttributeError`. Applied exactly as
suggested in REVIEW.md.

### CR-03: `render_status_mapping`'s task-side orphan scan had no `(OSError, UnicodeDecodeError)` guard

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`
**Commit:** `942b22f`
**Applied fix:** Wrapped the `parse_plan(plan_path)` call in the task-side orphan loop with
`try/except (OSError, UnicodeDecodeError): continue`, matching every other
`discover_plan_files(...).values()` iteration site in the file (`collect_all_task_files`,
`resolve_milestone_epic`, `collect_epic_task_ids`, `resolve_phase_epic`,
`_resolve_task_ordinal_map`, `render_wave_status_block`). Applied exactly as suggested in
REVIEW.md.

### WR-01: `resolve_milestone_epic` gave no divergence signal when it created a second epic for the same milestone

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`
**Commit:** `c4c017f`
**Applied fix:** Added a `divergence: ... none matched title ... -- creating a new epic` print
before the `bd create` fallback, fired only when `candidate_ids` is non-empty but none matched —
mirroring the existing `stale_epic_id` divergence message style in `create_issues`. Applied exactly
as suggested in REVIEW.md.

### WR-02: `parse_todo`'s `## Problem` section was silently dropped to empty when a todo had no `## Solution` heading

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`
**Commit:** `516581f`
**Applied fix:** Added a module-level `PROBLEM_FALLBACK_RE` (captures everything after
`## Problem` to end-of-body, no lookahead anchor) and changed `problem_m = PROBLEM_RE.search(body)`
to `PROBLEM_RE.search(body) or PROBLEM_FALLBACK_RE.search(body)` — the review's second suggested
option (fallback capture), chosen over the hard `ValueError` alternative to avoid changing
`parse_todo`'s existing raise-only-on-title/severity precondition contract. Verified with a
targeted script (`parse_todo` on a fixture with `## Problem` and no `## Solution` heading now
returns the full problem text instead of `""`) and the existing `TestMigrateTodos`/
`TestMigrateTodosReport` suite (8 tests, all pass unchanged).

**Note on verification depth:** This finding is a data-loss/logic gap, not a syntax issue. Beyond
Tier 1/2, I ran a standalone script exercising `parse_todo` directly (case with no Solution heading,
case with a Solution heading present, and a full round-trip through a temp todo file) plus the
project's own `TestMigrateTodos`/`TestMigrateTodosReport` test classes — all pass. Recommend a human
skim of the diff regardless, per the logic-bug verification guidance.

## Skipped Issues

None — all in-scope findings were fixed.

**Out of scope (not attempted, per `fix_scope=critical_warning`):** IN-01 (`run_bd` calls
throughout the file don't catch `subprocess.TimeoutExpired`) — REVIEW.md itself flags this as
"out of scope for a surgical fix to this phase alone... worth a follow-up ticket," a pre-existing
file-wide pattern rather than a Phase 4 regression.

## Verification Notes

Ran `.gsd/capabilities/beads/tests/test_sync.py` full suite after all 5 fixes: 84 passed, 4 failed.
All 4 failures reproduce identically when run in isolation from `main` at the pre-fix commit
(`TestOnDemandStatus::test_status_command_with_no_argument_resolves_default_phase_dir` passes
standalone; the 3 `TestShipPreGenericDispatch` failures are a `process.cwd()`/tempdir-removal race
in a `gsd-tools.cjs` subprocess call, unrelated to any of the touched functions
`resolve_milestone_epic`/`read_epic_per`/`render_status_mapping`/`parse_todo`). Confirmed
pre-existing test-isolation flakiness, not a regression introduced by these fixes — none of the 5
fixed functions are exercised by the failing tests.

---

_Fixed: 2026-08-15T22:44:48Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
