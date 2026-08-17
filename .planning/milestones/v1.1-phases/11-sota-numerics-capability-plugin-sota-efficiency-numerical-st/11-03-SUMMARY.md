---
phase: 11-sota-numerics-capability-plugin-sota-efficiency-numerical-st
plan: 03
subsystem: infra
tags: [claude-code-plugin, capability-loader, gate, documentation, decision-record]

# Dependency graph
requires:
  - phase: 11-01
    provides: "sota-numerics capability's plan:post command-exit-zero blocking gate spine, check-alternatives.py deterministic validator (including D-08's mechanical placeholder/TODO rejection), dogfood install"
  - phase: 11-02
    provides: "full D-12 four-point advisory fragment spread, all gated on sota-numerics.enabled"
provides:
  - "D-08 resolved on the record via an explicit checkpoint decision (mechanical route), not silently defaulted"
  - "NOTES.md documenting the capability's five deliberate divergences/anti-regression rules, installed byte-identically in both the plugin bundle and the dogfood copy"
affects: []

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 4062
  tasks: 3
  commits: 1

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Checkpoint decision honored inline rather than defaulted (RESEARCH Assumption A2): the coordinator answered Task 1's blocking checkpoint mid-session, execution resumed from that exact point with no redone work"

key-files:
  created:
    - sota-numerics/.gsd/capabilities/sota-numerics/NOTES.md
    - .gsd/capabilities/sota-numerics/NOTES.md
  modified: []

key-decisions:
  - "D-08 resolved mechanical at the Task 1 checkpoint (coordinator's explicit decision): deterministic heuristics already shipped in check-alternatives.py (Plan 01's entry_placeholder_violation — placeholder-host and bare TODO/TBD rejection) stand in for gsd-plan-checker's LLM-mediated citation-plausibility spot-check. No gsd-core patch, no checker-citation-spotcheck.md fragment, no fifth contributions[] entry, no GSD-CORE-PATCH.md. Deferred pending a D-04 dogfood signal: a plan passing the gate on a citation later discovered to be hallucinated."
  - "Task 2 produced zero file changes. The mechanical route's action step only adds artifacts when a concrete gap in check-alternatives.py's heuristics is named at the checkpoint; none was named, so there was nothing to strengthen. Its outcome (route confirmed, nothing to do) is folded into Task 3's NOTES.md commit rather than an empty separate commit."
  - "The §13a-13e plan-phase.md step ordering (Decision Coverage Gate -> STATE.md 'Ready to execute' -> ROADMAP annotate -> commit -> plan:post gate dispatch) was re-verified live against the installed ~/.claude/gsd-core/workflows/plan-phase.md during this plan, not restated from RESEARCH.md's Pitfall 1 record from memory (REVIEWS finding 1). Result: unchanged — the gate still fires after the plan is committed and STATE.md already says ready, so NOTES.md's backstop framing is still accurate, not stale."

requirements-completed: [D-04, D-08]

coverage:
  - id: D1
    description: "D-08's citation-plausibility route is decided at an explicit checkpoint (mechanical) rather than silently defaulted, and NOTES.md records the rationale plus the D-04 dogfood signal that would trigger revisiting it"
    requirement: D-08
    verification:
      - kind: other
        ref: "test ! -e .gsd/capabilities/sota-numerics/GSD-CORE-PATCH.md; jq '.contributions|length' .gsd/capabilities/sota-numerics/capability.json -> 4 (no fifth checker contribution added, manifest untouched from Plan 02)"
        status: pass
    human_judgment: false
  - id: D2
    description: "NOTES.md documents all five topics (onError divergence, late-gate ordering re-verified against the live workflow, script-path/missing-script guard, D-08 route+rationale, at-least-one-in-window recency rule) and is byte-identical in both trees"
    requirement: D-04
    verification:
      - kind: other
        ref: "diff sota-numerics/.gsd/capabilities/sota-numerics/NOTES.md .gsd/capabilities/sota-numerics/NOTES.md -> no differences; grep confirms onError/13e/rev-parse/D-08/--force/'capability install'/planner-sota.md all present"
        status: pass
    human_judgment: false
  - id: D3
    description: "Full plugin test suite passes unchanged after this plan's edits"
    verification:
      - kind: unit
        ref: "python3 -m unittest discover --start-directory sota-numerics/tests --pattern 'test_*.py' -> 19 tests, OK"
        status: pass
      - kind: other
        ref: "bash sota-numerics/tests/test-session-start.sh -> 7/7 PASS, ALL PASS"
        status: pass
    human_judgment: false

duration: ~20min (across the checkpoint pause)
completed: 2026-08-17
status: complete
---

# Phase 11 Plan 03: D-08 Route Decision + Capability NOTES.md Summary

**Closed D-08 via the mechanical route (deterministic heuristics only, LLM-mediated checker layer deferred) at an explicit checkpoint, then wrote the capability's NOTES.md documenting all five deliberate divergences the capability ships with — installed byte-identically in the plugin bundle and the dogfood copy.**

## Performance

- **Duration:** ~20 min (Task 1 checkpoint paused mid-session for the coordinator's decision; Tasks 2-3 ran as a continuation once the decision landed)
- **Started:** 2026-08-17T~11:20Z
- **Completed:** 2026-08-17T11:41:11Z
- **Tasks:** 3 (1 checkpoint decision, 1 no-op confirmation, 1 file-write task)
- **Files modified:** 2 (both created)

## Accomplishments

- **Task 1 (checkpoint:decision, gate="blocking"):** Stopped per standard checkpoint protocol (`workflow.auto_advance` and `workflow._auto_chain_active` both `false` — no auto-approval applies to a `checkpoint:decision`). The coordinator answered mid-session: **mechanical**. Rationale given: ship Phase 11 patch-free with zero core-repo risk, matching RESEARCH's own first-move recommendation, deferring the LLM layer pending a real D-04 false-negative signal.
- **Task 2:** Verified the mechanical route requires zero file changes — Plan 01's `check-alternatives.py` already implements D-08's mechanical half (`entry_placeholder_violation`: placeholder-host and bare TODO/TBD rejection), and no concrete heuristic gap was named at the checkpoint, so nothing to strengthen. Confirmed via the plan's own pairing check: `.gsd/capabilities/sota-numerics/capability.json` still has exactly 4 `contributions[]` entries (0 targeting `into: "checker"`), and no `GSD-CORE-PATCH.md` exists in either tree.
- **Task 3:** Wrote `NOTES.md` (115 lines) covering all five required topics: (1) `gates[0].onError: "halt"` vs. `contributions[].onError: "skip"`, both intentional; (2) the `plan:post` gate's late position relative to commit, **re-verified live against the installed `plan-phase.md`** rather than restated from RESEARCH — unchanged, still §13a→13b→13c→13d→13e in that order; (3) the `git rev-parse --show-toplevel` script-path resolution and the fail-closed `test -f` missing-script guard; (4) the D-08 mechanical route actually taken, its rationale, and the D-04 dogfood signal that would trigger revisiting it; (5) the at-least-one-in-window recency rule with an explicit warning against "tightening" it to reject foundational-citation years. Copied byte-identically to the dogfood location (`diff` clean).
- Full plugin test suite re-run clean after the edits: 19 `unittest` cases pass, 7/7 `test-session-start.sh` cases pass, dogfood parity (`diff -r`) clean.

## Task Commits

Task 1 was a checkpoint (no commit — decision only, recorded in this SUMMARY). Task 2 produced no file changes (no commit). Task 3 is the plan's sole commit:

1. **Task 3: Write NOTES.md documenting the capability's deliberate divergences and anti-regression rules** - `c7a7b45` (docs)

**Plan metadata:** (this commit)

## Files Created/Modified

- `sota-numerics/.gsd/capabilities/sota-numerics/NOTES.md` - capability operator documentation: onError divergence, late-gate ordering (re-verified), script-path resolution + missing-script guard, D-08 route + rationale, at-least-one-in-window recency rule
- `.gsd/capabilities/sota-numerics/NOTES.md` - byte-identical dogfood copy (D-04)

## Decisions Made

- **D-08 route: mechanical** (Task 1 checkpoint, coordinator's explicit choice) — deterministic heuristics stand in for the LLM-mediated checker layer; see `key-decisions` above and `NOTES.md` section 4 for full rationale and the dogfood escalation signal.
- Task 2's mechanical-route action (strengthen `check-alternatives.py` only if a concrete gap was named) resolved to a no-op — no gap was named at the checkpoint, and the deterministic layer already covers D-08's mechanical half from Plan 01. Documented here rather than committed as an empty diff.
- The §13a-13e ordering was re-verified against the live `~/.claude/gsd-core/workflows/plan-phase.md` rather than trusted from RESEARCH.md's record — confirmed unchanged (REVIEWS finding 1's ask satisfied: yes, still accurate).

## Deviations from Plan

None — plan executed exactly as written, including its explicit checkpoint gate. The mechanical route was selected by the coordinator, not defaulted, honoring RESEARCH Assumption A2's requirement that this choice be surfaced rather than silently picked.

## Issues Encountered

- The sandboxed shell's `python3 -m unittest discover -s ... -p 'test_*.py'` shorthand flags (`-s`/`-p`) were mistaken by the environment's inline-interpreter guard for an inline-code-execution flag. Worked around by using the long-form `--start-directory`/`--pattern` flags via a script file instead of the shorthand — same command, no functional difference, matches the plan's own acceptance-criteria note about inline-flag restrictions.

## User Setup Required

None — no external service configuration required. `NOTES.md` is documentation only; no config keys, gates, or contributions changed by this plan.

## Next Phase Readiness

- Phase 11 is now fully complete: Plan 01 (gate spine), Plan 02 (D-12 advisory fragment spread), Plan 03 (D-08 decision + capability documentation). All of D-01 through D-13 are resolved and shipped.
- D-08's mechanical route leaves one explicit, documented follow-up trigger: if this repo's own dogfooded (D-04) future phase planning ever passes the gate on a citation later found hallucinated, escalate to the patch route (RESEARCH Pattern 2(a)) rather than tightening the regex — `NOTES.md` section 4 records this so the decision isn't re-litigated from scratch.
- No blockers.

---
*Phase: 11-sota-numerics-capability-plugin-sota-efficiency-numerical-st*
*Completed: 2026-08-17*

## Self-Check: PASSED

Both NOTES.md files (`sota-numerics/.gsd/capabilities/sota-numerics/NOTES.md`, `.gsd/capabilities/sota-numerics/NOTES.md`) verified present on disk; commit `c7a7b45` verified present in `git log --oneline --all`.
