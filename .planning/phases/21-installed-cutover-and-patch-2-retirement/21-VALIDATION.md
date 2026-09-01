---
phase: "21"
slug: "installed-cutover-and-patch-2-retirement"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-01"
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python 3 standard-library `unittest` |
| **Config file** | none |
| **Quick run command** | `bash -lc 'set -euo pipefail; cd /home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads; TMPDIR=/dev/shm PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sync.TestIdentityBinding -v'` |
| **Full suite command** | `bash -lc 'set -euo pipefail; cd /home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads; TMPDIR=/dev/shm PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t tests'` |
| **Estimated runtime** | ~5 seconds for the capability suite; the live cutover transaction is separately bounded by explicit resolver and `bd` timeouts |

---

## Sampling Rate

- **After every task commit:** Run the focused test class named by that task plus `python3 -m py_compile scripts/sync.py` when `sync.py` changed.
- **After every plan wave:** Run the full capability suite.
- **Before `$gsd-verify-work`:** Re-run the post-retirement public positive, four one-factor public negatives, full capability suite, and independent Patch 1 check.
- **Max feedback latency:** 30 seconds for focused static/unit gates; each live resolver/Beads probe must carry its declared bounded timeout.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | CUT-01 | Global-install proof cannot be satisfied by a project overlay; malformed or unavailable resolver inputs stop non-zero without fallback. | Existing exact-argv spy plus fresh live public integration | Self-contained bounded `/dev/shm` transaction deriving bootstrap paths before parsing the stale global manifest, treating missing/non-exact resolver metadata as the approved install trigger, then proving base HEAD, natural identities/live row, four-tree tracked/project/global/bootstrap parity, explicit executed-resolver path under the recorded public environment, global-only selection, authored five-field positive, four isolated negatives, mutation absence, and cleanup; then the exact `bd show` argv spy | ✅ inline / existing | ⬜ pending |
| 21-01-02 | 01 | 2 | CUT-02 | Patch 2 is deleted only after the pre-removal gate; Patch 1 remains byte-identical and independently executable. | TDD retirement regression plus fresh live public integration | Execution-local exact RED producer, eight-file canonical post-edit source SHA-256, seven-surface residue/Patch-1 enduring-boundary/rollback transaction, repeated four-tree public positive/four-negative transaction and argv spy, Python compile plus full capability suite | ✅ inline / existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] No new harness or source scaffold is required: Task 1 embeds the bounded execution-local public transaction and reuses the existing exact-argv adapter spy.
- [x] Task 2 embeds the post-removal residue, Patch 1 identity, rollback-hash, repeated public matrix, compile, and full-suite commands; its tests-first edit deletes or narrows every Patch-2-owned test while retaining the public native contract.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | CUT-01, CUT-02 | Every volatile registry, live-row, installed-byte, negative-control, rollback, residue, Patch 1, compile, and full-suite claim is decided by the task's explicit automated commands. | No manual-only acceptance claim remains. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verification with immediate failure bindings
- [x] Sampling continuity: no 3 consecutive tasks without automated verification
- [x] Wave 0 has no MISSING references
- [x] No watch-mode flags
- [x] Focused gates are bounded; the inherited full-suite phase gate may exceed 30 seconds
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** plan verification pending
