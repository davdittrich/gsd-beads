# Async Gates

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

`bd gate` models an external wait — a human approval, a CI run, a PR merge, a deploy-propagation delay — as a **wisp**: an ephemeral, unsynced blocker distinct from a regular issue.

## Why a gate beats blocking an agent turn

Waiting on a review, a deploy, or a third-party turnaround inside a single agent turn burns the turn on nothing. A gate lets the agent create the wait as a typed condition, move on to other ready work, and check the gate later (or let it auto-resolve) instead of polling inline.

## Gate types

| Type | `--type` | Resolves when |
|---|---|---|
| Human | `human` (default) | Never automatically — `bd gate resolve` only |
| CI | `gh:run` | GitHub Actions run completes with success |
| PR | `gh:pr` | PR state becomes `MERGED` |
| Timer | `timer` | `now > created_at + --timeout` |
| Bead | `bead` | The named local bead closes |

## Creating and resolving

```bash
bd gate create --type human --blocks <issue-id> --reason "Approve production deploy"
bd gate create --type gh:run --blocks <issue-id> --await-id <run-id>
bd gate create --type timer --blocks <issue-id> --timeout 15m

bd gate check              # evaluate all open gates; resolves what it can
bd gate check --dry-run    # preview without closing anything
bd gate resolve <gate-id> --reason "Reviewed and approved"   # human gates need this
```

Only `timer`, `gh:run`, `gh:pr`, and `bead` gates auto-resolve via `bd gate check`. A `human` gate always needs an explicit `bd gate resolve`.

## Inspecting what a gate holds up

```bash
bd gate list               # open gates
bd gate list --all         # include closed
bd gate show <gate-id>     # detail for one gate
```

## Gates vs. issues

| Aspect | Gate (wisp) | Issue |
|---|---|---|
| Persistence | Ephemeral, not synced to git | Permanent, synced |
| Purpose | Block on an external condition | Track work |
| Closes via | Auto-resolve or `bd gate resolve` | `bd close` |

## gsd-core framing

A still-open gate blocks its `--blocks` issue the same way a `blocks` dependency does — the blocked issue stays out of `bd ready`, and if that issue belongs to the current phase, it also counts toward `BEADS.md`'s `blocking_open`, the field `ship:pre`'s gate checks. Run `bd gate check` at session start to clear elapsed timers, merged PRs, and completed CI runs before assuming a phase is stuck.
