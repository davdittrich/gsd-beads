---
phase: 03-enforcement
plan: 02
subsystem: infra
tags: [beads, bd, sync.py, capability.json, ship-gate, git-trailer]

# Dependency graph
requires:
  - phase: 03-enforcement
    provides: "03-01's real blocking_open/diverged BEADS.md frontmatter fields (D-01/D-02/D-04)
      -- this plan's gates and override primitive read those fields, not Phase 2's 0 placeholders"
provides:
  - "ship_override(phase_dir) + _read_beads_md_frontmatter(phase_dir) -- sync.py primitive that
    records a beads.ship_gate=false bypass via a durable git commit --amend --trailer (always
    attempted, load-bearing) plus a best-effort bd comment on the phase epic (fail-open, B6),
    sourced only from BEADS.md's own generated frontmatter (D-05)"
  - "sync.py ship-override <phase_dir> CLI subcommand"
  - "capability.json gates[]: two ship:pre artifact-frontmatter-equals entries (blocking_open==0,
    diverged==0), both blocking, onError: skip, gated on beads.ship_gate -- PRD Section 5.3's
    exact shape"
  - "capability.json config: beads.ship_gate (boolean, default true)"
  - "capability.json steps[]: ship:pre -> beads-status dispatch entry"
  - "beads-status/SKILL.md Step 2c (ship:pre override dispatch) and a documented, verified gap
    between these declared gates and gsd-core's currently-installed ship.md (which does not yet
    dispatch them) -- closed by 03-03"
affects: [03-03]

# Actuals (#2632)
actuals:
  tokens: 4421
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ship_override's git trailer write and bd comment write are independent -- git failing
      never skips the bd comment attempt, and bd unavailability never changes the git half's
      outcome or exit code; only the git result determines ship_override's return value"
    - "ship_override reads BEADS.md's own generated frontmatter only, via a small
      key:value-per-line regex over the frontmatter block -- never a fresh live bd query at
      override time"

key-files:
  created: []
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/tests/test_sync.py
    - .gsd/capabilities/beads/capability.json
    - .gsd/capabilities/beads/skills/beads-status/SKILL.md

key-decisions:
  - "Trailer key/format: 'Beads-Override: ship_gate bypassed, blocking_open=N, diverged=N' --
    Claude's Discretion per 03-CONTEXT.md, verified parseable via git log -1
    --format=%(trailers) against a real temporary git repo before committing"
  - "ship:pre gates/steps declared exactly per PRD Section 5.3, but the plan's objective and the
    beads-status SKILL.md's new 'Known Gap' section both document, not silently assume, that the
    installed gsd-core ship.md does not yet dispatch them -- verified directly by reading
    $HOME/.claude/gsd-core/workflows/ship.md's preflight_checks step (only capId=='security' and
    'broken-windows' are special-cased)"

patterns-established:
  - "A new non-bd subprocess call (git commit --amend --trailer) still follows T-01-01's
    argv-list-not-shell-string discipline, matching every existing bd call's convention even
    though it isn't bd"

requirements-completed: [B9, B10]

coverage:
  - id: D1
    description: "ship_override records a beads.ship_gate=false bypass via a durable git trailer
      (always attempted) plus a best-effort bd comment (fail-open), sourced only from BEADS.md's
      own generated frontmatter"
    requirement: B9
    verification:
      - kind: unit
        ref: "test_sync.py::TestShipOverride::test_full_success_records_trailer_and_bd_comment"
        status: pass
      - kind: unit
        ref: "test_sync.py::TestShipOverride::test_git_failure_still_records_bd_comment_and_exits_one"
        status: pass
      - kind: unit
        ref: "test_sync.py::TestShipOverride::test_bd_unavailable_still_writes_git_trailer_skips_comment"
        status: pass
      - kind: unit
        ref: "test_sync.py::TestShipOverride::test_missing_beads_md_makes_zero_subprocess_calls_and_exits_one"
        status: pass
      - kind: other
        ref: "git trailer argv form smoke-tested against a real temporary git repo (git log -1
          --format=%(trailers) parses it correctly) -- not just inside the mocked test suite"
        status: pass
    human_judgment: false
  - id: D2
    description: "capability.json declares the two ship:pre gates and the beads.ship_gate config
      key exactly per PRD Section 5.3, and beads-status/SKILL.md documents Step 2c's dispatch
      plus the verified, current non-enforcement gap in gsd-core's installed ship.md"
    requirement: B10
    verification:
      - kind: unit
        ref: "python3 one-liner asserting gates[] shape, beads.ship_gate config default, and the
          ship:pre steps[] entry (Task 2's <verify> command), run directly against the real
          capability.json"
        status: pass
      - kind: other
        ref: "python3 -m json.tool .gsd/capabilities/beads/capability.json (valid JSON)"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-08-15
status: complete
---

# Phase 3 Plan 02: Enforcement -- ship:pre Gates + Override-Audit Primitive Summary

**`ship_override` records a `beads.ship_gate=false` bypass as a durable git trailer plus a
best-effort `bd comment`, and `capability.json` now declares the two PRD Section 5.3 `ship:pre`
gates -- though a verified gap in gsd-core's installed `ship.md` means they are not yet
live-enforced until `03-03` lands.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-08-15T16:46:00Z
- **Completed:** 2026-08-15T16:53:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- `ship_override(phase_dir)` and its helper `_read_beads_md_frontmatter(phase_dir)` now exist in
  `sync.py`: on `ship-override <phase_dir>`, they always attempt a `git commit --amend
  --allow-empty --no-edit --trailer "Beads-Override: ship_gate bypassed, blocking_open=N,
  diverged=N"` (load-bearing, D-05) and independently attempt a best-effort `bd comment` on the
  phase epic (fail-open, B6) -- neither half's outcome affects the other, and both are sourced
  only from `BEADS.md`'s own generated frontmatter, never a fresh live `bd` query.
- `capability.json`'s `gates: []` is replaced with two `ship:pre` `artifact-frontmatter-equals`
  entries (`blocking_open == 0`, `diverged == 0`), both `blocking: true`, `onError: "skip"`,
  gated on the new `beads.ship_gate` config key (default `true`) -- PRD Section 5.3's shape
  reproduced exactly. A `ship:pre` -> `beads-status` `steps[]` entry was also added.
- `beads-status/SKILL.md` gained Step 2c (dispatches `ship-override` only when
  `beads.ship_gate=false` actually bypassed a block) and a "Known Gap" section documenting --
  verified by reading `$HOME/.claude/gsd-core/workflows/ship.md` directly -- that the installed
  `/gsd-ship` workflow's `preflight_checks` step only special-cases `capId=='security'`/
  `'broken-windows'`, so these new `gates[]`/`steps[]` entries are declarative, not yet
  live-enforced.
- `ship_override` has dedicated test coverage (`TestShipOverride`, 4 new tests: full success,
  git failure, bd unavailable, missing `BEADS.md`) plus a real-git-repo smoke test of the exact
  trailer argv form during execution.

## Task Commits

Each task was committed atomically:

1. **Task 1: `ship_override` -- BEADS.md-sourced git trailer + best-effort bd comment**
   - `7bcd456` (test) RED: `TestShipOverride` added, all 4 cases fail with `AttributeError`
     (`sync.ship_override` did not exist yet)
   - `04e235e` (feat) GREEN: `_read_beads_md_frontmatter`, `ship_override`, `ship-override` CLI
     subcommand; 49/49 tests passing
2. **Task 2: Declare `ship:pre` gates, `beads.ship_gate` config, `ship:pre` step; document the
   verified `ship.md` dispatch gap**
   - `6132fe4` (feat) `capability.json` `gates[]`/`config`/`steps[]`; `SKILL.md` Step 2c +
     "Known Gap" section + Anti-Patterns entry

**Plan metadata:** (this commit)

_Note: Task 1 is `tdd="true"` -- RED/GREEN split across two commits per protocol; Task 2 is
`type="auto"` with a single commit._

## Files Created/Modified

- `.gsd/capabilities/beads/scripts/sync.py` - `BEADS_MD_FIELD_RE`, `_read_beads_md_frontmatter`,
  `ship_override`, `ship-override` CLI subcommand wiring
- `.gsd/capabilities/beads/tests/test_sync.py` - `TestShipOverride` class (4 tests) plus its
  `_write_ship_override_workspace`/`_ship_override_beads_md_text` fixtures
- `.gsd/capabilities/beads/capability.json` - `gates[]` (2 new entries), `config.beads.ship_gate`,
  `steps[]` (1 new `ship:pre` entry)
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md` - Step 1.5's branch list extended to
  four points, new Step 2c, new "Known Gap" section, Anti-Patterns entry 8

## Decisions Made

- Trailer key/format `Beads-Override: ship_gate bypassed, blocking_open=N, diverged=N` chosen
  per Claude's Discretion (03-CONTEXT.md) and verified parseable against a real temporary git
  repo (`git log -1 --format=%(trailers)`) before committing, not just inside mocked tests.
- The `git commit --amend --trailer` write follows the same argv-list, `shell=False` discipline
  as every `bd` call in this file (T-01-01), even though it invokes `git` rather than `bd`.
- No new architectural decisions beyond what D-05 (03-CONTEXT.md) already fixed; the
  gates[]/config/steps[] shape is locked by PRD Section 5.3 and reproduced verbatim.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The plan's own "Known Limitation" section (verified during Phase 3 planning) already
anticipated that these `ship:pre` gates would be schema-valid but inert against the currently
installed `ship.md` -- Task 2's action explicitly required documenting this, not fixing it here;
`03-03-PLAN.md` closes the gap with a machine-local, user-authorized patch to the installed
`ship.md`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `capability.json` now declares the exact `ship:pre` gate/config/step shape PRD Section 5.3
  requires, and `ship_override` is a correct, independently-testable D-05 override-audit
  primitive -- both ready for `03-03` to wire live.
- Blocker carried forward (documented, not resolved by this plan): the installed `ship.md` does
  not yet dispatch any capability's `ship:pre` gates beyond `security`/`broken-windows` --
  `03-03-PLAN.md` is required before these gates actually block a real `/gsd-ship` run.

---
*Phase: 03-enforcement*
*Completed: 2026-08-15*

## Self-Check: PASSED

All 4 modified files (`sync.py`, `test_sync.py`, `capability.json`, `SKILL.md`) confirmed
present on disk; all 3 task commits (`7bcd456`, `04e235e`, `6132fe4`) confirmed present in
`git log`.
