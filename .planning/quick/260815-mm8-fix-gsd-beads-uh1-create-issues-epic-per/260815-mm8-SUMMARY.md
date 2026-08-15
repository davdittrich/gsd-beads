---
phase: quick-260815-mm8
plan: 01
subsystem: gsd-beads/sync
tags: [bugfix, tdd, epic-resolution, orphan-detection]
dependency-graph:
  requires: []
  provides:
    - "resolve_epic(frontmatter, roadmap_path, phase_num, phase_dir) -- phase-scoped via resolve_phase_epic"
    - "collect_epic_task_ids(phase_dir, epic_id) -- epic-scoped current_ids for orphan sweep"
  affects:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/tests/test_sync.py
tech-stack:
  added: []
  patterns:
    - "resolve-by-id before create, applied at the epic level (B4/B5 pattern extended to phase scope)"
key-files:
  created: []
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/tests/test_sync.py
decisions:
  - "resolve_epic's second return value renamed in meaning (not signature) from "created" to "needs frontmatter write" -- the phase-scoped reuse path finds an existing epic without creating one, but still needs rewrite_plan to write it into this plan's own frontmatter"
  - "collect_epic_task_ids does not touch find_orphans's signature or body -- the fix is entirely in what current_ids contains before find_orphans is called, exactly as scoped in the plan"
metrics:
  duration: 25min
  completed: 2026-08-15
status: complete
actuals:
  tokens: 2471
  tasks: 2
  commits: 2
---

# Phase quick-260815-mm8 Plan 01: Fix gsd-beads-uh1 and gsd-beads-bgb Summary

Phase-scoped epic resolution and epic-scoped orphan detection in `sync.py`, closing two pre-existing Phase 1 bugs discovered (but deferred) during `02-02-SUMMARY.md`.

## What Was Built

**Task 1 (gsd-beads-uh1):** `resolve_epic` gained a `phase_dir` parameter. When a plan carries no `beads_epic` of its own (or its stored id no longer resolves), it now calls the already-existing `resolve_phase_epic(phase_dir)` helper before falling through to `bd create --type epic`. Two plans in one phase, neither pre-set with `beads_epic`, now sync to exactly one shared epic instead of each creating its own.

**Task 2 (gsd-beads-bgb):** New module-level `collect_epic_task_ids(phase_dir, epic_id)` scans every plan in `phase_dir` sharing `epic_id` and unions their `<beads-id>` values. `create_issues` now unions this into `current_ids` before calling `find_orphans`, so the orphan sweep's "current" set spans every plan sharing the epic, not just the plan being synced. `find_orphans` itself is untouched — the fix is entirely in what `current_ids` contains.

Both new test classes (`TestPhaseScopedEpic`, `TestEpicScopedOrphans`) were confirmed RED against the pre-fix code (stashed sync.py, tests failing: `2 != 1` epic creates, and `shared-epic-01.1` found in the closed set) before being confirmed GREEN against the fix.

## Verification

`cd .gsd/capabilities/beads && python3 -m unittest discover -s tests -v` — 41/41 tests pass (39 pre-existing baseline + 2 new). Zero regressions.

Both bd tickets closed: `bd close gsd-beads-uh1`, `bd close gsd-beads-bgb`.

## Deviations from Plan

None — plan executed exactly as written. Both tasks' RED/GREEN behavior matched the plan's prescribed test and implementation shape; no scope changes, no architectural deviations.

## Commits

- `9f2868b` fix(mm8): phase-scope epic resolution in resolve_epic
- `cb0741e` fix(mm8): epic-scope orphan detection in find_orphans

## TDD Gate Compliance

Both tasks followed RED (test added, confirmed failing against pre-fix code) -> GREEN (implementation added, test passes) within a single commit per task (the plan's `tdd="true"` tasks did not separate test-only and implementation-only commits; each task's single commit bundles a passing test with its implementation, consistent with the plan's per-task commit granularity). Full-suite RED->GREEN confirmed via `git stash` on `sync.py` alone before committing.

## Self-Check

- FOUND: .gsd/capabilities/beads/scripts/sync.py (modified, contains `collect_epic_task_ids` and updated `resolve_epic`)
- FOUND: .gsd/capabilities/beads/tests/test_sync.py (modified, contains `TestPhaseScopedEpic` and `TestEpicScopedOrphans`)
- FOUND: commit 9f2868b
- FOUND: commit cb0741e
- `bd show gsd-beads-uh1` and `bd show gsd-beads-bgb` both report closed

## Self-Check: PASSED
