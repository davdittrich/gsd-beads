---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Config/Code Truth
status: roadmap_complete
last_updated: "2026-08-19T21:10:00.000Z"
last_activity: 2026-08-19
progress:
  total_phases: 1
  completed_phases: 0
  total_plans: 2
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-19)

**Core value:** gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero
duplicated task-state bookkeeping survives in `.planning/`.
**Current focus:** Phase 17 (Config/Code Truth) — every declared config value has an observable
effect; the two patch-check clones collapse into one reader.

## Current Position

Phase: 17 — Config/Code Truth (not started)
Plan: — (2 planned: 17-01 → TRUTH-01, 17-02 → TRUTH-02)
Status: Roadmap complete, ready to plan
Last activity: 2026-08-19 — v1.3 roadmap created (Phase 17, TRUTH-01 + TRUTH-02)

Progress: [░░░░░░░░░░] 0% (0/2 plans)

**Gating for this milestone (non-negotiable):** `plan_check` and `verifier` both on; no release
tag until CI is green on the exact commit being tagged. Reason: the gh-2 fix shipped the quick
path on 2026-08-19 as v1.3.0 and a post-release review found a data-loss bug in the fix itself
(hook matcher fired on any command merely mentioning its trigger string, reaching
`strip_task_bodies` and deleting `PLAN.md` task prose). v1.3.0 withdrawn, v1.3.1 tagged.

**Phase 17 pre-change baseline (recorded 2026-08-19, before any edit):** `python3 -m unittest
discover -s tests -t tests` from `plugins/beads-lifecycle/.gsd/capabilities/beads/` reports
`Ran 164 tests ... OK`. Success Criterion 5 is checked against this number.

## Performance Metrics

**Velocity:**

- Total plans completed (v1.2): 7
- Average duration: ~17min (Phase 13 P01-P04 + Phase 14 P01-P03)
- Total execution time: -

**Recent Trend:**

- Last 5 plans: -
- Trend: -

**Per-Plan Metrics (v1.0/v1.1, retained for velocity baseline):**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 09 P01 | 25min | 2 tasks | 4 files |
| Phase 09 P02 | 30min | 3 tasks | 7 files |
| Phase 09 P03 | 34min | 3 tasks | 9 files |
| Phase 09 P04 | 42min | 3 tasks | 1 files |
| Phase 10 P01 | 35min | 2 tasks | 6 files |
| Phase 10 P02 | ~20min | 3 tasks | 6 files |
| Phase 10.1 P01 | 15min | 2 tasks | 3 files |
| Phase 10.1 P02 | 12min | 3 tasks | 9 files |
| Phase 11 P01 | 35min | 3 tasks | 20 files |
| Phase 11 P02 | 30min | 2 tasks | 8 files |
| Phase 11 P03 | 20min | 3 tasks | 2 files |
| Phase 11.1 P01 | 12min | 2 tasks | 5 files |
| Phase 11.1 P02 | 8min | 3 tasks | 5 files |
| Phase 12 P01 | 18min | 4 tasks | 6 files |
| Phase 12 P02 | ~15min | 4 tasks | 7 files |
| Phase 12 P03 | ~20min | 2 tasks | 1 files |
| Phase 12 P04 | 12min | 2 tasks | 36 files |
| Phase 13 P01 | 20min | 3 tasks | 8 files |
| Phase 13 P02 | 15min | 2 tasks | 4 files |
| Phase 13 P03 | ~12min | 3 tasks | 118 files |
| Phase 13 P04 | 10min | 2 tasks | 2 files |
| Phase 14 P01 | ~25min | 2 tasks | 12 files |
| Phase 14 P02 | ~20min | 2 tasks | 4 files |
| Phase 14 P03 | ~25min | 2 tasks | 3 files |
| Phase 16 P01 | 14min | 2 tasks | 2 files |
| Phase 16 P02 | 5min | 3 tasks | 3 files |
| Phase 16 P03 | ~10min | 2 tasks | 2 files |
| Phase 16 P04 | 10 min | 3 tasks | 4 files |

Full v1.0/v1.1 per-plan history: `.planning/STATE-ARCHIVE.md`.

## Accumulated Context

### Decisions

Full decision log lives in PROJECT.md's Key Decisions table. Carried forward into v1.3 because
Phase 17 edits the exact surfaces these rows describe:

- **[v1.3, open]** TRUTH-01's direction is deliberately undecided at roadmap time. The plan must
  produce an Alternatives Considered table (narrow declaration+docs / implement `mirror` and `off`
  / drop the key) and must answer what happens to a project that already set
  `"sync_mode": "mirror"` or `"off"`. Precedent for option (b): 0.3.1 already collapsed
  `read_epic_per` + `read_beads_enabled` into one `read_beads_config` reader.
- **[v1.3, grounding]** `.gsd/capabilities/beads/` is a gitignored runtime mirror
  (`.gitignore:41`); the git-tracked source is `plugins/beads-lifecycle/.gsd/capabilities/beads/`
  (17 files). Phase 16 plan 01 edited the wrong one and it was caught in review.

  (upstream open-gsd/gsd-core#3559 filed, merge status unconfirmed). Any new gate must verify the
  patch marker is present and prove itself live via `gsd_run check predicate` before being trusted.

  post-consent edit silently deactivates the capability with no error. Re-consent after every edit.

  re-grants on drift; vendored into each plugin's `session-start.sh`.

  resolves its script path via `git rev-parse --show-toplevel`, not `${CLAUDE_PLUGIN_ROOT}`.

  stage-outside-tree → fix-relocation-paths → `gh repo create` + push → fresh-clone-verify sequence.

  URLs (commit `f706179`) — GitHub shorthand clones over SSH and breaks on SSH-keyless machines.

  `gsd-beads` in the same commit that repaired the orphaned `ci.yml` / `release.yml` references —
  was found false during quick-task 260818-h2h: `git log --follow` showed no deletion commit ever
  existed for `.gsd/capabilities/{ponytail,sota-numerics}`, only their Phase 10/11 authoring
  commits (`932cf34`, `246dfbc`). Whatever Phase 12 removed, it was not these two paths. They were
  actually removed in quick-task 260818-h2h, by `git rm -r`, in the same commit that scoped the
  `beads-lifecycle` plugin source to `plugins/beads-lifecycle/`.

- [Phase 14]: pr_status rollup extends D-01's precedence to gh's actual bucket vocabulary (skipping->passing, cancel->failing alongside fail), flagged per RESEARCH Pitfall 6 rather than silently reinterpreting D-01
- [Phase 14]: un-ignored .gsd/capabilities/pr-workflow/ in .gitignore, same one-line pattern Phase 13 established for markdown-linting
- [Phase 14]: the -t . unittest-discover verify-command defect (dotted-module-name incompatible with the hidden .gsd/ dir) was inherited from Phase 13's plan-doc shape and fixed at the plan-doc level for 14-01/14-02/14-03-PLAN.md (commit f31e6f4), mirroring Phase 13's own fix -- no code change, verification behavior unaffected
- [Phase 14]: verify_post's live gh calls wrapped in a single try/except catching only TimeoutExpired/OSError/JSONDecodeError, leaving check_buckets' RuntimeError (unrelated gh pr checks stderr) uncaught on purpose
- [Phase 14]: ship_post_notice() never reads PR.md -- PRW-03's no-open-PR answer is always a live gh pr list re-probe, never a possibly-stale generated artifact
- [Phase 14]: re-consented pr-workflow capability (capability install --scope project --yes) before trusting any live dispatch this session -- 14-01/14-02 both edited files inside the bundle after the original consent, silently deactivating it until re-installed
- [Phase 14]: Phase 14 complete -- all four requirements (PRW-01..04) and all five ROADMAP Success Criteria closed with live-cycle evidence in 14-GATE-SMOKE-TEST.md, not unit assertions alone
- [Phase ?]: [Phase 16, plan 01]: Edited plugins/beads-lifecycle/.gsd/capabilities/beads/ (the git-tracked plugin source) instead of the plan-specified .gsd/capabilities/beads/, which is a gitignored runtime-install mirror silently re-synced from the tracked source
- [Phase ?]: [Phase 16, plan 01]: get_milestone_bullet fails open (returns empty string on a miss) unlike its get_phase_header model, since resolve_milestone_epic must stay fail-open per B6/D-08
- [Phase ?]: [Phase 16, plan 02]: reconcile_stale_closed composes existing _resolve_completed_task_ids + filter_open_ids as a phase-wide idempotent close backstop for D-08, dispatched at verify:post before regenerate-beads-md
- [Phase ?]: [Phase 16, plan 02]: closed the four stale Phase 14 issues (gsd-beads-bu0.3-.6) live via the new reconcile-stale-closed subcommand, proving the backstop on real data
- [Phase ?]: [Phase 16, plan 03]: check_execute_plan_patch clones check_shipmd_patch's exact detector shape for the machine-local execute-plan.md bd-task-read patch (D-05) — **this clone is exactly what TRUTH-02 collapses in Phase 17**
- [Phase ?]: [Phase 16, plan 03]: strip_task_bodies turns a newly-created auto/tracer task block into name+beads-id+files+pointer, gated on check_execute_plan_patch()==0 and scoped to task_updates (this run's created ids only) -- checkpoint:* blocks and pre-existing tasks stay byte-identical (D-01/D-03/D-07)
- [Phase ?]: Second machine-local gsd-core patch (execute-plan.md bd task-read) installed under the same N2-exception discipline as ship.md; filed upstream as open-gsd/gsd-core#3646 with an explicit revert condition
- [Phase ?]: Filed open-gsd/gsd-core#3647 (capability lifecycle-dispatch reliability finding) as a distinct-but-related report alongside pre-existing #3606, rather than adopting it as a duplicate

### Pending Todos

None yet.

### Blockers/Concerns

- **[open-gsd/gsd-core#3646](https://github.com/open-gsd/gsd-core/issues/3646)** (native per-task
  external-tracker content-resolution seam) — re-check merge status before trusting the local
  `execute-plan.md` bd-task-read patch is still needed; see `GSD-CORE-PATCH.md` Patch 2's revert
  condition. Once merged, delete the marker-bracketed block, that section,
  `check_execute_plan_patch()`, and `beads-recall/SKILL.md`'s Step 3.5 call to it. **Phase 17 note:**
  TRUTH-02 merges that function into a shared reader — if #3646 lands first, the removal path
  changes shape. Re-check before planning 17-02.

- **[open-gsd/gsd-core#3647](https://github.com/open-gsd/gsd-core/issues/3647)** filed as a
  framework-level observation (capability lifecycle-dispatch steps intermittently skipped). No
  local patch corresponds to it; this project's own `reconcile-stale-closed` backstop already
  covers the local symptom regardless of upstream disposition.

- **[v1.1 formality, carried forward]** Phase 12's work is done and pushed but the v1.1 milestone
  was never formally closed via `/gsd-complete-milestone` (user decision, 2026-08-18) — its
  RETROSPECTIVE.md section is also missing as a result. Not a v1.3 blocker, but worth a
  retroactive backfill if the gap starts costing real time.

- **[Phase 16, one unverified path]** No real stripped `PLAN.md` has run through a live
  `gsd-executor` session yet in this repo — the bd-read patch's branch-trigger conditions are
  UAT-verified live against real `bd` (throwaway fixture, simulated failure, a genuine
  pre-migration issue), not exercised end-to-end. Will self-resolve the first time a future
  phase's `auto`/`tracer` tasks actually get stripped and executed.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260815-mm8 | Fix gsd-beads-uh1 and gsd-beads-bgb | 2026-08-15 | cb0741e | | [260815-mm8](./quick/260815-mm8-fix-gsd-beads-uh1-create-issues-epic-per/) |
| 260818-h2h | Fix gsd-beads-1iq: scope beads-lifecycle marketplace source to exclude sota-numerics/ponytail dev copies | 2026-08-18 | 4d83504 | Verified | [260818-h2h](./quick/260818-h2h-fix-gsd-beads-1iq-scope-beads-lifecycle-/) |
| 260819-e7a | Revise README.md with a full gsd-beads configuration reference section | 2026-08-19 | 640ccc3 | | [260819-e7a](./quick/260819-e7a-revise-readme-md-with-a-full-gsd-beads-c/) |
| 260819-k4p | Fix gh-2: dispatch the four lifecycle hooks gsd-core never reached (capability 0.3.0 / plugin 1.3.0) | 2026-08-19 | 62162d4 | Verified | [260819-k4p](./quick/260819-k4p-fix-gsd-beads-2-lifecycle-hook-dispatch/) |

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Capability | `get-available-resources` (RES-01) | Deferred to v2 — no "compute-heavy phase" signal exists in gsd-core to consume the advisory yet | v1.2 requirements, 2026-08-18 |
| Gate maturity | `pr-workflow.ship_gate` → blocking (PRW-05) | Deferred to v2 — needs one real PR cycle first | v1.2 requirements, 2026-08-18 |
| Gate maturity | `markdown-linting.ship_gate` → blocking (MDL-05) | Deferred to v2 — needs a clean full-milestone run first | v1.2 requirements, 2026-08-18 |
| Runtime reach | Lifecycle dispatch outside Claude Code (REACH-01) | Deferred — v1.3 is truth-in-declaration, not reach | v1.3 requirements, 2026-08-19 |

## Session Continuity

Last session: 2026-08-19
Stopped at: v1.3 roadmap created — Phase 17 (Config/Code Truth), TRUTH-01 + TRUTH-02 mapped, 2 plans
Resume file: None

## Operator Next Steps

- `/gsd-plan-phase 17` — TRUTH-01's plan must carry the Alternatives Considered table and the
  migration answer for existing `"sync_mode": "mirror"` / `"off"` projects; both plans go through
  plan-check and the verifier (no quick path this milestone).
