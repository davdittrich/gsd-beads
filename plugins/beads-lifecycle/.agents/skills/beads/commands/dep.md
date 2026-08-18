---
description: Manage dependencies between issues
argument-hint: "[command] [from-id] [to-id]"
---

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

Manages dependency edges between issues. See [../resources/DEPENDENCIES.md](../resources/DEPENDENCIES.md) for the four dependency types and how `blocks` affects `bd ready`.

## Common invocations

```bash
bd dep add <dependent-id> <prerequisite-id> --type blocks   # dependent needs prerequisite closed first
bd dep <blocker-id> --blocks <blocked-id>                    # shorthand for the same, in blocker-first order
bd dep tree <id>                                              # what blocks this issue
bd dep list <id>                                              # dependencies/dependents of one or more issues
bd dep cycles                                                  # detect circular dependencies
```

`bd dep [command] --help` documents the full option surface, including `tree`'s `--reverse`/`--format mermaid`/`--max-depth` flags — don't rely on this document for those; they drift across releases.

## Cycle detection

`bd dep add` rejects an edge that would create a cycle at creation time. `bd dep cycles` runs a standalone check across the whole graph, useful after a bulk `--file` import.

Use `--no-cycle-check` to skip the per-edge check for speed during bulk wiring — a final whole-graph check still runs before commit on a bulk `--file` add.

