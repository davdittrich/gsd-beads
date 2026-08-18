---
phase: 13-markdown-linting-capability-dogfood
plan: 02
subsystem: infra
tags: [rumdl, gsd-core-capability, fail-open, unittest, gate-predicate, markdown-linting]

requires:
  - phase: 13-01
    provides: "markdown-linting capability.json wired end to end: verify:post -> markdown-linting-report skill -> lint.py -> LINT-REPORT.md; lint.py's resolve_rumdl_invocation/count_violations/verify_post happy path"
provides:
  - "verify_post()'s MDL-04 fail-open path: rumdl+uvx absent, subprocess.TimeoutExpired, or OSError all print NOTICE exactly once and rewrite LINT-REPORT.md with a non-numeric violation_count: unavailable sentinel that fails the ship:pre gate's equals:0 predicate -- never left stale"
  - "10-test stdlib-unittest suite (tests/test_lint.py) pinning MDL-01/02/04 against checked-in fixtures (clean.md: 0 violations, dirty.md: 5 violations), plus D-04 uvx-fallback argv assertion and the empty-target-set edge case"
affects: [13-03, 14-pr-workflow, 15-capability-extraction]

actuals:
  tokens: 5150
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Sentinel-report fail-open (deliberate divergence from beads/scripts/sync.py::regenerate_beads_md): the tool-absent/erroring path still fully overwrites the artifact with a non-numeric sentinel field, rather than leaving a stale file untouched -- documented in code comments so a future editor doesn't 'fix' it back to match beads"
    - "Fixture-isolated real-subprocess tests: a scratch project root (tempfile.TemporaryDirectory, copied .rumdl.toml at the real CONFIG_REL_PARTS location) lets tests exercise real rumdl against checked-in fixtures without ever touching the live, session-drifting .planning/ tree"

key-files:
  created:
    - .gsd/capabilities/markdown-linting/tests/test_lint.py
    - .gsd/capabilities/markdown-linting/tests/fixtures/clean.md
    - .gsd/capabilities/markdown-linting/tests/fixtures/dirty.md
  modified:
    - .gsd/capabilities/markdown-linting/scripts/lint.py

key-decisions:
  - "verify_post()'s fail-open path (tool-absent, TimeoutExpired, OSError) always overwrites LINT-REPORT.md with violation_count: unavailable -- a bare, non-numeric YAML scalar that cannot satisfy artifact-frontmatter-equals's strict equals:0 comparison -- deliberately diverging from sync.py's regenerate_beads_md, which leaves BEADS.md untouched on bd-absence"
  - "No STATE.md blocker append on the fail-open path (sync.py's fail-open paths all do this): the sentinel plus the ship-transcript advisory already carry the signal; a per-run STATE.md append on every rumdl-less machine run would accumulate noise"
  - "rumdl returncode 2 (config/runtime error) is explicitly excluded from the fail-open path -- count_violations raises RuntimeError, which propagates uncaught, so a broken ruleset is never laundered into a fail-open violation_count: 0"
  - "test_report_matches_handrun_count compares verify_post()'s written count against a direct lint.count_violations() call (not a subprocess invocation of the count CLI subcommand) -- both paths call the identical function with identical arguments, so the comparison is exact; avoids a second subprocess round-trip per test run"

patterns-established:
  - "Sentinel non-numeric frontmatter value as a fail-open signal an artifact-frontmatter-equals gate cannot misread as clean -- reusable by any future capability with the same regenerate-every-run + advisory-gate shape"

requirements-completed: [MDL-04]

coverage:
  - id: D1
    description: "verify_post() fail-open: rumdl+uvx both absent -> exit 0, exactly one NOTICE, LINT-REPORT.md rewritten with violation_count: unavailable (never left stale)"
    requirement: MDL-04
    verification:
      - kind: unit
        ref: "tests/test_lint.py::TestFailOpen::test_tool_absent_fail_open"
        status: pass
      - kind: unit
        ref: "tests/test_lint.py::TestFailOpen::test_tool_absent_overwrites_stale_zero_report_sentinel"
        status: pass
      - kind: integration
        ref: "live gsd_run check predicate against a sentinel-report scratch phase dir -> block:true, actual:\"unavailable\", expected:0"
        status: pass
    human_judgment: false
  - id: D2
    description: "verify_post() fail-open: subprocess.TimeoutExpired and OSError take the identical fail-open path as tool-absence"
    requirement: MDL-04
    verification:
      - kind: unit
        ref: "tests/test_lint.py::TestFailOpen::test_rumdl_timeout_fail_open"
        status: pass
      - kind: unit
        ref: "tests/test_lint.py::TestFailOpen::test_rumdl_oserror_fail_open"
        status: pass
    human_judgment: false
  - id: D3
    description: "rumdl returncode 2 (config error) raises rather than writing violation_count: 0"
    requirement: MDL-04
    verification:
      - kind: unit
        ref: "tests/test_lint.py::TestFailOpen::test_config_error_raises"
        status: pass
    human_judgment: false
  - id: D4
    description: "Curated config produces 0 violations against fixtures/clean.md, and an exact known count (5) against fixtures/dirty.md, with every reported rule id inside the curated 7-rule allowlist"
    requirement: MDL-01
    verification:
      - kind: integration
        ref: "tests/test_lint.py::TestCuratedRuleset::test_curated_config_zero_violations"
        status: pass
      - kind: integration
        ref: "tests/test_lint.py::TestCuratedRuleset::test_dirty_fixture_known_count"
        status: pass
    human_judgment: false
  - id: D5
    description: "LINT-REPORT.md's violation_count matches a hand-run count over the identical target set and config"
    requirement: MDL-02
    verification:
      - kind: integration
        ref: "tests/test_lint.py::TestReportMatchesHandRun::test_report_matches_handrun_count"
        status: pass
    human_judgment: false
  - id: D6
    description: "D-04 tier ordering: when rumdl is absent but uvx is present, the actual subprocess argv invoked starts [\"uvx\", \"rumdl\"]"
    verification:
      - kind: unit
        ref: "tests/test_lint.py::TestToolResolution::test_uvx_fallback_used_when_rumdl_absent"
        status: pass
    human_judgment: false
  - id: D7
    description: "Empty target set (a directory matching zero markdown files) yields violation_count: 0 and exit 0, not an error"
    verification:
      - kind: integration
        ref: "tests/test_lint.py::TestEmptyTargetSet::test_empty_target_set"
        status: pass
    human_judgment: false
  - id: D8
    description: "Full suite is green under both stdlib python3 -m unittest discover and pytest, from any working directory, importing nothing outside the standard library"
    requirement: MDL-04
    verification:
      - kind: unit
        ref: "python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -v (10/10 pass, from repo root and from /tmp)"
        status: pass
      - kind: unit
        ref: "python3 -m pytest .gsd/capabilities/markdown-linting/tests/ -v (10/10 pass)"
        status: pass
    human_judgment: false

duration: ~20min
completed: 2026-08-18
status: complete
---

# Phase 13 Plan 02: Fail-open hardening + full test suite for markdown-linting Summary

**`lint.py verify_post()` now degrades honestly when rumdl can't run -- exit 0, one notice, and a non-numeric `violation_count: unavailable` sentinel that the ship:pre gate correctly reads as `block:true`, backed by a 10-test stdlib suite pinning MDL-01/02/04 against checked-in `clean.md`/`dirty.md` fixtures.**

## Performance

- **Duration:** ~20min
- **Completed:** 2026-08-18T12:29:48Z
- **Tasks:** 2/2
- **Files modified:** 4 (1 modified, 3 created)

## Accomplishments

- Added `lint.py`'s module-level `NOTICE` constant and a `_write_report()` shared writer, then routed `verify_post()`'s tool-absent/`TimeoutExpired`/`OSError` outcomes through a sentinel-report branch: exit 0, `NOTICE` printed exactly once, `LINT-REPORT.md` fully overwritten with `violation_count: unavailable` (a bare, non-numeric YAML scalar) plus `unavailable_reason` naming which tier failed
- Kept the returncode-2 (config error) path raising uncaught -- a broken ruleset is never laundered into a fail-open `violation_count: 0`
- Documented the deliberate divergence from `beads/scripts/sync.py::regenerate_beads_md` in code comments at the sentinel branch, so a future editor doesn't "fix" this back to match beads's leave-it-untouched behavior
- Live-verified the sentinel path end-to-end: `gsd_run check predicate` against a scratch phase dir carrying the sentinel report returns `block:true`, `match:false`, `actual:"unavailable"`, `expected:0` -- reproducing exactly what MDL-04 success criterion 5 requires
- Authored `tests/fixtures/clean.md` (measured live: 0 violations against the shipped `.rumdl.toml`) and `tests/fixtures/dirty.md` (measured live: 5 violations -- 3x MD022, 1x MD009, 1x MD040 -- all inside the curated 7-rule allowlist, with an intentionally long line and an inline HTML element that produce zero MD013/MD033 hits, proving those rules are genuinely off)
- Built a 10-test `unittest`-only suite (`TestFailOpen`, `TestCuratedRuleset`, `TestReportMatchesHandRun`, `TestToolResolution`, `TestEmptyTargetSet`) that is green under both `python3 -m unittest discover` and `pytest`, from any working directory, and never reads the live `.planning/` tree (uses a scratch project root with its own copied `.rumdl.toml` instead)

## Task Commits

1. **Task 1: Fail-open on rumdl absence without leaving a stale report (MDL-04)** - `66003f0` (test, RED: `TestFailOpen` written against the not-yet-modified `lint.py`) + `7b94129` (feat, GREEN: sentinel-report fail-open implemented, all 5 tests pass)
2. **Task 2: Test suite and fixtures for the capability (MDL-01/02/04)** - `6cc075e` (test: fixtures + 5 additional test classes, 10/10 green)

## Files Created/Modified

- `.gsd/capabilities/markdown-linting/scripts/lint.py` - added `NOTICE`, `_write_report()`, and the fail-open sentinel branch in `verify_post()`
- `.gsd/capabilities/markdown-linting/tests/test_lint.py` - full 10-test stdlib `unittest` suite
- `.gsd/capabilities/markdown-linting/tests/fixtures/clean.md` - 0-violation fixture (MDL-01)
- `.gsd/capabilities/markdown-linting/tests/fixtures/dirty.md` - 5-violation fixture, exact count asserted (MDL-01)

## Decisions Made

- Sentinel value is the bare string `unavailable`, not omitted field or `null` -- `artifact-frontmatter-equals`'s strict `equals: 0` integer comparison has no coercion path from a string, live-confirmed to report `block:true`.
- No `STATE.md` blocker append on the fail-open path, unlike every one of `sync.py`'s fail-open branches -- the sentinel report plus the ship-transcript advisory already carry the signal; a per-run append would accumulate noise on any machine that simply doesn't have rumdl installed.
- `test_report_matches_handrun_count` compares against a direct `lint.count_violations()` call rather than shelling out to the `lint.py count` CLI subcommand a second time -- both code paths invoke the identical function with identical arguments, so the equality proven is exact; this avoids doubling the real-subprocess cost of the test.

## Deviations from Plan

None - plan executed as written. No Rule 1/2/3 auto-fixes were needed; `lint.py`'s Task 1 groundwork from plan 01 required no bug fixes to build on.

## Flagged Assumption Left Deliberately Unresolved (per plan frontmatter)

The plan's `flagged_assumptions` entry names an open edge case: rumdl present but misbehaving in a way distinct from both "cleanly absent" and "clean run" -- e.g. exiting nonzero with an unparseable body, emitting malformed JSON, or being killed by a signal. Task 1's enumerable members of that state (`TimeoutExpired`, `OSError`, returncode 2) are explicitly routed; the residual set (malformed-but-parseable-exit-code JSON, signal kills) is not caught by `verify_post`'s `except (subprocess.TimeoutExpired, OSError)` clause and would instead raise an uncaught `json.JSONDecodeError` (or similar) straight out of the script.

This was deliberately left as-is, not expanded, because: (1) the plan's own frontmatter marks this UNRESOLVED and explicitly forbids auto-resolving it by enumeration; (2) an uncaught exception is a **loud** failure -- it does not silently write a false `violation_count`, so it already satisfies the plan's "escalate rather than pass silently" instruction without needing new code. Flagging here per the plan's own "Needs manual review at verify time... Escalate rather than pass silently" instruction, for `/gsd-verify-work` or a future plan to make an explicit decision on rather than one being made implicitly by omission.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `13-03-PLAN.md` (MDL-01/MDL-03/MDL-04, ruleset cleanup + README + 0-violations validation against the real tree) can proceed -- `lint.py`'s fail-open path, `fix` subcommand, and now a green regression suite are all in place to build the README's divergence-disclosure measurement on top of.
- The unresolved edge case above (rumdl present-but-misbehaving beyond `TimeoutExpired`/`OSError`/returncode-2) remains open; 13-03 or `/gsd-verify-work` should make an explicit call on it rather than let it stay implicit.

---
*Phase: 13-markdown-linting-capability-dogfood*
*Completed: 2026-08-18*
