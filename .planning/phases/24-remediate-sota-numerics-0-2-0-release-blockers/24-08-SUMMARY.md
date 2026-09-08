---
phase: 24-remediate-sota-numerics-0-2-0-release-blockers
plan: 08
subsystem: infra
tags: [check-alternatives, changelog, capability-manifest, pr-review, disposition-ledger, cross-repo]

# Dependency graph
requires:
  - phase: 24-01
  - phase: 24-02
  - phase: 24-03
  - phase: 24-04
  - phase: 24-05
  - phase: 24-06
  - phase: 24-07
provides:
  - Live-queried, exhaustive disposition of all 12 pull-request-4 review threads and every
    finding in REVIEW-CRITICAL-FINAL.md, REVIEW-PONYTAIL-FINAL.md, REVIEW-AGY-FINAL.md, and
    REVIEW-PROSE-TOKENS.md (DISPOSITION.md)
  - README.md/CHANGELOG.md corrected to describe the actual __pycache__ trigger mechanism (P1-3)
  - capability.json's description fixed (broken compound adjective, stale release-note sentence)
  - tests/test-gate-script-resolution.sh case2b pinning the GSD_HOME/HOME-unset rung (P2-3)
  - Branch pushed twice (e3d253a..f1fb830, f1fb830..c8c8a1b); PR #4 head now matches local HEAD,
    zero commits behind origin/main
  - 5 consolidated tracking tickets (gsd-beads-25vc.21.1..21.5) for every finding whose fix
    would require an unlisted file, so nothing was silently dropped
  - Final D-05 regression evidence (both corpora, four suites) and D-17 hash trail for the
    whole phase, plus global mirror restored to the released 0.1.3 bundle
affects: [24-09]

# Actuals (#2632)
actuals:
  tokens: 7286
  tasks: 3
  commits: 2
  commits_note:
    Cross-repo plan (target_repo override, not sub_repos), same pattern as 24-01
    through 24-07: 1 commit landed in the worktree repo
    (/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013, branch
    feat/extended-sota-definition) carrying the code/doc fixes, plus 1 commit
    in the orchestrator repo (gsd-beads) carrying DISPOSITION.md. The
    orchestrator repo's own plan-commit ledger (gsd-plan-head-before-24-08,
    base de0b3c9) measured 1 commit at SUMMARY-write time (the DISPOSITION.md
    commit); this SUMMARY's own commit and the final metadata commit
    (STATE.md/ROADMAP.md/REQUIREMENTS.md) are separate, later commits per
    standard executor protocol, not included in this count.
  plan_head_before: de0b3c90cf8552f1f054bfdd87aa1c56a869acea

tech-stack:
  added: []
  patterns:
    - "Disposition ledger as its own artifact, separate from the SUMMARY: DISPOSITION.md
      carries one row per finding (fixed/declined/tracked, each naming the commit or
      re-verification that settled it), so the ledger reads as a checklist rather than prose
      buried in a SUMMARY's Deviations section."
    - "Cross-path bundle-hash comparison pitfall (recorded again after 24-03 already found it
      once): sha256sum's output embeds the invoked path string, so comparing a bundle_hash()
      reading taken at one absolute path (the worktree) against a reading taken at a different
      absolute path (the plugin cache) produces two different hashes even when file content is
      byte-identical. `diff -rq` between the two paths is the correct comparison; the hash
      values are only comparable against each other when both readings are taken at the exact
      same absolute path across a git checkout boundary."

key-files:
  created:
    - .planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/DISPOSITION.md
  modified:
    - .gsd/capabilities/sota-numerics/capability.json (target repo)
    - CHANGELOG.md (target repo)
    - README.md (target repo)
    - tests/test-gate-script-resolution.sh (target repo)

key-decisions:
  - "Pushed the branch before re-triaging PR #4's threads, not after: D-26 requires internal
    review and its accepted fixes to land before external review sees the diff, and the branch
    was eleven then twelve commits behind its own PR head at the start of this plan (P1-5).
    Re-querying threads against a stale PR head would have re-litigated already-fixed findings."
  - "Attempted two 'minimal' fixes the reviews proposed (P2-2's internal-H3 Decided-by masking,
    and AGY's directory-named-like-a-plan OSError catch) and reverted both after they broke
    existing, deliberately-pinned tests. Both cases are recorded as declined/tracked with the
    exact test names that pinned the conflicting accepted behavior, not silently absorbed or
    silently dropped -- 'the review said fix it' is not sufficient authority when the project's
    own tested contract already disagrees with the review's premise."
  - "Filed 5 consolidated tracking tickets rather than ~25 individual ones: every finding whose
    fix needs a file outside 24-08's bounded files_modified list groups naturally by target file
    or theme (check-alternatives.py hardening, capability-auto-install.sh hardening, test-suite
    coverage gaps, ponytail simplifications, prose-token trims). Each ticket enumerates every
    sub-finding by name so none is lost inside a vague title."
  - "Restored the global capability mirror (~/.gsd/capabilities/sota-numerics) to the released
    0.1.3 plugin-cache bundle via `gsd_tools capability install ... --scope global --yes`
    rather than manually copying files, so the normal installation code path (and whatever
    bookkeeping it does beyond file copying) runs instead of being bypassed."

requirements-completed: [D-15, D-16, D-17]

coverage:
  - id: D1
    description: "Every one of PR #4's 12 review threads carries a disposition; the live count
      (12 total, 7 resolved, 5 unresolved at plan start) was re-queried via the GitHub GraphQL
      API rather than reused from the phase context's prose estimate (D-15)."
    requirement: D-15
    verification:
      - kind: other
        ref: "DISPOSITION.md Part 1; live re-query after replies showed 12/12 resolved, 0 unresolved"
    status: pass
    human_judgment: false
  - id: D2
    description: "Every finding across all four review artifacts has exactly one disposition row
      (fixed/declined/tracked), and every tracked deferral names a bd ticket (D-16)."
    requirement: D-16
    verification:
      - kind: other
        ref: "DISPOSITION.md Part 2, all four review-artifact tables"
    status: pass
    human_judgment: false
  - id: D3
    description: "The global capability mirror's hazard (D-17) was measured before and after
      this plan's edits, and restored to the released plugin-cache bundle at phase end."
    requirement: D-17
    verification:
      - kind: other
        ref: "This SUMMARY's 'D-17 hash trail' section, below"
    status: pass
    human_judgment: false

duration: n/a (single continuous session)
completed: 2026-09-08
status: complete
---

# Phase 24 Plan 08: Close the review loop before publish -- disposition ledger, PR sync, final regression evidence Summary

**Live-queried PR #4's 12 review threads and gave every finding in all four review artifacts a fixed/declined/tracked disposition in DISPOSITION.md; pushed the branch twice to close the PR-behind-base gap; fixed the three findings still open on the target repo (the false `__pycache__` claim, capability.json's broken compound adjective, and an untested GSD_HOME/HOME-unset rung); filed 5 tracking tickets for everything out of this plan's bounded scope; re-ran both regression corpora clean at the final commit.**

## Performance

- **Completed:** 2026-09-08T10:00:37Z
- **Tasks:** 3/3 complete
- **Files modified:** 4 (target repo) + 1 created (orchestrator repo)

## Accomplishments

- Re-queried PR #4's review threads live via `gh api graphql` (not reused from any prose count): 12 total, 7 already resolved on GitHub, 5 unresolved. Gave every one of the 12 a disposition; 2 of the 5 unresolved were genuinely fixed by earlier plans in this phase (D-09's CHANGELOG rewrite, D-04's duplicate-`current_phase` fix), 3 were declined with reproduced evidence that the finding no longer holds (the apostrophe/`${PHASE_DIR}` splice is gone; the rc-check test is already stronger than asked; the CRLF setext concern is real in isolation but unreachable because `Path.read_text()` normalizes newlines before any regex runs). Replied to and resolved all 5 via the GitHub API.
- Pushed `feat/extended-sota-definition` twice: once at plan start (`e3d253a..f1fb830`, closing the eleven-then-twelve-commit gap the reviews flagged as a D-26 breach) so thread re-triage happened against current code, and once at plan end (`f1fb830..c8c8a1b`) carrying this plan's own fixes. PR #4's head now matches local HEAD exactly; the branch is zero commits behind `origin/main`.
- Fixed three still-open findings within the plan's bounded `files_modified` list, one commit (`c8c8a1b`): README.md/CHANGELOG.md's `__pycache__` claim was reproducibly false (the checker is always invoked via `subprocess` with a full script path, never `-m`, and CPython never bytecode-caches a script run as `__main__`) -- reproduced the actual trigger (`python3 -m check-alternatives`) and rewrote both files; `capability.json`'s description had a mis-coordinated compound adjective and a release-note sentence baked into a permanent manifest field; added a regression case to `tests/test-gate-script-resolution.sh` pinning the `GSD_HOME`/`HOME`-both-unset rung as fail-closed; deleted CHANGELOG's self-referential "this paragraph keeps going stale" meta-commentary.
- Attempted and **reverted** two further "minimal" fixes the reviews proposed after each broke existing pinned tests -- recorded as declined/tracked with the exact conflicting test names, not silently absorbed.
- Filed 5 consolidated bd tickets (`gsd-beads-25vc.21.1`..`.21.5`) covering every finding whose fix needs a file outside this plan's bounded scope, so D-16's "never dropped for being minor" holds without inflating this plan's own diff.
- Restored `~/.gsd/capabilities/sota-numerics` (the global capability mirror) to the released 0.1.3 plugin-cache bundle via `gsd_tools capability install`, verified content-identical via `diff -rq` against the plugin cache's own 0.1.3 copy (D-17's phase-end step).
- Re-ran the full regression corpus at the final commit: 125 Python tests OK, all 4 shell suites (`test-gate-script-resolution.sh`, `test-session-start.sh`, `test-capability-auto-install.sh`, plus the Python suite already counted) `ALL PASS`, and the real 6-directory `gsd-beads/.planning/phases/*` corpus returned byte-identical verdicts (`1,0,0,1,0,0`) to every prior plan's recorded baseline in this phase.

## Task Commits

1. **Task 1 + Task 2 (combined): enumerate PR threads, disposition every internal-review finding, fix what's in scope**
   - Target repo (`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`): `c8c8a1b` (fix) -- corrects the `__pycache__` claim in README.md/CHANGELOG.md, fixes `capability.json`'s description, adds `tests/test-gate-script-resolution.sh` case2b, deletes CHANGELOG's self-referential paragraph.
   - Orchestrator repo (this repo): `16a32ab` (docs) -- creates `DISPOSITION.md`.
   - GitHub-side actions (no local commit, recorded via API): 5 review-thread replies + resolutions; 2 branch pushes; 5 bd ticket creations.
2. **Task 3: re-establish the phase's regression evidence after the last accepted fix**
   - No separate commit -- this SUMMARY.md is Task 3's artifact, committed as part of this plan's standard SUMMARY commit.

_This plan carried no `tdd="true"` tasks; no RED/GREEN pairing applies._

## D-05 regression evidence (final, whole-phase)

### Corpus A -- real `gsd-beads/.planning/phases/*` directories

| Phase | Verdict (exit code) | Matches phase-24-start baseline? |
|---|---|---|
| `19-native-resolver-contract-and-failure-boundary` | 1 | yes |
| `20-additive-identity-migration-and-compatibility` | 0 | yes |
| `21-installed-cutover-and-patch-2-retirement` | 0 | yes |
| `22-capability-projection-reconciliation` | 1 | yes |
| `23-extend-sota-definition-in-sota-numerics-and-refactor-plugin` | 0 | yes |
| `24-remediate-sota-numerics-0-2-0-release-blockers` | 0 | yes |

Byte-identical to the `1,0,0,1,0,0` baseline recorded in 24-01-SUMMARY.md and re-confirmed by every subsequent plan in this phase. No real-corpus verdict moved as a result of this plan's edits.

(One self-caught measurement bug during this check, recorded in Deviations below: an initial loop used `echo "$(basename $d): exit $?"`, where the embedded `$(basename $d)` command substitution overwrote `$?` before it was read, producing a false "all six exit 0" reading. Immediately re-run with `$?` captured on its own line; the corrected reading matches the baseline exactly, confirmed twice more.)

### Corpus B -- Python suite (`python3 -m unittest discover -s tests -v`)

| Measurement point | Test count | Failures |
|---|---|---|
| Phase-24 start (24-01-SUMMARY.md) | 97 | 0 |
| This plan's final commit (`c8c8a1b`) | 125 | 0 |

No test was added, removed, or modified by this plan (the 97→125 growth is entirely from plans 24-01 through 24-04's own TDD work, already recorded in their summaries); this plan only re-ran the existing suite to confirm it is still green after this plan's own edits.

### Shell suites, at final commit `c8c8a1b`

| Suite | Result |
|---|---|
| `tests/test-gate-script-resolution.sh` | ALL PASS (including the new case2b) |
| `tests/test-session-start.sh` | ALL PASS |
| `tests/test-capability-auto-install.sh` | ALL PASS |

### Branch state

`git rev-list --left-right --count origin/main...HEAD` → `0` behind, `131` ahead. `gh pr view 4` reports `headRefOid` == local HEAD == `c8c8a1ba5053d75651fbdc3515fbacb6790f527c`[^1] (pushed during this plan), `mergeable: MERGEABLE`.

[^1]: Recorded as `c8c8a1ba5053d75651fbdc3515fbacb6790f527c` in git; the short form used throughout this document and DISPOSITION.md is `c8c8a1b`.

## D-17 hash trail

Bundle: `.gsd/capabilities/sota-numerics` in the target worktree. Hash tool: the exact `bundle_hash()` function from `hooks/capability-auto-install.sh` (same `find`/`sha256sum`/`sort` pipeline), replicated in a scratch script so it could be run against a temporarily-checked-out prior commit's tree without touching `~/.gsd`.

| Reading | Absolute path used | `sha256` |
|---|---|---|
| Pre-edit (commit `f1fb830`, plan start) | live worktree bundle path | `ac399b2c105ba03c089d2acd4716d259ac603ba030ad1473ed775aeca0dca2fc` |
| Post-edit (commit `c8c8a1b`, plan end) | live worktree bundle path (same path, `git checkout f1fb830 -- .gsd/capabilities/sota-numerics` then `git checkout c8c8a1b -- .gsd/capabilities/sota-numerics` used to compare both readings at one path) | `77c265411359afa3887e397e534347db95ca160208cea90e3f5cacaae9f4d2b9` |
| Live sidecar (`~/.gsd/capability-auto-install-sota-numerics.hash`), observed before this plan's restoration step | n/a (hook-maintained file) | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` |

The pre-edit and post-edit hashes differ, as expected (this plan's own commit changed `capability.json` inside the bundle). The live sidecar value matched **neither** -- consistent with the hazard 24-01-SUMMARY.md already flagged and left unresolved for this plan to close: the sidecar reflects some earlier, unaccounted-for hook fire against the in-tree worktree, not either endpoint this plan measured.

**Restoration (D-17's phase-end step):** ran `gsd_tools capability install /home/dd/.claude/plugins/cache/gsd-beads/sota-numerics/0.1.3/.gsd/capabilities/sota-numerics --scope global --yes`, which reported `{"status":"installed","id":"sota-numerics","version":"0.1.3","scope":"global"}`. Verified the restoration landed correctly with `diff -rq` (content comparison, not hash comparison) between `~/.gsd/capabilities/sota-numerics` and the plugin cache's own `0.1.3` copy: **zero differences**. A direct hash comparison between those two paths would have been misleading -- `sha256sum`'s output embeds the invoked file path, so two content-identical trees at different absolute paths produce different `bundle_hash()` values (`ac951688c28a...` for the mirror vs `6e11b0be72dd...` for the plugin cache, both computed against now-identical content); `diff -rq` is the correct comparison here, and it confirms the restoration succeeded. Did **not** rewrite `~/.gsd/capability-auto-install-sota-numerics.hash` directly (that file is hook-maintained bookkeeping, not bundle content); it will read as stale until the hook next runs, which does not affect the restored mirror's actual content.

## Decisions Made

See `key-decisions` in frontmatter above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corpus-A verification loop's `$?` was overwritten by an embedded command substitution**
- **Found during:** Task 3, first regression-evidence pass
- **Issue:** `echo "$(basename $d): exit $?"` reads `$?` *after* `$(basename $d)` has already run and reset it, so the loop reported "exit 0" for every phase directory regardless of the actual `check-alternatives.py` exit code -- a false "all six phases now pass" reading that looked exactly like the verdict drift this plan's own verification step exists to catch.
- **Fix:** Re-ran with `$?` captured on the line immediately after the `python3` invocation, with no intervening command. Confirmed the corrected reading (`1,0,0,1,0,0`) twice more, including a fully separate command substitution `RESULTS="$RESULTS $rc"` pattern that captures `$?` into a variable before any other command can touch it.
- **Files modified:** none (measurement-only)
- **Verification:** Three independent re-runs of the corpus check, all agreeing on `1,0,0,1,0,0`.
- **Committed in:** n/a (evidence, not code)

### Attempted and reverted (not silently absorbed)

**2. [Review finding vs. tested contract] P2-2's suggested fix broke 5 existing tests**
- **Found during:** Task 2, dispositioning REVIEW-CRITICAL-FINAL P2-2
- **Issue:** The review's suggested fix (mask `### Internal design alternatives` spans before `DECIDED_BY_RE.search`) is reasonable-sounding but conflicts with the project's own already-tested contract: `TestMixedAlternatives.test_mixed_bullets_exits_0`, `test_mixed_table_exits_0`, `test_internal_bullets_do_not_suppress_mechanism_table`, `TestDocumentedSyntax.test_documented_mixed_body_exits_0`, and `TestMixedCompatibility.test_exact_marker_allows_trailing_horizontal_whitespace` all explicitly expect exit 0 when a `Decided by:` line follows an unterminated internal H3.
- **Fix:** Implemented the change, ran the full suite, saw 5 failures, reverted immediately (`git diff --stat` confirmed clean). Recorded as declined in DISPOSITION.md with the exact test names.
- **Files modified:** none (reverted before commit)
- **Verification:** `python3 -m unittest discover -s tests -v` -> 125/125 OK, both before the attempt and after the revert.
- **Committed in:** n/a (never committed)

**3. [Review finding vs. tested contract] AGY's directory-named-like-a-plan fix broke 1 existing pinned test**
- **Found during:** Task 2, dispositioning REVIEW-AGY-FINAL's directory-crash finding
- **Issue:** Catching `OSError` in `validate_plan()` (matching the existing `UnicodeDecodeError` handler's shape) does produce a clean exit-2 message instead of a raw traceback -- but `TestUnreadablePlanFiles.test_directory_named_like_a_plan_exits_1`'s class docstring explicitly documents and pins the current raw-traceback/exit-1 behavior as a known, accepted discrepancy between the two error paths.
- **Fix:** Implemented, verified the clean message worked, ran the full suite, saw 1 failure, reverted immediately.
- **Files modified:** none (reverted before commit)
- **Verification:** `python3 -m unittest discover -s tests -v` -> 125/125 OK, both before the attempt and after the revert.
- **Committed in:** n/a (never committed)

---

**Total deviations:** 1 auto-fixed (measurement bug in this plan's own verification tooling), 2 attempted-and-reverted (recorded as declined/tracked in DISPOSITION.md rather than absorbed against the project's own tested contract).
**Impact on plan:** No scope creep; no incorrect fix landed.

## Issues Encountered

None blocking. See Deviations above.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- Every finding from every source (12 PR threads, 4 internal review artifacts) now has a recorded disposition; the set of known-and-unhandled findings is empty by construction, per this plan's objective.
- PR #4's head matches local HEAD; the branch is zero commits behind `origin/main`; both regression corpora are clean at the final commit.
- 5 tracking tickets remain open for the phase's own next milestone or a future hardening pass; none are release-blocking per their own review's severity/confidence, and each has an explicit acceptance criterion.
- The global capability mirror is restored to the released 0.1.3 bundle -- the phase's dev-worktree state no longer leaks into the machine-wide install.
- 24-09 (the publish decision, per D-19/D-20/D-22) can now proceed: the "known-and-unhandled findings" precondition its own objective depends on is satisfied.

## Self-Check: PASSED

- FOUND: `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/DISPOSITION.md`
- FOUND: `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-08-SUMMARY.md`
- FOUND commit `16a32ab` (orchestrator repo, DISPOSITION.md)
- FOUND commit `c8c8a1b` (target repo, `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`)
- FOUND bd tickets `gsd-beads-25vc.21.1`, `.21.2`, `.21.3`, `.21.4`, `.21.5` (all open, all parented under `gsd-beads-25vc.21`)
- FOUND PR #4 (`davdittrich/sota-numerics`) head `c8c8a1b`, 12/12 review threads resolved

All items independently re-verified via `git log --oneline --all`, `[ -f ... ]`, and `bd show` on 2026-09-08 after writing this file. No discrepancy found.

---
*Phase: 24-remediate-sota-numerics-0-2-0-release-blockers*
*Completed: 2026-09-08*
