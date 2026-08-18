# Phase 15: Ship markdown-linting and pr-workflow plugins publicly - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract `markdown-linting` and `pr-workflow` — currently only dogfooded as subdirectories inside
`gsd-beads` (Phase 13, 14) — into two independently installable public Claude Code plugins on
GitHub, discoverable through the same marketplace `gsd-beads` already exposes for
`beads-lifecycle`, `ponytail-everywhere`, and `sota-numerics`. This is a distribution phase, not a
feature phase: no new plugin behavior, just making the two existing dogfooded plugins reachable by
a stranger — following Phase 12's extraction playbook (D-01..D-10) essentially verbatim, since
Phase 12 already solved the identical problem (splitting `ponytail-everywhere` and `sota-numerics`
out of this same repo).

</domain>

<decisions>

## Implementation Decisions

### Carried forward from Phase 12 (D-01..D-10, unchanged — same playbook applies here)
- **D-00 (carry-forward):** Each plugin gets its own separate public GitHub repo
  (`davdittrich/markdown-linting`, `davdittrich/pr-workflow` — names locked by ROADMAP.md Success
  Criteria 1). Fresh init, no history extraction. `gsd-beads` keeps hosting the shared
  `marketplace.json`; both entries switch from local Directory sources to `url`-type git sources
  with explicit `https://` URLs (ROADMAP Success Criteria 2, Pitfall 3). Once each repo is live and
  pushed, remove the `markdown-linting/` and `pr-workflow/` subdirectories from `gsd-beads` in the
  same commit that repairs every orphaned `ci.yml`/`release.yml`/doc reference (ROADMAP Success
  Criteria 4) — the repo-root dogfood copies under `.gsd/capabilities/<id>/` stay untouched, same
  as Phase 12 D-04's distinction. Neither repo needs a GitHub Release archive (Phase 12 D-07);
  `gsd-beads`' `release.yml` needs no change (D-08). Each README matches `beads-lifecycle`'s full
  structure — purpose, requirements (`rumdl` for markdown-linting; `gh` + auth for pr-workflow),
  install, uninstall, caveats, license, gsd-core link (D-09). Each repo needs the same full proof
  Phase 8/12 did: `claude plugin validate . --strict` clean from a fresh clone, AND a real
  `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip (D-10, ROADMAP
  Success Criteria 1-2). — **Reversibility:** one-way — once split and pushed, un-splitting means
  re-merging repos (loses their own history) or living with 3+1 repos forever.

### Versioning & tagging (phase-specific — discussed)
- **D-01:** Both new repos start at **v0.1.0** — a fresh repo gets a fresh version regardless of
  the code's maturity elsewhere; bump to v1.0.0 after the first real external install proves the
  extraction. This diverges from Phase 12's inconclusive "planner's call" framing by picking one
  answer explicitly for both repos (no per-repo split). — **Reversibility:** reversible — a version
  bump is a normal release, not a migration.
- **D-02:** `gsd-beads` gets **no new tag/release** after `marketplace.json` is updated to point at
  the two new repos. Matches Phase 12 D-06's precedent exactly: marketplace.json is metadata
  pointing existing installs elsewhere, not a release-worthy behavior change in `gsd-beads` itself.
  — **Reversibility:** reversible — a tag can always be cut later if this proves wrong.

### Order of operations (phase-specific — discussed)
- **D-03:** Create, validate, and round-trip **both repos in parallel** (same wave) — no dependency
  between `markdown-linting` and `pr-workflow` extraction, so there's no reason to serialize them.
  Each still gets its own full D-10 proof independently; a failure in one does not block or hide a
  failure in the other. — **Reversibility:** reversible — this is a planning/wave-structure choice,
  not a code artifact.

### Claude's Discretion
- Exact wave/task breakdown for the parallel D-03 execution (e.g. whether `gh repo create` calls
  for both repos happen in the same task or two independent tasks) — planner's call, as long as
  neither repo's proof depends on the other's completing first.
- Whether the two READMEs differ in any wording beyond the tool-name substitution (`rumdl` vs
  `gh`) — Phase 12 D-09 sets the structural bar; exact prose is Claude's call.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Extraction playbook precedent (this phase's primary reference — read first)
- `.planning/milestones/v1.1-phases/12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly/12-CONTEXT.md`
  — the full D-01..D-10 decision set this phase carries forward verbatim (repo topology, history,
  versioning framing, release scope, README depth, validation/round-trip proof).
- `.planning/milestones/v1.1-phases/12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly/12-01-PLAN.md`
  through `12-04-PLAN.md`/`-SUMMARY.md` — the actual executed task breakdown for the analogous
  2-repo extraction; the closest structural template for this phase's plan.
- `.planning/milestones/v1.1-phases/12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly/12-REVIEW.md`
  and `12-VERIFICATION.md` — findings and gate proof from the last time this exact extraction
  pattern ran; read to avoid repeating any fixed issue.

### Project context
- `.planning/ROADMAP.md` Phase 15 section — Goal, Depends on, Success Criteria 1-4, and the v1.2
  Cross-Cutting Constraints (advisory-not-blocking gates, fail-open on external tools, re-consent
  after bundle edits) that apply to both extracted repos post-move.
- `.planning/ROADMAP.md` Phase 13 and Phase 14 sections — the original build/dogfood scope this
  phase completes the distribution half of.
- `.planning/phases/13-markdown-linting-capability-dogfood/13-CONTEXT.md` and
  `.planning/phases/14-pr-workflow-capability-dogfood/14-CONTEXT.md` — original build decisions
  for each plugin; unchanged by this phase, just relocated.
- `.planning/phases/08-readme-release-ship-gate/` (all plans + SUMMARYs) — the original precedent
  Phase 12's D-09/D-10 mirrored and this phase mirrors again: README structure, `claude plugin
  validate . --strict`, and the marketplace add/install/uninstall round trip for `beads-lifecycle`.
- PROJECT.md's stated v1.2 milestone goal ("each dogfooded in this repo then extracted to its own
  public GitHub repo and marketplace entry") — the traceability anchor since this phase has no
  direct REQUIREMENTS.md items of its own.

No other external specs — this is an internal distribution/publishing phase, same as Phase 12.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets
- `markdown-linting/` and `pr-workflow/` subdirectories (this repo) — complete, verified,
  already-shipped-and-dogfooded plugin trees (`.claude-plugin/plugin.json`, `hooks/`,
  `.gsd/capabilities/<id>/`, `tests/`). These become the new repos' initial content verbatim,
  same as Phase 12 D-03 (no history, just current files).
- Phase 12's `12-01-PLAN.md`/`12-02-PLAN.md` — the exact task sequence (`gh repo create ...
  --public --source=.` + push, marketplace.json edit, validate/round-trip, subdirectory removal)
  already executed once for this identical extraction pattern; directly reusable as a template.

### Established Patterns
- MIT license, `plugin.json` shape (`name`, `version`, `description`, `author: {name, email}`,
  `license`) — both plugins already conform; only their new repo location changes.
- `claude plugin validate . --strict` as the standard pre-publish gate (Phase 5, 8, 12 precedent).
- Content-hash capability consent (`.gsd/capabilities/<id>/` bundle hash) — re-consent required
  after the subdirectory-removal commit touches anything inside a bundle dir; this is the same
  gotcha the v1.2 Cross-Cutting Constraints section already documents.

### Integration Points
- `.claude-plugin/marketplace.json` (`gsd-beads`) — the single file both new repos' entries get
  edited into, same integration point Phase 12 touched.
- `ci.yml` / `release.yml` / doc references naming `markdown-linting/` or `pr-workflow/` as
  in-repo paths — must be repaired in the same commit that removes the subdirectories (ROADMAP
  Success Criteria 4).

</code_context>

<specifics>

## Specific Ideas

No UI/behavior references — this is a repo-topology and publishing phase, identical in kind to
Phase 12. The concrete precedent to follow is Phase 12 itself (which followed Phase 5-8's
`beads-lifecycle` publication), scaled to these two plugins.

</specifics>

<deferred>

## Deferred Ideas

None — discussion stayed within phase scope. No scope creep surfaced.

</deferred>

---

*Phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly*
*Context gathered: 2026-08-18*
