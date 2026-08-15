---
phase: 02
slug: visibility
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-15
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib) — unchanged from Phase 1, per N5 |
| **Config file** | none |
| **Quick run command** | `python3 -m unittest discover -s .gsd/capabilities/beads/tests -p 'test_*.py' -q` |
| **Full suite command** | same as quick run |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command above
- **After every plan wave:** Run full suite command above
- **Before `/gsd-verify-work`:** Full suite must be green; B8's checkpoint trace must also be
  performed at least once before phase completion (cannot be fully proven by unit tests alone —
  the acceptance criterion is about a composed LLM-agent prompt, not pure code output)
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | B7 | — | tracer: capability.json -> beads-recall skill -> sync.py subcommand -> BEADS-RECALL.md | integration | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestBeadsRecall -v` | ❌ Wave 0 | ⬜ pending |
| 02-01-02 | 01 | 1 | B7 | Tampering (path traversal via cross-phase reverse lookup) | two-technique file-scope matching (`<beads-id>` reverse lookup + `--desc-contains` fallback) + Unscoped fallback (D-02) | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestBeadsRecall -v` | ❌ Wave 0 | ⬜ pending |
| 02-01-03 | 01 | 1 | B7 | — | zero open issues still produces BEADS-RECALL.md with explicit "none found" body (D-04) | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestBeadsRecall.test_no_matches -v` | ❌ Wave 0 | ⬜ pending |
| 02-01-04 | 01 | 1 | B7 | — | static `plan:pre` `contributions[]` entry (`into: "planner"`) points planner at BEADS-RECALL.md | unit (manifest JSON validity) | `python3 -m json.tool .gsd/capabilities/beads/capability.json` | ❌ Wave 0 | ⬜ pending |
| 02-02-01 | 02 | 2 | B11 | Tampering (command injection via issue description echoed into BEADS.md) | BEADS.md frontmatter/table full-overwrite regeneration; hand edit overwritten at next regen | unit + e2e | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestBeadsMdRegeneration -v` | ❌ Wave 0 | ⬜ pending |
| 02-02-02 | 02 | 2 | B8 | — | composed `Agent()` prompt at execute:wave:pre contains wave's issue ids after `beads-status`'s steps-only branch runs | manual/checkpoint trace | manual trace: run real 2-plan wave with `beads.enabled=true`, grep actual `Agent()` prompt text for synced issue ids | ❌ Wave 0 — flag as `checkpoint:human-verify`, not purely automatable | ⬜ pending |
| 02-02-03 | 02 | 2 | B7, B8 | — | `checkpoint:human-verify`: re-install/re-consent + live prompt-inspection trace for both the B7 planner-prompt fragment and B8 executor-prompt wave-status text | manual/checkpoint trace | manual: grep real `/gsd:plan-phase` planner prompt for recall-pointer text; grep real wave dispatch executor prompt for issue ids | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.gsd/capabilities/beads/tests/test_sync.py` — extend with `TestBeadsRecall`,
  `TestBeadsMdRegeneration` classes, reusing Phase 1's `_make_bd_side_effect` mock pattern
- [ ] `.gsd/capabilities/beads/tests/fixtures/` — second phase-directory fixture tree (proves the
  cross-phase `<beads-id>` reverse-lookup technique) and a multi-issue `bd list --json` fixture
  covering both `parent-child` and `blocks` dependency types (D-08's blocked-by column)
- [ ] No framework install needed — `unittest` ships with Python 3 stdlib

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Composed `Agent()` prompt at execute:wave:pre contains the wave's issue ids | B8 | Acceptance criterion is about prompt composition by an LLM orchestrator following SKILL.md prose, not pure code output — cannot be unit-tested | Run a real 2-plan wave with `beads.enabled=true` and a real `.beads` db; grep the actual `Agent()` prompt text for the synced issue ids |
| Composed planner prompt at plan:pre includes the BEADS-RECALL.md pointer fragment | B7 | Same class of gap as B8 — `contributions[]` manifest correctness is unit-testable, but whether the fragment text actually lands in a real planner subagent's prompt is not | Dispatch (or trace) a real planner subagent invocation and grep its composed prompt for the recall-pointer fragment text |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
