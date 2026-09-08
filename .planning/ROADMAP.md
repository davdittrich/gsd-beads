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

### Phase 22: Capability Projection Reconciliation

**Goal:** Installer updates reconcile every selected runtime skill projection with the one active global Beads capability generation without touching user-owned or unrelated capability content.
**Requirements:** GitHub issue #9
**Depends on:** Phase 21
**Success Criteria** (what must be TRUE):

1. A legacy marker-owned stale projection is replaced through gsd-core's native
   installed-capability surface, and every selected command is accepted by the
   active CLI; retired `execute-plan` is absent.
2. Projection receipts are bound to the active global capability generation,
   serialized across runtimes, and repeated updates are byte-idempotent.
3. User-owned skills, non-GSD skills, genuinely installed other capabilities,
   and unrelated runtime state remain intact.
**Plans:** 1/1 plans complete
**Verification:** PASSED at `ed547388ecfc3fa8ce7d35cbed795337b02c4bb4`;
code review PASS, security SECURED (7/7 closed), goal verification 7/7.

Plans:

- [x] 22-01-PLAN.md

### Phase 23: Extend SOTA definition in sota-numerics and refactor plugin to comply

**Goal:** Extend the sota-numerics plugin's definition of SOTA beyond numerical correctness so it also instructs generated code to be internally and project consistent, unambiguous, complete, efficient, carry agent-facing prose that follows the writing-for-agents standard, and stay token-efficient when the generated code is executed; then refactor the plugin's own content to fully comply with that extended definition.
**Requirements**: none in REQUIREMENTS.md — traced to 23-CONTEXT.md decisions D-01..D-27, amended by A-01..A-04 (publish moved to Phase 24 by A-04)
**Depends on:** Phase 22
**Plans:** 4/4 plans executed

Plans:
**Wave 1**

- [x] 23-01-PLAN.md — Executor role slice: tracer on `quiet`, then `legible` and efficiency, echoed in the verifier and ship fragments and README (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 23-02-PLAN.md — Planner role slice: prune the checker restatement, define `with the grain` and plan completeness, echo in verifier and ship (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 23-03-PLAN.md — Manifests to 0.2.0 with rewritten descriptions, gate-script prose refactor, gate contract frozen (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 23-04-PLAN.md — NOTES.md prune-only and README claim tracing plus legible-standard prose pass (wave 4)

**Cross-cutting constraints:**

- The three existing suites pass unchanged after every task (D-20).
- The three existing suites pass unchanged (D-20).

### Phase 24: Remediate sota-numerics 0.2.0 release blockers and publish

**Goal:** Close every blocking finding raised by the four-lens review of the `feat/extended-sota-definition` branch, then publish 0.2.0. The gate stops passing documents that omit an Alternatives Considered section, its diagnostics stay token-bounded, every README and CHANGELOG claim resolves against the code it describes, the cross-repo marketplace description matches the plugin manifest, and the agent-facing prose is unambiguous and internally consistent. Publishing is the last wave of this phase: merging to main serves the new bytes to every installer, so the decision checkpoint that guards it is answered after the remediation waves verify, never before.
**Requirements**: none in REQUIREMENTS.md — traced to the review reports in this phase directory (REVIEW-CRITICAL-FINAL.md, REVIEW-PONYTAIL-FINAL.md, REVIEW-AGY-FINAL.md, REVIEW-PROSE-TOKENS.md) and to 24-CONTEXT.md decisions D-01..D-24
**Depends on:** Phase 23
**Plans:** 5/9 plans executed

Plans:

- [x] 24-01-PLAN.md — wave 1 — tracer: an indented-code-block section stops crediting a plan, frontmatter is masked, and the regression baseline is captured before any parser edit (D-02, D-05, D-06, D-18)
- [x] 24-02-PLAN.md — wave 1 — marketplace description in `gsd-beads` brought back into agreement with the branch manifest (D-12)
- [x] 24-03-PLAN.md — wave 2 — bullet indentation bounded to the CommonMark range, frontmatter phase parse made unambiguous, cumulative regression diff recorded (D-03, D-04, D-05)
- [x] 24-04-PLAN.md — wave 3 — diagnostics bounded: quoted spans elided, violations reported as path, line and reason, one remediation line per run (D-07, D-08)
- [x] 24-05-PLAN.md — wave 4 — gate and hook resolve their entry points from their own location, not the caller's working directory (D-13, D-14)
- [ ] 24-06-PLAN.md — wave 5 — counts nothing recomputes deleted, spelling settled by measurement, NOTES residual completed with the key that can stop the gate dispatching (D-09, D-11)
- [ ] 24-07-PLAN.md — wave 6 — whole-README claim trace: every behavioural claim paired with the code deciding it, every documented command run or recorded as unrun (D-10)
- [ ] 24-08-PLAN.md — wave 7 — every review thread and every internal finding given a disposition, with a ticket for each deferral, then the regression evidence re-established (D-15, D-16)
- [ ] 24-09-PLAN.md — wave 8 — blocking release decision, merge at re-proved preconditions, annotated tag, mirror restored from released bytes (D-19..D-24)
