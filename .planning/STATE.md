---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: New Capability Plugins
current_phase: 13
current_phase_name: markdown-linting-capability-dogfood
status: Roadmap created — ready to plan Phase 13
stopped_at: Phase 13 context gathered
last_updated: "2026-08-18T09:55:14.669Z"
last_activity: 2026-08-18
last_activity_desc: v1.2 roadmap created (Phases 13-15, 8/8 requirements mapped)
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 3
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-18)

**Core value:** gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero
duplicated task-state bookkeeping survives in `.planning/`.
**Current focus:** Phase 13 — markdown-linting capability (dogfood)

## Current Position

Phase: 13 — markdown-linting capability (dogfood)
Plan: —
Status: Roadmap created, phase not yet planned
Progress: [··········] 0% (0/3 phases)
Last activity: 2026-08-18 — v1.2 roadmap created

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

Full v1.0/v1.1 per-plan history: `.planning/STATE-ARCHIVE.md`.

## Accumulated Context

### Decisions

Full decision log lives in PROJECT.md's Key Decisions table. Carried forward into v1.2 because
Phase 15 repeats the Phase 12 extraction playbook directly:

- [Phase 3]: `ship:pre` gate dispatch in the installed `ship.md` is a **machine-local patch**
  (upstream open-gsd/gsd-core#3559 filed, merge status unconfirmed). Any new gate must verify the
  patch marker is present and prove itself live via `gsd_run check predicate` before being trusted.

- [Phase 6/10]: gsd-core capability consent is a content hash over the whole bundle — any
  post-consent edit silently deactivates the capability with no error. Re-consent after every edit.

- [Phase 10.1]: `hooks/capability-auto-install.sh` hashes the bundle against a per-id sidecar and
  re-grants on drift; vendored into each plugin's `session-start.sh`.

- [Phase 11]: `sota-numerics`' `plan:post` gate uses `onError: halt` (deliberate divergence) and
  resolves its script path via `git rev-parse --show-toplevel`, not `${CLAUDE_PLUGIN_ROOT}`.

- [Phase 12]: `davdittrich/ponytail-everywhere` and `davdittrich/sota-numerics` shipped via the
  stage-outside-tree → fix-relocation-paths → `gh repo create` + push → fresh-clone-verify sequence.

- [Phase 12]: `marketplace.json` entries must use `url`-type sources with explicit `https://` git
  URLs (commit `f706179`) — GitHub shorthand clones over SSH and breaks on SSH-keyless machines.

- [Phase 12]: Dogfood subdirectories were removed from `gsd-beads` in the same commit that repaired
  the orphaned `ci.yml` / `release.yml` references.

### Pending Todos

None yet.

### Blockers/Concerns

- **[Phase 13, hard prerequisite]** The generic `ship:pre` gate-dispatch patch is machine-local and
  unconfirmed upstream. Phase 13's plan must include an explicit task verifying the marker in
  `$HOME/.claude/gsd-core/workflows/ship.md` before relying on the `markdown-linting` gate. If the
  marker is absent, the gate silently never fires and both Phase 13 and Phase 14 success criteria
  would be false-but-unnoticed.

- **[Phase 15, pre-extraction check]** Re-check gsd-core#3559's merge status before public
  extraction. If unmerged, each plugin's README must document the required local `ship.md` patch as
  a prerequisite, exactly as PROJECT.md already does — otherwise a stranger installs a plugin whose
  gate cannot fire.

- **[Phase 13, MEDIUM confidence]** The curated `rumdl` ruleset is validated only in theory. Phase
  13 must run it against the live `.planning/` tree and hand-review the output; if the corpus has
  violations the ruleset misses, iterate on the ruleset before the gate ships.

- **[Phases 13-14, advisory-by-design]** Both new gates default advisory. A green ship is therefore
  *not* evidence the gate works — only the live `gsd_run check predicate` smoke test is.

- **[v1.1 formality]** Phase 12's work is done and pushed but the milestone was never formally
  closed via `/gsd-complete-milestone` (user decision, 2026-08-18). Not a v1.2 blocker.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260815-mm8 | Fix gsd-beads-uh1 and gsd-beads-bgb | 2026-08-15 | cb0741e | [260815-mm8](./quick/260815-mm8-fix-gsd-beads-uh1-create-issues-epic-per/) |

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Capability | `get-available-resources` (RES-01) | Deferred to v2 — no "compute-heavy phase" signal exists in gsd-core to consume the advisory yet | v1.2 requirements, 2026-08-18 |
| Gate maturity | `pr-workflow.ship_gate` → blocking (PRW-05) | Deferred to v2 — needs one real PR cycle first | v1.2 requirements, 2026-08-18 |
| Gate maturity | `markdown-linting.ship_gate` → blocking (MDL-05) | Deferred to v2 — needs a clean full-milestone run first | v1.2 requirements, 2026-08-18 |

## Session Continuity

Last session: 2026-08-18T09:08:37.676Z
Stopped at: Phase 13 context gathered
Resume file: .planning/phases/13-markdown-linting-capability-dogfood/13-CONTEXT.md

## Operator Next Steps

- Plan Phase 13 with `/gsd:plan-phase 13`. The plan **must** include, as an explicit task before
  any gate work: verify the generic `ship:pre` dispatch marker in the installed `ship.md`.
