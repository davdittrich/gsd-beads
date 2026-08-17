---
phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
plan: 02
subsystem: infra
tags: [github, gh-cli, plugin-packaging, git-init, claude-plugin-validate]

# Dependency graph
requires:
  - phase: 11
    provides: sota-numerics plugin (blocking plan:post gate, advisory fragments, capability.json) as a subdirectory of gsd-beads
  - phase: 12-01
    provides: proven tracer sequence (stage outside working tree -> fix relocation paths -> README/CI -> checkpoint -> gh repo create --push -> fresh-clone verify)
provides:
  - Public standalone GitHub repo davdittrich/sota-numerics (branch main, one commit)
  - Second proof of the extraction sequence, now covering a plugin with a blocking gate and a Python unit-test suite
affects: [12-03, 12-04]

# Actuals (#2632)
actuals:
  tokens: 12000
  tasks: 4
  commits: 0

# Tech tracking
tech-stack:
  added: []
  patterns: ["stage-outside-tree extraction (repeat of 12-01's pattern): cp subdirectory to /tmp, fix relocation-path bugs in place, fresh git init, gh repo create --source=. --push, verify from a throwaway clone rather than the staging tree"]

key-files:
  created:
    - /tmp/sota-numerics-extract/README.md
    - /tmp/sota-numerics-extract/.github/workflows/ci.yml
    - /tmp/sota-numerics-extract/LICENSE
    - /tmp/sota-numerics-extract/.gitignore
    - /tmp/sota-numerics-extract/tests/.planning/.gitkeep
  modified:
    - /tmp/sota-numerics-extract/tests/test-session-start.sh (REPO_ROOT/SCRIPT/PLUGIN_DIR re-anchored one level up, not two)
    - /tmp/sota-numerics-extract/hooks/capability-auto-install.sh (two comment path refs re-anchored, no executable line touched)

key-decisions:
  - "Approved repo name: davdittrich/sota-numerics, public (Task 3 checkpoint, option create-as-planned)"
  - "Kept the discretionary .github/workflows/ci.yml (D-01..D-10 silent on CI) — for this plugin the file adds coverage rather than relocating it, since sota-numerics' tests were never wired into gsd-beads' own ci.yml"

patterns-established:
  - "Confirms the 12-01 extraction pattern generalizes to a plugin with a blocking plan:post gate and a Python unittest suite, not just an advisory-only plugin: the only new wrinkle was a test-collection import-time dependency (see Deviations), not a gate-logic or path-resolution difference."

requirements-completed: [D-01, D-03, D-05, D-07, D-09, D-10]

coverage:
  - id: D1
    description: "davdittrich/sota-numerics exists as a public GitHub repo whose root is the plugin root, on branch main"
    requirement: "D-01"
    verification:
      - kind: integration
        ref: "gh repo view davdittrich/sota-numerics --json visibility,defaultBranchRef,isPrivate -> PUBLIC main false"
        status: pass
    human_judgment: false
  - id: D2
    description: "Repo history is a fresh init with exactly one commit, nothing imported from gsd-beads"
    requirement: "D-03"
    verification:
      - kind: integration
        ref: "git rev-list --count HEAD in /tmp/sota-numerics-verify -> 1"
        status: pass
    human_judgment: false
  - id: D3
    description: "Fresh clone passes claude plugin validate . --strict, the bash smoke test (7 PASS cases), and the Python unit test (19 tests)"
    requirement: "D-10"
    verification:
      - kind: integration
        ref: "claude plugin validate . --strict in /tmp/sota-numerics-verify -> Validation passed"
        status: pass
      - kind: integration
        ref: "bash tests/test-session-start.sh in /tmp/sota-numerics-verify -> 7/7 PASS, exit 0"
        status: pass
      - kind: integration
        ref: "python3 -m unittest tests/test_check_alternatives.py in /tmp/sota-numerics-verify -> Ran 19 tests, OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "README carries all seven mandated sections (What it does, Requirements, Install, Uninstall, Caveats, License, gsd-core), states the plan:post gate is blocking, no bd mentions"
    requirement: "D-09"
    verification:
      - kind: other
        ref: "grep -n '^## ' README.md in fresh clone -> 7 headings in the mandated order"
        status: pass
    human_judgment: false
  - id: D5
    description: "gsd-beads working tree left provably unmodified by this plan (no marketplace.json edit, no sota-numerics/ subdirectory change)"
    verification:
      - kind: integration
        ref: "git -C /home/dd/projects/gsd-beads status --porcelain -- .claude-plugin sota-numerics -> empty"
        status: pass
    human_judgment: false

duration: ~15min (resumed across a session interruption; Task 1-3 and Task 4's push predate this session)
completed: 2026-08-17
status: complete
---

# Phase 12 Plan 02: Ship sota-numerics Publicly Summary

**Extracted `sota-numerics/` into standalone public repo `davdittrich/sota-numerics` (fresh git init, one commit `31608f2`), proving the 12-01 extraction tracer generalizes to a plugin carrying a blocking `plan:post` gate and its own Python unittest suite (19 tests), verified clean from an independent fresh clone.**

## Performance

- **Duration:** ~15 min (this plan spanned a session interruption; Tasks 1-3 and Task 4's `gh repo create --push` completed in a prior executor run, this run performed only Task 4's fresh-clone verification and closeout)
- **Tasks:** 4/4
- **Files modified:** 7 (all under `/tmp/sota-numerics-extract/`, none inside the gsd-beads working tree)

## Accomplishments
- Staged the plugin at `/tmp/sota-numerics-extract/` (outside the gsd-beads tree), fixed the `REPO_ROOT`/`SCRIPT`/`PLUGIN_DIR` relocation-path bug in `tests/test-session-start.sh` (one-level climb instead of two) and re-anchored two stale cross-repo comment refs in `hooks/capability-auto-install.sh`; left `tests/test_check_alternatives.py` byte-identical, unedited, per the plan
- Wrote the standalone repo's `README.md` (seven mandated D-09 sections, blocking-gate semantics stated prominently in Caveats) and `.github/workflows/ci.yml`, committed the fresh-init history as a single commit `31608f2` on `main`
- User approved the one-way public-repo checkpoint (option `create-as-planned`: `davdittrich/sota-numerics`, public)
- Created and pushed the public repo via `gh repo create --public --source=. --push`; verified from an independent fresh clone at `/tmp/sota-numerics-verify/`: `claude plugin validate . --strict` passes, bash smoke test 7/7 PASS, Python unit test 19/19 OK, exactly one commit, gsd-beads working tree untouched

## Task Commits

No commits landed in the gsd-beads repository for Tasks 1-4 — every file this plan created or modified lives in the staging tree `/tmp/sota-numerics-extract/`, which is its own independent git repository (commit `31608f2`, now pushed to `davdittrich/sota-numerics`). This matches the plan's `files_modified` frontmatter (only `/tmp/...` paths) and Task 4's acceptance criteria requiring `git -C /home/dd/projects/gsd-beads status --porcelain` to show no change under the plugin path.

1. **Task 1: Stage sota-numerics outside the gsd-beads tree and fix relocation paths** - staging-repo commit not yet made at this point (pre-init); verified via `bash tests/test-session-start.sh` and `python3 -m unittest tests/test_check_alternatives.py` both passing from `/tmp/sota-numerics-extract`
2. **Task 2: Write README + CI, commit fresh-init history** - `31608f2` (staging repo, not gsd-beads) - `feat: extract sota-numerics as a standalone plugin repo`
3. **Task 3: Approve public repo creation** - checkpoint:decision, user selected `create-as-planned`
4. **Task 4: Create public repo, push, verify from fresh clone** - no new commit (push of existing `31608f2` to `davdittrich/sota-numerics`); verification-only in gsd-beads

**Plan metadata:** (this commit) `docs(12-02): complete ship-sota-numerics-publicly plan`

## Files Created/Modified
- `/tmp/sota-numerics-extract/README.md` - D-09 seven-section README (What it does, Requirements, Install, Uninstall, Caveats, License, gsd-core), documents the blocking `plan:post` gate as prominently as the advisory fragments
- `/tmp/sota-numerics-extract/.github/workflows/ci.yml` - minimal CI running both the bash smoke test and the Python unit test
- `/tmp/sota-numerics-extract/LICENSE` - byte-identical MIT copy from gsd-beads' LICENSE
- `/tmp/sota-numerics-extract/.gitignore` - two lines, `__pycache__/` and `*.pyc` (load-bearing: the Python test creates `tests/__pycache__/`)
- `/tmp/sota-numerics-extract/tests/test-session-start.sh` - REPO_ROOT climbs one level (was two), SCRIPT/PLUGIN_DIR re-anchored to the new repo root
- `/tmp/sota-numerics-extract/hooks/capability-auto-install.sh` - two comment-only path refs re-anchored to this repo's own layout; no executable line changed
- `/tmp/sota-numerics-extract/tests/.planning/.gitkeep` - added (see Deviations); `tests/test_check_alternatives.py` itself left byte-identical to the gsd-beads original

## Decisions Made
- Approved repo name: `davdittrich/sota-numerics`, public (Task 3 checkpoint, `create-as-planned`)
- Kept the discretionary `.github/workflows/ci.yml` (D-01..D-10 are silent on CI for the split repos); unlike ponytail-everywhere's smoke test this plugin's tests were never wired into gsd-beads' own `ci.yml`, so for this repo the file adds coverage rather than relocating it
- No tag/release cut: D-07 rules out a release archive; Plan 03's unpinned marketplace `github` source resolves the pushed commit SHA as the version

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added `tests/.planning/.gitkeep` placeholder so `test_check_alternatives.py` imports cleanly at the relocated root**
- **Found during:** Task 1
- **Issue:** `tests/test_check_alternatives.py`'s module-level `PROJECT_ROOT = _project_root()` call failed at import time in the relocated staging tree — `_project_root()` walks up from the test file's directory looking for a `.planning/` ancestor, and none existed anywhere above `/tmp/sota-numerics-extract/tests/` once the plugin was copied out of gsd-beads (which has its own `.planning/` at the repo root, no longer an ancestor of the relocated tree).
- **Fix:** Added a new placeholder directory `tests/.planning/.gitkeep` to the staging tree so the walk-up finds a `.planning/` ancestor immediately. `test_check_alternatives.py` itself was left byte-identical to the gsd-beads original (confirmed via `diff` — no output), honoring the plan's explicit "do not edit this file" instruction literally: the fix supplies the directory the test's existing logic expects, rather than changing the test's logic to expect something else.
- **Files modified:** `/tmp/sota-numerics-extract/tests/.planning/.gitkeep` (new file, staging tree only)
- **Commit:** `31608f2` (staging repo)

Or otherwise: no other deviations. All other tasks executed exactly as written.

## Issues Encountered

None beyond the deviation above. The resumed session's `gh repo view`, fresh `git clone`, `claude plugin validate . --strict`, `bash tests/test-session-start.sh`, and `python3 -m unittest tests/test_check_alternatives.py` all passed on the first attempt against the already-pushed repo.

## User Setup Required

None - no external service configuration required. (`gh` was already authenticated as `davdittrich`; no new credentials created.)

## Next Phase Readiness

- **Approved repo name for this plan:** `davdittrich/sota-numerics` (public)
- **Pushed commit SHA:** `31608f2fda6762958db71c055a5592018d9c6b09`
- **Discretionary `.github/workflows/ci.yml`:** kept (not struck)
- The tracer sequence proven twice now (12-01 and this plan): stage outside tree -> fix relocation paths -> README/CI -> checkpoint -> `gh repo create --push` -> fresh-clone verify, including for a plugin with a blocking gate and a Python test suite.
- D-10 is half-satisfied here (`validate --strict` clean on the pushed repo, both test suites pass in the fresh clone); the marketplace add/install/uninstall round trip is deliberately deferred to Plan 03, which is the first point a marketplace entry pointing at this repo exists.
- `.claude-plugin/marketplace.json` in gsd-beads remains untouched, confirmed by `git status --porcelain -- .claude-plugin` returning empty — Plan 03's job.
- Both `davdittrich/ponytail-everywhere` (12-01) and `davdittrich/sota-numerics` (this plan) now exist and are verified — Plan 03 can repoint the marketplace without pointing at anything unproven.

---
*Phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly*
*Completed: 2026-08-17*

## Self-Check: PASSED

- FOUND: `.planning/phases/12-.../12-02-SUMMARY.md`
- FOUND: commit `31608f2` in `/tmp/sota-numerics-extract` (staging repo)
- FOUND: commit `31608f2` in `/tmp/sota-numerics-verify` (fresh clone of pushed `davdittrich/sota-numerics`, confirming the push landed)
