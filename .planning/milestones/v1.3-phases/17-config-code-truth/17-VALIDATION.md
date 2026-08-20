---
phase: 17
slug: config-code-truth
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-20
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python stdlib `unittest` |
| **Config file** | none — discovery-based |
| **Quick run command** | `cd plugins/beads-lifecycle/.gsd/capabilities/beads && python3 -m unittest discover -s tests -t tests` |
| **Full suite command** | `cd plugins/beads-lifecycle/.gsd/capabilities/beads && python3 -m unittest discover -s tests -t tests` |
| **Estimated runtime** | ~8 seconds (baseline: `Ran 164 tests in 4.792s`; post-phase: `Ran 246 tests in 7.905s`; post-audit: `Ran 248 tests in 7.953s / OK`) |

---

## Sampling Rate

- **After every task commit:** Run the full suite — even at ~8s it stays well under the 10s max feedback latency, so no quick/full split is warranted
- **After every plan wave:** Run the full suite
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

*Correction (this audit): the skeleton's "under 5s" claim went stale as the suite grew from 164→246 tests across the phase's 4 plans; corrected above to match the measured runtime.*

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| gsd-beads-u67.1 | 17-01 | 1 | TRUTH-04 | T-17-01-01/02 | Decimal-numbered phase resolves at `plan:pre` via string-only helpers, no `int()`/`float()`/`Decimal()` | unit | `python3 -m unittest tests.test_sync.TestDecimalPhase.test_decimal_phase_matches_at_plan_pre tests.test_sync.TestDecimalPhase.test_integer_phase_control_arm_still_matches` | ✅ | ✅ green |
| gsd-beads-u67.2 | 17-01 | 1 | TRUTH-04 | T-17-01-01/02 | Boundary/adjacency/precision/ordering/path-separator rejection/idempotency for decimal phases | unit | `python3 -m unittest tests.test_sync.TestDecimalPhase` (16 methods) | ✅ | ✅ green |
| gsd-beads-u67.3 | 17-01 | 1 | TRUTH-04 | T-17-01-SC | Runtime mirror (`.gsd/capabilities/beads/`) stays byte-identical to tracked source (`plugins/beads-lifecycle/.gsd/capabilities/beads/`) | integration (command) | `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/` (silent = pass) | N/A — deterministic filesystem command | ✅ green |
| gsd-beads-u67.4 | 17-02 | 2 | TRUTH-03 | T-17-02-01 | `lifecycle_dispatch` hook stands down for `plan:post`/`verify:post` once gsd-core PR #3687's native `kind == "step"` dispatch is detected | unit | `python3 -m unittest tests.test_sync.TestNativeStepDispatchProbe tests.test_sync.TestNativeStepDispatchProbeAgainstInstalledTree` | ✅ | ✅ green |
| gsd-beads-u67.5 | 17-02 | 2 | TRUTH-03 | T-17-02-01 | `plan:post`/`verify:post` are gated on the probe; `plan:pre`/`execute:wave:*` stay unconditional | unit | `python3 -m unittest tests.test_sync.TestLifecycleDispatchNativeGate tests.test_sync.TestLifecycleDispatchPointsAgreeWithHook` | ✅ | ✅ green |
| gsd-beads-u67.6 | 17-02 | 2 | TRUTH-03 (D-06) | T-17-02-02 | `beads.sync_mode` gates only the explicit `create-issues` CLI strip decision; hook path's `allow_strip` stays a literal `False` | unit | `python3 -m unittest tests.test_sync.TestReadSyncMode tests.test_sync.TestCreateIssuesCliSyncModeGate tests.test_sync.TestLifecycleDispatchNeverConsultsSyncMode` | ✅ | ✅ green |
| gsd-beads-u67.7 | 17-03 | 3 | TRUTH-01 | T-17-03-01 | Every value `capability.json` declares for `beads.sync_mode` has an observable, distinct, test-exercised effect | unit | `python3 -m unittest tests.test_sync.TestSyncModeDeclarationParity tests.test_sync.TestSyncModeAdjacencyAndEncoding` | ✅ | ✅ green |
| gsd-beads-u67.8 | 17-03 | 3 | TRUTH-01 (D-04) | T-17-03-02/03/04 | A project holding the retired `off` value is notified through a channel reached without acting; never crashes, never writes config | unit | `python3 -m unittest tests.test_sync.TestCheckSyncModeValue` (18 methods) | ✅ | ✅ green |
| gsd-beads-u67.9 | 17-04 | 4 | TRUTH-02 (D-09/D-10) | T-17-04-01/02 | One parameterized `check_patch` reader over `PATCH_CHECKS` serves both `check_shipmd_patch`/`check_execute_plan_patch` | unit | `python3 -m unittest tests.test_sync.TestCheckShipmdPatch tests.test_sync.TestPatchChecksTable` | ✅ | ✅ green |
| gsd-beads-u67.10 | 17-04 | 4 | TRUTH-02 (D-08) | T-17-04-03 | Human sign-off on the one-way CLI verb collapse before it ships (governance gate, not a testable behavior) | manual (`checkpoint:decision`, `gate="blocking"`) | none — resolved via `bd comment` on the issue (option-a confirmed by user) | N/A | see Manual-Only |
| gsd-beads-u67.11 | 17-04 | 4 | TRUTH-02 | T-17-04-03 | The two patch-check CLI verbs collapse to one (`check-patch <target> [--path]`); every caller updated in the same commit | unit + integration | `python3 -m unittest tests.test_sync.TestPatchChecksTable`; `! git grep -nE 'check-shipmd-patch\|check-execute-plan-patch' -- . ':!.planning'` (zero hits) | ✅ | ✅ green |
| gsd-beads-u67.12 | validate-17 | audit | TRUTH-01 | — | `sync.py`'s `SYNC_MODE_VALUES` constant and `capability.json`'s declared `values` array cannot silently diverge | unit | `python3 -m unittest tests.test_sync.TestSyncModeDeclarationParity.test_sync_module_constant_matches_capability_json` | ✅ | ✅ green |
| gsd-beads-u67.13 | validate-17 | audit | TRUTH-03 | T-17-02-01 | `check_native_step_dispatch` never mistakes a `kind == "step"` line inside a fenced doc example for a live dispatch arm | unit | `python3 -m unittest tests.test_sync.TestNativeStepDispatchProbe.test_generic_step_arm_inside_fenced_doc_example_in_region_is_not_a_false_positive` | ✅ | ✅ green (was ❌ red pre-fix, confirmed) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covered all phase requirements — `tests/test_sync.py` (4129 lines pre-phase, 5332 lines post-audit) is the sole test file and the discovery harness was already in place. No framework install needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|--------------------|
| Sign-off on the one-way CLI verb collapse (`check-shipmd-patch`/`check-execute-plan-patch` → `check-patch <target>`) before it ships | TRUTH-02 (D-08, gsd-beads-u67.10) | Governance gate on an irreversible, published-plugin CLI contract change — CONTEXT.md rates it `one-way` (no deprecation window); the project's `REVERSIBILITY_GATES` policy requires human sign-off before such a task executes, regardless of how well-reasoned the recommendation is. Not a behavior to verify — the *effect* of the decision (the actual collapse) is fully covered by gsd-beads-u67.11's automated tests above. | Review `bd show gsd-beads-u67.10` and its `bd comments` for the recorded decision; re-run only if the CLI verb contract changes again. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (gsd-beads-u67.10 is the sole exception — inherently manual, documented above)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (none were missing — existing infra covered every requirement)
- [x] No watch-mode flags
- [x] Feedback latency < 10s (measured ~8s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-08-20

---

## Validation Audit 2026-08-20

Ran via `/gsd-validate-phase 17` (State A — VALIDATION.md skeleton existed, Per-Task Verification Map was empty). Discovery agent cross-referenced all 4 plans/summaries against `tests/test_sync.py`; findings independently re-verified against live source before acting.

| Metric | Count |
|--------|-------|
| Requirements audited | 4 (TRUTH-01..04) |
| Tasks audited | 11 |
| Already COVERED (no action) | 9 |
| MANUAL-ONLY (inherent, no action) | 1 (gsd-beads-u67.10) |
| Gaps found | 2 |
| Gaps resolved | 2 |
| Escalated | 0 |

**Gap 1 (gsd-beads-u67.12, test-only):** `TestSyncModeDeclarationParity` pinned `capability.json`'s declared `beads.sync_mode` values but never cross-checked `sync.py`'s `SYNC_MODE_VALUES` runtime constant against it. Added `test_sync_module_constant_matches_capability_json` — green immediately, no implementation change needed. Commit `373e7fb`.

**Gap 2 (gsd-beads-u67.13, real defect — not just a missing test):** `check_native_step_dispatch`'s final detection loop (`sync.py:2446-2453` pre-fix) computed the region boundary in one fence-tracking pass, then matched `kind == "step"` arms in a second, fence-blind pass over the sliced lines — losing fence state entirely. A `kind == "step"` line inside a fenced documentation example within the anchor's region would false-positive as a live dispatch arm and wrongly stand native dispatch down for that lifecycle point — the exact failure class TRUTH-03 / threat `T-17-02-01` exists to prevent. Currently latent: no live installed workflow file triggers it. Confirmed by direct code read (not just the discovery agent's report) before acting. User chose "fix both now" over ticket-only. Regression test `test_generic_step_arm_inside_fenced_doc_example_in_region_is_not_a_false_positive` written first and confirmed RED (`1 != 0`) against pre-fix code, then `sync.py` merged the two passes into one that carries `in_fence` through both the boundary scan and the arm match. Test now green; full suite green (248 tests, was 246). Commit `0f8decb`.

Both gaps tracked as bd issues `gsd-beads-u67.12`, `gsd-beads-u67.13` (children of epic `gsd-beads-u67`), closed on completion.

**Note (non-blocking, out of Nyquist scope):** `CHANGELOG.md`'s `## 0.4.0` section omits any mention of TRUTH-03 (`check_native_step_dispatch`, PR #3687). Already flagged as WARNING (non-blocking) in `17-REVIEW.md` (WR-03) and `17-VERIFICATION.md`; not a test-coverage gap, left for a docs pass.
