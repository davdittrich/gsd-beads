---
quick_id: 260823-0dz
plan: 01
subsystem: tooling
tags: [beads, skills, path-resolution, shell, unittest]
beads_id: gsd-beads-elt.4
requires: []
provides:
  - Direct Beads skills resolve project-local, global, then plugin sync.py
  - Exact fence, precedence, argv, and missing-candidate regression coverage
affects: [beads-lifecycle, direct-skills]
actuals:
  tokens: 5350
  tasks: 1
  commits: 1
tech-stack:
  added: []
  patterns: [ordered regular-file capability resolution]
key-files:
  created: [tasks/lessons.md]
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-migrate-todos/SKILL.md
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
key-decisions:
  - Reuse lifecycle dispatch's project-global-plugin precedence without a helper or dependency.
  - Test exact executable Markdown fences and argv rather than a rewritten surrogate.
requirements-completed: []
coverage:
  - id: D1
    description: All four direct Beads skills resolve sync.py across project, global, and plugin installations while preserving argv.
    verification:
      - kind: integration
        ref: tests.test_sync.TestDirectSkillSyncResolver
        status: pass
    human_judgment: false
  - id: D2
    description: Existing lifecycle dispatch behavior remains unchanged.
    verification:
      - kind: integration
        ref: tests.test_sync.TestLifecycleDispatchHook and full 263-test capability suite
        status: pass
    human_judgment: false
duration: 48min
completed: 2026-08-23
status: complete
commit: dbb1ffd
---

# Quick Task 260823-0dz Summary

**Direct Beads skills now use the installed capability from project, global, or plugin roots without changing existing sync.py commands.**

## Accomplishments

- Added ordered regular-file resolution to all ten executable command fences across four direct skills.
- Preserved every existing subcommand and argument sequence; missing candidates fail with one stable diagnostic.
- Added exact raw-fence, precedence, HOME fallback, plugin fallback, path-with-spaces, argv-spy, optional-status-argument, and missing-candidate coverage.

## Task Commit

1. **Task 1: Prove and implement direct-skill parity** — `dbb1ffd`

## Verification Evidence

- RED: the original project-relative fences failed the new canonical-resolver contract.
- Focused resolver tests: 2/2 passed.
- Resolver plus lifecycle-hook tests: 12/12 passed.
- Full capability suite: 263/263 passed.
- `git diff --check`, lesson exact-count checks, and forbidden-component no-diff checks passed.
- Repository-required Agy adversarial review: PASS.

## Issues Encountered

The initial new test harness contained four independent defects: overescaped newline and dollar regexes, placeholder scanning beyond command tails, and a hard-coded call count that ignored multi-command fences. Each was corrected from exact failing evidence; no resolver behavior was changed to satisfy the tests.

## Deviations from Plan

None — implementation scope and selected mechanism remained unchanged.

## Unchanged Components

- `plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `gsd-core/`, manifests, dependencies, auto-install behavior, and public subcommand semantics

## User Setup Required

None.
