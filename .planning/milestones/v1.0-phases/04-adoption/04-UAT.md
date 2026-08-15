---
status: complete
phase: 04-adoption
source: [04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md]
started: 2026-08-16T01:00:00Z
updated: 2026-08-16T01:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Well-formed todo migrates to bd (B12)
expected: Live-traced — bd create argv correctly mapped (priority=2 for minor, area-uat label, folded description), file deleted only after confirmed success.
result: pass

### 2. Malformed todo left untouched and reported separately (B12)
expected: |
  Same live-trace run: a second synthetic todo missing the `severity` frontmatter key was placed
  alongside the well-formed one. Migration output: `could not be interpreted: uat-test-malformed.md:
  missing or unrecognized 'severity' frontmatter key`. The file was NOT deleted (still present in
  pending/ after the run) and was NOT sent to `bd create` — reported under a distinct count from
  the "bd create failed" count.
result: pass

### 3. On-demand beads-status prints mapping + both orphan sections (B13)
expected: |
  Live-traced: `sync.py status .planning/phases/04-adoption` (no lifecycle-point marker, direct
  invocation) printed the full 6-column issue/task mapping table (6 rows, all Phase 4 tasks,
  correctly cross-referenced to plan/task names) followed by both orphan section headings —
  "## Issues with no matching plan task" and "## Plan tasks with no bd issue" — present
  unconditionally even though both were empty in this case (every Phase 4 task is synced and
  closed).
result: pass

### 4. epic_per=milestone shares one epic across phases (B14)
expected: |
  Not live-traced this session (would require creating a second real phase-scoped epic against
  live project data to test cross-phase sharing — deferred as unnecessarily invasive for a UAT
  pass). Test-verified per 04-03-SUMMARY.md: `TestMilestoneEpic::test_two_phases_share_one_
  milestone_epic_and_second_sync_creates_no_second_epic` confirms two plans under different phase
  directories, with `beads.epic_per: "milestone"` set, resolve to the identical epic id, and a
  second sync issues zero additional `bd create --type epic` calls. The forward-only guard
  (`test_existing_phase_epic_not_reused_as_milestone_epic`) confirms an existing per-phase epic
  (title = a ROADMAP phase header) is never mistaken for the milestone epic (title = "Milestone
  {version}: {name}") even though both are discoverable by the same cross-phase scan.
result: pass

### 5. Default epic_per (absent or "phase") behavior is unchanged (B14 regression)
expected: |
  `TestMilestoneEpic::test_default_unchanged` confirms the same outcome as the pre-existing
  `TestPhaseScopedEpic::test_second_plan_in_phase_reuses_first_plans_epic_when_neither_preset_one`
  test, exercised through the now-edited `resolve_epic` signature — byte-for-byte identical
  result. Full suite (88/88, including all pre-Phase-4 tests) stays green with this plan's changes
  applied.
result: pass

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
