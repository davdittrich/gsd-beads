---
phase: 04-adoption
plan: 03
subsystem: beads-milestone-epic
tags: [beads, config, epic-resolution, cli, tdd]
status: complete
dependency-graph:
  requires: [04-01, 04-02]
  provides: [resolve_milestone_epic, beads-epic-per-config-key]
  affects: [.gsd/capabilities/beads/scripts/sync.py, .gsd/capabilities/beads/capability.json]
tech-stack:
  added: []
  patterns:
    - "sync.py's first-ever direct .planning/config.json read (read_epic_per), confined via the
       existing confined()/find_project_root() helpers -- no new dependency, D-11's read-fresh
       requirement satisfied without a new SKILL.md-level CLI flag"
    - "D-10 forward-only guard implemented as a live bd show --json title-match check, not a
       stored-flag/migration-marker mechanism -- a per-phase epic's title is always a verbatim
       ROADMAP phase header, structurally distinct from the computed milestone title, so it can
       never be mistaken for the milestone epic even though its id is discoverable by the same
       cross-phase scan collect_all_task_files already uses"
key-files:
  created: []
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/capability.json
    - .gsd/capabilities/beads/tests/test_sync.py
decisions:
  - "Task 2's two regression tests (test_default_unchanged,
     test_existing_phase_epic_not_reused_as_milestone_epic) were written together with Task 1's
     tracer tests in one RED/GREEN commit pair, matching the identical pattern already noted in
     04-01's and 04-02's Summaries: Task 1's own resolve_epic edit and its D-10 forward-only guard
     had to exist and be correct from the first working version for the tracer's own acceptance
     criteria to hold, so there is no intermediate implementation the dedicated regression tests
     could exercise separately. Running them found no gap, so no separate fix commit was needed
     -- see Deviations."
metrics:
  duration: ~15min
  completed: 2026-08-16
actuals:
  tokens: 4956
  tasks: 2
  commits: 2
---

# Phase 4 Plan 03: Milestone-Scoped Epic Option (B14) Summary

`beads.epic_per=milestone` in `.planning/config.json` makes `resolve_epic()` route to a new
`resolve_milestone_epic()` instead of the existing per-phase path: every phase in the current
milestone shares one epic, titled `"Milestone {milestone}: {milestone_name}"` from STATE.md's
frontmatter, resolved via a live `bd show --json` title match against every `beads_epic` value
found across every plan -- never by re-parenting or otherwise touching an already-created
per-phase epic (D-10 forward-only, test-verified). The default (`epic_per` absent or `"phase"`)
path is unchanged.

## What Was Built

- `sync.py`: `MILESTONE_RE`, `MILESTONE_NAME_RE` (single-token regexes matching `BEADS_EPIC_RE`'s
  style, for STATE.md's `milestone:`/`milestone_name:` frontmatter keys)
- `sync.py`: `read_epic_per(project_root)` -- `sync.py`'s first-ever direct
  `.planning/config.json` read (confined via `confined()`/`find_project_root()`); returns
  `"phase"` when the file is absent or `json.JSONDecodeError`, otherwise
  `cfg.get("beads", {}).get("epic_per", "phase")`
- `sync.py`: `milestone_epic_title(state_path)` -- matches `FRONTMATTER_RE`, extracts
  milestone/milestone_name via the two new regexes, returns
  `f"Milestone {milestone}: {milestone_name}"`
- `sync.py`: `resolve_milestone_epic(project_root)` -- computes the title, scans every phase
  directory under `.planning/phases/` (the same cross-phase technique `collect_all_task_files`
  uses) collecting every distinct `beads_epic` frontmatter value as a candidate; for each
  candidate, `bd show <id> --json` and compares the parsed `"title"` against the computed title,
  reusing the first exact match; creates a fresh epic via `bd create ... --type epic --silent`
  only when no candidate matches
- `sync.py`: `resolve_epic()` gains a `project_root` parameter; after the existing
  stored-`beads_epic` resolution block (unchanged), branches on
  `read_epic_per(project_root) == "milestone"` -- routes to `resolve_milestone_epic` and returns
  directly (skipping the phase-scoped path entirely) when true, otherwise falls through to the
  existing `resolve_phase_epic`/`get_phase_header`/create path completely unchanged.
  `create_issues()`'s one call site passes its already-resolved local `project_root`
- `capability.json`: `"beads.epic_per"` config key (enum, `values: ["phase", "milestone"]`,
  `default: "phase"`), cloned from `beads.sync_mode`'s shape
- `test_sync.py`: `TestMilestoneEpic` (9 tests) plus fixtures `_make_milestone_bd_side_effect()`
  (records `bd create --type epic` ids/titles so a second scan's title-match check sees what an
  earlier call created) and `_write_milestone_workspace()` (STATE.md with
  milestone/milestone_name frontmatter, optional `config.json` `epic_per` override, N empty phase
  directories)

## Verification

```
python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -k TestMilestoneEpic -x
# 9 passed

python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q
# 88 passed in 3.20s (full suite, including this plan's 9 new tests)
```

Manually confirmed via `test_resolve_epic_routes_to_milestone_when_epic_per_milestone` that the
one `bd create --type epic` call issued names the milestone title (`"Milestone v1.0: milestone"`)
verbatim -- not a ROADMAP phase header -- direct proof the phase-scoped
`resolve_phase_epic`/`get_phase_header` fallback path was never reached.

## Deviations from Plan

### Auto-fixed Issues

None - both tasks' behaviors were implemented and pass; no bug found.

### Structural note (not a Rule 1-4 deviation)

Task 1 (tracer, tdd) required its own D-10 forward-only guard (the live `bd show --json`
title-match check inside `resolve_milestone_epic`) to exist and be correct from the first working
version -- Task 1's own `<behavior>` spec ("resolve_milestone_epic creates one epic ... when no
plan anywhere ... carries a beads_epic value whose live bd title matches; a second call ... reuses
that same epic id") already exercises the exact mechanism Task 2's dedicated
`test_existing_phase_epic_not_reused_as_milestone_epic` re-asserts against a seeded, non-matching
candidate. There is no intermediate "Task 1 without Task 2's dedicated regression tests" version
that still meets Task 1's own acceptance criteria without that title-match logic. Both tasks' tests
(`TestMilestoneEpic`'s full 9-test suite) therefore landed in one RED (`1a1f773`) / GREEN
(`2cd12cd`) commit pair; running `test_default_unchanged` and
`test_existing_phase_epic_not_reused_as_milestone_epic` found no gap in the already-implemented
logic, so no separate fix commit was needed -- matching the identical pattern documented in
04-01's and 04-02's Summaries for the same reason.

## Task Verification Against Acceptance Criteria

**Task 1:**
- `TestMilestoneEpic` passes (9 tests, all written for this task's behavior spec plus Task 2's two
  dedicated regression tests per the structural note above) - confirmed
- Two plans synced under two different phase directories with `beads.epic_per: "milestone"`
  resolve to the identical epic id - confirmed
  (`test_two_phases_share_one_milestone_epic_and_second_sync_creates_no_second_epic`)
- A second sync under the same config issues zero additional `bd create --type epic` calls -
  confirmed (same test: exactly 1 epic-create call across both syncs)
- `capability.json`'s `config` object contains a `"beads.epic_per"` enum key with
  `values: ["phase", "milestone"]` and `default: "phase"` - confirmed
  (`test_capability_json_declares_epic_per_enum_key`)

**Task 2:**
- `TestMilestoneEpic::test_default_unchanged` passes - confirmed (byte-for-byte the same outcome
  `TestPhaseScopedEpic::test_second_plan_in_phase_reuses_first_plans_epic_when_neither_preset_one`
  already asserts, exercised through the edited `resolve_epic` signature)
- `TestMilestoneEpic::test_existing_phase_epic_not_reused_as_milestone_epic` passes - confirmed (a
  seeded per-phase epic whose live title is a ROADMAP-style phase header is never adopted; a fresh
  epic is created instead)
- `python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q` remains fully green - confirmed
  (88/88)

## Known Stubs

None.

## Threat Flags

None - `T-04-07` (config.json read confined via `confined()`/`find_project_root()`,
`json.JSONDecodeError` caught, defaults to `"phase"`), `T-04-08` (D-10 forward-only guard,
regression-tested), and `T-04-09` (zero new subprocess call sites -- `resolve_milestone_epic`
reuses `run_bd()`'s typed-argv contract verbatim) from the plan's own threat register are the only
new surface this plan introduces, and all three are implemented/dispositioned exactly as the
plan's threat model specifies.

## Self-Check: PASSED

All 3 modified files confirmed present on disk with the expected changes; both commit hashes
(`1a1f773`, `2cd12cd`) confirmed in `git log`.
