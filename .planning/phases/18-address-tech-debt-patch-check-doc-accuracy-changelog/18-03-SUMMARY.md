---
phase: 18-address-tech-debt-patch-check-doc-accuracy-changelog
plan: 03
subsystem: testing
tags: [python, unittest, tdd, docs-accuracy, sync.py, skill-md]

requires:
  - phase: 18-01
    provides: "both machine-local gsd-core patches restored on both runtime homes, so the plugin-tree suite is green (252/252) instead of FAILED (failures=6)"
provides:
  - "All four PATCH_CHECKS problem-reporting message templates (ship-md and execute-plan, not-found and could-not-read) carry the same '⚠ ' marker missing_msg already used, pinned by four new per-target tests"
  - "Both beads-recall and beads-status SKILL.md surfacing rules keyed to check_patch's exit code / absence of 'present' instead of the marker glyph"
  - "check_sync_mode_value's docstring and the plan:pre call-site comment above it no longer claim a stderr-only convention that does not exist -- both corrected to state the true shared-stdout behavior"
  - "A pinning comment on check_patch's final print() recording why stdout is deliberate (WR-01), so the docstring and implementation cannot drift apart again"
  - "Runtime overlay (.gsd/capabilities/beads/) re-synced and proven byte-identical to the tracked plugin source via diff -rq"
affects: [beads-recall, beads-status, sync.py-check-patch]

actuals:
  tokens: 4091
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "TDD RED-then-GREEN within a single commit, per the doc-sweep-in-same-commit convention Phase 17's TRUTH-01 plan established -- tests, template change, and consuming-doc change land together rather than as three separate TDD-cycle commits"

key-files:
  created: []
  modified:
    - "plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py"
    - "plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py"
    - "plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md"
    - "plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md"
    - ".gsd-capabilities.json"

key-decisions:
  - "Discovered (not caused) an out-of-scope defect during Task 3's overlay-vs-plugin-tree comparison: three test classes resolve PLUGIN_ROOT via a fixed Path(__file__).resolve().parents[4] traversal that lands correctly from the plugin tree but outside the vendored subtree from the runtime overlay, since hooks/ is never vendored into .gsd/capabilities/beads/. Ticketed as gsd-beads-2e2, logged to WINDOWS.md and deferred-items.md, not fixed (not in Task 3's declared files, pre-existing, unrelated to Task 1/2's edits)."

requirements-completed: []

coverage:
  - id: D1
    description: "All four PATCH_CHECKS not_found_msg/could_not_read_msg templates (ship-md x2, execute-plan x2) carry the '⚠ ' marker, with per-target tests that went red before the prefix existed"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestPatchChecksTable (15 tests, includes the 4 new test_*_carries_the_marker methods)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Both beads-recall and beads-status SKILL.md surfacing rules key off check_patch's exit code / absence of 'present' rather than the marker glyph"
    verification:
      - kind: other
        ref: "grep -c 'warning line' returns 0 in both SKILL.md files; both contain 'non-zero', 'onError: skip', and 'verbatim'"
        status: pass
    human_judgment: false
  - id: D3
    description: "check_sync_mode_value's docstring and the plan:pre call-site comment no longer claim a stderr-only convention that does not exist"
    verification:
      - kind: unit
        ref: "grep -c 'benign-skip convention' and grep -c 'stderr-only' in sync.py both return 0; python3 -c import check confirms 'stdout' still present in the docstring"
        status: pass
    human_judgment: false
  - id: D4
    description: "Runtime overlay is byte-identical to the tracked plugin source after re-sync"
    verification:
      - kind: other
        ref: "diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/ (silent, exit 0)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Full suite green from the plugin tree at N >= 252; overlay tree run also observed and recorded, though it exposed a pre-existing, out-of-scope test-fixture defect (see Deviations)"
    verification:
      - kind: unit
        ref: "python3 -m unittest discover -s tests -t tests from plugins/beads-lifecycle/.gsd/capabilities/beads/ -> Ran 252 tests, OK"
        status: pass
    human_judgment: true
    rationale: "Task 3's own acceptance criterion expected the identical command from .gsd/capabilities/beads/ to also report OK. It instead reports Ran 252 tests, FAILED (failures=12, errors=2) -- confirmed to be a pre-existing PLUGIN_ROOT path-resolution bug in the tests (not a content-sync gap; diff -rq is byte-silent), out of scope for this task's declared files. A human should confirm this documented, ticketed divergence is an acceptable plan-completion state rather than a blocker."

duration: ~20min
completed: 2026-08-20
status: complete
---

# Phase 18 Plan 03: Doc-accuracy + marker fixes for sync.py's patch-check messages Summary

Marked all four patch-check problem messages with the '⚠ ' prefix `missing_msg` already used (per-target TDD tests, red then green), re-keyed both consuming SKILL.md surfacing rules to `check_patch`'s exit code instead of the marker glyph, corrected `check_sync_mode_value`'s docstring and its plan:pre call-site comment to stop claiming a stderr-only convention that never existed, pinned the true stdout rationale with a new comment on `check_patch`'s final print, and re-synced + proved the gitignored runtime overlay byte-identical to the tracked plugin source.

## Performance

- **Duration:** ~20 min
- **Tasks:** 3 completed
- **Files modified:** 7 (5 tracked source files + WINDOWS.md ledger + a new deferred-items.md)

## Accomplishments

- WR-02 closed: all four `not_found_msg`/`could_not_read_msg` templates across both `PATCH_CHECKS` targets now carry the `⚠ ` marker, pinned by 4 new tests (`test_ship_md_not_found_message_carries_the_marker`, `test_ship_md_could_not_read_message_carries_the_marker`, `test_execute_plan_not_found_message_carries_the_marker`, `test_execute_plan_could_not_read_message_carries_the_marker`) that were confirmed RED against the pre-change templates before the prefix landed.
- Both consuming SKILL.md files (`beads-recall` Step 3.5, `beads-status` Step 2d) no longer gate surfacing on the marker glyph -- both now key on exit code being non-zero or the output not containing `"present"`, so a future template that forgets the prefix still surfaces.
- WR-01 closed at both sites where the false claim was made: `check_sync_mode_value`'s docstring (`sync.py:803`) and the `lifecycle_dispatch` `plan:pre` call-site comment (`sync.py:941`), which the original review did not name.
- D-02 pinning comment added directly above `check_patch`'s final `print()` recording why stdout is deliberate, so the docstring and the implementation cannot drift apart the same way again.
- Runtime overlay re-synced via `gsd-tools capability update beads --scope project` (observed no-op at 0.4.0, as documented) and proven byte-identical to the plugin source via `diff -rq`, both before and after the re-sync.

## Task Commits

Each task was committed atomically:

1. **Task 1: Mark every problem message, then stop depending on the mark** - `eab4221` (feat)
2. **Task 2: Correct the stream claim where it is made, and pin the line it is about** - `60ad910` (docs)
3. **Task 3: Prove the runtime overlay executes the code the tests just verified** - `0682869` (chore)

_Note: Task 1 (tdd="true") ran its RED-then-GREEN cycle inside one commit per the plan's explicit doc-sweep-in-same-commit instruction, not the default separate RED/GREEN commit pattern._

## Files Created/Modified

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` - 4 message templates marked, docstring and call-site comment corrected, new D-02 pinning comment
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` - 4 new tests on `TestPatchChecksTable` (15 total, up from 11)
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md` - Step 3.5 surfacing rule re-keyed to exit code / "present" absence
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md` - Step 2d surfacing rule re-keyed the same way
- `.gsd-capabilities.json` - `updatedAt` bumped by the re-sync (only field changed)
- `.planning/WINDOWS.md` - one new `unmet-truth` entry for the overlay test-fixture finding
- `.planning/phases/18-address-tech-debt-patch-check-doc-accuracy-changelog/deferred-items.md` - new file documenting the same finding in full

## Decisions Made

- Kept the RED-then-GREEN-then-SKILL.md sweep in one commit for Task 1, per the plan's explicit instruction, rather than the standard TDD three-commit pattern.
- Did not fix the overlay's `PLUGIN_ROOT` test-path-resolution defect discovered during Task 3 -- ticketed (`gsd-beads-2e2`) and logged instead, since it predates this plan, is unrelated to Task 1/2's edits, and is not in Task 3's declared `<files>` (`.gsd-capabilities.json` only).

## Deviations from Plan

### Auto-fixed Issues

None -- Task 1 and Task 2 executed exactly as specified; no Rule 1/2/3 fixes were needed.

### Documented (not auto-fixed) finding

**1. [Out-of-scope discovery, ticketed] Overlay-tree suite run diverges from plugin-tree run**
- **Found during:** Task 3's `diff -rq` + both-trees suite comparison
- **Issue:** Task 3's acceptance criteria expected `python3 -m unittest discover -s tests -t tests` to report the same `N` and `OK` from both the plugin tree and the runtime overlay. The plugin tree reports `Ran 252 tests`, `OK`. The overlay reports `Ran 252 tests`, `FAILED (failures=12, errors=2)`. All 14 failures/errors are confined to three test classes (`TestLifecycleDispatchHook`, `TestShipPreGenericDispatch`, `TestLifecycleDispatchPointsAgreeWithHook`) whose `PLUGIN_ROOT = Path(__file__).resolve().parents[4]` resolves to `plugins/beads-lifecycle/` (which has a `hooks/` sibling) from the plugin tree but to the repo worktree root (which does not) from the overlay -- the overlay only ever vendors the `capabilities/beads` subtree, never `hooks/`.
- **Evidence this is pre-existing, not caused by this plan:** `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/` is byte-silent both before and after Task 3's re-sync -- the two trees hold identical file content, so this is a path-resolution bug in three gh-2/17-02-vintage test classes, not a content-sync gap. None of the failing classes were touched by Task 1 or Task 2.
- **Action taken:** Filed `gsd-beads-2e2` (P2 bug) with full reproduction and fix-direction notes. Logged to `.planning/WINDOWS.md` (kind `unmet-truth`, phase 18) and to a new `deferred-items.md` in this phase directory. Not fixed -- fixing would require editing `test_sync.py` (outside Task 3's declared `<files>: .gsd-capabilities.json`) or changing what the capability vendors into the overlay (an architectural change to the vendoring manifest, Rule 4 territory).
- **Files modified for the finding:** `.planning/WINDOWS.md`, `.planning/phases/18-address-tech-debt-patch-check-doc-accuracy-changelog/deferred-items.md`
- **Not committed as part of:** the `.gsd-capabilities.json` re-sync itself, which succeeded on its own terms (diff silent, plugin-tree suite green at 252/OK, matching the plan-level `must_haves`).

---

**Total deviations:** 0 auto-fixed, 1 documented-and-ticketed out-of-scope discovery.
**Impact on plan:** None on this plan's must_haves (all of D-03.1, D-03.2, D-01, D-02, plugin-tree suite-green, and diff-silence are met). The overlay test-fixture divergence is a separate, pre-existing, now-tracked defect that does not block this plan's own deliverables.

## Issues Encountered

None beyond the documented finding above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `17-REVIEW.md` WR-01 and WR-02 are both closed by this plan.
- `gsd-beads-2e2` is now open in `bd` and should be picked up as its own task/quick-task when convenient -- not a blocker for Phase 18's remaining plan (18-04).
- The runtime overlay is confirmed byte-identical to the tracked source; the hook executes the exact code this plan's tests verify.

---
*Phase: 18-address-tech-debt-patch-check-doc-accuracy-changelog*
*Completed: 2026-08-20*

## Self-Check: PASSED

- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
- FOUND: .planning/phases/18-address-tech-debt-patch-check-doc-accuracy-changelog/deferred-items.md
- FOUND: commit eab4221 (Task 1)
- FOUND: commit 60ad910 (Task 2)
- FOUND: commit 0682869 (Task 3)
