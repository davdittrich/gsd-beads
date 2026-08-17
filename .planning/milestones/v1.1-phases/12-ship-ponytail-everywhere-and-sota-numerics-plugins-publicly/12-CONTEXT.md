# Phase 12: Ship ponytail-everywhere and sota-numerics plugins publicly - Context

**Gathered:** 2026-08-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Publish `ponytail-everywhere` and `sota-numerics` — currently only dogfooded as subdirectories
inside the `gsd-beads` repo (Phase 10, 10.1, 11) — as independently installable Claude Code
plugins on GitHub, discoverable through the same marketplace `gsd-beads` already exposes for
`beads-lifecycle`. This is a distribution phase, not a feature phase: no new plugin behavior,
just making the two existing plugins reachable by a stranger the way `beads-lifecycle` already is
(Phase 5-8 precedent).

</domain>

<decisions>
## Implementation Decisions

### Repo topology (major revision mid-discussion — supersedes the phase's original framing)
- **D-01:** Each of the 3 plugins gets its **own separate public GitHub repo** —
  `ponytail-everywhere` and `sota-numerics` are NOT staying as subdirectories of `gsd-beads`.
  This reverses the phase's initial assumption (that the existing in-repo subdirectory +
  Directory-source marketplace entry was already "shipped"). — **Reversibility:** one-way —
  once split and pushed, un-splitting means either re-merging repos (loses the split repos'
  own history) or keeping 3 repos forever; treat the split as permanent.
- **D-02:** `gsd-beads` hosts the shared `marketplace.json` (unchanged location). The
  `beads-lifecycle` entry stays a local Directory source (`"./"`); `ponytail-everywhere` and
  `sota-numerics` entries switch from local Directory sources (`"./ponytail-everywhere"`,
  `"./sota-numerics"`) to git-hosted sources pointing at their new standalone repos. Exact
  marketplace.json schema for a cross-repo git source is a research question (see
  canonical_refs) — no Claude Code plugin marketplace docs were consulted during this
  discussion.
- **D-03:** History: **fresh init, no history extraction.** The two new repos start clean at
  current file state — do NOT use `git filter-repo` to carry Phase 10/10.1/11 commit history
  out of `gsd-beads` into the new repos (unlike Phase 7's history-preserving rewrite of
  `gsd-beads` itself, which was a different problem — stripping files, not splitting repos).
- **D-04:** Once each new repo is live and pushed, **remove `ponytail-everywhere/` and
  `sota-numerics/` subdirectories from `gsd-beads`** — no dual-copy authoring source left
  behind. **The repo-root dogfood copies stay untouched**: `.gsd/capabilities/ponytail/` and
  `.gsd/capabilities/sota-numerics/` are a separate concern (capability activation/dogfooding
  in this repo, per Phase 10/11's D-04/D-05 vendored-copy pattern) and are NOT the plugin
  subdirectories being removed — do not confuse the two when planning file removal.

### Versioning & tagging
- **D-05:** Independent versioning per repo. `ponytail-everywhere` and `sota-numerics` each
  start their own version/tag sequence in their own repo (e.g. `v0.1.0` or `v1.0.0` — planner's
  call), with no coupling to `gsd-beads`' version number or release cadence.
- **D-06:** `gsd-beads`' existing ad-hoc `v1.2.0` tag (an untracked manual rename-fix, never run
  through a phase) is **left alone** — this phase does not touch it. Whether `gsd-beads` itself
  needs a new tag for the `marketplace.json` update is Claude's discretion (see below) — the
  user did not mandate a new gsd-beads release, only that it not disturb `v1.2.0`.

### Release archive scope
- **D-07:** Neither new plugin needs a GitHub Release archive (the clean 5-file allowlist
  pattern `beads-lifecycle` uses per Phase 8's `release.yml`). A plugin's own repo IS the clean
  scope already — no `.planning/`/`.beads/` pollution to strip, unlike `gsd-beads`' whole-repo
  Directory source. Marketplace install (once pointed at the new repos) is the only install
  path needed for these two.
- **D-08:** `gsd-beads`' existing `.github/workflows/release.yml` needs **no change** — it
  keeps building only the `beads-lifecycle` archive. The two new plugins are reached purely via
  their own repos + the shared marketplace entry, untouched by this CI file.

### README depth
- **D-09:** Each new repo's README matches `beads-lifecycle`'s full structure (Phase 8 PUB-07
  pattern): purpose, requirements, install, uninstall, caveats, license, link to gsd-core.
  Same "stranger can evaluate, install, and remove from the README alone" bar for all 3
  marketplace entries — no thinner treatment for the two advisory-only plugins.

### Validation & round-trip scope
- **D-10:** Each new repo needs the **same full proof** Phase 8 did for `beads-lifecycle`:
  `claude plugin validate . --strict` clean on the pushed repo, AND a real
  `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip executed
  against the public repo (not just validate-and-stop).

### Claude's Discretion
- Exact repo names (default assumption: `davdittrich/ponytail-everywhere` and
  `davdittrich/sota-numerics`, matching the existing subdirectory names and the
  `davdittrich/gsd-beads` naming convention) — confirm with user before creating if any doubt.
- Whether `gsd-beads` itself needs a new tag/release once `marketplace.json` is updated (D-06
  leaves this open — not mandated, not forbidden).
- Starting version number for each new repo (`v0.1.0` vs `v1.0.0`) — these plugins are not new
  code, just newly-distributed existing (already-verified, Phase 10/11-shipped) code, so either
  is defensible.
- Exact marketplace.json git-source schema/fields for a cross-repo plugin entry — this is a
  **research question**, not a discretion call; the researcher must find Claude Code's
  documented format before the planner locks the exact JSON shape (see canonical_refs).
- Order of operations across the two plugins (parallel vs sequential repo creation) — no
  dependency between them, planner's call on wave structure.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Research question (must resolve before planning locks JSON shape)
- **Claude Code plugin marketplace `source` schema for a git-hosted (non-local) plugin entry**
  — no existing example in this repo; `.claude-plugin/marketplace.json`'s current 3 entries are
  ALL local Directory sources (`"./"`, `"./ponytail-everywhere"`, `"./sota-numerics"`). The
  researcher must find the official schema for pointing a `plugins[]` entry at a different
  GitHub repo (owner/repo, git URL, or other supported form) before the planner can write the
  exact new entries for D-02.

### Structural analogues (read before implementing)
- `.claude-plugin/marketplace.json` (this repo) — current 3-entry state; the file this phase
  edits in place for D-02.
- `ponytail-everywhere/.claude-plugin/plugin.json` and `sota-numerics/.claude-plugin/plugin.json`
  — already-correct plugin manifests (name, description, author, MIT license); these move as-is
  into the new repos, no content changes needed per this discussion.
- `README.md` (repo root) — the structural template for D-09's new READMEs: purpose,
  requirements, install, uninstall, caveats, license, gsd-core link, in that section order.
- `LICENSE` (repo root, MIT) — both new plugins' `plugin.json` already declare `"license": "MIT"`;
  each new repo needs its own copy of this same MIT text.

### Project context
- `.planning/ROADMAP.md` Phase 10 and Phase 11 sections — the original build/dogfood scope this
  phase now completes the distribution half of; confirms neither phase's success criteria
  covered public push or a standalone repo (the gap this phase closes).
- `.planning/phases/10-ponytail-everywhere-capability-plugin-advisory-only-ladder-d/10-CONTEXT.md`
  and `.planning/phases/11-sota-numerics-capability-plugin-sota-efficiency-numerical-st/11-CONTEXT.md`
  — original build decisions for each plugin; unchanged by this phase, just relocated.
- `.planning/phases/10.1-capability-auto-install-sessionstart-triggered-user-scope-co/10.1-CONTEXT.md`
  D-05 — the vendored-copy-per-plugin rationale explaining why `.gsd/capabilities/<id>/` at
  `gsd-beads` root is a separate, untouched concern from the plugin subdirectories being removed
  (D-04 above must not be misread as touching these).
- `.planning/phases/08-readme-release-ship-gate/` (all plans + SUMMARYs) — the precedent this
  phase's D-09/D-10 explicitly mirror: README structure, `claude plugin validate . --strict`,
  and the marketplace add/install/uninstall round trip, all executed once already for
  `beads-lifecycle`.
- `.planning/phases/09-beads-content-depth/09-04-PLAN.md` and `09-04-SUMMARY.md` — the most
  recent release-cutting precedent (v1.1.0 → v1.1.1 retirement); relevant process reference even
  though D-07/D-08 concluded no release archive is needed here — the AskUserQuestion checkpoint
  pattern for irreversible public actions (push, tag, retire) still applies.

No other external specs — this is an internal distribution/publishing phase.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ponytail-everywhere/` and `sota-numerics/` subdirectories (this repo) — complete, verified,
  already-shipped-and-dogfooded plugin trees (`.claude-plugin/plugin.json`, `hooks/`,
  `.gsd/capabilities/<id>/`, `tests/`). These become the new repos' initial content verbatim
  (D-03: no history, just current files).
- `07-01-PLAN.md`/`07-02-PLAN.md` (Phase 7) — this repo's own precedent for standing up a fresh
  public GitHub repo from existing local content (`gh repo create ... --public --source=.` +
  push), directly reusable for the two new repos even though Phase 7's trigger (history
  rewrite) doesn't apply here.

### Established Patterns
- MIT license, `plugin.json` shape (`name`, `version`, `description`, `author: {name, email}`,
  `license`) — both new plugins already conform; no changes needed to `plugin.json` content
  itself, only its new repo location.
- `claude plugin validate . --strict` as the standard pre-publish gate (Phase 5, Phase 8
  precedent) — one documented permanent exception exists for `gsd-beads` root (CLAUDE.md
  warning, D-07 of Phase 5's CONTEXT.md); the two new repos have no such file at their root, so
  no analogous exception is expected — flag if the researcher/planner finds one.

### Integration Points
- `.claude-plugin/marketplace.json` (`gsd-beads`) — the single file both new repos' entries get
  edited into (D-02); this is the one gsd-beads-side integration point this phase touches.

</code_context>

<specifics>
## Specific Ideas

No UI/behavior references — this is a repo-topology and publishing phase. The concrete
precedent to follow is this repo's own Phase 5-8 history (how `beads-lifecycle` itself got
published), scaled down to 2 more repos with no history-preservation requirement and no release
archive.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. The mid-discussion repo-topology revision (D-01)
is a correction to the phase's own scope, not new work deferred elsewhere.

</deferred>

---

*Phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly*
*Context gathered: 2026-08-17*
