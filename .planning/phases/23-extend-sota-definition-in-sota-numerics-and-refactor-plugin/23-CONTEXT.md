# Phase 23: Extend SOTA definition in sota-numerics and refactor plugin to comply - Context

**Gathered:** 2026-09-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend what the `sota-numerics` capability means by "SOTA" so its advisory fragments also steer generated code toward internal and project consistency, unambiguity, completeness, efficiency, agent-facing prose that follows the writing-for-agents standard, and low token cost when an agent runs that code. Then refactor the plugin's own content to meet the same extended standard.

The work lands in the `sota-numerics` repository (`https://github.com/davdittrich/sota-numerics.git`), not in `gsd-beads`. `gsd-beads` only hosts the marketplace entry that points at that repository.

Out of scope: the `plan:post` gate's checking logic, the `beads-lifecycle` and `ponytail-everywhere` plugins, and any change to gsd-core itself.

</domain>

<decisions>
## Implementation Decisions

### Enforcement level

- **D-01:** The `plan:post` gate stays exactly as it is. `check-alternatives.py` gains no new checks, and `capability.json` gains no new gate.
- **D-02:** All six added dimensions ship as advisory fragment text at the existing contribution points.
- **D-03:** Rationale, and the reason a future contributor must not "finish the job" by adding checks: the existing gate works because its predicate has a valid measurement instrument — a section heading, two named entries, a citation, a four-digit year inside a window, a `Decided by:` line. "Consistent", "unambiguous", "complete", and "efficient" have no such instrument. A regex that scores their vocabulary measures word presence, not the property, so it would pass plans that recite the words and block plans that demonstrate the property without them. The gate is `blocking: true` with `onError: halt`, so a false positive there halts planning outright. An unmeasurable blocking check is compliance theater with a halt attached.
- **D-04:** Compliance evidence for the added dimensions comes from the verifier and ship fragments as findings, which is where the capability already puts every judgment it cannot mechanize.

### Fragment architecture

- **D-05:** Extend the four existing fragments in place. No new fragment files, no new contribution points, no change to the shape of `capability.json`'s `contributions` array.
- **D-06:** Rejected alternative — one shared "extended SOTA definition" fragment injected at all four points. Every point that renders it pays its full token cost, so a shared fragment multiplies context load by four while the four roles need different slices.
- **D-07:** Role slicing. `planner-sota.md` takes project consistency and plan completeness. `executor-numerics.md` takes agent-facing prose, quiet runtime output, and efficiency. `verifier-precision.md` takes the matching findings. `ship-precision-advisory.md` takes the claim-backing confirmation it already carries, extended to the new claims.
- **D-08:** Line budget. The four fragments total 27 lines today (planner 13, executor 5, verifier 5, ship 4). The extended set must total 45 lines or fewer. Part of the room comes from pruning `planner-sota.md`, which currently restates the gate's mechanics at length and duplicates what `check-alternatives.py` already enforces.
- **D-09:** Leading words carry the added dimensions so they cost tokens once instead of once per restatement: **with the grain** for project consistency, **quiet** for low token cost at runtime, **legible** for prose that is unambiguous and complete. Define each once, then repeat only the word.
- **D-10:** State every added instruction as the target behavior rather than as a prohibition. A ban names the behavior it forbids and makes it more available, not less.

### What "token-efficient during execution" means

- **D-11:** It means the generated code is cheap for an agent to run. On success it prints a compact, machine-readable result or nothing at all. On failure it prints one line naming the problem and one line naming the fix. It signals through exit codes rather than prose. It emits no progress chatter. Output large enough to flood a context window goes to a file and the code prints the path.
- **D-12:** This applies to code an agent invokes directly — scripts, CLIs, test harnesses, hooks — and not to library internals an agent never runs by hand.
- **D-13:** Two in-repo precedents anchor the wording, and both are already familiar to this project's agents: `check-alternatives.py` prints `<plan_path>: <reason>` per violation followed by exactly one `remediation: ...` line, and `gsd-tools` swaps stdout over roughly 50KB for an `@file:<tmp>` pointer.

### writing-for-agents portability

- **D-14:** Inline the operative rules into the executor fragment. Do not reference the skill by name.
- **D-15:** Rationale: the skill lives at `~/.local/share/agent-skills/writing-for-agents`, a user-local directory. It is not part of this plugin, not part of gsd-core, and not present for anyone else who installs `sota-numerics`. The capability declares support for every GSD runtime, so a pointer to that path would be dead for every consumer but its author. A pointer whose target is missing is worse than no pointer.
- **D-16:** The rules that survive compression to code-facing use: keep each meaning in one place, so a comment says why and the code says what; delete any line the agent would already honor by default; phrase instructions as the target behavior; give every completion criterion a bound the agent can check; keep a definition next to its caveats; name the ceiling of any simplification.

### Self-compliance scope for the refactor

- **D-17:** Must comply: the four fragments, `README.md`, the `description` fields in `.claude-plugin/plugin.json` and `capability.json` including the gate's `description` string, and `check-alternatives.py`'s module docstring and comments.
- **D-18:** `NOTES.md` gets pruning only. Its anti-regression entries are the single source of truth for the capability's deliberate divergences and stay intact; remove only what `README.md` already says.
- **D-19:** `hooks/*.sh` and `tests/` get no prose refactor. Touch a message there only when it is agent-facing and breaks the quiet or legible rule.
- **D-20:** Evidence of compliance: the existing Python and shell suites pass unchanged, `wc -l` on the four fragments confirms the D-08 budget, and every behavioral claim in `README.md` traces to a line of code or config.
- **D-21:** Add no test infrastructure for prose. The existing suites are the regression guard that the refactor left gate behavior alone.

### Target repository and release

- **D-22:** Work in the existing clone at `.worktrees/sota-numerics-release-013`, on a new branch cut from `origin/main`. Verified 2026-09-06: that clone's checkout and `origin/main` are both at `eccad87`, so it is current.
- **D-23:** Version becomes `0.2.0` in both `.claude-plugin/plugin.json` and `.gsd/capabilities/sota-numerics/capability.json`, kept in sync. Minor bump: the instruction surface grows and prompt behavior changes, while the gate contract does not.
- **D-24:** The phase ends at published `0.2.0`. Answered by the user on 2026-09-06.
- **D-25:** Because the marketplace entry points at the repository URL rather than at a tag, merging to `main` is the publish. There is no separate release step, so everything that must be true of a release must be true before the merge.
- **D-26:** Publish ordering. Internal review and every fix it accepts land on the branch before the pull request opens, so an external reviewer's first pass sees a finished diff rather than a known-incomplete one. CI must be green on the exact commit that reaches `main`. Any claim the release makes about behavior must trace to code, not to an assertion in the pull request body.
- **D-27:** Tag the published commit `v0.2.0`. `0.1.3` left no immutable marker for what was served; this phase does not repeat that.

### Claude's Discretion

- Exact wording of each fragment line, within the D-08 budget and the D-09 leading words.
- Which specific lines of `planner-sota.md` get pruned to make room.
- Commit granularity within the branch.

### Amendments

Four decisions above were breached during execution. Each breach was justified and
maintainer-approved at the time, but none was written down, and this section fixes that.
The original D-01, D-18, D-19 and D-21 text is left exactly as written — these are
amendments, not rewrites.

Every count below was re-derived at `3e9fa2e` and is stated against that commit, because
the branch is still moving: a count with no commit behind it is how this section went
stale the first time. At `3e9fa2e`, 37 of the 106 commits on this branch touch a 244-line
guard and an 893-line test file, against 14 on the fragments that are the phase's declared
scope. The release's one arbitrary-code-execution defect landed inside that unrecorded
expansion. An unrecorded scope change is precisely where review attention does not go,
which is how a green suite shipped it.

- **A-01 (amends D-01), 2026-09-07.** D-01 froze the gate: no new checks, no changed
  `capability.json` gate. The gate changed in four ways under D-01, and has changed
  further since as review found more defects; the current set is the commit history on
  `capability.json` and `check-alternatives.py`, not a number cached here. Cause: `${PHASE_DIR}` was spliced
  into a command handed to `sh -c`, so a phase directory name could execute as shell source,
  and one payload class exited `0` while doing so — the blocking gate reported success on a
  phase that had just run arbitrary code. No manifest-side quoting could close it, because
  every `sh` quoting context ends on a delimiter a directory name may contain. The command
  is now constant and `check-alternatives.py` resolves the phase from `.planning/STATE.md`.
  The other three changes: an empty phase argument exits `2` rather than scanning the
  working directory; fenced code blocks no longer count as plan content; one UTF-8 decode
  message names the offending plan. Measured scope of the change, at `3e9fa2e`: of this
  release's 89 checker tests, 61 pass unchanged against the 0.1.3 checker on `origin/main`
  and 28 fail. The fenced-block fix
  changes verdicts — a plan that passed under 0.1.3 may now fail. Residual coupling to
  gsd-core's step ordering, and the upstream fix, are recorded in the capability's
  `NOTES.md` §6 and tracked as `gsd-beads-g72`.

- **A-02 (amends D-18), 2026-09-07.** D-18 allowed `NOTES.md` pruning only. It gained an
  entire new §6. Cause: D-18 assumed NOTES.md's divergence set was complete, and the gate
  splice above was a deliberate divergence that had never been recorded. §6 has since been
  replaced outright, because its first version described the splice as fail-closed when it
  was a bypass, and justified rejecting an alternative with a claim about single-quote
  behaviour that is false. The current §6 is written against measurements.

- **A-03 (amends D-19 and D-21), 2026-09-07.** D-19 allowed `hooks/*.sh` and `tests/` message
  touch-ups only, and D-21 allowed no test infrastructure for prose at all. Both were
  breached by the same expansion: `hooks/capability-auto-install.sh` went from 99 lines to
  244, and `tests/test-capability-auto-install.sh` is a new 893-line file whose case `D0`
  parses README.md's refusal table and asserts it is the same set the hook emits — prose
  infrastructure, in a file `origin/main` does not have. (`origin/main`'s own
  `test_check_alternatives.py` already asserted on README.md, so those assertions are not
  evidence of this breach; the new file is.) Cause: the `SessionStart`
  and `SubagentStart` auto-install installs the bundle at global scope, publishing it to
  every project on the machine, and it would do so from an uncommitted development
  worktree. The guard refuses to install bytes the bundle's own upstream cannot be shown to
  hold. The test file is the partition that pins its control flow; two later defects — a
  discarded `ls-files` exit status and an unenumerated `git status` blinding mechanism —
  were found and closed inside that expansion rather than by it, which is the argument both
  for the guard and for having recorded its scope sooner.

</decisions>

<specifics>
## Specific Ideas

- The user's framing: the added dimensions are an extension of the definition of SOTA, not a new concern bolted alongside it. The fragments should read that way — one standard that grew, not two standards sharing a file.
- Delivery speed and token efficiency outrank ceremony for this phase.

</specifics>

<canonical_refs>
## Canonical References

### Capability under change (paths relative to the sota-numerics repo)
- `.gsd/capabilities/sota-numerics/capability.json` — contribution points, the single `plan:post` gate, version
- `.gsd/capabilities/sota-numerics/fragments/planner-sota.md` — current planner advisory, 13 lines
- `.gsd/capabilities/sota-numerics/fragments/executor-numerics.md` — current executor advisory, 5 lines
- `.gsd/capabilities/sota-numerics/fragments/verifier-precision.md` — current verifier advisory, 5 lines
- `.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md` — current ship advisory, 4 lines
- `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` — the gate checker, 330 lines, unchanged by this phase
- `.gsd/capabilities/sota-numerics/NOTES.md` — deliberate divergences, including why `gates[0].onError` is `halt`
- `README.md` — 240 lines, the behavioral contract stated for humans and agents

### Prior phases on this capability
- `.planning/phases/11-sota-numerics-capability-plugin-sota-efficiency-numerical-st/` — original capability build
- `.planning/phases/12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly/` — publication

### Standards applied
- writing-for-agents — context pointers, the context and cognitive loads, information hierarchy and progressive disclosure, completion criteria, leading words, negation, pruning. Read at `~/.local/share/agent-skills/writing-for-agents/SKILL.md`; inlined per D-14 rather than referenced from shipped content.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The four-fragment plus one-gate layout already maps cleanly onto the lifecycle points this phase needs. Nothing new has to be wired.
- `check-alternatives.py`'s stderr contract and `gsd-tools`' `@file:` spill are working examples of D-11's quiet output, usable verbatim as the fragment's illustration.
- The Python and shell suites already cover the gate's behavior, so they double as the refactor's regression guard at no extra cost.

### Established Patterns
- Advisory contributions carry `onError: "skip"`; the one blocking gate carries `onError: "halt"`. `NOTES.md` §1 records this as deliberate. Anything added by this phase is advisory and therefore `skip`.
- Fragment text is rendered into another agent's prompt on every run, so fragment length is a recurring cost rather than a one-time one. This is what D-08 budgets.
- The capability declares support for every GSD runtime. Claude-only paths and hooks must not become load-bearing, which is what D-14 protects.

### Integration Points
- `capability.json` `contributions[].fragment.path` — unchanged; the fragments behind those paths grow.
- The version fields in `.claude-plugin/plugin.json` and `capability.json` must move together.
- The `gsd-beads` marketplace entry for `sota-numerics` points at the repository URL, so `main` is the distribution channel.

</code_context>

<deferred>
## Deferred Ideas

Two findings surfaced during scouting. Neither is in scope for Phase 23; both are tracked.

- `.worktrees/sota-numerics-issue-1` and `.worktrees/sota-numerics-release-013` are clones of the `sota-numerics` repository sitting untracked inside the `gsd-beads` working tree. `git status` lists `.worktrees/` as untracked, so a `git add -A` in `gsd-beads` would commit another project's history into this one. Fix is either a `.gitignore` entry or relocation. Tracked as `gsd-beads-9tg`.
- `0.1.3` was published without a git tag, so the repository has no immutable marker for that version and the marketplace serves whatever `main` holds. D-27 tags this release; the convention for past and future releases is still unwritten. Tracked as `gsd-beads-oh1`.

</deferred>

---

*Phase: 23-extend-sota-definition-in-sota-numerics-and-refactor-plugin*
*Context gathered: 2026-09-06*
