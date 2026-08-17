---
phase: 07
slug: hygiene-publication
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-16
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — no application code, no test framework. "Tests" are the ROADMAP success criteria run as literal shell commands against git/gh state. |
| **Config file** | n/a |
| **Quick run command** | `git ls-files \| grep -E '\.beads/config\.yaml\|\.beads/metadata\.json$\|headroom_wrap_marker\|\.gsd-capabilities\.json'` (expect empty) |
| **Full suite command** | fresh-clone remote verification: `git clone <url> /tmp/verify && cd /tmp/verify && git log -p --all -- <4 target paths>` (expect empty) |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** `git ls-files | grep -E '<4 target paths>'` (expect empty) + `git log -p --all -- <4 paths>` (expect empty)
- **After every plan wave:** n/a — single-wave phase
- **Before `/gsd-verify-work`:** Fresh-clone check (Success Criterion 5) must run once, after push, before declaring the phase done
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | PUB-05 | Information Disclosure | 4 target files untracked, .gitignore extended | smoke | `git ls-files \| grep -E '\.beads/config\.yaml\|\.beads/metadata\.json$\|headroom_wrap_marker\|\.gsd-capabilities\.json'` (expect empty) + `git check-ignore -v .beads.backup-pre-recovery/ .beads/interactions.jsonl foo.bak` (expect all matched) | n/a — direct git commands | ⬜ pending |
| 07-01-02 | 01 | 1 | PUB-05 | Information Disclosure | History fully stripped, not just untracked | smoke | `git log -p --all -- <4 paths>` (expect empty output) | n/a | ⬜ pending |
| 07-01-03 | 01 | 1 | PUB-10 | Tampering | Public repo exists, remote configured, history pushed | smoke | `gh repo view davdittrich/gsd-beads --json visibility,url` + `git remote -v` | n/a | ⬜ pending |
| 07-01-04 | 01 | 1 | PUB-10 (Success Criterion 5) | Information Disclosure | Fresh clone contains no trace | e2e | `git clone <url> /tmp/verify && cd /tmp/verify && git log -p --all -- <4 paths>` (expect empty) | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Force-push confirmation | PUB-10 | Standing git-safety rule requires explicit user confirmation before any force-push affecting shared history | Present the exact `git push --force` command to the user and get explicit approval before running it |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
