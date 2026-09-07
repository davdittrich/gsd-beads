---
phase: 24-remediate-sota-numerics-0-2-0-release-blockers
plan: 02
subsystem: infra
tags: [marketplace, plugin-manifest, cross-repo, publish-gate]

# Dependency graph
requires:
  - phase: 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin
    provides: the plugin.json description on feat/extended-sota-definition that this plan's marketplace edit now matches
provides:
  - marketplace.json's sota-numerics description synced byte-for-byte with the release branch's plugin.json description (D-12)
  - a re-runnable comparison command, pinned in this SUMMARY, for plan 24-08 to re-execute immediately before merging
affects: [24-08]

# Actuals (#2632)
actuals:
  tokens: 244
  tasks: 2
  commits: 2
commits_note:
  Ledger base (gsd-plan-head-before-24-02) recorded retroactively at 69e1639, the
  commit immediately preceding this plan's first edit. git rev-list --count
  69e1639..HEAD at SUMMARY-write time (after both task commits, before the
  plan's own final metadata commit) is 2 -- Task 1's marketplace edit (64b038d)
  and Task 2's SUMMARY commit. The subsequent final_commit (STATE.md/ROADMAP.md/
  REQUIREMENTS.md) is a separate, later commit per the standard executor
  protocol and is not included in this count.

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - .claude-plugin/marketplace.json

key-decisions:
  - "Read the branch manifest description live from the worktree at execution time (not from a transcription in the plan or context file), so the comparison is a real check rather than a copy of a possibly-stale string."
  - "Committed the marketplace edit alone, as the plan and ticket required, so the change is separable from anything else touching this repository this wave."
  - "D-12 requires agreement at the moment merge lands, not the moment this edit lands, because the marketplace entry's source carries no ref -- an installer fetches whatever main holds at install time, not a pinned commit. This SUMMARY pins the exact re-run command and both commit hashes it was checked against so plan 24-08 can re-prove agreement immediately before merging feat/extended-sota-definition into sota-numerics' main, rather than trusting this wave's comparison to still hold."

patterns-established: []

requirements-completed: [D-12]

coverage:
  - id: D1
    description: "The sota-numerics marketplace description in gsd-beads matches the plugin.json description on feat/extended-sota-definition, byte-for-byte."
    requirement: D-12
    verification:
      - kind: unit
        ref: "jq comparison command (Verification section below), run against commit 64b038d (marketplace) vs. worktree HEAD 2321b74 (manifest) -- MATCH"
        status: pass
    human_judgment: false
  - id: D2
    description: "The marketplace source stays a bare repository URL with no ref, so merging to main remains the publish (D-19), and the description edit landed as its own single-file commit."
    requirement: D-12
    verification:
      - kind: unit
        ref: "jq '.plugins[] | select(.name==\"sota-numerics\").source' .claude-plugin/marketplace.json -- {\"source\":\"url\",\"url\":\"https://github.com/davdittrich/sota-numerics.git\"}, unchanged; git show 64b038d --stat -- 1 file changed"
        status: pass
    human_judgment: false
  - id: D3
    description: "The agreement is pinned as a re-runnable check (comparison command plus both commit hashes) for plan 24-08 to re-execute immediately before merging."
    requirement: D-12
    verification:
      - kind: other
        ref: "This SUMMARY's Verification section, below"
        status: pass
    human_judgment: false

duration: <5min
completed: 2026-09-07
status: complete
---

# Phase 24 Plan 02: Sync the marketplace description with the sota-numerics plugin manifest Summary

**Copied the branch manifest's description into `.claude-plugin/marketplace.json` byte-for-byte in a single-line, single-file commit, and pinned the exact comparison command plan 24-08 must re-run at merge time (D-12, D-19).**

## Performance

- **Duration:** <5 min
- **Tasks:** 2/2 complete
- **Files changed:** 1 (`.claude-plugin/marketplace.json`)

## Accomplishments

- Read `description` from `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.claude-plugin/plugin.json` on branch `feat/extended-sota-definition` (worktree HEAD `2321b74`) live, at execution time, rather than trusting a transcription.
- Confirmed the two descriptions had drifted: the marketplace copy was missing a clause Phase 23 added to the manifest (`-- steering toward internal/project consistency, unambiguity, completeness, efficiency, and agent-facing quiet code --`).
- Replaced the `sota-numerics` entry's `description` field in `.claude-plugin/marketplace.json` with the manifest's exact string, changing nothing else (name, `source.source`, `source.url` all byte-identical to before).
- Committed the edit alone (`64b038d`), one file changed, one line touched.
- Pinned the re-runnable comparison (command + both commit hashes) below for plan 24-08.

## Task Commits

1. **Task 1: Replace the marketplace description with the manifest description**
   - `64b038d` (fix) — `.claude-plugin/marketplace.json`: `sota-numerics` description now matches `feat/extended-sota-definition`'s `plugin.json` byte-for-byte.
2. **Task 2: Pin the agreement as a re-runnable check for the publish wave**
   - This file (`24-02-SUMMARY.md`), committed separately, records the comparison below.

## Files Created/Modified

- `.claude-plugin/marketplace.json` — `sota-numerics` entry's `description` field only; `source` object (kind `url`, no `ref`) untouched.
- `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-02-SUMMARY.md` — this file.

## Verification

### Comparison command (re-run this exact command in plan 24-08, immediately before merging)

```bash
cd /home/dd/projects/gsd-beads && \
A=$(jq -r '.plugins[]|select(.name=="sota-numerics").description' .claude-plugin/marketplace.json) && \
B=$(jq -r .description .worktrees/sota-numerics-release-013/.claude-plugin/plugin.json) && \
[ "$A" = "$B" ] && echo MATCH || echo DIFFER
```

### What it was checked against, this wave

| Repository | Commit | Role |
|---|---|---|
| `gsd-beads` (this repo, `main`) | `64b038d` | marketplace entry, after Task 1's edit |
| `sota-numerics` worktree (`.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`) | `2321b74` | plugin manifest, unchanged by this plan |

Result: `MATCH`.

### Source object unchanged

```bash
jq '.plugins[]|select(.name=="sota-numerics").source' .claude-plugin/marketplace.json
```

Returns `{"source":"url","url":"https://github.com/davdittrich/sota-numerics.git"}` — identical to before Task 1's edit. No `ref` key. D-19 (merging `main` is the publish) is unaffected by this plan.

### Why this needs re-checking, not just re-trusting

D-12 requires agreement at the moment merge lands, not the moment this edit lands, because `marketplace.json`'s `source` entry carries no ref: an installer resolves `sota-numerics` against whatever `main` (this repo's default branch) holds at install time, and against whatever commit `feat/extended-sota-definition` has been merged to when it becomes `main` on the `sota-numerics` side. Between this wave (24-02) and the publish wave (24-08), other plans in this phase land more commits on `feat/extended-sota-definition` — none of them touch `plugin.json`'s `description` field per this plan's own context note (`24-02-PLAN.md`: "No plan in this phase modifies that manifest"), but that is a fact to re-verify, not one to assume still holds five waves later. Plan 24-08 must re-run the comparison command above against its own live `HEAD` on both sides immediately before merging, not reuse this wave's `MATCH` result.

## Decisions Made

See `key-decisions` in frontmatter above.

## Deviations from Plan

None — plan executed exactly as written. `<sequential_execution>` (this dispatch's execution mode) directed commits land directly on `main` with no worktree isolation for this plan, consistent with plan 24-01's precedent in this same phase (commits `b07cded`, `3b8d538`, `69e1639`) and this repository's `git.branching_strategy: "none"` config.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `sota-numerics`' marketplace entry and its plugin manifest agree on the branch's current description.
- Plan 24-08 has the exact re-run command and both commit-hash roles it needs to re-prove agreement immediately before merging `feat/extended-sota-definition` to `main` on `sota-numerics`.
- D-12 is closed for this wave; D-19 (merge is the publish, entry points at repository not tag) is unaffected and still holds.

## Self-Check: PASSED

- FOUND: `.claude-plugin/marketplace.json`
- FOUND: `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-02-SUMMARY.md`
- FOUND commit `64b038d` (Task 1, this repo)
- FOUND commit `9cf3453` (Task 2, this repo)
- FOUND commit `2321b74` (worktree HEAD, `.worktrees/sota-numerics-release-013`, unchanged by this plan)

---
*Phase: 24-remediate-sota-numerics-0-2-0-release-blockers*
*Completed: 2026-09-07*
