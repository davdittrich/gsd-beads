---
phase: 01-substrate
plan: 02
subsystem: infra
tags: [beads, bd, gsd-capability, python-stdlib, unittest, dependency-graph]

# Dependency graph
requires:
  - "01-01: beads capability skeleton, sync.py create-issues, <beads-id>-first identity resolution, fail-open detection"
provides:
  - "sync.py: derive_dependency_edges/apply_dependency_edges -- intra-plan sequential edges plus plan-level depends_on cross-plan edges via bd dep add"
  - "sync.py: resolve_issue divergence detection (D-07) -- a stale <beads-id> is reported on stdout, never recreated, never cleared"
  - "sync.py: epic-child orphan sweep (D-06) -- an unmatched, not-already-closed child closes once with a reason"
  - "TestDependencyMapping, TestIdempotency, TestLiveDependencies plus plan-deps.md/plan-orphan.md fixtures other 01-* plans can reuse"
affects: [01-03-wave-close-beads-status-install]

# Actuals (#2632)
actuals:
  tokens: 7047
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "resolve-before-write extended to edges: dependency edges are derived as a pure function over already-resolved ids, then applied via a separate typed-argv bd call, never interleaved with issue creation"
    - "unresolvable prerequisite (unsynced plan) is a sequencing fact reported on stdout, not an error -- same fail-open posture as B6 applied to the whole script, not just bd-absent"
    - "orphan/divergence detection both read bd state (bd list --all, bd show) before writing, and both degrade to report-only rather than any self-healing write"

key-files:
  created:
    - .gsd/capabilities/beads/tests/fixtures/plan-deps.md
    - .gsd/capabilities/beads/tests/fixtures/plan-orphan.md
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/tests/test_sync.py

key-decisions:
  - "Cross-plan edge resolution matches depends_on entries only against PLAN.md files already discovered by globbing the phase directory (discover_plan_files), never by joining depends_on text onto a path -- satisfies T-01-04 without a bespoke sanitizer"
  - "resolve_issue now calls bd show for every already-identity-bound task, not just newly-resolved ones -- the only way to detect D-07 stale-identity divergence is to actually ask bd whether the stored id still resolves; this adds one bd call per already-synced task on every run but never a create/update call, so it does not affect B5's create/update-count assertions"
  - "Orphan sweep and dependency-edge application never raise on a failed bd call (unlike epic/task creation, which still raise per Plan 01): a failed bd dep add or bd close is printed and the run continues -- B2/B5/B6's whole-script fail-open posture, not per-issue-creation strictness, governs these newer code paths"
  - "Dependency edges are (re-)derived and (re-)applied on every sync run, including a no-op resync -- bd dep add's own idempotency (verified against a real db) absorbs the repetition, so B5's zero-create/zero-update assertion deliberately does not extend to dep-add argv counts"

patterns-established:
  - "Pure derive_* function (derive_dependency_edges) separated from its apply_* side-effecting counterpart (apply_dependency_edges) -- the derivation is unit-tested with zero bd/subprocess involvement, matching Task 1's own acceptance criterion that it be importable and callable without any bd process running"
  - "find_orphans mirrors the same pure/impure split: a pure filter function over already-fetched JSON rows, called from one bd list --all --json + loop of bd close calls in create_issues"

requirements-completed: [B2, B5]

coverage:
  - id: D1
    description: "Task 3 of a plan shows task 1 as a blocker via bd's transitive blocker-aware ready semantics; bd ready excludes task 3 until task 1 closes, proven against a real bd database (B2)"
    requirement: "B2"
    verification:
      - kind: e2e
        ref: "tests/test_sync.py#TestLiveDependencies.test_ready_excludes_blocked_tasks_until_blockers_close"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestDependencyMapping.test_three_task_plan_yields_two_intra_plan_edges"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestDependencyMapping.test_depends_on_prereq_adds_first_task_blocked_by_prereq_last_task"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestDependencyMapping.test_create_issues_wires_cross_plan_edge_from_depends_on"
        status: pass
    human_judgment: false
  - id: D2
    description: "wave number alone creates no dependency edge -- a wave-2 plan with an empty depends_on yields zero cross-plan edges (D-04)"
    requirement: "B2"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestDependencyMapping.test_empty_depends_on_yields_zero_cross_plan_edges_at_wave_two"
        status: pass
    human_judgment: false
  - id: D3
    description: "Two syncs over an unchanged plan create zero issues and modify zero issues; the plan file's bytes are identical after the second sync (B5)"
    requirement: "B5"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestIdempotency.test_second_sync_over_unchanged_plan_issues_no_create_or_update_calls"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestIdempotency.test_second_sync_over_unchanged_plan_leaves_plan_bytes_identical"
        status: pass
      - kind: manual
        ref: "plan <verification> block, run against a real bd db: md5sum identical across two real create-issues runs on plan-single.md"
        status: pass
    human_judgment: false
  - id: D4
    description: "A previously-synced issue with no matching current task closes once with an explanatory note, never deleted, never left dangling; a repeat sweep never re-closes an already-closed orphan (D-06)"
    requirement: "B5"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestIdempotency.test_orphaned_epic_child_closes_once_with_reason"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestIdempotency.test_orphan_sweep_skips_already_closed_children_on_repeat_run"
        status: pass
    human_judgment: false
  - id: D5
    description: "A <beads-id> pointing at an issue bd cannot find is reported as divergence on stdout, never silently recreated (D-07)"
    requirement: "B5"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestIdempotency.test_stale_beads_id_reports_divergence_without_recreating"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-08-15
status: complete
---

# Phase 01 Plan 02: Dependency Idempotency Orphans Summary

**`sync.py` derives `bd dep add` edges from intra-plan order and plan-level `depends_on`, resolves before writing so a repeat sync is a true no-op, closes orphaned epic children once with a reason, and reports (never heals) a stale `<beads-id>`.**

## Performance

- **Duration:** ~12 min (implementation only; excludes context-gathering reads)
- **Started:** 2026-08-15T01:56:00Z
- **Completed:** 2026-08-15T02:08:00Z
- **Tasks:** 3/3
- **Files modified:** 4 (2 created fixtures, 2 modified: `sync.py`, `test_sync.py`)

## Accomplishments

- `derive_dependency_edges`/`apply_dependency_edges` (pure derivation, separate side-effecting application) — intra-plan sequential edges (task *k* blocked by task *k-1*) plus one cross-plan edge per resolved prerequisite plan (`depends_on`), first-blocks-on-last, wired into `create_issues` after task resolution
- `parse_depends_on`/`discover_plan_files`/`resolve_prereq_last_task_id` — resolve `depends_on` entries strictly against PLAN.md files already discovered inside the phase directory (T-01-04), never by concatenating artifact text into a path; an unsynced prerequisite is reported on stdout, not an error
- `resolve_issue` now verifies an existing `<beads-id>` against `bd show`; a not-found id is D-07 stale-identity divergence — reported, never recreated
- `find_orphans` + an epic-child sweep in `create_issues` — `bd list --parent <epic> --all --json` (required so an already-closed orphan is never re-closed) diffed against this run's resolved task ids; each unmatched, still-open child closes once via `bd close --reason ...`
- `TestDependencyMapping` (8 tests), `TestIdempotency` (5 tests), `TestLiveDependencies` (1 real-bd test) — full suite now 21 tests, all passing
- `plan-deps.md` (wave 2, `depends_on`, three pre-assigned beads-ids) and `plan-orphan.md` (two identity-bound tasks, `beads_epic` set) fixtures

## Task Commits

Each task was committed atomically:

1. **Task 1: Derive and apply dependency edges from intra-plan order and plan-level depends_on** - `740682a` (feat)
2. **Task 2: Make re-sync a no-op, close orphans with a note, report divergence without healing it** - `9668446` (feat)
3. **Task 3: Live dependency proof against a real bd database** - `3df3e64` (test)

## Files Created/Modified

- `.gsd/capabilities/beads/scripts/sync.py` — `parse_depends_on`, `discover_plan_files`, `resolve_prereq_last_task_id`, `derive_dependency_edges`, `apply_dependency_edges`, `find_orphans`; `resolve_issue` extended to a 3-tuple with divergence detection; `create_issues` wired to apply edges, print divergences, and sweep orphans
- `.gsd/capabilities/beads/tests/test_sync.py` — `TestDependencyMapping`, `TestIdempotency`, `TestLiveDependencies` added; `_make_bd_side_effect` extended to answer `bd dep add`/`bd close`
- `.gsd/capabilities/beads/tests/fixtures/plan-deps.md` — three tasks, pre-assigned beads-ids, `wave: 2` + `depends_on: ["01-01"]`
- `.gsd/capabilities/beads/tests/fixtures/plan-orphan.md` — two identity-bound tasks under `beads_epic: tracer-f5x`

## Decisions Made

- **T-01-04 satisfied by matching against a discovered-file set, not a sanitizer.** `discover_plan_files` globs the phase directory once for `NN-NN-PLAN.md` files and builds an ordinal-prefix → path map; `depends_on` entries are looked up in that map, never joined onto a path. An entry with no match in the discovered set (typo, wrong phase, malicious text) resolves to `None` and is reported, not opened.
- **`bd show` added to the identity-bound path in `resolve_issue`, changing its return arity to a 3-tuple.** D-07 divergence can only be detected by asking bd whether a stored id still resolves; there was no other point in the existing flow where that question got asked. This adds one bd call per already-synced task on every sync, which is a real cost but not one any acceptance criterion excludes (B5 only forbids create/update calls on an unchanged resync, not show calls).
- **Dependency-edge application and orphan closure are always fail-open, unlike epic/task creation.** Plan 01's `resolve_epic`/`resolve_issue` still raise `RuntimeError` on a failed `bd create` (a genuine blocking failure the operator must see). Task 1's own action text extends B6's fail-open posture to "the whole script" for the newer edge/orphan paths specifically, so a failed `bd dep add` or `bd close` prints and continues rather than aborting the run.
- **Dependency edges are re-derived and re-applied on every run, deliberately not gated behind the same idempotency check as issue creation.** Verified against a real `bd` v1.2.1 database (see Deviations) that re-adding an existing edge exits 0 with no duplicate, so no separate existence probe was implemented — `bd`'s own idempotency is the mechanism, not a mirrored one in `sync.py`.

## Deviations from Plan

None — plan executed exactly as written. All bd CLI shapes assumed by the plan (`bd dep add <id> --depends-on <id>`, `bd list --parent <epic> --all --json` status field, `bd ready --json` id field, `bd show <missing-id>` exit code) were independently verified against the real, locally installed `bd` v1.2.1 binary in a scratch directory before implementation (not merely inferred from `--help` text), matching 01-RESEARCH.md's own verification standard.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. (As in Plan 01: the capability install/consent step is out of this plan's scope, expected in Plan 03.)

## Next Phase Readiness

- Dependency-edge derivation, idempotent re-sync, orphan closure, and divergence reporting are all in place and independently proven — B2 and B5 are both closed for Phase 1.
- Plan 03 (wave-scoped batch close, `beads-status`, install/consent checkpoint — B3) can build directly on `create_issues`'s now-stable resolve-before-write shape without further restructuring.
- No blockers. `bd` v1.2.1 confirmed present and behaving exactly as 01-RESEARCH.md and this plan's own smoke-testing described.

---
*Phase: 01-substrate*
*Completed: 2026-08-15*

## Self-Check: PASSED

All 5 created/modified files confirmed present on disk; all 3 task commit hashes
(`740682a`, `9668446`, `3df3e64`) confirmed present in `git log --oneline --all`.
