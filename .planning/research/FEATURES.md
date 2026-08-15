# Feature Research

**Domain:** README content for a niche Claude Code plugin repo (single-capability developer tool)
**Researched:** 2026-08-16
**Confidence:** MEDIUM

Scope note: "features" below means README *content sections*, not product features — this
milestone ships packaging + docs for an existing, already-built capability (v1.0, 14 requirements
shipped). The question is what a stranger's first read of the repo needs to contain.

## Feature Landscape

### Table Stakes (Users Expect These)

A stranger who lands on the repo must be able to decide install/skip and, if installed, remove
it — without reading `sync.py`.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| One-line purpose statement | First line answers "what is this" before scrolling — every reviewed example (dbt-core, gh cli, standard-readme spec) leads with it | LOW | "Syncs gsd-core's PLAN.md tasks to beads (`bd`) issues, bidirectionally-bound" — reuse PROJECT.md's "What This Is" |
| Requirements/Prerequisites | Anthropic's own official-marketplace plugins (LSP plugins) explicitly warn: "the plugin doesn't install [the binary] for you" — installs that silently no-op on a missing dependency must say so up front | LOW | `bd` binary on PATH, Python 3 stdlib only (N5), `gsd` engine `>=1.6.0` (PROJECT.md Constraints) |
| Install instructions, exact commands | Official docs give one canonical two-step form: `/plugin marketplace add <owner>/<repo>` then `/plugin install <plugin>@<marketplace>` — deviating confuses users trained on that pattern | LOW | Depends on marketplace.json/plugin.json naming being finalized first (see Dependencies) |
| Uninstall instructions, exact commands | Official form is `/plugin uninstall <plugin>@<marketplace>`; removing the marketplace instead (`/plugin marketplace remove`) also uninstalls it — worth stating since it's a common trap | LOW | Both paths exist; document the plugin-scoped one as primary, mention the marketplace-remove side effect as a caveat |
| Link to gsd-core (the host dependency) | This is a capability *for* gsd-core, not standalone — a stranger arriving without gsd-core context needs the parent link immediately, mirrors gsd-core's own README linking to `beads`' upstream (steveyegge/beads) | LOW | Link both directions: gsd-core (open-gsd/gsd-core) and beads (gastownhall/beads) |
| Caveats / limitations | standard-readme and every curated CLI README example includes a caveats-equivalent section; this project in particular has real, non-obvious failure modes already discovered and logged in PROJECT.md | MEDIUM | Must state: fail-open on missing/locked `bd` (N/A crash), `authoritative` sync_mode means bd content wins after first sync, global-scope installs require a consent gate |
| License | Standard-readme: required. Every reviewed CLI README has it | LOW | Confirm LICENSE file exists before linking |
| Security/trust note | Anthropic's own docs mandate this framing for every plugin: "Make sure you trust a plugin before installing... Anthropic does not control what MCP servers, files, or other software are included" | LOW | This plugin has no MCP servers/network calls — say so explicitly, it's a real differentiator (see below) but the *trust* framing itself is table stakes |

### Differentiators (Competitive Advantage)

Not required by convention, but earn trust for a single-capability, low-visibility plugin where
the maintainer has no reputation signal (stars, community) to lean on yet.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Explicit fail-open guarantee, stated plainly | Most plugin READMEs don't document failure modes at all; stating "`bd` absent/failing/locked → no-op, one visible notice, never blocks your phase" (B6, already shipped) preempts the #1 fear of installing a third-party gate-adjacent tool | LOW | Direct quote from PROJECT.md Out of Scope / Constraints — no new writing, just surfacing |
| Binding-model summary (phase↔epic, task↔issue, dependency↔`bd dep add`) | Explains *how* it works in one paragraph so a stranger can judge fit without reading source — most competing "AI + issue tracker" glue tools ship zero architecture explanation | LOW | Already written in PROJECT.md Context section — condense to ~5 lines |
| "Known gotchas we hit" section, sourced from real incidents | Three real production incidents are already logged in Key Decisions (bd schema-version skew, capability-consent-hash invalidation on file edit, stale `--id` flag behavior) — publishing these as documented gotchas is free credibility no competitor doc has, because it's this project's own operational history | LOW | Pure transcription from PROJECT.md Key Decisions table — do not invent new content |
| Config reference (`beads.*` keys) | Self-service: `sync_mode`, `epic_per` — lets a user configure without reading `sync.py` | LOW | Two keys currently (`sync_mode`, `epic_per`) — small table, not a burden |
| CI status badge | Free trust signal once a test workflow exists; gsd-core's own README leads with exactly this | LOW | Depends on a GitHub Actions test workflow existing (packaging-adjacent, check before promising) |

### Anti-Features (Commonly Requested, Often Problematic)

Things that look like "more README = more trust" but backfire for this project specifically.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|------------------|-------------|
| Full architecture/API deep-dive inline | Feels thorough | Duplicates PROJECT.md/PLAN.md content that will drift out of sync with the README the moment a phase changes; also makes the README too long to serve its actual job (evaluate/install/remove) | Link to `.planning/PROJECT.md` or a `docs/ARCHITECTURE.md` split, same pattern gsd-core uses (root README stays short, `docs/` holds depth) |
| Marketing tone / emoji headers (✨🚀) | `.beads/README.md` (bd's own auto-generated readme) uses this style and it's the nearest example in-repo | Wrong register for a precision developer tool competing on correctness, not vibes; also directly conflicts with this project's own CLAUDE.md voice rules (no unearned praise, no filler) | Plain, factual sentences — state what it does, not why it's exciting |
| Star history chart / Discord badge / community section | gsd-core's README has both, and it's the closest sibling repo | Cargo-culting a flagship, multi-thousand-install project's social-proof furniture onto a brand-new single-capability plugin is misleading (implies scale/community that doesn't exist) and looks worse when the numbers are near-zero | Omit until there's an actual community; a single "Issues" link is enough |
| Multi-language README translations | gsd-core ships 5 language variants | Zero signal of non-English demand for a niche integration tool; translations rot the moment English content changes and nobody maintains the other 4 | English only until requested |
| Restating the full `/plugin` command reference (all flags, all scopes) | Feels complete | Anthropic's own docs already own this surface and change it independently (version-gated behavior changes noted across v2.1.195/.221/.232) — a copy will silently go stale | Link to `code.claude.com/docs/en/discover-plugins`, only show the two commands this plugin actually needs |

## Feature Dependencies

```
Install section (exact commands)
    └──requires──> Finalized .claude-plugin/plugin.json `name` field
                       └──requires──> plugin.json/marketplace.json packaging work (parallel/prior ticket)

Uninstall section
    └──requires──> Install section's plugin-name@marketplace-name identifier (same value, must match)

Requirements section
    └──requires──> PROJECT.md Constraints (bd binary, Python 3 stdlib, gsd engine >=1.6.0) — already authored, no new research

Caveats section
    └──requires──> PROJECT.md Key Decisions table (fail-open behavior, authoritative sync_mode, consent-hash gotcha) — already authored

CI badge (differentiator)
    └──requires──> GitHub Actions test workflow existing in the repo (verify before promising in README)
```

### Dependency Notes

- **Install requires the plugin manifest work:** the README's install command literally embeds
  `plugin-name@marketplace-name` — these strings must be fixed by the packaging phase before the
  README can state a correct, non-speculative command. Writing the README first risks documenting
  a name that then has to change (and per official docs, a published plugin `name` is immutable —
  get it right once).
- **Uninstall reuses Install's identifier:** no independent research needed, just consistency.
- **Requirements and Caveats need zero new research:** both are already fully specified in
  `.planning/PROJECT.md` (Constraints, Key Decisions). The README work here is transcription and
  compression, not discovery.
- **CI badge is optional and gated:** don't reference a workflow badge until the workflow exists,
  or the README ships a broken badge on day one.

## MVP Definition

### Launch With (v1.1, this milestone)

- [ ] One-line purpose statement — required for any evaluation to happen at all
- [ ] Requirements (bd binary, Python 3, gsd-core `>=1.6.0`) — install fails silently without this
- [ ] Install instructions (`/plugin marketplace add`, `/plugin install`) — the literal ask in PROJECT.md's milestone goal
- [ ] Uninstall instructions (`/plugin uninstall`) — the literal ask in PROJECT.md's milestone goal
- [ ] Link to gsd-core and to beads (steveyegge/beads) — this is a glue capability, not standalone
- [ ] Caveats (fail-open behavior, authoritative sync_mode, consent-hash re-install gotcha) — directly requested ("caveats" in milestone goal)
- [ ] License section

### Add After Validation (v1.x)

- [ ] Config reference table (`beads.*` keys) — add once someone other than the author configures it and asks "what does `sync_mode` do"
- [ ] CI badge — add once a test workflow is actually wired to the public repo
- [ ] "Known gotchas" section — genuinely free (already written in PROJECT.md), fold into v1.1 if time allows, otherwise first fast-follow

### Future Consideration (v2+)

- [ ] Community/Discord section — defer until there is a community
- [ ] Translations — defer until non-English demand is observed
- [ ] Star history — defer indefinitely for a single-capability plugin; revisit only if adoption metrics justify it

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|----------------------|----------|
| Purpose statement | HIGH | LOW | P1 |
| Requirements | HIGH | LOW | P1 |
| Install commands | HIGH | LOW | P1 |
| Uninstall commands | HIGH | LOW | P1 |
| Caveats/limitations | HIGH | MEDIUM | P1 |
| Link to gsd-core/beads | HIGH | LOW | P1 |
| License | MEDIUM | LOW | P1 |
| Fail-open guarantee callout | MEDIUM | LOW | P2 |
| Binding-model summary | MEDIUM | LOW | P2 |
| Known-gotchas section | MEDIUM | LOW | P2 |
| Config reference table | LOW | LOW | P2 |
| CI badge | LOW | LOW | P3 |
| Community/Discord/star-history | LOW | LOW | P3 (defer) |
| Translations | LOW | MEDIUM | P3 (defer) |

**Priority key:**
- P1: Must have for this milestone's ship gate
- P2: Should have, cheap to add since content already exists in PROJECT.md
- P3: Explicitly deferred per Anti-Features above

## Competitor Feature Analysis

Comparable niche single-capability plugin/glue-tool READMEs (LSP plugins, `commit-commands`,
`plugin-dev` under `anthropics/claude-plugins-official`) were not individually fetchable (GitHub
tree view only, contents not retrievable via this session's tools) — treat this row as directional,
not verified line-by-line.

| Feature | Anthropic official small plugins (per docs description) | gsd-core (sibling, flagship-scale) | Our approach |
|---------|-----------------------------------------------------------|-------------------------------------|--------------|
| README length | Short — purpose, structure, usage, install pointer to marketplace | Long — badges, quickstart, docs index, community, star history | Short, closer to the official-plugin pattern; gsd-core's scale-appropriate furniture doesn't fit a single capability |
| Install docs | Delegates to the shared `/plugin install <name>@<marketplace>` convention, no bespoke script | Uses `npx @opengsd/gsd-core@latest` (own installer) | Use the shared `/plugin` convention — this is a plugin, not an installer-shipping framework |
| Trust/security framing | Implicit via Anthropic's own marketplace vetting | N/A (first-party) | Must be explicit — third-party plugin, no vetting badge to lean on |

## Sources

- [code.claude.com/docs/en/discover-plugins](https://code.claude.com/docs/en/discover-plugins) — official install/uninstall/disable command syntax, security warning language, version-gated behavior (LOW per this project's generic confidence classifier, which has no "official first-party docs" tier; treated as high-trust in practice as Anthropic's own current documentation)
- [code.claude.com/docs/en/plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) — plugin.json/marketplace.json required fields, directory layout, immutable-name rule
- [github.com/anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) — official plugin directory structure and example-plugin template (LOW confidence, WebFetch summarization only, page tree contents not independently verified)
- [github.com/RichardLitt/standard-readme](https://github.com/RichardLitt/standard-readme) (spec.md) — the closest thing to a codified README convention (Install/Usage/API/Maintainers/Contributing/License), used as the table-stakes baseline (LOW confidence, WebSearch summary only)
- [github.com/matiassingers/awesome-readme](https://github.com/matiassingers/awesome-readme) — curated high-quality README examples (LOW confidence, WebSearch summary only)
- `.planning/PROJECT.md` (this repo) — authoritative source for Requirements/Constraints/Key Decisions content; no external confidence rating applies, it is the project's own record
- `/home/dd/.claude/plugins/marketplaces/gsd-core/README.md` — direct read of the sibling/parent project's shipped README, used as the flagship-scale comparison point (read directly, not web-sourced)
- `/home/dd/Gemini/gsd-beads/.beads/README.md` — direct read of beads' own auto-generated README, used as the negative example for tone (read directly, not web-sourced)

All web-sourced findings in this file carry LOW confidence per this project's `classify-confidence`
seam (it has no tier above LOW for websearch/webfetch results). In practice the two official
`code.claude.com` fetches should be weighted higher than the community/summary sources — they are
Anthropic's own current documentation, fetched directly, not aggregated commentary — but the
tooling does not currently distinguish that. Flag for the roadmap: if a plugin-manifest or install-flow
detail in this file conflicts with what packaging work discovers hands-on, the hands-on result wins.

---
*Feature research for: Claude Code plugin README content*
*Researched: 2026-08-16*
