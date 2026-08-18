---
phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly
plan: 01
subsystem: infra
tags: [claude-plugin, gh-cli, git-init, markdown-lint, rumdl, public-repo]

# Dependency graph
requires:
  - phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
    provides: the wrap-then-extract playbook (stage outside tree, fresh git init, gh repo create --source=. --push, fresh-clone verify) this plan repeats
  - phase: 13-markdown-linting-capability-dogfood
    provides: the `.gsd/capabilities/markdown-linting/` capability bundle this plan wraps and publishes
provides:
  - public GitHub repo davdittrich/markdown-linting, branch main, one commit (d30ab57), 16 tracked files
  - proven plugin-tree wrapper shape (5-key manifest, no skills key, vendored capability-auto-install.sh) that Plan 02 repeats for pr-workflow
affects: [15-02-pr-workflow-extraction, 15-03-marketplace-entry, 15-05-bundle-removal]

actuals:
  tokens: 0
  tasks: 2
  commits: 1
duration_context: >
  Tasks 1-2 (staging, README, CI, fresh-init commit) were completed by a prior agent in a
  separate machine-local staging repo at /tmp/markdown-linting-extract, not in this gsd-beads
  worktree — no gsd-beads diff to measure tokens against. This continuation agent executed
  Task 3 (checkpoint resolution) and Task 4 (gh repo create + push + fresh-clone verify), which
  also touch no gsd-beads-tracked files other than this SUMMARY.

tech-stack:
  added: []
  patterns:
    - "plugin-tree wrapper: 5-key plugin.json (name/version/description/author/license), no skills key, SessionStart hook addressed via ${CLAUDE_PLUGIN_ROOT}"
    - "capability-auto-install.sh vendored byte-identical per plugin (Phase 10.1 D-05)"

key-files:
  created:
    - /tmp/markdown-linting-extract/.claude-plugin/plugin.json
    - /tmp/markdown-linting-extract/hooks/hooks.json
    - /tmp/markdown-linting-extract/hooks/session-start.sh
    - /tmp/markdown-linting-extract/hooks/capability-auto-install.sh
    - /tmp/markdown-linting-extract/README.md
    - /tmp/markdown-linting-extract/LICENSE
    - /tmp/markdown-linting-extract/.gitignore
    - /tmp/markdown-linting-extract/.github/workflows/ci.yml
  modified: []

key-decisions:
  - "Premise correction (see below): no top-level markdown-linting/ subdirectory ever existed in gsd-beads history; a plugin-tree wrapper had to be built around .gsd/capabilities/markdown-linting/ from scratch, not extracted from an existing top-level tree."
  - "Task 3 checkpoint resolved: operator approved option create-as-planned — public repo name davdittrich/markdown-linting, no rename."
  - "Task 4's plan-specified verify command (python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -t .) fails with ImportError: Start directory is not importable — the tests/ dir has no __init__.py, and -t . makes the loader treat it as a dotted package import under the hidden .gsd/ path. This is the same '-t . unittest-discover defect' STATE.md already logged as fixed at the plan-doc level for 14-01/14-02/14-03-PLAN.md (commit f31e6f4) but was not back-ported to 15-01-PLAN.md. Rule 1 auto-fix: ran the equivalent command without -t . (python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -v), which is start-dir-relative discovery with no package-import requirement and exercises the identical 12 tests. All 12 pass. No code or plan file was modified — this is a verification-command-only deviation, documented here per the plan's own precedent."

patterns-established:
  - "Fresh-clone gate always run in a throwaway directory (/tmp/<capability>-verify), never re-checked against the staging tree, so the check proves what a stranger actually receives."

requirements-completed: [D-00, D-01, D-03, D-09, D-10]

coverage:
  - id: D1
    description: "Public GitHub repo davdittrich/markdown-linting exists, is public, branch main, fresh single-commit history (D-00)"
    requirement: "D-00"
    verification:
      - kind: other
        ref: "gh repo view davdittrich/markdown-linting --json visibility,defaultBranchRef,isPrivate -> 'PUBLIC main false'"
        status: pass
      - kind: other
        ref: "git -C /tmp/markdown-linting-verify rev-list --count HEAD -> 1"
        status: pass
    human_judgment: false
  - id: D2
    description: "Plugin validates strictly and the capability's test suite passes from a fresh HTTPS clone (D-10 validate half)"
    requirement: "D-10"
    verification:
      - kind: other
        ref: "cd /tmp/markdown-linting-verify && claude plugin validate . --strict -> Validation passed"
        status: pass
      - kind: unit
        ref: "cd /tmp/markdown-linting-verify && python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -v -> Ran 12 tests, OK"
        status: pass
    human_judgment: false
  - id: D3
    description: "Fresh clone tracks exactly 16 files including the bundle's config and skill paths — the staged .gitignore did not silently exclude the capability payload (highest-severity failure mode)"
    verification:
      - kind: other
        ref: "git -C /tmp/markdown-linting-verify ls-files | wc -l -> 16; test -f config/.rumdl.toml; test -f skills/markdown-linting-report/SKILL.md"
        status: pass
    human_judgment: false
  - id: D4
    description: "gsd-beads working tree (.gsd/, .claude-plugin/) is untouched by this plan"
    verification:
      - kind: other
        ref: "git -C /home/dd/projects/gsd-beads status --porcelain -- .claude-plugin -> empty"
        status: pass
    human_judgment: false
  - id: D5
    description: "README.md meets D-09's seven-section structure with rumdl named first-class (structural/prose review, not independently re-verified by this continuation agent — inherited from Task 2's own acceptance criteria, already checked before the operator's checkpoint approval)"
    requirement: "D-09"
    verification: []
    human_judgment: true
    rationale: "This continuation agent did not re-derive README content; it verified structural gates (validate --strict, section headings via prior task's own acceptance criteria) but did not perform an independent human-quality read of the prose against D-09's rumdl-first-class bar. Flagging for verify-work spot-check."

duration: ~10min (this continuation session; Tasks 1-2 were a separate prior session)
completed: 2026-08-18
status: complete
---

# Phase 15 Plan 01: Ship markdown-linting Plugin Publicly Summary

**Public repo `davdittrich/markdown-linting` created and pushed (commit `d30ab57`), fresh HTTPS clone passes `claude plugin validate . --strict` and all 12 capability unit tests.**

## Performance

- **Duration:** ~10 min (this continuation agent's portion: Task 3 checkpoint resolution + Task 4 repo creation/push/verify)
- **Started:** 2026-08-18T21:00:00Z (approx, continuation agent spawn)
- **Completed:** 2026-08-18T21:10:30Z
- **Tasks:** 2 (Task 3, Task 4) completed this session; Tasks 1-2 completed by a prior agent
- **Files modified (this repo):** 1 (this SUMMARY.md)

## Accomplishments
- Resolved Task 3's blocking checkpoint: operator approved `create-as-planned`.
- Created public GitHub repository `davdittrich/markdown-linting` and pushed the single staged commit (`gh repo create davdittrich/markdown-linting --public --source=. --push`).
- Verified from a fresh HTTPS clone at `/tmp/markdown-linting-verify`: repo is public, default branch `main`, exactly one commit, 16 tracked files, `claude plugin validate . --strict` exits 0, and the capability's own 12-test `unittest` suite passes.
- Confirmed gsd-beads' `.claude-plugin/marketplace.json` and `.gsd/` tree remain untouched (that edit belongs to Plan 03).

## Task Commits

Tasks 1-2 were committed in a separate machine-local staging repo (not gsd-beads):

1. **Task 1+2: Build plugin-tree wrapper, write README/CI, fresh-init commit** - `d30ab57` (feat, in `/tmp/markdown-linting-extract`, pushed to `davdittrich/markdown-linting`)

Task 3 (checkpoint) and Task 4 (repo creation/push/verify) create no file changes in either repo besides this SUMMARY.

**Plan metadata:** (this SUMMARY.md commit, gsd-beads worktree)

## Files Created/Modified
- `/tmp/markdown-linting-extract/.claude-plugin/plugin.json` - 5-key plugin manifest, no `skills` key (PD-01)
- `/tmp/markdown-linting-extract/hooks/hooks.json` - SessionStart hook registration via `${CLAUDE_PLUGIN_ROOT}`
- `/tmp/markdown-linting-extract/hooks/session-start.sh` - PD-03 adaptation (no beads-specific logic)
- `/tmp/markdown-linting-extract/hooks/capability-auto-install.sh` - byte-identical vendored copy (PD-02)
- `/tmp/markdown-linting-extract/README.md` - D-09's 7-section structure, rumdl first-class
- `/tmp/markdown-linting-extract/LICENSE` - MIT, byte-identical to gsd-beads'
- `/tmp/markdown-linting-extract/.gitignore` - 2 lines, no capability-ignore block
- `/tmp/markdown-linting-extract/.github/workflows/ci.yml` - runs bundle's unittest suite
- `.planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-01-SUMMARY.md` - this file (gsd-beads worktree)

## Decisions Made
- **Premise correction** (per plan's `<premise_correction>` block): 15-CONTEXT.md's domain section claimed this phase extracts an existing top-level `markdown-linting/` subdirectory "currently only dogfooded as subdirectories inside gsd-beads." That premise is factually wrong: `git ls-files` shows no top-level `markdown-linting/` tree ever existed. Phase 13 built the capability directly at `.gsd/capabilities/markdown-linting/` with `"hooks": []` and no `.claude-plugin/plugin.json` anywhere. Consequence: this plan is wrap-then-extract, not extract-only — Task 1 constructed the plugin-tree wrapper from scratch. D-00's intent (one plugin, one public repo, fresh init, marketplace-reachable) is unchanged and fully honored.
- Task 3 checkpoint decision: operator selected `create-as-planned` — public repo `davdittrich/markdown-linting`, no rename, proceed as written.
- Ran Task 4's verify block's unittest-discover check without the plan's literal `-t .` flag (see Deviations below) — same test suite, same 12 tests, all pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Task 4's `-t .` unittest-discover verify command fails; ran the equivalent command without `-t .`**
- **Found during:** Task 4 (fresh-clone verification)
- **Issue:** The plan's automated verify command `cd /tmp/markdown-linting-verify && python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -t .` raises `ImportError: Start directory is not importable: '/tmp/markdown-linting-verify/.gsd/capabilities/markdown-linting/tests'`. The `tests/` directory has no `__init__.py`, and `-t .` forces the loader to resolve the start directory as a dotted package relative to the top-level directory, which fails under the hidden `.gsd/` path. This is the identical defect STATE.md's Decisions log already recorded as fixed at the plan-doc level for `14-01/14-02/14-03-PLAN.md` (commit `f31e6f4`) — the fix was not back-ported to `15-01-PLAN.md`'s Task 4 verify block.
- **Fix:** Ran `python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -v` (identical `-s` start directory, no `-t .`). This is start-directory-relative discovery with no package-import requirement — it exercises the same `test_lint.py` module and the same 12 tests.
- **Files modified:** None — no plan file or code was edited; this is a verification-invocation-only substitution, run and reported here per the Phase 14 precedent of documenting rather than "silently correcting" plan-doc verify-command defects.
- **Verification:** `Ran 12 tests in 0.027s / OK` — all tests pass (`TestCuratedRuleset`, `TestEmptyTargetSet`, `TestFailOpen` x5, `TestReportMatchesHandRun`, `TestToolResolution` x2).
- **Committed in:** N/A (no code change; recorded in this SUMMARY only)

---

**Total deviations:** 1 auto-fixed (1 bug — pre-existing plan-doc verify-command defect, inherited from Phase 13's original shape and not yet back-ported to this plan)
**Impact on plan:** No scope creep. The substituted command proves the identical claim (capability test suite passes from the fresh clone) that the plan's literal command intended to prove.

## Issues Encountered
None beyond the documented deviation above.

## User Setup Required
None - no external service configuration required (the `gh` CLI was already authenticated as `davdittrich` with `repo` scope before this session began).

## Next Phase Readiness
- Task 3 (checkpoint) and Task 4 (public push + verify) are both complete. All 4 tasks in 15-01-PLAN.md are now done.
- `davdittrich/markdown-linting` is public, on `main`, one commit (`d30ab57`), validated and test-proven from a fresh clone — the tracer sequence Plan 02 repeats for `pr-workflow` is fully proven end to end, including PD-01's no-`skills`-key manifest shape.
- D-10 is half-satisfied by this plan (validate-from-fresh-clone half); the marketplace add/install/uninstall round trip is deliberately deferred to Plan 03, the first point at which a marketplace entry pointing at this repo exists.
- Plan 03 must not point `.claude-plugin/marketplace.json` at `davdittrich/markdown-linting` until Plan 02 has also passed this same gate for `pr-workflow` (both new repos verified before either marketplace entry is written), per this plan's own Task 4 note.
- Plan 05 (disposition of `.gsd/capabilities/markdown-linting/` inside gsd-beads) is unblocked now that the public repo exists as the bundle's new home.

## Self-Check: PASSED

- `git -C /tmp/markdown-linting-verify rev-parse HEAD` -> `d30ab57e68c9f2396763404029a4df1cf01f0276` — FOUND, matches the commit pushed from `/tmp/markdown-linting-extract`.
- `gh repo view davdittrich/markdown-linting` -> public, main, isPrivate false — FOUND.
- `/tmp/markdown-linting-verify/.claude-plugin/plugin.json` — FOUND (fresh clone).
- `/tmp/markdown-linting-verify/.gsd/capabilities/markdown-linting/config/.rumdl.toml` — FOUND.
- `/tmp/markdown-linting-verify/.gsd/capabilities/markdown-linting/skills/markdown-linting-report/SKILL.md` — FOUND.

---
*Phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly*
*Plan: 01*
*Completed: 2026-08-18*
