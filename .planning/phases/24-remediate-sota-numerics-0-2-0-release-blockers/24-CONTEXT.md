# Phase 24: Remediate sota-numerics 0.2.0 release blockers and publish - Context

**Gathered:** 2026-09-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Close every blocking finding raised by the four-lens review of `feat/extended-sota-definition` in `davdittrich/sota-numerics`, so the branch satisfies the extended SOTA definition Phase 23 wrote, then publish 0.2.0. Merging is the publish (D-19), so everything that must be true of a release must be true before the merge. Remediation is this phase's early waves; the publish is its last, behind a decision checkpoint (D-22).

Work lands on the existing branch in the worktree at `.worktrees/sota-numerics-release-013`, plus exactly one edit in this repository: the `sota-numerics` entry in `.claude-plugin/marketplace.json`.

Out of scope: new gate predicates beyond repairing the ones that already exist, any new capability feature, and the content decisions Phase 23 already accepted and verified (the six added dimensions, the fragment slicing, the 45-line budget). Phase 23 ends at branch-ready; its plan 23-05 was removed and its publish scope moved here by Phase 23 amendment A-04.

The four review reports in this directory are the requirement source: `REVIEW-CRITICAL-FINAL.md`, `REVIEW-PONYTAIL-FINAL.md`, `REVIEW-AGY-FINAL.md`, `REVIEW-PROSE-TOKENS.md`. Every finding they mark blocking is in scope; every finding they mark non-blocking needs an explicit decision to fix or to ticket, never a silent drop.

</domain>

<decisions>
## Implementation Decisions

### Gate correctness — the three fail-open shapes

- **D-01:** Repair the parsers that already exist in `check-alternatives.py`. Add no new predicate. This does not reopen Phase 23 D-01: D-01 froze the gate's *contract* against new checks, and a check that returns exit 0 for a document with no Alternatives Considered section is not enforcing the contract it already declares.
- **D-02:** Root cause of shape 1, refined 2026-09-07 by research that reproduced it: fenced spans (``` and ~~~) are already masked correctly, and a control fixture exits 1 as it should. The hole is the *4-space indented code block*, which the masker does not treat as code, so a section written inside one is read as prose and passes at exit 0. Mask indented code blocks on the same pre-pass that already masks fences, and leave the fence masking alone.
- **D-03:** Root cause of shape 3 (a cited requirement carried only on a nested sub-bullet passes at exit 0): `BULLET_RE` at line 115 accepts unbounded leading indentation. Bound it to the CommonMark top-level range, 0 to 3 spaces of indentation, so a nested sub-bullet no longer satisfies a top-level entry requirement.
- **D-04:** Root cause of shape 2 (a state document whose phase marker sits in unindented frontmatter passes at exit 0): the frontmatter parse at line 241 takes the first match while the body parse at lines 255-261 demands exactly one. Make both apply the same rule — exactly one match, with more than one reported as a named failure rather than silently resolved.
- **D-05:** Regression evidence, and the reason it is required before any of D-02 through D-04 is accepted: tightening a `blocking: true` gate with `onError: halt` can newly halt planning on documents that pass today. Corpus, established 2026-09-07: `gsd-beads` holds the only real planning corpus (96 documents, 9 of them plan-shaped); `sota-numerics` has no `.planning/` of its own, only the fixtures under `tests/.planning`. Sweep both — the real corpus and the fixture corpus — before and after the change. The only verdicts allowed to change are the three crafted fail-open fixtures. Any other changed verdict is a finding, not a pass.
- **D-06:** The three shapes become fixtures in the existing Python suite. This does not violate Phase 23 D-21: D-21 forbade test infrastructure for *prose*, and these are gate-behavior tests of the kind the suite already holds.

### Gate diagnostics

- **D-07:** Bound every diagnostic the gate emits. One failure path currently joins a whole entry span into a single line, measured at 8,099 tokens. A gate that reports a failure by flooding the context window defeats the purpose it was added for.
- **D-08:** The bounded shape follows the precedent the capability already documents (Phase 23 D-13): one `<plan_path>:<line>: <reason>` line per violation, any quoted span truncated with an explicit elision marker, then exactly one `remediation: ...` line for the run.

### Claims that do not resolve

- **D-09:** Hand-maintained counts are drift by construction. `CHANGELOG.md` line 12 reports 94/62/32 where HEAD has 97/62/35, and `check-alternatives.py` line 47 claims "76 entries across phase directories" where the live count is 73. Prefer deleting a count that no mechanism keeps true over correcting it to a value that will be stale again; keep a number only where something recomputes or checks it.
- **D-10:** `README.md` line 58 describes `__pycache__` handling the code does not implement, and line 93 references `draft-PLAN.md`, which does not exist. Correct or delete both, then re-run the Phase 23 D-20 claim trace over the whole README rather than only the lines Phase 23 touched — the trace missed these, so its coverage is the defect, not just the two claims.
- **D-11:** `favor`/`favour` drift inside one corpus: pick the spelling the rest of the corpus already uses, verified by count rather than assumed, and apply it corpus-wide.

### Cross-repo consistency

- **D-12:** The `sota-numerics` description in this repository's `.claude-plugin/marketplace.json` no longer matches the plugin manifest description on the branch. Update the marketplace entry to match, as its own commit in `gsd-beads`. Because the marketplace entry is what installers read, the two repositories must be consistent at the moment of merge, not afterwards.

### Security

- **D-13:** `hooks/gsd-tools.sh` lines 5-7 run `git rev-parse --show-toplevel` without `-C` and use the result to locate the node entry point, so a hostile repository in the invoking working directory gets code execution. It is byte-identical to `origin/main`, so it is pre-existing rather than introduced here — and it ships with 0.2.0, so it is fixed here. Resolve the entry point relative to the script's own location, not the caller's working directory.
- **D-14:** Scope is every site in the bundle that resolves a path from the caller's working directory, not the files that happen to be called hooks. Research found three: `hooks/gsd-tools.sh:5`, which `session-start.sh` and `capability-auto-install.sh` both source, so it is one fix point rather than three; and a third, previously unrecorded occurrence of the identical `git rev-parse --show-toplevel` pattern inside the gate `command` string in `capability.json`. The `capability.json` site is in scope: it is the same defect, in the same shipped bundle, reachable on the same lifecycle.

### Outstanding external review

- **D-15:** PR #4 carries roughly eight unanswered CodeRabbit threads, of which the duplicate `current_phase` parse is one; D-04 addresses that one's code. Triage every open thread, not just the named one: each gets either a fix, a reply stating why the finding does not hold, or its own bd ticket. None is dropped for being minor. An unanswered bot finding on a publish PR is an open question, not a closed one.
- **D-16:** Publish ordering is unchanged from Phase 23 D-26. Every fix in this phase lands on the branch before external review runs again. PR #4 stays open and is treated as a known-incomplete diff until this phase verifies.

### Execution hazard specific to this phase

- **D-17:** Editing the bundle in `.worktrees/sota-numerics-release-013` changes its bundle hash, and the in-tree plugin's `SessionStart` and `SubagentStart` hooks then install the *uncommitted* bundle to the global mirror via `capability-auto-install.sh`. Verified 2026-09-07: `hooks/hooks.json` matches `startup|resume|clear|compact` plus the three GSD subagents, and the script has no opt-out env var. The effect is local to this machine and is not a publish, so it is accepted rather than prevented — but it is made visible: record `~/.gsd/capability-auto-install-sota-numerics.hash` before and after each plan, and restore the mirror from the released plugin-cache bundle when the phase ends.
- **D-18:** Rejected alternative — move the worktree outside the project tree so Claude Code never loads it as a plugin. The project rule requires worktrees to stay under the project root, and relocating the checkout to dodge a hook is a workaround whose cost lands on every later session that expects the worktree where the rule puts it.

### Publish

Phase 23 A-04 moved the publish here, because a later phase gating an earlier phase's last wave is a dependency GSD's ascending phase order cannot express. The first three decisions below are Phase 23's D-25, D-26 and D-27, restated as this phase's, unchanged in substance.

- **D-19:** The marketplace entry points at the repository URL rather than at a tag, so merging to `main` is the publish. There is no separate release step: everything that must be true of a release must be true before the merge.
- **D-20:** Publish ordering. Internal review and every fix it accepts land on the branch before the pull request opens. CI must be green on the exact commit that reaches `main`. Any claim the release makes about behavior traces to code, not to an assertion in the pull request body.
- **D-21:** Tag the published commit `v0.2.0`. `0.1.3` left no immutable marker for what was served.
- **D-22:** The publish is the final wave of this phase and is guarded by a `checkpoint:decision` task, exactly as 23-05 Task 2 was. That checkpoint's first answer, recorded 2026-09-07, was `hold`. It is re-asked after the remediation waves verify and answered fresh — a prior `hold` is not carried forward as a standing no, and it is not treated as spent either.
- **D-23:** Reuse the existing bd issues rather than creating new ones: `gsd-beads-sac.14` for the decision checkpoint, `gsd-beads-sac.15` for push, pull request, CI and merge, `gsd-beads-sac.16` for the tag. Carry those exact `<beads-id>` values into the corresponding tasks of this phase's publish plan. The `hold` answer and its findings are already comments on `.14`; a fresh issue would orphan that record.

### Phase exit

- **D-24:** This phase ends at published `0.2.0` with the commit tagged, or at a second recorded `hold` — not at "remediation done".

### Claude's Discretion

- Exact regex construction for D-02 through D-04, provided D-05's evidence holds.
- Exact truncation width for D-08.
- Which counts in D-09 are deleted and which are kept with a mechanism.
- Commit granularity within the branch.
