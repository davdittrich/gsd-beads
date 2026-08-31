---
phase: "20"
slug: "additive-identity-migration-and-compatibility"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-08-31"
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for additive native identity migration.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` |
| **Config file** | none |
| **Quick run command** | `TMPDIR=/dev/shm python3 -m unittest tests.test_sync.TestIdentityBinding -v` |
| **Full suite command** | `TMPDIR=/dev/shm python3 -m unittest discover -s tests -t tests` |
| **Estimated runtime** | ~30 seconds |

## Sampling Rate

- **After every task commit:** Run the focused Phase 20 test class.
- **After every plan wave:** Run the full capability suite from `plugins/beads-lifecycle/.gsd/capabilities/beads`.
- **Before `$gsd-verify-work`:** The full suite must be green under `/dev/shm`.
- **Max feedback latency:** 60 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | ID-01 | T-20-01 | Canonical `auto`/`tracer` native identity derives only from a safe live Beads id and the second sync is byte-identical. | public-boundary unit | `TMPDIR=/dev/shm python3 -m unittest tests.test_sync.TestIdentityBinding -v` | ✅ | pending |
| 20-01-02 | 01 | 1 | ID-02 | T-20-02 | Checkpoint, missing, and unknown task blocks remain byte-identical; duplicate or conflicting native identity causes no write or create. | public-boundary unit | `TMPDIR=/dev/shm python3 -m unittest tests.test_sync.TestIdentityBinding -v` | ✅ | pending |

## Wave 0 Requirements

- [ ] Existing `tests/test_sync.py` gains focused Phase 20 public-boundary coverage; no new framework or fixture layer.
- [ ] Existing infrastructure covers all requirements.

## Manual-Only Verifications

All phase behaviors have automated verification.

## Validation Sign-Off

- [ ] All tasks have automated verification.
- [ ] Sampling continuity: no 3 consecutive tasks without automated verification.
- [ ] Wave 0 covers all MISSING references.
- [ ] No watch-mode flags.
- [ ] Feedback latency < 60s.
- [ ] `nyquist_compliant: true` set in frontmatter.

**Approval:** pending
