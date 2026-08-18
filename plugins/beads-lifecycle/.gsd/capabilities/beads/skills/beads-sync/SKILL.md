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
python3 .gsd/capabilities/beads/scripts/sync.py create-issues <PLAN.md path>
```

This is a single-call dispatch -- the script parses every `<task>` block in the plan, resolves or
creates one phase epic, resolves or creates one beads issue per task (skipping any task that
already carries a `<beads-id>`), and rewrites the plan file in place with the resolved
`beads_epic` frontmatter key and per-task `<beads-id>` elements.

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
