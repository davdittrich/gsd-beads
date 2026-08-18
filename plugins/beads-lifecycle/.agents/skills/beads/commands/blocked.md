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

An open blocker is exactly what makes `BEADS.md`'s `blocking_open` field non-zero, and a non-zero `blocking_open` is what holds the `ship:pre` gate closed (see `.beads/PRIME.md` — "Ship gate"). Running `bd blocked` before `ship:pre` fires is the fastest way to see what's actually holding a phase back, rather than waiting for the gate to fail and reading `BEADS.md` cold.
