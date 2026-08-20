---
phase: quick-260820-j6g
plan: 01
subsystem: beads-lifecycle
tags: [beads, reconcile-stale-closed, sync.py, tdd]
status: complete
dependency-graph:
  requires: [gsd-beads-72u]
  provides: [resolves_issues-frontmatter-marker]
  affects:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md
    - CHANGELOG.md
tech-stack:
  added: []
  patterns:
    - "Third clone of the inline-flow/block-list YAML parse idiom (DEPENDS_ON_RE/DEPENDS_ON_BLOCK_RE -> FILES_BLOCK_RE -> RESOLVES_ISSUES_RE/RESOLVES_ISSUES_BLOCK_RE)"
    - "Frontmatter-only search boundary as the structural mechanism for prose-immunity (never scan artifact body text for a closure signal)"
    - "SAFE_BD_ID_RE fullmatch as the argv trust boundary before any artifact-derived string reaches a destructive subprocess argv"
key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md
    - CHANGELOG.md
decisions:
  - "resolves_issues: frontmatter key (not body-prose marker, not fuzzy title matching) -- the only option structurally immune to the 18-02-SUMMARY.md false-positive class, per the plan's Alternatives Considered table"
  - "Two separate bd close calls (existing <beads-id> path + new marker path), never merged into one union, so --reason keeps the two closure histories distinguishable in bd's audit trail"
  - "Third clone of the parse_depends_on idiom rather than a shared extraction -- parse_depends_on and parse_todo_files_block are both under test and out of this ticket's blast radius"
metrics:
  duration: "~35 min"
  completed: 2026-08-20
actuals:
  tokens: 5930
  tasks: 2
  commits: 3
---

# Quick Task 260820-j6g: extend reconcile_stale_closed to reach standalone bd issues Summary

`reconcile_stale_closed` now closes a standalone bd problem-report issue (one with no `<beads-id>`
in any PLAN.md) when a completed plan's `SUMMARY.md` frontmatter names it via an opt-in
`resolves_issues:` key, gated so a bd id mentioned only in SUMMARY body prose is provably never
closed.

## What Was Built

- **`RESOLVES_ISSUES_RE`, `RESOLVES_ISSUES_BLOCK_RE`, `SAFE_BD_ID_RE`** — three new module
  constants in `sync.py`, cloning the `DEPENDS_ON_RE`/`DEPENDS_ON_BLOCK_RE` inline-flow/block-list
  idiom for the new `resolves_issues:` frontmatter key, plus a fullmatch argv-trust-boundary
  pattern (leading alphanumeric, then `[A-Za-z0-9._-]*`).
- **`parse_resolves_issues(frontmatter)`** — structurally identical to `parse_depends_on`, returns
  raw unvalidated strings; validation happens only at the one place ids cross into an argv.
- **`_resolve_marked_issue_ids(phase_dir)`** — returns `(set_of_ids, rejected_count)`. Iterates
  `discover_plan_files`, derives each sibling `SUMMARY.md` path via `Path.with_name` (never joins
  from artifact text), skips missing/unreadable/undecodable files, matches `FRONTMATTER_RE`
  (skipping SUMMARY.md with no fence), and admits only ids that fullmatch `SAFE_BD_ID_RE`.
- **`reconcile_stale_closed` extended**: after the existing `bd close` call, resolves the marker
  set, subtracts already-handled `completed_ids`, and — when non-empty — issues a second `bd close`
  with reason `resolves_issues marker: <phase dir name>`, distinct from the first call's
  `phase-wide reconciliation: <phase dir name>`. Stdout line extended (byte-identical up to the
  existing wording) with the marker-closed count and rejected-entry count.
- **`TestResolvesIssuesMarker`** — 9 new tests in `test_sync.py`, one per `<behavior>` bullet:
  inline marker form, block-list form, identity-safety regression (body-mentioned id never
  closed), no-frontmatter SUMMARY contributes nothing, argv trust boundary on 5 unsafe entries,
  an id present both as a task `<beads-id>` and a marker appears exactly once, distinct
  `--reason` per call, idempotent repeat run, unreadable/undecodable SUMMARY skipped not raised.
- **`SKILL.md` Step 2b** — new subsection documenting the marker (what it's for, both YAML forms,
  the two properties an author depends on) plus DO-NOT entry 11 forbidding a future widening of
  the search into SUMMARY body text.
- **`CHANGELOG.md` `## 0.4.0` / `### Added`** — new bullet covering the key, both YAML forms, the
  separate `bd close` call and reason, the argv-boundary validation, and the frontmatter-only
  restriction with its motivating reason.
- Installed `.gsd/capabilities/beads` copy refreshed via `gsd-tools capability install` so the
  live lifecycle path runs the new code.

## Verification

- `python3 -m unittest discover -s tests -t tests` inside
  `plugins/beads-lifecycle/.gsd/capabilities/beads`: **261 tests, OK** (baseline 252 + 9 new).
  Every existing `TestCloseWave` and `TestReconcileStaleClosed` test passes unmodified.
- `diff -r -q .gsd/capabilities/beads/scripts plugins/beads-lifecycle/.gsd/capabilities/beads/scripts`:
  no differences (installed copy matches source).
- `grep -c resolves_issues CHANGELOG.md skills/beads-status/SKILL.md`: 4 and 5 occurrences
  respectively (>=1 and >=2 required).
- TDD gate sequence confirmed in git log: `test(260820-j6g)` (RED, 26541f5) ->
  `feat(260820-j6g)` (GREEN, 964a870) -> `docs(260820-j6g)` (9d16c33).
- Tracer feedback gate: re-ran the full suite after the GREEN commit before starting Task 2 —
  still 261/261 OK.
- Live smoke check (per plan's own caveat): confirmed `gsd-beads-he1` is already closed (from
  Phase 17), so a live end-to-end marker-close against it would report zero — as the plan
  anticipated. Did not force a close against a currently-open real bd issue purely to demonstrate
  the path, since that mutation is unrecoverable from git (`.beads/` untracked) and the mocked
  unit suite already pins the exact same property (`test_inline_marker_closes_standalone_issue_with_no_beads_id_anywhere`,
  `test_identity_safety_body_mentioned_id_is_never_closed`).

## Deviations from Plan

None — plan executed exactly as written. `close_wave`, `_resolve_completed_task_ids`,
`parse_depends_on`, and `parse_todo_files_block` were not touched, matching the plan's scope
boundaries.

## Known Stubs

None.

## Self-Check: PASSED

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` — FOUND, contains
  `RESOLVES_ISSUES_RE`, `RESOLVES_ISSUES_BLOCK_RE`, `SAFE_BD_ID_RE`,
  `parse_resolves_issues`, `_resolve_marked_issue_ids`.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` — FOUND, contains
  `class TestResolvesIssuesMarker` with 9 tests.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md` — FOUND,
  contains the marker subsection and DO-NOT entry 11.
- `CHANGELOG.md` — FOUND, contains the `## 0.4.0` bullet citing bd `gsd-beads-72u`.
- Commit `26541f5` — FOUND in `git log`.
- Commit `964a870` — FOUND in `git log`.
- Commit `9d16c33` — FOUND in `git log`.
- bd `gsd-beads-72u`, `gsd-beads-o7y`, `gsd-beads-xbc` — CLOSED.
