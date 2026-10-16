# Dependencies

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

`bd dep` links two issues with a typed edge. This skill uses four of the ten types `bd dep add --help` lists; of those, only `blocks` changes what shows up in `bd ready` — the other three are structure and context.

## The types this skill uses

| Type | Effect on `bd ready` | Use for |
|---|---|---|
| `blocks` | Yes — blocked issue disappears until the blocker closes | Hard prerequisites: schema before endpoint, step 1 before step 2 |
| `related` | No | Soft connections: similar work, alternative approaches, shared context |
| `parent-child` | No | Hierarchy: an epic and its subtasks |
| `discovered-from` | No | Provenance: work found while doing other work |

Only `blocks` gates readiness; use `related` for a preference, since a needless `blocks` silently serializes parallel work.

## Creating dependencies

```bash
bd dep add <dependent-id> <prerequisite-id>              # blocks (default)
bd dep add <dependent-id> <prerequisite-id> --type related
bd dep add <child-id> <parent-id> --type parent-child
bd dep add <discovered-id> <original-id> --type discovered-from
```

Add `--no-cycle-check` only for bulk wiring; the default rejects an edge that would close a cycle.

Direction matters for `blocks`, `parent-child`, and `discovered-from`: `from_id` depends on `to_id`. Think "dependent depends on prerequisite." `related` is symmetric.

## Automatic unblocking

Closing a blocking issue automatically surfaces what it blocked in `bd ready` — no manual unblock step. This is why `blocks` is the type worth using deliberately: a chain of `blocks` edges gives you a self-maintaining queue.

## Inspecting the graph

```bash
bd dep tree <id>       # dependency tree rooted at an issue
bd show <id>           # dependencies, dependents, related, discovered-from — all in one view
```

## gsd-core framing

- A phase's epic is the `parent-child` parent of every task issue synced from that phase's plans (see `.beads/PRIME.md` — "Phase epics").
- `BEADS.md`'s `blocking_open` counts epic children, not `blocks` edges: `PRIME.md`, "Ship gate".

## Decision guide

Ask in order:
1. Does A prevent B from starting? → `blocks`
2. Is B a subtask of A? → `parent-child` (A parent, B child)
3. Was B found while working on A? → `discovered-from`
4. Otherwise, are A and B just connected? → `related`

## Common mistakes

- **Using `discovered-from` for planned decomposition.** If you're breaking an epic into tasks you already knew you'd need, that's `parent-child`, not `discovered-from` — the latter is for genuinely emergent findings.
- **Wrong direction.** `bd dep add database-schema api-endpoint` reads as "the schema depends on the endpoint," which is backwards. `bd dep add api-endpoint database-schema` is correct: the endpoint needs the schema, not the reverse.
