---
name: gsd-beads-reconcile
description: "Use when a gsd lifecycle point dispatches beads reconcile (verify:post, ship:pre), or when asked which non-closed bd tickets a phase should reconcile before completing"
argument-hint: "[phase directory]"
allowed-tools:
  - Read
  - Bash
---

Display `GSD > BEADS RECONCILE` before any tool call.

Read `.planning/config.json`. Stop silently only when `config.beads.enabled` is explicitly `false`; a
missing file, `beads` object, or `enabled` key means enabled.

Pass the phase directory from the dispatch args (`$ARGUMENTS`); with none, use the current phase's directory.

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
python3 -I "$SYNC_PY" reconcile-report <phase directory>
```

Report its stdout. It is a read-only list of non-closed tickets to reconcile before completing (matched
by `BEADS-RECALL.md`, or under the phase epic with no plan task); it prints nothing when none, and a `bd`
failure is never fatal (`STATE.md` blocker, exit `0`).
