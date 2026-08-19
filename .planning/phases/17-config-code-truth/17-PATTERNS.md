# Phase 17: Config/Code Truth - Pattern Map

**Mapped:** 2026-08-20
**Files analyzed:** 4 (all requirements land in the same script + its config/test/doc twins)
**Analogs found:** 4 / 4 — this is a reconciliation phase; every analog is a sibling function or
sibling capability already in this repo/install, not an external pattern.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` (regex sites, TRUTH-04) | utility (regex/transform) | transform | `~/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` `PLAN_FILE_RE` | exact (same bug, already fixed in a sibling capability) |
| `sync.py` (patch-checker merge, TRUTH-02) | utility (diagnostic/CLI) | request-response | `sync.py check_shipmd_patch`/`check_execute_plan_patch` themselves — the two clones being merged, plus `LIFECYCLE_DISPATCH_POINTS` as the existing table-dispatch precedent | exact (self-analog: merge target is two existing siblings in the same file) |
| `sync.py` (`sync_mode` reader, TRUTH-01) + `capability.json` `beads.sync_mode` | config/utility | request-response | `sync.py:669-676` `read_epic_per`/`read_beads_enabled` over `read_beads_config` | exact |
| `sync.py` (native-dispatch strip gate, TRUTH-03/D-06) + `hooks/lifecycle-dispatch.sh` (unchanged, verify only) | middleware/dispatch | event-driven | `sync.py:679-758` `lifecycle_dispatch` (the `plan:post` `allow_strip=False` call already there) | role-match (same call, different call site) |
| `tests/test_sync.py` new cases | test | — | `class TestCheckExecutePlanPatch` (`tests/test_sync.py:2994`), specifically `test_cli_routes_through_main_and_returns_function_exit_code` (`:3060-3073`) | exact (this is the missing counterpart D-09 requires) |

## Pattern Assignments

### TRUTH-04 — decimal-phase regex widening

**Analog:** `~/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:34-37` (read this session, confirmed verbatim)

```python
# Phase segment widened to `\d+(?:\.\d+)?` (RESEARCH: beads' own
# `^(\d{2}-\d{2})-PLAN\.md$` is too narrow) so both `11-01-PLAN.md` and
# `10.1-02-PLAN.md` match.
PLAN_FILE_RE = re.compile(r"^\d+(?:\.\d+)?-\d+-PLAN\.md$")
```
Same file's ReDoS-discipline comment to copy verbatim as a rationale template:
```python
# Anchored, bounded, no nested quantifiers (ReDoS mitigation, RESEARCH
# Security Domain) -- every regex below follows this discipline.
```
Note: sota-numerics also drops the two-digit constraint entirely (`\d{2}-\d{2}` → `\d+-\d+`), which CONTEXT.md flags as "a deliberate choice to evaluate, not copy blindly" — beads' own `PLAN_FILE_RE` keeps the `-\d+` ordinal segment unconstrained already, so only the phase segment needs widening, not the ordinal.

**Beads' own three break sites (verified this session, exact text, no line drift from CONTEXT.md/RESEARCH.md):**

```python
# sync.py:72
PLAN_FILE_RE = re.compile(r"^(\d{2}-\d{2})-PLAN\.md$")
```
```python
# sync.py:634 (inside get_phase_header, sync.py:631-638)
pattern = re.compile(rf"^###\s+(Phase\s+0*{int(phase_num)}\s*:.*)$", re.MULTILINE)
```
```python
# sync.py:1489 (inside extract_phase_mentions, sync.py:1479-1505)
pattern = re.compile(
    rf"^###\s+Phase\s+0*{int(phase_num)}\s*:.*?(?=^###\s+Phase\s|\Z)",
    re.MULTILINE | re.DOTALL,
)
```
Both `get_phase_header` and `extract_phase_mentions` call `int(phase_num)` — this raises on `"01.5"` and is exactly what D-07 forbids reintroducing. The fix per D-07: strip a leading `"0"` from the phase-number **string**, then `re.escape()` it, keeping the existing `0*` regex prefix so `"01.5"` → `"1.5"` → escaped `"1\.5"` still matches `### Phase 01.5:` via the `0*` prefix.

---

### TRUTH-02 — patch-checker merge (both clone bodies, in full)

**Analog / merge target A:** `sync.py:2049-2111` — `check_shipmd_patch`

```python
def check_shipmd_patch(ship_md_path_override=None):
    """D-05 gap-closure diagnostic (03-03 Task 2): report whether the local
    `ship.md` patch (GSD-CORE-PATCH.md) is present in the installed,
    machine-local `ship.md` -- a future gsd-core update or capability
    reinstall can silently overwrite that file and drop the patch with no
    error. ...
    """
    if ship_md_path_override:
        ship_md_path = Path(ship_md_path_override)
    else:
        ship_md_path = (
            Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
            / "gsd-core"
            / "workflows"
            / "ship.md"
        )
    if not ship_md_path.exists():
        print(
            f"ship.md not found at {ship_md_path} -- cannot verify the local ship:pre dispatch "
            "patch (only this runtime home was probed; other runtime homes such as CODEX_HOME "
            "or CURSOR_CONFIG_DIR were not checked)"
        )
        return 1
    try:
        text = ship_md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(
            f"ship.md at {ship_md_path} could not be read ({exc}) -- cannot verify the "
            "local ship:pre dispatch patch"
        )
        return 1
    if SHIP_MD_PATCH_MARKER in text:
        print(f"ship.md ship:pre step-dispatch patch: present (v2) at {ship_md_path}")
        return 0
    print(
        f"⚠ ship.md's ship:pre generic STEP dispatch patch (beads, v2) is missing at "
        f"{ship_md_path} -- the ship_override step will not fire. The two ship:pre GATES are "
        "unaffected: gsd-core >= 1.11.0 dispatches those natively (#3559 / PR #3608). "
        "Reapply: see .gsd/capabilities/beads/GSD-CORE-PATCH.md"
    )
    return 1
```

**Analog / merge target B:** `sync.py:2114-2177` — `check_execute_plan_patch` (identical shape, different target/marker/version/messages)

```python
def check_execute_plan_patch(execute_plan_path_override=None):
    """D-05 gap-closure diagnostic (16-03 Task 1): report whether the
    machine-local `execute-plan.md` bd-task-read patch (GSD-CORE-PATCH.md)
    is present -- clone of check_shipmd_patch's structure immediately above,
    targeting gsd-core's `execute-plan.md` instead of `ship.md`. ...
    """
    if execute_plan_path_override:
        execute_plan_path = Path(execute_plan_path_override)
    else:
        execute_plan_path = (
            Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
            / "gsd-core"
            / "workflows"
            / "execute-plan.md"
        )
    if not execute_plan_path.exists():
        print(
            f"execute-plan.md not found at {execute_plan_path} -- cannot verify the local "
            "bd-task-read patch (only this runtime home was probed; other runtime homes such "
            "as CODEX_HOME or CURSOR_CONFIG_DIR were not checked)"
        )
        return 1
    try:
        text = execute_plan_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(
            f"execute-plan.md at {execute_plan_path} could not be read ({exc}) -- cannot "
            "verify the local bd-task-read patch"
        )
        return 1
    if EXECUTE_PLAN_PATCH_MARKER in text:
        print(f"execute-plan.md bd-task-read patch: present (v1) at {execute_plan_path}")
        return 0
    print(
        f"⚠ execute-plan.md's bd-task-read patch (beads) is missing at {execute_plan_path} -- "
        "gsd-executor will not read task content from bd. "
        "Reapply: see .gsd/capabilities/beads/GSD-CORE-PATCH.md"
    )
    return 1
```

**Exactly what differs between the two bodies** (the table's four columns per D-10, all four confirmed by direct read):
| | ship-md | execute-plan |
|---|---|---|
| target filename | `ship.md` | `execute-plan.md` |
| marker constant | `SHIP_MD_PATCH_MARKER` (`sync.py:110`) | `EXECUTE_PLAN_PATCH_MARKER` (`sync.py:115`) |
| marker version | v2 | v1 |
| "not found" message tail | "cannot verify the local ship:pre dispatch patch" | "cannot verify the local bd-task-read patch" |
| "could not be read" message tail | same as above (ship:pre dispatch patch) | same as above (bd-task-read patch) |
| "present" message | `"ship.md ship:pre step-dispatch patch: present (v2) at {path}"` | `"execute-plan.md bd-task-read patch: present (v1) at {path}"` |
| "missing" consequence message | `"the ship_override step will not fire. The two ship:pre GATES are unaffected: ..."` | `"gsd-executor will not read task content from bd."` |

**Existing table-dispatch precedent to imitate (not invent):** `sync.py:679-758` `lifecycle_dispatch`, which dispatches on `LIFECYCLE_DISPATCH_POINTS` (`sync.py:121-127`, a plain tuple, not a dict) via an `if/elif` chain, not a dict-of-callables — this repo's existing dispatch idiom for a **small, fixed** set of variants is `if point == "x": ...` chains keyed off a module-level tuple/dict of literal names, not a registry/decorator pattern. The merged patch-checker's `PATCH_CHECKS` table (RESEARCH.md Pattern 1 skeleton) should follow this same "plain dict/tuple of literals, no framework" idiom.

**CLI surface to preserve (both flags, same names — D-08 requires zero regression):** `sync.py:2219-2228` (argparse), `sync.py:2263-2266` (dispatch):
```python
# sync.py:2219-2228
check_shipmd_patch_p = sub.add_parser(
    "check-shipmd-patch",
    help="Report whether the local ship.md ship:pre dispatch patch (GSD-CORE-PATCH.md) is present",
)
check_shipmd_patch_p.add_argument("--ship-md-path", default=None)
check_execute_plan_patch_p = sub.add_parser(
    "check-execute-plan-patch",
    help="Report whether the local execute-plan.md bd-task-read patch (GSD-CORE-PATCH.md) is present",
)
check_execute_plan_patch_p.add_argument("--execute-plan-path", default=None)
```
```python
# sync.py:2263-2266
if args.command == "check-shipmd-patch":
    return check_shipmd_patch(args.ship_md_path)
if args.command == "check-execute-plan-patch":
    return check_execute_plan_patch(args.execute_plan_path)
```
D-08 replaces this pair with one parameterized verb — CONTEXT.md leaves the exact shape (positional target vs. flag, per-target path override spelling) to Claude's discretion, constrained by: same-commit caller updates at `beads-recall/SKILL.md:72-73`, `beads-status/SKILL.md:146`, `GSD-CORE-PATCH.md` (4 mentions), `.planning/intel/API-SURFACE.md:55-58` (regenerate).

**Call sites inside `sync.py` itself that must keep working post-merge:**
```python
# sync.py:737-738, inside lifecycle_dispatch's plan:pre branch
check_shipmd_patch()
check_execute_plan_patch()
```

---

### TRUTH-02 test analog (D-09 — add BEFORE the merge)

**Analog:** `tests/test_sync.py:2994` `class TestCheckExecutePlanPatch(unittest.TestCase)`, specifically the CLI-level test at `tests/test_sync.py:3060-3073` (`test_cli_routes_through_main_and_returns_function_exit_code`) — confirmed exact line range, no drift from RESEARCH.md's citation:

```python
def test_cli_routes_through_main_and_returns_function_exit_code(self):
    with tempfile.TemporaryDirectory() as tmp:
        execute_plan_md = Path(tmp) / "execute-plan.md"
        execute_plan_md.write_text(
            f"{sync.EXECUTE_PLAN_PATCH_MARKER}\n", encoding="utf-8"
        )
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            exit_code = sync.main(
                ["check-execute-plan-patch", "--execute-plan-path", str(execute_plan_md)]
            )

    self.assertEqual(exit_code, 0)
    self.assertIn("present", captured.getvalue())
```
`grep -c "ship.md.path\|ship_md_path" tests/test_sync.py` returns zero matches in the current tree (re-confirmed this session) — there is no `check-shipmd-patch` counterpart to this test anywhere in the 4129-line file. D-09's required new test is this exact shape, target-swapped to `sync.SHIP_MD_PATCH_MARKER` / `"check-shipmd-patch"` / `"--ship-md-path"`, added to a sibling `TestCheckShipmdPatch`-style class (naming convention: `TestCheck<TargetPascalCase>Patch`, matching `TestCheckExecutePlanPatch`) **before** the D-08 merge lands, so the merge is red/green-cycled against it.

D-10's new test (marker-version literal-string assertion) has no existing analog — no current test asserts literal marker text, only presence/absence via `assertIn`/`assertEqual(exit_code, ...)`. Model it on the same class's setup (`tempfile.TemporaryDirectory`, `write_text(f"{sync.MARKER}\n")`, `contextlib.redirect_stdout`) but assert `sync.SHIP_MD_PATCH_MARKER == "<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->"` and `sync.EXECUTE_PLAN_PATCH_MARKER == "<!-- gsd-beads-patch:execute-plan-bd-task-read v1 -->"` directly, or the merged table's per-entry `version` field.

---

### TRUTH-01 — `sync_mode` self-read (config)

**Analog:** `sync.py:641-676` (read this session, exact text) — the helper plus its two existing one-line callers:

```python
def read_beads_config(project_root, key, default):
    """Return `beads.<key>` read fresh from `.planning/config.json`, falling
    back to `default` when the file is absent, unreadable, malformed, carries
    no `beads` object, carries no such key, or carries a value of the wrong
    type -- a wrong-typed value returns the default rather than a truthiness
    guess, so `{"enabled": "false"}` cannot silently disable tracking.
    ...
    """
    try:
        cfg = json.loads(
            confined(project_root, ".planning", "config.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default
    beads_cfg = cfg.get("beads") if isinstance(cfg, dict) else None
    if not isinstance(beads_cfg, dict):
        return default
    value = beads_cfg.get(key, default)
    return value if isinstance(value, type(default)) else default


# The two accessors below exist so each shipped default is written down exactly
# once, next to the key it belongs to, and matches capability.json's `config`
# block. Inlining them would scatter the defaults across call sites.
def read_epic_per(project_root):
    """B14/D-11: `beads.epic_per`, default `"phase"`."""
    return read_beads_config(project_root, "epic_per", "phase")


def read_beads_enabled(project_root):
    """gh-2: `beads.enabled`, default `True` (capability.json since 0.2.0)."""
    return read_beads_config(project_root, "enabled", True)
```

New reader to add, same shape (RESEARCH.md Pattern 2, verified line numbers match):
```python
def read_sync_mode(project_root):
    return read_beads_config(project_root, "sync_mode", "authoritative")
```
Note the wrong-type fallback: `isinstance(value, type(default))` — since `default="authoritative"` is a `str`, any non-string stored value (e.g. accidentally `123`) falls back to `"authoritative"`, not the removed `"off"`. The D-04 detection-channel notice (see TRUTH-03 below, `plan:pre`) is the only place an on-disk `"off"` string becomes observable, since `read_sync_mode` itself has no enum validation on read (confirmed: `read_beads_config` does a plain dict lookup + type check, no `values` re-check).

**`capability.json` current declaration to narrow (D-01):**
```json
// capability.json:32-41 (read this session, exact text)
"beads.sync_mode": {
  "type": "enum",
  "values": [
    "authoritative",
    "mirror",
    "off"
  ],
  "default": "authoritative",
  "description": "authoritative (default): bd owns task status and task content (title/description) after first sync. Content originates in PLAN.md at first sync, but PLAN.md task text is never re-synced from later bd edits (D-01). 'mirror' and 'off' are reserved for later phases."
}
```
D-01 changes `values` to `["authoritative", "mirror"]` and D-02 requires the `description` stop claiming "reserved for later phases" once `mirror` is implemented — this is the exact "false claim" TRUTH-01's doc sweep targets. Sibling declaration for comparison (unchanged, same block, same file): `capability.json:47-55` `beads.epic_per`.

**Where `create_issues`'s existing comment must be corrected in the same commit** (currently a true statement that becomes false once `sync_mode` is wired) — `sync.py:1300-1302`:
```python
# Note the strip is NOT gated on `beads.sync_mode` -- that key is declared in
# capability.json and read by nothing (gsd-beads-v43). The only
# gate is `check_execute_plan_patch()` below, plus this flag.
```

---

### TRUTH-03 — hook forward-compat (D-05 probe) and native-dispatch strip gate (D-06)

**Analog for the D-05 probe's shape:** `check_shipmd_patch`'s "read-only, fail-open, name-the-path-checked" discipline (excerpted in full above) — same three-case return contract (missing file → 1, unreadable → 1, marker present/absent → 0/1), same `os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))` path-resolution idiom, but probing `plan-phase.md`/`verify-work.md` for #3687's generic-dispatch prose instead of a local-patch marker. RESEARCH.md's Open Question 2 recommends this stay a **separate function**, not a third `PATCH_CHECKS` table entry — different semantics (upstream-now-native is good; local-patch-missing is bad) — cite that reasoning in the plan rather than re-deciding it.

**Existing `plan:pre` dispatch site where the probe's two call sites already live (pattern to extend, not replace):** `sync.py:728-738`, inside `lifecycle_dispatch`:
```python
if point == "plan:pre":
    beads_recall(str(phase_dir))
    # The patch-loss detector documented in beads-recall/SKILL.md's
    # Step 3.5. ...
    check_shipmd_patch()
    check_execute_plan_patch()
```

**D-06's exact native-dispatch call site to change** — `sync.py:2249-2250`, currently hardcoded `allow_strip=True` (the argument is simply omitted, so `create_issues`'s default applies):
```python
if args.command == "create-issues":
    return create_issues(args.plan_path)
```
`create_issues`'s signature to gate against (`sync.py:1291`):
```python
def create_issues(plan_arg, allow_strip=True):
```
RESEARCH.md's Open Question 1 recommends computing `allow_strip` internally at this dispatch line via `read_sync_mode(project_root) != "mirror"` (no new CLI flag) rather than adding a `--allow-strip` argparse flag — cite this recommendation in the plan; it requires zero change to `beads-sync/SKILL.md`'s Step 3 invocation.

**D-03's contrasting, unchanged hardcode (the hook must NOT gain this gating)** — `sync.py:748-749`, inside the same `lifecycle_dispatch`'s `plan:post` branch:
```python
elif point == "plan:post":
    ...
    for plan_id in sorted(plans):
        create_issues(str(plans[plan_id]), allow_strip=False)
```
This is the analog proving the asymmetry D-03 mandates: the hook path (`lifecycle_dispatch`) keeps the literal `False`; only the native-dispatch CLI path (`main`'s `create-issues` branch) reads config.

**Hook file (verify-only — TRUTH-03 does not require editing this, per CONTEXT.md's "Reworking the lifecycle-dispatch hook matcher" being explicitly out of scope):** `plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh` — the `POINTS` tuple (`"plan:pre", "plan:post", "execute:wave:pre", "execute:wave:post", "verify:post"`) inside its embedded python3 block mirrors `sync.py:121-127`'s `LIFECYCLE_DISPATCH_POINTS` exactly, per the comment at `sync.py:118-120` ("`hooks/lifecycle-dispatch.sh` carries the same list: any change here must be mirrored there"). No new point is added by this phase, so no hook edit is required — only confirm this invariant still holds after TRUTH-03 lands.

**`LIFECYCLE_DISPATCH_POINTS` (the table this phase's probe function does NOT join — a separate concern per Open Question 2):**
```python
# sync.py:121-127
LIFECYCLE_DISPATCH_POINTS = (
    "plan:pre",
    "plan:post",
    "execute:wave:pre",
    "execute:wave:post",
    "verify:post",
)
```

## Shared Patterns

### Fail-open / never-raise discipline
**Source:** `sync.py:2081-2101` (`check_shipmd_patch`'s missing-file/unreadable-file guards) and `sync.py:756-757` (`lifecycle_dispatch`'s outer `except Exception`)
**Apply to:** the D-05 probe function, the merged `PATCH_CHECKS` reader, and any new `read_sync_mode`-driven branch — every lifecycle hook is `onError: "skip"` and `lifecycle_dispatch` always returns 0; nothing added in this phase may raise out of that function.

### Config self-read, never declarative wiring
**Source:** `sync.py:641-676` (`read_beads_config` + its two callers)
**Apply to:** `read_sync_mode` (TRUTH-01) and the D-06 native-dispatch strip-gate read (TRUTH-03) — `capability.json`'s `config` block has no delivery channel to any step (verified: `configValues`/`when:`/`config-equals` are all structurally unreachable for a `kind: "step"` skill per RESEARCH.md's Alternatives Considered table); every behavioral consumer must call this helper directly.

### Read-only, name-the-exact-path-checked diagnostics
**Source:** `check_shipmd_patch`/`check_execute_plan_patch` (both excerpted in full above)
**Apply to:** the D-05 upstream-native-dispatch probe — same `CLAUDE_CONFIG_DIR` resolution, same three-case return contract, same "never edits the target" invariant, same discipline of naming the exact path probed so a report never reads as "checked everywhere" when only the Claude runtime home was checked (WR-03).

### Marker substring check, never regex, for patch presence
**Source:** `sync.py:2102`/`sync.py:2169` (`if SHIP_MD_PATCH_MARKER in text:` / `if EXECUTE_PLAN_PATCH_MARKER in text:`)
**Apply to:** the merged `PATCH_CHECKS` table's per-entry check and the D-05 probe's generic-dispatch-text detection — plain `in` substring check against a literal string constant, never a regex (the markers/probe text are fixed literals, not patterns).

## No Analog Found

None — every file/function touched by this phase's four requirements has a direct, already-read sibling in this repo or a sibling capability install on the same machine (RESEARCH.md's "Don't Hand-Roll" table makes the same claim independently). The only genuinely novel piece is D-04's migration-notice mechanism (no passive gsd-core channel exists per RESEARCH.md's Detection Channel Analysis) — RESEARCH.md's own recommendation (a `plan:pre`-scoped notice via the same `hookSpecificOutput.additionalContext` channel the hook already promotes stdout through) is advisory, not a locked analog, since CONTEXT.md D-04 leaves the exact shape to Claude's discretion.

## Metadata

**Analog search scope:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` (2286 lines, all four requirements), `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`, `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` (4129 lines), `plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh`, `~/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (sibling capability install, read-only reference)
**Files scanned:** 5 read in full/targeted-section; zero external codebase search needed (all analogs are same-repo or same-machine sibling installs, per phase's reconciliation framing)
**Pattern extraction date:** 2026-08-20
**Line-number drift found vs. CONTEXT.md/RESEARCH.md:** none — every cited line (`sync.py:72, 110, 115, 121-127, 634, 641-676, 679-758, 1291, 1300-1302, 1479-1505, 1489, 2049-2111, 2114-2177, 2180-2266, 2219-2228, 2249-2250, 2263-2266`; `capability.json:27-56`; `tests/test_sync.py:2994, 3060-3073`) was re-verified against the current working tree and matches exactly.
