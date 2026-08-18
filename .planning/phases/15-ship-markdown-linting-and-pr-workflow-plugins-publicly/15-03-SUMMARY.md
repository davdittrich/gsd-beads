---
phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly
plan: 03
subsystem: infra
tags: [claude-plugin-marketplace, gh-cli, round-trip-verify]

# Dependency graph
requires:
  - phase: 15-01
    provides: public repo davdittrich/markdown-linting, fresh-clone-verified
  - phase: 15-02
    provides: public repo davdittrich/pr-workflow, fresh-clone-verified
provides:
  - .claude-plugin/marketplace.json with markdown-linting and pr-workflow url-type entries appended (commit 2b3d46d, local to this worktree branch, NOT yet on origin/main)
  - proven scratch-marketplace round trip (install/uninstall over HTTPS, no SSH key) for both new plugins
affects: [15-04-gate-re-proof]

actuals:
  tokens: 9000
  tasks: 2
  commits: 1

tech-stack:
  added: []
  patterns:
    - "scratch marketplace round trip: derive a throwaway N-entry manifest programmatically from the edited file, register under a disposable name, install/uninstall, then remove and delete — proves url sources resolve before the change is committed, without touching the live marketplace registration"

key-files:
  created: []
  modified:
    - .claude-plugin/marketplace.json

key-decisions:
  - "Task 3 NOT executed: its <precondition> ('git log origin/main..HEAD shows exactly that one commit') is unmet — origin/main is 79 commits behind local HEAD (origin/main tip is f706179, dated 2026-08-17; local HEAD carries all of phase 12's remainder plus phases 13, 14, and this phase's work). Per the unmet-precondition protocol this halts before Task 3's action (the `git push origin main`) runs at all: pushing now would publish 79 commits of internal phase history to the public repo, not the single marketplace.json change the plan's own precondition, Task 2 verify block, and acceptance criteria all assume. This is a Rule 4-scale decision (architectural/scope impact of what becomes public), not a Rule 1-3 auto-fixable blocker, and preconditions are never auto-approved even under auto-mode."

requirements-completed: []

coverage:
  - id: D1
    description: "marketplace.json carries five entries: beads-lifecycle unchanged Directory source, plus four url-type git sources including the two new ones added by Task 1"
    requirement: "D-00"
    verification:
      - kind: other
        ref: "claude plugin validate . --strict -> Validation passed"
        status: pass
      - kind: other
        ref: "python3 structural-assertion script -> 'marketplace shape OK' (5 entries, beads-lifecycle Directory-source unchanged, 4 url-type entries each with source.source==url, https:// + .git URL matching own plugin name, no ref/sha)"
        status: pass
      - kind: other
        ref: "git diff -- .claude-plugin/marketplace.json | grep -E '^-[^-]' | wc -l -> 0 (purely additive)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Both new plugins install and uninstall cleanly from a scratch marketplace over HTTPS with no SSH key, before the change is committed (D-10 round-trip half, pre-commit proof)"
    requirement: "D-10"
    verification:
      - kind: other
        ref: "claude plugin install markdown-linting@gsd-beads-verify -y -> Successfully installed; claude plugin list shows markdown-linting@gsd-beads-verify enabled; claude plugin uninstall markdown-linting -y -> Successfully uninstalled; no longer listed"
        status: pass
      - kind: other
        ref: "claude plugin install pr-workflow@gsd-beads-verify -y -> Successfully installed; claude plugin list shows pr-workflow@gsd-beads-verify enabled; claude plugin uninstall pr-workflow -y -> Successfully uninstalled; no longer listed"
        status: pass
      - kind: other
        ref: "gh auth status -> 'Git operations protocol: https' (no SSH key path, no GIT_SSH_COMMAND/insteadOf workaround applied)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Scratch marketplace fully cleaned up; live gsd-beads marketplace and beads-lifecycle@gsd-beads install undisturbed throughout"
    verification:
      - kind: other
        ref: "claude plugin marketplace remove gsd-beads-verify -> Successfully removed; rm -rf /tmp/gsd-beads-mkt-verify; test ! -e /tmp/gsd-beads-mkt-verify -> true"
        status: pass
      - kind: other
        ref: "claude plugin marketplace list -> gsd-beads still present, Source: Directory (/home/dd/projects/gsd-beads); claude plugin list -> beads-lifecycle@gsd-beads still enabled v1.2.0"
        status: pass
    human_judgment: false
  - id: D4
    description: "Task 3 (push + real-marketplace round trip + no-tag/no-release proof) NOT run: precondition unmet"
    verification: []
    human_judgment: true
    rationale: "origin/main..HEAD is 79 commits, not the 1 the plan's precondition/verify/acceptance-criteria all require. Pushing would publish 79 commits of unrelated phase history to the public repo. Halted per the unmet-precondition protocol (never auto-approved). Requires an operator decision: rebase/cherry-pick just this commit onto origin/main and push that, or accept publishing the full local history, or defer the push entirely to a separate, deliberate release step."

duration: ~12min
completed: 2026-08-18
status: blocked
---

# Phase 15 Plan 03: Repoint Marketplace at markdown-linting and pr-workflow Summary

**Tasks 1-2 complete and committed (`2b3d46d`): `.claude-plugin/marketplace.json` now carries five entries, and both new plugins round-tripped install/uninstall over HTTPS with no SSH key against a scratch marketplace. Task 3 halted before executing — its stated precondition ("exactly one commit ahead of origin/main") is false; the worktree's HEAD is 79 commits ahead of `origin/main`, so `git push origin main` would publish all of local phases 12(remainder)-15 history, not just this change.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-08-18T21:06:00Z (approx)
- **Completed (through Task 2):** 2026-08-18T21:18:57Z
- **Tasks:** 2/3 (Task 1 + Task 2 committed together per the plan's own instruction — "Do not commit yet: Task 2 commits, after the round trip proves the new entries resolve"; Task 3 blocked)
- **Files modified:** 1 (`.claude-plugin/marketplace.json`)

## Accomplishments

- Appended `markdown-linting` and `pr-workflow` entries to `.claude-plugin/marketplace.json`, each with a `{source: url, url: https://github.com/davdittrich/<name>.git}` source object and a `description` copied verbatim from that capability's `capability.json`. Diff is purely additive (0 removed lines); `beads-lifecycle`'s Directory source and the two pre-existing url-type entries are byte-identical.
- `claude plugin validate . --strict` and a structural Python assertion both pass: 5 entries, correct source shapes, no `ref`/`sha`, descriptions match capability manifests exactly.
- Built a throwaway two-entry scratch marketplace at `/tmp/gsd-beads-mkt-verify/` (registered as `gsd-beads-verify`), programmatically derived from the edited file (not hand-typed) so the `source` objects are copied byte-for-byte.
- Round-tripped both new plugins against the scratch marketplace: `install markdown-linting@gsd-beads-verify` -> appears enabled -> `uninstall markdown-linting` -> gone; identical sequence for `pr-workflow@gsd-beads-verify`. Both installs resolved over HTTPS (`gh auth status` reports `Git operations protocol: https`); no `GIT_SSH_COMMAND`, `insteadOf`, or other SSH workaround was used.
- Cleaned up: removed the `gsd-beads-verify` marketplace registration, deleted `/tmp/gsd-beads-mkt-verify`. Confirmed afterward that the live `gsd-beads` marketplace (Directory source, `/home/dd/projects/gsd-beads`) and `beads-lifecycle@gsd-beads` (v1.2.0, enabled) are undisturbed.
- Committed the marketplace.json change alone (`2b3d46d`), Conventional Commit, no AI attribution, not pushed.
- **Discovered and halted on Task 3's unmet precondition** before running `git push origin main` — see Deviations below.

## Task Commits

1. **Task 1 + Task 2: Append two url-type entries, prove scratch round trip, commit** - `2b3d46d` (feat, `.claude-plugin/marketplace.json` only)

Task 3: not executed (blocked — see below).

## Files Created/Modified

- `.claude-plugin/marketplace.json` - two entries appended (`markdown-linting`, `pr-workflow`), no existing content changed
- `.planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-03-SUMMARY.md` - this file

## Before/After State Captures

**`claude plugin marketplace list` (before, unchanged after — `gsd-beads` entry):**
```
❯ gsd-beads
    Source: Directory (/home/dd/projects/gsd-beads)
```

**`claude plugin list` (before, unchanged after — relevant entries):**
```
❯ beads-lifecycle@gsd-beads
    Version: 1.2.0
    Scope: user
    Status: ✔ enabled
❯ ponytail-everywhere@gsd-beads
    Version: 0.1.0
    Scope: user
    Status: ✔ enabled
❯ sota-numerics@gsd-beads
    Version: 0.1.1
    Scope: user
    Status: ✔ enabled
```

**`gh auth status`:**
```
github.com
  ✓ Logged in to github.com account davdittrich (/home/dd/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_************************************
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
```

**Scratch round trip — markdown-linting:**
```
$ claude plugin marketplace add /tmp/gsd-beads-mkt-verify
✔ Successfully added marketplace: gsd-beads-verify (declared in user settings)

$ claude plugin install markdown-linting@gsd-beads-verify -y
Installing plugin "markdown-linting@gsd-beads-verify"...✔ Successfully installed plugin: markdown-linting@gsd-beads-verify (scope: user)

$ claude plugin list | grep -A3 markdown-linting
❯ markdown-linting@gsd-beads-verify
    Version: 0.1.0
    Scope: user
    Status: ✔ enabled

$ claude plugin uninstall markdown-linting -y
✔ Successfully uninstalled plugin: markdown-linting (scope: user)
```

**Scratch round trip — pr-workflow:**
```
$ claude plugin install pr-workflow@gsd-beads-verify -y
Installing plugin "pr-workflow@gsd-beads-verify"...✔ Successfully installed plugin: pr-workflow@gsd-beads-verify (scope: user)

$ claude plugin list | grep -A3 pr-workflow@gsd-beads-verify
❯ pr-workflow@gsd-beads-verify
    Version: 0.1.0
    Scope: user
    Status: ✔ enabled

$ claude plugin uninstall pr-workflow -y
✔ Successfully uninstalled plugin: pr-workflow (scope: user)
```

**Cleanup:**
```
$ claude plugin marketplace remove gsd-beads-verify
✔ Successfully removed marketplace: gsd-beads-verify
$ rm -rf /tmp/gsd-beads-mkt-verify
```

**Post-cleanup confirmation:** `gsd-beads` marketplace and `beads-lifecycle@gsd-beads` both intact (captures above, re-checked after cleanup — identical).

## Decisions Made

- Followed the plan's explicit instruction to combine Task 1's edit and Task 2's commit into a single commit ("Do not commit yet: Task 2 commits, after the round trip proves the new entries resolve").
- **Halted before Task 3's action.** Task 3 carries `<precondition>Task 2 committed, git log origin/main..HEAD shows exactly that one commit, and the working tree is clean apart from files this phase does not own.</precondition>`. Checked: working tree is clean (met). `git log origin/main..HEAD --oneline | wc -l` returns **79**, not 1 (unmet) — `origin/main`'s tip is `f706179` (2026-08-17T21:52:54+02:00, the SSH-shorthand fix commit the plan itself cites), while local HEAD (`2b3d46d`) carries the remainder of phase 12, all of phases 13 and 14, and this phase's work on top of it. Per the executor protocol, an unmet `<precondition>` on an `auto` task is never auto-approved (even in auto-mode) and must halt with a `checkpoint:human-verify` rather than proceed or auto-fix — this is exactly that case, not a Rule 1-3 blocking-issue auto-fix, because "which 79 commits become public and when" is an operator-scale decision this executor cannot make unilaterally.

## Deviations from Plan

### Halted — Precondition Not Met (not an auto-fixable deviation)

**1. Task 3's precondition is false: `origin/main..HEAD` is 79 commits, not 1**

- **Found during:** Pre-Task-3 precondition check, before running any of Task 3's `<action>` steps (before `git push origin main`).
- **Issue:** Task 3's action begins "Push the commit to `origin main` with a plain push." The plan's own Task 2 `<verify>` block (`git log origin/main..HEAD --oneline | wc -l | grep -qx 1`) and Task 3's `<precondition>` both assert exactly one commit sits ahead of `origin/main` at this point — i.e., that this plan's single marketplace.json commit is the only thing about to be pushed. That assumption does not hold in this environment: `origin/main` (the real `davdittrich/gsd-beads` GitHub repo) is still at commit `f706179`, dated 2026-08-17 — the exact SSH-shorthand-fix commit the plan cites as historical context for why `url`-type sources are mandatory. Local `main` (and this worktree's branch, forked from it) has since accumulated 78 more commits: the remainder of Phase 12, all of Phase 13 (markdown-linting capability dogfood), all of Phase 14 (pr-workflow capability dogfood), and this phase's own prior work (15-01, 15-02, and phase-tracking updates) — none of it pushed to the public repo yet.
- **Why this blocks rather than auto-fixes:** A plain `git push origin main` right now would publish all 79 commits to the public repo in one push, not just this plan's single change. That is a materially different, much larger action than what the plan describes, authorizes, or reasons about in its `<reversibility>` rating (which explicitly scoped the risk to "this adds no new irreversible exposure" on the premise that only the two already-public plugin repos are newly referenced — it did not evaluate exposing 78 unrelated internal-development commits). Deciding whether to (a) push everything, (b) cherry-pick/rebase just this commit onto a fresh branch off `origin/main` and push only that, or (c) defer the push to a separate deliberate release step is an operator-scale, Rule-4-class decision, not one this executor can resolve via Rules 1-3. Per the executor protocol's precondition-check step, an unmet `<precondition>` is never auto-approved even under auto-mode — it must halt with a `checkpoint:human-verify` and cannot be partial-committed around.
- **Files modified:** None as a result of this finding — no push was attempted, no rebase or cherry-pick was performed.
- **State left behind:** `.claude-plugin/marketplace.json`'s edit is committed locally (`2b3d46d`) but NOT pushed. `git log origin/main..HEAD --oneline` still shows 79 commits (unchanged by this halt). No tag or release was touched (`git tag --list` unchanged at 3 tags; not queried against `gh release list` since no push occurred).

---

**Total deviations:** 0 auto-fixed. 1 halt (unmet precondition, Rule-4-class, requires operator decision before Task 3 can run).
**Impact on plan:** Tasks 1-2 fully discharge D-10's pre-commit round-trip proof and the structural/additive-diff proof for both new entries. Task 3 (the push-and-re-prove-against-the-real-marketplace half of D-10, plus the D-02 no-tag/no-release confirmation) is not yet done. ROADMAP success criterion 2 is proven on the scratch manifest but not yet in its "final form" (resolved from the manifest a stranger actually fetches from `davdittrich/gsd-beads`) until an operator resolves the push-scope decision and Task 3 runs.

## Issues Encountered

- See "Halted — Precondition Not Met" above. This is the only issue; no other deviations occurred.

## User Setup Required

**Operator decision needed before Task 3 can proceed** (see CHECKPOINT below). No environment/credential setup is needed — `gh auth status` already confirms an authenticated HTTPS session with `repo` and `workflow` scopes.

## Next Phase Readiness

- Plan 04 (gate re-proof) depends on Task 3's real-marketplace round trip per this plan's own `<objective>` ("the precondition Plan 04's gate re-proof depends on"). Plan 04 is **not** unblocked until Task 3 completes.
- Once the operator resolves the push-scope decision and Task 3 runs (push, `claude plugin marketplace update gsd-beads`, real-marketplace round trip, no-tag/no-release confirmation), this plan is complete and Plan 04 can proceed.
- Note for whoever resolves Task 3: the live `gsd-beads` marketplace registration is a **Directory** source pointing at `/home/dd/projects/gsd-beads` (the primary checkout, not this worktree, and not a GitHub-hosted source). `claude plugin marketplace update gsd-beads` re-reads that local path's files — it will not pick up a push to `origin/main` unless that primary checkout's `main` branch is also fast-forwarded to the pushed commit. Task 3 as written assumes marketplace refresh alone suffices; on this machine an explicit sync of the primary checkout (e.g. `git -C /home/dd/projects/gsd-beads pull`) is also required for the "real, refreshed marketplace" round trip to actually exercise the new entries, since this worktree-isolated agent is not permitted to alter the primary checkout directly.

## Known Stubs

None.

## Self-Check: PASSED

- `.claude-plugin/marketplace.json` — FOUND, contains 5 plugin entries (verified via structural Python assertion, printed `marketplace shape OK`).
- Commit `2b3d46d` — FOUND: `git log --oneline --all | grep 2b3d46d` matches `2b3d46d feat(15-03): repoint marketplace at markdown-linting and pr-workflow repos`.
- `/tmp/gsd-beads-mkt-verify` — confirmed absent (cleanup verified).
- `gsd-beads-verify` marketplace registration — confirmed absent from `claude plugin marketplace list`.
- `gsd-beads` marketplace and `beads-lifecycle@gsd-beads` — confirmed still present and enabled.

---
*Phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly*
*Plan: 03*
*Completed: 2026-08-18 (Tasks 1-2 only; Task 3 blocked, see checkpoint)*
