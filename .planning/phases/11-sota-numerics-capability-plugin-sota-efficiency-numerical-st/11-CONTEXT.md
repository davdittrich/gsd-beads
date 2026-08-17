# Phase 11: sota-numerics capability plugin - Context

**Gathered:** 2026-08-17
**Status:** Ready for planning

<domain>
## Phase Boundary

A third gsd-core capability plugin, `sota-numerics`, in this repo's marketplace alongside
`beads` and `ponytail-everywhere`. It pushes SOTA-verification, efficiency, and
numerical-stability discipline (mirroring the user's global CLAUDE.md rules — Alternatives
Mandatory, SOTA Verification, Mechanism Justification ranking) into gsd's plan/execute/verify/ship
lifecycle: advisory steering fragments at all four points, plus one blocking `plan:post` gate that
requires a populated, cited "Alternatives Considered" section in every non-trivial `PLAN.md`.
Reuses Phase 10.1's auto-install mechanism from the start (own vendored copy per D-05 of that
phase's decisions), not retrofitted later.

</domain>

<decisions>
## Implementation Decisions

### Gate trigger scope
- **D-01:** The blocking gate is universal — fires at `plan:post` for every phase's `PLAN.md`
  once `sota-numerics.enabled` is true, regardless of domain (not scoped to
  numerics/algorithm-touching phases only). Matches the user's global CLAUDE.md rule, which
  applies to "every new feature or refactor plan," not just numerics work. — **Reversibility:**
  reversible — config toggle, no migration.
- **D-02:** Scope is per-plan, not per-task. One "Alternatives Considered" section per `PLAN.md`
  covering the plan's significant mechanism/library choices — not one per `<task>` element.
  Mirrors CLAUDE.md's `PLAN MUST HEADER` pattern, which is per-plan.
- **D-03:** Trivial plans (pure config/doc/mechanical-rename, no real mechanism choice) are
  exempt: the planner may write an explicit "N/A — no mechanism choice" and the gate accepts
  that as satisfying the section-presence check, rather than forcing a fabricated comparison.
- **D-04:** Dogfooded in this repo. Once shipped, install and enable `sota-numerics` in
  gsd-beads' own `.gsd/capabilities/` the same way `beads` and `ponytail` were — this repo's own
  future phase plans go through the gate too, not just a build-and-release-only posture.
- **D-05:** When a phase has already gone through `/gsd-spec-phase` and has a `SPEC.md`, the
  `plan:post` gate still independently requires `PLAN.md`'s own Alternatives Considered section —
  a SPEC.md's alternatives analysis does not satisfy it. SPEC.md locks WHAT/requirements;
  PLAN.md's Alternatives Considered covers HOW/mechanism, a distinct decision layer (consistent
  with discuss-phase's own rule that CONTEXT.md's `<decisions>` never duplicates SPEC.md content).

### What the gate mechanically checks
- **D-06:** The gate requires cited grounding per alternative, not just section-presence with
  named alternatives. Each alternative in the Alternatives Considered section must carry an
  attached source (URL, doc ref, or dated citation) — mirrors CLAUDE.md's FR-47
  (`sota_findings_cited_in_spec`) and "grounded search backs it."
- **D-07:** Citations require a recency marker (a date, or the source itself being visibly
  current — e.g. official docs' "last updated," a recent release version). A source with no
  discoverable date does not satisfy the check. Matches CLAUDE.md's "web search for [Task] best
  practice [Current Year]" instruction literally.
- **D-08:** Truthfulness of citations (real URLs, real dates, not hallucinated) is not something
  a frontmatter predicate can verify — gsd-core's only predicate kinds are `command-exists` and
  `artifact-frontmatter-equals`, structural checks only. Verification is layered: the frontmatter
  predicate checks structural presence (fields exist, well-formed), and `gsd-plan-checker`
  (already dispatched by `/gsd-plan-phase`) gets a contribution fragment instructing it to
  spot-check that cited URLs/dates look plausible before the gate is allowed to pass. This is a
  soft, human-adjacent check, not a hard guarantee — same trust model beads uses for its own
  `blocking_open`/`diverged` frontmatter counts.
- **D-09:** The frontmatter check also requires the plan to name which ranked criterion
  (performance / simplicity-LOC / ecosystem / maintenance, in that order — CLAUDE.md's
  Mechanism Justification ranking) decided the choice for each mechanism pick. This makes the
  gate mechanically enforce the ranked-justification rule, not just alternatives-existence.
- **Minimum count:** at least 2 named, cited, dated alternatives per non-trivial mechanism
  choice (CLAUDE.md: "Compare proposed library/framework against 2+ current alternatives").

### Default on/off after install
- **D-10:** `sota-numerics.enabled` defaults **true** — the gate blocks immediately post-install,
  including in this repo per D-04. User explicitly chose this over opt-in-false, diverging from
  `beads.enabled`'s default-false precedent (a blocking gate is normally the higher-stakes case
  that precedent reserves for opt-in) in favor of ponytail's "used at all stages" reasoning
  extended to the blocking case too. — **Reversibility:** reversible — config default, flippable
  per project via `.planning/config.json`.
- **D-11:** One single config key controls both the advisory steering fragments and the blocking
  gate — no separate `gate_enabled` split. Simplest config surface; unlike `beads.ship_gate`
  (a genuinely separate finer-grained key layered under `beads.enabled`), this capability's
  steering and gating are treated as one inseparable feature, not two.

### Steering fragment coverage
- **D-12:** Full four-point spread, matching the phase title and ponytail's precedent:
  `plan:pre` (planner — SOTA-research framing, before the gate fires at `plan:post`),
  `execute:wave:pre` (executor — numerical-stability/no-cancellation framing),
  `execute:wave:post` (verifier — "flag unjustified simplification/precision loss" framing),
  `ship:pre` (ship reviewer — "confirm precision/efficiency claims before shipping" framing, no
  gate, advisory only).
- **D-13:** Stage-tailored fragment text, not one shared generic reminder — mirrors ponytail's
  D-05. Each point's wording matches what that agent is actually doing at that moment.

### Claude's Discretion
- Exact per-lifecycle-point fragment wording within the stage-tailored framings above (D-12,
  D-13).
- Exact schema/field names for the frontmatter the `plan:post` step writes (e.g. field names for
  alternatives list, citation, date, ranked-criterion) and the exact predicate expression(s) the
  gate evaluates against it.
- Exact wording of the `gsd-plan-checker` contribution fragment for citation plausibility
  spot-checking (D-08).
- Config key naming beyond `sota-numerics.enabled` (D-11) — e.g. whether any additional keys are
  needed (mirrors ponytail's `ponytail.level`-style precedent, if an analogous intensity/strictness
  knob turns out to be needed).
- Capability id / directory name and exact `into:` targeting per contribution point.
- How the `plan:post` step distinguishes "trivial, exempt" (D-03) plans from ones requiring the
  gate — heuristic left to planning/implementation, same as Phase 10.1's D-06 drift-prevention
  mechanism was left open.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Structural analogues (read before implementing)
- `.gsd/capabilities/beads/capability.json` — the only capability in this repo with `gates[]`
  populated; shows the `artifact-frontmatter-equals` predicate shape this phase's new gate must
  follow, and the two-predicate-kind ceiling (`command-exists`, `artifact-frontmatter-equals`) —
  no predicate kind queries content directly, which is why a `plan:post` step must write derived
  frontmatter for the gate to read.
- `.gsd/capabilities/ponytail/capability.json` — the closest structural precedent for
  stage-tailored `contributions[]` fragments (D-12, D-13) and for a config-driven
  intensity/level knob if one is added later; has `gates: []` (no blocking gate at all) — this
  phase is the first blocking gate outside `ship:pre` in this repo, requires new design, not a
  copy-paste.
- `.gsd/capabilities/beads/GSD-CORE-PATCH.md` — documents this repo's one precedent for a local
  gsd-core patch, made necessary because the installed `ship.md`'s `ship:pre` gate dispatch is
  hardcoded to `capId=='security'/'broken-windows'` with no generic gate-enumeration loop (per
  `PROJECT.md`'s Key Decisions table). **Before planning, verify whether the installed
  `plan-phase.md` workflow already has a generic `gates[]` dispatch at `plan:post`, or whether
  this phase needs an equivalent local patch** — this is the single highest-risk open question
  for the planner/researcher, analogous to the Phase 3 discovery that motivated
  `GSD-CORE-PATCH.md`.
- `.planning/phases/10.1-capability-auto-install-sessionstart-triggered-user-scope-co/10.1-CONTEXT.md`
  — the auto-install mechanism this phase must reuse from the start (own vendored copy per that
  phase's D-05, not a shared runtime file).
- `hooks/hooks.json` + `hooks/session-start.sh` (in each of `beads`/`ponytail` plugin dirs) — the
  SessionStart hook registration pattern a third plugin must replicate, including its own
  vendored auto-install script copy.
- `.claude-plugin/marketplace.json` — the `plugins[]` array this phase adds a third entry to.

### Project context
- `.planning/PROJECT.md` — Key Decisions table: the T-06-01 reversal / auto-install re-decision
  history (context for why D-04's dogfood choice and D-10's default-true choice are consistent
  with this repo's established pattern of installing and live-verifying its own capabilities).
- `.planning/ROADMAP.md` Phase 11 section — goal statement this CONTEXT.md expands on; confirms
  `Requirements: TBD` (no REQUIREMENTS.md entries exist yet for this phase, same as Phase 10 and
  10.1 — new scope, not part of the v1.1 milestone's requirement set).
- User's global `CLAUDE.md` (`~/.claude/CLAUDE.md`) — the literal source of the rules this
  capability encodes: "Alternatives Mandatory," "SOTA Verification," "Mechanism Justification"
  ranking (performance > simplicity/LOC > ecosystem > maintenance), "Spec gate" (`FR-47`,
  `sota_findings_cited_in_spec`), and "Confound gate." This capability is, in effect, a
  gsd-core-native enforcement mechanism for rules the user already holds themselves to manually —
  read this file's relevant sections directly, don't rely on this CONTEXT.md's paraphrase.

No other external specs.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `hooks/session-start.sh` pattern (present in both `beads` and `ponytail` plugin dirs) — a third
  plugin's SessionStart hook follows the same shape, plus the vendored Phase 10.1 auto-install
  script.
- `.gsd/capabilities/beads/fragments/recall-pointer.md` and `.gsd/capabilities/ponytail/fragments/`
  — existing example fragment files referenced by `fragment.path` from `capability.json`.
- `.gsd/capabilities/beads/capability.json`'s `gates[]` array — the only existing
  `artifact-frontmatter-equals` gate examples in this repo, both at `ship:pre`; this phase's
  `plan:post` gate is new territory but the predicate shape is directly reusable.

### Established Patterns
- Config keys namespaced under `<capability-id>.*` — collisions rejected by gsd-core's capability
  loader; `sota-numerics.*` (or whatever id is chosen) must be checked against every shipped
  manifest before use, same rule documented for `beads.*` and `ponytail.*`.
- `onError: "skip"` fail-open posture used throughout `beads`/`ponytail` — applies to this
  capability's steps/contributions, but the blocking gate itself is deliberately NOT fail-open by
  design (a blocking gate that skips on error would defeat its own purpose) — same kind of
  deliberate fail-open divergence Phase 10.1's D-04 called out for its own auto-grant failure
  path; flag this divergence explicitly in the plan so a future edit doesn't "fix" it back to
  silent-skip.
- Phase 10.1's vendored-copy-per-plugin pattern (not a shared runtime file) — this phase's
  auto-install integration follows the same shape.

### Integration Points
- `.claude-plugin/marketplace.json`'s `plugins[]` array — needs a third entry for
  `sota-numerics`.
- The installed `plan-phase.md` workflow (or its `plan:post` gate-dispatch point, if one doesn't
  yet exist) — the single largest unresolved mechanism question, flagged above.
- `gsd-plan-checker`'s dispatch — needs a new contribution fragment for citation-plausibility
  spot-checking (D-08).

</code_context>

<specifics>
## Specific Ideas

No UI/behavior references — this is a capability-plugin authoring phase, same as Phase 10/10.1.
The `beads` and `ponytail` capabilities are the concrete structural models to follow
(canonical_refs above), not abstract standards. The gate design itself is explicitly modeled on
the user's own global CLAUDE.md rules (Alternatives Mandatory / SOTA Verification / Mechanism
Justification / Spec gate) — those sections are the closest thing this phase has to a spec.

</specifics>

<deferred>
## Deferred Ideas

- **`beads.enabled` default flip to `true`** — user raised mid-discussion (2026-08-17) that
  `beads` should also default enabled=true on install, matching D-10's sota-numerics choice and
  ponytail's existing default-true. This is a change to the already-shipped `beads` capability's
  `capability.json` (`.gsd/capabilities/beads/capability.json`), not part of Phase 11's
  `sota-numerics` scope. Routed to its own phase, inserted after Phase 11 —
  see `.planning/phases/11.1-beads-enabled-default-flip-to-true/`.

</deferred>

---

*Phase: 11-sota-numerics capability plugin*
*Context gathered: 2026-08-17*
