---
phase: quick-260821-rcp
plan: 01
subsystem: diagnostics
tags: [gsd-core, codex, installer, model-overrides, issue-3715]
status: complete
requires: []
provides:
  - Exact-SHA reproduction evidence for open-gsd/gsd-core#3715
affects: [gsd-core-installer, codex-model-routing]
actuals:
  tokens: 2207
  tasks: 1
  commits: 0
tech-stack:
  added: []
  patterns: [isolated HOME installer reproduction]
key-files:
  created:
    - .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md
  modified: []
key-decisions:
  - "Treat project-local A and B as separate negative observations and the HOME-ancestor configuration only as a harness control."
patterns-established: []
requirements-completed: []
coverage:
  - id: D1
    description: "Exact-SHA isolated reproduction distinguishes the overwrite claim from the maintainer no-model-line diagnosis."
    verification:
      - kind: integration
        ref: "Three exact installer runs plus the automated command in Verification"
        status: pass
    human_judgment: false
---

# Quick 260821-rcp: gsd-core Issue 3715 Reproduction Summary

**At gsd-core `adb46cdd85add7928977a5664793267efdfca83f`, neither descendant project configuration reached the global Codex target; the HOME-ancestor control did.**

## Environment

- **Date:** 2026-08-21
- **Completed:** 2026-08-21T17:51:05Z
- **Platform:** Linux 7.1.8-arch1-3 x86_64
- **Node.js:** v26.7.0
- **Git:** 2.55.0
- **Fixture root:** `/tmp/gsd-3715.kfB1Ij` (mode 0700)
- **Disposable HOME:** `/tmp/gsd-3715.kfB1Ij/home`
- **Checked-out gsd-core SHA:** `adb46cdd85add7928977a5664793267efdfca83f` (asserted before every observation)
- **Package contract:** version 1.11.0, Node.js `>=24.0.0`, `gsd-core` bin `bin/install.js`

## Assertion Under Test

**ASSERTION UNDER TEST, not an observed fact:** open-gsd/gsd-core#3715 reports that installing globally from project A bakes `gpt-5.6-sol` into the shared planner TOML, then installing from project B overwrites it with `gpt-5.6-luna`.

The separate maintainer diagnosis in comment 5372430413 says neither ordinary project-local configuration is discovered for a global Codex installation, so neither run emits a `model =` line; placing the override in `$HOME/.planning/config.json` does emit one.

## Exact Procedure

The public commit was fetched into the disposable fixture and detached with this blocking identity assertion:

```bash
git -C /tmp/gsd-3715.kfB1Ij/gsd-core fetch --depth=1 origin adb46cdd85add7928977a5664793267efdfca83f
git -C /tmp/gsd-3715.kfB1Ij/gsd-core checkout --detach FETCH_HEAD
test "$(git -C /tmp/gsd-3715.kfB1Ij/gsd-core rev-parse HEAD)" = adb46cdd85add7928977a5664793267efdfca83f
```

Every observation invoked the same checked-out installer against the same disposable global target, with the real `CODEX_HOME` forcibly removed from the child environment:

```bash
env -u CODEX_HOME HOME=/tmp/gsd-3715.kfB1Ij/home \
  node /tmp/gsd-3715.kfB1Ij/gsd-core/bin/install.js --codex --global
```

The command ran first from `home/projA`, then `home/projB`. The positive control ran after adding `home/.planning/config.json`. Each resulting planner TOML was copied before the next run.

## Results

| Observation | Config location and requested override | Preserved planner TOML | Result | SHA-256 |
|---|---|---|---|---|
| Project A negative | `home/projA/.planning/config.json`: `gpt-5.6-sol` | `evidence/project-a-gsd-planner.toml` | No line matching `^model[[:space:]]*=` | `48645902a265d8c52210e0f9a54b4cd1c95fd83c1a14bf8827934edec2161c4e` |
| Project B negative | `home/projB/.planning/config.json`: `gpt-5.6-luna` | `evidence/project-b-gsd-planner.toml` | No line matching `^model[[:space:]]*=`; it did not bake or overwrite A | `48645902a265d8c52210e0f9a54b4cd1c95fd83c1a14bf8827934edec2161c4e` |
| Positive harness control | `home/.planning/config.json`: `gpt-5.6-sol` | `evidence/positive-control-gsd-planner.toml` | Exactly one `model = "gpt-5.6-sol"` line | `59530c1566d7cec72db3cc872bd1a34ba2d653602fd59ec575def2869d93fdde` |

The A and B evidence files are independent even though their byte hashes are identical. The positive control proves that this pinned installer and fixture can emit a model override when configuration discovery can reach it; it is not evidence that cross-project overwrite occurred.

## Verdict

1. **Original issue overwrite symptom: NOT REPRODUCED.** Project A did not bake `gpt-5.6-sol`; project B did not bake `gpt-5.6-luna` or overwrite an A model line.
2. **Maintainer comment 5372430413: REPRODUCED.** Both descendant project-local installs omitted the model line, while the `$HOME/.planning/config.json` ancestor control emitted exactly `model = "gpt-5.6-sol"`.

The evidence supports this narrow diagnosis: the global target is `$HOME/.codex`, and configuration discovery searches that target's ancestors. Ordinary project directories are descendants elsewhere under HOME, so their `.planning/config.json` files are not incorporated; `$HOME/.planning/config.json` is an ancestor-visible control.

## Beads Disposition

- Added a concise evidence comment to `gsd-beads-6kl` containing both verdicts and this SUMMARY path.
- Closed `gsd-beads-6kl` with reason: `Exact-SHA reproduction recorded in 260821-rcp-SUMMARY.md`.

## Safety and Integrity

- The real `/home/dd/.codex/agents/gsd-planner.toml` existed before and after with the same SHA-256: `e99d04d45f7f8585d6cba1e5e303b7a14efff8d1fe6edec83b17e5b514bea160`.
- Every installer process used `env -u CODEX_HOME HOME=/tmp/gsd-3715.kfB1Ij/home`; the real HOME global Codex installation was unchanged.
- Repository porcelain was captured before the run. After the run it was byte-identical at the top level; only this already-untracked quick-task directory gained the requested SUMMARY artifact.
- Existing unrelated changes in `.gsd-capabilities.json`, `.planning/STATE-ARCHIVE.md`, `CLAUDE.md`, `BEADS`, `docs/agents/`, and `ponytail-everywhere/` were left untouched.
- No gsd-core or gsd-beads source patch was attempted or authorized. No dependency was installed. No commit, push, or Dolt remote sync was performed.

## Execution Note

The clean Git tree does not contain the gitignored runtime build output required by `bin/install.js`; the first direct attempt failed on missing `gsd-core/bin/lib/shell-command-projection.cjs`. To execute the pinned installer without installing packages or changing source, the exact SHA's `src/*.cts` files were compiled inside the disposable checkout using already-present TypeScript 7.0.2 and `@types/node` 26.1.2. The checkout remained at the asserted SHA with tracked files clean. This is a Rule 3 blocking-environment deviation from the plan's statement that the Git checkout itself was fully bundled, not a product patch or alternate installer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Generated absent ignored runtime build artifacts**

- **Found during:** Task 1, first project-A installer invocation
- **Issue:** The exact Git tree omitted build-at-publish `.cjs` artifacts required by `bin/install.js`.
- **Fix:** Compiled exact-SHA TypeScript sources inside the disposable checkout with an already-installed compiler; installed no package and changed no tracked file.
- **Verification:** Installer completed for all three runs; `git rev-parse HEAD` stayed exact and `git status --short --untracked-files=no` stayed empty.
- **Committed in:** None (diagnosis-only task)

---

**Total deviations:** 1 auto-fixed blocking fixture issue. No scope expansion.

## Issues Encountered

- The initial clean-tree invocation failed before installation because build-at-publish runtime files are not tracked. Resolved as documented above without touching either real HOME or repository source.

## Verification

```bash
test -f .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md && \
rg -q 'adb46cdd85add7928977a5664793267efdfca83f' .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md && \
rg -q 'gpt-5\.6-sol' .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md && \
rg -q 'gpt-5\.6-luna' .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md && \
rg -qi 'real.*HOME.*unchanged|unchanged.*real.*HOME' .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md
```

## Self-Check: PASSED

- Summary exists and names the exact SHA, both requested models, both separate verdicts, and the unchanged real HOME assertion.
- All three preserved fixture TOMLs exist and satisfy their model-line assertions.
- Exact upstream SHA, real planner hash, and repository baseline assertions passed.
- Task commits: none, as explicitly required for this diagnosis-only quick task.
