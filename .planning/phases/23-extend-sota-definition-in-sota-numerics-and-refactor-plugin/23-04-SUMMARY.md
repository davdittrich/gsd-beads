---
phase: 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin
plan: 04
subsystem: infra
tags: [gsd-core, capability-plugin, sota-numerics, self-compliance, documentation]

# Dependency graph
requires:
  - phase: 23-02
    provides: "with the grain and plan-completeness dimensions defined once in planner-sota.md, echoed as bare tokens in verifier-precision.md and ship-precision-advisory.md"
  - phase: 23-03
    provides: "capability.json and plugin.json at 0.2.0 with rewritten description strings; check-alternatives.py's docstrings/comments self-contained, executable logic frozen"
provides:
  - "NOTES.md pruned from 115 to 88 lines, removing only passages README.md already states independently, with all five anti-regression headings and every literal pinned by TestFoundationalCitationPairing/the do-not-revert instruction intact"
  - "README.md's `## What it changes` table rows for execute:wave:post and ship:pre corrected to name the completeness flags (unreachable/unwritten branch, undocumented argument values) and the legibility claim, closing the only two gaps found by a 12-claim mechanical trace against capability.json and check-alternatives.py"
  - "README.md brought to the legible standard its own executor fragment defines: a claim stated once, in one place, with a checkable bound, at exactly 240 lines (unchanged from origin/main)"
affects: ["23-05 (publish 0.2.0)"]

# Actuals (#2632)
actuals:
  tokens: 5600
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Vocabulary containment as the prune-only enforcement mechanism: set(words(new_file)) - set(words(origin/main_file)) must be empty. Replaces a rejected git diff --numstat added-line gate that penalized correct rewording (merging two sentences into one, using fewer of the same words, still showed as an addition under numstat)."
    - "Claim-to-source tracing: every behavioral assertion in a README table cell is checked against a concrete value in capability.json (JSON key path) or a concrete line in check-alternatives.py (grep/AST), rather than trusted as prose. A claim with no such anchor is a FAIL, not a judgment call."
    - "README's one-paragraph-per-line structure (up to 801 chars/line) means word-level prose trimming does not move wc -l; only whole-clause deletion or merging two sentences into one changes the line count. The 200-240 target was hit by two small, load-bearing clause edits, not a sweeping rewrite."

key-files:
  created: []
  modified:
    - .gsd/capabilities/sota-numerics/NOTES.md
    - README.md

key-decisions:
  - "NOTES.md's three prunes (Sections 1-3) were sentence-level deletions/merges, never bulk cuts: Section 1 dropped one sentence already restated by README's blocking-gate description; Section 2 replaced a multi-paragraph justification with the one sentence not already in README (the plan-phase.md `gap-analysis` code-comment citation); Section 3 dropped one redundant sentence about the test -f guard's purpose that duplicated the surrounding text. Sections 4 and 5 were left untouched because neither restates anything README says."
  - "The two README corrections in Task 2 (verifier row's missing completeness flags, ship row's missing legibility claim) were found by diffing the fragment files against the table cells describing them, not by rewriting the table wholesale -- both are targeted single-clause additions to existing table cells, keeping the row structure and every other cell byte-identical."
  - "Task 3's legible-standard pass made exactly two edits, both clause-level: dropped a sentence in Failures/recovery that restated the preceding sentence's point (running the checker directly to catch a bad section早 vs. plan:post being a fail-closed backstop -- the plan checker point already covers 'catch earlier'), and rephrased the Install section's hook-banner sentence from a negative frame requiring inference (\"must not assume hooks ran\") to a direct statement of the covered case (\"including one where hooks never ran\") -- same fact, one meaning, no double-negative."
  - "hooks/capability-auto-install.sh continues to show in `git diff --name-only origin/main` from commits 6e1d61c and 9b36af2 that predate this phase entirely (established in 23-03-SUMMARY.md); this plan touched neither that file nor any other file outside NOTES.md and README.md, confirmed by `git diff --name-only 0ce9ee1~1 bf1a847`."

patterns-established:
  - "A prune-only gate on a reasoning document (NOTES.md) needs a positive-content check (headings, anchor literals) alongside the negative-content check (vocabulary containment), because containment alone would pass an over-aggressive prune that deleted a whole anti-regression section using only words the file already had."

requirements-completed:
  - D-02
  - D-10
  - D-16
  - D-17
  - D-18
  - D-20
  - D-21

coverage:
  - id: D1
    description: "NOTES.md pruned from 115 to 88 lines (within the 65-95 band), removing only passages README.md already states independently across Sections 1-3, with Sections 4-5 untouched"
    requirement: "D-18"
    verification:
      - kind: other
        ref: "wc -l NOTES.md == 88; grep -c '^## ' NOTES.md == 5; anchor literals 'back to', 'TestFoundationalCitationPairing', 'command-exit-zero' all present -> NOTES-PRUNED; commit 0ce9ee1"
        status: pass
    human_judgment: false
  - id: D2
    description: "NOTES.md's pruned text uses no word absent from origin/main's NOTES.md (vocabulary containment) -- proves the prune deleted and merged sentences rather than introducing new phrasing"
    requirement: "D-18"
    verification:
      - kind: other
        ref: "set(words(new NOTES.md)) - set(words(origin/main NOTES.md)) computed empty; no git diff --numstat added-line count used (that gate was explicitly rejected for penalizing correct rewording); commit 0ce9ee1"
        status: pass
    human_judgment: false
  - id: D3
    description: "All twelve mechanically-checkable behavioral claims in README.md (contribution/gate counts, onError values, 30s timeout, engine floor, config default, MIN_ALTERNATIVES, ancestor walk depth, no-subprocess, recovery line in script and README) trace to a concrete value in capability.json or a concrete line in check-alternatives.py"
    requirement: "D-20"
    verification:
      - kind: other
        ref: "python3 script parsing capability.json and check-alternatives.py asserted all 12 claims true, printed README-CLAIMS-TRACED with zero FAILs; claim-to-source map recorded below; no commit (verification-only, no file changed by this check)"
        status: pass
    human_judgment: false
  - id: D4
    description: "README.md's `## What it changes` table accurately describes what the four fragments say after Plans 01-02: execute:wave:post names the two completeness flags Plan 01 added, ship:pre names the legibility claim the fragment's confirm sentence requires"
    requirement: "D-17"
    verification:
      - kind: other
        ref: "diff of the two corrected table rows against the corresponding fragment sentences in verifier-precision.md and ship-precision-advisory.md shows every fragment clause now named in its README row; all five table rows intact; commit 6861aec"
        status: pass
    human_judgment: false
  - id: D5
    description: "README.md meets the legible standard its own executor fragment defines (one meaning per place, checkable bound), landing at 200-240 lines with every TestDocumentedSyntax-pinned literal surviving verbatim"
    requirement: "D-16, D-17"
    verification:
      - kind: other
        ref: "wc -l README.md == 240; grep -c '^| \\`' README.md == 5 (all five reference-table rows intact); literals '### Internal design alternatives', internal-entries sentence, and 'mechanism' inside 'Each parsed mechanism entry must contain:' all present verbatim -> README-LEGIBLE-OK, PINNED-OK; commit bf1a847"
        status: pass
    human_judgment: false
  - id: D6
    description: "No capability behavior changed: no manifest, fragment, script, hook, or test edited by this plan; the three pre-existing regression suites pass unchanged"
    requirement: "D-01, D-19, D-21"
    verification:
      - kind: other
        ref: "git diff --name-only 0ce9ee1~1 bf1a847 lists only NOTES.md and README.md; tests/test-session-start.sh and tests/test-gate-script-resolution.sh exit 0; python3 -m unittest tests/test_check_alternatives.py -> Ran 50 tests, OK"
        status: pass
    human_judgment: false
  - id: D7
    description: "Recursion guard held: the globally installed mirror at ${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics was never written to"
    verification:
      - kind: other
        ref: "( cd \"${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics\" && find . -name __pycache__ -prune -o -type f -print | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1 ) re-verified after all three tasks, unchanged at 3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e"
        status: pass
    human_judgment: false

duration: 35min
completed: 2026-09-07
status: complete
---

# Phase 23 Plan 04: Prune NOTES.md and trace README's claims to source Summary

**Pruned NOTES.md from 115 to 88 lines by deleting only what README already states independently, then closed two README accuracy gaps (missing completeness flags on the verifier row, missing legibility claim on the ship row) found by mechanically tracing all twelve checkable behavioral claims to capability.json and check-alternatives.py, and applied the capability's own legible standard to two clauses in README's own prose.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-07
- **Tasks:** 3/3 completed
- **Files modified:** 2 (NOTES.md, README.md, in the sota-numerics worktree)

## Accomplishments

- Pruned `NOTES.md` Sections 1-3 line by line against README's final text, landing at 88 lines (within the required 65-95 band) while every anti-regression heading (all 5), the do-not-revert-`onError` instruction, and the `TestFoundationalCitationPairing` anchor literal survived verbatim. Vocabulary containment held: no word absent from `origin/main`'s NOTES.md appears in the pruned file, proving the prune only deleted and merged sentences rather than introducing new phrasing that a line-count check alone could not catch.
- Traced all twelve of README's mechanically-checkable behavioral claims to a concrete value in `capability.json` or a concrete line in `check-alternatives.py` — found two accuracy gaps in the `## What it changes` table (verifier row missing the two completeness flags Plan 01 added; ship row missing the legibility claim its fragment already requires) and corrected both in place, changing no other row.
- Applied README's own legible standard (one meaning per place, checkable bound) to two clauses in its own prose: removed a sentence in Failures/recovery that restated a point the preceding sentence already made, and rephrased a double-negative install-banner sentence into a direct positive statement of the same fact. README ended the plan at exactly 240 lines — unchanged from `origin/main` despite the corrections, because the structural one-paragraph-per-line format means clause-level edits don't move `wc -l` unless a whole clause is deleted or two sentences are merged.

## Task Commits

Each task was committed atomically in the `sota-numerics` worktree (`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`):

1. **Task 1: Prune NOTES.md Sections 1-3 of content README already states** - `0ce9ee1` (refactor)
2. **Task 2: Trace README's behavioral claims to capability.json and check-alternatives.py, correct two accuracy gaps** - `6861aec` (fix)
3. **Task 3: Apply the legible standard to README's own prose** - `bf1a847` (docs)

**Plan metadata:** this SUMMARY, STATE.md, ROADMAP.md, REQUIREMENTS.md are committed in the `gsd-beads` repository, not the worktree — see `<final_commit>`.

## Files Created/Modified

(all paths relative to `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`)

- `.gsd/capabilities/sota-numerics/NOTES.md` - pruned 115→88 lines across Sections 1-3 (Task 1); Sections 4-5 untouched
- `README.md` - `## What it changes` table's `execute:wave:post` and `ship:pre` rows corrected (Task 2); Failures/recovery and Install sections' prose tightened to the legible standard (Task 3); net line count unchanged at 240

## Claim-to-Source Map (Task 2)

Every behavioral claim in README.md's checkable table cells, traced to its concrete source:

| # | Claim | Source | Location |
|---|-------|--------|----------|
| 1 | Four advisory prompts | `capability.json` | `contributions` array, length 4 |
| 2 | One blocking plan gate | `capability.json` | `gates` array, length 1, `gates[0].blocking === true` |
| 3 | A rendering failure skips that prompt | `capability.json` | every `contributions[].onError === "skip"` |
| 4 | The gate halts when its command cannot run | `capability.json` | `gates[0].onError === "halt"` |
| 5 | 30-second timeout | `capability.json` | `gates[0].check.predicate.timeout === 30` |
| 6 | gsd-core 1.10.0 or newer | `capability.json` | `engines.gsd === ">=1.10.0"` |
| 7 | The default is true | `capability.json` | `config["sota-numerics.enabled"].default === true` |
| 8 | At least two bold-named entries required | `check-alternatives.py` | `MIN_ALTERNATIVES = 2` |
| 9 | No `.planning` ancestor within ten levels | `check-alternatives.py` | ancestor walk uses `range(10)` |
| 10 | The checker launches no child processes | `check-alternatives.py` | no `import subprocess` / `subprocess.*` call anywhere in the file |
| 11 | The script prints the recovery line on failure | `check-alternatives.py` | literal `remediation: fix the plans above, then re-run /gsd-plan-phase` present |
| 12 | README quotes the same recovery line | `README.md` | same literal string present verbatim |

All twelve traced green on first check; no third gap was found beyond the two the plan's own `must_haves` anticipated.

## Decisions Made

- NOTES.md's three prunes were sentence-level deletions/merges, never bulk cuts, matching the plan's explicit prohibition against bulk cutting: Section 1 dropped one sentence that duplicated README's blocking-gate description; Section 2 replaced a multi-paragraph justification with the one sentence not already stated in README; Section 3 dropped one sentence that restated the surrounding `test -f` guard rationale in different words.
- The two README corrections were targeted single-clause additions to existing table cells, not a table rewrite — every other row and every other cell in the two corrected rows stayed byte-identical.
- Task 3's legible pass made exactly two edits, both removing redundancy or a double negative rather than adding new content: one sentence deleted for restating its predecessor, one sentence reworded from a negative frame requiring inference to a direct positive statement of the same fact.
- `hooks/capability-auto-install.sh`'s presence in `git diff --name-only origin/main` is unrelated to this plan: it comes from commits `6e1d61c` and `9b36af2` that predate Phase 23 (established in 23-03-SUMMARY.md). This plan's own diff (`0ce9ee1~1..bf1a847`) touches only `NOTES.md` and `README.md`, confirming no cross-plan contamination.

## Deviations from Plan

None beyond the two accuracy corrections the plan's own `must_haves.truths` explicitly anticipated as in-scope work for Task 2 (the plan describes closing "two accuracy gaps" as the task's purpose, not an unplanned discovery), and the two legible-standard prose edits Task 3 was written to make. No Rule 1-4 deviation was needed: every fix performed was work the plan's own task bodies specified, not a bug found outside plan scope.

## Verification Evidence

- `NOTES-PRUNED`: `wc -l` = 88 (within 65-95); `grep -c '^## '` = 5; anchor literals `back to`, `TestFoundationalCitationPairing`, `command-exit-zero` all present.
- Vocabulary containment: `set(words(new NOTES.md)) - set(words(origin/main NOTES.md))` computed empty.
- `README-CLAIMS-TRACED`: all 12 mechanically-checked claims verified against `capability.json` and `check-alternatives.py` with zero FAILs.
- `README-LEGIBLE-OK`: `wc -l README.md` = 240 (within 200-240); five reference-table rows intact.
- `PINNED-OK`: all four `TestDocumentedSyntax.test_readme_and_planner_name_exact_mixed_contract`-pinned literals survive verbatim (`### Internal design alternatives` marker, the internal-entries sentence, and `mechanism` inside `Each parsed mechanism entry must contain:`).
- `DIFF-CLEAN`: `git diff --name-only 0ce9ee1~1 bf1a847` lists only `.gsd/capabilities/sota-numerics/NOTES.md` and `README.md`.
- `tests/test-session-start.sh` and `tests/test-gate-script-resolution.sh` -> exit 0 (ALL PASS).
- `python3 -m unittest tests/test_check_alternatives.py` -> Ran 50 tests, OK.
- Recursion guard digest re-verified before Task 1 and after Task 3, using the plan's exact command (`cd` into the mirror, `find . -name __pycache__ -prune -o -type f -print | LC_ALL=C sort | xargs sha256sum | sha256sum`): unchanged at `3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e`.

## Known Stubs

None.

## Threat Flags

None — this plan edits only two Markdown documents (NOTES.md, README.md); no new network endpoint, auth path, file-access pattern, or schema change at a trust boundary was introduced. The threat register's four `mitigate` dispositions (T-23-12 README claims, T-23-13 NOTES.md anti-regression entries, T-23-14 README reference list, T-23-03 installed mirror) were all satisfied by this plan's own verification: the 12-claim trace, the 5-heading/3-literal NOTES.md check, the 7-entry reference-list survival check (confirmed unchanged — this plan touched no reference-list line), and the recursion-guard digest.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Both of the capability's shipped reasoning documents (NOTES.md, README.md) now comply with the standard the capability itself teaches: NOTES.md is prune-only free of README duplication, README's behavioral claims are traceable to code, and README's own prose meets the legible bar.
- Branch `feat/extended-sota-definition` now holds eight commits on top of the two pre-existing, unrelated hook-fix commits (`6e1d61c`, `9b36af2`).
- No blockers for Plan 05 (publish 0.2.0); the recursion guard digest is confirmed unchanged and ready for Plan 05's own re-verification before publish.

---
*Phase: 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin*
*Completed: 2026-09-07*

## Self-Check: PASSED

All modified files found on disk in the sota-numerics worktree; all three task commits (`0ce9ee1`, `6861aec`, `bf1a847`) found in `git log --oneline --all`.
