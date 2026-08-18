---
phase: 16-beads-issue-content-parity
plan: 01
subsystem: infra
tags: [beads, bd, sync.py, gsd-core-capability, python-stdlib]

# Dependency graph
requires:
  - phase: 04-adoption
    provides: sync.py's parse_plan/resolve_issue/resolve_epic/resolve_milestone_epic base implementation
provides:
  - "parse_plan() task dicts carry type/read_first/precondition/behavior/action/verify/acceptance_criteria/done"
  - "_task_description(task) — the one renderer for a task's bd -d description"
  - "_epic_description(objective) — the one renderer for an epic's bd -d description"
  - "get_milestone_bullet(roadmap_path, milestone) — verbatim ROADMAP milestone-bullet lookup, fail-open"
  - "resolve_issue()/resolve_epic()/resolve_milestone_epic() all write real -d/--acceptance content on create"
affects: [16-02, 16-03, beads-status, beads-sync, beads-recall skills]

# Actuals (#2632)
actuals:
  tokens: 6309
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "One-place-writes-the-shape renderer functions (_task_description, _epic_description), cloning _todo_description's established discipline"
    - "acceptance_criteria routed to bd's own --acceptance structured flag, never folded into the -d prose blob"

key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py

key-decisions:
  - "Edited the git-tracked plugin source (plugins/beads-lifecycle/.gsd/capabilities/beads/) instead of the plan-specified .gsd/capabilities/beads/ path, which is a gitignored runtime-install mirror that gets silently re-synced from the tracked source (commit 4d83504) — editing only the mirror would have been invisible to git and lost on the next capability sync"
  - "get_milestone_bullet fails open (returns \"\" on a miss) rather than raising, unlike its get_phase_header model, because resolve_milestone_epic must stay fail-open per B6/D-08"

patterns-established:
  - "Pattern: renderer function per bd-create call site (_task_description, _epic_description), never inline string-building at the call site itself"

requirements-completed: [D-06, D-02, D-03]

coverage:
  - id: D1
    description: "A task issue created by sync.py create-issues returns non-empty description and acceptance_criteria as two distinct bd show --json fields"
    requirement: "D-06"
    verification:
      - kind: unit
        ref: "test_sync.py#TestCreateIssues.test_task_create_argv_carries_description_and_acceptance"
        status: pass
      - kind: integration
        ref: "test_sync.py#TestEndToEndTracer.test_created_task_issue_round_trips_description_and_acceptance"
        status: pass
    human_judgment: false
  - id: D2
    description: "parse_plan() extracts every per-task content field (read_first/precondition/behavior/action/verify/acceptance_criteria/done) plus the task type attribute"
    requirement: "D-02"
    verification:
      - kind: unit
        ref: "test_sync.py#TestTaskDescription.test_full_task_emits_every_non_empty_section"
        status: pass
    human_judgment: false
  - id: D3
    description: "parse_plan() exposes each task's type attribute so downstream code can distinguish auto/tracer from checkpoint:* without a second string search"
    requirement: "D-03"
    verification:
      - kind: unit
        ref: "test_sync.py#TestCreateIssues (existing suite exercises parse_plan via create_issues; type field verified by direct parse_plan reads in TestTaskDescription's sibling coverage)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Phase and milestone epics carry real -d descriptions (plan <objective> / ROADMAP milestone bullet), or no -d at all when no source content exists"
    verification:
      - kind: unit
        ref: "test_sync.py#TestEpicDescription (6 new tests)"
        status: pass
      - kind: integration
        ref: "live_tracer.py ad-hoc script — bd show <epic-id> --json"
        status: pass
    human_judgment: false

duration: ~14min
completed: 2026-08-19
status: complete
---

# Phase 16 Plan 01: Task & Epic Content Parity Summary

**Every new `bd create` for a task or epic now carries a real `-d` description (and `--acceptance` for tasks), closing the write-path half of D-06 — proven by a live `bd show --json` round trip, not a mocked assertion.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-08-18T23:29:26Z (STATE.md session start)
- **Completed:** 2026-08-18T23:42:05Z (Task 2 commit)
- **Tasks:** 2
- **Files modified:** 2 (`sync.py`, `test_sync.py`, both under `plugins/beads-lifecycle/.gsd/capabilities/beads/`)

## Accomplishments

- `parse_plan()` extracts every per-task content field (`read_first`, `precondition`, `behavior`,
  `action`, `verify`, `acceptance_criteria`, `done`) plus the task `type` attribute — 8 new dict
  keys, none of the 4 existing keys touched.
- New `_task_description(task)` renders read_first/precondition/behavior/action/verify/done/files
  as `##` markdown sections into a task's `bd create -d` value; `acceptance_criteria` is
  deliberately excluded and instead passed to `bd create --acceptance`, its own structured field.
- New `_epic_description(objective)` renders a single `## Objective` section, shared by both the
  phase-epic path (fed the plan's `<objective>`) and the milestone-epic path (fed a ROADMAP
  milestone bullet).
- New `get_milestone_bullet(roadmap_path, milestone)`, modeled on `get_phase_header`, returns the
  verbatim `## Milestones` bullet matching a milestone token, fail-open (`""`) on a miss.
- `resolve_issue()`, `resolve_epic()`, and `resolve_milestone_epic()` all now write non-empty `-d`
  content on create, and never write an empty `-d` when no source content exists.
- Live round trip (see below) proves both a task issue and its parent epic issue return non-empty
  `description` (and, for the task, non-empty `acceptance_criteria`) from a real `bd show --json`.

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end task content — one PLAN.md task block reaches bd show --json** - `7fccc61`
   (feat) — `parse_plan()` extension, `_task_description()`, `resolve_issue()`'s `-d`/`--acceptance`
2. **Task 2: Epic descriptions — phase epics and milestone epics stop being title-only** - `b46fbba`
   (feat) — `OBJECTIVE_RE`, `_epic_description()`, `get_milestone_bullet()`, `resolve_epic()`'s and
   `resolve_milestone_epic()`'s `-d`

Both commits land on `plugins/beads-lifecycle/.gsd/capabilities/beads/` — see Deviations below for
why that path replaces the plan's stated `.gsd/capabilities/beads/`.

## Files Created/Modified

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` — `TASK_TYPE_RE`,
  `READ_FIRST_RE`, `PRECONDITION_RE`, `BEHAVIOR_RE`, `ACTION_RE`, `VERIFY_RE`,
  `ACCEPTANCE_CRITERIA_RE`, `DONE_RE`, `OBJECTIVE_RE` (new module-level regexes); `parse_plan()`
  extended; `_task_description()`, `_epic_description()`, `get_milestone_bullet()` (new functions);
  `resolve_issue()`, `resolve_epic()` (new trailing `objective=""` kwarg), `resolve_milestone_epic()`
  argv changes; `create_issues()` now extracts and threads the plan's `<objective>`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` — extended `TestCreateIssues`
  (2 new tests), new `TestTaskDescription` (3 tests), new `TestEpicDescription` (6 tests), extended
  `TestEndToEndTracer` (1 new live test)

## Decisions Made

- **Edited the tracked plugin source, not the plan's stated path.** The plan's `files_modified`
  names `.gsd/capabilities/beads/scripts/sync.py` and its test sibling. That path is a **gitignored
  runtime-install mirror** (`.gitignore:38-40`, comment: "copied from a plugin's own tracked source
  tree ... never track that copy here again", per commit `4d83504`, Phase 15). The actual
  git-tracked source is `plugins/beads-lifecycle/.gsd/capabilities/beads/`. Edits made only at the
  root path were repeatedly and silently reverted mid-task — confirmed by observing the file's
  content and test count regress between successive tool calls with no git operation of mine in
  between, and by `git ls-files .gsd/capabilities/beads` returning 0 tracked files vs. 17 under
  `plugins/beads-lifecycle/.gsd/capabilities/beads`. Root-caused to the runtime mirror being
  re-synced from the tracked source (the mechanism PROJECT.md's Key Decisions table documents as
  "capability-auto-install", vendored into each plugin's `session-start.sh`) — most likely
  re-triggered by a concurrent session/hook on this same working tree during this run. All edits
  now live at `plugins/beads-lifecycle/.gsd/capabilities/beads/` and are committed; the root mirror
  was best-effort synced to match after each commit but is not itself tracked or authoritative.
  Documented as a Rule 3 auto-fix (blocking issue: the plan-specified path cannot durably hold
  edits).
- **`get_milestone_bullet` fails open, unlike its `get_phase_header` model** — returns `""` on a
  miss rather than raising, because `resolve_milestone_epic` must stay fail-open per B6/D-08; a
  missing bullet is a formatting variation, not a corrupt roadmap (matches the plan's explicit
  instruction).
- **`<behavior>` included in `_task_description`'s output** even though CONTEXT.md's D-02 list does
  not name it — `workflow.tdd_mode` is `true` for this project (`config.json`), so most future tasks
  carry a `<behavior>` block; leaving it in PLAN.md while everything else moves to bd would split
  one task's instructions across two sources (documented in the function's docstring per the plan's
  discretion call).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Edited `plugins/beads-lifecycle/.gsd/capabilities/beads/` instead of the plan's `.gsd/capabilities/beads/`**
- **Found during:** Task 1, after the first round of edits at the plan-specified path silently
  disappeared between tool calls
- **Issue:** `.gsd/capabilities/beads/` is a gitignored, non-tracked runtime-install copy; the
  actual source of truth lives at `plugins/beads-lifecycle/.gsd/capabilities/beads/`
  (`git ls-files .gsd/capabilities/beads` → 0 files; same path under `plugins/beads-lifecycle/` →
  17 files). Editing only the runtime mirror produces work that git never sees and that a future
  capability re-sync overwrites.
- **Fix:** Re-applied both tasks' full edit sets against
  `plugins/beads-lifecycle/.gsd/capabilities/beads/{scripts/sync.py,tests/test_sync.py}`, ran the
  full test suite from that path, best-effort copied the result back onto the runtime mirror for
  local convenience, then committed the tracked-source files.
- **Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`,
  `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
- **Verification:** `python3 -m unittest discover -s plugins/beads-lifecycle/.gsd/capabilities/beads/tests -v` — 100 tests, 0 failures, 0 errors, both commits present in `git log`
- **Committed in:** `7fccc61` (Task 1), `b46fbba` (Task 2)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The plan's task content, acceptance criteria, tests, and behavior are
implemented exactly as specified — only the on-disk location of the edit changed, because the
plan's stated location cannot durably hold a commit in this repo's current structure.

## Issues Encountered

- Uncommitted edits at `.gsd/capabilities/beads/scripts/sync.py` (the plan's stated path) were
  observed reverting to original content across multiple tool-call boundaries with no git operation
  performed by this session. Root-caused (not just worked around) to that path being a gitignored
  runtime-install mirror of the tracked `plugins/beads-lifecycle/` source — see Deviations. Resolved
  by moving all edits to the tracked source and using atomic write+test+commit scripts to close the
  window between file write and `git commit` to a single process lifetime.

## Live Verification (tracer end-to-end proof)

Ad-hoc script against a scratch `bd` database (`bd init --prefix livedemo`), running
`create_issues()` on the `plan-single.md` fixture (which has a plan-level `<objective>` and one
task with `<acceptance_criteria>`), then `bd show <id> --json` on both the created task and its
parent epic:

```
$ python3 sync.py create-issues 01-01-PLAN.md
Synced 1 issue(s) -> epic livedemo-abt

$ bd show livedemo-abt.1 --json
[
  {
    "id": "livedemo-abt.1",
    "title": "01-01.1 Task 1: Do the thing",
    "description": "## Read First\n- src/example.py\n\n## Action\nImplement the thing.\n\n## Verify\npython3 -m py_compile src/example.py\n\n## Done\nThe thing is implemented.\n\n## Files\n- src/example.py\n",
    "acceptance_criteria": "- src/example.py exists",
    "status": "open",
    "parent": "livedemo-abt",
    ...
  }
]

$ bd show livedemo-abt --json
[
  {
    "id": "livedemo-abt",
    "title": "Phase 1: Substrate",
    "description": "## Objective\nMinimal single-task fixture plan used by sync.py's tests -- one task, no\nbeads-id element yet (first-sync input).\n",
    "status": "open",
    "issue_type": "epic",
    ...
  }
]
```

`description` and `acceptance_criteria` are confirmed as two distinct non-empty top-level keys on
the task, and the parent epic carries a real `## Objective` description drawn from the plan's
`<objective>` — the ROADMAP goal ("a `bd show <issue-id>` on any beads-synced task is
self-sufficient") is now true for newly-created issues.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `parse_plan()` now exposes each task's `type` attribute (D-03), unblocking plan 16-02/16-03's
  planned checkpoint-exclusion work for the read-path inversion.
- `_task_description`/`_epic_description` are the single rendering points for future plans to
  extend if additional per-task/per-epic fields are ever added — no second formatter exists.
- The `.gsd/capabilities/beads/` vs. `plugins/beads-lifecycle/.gsd/capabilities/beads/` path
  ambiguity is a real footgun for any future plan touching this capability; worth a one-line note in
  the phase's `<context>` or a follow-up doc fix so future plans specify the tracked path directly.
- Zero Phase 1-15 artifacts touched (confirmed via `git status --porcelain .planning/phases/` —
  only pre-existing, session-start untracked files under `14-pr-workflow-capability-dogfood/`
  remain, unrelated to this plan's changes).

---
*Phase: 16-beads-issue-content-parity*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
- FOUND: commit `7fccc61`
- FOUND: commit `b46fbba`
