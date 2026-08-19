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

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 1 | 4 | First milestone — established the overlay-capability pattern, fail-open discipline, and tracer-first planning for this project |
| v1.1 | — | 8 (5-12) | Not recorded — this milestone's retrospective section was never written at close time |
| v1.2 | 2+ days | 4 (13-16) | First milestone to ship independent public plugins extracted from in-repo dogfood, and the first mid-milestone scope reallocation (get-available-resources dropped for a higher-priority discovered gap) |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|---------------------|
| v1.0 | 88 | Not measured (no coverage tool configured) | 0 (N5: `bd` binary + Python stdlib only, no new dependency added) |
| v1.2 | 4/4 phases verification `passed` | Not measured (no coverage tool configured) | 0 (`markdown-linting`/`pr-workflow` wrap external CLIs already required, no new project dependency) |

### Top Lessons (Verified Across Milestones)

1. Fail-open correctly hid a real, fixable problem (bd schema skew) for most of the milestone — the design worked exactly as intended, but "no error" isn't the same as "everything is fine"; worth a periodic real-environment check, not just trusting the skip path. (v1.0)
2. Tracking artifacts (debug sessions, UAT gaps, milestone headers) need their own explicit closure step — a shipped fix or a phase's existence in the file doesn't automatically close the record that references it. (v1.2)
