---
phase: 09-beads-content-depth
plan: 04
subsystem: infra
tags: [release, plugin, ci, beads]

requires:
  - phase: 09-beads-content-depth
    provides: PRIME.md/hooks (09-01), resource docs (09-02), command docs (09-03)
provides:
  - v1.1.1 as the sole public release, v1.1.0 retired, proven install round trip
affects: []

actuals:
  tokens: 5000
  tasks: 3
  commits: 1

tech-stack:
  added: []
  patterns:
    - "Release provenance check: asset createdAt must fall inside the CI run's [createdAt, updatedAt] window"

key-files:
  created: []
  modified:
    - .claude-plugin/plugin.json

key-decisions:
  - "User approved pushing to origin/main, deleting the public v1.1.0 release+tag, and cutting v1.1.1 before any of it ran (AskUserQuestion checkpoint) — this wave is publicly visible and partly irreversible, outside the plan's own autonomous:true scope."
  - "Task 3's plan assumed a clean marketplace add; this machine already had beads@gsd-beads installed twice (local+user scope, v1.1.0) from a Directory-source marketplace named 'gsd-beads' pointing at this repo. A second AskUserQuestion checkpoint confirmed proceeding with `claude plugin marketplace add davdittrich/gsd-beads`, which silently converts the existing user-scope 'gsd-beads' marketplace declaration from Directory to GitHub source (same name, no collision error) rather than erroring or aliasing — this CLI behavior was not previously documented anywhere in this project and is worth remembering."
  - "Local-scope beads@gsd-beads install was never touched by uninstall/install (both scoped to 'user' only) — restore only needed to re-point the marketplace source back to Directory and reinstall at user scope, which now correctly reflects the dogfooded directory's real v1.1.1 content instead of the pre-phase v1.1.0."

patterns-established: []

requirements-completed: [PUB-11, PUB-12]

coverage:
  - id: D1
    description: "v1.1.0 is retired (release+tag) and v1.1.1 is the sole public release, its asset produced by CI (not a workstation upload)"
    requirement: "PUB-12"
    verification:
      - kind: other
        ref: "gh release list / git ls-remote --tags / provenance timestamp window check (09-04-PLAN.md Task 2 <verify>)"
        status: pass
    human_judgment: false
  - id: D2
    description: "The published v1.1.1 archive's top level is exactly the five allowlisted entries, carrying PRIME.md, the self-heal wrapper, six resources, and eight commands"
    requirement: "PUB-11, PUB-12"
    verification:
      - kind: other
        ref: "downloaded-asset unzip -Z1 listing check (09-04-PLAN.md Task 2 <verify>)"
        status: pass
    human_judgment: false
  - id: D3
    description: "A fresh clone at the v1.1.1 tag validates and carries the full file inventory; a README-driven install of the plugin yields an installed copy whose SessionStart wrapper restores .beads/PRIME.md and whose bd prime prints the gsd override"
    requirement: "PUB-12"
    verification:
      - kind: other
        ref: "Gate A (fresh clone + claude plugin validate . --strict) and Gate B (real marketplace add/install/uninstall round trip against the installed cache copy; 09-04-PLAN.md Task 3 <verify>)"
        status: pass
    human_judgment: false

duration: 42min
completed: 2026-08-16
status: complete
---

# Phase 09 Plan 04: Beads Content Depth — Release Summary

**`v1.1.1` is tagged, released, and verified end-to-end from a real plugin install: the known-short `v1.1.0` is retired, the CI-built archive carries the full 16-file inventory this phase added with an unchanged allowlist, and a `bd prime` run against the *installed* plugin copy (not the working tree) prints the gsd-tailored lifecycle override.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-08-16T20:31:00Z
- **Completed:** 2026-08-16T21:12:25Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments
- `.claude-plugin/plugin.json` bumped `1.1.0` → `1.1.1`; `claude plugin validate . --strict` passed; a local archive rebuild matched the exact `.github/workflows/release.yml` allowlist command and carried all 16 files this phase added with the top-level entry set unchanged (`.agents`, `.claude-plugin`, `LICENSE`, `README.md`, `hooks`).
- Pushed to `origin/main`; deleted `v1.1.0`'s GitHub Release and tag (`gh release delete v1.1.0 --cleanup-tag`); cut and pushed `v1.1.1`; watched the Release workflow run to a successful conclusion.
- Downloaded the published `v1.1.1` asset and independently verified its contents (not just a local build) match the allowlist exactly, and its `createdAt` falls inside the CI run's `[createdAt, updatedAt]` window — proof the asset came from CI, not a workstation upload.
- Gate A: fresh `git clone` at the `v1.1.1` tag validated with `claude plugin validate . --strict` and carried the full 6-resource/8-command/PRIME.md/wrapper inventory.
- Gate B: real `claude plugin marketplace add`/`install`/`uninstall` round trip against this machine's actual plugin cache, proving `bd prime` prints the gsd override from the **installed** copy at `~/.claude/plugins/cache/gsd-beads/beads/1.1.1/`, not from this working tree. Machine state fully restored afterward.

## Task Commits

Each task was committed atomically:

1. **Task 1: Bump to 1.1.1 and prove the working tree ships everything** - `d4e132b` (feat)
2. **Task 2: Retire v1.1.0 and cut v1.1.1** - (no file changes; release operations only — `gh release delete`, `git tag`/`git push --tags`)
3. **Task 3: Install round trip from the README** - (no file changes; install verification only)

**Plan metadata:** (this commit)

## Files Created/Modified
- `.claude-plugin/plugin.json` - version bumped to `1.1.1`

## Decisions Made

- **User checkpoint before any public action.** Before Task 1's push, I stopped and asked the user to confirm pushing 16 commits to `origin/main`, deleting the public `v1.1.0` release/tag, and cutting `v1.1.1` — this wave does real, publicly-visible, partly-irreversible actions outside a normal autonomous plan's blast radius. User confirmed "Proceed."
- **Second checkpoint on an environment conflict the plan didn't anticipate.** Task 3's script assumes a clean `claude plugin marketplace add davdittrich/gsd-beads`. This machine already had `beads@gsd-beads` installed twice (local + user scope, `v1.1.0`) from a **Directory**-source marketplace named `gsd-beads` pointing at this very working repo (the disclosed dogfooding install from earlier phases). Adding a same-named GitHub marketplace risked silently converting that entry. I stopped and confirmed with the user before running the mutating command rather than guessing.
- **Discovered CLI behavior worth recording:** `claude plugin marketplace add <source>` has no rename/alias flag. Adding a source whose derived name (`gsd-beads`) already exists **silently converts the existing marketplace declaration to the new source** (Directory → GitHub here) rather than erroring or aliasing — confirmed by testing, not documented anywhere I could find beforehand.
- **Restore was exact, not approximate.** `claude plugin uninstall`/`install` in this session only ever reported `(scope: user)` — the pre-existing **local**-scope install was never touched by any command I ran, so it needed no restoration. Restoration for the **user**-scope install was: re-add the Directory marketplace source, then reinstall — which now correctly reports `v1.1.1` (the directory's real current content) rather than the pre-phase `v1.1.0`, since the directory itself was legitimately bumped by Task 1 of this very plan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Task 3's install-round-trip script assumed no pre-existing `gsd-beads` marketplace/install state**
- **Found during:** Task 3, before running `claude plugin marketplace add davdittrich/gsd-beads`
- **Issue:** `claude plugin list` showed `beads@gsd-beads` already installed at both `local` and `user` scope (v1.1.0) from a Directory-source marketplace pointing at this repo. The plan's verify script assumes a clean `add`/`install` with no name collision.
- **Fix:** Confirmed with the user before proceeding (checkpoint, not silent). Ran the marketplace add/install/uninstall sequence as planned — it worked without error (silent source-conversion, not a collision error) — then explicitly restored the marketplace source to Directory and reinstalled at user scope afterward, verifying local-scope was never touched and thus needed no restoration.
- **Files modified:** None (machine-local Claude plugin config only, outside this repo).
- **Verification:** Post-restore `claude plugin marketplace list` shows `gsd-beads: Source: Directory (/home/dd/Gemini/gsd-beads)`; `claude plugin list` shows local scope untouched at `1.1.0` and user scope correctly reflecting the directory's actual current version `1.1.1`.
- **Committed in:** N/A (no repo file changes; documented here per deviation protocol).

---

**Total deviations:** 1 auto-fixed (Rule 1 — an environment assumption in the plan's install-round-trip script, resolved via a user checkpoint rather than blind execution)
**Impact on plan:** All of the plan's `<verify>` assertions still passed (PRIME.md restored, content match, `bd prime` prints the override, `bd prime` differs from `--export`); the deviation is entirely about safely handling a pre-existing machine state the plan didn't anticipate, not about the release content itself.

## Issues Encountered

None beyond the two deliberate checkpoints documented above. Both were resolved with explicit user confirmation before any mutating command ran.

## User Setup Required

None - no external service configuration required beyond what already existed (this machine's `gh`/`claude` CLI auth, already in place).

## Next Phase Readiness
- Phase 9 is complete: all 4 success criteria met (SKILL.md coverage, PRIME.md shipped+allowlisted, installed-copy `bd prime` override proven, `v1.1.1` public and `v1.1.0` retired).
- No blockers for the next phase.

---
*Phase: 09-beads-content-depth*
*Completed: 2026-08-16*
