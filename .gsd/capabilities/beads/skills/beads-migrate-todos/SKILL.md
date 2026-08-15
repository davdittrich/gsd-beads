---
name: gsd-migrate-todos
description: "One-shot migration of .planning/todos/pending/ entries into bd issues (B12)"
argument-hint: ""
allowed-tools:
  - Read
  - Bash
---

**STOP -- DO NOT READ THIS FILE. You are already reading it. This prompt was injected into your context by the command system. Using the Read tool on this file wastes tokens. Begin executing Step 0 immediately.**

## Step 0 -- Banner

**Before ANY tool calls**, display this banner:

```
GSD > MIGRATE TODOS
```

Then proceed to Step 1.

## Step 1 -- Config Gate

Check whether the beads capability is enabled by reading `.planning/config.json` directly with the Read tool.

1. Read `.planning/config.json` with the Read tool.
2. If the file does not exist, or `config.beads` is absent, or `config.beads.enabled !== true`: display the disabled message and **STOP**.
3. Otherwise proceed to Step 2.

**Disabled message:**

```
GSD > MIGRATE TODOS

Beads sync is disabled (beads.enabled).
Nothing was migrated; no todo files were touched.
```

## Step 2 -- bd-availability gate

`bd` usability is not checked here directly -- it is delegated to `sync.py`, which locates the
binary and runs one cheap read command as its first action (B6/D-08). If `bd` is absent, failing,
or locked, `sync.py` prints the one required notice line, appends an entry to `.planning/STATE.md`
under `### Blockers/Concerns`, and exits 0 without issuing any `bd create` calls. Proceed straight
to Step 3 -- do not duplicate the check here.

## Step 3 -- Migration dispatch

Run the migration script via Bash. This subcommand takes no arguments -- it resolves the current
project's `.planning/todos/pending/` directory itself:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py migrate-todos
```

Every parseable `.planning/todos/pending/*.md` file becomes one mapped `bd create` issue
(`severity` -> priority, `area` -> an `area-<area>` label, problem/solution/files folded into the
description), and that file is deleted only after its `bd create` call is confirmed successful. A
todo that cannot be parsed (missing required frontmatter) is left untouched in
`.planning/todos/pending/`, reported separately from a todo whose parse succeeded but whose
`bd create` call failed.

## Step 4 -- Report

Print `sync.py`'s stdout verbatim as the report -- it already names the moved/could-not-be-
interpreted/bd-create-failed counts and lists each item under its own heading (D-13: console
output only, no `MIGRATION-REPORT.md` file).

## Anti-Patterns

1. DO NOT delete a todo file before its `bd create` call is confirmed to return code 0 (D-05).
2. DO NOT assemble a `bd` invocation as a shell string built from todo file text -- every `bd`
   call is a typed argv list passed to `subprocess.run([...])` with shell execution left disabled
   (N4, threat T-04-01).
3. DO NOT merge a parse failure ("could not be interpreted") with a `bd create` failure into one
   count or one list -- they are reported as two distinct outcomes (D-04, Pitfall 2).
4. DO NOT write a separate `MIGRATION-REPORT.md` artifact -- bd itself is the durable record of
   what moved (D-13).
5. DO NOT skip the config gate.
