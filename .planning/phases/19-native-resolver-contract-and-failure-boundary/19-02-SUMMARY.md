---
phase: 19
plan: 02
subsystem: beads-lifecycle
tags: [beads, task-content-resolver, fail-closed, unittest]
requires:
  - phase: 19-01
    provides: Native resolver branches and public CLI seam
provides:
  - Public-main fixtures for every remaining RES-03 failure class
affects: [phase-19-verification]
tech-stack:
  added: []
  patterns: [one-factor-public-main-failure-fixtures, stdlib-unittest-mock]
key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
key-decisions:
  - Reuse TestResolveTaskContent through sync.main() and mock run_bd at its typed seam.
actuals:
  tokens: 1014
  tasks: 2
  commits: 2
requirements-completed: [RES-03]
coverage:
  - id: D1
    description: Public resolver rejects timeout and unavailable-bd execution without stdout or fallback task prose.
    requirement: RES-03
    verification:
      - kind: unit
        ref: plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py#TestResolveTaskContent
        status: pass
    human_judgment: false
  - id: D2
    description: Public resolver rejects malformed Read First and unusable descriptions without stdout or fallback task prose.
    requirement: RES-03
    verification:
      - kind: unit
        ref: plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py#TestResolveTaskContent
        status: pass
    human_judgment: false
metrics:
  duration: 4min
  completed: 2026-08-31
status: complete
---

# Phase 19 Plan 02: Resolver Failure Coverage Summary

**Public-main fixtures now prove every remaining Beads resolver failure arm stays fail closed.**

## Completed Tasks

1. Added timeout and unavailable-`bd` fixtures that inject typed exceptions at `run_bd` and assert bounded stderr-only failure.
2. Added malformed Read First, blank description, and extracted-only description fixtures, each through `sync.main()`.

## Validation

- `TMPDIR=/dev/shm python3 -m unittest tests.test_sync.TestResolveTaskContent -v` — 10 passed.
- `TMPDIR=/dev/shm python3 -m unittest discover -s tests -t tests` — 275 passed.
- `python3 -m py_compile tests/test_sync.py` and `git diff --check` passed.

## Task Commits

1. `23b01ed` — `test(19-02): cover resolver exception failures`
2. `2b08d32` — `test(19-02): cover resolver content failures`

## Files Created/Modified

- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` — one-factor public CLI failure fixtures and shared output-boundary assertions.

## Decisions Made

- Reused the existing `_invoke` public-main helper and stdlib `mock` seam; no process, dependency, or production change was needed.

## Deviations from Plan

The requested branches already existed from Plan 19-01, so coverage-closure tests passed immediately rather than producing a meaningful RED state. This is not a production deviation: the commits add only the required public-boundary proof.

## Known Stubs

None.

## Self-Check: PASSED

Both task commits exist, the modified test file exists, and focused plus authoritative suites passed.
