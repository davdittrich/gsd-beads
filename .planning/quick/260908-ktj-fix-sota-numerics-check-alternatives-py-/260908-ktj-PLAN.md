---
phase: quick-260908-ktj
plan: 01
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [gsd-beads-to0b]
beads_epic: gsd-beads-to0b
quick_id: 260908-ktj
slug: fix-sota-numerics-check-alternatives-py-
date: 2026-09-08
target_repo: /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013
target_branch: feat/extended-sota-definition
files_modified:
  - .gsd/capabilities/sota-numerics/scripts/check-alternatives.py

estimate:
  tokens: 26000
  raw_tokens: 26000
  tasks: 1
  confidence: low

must_haves:
  truths:
    - "A reader of `check-alternatives.py`'s module docstring can tell, without re-reading, that `-- when no phase_dir is given --` qualifies the STATE.md corroboration condition ONLY, and not the other four exit-2 conditions (gsd-beads-to0b)."
    - "A reader can tell that the directory-named-like-a-plan aside qualifies the could-not-be-read condition ONLY, and not the not-valid-UTF-8 condition it currently shares a clause with (gsd-beads-to0b)."
    - "All five exit-2 conditions still appear, with the same content: empty/missing/non-directory phase_dir; no `.planning/` ancestor within 10 levels; plan file not valid UTF-8; plan file could not be read; STATE.md `current_phase` and `## Current Position` `Phase:` disagree."
    - "The exit-2 paragraph contains no ` -- ` aside and no `(` parenthetical — both nestings are hoisted into their own clauses, so scope is syntactically unambiguous rather than inferred."
    - "Behaviour is byte-identical: every line of `check-alternatives.py` after the module docstring's closing `\"\"\"` matches HEAD exactly."
    - "`python3 -m unittest tests/test_check_alternatives.py` still runs 131 tests and reports OK, with zero test-file edits."
    - "The gsd-beads plan corpus still yields the same six verdicts as the pre-change baseline (19->1, 20->0, 21->0, 22->1, 23->0, 24->0)."
  artifacts:
    - "`.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` module docstring, exit-2 statement rewritten as one declarative sentence per condition (currently lines 19-24)."
    - "One commit on `feat/extended-sota-definition` in the target repo, touching exactly one file."
    - "`.planning/quick/260908-ktj-fix-sota-numerics-check-alternatives-py-/260908-ktj-SUMMARY.md` in the WORKING repo."
  key_links:
    - "module docstring exit-2 statement <-> `main()`'s `return 2` arms <-> `README.md` lines 191-207 — the docstring is the compressed statement of the contract the README states in full; this plan changes the compressed statement's PROSE only, so the three stay in agreement without touching the other two."
    - "commit 2f4d52a (`test(checker): drop the circular docstring self-match assertions`) <-> `tests/test_check_alternatives.py` — that commit is why no test pins this docstring's wording; the task re-verifies rather than trusting the claim."
---

<objective>
Rewrite the exit-2 statement in `check-alternatives.py`'s module docstring so
that its five conditions read as five separate sentences and its two nested
asides are hoisted into their own clauses, closing `gsd-beads-to0b`.

Purpose: today the five conditions are one comma-joined sentence carrying a
parenthetical inside its fourth clause and an em-dash-bounded aside inside its
fifth. On a fast read it is not decidable whether the fifth aside scopes the
whole exit-2 list or only the STATE.md condition. That is a real parse-risk
defect in the prose contract a reader of this script meets first.

Output: one atomic commit in the sota-numerics worktree containing a docstring
rewrite and nothing else.

**Non-goal — read this before you start.** This is a clarity rewrite, not a
content change and not a behaviour change. The ticket states it outright: "the
code's actual exit-2 branches are unaffected." Do not add, remove, merge or
re-scope any condition. Do not touch `README.md` (its exit-code section at
lines 191-207 is already the fuller, unnested statement and is not what the
ticket names). Do not add a `CHANGELOG.md` entry: that section's framing is
"which verdicts change and why", and no verdict changes here.
</objective>

<target_repo>
## READ THIS BEFORE TOUCHING ANY FILE

**The code lives in a DIFFERENT repository from the one you are running in.**

- Working repo (where this PLAN.md and its SUMMARY.md live):
  `/home/dd/projects/gsd-beads`
- **Target repo (where the ONE file edit in this plan happens):**
  `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`
  — a checkout of `https://github.com/davdittrich/sota-numerics.git`,
  branch `feat/extended-sota-definition`, clean at `ce855f9`
  (past the 15 commits from this session's earlier quick tasks).

The single path in `<files>` below is **relative to the target repo**.
`.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` means
`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`,
NOT any path under `/home/dd/projects/gsd-beads/.gsd/`.

The commit is made **in the target repo**, on `feat/extended-sota-definition`.
Do not commit code changes to the working repo. The only artifact that belongs
in the working repo is this plan's `260908-ktj-SUMMARY.md`, written beside this
file.

Do not push. Do not open a PR. Landing on the branch is the whole deliverable.

## Worktree hazard (recorded project rule — read before your first edit)

This worktree lives inside the gsd-beads project tree and carries its own
`.claude-plugin/plugin.json`, so its `hooks/hooks.json` SubagentStart hook runs
`capability-auto-install.sh` on the next agent spawn. `6e1d61c` ("fix(hooks):
refuse global auto-install of a dirty bundle") is an ancestor of HEAD, so an
install is refused while the worktree is dirty; the residual is the moment
**after** the commit, when a clean worktree holds an unreleased bundle.

Baseline recorded at plan time (2026-09-08):

```
$ cat ~/.gsd/capability-auto-install-sota-numerics.hash
da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498
```

Re-read it at the end. **If it changed, STOP and report it in the SUMMARY** —
an uncommitted worktree bundle has been installed machine-wide. Do not attempt
remediation; that is outside this plan's scope.
</target_repo>

<context>
@/home/dd/projects/gsd-beads/CLAUDE.md
@/home/dd/projects/gsd-beads/.planning/STATE.md

Target-repo source — read ONE region, not the whole 945-line file:

- `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` lines 1-32
  (the module docstring). Lines 19-24 are the statement this plan rewrites;
  lines 11-18 are the Exit 0 / Exit 1 statement whose style it must match.
  Line 32 is the docstring's closing `"""` — the only line in the file matching
  `^"""$`, which the byte-identity check below relies on.

Ticket detail (exact prose of the finding and its suggested fix):
`bd show gsd-beads-to0b`

Do NOT read `tests/test_check_alternatives.py` (2000+ lines) up front. Task 1's
first step is a two-command grep that answers the only question this plan has
about it.
</context>

<baselines>
Captured 2026-09-08 in the target repo at `ce855f9`, worktree clean, before
any edit. Every one must still hold after the task.

```
$ python3 -m unittest tests/test_check_alternatives.py
Ran 131 tests in 3.998s
OK

$ awk 'f; /^"""$/{f=1}' .gsd/capabilities/sota-numerics/scripts/check-alternatives.py | wc -l
913

$ S=.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py
$ (cd /home/dd/projects/gsd-beads && for d in .planning/phases/19* .planning/phases/2[0-4]*; do python3 "$S" "$d" >/dev/null 2>&1; echo "$? $d"; done)
1 .planning/phases/19-native-resolver-contract-and-failure-boundary
0 .planning/phases/20-additive-identity-migration-and-compatibility
0 .planning/phases/21-installed-cutover-and-patch-2-retirement
1 .planning/phases/22-capability-projection-reconciliation
0 .planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin
0 .planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers
```
</baselines>

<plan_time_findings>
Two facts established while writing this plan. The task re-verifies both rather
than trusting them.

1. **No test pins this docstring's wording.** `grep -rn "__doc__" tests/ .gsd/`
   returns zero hits (excluding `__pycache__`). Each of the five phrases
   distinctive to the exit-2 statement — `usage/IO error`, `no phase_dir is
   given`, `plan-shaped name that names a directory`, `corroborate each other`,
   `Gate script for the sota-numerics` — appears in exactly one place in the
   repo: `check-alternatives.py` itself. The one near-miss,
   `tests/test_check_alternatives.py:1802`, is a source comment containing the
   words `usage/IO error`, not an assertion.

2. **`test_readme_and_planner_name_exact_mixed_contract` still exists** at
   `tests/test_check_alternatives.py:493` and does NOT need updating. Commit
   `2f4d52a` ("test(checker): drop the circular docstring self-match
   assertions") already relaxed it: what remains asserts that `README.md` and
   `.gsd/capabilities/sota-numerics/fragments/planner-sota.md` both carry the
   `### Internal design alternatives` marker and the internal-entries contract
   sentence. Neither string is in the module docstring.

   The `docstring still applies` comment at
   `tests/test_check_alternatives.py:1254` refers to `mask_fenced_regions`'
   FUNCTION docstring, not the module docstring. Out of scope; do not touch it.

Consequence: this plan modifies zero test files and expects the suite to stay
green at 131 tests unchanged. If step 1 of the task contradicts either finding,
stop and report before editing.
</plan_time_findings>

<tasks>

<task type="auto">
  <name>Task 1: Split the exit-2 statement into one sentence per condition</name>
  <files>.gsd/capabilities/sota-numerics/scripts/check-alternatives.py</files>
  <precondition>The target repo is clean at `ce855f9` on `feat/extended-sota-definition` (`git -C /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 status --short` prints nothing).</precondition>
  <action>
    Work in the target repo named in `<target_repo>`. Every command below runs
    with that directory as cwd.

    **Step 1 — confirm no test pins the wording (two commands, before editing).**
    Run `grep -rn "__doc__" tests/ .gsd/ | grep -v __pycache__` and expect zero
    output. Then grep the repo, excluding `.git` and `__pycache__`, for each of
    the five distinctive exit-2 phrases listed in `<plan_time_findings>` and
    expect each to hit `check-alternatives.py` only. If either expectation
    fails, STOP and report in the SUMMARY — a test pinning this wording changes
    the shape of the work and needs the developer's call before you proceed.

    **Step 2 — apply the rewrite.** Replace the docstring text that currently
    runs from `Exit 2 = ` (mid-line 19) through the end of line 24 with the
    exact paragraph below, made its own paragraph by ending line 18's sentence
    at `(D-07).` and inserting a blank line after it. No line of the
    replacement paragraph may exceed 76 characters. Do not reflow anything
    else — docstring line 6 is 78 characters and stays exactly as it is.

    Exact replacement paragraph, verbatim (this exact wrapping was dry-run at
    plan time against a scratch copy and passes the `<verify>` gate below; the
    seven lines measure 72/68/75/74/74/76/71 characters):

    Exit 2 = usage/IO error. Any of five conditions raises it. The phase_dir
    argument is empty, missing, or not a directory. The phase_dir has no
    `.planning/` ancestor within 10 levels. A discovered plan file is not valid
    UTF-8. A discovered plan file could not be read at all; a plan-shaped name
    that names a directory is the usual cause. No phase_dir was given, and the
    STATE.md the phase resolves from carries a frontmatter `current_phase` and a
    `## Current Position` `Phase:` line that do not corroborate each other.

    Why this exact shape, so you do not "improve" it back into the defect:
    each condition is a full declarative sentence rather than a comma-joined
    clause, so no condition can be read as governing another; the
    directory-named-like-a-plan aside becomes a semicolon clause attached to
    the could-not-be-read sentence, so it can no longer be read as also
    qualifying the not-valid-UTF-8 condition it used to share a clause with;
    and the no-phase_dir condition leads its own sentence as a conjoined
    fact, so it cannot be read as scoping the whole list. That third change is
    the ticket's actual complaint.

    This also removes the 89-character overflow on line 19, which is the
    artefact of the old statement starting mid-line.

    Nothing else in the file changes: not one character below the docstring's
    closing `"""` (line 32 before the edit; it shifts down by two lines after,
    since the rewrite adds a blank line and one line of prose).

    Scope bound: `README.md`, `CHANGELOG.md`, `tests/`, and every function
    docstring in this file are out of scope. If you believe one of them also
    needs this treatment, say so in the SUMMARY and file a follow-up `bd`
    issue rather than widening the diff.
  </action>
  <verify>
    <automated>(cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && F=.gsd/capabilities/sota-numerics/scripts/check-alternatives.py && diff <(git show HEAD:$F | awk 'f; /^"""$/{f=1}') <(awk 'f; /^"""$/{f=1}' $F) && test "$(git diff --name-only | wc -l)" = 1 && P=$(sed -n '/^Exit 2 = /,/^$/p' $F) && test -n "$P" && test "$(printf '%s' "$P" | grep -cE ' -- |\(')" = 0 && test "$(printf '%s' "$P" | grep -o '\. ' | wc -l)" -ge 5 && printf '%s' "$P" | grep -q 'empty, missing, or not a directory' && printf '%s' "$P" | grep -q 'ancestor within 10 levels' && printf '%s' "$P" | grep -q 'not valid UTF-8' && printf '%s' "$P" | grep -q 'could not be read' && printf '%s' "$P" | grep -q 'corroborate each other' && test "$(printf '%s\n' "$P" | awk 'length > 76' | wc -l)" = 0 && python3 -m unittest tests/test_check_alternatives.py 2>&1 | tail -3 | grep -q '^OK$' && echo VERIFY_OK)</automated>
  </verify>
  <done>
    The exit-2 statement is its own paragraph of six sentences; that paragraph
    carries no ` -- ` aside and no `(` parenthetical; all five conditions are
    still stated; every line after the docstring's closing `"""` is
    byte-identical to `ce855f9`; the suite still runs 131 tests OK with zero
    test-file edits; the change is one commit in the target repo touching one
    file.
  </done>
</task>

</tasks>

<verification>
Run all of these from the target repo before writing the SUMMARY.

1. Full suite, the exact command CI runs (`.github/workflows/ci.yml`, the
   `alternatives-checker unit test` step):

   ```bash
   (cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 \
     && python3 -m unittest tests/test_check_alternatives.py)
   ```

   Must report `Ran 131 tests` and `OK`. Not 130, not 132 — this plan adds and
   removes no tests.

2. Behaviour byte-identity — the check that makes this a prose change:

   ```bash
   (cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 \
     && F=.gsd/capabilities/sota-numerics/scripts/check-alternatives.py \
     && diff <(git show ce855f9:$F | awk 'f; /^"""$/{f=1}') <(awk 'f; /^"""$/{f=1}' $F) \
     && echo "code body identical")
   ```

3. Corpus verdicts unchanged against the recorded baseline:

   ```bash
   (cd /home/dd/projects/gsd-beads \
     && S=.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py \
     && for d in .planning/phases/19* .planning/phases/2[0-4]*; do \
          python3 "$S" "$d" >/dev/null 2>&1; echo "$? $d"; done)
   ```

   Must print exactly `1 …/19-…`, `0 …/20-…`, `0 …/21-…`, `1 …/22-…`,
   `0 …/23-…`, `0 …/24-…`.

4. Diff shape: `git diff --stat ce855f9` names exactly one file, and every
   changed line falls inside the module docstring.

5. Worktree hazard check:

   ```bash
   cat ~/.gsd/capability-auto-install-sota-numerics.hash
   ```

   Must still be
   `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498`.
   If it changed, say so in the SUMMARY and stop.

6. `git -C /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 status --short`
   is clean and `git log --oneline -1` shows the one commit on
   `feat/extended-sota-definition`.
</verification>

<success_criteria>
- `gsd-beads-to0b` is closed by a landed fix: both nestings the ticket names
  are hoisted out, and the five conditions read as five sentences.
- One commit on `feat/extended-sota-definition` in the target repo, touching
  exactly `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`.
- Zero test-file edits; suite green at 131 tests; corpus verdicts identical to
  the recorded baseline; code body byte-identical to `ce855f9`.
- No scope creep: `README.md` and `CHANGELOG.md` untouched, no function
  docstring touched, no condition added, removed, merged or re-scoped.
- The SUMMARY records the two `<plan_time_findings>` re-verification results,
  the auto-install hash check, and any follow-up `bd` issue filed.
</success_criteria>

## Alternatives Considered

Mechanism choice: how to state five exit-2 conditions in a module docstring so
that a nested qualifier cannot be misread as scoping the list.

- **One short declarative sentence per condition, asides hoisted to their own
  clauses** (chosen). Doc-ref: the Exit 0 / Exit 1 statement immediately above
  it, `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` lines
  11-18 (target repo at `ce855f9`, 2026-09-08), which already states its own
  conditions this way. One paragraph rewritten, no new structure, and the
  ticket's own suggested fix.

- **A bulleted list inside the docstring**, one `- ` item per condition.
  Doc-ref: `README.md` lines 191-207 (target repo at `ce855f9`, 2026-09-08),
  which uses exactly that shape for the same contract and proves it reads
  well. Rejected: this module's docstring is unbroken prose end to end, and
  every function docstring in the file follows suit. A list here makes the
  exit-2 case structurally unlike the Exit 0 / Exit 1 statement one line above
  it, and invites the README's fuller enumeration to be copied in — the
  duplication commit `2f4d52a` and `252c2cc` spent this session removing.

- **Delete the enumeration from the docstring and point at the README's
  exit-code section.** Doc-ref: `README.md` lines 191-207 (target repo at
  `ce855f9`, 2026-09-08). Rejected: the docstring is what a reader of the
  script meets first, and after `2f4d52a` dropped the circular self-match
  assertions it is the only in-module statement of the contract. A pointer
  costs a file hop, and the README's version is scoped to the CLI surface
  rather than to the module.

- **Leave it and document the ambiguity** (the null option). Rejected: the
  ticket records a measured parse-risk in a contract statement, and the fix is
  one paragraph.

Decided by: simplicity — the chosen shape is the smallest edit that removes
both nestings, introduces no structure the file does not already use, and
leaves the five conditions' content and the docstring's paragraph form
identical to the Exit 0 / Exit 1 statement it sits beside. Performance is not a
discriminator (docstring prose, zero runtime effect); maintenance favours the
chosen option for the same reason it wins on simplicity — no second format to
keep in sync.

<output>
Write `.planning/quick/260908-ktj-fix-sota-numerics-check-alternatives-py-/260908-ktj-SUMMARY.md`
in the WORKING repo (`/home/dd/projects/gsd-beads`), not the target repo, when
done. Record: the commit SHA, the two `<plan_time_findings>` re-verification
results, the final test count, the post-change corpus verdict table, the
byte-identity diff result, the auto-install hash check, and any follow-up `bd`
issue filed.
</output>
