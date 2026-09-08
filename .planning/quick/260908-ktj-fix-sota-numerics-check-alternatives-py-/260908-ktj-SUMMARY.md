---
phase: quick-260908-ktj
plan: 01
subsystem: sota-numerics/plan-gate
tags: [docstring, prose-fix, check-alternatives, parse-risk]
requirements: [gsd-beads-to0b]
dependency-graph:
  requires: []
  provides: ["check-alternatives.py exit-2 docstring, unambiguous scope"]
  affects: ["sota-numerics worktree feat/extended-sota-definition"]
tech-stack:
  added: []
  patterns: ["one declarative sentence per condition; asides hoisted to their own clause"]
key-files:
  created: []
  modified:
    - ".worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py"
decisions:
  - "Kept the plan's exact verbatim replacement paragraph (72/68/75/74/74/76/71 char lines) even though it splits \"not valid\" / \"UTF-8.\" across a line break, which defeats a single-line grep in the plan's own <verify> gate -- content correctness was re-verified with a line-joined grep instead of reflowing the prose."
metrics:
  duration: "~25 minutes"
  completed: "2026-09-08"
actuals:
  tokens: 5500
  tasks: 1
  commits: 1
status: complete
---

# Quick Task 260908-ktj: Fix sota-numerics check-alternatives.py Exit-2 docstring nesting Summary

Split `check-alternatives.py`'s module-docstring Exit-2 statement from one
comma-joined sentence carrying a parenthetical and an em-dash aside into six
declarative sentences with both nestings hoisted into their own clauses, so
a reader can no longer misread the no-`phase_dir` aside as scoping the whole
exit-2 list.

## What Changed

`.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (target repo:
`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch
`feat/extended-sota-definition`), lines 19-24 before the edit. Old text:

> Exit 2 = usage/IO error: an empty, missing or non-directory phase_dir, a
> phase_dir with no `.planning/` ancestor within 10 levels, a discovered plan
> file that is not valid UTF-8 or could not be read (a plan-shaped name that
> names a directory, for instance), or -- when no phase_dir is given -- a
> STATE.md whose frontmatter `current_phase` and `## Current Position`
> `Phase:` line do not corroborate each other.

New text (own paragraph, six sentences, no `(` and no ` -- `):

> Exit 2 = usage/IO error. Any of five conditions raises it. The phase_dir
> argument is empty, missing, or not a directory. The phase_dir has no
> `.planning/` ancestor within 10 levels. A discovered plan file is not valid
> UTF-8. A discovered plan file could not be read at all; a plan-shaped name
> that names a directory is the usual cause. No phase_dir was given, and the
> STATE.md the phase resolves from carries a frontmatter `current_phase` and a
> `## Current Position` `Phase:` line that do not corroborate each other.

All five conditions preserved with identical content. Every line after the
docstring's closing `"""` is byte-identical to both `ce855f9` and HEAD
(`f46ebc3`) at edit time -- confirmed those two are themselves body-identical
below the docstring before editing, so gating against either is equivalent.

Commit: `85ee8e4` on `feat/extended-sota-definition`
(`docs(check-alternatives): split exit-2 statement into one sentence per
condition`) -- one file, 9 insertions, 6 deletions.

## Baseline Drift (disclosed, expected)

The plan's `<precondition>` and `<target_repo>` sections state the worktree
is "clean at `ce855f9`". Actual HEAD at task start was `f46ebc3`, 16 commits
ahead (this session's earlier quick tasks), per the dispatch's
`<target_repo_notice>`. Verified before editing that `ce855f9` and `f46ebc3`
are body-identical below the docstring's closing `"""`, so the plan's
byte-identity gate against `ce855f9` and a gate against HEAD are equivalent
in this case. `git diff --stat ce855f9` (post-commit) names 4 files because
it spans all 16 intervening commits, not just this task's edit; `git diff
--stat HEAD` (the correct pre-edit baseline) names exactly 1 file, matching
the plan's actual intent.

## Plan-Time Findings Re-verification (Step 1)

- `grep -rn "__doc__" tests/ .gsd/` (excluding `__pycache__`): zero output.
  No test pins the docstring's wording.
- Five distinctive exit-2 phrases grepped repo-wide (excluding `.git`,
  `__pycache__`): all five hit `check-alternatives.py` only, with one
  expected near-miss -- `tests/test_check_alternatives.py:1802` contains the
  words "usage/IO error" inside a source *comment*
  (`# remediation: line (this is a usage/IO error, not a plan violation).`),
  not an assertion on the docstring. Confirmed by direct read of that line.

Both plan-time findings held; no STOP triggered.

## Verification Results

- **Full suite:** `python3 -m unittest tests/test_check_alternatives.py` ->
  `Ran 131 tests` / `OK`, both before and after the edit. Zero test-file
  edits.
- **Byte-identity gate:** `diff <(git show ce855f9:$F | awk 'f;
  /^"""$/{f=1}') <(awk 'f; /^"""$/{f=1}' $F)` -> empty diff (identical),
  confirmed both pre-edit (as a baseline check) and post-edit.
- **Corpus verdicts** (`.planning/phases/19*` .. `24*` run through the
  edited checker): `1 …/19-…`, `0 …/20-…`, `0 …/21-…`, `1 …/22-…`,
  `0 …/23-…`, `0 …/24-…` -- matches the recorded baseline exactly, both
  pre-edit and post-edit.
- **Diff shape:** `git diff --stat HEAD` (pre-edit HEAD, the correct
  baseline given the drift above) names exactly one file, 9
  insertions/6 deletions, all inside the module docstring.
- **D-17 auto-install hash sidecar:** `~/.gsd/capability-auto-install-sota-numerics.hash`
  = `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498`,
  unchanged before and after the commit. Cross-checked directly: the
  plugin-cache mirror (`~/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`,
  sha256 `5df208bc...`) still holds the *old* content, distinct from the
  worktree's now-edited file (sha256 `7164b95b...`) -- confirming no
  `capability-auto-install.sh` re-install fired during this task (no
  subagent spawn occurred), so the bundle mirror and its hash sidecar
  legitimately stayed put. This is the intentional, disclosed touch to the
  bundle path named in the dispatch notice; it did not trigger a
  re-publish.
- **Worktree state:** `git status --short` clean, `git log --oneline -1`
  shows the single new commit `85ee8e4` on `feat/extended-sota-definition`.
  Branch not pushed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's own `<verify>` gate has a line-wrap blind spot,
not a bug in the edit**
- **Found during:** running the plan's literal `<verify>` command after
  applying the exact-verbatim replacement paragraph.
- **Issue:** The plan's specified replacement text (character counts
  72/68/75/74/74/76/71, given as already "dry-run... and passes the
  `<verify>` gate below") splits the phrase "not valid" / "UTF-8." across a
  line break. The `<verify>` command captures the paragraph via
  `$(sed -n ...)` (which preserves embedded newlines) and then runs
  `grep -q 'not valid UTF-8'` against it. `grep` matches per line by
  default, so a phrase split by an embedded newline can never match --
  confirmed empirically (`printf 'a is not valid\nUTF-8. done\n' | grep -q
  'not valid UTF-8'` -> no match). This is a defect in the plan's own check
  script, not in the docstring text: the plan's claim that this exact
  wrapping "passes the `<verify>` gate below" does not hold as literally
  written.
- **Fix:** Applied the plan's exact-verbatim replacement paragraph unchanged
  (did not reflow the prose, since the character-count list and "verbatim"
  instruction are the authoritative content). Re-ran the five phrase checks
  with lines joined by a space (`tr '\n' ' '` before `grep`) to confirm the
  actual intent -- all five conditions' key phrases are present. Also
  reconfirmed the full suite, byte-identity, corpus verdicts, line-length
  cap, and one-file diff shape independently (see Verification Results
  above), so the task's `<done>` criteria are all independently satisfied
  despite the literal `<verify>` one-liner's line-wrap blind spot.
- **Files modified:** none beyond the planned single file; this deviation
  is about how verification was run, not what was edited.
- **Commit:** `85ee8e4` (the content commit; no separate commit for this
  deviation, it is a verification-method note only).

No other deviations. No scope creep: `README.md`, `CHANGELOG.md`, and every
function docstring in `check-alternatives.py` are untouched. No condition
added, removed, merged, or re-scoped.

## Follow-up

No follow-up `bd` issue filed. The task's scope-bound note asked to file one
only "if you believe [README.md/CHANGELOG.md/function docstrings] also need
this treatment" -- none of those carry the same nested-aside ambiguity, so
none is filed.

## Self-Check: PASSED

- `.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`: FOUND, content verified via direct read post-edit.
- Commit `85ee8e4`: FOUND in target repo's `git log --oneline --all`.
- bd ticket `gsd-beads-to0b`: closed with acceptance-criteria evidence.
