# Phase 17: Config/Code Truth — Discussion Log

**Date:** 2026-08-20
**Mode:** default (interactive), 4 areas selected of 4 offered

Human reference only. Downstream agents read `17-CONTEXT.md`, not this file.

---

## Area 1 — `sync_mode` disposition

### Q: What should happen to `beads.sync_mode`?

Options presented:
- Narrow to `["authoritative"]` — keep the key, delete `mirror`/`off`, keeps the typed
  `config-set` error alive
- Drop the key entirely — follows the `reviewerCli` removal precedent and the siblings' 0-orphan norm
- Implement `mirror` and `off` — possible via self-read, but `off` duplicates `beads.enabled: false`
- You decide during planning

**Selected: "Other" — `implement mirror, drop "off"`.**

A hybrid none of the options offered. Rationale developed in the exchange: `off` was never a
distinct behavior (it duplicates `beads.enabled: false`), while `mirror` names something the
capability already does privately via `allow_strip=False`. This turns TRUTH-01 from "delete a dead
declaration" into "expose existing behavior under the name already declared for it."

Note the three research documents had converged on narrow (ARCHITECTURE, PITFALLS) vs drop
(FEATURES); the user's answer was outside both.

### Q: Concretely, what does `mirror` do?

Options presented:
- `mirror` = never strip PLAN.md *(recommended)*
- `mirror` = read-only projection (bd never the source; executor always reads PLAN.md)
- Let me describe it

**Selected: never strip PLAN.md.**

### Q: Hook's hardcoded `allow_strip=False` vs config — which wins?

Options presented:
- Hook forces mirror regardless of config
- Config governs every path uniformly
- You decide during planning

**Selected: hook forces mirror regardless of config.** Locks the asymmetry: a string-matched hook
is a weaker principal than an explicit dispatch, and v1.3.0 proved what happens when
pattern-matching can trigger irreversible deletion.

### Q: How should an existing on-disk `sync_mode` value be treated?

Options presented: silent no-op + release note / warn once / you decide

**Selected: you decide during planning.**

Orchestrator note added afterwards: the question *inverted* once `mirror` became real. An existing
`mirror` is no longer stale — it starts behaving differently on upgrade. `off` is now the only
value needing a removal migration.

---

## Area 2 — `allow_strip` under native dispatch

Policy was resolved inside Area 1 (D-03/D-06), leaving only the mechanism.

### Q: When #3687 ships, how should the hook know to stand down?

Options presented:
- Probe the workflow file for native dispatch *(recommended)*
- Version-sniff gsd-core VERSION
- Accept double dispatch, do nothing
- You decide during planning

**Selected: probe the workflow file.** Version-sniffing was unavailable in practice — the release
carrying #3687 does not exist yet, so the constant could not be written.

---

## Area 3 — Decimal-phase semantics

### Q: How should `int(phase_num)` at `sync.py:634` and `:1489` be replaced?

Options presented:
- Strip leading zeros as a string, then `re.escape` *(recommended)*
- Parse to float or Decimal
- You decide during planning

**Selected: string strip + `re.escape`.**

Raised during scouting and carried into the decision: both sites interpolate the value directly
into a regex, so a bare `"11.1"` makes `.` a metacharacter. `re.escape` is a correctness
requirement, not a style preference.

---

## Area 4 — Patch-checker CLI surface

### Q: Keep both verbs or collapse to one parameterized verb?

Options presented:
- Keep both verbs, share the internals *(recommended)*
- Collapse to one parameterized verb
- You decide during planning

**Selected: collapse to one parameterized verb** — against the recommendation.

The recommendation was made before the callers were grepped. Once established that no README
exposure and no out-of-repo caller exists, collapsing became the better-supported option and the
recommendation was withdrawn.

### Q: How should the table handle differing marker versions?

Options presented:
- Per-entry version + a test that asserts it *(recommended)*
- Per-entry version, no new test
- You decide during planning

**Selected: per-entry version + a test.** Closes the blind spot that let commit `966315a` change
`SHIP_MD_PATCH_MARKER` from v1 to v2 with the suite still green.

### Q: Hard break on the old verb names, or aliases?

Options presented:
- Hard break, update all callers in the same commit *(recommended, after the caller grep)*
- Keep old verbs as aliases for one release (`reviewerCli` precedent)
- You decide during planning

**Selected: hard break.**

---

## Claude's discretion (recorded, not asked)

- Migration handling for an existing `sync_mode` value
- Exact shape/name of the parameterized verb
- Internal table data shape
- Whether release-hygiene debt is its own plan or folds into the last plan's ship step

## Deferred ideas

- `REACH-01` — non-Claude-Code runtime dispatch
- `RES-01` — `get-available-resources`
- Refiling the `execute:wave:*` step-dispatch gap upstream (no track exists; #3554 closed unreviewed)

## Process note

This discussion ran *after* a research phase that had been skipped on the first pass. The skip cost
a roadmap revision: the original Phase 17 was written against gsd-core 1.10.0 while 1.11.0 was
already released, and the research then surfaced PR #3687 — merged 6h50m after the 1.11.0 cut —
which added TRUTH-03 to this phase entirely.
