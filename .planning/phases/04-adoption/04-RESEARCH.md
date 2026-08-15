# Phase 4: Adoption - Research

**Researched:** 2026-08-15
**Domain:** Python stdlib CLI scripting against a live `bd` (beads) binary; gsd-core capability
skill/config-schema extension. No web framework, no new runtime dependency.
**Confidence:** HIGH (every load-bearing claim below was verified against the real, installed `bd`
1.2.2 binary or the real source files in this repo — not against `bd --help` prose alone, and not
against training-data assumptions about beads' schema)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** A pending todo's `severity` (blocker/major/minor/cosmetic) frontmatter maps to bd
  priority; `area` frontmatter becomes a bd label. Both fields carry forward structurally, neither
  is dropped into prose-only.
- **D-02:** The exact severity→priority numeric mapping is NOT locked here — research must verify
  bd's actual priority scale against the real installed `bd` CLI before the planner locks the
  mapping. (Addressed below — see "bd's Real Priority Scale".)
- **D-03:** A todo's `files:` frontmatter (`file:lines` pointers) carries into the created issue's
  body/description as prose — no structured bd field exists for it, same treatment as
  Problem/Solution text.
- **D-04:** A todo that cannot be parsed (missing required frontmatter, malformed file) is left in
  place in `.planning/todos/pending/`, untouched — migration is non-destructive. The migration
  report lists it so a human can fix and re-run.
- **D-05:** A todo that WAS successfully migrated has its file deleted after the bd issue is
  created — bd becomes the sole source of truth for that item. Re-running the migration later only
  ever sees genuinely-new, not-yet-migrated todos — no separate migrated-marker mechanism needed.
- **D-06:** No duplicate detection against existing bd issues — every parseable todo always creates
  a new issue on each migration run. A slipped-through duplicate is a cheap one-off `bd close`/`bd
  delete`, not a migration correctness bug.
- **D-07:** A new user-invokable slash command (e.g. `/gsd-beads-status [phase]`) exposes the
  plan-task ↔ issue mapping on demand — today `beads-status` only fires via `steps[]` lifecycle
  dispatch. This phase adds the first human-invoked entry point.
- **D-08:** With no phase argument, the command defaults to the current/last-active phase (infer
  from `STATE.md`'s `current_phase`); an explicit phase argument overrides. Matches the existing
  `beads-status` skill's `argument-hint: "[phase directory] [plan id...]"` shape.
- **D-09:** Orphans on both sides — a bd issue with no matching plan task, and a plan task with no
  bd issue — are rendered as two separate labeled sections below the main mapping table (not extra
  table columns), matching the "Unscoped" heading pattern `BEADS-RECALL.md` established in Phase 2.
- **D-10:** Setting `beads.epic_per=milestone` applies forward-only — it does NOT retroactively
  fold already-created per-phase epics (Phases 1-3's existing epics) under one milestone epic.
- **D-11:** `beads.epic_per` can be changed at any point mid-milestone — it is read fresh at each
  epic-creation call site, no lock or validation gate needed. A phase already mid-flight keeps
  whatever epic it already has regardless of a later config change.
- **D-12:** The one-shot migration is triggered via a new slash command (e.g.
  `/gsd-migrate-todos`), consistent with D-07's on-demand beads-status decision — not a bare
  `sync.py` CLI-only invocation.
- **D-13:** The migration report ("what moved vs what could not be interpreted") is console output
  only — no separate `.planning/` artifact (e.g. `MIGRATION-REPORT.md`). bd itself is the durable
  record of what moved.

### Claude's Discretion

- Exact severity→priority numeric mapping (D-02) — pending research verification of bd's real
  priority scale (verified below; recommendation given, not locked).
- Exact slash-command names (`/gsd-beads-status`, `/gsd-migrate-todos`) and their argument parsing
  details.
- Exact section headings/wording for the two orphan sections (D-09), as long as the pattern matches
  `BEADS-RECALL.md`'s established "Unscoped" heading style.

### Deferred Ideas (OUT OF SCOPE)

None raised during discuss-phase — stayed within B12/B13/B14 scope throughout.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| B12 | One-shot migration of `.planning/todos/pending/` entries into beads, reporting what moved vs what could not be interpreted | bd's verified priority scale, label auto-creation, multi-line `-d` description behavior, reusable frontmatter regex patterns from `sync.py`, and the non-destructive parse-then-create ordering documented below |
| B13 | `beads-status` runnable on demand, printing the plan-task ↔ issue mapping including orphans on both sides | Verified that Skills are the slash-command mechanism (no separate "commands" concept in `capability.json`); documented gap that no code today computes task-side orphans; two extension options for `beads-status` SKILL.md laid out below |
| B14 | Milestone-level epic option (`beads.epic_per=milestone`) | Verified `capability.json`'s `config` schema shape for adding `beads.epic_per`; verified `sync.py` never reads `.planning/config.json` today (all config gating happens in SKILL.md via the Read tool) — documented as the key architectural decision the plan must make |
</phase_requirements>

## Summary

This phase adds no new runtime dependency and no new web-facing surface — it extends the existing
`beads` gsd-core capability overlay (`.gsd/capabilities/beads/`), a single stdlib-only Python
script (`scripts/sync.py`) invoked exclusively via SKILL.md-mediated `subprocess.run([...])` calls
with typed argv (never a shell string). All three requirements are additive extensions of patterns
already proven and tested in Phases 1-3: a new `sync.py migrate-todos` subcommand (B12) that reuses
`FRONTMATTER_RE` and the `DEPENDS_ON_BLOCK_RE` block-list-parsing technique already written for
`depends_on:`, a new `sync.py`/SKILL.md on-demand branch (B13) that reuses `_beads_md_argv`/
`_render_beads_md_table` and adds one genuinely new capability (task-side orphan detection, which
no existing code computes), and one new `config` key (B14) plus a new `resolve_milestone_epic`
function parallel to the existing `resolve_phase_epic`.

The one load-bearing verification this research had to do live (per D-02's explicit deferral) was
`bd`'s real priority scale — done against the installed `bd` 1.2.2 binary, both via `--help` output
and by round-tripping real `bd create`/`bd show --json` calls in a scratch database. The scale is
`0` (Critical) through `4` (Backlog), stored as a JSON integer regardless of whether `P0`/`0` was
passed to `--priority`. Labels require no pre-registration step — `bd create -l <name>` auto-creates
an unknown label. `bd create -d <string>`/`bd update -d <string>` accepts an embedded-newline Python
string directly as one argv element (no temp file, no `--body-file` indirection needed) and stores
it verbatim, confirmed against a real `bd show --json` round-trip.

The one genuine architectural gap this research surfaced (not previously flagged in CONTEXT.md):
`sync.py` **never reads `.planning/config.json` today** — every config gate (`beads.enabled`,
`beads.ship_gate`) is checked at the SKILL.md layer via the orchestrator's `Read` tool, then
`sync.py` is dispatched unconditionally once the gate passes. D-11's "read fresh at each
epic-creation call site" requirement means `beads.epic_per` cannot follow that same pattern
unchanged — either `sync.py` gains its first-ever `config.json` read (recommended, see Pattern 3
below), or the SKILL.md layer must resolve the epic-per mode and pass it as a new CLI flag into
every `create-issues` call. This is the single decision most likely to derail planning if left
implicit.

**Primary recommendation:** Extend `sync.py` with three new subcommands (`migrate-todos`,
`status` or `beads-status-ondemand`, and no new subcommand for B14 — thread `--epic-per`
resolution into `resolve_epic` itself via a direct `.planning/config.json` read). Reuse
`FRONTMATTER_RE`, `DEPENDS_ON_BLOCK_RE`'s block-list parsing shape, `_escape_table_cell`,
`_beads_md_argv`/`_render_beads_md_table`, and `bd_available()`'s fail-open gate throughout — write
zero new YAML/table-rendering/subprocess-wrapping logic.

## Architectural Responsibility Map

This capability is a CLI/automation tool, not a web app — the tiers below are the project's own
established layers (confirmed by reading `sync.py`, the three existing SKILL.md files, and
`capability.json`), not a generic web-tier table.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Config gating (`beads.enabled`, `beads.ship_gate`, new `beads.epic_per`... see caveat) | SKILL.md orchestrator (Read tool on `.planning/config.json`) | `sync.py` (only if D-11 forces a script-level read — see Summary) | Every existing config check in this capability happens in the SKILL.md's `## Step 1 -- Config Gate`, never in Python — `sync.py` has zero references to `config.json` today (`[VERIFIED: .gsd/capabilities/beads/scripts/sync.py]`, confirmed via grep on the full file, no matches for `config.json`) |
| Todo file parsing, bd issue creation, bd query/table rendering | `sync.py` (Python stdlib) | — | All `bd` invocations are typed argv passed to `subprocess.run` from this one script; no other file in the capability calls `bd` |
| Persistent task state | `bd`/Dolt DB (external process, `.beads/`) | — | bd owns issue status/content post-creation (`beads.sync_mode: authoritative`, established Phase 1) |
| Human-readable mapping surfaces | `.planning/phases/NN-*/NN-BEADS.md`, `NN-BEADS-RECALL.md` (regenerated artifacts) | — | Always fully overwritten from a live `bd` query, never hand-edited or merged (B11) |
| Todo capture (upstream of this phase) | `.claude/gsd-core/workflows/add-todo.md` (first-party gsd-core, not this capability) | `.planning/todos/pending/*.md` (filesystem) | This phase only consumes the schema add-todo.md produces; it does not change how todos are captured |
| Slash-command surface (B13/B12's new entry points) | Skill tool / SKILL.md frontmatter (`name:`, `argument-hint:`) | — | `capability.json` has no separate "commands" concept — confirmed by reading the full schema (`id, role, version, title, description, tier, requires, engines, runtimeCompat, skills, agents, hooks, config, steps, contributions, gates`, `[VERIFIED: .gsd/capabilities/beads/capability.json:1-177]`); a skill IS the slash-command mechanism (the harness treats `/<skill-name>` as a Skill-tool invocation by name) |

## bd's Real Priority Scale (D-02, the deferred research question)

Verified three independent ways against the real installed `bd` 1.2.2 binary (`bd version` ->
`bd version 1.2.2 (6c124203e)`, `[VERIFIED: bd version]`):

1. `bd create --help` flag description: `` -p, --priority string   Priority (0-4 or P0-P4, 0=highest) (default "2")`` `[VERIFIED: bd create --help]`
2. `bd priority --help` (the dedicated shorthand subcommand) prints the full semantic scale
   verbatim:
   ```
   Priority levels:
     0 - Critical (security, data loss, broken builds)
     1 - High (major features, important bugs)
     2 - Medium (default)
     3 - Low (polish, optimization)
     4 - Backlog (future ideas)
   ```
   `[VERIFIED: bd priority --help]`
3. Round-tripped in a real scratch `bd` database (`bd init --prefix test` in an isolated temp
   dir): `bd create "..." --priority 0 --silent` then `bd show <id> --json` returned
   `"priority": 0` as a **JSON integer**, not a string, not `"P0"`. A second issue created with
   `--priority 4` returned `"priority": 4`. A third created with `--priority "P1"` (the alternate
   `P0`-`P4` form) also normalized to the integer `1` in `bd show --json`.
   `[VERIFIED: live bd 1.2.2 round-trip, this session]`

**Divergence check (the pattern that burned Phase 1):** unlike Phase 1's `--id`/hierarchical-child-
id/`bd list --parent`-hides-closed surprises, this scale does **not** diverge between `--help` text
and real behavior — the docs and the live binary agree exactly. The only thing training data alone
could not have supplied with confidence is the exact JSON field type (`priority` is an int, not a
zero-padded string like `"P0"`) — now confirmed.

**Recommended severity→priority mapping** (Claude's Discretion per CONTEXT.md — present to
user/planner for confirmation, not silently locked):

| Todo severity (add-todo.md taxonomy) | bd priority | Rationale |
|---|---|---|
| `blocker` — "breaks a workflow or loses data; fix first" | `0` (Critical) | Exact semantic match to bd's own "security, data loss, broken builds" description |
| `major` — "wrong behavior with no workaround" | `1` (High) | Matches bd's "major features, important bugs" |
| `minor` — "works, but with a workaround or annoyance" | `2` (Medium/default) | A workable-but-real issue fits bd's own "(default)" tier better than "polish" |
| `cosmetic` — "visual/polish only" | `3` (Low — polish, optimization) | Direct wording echo: bd's own description literally says "polish" |

Priority `4` (Backlog — "future ideas") is intentionally left unmapped: none of the four todo
severities describe a future idea, and reusing `4` for `cosmetic` would waste the semantic distance
bd's own scale already draws between "polish now" (3) and "maybe later" (4).

## Label Creation Mechanism (D-01, `area` → label)

Verified live: `bd create <title> --labels "area-auth"` (or `-l`) creates the label with **no
pre-registration step** — an unknown label string is silently created on first use. Confirmed via
`bd label list-all` after creating two issues with three distinct label strings:

```
🏷 All labels (3 unique):
  area-auth     (1 issues)
  area-general  (1 issues)
  area-ui       (1 issues)
```

`bd show --json`'s `"labels"` array normalizes to alphabetical order regardless of the `-l` flag's
input order (`area-ui,area-general` in → `["area-general", "area-ui"]` out) — do not rely on label
array order for anything positional. `[VERIFIED: live bd 1.2.2 round-trip, this session]`

There is a separate `bd label add <id> <label>` subcommand for adding a label to an *existing*
issue after creation, and `bd label list-all`/`bd label list <id>` for inspection — none of these
are needed for the migration path itself, since `-l`/`--labels` on `bd create` does the whole job
in one call. `[VERIFIED: bd label --help]`

**Recommendation:** prefix the label with `area-` (e.g. `area-auth`, `area-general`) rather than
the bare area string, to visually distinguish migration-sourced area labels from any other label
scheme a user might add later to the same `bd` database. This is a naming convention choice, not a
bd requirement — flag for user/planner confirmation alongside the priority mapping.

## Multi-line / Markdown Description Support (D-03, `files:` pointer carry-through)

Verified live: `bd create <title> -d <multiline-python-string>` accepts a string containing literal
`\n` characters as **one argv element** — passed through `subprocess.run(["bd", "create", title,
"-d", desc, ...])` with no shell involved, matching this codebase's existing N4/T-01-01 discipline.
No temp file, no `--body-file -`/stdin indirection is required for this to work correctly. A round
trip through `bd show --json` returned the description verbatim, byte-for-byte, including embedded
markdown syntax (` ``` ` code, `- ` list items):

```python
desc = "## Problem\nSomething broke\n\n## Solution\nTBD\n\n## Files\n- src/foo.py:12-20\n"
subprocess.run(["bd", "create", "Migrated todo test", "-d", desc, "-t", "task",
                 "-p", "1", "-l", "area-general", "--silent"], ...)
# bd show --json ->
# "description": "## Problem\nSomething broke\n\n## Solution\nTBD\n\n## Files\n- src/foo.py:12-20\n"
```
`[VERIFIED: live bd 1.2.2 round-trip, this session]`

**Recommendation for D-03:** build the migrated issue's `-d` value as
`## Problem\n{problem}\n\n## Solution\n{solution}\n\n## Files\n{files as "- path:lines" lines}\n`
— i.e. append a `## Files` section carrying the `file:lines` pointers as-is, matching the
`## Problem`/`## Solution` heading convention the todo file itself already uses (so a human reading
the bd issue sees the same structure the `.md` file had). `bd create` also has separate `--context`,
`--acceptance`, `--design` flags, but none of them is a better structural fit than folding `files:`
into the one `-d` description block alongside Problem/Solution — introducing a second field here
would split one logical unit across two bd fields for no benefit.

## Config Schema Mechanism (`capability.json`, for `beads.epic_per`)

Read the live, working `capability.json` in full (`[VERIFIED:
.gsd/capabilities/beads/capability.json:25-46]`). The `config` object's shape, verbatim:

```json
"config": {
  "beads.enabled": {
    "type": "boolean",
    "default": false,
    "description": "Master toggle for the beads issue-tracking capability."
  },
  "beads.sync_mode": {
    "type": "enum",
    "values": ["authoritative", "mirror", "off"],
    "default": "authoritative",
    "description": "authoritative (default): bd owns task status and task content ..."
  },
  "beads.ship_gate": {
    "type": "boolean",
    "default": true,
    "description": "When true, ship:pre blocks on blocking_open>0 or diverged>0 in BEADS.md."
  }
}
```

`beads.epic_per` follows the exact `beads.sync_mode` shape (an `enum` with a `values` array and a
`default`), not the boolean shape:

```json
"beads.epic_per": {
  "type": "enum",
  "values": ["phase", "milestone"],
  "default": "phase",
  "description": "phase (default): one epic per phase, as today. milestone: one epic shared across every phase in the current milestone (D-10: forward-only, does not retroactively fold existing per-phase epics; D-11: read fresh at each epic-creation call site)."
}
```

The project's live `.planning/config.json` today only sets `"beads": { "enabled": true }`
(`[VERIFIED: .planning/config.json:67-69]`, quoted verbatim) — `sync_mode` and `ship_gate` are
*not* written there, meaning they run on `capability.json`'s declared defaults. This confirms the
mechanism: a project only needs to write a `beads.epic_per` override into `.planning/config.json`
when it wants `milestone` mode; the `"phase"` default requires no project-level config change at
all, matching every other key in this schema.

**The unresolved architectural question this surfaces (see Summary):** `capability.json`'s
`config` block only *declares* the schema/default — nothing in this repo currently *reads*
`beads.epic_per`'s (or any `beads.*` key's) value from inside `sync.py` itself. `sync.py` has zero
references to `config.json` anywhere in its ~1266 lines (`[VERIFIED: grep over the full file, this
session, 0 matches for "config.json"]`). Every existing config check
(`beads.enabled`/`beads.ship_gate`) happens in the calling SKILL.md's `## Step 1 -- Config Gate` /
`## Step 2c` via the orchestrator's own `Read` tool — `sync.py` is dispatched unconditionally once
that gate passes. D-11 requires the epic-per mode to be "read fresh at each epic-creation call
site" (i.e. inside `resolve_epic()`, which `sync.py` alone executes) — the planner must choose
between (a) giving `sync.py` its first-ever direct `.planning/config.json` read (stdlib `json`,
confined via the existing `confined()`/`find_project_root()` helpers — no new dependency, N5-safe),
or (b) having the calling SKILL.md read the value and pass a new `--epic-per <value>` CLI flag into
`create-issues`. Option (a) is recommended: it is the only option that satisfies "read fresh at
each epic-creation call site" without adding a new flag to every SKILL.md dispatch call site that
invokes `create-issues`.

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────┐
 User types          │  Skill tool ("/gsd-migrate-  │
 /gsd-migrate-todos ─▶│   todos" / "/gsd-beads-      │
 or /gsd-beads-status │   status [phase]")           │
                    └──────────────┬──────────────┘
                                   │ dispatches new SKILL.md
                                   ▼
                    ┌─────────────────────────────┐
                    │ SKILL.md Step 1: Config Gate │  Read .planning/config.json
                    │ (beads.enabled check)        │  -- same pattern as existing 3 skills
                    └──────────────┬──────────────┘
                                   │ enabled=true
                                   ▼
                    ┌─────────────────────────────┐
                    │ sync.py new subcommand       │
                    │ (migrate-todos | status)     │
                    └──────────────┬──────────────┘
                                   │
                bd_available()?───┤─── no ──▶ print NOTICE, append STATE.md blocker, exit 0 (B6)
                                   │ yes
                        ┌──────────┴───────────┐
                        ▼                       ▼
        migrate-todos path            status/on-demand path
        ┌─────────────────────┐       ┌───────────────────────────┐
        │ glob .planning/      │       │ resolve_phase_epic(phase)  │
        │ todos/pending/*.md   │       │ bd list --parent <epic>    │
        └──────────┬───────────┘       │   --all --json (reuse      │
                    │                   │   _beads_md_argv)          │
        per file:   ▼                   └──────────┬──────────────┘
        ┌─────────────────────┐                     │
        │ parse frontmatter    │         ┌───────────┴────────────┐
        │ (reuse FRONTMATTER_RE│         ▼                        ▼
        │  + block-list regex  │  discover_plan_files(phase)  children (bd rows)
        │  shape from           │  -> every task's <beads-id>  -> ids not in
        │  parse_depends_on)    │        │                       task-id set
        └──────────┬───────────┘         │  = task-side orphan   = bd-side orphan
              parse ok? ── no ──▶ leave file in place, add to      (NEW logic --
                    │              "could not be interpreted" list  no existing code
                   yes                                              computes this)
                    ▼
        ┌─────────────────────┐
        │ bd create <title>    │
        │  -d <problem+solution │
        │     +files prose>     │
        │  -p <mapped priority> │
        │  -l area-<area>       │
        │  -t task --silent     │
        └──────────┬───────────┘
                    │ success
                    ▼
        delete todo file (D-05)          Render main mapping table
        add to "moved" list              (reuse _render_beads_md_table)
                    │                    + two orphan sections (D-09,
                    ▼                      "Unscoped"-style headings)
        print console-only report                    │
        (D-13: no MIGRATION-REPORT.md)                ▼
                                          print to console (on-demand path
                                          never writes NN-BEADS.md itself --
                                          it's a read/render, not a lifecycle
                                          regeneration step)
```

### Recommended Project Structure

No new files or directories beyond what the existing capability already has — every addition is
either a new function in the existing `sync.py`, a new `argparse` subcommand in its existing
`main()`, or a new/extended `SKILL.md`:

```
.gsd/capabilities/beads/
├── capability.json              # + "beads.epic_per" config key; + 2 new skill ids in skills[]
├── scripts/
│   └── sync.py                  # + migrate_todos(), + status/orphan-rendering functions,
│                                 #   + resolve_milestone_epic(), edited resolve_epic() to
│                                 #   read config.json for epic_per
├── skills/
│   ├── beads-sync/SKILL.md      # unchanged (plan:post dispatch)
│   ├── beads-status/SKILL.md    # extend Step 1.5 with a 5th on-demand branch (B13),
│   │                            #   OR create a new sibling skill (see Pattern 2 below --
│   │                            #   genuine open choice, not resolved by existing code)
│   ├── beads-recall/SKILL.md    # unchanged
│   └── beads-migrate-todos/     # NEW skill directory (B12/D-12) -- SKILL.md only, no script
│       └── SKILL.md
└── tests/
    ├── test_sync.py             # + new TestMigrateTodos, TestOnDemandStatus,
    │                             #   TestMilestoneEpic classes (unittest, same file --
    │                             #   this project keeps one test file for the whole capability)
    └── fixtures/
        └── todo-*.md             # NEW: synthetic todo fixtures (well-formed + malformed),
                                   #   since .planning/todos/pending/ is genuinely empty in this
                                   #   repo (verified: directory does not exist yet)
```

### Pattern 1: Reuse the block-list frontmatter parsing shape for `files:`

**What:** `add-todo.md`'s todo schema writes `files:` as a YAML block list:
```yaml
files:
  - src/auth/token.py:40-55
```
This is structurally identical to the `depends_on:` block-list form `sync.py` already parses and
tests (`DEPENDS_ON_BLOCK_RE`, in `parse_depends_on`, added for WR-04). Do not write a new YAML
parser or pull in a YAML library (violates N5) — copy the same `^[ \t]*-[ \t]*(.+)$`-style
block-item extraction technique, scoped to a `files:` key instead of `depends_on:`.

**When to use:** Any time this capability needs to read a structured-but-simple frontmatter list
from a markdown file that is not `PLAN.md` — this is now the second file format (todos, alongside
plans) needing this exact shape.

**Example (adapt, don't reinvent):**
```python
# Source: .gsd/capabilities/beads/scripts/sync.py:39, DEPENDS_ON_BLOCK_RE — same shape needed
# for a new FILES_BLOCK_RE against todo frontmatter's `files:` key.
DEPENDS_ON_BLOCK_RE = re.compile(r"^depends_on:\s*\n((?:^[ \t]*-[ \t]*.+\n?)+)", re.MULTILINE)
```

### Pattern 2: Extend `beads-status` vs. add a new sibling skill (B13's real open choice)

**What:** Skills, not a separate "commands" concept, are the slash-command mechanism in this
runtime — confirmed by reading `capability.json`'s full schema (no `commands` key exists anywhere
in the manifest) and by every existing user-invoked gsd-core workflow (`add-todo.md`) being a
SKILL.md dispatched by name/argument, exactly like `/gsd-capture`.

**When to use:** D-08 explicitly says the new on-demand entry point should match
`beads-status`'s existing `argument-hint: "[phase directory] [plan id...]"` shape — this is a
strong hint (not a hard requirement in CONTEXT.md) toward extending the *same* skill file rather
than forking a new one, since the argument shape and epic/table-rendering logic (`_beads_md_argv`,
`_render_beads_md_table`) are identical between "regenerate for a lifecycle step" and "regenerate
for a human's on-demand request" — only the *branch-selection signal* differs.

**The concrete gap the plan must close:** `beads-status`'s Step 1.5 currently determines its branch
by "which point dispatched this run" — a fact known only because gsd-core's own `steps[]` dispatch
loop invokes the skill with lifecycle-specific context (e.g. `WAVE_PLAN_IDS` for
`execute:wave:pre`/`execute:wave:post`). A direct `/gsd-beads-status [phase]` invocation carries
**no** such lifecycle context — it is a bare Skill-tool call with `$ARGUMENTS` = whatever the user
typed. The plan needs an explicit **new** Step 1.5 branch whose trigger condition is "this
invocation carries no lifecycle-point marker at all" (i.e., it is being run directly by a human or
by another skill, not by gsd-core's native step-dispatch loop) — this is a genuinely new signal,
not something any existing code already computes. Document this as its own task in the plan; do
not let it get silently folded into the four existing Step 1.5 branches (which the skill's own
Anti-Patterns section already warns against collapsing).

### Pattern 3: `sync.py` reading `.planning/config.json` directly (first time, for `beads.epic_per`)

**What:** Every existing `bd`-adjacent read in `sync.py` is `bd`, `git`, or the local filesystem
(`.planning/STATE.md`, `PLAN.md`, `ROADMAP.md`) — never `.planning/config.json`. Reading it
directly for `beads.epic_per` is new, but the pattern to copy is already in the file: resolve the
project root with `find_project_root()`, confine the path with `confined()`, then a plain
`json.loads(Path(...).read_text())` (stdlib `json`, already imported at the top of the file).

**When to use:** Inside `resolve_epic()` (or a small helper it calls), immediately before deciding
whether to call `resolve_phase_epic()` (today's only path) or a new `resolve_milestone_epic()`.

**Example (skeleton, not verbatim — the planner designs the exact function):**
```python
# Source: .gsd/capabilities/beads/scripts/sync.py:85-108 -- find_project_root/confined already
# exist and are reused verbatim; only the config.json read + json.loads call is new.
def read_epic_per(project_root):
    cfg_path = confined(project_root, ".planning", "config.json")
    if not cfg_path.exists():
        return "phase"  # capability.json's declared default
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "phase"
    return cfg.get("beads", {}).get("epic_per", "phase")
```

### Anti-Patterns to Avoid

- **Writing a YAML parser for `files:`:** the existing `depends_on:` block-list regex already
  solves this exact shape (Pattern 1) — a new dependency or a hand-rolled multi-line YAML parser
  would violate N5 and duplicate tested logic.
- **Passing todo body text through a shell string to `bd`:** every `bd create -d <text>` call must
  stay a single argv element inside a Python-list `subprocess.run([...])` call, exactly like every
  existing `run_bd()` call in this file — confirmed safe with embedded newlines/markdown in this
  session's live test; do not introduce a `--body-file`/temp-file indirection "to be safe" — it is
  unnecessary complexity for behavior already verified to work.
  - `# ponytail: unnecessary temp-file indirection — argv already handles embedded newlines, verified live.`
- **Deleting a todo file before confirming `bd create` succeeded:** D-05's "delete after the bd
  issue is created" is causally ordered — check `bd create`'s exit code (`run_bd(...).returncode
  == 0`) before unlinking the file, mirroring every other write-then-verify pattern in this script
  (`resolve_epic`/`resolve_issue` raise `RuntimeError` on a failed `bd create`, which the existing
  `create_issues()` catches with the B6/D-08 fail-open path — the migration path should follow the
  same per-file try/except shape, but per-file, not per-run, since one malformed `bd create` call
  must not abort the whole batch).
- **Auto-closing a bd-side orphan from the on-demand status view:** `find_orphans` exists today
  specifically for the *sync* path's auto-close behavior (a task removed from a plan closes its
  stale issue). The on-demand status view (B13) must only **report** orphans, never call `bd
  close` — conflating "show me the mapping" with "reconcile the mapping" would silently start
  closing issues on every human-invoked status check, which is not what B13 asks for.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parsing todo frontmatter (`created`/`title`/`area`/`severity`/`files`) | A new YAML/frontmatter parser or library | `FRONTMATTER_RE` (already in `sync.py`) plus per-key single-line regexes matching the existing `BEADS_EPIC_RE`/`DEPENDS_ON_RE` style, and `DEPENDS_ON_BLOCK_RE`'s block-list shape for `files:` | The exact same `---\n...\n---\n` delimiter shape and block-list nesting already has tested, working regex code two files away; N5 forbids a YAML dependency anyway |
| Rendering the epic-children mapping table for the on-demand view | A new table-renderer | `_render_beads_md_table` + `_escape_table_cell` (already in `sync.py`) | Identical 6-column shape (`Issue \| Title \| Status \| Task Status \| Plan Task \| Blocked By`) is exactly what the on-demand view needs to print; the only genuinely new logic is the two orphan-list computations appended after it |
| Detecting bd-side orphans (issue with no matching task) | New detection logic | `find_orphans` + `collect_epic_task_ids` (already in `sync.py`, epic-scoped since the `gsd-beads-bgb` fix) | Already correct and tested against the exact "one epic shared by several plans" edge case this project hit and fixed earlier this milestone |
| Reading `bd`'s live issue/epic state safely | A new `bd`-wrapping helper | `run_bd()` + `bd_available()` (already in `sync.py`) | Single point of truth for the argv-list/no-shell/timeout/fail-open contract (N4, B6) — every new subcommand must call through these, never `subprocess.run(["bd", ...])` directly |
| Confining every new file read/write to the project root | Ad hoc path validation | `find_project_root()` + `confined()` (already in `sync.py`) | T-01-02's guard already exists and is tested; a new path-join elsewhere would be an unreviewed, untested second implementation of the same security boundary |

**Key insight:** every piece of this phase's real new logic (severity→priority mapping table,
task-side orphan detection, the config.json read for `epic_per`, the milestone-epic title source)
is genuinely new — but every piece of *plumbing* around that logic (parsing, escaping, table
rendering, bd invocation, path confinement, fail-open) already exists, tested, in this one file.
The risk in this phase is writing a second implementation of plumbing that already works, not
under-building the genuinely new decision logic.

## Common Pitfalls

### Pitfall 1: Assuming `.planning/todos/pending/` has live fixtures to test against

**What goes wrong:** Writing the migration parser against imagined todo files, or worse, hand-
authoring a "realistic-looking" fixture that silently drifts from `add-todo.md`'s real schema.
**Why it happens:** `.planning/todos/pending/` does not exist in this repo yet (`[VERIFIED:
find .planning/todos -> "No such file or directory", this session]`) — there is nothing to
introspect live, unlike `PLAN.md`'s schema, which Phase 1 could read directly off real synced
plans.
**How to avoid:** Build fixtures by copying `add-todo.md`'s `create_file` step's exact template
verbatim (`[VERIFIED: ~/.claude/gsd-core/workflows/add-todo.md:123-142]`, reproduced above in this
document's Pattern 1 discussion) — including a `files:` block-list, not an inline-bracket form,
since that is the only form add-todo.md ever writes. Include at least one deliberately malformed
fixture (missing `---` closing delimiter, missing `severity` key) to exercise D-04's non-destructive
path in tests.
**Warning signs:** A fixture using `files: [foo.py:1]` (inline-bracket YAML) instead of the
block-list form — that is not what `add-todo.md` produces and would test the wrong parser branch.

### Pitfall 2: Conflating "could not be interpreted" (parse failure) with "bd create failed" (write failure)

**What goes wrong:** A migration run where `bd` becomes unavailable mid-run (locked DB, killed
process) reports every remaining todo as "could not be interpreted," which is misleading — the
todo parsed fine, the *write* failed, and D-04's guarantee ("left in place... so a human can fix
and re-run") still holds, but the report's wording would send a human toward editing a
well-formed todo file that needs no editing at all.
**Why it happens:** Both failure modes result in the same visible outcome (file stays in
`pending/`) if the report code doesn't track the reason separately.
**How to avoid:** Track two independent reasons per un-migrated file: `parse_error` (D-04's actual
target) and `bd_create_failed` (B6's fail-open path, applied per-file within the batch). Report
them as separate report sections/counts. If `bd_available()` returns false before the loop even
starts, take the whole-run NOTICE fail-open path immediately (matching every other `sync.py`
subcommand), rather than looping and reporting N individual `bd_create_failed` entries.
**Warning signs:** A migration report that says "12 could not be interpreted" right after `bd
unavailable` was printed — the two messages contradict each other if reasons aren't separated.

### Pitfall 3: `bd list`'s default row limit silently truncating the on-demand mapping view

**What goes wrong:** Reusing a `bd list` call without `-n 0` silently caps output at bd's default
50-row limit, exactly the pitfall `sync.py`'s own comments already document and guard against at
three existing call sites (`_beads_recall_argv`, `_beads_md_argv`, `filter_open_ids`).
**Why it happens:** It's an easy detail to drop when writing a fourth call site under time
pressure — bd's default page size is not documented in `--help` output as prominently as `-n`
itself.
**How to avoid:** Reuse `_beads_md_argv(epic_id)` verbatim for the on-demand view's main query — it
already has `-n 0` baked in — rather than writing a new `bd list --parent ...` argv list from
scratch.
**Warning signs:** An on-demand status view that looks correct on a small phase (few issues under
the epic) but silently drops rows once a phase accumulates more than 50 issues under one epic.

## Code Examples

### bd create with mapped priority, area label, and folded description (B12)

```python
# Verified live against bd 1.2.2, this session -- exact argv shape to follow.
# Source: pattern matches sync.py's existing run_bd() usage (e.g. resolve_issue, line 336-338).
title = todo["title"]
desc = (
    f"## Problem\n{todo['problem']}\n\n"
    f"## Solution\n{todo['solution']}\n\n"
    f"## Files\n" + "\n".join(f"- {f}" for f in todo["files"]) + "\n"
)
result = run_bd([
    "bd", "create", title,
    "-d", desc,
    "-t", "task",
    "-p", str(SEVERITY_TO_PRIORITY[todo["severity"]]),
    "-l", f"area-{todo['area']}",
    "--silent",
])
```

### On-demand mapping table + orphan sections, reusing existing renderers (B13)

```python
# Source: sync.py:842-845 (_beads_md_argv), 863-896 (_render_beads_md_table) -- reused verbatim.
# Only the two orphan computations below are new.
epic_id = resolve_phase_epic(phase_dir)  # existing function, unchanged
argv = _beads_md_argv(epic_id)           # existing: ["bd", "list", "--parent", epic_id, "--all", "--json", "-n", "0"]
rows = json.loads(run_bd(argv).stdout)

# bd-side orphan: an epic child issue matching no current task (existing logic, read-only use).
current_ids = collect_epic_task_ids(phase_dir, epic_id)
bd_side_orphans = [r for r in rows if r.get("id") not in current_ids]

# task-side orphan: a plan task with no <beads-id> at all (NEW -- no existing function computes
# this; find_completed_task_ids only iterates tasks that already have a beads_id or counts them
# "skipped", it never surfaces WHICH task index/name was skipped).
task_side_orphans = []
for plan_path in discover_plan_files(phase_dir).values():
    _, _, tasks = parse_plan(plan_path)
    for task in tasks:
        if not task["beads_id"]:
            task_side_orphans.append((plan_path.name, task["name"]))
```

## Runtime State Inventory

This phase is not a rename/refactor/migration-of-identifiers phase (it is "migrate todo *files*
into a *new* bd *record*", not "rename an existing string across stored state") — the Runtime
State Inventory trigger in the verification protocol does not apply. For completeness:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `.planning/todos/pending/*.md` — currently **zero files** (directory does not exist) `[VERIFIED: find .planning/todos, this session, "No such file or directory"]` | None to migrate today; the migration script and its tests must still work correctly against synthetic fixtures, since there is nothing live to run it against |
| Live service config | None — `bd`'s Dolt DB is written to only via typed `bd create` calls this phase adds, no existing external config references todo file paths | None |
| OS-registered state | None | None |
| Secrets/env vars | None | None |
| Build artifacts | None | None |

## Common Pitfalls

*(see above — merged into the single "Common Pitfalls" section per template; duplicate heading
omitted)*

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Recommended severity→priority mapping (blocker→0, major→1, minor→2, cosmetic→3, leaving 4 unused) | "bd's Real Priority Scale" | Low — bd's own priority scale is verified fact; only the *mapping choice* is an editorial recommendation. If the user prefers a different mapping (e.g. minor→3, cosmetic→4), it is a one-line constant change, not a re-architecture |
| A2 | `area-` label prefix convention (e.g. `area-auth` rather than bare `auth`) | "Label Creation Mechanism" | Low — cosmetic naming choice; bd's label mechanism is unaffected either way. Flag for user confirmation since it affects future manual `bd list --labels` filtering ergonomics |
| A3 | Migrated issue type defaults to `task` for every todo (no per-item type inference from content) | "Multi-line / Markdown Description Support" recommendation section | Low — consistent with N4/D-06's "no clever inference from artifact text" spirit and with `sync.py`'s own plan-task creation default (`--type task`); if wrong, a one-off `bd update --type` per issue, not a migration bug |
| A4 | Migrated issues are created with no `--parent` epic (standalone, not attached to any phase epic) | "Don't Hand-Roll" / Summary | Medium — this is inferred from PROJECT.md's own Constraints note that this project's *own* dev todos (`gsd-beads-bgb`, `gsd-beads-uh1`) are tracked as standalone bd issues, not phase-epic children `[VERIFIED: .planning/PROJECT.md:94-97]`, but B12's requirements/success-criteria text does not explicitly say "no epic" — confirm with user/planner before locking |
| A5 | `resolve_epic()` (inside `sync.py`) is the right place for the new `.planning/config.json` read for `beads.epic_per`, rather than the calling SKILL.md passing a `--epic-per` flag | "Config Schema Mechanism" | Medium — this is an architecture recommendation, not a verified fact; both options are technically viable and D-11's wording ("read fresh at each epic-creation call site") is the only textual signal favoring the script-reads-directly option. Surface both options to the user during planning rather than silently picking one |

## Open Questions

1. **What does a milestone-epic title look like, and where does its source text come from?**
   - What we know: Phase epics get their title from `ROADMAP.md`'s `### Phase N: Name` header,
     read verbatim by `get_phase_header()` (`[VERIFIED: sync.py:271-278]`). `STATE.md`'s
     frontmatter carries `milestone: v1.0` and `milestone_name: milestone`
     (`[VERIFIED: .planning/STATE.md:3-4]`, quoted verbatim) — note `milestone_name`'s value is
     literally the string `"milestone"` in this project today, an apparently un-customized
     placeholder, not a real release name.
   - What's unclear: There is no `### Milestone` heading anywhere in `ROADMAP.md` or `PROJECT.md`
     analogous to phase headers (`[VERIFIED: grep -n "^#|milestone" over both files, this session]`)
     — no existing "read this verbatim as the epic title" source exists for the milestone case.
   - Recommendation: Source the title from `STATE.md`'s frontmatter, e.g. `f"Milestone
     {milestone}: {milestone_name}"`, since it is the only machine-readable field that names the
     current milestone today, and `STATE.md` is already read for other phase-boundary facts
     elsewhere in this capability. Flag to the user that `milestone_name` may need to actually be
     set to something other than the literal placeholder `"milestone"` before this is useful.

2. **Should `bd priority` (the shorthand subcommand) or `bd create -p`/`bd update -p` be used for
   migration?**
   - What we know: Both accept the identical `0-4`/`P0-P4` value shape and produce the identical
     stored integer (verified above). `bd priority <id> <n>` is explicitly documented as
     "Shorthand for `bd update <id> --priority <n>`" and only operates on an *existing* issue.
   - What's unclear: N/A — this is a non-issue. Migration always uses `bd create -p <n>` (setting
     priority at creation time), never the `bd priority` shorthand (which requires an id that
     doesn't exist yet at creation time).
   - Recommendation: Use `bd create -p <n>` exclusively for this phase; `bd priority`/`bd update -p`
     would only matter for a hypothetical future re-prioritization feature, out of scope here.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `bd` binary on `PATH` | All three requirements (B12/B13/B14) | Yes | 1.2.2 (`6c124203e`) | B6's existing fail-open: `bd` absent/failing/locked → NOTICE + STATE.md blocker, exit 0, no phase blocked |
| Python 3 stdlib (`json`, `re`, `subprocess`, `pathlib`, `argparse`) | All three requirements | Yes | Python 3.14 (per `__pycache__/*.cpython-314.pyc` filenames observed in the repo) | None needed — no fallback required, stdlib is always present |
| `.planning/todos/pending/` directory | B12 only | No — directory does not exist yet in this repo | — | `migrate-todos` must handle a missing/empty `pending/` directory gracefully (zero files migrated, zero uninterpretable, print a "nothing to migrate" line) rather than erroring |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** `.planning/todos/pending/` — the migration subcommand's
first action should be `Path(pending_dir).glob("*.md")` guarded by `.exists()`, printing a clean
"no pending todos found" line rather than a stack trace, consistent with this script's existing
posture of never crashing on an empty/absent input.

**Note on the local `.beads/` schema-skew warning encountered during this research:** running
`bd list --json` against this project's own real `.beads/` database returned `"error": "schema
version mismatch: database is at v65, binary knows up to v53 (12 migrations ahead)"`. This is an
environment-local condition (this machine's installed `bd` binary is older than the schema this
project's Dolt DB has already been migrated to by some other, newer `bd` install/session) — it
does not affect the validity of any finding in this document, since every live-behavior claim above
was verified against a fresh, schema-matched scratch database created with this session's `bd
init`, not against the project's real (skewed) database. **Flag this for the user/planner:** any
plan task that needs to run `bd` commands against *this project's real* `.beads/` database (e.g. a
verification step) may need `--ignore-schema-skew` or a `bd` binary upgrade first — this is
independent of and orthogonal to the phase's actual implementation work.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib), runnable via `pytest` — confirmed both `import unittest` (no pytest-specific API used in the file) and a working `pytest` collection/run this session |
| Config file | none — no `pytest.ini`/`pyproject.toml`/`conftest.py` found under `.gsd/capabilities/beads/tests/` |
| Quick run command | `python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q` — verified this session: `66 passed in 3.22s` |
| Full suite command | Same command — this capability has exactly one test file (`test_sync.py`), no separate "quick vs full" split exists today |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| B12 | Parseable todo migrates to a bd issue with mapped priority/label/description; malformed todo left in place; migrated file deleted | unit (real `bd` in a scratch DB, matching this file's existing `TestCreateIssues`/`TestEndToEndTracer` style) | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestMigrateTodos -x` | ❌ Wave 0 — class does not exist yet |
| B12 | Migration report separates "moved" from "could not be interpreted", and (Pitfall 2) separates parse-failure from bd-write-failure reasons | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestMigrateTodosReport -x` | ❌ Wave 0 |
| B13 | On-demand status renders the same table shape as `regenerate-beads-md`, plus two orphan sections | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestOnDemandStatus -x` | ❌ Wave 0 |
| B13 | Task-side orphan (task with no `<beads-id>`) is detected and named | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestOnDemandStatus::test_task_side_orphan -x` | ❌ Wave 0 (this exact case has no analog anywhere in the current 66 tests) |
| B14 | `beads.epic_per=milestone` in `.planning/config.json` routes epic resolution to a shared milestone epic instead of a per-phase one | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestMilestoneEpic -x` | ❌ Wave 0 |
| B14 | `beads.epic_per` absent/`"phase"` preserves today's exact per-phase behavior (regression guard) | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestMilestoneEpic::test_default_unchanged -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q`
- **Per wave merge:** same command (single test file, ~3 seconds — no reason to split quick/full)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `.gsd/capabilities/beads/tests/fixtures/todo-wellformed.md` — a valid todo matching
      `add-todo.md`'s exact schema (frontmatter block-list `files:`, `## Problem`/`## Solution`
      body) — covers B12
- [ ] `.gsd/capabilities/beads/tests/fixtures/todo-malformed.md` — missing closing `---` or missing
      `severity` key — covers B12/D-04
- [ ] `TestMigrateTodos`, `TestMigrateTodosReport`, `TestOnDemandStatus`, `TestMilestoneEpic` test
      classes in the existing `test_sync.py` (this project's established one-file-per-capability
      pattern — do not create a second test file)
- [ ] No new framework install needed — `pytest`/`unittest` already present and working

## Security Domain

`security_enforcement` is `true` in `.planning/config.json`'s `workflow` block
(`[VERIFIED: .planning/config.json:48]`), so this section is required.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | This capability has no auth surface — it shells out to a local `bd` binary under the invoking user's own OS identity |
| V3 Session Management | No | N/A — no session concept |
| V4 Access Control | No | N/A — local CLI tool, no multi-tenant boundary |
| V5 Input Validation | Yes | Every field pulled from a todo file (title/area/severity/files/problem/solution) is untrusted input (a different principal — whoever wrote the `.md` file — than the process invoking `bd`, same T-01-01/N4 threat model this capability already documents). Validation control: the parse-then-create ordering (Pattern in Anti-Patterns above) — a field that fails to match its expected regex shape routes the whole file to D-04's "left in place" path, never a partially-populated `bd create` call |
| V6 Cryptography | No | N/A — no crypto surface |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Shell injection via todo file content reaching a `bd` command line (e.g. a todo `title` containing `` `$(rm -rf /)` ``) | Tampering | Already the whole-file discipline in `sync.py`: every `bd` invocation is a Python list passed to `subprocess.run([...])` with `shell=False` (the default) — confirmed this session that a string containing shell metacharacters passed as one argv element is never shell-interpreted. The migration subcommand must follow this exact pattern for every field pulled from todo files (title, problem, solution, files, area), with zero exceptions |
| Path traversal via a crafted `files:` frontmatter entry (e.g. `../../etc/passwd:1`) | Tampering / Information Disclosure | Not applicable to write operations here — `files:` values are only ever read as opaque strings and folded into a `bd create -d` description's prose text; they are never used to open, read, or write a filesystem path. No `confined()`/path-resolution call should ever be applied to a `files:` value from a todo — doing so would be over-engineering a control this data flow doesn't need (the value never becomes a path argument to anything) |
| Resource exhaustion via unbounded todo directory scan | Denial of Service | Low risk (this is a local dev tool, not a service) — `Path(pending_dir).glob("*.md")` is bounded by the same filesystem the rest of `.planning/` already lives in; no additional control needed beyond what already exists |

## Sources

### Primary (HIGH confidence)

- `bd version`, `bd --help`, `bd create --help`, `bd priority --help`, `bd label --help`,
  `bd update --help`, `bd epic --help` — run against the real installed `bd` 1.2.2 binary this
  session
- Live round-trip in a scratch `bd init --prefix test` database this session: `bd create` with
  `--priority`/`--labels`/`--body-file`/`-d`, then `bd show --json`/`bd list --json`/`bd label
  list-all` to confirm stored values
- `.gsd/capabilities/beads/scripts/sync.py` (full file, 1266 lines) — read in full this session
- `.gsd/capabilities/beads/capability.json` — read in full this session
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md`, `beads-recall/SKILL.md`,
  `beads-sync/SKILL.md` — read in full this session
- `~/.claude/gsd-core/workflows/add-todo.md` — read in full this session (todo file schema
  source of truth)
- `~/.claude/gsd-core/bin/lib/capability-command-router.cjs` — read to confirm no separate
  "commands" registration concept exists in the capability manifest
- `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/PROJECT.md`,
  `.planning/ROADMAP.md`, `.planning/config.json`, `.planning/phases/04-adoption/04-CONTEXT.md` —
  read in full this session

### Secondary (MEDIUM confidence)

None — every claim in this document was either read directly from a source file this session or
verified against the live `bd` binary; no claim rests on a WebSearch cross-check.

### Tertiary (LOW confidence)

None.

## Metadata

**Confidence breakdown:**
- Standard stack: N/A — no new library/dependency this phase (N5); all plumbing reuses existing
  stdlib-only `sync.py` code, HIGH confidence by direct file read
- bd priority scale / label mechanism / multi-line description: HIGH — verified via three
  independent live round-trips against the real bd 1.2.2 binary this session, not inferred from
  `--help` text alone
- Architecture (config-read gap, skill-vs-slash-command mechanism, task-side-orphan gap): HIGH —
  each claim is grounded in a full read of the relevant source file this session, with an explicit
  grep confirming absence (e.g. zero `config.json` references in `sync.py`)
- Severity→priority mapping recommendation, area-label prefix convention, no-epic-parent
  recommendation: MEDIUM — editorial recommendations built on verified facts, but the choice
  itself is not dictated by any spec; flagged in the Assumptions Log for user/planner confirmation

**Research date:** 2026-08-15
**Valid until:** 30 days (stable internal tooling; re-verify if `bd` is upgraded past 1.2.2, since
Phase 1 already found this exact binary's CLI surface to diverge across versions once before)
