# Phase 18: Address tech-debt (patch-check doc accuracy + CHANGELOG) - Pattern Map

**Mapped:** 2026-08-20
**Files analyzed:** 8 (all edits to existing files; no new files)
**Analogs found:** 8 / 8 (self-analogous — every file's own current content is the pattern to extend)

This phase creates no new files. Every D-0x item is a targeted edit inside a file that already
contains the pattern being extended (docstring correction, table entry edit, doc-instruction
broadening, changelog entry, version bump). "Analog" below means the exact existing
structure/convention the edit must match, not a different file to imitate.

## File Classification

| File | Role | Data Flow | Pattern Source (self) | Match Quality |
|------|------|-----------|------------------------|---------------|
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` (docstring, ~802-822) | utility (docstring) | N/A | same file's `check_patch` docstring (2285-2295) | exact — sibling docstring in same module, same function-doc convention |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` (`PATCH_CHECKS`, 136-179) | config/table | CRUD (table entries) | `missing_msg`'s existing `"⚠ {filename}..."` prefix convention, same table | exact — extending an established key convention within the same dict |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` (`check_patch` final print, 2320-2322) | utility | request-response | inline comment convention used elsewhere in file (e.g. line 2306-2308 `# WR-02/CR-02:` comment) | exact — same file's inline-comment-above-line style |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md` (Step 3.5, ~76-81) | doc/instruction | event-driven (agent instruction) | same file's own prose instruction block | exact |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md` (Step 2d, ~145-149) | doc/instruction | event-driven | same file's own prose instruction block, near-duplicate of beads-recall's | exact |
| `CHANGELOG.md` (0.4.0 section, 1-38; 0.3.1 `### Performance`, 68-75) | doc | N/A | same file's existing entry style (bolded one-line summary + supporting prose, `###` category headers) | exact |
| `plugins/beads-lifecycle/.claude-plugin/plugin.json` | config | N/A | same file's `"version"` field | exact |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` | doc | N/A | same file's existing section style (numbered reasons, prose register) | exact |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` (`TestPatchChecksTable`, 3376+) | test | request-response (unit) | same class's existing assertion style (`assertIn`/`assertEqual` against captured stdout) | exact |

## Pattern Assignments

### D-01/D-02 — `sync.py` docstring + comment (target lines ~790-822, ~2285-2322)

**Current docstring to rewrite** (`sync.py:802-807`, verbatim, confirmed via Read):
```python
def check_sync_mode_value(project_root):
    """17-03 Task 2 (D-04 Case 2): read-only, never-raises notice for a
    ...
    Prints to STDOUT -- the opposite of `check_shipmd_patch`/
    `check_execute_plan_patch`'s stderr-only benign-skip convention.
    `hooks/lifecycle-dispatch.sh` promotes only stdout into
    `additionalContext`; ...
```
This is FALSE per D-01 — `check_patch` (which both wrappers thin-wrap, confirmed at
`sync.py:2296-2322`) prints all four message paths to stdout unconditionally via
`print(entry["not_found_msg"]...)`, `print(entry["could_not_read_msg"]...)`, and the final
`print(fmt...)` covering both `present_msg`/`missing_msg` — there is no stderr path anywhere in
`check_patch`. Fix: replace "the opposite of ... stderr-only benign-skip convention" with
language stating `check_patch`/its wrappers **also** print to stdout unconditionally, same as
this function — drop the "opposite" framing entirely.

**Sibling docstring convention to match** (`check_patch`, `sync.py:2286-2295`):
```python
def check_patch(target, path_override=None):
    """17-04 Task 3 (TRUTH-02): the one reader PATCH_CHECKS parameterizes,
    replacing check_shipmd_patch's and check_execute_plan_patch's identical
    bodies. Preserves the three-case return contract (not-found /
    could-not-read / marker present-or-missing), the `CLAUDE_CONFIG_DIR`
    idiom, and naming the exact path probed in every message (WR-03).
    Read-only. Total by construction (T-17-04-02): both checks run inside
    `lifecycle_dispatch`'s one `try/except` alongside `beads_recall`, so an
    unrecognized `target` fails open like an unreadable file rather than
    raising -- but names the unknown target so the two cases stay separable.
    """
```
Use this docstring's register (task-ref prefix, terse behavior statement, no marketing) as the
model for the D-01 rewrite.

**Final print call to pin with D-02 comment** (`sync.py:2320-2322`, verbatim):
```python
    present = entry["marker"] in text
    fmt = entry["present_msg"] if present else entry["missing_msg"]
    print(fmt.format(filename=entry["filename"], path=path, version=entry["version"]))
    return 0 if present else 1
```
**Inline-comment convention to copy** (existing precedent at `sync.py:2306-2308`, same function):
```python
    # WR-02/CR-02: degrade to "cannot verify" rather than raise -- an
    # uncaught exception here would abort create_issues before
    # plan_path.write_text runs (execute-plan target).
```
D-02's new comment goes directly above the final `print(fmt...)` line, same one-line-prefixed
`# WR-01:` style: e.g. `# WR-01: stdout is deliberate; the hook promotes only stdout.`

---

### D-03.1 — `PATCH_CHECKS` message prefixes (`sync.py:136-179`)

**Existing `⚠` convention already present** on `missing_msg` (both entries, confirmed verbatim
above):
```python
        "missing_msg": (
            "⚠ {filename}'s ship:pre generic STEP dispatch patch (beads, {version}) is "
            ...
        ),
```
```python
        "missing_msg": (
            "⚠ {filename}'s bd-task-read patch (beads) is missing at {path} -- "
            ...
        ),
```
**Fields to prefix** (currently un-prefixed, both entries — verbatim current text):
```python
        "not_found_msg": (
            "{filename} not found at {path} -- cannot verify the local ship:pre dispatch "
            "patch (only this runtime home was probed; other runtime homes such as "
            "CODEX_HOME or CURSOR_CONFIG_DIR were not checked)"
        ),
        "could_not_read_msg": (
            "{filename} at {path} could not be read ({exc}) -- cannot verify the "
            "local ship:pre dispatch patch"
        ),
```
(and the execute-plan entry's parallel two fields at lines ~163-170). Fix: prepend `"⚠ "` to
each of the 4 templates' leading `"{filename}..."` string, matching `missing_msg`'s existing
`"⚠ {filename}'s..."` shape exactly (same `⚠ ` + space + `{filename}` pattern, no other
reformatting).

**Table-wide comment already documenting this idiom** (`sync.py:130-135`, do not disturb):
```python
# 17-04 Task 3 (D-08/D-10): the table `check_patch` walks -- a plain dict of
# literals keyed by target name (this module's existing small-fixed-variant
# idiom, LIFECYCLE_DISPATCH_POINTS below; no registry/decorator/class). Each
# entry's own `version` matters: the two markers are independently versioned
# (v2 vs v1), so one shared field would let a bump to one silently apply to
# both. The `*_msg` fields are the exact pre-merge message templates.
```

---

### D-03.2 — SKILL.md instruction broadening

**`beads-recall/SKILL.md:76-81` current text** (verbatim, confirmed via Read):
```markdown
If either output contains the "⚠" warning line, surface it to the user verbatim -- never swallow
it -- but never block planning on either; both are diagnostic only, matching the `onError: skip`
this entire beads-recall `plan:pre` dispatch already runs under.
```
**`beads-status/SKILL.md:148-149` current text** (verbatim, near-duplicate structure):
```markdown
If its output contains the "⚠" warning line, surface it to the user verbatim -- never swallow it
-- but never block shipping on it; this is diagnostic only, matching the `onError: skip` this
entire beads-status `ship:pre` dispatch already runs under.
```
Fix (both files, same edit shape): replace `contains the "⚠" warning line` with an exit-code- or
absence-of-`"present"`-keyed condition — e.g. "the command exits non-zero (or its output does not
contain the string `present`)" — per D-03's robustness requirement. `check_patch` already returns
`0 if present else 1` (confirmed `sync.py:2322`), so exit code is a reliable existing signal to
key off; no code change needed to support this, only the doc instruction.

---

### D-04/D-05 — `CHANGELOG.md`

**0.4.0 section entry-style to match** (`CHANGELOG.md:6-13`, `### Fixed` bullet, verbatim
opening as a model for register/format):
```markdown
### Fixed
- **A decimal-numbered phase (`1.5`, `01.5`, `10.1`, `11.1` — the form `/gsd-phase --insert`
  produces) failed silently at every beads lifecycle point.** `PLAN_FILE_RE` never matched a
  ...
```
Bold one-sentence summary, then supporting prose paragraph, matches project's changelog voice.
D-04's new entry (TRUTH-03: `check_native_step_dispatch`, its two module constants, the
`plan:post`/`verify:post` stand-down mechanism, naming PR #3687 the way `GSD-CORE-PATCH.md`
already does) should go under `### Added` or `### Changed` in the existing 0.4.0 section using
this same bold-summary-then-prose shape.

**0.3.1 `### Performance` section, entry to relocate** (`CHANGELOG.md:68-75`, verbatim):
```markdown
### Performance
- **The hook no longer starts a Python interpreter on every Bash tool call.** ...
  spawn: **13.00 ms → 0.91 ms** per non-matching call. `LC_ALL=C` matters because PostToolUse
  payloads carry the tool's full output — on a 4 MB payload, UTF-8 pattern matching alone cost
  ~34 ms. Also merged two JSON parses into one. Separately, the hook's own timeout is set
  explicitly to 120 s — a deliberate reduction from Claude Code's 600 s default hook timeout,
  bounding the hook's own worst-case blocking time; this is not itself a throughput
  optimization and does not belong under this heading's ms/call numbers above.
```
D-05: split the 120s-timeout sentence (`"Separately, the hook's own timeout is set explicitly
to 120 s — a deliberate reduction..."`) out of this `### Performance` bullet into its own bullet
under `### Fixed` or `### Changed` in the same 0.3.1 section — the sentence's own text already
argues it is misfiled; move it verbatim (or lightly reworded to stand alone) rather than
rewriting the reasoning.

---

### D-06 — `plugin.json` version bump

**Current file** (verbatim, confirmed via Read):
```json
{
  "name": "beads-lifecycle",
  "version": "1.3.1",
  "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle",
  "author": {
    "name": "Dennis A. V. Dittrich",
    "email": "davdittrich@gmail.com"
  },
  "license": "MIT",
  "skills": ["./.agents/skills/beads"]
}
```
Single-line edit: change `"version": "1.3.1"` to the new value (planner's call, minor vs.
patch — Phase 17's TRUTH-01..04 work plus the `SHIP_MD_PATCH_MARKER` v1→v2 change are
behavioral, favoring a minor bump per semver convention already used by `capability.json`'s
`0.3.1` → `0.4.0` jump for comparable scope).

---

### D-08.3 — `GSD-CORE-PATCH.md` reapply-mechanism naming

**Existing section-style to extend** (`GSD-CORE-PATCH.md:1-9`, register to match — numbered
reasons, precise cross-references, no marketing prose):
```markdown
# Local gsd-core patches (machine-local, this project)

A register of every local, marker-bracketed patch this machine carries to an installed
`gsd-core` workflow file. ...
```
Add a subsection (or extend an existing one) naming `verify-reapply-patches.cjs` and the
`sync.py check-patch <target>` verbs as the reapply-verification mechanism — same
numbered-reasons prose style seen in "Scope: why there are only two patches, not six" (lines
11-30) as the closest structural analog for a new explanatory subsection.

---

### D-03 test coverage — `tests/test_sync.py::TestPatchChecksTable`

**Existing assertion pattern to extend** (`test_sync.py:3421-3441`, verbatim, the class's
established style for pinning message content against captured stdout):
```python
    def test_ship_md_missing_message_names_ship_pre_gates_unaffected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            ship_md.write_text("no patch marker in this file\n", encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_shipmd_patch(str(ship_md))
        out = captured.getvalue()
        self.assertIn("ship_override step will not fire", out)
        self.assertIn("ship:pre GATES are", out)
        self.assertIn("unaffected", out)
```
New/updated tests for D-03's `⚠` prefix on `not_found_msg`/`could_not_read_msg` should follow
this exact shape: `tempfile.TemporaryDirectory()`, `contextlib.redirect_stdout`, then
`assertIn("⚠", out)` (or `assertTrue(out.startswith("⚠"))`) for the not-found and
could-not-read cases, one test per target (ship-md, execute-plan) per the class's own stated
convention ("Separate ... so a merge that collapses both ... strings into one shared sentence
cannot pass this test on the other target's wording" — same rationale at lines 3438-3440
applies to the new prefix tests).

**Class docstring for context** (`test_sync.py:3376-3384`, explains why these tests exist and
must not regress):
```python
class TestPatchChecksTable(unittest.TestCase):
    """17-04 Task 1 (D-09/D-10): pre-merge coverage pinning the exact literal
    marker strings, the per-entry version tokens in each present message, and
    the consequence text in each missing message -- the blind spot commit
    `966315a` exploited (moving SHIP_MD_PATCH_MARKER v1 -> v2 with the suite
    still reporting 164/164 green, because no test asserted either marker's
    literal string). ...
```

## Shared Patterns

### Doc-sweep-in-same-commit
**Source:** CONTEXT.md's `<code_context>` section, citing Phase 17's TRUTH-01 plan precedent.
**Apply to:** D-01/D-02 (sync.py) must land in the same commit as any SKILL.md text that
references `check_sync_mode_value`'s behavior (none currently do, but verify during execution);
D-03's `sync.py` table edit and both SKILL.md edits are one logical change and should land
together.

### Test-per-behavior-change discipline
**Source:** WR-04/WR-05 resolution commits `373e7fb`, `0f8decb` (cited in CONTEXT.md), and the
`TestPatchChecksTable` class itself (`test_sync.py:3376+`).
**Apply to:** D-03's message-template prefix change — extend `TestPatchChecksTable` with
RED-then-GREEN assertions before/after adding the `⚠` prefix, matching the existing
`assertIn`/`captured.getvalue()` idiom shown above. No new test file or class needed — this is
the same class, same file, same fixtures (`tempfile.TemporaryDirectory`,
`contextlib.redirect_stdout`).

### Inline task-ref comment convention
**Source:** `sync.py:130-135` (`# 17-04 Task 3 (D-08/D-10): ...`) and `sync.py:2306-2308`
(`# WR-02/CR-02: ...`).
**Apply to:** D-02's new pinning comment on `check_patch`'s final print — use the same
`# WR-01: <terse statement>` one-to-three-line comment shape, not a docstring-style block.

## No Analog Found

None — every file in scope already exists with an established internal convention (docstring
style, table-entry shape, doc-instruction prose, changelog entry format, JSON version field,
test-class assertion idiom) that the edit extends. D-07 (tag deletion), D-08.1/.2/.4 (local
machine patch reapply + verification), and D-09 (bd issue reconciliation) are git/CLI/`bd`
operations, not source-file edits, and have no code pattern to map — they follow
`GSD-CORE-PATCH.md`'s own "Patch Content (verbatim)" sections (for D-08.1) and the
`reconcile-stale-closed` mechanism already used for the 4 stale Phase 14 issues (for D-09, per
CONTEXT.md's own citation — no separate analog search needed, CONTEXT.md already names the exact
precedent command).

## Metadata

**Analog search scope:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`,
`plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`,
`plugins/beads-lifecycle/.gsd/capabilities/beads/skills/{beads-recall,beads-status}/SKILL.md`,
`CHANGELOG.md`, `plugins/beads-lifecycle/.claude-plugin/plugin.json`,
`plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md`.
**Files scanned:** 8 (all in scope, all read directly — no broader search needed since
CONTEXT.md's canonical_refs already pin every file:line location).
**Pattern extraction date:** 2026-08-20
</content>
