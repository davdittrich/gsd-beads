---
quick_id: 260908-h0l
subsystem: testing
tags: [sota-numerics, hooks, pytest, bash-tests, gsd-core-capability, case-sensitivity]

# Dependency graph
requires:
  - gsd-beads-25vc.21 (D-01, D-18, D-19 amendments) — closed parent ticket
provides:
  - Regression coverage for hooks.json's SubagentStart wiring
  - A containment digest that sees a __pycache__ leak into the real global mirror
  - A verified (not asserted) decision record for the case-insensitive-filesystem
    residual in PLAN_FILE_RE/PLAN_SHAPED_RE
affects:
  - Any future edit to sota-numerics/hooks/hooks.json, hooks/session-start.sh,
    tests/test-capability-auto-install.sh, tests/test-session-start.sh,
    .gsd/capabilities/sota-numerics/scripts/check-alternatives.py,
    tests/test_check_alternatives.py

# Actuals (#2632)
actuals:
  tokens: 4218   # 16870 chars / 4 over `git diff cc014e1..d36678d` in the target repo
  tasks: 3
  commits: 3
  plan_head_before: cc014e1

tech-stack:
  added: []
  patterns:
    - "Two-walk containment digest: full path listing (names only) folded with a
       content-hashed, __pycache__-pruned walk, piped into one final hash"
    - "Manifest-driven role-token test: extract hooks.json's SubagentStart role
       tokens with python3, then exercise session-start.sh with the extracted
       tokens rather than hardcoded ones"

key-files:
  created: []
  modified:
    - path: .worktrees/sota-numerics-release-013/tests/test-capability-auto-install.sh
      note: real_gsd_state() now folds a full path listing into the digest
    - path: .worktrees/sota-numerics-release-013/tests/test-session-start.sh
      note: real_gsd_state() fix (same as above) + new case 8 (hooks.json wiring)
    - path: .worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/NOTES.md
      note: new section 7, the case-insensitivity decision record
    - path: .worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py
      note: PLAN_SHAPED_RE comment now points at NOTES.md section 7
    - path: .worktrees/sota-numerics-release-013/tests/test_check_alternatives.py
      note: new test pinning the Linux-observable half of the case-sensitivity decision

key-decisions:
  - "gsd-beads-25vc.21.3 item 3: no macOS/Windows CI leg added for the case-insensitive-
     filesystem residual. Read gsd-core 1.13.0's actual source (plan-phase.md:574,
     execute-plan.md:58-69, gsd-tools.cjs) before deciding, rather than asserting: both
     places gsd-core discovers/reads PLAN.md content use a bare case-sensitive shell
     glob, identical case-sensitivity to PLAN_FILE_RE/PLAN_SHAPED_RE — no divergence
     found. Recorded as NOTES.md section 7 with citations, with a reopen trigger."
  - "__pycache__ containment fix uses a full path listing (names only, no content
     hash) folded alongside the existing content-hashed walk, rather than hashing
     .pyc content directly — a .pyc embeds its source's mtime, so hashing its bytes
     would make the containment check flaky on every mirror re-read."
  - "hooks.json wiring test reads role tokens FROM the manifest via python3, not
     hardcoded planner/executor/verifier literals, so a manifest typo (not just a
     script bug) is what turns the case red."

requirements-completed: []

coverage:
  - id: D1
    description: "hooks.json's SubagentStart matchers/commands/role-tokens are
      asserted against README.md's documented contract, and the tokens it supplies
      are proven to reproduce the case-3a-3c role banners"
    verification:
      - kind: unit
        ref: "tests/test-session-start.sh case 8 (all 6 PASS lines) + RED-PROOF
          (drifted gsd-planner->gsd-plannr matcher makes the suite exit non-zero)"
        status: pass
    human_judgment: false
  - id: D2
    description: "real_gsd_state()'s containment digest now moves when a
      __pycache__ path is added to the real global mirror, and stays stable when
      only bytecode content churns"
    verification:
      - kind: unit
        ref: "bash tests/test-capability-auto-install.sh && bash tests/test-session-start.sh
          (both ALL PASS) + inline PROOF-OK synthetic digest comparison"
        status: pass
    human_judgment: false
  - id: D3
    description: "The case-insensitive-filesystem residual is verified against
      gsd-core 1.13.0 source (not asserted), recorded as an accepted-risk decision
      in NOTES.md section 7, and its Linux-observable half is pinned by a unit test"
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py::TestMisnamedPlans::test_lowercase_plan_suffix_is_invisible_not_merely_misnamed"
        status: pass
    human_judgment: false

# Metrics
duration: ~27min (commit-to-commit, cc014e1..d36678d); source-verification research
  preceding the first commit (reading gsd-core's own discovery code before writing
  the NOTES.md decision, per the plan's explicit instruction) took materially longer
  and was not separately timed
completed: 2026-09-08
status: complete
---

# Quick Task 260908-h0l: sota-numerics test coverage for hooks.json, pycache leak, case-insensitive PLAN.md glob — Summary

**Closed all three findings in gsd-beads-25vc.21.3 by testing the two real gaps (SubagentStart wiring, `__pycache__` containment) and replacing an unverified case-sensitivity claim with one actually checked against gsd-core's source.**

## Performance

- **Tasks:** 3/3 completed
- **Files modified:** 5 (all in the target repo, `davdittrich/sota-numerics` branch `feat/extended-sota-definition`, worktree `.worktrees/sota-numerics-release-013`)
- **Test suites re-run green:** 4/4 (`test-capability-auto-install.sh`, `test-session-start.sh`, `test-gate-script-resolution.sh`, `test_check_alternatives.py` — 131 unit tests)

## Accomplishments

- **hooks.json SubagentStart wiring is now tested (item 1).** Added case 8 to `tests/test-session-start.sh`: parses `hooks/hooks.json` with python3, asserts (each its own PASS/FAIL line) it is valid JSON, `SubagentStart` holds exactly the three `gsd-planner`/`gsd-executor`/`gsd-verifier` matchers, each entry invokes `session-start.sh` with its own `gsd-` suffix as the role token, `SessionStart`'s matcher is unchanged, and every `${CLAUDE_PLUGIN_ROOT}`-relative script the manifest names exists. Then re-runs `session-start.sh` with the role tokens *read from the manifest* (not hardcoded) and asserts the case-3a-3c banner substrings. Confirmed the case actually detects drift: a synthetic `gsd-planner` → `gsd-plannr` matcher rename made the suite exit non-zero with 4 distinct FAIL lines, then reverted via `git checkout --`.
- **`__pycache__` leak into the containment digest is closed (item 2).** `real_gsd_state()` in both `test-capability-auto-install.sh` and `test-session-start.sh` previously pruned `__pycache__` out of *both* the path listing and the content hash, so bytecode leaked into the real global mirror was completely invisible to the I0/case5 containment check. Fixed by folding a full path listing (directories included, names only) alongside the existing pruned content walk into one final hash — a new `__pycache__` directory or `.pyc` file now moves the digest, while `.pyc` content churn (which embeds the source file's mtime and would otherwise make the check flaky) still does not. Verified with an inline synthetic proof: `A != B` when a `.pyc` first appears, `B == C` when its content later changes.
- **The case-insensitive-filesystem residual is now a checked decision, not an assumption (item 3).** The `PLAN_SHAPED_RE` comment asserted, without ever reading gsd-core's source, that gsd-core's own `*-PLAN.md` glob would read a lowercase-named plan on a case-insensitive filesystem (macOS/Windows) where this gate would not. Read gsd-core 1.13.0's actual source first: both places it discovers or reads PLAN.md content (`plan-phase.md:574`, `execute-plan.md:58-69`) use a bare, case-sensitive shell glob — the same case-sensitivity `PLAN_FILE_RE`/`PLAN_SHAPED_RE` already have. `gsd-tools.cjs` has no plan-discovery code of its own. **No divergence was found.** Recorded this as NOTES.md section 7 (citations, accepted-risk decision, reopen trigger) and pointed the `PLAN_SHAPED_RE` comment at it instead of restating the now-corrected claim. Pinned the half of the decision that *is* observable on Linux with a new unit test: a lowercase `23-01-plan.md` is invisible to the gate (exit 0, no output), not merely misnamed.
- Verified the plan's explicit safety invariant held throughout: `~/.gsd/capability-auto-install-sota-numerics.hash` still reads `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` after all three tasks (checked after each commit), and the worktree was never dirty going into any subsequent task.

## Task Commits

All three commits are in the **target repo** (`davdittrich/sota-numerics`, worktree `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`), not in `gsd-beads`:

1. **Task 1: make the containment digest see leaked Python bytecode** - `b87a661` (fix)
2. **Task 2: pin the hooks.json SubagentStart wiring, with its assumption stated** - `cd8b5b6` (test)
3. **Task 3: verify, then record, the case-insensitive-filesystem residual** - `d36678d` (docs)

No plan-metadata commit was made in `gsd-beads` beyond this SUMMARY.md and STATE.md update (per `<sequential_execution>`, ISOLATION=none — this plan's deliverable lives entirely in the target repo).

## Files Created/Modified

(All paths relative to `.worktrees/sota-numerics-release-013/`)

- `tests/test-capability-auto-install.sh` - `real_gsd_state()` folds a full path listing into the containment digest; extended its existing comment rather than adding a separate block
- `tests/test-session-start.sh` - same `real_gsd_state()` fix, plus new case 8 (hooks.json SubagentStart wiring, ~130 lines)
- `.gsd/capabilities/sota-numerics/NOTES.md` - new `## 7.` section recording the verified case-sensitivity decision
- `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` - `PLAN_SHAPED_RE`'s comment now points at NOTES.md section 7 instead of restating the claim
- `tests/test_check_alternatives.py` - new test in `TestMisnamedPlans` pinning the Linux-observable half of the decision

## Decisions Made

See `key-decisions` in frontmatter. The most consequential: the case-insensitivity residual was **verified false** (no divergence exists in gsd-core 1.13.0's actual PLAN.md discovery code) rather than accepted as an unverified risk — the plan's Task 3 explicitly required establishing the mechanism before recording any decision, since "a sentence CLAIM about another project's code nobody in this repository has checked" would have been worthless.

## Deviations from Plan

None — plan executed exactly as written, including its explicit instruction to fix the `__pycache__` helper in both test files (not just the ticket-named one) and to verify gsd-core's own source before recording the case-sensitivity decision.

## Known Stubs

None.

## Threat Flags

None. Task 3 touches the capability bundle (`.gsd/capabilities/sota-numerics/`), which is the plan's named threat surface for this quick task; the target repo's own dirty-tree and not-an-ancestor-of-origin/HEAD guards in `hooks/capability-auto-install.sh` were confirmed still holding (sidecar hash unchanged, branch never pushed) rather than newly introduced.

## Self-Check: PASSED

All three commits (`b87a661`, `cd8b5b6`, `d36678d`) confirmed present in the target repo's history. All five modified files confirmed present on disk. This SUMMARY.md confirmed written. Final re-run of all 4 CI suites (`test-session-start.sh`, `test-capability-auto-install.sh`, `test-gate-script-resolution.sh`, `test_check_alternatives.py`) confirmed `ALL PASS` / `OK`. `~/.gsd/capability-auto-install-sota-numerics.hash` confirmed unchanged (`da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498`). Target worktree confirmed clean (`git status --short` empty) at HEAD `d36678d`.
