---
name: gsd-beads-status
description: "Batch-close every completed task's beads (bd) issue across every plan in a just-finished wave"
argument-hint: "[phase directory] [plan id...]"
allowed-tools:
  - Read
  - Bash
---

**STOP -- DO NOT READ THIS FILE. You are already reading it. This prompt was injected into your context by the command system. Using the Read tool on this file wastes tokens. Begin executing Step 0 immediately.**

## Step 0 -- Banner

**Before ANY tool calls**, display this banner:

```
GSD > BEADS STATUS
```

Then proceed to Step 1.

## Step 1 -- Config Gate

Check whether the beads capability is enabled by reading `.planning/config.json` directly with the Read tool.

1. Read `.planning/config.json` with the Read tool.
2. If the file does not exist, or `config.beads` is absent, or `config.beads.enabled !== true`: display the disabled message and **STOP**.
3. Otherwise proceed to Step 2.

**Disabled message:**

```
GSD > BEADS STATUS

Beads status is disabled (beads.enabled).
Nothing was closed; the loop proceeds normally.
```

This step is `onError: skip` at `execute:wave:post` -- a wave-close dispatch never fails a phase.

## Step 2 -- Batch close dispatch

`execute:wave:post` fires **once per wave**, after every plan in that wave has merged, carrying
`WAVE_PLAN_IDS` -- a space-separated list of the plan ids that completed in this wave. **This list
may name several plans, and each of those plans may hold several tasks.** Do not narrow this to a
single plan or a single task: a design that closes only the first id it sees silently drops every
task past the first in any wave with more than one completed task.

`bd` usability is not checked here directly -- it is delegated to `sync.py close-wave`, which
locates the binary and runs one cheap read command as its first action (B6/D-08). If `bd` is
absent, failing, or locked, `sync.py` prints the one required notice line, appends an entry to
`.planning/STATE.md` under `### Blockers/Concerns`, and exits 0.

Run one Bash call passing the phase directory and **every** plan id in the wave at once:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py close-wave <phase directory> <plan id> [<plan id> ...]
```

This is a single-call dispatch -- the script resolves each plan id's `PLAN.md` inside the phase
directory, treats a plan as complete only when its `SUMMARY.md` exists (a plan with no `SUMMARY.md`
contributes nothing), collects every `<beads-id>` of a task in a completed plan (skipping any task
with no `<beads-id>` without error), filters out ids already closed in bd, and closes every
remaining id in one `bd close` call.

## Step 3 -- Report

Print the one-line summary `sync.py` printed to stdout: either
`Closed <n> issue(s) across <m> plan(s) (...)` naming the per-plan counts and the skipped-task
count, or the B6/D-08 skip notice `bd unavailable -- sync skipped`.

## Anti-Patterns

1. DO NOT assume `execute:wave:post` carries a single task, or even a single plan. It fires once
   per **wave** and carries the full list of plan ids that completed in that wave -- a wave can
   hold several plans, and each plan can hold several tasks. A close-one-issue design silently
   misses every task past the first in any wave that completed more than one task.
2. DO NOT resolve a task to an issue by matching its title -- identity is bound exclusively by the
   `<beads-id>` element.
3. DO NOT assemble a `bd` invocation as a shell string built from PLAN.md text -- every `bd` call
   is a typed argv list passed to `subprocess.run([...])` with shell execution left disabled
   (N4, threat T-01-01).
4. DO NOT skip the config gate, and DO NOT call `sync.py close-wave` once per plan id -- always
   pass the whole `WAVE_PLAN_IDS` list to a single invocation so the close is one batch dispatch.
