---
quick_id: 260908-h0m
phase: quick-260908-h0m
plan: 01
subsystem: sota-numerics (davdittrich/sota-numerics, target_repo — NOT this repo)
tags: [ponytail, cleanup, sota-numerics, check-alternatives, capability-auto-install]
dependency-graph:
  requires: [gsd-beads-25vc.21]
  provides: [gsd-beads-25vc.21.4]
  affects:
    - target_repo:.gsd/capabilities/sota-numerics/scripts/check-alternatives.py
    - target_repo:hooks/capability-auto-install.sh
    - target_repo:tests/test-capability-auto-install.sh
    - target_repo:tests/test_check_alternatives.py
tech-stack:
  added: []
  patterns:
    - "Rationale lives once, in the executable test that pins it; code comments point at the test method by name instead of restating the rationale."
key-files:
  created: []
  modified:
    - target_repo:.gsd/capabilities/sota-numerics/scripts/check-alternatives.py
    - target_repo:hooks/capability-auto-install.sh
    - target_repo:tests/test-capability-auto-install.sh
    - target_repo:tests/test_check_alternatives.py
decisions:
  - "Re-verified all plan baselines at actual start-of-execution HEAD (d36678d) rather than the plan's stated target_baseline_head (c8c8a1b, 9 commits behind): 131 Python tests (not 125), D0=9 refusals (unchanged), and total file line counts 73-120 lines higher than the plan's stated baseline across the four files. Treated the plan's absolute-line-count verify thresholds (e.g. '<860', '<830', '<1995') as calibrated to the stale baseline and therefore advisory; graded against the plan's prose done-criteria and measured, reported the honest delta instead."
  - "P2-6 declined and deferred to the author per the plan's explicit instruction — recorded, not implemented."
  - "P2-7 and P2-8 verified already-resolved by earlier commits — recorded, nothing deleted (plan explicitly forbids manufacturing a deletion to match the review's line count)."
  - "Found and collapsed one additional genuine near-verbatim duplicate in hooks/capability-auto-install.sh (the assume-unchanged/skip-worktree rationale, duplicated at tests/test-capability-auto-install.sh:528-534) beyond the two pairs the plan named explicitly, applying the same 'one copy of each rationale' rule P1-2 states. Left the bundle_hash algorithm comment and the ASVS/defense-in-depth comment untouched after grepping the test file and finding no near-verbatim duplicate for either — per the plan's own 'if unique, keep it' clause."
metrics:
  duration: ~55min
  completed: 2026-09-08
actuals:
  tokens: n/a (target repo work, not measured against this repo's estimate scale)
  tasks: 3
  commits: 3
status: complete
---

# Quick Task 260908-h0m: Ponytail cleanup of sota-numerics check-alternatives.py and capability-auto-install.sh Summary

Landed six of nine REVIEW-PONYTAIL-FINAL.md findings (P1-1, P1-2, P1-3, P2-4, P2-5, P2-9) as three atomic commits in `davdittrich/sota-numerics` on `feat/extended-sota-definition`, declined one (P2-6, per the plan's explicit instruction), and confirmed two already resolved by earlier commits (P2-7, P2-8) — with every disposition backed by re-verification at the actual starting HEAD rather than the plan's stale baseline.

**Target repo:** `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013` (davdittrich/sota-numerics, branch `feat/extended-sota-definition`). This repo (gsd-beads) only hosts this SUMMARY and the beads ticket; no file in gsd-beads itself was modified.

## Baseline re-verification (before Task 1)

The plan's `target_baseline_head` was `c8c8a1b`; actual starting HEAD was `d36678d`, 9 commits ahead (plans .21.1–.21.3 landed earlier this session). Re-ran all four suites and `wc -l` before touching anything:

| Measurement | Plan's stated baseline | Actual baseline (d36678d) |
|---|---|---|
| Python tests | `Ran 125 tests` / OK | `Ran 131 tests` / OK |
| D0 refusal count | 9 | 9 (unchanged) |
| `check-alternatives.py` | 894 lines | 967 lines |
| `hooks/capability-auto-install.sh` | 244 lines | 355 lines |
| `tests/test-capability-auto-install.sh` | 894 lines | 987 lines |
| `tests/test_check_alternatives.py` | 2010 lines | 2130 lines |
| `CHANGELOG.md` | 92 lines | 138 lines |

Every stop condition in the plan is phrased against these stale numbers (e.g. "the Python test count moves off 125" — it already had, at baseline, before any edit). Treated the *behavior* each stop condition protects (no test method deleted, D0 count and load-bearingness intact, hash sidecar unchanged, no review-item target invented) as the real gate, and the specific numbers as the plan's authors' own estimate at an earlier HEAD — consistent with the plan's own `<line_number_warning>`, which already flagged this staleness for line numbers and told the executor to "anchor on symbol names and quoted content, not on the review's line numbers." Extended the same standard to the embedded absolute-line-count thresholds in `<verify>` blocks (e.g. `-lt 860`), which are derived from the same stale baseline and were already unsatisfiable if taken literally once the true baseline is 73–120 lines higher. All *relative* and *behavioral* verify criteria (test count unchanged from actual baseline, D0 count and provability unchanged, hash unchanged, no branch/refusal touched) passed cleanly at every task.

D-17 hash sidecar (`~/.gsd/capability-auto-install-sota-numerics.hash`) verified `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` before Task 1 and again after Task 3 — unchanged throughout.

## Disposition table (acceptance criterion for gsd-beads-25vc.21.4)

| Item | Disposition | Commit / reason | Measured delta |
|---|---|---|---|
| P1-1 (D0 doc-parity check) | **Landed** | `252c2cc` | `tests/test-capability-auto-install.sh` D0 block: 97 lines → 20 lines |
| P1-2 (Python half) | **Landed** | `ca6dca2` | `check-alternatives.py`: -18 lines (NEXT_HEADING_RE + BULLET_RE comment blocks) |
| P1-2 (shell half) | **Landed** | `252c2cc` | `hooks/capability-auto-install.sh`: -22 lines (status-flag/`.gitattributes` block, assume-unchanged/skip-worktree block) |
| P1-3 (circular docstring assertions) | **Landed** | `2f4d52a` | `tests/test_check_alternatives.py`: -15 lines |
| P2-4 (`validate_entry` returns reason, not list) | **Landed** | `ca6dca2` | ~0 net lines (signature/return-type change, not a deletion) |
| P2-5 (inline single-use helpers) | **Landed** | `ca6dca2` | `check-alternatives.py`: -7 lines |
| P2-6 (merge bullet/table-row parsers) | **Declined, deferred to author** | Contract change, not simplification — three tests pin the current keep-both-when-mixed behavior (`test_two_bullets_override_valid_table`, `test_one_bullet_selects_valid_table`, `test_pipe_rows_without_separator_are_not_a_markdown_table`) and `README:125` documents it. Not implemented, per the plan's explicit instruction. | 0 |
| P2-7 (CHANGELOG.md self-referential paragraph) | **Already-resolved** | The paragraph the review quoted (at HEAD `1de851c`) is absent from the current `CHANGELOG.md`; rewritten by an earlier phase-24 commit. Confirmed via grep; file untouched (`git diff --name-only HEAD -- CHANGELOG.md` = empty). | 0 (already banked) |
| P2-8 (redundant `bullet_result.returncode` assertion) | **Already-resolved** | At current HEAD there is exactly one `bullet_result.returncode` occurrence (`TestSupportedEntryShapes.test_table_accepts_same_semantics_as_bullets`, paired with a `table_result` assertion — not a duplicate). The duplicate the review named no longer exists. Nothing deleted, per the plan's explicit "do not manufacture a deletion" instruction. | 0 |
| P2-9 (walk project root once) | **Landed** | `ca6dca2` | Net +3 lines in `check-alternatives.py` (removing the 3-line guard from `check_alternatives()` costs less than the 7-line try/except added to `main()`'s explicit-argument branch to preserve the exit-2 contract) — one fewer filesystem walk per gate run, the behavioral goal, achieved; line count is not a proxy for this item. |

## Line count deltas (measured, not targets)

| File | Baseline (actual, d36678d) | Final | Delta |
|---|---|---|---|
| `check-alternatives.py` | 967 | 945 | -22 |
| `hooks/capability-auto-install.sh` | 355 | 339 | -16 |
| `tests/test-capability-auto-install.sh` | 987 | 911 | -76 |
| `tests/test_check_alternatives.py` | 2130 | 2115 | -15 |
| `CHANGELOG.md` | 138 | 138 | 0 (untouched, confirmed) |
| **Total** | **4577** | **4448** | **-129** |

The plan estimated "in the region of -290" (excluding declined P2-6); the actual measured total is -129. The shortfall is fully accounted for: P2-4 and P2-9 are near-zero-to-slightly-positive net-line items (behavioral changes, not deletions), and the two comment blocks collapsed under P1-2 were smaller in their current, re-verified form than the review's stale line-range estimates implied. No deletion was padded to chase the estimate, per the plan's explicit instruction not to.

## Test suite state (unchanged behavior, all four green after every commit)

- `python3 -m unittest tests/test_check_alternatives.py`: `Ran 131 tests` / `OK` (baseline and final — unchanged by this plan; the plan's stated "125" was already stale before Task 1).
- `bash tests/test-capability-auto-install.sh`: `ALL PASS`, D0 line reads `PASS: D0: the hook's 9 refusals and README's table of them are the same set` (baseline and final).
- `bash tests/test-gate-script-resolution.sh`: `ALL PASS` (baseline and final).
- `bash tests/test-session-start.sh`: `ALL PASS` (baseline and final).
- No test method was deleted anywhere in this plan — only comments, dead-shape helpers, one return-type signature, one redundant filesystem walk, and three assertions with zero behavioral content (P1-3).

## D0 check load-bearingness proof (P1-1)

Before committing Task 2, added a temporary 10th refusal string to `hooks/capability-auto-install.sh` not present in `README.md`, confirmed the new pure-shell D0 loop turned red (`FAIL: D0: README.md does not document the refusal: TENTH-CANARY-REFUSAL-NOT-IN-README`, `1 FAILED`), then reverted the hook to byte-identical content (`diff` confirmed) before re-running the suite green. Also fixed the replacement's pass/fail semantics mid-task: the first draft printed the `PASS: D0: ...` summary line unconditionally even when a refusal was undocumented; corrected so the pass line is emitted only when zero problems are found, matching the original implementation's behavior.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking issue] Plan's absolute line-count verify thresholds were stale**
- **Found during:** Baseline re-verification, before Task 1
- **Issue:** The plan's `<verify>` blocks assert absolute line counts (e.g. `-lt 860`, `-lt 830`, `-lt 1995`) calibrated to a baseline (894/244/894/2010) that was already 73-120 lines lower than the actual starting HEAD (967/355/987/2130). Taken literally, several thresholds were unsatisfiable without deleting content unrelated to this plan's scope, which the plan itself forbids ("do not pad the deletion to reach it").
- **Fix:** Graded against the plan's prose done-criteria (behavioral: test count stable from actual baseline, D0 count and provability intact, hash sidecar unchanged, helpers/return-type/walk-count changed as specified) instead of the stale absolute thresholds. Documented every measured delta honestly above rather than manufacturing extra deletions to chase the plan's estimate.
- **Files modified:** None (this is a grading-standard note, not a code change).
- **Commit:** N/A

**2. [Rule 2 - missing item, found via independent verification] One additional genuine duplicate in hooks/capability-auto-install.sh**
- **Found during:** Task 2
- **Issue:** Beyond the two rationale pairs the plan named explicitly (the `.gitattributes`/status-flag block and the four-flag prose list), grep found a third near-verbatim duplicate: the hook's explanation of `update-index --assume-unchanged`/`--skip-worktree` (why they're "an ordinary local tweak, not an exotic attack", and why `diff --quiet HEAD` doesn't help) was duplicated near-verbatim in `tests/test-capability-auto-install.sh:528-534` (cases J2, J3).
- **Fix:** Collapsed to a shorter comment retaining the load-bearing mechanism detail (the `-v` H/lowercase/S tagging the subsequent `grep '^[^H]'` logic depends on) while cutting the duplicated framing prose, applying the same P1-2 "one copy of each rationale" rule the plan states.
- **Files modified:** `target_repo:hooks/capability-auto-install.sh`
- **Commit:** `252c2cc`

Also checked and explicitly declined to touch two other candidate blocks in `hooks/capability-auto-install.sh` (the whole-bundle-hash algorithm comment at lines 85-105, and the ASVS/defense-in-depth comment at lines 14-16): grepped `tests/test-capability-auto-install.sh` for their distinguishing phrases and found no near-verbatim match for either — per the plan's own "if a rationale exists only in the code comment and nowhere else, keep it" rule, these were left unmodified.

### No other deviations. Plan executed as written, including its own explicit stale-baseline caveat.

## Known Stubs

None.

## Threat Flags

None — this plan touched no new trust boundary. The threat model's four `mitigate` items (T-h0m-01 through T-h0m-04) were all satisfied: hash sidecar re-verified unchanged before Task 1 and after Task 3; no refusal branch, `exit 0` fail-closed path, `unverifiable_repo` HEAD refinement, or capability-id pattern check was touched; the D0 check's continued ability to fail was proven with a canary before commit; every caller of `validate_entry` was grepped for before its return type changed (one caller found, updated).

## Self-Check: PASSED

- FOUND: target_repo `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` modified, commit `ca6dca2` present in `git log --oneline --all`.
- FOUND: target_repo `hooks/capability-auto-install.sh` and `tests/test-capability-auto-install.sh` modified, commit `252c2cc` present in `git log --oneline --all`.
- FOUND: target_repo `tests/test_check_alternatives.py` modified, commit `2f4d52a` present in `git log --oneline --all`.
- FOUND: target repo working tree clean after all three commits (`git status --short` empty).
- FOUND: target repo branch `feat/extended-sota-definition` still current, HEAD advanced from `d36678d` to `2f4d52a`, not pushed.
- FOUND: `~/.gsd/capability-auto-install-sota-numerics.hash` = `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498`, unchanged from pre-Task-1 reading.
