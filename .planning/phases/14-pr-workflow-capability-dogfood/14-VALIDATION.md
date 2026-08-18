---
phase: 14
slug: pr-workflow-capability-dogfood
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-18
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (matches `.gsd/capabilities/markdown-linting/tests/test_lint.py`'s established pattern in this repo) |
| **Config file** | none dedicated — reuses whatever root pytest config already collects `.gsd/capabilities/*/tests/` (verify at Wave 0; `markdown-linting`'s `tests/test_lint.py` is the direct precedent to confirm collection against) |
| **Quick run command** | `pytest .gsd/capabilities/pr-workflow/tests/ -x` |
| **Full suite command** | `pytest .gsd/capabilities/pr-workflow/tests/` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest .gsd/capabilities/pr-workflow/tests/ -x`
- **After every plan wave:** Run `pytest .gsd/capabilities/pr-workflow/tests/` (full suite; small, no quick/full split needed)
- **Before `/gsd-verify-work`:** Full suite must be green, plus the live `gsd_run check predicate`
  smoke test (not pytest-automatable against the real evaluator binary — documented manual/scripted
  step, same form as `13-GATE-SMOKE-TEST.md`)
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | PRW-01 | — | Rollup precedence (failing>pending>passing) over synthetic `gh pr checks --json bucket` fixtures, one per state incl. zero-checks | unit | `pytest .gsd/capabilities/pr-workflow/tests/test_pr_status.py::test_rollup_precedence -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | PRW-01 | — | `PR.md` full-overwrite (not append) on re-run | unit | `pytest .gsd/capabilities/pr-workflow/tests/test_pr_status.py::test_regenerate_overwrites -x` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | PRW-02 | T-14-01 | Gate predicate satisfied for `none`/`passing`, unsatisfied for `pending`/`failing` via `gsd_run check predicate` | smoke (live subprocess, mirrors `13-GATE-SMOKE-TEST.md`) | manual/scripted `gsd_run check predicate --predicate '...' --phase-dir <scratch> --raw` per state | ❌ W0 (fixture scratch dirs) | ⬜ pending |
| TBD | TBD | TBD | PRW-03 | — | No-open-PR notice printed exactly once, no PR created, `gh pr list` empty before/after | integration (real `gh pr list` against this repo's actual `main` branch) | `pytest .gsd/capabilities/pr-workflow/tests/test_pr_status.py::test_no_open_pr_notice -x` (skip if no `gh`/auth) | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | PRW-04 | T-14-02 | `gh` absent → one notice, no hang; `gh auth status` failing → one different notice | unit (scratch `PATH` without `gh`; `GH_CONFIG_DIR` pointed at empty dir for auth-failure) | `pytest .gsd/capabilities/pr-workflow/tests/test_pr_status.py::test_gh_absent -x` / `::test_gh_unauthenticated -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Task IDs/plan/wave columns are TBD — filled in by the planner once tasks are assigned; Threat Ref columns reference the plan's `<threat_model>` block IDs.*

---

## Wave 0 Requirements

- [ ] `.gsd/capabilities/pr-workflow/tests/test_pr_status.py` — covers PRW-01/02/04 unit-level rollup/notice logic
- [ ] `.gsd/capabilities/pr-workflow/tests/fixtures/` — synthetic `gh pr checks --json bucket` stdout captures for pass/pending/fail/zero-checks, and a synthetic empty `gh pr list` capture for the no-open-PR case
- [ ] `14-GATE-SMOKE-TEST.md` (doc, not a test file) — live `gsd_run check predicate` smoke run
  across the four `pr_gate_ok` states, same form as `13-GATE-SMOKE-TEST.md`, required to satisfy
  PRW-02's "predicate is observed firing" success criterion literally — a passing pytest suite
  alone does not satisfy it (STATE.md: "a green ship is not evidence the gate works")

---

## Manual-Only Verifications

- PRW-02 Success Criterion 2 (live `gsd_run check predicate` smoke test against synthetic `PR.md`
  files, one per `pr_gate_ok` state) — cannot be pytest-automated against the real compiled
  evaluator binary without shelling out; kept as a documented manual/scripted step
  (`14-GATE-SMOKE-TEST.md`), matching `13-GATE-SMOKE-TEST.md`'s precedent exactly.
- PRW-03/PRW-04's "exactly one visible notice" acceptance criteria require eyeballing transcript
  output during a real execute→ship cycle in addition to the pytest assertions — the pytest tests
  assert the notice text/count programmatically, but the phase's Success Criteria explicitly
  require a live cycle, not just unit coverage.

---

## Notes

Derived from `14-RESEARCH.md`'s `## Validation Architecture` section (Test Framework, Phase
Requirements → Test Map, Sampling Rate, Wave 0 Gaps) — see that document for full sourcing and
the live-verified `gh` CLI behaviors (v2.97.0) this validation plan depends on.
