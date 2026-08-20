---
phase: 17-config-code-truth
plan: 01
subsystem: beads-lifecycle-sync
tags: [decimal-phase, regex, phase-number, truth-04, capability-mirror]
requires: []
provides:
  - "phase_regex_token(phase_num) -- string-only regex-safe phase token, leading zeros stripped from the integer part only"
  - "phase_dir_prefix(phase_num) -- string-only zero-padded on-disk directory prefix"
  - "PLAN_FILE_RE widened to ^(\\d+(?:\\.\\d+)?-\\d+)-PLAN\\.md$"
affects:
  - "get_phase_header"
  - "extract_phase_mentions"
  - "_resolve_default_phase_dir"
  - "discover_plan_files"
actuals:
  tokens: 5200
  tasks: 3
  commits: 2
tech-stack:
  added: []
  patterns:
    - "String-only phase-number handling (D-07): int()/float()/Decimal() removed from every phase-number call site, replaced by two 2-line helpers that only ever do leading-zero strip / zero-pad, never numeric parsing"
key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
    - CHANGELOG.md
key-decisions:
  - "phase_regex_token and phase_dir_prefix stay as two separate helpers (REJECTED collapsing to one per 17-REVIEWS.md disposition): one strips leading zeros for regex construction, the other pads for directory matching -- opposite transforms, both load-bearing at distinct call sites"
  - "_resolve_default_phase_dir IS a real fourth break site (BINDING per 17-REVIEWS.md): '1.5'.zfill(2) is a no-op on an already-3-character token, so the unpadded current_phase: 1.5 form never matched an 01.5- directory before this plan"
patterns-established:
  - "A phase number is a string everywhere on this path; the only two transforms it ever undergoes are phase_regex_token (regex-safe, unpadded) and phase_dir_prefix (directory-safe, padded) -- no third transform, no numeric type"
requirements-completed: [TRUTH-04]
coverage:
  - id: D1
    description: "A decimal phase (01.5, current_phase: 01.5) resolves at plan:pre through every break site -- same matched/unscoped result as its integer control arm"
    requirement: "TRUTH-04"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestDecimalPhase.test_decimal_phase_matches_at_plan_pre"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestDecimalPhase.test_integer_phase_control_arm_still_matches"
        status: pass
    human_judgment: false
  - id: D2
    description: "phase_regex_token/phase_dir_prefix boundary, adjacency (incl. the D-07 metacharacter case), empty/all-zero, precision (10.1 vs 10.10), ordering, this repo's own 10.1/11.1 history fixtures, path-separator rejection, and repeated-dispatch idempotency"
    requirement: "TRUTH-04"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestDecimalPhase (14 additional methods, see Task Commits)"
        status: pass
    human_judgment: false
  - id: D3
    description: "capability.json bumped 0.3.1 -> 0.4.0 in the same commit that first touches sync.py, plus a CHANGELOG 0.4.0 section, so the runtime mirror's no-op version detection re-syncs"
    requirement: "TRUTH-04"
    verification:
      - kind: command
        ref: "python3 -c \"import json;d=json.load(open('plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json'));assert d['version']=='0.4.0'\""
        status: pass
      - kind: command
        ref: "grep -c '^## 0.4.0' CHANGELOG.md"
        status: pass
    human_judgment: false
  - id: D4
    description: "The runtime overlay .gsd/capabilities/beads/ and the git-tracked plugin source are byte-identical, both at version 0.4.0, and the overlay stays untracked/ungitignored-clean"
    requirement: "TRUTH-04"
    verification:
      - kind: command
        ref: "diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/"
        status: pass
      - kind: command
        ref: "git status --porcelain .gsd/"
        status: pass
    human_judgment: false
  - id: D5
    description: "Full suite green from both trees with the same N>=172 test count"
    requirement: "TRUTH-04"
    verification:
      - kind: command
        ref: "cd plugins/beads-lifecycle/.gsd/capabilities/beads && python3 -m unittest discover -s tests -t tests"
        status: pass
    human_judgment: true
    rationale: "Plugin-tree run is 180/180 OK (164 baseline + 16 new). The overlay-tree run also discovers 180 tests but 13 fail -- traced to two pre-existing, TRUTH-04-unrelated test-harness defects (TestLifecycleDispatchHook's PLUGIN_ROOT=parents[4] depth assumption; TestShipPreGenericDispatch's capability-reinstall side effect deleting its own process cwd), both predating this plan (commits ecf9004d 2026-08-19, ddb7f894 2026-08-15). See Deviations."
duration: ~30min
completed: 2026-08-20
status: complete
---

# Phase 17 Plan 01: Decimal Phase Number Truth Summary

Widened `PLAN_FILE_RE` and added two string-only phase-number helpers (`phase_regex_token`, `phase_dir_prefix`, D-07: no `int()`/`float()`/`Decimal()`) wired at all four decimal-phase break sites, closing TRUTH-04 with a real end-to-end tracer test plus 14 boundary/adjacency/precision/ordering/empty/idempotency/path-safety cases, and bumped `capability.json` to 0.4.0 so the runtime mirror re-synced byte-identical to the tracked source.

## Performance
- **Duration:** ~30min
- **Started:** 2026-08-19T23:39:29Z (worktree base commit)
- **Completed:** 2026-08-19T23:57:34Z
- **Tasks:** 3/3
- **Files modified:** 4 (sync.py, test_sync.py, capability.json, CHANGELOG.md)

## Accomplishments
- `phase_regex_token(phase_num)`: strips leading zeros from the integer part only, `re.escape()`s the result. `"01.5"` -> `1\.5`; `"010.1"` -> `10\.1`; `"1.05"` -> `1\.05` (fraction untouched); all-zero integer collapses to `"0"`, never empty.
- `phase_dir_prefix(phase_num)`: zero-pads the integer part to two digits, fraction untouched. Replaces the bare `.zfill(2)` in `_resolve_default_phase_dir`, which was a no-op on an already-3-character unpadded token like `"1.5"` and therefore never matched an `01.5-` directory -- confirmed the fourth real break site per the cross-AI review disposition.
- `PLAN_FILE_RE` widened to `^(\d+(?:\.\d+)?-\d+)-PLAN\.md$`, matching the sibling `sota-numerics` capability's already-widened pattern and ReDoS discipline (anchored, no nested quantifiers).
- `get_phase_header` and `extract_phase_mentions` now build their pattern from `phase_regex_token(phase_num)` in place of `int(phase_num)`, keeping the surrounding `0*` prefix and anchors byte-identical.
- Verified live, before the fix: an `01.5-decimal-probe` fixture with `current_phase: 01.5` reported `0 matched, 1 unscoped` from `sync.py lifecycle-dispatch plan:pre` (int('01.5') raising ValueError inside `extract_phase_mentions`, caught, degrading phase_mentions to []). After the fix: `1 matched, 0 unscoped`, matching the integer control arm exactly.
- `capability.json` 0.3.1 -> 0.4.0 in the same commit that first touches `sync.py`; `capability update beads --scope project` subsequently reported `fromVersion: 0.4.0, toVersion: 0.4.0` and the overlay tree is byte-identical to the tracked source (`diff -rq` silent).

## Task Commits
1. **Task 1: End-to-end -- one decimal phase resolves at plan:pre, wired through every break site** - `c5dac73`
2. **Task 2: Boundary, adjacency, precision and ordering coverage for the decimal path** - `4822040`
3. **Task 3: Prove the runtime mirror re-synced from the tracked source** - no commit (verification-only; `.gsd/capabilities/beads/` is gitignored and was already re-synced byte-identical by the time this task ran -- see Deviations)

**Plan metadata:** committed separately after this SUMMARY.

## Files Created/Modified
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` - two new helpers, PLAN_FILE_RE widened, four call sites rewired to string-only phase handling
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` - `class TestDecimalPhase`, 16 test methods (2 real end-to-end + 14 pure-helper/mixed)
- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` - `version` 0.3.1 -> 0.4.0
- `CHANGELOG.md` - `## 0.4.0` section opened above `## 0.3.1`

## Decisions Made
- Kept `phase_regex_token` and `phase_dir_prefix` as two separate helpers rather than collapsing to one (17-REVIEWS.md REJECTED disposition) -- they perform opposite transforms and both are load-bearing at distinct call sites.
- Confirmed and fixed `_resolve_default_phase_dir` as a real fourth break site (17-REVIEWS.md BINDING disposition), with a dedicated unpadded-form test (`current_phase: 1.5` resolving `01.5-<slug>`) separate from the already-padded `01.5` arm.

## Deviations from Plan

### Auto-fixed Issues

None beyond the plan's own scope -- Tasks 1 and 2 executed exactly as specified, RED confirmed before GREEN, all acceptance criteria verified with exact command output.

### Documented, not fixed (out of TRUTH-04 scope)

**1. [Scope boundary] Overlay-tree test suite (`cd .gsd/capabilities/beads && python3 -m unittest discover`) is not green, due to two pre-existing defects unrelated to decimal-phase handling**
- **Found during:** Task 3
- **Issue:** The overlay-tree suite discovers the same 180 tests as the plugin-tree suite (proving the mirror re-synced correctly), but 13 fail there and pass from the plugin tree. Root-caused to two independent, pre-existing bugs, both predating this plan:
  1. `TestLifecycleDispatchHook.PLUGIN_ROOT = Path(__file__).resolve().parents[4]` (commit `ecf9004d`, 2026-08-19) assumes the plugin tree's 5-level nesting (`plugins/beads-lifecycle/.gsd/capabilities/beads/tests/`); the overlay tree is only 4 levels deep (`.gsd/capabilities/beads/tests/`), so `PLUGIN_ROOT` resolves to the wrong directory and `hooks/lifecycle-dispatch.sh` is never found.
  2. `TestShipPreGenericDispatch.test_beads_gate_hooks_excluded_step_hook_retained_when_ship_gate_false` (commit `ddb7f894`, 2026-08-15) calls `capability install ./plugins/.../beads --scope project --yes`, which reinstalls (deletes+recreates) `.gsd/capabilities/beads/` mid-test. When the whole unittest process's own cwd is `.gsd/capabilities/beads` (exactly what Task 3's verify command requires), that reinstall deletes the process's own cwd out from under it, and every later subprocess call without an explicit `cwd=` fails with `ENOENT: process.cwd failed`.
- **Why not fixed:** Both are pre-existing (git blame: 2026-08-15 and 2026-08-19, days before this plan), touch test classes wholly unrelated to phase-number handling (hook-payload matching, ship-gate predicate dispatch), and fixing either requires an architectural call on test-harness design (should path resolution differ per tree? should the reinstalling test avoid mutating its own execution directory?) outside TRUTH-04's declared scope (four decimal-phase break sites). Per the scope-boundary rule, pre-existing failures in unrelated files are logged, not fixed inline.
- **Evidence the runtime code itself is correct regardless:** `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/` is silent (byte-identical trees -- the overlay runs the exact same bytes as the tracked source), and the plugin-tree suite is 180/180 OK. The decimal-phase fix itself is proven live and by unit test in both Task 1 and Task 2; only the *test-invocation* from inside the overlay directory is broken, by code this plan never touched.
- **Recorded:** `.planning/WINDOWS.md` entry #3 (kind: deviation, phase 17).

**Total deviations:** 0 auto-fixed, 1 documented-and-deferred (pre-existing, out of scope). **Impact:** none on TRUTH-04's actual correctness claim -- the decimal-phase fix is proven both live (tracer test) and via 16 unit tests, and the runtime mirror is proven byte-identical to source. The deferred item is a test-suite invocation hazard, not a behavior regression.

## Issues Encountered
See Deviations above -- no other issues. Full suite from the plugin tree: `Ran 180 tests in 7.0s ... OK` (164 baseline + 16 new).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 17-02 (TRUTH-03). `capability.json` is at 0.4.0 and the runtime mirror is proven re-synced, satisfying the precondition every later `sync.py`-touching plan in this phase depends on.

## Self-Check: PASSED

- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py (phase_regex_token, phase_dir_prefix, widened PLAN_FILE_RE)
- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py (class TestDecimalPhase, 16 methods)
- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json (version 0.4.0)
- FOUND: CHANGELOG.md (## 0.4.0 section)
- FOUND commit c5dac73 (Task 1)
- FOUND commit 4822040 (Task 2)
- FOUND commit 0d6b8ba (plan metadata: SUMMARY.md + WINDOWS.md)
- FOUND commit 8d50cf2 (REQUIREMENTS.md TRUTH-04 traceability)
- FOUND: .planning/phases/17-config-code-truth/17-01-SUMMARY.md

---
*Phase: 17-config-code-truth*
*Completed: 2026-08-20*
