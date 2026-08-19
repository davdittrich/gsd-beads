---
phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly
plan: 02
subsystem: infra
tags: [claude-code-plugin, github, gh-cli, unittest, pr-workflow]

# Dependency graph
requires:
  - phase: 14-pr-workflow-capability-dogfood
    provides: the `.gsd/capabilities/pr-workflow/` capability bundle this plan extracted (live-proven on gsd-beads)
provides:
  - Public GitHub repository `davdittrich/pr-workflow`, branch `main`, one commit (`0dc48556495839544d1be8d48b68e7c2e52b6d03`), 17 tracked files, plugin root at repo root
affects: [15-03-ship-plugin-manifests-and-marketplace-registration, 15-05]

actuals:
  tokens: 3200
  tasks: 4
  commits: 1

tech-stack:
  added: []
  patterns: [stage-outside-tree, fresh-git-init, gh-repo-create-source-push, fresh-clone-verify]

key-files:
  created:
    - /tmp/pr-workflow-extract/.claude-plugin/plugin.json
    - /tmp/pr-workflow-extract/hooks/hooks.json
    - /tmp/pr-workflow-extract/hooks/session-start.sh
    - /tmp/pr-workflow-extract/hooks/capability-auto-install.sh
    - /tmp/pr-workflow-extract/README.md
    - /tmp/pr-workflow-extract/LICENSE
    - /tmp/pr-workflow-extract/.gitignore
    - /tmp/pr-workflow-extract/.github/workflows/ci.yml
  modified: []

key-decisions:
  - "Task 3 checkpoint resolved: operator approved option create-as-planned — create davdittrich/pr-workflow public and push exactly as planned, no name change."
  - "Task 4's -t . unittest-discover verify command fails to import the start dir on this machine (Python 3.14.7) because the path component pr-workflow contains a hyphen, an invalid Python identifier fragment — same class of pre-existing verify-command defect STATE.md already documents for Phase 13/14 (dotted-module-name incompatible with hidden .gsd/ dir). Not a code defect: invoking `python3 -m unittest discover -s tests` with cwd = the bundle root (.gsd/capabilities/pr-workflow/) runs cleanly and reports 27/27 passing, both in the staging tree and in the fresh clone."

requirements-completed: [D-00, D-01, D-03, D-09, D-10]

coverage:
  - id: D1
    description: "Public GitHub repo davdittrich/pr-workflow created and pushed, one commit, fresh init"
    requirement: D-00
    verification:
      - kind: other
        ref: "gh repo view davdittrich/pr-workflow --json visibility,defaultBranchRef,isPrivate -> 'PUBLIC main false'"
        status: pass
      - kind: other
        ref: "git -C /tmp/pr-workflow-verify rev-list --count HEAD -> 1"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fresh HTTPS clone of the pushed repo passes claude plugin validate . --strict"
    requirement: D-10
    verification:
      - kind: other
        ref: "cd /tmp/pr-workflow-verify && claude plugin validate . --strict -> Validation passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Bundle's own test suite (27 tests) passes from the round-tripped fresh clone"
    verification:
      - kind: unit
        ref: "cd /tmp/pr-workflow-verify/.gsd/capabilities/pr-workflow && python3 -m unittest discover -s tests -> Ran 27 tests, OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Fresh clone tracks 17 files including skills/pr-workflow-report/SKILL.md and 5 fixtures; no gsd-beads state was mutated by this plan"
    verification:
      - kind: other
        ref: "git ls-files | wc -l -> 17; test -f .gsd/capabilities/pr-workflow/skills/pr-workflow-report/SKILL.md; ls tests/fixtures | wc -l -> 5"
        status: pass
      - kind: other
        ref: "git -C gsd-beads-worktree status --porcelain -- .claude-plugin -> empty"
        status: pass
    human_judgment: false

duration: ~15min (continuation from Task 3 checkpoint)
completed: 2026-08-18
status: complete
---

# Phase 15 Plan 02: Ship pr-workflow plugin publicly Summary

**Published `davdittrich/pr-workflow` as a public, independently installable Claude Code plugin — fresh single-commit history, `claude plugin validate . --strict` and the bundle's 27-test suite both green from a fresh HTTPS clone.**

## Performance

- **Duration:** ~15min (this continuation agent; resumed at Task 3's blocking checkpoint)
- **Started:** 2026-08-18 (continuation)
- **Completed:** 2026-08-18
- **Tasks:** 4/4 (Tasks 1-2 completed and committed by the prior agent as `0dc4855` in the staging repo before this continuation started; Tasks 3-4 completed here)
- **Files modified (this worktree):** 1 (this SUMMARY.md — Tasks 1-4 touch only `/tmp/pr-workflow-extract` and GitHub, outside the gsd-beads tree per plan design)

## Accomplishments
- Task 3 checkpoint resolved: operator approved `create-as-planned`.
- `gh repo create davdittrich/pr-workflow --public --source=. --push` run from `/tmp/pr-workflow-extract`: created the repo and pushed commit `0dc48556495839544d1be8d48b68e7c2e52b6d03` to `main`.
- `gh repo view davdittrich/pr-workflow` confirms `visibility=PUBLIC`, `defaultBranchRef.name=main`, `isPrivate=false`.
- Fresh HTTPS clone into `/tmp/pr-workflow-verify` (no SSH key involved) passes `claude plugin validate . --strict` and the bundle's own `unittest` suite (27/27 passing), and tracks exactly 17 files including `.gsd/capabilities/pr-workflow/skills/pr-workflow-report/SKILL.md` and all 5 test fixtures.
- gsd-beads' `.claude-plugin/marketplace.json` and the rest of the working tree are untouched by this plan (confirmed via `git status --porcelain`).

## Task Commits

Tasks 1-2 were executed and committed by the prior agent inside the standalone staging repo (not the gsd-beads worktree):

1. **Task 1+2: Build plugin-tree wrapper, write README/CI, validate, fresh-init commit** - `0dc4855` (feat, in `/tmp/pr-workflow-extract`, a separate git repo — not part of gsd-beads history)

Task 3 (checkpoint:decision) required no code commit — it was a human approval gate, resolved with `create-as-planned`.

Task 4 (this continuation) created no gsd-beads commits; its only output is the GitHub push (`gh repo create ... --push`) and the throwaway verify clone.

**Plan metadata:** this SUMMARY.md commit (docs: complete plan)

## Files Created/Modified
- `/tmp/pr-workflow-extract/` (17 files) - staging repo, pushed as `davdittrich/pr-workflow`'s sole commit
- `/tmp/pr-workflow-verify/` - throwaway fresh HTTPS clone used only for the post-push verification gate; not committed anywhere
- `.planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-02-SUMMARY.md` - this file (gsd-beads-tracked)

## Decisions Made
- **Task 3 checkpoint resolved as `create-as-planned`** — operator approved creating `davdittrich/pr-workflow` public and pushing the staged commit exactly as Task 3 described, no repo-name change.
- **Documented, not "fixed", the `-t .` unittest-discover verify-command defect**: the plan's literal verify command (`python3 -m unittest discover -s .gsd/capabilities/pr-workflow/tests -t .`) fails with `ImportError: Start directory is not importable` on this machine's Python 3.14.7, because the hyphen in the `pr-workflow` path segment is not a valid Python package-name character when the loader tries to import the full dotted path from repo root. This is the same class of pre-existing verify-command defect STATE.md's Decisions log already records for Phase 13/14 (`the -t . unittest-discover verify-command defect... inherited from Phase 13's plan-doc shape`). It is a verify-wording defect, not a code defect: `python3 -m unittest discover -s tests` run with cwd = the bundle root (`.gsd/capabilities/pr-workflow/`) passes cleanly — 27/27 tests OK — both in `/tmp/pr-workflow-extract` and in the fresh `/tmp/pr-workflow-verify` clone. No plan or code file was altered to work around this; the actual behavioral proof (test suite passing on the round-tripped repo) was obtained via the equivalent working invocation instead.

## Deviations from Plan

### Auto-fixed Issues

None — no code or plan file was modified. The item above is a documented verify-command wording defect, not an auto-fix; the plan's <verify> block text is inaccurate on this Python version but no plan edit was made per scope (this continuation's job was execution, not plan revision).

---

**Total deviations:** 0 auto-fixed. One pre-existing verify-command wording defect documented (see Decisions), matching an already-logged pattern from Phase 13/14.
**Impact on plan:** None on outcome — every acceptance criterion this defect nominally covers (bundle test suite passing post-round-trip) was independently proven via the equivalent working invocation.

## Issues Encountered
- `python3 -m unittest discover -s .gsd/capabilities/pr-workflow/tests -t .` (the literal Task 4 `<verify>` command) does not run on this machine's Python 3.14.7 due to the hyphenated `pr-workflow` directory name being an invalid Python module-path component under dotted-import resolution from repo root. Resolved by running the discovery from inside the bundle directory (`cd .gsd/capabilities/pr-workflow && python3 -m unittest discover -s tests`), which is functionally equivalent and is the exact form Task 1's `<read_first>`/CI step implies. All 27 tests pass in both the staging tree and the fresh clone.

## Premise Correction (restated from plan)

15-CONTEXT.md described `pr-workflow` as a subdirectory of gsd-beads awaiting extraction. `git ls-files` shows no top-level `pr-workflow/` tree ever existed — Phase 14 built the capability directly at `.gsd/capabilities/pr-workflow/` with `"hooks": []` in its manifest and no `.claude-plugin/plugin.json`. This plan was therefore wrap-then-extract: Task 1 constructed the plugin-tree wrapper before Phase 12's extraction sequence could run. D-00's intent is unchanged and fully honored — the published repo has fresh single-commit history with nothing imported from gsd-beads.

## User Setup Required

None - no external service configuration required. (`gh` was already authenticated as `davdittrich` with `repo` scope, verified via `gh auth status` before repo creation.)

## Next Phase Readiness
- `davdittrich/pr-workflow` exists, is public, on `main`, one commit, and passes both `claude plugin validate . --strict` and its own test suite from a fresh clone — D-10's validate half is done; the marketplace round-trip (install/uninstall) is deferred to Plan 03 as designed.
- Plan 03 can now write `.claude-plugin/marketplace.json`'s `pr-workflow` entry against the confirmed URL `https://github.com/davdittrich/pr-workflow.git`.
- No blockers for Plan 03, 04, or 05.

---
*Phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly*
*Completed: 2026-08-18*
