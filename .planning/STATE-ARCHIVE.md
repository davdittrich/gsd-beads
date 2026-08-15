# STATE Archive

Pruned entries from STATE.md. Recoverable but no longer loaded into agent context.

## Pruned 2026-08-16 (phases 1-1, kept recent 3)

### Decisions

- [Phase 1]: real `bd` v1.2.1 CLI diverges from initial research in three ways (no `--id`, hierarchical child ids, `bd list --parent` hides closed by default) — full detail in PROJECT.md Key Decisions
- [Phase 1]: gsd-core project-scope capability consent is a whole-bundle content hash — any post-consent file edit silently deactivates it; re-run `capability install --scope project` after any such edit, every phase
- [Phase 1]: PLAN.md task schema is XML `<task type="...">` elements, never markdown `### Task N:` headings (corrected from an earlier wrong assumption)

### Blockers (resolved)

- ~~[Backlog] Phase 1 sync.py: create_issues resolves each plan's epic independently...~~ FIXED

### Performance Metrics

| 01 | 3 | - | - |
