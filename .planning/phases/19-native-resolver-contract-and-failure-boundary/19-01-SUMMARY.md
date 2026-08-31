---
phase: 19
plan: 01
subsystem: beads-lifecycle
tags: [beads, task-content-resolver, fail-closed]
status: complete
provides:
  - Native Beads task-content resolver source contract
  - Fail-closed sync.py adapter command
affects: [phase-20-identity, phase-21-installed-cutover]
tech-stack:
  added: []
  patterns: [native-gsd-core-resolver, python-stdlib-execv]
key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - CHANGELOG.md
    - README.md
decisions:
  - Preserve source availability separately from installed-runtime cutover evidence.
metrics:
  tasks: 2
  commits: 4
---

# Phase 19 Plan 01: Native Resolver Contract and Failure Boundary Summary

Implemented a fail-closed Beads resolver and source-only native declaration using the existing gsd-core seam.

## Completed Tasks

1. Added `sync.py resolve-task-content <id>` with typed `bd show` argv, an eight-second inner bound, strict envelope and field validation, and JSON-only success output.
2. Declared the single version-0.5.0 native resolver bootstrap and documented its inert-before-Phase-20 boundary.

## Validation

- `TMPDIR=/dev/shm python3 -m unittest tests.test_sync.TestResolveTaskContent tests.test_sync.TestTaskContentResolverManifest -v` — 7 passed.
- `TMPDIR=/dev/shm python3 -m unittest discover -s tests -t tests` — 270 passed.
- Manifest validator returned no errors; tracked `sync.py` remains mode `100644` and non-executable.

## Commits

- `8b5665e` test(19-01): specify native beads content resolution
- `9860f26` feat(19-01): resolve beads task content through sync adapter
- `0e8d2f6` test(19-01): specify beads resolver declaration
- `166d1d6` feat(19-01): declare native beads task resolver

## Deviations from Plan

None - the existing native resolver seam and Python standard library were sufficient; no installed bundle, registry, hook, PATH, dependency, or Phase 20/21 artifact changed.

## Self-Check: PASSED

All declared source files exist, all four task commits exist, and the authoritative capability suite is green.
