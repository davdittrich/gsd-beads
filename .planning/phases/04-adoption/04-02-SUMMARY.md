---
phase: 04-adoption
plan: 02
subsystem: beads-status-ondemand
tags: [beads, status, cli, tdd, read-only]
status: complete
dependency-graph:
  requires: [04-01]
  provides: [render_status_mapping, gsd-beads-status-ondemand-branch]
  affects: [.gsd/capabilities/beads/scripts/sync.py, .gsd/capabilities/beads/skills/beads-status/SKILL.md]
tech-stack:
  added: []
  patterns:
    - "render_status_mapping reuses _beads_md_argv/_render_beads_md_table verbatim (RESEARCH's
       Don't Hand-Roll) -- the only new logic is the two orphan-list computations appended after
       the table"
    - "bd-side orphan computed against collect_epic_task_ids (read-only), deliberately not
       find_orphans (whose already-closed filtering is tuned for the sync path's auto-close
       decision, not a report)"
    - "_resolve_default_phase_dir mirrors resolve_phase_epic's fail-open-on-any-miss shape (missing
       STATE.md, no frontmatter, no current_phase key, no matching phase dir all return None)"
key-files:
  created: []
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/skills/beads-status/SKILL.md
    - .gsd/capabilities/beads/tests/test_sync.py
decisions:
  - "Task 2's two dedicated tests (test_task_side_orphan, the read-only-guarantee test) were
     written together with Task 1's tracer tests in one RED/GREEN commit pair, since Task 1's own
     <behavior> spec (a task with no <beads-id> must be named under 'Plan tasks with no bd issue')
     already required the task-side-orphan logic Task 2's dedicated test re-asserts -- there is no
     intermediate implementation that satisfies Task 1 without it. Task 2's actual new work (SKILL.md
     wiring) landed in its own separate commit. See Deviations."
metrics:
  duration: ~12min
  completed: 2026-08-16
actuals:
  tokens: 5234
  tasks: 2
  commits: 3
---

# Phase 4 Plan 02: On-Demand Beads Status (B13) Summary

`sync.py status [phase directory]` and a fifth `beads-status/SKILL.md` Step 1.5 branch expose the
plan-task <-> bd issue mapping on demand: the same 6-column table `regenerate_beads_md` already
builds, followed by two always-present orphan sections -- a bd issue under the epic matching no
current plan task, and a plan task carrying no `<beads-id>` at all -- with a test-verified guarantee
that this read path never calls `bd close`/`update`/`comment`.

## What Was Built

- `sync.py`: `CURRENT_PHASE_RE` (single-token style matching `BEADS_EPIC_RE`)
- `sync.py`: `_resolve_default_phase_dir(project_root)` -- reads `STATE.md`'s frontmatter via
  `FRONTMATTER_RE`, extracts `current_phase`, zero-pads it, and matches it against the leading
  token of each `.planning/phases/` directory name; returns `None` on any miss (fail-open, same
  posture as every other resolution path in this script)
- `sync.py`: `render_status_mapping(phase_dir_arg)` -- follows `regenerate_beads_md`'s fail-open
  opener shape (NOTICE + STATE.md blocker + return 0 when `bd` is unavailable; "no epic yet --
  nothing to show" + return 0 when the phase has never synced); when an epic exists, queries via
  `_beads_md_argv(epic_id)`, builds the table via `_resolve_task_ordinal_map` /
  `_resolve_completed_task_ids` / `_compute_diverged` / `_render_beads_md_table` (all reused
  verbatim), then appends the two orphan sections. bd-side orphans:
  `[r for r in rows if r.get("id") not in collect_epic_task_ids(phase_dir, epic_id)]`. Task-side
  orphans: every task across `discover_plan_files(phase_dir)` whose `task["beads_id"]` is falsy,
  named by `(plan filename, task name)`. Never calls `run_bd` with `close`/`update`/`comment`.
- `sync.py`: new `status` argparse subcommand, optional `phase_dir` positional
  (`nargs="?", default=None`); `main()` calls `_resolve_default_phase_dir` only when no argument
  was given, printing an explanatory line and returning 1 when no default resolves
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md`: Step 1.5's fifth branch ("Bare invocation
  (no lifecycle-point marker)") routes a direct `/gsd-beads-status [phase]` call to new Step 2e,
  then stops before Step 2's close-wave dispatch; Step 2e runs `sync.py status [phase directory]`
  and prints its stdout verbatim; frontmatter `description:`/`argument-hint:` extended to name both
  invocation shapes; Anti-Pattern #10 added (never call `bd close`/`update`/`comment` from the
  on-demand branch)
- `test_sync.py`: `TestOnDemandStatus` (5 tests) plus fixtures
  `_status_mixed_task_plan_text()` (one synced task, one never-synced task) and
  `_write_status_workspace()` (phase workspace with an optional `current_phase`-bearing `STATE.md`)

## Verification

```
python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q
# 79 passed in 3.30s (full suite, including this plan's 5 new tests)
```

`grep -n "Step 2e" .gsd/capabilities/beads/skills/beads-status/SKILL.md` confirms the new branch/
section exists (lines 71 and 137).

Manually confirmed via the read-only-guarantee test (`test_read_only_guarantee_no_bd_close_update_comment_calls`)
that inspects every `subprocess.run` argv across a full `render_status_mapping` run (with both a
matched issue and a bd-side orphan present) and asserts none has `close`, `update`, or `comment` as
its second argv element.

## Deviations from Plan

### Auto-fixed Issues

None - both tasks' behaviors were implemented and pass; no bug found.

### Structural note (not a Rule 1-4 deviation)

Task 1 (tracer, tdd) required, to satisfy its own `<behavior>` spec ("a plan task whose second task
carries no `<beads-id>` prints that task's name under 'Plan tasks with no bd issue'"), the exact
task-side-orphan logic Task 2's dedicated `test_task_side_orphan` and read-only-guarantee tests were
written to re-assert. There is no intermediate "Task 1 without Task 2's dedicated tests" version
that still meets Task 1's own acceptance criteria without that logic existing. Both tests therefore
landed in Task 1's RED (`fa13fa0`) and GREEN (`a8fc09a`) commit pair; running them found no gap in
the already-implemented logic, so no separate fix commit was needed -- matching the identical
pattern noted in 04-01's Summary for the same reason (a task's own `<behavior>` spec requiring logic
a later task's test was written to confirm). Task 2's genuinely new work -- wiring
`beads-status/SKILL.md`'s bare-invocation branch, Step 2e, and Anti-Pattern #10 -- landed in its own
separate commit (`76106df`), as planned.

## Task Verification Against Acceptance Criteria

**Task 1:**
- `TestOnDemandStatus` passes (5 tests, all written for this task's behavior spec plus Task 2's two
  dedicated tests per the structural note above) - confirmed
- The printed output contains both orphan section headings on every run (structurally unconditional
  in `render_status_mapping` -- both headings are appended regardless of orphan-list emptiness) -
  confirmed by every `TestOnDemandStatus` test's assertions against the captured stdout
- A task with no `<beads-id>` appears under "Plan tasks with no bd issue" naming its plan filename
  and task name - confirmed (`test_task_with_no_beads_id_listed_under_plan_tasks_with_no_bd_issue`)
- The default-phase-dir path (no explicit argument) resolves the same phase directory an explicit
  argument would - confirmed (`test_status_command_with_no_argument_resolves_default_phase_dir`
  drives `sync.main(["status"])` with `cwd` inside the workspace, no argument, and asserts the same
  issue data appears as the explicit-argument tests print)

**Task 2:**
- `beads-status/SKILL.md` documents a fifth Step 1.5 branch and a Step 2e section - confirmed (grep
  above)
- `beads-status/SKILL.md` lists an Anti-Pattern entry about never calling bd close/update/comment
  from the on-demand branch - confirmed (Anti-Pattern #10)
- `TestOnDemandStatus`'s read-only-guarantee test passes - confirmed
  (`test_read_only_guarantee_no_bd_close_update_comment_calls`)
- `TestOnDemandStatus::test_task_side_orphan` passes - confirmed

## Known Stubs

None.

## Threat Flags

None - `T-04-04` (typed argv via reused `_beads_md_argv`), `T-04-05` (read-only guarantee, test-
verified), and `T-04-06` (`_escape_table_cell` reused verbatim via `_render_beads_md_table`) from
the plan's own threat register are the only new surface this plan introduces, and all three are
implemented/dispositioned exactly as the plan's threat model specifies -- zero new subprocess call
sites, zero new table-escaping logic.

## Self-Check: PASSED

All 3 modified files confirmed present on disk with the expected changes; all 3 commit hashes
(`fa13fa0`, `a8fc09a`, `76106df`) confirmed in `git log`.
