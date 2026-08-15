# Phase 1: Substrate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-15
**Phase:** 1-Substrate
**Areas discussed:** Issue title/body format & content ownership, Fail-open notice format,
Epic naming, Stale beads-id handling, Dependency mapping, Replan orphans, beads-id placement,
gsd-core source availability

---

## Issue title/body format

| Option | Description | Selected |
|--------|-------------|----------|
| Verbatim title, body links back to PLAN.md | Minimal duplication; PLAN.md stays single source of truth | |
| Verbatim title, full description copied into body | Self-contained issue | |
| Prefixed title (task-id/number) | Better sort/search across phases | ✓ (as free text: "Prefixed title, minimal duplication: TICKET is single source of truth for task content") |

**User's choice:** Prefixed title; and — surfaced as a side effect of the free-text answer — the
bd issue, not `PLAN.md`, should be the source of truth for task content going forward.

**Notes:** This contradicted a locked PROJECT.md decision ("beads owns status only; PLAN.md owns
content"). Flagged the conflict and asked a follow-up.

---

## Content ownership (follow-up clarification)

| Option | Description | Selected |
|--------|-------------|----------|
| Keep locked split: PLAN.md owns content, prefixed title only mirrors it | No content duplication, B10 divergence semantics unchanged | |
| Reverse it: bd issue becomes source of truth for content | Overrides the PROJECT.md Key Decision | ✓ |

**User's choice:** Reverse it — bd issue is authoritative for content from first sync onward.

**Notes:** PROJECT.md's Key Decisions table and Binding Model section were updated in place
(2026-08-15) to record this as a superseding decision rather than leaving a silent contradiction.

---

## Fail-open notice format (B6)

| Option | Description | Selected |
|--------|-------------|----------|
| stdout line only | Ephemeral, minimal | |
| stdout line + STATE.md Blockers/Concerns | Stays visible across sessions, no new artifact | ✓ |
| stdout line + BEADS.md frontmatter status field | Conflicts with B6 wording (BEADS.md must be absent, not stale, when bd is down) | |

**User's choice:** stdout line + STATE.md Blockers/Concerns entry.

---

## Epic naming per phase

| Option | Description | Selected |
|--------|-------------|----------|
| "Phase 1: Substrate" verbatim from ROADMAP.md | Zero mapping/translation logic | ✓ |
| Coded form, e.g. "P01-substrate" | Compact, sorts predictably | |
| Project-code prefixed | Disambiguates across projects sharing one bd database | |

**User's choice:** Verbatim ROADMAP.md phase header.

---

## Stale beads-id handling

| Option | Description | Selected |
|--------|-------------|----------|
| Treat as B10 divergence — block, report both sides | Consistent with locked "never auto-reconciled" decision | ✓ |
| Recreate automatically with a fresh id | Contradicts B10 | |
| Error loudly, fail the sync step | Risks blocking a phase over external bd drift, contradicts B6 | |

**User's choice:** Treat as B10 divergence.

---

## Dependency mapping (B2)

| Option | Description | Selected |
|--------|-------------|----------|
| Only explicit "depends on" edges | Matches PLAN.md's authored dependency graph exactly | ✓ |
| Also infer wave-order as implicit dependency | More conservative `bd ready` output | |

**User's choice:** Only explicit edges; wave grouping is scheduling, not a dependency.

---

## Replan orphans

| Option | Description | Selected |
|--------|-------------|----------|
| Close as orphaned, leave a note | Nothing silently vanishes | ✓ |
| Leave open, flag in beads-status only | No automatic close | |

**User's choice:** Close as orphaned, leave a note.

---

## beads-id placement

| Option | Description | Selected |
|--------|-------------|----------|
| One-line metadata field under the task heading | Visible, greppable, minimal format change | ✓ |
| HTML comment marker | Invisible in rendered markdown | |

**User's choice:** One-line metadata field under the task heading.

---

## gsd-core source availability

No gsd-core source checkout found on disk (only the runtime skill overlay, no `src/`,
`capabilities/`, or `tests/`). Asked how Phase 1 research should proceed.

| Option | Description | Selected |
|--------|-------------|----------|
| User provides the checkout path | Point at a local clone or npm package location before research | |
| Researcher fetches it (npm/GitHub) as part of Phase 1 | Add as explicit research task; note as open blocker in CONTEXT.md | ✓ |

**User's choice:** Researcher fetches gsd-core source as part of Phase 1 research.

---

## Claude's Discretion

- Exact stdout notice wording/format for the B6 fail-open case.
- Exact `bd dep add` invocation shape (batched vs. per-edge), as long as B5 idempotency holds.
- Whether the phase epic is created eagerly at first sync or lazily on first issue — deferred to
  whatever fits gsd-core's actual `plan:post` hook firing behavior (technical, not user-facing).

## Deferred Ideas

- PRD §12: `execute:wave:post` per-task vs per-wave firing — technical question for the
  researcher, not a user preference; carried forward from STATE.md.
- PRD §12: packaging (Python entry point vs JS shell-out) — likely already resolved by
  PROJECT.md's N5 constraint (bd + Python 3 stdlib only); researcher to confirm.
- PRD §12: where a `beads.ship_gate=false` override gets recorded — relevant to Phase 3, not
  Phase 1.
