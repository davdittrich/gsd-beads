---
phase: 21-installed-cutover-and-patch-2-retirement
verified: 2026-09-01T23:34:30+02:00
status: passed
score: 5/7 must-haves verified
behavior_unverified: 2
overrides_applied: 0
behavior_unverified_items:

  - truth: "Patch 2 retirement began only after the ordered pre-removal gate; every post-removal proof repeated, and a post-removal failure restored captured workflow bytes before SPEC_FAILURE."
    test: "Review an immutable, time-ordered record of the pre-removal gate, retirement, repeated post-removal gate, and rollback-on-failure path; or add a behavioral transaction test that exercises those transitions in an isolated runtime."
    expected: "The pre-removal CUT-01/negative matrix completes before the marker deletion; a post-removal failure restores exactly the captured workflow bytes and exits SPEC_FAILURE."
    why_human: "The current runtime proves only the post-removal state. The one-time transaction left no executable behavioral test or immutable run receipt; SUMMARY.md is not evidence."
  - truth: "Missing or empty proof inputs fail, proof and mutation stages remain separate, and the D-04 order is stable and repeated after removal."
    test: "Inspect an immutable phase-execution receipt or execute a dedicated isolated transaction test covering D-04 ordering and failure rollback."
    expected: "Empty/missing inputs stop before mutation, and the repeated post-removal proof follows the same enforced stage order."
    why_human: "Presence checks and the current post-removal public matrix cannot reconstruct the historical pre-removal ordering invariant."
human_verification:

  - test: "Accept or reject the historical D-04/rollback evidence."
    expected: "A durable external receipt or a new isolated behavior test proves pre-gate → removal → repeat/rollback ordering."
    why_human: "No current test or immutable receipt exercises the phase's irreversible historical transition."
---

# Phase 21: Installed Cutover and Patch 2 Retirement Verification Report

**Phase Goal:** Installed resolution is proven before Patch 2 removal; Patch 1 remains.
**Verified:** 2026-09-01T23:34:30+02:00
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

Implementation HEAD was `d3b8d2686ba57f545a310e5e7346cbdf1d92b2de`. The release source used for installed-tree proof was clean worktree `153a61c` (capability `0.6.0`), and that release contains the Phase implementation (`d3b8d26` is an ancestor of merge `f8a8fd9`).

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Natural Phase 21 tracer has matching native/legacy identity and live Beads row | ✓ VERIFIED | `21-01-PLAN.md` has `tracker-id="beads:gsd-beads-3h2.1"` and matching `<beads-id>`; host `bd --readonly show` resolved the real closed row. Confidence 100/100. |
| 2 | Tracked/project/global/bootstrap capability trees are non-empty, byte-identical, and global selection reaches the bootstrap resolver | ✓ VERIFIED | `diff -qr` produced no output between release `153a61c`, Claude cache, Codex cache, and `/home/dd/.gsd/capabilities/beads`; all manifests are `0.6.0`. Non-project registry selected one active global Beads bundle. Confidence 100/100. |
| 3 | Public `task resolve-content` returns all authored fields from live Beads | ✓ VERIFIED | From `/home/dd`, with absolute release plan and runtime-derived `BEADS_DIR`, the public command returned `resolved: true`, five fields, and the authored first `readFirst` path. Confidence 100/100. |
| 4 | Unknown identity, legacy-only task, unavailable `bd`, and malformed resolver stdout fail closed | ✓ VERIFIED | Four isolated public controls each exited `1` with zero stdout: unknown, real Phase 20 legacy task, `PATH` without `bd`, and executable malformed-stdout wrapper. Confidence 100/100. |
| 5 | Retirement happened only after the ordered gate and rolls back exact workflow bytes on post-gate failure | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Commit order (`9da2d34` before `902488c`) is supporting context only. No current test or immutable receipt exercises the historical removal/rollback transition. Confidence 100/100. |
| 6 | No active Patch 2 surface remains; Patch 1 remains installed and independently passes | ✓ VERIFIED | Patch 2 marker absent from both Claude/Codex `execute-plan.md`; v2 Patch 1 marker is present and `sync.py check-patch ship-md --path` passed for both `ship.md` files. Static active-source scan found no active Patch 2 checker/wrapper/detector. Confidence 100/100. |
| 7 | Empty/missing inputs fail and proof/mutation ordering stays separate and repeats after removal | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Current parity and four-negative checks prove the observable failure direction, but not the historical D-04 stage-order/rollback invariant. Confidence 100/100. |

**Score:** 5/7 truths verified (2 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `scripts/sync.py` | Native resolver and surviving Patch 1 checker | ✓ VERIFIED | Substantive `resolve_task_content()` runs fixed `bd show <id> --json`; `check_patch()`/`check_shipmd_patch()` remain wired. |
| `tests/test_sync.py` | Native/Patch 1 regression coverage | ✓ VERIFIED | 288-test suite passed at implementation HEAD; focused five-field/argv test passed from release source. |
| `GSD-CORE-PATCH.md` | Patch 1-only contract | ✓ VERIFIED | No active Patch 2 operational contract; historical references are confined to release history. |
| `skills/beads-recall/SKILL.md` | Plan-time Patch 1 detector only | ✓ VERIFIED | Key-link query and active source scan confirm surviving ship-md target. |
| `capability.json` | Native resolver declaration | ✓ VERIFIED | Release and all installed manifests declare `0.6.0` and the resolver invocation. |
| `.agents/skills/beads/PRIME.md` | Patch 1/native lifecycle guidance | ✓ VERIFIED | Artifact check passed; no active Patch 2 instruction found. |
| `README.md` | Installed native-resolution contract | ✓ VERIFIED | Artifact check passed; documents fail-closed native resolution. |
| `CHANGELOG.md` | Append-only retirement history | ✓ VERIFIED | Artifact check passed; Patch 2 mention is historical, not operational wiring. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| Phase tracer plan | Native resolver | matching `tracker-id` / `<beads-id>` | ✓ WIRED | Public live resolution of `beads:gsd-beads-3h2.1` proves the link. |
| `task resolve-content` | Live Beads | fixed `bd show <id> --json` | ✓ WIRED | Resolver source uses fixed argv; focused regression and live public response passed. |
| `sync.py` | `beads-recall/SKILL.md` | surviving `check-patch ship-md` | ✓ WIRED | Automated key-link query verified this declared link. |
| Runtime workflow | Patch 2 marker retirement | marker-bounded absence | ✓ WIRED | Both host runtime workflows lack the Patch 2 marker; Patch 1 blocks remain intact. |

`verify.key-links` reported three declarative patterns as unparseable because their `from` values are commands/runtime descriptions rather than repository paths; direct live evidence above verifies those links.

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| Native resolver | task content | `bd --readonly show gsd-beads-3h2.1 --json` | Live Beads row, not fixture/static fallback | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Public live resolution | non-project `gsd_run task resolve-content --plan <absolute release plan> --task-id beads:gsd-beads-3h2.1 --raw` with derived `BEADS_DIR` | `resolved: true`, five fields | ✓ PASS |
| Unknown native identity | same public command with unknown id | exit 1, zero stdout | ✓ PASS |
| Legacy-only Phase 20 task | same public command with real legacy task | exit 1, zero stdout | ✓ PASS |
| `bd` unavailable | same public command with bounded no-`bd` PATH | exit 1, zero stdout | ✓ PASS |
| Malformed resolver stdout | same public command with executable malformed `python3` in `/dev/shm` | exit 1, zero stdout | ✓ PASS |
| Capability suite | `TMPDIR=/dev/shm PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t tests` | 288 tests, OK | ✓ PASS |
| Exact internal adapter contract | named `TestResolveTaskContent.test_round_trip_emits_exact_five_key_json_and_typed_lists` | 1 test, OK | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| CUT-01 | 21-01 | Installed capability resolves a live task and all trees match | ✓ SATISFIED | Fresh global public proof plus four-tree release/installed parity. |
| CUT-02 | 21-01 | Retire Patch 2 after proof while preserving Patch 1 | ? NEEDS HUMAN | Current end state and Patch 1 are verified; historical ordered-removal/rollback evidence is not. |

No orphaned Phase 21 requirements: the plan declares both roadmap requirements.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/test_sync.py` | CUT-01/CUT-02 | 288-suite plus focused resolver test | Requirement-linked resolver test active; unrelated `skipUnless(bd)` tests exist | None found | Behavioral/value | PASS |

The focused resolver test spies the exact `bd show <id> --json` argv and validates all five typed fields. No disabled test is the sole evidence for either requirement.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `CHANGELOG.md` | 9 | Historical “Patch 2” entry | ℹ️ Info | Required retirement history, not active wiring. |

No unreferenced `TBD`, `FIXME`, or `XXX` marker was found in Phase 21 artifacts. Ponytail review found no new dependency, fallback, cache, retry, or single-use abstraction in the verified resolver path.

### Decision Coverage

All 15 trackable Phase 21 context decisions are honored by shipped artifacts (non-blocking decision-coverage gate).

## Human Verification Required

### 1. Historical D-04 ordering and rollback

**Test:** Review a durable external transaction receipt, or run a dedicated isolated transaction test that reaches a post-removal failure.

**Expected:** It proves pre-gate → marker removal → repeated post-gate ordering and exact-byte workflow restore before `SPEC_FAILURE`.

**Why human:** The current post-removal runtime, commits, and passing public matrix cannot recreate the historical state transition; SUMMARY claims are not proof.

## Gaps Summary

No missing implementation was found. The Escalation Gate is evidence-only: accept a durable historical receipt, or add a narrowly isolated transition/rollback test before treating this phase as fully automated `passed`.

---

_Verified: 2026-09-01T23:34:30+02:00_
_Verifier: the agent (gsd-verifier)_
