---
phase: 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin
plan: 02
subsystem: infra
tags: [gsd-core, capability-plugin, sota-numerics, prompt-fragments, prose-spec]

# Dependency graph
requires:
  - phase: 23-01
    provides: "quiet, legible, and efficiency/completeness dimensions defined once in executor-numerics.md and reused as bare tokens in verifier-precision.md and ship-precision-advisory.md"
provides:
  - "with the grain (project consistency) and a per-task completion-bound rule defined once in planner-sota.md, pruned from 13 to 10 lines first to fund them at no net growth"
  - "with the grain reused as a bare token in one new Flag clause in verifier-precision.md and folded into the extended confirm sentence in ship-precision-advisory.md"
  - "README `## What it changes` table's plan:pre, execute:wave:post, and ship:pre rows document the two added planner-role behaviors"
  - "all six of D-07's added dimensions (with the grain, plan completeness, quiet, legible, efficiency, completeness) present across the four fragments at 35/45 lines, 10 lines of headroom remaining"
affects: ["23-03 (version bumps and manifest description rewrites)", "23-04 (NOTES.md pruning)", "23-05 (publish 0.2.0)"]

# Actuals (#2632)
actuals:
  tokens: 2852
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Prune restatement of mechanical enforcement before adding new prose: planner-sota.md's citation-precedence and placeholder-authority clauses were deleted only because check-alternatives.py already reports the same information as a stderr remediation line on failure — the planner learns the mechanic from the gate, not from the prompt."
    - "Range-bounded line-count verification (8-10, not exact-equality 10) proves the arithmetic without letting a correct off-by-one prune fail or an incorrect same-total prune pass; the accompanying literal-token list is what actually proves no rule was lost."
    - "New dimension reused as a bare token in sibling fragments without redefinition — 'cannot tell', the tail of with the grain's definition sentence, appears exactly once across all four fragment files, confirmed by grep count."

key-files:
  created: []
  modified:
    - .gsd/capabilities/sota-numerics/fragments/planner-sota.md
    - .gsd/capabilities/sota-numerics/fragments/verifier-precision.md
    - .gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md
    - README.md

key-decisions:
  - "Task 1's three prunes were merges, not deletions: the three-line foundational-citation-pairing rule collapsed to one line preserving the Kahan/IEEE754 example and the in-window-year logic; the internal-design-alternatives marker line merged with the internal-entries rule line, dropping only the heading whitespace/case-handling restatement while keeping the two literals TestDocumentedSyntax.test_readme_and_planner_name_exact_mixed_contract pins byte for byte."
  - "with the grain and plan completeness were placed after the existing alternatives-considered guidance rather than inserted mid-file, following the same in-flow-append precedent Plan 01 used for quiet and legible in executor-numerics.md, with no 'additionally/new' framing per D-10."
  - "ship-precision-advisory.md's with-the-grain coverage extended the existing confirm sentence in place (line count unchanged at 4) rather than adding a new line, matching the plan's artifact table entry describing it as a modified cell, not a new line."

patterns-established:
  - "Bare-token literal count as a regression check: grepping for the unique tail phrase of a dimension's definition sentence across all fragment files and asserting a total of exactly 1 is a cheap, durable proof that a sibling fragment echoed the token without re-defining it."

requirements-completed:
  - D-01
  - D-02
  - D-04
  - D-05
  - D-07
  - D-08
  - D-09
  - D-10
  - D-17
  - D-20
  - D-21

coverage:
  - id: D1
    description: "planner-sota.md pruned from 13 to 10 lines by merging the three-line foundational-citation-pairing rule into one and the internal-design-alternatives marker/rule lines into one, and trimming the bullet-vs-table-precedence and placeholder-authority-filter mechanics in place, with every gate rule (including the two byte-for-byte-pinned literals) still present"
    requirement: "D-08"
    verification:
      - kind: other
        ref: "python3 -m unittest tests/test_check_alternatives.py && -k FoundationalCitationPairing (Ran 50 / Ran 3, both OK); wc -l planner-sota.md == 10; grep -F for each of 7 LOST RULE tokens all present; grep -qE 'case-sensitive|never combine|containing port' returns no match (MECHANICS-PRUNED); commit 02e3839"
        status: pass
    human_judgment: false
  - id: D2
    description: "with the grain (project consistency, defined as target behavior per D-10) and a per-task completion-bound rule added to planner-sota.md as two new lines (10 to 12), placed in flow after the alternatives guidance; README's plan:pre row documents both"
    requirement: "D-09"
    verification:
      - kind: other
        ref: "same suite plus grep -qF 'with the grain' in planner-sota.md and README.md (GRAIN-OK), grep -cE '^(#|\\s*[-*] |```)' planner-sota.md == 0, fragment total 34/45, commit e2aee65"
        status: pass
    human_judgment: false
  - id: D3
    description: "verifier-precision.md gains one Flag clause for code that does not go with the grain (naming-scheme divergence, error-shape divergence, misplaced test); ship-precision-advisory.md's confirm sentence extended to require a with-the-grain claim name its convention rather than assert it; both fragments' opening no-gate disclaimer preserved byte-identical; README's execute:wave:post and ship:pre rows updated"
    requirement: "D-04"
    verification:
      - kind: other
        ref: "same suite (Ran 50 OK) plus PLANNER-SLICE-OK (fragment total 35/45, verifier 8/9 lines, ship 4/7 lines) and DISCLAIMERS-INTACT (both opening lines byte-identical, git diff --name-only origin/main lists only the 5 expected files); grep -cF 'cannot tell' across all four fragments totals 1 (planner-sota.md only); commit 4be1407"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-09-07
status: complete
---

# Phase 23 Plan 02: Planner role slice of the extended SOTA definition (with the grain, plan completeness) Summary

**Pruned planner-sota.md's checker-internals restatement from 13 to 10 lines to self-fund two new planner dimensions — with the grain (project consistency) and per-task completion bounds — then echoed with the grain as a bare token in the verifier and ship fragments, landing the phase's full six-dimension set at 35/45 fragment lines.**

## Performance

- **Duration:** ~20min
- **Started:** 2026-09-07T00:47Z (session start per STATE.md)
- **Completed:** 2026-09-07T00:57Z
- **Tasks:** 3/3 completed
- **Files modified:** 4 (planner-sota.md, verifier-precision.md, ship-precision-advisory.md, README.md)

## Accomplishments

- Proved the plan's own arithmetic bet: three targeted merges (not deletions) took planner-sota.md from 13 to exactly 10 lines while every gate rule the planner needs — including the two literals `TestDocumentedSyntax.test_readme_and_planner_name_exact_mixed_contract` pins byte for byte in both this file and README.md — survived, confirmed by an explicit `LOST RULE:` grep loop over 7 tokens plus the full 50-test Python suite and the `TestFoundationalCitationPairing` subset.
- Funded and landed the planner's two new D-07 dimensions — **with the grain** and plan completeness — inside that reclaimed budget, taking the file to 12 lines, still under the plan's 12-line ceiling.
- Echoed **with the grain** as a bare token (no redefinition) into one new `Flag ...` clause in `verifier-precision.md` and into an extended `confirm` sentence in `ship-precision-advisory.md`, while both fragments' opening "no gate here" disclaimer stayed byte-identical.
- Closed out the phase-wide count: all six added D-07 dimensions (with the grain, plan completeness, quiet, legible, efficiency, completeness) now exist across the four fragments at 35 of the 45-line ceiling, 10 lines of headroom remaining for Plans 03-05's non-fragment refactors.

## Task Commits

Each task was committed atomically in the `sota-numerics` worktree (`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`):

1. **Task 1: Prune planner-sota.md's restatement of checker internals from 13 lines to 10** - `02e3839` (refactor)
2. **Task 2: Define "with the grain" and plan completeness in planner-sota.md** - `e2aee65` (feat)
3. **Task 3: Echo the planner dimensions in the verifier and ship fragments** - `4be1407` (feat)

**Plan metadata:** this SUMMARY, STATE.md, ROADMAP.md, REQUIREMENTS.md are committed in the `gsd-beads` repository, not the worktree — see `<final_commit>`.

## Files Created/Modified

(all paths relative to `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`)

- `.gsd/capabilities/sota-numerics/fragments/planner-sota.md` - pruned 13→10 lines (Task 1), then extended 10→12 lines with with-the-grain and plan-completeness (Task 2)
- `.gsd/capabilities/sota-numerics/fragments/verifier-precision.md` - gained one `Flag ...` clause for with-the-grain violations (7→8 lines, Task 3)
- `.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md` - extended the existing `confirm` sentence to cover with-the-grain claims (line count unchanged at 4, Task 3)
- `README.md` - `## What it changes` table's `plan:pre` row (Task 2), `execute:wave:post` and `ship:pre` rows (Task 3) document the new behaviors; five data rows preserved

## Decisions Made

- Pruned by merging, never deleting: the foundational-citation-pairing rule (3 lines → 1) and the internal-design-alternatives marker/rule (2 lines → 1) both kept every rule a planner needs, dropping only sentences that restate how `check-alternatives.py` implements the check internally — mechanics the gate's own stderr output already teaches on failure.
- Used a range bound (8-10 lines, not exact 10) for Task 1's line-count check, per the plan's own reasoning: exact equality would fail a correct prune landing at 9 and pass an incorrect one landing at 10. The literal `LOST RULE:` token list is what actually proves no rule was lost.
- Placed the two new planner lines in flow after the existing alternatives-considered guidance (not inserted mid-file, not appended after an explicit break), mirroring how Plan 01 appended quiet and legible to executor-numerics.md — one standard that grew, not two sharing a file.
- Extended ship-precision-advisory.md's existing `confirm` sentence in place for the with-the-grain claim rather than adding a new line, since the plan's own artifact table describes this as a modified cell.

## Deviations from Plan

None — plan executed exactly as written. All three tasks' verification blocks passed on the first attempt with no auto-fixes.

## Issues Encountered

None. The recursion-guard digest for the installed global mirror (`${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics`) was re-verified with the plan's exact command after every task and never moved from `3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e`. The plugin's `capability-auto-install.sh` SessionStart/SubagentStart hook fired on each verification's shell-suite invocation (as expected per `.wolf/cerebrum.md`'s 2026-09-07 entry) and correctly refused to install the uncommitted worktree bundle at global scope each time, printing `capability-auto-install: sota-numerics bundle has uncommitted changes; refusing to install it at global scope`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All six D-07 dimensions are now defined and cross-referenced across the four fragments at 35/45 lines; the phase's fragment-content work is complete after this plan.
- Branch `feat/extended-sota-definition` now holds five commits on top of the two pre-existing, deliberately untouched hook-fix commits (`6e1d61c`, `9b36af2`).
- No blockers for Plan 03 (version bumps and manifest description rewrites), Plan 04 (NOTES.md pruning), or Plan 05 (publish 0.2.0).

---
*Phase: 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin*
*Completed: 2026-09-07*

## Self-Check: PASSED

All four modified files found on disk in the sota-numerics worktree; all three task commits (`02e3839`, `e2aee65`, `4be1407`) found in `git log --oneline --all`.
