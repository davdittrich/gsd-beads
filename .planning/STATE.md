---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Publish & Document
current_phase: 12
current_phase_name: ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
status: executing
stopped_at: Completed 12-02-PLAN.md
last_updated: "2026-08-17T16:32:14.720Z"
last_activity: 2026-08-17
last_activity_desc: All v1.1 phases (5-9, plus inserted 10/10.1/11/11.1) verified complete; ROADMAP.md tracking corrected — Phase 9's Progress row and milestone checkbox were stale (query-blocked by an upstream gsd-core plan-scan bug misclassifying 09-PLAN-CHECK.md as an unsummarized plan)
progress:
  total_phases: 10
  completed_phases: 8
  total_plans: 25
  completed_plans: 22
  percent: 80
---

Total Phases: 3
---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Publish & Document
current_phase: 08
current_phase_name: readme-release-ship-gate
status: Ready to execute
stopped_at: Phase 8 context gathered
last_updated: "2026-08-16T15:30:06.762Z"
last_activity: 2026-08-16
last_activity_desc: v1.1 roadmap created (Phases 5-8, 10/10 requirements mapped)
progress:[█████████░] 88%
  total_phases: 4
  completed_phases: 3
  total_plans: 6
  completed_plans: 4
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-15)

**Core value:** gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero
duplicated task-state bookkeeping survives in `.planning/`.
**Current focus:** Phase 12 — ship-ponytail-everywhere-and-sota-numerics-plugins-publicly

## Current Position

Phase: 12 (ship-ponytail-everywhere-and-sota-numerics-plugins-publicly) — EXECUTING
Plan: 3 of 4
Status: Ready to execute
Last activity: 2026-08-17 — Phase 12 execution started

## Performance Metrics

**Velocity:**

- Total plans completed: 6
- Average duration: - min
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 10 | 2 | - | - |
| 10.1 | 2 | - | - |
| 11.1 | 2 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 8min | 2 tasks | 7 files |
| Phase 01 P02 | 12min | 3 tasks | 4 files |
| Phase 02 P01 | 13min | 3 tasks | 5 files |
| Phase 02 P02 | 15min | 3 tasks | 5 files |
| Phase 03 P01 | 8min | 2 tasks | 4 files |
| Phase 03 P02 | 7min | 2 tasks | 4 files |
| Phase 03 P03 | 20min | 2 tasks | 4 files |
| Phase 04-adoption P01 | 20min | 2 tasks | 6 files |
| Phase 04-adoption P02 | ~12min | 2 tasks | 3 files |
| Phase 04-adoption P03 | ~15min | 2 tasks | 3 files |
| Phase 05 P01 | ~11min | 3 tasks | 3 files |
| Phase 06 P01 | 25min | 3 tasks | 4 files |
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

## Accumulated Context

### Decisions

Full decision log lives in PROJECT.md's Key Decisions table (v1.0 milestone archived to
`.planning/milestones/v1.0-ROADMAP.md` for phase-level detail). Cleared here at milestone close.

- [Phase 10]: ponytail-everywhere plugin: gsd-tools resolves via CLAUDE_CONFIG_DIR branch (repo-local absent, PATH absent); claude plugin validate . --strict accepted ./ponytail-everywhere source on first try; test harness proves scratch-dir config isolation with zero repo mutation
- [Phase 10]: Plan 02 relocated the verifier contribution from verify:pre to execute:wave:post — gsd-core's Loop Host Contract restricts verify:pre/post's contribution.into to [orchestrator] only, 'verifier' is only valid within the execute step's points
- [Phase 10]: Plan 02 — project-scope capability consent binds to realpath(projectRoot) (#1459) — a --cwd symlink mirror needs its own GSD_HOME-scoped consent record to test the ponytail.enabled toggle, not just matching bundle content
- [Phase 10]: Code review found a real, reproduced critical bug (CR-01) — ponytail-everywhere/hooks/gsd-tools.sh built its node invocation as an unquoted string, breaking on any repo/HOME path containing a space and silently fail-opening to enabled:true; fixed via --fix (array-based invocation) with a genuine regression test
- [Phase ?]: Tracer feedback gate (Task 1) accepted as-is by user at checkpoint; Task 2 plugin-root parity case compares two independent first-install runs (separate GSD_HOME sidecars) for byte-identity rather than first-vs-second.
- [Phase ?]: Real marketplace install performed directly to close RESEARCH Assumption A2 (subdirectory-plugin cache layout confirmed); macOS shasum fallback (A3) accepted as documented gap, no macOS hardware available.
- [Phase ?]: [Phase 11]: sota-numerics plan:post gate uses onError: halt (deliberate divergence from every other gate in this repo) and resolves its script path via $(git rev-parse --show-toplevel), not ${CLAUDE_PLUGIN_ROOT} -- the gate subprocess's environment is unverified
- [Phase ?]: [Phase 11]: check-alternatives.py's validate_plan reports only the first offending alternative entry per plan (fail-fast), not every entry -- the gate is a structural backstop, the checker's pre-commit revision loop is the primary enforcement point
- [Phase ?]: [Phase 11]: sota-numerics D-12 four-point advisory spread wired -- planner/executor/verifier/orchestrator each get a distinct fragment gated solely on sota-numerics.enabled, no configValues (D-11); ship:pre contribution's into must be orchestrator per the loop-host contract's ship-step agentRoles
- [Phase ?]: [Phase 11]: D-08 resolved mechanical (Task 1 checkpoint, coordinator decision) -- check-alternatives.py's deterministic placeholder/TODO-TBD rejection stands in for gsd-plan-checker's LLM-mediated citation-plausibility spot-check; no gsd-core patch, no checker fragment, deferred pending a D-04 dogfood false-negative signal
- [Phase ?]: [Phase 11]: sota-numerics NOTES.md re-verified the plan-phase.md 13a-13e step ordering live (not from RESEARCH memory) -- unchanged: plan:post gate still fires after commit and STATE.md 'Ready to execute', checker revision loop remains the primary enforcement point
- [Phase ?]: [Phase 11.1]: beads.enabled shipped default flipped false->true (capability.json 0.2.0); all four beads skills' Step 1 gate inverted to opt-out polarity so a silent project runs beads by default while explicit beads.enabled:false still fully disables it.
- [Phase ?]: [Phase 11.1]: global-scope installed capability copy (~/.gsd/capabilities/beads/) is a materialized snapshot, not a live read of the source bundle -- must be refreshed via hooks/capability-auto-install.sh (or a fresh SessionStart) after any source bundle edit, same gotcha PROJECT.md already documents for project-scope consent.
- [Phase ?]: [Phase 11.1]: doc sweep (README, PRIME.md twins, PRD) brought in line with beads.enabled default true; CHANGELOG.md created at repo root keyed to capability.json 0.2.0, stating explicit beads.enabled values in .planning/config.json are unaffected
- [Phase ?]: [Phase 12]: davdittrich/ponytail-everywhere shipped as standalone public repo (fresh git init, commit 36245fe), proving the stage-outside-tree + fix-relocation-paths + gh-repo-create-push + fresh-clone-verify tracer sequence for Plan 02 to repeat against sota-numerics
- [Phase ?]: [Phase 12]: davdittrich/sota-numerics shipped as standalone public repo (fresh git init, commit 31608f2), proving the 12-01 tracer sequence generalizes to a plugin with a blocking plan:post gate and a Python unittest suite (19 tests); test_check_alternatives.py's PROJECT_ROOT walk-up required a tests/.planning/.gitkeep placeholder in the staging tree, file itself left byte-identical

### Pending Todos

None yet.

### Blockers/Concerns

- [Resolved by roadmap] The packaging gap (no README, LICENSE, or git remote) is now owned by
  Phases 5-8. Memory `gsd-beads-ships-as-github-plugin` no longer describes an unowned gap.

- [Phase 7, one-way door] The window to strip machine-local state from git history closes at the
  first public push. `.beads/config.yaml`, `.beads/metadata.json`,
  `.claude/.headroom_wrap_marker.json`, `.gsd-capabilities.json` are tracked today.

- [Resolved 2026-08-16, Phase 6] The capability-loader bridge (PUB-03) decision is closed: satisfied
  by the documented manual `capability install --scope project --yes` step, not an automatic
  postinstall bridge. Verified from a clean scratch project against `.gsd/capabilities/beads/` in
  this repo — see PROJECT.md Key Decisions and `06-01-SUMMARY.md`.

- [Phase 7/8, allowlist gap] PUB-04's ship allowlist (`.claude-plugin/`, `hooks/`,
  `.agents/skills/`, `README.md`, `LICENSE`) omits `.gsd/capabilities/beads/`. The PUB-03 bridge
  command's spec argument only resolves against a full git clone of this repository, not the
  Phase 8 release archive — Phase 8's README must direct users to clone the repo for this step
  unless Phase 8 amends the allowlist to include the capability bundle. Phase 6 does not decide
  this; it hands the gap forward.

- [Phase 5/8, false-green risk] `claude plugin validate` skips skill-frontmatter checks when
  `marketplace.json` is present, and only `--strict` promotes field warnings to errors.

- [Resolved 2026-08-16] Phase 05 Plan 01 Task 1's two HALT blockers (author.name/D-02, root-CLAUDE.md/D-10) were both resolved by user decision; 05-01 completed all 3 tasks, requirements PUB-01/PUB-02/PUB-08 marked complete. See 05-01-SUMMARY.md.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260815-mm8 | Fix gsd-beads-uh1 (create_issues epic-per-plan) and gsd-beads-bgb (orphan sweep closes sibling issue) | 2026-08-15 | cb0741e | [260815-mm8-fix-gsd-beads-uh1-create-issues-epic-per](./quick/260815-mm8-fix-gsd-beads-uh1-create-issues-epic-per/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-08-17T16:32:14.713Z
Stopped at: Completed 12-02-PLAN.md
Resume file: None

## Operator Next Steps

- Phase 06 complete — TTY backstop confirmed by user (06-UAT.md), SECURITY.md verified
  (threats_open: 0). Plan Phase 07 (Hygiene & Publication) with /gsd-plan-phase 7
