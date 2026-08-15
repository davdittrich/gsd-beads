---
phase: 01-substrate
plan: 03
subsystem: infra
tags: [beads, bd, gsd-capability, python-stdlib, unittest, wave-close, capability-install]

# Dependency graph
requires:
  - "01-01: beads capability skeleton, sync.py create-issues, <beads-id>-first identity resolution, fail-open detection"
  - "01-02: dependency edges, idempotent re-sync, orphan closure, divergence reporting"
provides:
  - "sync.py: close-wave subcommand -- batch-closes every completed task's beads-id across every plan named in one wave dispatch, in a single bd close call"
  - "beads-status SKILL.md -- execute:wave:post entry point, dispatches close-wave over the wave's full plan-id list"
  - "capability.json: second steps[] entry (execute:wave:post -> beads-status), completing both lifecycle hooks declared for Phase 1"
  - "Installed + consented + enabled beads capability -- render-hooks for plan:post and execute:wave:post both confirmed active, fail-open path proven by hand against bd-unreachable PATH"
affects: []

# Actuals (#2632)
actuals:
  tokens: 0
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Completion source of truth is SUMMARY.md existence, not a second in-PLAN.md marker -- close-wave treats 'plan has a SUMMARY.md' as 'all its tasks are done', matching how gsd-core itself marks a plan finished"
    - "Batch close is one bd call, not one call per task -- ids across every plan in the wave are gathered into a single list and closed together, since bd close accepts multiple positional ids and exits 0 for all of them at once"
    - "Idempotent batch close via a pre-filter, not a post-check -- close-wave lists the epic's children with an explicit status filter before closing, so an already-closed wave produces zero close argvs on repeat dispatch"

key-files:
  created:
    - .gsd/capabilities/beads/skills/beads-status/SKILL.md
    - .gsd/capabilities/beads/tests/fixtures/plan-wave-a.md
    - .gsd/capabilities/beads/tests/fixtures/plan-wave-b.md
    - .planning/config.json
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/tests/test_sync.py
    - .gsd/capabilities/beads/capability.json
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "Task 3 (install/consent/confirm) is a checkpoint:human-verify gate, not code -- it exists because 01-RESEARCH.md verified from capability-loader.cts that a project-scoped capability declaring skills[] stays unconsented (every step a silent no-op) until a human installs it and passes the consent disclosure; dropping files on disk is not enough, and the failure mode is silent, so a human had to confirm it once."
  - ".planning/config.json did not exist in this repo before this checkpoint -- generated via config-new-project's standard schema, then beads.enabled:true and workflow.use_worktrees:false both added. The latter was needed because this repo has no git remote yet (worktree base-check degrades to fork-ref-unknown), and the harness's own Agent-dispatch isolation guard could not resolve a project with no config.json at all."
  - "Executor dispatch for this plan's Task 3 closeout could not run in an isolated worktree (WorktreeCreate hook returned no path, twice, in this sandbox) -- closeout was done inline by the orchestrator instead of a third subagent retry, per the two-attempt cap on any single fix."

patterns-established:
  - "close-wave shares the same plan parser, bd helper, and availability guard as create-issues rather than duplicating any of them -- the only new logic is SUMMARY.md-based completion detection and the batch-gather-then-single-close shape"
  - "beads-status SKILL.md reuses the exact four-step scaffold (banner, config gate, single dispatch, one-line report) established by beads-sync in Plan 01 and the mempalace-capture analog identified in 01-PATTERNS.md"

requirements-completed: [B3]

coverage:
  - id: D1
    description: "A wave of two plans with two completed tasks each closes exactly four issues in one bd close dispatch"
    requirement: "B3"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestCloseWave.test_two_plan_wave_closes_four_ids_in_one_argv"
        status: pass
    human_judgment: false
  - id: D2
    description: "An incomplete task's beads-id never appears in any close argv; a task with no beads-id is skipped without error and counted in the report"
    requirement: "B3"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestCloseWave.test_incomplete_task_id_absent_from_close_argv"
        status: pass
    human_judgment: false
  - id: D3
    description: "Re-running close-wave over an already-closed wave issues zero close calls (idempotent batch close via a pre-filter on status)"
    requirement: "B3"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestCloseWave.test_repeat_dispatch_over_closed_wave_issues_zero_close_calls"
        status: pass
    human_judgment: false
  - id: D4
    description: "capability.json declares both lifecycle steps (plan:post -> beads-sync, execute:wave:post -> beads-status), each onError:skip, and the loop's render-hooks for both points names the beads capability once installed and consented"
    requirement: "B3"
    verification:
      - kind: manual
        ref: "node gsd-tools.cjs loop render-hooks plan:post --raw and execute:wave:post --raw, both run post-install: capId 'beads' present in both"
        status: pass
    human_judgment: true
  - id: D5
    description: "With bd made unreachable via PATH, close-wave exits 0, prints one notice, and adds one entry to STATE.md's Blockers/Concerns (B6's fail-open guarantee extended to the wave-close path)"
    requirement: "B3"
    verification:
      - kind: manual
        ref: "sync.py close-wave run with PATH containing only a python3 symlink: exit 0, 'bd unavailable -- sync skipped' printed, one STATE.md Blockers/Concerns line added"
        status: pass
    human_judgment: true

duration: unknown (closeout performed inline by orchestrator after two failed worktree-dispatch attempts; Tasks 1-2 timing not separately tracked here, see their own commits)
completed: 2026-08-15
status: complete
---

# Phase 01 Plan 03: Wave Close Beads Status Install Summary

**`close-wave` batch-closes every completed task's beads issue across a full wave in one `bd close` call, `beads-status` wires it to `execute:wave:post`, and the capability is now installed, consented, enabled, and proven fail-open — Phase 1's substrate (B1-B6) is complete.**

## Performance

- **Tasks:** 3/3 (2 code tasks executed by a prior gsd-executor dispatch, 1 checkpoint task closed out inline after worktree dispatch failed twice)
- **Files created:** 4 (`beads-status/SKILL.md`, `plan-wave-a.md`, `plan-wave-b.md`, `.planning/config.json`)
- **Files modified:** 6 (`sync.py`, `test_sync.py`, `capability.json`, `REQUIREMENTS.md`, `STATE.md`, `ROADMAP.md`)

## Accomplishments

- `close-wave` subcommand in `sync.py`, sharing the plan parser, bd helper, and availability guard with `create-issues`. Completion is read from SUMMARY.md existence per plan (not a second in-PLAN.md marker); ids across every named plan are gathered and closed in one `bd close` call; a status-filtered pre-list makes a repeat dispatch over an already-closed wave a true no-op.
- `beads-status/SKILL.md` — four-step scaffold (banner, `.planning/config.json` gate, single batch dispatch, one-line report), matching `beads-sync`'s established shape.
- `capability.json`'s second `steps[]` entry: `execute:wave:post` -> `beads-status`, `onError: skip`, symmetric with the `plan:post` entry from Plan 01.
- Full suite: 26 tests, all passing (`TestCreateIssues`, `TestIdentityBinding`, `TestFailOpen`, `TestEndToEndTracer`, `TestDependencyMapping`, `TestIdempotency`, `TestLiveDependencies`, `TestCloseWave`).
- **Checkpoint resolved:** capability installed at project scope (`{"status":"installed","id":"beads","version":"0.1.0","scope":"project"}`); `.planning/config.json` created with `beads.enabled: true`; both `render-hooks` calls (`plan:post`, `execute:wave:post`) confirmed a `capId: "beads"` step; fail-open path proven by hand (bd unreachable -> exit 0, one notice, one `STATE.md` Blockers/Concerns line).

## Task Commits

1. **Task 1: close-wave subcommand** - `c62886a` (feat)
2. **Task 2: beads-status skill and execute:wave:post manifest step** - `097bc8f` (feat)
3. **Task 3: Install, consent, and confirm the loop dispatches the beads capability** - checkpoint, resolved by the orchestrator; this closeout commit finalizes REQUIREMENTS.md, STATE.md, ROADMAP.md, and adds `.planning/config.json`

## Files Created/Modified

- `.gsd/capabilities/beads/scripts/sync.py` — `close-wave` subcommand added
- `.gsd/capabilities/beads/tests/test_sync.py` — `TestCloseWave` (26 tests total across the suite)
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md` — new
- `.gsd/capabilities/beads/capability.json` — second `steps[]` entry added
- `.gsd/capabilities/beads/tests/fixtures/plan-wave-a.md`, `plan-wave-b.md` — new
- `.planning/config.json` — new (project's first config.json; `beads.enabled: true`, `workflow.use_worktrees: false`)
- `.planning/REQUIREMENTS.md` — B3 marked complete
- `.planning/STATE.md`, `.planning/ROADMAP.md` — phase 1 (3/3 plans) complete

## Decisions Made

- **`.planning/config.json` gained `workflow.use_worktrees: false`.** This repo has no git remote yet — `worktree base-check` already degrades to sequential execution for that reason (fork-ref-unknown), and once `config.json` existed the harness's own Agent-dispatch isolation guard began resolving a definite `harness-worktree` requirement it couldn't previously assert without a config file. `use_worktrees: false` keeps the run's isolation model consistent with the environment's actual constraint rather than fighting a broken `WorktreeCreate` hook.
- **Task 3's closeout ran inline, not through a third subagent dispatch.** Two `Agent(isolation="worktree")` attempts both failed identically (`WorktreeCreate hook failed: hook succeeded but returned no worktree path`) — a sandbox-level tooling gap, not a transient error. Per the two-attempt cap on any single fix, the orchestrator performed the remaining checkpoint closeout (REQUIREMENTS.md, SUMMARY.md, STATE.md, ROADMAP.md) directly rather than retrying a third time.

## Deviations from Plan

- **Task 3's completion mechanics ran outside the normal executor-agent flow.** The verification steps themselves (install, config, both render-hooks checks, the fail-open hand-test) were performed exactly as `01-03-PLAN.md`'s `<how-to-verify>` specifies, by the user and the orchestrator together. Only the *closeout bookkeeping* (this SUMMARY.md, REQUIREMENTS.md/STATE.md/ROADMAP.md updates) was done inline instead of by a dispatched `gsd-executor`, due to the worktree-creation failure above — no plan content was skipped or altered.

## Issues Encountered

- `WorktreeCreate hook failed: hook succeeded but returned no worktree path` — occurred on both `isolation="worktree"` dispatch attempts for this plan's closeout. Environment-level (this sandbox), not a gsd-core or plan defect. Worth a standing note if later phases need worktree-isolated parallel execution in this environment before a git remote exists.

## User Setup Required

None further — the install/consent/enable steps that Task 3 required as a one-time human action are now complete.

## Next Phase Readiness

- Phase 1 (Substrate) is complete: B1-B6 all closed, 26 tests green, capability installed/consented/enabled, both lifecycle hooks (`plan:post`, `execute:wave:post`) confirmed active in the render-hooks output.
- Phase 2 (Visibility) can build directly on the now-stable `sync.py`/`capability.json` shape.
- Standing note for later phases: this repo has no git remote configured yet, so worktree-isolated parallel execution is unavailable in this environment until one is added (see `gsd-beads-ships-as-github-plugin` memory) — `workflow.use_worktrees: false` should stay set until then.

---
*Phase: 01-substrate*
*Completed: 2026-08-15*
