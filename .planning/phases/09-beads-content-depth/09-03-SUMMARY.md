---
phase: 09-beads-content-depth
plan: 03
subsystem: docs
tags: [beads, bd, skill, documentation]

requires:
  - phase: 09-beads-content-depth
    provides: Resource docs + SKILL.md Resources index (09-02)
provides:
  - Eight bd-subcommand reference documents (dep, label, comments, search, compact, import, stats, blocked) routed from SKILL.md
affects: [09-04-release]

actuals:
  tokens: 6500
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Command reference docs: upstream frontmatter shape (description/argument-hint) retained so registering them as slash commands later is a one-line change, without actually registering them now"

key-files:
  created:
    - .agents/skills/beads/commands/dep.md
    - .agents/skills/beads/commands/label.md
    - .agents/skills/beads/commands/comments.md
    - .agents/skills/beads/commands/search.md
    - .agents/skills/beads/commands/compact.md
    - .agents/skills/beads/commands/import.md
    - .agents/skills/beads/commands/stats.md
    - .agents/skills/beads/commands/blocked.md
  modified:
    - .agents/skills/beads/SKILL.md

key-decisions:
  - "Every invocation was confirmed against live bd --help output (bd v1.2.2), not upstream's $1/$2 slash-command template files, which describe a different (registered-command) invocation style than these skill-internal reference docs use."
  - "bd comment (singular) is documented as the actual primary subcommand — a shorthand for bd comments add — since that's what the installed binary exposes; bd stats is documented as an alias of bd status, matching --help's own Aliases: line."

patterns-established: []

requirements-completed: [PUB-11]

coverage:
  - id: D1
    description: "All 13 of PUB-11's named topics (6 resources + 8 commands = the full inventory, dependencies counted once) are covered in the shipped skill"
    requirement: "PUB-11"
    verification:
      - kind: other
        ref: "09-03-PLAN.md Task 1 <verify> (COMMANDS_A_OK) and Task 2 <verify> (COMMANDS_B_OK)"
        status: pass
    human_judgment: false
  - id: D2
    description: "SKILL.md indexes all eight command documents and all six resource documents by resolvable relative path, with the entry point and Resources index from 09-02 left intact"
    requirement: "PUB-11"
    verification:
      - kind: other
        ref: "09-03-PLAN.md Task 3 <verify> (SKILL_COMMANDS_OK)"
        status: pass
    human_judgment: false

duration: 34min
completed: 2026-08-16
status: complete
---

# Phase 09 Plan 03: Beads Content Depth — Command Reference Docs Summary

**Eight `bd`-subcommand reference documents (dep, label, comments, search, compact, import, stats, blocked) ship under `.agents/skills/beads/commands/`, each confirmed against live `bd --help` output and carrying upstream MIT attribution, completing all 13 of PUB-11's named topics.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-08-16T20:31:00Z
- **Completed:** 2026-08-16T21:05:04Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- `dep.md`, `label.md`, `comments.md`, `search.md` — each with upstream-shaped `description`/`argument-hint` frontmatter, an MIT attribution blockquote, and invocations confirmed against `bd dep/label/comment/comments/search --help`; `dep.md` links into `resources/DEPENDENCIES.md` for the ready-queue mechanics.
- `compact.md`, `import.md`, `stats.md`, `blocked.md` — `compact.md` distinguishes `bd compact` (Dolt commit-history squash) from `bd admin compact` (semantic issue summarization); `import.md` documents the upsert/`updated_at`-tiebreak collision behavior; `stats.md` notes `bd stats` is a plain alias of `bd status`; `blocked.md` ties an open blocker to `BEADS.md`'s `blocking_open` and the `ship:pre` gate.
- `SKILL.md` gained a `### Commands` subsection alongside 09-02's `### Resources`, indexing all 8 command docs by relative path — the pre-existing entry point and Resources index are untouched.

## Task Commits

Each task was committed atomically:

1. **Task 1: dep, label, comments, search** - `adc6fd3` (feat)
2. **Task 2: compact, import, stats, blocked** - `e34112c` (feat)
3. **Task 3: Route SKILL.md to the commands** - `9c1a637` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `.agents/skills/beads/commands/dep.md` - `bd dep` reference, links to DEPENDENCIES.md
- `.agents/skills/beads/commands/label.md` - `bd label` reference + gsd phase-label convention
- `.agents/skills/beads/commands/comments.md` - `bd comment`/`bd comments` reference
- `.agents/skills/beads/commands/search.md` - `bd search` reference, when it beats `bd list`
- `.agents/skills/beads/commands/compact.md` - `bd compact` reference, what it does NOT remove
- `.agents/skills/beads/commands/import.md` - `bd import` reference, id-collision/tiebreak behavior
- `.agents/skills/beads/commands/stats.md` - `bd stats`/`bd status` reference, acting on the numbers
- `.agents/skills/beads/commands/blocked.md` - `bd blocked` reference, ship-gate connection
- `.agents/skills/beads/SKILL.md` - `### Commands` index appended

## Decisions Made
- Upstream's `commands/*.md` files use a `$1`/`$2`-positional slash-command template format (for registered Claude commands); this plan's docs use plain prose + fenced-bash invocations instead, matching the plan's explicit instruction and this repo's D-01 constraint that these ship as skill-internal reference material, not registered slash commands (registering them would need a plugin-root `commands/` directory outside the release allowlist).
- Confirmed via live `--help` that `bd blocked`'s only non-global flag is `--parent`, and that `bd stats`/`bd status` are literally the same command (`Aliases: status, stats` in `--help`) — both documented as observed rather than assumed from the upstream filename.

## Deviations from Plan

None - plan executed exactly as written. All invocations shown were confirmed against `bd --help` output for the installed binary before being written, per the plan's precondition and read_first instructions.

## Issues Encountered

None beyond the nested-repo executor-dispatch issue already logged in 09-01-SUMMARY.md (still running inline sequential execution for this plan too).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Wave 4 (09-04) can proceed: bump to v1.1.1, retire v1.1.0, cut and verify the release, prove the README install round trip.
- All 13 of PUB-11's named topics are now covered; D-04's "no curation, no cutting" holds with no topic dropped.
- No blockers.

---
*Phase: 09-beads-content-depth*
*Completed: 2026-08-16*
