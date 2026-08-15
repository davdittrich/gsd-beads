# Phase 4: Adoption - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Existing hand-tracked todos move into beads, and the plan-task ↔ issue mapping is inspectable
on demand — at whichever epic granularity the user prefers. Covers REQ-B12, REQ-B13, REQ-B14.
Depends only on Phase 1 (substrate) — independent of Phase 2 (visibility) and Phase 3
(enforcement) machinery.

</domain>

<decisions>
## Implementation Decisions

### Todo → issue field mapping (B12)
- **D-01:** A pending todo's `severity` (blocker/major/minor/cosmetic) frontmatter maps to bd
  priority; `area` frontmatter becomes a bd label. Both fields carry forward structurally, neither
  is dropped into prose-only.
- **D-02:** The exact severity→priority numeric mapping is NOT locked here — research must verify
  bd's actual priority scale against the real installed `bd` CLI before the planner locks the
  mapping. — **Reversibility:** costly — **rationale:** same failure mode Phase 1 hit with
  `--id`/hierarchical-child-ids/`--parent` defaults: guessing at bd's schema from docs produced
  code that had to be corrected after live discovery; verify first this time.
- **D-03:** A todo's `files:` frontmatter (`file:lines` pointers) carries into the created issue's
  body/description as prose — no structured bd field exists for it, same treatment as
  Problem/Solution text.

### Un-interpretable / already-moved todos (B12)
- **D-04:** A todo that cannot be parsed (missing required frontmatter, malformed file) is left in
  place in `.planning/todos/pending/`, untouched — migration is non-destructive. The migration
  report lists it so a human can fix and re-run.
- **D-05:** A todo that WAS successfully migrated has its file deleted after the bd issue is
  created — bd becomes the sole source of truth for that item, matching the project's core value
  ("zero duplicated task-state bookkeeping survives in `.planning/`"). Re-running the migration
  later only ever sees genuinely-new, not-yet-migrated todos — no separate migrated-marker
  mechanism needed.
- **D-06:** No duplicate detection against existing bd issues — every parseable todo always
  creates a new issue on each migration run. — **Reversibility:** reversible — **rationale:** a
  slipped-through duplicate is a cheap one-off `bd close`/`bd delete`, not a migration
  correctness bug; fuzzy title/content matching would be an unreliable heuristic and violates N4's
  spirit (no clever inference from artifact text).

### beads-status "on demand" surface (B13)
- **D-07:** A new user-invokable slash command (e.g. `/gsd-beads-status [phase]`) exposes the
  plan-task ↔ issue mapping on demand — today `beads-status` only fires via `steps[]` lifecycle
  dispatch (`execute:wave:pre/post`, `verify:post`, `ship:pre`); this phase adds the first
  human-invoked entry point.
- **D-08:** With no phase argument, the command defaults to the current/last-active phase (infer
  from `STATE.md`'s `current_phase`); an explicit phase argument overrides. Matches the existing
  `beads-status` skill's `argument-hint: "[phase directory] [plan id...]"` shape.
- **D-09:** Orphans on both sides — a bd issue with no matching plan task, and a plan task with no
  bd issue — are rendered as two separate labeled sections below the main mapping table (not extra
  table columns), matching the "Unscoped" heading pattern `BEADS-RECALL.md` already established in
  Phase 2.

### epic_per=milestone behavior (B14)
- **D-10:** Setting `beads.epic_per=milestone` applies forward-only — it does NOT retroactively
  fold already-created per-phase epics (Phases 1-3's existing epics) under one milestone epic.
  — **Reversibility:** one-way if reversed later — **rationale:** matches B10's "never
  auto-reconciled" philosophy; a retroactive-fold feature would be a real `bd` re-parent write
  operation against historical data, a materially different and riskier feature than this phase
  scopes.
- **D-11:** `beads.epic_per` can be changed at any point mid-milestone — it is read fresh at each
  epic-creation call site, no lock or validation gate needed. A phase already mid-flight keeps
  whatever epic it already has regardless of a later config change.

### Migration invocation & report format (B12)
- **D-12:** The one-shot migration is triggered via a new slash command (e.g.
  `/gsd-migrate-todos`), consistent with D-07's on-demand beads-status decision — not a bare
  `sync.py` CLI-only invocation.
- **D-13:** The migration report ("what moved vs what could not be interpreted") is console output
  only — no separate `.planning/` artifact (e.g. `MIGRATION-REPORT.md`). bd itself is the durable
  record of what moved; a written report would be a second bookkeeping surface that could go
  stale, contradicting the project's core value.

### Claude's Discretion
- Exact severity→priority numeric mapping (D-02) — pending research verification of bd's real
  priority scale.
- Exact slash-command names (`/gsd-beads-status`, `/gsd-migrate-todos`) and their argument parsing
  details.
- Exact section headings/wording for the two orphan sections (D-09), as long as the pattern
  matches `BEADS-RECALL.md`'s established "Unscoped" heading style.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product requirements
- `.planning/REQUIREMENTS.md` — REQ-B12, REQ-B13, REQ-B14 with acceptance criteria; this phase's
  scope
- `.planning/PROJECT.md` — Active requirements section (B12/B13/B14) and Key Decisions table;
  N1-N6 Out of Scope constraints (especially N4: no command strings assembled from artifact text,
  and N5: no dependency beyond `bd` and Python stdlib) apply directly to the migration script

### Prior-phase verified findings (carry forward, do not re-derive)
- `.planning/phases/01-substrate/01-CONTEXT.md`, `01-*-SUMMARY.md` — real `bd` v1.2.1 CLI
  divergence from docs (no `--id`, hierarchical child ids, `bd list --parent` hides closed by
  default) — the same live-verification discipline applies to D-02's priority-scale research
- `.planning/phases/02-visibility/02-*-SUMMARY.md` — `_escape_table_cell`, `confined`,
  `resolve_phase_epic`/`collect_epic_task_ids`, the "Unscoped" heading pattern this phase's D-09
  orphan sections reuse
- `.gsd/capabilities/beads/scripts/sync.py` — read before writing any new function; reuse
  `run_bd`, `bd_available`, `confined`, `find_project_root`, `resolve_phase_epic`,
  `collect_epic_task_ids`, `_escape_table_cell` rather than duplicating logic
- `.gsd/capabilities/beads/capability.json` — current manifest shape (`steps[]`,
  `contributions[]`, `gates[]`); this phase adds new slash-command surfaces, not new lifecycle
  hook points
- `.claude/gsd-core/workflows/add-todo.md` — canonical todo file format (frontmatter:
  `created`/`title`/`area`/`severity`/`files`; body: `## Problem` / `## Solution`) that the
  migration parser must handle

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.gsd/capabilities/beads/scripts/sync.py:resolve_phase_epic`,
  `collect_epic_task_ids` — epic resolution to extend for D-10/D-11's `epic_per` config read
- `.gsd/capabilities/beads/scripts/sync.py:_escape_table_cell`,
  `_render_beads_md_table` — table-rendering patterns to reuse for the on-demand mapping output
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md` — Step 1.5 lifecycle-point branch pattern
  (D-11 from Phase 2) to extend with a new on-demand branch for D-07/D-08

### Established Patterns
- Every `bd` invocation is argv-list, `shell=False`, single call site (`run_bd`) — the migration's
  `bd create` calls must follow this
- Fail-open per B6: `bd` absent/failing/locked degrades to a no-op with one visible notice — the
  new slash commands must follow this too, not introduce a new failure mode
- `.planning/todos/pending/*.md` currently EMPTY in this project — no live fixtures exist; the
  migration script's parser and D-04/D-05 file-handling logic will need synthetic test fixtures
  matching `add-todo.md`'s exact frontmatter/body schema

### Integration Points
- New slash commands (D-07, D-12) are the first human-invoked entry points this capability adds —
  everything through Phase 3 only fires via `steps[]`/`gates[]` lifecycle dispatch
- `capability.json`'s config schema gains `beads.epic_per` (default likely `phase`, opt-in
  `milestone`) alongside the existing `beads.enabled`/`beads.ship_gate` keys

</code_context>

<specifics>
## Specific Ideas

No specific UI/UX references — this phase adds two new slash-command surfaces (migration,
on-demand status) and a config option, all rendered as markdown/console text following patterns
already established in `BEADS-RECALL.md`/`BEADS.md`.

</specifics>

<deferred>
## Deferred Ideas

None raised during this discussion — stayed within B12/B13/B14 scope throughout.

### Reviewed Todos (not folded)
None — `.planning/todos/pending/` is currently empty; no todos existed to match against this
phase's scope.

</deferred>

---

*Phase: 4-Adoption*
*Context gathered: 2026-08-15*
