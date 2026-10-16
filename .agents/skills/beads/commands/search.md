---
description: Full-text search over issue titles and IDs
argument-hint: "[query]"
---

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

Searches issue titles and IDs across all statuses, closed included, so "was this already filed?" cannot silently answer no. Narrow with `--status open`; matches beyond `--limit` (default 50) are dropped without regard to status, so when hunting live work in a large database narrow first or raise `--limit`. An ID-like query (`bd-123`) gets fast exact/prefix matching instead of a text search.

## Common invocations

```bash
bd search "authentication bug"                       # title search, every status
bd search "login" --status open
bd search "database" --label backend --limit 10
bd search "bd-5q"                                      # partial-ID prefix match
bd search "api" --desc-contains "endpoint"             # search descriptions, not just titles
```

## When search beats `bd list`

- You don't know the issue's ID and need to find it by title fragment.
- You need a description-body match (`--desc-contains`), which `bd list`'s status/type filters don't offer.
