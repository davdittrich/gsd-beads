---
phase: 16-beads-issue-content-parity
plan: 02
subsystem: infra
tags: [beads, bd, sync.py, gsd-core-capability, python-stdlib, D-08]

# Dependency graph
requires:
  - phase: 16-beads-issue-content-parity
    provides: "plan 16-01's parse_plan()/find_completed_task_ids() task-content parity — this plan reuses _resolve_completed_task_ids and filter_open_ids unchanged"
provides:
  - "reconcile_stale_closed(phase_dir_arg) — a phase-wide, idempotent close backstop composing _resolve_completed_task_ids + filter_open_ids"
  - "`reconcile-stale-closed` sync.py subcommand, registered in main()"
  - "beads-status SKILL.md Step 2b dispatches reconcile-stale-closed before regenerate-beads-md at every verify:post"
  - "gsd-beads-bu0.3/.4/.5/.6 closed in the live bd database, proving the backstop on real data"
affects: [16-03, 16-04, beads-status, beads-sync, beads-recall skills, future phases relying on bd close accuracy]

# Actuals (#2632)
actuals:
  tokens: 4163
  tasks: 3
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Backstop-composes-existing-primitives: reconcile_stale_closed adds zero new completion-detection logic, only a new call site over _resolve_completed_task_ids (already tested, phase-wide) + filter_open_ids (already tested, idempotent)"
    - "Distinct close_reason strings per closing mechanism ('phase-wide reconciliation: <phase>' vs close_wave's 'wave complete: <plan ids>') so bd show --json's audit trail always shows which mechanism closed an issue"

key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md

key-decisions:
  - "Edited the git-tracked plugin source (plugins/beads-lifecycle/.gsd/capabilities/beads/) instead of the plan-specified .gsd/capabilities/beads/ path — same gitignored runtime-install mirror issue documented in 16-01-SUMMARY.md (commit 4d83504). Confirmed via git ls-files before editing this time, so no edits were lost to the mirror re-sync."
  - "reconcile_stale_closed's summary line recomputes skipped_total via a second discover_plan_files + find_completed_task_ids pass (same pair close_wave uses), because _resolve_completed_task_ids discards per-plan skip counts by design — this duplicates only a count, not the completion/closing decision itself, so there is still exactly one source of truth for 'is this task done'"
  - "Sorted completed_ids before calling filter_open_ids so the bd close argv is deterministic across runs (plan's explicit requirement, for flake-free test assertions)"

patterns-established:
  - "Pattern: a lifecycle-point backstop is added by composing existing tested primitives at a new call site, never by writing a second completion-detection mechanism that could diverge from the first"

requirements-completed: [D-08]

coverage:
  - id: D1
    description: "reconcile_stale_closed closes only completed-plan task ids across a whole phase in one batched bd close call; an incomplete plan's ids never appear in the argv"
    requirement: "D-08"
    verification:
      - kind: unit
        ref: "test_sync.py#TestReconcileStaleClosed.test_two_completed_plans_closes_four_ids_in_one_call"
        status: pass
      - kind: unit
        ref: "test_sync.py#TestReconcileStaleClosed.test_incomplete_plan_contributes_nothing_and_never_appears_in_close_argv"
        status: pass
    human_judgment: false
  - id: D2
    description: "A second reconcile-stale-closed run over an already-reconciled phase issues zero bd close calls"
    requirement: "D-08"
    verification:
      - kind: unit
        ref: "test_sync.py#TestReconcileStaleClosed.test_repeat_run_over_already_reconciled_phase_issues_zero_close_calls"
        status: pass
      - kind: integration
        ref: "live: second `sync.py reconcile-stale-closed .planning/phases/14-pr-workflow-capability-dogfood` run printed 'Closed 0 issue(s)' (see Live Verification below)"
        status: pass
    human_judgment: false
  - id: D3
    description: "verify:post dispatches the phase-wide reconciliation; execute:wave:post keeps dispatching close-wave unchanged"
    requirement: "D-08"
    verification:
      - kind: unit
        ref: "test_sync.py full suite unchanged/green (SKILL.md structural tests unaffected)"
        status: pass
    human_judgment: true
    rationale: "SKILL.md prose correctness (Step 2b ordering, Anti-Pattern 6 wording) is a documentation/orchestration-instruction change with no automated assertion on the prose itself — confirm by reading the rewritten sections."
  - id: D4
    description: "The four Phase 14 stale issues (gsd-beads-bu0.3-.6) are closed in the live bd database via the new backstop, and a live re-run proves idempotency"
    requirement: "D-08"
    verification:
      - kind: integration
        ref: "live bd list/show commands, see Live Verification below"
        status: pass
    human_judgment: false
  - id: D5
    description: "bd unavailable makes reconcile-stale-closed print the standard notice, append a STATE.md blocker, and exit 0"
    requirement: "D-08"
    verification:
      - kind: unit
        ref: "test_sync.py#TestReconcileStaleClosed.test_bd_unavailable_exits_zero_with_one_notice_and_closes_nothing"
        status: pass
    human_judgment: false

duration: ~5min
completed: 2026-08-19
status: complete
---

# Phase 16 Plan 02: D-08 Reconciliation Backstop Summary

**A phase-wide, idempotent `reconcile-stale-closed` backstop, wired into `verify:post`, closed the four Phase 14 issues that `execute:wave:post`'s per-wave dispatch had silently left open — live data, not a fixture.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-08-18T23:44:47Z (immediately after 16-01's plan-metadata commit)
- **Completed:** 2026-08-18T23:49:04Z
- **Tasks:** 3
- **Files modified:** 3 (`sync.py`, `test_sync.py`, `SKILL.md`, all under `plugins/beads-lifecycle/.gsd/capabilities/beads/`)

## Accomplishments

- New `reconcile_stale_closed(phase_dir_arg)` in `sync.py`, placed immediately after `close_wave` —
  composes the already-tested `_resolve_completed_task_ids(phase_dir)` (phase-wide, every plan in
  the dir) with the already-tested `filter_open_ids()` (live-status re-query, the idempotency
  guarantee) and issues one batched `bd close` call. Fail-open guard cloned verbatim from
  `close_wave`. Sorted id list for deterministic argv. Distinct `--reason` string
  (`"phase-wide reconciliation: <phase>"`) so a `bd show --json` audit trail can always tell a
  backstop close from a wave close.
- Registered as `reconcile-stale-closed <phase_dir>` in `main()`'s subparser/dispatch.
- 8 new tests in `TestReconcileStaleClosed`, mirroring `TestCloseWave`'s coverage plus two backstop-
  specific cases (empty phase directory, reason-string content) and a CLI-dispatch smoke test. Full
  suite: 108 tests, 0 failures, 0 errors (100 pre-existing + 8 new).
- `beads-status/SKILL.md` Step 2b now runs `reconcile-stale-closed` **before**
  `regenerate-beads-md` at every `verify:post`, with the ordering rationale stated explicitly
  (reconciling first keeps `blocking_open`/`diverged` fresh for `ship:pre`'s gates). Anti-Pattern 6
  rewritten from an absolute ("never dispatches close-wave") to the precise rule distinguishing the
  two subcommands' scopes; a new Anti-Pattern 6a states neither subcommand replaces the other.
- Live proof: ran the new subcommand against `.planning/phases/14-pr-workflow-capability-dogfood`
  — closed exactly the four expected stale ids in one batch, then a second run closed zero. No
  Phase 14 file was modified.

## Task Commits

Each task was committed atomically:

1. **Task 1: reconcile_stale_closed — a phase-wide, idempotent close backstop** - `e542b82` (feat)
2. **Task 2: Wire the backstop at verify:post and correct Anti-Pattern 6** - `3a5ed80` (docs)
3. **Task 3: Close the four stale Phase 14 issues with the new backstop, as live proof** — no code
   commit (live `bd` state change only; evidence recorded below and in this SUMMARY, which is
   committed as part of the plan-metadata commit)

**Plan metadata:** committed alongside this SUMMARY (see final commit).

## Files Created/Modified

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` — `reconcile_stale_closed()`
  (new function, ~40 lines), `reconcile-stale-closed` subparser + dispatch in `main()`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` — new
  `TestReconcileStaleClosed` (8 tests)
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md` — revised Step 2b
  (reconciliation dispatch + explicit ordering rationale), rewritten Anti-Pattern 6, new
  Anti-Pattern 6a

## Decisions Made

- **Edited the tracked plugin source, not the plan's stated path** — see key-decisions above and
  16-01-SUMMARY.md's fuller root-cause writeup (commit `4d83504`, Phase 15's `.gitignore` scoping).
  Verified via `git ls-files` up front this time; no edits were lost to the mirror.
- **skipped_total recomputed via a second pass** rather than modifying `_resolve_completed_task_ids`
  to also return skip counts — the plan explicitly allowed either choice, and adding a second return
  value to an already-tested, already-used-elsewhere function risked a wider blast radius than a
  local recount for a print-line-only metric.
- **plan_ids count in the summary line is the total discovered plans in the phase** (via
  `discover_plan_files`, not just completed ones) — matches "across how many plans the phase
  contains" from the plan's action text; visible in the live run's `across 3 plan(s)` (all of
  14-01/02/03) even though only 14-02/14-03 contributed closeable ids.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Edited `plugins/beads-lifecycle/.gsd/capabilities/beads/` instead of the plan's `.gsd/capabilities/beads/`**
- **Found during:** Task setup, before any edit (pre-empted via 16-01's documented root cause and
  this plan's own `<path_note>`)
- **Issue:** `.gsd/capabilities/beads/scripts/sync.py` etc. is a gitignored runtime-install mirror
  of the tracked `plugins/beads-lifecycle/.gsd/capabilities/beads/` source; edits at the mirror path
  are invisible to git and get silently reverted on the next capability re-sync.
- **Fix:** All edits made directly against `plugins/beads-lifecycle/.gsd/capabilities/beads/{scripts/sync.py,tests/test_sync.py,skills/beads-status/SKILL.md}`; the runtime mirror was
  best-effort copied to match after each commit for local convenience, but is not itself tracked or
  authoritative.
- **Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`,
  `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`,
  `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md`
- **Verification:** `python3 -m unittest discover -s plugins/beads-lifecycle/.gsd/capabilities/beads/tests -v` — 108 tests, 0 failures, 0 errors, both commits present in `git log`
- **Committed in:** `e542b82` (Task 1), `3a5ed80` (Task 2)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The plan's task content, tests, and behavior are implemented exactly as
specified — only the on-disk location of the edit changed, matching the same footgun 16-01 already
documented and this plan's `<path_note>` anticipated.

## Issues Encountered

None beyond the anticipated path deviation above, which was avoided proactively (confirmed via
`git ls-files` before the first edit) rather than discovered mid-task as in 16-01.

## Live Verification (D-08 proof, Task 3)

**Before-state** — `bd list --id gsd-beads-bu0.3,gsd-beads-bu0.4,gsd-beads-bu0.5,gsd-beads-bu0.6 --json`:

All four ids present, each `"status": "open"`, `updated_at == created_at` (never touched since
creation on 2026-08-18T15:39:2x-34Z):

```
gsd-beads-bu0.6  status=open  title="14-03.2 Task 2: Record that the gate is advisory ..."
gsd-beads-bu0.5  status=open  title="14-03.1 Task 1: Re-consent the bundle, then record ..."
gsd-beads-bu0.4  status=open  title="14-02.2 Task 2: ship:post warn-only notice when no open PR exists (PRW-03)"
gsd-beads-bu0.3  status=open  title="14-02.1 Task 1: Two distinct fail-open notices for gh-absent and gh-unauthenticated (PRW-04)"
```

**Reconciliation command and stdout:**

```
$ python3 plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py reconcile-stale-closed .planning/phases/14-pr-workflow-capability-dogfood
Closed 4 issue(s) across 3 plan(s) in 14-pr-workflow-capability-dogfood; skipped 0 task(s) with no beads-id
```

Exactly 4 closed — the expected count, no discrepancy.

**After-state** — `bd list --id gsd-beads-bu0.3,gsd-beads-bu0.4,gsd-beads-bu0.5,gsd-beads-bu0.6 --json`:

```
[]
```

All four ids are no longer reported by a `--status open,in_progress,blocked,deferred` filter — i.e.
all four are now closed.

`bd show gsd-beads-bu0.3 --json` (excerpt):

```json
{
  "id": "gsd-beads-bu0.3",
  "status": "closed",
  "updated_at": "2026-08-18T23:48:37Z",
  "closed_at": "2026-08-18T23:48:37Z",
  "close_reason": "phase-wide reconciliation: 14-pr-workflow-capability-dogfood"
}
```

`close_reason` is distinguishable from wave 1's own closure style, e.g. `gsd-beads-bu0.2`'s
`"Task 2 committed (0b31063): four-state live gsd_run check predicate smoke test recorded in 14-GATE-SMOKE-TEST.md"`
(a per-task commit-message-style reason from a different, earlier closing path) — confirming the
`--reason` string uniquely names the phase-wide reconciliation mechanism.

**Second run (live idempotency proof):**

```
$ python3 plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py reconcile-stale-closed .planning/phases/14-pr-workflow-capability-dogfood
Closed 0 issue(s) across 3 plan(s) in 14-pr-workflow-capability-dogfood; skipped 0 task(s) with no beads-id
```

Zero issues closed — `filter_open_ids` re-queried bd's live status, found nothing left open among
the phase's completed-task ids, and issued no `bd close` call. Safe to fire on every phase
regardless of prior runs, as designed.

**No Phase 14 file modified:**

```
$ git status --porcelain .planning/phases/14-pr-workflow-capability-dogfood/
?? .planning/phases/14-pr-workflow-capability-dogfood/14-BEADS-RECALL.md
?? .planning/phases/14-pr-workflow-capability-dogfood/14-PATTERNS.md
```

Both untracked entries predate this plan (pre-existing session-start artifacts, already present at
conversation start per `git status` and confirmed unrelated by 16-01-SUMMARY.md's own "Next Phase
Readiness" note) — `git status --porcelain` reports zero **modified** files under Phase 14.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The reconciliation backstop is live and dispatched at `verify:post`; the known residual risk
  (`verify:post`'s own dispatch is itself skippable, same class of gap as `execute:wave:post`) is
  accepted deliberately per 16-RESEARCH.md's Assumption A3 and is not addressed by this plan —
  plan 16-04 Task 3 files the dispatch-reliability finding upstream.
- `close_wave`'s own behavior and tests are completely unchanged — confirmed by the full 108-test
  suite passing with zero modifications to `TestCloseWave`.
- Any future phase whose `execute:wave:post` dispatch is silently skipped now self-heals at the
  next `verify:post`, closing the exact class of gap D-08 found in Phase 14.

---
*Phase: 16-beads-issue-content-parity*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md`
- FOUND: commit `e542b82`
- FOUND: commit `3a5ed80`
</content>
