# Phase 19: Native Resolver Contract and Failure Boundary - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in CONTEXT.md; this log preserves alternatives.

**Date:** 2026-08-30
**Phase:** 19-native-resolver-contract-and-failure-boundary
**Areas discussed:** Description boundary, heading grammar, list normalization,
unusable-content failures

---

## Description Boundary

| Option | Description | Selected |
|---|---|---|
| Non-duplicated execution prose | Retain only content not moved to native fields. | ✓ |
| Complete original Markdown | Retain all content and duplicate extracted fields. | |
| Flatten or Action-only | Remove headings or discard other execution sections. | |

**User's choice:** Non-duplicated prose with headings and order preserved,
leading prose retained, and no synthesized metadata.

**Notes:** The user selected this across four single-question turns.

---

## Heading Grammar

| Option | Description | Selected |
|---|---|---|
| Canonical writer inverse | Exact headings, fence-aware, duplicates fail. | ✓ |
| Permissive partial CommonMark | Accept case, indentation, and duplicate variants. | |
| Full Markdown parser | Add an AST dependency for arbitrary Markdown. | |

**User's choice:** Delegated to the named skills.

**Notes:** Ponytail and codebase-design select the existing producer grammar and
single adapter seam. Scientific-critical-thinking rejects silent duplicate
aggregation and unsupported tolerance. Recognized sections may occur in any
order because an order check adds rejection without resolving ambiguity.

---

## List Normalization

| Option | Description | Selected |
|---|---|---|
| Writer/core-compatible | Canonical Read First bullets plus `splitCriteria`. | ✓ |
| Permissive inference | Guess commas, bullets, and wrapped paragraphs. | |
| Scalar-only | Preserve every field as one array item. | |

**User's choice:** Delegated to the named skills.

**Notes:** Matching the installed core is direct evidence; broader inference is
not. Preserve order and duplicates, reject malformed Read First content, and
accept absent optional fields.

---

## Unusable-Content Failures

| Option | Description | Selected |
|---|---|---|
| Strict adapter validation | Nonzero with bounded stderr and empty stdout. | ✓ |
| Core coercion | Let wrong types become null or empty arrays. | |
| Plan fallback | Recover from Beads failures using inline prose. | |

**User's choice:** Delegated to the named skills.

**Notes:** Official Beads documentation now defines both the legacy array and
the opt-in versioned envelope, so both documented shapes are accepted and all
others fail. The fallback option violates RES-03.

## the agent's Discretion

- Exact private helper names.
- Exact concise diagnostic wording within the fixed categories and bounded
  stderr contract.
- Test fixture names and organization.

## Deferred Ideas

None.
