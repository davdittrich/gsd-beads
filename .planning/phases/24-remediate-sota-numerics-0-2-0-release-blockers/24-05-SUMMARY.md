---
phase: 24-remediate-sota-numerics-0-2-0-release-blockers
plan: 05
subsystem: infra
tags: [security, elevation-of-privilege, gsd-tools-resolution, plan-gate, hooks]

# Dependency graph
requires:
  - phase: 24-04
    provides: bounded diagnostics (D-07, D-08), Corpus A/B baseline (1,0,0,1,0,0
      across phases 19-24; 125/125 Python tests) this plan's own regression sweep
      re-confirms unchanged, since neither task here touches check-alternatives.py.
provides:
  - "hooks/gsd-tools.sh's provider-resolution first rung anchored to the sourced
    file's own location (CLAUDE_PLUGIN_ROOT when host-set, else BASH_SOURCE[0]'s
    own directory) instead of `git rev-parse --show-toplevel` at the caller's
    working directory -- closes D-13."
  - "capability.json's plan:post gate command with its enclosing-repository rung
    deleted, leaving project-relative then GSD_HOME-global -- closes D-14."
  - "Two new regression cases (test-session-start.sh case6, test-gate-script-resolution.sh
    case6) pinning that a hostile/enclosing repository at the working directory
    never supplies the node entry point or the checker script, plus a case pinning
    that an unresolvable provider still exits 127 unchanged (T-24-21)."
  - "README.md, NOTES.md and the hooks' own comments describing the resolution
    order the code now performs, not the one it used to (D-13, D-14 doc claims)."
affects: []

# Actuals (#2632)
actuals:
  tokens: 4003
  tasks: 3
  commits: 3
  commits_note: >
    Plan's code/test/doc edits land in a DIFFERENT repository from this
    SUMMARY (target_repo per 24-05-PLAN.md frontmatter): sota-numerics
    worktree at /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013,
    branch feat/extended-sota-definition. 3 commits there: 55c44e7 (Task 1,
    fix), 6b61d4b (Task 2, fix), f405303 (Task 3, docs -- folds in two
    Rule-1 doc-truth auto-fixes discovered running the full suite after
    Tasks 1-2). Measured: `git rev-list --count 1cb14d9..HEAD` = 3 in the
    target repo (1cb14d9 is this plan's `depends_on: [24-04]` base, its
    last commit). 130 insertions / 25 deletions across 7 files, 16,013
    diff chars (~4,003 estimateTokens), well under the plan's 58,000-token
    low-confidence estimate.
    THIS (gsd-beads) repo carries only STATE.md/ROADMAP.md/REQUIREMENTS.md/
    this SUMMARY, docs-only, in the final target-repo-external commit below.

tech-stack:
  patterns-established:
    - "Anchor a sourced shell function's own resolution to the sourced file's
      location (CLAUDE_PLUGIN_ROOT when a host sets it, BASH_SOURCE[0]'s own
      directory otherwise) rather than to any git-derived property of the
      caller's working directory -- the working directory is attacker-influenced
      input in a SessionStart/SubagentStart hook context, the sourced file's own
      path is not."
    - "A command string executed via `sh -c` has no file of its own to anchor
      to, so the only available fix for the identical class of defect there is
      deletion of the caller-cwd-derived rung, not anchoring -- confirmed live:
      case5's monorepo-precedence assertion was already fully satisfied by the
      project-relative rung alone, so deleting the middle rung cost no coverage."

key-files:
  created: []
  modified:
    - hooks/gsd-tools.sh (target repo)
    - .gsd/capabilities/sota-numerics/capability.json (target repo)
    - .gsd/capabilities/sota-numerics/NOTES.md (target repo)
    - tests/test-gate-script-resolution.sh (target repo)
    - tests/test-session-start.sh (target repo)
    - tests/test-capability-auto-install.sh (target repo, Rule-1 auto-fix)
    - README.md (target repo)

key-decisions:
  - "Anchored hooks/gsd-tools.sh's first rung to CLAUDE_PLUGIN_ROOT (preferred,
    host-set) falling back to BASH_SOURCE[0]'s own directory, matching the exact
    convention session-start.sh already computes at its own line 4 -- the
    plan's own decided alternative (Anchor sourced file's own location), not
    the rejected 'anchor to host variable alone' (loses non-host invocation)
    or 'keep the rung and harden it with safe.directory' (keeps a
    working-directory-derived path in the resolution at all)."
  - "Deleted the gate command's enclosing-repository rung outright rather than
    anchoring it: a `sh -c` command string has no file of its own to derive a
    location from, so the plan's own Internal design alternative applies --
    deletion is the only available instance of 'not the caller's working
    directory' there, and the project-relative rung already reaches the copy
    gsd-core's dispatch places the gate at."
  - "Wrote both NOTES.md's and hooks/gsd-tools.sh's own explanatory prose about
    the removed rung WITHOUT the literal string 'show-toplevel', matching the
    plan's own ticket-description style -- Task 3's verify command greps for
    that literal string across README.md/NOTES.md/hooks//capability.json and
    fails on any hit, tense notwithstanding; a first draft that quoted the
    removed command literally would have tripped its own gate."

requirements-completed: [D-13, D-14, D-17]

coverage:
  - id: D1
    description: "A session started with the working directory inside a hostile
      repository does not run that repository's node entry point (D-13).
      Pinned live: a real git repository at cwd carrying its own
      gsd-core/bin/gsd-tools.cjs is proven never to run, and legitimate
      resolution via PATH still succeeds despite the hostile cwd."
    requirement: D-13
    verification:
      - kind: unit
        ref: "tests/test-session-start.sh case6 (target repo), commit 55c44e7"
        status: pass
      human_judgment: false
  - id: D2
    description: "The gate does not consult a path derived from an enclosing
      repository of the caller's working directory (D-14). Pinned live: a
      repository enclosing the working directory, carrying a hostile checker
      copy at the same relative path, is proven never executed; the gate
      falls straight through to the global copy instead."
    requirement: D-14
    verification:
      - kind: unit
        ref: "tests/test-gate-script-resolution.sh case6 (target repo), confirmed
          RED against the unedited command before the fix, GREEN after --
          commit 6b61d4b"
        status: pass
      human_judgment: false
  - id: D3
    description: "No file in the shipped bundle resolves an executable path
      from the caller's working directory through an enclosing-repository
      lookup, and an unresolvable provider still exits 127 unchanged (no rung
      silently disabled, T-24-21)."
    requirement: D-14
    verification:
      - kind: unit
        ref: "tests/test-session-start.sh case7 (target repo); all three shell
          suites (test-session-start.sh, test-gate-script-resolution.sh,
          test-capability-auto-install.sh) pass -- 41 case/pass lines total
          across the three, 0 FAIL"
        status: pass
      - kind: other
        ref: "grep -rn 'show-toplevel' README.md NOTES.md hooks/ capability.json
          -- count 0 (this plan's Task 3 verify command, run after all three
          commits)"
        status: pass
      human_judgment: false
  - id: D4
    description: "README and NOTES describe the resolution order the code now
      performs, not the one it used to."
    requirement: D-13
    verification:
      - kind: other
        ref: "README.md lines 68 and 222 (installer provider resolution order;
          Git-not-needed claim) and NOTES.md section 3 rewritten to match the
          two-rung code in both files; see 'Doc-truth sweep' section below for
          the full before/after"
        status: pass
      human_judgment: false
  - id: D5
    description: "D-17: live install-mirror hash sidecar
      (~/.gsd/capability-auto-install-sota-numerics.hash) independently
      re-measured before this plan's edits and after, using the same
      absolute-PLUGIN_ROOT-rooted method 24-01/24-03/24-04 verified."
    requirement: D-17
    verification:
      - kind: other
        ref: "This SUMMARY's 'D-17 hash sidecar' section, below"
        status: pass
      human_judgment: false

duration: ~70min
completed: 2026-09-08
status: complete
plan_head_before: 1cb14d9d8408933b0f1e7fdd7ea1b680bcdd1e40
---

# Phase 24 Plan 05: Stop the shipped bundle resolving an executable path out of the caller's working directory Summary

**Closed the phase's only third-party-exploitable finding: `hooks/gsd-tools.sh`'s node-entry-point resolution and `capability.json`'s plan:post gate command both anchored a rung to whatever repository the caller's cwd sat inside; both now anchor to the sourced file's own location or delete the rung outright, with regression tests proving a hostile/enclosing repository is never reached (D-13, D-14).**

## Performance

- **Duration:** ~70min
- **Completed:** 2026-09-08T08:48:13Z
- **Tasks:** 3/3 complete
- **Commits:** 3 in the target repo (sota-numerics worktree) -- fix, fix, docs

## Accomplishments

- `hooks/gsd-tools.sh`'s first provider-resolution rung no longer runs `git
  rev-parse --show-toplevel` at the invoking working directory. It anchors to
  `CLAUDE_PLUGIN_ROOT` when the host sets it, or to `BASH_SOURCE[0]`'s own
  directory otherwise -- the identical anchor `session-start.sh` already
  computes at its own line 4, per the plan's decided alternative. A hostile
  repository placed at cwd, carrying its own `gsd-core/bin/gsd-tools.cjs`, can
  no longer supply the node entry point this function sources and runs (D-13).
  The remaining rungs -- `command -v gsd-tools` on `PATH`, then
  `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs`, then
  `return 127` -- are unchanged in order and behavior.
- `capability.json`'s `plan:post` gate command had the identical pattern in its
  own resolution chain: `SOTA_SCRIPT="$(git rev-parse --show-toplevel
  2>/dev/null)/$_SN"` as its middle rung. Deleted outright (a `sh -c` command
  string has no file of its own to anchor to, so deletion is the only
  available fix, per the plan's Internal design alternative), leaving the
  project-relative rung (`./$_SN`) then the `${GSD_HOME:-$HOME}` global rung.
  The `test -f` fail-closed guard, its message text, and its exit status of 1
  are byte-identical to before.
- Two live-pinned regression cases close the loop each task's own acceptance
  criteria named: `test-session-start.sh` case6 builds a real git repository
  at cwd carrying a `gsd-core/bin/gsd-tools.cjs` that writes a canary file if
  node ever runs it, and proves the canary never appears while legitimate
  PATH-based resolution still succeeds. `test-gate-script-resolution.sh`
  case6 builds a repository enclosing the working directory, carrying a
  hostile checker copy at the same relative path as the real script, and
  proves the gate falls straight through to the global copy instead --
  confirmed RED against the unedited gate command before Task 2's fix, GREEN
  after. A third case (`test-session-start.sh` case7) pins that an
  unresolvable provider still exits 127 unchanged, closing T-24-21 (the fix
  must not silently disable the hook path it touches).
- README.md (lines 68 and 222) and `NOTES.md` section 3 rewritten to describe
  the two-rung resolution order the code now performs in each file, not the
  three-rung order it used to. Both intentionally avoid the literal string
  `show-toplevel` in their own prose, describing the removed mechanism instead
  by what it did -- Task 3's own verify command greps for that literal across
  README.md/NOTES.md/`hooks/`/`capability.json` and fails on any hit
  regardless of tense; a first draft that quoted the removed command directly
  in NOTES.md's explanation would have tripped its own check (documented under
  Deviations).

## Task Commits

All commits below are in the **target repository**
(`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch
`feat/extended-sota-definition`), per the plan's `target_repo` frontmatter --
not the orchestrator repo.

1. **Task 1: Resolve the node entry point from the script's own location**
   - `55c44e7` (fix) -- `hooks/gsd-tools.sh`'s first rung anchored to
     `CLAUDE_PLUGIN_ROOT`/`BASH_SOURCE[0]`, no more `git rev-parse
     --show-toplevel`. New cases `case6` (hostile repository at cwd never
     supplies the entry point) and `case7` (unresolvable provider still exits
     127) added to `tests/test-session-start.sh`; corrected `mk_scratch`'s
     stale comment describing the removed git-based walk as current, dropping
     the now-unneeded `GIT_CEILING_DIRECTORIES` workaround it required.
     `bash tests/test-session-start.sh` -- 9/9 cases pass.
2. **Task 2: Remove the enclosing-repository rung from the gate command**
   - `6b61d4b` (fix) -- Added the failing case first
     (`tests/test-gate-script-resolution.sh` case6), confirmed RED against
     the unedited command (the hostile checker copy in the enclosing
     repository ran). Deleted `capability.json`'s middle rung; guard, message,
     and exit status 1 untouched. Confirmed GREEN: `bash
     tests/test-gate-script-resolution.sh` -- all 9 case/pass lines,
     `case5` (monorepo precedence) unaffected since it was already satisfied
     by the project-relative rung alone. Corrected `NOTES.md` section 3 to
     describe two rungs and name why the third went, without repeating the
     literal lookup string.
3. **Task 3: Bring README's resolution claims back in step with the code**
   - `f405303` (docs) -- Rewrote README.md lines 68 and 222 to name the new
     anchor and drop the claim that Git widens the project lookup (Task 2
     removed the rung that did that), keeping the untouched claim about
     Claude's automatic global install needing Git for provenance. Folded in
     two Rule-1 auto-fixes caught running the full suite after Tasks 1-2 (see
     Deviations): `hooks/gsd-tools.sh`'s own new comment named the removed
     rung literally, and `tests/test-capability-auto-install.sh`'s file-header
     comment described `GIT_CEILING_DIRECTORIES` as protecting the now-removed
     rung specifically. This SUMMARY plus the STATE.md/ROADMAP.md/
     REQUIREMENTS.md commit lands in the orchestrator (`gsd-beads`) repo.

## Files Created/Modified

- `hooks/gsd-tools.sh` (target repo) -- provider resolution anchored to
  `CLAUDE_PLUGIN_ROOT`/`BASH_SOURCE[0]`; comment corrected in Task 3.
- `.gsd/capabilities/sota-numerics/capability.json` (target repo) -- gate
  command's enclosing-repository rung deleted.
- `.gsd/capabilities/sota-numerics/NOTES.md` (target repo) -- section 3
  rewritten for the two-rung gate command.
- `tests/test-gate-script-resolution.sh` (target repo) -- new case6.
- `tests/test-session-start.sh` (target repo) -- new case6, case7; corrected
  `mk_scratch` comment.
- `tests/test-capability-auto-install.sh` (target repo, Rule-1 auto-fix) --
  corrected file-header comment.
- `README.md` (target repo) -- lines 68 and 222 rewritten.
- `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-05-SUMMARY.md`
  (this file, orchestrator repo).

## Decisions Made

See `key-decisions` in frontmatter -- all three are Claude's-discretion items
the plan explicitly delegated (exact anchor construction, matching the plan's
own decided Alternatives Considered rather than reopening them).

## D-05-shaped regression sweep

Not formally required by this plan (neither task touches
`check-alternatives.py`), but run anyway since both tasks change how the gate
*resolves* that script, which could in principle change what it sees:

| Measurement point | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|
| 24-04 end (D-07/D-08 closed), per 24-04-SUMMARY.md | 1 | 0 | 0 | 1 | 0 | 0 |
| After this plan's Tasks 1-3, direct script invocation | 1 | 0 | 0 | 1 | 0 | 0 |

Byte-identical. Python suite: 125/125 (unchanged from 24-04 -- no test added
or removed here, since `check-alternatives.py` itself is untouched).

## D-17 hash sidecar

Per D-17, `~/.gsd/capability-auto-install-sota-numerics.hash` is written by the
plugin's own `SessionStart`/`SubagentStart` hooks, hashing the whole
`.gsd/capabilities/sota-numerics` directory using the **absolute**,
`PLUGIN_ROOT`-rooted path (24-01/24-03 verified method). This plan recorded
both the live sidecar value and an independently re-measured whole-bundle
hash, before and after its edits:

| Value | Pre-edit (plan's start, commit `1cb14d9`) | Post-edit (plan's end, commit `f405303`) |
|---|---|---|
| Live sidecar (`~/.gsd/capability-auto-install-sota-numerics.hash`) | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` (unchanged) |
| Independently re-measured whole-bundle hash (absolute path, matching hook's own computation) | `daf0c3885432184b29335f94ab3f42dcfe496e1ed71d5410faca59e2d5293020` | `4f7e518bd92473752aa4e6063b1f8b46845bb0c1bbffa0cd20ba6541b4382143` (changed -- expected, `capability.json` and `NOTES.md` are inside the hashed bundle and this plan edits both) |

The live sidecar stayed unchanged throughout: the bundle's own dirty-tree
guard (`hooks/capability-auto-install.sh`, commit `6e1d61c`, ancestor of this
plan's base) refuses to install an uncommitted bundle at global scope, and
this plan's worktree carried uncommitted changes for its entire duration.
This matches the previously-documented stale state 24-01/24-03/24-04 each
independently confirmed unchanged.

The independently re-measured pre-edit value here
(`daf0c3885432184b29335f94ab3f42dcfe496e1ed71d5410faca59e2d5293020`) differs
from 24-04-SUMMARY.md's own recorded post-edit value
(`909bd37ef555b4042241eb10f2ed046b2be06a39224a1aa722e14116c7360a08`) despite
`git status --porcelain` showing a clean tree at both measurement points and
`HEAD` matching (`1cb14d9`) at the start of this plan. Root cause: the bundle
hash function (`hooks/capability-auto-install.sh`'s `bundle_hash`) walks and
hashes `scripts/__pycache__/check-alternatives.cpython-314.pyc`, which is
gitignored and therefore outside `git status`'s clean-tree guarantee; that
`.pyc`'s own bytes are not purely a function of the tracked source (CPython's
default invalidation mode embeds the source file's mtime in the header), so
running the Python test suite between 24-04's measurement and this plan's
start -- neither of which changes tracked content -- can still shift the
measured bundle hash. This is a pre-existing measurement-instability gap in
the hash function itself, not a defect this plan's tasks introduced or are
scoped to fix; documented here rather than silently reconciled, per this
project's rule against tuning a claim to look closer to expectation than the
evidence supports.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Doc-truth bug, self-caught before commit] NOTES.md's first draft
quoted the removed lookup literally, which would have failed Task 3's own
verify command**
- **Found during:** Task 2, writing NOTES.md's replacement prose for section 3.
- **Issue:** The first draft explained the removed rung by quoting it verbatim
  (`` `$(git rev-parse --show-toplevel)/$_SN` `` and a second sentence
  containing the bare phrase `` `git rev-parse --show-toplevel` ``). Task 3's
  own verify command is `grep -rn 'show-toplevel' README.md NOTES.md hooks/
  capability.json | grep -c .`, `fails_when` that count is greater than 0 --
  tense-blind, so a past-tense explanation that quotes the code is exactly as
  disqualifying as a present-tense claim.
- **Fix:** Rewrote both sentences to describe the removed mechanism by what it
  did ("asking Git for the top level of the repository enclosing the working
  directory and appending the script path to it"), matching the plan's own
  ticket-description style, which itself avoided the literal string for the
  same reason.
- **Files modified:** `.gsd/capabilities/sota-numerics/NOTES.md` (target repo).
- **Verification:** `grep -rn 'show-toplevel' README.md NOTES.md hooks/
  capability.json` -- count 0, run before Task 2's commit.
- **Committed in:** `6b61d4b` (folded into Task 2's commit; caught before
  commit, not a separate correction).

**2. [Rule 1 - Doc-truth bug, directly caused by Task 1] hooks/gsd-tools.sh's
own new comment named the removed rung literally**
- **Found during:** Task 3, running the repo-wide sanity grep before README's
  own commit.
- **Issue:** Task 1's commit (`55c44e7`) added an explanatory comment inside
  `gsd_tools()` that read `` # deliberately no `git rev-parse --show-toplevel`
  rung here any more -- ``. This is `hooks/`-scoped, directly inside Task 3's
  own verify command's file set, and would have made its grep count 1 instead
  of 0 had it not been caught.
- **Fix:** Reworded to `` # deliberately no Git-based rung asking for the
  repository enclosing the invoking working directory any more -- `` --
  same meaning, no literal match.
- **Files modified:** `hooks/gsd-tools.sh` (target repo).
- **Verification:** `grep -rn 'show-toplevel' README.md NOTES.md hooks/
  capability.json` -- count 0.
- **Committed in:** `f405303` (Task 3's commit).

**3. [Rule 1 - Doc-truth bug, directly caused by Tasks 1-2] test-capability-auto-install.sh's
file-header comment described GIT_CEILING_DIRECTORIES as protecting the
now-removed rung specifically**
- **Found during:** Task 3, running a repo-wide (not just Task 3's own
  three-file) grep for `show-toplevel` as an extra sanity pass, which
  surfaced this file even though it carries no `files_modified` entry in any
  task.
- **Issue:** `tests/test-capability-auto-install.sh` is a dedicated suite for
  `hooks/capability-auto-install.sh`, which itself sources `hooks/gsd-tools.sh`
  (line 224). Its file-header comment claimed `GIT_CEILING_DIRECTORIES`
  "keeps the hook's first gsd-tools rung (`git rev-parse --show-toplevel`,
  then `$toplevel/gsd-core/bin/gsd-tools.cjs`) from reaching a real binary" --
  a claim about the rung Task 1 just deleted. Re-reading the suite's own
  `run_hook()` helper (line ~194) confirmed it unconditionally sets
  `CLAUDE_PLUGIN_ROOT="${2:-$_root}"` on every invocation, so the suite's own
  assertions were never actually exercising the deleted rung and needed no
  functional change -- confirmed by running the full suite both before and
  after this edit (54/54 case/pass lines, 0 FAIL, both times). Only the
  comment's claim was stale.
- **Fix:** Reworded to attribute `GIT_CEILING_DIRECTORIES` to its remaining
  real purpose (isolating the hook's own bundle-provenance git commands) and
  to name `run_hook`'s unconditional `CLAUDE_PLUGIN_ROOT` as what now keeps
  `gsd-tools.sh`'s resolution off the working directory in this suite.
- **Files modified:** `tests/test-capability-auto-install.sh` (target repo).
- **Verification:** `bash tests/test-capability-auto-install.sh` -- unchanged
  pass count before and after (54/54 lines, 0 FAIL); this file carries no test
  assertions on the comment text itself, so the fix is comment-only.
- **Committed in:** `f405303` (Task 3's commit).

Three auto-fixed issues, all Rule 1 (doc-truth bugs directly caused by this
plan's own Tasks 1-2), none requiring a functional code change -- one caught
before its own commit, two caught by an extra sanity sweep beyond Task 3's
formal three-file verify scope, before the plan's final commit.

## Known Stubs

None.

## Threat Flags

None -- this plan closes threat register entries T-24-17 through T-24-21 (all
`mitigate` dispositions in its own `<threat_model>`); it introduces no new
network endpoint, auth path, file-access pattern, or schema change at a trust
boundary. It removes a caller-cwd-derived lookup, which narrows attack surface
rather than widening it.

## Issues Encountered

None blocking. One workflow near-miss, corrected before it caused any harm:
while spot-checking the gate command's end-to-end behavior against a real
project (beyond what the plan's own verify commands require), an `ln -sfn
<worktree>/.gsd .gsd` run from the orchestrator repo's root landed inside the
orchestrator's own pre-existing `.gsd/` directory (a real, unrelated
project-scope install of the `beads` capability) as a nested stray symlink
`.gsd/.gsd`, rather than replacing `.gsd` itself. Removed immediately
(`rm -f .gsd/.gsd`); confirmed the orchestrator's real `.gsd/capabilities/beads/`
content was untouched (`find .gsd -maxdepth 3` before and after matched
except for the added-then-removed entry) and `git status --short -- .gsd`
showed no change. No further ad hoc end-to-end probing against the live
orchestrator repo was performed; the plan's own three shell suites plus the
direct D-05-shaped script sweep (against `gsd-beads`'s real `.planning/phases/`
corpus, read-only) already cover the required evidence.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- D-13, D-14 closed: the only third-party-exploitable finding this phase's
  four-lens review raised is fixed in both sites it occurred at, with live
  regression evidence a hostile or enclosing repository at the caller's
  working directory is never reached.
- D-17: live sidecar remains in its previously-documented stale state
  (unchanged across 24-01, 24-03, 24-04, and this plan); independently
  re-measured pre-edit bundle hash confirms the tracked-content baseline this
  plan started from, and the post-edit hash reflects exactly the two files
  (`capability.json`, `NOTES.md`) this plan edits inside the bundle.
  Reconciling the sidecar with a real install remains a later plan's scope
  (unchanged from 24-04's own note).
- Remaining phase-24 requirements not yet closed by 24-01/24-03/24-04/24-05:
  D-06, D-09 through D-12, D-15, D-16, D-18 through D-24 (publish sequence,
  outstanding CodeRabbit threads, claims-do-not-resolve cleanup) are later
  plans' scope per the phase's wave structure.

---
*Phase: 24-remediate-sota-numerics-0-2-0-release-blockers*
*Completed: 2026-09-08*

## Self-Check: PASSED

- FOUND: `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-05-SUMMARY.md`
- FOUND: target-repo commits `55c44e7`, `6b61d4b`, `f405303`
- FOUND: `hooks/gsd-tools.sh`, `.gsd/capabilities/sota-numerics/capability.json`, `tests/test-gate-script-resolution.sh` (target repo)
