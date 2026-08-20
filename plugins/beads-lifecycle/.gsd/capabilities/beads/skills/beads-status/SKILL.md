---
name: gsd-beads-status
description: "Batch-close every completed task's beads (bd) issue across every plan in a just-finished wave (lifecycle dispatch), or print the on-demand plan-task <-> bd issue mapping for a phase, including orphans on both sides, when invoked directly (B13)"
argument-hint: "[phase directory] [plan id...] -- lifecycle dispatch passes plan ids; a bare on-demand call passes only [phase directory] (or nothing, to use the current phase)"
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
2. If the file exists, `config.beads` is present, and `config.beads.enabled` is explicitly the boolean `false`: display the disabled message and **STOP**.
3. Otherwise -- the file is missing, `config.beads` is absent, or `config.beads` is present with no `enabled` key -- fall through to the shipped default (`beads.enabled: true` in `capability.json`) and proceed to Step 2.

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
"beads-status"`: `execute:wave:pre`, `execute:wave:post`, `verify:post`, and `ship:pre`. It is also
directly invokable by a human or another skill (B13/D-07) via a bare `/gsd-beads-status [phase]`
call, which carries none of those four lifecycle-point markers at all. Determine which point
dispatched this run and follow the matching branch below -- **do not** collapse any two of them
into one call; a future editor who merges branches will silently either close issues too early (at
`execute:wave:pre`, before the wave's work exists), stop naming the wave's issues to the
orchestrator (at `execute:wave:post`, after it no longer matters for prompt composition), dispatch
a spurious close-wave at `verify:post` (which has no wave/plan-id context at all), skip recording
an override at `ship:pre`, or start reconciling bd state from what should be a read-only on-demand
report.

**At `execute:wave:pre`** (before any executor `Agent()` call is spawned for this wave): follow
**Step 2a** below, then **stop** -- do not proceed to Step 2's close-wave dispatch.

**At `execute:wave:post`** (after every plan in this wave has merged): proceed directly to the
existing **Step 2** close-wave dispatch, unchanged from Phase 1.

**At `verify:post`** (once per phase, after UAT records zero issues, before the phase-completion
predicate): follow **Step 2b** below, then **stop** -- do not proceed to Step 2's close-wave
dispatch.

**At `ship:pre`** (once per phase, immediately before the ship gates evaluate): follow
**Step 2c** below, then **stop** -- do not proceed to Step 2's close-wave dispatch.

**Bare invocation (no lifecycle-point marker)** (this run carries none of the four lifecycle
markers above -- i.e. it is a direct `/gsd-beads-status [phase]` call from a human or another
skill, not a dispatch from gsd-core's own `steps[]` loop): follow **Step 2e** below, then **stop**
-- do not fall through to Step 2's close-wave dispatch.

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

## Step 2b -- verify:post: Reconcile stale closes, then regenerate BEADS.md

Run two Bash calls, **in this order**, both passing only the phase directory -- there is no
wave/plan-id list at this lifecycle point:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py reconcile-stale-closed <phase directory>
python3 .gsd/capabilities/beads/scripts/sync.py regenerate-beads-md <phase directory>
```

**Ordering matters and is not incidental**: `reconcile-stale-closed` must run first. It is the
phase-wide backstop for D-08 -- it closes every issue whose owning plan's `SUMMARY.md` exists but
whose bd issue is still open, across every plan in the phase, not just the plan ids one wave's
`close-wave` dispatch happened to carry. Running `regenerate-beads-md` before it would compute
`blocking_open`/`diverged` from the pre-reconciliation state and hand `ship:pre`'s gates a
projection that is one step stale -- exactly the class of gap this step exists to close.

This pass is phase-wide and idempotent: `filter_open_ids` re-queries bd's live status immediately
before closing, so it is safe to run on every `verify:post` dispatch regardless of how many times
it has already run over this phase -- a repeat run closes nothing. It exists specifically because
the per-wave `execute:wave:post` dispatch (Step 2 below) is empirically skippable: Phase 14's waves
2 and 3 left four issues (`gsd-beads-bu0.3`-`.6`) open despite both plans' `SUMMARY.md` files being
committed, because nothing after `execute:wave:post` ever re-checked wave-close state.

`regenerate-beads-md` then runs second, over the now-reconciled state, printing no
`<beads_status>` block and taking no plan-id argument, since there is no executor prompt to compose
here and no single wave's issues to name -- it regenerates `BEADS.md`, recomputing
`blocking_open`/`diverged` (D-03) from post-reconciliation data, so the projection going into
`ship:pre`'s gates is fresh. Report both commands' stdout. Then stop; do not call the wave-scoped
`close-wave` from this branch (see Anti-Pattern 6).

## Step 2c -- ship:pre: record an override if one occurred

Read `{padded_phase}-BEADS.md`'s `blocking_open`/`diverged` frontmatter fields and
`.planning/config.json`'s `beads.ship_gate` value. When `beads.ship_gate` is `false` **and**
(`blocking_open > 0` **or** `diverged > 0`), run:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py ship-override <phase directory>
```

and report its printed summary (the recorded git trailer, and the bd comment outcome or B6 skip
notice). Otherwise this branch is a no-op -- print nothing.

## Step 2d -- ship:pre: verify the local ship.md patch (reapply check)

This step always runs at `ship:pre`, independent of whether Step 2c did anything. Run:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py check-patch ship-md
```

If its output contains the "⚠" warning line, surface it to the user verbatim -- never swallow it
-- but never block shipping on it; this is diagnostic only, matching the `onError: skip` this
entire beads-status `ship:pre` dispatch already runs under.

## Step 2e -- Bare invocation: On-demand status (B13)

Resolve `phase_dir` from `$ARGUMENTS` when a phase directory (or phase number) was given. When
`$ARGUMENTS` is empty, pass it through verbatim (i.e. give no phase-directory argument at all) --
`sync.py status`, called with no argument, resolves the default itself from `STATE.md`'s
`current_phase` frontmatter (D-08). Do not resolve a default phase directory yourself here; that
would duplicate `_resolve_default_phase_dir`'s logic in a second place.

```bash
python3 .gsd/capabilities/beads/scripts/sync.py status [phase directory]
```

Print its stdout verbatim, including both orphan sections ("Issues with no matching plan task" and
"Plan tasks with no bd issue") -- this is a read-only report; nothing about the phase-task/bd
mapping is reconciled or written by this call.

## Patch Status (gap closed locally, 03-03)

The two hardcoded `capId` checks (`security`/`broken-windows`) that made the installed
`/gsd-ship` workflow's `ship:pre` dispatch gap true during Plan 02's planning are now joined by a
generic `ship:pre` **step** dispatch loop, patched locally into the installed
`$HOME/.claude/gsd-core/workflows/ship.md` (marked with the `gsd-beads-patch:
ship-pre-generic-dispatch v2` comment, reapply source in `GSD-CORE-PATCH.md`, confirmed present by
Step 2d above on every `ship:pre` dispatch).

The **gate** half of that gap is already fixed upstream: open-gsd/gsd-core#3559, closed COMPLETED
via PR #3608, shipped in gsd-core v1.11.0, which dispatches every capability's declared `ship:pre`
gate natively. (An earlier revision of this file cited #3554 — that issue was closed NOT_PLANNED
without review and never tracked anything.) The **step** half has no upstream track and no native
equivalent, which is why v2 of the patch still exists; once that lands natively, this local patch
(and this Step 2d / `GSD-CORE-PATCH.md`) should be deleted, not kept as permanent duplication.

**CR-01 (03-03 code review):** Step 2d's own call site is reachable only through the dispatch loop
the patch installs -- if a `gsd-core` update or capability reinstall silently strips the patch,
Step 2d never runs either, so it *confirms* an intact patch but cannot *detect* a lost one. The
actual detector is `beads-recall/SKILL.md`'s Step 3.5 (`plan:pre`, dispatched by gsd-core's own
native generic step-dispatch loop -- independent of `ship.md`'s patched loop entirely), which keeps
firing even when the patch has been dropped. Do not treat Step 2d alone as sufficient patch-loss
detection.

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
   `verify:post` fires once per **phase** (not once per wave). It still never dispatches the
   wave-scoped `close-wave` subcommand (it has no wave/plan-id context to pass), and now always
   dispatches the phase-wide `reconcile-stale-closed` subcommand, which takes no plan-id list at
   all -- the two subcommands are not interchangeable, and a future editor must not collapse them
   into one call.
6a. DO NOT treat `reconcile-stale-closed` as a replacement for the `execute:wave:post` `close-wave`
    dispatch, or vice versa. `close-wave` stays the fast path that closes a wave's issues as soon
    as that wave lands; `reconcile-stale-closed` is the phase-wide backstop for when that dispatch
    was missed (D-08). Removing either one loses something real: dropping `close-wave` means every
    issue sits open until the next `verify:post`; dropping `reconcile-stale-closed` reintroduces the
    exact gap that left Phase 14's `gsd-beads-bu0.3`-`.6` open for eleven phases.
7. DO NOT embed the `<beads_status>` block's content inside a manifest-level fragment file and
   expect it to reach the executor automatically -- `execute:wave:pre` has no template slot that
   forwards fragment text into a spawned `Agent()` call's `prompt=`. Pasting the block into that
   `prompt=` string is your own next action as the orchestrator, per Step 2a.
8. DO NOT assume this SKILL.md registration alone makes `/gsd-ship` block -- Step 2d verifies the
   installed `ship.md` patch is present on every `ship:pre` dispatch (see "Patch Status" above).
9. DO NOT skip Step 2d or swallow its "⚠" warning when the local `ship.md` patch is missing -- it
   is diagnostic-only (never blocks shipping), but a silently-dropped patch means Plan 01/02's
   gates and `ship_override` stop firing with no other visible signal.
10. DO NOT call `bd close`, `bd update`, or `bd comment` from the on-demand status branch (Step
    2e) -- it only reports the plan-task <-> bd issue mapping and its orphans, it never
    reconciles bd state (mirrors `beads-recall`'s own read-only discipline; T-04-05).
