---
phase: 1
slug: substrate
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib) — no pytest/other framework, per N5's "no dependency beyond bd + Python 3 stdlib" |
| **Config file** | none — `unittest discover` needs no config |
| **Quick run command** | `python3 -m unittest discover -s .gsd/capabilities/beads/tests -p 'test_*.py' -q` |
| **Full suite command** | same as quick run (test surface small enough that quick == full for this phase) |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m unittest discover -s .gsd/capabilities/beads/tests -p 'test_*.py' -q`
- **After every plan wave:** Run same command (full suite == quick run at this phase's scale)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | B1 | — | N-task plan produces N issues under one epic | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestCreateIssues -v` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | B2 | — | Dependency edges match intra-plan order + `depends_on` | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestDependencyMapping -v` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | B3 | — | Wave-batch close touches only completed tasks in the wave | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestCloseWave -v` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | B4 | — | Re-sync resolves by `<beads-id>`, never creates a duplicate on title rename | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestIdentityBinding -v` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | B5 | — | Two syncs over an unchanged plan create/modify nothing | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestIdempotency -v` | ❌ W0 | ⬜ pending |
| 01-01-06 | 01 | 1 | B6 | — | `bd` absent → skip with one notice, no exception | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestFailOpen -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.gsd/capabilities/beads/tests/test_sync.py` — covers B1–B6, using `unittest.mock.patch` on `subprocess.run` so no real `bd` database is touched by unit tests
- [ ] `.gsd/capabilities/beads/tests/fixtures/*.md` — at least one minimal real-schema PLAN.md fixture (XML `<task>` blocks per corrected schema) and one multi-plan wave fixture for B3's batch-close test
- [ ] No framework install needed — `unittest` ships with Python 3 stdlib

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
