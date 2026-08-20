# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — milestone

**Shipped:** 2026-08-16
**Phases:** 4 | **Plans:** 11 | **Sessions:** 1 (continuous, across a `/clear` boundary)

### What Was Built
- A `bd`-backed task substrate: every `PLAN.md` task syncs to an idempotent, dependency-ordered beads issue bound by explicit `<beads-id>`, closing itself on task completion and degrading to a fail-open no-op whenever `bd` is unavailable (Phase 1)
- Live visibility for the planner and executor: `BEADS-RECALL.md` at `plan:pre`, a regenerated `BEADS.md` and composed `<beads_status>` block at `execute:wave:pre/post` (Phase 2)
- A real ship gate: `ship:pre` blocks on `blocking_open`/`diverged`, with a recorded override path — including a machine-local patch to gsd-core's `ship.md` to make third-party `ship:pre` gates actually dispatch (Phase 3)
- Adoption tooling: one-shot todo migration, on-demand `beads-status` mapping with orphan detection on both sides, and a `beads.epic_per=milestone` option (Phase 4)

### What Worked
- The fail-open discipline (B6/D-08) proved itself for real: `bd`'s genuine schema-version skew (v65 DB vs v53 binary) silently degraded every sync attempt across Phases 1-4 without ever blocking a phase — exactly the invariant it was built to guarantee, discovered working as designed rather than by crash.
- Tracer-first planning consistently avoided rework: in all three Phase 4 plans, the tracer task's own `<behavior>` spec already required the logic a later "hardening" task's dedicated regression test re-asserted — zero fix commits needed across 6 tasks.
- The spec-less probe fallback (edge-probe + prohibition-probe) surfaced two genuine bespoke prohibitions for Phase 4 (B13's read-only guarantee, B14's forward-only epic guard) that became actual `must_haves.prohibitions` entries and were later confirmed as STRIDE threats — the adversarial-recall step earned its keep.
- Cross-checking a subagent's self-report against source directly (code-review findings, integration-checker's capability.json claim) caught nothing wrong this milestone, but the discipline of verifying before trusting stayed cheap and is worth keeping.

### What Was Inefficient
- `bd`'s real unavailability (schema skew) went undiagnosed for the first three phases plus part of Phase 4 — every "bd unavailable" message was accurate but nobody investigated whether it was a genuine environment gap or a real, fixable problem until a human asked directly. The fail-open design correctly prevented any phase from blocking on it, but it also meant nothing forced an investigation.
- Phase 4's three SUMMARY.md files were written without the `requirements-completed` frontmatter field every prior phase's summaries carried — a manual-fallback gap the milestone audit's 3-source cross-reference had to route around.
- Two phases (02, 04) seeded a `VALIDATION.md` at plan time that was never reconciled by `/gsd-validate-phase`, and Phase 03 never got one at all — Nyquist coverage was tracked in spirit (every task had automated verifies) but never formally closed out.

### Patterns Established
- **Live-trace over trust**: when the real tool becomes available mid-project, prefer a genuine round-trip (create/read/close against the actual database) over accepting mocked-test evidence alone for a UAT pass — caught nothing wrong this time, but is now the standard for any phase that touches an external system with a real instance reachable.
- **Verify subagent findings against source before acting**: every code-review, integration-check, and audit finding this milestone was independently re-confirmed via direct file reads before being accepted or acted on (fixed, dismissed, or logged) — zero false positives shipped, one real bug (capability.json `produces` mismatch) caught and fixed same-session.

### Key Lessons
1. A capability's own SUMMARY.md/VERIFICATION.md metadata (like `requirements-completed` frontmatter) is itself part of the deliverable — omitting it doesn't break functionality, but it breaks the milestone audit's automated cross-reference and forces a manual fallback every time.
2. "Unavailable" and "broken but fixable" look identical from inside a fail-open system by design — that's the point of fail-open, but it means periodic real-environment investigation (not just trusting the skip message) is still worth doing, especially before a milestone close.
3. A machine-local patch to upstream tooling (the `ship.md` ship:pre dispatch gap) is a legitimate, in-scope fix when upstream can't move fast enough — but it needs its own self-detecting diagnostic (`check-shipmd-patch`) so a future update silently dropping the patch doesn't go unnoticed.

### Cost Observations
- Model mix: 0% opus, ~90% sonnet (planner/executor/verifier/reviewer/fixer/secure-phase all ran sonnet), ~10% haiku (integration-checker only)
- Sessions: 1 continuous session (across a `/clear` boundary)
- Notable: three subagent-reported "regressions" (4 pytest failures reported by the code-fixer) turned out to be transient test-isolation flakiness on independent re-run (88/88 clean) — worth a standing habit of one clean re-run before accepting a "pre-existing flakiness" claim, which is what happened here.

---

## Milestone: v1.2 — New Capability Plugins

**Shipped:** 2026-08-19
**Phases:** 4 (13-16) | **Plans:** 16 | **Sessions:** spans 2026-08-18 → 2026-08-19, 107 commits

### What Was Built
- `markdown-linting` capability: `rumdl`-backed `.planning/` quality gate, advisory `ship:pre`, 488/489 pre-existing violations fixed mechanically (Phase 13)
- `pr-workflow` capability: `gh`-backed PR check-status gate, advisory `ship:pre`, fails open across every `gh`-degraded state (Phase 14)
- Both capabilities extracted to independent public repos and marketplace entries, dogfood copies removed from this repo, CI green (Phase 15)
- Beads issue content parity: every `bd create` for a task/epic now carries a real description/acceptance criteria; `gsd-executor` reads `auto`/`tracer` task instructions from `bd show`, hard-halting on an unreachable bd; a phase-wide `reconcile-stale-closed` backstop closes issues left open by per-wave dispatch (Phase 16)

### What Worked
- Live-recorded proof over narrated confidence, again: Phase 13/14/15 all reproduced their gate behavior via a real `gsd_run check predicate` smoke test against synthetic or installed-copy artifacts rather than trusting "the manifest declares `gates[]`" — carried forward from v1.0's established pattern.
- Mid-milestone scope reallocation: when Phase 16 (beads issue content parity) was discovered as a real, higher-priority gap, `get-available-resources` was cleanly dropped rather than force-fit — a scope change made explicit in ROADMAP.md/PROJECT.md rather than silently absorbed.
- UAT-verifying live mechanism instead of accepting "patch text installed" as sufficient: Phase 16's UAT built a throwaway bd fixture and simulated a real bd-unreachable failure rather than treating byte-verified patch text as proof of runtime behavior.

### What Was Inefficient
- Phase 16 was folded into the v1.2 milestone via a `### Phase 16` ROADMAP.md section that was never added to the milestone's own header/bullet list (`### v1.2 New Capability Plugins (Phases 13-15)`) or moved ahead of the `## Cross-Cutting Constraints (v1.2)` section — whose heading incidentally contains the literal token `v1.2` and was misread by `extractCurrentMilestone`'s stop-boundary scan as the next milestone marker, silently truncating Phase 16 out of every milestone-scoped query (`init.manager`, `/gsd-complete-milestone`'s readiness check) until caught at milestone-close time. Cost: one extra investigation-and-fix cycle immediately before archival that phase-registration discipline would have avoided entirely.
- A diagnosed-but-unresolved debug session (`readme-beads-value-prop`, root cause confirmed, fix already shipped in an earlier commit) sat in `status: diagnosed` instead of `status: resolved` and blocked the pre-close artifact audit — the underlying README fix had landed correctly, but the session bookkeeping wasn't closed out when it did.
- v1.1's milestone completion never wrote a retrospective section (this file jumps from v1.0 straight to v1.2) — a gap in this project's own closeout discipline, not something this milestone can retroactively fix without fabricating data.

### Patterns Established
- **Register new mid-milestone phases in the milestone header, not just as a standalone `### Phase N` section** — every milestone-scoped tool (readiness checks, archival) reads the header/bullet-list range, not just the presence of a phase heading anywhere in the file.
- **Close diagnosed debug sessions when their fix ships**, even if the fix landed via a separately-authored commit rather than the debug session's own `next_action` — the artifact audit gate treats `diagnosed` as still-open regardless of whether the underlying problem is actually fixed.

### Key Lessons
1. A milestone-scoped ROADMAP.md parser that stops at the next heading matching a version-like token is a real footgun for any other heading that incidentally contains that token (e.g. `## Cross-Cutting Constraints (v1.2)`) — phase detail sections belong before summary/constraints sections, not after, purely to stay inside the parser's section boundary.
2. "Fix shipped" and "tracking artifact closed" are two different facts — a debug session, UAT gap, or similar tracking record needs its own explicit closure step even when the underlying code fix happens to land through unrelated work.
3. UAT for an internal-mechanism change (not a user-facing feature) can still be meaningfully live-verified without a full end-to-end harness run — testing the actual branch-trigger conditions (a real `bd show` success/failure, a real empty-description issue) against genuine `bd` state is stronger evidence than a synthetic mock, even short of a full `gsd-executor` session.

### Cost Observations
- Sessions: spans at least 2 UTC days (2026-08-18 start, 2026-08-19 ship), 107 commits across the milestone range
- Notable: milestone close itself required two structural fixes (ROADMAP.md phase-registration, a stale debug-session closure) before archival could proceed — both were pre-existing gaps surfaced by the close workflow's own gates working as intended, not new defects introduced by closing

---

## Milestone: v1.3 — Config/Code Truth

**Shipped:** 2026-08-20
**Phases:** 2 (17-18) | **Plans:** 8 | **Sessions:** at least 2 (Phase 17 execution, then a
second continuous session covering Phase 18, a follow-up quick task, both phases' security gate,
and milestone close)

### What Was Built
- TRUTH-04: decimal-numbered phases (`1.5`, `11.1`) resolve at every beads lifecycle point via
  string-only helpers — closed a P1 bug that was failing silently on every hook (Phase 17)
- TRUTH-03: `check_native_step_dispatch` gates the double-dispatch hook on live probing of the
  installed gsd-core workflow files, not a version guess — self-adapts the moment upstream #3687
  releases (Phase 17)
- TRUTH-01: `beads.sync_mode` narrowed to two behaviorally-distinct values; a project holding the
  retired `off` value gets exactly one silent notice, never a crash or a config write (Phase 17)
- TRUTH-02: two structurally-cloned patch-check functions collapsed into one `PATCH_CHECKS`-table
  reader behind one CLI verb, D-08 hard break with no alias window (Phase 17)
- Both machine-local gsd-core patches reapplied and verified live on both runtime homes; the
  withdrawn `v1.3.0` tag deleted from `origin` behind a live-confirmed `checkpoint:decision`; four
  stale Phase 17 bd issues closed with verified identity; CHANGELOG/`plugin.json` accuracy gaps
  closed (Phase 18)
- Follow-up quick task: `reconcile_stale_closed` extended with an opt-in `resolves_issues:`
  SUMMARY.md frontmatter marker so standalone problem-report bd issues (no `<beads-id>`) can be
  closed by the phase-wide backstop too — closing the exact gap Phase 18 surfaced about itself

### What Worked
- Live-reverifying every `mitigate`-dispositioned threat at security-gate time, not just trusting
  each plan's own threat-model prose: for Phase 18's 17-threat register, every high-severity claim
  (patch markers present, tag actually gone from origin, `bd show` confirms closure, `diff -rq`
  empty between tracked/overlay trees) was re-run live against the current `HEAD`, not accepted
  from a SUMMARY.md's self-report.
- Pinning every `bd` invocation inside an isolated executor worktree to `-C <main-repo-root>`
  before dispatch, once the worktree/`.beads/` gap was diagnosed — caught a correctness bug (an
  isolated worktree cannot see the untracked, gitignored `.beads/` database) before any bd state
  was silently mutated against a stale/absent local copy instead of the real project database.
- Treating a genuinely destructive, checkpoint-gated operation (deleting a public git tag) as a
  real decision point even though the plan itself recommended an option — surfaced it via
  `AskUserQuestion` rather than auto-approving the plan's own recommendation, consistent with
  "hard-to-reverse, affects shared state" always warranting explicit confirmation regardless of
  which option a subagent argues for.

### What Was Inefficient
- A Claude Code worktree got torn down by the harness mid-checkpoint (between a plan pausing at
  `checkpoint:decision` and being resumed with the answer), losing the in-progress worktree state
  for plan 18-02's Task 3. Recovery required the orchestrator to manually recreate the worktree at
  the same base/branch before resuming — the checkpoint-pause protocol does not currently protect
  against harness-side worktree cleanup firing on a paused (not actually finished) agent.
- The `gsd-write-guard.js` shrink-protection hook's documented escape hatch (a single-use
  `.gsd-allow-shrink` sentinel file, armed by the workflow before the milestone-close ROADMAP.md
  rewrite) failed three times in a row during this milestone's close. Root cause: **two copies of
  the hook are both registered** (a user-level install and a marketplace-plugin install), and the
  sentinel is single-use — the first hook instance to run consumes it, so the second instance always
  finds it already gone and blocks. The documented workaround (Edit instead of Write, after a full
  Read) works and was used, but the sentinel mechanism itself is silently broken for any project
  with both hook copies registered, and nothing surfaces that duplication to the user.
- `.gsd-capabilities.json`'s `updatedAt` timestamp kept drifting into a merge conflict on nearly
  every worktree merge and cross-session sync this milestone (stash-and-drop was the workaround
  each time) — pure bookkeeping noise with no semantic content, but it cost a manual stash/drop
  cycle on at least four separate merges across Phase 18 and this close.

### Patterns Established
- **Re-verify high-severity threat mitigations live at the security gate, independent of the
  executor's own SUMMARY.md claim** — this milestone's `asvs_level: 1` short-circuit rule still
  means "grep-depth," not "trust the report"; every `mitigate` disposition at `high` severity got
  an independent command re-run before being marked closed.
- **`-C <main-repo-root>` for every `bd` call inside an isolated executor worktree** — `.beads/` is
  untracked and a `git worktree add` checkout never contains it; any plan whose real work is bd
  state (not repo files) needs this pinning or it silently operates on an absent/stale database.

### Key Lessons
1. A checkpoint pause is not the same as agent completion from the harness's perspective — a
   worktree can be reclaimed between a plan pausing at `checkpoint:decision` and being resumed with
   the user's answer. Treat "worktree missing on resume" as an expected, recoverable orchestrator
   task (recreate at the recorded base/branch), not a fatal error.
2. A single-use escape-hatch sentinel is only as reliable as the assumption that exactly one
   consumer will check it. Two registered copies of the same hook silently defeats a single-use
   token every time, with no error pointing at the actual cause — worth auditing for duplicate hook
   registration (`~/.claude/hooks/` vs. `~/.claude/plugins/marketplaces/*/hooks/`) whenever a
   documented single-use bypass mysteriously never works.
3. Deleting a public git tag (or any destructive operation against shared/external state) still
   needs explicit human confirmation even when the executing plan already argues for a specific
   option — a plan's own recommendation is not the same as the user's consent.

### Cost Observations
- Model mix: security-gate re-verification and milestone archival ran on the orchestrator directly
  (no subagent spawn needed for either); phase execution used sonnet executors/verifiers, opus for
  the quick-task planner and the security auditor role (unused this pass — `asvs_level: 1`
  short-circuited both phases' auditor spawn)
- Sessions: Phase 17 in one session; Phase 18 + quick task 260820-j6g + both phases' security gate
  + this milestone close in one continuous second session
- Notable: the worktree-recreation recovery for plan 18-02 and the write-guard sentinel workaround
  for ROADMAP.md were both real, in-session recoveries from genuine tooling gaps — neither was a
  planning or execution defect in this milestone's own deliverables

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 1 | 4 | First milestone — established the overlay-capability pattern, fail-open discipline, and tracer-first planning for this project |
| v1.1 | — | 8 (5-12) | Not recorded — this milestone's retrospective section was never written at close time |
| v1.2 | 2+ days | 4 (13-16) | First milestone to ship independent public plugins extracted from in-repo dogfood, and the first mid-milestone scope reallocation (get-available-resources dropped for a higher-priority discovered gap) |
| v1.3 | 2+ (1 day) | 2 (17-18) | First milestone with a mid-milestone tech-debt phase inserted after the requirement-scoped phase shipped (Phase 18, audit-sourced, no REQUIREMENTS.md IDs), and the first to hit real harness/tooling gaps (worktree reclaimed mid-checkpoint, duplicate-hook sentinel) rather than planning or execution defects |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|---------------------|
| v1.0 | 88 | Not measured (no coverage tool configured) | 0 (N5: `bd` binary + Python stdlib only, no new dependency added) |
| v1.2 | 4/4 phases verification `passed` | Not measured (no coverage tool configured) | 0 (`markdown-linting`/`pr-workflow` wrap external CLIs already required, no new project dependency) |
| v1.3 | 2/2 phases verification `passed`, 261/261 suite (up from 246 at Phase 17 start) | Not measured (no coverage tool configured) | 0 (both phases and the follow-up quick task stayed within `bd` + Python stdlib) |

### Top Lessons (Verified Across Milestones)

1. Fail-open correctly hid a real, fixable problem (bd schema skew) for most of the milestone — the design worked exactly as intended, but "no error" isn't the same as "everything is fine"; worth a periodic real-environment check, not just trusting the skip path. (v1.0)
2. Tracking artifacts (debug sessions, UAT gaps, milestone headers) need their own explicit closure step — a shipped fix or a phase's existence in the file doesn't automatically close the record that references it. (v1.2)
3. A worktree-isolated executor cannot see untracked project state (`.beads/`), and a checkpoint pause is not the same as agent completion to the harness — both need an explicit, documented recovery path rather than being discovered fresh each time. (v1.3)
