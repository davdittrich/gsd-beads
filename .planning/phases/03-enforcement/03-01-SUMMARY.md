---
phase: 03-enforcement
plan: 01
subsystem: infra
tags: [beads, bd, sync.py, markdown-generation, python-stdlib]

# Dependency graph
requires:
  - phase: 02-visibility
    provides: regenerate_beads_md's full-overwrite BEADS.md frontmatter/table pattern (D-05..D-08),
      resolve_phase_epic, collect_epic_task_ids (post gsd-beads-uh1/gsd-beads-bgb fix)
provides:
  - "blocking_open BEADS.md frontmatter field: real live-computed open-issue count under the
    phase's shared epic, no priority/type filter (D-01/D-02)"
  - "diverged BEADS.md frontmatter field: real live-computed count of synced issues whose bd
    status disagrees with linked task completion state, in either direction (D-04)"
  - "BEADS.md's issue table extended to 6 columns with a Task Status (done/incomplete) column
    naming the task-completion side of any diverged row (D-06)"
  - "BEADS.md regeneration wired into verify:post (capability.json steps[] + beads-status
    SKILL.md Step 2b), in addition to the existing execute:wave:pre/execute:wave:post points
    (D-03)"
affects: [03-02, 03-03]

# Actuals (#2632)
actuals:
  tokens: 3933
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "blocking_open is a rename-in-place of the already-computed open_count -- no separate
      filtered variable, per D-01/D-02's no-filtering rule"
    - "divergence is computed once per regenerate_beads_md pass (three call sites) rather than a
      dedicated ship-time check -- reuses the one bd query that pass already makes"

key-files:
  created: []
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/tests/test_sync.py
    - .gsd/capabilities/beads/capability.json
    - .gsd/capabilities/beads/skills/beads-status/SKILL.md

key-decisions:
  - "blocking_open == open_count exactly (D-01/D-02) -- named explicitly with a one-line comment
    in regenerate_beads_md so a future reader doesn't assume a separate filtered count exists"
  - "verify:post's beads-status dispatch never calls close-wave -- Step 2b only regenerates
    BEADS.md, matching the PRD's target manifest shape and the SKILL.md's D-11 lifecycle-branch
    convention"

patterns-established:
  - "A row absent from ordinal_map (no linked task) is skipped entirely from divergence counting
    and task_status_by_id -- never counted, never rendered with an empty Task Status guess"

requirements-completed: [B9, B10]

coverage:
  - id: D1
    description: "blocking_open/diverged BEADS.md frontmatter fields are real computed integers
      (no longer the Phase 2 literal 0 placeholders), and the issue table gains a Task Status
      column naming each row's task-completion side"
    requirement: B9
    verification:
      - kind: unit
        ref: "test_sync.py::TestBeadsMdRegeneration::test_frontmatter_matches_mocked_bd_response_counts"
        status: pass
      - kind: unit
        ref: "test_sync.py::TestBlockingOpen::test_zero_row_epic_yields_blocking_open_zero"
        status: pass
      - kind: unit
        ref: "test_sync.py::TestBlockingOpen::test_two_open_one_closed_yields_blocking_open_two"
        status: pass
      - kind: unit
        ref: "test_sync.py::TestDivergence::test_closed_issue_with_incomplete_task_diverges"
        status: pass
      - kind: unit
        ref: "test_sync.py::TestDivergence::test_zero_row_epic_yields_diverged_zero"
        status: pass
    human_judgment: false
  - id: D2
    description: "verify:post fires the beads-status skill's regenerate-beads-md-only branch so
      BEADS.md is fresh going into ship, without dispatching close-wave"
    requirement: B10
    verification:
      - kind: unit
        ref: "gsd/capabilities/beads/capability.json steps[] verify:post entry shape check
          (python3 check_capability.py, run against this plan's -k 'BlockingOpen or Divergence'
          verify command)"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-08-15
status: complete
---

# Phase 3 Plan 01: Enforcement -- BEADS.md Live Divergence/Blocking Computation Summary

**`blocking_open`/`diverged` BEADS.md frontmatter fields are now real live-`bd`-computed values
(no longer Phase 2's `0` placeholders), the issue table gained a `Task Status` column, and
regeneration now also fires at `verify:post`.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-08-15T16:37:00Z
- **Completed:** 2026-08-15T16:45:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- `regenerate_beads_md` now writes real `blocking_open` (== `open_count`, D-01/D-02: every open
  issue under the epic counts, no priority/type filter) and `diverged` (D-04: per-issue `bd`
  status vs. task-completion disagreement) values instead of literal `0` placeholders.
- `_render_beads_md_table` extended from 5 to 6 columns: a `Task Status` column (`done`/
  `incomplete`) inserted between `Status` and `Plan Task`, so a diverged row is readable without
  cross-referencing `PLAN.md`/`SUMMARY.md` (D-06).
- `verify:post` now dispatches the `beads-status` skill's new `Step 2b` branch, which regenerates
  `BEADS.md` (no wave-status-block, no plan-id list, never calls `close-wave`) so the projection
  Plan 02's `ship:pre` gates will read is fresh (D-03).
- `blocking_open`/`diverged` now have dedicated test coverage (`TestBlockingOpen`,
  `TestDivergence`, 4 new tests) beyond the single existing regression fixture.

## Task Commits

Each task was committed atomically:

1. **Task 1: Tracer -- compute blocking_open + diverged end-to-end through regenerate_beads_md**
   - `2e31c6c` (test) RED: updated `test_frontmatter_matches_mocked_bd_response_counts` to expect
     real values (`blocking_open: 1`, `diverged: 1`), dropped the placeholder assertion
   - `2ac1a83` (feat) GREEN: `_resolve_completed_task_ids`, `_compute_diverged`,
     `_render_beads_md_table` 6-column extension, real frontmatter values, placeholder body line
     removed
2. **Task 2: Wire BEADS.md regeneration into verify:post (D-03); dedicated test coverage**
   - `9ac1d2a` (feat) `capability.json` `verify:post` steps[] entry, `SKILL.md` Step 2b +
     Anti-Patterns entry, `TestBlockingOpen`/`TestDivergence` classes

**Plan metadata:** (this commit)

_Note: Task 1 is `tdd="true"` -- RED/GREEN split across two commits per protocol; Task 2 is
`type="auto"` with test coverage folded into its single commit._

## Files Created/Modified

- `.gsd/capabilities/beads/scripts/sync.py` - `_resolve_completed_task_ids`, `_compute_diverged`,
  6-column `_render_beads_md_table`, real `blocking_open`/`diverged` frontmatter values
- `.gsd/capabilities/beads/tests/test_sync.py` - updated regression fixture assertions;
  `TestBlockingOpen`, `TestDivergence` classes
- `.gsd/capabilities/beads/capability.json` - new `verify:post` `steps[]` entry
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md` - Step 1.5 three-way lifecycle branch,
  new Step 2b, new Anti-Patterns entry, `onError: skip` count corrected from "both" to "all three"

## Decisions Made

- `blocking_open = open_count` named explicitly with a one-line D-01/D-02 comment rather than
  left as an unexplained direct assignment, since the plan's `<action>` specifically called out
  that a future reader must not assume a separate filtered variable exists.
- No deviations required a new architectural decision beyond what D-01..D-06 (03-CONTEXT.md)
  already fixed.

## Deviations from Plan

None - plan executed exactly as written. One incidental correction folded into Task 2's commit:
`SKILL.md`'s pre-existing "This step is `onError: skip` at both `execute:wave:pre` and
`execute:wave:post`" line was now factually wrong (a third `onError: skip` dispatch point exists)
-- updated to "all three points" (Rule 1: bug/inaccuracy directly caused by this task's own
change, fixed inline, no separate commit).

## Issues Encountered

None. The tracer feedback gate (task type="tracer") was satisfied by the full
`test_sync.py` suite re-run after Task 1's commit (41/41 passing, matching the prior quick-task
baseline) before proceeding to Task 2's expansion work -- consistent with how this repo's prior
tracer tasks (01-01 Task 1, 02-01 Task 1) were executed in one continuous pass per their own
SUMMARYs, rather than pausing for a separate interactive checkpoint.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `BEADS.md`'s `blocking_open`/`diverged` fields are real and regenerated at all three lifecycle
  points (`execute:wave:pre`, `execute:wave:post`, `verify:post`) -- Plan 02 (wave 2) can now
  declare its `ship:pre` `artifact-frontmatter-equals` gates against these fields with confidence
  they're live, not placeholders.
- No blockers for Plan 02 or Plan 03.

---
*Phase: 03-enforcement*
*Completed: 2026-08-15*
