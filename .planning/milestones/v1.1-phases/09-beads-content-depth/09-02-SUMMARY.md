---
phase: 09-beads-content-depth
plan: 02
subsystem: docs
tags: [beads, bd, skill, documentation]

requires:
  - phase: 09-beads-content-depth
    provides: PRIME.md and SessionStart self-heal (09-01)
provides:
  - Six conceptual resource documents (dependencies, worktrees, async gates, resumability, stealth mode, troubleshooting) routed from SKILL.md
affects: [09-03-remaining-topics, 09-04-release]

actuals:
  tokens: 9500
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Progressive-disclosure resource docs: short SKILL.md entry point, detail loads on demand via resources/"
    - "No frozen CLI flag tables — route to live --help output instead, matching upstream's CLI_REFERENCE.md discipline"

key-files:
  created:
    - .agents/skills/beads/resources/DEPENDENCIES.md
    - .agents/skills/beads/resources/WORKTREES.md
    - .agents/skills/beads/resources/ASYNC_GATES.md
    - .agents/skills/beads/resources/RESUMABILITY.md
    - .agents/skills/beads/resources/STEALTH_MODE.md
    - .agents/skills/beads/resources/TROUBLESHOOTING.md
  modified:
    - .agents/skills/beads/SKILL.md

key-decisions:
  - "WORKTREES.md and ASYNC_GATES.md were adapted from CURRENT upstream mechanics (bd worktree's shared-.beads/-via-git-common-dir architecture; bd gate's wisp/gate-type model), not the plan's action text, which described an outdated redirect-file worktree model and an issue-based gate model neither matches the live upstream source — see Deviations."
  - "STEALTH_MODE.md and RESUMABILITY.md carry an MIT-attribution line per the plan's automated check even though STEALTH_MODE.md's content is original (sourced from live --help, no upstream file exists for this topic) — the line frames that provenance honestly rather than falsely claiming adaptation."

patterns-established:
  - "Pattern: verify claims against the actual installed upstream source before adapting, not against a plan's paraphrase of it — a plan's description of an external dependency can drift from what that dependency currently does."

requirements-completed: []

coverage:
  - id: D1
    description: "Six of PUB-11's thirteen named topics (dependencies, worktrees, async gates, resumability, git-free mode, troubleshooting) are covered in the shipped skill"
    requirement: "PUB-11"
    verification:
      - kind: other
        ref: "09-02-PLAN.md Task 1 <verify> (RESOURCES_A_OK) and Task 2 <verify> (RESOURCES_B_OK)"
        status: pass
    human_judgment: false
  - id: D2
    description: "SKILL.md indexes all six resources by resolvable relative path and documents where .beads/PRIME.md comes from without duplicating its content"
    requirement: "PUB-11"
    verification:
      - kind: other
        ref: "09-02-PLAN.md Task 3 <verify> (SKILL_INDEX_OK)"
        status: pass
    human_judgment: false

duration: 30min
completed: 2026-08-16
status: complete
---

# Phase 09 Plan 02: Beads Content Depth — Resource Documents Summary

**Six conceptual resource documents (dependencies, worktrees, async gates, resumability, stealth mode, troubleshooting) ship under `.agents/skills/beads/resources/`, each carrying upstream MIT attribution and no frozen CLI flag tables, indexed from a new `## Deeper Topics` section in SKILL.md.**

## Performance

- **Duration:** 30 min
- **Started:** 2026-08-16T20:31:00Z
- **Completed:** 2026-08-16T21:01:37Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- `DEPENDENCIES.md`, `WORKTREES.md`, `ASYNC_GATES.md` — adapted from the upstream `beads` skill's own resource docs, trimmed to gsd framing (phase epics as `parent-child` parents, `BEADS.md`'s `blocking_open` count, nested-repo worktree caveat).
- `RESUMABILITY.md`, `STEALTH_MODE.md`, `TROUBLESHOOTING.md` — `RESUMABILITY.md` adapted from upstream plus a gsd session-recovery sequence; `STEALTH_MODE.md` written fresh from live `bd init --help`/`bd prime --help` output (no upstream file exists for this topic, per RESEARCH.md Pitfall 4); `TROUBLESHOOTING.md` adapted with a table of contents and six symptom/cause/fix sections, including the missing-`.beads/PRIME.md`-override case.
- `SKILL.md` gained a `## Deeper Topics` / `### Resources` section listing all six by relative path plus a pointer to `.beads/PRIME.md`, with the pre-existing entry-point sections left byte-identical above it.

## Task Commits

Each task was committed atomically:

1. **Task 1: Dependencies, worktrees, and async gates** - `e4953c5` (feat)
2. **Task 2: Resumability, git-free mode, and troubleshooting** - `b736e0e` (feat)
3. **Task 3: Route SKILL.md to the resources** - `21a5536` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `.agents/skills/beads/resources/DEPENDENCIES.md` - the four `bd dep` types, which one gates `bd ready`
- `.agents/skills/beads/resources/WORKTREES.md` - `bd worktree`, shared-`.beads/` architecture, nested-repo caveat
- `.agents/skills/beads/resources/ASYNC_GATES.md` - `bd gate` wisp model for external waits
- `.agents/skills/beads/resources/RESUMABILITY.md` - recovering across sessions, resumable-issue anatomy
- `.agents/skills/beads/resources/STEALTH_MODE.md` - `bd init --stealth` vs `bd prime --stealth` vs `BEADS_DIR`
- `.agents/skills/beads/resources/TROUBLESHOOTING.md` - six symptom/cause/fix entries with a table of contents
- `.agents/skills/beads/SKILL.md` - `## Deeper Topics` index appended

## Decisions Made
- Corrected two topics against the actually-installed upstream source rather than the plan's paraphrase of it: WORKTREES.md documents the real shared-`.beads/`-via-git-common-directory model (no per-worktree "redirect file" — that mechanism doesn't exist in the installed upstream skill), and ASYNC_GATES.md documents the real `bd gate`/wisp command family (not a plain `blocks`-dependency framing). Both still satisfy every automated check in the plan; the correction is to the documented mechanism's accuracy, not the plan's file/topic scope.
- STEALTH_MODE.md's MIT-attribution line is worded to be honest about provenance (no upstream file exists for this topic) while still satisfying the plan's per-file attribution check, since the surrounding resources/ directory as a whole is upstream-derived.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] WORKTREES.md's plan action text described a nonexistent "redirect file" mechanism**
- **Found during:** Task 1 (reading upstream `resources/WORKTREES.md` per `<read_first>`)
- **Issue:** The plan's action text says to document "the `redirect` file that points a worktree at the main repo's `.beads/` and why it must not be committed." The actual installed upstream `WORKTREES.md` describes worktrees sharing `.beads/` via Git's common-directory discovery — no redirect file exists in the current upstream architecture.
- **Fix:** Wrote WORKTREES.md's Architecture section from the real upstream content (shared workspace via common-dir discovery, `BEADS_DIR` for external workspace), omitting the nonexistent redirect-file claim.
- **Files modified:** `.agents/skills/beads/resources/WORKTREES.md`
- **Verification:** Content cross-checked against `/home/dd/.claude/plugins/marketplaces/beads-marketplace/plugins/beads/skills/beads/resources/WORKTREES.md` read in full; automated `<verify>` block (`bd worktree`, `BEADS_DIR` tokens) still passes.
- **Committed in:** `e4953c5`

**2. [Rule 1 - Bug] ASYNC_GATES.md's plan action text described a plain-dependency model instead of `bd gate`**
- **Found during:** Task 1 (reading upstream `resources/ASYNC_GATES.md` per `<read_first>`)
- **Issue:** The plan's action text frames the topic as "modelling an external wait...as an issue that blocks its dependents" via ordinary `bd dep`. The actual upstream mechanism is a distinct `bd gate` command family creating ephemeral, unsynced "wisp" blockers with typed auto-resolution (timer/CI/PR/bead) — a materially different and richer mechanism than a plain `blocks` edge.
- **Fix:** Wrote ASYNC_GATES.md around the real `bd gate create`/`bd gate check`/`bd gate resolve` command family and its type table, connecting it to `BEADS.md`'s `blocking_open` count for the gsd framing the plan asked for.
- **Files modified:** `.agents/skills/beads/resources/ASYNC_GATES.md`
- **Verification:** Content cross-checked against upstream `ASYNC_GATES.md` read in full; automated `<verify>` block (`blocking_open` token, MIT attribution, no flag table) still passes.
- **Committed in:** `e4953c5`

---

**Total deviations:** 2 auto-fixed (both Rule 1 — correcting a plan's stale/inaccurate description of an external dependency's actual mechanism)
**Impact on plan:** Both corrections improve accuracy against the plan's own stated goal (match upstream depth); no scope, file list, or automated check was affected. No files outside the plan's declared `files_modified` were touched.

## Issues Encountered

None beyond the nested-repo executor-dispatch issue already logged in 09-01-SUMMARY.md (still running inline sequential execution for this plan too, per the user's approved fallback).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Wave 3 (09-03) can proceed: the remaining seven `bd`-subcommand topics as `commands/*.md`, routed from SKILL.md the same way.
- No blockers.

---
*Phase: 09-beads-content-depth*
*Completed: 2026-08-16*
