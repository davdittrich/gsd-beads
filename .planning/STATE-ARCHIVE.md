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

## Pruned 2026-08-18 (phases 1-11, kept recent 3)

### Decisions

- [Phase 3]: `ship:pre` gate dispatch in the installed `ship.md` is a **machine-local patch**
- [Phase 6/10]: gsd-core capability consent is a content hash over the whole bundle — any
- [Phase 10.1]: `hooks/capability-auto-install.sh` hashes the bundle against a per-id sidecar and
- [Phase 11]: `sota-numerics`' `plan:post` gate uses `onError: halt` (deliberate divergence) and

## Pruned 2026-08-18 (phases 1-12, kept recent 3)

### Decisions

- [Phase 12]: `davdittrich/ponytail-everywhere` and `davdittrich/sota-numerics` shipped via the
- [Phase 12]: `marketplace.json` entries must use `url`-type sources with explicit `https://` git
- [Phase 12]: The claim previously recorded here — that dogfood subdirectories were removed from

## Pruned 2026-08-19 (phases 1-13, kept recent 3)

### Decisions

- [Phase 13]: Narrowed .gitignore's blanket .gsd/ ignore (from quick-task 260818-h2h) to un-ignore .gsd/capabilities/markdown-linting/ specifically -- the bare pattern silently blocked this milestone's documented in-repo dogfood pattern for brand-new capabilities with no extracted plugin source yet
- [Phase 13]: markdown-linting's verify_post fail-open path deliberately diverges from sync.py's regenerate_beads_md -- always overwrites LINT-REPORT.md with a non-numeric violation_count: unavailable sentinel instead of leaving a stale artifact untouched
- [Phase 13]: dirty.md/clean.md fixtures pin MDL-01/02/04 test coverage against real rumdl subprocess calls, never the live .planning/ tree; real-subprocess tests skip cleanly (unittest.skipUnless) on a machine with no rumdl/uvx
- [Phase 13]: isolated pre-existing unrelated dirty working-tree state (CLAUDE.md beads-block strip, state pruning, API-SURFACE staleness note, 13-PATTERNS.md) into its own prep commit before the wide auto-fix pass, so Task 1's mechanical-fix diff stayed spot-checkable
- [Phase 13]: markdown-linting README's rumdl-vs-markdownlint-cli2 divergence table is measured post-fix (rumdl 0 vs cli2 309, all MD022/MD024) -- a materially different, non-comparable shape from the pre-fix 471-vs-708 figure in RESEARCH.md/REQUIREMENTS.md
- [Phase 13]: closed CR-01/CR-02 lint.py gaps (rumdl_argv-None guard on count, CalledProcessError fail-open widening) verbatim per 13-REVIEW.md; two plan acceptance-criteria grep counts were miscounted by the plan author (pre-existing occurrences not accounted for) -- documented in 13-04-SUMMARY.md rather than silently 'corrected'
