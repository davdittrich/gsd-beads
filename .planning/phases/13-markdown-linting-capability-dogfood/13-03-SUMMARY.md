---
phase: 13-markdown-linting-capability-dogfood
plan: 03
subsystem: infra
tags: [rumdl, markdownlint-cli2, gsd-core-capability, gate-predicate, markdown-linting, fail-open]

requires:
  - phase: 13-01
    provides: "markdown-linting capability.json wired end to end: verify:post -> markdown-linting-report skill -> lint.py -> LINT-REPORT.md; lint.py's fix subcommand; the live-proven generic ship:pre gate dispatch"
  - phase: 13-02
    provides: "lint.py verify_post()'s MDL-04 fail-open sentinel path (violation_count: unavailable) and the 10-test regression suite"
provides:
  - "The real .planning/ + README.md + CLAUDE.md tree at 0 rumdl violations under the curated 7-rule allowlist, achieved via a spot-checked, structural-token-proven mechanical auto-fix"
  - "The capability's public README: ruleset + disabled-rule rationale, three D-04 install tiers, phase-scoped-artifact rationale, and a freshly measured (2026-08-18, commit 866d071) rumdl-vs-markdownlint-cli2 divergence table"
  - "Live-recorded proof of both remaining MDL-03/MDL-04 success criteria: a nonzero violation_count ships with a visible advisory line and never halts (blocking: false); a simulated rumdl+uvx absence yields exactly one notice, exit 0, and a sentinel the gate reads as unsatisfied"
affects: [14-pr-workflow, 15-capability-extraction]

actuals:
  tokens: 56700
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Structural-token multiset diff (R-02): grep -rhoE over sync.py's six regex anchors (task tags, name/beads-id tags, depends_on:, beads_epic:, frontmatter ---), captured before/after a repo-wide automated rewrite and diffed for exact equality -- cheaper and stricter than re-running a bd-dependent parser sweep, reusable for any future mass-rewrite of .planning/"
    - "Scratch-PATH tool-absence simulation: when the tool-under-test shares its binary directory with the interpreter needed to invoke the wrapper script, exclude just the tool by symlinking only the interpreter into an empty scratch dir and setting PATH to that dir alone, rather than stripping the whole real bin directory"

key-files:
  created:
    - .gsd/capabilities/markdown-linting/README.md
  modified:
    - .planning/**/*.md (114 files: mechanical rumdl --fix pass plus one hand-resolved MD024)
    - README.md (already clean, no diff)
    - CLAUDE.md (already clean, no diff after the prep-commit isolation below)
    - .planning/phases/13-markdown-linting-capability-dogfood/13-GATE-SMOKE-TEST.md
    - .planning/phases/13-markdown-linting-capability-dogfood/13-LINT-REPORT.md

key-decisions:
  - "Isolated pre-existing, unrelated uncommitted working-tree state (CLAUDE.md's beads-integration block silently stripped by a capability consent-hash mismatch, .gsd-capabilities.json's timestamp, STATE-ARCHIVE.md's auto-pruned entries, API-SURFACE.md's staleness note, and the untracked 13-01/02 pattern-mapper artifact 13-PATTERNS.md) into its own prep commit before Task 1's fixer ran, so Task 1's diff -- and its D-01 spot-check -- stayed isolated to mechanical lint fixes only, per CLAUDE.md's Surgical Changes directive"
  - "The one rumdl-unfixable residual this session was an MD024 duplicate '## Common Pitfalls' heading in archived 04-RESEARCH.md (not the MD001 the plan's read_first anticipated from a prior session's measurement -- the corpus had already changed). The second heading's own body text said 'merged into the single Common Pitfalls section... duplicate heading omitted', so it was demoted from a heading to bold text rather than renamed or deleted -- preserves the archival note verbatim while resolving MD024"
  - "The divergence table's post-fix measurement (rumdl 0 vs markdownlint-cli2 309, all MD022/MD024) is fundamentally different in shape from the pre-fix session's 471-vs-708 figure cited in RESEARCH.md/REQUIREMENTS.md: Task 1 fixed every violation rumdl itself detects, so the residual divergence is now 100% composed of cases rumdl's own detector never flags at all, not unfixed residue -- README frames this explicitly as the honest post-fix baseline, not a copy of either stale figure"
  - "Task 3's advisory-gate test injected the nonzero violation_count into the real 13-LINT-REPORT.md (per the plan's literal instruction), not a scratch copy like plan 01's two-case test -- backed up first, restored via a live verify-post run immediately after, confirmed via git diff that only generated_at changed in the final committed state"

patterns-established:
  - "Prep-commit isolation of pre-existing dirty state before a wide automated-rewrite task, so the rewrite's own diff stays spot-checkable"

requirements-completed: [MDL-01, MDL-03, MDL-04]

coverage:
  - id: D1
    description: "python3 lint.py count reports 0 for the combined D-02 target set and each of the three scopes (.planning, README.md, CLAUDE.md) independently"
    requirement: MDL-01
    verification:
      - kind: integration
        ref: "python3 .gsd/capabilities/markdown-linting/scripts/lint.py count / count .planning / count README.md / count CLAUDE.md -- all 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "Structural-token multiset (task tags, name/beads-id tags, depends_on:, beads_epic:, frontmatter ---) across .planning/**/*.md is byte-identical before and after the fix pass (R-02); verify.plan-structure task_count unchanged for 13-01/02/03-PLAN.md"
    requirement: MDL-01
    verification:
      - kind: integration
        ref: "diff -u /tmp/mdl-tokens.before /tmp/mdl-tokens.after -- empty, exit 0"
        status: pass
      - kind: integration
        ref: "gsd_run query verify.plan-structure on 13-01/02/03-PLAN.md -- task_count 3/2/3, unchanged"
        status: pass
    human_judgment: false
  - id: D3
    description: "git diff --numstat shows no changed file outside .planning/, README.md, CLAUDE.md; docs/ untouched"
    requirement: MDL-01
    verification:
      - kind: integration
        ref: "git diff --numstat | awk '{print $3}' filtered against the D-02 scope -- empty result; git status --short docs/ -- empty"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every mechanical hunk in the auto-fix diff is meaning-preserving (blank-line/whitespace/language-tag changes only); the one hand-resolved MD024 preserves the archival note's meaning"
    verification: []
    human_judgment: true
    rationale: "Diff meaning-preservation across 114 files is a human spot-check per D-01's own instruction, not fully machine-provable; sampled the largest diffs (01-RESEARCH.md, ARCHITECTURE.md, FEATURES.md) plus the one hand edit during execution -- all confirmed mechanical, but a second human pass is the plan's own designed check."
  - id: D5
    description: "Capability README names all 7 enabled + 3 disabled rules with reasons, documents all 3 D-04 install tiers, the phase-scoped-artifact rationale, both config keys with the MDL-05 note, and a date+sha-stamped divergence table with no stale 45%/14-vs-1 figures"
    requirement: MDL-01
    verification:
      - kind: integration
        ref: "grep -qF token-presence loop over MD001..MD041/markdownlint-cli2/uvx/ship_gate + date-regex + sha match against git rev-parse --short HEAD, plus negative greps for the stale figures -- all pass"
        status: pass
    human_judgment: false
  - id: D6
    description: "A nonzero violation_count in the real LINT-REPORT.md produces a visible advisory line naming the count via ship.md's blocking:false template, and the ship does not halt"
    requirement: MDL-03
    verification:
      - kind: integration
        ref: "gsd_run check predicate against the real 13-LINT-REPORT.md with violation_count: 12 injected -- block:true, actual:'12'; ship.md step 8(c) template applied verbatim, recorded in 13-GATE-SMOKE-TEST.md Step 3"
        status: pass
    human_judgment: false
  - id: D7
    description: "Simulated rumdl+uvx absence for one verify-post invocation yields exactly one notice, exit 0, no hang, and violation_count: unavailable; the gate reads that sentinel as unsatisfied, not clean; no installation was removed"
    requirement: MDL-04
    verification:
      - kind: integration
        ref: "PATH-scoped verify-post run (scratch dir containing only a python3 symlink) -- one NOTICE line, exit 0, sentinel report; gsd_run check predicate against the sentinel -- block:true, actual:'unavailable'; recorded in 13-GATE-SMOKE-TEST.md Step 4"
        status: pass
    human_judgment: false
  - id: D8
    description: "The committed 13-LINT-REPORT.md ends the plan at violation_count: 0 from a real rumdl run, not a hand-set or sentinel value"
    verification:
      - kind: integration
        ref: "grep -qE '^violation_count: 0$' .planning/.../13-LINT-REPORT.md; git diff shows only generated_at changed from the pre-Task-3 committed state"
        status: pass
    human_judgment: false

duration: ~12min
completed: 2026-08-18
status: complete
---

# Phase 13 Plan 03: Zero-violation cleanup, capability README, and live gate-behavior proof Summary

**Fixed 488/489 rumdl violations mechanically across 114 `.planning/`+`README.md`+`CLAUDE.md` files, hand-resolved the one MD024 residual, published the capability's README with a freshly measured 0-vs-309 rumdl/markdownlint-cli2 divergence table, and live-proved both the advisory-ship and rumdl-absent gate behaviors against the real `LINT-REPORT.md`.**

## Performance

- **Duration:** ~12min
- **Started:** 2026-08-18T12:34:58Z
- **Completed:** 2026-08-18T12:42:25Z
- **Tasks:** 3/3
- **Files modified:** 118 (114 in Task 1's fix pass, 1 created in Task 2, 2 modified in Task 3 -- `13-LINT-REPORT.md` touched by both Task 1 and Task 3)

## Accomplishments

- Ran `lint.py fix` over the full D-02 scope: 488 of 489 violations auto-fixed (blank lines around headings, trailing-whitespace/blank-line collapse, fenced-code language tags); hand-resolved the one MD024 duplicate-heading residual in archived `04-RESEARCH.md` by demoting an already-vestigial "see above, duplicate omitted" stub heading to bold text
- Proved the auto-fix touched nothing but formatting: a before/after structural-token multiset (task tags, name/beads-id tags, `depends_on:`, `beads_epic:`, frontmatter `---`) across `.planning/**/*.md` diffed byte-identical (R-02), and `verify.plan-structure`'s `task_count` was unchanged for all three in-flight Phase 13 plans
- All four D-02 scopes (combined, `.planning`, `README.md`, `CLAUDE.md`) now report `0` violations; `13-LINT-REPORT.md` regenerated to `violation_count: 0` from a real `rumdl` run
- Published `.gsd/capabilities/markdown-linting/README.md`: the verify:post/ship:pre flow with phase-scoped-artifact rationale, both config keys (`markdown-linting.enabled`/`ship_gate`, with the MDL-05 blocking-flip note), all three D-04 install tiers (including why the PyPI `SUS` verdict is a rolling-release false positive), the 7-rule curated allowlist plus the 3 disabled rules' reasons, and a fresh divergence table measured this session at commit `866d071`: rumdl `0` vs `markdownlint-cli2` `309` (all MD022/MD024) -- a materially different shape from the pre-fix session's 471-vs-708 figure, since every case rumdl itself flags is now fixed and the residual is 100% cases rumdl's detector never catches at all
- Appended two live-behavior transcript sections to `13-GATE-SMOKE-TEST.md`: injecting `violation_count: 12` into the real report and applying `ship.md`'s patched advisory template verbatim produces `⚠ markdown-linting advisory: Frontmatter field "violation_count" in LINT-REPORT.md is 12, expected 0` without halting (MDL-03 criterion 4); simulating `rumdl`+`uvx` absence for one `verify-post` invocation (a scratch `PATH` with only a `python3` symlink, since both tools share `/usr/bin` with the interpreter) produced exactly one notice, exit `0`, and a `violation_count: unavailable` sentinel the gate correctly reads as `block: true` (MDL-04 criterion 5)
- Restored the real `13-LINT-REPORT.md` to `violation_count: 0` from a live `rumdl` run after each simulated test, so the committed report never carries an injected or sentinel value

## Task Commits

0. **Prep (not a plan task): isolate pre-existing background state** - `4c797a3` (chore) -- see Deviations below
1. **Task 1: Bring the lint scope to 0 violations via mechanical auto-fix (D-01, MDL-01)** - `866d071` (fix)
2. **Task 2: Capability README with freshly measured divergence disclosure (MDL-01)** - `599b221` (docs)
3. **Task 3: Confirm advisory ship behavior and the rumdl-absent cycle (MDL-03, MDL-04)** - `d37a992` (test)

**Plan metadata:** pending (this commit)

## Files Created/Modified

- `.gsd/capabilities/markdown-linting/README.md` - ruleset, install tiers, artifact-path rationale, divergence disclosure
- `.planning/**/*.md` (114 files) - mechanical rumdl fix pass; `04-RESEARCH.md` additionally hand-edited for the MD024 residual
- `.planning/phases/13-markdown-linting-capability-dogfood/13-GATE-SMOKE-TEST.md` - Step 3/4 live transcripts appended
- `.planning/phases/13-markdown-linting-capability-dogfood/13-LINT-REPORT.md` - regenerated at `violation_count: 0`, final `generated_at` from Task 3's restore run

## Decisions Made

- Isolated pre-existing, unrelated uncommitted working-tree state into its own prep commit (`4c797a3`) before Task 1's fixer ran (see Deviations).
- Hand-resolved the MD024 residual by demoting the vestigial second "## Common Pitfalls" heading to bold text rather than deleting or renaming it -- preserves the archival note's meaning exactly.
- Measured the divergence table fresh at commit `866d071` (post-Task-1) rather than reusing either RESEARCH.md's or REQUIREMENTS.md's pre-fix figures, per the plan's explicit instruction -- the two are not comparable shapes (pre-fix vs. post-fix corpus).
- Injected Task 3's nonzero-count test into the real `13-LINT-REPORT.md` (per the plan's literal wording), backed up first and restored via a live `verify-post` run immediately after.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking issue] Isolated pre-existing unrelated dirty working-tree state before Task 1's fixer ran**
- **Found during:** Pre-Task-1 setup, before capturing the structural-token baseline
- **Issue:** The working tree already had uncommitted changes at session start, unrelated to this plan: `.gsd-capabilities.json`'s `updatedAt` timestamp, `.planning/STATE-ARCHIVE.md`'s auto-pruned entries, `.planning/intel/API-SURFACE.md`'s staleness note, `CLAUDE.md`'s beads-integration block (silently stripped, apparently by a capability consent-hash mismatch per `PROJECT.md`'s Phase 6/10 decision log), and an untracked `13-PATTERNS.md` pattern-mapper artifact from earlier planning. `STATE-ARCHIVE.md` and `CLAUDE.md` are both inside Task 1's D-02 lint scope, so committing Task 1's fix on top of this dirty state would have bundled unrelated hunks into a commit meant to be a pure, spot-checkable mechanical diff -- violating both the plan's D-01 spot-check design and CLAUDE.md's Surgical Changes directive.
- **Fix:** Committed the five pre-existing files separately as `4c797a3` with an honest message describing them as pre-existing background state, before running `lint.py fix`. Left `.claude/` (local tool state: `settings.json`, `settings.local.json`, `scheduled_tasks.lock`) untouched -- out of scope for this plan, not part of the D-02 target set.
- **Verification:** `git status --short` confirmed a clean tree (`.claude/` only) before Task 1's baseline capture; Task 1's own diff (`866d071`) touched only the D-02 scope with no unrelated hunks.
- **Files modified:** `.gsd-capabilities.json`, `.planning/STATE-ARCHIVE.md`, `.planning/intel/API-SURFACE.md`, `CLAUDE.md`, `.planning/phases/13-markdown-linting-capability-dogfood/13-PATTERNS.md` (new)
- **Committed in:** `4c797a3` (separate prep commit, not part of Task 1/2/3's own commits)

**2. [Rule 1 - bug] Self-introduced MD040 violations while authoring Task 3's transcript, fixed before commit**
- **Found during:** Task 3, immediately after appending the two new sections to `13-GATE-SMOKE-TEST.md`
- **Issue:** Five new fenced code blocks in the appended transcript sections omitted language tags, reintroducing 5 violations into a file this plan's own Task 1 had just brought to 0 -- `python3 lint.py count` returned `5` instead of `0` after the edit.
- **Fix:** Ran `lint.py fix .../13-GATE-SMOKE-TEST.md`; all 5 auto-fixed to `text` language tags.
- **Verification:** `python3 lint.py count` returned `0` again for the full D-02 scope; Task 3's automated verify (the `unavailable`/`violation_count: 0` greps) still passed.
- **Files modified:** `.planning/phases/13-markdown-linting-capability-dogfood/13-GATE-SMOKE-TEST.md`
- **Committed in:** `d37a992` (part of Task 3's commit, fixed before staging)

---

**Total deviations:** 2 auto-fixed (1 blocking-scope-isolation prep commit, 1 self-introduced-then-fixed bug)
**Impact on plan:** Necessary to keep Task 1's diff spot-checkable and to preserve the plan's own 0-violation invariant through Task 3's own edits. No scope creep -- the prep commit touches only files that were already dirty before this session started, and the MD040 self-fix reverts an omission this session itself made.

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 13 (`markdown-linting-capability-dogfood`) is now feature-complete against all four MDL requirements: MDL-01 (0 violations + README disclosure, this plan), MDL-02/MDL-03 (13-01), MDL-04 (13-02, and this plan's Task 3 live-cycle confirmation of criterion 5).
- MDL-05 (`markdown-linting.ship_gate` flipping to blocking) remains explicitly deferred to v2 in `STATE.md`'s Deferred Items, pending a clean full-milestone run.
- The divergence table's `309`-issue markdownlint-cli2 gap (all MD022/MD024, none of them rumdl-detectable at all) is disclosed as a known, accepted tradeoff in the README, not a follow-up bug -- future phases adding `.planning/` content will drift this figure further and should re-measure per the README's own stated caveat.

---
*Phase: 13-markdown-linting-capability-dogfood*
*Completed: 2026-08-18*

## Self-Check: PASSED

All 3 claimed files found on disk (`.gsd/capabilities/markdown-linting/README.md`,
`13-GATE-SMOKE-TEST.md`, `13-LINT-REPORT.md`); all 4 claimed commits (`4c797a3`, `866d071`,
`599b221`, `d37a992`) found in git history.
