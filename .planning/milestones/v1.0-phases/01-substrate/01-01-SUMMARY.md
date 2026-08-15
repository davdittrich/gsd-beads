---
phase: 01-substrate
plan: 01
subsystem: infra
tags: [beads, bd, gsd-capability, python-stdlib, unittest]

# Dependency graph
requires: []
provides:
  - "beads capability skeleton at .gsd/capabilities/beads/ (capability.json, beads-sync SKILL.md)"
  - "sync.py create-issues: resolve-or-create one phase epic + one issue per PLAN.md task, identity bound via <beads-id>, fail-open on bd absent/failing (B6/D-08)"
  - "real-bd end-to-end proof (TestEndToEndTracer) plus mocked unit coverage for B1/B4/B6"
  - "PLAN.md fixtures (plan-single.md, plan-synced.md) other 01-* plans can reuse"
affects: [01-02-dependency-idempotency-orphans, 01-03-wave-close-beads-status-install]

# Actuals (#2632)
actuals:
  tokens: 6677
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "gsd-core role:feature capability overlay, mempalace-analog shape (config-gate -> bd-availability-gate -> dispatch -> report SKILL.md)"
    - "bd identity resolution: <beads-id>/beads_epic frontmatter is the sole identity source, never title matching"
    - "every bd call is a typed subprocess.run argv list, shell execution never enabled (N4/T-01-01)"

key-files:
  created:
    - .gsd/capabilities/beads/capability.json
    - .gsd/capabilities/beads/skills/beads-sync/SKILL.md
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/tests/test_sync.py
    - .gsd/capabilities/beads/tests/fixtures/plan-single.md
    - .gsd/capabilities/beads/tests/fixtures/plan-synced.md
    - .gitignore
  modified: []

key-decisions:
  - "capability.json's skills[] lists only 'beads-sync' (not 'beads-status') -- beads-status/SKILL.md doesn't exist until Plan 03, so declaring it now would be a phantom skill reference"
  - "sync.py derives the plan-and-task ordinal prefix (e.g. 01-01) from the PLAN.md filename, not from parsing the frontmatter phase/plan text values -- keeps T-01-02 path-confinement trivially true since no filesystem path is ever built from untrusted frontmatter content"
  - "epic resolution treats a stored-but-now-missing beads_epic id the same as absent: falls through to create a fresh epic rather than hard-erroring -- consistent with B6's fail-open ethos; full B10 divergence handling for this case is explicitly out of Phase 1 scope (Phase 3)"

patterns-established:
  - "Pattern: resolve-by-id-before-create for every bd entity (epic and task) -- bd show/list confirms existence first, bd create only runs on confirmed absence"
  - "Pattern: fail-open detection is a single function (bd_available()) called once at the top of any bd-touching entry point; absent/non-zero-exit/timeout all take the identical skip path"

requirements-completed: [B1, B4, B6]

coverage:
  - id: D1
    description: "One PLAN.md task becomes exactly one beads issue under a phase epic, proven against a real bd v1.2.1 database (B1)"
    requirement: "B1"
    verification:
      - kind: e2e
        ref: "tests/test_sync.py#TestEndToEndTracer.test_single_task_creates_one_issue_under_epic"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestCreateIssues.test_single_task_builds_one_epic_and_one_task_create"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestCreateIssues.test_three_task_plan_builds_three_task_creates_same_parent"
        status: pass
    human_judgment: false
  - id: D2
    description: "Identity is bound by explicit <beads-id>, never title -- a renamed task resolves to the same issue and creates no duplicate (B4)"
    requirement: "B4"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestIdentityBinding.test_synced_plan_creates_nothing"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestIdentityBinding.test_rename_then_resync_creates_nothing_and_keeps_id"
        status: pass
    human_judgment: false
  - id: D3
    description: "bd absent, or bd present but every invocation failing, degrades to exit 0 with one stdout notice and one STATE.md Blockers/Concerns bullet, never an exception, no BEADS.md written (B6)"
    requirement: "B6"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestFailOpen.test_bd_missing_from_path"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestFailOpen.test_bd_present_but_every_invocation_fails"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-08-15
status: complete
---

# Phase 01 Plan 01: Beads Substrate Tracer Summary

**Working end-to-end path from one PLAN.md task to one real `bd` issue under a phase epic, with `<beads-id>` write-back, `<beads-id>`-first idempotent resolution, and full fail-open degrade on `bd` absent/failing.**

## Performance

- **Duration:** ~8 min (implementation only; excludes context-gathering reads)
- **Started:** 2026-08-15T01:47:00Z
- **Completed:** 2026-08-15T01:53:34Z
- **Tasks:** 2/2
- **Files modified:** 7 (6 created under `.gsd/capabilities/beads/`, plus `.gitignore`)

## Accomplishments

- `.gsd/capabilities/beads/capability.json` — role:feature manifest declaring `beads.enabled`/`beads.sync_mode` config and the single `plan:post` -> `beads-sync` step, `onError: skip`
- `beads-sync` SKILL.md — banner, config gate, bd-availability delegation to `sync.py`, single dispatch call, report line
- `sync.py create-issues` (stdlib only) — resolves-or-creates one phase epic (title read verbatim from `ROADMAP.md`, D-05) and one issue per task lacking a `<beads-id>`, writes `beads_epic`/`<beads-id>` back into the plan file, and fails open per B6/D-08
- `TestEndToEndTracer` proves the whole path against a real `bd` v1.2.1 database in a temporary directory: one epic created, exactly one child returned by `bd list --parent <epic> --json`, `<beads-id>` written back matching the created id
- `TestCreateIssues`/`TestIdentityBinding`/`TestFailOpen` add mock-backed coverage for B1, B4 and B6 without touching a real `bd` database

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "one plan task becomes one beads issue" — one path only** - `8d0d981` (feat)
2. **Task 2: Mocked unit coverage for issue creation, identity binding and fail-open** - `c69f45b` (test)

_Note: Task 2 is annotated `tdd="true"` but adds coverage for behavior Task 1's tracer already
implemented and proved end-to-end — see "TDD Gate Compliance" below for why the classic
RED-before-implementation ordering does not apply here, and what stood in for it._

## Files Created/Modified

- `.gsd/capabilities/beads/capability.json` — capability manifest (config, one step, empty contributions/gates)
- `.gsd/capabilities/beads/skills/beads-sync/SKILL.md` — agent-invocable sync instructions
- `.gsd/capabilities/beads/scripts/sync.py` — stdlib-only `create-issues` subcommand
- `.gsd/capabilities/beads/tests/test_sync.py` — `TestEndToEndTracer` (Task 1) + `TestCreateIssues`, `TestIdentityBinding`, `TestFailOpen` (Task 2)
- `.gsd/capabilities/beads/tests/fixtures/plan-single.md` — one-task, no-`<beads-id>` fixture (first-sync input)
- `.gsd/capabilities/beads/tests/fixtures/plan-synced.md` — two-task fixture already carrying `<beads-id>`/`beads_epic`
- `.gitignore` — excludes `__pycache__/`, `*.pyc` (byproduct of running the new test suite)

## Decisions Made

- **`skills[]` lists only `beads-sync`.** RESEARCH.md's illustrative `capability.json` skeleton listed both `beads-sync` and `beads-status`, but `beads-status/SKILL.md` doesn't exist until Plan 03. Declaring an unshipped skill stem risks a phantom reference at install/consent time; only `beads-sync` is declared now, matching the plan's own instruction to "register the beads-status step only in Plan 03, when that skill exists."
- **Ordinal prefix derived from the PLAN.md filename, not frontmatter text.** `sync.py` computes the `01-01` title prefix from `Path(plan_path).stem`, never from the frontmatter `phase`/`plan` string values. This keeps T-01-02's path-confinement mitigation trivially satisfied — no filesystem path is ever built from PLAN.md-authored text — without needing a more elaborate sanitizer.
- **Stored-but-missing `beads_epic` id falls through to a fresh `bd create`.** The plan's `<action>` text only specifies "confirm exists" vs. "absent -> create"; it doesn't cover a stored id that no longer resolves. Chose fail-open-and-recreate over hard-erroring, consistent with B6's design ethos. Full B10 divergence semantics for this exact case are Phase 3 scope, not re-derived here.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created `test_sync.py` with `TestEndToEndTracer` inside Task 1, not Task 2**
- **Found during:** Task 1
- **Issue:** Task 1's own `<verify>` command (`... -k TestEndToEndTracer -v`) and acceptance criteria require `TestEndToEndTracer` to exist and pass, but Task 1's `<files>` list does not include `tests/test_sync.py` — that file, and the `TestEndToEndTracer` class specifically, is described as Task 2's deliverable ("Add the TestEndToEndTracer class that Task 1's verify targets"). As written, Task 1 cannot pass its own gate without a file Task 2 was scheduled to write.
- **Fix:** Created `.gsd/capabilities/beads/tests/test_sync.py` in Task 1 containing the `sys.path` bootstrap and only the `TestEndToEndTracer` class, so Task 1's `<verify>` runs and passes against real infrastructure it built. Task 2 then extended the same file with the three mock-backed classes, leaving `TestEndToEndTracer` untouched.
- **Files modified:** `.gsd/capabilities/beads/tests/test_sync.py` (created in Task 1's commit instead of Task 2's, per necessity)
- **Verification:** `python3 -m unittest discover -s .gsd/capabilities/beads/tests -k TestEndToEndTracer -v` passes against a real `bd` v1.2.1 database
- **Committed in:** `8d0d981` (Task 1 commit)

**2. [Rule 1 - Bug] Fixed two fixtures' prose containing an unclosed literal `<beads-id>` substring**
- **Found during:** Task 1, running `TestEndToEndTracer` for the first time
- **Issue:** `plan-single.md`'s and `plan-synced.md`'s `<objective>` prose originally used the literal text `<beads-id>` inline (e.g. "one task, no `<beads-id>` yet"). Because `BEADS_ID_RE`/regex-based lookups scan for `<beads-id>...</beads-id>` spans, a lone unclosed opening tag in prose greedily matched forward to the next real closing tag elsewhere in the file, producing a garbage captured id and a spurious end-to-end test failure.
- **Fix:** Rewrote the prose to say "beads-id element" instead of the bracketed literal, eliminating the false match. (Note: production `sync.py` itself was never affected — its `parse_plan()` scopes `NAME_RE`/`BEADS_ID_RE` searches to each `<task>` block already matched by `TASK_RE`, not the whole file; only the test's own file-wide assertion in `test_sync.py` and the fixtures' prose needed the fix.)
- **Files modified:** `.gsd/capabilities/beads/tests/fixtures/plan-single.md`, `.gsd/capabilities/beads/tests/fixtures/plan-synced.md`
- **Verification:** `TestEndToEndTracer` passes; `grep -c '<beads-id>' fixtures/plan-synced.md` returns exactly 2 (both real task elements)
- **Committed in:** `8d0d981` (Task 1 commit)

**3. [Rule 3 - Blocking] Added `.gitignore` for `__pycache__/`**
- **Found during:** Task 1, after running the test suite for the first time
- **Issue:** Running `python3 -m unittest` generated `__pycache__/` directories under both `scripts/` and `tests/`, which `git status` reported as untracked — left as-is this would either get committed (noise) or silently ignored file-by-file forever.
- **Fix:** Added a repo-root `.gitignore` (none existed) excluding `__pycache__/` and `*.pyc`.
- **Files modified:** `.gitignore` (created)
- **Verification:** `git status --short` shows no untracked generated files after this fix
- **Committed in:** `8d0d981` (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (2 Rule 3 - blocking, 1 Rule 1 - bug)
**Impact on plan:** All three were necessary to make Task 1's own verify command runnable and its test suite hygienic. No scope creep — no functionality beyond what B1/B4/B6 and the plan's stated artifacts require was added.

## TDD Gate Compliance

Task 2 carries `tdd="true"` but the strict RED-before-implementation ordering does not apply
cleanly: `sync.py`'s `create-issues` logic was already fully implemented and committed in Task 1
(the tracer), so writing `TestCreateIssues`/`TestIdentityBinding`/`TestFailOpen` against that
already-correct implementation produced passing tests on the first run — there was no failing-red
phase to observe, because no new behavior was being added. This follows directly from the plan's
own tracer-first design ("Every later plan expands out from this proven slice instead of
discovering an architectural dead end after three plans have landed") — the deliberate ordering is
real-implementation-first, then backfill mocked coverage.

In place of a RED commit, the plan's own acceptance criteria specify a planted-failure check:
"Deleting the parent-flag argument from the task-create argv in sync.py makes TestCreateIssues fail
(planted-failure check, run once and revert)." This was performed exactly as specified before the
Task 2 commit: `--parent`/`epic_id` was removed from `resolve_issue`'s argv, `TestCreateIssues` was
re-run and confirmed to fail (`AssertionError: '--parent' not found in [...]` and a `ValueError`
from the second sub-test), the argv was reverted, and the full suite was re-confirmed green before
committing. This is the RED-phase proof for this task; no failing-test commit exists in git history
for Task 2 since the same working tree state (pre-fix, post-fix) was never meant to be persisted
mid-fix — only the final, passing state was committed (`c69f45b`).

Gate sequence found in git log for this plan: `feat(01-01)` (Task 1, `8d0d981`) then `test(01-01)`
(Task 2, `c69f45b`) — feat before test, the inverse of the canonical `test` -> `feat` TDD ordering,
for the reason above.

## Issues Encountered

None beyond the three items documented under Deviations above.

## User Setup Required

None — no external service configuration required. (The capability itself requires
`gsd capability install ... --scope project` plus the `beads.enabled` config flip before it is
live in any real gsd loop; that install+consent step is explicitly out of this plan's scope per
01-RESEARCH.md's Pitfall 4 and is expected to land as a `checkpoint:human-verify`/
`checkpoint:human-action` task in Plan 03.)

## Next Phase Readiness

- The proven tracer slice (epic resolution, `<beads-id>`-first issue resolution, fail-open
  detection, argv-list `bd` invocation pattern) is the foundation Plan 02 (dependency edges,
  idempotent re-sync, orphan closure, divergence reporting — B2/B5) and Plan 03 (wave-scoped batch
  close, `beads-status`, install/consent checkpoint — B3) both extend directly.
- No blockers. `bd` v1.2.1 and Python 3.14.7 are both confirmed present in this environment; the
  gsd-beads repo itself has no `.beads/` database yet, which is expected and handled correctly by
  the fail-open path (running `beads-sync` against this repo today prints the B6 notice rather than
  erroring, until an operator runs `bd init` as part of the not-yet-built install step).

---
*Phase: 01-substrate*
*Completed: 2026-08-15*

## Self-Check: PASSED

All 8 created/modified files confirmed present on disk; both task commit hashes (`8d0d981`,
`c69f45b`) confirmed present in `git log --oneline --all`.
