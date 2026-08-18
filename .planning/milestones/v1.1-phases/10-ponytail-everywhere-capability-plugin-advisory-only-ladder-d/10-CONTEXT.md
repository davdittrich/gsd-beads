# Phase 10: ponytail-everywhere capability plugin - Context

**Gathered:** 2026-08-17
**Status:** Ready for planning

<domain>

## Phase Boundary

A new gsd-core capability plugin, `ponytail-everywhere`, that pushes `/ponytail`'s
lazy-ladder discipline (YAGNI, reuse before writing, stdlib/native before dependencies,
shortest working diff) into gsd's plan/execute/verify/ship lifecycle — advisory reminders
only, no mechanical gate. Ships as a new entry in this repo's marketplace, alongside the
existing `beads-lifecycle` plugin.

</domain>

<decisions>

## Implementation Decisions

### Mechanism (carried forward from /gsd-explore)
- **D-01:** No gsd-core patch. `/gsd-explore` and `/gsd-spec-phase` dispatch zero capability
  lifecycle hooks — only `discuss:{pre,post}`, `plan:{pre,post}`,
  `execute:{pre,wave:pre,wave:post,post}`, `verify:{pre,post}`, `ship:{pre,post}` exist. Reach
  is instead layered: a SessionStart hook (broad, always-on, reaches every stage including
  explore/spec) plus `capability.json` `contributions[]` fragments at the six real lifecycle
  points (targeted, injected into the actual agent prompt). — **Reversibility:** reversible —
  config/content change, no migration.
- **D-02:** Advisory only — no gate. "Did you pick the laziest rung that works" isn't
  mechanically checkable; a diff-size/line-count gate was considered and rejected as a blunt,
  false-positive-prone proxy.

### Default on/off
- **D-03:** `ponytail.enabled` defaults to **true** (on by default post-install) — diverges
  from this repo's own `beads.enabled` (default false) convention deliberately. User's
  reasoning: the capability's whole point is "used at all stages"; silently-off-by-default
  would defeat that purpose. — **Reversibility:** reversible — a config default, flippable per
  project via `.planning/config.json`.

### Intensity source
- **D-04:** Injected fragments read a configurable `ponytail.level` config key (values:
  `lite`/`full`/`ultra`, default `full`) rather than hardcoding one fixed ladder text —
  mirrors `/ponytail`'s own intensity levels, so a project running `/ponytail ultra` gets
  capability reminders matching that level instead of a mismatched fixed text.

### Fragment specificity
- **D-05:** Stage-tailored fragment text, not one shared generic reminder repeated verbatim at
  every lifecycle point. Each contribution's text matches what the agent at that point is
  actually doing — e.g. the planner gets a "pick the laziest viable task shape" framing, the
  executor gets a "climb the ladder before writing code" framing, the verifier gets a "flag
  unrequested abstractions found" framing. Exact per-point wording and exact stage-to-point
  mapping is Claude's discretion (see below).

### Claude's Discretion
- Exact per-lifecycle-point fragment wording within the stage-tailored framings above (D-05).
- Exact mapping of which of the 10 available lifecycle points (`plan:pre/post`,
  `execute:pre/wave:pre/wave:post/post`, `verify:pre/post`, `ship:pre/post`) receive a
  contribution vs. rely on the SessionStart hook alone.
- Config key naming beyond the two named above (`ponytail.enabled`, `ponytail.level`) — e.g.
  whether any additional keys are needed.
- Capability id / directory name (e.g. `ponytail-everywhere`) and how the `<available_agent_types>`-style
  fragment insertion point (`into: "planner"` / `"executor"` / `"verifier"`) is chosen per hook.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Structural analogue (read before implementing)
- `.gsd/capabilities/beads/capability.json` — the only shipped capability in this repo;
  concrete shape for `steps[]`/`contributions[]`/`gates[]`, `config`, `runtimeCompat`, `engines`.
- `.gsd/capabilities/beads/GSD-CORE-PATCH.md` — documents the one precedent for patching
  gsd-core itself (the `ship:pre` generic-dispatch gap); read as the cautionary example this
  phase's D-01 explicitly avoids repeating.
- `hooks/hooks.json` + `hooks/session-start.sh` — this repo's existing SessionStart hook
  registration pattern (the `beads-lifecycle` plugin's own hook). New plugins need their own
  hook registration — exact directory layout for a second/third plugin in one marketplace is a
  research question (marketplace.json `source` pointing at a subdirectory with its own
  `.claude-plugin/plugin.json`), not a user decision.
- `.claude-plugin/marketplace.json` — the `plugins[]` array this phase adds an entry to.

### Project context
- `.planning/PROJECT.md` — Current Milestone is "v1.1 Publish & Document" (beads-focused,
  already fully shipped per Validated requirements). Phase 10/11 are NOT part of that
  milestone's requirement set — this is new scope created directly via `/gsd-explore` →
  `phase add`, with no REQUIREMENTS.md entries yet. Flag this to the planner: no `phase_req_ids`
  exist for Phase 10 (confirmed — `roadmap.get-phase` returned `"Requirements": TBD`).
- `.planning/notes/two-plugin-capability-design.md` — the `/gsd-explore` session's design
  rationale in full (mechanism layering, no-core-patch reasoning, gate divergence between the
  two new plugins).

No other external specs.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets
- `hooks/session-start.sh` pattern — a new plugin's own SessionStart hook is a small shell
  script emitting static/config-driven reminder text, same shape as the existing one (which
  self-heals `.beads/PRIME.md` then execs `bd prime --hook-json`).
- `.gsd/capabilities/beads/fragments/recall-pointer.md` — existing example of a `contributions[]`
  fragment file referenced by `fragment.path` from `capability.json`.

### Established Patterns
- Config keys namespaced under `<capability-id>.*` (e.g. `beads.enabled`) — collisions rejected
  by gsd-core's capability loader; `ponytail.*` must be checked against every shipped manifest
  before use (same rule PROJECT.md documents for `beads.*`).
- `gates[].onError: "skip"` / fail-open pattern used throughout `beads` capability — not directly
  applicable here since this phase has no gates, but the same fail-open posture should apply to
  the SessionStart hook (a missing config value should default silently, never error the session).

### Integration Points
- `.claude-plugin/marketplace.json`'s `plugins[]` array — needs a second entry pointing at this
  plugin's new subdirectory (exact path is a research/planning decision).

</code_context>

<specifics>

## Specific Ideas

No particular UI/behavior references — this is a capability-plugin authoring phase. The
`beads` capability is the concrete structural model to follow (canonical_refs above), not an
abstract standard.

</specifics>

<deferred>

## Deferred Ideas

None — discussion stayed within phase scope. (Phase 11's `sota-numerics` capability is a
separate, already-scoped phase — not a deferred idea, just not this phase's concern.)

</deferred>

---

*Phase: 10-ponytail-everywhere capability plugin*
*Context gathered: 2026-08-17*
