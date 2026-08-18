# Phase 9: Beads Content Depth - Pattern Map

**Mapped:** 2026-08-16
**Files analyzed:** 15 (new content files + 2 modified config/hook files)
**Analogs found:** 15 / 15 (all have a direct upstream or in-repo analog — this phase is almost pure "port from upstream" work)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.agents/skills/beads/SKILL.md` (expand) | config (skill entry point) | request-response (doc lookup) | itself (current 80-line version) + upstream `SKILL.md` | exact — modify in place |
| `.agents/skills/beads/PRIME.md` (new) | config (bd override doc) | request-response | `.gsd/capabilities/beads/capability.json` steps[] + `beads-sync/SKILL.md` + `beads-status/SKILL.md` | role-match (content source, not doc-structure analog) |
| `.agents/skills/beads/resources/DEPENDENCIES.md` | utility (doc resource) | request-response | upstream `resources/DEPENDENCIES.md` | exact |
| `.agents/skills/beads/resources/WORKTREES.md` | utility (doc resource) | request-response | upstream `resources/WORKTREES.md` | exact |
| `.agents/skills/beads/resources/ASYNC_GATES.md` | utility (doc resource) | request-response | upstream `resources/ASYNC_GATES.md` | exact |
| `.agents/skills/beads/resources/RESUMABILITY.md` | utility (doc resource) | request-response | upstream `resources/RESUMABILITY.md` | exact |
| `.agents/skills/beads/resources/TROUBLESHOOTING.md` | utility (doc resource) | request-response | upstream `resources/TROUBLESHOOTING.md` | exact |
| `.agents/skills/beads/resources/STEALTH_MODE.md` (or similar) | utility (doc resource) | request-response | `bd init --help` / `bd prime --help` output (no single upstream file — see Pitfall 4) | partial — synthesize from CLI help, not a file |
| `.agents/skills/beads/commands/dep.md` | route (slash-command doc) | request-response | upstream `commands/dep.md` | exact |
| `.agents/skills/beads/commands/label.md` | route (slash-command doc) | request-response | upstream `commands/label.md` | exact |
| `.agents/skills/beads/commands/comments.md` | route (slash-command doc) | request-response | upstream `commands/comments.md` | exact |
| `.agents/skills/beads/commands/search.md` | route (slash-command doc) | request-response | upstream `commands/search.md` | exact |
| `.agents/skills/beads/commands/compact.md` | route (slash-command doc) | request-response | upstream `commands/compact.md` | exact |
| `.agents/skills/beads/commands/import.md` | route (slash-command doc) | request-response | upstream `commands/import.md` | exact |
| `.agents/skills/beads/commands/stats.md` | route (slash-command doc) | request-response | upstream `commands/stats.md` | exact |
| `.agents/skills/beads/commands/blocked.md` | route (slash-command doc) | request-response | upstream `commands/blocked.md` | exact |
| `hooks/hooks.json` (modify) | config/hook | event-driven (SessionStart) | itself, existing `SessionStart` array | exact — modify in place |
| `.beads/.gitignore` (modify, pending D-02 gitignore resolution) | config | file-I/O | itself, existing patterns for `config.yaml`/`metadata.json` | exact |
| D-02 self-heal copy-if-missing script/command | utility (file-copy) | file-I/O | `.gsd/capabilities/beads/scripts/sync.py` (`find_project_root`/`confined`) | role-match |
| `.claude-plugin/plugin.json` (version bump) | config | CRUD (single field edit) | itself, prior `08-02` bump (`0.1.0` -> `1.1.0`) | exact |

## Pattern Assignments

### `.agents/skills/beads/SKILL.md` (expand to entry point + links)

**Analog:** current file itself (`.agents/skills/beads/SKILL.md`, 80 lines) + upstream `SKILL.md` structure (frontmatter, "First Step", "Core CLI Workflow", "Rules" sections already match upstream's shape).

**Frontmatter to preserve verbatim** (lines 1-4):
```yaml
---
name: beads
description: Use when working in a repository that uses bd or Beads for durable project task tracking, issue dependencies, blocker management, multi-session handoff, or shared work memory. Trigger when the user asks to find ready work, claim or close tasks, create follow-up work, inspect blockers, recover project context, or choose between local planning and persistent project tracking.
---
```

**Existing structure to extend, not replace** (whole file, 80 lines): keep "First Step" (`bd prime` / `bd where`), "Core CLI Workflow" (5 numbered steps: find/inspect/claim/create/close), "What Belongs In Beads", "Rules" sections as-is. Add a new section listing the `resources/` and `commands/` files added by this phase, e.g. a "Deeper Topics" section with one bullet per new resource/command file and a one-line description — this is the progressive-disclosure index upstream's own `SKILL.md` doesn't need to duplicate (upstream relies on slash-command discovery + `resources/` directory listing).

**Anti-pattern to avoid** (from upstream `resources/CLI_REFERENCE.md`, verbatim):
```text
This skill does not bundle a copied CLI command reference. The command
surface is generated from the installed `bd` binary and would drift if
duplicated here.
```
Apply the same discipline to every new `commands/*.md` and `resources/*.md`: describe usage patterns, not frozen `--help` flag tables.

---

### `.agents/skills/beads/PRIME.md` (new — PUB-12)

**Analog:** No upstream doc-structure analog (PRIME.md is gsd-specific). Content source is verbatim from two places:

**Sync-point definitions** (`.gsd/capabilities/beads/capability.json` lines 57-140, `steps[]` array):
```json
{ "point": "plan:post",         "ref": {"skill": "beads-sync"},   "produces": ["PLAN.md"], "consumes": ["PLAN.md"], "when": "beads.enabled", "onError": "skip" },
{ "point": "execute:wave:pre",  "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"], "consumes": ["PLAN.md"], "when": "beads.enabled", "onError": "skip" },
{ "point": "execute:wave:post", "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"], "consumes": ["PLAN.md"], "when": "beads.enabled", "onError": "skip" },
{ "point": "verify:post",       "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"], "consumes": ["UAT.md"],  "when": "beads.enabled", "onError": "skip" },
{ "point": "ship:pre",          "ref": {"skill": "beads-status"}, "produces": [],           "consumes": ["BEADS.md"],"when": "beads.enabled", "onError": "skip" }
```

**Behavior per point** (read from `.gsd/capabilities/beads/skills/beads-sync/SKILL.md` and `.gsd/capabilities/beads/skills/beads-status/SKILL.md` this session — condense to terse bullets per D-05):
- `plan:post` (beads-sync): parse `<task>` blocks in PLAN.md, resolve/create one phase epic, create one `bd` issue per task lacking `<beads-id>`, rewrite PLAN.md with `beads_epic` frontmatter + per-task `<beads-id>`. Identity = `<beads-id>` only, never title match.
- `execute:wave:pre` (beads-status, branch 2a): regenerate `BEADS.md`, print `<beads_status>` block; orchestrator pastes it into every executor prompt for the wave.
- `execute:wave:post` (beads-status, "Step 2"): one batch `bd close` across all plan ids in the wave whose `SUMMARY.md` now exists.
- `verify:post` (beads-status, branch 2b): regenerate `BEADS.md` read-only (`blocking_open`/`diverged`), no close dispatch.
- `ship:pre` (beads-status, branches 2c/2d): if `beads.ship_gate=false` and blocking/diverged issues exist, record a `ship-override` trailer + `bd comment`; always verify `GSD-CORE-PATCH.md` still present, warn (non-blocking) if dropped.
- Ship gate (`capability.json` `gates[]` lines 156-184): blocks when `BEADS.md` frontmatter `blocking_open != 0` or `diverged != 0`, gated by `beads.ship_gate` (default `true`).

**D-06 constraint:** do not restate bare `bd` CLI basics (`bd ready`, `bd show`, `bd update --claim`) already in SKILL.md — PRIME.md is gsd-integration-only.

**Verified override mechanism** (`bd prime --help`, bd v1.2.2):
```text
Workflow customization:
- Place a .beads/PRIME.md file in the local clone or resolved workspace to override the default output entirely.
- Use --export to dump the default content for customization.
- Use --memories-only for hook contexts that should inject only persistent memories.
```

---

### `.agents/skills/beads/resources/DEPENDENCIES.md`, `WORKTREES.md`, `ASYNC_GATES.md`, `RESUMABILITY.md`, `TROUBLESHOOTING.md`

**Analog:** upstream `resources/*.md` at `/home/dd/.claude/plugins/marketplaces/beads-marketplace/plugins/beads/skills/beads/resources/`.

**Structure pattern** (from `resources/WORKTREES.md` lines 1-60):
```markdown
# Git Worktree Support

> Adapted from ACF beads skill

**v0.40+**: First-class worktree management via `bd worktree` command.

## When to Use Worktrees
| Scenario | Worktree? | Why |
|----------|-----------|-----|
...

## Creating Worktrees
```bash
bd worktree create .worktrees/{name} --branch feature/{name}
```

## Architecture

[diagram + prose]
```text
Table-driven "when to use" sections + fenced `bash` command examples + a short architecture note is the recurring shape across all 5 files. Copy this shape; content is gsd-core-neutral (worktree/dependency/async-gate mechanics don't change per-project) so upstream text can largely be adapted/trimmed, not rewritten from scratch.

**Troubleshooting structure specifically** (from `resources/TROUBLESHOOTING.md` lines 1-30):
```markdown
# Troubleshooting Guide
## Interface-Specific Troubleshooting
**MCP tools (local environment):** ...
**CLI (web environment or local):** ...
## Contents
- [Dependencies Not Persisting](#dependencies-not-persisting)
...
---
## Dependencies Not Persisting
### Symptom
```bash
[repro command]
```
```text
Symptom/cause/fix subsections per issue, TOC at top — reuse verbatim structure.

---

### `.agents/skills/beads/resources/STEALTH_MODE.md` (or fold into TROUBLESHOOTING.md — Claude's discretion)

**Analog:** none — no upstream file (Pitfall 4, confirmed). Source is live CLI help output, not a file to port:
- `bd init --help`: `--stealth` — *"configures per-repository git settings for invisible beads usage: `.git/info/exclude` to prevent beads files from being committed... To set up a specific AI tool, run: `bd setup <claude|cursor|aider|...> --stealth`"*
- `bd prime --help`: `--stealth` — *"Stealth mode (no git operations, flush only)"*
- Two upstream one-line mentions: `resources/WORKTREES.md:52` (`BEADS_DIR` in worktree-external-workspace context) and `SKILL.md` Prerequisites line (`"Git repository (optional — use BEADS_DIR + --stealth for git-free operation)"`).

Do not invent a fuller upstream source — write this section directly from the `--help` text above.

---

### `.agents/skills/beads/commands/dep.md`, `label.md`, `comments.md`, `search.md`, `compact.md`, `import.md`, `stats.md`, `blocked.md`

**Analog:** upstream `commands/*.md` (same filenames exist upstream 1:1 for every PUB-11-named topic).

**Structure pattern** (`commands/dep.md` full file, lines 1-40):
```markdown
---
description: Manage dependencies between issues
argument-hint: "[command] [from-id] [to-id]"
---

Manage dependencies between beads issues.

## Available Commands

- **add**: Add a dependency between issues
  - $1: "add"
  - $2: From issue ID
  - $3: To issue ID
  - $4: Dependency type (blocks, related, parent-child, discovered-from)
...
## Dependency Types
- **blocks**: Hard blocker (from blocks to) - affects ready queue
...
```

**Simpler variant** (`commands/stats.md` full file, lines 1-19):
```markdown
---
description: Show project statistics and progress
---

Display statistics about the current beads project.

Use the beads MCP `stats` tool to retrieve project metrics and present them clearly:
- Total issues by status (open, in_progress, blocked, closed)
...

Optionally suggest actions based on the stats:
- High number of blocked issues? Run `/beads:blocked` to investigate
- No in_progress work? Run `/beads:ready` to find tasks
```

Frontmatter (`description` + optional `argument-hint`) + prose instructing the agent what MCP tool/CLI subcommand to invoke + optional "Available Commands"/"Types" reference tables is the consistent shape across every upstream command file. Copy this exact two-field frontmatter + body shape for all 8 new command files; adapt slash-command names (`/beads:blocked` etc.) to whatever this repo's command namespace is (check `.claude-plugin/plugin.json`'s `skills` field — currently no `commands` registration exists, so this may just be doc content inside the skill rather than registered slash commands; confirm during planning).

---

### `hooks/hooks.json` (modify — D-02 self-heal)

**Analog:** itself, current file (full content, 15 lines):
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "command": "bd prime --hook-json", "type": "command" }
        ],
        "matcher": ""
      }
    ]
  }
}
```

**Core pattern:** D-02/D-09 require the copy-if-missing check to run *before* `bd prime --hook-json` in the same `SessionStart` entry. Two mechanically equivalent options, both fitting the existing single-`hooks[]`-array shape:
1. Two sequential `command` entries in the `hooks[]` array (copy-check first, `bd prime --hook-json` second).
2. One `command` entry chaining `&&`: `"[ -f .beads/PRIME.md ] || cp .agents/skills/beads/PRIME.md .beads/PRIME.md; bd prime --hook-json"`.

No other hook file in this repo to pattern-match against — this is the sole `hooks.json`.

---

### D-02 self-heal copy-if-missing logic (bash one-liner or Python script)

**Analog (if Python):** `.gsd/capabilities/beads/scripts/sync.py` lines 116-139:
```python
def find_project_root(start):
    """Walk up from `start` to the nearest ancestor containing `.planning/`."""
    current = start.resolve()
    for _ in range(10):
        if (current / ".planning").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise ValueError(f"could not locate a .planning/ ancestor above {start}")

def confined(root, *parts):
    """Join parts onto root and reject any resolved escape (T-01-02)."""
    candidate = root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError(f"path escapes project root: {candidate} not under {root}")
    return candidate
```
Reuse this exact pair rather than re-deriving path resolution if the self-heal is implemented as a Python script. This repo's stdlib-only / typed-argv-only convention (`sync.py` module docstring: "no `bd` command is ever assembled as a shell string, N4, T-01-01") applies if the script shells out — the copy-if-missing check itself needs no `bd` invocation, pure `shutil.copy`/`pathlib` file I/O.

**Analog (if bash one-liner, per research's Alternatives Considered):** no in-repo bash-hook precedent beyond the existing `bd prime --hook-json` single command — pattern is "one more `command` string in `hooks.json`'s `hooks[]` array," not a script file.

---

### `.claude-plugin/plugin.json` (version bump)

**Analog:** itself (full file, 11 lines) + prior bump precedent (`08-02-SUMMARY.md` Task 1: `0.1.0` -> `1.1.0`, byte-identical elsewhere):
```json
{
  "name": "beads",
  "version": "1.1.0",
  "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle",
  "author": { "name": "Dennis A. V. Dittrich", "email": "davdittrich@gmail.com" },
  "license": "MIT",
  "skills": ["./.agents/skills/beads"]
}
```
Only the `version` field changes (`1.1.0` -> `1.1.1`); everything else byte-identical, matching the established single-field-edit pattern from Phase 8.

## Shared Patterns

### "Don't duplicate the CLI reference" discipline

**Source:** upstream `resources/CLI_REFERENCE.md` (full file, verbatim above)
**Apply to:** every new `commands/*.md` and `resources/*.md` file — describe usage/framing, point to `bd help --all` / `bd <command> --help` for flag tables, never transcribe `--help` output into a frozen table that will drift on the next `bd` release.

### Typed-argv / no-shell-string discipline

**Source:** `.gsd/capabilities/beads/scripts/sync.py` module docstring + `run_bd()` (lines 1-9, 77-81)
**Apply to:** D-02's self-heal, only if it ends up invoking `bd` at all (it doesn't need to — pure filesystem copy). If it does shell out for any reason, use `subprocess.run([...])`, never a shell string.

### Path confinement

**Source:** `.gsd/capabilities/beads/scripts/sync.py` `find_project_root()`/`confined()` (lines 116-139, quoted above)
**Apply to:** D-02's self-heal destination path resolution (`.beads/PRIME.md`), hardcoded relative to a resolved project root — never derived from hook arguments, env vars, or file content (ASVS V5/V12, threat T-01-02).

### Frontmatter shape for skill/command docs

**Source:** `.agents/skills/beads/SKILL.md` lines 1-4 (skill-level) and upstream `commands/dep.md`/`commands/stats.md` lines 1-4 (command-level: `description` + optional `argument-hint`)
**Apply to:** all new/modified `.md` files under `.agents/skills/beads/` — keep frontmatter minimal (1-2 keys), never add unused keys.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `.beads/.gitignore` entry for `PRIME.md` (pending Open Question 1 in RESEARCH.md) | config | file-I/O | Whether `.beads/PRIME.md` is gitignored or committed-once is an unresolved design fork (RESEARCH.md Pitfall 2) not yet decided in CONTEXT.md — planner must resolve before writing this task; existing `.beads/.gitignore` entries for `config.yaml`/`metadata.json` are the closest precedent either way. |

## Metadata

**Analog search scope:** `.agents/skills/beads/` (this repo), `/home/dd/.claude/plugins/marketplaces/beads-marketplace/plugins/beads/skills/beads/` (upstream v1.2.2 marketplace copy), `.gsd/capabilities/beads/` (capability.json, sync.py, dispatch SKILL.md files), `hooks/hooks.json`, `.claude-plugin/plugin.json`
**Files scanned:** ~25 (5 upstream resources + upstream SKILL.md/CLI_REFERENCE.md read in full or targeted excerpt; 8 upstream commands sampled at 2 representative files; 3 in-repo config/hook files read in full; sync.py read for its path-confinement helper pair; capability.json steps[] block read)
**Pattern extraction date:** 2026-08-16
