---
description: Squash old Dolt commit history to reclaim storage
argument-hint: "[--days N] [--dry-run|--force]"
---

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

Squashes Dolt commits older than a retention window into a single commit, prunes remote-tracking refs (the next push or fetch recreates them at the new tip), then runs a full Dolt GC to reclaim storage; the GC can take minutes on a multi-gigabyte store. Recent commits inside the window are preserved via cherry-pick. This rewrites local history: confirm with `--dry-run` first. For a full-history squash use `bd flatten`.

## Common invocations

```bash
bd compact --dry-run              # preview the commit breakdown, no changes
bd compact --days 7 --force       # squash everything older than 7 days
bd compact --force                # default 30-day retention window
```

## What it does NOT remove

`bd compact` squashes **git commit history** for the Dolt data store, not issue content. No issue, comment, or dependency is deleted by it — closed issues stay closed and readable, `bd show` still returns everything. For actual semantic summarization of closed issues, that's a different command: `bd admin compact`. Confirm with `--dry-run` before running `--force` if you're unsure which one you meant.

## When it's worthwhile

Storage overhead from Dolt's per-write auto-commit history accumulates fastest on a project with frequent small updates (status changes, comment adds). Run `bd compact` when `bd doctor` or a growing `.beads/` size flags it, not on a fixed schedule — a fresh project has nothing worth squashing yet.
