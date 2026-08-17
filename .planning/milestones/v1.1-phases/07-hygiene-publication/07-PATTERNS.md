# Phase 7: Hygiene & Publication - Pattern Map

**Mapped:** 2026-08-16
**Files analyzed:** 1 (config edit) + 2 non-file operations (history rewrite, remote creation)
**Analogs found:** 1 / 1 file edits; 0 / 2 shell operations (no in-repo analog exists for either)

## Scope note

This phase has no application code deliverables. Per ROADMAP §Phase 7, the three units of work are:

1. Edit `.gitignore` (the only text file this phase modifies).
2. Run `git filter-repo` to strip 4 named files from all history (a one-shot CLI operation, not a source file).
3. Run `gh repo create` + `git push` (a one-shot CLI operation, not a source file).

There are no controllers/services/components/models to classify — the planner should treat items 2 and 3 as scripted shell procedures (exact invocations already specified verbatim in ROADMAP.md and RESEARCH.md), not as code requiring an analog.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.gitignore` (root, edit) | config | file-I/O | `.gitignore` (root, itself — extend in place) | exact (self-analog) |
| `06-PATTERNS.md` (commit, no content change) | n/a — git add only | n/a | n/a | not applicable, no pattern needed |

No controller/service/component/model files exist in this phase's scope.

## Pattern Assignments

### `.gitignore` (config, file-I/O)

**Analog:** the file itself — extend existing conventions, do not restructure.

**Current full contents** (`/home/dd/Gemini/gsd-beads/.gitignore`, 8 lines):
```gitignore
__pycache__/
*.pyc

# Beads / Dolt files (added by bd init)
.dolt/
*.db
.beads-credential-key
.beads/proxieddb/
*.gate.lock*
```

**Convention observed:**
- Blank line separates unrelated groups.
- Each group has a `# Comment` header naming the subsystem/origin (`# Beads / Dolt files (added by bd init)`).
- Entries are one bare pattern per line, no trailing inline comments, no quoting.
- Directory patterns end in `/`; wildcard patterns use bare `*`.

**Additions required by CONTEXT.md D-01/D-02 and ROADMAP Success Criterion 2**, following the same group+comment convention:
```gitignore
# Beads backup/interaction artifacts
.beads.backup-pre-recovery/
.beads/interactions.jsonl
*.bak

# Editor/tooling local state
.serena/
```
(`.gsd/dispatch-isolation-sentinel.json`: per D-01, inspect content before deciding ignore vs. delete — file already read during pattern-mapping: contents are `{"isolation":"none","harness_flag":null,"phase":"06","plan":null,"written_at":...}`, a regenerated per-dispatch state file, not committed source — supports gitignore over delete, add as its own line if kept, under the same "Editor/tooling local state" group or a new `# GSD dispatch state` group.)

**Nested `.gitignore` files already exist and take precedence for their own trees** — do not duplicate their entries in root `.gitignore`:
- `.beads/.gitignore` (1917 bytes) already scopes `.beads/` internals.
- `.serena/.gitignore` (26 bytes) already scopes `.serena/` internals — but since `.serena/` itself is untracked and undecided (D-01), the root-level ignore of `.serena/` (whole dir) makes the nested one moot unless `.serena/` is later force-added.

## Shared Patterns

None — no cross-cutting code pattern (auth, error handling, validation) applies; this phase touches no application logic.

## No Analog Found

| File / Operation | Role | Data Flow | Reason |
|---|---|---|---|
| `git filter-repo` invocation | n/a (shell procedure) | batch/one-shot | No prior filter-repo run exists in this repo's history or scripts; ROADMAP.md and RESEARCH.md already specify the exact invocation verbatim — planner should cite those directly, not a codebase analog. |
| `gh repo create` + push | n/a (shell procedure) | one-shot | No prior remote-creation script exists (`git remote -v` is empty, first-time setup); RESEARCH.md/CONTEXT.md D-04/D-05 already specify exact flags — planner should cite those directly. |

## Metadata

**Analog search scope:** repo root (`.gitignore`), `.beads/.gitignore`, `.serena/.gitignore`, `.gsd/dispatch-isolation-sentinel.json`
**Files scanned:** 4
**Pattern extraction date:** 2026-08-16
