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

This step is `onError: skip` at all four points (`execute:wave:pre`, `execute:wave:post`,
`verify:post`, `ship:pre`) -- no dispatch ever fails a phase.

## Step 1.5 -- Lifecycle-point branch (D-11)

This skill is registered at **four** `capability.json` `steps[]` entries, all `ref.skill:
"beads-status"`: `execute:wave:pre`, `execute:wave:post`, `verify:post`, and `ship:pre`. Determine
which point dispatched this run and follow the matching branch below -- **do not** collapse any
two of them into one call; a future editor who merges branches will silently either close issues
too early (at `execute:wave:pre`, before the wave's work exists), stop naming the wave's issues to
the orchestrator (at `execute:wave:post`, after it no longer matters for prompt composition),
dispatch a spurious close-wave at `verify:post` (which has no wave/plan-id context at all), or
skip recording an override at `ship:pre`.

**At `execute:wave:pre`** (before any executor `Agent()` call is spawned for this wave): follow
**Step 2a** below, then **stop** -- do not proceed to Step 2's close-wave dispatch.

**At `execute:wave:post`** (after every plan in this wave has merged): proceed directly to the
existing **Step 2** close-wave dispatch, unchanged from Phase 1.

**At `verify:post`** (once per phase, after UAT records zero issues, before the phase-completion
predicate): follow **Step 2b** below, then **stop** -- do not proceed to Step 2's close-wave
dispatch.

**At `ship:pre`** (once per phase, immediately before the ship gates evaluate): follow
**Step 2c** below, then **stop** -- do not proceed to Step 2's close-wave dispatch.

## Step 2a -- execute:wave:pre: Regenerate BEADS.md and compose the wave-status block (B8)

Run one Bash call passing the phase directory and **every** plan id in the wave at once:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py wave-status-block <phase directory> <plan id> [<plan id> ...]
```

This single call regenerates `BEADS.md` from a live `bd` query first (D-05..D-08's frontmatter/
table shape -- a hand edit is fully overwritten, never merged, per B11) and then prints a
`<beads_status>` block to stdout naming this wave's synced issues (id, title, status), or the
literal line `no synced issues for this wave` when none of this wave's tasks have synced yet.

**Read that printed `<beads_status>` block, then take this as a direct instruction to your own
next action, not a fact about this skill's behavior:** include the block verbatim inside **every**
executor `Agent()` call's `prompt=` string for this wave, before spawning any executor. This is
the mechanism 02-RESEARCH.md verified actually reaches a spawned executor's composed prompt at
this lifecycle point (Pattern 2: skill-mediated dispatch, not automatic manifest-level fragment
forwarding -- `execute:wave:pre` has no working slot that forwards fragment text automatically
into a spawned `Agent()` prompt). B8's literal
acceptance criterion is checked by grepping the real `prompt=` text an `Agent()` call receives for
these issue ids, not by inferring it from behavior.

## Step 2b -- verify:post: Regenerate BEADS.md only

Run one Bash call passing only the phase directory -- there is no wave/plan-id list at this
lifecycle point:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py regenerate-beads-md <phase directory>
```

This is the identical read-only call Step 2a already uses, but with no `<beads_status>` block
printed and no plan-id argument, since there is no executor prompt to compose here and no single
wave's issues to name. It regenerates `BEADS.md` -- recomputing `blocking_open`/`diverged` (D-03)
-- so the projection going into `ship:pre`'s gates is fresh. Then stop; do not call `close-wave`
from this branch.

## Step 2c -- ship:pre: record an override if one occurred

Read `{padded_phase}-BEADS.md`'s `blocking_open`/`diverged` frontmatter fields and
`.planning/config.json`'s `beads.ship_gate` value. When `beads.ship_gate` is `false` **and**
(`blocking_open > 0` **or** `diverged > 0`), run:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py ship-override <phase directory>
```

and report its printed summary (the recorded git trailer, and the bd comment outcome or B6 skip
notice). Otherwise this branch is a no-op -- print nothing.

## Known Gap (verified during Phase 3 planning)

The installed gsd-core `/gsd-ship` workflow's `preflight_checks` step only special-cases
`capId == "security"` and `capId == "broken-windows"` at `ship:pre` (confirmed by reading
`$HOME/.claude/gsd-core/workflows/ship.md` directly) -- there is no generic `ship:pre`
hook-dispatch loop for other capability ids in that file. This capability's `ship:pre`
`gates[]`/`steps[]` entries are therefore declarative and forward-compatible, **not yet
live-enforced** by `/gsd-ship`. Making them live requires either an upstream gsd-core change
(generic `ship:pre` dispatch, or a beads-specific block analogous to security/broken-windows) or a
local patch to `ship.md`; the latter is out of scope for this skill per this project's N2
constraint (overlay-only, no gsd-core fork/patch) -- raise the gap upstream instead of working
around it here (see `03-03-PLAN.md` for the machine-local patch this project separately
authorized, and open-gsd/gsd-core#3554 for the upstream request).

## Step 2 -- Batch close dispatch (execute:wave:post only)

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
5. DO NOT collapse the `execute:wave:pre` and `execute:wave:post` branches (Step 1.5) into one
   call, and DO NOT call `sync.py close-wave` from the `execute:wave:pre` branch -- closing at
   `execute:wave:pre` would close issues before this wave's executors have even started.
6. DO NOT collapse the `verify:post` branch into either of the two `execute:wave` branches --
   `verify:post` fires once per **phase** (not once per wave) and never dispatches `close-wave`.
7. DO NOT embed the `<beads_status>` block's content inside a manifest-level fragment file and
   expect it to reach the executor automatically -- `execute:wave:pre` has no template slot that
   forwards fragment text into a spawned `Agent()` call's `prompt=`. Pasting the block into that
   `prompt=` string is your own next action as the orchestrator, per Step 2a.
8. DO NOT assume this SKILL.md registration alone makes `/gsd-ship` block -- verify against the
   installed `ship.md` before relying on it (see "Known Gap" above).
