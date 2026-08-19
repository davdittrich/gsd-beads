# Phase 15: Ship markdown-linting and pr-workflow plugins publicly - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 15-ship-markdown-linting-and-pr-workflow-plugins-publicly
**Areas discussed:** Initial versioning, gsd-beads tag/release, Order of operations

---

## Initial versioning

| Option | Description | Selected |
|--------|-------------|----------|
| v1.0.0 for both | Code already shipped/verified via Phases 13-14 dogfood — not new, mark stable from day one | |
| v0.1.0 for both | Fresh repo = fresh start regardless of maturity elsewhere; bump to 1.0 after first real external install | ✓ |
| Match Phase 12 precedent exactly | Use whatever version ponytail-everywhere/sota-numerics actually got tagged, mirror it | |

**User's choice:** v0.1.0 for both.
**Notes:** None.

---

## gsd-beads tag/release

| Option | Description | Selected |
|--------|-------------|----------|
| No new tag | marketplace.json is metadata, not a release artifact; Phase 12 D-06 precedent — leave gsd-beads' tag history untouched | ✓ |
| Yes, cut a new tag | marketplace.json changed shipped behavior (existing installs now resolve differently) — release-worthy | |

**User's choice:** No new tag.
**Notes:** Matches Phase 12 D-06 exactly.

---

## Order of operations

| Option | Description | Selected |
|--------|-------------|----------|
| Sequential | Create+validate+round-trip markdown-linting fully, then repeat for pr-workflow — isolates failures | |
| Parallel | Both repos created and validated in the same wave — no dependency between them, faster overall | ✓ |

**User's choice:** Parallel.
**Notes:** No dependency between the two extractions; each still gets its own full validation/round-trip proof independently.

---

## Claude's Discretion

- Exact wave/task breakdown for the parallel execution (single task doing both `gh repo create` calls vs two independent tasks).
- README prose differences beyond the tool-name substitution (`rumdl` vs `gh`).

## Deferred Ideas

None — discussion stayed within phase scope.
