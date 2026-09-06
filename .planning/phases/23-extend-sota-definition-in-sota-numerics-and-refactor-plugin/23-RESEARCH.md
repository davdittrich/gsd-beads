# Phase 23: Extend SOTA definition in sota-numerics and refactor plugin - Research

**Researched:** 2026-09-06
**Domain:** GSD capability manifest / advisory-prompt-fragment design (Markdown + JSON, no application code)
**Confidence:** HIGH (in-repo mechanics, verified this session) / MEDIUM (external citations for the mechanism choices)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Enforcement level**
- D-01: The `plan:post` gate stays exactly as it is. `check-alternatives.py` gains no new checks, and `capability.json` gains no new gate.
- D-02: All six added dimensions ship as advisory fragment text at the existing contribution points.
- D-03: Rationale, and the reason a future contributor must not "finish the job" by adding checks: the existing gate works because its predicate has a valid measurement instrument — a section heading, two named entries, a citation, a four-digit year inside a window, a `Decided by:` line. "Consistent", "unambiguous", "complete", and "efficient" have no such instrument. A regex that scores their vocabulary measures word presence, not the property, so it would pass plans that recite the words and block plans that demonstrate the property without them. The gate is `blocking: true` with `onError: halt`, so a false positive there halts planning outright. An unmeasurable blocking check is compliance theater with a halt attached.
- D-04: Compliance evidence for the added dimensions comes from the verifier and ship fragments as findings, which is where the capability already puts every judgment it cannot mechanize.

**Fragment architecture**
- D-05: Extend the four existing fragments in place. No new fragment files, no new contribution points, no change to the shape of `capability.json`'s `contributions` array.
- D-06: Rejected alternative — one shared "extended SOTA definition" fragment injected at all four points. Every point that renders it pays its full token cost, so a shared fragment multiplies context load by four while the four roles need different slices.
- D-07: Role slicing. `planner-sota.md` takes project consistency and plan completeness. `executor-numerics.md` takes agent-facing prose, quiet runtime output, and efficiency. `verifier-precision.md` takes the matching findings. `ship-precision-advisory.md` takes the claim-backing confirmation it already carries, extended to the new claims.
- D-08: Line budget. The four fragments total 27 lines today (planner 13, executor 5, verifier 5, ship 4). The extended set must total 45 lines or fewer. Part of the room comes from pruning `planner-sota.md`, which currently restates the gate's mechanics at length and duplicates what `check-alternatives.py` already enforces.
- D-09: Leading words carry the added dimensions so they cost tokens once instead of once per restatement: **with the grain** for project consistency, **quiet** for low token cost at runtime, **legible** for prose that is unambiguous and complete. Define each once, then repeat only the word.
- D-10: State every added instruction as the target behavior rather than as a prohibition. A ban names the behavior it forbids and makes it more available, not less.

**What "token-efficient during execution" means**
- D-11: It means the generated code is cheap for an agent to run. On success it prints a compact, machine-readable result or nothing at all. On failure it prints one line naming the problem and one line naming the fix. It signals through exit codes rather than prose. It emits no progress chatter. Output large enough to flood a context window goes to a file and the code prints the path.
- D-12: This applies to code an agent invokes directly — scripts, CLIs, test harnesses, hooks — and not to library internals an agent never runs by hand.
- D-13: Two in-repo precedents anchor the wording, and both are already familiar to this project's agents: `check-alternatives.py` prints `<plan_path>: <reason>` per violation followed by exactly one `remediation: ...` line, and `gsd-tools` swaps stdout over roughly 50KB for an `@file:<tmp>` pointer.

**writing-for-agents portability**
- D-14: Inline the operative rules into the executor fragment. Do not reference the skill by name.
- D-15: Rationale: the skill lives at `~/.local/share/agent-skills/writing-for-agents`, a user-local directory. It is not part of this plugin, not part of gsd-core, and not present for anyone else who installs `sota-numerics`. The capability declares support for every GSD runtime, so a pointer to that path would be dead for every consumer but its author. A pointer whose target is missing is worse than no pointer.
- D-16: The rules that survive compression to code-facing use: keep each meaning in one place, so a comment says why and the code says what; delete any line the agent would already honor by default; phrase instructions as the target behavior; give every completion criterion a bound the agent can check; keep a definition next to its caveats; name the ceiling of any simplification.

**Self-compliance scope for the refactor**
- D-17: Must comply: the four fragments, `README.md`, the `description` fields in `.claude-plugin/plugin.json` and `capability.json` including the gate's `description` string, and `check-alternatives.py`'s module docstring and comments.
- D-18: `NOTES.md` gets pruning only. Its anti-regression entries are the single source of truth for the capability's deliberate divergences and stay intact; remove only what `README.md` already says.
- D-19: `hooks/*.sh` and `tests/` get no prose refactor. Touch a message there only when it is agent-facing and breaks the quiet or legible rule.
- D-20: Evidence of compliance: the existing Python and shell suites pass unchanged, `wc -l` on the four fragments confirms the D-08 budget, and every behavioral claim in `README.md` traces to a line of code or config.
- D-21: Add no test infrastructure for prose. The existing suites are the regression guard that the refactor left gate behavior alone.

**Target repository and release**
- D-22: Work in the existing clone at `.worktrees/sota-numerics-release-013`, on a new branch cut from `origin/main`. Verified 2026-09-06: that clone's checkout and `origin/main` are both at `eccad87`, so it is current.
- D-23: Version becomes `0.2.0` in both `.claude-plugin/plugin.json` and `.gsd/capabilities/sota-numerics/capability.json`, kept in sync. Minor bump: the instruction surface grows and prompt behavior changes, while the gate contract does not.
- D-24: The phase ends at published `0.2.0`. Answered by the user on 2026-09-06.
- D-25: Because the marketplace entry points at the repository URL rather than at a tag, merging to `main` is the publish. There is no separate release step, so everything that must be true of a release must be true before the merge.
- D-26: Publish ordering. Internal review and every fix it accepts land on the branch before the pull request opens, so an external reviewer's first pass sees a finished diff rather than a known-incomplete one. CI must be green on the exact commit that reaches `main`. Any claim the release makes about behavior must trace to code, not to an assertion in the pull request body.
- D-27: Tag the published commit `v0.2.0`. `0.1.3` left no immutable marker for what was served; this phase does not repeat that.

### Claude's Discretion
- Exact wording of each fragment line, within the D-08 budget and the D-09 leading words.
- Which specific lines of `planner-sota.md` get pruned to make room.
- Commit granularity within the branch.

### Deferred Ideas (OUT OF SCOPE)
- `.worktrees/sota-numerics-issue-1` and `.worktrees/sota-numerics-release-013` are clones of the `sota-numerics` repository sitting untracked inside the `gsd-beads` working tree. `git status` lists `.worktrees/` as untracked, so a `git add -A` in `gsd-beads` would commit another project's history into this one. Fix is either a `.gitignore` entry or relocation. Tracked as `gsd-beads-9tg`.
- `0.1.3` was published without a git tag, so the repository has no immutable marker for that version and the marketplace serves whatever `main` holds. D-27 tags this release; the convention for past and future releases is still unwritten. Tracked as `gsd-beads-oh1`.
</user_constraints>

## Project Constraints (from CLAUDE.md)

`/home/dd/projects/gsd-beads/CLAUDE.md` is a placeholder ("Add your build and test commands here" / "Add a brief overview of your project architecture") with no actionable directives — verified by reading it this session. No project-specific constraint from this file bears on the plan beyond the global user-level `~/.claude/CLAUDE.md` directives already governing this session (bd-ticket-per-task, Alternatives Considered on every plan, GSD lifecycle for multi-file work), which this phase's own `plan:post` gate independently and mechanically enforces for the Alternatives requirement. `/home/dd/projects/gsd-beads/.claude/rules/openwolf.md` governs local code-exploration tooling (`openwolf find`) and is orthogonal to this phase's content — it applies to the target repo's own future edits performed via Serena/OpenWolf during execution, not to the research or planning artifacts.

## Summary

This phase edits Markdown prompt fragments and two `description` strings inside an already-shipped GSD capability (`sota-numerics`, cloned at `.worktrees/sota-numerics-release-013`, `origin/main` = `eccad87`, v0.1.3). There is no new library, framework, or runtime to select — every "mechanism choice" this phase makes is an information-architecture decision (where a rule lives, how long it may run, whether it gates or advises), so the plan's `## Alternatives Considered` section needs citations from the context-engineering / CLI-design / measurement-validity literature, not a package registry.

The two things a planner most needs from this research: (1) the exact, verified mechanics of how `contributions[].fragment.path` becomes prompt text in the four target roles — confirmed by reading `capability-validator.cjs` and `loop-hook-dispatch.md` this session — and (2) real, current, dated sources backing each of the four locked mechanism choices in CONTEXT.md (D-01–D-04, D-05–D-06, D-11–D-13, D-14–D-15), which is what `check-alternatives.py` requires the plan to cite.

**Primary recommendation:** Treat every fragment edit as a token-budget decision first and a wording decision second — gsd-core enforces no size limit on rendered fragment text (only an 8 MiB DoS backstop at load time), so the D-08 45-line ceiling is the only thing standing between this capability and unbounded per-invocation context cost, and the plan should cite that absence of an external limit explicitly.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fragment content (the 4 `.md` files) | Capability manifest (data) | Agent prompt (rendered) | Author-owned Markdown, materialized verbatim into another agent's context at a fixed lifecycle point — no application-tier code involved |
| `plan:post` gate script | Capability manifest (script) | — | `check-alternatives.py` is explicitly out of scope (D-01); untouched by this phase |
| Version/description strings | Capability manifest (metadata) | — | `capability.json`, `.claude-plugin/plugin.json`, `README.md` — human- and agent-facing prose, no runtime behavior |
| Fragment → prompt rendering | gsd-core (`loop-resolver.cjs` + `capability-validator.cjs`) | — | Owned by gsd-core, explicitly out of scope (phase boundary: "no change to gsd-core itself"); this phase can only work within gsd-core's existing verbatim-injection contract |
| Release/tag/branch mechanics | Git / GitHub (`sota-numerics` repo) | — | D-22–D-27; standard git flow, no new tooling |

## Standard Stack

Not applicable in the conventional sense — this phase adds no dependency. The "stack" is:

| Component | Version (verified) | Purpose |
|-----------|---------------------|---------|
| `sota-numerics` capability | 0.1.3 → 0.2.0 (target) | The artifact under change |
| Python 3, stdlib only | unchanged | `check-alternatives.py` — untouched (D-01) |
| gsd-core | `>=1.10.0` (per `capability.json` `engines.gsd`) [VERIFIED: .worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/capability.json] | Host runtime that renders the fragments |

### Alternatives Considered — not applicable to package selection

No library/package alternatives apply. The "Alternatives Considered" work for this phase's own `*-PLAN.md` files is about **mechanism** choices in prompt/information architecture; see `## Code Examples` and `## Common Pitfalls` below for the citable sources against each of the four locked decisions.

## Package Legitimacy Audit

**Not applicable.** This phase installs no new packages in either `gsd-beads` or `sota-numerics`. `check-alternatives.py` (stdlib-only, no child processes — verified in its own docstring, quoted below) is unchanged. No `npm view` / `pip index versions` / `cargo search` check is warranted.

## Verified Rendering Mechanics (the load-bearing research finding)

This is the part of the phase that is *not* covered by CONTEXT.md and is not something training data can be trusted on — it had to be read from the installed gsd-core source this session.

### How `fragment.path` becomes prompt text

1. **Materialization (capability install/load time).** `capability-validator.cjs`'s `materializeHookFragments(cap, capDir)` walks `cap.steps` and `cap.contributions`, and for every hook whose `fragment.path` is set (and `fragment.inline` is not), reads the file via a bounded reader and assigns the result to `fragment.inline`:
   ```
   const body = readSmallRegularFile(abs, FRAGMENT_MAX_BYTES);
   ...
   fragment.inline = body;
   ```
   [VERIFIED: /home/dd/.claude/gsd-core/bin/lib/capability-validator.cjs:2717-2724] — quoted verbatim above.
   The only size constraint is:
   ```
   const FRAGMENT_MAX_BYTES = 8 * 1024 * 1024;
   ```
   [VERIFIED: /home/dd/.claude/gsd-core/bin/lib/capability-validator.cjs:2677] — an 8 MiB DoS backstop against a forged oversized/FIFO fragment file, not a prompt-budget control. The comment beside it states the intent explicitly: "A real fragment is a few KiB of markdown; 8 MiB is wildly more than any legitimate fragment" [VERIFIED: capability-validator.cjs:2672-2675]. **There is no line-count, token-count, or KB ceiling enforced by gsd-core below 8 MiB** — the D-08 45-line budget is a self-imposed discipline with no mechanical backstop from the host.

2. **Dispatch (per-lifecycle-point, at every phase run).** All four contribution points this capability uses are documented in one point-agnostic contract, `references/loop-hook-dispatch.md`:
   ```
   Inject `fragment.inline` verbatim into the context for the role named in `into`
   (e.g. `orchestrator`, `planner`). Do not paraphrase — the text is the product.
   ```
   [VERIFIED: /home/dd/.claude/gsd-core/references/loop-hook-dispatch.md — "### `contribution`" section] — quoted verbatim.
   Confirmed cut over for all four of this capability's points, each via `gsd_run loop render-hooks <point> --raw` followed by "Contribution dispatch: inject every `kind == "contribution"` fragment per @gsd-core/references/loop-hook-dispatch.md":
   - `plan:pre` → planner: `workflows/plan-phase.md` — "Contribution dispatch (#3606): inject `kind == "contribution"` fragment from `PLAN_PRE_HOOKS_JSON` ... per @gsd-core/references/loop-hook-dispatch.md" [VERIFIED: /home/dd/.claude/gsd-core/workflows/plan-phase.md:414]
   - `execute:wave:pre` → executor: [VERIFIED: /home/dd/.claude/gsd-core/workflows/execute-phase.md:656]
   - `execute:wave:post` → verifier: [VERIFIED: /home/dd/.claude/gsd-core/workflows/execute-phase.md:1026]
   - `ship:pre` → orchestrator: [VERIFIED: /home/dd/.claude/gsd-core/workflows/ship.md:109]

3. **No budget trimming applies to this render path.** gsd-core does have a token-budget composer (`context-composer.cjs`, extracted from `prompt-budget.cts` under ADR-1671), but its own docstring scopes it to a different consumer: "the review-prompt consumer assembles Markdown sections... the per-runtime emission consumer renders differently" [VERIFIED: /home/dd/.claude/gsd-core/bin/lib/context-composer.cjs:14-19]. No workflow file wires `contribution` dispatch through `composeWithinBudget` — the four fragments are injected in full, every time, with no truncation ladder. This directly grounds D-08's "cost once per restatement" framing: there is no host-side trimming to fall back on if the fragments grow past 45 lines.

**Consequence for the plan:** the plan can state, as a verified (not assumed) fact, that fragment length is a direct, untrimmed, per-invocation token cost on the target role's context, with the only ceiling being the author's own discipline. This is the strongest evidence for D-06's "shared fragment multiplies cost by four" argument and for keeping the four fragments role-sliced rather than consolidated.

## Architecture Patterns

### Fragment/gate topology (unchanged by this phase)

```
capability.json
  ├─ contributions[0] plan:pre        → planner-sota.md          (advisory, onError: skip)
  ├─ contributions[1] execute:wave:pre → executor-numerics.md    (advisory, onError: skip)
  ├─ contributions[2] execute:wave:post→ verifier-precision.md   (advisory, onError: skip)
  ├─ contributions[3] ship:pre         → ship-precision-advisory.md (advisory, onError: skip)
  └─ gates[0] plan:post → check-alternatives.py (blocking: true, onError: halt)  ← untouched (D-01)
```
Data flow: `git rev-parse --show-toplevel` (or `$GSD_HOME`) locates the bundle → `materializeHookFragments` reads each `.md` file into `fragment.inline` at capability-load time → `gsd_run loop render-hooks <point> --raw` returns the `activeHooks` envelope for that point on every phase-lifecycle event → the host workflow (`plan-phase.md` / `execute-phase.md` / `ship.md`) injects `fragment.inline` verbatim into the named role's context, per `loop-hook-dispatch.md`. The `plan:post` gate is a fully separate code path (`command-exit-zero` predicate calling `check-alternatives.py` as a subprocess) that this phase does not touch.

### Recommended edit sequence (not a new structure — same 4 files, same 1 gate)
```
.gsd/capabilities/sota-numerics/
├── capability.json                # version bump only (0.1.3 → 0.2.0); contributions[] shape unchanged (D-05)
├── fragments/
│   ├── planner-sota.md            # + project-consistency + plan-completeness; prune restated gate mechanics
│   ├── executor-numerics.md       # + agent-facing prose + quiet runtime output + efficiency
│   ├── verifier-precision.md      # + matching findings for the new dimensions
│   └── ship-precision-advisory.md # extend existing claim-backing confirmation to new claims
├── scripts/check-alternatives.py  # UNCHANGED (D-01) — docstring/comments still get the D-17 prose refactor
├── NOTES.md                       # pruning only (D-18); anti-regression entries stay intact
└── (README.md, .claude-plugin/plugin.json — sibling files, also in scope per D-17)
```

### Pattern: leading-word compression (D-09)
**What:** Define a pretrained-recruiting word once, then reuse the bare token everywhere the concept recurs, instead of re-spelling the concept in each fragment.
**When to use:** Exactly D-09's three coined anchors — **with the grain** (project consistency), **quiet** (low token cost at runtime), **legible** (unambiguous + complete prose) — each defined once in its home fragment, then referenced by the bare word in any fragment that needs it again.
**Source pattern (verified against the actual technique, not the specific words, which are this phase's own coinages per Claude's Discretion):**
```
## Leading words
A leading word is a compact concept already living in the model's pretraining that
the agent thinks with while running the document... Coining your own works if you
define it clearly, but a made-up word recruits no priors: you pay in definition
tokens what a pretrained word gives free; reach for an existing word first.
```
[CITED: `~/.local/share/agent-skills/writing-for-agents/SKILL.md` — "## Leading words" section, read directly this session]

### Pattern: state the target, not the ban (D-10)
**What:** Phrase every new instruction as the behavior wanted, never as a prohibition.
**Source:**
```
Negation is the failure mode beside this lever: steering by prohibition drags the
forbidden behaviour into context and makes it more available, not less... Prompt
the positive: state the target behaviour... so the banned one is never spoken.
```
[CITED: `~/.local/share/agent-skills/writing-for-agents/SKILL.md` — "## Leading words" section, "Negation" subsection]
This is exactly D-10's stated rationale, independently corroborated by the skill text itself — strong signal the plan's fragment wording should follow this skill's own vocabulary discipline even though D-14/D-15 forbid *citing* the skill in shipped text.

### Anti-Patterns to Avoid
- **Shared "extended definition" fragment injected at 4 points (the rejected D-06 alternative):** every render point pays the full token cost of every other point's slice — a 4x multiplier with no corresponding benefit, since `loop-hook-dispatch.md` injects `fragment.inline` verbatim with no dedup/caching across points [VERIFIED: loop-hook-dispatch.md, contribution section, quoted above].
- **Mechanizing an unmeasurable check into the blocking gate:** see Common Pitfalls below — this is D-01's rejected alternative and has independent literature support (Goodhart's Law / proxy-metric fragility).
- **Referencing the user-local `writing-for-agents` skill path from shipped fragment text (rejected D-14 alternative):** the path `~/.local/share/agent-skills/writing-for-agents` is confirmed to exist only on this machine — a capability that "declares support for every GSD runtime" [VERIFIED: .worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/capability.json — `runtimeCompat.supported: ["*"]`] cannot assume that path exists for any other installer.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting whether a plan's Alternatives section is well-formed | A new regex/heuristic bolted onto the existing gate | Nothing — D-01 leaves `check-alternatives.py` untouched | The existing predicate's design principle (only gate what has "a valid measurement instrument") is the reason this phase must NOT add mechanical checks for the six new SOTA dimensions — see Pitfall 1 |
| A size limit for fragment text | A new line-count enforcement script | The existing `wc -l` manual check named in D-20 | gsd-core provides no automatic budget enforcement at this render path (verified above); a hand-rolled enforcement script would be new test infrastructure, which D-21 explicitly forbids adding for prose |

**Key insight:** every "don't hand-roll" instinct in this phase points the same direction as the locked decisions — the capability's own design principle (mechanize only what has a real measurement instrument) applies recursively to how this phase should verify its own compliance.

## Common Pitfalls

### Pitfall 1: Treating "advisory" as "unenforced, so it doesn't matter how it's worded"
**What goes wrong:** A planner or executor treats fragments feeding the executor/verifier/ship roles as low-stakes because `onError: "skip"` means a render failure never blocks. But the four fragments' *content*, once rendered, is exactly what steers those roles' behavior every single run — the enforcement mechanism (gate vs. advisory) is orthogonal to the fragment's actual influence on outcomes.
**Why it happens:** Conflating "not gated" with "not load-bearing."
**How to avoid:** D-04 already routes this correctly — compliance evidence for the six new dimensions comes from verifier/ship *findings*, i.e., a human or later gate still gets a signal, just not a blocking one.
**Warning signs:** A plan task that treats "extend executor-numerics.md" as pure prose polish with no verification step attached.

### Pitfall 2: Adding a mechanical check for an unmeasurable property (D-01's rejected alternative), rediscovering the false-positive failure mode independently confirmed by the literature
**What goes wrong:** A future contributor (or an over-eager plan) adds a regex that scores for words like "consistent," "unambiguous," "complete," "efficient" in a plan's prose, intending to extend the blocking gate.
**Why it happens:** The existing gate's success (a working, if narrow, mechanical check) invites generalizing the same technique to properties that don't share its structure.
**How to avoid:** D-03 states the mechanism precisely: the existing predicate works because it checks *structural* facts (a heading exists, two named entries exist, a citation matches a URL/doc-ref regex, a year falls in a window) — never semantic quality. A regex over "consistent"/"unambiguous"/etc. would score vocabulary presence, not the property, which is a textbook Goodhart's-Law failure: "When a measure becomes a target, it ceases to be a good measure" — proxies with high aggregate correlation can still carry "high segment-level fragility," i.e., they misfire in exactly the cases (well-written but wordless-of-the-magic-terms plans) where correctness matters most [CITED: https://arxiv.org/pdf/2505.23445 — "Strong, Weak and Benign Goodhart's law" (2025)] [CITED: https://arxiv.org/pdf/2604.14352 — PROXIMA reliability-scoring framework for proxy metrics (2026)].
**Warning signs:** Any task in the plan whose action is "add a check to `check-alternatives.py`" or "add a new `gates[]` entry" for the six new dimensions — this contradicts D-01/D-02 directly and should be rejected at plan-check.

### Pitfall 3: Letting fragment growth silently erode the target roles' context quality
**What goes wrong:** Growing planner-sota.md, executor-numerics.md, etc. without pruning invisibly taxes every future invocation's attention budget, even though each individual addition looks small.
**Why it happens:** No mechanical size gate exists (verified above) to catch this — it's purely a human/plan-check discipline (D-08's 45-line ceiling).
**How to avoid:** Anthropic's own context-engineering guidance frames this directly: context is a "finite, precious resource," and the core constraint is that "as context grows, the model's ability to capture [pairwise token] relationships gets stretched thin" [CITED: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — Anthropic Applied AI team, "Effective context engineering for AI agents," Sep 2025]. Chroma's controlled study found performance degrading "noticeably as input gets longer" across all 18 tested models at every length increment, independent of whether the window is nominally full [CITED: Chroma Research, "Context Rot: How Increasing Input Tokens Impacts LLM Performance," Jul 2025, summarized at https://www.morphllm.com/context-rot]. Every added fragment line is a permanent per-invocation cost that these findings show has a real, measured downside, not just an aesthetic one — this is the strongest available grounding for D-08's line budget as a genuine engineering constraint rather than house style.
**Warning signs:** Any fragment edit that leaves the total above 45 lines, or that duplicates a sentence already present in a sibling fragment instead of using a shared leading word.

### Pitfall 4: Pointing at a skill path that doesn't travel with the capability
**What goes wrong:** Citing `~/.local/share/agent-skills/writing-for-agents/SKILL.md` by name or path from inside `executor-numerics.md`, on the assumption that "everyone probably has this skill."
**Why it happens:** The skill is genuinely useful and its rules are the direct source for this phase's own compressed rules (D-16) — the temptation to just point at it instead of restating it is real.
**How to avoid:** D-14/D-15's rationale is airtight and independently checkable: `capability.json`'s `runtimeCompat.supported` is `["*"]` [VERIFIED: capability.json, quoted in Standard Stack above], meaning the capability declares support for every GSD host, while the skill directory is user-local and Claude-specific. A pointer whose target is absent for most installs is worse than inlining, per the skill's own stated pointer principle: "A must-have target behind a weakly worded pointer is a variance bug: sharpen the wording first, and inline the material only if sharpening fails" [CITED: `~/.local/share/agent-skills/writing-for-agents/SKILL.md` — "## Context pointers"] — here sharpening cannot fix a target that is simply absent, so inlining (D-14) is the correct move by the skill's own logic, not just this phase's local decision.
**Warning signs:** Any fragment line that names "writing-for-agents" or contains the literal path `~/.local/share/agent-skills`.

## Code Examples

### Example 1: The existing quiet-output precedent to cite for D-11/D-13 (in-repo, verified)
```python
# check-alternatives.py's actual stderr contract, quoted from its own docstring:
# "Exit 0 = every discovered plan passes. Exit 1 = one or more violations,
#  printed to stderr as `<plan_path>: <reason>`, followed by exactly one
#  `remediation: ...` line. Exit 2 = usage/IO error..."
```
[VERIFIED: /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:12-14]
The literal remediation line printed at runtime:
```python
f"remediation: fix the plans above, then re-run /gsd-plan-phase {phase_label} --force",
```
[VERIFIED: check-alternatives.py:323]

### Example 2: The existing `@file:` spill precedent to cite for D-13 (in-repo, verified)
```javascript
// Large payloads exceed Claude Code's Bash tool buffer (~50KB).
// Write to tmpfile and output the path prefixed with @file: so callers can detect it.
if (json.length > 50000) {
    ...
    data = '@file:' + tmpPath;
}
```
[VERIFIED: /home/dd/.claude/gsd-core/bin/lib/io.cjs:189-196] — D-13's claim of "roughly 50KB" is precise: the literal threshold is `50000` (bytes of serialized JSON, not characters of arbitrary text), so the fragment wording should say "tens of kilobytes" or cite the exact `50000` rather than round further.

### Example 3: External CLI-output convention supporting D-11 (compact success / one-line failure / exit codes)
```
Return zero exit code on success, non-zero on failure... Send primary output to
stdout... Log messages and errors go to stderr.
```
[CITED: https://clig.dev/ — Command Line Interface Guidelines, "Output" and "Errors" sections] — note CLIG's own nuance: it argues *against* fully silent success for interactive human use ("it's rare that printing nothing at all is the best default"), but the phase's target audience for this rule is explicitly agent-invoked code (D-12), where CLIG's own stdout/stderr and exit-code separation still applies cleanly even where its "always print something for humans" caveat does not.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| "Prompt engineering" (wording a single instruction well) | "Context engineering" (curating the full token budget across a multi-step agent run) | Named/systematized by Anthropic, Sep 2025 [CITED: anthropic.com/engineering/effective-context-engineering-for-ai-agents] | Reframes D-08's line budget from a style preference into the current, named discipline this phase is applying |
| Assuming a bigger context window removes the need to prune | "Context rot" — measured, monotonic quality degradation with input length, independent of window fullness | Chroma Research, Jul 2025 [CITED: https://www.morphllm.com/context-rot]; extended by Du et al. 2025 showing it isn't a retrieval artifact | Directly undercuts any argument that "gsd-core has no size limit, so 45 lines doesn't matter" — the model-level cost exists regardless of the host's mechanical limit |

**Deprecated/outdated:** None specific to this capability — `sota-numerics` v0.1.3 is current (this session confirmed `.worktrees/sota-numerics-release-013` HEAD, `origin/main`, and `origin/HEAD` all resolve to `eccad87` [VERIFIED: `git log -1` in that worktree]).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The specific coined leading words in D-09 ("with the grain," "quiet," "legible") will read as intended to future agents encountering them for the first time without the skill's definition-priming | Architecture Patterns / Pattern: leading-word compression | Low — D-09 requires each word be defined once in its home fragment before reuse, which is exactly the skill's own mitigation for a coined (non-pretrained) word; worst case is a slightly longer definition, not a broken mechanism |
| A2 | No other gsd-core workflow file (beyond plan-phase.md, execute-phase.md, ship.md) renders these four contribution points a second time through a different, budget-trimming path | Verified Rendering Mechanics | Low-medium — verified via targeted grep across `workflows/*.md` for the four exact points; a renamed or newly added workflow file introduced after this research would not be caught, but no evidence of one exists as of `eccad87`-era gsd-core install |

**If this table is empty:** N/A — two low-risk assumptions logged above; everything else in this research traces to a file read this session or a dated external citation.

## Open Questions

1. **Exact per-fragment line allocation within the 45-line ceiling**
   - What we know: current totals (planner 13, executor 5, verifier 5, ship 4 = 27 total, all confirmed by direct read this session) and D-08's target ceiling of 45.
   - What's unclear: how the ~18 new lines split across 4 fragments given each fragment absorbs a different subset of the 6 new dimensions (D-07's role slicing) plus D-08's required pruning of planner-sota.md's gate-mechanics restatement.
   - Recommendation: leave this to Claude's Discretion per CONTEXT.md — it is explicitly named there as in-scope for planner judgment, not something research can pre-resolve without writing the fragments themselves.

2. **Whether `README.md`'s existing 240-line literature section (the "Why block the plan" section with its own References list) needs any addition for the six new dimensions**
   - What we know: D-17 requires `README.md` to comply with the extended SOTA definition (i.e., be internally/project consistent, unambiguous, complete, efficient, legible); D-18 exempts only `NOTES.md` from full compliance, requiring pruning-only there.
   - What's unclear: "comply with the extended definition" for a human-facing README that documents six new advisory dimensions could mean either (a) the README's own prose must itself exhibit those six properties, or (b) the README's *description* of what the capability now does must be updated to list the six new dimensions (an accuracy/completeness requirement, distinct from a style requirement).
   - Recommendation: treat as both — D-20's evidence bar ("every behavioral claim in README.md traces to a line of code or config") means the README's table of "What it changes" (currently listing only the original 5 rows of behavior) should gain the six new dimensions' behavior, and the surrounding prose should itself pass the extended bar.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Git | Branching/tagging in `sota-numerics` repo | ✓ | confirmed working in `.worktrees/sota-numerics-release-013` | — |
| Python 3 | Existing test suite (`test_check_alternatives.py`), untouched gate script | ✓ | stdlib only, no new deps | — |
| GitHub CLI (`gh`) | Opening the PR per D-26 | not probed this session | — | manual PR via `git push` + web UI if `gh` unavailable |
| `sha256sum`/`shasum` + `gsd-tools` | Claude auto-install hash check (README's "What the Claude hooks do") | not relevant to this phase's edits | — | — |

**Missing dependencies with no fallback:** None identified.
**Missing dependencies with fallback:** `gh` CLI (not probed) — PR can be opened manually via git push + GitHub web UI if absent.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib) + Bash smoke scripts, both pre-existing in `sota-numerics` |
| Config file | none — CI invokes them directly (see below) |
| Quick run command | `python3 -m unittest tests/test_check_alternatives.py` |
| Full suite command | `bash tests/test-session-start.sh && bash tests/test-gate-script-resolution.sh && python3 -m unittest tests/test_check_alternatives.py` |

CI already runs exactly this three-step sequence [VERIFIED: /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/.github/workflows/ci.yml — `session-start smoke test`, `gate script resolution test`, `alternatives-checker unit test` steps].

### Phase Requirements → Test Map
No `REQ-ID`s are mapped to this phase (confirmed: REQUIREMENTS.md's traceability table covers only the beads-capability v1.4 requirements RES-01..CUT-02, none of which reference this phase). Per D-21, this phase adds no new test infrastructure for prose; the existing suite is the regression guard that the fragment/README/description refactor left the *gate's behavior* unchanged.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|--------------------|--------------|
| (none mapped) | Gate behavior unchanged after refactor | unit | `python3 -m unittest tests/test_check_alternatives.py` | ✅ |
| (none mapped) | Fragment rendering (hooks) unchanged | smoke | `bash tests/test-session-start.sh` | ✅ |
| (none mapped) | Gate script path resolution unchanged | smoke | `bash tests/test-gate-script-resolution.sh` | ✅ |
| (D-08, manual) | Fragment line budget ≤ 45 total | manual | `wc -l .gsd/capabilities/sota-numerics/fragments/*.md` | ✅ (D-20 names this explicitly) |
| (D-20, manual) | Every README behavioral claim traces to code/config | manual review | — | N/A — human/reviewer check, not automatable |

### Sampling Rate
- **Per task commit:** `python3 -m unittest tests/test_check_alternatives.py` (fast, catches gate-behavior regressions immediately)
- **Per wave merge:** full three-step CI sequence above
- **Phase gate:** CI green on the exact commit that reaches `main` (D-26) — no separate release step exists (D-25), so this is also the ship gate

### Wave 0 Gaps
None — existing test infrastructure (Python unittest + 2 bash smoke scripts) already covers every behavior this phase can regress (gate logic, hook materialization/session-start, gate-script path resolution). D-21 explicitly forbids adding new test infrastructure for the prose changes themselves.

## Security Domain

`security_enforcement` is absent from `.planning/config.json` in `gsd-beads` [VERIFIED: /home/dd/projects/gsd-beads/.planning/config.json — no `security_enforcement` key present], so it is treated as enabled per the default rule. In practice almost every ASVS category is inapplicable: this phase edits advisory Markdown prompt text, two `description` strings, and a version number — no authentication, session, access-control, or cryptographic surface is touched, and the one component with a real trust boundary (`check-alternatives.py`, which parses untrusted `PLAN.md` content) is explicitly out of scope (D-01) and unmodified.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|-------------------|
| V2 Authentication | No | N/A — no auth surface in this phase's edits |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Marginal — see note | `check-alternatives.py` already treats `PLAN.md` as untrusted, stdlib-only, no `eval`/shell-out [VERIFIED: check-alternatives.py:16-21, its own docstring — "treated as untrusted input throughout -- never eval'd, never shelled out"]; this phase does not touch that script, only the prose around it (docstring/comments per D-17), so no new input-validation surface is created |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| A fragment file becomes a supply-chain injection vector if a future contributor lets `fragment.path` resolve outside the capability directory | Tampering | Already mitigated by gsd-core, not this phase: `materializeHookFragments` explicitly checks `abs.startsWith(capRoot + path.sep)` and errors on escape [VERIFIED: capability-validator.cjs:2705-2711] — worth noting in the plan as a reason NOT to move fragment files outside `fragments/` during the D-05 in-place edit |

## Sources

### Primary (HIGH confidence — read directly this session)
- `.worktrees/sota-numerics-release-013/.gsd/capabilities/sota-numerics/capability.json`, `fragments/*.md`, `scripts/check-alternatives.py`, `NOTES.md`, `README.md`, `.claude-plugin/plugin.json`, `.github/workflows/ci.yml`, `tests/test_check_alternatives.py` — full or targeted reads, quoted verbatim above where cited
- `/home/dd/.claude/gsd-core/bin/lib/capability-validator.cjs` — `materializeHookFragments`, `FRAGMENT_MAX_BYTES` (lines 2672-2735, quoted verbatim)
- `/home/dd/.claude/gsd-core/bin/lib/io.cjs` — `@file:` spill threshold (lines 185-200, quoted verbatim)
- `/home/dd/.claude/gsd-core/references/loop-hook-dispatch.md` — contribution dispatch contract, quoted verbatim
- `/home/dd/.claude/gsd-core/workflows/plan-phase.md`, `execute-phase.md`, `ship.md` — contribution dispatch call sites confirmed by line number
- `~/.local/share/agent-skills/writing-for-agents/SKILL.md` — read directly this session; source for D-09/D-10/D-14 rationale cross-checks

### Secondary (MEDIUM confidence — WebSearch, official/primary sources)
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Sep 2025)
- [Chroma Research — Context Rot (summarized)](https://www.morphllm.com/context-rot) (Jul 2025 origin)
- [clig.dev — Command Line Interface Guidelines](https://clig.dev/)
- [Strong, Weak and Benign Goodhart's Law](https://arxiv.org/pdf/2505.23445) (2025)
- [PROXIMA: A Reliability Scoring Framework for Proxy Metrics](https://arxiv.org/pdf/2604.14352) (2026)

### Tertiary (LOW confidence — not relied upon for any claim above)
None used without cross-check.

## Metadata

**Confidence breakdown:**
- In-repo rendering mechanics: HIGH — read directly from installed gsd-core source and the target repo this session, all claims carry file:line citations and verbatim quotes.
- External mechanism-choice citations (Goodhart's Law, context rot, CLI conventions): MEDIUM — WebSearch-sourced but from primary/official sources (Anthropic's own blog, arXiv preprints, clig.dev), each carrying an in-window (≤6 years) date as `check-alternatives.py` requires.
- Fragment wording specifics (exact new sentences): LOW/not researched — correctly left to Claude's Discretion per CONTEXT.md; not a research question.

**Research date:** 2026-09-06
**Valid until:** 30 days (stable domain — gsd-core rendering mechanics and the target repo's `main` branch are both unlikely to shift meaningfully in that window; re-verify `origin/main` HEAD before executing if the phase start slips past that window)
