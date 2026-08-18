---
description: Add or read comments on an issue
argument-hint: "[issue-id] [text...]"
---

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

Comments are where task findings and handoff notes belong — they travel with the issue across sessions and agents, unlike a chat transcript.

## Common invocations

```bash
bd comment <issue-id> "Working on this now"     # shorthand: adds a comment
bd comments add <issue-id> "Full note text"      # equivalent, explicit form
bd comments add <issue-id> -f notes.txt          # comment body from a file
bd comments <issue-id>                            # list all comments on an issue
```

There is no `bd comments list` — listing is the bare `bd comments <issue-id>` form; `bd comments <issue-id> --json` gets the same output as JSON.

## When to write one

Before releasing a stale claim, before ending a session mid-task, or the moment you discover something a future session would otherwise have to rediscover — see [../resources/RESUMABILITY.md](../resources/RESUMABILITY.md).
