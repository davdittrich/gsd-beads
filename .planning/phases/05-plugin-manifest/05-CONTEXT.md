# Phase 5: Plugin Manifest - Context

**Gathered:** 2026-08-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Claude Code recognizes this repo as a valid, discoverable, MIT-licensed plugin: `.claude-plugin/plugin.json` declares identity and points at the existing skill without duplicating it, `.claude-plugin/marketplace.json` makes a local `/plugin marketplace add ./` + `/plugin install` round trip work, `LICENSE` exists at repo root. No new capability behavior — this phase is packaging metadata only.

</domain>

<decisions>
## Implementation Decisions

### Plugin identity (plugin.json)
- **D-01:** `name` field is `beads` — matches the capability id (`.gsd/capabilities/beads/`) and the install command from REQUIREMENTS.md PUB-02 (`/plugin install beads@gsd-beads`), not the repo name `gsd-beads`.
- **D-02 (amended 2026-08-16 during execution, user consent required by Task 1's HALT RULE):** `author` field is `{"name": "Dennis A. V. Dittrich", "email": "davdittrich@gmail.com"}`. Originally email-only; `claude plugin validate . --strict` hard-errors (`author.name: Invalid input: expected string, received undefined`) in plugin-directory mode without `name`. User chose to amend rather than accept validation failure.
- **D-03:** `version` starts at `0.1.0` — matches `capability.json`'s current version rather than jumping to `1.0.0`.

### LICENSE
- **D-04:** MIT `LICENSE` copyright line reads: `Copyright (c) 2026 Dennis A. V. Dittrich` — **Reversibility:** reversible — cosmetic text change, no downstream dependency.

### Marketplace entry (marketplace.json)
- **D-05:** Entry id/name is `beads`, same as plugin.json's `name` — one identity across manifest and marketplace, matches PUB-02's install command.
- **D-06:** Entry `description` is a short, friendly install-page blurb written fresh for browsing installers (e.g. "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle") — NOT the verbatim PROJECT.md "Core Value" sentence, which is denser/more jargon-heavy than a marketplace listing needs.
- **D-07:** Source in this phase stays a relative local path (`./`) — per PROJECT.md's note, PUB-02 is authored here and re-pointed at the release archive URL in Phase 8. Do not point at a GitHub URL yet.

### Skills-path mechanism
- **D-08:** How `plugin.json` references `.agents/skills/beads/` without a duplicated copy is left to `gsd-phase-researcher` — find what Claude Code's plugin schema actually supports (relative path in a `skills` field, symlink, etc.) rather than guessing now. Whatever mechanism the researcher confirms is binding; do not invent a second mechanism during planning.

### Validation strategy
- **D-09:** Phase verification runs `claude plugin validate . --strict` **twice**: once with `marketplace.json` temporarily moved/absent (this is the mode that actually checks skill frontmatter, per ROADMAP.md success criterion 1's explicit wording), and once in the normal repo state. Both runs must exit clean before the phase is considered done — a single normal-state run is not sufficient evidence given the known false-green gotcha.

### Claude's Discretion
- Exact JSON formatting/key ordering in `plugin.json` and `marketplace.json`.
- Whether `LICENSE` uses the canonical MIT template verbatim or a lightly reformatted equivalent (content, not wording, is what's decided above).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap / Requirements (locked scope)
- `.planning/ROADMAP.md` §"Phase 5: Plugin Manifest" — success criteria 1-4, the exact `claude plugin validate . --strict` double-run requirement, and the "Known gate hazard" note this context's D-09 is built from.
- `.planning/REQUIREMENTS.md` §"Plugin Packaging" — PUB-01, PUB-02, PUB-08 full requirement text.
- `.planning/PROJECT.md` — "PUB-02 is authored in Phase 5, re-pointed in Phase 8" note (source of D-07); Constraints section (reserved id prefixes, `beads.*` config namespace, no new runtime dependency).

### Existing capability (do not duplicate, do not modify without re-consent)
- `.gsd/capabilities/beads/capability.json` — the shipped capability this plugin packages. plugin.json's `skills` field must resolve to `.agents/skills/beads/`, listed here as `beads-sync`, `beads-status`, `beads-recall`, `beads-migrate-todos`.
- `.agents/skills/beads/SKILL.md` — the skill directory plugin.json must reference without copying.

No ADRs/PRDs exist for this phase beyond the above; no user-referenced docs came up during discussion.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.gsd/capabilities/beads/capability.json` — source of truth for capability id (`beads`), version (`0.1.0`), and skill list; plugin.json's identity fields should stay consistent with it (D-01, D-03).

### Established Patterns
- None yet — no `.claude-plugin/` directory exists in the repo. This phase creates it from scratch.

### Integration Points
- `.agents/skills/beads/` is the skill directory plugin.json must point at (D-08, mechanism TBD by research).
- Repo root is where `LICENSE` and `.claude-plugin/` both land — currently no `LICENSE` file exists (confirmed via directory listing).

</code_context>

<specifics>
## Specific Ideas

No particular UI/format references given beyond the decisions above — standard Claude Code plugin manifest conventions apply, informed by research into the actual schema.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. No scope-creep suggestions came up.

</deferred>

---

*Phase: 5-Plugin Manifest*
*Context gathered: 2026-08-16*
