---
name: gsd-beads-sync
description: "Use after a gsd PLAN.md is written (plan:post), or when asked to sync a plan's tasks into beads (bd) issues under a phase epic, binding identity via <beads-id>"
argument-hint: "[PLAN.md path]"
allowed-tools:
  - Read
  - Bash
---

Display `GSD > BEADS SYNC` before any tool call.

## Step 1 -- Config gate

Read `.planning/config.json`. Print the message below and stop only when `config.beads.enabled` is
explicitly `false`; a missing file, a missing `beads` object, and a missing `enabled` key all mean
enabled.

```
GSD > BEADS SYNC

Beads sync is disabled (beads.enabled).
Nothing was synced; the loop proceeds normally.
```

This step is `onError: skip`: sync never fails a phase.

## Step 2 -- Sync dispatch

`sync.py` checks `bd` itself. When `bd` is absent, failing, or locked it prints one notice line,
appends to `.planning/STATE.md` under `### Blockers/Concerns`, and exits 0; go straight to the call.
Run it against the PLAN.md path from `$ARGUMENTS`:

```bash
_B="${GSD_HOME:-${HOME:-}}"
case "$_B" in /?*) ;; *) echo "gsd-beads: no absolute GSD_HOME or HOME; refusing to resolve sync.py" >&2; exit 1;; esac
_G="$_B/.gsd/capabilities/beads"
_P="${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/scripts/sync.py}"; case "$_P" in /?*) ;; *) _P= ;; esac
if [ -e "$_G/capability.json" ] || [ -L "$_G/capability.json" ]; then SYNC_PY="$_G/scripts/sync.py"
elif [ -f "$_P" ]; then SYNC_PY="$_P"
else SYNC_PY=; fi
if [ ! -f "$SYNC_PY" ]; then
  echo "gsd-beads: sync.py not found in global or plugin roots" >&2
  exit 1
fi
python3 -I "$SYNC_PY" create-issues <PLAN.md path>
```

The script parses every `<task>` block in the plan, verifies every existing `<beads-id>` before any
create, resolves or creates one phase epic, and resolves or creates one issue per task.
`<beads-id>` is authoritative: a renamed task keeps its issue, and a title never identifies one.
The script rewrites the plan with the resolved `beads_epic` and each missing `<beads-id>`; exact
`auto` and `tracer` tasks also gain `tracker-id="beads:<id>"`. Every other task keeps its bytes
apart from the inserted `<beads-id>`.

Omit `<beads-id>` entirely from a task not yet bound to an issue. A placeholder such as `TBD` is
not an identity: one shaped like a bd id (lowercase, hyphenated, e.g. `gsd-beads-xy2`) reads as a
deleted issue, so sync reports a divergence and creates nothing for that task.

## Step 3 -- Report

Print the one-line summary `sync.py` printed: `Synced <n> issue(s) -> epic <id>` or the skip
notice `bd unavailable -- sync skipped`. `<n>` counts newly created issues only, so a re-run of a
fully synced plan legitimately prints `Synced 0 issue(s)`.

When every task's stored `<beads-id>` diverged from bd, `sync.py` also prints
`beads-sync: 0 of <n> task(s) bound`. Stop and investigate that line before proceeding: no issue
exists for this phase.
