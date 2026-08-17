---
phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
plan: 04
subsystem: infra
tags: [github-plugin-removal, ci-workflow-repair, release-workflow-repair, marketplace-round-trip]

# Dependency graph
requires:
  - phase: 12-01
    provides: davdittrich/ponytail-everywhere, public, verified from fresh clone
  - phase: 12-02
    provides: davdittrich/sota-numerics, public, verified from fresh clone
  - phase: 12-03
    provides: gsd-beads/.claude-plugin/marketplace.json repointed to both standalone repos via github source objects (commit cb4d49d, unpushed)
provides:
  - gsd-beads with neither ponytail-everywhere/ nor sota-numerics/ tracked (D-04)
  - gsd-beads' CI green on the removal commit (ci.yml/release.yml repaired in the same commit)
  - both plugins proven to install and uninstall from the real, pushed davdittrich/gsd-beads marketplace (D-10 final form)
affects: []

# Actuals (#2632)
actuals:
  tokens: 23482
  tasks: 2
  commits: 1

# Tech tracking
tech-stack:
  added: []
  patterns: ["single-commit removal-plus-repair: delete a tracked path and fix every workflow/comment reference to it in the SAME commit, so no intermediate commit in history has a red build"]

key-files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - .github/workflows/release.yml
    - hooks/capability-auto-install.sh

key-decisions:
  - "D-08 correction (recorded per plan instruction): CONTEXT.md asserted release.yml 'needs no change'. False against the file as it existed — three of its nine zip arguments (ponytail-everywhere/.claude-plugin, ponytail-everywhere/hooks, ponytail-everywhere/.gsd) named the removed tree. Deleted those three; the six remaining arguments (.claude-plugin, hooks, .agents/skills, .gsd, README.md, LICENSE) are unchanged. D-08's intent (release archive keeps carrying only beads-lifecycle content, no new step) is exactly what the correction achieves."
  - "Untracked sota-numerics/tests/__pycache__/*.pyc residue survived git rm -r sota-numerics (git rm only removes tracked paths); removed it explicitly with rm -rf so the 'directory does not exist on disk' verify held. Rule 3 auto-fix, no file tracked/committed."
  - "Task 2's precondition text ('git log origin/main..HEAD shows exactly the two unpushed commits from Plans 03 and 04') was inaccurate: origin/main had not been pushed since phase 09 (commit 69acbc3, 2026-08-16 23:57), so 95 commits (all of phases 10, 10.1, 11, 11.1, and 12-01..04) were locally unpushed, not 2. Verified origin/main was a strict ancestor of local HEAD (fast-forward, no divergence) before pushing — this is accumulated backlog, not a rewrite or conflict. Proceeded per the plan's pre-approval to push."

patterns-established:
  - "git rm -r on a plugin tree does not remove untracked build artifacts (__pycache__, etc.) left inside it; follow with rm -rf on the path to satisfy a 'directory does not exist' verification."

requirements-completed: [D-04, D-06, D-08, D-10]

coverage:
  - id: D1
    description: "Neither ponytail-everywhere/ nor sota-numerics/ is tracked in gsd-beads or present on disk; the repo-root .gsd/capabilities/ponytail/ and .gsd/capabilities/sota-numerics/ dogfood bundles remain tracked and byte-unchanged"
    requirement: "D-04"
    verification:
      - kind: integration
        ref: "git ls-files ponytail-everywhere sota-numerics -> 0 files; test ! -e ponytail-everywhere && test ! -e sota-numerics -> both gone; git ls-files .gsd/capabilities/ponytail .gsd/capabilities/sota-numerics -> 12 files; git diff HEAD~1 -- .gsd/ -> empty"
        status: pass
    human_judgment: false
  - id: D2
    description: "gsd-beads' CI is green on the commit that performs the removal — no workflow step references a path that no longer exists"
    requirement: "D-10 (verification clause)"
    verification:
      - kind: integration
        ref: "bash tests/test-capability-auto-install.sh -> ALL PASS locally before commit; gh run list --branch main --limit 1 -> conclusion success for headSha 52b53d28b83cf1813c9b672f5ed855f51ae27bdb"
        status: pass
    human_judgment: false
  - id: D3
    description: "Both new plugins install and uninstall through the real, pushed davdittrich/gsd-beads marketplace via the plugin@gsd-beads form; beads-lifecycle@gsd-beads keeps working unchanged"
    requirement: "D-10"
    verification:
      - kind: integration
        ref: "claude plugin install ponytail-everywhere@gsd-beads -y / sota-numerics@gsd-beads -y -> both succeeded and appeared in claude plugin list; uninstall for both -> both gone from claude plugin list; beads-lifecycle@gsd-beads still enabled afterward"
        status: pass
    human_judgment: false
  - id: D4
    description: "v1.2.0 tag untouched, no new gsd-beads tag or release created"
    requirement: "D-06"
    verification:
      - kind: integration
        ref: "git tag --list 'v*' -> v1.0, v1.1.1, v1.2.0 (unchanged); gh release list --limit 5 -> only pre-existing v1.2.0 and v1.1.1 releases, nothing new"
        status: pass
    human_judgment: false
  - id: D5
    description: "The rendered READMEs of both new public repos let a stranger tell what each plugin does, install it, and uninstall it (D-09's stated bar)"
    verification: []
    human_judgment: true
    rationale: "Visual/comprehension judgment of a rendered GitHub README page cannot be scripted; this is the plan's own <human-check> item, deferred to the user opening https://github.com/davdittrich/ponytail-everywhere and https://github.com/davdittrich/sota-numerics."

duration: ~12min
completed: 2026-08-17
status: complete
---

# Phase 12 Plan 04: Remove Vendored Plugin Copies and Push Summary

**Removed the two vendored plugin trees from `gsd-beads`, repaired both GitHub workflows and two hook comments in the same commit, pushed 95 accumulated local commits (fast-forward) to `origin/main`, and proved both plugins install and uninstall from the real, live `davdittrich/gsd-beads` marketplace while `beads-lifecycle` kept working unchanged.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-08-17T16:29:00Z (approx)
- **Completed:** 2026-08-17T16:41:19Z
- **Tasks:** 2/2
- **Files modified:** 3 (`.github/workflows/ci.yml`, `.github/workflows/release.yml`, `hooks/capability-auto-install.sh`), plus 33 files deleted (11 `ponytail-everywhere/`, 22 `sota-numerics/`)

## Accomplishments

- Task 1: `git rm -r ponytail-everywhere sota-numerics` (33 tracked files removed); repaired `ci.yml` (dropped the vendored-copy parity step and the `ponytail-everywhere` session-start smoke test, kept the checkout action and the capability auto-install smoke test); repaired `release.yml` (dropped the three archive path arguments pointing into the removed tree, kept the other six including the bare `.gsd` glob); re-anchored two comments in `hooks/capability-auto-install.sh` to name the standalone repo instead of the removed subdirectory, with zero executable-line changes. Ran `bash tests/test-capability-auto-install.sh` locally (ALL PASS) before committing everything as one commit, `52b53d2`.
- Task 2: pushed `52b53d2` to `origin main` (plain push, fast-forward, no `--force`); `claude plugin marketplace update gsd-beads` refreshed the registered marketplace; ran the full install-confirm-uninstall-confirm round trip for both `ponytail-everywhere@gsd-beads` and `sota-numerics@gsd-beads` against the real, pushed manifest; confirmed `beads-lifecycle@gsd-beads` still installed and enabled throughout; confirmed `gh run list` reports `success` for the pushed head commit; confirmed `v1.2.0` untouched and no new tag/release created.

## Task Commits

1. **Task 1: Remove both subdirectories and repair every reference the removal orphans** - `52b53d2` (feat)
2. **Task 2: Push gsd-beads and prove the finished topology from the real marketplace** - no file changes; the task pushed the existing commit and ran verification only. No new commit.

**Plan metadata:** (this commit) `docs(12-04): complete remove-vendored-plugin-copies-and-push plan`

## Files Created/Modified

- `.github/workflows/ci.yml` - dropped the vendored-copy parity step and the ponytail-everywhere session-start smoke test; kept checkout + capability auto-install smoke test (now the sole named step)
- `.github/workflows/release.yml` - dropped the three archive path arguments naming the removed `ponytail-everywhere/` tree; six arguments remain (`.claude-plugin`, `hooks`, `.agents/skills`, `.gsd`, `README.md`, `LICENSE`)
- `hooks/capability-auto-install.sh` - two comments re-anchored to name `davdittrich/ponytail-everywhere` instead of the removed `ponytail-everywhere/` subdirectory path; no executable line touched
- `ponytail-everywhere/` (11 files) and `sota-numerics/` (22 files) - removed entirely from tracking and disk

## Decisions Made

- D-08 correction: CONTEXT.md's premise that `release.yml` "needs no change" was factually wrong; three of its nine archive arguments named the removed tree. Fixed by deleting exactly those three, preserving D-08's intent (release archive still carries only beads-lifecycle content, no new step, no release for either new plugin per D-07).
- Task 2's precondition text undercounted the unpushed backlog (expected 2 commits, actual 95 — origin/main hadn't been pushed since phase 09). Verified fast-forward (origin/main was a strict ancestor of local HEAD) before pushing; this is accumulated history catching up, not a scope change to this plan's action (`git push origin main`, no force).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Untracked `__pycache__` residue left `sota-numerics/` on disk after `git rm -r`**
- **Found during:** Task 1, post-removal verification (`test ! -e sota-numerics`)
- **Issue:** `git rm -r sota-numerics` removes only tracked paths; `sota-numerics/tests/__pycache__/test_check_alternatives.cpython-314.pyc` (an untracked build artifact from a prior `pytest`/`python3` run) and its containing directories survived on disk, so the directory still existed even though it was empty of tracked content.
- **Fix:** `rm -rf sota-numerics` after the `git rm`, before committing. No tracked file was affected — the `.pyc` was never in the index.
- **Files modified:** none (untracked artifact only)
- **Commit:** N/A (nothing to commit; the artifact was never tracked)

**2. [Rule 1/documentation] Task 2 precondition text inaccurate re: unpushed commit count**
- **Found during:** Task 2, before running `git push`
- **Issue:** The plan's Task 2 precondition asserted `git log origin/main..HEAD` would show exactly 2 commits (Plans 03 and 04). Actual count was 95 — `origin/main` had not been pushed since phase 09 (2026-08-16, commit `69acbc3`), so all of phases 10, 10.1, 11, 11.1, and 12-01 through 12-04 were locally unpushed.
- **Fix:** Verified `origin/main` was a strict ancestor of local `HEAD` (`git merge-base --is-ancestor origin/main HEAD` -> true) before pushing, confirming a clean fast-forward with no divergence or history rewrite. Proceeded with the plain `git push origin main` the plan specified; the operation and its risk profile are unchanged by the larger backlog, only the count.
- **Files modified:** none
- **Commit:** N/A (documentation-only correction, no code change)

Beyond these two, both tasks executed exactly as written.

## Issues Encountered

None blocking. Both deviations above were resolved without user input per Rules 1/3 (auto-fix blocking issue / bug-adjacent documentation correction).

## User Setup Required

None.

## Human Verification Still Outstanding

Per the plan's `<human-check>`: open `https://github.com/davdittrich/ponytail-everywhere` and `https://github.com/davdittrich/sota-numerics` and confirm, from the rendered README alone, that a stranger could tell what each plugin does, install it, and uninstall it; then confirm the `davdittrich/gsd-beads` repository page no longer lists either plugin as a subdirectory. Not performed by this executor (visual/comprehension judgment, D5 above).

## Command Output Captures

**Pushed head SHA:** `52b53d28b83cf1813c9b672f5ed855f51ae27bdb`

**`gh run list --branch main --limit 1`:**
```json
[{"conclusion":"success","headSha":"52b53d28b83cf1813c9b672f5ed855f51ae27bdb","status":"completed"}]
```

**Install/uninstall round trip (`ponytail-everywhere@gsd-beads`):**
```
Installing plugin "ponytail-everywhere@gsd-beads"...✔ Successfully installed plugin: ponytail-everywhere@gsd-beads (scope: user)
✔ Successfully uninstalled plugin: ponytail-everywhere (scope: user)
```
(Note: an earlier `install` call in this same task first reported "already installed" — a pre-existing `ponytail-everywhere@gsd-beads` install from before this plan, per 12-03-SUMMARY.md. That stale install was uninstalled, then a fresh install/uninstall cycle was run against the now-pushed github-source marketplace entry, which is the sequence captured above and is what proves D-10's final form.)

**Install/uninstall round trip (`sota-numerics@gsd-beads`):**
```
Installing plugin "sota-numerics@gsd-beads"...✔ Successfully installed plugin: sota-numerics@gsd-beads (scope: user)
✔ Successfully uninstalled plugin: sota-numerics (scope: user)
```

**`beads-lifecycle@gsd-beads` after both round trips:**
```
❯ beads-lifecycle@gsd-beads
    Version: 1.2.0
    Scope: user
    Status: ✔ enabled
```

**Tag/release state:**
```
git tag --list 'v*'  -> v1.0, v1.1.1, v1.2.0 (unchanged)
gh release list --limit 5 -> v1.2.0, v1.1.1 (no new release)
```

## Next Phase Readiness

- `gsd-beads` now hosts only the marketplace and its own `beads-lifecycle` plugin plus root-level `.gsd/capabilities/` dogfood bundles; `ponytail-everywhere` and `sota-numerics` ship exclusively from their own repos.
- D-04, D-06, D-08 (corrected), and D-10 (final form) all satisfied. This closes Phase 12.
- Outstanding: the human README-comprehension check (D-09 bar) noted above — not blocking, deferred to the user.

---
*Phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly*
*Completed: 2026-08-17*

## Self-Check: PASSED

- FOUND: `.github/workflows/ci.yml` (repaired, one named step)
- FOUND: `.github/workflows/release.yml` (repaired, six archive arguments)
- FOUND: `hooks/capability-auto-install.sh` (comments re-anchored)
- MISSING (expected — removed by design): `ponytail-everywhere/`, `sota-numerics/`
- FOUND: `.gsd/capabilities/ponytail/`, `.gsd/capabilities/sota-numerics/` (untouched)
- FOUND: commit `52b53d28b83cf1813c9b672f5ed855f51ae27bdb` in `gsd-beads` git history, present on `origin/main`
