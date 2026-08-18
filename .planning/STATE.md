---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: New Capability Plugins
current_phase: 14
current_phase_name: pr-workflow capability (dogfood)
status: executing
stopped_at: Phase 14 context gathered
last_updated: "2026-08-18T16:07:41.426Z"
last_activity: 2026-08-18
last_activity_desc: Phase 13 complete, transitioned to Phase 14
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 7
  completed_plans: 4
  percent: 33
---

Total Phases: 2
---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: New Capability Plugins
current_phase: 14
current_phase_name: pr-workflow capability (dogfood)
status: executing
stopped_at: Phase 14 context gathered
last_updated: "2026-08-18T15:25:16.511Z"
last_activity: 2026-08-18
last_activity_desc: v1.2 roadmap created (Phases 13-15, 8/8 requirements mapped)
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 7
  completed_plans: 4
  percent: 33
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-18)

**Core value:** gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero
duplicated task-state bookkeeping survives in `.planning/`.
**Current focus:** Phase 13 — markdown-linting-capability-dogfood

## Current Position

Phase: 14 — pr-workflow capability (dogfood)
Plan: Not started
Status: Ready to execute
Progress: [██████████] 100% (0/3 phases)
Last activity: 2026-08-18 — Phase 13 complete, transitioned to Phase 14

## Performance Metrics

**Velocity:**

- Total plans completed (v1.2): 0
- Average duration: -
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

Full v1.0/v1.1 per-plan history: `.planning/STATE-ARCHIVE.md`.

## Accumulated Context

### Decisions

Full decision log lives in PROJECT.md's Key Decisions table. Carried forward into v1.2 because
Phase 15 repeats the Phase 12 extraction playbook directly:

  (upstream open-gsd/gsd-core#3559 filed, merge status unconfirmed). Any new gate must verify the
  patch marker is present and prove itself live via `gsd_run check predicate` before being trusted.

  post-consent edit silently deactivates the capability with no error. Re-consent after every edit.

  re-grants on drift; vendored into each plugin's `session-start.sh`.

  resolves its script path via `git rev-parse --show-toplevel`, not `${CLAUDE_PLUGIN_ROOT}`.

- [Phase 12]: `davdittrich/ponytail-everywhere` and `davdittrich/sota-numerics` shipped via the
  stage-outside-tree → fix-relocation-paths → `gh repo create` + push → fresh-clone-verify sequence.

- [Phase 12]: `marketplace.json` entries must use `url`-type sources with explicit `https://` git
  URLs (commit `f706179`) — GitHub shorthand clones over SSH and breaks on SSH-keyless machines.

- [Phase 12]: The claim previously recorded here — that dogfood subdirectories were removed from
  `gsd-beads` in the same commit that repaired the orphaned `ci.yml` / `release.yml` references —
  was found false during quick-task 260818-h2h: `git log --follow` showed no deletion commit ever
  existed for `.gsd/capabilities/{ponytail,sota-numerics}`, only their Phase 10/11 authoring
  commits (`932cf34`, `246dfbc`). Whatever Phase 12 removed, it was not these two paths. They were
  actually removed in quick-task 260818-h2h, by `git rm -r`, in the same commit that scoped the
  `beads-lifecycle` plugin source to `plugins/beads-lifecycle/`.

- [Phase 13]: Narrowed .gitignore's blanket .gsd/ ignore (from quick-task 260818-h2h) to un-ignore .gsd/capabilities/markdown-linting/ specifically -- the bare pattern silently blocked this milestone's documented in-repo dogfood pattern for brand-new capabilities with no extracted plugin source yet
- [Phase 13]: markdown-linting's verify_post fail-open path deliberately diverges from sync.py's regenerate_beads_md -- always overwrites LINT-REPORT.md with a non-numeric violation_count: unavailable sentinel instead of leaving a stale artifact untouched
- [Phase 13]: dirty.md/clean.md fixtures pin MDL-01/02/04 test coverage against real rumdl subprocess calls, never the live .planning/ tree; real-subprocess tests skip cleanly (unittest.skipUnless) on a machine with no rumdl/uvx
- [Phase 13]: isolated pre-existing unrelated dirty working-tree state (CLAUDE.md beads-block strip, state pruning, API-SURFACE staleness note, 13-PATTERNS.md) into its own prep commit before the wide auto-fix pass, so Task 1's mechanical-fix diff stayed spot-checkable
- [Phase 13]: markdown-linting README's rumdl-vs-markdownlint-cli2 divergence table is measured post-fix (rumdl 0 vs cli2 309, all MD022/MD024) -- a materially different, non-comparable shape from the pre-fix 471-vs-708 figure in RESEARCH.md/REQUIREMENTS.md
- [Phase 13]: closed CR-01/CR-02 lint.py gaps (rumdl_argv-None guard on count, CalledProcessError fail-open widening) verbatim per 13-REVIEW.md; two plan acceptance-criteria grep counts were miscounted by the plan author (pre-existing occurrences not accounted for) -- documented in 13-04-SUMMARY.md rather than silently 'corrected'

### Pending Todos

None yet.

### Blockers/Concerns

- **[Phase 15, pre-extraction check]** Re-check gsd-core#3559's merge status before public
  extraction. If unmerged, each plugin's README must document the required local `ship.md` patch as
  a prerequisite, exactly as PROJECT.md already does — otherwise a stranger installs a plugin whose
  gate cannot fire.

- **[Phases 13-14, advisory-by-design]** Both new gates default advisory. A green ship is therefore
  *not* evidence the gate works — only the live `gsd_run check predicate` smoke test is.

- **[v1.1 formality]** Phase 12's work is done and pushed but the milestone was never formally
  closed via `/gsd-complete-milestone` (user decision, 2026-08-18). Not a v1.2 blocker.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260815-mm8 | Fix gsd-beads-uh1 and gsd-beads-bgb | 2026-08-15 | cb0741e | | [260815-mm8](./quick/260815-mm8-fix-gsd-beads-uh1-create-issues-epic-per/) |
| 260818-h2h | Fix gsd-beads-1iq: scope beads-lifecycle marketplace source to exclude sota-numerics/ponytail dev copies | 2026-08-18 | 4d83504 | Verified | [260818-h2h](./quick/260818-h2h-fix-gsd-beads-1iq-scope-beads-lifecycle-/) |

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Capability | `get-available-resources` (RES-01) | Deferred to v2 — no "compute-heavy phase" signal exists in gsd-core to consume the advisory yet | v1.2 requirements, 2026-08-18 |
| Gate maturity | `pr-workflow.ship_gate` → blocking (PRW-05) | Deferred to v2 — needs one real PR cycle first | v1.2 requirements, 2026-08-18 |
| Gate maturity | `markdown-linting.ship_gate` → blocking (MDL-05) | Deferred to v2 — needs a clean full-milestone run first | v1.2 requirements, 2026-08-18 |

## Session Continuity

Last session: 2026-08-18T14:53:25.598Z
Stopped at: Phase 14 context gathered
Resume file: .planning/phases/14-pr-workflow-capability-dogfood/14-CONTEXT.md

## Operator Next Steps

- Plan Phase 13 with `/gsd:plan-phase 13`. The plan **must** include, as an explicit task before
  any gate work: verify the generic `ship:pre` dispatch marker in the installed `ship.md`.
