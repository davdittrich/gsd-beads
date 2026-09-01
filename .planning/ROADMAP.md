# Roadmap: beads capability for gsd-core

## Overview

v1.4 replaces the machine-local task-content read patch with gsd-core's
native resolver seam. The sequence first establishes the lossless, fail-closed
resolver contract, then adds compatible task identity, and only then proves the
installed path before removing Patch 2 while preserving Patch 1.

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 (shipped 2026-08-16) —
  `.planning/milestones/v1.0-ROADMAP.md`
- ✅ **v1.1 Publish & Document** — Phases 5-12 (shipped 2026-08-18) —
  `.planning/milestones/v1.1-phases/`
- ✅ **v1.2 New Capability Plugins** — Phases 13-16 (shipped 2026-08-19) —
  `.planning/milestones/v1.2-ROADMAP.md`
- ✅ **v1.3 Config/Code Truth** — Phases 17-18 (shipped 2026-08-20) —
  `.planning/milestones/v1.3-ROADMAP.md`
- 📋 **v1.4 Native Task Content Resolution** — Phases 19-21 (planned)

## Phases

- [ ] **Phase 19: Native Resolver Contract and Failure Boundary** - Resolve
  live Beads task content through one lossless, fail-closed native adapter.
- [x] **Phase 20: Additive Identity Migration and Compatibility** - Add native (completed 2026-09-01)
  tracker identity without disturbing legacy identity or checkpoints.
- [ ] **Phase 21: Installed Cutover and Patch 2 Retirement** - Prove the
  installed native path before removing Patch 2 and re-verifying Patch 1.

## Phase Details

### Phase 19: Native Resolver Contract and Failure Boundary

**Goal:** Live Beads content resolves losslessly through the stdlib adapter.
**Depends on:** Phase 18
**Requirements:** RES-01, RES-02, RES-03
**Success Criteria** (what must be TRUE):

1. The capability's sole `beads` resolver is accepted by gsd-core and invokes
   the globally installed adapter through `python3 -c`,
   `GSD_HOME`/`Path.home()`, `os.execv`, and a separate tracker-id argument.
2. Resolving a valid Beads issue returns one schema-valid object that preserves
   `description`, `read_first`, `verify`, `acceptance_criteria`, and `done`
   without losing Markdown sections or scalar criteria.
3. Missing scripts, unavailable or failing `bd`, timeouts, ambiguous results,
   malformed JSON, invalid envelopes, and unusable content stop with precise
   diagnostics and never expose `PLAN.md` task prose as fallback content.

**Plans:** TBD

### Phase 20: Additive Identity Migration and Compatibility

**Goal:** Eligible tasks gain native identity without changing legacy consumers.
**Depends on:** Phase 19
**Requirements:** ID-01, ID-02
**Success Criteria** (what must be TRUE):

1. After synchronization, each eligible `auto` and `tracer` task contains both
   `tracker-id="beads:<id>"` and its existing `<beads-id>`.
2. Repeating synchronization leaves the plan byte-identical and creates no
   duplicate Beads issue.
3. Checkpoint tasks never gain `tracker-id` and preserve their existing
   human-decision and human-verification behavior.

**Plans:** 1/1 plans complete

### Phase 21: Installed Cutover and Patch 2 Retirement

**Goal:** Installed resolution is proven before Patch 2 removal; Patch 1 remains.
**Depends on:** Phase 20
**Requirements:** CUT-01, CUT-02
**Success Criteria** (what must be TRUE):

1. gsd-core's public `task resolve-content` command resolves a real plan task
   from live Beads through the globally installed capability.
2. Source, project-installed, and global-installed capability files are
   byte-identical, and isolated negative paths stop non-zero without fallback.
3. Only after those proofs pass, no Patch 2 marker, checker, installer, or
   documentation wiring remains, while Patch 1 is still installed and passes
   its independent verification.

**Plans:** 1 plan

Plans:
- [ ] 21-01-PLAN.md — Prove the active global resolver against live Beads, then retire Patch 2 transactionally while preserving Patch 1.

## Progress

**Execution Order:** Phase 19 → Phase 20 → Phase 21

| Phase | Plans Complete | Status | Completed |
|---|---:|---|---|
| 19. Native Resolver Contract and Failure Boundary | 0/TBD | Not started | - |
| 20. Additive Identity Migration and Compatibility | 1/1 | Complete    | 2026-09-01 |
| 21. Installed Cutover and Patch 2 Retirement | 0/TBD | Not started | - |
