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

## Pruned 2026-08-16 (phases 1-3, kept recent 3)

### Performance Metrics

| 03 | 3 | - | - |
| 02 | 2 | - | - |

## Pruned 2026-08-16 (phases 1-4, kept recent 3)

### Performance Metrics

| 4 | 3 | - | - |

## Pruned 2026-08-16 (phases 1-5, kept recent 3)

### Decisions

- [Phase 05]: D-02 amended: plugin.json author is {name, email} — claude plugin validate --strict hard-requires author.name; user chose to amend the locked email-only decision
- [Phase 05]: D-10 (new): root CLAUDE.md's --strict warning has no suppression mechanism; user accepted it as a permanent, scoped exception rather than restructure the plugin root
- [Phase 05]: marketplace.json given a top-level description (RESEARCH.md's example omitted it) — --strict requires it, reused the existing D-06 blurb

### Performance Metrics

| 05 | 1 | - | - |

## Pruned 2026-08-16 (phases 1-6, kept recent 3)

### Decisions

- [Phase 06]: PUB-03 satisfied by documented manual capability install --scope project --yes bridge, not automation (defeats CB-3 consent gate, targets a path absent from PUB-04 ship allowlist)
- [Phase 06]: hooks/hooks.json ships bare bd prime --hook-json with no PATH guard; Claude Code's own SessionStart fail-open contract already satisfies criterion 4
- [Phase 06]: A merely checked-out repo does not auto-load plugin hooks.json (Assumption A1 resolved); beads@gsd-beads plugin kept installed at local scope as this repo's disclosed dogfooding dependency

### Performance Metrics

| 6 | 1 | - | - |

## Pruned 2026-08-17 (phases 1-8, kept recent 3)

### Performance Metrics

| 07 | 2 | - | - |
| 08 | 3 | - | - |
