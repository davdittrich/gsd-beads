# Requirements: beads capability for gsd-core

**Defined:** 2026-08-15
**Core Value:** gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero
duplicated task-state bookkeeping survives in `.planning/`.

## v1 Requirements

Requirements for initial release. Each maps to exactly one roadmap phase.

### Substrate (F1 — task status lives in beads)

- [ ] **B1**: One beads issue per `PLAN.md` task, parented to a phase epic. After planning an
  N-task phase, `bd list --parent <epic>` returns exactly N issues whose titles match the plan's
  tasks.
- [ ] **B2**: Plan task ordering becomes beads dependencies. Task 3 depending on task 1 shows
  task 1 as a blocker in `bd show`; `bd ready` excludes task 3 until task 1 closes.
- [ ] **B3**: Task completion closes its issue automatically. After a wave completes task 2, that
  issue is `closed` and no other issue changed.
- [ ] **B4**: Identity is bound explicitly, never by title matching. Each plan task block carries
  a `beads-id:` written on first sync; re-sync resolves by that id. Renaming a task title does
  not create a second issue.
- [ ] **B5**: Sync is idempotent. Two syncs over an unchanged plan create zero issues and modify
  zero issues, proven by a `bd list --json` diff.
- [ ] **B6**: `bd` absent, failing or locked degrades to a no-op with one visible notice. With
  `bd` off `PATH`, every gsd command completes normally, one line explains the skip, no phase is
  blocked, and `BEADS.md` is absent rather than stale.

### Visibility (F2, F4 — planner/executor see live beads state)

- [ ] **B7**: The planner sees open issues before planning. With an open issue touching a file in
  the phase's scope, `BEADS-RECALL.md` exists before the planner runs and names that issue.
- [ ] **B8**: The executor's prompt carries live issue state. The `execute:wave:pre` fragment is
  present in the composed orchestrator prompt and names the issues in the wave — verified by
  inspecting the prompt, not by inferring from behaviour.
- [ ] **B11**: `BEADS.md` is regenerated, never hand-edited. A hand edit is overwritten at the
  next step; frontmatter always reflects a real `bd` query at generation time.

### Enforcement (F3 — beads state can block a ship)

- [ ] **B9**: A phase with unfinished blocking issues cannot ship. With one open blocking issue,
  `ship:pre` blocks and names it. `beads.ship_gate=false` allows the ship and records that it was
  overridden.
- [ ] **B10**: Divergence blocks and is reported; it is never auto-reconciled. An issue closed in
  beads whose task is incomplete (or the reverse) sets `diverged>0`, blocks ship, and reports
  both sides. Nothing changes until the operator decides.

### Adoption

- [ ] **B12**: One-shot migration of existing `.planning/todos/pending/` entries into beads,
  reporting what moved and what could not be interpreted.
- [ ] **B13**: `beads-status` runnable on demand, printing the plan-task ↔ issue mapping
  including orphans on both sides.
- [ ] **B14**: Milestone-level epic option (`beads.epic_per=milestone`) for users who prefer one
  epic per release.

## v2 Requirements

None identified — all 14 requirements extracted from the PRD are in v1 scope.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Overriding first-party gsd-core behavior | N1 — overlay is additive only; first-party wins on any collision |
| Forking or patching gsd-core | N2 — overlay-only installation; raise upstream if a core change is ever needed |
| A second planning/gating pipeline | N3 — this capability tracks work state, it does not decide how work is planned |
| Executing command strings sourced from plan/ticket artifacts | N4 — `bd` invocations are built from typed values only; the artifact's author and the workflow's runner are different principals |
| Any dependency beyond `bd` + Python 3 stdlib | N5 |
| Syncing beads onward to GitHub Issues, Jira, or any other tracker | N6 — one tracker only |
| Deterministic plan-checker reviewer capability (PRD Appendix A) | Deferred, possibly never — benefit unmeasured; revisit only after `beads` ships and only if the LLM plan-checker is observed spending judgement on decidable properties, and only if 5+ such checks prove worth writing |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| B1 | Phase 1 | Pending |
| B2 | Phase 1 | Pending |
| B3 | Phase 1 | Pending |
| B4 | Phase 1 | Pending |
| B5 | Phase 1 | Pending |
| B6 | Phase 1 | Pending |
| B7 | Phase 2 | Pending |
| B8 | Phase 2 | Pending |
| B11 | Phase 2 | Pending |
| B9 | Phase 3 | Pending |
| B10 | Phase 3 | Pending |
| B12 | Phase 4 | Pending |
| B13 | Phase 4 | Pending |
| B14 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-08-15*
*Last updated: 2026-08-15 after initial roadmap creation*
