# Phase 16: beads-issue-content-parity - Context

**Gathered:** 2026-08-19
**Status:** Ready for planning

<domain>
## Phase Boundary

`bd` becomes the actual source of truth for task WHAT/HOW, not just a status tracker pointing
at `PLAN.md`. This closes the gap between PROJECT.md's stated Core Value ("gsd's lifecycle
writes to and reads from `bd` exclusively for task state; zero duplicated task-state
bookkeeping survives in `.planning/`") and the current implementation, where `bd create` runs
with no `--description` (`sync.py::resolve_issue`), every synced issue is a title-only stub,
and `PLAN.md` — not `bd` — is what `gsd-executor` actually reads at execution time. The
operator's framing: "the current version has the source of truth exactly opposite of what was
intended."

This phase does three things, in order of dependency:
1. Makes new task creation write a real, complete description to `bd` (not just a title).
2. Flips `gsd-executor`'s read path (for `auto`/`tracer` tasks only) from `PLAN.md`'s `<task>`
   blocks to `bd show` — requiring a machine-local patch to gsd-core's `execute-plan.md`,
   filed upstream, same pattern as the existing `ship.md` generic-gate-dispatch patch.
3. Root-causes and fixes why `close_wave()` stopped closing issues after wave 1 of Phase 14's
   historical execution (2/6 closed, 4/6 stuck open despite all three waves being fully
   committed) — then closes those 4 stale issues as live proof the fix works.

Scope is forward-only: this phase does not touch Phases 1-15's already-shipped `PLAN.md` files
or backfill their already-closed bd issues' descriptions.

</domain>

<decisions>
## Implementation Decisions

### Inversion depth and mechanism
- **D-01: True full inversion — `bd` is the source, `PLAN.md` becomes a pointer for `auto`/`tracer` tasks.** After sync, `gsd-executor` reads a task's `<objective>`/`<action>`/`<verify>`/`<acceptance_criteria>` content from `bd show <task-id>`, not from `PLAN.md`'s `<task>` block. `PLAN.md` retains only `<name>` and `<beads-id>` per task (identity-binding anchor, unchanged mechanism — B4/B5's resolve-by-id-never-title still applies). — **Reversibility:** costly — undoing this means re-inflating every stripped `PLAN.md` task block from `bd` content and reverting the gsd-core patch; not a data-loss risk (content lives in `bd`), but touches the executor contract every future phase runs on.
- **D-02: Plan-level content stays in `PLAN.md`.** Only *per-task* content (`<objective>`, `<action>`, `<verify>`, `<acceptance_criteria>`, `<read_first>`, `<precondition>`, `<done>`) moves into that task's `bd` description. Plan-level sections that have no natural per-task home — `<threat_model>`, `<alternatives_considered>`, `<success_criteria>`, `<context>` — stay in `PLAN.md` exactly as today. `gsd-executor` reads task detail from `bd`, plan-level context from `PLAN.md`, for the same plan.
- **D-03: Checkpoint tasks are excluded from the inversion.** `type="checkpoint:decision"`/`"checkpoint:human-verify"` tasks (the blocking-approval tasks — e.g. Phase 15's public-repo-push gates) keep their full structure — options, pros/cons, reversibility ratings, resume-signal — in `PLAN.md`, unchanged. Only `type="auto"` and `type="tracer"` tasks invert. Rationale: checkpoint structure doesn't compress cleanly into a `bd` description read at execute time, and checkpoints are inherently interactive (`AskUserQuestion`-driven) — the read-from-bd model doesn't fit that shape.
- **D-04: bd-unreachable at execute time is a hard failure, stated plainly.** If `bd show` fails for a task `gsd-executor` needs to read, the executor halts with a clear error naming the missing/unreachable issue. This is a genuine NEW hard dependency — unlike B6's existing degrade-to-no-op-with-notice pattern (which applies to `bd` sync/status operations, not task content retrieval) — because execution literally cannot proceed without knowing what to do. Do not paper over this with a `PLAN.md` fallback (that would require `PLAN.md` and `bd` to stay in sync forever, defeating D-01's whole point).

### Upstream patch strategy
- **D-05: File the gsd-core patch upstream immediately; run the local patch until merged.** Same pattern as the `ship.md` generic-gate-dispatch patch already in use (unmerged, upstream issue filed, every phase that depends on it re-verifies the patch marker is present before trusting it — never assumes merged). Do not defer the upstream conversation. — **Reversibility:** reversible — the local patch itself is a small diff to a machine-local copy; filing upstream is a one-time action with no lock-in.

### Backfill and migration scope
- **D-06: Forward-only backfill.** Fix `sync.py::resolve_issue`/`resolve_or_create_epic` so all NEW task/epic creation from this point forward writes a real `--description`. The ~40 already-closed historical issues from Phases 1-15 stay title-only. Do not write a backfill script for closed history.
- **D-07: Forward-only migration.** Only phases *planned after* this change get the `PLAN.md`-becomes-pointer treatment (D-01). Phases 1-15's `PLAN.md` files are not rewritten retroactively — they stay exactly as committed, full content, untouched.

### Stale-issue root cause (Phase 14 regression)
- **D-08: Root-cause the `close_wave()` gap, fix it, and close the 4 stale issues as proof.** Evidence gathered during discussion: Phase 14's epic (`gsd-beads-bu0`) shows 2/6 tasks closed (wave 1: `gsd-beads-bu0.1`, `.2`) and 4/6 still open (`gsd-beads-bu0.3`, `.4`, `.5`, `.6` — waves 2 and 3) despite `git log` confirming all three waves were fully committed (`14-02`, `14-03` commit subjects present, matching `close_wave()`'s `find_completed_task_ids` grep pattern). `close_wave()` fires from the `execute:wave:post` beads-status hook; something broke that dispatch after wave 1 in that historical session — this phase's research step should investigate git history around that session (worktree/fork-base issues are the leading hypothesis, per the same class of problem hit and fixed during Phase 15's execution — see `15-CONTEXT.md`/`15-01-SUMMARY.md` for the `#683` fork-base-divergence pattern). Not a design decision to make here — flagging for `gsd-phase-researcher` to investigate and `gsd-planner` to scope a fix task around. — **Reversibility:** reversible — closing 4 already-complete issues is a pure bookkeeping correction with no code dependency.

### Claude's Discretion
- Exact `bd` description markdown formatting (how `<objective>`/`<action>`/`<verify>`/`<acceptance_criteria>` XML-ish PLAN.md tags render as clean bd-description markdown) — Claude decides during planning, following the existing `_write_report`-style "one place writes the shape" discipline already established in `sync.py` and the two extracted capability scripts.
- Whether the gsd-core patch to `execute-plan.md` is a single unified diff or split into a read-path change plus a separate `PLAN.md`-stripping-at-sync change — Claude decides during planning based on what's independently testable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current sync/bd-creation mechanism (what's being changed)
- `.gsd/capabilities/beads/scripts/sync.py` — `resolve_issue()` (line ~615, `bd create` call with no `--description`), `resolve_phase_epic()`/`resolve_milestone_epic()` (line ~510-561, same gap at epic level), `parse_plan()` (line ~142, current task-dict shape: `name`/`name_end`/`beads_id`/`files` only — no content fields), `close_wave()` (line ~784, the hook this phase must root-cause)
- `.gsd/capabilities/beads/tests/test_sync.py` — existing test patterns for `resolve_issue`/`resolve_epic`, to extend rather than replace

### Executor read path (what gets inverted)
- `$HOME/.claude/gsd-core/workflows/execute-plan.md` (558 lines) — the gsd-core file that needs the machine-local patch; read in full before proposing the patch shape
- `$HOME/.claude/gsd-core/workflows/execute-phase/steps/regression-gate.md` and sibling step files — for how gsd-core step files are conventionally patched/referenced, matching the `ship.md` precedent's style

### Upstream patch precedent (pattern to replicate)
- `$HOME/.claude/gsd-core/workflows/ship.md` — search for `gsd-beads-patch:ship-pre-generic-dispatch v1` marker; this is the exact machine-local-patch-plus-upstream-filing pattern D-05 replicates
- ROADMAP.md's "Cross-Cutting Constraints (v1.2)" section — "Verify the patch before trusting any gate" — the re-verify-every-time discipline D-05 must also follow

### Fork-base divergence precedent (for D-08's root-cause investigation)
- `.planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-CONTEXT.md` and `15-01-SUMMARY.md` — the `#683` worktree fork-base-divergence class of bug hit and fixed during this session's Phase 15 execution; leading hypothesis for D-08's root cause
- `$HOME/.claude/gsd-core/workflows/execute-phase.md` — "Resolve ISOLATION" section, `worktree.baseRef` config, `gsd_run worktree set-baseref` — the actual fix mechanism if the hypothesis holds

### Project-level constraints
- `.planning/PROJECT.md` — "no fork and no patch to gsd-core itself" is the locked constraint D-05's machine-local-patch-with-upstream-filing exception must satisfy, not violate
- `.planning/ROADMAP.md` Phase 16 section — the original two-option framing (minimal fix vs. full inversion) this discussion resolved in favor of full inversion

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `sync.py::run_bd()` — the existing subprocess wrapper for all `bd` CLI calls; the new `--description`-carrying `bd create` calls route through this, no new subprocess-handling code needed
- `sync.py::confined()`-style path-confinement pattern (also used in both extracted capability scripts, `lint.py`/`pr_status.py`) — apply the same discipline if the description-writing code needs to resolve any file paths
- `close_wave()`'s existing `find_completed_task_ids()` — already does the git-log-grep-by-task-id matching; D-08's fix likely extends or repairs this function's caller chain, not the matching logic itself

### Established Patterns
- **Machine-local gsd-core patch + upstream filing + every-run re-verification** — `ship.md`'s `gsd-beads-patch:ship-pre-generic-dispatch v1` marker is the direct precedent for D-05; copy its verification-before-trust discipline exactly (grep for the marker, count it, never assume merged).
- **One place writes the shape** — `_write_report()` in both `lint.py` and `pr_status.py` (Phase 15's post-review fixes) is the established discipline for "every writer of a generated artifact goes through one function so escaping/shape can't drift" — apply the same discipline to whatever function renders `PLAN.md` task content into a `bd` description.
- **Resolve-by-id-never-title (B4/B5)** — `resolve_issue()`'s `<beads-id>` check is unchanged by this phase; D-01 only moves WHAT gets read once the ID resolves, not HOW identity resolves.

### Integration Points
- `sync.py`'s task-creation path (`resolve_issue`) is the single write point for D-01/D-06.
- gsd-core's `execute-plan.md` task-read path is the single read point for D-01 (on the executor side) — needs the machine-local patch.
- `close_wave()`'s hook dispatch (`execute:wave:post`) is the integration point for D-08.

</code_context>

<specifics>
## Specific Ideas

No specific UI/UX references — this is an internal tooling/data-model phase. The operator's core
framing to hold onto throughout planning: "the current version has the source of truth exactly
opposite of what was intended" — every decision above optimizes for closing that specific gap,
not for generic sync-robustness improvements beyond it.

</specifics>

<deferred>
## Deferred Ideas

- **Retroactive backfill of Phases 1-15's bd issue descriptions** — deferred by D-06 (forward-only). Could become its own future phase/todo if historical `bd show` completeness is later needed for an audit or migration.
- **Retroactive `PLAN.md` stripping for Phases 1-15** — deferred by D-07 (forward-only migration), same reasoning as above.

### Reviewed Todos (not folded)
None — no pending todos matched Phase 16 (`todo.match-phase` returned 0 matches).

</deferred>

---

*Phase: 16-beads-issue-content-parity*
*Context gathered: 2026-08-19*
