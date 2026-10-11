---
name: gsd-beads-recall
description: "Use before planning a gsd phase (plan:pre), or when asked which open beads (bd) issues may touch a phase: writes BEADS-RECALL.md naming each one"
argument-hint: "[phase directory]"
allowed-tools:
  - Read
  - Bash
---

Display `GSD > BEADS RECALL` before any tool call.

## Step 1 -- Config gate

Read `.planning/config.json`. Print the message below and stop only when `config.beads.enabled` is
explicitly `false`; a missing file, a missing `beads` object, and a missing `enabled` key all mean
enabled.

```
GSD > BEADS RECALL

Beads recall is disabled (beads.enabled).
Nothing was written; the loop proceeds normally.
```

This step is `onError: skip`: recall never fails a phase.

## Step 3 -- Recall dispatch

`sync.py` checks `bd` itself. When `bd` is absent, failing, or locked it prints one notice line,
appends to `.planning/STATE.md` under `### Blockers/Concerns`, overwrites `BEADS-RECALL.md` with
`recall_status: failed`, and exits 0; go straight to the call. One Bash call, passing the phase
directory:

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
python3 -I "$SYNC_PY" beads-recall <phase directory>
```

One `bd list` call fetches every open, non-epic issue. Each is matched to the phase's scope by a
`<beads-id>` reverse lookup against every `PLAN.md`'s `<files>` element, then by a
case-insensitive substring match on its description. The result goes to
`{phase_dir}/{padded_phase}-BEADS-RECALL.md`, even when no issue is open. An issue matching
neither way is listed under "Unscoped", never dropped. A successful run carries
`recall_status: ok`; a failed `bd list` overwrites the file with `recall_status: failed` and a
`recall_error`, so one key tells a consumer which it is.

## Step 3.5 -- verify the local gsd-core patch

Always runs after Step 3, even when `bd` was unavailable (it reads only the installed workflow file):

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
user verbatim. Let planning proceed whatever it prints: the check is diagnostic. This is the call that detects a
lost `ship.md` patch; `beads-status` Step 2d only confirms an intact one. It stays independent of
the patch because `hooks/lifecycle-dispatch.sh` dispatches `plan:pre`, so it fires whether or not
the patch survived a `gsd-core` update.

## Step 4 -- Report

Print the one-line summary `sync.py` printed: `BEADS-RECALL.md written: <n> matched, <m> unscoped
(<t> open issue(s) total)`, or `BEADS-RECALL.md recall failed: <reason>` when `bd` was unavailable
or `bd list` failed or timed out. The failure case still writes `BEADS-RECALL.md`.
