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
2. If the file does not exist, or `config.beads` is absent, or `config.beads.enabled !== true`: display the disabled message and **STOP**.
3. Otherwise proceed to Step 2.

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
