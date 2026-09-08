---
phase: quick-260908-h0m
plan: 01
subsystem: infra
tags: [gsd-core, capability-plugin, prose-trim, sota-numerics, bash, python]
requires: []
provides:
  - "sota-numerics 0.2.0's SubagentStart banners point at their fragments instead of copying them"
  - "sota-numerics's four injected fragments (planner-sota.md, executor-numerics.md, verifier-precision.md, ship-precision-advisory.md) trimmed to one statement per rule"
  - "sota-numerics's plugin.json description and NOTES.md section 1 trimmed"
affects: [sota-numerics-release]
actuals:
  tokens: 5029
  tasks: 3
  commits: 3
  plan_head_before: 2f4d52aa5f6f56f6b138b9c4b10522fd136477dd
tech-stack:
  added: []
  patterns: []
key-files:
  created: []
  modified:
    - hooks/session-start.sh
    - tests/test-session-start.sh
    - CHANGELOG.md
    - .gsd/capabilities/sota-numerics/fragments/planner-sota.md
    - .gsd/capabilities/sota-numerics/fragments/executor-numerics.md
    - .gsd/capabilities/sota-numerics/fragments/verifier-precision.md
    - .gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md
    - .claude-plugin/plugin.json
    - .gsd/capabilities/sota-numerics/NOTES.md
key-decisions:
  - "The SubagentStart role banners now point at their fragment (\"the injected sota-numerics planner fragment carries...\") instead of restating its rules verbatim, giving up the failsafe that a silently-skipped fragment render left the full rule text visible in the banner."
  - "executor-numerics.md's 'keep a definition next to the caveats that qualify it' clause was dropped rather than compressed — judged to restate a general prose standard a competent model already follows."
  - "The plan's own literal Result text for executor-numerics.md line 7 ran 431 characters against Task 2's own 400-char verify gate; tightened three clauses (unresolvable-input phrasing, exit-code sentence, file-path sentence) to 398 chars with no content or constraint dropped."
  - "check-alternatives.py's module docstring Exit-2 parse-risk finding is out of REVIEW-PROSE-TOKENS.md's scope and gsd-beads-25vc.21.5's acceptance criteria; filed as standalone issue gsd-beads-to0b rather than fixed here."
  - "hooks/capability-auto-install.sh's nine refusal messages are left unchanged as a recorded decision (P4, confidence 65, retry semantics already documented in the script)."
requirements-completed: [gsd-beads-25vc.21.5]
coverage:
  - id: D1
    description: "SubagentStart banners point at their fragment; tests/test-session-start.sh's case3a/case3b (plus the case8 manifest-token duplicate) pin the pointer phrases and stay role-unique."
    requirement: "gsd-beads-25vc.21.5"
    verification:
      - kind: unit
        ref: "tests/test-session-start.sh (bash tests/test-session-start.sh)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Four injected fragments trimmed to one statement per rule; test_check_alternatives.py's pinned planner-sota.md contract sentence stays byte-identical."
    requirement: "gsd-beads-25vc.21.5"
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py (python3 -m unittest tests/test_check_alternatives.py)"
        status: pass
    human_judgment: false
  - id: D3
    description: "plugin.json description reuses README.md:3's sentence plus the gate clause; NOTES.md section 1 trimmed to the contributions contrast, pointing at capability.json for the full argument."
    requirement: "gsd-beads-25vc.21.5"
    verification:
      - kind: unit
        ref: "ad hoc python3 assertions in the plan's Task 3 <verify> block (json load + string checks on plugin.json and NOTES.md)"
        status: pass
    human_judgment: false
---

- **Completed:** 2026-09-08T12:05:00Z
- **Tasks:** 3/3
- **Files modified:** 9 (target repo `.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`)

## Accomplishments

- Landed the three remaining trim commits from `REVIEW-PROSE-TOKENS.md` against bd ticket `gsd-beads-25vc.21.5`: SubagentStart banner pointers (row 1, TDD test-first), the four injected fragments (rows 2-9), and `plugin.json`/`NOTES.md` (rows 10, 13).
- Test-first per Task 1's `<behavior>`: edited `tests/test-session-start.sh`'s case3a/case3b assertions before touching the hook, confirmed exactly those two cases went RED, then made the hook change and confirmed the full suite went GREEN.
- Recorded both no-change dispositions on `gsd-beads-25vc.21.5` (one bd comment) and filed the check-alternatives.py docstring parse-risk finding as standalone issue `gsd-beads-to0b`.
- Closed `gsd-beads-25vc.21.5` with acceptance-criteria evidence in a bd comment.

## Task Commits

Each task committed atomically in `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013` on `feat/extended-sota-definition`:

1. **Task 1: Replace the three SubagentStart banner bodies with pointers, and document the failsafe given up** — `a0a66d1` (docs, tdd)
2. **Task 2: Land the seven fragment trims across the four injected fragments** — `61cc8d2` (docs)
3. **Task 3: Rewrite plugin.json's description, trim NOTES.md section 1, and record the two no-change dispositions** — `ce855f9` (docs)

**Plan metadata:** this SUMMARY.md and the STATE.md row are committed in the `gsd-beads` orchestrator repo, separately from the above (see Final Commit below); no plan-metadata commit lands in the target repo.

`BASE_SHA` recorded before Task 1's first edit: `2f4d52aa5f6f56f6b138b9c4b10522fd136477dd`. `git log --oneline "$BASE_SHA"..HEAD` shows exactly the three commits above and nothing else; `git status --short` is clean; `git diff --stat "$BASE_SHA"..HEAD` touches exactly the nine `files_modified` files; `git diff "$BASE_SHA"..HEAD -- .gsd/capabilities/sota-numerics/scripts/` is empty.

## RED-then-GREEN Transcript (Task 1, TDD)

RED — after editing `tests/test-session-start.sh`'s case3a/case3b assertions to look for `planner fragment` / `executor fragment`, before touching `hooks/session-start.sh` (`bash tests/test-session-start.sh`, exit 1):

```
FAIL: case3a: planner framing line missing
PASS: case3a: ROLE=planner framing
FAIL: case3b: executor framing line missing
PASS: case3b: ROLE=executor framing
PASS: case3c: ROLE=verifier framing
PASS: case3d: bogus role falls back to generic
...
2 FAILED
```

Exactly `case3a` and `case3b` failed — the plan's required RED shape.

GREEN — after the `hooks/session-start.sh` edit (`bash tests/test-session-start.sh`, exit 0): `ALL PASS`.

**Undocumented duplicate assertion found during RED/GREEN.** `tests/test-session-start.sh`'s `case8` block (added to the suite after this plan was drafted — the plan's line-number anchors predate it) contains a *second*, independent pair of assertions checking the same banner text via the `hooks.json` manifest-token invocation path (`case8: manifest's planner token did not produce the planner framing` / `...executor token...`). These still asserted the old verbatim phrases (`ranked criterion`, `avoid cancellation`) and went red once the hook was edited, even though Task 1's own two named assertions were already green. Fixed as a Rule 3 auto-fix (blocking issue, same intent as the plan's own instruction, plan predates this test's addition): updated both `case8` assertions to the same pointer phrases, in the same commit as Task 1.

## Steering Rule Removed (Task 2, not compressed)

`executor-numerics.md`'s former lines 9-10 were merged into one line (row 8). One clause was dropped outright rather than compressed: **"keep a definition next to the caveats that qualify it."** Judgement per the plan: this restates a general prose standard a competent model already follows by default, so it was removed rather than folded into the merged sentence. Every other clause on those two lines survives, merged, in `executor-numerics.md`'s current line 9.

## Failsafe Traded Away (Task 1)

Before this change, each SubagentStart banner body was a full backup copy of its fragment's rule text. Now each body is a short pointer (e.g. `"Executing: the injected sota-numerics executor fragment carries the numerical-stability, efficiency and quiet-output rules."`). The four fragment contributions declare `onError: skip`, so a contribution that fails to render fails silently. On such a silent render failure, the subagent now learns only that the capability is active and that the step carries a blocking gate — not what the gate wants — where before, the banner itself was a complete fallback copy of the rules. This is recorded in both `hooks/session-start.sh` (a comment above the `case "$ROLE" in` block, citing `gsd-beads-25vc.21.5` row 1) and `CHANGELOG.md`'s unreleased `0.2.0` section.

## T-Q1-02 Hash Comparison (worktree bundle -> global mirror, threat register)

Computed the actual `bundle_hash()` from `hooks/capability-auto-install.sh` (path-and-content-inclusive SHA-256 over the bundle tree) against three candidates, and compared each to the stored sidecar `${GSD_HOME:-$HOME}/.gsd/capability-auto-install-sota-numerics.hash`:

| Source | Hash (first 12 hex) | Matches stored? |
|---|---|---|
| Stored sidecar | `da4da96a5d83` | — |
| This worktree's current bundle (`.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics`, post-Task-3) | `a3184d4dc553` | **No** |
| Sibling worktree `.worktrees/sota-numerics-issue-1`'s bundle | `0730d6aae4aa` | No |
| Plugin-cache bundle `~/.claude/plugins/cache/gsd-beads/sota-numerics/{0.1.1,0.1.2,0.1.3}` | `b29534cedfe4`, `ab349a0d9c1b`, `09d8993d7b0b` | No (none of the three) |

**Result: the stored global-mirror hash does NOT equal this worktree's (or the sibling worktree's) bundle hash** — the critical safety property T-Q1-02 exists to check. No leak of this session's edits into the global mirror occurred. Separately, live re-runs of the test suite throughout this task independently confirmed the mirror is untouched: every invocation printed `capability-auto-install: sota-numerics bundle HEAD is not published (not an ancestor of eccad8702...); refusing to install it at global scope` (the dirty-tree/publication guard from commit `6e1d61c`, per `.wolf/buglog.json`'s `gsd-capability-mirror-worktree-leak-20260907` entry).

I could **not** positively identify which bundle the stored hash `da4da96a5d83...` corresponds to — it matched none of the three cached marketplace plugin versions found under `~/.claude/plugins/cache/gsd-beads/sota-numerics/`, nor either sota-numerics worktree's current content. Its provenance is unconfirmed and out of this task's scope to trace further; what is confirmed, positively, is that it is not this session's edits.

## Recorded Dispositions (Task 3)

One bd comment on `gsd-beads-25vc.21.5` records both no-change dispositions:

1. **`hooks/capability-auto-install.sh`'s nine refusal messages** (no refusal-state sidecar): keep current behaviour and prose, unchanged. Basis: the ticket's own framing ("no fix, note only ... low actionability", P4); the retry semantics are already explained in the script's own comment (lines 93-94); the review's own confidence for this finding was 65 (lowest in the review), since the "never reaches the model's context" claim depends on inferred Claude Code hook-stderr-forwarding semantics never verified against the host.
2. **`check-alternatives.py`'s module docstring** — its Exit-2 sentence nests a parenthetical (clause 4) and an em-dash aside (clause 5) inside one five-clause sentence, creating real parse-risk about which clause each aside qualifies. Genuine defect, but out of `.21.5`'s scope (no row in the review, no bullet in the ticket). Filed as standalone issue **`gsd-beads-to0b`** (P3), linked back from `.21.5`'s disposition comment.

`gsd-beads-25vc.21.5` closed with both commit hashes and the disposition summary as the close reason.

## Files Created/Modified

All in `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`:

- `hooks/session-start.sh` — three role `FRAMING` bodies replaced with fragment pointers; comment added above the `case` block naming the failsafe tradeoff.
- `tests/test-session-start.sh` — case3a/case3b assertions (and the case8 manifest-token duplicates) updated to the pointer phrases; a comment added recording the role-uniqueness invariant.
- `CHANGELOG.md` — new paragraph under the unreleased `## 0.2.0` section recording the banner change and the failsafe tradeoff.
- `.gsd/capabilities/sota-numerics/fragments/planner-sota.md` — lines 1, 4, 5, 7 trimmed (rows 2, 3, 5, 4); 11 lines, unchanged count.
- `.gsd/capabilities/sota-numerics/fragments/executor-numerics.md` — line 7 rewritten (row 7, tightened to 398 chars); lines 9-10 merged into one, one clause dropped (row 8); 9 lines.
- `.gsd/capabilities/sota-numerics/fragments/verifier-precision.md` — line 4 split into two (row 9); 8 lines.
- `.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md` — line 1 deleted, line 2 split (row 6); 4 lines.
- `.claude-plugin/plugin.json` — `description` replaced with README.md:3's sentence plus the gate clause (row 10).
- `.gsd/capabilities/sota-numerics/NOTES.md` — section 1's two paragraphs replaced with one paragraph pointing at `capability.json`'s `gates[0].description` (row 13).

In `/home/dd/projects/gsd-beads` (this repo): `.planning/STATE.md` (Quick Tasks Completed row added), this `SUMMARY.md`.

## Decisions Made

See `key-decisions` in frontmatter. In addition: this dispatch's Quick ID (`260908-h0m`) collides with an earlier, distinct, already-completed quick task in the same session (the `.21.4` ponytail-cleanup task, commits `ca6dca2`/`252c2cc`/`2f4d52a`). Both STATE.md rows were preserved rather than the earlier one being overwritten; the new row is labeled `260908-h0m (prose-trims variant)` to disambiguate. This is an upstream ID-generation collision, not something this task's scope covers fixing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] `tests/test-session-start.sh`'s `case8` block asserted the pre-trim banner text, which the plan's stale line-number anchors did not name**
- **Found during:** Task 1, after the RED/GREEN cycle for the plan's own two named assertions.
- **Issue:** `case8` (added to the test suite after this plan was drafted, confirmed by re-verifying against the current HEAD per the `<target_repo_notice>` instruction) independently re-asserts the same banner phrases via the `hooks.json` manifest-token dispatch path, using the old verbatim text (`ranked criterion`, `avoid cancellation`). Editing only the plan's two named assertions would have left the suite red.
- **Fix:** Updated `case8`'s planner/executor assertions to the same pointer phrases (`planner fragment`, `executor fragment`), matching the plan's own uniqueness requirement for the other two assertions.
- **Files modified:** `tests/test-session-start.sh` (same file, same commit as the plan's own Task 1 edits).
- **Verification:** `bash tests/test-session-start.sh` — `ALL PASS`.
- **Committed in:** `a0a66d1`

**2. [Rule 1 - Bug] The plan's own literal `executor-numerics.md` line-7 result text exceeded Task 2's own 400-character `<verify>` gate**
- **Found during:** Task 2, after transcribing the plan's quoted "Result:" text verbatim.
- **Issue:** The plan's specified replacement sentence for row 7 is 431 characters; Task 2's own `<verify>` requires `length($0) > 400` to be false for every line in this file. The plan's quoted text failed its own gate.
- **Fix:** Tightened three clauses with no content or constraint dropped ("an input it cannot resolve at all gets the diagnostic and no fix line" -> "an unresolvable input gets the diagnostic, no fix line"; "signals through its exit code and prints no progress chatter" -> "signals through its exit code, no progress chatter"; "writes the result to a file" -> "writes it to a file"), landing at 398 characters.
- **Files modified:** `.gsd/capabilities/sota-numerics/fragments/executor-numerics.md`.
- **Verification:** `awk 'length($0) > 400 {...}'` over all three fragments — exits 0.
- **Committed in:** `61cc8d2`

---

**Total deviations:** 2 auto-fixed (2 Rule 3/Rule 1)
**Impact on plan:** Both were required for the plan's own stated done-criteria (a green test suite; no fragment line over 400 characters) to hold. No scope creep — no file outside the plan's `files_modified` list was touched, confirmed by `git diff --stat` in Task Commits above.

## Issues Encountered

`bd` command auto-discovery (no `-C`/`--db` flag) was unreliable when invoked from a cwd inside the nested worktree (`.worktrees/sota-numerics-release-013`, itself a separate git repository under the `gsd-beads` tree): some `bd show`/`bd list` calls succeeded, others returned `Error fetching ...: no issue found matching ...` for the identical command. Root cause not diagnosed (out of this task's scope); worked around by always passing `bd -C /home/dd/projects/gsd-beads` for verification reads once the flakiness was observed, and by independently confirming (via `bd -C ... show`) that the writes made while cwd was ambiguous (the `gsd-beads-to0b` issue creation, the two bd comments) landed correctly in the canonical database before relying on them.

## Threat Flags

None. All edits stayed within the plan's declared `<threat_model>` (T-Q1-01 accept, T-Q1-02 mitigate — see above, T-Q1-03 mitigate — see the case3a/case3b uniqueness comment and RED evidence).

## Self-Check: PASSED
