# Phase 15 — Open bd Issue Recall

Scanned all open bd issues (`bd list --status open`, `bd list --status in_progress`) for scope overlap with Phase 15 (extract `markdown-linting` and `pr-workflow` to public repos).

## Scope-matched

None. All 5 open issues belong to `gsd-beads-bu0` (Phase 14: pr-workflow capability dogfood), not to the extraction/publishing work this phase covers.

## Unscoped (not dropped — flagged for awareness)

- `gsd-beads-bu0.3` .. `gsd-beads-bu0.6` — Phase 14 tasks (PRW-04, PRW-03, re-consent evidence, advisory-gate evidence). ROADMAP.md Phase 14 checklist marks the corresponding plans (`14-02-PLAN.md`, `14-03-PLAN.md`) `[x]` complete, and recent commits (`8880aca`, `92d1320`, `f93622f`) record phase-14 completion — so this looks like a stale bd-sync gap (`execute:wave:post` batch-close didn't fire), not unfinished work. Does not block Phase 15 planning; the `pr-workflow/` subdirectory content these extract is the already-completed Phase 14 tree. Worth closing these tickets separately, but out of scope for this phase's plan.
