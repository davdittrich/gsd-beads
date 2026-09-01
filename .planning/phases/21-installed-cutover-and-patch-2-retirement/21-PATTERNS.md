# Phase 21: Installed Cutover and Patch 2 Retirement - Pattern Map

**Mapped:** 2026-09-01
**Files analyzed:** 9 (8 tracked files; 1 runtime-derived machine-local workflow)
**Analogs found:** 8 / 9 tracked/runtime targets

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` | utility / CLI adapter | request-response | its retained `ship-md` `PATCH_CHECKS` entry and `check_shipmd_patch` wrapper | exact seam |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` | test | request-response | `TestResolveTaskContent` and `TestCheckShipmdPatch` | exact role/flow |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` | operational documentation | file-I/O | Patch 1 section in the same document | exact retention/deletion boundary |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md` | workflow instruction | event-driven | surviving `check-patch ship-md` step in the same block | exact call-site reduction |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` | feature manifest/config documentation | request-response | existing `beads.sync_mode` description and native resolver declaration | exact local wording seam |
| `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md` | active integration guidance | event-driven | existing `plan:pre` and config-key rows | exact local wording seam |
| `README.md` | operational documentation | request-response | existing native-resolver source-contract caveat | role-match |
| `CHANGELOG.md` | release-history documentation | transform | current version's `Added` / `Changed` / `Breaking` entries | exact format |
| runtime-derived installed `execute-plan.md` workflow (not a tracked path) | runtime workflow configuration | file-I/O | no tracked analog; Patch 2 is its own recorded exact-byte source | no reusable source analog |

All named analog files are tracked (`git ls-files --` returned each path). The installed workflow is intentionally not named with a fixed runtime path: derive it from the active installer/registry transaction immediately before mutation.

## Pattern Assignments

### `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` (utility / CLI adapter, request-response)

**Analog:** retained `ship-md` table row and `check_shipmd_patch` wrapper in the same tracked module.

**Keep the small fixed table; remove only the `execute-plan` variant** (lines 151-201):

```python
PATCH_CHECKS = {
    "ship-md": {
        "default_path_parts": ("gsd-core", "workflows", "ship.md"),
        "marker": SHIP_MD_PATCH_MARKER,
        "version": "v2",
        # message templates
    },
    "execute-plan": {
        "marker": EXECUTE_PLAN_PATCH_MARKER,
        # Patch 2-only templates
    },
}
```

Delete the Patch 2 marker constant, the second table entry, and `check_execute_plan_patch`; leave the `ship-md` row, `check_patch`, and `check_shipmd_patch` structurally unchanged. Do not replace the surviving one-entry table with a new special case or compatibility abstraction.

**Preserve the generic reader contract** (lines 2827-2866):

```python
entry = PATCH_CHECKS.get(target)
if entry is None:
    known = ", ".join(sorted(PATCH_CHECKS))
    print(f"unknown patch-check target '{target}' -- expected one of: {known}")
    return 1
...
present = entry["marker"] in text
fmt = entry["present_msg"] if present else entry["missing_msg"]
print(fmt.format(filename=entry["filename"], path=path, version=entry["version"]))
return 0 if present else 1
```

**Delete both reached call sites, preserve Patch 1 immediately beside them:**

```python
# `lifecycle_dispatch`, lines 1208-1223
beads_recall(str(phase_dir))
check_shipmd_patch()
check_execute_plan_patch()
check_sync_mode_value(project_root)
```

Delete only `check_execute_plan_patch()`. The CodeGraph call path establishes the other material caller: `main → create_issues → check_execute_plan_patch → check_patch`; the Patch 2 strip gate is at lines 2143-2166. After the native public proof, remove that gate and its Patch-2-only diagnostic while retaining the existing `allow_strip` hook safeguard and `strip_task_bodies` flow.

**CLI routing pattern** (lines 3052-3062 and 3111-3112, read through CodeGraph):

```python
check_patch_p = sub.add_parser("check-patch", ...)
check_patch_p.add_argument("target", choices=sorted(PATCH_CHECKS))
...
if args.command == "check-patch":
    return check_patch(args.target, args.path)
```

Keep the public `check-patch` seam for `ship-md`; deleting the `execute-plan` key automatically narrows its accepted target. Do not leave an alias, tombstone, or explicit retired-target branch.

**Resolver must be unchanged and is the proof mechanism, not a replacement to implement** (lines 676-782):

```python
result = run_bd(["bd", "show", issue_id, "--json"], timeout=8)
...
print(json.dumps({
    "description": retained_description,
    "read_first": read_first,
    "verify": extracted["Verify"] or None,
    "acceptance_criteria": criteria_items,
    "done": extracted["Done"] or None,
}))
return 0
```

The manifest delegates to this existing CLI at `capability.json:5-11`; do not add another resolver, parser, cache, retry, or install verifier.

---

### `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` (test, request-response)

**Analogs:** `TestResolveTaskContent` (lines 1205-1358) for public/adapter proof, and `TestCheckShipmdPatch` (lines 4802-4885, obtained through CodeGraph) for retained Patch 1 behavior.

**Public command plus internal argv spy** (lines 1230-1244 and 1287-1305):

```python
with mock.patch.object(sync, "run_bd", return_value=result, side_effect=side_effect) as run, \
     contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    code = sync.main(["resolve-task-content", self.ISSUE_ID])
...
self.assertEqual(run.call_args.args[0], ["bd", "show", self.ISSUE_ID, "--json"])
self.assertEqual(run.call_args.kwargs["timeout"], 8)
```

Extend this class for focused installed-cutover probes only if they can invoke the public router and vary one negative factor. Preserve the existing Phase 19 failure matrix instead of duplicating its timeout, envelope, type, duplicate-heading, and unusable-content cases.

**Fail-closed assertion shape** (lines 1238-1244):

```python
self.assertNotEqual(code, 0)
self.assertEqual(out, "")
self.assertNotIn("Implement the adapter.", out)
self.assertIn(token, err)
self.assertEqual(err.count("\n"), 1)
self.assertLessEqual(len(err), 2000)
```

Use this exact public-boundary assertion for each Phase 21 negative arm: unknown native id, real legacy pointer-only task, unavailable/failing `bd`, and malformed resolver stdout. Each arm starts from the known-good installed baseline and changes one factor only.

**Remove Patch 2-only tests; preserve the Patch 1 sibling tests** (lines 4888-5137):

```python
class TestCheckExecutePlanPatch(unittest.TestCase):
    ...
    exit_code = sync.main(
        ["check-patch", "execute-plan", "--path", str(execute_plan_md)]
    )

class TestPatchChecksTable(unittest.TestCase):
    self.assertEqual(len(sync.PATCH_CHECKS), 2)
    self.assertIn("ship-md", sync.PATCH_CHECKS)
    self.assertIn("execute-plan", sync.PATCH_CHECKS)
```

Delete the execute-plan class and all execute-plan table, CLI, lifecycle, and strip-gate assertions. Change only the mechanically inseparable table assertion to prove the retained `ship-md` entry; retain the `TestCheckShipmdPatch` body and the `ship-md` marker/message assertions byte-for-byte where possible. `TestCreateIssuesStripGate` at lines 1014-1100 is Patch-2-specific and must be retired with its production gate, rather than reworked into a new mechanism.

**Keep release-documentation assertions synchronized** (`TestTaskContentResolverManifest.test_release_docs_keep_source_availability_distinct_from_cutover`, lines 1383-1404): update only its expected current Phase 21 sentence after the README/CHANGELOG change. Preserve its distinction that tracked resolver availability is not installed byte-parity proof.

---

### `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` (operational documentation, file-I/O)

**Analog:** Patch 1 retention section, lines 43-160.

**Keep Patch 1's marker and operational record intact** (lines 114-124):

```markdown
<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->
<!-- /gsd-beads-patch:ship-pre-generic-dispatch v2 -->
```

**Patch 2 is the deletion inventory itself** (lines 188-205):

```markdown
Delete all four artifacts together: the marker-bracketed block ...,
this section, `sync.py`'s `check_execute_plan_patch()` ...,
and `beads-recall/SKILL.md`'s Step 3.5 call to `check-patch execute-plan`.
```

Remove the entire Patch 2 section and all Patch-2-only reapply/detector prose after the fresh D-04 gate succeeds. Retain the Patch 1 section and edit shared framing only as mechanically necessary so it no longer claims two active patches or tells operators to install, check, or restore Patch 2.

---

### `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md` (workflow instruction, event-driven)

**Analog:** surviving `ship-md` call in Step 3.5 (lines 77-104).

```bash
python3 "$SYNC_PY" check-patch ship-md
python3 "$SYNC_PY" check-patch execute-plan
```

Reduce this to the `ship-md` command and update the immediately associated explanation/anti-pattern text (lines 100-148) to describe only Patch 1. Preserve its source-location discovery pattern and diagnostic behavior; do not substitute a new detector or hard-code a runtime home.

---

### `capability.json` and `PRIME.md` (active configuration/integration guidance)

**Analogs:** each file's existing `beads.sync_mode` wording and `PRIME.md`'s `plan:pre` row. Change only those active Patch 2 claims: authoritative stripping is consumed through native task resolution; `plan:pre` runs the one surviving `ship-md` Patch 1 loss check. Preserve the resolver argv, enum/default, hook-driven no-strip boundary, and all unrelated manifest/PRIME content.

---

### `README.md` (operational documentation, request-response)

**Analog:** native resolver contract caveat, lines 174-186.

```markdown
The tracked Beads capability declares one native resolver ... It fails closed
with no PLAN.md fallback ...
...
Phase 21 owns exact tracked, project-installed, and global-installed byte
parity, installed cutover, and Patch 2 retirement.
```

Update this existing caveat in the same contract-focused voice to state the completed native cutover/retirement only after it is proven. Do not claim installed parity from tracked source alone and do not document an active Patch 2 workflow.

---

### `CHANGELOG.md` (release-history documentation, transform)

**Analog:** the current release's categorized entries, lines 3-8 and 52-91.

```markdown
## 0.5.0

### Added
- **Tracked `taskContentResolver` source contract.** ...
```

Append the current retirement fact under the current release using the existing `Added`/`Changed`/`Breaking` vocabulary as appropriate. Preserve earlier Patch 2 claims as historical statements; do not rewrite archived release history.

---

### Runtime-derived installed `execute-plan.md` workflow (runtime workflow configuration, file-I/O)

**Analog:** none in tracked source. The old Patch 2 block is documented at `GSD-CORE-PATCH.md:233-243`, but its actual installed path and bytes are volatile execution-time inputs.

Before retirement, derive the active path from runtime/installer output, capture its exact bytes in bounded `/dev/shm` evidence, and confirm byte-identical tracked, project-active, global-active, and exact-environment bootstrap/executed trees plus the positive/negative public matrix. Only then delete the marker-bracketed Patch 2 block. If a post-removal proof fails, restore exactly the captured bytes and emit `SPEC_FAILURE`; do not use a fallback.

## Shared Patterns

### Native resolver is the only public oracle

**Sources:** `capability.json:5-11`, `sync.py:676-782`, and `test_sync.py:1230-1305`.

```json
"trackerPrefix": "beads",
"binary": "python3",
"timeoutMs": 10000
```

Use `task resolve-content` for CUT-01/CUT-02 behavior and retain the focused `run_bd` spy to prove exact internal argv. Adapter-only success, parser tests, or a project-overlay result do not establish the installed cutover.

### Full-bundle parity through the existing installer seam

**Source:** `plugins/beads-lifecycle/hooks/capability-auto-install.sh:31-40,78-87`.

```bash
find "$BUNDLE_DIR" \( -type f -o -type d \) | LC_ALL=C sort
find "$BUNDLE_DIR" -type f | LC_ALL=C sort | while IFS= read -r _f; do cat "$_f"; done
...
gsd_tools capability install "$BUNDLE_DIR" --scope global --yes
```

Reuse its runtime-derived bundle root and whole-tree semantics, but prove all four observed trees: tracked source, project-active registry source, global-active registry source, and the bootstrap/executed bundle derived from the exact public-command `GSD_HOME`/`Path.home()` environment. Derive the bootstrap path without parsing the possibly stale pre-install global manifest; a missing/non-exact resolver declaration triggers this existing installer. Re-derive all four after install and assert the selected manifest resolves to the recorded executed `scripts/sync.py`; do not modify this hook or introduce another installer/verifier.

### One-factor, fail-closed negative evidence

**Source:** `test_sync.py:1238-1244,1342-1357`.

The known-good installed baseline is the control. For each negative arm, assert nonzero exit, empty stdout/no resolved object, and no fallback task content. Keep live installation and Beads data read-only; the required failure controls are runtime actions, not fixtures to commit.

### Patch 1 preservation is an independent regression gate

**Sources:** `sync.py:157-179,2869-2875`; `test_sync.py:4802-4885`; `skills/beads-status/SKILL.md:267-286`.

`check-patch ship-md` remains the one active check target. Keep its marker, table row, wrapper, tests, status skill, installer, manifest `ship:pre` slice, runtime workflow, and core Patch 1 documentation bytes. For the document, apply one identical normalizer bounded by enduring `## Patch 1:`/`## Probe (not a patch):`: pre-edit it removes the intervening Patch 2/shared-reapply interval; post-edit it hashes the whole interval. Exercise the checker after deletion rather than folding the mechanisms together.

## No Analog Found

| Target | Role | Data Flow | Reason |
|---|---|---|---|
| Runtime-derived installed Patch 2 workflow | runtime workflow configuration | file-I/O | It is machine-local mutable state, intentionally not a tracked repository source. Its exact path/bytes must be observed during the cutover transaction. |

## Metadata

**Analog search scope:** tracked capability source, tests, active capability skills/docs, installer hook, root README/changelog, and CodeGraph call paths.
**Files scanned:** 9 tracked files plus phase inputs and runtime-contract references.
**Pattern extraction date:** 2026-09-01
