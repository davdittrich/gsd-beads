# Dependencies

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

`bd dep` links two issues with one of four typed relationships. Only one of the four changes what shows up in `bd ready` — the other three are structure and context.

## The four types

| Type | Effect on `bd ready` | Use for |
|---|---|---|
| `blocks` | Yes — blocked issue disappears until the blocker closes | Hard prerequisites: schema before endpoint, step 1 before step 2 |
| `related` | No | Soft connections: similar work, alternative approaches, shared context |
| `parent-child` | No | Hierarchy: an epic and its subtasks |
| `discovered-from` | No | Provenance: work found while doing other work |

**Key insight:** only `blocks` gates readiness. Reach for `related` when you're tempted to use `blocks` for a preference rather than a real prerequisite — a common mistake that silently serializes work that could run in parallel.

## Creating dependencies

```bash
bd dep add <dependent-id> <prerequisite-id>              # blocks (default)
bd dep add <dependent-id> <prerequisite-id> --type related
bd dep add <child-id> <parent-id> --type parent-child
bd dep add <discovered-id> <original-id> --type discovered-from
```

Direction matters for `blocks`, `parent-child`, and `discovered-from`: `from_id` depends on `to_id`. Think "dependent depends on prerequisite." `related` is symmetric.

## Automatic unblocking

Closing a blocking issue automatically surfaces what it blocked in `bd ready` — no manual unblock step. This is why `blocks` is the type worth using deliberately: a chain of `blocks` edges gives you a self-maintaining queue.

## Inspecting the graph

```bash
bd dep tree <id>       # dependency tree rooted at an issue
bd show <id>           # dependencies, dependents, related, discovered-from — all in one view
```

`bd show` prints four sections for an issue: what blocks it, what it blocks, what it's related to, and what it was discovered from.

## gsd-core framing

- A phase's epic is the `parent-child` parent of every task issue synced from that phase's plans (see `.beads/PRIME.md` — "Phase epics").
- `BEADS.md`'s `blocking_open` count — the number that gates `ship:pre` — is exactly the count of open issues still holding a `blocks` edge over something in the current phase. `related`, `parent-child`, and `discovered-from` edges never contribute to that count.
- Cycles are rejected at creation time; `bd dep add` refuses an edge that would make the graph unsatisfiable.

## Decision guide

Ask in order:
1. Does A prevent B from starting? → `blocks`
2. Is B a subtask of A? → `parent-child` (A parent, B child)
3. Was B found while working on A? → `discovered-from`
4. Otherwise, are A and B just connected? → `related`

## Common mistakes

- **Using `blocks` for preferences.** "We'd rather do docs first" is not a `blocks` relationship — nothing technically prevents the feature from shipping without docs. Use `related`, or say it in the description.
- **Using `discovered-from` for planned decomposition.** If you're breaking an epic into tasks you already knew you'd need, that's `parent-child`, not `discovered-from` — the latter is for genuinely emergent findings.
- **Wrong direction.** `bd dep add database-schema api-endpoint` reads as "the schema depends on the endpoint," which is backwards. `bd dep add api-endpoint database-schema` is correct: the endpoint needs the schema, not the reverse.
