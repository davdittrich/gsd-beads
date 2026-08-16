# Phase 10: ponytail-everywhere capability plugin - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-17
**Phase:** 10-ponytail-everywhere capability plugin
**Areas discussed:** Default on/off, Intensity source, Fragment specificity

---

## Default on/off

| Option | Description | Selected |
|--------|-------------|----------|
| Opt-in (matches beads.enabled) | ponytail.enabled default false — consistent with this repo's own beads capability convention. | |
| On by default | ponytail.enabled default true — the capability's whole point is "used at all stages", so silently-off-by-default defeats the purpose. | ✓ |

**User's choice:** On by default
**Notes:** None

---

## Intensity source

| Option | Description | Selected |
|--------|-------------|----------|
| Configurable ponytail.level (Recommended) | default full, values lite/full/ultra — mirrors /ponytail's own tiers. | ✓ |
| Hardcode full | Simpler, no config key — always injects the 'full' ladder text. | |

**User's choice:** Configurable ponytail.level
**Notes:** None

---

## Fragment specificity

| Option | Description | Selected |
|--------|-------------|----------|
| Stage-tailored (Recommended) | plan: "pick the laziest viable task shape"; execute: "climb the ladder before writing code"; verify: "flag unrequested abstractions found". | ✓ |
| One shared text | Same generic ladder reminder injected verbatim at every point. | |

**User's choice:** Stage-tailored
**Notes:** Exact per-point wording and point-to-stage mapping left to Claude's discretion.

---

## Claude's Discretion

- Exact per-lifecycle-point fragment wording within the stage-tailored framings.
- Exact mapping of which of the 10 available lifecycle points receive a contribution vs. rely on the SessionStart hook alone.
- Config key naming beyond `ponytail.enabled` / `ponytail.level`.
- Capability id / directory name and per-hook `into:` target.

## Deferred Ideas

None — discussion stayed within phase scope. Phase 11 (`sota-numerics`) is a separately-scoped phase, not a deferred idea from this discussion.
