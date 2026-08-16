---
description: Import issues from a JSONL export (incremental upsert)
argument-hint: "[file|-]"
---

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

Imports issues from a `bd export`-shaped JSONL file. It's the incremental counterpart to `bd export`: new issues are created, existing ones are updated — upsert, not a full replace.

## Common invocations

```bash
bd import                    # from the configured import.path (default .beads/issues.jsonl)
bd import backup.jsonl       # from a specific file
cat issues.jsonl | bd import -   # from stdin
bd import --dry-run          # preview without writing
```

## ID-collision behaviour

A row only overwrites an existing local issue when its `updated_at` is strictly newer than the local copy's. Older rows are skipped (`stale_skipped_ids`); a same-second tie keeps the local row's columns, though labels/comments/dependencies still merge (`tie_kept_local_ids`). To deliberately restore an older snapshot over newer local state, pass `--allow-stale` — otherwise the import can never silently regress an issue that changed locally since the export was taken.

## Inspect before trusting the result

`bd import --json` reports `created`, `updated_issues` (with a field-level diff), `stale_skipped_ids`, and `tie_kept_local_ids` — read that output rather than assuming a clean run touched everything you expected.
