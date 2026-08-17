---
phase: 08-readme-release-ship-gate
plan: 03
subsystem: docs
tags: [readme, gap-closure, beads, gsd-core-lifecycle]

requires:
  - phase: 08-readme-release-ship-gate
    provides: "README.md initial content (Phase 8 plans 01-02), 08-UAT.md gap G-08-1 diagnosis"
provides:
  - "README.md 'What it does' section states the beads-vs-.planning/-markdown value proposition, with the PRD 3.1 comparison table"
  - "README.md 'Example workflow' subsection shows gsd-core's plan/execute/verify lifecycle driving beads state, not just bare bd CLI usage"
affects: [08-ship-gate, release-v1.1.1]

actuals:
  tokens: 732
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - README.md

key-decisions:
  - "Task 2's lifecycle description was written from the shipped skill files (.gsd/capabilities/beads/skills/beads-sync/SKILL.md, beads-status/SKILL.md, capability.json) rather than quoted from a Phase 6 transcript — Phase 6's only SUMMARY.md (06-01-SUMMARY.md) documents the SessionStart-hook and capability-install bridge, not a plan/execute/verify lifecycle run, so D-02's 'quote verbatim if a real transcript exists' branch did not apply."
  - "No release artifact was re-cut in this plan: no git tag, no GitHub Release, no .claude-plugin/plugin.json version bump, no .github/workflows/release.yml change. Both commits touch README.md only. Whether v1.1.0 needs a v1.1.1 re-release to carry this content is a separate decision for the orchestrator to raise with the user, per the plan's scope guard."

requirements-completed: [PUB-07]

coverage:
  - id: D1
    description: "'What it does' section explains WHY bd is used instead of gsd-core's built-in .planning/-markdown task tracking (drift-cost prose + 6-axis comparison table from PRD 3.1/3.2), closing G-08-1's first missing item"
    requirement: PUB-07
    verification:
      - kind: automated
        ref: "Task 1 <verify> script: grep -c over the 'What it does'..'Requirements' slice for all 6 table axis phrasings (>=5 required), Need-column table header, .planning/ token, 'drift' token, and the unchanged ## heading sequence"
        status: pass
    human_judgment: false
  - id: D2
    description: "'Example workflow' subsection shows /gsd-plan-phase, /gsd-execute-phase, /gsd-verify-work and ship:pre tied to the beads state (beads-recall, beads-sync epic+per-task-issue creation, beads-status, BEADS.md, blocking_open/diverged gates) they actually produce/consume, closing G-08-1's second missing item"
    requirement: PUB-07
    verification:
      - kind: automated
        ref: "Task 2 <verify> script: grep over the 'Example workflow'..'Uninstall' slice for all three /gsd-* command names, beads.enabled, BEADS.md, blocking_open, diverged, 'epic', bd ready, AGENTS.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "Scope guard held: only README.md modified, no release artifact (tag/GitHub Release/plugin.json version/release.yml) touched"
    requirement: PUB-07
    verification:
      - kind: automated
        ref: "git diff --name-only HEAD~2 HEAD -> README.md only; claude plugin validate . --strict -> Validation passed"
        status: pass
    human_judgment: false

duration: ~20min
completed: 2026-08-16
status: complete
---

# Phase 08 Plan 03: README Value-Prop and Lifecycle Gap Closure Summary

**Closed gap G-08-1: README.md now states the beads-vs-.planning/-markdown value proposition and shows gsd-core's plan/execute/verify lifecycle actually driving beads state, not just bare `bd` CLI commands.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-08-16T16:35:00Z (approx, per STATE.md)
- **Completed:** 2026-08-16T16:42:11Z
- **Tasks:** 2 completed
- **Files modified:** 1 (`README.md`)

## Accomplishments

- "What it does" section gained a short drift-cost rationale (PRD 3.2 / PROJECT.md Core Value)
  plus a 6-row `Need` / `.planning/ markdown` / `beads` comparison table (PRD 3.1), inserted as a
  `###` subsection between the existing mechanism paragraph and `## Requirements` — no reordering
  of the D-04 locked `##` section sequence.
- "Example workflow" subsection rewritten to open with the real `beads.enabled` config gate, then
  a 4-point walkthrough tying `/gsd-plan-phase` (beads-recall + beads-sync epic/issue creation),
  `/gsd-execute-phase` (beads-status wave pre/post), `/gsd-verify-work` (beads-status refresh), and
  ship (`blocking_open`/`diverged` gates) to the exact mechanism named in
  `.gsd/capabilities/beads/skills/*/SKILL.md` and `capability.json`. The three bare `bd` commands
  and the `AGENTS.md` pointer (D-05) were kept, reframed as the manual escape hatch.
- Verified Phase 6 has no real captured lifecycle transcript to quote verbatim (D-02's alternate
  branch): `06-01-SUMMARY.md` documents the SessionStart-hook/capability-install work only, so the
  lifecycle description was written from the shipped skill files instead, per the plan's own
  fallback instruction.
- Confirmed no release artifact was touched: `git diff --name-only HEAD~2 HEAD` lists `README.md`
  only, and `claude plugin validate . --strict` still passes.

## Task Commits

1. **Task 1: Add the beads-vs-built-in-tracking value proposition to "What it does"** - `83b3897` (docs)
2. **Task 2: Show the gsd-core lifecycle driving beads state in the Example workflow** - `3e0e31f` (docs)

_No plan-metadata commit issued by this executor — STATE.md/ROADMAP.md updates and the final
docs commit are owned by the orchestrator per this plan's execution directive._

## Files Created/Modified

- `README.md` - "What it does" gained the value-prop paragraph + comparison table; "Example
  workflow" rewritten to show the gsd-core lifecycle driving beads state, bare `bd` commands kept
  as the manual escape hatch.

## Decisions Made

- Placed the value-prop content as a `###` subsection (not a new `##` top-level section) inside
  the existing "What it does" section, per D-04's locked section order.
- Wrote Task 2's lifecycle description from the shipped `SKILL.md`/`capability.json` files rather
  than a Phase 6 transcript, since no real end-to-end lifecycle transcript exists in Phase 6's
  output — confirmed by reading `06-01-SUMMARY.md` in full before writing.

## Deviations from Plan

None - plan executed exactly as written. Both `<verify>` automated scripts pass unmodified from
the plan text.

### Out-of-scope observation (not fixed, not committed)

During execution, `git status` showed `CLAUDE.md` (repo root) as modified — the managed
`<!-- BEGIN BEADS INTEGRATION -->` block appears to have been stripped by something outside this
plan's action set. This was **not** caused by any Edit/Write call in this plan (only `README.md`
was touched via the `Edit` tool), was not present in the git status captured at the start of the
session, and is unrelated to G-08-1 / PUB-07. Left untouched and uncommitted, consistent with the
plan's scope guard and this executor's file-scope restriction to `README.md`. Likely related to
the capability-consent-hash-invalidation behavior already on record (a post-consent edit to a
capability bundle file silently deactivates render-hooks output) — worth a follow-up ticket, not
this plan's concern.

## Issues Encountered

None blocking. See the out-of-scope observation above for a noted-but-unfixed pre-existing repo
state change.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- G-08-1's two `missing` items (value-prop comparison, lifecycle-integrated worked example) are
  both closed; `08-UAT.md`'s gap can be re-verified against this README.md.
- No release artifact was re-cut here. The orchestrator should raise with the user whether v1.1.0
  needs a v1.1.1 re-release to carry this README content, and whether that should wait until
  Phase 9 (Beads Content Depth) also lands, per this plan's scope guard.
- The unrelated `CLAUDE.md` drift noted above is flagged for the orchestrator/user, not resolved
  by this plan.

---
*Phase: 08-readme-release-ship-gate*
*Completed: 2026-08-16*

## Self-Check: PASSED

- FOUND: `.planning/phases/08-readme-release-ship-gate/08-03-SUMMARY.md`
- FOUND: `README.md`
- FOUND commit `83b3897` (Task 1)
- FOUND commit `3e0e31f` (Task 2)
