---
name: gsd-beads-status
description: "Use when a gsd lifecycle point dispatches beads (execute:wave:pre, execute:wave:post, verify:post, ship:pre), or when asked for a phase's plan-task to bd-issue status report with orphans on both sides"
argument-hint: "[phase directory] [plan id...] -- lifecycle dispatch passes plan ids; a bare on-demand call passes only [phase directory] (or nothing, to use the current phase)"
allowed-tools:
  - Read
  - Bash
---

Display `GSD > BEADS STATUS` before any tool call.

## Step 1 -- Config gate

Read `.planning/config.json`. Print the message below and stop only when `config.beads.enabled` is
explicitly `false`; a missing file, a missing `beads` object, and a missing `enabled` key all mean
enabled.

```
GSD > BEADS STATUS

Beads status is disabled (beads.enabled).
Nothing was closed; the loop proceeds normally.
```

Every point is `onError: skip`: a failure here never fails the phase.

## Step 1.5 -- Pick the branch

Run exactly the branch for the dispatching point, then stop. The branches are not interchangeable:
closing at `execute:wave:pre` closes issues before the wave's work exists, and `verify:post` carries
no plan ids.

| Point | Branch |
|---|---|
| `execute:wave:pre`, before any executor `Agent()` spawns | Step 2a |
| `execute:wave:post`, after every plan in the wave merged | Step 2f, then Step 3 |
| `verify:post`, once per phase | Step 2b |
| `ship:pre`, once per phase | Step 2c, then Step 2d |
| none (a direct `/gsd-beads-status [phase]` call) | Step 2e |

## Step 2a -- execute:wave:pre: compose the wave-status block

One Bash call, passing the phase directory and **every** plan id in the wave:

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
python3 -I "$SYNC_PY" wave-status-block <phase directory> <plan id> [<plan id> ...]
```

It regenerates `BEADS.md` from live `bd` (a hand edit is overwritten, never merged) and prints a
`<beads_status>` block naming this wave's synced issues (id, title, status), or `no synced issues
for this wave`.

Paste that block verbatim into **every** executor `Agent()` call's `prompt=` string for this wave
before spawning any executor. Manifest-level fragments do not reach a spawned `Agent()` prompt, so
this paste is your own next action. Done when each executor prompt contains the block.

## Step 2b -- verify:post: regenerate BEADS.md

One Bash call, passing only the phase directory:

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
python3 -I "$SYNC_PY" regenerate-beads-md <phase directory>
```

It rewrites `BEADS.md` from live `bd` state, recomputing `blocking_open` and `diverged` for
`ship:pre`'s gates, prints no block, and changes nothing in `bd`. Report its stdout.

## Step 2c -- ship:pre: record an override

Read `{padded_phase}-BEADS.md`'s `blocking_open` and `diverged` frontmatter and `beads.ship_gate`
from `.planning/config.json`. When `beads.ship_gate` is `false` and either field is not `0` (`unknown` counts), run
the call below and report its summary (the git trailer, and the bd comment outcome or skip notice).
Otherwise print nothing.

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
python3 -I "$SYNC_PY" ship-override <phase directory>
```

## Step 2d -- ship:pre: verify the local ship.md patch

Always runs at `ship:pre`, whether or not Step 2c did anything.

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
python3 -I "$SYNC_PY" check-patch ship-md
```

When the command exits non-zero or its output lacks the word "present", show that output to the
user verbatim. Let shipping proceed whatever it prints: the check is diagnostic. It confirms an intact patch but
cannot detect a lost one, because this call site runs only through the patched loop;
`beads-recall` Step 3.5 is the detector. Patch and upstream status: `GSD-CORE-PATCH.md`.

## Step 2e -- bare invocation: on-demand status

Pass `$ARGUMENTS` through as the phase directory (or number). With no argument, pass none:
`sync.py status` resolves the current phase from `STATE.md` itself.

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
python3 -I "$SYNC_PY" status [phase directory]
```

Print stdout verbatim, including both orphan sections ("Issues with no matching plan task" and
"Plan tasks with no bd issue"). Print it and stop: this branch only reads `bd`.

## Step 2f -- execute:wave:post: close completed plans' issues

The `PostToolUse` hook runs `sync.py lifecycle-dispatch execute:wave:post` here. It reconciles the
whole phase: every completed plan's open issues close, so a wave whose dispatch was skipped heals
on the next one. A plan is **complete** when its `SUMMARY.md` exists and its `status` frontmatter
is neither `halted` nor `blocked`; tasks without a `<beads-id>` are skipped without error.

`close-wave` is the manual form, for a runtime without `PostToolUse` or a call carrying
`WAVE_PLAN_IDS` (the plan ids completed in this wave: several plans, each with several tasks).
Pass the whole list to one invocation:

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
python3 -I "$SYNC_PY" close-wave <phase directory> <plan id> [<plan id> ...]
```

The script collects the `<beads-id>` of every task in a complete plan, drops ids already closed,
and closes the rest in one `bd close` call. `sync.py` checks `bd` itself: when `bd` is absent,
failing, or locked it prints one notice, appends to `.planning/STATE.md` under
`### Blockers/Concerns`, and exits 0.

### `resolves_issues:` -- closing a standalone issue

A bd issue filed independently of any task has no `<beads-id>` link, so the close paths above never
reach it. List its id in the **frontmatter** of the completed plan's `SUMMARY.md`:

```yaml
resolves_issues: ["gsd-beads-he1"]
```

or

```yaml
resolves_issues:
  - "gsd-beads-he1"
```

`reconcile-stale-closed` adds every listed id to its candidates and closes those still open,
printing the marker-closed and rejected-entry counts on one line. Only the frontmatter is searched:
an id that appears in SUMMARY.md body prose never closes anything, so a phase that merely mentions
a newly filed follow-up cannot close it. A listed id may be any open bd issue, not only this phase's; ids are syntax-checked only. An unknown or already-closed id is a silent no-op.

## Step 3 -- Report

Print the one-line summary `sync.py` printed: `Closed <n> issue(s) across <m> plan(s) (...)`, or
the skip notice `bd unavailable -- sync skipped`.
