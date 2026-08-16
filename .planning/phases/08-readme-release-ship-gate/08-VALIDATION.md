---
phase: 08
slug: readme-release-ship-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-16
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — no unit-test suite in this repo. Verification is procedural (CLI transcripts), matching Phase 7's established pattern. |
| **Config file** | n/a |
| **Quick run command** | n/a — see Per-Task Verification Map for the actual per-SC verification commands |
| **Full suite command** | All 5 SC verification commands below, run in sequence |
| **Estimated runtime** | ~2 minutes |

---

## Sampling Rate

- **After every task commit:** re-run the specific SC's verification command for whatever was just changed
- **After every plan wave:** n/a — single-wave phase expected
- **Before `/gsd-verify-work`:** all five SC verification commands must be green

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | PUB-04 (SC2) | Information Disclosure | Release zip contains exactly the allowlist | scripted | `gh release download v1.1.0 --pattern '*.zip' -O out.zip && unzip -l out.zip` | ✅ `gh` installed | ⬜ pending |
| 08-01-02 | 01 | 1 | PUB-04 (SC3) | Information Disclosure | No `.planning/`/`.beads/` file in the release archive | scripted | `unzip -l out.zip \| grep -E '\.planning/\|\.beads/'` (expect empty) | ✅ | ⬜ pending |
| 08-01-03 | 01 | 1 | PUB-07 (SC1) | n/a | README commands are all real, transcribed from execution | manual | Run every README command verbatim, capture output for cross-check | n/a — new file | ⬜ pending |
| 08-01-04 | 01 | 1 | PUB-09 (SC4) | n/a | Marketplace round trip succeeds | scripted | `claude plugin marketplace add davdittrich/gsd-beads && claude plugin install beads@gsd-beads -y && claude plugin uninstall beads -y` | ✅ `claude` installed | ⬜ pending |
| 08-01-05 | 01 | 1 | PUB-09 (SC5) | Elevation of Privilege | `claude plugin validate . --strict` clean at the tagged fresh clone | scripted | `git clone <url> /tmp/verify && git -C /tmp/verify checkout v1.1.0 && claude plugin validate /tmp/verify --strict` | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing tooling (`gh`, `claude`, `git`, `zip`) covers every phase requirement's verification method; no test-framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README command transcription accuracy | PUB-07 | Requires reading the README as a stranger would and executing each command as written | Execute every command shown in README.md exactly as written; confirm it works and matches the doc |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
