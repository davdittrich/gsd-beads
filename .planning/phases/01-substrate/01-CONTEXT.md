# Phase 1: Substrate - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Every `PLAN.md` task in a phase gets exactly one beads issue, parented to that phase's epic.
Task ordering (explicit "depends on" edges) becomes `bd dep add` calls. Task completion closes
its issue automatically. Identity between a task and its issue is bound by an explicit
`beads-id:` field, never by title matching. Sync is idempotent — re-running it over an unchanged
plan creates and modifies nothing. If `bd` is absent, failing, or locked, every gsd command
still completes normally with one visible notice; no phase is blocked. Covers REQ-B1 through
REQ-B6.

</domain>

<decisions>
## Implementation Decisions

### Content ownership (overrides prior PROJECT.md decision)
- **D-01:** `beads.sync_mode` (`authoritative`) now covers task *status AND content*, not status
  only. A bd issue's title/description originates from `PLAN.md` at first sync, but the bd issue
  is authoritative from that point forward — `PLAN.md`'s task text is never re-synced from later
  bd edits. — **Reversibility:** one-way — **rationale:** B10 divergence semantics, the sync
  idempotency proof (B5), and downstream planner/executor prompts (Phase 2) all get built around
  "bd is truth for content"; reverting to status-only ownership after Phase 2 ships means
  re-deriving divergence detection and re-auditing every consumer of issue content.
  PROJECT.md's Key Decisions table and Binding Model section have been updated to match
  (2026-08-15) — this supersedes the original ingest-derived "PLAN.md owns content" decision.

### Issue shape
- **D-02:** Issue title is prefixed with the task's id/number from `PLAN.md` (not verbatim task
  title) — supports sort/search across phases in `bd list`.
- **D-03:** `beads-id:` lives as a one-line metadata field directly under the task heading in
  `PLAN.md` (e.g. `beads-id: bd-123` right after `### Task 3: ...`) — visible, greppable, minimal
  format change to existing `PLAN.md` structure.

### Dependency mapping (B2)
- **D-04:** Only explicit "depends on" edges in `PLAN.md` become `bd dep add` calls. Wave
  grouping (parallel-batch scheduling) is NOT treated as an implicit dependency — a task in wave
  N+1 with no explicit edge to wave N is not blocked on it in `bd ready`.

### Epic naming
- **D-05:** Phase epic title in bd is the phase header verbatim from `ROADMAP.md`, e.g.
  `"Phase 1: Substrate"` — zero translation/mapping logic between roadmap and bd.

### Replan / orphan handling
- **D-06:** When a phase is replanned and a previously-synced issue no longer matches any current
  task, the orphaned issue is closed with a note explaining it no longer maps to a plan task.
  Nothing is silently left dangling or silently deleted. — **Reversibility:** costly —
  **rationale:** closing writes a bd state change (comment + status transition) that a future
  "undo" would need to specifically detect and reopen; there's no batch undo for this.

### Stale/divergent identity
- **D-07:** If a task's `beads-id:` points at an issue that no longer exists in bd (deleted
  externally), treat it as B10 divergence: block ship, report both sides. Never silently
  recreate a fresh id and never hard-error the sync step itself — consistent with B6's fail-open
  guarantee and B10's "never auto-reconciled" rule.

### Fail-open notice (B6)
- **D-08:** The one required visible notice is a stdout line at the point `bd` is found
  absent/failing/locked, AND a corresponding entry is appended under `.planning/STATE.md`'s
  "Blockers/Concerns" section so the condition stays visible across sessions without a new
  artifact type.

### Claude's Discretion
- Exact stdout notice wording/format.
- Exact `bd dep add` invocation shape (batched vs. per-edge) as long as B5 idempotency holds.
- Whether the epic is created eagerly at first sync or lazily on first issue — pick whichever is
  simpler given how `plan:post` hooks fire in gsd-core (technical, not user-facing).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product requirements
- `docs/prd-beads-capability.md` — full PRD; §12 open questions (execute:wave:post firing
  granularity, packaging) still need resolving during research/planning, not discussion
- `.planning/PROJECT.md` — locked project decisions, constraints, binding model (updated
  2026-08-15 per D-01 above)
- `.planning/REQUIREMENTS.md` — REQ-B1..B14 with measurable acceptance criteria; B1-B6 are this
  phase's scope

### gsd-core capability mechanism (BLOCKER — not present in this checkout)
- No local gsd-core source checkout (`src/capability-loader.cts`, `tests/capability-loader.test.cjs`,
  `capabilities/mempalace/capability.json`) exists anywhere on this disk — only the runtime skill
  overlay at `~/.claude/gsd-core/` (workflows/references/bin, no `src/`). The PRD's claims about
  the capability registry shape, `steps[]`/`contributions[]`/`gates[]`, and the mempalace analogue
  are unverified against source in this environment.
- **Explicit research task for Phase 1 (per user decision 2026-08-15):** the researcher must
  locate and fetch the gsd-core source (npm package or GitHub) before any implementation claims
  about `capability-loader.cts`, `capability.json` schema, or `mempalace`'s shape can be trusted.
  Do not proceed to planning on PRD claims alone without this verification.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
None — this repository (`gsd-beads`) currently holds only `docs/prd-beads-capability.md` and
`.planning/`; no source code exists yet (net-new capability, greenfield within this repo).

### Established Patterns
None locally. The PRD names `capabilities/mempalace/capability.json` in the (unavailable)
gsd-core checkout as the closest shipped analogue for shape and degrade-cleanly behavior — must
be fetched and read per the canonical_refs blocker above before it can inform this phase's design.

### Integration Points
- gsd-core capability registry overlay: `$GSD_HOME/.gsd/capabilities/beads/` (global) or
  `<projectRoot>/.gsd/capabilities/beads/` (project) — per PROJECT.md Constraints, project-scoped
  ships first.

</code_context>

<specifics>
## Specific Ideas

No specific UI/UX references — this is an infrastructure/plumbing phase. The PRD's acceptance
criteria (B1-B6) are already precise and mechanistic; discussion focused on the handful of
genuine implementation-preference gray areas (content ownership, issue shape, dependency
mapping, orphan handling, notice destination) rather than broad exploratory questions.

</specifics>

<deferred>
## Deferred Ideas

- PRD §12 open question: does `execute:wave:post` fire per task or per wave? Decides whether B3
  closes one issue or several at a time — this is a technical/architecture question for the
  researcher to answer by reading gsd-core's hook system, not a user preference; carried forward
  from `.planning/STATE.md` Blockers/Concerns.
- PRD §12 open question: packaging (Python entry point vs. JS shell-out) — already constrained by
  PROJECT.md's N5 (`bd` binary + Python 3 stdlib only, no other dependency); researcher should
  confirm this resolves the open question rather than treating it as still open.
- PRD §12 open question: where a `beads.ship_gate=false` override gets recorded so it stays
  visible afterward — relevant to Phase 3 (Enforcement), not Phase 1.

### Reviewed Todos (not folded)
None — `todo.match-phase` returned zero matches for this phase.

</deferred>

---

*Phase: 1-Substrate*
*Context gathered: 2026-08-15*
