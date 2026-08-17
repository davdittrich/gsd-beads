# Phase 11: sota-numerics capability plugin - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-17
**Phase:** 11-sota-numerics capability plugin
**Areas discussed:** Gate trigger scope, What the gate mechanically checks, Default on/off after install, Steering fragment coverage

---

## Gate trigger scope

| Option | Description | Selected |
|--------|-------------|----------|
| Universal | Fires on every plan:post regardless of domain | ✓ |
| Numerics/perf-gated | Only fires when the plan touches numerical/algorithmic/perf-sensitive code | |
| You decide | Claude picks simplest reliable implementation | |

**User's choice:** Universal (D-01)
**Notes:** Followed by 4 sub-questions, all answered:
- Per-plan vs per-task section granularity → **Per-plan** (D-02)
- Exempt trivial plans with "N/A" vs always required → **Exempt trivial plans** (D-03)
- Dogfood in this repo vs ship-only → **Dogfood it here too** (D-04)
- SPEC.md-locked phases: does SPEC.md's alternatives analysis satisfy the gate → **No, PLAN.md always required independently** (D-05)

---

## What the gate mechanically checks

| Option | Description | Selected |
|--------|-------------|----------|
| Require cited grounding per alternative | Each alternative needs an attached source | ✓ |
| Presence-only | Section + ≥2 named alternatives, no citation check | |
| Presence + freshness marker, no content check | Requires a date/flag marker only | |

**User's choice:** Require cited grounding per alternative (D-06)
**Notes:** User raised mid-discussion: "Alternatives considered is not sufficient to nudge the use of SOTA... is it?" — correctly identified that alternatives-comparison alone doesn't guarantee currency. This drove the follow-up chain:
- Recency required vs any-age source → **Recency required** (D-07)
- Who verifies citations aren't hallucinated: trust self-report vs plan-checker spot-check → **Add a plan-checker verification step** (D-08)
- Require ranked-criterion (performance/simplicity/ecosystem/maintenance) rationale in the frontmatter vs leave as free-text prose → **Require the ranking rationale** (D-09)

---

## Default on/off after install

| Option | Description | Selected |
|--------|-------------|----------|
| Default false, opt-in | Matches beads.enabled precedent for higher-stakes toggles | |
| Default true | Matches ponytail's "used at all stages" reasoning, extended to the blocking case | ✓ |

**User's choice:** Default true (D-10) — overrode Claude's recommendation (default false)
**Notes:** Follow-up: one shared toggle for fragments+gate vs split keys (`enabled` vs `gate_enabled`) → **One toggle for both** (D-11).

Mid-turn, user separately noted: `beads.enabled` should ALSO default to true on install — flagged as out of Phase 11 scope (see Deferred Ideas in CONTEXT.md), not acted on in this discussion.

---

## Steering fragment coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Full spread, ponytail-style | plan:pre + execute:wave:pre + execute:wave:post | ✓ |
| plan:pre only | Only the planner gets a fragment | |

**User's choice:** Full spread (D-12)
**Notes:** Follow-ups:
- Add ship:pre fragment (matching phase title's "plan/execute/verify/ship") vs stop at verify → **Yes, add ship:pre fragment** (D-12 extended)
- Stage-tailored fragment text (ponytail D-05 style) vs one shared generic text → **Stage-tailored** (D-13)

---

## Claude's Discretion

- Exact per-lifecycle-point fragment wording within the stage-tailored framings (D-12, D-13)
- Exact frontmatter schema/field names the plan:post step writes, and exact predicate expression(s)
- Exact wording of the gsd-plan-checker citation-plausibility-spot-check fragment (D-08)
- Config key naming beyond `sota-numerics.enabled` (D-11)
- Capability id / directory name and exact `into:` targeting per contribution point
- Heuristic for detecting "trivial, exempt" plans (D-03)

## Deferred Ideas

- `beads.enabled` default flip to `true` — raised mid-discussion, out of Phase 11 scope (affects
  the already-shipped `beads` capability, not `sota-numerics`). Not acted on; user to route
  separately (quick task vs. new phase).
