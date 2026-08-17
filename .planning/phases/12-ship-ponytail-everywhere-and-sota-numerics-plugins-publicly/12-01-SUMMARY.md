---
phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
plan: 01
subsystem: infra
tags: [github, gh-cli, plugin-packaging, git-init, claude-plugin-validate]

# Dependency graph
requires:
  - phase: 10
    provides: ponytail-everywhere plugin (hooks, capability.json, test harness) as a subdirectory of gsd-beads
  - phase: 11.1
    provides: beads.enabled default-true precedent for capability doc sweeps
provides:
  - Public standalone GitHub repo davdittrich/ponytail-everywhere (branch main, one commit)
  - Proven tracer sequence (stage outside working tree -> fix relocation paths -> README/CI -> checkpoint -> gh repo create --push -> fresh-clone verify) for Plan 02 to repeat against sota-numerics
affects: [12-02, 12-03, 12-04]

# Actuals (#2632)
actuals:
  tokens: 0
  tasks: 4
  commits: 0

# Tech tracking
tech-stack:
  added: []
  patterns: ["stage-outside-tree extraction: cp subdirectory to /tmp, fix relocation-path bugs in place, fresh git init, gh repo create --source=. --push, verify from a throwaway clone rather than the staging tree"]

key-files:
  created:
    - /tmp/ponytail-everywhere-extract/README.md
    - /tmp/ponytail-everywhere-extract/.github/workflows/ci.yml
    - /tmp/ponytail-everywhere-extract/LICENSE
    - /tmp/ponytail-everywhere-extract/.gitignore
  modified:
    - /tmp/ponytail-everywhere-extract/tests/test-session-start.sh (REPO_ROOT/SCRIPT/PLUGIN_DIR re-anchored one level up, not two)
    - /tmp/ponytail-everywhere-extract/hooks/capability-auto-install.sh (two comment path refs re-anchored, no executable line touched)

key-decisions:
  - "Approved repo name: davdittrich/ponytail-everywhere, public (Task 3 checkpoint, option create-as-planned)"
  - "Kept the discretionary .github/workflows/ci.yml (D-01..D-10 silent on CI) to avoid a verification regression: gsd-beads' own ci.yml runs this smoke test today and Plan 04 removes that step"

patterns-established:
  - "Pattern: extract a plugin subdirectory to a standalone public repo by staging OUTSIDE the source working tree, fixing only the relocation-path assumptions (REPO_ROOT climb depth), fresh git init (no history import per D-03), gh repo create --source=. --push (no --add-readme/--gitignore/--license flags), then verify from an independent throwaway clone."

requirements-completed: [D-01, D-03, D-05, D-07, D-09, D-10]

coverage:
  - id: D1
    description: "davdittrich/ponytail-everywhere exists as a public GitHub repo whose root is the plugin root, on branch main"
    requirement: "D-01"
    verification:
      - kind: integration
        ref: "gh repo view davdittrich/ponytail-everywhere --json visibility,defaultBranchRef,isPrivate -> PUBLIC main false"
        status: pass
    human_judgment: false
  - id: D2
    description: "Repo history is a fresh init with exactly one commit, nothing imported from gsd-beads"
    requirement: "D-03"
    verification:
      - kind: integration
        ref: "git rev-list --count HEAD in /tmp/ponytail-everywhere-verify -> 1"
        status: pass
    human_judgment: false
  - id: D3
    description: "Fresh clone passes claude plugin validate . --strict and the plugin's own smoke test (11 PASS cases)"
    requirement: "D-10"
    verification:
      - kind: integration
        ref: "claude plugin validate . --strict in /tmp/ponytail-everywhere-verify -> Validation passed"
        status: pass
      - kind: integration
        ref: "bash tests/test-session-start.sh in /tmp/ponytail-everywhere-verify -> 11/11 PASS, exit 0"
        status: pass
    human_judgment: false
  - id: D4
    description: "README carries all seven mandated sections (What it does, Requirements, Install, Uninstall, Caveats, License, gsd-core) with plugin-accurate content, no bd/Python mentions"
    requirement: "D-09"
    verification:
      - kind: other
        ref: "grep -n '^## ' README.md in fresh clone -> 7 headings in the mandated order"
        status: pass
    human_judgment: false
  - id: D5
    description: "gsd-beads working tree left provably unmodified by this plan (no marketplace.json edit, no ponytail-everywhere/ subdirectory change)"
    verification:
      - kind: integration
        ref: "git -C /home/dd/projects/gsd-beads status --porcelain -- .claude-plugin ponytail-everywhere -> empty"
        status: pass
    human_judgment: false

duration: ~18min (resumed across a session interruption; Task 1-2 work predates this session)
completed: 2026-08-17
status: complete
---

# Phase 12 Plan 01: Ship ponytail-everywhere Publicly Summary

**Extracted `ponytail-everywhere/` into standalone public repo `davdittrich/ponytail-everywhere` (fresh git init, one commit `36245fe`) with a full README/CI/LICENSE treatment, and proved D-10's validate half plus the smoke test pass from an independent fresh clone.**

## Performance

- **Duration:** ~18 min (this plan spanned a session interruption; Tasks 1-3 and the Task 4 push completed in a prior executor run, this run only performed Task 4's fresh-clone verification and closeout)
- **Tasks:** 4/4
- **Files modified:** 6 (all under `/tmp/ponytail-everywhere-extract/`, none inside the gsd-beads working tree)

## Accomplishments
- Staged the plugin at `/tmp/ponytail-everywhere-extract/` (outside the gsd-beads tree), fixed the `REPO_ROOT`/`SCRIPT`/`PLUGIN_DIR` relocation-path bug in `tests/test-session-start.sh` (one-level climb instead of two) and re-anchored two stale cross-repo comment refs in `hooks/capability-auto-install.sh`
- Wrote the standalone repo's `README.md` (seven mandated D-09 sections) and `.github/workflows/ci.yml`, committed the fresh-init history as a single commit `36245fe` on `main`
- User approved the one-way public-repo checkpoint (option `create-as-planned`: `davdittrich/ponytail-everywhere`, public)
- Created and pushed the public repo via `gh repo create --public --source=. --push`; verified from an independent fresh clone at `/tmp/ponytail-everywhere-verify/`: `claude plugin validate . --strict` passes, all 11 smoke-test cases PASS, exactly one commit, gsd-beads working tree untouched

## Task Commits

No commits landed in the gsd-beads repository for Tasks 1-4 — every file this plan created or modified lives in the staging tree `/tmp/ponytail-everywhere-extract/`, which is its own independent git repository (commit `36245fe`, now pushed to `davdittrich/ponytail-everywhere`). This is intended: the plan's `files_modified` frontmatter lists only `/tmp/...` paths, and Task 4's acceptance criteria explicitly require `git -C /home/dd/projects/gsd-beads status --porcelain` to show no change.

1. **Task 1: Stage ponytail-everywhere outside the gsd-beads tree and fix relocation paths** - staging-repo commit not yet made at this point (pre-init); verified via `bash tests/test-session-start.sh` passing from `/tmp/ponytail-everywhere-extract`
2. **Task 2: Write README + CI, commit fresh-init history** - `36245fe` (staging repo, not gsd-beads) - `feat: extract ponytail-everywhere as a standalone plugin repo`
3. **Task 3: Approve public repo creation** - checkpoint:decision, user selected `create-as-planned`
4. **Task 4: Create public repo, push, verify from fresh clone** - no new commit (push of existing `36245fe` to `davdittrich/ponytail-everywhere`); verification-only in gsd-beads

**Plan metadata:** (this commit) `docs(12-01): complete ship-ponytail-everywhere-publicly plan`

## Files Created/Modified
- `/tmp/ponytail-everywhere-extract/README.md` - D-09 seven-section README (What it does, Requirements, Install, Uninstall, Caveats, License, gsd-core)
- `/tmp/ponytail-everywhere-extract/.github/workflows/ci.yml` - minimal CI mirroring gsd-beads' shape, runs `bash tests/test-session-start.sh`
- `/tmp/ponytail-everywhere-extract/LICENSE` - byte-identical MIT copy from gsd-beads' LICENSE
- `/tmp/ponytail-everywhere-extract/.gitignore` - two lines, `__pycache__/` and `*.pyc`
- `/tmp/ponytail-everywhere-extract/tests/test-session-start.sh` - REPO_ROOT climbs one level (was two), SCRIPT/PLUGIN_DIR re-anchored to the new repo root
- `/tmp/ponytail-everywhere-extract/hooks/capability-auto-install.sh` - two comment-only path refs re-anchored to this repo's own layout; no executable line changed

## Decisions Made
- Approved repo name: `davdittrich/ponytail-everywhere`, public (Task 3 checkpoint, `create-as-planned`)
- Kept the discretionary `.github/workflows/ci.yml` (D-01..D-10 are silent on CI for the split repos) to avoid silently deleting an existing CI check — gsd-beads' own `ci.yml` runs this exact smoke test today and Plan 04 removes that step along with the subdirectory
- No tag/release cut: D-07 rules out a release archive; Plan 03's unpinned marketplace `github` source resolves the pushed commit SHA as the version

## Deviations from Plan

None - plan executed exactly as written across both executor sessions. The only operational note: this executor run resumed after a session interruption between Task 4's `gh repo create --push` (completed by the interrupted run) and Task 4's fresh-clone verification (completed by this run) — no task work was redone, no commits were duplicated.

## Issues Encountered

None. The resumed session's `gh repo view`, fresh `git clone`, `claude plugin validate . --strict`, and `bash tests/test-session-start.sh` all passed on the first attempt against the already-pushed repo.

## User Setup Required

None - no external service configuration required. (`gh auth status` was already authenticated as `davdittrich` per the plan's precondition; no new credentials created.)

## Next Phase Readiness

- **Approved repo name for this plan:** `davdittrich/ponytail-everywhere` (public)
- **Pushed commit SHA:** `36245fe5da64dcf3f03fa59da455cb9e9afab4f5`
- **Discretionary `.github/workflows/ci.yml`:** kept (not struck)
- The tracer is proven end-to-end: Plan 02 can repeat this exact sequence (stage outside tree -> fix relocation paths -> README/CI -> checkpoint -> `gh repo create --push` -> fresh-clone verify) for `sota-numerics` with no unknowns left.
- D-10 is half-satisfied here (`validate --strict` clean on the pushed repo); the marketplace add/install/uninstall round trip is deliberately deferred to Plan 03, which is the first point a marketplace entry pointing at this repo exists.
- `.claude-plugin/marketplace.json` in gsd-beads remains untouched, confirmed by `git status --porcelain -- .claude-plugin` returning empty — Plan 03's job.

---
*Phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly*
*Completed: 2026-08-17*

## Self-Check: PASSED

- FOUND: `.planning/phases/12-.../12-01-SUMMARY.md`
- FOUND: commit `36245fe` in `/tmp/ponytail-everywhere-extract` (staging repo)
- FOUND: commit `36245fe` in `/tmp/ponytail-everywhere-verify` (fresh clone of pushed `davdittrich/ponytail-everywhere`, confirming the push landed)
