---
phase: 4
slug: adoption
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-15
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib), runnable via `pytest` — confirmed both `import unittest` and a working `pytest` collection/run this session |
| **Config file** | none — no `pytest.ini`/`pyproject.toml`/`conftest.py` under `.gsd/capabilities/beads/tests/` |
| **Quick run command** | `python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q` |
| **Full suite command** | `python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q` (single test file, no quick/full split) |
| **Estimated runtime** | ~3 seconds (66 passed in 3.22s this session, pre-Phase-4 baseline) |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q`
- **After every plan wave:** Run same command (single file, no split)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

*Filled by the planner once PLAN.md tasks exist — RESEARCH.md's Phase Requirements → Test Map
below is the pre-planning source; planner assigns task IDs/plans/waves.*

| Req ID | Behavior | Test Type | Automated Command | File Exists |
|--------|----------|-----------|--------------------|-------------|
| B12 | Parseable todo migrates to a bd issue with mapped priority/label/description; malformed todo left in place; migrated file deleted | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestMigrateTodos -x` | ❌ Wave 0 |
| B12 | Migration report separates "moved" from "could not be interpreted"; separates parse-failure from bd-write-failure reasons | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestMigrateTodosReport -x` | ❌ Wave 0 |
| B13 | On-demand status renders the same table shape as `regenerate-beads-md`, plus two orphan sections | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestOnDemandStatus -x` | ❌ Wave 0 |
| B13 | Task-side orphan (task with no `<beads-id>`) is detected and named | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestOnDemandStatus::test_task_side_orphan -x` | ❌ Wave 0 |
| B14 | `beads.epic_per=milestone` routes epic resolution to a shared milestone epic instead of a per-phase one | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestMilestoneEpic -x` | ❌ Wave 0 |
| B14 | `beads.epic_per` absent/`"phase"` preserves today's exact per-phase behavior (regression guard) | unit | `pytest .gsd/capabilities/beads/tests/test_sync.py::TestMilestoneEpic::test_default_unchanged -x` | ❌ Wave 0 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.gsd/capabilities/beads/tests/fixtures/todo-wellformed.md` — a valid todo matching
      `add-todo.md`'s exact schema (frontmatter block-list `files:`, `## Problem`/`## Solution`
      body) — covers B12
- [ ] `.gsd/capabilities/beads/tests/fixtures/todo-malformed.md` — missing closing `---` or missing
      `severity` key — covers B12/D-04
- [ ] `TestMigrateTodos`, `TestMigrateTodosReport`, `TestOnDemandStatus`, `TestMilestoneEpic` test
      classes in the existing `test_sync.py` (one-file-per-capability pattern — no new test file)
- [ ] No new framework install needed — `pytest`/`unittest` already present and working

---

## Manual-Only Verifications

*All phase behaviors have automated verification per RESEARCH.md's live-verified bd mechanics
(priority scale, label auto-creation, multi-line description round-trip).*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
