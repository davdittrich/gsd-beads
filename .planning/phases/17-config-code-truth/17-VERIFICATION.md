---
phase: 17-config-code-truth
verified: 2026-08-20T02:07:23Z
status: passed
score: 4/4 must-haves verified (all four requirements TRUTH-01..04)
behavior_unverified: 0
overrides_applied: 0
---

# Phase 17: Config/Code Truth Verification Report

**Phase Goal:** Everything this capability *declares* — a config enum, a set of lifecycle
dispatch points, a phase-number format, a patch marker — matches what its code actually does,
verified by a run rather than by prose. Four independent divergences close: a declared-but-unread
config key, a phase-number format the code rejects while this repo's own history contains it, a
hook that will start double-dispatching the moment upstream ships PR #3687, and two
structurally-identical patch detectors carrying two copies of one body.

**Verified:** 2026-08-20T02:07:23Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | TRUTH-04: a decimal-numbered phase (`1.5`, `01.5`, `10.1`, `11.1`) resolves at all beads lifecycle points via string-only helpers, no `int()`/`float()`/`Decimal()` | ✓ VERIFIED | `phase_regex_token`/`phase_dir_prefix` present at `sync.py:854,867`; live-executed `phase_regex_token('01.5') == '1\.5'`, `phase_dir_prefix('1.5') == '01.5'`; `PLAN_FILE_RE = r"^(\d+(?:\.\d+)?-\d+)-PLAN\.md$"` at `sync.py:86`; `class TestDecimalPhase` (16 methods) exists and passes in the 246-test full-suite run |
| 2 | TRUTH-03: `lifecycle_dispatch` gates `plan:post`/`verify:post` on a region-scoped, fail-open probe of PR #3687's native `kind == "step"` dispatch; `plan:pre`/`execute:wave:*` stay unconditional | ✓ VERIFIED | `check_native_step_dispatch` present at `sync.py:2342`; live-executed against the real installed `~/.claude/gsd-core/workflows/{plan-phase,verify-work}.md` (v1.11.0) — both report `not detected`, dispatch continues; `GSD-CORE-PATCH.md:245` documents the mechanism and cites `#3687`; test classes `TestNativeStepDispatchProbe`, `TestNativeStepDispatchProbeAgainstInstalledTree` present and passing |
| 3 | TRUTH-03 (D-06): `beads.sync_mode` governs only the explicit `create-issues` CLI strip decision; the hook path's `allow_strip` stays a literal `False`, ungated by config | ✓ VERIFIED | `read_sync_mode` at `sync.py:759`; `sed -n '/elif point == "plan:post"/,/elif point == "execute:wave:pre"/p' sync.py \| grep -c 'allow_strip=False'` → 1 (re-confirmed by direct read of the file); `TestCreateIssuesCliSyncModeGate`, `TestLifecycleDispatchNeverConsultsSyncMode` present |
| 4 | TRUTH-01: every value `capability.json` declares for `beads.sync_mode` (`authoritative`, `mirror`) has an observable, distinct, test-exercised effect; the retired `off` value and every doc claim describing an effect the code lacks are gone | ✓ VERIFIED | `capability.json:32-40` declares exactly `["authoritative","mirror"]`; description string states the true `create-issues`-strip effect; `git grep -n sync_mode -- . ':!.planning'` shows zero surviving false claims in `CHANGELOG.md`, `README.md`, `docs/prd-beads-capability.md`, `PRIME.md` (all read true against the code, verified directly); `class TestSyncModeDeclarationParity` pins the array by equality/order |
| 5 | TRUTH-01: a project already holding the retired value is notified through a channel reached without acting (D-04 Case 2), never crashes, never triggers a config write | ✓ VERIFIED | `check_sync_mode_value` at `sync.py:792`, wired into `lifecycle_dispatch`'s `plan:pre` branch at `sync.py:942`; `class TestCheckSyncModeValue` (18 methods) covers the full silent/notice truth table including the presence-vs-effective-value split; `! grep -Eq 'config\.json.*write_text\|write_text.*config\.json' sync.py` confirmed clean (no write path) |
| 6 | TRUTH-02: `check_shipmd_patch`/`check_execute_plan_patch` are served by one parameterized `check_patch` reader over a `PATCH_CHECKS` table; both Python function names and both in-file call sites survive unedited | ✓ VERIFIED | `PATCH_CHECKS` at `sync.py:136`, `check_patch` at `sync.py:2286`; both wrapper function names present and callable; `class TestPatchChecksTable` present; full suite green at 246 tests (`Ran 246 tests in 7.753s ... OK`) |
| 7 | TRUTH-02 (D-08): the two patch-check CLI verbs collapse to one (`check-patch <target> [--path]`), hard break, every caller updated in the same commit, ROADMAP Criterion 4 amended | ✓ VERIFIED | `sync.py:2506-2507` registers `check-patch` as the sole patch-check subparser; `beads-recall/SKILL.md:72-73`, `beads-status/SKILL.md:146` both call `check-patch`; `git grep -nE 'check-shipmd-patch\|check-execute-plan-patch' -- . ':!.planning'` returns zero hits; `.planning/ROADMAP.md:128-134` amended with the D-08 supersession line; checkpoint decision confirmed via `bd comments gsd-beads-u67.10` (option-a, recommended verb shape, resolved by the actual user) |

**Score:** 4/4 requirements (TRUTH-01, TRUTH-02, TRUTH-03, TRUTH-04) verified with passing evidence; 0 present-but-behavior-unverified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` | `phase_regex_token`, `phase_dir_prefix`, widened `PLAN_FILE_RE`, `check_native_step_dispatch`, `read_sync_mode`, `SYNC_MODE_VALUES`, `check_sync_mode_value`, `PATCH_CHECKS`, `check_patch` | ✓ VERIFIED | All symbols confirmed present at cited line numbers by direct grep of the tracked source |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` | `TestDecimalPhase`, `TestNativeStepDispatchProbe`(+installed-tree variant), `TestSyncModeDeclarationParity`, `TestCheckSyncModeValue`, `TestPatchChecksTable` | ✓ VERIFIED | All classes present; full suite run confirms 246 tests, `OK` |
| `capability.json` | `version: 0.4.0`; `beads.sync_mode.values == ["authoritative","mirror"]` | ✓ VERIFIED | Both read directly from the tracked file |
| `CHANGELOG.md` | `## 0.4.0` section covering TRUTH-04 (Fixed), TRUTH-01 (Changed), TRUTH-02 (Breaking) | ✓ VERIFIED (with a noted gap) | Section present and accurate for TRUTH-01/02/04. **Does not mention TRUTH-03** (`check_native_step_dispatch`/PR #3687) at all — confirmed by direct grep; this matches the code review's WR-03 finding (WARNING, not blocking; no PLAN's `files_modified`/`must_haves` required a CHANGELOG entry for TRUTH-03) |
| `README.md`, `docs/prd-beads-capability.md`, `PRIME.md` | Doc sweep — no claim of an effect the code lacks | ✓ VERIFIED | Read directly; all three describe the true, current `create-issues`-strip semantics |
| `.planning/ROADMAP.md` | Phase 17 Success Criterion 4 amended for D-08 | ✓ VERIFIED | Amendment present at lines 128-134 |
| `.planning/intel/API-SURFACE.md` | Regenerated CLI surface reflecting the collapsed `check-patch` verb | ✓ VERIFIED | `check-patch` present per SUMMARY's cited command output; not independently re-run (low-risk, generated artifact) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `sync.py` (`get_phase_header`/`extract_phase_mentions`) | `sync.py` (`phase_regex_token`) | regex construction | ✓ WIRED | Live-executed; matches expected escaped tokens |
| `sync.py` (`_resolve_default_phase_dir`) | `.planning/phases/<decimal>-<slug>/` | `phase_dir_prefix` | ✓ WIRED | Live-executed `phase_dir_prefix('1.5') == '01.5'` |
| `sync.py` (`lifecycle_dispatch`) | `$CLAUDE_CONFIG_DIR/gsd-core/workflows/{plan-phase,verify-work}.md` | `check_native_step_dispatch` | ✓ WIRED | Live-executed against the real installed 1.11.0 tree; both points report not-detected |
| `sync.py` (`main()`'s `create-issues` CLI) | `.planning/config.json` | `read_sync_mode` | ✓ WIRED | Confirmed present at the CLI dispatch site (`sync.py:2535-2543`) |
| `capability.json` | `sync.py` | `read_sync_mode`/every declared value read by a tested code path | ✓ WIRED | `TestSyncModeDeclarationParity.test_every_declared_value_has_a_covering_test` present and passing |
| `.planning/config.json` | hook `additionalContext` | `check_sync_mode_value` stdout at `plan:pre` | ✓ WIRED | Wired into `lifecycle_dispatch`'s `plan:pre` branch (`sync.py:942`) alongside the two existing patch checks |
| `beads-status/SKILL.md` Step 2d | `sync.py` | `check-patch ship-md` CLI verb | ✓ WIRED | Confirmed by direct grep of the SKILL.md file |
| `beads-recall/SKILL.md` Step 3.5 | `sync.py` | `check-patch ship-md`/`check-patch execute-plan` | ✓ WIRED | Confirmed by direct grep |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite reports the claimed count and is green | `python3 -m unittest discover -s tests -t tests` (from `plugins/beads-lifecycle/.gsd/capabilities/beads`) | `Ran 246 tests in 7.753s ... OK` | ✓ PASS |
| Runtime overlay re-syncs to the tracked source | `gsd-tools capability update beads --scope project` then `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/` | Overlay was stale before the update command (differed in 6 files — a session-local drift artifact of this checkout's gitignored `.gsd/`, not tracked in git); after running the documented `capability update` command, `diff -rq` is silent | ✓ PASS |
| Decimal-phase resolution live | `phase_regex_token`/`phase_dir_prefix` executed directly | `phase_regex_token('01.5') == '1\.5'`; `phase_dir_prefix('1.5') == '01.5'` | ✓ PASS |
| Native-dispatch probe against the real installed gsd-core 1.11.0 tree | `check_native_step_dispatch('plan:post')` / `('verify:post')` executed directly | Both report `not detected`, `0` (exit code), naming the real installed path | ✓ PASS |
| CLI collapse — no surviving retired-verb references | `git grep -nE 'check-shipmd-patch\|check-execute-plan-patch' -- . ':!.planning'` | Zero hits | ✓ PASS |
| Doc sweep — no surviving false `sync_mode` claims | `git grep -n sync_mode -- . ':!.planning'` reviewed line-by-line | All non-code hits read true against the shipped behavior | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| TRUTH-01 | 17-03 | Every `beads.sync_mode` value has an observable effect; doc sweep; D-04 migration notice | ✓ SATISFIED | See Observable Truths #4-5 |
| TRUTH-02 | 17-04 | One table-driven reader serves both patch checks; CLI collapse (D-08) | ✓ SATISFIED | See Observable Truths #6-7 |
| TRUTH-03 | 17-02 | `lifecycle-dispatch` hook stays correct across PR #3687; `allow_strip` ruling (D-06) | ✓ SATISFIED | See Observable Truths #2-3 |
| TRUTH-04 | 17-01 | Decimal-numbered phase resolves at all lifecycle points | ✓ SATISFIED | See Observable Truths #1 |

No orphaned requirements: `.planning/REQUIREMENTS.md`'s Phase 17 section declares exactly TRUTH-01..04, and each ID appears in exactly one plan's `requirements` frontmatter field (17-01→TRUTH-04, 17-02→TRUTH-03, 17-03→TRUTH-01, 17-04→TRUTH-02). All four are accounted for.

**Traceability-tracking discrepancy (not a requirement-coverage failure, noted for correction):**
`.planning/REQUIREMENTS.md` line 22 (`- [ ] **TRUTH-01**`) and line 160 (`| TRUTH-01 | Phase 17 | 17-03 | ... | Pending |`) are stale — TRUTH-01 is fully implemented and verified (Observable Truths #4-5) but was never flipped to `[x]`/`Complete`. Root cause confirmed by `git blame`: plans 17-01, 17-02, 17-04 each carried their own `docs(XX): complete ... plan` commit that updated `REQUIREMENTS.md`'s checkbox and traceability row for their own requirement (commits `8d50cf2`, `eb3be71`, `0bc3e63`); plan 17-03's equivalent commit (`64317eb`) touched only `.gsd-capabilities.json` and the SUMMARY file, omitting the same REQUIREMENTS.md update. This is not flagged as a blocking gap because `execute-phase.md`'s own `update_roadmap` step (`gsd_run query phase.complete "17"`) is the standard, idempotent mechanism that updates REQUIREMENTS.md traceability for the whole phase once verification passes, and that step runs immediately after this report is returned — it is expected to close this exact discrepancy. Recorded here so it is visibly checked (per the instruction to cross-reference every requirement ID against REQUIREMENTS.md) rather than silently passed over.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `CHANGELOG.md` | 0.4.0 section | Omits any mention of TRUTH-03 (`check_native_step_dispatch`, PR #3687, the `plan:post`/`verify:post` stand-down mechanism) | ℹ️ Info (matches code review WR-03, WARNING) | No functional impact; not required by any plan's `files_modified`/`must_haves`; a future reader of the changelog alone would not learn the hook now silently stands down once gsd-core ships #3687 |
| `sync.py:2426-2453` (`check_native_step_dispatch`'s final detection loop) | — | Fence-parity (`in_fence`) is tracked for region-boundary detection but not consulted in the final `kind == "step"` match loop — a latent false-detected risk for an unqualified step-arm mention *inside* a fenced example within the anchor's region | ℹ️ Info (code review WR-05, confidence 55, no confirmed live defect against the real installed 1.11.0 tree) | Not exercised by current shipped workflow files; `TestNativeStepDispatchProbeAgainstInstalledTree` passes against the real tree today |
| `sync.py:770-776` (`SYNC_MODE_VALUES`) | — | No direct parity test asserting `sync.SYNC_MODE_VALUES == frozenset(capability.json's declared values)` — `TestSyncModeDeclarationParity` pins `capability.json`'s array independently, not against the runtime constant | ℹ️ Info (code review WR-04) | A future edit to one copy without the other would not be caught by a test until the arm-proving tests separately fail |

No 🛑 blocker-severity anti-patterns; no TBD/FIXME/XXX debt markers found in any file modified by this phase.

### Human Verification Required

None. Every truth's supporting behavior is exercised by a passing test (not merely symbol presence) or was directly, live-executed during this verification against real installed artifacts (the machine's actual gsd-core 1.11.0 workflow files, a live `capability update`, and direct function calls).

### Gaps Summary

No blocking gaps. All four requirements (TRUTH-01 through TRUTH-04) are implemented, tested, and independently confirmed live against the real codebase — not merely claimed in SUMMARY.md prose. The phase's own theme (declared vs. actual truth) was applied reflexively to its own artifacts during this verification:

- The runtime `.gsd/` overlay in this specific checkout was initially stale relative to the tracked source (a session-local, gitignored-state artifact, not a git-tracked defect) — resolved by running the documented `capability update` command, after which `diff -rq` was silent, confirming the resync mechanism itself works as designed.
- `.planning/REQUIREMENTS.md` has one stale traceability entry (TRUTH-01) that the standard post-verification `update_roadmap` step is expected to correct automatically; flagged above for visibility, not as a blocker.
- Two WARNING-level findings from `17-REVIEW.md` (CHANGELOG.md omitting TRUTH-03, and a test-coverage gap for `SYNC_MODE_VALUES`/`capability.json` parity) remain open; neither affects a `must_haves` truth, artifact, or key link for this phase, and are recorded above as low-severity anti-patterns rather than gaps.

---

*Verified: 2026-08-20T02:07:23Z*
*Verifier: Claude (gsd-verifier)*
