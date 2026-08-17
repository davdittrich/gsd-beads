---
phase: 10
slug: ponytail-everywhere-capability-plugin-advisory-only-ladder-d
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-17
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — this repo has no unit-test framework for capability/plugin manifests; validation is CLI-driven smoke testing, the same posture `beads`'s own Phase 5/8 plans used (`claude plugin validate . --strict`, `/plugin marketplace add`/`install`/`uninstall` round trips). |
| **Config file** | none |
| **Quick run command** | `node gsd-core/bin/gsd-tools.cjs loop render-hooks plan:pre --raw` (checks the one functional contribution appears in `activeHooks`) |
| **Full suite command** | `claude plugin validate . --strict` + a real `/plugin marketplace add` → `/plugin install ponytail-everywhere@gsd-beads` → `/plugin uninstall` round trip (same shape as PUB-09) |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `node gsd-core/bin/gsd-tools.cjs loop render-hooks plan:pre --raw`
- **After every plan wave:** Run `claude plugin validate . --strict`
- **Before `/gsd-verify-work`:** Full `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | D-01/D-02 | T-10-01 | `ponytail.level` validated against `lite\|full\|ultra` enum before shell interpolation | smoke | `claude plugin validate . --strict` | ✅ existing gate, reused | ⬜ pending |
| 10-01-02 | 01 | 1 | D-04/D-05 | — | `plan:pre` contribution fires only when `ponytail.enabled` true | smoke | `node gsd-core/bin/gsd-tools.cjs loop render-hooks plan:pre --raw` | ✅ CLI already exists | ⬜ pending |

---

## Wave 0 Requirements

- Existing infrastructure (`claude plugin validate`, `gsd-tools loop render-hooks`) covers all phase requirements — no new test framework needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SessionStart reaches orchestrator | D-01 | No automated harness for hook stdout injection exists in this repo | Inspect session transcript after `/plugin install` + a fresh session |
| SubagentStart reaches a real gsd subagent | D-01 | Same gap — no harness asserts hook-injected `additionalContext` reached a subagent transcript | Run any `/gsd-execute-phase` and inspect the spawned executor's/planner's own transcript |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
