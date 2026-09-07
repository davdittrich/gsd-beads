---
phase: 24-remediate-sota-numerics-0-2-0-release-blockers
plan: 01
subsystem: tooling
tags: [python, unittest, commonmark, regex, gate-script, tdd]

# Dependency graph
requires:
  - phase: 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin
    provides: check-alternatives.py's mask_fenced_regions pre-pass, its 97-test suite, and the D-02/D-01 fail-open findings from REVIEW-CRITICAL-FINAL and REVIEW-AGY-FINAL that this plan closes
provides:
  - Indented-code-block masking (D-02) so a section hidden in a 4-space-indented block no longer credits a plan
  - Leading-YAML-frontmatter masking (D-01, REVIEW-AGY-FINAL blocking item 2) so a section declared only in frontmatter no longer credits a plan
  - 8 new gate-behaviour fixtures (D-06), 105 total tests, 0 non-passing
  - D-05 before/after corpus evidence (this file) that plan 24-03 diffs against
affects: [24-02, 24-03, 24-08]

# Actuals (#2632)
actuals:
  tokens: 3391
  tasks: 3
  commits: 5
  commits_note: >
    Cross-repo plan (target_repo override, not sub_repos): 4 commits landed in the
    worktree repo (/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013,
    branch feat/extended-sota-definition) where the code changes are tracked, plus
    this SUMMARY's own commit in the orchestrator repo (gsd-beads). The orchestrator
    repo's own plan-commit ledger (gsd-plan-head-before-24-01, base 00df0b0) measures
    1 commit for this plan -- the SUMMARY commit itself -- because no code in this
    plan's files_modified list lives in the orchestrator repo.
  worktree_repo: /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013
  worktree_commits: [4849937, c6a52a2, 5dc6b7a, 2321b74]
commits: 1
plan_head_before: 00df0b096d57fdc52693d78025121040edc16e91

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Offset-preserving span masking: fences, HTML comments, indented code blocks, and now leading frontmatter are all blanked to same-length spaces in mask_fenced_regions, so line numbers and later regex offsets stay true regardless of how many constructs are masked."

key-files:
  created: []
  modified:
    - "[worktree] .gsd/capabilities/sota-numerics/scripts/check-alternatives.py — added mask_leading_frontmatter and mask_indented_code_blocks, wired into mask_fenced_regions (frontmatter first, then fence/comment, then indented-code)"
    - "[worktree] tests/test_check_alternatives.py — added TestIndentedCodeBlocks (4 tests) and TestFrontmatterMasking (4 tests)"

key-decisions:
  - "D-05's fixture corpus is interpreted as corpus B (the Python suite): the crafted fail-open fixtures are exercised as unittest cases, so a fixture's verdict changing shows up directly as that test's PASS/FAIL outcome, not as a separate hand-run comparison."
  - "Task 1's literal ticket fixture (heading AND entries all indented 4 spaces) does not reproduce the fail-open at all -- it already exits 1 pre-fix, because SECTION_HEADING_RE is column-0-anchored. Verified empirically both ways and cross-checked against REVIEW-CRITICAL-FINAL's P1-1a reproduction (heading at column 0, only the entries and Decided-by line indented). Adopted the corrected fixture as the primary RED/GREEN test; kept the ticket's literal fixture as a second, already-passing regression pin (test_a_wholly_indented_heading_and_body_is_still_a_missing_section) rather than deleting it. Rule 1 auto-fix (test-design correction, not a code bug); no user turn occurred to raise it against."
  - "The gsd-tools TDD gate (check tdd-red-evidence) is Node-TAP-format only. Both RED phases ran python3 -m unittest -v directly and were then translated -- faithfully, no fabricated values -- into the tool's TAP input shape (# tests/# pass/# fail header plus ok/not ok lines) with the verbatim unittest -v transcript appended for the human record. Both gate calls returned RED_EVIDENCE_OK."
  - "mask_leading_frontmatter runs first inside mask_fenced_regions, before fence/comment/indented-code masking, because frontmatter is a document-level boundary (literal --- / ... delimiter lines) that CommonMark block constructs nested inside it must not be able to move or hide."
  - "PLAN_FRONTMATTER_RE requires an actual closing --- or ... line; an opening --- with no closer is left unmasked (fail-safe direction), so a document whose first line is a thematic break or an empty-paragraph setext H2 underline is scanned exactly as before this plan (T-24-04)."

patterns-established:
  - "Same-length space-substitution masking for every CommonMark-invisible construct the gate must not read, applied in a single ordered pre-pass (frontmatter -> fence/comment -> indented-code) so later constructs cannot be forged by an earlier mask's blank interior."

requirements-completed: [D-01, D-02, D-05, D-06, D-17, D-18]

coverage:
  - id: D1
    description: "Indented-code-block masking closes the D-02 fail-open: a plan whose only Alternatives Considered section sits inside a 4-space-indented block now exits 1."
    requirement: D-02
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py#TestIndentedCodeBlocks.test_indented_alternatives_are_not_counted_as_prose"
        status: pass
    human_judgment: false
  - id: D2
    description: "Leading-YAML-frontmatter masking closes the D-01 / REVIEW-AGY-FINAL blocking-item-2 fail-open: a section declared only inside frontmatter now exits 1."
    requirement: D-01
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py#TestFrontmatterMasking.test_a_section_declared_only_in_frontmatter_is_a_missing_section"
        status: pass
    human_judgment: false
  - id: D3
    description: "D-05 regression evidence: corpus A (6 real gsd-beads phase directories) and corpus B (Python suite) are unchanged except the crafted fixtures, recorded before the first edit and after the last."
    requirement: D-05
    verification:
      - kind: other
        ref: "24-01-SUMMARY.md#D-05 regression evidence (this file, tables below)"
        status: pass
    human_judgment: false
  - id: D4
    description: "D-17 hash sidecar values recorded before the first edit and after the last, per the accepted in-tree-worktree auto-install hazard."
    requirement: D-17
    verification:
      - kind: other
        ref: "24-01-SUMMARY.md#D-17 hash sidecar (this file, values below)"
        status: pass
    human_judgment: false

duration: n/a (continued across a context compaction; wall-clock not meaningful)
completed: 2026-09-07
status: complete
---

# Phase 24 Plan 01: Close the indented-code-block and frontmatter fail-opens in check-alternatives.py Summary

**Masked two CommonMark-invisible constructs (4-space indented code blocks, D-02; leading YAML frontmatter, D-01) in the sota-numerics Alternatives-Considered gate, closing both with TDD fixtures and a byte-identical corpus sweep.**

## Performance

- **Started:** session preceding this compaction (exact ISO timestamp lost to compaction)
- **Completed:** 2026-09-07T20:46:23Z
- **Tasks:** 3/3 completed
- **Files modified:** 2 (both in the worktree repo)

## Accomplishments

- Closed the D-02 indented-code-block fail-open: `mask_indented_code_blocks` blanks any non-blank, non-list, 4+-space-indented run that follows a blank line, guarded by list context so an ordinary bullet continuation paragraph is never masked.
- Closed the D-01 / REVIEW-AGY-FINAL blocking-item-2 frontmatter fail-open: `mask_leading_frontmatter` blanks a plan's leading `---`/`...`-delimited YAML block, requiring an actual closing delimiter so an unclosed leading `---` is never treated as frontmatter.
- Both fixes are wired into the single `mask_fenced_regions` pre-pass every section/bullet/table scan already runs through, in the order frontmatter -> fence/comment -> indented-code, so a masked span cannot forge a later mask's boundary state.
- 8 new gate-behaviour tests added (105 total, 0 non-passing); the 97 pre-existing tests are untouched and still pass.
- Corpus A (the 6 real `gsd-beads/.planning/phases/*` directories) returns byte-identical exit codes before and after both fixes: `1,0,0,1,0,0`.

## Task Commits

Each task was committed atomically, in the worktree repo (`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`):

1. **Task 1: End-to-end — indented-code-block masking (D-02)**
   - `4849937` (test) — pin the indented-code-block fail-open with `TestIndentedCodeBlocks` (RED; RED_EVIDENCE_OK via TAP-translated `python3 -m unittest` output)
   - `c6a52a2` (feat) — `mask_indented_code_blocks`, wired into `mask_fenced_regions` (GREEN)
2. **Task 2: Mask YAML frontmatter (D-01)**
   - `5dc6b7a` (test) — pin the frontmatter fail-open with `TestFrontmatterMasking` (RED; RED_EVIDENCE_OK)
   - `2321b74` (feat) — `PLAN_FRONTMATTER_RE` / `mask_leading_frontmatter`, wired first in `mask_fenced_regions` (GREEN)
3. **Task 3: Record the post-edit hash and corpus delta** — this file (committed separately in the orchestrator repo, see frontmatter `commits_note`).

**Plan metadata:** recorded in a separate final commit in the orchestrator repo (STATE.md/ROADMAP.md/REQUIREMENTS.md), after this SUMMARY.

_TDD tasks each carry a test-then-feat commit pair (RED then GREEN); no separate refactor commit was needed._

## Files Created/Modified

- `[worktree] .gsd/capabilities/sota-numerics/scripts/check-alternatives.py` — added `PLAN_FRONTMATTER_RE`, `mask_leading_frontmatter`, `mask_indented_code_blocks`; wired both into `mask_fenced_regions`
- `[worktree] tests/test_check_alternatives.py` — added `TestIndentedCodeBlocks` (4 tests) and `TestFrontmatterMasking` (4 tests)
- `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-01-SUMMARY.md` — this file

## D-05 regression evidence

**Interpretation used:** D-05's fixture corpus is corpus B, the Python suite -- the crafted fail-open fixtures are unittest cases, so a fixture's verdict changing appears directly as that test's PASS/FAIL outcome rather than as a separately hand-run comparison.

### Corpus A — real `gsd-beads/.planning/phases/*` directories (exit code per directory)

Pre-edit codes measured against commit `1de851c` (the commit immediately before Task 1's RED commit `4849937`, i.e. the true Step-0 state). Post-edit codes measured against `2321b74` (current HEAD, after Task 2's GREEN commit).

| Directory | Pre-edit exit | Post-edit exit | Changed? |
|---|---|---|---|
| `19-native-resolver-contract-and-failure-boundary` | 1 | 1 | no |
| `20-additive-identity-migration-and-compatibility` | 0 | 0 | no |
| `21-installed-cutover-and-patch-2-retirement` | 0 | 0 | no |
| `22-capability-projection-reconciliation` | 1 | 1 | no |
| `23-extend-sota-definition-in-sota-numerics-and-refactor-plugin` | 0 | 0 | no |
| `24-remediate-sota-numerics-0-2-0-release-blockers` | 0 | 0 | no |

No real corpus verdict moved. Sorted-order codes: pre-edit `1,0,0,1,0,0`, post-edit `1,0,0,1,0,0` — matches the plan's recorded Step-0 expectation exactly.

### Corpus B — Python suite (`python3 -m unittest tests.test_check_alternatives -v`)

| | Pre-edit (`1de851c`) | Post-edit (`2321b74`) |
|---|---|---|
| Total tests | 97 | 105 |
| Non-passing | 0 | 0 |
| Result | OK | OK |

All 97 pre-existing tests are a subset of the 105 post-edit tests, unmodified and still passing (no pre-existing test was renamed, removed, or edited by this plan — only two new classes were added). The delta is exactly the 8 new fixtures.

### Crafted fixtures whose verdict changed

Only these two fixtures moved, and both moved fail-open -> blocked (0 -> 1), the fail-closed direction the plan requires; every other new fixture pinned already-correct pre-fix behavior (no change):

| Test | Pre-fix exit (unfixed script) | Post-fix exit |
|---|---|---|
| `TestIndentedCodeBlocks.test_indented_alternatives_are_not_counted_as_prose` | 0 (fail-open) | 1 (blocked) |
| `TestFrontmatterMasking.test_a_section_declared_only_in_frontmatter_is_a_missing_section` | 0 (fail-open) | 1 (blocked) |

## D-17 hash sidecar

Per D-17, `~/.gsd/capability-auto-install-sota-numerics.hash` is a live, unversioned singleton written by the plugin's SessionStart/SubagentStart hook (`bundle_hash()` in `hooks/capability-auto-install.sh`, a whole-directory content+path hash of `.gsd/capabilities/sota-numerics` at its real absolute worktree path). Recovering a true "before this session's edits" reading of that file was not possible after the mid-plan context compaction, since it is overwritten in place with no history. Instead, the pre-edit and post-edit values below were **computed directly** by running the hook's exact `bundle_hash()` algorithm against the real worktree path, once with the tree checked out at the pre-edit commit (`1de851c`, briefly, tree confirmed clean before and after, branch restored to `feat/extended-sota-definition` at `2321b74`) and once at the current HEAD:

| Reading | `sha256` |
|---|---|
| Pre-edit (`1de851c`, real worktree path) | `46a7366bd3b7eada50b3b5a9fab3b0c3dbe18897e8d3cb599504e8ea120c5858` |
| Post-edit (`2321b74`, real worktree path, current HEAD) | `9b76f03bb04fb7cfa813813e0a72c4b5d441c082492a1889bd506de19cf14f59` |
| Live sidecar file observed at measurement time | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` |

The live sidecar value matches **neither** computed reading. This means the global mirror currently reflects some other bundle state (most likely an earlier point in this same multi-session plan, or a prior unrelated hook fire) rather than either this plan's true starting point or its current end state. This is exactly the D-17 hazard as designed -- it is not resolved by this plan; per the plan's own context note, the mirror is restored to the released plugin-cache bundle at the end of the phase by plan 24-08. Flagging it here rather than silently treating the stale value as authoritative.

## Decisions Made

See `key-decisions` in the frontmatter above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test design] Task 1's ticket-literal fixture did not reproduce the D-02 fail-open**
- **Found during:** Task 1, RED phase
- **Issue:** The bd ticket's Behavior bullet described "heading AND entries indented four spaces," but `SECTION_HEADING_RE` is anchored `^##` at column 0, so that shape already exits 1 before any fix — it never reproduces the exploit.
- **Fix:** Verified empirically both the ticket-literal fixture (exits 1 unfixed) and a corrected fixture matching REVIEW-CRITICAL-FINAL's P1-1a reproduction (heading at column 0, only entries and Decided-by indented; exits 0 unfixed). Adopted the corrected fixture as the primary RED/GREEN test (`test_indented_alternatives_are_not_counted_as_prose`); kept the ticket-literal shape as a second, already-passing regression pin (`test_a_wholly_indented_heading_and_body_is_still_a_missing_section`).
- **Files modified:** `[worktree] tests/test_check_alternatives.py`
- **Verification:** Cross-checked against `REVIEW-CRITICAL-FINAL.md`'s P1-1(a) text; both fixtures run and behave as documented.
- **Committed in:** `4849937`

**2. [Rule 3 - Blocking issue] `gsd-tools check tdd-red-evidence` only accepts Node-TAP-format output**
- **Found during:** Task 1 and Task 2, RED phase
- **Issue:** The TDD gate tool has no native support for `python3 -m unittest -v` output; feeding it the raw unittest transcript would misclassify a genuinely valid RED result as `INVALID_RED` (zero-test-discovery), purely from a format mismatch.
- **Fix:** Captured the real, exact `python3 -m unittest -v` run (command, exit code, test/pass/fail counts, failing test identity) and translated it faithfully — no fabricated values — into the tool's TAP-format input shape, with the verbatim `-v` transcript appended. Both gate calls returned `RED_EVIDENCE_OK`.
- **Files modified:** none (evidence records only, in scratchpad)
- **Verification:** `gsd_run check tdd-red-evidence <record.json>` returned `{"passed":true,"verdict":"RED_EVIDENCE_OK",...}` both times.
- **Committed in:** n/a (evidence, not code)

**3. [Rule 1 - Scratchpad discipline] Stray RED-evidence JSON found written into the project tree**
- **Found during:** Task 3, before writing this SUMMARY
- **Issue:** An earlier portion of this same session (before compaction) wrote `24-01-task1-red-evidence.json` directly into `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/` instead of the session scratchpad, violating the standing scratchpad-only rule for temporary files. It was never git-tracked.
- **Fix:** Deleted (`rm`). Its content was already fully captured, faithfully, in Task 1's RED commit message (`4849937`) in the worktree repo, so nothing was lost.
- **Files modified:** none (untracked file removed)
- **Verification:** `git status --short` on the phase directory no longer shows it.
- **Committed in:** n/a (untracked, not part of history)

---

**Total deviations:** 3 auto-fixed (1 test-design correction, 1 blocking-issue format adaptation, 1 scratchpad-discipline cleanup)
**Impact on plan:** None affected scope, mechanism, or the D-05/D-17 evidence this plan is required to produce. No verdict outside the two crafted fixtures moved.

## Issues Encountered

Mid-plan context compaction interrupted the session between Task 2's GREEN commit and Task 3's evidence recording. On resume, all four worktree commits (`4849937`, `c6a52a2`, `5dc6b7a`, `2321b74`) were verified present in `git log` before continuing, and the pre-edit corpus/hash baselines were re-derived from git history (commit `1de851c`) rather than trusted from memory, per the standing rule that historical hints are never authority for current verification scope.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Both fail-open shapes this plan targeted (D-02 indented code block, D-01 frontmatter) are closed, tested, and corpus-verified unchanged elsewhere.
- `24-03` can now diff its own corpus sweep against this file's D-05 tables as its recorded baseline.
- `24-08`'s mirror-restoration step should account for the live sidecar value observed here (`da4da96a...`), which matches neither this plan's pre- nor post-edit computed hash — the mirror is in some other, unaccounted-for state.
- Requirements D-01, D-02, D-05, D-06, D-17, D-18 are complete for this plan's scope; D-06 (new gate-behaviour fixtures) and D-05 (before/after evidence) are fully evidenced above.

## Self-Check: PASSED

- FOUND: `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-01-SUMMARY.md`
- FOUND: `[worktree] .gsd/capabilities/sota-numerics/scripts/check-alternatives.py`
- FOUND: `[worktree] tests/test_check_alternatives.py`
- FOUND commit `b07cded` (orchestrator repo)
- FOUND commits `4849937`, `c6a52a2`, `5dc6b7a`, `2321b74` (worktree repo)

---
*Phase: 24-remediate-sota-numerics-0-2-0-release-blockers*
*Completed: 2026-09-07*
