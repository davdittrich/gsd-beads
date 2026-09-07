---
phase: 24-remediate-sota-numerics-0-2-0-release-blockers
plan: 03
subsystem: infra
tags: [check-alternatives, plan-gate, tdd, regex, state-parsing, cross-repo]

# Dependency graph
requires:
  - phase: 24-01
    provides: mask_leading_frontmatter (D-01) and mask_indented_code_blocks (D-02), and the D-05 pre-edit baseline table (Corpus A 1,0,0,1,0,0; Corpus B 105 tests) this plan diffs against
provides:
  - BULLET_RE and TABLE_ROW_RE bounded to CommonMark's zero-to-three-space top-level indentation range (D-03)
  - resolve_current_phase_dir's frontmatter branch demands exactly one current_phase match, parallel to the body branch (D-04)
  - the cumulative D-05 verdict diff for the whole D-01-through-D-04 gate change set, naming a fourth fail-open shape D-05 did not originally enumerate
  - D-17 pre/post-edit values for the live install-mirror sidecar and the independently re-measured bundle hash
affects: [24-08]

# Actuals (#2632)
actuals:
  tokens: 3583
  tasks: 3
  commits: 5
commits_note:
  This plan's code/test edits land in a DIFFERENT repository than this SUMMARY
  (target_repo per 24-03-PLAN.md frontmatter): the sota-numerics worktree at
  /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013, branch
  feat/extended-sota-definition. Four commits landed there: 8a443d4 (test,
  Task 1 RED), 55ded41 (test, Task 2 RED), 14307c0 (fix, Task 1 GREEN),
  e1818c5 (fix, Task 2 GREEN) -- git rev-list --count 2321b74..e1818c5 = 4.
  The `tokens` actual above (3583 = 14332 chars / 4) is measured from
  `git diff --shortstat 2321b74 e1818c5` in that worktree (2 files, 189
  insertions, 10 deletions), NOT from this orchestrator repo's diff.
  This orchestrator repo (gsd-beads, branch main, git.branching_strategy:
  "none") carries only this SUMMARY commit for Task 3; ledger base
  (gsd-plan-head-before-24-03) recorded at f0a2103, the commit immediately
  preceding this plan's first edit (24-02's final metadata commit). git
  rev-list --count f0a2103..HEAD at SUMMARY-write time is 1 (this SUMMARY
  commit). The `commits: 5` total above sums both repos (4 target-repo task
  commits + 1 orchestrator SUMMARY commit); the subsequent final_commit
  (STATE.md/ROADMAP.md/REQUIREMENTS.md) is a separate, later commit per the
  standard executor protocol and is not included in this count.

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - .gsd/capabilities/sota-numerics/scripts/check-alternatives.py
    - tests/test_check_alternatives.py

key-decisions:
  - "Bounded BULLET_RE and TABLE_ROW_RE's leading-indentation class to [ \\t]{0,3} (CommonMark's own zero-to-three-space top-level range) rather than tracking list-nesting depth in a structural pre-pass or delegating to markdown-it-py/PyYAML -- the plan's Alternatives Considered section already selected the in-place regex bound; this plan verified it against the real corpus rather than re-litigating the choice."
  - "Split each task's single working-tree diff into a separate RED-only commit and GREEN-only commit by reconstructing intermediate file states from git blobs (git show <base>:<path> plus exact line-range splicing verified byte-identical before writing), rather than accepting one mixed commit -- CLAUDE.md's git-safety rules forbid -i/--no-verify but the working tree had both tasks' RED tests applied before either task's commit; reconstruction was the only way to keep the test(RED)->fix(GREEN) pairing per task without discarding and re-writing either task's tests."
  - "Independently re-measured the D-17 pre-edit bundle hash rather than trusting the prior session's recorded value: a first attempt using a relative BUNDLE_DIR path and a separate attempt via `git archive` both produced different hashes than the historical value, because bundle_hash.sh's sha256sum output embeds the path string it was invoked with and capability-auto-install.sh always hashes an ABSOLUTE PLUGIN_ROOT-rooted path. Re-running with the correct absolute path reproduced the historical pre-edit value (9b76f03bb0...) exactly, confirming it rather than assuming it."

patterns-established: []

requirements-completed: [D-01, D-03, D-04, D-05, D-06, D-17]

coverage:
  - id: D1
    description: "BULLET_RE and TABLE_ROW_RE bound their leading indentation to [ \\t]{0,3}, closing the D-03 fail-open where an Alternatives Considered entry stated only as a 4-space-or-deeper sub-bullet or sub-table-row satisfied the top-level 'at least two named alternatives' gate."
    requirement: D-03
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py::TestBulletIndentationBound (4 tests: 2 RED-then-GREEN, 2 regression pins) -- commits 8a443d4 (RED), 14307c0 (GREEN)"
        status: pass
    human_judgment: false
  - id: D2
    description: "resolve_current_phase_dir's frontmatter branch now uses STATE_CURRENT_PHASE_RE.findall() and demands exactly one match, closing the D-04 fail-open where a duplicated frontmatter current_phase key silently resolved to whichever phase matched first instead of halting, unlike the body branch which already demanded exactly one."
    requirement: D-04
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py::TestCurrentPhaseResolution (4 new tests: 3 RED-then-GREEN, 1 regression pin) -- commits 55ded41 (RED), e1818c5 (GREEN)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Cumulative D-05 verdict diff for the whole D-01-through-D-04 gate change set: Corpus A (6 real phase directories) and Corpus B (Python suite) measured before this plan's edits and after, with every crafted fail-open fixture whose verdict moved itemised and counted, naming the fourth shape (frontmatter-masking, D-01) that D-05's original three-shape count did not enumerate."
    requirement: D-05
    verification:
      - kind: other
        ref: "This SUMMARY's 'D-05 cumulative evidence' section, below"
        status: pass
    human_judgment: false
  - id: D4
    description: "D-17: pre/post-edit values recorded for both the live install-mirror sidecar (~/.gsd/capability-auto-install-sota-numerics.hash) and an independently re-measured whole-bundle hash of .gsd/capabilities/sota-numerics."
    requirement: D-17
    verification:
      - kind: other
        ref: "This SUMMARY's 'D-17 hash sidecar' section, below"
        status: pass
    human_judgment: false

duration: n/a (continued across context compaction)
completed: 2026-09-07
status: complete
---

# Phase 24 Plan 03: Bound bullet/table-row indentation and demand exactly one frontmatter current_phase match Summary

**Closed the last two fail-open shapes in check-alternatives.py (D-03 unbounded sub-bullet/sub-table-row indentation, D-04 duplicated frontmatter current_phase) via TDD RED/GREEN pairs, then recorded the cumulative D-05 verdict diff for the whole four-shape gate change set spanning plans 24-01 and 24-03, naming a fourth shape D-05's original count did not enumerate.**

## Performance

- **Duration:** n/a (continued across context compaction)
- **Completed:** 2026-09-07T21:38:54Z
- **Tasks:** 3/3 complete
- **Files modified:** 2 (target repo) + 1 (this SUMMARY, orchestrator repo)

## Accomplishments

- Bounded `BULLET_RE` and `TABLE_ROW_RE`'s leading-indentation class from unbounded `[ \t]*` to `[ \t]{0,3}` (CommonMark's own zero-to-three-space top-level range), closing D-03: a plan whose Alternatives Considered entries existed only as 4-space-or-deeper indented sub-bullets or sub-table-rows could previously satisfy the "at least two named alternatives" gate on a section that named zero alternatives at the level the requirement is about.
- Changed `resolve_current_phase_dir`'s frontmatter branch from `STATE_CURRENT_PHASE_RE.search(...)` (first match) to `.findall(...)` with an exactly-one check, closing D-04: a STATE.md frontmatter block with a duplicated `current_phase:` key previously let the gate silently resolve to whichever phase matched first, instead of halting the way the body parse (`## Current Position`'s `Phase:` lines) already did.
- Ran the full Python suite (113/113 pass, up from 24-01's 105), the real 6-phase-directory corpus sweep, and an independent D-17 bundle-hash re-measurement before and after both fixes; recorded the cumulative before/after diff for the whole D-01-through-D-04 change set below.
- Produced and machine-validated (`gsd_run check tdd-red-evidence` -> `RED_EVIDENCE_OK`) a TAP-format RED-evidence record for each task before applying its GREEN fix.

## Task Commits

All commits below are in the **target repository** (`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`), per this plan's `target_repo` frontmatter -- not this orchestrator repo.

1. **Task 1: Bound bullet indentation to the CommonMark top-level range**
   - `8a443d4` (test) -- `TestBulletIndentationBound`: 2 RED cases (4-space sub-bullets/sub-table-rows wrongly counted as top-level) + 2 regression pins (0-3 space bullets still count; a compliant top-level entry still draws its citation from a sub-bullet). RED_EVIDENCE_OK.
   - `14307c0` (fix) -- `BULLET_RE`/`TABLE_ROW_RE` leading indentation bounded to `[ \t]{0,3}`. Full suite 113/113; Corpus A unchanged at `1,0,0,1,0,0`.
2. **Task 2: Make the frontmatter phase parse demand exactly one match, as the body parse already does**
   - `55ded41` (test) -- 4 new cases in `TestCurrentPhaseResolution`: 3 RED (duplicate `current_phase` names the count; three duplicates names 3; frontmatter and body ambiguity reasons are distinguishable) + 1 regression pin (single frontmatter `current_phase` still resolves). RED_EVIDENCE_OK.
   - `e1818c5` (fix) -- `resolve_current_phase_dir`'s frontmatter branch uses `findall()`, requires exactly one, preserves the existing zero-match message. Full suite 113/113; Corpus A unchanged at `1,0,0,1,0,0`.
3. **Task 3: Record the cumulative D-05 verdict diff for the whole gate change set**
   - This file (`24-03-SUMMARY.md`), committed in the orchestrator repo, records the diff below.

**Plan metadata:** committed separately after this SUMMARY, per the standard executor protocol (STATE.md/ROADMAP.md/REQUIREMENTS.md).

_TDD tasks each ran RED -> validated RED-evidence record -> GREEN, with the working tree's two tasks' RED tests reconstructed into separate per-task commits from git blobs (see Decisions Made) rather than one mixed test commit._

## Files Created/Modified

- `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (target repo) -- `BULLET_RE`/`TABLE_ROW_RE` indentation bound; `resolve_current_phase_dir` frontmatter exactly-one check.
- `tests/test_check_alternatives.py` (target repo) -- `TestBulletIndentationBound` (new class, 4 tests); 4 new tests appended to `TestCurrentPhaseResolution`.
- `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-03-SUMMARY.md` (this repo) -- this file.

## D-05 cumulative evidence

**Interpretation used (matching 24-01's precedent):** D-05's fixture corpus is Corpus B, the Python suite -- crafted fail-open fixtures are unittest cases, so a fixture's verdict changing shows up directly as that test's PASS/FAIL outcome rather than as a separate hand-run comparison. Corpus A (the real planning corpus) is checked separately for zero drift.

### Corpus A -- real `gsd-beads/.planning/phases/*` directories (exit code per directory, in fixed order 19/20/21/22/23/24)

| Measurement point | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|
| Phase-24 start (before any of D-01/D-02/D-03/D-04), per 24-01-SUMMARY.md | 1 | 0 | 0 | 1 | 0 | 0 |
| After 24-01 (D-01, D-02 closed), per 24-01-SUMMARY.md | 1 | 0 | 0 | 1 | 0 | 0 |
| After this plan's Task 1 (D-03 closed) -- measured | 1 | 0 | 0 | 1 | 0 | 0 |
| After this plan's Task 2 (D-04 closed) -- measured, final state | 1 | 0 | 0 | 1 | 0 | 0 |

Byte-identical across every measurement point in the whole D-01-through-D-04 gate change set. No real corpus verdict moved.

### Corpus B -- Python suite (`python3 -m unittest discover -s tests -v`)

| Measurement point | Test count | Failures |
|---|---|---|
| Phase-24 start, per 24-01-SUMMARY.md | 97 | 0 |
| After 24-01 (D-01, D-02 closed; +8 tests) | 105 | 0 |
| After this plan's Task 1 RED (+4 tests: `TestBulletIndentationBound`) | 109 | 2 (both target tests, as designed) |
| After this plan's Task 1 GREEN | 109 | 0 |
| After this plan's Task 2 RED (+4 tests: `TestCurrentPhaseResolution` additions) | 113 | 3 (all three target tests, as designed) |
| After this plan's Task 2 GREEN, final state | 113 | 0 |

This plan added 8 new tests (109 - 105 = 4 for D-03, 113 - 109 = 4 for D-04), all passing at final state. Exceeds the 24-01 baseline of 105 as required by this plan's `<verification>`.

### Crafted fail-open fixtures whose verdict changed, across the whole D-01-through-D-04 gate change set

**Count as measured: 4 distinct fail-open shapes closed across the phase, not the 3 D-05 originally named.** D-05 (as decided) names three crafted shapes; the fourth -- the frontmatter-masking shape closed by plan 24-01 Task 2 (D-01) -- was raised by AGY review after that decision was written and is named here explicitly rather than silently folded into a count of three. 7 individual test methods pin these 4 shapes (D-04 has three test variants: two duplicate-count cases plus one message-shape/distinguishability case):

| # | Shape (requirement) | Test | Pre-fix exit (unfixed script) | Post-fix exit |
|---|---|---|---|---|
| 1 | Frontmatter-masking (D-01, closed in 24-01) | `TestFrontmatterMasking.test_a_section_declared_only_in_frontmatter_is_a_missing_section` | 0 (fail-open) | 1 (blocked) |
| 2 | Indented-code-block masking (D-02, closed in 24-01) | `TestIndentedCodeBlocks.test_indented_alternatives_are_not_counted_as_prose` | 0 (fail-open) | 1 (blocked) |
| 3 | Bullet indentation bound (D-03, this plan) | `TestBulletIndentationBound.test_entries_stated_only_as_four_space_sub_bullets_are_not_top_level` | 0 (fail-open) | 1 (blocked) |
| 4 | Table-row indentation bound (D-03, this plan) | `TestBulletIndentationBound.test_entries_stated_only_as_four_space_table_rows_are_not_top_level` | 0 (fail-open) | 1 (blocked) |
| 5 | Frontmatter duplicate current_phase (D-04, this plan) | `TestCurrentPhaseResolution.test_duplicate_current_phase_in_frontmatter_blocks_naming_the_count` | 0 (fail-open) | 2 (blocked, ambiguity) |
| 6 | Frontmatter duplicate current_phase, 3x (D-04, this plan) | `TestCurrentPhaseResolution.test_three_duplicate_current_phase_fields_names_the_exact_count` | 0 (fail-open) | 2 (blocked, ambiguity) |
| 7 | Frontmatter duplicate current_phase, message shape (D-04, this plan) | `TestCurrentPhaseResolution.test_frontmatter_and_body_ambiguity_reasons_are_distinguishable` (frontmatter half only -- the body half was already exit 2 pre-fix and is unaffected) | 0 (fail-open) | 2 (blocked, ambiguity) |

No other verdict moved: every other test present both before and after this plan's edits (109 - 4 = 105 tests pre-existing at Task 1's start, 113 - 8 = 105 tests pre-existing at Task 2's completion) kept its prior PASS/FAIL outcome, and Corpus A above is byte-identical at every measurement point.

## D-17 hash sidecar

Per D-17, `~/.gsd/capability-auto-install-sota-numerics.hash` is written by the plugin's own `SessionStart`/`SubagentStart` hook (`hooks/capability-auto-install.sh`), which hashes the whole `.gsd/capabilities/sota-numerics` directory using an **absolute**, `PLUGIN_ROOT`-rooted path (deliberately, per the script's own comment: rooting the hash is what lets two plugin roots serving the same capability id share or diverge a fast path). This plan recorded both the live sidecar value and an independently re-measured whole-bundle hash, pre- and post-edit:

| Value | Pre-edit (this plan's start, commit `2321b74`) | Post-edit (this plan's end, commit `e1818c5`) |
|---|---|---|
| Live sidecar (`~/.gsd/capability-auto-install-sota-numerics.hash`) | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` (unchanged) |
| Independently re-measured whole-bundle hash (absolute path, matching the hook's own computation) | `9b76f03bb04fb7cfa813813e0a72c4b5d441c082492a1889bd506de19cf14f59` | `909bd37ef555b4042241eb10f2ed046b2be06a39224a1aa722e14116c7360a08` |

The pre-edit re-measurement (`9b76f03bb0...`) exactly matches the value recorded earlier this session, confirming it rather than assuming it (see Decisions Made for why two other measurement attempts -- relative-path and `git archive`-based -- produced different, non-comparable hashes before this one used the correct absolute path). The live sidecar's unchanged value is the known, deferred, non-blocking D-17 hazard from 24-01: it reflects whatever bundle state was hashed at the last hook fire in this in-tree worktree, not necessarily this plan's edits, and is restored to the released plugin-cache bundle by plan 24-08 per that plan's own scope. This plan did not touch the sidecar or `~/.gsd/capabilities/sota-numerics/...` (the install mirror) -- only the worktree source, per this plan's explicit instruction.

## Decisions Made

See `key-decisions` in frontmatter above.

## Deviations from Plan

None outside ordinary TDD/RED-evidence mechanics. Two clarifications worth recording explicitly:

**1. [Process] Reconstructed per-task RED commits from git blobs rather than one mixed test commit.**
- **Found during:** Task 1/Task 2 boundary. Both tasks' RED tests were applied to the same working file before either was committed (Task 1's RED tests were applied in an earlier part of this same session, before compaction; Task 2's RED tests were added after resuming).
- **Issue:** Committing the file as-is would mix Task 1's and Task 2's RED tests into a single commit, breaking the plan's per-task test-then-feat commit pairing.
- **Fix:** Used `git show <commit>:<path>` to get the pre-session base file, spliced in only Task 1's test class at its exact line range (verified byte-for-byte against the full working file via a reconstruction equality assertion before writing), committed that as Task 1's RED commit, then restored the full working file (both tasks' tests) and committed the delta as Task 2's RED commit.
- **Files modified:** `tests/test_check_alternatives.py` (target repo) only; no production code touched by this reconstruction.
- **Verification:** Reconstructed content compared byte-for-byte (Python string equality) against the actual working file before either commit; both intermediate states re-run through the target test class to confirm the expected RED count at each step (2 failures after Task 1's commit, 3 additional failures after Task 2's commit).
- **Committed in:** `8a443d4`, `55ded41`.

**2. [Rule 1 - methodology bug, self-caught] First two D-17 bundle-hash re-measurements used the wrong path shape and were discarded.**
- **Found during:** Task 3, independently re-verifying the D-17 pre-edit hash rather than trusting the prior session's recorded value (per this project's Volatile-State Authority rule: historical hints are hypotheses until observed).
- **Issue:** `bundle_hash.sh`'s `sha256sum`/`find` output embeds the invoked path string, so a relative-path invocation and a `git archive`-reconstructed-directory invocation both produced hashes that could not be compared to the live hook's own (always absolute-path) computation, momentarily looking like non-determinism in the D-17 hazard itself.
- **Fix:** Re-read `capability-auto-install.sh` to find `PLUGIN_ROOT="$(cd "${CLAUDE_PLUGIN_ROOT:-...}" ... && pwd)"` (always absolute), then re-ran the hash tool with the correct absolute `BUNDLE_DIR`. This reproduced the historical pre-edit value exactly.
- **Files modified:** None (measurement-only; the one production file was reverted and restored byte-for-byte within the same command sequence, confirmed via `git status --short` returning clean before proceeding).
- **Verification:** `git status --short` clean after each temporary revert/restore cycle; final absolute-path pre-edit measurement matched the prior session's recorded value exactly.

---

**Total deviations:** 0 auto-fixed (no Rule 1-4 code/test changes outside the plan's own scope); 2 process notes documented above for full evidentiary transparency.
**Impact on plan:** No scope creep. Both notes are about how evidence was assembled, not what was built.

## Issues Encountered

None blocking. See Deviations from Plan above for the two self-caught-and-corrected measurement issues.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- All four fail-open shapes named across D-01 through D-04 are closed: frontmatter-masking, indented-code-block masking, bullet/table-row indentation bound, and frontmatter duplicate-`current_phase` resolution.
- The real planning corpus (Corpus A) verdicts are exactly what they were before Phase 24 began, at every measurement point across both plans in this wave.
- `~/.gsd/capabilities/sota-numerics/...` (the install mirror) was never touched by this plan; only the worktree source at `target_repo` was edited, per this plan's explicit instruction.
- The live D-17 sidecar remains in its previously-documented stale state (unchanged pre/post this plan) -- plan 24-08's scope, not this plan's, per 24-01/D-17.
- Plan 24-08 (or whichever plan performs the merge/publish) has this plan's independently re-verified D-17 bundle-hash measurement method (absolute `PLUGIN_ROOT`-rooted path) to avoid the two false-non-determinism readings this plan hit and discarded.

## Self-Check: PASSED

- FOUND: `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`
- FOUND: `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/tests/test_check_alternatives.py`
- FOUND: `/home/dd/projects/gsd-beads/.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-03-SUMMARY.md`
- FOUND commit `8a443d4` (Task 1 RED, target repo)
- FOUND commit `55ded41` (Task 2 RED, target repo)
- FOUND commit `14307c0` (Task 1 GREEN, target repo)
- FOUND commit `e1818c5` (Task 2 GREEN, target repo)
- FOUND bd ticket `gsd-beads-25vc.6`: closed, commented
- FOUND bd ticket `gsd-beads-25vc.7`: closed, commented

---
*Phase: 24-remediate-sota-numerics-0-2-0-release-blockers*
*Completed: 2026-09-07*
