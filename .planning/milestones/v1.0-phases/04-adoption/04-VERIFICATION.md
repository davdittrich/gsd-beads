---
phase: 04-adoption
verified: 2026-08-15T22:48:32Z
status: passed
score: 9/9 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 4: Adoption Verification Report

**Phase Goal:** Existing hand-tracked todos move into beads, and the plan-task ↔ issue mapping is
inspectable on demand — at whichever epic granularity the user prefers.
**Verified:** 2026-08-15T22:48:32Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Roadmap Success Criteria (contract) plus PLAN frontmatter must-haves, merged and deduplicated.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running the one-shot migration moves `.planning/todos/pending/` entries into beads and reports what moved versus what could not be interpreted (SC1/B12) | VERIFIED | `migrate_todos()` (sync.py:288-366) parses, maps severity->priority, creates one `bd create` argv per well-formed todo, deletes the file only after a confirmed-zero return code, and prints a 3-count summary (moved / could not be interpreted / bd create failed). `TestMigrateTodos`+`TestMigrateTodosReport` (11 tests) pass, including the file-not-deleted-on-bd-create-failure invariant (D-05 causal ordering) |
| 2 | A well-formed todo maps to priority/label/description and the malformed todo is left untouched, reported separately from a bd-create failure (D-01/D-03/D-04/D-05, B12 must-have) | VERIFIED | `SEVERITY_TO_PRIORITY` mapping, `_todo_description()` folding, `parse_todo()` raising `ValueError` per-file (never touching the file) — confirmed by reading sync.py:46-366 and passing tests |
| 3 | With `bd` unavailable, `migrate-todos` fails open (NOTICE, STATE.md blocker, zero `bd create` calls) (B6 continuity, B12 must-have) | VERIFIED | `migrate_todos()`'s `bd_available()` gate runs before any per-file loop (sync.py:296-307); `TestMigrateTodosReport`'s bd-unavailable case asserts zero `subprocess.run` calls via an `AssertionError`-raising side effect — passes |
| 4 | Running `beads-status` on demand prints the plan-task ↔ issue mapping, including orphans on both sides (SC2/B13) | VERIFIED | `render_status_mapping()` (sync.py:1288-1359) reuses `_beads_md_argv`/`_render_beads_md_table` verbatim, then prints "## Issues with no matching plan task" and "## Plan tasks with no bd issue" unconditionally. `TestOnDemandStatus` (7 tests, including `test_task_side_orphan`) pass |
| 5 | A bare `/gsd-beads-status [phase]` invocation resolves phase_dir from the argument or STATE.md's `current_phase` (D-08, B13 must-have) | VERIFIED | `_resolve_default_phase_dir()` (sync.py:1260-1285) + `status` argparse subcommand (sync.py:1647-1652, 1672-1680); `beads-status/SKILL.md` Step 1.5's fifth branch ("Bare invocation") + Step 2e (lines 69-137) dispatch `sync.py status [phase]`; test `test_status_command_with_no_argument_resolves_default_phase_dir` passes |
| 6 | The on-demand status/mapping read path never calls a bd mutation command (close/update/comment) (B13 prohibition, verification: test) | VERIFIED | `render_status_mapping()` only calls `run_bd` for `bd show`/`bd list --json`; `TestOnDemandStatus::test_read_only_guarantee_no_bd_close_update_comment_calls` inspects every captured argv and asserts none has close/update/comment as its second element — passes. SKILL.md Anti-Pattern #10 documents the same constraint |
| 7 | Setting `beads.epic_per=milestone` creates one epic per release instead of one per phase (SC3/B14) | VERIFIED | `resolve_milestone_epic()` (sync.py:506-561) computes `"Milestone {milestone}: {milestone_name}"` from STATE.md, scans every phase's plan frontmatter as candidates, confirms via live `bd show --json` title match, creates only on no match; `resolve_epic()` (sync.py:564-612) branches on `read_epic_per(project_root) == "milestone"`. `capability.json` declares `"beads.epic_per"` (enum, `["phase","milestone"]`, default `"phase"`). `TestMilestoneEpic` (9 tests) pass, including the two-phase shared-epic case and the zero-second-create case |
| 8 | `beads.epic_per` absent or `"phase"` leaves sync behavior byte-for-byte unchanged from Phase 1-3 (B14 must-have, regression) | VERIFIED | `TestMilestoneEpic::test_default_unchanged` passes, asserting the identical outcome `TestPhaseScopedEpic`'s pre-existing regression test already asserts |
| 9 | An already-existing per-phase epic is never adopted as the milestone epic — forward-only (D-10, B14 must-have) | VERIFIED | `resolve_milestone_epic()`'s title-match check (sync.py:540-549) structurally excludes a per-phase epic (its title is always a ROADMAP phase header, never the computed milestone title); `TestMilestoneEpic::test_existing_phase_epic_not_reused_as_milestone_epic` passes |

**Score:** 9/9 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gsd/capabilities/beads/scripts/sync.py` | `migrate_todos`, `render_status_mapping`, `resolve_milestone_epic` + helpers | VERIFIED | All functions present, substantive (not stubs), read in full |
| `.gsd/capabilities/beads/skills/beads-migrate-todos/SKILL.md` | New skill, `name: gsd-migrate-todos` | VERIFIED | Exists (79 lines), dispatches `sync.py migrate-todos`, prints stdout verbatim, 5 anti-patterns documented |
| `.gsd/capabilities/beads/skills/beads-status/SKILL.md` | Fifth Step 1.5 branch + Step 2e | VERIFIED | "Bare invocation" branch at line 69, "Step 2e" heading at line 137, Anti-Pattern #10 at line 230 |
| `.gsd/capabilities/beads/capability.json` | `"beads-migrate-todos"` in `skills[]`; `"beads.epic_per"` enum config key | VERIFIED | Both entries confirmed present |
| `.gsd/capabilities/beads/tests/fixtures/todo-wellformed.md`, `todo-malformed.md` | Match `add-todo.md`'s schema | VERIFIED | Both fixtures present, wellformed carries full frontmatter+body, malformed omits `severity:` |
| `.gsd/capabilities/beads/tests/test_sync.py` | `TestMigrateTodos`, `TestMigrateTodosReport`, `TestOnDemandStatus`, `TestMilestoneEpic` | VERIFIED | All 4 classes present; 22 phase-4-specific tests, all passing |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `migrate_todos()` | `run_bd(["bd","create",...])` | typed argv list | WIRED | sync.py:328-343 — one Python list, never a shell string |
| `parse_todo()` parse failure | "could not be interpreted" list | `ValueError` caught per-file | WIRED | sync.py:321-326 — never reaches `bd create` |
| `render_status_mapping()` | `_beads_md_argv()`/`_render_beads_md_table()` | reused verbatim | WIRED | sync.py:1320,1332 |
| `render_status_mapping()` bd-side orphan | `collect_epic_task_ids()` | read-only, never `find_orphans` | WIRED | sync.py:1334-1335 |
| `resolve_epic()` | `read_epic_per(project_root)` -> `.planning/config.json` | first-ever direct config.json read | WIRED | sync.py:481-489, 598 |
| `resolve_milestone_epic()` | `bd show --json` title match | D-10 forward-only guard | WIRED | sync.py:540-549 |
| argparse `migrate-todos`/`status` subcommands | `main()` dispatch | direct call | WIRED | sync.py:1643-1652, 1668-1680 |
| `create_issues()` | `resolve_epic(..., project_root)` | call-site edit | WIRED | sync.py:858-860 |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite green | `python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q` | 88 passed in 3.34s | PASS |
| Phase-4-specific classes | `pytest -k "TestMigrateTodos or TestOnDemandStatus or TestMilestoneEpic"` | 22 passed | PASS |
| D-05 delete-after-confirm invariant (state transition) | `TestMigrateTodosReport` bd-create-failure case | file remains on disk, reported under distinct bucket | PASS |
| B13 read-only invariant (never mutates) | `TestOnDemandStatus::test_read_only_guarantee_no_bd_close_update_comment_calls` | no close/update/comment argv found | PASS |
| D-10 forward-only invariant (never adopts existing epic) | `TestMilestoneEpic::test_existing_phase_epic_not_reused_as_milestone_epic` | fresh epic created, seeded epic id never returned | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| B12 | 04-01-PLAN.md | One-shot migration of `.planning/todos/pending/` into bd, reporting moved vs. could-not-interpret | SATISFIED | `migrate_todos()`, `beads-migrate-todos` skill, 11 passing tests |
| B13 | 04-02-PLAN.md | `beads-status` runnable on demand, plan-task ↔ issue mapping with orphans on both sides | SATISFIED | `render_status_mapping()`, `status` subcommand, Step 2e, 7 passing tests |
| B14 | 04-03-PLAN.md | Milestone-level epic option (`beads.epic_per=milestone`) | SATISFIED | `resolve_milestone_epic()`, `beads.epic_per` config key, 9 passing tests |

No orphaned requirements: REQUIREMENTS.md's Phase 4 traceability table lists exactly B12/B13/B14, and all three appear in a plan's `requirements:` frontmatter.

### Anti-Patterns Found

None blocking. One `TBD` string found in `.gsd/capabilities/beads/tests/fixtures/todo-malformed.md:15` — this is deliberate test-fixture body content (the fixture's `## Solution` section), not a debt marker in shipped code; excluded from the debt-marker gate.

### Human Verification Required

None. All must-haves — including the three state-transition/invariant truths (D-05 delete-after-confirm, B13 read-only guarantee, D-10 forward-only) — have direct passing behavioral test coverage, not just presence/wiring.

### Gaps Summary

None. All 3 roadmap Success Criteria, all 9 merged must-have truths (roadmap + PLAN frontmatter,
deduplicated), all declared key links, and both `must_haves.prohibitions` entries (B13's read-only
constraint, B14's D-10 non-destructive constraint) are verified against the actual codebase, not
just SUMMARY.md claims. Full test suite is green (88/88). Five post-summary review-fix commits
(CR-01/02/03, WR-01/02, per `04-REVIEW-FIX.md`) are already applied and reflected in the code read
above. One deferred item (IN-01, `run_bd`'s missing `TimeoutExpired` catch) was explicitly scoped
out as a pre-existing file-wide pattern, not a Phase 4 regression — informational only, not a gap
against this phase's goal.

---

_Verified: 2026-08-15T22:48:32Z_
_Verifier: Claude (gsd-verifier)_
