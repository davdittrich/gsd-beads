---
phase: quick-260908-gzq
plan: 01
quick_id: 260908-gzq
subsystem: sota-numerics
tags: [python, unittest, gate-script, check-alternatives]

requires:
  - phase: 24-remediate-sota-numerics-0-2-0-release-blockers
    provides: the deferred-out ticket (gsd-beads-25vc.21.1) naming these three findings
provides:
  - "next_comment_opener(): backtick-protected <!-- candidates no longer blank a plan to EOF"
  - "symlinked .planning/phases/ entries are skipped during phase-directory discovery"
  - "an unreadable plan-shaped path (directory or unreadable file) maps to the documented exit-2 contract"
affects: [sota-numerics-release, gsd-beads-25vc.21]

actuals:
  tokens: 4986
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "same-line bounded inline-code-span regex (INLINE_CODE_SPAN_RE) mirroring DOC_REF_RE's shape, sited beside next_fence_opener"

key-files:
  created: []
  modified:
    - .gsd/capabilities/sota-numerics/scripts/check-alternatives.py
    - tests/test_check_alternatives.py
    - README.md
    - CHANGELOG.md

key-decisions:
  - "Task 3's exit code is 2, not 1: the ticket (acceptance authority) records the measured fix as the exit-2 mapping; the quick-task dispatch's own paraphrase said exit 1 and is wrong. Both block identically (evaluateCommandExitZero derives block from non-zero alone), so no gate consumer's behavior changes -- only the diagnostic contract and the exit code."
  - "except OSError (broad) rather than except IsADirectoryError (narrow) in validate_plan: the ticket's own recorded wording covers every unreadable plan path -- directory, permission failure, dangling link -- through one documented message, not a growing list of individually-caught errno subclasses."

requirements-completed: [gsd-beads-25vc.21.1]

duration: 11min
completed: 2026-09-08
status: complete
---

# Quick Task 260908-gzq: Fix sota-numerics check-alternatives.py three low-severity fail-closed edge cases

Landed all three `gsd-beads-25vc.21.1` findings as three atomic TDD commits on `feat/extended-sota-definition` in the sota-numerics worktree: a backticked `<!--` no longer blanks a compliant plan to EOF, a symlinked phase directory can no longer escape `.planning/phases/` during discovery, and a directory named like a plan now exits 2 with a clean message instead of a raw traceback.

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-08T10:23:13Z
- **Completed:** 2026-09-08T10:34:05Z
- **Tasks:** 3/3
- **Files modified:** 4 (target repo only; this SUMMARY is the only file touched in the working repo)

## Target repo

All code/test/doc commits landed in `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013` (davdittrich/sota-numerics), branch `feat/extended-sota-definition`, starting at `c8c8a1b`. Nothing was pushed and no PR was opened, per the plan's instruction — landing on the branch is the whole deliverable.

## Task Commits (in target repo)

1. **Task 1: Stop a backticked comment opener from blanking the plan to EOF** — `0adf316` (fix)
2. **Task 2: Skip symlinked entries during phase-directory discovery** — `5d99557` (fix)
3. **Task 3: Map an unreadable plan path to the documented exit-2 contract** — `e5ff8d3` (fix)

Each commit carries its fix, its test(s), and — for Task 3 — the README and CHANGELOG lines that pin the behavior it changes, in the same commit (the ticket's acceptance criterion).

Final target-repo state: `git status --short` clean, `git log --oneline -3` shows the three commits above in order on `feat/extended-sota-definition`.

## Files Modified (target repo)

- `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` — added `INLINE_CODE_SPAN_RE` and `next_comment_opener()`; required `not entry.is_symlink()` in the phase-match loop; added an `except OSError` arm in `validate_plan()`; updated the module docstring's exit-2 sentence and `mask_fenced_regions()`'s fail-closed note
- `tests/test_check_alternatives.py` — 4 new cases in `TestHtmlComments`, 1 new case in `TestCurrentPhaseResolution`, `TestUnreadablePlanFiles` rewritten (class docstring + `test_directory_named_like_a_plan_exits_1` renamed to `..._exits_2` and its assertions changed)
- `README.md` — extended the `2:` exit-code bullet with the unreadable-plan case; rewrote the "Other unexpected filesystem errors" paragraph, since it was no longer true for the `read_text` path
- `CHANGELOG.md` — three new paragraphs under the unreleased `## 0.2.0` section, one per finding

## Test count and results

Baseline at `c8c8a1b`: 125 tests, `OK`. After Task 1: 129 (4 added). After Task 2: 130 (1 added). After Task 3: 130 (net 0 — `test_directory_named_like_a_plan_exits_1` renamed to `..._exits_2`, not added or removed). Full suite green after every commit; final run: **130 tests, OK**.

Each of the three new/rewritten cases was run RED against the pre-fix code before its fix was applied (Task 2 and Task 3 verified by temporarily reverting only the relevant hunk of `check-alternatives.py` via `git checkout -- <file>` / `git apply` of a saved patch — never `git stash`, per this worktree's prohibition — then reapplying):

- Task 1 (`test_a_backticked_comment_opener_does_not_open_a_comment`): RED — exit 1, `missing '## Alternatives Considered' section`. GREEN after fix.
- Task 2 (`test_a_symlinked_phase_directory_is_not_matched`): RED — exit 1 (symlink target's plan was validated and reported a real violation). GREEN after fix — exit 2, `matches 0 directories`.
- Task 3 (`test_directory_named_like_a_plan_exits_2`): RED — exit 1 (uncaught `IsADirectoryError` traceback surfaced as Python's own exit 1). GREEN after fix — exit 2, clean message, no `Traceback`.

## Corpus verdicts (unchanged, all three checkpoints)

Ran after every task's commit; identical every time, matching the plan's baseline exactly:

| Phase dir | Verdict (exit code) |
|---|---|
| 19-native-resolver-contract-and-failure-boundary | 1 |
| 20-additive-identity-migration-and-compatibility | 0 |
| 21-installed-cutover-and-patch-2-retirement | 0 |
| 22-capability-projection-reconciliation | 1 |
| 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin | 0 |
| 24-remediate-sota-numerics-0-2-0-release-blockers | 0 |

## Finding-3 exit-code divergence (recorded per plan instruction)

The quick-task dispatch's own constraint list paraphrased the ticket as "catch it fail-closed (exit 1)". This is a paraphrase error, not the ticket's actual text. `bd show gsd-beads-25vc.21.1` records: "I attempted the obvious fix ... and confirmed it produces a clean message and exit 2" and frames the deferred work as landing that fix with its test/README updated together — i.e., the ticket's own measured, recorded fix is exit 2, not exit 1. The plan (`260908-gzq-PLAN.md`) explicitly calls out and corrects this divergence in Task 3's `<action>` block, and this execution implemented exit 2 as directed. Both exit codes block identically under `evaluateCommandExitZero` (derives `block` from non-zero exit alone), so no gate consumer's pass/fail behavior changes — only the diagnostic contract (clean message vs. raw traceback) and the numeric code.

## Worktree hazard check

`~/.gsd/capability-auto-install-sota-numerics.hash` recorded before the first edit: `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498`. Re-checked after every commit and at the end of the plan: **unchanged** at every checkpoint. No uncommitted-bundle install occurred.

## Decisions Made

- **Task 1 mechanism** (from the plan's own Alternatives Considered): same-line bounded backtick-span regex, chosen over a markdown-parser dependency (disqualified by the capability's stdlib-only constraint) and over "document limitation only" (leaves the false positive live; rejected as more code to explain than to fix). Documented, not silently widened: an unterminated backtick or a code span crossing a line break still masks to EOF.
- **Task 2 scope bound**: `discover_plan_files` (plan-file discovery inside an already-resolved phase directory) is untouched. Considered whether it needs the same `is_symlink()` guard and judged it does not warrant a follow-up bd issue on its own: `PLAN_SHAPED_RE`/`PLAN_FILE_RE` match names only, no content is printed for a misnamed or symlinked entry there, and the ticket names phase-directory discovery specifically. No follow-up issue filed.
- **Task 3 mechanism**: broad `except OSError` rather than a narrower `except IsADirectoryError`, per the ticket's own recorded wording and the plan's Alternatives Considered — one arm, one documented message, covers directory-named-like-a-plan, permission failures, and dangling links alike, instead of growing a list of individually-caught errno subclasses.

## Deviations from Plan

None — plan executed exactly as written, including its own explicit correction of the exit-code paraphrase (see above, which the plan itself flags as a correction rather than a deviation this execution introduced).

## Issues Encountered

TDD RED verification for Tasks 2 and 3 required reverting an already-applied code fix before writing/running the new test, since the fix for each task was implemented before the corresponding test was written in this session. `git stash` is prohibited inside this worktree (shared `refs/stash` across sibling worktrees). Used `git diff -- <file> > patch; git checkout -- <file>` to isolate the code change, ran the new test to confirm RED, then `git apply patch` to restore it — confirmed genuine RED/GREEN transitions for all three findings without touching the shared stash.

## User Setup Required

None — no external service configuration required.

## Bead Ticket

`gsd-beads-25vc.21.1` claimed at task start (`bd update ... --status in_progress`), closed after all three findings landed and verified — see the ticket's comment for the acceptance-criteria evidence trail (commit SHAs, test count, corpus verdicts).

## Next Phase Readiness

The three `gsd-beads-25vc.21.1` findings are resolved on `feat/extended-sota-definition`; nothing further is required by this ticket. The branch is not pushed and no PR is opened — that remains a separate, explicit action for whoever ships the sota-numerics 0.2.0 release.

---
*Quick task: 260908-gzq*
*Completed: 2026-09-08*

## Self-Check: PASSED

- SUMMARY.md at the working-repo path: FOUND
- Commit `0adf316` in target repo: FOUND
- Commit `5d99557` in target repo: FOUND
- Commit `e5ff8d3` in target repo: FOUND
