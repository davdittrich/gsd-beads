# Phase 20: Additive Identity Migration and Compatibility - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-31
**Phase:** 20-Additive Identity Migration and Compatibility
**Areas discussed:** Migration coverage, Pre-existing native identity, Identity placement and byte stability, Checkpoint protection

---

## Migration Coverage

| Option | Description | Selected |
|---|---|---|
| New mappings only | Add native identity only when this sync creates a Beads issue. | |
| All eligible mappings | Add it to existing and newly resolved exact `auto`/`tracer` mappings. | ✓ |

**User's choice:** Delegate all open questions to Ponytail, scientific-critical-thinking, and domain-specific installed skills.
**Notes:** Successful resolution is required; stale/unavailable Beads state does not authorize a migration.

---

## Pre-existing Native Identity

| Option | Description | Selected |
|---|---|---|
| Overwrite | Replace any present native value with Beads-derived identity. | |
| Fail closed | Add only a missing value; conflict or duplicate attributes leave the plan unwritten. | ✓ |

**User's choice:** Delegate all open questions to Ponytail, scientific-critical-thinking, and domain-specific installed skills.
**Notes:** Prevents silent displacement of a competing tracker binding.

---

## Identity Placement and Byte Stability

| Option | Description | Selected |
|---|---|---|
| Child element | Add a new `<tracker-id>` task child. | |
| Rewrite blocks | Reserialize task blocks into a canonical form. | |
| Opening attribute | Insert one lexical `tracker-id` attribute after `type`; leave all other bytes intact. | ✓ |

**User's choice:** Delegate all open questions to Ponytail, scientific-critical-thinking, and domain-specific installed skills.
**Notes:** Second synchronization makes no write and no `bd create` call.

---

## Checkpoint Protection

| Option | Description | Selected |
|---|---|---|
| Current fixtures only | Protect only known checkpoint forms. | |
| All checkpoint variants | Keep all `checkpoint:*` tasks, plus missing/unknown types, byte-identical. | ✓ |

**User's choice:** Delegate all open questions to Ponytail, scientific-critical-thinking, and domain-specific installed skills.
**Notes:** Eligibility is exact `auto` or `tracer` only.

---

## the agent's Discretion

Private helper names, exact diagnostics, and fixture names may vary only within
the decisions captured in CONTEXT.md.

## Deferred Ideas

None.
