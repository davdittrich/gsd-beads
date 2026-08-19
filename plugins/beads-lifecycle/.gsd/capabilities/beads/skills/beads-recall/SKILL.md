---
name: gsd-beads-recall
description: "Scan open beads (bd) issues and write BEADS-RECALL.md naming any issue that may touch the phase about to be planned"
argument-hint: "[phase directory]"
allowed-tools:
  - Read
  - Bash
---

**STOP -- DO NOT READ THIS FILE. You are already reading it. This prompt was injected into your context by the command system. Using the Read tool on this file wastes tokens. Begin executing Step 0 immediately.**

## Step 0 -- Banner

**Before ANY tool calls**, display this banner:

```
GSD > BEADS RECALL
```

Then proceed to Step 1.

## Step 1 -- Config Gate

Check whether the beads capability is enabled by reading `.planning/config.json` directly with the Read tool.

1. Read `.planning/config.json` with the Read tool.
2. If the file exists, `config.beads` is present, and `config.beads.enabled` is explicitly the boolean `false`: display the disabled message and **STOP**.
3. Otherwise -- the file is missing, `config.beads` is absent, or `config.beads` is present with no `enabled` key -- fall through to the shipped default (`beads.enabled: true` in `capability.json`) and proceed to Step 2.

**Disabled message:**

```
GSD > BEADS RECALL

Beads recall is disabled (beads.enabled).
Nothing was written; the loop proceeds normally.
```

This step is `onError: skip` at `plan:pre` -- a recall dispatch never fails a phase.

## Step 2 -- bd-availability gate

`bd` usability is not checked here directly -- it is delegated to `sync.py beads-recall`, which
locates the binary and runs one cheap read command as its first action (B6/D-08). If `bd` is
absent, failing, or locked, `sync.py` prints the one required notice line, appends an entry to
`.planning/STATE.md` under `### Blockers/Concerns`, and exits 0 without writing
`BEADS-RECALL.md`.

## Step 3 -- Recall dispatch

Run one Bash call passing the phase directory:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py beads-recall <phase directory>
```

This scans every open, non-epic bd issue and matches it against this phase's expected scope by
two techniques: a cross-phase `<beads-id>` reverse lookup against every `PLAN.md`'s `<files>`
element, falling back to a `bd list --desc-contains` substring match for an issue with no
matching `<beads-id>` anywhere. The result is written to
`{phase_dir}/{padded_phase}-BEADS-RECALL.md` -- always, even when zero issues are open (D-04). An
issue matching neither technique is listed under a separate "Unscoped" heading, never dropped
(D-02).

## Step 3.5 -- verify the local gsd-core patches (independent reapply check, CR-01)

This step always runs after Step 3, whether or not `bd` was available for Step 3 (these checks
read only the installed workflow files, never `bd`). Run both, alongside each other -- the
second joins the first, it does not replace it:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py check-shipmd-patch
python3 .gsd/capabilities/beads/scripts/sync.py check-execute-plan-patch
```

If either output contains the "⚠" warning line, surface it to the user verbatim -- never swallow
it -- but never block planning on either; both are diagnostic only, matching the `onError: skip`
this entire beads-recall `plan:pre` dispatch already runs under.

This is the call site that actually *detects* patch loss for both patches (unlike `beads-status`'s
Step 2d, which only *confirms* the `ship.md` patch is still intact, and has no counterpart at all
for the `execute-plan.md` patch).

**Corrected 0.3.0 (gh-2).** The original independence argument here was that `plan:pre` "is
dispatched by gsd-core's own native generic step-dispatch loop". It is not. `plan-phase.md` §5.6
states its generic step contract but only ever fires it from Branch 5, which requires
`AUTO_CHAIN == true`, and Branch 2 returns to step 6 outright when the phase shows no frontend
indicators. A manually invoked `/gsd:plan-phase` therefore reached neither -- so the detector
shared the failure mode of the thing it protects, and had been silently not running.

Independence is now real, by a different route: `plan:pre` is dispatched by
`hooks/lifecycle-dispatch.sh`, a `PostToolUse` hook keyed on the
`gsd_run loop render-hooks plan:pre --raw` call gsd-core makes regardless of branch. That hook
runs both checks itself, so they fire whether this skill is invoked or not, and keep firing when
the patch they check has been stripped by a `gsd-core` update or capability reinstall -- the exact
scenario in which `beads-status`'s `ship:pre`-gated Step 2d cannot run at all for the `ship.md`
patch (its own call site depends on the patch it verifies), and the exact scenario the
`execute-plan.md` patch has no `ship:pre`-gated confirmation step at all (by design -- see
`GSD-CORE-PATCH.md`'s "Scope" section and Patch 2, and Anti-Pattern 5 below).

## Step 4 -- Report

Print the one-line summary `sync.py` printed to stdout: either
`BEADS-RECALL.md written: <n> matched, <m> unscoped (<t> open issue(s) total)` or the B6/D-08 skip
notice `bd unavailable -- sync skipped`.

## Anti-Patterns

1. DO NOT resolve an issue's file scope by matching its title -- scope binds through the
   `<beads-id>` reverse lookup or a `bd list --desc-contains` substring match, never a title
   string.
2. DO NOT assemble a `bd` invocation as a shell string -- every `bd` call is a typed argv list
   passed to `subprocess.run([...])` with shell execution left disabled (N4, threat T-02-01).
3. DO NOT skip the config gate.
4. DO NOT silently drop an issue that matches neither scope-matching technique -- it must appear
   under the "Unscoped" heading (D-02).
5. DO NOT skip Step 3.5 or swallow either of its "⚠" warnings -- it is the only patch-loss
   *detector* in this capability for both the `ship.md` patch (Step 2d in `beads-status` is
   confirmation-only, see Step 3.5's own note) and the `execute-plan.md` patch (which has no
   `beads-status` counterpart at all -- `check-execute-plan-patch` is deliberately NOT wired at
   `ship:pre`, see `GSD-CORE-PATCH.md` Patch 2). A future editor merging or trimming steps must
   not remove either check from this step.
