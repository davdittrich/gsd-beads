# Phase 3: Enforcement - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning

<domain>

## Phase Boundary

Beads state can block a ship — a phase with unfinished or diverged issues does not pass unless
the operator overrides deliberately, and the override is recorded. Covers REQ-B9, REQ-B10. Ship
gate only — no new bd write calls beyond what Phases 1-2 already built (create-issues, dependency
edges, close-wave, BEADS-RECALL.md, BEADS.md regeneration).

</domain>

<decisions>

## Implementation Decisions

### blocking_open definition (B9)
- **D-01:** `blocking_open` counts every open issue under the phase's shared beads epic — not
  scoped to issues synced from this phase's own plans alone. No priority/type filtering; an open
  issue under the epic counts, full stop. — **Reversibility:** costly — **rationale:** Phase 3's
  ship gate reads this field via `artifact-frontmatter-equals`; narrowing the definition later
  means re-touching the gate predicate's semantics and every consumer that has learned to trust
  the current count.
- **D-02:** Scope follows the epic (post-gsd-beads-uh1/gsd-beads-bgb fix: `resolve_epic` is now
  phase-scoped and `find_orphans` is epic-scoped), matching what `regenerate_beads_md` already
  computes — no new scanning logic, reuse the existing epic-wide issue enumeration.

### Divergence detection (B10)
- **D-03:** Divergence is computed at every `BEADS.md` regeneration (`execute:wave:pre`,
  `execute:wave:post`, `verify:post`) — one more field alongside `blocking_open`/`open`/`closed`
  in the same pass that already makes a live `bd` query, not a new call site or a check that only
  runs at `ship:pre`.
- **D-04:** Trigger per issue: for each synced issue (linked via `<beads-id>` to a task), compare
  `bd` status against task-completion state. Diverged in either direction counts: `bd` status
  `closed` while the linked task has no completing `SUMMARY.md`, OR `bd` status `open` while the
  linked task's `SUMMARY.md` marks it done. `diverged` in `BEADS.md` frontmatter is the count of
  issues meeting this predicate.

### Override audit trail (B9, PRD §12 Q3 — resolved)
- **D-05:** When `beads.ship_gate=false` allows a ship past an otherwise-blocking gate, record it
  in **both** places: (1) a commit trailer on the ship commit (e.g. `Beads-Override: ship_gate
  bypassed, blocking_open=N, diverged=N`) — always written, durable, travels with git history,
  needs no external tool at read time; (2) a `bd comment` on the phase epic recording the same
  fact — best-effort, follows this project's existing fail-open convention (B6): if `bd` is
  unavailable at ship time, skip the comment write and note the skip, never block the ship on it.
  The commit trailer is the load-bearing record; the bd comment is a convenience mirror.

### Divergence report shape (B10)
- **D-06:** No new artifact. Extend `BEADS.md`'s existing issue table (built in Phase 2, D-08)
  with columns surfacing each diverged issue's two sides — task status and `bd` status — rather
  than creating a separate `DIVERGENCE.md`. Visible at every step `BEADS.md` already regenerates;
  `ship:pre`'s blocking message can point the operator at this same table instead of duplicating
  the data into console output.

### Claude's Discretion
- Exact commit-trailer key name and format, as long as it's a real git trailer (`Key: value`
  syntax) parseable by `git log --format=%(trailers)`.
- Exact `bd comment` text content, as long as it names the override and the blocking_open/diverged
  values at override time.
- Which specific new column names/order to add to `BEADS.md`'s table for D-06 — pick whichever
  reads cleanest given the existing 5-column shape (issue/title/status/plan task/blocked-by).

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product requirements
- `docs/prd-beads-capability.md` §5.3 — the exact `gates[]` manifest shape for `ship:pre`: two
  `artifact-frontmatter-equals` predicates over `BEADS.md`'s `blocking_open` and `diverged`
  fields, both `blocking: true`, `onError: "skip"` — this is the locked gate mechanism, not a
  gray area re-opened by this discussion
- `docs/prd-beads-capability.md` §5.4 — `BEADS.md`'s frontmatter/table shape (baseline this
  phase extends with the divergence columns from D-06)
- `docs/prd-beads-capability.md` §12 Q3 — the override-auditing open question this discussion
  resolved as D-05
- `.planning/REQUIREMENTS.md` — REQ-B9, REQ-B10 with acceptance criteria; this phase's scope
- `.planning/PROJECT.md` Key Decisions — "gate predicates read only generated artifact
  frontmatter, never query `bd` directly" and "`gates[].onError: skip`, never `halt`" are already
  locked project-wide decisions this phase must follow, not re-derive

### Phase 1/2 verified findings (carry forward, do not re-derive)
- `.planning/phases/02-visibility/02-02-SUMMARY.md` — `regenerate_beads_md`'s full-overwrite
  regeneration pattern (D-05..D-08's frontmatter/table shape, built to the future shape
  specifically so Phase 3 doesn't have to re-touch every generation call site)
- `.gsd/capabilities/beads/scripts/sync.py` — read before writing any new function; reuse
  `run_bd`, `bd_available`, `confined`, `regenerate_beads_md`, `resolve_phase_epic`,
  `collect_epic_task_ids` (new in the gsd-beads-uh1/gsd-beads-bgb fix) rather than duplicating
  epic/issue enumeration logic
- `.gsd/capabilities/beads/capability.json` — current manifest with `plan:pre`/`execute:wave:pre`/
  `execute:wave:post` steps and the `plan:pre`→planner contribution; `gates[]` is currently empty
  — this phase adds the first two `ship:pre` gate entries

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets
- `.gsd/capabilities/beads/scripts/sync.py:regenerate_beads_md` — already makes the live `bd`
  query and writes `BEADS.md`'s frontmatter/table at every `execute:wave:*`/`verify:post` point;
  `blocking_open`/`diverged` computation and the new table columns extend this function, not a
  new one.
- `.gsd/capabilities/beads/scripts/sync.py:resolve_phase_epic`, `collect_epic_task_ids` — epic
  resolution and epic-wide issue-id enumeration already exist post-quick-task-260815-mm8; reuse
  for `blocking_open`'s epic-wide count and for finding every synced issue to check for
  divergence.
- `.gsd/capabilities/beads/tests/test_sync.py` — 41 existing tests, `_make_bd_side_effect`
  pattern; extend with `TestBlockingOpen`/`TestDivergence`/`TestShipGate` classes.

### Established Patterns
- Every `bd` invocation is argv-list, `shell=False`, single call site (`run_bd`) — must extend to
  any new `bd list`/`bd show`/`bd comment` calls this phase adds.
- Fail-open is per-script: a mid-operation `bd` failure degrades to the B6 notice + STATE.md
  bullet + exit 0 pattern — the D-05 bd-comment write for override auditing follows this same
  convention, never blocking the ship on a `bd` failure.
- Gate checks read only `BEADS.md` frontmatter (`artifact-frontmatter-equals`), never call `bd`
  live from the gate predicate itself — confirmed as a locked PROJECT.md decision, not
  re-litigated here.

### Integration Points
- `capability.json`'s `gates[]` array (currently empty) gains two entries at `ship:pre`: the
  `blocking_open == 0` check and the `diverged == 0` check, both `when: "beads.ship_gate"`,
  `blocking: true`, `onError: "skip"` — per PRD §5.3's exact shape.
- `capability.json`'s config schema gains the `beads.ship_gate` boolean (default `true`) if not
  already present — `.planning/config.json` currently has `beads.enabled: true` only; `bd` schema
  warning ("unknown config key(s): beads") observed this session means the config schema likely
  needs a re-sync alongside this phase's capability.json changes.

</code_context>

<specifics>

## Specific Ideas

No specific UI/UX references — this phase extends an existing markdown artifact (`BEADS.md`) and
adds two gate predicates plus a commit-trailer convention, not user-facing interaction beyond
what a ship-blocking console message already looks like.

</specifics>

<deferred>

## Deferred Ideas

None raised during this discussion — stayed within B9/B10 scope throughout.

### Reviewed Todos (not folded)

None — no pending todos matched this phase's scope.

</deferred>

---

*Phase: 3-Enforcement*
*Context gathered: 2026-08-15*
