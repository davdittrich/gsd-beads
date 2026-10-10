---
description: List blocked issues
argument-hint: "[--parent id]"
---

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

Lists every issue currently excluded from `bd ready` by an open `blocks` dependency or an unresolved `bd gate`.

## Common invocations

```bash
bd blocked                         # every blocked issue
bd blocked --parent <epic-id>      # blocked issues under one epic/bead
```

## Reading the chain

`bd blocked` names the blocked issue; `bd show <id>` on it names the actual blocker(s) — the thing that needs resolving is often not the blocked issue itself but whatever it's waiting on. Chase `bd show`'s "Dependencies" section to the root blocker before deciding what to work on next.

## gsd-core framing

`blocking_open` (definition: `.beads/PRIME.md`, "Ship gate") counts every non-closed child of the phase epic, blocked or not, so `bd blocked` lists a subset of what holds `ship:pre` closed. Run it with `--parent <phase-epic-id>` before `ship:pre` to see which of those children are waiting on something.
