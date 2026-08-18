---
description: Quick snapshot of the issue database — counts, ready work, recent activity
argument-hint: ""
---

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

`bd stats` is an alias for `bd status` — both names run the same command. It's the `bd` analogue of `git status`: a project health snapshot without running multiple separate queries.

## Common invocations

```bash
bd stats                    # counts by state, ready work, 24h activity
bd stats --no-activity      # skip git-history activity lookup (faster)
bd stats --assigned         # only issues assigned to the current actor
bd stats --json             # structured output
```

## Acting on the numbers

- A high blocked count → `bd blocked` to see which issues, then trace the chain to the blocker that actually needs resolving.
- An empty or near-empty ready count with plenty of open issues → most open work is blocked or claimed; check `bd blocked` and stale claims (see `resources/TROUBLESHOOTING.md`).
- A large gap between open and in-progress → work may be sitting unclaimed rather than genuinely blocked; run `bd ready` to confirm what's actually available.
