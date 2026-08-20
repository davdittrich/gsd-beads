---
phase: 17-config-code-truth
plan: 02
subsystem: beads-lifecycle-sync
tags: [lifecycle-dispatch, native-dispatch-probe, truth-03, sync-mode, gsd-core-3687]
requires:
  - phase: 17-config-code-truth
    provides: "capability.json at 0.4.0 with a proven byte-identical runtime mirror (17-01)"
provides:
  - "check_native_step_dispatch(point, workflow_path_override=None) -- read-only, fail-open, region-scoped probe for gsd-core PR #3687's native kind == \"step\" dispatch at plan:post/verify:post"
  - "read_sync_mode(project_root) -- beads.sync_mode accessor, default \"authoritative\""
  - "lifecycle_dispatch's plan:post/verify:post branches stand down when native dispatch is detected; plan:pre/execute:wave:pre/execute:wave:post stay unconditional"
  - "main()'s create-issues CLI dispatch computes allow_strip from beads.sync_mode (mirror withholds the strip); lifecycle_dispatch's plan:post keeps the literal allow_strip=False, ungated by config (D-03)"
affects:
  - "lifecycle_dispatch"
  - "create_issues"
  - "main (create-issues CLI dispatch)"
actuals:
  tokens: 10241
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns:
    - "Region-scoped, fence-aware workflow-file probing (D-05): anchor on the point's own render-hooks <point> --raw call, scope to the earlier of the next non-fenced level-two heading or 120 lines past the anchor, exclude capId==/ref.skill== qualified lines -- a whole-file scan is a verified false positive on both shipped 1.11.0 workflow files"
    - "Opposite-polarity patch-checker sibling: check_native_step_dispatch asks \"does upstream now do this natively\" (present is good) versus check_shipmd_patch/check_execute_plan_patch's \"is our patch still here\" (missing is bad) -- kept as a separate function rather than a shared table"
    - "D-06 principal-strength asymmetry: an explicit CLI dispatch is a stronger principal than a substring-matched PostToolUse hook, so only the CLI path's strip decision is config-governed (beads.sync_mode); the hook path's allow_strip stays a literal False (D-03)"
key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md
key-decisions:
  - "check_native_step_dispatch's own diagnostic prints route to stderr, not stdout (deviation from check_shipmd_patch/check_execute_plan_patch's stdout convention) -- it is called unconditionally at the top of plan:post/verify:post, before either branch knows whether there is anything to do, and a benign not-detected diagnostic must not turn a silent no-op (e.g. no PLAN.md in the phase) into stdout noise a PostToolUse hook promotes into Claude's context"
  - "Fence-parity state for the probe's region scan is computed from line 0 up to the anchor, not reset at the anchor -- the anchor line itself commonly sits inside a ```bash ... ``` block opened before it (the shipped shape), so resetting fence state at the anchor misclassifies the block's own closing fence as an opening one (caught by a dedicated RED test, fixed before GREEN)"
patterns-established:
  - "A native-dispatch probe is read-only, never raises, and every miss (unmapped point, missing/unreadable file, no anchor, no qualifying line) degrades to not-detected -- the only failure direction that keeps the existing hook path working (D-05)"
requirements-completed: [TRUTH-03]
coverage:
  - id: D1
    description: "On a gsd-core install whose plan-phase.md/verify-work.md plan:post/verify:post region carries no generic kind == \"step\" dispatch arm (the shipped 1.11.0 shape), lifecycle-dispatch still creates bd issues / regenerates BEADS.md exactly as before"
    requirement: "TRUTH-03"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestNativeStepDispatchProbeAgainstInstalledTree (both points, real installed tree)"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNativeGate.test_plan_post_dispatches_as_today_when_native_dispatch_not_detected"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNativeGate.test_verify_post_dispatches_as_today_when_native_dispatch_not_detected"
        status: pass
      - kind: command
        ref: "live scratch fixture: python3 scripts/sync.py lifecycle-dispatch plan:post creates a real bd epic+task and rewrites beads_epic/<beads-id> into PLAN.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "On an install whose region DOES contain a generic unqualified kind == \"step\" arm, the hook performs no sync and prints a stderr-only skip notice naming the exact workflow file path probed"
    requirement: "TRUTH-03"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestNativeStepDispatchProbe.test_unqualified_generic_step_arm_in_region_is_detected"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNativeGate.test_plan_post_skips_create_issues_when_native_dispatch_detected"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNativeGate.test_verify_post_skips_regenerate_when_native_dispatch_detected"
        status: pass
    human_judgment: false
  - id: D3
    description: "Region scoping (not whole-file) correctly classifies both shipped 1.11.0 false-positive shapes as not-detected: plan-phase.md's three out-of-region kind == \"step\" mentions, and verify-work.md's in-region ref.skill-qualified one"
    requirement: "TRUTH-03"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestNativeStepDispatchProbe.test_shipped_1_11_0_plan_phase_shape_is_not_detected"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestNativeStepDispatchProbe.test_shipped_1_11_0_verify_work_shape_is_not_detected"
        status: pass
    human_judgment: false
  - id: D4
    description: "plan:pre, execute:wave:pre and execute:wave:post dispatch unconditionally regardless of probe result -- no upstream work covers them anywhere"
    requirement: "TRUTH-03"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNativeGate.test_plan_pre_dispatches_regardless_of_probe_result"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNativeGate.test_execute_wave_pre_dispatches_regardless_of_probe_result"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNativeGate.test_execute_wave_post_dispatches_regardless_of_probe_result"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchPointsAgreeWithHook.test_five_points_same_order_in_both_places"
        status: pass
    human_judgment: false
  - id: D5
    description: "create-issues CLI computes allow_strip from beads.sync_mode (mirror withholds, authoritative/no-config/retired-off strip as before); lifecycle_dispatch's plan:post keeps the literal allow_strip=False, never consulting config"
    requirement: "TRUTH-03"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestReadSyncMode (default/explicit/malformed-config coverage)"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestCreateIssuesCliSyncModeGate (mirror/authoritative/no-config/retired-off arms)"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNeverConsultsSyncMode.test_authoritative_config_still_leaves_task_bodies_intact_via_hook"
        status: pass
      - kind: command
        ref: "sed -n '/elif point == \"plan:post\"/,/elif point == \"execute:wave:pre\"/p' scripts/sync.py | grep -c 'allow_strip=False' -> 1"
        status: pass
      - kind: command
        ref: "grep -c 'add_argument' scripts/sync.py unchanged (13 before and after Task 3) -- no CLI flag added"
        status: pass
    human_judgment: false
  - id: D6
    description: "Every added code path is fail-open (missing/unreadable workflow file, no anchor, no region match, or an unexpected exception all degrade to not-detected / a 0 return, never a crash or a wrongly-suppressed dispatch); the probe is idempotent (pure, read-only, no module or filesystem state mutated)"
    requirement: "TRUTH-03"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestNativeStepDispatchProbe (missing file, unreadable file, no anchor, region-ends-before-arm)"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestLifecycleDispatchNativeGate.test_lifecycle_dispatch_returns_zero_for_every_point_when_probe_raises"
        status: pass
    human_judgment: true
    rationale: "Idempotency is not exercised by a dedicated 'call twice, compare' test -- it follows from the implementation being purely read-only (a single Path.read_text, no writes anywhere in the function, no mutable module-level state consulted or set) and from the same fixture-driven tests passing deterministically across the suite's repeated collection/execution. Judged correct by code inspection rather than pinned by an explicit repeat-call assertion."
duration: ~20min
completed: 2026-08-20
status: complete
---

# Phase 17 Plan 02: lifecycle-dispatch Hook Version-Skew Safety Summary

**A region-scoped, fence-aware, fail-open probe (`check_native_step_dispatch`) gates `plan:post`/`verify:post` on gsd-core PR #3687's native `kind == "step"` dispatch, and `beads.sync_mode` now governs only the explicit `create-issues` CLI's destructive strip -- the hook path stays permanently non-stripping (D-03).**

## Performance
- **Duration:** ~20min (base commit 02:02:46 -> final task commit 02:22:48, 2026-08-20)
- **Started:** 2026-08-20T02:02:46+02:00 (worktree base)
- **Completed:** 2026-08-20T02:22:48+02:00
- **Tasks:** 3/3
- **Files modified:** 3 (sync.py, test_sync.py, GSD-CORE-PATCH.md)

## Accomplishments
- `check_native_step_dispatch(point, workflow_path_override=None)`: reads the installed
  `plan-phase.md`/`verify-work.md`, anchors on the point's own literal `render-hooks <point> --raw`
  call, scopes to the earlier of the next non-fenced level-two heading or 120 lines past the
  anchor, and reports detected only for an unqualified `kind == "step"` line in that region --
  excluding any line also carrying `capId ==` or `ref.skill ==`. Live-verified on this machine's
  real installed 1.11.0 tree: both `plan:post` and `verify:post` report not-detected, each naming
  the exact absolute path read.
- `lifecycle_dispatch`'s `plan:post` (Task 1) and `verify:post` (Task 2) branches now skip their
  verb and print a stderr-only notice when the probe reports detected; every other outcome
  dispatches exactly as before. `plan:pre`/`execute:wave:pre`/`execute:wave:post` are unconditional
  by design and regression-pinned against a probe stubbed to always report detected.
- A whole-file `kind == "step"` grep is a *verified* false positive on both shipped 1.11.0 files --
  pinned by fixtures reproducing `plan-phase.md`'s three out-of-region mentions and
  `verify-work.md`'s in-region `ref.skill`-qualified one (the latter fixture also asserts a naive
  scan WOULD match, documenting exactly what region scoping prevents).
- `read_sync_mode(project_root)` (Task 3) added beside `read_epic_per`/`read_beads_enabled`;
  `main()`'s `create-issues` CLI dispatch now resolves `allow_strip` from
  `beads.sync_mode != "mirror"` (authoritative default, no-config, and the retired `off` value all
  behave exactly as before this task -- only `mirror` changes anything). No CLI flag added
  (`add_argument` count unchanged: 13 before and after). `lifecycle_dispatch`'s `plan:post` keeps
  the literal `allow_strip=False`, untouched by config -- the D-03 answer to the v1.3.0 incident.
- `GSD-CORE-PATCH.md` gained a new "Probe (not a patch)" section: what the probe looks for, why
  it is region-scoped rather than whole-file, its fail-open contract, and its revert condition
  (retire the gate branches once a *released* gsd-core reports detected for both points; the hook
  itself cannot be deleted while `execute:wave:pre`/`execute:wave:post` remain uncovered).

## Task Commits
1. **Task 1 RED: failing tests for the native-step-dispatch probe** - `a80aeb8`
2. **Task 1 GREEN: gate plan:post on the probe** - `2e788ea`
3. **Task 2 RED: failing test for the verify:post gate** - `30e0ad6`
4. **Task 2 GREEN: gate verify:post on the probe** - `45146ac`
5. **Task 3 RED: failing tests for D-06 sync_mode strip gating** - `4bef541`
6. **Task 3 GREEN: wire beads.sync_mode to the native create-issues strip** - `ca8cb36`

**Plan metadata:** committed separately after this SUMMARY.

## Files Created/Modified
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` - `check_native_step_dispatch`,
  `read_sync_mode`, the `plan:post`/`verify:post` gate branches in `lifecycle_dispatch`, and the
  config-governed `allow_strip` at the `create-issues` CLI dispatch site
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` -
  `TestNativeStepDispatchProbe`, `TestNativeStepDispatchProbeAgainstInstalledTree`,
  `TestLifecycleDispatchNativeGate`, `TestLifecycleDispatchPointsAgreeWithHook`,
  `TestReadSyncMode`, `TestCreateIssuesCliSyncModeGate`, `TestLifecycleDispatchNeverConsultsSyncMode`
  (28 new test methods total)
- `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` - new "Probe (not a patch)"
  section documenting the mechanism, its fail-open contract, and its revert condition

## Decisions Made
- `check_native_step_dispatch`'s own diagnostic prints route to stderr, not stdout, deliberately
  breaking from `check_shipmd_patch`/`check_execute_plan_patch`'s stdout convention -- see
  key-decisions above for the reasoning (a benign not-detected diagnostic must not leak into the
  hook's `additionalContext` on a silent no-op).
- Fence-parity for the region scan is computed from the top of the file up to the anchor, not reset
  at the anchor -- caught live by a RED test (`test_region_ends_at_heading_before_a_later_step_arm_is_not_detected`
  failed with `1 != 0` before the fix) reproducing the real shape where the anchor line sits inside
  a `` ```bash ... ``` `` block opened before it.
- Split each task into its own RED-then-GREEN commit pair (6 commits for 3 tasks) rather than one
  commit per task, per CLAUDE.md's mandatory TDD discipline (`workflow.tdd_mode: true`) -- verified
  live by reverting the already-drafted Task 1 implementation via `git checkout --` on the single
  file before writing its tests, confirming genuine RED (9/9 AttributeError failures), then
  reapplying.

## Deviations from Plan

None beyond the plan's own scope. All three tasks (`gsd-beads-u67.4`, `.5`, `.6`) executed exactly
as specified in their `bd show` content, including every BINDING cross-AI review disposition
(codex HIGH totality-of-probe acceptance criterion, codex MEDIUM retired-`off`-value fixture).

## Issues Encountered

One implementation bug caught during Task 1's own RED-GREEN-verify loop before the task commit:
the region-scan's fence-parity tracking initially reset `in_fence = False` at the anchor line
itself, which misclassified the closing `` ``` `` of a fenced block opened *before* the anchor (the
real shipped shape) as an opening fence -- causing the region to terminate one line early and a
step arm placed intentionally out-of-region to be missed for the wrong reason (a boundary bug, not
the intended "not detected because out of region" behavior). Fixed by computing fence parity from
line 0 up to the anchor before starting the region scan; the specific RED test that caught it
(`test_region_ends_at_heading_before_a_later_step_arm_is_not_detected`) stayed in the suite as the
regression pin.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 17-03 (TRUTH-01). The `beads.sync_mode` accessor this plan introduces
(`read_sync_mode`) is a two-line prerequisite of 17-03's own scope, per this plan's objective's
cross-decision note -- 17-03 owns the `capability.json` declaration change and the doc sweep;
nothing here needs revisiting.

---
*Phase: 17-config-code-truth*
*Completed: 2026-08-20*
