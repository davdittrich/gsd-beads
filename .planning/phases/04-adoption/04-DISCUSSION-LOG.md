# Phase 4: Adoption - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-15
**Phase:** 4-Adoption
**Areas discussed:** Todo → issue field mapping, Un-interpretable / already-moved todos,
beads-status "on demand" surface, epic_per=milestone behavior, Migration invocation & report
format, Migration duplicate detection, beads-status orphan output format

---

## Todo → issue field mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Severity → priority, area → label | Both fields carry forward, nothing dropped | ✓ |
| Area → label only, severity ignored | Severity stays in body text, not a structured field | |
| You decide | Leave mapping to research/planning | |

**User's choice:** Severity → priority, area → label
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Research verifies bd's scale first | Same pattern as Phase 1's bd-divergence discovery | ✓ |
| Lock it now: blocker=P0, major=P1, minor=P2, cosmetic=P3 | Skip research detour | |

**User's choice:** Research verifies bd's scale first
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Carry into issue body/description | Prose, same treatment as Problem/Solution text | ✓ |
| Drop it | file:lines pointers often stale by migration time | |

**User's choice:** Carry into issue body/description
**Notes:** —

---

## Un-interpretable / already-moved todos

| Option | Description | Selected |
|--------|-------------|----------|
| Left in place in pending/, reported | Non-destructive, human fixes and re-runs | ✓ |
| Moved to a pending/failed/ subfolder | Sorts failures out of main listing | |

**User's choice:** Left in place in pending/, reported
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Delete the file after successful migration | bd becomes sole source of truth | ✓ |
| Move to .planning/todos/migrated/, archive | Preserves original for reference | |
| Leave in place, track via bd-id: frontmatter | Same binding pattern as PLAN.md tasks | |

**User's choice:** Delete the file after successful migration
**Notes:** —

---

## beads-status "on demand" surface

| Option | Description | Selected |
|--------|-------------|----------|
| New slash command, e.g. /gsd-beads-status [phase] | Consistent with other gsd capabilities | ✓ |
| Direct sync.py CLI invocation only | Power users call the script directly | |

**User's choice:** New slash command
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Current/last-active phase by default, optional arg | Matches skill's argument-hint shape | ✓ |
| Whole milestone by default (all phases) | Full-picture audit but bigger report | |

**User's choice:** Current/last-active phase by default, optional arg to override
**Notes:** —

---

## epic_per=milestone behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Forward-only, no retroactive folding | Matches "never auto-reconciled" philosophy | ✓ |
| Retroactively fold existing epics too | More consistent end state, real write op on history | |

**User's choice:** Forward-only, no retroactive folding
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Allowed to change anytime | Config read at sync time, no lock needed | ✓ |
| Locked after first epic created for the milestone | Prevents mixed-granularity milestone | |

**User's choice:** Allowed to change anytime
**Notes:** —

---

## Migration invocation & report format

| Option | Description | Selected |
|--------|-------------|----------|
| New slash command, e.g. /gsd-migrate-todos | Consistent user-facing surface | ✓ |
| CLI-only: python3 sync.py migrate-todos | Matches create-issues/close-wave internal-only pattern | |

**User's choice:** New slash command
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Console output only | bd is durable record, no artifact to go stale | ✓ |
| Console output + written MIGRATION-REPORT.md | Durable audit trail like SUMMARY.md | |

**User's choice:** Console output only
**Notes:** —

---

## Migration duplicate detection

| Option | Description | Selected |
|--------|-------------|----------|
| Always create new, no dedup | Matches N4's spirit, cheap cleanup if it happens | ✓ |
| Dedup via exact title match against open bd issues | Cheap deterministic check | |

**User's choice:** Always create new, no dedup
**Notes:** —

---

## beads-status orphan output format

| Option | Description | Selected |
|--------|-------------|----------|
| Two separate labeled sections below the mapping table | Matches BEADS-RECALL.md's "Unscoped" pattern | ✓ |
| Extra columns in the existing mapping table | More compact but busier single table | |

**User's choice:** Two separate labeled sections below the mapping table
**Notes:** —

---

## Claude's Discretion

- Exact severity→priority numeric mapping — pending research verification of bd's real priority
  scale.
- Exact slash-command names (`/gsd-beads-status`, `/gsd-migrate-todos`) and argument parsing
  details.
- Exact section headings/wording for the two orphan sections, as long as the pattern matches
  `BEADS-RECALL.md`'s established "Unscoped" heading style.

## Deferred Ideas

None raised during this discussion — stayed within B12/B13/B14 scope throughout.
