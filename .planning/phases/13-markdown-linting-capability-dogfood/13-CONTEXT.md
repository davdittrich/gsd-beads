# Phase 13: markdown-linting capability (dogfood) - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

This repo's own lifecycle measures and reports `.planning/` (+ selected root docs) markdown
quality via a new `markdown-linting` gsd-core capability, built on the already-proven
`artifact-frontmatter-equals` mechanism (the same predicate kind `beads` uses for its `ship:pre`
gate). This phase also delivers the first live proof that a generic `ship:pre` gate fires for a
capId other than `security` / `broken-windows`.

Requirements: MDL-01, MDL-02, MDL-03, MDL-04 (see REQUIREMENTS.md). All four are already
precisely specified there — this discussion clarifies HOW to implement them, not WHAT they are.

</domain>

<decisions>
## Implementation Decisions

### Existing-violation cleanup (MDL-01 prerequisite)
- **D-01:** Bring `.planning/` (and README.md/CLAUDE.md, per D-02) to 0 violations via `rumdl --fix`
  (mechanical auto-fix), then spot-check the diff before committing — not a full line-by-line
  hand-review of every changed file. — **Reversibility:** reversible — it's a working-tree diff,
  revertable via git before commit if the spot-check finds a problem.

### Lint scope boundary
- **D-02:** Lint globs for v1: `.planning/**/*.md` **plus** root `README.md` and `CLAUDE.md` (the
  two root docs agents touch most often). `docs/` and any other markdown is excluded from v1.
  — **Reversibility:** reversible — glob list is a config value, not a migration.
- **Note for planner:** ROADMAP.md's Phase 13 success criteria (MDL-01/MDL-02) only name the
  `.planning/` tree explicitly ("0 violations" against ".planning/ tree", "hand-run rumdl count on
  the same tree"). Since scope now also includes README.md/CLAUDE.md, both must independently pass
  0 violations before the gate ships, and the plan's verification steps should cover all three
  paths — not just what the roadmap wording names.

### LINT-REPORT.md depth
- **D-03:** `.planning/LINT-REPORT.md` is count-only: frontmatter (`violation_count`, timestamp,
  config path used) plus the standard "regenerated every step, never hand-edited" banner (matches
  `BEADS.md`'s established minimalism). No per-rule or per-file breakdown table in the body —
  detail comes from a manual `rumdl` run against the same `--config`, not from the generated
  artifact. — **Reversibility:** reversible — adding a breakdown table later is additive, doesn't
  change the frontmatter contract the `ship:pre` gate reads.

### rumdl install/invocation method
- **D-04:** Prefer a locally-installed `rumdl` already on `PATH`. If absent, fall back to
  `uvx rumdl` (no persistent install). If `uvx` itself fails or is unavailable, degrade
  non-blocking with exactly one visible notice — this composes with MDL-04's existing
  `shutil.which("rumdl")` B6 fail-open requirement rather than replacing it: check PATH first,
  then attempt the `uvx` fallback, then fail open. README documents both paths; `uvx` is not
  presented as the sole/primary method. — **Reversibility:** reversible — invocation order is a
  script-level detail, not a contract.

### Claude's Discretion
- Exact rumdl config file location under `.gsd/capabilities/markdown-linting/` (e.g.
  `config/.rumdl.toml`) and its internal TOML structure.
- Whether the `verify:post` step is a Python script (beads-sync style) or another mechanism —
  must still produce `.planning/LINT-REPORT.md` with the frontmatter contract in D-03.
- Exact wording of the advisory ship-transcript warning naming the violation count (MDL-03,
  success criterion 4).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §MARKDOWN-LINTING (MDL-01..04, MDL-05 deferred to v2) — full
  requirement text, including the rumdl-vs-markdownlint-cli2 and rumdl-vs-mdsmith Out of Scope
  entries with their benchmark rationale
- `.planning/ROADMAP.md` §Phase 13 — success criteria (5 items) and the v1.2 Cross-Cutting
  Constraints (ship:pre patch verification requirement, advisory-not-blocking default, fail-open
  on every external tool)
- `.planning/PROJECT.md` §Key Decisions — `ship.md` generic gate-dispatch patch history
  (gsd-core#3554/#3559), the `beads` `ship:pre` gate live-verification precedent this phase must
  match

### Precedent capabilities (read before designing capability.json)
- `.gsd/capabilities/beads/capability.json` — `artifact-frontmatter-equals` gate pattern
  (`ship:pre`, `onError: skip`), step-based generation of a regenerated-every-step artifact
  (`BEADS.md`)
- `.gsd/capabilities/sota-numerics/capability.json` — alternate gate shape
  (`command-exit-zero` + script), contribution-fragment pattern; **not** the mechanism MDL-03
  specifies (MDL-03 requires `artifact-frontmatter-equals`, matching `beads`, not `sota-numerics`)
- `.gsd/capabilities/mempalace/capability.json` — closest shipped analogue for shape and
  degrade-cleanly behavior per PROJECT.md's own note; read before implementing

### State / open risks
- `.planning/STATE.md` §Blockers/Concerns — hard prerequisite: verify the generic `ship:pre`
  gate-dispatch marker in `$HOME/.claude/gsd-core/workflows/ship.md` before relying on the gate
  (MDL-03, Pitfall 1); curated ruleset validated only in theory until run against the live tree

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.gsd/capabilities/beads/` sync/step scripts — pattern for a Python script invoked at a
  lifecycle point that writes a generated, frontmatter-bearing artifact
- `capabilities/mempalace/capability.json` — shape/degrade-cleanly reference named directly in
  PROJECT.md

### Established Patterns
- Every capability's config lives under `<id>.*` (collision-checked at load) — this capability's
  namespace is `markdown-linting.*`
- Gates default `onError: skip`; the one exception in this repo (`sota-numerics`'s blocking
  `plan:post` gate) deliberately uses `onError: halt` and documents why inline — MDL-03 is
  advisory, so it follows the `skip` default, not the `sota-numerics` exception
- B6 fail-open pattern: `shutil.which(<tool>)` guard, exactly one visible notice per missing-tool
  case, no hang, no stale artifact presented as current

### Integration Points
- `verify:post` → generates/regenerates `.planning/LINT-REPORT.md`
- `ship:pre` → gate reads `LINT-REPORT.md`'s `violation_count` via `artifact-frontmatter-equals`

</code_context>

<specifics>
## Specific Ideas

- rumdl invocation always passes an explicit `--config <path>` — never relies on auto-discovery
  (measured in this repo to silently ignore `.markdownlint-cli2.jsonc`-style config files).
- README must state rumdl's measured 45% detection-logic miss rate vs. markdownlint-cli2 on this
  exact curated ruleset (e.g. MD001: 14 vs 1) as a known, accepted difference — not glossed over.

</specifics>

<deferred>
## Deferred Ideas

None raised beyond the roadmap's own v2 backlog (MDL-05, blocking gate — already tracked in
REQUIREMENTS.md).

### Reviewed Todos (not folded)
None — no pending todos matched this phase's scope.

</deferred>

---

*Phase: 13-markdown-linting-capability-dogfood*
*Context gathered: 2026-08-18*
