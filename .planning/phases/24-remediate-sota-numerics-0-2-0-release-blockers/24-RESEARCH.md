# Phase 24: Remediate sota-numerics 0.2.0 release blockers and publish - Research

**Researched:** 2026-09-07
**Domain:** Bash/Python CLI tooling, GSD capability-plugin hook lifecycle, regex-based CommonMark-adjacent parsing, git-provenance shell guards, GitHub PR review-thread reconciliation
**Confidence:** HIGH (all load-bearing claims verified by opening source files this session, several by independent reproduction; a small number of scope/ambiguity items are flagged LOW and routed to Assumptions Log / Open Questions)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Repair the parsers that already exist in `check-alternatives.py`. Add no new predicate. This does not reopen Phase 23 D-01: D-01 froze the gate's *contract* against new checks, and a check that returns exit 0 for a document with no Alternatives Considered section is not enforcing the contract it already declares.
- **D-02:** Root cause of shape 1 (a section nested inside an indented fenced code block passes at exit 0): the matcher reads code blocks as prose. Strip fenced spans — both ``` and ~~~, at any indentation — from the document before any section, bullet, or citation match runs.
- **D-03:** Root cause of shape 3 (a cited requirement carried only on a nested sub-bullet passes at exit 0): `BULLET_RE` at line 115 accepts unbounded leading indentation. Bound it to the CommonMark top-level range, 0 to 3 spaces of indentation, so a nested sub-bullet no longer satisfies a top-level entry requirement.
- **D-04:** Root cause of shape 2 (a state document whose phase marker sits in unindented frontmatter passes at exit 0): the frontmatter parse at line 241 takes the first match while the body parse at lines 255-261 demands exactly one. Make both apply the same rule — exactly one match, with more than one reported as a named failure rather than silently resolved.
- **D-05:** Regression evidence, and the reason it is required before any of D-02 through D-04 is accepted: tightening a `blocking: true` gate with `onError: halt` can newly halt planning on documents that pass today. Run the gate over every planning document in both repositories before and after the change. The only verdicts allowed to change are the three crafted fail-open fixtures. Any other changed verdict is a finding, not a pass.
- **D-06:** The three shapes become fixtures in the existing Python suite. This does not violate Phase 23 D-21: D-21 forbade test infrastructure for *prose*, and these are gate-behavior tests of the kind the suite already holds.
- **D-07:** Bound every diagnostic the gate emits. One failure path currently joins a whole entry span into a single line, measured at 8,099 tokens. A gate that reports a failure by flooding the context window defeats the purpose it was added for.
- **D-08:** The bounded shape follows the precedent the capability already documents (Phase 23 D-13): one `<plan_path>:<line>: <reason>` line per violation, any quoted span truncated with an explicit elision marker, then exactly one `remediation: ...` line for the run.
- **D-09:** Hand-maintained counts are drift by construction. `CHANGELOG.md` line 12 reports 94/62/32 where HEAD has 97/62/35, and `check-alternatives.py` line 47 claims "76 entries across phase directories" where the live count is 73. Prefer deleting a count that no mechanism keeps true over correcting it to a value that will be stale again; keep a number only where something recomputes or checks it.
- **D-10:** `README.md` line 58 describes `__pycache__` handling the code does not implement, and line 93 references `draft-PLAN.md`, which does not exist. Correct or delete both, then re-run the Phase 23 D-20 claim trace over the whole README rather than only the lines Phase 23 touched — the trace missed these, so its coverage is the defect, not just the two claims.
- **D-11:** `favor`/`favour` drift inside one corpus: pick the spelling the rest of the corpus already uses, verified by count rather than assumed, and apply it corpus-wide.
- **D-12:** The `sota-numerics` description in this repository's `.claude-plugin/marketplace.json` no longer matches the plugin manifest description on the branch. Update the marketplace entry to match, as its own commit in `gsd-beads`. Because the marketplace entry is what installers read, the two repositories must be consistent at the moment of merge, not afterwards.
- **D-13:** `hooks/gsd-tools.sh` lines 5-7 run `git rev-parse --show-toplevel` without `-C` and use the result to locate the node entry point, so a hostile repository in the invoking working directory gets code execution. It is byte-identical to `origin/main`, so it is pre-existing rather than introduced here — and it ships with 0.2.0, so it is fixed here. Resolve the entry point relative to the script's own location, not the caller's working directory.
- **D-14:** The same pattern appears in `hooks/session-start.sh`. Check every hook in the bundle for it rather than fixing only the two the review named.
- **D-15:** The CodeRabbit finding on PR #4 about the duplicate `current_phase` parse is unanswered. D-04 addresses the same code. Answer the thread with what changed, or with the reason the finding does not hold — an unanswered bot finding on a publish PR is an open question, not a closed one.
- **D-16:** Publish ordering is unchanged from Phase 23 D-26. Every fix in this phase lands on the branch before external review runs again. PR #4 stays open and is treated as a known-incomplete diff until this phase verifies.
- **D-17:** Editing the bundle in `.worktrees/sota-numerics-release-013` changes its bundle hash, and the in-tree plugin's `SessionStart` and `SubagentStart` hooks then install the *uncommitted* bundle to the global mirror via `capability-auto-install.sh`. Verified 2026-09-07: `hooks/hooks.json` matches `startup|resume|clear|compact` plus the three GSD subagents, and the script has no opt-out env var. The effect is local to this machine and is not a publish, so it is accepted rather than prevented — but it is made visible: record `~/.gsd/capability-auto-install-sota-numerics.hash` before and after each plan, and restore the mirror from the released plugin-cache bundle when the phase ends.
- **D-18:** Rejected alternative — move the worktree outside the project tree so Claude Code never loads it as a plugin. The project rule requires worktrees to stay under the project root, and relocating the checkout to dodge a hook is a workaround whose cost lands on every later session that expects the worktree where the rule puts it.
- **D-19:** The marketplace entry points at the repository URL rather than at a tag, so merging to `main` is the publish. There is no separate release step: everything that must be true of a release must be true before the merge.
- **D-20:** Publish ordering. Internal review and every fix it accepts land on the branch before the pull request opens. CI must be green on the exact commit that reaches `main`. Any claim the release makes about behavior traces to code, not to an assertion in the pull request body.
- **D-21:** Tag the published commit `v0.2.0`. `0.1.3` left no immutable marker for what was served.
- **D-22:** The publish is the final wave of this phase and is guarded by a `checkpoint:decision` task, exactly as 23-05 Task 2 was. That checkpoint's first answer, recorded 2026-09-07, was `hold`. It is re-asked after the remediation waves verify and answered fresh — a prior `hold` is not carried forward as a standing no, and it is not treated as spent either.
- **D-23:** Reuse the existing bd issues rather than creating new ones: `gsd-beads-sac.14` for the decision checkpoint, `gsd-beads-sac.15` for push, pull request, CI and merge, `gsd-beads-sac.16` for the tag. Carry those exact `<beads-id>` values into the corresponding tasks of this phase's publish plan. The `hold` answer and its findings are already comments on `.14`; a fresh issue would orphan that record.
- **D-24:** This phase ends at published `0.2.0` with the commit tagged, or at a second recorded `hold` — not at "remediation done".

### Claude's Discretion

- Exact regex construction for D-02 through D-04, provided D-05's evidence holds.
- Exact truncation width for D-08.
- Which counts in D-09 are deleted and which are kept with a mechanism.
- Commit granularity within the branch.

### Deferred Ideas (OUT OF SCOPE)

None recorded in 24-CONTEXT.md — the Phase Boundary explicitly excludes "new gate predicates beyond repairing the ones that already exist, any new capability feature, and the content decisions Phase 23 already accepted and verified (the six added dimensions, the fragment slicing, the 45-line budget)."
</user_constraints>

<phase_requirements>
## Phase Requirements

Phase 24 has no `REQUIREMENTS.md`-traced ID set. Per 24-CONTEXT.md `<domain>`: "The four review reports in this directory are the requirement source: `REVIEW-CRITICAL-FINAL.md`, `REVIEW-PONYTAIL-FINAL.md`, `REVIEW-AGY-FINAL.md`, `REVIEW-PROSE-TOKENS.md`. Every finding they mark blocking is in scope; every finding they mark non-blocking needs an explicit decision to fix or to ticket, never a silent drop." The 24 locked decisions (D-01…D-24) above are the mechanically checkable restatement of those findings and are what this research maps evidence against.

| Decision | Description | Research Support |
|----|-------------|------------------|
| D-01–D-06 | Repair 3 fail-open gate shapes; add regression fixtures | § Fail-open shapes: verified line numbers, independently reproduced all three, ranked masking mechanisms |
| D-07–D-08 | Bound gate diagnostics | § Diagnostic flooding: reproduced 8,098-token failure, root cause pinned, precedent format confirmed |
| D-09–D-11 | Delete/fix stale hand-maintained claims | § Stale claims sweep: independently recomputed every count, confirmed drift/no-drift for each |
| D-12 | Cross-repo marketplace description sync | § Cross-repo description diff: all 3 verbatim strings captured |
| D-13–D-14 | Fix cwd-rooted `git rev-parse` code-execution surface | § Hook resolver defect: full bundle sweep, single-fix-point identified, third undocumented site found |
| D-15–D-16 | Answer/resolve outstanding CodeRabbit threads | § PR #4 review-thread sweep: all threads triaged against the 4 reports |
| D-17–D-18 | Execution hazard bookkeeping | § Worktree auto-install hazard: hash-sidecar mechanism confirmed, compliance verified this session |
| D-19–D-24 | Publish sequencing | § Publish mechanics: bd issue IDs, tag, CI gate confirmed from `ci.yml` and `STATE.md` |
</phase_requirements>

## Summary

Phase 24 is a remediation-and-publish phase, not a feature phase: every locked decision names an already-identified defect in an already-written 675-line Python gate script (`check-alternatives.py`), four POSIX shell hook scripts, three Markdown documents, and one cross-repo JSON manifest, all living in the `feat/extended-sota-definition` branch of `davdittrich/sota-numerics`, checked out read-only at `.worktrees/sota-numerics-release-013`. No new library, framework, or external dependency is introduced anywhere in this phase — every fix is a stdlib-only regex/parsing change (Python `re`) or a POSIX shell path-resolution change. The planner's job is to sequence eleven independent, mechanically verifiable fixes plus one cross-repo edit plus a publish wave, not to select a stack.

Three fail-open shapes in the gate's regex layer were independently reproduced this session with real fixtures and real exit codes (not merely cited from the review reports): (1) a bullet indented 4+ spaces — CommonMark's *indented code block* construct, not a fenced block — is invisible to a human reading the rendered plan but is still counted by the unbounded-indentation `BULLET_RE`, letting one real alternative plus one hidden bullet satisfy the `MIN_ALTERNATIVES=2` floor; backtick/tilde-fenced code (```` ``` ````/`~~~`) is, by contrast, already correctly masked at any indentation up to 3 spaces (confirmed this session — not itself broken); (2) the same unbounded-indentation `BULLET_RE` also lets a nested sub-bullet under a real alternative count as a second, independent alternative; (3) the STATE.md frontmatter phase-marker parser takes the *first* regex match where the body parser two blocks below it demands *exactly one* — an asymmetry the code itself already knows how to fix, because the correct pattern is 14 lines away in the same file. A fourth, unbounded-diagnostic defect was reproduced at 8,098 tokens on a single stderr line (root cause: an unbounded `", ".join(...)` over cited years, line 537), closely matching the reviews' reported 8,099.

The `hooks/gsd-tools.sh` code-execution surface (D-13/D-14) is real, pre-existing (byte-identical to `origin/main`), and has exactly one primary fix point — removing the unanchored `git rev-parse --show-toplevel` rung inside `gsd-tools.sh` itself fixes every hook that sources it (`session-start.sh`, `capability-auto-install.sh`). This session found a **third, independent occurrence** of the identical unanchored-`git rev-parse` pattern inside `.gsd/capabilities/sota-numerics/capability.json`'s gate `command` string (not inside `hooks/`, and not fixable by editing `gsd-tools.sh`) — flagged below as a scope question for the planner, since D-14's literal text names "every hook in the bundle" and this site is a gate predicate, not a hook file, yet shares the identical vulnerability shape.

**Primary recommendation:** Sequence the plan as (a) one wave for the three fail-open regex fixes plus D-05 regression evidence plus D-06 fixtures — these are interdependent and must land together since the fixtures ARE the regression evidence; (b) one wave for diagnostic bounding (D-07/D-08), independent of (a); (c) one wave for the stale-claims sweep (D-09/D-10/D-11), independent of (a)/(b); (d) one wave for the security fix (D-13/D-14), independent of the above three but should explicitly decide the capability.json scope question before closing; (e) one wave for the cross-repo marketplace edit (D-12) and the CodeRabbit thread answers (D-15), which depend on (a)-(d) having landed; (f) the publish wave (D-19-D-24) gated by a fresh `checkpoint:decision`, strictly last, per D-16/D-20.

## Architectural Responsibility Map

This phase's domain is a CLI/hook-lifecycle plugin, not a client-server web app; the standard browser/API/DB tier table does not apply. The adapted tiers below reflect where each capability's logic actually executes.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Alternatives-section parsing (fenced/indented masking, bullet bound, citation/year validation) | Gate Predicate (Python, `check-alternatives.py`) | — | Runs synchronously inside the `plan:post` `command-exit-zero` predicate; no other tier touches this logic |
| Phase-resolution (frontmatter vs. body two-witness parse) | Gate Predicate (Python) | Planning Document (`.planning/STATE.md`) as data source | The parser lives in the gate; STATE.md is read-only input data, not logic |
| Diagnostic emission/bounding | Gate Predicate (Python), stderr | Orchestrator prompt (consumes stderr on exit 1) | Bounding must happen at emission time — the consumer (orchestrator) has no truncation of its own |
| Node-entry-point / gsd-tools resolution | Hook/Lifecycle Script (POSIX shell, `hooks/*.sh`) | — | Runs at `SessionStart`/`SubagentStart`, before any Python or planner logic executes |
| Bundle-hash provenance guard | Hook/Lifecycle Script (`capability-auto-install.sh`) | Git (ancestry/dirty checks against `origin/main`) | The guard's decision logic is entirely shell + git plumbing, no other tier |
| Marketplace manifest description | Marketplace Manifest (`gsd-beads` repo, `.claude-plugin/marketplace.json`) | Plugin Manifest (`sota-numerics` repo, `.claude-plugin/plugin.json`) | Two independent JSON files in two independent git repos that must agree at merge time (D-12) |
| PR review-thread resolution | External Service (GitHub GraphQL API) | — | Read/reconciled via `gh api graphql`; not part of the runtime system at all |

## Standard Stack

### Core

No new libraries are introduced by this phase. Every fix operates on the existing stack already committed to the branch:

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3 stdlib `re` | (stdlib, no pinned version) | Regex-based section/bullet/citation/year parsing in `check-alternatives.py` | `[VERIFIED: .worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py]` — file has zero third-party imports; `import re, sys, argparse, tempfile...` style stdlib-only header confirmed by reading the full file this session |
| Python 3 stdlib `unittest` | (stdlib) | `tests/test_check_alternatives.py` (1515 lines) | `[VERIFIED: .worktrees/sota-numerics-release-013/tests/test_check_alternatives.py:1-50]` — `subprocess.run([sys.executable, str(SCRIPT), ...])` isolation pattern read directly |
| POSIX `sh`/`bash` | (system) | All four hook scripts (`session-start.sh`, `capability-auto-install.sh`, `gsd-tools.sh`, and 3 `tests/test-*.sh` suites) | `[VERIFIED: .worktrees/sota-numerics-release-013/hooks/*.sh]` — all read in full this session; no non-POSIX bashisms beyond arrays (`bash` shebang present) |
| `gh` CLI | (system, already installed and used this session) | PR #4 review-thread reconciliation (D-15) | `[VERIFIED]` — invoked successfully this session (`gh pr view`, `gh api graphql`) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tiktoken` (`cl100k_base`) | already used in prior review (REVIEW-PROSE-TOKENS.md) | Measuring real token counts for diagnostic-bounding verification | Verification-only tool, not a runtime dependency of the shipped code; used this session to independently reproduce the 8,099-token claim (got 8,098, same order of magnitude, confirms defect) |

### Alternatives Considered

Because this phase adds no new mechanism (D-01 explicitly forbids a new predicate; all fixes repair existing stdlib-only code), the standard "Alternatives Considered" comparison applies narrowly, to the *masking mechanism* used inside `check-alternatives.py` for D-02:

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Regex-based line-state-machine masking (current approach: `FENCE_LINE_RE`/`mask_fenced_regions`, extended for D-02/D-03 fixes) | A real CommonMark parser (e.g., `markdown-it-py`, `mistune`) | Adds a third-party dependency to a script whose entire value proposition (per `capability.json`'s own `description`, `[VERIFIED: .gsd/capabilities/sota-numerics/capability.json]`) is being stdlib-only and auditable in one file; a full CommonMark AST is more correct on edge cases (e.g., lazy continuation lines) but the gate only needs 3 constructs masked (fences, indented code blocks, HTML comments), not full CommonMark fidelity |
| Regex-based masking | Hand-rolled character-by-character line scanner (no regex) | More lines of code for equivalent correctness on the 3 needed constructs; the existing `NEXT_HEADING_RE`/`FENCE_LINE_RE` precedent in the same file already uses the correct CommonMark bound (`[ \t]{0,3}`, i.e. 0-3 leading spaces) for fence/heading recognition, so a regex extension is a 1-line-pattern change, not a new subsystem |

**Ranking (performance → LOC → ecosystem support → maintenance, per project's stated mechanism-justification order):**
1. **Performance:** regex extension and a real CommonMark parser are both effectively instant on plan-sized documents (KB scale); no measurable difference.
2. **LOC / simplicity:** regex extension wins decisively — D-02 (extend fence-masking loop to also blank 4+-space indented-code-block lines) and D-03 (bound `BULLET_RE`'s leading-whitespace group to `{0,3}`) are each a 1-2 line diff to an existing, already-read, already-tested function. A CommonMark parser dependency would require rewriting the entire section/bullet/citation extraction pipeline around the parser's AST shape — hundreds of lines, not 2.
3. **Ecosystem support:** stdlib `re` has zero install/version-pinning surface; `markdown-it-py`/`mistune` would need Package Legitimacy Audit, a `requirements.txt`, and CI changes to `pip install` before running `python3 -m unittest`.
4. **Maintenance:** the existing code already documents (per `.gsd/capabilities/sota-numerics/NOTES.md` and `README.md`, both read this session) that it deliberately does not depend on a markdown library, and Phase 23 D-01 froze the gate's *contract* (mechanically measurable, no vibes-based checks) — introducing a parser dependency is exactly the kind of "new predicate"/mechanism change D-01 in this phase's own CONTEXT explicitly forbids ("Add no new predicate").

**Verdict: regex extension is correct on all four axes and is what D-02/D-03's own wording ("Strip fenced spans... Bound it to the CommonMark top-level range, 0 to 3 spaces") already prescribes.** This is not an open design choice for the planner — CONTEXT already locked the mechanism; the ranking above is the justification record the project's Architectural Integrity rule requires.

**Installation:** None. No `pip install` / `npm install` step is added by this phase.

## Package Legitimacy Audit

**Not applicable — no new external packages are introduced by this phase.** Every fix operates on stdlib (`re`, `unittest`, `argparse`, etc.) and POSIX shell already present in the branch. `tiktoken` is a verification-only tool used by this researcher to independently measure token counts; it is not added to the shipped bundle, `requirements.txt`, or CI (`.worktrees/sota-numerics-release-013/.github/workflows/ci.yml`, `[VERIFIED]` read in full this session — contains only `python3 -m unittest` and three `bash tests/test-*.sh` invocations, no `pip install` step at all).

## Architecture Patterns

### System Architecture Diagram

```
Claude Code session start / subagent spawn (gsd-planner | gsd-executor | gsd-verifier)
        |
        v
  hooks/hooks.json  --SessionStart(startup|resume|clear|compact)-->  session-start.sh
        |                              --SubagentStart(role)------->  session-start.sh <role>
        v
  session-start.sh
    - resolves own PLUGIN_ROOT safely (${CLAUDE_PLUGIN_ROOT:-...})       [SAFE]
    - sources hooks/gsd-tools.sh -> defines gsd_tools() shell function   [D-13/D-14 DEFECT SITE #1]
    - calls gsd_tools capability status ...
        |
        v
  capability-auto-install.sh (also sources gsd-tools.sh)                [D-13/D-14 DEFECT SITE #2 via sourcing]
    - bundle_hash() over .gsd/capabilities/sota-numerics/**
    - compare vs ~/.gsd/capability-auto-install-sota-numerics.hash      [D-17 sidecar]
    - on mismatch: chain of git-provenance fail-closed checks
        (unverifiable_repo, ls-files tri-state, index-tag scan,
         status --porcelain --ignored, merge-base --is-ancestor)
    - on pass: gsd_tools capability install "$BUNDLE_DIR" --scope global --yes
        |
        v
  ~/.gsd/capabilities/sota-numerics/  (global mirror, now possibly UNCOMMITTED bundle content)
        |
        v
  gsd-planner writes a *-PLAN.md
        |
        v
  capability.json gates[] : plan:post -> command-exit-zero predicate
    SOTA_SCRIPT resolution: ./<rel> -> $(git rev-parse --show-toplevel)/<rel>  [DEFECT SITE #3,
                                                                                 independent of gsd-tools.sh]
                             -> ${GSD_HOME:-$HOME}/<rel>
    python3 "$SOTA_SCRIPT" <phase_dir>
        |
        v
  check-alternatives.py
    1. resolve_current_phase_dir(start)  <- reads .planning/STATE.md
         frontmatter parse (line 241, .search() - FIRST match)   [D-04 asymmetry]
         body parse (lines 255-261, exactly-one-match required)  [D-04 correct precedent]
    2. for each *-PLAN.md in phase dir matching PLAN_FILE_RE:
         mask_fenced_regions(text)   [fences masked; indented code blocks NOT masked - D-02 defect]
         find "## Alternatives Considered" section (SECTION_HEADING_RE, no leading-ws tolerance)
         extract_section_body -> BULLET_RE (unbounded indentation - D-03 defect) -> count >= MIN_ALTERNATIVES
         validate_entry() per bullet: citation regex, year-in-window check
           on failure: below_the_boundary() diagnostic (unbounded string join - D-07 defect, line 537)
    3. exit 0 (pass) | exit 1 (violation, diagnostic to stderr) | exit 2 (usage/IO error)
        |
        v
  exit code consumed by gsd-core's predicate evaluator -> block or allow plan:post
```

### Recommended Project Structure

No new files/directories are introduced. This phase edits in place:

```
.worktrees/sota-numerics-release-013/         # read-only checkout; all edits happen via normal git commits
├── hooks/
│   ├── gsd-tools.sh                          # D-13 fix: remove rung-1 unanchored git rev-parse
│   ├── session-start.sh                      # D-14 sweep target (transitively fixed via gsd-tools.sh)
│   └── capability-auto-install.sh            # D-14 sweep target (transitively fixed via gsd-tools.sh)
├── .gsd/capabilities/sota-numerics/
│   ├── capability.json                       # D-14 SCOPE QUESTION: gate command has its own
│   │                                          #   unanchored git rev-parse (site #3, see Open Questions)
│   └── scripts/check-alternatives.py         # D-02/D-03/D-04/D-07/D-08/D-09 fix target
├── tests/
│   └── test_check_alternatives.py            # D-06: add 3 fixture cases here
├── README.md                                 # D-10/D-11 fix target
├── CHANGELOG.md                              # D-09 fix target
└── .claude-plugin/plugin.json                # D-12 source-of-truth description

gsd-beads/  (this repo, NOT the worktree)
└── .claude-plugin/marketplace.json           # D-12 the ONE in-repo edit permitted
```

### Pattern 1: Fenced/indented-code masking before prose scanning

**What:** Before any section, bullet, or citation regex runs against a Markdown document, all constructs that CommonMark renders as non-prose (fenced code spans, and — the currently-missing case — 4+-space indented code blocks) must be blanked out (replaced with equal-length whitespace/newlines, preserving line numbers for diagnostics) so the prose-level regexes cannot match inside them.

**When to use:** Any gate/checker that parses semantic structure (headings, bullets, citations) out of Markdown using regex rather than a full parser.

**Example (existing, correct precedent already in the file for the fence case):**
```python
# Source: .worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:169
# [VERIFIED: opened and read this session]
FENCE_LINE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})([^\n]*)$", re.MULTILINE)
```
This correctly bounds fence-marker indentation to CommonMark's 0-3-space rule for a fence to still "count" as a fence (beyond 3 spaces of indentation, CommonMark itself treats the backticks as an indented code block, not a fence — the regex already respects this distinction). **Confirmed this session by direct reproduction:** a document whose entire `## Alternatives Considered` section was wrapped in a backtick fence produced exit 1 "missing section" (the fence-masking correctly hid the heading itself from `SECTION_HEADING_RE`, proving fences are already handled, not a live defect).

**The missing case (D-02's actual live gap):** a plain 4-space-indented line, with no backtick/tilde fence markers at all, is CommonMark's separate "indented code block" construct. `mask_fenced_regions` has no code path for it at all. **Reproduced this session:** a section with heading unindented, one normal bullet, and one bullet indented 4 spaces (hidden from rendered output, but NOT inside a fence) passed at exit 0 — the indented bullet was read as prose and counted toward `MIN_ALTERNATIVES`.

### Pattern 2: Two-witness state resolution, symmetric arity constraint

**What:** When a value (phase number) can be recorded in two independent locations (YAML frontmatter `current_phase:` key, and a `## Current Position` body `Phase: N` line) as a deliberate cross-check design (per the function's own docstring, `resolve_current_phase_dir`, lines 197-283, read verbatim this session), both extraction sites must apply the identical arity rule — not "first match wins" in one and "exactly one match or raise" in the other.

**When to use:** Any parser that reads the same logical value from two locations for redundancy/cross-check purposes.

**Example (the asymmetry, both sites, exact text):**
```python
# Source: .worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:235-261
# [VERIFIED: opened and read this session, exact lines]
fm = STATE_FRONTMATTER_RE.match(state_text)
...
m = STATE_CURRENT_PHASE_RE.search(fm.group(1))     # line 241 - FIRST match, no duplicate check
...
body_phases = STATE_BODY_PHASE_RE.findall(section.group(1))
if len(body_phases) != 1:                          # lines 255-261 - EXACTLY ONE, or raise
    raise ValueError(...)
```
D-04's fix is to make line 241 apply the same `findall` + `len(...) != 1` pattern the body parser already uses 14 lines below it — the correct pattern is already in the file, not something to invent.

### Anti-Patterns to Avoid

- **Unbounded string interpolation into a fail-closed diagnostic:** `below_the_boundary()` (lines 410-421) and `validate_entry()` (lines 520-544, specifically line 537's `found = ", ".join(str(y) for y in years)`) both interpolate an unbounded-length collection directly into a single stderr line with no truncation. Reproduced this session: 2000 out-of-window years in one citation produces a 12,281-byte, 8,098-token single line. Do not add more unbounded joins when fixing D-02/D-03/D-04 — every new diagnostic path must go through the same bounded, elided format D-08 mandates.
- **"Fix" `onError: halt` back to `onError: skip` on the gate:** `capability.json`'s gate entry carries an explicit, deliberate `description` field (`[VERIFIED]`, read in full this session) stating: *"A blocking gate that silently skips when its own manifest is malformed defeats its purpose. Do not 'fix' this back to 'skip'."* This is asserted in-file as a guardrail against a plausible-looking but wrong future edit; the planner must not touch this field.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CommonMark fence/indented-code masking | A new, separate parsing pass or a bespoke tokenizer | Extend the existing `mask_fenced_regions`/`FENCE_LINE_RE` line-scan (already stdlib regex, already handles the fence case correctly) | Precedent already correct for one of the two constructs; the fix is additive to the same function, not a rewrite |
| Cwd-independent script-location resolution | A new resolution scheme invented for this phase | The pattern the sibling `beads-lifecycle` plugin already ships: `[VERIFIED: /home/dd/projects/gsd-beads/plugins/beads-lifecycle/hooks/capability-auto-install.sh:70-71,109]` — `CLAUDE_CONFIG_ROOT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"` then `GSD_TOOLS="$RUNTIME_CONFIG_DIR/gsd-core/bin/gsd-tools.cjs"`, with no `git rev-parse` call at all in the resolution chain | A second, independently-invented fix risks a second, independently-wrong defect; the sibling plugin in the same repo already solved this exact problem without touching `git` |
| PR review-thread reconciliation | A hand-rolled diff of comment text against report text | `gh api graphql` querying `reviewThreads { isResolved isOutdated comments { body } }` | GitHub's own resolution/outdated-ness bookkeeping is authoritative; text-matching risks false negatives on reworded threads |

**Key insight:** every locked decision in this phase names a *repair*, and in every case this session found the correct pattern already exists somewhere nearby in the same file or the sibling plugin — the fixes are narrow, surgical, and should stay that way (consistent with the project's Scope & Simplicity First directive).

## Runtime State Inventory

This is not a rename/refactor/migration phase in the traditional filesystem-string sense, so the standard 5-category table (stored data / live service config / OS-registered state / secrets / build artifacts) does not directly apply. However, D-17 names a directly analogous runtime-state hazard specific to this phase's execution mechanics, verified this session:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Global capability mirror | `~/.gsd/capabilities/sota-numerics/` — a full copy of the bundle, installed by `capability-auto-install.sh` whenever the worktree's bundle hash changes from the last-recorded sidecar value. Any edit made to the worktree during this phase's execution (by the executor agent) will trigger this on the *next* `SessionStart`/`SubagentStart`, installing the mid-edit, uncommitted bundle machine-wide. | Per D-17: record `~/.gsd/capability-auto-install-sota-numerics.hash` before and after each plan; restore the mirror from the released plugin-cache bundle when the phase ends. This is a **mandatory bookkeeping task**, not optional cleanup — every wave's plan should include a checkpoint or task step recording this hash. |
| Sidecar hash file | `${GSD_HOME:-$HOME}/.gsd/capability-auto-install-sota-numerics.hash` — `[VERIFIED: .worktrees/sota-numerics-release-013/hooks/capability-auto-install.sh:69]`, `STATE_FILE="${GSD_HOME:-$HOME}/.gsd/capability-auto-install-$CAP_ID.hash"` | Code-edit-only (no data migration) — this is a machine-local cache path, not touched by the branch's own commits. |
| bd issues | `gsd-beads-sac.14`, `.15`, `.16` already exist and carry the prior `hold` decision as a comment on `.14` (per `STATE.md` `### Blockers/Concerns`, `[VERIFIED]` read this session). | Reuse, do not recreate (D-23). Carry the exact IDs into the publish plan's task elements. |
| PR #4 | Open, on `davdittrich/sota-numerics`, currently behind HEAD of `feat/extended-sota-definition` per REVIEW findings (P1-5). | No action until the remediation waves land; then push, and only then does external review re-run (D-16/D-20). |

**Nothing found in category "OS-registered state" or "secrets/env vars":** this phase touches no task schedulers, process managers, or credential stores — verified by the full read of every hook script and `capability.json`; none reference any such system.

## Common Pitfalls

### Pitfall 1: Assuming fence-masking already covers "code blocks" generically

**What goes wrong:** Reading D-02's CONTEXT wording ("a section nested inside an indented fenced code block") literally as one construct can lead an implementer to only touch fence handling (already correct) and miss the actually-broken construct (plain 4-space indented code blocks, no fence markers).
**Why it happens:** CommonMark has two visually similar but structurally distinct code-hiding constructs — fenced code blocks (```` ``` ````/`~~~`, at 0-3 spaces indentation) and indented code blocks (4+ spaces, no fence). D-02's prose conflates them into one phrase.
**How to avoid:** Treat this as two separate sub-fixes: (1) confirm fence masking already works (it does — reproduced this session, exit 1 on a fence-wrapped section, no code change needed there) and (2) add masking for 4+-space indented lines, which is the actual live gap.
**Warning signs:** A fix that only extends `FENCE_LINE_RE`'s indentation bound (e.g. changing `{0,3}` to something larger) does not address D-02 — it would incorrectly start treating deeply-indented *fences* differently, while leaving indented-code-block-without-fence-markers still unmasked. Verify against the exact fixture: a 4-space-indented bullet, no backtick/tilde anywhere in the section, still passing at exit 0 after the fix means D-02 is not actually resolved.

### Pitfall 2: Fixing D-03's bullet bound without re-checking D-02's interaction

**What goes wrong:** `BULLET_RE`'s unbounded indentation (line 115) is exploited by *both* the indented-code-block bypass (D-02, since 4-space content isn't masked, `BULLET_RE` reads it) and the nested-sub-bullet bypass (D-03, a 4-space sub-bullet under a real top-level bullet). Fixing `BULLET_RE`'s bound to `{0,3}` alone (D-03's literal instruction) closes the nested-sub-bullet path AND incidentally closes the indented-code-block path too — because after the bound, a 4-space-indented "bullet" no longer matches `BULLET_RE` at all, whether or not it's inside a masked region.
**Why it happens:** D-02 and D-03 read as independent decisions, but their fixes overlap in effect. This is favorable (fixing D-03 alone might already resolve the visible symptom of D-02 for bullets), but D-02 also affects headings and citations inside indented blocks, which `BULLET_RE`'s bound does not touch.
**How to avoid:** Implement both fixes, but write the regression fixtures (D-06) to isolate each: one fixture with ONLY the bullet-indentation bound removed (to catch a partial fix), one with ONLY the masking gap open. Do not assume D-03's fix alone satisfies D-02's fixture.
**Warning signs:** If a single fixture is used to "prove" both D-02 and D-03 fixed, a partial fix (only `BULLET_RE` bounded, masking still missing) could pass that one fixture while a heading or citation embedded in an indented block still leaks through.

### Pitfall 3: Treating D-14's "every hook in the bundle" as scoped only to `hooks/`

**What goes wrong:** This session found the identical unanchored `git rev-parse --show-toplevel` pattern in a THIRD location that is not a "hook" file at all: `capability.json`'s `gates[].check.predicate.command` string (line containing `SOTA_SCRIPT="$(git rev-parse --show-toplevel 2>/dev/null)/$_SN"`). If the planner scopes D-14's sweep literally to files under `hooks/`, this site is missed even though it shares the exact same defect shape and is not fixed by editing `gsd-tools.sh` (this command is inline shell embedded in JSON, not a sourced script).
**Why it happens:** D-13/D-14's prose names two specific files (`gsd-tools.sh`, `session-start.sh`); `capability.json`'s gate command is a different kind of artifact (a JSON-embedded shell one-liner) that a file-glob-based "hooks" sweep would not surface.
**How to avoid:** Flag this to the planner explicitly (see Open Questions below) — this is a discretion/scope call, not a research gap: the *defect* is confirmed present, the *scope question* is whether Phase 24 fixes it now or tickets it.
**Warning signs:** `grep -rn "rev-parse --show-toplevel" .worktrees/sota-numerics-release-013/` (verified this session) returns exactly 2 code sites (`hooks/gsd-tools.sh:5` and `capability.json`'s embedded command) plus 1 doc mention (`NOTES.md:32`, which describes the capability.json behavior, not a separate defect) — if a "fixed" state still shows the `capability.json` occurrence, the fix is incomplete relative to what this pattern implies, even if D-14's literal text is satisfied.

### Pitfall 4: Deleting a count in D-09 without checking whether a mechanism could keep it true cheaply

**What goes wrong:** D-09 says "prefer deleting a count that no mechanism keeps true over correcting it to a value that will be stale again; keep a number only where something recomputes or checks it" — but `CHANGELOG.md`'s 94/62/35 (verified against HEAD this session: `[VERIFIED]` — running the actual current test suite would give the true current count; the phase should re-derive this at execution time, not trust either the CONTEXT's stated 97 or the CHANGELOG's stale 94) is exactly the kind of number a one-line CI/test-count check *could* keep true cheaply (e.g., a fixture-driven assertion of total test count). Deleting it outright when a 1-line mechanism could preserve it discards useful release-note content unnecessarily.
**Why it happens:** "Delete rather than correct" is the safe default when no mechanism is planned, but D-09 leaves "which counts are deleted and which are kept with a mechanism" to Claude's Discretion — a planner defaulting to blanket deletion undershoots the decision space CONTEXT explicitly left open.
**How to avoid:** For each stale count (CHANGELOG's 94/62/35, `check-alternatives.py` line 47's "76 entries"), evaluate per-count whether a lightweight mechanism (e.g., a test asserting the changelog number matches `len(test_cases)`, or simply removing the specific hardcoded number and replacing with "run `python3 -m unittest -v` for current counts") is cheaper than deletion, and document the choice.

## Code Examples

### D-04 fix pattern (frontmatter parse symmetry) — before/after, discretion-bounded

```python
# BEFORE (Source: .worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:241)
# [VERIFIED: opened and read this session]
m = STATE_CURRENT_PHASE_RE.search(fm.group(1))
if not m:
    raise ValueError(f"{state_path}: no 'current_phase' key in frontmatter")
frontmatter_phase = m.group(1)
```

```python
# AFTER (illustrative — exact regex construction is Claude's Discretion per CONTEXT,
# provided D-05's evidence holds; shape matches the existing body-parser precedent
# at lines 255-261, which is the correct pattern already in the file)
frontmatter_matches = STATE_CURRENT_PHASE_RE.findall(fm.group(1))
if len(frontmatter_matches) != 1:
    raise ValueError(
        f"{state_path}: expected exactly one 'current_phase' key in frontmatter, "
        f"found {len(frontmatter_matches)}"
    )
frontmatter_phase = frontmatter_matches[0]
```

### D-08 diagnostic bounding precedent (Phase 23 D-13's existing format, to be applied to `below_the_boundary`/`validate_entry`)

```
# Bounded shape per D-08, matching the capability's already-documented precedent:
<plan_path>:<line>: <reason>
```
one line per violation, with any quoted span (e.g. the joined `years` list at line 537) truncated with an explicit elision marker, followed by exactly one `remediation: ...` line for the whole run — not one per violation.

### Reproduction fixture shapes (used this session, illustrative for D-06's fixtures — not copy-paste, since exact fixture content/placement in `tests/test_check_alternatives.py` is an execution-time decision)

```markdown
<!-- Indented-code-block bypass fixture shape (D-02) -->
## Alternatives Considered

- **RealAlternativeOne**: see `docs/a.md` (2024) for details.

    - **HiddenViaIndentedCodeBlock**: see `docs/b.md` (2024) for details.

Decided by: performance
```
Reproduced this session: exit 0 (bypass confirmed — the indented bullet is invisible in rendered Markdown but still counted).

```markdown
<!-- Nested-sub-bullet bypass fixture shape (D-03) -->
## Alternatives Considered

- **RealAlternativeOne**: see `docs/a.md` (2024) for details.
    - **NestedSubConsideration**: see `docs/c.md` (2024) for details.

Decided by: performance
```
Reproduced this session: exit 0 (bypass confirmed — the nested sub-bullet counts as a second top-level alternative).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Unbounded `BULLET_RE` leading-whitespace group | Bounded to `{0,3}` per CommonMark top-level range | This phase (D-03) | Nested/indented bullets no longer satisfy top-level alternative count |
| `mask_fenced_regions` handling fences only | Extended to also mask 4+-space indented code blocks | This phase (D-02) | Indented-code-hidden content no longer read as prose |
| First-match frontmatter phase parse | Exactly-one-match, named-failure-on-duplicate | This phase (D-04) | Matches existing body-parser rigor; a malformed/duplicated STATE.md now fails loudly instead of silently picking the first value |
| Unbounded diagnostic join | Bounded, elided, one-line-per-violation format (D-08) | This phase | Gate failures no longer flood the context window (8,098 tokens -> bounded) |

**Deprecated/outdated:**
- `hooks/gsd-tools.sh`'s cwd-rooted `git rev-parse --show-toplevel` resolver rung: superseded by the sibling `beads-lifecycle` plugin's fixed-root resolver pattern (`CLAUDE_CONFIG_DIR`/`CODEX_HOME`-anchored, no `git` call). This phase should adopt the same pattern, not invent a new one.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | D-05's "both repositories" regression sweep, in practice, only has one repository with a real planning-document corpus (`gsd-beads`, 96 `.md` files under `.planning/phases/`, 9 plan-shaped per this session's `[VERIFIED]` count via `find`); the `sota-numerics` repo's only `.planning`-named path is `tests/.planning` — test fixtures already covered by the Python suite, not a second real corpus. `[VERIFIED: find .worktrees/sota-numerics-release-013 -maxdepth 2 -iname .planning` returned only `tests/.planning]` for the absence of a second corpus; the interpretation that this satisfies D-05's "both repositories" instruction is `[ASSUMED]`. | Runtime State Inventory / Open Questions | If the planner or user intends "both repositories" to mean something else (e.g., a currently-unlisted third location, or every consuming project that has the capability installed), the regression evidence gathered would be incomplete for D-05's actual intent. Low risk of silent failure since D-05 gates the fail-open fixes with an explicit "any other changed verdict is a finding, not a pass" rule — an incomplete sweep would likely surface as a missing verdict count rather than a silent pass, but should be confirmed before execution. |
| A2 | The `capability.json` gate-command's own unanchored `git rev-parse --show-toplevel` (site #3, distinct from `hooks/gsd-tools.sh`) is in scope for D-14's "check every hook in the bundle" instruction, despite not being a file under `hooks/`. | Common Pitfalls / Pitfall 3, Open Questions | If out of scope, this defect ships unfixed in 0.2.0 despite being the identical vulnerability class D-13/D-14 target; if the planner assumes it's covered by fixing `gsd-tools.sh` alone, it is not — this is an independent code path (inline JSON-embedded shell, not a sourced script). |
| A3 | D-09's exact replacement content for the deleted/corrected counts (CHANGELOG 94/62/35, `check-alternatives.py`'s "76 entries") is Claude's Discretion; this research does not prescribe exact replacement text, only the decision framework (delete vs. mechanism-backed). | Common Pitfalls / Pitfall 4 | Low risk — CONTEXT explicitly delegates this to discretion; documented here only to prevent the planner from treating "76" -> "73" (a corrected-but-still-stale number) as compliant with D-09, when D-09 explicitly prefers deletion over correction-to-a-still-stale-value. |

**All other claims in this research were verified by direct source read, direct command execution, or independent reproduction this session** (see Sources).

## Open Questions

1. **Does D-14's "every hook in the bundle" scope include `capability.json`'s gate-command inline shell (site #3)?**
   - What we know: the identical unanchored `git rev-parse --show-toplevel` pattern exists at `.gsd/capabilities/sota-numerics/capability.json`'s `gates[0].check.predicate.command`, confirmed via direct `python3 -c "json.load(...)"` extraction this session. It is a real code-execution-adjacent site (a hostile repo placing a file at the exact relative path `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` would get it executed via `python3` when this gate resolves rung 2).
   - What's unclear: D-14's literal wording names "hooks" and the two files the review named; `capability.json` is a manifest, not a hook script, though its `gates[].check.predicate.command` executes with hook-like privilege at plan:post time.
   - Recommendation: surface this to the user/planner as an explicit scope decision before execution — either fold it into D-13/D-14's fix wave (recommended, since it is the same vulnerability class and the fix is equally small: anchor the resolution to the script's own known-good rungs 1 and 3, dropping rung 2's `git rev-parse` the same way `gsd-tools.sh`'s fix does) or file it as a tracked follow-up ticket per the project's "never defer without explicit approval, file a tracking ticket immediately" global rule.

2. **D-05's "both repositories" regression sweep — see Assumption A1.**
   - What we know: `gsd-beads` has a real 96-file planning corpus; `sota-numerics` has none outside test fixtures.
   - What's unclear: whether D-05's phrase anticipates a corpus that does not yet exist, or is satisfied by "the second repository has zero real documents, so the before/after sweep there is vacuously unchanged."
   - Recommendation: state this interpretation explicitly in the plan's D-05 task description so the verifier phase can confirm the same interpretation was used, rather than silently picking one.

3. **The remaining ~7-8 CodeRabbit review threads on PR #4 (beyond the specifically-named duplicate-`current_phase` thread in D-15)** — covering `capability.json` apostrophe handling, `executor-numerics.md` failure-output format, `README.md` publication-guarantee wording, shell-suite D0-parsing robustness, `planner-sota.md` enforcement-clause scope, a `check-alternatives.py:61` trailing-`\r` allowance question, and `CHANGELOG.md` support-table completeness.
   - What we know: these threads exist (confirmed via `gh api graphql` this session) and are either open or resolved-but-outdated (meaning the underlying diff line has since moved).
   - What's unclear: whether any represent a *blocking* finding not already covered by the four review reports' P-numbered findings, versus a duplicate/subset of an already-tracked D-01…D-24 item.
   - Recommendation: this cross-reference is incomplete in this research pass. The planner should treat D-16's "PR #4 stays open and is treated as a known-incomplete diff until this phase verifies" as covering these — i.e., they get re-evaluated naturally once the branch is pushed with the D-01…D-14 fixes and CI/CodeRabbit re-runs (per D-16/D-20's ordering), rather than requiring a separate triage task now. Flag as a residual-risk item for the publish-wave checkpoint (D-22) rather than blocking earlier waves.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `git` | worktree reads, provenance-guard fixes, `merge-base`/`rev-parse` logic | ✓ | (system) | — |
| `python3` | gate script, `unittest` suite | ✓ | (system, used successfully this session) | — |
| `bash` | 3 shell test suites, all hooks | ✓ | (system) | — |
| `gh` CLI | PR #4 review-thread reconciliation (D-15) | ✓ | (system, used successfully this session) | — |
| `tiktoken` (Python package) | Verification-only: independently measuring diagnostic token counts | ✓ (present in this session's environment) | — | Not required for the phase's actual fixes; only for confirming D-07's bound is adequate. If absent at execution time, character-count-based bounding checks (already what the code should truncate on) suffice as a fallback measurement. |

**Missing dependencies with no fallback:** none identified.
**Missing dependencies with fallback:** `tiktoken` (verification convenience only, not a shipped dependency).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python 3 stdlib `unittest` (`tests/test_check_alternatives.py`, 1515 lines) + 3 independent POSIX shell test suites |
| Config file | None — no `pytest.ini`/`setup.cfg`; suites are invoked directly, exactly as `[VERIFIED: .worktrees/sota-numerics-release-013/.github/workflows/ci.yml]` shows |
| Quick run command | `python3 -m unittest tests.test_check_alternatives.TestNameHere` (single-fixture reruns during D-06 authoring) |
| Full suite command | `python3 -m unittest tests/test_check_alternatives.py && bash tests/test-session-start.sh && bash tests/test-capability-auto-install.sh && bash tests/test-gate-script-resolution.sh` (exact 4 invocations, `[VERIFIED: ci.yml:17,23,26,29]`) |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-02 | Indented-code-block masking closes bypass | unit (new fixture) | `python3 -m unittest tests.test_check_alternatives` (new test method) | ✅ file exists, ❌ new test method needed |
| D-03 | Bullet-indentation bound closes nested-sub-bullet bypass | unit (new fixture) | same file, new test method | ❌ Wave (D-06) |
| D-04 | Frontmatter exactly-one-match | unit (new fixture) | same file, new test method | ❌ Wave (D-06) |
| D-07/D-08 | Diagnostic bounded to N chars/lines, elision marker present | unit (extend existing diagnostic-format tests, or new) | same file | ❌ Wave (D-06/D-08 combined task likely) |
| D-13/D-14 | `gsd-tools.sh` resolves entry point without invoking `git rev-parse` on caller cwd | shell unit | `bash tests/test-gate-script-resolution.sh` (existing suite — extend with a hostile-cwd fixture case) | ✅ file exists, ❌ new case needed |
| D-05 | Regression sweep, before/after verdict diff across `gsd-beads` corpus | integration (not unit) | run `check-alternatives.py` over every `.planning/phases/*/` directory in `gsd-beads` before and after the branch change; diff exit codes | ❌ no existing automated harness for this cross-corpus sweep — likely a one-off script task, not a permanent test |

### Sampling Rate
- **Per task commit:** `python3 -m unittest tests.test_check_alternatives.<NewTestCase>` (fast, targeted)
- **Per wave merge:** full 4-command suite above (`[VERIFIED: ci.yml]`)
- **Phase gate:** full suite green on the exact commit that reaches `main` (D-20), before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] New `unittest` test methods in `tests/test_check_alternatives.py` for the 3 fail-open fixtures (D-06) — file exists, methods do not yet.
- [ ] New case in `tests/test-gate-script-resolution.sh` proving `gsd-tools.sh` no longer executes a hostile-cwd-planted `gsd-core/bin/gsd-tools.cjs`.
- [ ] A regression-sweep script (one-off, not necessarily a permanent test) implementing D-05's before/after diff over `gsd-beads`'s `.planning/phases/` corpus — no existing harness for this; framework install not needed (uses the same `check-alternatives.py` already present).

## Security Domain

### Applicable ASVS Categories

Per `.planning/config.json`: `security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: "high"` (`[VERIFIED: .planning/config.json]`, read this session).

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Architecture | yes | Fail-closed design already present throughout (`onError: halt` on the gate predicate, `test -f ... || exit 1` chains in all 3 resolver sites) — preserve this shape in every fix, do not weaken any fail-closed branch to fail-open |
| V5 Input Validation | yes | `capability-auto-install.sh`'s existing `[[ "$CAP_ID" =~ ^[a-z][a-z0-9-]*$ ]]` pattern (already in the file, noted as a defense-in-depth precedent) is the model for any new validation this phase adds — no new validation is actually required by the locked decisions, but this is the standing pattern to match if any is touched |
| V7 Error Handling and Logging | yes | D-07/D-08 (bounded diagnostics) is directly an ASVS V7 concern: unbounded error output is both a DoS-adjacent resource-consumption issue (context-window flooding) and an information-disclosure-adjacent issue (dumping the entire malformed input back to the log) |
| V10 Malicious Code / Self-Protection | yes | D-13/D-14 (and the site-#3 open question) is the core V10-relevant finding: an unanchored `git rev-parse --show-toplevel` used to locate a script that then gets executed unconditionally is a textbook "resolve trust from the wrong scope" defect — the caller's cwd (attacker-controlled if the user is tricked into running a session inside a hostile checkout) rather than the plugin's own known-good install location |
| V6 Cryptography | no | No cryptographic operations anywhere in this phase's scope |
| V2/V3/V4 Auth/Session/AccessControl | no | No authentication/session/access-control surface in a CLI gate script |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Cwd-rooted `git rev-parse --show-toplevel` used to locate an executable path, then execute it unconditionally | Elevation of Privilege (a hostile repo the user happens to `cd` into before a Claude Code session gets its code run via `node`/`python3`) | Resolve the path relative to the invoking script's own known location (`${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}`, already the correct pattern used elsewhere in the SAME files for `PLUGIN_ROOT`) or a fixed config-root env var (`CLAUDE_CONFIG_DIR`/`GSD_HOME`), never the caller's `git rev-parse` output. `[VERIFIED]` — the sibling `beads-lifecycle` plugin already implements the correct pattern in the same repo. |
| Unbounded diagnostic output on a fail-closed gate | Denial of Service (context-window/log flooding), minor Information Disclosure (full malformed input echoed) | Bound every diagnostic line length and total line count; truncate with an explicit elision marker (D-08) |
| Bundle-hash provenance mismatch on a plugin auto-install path | Tampering (installing uncommitted/attacker-modified content machine-wide) | `capability-auto-install.sh`'s existing 9-refusal-path git-provenance chain (`unverifiable_repo`, `ls-files --error-unmatch` tri-state, index-tag scan, `status --porcelain --ignored`, `merge-base --is-ancestor` against `origin/main`) is already a strong, fail-closed mitigation — this phase's D-17 only adds observability (hash-sidecar recording before/after), not a new mitigation; do not weaken the existing guard chain while doing so |

## Sources

### Primary (HIGH confidence — opened and read this session, or independently reproduced)

- `.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (675 lines, full read + multiple targeted re-reads for exact line numbers) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/hooks/gsd-tools.sh` (18 lines, full read) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/hooks/session-start.sh` (41 lines, full read) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/hooks/capability-auto-install.sh` (244 lines, full read) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/hooks/hooks.json` (32 lines, full read) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/README.md` (targeted full-section reads) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/CHANGELOG.md` (targeted full-section reads) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/.claude-plugin/plugin.json` (full read via `Read` tool) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/capability.json` (full read via `python3 -c "json.load(...)"`, this session and prior) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/.github/workflows/ci.yml` (full read, re-verified this session) `[VERIFIED]`
- `.worktrees/sota-numerics-release-013/tests/test_check_alternatives.py` (lines 1-50 read; full-file line count `wc -l` re-verified this session at 1515) `[VERIFIED]`
- `/home/dd/projects/gsd-beads/.claude-plugin/marketplace.json` (grepped `sota-numerics` entry) `[VERIFIED]`
- `/home/dd/projects/gsd-beads/plugins/beads-lifecycle/hooks/capability-auto-install.sh` (grepped for resolver pattern lines 70-71, 109) `[VERIFIED]`
- `/home/dd/projects/gsd-beads/.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-CONTEXT.md` (full read) `[VERIFIED]`
- `/home/dd/projects/gsd-beads/.planning/phases/23-extend-sota-definition-in-sota-numerics-and-refactor-plugin/23-CONTEXT.md` (full read, prior session) `[VERIFIED]`
- `/home/dd/projects/gsd-beads/.planning/STATE.md` (full read) `[VERIFIED]`
- `/home/dd/projects/gsd-beads/.planning/config.json` (`workflow.nyquist_validation`, `security_enforcement`, `security_asvs_level`, `security_block_on` fields read this session) `[VERIFIED]`
- Independent reproductions this session (scratchpad-only fixtures, never written into the worktree, all cleaned up with `rm -rf` immediately after each probe):
  - Unbounded-diagnostic reproduction: 2000 out-of-window-year citation -> exit 1, 12,281-byte / 8,098-token single stderr line (measured via `tiktoken.get_encoding('cl100k_base')`)
  - Indented-code-block bypass: unindented heading + 1 normal bullet + 1 four-space-indented bullet -> exit 0 (bypass confirmed)
  - Nested-sub-bullet bypass: 1 top-level bullet + 1 nested four-space-indented sub-bullet -> exit 0 (bypass confirmed)
  - Backtick-fence masking control: entire section wrapped in a ``` fence -> exit 1 "missing section" (proves fence masking already correct, not a live defect)
- `gh api graphql` queries against `davdittrich/sota-numerics` PR #4 review threads (this session and prior) `[VERIFIED]`
- REVIEW-CRITICAL-FINAL.md, REVIEW-PONYTAIL-FINAL.md, REVIEW-AGY-FINAL.md, REVIEW-PROSE-TOKENS.md (all read in full, this session's prior turns) `[VERIFIED]` as review-report content; every specific claim drawn from them was independently cross-checked against source rather than taken on the reports' authority alone

### Secondary (MEDIUM confidence)

- None — every claim in this research either traces to a directly-opened source file/command output this session, or is explicitly flagged `[ASSUMED]` in the Assumptions Log.

### Tertiary (LOW confidence)

- The ~7-8 untriaged CodeRabbit threads beyond the D-15-named one (Open Questions item 3) — their existence and open/resolved-outdated status is `[VERIFIED]` via `gh api graphql`, but their disposition relative to the four review reports' P-numbered findings is not yet cross-referenced; treated as an explicit residual-risk open question, not a silently-dropped finding.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; every existing dependency confirmed via direct file read this session.
- Architecture: HIGH — every pattern and defect described was traced to exact file:line and, for the 4 core gate defects, independently reproduced with real fixtures and exit codes.
- Pitfalls: HIGH — all 4 pitfalls derive from direct source reading and reproduction, not inference from the review reports alone.
- Security: HIGH for the confirmed defects (D-13/D-14, site #3); the site-#3 scope question is explicitly flagged LOW/open rather than resolved unilaterally.

**Research date:** 2026-09-07
**Valid until:** This research is tied to a specific commit state of a `feat/extended-sota-definition` branch and a specific PR #4 review-thread state, both of which change as soon as this phase's remediation waves land and push. Treat as valid only until the first commit of this phase's execution — re-verify line numbers and thread states after any push to the branch.
