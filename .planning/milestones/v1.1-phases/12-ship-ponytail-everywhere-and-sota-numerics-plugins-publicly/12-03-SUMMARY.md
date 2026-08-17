---
phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
plan: 03
subsystem: infra
tags: [claude-plugin-marketplace, github-source, plugin-install-uninstall, round-trip-verification]

# Dependency graph
requires:
  - phase: 12-01
    provides: davdittrich/ponytail-everywhere, public, verified from fresh clone
  - phase: 12-02
    provides: davdittrich/sota-numerics, public, verified from fresh clone
provides:
  - gsd-beads/.claude-plugin/marketplace.json with both plugins pointing at their standalone repos via github source objects
  - D-10's marketplace add -> install -> uninstall round trip, proven against a scratch marketplace before commit
affects: [12-04]

# Actuals (#2632)
actuals:
  tokens: 4500
  tasks: 2
  commits: 1

# Tech tracking
tech-stack:
  added: []
  patterns: ["scratch-marketplace round trip: derive a throwaway two-entry manifest from the edited file, register it under a distinct name, install/uninstall both plugins from it, then delete it and re-verify the live marketplace/install are untouched — proves the change before it is committed"]

key-files:
  created: []
  modified:
    - .claude-plugin/marketplace.json

key-decisions:
  - "ponytail-everywhere and sota-numerics repo names: davdittrich/ponytail-everywhere and davdittrich/sota-numerics, matching the names approved at 12-01/12-02 checkpoints (no deviation)"
  - "Rule 3 auto-fix: claude plugin install clones via a hardcoded git@github.com: SSH URL; this machine authenticates to GitHub only via gh's HTTPS token (no SSH key registered), so the first install attempt failed with 'Permission denied (publickey)'. Fixed by exporting GIT_CONFIG_COUNT/GIT_CONFIG_KEY_0/GIT_CONFIG_VALUE_0 as process-scoped environment variables (git.https://github.com/.insteadOf -> git@github.com:) for the two install invocations only — no git config file was read or written, satisfying the harness's 'never update git config' constraint while unblocking a public, credential-free HTTPS clone."

patterns-established:
  - "When claude plugin install fails against a github-source entry with an SSH publickey error on a machine that only has HTTPS/gh auth, use GIT_CONFIG_COUNT/GIT_CONFIG_KEY_n/GIT_CONFIG_VALUE_n env vars scoped to that single command to rewrite the SSH URL to HTTPS, rather than editing any gitconfig file."

requirements-completed: [D-02, D-10]

coverage:
  - id: D1
    description: "Both non-beads marketplace entries are github source objects naming their own public repos, unpinned; beads-lifecycle keeps its Directory source unchanged"
    requirement: "D-02"
    verification:
      - kind: integration
        ref: "claude plugin validate . --strict -> Validation passed; Python structural assertion -> marketplace shape OK"
        status: pass
      - kind: integration
        ref: "git diff -- .claude-plugin/marketplace.json touches only the two source blocks"
        status: pass
    human_judgment: false
  - id: D2
    description: "Both plugins install from their real public repos through a github-source marketplace entry and uninstall cleanly, without disturbing the live gsd-beads marketplace or beads-lifecycle@gsd-beads install"
    requirement: "D-10"
    verification:
      - kind: integration
        ref: "claude plugin install ponytail-everywhere@gsd-beads-verify / sota-numerics@gsd-beads-verify -> both succeeded, both appeared in claude plugin list sourced from gsd-beads-verify"
        status: pass
      - kind: integration
        ref: "claude plugin uninstall for both -> claude plugin list shows 0 matches for either @gsd-beads-verify entry afterward"
        status: pass
      - kind: integration
        ref: "post-cleanup: claude plugin marketplace list has no gsd-beads-verify entry, /tmp/gsd-beads-mkt-verify does not exist, gsd-beads marketplace and beads-lifecycle@gsd-beads install both still present"
        status: pass
  - id: D3
    description: "marketplace.json change is committed locally, not pushed, with no AI attribution"
    verification:
      - kind: integration
        ref: "git log -1 --format=%B -- .claude-plugin/marketplace.json | grep -ci 'co-authored-by|anthropic' -> 0; git log origin/main..HEAD --oneline includes commit cb4d49d"
        status: pass
    human_judgment: false

duration: ~20min
completed: 2026-08-17
status: complete
---

# Phase 12 Plan 03: Repoint Marketplace and Prove the Round Trip Summary

**Rewrote both non-beads marketplace entries as `{source: github, repo: owner/repo}` objects pointing at `davdittrich/ponytail-everywhere` and `davdittrich/sota-numerics`, then proved the full `marketplace add -> install -> uninstall` round trip against a scratch marketplace before committing — closing D-10's remaining half.**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2/2
- **Files modified:** 1 (`.claude-plugin/marketplace.json`)

## Accomplishments

- Task 1: edited the `ponytail-everywhere` and `sota-numerics` entries' `source` field from a relative-path string to `{"source": "github", "repo": "davdittrich/<name>"}`, leaving `name`, `description`, the `beads-lifecycle` entry, and the top-level manifest fields byte-identical. `claude plugin validate . --strict` passed; the structural Python assertion confirmed three entries by name, `beads-lifecycle` still `"./"`, both others github objects with no `ref`/`sha`; the diff touched only the two `source` blocks.
- Task 2: captured the starting `claude plugin marketplace list` / `claude plugin list` state, built `/tmp/gsd-beads-mkt-verify/.claude-plugin/marketplace.json` programmatically (top-level `name` set to `gsd-beads-verify`, kept only the two github-source entries), registered it as a marketplace, then ran the full round trip for both plugins: install (from `plugin@gsd-beads-verify`) -> confirm listed, sourced from `gsd-beads-verify` -> uninstall -> confirm gone. Removed the scratch marketplace registration and directory, then re-confirmed the live `gsd-beads` marketplace and `beads-lifecycle@gsd-beads` install were both untouched. Committed the marketplace.json change alone (commit `cb4d49d`), not pushed.

## Before/After State Captures

**`claude plugin marketplace list` (before, relevant entries only):**
```
❯ gsd-beads
    Source: Directory (/home/dd/projects/gsd-beads)
```
(13 other pre-existing marketplaces present and unrelated to this plan, all unchanged throughout.)

**`claude plugin list` (before, relevant entries only):**
```
❯ beads-lifecycle@gsd-beads
    Version: 1.2.0 / Scope: user / Status: enabled
❯ ponytail-everywhere@gsd-beads
    Version: 0.1.0 / Scope: user / Status: enabled
```
Note: `ponytail-everywhere@gsd-beads` (installed earlier from the old `./ponytail-everywhere` Directory-relative source, pre-dating this plan) was present at the start and was never touched by this task — the round trip installed/uninstalled a *different* plugin identity, `ponytail-everywhere@gsd-beads-verify`, from the distinct scratch marketplace.

**Install output:**
```
Installing plugin "ponytail-everywhere@gsd-beads-verify"...
✔ Successfully installed plugin: ponytail-everywhere@gsd-beads-verify (scope: user)

Installing plugin "sota-numerics@gsd-beads-verify"...
✔ Successfully installed plugin: sota-numerics@gsd-beads-verify (scope: user)
```
Both then confirmed in `claude plugin list` as `Version: 0.1.0 / Scope: user / Status: enabled`, sourced from `gsd-beads-verify`.

**Uninstall output:**
```
✔ Successfully uninstalled plugin: ponytail-everywhere (scope: user)
✔ Successfully uninstalled plugin: sota-numerics (scope: user)
```
`claude plugin list | grep -cE 'ponytail-everywhere@gsd-beads-verify|sota-numerics@gsd-beads-verify'` returned 0 matches afterward.

**After cleanup:**
- `claude plugin marketplace list` has no `gsd-beads-verify` entry; `/tmp/gsd-beads-mkt-verify` does not exist.
- `claude plugin marketplace list` still contains `gsd-beads` (Directory source, unchanged); `claude plugin list` still contains `beads-lifecycle@gsd-beads` (enabled, unchanged).

**Commit SHA:** `cb4d49d89f2cd4b501201c4160854ddcefb5f19a` — `feat(12-03): repoint ponytail-everywhere and sota-numerics to their own repos`. `git log origin/main..HEAD --oneline` confirms it is local-only (not pushed); Plan 04 pushes it.

## Task Commits

1. **Task 1: Switch the two marketplace entries to github sources** — not committed separately (Task 2 commits the full edit, per plan instruction "Do not commit yet — Task 2 commits")
2. **Task 2: Prove the round trip against a scratch marketplace, then commit** — `cb4d49d` — `feat(12-03): repoint ponytail-everywhere and sota-numerics to their own repos`

**Plan metadata:** (this commit) `docs(12-03): complete repoint-marketplace-and-prove-round-trip plan`

## Files Created/Modified

- `.claude-plugin/marketplace.json` — the `source` value of the `ponytail-everywhere` entry and the `sota-numerics` entry, each replaced by a `{source: github, repo: owner/repo}` object naming the plan 01/02 repos. No other field changed.

## Decisions Made

- Repo names used: `davdittrich/ponytail-everywhere`, `davdittrich/sota-numerics` — exactly the names approved at the 12-01 and 12-02 checkpoints, no divergence.
- No `ref`/`sha` pin added, per the plan's explicit instruction — matches every other entry this file has carried and lets the unpinned github source resolve each pushed commit as the version (D-05).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] `claude plugin install` failed with SSH publickey error; worked around via process-scoped git URL rewrite**
- **Found during:** Task 2, first `claude plugin install ponytail-everywhere@gsd-beads-verify` attempt
- **Issue:** The install command clones the github-source repo using a hardcoded `git@github.com:owner/repo` SSH URL. This machine's GitHub auth is HTTPS-only via `gh` (confirmed: `gh auth status` reports `Git operations protocol: https`); no SSH key is registered with GitHub for this account, so the clone failed with `Permission denied (publickey)`.
- **Fix:** Set `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.https://github.com/.insteadOf" GIT_CONFIG_VALUE_0="git@github.com:"` as environment variables scoped only to the two `claude plugin install` invocations. This is a git-native mechanism for supplying config values via the process environment — it does not read or write any `.gitconfig` file, so it does not violate the harness's "never update git config" constraint. Both repos are public, so the HTTPS clone required no credentials.
- **Files modified:** none (environment-scoped, not a file change)
- **Commit:** N/A — no file changed by this fix; the workaround applied only to the two install command invocations in this session's shell.

Beyond this, no other deviations. Both tasks executed exactly as written.

## Issues Encountered

The SSH-vs-HTTPS auth gate above was the only issue; resolved without user input per Rule 3 (auto-fix blocking issue — a git protocol mismatch preventing task completion, not a credential the user needed to supply).

## User Setup Required

None. If a future environment also lacks a GitHub SSH key, the same `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_0`/`GIT_CONFIG_VALUE_0` workaround (or registering an SSH key with `gh ssh-key add`) unblocks `claude plugin install` against github-source entries.

## Next Phase Readiness

- `.claude-plugin/marketplace.json` now carries two github-object sources and one unchanged Directory source; committed locally as `cb4d49d`, not pushed.
- D-02 satisfied: `gsd-beads` still hosts the marketplace, `beads-lifecycle` keeps its local Directory source, the other two entries are git-hosted pointing at their new standalone repos.
- D-10 fully satisfied for both plugins: `validate --strict` clean on the pushed repos (12-01/12-02) plus this plan's real `marketplace add -> install -> uninstall` round trip.
- Plan 04 can now push `cb4d49d` together with the removal of the `ponytail-everywhere/` and `sota-numerics/` subdirectories, so the public manifest never ships alongside stale local copies.

---
*Phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly*
*Completed: 2026-08-17*

## Self-Check: PASSED

- FOUND: `.claude-plugin/marketplace.json`
- FOUND: commit `cb4d49d` in gsd-beads git history
- FOUND: `.planning/phases/12-.../12-03-SUMMARY.md`
