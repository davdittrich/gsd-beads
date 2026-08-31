# Phase 20: Additive Identity Migration and Compatibility - Pattern Map

**Mapped:** 2026-08-31
**Files analyzed:** 3 (2 implementation/test targets, 1 fixture analog)
**Analogs found:** 3 / 3

## Phase Scope and Non-Negotiable Fences

- Keep `<beads-id>` as the only Beads authority. `tracker-id` is precisely
  `beads:<beads-id>`, never a lookup replacement, title deduplication input,
  or second tracker model. **Confidence: 100/100.**
- Extend the existing `parse_plan -> create_issues -> rewrite_plan` path. No
  new command, pipeline, cache, registry, serializer, retry, dependency, or
  gsd-core change. **Confidence: 98/100.**
- This phase owns source synchronization only. Installed/runtime cutover and
  Patch 2 retirement are Phase 21 work.
- Conflict (`tracker-id` wrong or duplicated) is an explicit hard halt before
  `bd create` and before `plan_path.write_text`; it is not B6 degradation.
  `bd` unavailable/failing retains the established B6 fail-open/no-write path.
- One Beads ticket is required for each generated `<task>`; tickets carry the
  plan's `beads_epic` binding. Do not replace tickets with Markdown tasks.

## File Classification

| New/Modified File | Role | Data Flow | Closest Tracked Analog | Match Quality |
|---|---|---|---|---|
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` | synchronizer/service | plan text -> live Beads resolution -> lexical file rewrite | same file: `parse_plan`, `resolve_issue`, `rewrite_plan`, `create_issues` | exact |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` | public-boundary test | mocked `bd` request-response plus file I/O | `TestIdentityBinding`, `TestIdempotency`, `TestStripTaskBodies` | exact |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/fixtures/plan-synced.md` | plan fixture | plan text / file I/O | same fixture | exact (extend only if a static fixture is smaller than inline test text) |

All named analogs are Git-tracked (`git ls-files --` verified 2026-08-31).

## Real Data Flow and Blast Radius

```text
PLAN.md text
  -> parse_plan()
       task record: name, name_end, beads_id, type, task-body fields
  -> create_issues()
       bd_available -> resolve_epic -> resolve_issue(each task)
       -> task_updates / task_ids / divergences
       -> rewrite_plan() -> plan_path.write_text()
       -> orphan sweep -> dependency edges
  -> later consumers of parse_plan()
       collect_all_task_files, resolve_prereq_last_task_id,
       resolve_milestone_epic, collect_epic_task_ids,
       find_completed_task_ids/close_wave, resolve_phase_epic,
       _resolve_task_ordinal_map, render_status_mapping,
       render_wave_status_block
```

`parse_plan` currently emits the shared task record at
`sync.py:335-363`; every task-record extension must be backward-compatible for
the ten non-sync callers listed above. They use legacy `beads_id`, names,
files, and task order; none may start treating `tracker_id` as an identity.
**Confidence: 97/100.**

### `parse_plan` -> `create_issues` -> `rewrite_plan`

**Source:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`

The current parser uses the entire matched task block and projects both
authoritative Beads identity and type:

```python
# sync.py:310-341
for m in TASK_RE.finditer(text):
    block = m.group(0)
    id_m = BEADS_ID_RE.search(block)
    type_m = TASK_TYPE_RE.search(block)
    ...
    {
        "name_end": m.start() + (name_m.end() if name_m else 0),
        "beads_id": id_m.group(1).strip() if id_m else None,
        "type": type_m.group(1).strip() if type_m else "",
    }
```

`resolve_issue` already protects the authoritative identity boundary:

```python
# sync.py:1346-1358
if task["beads_id"]:
    check = run_bd(["bd", "show", task["beads_id"], "--json"])
    if check.returncode != 0:
        return task["beads_id"], False, True
    return task["beads_id"], False, False
# only an absent beads_id reaches bd create
```

`create_issues` is the only `rewrite_plan` caller. Its existing mutation guard
and write are the sole legal persistence seam:

```python
# sync.py:1788-1800, 1824-1846
for i, task in enumerate(tasks, start=1):
    issue_id, created, divergent = resolve_issue(task, epic_id, ordinal_prefix, i)
    if created:
        task_updates.append((task["name_end"], issue_id))
    if divergent:
        divergences.append((task["name"], issue_id))
    task_ids.append(issue_id)

if task_updates or epic_created:
    new_text = rewrite_plan(text, epic_id, epic_created, task_updates)
    ...
    plan_path.write_text(new_text, encoding="utf-8")
```

`rewrite_plan` establishes the correct positional-write pattern: sorted,
descending insertions preserve every earlier source offset.

```python
# sync.py:1422-1439
for name_end_pos, issue_id in sorted(task_updates, key=lambda t: t[0], reverse=True):
    insertion = f"\n  <beads-id>{issue_id}</beads-id>"
    text = text[:name_end_pos] + insertion + text[name_end_pos:]
```

**Required adaptation:** add only enough opening-tag metadata to the task
record to determine (a) exact `auto`/`tracer`, (b) zero/one/multiple
`tracker-id` attributes, (c) canonical equality, and (d) the offset directly
after the `type` attribute. Represent native edits as a second local insertion
collection consumed by this same `rewrite_plan` invocation, sorted with every
other source-position insertion. Do not reconstruct a task block.

The existing exact-type fence is the implementation analog, not a broad
prefix match:

```python
# sync.py:1481-1487
task_type = type_m.group(1).strip() if type_m else None
if task_type not in ("auto", "tracer"):
    continue
```

## Pattern Assignments

### `scripts/sync.py` (synchronizer, plan text -> Beads -> file I/O)

**Copy from:** its `parse_plan`, `resolve_issue`, `rewrite_plan`, and
`create_issues` symbols above.

**Required state machine:**

| Condition | Beads action | Native action | Plan write |
|---|---|---|---|
| `type` exactly `auto`/`tracer`, safe live `<beads-id>`, no `tracker-id` | existing `bd show`; no create | queue ` tracker-id="beads:<id>"` immediately after `type` | one local splice |
| exact eligible type, one canonical attribute | existing `bd show`; no create | none | no native-induced write |
| stale `<beads-id>` | `bd show` gives current divergence behavior | none | no native-induced write |
| `bd` unavailable or mid-sync fails | existing B6 route | none | no write |
| wrong or duplicate native attribute | **no `bd create`**; halt before resolution/create as needed to preserve the fence | none | **no write** |
| `checkpoint:*`, missing, partial, unknown type | existing behavior unchanged | none | byte-identical block |
| no `<beads-id>` and eligible task | existing `bd create` produces the authoritative id | queue one native insertion from that returned id in the same rewrite | one combined write |

**Insertion shape:** it must be one opening-tag splice only:

```text
<task type="auto" other="kept">
         ^ insert ` tracker-id="beads:<legacy-id>"` here
```

Result: `<task type="auto" tracker-id="beads:<legacy-id>" other="kept">`.
All body bytes, unrelated attributes and their order remain untouched.

**Do not copy:** `strip_task_bodies` is a separate, destructive content-sync
policy. It is useful only as its exact-type and byte-preservation test analog;
do not couple native identity migration to stripping.

### `tests/test_sync.py` (public-boundary unittest, request-response + file I/O)

**Copy from:**

- `TestIdentityBinding.test_synced_plan_creates_nothing`, lines 1648-1664:
  existing `<beads-id>` resolves through `bd show` and filters mock calls where
  `argv[1] == "create"`.
- `TestIdempotency.test_second_sync_over_unchanged_plan_issues_no_create_or_update_calls`,
  lines 1686-1707, and `...leaves_plan_bytes_identical`, lines 1710-1720:
  invoke the same `plan_copy` twice and compare `read_bytes()`.
- `TestIdempotency.test_stale_beads_id_reports_divergence_without_recreating`,
  lines 1788-1813: a nonzero `bd show` must have zero `bd create` calls.
- `TestStripTaskBodies`, lines 910-978: compare exact blocks for
  `checkpoint:decision`, `checkpoint:human-verify`, and a missing `type` in a
  fixture containing eligible siblings. This is the closest coexistence
  preservation analogue.

**Mock and workspace pattern:**

```python
# test_sync.py:71-91, 133-149
mock_run.side_effect = _make_bd_side_effect()
plan_copy = _write_plan_workspace(Path(tmp), plan_text)
```

`_make_bd_side_effect` makes `bd list`/`bd show` succeed and gives `bd create`
a distinct id each invocation; it detects accidental creation when the test
filters call history. `_write_plan_workspace` makes a minimal
`.planning/phases/01-substrate/01-01-PLAN.md` tree. Use existing helpers, not
a Phase-20 fixture framework.

### `tests/fixtures/plan-synced.md` (fixture, plan text)

**Copy from:** lines 15-46: two pre-bound `<task type="auto">` blocks with
legacy ids. It is the smallest existing fixture for migrating already-bound
tasks without a `bd create` confound. It may be extended to add one `tracer`
or a focused inline plan string may be preferable if that avoids changing a
shared fixture's semantics.

## Native Runtime Compatibility Pattern

No gsd-core source is modified. Verify the emitted syntax against the installed
parser and public route:

```javascript
// /home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:127-157
const type = tagAttribute(openTag, 'type');
if (kind === TASK_KIND.CHECKPOINT) {
  return { ..., trackerId: null };
}
return { ..., trackerId: tagAttribute(openTag, 'tracker-id') };
```

```javascript
// /home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:121-134
const parsedPlan = parsePlanDocument(planContent, resolvedPlanPath);
const task = (parsedPlan.tasks ?? []).find((t) => t.trackerId === taskId);
...
result = resolveFn({ trackerId: task.trackerId, capabilities });
```

`splitTrackerId` keeps text after the first colon in the id
(`task-content-resolution.cjs:142-163`), so `beads:<beads-id>` is the required
projection. The test must prove parser recognition of the exact inserted
attribute, but must not claim installed-capability cutover; that is Phase 21.

## Scientific-Critical-Thinking Verification Design

**Claim:** a conditional local splice implements additive native identity
without changing legacy identity, human tasks, or unrelated plan bytes.
**Evidence grade:** Strong if all following one-factor arms pass; otherwise
`SPEC_FAILURE`. **Confidence: 96/100.**

| Arm | Only manipulated factor | Required observation | Confound controlled |
|---|---|---|---|
| Existing bound `auto` and `tracer` | missing native attribute | exactly one canonical insertion; legacy id retained; no `bd create`; gsd-core parses tracker id | distinguishes migration from new issue creation |
| Newly resolved eligible task | absent legacy and native attributes | one existing creation, then both `<beads-id>` and canonical attribute in the same written plan | distinguishes new-task path from backfill |
| Second sync of same file | repetition only | `read_bytes()` exactly equal; retained second-call history has no `create`/`update`; no write spy/call | prevents reset-mock/fresh-fixture false pass |
| Stale Beads id | `bd show` returns nonzero | divergence/no create/no plan write | prevents stale remediation masking a native write |
| Wrong native id | value differs from `beads:<id>` | hard halt/no create/no write | prevents destructive replacement being counted as migration |
| Duplicate native attribute | cardinality two | hard halt/no create/no write | parser-first-value behavior cannot mask ambiguity |
| checkpoint + missing + unknown types beside an eligible task | type only | each noneligible block byte-identical while eligible sibling changes | standalone preservation fixture cannot prove coexistence |

Use byte equality for lexical claims, a `write_text` spy (or equivalent
observable) for no-write claims, and the real `mock_run.call_args_list` without
clearing it between the critical first/second pass when asserting idempotence.
No skip, xfail, relaxed semantic-only comparison, or fresh-fixture second pass.

Alternative explanations rejected:

1. **Reserialization is safer:** invalid because semantic success cannot prove
   byte/order/body preservation.
2. **A post-sync migrator isolates risk:** invalid because it adds a second
   write/failure flow even though the authoritative Beads id is available here.
3. **Parser acceptance permits duplicate values:** invalid because D-04 makes
   duplicate identity semantically ambiguous regardless of parser behavior.

## Ponytail Appraisal

### Whole plan

1. **Need:** requirements ID-01/ID-02 require emitted native identity plus
   checkpoint exclusion; a no-op cannot satisfy them.
2. **Reuse:** current parser, live `resolve_issue`, positional writer, unit
   helpers, and Beads typed argv cover the complete path.
3. **Stdlib/native:** Python regex spans and string slicing are sufficient.
4. **Dependencies:** none; serializers/registries are prohibited and cannot
   satisfy lexical preservation economically.
5. **Minimum:** a tracer validates existing-bound migration and native parser
   recognition; an expansion task adds newly-created plus all negative,
   coexistence, and idempotence arms. Two plans/tasks are not required unless
   plan-check needs the tracer expansion split for independent verification.

### Mandatory per-task rationale for the planner

| Task | Why it exists | Minimum mechanism | Explicitly forbidden |
|---|---|---|---|
| Tracer: safely migrate existing bound eligible tasks | proves the shared production seam before expansion and establishes ID-01 | add opening-tag metadata and local insertion to existing parser/writer path; use bound auto + tracer tests and gsd-core parse assertion | serializer, new module/command, new issue, title lookup, gsd-core edit |
| Expansion: newly created, conflict, preservation, idempotence arms | distinguishes additive migration from unsafe repair or hidden rewrites; establishes ID-02 | table-driven/nearby unit tests in existing module using current helpers | retry/cache/registry, conflict overwrite, xfail/skip, weakened byte tests |

Every generated PLAN header must state:

```text
Mechanism: existing parse_plan/create_issues/rewrite_plan opening-tag splice
Forbidden: serializer, second migration pipeline, tracker abstraction, conflict repair
Audit: public sync calls; bd argv history; plan bytes/write observation; gsd-core parser recognition
```

## Required Verification and Execution Gates

- Before Wave 1: verify Phase 19's epic terminal state from live Beads, then
  run the exact capability suite from a scratch root outside repository
  ancestry (`TMPDIR=/dev/shm` per validated contract). The closed prerequisite
  task does not prove the epic is complete.
- Focused after each task:
  `TMPDIR=/dev/shm python3 -m unittest tests.test_sync.TestIdentityBinding -v`
  (extend this class or update `20-VALIDATION.md` consistently to name the
  actual focused class).
- Each wave and before verification:
  `TMPDIR=/dev/shm python3 -m unittest discover -s tests -t tests`, from
  `plugins/beads-lifecycle/.gsd/capabilities/beads`.
- Invoke the installed gsd-core parser/public resolver contract against a
  migrated plan; assert `trackerId == "beads:<beads-id>"` for auto/tracer and
  `trackerId is null` for checkpoints.
- Run GSD plan-check. A failing check is **Insufficient Research**, not an
  approval.

## No Analog Found

None. The production mutation, identity, no-create/no-write, stale-divergence,
and checkpoint byte-preservation patterns already exist in the tracked
capability.

## Metadata

**Analog search scope:** tracked Beads lifecycle synchronizer, its public
unittest suite/fixtures, and installed gsd-core native parser/resolver.
**Files scanned:** 5 source/fixture/runtime files plus phase inputs.
**Pattern extraction date:** 2026-08-31.
