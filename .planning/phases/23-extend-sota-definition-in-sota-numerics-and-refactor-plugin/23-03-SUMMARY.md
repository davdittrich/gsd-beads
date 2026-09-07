---
phase: 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin
plan: 03
subsystem: infra
tags: [gsd-core, capability-plugin, sota-numerics, self-compliance, manifest]

# Dependency graph
requires:
  - phase: 23-01
    provides: "quiet, legible, and efficiency/completeness dimensions defined once in executor-numerics.md"
  - phase: 23-02
    provides: "with the grain and plan-completeness dimensions defined once in planner-sota.md"
provides:
  - "capability.json and plugin.json both at 0.2.0 with rewritten description strings naming the extended six-dimension SOTA definition while still stating exactly one gate, at plan:post"
  - "check-alternatives.py's module docstring, function docstrings, and inline comments rewritten to state their claims inline instead of pointing at RESEARCH.md/REVIEWS/CONTEXT.md/threat-ID references that don't ship with the capability -- its executable logic (docstring-stripped AST) unchanged from origin/main"
affects: ["23-04 (NOTES.md pruning)", "23-05 (publish 0.2.0)"]

# Actuals (#2632)
actuals:
  tokens: 3108
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Structural JSON diff against origin/main with an explicit allowed-key-path allowlist (version, description, gates[0].description, config.sota-numerics.enabled.description) proves a manifest rewrite touched only prose, not the gate contract or contributions array."
    - "Docstring-stripped AST equality (ast.dump() on a tree with the first Expr(Constant(str)) node popped off every Module/FunctionDef/ClassDef body) proves a prose refactor changed zero executable lines -- comments are already invisible to ast.parse(), so only docstrings needed explicit stripping."
    - "Document pointers replaced by their claims: a comment or docstring that cited an ID or filename from a planning artifact the capability doesn't ship (RESEARCH.md, REVIEWS, CONTEXT.md, T-nn-nn threat IDs) was rewritten to state the underlying reasoning inline, so the shipped file is self-contained for a reader who only has the sota-numerics repo."

key-files:
  created: []
  modified:
    - .gsd/capabilities/sota-numerics/capability.json
    - .claude-plugin/plugin.json
    - .gsd/capabilities/sota-numerics/scripts/check-alternatives.py

key-decisions:
  - "gates[0].description's do-not-revert-onError instruction was kept as a self-contained claim (\"A blocking gate that silently skips on its own command failure defeats its purpose.\") with its dangling \"(CONTEXT.md Established Patterns)\" citation removed rather than shortened -- the sentence already carried the full claim independent of the citation."
  - "check-alternatives.py's check_alternatives() docstring bug (claimed a (exit_code, violations) return; the function returns violations only) was fixed as part of the prose refactor since it falls squarely inside Task 3's docstring/comment scope -- Rule 1 auto-fix, not a deviation, since the function body was never touched."
  - "Two independent verification instruments were run for the gate script, per the plan's Internal design alternatives: docstring-stripped AST equality (catches any executable-line drift) plus a manual reference-pointer grep and a negative-fixture exit-1 remediation-line check (catches prose regressions the AST comparison is blind to inside docstrings)."

patterns-established:
  - "A manifest description-string rewrite that grows the surface of what a capability describes must still be size- and truth-bounded: both new descriptions state the extended definition while explicitly disclaiming any new gate (\"No new gate covers the added dimensions\"), matching D-01/D-02/D-03's blocking-gate-must-stay-measurable rationale from CONTEXT.md."

requirements-completed:
  - D-01
  - D-02
  - D-03
  - D-05
  - D-17
  - D-19
  - D-20
  - D-21
  - D-23

coverage:
  - id: D1
    description: "capability.json bumped to 0.2.0; description, gates[0].description, and config.sota-numerics.enabled.description rewritten to name the extended SOTA definition and drop citations to documents the capability doesn't ship, while gates[0].check (predicate.command, blocking, onError, when) and the whole contributions array stay byte-identical to origin/main"
    requirement: "D-01, D-05, D-17, D-23"
    verification:
      - kind: other
        ref: "structural JSON diff vs origin/main with a 4-path allowlist (version, description, config.sota-numerics.enabled.description, gates.0.description) -- printed MANIFEST-OK with zero unexpected diffs; commit eaca1c1"
        status: pass
    human_judgment: false
  - id: D2
    description: "plugin.json bumped to 0.2.0 with a matching, marketplace-audience description naming the same extended dimensions and still describing exactly one blocking gate"
    requirement: "D-19, D-23"
    verification:
      - kind: other
        ref: "git diff origin/main -- .claude-plugin/plugin.json shows only version and description changed; both manifests read 0.2.0; commit f3478ad"
        status: pass
    human_judgment: false
  - id: D3
    description: "check-alternatives.py's module docstring, six function docstrings, and three inline comments rewritten to remove every RESEARCH.md/REVIEWS/CONTEXT.md/T-nn-nn/sync.py citation, replacing each with the claim it stood for, while a stale check_alternatives() docstring bug (wrong return-shape claim) was also fixed"
    requirement: "D-17, D-20, D-21"
    verification:
      - kind: other
        ref: "grep -nE 'RESEARCH|REVIEWS|CONTEXT\\.md|NOTES\\.md|T-[0-9]{2}-[0-9]{2}|D-[0-9]{2}\\b' on the file returns no match (REFS-RESOLVED count=0); commit f1e7f3a"
        status: pass
    human_judgment: false
  - id: D4
    description: "check-alternatives.py's docstring-stripped AST is identical to origin/main's, and all three pre-existing regression suites plus a manual negative-fixture check still pass"
    requirement: "D-01, D-20"
    verification:
      - kind: other
        ref: "ast.dump() on both trees with the leading docstring Expr node popped from every Module/FunctionDef/ClassDef -- printed AST-IDENTICAL; python3 -m unittest tests/test_check_alternatives.py (Ran 50 tests OK), tests/test-session-start.sh and tests/test-gate-script-resolution.sh (ALL PASS); a hand-built non-compliant PLAN.md fixture still exits 1 with exactly one remediation: line"
        status: pass
    human_judgment: false
  - id: D5
    description: "Recursion guard held throughout: the globally installed mirror at ${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics was never written to, and hooks/ and tests/ were never touched"
    verification:
      - kind: other
        ref: "sha256sum digest of ~/.gsd/capabilities/sota-numerics re-checked before and after every task, unchanged at 3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e; git diff --stat origin/main -- hooks/ tests/ shows only the two pre-existing, unrelated commits (6e1d61c, 9b36af2) already on the branch before this plan, no new changes"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-09-07
status: complete
---

**Bumped `capability.json` and `plugin.json` to 0.2.0 with rewritten description strings that name the extended six-dimension SOTA definition while still stating exactly one gate at plan:post, and rewrote `check-alternatives.py`'s docstrings/comments to remove every dangling pointer to a document the capability doesn't ship -- its executable logic, proven by docstring-stripped AST equality, did not change a single line.**

- **Duration:** 20 min
- **Completed:** 2026-09-07T01:25:03Z
- **Tasks:** 3
- **Files modified:** 3 (in the sota-numerics worktree)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed a stale docstring on `check_alternatives()`**
- **Found during:** Task 3
- **Issue:** The function's docstring claimed it returns `(exit_code, violations)`, but the function body only ever returns `violations` (a list of `(plan_path, reason)` tuples) -- a pre-existing documentation/implementation mismatch, unrelated to any document-pointer removal.
- **Fix:** Rewrote the docstring to describe the actual return value.
- **Files modified:** `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`
- **Commit:** f1e7f3a

No other deviations -- plan executed as written.

## Verification Evidence

- `MANIFEST-OK`: structural JSON diff of `capability.json` against `origin/main` with a 4-path allowlist (`version`, `description`, `config.sota-numerics.enabled.description`, `gates.0.description`) found zero unexpected diffs.
- `plugin.json` diff against `origin/main` touches only `version` and `description`; both manifests read `0.2.0`.
- `AST-IDENTICAL`: `check-alternatives.py`'s docstring-stripped AST (`ast.dump()`, leading `Expr(Constant(str))` popped from every `Module`/`FunctionDef`/`ClassDef` body) matches `origin/main` byte for byte.
- `REFS-RESOLVED count=0`: no remaining `RESEARCH|REVIEWS|CONTEXT\.md|NOTES\.md|T-\d{2}-\d{2}|D-\d{2}\b` pattern in the gate script.
- `python3 -m unittest tests/test_check_alternatives.py` -> Ran 50 tests, OK.
- `tests/test-session-start.sh` and `tests/test-gate-script-resolution.sh` -> ALL PASS.
- Hand-built non-compliant `PLAN.md` fixture still exits 1 with exactly one `remediation: ...` line.
- Recursion guard digest re-verified before Task 1 and after Task 3: `3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e`, unchanged.
- `hooks/` and `tests/` carry no new diff against `origin/main` beyond the two pre-existing, unrelated commits (`6e1d61c`, `9b36af2`) already on the branch.

## Known Stubs

None.

## Threat Flags

None -- this plan edits only advisory manifest description strings and gate-script prose; no new network endpoint, auth path, file-access pattern, or schema change at a trust boundary was introduced.

## Self-Check: PASSED
