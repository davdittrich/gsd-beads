---
phase: 07-hygiene-publication
plan: 01
subsystem: infra
tags: [git, git-filter-repo, gitignore, history-rewrite]

requires:
  - phase: 06-runtime-integration
    provides: hooks/hooks.json SessionStart bridge, PUB-03/PUB-06 shipped
provides:
  - Every commit in local history stripped of .beads/config.yaml, .beads/metadata.json,
    .claude/.headroom_wrap_marker.json, .gsd-capabilities.json
  - Root .gitignore extended so those + sibling local-only artifacts cannot re-enter tracking
  - A bare mirror backup of pre-rewrite history at /home/dd/Gemini/gsd-beads-backup-pre-filter-repo
affects: [07-hygiene-publication plan 02 (publication/push)]

actuals:
  tokens: 4800
  tasks: 3
  commits: 1

tech-stack:
  added: []
  patterns:
    - "Mirror-backup-then-rehearse-on-throwaway-clone before any in-place git filter-repo run"
    - "Negative control (probe must be non-empty pre-rewrite) proves verification probes can actually fail"

key-files:
  created: []
  modified:
    - .gitignore
    - .planning/STATE-ARCHIVE.md
    - .planning/config.json

key-decisions:
  - "RESEARCH.md's .beads/hooks/*.backup count (11) was stale; actual tracked count is 5. Used the correct 5 as the collateral-integrity invariant for both Task 1 and Task 3 checks instead of the plan's literal acceptance-criteria number."

patterns-established:
  - "git clone --mirror to a sibling path outside the project root as the sole undo path before an irreversible git filter-repo run, verified readable via rev-list --count --all before proceeding"

requirements-completed: [PUB-05]

coverage:
  - id: D1
    description: "Root .gitignore extended with 5 new patterns (backup/interaction-log artifacts, per-machine tool state) without shadowing tracked .beads/hooks/*.backup files or the .gsd/capabilities/beads/ subtree"
    requirement: "PUB-05"
    verification:
      - kind: other
        ref: "git check-ignore -v .beads.backup-pre-recovery/ .beads/interactions.jsonl foo.bak .serena/ .gsd/dispatch-isolation-sentinel.json (all 5 matched by root .gitignore); git ls-files .gsd/capabilities/beads/ | wc -l == 17; git ls-files .beads/hooks/ | grep -c '\\.backup$' == 5"
        status: pass
    human_judgment: false
  - id: D2
    description: "git filter-repo rehearsed end-to-end on a throwaway clone of the mirror backup, with a negative control proving the verification probes detect the target files before they are trusted to prove absence"
    requirement: "PUB-05"
    verification:
      - kind: other
        ref: "Pre-rewrite probes non-empty (357 lines / 3 matched paths); post-rewrite probes empty; rev-list 173 -> 170 (3 pruned empty commits, matches RESEARCH Pitfall 2)"
        status: pass
    human_judgment: false
  - id: D3
    description: "git filter-repo run in place on the real repo strips all 4 target files from every commit's tree; local verification probes both empty; collateral files (.gsd/capabilities/beads/ 17 files, .beads/hooks/*.backup 5 files, v1.0 tag) intact; mirror backup preserved untouched"
    requirement: "PUB-05"
    verification:
      - kind: other
        ref: "git log -p --all -- <4 paths> == 0 bytes; git ls-files | grep -E '<4 patterns>' == no match (exit 1); rev-list 173 -> 170 (matches rehearsal); backup rev-list still 173"
        status: pass
    human_judgment: false

duration: ~15min
completed: 2026-08-16
status: complete
---

# Phase 7 Plan 1: Git History Hygiene Summary

**Stripped 4 machine-local files (`.beads/config.yaml`, `.beads/metadata.json`, `.claude/.headroom_wrap_marker.json`, `.gsd-capabilities.json`) from every commit via `git filter-repo`, rehearsed first on a throwaway clone with a negative-control probe, backed up pre-rewrite history to a sibling bare mirror, and extended the root `.gitignore` against recurrence.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-08-16T14:35:51Z
- **Tasks:** 3
- **Files modified:** 7 tracked (Task 1 commit) + entire object DB rewritten in place (Task 3)

## Accomplishments
- Extended root `.gitignore` with two new groups (backup/interaction-log artifacts; per-machine tool state) without widening `*.bak` into `*.backup` (would have shadowed tracked `.beads/hooks/*.backup` files) or ignoring the `.gsd/` directory wholesale (would have untracked the 17-file `.gsd/capabilities/beads/` subtree PUB-03 depends on)
- Took a verified bare mirror backup of pre-rewrite history at `/home/dd/Gemini/gsd-beads-backup-pre-filter-repo` (173 commits, matches real repo) — the sole undo path for the in-place rewrite
- Rehearsed the exact `git filter-repo --invert-paths` invocation end-to-end on a throwaway clone of that backup, including a negative control proving the verification probes actually detect the target files before trusting them to prove absence
- Ran the real filter-repo pass in place: every commit's tree in the local repo is now free of all 4 target files; both ROADMAP verification probes (SC-1, SC-3) are empty; the `.gitignore` extension (SC-2) is confirmed matching

## Task Commits

1. **Task 1: Resolve the working tree into one clean pre-rewrite commit** - `e54dd5f` (chore) — subsequently rewritten to `b44d518` by Task 3's filter-repo pass (same content, new hash, expected)
2. **Task 2: Mirror backup + full strip-and-verify rehearsal on a throwaway clone** - no commit (produces only external artifacts: the mirror backup at a sibling path and a disposable `/tmp` rehearsal clone, neither tracked by the repo; also dropped one stray stash entry)
3. **Task 3: Run filter-repo in place on the real repo and verify locally** - no new commit; `git filter-repo` rewrites the object DB and commit hashes in place rather than adding a commit. Real repo HEAD moved from `e54dd5f` (pre-rewrite) to `b44d518` (post-rewrite, same tree content minus the 4 stripped files across all history)

**Plan metadata:** committed as part of this SUMMARY per sequential-executor instructions (STATE.md/ROADMAP.md left untouched, orchestrator-owned)

## Files Created/Modified
- `.gitignore` - extended with `.beads.backup-pre-recovery/`, `.beads/interactions.jsonl`, `*.bak`, `.serena/`, `.gsd/dispatch-isolation-sentinel.json` under two new grouped headers
- `.planning/phases/06-runtime-integration/06-PATTERNS.md` - newly tracked (was untracked since Phase 6, D-02)
- `.planning/phases/07-hygiene-publication/07-PATTERNS.md` - newly tracked
- `.planning/research/.cache/255dcad363ccf0b782ea7c97a6975466963460aed6ac2b1019bcc2ecc49869fb.json` - newly tracked, consistent with 8 sibling cache files already tracked
- `.planning/STATE-ARCHIVE.md`, `.planning/config.json` - carried-forward modifications from planning, committed alongside the gitignore change
- `.claude/.headroom_wrap_marker.json` - deleted (cosmetic; Task 3's rewrite removes it from every commit's tree regardless)
- `/home/dd/Gemini/gsd-beads-backup-pre-filter-repo` - NEW, bare mirror clone outside project root, untracked by design (Plan 02's undo path)
- Entire local git object database - rewritten in place by `git filter-repo`; all 173 pre-rewrite commits recreated as 170 post-rewrite commits (3 empty-after-strip commits pruned: the 3 that touched only target files)

## Decisions Made
- RESEARCH.md's stated `.beads/hooks/*.backup` count (11) does not match the actual tracked count (5) — verified via `git log --diff-filter=D --all` showing zero prior deletions under that path, so this is a stale figure in the planning document, not a regression caused by this plan. Used the correct value (5) as the collateral-integrity invariant in both Task 1 and Task 3 verification instead of the plan's literal acceptance-criteria text. The `*.bak` gitignore pattern (distinct extension from `*.backup`) never touches these files regardless of count, so P-01 is unaffected either way.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected stale `.beads/hooks/*.backup` count in verification (11 → 5)**
- **Found during:** Task 1 verification
- **Issue:** Plan's acceptance criteria and automated `<verify>` blocks (Tasks 1 and 3) assert `git ls-files .beads/hooks/ | grep -c '\.backup$'` equals `11`. Actual repository state is `5`. `git log --diff-filter=D --all -- '.beads/hooks/*.backup'` returns no history of deletions, confirming this is a stale figure from RESEARCH.md's inventory, not data loss caused during execution.
- **Fix:** Verified the invariant that matters (the `*.bak` pattern added to `.gitignore` does not shadow any `.backup` file, and the count is unchanged before and after the filter-repo rewrite: 5 before Task 3, 5 after) rather than enforcing the plan's literal (incorrect) number.
- **Files modified:** None (verification-only correction; no code or config change)
- **Verification:** `git ls-files .beads/hooks/ | grep -c '\.backup$'` = 5 both pre- and post-filter-repo; all 5 `.backup` filenames enumerated and confirmed untouched
- **Committed in:** N/A (verification step, not a file change)

---

**Total deviations:** 1 auto-fixed (1 documentation/verification correction)
**Impact on plan:** No scope creep, no change to the actual actions taken (gitignore content and filter-repo invocation ran exactly as specified). Only the numeric expectation in an automated check was corrected against ground truth.

## Issues Encountered
None beyond the documented deviation above.

## User Setup Required
None - no external service configuration required.

## Verification Record (for Plan 02's checkpoint)

- **Mirror backup absolute path:** `/home/dd/Gemini/gsd-beads-backup-pre-filter-repo`
- **Rehearsal (Task 2, throwaway clone of the backup):**
  - Pre-rewrite negative control: `git log -p --all -- <4 paths>` = 357 lines (non-empty); `git ls-files | grep -E <pattern>` = 3 matched paths (non-empty)
  - Post-rewrite: both probes empty
  - `git rev-list --count --all`: 173 → 170
- **Real run (Task 3):**
  - `git log -p --all -- <4 paths>` = 0 bytes
  - `git ls-files | grep -E <pattern>` = no match (exit 1)
  - `git rev-list --count --all`: 173 → 170 (matches rehearsal)
  - Collateral intact: `.gsd/capabilities/beads/` = 17 files, `.beads/hooks/*.backup` = 5 files, `v1.0` tag present
  - Mirror backup untouched: `git -C /home/dd/Gemini/gsd-beads-backup-pre-filter-repo rev-list --count --all` = 173
- **Stash:** dropped (`stash@{0}: WIP on main: 516581f`, content was a discardable `.gsd-capabilities.json` timestamp bump, preserved in the mirror backup)
- **No remote configured** — confirmed both before and after filter-repo; Plan 02 adds `origin` fresh

## Next Phase Readiness
- Plan 02 (publication) can proceed: local history is clean, the undo path (mirror backup) is verified and preserved, and the root `.gitignore` prevents the 4 targets (and siblings) from re-entering tracking.
- No blockers.

---
*Phase: 07-hygiene-publication*
*Completed: 2026-08-16*
