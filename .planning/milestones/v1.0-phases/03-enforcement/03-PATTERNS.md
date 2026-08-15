# Phase 3: Enforcement - Pattern Map

**Mapped:** 2026-08-15
**Files analyzed:** 4 (2 modified, 1 config-only, 1 test file extended)
**Analogs found:** 4 / 4 (all patterns reused from within the same module — no cross-codebase search needed; CONTEXT.md's `code_context` section already names every reuse target)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `.gsd/capabilities/beads/scripts/sync.py` (extend `regenerate_beads_md`, add `blocking_open`/`diverged` computation, add override-audit helpers) | service (data-projection + write) | CRUD (reads `bd`, writes artifact + git trailer + `bd comment`) | itself — `regenerate_beads_md` (same file, lines 810-874) | exact (same function, extended) |
| `.gsd/capabilities/beads/capability.json` (`gates[]`, `config` schema) | config | request-response (declarative gate manifest, no runtime code) | itself — existing `steps[]`/`config` blocks (lines 25-98) | exact (same file, same array pattern) |
| `.gsd/capabilities/beads/tests/test_sync.py` (new `TestBlockingOpen`/`TestDivergence`/`TestShipGate` classes) | test | request-response (unit tests over pure functions + mocked `bd`) | itself — `_make_bd_side_effect` + `TestEndToEndTracer`/existing test classes (lines 31-120) | exact (same file, same harness) |
| ship-time commit-trailer writer (new function in `sync.py`, e.g. `record_ship_override`) | utility (git write + fail-open `bd comment`) | event-driven (fires only when `beads.ship_gate=false` bypasses a blocking gate) | `close_wave`'s fail-open shape (lines 419-460) and `bd_available`/`append_state_blocker` (lines 40-68) | role-match (fail-open convention, not a literal function to extend) |

No file outside `.gsd/capabilities/beads/` is touched — D-01..D-06 are additive to the existing sync.py/capability.json/test_sync.py trio. There is no controller, component, or migration file in scope.

## Pattern Assignments

### `.gsd/capabilities/beads/scripts/sync.py` — extend `regenerate_beads_md` (service, CRUD)

**Analog:** itself, `regenerate_beads_md` (lines 810-874), plus its helper `resolve_phase_epic`/`collect_epic_task_ids` (lines 749-762, 319-339)

**Fail-open guard pattern to keep unchanged** (lines 815-826):
```python
if not bd_available():
    print(NOTICE)
    try:
        project_root = find_project_root(Path(phase_dir_arg).resolve())
    except ValueError:
        project_root = None
    if project_root is not None:
        append_state_blocker(
            confined(project_root, ".planning", "STATE.md"),
            "bd unavailable -- beads-status regenerate-beads-md skipped (B6/D-08)",
        )
    return 0
```
D-05's override-comment write must reuse this exact same shape: `bd` failure at write time degrades silently (print + skip), never raises, never blocks the ship.

**blocking_open computation (D-01/D-02) — reuse, don't rebuild, epic enumeration** (lines 831-849):
```python
epic_id = resolve_phase_epic(phase_dir)
if epic_id is None:
    print("no epic yet -- nothing to regenerate")
    return 0

argv = _beads_md_argv(epic_id)          # bd list --parent <epic> --all --json -n 0
result = run_bd(argv)
rows = []
if result.returncode == 0:
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        rows = []

closed_count = sum(1 for r in rows if r.get("status") == "closed")
open_count = len(rows) - closed_count
```
D-01/D-02: `blocking_open` is `open_count` computed from this exact `rows` list — same epic-wide `bd list --parent <epic> --all` query already fetched here, no second `bd` call. No priority/type filter is applied (D-01), so `blocking_open` can literally reuse `open_count` (or be aliased to it) rather than a new predicate.

**Ordinal/task map for divergence, reuse verbatim** (lines 771-783):
```python
def _resolve_task_ordinal_map(phase_dir):
    mapping = {}
    for ordinal, plan_path in discover_plan_files(phase_dir).items():
        try:
            _, _, tasks = parse_plan(plan_path)
        except (OSError, UnicodeDecodeError):
            continue
        for task in tasks:
            if task["beads_id"]:
                mapping[task["beads_id"]] = ordinal
    return mapping
```
D-04's per-issue divergence trigger needs, per synced issue: its `bd` status (already in `rows`) and its task's completion state. Completion state is NOT in `_resolve_task_ordinal_map` — reuse `find_completed_task_ids` (lines 362-385) per plan to build a `{beads_id: task_done_bool}` side table, keyed the same way this ordinal map is built (iterate `discover_plan_files(phase_dir)`, one pass, no new `bd` call).

**find_completed_task_ids — the SUMMARY.md-is-plan-granular-done signal to reuse for D-04's task-completion side** (lines 362-385):
```python
def find_completed_task_ids(phase_dir, plan_id):
    plan_path = discover_plan_files(phase_dir).get(plan_id)
    if plan_path is None:
        return [], 0
    summary_path = plan_path.with_name(f"{plan_id}-SUMMARY.md")
    if not summary_path.exists():
        return [], 0
    _, _, tasks = parse_plan(plan_path)
    ids = []
    skipped = 0
    for task in tasks:
        if task["beads_id"]:
            ids.append(task["beads_id"])
        else:
            skipped += 1
    return ids, skipped
```
D-04's "task has no completing SUMMARY.md" / "SUMMARY.md marks it done" predicate is exactly this function's existence check — call it once per plan in the phase to build the task-completion set, then diff against `rows`' `bd` status per D-04's two directions (`closed`+incomplete, `open`+complete).

**Table renderer to extend with D-06's two new columns** (lines 786-807):
```python
def _render_beads_md_table(rows, ordinal_map):
    lines = [
        "| Issue | Title | Status | Plan Task | Blocked By |",
        "|-------|-------|--------|-----------|------------|",
    ]
    for row in rows:
        issue_id = str(row.get("id", ""))
        title = _escape_table_cell(str(row.get("title", "")))
        status = _escape_table_cell(str(row.get("status", "")))
        plan_task = ordinal_map.get(issue_id, "")
        blocked_by = ", ".join(
            str(dep.get("depends_on_id", ""))
            for dep in row.get("dependencies", []) or []
            if dep.get("type") == "blocks"
        )
        lines.append(f"| {issue_id} | {title} | {status} | {plan_task} | {blocked_by} |")
    return "\n".join(lines)
```
D-06: extend this same function's header/row to a 7-column shape (add "Task Status" and "BD Status" or similar — Claude's Discretion on exact naming per CONTEXT.md) rather than writing a second renderer or a `DIVERGENCE.md`. Every existing caller of `_render_beads_md_table` is `regenerate_beads_md` alone (line 849) — one call site to update.

**Frontmatter block to replace the two placeholder literals** (lines 852-863):
```python
frontmatter = (
    "---\n"
    f"phase: {phase_dir.name}\n"
    f"epic: {epic_id}\n"
    f"open: {open_count}\n"
    f"closed: {closed_count}\n"
    "blocking_open: 0\n"      # <- replace with the D-01/D-02 computed value
    "diverged: 0\n"           # <- replace with the D-04 computed value
    f'generated_from: "{" ".join(argv)}"\n'
    f"generated_at: {generated_at}\n"
    "---\n\n"
)
body = (
    f"# BEADS.md: {phase_dir.name}\n\n"
    "blocking_open/diverged: not yet computed, Phase 3\n\n"   # <- delete this placeholder line
    f"{table}\n"
)
```
These two `0` literals (line 858-859) and the placeholder body line (line 866) are the exact insertion points Phase 3 fills in — `regenerate_beads_md`'s frontmatter/table shape was deliberately built ahead of time for this (per `02-02-SUMMARY.md`).

---

### `.gsd/capabilities/beads/scripts/sync.py` — new override-audit function (utility, event-driven)

**Analog:** `close_wave`'s fail-open write pattern (lines 419-460) + `run_bd` single-call-site convention (lines 34-37)

D-05 needs a new function, e.g. `record_ship_override(project_root, blocking_open, diverged, epic_id)`, invoked only when `beads.ship_gate=false` allows a ship past an otherwise-blocking gate (caller is outside `sync.py` — likely the `ship:pre` orchestration point; `sync.py` need only expose the function + a CLI subcommand mirroring the existing `regenerate-beads-md` subcommand pattern, lines 953-957).

**Git trailer write — no existing analog in this file; stdlib subprocess call to `git commit --trailer` or a formatted string appended pre-commit, per D-05's "always written, durable" requirement.** Use the same `subprocess.run(argv, ...)` argv-list convention as `run_bd` (line 34-37) rather than a shell string, to stay consistent with T-01-01's shell=False rule across the whole file — even though this is `git`, not `bd`.

**`bd comment` write — reuse `run_bd` verbatim, fail-open on error, matching `close_wave`'s bd-call-then-print-on-failure shape** (lines 449-453):
```python
if to_close:
    reason = f"wave complete: {', '.join(plan_ids)}"
    result = run_bd(["bd", "close", *to_close, "--reason", reason])
    if result.returncode != 0:
        print(f"close-wave: bd close failed: {result.stderr.strip()}")
```
D-05's `bd comment <epic_id> "..."` call follows this identical shape: call `run_bd(["bd", "comment", epic_id, comment_text])`, and on non-zero returncode print a skip notice — never raise, never block the ship (matches B6's fail-open convention already established for every other `bd` call in this file).

---

### `.gsd/capabilities/beads/capability.json` — `gates[]` array (config, request-response)

**Analog:** itself — existing `steps[]` array shape (lines 42-98) and `config` block (lines 25-41)

**Exact gate shape from PRD §5.3, to insert verbatim (values only, no research needed — this is a locked spec, not a gray area):**
```json
"gates": [
  { "point": "ship:pre",
    "check": { "predicate": { "kind": "artifact-frontmatter-equals", "artifact": "BEADS.md", "field": "blocking_open", "equals": 0 } },
    "when": "beads.ship_gate", "blocking": true, "onError": "skip" },
  { "point": "ship:pre",
    "check": { "predicate": { "kind": "artifact-frontmatter-equals", "artifact": "BEADS.md", "field": "diverged", "equals": 0 } },
    "when": "beads.ship_gate", "blocking": true, "onError": "skip" }
]
```
Replaces `"gates": []` (line 115 of the current `capability.json`).

**New config key, matching the existing `config` block's per-key shape** (analog: `beads.enabled`, lines 26-30):
```json
"beads.ship_gate": {
  "type": "boolean",
  "default": true,
  "description": "When true, ship:pre blocks on blocking_open>0 or diverged>0 in BEADS.md."
}
```
Add alongside the existing `beads.enabled`/`beads.sync_mode` keys (lines 25-41). PRD §5.3's full config block (line 151) also lists `beads.epic_per` and `beads.recall_scope`, which are NOT this phase's scope — do not add them; add only `beads.ship_gate`.

**`ship:pre` step is currently entirely absent from `steps[]`** (current file only has `plan:pre`/`plan:post`(missing!)/`execute:wave:pre`/`execute:wave:post`, lines 42-98) — verify whether a `ship:post` step (per PRD line 160, which also shows `plan:post` — currently missing from the live capability.json too) needs adding in this phase or was already scoped to a prior phase; CONTEXT.md's integration_points section names only the `gates[]` array and the `beads.ship_gate` config key as this phase's additions — treat `steps[]` changes as out of scope unless confirmed against `.planning/REQUIREMENTS.md` REQ-B9/B10 acceptance criteria during planning.

---

### `.gsd/capabilities/beads/tests/test_sync.py` — new test classes (test, request-response)

**Analog:** itself — `_make_bd_side_effect` (lines 31-51) and `_write_plan_workspace`/`_three_task_plan_text` fixtures (lines 54-109)

**Mocked-bd-response pattern to extend for blocking_open/diverged fixtures:**
```python
def _make_bd_side_effect():
    counter = {"n": 0}
    def _side_effect(argv, **kwargs):
        if argv[:2] == ["bd", "list"]:
            return _completed(0, stdout="[]\n")
        if argv[:2] == ["bd", "show"]:
            return _completed(0, stdout="{}\n")
        if argv[:2] == ["bd", "create"]:
            counter["n"] += 1
            return _completed(0, stdout=f"mock-e1.{counter['n']}\n")
        if argv[:3] == ["bd", "dep", "add"]:
            return _completed(0)
        if argv[:2] == ["bd", "close"]:
            return _completed(0)
        return _completed(1, stderr=f"unexpected bd invocation: {argv}")
    return _side_effect
```
`TestBlockingOpen`/`TestDivergence`/`TestShipGate` need a variant returning a non-empty `bd list --parent <epic> --all --json` JSON array with mixed `status` values (`open`, `closed`) and a `bd comment` branch (`argv[:2] == ["bd", "comment"]`) not present in the current side effect — extend this function (or add a phase-3-specific sibling) rather than duplicating the whole harness.

**Workspace-fixture pattern to reuse for a phase with a synced epic + completed/incomplete plans** (lines 93-109):
```python
def _write_plan_workspace(tmp_path, plan_text, with_state=False):
    planning_dir = tmp_path / ".planning"
    phase_dir = planning_dir / "phases" / "01-substrate"
    phase_dir.mkdir(parents=True)
    (planning_dir / "ROADMAP.md").write_text(
        "### Phase 1: Substrate\nGoal.\n", encoding="utf-8"
    )
    if with_state:
        (planning_dir / "STATE.md").write_text(
            "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
            encoding="utf-8",
        )
    plan_copy = phase_dir / "01-01-PLAN.md"
    plan_copy.write_text(plan_text, encoding="utf-8")
    return plan_copy
```
`TestDivergence` needs the SUMMARY.md-present/absent variable this fixture doesn't yet parametrize — add a `with_summary=False` kwarg that additionally writes `01-01-SUMMARY.md` next to the plan, mirroring `find_completed_task_ids`'s own `summary_path = plan_path.with_name(f"{plan_id}-SUMMARY.md")` check (sync.py line 374).

## Shared Patterns

### `bd` invocation convention
**Source:** `sync.py` module docstring + `run_bd` (lines 1-10, 34-37)
**Apply to:** every new `bd list`/`bd comment` call this phase adds — argv-list, `shell=False` implicit default, single call site (`run_bd`), never a shell string. The new commit-trailer write is `git`, not `bd`, but must follow the identical argv-list-not-shell-string discipline (T-01-01's rationale applies equally to any subprocess call mixing two trust principals).

### Fail-open (B6/D-08)
**Source:** `bd_available` (lines 40-50) + `append_state_blocker` (lines 53-68), applied identically in `close_wave`, `create_issues`, `beads_recall`, `regenerate_beads_md`
**Apply to:** the D-05 override-audit `bd comment` write — "best-effort, follows this project's existing fail-open convention (B6): if `bd` is unavailable at ship time, skip the comment write and note the skip, never block the ship on it" (CONTEXT.md D-05, verbatim). The commit trailer write is NOT fail-open — CONTEXT.md D-05 calls it "always written, durable" — do not wrap the trailer write in the same skip-on-failure branch as the `bd comment` write; only the `bd comment` half gets the B6 treatment.

### Gate predicates never call `bd` live
**Source:** PROJECT.md locked decision, restated in CONTEXT.md canonical_refs — "gate predicates read only generated artifact frontmatter, never query `bd` directly"
**Apply to:** the two new `gates[]` entries in `capability.json` — both must be `artifact-frontmatter-equals` over `BEADS.md`, never a new predicate kind (PRD §5.3 confirms only `command-exists` and `artifact-frontmatter-equals` exist).

## No Analog Found

None. Every file/function in scope is an extension of code already in `.gsd/capabilities/beads/scripts/sync.py`, `capability.json`, or `tests/test_sync.py` — CONTEXT.md's `code_context` section was written specifically to preempt a fresh-pattern search for this phase.

## Metadata

**Analog search scope:** `.gsd/capabilities/beads/` (scripts, capability.json, tests) plus `docs/prd-beads-capability.md` §5.3/§5.4 for the locked gate/frontmatter shape
**Files scanned:** `sync.py` (980 lines, full read), `capability.json` (117 lines, full read), `test_sync.py` (first 120 lines read for harness conventions), `docs/prd-beads-capability.md` (targeted grep + 65-line range read)
**Pattern extraction date:** 2026-08-15
</content>
