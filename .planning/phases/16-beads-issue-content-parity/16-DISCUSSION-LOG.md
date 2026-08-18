# Phase 16: beads-issue-content-parity - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-19
**Phase:** 16-beads-issue-content-parity
**Areas discussed:** Inversion mechanism, Backfill scope, Description content shape, Stale Phase 14 tasks, bd-unreachable fallback, PLAN.md migration scope, task-content shape, Upstream patch strategy, Checkpoint task handling

---

## Inversion mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Bd becomes richly self-sufficient, PLAN.md stays the read path | sync.py writes full description to bd; gsd-executor keeps reading PLAN.md; zero gsd-core patch | |
| True full inversion — gsd-executor reads from bd | PLAN.md becomes a title+beads-id pointer after sync; gsd-executor fetches task content via `bd show`; requires machine-local patch to gsd-core's execute-plan.md | ✓ |

**User's choice:** True full inversion.
**Notes:** Matches planning-with-beads' own model, the project's original inspiration. Operator's framing: "the current version has the source of truth exactly opposite of what was intended" — the recommended lower-risk option was explicitly declined in favor of the harder, correct fix.

---

## Backfill scope

| Option | Description | Selected |
|--------|-------------|----------|
| Forward-only | Fix sync.py for new task creation only; leave ~40 already-closed historical issues title-only | ✓ |
| Backfill everything | One-shot script patches every closed issue's description from its archived PLAN.md source | |

**User's choice:** Forward-only.

---

## Stale Phase 14 tasks

| Option | Description | Selected |
|--------|-------------|----------|
| Root-cause fix + backfill-close as part of Phase 16 | Find why close_wave stopped firing after wave 1, fix it, close the 4 issues as evidence | ✓ |
| Just close them now, investigate separately | Manual close immediately, file a separate ticket for root cause | |

**User's choice:** Root-cause fix + backfill-close, bundled into Phase 16.
**Notes:** Evidence gathered live during discussion: Phase 14's epic (gsd-beads-bu0) has 2/6 tasks closed (wave 1) and 4/6 still open (waves 2-3), despite `git log` confirming all three waves were fully committed. Leading hypothesis: same class of worktree/fork-base-divergence issue (#683) hit and fixed during this session's Phase 15 execution.

---

## Bd-unreachable fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Hard fail, surface clearly | Executor halts with a clear error naming the missing bd issue | ✓ |
| Fall back to PLAN.md if still present | Keep PLAN.md content as cold-standby fallback | |

**User's choice:** Hard fail, surface clearly.
**Notes:** A fallback would require PLAN.md and bd to stay in sync forever, undermining the whole point of the inversion.

---

## PLAN.md migration scope

| Option | Description | Selected |
|--------|-------------|----------|
| Forward-only, matches backfill decision | Only new phases get the pointer treatment; Phases 1-15's PLAN.md files stay untouched | ✓ |
| Strip everything retroactively | Rewrite all existing PLAN.md files down to pointers too | |

**User's choice:** Forward-only.

---

## Description/task-content shape

| Option | Description | Selected |
|--------|-------------|----------|
| Per-task content moves, plan-level stays | Each task's objective/action/verify/acceptance-criteria becomes its bd description; plan-level sections (threat model, alternatives considered) stay in PLAN.md | ✓ |
| Everything moves, PLAN.md becomes near-empty | Plan-level sections also get distributed into task descriptions or an epic-level description | |

**User's choice:** Per-task content moves, plan-level stays.

---

## Upstream patch strategy

| Option | Description | Selected |
|--------|-------------|----------|
| File upstream immediately, run local patch until merged | Same pattern as the ship.md gate-dispatch patch — open a PR/issue now, re-verify the patch marker every run | ✓ |
| Local-only for now, file upstream later | Defer the upstream conversation | |

**User's choice:** File upstream immediately, run local patch until merged.

---

## Checkpoint task handling

| Option | Description | Selected |
|--------|-------------|----------|
| Checkpoints stay in PLAN.md, only auto tasks invert | checkpoint:decision/human-verify tasks keep their full interactive structure in PLAN.md | ✓ |
| Checkpoints invert too | Full consistency — every task type reads from bd | |

**User's choice:** Checkpoints stay in PLAN.md, only auto/tracer tasks invert.

---

## Claude's Discretion

- Exact bd description markdown formatting (how PLAN.md's XML-ish task tags render as clean bd-description markdown).
- Whether the gsd-core patch is a single unified diff or split into a read-path change plus a PLAN.md-stripping-at-sync change.

## Deferred Ideas

- Retroactive backfill of Phases 1-15's bd issue descriptions.
- Retroactive PLAN.md stripping for Phases 1-15.
