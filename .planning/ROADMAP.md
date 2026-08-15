# Roadmap: beads capability for gsd-core

## Overview

Build `beads` as a gsd-core capability overlay that makes `bd` the task substrate for gsd's
lifecycle. Phase 1 lays the substrate — every plan task becomes a bound, dependency-ordered
beads issue that closes itself and degrades to a no-op when `bd` is unavailable. Phase 2 makes
that state visible to the planner and executor through recall artifacts and prompt contributions.
Phase 3 turns visibility into enforcement — a phase cannot ship with open or diverged issues
without a deliberate, recorded override. Phase 4 rounds out adoption: migrating existing todos,
an on-demand status view, and a milestone-level epic option for users who want one epic per
release instead of one per phase.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Substrate** - Plan tasks exist as bound, dependency-ordered beads issues that close themselves and fail open (completed 2026-08-15)
- [x] **Phase 2: Visibility** - The planner and executor operate with live beads state in context (completed 2026-08-15)
- [ ] **Phase 3: Enforcement** - A phase cannot ship with open or diverged issues without a deliberate override
- [ ] **Phase 4: Adoption** - Existing todos migrate in; the mapping is inspectable on demand

## Phase Details

### Phase 1: Substrate

**Goal**: Every gsd task exists as a beads issue, with correct status, without anyone running
`bd` by hand — and `bd` being absent, failing, or locked never blocks a phase.
**Depends on**: Nothing (first phase)
**Requirements**: B1, B2, B3, B4, B5, B6
**Success Criteria** (what must be TRUE):

  1. Planning an N-task phase creates exactly N beads issues parented to a phase epic (`bd list --parent <epic>` returns N matching titles)
  2. Task ordering declared in `PLAN.md` becomes enforced beads dependencies (`bd ready` excludes a blocked task until its blocker closes)
  3. Completing a task automatically closes exactly its own beads issue and no other
  4. Each task block carries an explicit `beads-id:` binding written on first sync; renaming a task title never creates a duplicate issue
  5. Re-running sync over an unchanged plan creates zero issues and modifies zero issues
  6. With `bd` off `PATH` (or failing, or locked), every gsd command still completes normally, one line explains the skip, no phase is blocked, and `BEADS.md` is absent rather than stale

**Plans**: 3/3 plans complete

Plans:

- [x] 01-01-PLAN.md — Tracer: capability manifest, beads-sync skill, and one plan task synced end-to-end into a real beads issue (B1, B4, B6)
- [x] 01-02-PLAN.md — Dependency edges from declared ordering, idempotent re-sync, orphan closure and divergence reporting (B2, B5)
- [x] 01-03-PLAN.md — Wave-scoped batch close, beads-status skill, and the install/consent checkpoint that activates the capability (B3)

### Phase 2: Visibility

**Goal**: The planner and executor see live beads issue state as part of their normal operation,
and the projection they read from is always freshly generated.
**Depends on**: Phase 1
**Requirements**: B7, B8, B11
**Success Criteria** (what must be TRUE):

  1. Before planning a phase, `BEADS-RECALL.md` exists and names any open issue touching that phase's scope
  2. The composed orchestrator prompt at `execute:wave:pre` includes the beads fragment and names the issues in the wave, verified by inspecting the prompt directly
  3. `BEADS.md` is regenerated from a real `bd` query at every step; a hand edit is overwritten at the next step rather than preserved

**Plans**: 2/2 plans executed

Plans:

- [x] 02-01-PLAN.md — Tracer: beads-recall skill/subcommand, two-technique file-scope matching, and the plan:pre planner-pointer contribution (B7)
- [x] 02-02-PLAN.md — BEADS.md full-overwrite regeneration at execute:wave:pre, the wave-status block for composed executor prompts, and re-install/re-consent (B8, B11)

### Phase 3: Enforcement

**Goal**: Beads state can block a ship — a phase with unfinished or diverged issues does not pass
unless the operator overrides deliberately, and the override is recorded.
**Depends on**: Phase 2
**Requirements**: B9, B10
**Success Criteria** (what must be TRUE):

  1. With one open blocking issue, `ship:pre` blocks and names it
  2. Setting `beads.ship_gate=false` allows the ship to proceed and records that the gate was overridden
  3. An issue closed in beads while its task is incomplete (or the reverse) sets `diverged>0`, blocks ship, and reports both sides without anything being auto-reconciled

**Plans**: 2/3 plans executed

Plans:

- [x] 03-01-PLAN.md — Real blocking_open/diverged in BEADS.md's frontmatter/table, regenerated at verify:post too (B9, B10)
- [x] 03-02-PLAN.md — ship:pre gates/config, ship_override audit-trail primitive, and the documented gap in gsd-core's ship.md dispatch (B9, B10)
- [ ] 03-03-PLAN.md — Machine-local patch to gsd-core's ship.md making the ship:pre gates/step dispatch live, plus a self-detecting reapply check (B9, B10)

### Phase 4: Adoption

**Goal**: Existing hand-tracked todos move into beads, and the plan-task ↔ issue mapping is
inspectable on demand — at whichever epic granularity the user prefers.
**Depends on**: Phase 1
**Requirements**: B12, B13, B14
**Success Criteria** (what must be TRUE):

  1. Running the one-shot migration moves `.planning/todos/pending/` entries into beads and reports what moved versus what could not be interpreted
  2. Running `beads-status` on demand prints the plan-task ↔ issue mapping, including orphans on both sides
  3. Setting `beads.epic_per=milestone` creates one epic per release instead of one per phase

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|-----------------|--------|-----------|
| 1. Substrate | 3/3 | Complete    | 2026-08-15 |
| 2. Visibility | 2/2 | Complete    | 2026-08-15 |
| 3. Enforcement | 2/3 | In Progress|  |
| 4. Adoption | 0/TBD | Not started | - |
