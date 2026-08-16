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

Labelling an issue with its phase slug (e.g. `phase-09`) lets a phase's issues be pulled as a set with `bd search --label phase-09`, independent of the `parent-child` epic hierarchy that already groups them structurally — useful when you want a flat list rather than a tree.
