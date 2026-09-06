---
quick_id: 260828-olq
slug: implement-davdittrich-sota-numerics-1-in
date: 2026-08-28
phase: quick-260828-olq
plan: 01
type: tdd
wave: 1
depends_on: []
files_modified:
  - .worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py
  - .worktrees/sota-numerics-issue-1/tests/test_check_alternatives.py
  - .worktrees/sota-numerics-issue-1/README.md
  - .worktrees/sota-numerics-issue-1/.claude-plugin/plugin.json
  - .worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/capability.json
autonomous: true
beads_epic: gsd-beads-p07
estimate:
  tokens: 42000
  raw_tokens: 42000
  tasks: 1
  confidence: low
must_haves:
  truths:
    - "A plan headed `## Alternatives Considered (REQ-10)` is recognized as having the Alternatives Considered section, while a concatenated `## Alternatives ConsideredFoo` heading remains absent."
    - "A Markdown table row with one bold mechanism name is one alternative entry, citation/date validation is scoped to that row so evidence from a neighboring row cannot make it pass, and neither a bold citation-bearing header nor its separator row counts as an alternative."
    - "An exact heading with zero recognized bullet or table entries reports that the section was found but no alternatives were parsed; exactly one parsed entry retains the existing `fewer than 2 named alternatives (found 1)` diagnostic."
    - "The existing bold-bullet syntax remains accepted with the same minimum count, citation, recency, placeholder, exemption, decision-criterion, discovery, confinement, remediation, and blocking behavior."
    - "Every regression pair changes rendering shape only; names, prose, citations, years, ranked criterion, and invocation path are otherwise identical."
    - "README documents the executable heading, bullet, table-row, row-local evidence, and zero-entry diagnostic contract without claiming broader Markdown support."
    - "Plugin and capability metadata are synchronized at 0.1.2; the versionless `gsd-beads` marketplace entry remains unchanged."
    - "Antigravity, Claude, Codex, and critical-code reviews all cite the exact final candidate SHA and have no unresolved in-scope Blocking or Required finding before merge."
    - "The reviewed SHA is fast-forward merged to `main`, pushed without force, and its unique GitHub Actions `CI` push run succeeds."
    - "Claude and Codex registries report sota-numerics 0.1.2, both installed tracked payloads match pushed source byte-for-byte, and the user-scoped capability bundle matches source recursively."
    - "GitHub issue davdittrich/sota-numerics#1 and Beads ticket gsd-beads-p07 close only after every code, review, remote, CI, and install predicate passes."
  artifacts:
    - path: ".worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py"
      provides: "Bounded suffixed-heading recognition, bold table-row entry extraction, and distinct zero-parsed diagnostic"
    - path: ".worktrees/sota-numerics-issue-1/tests/test_check_alternatives.py"
      provides: "CLI-boundary RED/GREEN regressions and shape-only controls"
    - path: ".worktrees/sota-numerics-issue-1/README.md"
      provides: "Executable accepted-syntax and diagnostic contract"
    - path: ".worktrees/sota-numerics-issue-1/.claude-plugin/plugin.json"
      provides: "Claude/Codex marketplace plugin version 0.1.2"
    - path: ".worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/capability.json"
      provides: "User-scoped capability version 0.1.2"
    - path: "/home/dd/.claude/plugins/cache/gsd-beads/sota-numerics/0.1.2"
      provides: "Byte-verified Claude installation"
    - path: "/home/dd/.codex/plugins/cache/gsd-beads/sota-numerics/0.1.2"
      provides: "Byte-verified Codex installation"
    - path: "/home/dd/.gsd/capabilities/sota-numerics"
      provides: "Byte-verified installed capability bundle"
  key_links:
    - from: ".worktrees/sota-numerics-issue-1/tests/test_check_alternatives.py"
      to: ".worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py"
      via: "`sys.executable` subprocess calls exercise exit code and stderr at the public CLI boundary"
      pattern: "run_check"
    - from: ".worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py"
      to: ".worktrees/sota-numerics-issue-1/README.md"
      via: "Accepted heading and entry grammar plus diagnostics are documented verbatim"
      pattern: "Alternatives Considered"
    - from: ".worktrees/sota-numerics-issue-1/.claude-plugin/plugin.json"
      to: ".worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/capability.json"
      via: "Exact 0.1.2 version equality"
      pattern: "0.1.2"
    - from: ".worktrees/sota-numerics-issue-1"
      to: "/home/dd/.claude/plugins/cache/gsd-beads/sota-numerics/0.1.2"
      via: "Native marketplace refresh/update and tracked-file SHA-256 parity"
      pattern: "sota-numerics@gsd-beads"
    - from: ".worktrees/sota-numerics-issue-1"
      to: "/home/dd/.codex/plugins/cache/gsd-beads/sota-numerics/0.1.2"
      via: "Native marketplace upgrade/add and tracked-file SHA-256 parity"
      pattern: "sota-numerics@gsd-beads"
    - from: ".worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics"
      to: "/home/dd/.gsd/capabilities/sota-numerics"
      via: "Installed Claude hook followed by recursive byte comparison"
      pattern: "capability-auto-install.sh"
---

## Mechanism

Extend the existing bounded Python `re` grammar at its two proven choke points: accept a heading suffix only after the `Alternatives Considered` word boundary, and add a bounded, line-anchored table-row matcher that extracts one bold mechanism name and hands that single row to the unchanged entry validator. Keep bullet parsing as the first path; use table rows when bullets do not satisfy the existing minimum. Add one explicit zero-parsed branch before the unchanged one-entry diagnostic. This is the first Ponytail rung that holds: existing parser, standard library, no new dependency, no new abstraction.

## Forbidden

Do not change alternative counts, URL/backticked-doc citation rules, six-year recency semantics, foundational-plus-current citation handling, placeholder detection, the `N/A — no mechanism choice` exemption, `Decided by:` criteria, plan discovery, dotted phase names, project-root discovery, path confinement, remediation cardinality/text except the requested zero-parsed diagnostic, exit codes, gate `blocking: true`, gate `onError: halt`, advisory contribution behavior, capability configuration, or any non-parser lifecycle behavior. Do not accept concatenated heading names, parse arbitrary Markdown, combine evidence across table rows, count separator/header rows, mix bullet and table evidence to evade the minimum, add a dependency, edit the outer versionless marketplace manifest, create a tag or GitHub Release, force-push, commit `.planning/`, or use bare `/tmp`.

## Audit

Audit the public CLI contract, not regex implementation details: write `unittest` cases that invoke the checker through the existing `run_check` subprocess helper and assert exit code plus exact stderr fragments. Pair each new acceptance case with a control whose only changed bytes are the heading or entry rendering shape. The row-local negative must place valid evidence only in the neighboring row and assert the deficient alternative's name and evidence error. No internal-call claim is made, so no mock or spy is needed; the subprocess is the observable trust boundary. Every external reviewer must name the exact reviewed SHA, cite file and line evidence, classify each finding with a 0–100 confidence score, and return an explicit PASS/BLOCK verdict; empty, uncited, stale-SHA, permission-denied, or malformed output is failure.

## Alternatives Considered

- **Bounded stdlib heading and table-row regexes (selected)**: Python's current `re` documentation defines line anchors, word boundaries, compiled patterns, and bounded repetitions; the existing checker already uses this mechanism and feeds extracted entries into one validator ([Python 3.14 `re` documentation](https://docs.python.org/3/library/re.html), accessed 2026-08-28). Rank: performance 1, simplicity/LOC 1, ecosystem 1, maintenance 1. It changes only the two narrow grammar seams and preserves every downstream invariant.
- **Line-oriented state parser**: Python's current string API supplies `splitlines()` and ordinary prefix/content operations sufficient to track the target section and table rows without regex ([Python 3.14 standard types documentation](https://docs.python.org/3/library/stdtypes.html#str.splitlines), accessed 2026-08-28). Rank: performance 2, simplicity/LOC 2, ecosystem 1, maintenance 2. It is viable and dependency-free, but duplicates heading/entry recognition already centralized in compiled patterns and introduces more branch state for a two-shape extension.
- **Markdown AST via markdown-it-py**: the maintained parser exposes block/inline tokens and a GFM-like table component, so headings and table cells can be recognized structurally ([markdown-it-py usage documentation](https://markdown-it-py.readthedocs.io/en/latest/using.html), accessed 2026-08-28). Rank: performance 3, simplicity/LOC 3, ecosystem 2, maintenance 3. It is the broadest grammar, but adds a runtime dependency and AST traversal for a five-line input contract; CommonMark itself does not standardize tables, so an extension still must be configured ([CommonMark 0.31.2 specification](https://spec.commonmark.org/0.31.2/), 2024, accessed 2026-08-28).

Decided by: performance — the bounded stdlib extension avoids full-document tokenization; it also wins the next-ranked simplicity/LOC criterion and adds no dependency.

<objective>
Implement, independently review, release, merge, install, and close davdittrich/sota-numerics#1 from the completed diagnosis.

Purpose: Common traceability suffixes and ranked Markdown tables must pass the blocking Alternatives Considered gate when their substantive evidence is compliant, while malformed shapes and all existing enforcement semantics remain fail-closed.
Output: Five reviewed source/test/docs/version files at pushed version 0.1.2, successful CI, byte-identical Claude/Codex installations and shared capability, and both trackers closed with terminal evidence.
</objective>

<execution_context>
@/home/dd/.codex/gsd-core/workflows/execute-plan.md
@/home/dd/.codex/gsd-core/templates/summary.md
</execution_context>

<context>
@AGENTS.md
@.planning/STATE.md
@.worktrees/sota-numerics-issue-1/.planning/debug/alternatives-shape-rejection.md
@.worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py
@.worktrees/sota-numerics-issue-1/tests/test_check_alternatives.py
@.worktrees/sota-numerics-issue-1/README.md
@.worktrees/sota-numerics-issue-1/.claude-plugin/plugin.json
@.worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/capability.json
@.worktrees/sota-numerics-issue-1/.github/workflows/ci.yml
@.worktrees/sota-numerics-issue-1/hooks/capability-auto-install.sh
@.claude-plugin/marketplace.json

Authoritative scope is the live open GitHub issue `https://github.com/davdittrich/sota-numerics/issues/1` plus Beads ticket `gsd-beads-p07`. Diagnosis at `.worktrees/sota-numerics-issue-1/.planning/debug/alternatives-shape-rejection.md` is evidence only and must not be committed to sota-numerics. Planning observed target `main` and `origin/main` both at `68c5c9d13cebb031104e19900be78f9d27c1c4c2`, synchronized plugin/capability version 0.1.1, a versionless outer marketplace URL, Claude and Codex installations at 0.1.1, and no tracked target change. Execution must refresh these volatile facts before mutation.
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: Prove shape-only parsing, converge reviews, and deliver 0.1.2</name>
  <beads-id>gsd-beads-p07</beads-id>
  <precondition>The target remote is still `https://github.com/davdittrich/sota-numerics.git`, GitHub issue #1 remains open and ready-for-agent with the observed acceptance criteria, both version files still equal 0.1.1, and the only allowed pre-existing untracked target artifact is the completed `.planning/debug/alternatives-shape-rejection.md` diagnosis.</precondition>
  <reversibility rating="costly">The public main push, 0.1.2 marketplace caches, capability refresh, and tracker closures require a follow-up release or reopen to supersede, but there is no data migration or incompatible API change.</reversibility>
  <files>.worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py, .worktrees/sota-numerics-issue-1/tests/test_check_alternatives.py, .worktrees/sota-numerics-issue-1/README.md, .worktrees/sota-numerics-issue-1/.claude-plugin/plugin.json, .worktrees/sota-numerics-issue-1/.gsd/capabilities/sota-numerics/capability.json</files>
  <behavior>
    - RED/GREEN heading acceptance: with byte-identical section content and invocation, replacing the exact heading by `## Alternatives Considered (REQ-10)` changes failure to success.
    - RED/GREEN heading boundary: with the same body, `## Alternatives ConsideredFoo` remains rejected as a missing section.
    - RED/GREEN table acceptance: a two-or-more-row table whose bold mechanism names, citations, in-window years, and `Decided by:` content equal the passing bullet control exits 0.
    - RED/GREEN row-local evidence: a table row lacking its own citation/date fails and names that alternative even when the adjacent row has valid evidence.
    - RED/GREEN zero-parsed diagnostic: a present section with no recognized bullets or bold mechanism table rows reports `section found but no alternatives parsed` and names both supported entry renderings.
    - RED/GREEN one-entry diagnostic and table framing: one recognized bullet or table entry retains `fewer than 2 named alternatives (found 1)`; a one-real-row table with a bold citation-bearing header and separator must still report exactly `found 1`, proving neither framing row counts.
    - RED/GREEN bullet control: the existing bold-bullet rendering with identical substantive content remains exit 0.
    - Regression: citation count, recency, placeholder, exemption, decision criteria, discovery, dotted filenames, confinement, exit-2 usage/IO behavior, and exactly-one remediation line remain unchanged.
  </behavior>
  <action>Run all source, Git, GitHub, test, review, release, and install work whose cwd is not explicitly overridden in `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-issue-1`; do not revert or absorb other agents' changes. Every Beads read, claim/update, comment, close, and terminal re-read must instead execute with cwd exactly `/home/dd/projects/gsd-beads` (for example, `cd /home/dd/projects/gsd-beads &amp;&amp; bd ...`); never invoke `bd` from the nested source worktree. Run each multi-command operation as one self-contained non-interactive script. Resolve the current default branch and fetch `origin/main`; require the observed main tip to be an ancestor, record it in the dedicated local Git ref `refs/gsd/issue-1-base` with `git update-ref` before creating/reusing `fix/issue-1-alternatives-shapes`, and on resume halt unless that ref still resolves to the branch's original base. Derive `BASE_SHA` only with `git rev-parse refs/gsd/issue-1-base^{commit}` and derive candidate/final SHAs only from `refs/heads/fix/issue-1-alternatives-shapes`; never recover either value from prose, Beads, or a stale shell variable. Preserve the untracked diagnosis outside commits. Before editing, re-read the five declared files, inspect all checker call sites with codegraph or Serena, and record the exact live issue body plus current metadata/install state in a comment on `gsd-beads-p07` from the required outer cwd. If any authority, target, or scope predicate differs materially, halt rather than infer scope.

For every Python test, Bash test, or external review invocation that may allocate temporary files, use the literal environment value `TMPDIR=/home/dd/projects/gsd-beads/.scratch/issue-1-plan`. Create that root once with owner-only permissions before the first invocation; in every self-contained invocation script require it to exist, resolve and compare its real path to the literal path, require owner-only permissions and no descendants, and install an exit trap that deletes only its descendants. Pass `TMPDIR` explicitly to each invocation, consume any result, immediately delete its consumed descendants, and require the directory empty before the next gate and at script end. Never use bare `/tmp`. Do not edit either Bash test solely to redirect its internal `mktemp`; the environment override must contain those allocations.

RED: edit only `tests/test_check_alternatives.py`. Add CLI-boundary cases for the seven behaviors above. Build paired text from shared constants/helpers so the heading pair differs only in the heading line and the table/bullet pair differs only in rendering delimiters; assert their normalized mechanism names, prose, citations, years, and decision text are identical before invoking the checker. The table negative must prove row locality by placing citation/date evidence only in the other row. The one-entry table case must contain exactly one real alternative row beneath a bold citation-bearing header and a separator row, then assert the exact `fewer than 2 named alternatives (found 1)` diagnostic; this is the strict CLI proof that neither header nor separator contributes an entry. Assert exact exit codes and diagnostic fragments, including the absent-heading message, the new zero-parsed message, the named row-local evidence error, and the unchanged one-entry message. Keep every existing test. Migrate every temporary helper and allocation in this test module—including `scratch_dir()`, both remediation `mkdtemp(..., dir=PROJECT_ROOT)` sites, and the default-system `TemporaryDirectory()` path-safety allocation—to one test root read from `TMPDIR`. At module setup, require that environment value, resolve it, require exact equality with `/home/dd/projects/gsd-beads/.scratch/issue-1-plan`, and require the existing directory to contain no descendants; do not fall back to `PROJECT_ROOT`, a default temp directory, or any other path. Make each test allocation a context-managed child of that root so cleanup is automatic per test, and replace the manual remediation cleanup paths accordingly. The project-root-negative CLI regression must not allocate a temporary directory: invoke the public CLI with an existing, verified non-writable directory such as `/usr`, assert it is a directory with no `.planning` ancestor, and assert exit 2 without creating or modifying a file. Do not alter either Bash test, and keep the total source allowlist at the same five files. Run the focused seven tests first, then the whole unittest module under the bounded `TMPDIR` protocol; require the new tests to fail only on the missing heading/table/diagnostic behavior while all pre-existing tests stay green, and require the scratch directory empty after each run. Commit the RED tests as a Conventional Commit with no AI attribution or co-author trailer.

GREEN: change only the parser, README, and synchronized version files. Broaden `SECTION_HEADING_RE` with a word boundary and a same-line bounded suffix so `ConsideredFoo` cannot match. Add one bounded, line-anchored bold-name table-row regex that can match only body rows after the table header and separator; retain bullet entries unchanged and use table-row entries only when bullets do not meet `MIN_ALTERNATIVES`, so formats are not combined to satisfy the count. Pass exactly one body row as each entry's evidence text. In `validate_plan`, preserve the absent-section branch, add the requested zero-parsed diagnostic when `len(entries) == 0`, and leave the existing `found 1` branch for one entry. Do not introduce a parser class, Markdown tokenizer, dependency, or helper used once unless it shortens the existing function without changing behavior. Update README's gate contract and caveats to state the accepted heading suffix boundary, bold bullet and bold table-body-row forms, header/separator exclusion, row-local table evidence, and zero-versus-one diagnostics; do not advertise arbitrary Markdown. Audit Git history and SemVer, then synchronize `.claude-plugin/plugin.json` and the capability manifest from 0.1.1 to the repository-consistent bug-fix release 0.1.2; the outer `gsd-beads` marketplace entry is a versionless Git URL and must remain byte-unchanged. Run the focused tests, full unittest module, both Bash tests, JSON parsing/version equality, `git diff --check`, and an exact five-path diff gate. Apply the bounded `TMPDIR` protocol independently to the Python module and to each Bash test, consume and delete temporary descendants immediately, and prove the scratch directory empty at every gate. Commit GREEN as a Conventional Commit with why, no AI attribution, and no release tag.

Review convergence: review the committed `BASE_SHA..CANDIDATE_SHA` diff before merge. Because `$gsd-review` is a phase-plan reviewer and this is a quick source task with no phase number, reuse its declared external review-lane adapters directly rather than fabricating a phase. Immediately before each explicitly requested `antigravity`, `claude`, and `codex` lane invocation, empty-check `/home/dd/projects/gsd-beads/.scratch/issue-1-plan`, set `TMPDIR` to that exact path for the invocation, and install the bounded cleanup trap. Use the same source-review prompt containing the live issue, diagnosis, acceptance predicates, forbidden scope, Git-ref-derived `BASE_SHA`, Git-ref-derived `CANDIDATE_SHA`, exact committed diff, five allowed source files, and test evidence. Consume the lane result, delete its consumed scratch descendants immediately, and prove the directory empty before invoking the next lane. Separately dispatch a short-lived independent reviewer loaded with the `critical-code-reviewer` skill and the same exact committed SHA/range. The critical reviewer is read-only: it may inspect only `git diff BASE_SHA..CANDIDATE_SHA` and the five committed files, must not run tests, builds, formatters, package managers, cache writers, or any other temp-producing command, and must not edit or create files. If it runs any read-only command, invoke that command as `env TMPDIR=/home/dd/projects/gsd-beads/.scratch/issue-1-plan ...`; require its Blocking/Required/Suggestions/Verdict return to state `scratch_proof=NO_TEMP_FILES_CREATED` or cite an empty-scratch check as `scratch_proof=EMPTY`. Reject the critical review unless that evidence is present and the orchestrator independently proves the scratch root empty afterward. The requested typo flags normalize to the supported `--antigravity` and `--codex` lanes. Reject any response that is empty, permission-denied, malformed, lacks file/line citations, omits the candidate SHA, reviews a stale SHA, lacks explicit PASS/BLOCK, or omits scratch proof. Every finding carries a 0–100 confidence score. Add source-cited review summaries and exact SHA to `gsd-beads-p07` using `bd` only from `/home/dd/projects/gsd-beads`, then require the scratch directory empty.

Fix every in-scope Blocking and Required finding at its root cause, retain all forbidden behavior, commit each coherent correction atomically, and rerun all local gates with the same per-invocation `TMPDIR` setup, immediate cleanup, and empty-directory assertions. A requested scope expansion outside issue #1 halts for user approval; it is not silently implemented. Regardless of whether the first round found blockers, fetch `origin/main` again before final review. If remote main advanced, rebase the clean issue branch onto it, update `refs/gsd/issue-1-base` to that observed pre-rebase `origin/main`, and rerun all gates. Then derive `BASE_SHA` from `refs/gsd/issue-1-base` and `FINAL_SHA` from `refs/heads/fix/issue-1-alternatives-shapes`, prove `git diff --name-only "$BASE_SHA..$FINAL_SHA"` equals exactly the five relative source paths in `files_modified`, and invoke all four requested reviewers again against that exact range under the same bounded scratch protocol and critical-review restrictions; all four must explicitly PASS with no unresolved in-scope Blocking or Required finding. Write exactly one final Beads comment per reviewer using the machine-parseable single-line format `GSD_REVIEW|reviewer=&lt;antigravity|claude|codex|critical-code-reviewer&gt;|FINAL_SHA=&lt;40-hex&gt;|verdict=PASS|citations=&lt;file:line[,file:line...]&gt;|confidence=&lt;0-100&gt;|scratch=&lt;EMPTY|NO_TEMP_FILES_CREATED&gt;`. Use `cd /home/dd/projects/gsd-beads &amp;&amp; bd comments add gsd-beads-p07 "..."` for writes; the installed read syntax is `cd /home/dd/projects/gsd-beads &amp;&amp; bd comments gsd-beads-p07 --json` (not `bd comments list`). Query those comments before release and fail unless exactly four records have the current `FINAL_SHA`, `verdict=PASS`, valid citations/confidence/scratch proof, and the four distinct required reviewer names. Require the scratch directory empty. Do not accept a prior-SHA review as final.

Release: require the branch clean except the untracked diagnosis, exact five-file committed scope, versions 0.1.2, all tests green, and four final-SHA approvals. Switch to `main`, fast-forward it to current `origin/main`, merge `fix/issue-1-alternatives-shapes` with `--ff-only`, and require merged HEAD to equal `FINAL_SHA`; any merge/rebase content change invalidates reviews and sends execution back through all gates and four final reviews. Push `main` normally, never force. Verify `origin/main`, local main, and `FINAL_SHA` are identical. Resolve exactly one GitHub Actions push run for `FINAL_SHA` whose workflow name is `CI`, extract its numeric run ID, and use the built-in `gh run watch <id> --exit-status`; zero or multiple matching runs is an ambiguity and halts.

Install and close: after CI succeeds, run `claude plugin marketplace update gsd-beads` and `claude plugin update sota-numerics@gsd-beads --scope user -y`; if the Claude registry version is not exactly 0.1.2, use the single native fallback `claude plugin uninstall sota-numerics@gsd-beads --scope user --keep-data -y` followed by `claude plugin install sota-numerics@gsd-beads --scope user -y`. Run `codex plugin marketplace upgrade gsd-beads --json` and `codex plugin add sota-numerics@gsd-beads --json`; use one native remove/add fallback only if the Codex registry version is not exactly 0.1.2. Resolve each cache path from the runtime registries/current marketplace layout, require both plugin registries to report 0.1.2, and explicitly run the installed Claude cache's `hooks/capability-auto-install.sh sota-numerics` with `CLAUDE_PLUGIN_ROOT` set to that cache. Compare SHA-256 manifests over the exact source `git ls-files` set against both caches using process substitution, and require `diff -qr` between source and `/home/dd/.gsd/capabilities/sota-numerics` to be empty. Do not write parity manifests to disk. Immediately before either closure, re-derive `BASE_SHA` and `FINAL_SHA` from their Git refs, rerun the exact five-path committed-diff gate, query `bd comments gsd-beads-p07 --json` from `/home/dd/projects/gsd-beads`, and fail unless exactly the four required machine-parseable final-review records match `FINAL_SHA` and PASS. Only after remote SHA, CI, that comment gate, two runtime versions, two tracked-payload comparisons, capability parity, and an empty scratch directory pass, close GitHub issue #1 as completed with `FINAL_SHA`/CI/install evidence; then close `gsd-beads-p07` with the same evidence and re-read it using `bd` only from `/home/dd/projects/gsd-beads`, while the GitHub tracker may be re-read from the nested source worktree.</action>
  <verify>
    <automated>PLAN_TMPDIR=/home/dd/projects/gsd-beads/.scratch/issue-1-plan &amp;&amp; SOURCE_ROOT=/home/dd/projects/gsd-beads/.worktrees/sota-numerics-issue-1 &amp;&amp; test -d "$PLAN_TMPDIR" &amp;&amp; test "$(realpath "$PLAN_TMPDIR")" = "$PLAN_TMPDIR" &amp;&amp; test "$(stat -c '%a' "$PLAN_TMPDIR")" = 700 &amp;&amp; test -z "$(find "$PLAN_TMPDIR" -mindepth 1 -print -quit)" &amp;&amp; trap 'find "$PLAN_TMPDIR" -mindepth 1 -delete' EXIT &amp;&amp; cd "$SOURCE_ROOT" &amp;&amp; BASE_SHA=$(git rev-parse refs/gsd/issue-1-base^{commit}) &amp;&amp; FINAL_SHA=$(git rev-parse refs/heads/fix/issue-1-alternatives-shapes^{commit}) &amp;&amp; EXPECTED_PATHS=$(printf '%s\n' '.claude-plugin/plugin.json' '.gsd/capabilities/sota-numerics/capability.json' '.gsd/capabilities/sota-numerics/scripts/check-alternatives.py' 'README.md' 'tests/test_check_alternatives.py') &amp;&amp; test "$(git diff --name-only "$BASE_SHA..$FINAL_SHA")" = "$EXPECTED_PATHS" &amp;&amp; env TMPDIR="$PLAN_TMPDIR" python3 -m unittest tests/test_check_alternatives.py &amp;&amp; find "$PLAN_TMPDIR" -mindepth 1 -delete &amp;&amp; test -z "$(find "$PLAN_TMPDIR" -mindepth 1 -print -quit)" &amp;&amp; env TMPDIR="$PLAN_TMPDIR" bash tests/test-session-start.sh &amp;&amp; find "$PLAN_TMPDIR" -mindepth 1 -delete &amp;&amp; test -z "$(find "$PLAN_TMPDIR" -mindepth 1 -print -quit)" &amp;&amp; env TMPDIR="$PLAN_TMPDIR" bash tests/test-gate-script-resolution.sh &amp;&amp; find "$PLAN_TMPDIR" -mindepth 1 -delete &amp;&amp; test -z "$(find "$PLAN_TMPDIR" -mindepth 1 -print -quit)" &amp;&amp; jq -e '.version == "0.1.2"' .claude-plugin/plugin.json &amp;&amp; jq -e '.version == "0.1.2"' .gsd/capabilities/sota-numerics/capability.json &amp;&amp; git diff --check "$BASE_SHA..$FINAL_SHA" &amp;&amp; test "$(git ls-remote origin refs/heads/main | cut -f1)" = "$FINAL_SHA" &amp;&amp; test "$(git rev-parse refs/heads/main^{commit})" = "$FINAL_SHA" &amp;&amp; gh run list --repo davdittrich/sota-numerics --workflow ci.yml --commit "$FINAL_SHA" --event push --limit 10 --json databaseId,headSha,workflowName,conclusion | jq -e --arg sha "$FINAL_SHA" 'length == 1 and .[0].headSha == $sha and .[0].workflowName == "CI" and .[0].conclusion == "success"' &amp;&amp; test "$(claude plugin list --json | jq -r '.[] | select(.id == "sota-numerics@gsd-beads") | .version')" = "0.1.2" &amp;&amp; test "$(codex plugin list --json | jq -r '.installed[] | select(.pluginId == "sota-numerics@gsd-beads") | .version')" = "0.1.2" &amp;&amp; diff -u &lt;(git ls-files -z | xargs -0 sha256sum) &lt;(git ls-files -z | (cd /home/dd/.claude/plugins/cache/gsd-beads/sota-numerics/0.1.2 &amp;&amp; xargs -0 sha256sum)) &amp;&amp; diff -u &lt;(git ls-files -z | xargs -0 sha256sum) &lt;(git ls-files -z | (cd /home/dd/.codex/plugins/cache/gsd-beads/sota-numerics/0.1.2 &amp;&amp; xargs -0 sha256sum)) &amp;&amp; diff -qr .gsd/capabilities/sota-numerics /home/dd/.gsd/capabilities/sota-numerics &amp;&amp; cd /home/dd/projects/gsd-beads &amp;&amp; bd comments gsd-beads-p07 --json | jq -e --arg sha "$FINAL_SHA" '[.[] | .text | select(startswith("GSD_REVIEW|")) | select(contains("|FINAL_SHA=" + $sha + "|"))] as $tagged | [$tagged[] | capture("^GSD_REVIEW\\|reviewer=(?&lt;reviewer&gt;antigravity|claude|codex|critical-code-reviewer)\\|FINAL_SHA=(?&lt;sha&gt;[0-9a-f]{40})\\|verdict=(?&lt;verdict&gt;PASS|BLOCK)\\|citations=(?&lt;citations&gt;[^|]+:[0-9]+(?:,[^|]+:[0-9]+)*)\\|confidence=(?&lt;confidence&gt;[0-9]{1,3})\\|scratch=(?&lt;scratch&gt;EMPTY|NO_TEMP_FILES_CREATED)$")] as $records | ($tagged | length) == 4 and ($records | length) == 4 and all($records[]; .sha == $sha and .verdict == "PASS" and (.confidence | tonumber) &gt;= 0 and (.confidence | tonumber) &lt;= 100) and ([$records[].reviewer] | sort) == ["antigravity","claude","codex","critical-code-reviewer"]' &amp;&amp; cd "$SOURCE_ROOT" &amp;&amp; gh issue view 1 --repo davdittrich/sota-numerics --json state,stateReason | jq -e '.state == "CLOSED" and .stateReason == "COMPLETED"' &amp;&amp; cd /home/dd/projects/gsd-beads &amp;&amp; bd show gsd-beads-p07 --json | jq -e '.[0].status == "closed"' &amp;&amp; test -z "$(find "$PLAN_TMPDIR" -mindepth 1 -print -quit)"</automated>
  </verify>
  <done>The public CLI accepts the suffixed heading and compliant bold-name table rows, rejects the concatenated heading, keeps table evidence row-local, distinguishes zero parsed entries from one, and preserves the existing bullet control plus every out-of-scope rule. README matches executable syntax. Exactly five source files deliver synchronized 0.1.2. Antigravity, Claude, Codex, and critical-code reviewers cite and PASS the exact final SHA with no unresolved in-scope Blocking or Required finding. That SHA is fast-forward merged and pushed to main, its unique CI push run succeeds, Claude/Codex tracked payloads and the shared capability are byte-identical to source, both registries report 0.1.2, the scratchpad is empty, and both issue #1 and gsd-beads-p07 are closed only after terminal proof.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Untrusted PLAN.md text -> regex parser | Authored Markdown controls section and entry extraction but must never execute or escape validation. |
| Table row -> entry evidence validator | Citation/date evidence must remain local to one alternative row. |
| External reviewer output -> release decision | Independent model output may identify defects but cannot redefine scope or spoof approval for another SHA. |
| Local reviewed branch -> `origin/main` -> GitHub Actions | Only the exact reviewed commit may be merged, pushed, and accepted by CI. |
| Marketplace source -> Claude/Codex caches -> user capability | Installer-controlled copies must match the pushed tracked bytes before closure. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-OLQ-01 | Denial of Service | Heading/table regexes | high | mitigate | Keep patterns line-anchored and quantitatively bounded, avoid nested unbounded quantifiers, and retain a timeout at the gate boundary. |
| T-OLQ-02 | Tampering | Row-local citations | high | mitigate | Feed only the matched row to the unchanged validator and prove adjacent-row evidence cannot satisfy a deficient row. |
| T-OLQ-03 | Spoofing | Heading boundary | medium | mitigate | Require a word boundary after `Considered`; the concatenated-heading CLI test remains red unless rejected. |
| T-OLQ-04 | Elevation of Privilege | Parser scope | high | mitigate | Exact regression gates preserve exemption, placeholders, recency, decision criteria, confinement, exit codes, and blocking/onError semantics. |
| T-OLQ-05 | Repudiation | Cross-AI reviews | medium | mitigate | Require exact SHA, file/line citations, confidence, explicit verdict, and Beads evidence for both review rounds. |
| T-OLQ-06 | Tampering | Merge/push/CI | high | mitigate | Fast-forward only, no force push, exact final-SHA equality, and one uniquely resolved successful CI push run. |
| T-OLQ-07 | Tampering | Runtime installs | high | mitigate | Native installers, registry version checks, tracked-file SHA-256 comparisons, and recursive capability diff. |
| T-OLQ-08 | Denial of Service | Temporary review/test data | medium | mitigate | Constrain every test and review invocation through the named `TMPDIR`, preserve the separately isolated no-project-root CLI regression without file creation, and require immediate cleanup plus an empty scratchpad at every gate. |
| T-OLQ-SC | Tampering | npm/pip/cargo installs | low | accept | No package dependency is added; the selected mechanism uses Python's standard library and existing native plugin marketplaces only. |
</threat_model>

## Multi-Source Coverage Audit

| Source | ID | Feature / Requirement | Covered by | Status | Notes |
|---|---|---|---|---|
| GOAL | gsd-beads-p07 | Implement and deliver davdittrich/sota-numerics#1 | Task 1 end-to-end tracer | COVERED | Includes TDD, review, release, merge, push, installs, and closures. |
| REQ | issue #1 symptom 1 | Accept suffixed heading while rejecting concatenation | Heading RED/GREEN pair | COVERED | Shape is the only varying input. |
| REQ | issue #1 symptom 2 | Accept bold-name table rows | Table/bullet RED/GREEN pair | COVERED | Same names, evidence, years, and decision text. |
| REQ | issue #1 suggested fix 2 | Keep evidence scoped per table row | Row-local negative | COVERED | Neighbor evidence cannot leak. |
| REQ | issue #1 suggested fix 3 | Distinguish absent, zero parsed, and one parsed | Diagnostic tests and branch | COVERED | Absent and one-entry wording remain stable. |
| REQ | user | Preserve counts, citations, recency, placeholders, exemption, criteria, discovery, confinement, blocking | Forbidden, regressions, threat model | COVERED | No enforcement weakening. |
| REQ | user | Strict CLI-boundary TDD with seven named cases | Task behavior and RED action | COVERED | Tests precede production edits and RED evidence is required. |
| REQ | user | Ponytail-minimal parser fix | Mechanism, alternatives, GREEN action | COVERED | Two regex seams; no dependency or parser framework. |
| REQ | user | Docs match executable syntax | README action and key link | COVERED | No broader Markdown claim. |
| REQ | user | Version audit and marketplace synchronization | 0.1.2 metadata, release/install action | COVERED | Outer marketplace is versionless and unchanged. |
| REQ | user | Antigravity, Claude, Codex, and critical reviews; fix blockers; final-SHA rerun | Review convergence | COVERED | Both rounds reject stale or malformed output. |
| REQ | user | Merge, push, CI, Claude/Codex update, byte/hash parity | Release and install action | COVERED | Exact reviewed SHA is terminal authority. |
| REQ | user | Close trackers only after terminal evidence | Final action and automated verify | COVERED | Both live states are re-read. |
| RESEARCH | 2026 best practice | Compare regex, state parser, and Markdown AST using current official sources | Alternatives Considered | COVERED | Performance > simplicity/LOC > ecosystem > maintenance decides. |
| CONTEXT | completed debug | Two independent narrow-grammar root causes, no configuration/environment confound | Context and Task 1 | COVERED | Diagnosis is read-only evidence and remains uncommitted. |

<verification>
1. Preserve RED evidence for all seven CLI-boundary cases before production edits; shape-only controls must compare their non-rendering content before invocation.
2. Run all existing unit and Bash tests after every implementation or review-fix commit; no pre-existing enforcement path may regress.
3. Require exact five-file scope, synchronized 0.1.2 metadata, valid JSON, README/source grammar agreement, and `git diff --check` before review and release.
4. Require two explicit review rounds from Antigravity, Claude, Codex, and the critical reviewer, with the second round bound to the final SHA and no unresolved in-scope Blocking or Required finding.
5. Require local/remote/final SHA equality, a unique successful CI push run, two native registry versions, tracked-source hash parity for both caches, recursive shared-capability parity, empty scratchpad, and both tracker closures.
</verification>

<success_criteria>
- The two issue reproductions pass with rendering shape as the sole changed variable.
- Concatenated headings, row-local evidence failures, and zero/one-entry diagnostics behave exactly as specified.
- All existing enforcement and failure semantics remain unchanged outside the two accepted shapes and zero-entry diagnostic.
- README, parser, tests, plugin metadata, and capability metadata are the only changed source files.
- All requested reviewers approve the final delivered SHA after blocker convergence.
- Version 0.1.2 is pushed on main, CI passes, and Claude/Codex/shared-capability bytes match source.
- GitHub issue #1 and gsd-beads-p07 close only after every preceding predicate passes.
</success_criteria>

<output>
Create `.planning/quick/260828-olq-implement-davdittrich-sota-numerics-1-in/260828-olq-SUMMARY.md` when done and keep `gsd-beads-p07` authoritative for execution, review, release, install, and closure evidence.
</output>
