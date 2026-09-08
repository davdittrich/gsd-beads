---
phase: quick-260908-gzq
plan: 01
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [gsd-beads-25vc.21.1]
beads_epic: gsd-beads-25vc.21.1
quick_id: 260908-gzq
slug: fix-sota-numerics-check-alternatives-py-
date: 2026-09-08
target_repo: /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013
target_branch: feat/extended-sota-definition
files_modified:
  - .gsd/capabilities/sota-numerics/scripts/check-alternatives.py
  - tests/test_check_alternatives.py
  - README.md
  - CHANGELOG.md
estimate:
  tokens: 58000
  raw_tokens: 58000
  tasks: 3
  confidence: low
must_haves:
  truths:
    - "A plan whose prose contains a backticked comment opener (``We discuss `<!--` markers here.``) above a compliant `## Alternatives Considered` section exits 0 — the inline code span is rendered page content, so it no longer blanks the rest of the document to EOF."
    - "A real `<!--` on a line that also carries an unrelated inline code span still masks: an entry commented out after a `` `numpy` `` mention is still invisible to the gate."
    - "An unterminated backtick before a comment opener still masks to EOF (exit 1, `missing '## Alternatives Considered' section`) — the fail-closed residual is preserved, not widened."
    - "A symlinked entry under `.planning/phases/` is never selected as the current phase directory: `ln -s $OUTSIDE .planning/phases/16-sym` with `current_phase: 16` exits 2 with `matches 0 directories`, and no path under `$OUTSIDE` appears on stderr."
    - "A real (non-symlink) phase directory still resolves through the same loop — the existing `TestCurrentPhaseResolution` cases keep their verdicts."
    - "A directory named `11-01-PLAN.md` exits 2 with a single `check-alternatives.py: <path>: ...` line and no Python traceback on stderr, replacing the raw `IsADirectoryError` crash the module docstring's `<plan_path>:<line>:` contract never promised."
    - "The gsd-beads corpus verdicts are byte-identical to the pre-change baseline: phases 19→1, 20→0, 21→0, 22→1, 23→0, 24→0."
    - "`python3 -m unittest tests/test_check_alternatives.py` passes, with no test count lower than the 125-test baseline."
  artifacts:
    - "`next_comment_opener(text, pos)` helper in `check-alternatives.py`, sited next to `next_fence_opener` (line 406)"
    - "An inline-code-span constant in `check-alternatives.py` used only by `next_comment_opener`"
    - "`not entry.is_symlink()` in the phase-match loop at `check-alternatives.py:373`"
    - "`except OSError` arm in `validate_plan` (`check-alternatives.py:743`) re-raising as `ValueError`"
    - "New tests in `tests/test_check_alternatives.py::TestHtmlComments` (backtick-span cases)"
    - "New symlink test in `tests/test_check_alternatives.py::TestCurrentPhaseResolution`"
    - "`tests/test_check_alternatives.py::TestUnreadablePlanFiles` rewritten: renamed test + rewritten class docstring"
    - "`README.md` exit-code section updated (the `2:` bullet and the `Other unexpected filesystem errors` paragraph at line 205)"
    - "`CHANGELOG.md` `## 0.2.0` entries for the three behaviour changes"
  key_links:
    - "`mask_fenced_regions` -> `next_comment_opener` -> inline-code-span constant (the whole of finding 1 flows through this one call site, replacing `text.find(HTML_COMMENT_OPEN, pos)` at line 504)"
    - "`resolve_current_phase_dir` -> `phases_root.iterdir()` -> `entry.is_dir() and not entry.is_symlink()` (line 373) -> `matches` (the traversal boundary)"
    - "`check_alternatives` -> `validate_plan` -> `path.read_text` -> `except OSError` -> `ValueError` -> `main()`'s existing exit-2 mapping (line 868)"
    - "`README.md` line 205 <-> `TestUnreadablePlanFiles` <-> `validate_plan`'s except arms — the three that must move together, and the reason this was deferred out of 24-08"
---

<objective>
Close the three low-severity fail-closed edge cases in sota-numerics'
`check-alternatives.py` recorded on `gsd-beads-25vc.21.1`: a backticked `<!--`
inside inline code blanking a plan to EOF, a symlinked phase directory escaping
the `.planning` tree during phase discovery, and a directory named like a plan
crashing with a raw `IsADirectoryError` traceback.

Purpose: all three are diagnostics/correctness defects, not gate bypasses. Two
of them make the gate lie about a compliant plan; the third breaks the module
docstring's stderr contract. They were deferred out of phase 24-08's bounded
`files_modified` list rather than rushed; this plan is the "future plan" the
ticket names.

Output: three atomic commits in the sota-numerics worktree, each carrying its
fix, its test, and (for the third) the README and CHANGELOG lines that pin the
behaviour it changes.
</objective>

<target_repo>
## READ THIS BEFORE TOUCHING ANY FILE

**The code lives in a DIFFERENT repository from the one you are running in.**

- Working repo (where this PLAN.md and its SUMMARY.md live):
  `/home/dd/projects/gsd-beads`
- **Target repo (where EVERY code, test and doc edit in this plan happens):**
  `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`
  — a checkout of `https://github.com/davdittrich/sota-numerics.git`,
  branch `feat/extended-sota-definition`, currently clean at `c8c8a1b`
  (past phase-24 plans 01-08).

Every path in every `<files>` block below is **relative to the target repo**.
`.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` means
`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`,
NOT any path under `/home/dd/projects/gsd-beads/.gsd/`.

All three commits are made **in the target repo**, on
`feat/extended-sota-definition`. Do not commit code changes to the working
repo. The only artifact that belongs in the working repo is this plan's
`260908-gzq-SUMMARY.md`, written beside this file.

Do not push. Do not open a PR. Landing on the branch is the whole deliverable.

## Worktree hazard (recorded project rule — read before your first edit)

This worktree lives inside the gsd-beads project tree and carries its own
`.claude-plugin/plugin.json`, so its `hooks/hooks.json` SubagentStart hook runs
`capability-auto-install.sh` on the next agent spawn.

Half of this is already mitigated: `6e1d61c` ("fix(hooks): refuse global
auto-install of a dirty bundle") is an ancestor of HEAD, so an install is
refused while the worktree is dirty. The residual is the moment **after** each
task commits — a clean worktree holding an unreleased bundle is installable —
so the check below still matters, and matters most between commits.

Before your first edit, record the current value:

```bash
cat ~/.gsd/capability-auto-install-sota-numerics.hash
# baseline at plan time: da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498
```

Re-read it at the end of the plan. **If it changed, STOP and report it in the
SUMMARY** — an uncommitted worktree bundle has been installed machine-wide.
Do not attempt remediation; that is outside this plan's scope.
</target_repo>

<context>
@/home/dd/projects/gsd-beads/CLAUDE.md
@/home/dd/projects/gsd-beads/.planning/STATE.md

Target-repo sources (read the named regions, not the whole files — the script
is 894 lines, the test file 2010):

- `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`
  - module docstring, lines 1-32 (the exit-code contract this plan changes)
  - `DOC_REF_RE` line 147, `HTML_COMMENT_OPEN`/`CLOSE` lines 197-198
  - `resolve_current_phase_dir` line 280, phase-match loop lines 368-379
  - `next_fence_opener` line 406, `fence_close` line 416
  - `mask_fenced_regions` line 460, its scan loop lines 500-514
  - `validate_plan` line 743, its `read_text` + `except UnicodeDecodeError`
    lines 752-762
  - `main()` line 834, its `except ValueError -> return 2` at lines 869-871
- `tests/test_check_alternatives.py`
  - helpers `scratch_dir`/`run_check`/`write_plan`/`fixture_text` lines 41-68
  - `TestHtmlComments` line 1168
  - `TestCurrentPhaseResolution` line 1239, `build_project` line 1249,
    `run_no_arg` line 1263
  - `TestUnreadablePlanFiles` line 1674 (class docstring 1675-1681,
    `test_directory_named_like_a_plan_exits_1` 1697-1705)
- `README.md` lines 189-205 (the exit-code list and the paragraph after it)
- `CHANGELOG.md` `## 0.2.0` section (unreleased — no git tags exist yet, so
  0.2.0's entries are still editable rather than append-only history)

Ticket detail (three findings, exact locations, acceptance criteria):
`bd show gsd-beads-25vc.21.1`
</context>

<baselines>
Captured 2026-09-08 at `c8c8a1b`, before any edit. Every one must still hold
after all three tasks.

```
$ (cd <target repo> && python3 -m unittest tests/test_check_alternatives.py)
Ran 125 tests ... OK

$ S=.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py
$ for d in .planning/phases/19* .planning/phases/2[0-4]*; do python3 "$S" "$d" >/dev/null 2>&1; echo "$? $d"; done
1 .planning/phases/19-native-resolver-contract-and-failure-boundary
0 .planning/phases/20-additive-identity-migration-and-compatibility
0 .planning/phases/21-installed-cutover-and-patch-2-retirement
1 .planning/phases/22-capability-projection-reconciliation
0 .planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin
0 .planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers
```

All three findings reproduce against `c8c8a1b`; each task below states its
own reproduction.
</baselines>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Stop a backticked comment opener from blanking the plan to EOF</name>
  <files>.gsd/capabilities/sota-numerics/scripts/check-alternatives.py, tests/test_check_alternatives.py</files>
  <behavior>
    Add to `TestHtmlComments` (line 1168), written and run RED before the fix:
    - A plan whose body is ``We discuss `<!--` markers here.`` followed by a
      compliant `## Alternatives Considered` section exits 0. (Against
      `c8c8a1b` this exits 1 with `missing '## Alternatives Considered'
      section` — reproduce that first.)
    - A line carrying an unrelated inline code span AND a real comment opener
      (`` Uses `numpy`. <!-- ``) that comments out the section's entries still
      masks them: the gate still reports a violation. This is the assertion
      that stops the fix from becoming a bypass.
    - An unterminated backtick before an opener (`` `a <!-- ``) still masks to
      EOF and exits 1. The fail-closed residual stays.
    - A `<!--` inside a fenced code block is still masked by the fence path
      (whichever opener starts first wins) — add or extend a case so the
      precedence rule is pinned, not incidentally true.
  </behavior>
  <action>
    Replace the bare `comment = text.find(HTML_COMMENT_OPEN, pos)` at line 504
    inside `mask_fenced_regions` with a `next_comment_opener(text, pos)` helper
    sited next to `next_fence_opener` (line 406), mirroring its shape and
    returning an offset (or -1) so the surrounding loop's `pos`/comparison
    semantics at lines 505-512 are untouched.

    `next_comment_opener` walks `str.find` candidates and skips any candidate
    that falls inside an inline code span on its own line: slice the candidate's
    line with `text.rfind("\n", 0, cand) + 1` and `text.find("\n", cand)`, run
    the inline-code regex over that slice, and if any match covers the
    candidate, resume the search at `cand + len(HTML_COMMENT_OPEN)`.

    Use a single-backtick, same-line, bounded span pattern of the shape
    `` `[^`\n]{1,300}` `` (the shape `DOC_REF_RE` at line 147 already uses).
    Give it its own name and comment rather than reusing `DOC_REF_RE`, whose
    job is citation detection. Do NOT use a backreferenced `` (`+)[^\n]*?\1 ``
    variable-length-delimiter form: this module's whole regex discipline is
    anchored, no-nested-quantifier, no-backtracking, and matching CommonMark's
    full code-span rule is not worth breaking it for.

    Document the residual in `mask_fenced_regions`' docstring beside its
    existing fail-closed note (lines 480-483): CommonMark permits a code span
    to cross a line break, and this same-line scan does not see that case — it
    still masks to EOF, the fail-closed direction. The ticket's P2-1 offers
    "fix OR document"; this delivers the fix and documents only what the fix
    does not reach.

    Direction check before you commit: this change only ever UNMASKS. Anything
    it unmasks is text CommonMark renders on the page, which is exactly what
    the docstring says the gate must read ("What the rendered plan does not
    say, the gate must not read" — the converse holds too).
  </action>
  <verify>
    <automated>(cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && python3 -m unittest tests.test_check_alternatives.TestHtmlComments tests.test_check_alternatives.TestFencedRegions tests.test_check_alternatives.TestIndentedCodeBlocks)</automated>
  </verify>
  <done>
    The four behaviours above pass; `TestFencedRegions` and
    `TestIndentedCodeBlocks` are unchanged and still green; committed to the
    target repo as one commit naming the finding.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Skip symlinked entries during phase-directory discovery</name>
  <files>.gsd/capabilities/sota-numerics/scripts/check-alternatives.py, tests/test_check_alternatives.py</files>
  <behavior>
    Add to `TestCurrentPhaseResolution` (line 1239), using its existing
    `build_project` (line 1249) and `run_no_arg` (line 1263) helpers, RED
    before the fix:
    - A project whose `.planning/phases/16-sym` is a symlink to a directory
      OUTSIDE `.planning/` (create the target inside the same `scratch_dir()`
      root so `tearDownModule`'s empty-TMPDIR assertion still holds), holding a
      `11-01-PLAN.md`, with `current_phase: 16` corroborated by the
      `## Current Position` line, exits 2 and reports `matches 0 directories`.
    - The same run prints no path under the symlink target on stderr.
    - A real directory at the same phase number still resolves (assert the
      non-symlink control in the same test or lean on the existing
      `test_resolves_the_current_phase_and_reaches_its_verdict`, but state
      which).
  </behavior>
  <action>
    At line 373, change `if entry.is_dir() and num and ...` to also require
    `not entry.is_symlink()`. `is_dir()` follows symlinks, so a symlinked entry
    under `.planning/phases/` currently resolves to a directory anywhere on the
    filesystem and its plan filenames get validated — low impact (names only,
    no content printed) but a real traversal out of the tree the gate is scoped
    to.

    Add a one-or-two-line comment stating why the `is_symlink()` check is there
    (a `is_dir()`-only test follows the link) so a later reader does not
    "simplify" it back out.

    Scope bound: `discover_plan_files` (line 383) is NOT in scope. The ticket
    names the phase-directory discovery loop only. Do not add symlink handling
    to plan-file discovery in this plan; if you think it needs one, say so in
    the SUMMARY and file a follow-up bd issue rather than widening the diff.
  </action>
  <verify>
    <automated>(cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && python3 -m unittest tests.test_check_alternatives.TestCurrentPhaseResolution tests.test_check_alternatives.TestPathSafety)</automated>
  </verify>
  <done>
    Symlinked phase entries are skipped, the new test passes, every existing
    `TestCurrentPhaseResolution` and `TestPathSafety` case keeps its verdict;
    committed to the target repo as one commit.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Map an unreadable plan path to the documented exit-2 contract</name>
  <files>.gsd/capabilities/sota-numerics/scripts/check-alternatives.py, tests/test_check_alternatives.py, README.md, CHANGELOG.md</files>
  <behavior>
    Rewrite `TestUnreadablePlanFiles` (line 1674):
    - `test_directory_named_like_a_plan_exits_1` becomes an exit-2 test: a
      directory named `01-01-PLAN.md` inside the phase directory exits 2, the
      offending path appears on stderr, stderr carries no `Traceback`, and
      there is still no `remediation:` line.
    - The class docstring (lines 1675-1681), which currently pins the raw
      traceback as a documented discrepancy ("The two look alike in the source
      and behave differently"), is rewritten to describe the unified contract.
    - `test_non_utf8_plan_names_the_file_and_the_remedy` is unchanged and
      still green — the decode path keeps its own message.
  </behavior>
  <action>
    In `validate_plan` (line 743), add an `except OSError as exc:` arm beside
    the existing `except UnicodeDecodeError` (line 754) and re-raise as
    `ValueError` naming the path and the reason, e.g.
    `f"{path}: could not be read ({exc.strerror}); a plan-shaped name must be a
    readable file"`. `main()`'s existing `except ValueError -> return 2` at
    lines 869-871 does the rest; no change is needed there.

    The two arms are disjoint (`UnicodeDecodeError` subclasses `ValueError`,
    not `OSError`), so ordering is cosmetic — keep the decode arm first so the
    more specific message reads first.

    **Exit code — read this, it diverges from one line of the task brief.** The
    orchestrator's constraint list paraphrases this as "catch it fail-closed
    (exit 1)". The ticket, which is the acceptance authority, records the
    measured fix as the exit-2 mapping and says the test and README must move
    with it. Exit 2 is also the coherent channel: 1 means "a plan violates the
    gate", 2 means "usage/IO error", and a directory that is not a file is the
    latter. Both block identically — `evaluateCommandExitZero` derives `block`
    from non-zero alone — so no gate consumer changes behaviour. Implement
    exit 2, and record this divergence explicitly in the SUMMARY.

    Update the module docstring's exit-2 sentence (lines 18-24) to include an
    unreadable plan path alongside the not-valid-UTF-8 case.

    Update `README.md`: extend the `2:` bullet (lines 193-203) to name the
    unreadable-plan case, and rewrite the paragraph at line 205 — "Other
    unexpected filesystem errors are not converted to `2`; they escape as
    Python errors, exit `1` ..." is now false for the `read_text` path. State
    what remains true: discovery still matches names without a file-type check,
    but a plan-shaped directory or an unreadable plan file now reports through
    the `check-alternatives.py: ` contract and exits 2.

    Add `CHANGELOG.md` entries under the unreleased `## 0.2.0` section for all
    three findings in this plan — that section's own framing is "which verdicts
    change and why", and finding 3 changes a verdict (1 -> 2) while findings 1
    and 2 change which documents and directories are read.

    These four files are one commit. Splitting the code from the test and the
    README is the exact shape the ticket says caused the deferral.
  </action>
  <verify>
    <automated>(cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && python3 -m unittest tests/test_check_alternatives.py)</automated>
  </verify>
  <done>
    The plan-shaped directory exits 2 with one clean `check-alternatives.py:`
    line and no traceback; the full suite passes with at least 125 tests; the
    module docstring, README exit-code section and CHANGELOG all describe the
    new behaviour; committed to the target repo as one commit.
  </done>
</task>

</tasks>

<verification>
Run all of these from the target repo before writing the SUMMARY.

1. Full suite, the exact command CI runs
   (`.github/workflows/*.yml` line 29):

   ```bash
   (cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 \
     && python3 -m unittest tests/test_check_alternatives.py)
   ```

   Must pass, with a test count >= 125 (three fixes add tests, none removed;
   one test is renamed, not deleted).

2. Corpus verdicts unchanged — the constraint that makes these edge-case
   handling rather than gate-behaviour changes:

   ```bash
   (cd /home/dd/projects/gsd-beads \
     && S=.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py \
     && for d in .planning/phases/19* .planning/phases/2[0-4]*; do \
          python3 "$S" "$d" >/dev/null 2>&1; echo "$? $d"; done)
   ```

   Must print exactly `1 …/19-…`, `0 …/20-…`, `0 …/21-…`, `1 …/22-…`,
   `0 …/23-…`, `0 …/24-…`.

3. All three findings no longer reproduce. Re-run each task's own
   reproduction against the patched script; the P2-1 repro that exited 1 with
   `missing '## Alternatives Considered' section` must now exit 0, the
   directory-named-like-a-plan repro must print one line and exit 2 with no
   `Traceback`, and the symlink repro must exit 2 with `matches 0 directories`.

4. Worktree hazard check:

   ```bash
   cat ~/.gsd/capability-auto-install-sota-numerics.hash
   ```

   Must still be `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498`.
   If it changed, say so in the SUMMARY and stop.

5. `git -C /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 status --short`
   is clean, and `git log --oneline -3` shows the three commits on
   `feat/extended-sota-definition`.
</verification>

<success_criteria>
- All three `gsd-beads-25vc.21.1` findings are fixed, each with its test in the
  same commit; the ticket's acceptance criterion ("a fix landed with its
  accompanying test/doc updated in the same commit, or an explicit recorded
  decision") is met by the fix branch for all three, with no deferrals.
- Three atomic commits on `feat/extended-sota-definition` in the target repo.
- Full suite green; corpus verdicts identical to the recorded baseline.
- The finding-3 exit-code divergence from the task brief's "(exit 1)"
  parenthetical is recorded in the SUMMARY, with the ticket text that
  authorizes exit 2.
- No scope beyond the ticket: no symlink handling in `discover_plan_files`, no
  new gate rules, no touched files outside the four in `files_modified`.
</success_criteria>

## Alternatives Considered

Mechanism choice for finding 1 (how to know a `<!--` sits inside inline code):

- **Same-line bounded backtick-span scan** (chosen): one anchored regex of the
  shape `` `[^`\n]{1,300}` ``, checked only against the candidate opener's own
  line. Zero new dependencies, ~10 lines, and identical in shape to
  `DOC_REF_RE` (line 147) and to every other scan in the module, all of which
  are deliberately anchored with no nested quantifiers. Residual — a code span
  crossing a line break, permitted by CommonMark
  (`https://spec.commonmark.org/0.31.2/#code-spans`, 2024) — fails closed and
  is documented.
- **Full CommonMark code-span matching via backreferenced variable-length
  delimiters** (`` (`+)[^\n]*?\1 ``): correct for the multi-backtick and
  multi-line cases the chosen scan misses, but introduces a backreference and a
  lazy quantifier into a module whose stated ReDoS discipline is anchored,
  no-backtracking patterns over untrusted planner-authored text. Rejected: it
  buys a case nobody has produced at the cost of the property the whole module
  is shaped around.
- **A markdown parser dependency** (`markdown-it-py`,
  `https://markdown-it-py.readthedocs.io/`, 2024, or `commonmark.py`): exactly
  correct, and immediately disqualified — the capability is stdlib-only by
  constraint (N5) and its gate script runs from a plugin bundle with no
  install step.
- **Document the limitation only**, the ticket's own second option: zero code,
  but leaves a compliant plan blocked by a false "missing section", which is
  the defect being reported rather than a mitigation of it. Rejected because
  the fix is ten lines.

Decided by: simplicity — the chosen scan is the smallest change that removes
the reported false positive without weakening the module's regex discipline or
its stdlib-only bound; performance is equivalent (both are single-pass over the
candidate's line).

Mechanism choice for finding 3 (`except OSError` vs `except IsADirectoryError`):
broad `OSError` is the ticket's own recorded wording and gives every unreadable
plan path — a directory, a permission failure, a dangling link — the same
`check-alternatives.py: <path>: <reason>` contract the module docstring
promises, instead of one special case and a traceback for the rest.
Decided by: maintenance — one arm and one documented paragraph beats a growing
list of individually-caught errno subclasses.

<output>
Write `.planning/quick/260908-gzq-fix-sota-numerics-check-alternatives-py-/260908-gzq-SUMMARY.md`
in the WORKING repo (`/home/dd/projects/gsd-beads`), not the target repo, when
done. Record: the three commit SHAs, the post-change corpus verdict table, the
final test count, the finding-3 exit-code divergence and its authorization, the
auto-install hash check, and any follow-up bd issue filed.
</output>
