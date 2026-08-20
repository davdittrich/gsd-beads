---
phase: 18-address-tech-debt-patch-check-doc-accuracy-changelog
verified: 2026-08-20T11:23:39Z
status: passed
score: 9/9 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 18: Address tech debt: patch-check doc accuracy + CHANGELOG Verification Report

**Phase Goal:** Every claim this capability makes about itself is true again, and nothing
withdrawn, stale, or already-fixed is still resolving: the patch-check docstring matches the
code, every patch-check problem message is uniformly marked and no consumer depends on that mark,
the CHANGELOG documents all four of Phase 17's requirements and files its own entries correctly,
both version declarations match what `main` actually carries, the withdrawn `v1.3.0` tag is gone,
the four already-shipped bd issues are closed, and both machine-local gsd-core patches are live
again on both runtime homes.

**Verified:** 2026-08-20T11:23:39Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Both machine-local gsd-core patches are live again on both runtime homes | ✓ VERIFIED | Live `check-patch` runs: `~/.claude/.../ship.md` → exit 0 `present (v2)`; `~/.claude/.../execute-plan.md` → exit 0 `present (v1)`; `~/.codex/.../ship.md` (via `--path`) → exit 0 `present (v2)`; `~/.codex/.../execute-plan.md` (via `--path`) → exit 0 `present (v1)`. `diff` of both `~/.claude` live files against `gsd-local-patches` backup: byte-empty. `wc -l ship.md` = 638. Marker count = 2. `grep -c '/gsd-secure-phase' ~/.codex/.../ship.md` = 0 (no cross-home leakage). `backup-meta.json.from_version` = `1.11.0` = `$HOME/.claude/gsd-core/VERSION` contents. |
| 2 | The four already-shipped Phase 17 bd issues are closed | ✓ VERIFIED | `bd show --json` for `gsd-beads-he1`, `-bzl`, `-v43`, `-t7a`: all four `"status": "closed"`. Follow-up issue `gsd-beads-72u` (mechanism gap that caused staleness) confirmed open/P3. |
| 3 | The withdrawn `v1.3.0` tag is gone | ✓ VERIFIED | `git tag -l v1.3.0` → empty. `git ls-remote --tags origin \| grep -c v1.3.0` → 0. `v1.3.1` untouched: `git tag -l v1.3.1` → `v1.3.1`; remote count 2. D-07/checkpoint answered option-a (delete origin+local), confirmed by 18-02-SUMMARY.md and by the tag's live absence. |
| 4 | The patch-check docstring matches the code (no false stream-convention claim) | ✓ VERIFIED | `grep -c 'benign-skip convention' sync.py` = 0; `grep -c 'stderr-only' sync.py` = 0 (both false claims removed at the docstring AND the `lifecycle_dispatch` call-site comment, `sync.py:941` — read live, states "all three plan:pre checks above and here print to stdout"). `check_sync_mode_value`'s docstring now states the true shared-stdout behavior and references WR-01. A new `# WR-01:` pinning comment sits directly above `check_patch`'s final `print(...)` call (read live at `sync.py:~2320`). |
| 5 | Every patch-check problem message is uniformly marked | ✓ VERIFIED | `grep -c '⚠' sync.py` = 6 (was 2). Both `ship-md` and `execute-plan` `not_found_msg`/`could_not_read_msg` templates confirmed marked via live grep for exact template strings (1 match each). `TestPatchChecksTable` holds 15 tests (was ~10/11), including the 4 new per-target `*_carries_the_marker` tests — full class re-run live: `Ran 15 tests`, `OK`. |
| 6 | No consumer depends on that mark any more | ✓ VERIFIED | `grep -c 'warning line'` = 0 in both `beads-recall/SKILL.md` and `beads-status/SKILL.md` (was 1 each). Both now contain `non-zero` (1 each), plus unchanged `onError: skip`/`verbatim` guarantees (per SUMMARY, spot-checked). Code review IN-02 independently confirmed the `"present"` substring appears only in `present_msg` templates, never in a failure-path template — the exit-code/`"present"`-absence heuristic cannot currently false-positive/negative. |
| 7 | CHANGELOG documents all four of Phase 17's requirements | ✓ VERIFIED | `awk` region `## 0.4.0`..`## 0.3.1` (live): `check_native_step_dispatch` count 1, `NATIVE_STEP_DISPATCH_WORKFLOW_FILES` 1, `NATIVE_STEP_DISPATCH_REGION_LINES` 1, `open-gsd/gsd-core#3687` 1, `plan:post` 2, `verify:post` 1 — TRUTH-03 (previously the sole omission per WR-03) now present alongside the pre-existing TRUTH-01/02/04 entries. `### Added` precedes `### Fixed`/`### Changed`/`### Breaking` in original relative order. |
| 8 | CHANGELOG files its own entries correctly (0.3.1 hook-timeout reclassified) | ✓ VERIFIED | `awk '### Performance'..'### Changed'` region: `120 s` count 0 (was 1). `awk '## 0.3.1'..'## 0.3.0'` region: `120 s` count 1 (relocated, not deleted), and contains `reduction`. Performance region retains `13.00 ms`, `0.91 ms`, `LC_ALL=C` (1 each). 0.3.1 subsection order unchanged: `### Fixed`, `### Performance`, `### Changed`, `### Known issues`. |
| 9 | Both version declarations match what `main` actually carries | ✓ VERIFIED | `plugin.json` live: `"version": "1.4.0"` (was `1.3.1`), file otherwise unchanged (`name`/`description`/`author`/`license`/`skills` intact), parses via `json.tool`. `capability.json` unchanged at `0.4.0` (Phase 17 bump, untouched here). `git diff --quiet v1.3.1..HEAD -- plugins .claude-plugin README.md` → exit 1 (non-zero = changes exist). `CHANGELOG.md` carries `## 0.4.0` (1 occurrence) matching `capability.json`'s version. |

**Score:** 9/9 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` | Names `verify-reapply-patches.cjs` and `check-patch` as the reapply-verification mechanism | ✓ VERIFIED | Live grep: `verify-reapply-patches.cjs` 2, `--path` 2, `check-patch` 5, `gsd-local-patches` 2. Both verbatim patch-content fenced blocks (v2/v1 markers) still present, undisturbed. |
| `$HOME/{.claude,.codex}/gsd-core/workflows/{ship,execute-plan}.md` (machine-local, untracked) | Both patches present on both homes | ✓ VERIFIED | `check-patch` exits 0 with correct version string on all 4 file×home combinations (see Truth 1). |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` | 6 `⚠`-marked templates, corrected docstring/comment, WR-01 pinning comment | ✓ VERIFIED | See Truths 4–5. |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` | 4 new per-target marker tests | ✓ VERIFIED | `TestPatchChecksTable` = 15 tests live, all pass. |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/{beads-recall,beads-status}/SKILL.md` | Surfacing keyed to exit code, not marker text | ✓ VERIFIED | See Truth 6. |
| `CHANGELOG.md` | Complete 0.4.0 section + corrected 0.3.1 filing | ✓ VERIFIED | See Truths 7–8. |
| `plugins/beads-lifecycle/.claude-plugin/plugin.json` | Version `1.4.0` | ✓ VERIFIED | See Truth 9. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `GSD-CORE-PATCH.md` | `$HOME/.claude/gsd-core/workflows/ship.md` | Patch Content (verbatim) block is the byte source the reapply inserts | ✓ WIRED | `diff` against `gsd-local-patches` backup byte-empty; marker present at count 2. |
| `sync.py` | `$HOME/.codex/gsd-core/workflows/execute-plan.md` | `check_patch`'s `--path` override probes a non-default runtime home | ✓ WIRED | Live `check-patch execute-plan --path` against the codex path exits 0, `present (v1)`. |
| `sync.py` (`PATCH_CHECKS`) | `beads-recall/SKILL.md`, `beads-status/SKILL.md` | Exit code (`0 if present else 1`), not message text | ✓ WIRED | Both SKILL.md files contain `non-zero`; `warning line` gone from both; `check_patch`'s return contract unchanged and independently confirmed live. |
| `plugin.json` | `.claude-plugin/marketplace.json` | Marketplace resolves `./plugins/beads-lifecycle` from branch | ✓ WIRED | `marketplace.json`'s `source` still points at the plugin dir; version bump lands on the resolved path. |
| `CHANGELOG.md` | `capability.json` | Version headings track capability version | ✓ WIRED | `## 0.4.0` heading matches `capability.json`'s `"version": "0.4.0"`, unchanged by this phase per D-06's explicit prohibition. |

### Requirements Coverage

Phase 18 declares `requirements: []` in all four plan frontmatters, and `.planning/REQUIREMENTS.md`
has no `Phase 18` mapping (`grep -n "Phase 18" REQUIREMENTS.md` → no match). This is consistent
with the phase's own stated scope: audit-sourced from `17-REVIEW.md` WR-01/02/03, ROADMAP Phase 17
Ship-step checks #1–#4, and `18-CONTEXT.md` D-01..D-09. No orphaned requirements found.

### Anti-Patterns Found

None. `TBD`/`FIXME`/`XXX` grep across all 7 tracked files this phase modified
(`sync.py`, `test_sync.py`, both `SKILL.md` files, `GSD-CORE-PATCH.md`, `CHANGELOG.md`,
`plugin.json`) returned zero matches.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full plugin-tree suite is green and strictly larger than pre-phase (248) | `python3 -m unittest discover -s tests -t tests` from `plugins/beads-lifecycle/.gsd/capabilities/beads/` | `Ran 252 tests in ~9s`, `OK` | ✓ PASS |
| `TestPatchChecksTable` (the class this phase's Task 1 extended) passes standalone | `python3 -m unittest tests.test_sync.TestPatchChecksTable -v` | 15/15 `ok` | ✓ PASS |
| Runtime overlay is byte-identical to tracked source | `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/` | silent, exit 0 | ✓ PASS |
| bd epic sub-issues all closed | `bd show gsd-beads-0lu.{1..12} --json` | all 12 `"status": "closed"` | ✓ PASS |
| Four stale Phase 17 bd issues closed | `bd show gsd-beads-{he1,bzl,v43,t7a} --json` | all 4 `"status": "closed"` | ✓ PASS |
| `v1.3.0` tag absent locally and on origin | `git tag -l v1.3.0`; `git ls-remote --tags origin \| grep -c v1.3.0` | empty; 0 | ✓ PASS |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` convention in this repo/phase, and neither
PLAN nor SUMMARY declares probe-based verification. Skipped.

### Human Verification Required

None. Every must-have in this phase resolves to a grep/diff/test/bd/git command with a
deterministic, machine-checkable answer, and all were independently re-run live during this
verification (not taken from SUMMARY.md claims).

### Gaps Summary

No gaps. All 9 observable truths, all 7 required artifacts, and all 5 key links verified live
against the current codebase and both runtime homes. `18-REVIEW.md` (code review, run
independently of this verification) found 0 critical and 1 warning issue; the warning
(`WR-01`: two `WINDOWS.md` ledger entries describing the same known, pre-existing, already-ticketed
overlay-tree test-path-resolution defect without cross-referencing each other) is a documentation
cross-reference nit in a *pre-existing* cross-phase ledger, not a Phase 18 must-have, and does not
affect any of this phase's 9 observable truths. It is noted here for completeness but is not a gap
against this phase's goal.

**Noted but out of scope (not a gap):** the gitignored runtime overlay
(`.gsd/capabilities/beads/`), when the suite is run *from inside it* rather than from the tracked
plugin tree, fails 14/252 tests due to a pre-existing `PLUGIN_ROOT = Path(__file__).resolve().parents[4]`
path-resolution bug in three test classes unrelated to any Phase 18 edit (`diff -rq` between the
two trees is byte-silent — same file content, different resolved ancestor depth). This was
discovered during 18-03 Task 3, is fully documented in `deferred-items.md` and `WINDOWS.md` entry
4, ticketed as `gsd-beads-2e2` (P2, open), and independently reproduced by both this verification
and `18-REVIEW.md`. None of Phase 18's must-haves require the overlay-tree suite to be green — only
the plugin-tree run (the one CI exercises) and `diff -rq` byte-equality, both of which pass.

---

_Verified: 2026-08-20T11:23:39Z_
_Verifier: Claude (gsd-verifier)_
