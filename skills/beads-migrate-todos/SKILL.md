---
name: gsd-migrate-todos
description: "Use when asked to migrate .planning/todos/pending/ entries into beads (bd) issues, a one-shot move"
argument-hint: ""
allowed-tools:
  - Read
  - Bash
---

Display `GSD > MIGRATE TODOS` before any tool call.

## Step 1 -- Config gate

Read `.planning/config.json`. Print the message below and stop only when `config.beads.enabled` is
explicitly `false`; a missing file, a missing `beads` object, and a missing `enabled` key all mean
enabled.

```
GSD > MIGRATE TODOS

Beads sync is disabled (beads.enabled).
Nothing was migrated; no todo files were touched.
```

## Step 2 -- Migration dispatch

`sync.py` checks `bd` itself. When `bd` is absent, failing, or locked it prints one notice line,
appends to `.planning/STATE.md` under `### Blockers/Concerns`, and exits 0 without a `bd create`;
go straight to the call. It takes no arguments and finds the project's `.planning/todos/pending/`
itself:

```bash
_B="${GSD_HOME:-${HOME:-}}"
case "$_B" in /?*) ;; *) echo "gsd-beads: no absolute GSD_HOME or HOME; refusing to resolve sync.py" >&2; exit 1;; esac
_G="$_B/.gsd/capabilities/beads"
_P="${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/scripts/sync.py}"
if [ -e "$_G/capability.json" ] || [ -L "$_G/capability.json" ]; then SYNC_PY="$_G/scripts/sync.py"
elif [ -f "$_P" ]; then SYNC_PY="$_P"
else SYNC_PY=; fi
if [ ! -f "$SYNC_PY" ]; then
  echo "gsd-beads: sync.py not found in global or plugin roots" >&2
  exit 1
fi
python3 -I "$SYNC_PY" migrate-todos
```

Every parseable `.planning/todos/pending/*.md` becomes one `bd create` issue (`severity` ->
priority, `area` -> an `area-<area>` label, problem/solution/files folded into the description).
A file is deleted only after its `bd create` succeeds. A todo missing required frontmatter stays
untouched and is reported apart from a todo whose parse succeeded but whose `bd create` failed.

## Step 3 -- Report

Print `sync.py`'s stdout verbatim: it names the moved, could-not-be-interpreted, and
bd-create-failed counts and lists each item under its own heading. Console output is the whole
report; bd is the durable record, so write no report file.
