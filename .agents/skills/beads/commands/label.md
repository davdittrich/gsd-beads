---
description: Manage issue labels
argument-hint: "[command] [issue-id] [label]"
---

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

Labels are flexible cross-cutting metadata beyond the structured fields (status, priority, type).

## Common invocations

```bash
bd label add <issue-id> <label>       # tag an issue
bd label remove <issue-id> <label>    # untag an issue
bd label list <issue-id>              # labels on one issue
bd label list-all                     # every unique label in the database
```

## gsd-core convention

`sync.py` labels every issue it creates `gsd-sync`, so `bd list --label gsd-sync --all -n 0` lists them as a flat set. A phase label such as `phase-09` exists only if you add it by hand.
