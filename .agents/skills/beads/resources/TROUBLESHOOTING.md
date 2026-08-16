# Troubleshooting

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

## Contents

- [No Active Workspace](#no-active-workspace)
- [Dependencies Not Persisting](#dependencies-not-persisting)
- [Stale Claim Blocking the Ready Queue](#stale-claim-blocking-the-ready-queue)
- [Interactive Editor Hangs an Agent Turn](#interactive-editor-hangs-an-agent-turn)
- [Nothing Injected at Session Start](#nothing-injected-at-session-start)
- [`bd prime` Prints Generic Output Instead of the gsd Override](#bd-prime-prints-generic-output-instead-of-the-gsd-override)

---

## No Active Workspace

### Symptom
```bash
bd ready
# Error: no beads workspace found
```

### Cause
The current directory (or any parent) has no `.beads/` directory — `bd` was never initialized here, or you're outside the repository entirely.

### Fix
```bash
bd where           # confirms whether a workspace is discoverable from here
bd init             # initializes .beads/ in the current directory if none exists
```
Do not run `bd init` inside a subdirectory of an already-initialized repo — check `bd where` first; a nested `.beads/` is a separate, disconnected workspace.

## Dependencies Not Persisting

### Symptom
```bash
bd dep add issue-2 issue-1 --type blocks
# Reports: added dependency
bd show issue-2
# Shows: no dependencies listed
```

### Cause
Usually a stale `bd` binary — this class of bug was fixed upstream in bd v0.15.0 (GitHub issue #101, dependencies silently ignored during issue creation).

### Fix
```bash
bd version                    # check your version
# upgrade if old, then:
bd dolt stop && bd dolt start # restart the server so the fix takes effect
bd dep add issue-2 issue-1 --type blocks
bd show issue-2                # confirm the dependency now appears
```
If it's still missing after upgrading, run `bd doctor` and check the Dolt server is actually running before assuming the data layer is broken.

## Stale Claim Blocking the Ready Queue

### Symptom
An issue you know is actually available doesn't show in `bd ready`, but `bd show <id>` reports it as `in_progress` with an assignee nobody recognizes as active.

### Cause
A prior session claimed the issue (`bd update <id> --claim`) and never released or closed it — a crash, a reset, or an abandoned attempt.

### Fix
```bash
bd show <id>                          # read the comments first — was there a partial finding?
bd update <id> --assignee=             # release the stale claim
bd ready                               # confirm it's now available
```
Never force-release a claim without reading its comments first — see RESUMABILITY.md's recovery sequence.

## Interactive Editor Hangs an Agent Turn

### Symptom
A `bd` command appears to hang indefinitely with no output and no error.

### Cause
`bd edit` (and any command that falls back to `$EDITOR`) opens an interactive terminal editor. An agent has no terminal to interact with, so the process blocks forever waiting for input that will never arrive.

### Fix
Never call `bd edit`. Use the non-interactive flag form instead:
```bash
bd update <id> --title="New title" --description="New description" --priority=1
```
Every field `bd edit` can change has an equivalent `bd update --<flag>` form.

## Nothing Injected at Session Start

### Symptom
A new session starts with no workflow context — no reminder of `bd ready`, no phase epic info, nothing.

### Cause
Either the SessionStart hook isn't installed for this project, or it ran but `bd` itself failed silently (binary missing, workspace not discoverable).

### Fix
```bash
cat hooks/hooks.json | grep -A2 SessionStart   # confirm the hook is registered
bd prime                                        # run it manually — does it produce output?
bd where                                        # confirms bd can find a workspace at all
```
If `bd prime` works manually but the hook never fired, the harness may not be picking up `hooks/hooks.json` for this project — check the plugin/hook install path, not `bd` itself.

## `bd prime` Prints Generic Output Instead of the gsd Override

### Symptom
`bd prime` prints beads' stock workflow reminder text — no mention of gsd-core phase epics, sync points, or the ship gate.

### Cause
`.beads/PRIME.md` is absent. `bd prime` only overrides its default output when that file exists in the local clone or resolved workspace (`bd prime --help`) — with it missing, it silently falls back to the generic default, not an error.

### Fix
```bash
test -f .beads/PRIME.md && echo present || echo missing
```
If missing, the fix is that the SessionStart hook (`hooks/session-start.sh`) should have restored it from `.agents/skills/beads/PRIME.md` on the last session start. Check the hook actually ran (see "Nothing Injected at Session Start" above), or restore it directly:
```bash
cp .agents/skills/beads/PRIME.md .beads/PRIME.md
bd prime | grep -qF 'execute:wave:post' && echo "override active"
```
