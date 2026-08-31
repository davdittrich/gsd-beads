---
name: gsd-beads-sync
description: "Sync PLAN.md tasks into beads (bd) issues under a phase epic, binding identity via <beads-id>"
argument-hint: "[PLAN.md path]"
allowed-tools:
  - Read
  - Bash
---

**STOP -- DO NOT READ THIS FILE. You are already reading it. This prompt was injected into your context by the command system. Using the Read tool on this file wastes tokens. Begin executing Step 0 immediately.**

## Step 0 -- Banner

**Before ANY tool calls**, display this banner:

```
GSD > BEADS SYNC
```

Then proceed to Step 1.

## Step 1 -- Config Gate

Check whether the beads capability is enabled by reading `.planning/config.json` directly with the Read tool.

1. Read `.planning/config.json` with the Read tool.
2. If the file exists, `config.beads` is present, and `config.beads.enabled` is explicitly the boolean `false`: display the disabled message and **STOP**.
3. Otherwise -- the file is missing, `config.beads` is absent, or `config.beads` is present with no `enabled` key -- fall through to the shipped default (`beads.enabled: true` in `capability.json`) and proceed to Step 2.

**Disabled message:**

```
GSD > BEADS SYNC

Beads sync is disabled (beads.enabled).
Nothing was synced; the loop proceeds normally.
```

This step is `onError: skip` at `plan:post` -- sync never fails a phase.

## Step 2 -- bd-availability gate

`bd` usability is not checked here directly -- it is delegated to `sync.py`, which locates the
binary and runs one cheap read command as its first action (B6/D-08). If `bd` is absent, failing,
or locked, `sync.py` prints the one required notice line, appends an entry to `.planning/STATE.md`
under `### Blockers/Concerns`, and exits 0. Proceed straight to Step 3 -- do not duplicate the
check here.

## Step 3 -- Sync dispatch

Run the sync script via Bash against the PLAN.md path taken from `$ARGUMENTS`:

```bash
SYNC_PY=""
for candidate in \
  "${CLAUDE_PROJECT_DIR:-}/.gsd/capabilities/beads/scripts/sync.py" \
  "${GSD_HOME:-$HOME}/.gsd/capabilities/beads/scripts/sync.py" \
  "${CLAUDE_PLUGIN_ROOT:-}/.gsd/capabilities/beads/scripts/sync.py"
do
  if [ -f "$candidate" ]; then SYNC_PY="$candidate"; break; fi
done
if [ -z "$SYNC_PY" ]; then
  echo "gsd-beads: sync.py not found in project, global, or plugin capability roots" >&2
  exit 1
fi
python3 "$SYNC_PY" create-issues <PLAN.md path>
```

This is a single-call dispatch -- the script parses every `<task>` block in
the plan, verifies every existing `<beads-id>` before any create, resolves or
creates one phase epic, and resolves or creates one beads issue per task.
`<beads-id>` remains authoritative. The script rewrites the plan with the
resolved `beads_epic` and missing `<beads-id>` values; exact `auto` and `tracer`
tasks also gain deterministic `tracker-id="beads:<id>"` attributes. Checkpoints
and tasks with missing, partial, prefixed, case-variant, or unknown `type`
attributes never gain `tracker-id`. A newly created issue still inserts its
missing `<beads-id>` on first sync; apart from that insertion, these excluded
task blocks retain their original bytes.

## Step 4 -- Report

Print the one-line summary `sync.py` printed to stdout: either
`Synced <n> issue(s) -> epic <id>` or the B6/D-08 skip notice `bd unavailable -- sync skipped`.

## Anti-Patterns

1. DO NOT resolve a task to an issue by matching its title -- identity is bound exclusively by the
   `<beads-id>` element; a renamed task must resolve to the same issue, never create a duplicate.
2. DO NOT assemble a `bd` invocation as a shell string built from PLAN.md text -- every `bd` call
   is a typed argv list passed to `subprocess.run([...])` with shell execution left disabled
   (N4, threat T-01-01).
3. DO NOT assume the wave hook carries a single task -- a phase's `plan:post` sync covers every
   task in the one plan just written; a later `execute:wave:post` dispatch (Plan 03's
   `beads-status`) covers every task across every plan in the wave, never one task at a time.
4. DO NOT skip the config gate or the `<beads-id>`-first identity resolution.
