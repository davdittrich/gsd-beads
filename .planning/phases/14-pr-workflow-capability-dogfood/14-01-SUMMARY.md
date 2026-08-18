---
phase: 14-pr-workflow-capability-dogfood
plan: 01
subsystem: infra
tags: [gh-cli, gsd-core-capability, gate-predicate, pr-workflow]

requires:
  - phase: 13-markdown-linting-capability-dogfood
    provides: "Structural analog to clone (capability.json steps[]/gates[] shape, lint.py's find_project_root/confined/_write_report/verify_post pattern, markdown-linting-report SKILL.md dispatch shape) and the machine-local ship.md gsd-beads-patch:ship-pre-generic-dispatch v1 patch that makes any capability's ship:pre gates[] entry actually fire"
provides:
  - "pr-workflow capability.json wired end to end: execute:wave:post -> pr-workflow-report skill -> pr_status.py verify-post -> 14-PR.md"
  - "Live proof that the generic ship:pre gate-dispatch loop evaluates pr-workflow's derived pr_gate_ok boolean correctly across all four pr_status states (none/passing satisfied, pending/failing unsatisfied)"
affects: [14-02, 14-03, 15-capability-extraction]

actuals:
  tokens: 6900
  tasks: 2
  commits: 2

tech-stack:
  added: [gh CLI 2.97.0 (pre-installed system binary, no new dependency)]
  patterns:
    - "Regenerate-every-run artifact (B11-style): pr_status.py verify_post() fully overwrites {phase_dir}/{padded_phase}-PR.md, never merging a prior hand edit -- mirrors lint.py's verify_post()"
    - "Derived gate-target boolean alongside a raw display field: PR.md carries both pr_status (four-state, human-readable) and pr_gate_ok (boolean, the actual gate predicate target) -- necessary because artifact-frontmatter-equals's equals key is single-scalar and cannot express pr_status in {none,passing} directly (RESEARCH Pitfall 1)"
    - "Path confinement (confined()/find_project_root()) copied verbatim from lint.py, not imported -- capabilities stay independent"
    - "Existence-probe-then-status-probe: gh pr list --head <branch> --state open first (empty array short-circuits to pr_status=none without a second call), gh pr checks <n> --json bucket only once a PR number is confirmed"

key-files:
  created:
    - .gsd/capabilities/pr-workflow/capability.json
    - .gsd/capabilities/pr-workflow/scripts/pr_status.py
    - .gsd/capabilities/pr-workflow/skills/pr-workflow-report/SKILL.md
    - .gsd/capabilities/pr-workflow/tests/test_pr_status.py
    - .gsd/capabilities/pr-workflow/tests/fixtures/checks_pass.json
    - .gsd/capabilities/pr-workflow/tests/fixtures/checks_pending.json
    - .gsd/capabilities/pr-workflow/tests/fixtures/checks_fail.json
    - .gsd/capabilities/pr-workflow/tests/fixtures/checks_skipping.json
    - .gsd/capabilities/pr-workflow/tests/fixtures/pr_list_empty.json
    - .planning/phases/14-pr-workflow-capability-dogfood/14-PR.md
    - .planning/phases/14-pr-workflow-capability-dogfood/14-GATE-SMOKE-TEST.md
  modified:
    - .gitignore

key-decisions:
  - "rollup_pr_status extends D-01's literal failing/pending/passing precedence to gh's actual bucket vocabulary per RESEARCH Pitfall 6: skipping contributes to passing, cancel contributes to failing alongside fail -- D-01 was written against GitHub's raw check-run states, not gh's own bucket reduction"
  - "check_buckets() branches on gh pr checks's returncode/stderr text (RESEARCH Pitfall 3: --json mode's own exit code carries no pass/fail/pending signal), not on the exit code alone -- a non-zero exit matching the documented zero-checks strings maps to an empty bucket set (D-01 passing), any other non-zero exit raises RuntimeError uncaught rather than being laundered into a status"
  - "Un-ignored .gsd/capabilities/pr-workflow/ in .gitignore, the same one-line pattern Phase 13 established for markdown-linting -- STATE.md's Next Phase Readiness note for this exact addition was correct"

patterns-established:
  - "Advisory ship:pre gate via artifact-frontmatter-equals with blocking:false, onError:skip -- second dogfooded capability (after markdown-linting) to reuse this exact predicate shape for a derived gate-target boolean"

requirements-completed: [PRW-01, PRW-02]

coverage:
  - id: D1
    description: "execute:wave:post lifecycle dispatch regenerates {phase_dir}/{padded_phase}-PR.md with pr_status/pr_gate_ok frontmatter on every run, full-overwrite not append"
    requirement: PRW-01
    verification:
      - kind: unit
        ref: ".gsd/capabilities/pr-workflow/tests/test_pr_status.py::TestVerifyPost (3 cases: none/gate-ok, failing/gate-not-ok, rerun-overwrites)"
        status: pass
      - kind: integration
        ref: "python3 .gsd/capabilities/pr-workflow/scripts/pr_status.py verify-post .planning/phases/14-pr-workflow-capability-dogfood (live gh, this repo's main branch)"
        status: pass
    human_judgment: false
  - id: D2
    description: "rollup_pr_status precedence (failing>pending>passing, empty set->passing) and derive_gate_ok (pr_status in {none,passing}) as pure functions"
    requirement: PRW-01
    verification:
      - kind: unit
        ref: ".gsd/capabilities/pr-workflow/tests/test_pr_status.py::TestRollupPrecedence, TestDeriveGateOk (8 cases)"
        status: pass
    human_judgment: false
  - id: D3
    description: "ship:pre gate (artifact-frontmatter-equals on pr_gate_ok, blocking:false) evaluates satisfied for none/passing and unsatisfied for pending/failing, using the predicate extracted verbatim from the shipped capability.json"
    requirement: PRW-02
    verification:
      - kind: integration
        ref: "gsd_run check predicate --predicate <shipped gate predicate> --phase-dir <scratch, x4 states> --phase-number 14 --raw (recorded in 14-GATE-SMOKE-TEST.md)"
        status: pass
    human_judgment: false
  - id: D4
    description: "confined() rejects a phase-dir resolution escaping the project root (T-14-03); no subprocess.run call in pr_status.py enables shell execution (T-14-02)"
    requirement: PRW-01
    verification:
      - kind: unit
        ref: ".gsd/capabilities/pr-workflow/tests/test_pr_status.py::TestConfined::test_confined_raises_for_escape"
        status: pass
      - kind: other
        ref: "AST walk asserting no ast.keyword(arg='shell', value=True) in pr_status.py"
        status: pass
    human_judgment: false

duration: ~25min
completed: 2026-08-18
status: complete
---

# Phase 14 Plan 01: Wire pr-workflow end to end, prove the ship:pre gate fires across all four states

**`pr-workflow` capability wired `execute:wave:post` -> skill -> `pr_status.py` -> `14-PR.md`, with a live-recorded four-state proof that the derived `pr_gate_ok` boolean (not the raw `pr_status`) is what the `ship:pre` gate actually evaluates.**

## Performance

- **Duration:** ~25min
- **Completed:** 2026-08-18T18:34:54+02:00
- **Tasks:** 2 (both executed; no checkpoint tasks in this plan)
- **Files modified:** 12 (11 created, 1 modified)

## Accomplishments

- Built the `pr-workflow` capability's full vertical slice: `capability.json` (one `execute:wave:post` step, one advisory `ship:pre` gate), `pr_status.py` (stdlib-only `gh` wrapper: two-tier availability guard, existence-probe-then-checks-probe, D-01/Pitfall-6 rollup, `_write_report`), and `pr-workflow-report/SKILL.md` (config-gate + single-lifecycle-point dispatch)
- Live-verified the single end-to-end path against this repo's real `main` branch (no open PR): `pr_status.py verify-post` writes `14-PR.md` with `pr_status: none`, `pr_gate_ok: true`, correct `generated_from`/`generated_at` provenance, and full-overwrite (not append) on re-run — byte length unchanged, exactly one frontmatter delimiter pair both times
- Recorded a live four-state proof (`14-GATE-SMOKE-TEST.md`) that the machine-local `ship.md` generic gate-dispatch patch, independently re-confirmed present (line 157/242, unchanged from Phase 13), fires `pr-workflow`'s `ship:pre` gate correctly: `block:false` for both `none` and `passing`, `block:true` for both `pending` and `failing` — the exact tri-state split PRW-02 requires, and direct evidence RESEARCH Pitfall 1 was avoided (the gate targets the derived `pr_gate_ok` boolean, never the raw four-state `pr_status`)
- 12 unit tests, all green, covering every `<behavior>` case: rollup precedence (D-01 + Pitfall 6's `skipping`/`cancel` mapping), gate-ok derivation, `verify_post` happy/failing/idempotent paths, and the `confined()` path-escape guard

## Task Commits

1. **Task 1: End-to-end "a real branch's PR check status becomes a gate-readable artifact" (tracer, tdd)** - `3995088` (feat)
2. **Task 2: Prove the ship:pre gate fires live across all four pr_status states** - `0b31063` (docs)

**Plan metadata:** pending (this commit)

## Files Created/Modified

- `.gsd/capabilities/pr-workflow/capability.json` - id/config/steps/gates manifest, one `execute:wave:post` step + one advisory `ship:pre` gate on `pr_gate_ok`
- `.gsd/capabilities/pr-workflow/scripts/pr_status.py` - `gh_available`, `current_branch`, `find_open_pr`, `check_buckets`, `rollup_pr_status`, `derive_gate_ok`, `_write_report`, `verify_post`, `find_project_root`/`confined` (copied from `lint.py`), `verify-post` CLI subcommand
- `.gsd/capabilities/pr-workflow/skills/pr-workflow-report/SKILL.md` - config gate + single `execute:wave:post` dispatch, mirrors `markdown-linting-report/SKILL.md`'s shape
- `.gsd/capabilities/pr-workflow/tests/test_pr_status.py` - stdlib `unittest`, 12 tests
- `.gsd/capabilities/pr-workflow/tests/fixtures/{checks_pass,checks_pending,checks_fail,checks_skipping,pr_list_empty}.json` - synthetic `gh --json` stdout captures, one per state
- `.planning/phases/14-pr-workflow-capability-dogfood/14-PR.md` - generated artifact, `pr_status: none`/`pr_gate_ok: true` as of this plan's last run (this repo's `main` branch has no open PR)
- `.planning/phases/14-pr-workflow-capability-dogfood/14-GATE-SMOKE-TEST.md` - recorded live four-case predicate smoke test transcript (PRW-02)
- `.gitignore` - un-ignored `.gsd/capabilities/pr-workflow/`, same one-line pattern Phase 13 established for `markdown-linting`

## Decisions Made

- `rollup_pr_status` extends D-01's literal three-state precedence to `gh`'s actual five-value `bucket` vocabulary (RESEARCH Pitfall 6): `skipping` contributes to `passing`, `cancel` contributes to `failing` alongside `fail`. Flagged explicitly rather than silently reinterpreting D-01, per the plan's own `flagged_assumptions`.
- `check_buckets()` treats a non-zero `gh pr checks` exit whose stderr does not match the documented zero-checks strings as a genuine tool failure (`RuntimeError`, uncaught) rather than laundering it into any `pr_status` value — mirrors `lint.py::count_violations`'s "raise on returncode 2" discipline.
- `.gitignore`'s `.gsd/capabilities/*` blanket-ignore was un-ignored for `pr-workflow/` specifically, the exact sibling addition Phase 13's own `13-01-SUMMARY.md` "Next Phase Readiness" section predicted would be needed here.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - plan-verify defect, inherited from Phase 13] Task 1's literal `<verify>` command could not execute in this environment**
- **Found during:** Task 1, immediately after implementing `pr_status.py` and attempting to run the acceptance-criteria unittest-discover command.
- **Issue:** The plan's original `<verify>`/acceptance-criteria text used `python3 -m unittest discover -s .gsd/capabilities/pr-workflow/tests -t . -p 'test_*.py'`. Reading `/usr/lib/python3.14/unittest/loader.py` directly confirmed the root cause: with `-t .` (top-level dir differing from start dir), `unittest`'s discovery requires an importable dotted module path from the top-level dir down to the test dir, and a literal leading `.` (this repo's `.gsd/` directory) is not a valid Python package-name segment (`ModuleNotFoundError: No module named '.gsd'`). Confirmed identical, pre-existing behavior against `markdown-linting`'s own `test_lint.py` using the same `-t .` shape — this defect shipped un-noticed in Phase 13 and was copied into this plan's text by the same pattern-clone.
- **Fix:** No code change. The coordinator fixed the plan documents directly (`f31e6f4`, outside this execution) by dropping `-t .` from `14-01-PLAN.md`/`14-02-PLAN.md`/`14-03-PLAN.md`'s verify commands, mirroring an identical fix already applied to Phase 13's plans. This executor re-read `14-01-PLAN.md` fresh from disk after that commit and confirmed the corrected command (`python3 -m unittest discover -s .gsd/capabilities/pr-workflow/tests -p 'test_*.py'`) before treating Task 1's verify as passing.
- **Verification:** The corrected command exits 0 with all 12 tests passing; this was independently confirmed against `markdown-linting`'s suite too (same root cause, same fix shape, not touched by this plan).
- **Committed in:** `f31e6f4` (coordinator, prior to Task 2 execution — not part of this plan's own task commits)

---

**Total deviations:** 1 auto-fixed (1 inherited plan-doc defect, fixed by the coordinator before Task 2)
**Impact on plan:** No code or test behavior changed — only the verify-command text differed from what was literally written. No scope creep.

## Issues Encountered

None beyond the deviation above.

## User Setup Required

None - `gh` CLI was already installed and authenticated (`davdittrich`) in this environment; no external service configuration required.

## Next Phase Readiness

- `14-02-PLAN.md` (PRW-04, two distinct `gh`-absent/`gh`-unauthenticated fail-open notices, `ship-post-notice` subcommand + `ship:post` step) and `14-03-PLAN.md` (PRW-03, live degrade-cycle evidence appendix) can both proceed — the underlying capability skeleton, `NOTICE_GH_ABSENT`/`NOTICE_GH_UNAUTH` placeholder constants (already defined, wording is 14-02's scope), and the live-proven gate mechanism are all in place.
- `.planning/phases/14-pr-workflow-capability-dogfood/14-COVERAGE.md` (the `gh` API coverage matrix named in this plan's "Artifacts this phase produces" table) was not authored by this plan — it is listed there as a planner-time deliverable, not one of this plan's two tasks; confirm with the planner whether it still needs to land before Phase 14 closes.
- The `-t .` unittest-discover defect (see Deviations) is now fixed at the plan-doc level for Phase 14's three plans and was already fixed for Phase 13's; no other phase's plans were checked and none were modified by this execution.

---
*Phase: 14-pr-workflow-capability-dogfood*
*Completed: 2026-08-18*

## Self-Check: PASSED

All 13 claimed files found on disk (11 created capability/artifact files, `.gitignore`,
`14-GATE-SMOKE-TEST.md`); both claimed task commits (`3995088`, `0b31063`) found in git history.
