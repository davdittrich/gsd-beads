---
name: gsd-beads-close
description: "Use when a gsd lifecycle point dispatches beads-close (verify:post, ship:pre), or when asked to close a verified phase's bd epic: closes the phase epic when verified, then lists non-closed tickets to reconcile"
argument-hint: "[phase directory]"
allowed-tools:
  - Read
  - Bash
---

Display `GSD > BEADS CLOSE` before any tool call.

Read `.planning/config.json`. Stop silently only when `config.beads.enabled` is explicitly `false`; a
missing file, `beads` object, or `enabled` key means enabled.

One Bash call. Only the phase directory (or a bare phase number, which the commands resolve) matters; use the
dispatch's phase directory, else `$ARGUMENTS`. Flags such as `--auto <ws>` are ignored, so passing the whole
`$ARGUMENTS` is acceptable.

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
python3 -I "$SYNC_PY" close-phase-epic <phase directory>
python3 -I "$SYNC_PY" reconcile-report <phase directory>
```

`close-phase-epic` regenerates `{padded_phase}-BEADS.md` first, then closes the phase epic only when all hold:

- `beads.epic_per` is `phase`.
- `{padded_phase}-VERIFICATION.md` has `status: passed` (case-insensitive).
- `BEADS.md` shows `blocking_open: 0` and `diverged: 0`.
- The epic is not a milestone epic, is not already closed, and has at least one child.
- Every child is closed.

Otherwise the epic stays open. Wrong `epic_per` or a status other than `passed` print nothing; every
other refusal prints its reason on stdout (for open children, their ids). A `bd` failure never fails
the phase. Report their stdout.

`reconcile-report` is read-only: it lists non-closed tickets that `BEADS-RECALL.md` matched or that are epic
children no plan task names. It prints nothing when there are none and no source degraded; a `bd` failure is
never fatal.
