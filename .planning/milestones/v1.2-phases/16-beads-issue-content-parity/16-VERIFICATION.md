---
phase: 16-beads-issue-content-parity
verified: 2026-08-19T02:00:00Z
status: passed
score: 18/21 must-haves verified
behavior_unverified: 3
overrides_applied: 0
behavior_unverified_items:

  - truth: "gsd-executor reads an auto/tracer task's instructions from `bd show <beads-id> --json`, not from the PLAN.md task block (D-01)"
    test: "Run an actual `execute-plan.md` execution (via gsd-executor / Claude Code) against a PLAN.md whose auto/tracer task was stripped by this phase's sync.py, and confirm the agent runs `bd show <beads-id> --json` and prints `beads: task content read from bd (<beads-id>)` before doing the task, using bd's `description`/`acceptance_criteria` fields as its instructions instead of the (now-absent) PLAN.md body."
    expected: "The executing agent's transcript shows the `bd show` call and the print line, and the task is carried out using the bd-sourced content — never falls back to re-deriving instructions from the stripped PLAN.md block."
    why_human: "The patch is markdown prose interpreted by an LLM agent at execution time, not code exercised by a unit test. sync.py's test suite (134 tests, all passing) proves the *writer* (strip_task_bodies, check_execute_plan_patch) is correct, and the patch's text was byte-verified as installed at the correct anchor — but no phase has yet run gsd-executor against a real stripped/inverted task, so the read-path's actual runtime effect on agent behavior is unexercised. 16-04-SUMMARY.md's own coverage table flags this identically (`human_judgment: true`, \"the first real inverted plan a future phase runs is the live exercise of this branch\")."

  - truth: "A failing `bd show` halts execution with an error naming the unreachable issue — never a silent fall-back to PLAN.md (D-04)"
    test: "During a live gsd-executor run, force a task's `<beads-id>` to reference a bd issue that has been deleted or is otherwise unreachable, and confirm the agent halts with the exact `FATAL: bd task content unreachable for <beads-id> ...` message rather than silently reconstructing the task from the stripped PLAN.md block."
    expected: "Execution stops; the agent reports the FATAL message naming the unreachable id; no task work is attempted."
    why_human: "The D-04 *signature* bd itself produces on a missing id was independently re-confirmed live this session (`bd show <bad-id> --json` → exit 1, `{\"error\": ...}`), and the patch's halt-branch text correctly names that exact shape. But whether an executing agent actually honors the halt instruction rather than working around it is agent behavior, not testable by sync.py's suite or by grep."

  - truth: "A bd issue with an empty description routes to the PLAN.md inline body with a printed notice — the pre-inversion boundary for Phases 1-15 (D-07)"
    test: "Run gsd-executor against a Phase 1-15 plan whose task carries a `<beads-id>` resolving to a bd issue with an empty `description` (the pre-inversion state), and confirm the agent falls back to the PLAN.md inline task body and prints `beads: <beads-id> carries no description -- using inline PLAN.md task body (pre-migration plan)`."
    expected: "Task instructions are read from PLAN.md's own task block, unchanged from pre-Phase-16 behavior, with the fallback notice printed."
    why_human: "Same class as the two items above — the branch text is installed and byte-identical to GSD-CORE-PATCH.md's record, but 16-04-SUMMARY.md explicitly notes no PLAN.md in this phase actually exercised this branch live; it is deferred to whichever future phase first re-runs sync against Phase 1-15-vintage issues."
human_verification:

  - test: "Run an actual `execute-plan.md` execution against a PLAN.md whose auto/tracer task was stripped by sync.py, and confirm the agent reads task content from `bd show <beads-id> --json` (prints the evidence line) rather than the absent PLAN.md body."
    expected: "Agent transcript shows the `bd show` call, the `beads: task content read from bd (<beads-id>)` line, and task execution driven by bd's description/acceptance_criteria."
    why_human: "LLM-interpreted markdown patch; behavior is agent-runtime, not unit-testable."

  - test: "Force a `<beads-id>` to an unreachable bd issue during a live execute-plan.md run and confirm the agent halts with the FATAL message rather than falling back to PLAN.md."
    expected: "Execution stops with the exact FATAL message naming the unreachable id; no silent PLAN.md reconstruction."
    why_human: "Agent halt-compliance is not testable by sync.py's suite; only the bd-side failure signature was live-confirmed."

  - test: "Run gsd-executor against a pre-inversion (Phase 1-15) task whose bd issue has an empty description and confirm it falls back to the inline PLAN.md body with the printed notice."
    expected: "Task instructions read from PLAN.md, `beads: <beads-id> carries no description -- using inline PLAN.md task body (pre-migration plan)` printed."
    why_human: "Same LLM-runtime-behavior class as the two items above; 16-04-SUMMARY.md's own coverage table marks this branch as un-exercised live."
---

# Phase 16: beads issue content parity Verification Report

**Phase Goal:** A `bd show <issue-id>` on any beads-synced task is self-sufficient — readable
without also having `PLAN.md` open.
**Verified:** 2026-08-19T02:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A task issue created by `sync.py create-issues` returns a non-empty `description` from `bd show <id> --json` (D-06) | ✓ VERIFIED | Live tracer test `TestEndToEndTracer.test_created_task_issue_round_trips_description_and_acceptance` ran (not skipped) and passed; 16-01-SUMMARY.md's own live round trip (`bd show livedemo-abt.1 --json`) shows non-empty `description` |
| 2 | Description carries read_first/precondition/behavior/action/verify/done content (D-02) | ✓ VERIFIED | `_task_description()` at sync.py:~ renders these sections; `TestTaskDescription` (3 tests) pass |
| 3 | `<acceptance_criteria>` returns a non-empty `acceptance_criteria` key from `bd show --json` distinct from `description` (D-06) | ✓ VERIFIED | Live tracer test confirms both `description` and `acceptance_criteria` non-empty and distinct; `resolve_issue` code read directly (sync.py:857-861) — `--acceptance` is a separate argv element, never folded into `-d` |
| 4 | A phase epic carries non-empty description sourced from plan's `<objective>` (D-06) | ✓ VERIFIED | `_epic_description()`/`OBJECTIVE_RE` present; `TestEpicDescription` (6 tests) pass; 16-01-SUMMARY.md live round trip shows epic `description` with `## Objective` |
| 5 | `parse_plan()` exposes each task's `type` attribute (D-03) | ✓ VERIFIED | `TASK_TYPE_RE = re.compile` present (1), `type` key added to task dict, used throughout `strip_task_bodies`/`resolve_issue` |
| 6 | A phase-wide, idempotent reconciliation pass closes any bd issue whose plan's SUMMARY.md exists but whose issue is still open (D-08) | ✓ VERIFIED | `reconcile_stale_closed()` present; `TestReconcileStaleClosed` (8 tests) pass, including `test_two_completed_plans_closes_four_ids_in_one_call` |
| 7 | Re-running the pass over an already-reconciled phase issues zero `bd close` calls (D-08) | ✓ VERIFIED | `test_repeat_run_over_already_reconciled_phase_issues_zero_close_calls` passes; live proof: second run printed `Closed 0 issue(s)` |
| 8 | `verify:post` dispatches reconciliation; `execute:wave:post` keeps dispatching `close-wave` unchanged (D-08) | ✓ VERIFIED | `beads-status/SKILL.md` Step 2b runs `reconcile-stale-closed` before `regenerate-beads-md` (grep confirmed at lines 103-121); `close_wave`'s own tests (`TestCloseWave`) unmodified and still pass |
| 9 | The four Phase 14 stale issues are closed in the live bd database (D-08) | ✓ VERIFIED | Live `bd list --id gsd-beads-bu0.3,.4,.5,.6 --json` returns `[]` (none open); `bd show gsd-beads-bu0.3 --json` shows `"status": "closed"`, `"close_reason": "phase-wide reconciliation: 14-pr-workflow-capability-dogfood"` |
| 10 | `bd` unavailable makes the subcommand print the standard notice, append a STATE.md blocker, and exit 0 (B6) | ✓ VERIFIED | `test_bd_unavailable_exits_zero_with_one_notice_and_closes_nothing` passes |
| 11 | `sync.py check-execute-plan-patch` reports present/absent for the machine-local patch, read-only (D-05) | ✓ VERIFIED | `check_execute_plan_patch()` present; live command run this session: `execute-plan.md bd-task-read patch: present (v1) ...`, exit 0 |
| 12 | A synced `auto`/`tracer` task block retains only name, beads-id, files, and a pointer comment (D-01) | ✓ VERIFIED | `test_strippable_auto_task_loses_content_elements`/`test_strippable_auto_task_keeps_identity_and_routing_elements`/`test_stripped_block_gains_exactly_one_pointer_comment` all pass; before/after evidence in 16-03-SUMMARY.md shows the exact transformation |
| 13 | A `checkpoint:*` task block is byte-identical after a sync (D-03) | ✓ VERIFIED | `test_checkpoint_decision_task_is_byte_identical`, `test_checkpoint_human_verify_task_is_byte_identical`, `test_no_type_attribute_task_is_byte_identical` all pass |
| 14 | Nothing is stripped on a machine where the patch is absent (D-05) | ✓ VERIFIED | `TestCreateIssuesStripGate` (2 tests, patch mocked 0 and 1) passes; live-confirmed at 16-03 close-out (patch absent → exit 1 → content left intact) |
| 15 | Only a task whose bd issue was created in this same run is stripped (D-07) | ✓ VERIFIED | `test_pre_existing_task_not_in_stripped_set_is_byte_identical` passes; strip set built exclusively from `task_updates` (sync.py code read) |
| 16 | `gsd-executor` reads an `auto`/`tracer` task's instructions from `bd show <beads-id> --json`, not from the PLAN.md task block (D-01) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Patch text installed at the correct anchor (verified: first bullet under "3. Per task:", markers present ×2) — but no live gsd-executor run has exercised this branch; see Human Verification |
| 17 | A failing `bd show` halts execution, never a silent fall-back (D-04) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | bd's failure signature independently re-confirmed live (`bd show <bad-id> --json` → exit 1, `error` key) and the patch's halt-branch text matches it exactly — but agent halt-compliance is unexercised; see Human Verification |
| 18 | `checkpoint:*` tasks and plan-level sections are always read from PLAN.md, unchanged (D-02, D-03) | ✓ VERIFIED | `<step name="load_prompt">`'s `cat` line unchanged (grep confirmed, count=1); the patch's closing paragraph states the exclusions verbatim; this is pre-existing, unmodified behavior, not new code needing live exercise |
| 19 | A bd issue with empty description routes to inline PLAN.md body with a printed notice (D-07) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Branch text installed and byte-identical to `GSD-CORE-PATCH.md`'s record — but 16-04-SUMMARY.md itself records no live exercise of this branch; see Human Verification |
| 20 | `check-execute-plan-patch` reports present after this plan runs, dispatched at `plan:pre` (D-05) | ✓ VERIFIED | Live command confirms `present (v1)`; `beads-recall/SKILL.md` grep shows `check-execute-plan-patch` (2 occurrences) alongside `check-shipmd-patch` (1) |
| 21 | The gsd-core change is filed upstream with an explicit revert condition (D-05) | ✓ VERIFIED | `gh issue view 3646 --repo open-gsd/gsd-core` → OPEN; revert condition in `GSD-CORE-PATCH.md` names all 4 artifacts to delete; `.planning/STATE.md` records issue with re-check discipline |

**Score:** 18/21 truths verified (3 present, behavior-unverified)

### Required Artifacts

All artifacts verified against the git-tracked source at
`plugins/beads-lifecycle/.gsd/capabilities/beads/` — per this phase's own documented Rule 3
deviation, this is the real source of truth, not the gitignored `.gsd/capabilities/beads/`
runtime mirror the plans' frontmatter named.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `sync.py::TASK_TYPE_RE`, `READ_FIRST_RE`, `PRECONDITION_RE`, `BEHAVIOR_RE`, `ACTION_RE`, `VERIFY_RE`, `ACCEPTANCE_CRITERIA_RE`, `DONE_RE`, `OBJECTIVE_RE` | 9 module-level regexes | ✓ VERIFIED | Each grep-confirmed present exactly once |
| `sync.py::_task_description()`, `_epic_description()`, `get_milestone_bullet()` | Renderer functions | ✓ VERIFIED | All present, read in full, correctly implemented |
| `sync.py::_checkpoint_task_description()` (CR-01 fix) | Checkpoint content renderer | ✓ VERIFIED | Present, dispatched from `resolve_issue` for `checkpoint:*` types (code read at sync.py:853-856) |
| `sync.py::reconcile_stale_closed()` | Phase-wide close backstop | ✓ VERIFIED | Present, wired in `main()`, 8 passing tests |
| `sync.py::check_execute_plan_patch()`, `EXECUTE_PLAN_PATCH_MARKER` | Read-path patch detector | ✓ VERIFIED | Present; hardened with `try/except (OSError, UnicodeDecodeError)` per CR-02 fix (code read at sync.py:2019-2021) |
| `sync.py::strip_task_bodies()` | PLAN.md pointer-conversion | ✓ VERIFIED | Present, gated correctly inside `create_issues` (code read at sync.py:1231-1247) |
| `test_sync.py` — `TestTaskDescription`, `TestEpicDescription`, `TestCheckpointTaskDescription`, `TestReconcileStaleClosed`, `TestCheckExecutePlanPatch`, `TestStripTaskBodies`, `TestCreateIssuesStripGate` | 7 test classes | ✓ VERIFIED | All present; full suite 134 tests, 0 failures, 0 errors (independently re-run this session) |
| `beads-status/SKILL.md` — revised Step 2b, Anti-Pattern 6/6a | verify:post reconciliation wiring | ✓ VERIFIED | `reconcile-stale-closed` runs before `regenerate-beads-md`; ordering rationale stated |
| `beads-recall/SKILL.md` — Step 3.5, Anti-Pattern 5 | plan:pre dual-patch detection | ✓ VERIFIED | `check-execute-plan-patch` (2 hits) joined alongside `check-shipmd-patch` (1 hit) |
| `GSD-CORE-PATCH.md` — two-patch register | Patch 1 (ship.md) + Patch 2 (execute-plan.md) | ✓ VERIFIED | Both marker sets present (4 hits each); revert conditions for both name all affected artifacts; no `PENDING` placeholder remains |
| `$HOME/.claude/gsd-core/workflows/execute-plan.md` (machine-local) | bd-task-read patch installed | ✓ VERIFIED | Live-confirmed this session: marker present ×2, positioned as first bullet under "3. Per task:", `check-execute-plan-patch` exits 0 |
| `.planning/STATE.md` | Both upstream issue numbers recorded | ✓ VERIFIED | Both #3646/#3647 present with re-check discipline |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `parse_plan()` task dict | `resolve_issue()`'s `bd create` argv | `_task_description()` / `_checkpoint_task_description()` | ✓ WIRED | Code read directly; dispatch by `type` prefix confirmed |
| `resolve_issue()` | `bd show --json`'s `acceptance_criteria` key | `--acceptance` argv element, never folded into `-d` | ✓ WIRED | Code read (sync.py:857-861); live tracer test confirms both keys distinct |
| `verify:post` dispatch | `bd close` (batched) | `beads-status/SKILL.md` Step 2b → `reconcile-stale-closed` → `_resolve_completed_task_ids` + `filter_open_ids` | ✓ WIRED | SKILL.md text + sync.py code both confirmed; live proof (4 closed, then 0 on re-run) |
| `create_issues`' rewrite path | PLAN.md write | `strip_task_bodies(new_text, newly_created_ids)`, gated on `check_execute_plan_patch() == 0` | ✓ WIRED | Code read at sync.py:1231-1247 |
| `plan:pre` | patch-loss detection | `beads-recall/SKILL.md` Step 3.5 → `sync.py check-execute-plan-patch` | ✓ WIRED | grep-confirmed, live command exits 0 |
| `execute-plan.md`'s `execute` step, item 3 | task instructions | `bd show <beads-id> --json` → `description`+`acceptance_criteria` become instructions | ⚠️ INSTALLED, NOT RUNTIME-EXERCISED | Text correctly installed at the anchor; no live gsd-executor run has followed this path yet (see truths #16/#17/#19) |

### Requirements Coverage

Per ROADMAP.md, Phase 16's requirements (D-01 through D-08) are recorded in
`16-CONTEXT.md`, not `REQUIREMENTS.md` — no `REQ-*` entries exist for this phase, confirmed by a
direct grep of `REQUIREMENTS.md` returning zero matches for "Phase 16"/"beads-issue-content-parity".
This is explicitly documented in ROADMAP.md as intentional (discuss-phase decisions are the
requirements source of truth for this phase). No orphaned requirements found.

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| D-01 | 16-01, 16-03, 16-04 | Full inversion: bd is the source, PLAN.md becomes a pointer, gsd-executor reads from bd | ⚠️ Write+strip half VERIFIED; read half (executor behavior) PRESENT_BEHAVIOR_UNVERIFIED | See truths #12, #16 |
| D-02 | 16-01, 16-04 | Plan-level content stays in PLAN.md | ✓ SATISFIED | Truth #2, #18 |
| D-03 | 16-01, 16-03, 16-04 | Checkpoint tasks excluded from inversion | ✓ SATISFIED | Truths #5, #13, #18 |
| D-04 | 16-04 | bd-unreachable is a hard failure | ⚠️ Signature VERIFIED; executor halt behavior PRESENT_BEHAVIOR_UNVERIFIED | Truth #17 |
| D-05 | 16-03, 16-04 | File the gsd-core patch upstream immediately; run local patch until merged | ✓ SATISFIED | Truths #11, #14, #20, #21 |
| D-06 | 16-01 | Forward-only backfill: new task/epic creation writes real description | ✓ SATISFIED | Truths #1, #3, #4 |
| D-07 | 16-03, 16-04 | Forward-only migration: only phases planned after this change get stripped; Phase 1-15 untouched | ⚠️ File-preservation VERIFIED (git history confirms zero Phase 1-15 file touches); empty-description fallback behavior PRESENT_BEHAVIOR_UNVERIFIED | Truths #15, #19 |
| D-08 | 16-02 | Root-cause and fix `close_wave()` gap; close 4 stale issues as proof | ✓ SATISFIED | Truths #6-#10 |

### Anti-Patterns Found

None. Scanned all files modified by this phase (`sync.py`, `test_sync.py`, both `SKILL.md` files,
`GSD-CORE-PATCH.md`, the machine-local `execute-plan.md` patch block) for `TODO`/`FIXME`/`XXX`/
`HACK`/`PLACEHOLDER`/"not yet implemented"/"coming soon" — zero matches. No unfilled `PENDING`
placeholder remains in `GSD-CORE-PATCH.md`.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite passes | `python3 -m unittest discover -s plugins/beads-lifecycle/.gsd/capabilities/beads/tests -v` | `Ran 134 tests in 4.191s / OK` | ✓ PASS |
| Live tracer test round-trips real content | `TestEndToEndTracer` (2 tests, real `bd`, not mocked) | Both `ok`, not skipped | ✓ PASS |
| check-execute-plan-patch reports present | `python3 sync.py check-execute-plan-patch` | `present (v1) ... exit=0` | ✓ PASS |
| D-04 failure signature | `bd show gsd-beads-no-such-id-verify --json` | exit 1, `{"error": "no issues found matching the provided IDs", ...}` | ✓ PASS |
| D-08 stale issues closed live | `bd list --id gsd-beads-bu0.3,.4,.5,.6 --json` | `[]` (none open) | ✓ PASS |
| D-08 close_reason distinguishable | `bd show gsd-beads-bu0.3 --json` | `close_reason: "phase-wide reconciliation: 14-pr-workflow-capability-dogfood"` | ✓ PASS |
| CR-01 checkpoint create-path integration test | `-k test_checkpoint_decision_task_create_argv_carries_real_content` | `ok` | ✓ PASS |
| Upstream issues live and OPEN | `gh issue view 3646/3647 --repo open-gsd/gsd-core` | Both `"state":"OPEN"` | ✓ PASS |
| No Phase 1-15 files touched | `git log --oneline --name-only 7fccc61..0d1343d \| grep phases/0[1-9]\|1[0-5]-` | No output | ✓ PASS |

### Code Review Fix Verification

`16-REVIEW.md` found 2 Critical + 2 Warning issues; `16-REVIEW-FIX.md` claims all 4 fixed. Each
was independently re-verified against the current tracked source (not taken on the SUMMARY's word):

| Finding | Claim | Verification | Status |
|---|---|---|---|
| CR-01 | Checkpoint tasks get a real description via `_checkpoint_task_description` | Code read at sync.py:832-866: `resolve_issue` dispatches to `_checkpoint_task_description` for `type.startswith("checkpoint:")`; integration test `test_checkpoint_decision_task_create_argv_carries_real_content` passes | ✓ VERIFIED FIXED |
| CR-02 | `check_execute_plan_patch()`'s file read is hardened so a crash never orphans a just-created bd issue | Code read at sync.py:2019-2021: `try/except (OSError, UnicodeDecodeError)` around `.read_text()`, degrading to return 1 | ✓ VERIFIED FIXED |
| WR-01 | `get_milestone_bullet` anchors the match to token boundaries | Code read at sync.py:661-676: `re.compile(rf"(?<![\w.]){re.escape(milestone)}(?![\w.])")` | ✓ VERIFIED FIXED |
| WR-02 | `check_shipmd_patch`'s file read gets the same I/O guard | Code read at sync.py:1953-1960: same `try/except (OSError, UnicodeDecodeError)` pattern | ✓ VERIFIED FIXED |

### Human Verification Required

Three items, all in the same class: the machine-local `execute-plan.md` patch's text is installed
correctly and byte-verified against its documented record, but its actual effect on a live
`gsd-executor` run has not yet been observed by any executed phase (16 was the phase that built
the mechanism; no phase since has run against a stripped/inverted plan). This is not a code gap —
`sync.py`'s writer/detector/stripper side is fully tested and live-proven — it is prose interpreted
by an LLM agent at execution time, which only a real execution can confirm.

#### 1. gsd-executor reads task content from bd, not PLAN.md

**Test:** Run `execute-plan.md` against a PLAN.md whose `auto`/`tracer` task was stripped by this
phase's `sync.py`, and observe the agent's behavior.
**Expected:** The agent runs `bd show <beads-id> --json`, prints
`beads: task content read from bd (<beads-id>)`, and carries out the task using bd's
`description`/`acceptance_criteria` — never re-deriving instructions from the absent PLAN.md body.
**Why human:** LLM-interpreted markdown instruction; not unit-testable.

#### 2. Hard halt on unreachable bd

**Test:** During a live run, point a task's `<beads-id>` at an unreachable/deleted bd issue and
observe whether the agent halts.
**Expected:** Execution stops with the exact `FATAL: bd task content unreachable for <beads-id> ...`
message; no silent fall-back to PLAN.md.
**Why human:** Agent halt-compliance is behavior, not code; only bd's own failure signature was
live-confirmed this session.

#### 3. Empty-description pre-migration fallback

**Test:** Run `execute-plan.md` against a Phase 1-15-vintage task whose bd issue has an empty
`description` and observe the fallback.
**Expected:** Agent reads the inline PLAN.md task body and prints
`beads: <beads-id> carries no description -- using inline PLAN.md task body (pre-migration plan)`.
**Why human:** Same LLM-runtime class as items 1-2; 16-04-SUMMARY.md's own coverage table already
flags this branch as unexercised.

### Gaps Summary

No blocking gaps. All 18 code-level truths (write path D-06, strip path D-01/D-03/D-07 file
preservation, reconciliation D-08, detector/upstream-filing D-05) are VERIFIED with live evidence
independently re-run this session — not merely SUMMARY claims. All 4 code-review findings (2
Critical, 2 Warning) are confirmed fixed in the tracked source, not just claimed fixed.

The 3 PRESENT_BEHAVIOR_UNVERIFIED items are the read-path's actual effect on a running
`gsd-executor` agent (D-01's read half, D-04's halt behavior, D-07's fallback behavior). The
installed patch text is correct and byte-verified against its documented record, and its
prerequisites (bd's own failure signature, the detector, the strip mechanism) are all live-proven
— but no phase has yet executed a real inverted task through `gsd-executor`, so the prose's actual
runtime effect on agent behavior is unobserved. This is inherent to the mechanism (an LLM
interpreting markdown, not code a test suite can exercise) and is honestly self-disclosed in
16-04-SUMMARY.md's own coverage table (`human_judgment: true` on the D-07 item). Recommend
resolving via human verification during this phase's UAT, or accepting the risk and observing the
first future phase that actually executes an inverted task.

---

_Verified: 2026-08-19T02:00:00Z_
_Verifier: Claude (gsd-verifier)_
