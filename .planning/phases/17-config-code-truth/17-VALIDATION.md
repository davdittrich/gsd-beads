---
phase: 17
slug: config-code-truth
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| **Estimated runtime** | ~5 seconds (baseline: `Ran 164 tests in 4.792s / OK`) |

---

## Sampling Rate

- **After every task commit:** Run the full suite — it completes in under 5s, so no quick/full split is warranted
- **After every plan wave:** Run the full suite
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|

*Populated by `/gsd-validate-phase` after plans are finalized. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — `tests/test_sync.py` (4129 lines) is the sole test file and the discovery harness is already in place. No framework install needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|

*Populated by `/gsd-validate-phase`. Target: all phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
