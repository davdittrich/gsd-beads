# gsd-beads

A gsd-core capability (`beads`) that makes `bd` the source of truth for plan-task state. `README.md` covers behaviour; this file covers working on the repo.

## Build & Test

Python 3 stdlib only; no build step. Run each suite with a throwaway `HOME`: tests resolve `${GSD_HOME:-$HOME}/.gsd`, and a real install there changes the outcome.

```bash
HOME=$(mktemp -d) python3 -I -m pytest tests -q -p no:cacheprovider   # CI runs `python3 -m unittest discover -s tests -t tests`
HOME=$(mktemp -d) bash tests/test-session-start.sh
HOME=$(mktemp -d) TMPDIR=/dev/shm bash tests/test-capability-auto-install.sh
```

`test-capability-auto-install.sh` case24 needs a local gsd-core source checkout and fails without one; the other cases are hermetic.

## Layout

- `scripts/sync.py`: every subcommand (`create-issues`, `close-wave`, `lifecycle-dispatch`, ...). `skills/*/SKILL.md` call it through a resolver fence; `tests/test_sync.py` pins the fence byte for byte.
- `hooks/`: `lifecycle-dispatch.sh` (PostToolUse), `session-start.sh`, `capability-auto-install.sh`.
- `.agents/skills/beads/`, `AGENTS.md` bd block, `.cursor/rules/beads.mdc`: bundled or generated bd guidance. Change the `bd setup` profile; do not hand-edit generated blocks.

## Conventions

- Skills and docs are agent-facing prose: follow the `writing-for-agents` skill.
- Editing `scripts/sync.py` does not affect installed skills until the capability is reinstalled.
