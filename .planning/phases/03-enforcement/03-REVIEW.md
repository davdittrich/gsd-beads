---
phase: 03-enforcement
reviewed: 2026-08-15T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - .gsd/capabilities/beads/scripts/sync.py
  - .gsd/capabilities/beads/tests/test_sync.py
  - .gsd/capabilities/beads/capability.json
  - .gsd/capabilities/beads/skills/beads-status/SKILL.md
  - .gsd/capabilities/beads/GSD-CORE-PATCH.md
  - $HOME/.claude/gsd-core/workflows/ship.md
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-08-15T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed sync.py (the beads-capability's core script), its unit tests, capability.json's
step/gate declarations, the beads-status skill's orchestration prompt, and — with the extra
scrutiny the task requested — the machine-local ship.md patch (GSD-CORE-PATCH.md) plus the live,
already-patched `$HOME/.claude/gsd-core/workflows/ship.md`.

The patch mechanics check out: the marker (`<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->`
/ `<!-- /gsd-beads-patch:ship-pre-generic-dispatch v1 -->`) appears exactly once in the live
ship.md, and a byte-for-byte diff of GSD-CORE-PATCH.md's fenced "Patch Content (verbatim)" block
against the text between those markers in the live file is **identical** (confirmed
programmatically, not by eyeballing). `check_shipmd_patch`'s marker-substring check is a correct,
side-effect-free read.

However, the *purpose* of that staleness-detection mechanism does not survive scrutiny: its only
call site is unreachable in exactly the failure scenario it exists to catch (see CR-01). Beyond
that, sync.py has a handful of real quality/robustness gaps: an escaping inconsistency between two
markdown-table renderers where one of them feeds a re-parsed value into a subagent prompt, a
silent (unreported) epic-identity fallback that can fork a phase across multiple bd epics, a
narrower-than-necessary runtime-path assumption in the new patch-check subcommand, and a
YAML-parsing regex that silently drops multi-line `depends_on:` lists instead of erroring.

## Critical Issues

### CR-01: `check_shipmd_patch`'s self-check cannot fire in the scenario it exists to detect

**File:** `.gsd/capabilities/beads/scripts/sync.py:1049-1077`, `.gsd/capabilities/beads/skills/beads-status/SKILL.md:117-138`, `$HOME/.claude/gsd-core/workflows/ship.md` (steps 8-9, lines 157-242)

**Issue:** `check_shipmd_patch`'s own docstring states the reason it exists: "a future gsd-core
update or capability reinstall can silently overwrite that file and drop the patch with no error,
so this runs on every `ship:pre` dispatch." Its *only* call site is Step 2d of the `beads-status`
skill, and `beads-status` is *only* ever dispatched at `ship:pre` via the generic step-dispatch
loop that steps 8/9 of the patch itself install (unpatched `ship.md` has no other mechanism that
enumerates `kind == "step"` capability hooks at `ship:pre` — that gap is precisely
GSD-CORE-PATCH.md's stated motivation, and `ship_post_capability_dispatch` is a *different*
lifecycle point, `ship:post`).

Trace the failure mode the check is designed for: a `gsd-core` update (or capability reinstall)
overwrites `~/.claude/gsd-core/workflows/ship.md`, stripping the patch block. The next
`/gsd-ship` run loads the *fresh, unpatched* `ship.md` as its own instructions. That fresh copy no
longer contains step 9's dispatch loop, so `beads-status` is never invoked at `ship:pre` at all —
which means Step 2d, and therefore `check_shipmd_patch`, never runs, and the "⚠ ship.md ship:pre
… patch is missing" warning is never printed. The one scenario this diagnostic exists to catch is
exactly the scenario in which it cannot execute. Silently, `03-01`'s `blocking_open`/`diverged`
fields and `03-02`'s `ship_override` step stop being enforced — with zero visible signal to the
user, which is the exact regression Phase 3 exists to prevent (per GSD-CORE-PATCH.md's own "Why
this patch exists" section).

This is not a hypothetical: it is the single most likely real-world failure mode for a
machine-local patch to a file that `npx @opengsd/gsd-core@latest` (or any capability reinstall)
can overwrite outside this repository's control.

**Fix:** The check needs a call site that survives patch loss — it cannot live exclusively inside
the thing it is verifying. Two viable options, either is sufficient:
1. Add an independent trigger unrelated to `ship:pre` dispatch — e.g., have the `beads-sync`
   skill (registered at `plan:post`, already always dispatched when `beads.enabled`) or
   `beads-recall` (`plan:pre`) also call `sync.py check-shipmd-patch` and surface the warning
   there, so patch loss is caught well before a ship attempt, on a lifecycle point that does not
   depend on the patch under test.
2. Have `ship.md`'s own **unpatched** preflight (steps 1-7, which run regardless of the patch)
   independently probe for the marker's absence when `beads.enabled` — i.e., push the guard
   outside the thing being guarded, even if that means a small always-present stub in the
   unpatched file (a much smaller, more defensible upstream ask than the full dispatch loop).

Either way, document in GSD-CORE-PATCH.md that Step 2d is a *confirmation* of an intact patch, not
a *detector* of a lost one, until a patch-independent trigger exists.

## Warnings

### WR-01: `_render_beads_md_table` skips escaping that `_render_issue_table` applies, and the result is re-parsed into a subagent prompt

**File:** `.gsd/capabilities/beads/scripts/sync.py:823-850` (contrast `:602-617` and `:921-933`)

**Issue:** `_render_issue_table` (used by `beads_recall`) escapes `id`, `title`, and `status`
through `_escape_table_cell` before writing a markdown table cell — the comment on
`_escape_table_cell` explicitly frames this as a trust-boundary control (T-02-03: "issue
title/status text originates from a different principal … than the process rendering this
generated artifact"). `_render_beads_md_table` (used by `regenerate_beads_md`), however, only
escapes `title` and `status`; `issue_id` and the `blocked_by` cell (joined `depends_on_id`
values, sourced from the same `bd list --json` response) are interpolated raw:

```python
issue_id = str(row.get("id", ""))
...
blocked_by = ", ".join(
    str(dep.get("depends_on_id", ""))
    for dep in row.get("dependencies", []) or []
    if dep.get("type") == "blocks"
)
lines.append(
    f"| {issue_id} | {title} | {status} | {task_status} | {plan_task} | {blocked_by} |"
)
```

This table is not just for human reading: `_parse_beads_md_table_rows` (line 921) later
re-splits each row on `|` to reconstruct `{id, title, status}` for `render_wave_status_block`,
whose output is the `<beads_status>` block that SKILL.md's Step 2a instructs the orchestrator to
paste verbatim into every executor `Agent()` call's `prompt=` for the wave. An unescaped `|` or
embedded newline in a bd-supplied `id` or `depends_on_id` would shift table columns, corrupt the
re-parsed row, and inject attacker-influenced content directly into a spawned subagent's prompt —
the exact channel the code's own T-02-03 comment is trying to close, just not applied uniformly.

Today's exploitability is low (bd generates `id`/`depends_on_id` internally, they are not typically
free text a different principal can shape directly), but the inconsistency with the sibling
renderer, plus the fact that this specific table is the one that gets re-parsed into a prompt,
makes this worth closing rather than leaving as an asymmetry.

**Fix:**
```python
issue_id = _escape_table_cell(str(row.get("id", "")))
...
blocked_by = _escape_table_cell(
    ", ".join(
        str(dep.get("depends_on_id", ""))
        for dep in row.get("dependencies", []) or []
        if dep.get("type") == "blocks"
    )
)
```
(And update `_parse_beads_md_table_rows`'s consumers, or leave as-is — escaping only touches `|`
and newlines, so `_parse_beads_md_table_rows`'s `split("|")` on the now-guaranteed-pipe-free cell
values remains correct.)

### WR-02: Stale `beads_epic` fallback is silent — unlike the analogous stale-task-id path

**File:** `.gsd/capabilities/beads/scripts/sync.py:255-284`

**Issue:** `resolve_issue` (task level) explicitly reports a stale `<beads-id>` that no longer
resolves in bd via the `divergences` list, which `create_issues` prints (`divergence: task … not
found in bd`) — this is D-07's documented contract. `resolve_epic` has the same class of failure
one level up (a stored `beads_epic` in frontmatter that `bd show` can no longer find) but handles
it with **zero reporting**:

```python
m = BEADS_EPIC_RE.search(frontmatter)
if m:
    epic_id = m.group(1)
    check = run_bd(["bd", "show", epic_id, "--json"])
    if check.returncode == 0:
        return epic_id, False
    # stored epic id no longer resolves in bd -- fall through and create fresh
```

Because `resolve_phase_epic`'s sibling-plan lookup can itself resolve to the same
now-invalid epic id (every plan in the phase shares it, by design — D-05), a resync after an
external epic deletion doesn't just "heal" quietly: it can fork the phase across multiple epics
as different plans resync at different times, each landing on `create fresh` independently. Once
that happens, `bd list --parent <epic_id>` (which `regenerate_beads_md`/`ship_override` both key
off) only ever sees a subset of the phase's real issues, silently understating `blocking_open`
and `diverged` — the exact fields Phase 3's ship gate depends on for correctness.

**Fix:** Surface this the same way task-level divergence is surfaced — return a divergence signal
from `resolve_epic` and print it in `create_issues`, e.g.:
```python
print(f"divergence: stored beads_epic {epic_id!r} not found in bd -- creating a replacement epic")
```
so the split is at least visible in sync output, matching D-07's existing pattern instead of
introducing an unreported asymmetric case.

### WR-03: `check_shipmd_patch`'s default path ignores the multi-runtime resolution `ship.md` itself uses

**File:** `.gsd/capabilities/beads/scripts/sync.py:1056-1064`

**Issue:** `ship.md`'s own `initialize` step resolves `gsd-tools.cjs` across roughly 18 possible
runtime homes (`CLAUDE_CONFIG_DIR`, `HERMES_HOME`, `CURSOR_CONFIG_DIR`, `CODEX_HOME`,
`GEMINI_CONFIG_DIR`, `COPILOT_CONFIG_DIR`, `WINDSURF_CONFIG_DIR`, `AUGMENT_CONFIG_DIR`,
`TRAE_CONFIG_DIR`, `QWEN_CONFIG_DIR`, `CODEBUDDY_CONFIG_DIR`, `CLINE_CONFIG_DIR`,
`GROK_AGENTS_HOME`, `ANTIGRAVITY_CONFIG_DIR`, `OPENCODE_CONFIG_DIR`, `KILO_CONFIG_DIR`, …), because
`runtimeCompat.supported: ["*"]` in `capability.json` claims support for any of them. `sync.py`'s
`check_shipmd_patch`, by contrast, only checks one location:

```python
ship_md_path = (
    Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    / "gsd-core" / "workflows" / "ship.md"
)
```

On any runtime other than Claude whose actual `ship.md` lives under, say, `CODEX_HOME` or
`CURSOR_CONFIG_DIR`, this always reports "ship.md not found … cannot verify the local ship:pre
dispatch patch" (exit 1), even when that runtime's real `ship.md` is correctly patched — a false
negative that will confuse users on any non-Claude runtime this project otherwise claims to
support.

(GSD-CORE-PATCH.md itself scopes the *patch* only to `$HOME/.claude/…` — if that scoping is
intentional/Claude-only for now, the false-negative risk is only realized when a project opts to
run this capability under another runtime, but the check still reports success/failure with no
indication that only one of several possible install locations was probed.)

**Fix:** Either (a) reuse the same runtime-home resolution `ship.md`'s `initialize` step encodes
(factor it into one shared lookup both sides call), or (b) at minimum, have
`check_shipmd_patch`'s warning message name which path it checked and note that other runtime
homes were not probed, so a false negative doesn't read as a confirmed absence.

### WR-04: `parse_depends_on` silently drops multi-line YAML `depends_on:` lists

**File:** `.gsd/capabilities/beads/scripts/sync.py:31, 134-148`

**Issue:**
```python
DEPENDS_ON_RE = re.compile(r"^depends_on:\s*\[(.*?)\]\s*$", re.MULTILINE)
```
This regex requires `depends_on:`'s value to be a single-line, inline-bracket YAML flow sequence
(`depends_on: ["01-01"]` or `depends_on: []`) — every fixture and example in this codebase uses
that form. YAML also permits (and many tools/humans prefer) the block-list form:
```yaml
depends_on:
  - "01-01"
```
Because the regex has no `re.DOTALL` and anchors `$` to end-of-line, a block-list `depends_on:`
never matches. `parse_depends_on` returns `[]` in that case — indistinguishable from a
legitimately empty dependency list. There is no error, no warning, and no test exercising the
block-list form; the cross-plan dependency edge this frontmatter is meant to declare (the "sole
cross-plan edge source," per the function's own docstring) is silently dropped.

**Fix:** Either parse frontmatter with a real (minimal) YAML reader for this one key, or extend
the regex to also accept the block-list form and merge results, and add a test fixture using
block-list syntax so a future frontmatter generator that emits either style is covered:
```python
DEPENDS_ON_BLOCK_RE = re.compile(r"^depends_on:\s*\n((?:^\s*-\s*.+\n?)+)", re.MULTILINE)
```

## Info

### IN-01: `filter_open_ids` duplicates the `BEADS_RECALL_STATUSES` constant instead of reusing it

**File:** `.gsd/capabilities/beads/scripts/sync.py:23, 435-444`

**Issue:** `BEADS_RECALL_STATUSES = "open,in_progress,blocked,deferred"` is defined once at module
scope and used by `_beads_recall_argv`. `filter_open_ids` needs the identical value but
re-hardcodes the literal string instead of referencing the constant:
```python
result = run_bd(
    ["bd", "list", "--id", ",".join(ids), "--status", "open,in_progress,blocked,deferred", "--json"]
)
```
Today the two are consistent; nothing enforces they stay that way.

**Fix:** `"--status", BEADS_RECALL_STATUSES,`.

### IN-02: `BD_TIMEOUT` reused for an unrelated `git commit --amend` call

**File:** `.gsd/capabilities/beads/scripts/sync.py:21, 1022-1028`

**Issue:** `BD_TIMEOUT = 15  # seconds; bounded timeout on every bd subprocess call` is documented
as a `bd`-specific bound, but `ship_override` also passes it to the unrelated `git commit --amend`
call. The value (15s) is a reasonable timeout for a git amend too, so this isn't a functional bug,
but the name no longer describes every call site that uses it.

**Fix:** Either rename to a generic `SUBPROCESS_TIMEOUT`, or introduce a separate
`GIT_TIMEOUT` constant for clarity at the call site.

---

_Reviewed: 2026-08-15T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
