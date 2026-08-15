# Phase 3: Enforcement - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-15
**Phase:** 3-Enforcement
**Areas discussed:** blocking_open definition, Divergence detection, Override audit trail, Divergence report shape

---

## blocking_open definition

| Option | Description | Selected |
|--------|-------------|----------|
| Every open issue under the phase epic | Simplest, matches B9's literal wording, no priority/type filtering | ✓ |
| Only P0/P1 priority issues | Requires bd priority field reliably set, adds a config knob | |
| You decide | Let planner/researcher pick based on bd's priority field support | |

**User's choice:** Every open issue under the phase epic

**Follow-up:**

| Option | Description | Selected |
|--------|-------------|----------|
| This phase's own synced issues only | Traces `<beads-id>` back to a task in this phase's own PLAN.md | |
| Everything under the shared epic | Any open issue under the phase's beads_epic, regardless of which plan created it | ✓ |

**User's choice:** Everything under the shared epic
**Notes:** Matches what `regenerate_beads_md` already computes epic-wide; couples to the epic-sharing semantics fixed in quick task 260815-mm8.

---

## Divergence detection

| Option | Description | Selected |
|--------|-------------|----------|
| At every BEADS.md regeneration | Reuse the existing live-bd-query pass; one more computed field | ✓ |
| Only at ship:pre | Dedicated check, new call site | |

**User's choice:** At every BEADS.md regeneration

| Option | Description | Selected |
|--------|-------------|----------|
| bd status vs task completion mismatch | Either direction (closed-but-incomplete OR open-but-done) counts as diverged | ✓ |
| You decide | Let planner work out the comparison during research | |

**User's choice:** bd status vs task completion mismatch (either direction)

---

## Override audit trail

| Option | Description | Selected |
|--------|-------------|----------|
| A commit trailer on the ship commit | Durable, travels with git history, no new artifact | |
| A bd comment on the epic | Visible in bd's own history, requires bd reachable at ship time | |
| Both | Commit trailer (durable) + bd comment (convenience mirror) | ✓ |

**User's choice:** Both
**Notes:** Resolves PRD §12 Q3's open question. Commit trailer is load-bearing (always written); bd comment is best-effort and follows the project's existing B6 fail-open convention — skip and note the skip if bd is unavailable, never block the ship on it.

---

## Divergence report shape

| Option | Description | Selected |
|--------|-------------|----------|
| Extra columns on BEADS.md's existing issue table | No new artifact, visible at every regeneration step | ✓ |
| Separate DIVERGENCE.md artifact | Cleaner for large tables, but duplicates data and adds maintenance | |

**User's choice:** Extra columns on BEADS.md's existing issue table

---

## Claude's Discretion

- Exact commit-trailer key name/format (must be a real parseable git trailer)
- Exact bd comment text content (must name the override and blocking_open/diverged values)
- Which new column names/order to add to BEADS.md's table for the divergence report

## Deferred Ideas

None — discussion stayed within B9/B10 scope throughout.
