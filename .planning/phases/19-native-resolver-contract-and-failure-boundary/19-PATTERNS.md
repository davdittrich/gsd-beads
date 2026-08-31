# Phase 19: Native Resolver Contract and Failure Boundary - Pattern Map

**Mapped:** 2026-08-30
**Files analyzed:** 3 modified files (no new module or fixture file)
**Analogs found:** 3 / 3 role matches; no exact prior `taskContentResolver` declaration exists in tracked plugin source.

## Scope and tracked-source gate

Phase 19 has two implementation tasks only:

1. Add `resolve-task-content <id>` to the existing Beads adapter, with focused public-seam TDD in its existing test module.
2. Add the sole manifest `taskContentResolver` declaration and its validator/declaration test in that same existing test module.

`git ls-files --` proves these are tracked source files:

```text
plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
```

Do **not** name or edit `.gsd/capabilities/beads/**`: `.gitignore:41` ignores that installed/runtime mirror. Its source origin is `plugins/beads-lifecycle/.gsd/capabilities/beads/**`. The installed gsd-core files are contract evidence only, not analogs to edit.

Phase 20 identity migration (`tracker-id` emission/migration) and Phase 21 installed cutover/Patch 2 retirement remain excluded.

## File Classification

| New/Modified File | Role | Data Flow | Closest tracked analog | Match quality |
|---|---|---|---|---|
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` | adapter / CLI controller | request-response, transform | its existing `_task_description`, `run_bd`, `resolve_issue`, and `main` | exact role; new resolver direction |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` | public-boundary test | request-response, transform | `TestEndToEndTracer`, `TestTaskDescription`, `TestSyncModeDeclarationParity`, `TestDirectSkillSyncResolver` | exact role; complementary seams |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` | config / manifest | process invocation | existing top-level capability declaration and `beads.sync_mode` declaration | role-match; no existing resolver field |

No separate fixture module is justified. The existing `test_sync.py` already owns temporary directories, inline task dictionaries, real `bd` tracer setup, mock subprocess results, and manifest reads. Adding a static fixture file or a new adapter module would be an unneeded abstraction.

## Pattern Assignments

### `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` (adapter / CLI controller, request-response + transform)

**Tracked analogs:** `run_bd` (lines 237-240), `_task_description` (lines 513-552), `resolve_issue` (lines 1231-1265), `main` (lines 2573-2686).

**Reuse the typed subprocess seam; do not introduce a shell or a second runner.**

```python
# sync.py:237-240
def run_bd(argv, timeout=BD_TIMEOUT):
    """Run one bd subcommand from a typed argv list; shell interpretation is
    never enabled here -- see module docstring, T-01-01."""
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
```

The resolver must call this unchanged seam with exactly `['bd', 'show', issue_id, '--json']`; validate `issue_id` with the existing `SAFE_BD_ID_RE.fullmatch`, not a new regex. Existing use is at lines 1429-1436.

**Use the canonical writer as the round-trip oracle, not as a parser to modify.**

```python
# sync.py:513-552
sections = []
if task["read_first"]:
    items = [f.strip() for f in task["read_first"].split(",") if f.strip()]
    sections.append("## Read First\n" + "\n".join(f"- {f}" for f in items))
if task["precondition"]:
    sections.append(f"## Precondition\n{task['precondition']}")
if task["behavior"]:
    sections.append(f"## Behavior\n{task['behavior']}")
if task["action"]:
    sections.append(f"## Action\n{task['action']}")
if task["verify"]:
    sections.append(f"## Verify\n{task['verify']}")
if task["done"]:
    sections.append(f"## Done\n{task['done']}")
if task["files"]:
    sections.append("## Files\n" + "\n".join(f"- {f}" for f in task["files"]))
return "\n\n".join(sections) + ("\n" if sections else "")
```

The new private resolver implementation is the inverse only for the locked writer grammar: exact, column-zero `## Read First`, `## Verify`, and `## Done`, while preserving all non-extracted prose and H2 sections in order. It must return exactly the five-key JSON object on stdout, or nonzero with bounded stderr and zero stdout. Do not reuse `bd_available()` (lines 242-252): its intentional fail-open semantics conflict with Phase 19's fail-closed resolver interface.

**Follow existing CLI registration and dispatch.**

```python
# sync.py:2573-2580, 2642-2656
def main(argv=None):
    parser = argparse.ArgumentParser(prog="sync.py")
    sub = parser.add_subparsers(dest="command", required=True)
    create_p = sub.add_parser(
        "create-issues", help="Sync a PLAN.md's tasks into bd issues under a phase epic"
    )
    create_p.add_argument("plan_path")
    ...
    args = parser.parse_args(argv)
    if args.command == "create-issues":
        ...
        return create_issues(args.plan_path, allow_strip=(sync_mode != "mirror"))
```

Add one required positional id on a `resolve-task-content` subparser and one dispatch arm returning the resolver exit code. Keep the final `return 1`; do not route through lifecycle dispatch, config, PLAN parsing, retries, or fallback prose.

**Existing callers / impact:** only `main` changes. Its current production caller is the module guard at lines 2688-2689, `sys.exit(main())`; test callers are at `test_sync.py:2153, 3542, 3624, 3794, 3796, 3970, 5279, 5382`. The proposed resolver has no current caller; its caller is the declared external gsd-core invocation after Phase 21, so this phase verifies it only at `main([...])`. `_task_description`, `run_bd`, `resolve_issue`, and `SAFE_BD_ID_RE` are reused unchanged. `resolve_issue` is called only by `create_issues` at lines 1691-1698 and must not gain Phase 20 identity work.

**Ponytail result:** Task 1 first holds at rung **2**: existing writer, id grammar, typed runner, CLI, and test module already provide the needed pieces. Rung 3 supplies only stdlib `json`, `re`, and existing `subprocess`; no general Markdown parser, class, interface, cache, retry wrapper, or separate executable is warranted.

### `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` (public-boundary test, request-response + transform)

**Tracked analogs:** `TestEndToEndTracer` (lines 153-272), `TestTaskDescription` (lines 1131-1178), `TestSyncModeDeclarationParity` (lines 5317-5363), and `TestDirectSkillSyncResolver` (lines 5639-5828).

**Use the existing producer-to-live-Beads tracer for the primary round trip.**

```python
# test_sync.py:220-271
result = subprocess.run(
    [sys.executable, str(Path(sync.__file__)), "create-issues", str(plan_copy)],
    cwd=tmp_path, capture_output=True, text=True, timeout=30,
)
self.assertEqual(result.returncode, 0, result.stderr)
...
shown = subprocess.run(
    ["bd", "show", issue_id, "--json"],
    cwd=tmp_path, capture_output=True, text=True, timeout=30,
)
self.assertEqual(shown.returncode, 0, shown.stderr)
payload = json.loads(shown.stdout)
if isinstance(payload, list):
    payload = payload[0]
self.assertTrue(payload.get("description", "").strip(), payload)
self.assertTrue(payload.get("acceptance_criteria", "").strip(), payload)
```

Extend this pattern with a vertical public-seam test: build the description through `sync._task_description(task)`, make `bd show` return that one issue row, invoke `sync.main(["resolve-task-content", issue_id])`, parse stdout, and assert exact five-field lossless output. This makes the writer—not a hand-reimplemented expected parser—the independent producer oracle.

**Spy the trust-boundary argv and isolate negative arms.**

```python
# test_sync.py:68-90
def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)

def _make_bd_side_effect():
    def _side_effect(argv, **kwargs):
        if argv[:2] == ["bd", "show"]:
            return _completed(0, stdout="{}\n")
        ...
        return _completed(1, stderr=f"unexpected bd invocation: {argv}")
    return _side_effect
```

Patch `subprocess.run`, capture both streams with `contextlib.redirect_stdout` / `redirect_stderr`, and assert the single argv exactly rather than only that a mock was called. For each negative test, change one variable only (id, timeout, process exit, UTF-8/JSON, envelope, row count/type/id, source field type, duplicate heading, fence state, `Read First` grammar, or unusable description); assert `exit_code != 0`, `stdout == ''`, and one bounded stderr diagnostic. Do not build confounded multi-fault fixtures.

**Retain direct writer tests as a narrow unit complement, not the primary proof.**

```python
# test_sync.py:1131-1177
description = sync._task_description(task)
self.assertIn("## Read First", description)
self.assertIn("## Precondition", description)
self.assertIn("## Behavior", description)
self.assertIn("## Action", description)
self.assertIn("## Verify", description)
self.assertIn("## Done", description)
self.assertIn("## Files", description)
...
self.assertNotIn("acceptance", description.lower())
```

**Ponytail result:** Task 1's tests also stop at rung **2**. Add methods to the established stdlib `unittest` file and inline payloads/temporary directories; do not create fixture files, a fake `bd` package, snapshots, or a second test framework.

### `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` (manifest/config, process invocation)

**Tracked analog:** its existing single top-level capability declaration, especially the `config` object (lines 26-55) and lifecycle declaration arrays (lines 56-184). There is no exact tracked `taskContentResolver` field analog.

```json
// capability.json:1-10, 26-39
{
  "id": "beads",
  "role": "feature",
  "version": "0.4.0",
  "title": "Beads issue tracking",
  ...
  "config": {
    "beads.enabled": { "type": "boolean", "default": true },
    "beads.sync_mode": {
      "type": "enum",
      "values": ["authoritative", "mirror"],
      "default": "authoritative"
    }
  }
}
```

Add exactly one top-level `taskContentResolver` declaration with the locked `trackerPrefix: "beads"`, `invoke.binary: "python3"`, `invoke.args: ["-c", <stdlib bootstrap>, "{{id}}"]`, and `timeoutMs: 10000`. The bootstrap owns the fixed verb: resolve `script = Path(os.environ.get("GSD_HOME") or Path.home()) / ".gsd/capabilities/beads/scripts/sync.py"`, fail boundedly when absent, then call `os.execv(sys.executable, [sys.executable, str(script), "resolve-task-content", sys.argv[1]])`. The manifest supplies `{{id}}` as its one standalone post-bootstrap argv element; the interpreter relaunch preserves tracked mode `100644` and avoids executable-bit lifecycle state. Do not add a PATH shim, shell wrapper, capability-root feature request, second resolver, or manifest config key.

**Use the existing manifest-parity test layout for the validator/declaration test.**

```python
# test_sync.py:5317-5339
CAPABILITY_PATH = Path(__file__).resolve().parent.parent / "capability.json"

def _sync_mode_config(self):
    return json.loads(self.CAPABILITY_PATH.read_text(encoding="utf-8"))["config"][
        "beads.sync_mode"
    ]

def test_declared_values_array_is_exactly_authoritative_then_mirror(self):
    self.assertEqual(self._sync_mode_config()["values"], ["authoritative", "mirror"])
```

Place a small adjacent test class in `test_sync.py`: load the tracked manifest through `CAPABILITY_PATH`, assert one resolver and its literal invocation shape, then call the installed `validateCapability` export read-only and assert `errors == []`. The closest installed-tree probe model uses a truthful skip only when its external installed prerequisite is absent:

```python
# test_sync.py:5046-5061
workflow_path = _installed_workflow_path("plan-phase.md")
if not workflow_path.exists():
    self.skipTest(f"{workflow_path} not present on this machine")
captured = io.StringIO()
with contextlib.redirect_stderr(captured):
    exit_code = sync.check_native_step_dispatch("plan:post")
self.assertEqual(exit_code, 0)
```

**Ponytail result:** Task 2 first holds at rung **4**: gsd-core's native resolver seam is the required platform feature. Its locator is rung **3** Python stdlib only. A new module, dependency, PATH lifecycle, or duplicate declaration would be shallow, lower-locality work.

## Shared Patterns

### Resolver seam, interface, depth, and locality

The manifest declaration is the **seam**. `sync.py resolve-task-content <id>` is the concrete **adapter**. Its **interface** is deliberately small: one validated id input; success emits only `description`, `read_first`, `verify`, `acceptance_criteria`, and `done`; every invalid outcome is nonzero with empty stdout. Parsing Beads envelopes, validation, fence-aware partitioning, list normalization, and process defects stay in the adapter **implementation**. This gives the module **depth**, **leverage**, and **locality**: gsd-core learns one generic resolver contract and no caller learns Beads JSON or Markdown rules.

### Error handling and output discipline

`sync.py` has both fail-open lifecycle operations and fail-closed operations. The resolver is an intentional fail-closed exception: never inherit `bd_available()`/lifecycle notice behavior. Centralize a small private error path that writes one bounded diagnostic to stderr and returns 1; every error path must have no stdout. `argparse` must not be the observable failure format for invalid resolver data after command parsing.

### Public-boundary TDD and subprocess spies

Test through `main([...])` for behavior and through `subprocess.run` patching for the exact fixed argv. The public test owns stdout/stderr capture and JSON assertions; direct tests of private partition helpers are allowed only as small focused complements. Keep one-factor negative fixtures so each green/red result identifies the exercised contract.

### Manifest validation

Use `CAPABILITY_PATH` derived from the tracked test file, never an installed `.gsd` mirror. The validator test is read-only against installed gsd-core and must assert the literal single resolver declaration as well as `errors == []`; validator acceptance alone would not catch a wrong but schema-valid invocation.

## Scientific ambiguity resolution

1. **Argument map:** The claim is that the canonical writer inverse behind the native resolver seam is the minimal contract-complete adapter. Direct premises are D-01–D-19, `_task_description`, fixed argv `run_bd`, and the installed resolver/validator contract.
2. **Evidentiary inventory:** current tracked source and direct installed-runtime inspection are high-quality empirical/code evidence; the issue is scope evidence only, not runtime authority.
3. **Logic audit:** a blank resolver result is not a safe substitute for unusable authored content; it changes a hard failure into a non-throwing gsd-core outcome. **Confidence: 99/100.**
4. **Bias/confound audit:** a fixture combining malformed JSON, an invalid id, and duplicate headings cannot establish which guard worked. Each negative arm therefore varies exactly one input category. **Confidence: 98/100.**
5. **Alternative explanations:**
   - A general CommonMark parser is needed for arbitrary task prose. Rejected: only three exact headings and fence protection are in contract; a broader parser adds behavior without resolving duplicate reserved-heading ambiguity. **Confidence: 94/100.**
   - gsd-core should ingest raw Beads JSON or coerce an empty result. Rejected: that leaks tracker behavior across the seam and weakens the specified failure semantics. **Confidence: 99/100.**
6. **Integrated appraisal:** **Strong — accept the existing-adapter inverse. Confidence: 96/100.** Retain the explicit residual uncertainty: an unfenced reserved H2 in authored prose is structurally indistinguishable; the locked duplicate rejection is the fail-closed policy.

## No Exact Analog Found

| Need | Closest tracked source | Planner instruction |
|---|---|---|
| `taskContentResolver` field | `capability.json` top-level declaration | Add the sole field using the locked research shape; do not copy an untracked runtime mirror. |
| Resolver command/parser | `_task_description` + `run_bd` + `main` | Keep parsing private in `sync.py`; no generic Markdown-parser dependency or new module. |
| Installed capability-validator test | `TestSyncModeDeclarationParity` + `TestNativeStepDispatchProbeAgainstInstalledTree` | Combine tracked-manifest literal assertions with a read-only installed-validator invocation in `test_sync.py`. |

## Metadata

**Analog search scope:** tracked `plugins/beads-lifecycle/.gsd/capabilities/beads/{capability.json,scripts,sync.py,tests/test_sync.py}` plus tracked test roots; `.gsd/capabilities/beads/**` rejected as ignored runtime mirror.

**Symbols traced:** `run_bd`, `SAFE_BD_ID_RE`, `_task_description`, `resolve_issue`, `main`, `TestEndToEndTracer`, `TestTaskDescription`, `TestSyncModeDeclarationParity`, `TestNativeStepDispatchProbeAgainstInstalledTree`, and `TestDirectSkillSyncResolver`.

**Pattern extraction date:** 2026-08-30
