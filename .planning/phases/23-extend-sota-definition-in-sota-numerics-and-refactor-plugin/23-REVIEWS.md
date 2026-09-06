---
phase: 23
reviewers: [claude, antigravity]
reviewed_at: 2026-09-06T17:52:06Z
plans_reviewed: [23-01-PLAN.md, 23-02-PLAN.md, 23-03-PLAN.md, 23-04-PLAN.md, 23-05-PLAN.md]
models:
  claude: "unknown"
  antigravity: "unknown"
model_sources:
  claude: "unknown"
  antigravity: "unknown"
---

# Cross-AI Plan Review — Phase 23

## Consensus Summary

Both reviewers verified plan claims directly against the sota-numerics worktree
(`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, `origin/main` @ `eccad87`,
v0.1.3) rather than taking the plan text at face value, citing `file:line` evidence throughout.
Both independently reach the same overall verdict: the phase is architecturally low-risk (advisory
prose/metadata edits only, no changes to the blocking gate's enforcement logic), but the plans'
own verification instruments contain brittle equality gates that will produce false-halt rework
during execution rather than shipped defects — every task re-runs the 50-test suite, so nothing
unsafe reaches `main`.

A source-grounding pass (below) independently re-derived three of these findings against the live
repository and confirms all three exactly as reported.

### Agreed Strengths
- **Recursion guard is real and verified against source.** Both reviewers independently confirmed
  the `${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics` installed-mirror fallback at
  `capability.json:81` is what the running `plan:post` gate actually executes when no project-scope
  copy exists, and that no task writes to the mirror (Claude Strengths §2; Antigravity Plan 23-01
  Strengths, Plan 23-01 Concerns "Strict Recursion Guard").
- **Mechanical/topological claims hold exactly.** Both reviewers checked concrete counts asserted by
  the plans (fragment line totals, `capability.json` gate `onError`/`blocking` fields, `README.md`
  table row counts) against the live files and found them exact (Claude Strengths §2; Antigravity
  Plan 23-03 Summary/Concerns).
- **Foundational-citation-pairing rule is protected.** Both reviewers traced the Kahan/IEEE-754
  pairing rule from `NOTES.md` through `TestFoundationalCitationPairing` in
  `tests/test_check_alternatives.py` and confirmed the plans do not weaken it (Claude Strengths §2;
  Antigravity Plan 23-02 Strengths).
- **Plan 05's review-before-publish and human checkpoint gate are correctly designed** against the
  live `marketplace.json` `source.url` publish mechanism (no `ref` — merge to `main` is publish)
  (Claude Strengths §2, D-25; Antigravity Plan 23-05 Strengths).

### Agreed Concerns
- **HIGH (independently confirmed by source-grounding) — Plan 02 Task 1's exact-equality line-count
  gate (`[ "$L" -eq 10 ]`) collides with a shipped test that pins verbatim prose.** Claude traced this
  to `tests/test_check_alternatives.py:522`
  (`TestDocumentedSyntax.test_readme_and_planner_name_exact_mixed_contract`), which asserts the exact
  25-word sentence "Internal entries need no external citation or date, do not count toward the two
  mechanism alternatives, and cannot lend evidence to a mechanism entry." survives verbatim in both
  `README.md` and `planner-sota.md`. Antigravity independently flagged the same underlying gate as
  brittle from a different angle ("Exact Line-Count Assertion in Task 1... causes failures if clean
  prose consolidation results in 9 lines," Plan 23-02 Concerns), i.e. the same `-eq 10` gate that
  Claude shows is also unsafe with respect to the pinned test. This report's own source-grounding
  pass read `bd show gsd-beads-sac.4` directly and confirmed Task 1's Action explicitly instructs
  "Merge the internal-design-alternatives line and the line about internal entries not counting into
  one line" — the merge target that would break the pinned sentence — while its `LOST RULE` grep list
  checks only `'Internal design alternatives'`, never the pinned sentence itself. No plan names this
  test as a constraint.
- **HIGH (independently confirmed by source-grounding) — Plan 04 Task 1's `git diff --numstat`
  prune-only gate is self-contradictory with its own Action text.** Antigravity traced this to the
  literal verify command
  (`git diff --numstat origin/main -- .../NOTES.md | awk '{print "added="$1" removed="$2; exit
  ($1>0)?1:0}'`) and observed that `git diff --numstat` counts any edited (not just deleted) line as
  one addition, so the task's own instruction to "leave its heading and its remaining sentences
  readable on their own; do not leave a paragraph that begins mid-argument" — which permits light
  rewording of surviving text — will trip `added > 0` and fail the task even when the file legitimately
  shrank. This report's own source-grounding pass read `bd show gsd-beads-sac.10` directly and
  confirmed both the exact verify command and the exact rewording permission in the Action text,
  independently reproducing the contradiction. Claude did not review this specific gate but
  independently identified the same class of problem elsewhere (the mirror-digest gate, below) —
  a plan-wide pattern of hard-equality verification gates that do not tolerate the executor behavior
  the plan itself permits.
- **MEDIUM — `plugin.json` / `marketplace.json` drift after Plan 03.** Both reviewers flagged that
  editing `.claude-plugin/plugin.json`'s description in Plan 03 immediately diverges from
  `.claude-plugin/marketplace.json` in the `gsd-beads` repo (already byte-identical today, per Claude's
  verification), and that the installer-facing marketplace listing will describe pre-0.2.0 dimensions
  until that separately-tracked issue (`gsd-beads-8pg`) is resolved (Claude Concerns §3 LOW;
  Antigravity Plan 23-03 Concerns MEDIUM). Reviewers differ on severity (LOW vs. MEDIUM) but agree on
  the mechanism and the fact that it is correctly out of this phase's scope.
- **MEDIUM — Plan 05's CI-before-publish sequencing is not actually preventive.** Claude found via
  `gh api repos/davdittrich/sota-numerics/branches/main/protection` (independently reproduced by this
  report's source-grounding pass: HTTP 404 "Branch not protected") that nothing blocks the merge from
  landing before CI runs on the merged SHA, so Plan 05's "re-verify CI on the merged SHA" is detective
  rather than preventive. Antigravity separately flagged the mechanical consequence of the same
  post-merge-only verification: a 5-15 second GitHub Actions registration delay means Task 3's
  check-runs query can read zero check-runs immediately after merge and false-halt on `NO-CHECKS.`
  Both concerns point at the same structural gap — nothing gates `main` before publish — from
  different angles (policy vs. timing).

### Divergent Views
- **Claude raised, Antigravity did not:** the mirror tree digest
  (`3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e`) cited as a pre-publish gate in
  all five plans is not reproducible by any obvious command (sorted `sha256sum`, concatenated `cat`,
  deterministic tar, and git-tree hash over the actual installed mirror all produced different values
  in this report's independent re-derivation). This is a HIGH/MEDIUM finding with no corroborating
  mention from Antigravity's review — see Source-Grounding Pass and Consensus Gate note below.
- **Claude raised, Antigravity did not:** three verification instruments described in prose (Plan 03's
  structural JSON allowlist diff and docstring-stripped AST comparison; Plan 04's twelve-claim README
  trace script) are asserted to have been run green on 2026-09-06 but are not committed anywhere, so
  the executor must reinvent them and the "already green" claim is unverifiable independently.
- **Claude raised, Antigravity did not:** the target is a linked git worktree
  (`.git` → `gitdir: .../sota-numerics-issue-1/.git/worktrees/sota-numerics-release-013`), not a
  standalone clone — HEAD is on branch `chore/release-0.1.3` (independently confirmed by this
  report's source-grounding pass), not `main`, and a sibling branch is checked out in a related
  worktree sharing the same object store. D-22's "clone" framing is imprecise but nothing in the
  plans actually breaks because of it.
- **Antigravity raised, Claude did not:** Plan 23-01's Task 1/2/3 and Plan 02/04 repeatedly touch the
  same `README.md:9-15` table rows across five separate tasks before a final prose pass, creating diff
  churn; and Plan 01 Task 1's `git switch -c feat/extended-sota-definition origin/main` is not
  idempotent if the branch already exists locally (`-C` would be).
- **Antigravity raised, Claude did not:** Plan 04 declares `depends_on: [23-02]` but its own Read
  First section says "capability.json/check-alternatives.py as Plan 03 left it," which is an
  undeclared Wave-3 ordering dependency on Plan 03.

## Claude Review

Reviewed against live source in the worktree, not the plan text. Findings below carry `file:line`.

## 1. Summary

Five plans are unusually well-grounded: topology, line counts, baseline, and publish mechanism all check out against source (`capability.json:29-89`, `wc -l` = 13/5/5/4, `Ran 50 tests ... OK` in 1.4s, both smoke scripts `ALL PASS`, `marketplace.json` has no `ref`). Decomposition is sound — Plan 01 Task 3 sets per-file caps (exec ≤15, verifier ≤9, ship ≤7) so the 45-line ceiling stays satisfiable across plans; worst case is 44. Three real defects: a shipped test pins verbatim prose in three files this phase rewrites and no plan names it; the mirror tree digest cited as a gate in all five plans is not reproducible by any obvious command; and three load-bearing verification instruments are described but never written out. None ships a defect — every task re-runs the suite — but all three convert into executor rework against hard equality bounds.

## 2. Strengths

- **Recursion guard is real, not theater.** `gsd-beads` has no project-scope `.gsd/capabilities/sota-numerics/` (only `beads/`), so the gate's `${GSD_HOME:-$HOME}` fallback at `capability.json:81` is what the running `plan:post` actually executes. Premise verified.
- **Every mechanical claim about the artifact holds.** Four contributions all `onError: "skip"` (`capability.json:39,50,60,72`); one gate `blocking: true` + `onError: "halt"` (`:86-87`); fragments 13/5/5/4 = 27; README 240; NOTES 115; checker 330. README's `## What it changes` table is exactly 5 rows (`README.md:11-15`) and the reference list is exactly 7 entries (`:224-236`) — both counts the plans assert.
- **Baseline honest and reproducible.** Re-ran this session: 50 tests OK, `test-session-start.sh` ALL PASS, `test-gate-script-resolution.sh` ALL PASS. Mirror is byte-identical to the worktree (`diff -rq` empty).
- **D-25 verified at the source.** `.claude-plugin/marketplace.json` entry: `"source": {"source":"url","url":"https://github.com/davdittrich/sota-numerics.git"}` — no `ref`. Merge *is* publish. Plan 05's one-way framing and its decision checkpoint before Task 3 are correct.
- **Plan 03's freeze instrument fits the risk.** Docstring-stripped AST equality is the right tool for a comment rewrite over a parser of untrusted input; a text diff cannot distinguish a reflowed comment from an altered regex.
- **`gh` available and authenticated** (`/usr/bin/gh`, account `davdittrich`). Research listed it unprobed; Plan 05's manual-PR fallback is dead weight.

## 3. Concerns

**HIGH — A shipped test pins verbatim prose in three files this phase rewrites; no plan names it.**
`tests/test_check_alternatives.py:522` `TestDocumentedSyntax.test_readme_and_planner_name_exact_mixed_contract` asserts by literal substring:
- `### Internal design alternatives` in **both** `README.md` and `planner-sota.md`
- the 25-word sentence `"Internal entries need no external citation or date, do not count toward the two mechanism alternatives, and cannot lend evidence to a mechanism entry."` in **both** — present at `README.md:129` and `planner-sota.md:5` (verified `True`)
- `assertNotIn("Each parsed entry must contain:", readme_text)` — `README.md:131` reads "Each parsed **mechanism** entry must contain:", passing on one word
- whitespace-normalized `"at least two named mechanism alternatives"` and `"Internal entries are excluded from the count and evidence validation."` inside `check-alternatives.py`'s **module docstring** (both verified `True`)

Collides with three tasks:
- **Plan 02 Task 1**, reduction #2 (`bd show gsd-beads-sac.4`): "Merge the internal-design-alternatives line and the line about internal entries not counting into one line, dropping..." — that second line *is* the pinned sentence. The task's `LOST RULE` grep list checks `'Internal design alternatives'` but not the sentence, and the task carries a hard `[ "$L" -eq 10 ]`.
- **Plan 03 Task 3** rewrites the module docstring; its freeze instrument strips docstrings, so it is blind by construction to the two pinned phrases.
- **Plan 04 Task 3**'s "legible standard prose pass" is exactly the moment "Each parsed **mechanism** entry" gets simplified into the forbidden string.

The 50-test suite catches all three, so nothing escapes to `main`. Cost is thrash, not defect.

**HIGH/MEDIUM — The mirror tree digest is not reproducible.**
`3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e` is a verification item in all five plans and a pre-publish gate in Plan 05 Task 1, with no command named. Over the mirror's 7 files: sorted `sha256sum` lines → `4111c09e…`; `cat` sorted → `40eb82fb…`; deterministic tar → `4f94e1b6…`; git tree → `8bcd3be0…`. None match. As written the check cannot be executed.

**MEDIUM — Publishing precedes CI verification and nothing enforces ordering.**
`gh api repos/davdittrich/sota-numerics/branches/main/protection` → 404 "Branch not protected". `allow_squash_merge: true`. With D-25, bytes are served the instant the merge lands; the squash SHA never ran CI before publication. Plan 05's "re-verify CI on the merged SHA" is detective, not preventive. The plan's own must_have — "CI is green on exact commit that reaches `main`" — is not achievable in the preventive sense it implies.

**MEDIUM — The target is a linked worktree, not a clone.**
`.git` is a file: `gitdir: /home/dd/projects/gsd-beads/.worktrees/sota-numerics-issue-1/.git/worktrees/sota-numerics-release-013`. Consequences the plans do not account for: HEAD is on `chore/release-0.1.3` (which happens to be at `eccad87`), not `main`; `fix/issue-2-internal-alternatives` is checked out in the sibling worktree and cannot be checked out here; refs and objects are shared with `sota-numerics-issue-1`. Nothing breaks, but D-22's "that clone's checkout and `origin/main` are both at `eccad87`" is imprecise about what is checked out.

**MEDIUM — Three load-bearing verification instruments are described but never written.**
Plan 03's "structural JSON diff with a four-path allowlist" and "docstring-stripped AST comparison"; Plan 04's twelve-claim README trace. Each is asserted "run green against the unmodified tree on 2026-09-06", each is the task's fail condition, none appears in the plan. The executor reinvents all three, and the no-op-green assurance is unverifiable.

**LOW — README compliance pulls two directions.** Plan 04 Task 3 caps README at 260 lines (currently 240) with no lower bound, while Plans 01/02 add content to the 5 Behavior cells and Task 3 prunes. No stated resolution. `23-RESEARCH.md` Open Question 2 raised this; the answer chose "both" without reconciling them.

**LOW — Marketplace drift is understated.** `marketplace.json`'s description is byte-identical to `plugin.json:4` (verified). After Plan 03 rewrites it, the listing an installer reads first will describe 0.1.3 and omit the six added dimensions entirely — the whole point of the release. Correctly out of scope (other repo, tracked `gsd-beads-8pg`), but Plan 05's "misleads about wording only, not enforcement" undersells it.

**LOW — NOTES.md bound off by one.** Plan 04 requires "shorter than 115 lines" and "zero added lines"; the file is exactly 115. One deletion satisfies a prune whose stated purpose is removing README overlap, and real overlap exists (`README.md:17` vs `NOTES.md:6-22`; the remediation-line passage at `NOTES.md:45-51` vs README's `remediation:` block).

## 4. Suggestions

- Add `tests/test_check_alternatives.py:521-560` to `read_first` on `sac.4`, `sac.9`, `sac.12`, and give each a literal-preservation assertion before the suite runs — one `python3 -c` checking the four pinned strings. Cheaper than discovering it through a red suite against `-eq 10`.
- Replace the digest with a predicate that runs: `diff -rq "${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics" <worktree>/.gsd/capabilities/sota-numerics` — empty today, proves the same property. Or pin the generating command beside the hash.
- Inline the JSON-allowlist diff, the AST comparison, and the twelve-claim trace verbatim in Plans 03 and 04.
- Plan 05: enable a required status check on `main`, or state in the SUMMARY that post-merge verification is detective and name the exposure window.
- Reword D-22 to "linked worktree of `sota-numerics-issue-1`, HEAD on `chore/release-0.1.3` at `eccad87`", and note the shared ref namespace.
- Give NOTES.md a target rather than a ceiling — sections 1 and 2 carry the README overlap D-18 asks to remove.

## 5. Risk Assessment

**MEDIUM.**

Downward: scope is prose in a small, fully-tested capability; suites are 3s and green; per-file caps make the budget decomposable and the arithmetic holds; the single one-way step sits behind a genuine decision checkpoint with the marketplace mechanism verified at source; every task re-runs the full suite, so the prose-pinning test cannot leak a break to `main`.

Upward: a shipped test pins verbatim prose in exactly the three files being rewritten, intersecting a task with a hard `-eq 10` line count and a task whose freeze instrument is blind to it; the digest gate cited in all five plans cannot be run as written; three named verification instruments do not exist yet; and the publish step has no preventive CI gate on an unprotected branch that *is* the distribution channel. All four manifest as rework and false-halt thrash during execution, not as shipped defects — which is why this is MEDIUM and not HIGH.

---

## Antigravity Review

# Cross-AI Plan Review: Phase 23 (sota-numerics v0.2.0)

Reviewing implementation plans [`23-01-PLAN.md`](file:///home/dd/projects/gsd-beads/.planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin/23-01-PLAN.md), [`23-02-PLAN.md`](file:///home/dd/projects/gsd-beads/.planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin/23-02-PLAN.md), [`23-03-PLAN.md`](file:///home/dd/projects/gsd-beads/.planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin/23-03-PLAN.md), [`23-04-PLAN.md`](file:///home/dd/projects/gsd-beads/.planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin/23-04-PLAN.md), and [`23-05-PLAN.md`](file:///home/dd/projects/gsd-beads/.planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin/23-05-PLAN.md). All target repository files resolve against the worktree clone at [`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013) (currently at `eccad87`, version `0.1.3`).

---

### Plan 23-01: Executor Role Slice

#### 1. Summary
Plan 01 implements the executor role slice of the extended SOTA definition across [`executor-numerics.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/fragments/executor-numerics.md), [`verifier-precision.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/fragments/verifier-precision.md), [`ship-precision-advisory.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md), and [`README.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/README.md). It uses an end-to-end tracer on `quiet` before expanding to `legible` and efficiency, enforcing strict line budgets (<= 45 lines total across fragments) while preserving the green test baseline.

#### 2. Strengths
- **Tracer Discipline:** Task 1 validates the pipeline on `quiet` alone before adding `legible` and efficiency, isolating structural issues early.
- **Strict Recursion Guard:** Tasks verify the installed mirror at [`/home/dd/.gsd/capabilities/sota-numerics`](file:///home/dd/.gsd/capabilities/sota-numerics) against exact sha256 `3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e`, ensuring the active gate evaluator cannot be poisoned.
- **Dead Reference Cleanup:** Directly identifies and purges the unresolvable decision pointer `(D-12)` in [`ship-precision-advisory.md:1`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md#L1).
- **Prompt Token Budget Control:** Automatically asserts fragment line bounds (`awk 'END{print NR}' fragments/*.md <= 45`), preventing context bloating.

#### 3. Concerns
- **LOW:** *Ponytail Lens / Fragment-README Churn:* [`README.md:9-15`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/README.md#L9-L15) is modified repeatedly in Tasks 1, 2, and 3, then modified again in Plan 02 Tasks 2 and 3, and again in Plan 04 Tasks 2 and 3. Iteratively editing the same Markdown table cells across 5 tasks before the final prose pass creates excessive diff noise.
- **LOW:** *Branch Precondition Fragility:* Task 1 specifies `git switch -c feat/extended-sota-definition origin/main`. The worktree is currently checked out on branch `chore/release-0.1.3`. If `feat/extended-sota-definition` already exists locally, `-c` aborts.

#### 4. Suggestions
- Use `git switch -C feat/extended-sota-definition origin/main` to make branch checkout idempotent.
- Defer granular README table updates until Plan 04, or update table rows in a single batch per plan rather than per task.

#### 5. Risk Assessment: LOW
Targeted, purely prompt-advisory changes backed by existing suites and line counters.

---

### Plan 23-02: Planner Role Slice

#### 1. Summary
Plan 02 prunes the internal checker implementation details from [`planner-sota.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/fragments/planner-sota.md#L1-L13) from 13 lines down to 10, then defines **with the grain** and plan completeness (<= 12 lines), echoing the bare tokens into [`verifier-precision.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/fragments/verifier-precision.md) and [`ship-precision-advisory.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md).

#### 2. Strengths
- **Self-Funding Token Budget:** Tokens for the new dimensions are reclaimed by pruning checker mechanics that planners already receive from [`check-alternatives.py:323`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py#L323) runtime diagnostics.
- **Canonical Pairing Rule Integrity:** Protects the Kahan/IEEE-754 pairing rule documented in [`NOTES.md:99-115`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/NOTES.md#L99-L115) and enforced by [`TestFoundationalCitationPairing`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/tests/test_check_alternatives.py#L273) in [`tests/test_check_alternatives.py`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/tests/test_check_alternatives.py).
- **Mechanical Rule Preservation:** Task 1 verify checks literal survival of all critical keywords (`Alternatives Considered`, `Decided by:`, `Internal design alternatives`, `no mechanism choice`, `SPEC.md`, `Kahan`).

#### 3. Concerns
- **LOW:** *Exact Line-Count Assertion in Task 1:* Task 1 verify requires `[ "$L" -eq 10 ]`. Pinning an exact equality rather than `<= 10` causes failures if clean prose consolidation results in 9 lines.

#### 4. Suggestions
- Adjust the check to `[ "$L" -le 10 ]` while ensuring the literal token checks continue to guard against omitted rules.

#### 5. Risk Assessment: LOW
Clear separation of concerns; verified by both unit tests and string assertions.

---

### Plan 23-03: Manifest Bumps and Gate Script Refactor

#### 1. Summary
Plan 03 updates [`capability.json`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/capability.json) and [`plugin.json`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.claude-plugin/plugin.json) to version `0.2.0` with updated description strings. It refactors [`check-alternatives.py`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py) docstrings and comments for legibility, verifying AST equivalence against `origin/main` to guarantee zero logic mutation.

#### 2. Strengths
- **Structural Manifest Diffing:** Implements an automated recursive AST/dict diff allowing mutations *only* at `version`, `description`, `gates[0].description`, and `config.sota-numerics.enabled.description`, preventing accidental changes to `gates[0].check.predicate.command` ([`capability.json:81`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/capability.json#L81)).
- **AST Normalization Guard:** Task 3 uses `ast.parse` and docstring stripping to prove that [`check-alternatives.py`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py) executable bytecode remains identical to `origin/main`.
- **Elimination of Unshipped References:** Purges 14 internal references (`D-01`, `RESEARCH`, `REVIEWS`, `T-11-02`) from docstrings so agent-facing code does not point to inaccessible planning files.
- **Negative Path Validation:** Executes [`tests/fixtures`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/tests/fixtures) to verify exit code 1 and stderr remediation output.

#### 3. Concerns
- **MEDIUM:** *Downstream Marketplace Drift:* Modifying [`plugin.json:4`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.claude-plugin/plugin.json#L4) causes immediate drift from [`marketplace.json:28`](file:///home/dd/projects/gsd-beads/.claude-plugin/marketplace.json#L28) in `gsd-beads`. While tracking issue [`gsd-beads-8pg`](file:///home/dd/projects/gsd-beads) is correctly logged, installers viewing the marketplace catalog will see pre-0.2.0 descriptions until `gsd-beads` is updated.

#### 4. Suggestions
- Re-verify in Plan 03 summary that [`gsd-beads-8pg`](file:///home/dd/projects/gsd-beads) remains open and queued for immediate resolution upon 0.2.0 release.

#### 5. Risk Assessment: LOW
AST equivalence check and structural JSON allowlist make accidental regressions mathematically impossible.

---

### Plan 23-04: Documentation Prune and Claim Tracing

#### 1. Summary
Plan 04 prunes [`NOTES.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/NOTES.md) against [`README.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/README.md) while preserving all 5 anti-regression entries. It runs an automated 12-claim verification script proving all behavioral claims in [`README.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/README.md) resolve to code/config.

#### 2. Strengths
- **Mechanical Claim Tracing:** Task 2's Python script checks 12 concrete facts (counts, timeouts, regex limits, `MIN_ALTERNATIVES = 2`, `range(10)`) directly against [`capability.json`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/capability.json), [`check-alternatives.py`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py), and [`README.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/README.md).
- **Anti-Regression Anchors:** Preserves all 5 headings and critical warnings in [`NOTES.md:1-116`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/NOTES.md#L1-L116) (such as `onError: halt` and recency rule window).

#### 3. Concerns
- **HIGH:** *Numstat Verification Failure on Line Rewrites:* Task 1 verify runs:
  `git diff --numstat origin/main -- .gsd/capabilities/sota-numerics/NOTES.md | awk '{print "added="$1" removed="$2; exit ($1>0)?1:0}'`
  In `git diff --numstat`, any edited line registers as 1 addition and 1 deletion (`$1=1, $2=1`). Task 1's action instructs: "Where a section shrinks, leave its heading and its remaining sentences readable on their own; do not leave a paragraph that begins mid-argument." If an executor edits a surviving sentence to smooth the transition after cutting earlier text, `$1 > 0` and the check aborts.
- **LOW:** *Wave 3 Dependency Ambiguity:* Plan 04 states in Read First: "capability.json as Plan 03 left it" and "check-alternatives.py as Plan 03 left it", but only specifies `depends_on: [ 23-02 ]`. Running 03 and 04 concurrently in Wave 3 without declared sequencing risks race conditions if executed sequentially on the same worktree branch.

#### 4. Suggestions
- Update Task 1 verify in Plan 04 to allow sentence rewording by checking net line reduction instead:
  `awk '{added+=$1; removed+=$2} END {exit (added >= removed || added > 20)?1:0}'`
  Or explicitly instruct the executor that only full line deletions are allowed (zero modifications to surviving lines).
- Set `depends_on: [ 23-03 ]` in [`23-04-PLAN.md`](file:///home/dd/projects/gsd-beads/.planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin/23-04-PLAN.md) to formally order execution.

#### 5. Risk Assessment: MEDIUM
Risk is driven by the brittle `awk ($1>0)` gate on [`NOTES.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/NOTES.md).

---

### Plan 23-05: Review, Publish, and Tag

#### 1. Summary
Plan 05 executes internal review across three lenses (correctness/security, over-engineering/ponytail, self-compliance) and lands fixes on branch before opening a PR. It features a human decision checkpoint (Task 2) before pushing and merging to `main` (which serves `0.2.0` immediately via marketplace URL), re-verifies CI on the merged commit SHA, and creates annotated tag `v0.2.0`.

#### 2. Strengths
- **Review-Before-Publish Enforcement:** Internal review and fixes must land on the branch *before* opening the PR (`gh pr list` asserted empty in Task 1), preventing external reviewers/bots from reviewing half-baked diffs.
- **Explicit Checkpoint Gate:** Task 2 blocks on human approval because merging to `main` immediately publishes to all marketplace consumers (`source.url` in [`marketplace.json:26`](file:///home/dd/projects/gsd-beads/.claude-plugin/marketplace.json#L26)).
- **Exact-Commit CI Re-Verification:** Task 3 explicitly fetches and checks GitHub Actions check-runs on `origin/main`'s merge SHA, rather than assuming pre-merge PR status is sufficient.
- **Release Marker Fix:** Introduces tag `v0.2.0`, resolving the historical lack of release tags identified in tracking issue [`gsd-beads-oh1`](file:///home/dd/projects/gsd-beads).

#### 3. Concerns
- **MEDIUM:** *Race Condition on Post-Merge Check-Runs:* Task 3 runs:
  `SHA=$(git rev-parse origin/main) && gh api "repos/davdittrich/sota-numerics/commits/$SHA/check-runs" ...`
  Immediately after `git merge`, GitHub Actions takes 5–15 seconds to register a check-run suite for the `push` event. If queried immediately, `.check_runs | length` is 0, returning `NO-CHECKS` and triggering failure.
- **LOW:** *Merge Strategy Unspecified:* Task 3 states "Merge once every check is green", but does not specify `--merge`, `--squash`, or `--rebase`. Using `--squash` generates a new commit with a synthetic message that must be properly attributed.

#### 4. Suggestions
- Add a retry loop or wait step for check-run registration before querying check-runs on `origin/main` (e.g., `gh run watch $(gh run list --commit "$SHA" --json databaseId -q '.[0].databaseId')`).
- Explicitly specify `gh pr merge --merge` (or `--squash`) in Task 3 instructions.

#### 5. Risk Assessment: LOW-MEDIUM
The checkpoint gate prevents accidental publication. CI check-run race condition is the only notable operational friction.

---

### Phase 23 Overall Risk Assessment

**Overall Risk Level: LOW-MEDIUM**

**Justification:**
1. **Architectural Isolation:** The phase modifies only advisory Markdown fragments, version/description metadata, and docstrings/comments. The blocking gate logic in [`check-alternatives.py`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py) and the gate manifest contract in [`capability.json:75-90`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/capability.json#L75-L90) are frozen by AST and structural diff assertions.
2. **Defensive Rigor:** Verification scripts test exact regexes, line budgets, and tree digests across all tasks.
3. **Key Friction Points:**
   - Brittle numstat verification in Plan 04 Task 1 (`NOTES.md`).
   - Timing delay in post-merge CI check-run creation in Plan 05 Task 3.
   - Diff churn on [`README.md`](file:///home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/README.md) across multiple waves.

---

## Verification Coverage (Source-Grounding Pass)

Per `plan_review.source_grounding`, every symbol/path the five plans cite outside their "Artifacts
this phase produces" sections was enumerated and resolved directly against the sota-numerics
worktree (`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, `origin/main` @
`eccad87`) — chosen over `.planning/intel/API-SURFACE.md`/`api-map.json` because those intel files
index only `gsd-beads`'s own `beads` capability (`sync.py` CLI verbs) and carry no entries at all
for the sota-numerics repository; they are the wrong authority for this phase's target repo and are
marked UNCHECKABLE-VIA-INTEL below rather than silently skipped.

| Symbol / path cited | Kind | Plan:line | Resolution |
|---|---|---|---|
| `MIN_ALTERNATIVES = 2` | module constant | 23-04-PLAN.md (Task 2, via `bd show gsd-beads-sac.11`) | VERIFIED — `scripts/check-alternatives.py:33` |
| `range(10)` | literal | 23-04-PLAN.md (Task 2) | VERIFIED — `scripts/check-alternatives.py:78` |
| `TestFoundationalCitationPairing` | test class | 23-02-PLAN.md, 23-04-PLAN.md | VERIFIED — `tests/test_check_alternatives.py:785` |
| `TestDocumentedSyntax.test_readme_and_planner_name_exact_mixed_contract` | test method | cited only in Claude's review, not in any plan | VERIFIED — `tests/test_check_alternatives.py:521-522`; body confirmed to assert the exact pinned sentence in both `README.md` and `.gsd/capabilities/sota-numerics/fragments/planner-sota.md` |
| `capability.json` `gates[0].onError`/`blocking` | dataclass/config fields | 23-03-PLAN.md, 23-04-PLAN.md | VERIFIED — `.gsd/capabilities/sota-numerics/capability.json:86-88` (`"blocking": true`, `"onError": "halt"`) |
| `capability.json` contribution `onError: "skip"` (x4) | config field | 23-01-PLAN.md | VERIFIED — `capability.json:39,50,61,72` |
| `scripts/check-alternatives.py` (relative shorthand) | file path | all 5 plans | VERIFIED via full path `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` — the plans' shorthand omits the capability-directory prefix but resolves unambiguously |
| `git diff --numstat origin/main -- .../NOTES.md \| awk '{print "added="$1" removed="$2; exit ($1>0)?1:0}'` | CLI invocation / verify gate | 23-04-PLAN.md Task 1 (`bd show gsd-beads-sac.10`) | VERIFIED — exact command confirmed in the bd ticket body, alongside the Action text's explicit permission to reword surviving sentences, confirming Antigravity's HIGH finding of a self-contradiction |
| `[ "$L" -eq 10 ]` / `LOST RULE:` grep list | CLI/shell assertion | 23-02-PLAN.md Task 1 (`bd show gsd-beads-sac.4`) | VERIFIED — exact grep list (`Alternatives Considered`, `Decided by:`, `Internal design alternatives`, `no mechanism choice`, `SPEC.md`, `Kahan`) confirmed; does not include the pinned test's 25-word sentence, confirming Claude's HIGH finding |
| Mirror tree digest `3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e` | hash literal / gate | all 5 plans, gate in 23-05-PLAN.md Task 1 | MISSING / NOT REPRODUCIBLE — independently attempted sorted `sha256sum` (`4111c09e…`), concatenated `cat` (`40eb82fb…`), deterministic tar (`4f94e1b6…`) over the live `${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics` mirror; none match the cited hash and the mirror is not a git repo (no tree hash available). No plan names the generating command. |
| `.git` → linked worktree, HEAD on `chore/release-0.1.3` | repo state claim | Claude's review (cross-cutting on D-22) | VERIFIED — `.git` file reads `gitdir: /home/dd/projects/gsd-beads/.worktrees/sota-numerics-issue-1/.git/worktrees/sota-numerics-release-013`; `git branch --show-current` = `chore/release-0.1.3`, at `eccad87`, matching `origin/main` |
| `gh api repos/davdittrich/sota-numerics/branches/main/protection` → 404 | CLI flag / API claim | Claude's review (Plan 05) | VERIFIED — independently re-ran; identical 404 "Branch not protected" |
| `.claude-plugin/marketplace.json` `source` (no `ref`) | config field | 23-05-PLAN.md | VERIFIED — `gsd-beads/.claude-plugin/marketplace.json`: `"source":{"source":"url","url":"https://github.com/davdittrich/sota-numerics.git"}`, no `ref` key |
| `.planning/intel/API-SURFACE.md`, `api-map.json` | authority artifact | n/a (workflow-level authority, not plan-cited) | UNCHECKABLE-VIA-INTEL — both files enumerate only `gsd-beads`'s own `sync.py` CLI surface; they carry zero entries for sota-numerics and the API-SURFACE.md banner itself flags the source `api-map.json` as stale (>24h). All sota-numerics symbols above were instead resolved directly against the live worktree. |

No plan-cited symbol resolved AMBIGUOUS. Two resolved MISSING/NOT REPRODUCIBLE (the mirror digest);
all others VERIFIED.

## Cross-Artifact Fact-Drift Pass (Advisory)

`gsd_run drift-guard phase-status --phase 23` returned:
```json
{"verdict":"uncheckable","reason":"phase_not_in_roadmap","phase":"23","stateStatus":"Ready to execute","roadmapStatus":null,"stateRank":1,"roadmapRank":null,"authority":"STATE.md"}
```
Recorded as **uncheckable** per instruction (never treated as `consistent`) — the tool could not
match phase 23 against its roadmap-parsing pattern even though `.planning/ROADMAP.md:121` contains
`### Phase 23: Extend SOTA definition in sota-numerics and refactor plugin to comply`. This is a
tooling/parser gap, not a claim about phase 23 itself, and is not counted toward `current_high` or
`current_actionable` (advisory pass).

Manual pairwise checks (advisory, per instruction — SAME fact on both sides required to flag):
- **ROADMAP.md `**Requirements:**` ↔ PLAN.md `requirements:` frontmatter (DRIFT FLAGGED, advisory
  only).** ROADMAP.md's Phase 23 entry (authority) states "Requirements: none in REQUIREMENTS.md —
  traced to 23-CONTEXT.md decisions D-01..D-27 (all 27 covered)." The union of all five plans'
  `requirements:` frontmatter arrays is `{D-01, D-02, D-03, D-04, D-05, D-07, D-08, D-09, D-10, D-11,
  D-12, D-13, D-14, D-15, D-16, D-17, D-18, D-19, D-20, D-21, D-22, D-23, D-24, D-25, D-26, D-27}` —
  26 of 27, missing `D-06`. D-06 ("rejected shared fragment injected at all four points") is not
  absent from the phase, however: `23-01-PLAN.md:50,157` cites it by ID in a `prohibitions` must-have
  and in `## Alternatives Considered`. So the underlying decision is addressed, but the roadmap's
  literal "all 27 covered" claim and the plans' `requirements:` frontmatter (which is what
  plan-checker-style coverage tooling reads) disagree on whether D-06 is a *tracked requirement* of
  any plan. This is a same-fact contradiction (full D-01..D-27 frontmatter coverage), not a
  wording-only difference — flagged per instruction, advisory only, does not affect
  `current_high`/`current_actionable`.
- **ROADMAP.md Success Criteria ↔ PLAN.md `must_haves.truths`:** no additional contradiction found
  beyond the D-06 gap above.
- **CONTEXT.md Decisions ↔ PLAN.md usage of defined terms:** spot-checked D-25 (marketplace publish
  is one-way on merge to `main`) against 23-05-PLAN.md's framing — consistent, both describe merge as
  immediate, irreversible publish. No contradiction found.

One drift flagged (ROADMAP.md/PLAN.md requirement-coverage gap on D-06, above). This pass is
advisory only per instruction and contributes to neither `current_high` nor `current_actionable`.

---

## Orchestrator Adjudication — Cycle 1

The three HIGHs reported by the review agent were re-checked against source by the orchestrator before any replan, because a false HIGH fed into a `--reviews` replan produces a worse plan than no review at all. Verdicts and the evidence for each:

### HIGH 1 — Pinned-prose test collision: UPHELD

`tests/test_check_alternatives.py`'s `TestDocumentedSyntax.test_readme_and_planner_name_exact_mixed_contract` hard-pins two literals and asserts both survive in BOTH `README.md` and `.gsd/capabilities/sota-numerics/fragments/planner-sota.md`:

- the marker `### Internal design alternatives`
- the sentence `Internal entries need no external citation or date, do not count toward the two mechanism alternatives, and cannot lend evidence to a mechanism entry.`

Confirmed by reading the test body directly, and by `grep -c` returning 1 in each of the two files. Plan 02 Task 1's Action instructs merging that exact sentence into another line during the prune, and its `LOST RULE` grep list checks only `Internal design alternatives`, never the sentence. The suite goes red on execution. The finding stands and must be planned around.

### HIGH 2 — Mirror-tree digest "not reproducible": REJECTED

The digest reproduces exactly. Run twice by the orchestrator on 2026-09-06 using the plans' own command verbatim:

```
cd "${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics" && find . -type f | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1
3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e
```

That is byte-identical to the digest the five plans cite. The review's re-derivation compared four DIFFERENT hashing methods (sorted `sha256sum`, concatenated `cat`, deterministic tar, git-tree hash) and reported that they disagree with each other. They do — different methods produce different digests by construction. Method-independence is not the property a recursion guard needs; reproducibility of one named command is, and that holds.

This HIGH is excluded from `current_high`. It is retained here rather than deleted, per the no-silent-drop rule. **No replan may weaken or remove the digest guard on the strength of this finding.**

### HIGH 3 — Self-contradictory prune gate in Plan 04 Task 1: UPHELD

`git diff --numstat` reports an edited line as one addition and one deletion. The gate exits non-zero when `$1 > 0`, while the same task's Action explicitly permits rewording surviving sentences to keep them readable after a cut. Any executor that takes the permission trips the gate on a file that legitimately shrank. Confirmed present in `bd show gsd-beads-sac.10`.

Worth recording why the command is not greppable in `23-04-PLAN.md`: `beads.sync_mode` is `authoritative`, so `beads-sync` moved task bodies into bd and left `<!-- beads: content synced to bd -->` stubs in the plan. bd holds the authoritative task content. The reviewer reading it via `bd show` was reading the real plan, not a stale copy.

### Adjudicated count

`current_high = 2` (HIGH 1, HIGH 3). `current_actionable = 11`, unchanged.

### One divergent finding promoted

The "linked worktree, not a clone" observation is upheld and is more consequential than its LOW framing suggests. `.worktrees/sota-numerics-release-013/.git` is a gitdir pointer to `.worktrees/sota-numerics-issue-1/.git/worktrees/sota-numerics-release-013`; the two share one object store and one ref namespace, and HEAD is on `chore/release-0.1.3`, not `main`. CONTEXT D-22's "clone" wording is wrong, and any plan step that creates a branch affects the sibling worktree. This must be corrected in the replan.
