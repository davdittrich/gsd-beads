# Phase 16: beads-issue-content-parity - Pattern Map

**Mapped:** 2026-08-19
**Files analyzed:** 5 (all existing files, extended in place — no new files per RESEARCH.md's
"Recommended Project Structure": this phase is pure extension, not invention)
**Analogs found:** 5 / 5 (every target file is its own best analog — new functions clone an
existing sibling function in the same file)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog (same file, sibling function) | Match Quality |
|---|---|---|---|---|
| `.gsd/capabilities/beads/scripts/sync.py` — `parse_plan()` extension (type + content-field regexes) | parser/transform | transform | `parse_plan()` itself, lines 142-170 (existing `NAME_RE`/`BEADS_ID_RE`/`FILES_RE` extraction loop) | exact |
| `.gsd/capabilities/beads/scripts/sync.py` — new `_task_description(task)` | utility/transform | transform | `_todo_description()`, lines 278-285 | exact |
| `.gsd/capabilities/beads/scripts/sync.py` — `resolve_issue()` `-d`/`--acceptance` addition | service, CRUD (create) | CRUD | `resolve_issue()` itself, lines 615-634 (particularly the `bd create` argv at line 629-631) | exact |
| `.gsd/capabilities/beads/scripts/sync.py` — `resolve_epic()`/`resolve_phase_epic()`/`resolve_milestone_epic()` `-d` addition | service, CRUD (create) | CRUD | `resolve_epic()` itself, lines 564-612 (`bd create` argv at line 609) | exact |
| `.gsd/capabilities/beads/scripts/sync.py` — new `check_execute_plan_patch()` detector | utility, config-verification | request-response (subprocess+file read) | `check_shipmd_patch()`, lines 1553-1601 | exact |
| `.gsd/capabilities/beads/scripts/sync.py` — new `reconcile_stale_closed(phase_dir)` subcommand | service, batch reconciliation | batch/event-driven | `close_wave()`, lines 784-825, composed with `_resolve_completed_task_ids()`/`filter_open_ids()` | exact |
| `.gsd/capabilities/beads/scripts/sync.py` — `main()` new subparser wiring (`reconcile-stale-closed`, `check-execute-plan-patch`) | CLI/router | request-response | `main()` itself, lines 1604-1681 (`close-wave`/`check-shipmd-patch` subparser blocks) | exact |
| `.gsd/capabilities/beads/tests/test_sync.py` — new/extended test classes | test | request-response (mocked subprocess) | `TestCreateIssues` (301-345), `TestCloseWave` (907+), `TestCheckShipmdPatch` (2086+) | exact |
| `$HOME/.claude/gsd-core/workflows/execute-plan.md` — new patch block | config (machine-local patch) | request-response | `ship.md`'s existing `gsd-beads-patch:ship-pre-generic-dispatch v1` block (external file, not in this repo — see `GSD-CORE-PATCH.md`) | role-match (pattern documented, file itself outside repo) |
| `.gsd/capabilities/beads/GSD-CORE-PATCH.md` — second `##` section for the new patch | documentation/config record | n/a | `GSD-CORE-PATCH.md`'s existing single-patch section (own file, extend in place) | exact |
| `.gsd/capabilities/beads/skills/beads-status/SKILL.md` — revise Anti-Pattern 6, wire `verify:post` reconciliation dispatch | config/skill-doc | event-driven (lifecycle dispatch) | Same file's existing Step 2/2a/2b dispatch-point sections | exact |

## Pattern Assignments

### `parse_plan()` extension — task `type` attribute + content-field regexes

**Analog:** `.gsd/capabilities/beads/scripts/sync.py:142-170` (same function, extend in place)

**Existing regex/extraction convention** (lines 26-29, all module-level `re.compile`, DOTALL, paired
one-per-tag):
```python
TASK_RE = re.compile(r"<task\b[^>]*>.*?</task>", re.DOTALL)
NAME_RE = re.compile(r"<name>(.*?)</name>", re.DOTALL)
BEADS_ID_RE = re.compile(r"<beads-id>(.*?)</beads-id>", re.DOTALL)
FILES_RE = re.compile(r"<files>(.*?)</files>", re.DOTALL)
```
Clone this shape for the six new tags RESEARCH.md's Priority 3 identifies as missing:
`ACTION_RE`, `VERIFY_RE`, `ACCEPTANCE_CRITERIA_RE`, `READ_FIRST_RE`, `DONE_RE`, `PRECONDITION_RE`
— each `re.compile(r"<tag>(.*?)</tag>", re.DOTALL)`, no new parsing technique.

**Task `type` attribute** — no existing regex extracts an XML attribute (only tag bodies); add
`TASK_TYPE_RE = re.compile(r'<task\b[^>]*\btype="([^"]*)"')` run against each `TASK_RE` match's
`m.group(0)` block, same way `NAME_RE.search(block)` etc. already work at line 154-156.

**Core extraction loop pattern** (lines 152-169, extend the dict literal in place):
```python
for m in TASK_RE.finditer(text):
    block = m.group(0)
    name_m = NAME_RE.search(block)
    id_m = BEADS_ID_RE.search(block)
    files_m = FILES_RE.search(block)
    files = (
        [f.strip() for f in files_m.group(1).split(",") if f.strip()]
        if files_m else []
    )
    tasks.append({
        "name": name_m.group(1).strip() if name_m else "",
        "name_end": m.start() + (name_m.end() if name_m else 0),
        "beads_id": id_m.group(1).strip() if id_m else None,
        "files": files,
    })
```
Add `type_m`/`action_m`/`verify_m`/`acceptance_m`/`read_first_m`/`done_m`/`precondition_m` the same
way, `.strip() if <>_m else ""` (or `None` for optional `<precondition>`, matching `beads_id`'s
`None`-when-absent convention already established).

**Test fixture ground truth** — `_three_task_plan_text()` in `test_sync.py:93-129` and
`.gsd/capabilities/beads/tests/fixtures/plan-single.md` already contain real
`<task type="auto"><name>...</name><files>...</files><read_first>...</read_first><action>...</action>
<verify>...</verify><acceptance_criteria>...</acceptance_criteria><done>...</done></task>` blocks —
use these as the exact schema to parse against, no new fixture needed for the parser-extension tests.

---

### `_task_description(task)` — new rendering function

**Analog:** `_todo_description()`, `.gsd/capabilities/beads/scripts/sync.py:278-285`

```python
def _todo_description(todo):
    """Fold problem/solution (and files, when present) into one `-d` prose
    string (D-03: `files:` has no structured bd field, so it carries as a
    "## Files" section appended only when non-empty)."""
    desc = f"## Problem\n{todo['problem']}\n\n## Solution\n{todo['solution']}\n"
    if todo["files"]:
        desc += "\n## Files\n" + "\n".join(f"- {f}" for f in todo["files"]) + "\n"
    return desc
```

Clone this exact shape for `_task_description(task)`: one function, one call site, markdown `##`
section headers per field, a field folded in only when non-empty (mirrors the `files` conditional
here). Per RESEARCH.md's corrected field list (Priority 3), fold `precondition` (optional),
`read_first`, `action`, `verify`, `done` into the `-d` string; `acceptance_criteria` is passed
**separately** to `bd create --acceptance` (RESEARCH.md's live-verified structured-field finding —
do NOT fold it into this function's output, unlike `_todo_description`'s `files` which has no
structured bd field to use instead).

---

### `resolve_issue()` — add `-d`/`--acceptance` to the create call

**Analog:** `resolve_issue()` itself, `.gsd/capabilities/beads/scripts/sync.py:615-634`

```python
def resolve_issue(task, epic_id, ordinal_prefix, task_index):
    """Return (issue_id, created, divergent). <beads-id> is the identity;
    only create when it is absent -- never resolve or dedup by title (B4).
    ...
    """
    if task["beads_id"]:
        check = run_bd(["bd", "show", task["beads_id"], "--json"])
        if check.returncode != 0:
            return task["beads_id"], False, True
        return task["beads_id"], False, False
    title = f"{ordinal_prefix}.{task_index} {task['name']}"
    result = run_bd(
        ["bd", "create", title, "--type", "task", "--parent", epic_id, "--silent"]
    )
    if result.returncode != 0:
        raise RuntimeError(f"bd create (task) failed: {result.stderr.strip()}")
    return result.stdout.strip(), True, False
```

**Change:** only the `bd create` argv (line 629-631) grows — insert `"-d", _task_description(task)`
and, when `task["acceptance_criteria"]` is non-empty, `"--acceptance", task["acceptance_criteria"]`.
Everything else (resolve-by-id-first, never-recreate, `divergent` flag) is unchanged — this is the
single insertion point RESEARCH.md's "one place writes the shape" discipline calls for. Keep the
argv as a typed list, never a shell string (module docstring, T-01-01 — unchanged threat model,
same mitigation, new field content).

---

### `resolve_epic()` / `resolve_phase_epic()` / `resolve_milestone_epic()` — add `-d`

**Analog:** `resolve_epic()` itself, `.gsd/capabilities/beads/scripts/sync.py:564-612`, specifically:
```python
title = get_phase_header(roadmap_path, phase_num)
result = run_bd(["bd", "create", title, "--type", "epic", "--silent"])
if result.returncode != 0:
    raise RuntimeError(f"bd create (epic) failed: {result.stderr.strip()}")
return result.stdout.strip(), True, stale_epic_id
```
Same insertion pattern as `resolve_issue()` above: add `"-d", <content>` to this argv. Content
source per RESEARCH.md's Assumption A1 (Claude's Discretion): the plan's `<objective>` text,
extracted from `frontmatter`/`text` the same way `parse_depends_on(frontmatter)` already extracts
a plan-level field from the same parsed inputs this function already receives.

---

### `check_execute_plan_patch()` — new detector function

**Analog:** `check_shipmd_patch()`, `.gsd/capabilities/beads/scripts/sync.py:1553-1601`

```python
def check_shipmd_patch(ship_md_path_override=None):
    """... Called from two independent points (CR-01): ... `beads-recall`
    SKILL.md's Step 3.5 is the call site that actually detects loss: it runs
    at `plan:pre`, dispatched by gsd-core's own native generic step-dispatch
    loop, independent of ship.md's patched dispatch loop entirely. ...
    """
    if ship_md_path_override:
        ship_md_path = Path(ship_md_path_override)
    else:
        ship_md_path = (
            Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
            / "gsd-core" / "workflows" / "ship.md"
        )
    if not ship_md_path.exists():
        print(f"ship.md not found at {ship_md_path} -- cannot verify ...")
        return 1
    text = ship_md_path.read_text(encoding="utf-8")
    if SHIP_MD_PATCH_MARKER in text:
        print(f"ship.md ship:pre patch: present (v1) at {ship_md_path}")
        return 0
    print(f"⚠ ship.md's ... patch is missing at {ship_md_path} -- ... Reapply: see "
          "...GSD-CORE-PATCH.md")
    return 1
```

Clone verbatim for `check_execute_plan_patch()`: new module-level marker constant
(`EXECUTE_PLAN_PATCH_MARKER = "<!-- gsd-beads-patch:execute-plan-bd-task-read v1 -->"`, sibling to
`SHIP_MD_PATCH_MARKER` at line 67), same `CLAUDE_CONFIG_DIR`-with-default resolution, same
exists-check / substring-check / two-branch print+return-code shape, targeting
`gsd-core/workflows/execute-plan.md` instead of `ship.md`. Per RESEARCH.md's D-05 "independence"
principle, dispatch this new detector from `beads-recall/SKILL.md`'s existing Step 3.5 alongside
(not replacing) the existing `check_shipmd_patch` call — same lifecycle point, same independence
guarantee already proven for the ship.md patch.

---

### `reconcile_stale_closed(phase_dir)` — new phase-wide backstop subcommand

**Analog:** `close_wave()`, `.gsd/capabilities/beads/scripts/sync.py:784-825`, composed with the
two helper functions it already reuses:

```python
def close_wave(phase_dir_arg, plan_ids):
    if not bd_available():
        print(NOTICE)
        ...
        return 0
    phase_dir = Path(phase_dir_arg).resolve()
    all_ids = []
    skipped_total = 0
    plan_counts = []
    for plan_id in plan_ids:
        ids, skipped = find_completed_task_ids(phase_dir, plan_id)
        all_ids.extend(ids)
        skipped_total += skipped
        plan_counts.append((plan_id, len(ids)))
    unique_ids = list(dict.fromkeys(all_ids))
    to_close = filter_open_ids(unique_ids)
    if to_close:
        reason = f"wave complete: {', '.join(plan_ids)}"
        result = run_bd(["bd", "close", *to_close, "--reason", reason])
        if result.returncode != 0:
            print(f"close-wave: bd close failed: {result.stderr.strip()}")
    per_plan = ", ".join(f"{pid}:{n}" for pid, n in plan_counts)
    print(f"Closed {len(to_close)} issue(s) across {len(plan_ids)} plan(s) ({per_plan}); "
          f"skipped {skipped_total} task(s) with no beads-id")
    return 0
```

**Difference for the new function:** replace the wave-scoped `for plan_id in plan_ids:
find_completed_task_ids(...)` loop with a single call to the already-existing, already-tested
phase-wide helper `_resolve_completed_task_ids(phase_dir)` (`sync.py:696-705`, itself just this
same per-plan loop generalized to every plan the phase's `discover_plan_files` finds — no new
completion-detection logic needed). Then reuse `filter_open_ids()` (`sync.py:753-781`) and the same
`bd close <ids> --reason ...` call unchanged. This is RESEARCH.md's "Don't Hand-Roll" #3: both
halves of the stale-detection math already exist and are tested; the only new code is the call site
and its `bd_available()`/`NOTICE` fail-open guard (clone lines 785-796 verbatim, matching every
other subcommand entry point in this file).

**Idempotency guarantee (unchanged, same as `close_wave`):** `filter_open_ids()` already re-queries
bd's live status before closing, so a repeat `reconcile-stale-closed` run over already-closed issues
issues zero `bd close` calls — same B5 guarantee, no new logic needed to make the new subcommand
safe to call from `verify:post` on every phase regardless of how many times it's already run.

---

### `main()` — new subparser wiring

**Analog:** `main()` itself, `.gsd/capabilities/beads/scripts/sync.py:1604-1681`, specifically the
`close-wave`/`check-shipmd-patch` subparser blocks:
```python
close_p = sub.add_parser("close-wave", help="...")
close_p.add_argument("phase_dir")
close_p.add_argument("plan_ids", nargs="+")
...
check_shipmd_patch_p = sub.add_parser("check-shipmd-patch", help="...")
check_shipmd_patch_p.add_argument("--ship-md-path", default=None)
...
if args.command == "close-wave":
    return close_wave(args.phase_dir, args.plan_ids)
...
if args.command == "check-shipmd-patch":
    return check_shipmd_patch(args.ship_md_path)
```
Clone this shape for `reconcile-stale-closed` (one positional `phase_dir` arg, like `close-wave`
minus `plan_ids`) and `check-execute-plan-patch` (one optional override flag, like
`check-shipmd-patch`'s `--ship-md-path`).

---

## Shared Patterns

### bd subprocess invocation (applies to every new `bd create`/`bd show` call site)
**Source:** `sync.py:79-82` (`run_bd`) + module docstring lines 1-10
```python
def run_bd(argv, timeout=BD_TIMEOUT):
    """Run one bd subcommand from a typed argv list; shell interpretation is
    never enabled here -- see module docstring, T-01-01."""
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
```
**Apply to:** every new `-d`/`--acceptance` argv addition in `resolve_issue`/`resolve_epic` — always
build the argv as a Python list appended to, never string-interpolated (T-01-01/N4, ASVS V5 per
RESEARCH.md's Security Domain section — PLAN.md text is a different trust principal than the `bd`
process).

### bd-unavailable / bd-failing-mid-run fail-open guard
**Source:** `create_issues()` lines 828-840 and 852-885, `close_wave()` lines 784-797
```python
if not bd_available():
    print(NOTICE)
    try:
        project_root = find_project_root(...)
    except ValueError:
        project_root = None
    if project_root is not None:
        append_state_blocker(
            confined(project_root, ".planning", "STATE.md"),
            "bd unavailable -- <subcommand> skipped (B6/D-08)",
        )
    return 0
```
**Apply to:** the new `reconcile_stale_closed` subcommand (clone verbatim, same guard every
subcommand entry point already has) and any new mid-run `RuntimeError` raised by the extended
`resolve_issue`/`resolve_epic` (already wrapped by `create_issues`'s existing `try/except
RuntimeError` at lines 857-885 — no new exception handling needed there, only the raise-on-failure
convention `if result.returncode != 0: raise RuntimeError(...)` already used at lines 610-611 and
632-633).

### D-04 hard-fail signature for `bd show` (read-path patch, execute-plan.md — outside this repo)
**Source:** RESEARCH.md live verification (not a sync.py excerpt — this is gsd-core's file):
```
$ bd show nonexistent-id --json; echo "exit=$?"
{"error": "no issues found matching the provided IDs", "schema_version": 1}
exit=1
```
**Apply to:** the new `execute-plan.md` patch's per-task `bd show <beads-id> --json` branch — check
BOTH non-zero exit code AND (defensively) an `"error"` key in the parsed JSON, matching `sync.py`'s
own `result.returncode != 0` convention used everywhere else in this file (e.g. `resolve_epic`
line 593, `resolve_issue` line 625).

### Test mocking convention (applies to every new test class)
**Source:** `test_sync.py:70-90` (`_make_bd_side_effect`) + `TestCreateIssues` (301-345)
```python
@mock.patch("subprocess.run")
def test_...(self, mock_run):
    mock_run.side_effect = _make_bd_side_effect()
    with tempfile.TemporaryDirectory() as tmp:
        plan_copy = _write_plan_workspace(Path(tmp), _three_task_plan_text())
        exit_code = sync.create_issues(str(plan_copy))
    self.assertEqual(exit_code, 0)
    task_creates = self._create_argvs(mock_run.call_args_list, "task")
    self.assertIn("--parent", task_creates[0])
```
**Apply to:** all new tests for `-d`/`--acceptance` presence (extend `TestCreateIssues`/
`TestPhaseScopedEpic`), the new `TestReconcileStaleClosed` class (mirror `TestCloseWave`'s
mocking, `test_sync.py:907+`), and the new `TestCheckExecutePlanPatch` class (mirror
`TestCheckShipmdPatch`, `test_sync.py:2086+`, same tmp-file-with/without-marker structure). Assert
against the argv list built by the function under test (`self.assertIn("-d", argv)` /
`argv[argv.index("-d") + 1]` non-empty) — never spin up a real `bd` database.

## No Analog Found

None. Every file/function this phase touches is an extension of an existing sibling in the same
file, per RESEARCH.md's own "Don't Hand-Roll" table and "Key insight: every mechanism this phase
needs ... already has a proven, tested precedent inside this exact file." The one file outside this
repo (`$HOME/.claude/gsd-core/workflows/execute-plan.md`) has a documented precedent
(`ship.md`'s existing patch) but is machine-local, not codebase-searchable — its analog is the
*pattern* recorded in `GSD-CORE-PATCH.md`, not a second in-repo file.

## Metadata

**Analog search scope:** `.gsd/capabilities/beads/scripts/sync.py`,
`.gsd/capabilities/beads/tests/test_sync.py`, `.gsd/capabilities/beads/GSD-CORE-PATCH.md`,
`.gsd/capabilities/beads/skills/beads-status/SKILL.md`
**Files scanned:** 4 (all in-repo files RESEARCH.md's "Recommended Project Structure" names; no
directory sweep needed since RESEARCH.md already identified the exact touch-set)
**Pattern extraction date:** 2026-08-19
