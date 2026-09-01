---
phase: 21-installed-cutover-and-patch-2-retirement
plan: 01
subsystem: beads-lifecycle
tags: [beads, native-resolver, installed-cutover, patch-retirement]

requires:
  - phase: 20-additive-identity-migration-and-compatibility
    provides: Canonical tracker identity for native task-content resolution
provides:
  - Installed four-tree native resolver cutover with public fail-closed proof
  - Complete Patch 2 retirement with Patch 1 byte preservation
affects: [task-content-resolver, execute-plan, capability-install]

actuals:
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns: [native-task-resolution, marker-bounded-retirement, exact-byte-rollback]

key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md
    - plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
    - plugins/beads-lifecycle/.agents/skills/beads/PRIME.md
    - README.md
    - CHANGELOG.md

key-decisions:
  - "Retire Patch 2 only after proving tracked, project-active, global-active, and bootstrap trees byte-identical."
  - "Use native task resolution as the authoritative strip/read seam; retain the hook-driven no-strip safety boundary."
  - "Preserve Patch 1 through exact raw-region gates and a separately derived ship workflow hash."

requirements-completed: [CUT-01, CUT-02]

duration: 163 min
completed: 2026-09-01
status: complete
---

# Phase 21 Plan 01: Installed Cutover and Patch 2 Retirement Summary

The installed native resolver is the proved task-content authority across all
four capability trees, and the obsolete execute-plan Patch 2 surface is gone
without changing the independent ship Patch 1 contract.

## Accomplishments

- Proved one natural live Phase 21 tracer through the public resolver, including
  exact five-field output, matching Beads identity, four negative controls, and
  the exact `bd show` argv spy.
- Removed Patch 2 production code, tests, detector, operational documentation,
  and the runtime marker-bounded block across exactly eight tracked files.
- Kept Patch 1's marker, table row, messages, ship workflow, status skill,
  installer, documentation region, and retained raw code regions byte-exact
  except for the four approved wording transformations.

## Task Commits

1. **Task 1: Prove installed native resolver cutover** - `9da2d34` (test)
2. **Task 2: Retire execute-plan Patch 2** - `902488c` (feat)

## Verification

- Public cutover transaction: `PHASE21_CUTOVER_OK`.
- Retirement surface gate: `PHASE21_RETIREMENT_SURFACE_OK`.
- Repeated public matrix: `PHASE21_POST_MATRIX_OK`.
- Full capability suite: 288/288 passed.
- Final source digest: `4829a5a67d872cabe4defd144cdd9414f8cb574ef98de3234b18ffe15913249a`.
- Runtime `ship.md` remained hash-identical; retirement scratch was empty.

## Deviations from Plan

- Verifier-only repairs changed no product mechanism: Task 1 heredoc execution
  now uses Bash, Task 2 reads stripped task content from the live Beads row,
  and atomic runtime replacement uses a same-filesystem target sibling.

## Issues Encountered

- Per-command sandbox `/dev/shm` isolation required one persistent host shell.
- Two exact preservation gates caught a missing README manifest-key token and
  one over-broad Patch 1 comment deletion; both rolled runtime back before retry.

## User Setup Required

None.

## Self-Check: PASSED

- Both task commits exist in order.
- Exactly eight Task 2 files were committed.
- All authored gates passed and removed their bounded evidence.

---

*Phase: 21-installed-cutover-and-patch-2-retirement*
*Completed: 2026-09-01*
