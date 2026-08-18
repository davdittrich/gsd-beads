---
phase: 13-markdown-linting-capability-dogfood
plan: 01
subsystem: infra
tags: [rumdl, gsd-core-capability, gate-predicate, markdown-linting]

requires:
  - phase: 03-beads-ship-gate
    provides: "machine-local ship.md gsd-beads-patch:ship-pre-generic-dispatch v1 patch that makes any capability's ship:pre gates[] entry actually fire"
provides:
  - "markdown-linting capability.json wired end to end: verify:post -> markdown-linting-report skill -> lint.py -> LINT-REPORT.md"
  - "First live proof that the generic ship:pre gate-dispatch loop evaluates a non-security/broken-windows capId's gate correctly, both satisfied and unsatisfied"
affects: [13-02, 13-03, 14-pr-workflow, 15-capability-extraction]

actuals:
  tokens: 4880
  tasks: 3
  commits: 3

tech-stack:
  added: [rumdl 0.2.53 (PATH), uvx rumdl (untested fallback tier, not yet exercised)]
  patterns:
    - "Regenerate-every-run artifact (B11-style): lint.py verify_post() fully overwrites {phase_dir}/{padded_phase}-LINT-REPORT.md, never merging a prior hand edit -- mirrors sync.py's regenerate_beads_md()"
    - "D-02 single-source-of-truth target constant (LINT_TARGETS) shared by count/verify-post/fix"
    - "Path confinement (confined()/find_project_root()) copied verbatim from sync.py, not imported -- capabilities stay independent"

key-files:
  created:
    - .gsd/capabilities/markdown-linting/capability.json
    - .gsd/capabilities/markdown-linting/config/.rumdl.toml
    - .gsd/capabilities/markdown-linting/scripts/lint.py
    - .gsd/capabilities/markdown-linting/skills/markdown-linting-report/SKILL.md
    - .planning/phases/13-markdown-linting-capability-dogfood/13-LINT-REPORT.md
    - .planning/phases/13-markdown-linting-capability-dogfood/13-GATE-SMOKE-TEST.md
  modified:
    - .gitignore
    - .planning/STATE.md

key-decisions:
  - "Task 1's blocking-human checkpoint (PyPI rumdl SUS verdict) was approved by the user before this continuation agent started; no re-verification performed per explicit resume instructions"
  - "Narrowed .gitignore's blanket .gsd/ ignore (added same day by quick-task 260818-h2h) to explicitly un-ignore .gsd/capabilities/markdown-linting/ -- the blanket form silently blocked this phase's in-repo dogfood pattern for a brand-new capability with no extracted plugin source yet"
  - "requirements mark-complete run for MDL-02/MDL-03 only, NOT MDL-01 -- MDL-01's literal acceptance text requires 0 violations against the real .planning/ tree plus a README divergence disclosure, neither of which this plan delivers (489 violations remain); that is 13-03's explicit scope (MDL-01 also appears in 13-03-PLAN.md's own requirements frontmatter)"

patterns-established:
  - "Advisory ship:pre gate via artifact-frontmatter-equals with blocking:false, onError:skip -- second capability (after beads) to prove this predicate kind for a non-blocking gate"

requirements-completed: [MDL-02, MDL-03]

coverage:
  - id: D1
    description: "verify:post lifecycle dispatch regenerates {phase_dir}/{padded_phase}-LINT-REPORT.md with an integer violation_count frontmatter field on every run"
    requirement: MDL-02
    verification:
      - kind: integration
        ref: "python3 .gsd/capabilities/markdown-linting/scripts/lint.py verify-post .planning/phases/13-markdown-linting-capability-dogfood"
        status: pass
    human_judgment: false
  - id: D2
    description: "ship:pre gate (artifact-frontmatter-equals, blocking:false) evaluates satisfied at violation_count 0 and unsatisfied at violation_count 7, using the predicate extracted verbatim from the shipped capability.json"
    requirement: MDL-03
    verification:
      - kind: integration
        ref: "gsd_run check predicate --predicate <shipped gate predicate> --phase-dir <scratch> --phase-number 13 --raw (recorded in 13-GATE-SMOKE-TEST.md)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Curated rumdl config wired with an always-explicit --config path (no auto-discovery reliance)"
    requirement: MDL-01
    verification: []
    human_judgment: true
    rationale: "MDL-01 also requires 0 violations against the real tree and a README divergence disclosure -- neither delivered by this plan (489 violations remain, no README yet); full MDL-01 closure is 13-03's scope. Config wiring itself is proven by D1's live run, but the requirement as a whole is not yet satisfiable by automated status alone."

duration: ~20min (continuation from Task 1 checkpoint; original checkpoint-session duration not separately tracked)
completed: 2026-08-18
status: complete
---

# Phase 13 Plan 01: Wire markdown-linting end to end, prove the generic ship:pre gate fires

**`markdown-linting` capability wired verify:post -> skill -> lint.py -> LINT-REPORT.md, with a live-recorded proof that the generic `ship:pre` gate dispatch loop actually evaluates its `artifact-frontmatter-equals` predicate for a non-`security`/`broken-windows` `capId`.**

## Performance

- **Duration:** ~20min (continuation agent; Task 1's original checkpoint session duration not tracked)
- **Completed:** 2026-08-18T12:20:15Z
- **Tasks:** 3 (1 checkpoint approved by user before this session, 2 executed)
- **Files modified:** 8 (6 created, 2 modified)

## Accomplishments

- Built the `markdown-linting` capability's full vertical slice: `capability.json` (one `verify:post` step, one advisory `ship:pre` gate), `.rumdl.toml` (curated 7-rule MD0XX allowlist), `lint.py` (stdlib-only rumdl/uvx wrapper), and `markdown-linting-report/SKILL.md` (config-gate + single-lifecycle-point dispatch)
- Live-verified the single end-to-end path: `lint.py verify-post` writes `{phase_dir}/13-LINT-REPORT.md` with an integer `violation_count` (489, against this repo's real `.planning/`/`README.md`/`CLAUDE.md`), a matching `count` subcommand, correct `generated_from`/`generated_at` provenance, and the required "do not hand-edit" banner
- Recorded the first live proof that the machine-local `ship.md` generic gate-dispatch patch fires for a capability other than `beads` (`security`/`broken-windows` were the only previously-proven `capId`s): `gsd_run check predicate` returns `block:false`/`match:true` at `violation_count:0` and `block:true`/`match:false` (`actual:"7"`, `expected:0`) at `violation_count:7`, using the predicate extracted byte-identical from the shipped `capability.json`
- Discharged the Phase 13 hard-prerequisite blocker recorded in `STATE.md`

## Task Commits

1. **Task 1: Confirm the PyPI `rumdl` package legitimacy** - checkpoint, approved by user before this session (no commit; nothing built)
2. **Task 2: End-to-end "lifecycle run measures this repo's markdown"** - `bc36422` (feat) + `c0ab16e` (chore: commit generated LINT-REPORT.md artifact)
3. **Task 3: Prove the generic ship:pre gate actually evaluates** - `1135130` (feat)

**Plan metadata:** pending (this commit)

## Files Created/Modified

- `.gsd/capabilities/markdown-linting/capability.json` - id/config/steps/gates manifest, one `verify:post` step + one advisory `ship:pre` gate
- `.gsd/capabilities/markdown-linting/config/.rumdl.toml` - curated `[global] enable=[...]` 7-rule allowlist, no `disable` key
- `.gsd/capabilities/markdown-linting/scripts/lint.py` - `resolve_rumdl_invocation`, `count_violations`, `verify_post`, `fix`, `find_project_root`/`confined` (copied from `sync.py`), `verify-post`/`count`/`fix` CLI subcommands
- `.gsd/capabilities/markdown-linting/skills/markdown-linting-report/SKILL.md` - config gate + single `verify:post` dispatch, mirrors `beads-status/SKILL.md`'s shape
- `.planning/phases/13-markdown-linting-capability-dogfood/13-LINT-REPORT.md` - generated artifact, `violation_count: 489` as of this plan's last run
- `.planning/phases/13-markdown-linting-capability-dogfood/13-GATE-SMOKE-TEST.md` - recorded live two-case predicate smoke test transcript (MDL-03)
- `.gitignore` - narrowed `.gsd/` blanket ignore to un-ignore `.gsd/capabilities/markdown-linting/` specifically (deviation, see below)
- `.planning/STATE.md` - removed the discharged Phase 13 hard-prerequisite blocker bullet

## Decisions Made

- Task 1's checkpoint (PyPI `rumdl` `SUS` verdict) was already approved by the user (`"approved"`) before this continuation agent started; per explicit resume instructions, the prior agent's automated checks (PyPI metadata cross-check, live `uvx rumdl --version`) were treated as verified and not re-run.
- `requirements mark-complete` was run for MDL-02 and MDL-03 only, not MDL-01, despite MDL-01 appearing in this plan's frontmatter `requirements` list -- see Deviations below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1/3 - blocking bug in tooling config] `.gitignore`'s blanket `.gsd/` pattern silently blocked this phase's dogfood commits**
- **Found during:** Task 2, immediately after building the four capability files -- `git status --short .gsd/` showed nothing, despite four new untracked files existing on disk.
- **Issue:** The same-day quick-task `260818-h2h` (commit `4d83504`) added a bare `.gsd/` line to `.gitignore` to stop re-tracking `beads`'/`ponytail`'s/`sota-numerics`' local runtime-install copies (whose real tracked source now lives under `plugins/<name>/.gsd/capabilities/<id>/`). That fix's blanket form has a side effect its own commit message didn't anticipate: it also silently blocks the proven, twice-repeated Phase 10/11 dogfood pattern this v1.2 milestone explicitly documents in `PROJECT.md` -- "Each ships first as a dogfooded `.gsd/capabilities/<id>/` subdirectory in this repo" -- for a brand-new capability that has no extracted plugin source tree yet. Without a fix, none of Task 2's four files could ever be committed, and Task 2's own `<done>` criterion ("...is committed") would be unsatisfiable.
- **Fix:** Changed `.gsd/` to `.gsd/*` + `!.gsd/capabilities/` + `.gsd/capabilities/*` + `!.gsd/capabilities/markdown-linting/` -- ignores capability subdirectories by default (still correctly ignoring `.gsd/capabilities/beads/` and `.gsd/capabilities/.staging/`), while explicitly un-ignoring the one capability actively being dogfooded in this repo right now.
- **Verification:** `git check-ignore -v` confirmed `markdown-linting/capability.json` is now trackable while `beads/capability.json` and `.staging/foo` remain ignored; `git status --short .gsd/` then showed exactly the four intended untracked files, no more, no less.
- **Files modified:** `.gitignore`
- **Committed in:** `bc36422` (part of Task 2's commit)

---

**Total deviations:** 1 auto-fixed (1 blocking-config fix)
**Impact on plan:** Necessary for Task 2's own done-criterion (files committed) to be satisfiable at all. No scope creep -- the fix is scoped to exactly the one capability directory this plan authors; future phases (13-02/13-03, and Phase 14's `pr-workflow`) will need their own analogous negation lines when they reach the same point, which is a small, expected, one-line addition each time, not a re-opening of this decision.

## Issues Encountered

None beyond the deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `13-02-PLAN.md` (MDL-02/MDL-04, fail-open tool-absence handling + tests) and `13-03-PLAN.md` (MDL-01/MDL-03/MDL-04, ruleset cleanup + README + 0-violations validation) can both proceed -- the underlying capability skeleton, `lint.py`'s `fix` subcommand (sole caller is 13-03 Task 1), and the live-proven gate mechanism are all in place.
- MDL-01 remains open (config wiring proven, but 0-violations-on-real-tree and the README divergence disclosure are not yet delivered) -- explicitly 13-03's scope, already reflected in that plan's own `requirements` frontmatter.
- The `.gitignore` negation pattern this plan introduced (`!.gsd/capabilities/markdown-linting/`) will need a sibling line for `pr-workflow` when Phase 14 reaches the same point, and for `get-available-resources` if/when it is un-deferred from v2.

---
*Phase: 13-markdown-linting-capability-dogfood*
*Completed: 2026-08-18*

## Self-Check: PASSED

All 7 claimed files found on disk; all 3 claimed task commits (`bc36422`, `c0ab16e`, `1135130`) found in git history.
