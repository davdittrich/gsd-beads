---
phase: 04-adoption
plan: 01
subsystem: beads-migrate-todos
tags: [beads, migration, cli, tdd]
status: complete
dependency-graph:
  requires: []
  provides: [migrate_todos, gsd-migrate-todos-skill]
  affects: [.gsd/capabilities/beads/scripts/sync.py, .gsd/capabilities/beads/capability.json]
tech-stack:
  added: []
  patterns:
    - "FRONTMATTER_RE + per-key single-line regex (TITLE_RE/AREA_RE/SEVERITY_RE), block-list
       regex cloned from DEPENDS_ON_BLOCK_RE (FILES_BLOCK_RE) -- no new YAML dependency"
    - "parse-then-create ordering: a per-file ValueError from parse_todo() never reaches bd
       create; a todo file is unlink()'d only after bd create's return code is confirmed 0"
key-files:
  created:
    - .gsd/capabilities/beads/skills/beads-migrate-todos/SKILL.md
    - .gsd/capabilities/beads/tests/fixtures/todo-wellformed.md
    - .gsd/capabilities/beads/tests/fixtures/todo-malformed.md
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/capability.json
    - .gsd/capabilities/beads/tests/test_sync.py
decisions:
  - "Task 1 and Task 2 landed in the same RED/GREEN commit pair: migrate_todos' three-way
     parse-error/bd-create-failure/moved report separation (Task 2's actual subject) had to
     exist from Task 1's first working version for the tracer's own behavior spec to hold, so
     Task 2's TestMigrateTodosReport tests were written alongside Task 1's TestMigrateTodos
     tests and both went green together -- no gap was found, no additional fix commit was
     needed (see Deviations)."
metrics:
  duration: ~20min
  completed: 2026-08-16
actuals:
  tokens: 5320
  tasks: 2
  commits: 2
---

# Phase 4 Plan 01: Todo Migration (B12) Summary

One-shot `sync.py migrate-todos` subcommand plus a `gsd-migrate-todos` skill: a parseable
`.planning/todos/pending/*.md` todo becomes a bd issue (severity mapped to priority, area mapped
to an `area-<area>` label, problem/solution/files folded into the description) and its file is
deleted only after `bd create` confirms success; an unparseable todo (missing/invalid `severity`,
missing frontmatter) is left untouched and reported under a distinct "could not be interpreted"
count from a "bd create failed" count.

## What Was Built

- `sync.py`: `TITLE_RE`, `AREA_RE`, `SEVERITY_RE`, `FILES_BLOCK_RE`, `PROBLEM_RE`, `SOLUTION_RE`,
  `SEVERITY_TO_PRIORITY` (`blocker`->0, `major`->1, `minor`->2, `cosmetic`->3, per bd's verified
  priority scale)
- `sync.py`: `parse_todo_files_block()` (clones `DEPENDS_ON_BLOCK_RE`'s block-list extraction,
  scoped to `files:`), `parse_todo()` (raises `ValueError` naming the reason on any structural
  gap -- never returns a partially-populated dict), `_todo_description()` (folds
  problem/solution/files into one `-d` prose string, `## Files` section only when non-empty),
  `migrate_todos()` (whole-run `bd_available()` fail-open gate before any per-file loop; per-file
  parse-then-create ordering; three-list report: moved / could not be interpreted / bd create
  failed)
- `sync.py`: new `migrate-todos` argparse subcommand, no positional args -- resolves
  `project_root`/`pending_dir` from `Path.cwd()` itself
- `.gsd/capabilities/beads/skills/beads-migrate-todos/SKILL.md` (new skill, `name:
  gsd-migrate-todos`, `argument-hint: ""`), cloned from `beads-sync/SKILL.md`'s Step
  0-4 structure
- `capability.json`: `"beads-migrate-todos"` added to `skills[]`
- `test_sync.py`: `TestMigrateTodos` (8 fixtures/behavior tests), `TestMigrateTodosReport` (3
  regression tests for the D-04/Pitfall-2 three-way separation)
- New fixtures `todo-wellformed.md`/`todo-malformed.md` matching `add-todo.md`'s exact schema

## Verification

```
python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q
# 74 passed in 3.24s (full suite, including this plan's 8 new tests)
```

Manually inspected a mocked `bd create` argv (`test_wellformed_migrates_and_deletes_file`): a
well-formed todo (`severity: major`, `area: sync`) produces
`["bd", "create", "Fix flaky retry loop in sync", "-d", "## Problem\n...", "-t", "task", "-p",
"1", "-l", "area-sync", "--silent"]` -- a Python list passed to `subprocess.run`, never a joined
shell string (N4/T-04-01).

## Deviations from Plan

### Auto-fixed Issues

None - both tasks' behaviors were implemented and pass; no bug found.

### Structural note (not a Rule 1-4 deviation)

Task 1 (tracer) and Task 2 (report-separation hardening) share one function, `migrate_todos()`.
Building Task 1's tracer to satisfy its own `<behavior>` spec (a well-formed todo migrates; a
malformed todo is left in place) required the parse-error/bd-create-failure split from the start
-- there is no intermediate "Task 1 without Task 2's separation" version that still meets Task
1's own acceptance criteria. Both tasks' tests (`TestMigrateTodos`, `TestMigrateTodosReport`) were
therefore written in the RED commit together, and both went green in the GREEN commit together.
Task 2's action explicitly anticipates this outcome ("If any of these three cases surfaces a real
gap ... fix it directly ... do not work around a real defect with a weaker test") -- running
`TestMigrateTodosReport` found no gap, so no separate fix commit was needed. Both tasks' full
acceptance criteria are independently verified green (see `<verify>` commands above and per-task
acceptance criteria below).

## Task Verification Against Acceptance Criteria

**Task 1:**
- `TestMigrateTodos` passes (5 tests) - confirmed
- A well-formed fixture produces one `bd create` argv with mapped priority/label/folded
  description - confirmed (`-p 1`, `-l area-sync`, `-d` starts with `## Problem`)
- The well-formed fixture's file no longer exists on disk after `migrate_todos` returns -
  confirmed
- The malformed fixture is neither deleted nor sent to `bd create` - confirmed
- `beads-migrate-todos/SKILL.md` exists - confirmed
- `capability.json`'s `skills[]` contains `"beads-migrate-todos"` - confirmed

**Task 2:**
- `TestMigrateTodosReport` passes (3 tests) - confirmed
- bd-create-failure report text and parse-error report text use distinct labels ("bd create
  failed" vs "could not be interpreted") - confirmed
- A bd-create-failure leaves the todo file on disk - confirmed
- A bd-unavailable run issues zero `subprocess.run` calls (via an `AssertionError`-raising side
  effect) - confirmed
- A missing pending directory returns 0, not an exception - confirmed

## Known Stubs

None.

## Threat Flags

None - `T-04-01` (typed argv, no shell string) and `T-04-02`/`T-04-03` (accepted, low severity)
from the plan's own threat register are the only new surface this plan introduces, and both are
implemented/dispositioned exactly as the plan's threat model specifies.

## Self-Check: PASSED

All 6 created/modified files confirmed present on disk; both commit hashes (`fb5ef97`, `aee2bba`)
confirmed in `git log`.
