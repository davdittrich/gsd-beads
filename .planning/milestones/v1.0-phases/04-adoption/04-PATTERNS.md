# Phase 4: Adoption - Pattern Map

**Mapped:** 2026-08-15
**Files analyzed:** 6 (1 heavily-modified script, 1 modified config manifest, 1 new/extended
skill dispatch decision, 1 new skill, 1 modified test file, 2 new fixture files)
**Analogs found:** 6 / 6 (all analogs are in-file — this capability is one script + one manifest +
three skill files + one test file; there is no separate codebase to search outside
`.gsd/capabilities/beads/`)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.gsd/capabilities/beads/scripts/sync.py` — `migrate_todos()` + helpers (new function) | service (CLI subcommand handler) | file-I/O → CRUD (todo file parse → `bd create` → file delete) | `sync.py:create_issues()` (lines 535-625) | exact — same fail-open shape, same "parse untrusted artifact text → typed `bd` argv → write-back" flow |
| `.gsd/capabilities/beads/scripts/sync.py` — `FILES_BLOCK_RE` + todo frontmatter regexes (new constants) | utility (parser) | transform | `sync.py:DEPENDS_ON_BLOCK_RE`/`parse_depends_on()` (lines 39, 142-174) | exact — identical block-list YAML shape, different key |
| `.gsd/capabilities/beads/scripts/sync.py` — on-demand status/orphan function (new function) | service (CLI subcommand handler) | request-response (read-only query → render) | `sync.py:regenerate_beads_md()` (lines 899-964) + `_render_beads_recall_body()`'s "Unscoped" pattern (lines 660-684) | exact — same `_beads_md_argv`/`_render_beads_md_table` reuse, same two-section-below-table shape as `beads-recall`'s Unscoped |
| `.gsd/capabilities/beads/scripts/sync.py` — `resolve_epic()` edit + `resolve_milestone_epic()` (modified + new function) | service (CRUD resolve-or-create) | CRUD | `sync.py:resolve_epic()`/`resolve_phase_epic()` (lines 281-319, 826-839) | exact — same resolve-by-id-first-then-create contract, one new fork |
| `.gsd/capabilities/beads/skills/beads-migrate-todos/SKILL.md` (new file) | route (slash-command skill) | request-response | `.gsd/capabilities/beads/skills/beads-sync/SKILL.md` (whole file) | exact — same frontmatter shape, same Step 0 banner / Step 1 config gate / single Bash dispatch call structure, but human-invoked not lifecycle-invoked |
| `.gsd/capabilities/beads/skills/beads-status/SKILL.md` (extended — new Step 1.5 branch) | route (slash-command skill, extended) | request-response | same file, existing Step 1.5 branch structure (lines with "At `execute:wave:pre`" etc.) | exact — literally the same file, add a 5th branch following the 4 existing ones' shape |
| `.gsd/capabilities/beads/capability.json` (modified — `beads.epic_per` config key + 2 new `skills[]` entries) | config | CRUD (declarative merge) | same file's `beads.sync_mode` block (lines ~242-247) | exact — copy the `enum`/`values`/`default` shape verbatim |
| `.gsd/capabilities/beads/tests/test_sync.py` (modified — new test classes) | test | request-response (unit, real `bd` scratch DB) | `TestCreateIssues` (line 293), `TestBeadsRecall` (line 1143), `TestPhaseScopedEpic` (line 338) | exact — same `unittest.TestCase` + scratch-`bd`-DB style already used 18 times in this file |
| `.gsd/capabilities/beads/tests/fixtures/todo-wellformed.md`, `todo-malformed.md` (new files) | test fixture | file-I/O | none (no todo fixtures exist yet) — closest structural analog is `add-todo.md`'s `create_file` step's literal template | new — no analog, build from the workflow template directly |

## Pattern Assignments

### `sync.py` — `migrate_todos()` (service, file-I/O → CRUD)

**Analog:** `sync.py:create_issues()` (lines 535-625), fail-open opener at `bd_available()` gate.

**Fail-open opener pattern** (lines 536-547, copy this exact shape):
```python
def create_issues(plan_arg):
    if not bd_available():
        print(NOTICE)
        try:
            project_root = find_project_root(Path(plan_arg).resolve().parent)
        except ValueError:
            project_root = None
        if project_root is not None:
            append_state_blocker(
                confined(project_root, ".planning", "STATE.md"),
                "bd unavailable -- beads-sync skipped (B6/D-08)",
            )
        return 0
```
`migrate_todos(pending_dir_arg)` must open with the identical `bd_available()` gate (whole-run
skip, per RESEARCH.md Pitfall 2 — do not loop into N per-file `bd_create_failed` entries when `bd`
is unavailable before the loop even starts).

**Per-item try/except, not per-run** (lines 564-592 pattern, adapt to per-file):
```python
try:
    epic_id, epic_created, stale_epic_id = resolve_epic(...)
    ...
except RuntimeError as exc:
    print(NOTICE)
    append_state_blocker(..., f"bd failing mid-sync -- beads-sync skipped (B6/D-08): {exc}")
    return 0
```
Adapt: wrap each todo file's `bd create` call individually (RESEARCH.md's Anti-Patterns section
is explicit this must be per-file, unlike `create_issues`' per-run wrap, since one malformed `bd
create` must not abort the whole migration batch).

**Write-then-verify-then-delete ordering** (D-05, mirrors this comment already in the file at
lines 594-599's `if task_updates or epic_created: ... plan_path.write_text(...)` — write only
after success is confirmed): check `run_bd([...]).returncode == 0` before `Path(todo_path).unlink()`.

**`bd create` argv shape to copy** (RESEARCH.md's verified Code Example, matches `resolve_issue`'s
argv style at lines 336-341):
```python
result = run_bd([
    "bd", "create", title,
    "-d", desc,
    "-t", "task",
    "-p", str(SEVERITY_TO_PRIORITY[todo["severity"]]),
    "-l", f"area-{todo['area']}",
    "--silent",
])
if result.returncode != 0:
    raise RuntimeError(f"bd create (migrated todo) failed: {result.stderr.strip()}")
```

---

### `sync.py` — `FILES_BLOCK_RE` + todo frontmatter parsing (utility, transform)

**Analog:** `sync.py:DEPENDS_ON_BLOCK_RE` + `parse_depends_on()` (lines 32-39, 142-174).

**Constant to clone** (line 39, change key only):
```python
DEPENDS_ON_BLOCK_RE = re.compile(r"^depends_on:\s*\n((?:^[ \t]*-[ \t]*.+\n?)+)", re.MULTILINE)
# -> FILES_BLOCK_RE = re.compile(r"^files:\s*\n((?:^[ \t]*-[ \t]*.+\n?)+)", re.MULTILINE)
```

**Block-list extraction loop to clone** (lines 163-174):
```python
m = DEPENDS_ON_BLOCK_RE.search(frontmatter)
if not m:
    return []
items = []
for line in m.group(1).splitlines():
    line = line.strip()
    if not line.startswith("-"):
        continue
    item = line[1:].strip().strip('"').strip("'")
    if item:
        items.append(item)
return items
```
Reuse `FRONTMATTER_RE` (line 30, `\A---\n(.*?\n)---\n`) unchanged to isolate the todo file's
frontmatter block before running per-key regexes against it — same call shape as
`parse_plan()`'s `fm_match = FRONTMATTER_RE.match(text)` (line 118). Add single-line regexes for
`created`/`title`/`area`/`severity` matching `BEADS_EPIC_RE`'s style (line 31:
`re.compile(r"^beads_epic:\s*(\S+)\s*$", re.MULTILINE)`) — `title`/`area`/`severity` need a
looser `(.+)` capture since they aren't single-token values like an epic id.

**Missing/malformed → D-04 "leave in place" path:** a todo missing `severity`, missing the
closing `---`, or otherwise failing FRONTMATTER_RE must be routed to the "could not be
interpreted" list, never partially processed — same discipline `resolve_epic`/`resolve_issue`
apply (raise, caught by the per-file try/except above), except here the trigger is a parse
regex miss, not a `bd` call failure.

---

### `sync.py` — on-demand status + orphan sections (service, request-response)

**Analog:** `regenerate_beads_md()` (lines 899-964) for the query+render half;
`_render_beads_recall_body()`'s Unscoped-heading pattern (lines 660-684) for the "two extra
sections below a table" shape.

**Query pattern to reuse verbatim** (lines 920-932, `-n 0` already baked into `_beads_md_argv`):
```python
epic_id = resolve_phase_epic(phase_dir)
if epic_id is None:
    print("no epic yet -- nothing to regenerate")
    return 0
argv = _beads_md_argv(epic_id)   # ["bd", "list", "--parent", epic_id, "--all", "--json", "-n", "0"]
result = run_bd(argv)
rows = json.loads(result.stdout) if result.returncode == 0 else []
```

**Table render to reuse verbatim:** `_render_beads_md_table(rows, ordinal_map, task_status_by_id)`
(lines 863-896) — do not write a second table renderer for the on-demand view; call the existing
one with the same three arguments `regenerate_beads_md` already builds via
`_resolve_task_ordinal_map`/`_compute_diverged`.

**Orphan-section heading shape to copy** (lines 660-684 — "## Unscoped" pattern, D-09 requires
this exact "separate labeled section below the table" shape, not extra columns):
```python
parts.append("")
parts.append("## Unscoped")
parts.append("")
if unscoped:
    parts.append(_render_issue_table([(issue, None) for issue in unscoped], include_matched_via=False))
else:
    parts.append("None.")
```
Adapt: two sections, e.g. `## Issues with no matching plan task` (bd-side orphan, computed via
`find_orphans`/`collect_epic_task_ids`, already existing — read-only use, per RESEARCH.md's
Anti-Patterns section: **never call `bd close` from this path**) and
`## Plan tasks with no bd issue` (task-side orphan — genuinely new logic, no existing function;
see RESEARCH.md's Code Examples section for the exact loop over `discover_plan_files`/`parse_plan`
checking `task["beads_id"]` falsy).

---

### `sync.py` — `resolve_epic()` edit + `resolve_milestone_epic()` (service, CRUD)

**Analog:** `resolve_epic()`/`resolve_phase_epic()` (lines 281-319, 826-839) — the exact
resolve-by-id-then-create-on-confirmed-absence contract this new fork must preserve.

**Config read to add** (RESEARCH.md Pattern 3, first-ever `config.json` read in this file — reuse
`find_project_root`/`confined` verbatim, lines 85-108):
```python
def read_epic_per(project_root):
    cfg_path = confined(project_root, ".planning", "config.json")
    if not cfg_path.exists():
        return "phase"
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "phase"
    return cfg.get("beads", {}).get("epic_per", "phase")
```
Call this inside `resolve_epic()` immediately before the `resolve_phase_epic(phase_dir)` call at
line 309, branching to a new `resolve_milestone_epic(project_root)` when the value is
`"milestone"` — same "resolve existing by id first, `bd show --json` returncode check, only
`bd create --type epic` on confirmed absence" shape as lines 309-319.

---

### `.gsd/capabilities/beads/skills/beads-migrate-todos/SKILL.md` (new — route)

**Analog:** `beads-sync/SKILL.md` (whole file, 1 Bash dispatch, no lifecycle branching needed
since this is a single-purpose skill).

**Frontmatter to clone** (`beads-sync/SKILL.md` lines 1-8):
```yaml
---
name: gsd-beads-sync
description: "Sync PLAN.md tasks into beads (bd) issues under a phase epic, binding identity via <beads-id>"
argument-hint: "[PLAN.md path]"
allowed-tools:
  - Read
  - Bash
---
```
Adapt to `name: gsd-migrate-todos` (or whatever D-12's discretion picks), `argument-hint: ""` (no
args per CONTEXT.md), same `allowed-tools` list.

**Step 0/Step 1 boilerplate to clone verbatim** (`beads-status/SKILL.md` lines 10-33 — the
"STOP -- DO NOT READ THIS FILE" banner instruction, the `## Step 0 -- Banner` block, and the
`## Step 1 -- Config Gate` reading `.planning/config.json`'s `beads.enabled`, with the identical
disabled-message shape):
```text
GSD > BEADS STATUS
```
```text
Beads status is disabled (beads.enabled).
Nothing was closed; the loop proceeds normally.
```
Adapt banner text to `GSD > MIGRATE TODOS`; disabled-message body to describe migration being
skipped, not "nothing was closed."

**Single dispatch call to clone** (`beads-status/SKILL.md`'s Step 2a shape, lines with the
`python3 .gsd/capabilities/beads/scripts/sync.py wave-status-block ...` call):
```bash
python3 .gsd/capabilities/beads/scripts/sync.py migrate-todos
```
Print the script's stdout verbatim as the console-only report (D-13 — no separate
`MIGRATION-REPORT.md` write from the skill layer either).

---

### `.gsd/capabilities/beads/skills/beads-status/SKILL.md` — new Step 1.5 branch (route, extended)

**Analog:** the file's own existing Step 1.5 branch structure (the four "At `execute:wave:pre`" /
"At `execute:wave:post`" / "At `verify:post`" / "At `ship:pre`" paragraphs).

**Branch-selection trigger to add:** RESEARCH.md's Pattern 2 is explicit — the new 5th branch's
condition is "this invocation carries no lifecycle-point marker at all" (a bare
`/gsd-beads-status [phase]` call has no `WAVE_PLAN_IDS`/lifecycle context, unlike the four
existing dispatch points). Do not fold this into any of the four existing branches — the file's
own Anti-Patterns section (items 5-6) already warns against collapsing branches, and this is a
fifth, structurally identical warning for the new branch.

**Dispatch call to reuse:** the new branch should call `regenerate-beads-md` (read-only, same as
Step 2b's `verify:post` branch) then render the same two orphan sections described above — do not
introduce a third rendering path; the on-demand view and `regenerate-beads-md`'s underlying query
share one function (see the `sync.py` on-demand section above).

---

### `capability.json` — `beads.epic_per` + new `skills[]` entries (config)

**Analog:** the existing `beads.sync_mode` block (verbatim, lines ~242-247).

```json
"beads.epic_per": {
  "type": "enum",
  "values": ["phase", "milestone"],
  "default": "phase",
  "description": "phase (default): one epic per phase, as today. milestone: one epic shared across every phase in the current milestone (D-10: forward-only; D-11: read fresh at each epic-creation call site)."
}
```

**`skills[]` array to extend** (currently `["beads-sync", "beads-status", "beads-recall"]`):
add `"beads-migrate-todos"` (new skill directory); `beads-status` needs no new entry (it's
extended in place, not duplicated). No new `steps[]`/`gates[]` entries are needed for either new
human-invoked skill — RESEARCH.md confirms a skill IS the slash-command mechanism, with no
separate "commands" registration concept in this manifest shape.

---

### `tests/test_sync.py` — new test classes (test, request-response, real scratch `bd`)

**Analog:** `TestCreateIssues` (line 293) for the migration path's real-`bd`-round-trip style;
`TestBeadsRecall` (line 1143) for the "Unscoped"-section rendering assertions;
`TestPhaseScopedEpic` (line 338) for the epic-resolution-fork test shape (`TestMilestoneEpic`
should mirror this class's structure, asserting `resolve_epic` routes to
`resolve_milestone_epic` when `.planning/config.json` sets `beads.epic_per: "milestone"`, and
preserves today's exact behavior when absent/`"phase"`).

**Fixture/setup pattern:** every existing class uses a `tempfile`-based scratch project root
with a real `bd init` (see `TestEndToEndTracer`, line 143, and `TestLiveDependencies`, line 207)
— new classes (`TestMigrateTodos`, `TestMigrateTodosReport`, `TestOnDemandStatus`,
`TestMilestoneEpic`) must follow the same real-`bd`-scratch-DB discipline, not mocked `subprocess`
calls, matching this file's own established testing philosophy (no `unittest.mock` used for `bd`
itself anywhere in the 18 existing classes — `mock` import at line 16 is used elsewhere, verify
scope before reusing it for `bd` calls specifically).

## Shared Patterns

### `bd` invocation discipline (applies to every new function above)

**Source:** `sync.py:run_bd()` (lines 48-51) + `bd_available()` (lines 54-64)
**Apply to:** `migrate_todos()`, on-demand status function, `resolve_milestone_epic()` — every
new `bd` call, with zero exceptions.
```python
def run_bd(argv, timeout=BD_TIMEOUT):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
```
Never assemble a `bd` command as a shell string; always a typed argv list (N4/T-01-01, restated
in `beads-status/SKILL.md` Anti-Pattern 3 and RESEARCH.md's Known Threat Patterns table).

### Fail-open (B6) on `bd` absence/failure

**Source:** `create_issues()`'s opening gate (lines 536-547) + `append_state_blocker()` (lines
67-82)
**Apply to:** `migrate_todos()`'s whole-run gate; the on-demand status branch's dispatch.
Every new subcommand must print `NOTICE` and, when a project root resolves, append one dated
bullet to `STATE.md`'s `### Blockers/Concerns` — never crash, never partially run.

### Path confinement (T-01-02)

**Source:** `find_project_root()` + `confined()` (lines 85-108)
**Apply to:** the new `.planning/config.json` read in `resolve_epic()`; the `pending_dir` glob in
`migrate_todos()` (`confined(project_root, ".planning", "todos", "pending")` before globbing).
Never join an artifact-derived path fragment without routing it through `confined()`.

### Table rendering / cell escaping

**Source:** `_escape_table_cell()` (lines 628-633), `_render_beads_md_table()` (lines 863-896),
`_render_issue_table()` (lines 642-657)
**Apply to:** the on-demand status view — reuse all three verbatim; the only new rendering logic
needed is the two orphan-list `parts.append(...)` blocks (see `_render_beads_recall_body`'s
Unscoped pattern above).

### Argparse subcommand registration

**Source:** `main()` (lines 1207-1261) — each subcommand is `sub.add_parser("name", help=...)`
plus positional `.add_argument(...)` calls, dispatched via a flat `if args.command == "..."` chain.
**Apply to:** register `migrate-todos` (no positional args — `pending_dir` is derived internally
via `find_project_root`, matching `regenerate-beads-md`'s single-`phase_dir`-arg simplicity where
possible) and the on-demand status subcommand (`phase_dir` positional, optional — default to
`STATE.md`'s `current_phase` per D-08, resolved inside the handler, not via `argparse` default
since it requires a file read).

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `.gsd/capabilities/beads/tests/fixtures/todo-wellformed.md` | test fixture | file-I/O | No todo fixtures exist anywhere in this repo (`.planning/todos/pending/` doesn't exist yet, verified in RESEARCH.md). Build directly from `~/.claude/gsd-core/workflows/add-todo.md`'s `create_file` step template (frontmatter: `created`/`title`/`area`/`severity`/`files` block-list; body: `## Problem`/`## Solution`) — reproduced in full in the `<code_context>` read above, not paraphrased. |
| `.gsd/capabilities/beads/tests/fixtures/todo-malformed.md` | test fixture | file-I/O | Same — no existing "malformed input" fixture pattern in this capability's tests to copy; construct by deliberately omitting the closing `---` or the `severity` key from the well-formed template, per RESEARCH.md's Pitfall 1 guidance. |
| Task-side orphan detection logic (inside the new on-demand status function) | — | transform | RESEARCH.md is explicit this is genuinely new: `find_completed_task_ids` counts tasks with no `beads_id` as "skipped" but never surfaces *which* task/plan — no existing function to copy, only the surrounding loop shape (`discover_plan_files` → `parse_plan` → iterate `tasks`) is reusable plumbing. |

## Metadata

**Analog search scope:** `.gsd/capabilities/beads/` in full (`scripts/sync.py` 1265 lines,
`capability.json` 176 lines, three `skills/*/SKILL.md` files, `tests/test_sync.py` ~2100+ lines) —
this capability is self-contained; no analog search was needed outside this directory since
CONTEXT.md/RESEARCH.md scope every file change to here.
**Files scanned:** `sync.py` (full, via targeted non-overlapping offset/limit reads), `capability.json`
(full), `skills/beads-status/SKILL.md` (full), `skills/beads-recall/SKILL.md` (header),
`skills/beads-sync/SKILL.md` (header), `tests/test_sync.py` (class index via grep),
`~/.claude/gsd-core/workflows/add-todo.md` (full, todo schema source of truth).
**Pattern extraction date:** 2026-08-15
