# Phase 20: Additive Identity Migration and Compatibility - Research

**Researched:** 2026-08-31
**Domain:** Backward-compatible, text-preserving native task-identity migration in the Beads plan synchronizer
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|---|---|---|
| ID-01 | Every eligible `auto` or `tracer` task gains `tracker-id="beads:<id>"` while retaining `<beads-id>`; repeat sync is byte-identical and creates no duplicate issue. | Existing parsing, live identity resolution, and the one rewrite seam are identified below; use a local opening-tag splice plus existing idempotency tests. |
| ID-02 | Checkpoints never gain `tracker-id` and retain their human-decision and human-verification behavior. | Existing parser classifies checkpoint tasks separately and assigns `trackerId: null`; existing fixture tests already compare checkpoint blocks byte-for-byte. |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Use CodeGraph or Serena before source exploration; use Serena for edits when it exposes a suitable operation.
- Use Beads as the durable task backend: one ticket for each eventual PLAN task; do not create parallel Markdown task tracking.
- Keep the change surgical, test-first, evidence-backed, and free of speculative abstractions or new dependencies.
- Every plan must compare at least two alternatives; rank the chosen mechanism by performance, line count/simplicity, ecosystem support, then maintenance cost.
- The plan must pass GSD plan-check; no skip, xfail, weakened assertion, or unverified environmental dismissal is acceptable.
- Run the capability suite from a temporary root outside repository ancestry. The live closed prerequisite records `/dev/shm` as the compliant scratch root; do not use repository-local temporary workspaces. [VERIFIED: `bd show gsd-beads-c5l --json`, 2026-08-31]

## Summary

The repository already has the needed lifecycle and mutation architecture. `create_issues` parses every task, resolves `<beads-id>` through live `bd show`, and invokes `rewrite_plan` only when it has plan changes. The legacy identity is explicitly authoritative: the implementation says it creates only when `<beads-id>` is absent and reports a stale id without recreation. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1346-1380`, quoted: `"<beads-id> is the identity; only create when it is absent"`]

Phase 20 should extend that same path, not add a migration command, cache, registry, XML serializer, or tracker abstraction. Parse only the opening tag metadata needed to decide eligibility and preserve every other byte; after a successful legacy-id resolution, splice ` tracker-id="beads:<id>"` immediately after the existing `type` attribute. A canonical task contributes no update, so the existing no-write branch preserves byte identity. Python’s official `Match.start()`/`Match.end()` API supplies the exact source span needed for such a splice. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1422-1439`, quoted: `"Insertions happen in descending position order first so earlier offsets in text stay valid"`] [CITED: https://docs.python.org/3/library/re.html]

**Primary recommendation:** Add one narrowly scoped native-identity update list to the existing `parse_plan → create_issues → rewrite_plan` path, with opening-tag conflict preflight and one-factor public-boundary tests; do not create a second migration pipeline. **Confidence: 97/100.**

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| Determine whether a task is eligible | API / Backend (local synchronizer) | Storage / Beads | `sync.py` owns task parsing and the live `bd show` identity check. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:300-365,1346-1380`] |
| Persist additive native identity | API / Backend (local synchronizer) | Static plan document | `rewrite_plan` is the existing text-mutation seam. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1422-1439`] |
| Resolve native task content | gsd-core runtime | API / Backend adapter | gsd-core reads the attribute verbatim and routes its prefix to a resolver; this phase must not change that runtime. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:118-157`; VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs:142-163`] |
| Preserve human checkpoints | gsd-core parser | Plan document | A checkpoint has `trackerId: null`; it must remain outside migration. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:127-146`, quoted: `"trackerId: null"`] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---|---:|---|---|
| Python `re` and string slicing | Python 3.14.7 | Locate the exact opening-tag insertion boundary and splice only that span. | Already used by `sync.py`; no package or serializer is needed. [VERIFIED: `python3 --version`, 2026-08-31; VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:26-55`] |
| Existing `sync.py` text model | repository source | Parse, live-resolve, and rewrite the plan. | It is the current production seam and preserves legacy Beads behavior. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:300-365,1736-1846`] |
| Python `unittest` + `mock` | existing test suite | One-factor no-write/no-create and lexical-preservation assertions. | Existing test module uses these exact tools. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1686-1813`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---|---:|---|---|
| gsd-core plan parser | installed GSD Core 1.12.0 | Prove the emitted attribute is recognized as `trackerId`. | Compatibility assertion only; do not modify gsd-core in this phase. [VERIFIED: `node .../gsd-tools.cjs runtime-identity --raw`, 2026-08-31; VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:148-157`] |
| Beads CLI | 1.2.2 | Existing authoritative legacy-id resolution. | Use only through the existing typed `run_bd` seam. [VERIFIED: `bd --version`, 2026-08-31; VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:237-253`] |

**Installation:** None. This phase adds no package, SDK, parser, or runtime dependency. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1-10`, quoted: `"stdlib-only"`]

## Package Legitimacy Audit

Not applicable: no external package is installed or recommended. The approved solution reuses Python standard library functionality and repository code. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1-10`]

## Alternatives Considered

| Rank | Mechanism | Performance | Simplicity / LOC | Ecosystem support | Maintenance | Decision |
|---:|---|---|---|---|---|---|
| 1 | Add opening-tag positions to `parse_plan`; feed native updates to existing `rewrite_plan`; splice in reverse offset order. | One linear parse and O(k) splices; no whole-document reconstruction. | Small extension of two existing functions. | Uses installed Python and gsd-core’s existing attribute parser. | One mutation seam. | **Choose.** [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:300-365,1422-1439`; CITED: https://docs.python.org/3/library/re.html] |
| 2 | Parse/reserialize XML or HTML. | Extra parse and render work. | Larger dependency or custom grammar; cannot guarantee attribute order/body whitespace byte preservation. | General-purpose parsers exist, but the plan grammar is not a schema migration target. | A second representation becomes a compatibility surface. | Reject: violates D-05 and Ponytail rungs 2–5. **Confidence: 96/100.** |
| 3 | Separate `migrate-tracker-ids` command or post-sync pass. | A second traversal and write decision. | Extra CLI, state flow, and failure boundary. | No existing use requires it. | Duplicates the existing resolver/write flow. | Reject: violates the explicit no-second-pipeline constraint. **Confidence: 99/100.** |
| 4 | Generic multi-tracker registry / mapping abstraction. | Indirect lookup for one deterministic prefix. | More classes/configuration than the one `beads:` projection needs. | No present second tracker. | Creates unsupported ownership and migration obligations. | Reject: YAGNI. **Confidence: 99/100.** |

## Ponytail Appraisal — Whole Plan and Task Justification

### Whole-plan ladder

1. **Need:** ID-01 and ID-02 require a native identity and checkpoint exclusion; no deletion or no-op satisfies them. **Confidence: 100/100.**
2. **Already in repository:** `parse_plan`, `resolve_issue`, and `rewrite_plan` already own exactly the parse, live-id, and mutation boundaries. **Confidence: 98/100.** [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:300-365,1346-1439`]
3. **Stdlib/native:** Python regex match spans and slicing implement the lexical splice; no XML library is justified. **Confidence: 96/100.** [CITED: https://docs.python.org/3/library/re.html]
4. **Dependency:** none; adding one violates locked scope. **Confidence: 100/100.**
5. **Minimum plan:** one tracer task that establishes valid existing-id migration at the public sync seam, then one expansion task that covers newly-created identity and all negative/preservation arms. No new module or command. **Confidence: 94/100.**

### Required planner task rationale

| Proposed task | Why it exists | Why it is the minimum | Forbidden expansion |
|---|---|---|---|
| Tracer: canonical existing Beads-bound `auto`/`tracer` task gains the attribute; parser recognizes it. | Establishes ID-01 through the real production flow without creating a new issue. | Reuses the shared mutation seam and proves the legacy id remains. | Serializer, separate migrator, manifest/runtime cutover, Patch 2 work. |
| Expansion: newly resolved task plus stale/malformed/conflicting/duplicate/checkpoint/unknown/idempotence arms. | Distinguishes safe migration from unsafe competing identity and prevents regression. | Table-driven tests in existing `test_sync.py`; one factor differs per arm. | Retry/cache, title matching, auto-repair, xfail/skip, relaxed byte assertions. |

**Planner gate:** Every `<task>` and the plan summary must state its Ponytail rung outcome using the table above, and must retain the explicit **Mechanism**, **Forbidden**, and **Audit** PLAN header required by project instructions.

## Architecture Patterns

### System Architecture Diagram

```mermaid
flowchart LR
    P[PLAN.md task opening tag + body] --> A[parse_plan: type, beads-id, opening-tag span]
    A --> E{exact auto or tracer?}
    E -- no --> K[Preserve task bytes]
    E -- yes --> C{zero or canonical single tracker-id?}
    C -- conflict/duplicate --> H[Halt: no plan write, no bd create]
    C -- acceptable --> B[resolve_issue using legacy beads-id]
    B --> S{legacy id live and safe?}
    S -- no --> F[B6/D-03 degradation: no native write]
    S -- yes --> R[rewrite_plan: local attribute splice]
    R --> N[tracker-id="beads:<beads-id>"]
    N --> G[gsd-core parsePlanDocument reads trackerId]
```

### Recommended Project Structure

```text
plugins/beads-lifecycle/.gsd/capabilities/beads/
├── scripts/sync.py       # extend existing parsing + single rewrite seam
└── test_sync.py          # extend existing public sync regression suite
```

### Pattern 1: Opening-tag-only mutation

**What:** Keep `TASK_RE` task block discovery, but record the end offset of the `type` attribute in its opening tag and splice the single native attribute at that offset.

**When to use:** Only after an exact eligible type, exactly one or zero native attribute, a safe verified legacy id, and successful `bd` resolution.

**Evidence:** The current parser already returns task-local positions (`"name_end"`) and the current writer applies insertions in descending position order. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:335-365,1422-1439`, quoted: `"name_end"` and `"sorted(task_updates, key=lambda t: t[0], reverse=True)"`]

**Implementation shape (not a new abstraction):**

```python
# Extend the existing task record with an opening-tag attribute-end offset.
if task["type"] in ("auto", "tracer") and verified_beads_id:
    # Insert only if no tracker-id exists; exact canonical is a no-op.
    text = text[:type_end] + f' tracker-id="beads:{beads_id}"' + text[type_end:]
```

`"auto"` and `"tracer"` are the repository’s exact migration types; every other type must take the no-op branch. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1462-1502`, quoted: `"if task_type not in (\"auto\", \"tracer\"): continue"`]

### Pattern 2: Fail closed for competing native identity; fail open only at the established Beads boundary

**What:** Preflight the opening-tag attributes before any `bd create`; a duplicate or noncanonical `tracker-id` is a local semantic conflict and returns without a plan write. Preserve B6 only for unavailable/failing `bd`.

**Why:** Replacing a conflicting native id would conflate a Beads migration with an unrelated tracker binding. Conversely, `bd_available()` already defines the project’s B6 no-op boundary. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:243-253`, quoted: `"Absent, non-zero exit, or timeout all take the same 'unavailable' path"`]

### Anti-Patterns to Avoid

- **Reserializing a task:** changes lexical representation unrelated to the identity feature and fails D-05.
- **Creating a new Beads issue when `<beads-id>` is stale:** `resolve_issue` explicitly reports divergence rather than recreating. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1346-1358`]
- **Treating `checkpoint:*` as an auto task:** it would change human-task behavior and contradict the native parser’s `trackerId: null`. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:127-146`]
- **Normalizing unknown/missing type:** unknown is a preservation case, not a compatibility opportunity. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1467-1470`]

## Don’t Hand-Roll

| Problem | Don’t Build | Use Instead | Why |
|---|---|---|---|
| XML/HTML transformation | A DOM or serializer migration | Existing regex + string offset splice | The contract requires byte preservation, including unrelated attribute order and body content. |
| Migration orchestration | New command, queue, cache, retry, or registry | Existing `create_issues` and `rewrite_plan` | One authoritative flow already knows live identity and whether a write is needed. |
| Duplicate identity resolution | Title matching or fallback issue creation | Existing `<beads-id>` + `bd show` resolution | Legacy identity binding is explicit and stale ids must not be healed. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1346-1358`] |

**Key insight:** The minimal safe implementation is an additive projection at the existing authoritative identity seam—not a second identity system.

## Scientific-Critical-Thinking Appraisal

### 1. Argument map

**Claim:** A local, conditional opening-tag splice is sufficient to add native identity without changing legacy consumers or checkpoint semantics. **Confidence: 96/100.**

Premises:

- Legacy `<beads-id>` is already the only lookup identity used by `resolve_issue`. **Confidence: 98/100.** [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1346-1358`]
- gsd-core reads `tracker-id` from the opening tag for non-checkpoints. **Confidence: 99/100.** [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:118-157`]
- Existing sync does not write an unchanged plan when no `task_updates`/epic update exists. **Confidence: 97/100.** [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1822-1846`]
- Existing tests prove byte equality and zero `bd create`/`update` calls for a second unchanged sync. **Confidence: 99/100.** [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1691-1720`]

### 2. Evidentiary inventory

| Premise | Evidence type | Quality | Limitation |
|---|---|---|---|
| Native attribute consumption | Current installed gsd-core source | Direct empirical/source evidence | It proves parser recognition, not Phase 21 installed-cutover UAT. |
| Legacy id and stale behavior | Current repository production source + unit test | Direct empirical/source evidence | Unit tests use mocked `bd`; retain real capability suite gate. |
| Lexical splice feasibility | Existing positional writer + Python official API | Direct source + primary documentation | Correctness still depends on all conflict/attribute-count arms. |

### 3. Logic audit

The argument is valid only if a migration is conditioned on successful legacy-id resolution and if the mutation records a source position inside the opening tag. A whole-block replacement would not prove D-05 even when semantic parser output is correct. The plan must assert raw bytes, not merely parsed task fields. **Confidence: 98/100.**

### 4. Bias and confound audit

| Threat | How it could create a false pass | Required control |
|---|---|---|
| Compatibility confound | A parser round-trip makes semantic tests pass while whitespace/order/body bytes change. | Compare original and transformed task-block bytes; assert the one expected attribute insertion only. |
| Idempotence confound | Resetting mocks or rewriting a fresh fixture hides a second `bd create`/write. | Call `create_issues` twice on the same path; retain the second call history and compare `read_bytes()`. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1691-1720`] |
| Checkpoint exclusion confound | Testing a checkpoint in a separate fixture does not prove coexistence preservation during an eligible mutation. | Put checkpoint/unknown blocks beside a changed eligible block and compare their exact blocks before/after. |
| Stale-id confound | Mocking stale state after the writer has already run proves only a message. | Make `bd show` fail in an otherwise valid bound-task control and assert no plan write/no `bd create`. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1788-1813`] |
| Competing-native-id confound | Replacing the value passes Beads resolution while destroying another tracker binding. | One wrong-value and one duplicate-value arm; both halt before mutation and creation. |

### 5. Alternative explanations

1. **A generic XML parser is safer.** Rejected: it can validate a structure but cannot satisfy the stronger lexical-byte contract without additional bespoke preservation machinery. **Confidence: 94/100.**
2. **A separate post-sync migrator isolates risk.** Rejected: it creates an additional failure and write boundary, while the existing sync already knows whether the legacy id is live. **Confidence: 98/100.**
3. **No attribute-count validation is necessary because the parser takes one value.** Rejected: D-04 defines duplicates as an ambiguous identity, so parser acceptance cannot substitute for migration safety. **Confidence: 100/100.**

### 6. Integrated appraisal

**Grade: Strong — Accept with conditions.** Implement only the positional extension and tests described here. The plan must hard-gate execution on Phase 19 completion plus a green capability suite, keep all comparison arms one-factor, and refuse conflict/no-write tests that conflate an unrelated rewrite with native identity. **Confidence: 96/100.**

## Common Pitfalls

### Pitfall 1: One old writer condition prevents backfill

**What goes wrong:** The current writer runs only for `task_updates` or a new epic, but an already Beads-bound plan has neither; existing tasks never gain `tracker-id`. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1825-1846`]

**Avoidance:** Include native-identity updates in the existing write predicate, while canonical tasks add none.

### Pitfall 2: Inserting a child `<tracker-id>` element

**What goes wrong:** gsd-core reads the opening-tag attribute, not a child element. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:148-157`, quoted: `"trackerId: tagAttribute(openTag, 'tracker-id')"`]

**Avoidance:** Insert only the attribute after `type`.

### Pitfall 3: Treating a checkpoint as a migration candidate

**What goes wrong:** The native parser deliberately returns `trackerId: null` for checkpoints, and existing body logic distinguishes `checkpoint:*`. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:127-146`; VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1360-1370`]

**Avoidance:** Eligibility is exact `auto`/`tracer`, never prefix/non-empty type matching.

### Pitfall 4: Incorrectly treating Phase 19 as complete

**What goes wrong:** The resolver task and its temporary-workspace prerequisite are closed live, but the Phase 19 epic remains open. Planning Phase 20 is safe; execution must not infer dependency completion from the closed task alone. [VERIFIED: `bd show gsd-beads-0y4.1 --json`, 2026-08-31; VERIFIED: `bd show gsd-beads-c5l --json`, 2026-08-31]

**Avoidance:** Add a Wave-0 execution precondition that checks the Phase 19 epic’s final authoritative state and runs the exact capability suite using a scratch root outside repository ancestry.

## Code Examples

### Native parser compatibility assertion

```javascript
// Installed gsd-core parser contract, not production code to duplicate.
const task = parsePlanDocument(planText, planPath).tasks[0];
assert.equal(task.trackerId, 'beads:fixture-1');
```

The parser returns the attribute exactly through `tagAttribute(openTag, 'tracker-id')`; use this as a narrow compatibility test, not as a Phase 21 cutover proof. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:148-157`]

### Second-pass idempotence control

```python
sync.create_issues(str(plan_copy))
before = plan_copy.read_bytes()
sync.create_issues(str(plan_copy))
after = plan_copy.read_bytes()
assert before == after
```

This exact existing control prevents a semantic-only idempotence claim. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1710-1720`]

## State of the Art

| Old approach | Current approach | When changed | Impact |
|---|---|---|---|
| Machine-local executor patch reads Beads task prose | gsd-core native `tracker-id` parser/resolver seam | Installed gsd-core 1.12.0 observed 2026-08-31 | Phase 20 supplies only the additive identity; Phase 21 proves installed cutover and retires Patch 2. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92-157`; VERIFIED: `.planning/ROADMAP.md:52-83`] |

**Deprecated/outdated:** Do not expand the existing Patch 2 path in this phase; its retirement is explicitly Phase 21 scope. [VERIFIED: `.planning/phases/20-additive-identity-migration-and-compatibility/20-CONTEXT.md`, `Phase Boundary`]

## Resolved Compatibility Conclusions

### Task-record compatibility: safe to extend

All ten live production callers of `parse_plan` and its one direct unit-test call use only named dictionary keys; none serializes a task dictionary, iterates `task.values()`/`task.items()`, or compares a task key set. The callers are: `collect_all_task_files` (`beads_id`, `files`); `resolve_prereq_last_task_id` (`beads_id`); `resolve_milestone_epic` (frontmatter only); `collect_epic_task_ids` (`beads_id`); `find_completed_task_ids` (`beads_id`); `create_issues` (named fields including `name_end`); `resolve_phase_epic` (frontmatter only); `_resolve_task_ordinal_map` (`beads_id`); `render_status_mapping` (`beads_id`, `name`); and `render_wave_status_block` (`beads_id`). The direct test consumes only `beads_id`. [VERIFIED: Serena references for `parse_plan`, 2026-08-31; VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:796-836,1234-1245,1399-1419,1578-1597,1775-1813,2073-2107,2288-2314,2358-2375`; VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1550-1554`]

**Conclusion:** Extend the internal task record with only the opening-tag/type-attribute end offset and native-attribute count/value needed by the existing write seam. The current caller set proves this is backward-compatible. **Confidence: 99/100.**

**Bounded fallback if that evidence changes before implementation:** Do not add a task-dictionary key. In `create_issues`, make one local `TASK_RE.finditer(text)` pass over the already-read original document to calculate `(type_attribute_end, beads_id)` native insertions, then feed those offsets into `rewrite_plan`’s existing descending-offset writer. This is a local fallback within the same write seam, not a command, cache, or second migration pipeline. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:26-55,1422-1439`, quoted: `"sorted(task_updates, key=lambda t: t[0], reverse=True)`"]

### Portable native-parser compatibility probe: active GSD executable only

`GSD_HOME` is the documented global **capability overlay** root (the global overlay expands to the GSD_HOME variable followed by `.gsd/capabilities/<id>`), not a gsd-core runtime root; do not derive the parser from it. [VERIFIED: active GSD Core capability-loader source, lines 9-13 and 244-256, quoted: `"global:  $GSD_HOME/.gsd/capabilities/<id>/capability.json"`]

Use the documented active `gsd_run` launcher instead: it resolves its real path and executes its sibling `gsd-tools.cjs`. Therefore a portable test resolves `command -v gsd_run`, canonicalizes it with `readlink -f`, and derives the sibling parser module under that executable’s bin directory. This avoids hard-coding a Codex configuration home and follows the runtime’s active installation; GSD’s current Codex active-home descriptor likewise names `CODEX_HOME` with a default Codex-home fallback. [VERIFIED: active GSD Core gsd_run source, lines 1-20, quoted: `"It resolves its own real location (following symlinks) and delegates to gsd-tools.cjs."`; VERIFIED: active GSD Core capability-registry source, lines 1068-1084]

The probe must hard-fail (nonzero) if `gsd_run` is absent, the derived parser is missing/unreadable, `require()` fails, or its export lacks callable `parsePlanDocument`; it must never skip, use a hard-coded alternate home, or silently omit the native-parser assertion. This active-path method was run successfully in this session and returned `active-parser-ok` for `tracker-id="beads:fixture-1"`. [VERIFIED: active `gsd_run` probe and active parser source read, 2026-08-31]

## Assumptions Log

None for task-record compatibility or native-parser portability; both former assumptions are resolved by fresh structural and active-runtime evidence above.

## Open Questions

None that block Phase 20 planning. The Phase 19 epic’s open state remains an existing Wave-0 execution gate, not an unresolved implementation question. [VERIFIED: `bd show gsd-beads-0y4.1 --json`; VERIFIED: `bd show gsd-beads-c5l --json`, 2026-08-31]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---:|---|---|
| Python | synchronizer and unit suite | ✓ | 3.14.7 | — [VERIFIED: `python3 --version`, 2026-08-31] |
| Beads CLI | identity resolution | ✓ | 1.2.2 | B6 no-op only for runtime unavailability; no migration fallback. [VERIFIED: `bd --version`, 2026-08-31] |
| Node + installed gsd-core | parser compatibility assertion | ✓ | Node 26.8.1; gsd-core 1.12.0 | Omit the installed-parser assertion only if the planner replaces it with an equally public native-contract proof. [VERIFIED: `node --version`; VERIFIED: `node .../gsd-tools.cjs runtime-identity --raw`, 2026-08-31] |
| Compliant scratch root | capability tests | ✓ | `/dev/shm` proven by closed prerequisite | Do not use `/tmp` or project ancestry. [VERIFIED: `bd show gsd-beads-c5l --json`, 2026-08-31] |

## Validation Architecture

### Test Framework

| Property | Value |
|---|---|
| Framework | Python `unittest` with `mock` [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1686-1813`] |
| Config file | none — test discovery is at the capability root. [ASSUMED] |
| Quick run command | `TMPDIR=/dev/shm python3 -m unittest tests.test_sync.TestIdempotency -v` from `plugins/beads-lifecycle/.gsd/capabilities/beads` |
| Full suite command | `TMPDIR=/dev/shm python3 -m unittest discover -s tests -t tests` from `plugins/beads-lifecycle/.gsd/capabilities/beads` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| ID-01 | Existing valid id gains one canonical attribute with no new `bd create`; new valid task gains both identities; second pass is raw-byte identical. | unit/public-sync integration | focused Phase 20 class, then full discovery | ❌ Wave 0 extension to the existing synchronizer test module |
| ID-02 | `checkpoint:decision`, `checkpoint:human-verify`, missing type, and unknown type blocks are exact when a neighboring eligible block changes. | unit preservation | focused Phase 20 class, then full discovery | ❌ Wave 0 extension to the existing synchronizer test module |

### Required one-factor matrix

| Arm | Control differs only in | Required assertion |
|---|---|---|
| Existing valid eligible | Add pre-existing live `<beads-id>` | one exact inserted attribute; no `bd create`; legacy element remains. |
| Newly resolved eligible | Remove legacy identity from control | one `bd create`, then `<beads-id>` and canonical attribute are written together. |
| Canonical second pass | Repeat exact same path | no plan write, no `bd create`, `read_bytes()` equal. |
| Stale legacy id | `bd show` nonzero | no native insertion, no plan write, no replacement create. |
| Malformed legacy id | Only id shape changes | no native insertion/write/create. |
| Wrong/duplicate native id | Only native attribute value/count changes | halt before write/create; do not overwrite. |
| Checkpoint/unknown coexistence | Neighboring eligible block changes | each excluded block is byte-identical. |
| Native parser | Parse transformed fixture | expected exact `trackerId` value. |

### Sampling Rate

- **Per task commit:** focused Phase 20 class with `TMPDIR=/dev/shm`.
- **Per wave merge:** `TMPDIR=/dev/shm python3 -m unittest discover -s tests -t tests` from the capability root.
- **Phase gate:** Full suite green and all raw-byte/no-create/no-write assertions green before `$gsd-verify-work`.

### Wave 0 Gaps

- [ ] Add a focused `TestNativeTrackerIdentityMigration` (or equivalent) in the existing test module before production edits.
- [ ] Verify exact Phase 19 epic completion and suite status immediately before Phase 20 execution.
- [ ] Use the closed prerequisite’s outside-ancestry scratch mechanism; do not invent another temporary-workspace setup.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | no | No authentication boundary changes. |
| V3 Session Management | no | No session state exists in this flow. |
| V4 Access Control | yes | Preserve explicit Beads identity; never replace a competing tracker binding. |
| V5 Input Validation | yes | Count `tracker-id` only in the opening tag; accept exact eligible types; require safe/live legacy id before derivation. |
| V6 Cryptography | no | No cryptographic material or protocol changes. |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Plan-authored value reaches `bd` argv | Tampering | Retain typed argv (`subprocess.run` with shell disabled) and safe-id validation; no shell command construction. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1-10,107-113,237-240`] |
| Competing native tracker identity overwritten | Tampering | Duplicate/noncanonical attribute is a hard no-write conflict. |
| Stale legacy id recreated as a different issue | Integrity | Report divergence, never title-match or recreate. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1346-1358`] |
| Checkpoint state reclassified as automated | Elevation of Privilege | Exact `auto`/`tracer` allow-list and byte-preservation tests. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1462-1502`] |

## Sources

### Primary (HIGH confidence)

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1-10,26-55,300-365,1346-1439,1736-1846` — current parser, Beads resolution, and plan mutation contract.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1686-1813,910-1012` — idempotence, stale-id, and checkpoint/unknown byte-preservation controls.
- `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:118-157` and `task-content-resolution.cjs:142-163` — installed native attribute parsing and prefix splitting.
- `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92-157` — public resolver route matches task by exact `tracker-id`.
- Live Beads: `bd show gsd-beads-c5l --json`, `bd show gsd-beads-0y4.1 --json`, 2026-08-31.

### Secondary (MEDIUM confidence)

- [Python 3.14 `re` documentation](https://docs.python.org/3/library/re.html) — match source boundaries and same-type string replacement; fetched 2026-08-31.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — existing source and installed runtime prove no dependency is needed.
- Architecture: HIGH — direct current-source flow and call-path evidence identify one mutation seam.
- Pitfalls: HIGH — direct stale/idempotence/checkpoint tests already encode the relevant regressions.

**Research date:** 2026-08-31
**Valid until:** Recheck immediately before Phase 20 execution, because Phase 19’s epic remains open and current capability source may change.
