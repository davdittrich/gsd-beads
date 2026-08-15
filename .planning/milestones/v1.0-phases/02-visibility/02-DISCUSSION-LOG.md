# Phase 2: Visibility - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-15
**Phase:** 2-visibility
**Areas discussed:** BEADS-RECALL.md scope-matching, BEADS.md frontmatter shape, claim-and-close fragment content, beads-status skill reuse vs. new skill

---

## BEADS-RECALL.md scope-matching

| Option | Description | Selected |
|--------|-------------|----------|
| File-path overlap | Compare issue's linked file paths against phase's expected files_modified | |
| Epic/label match | Match by phase epic naming convention or bd label | |
| Both, file-path first | Try file-path overlap; fall back to epic/label match if no file refs | ✓ |

**User's choice:** Both, file-path first
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| List separately as "Unscoped" | Never silently drop an open issue with no match | ✓ |
| Exclude entirely | Only list issues with a confirmed match | |

**User's choice:** List separately as "Unscoped"
**Notes:** —

---

## BEADS.md frontmatter shape

| Option | Description | Selected |
|--------|-------------|----------|
| Full shape now, zeroed placeholders | phase/epic/open/closed/blocking_open/diverged/generated_from/generated_at all present now | ✓ |
| Minimal now, extend in Phase 3 | Only phase/epic/open/closed/generated_from/generated_at | |

**User's choice:** Full shape now, zeroed placeholders
**Notes:** One artifact schema across phases, no Phase 3 migration.

| Option | Description | Selected |
|--------|-------------|----------|
| Fine as-is | gates[] empty until Phase 3, nothing consumes these fields yet | |
| Mark it explicitly | Note in body text that blocking_open/diverged aren't computed yet | ✓ |

**User's choice:** Mark it explicitly
**Notes:** Documentation safeguard against a human mid-Phase-2 misreading the zero as verified.

| Option | Description | Selected |
|--------|-------------|----------|
| Phase dir, same 4 columns | issue/title/status/plan-task | |
| Add a blocked-by column | Same location, plus dependency-chain visibility | ✓ |

**User's choice:** Add a blocked-by column
**Notes:** Surfaces Phase 1's dependency edges (B2) without a manual `bd show`.

---

## claim-and-close fragment content

| Option | Description | Selected |
|--------|-------------|----------|
| Names + status only | List issue ids/titles/status, no instruction line | ✓ |
| Names + status + a soft instruction | Same list plus a "don't duplicate" suggestion | |

**User's choice:** Names + status only
**Notes:** Contributions are prompt text only — can't force bd command compliance.

| Option | Description | Selected |
|--------|-------------|----------|
| Out of scope, defer | Claim behavior isn't in B7/B8/B11's acceptance criteria | ✓ |
| Rename the fragment now | Same outcome, framed as a naming fix | |

**User's choice:** Out of scope, defer
**Notes:** Fragment renamed to describe what it does (e.g. `wave-issue-status.md`) since the PRD's literal `claim-and-close.md` name describes unbuilt capability.

---

## beads-status skill reuse vs. new skill

| Option | Description | Selected |
|--------|-------------|----------|
| Same skill, branch on dispatch point | capability.json wires beads-status at both execute:wave:pre and execute:wave:post | ✓ |
| Separate skill for pre-wave | New read-only skill, no closing logic reachable | |

**User's choice:** Same skill, branch on dispatch point
**Notes:** Matches Phase 1's pattern of sharing sync.py helpers rather than duplicating them.

| Option | Description | Selected |
|--------|-------------|----------|
| Separate beads-recall skill | Matches PRD's three-skill list; different consumer and matching logic than BEADS.md | ✓ |
| Fold into beads-status | One skill, branches on dispatch point | |

**User's choice:** Separate beads-recall skill
**Notes:** Scope-matching logic doesn't share meaningfully with BEADS.md's plain wave-id lookup.

---

## Follow-up: Recall UX

| Option | Description | Selected |
|--------|-------------|----------|
| Silent, planner reads it | No blocking, matches B7's literal acceptance criterion | ✓ |
| Surface to user before planning | Print a short summary before the planner spawns | |

**User's choice:** Silent, planner reads it
**Notes:** —

## Follow-up: Empty case

| Option | Description | Selected |
|--------|-------------|----------|
| Always write it, explicit "none found" | Consistent artifact presence | ✓ |
| Skip writing when nothing matches | Matches B6's existing absence-means-nothing pattern | |

**User's choice:** Always write it, explicit "none found"
**Notes:** Keeps file-presence unambiguous — absent means bd unavailable (B6), present always means the scope-match ran.

---

## Claude's Discretion

- Exact BEADS-RECALL.md/BEADS.md markdown formatting beyond the locked column/field lists.
- Whether the fragment's status list is inline prose or a small table.
- Internal helper function names/shapes in sync.py for the new generation paths.

## Deferred Ideas

- Claim behavior (marking a bd issue in_progress when a wave starts) — not in B7/B8/B11's scope; revisit in a future phase if the executor needs to actively coordinate issue ownership.
