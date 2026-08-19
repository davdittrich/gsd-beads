---
phase: 16-beads-issue-content-parity
plan: 03
subsystem: infra
tags: [beads, bd, sync.py, gsd-core-capability, python-stdlib, D-01, D-03, D-05, D-07]

# Dependency graph
requires:
  - phase: 16-beads-issue-content-parity
    provides: "plan 16-01's parse_plan()/TASK_TYPE_RE/per-task content-field regexes -- this plan's strip_task_bodies decodes task type from the same regex and removes the same fields D-06 taught bd create to read"
provides:
  - "EXECUTE_PLAN_PATCH_MARKER + check_execute_plan_patch() -- read-only detector for the machine-local execute-plan.md bd-task-read patch (D-05), dispatched independently of the patch itself"
  - "strip_task_bodies(text, stripped_ids) -- turns a newly-synced auto/tracer task block into name+beads-id+files+pointer once its content is confirmed in bd (D-01)"
  - "create_issues' rewrite path gated: strips only newly-created task ids, only when check_execute_plan_patch() == 0"
affects: [16-04, gsd-executor via a future execute-plan.md patch, any phase synced with the patch installed]

# Actuals (#2632)
actuals:
  tokens: 6023
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Detector-clone pattern: check_execute_plan_patch is check_shipmd_patch's exact shape retargeted at a different file, same three-case return/print contract, same WR-03 single-runtime-home wording discipline"
    - "Reverse-match-order splice for destructive plan rewrites: strip_task_bodies iterates TASK_RE matches in reverse start-position order and splices against the original text's offsets, the same technique rewrite_plan already used for insertions -- now proven for removals too"
    - "Fail-toward-keeping-content: an unrecognized/absent task type is never treated as strippable; the type check is an allowlist (auto, tracer only), not a denylist"
    - "Verify-before-trust gate: the strip is re-evaluated via a live check_execute_plan_patch() call on every sync, never cached or config-flagged, so a machine that silently lost the patch falls back to leaving content in place rather than assuming a stale intention"

key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py

key-decisions:
  - "Edited the git-tracked plugin source (plugins/beads-lifecycle/.gsd/capabilities/beads/) instead of the plan-specified .gsd/capabilities/beads/ path -- same gitignored runtime-install mirror issue documented in 16-01-SUMMARY.md and 16-02-SUMMARY.md. Confirmed via git ls-files before the first edit."
  - "TASK_POINTER_PREFIX (a fixed literal, not the whole pointer line) is what idempotency checks against, since the suffix varies per beads-id -- a second strip_task_bodies pass recognizes the prefix and does not stack a second pointer comment"
  - "Blank-line collapse after element removal uses one whitespace-aware regex (`[ \\t]*\\n(?:[ \\t]*\\n)+` -> `\\n`) scoped to a single already-isolated task block, not the whole plan text -- safe because by the time it runs, every removable multi-line body (behavior/acceptance_criteria/etc.) has already been deleted, so nothing but structural indentation whitespace remains to collapse"
  - "create_issues only calls check_execute_plan_patch() when there is at least one newly-created id to strip (task_updates non-empty) -- avoids an unnecessary machine-local file read and printed notice on every sync that adds zero new tasks (e.g. a divergence-only orphan-close pass)"

patterns-established:
  - "Pattern: a destructive plan-rewrite step earns its removal permission from a two-part gate -- (1) the id must be in the same run's task_updates (bd create returned 0 for it this run), (2) a live re-check of the read-path patch must return 0 -- neither alone is sufficient"

requirements-completed: [D-01, D-03, D-05, D-07]

coverage:
  - id: D1
    description: "check_execute_plan_patch answers present/absent/file-missing for the machine-local execute-plan.md patch, read-only, from a lifecycle point independent of the patch"
    requirement: "D-05"
    verification:
      - kind: unit
        ref: "test_sync.py#TestCheckExecutePlanPatch (5 tests: present, marker-absent, file-absent, never-writes, CLI-dispatch)"
        status: pass
      - kind: integration
        ref: "live: `sync.py check-execute-plan-patch` on this machine (patch not yet installed, correctly exits 1 naming the probed path)"
        status: pass
    human_judgment: false
  - id: D2
    description: "A synced auto/tracer task block whose issue was created this run becomes name+beads-id+files+one pointer comment; every content element is gone"
    requirement: "D-01"
    verification:
      - kind: unit
        ref: "test_sync.py#TestStripTaskBodies.test_strippable_auto_task_loses_content_elements, test_strippable_auto_task_keeps_identity_and_routing_elements, test_strippable_tracer_task_is_stripped_like_auto, test_stripped_block_gains_exactly_one_pointer_comment"
        status: pass
    human_judgment: true
    rationale: "See Before/After Evidence below -- a rendered before/after pair, not just an assertion, is the clearest proof D-01's shape is what was asked for"
  - id: D3
    description: "checkpoint:decision and checkpoint:human-verify task blocks are byte-identical after strip_task_bodies, even when their id is passed in stripped_ids"
    requirement: "D-03"
    verification:
      - kind: unit
        ref: "test_sync.py#TestStripTaskBodies.test_checkpoint_decision_task_is_byte_identical, test_checkpoint_human_verify_task_is_byte_identical, test_no_type_attribute_task_is_byte_identical"
        status: pass
    human_judgment: false
  - id: D4
    description: "Nothing is stripped without the read-path patch installed (create_issues-level gate), and a task whose issue predates this run is never stripped even if its type qualifies"
    requirement: "D-05, D-07"
    verification:
      - kind: unit
        ref: "test_sync.py#TestCreateIssuesStripGate (patch-present strips, patch-absent leaves content intact); TestStripTaskBodies.test_pre_existing_task_not_in_stripped_set_is_byte_identical"
        status: pass
    human_judgment: false
  - id: D5
    description: "The strip is idempotent and never touches plan-level content (frontmatter, objective, context, verification, success_criteria) or any other phase's PLAN.md files"
    requirement: "D-01, D-07"
    verification:
      - kind: unit
        ref: "test_sync.py#TestStripTaskBodies.test_idempotent_second_pass_is_byte_identical_to_first, test_plan_level_sections_are_byte_identical"
        status: pass
      - kind: integration
        ref: "live: `git status --porcelain .planning/phases/` after the full 125-test suite run shows zero modifications outside the two pre-existing untracked Phase 14/16 artifact files"
        status: pass
    human_judgment: false

duration: ~10min
completed: 2026-08-19
status: complete
---

# Phase 16 Plan 03: D-01 Sync-Side Inversion (check_execute_plan_patch + strip_task_bodies) Summary

**`sync.py` now proves the machine-local `execute-plan.md` bd-task-read patch is present before doing the one truly destructive thing this capability has ever done: turning a synced `auto`/`tracer` task block into a name+beads-id+files+pointer, while `checkpoint:*` blocks and pre-existing tasks stay byte-identical.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-08-18T23:50:36Z (STATE.md, immediately after 16-02)
- **Completed:** 2026-08-18T23:58:45Z
- **Tasks:** 2
- **Files modified:** 2 (`sync.py`, `test_sync.py`, both under `plugins/beads-lifecycle/.gsd/capabilities/beads/`)

## Accomplishments

- `EXECUTE_PLAN_PATCH_MARKER` module-level constant, sibling to `SHIP_MD_PATCH_MARKER`, holding
  the literal `<!-- gsd-beads-patch:execute-plan-bd-task-read v1 -->`.
- `check_execute_plan_patch(execute_plan_path_override=None)`, a line-for-line clone of
  `check_shipmd_patch`'s structure (`CLAUDE_CONFIG_DIR`-with-`~/.claude`-default resolution,
  exists-check-then-substring-check-then-two-branch-print, same 0/1 return codes, read-only),
  retargeted at `gsd-core/workflows/execute-plan.md`. Docstring records the independence
  requirement: it must be dispatched from a lifecycle point gsd-core reaches natively (plan 16-04
  wires it at `plan:pre`), never from inside the patch it checks.
- `check-execute-plan-patch` subcommand + `--execute-plan-path` override flag, registered in
  `main()` exactly like `check-shipmd-patch`.
- `strip_task_bodies(text, stripped_ids)`, placed immediately after `rewrite_plan`. Walks
  `TASK_RE.finditer(text)`, applies replacements in reverse match order (the same offset-safety
  technique `rewrite_plan` uses for insertions), and for each block requires two conditions before
  touching it: `type` is exactly `auto` or `tracer`, and `<beads-id>` is in `stripped_ids`. Every
  other shape -- every `checkpoint:*` variant and a block with no `type` attribute at all -- is
  skipped untouched. A stripped block loses `read_first`, `precondition`, `behavior`, `action`,
  `verify`, `acceptance_criteria` and `done` (reusing plan 16-01's per-field regexes), keeps
  `name`/`beads-id`/`files`, has its blank lines collapsed, and gains exactly one fixed-shape
  pointer comment naming the beads id.
- Wired into `create_issues`: after `rewrite_plan` inserts beads-ids, the newly-created id set
  (`task_updates`) is passed to `strip_task_bodies` only when `check_execute_plan_patch() == 0`;
  otherwise one notice line explains content was left in place because the patch is not detected.
- 17 new tests: `TestCheckExecutePlanPatch` (5), `TestStripTaskBodies` (10, an inline six-task-shape
  fixture covering every behavior in the plan's `<behavior>` block), `TestCreateIssuesStripGate`
  (2, `check_execute_plan_patch` mocked to 0 and to 1). Full suite: 125 tests, 0 failures, 0 errors
  -- 108 (16-02's baseline) + 5 (Task 1) = 113, then + 10 + 2 (Task 2) = 125.

## Task Commits

Each task was committed atomically:

1. **Task 1: check_execute_plan_patch -- an independent detector for the read-path patch** -
   `33d7c34` (feat)
2. **Task 2: strip_task_bodies -- PLAN.md becomes a pointer for auto and tracer tasks** -
   `82f953f` (feat)

**Plan metadata:** committed alongside this SUMMARY (see final commit).

## Files Created/Modified

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` -- `EXECUTE_PLAN_PATCH_MARKER`,
  `check_execute_plan_patch()`, `check-execute-plan-patch` subparser + dispatch (Task 1);
  `_STRIP_ELEMENT_RES`, `TASK_POINTER_PREFIX`, `strip_task_bodies()`, gated wiring in
  `create_issues` (Task 2)
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` -- `TestCheckExecutePlanPatch`
  (5 tests), `TestStripTaskBodies` (10 tests), `TestCreateIssuesStripGate` (2 tests)

## Decisions Made

See `key-decisions` in frontmatter -- path deviation (same footgun as 16-01/16-02), the
`TASK_POINTER_PREFIX`-not-whole-line idempotency check, the blank-line-collapse scope, and the
task_updates-non-empty guard around the `check_execute_plan_patch()` call.

## Before/After Evidence (D-01 / D-03)

Generated live from `strip_task_bodies` against this plan's own test fixture
(`test_sync._strip_test_plan_text`), not hand-transcribed:

**Before (auto task, `fixture-1` in `stripped_ids`):**

```xml
<task type="auto">
  <name>Task 1: Strippable auto task</name>
  <beads-id>fixture-1</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <precondition>`bd` is on PATH.</precondition>
  <behavior>
    - does the thing
  </behavior>
  <action>Implement the thing.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>The thing is implemented.</done>
</task>
```

**After (`strip_task_bodies(text, {"fixture-1", ...})`):**

```xml
<task type="auto">
  <name>Task 1: Strippable auto task</name>
  <beads-id>fixture-1</beads-id>
  <files>src/example.py</files>
  <!-- beads: content synced to bd -- see `bd show fixture-1` -->
</task>
```

**checkpoint:decision block, same call, same `stripped_ids` set containing its id (`fixture-4`) --
byte-identical, D-03 exclusion holding even when the id would otherwise qualify:**

```xml
<task type="checkpoint:decision" gate="blocking">
  <name>Task 4: Approve the approach</name>
  <beads-id>fixture-4</beads-id>
  <decision>Pick an approach.</decision>
  <context>
    Some context here.
  </context>
  <options>
    <option id="a">
      <name>Option A</name>
    </option>
  </options>
  <selection-prompt>Which option?</selection-prompt>
</task>
```

`before_cp == after_cp` asserted `True` in the same run (script output; also covered by
`test_checkpoint_decision_task_is_byte_identical`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Edited `plugins/beads-lifecycle/.gsd/capabilities/beads/` instead of the plan's `.gsd/capabilities/beads/`**
- **Found during:** Task setup, before any edit (pre-empted via 16-01/16-02's documented root cause
  and this plan's own `<path_note>`)
- **Issue:** `.gsd/capabilities/beads/scripts/sync.py` etc. is a gitignored runtime-install mirror
  of the tracked `plugins/beads-lifecycle/.gsd/capabilities/beads/` source; edits at the mirror path
  are invisible to git and get silently reverted on the next capability re-sync.
- **Fix:** All edits made directly against
  `plugins/beads-lifecycle/.gsd/capabilities/beads/{scripts/sync.py,tests/test_sync.py}`.
- **Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`,
  `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
- **Verification:** `python3 -m unittest discover -s plugins/beads-lifecycle/.gsd/capabilities/beads/tests -v`
  -- 125 tests, 0 failures, 0 errors, both commits present in `git log`
- **Committed in:** `33d7c34` (Task 1), `82f953f` (Task 2)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The plan's task content, tests, and behavior are implemented exactly as
specified -- only the on-disk location of the edit changed, matching the same footgun 16-01 and
16-02 already documented.

## Issues Encountered

None beyond the anticipated path deviation above, avoided proactively (confirmed via `git ls-files`
before the first edit).

## Live Verification

```
$ python3 .../sync.py check-execute-plan-patch
⚠ execute-plan.md's bd-task-read patch (beads) is missing at /home/dd/.claude/gsd-core/workflows/execute-plan.md -- gsd-executor will not read task content from bd. Reapply: see .gsd/capabilities/beads/GSD-CORE-PATCH.md
exit code: 1
```

Expected at this point in the phase -- plan 16-04 installs the patch. Matches the plan's stated
acceptance criterion exactly.

```
$ python3 -m unittest discover -s plugins/beads-lifecycle/.gsd/capabilities/beads/tests -v
...
Ran 125 tests in 4.198s
OK
```

```
$ git status --porcelain .planning/phases/
?? .planning/phases/14-pr-workflow-capability-dogfood/14-BEADS-RECALL.md
?? .planning/phases/14-pr-workflow-capability-dogfood/14-PATTERNS.md
?? .planning/phases/16-beads-issue-content-parity/.gitkeep
?? .planning/phases/16-beads-issue-content-parity/16-BEADS-RECALL.md
?? .planning/phases/16-beads-issue-content-parity/16-PATTERNS.md
```

All five entries are pre-existing untracked artifacts (present at session start per the initial
`git status`, and 16-02-SUMMARY.md already confirmed the two Phase 14 ones predate that plan too) --
zero **modified** files under `.planning/phases/`, and specifically zero modification to
`16-01-PLAN.md`, `16-02-PLAN.md` or `16-04-PLAN.md` (confirmed by an empty `git status --porcelain`
against all three paths directly).

## User Setup Required

None -- no external service configuration required. Plan 16-04 is the plan that actually installs
the `execute-plan.md` patch this detector checks for; until then, `check-execute-plan-patch`
correctly reports absent and `strip_task_bodies` stays inert on this machine (by design, per the
plan's "Ordering note").

## Next Phase Readiness

- Plan 16-04 can now wire `check-execute-plan-patch` at `plan:pre` and install the
  `execute-plan.md` patch itself -- once both land, the next `sync.py create-issues` run on a plan
  with new `auto`/`tracer` tasks will start stripping their content for real.
- `strip_task_bodies` and `check_execute_plan_patch` are both fully tested in isolation and through
  `create_issues`' two gate states; no further sync.py work is required before 16-04 wires the
  dispatch point.
- This phase's own remaining plan (16-04) is itself synced through the unmodified,
  content-carrying path -- confirmed by the empty `git status --porcelain` against
  `16-04-PLAN.md` above -- so 16-04's own task instructions are exactly as written, not yet
  affected by this plan's stripper.

---
*Phase: 16-beads-issue-content-parity*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
- FOUND: commit `33d7c34`
- FOUND: commit `82f953f`
</content>
