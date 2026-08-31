# Phase 20: Additive Identity Migration and Compatibility - Context

**Gathered:** 2026-08-31
**Status:** Ready for planning

<domain>

## Phase Boundary

Add gsd-core native `tracker-id` identity to already-Beads-bound and newly
resolved eligible plan tasks without replacing `<beads-id>`, creating duplicate
issues, or changing checkpoint/human-task behavior. This phase depends on the
verified Phase 19 resolver contract; installed cutover and Patch 2 retirement
remain Phase 21 work.

</domain>

<decisions>

## Implementation Decisions

### Eligibility and authoritative identity

- **D-01:** The legacy `<beads-id>` remains the authoritative Beads identity.
  `tracker-id` is only its deterministic native projection:
  `beads:<beads-id>`.
- **D-02:** On every successful sync, migrate every existing or newly resolved
  task of exact type `auto` or `tracer`; do not limit migration to issues
  created during the current invocation. — **Reversibility:** costly — undoing
  it requires removing persisted native identities from already-synced plans.
- **D-03:** A task is ineligible when its legacy Beads identity is stale or bd
  is unavailable/failing. Preserve current plan bytes and the established B6
  fail-open degradation; never derive native identity from unverified state.

### Native-identity conflicts

- **D-04:** Add a missing `tracker-id` only from an existing safe Beads id. A
  present value that is not exactly `beads:<beads-id>`, or duplicate
  `tracker-id` attributes, is an ambiguous/competing identity: halt without
  writing rather than overwrite it. — **Reversibility:** costly — automatic
  replacement could destroy another tracker's published binding.

### Lexical compatibility and idempotence

- **D-05:** Write one `tracker-id` attribute immediately after `type` on the
  opening `<task>` tag. Make a local opening-tag insertion; do not reserialize
  a task, alter body content, reorder unrelated attributes, or add a child
  element.
- **D-06:** An already-canonical task is unchanged: repeat synchronization
  performs no plan write and no `bd create`; the resulting plan is
  byte-identical.

### Checkpoint and unknown-task preservation

- **D-07:** Every `checkpoint:*` task remains byte-identical, including
  `checkpoint:decision` and `checkpoint:human-verify`; their human-decision
  and human-verification behavior is not migrated.
- **D-08:** Missing, partial, and unknown task types are also non-eligible and
  byte-identical. Only exact `auto` and `tracer` types are eligible.

### Verification discipline

- **D-09:** Prove one factor per arm: migrate existing and newly resolved
  eligible tasks; prove a zero-write/zero-create byte-identical second pass;
  reject stale, malformed, conflicting, and duplicate native identities
  without a write; prove gsd-core recognizes the inserted native attribute;
  and prove checkpoint/unknown-type blocks remain exact. Do not use skips,
  xfails, or weakened assertions.

### the agent's Discretion

The user delegated private helper names, precise diagnostic text, fixture
names, and the smallest implementation that realizes D-01 through D-09 to
Ponytail, scientific-critical-thinking, Beads, and domain-modeling. The
planner may not introduce another migration pipeline, dependency, cache,
retry, or tracker abstraction, nor weaken conflict/no-write behavior.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and prior contract

- `.planning/PROJECT.md` — v1.4 scope, additive-only constraint, and Phase 21
  Patch 2 boundary.
- `.planning/REQUIREMENTS.md` — locked ID-01 and ID-02 requirements and
  exclusions.
- `.planning/ROADMAP.md` — Phase 20 success criteria and dependency order.
- `.planning/phases/19-native-resolver-contract-and-failure-boundary/19-CONTEXT.md`
  — Phase 19 resolver boundary that Phase 20 must not broaden.

### Existing Beads synchronization

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` —
  `parse_plan`, `resolve_issue`, `rewrite_plan`, typed task semantics, and
  existing `<beads-id>` rewrite seam.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` —
  current sync fixtures, real-bd workspace patterns, task-body and checkpoint
  byte-preservation assertions.

### Native gsd-core contract

- `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs` — native parser reads
  `tracker-id` verbatim from the opening task tag.
- `/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs` — prefix/id
  split and resolver selection semantics.
- `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs` — public
  `task resolve-content` matches a task by exact native `tracker-id`.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets

- `parse_plan`: supplies the task type, `<beads-id>`, and source positions for
  the shared sync path.
- `resolve_issue`: preserves explicit legacy identity and reports stale-id
  divergence without title matching or replacement.
- `rewrite_plan`: is the one existing plan-mutation seam; extend it rather
  than introduce a second migration pass.
- `TASK_RE` / `TASK_TYPE_RE`: existing task-block and type recognition
  boundaries.

### Established Patterns

- `<beads-id>` binds lifecycle status, dependency, and close-wave consumers;
  it is never removed.
- `auto`/`tracer` task bodies differ from `checkpoint:*` human-task bodies.
- bd calls use fixed typed argv; degraded bd behavior is visible and fail-open
  only where B6 already declares it.

### Integration Points

- The post-resolution `create_issues` flow can migrate both existing and
  newly-created task mappings in the same plan write.
- gsd-core's native parser and public resolver command consume the added
  opening-tag attribute; Phase 21 proves installed runtime cutover.

</code_context>

<specifics>

## Specific Ideas

- Ponytail: reuse the existing `rewrite_plan` path; no dependency, registry,
  or second migration pipeline. **Confidence: 96/100.**
- Scientific appraisal: silent replacement of a conflicting native identity
  confounds Beads migration with another tracker binding. A no-write conflict
  arm is the required discriminating test. **Confidence: 98/100.**
- Domain model: `beads-id` is the authoritative legacy identity; `tracker-id`
  is a deterministic projection for gsd-core native resolution, not a second
  source of truth. **Confidence: 98/100.**

</specifics>

<deferred>

## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 20-additive-identity-migration-and-compatibility*
*Context gathered: 2026-08-31*
