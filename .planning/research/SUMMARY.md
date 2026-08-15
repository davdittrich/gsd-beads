# Project Research Summary

**Project:** gsd-beads (GitHub publication & Claude Code plugin packaging)
**Domain:** Claude Code plugin publishing for an existing gsd-core capability
**Researched:** 2026-08-16
**Overall Confidence:** HIGH

## Executive Summary

Publishing gsd-beads as a Claude Code plugin is fundamentally a **packaging and documentation problem**, not an engineering problem — the capability code already exists at v1.0 (14 requirements, fully built). The research discovered two distinct, independent distribution channels that must not be conflated: Claude Code's native plugin system (which will copy the repo into `~/.claude/plugins/cache/` on install) and gsd-core's capability loader (which resolves from `.gsd/capabilities/beads/` in each project). The critical risk is an architecture mismatch where a naive `plugin.json` ships a capability that Claude can cache but gsd-core cannot find, leaving users with a non-functional install. Prevention is explicit: the packaging phase must decide whether to (a) wrap the capability with a native plugin shell that bridges the two install flows, or (b) document a non-`/plugin` install path entirely. Separately, the first public push must pass a **hard `git ls-files` audit** before touching GitHub, since tracked dev-state files (`.beads/`, `.claude/.headroom_wrap_marker.json`, `.gsd-capabilities.json`, plus untracked Dolt backups) must not leak into an installer's machine.

The recommended approach is a **self-hosted single-plugin marketplace** pattern: ship both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` at repo root, with marketplace entry pointing to an `archive` source (a release-built zip with an explicit allowlist of what ships). This keeps `.planning/` and `.beads/` entirely out of the installed plugin, avoids symlink pitfalls, and makes both `/plugin marketplace add owner/gsd-beads` and direct repo cloning work correctly. The README becomes the trust anchor — it must document exact prerequisites (`bd` binary on PATH, gsd-core >=1.6.0), exact install/uninstall commands, the fail-open behavior, and be validated by an actual clean-environment install test before any push, since a disconnect between documented and actual install paths is the #1 reason strangers lose trust in a new plugin.

## Key Findings

### Recommended Stack

No runtime dependencies. The entire plugin manifest is hand-authored static JSON (`plugin.json` and `marketplace.json`) interpreted by Claude Code's built-in plugin loader. Distribution is GitHub-hosted (repo + Releases for archive assets).

**Core components:**
- `.claude-plugin/plugin.json` manifest — declares plugin identity (`name: "gsd-beads"`), component paths, and metadata; references `.agents/skills/beads/` (existing cross-runtime skill, reused without duplication)
- `.claude-plugin/marketplace.json` catalog — makes `/plugin marketplace add owner/gsd-beads` work; single-plugin repo pattern with `source: "./"` or archive URL
- GitHub repository (public) — hosts manifest and releases archive zip; recommended distribution transport per Anthropic's docs
- `hooks/hooks.json` — new, lifts the SessionStart `bd prime --hook-json` hook from `.claude/settings.json` so installers get it too
- `LICENSE` file (MIT or Apache-2.0) — required by GitHub's OSS detection and referenced in `plugin.json`'s `license` field
- `README.md` — separate deliverable, covers purpose/install/uninstall/requirements/caveats

**Development tools:**
- `claude plugin validate . --strict` — mandatory linting before every push; catches field typos that default mode only warns about

**Why this stack:**
- Zero external dependencies: JSON manifests are static (no build, no package managers, no runtime deps)
- Official schema: all fields documented directly by Anthropic at `code.claude.com/docs/en/plugins-reference`
- Archive pattern: explicit allowlist of shipped files (avoids `.gitignore` brittleness and `.planning/`/`.beads/` leakage)
- Reuse existing `.agents/skills/beads/`: already has Claude-compatible `SKILL.md` frontmatter; moving it is a larger diff for zero functional gain

### Expected Features (README Content)

**Must have (users cannot evaluate/install without these):**
- One-line purpose statement (reuse PROJECT.md's "What This Is")
- Requirements: `bd` binary on PATH, Python 3 stdlib only, gsd-core `>=1.6.0`
- Install instructions (`/plugin marketplace add`, `/plugin install`)
- Uninstall instructions (`/plugin uninstall`)
- Links to gsd-core and steveyegge/beads upstream
- Caveats/limitations (fail-open behavior, authoritative sync_mode, consent-hash gotcha)
- License section

**Should have (differentiators, low cost since content exists in PROJECT.md):**
- Explicit fail-open guarantee callout
- Binding-model summary (phase↔epic, task↔issue, dependency↔`bd dep add`)
- "Known gotchas we hit" section (real incidents from PROJECT.md Key Decisions)
- CI badge (defer until test workflow wired to public repo)

**Anti-features (avoid these):**
- Full architecture/API deep-dive inline (link to PROJECT.md instead)
- Marketing tone / emoji headers
- Star history / community furniture (scale-inappropriate)
- Multi-language translations (zero non-English demand)

### Architecture Approach

Two independent distribution channels coexist in one repo and must not be merged:

1. **Claude Code plugin surface** (new): `.claude-plugin/plugin.json` + marketplace.json, `hooks/hooks.json`, re-referenced `.agents/skills/beads/SKILL.md`, unpacked into `~/.claude/plugins/cache/` on `/plugin install`
2. **gsd-core capability overlay** (existing, unchanged): `.gsd/capabilities/beads/` installed via gsd-core's own `capability-loader.cts`, resolving from each project's `.gsd/capabilities/` directory

**Critical integration point:** Claude Code's plugin system does *not* know how to resolve a gsd-core capability overlay. If packaging simply drops a `plugin.json` at repo root without a bridge, `/plugin install` will succeed (Claude caches the repo), but the capability won't be where gsd-core's loader looks for it. **Decision required in packaging phase:** either (a) add a postinstall hook / `bd prime` SessionStart hook that bridges the two install flows, or (b) document a non-`/plugin` install path entirely.

**Major components:**
1. `.claude-plugin/plugin.json` — Plugin identity, version "0.1.0", description, author, license, `skills: "./.agents/skills/"` (points at existing skill, does not duplicate)
2. `.claude-plugin/marketplace.json` — Catalog declaring one plugin entry with `source: "./"`  or archive URL
3. `hooks/hooks.json` — Lifts SessionStart `bd prime --hook-json` from `.claude/settings.json` verbatim; idempotent with repo's own dev-session hook
4. `.agents/skills/beads/SKILL.md` — Reused as-is; contains Claude-compatible frontmatter already
5. `.gsd/capabilities/beads/` — Rides along as inert product payload; gsd-core users install via separate capability mechanism

**Recommended pattern:** Self-hosted single-plugin marketplace with archive source. Build order: (1) plugin.json → (2) hooks.json → (3) LICENSE → (4) archive zip (allowlist) → (5) marketplace.json → (6) README → (7) validation.

### Critical Pitfalls

**1. Capability-loader vs native-plugin mismatch**
- Risk: Ship plugin.json without bridging capability-loader; users install plugin, see no skills, assume broken
- Prevention: Decide *before* writing plugin.json: (a) add bridge (postinstall/SessionStart hook) or (b) document non-`/plugin` install path
- Phase: Packaging phase — this is architecture decision, not patch-later detail
- Test: Real `/plugin install` on clean project; `bd`-related skills must appear in `/help`

**2. First public push leaks machine-local dev/runtime state**
- Risk: `.beads/config.yaml`, `.beads/metadata.json`, `.claude/.headroom_wrap_marker.json`, `.gsd-capabilities.json` (integrity=""), untracked `.beads.backup-pre-recovery/` (2.7 MB) all exposed to plugin installers
- Prevention: Hard `git ls-files` audit before first push; untrack `.beads/*`, extend `.gitignore` for backup patterns, untrack `.headroom_wrap_marker.json` and `.gsd-capabilities.json`
- Phase: Pre-push audit phase (explicit, gated step) — window closes after first push to GitHub
- Flag: Review `git status` for untracked 2.7 MB directories before any push

**3. Shipping plugin.json without marketplace.json**
- Risk: Claude Code has no direct "install repo as plugin" command; `/plugin marketplace add owner/repo` fails with file-not-found
- Prevention: Ship both manifests; self-hosted pattern with `.claude-plugin/marketplace.json` at repo root
- Phase: Packaging phase — validate locally with `claude plugin validate .` and real `/plugin marketplace add ./` round trip before pushing

**4. Manifest field-name/type mistakes fail silently**
- Risk: Default `claude plugin validate` reports warnings only; typos like `"authors"` instead of `"author"` silently fail; `author` must be object (not string), `license`/`repository` must be strings (not objects)
- Prevention: Always run `claude plugin validate . --strict` before every push that touches manifest
- Phase: Packaging phase — mandatory mechanical validator gate
- Flag: --strict mode required; default mode insufficient

**5. Version pinning mistakes strand users**
- Risk: (a) Declaring `version` in both plugin.json and marketplace.json; Claude prefers plugin.json silently, or (b) forgetting to bump version; stale installs cached forever
- Prevention: Pick one authority and document: either (a) never set version in marketplace.json OR (b) omit version entirely (git SHA gates updates)
- Phase: Packaging phase (policy decision) and one test cycle
- For this milestone: omit version or use git SHA; revisit once external installs exist

**6. README claims outrun what a fresh install does**
- Risk: README documents "install beads, done" without mentioning `bd` binary, gsd-core >=1.6.0, or capability-loader bridge; stranger installs on clean machine, sees no skills, loses trust
- Prevention: Write README only after literal install/removal on machine with zero prior `bd`, gsd-core state; state explicitly: prerequisites, exact commands, fail-open behavior
- Phase: README phase (separate deliverable) — gated on clean-environment dry run before shipping
- Flag: No one has run README's install steps from machine without this project's prior state (mandatory)

## Implications for Roadmap

Suggested phase structure (6 phases):

### Phase 1: Plugin Manifests & Core Packaging
**Rationale:** Architectural prerequisites — everything else depends on decisions here. Cannot test architecture until manifests exist.
**Delivers:** 
- `.claude-plugin/plugin.json` with name "gsd-beads", version "0.1.0", skills path "./.agents/skills/", license field
- `.claude-plugin/marketplace.json` with self-hosted marketplace entry
- Architecture bridge decision (Pitfall 1): implicit in plugin.json field choices
- Validation: `claude plugin validate . --strict` passes

**Research needed:** None — schema fully documented at code.claude.com; decision on bridge design

### Phase 2: Payload Packaging & Release Pipeline
**Rationale:** Once manifests decided, implement "what ships". Archive (allowlist) pattern prevents `.planning/`/`.beads/` leakage.
**Delivers:**
- Build script: `zip -r gsd-beads-plugin.zip .claude-plugin hooks .agents/skills README.md LICENSE`
- GitHub Release asset tagged v0.1.0
- Updated marketplace.json with `source: {source: "archive", url: ...}`

**Implements:** Architecture pattern (archive source with explicit allowlist)

**Avoids:** Pitfall 2 (leaked dev state) — archive makes `.gitignore` irrelevant by using allowlist

**Research needed:** None — archive mechanism fully documented in Architecture research

### Phase 3: Git Cleanup & Repository Audit
**Rationale:** Before first push to GitHub, audit tracked files. This window closes after first public push (history rewrite becomes breaking change). Must complete *before* Phase 4.
**Delivers:**
- `git ls-files` audit reviewed line-by-line against "does installer need this?"
- Untracked `.beads.backup-pre-recovery/`, `.beads/interactions.jsonl` gitignored
- `.beads/config.yaml`, `.beads/metadata.json` untracked
- `.claude/.headroom_wrap_marker.json`, `.gsd-capabilities.json` untracked
- `.gitignore` extended to cover `*.backup*`, `*-pre-recovery*` patterns

**Avoids:** Pitfall 2 (leaked dev state)

### Phase 4: Hooks & Lifecycle Integration
**Rationale:** SessionStart hook must be in `hooks/hooks.json` so installers get git hook setup. Resolves Pitfall 1 (capability-loader bridge).
**Delivers:**
- `hooks/hooks.json` with SessionStart hook, content identical to existing `.claude/settings.json` hook
- Bridge mechanism explicit (from Phase 1 ADR): postinstall hook OR documented manual `gsd capability install` step
- Validation: Hook fires idempotently

**Avoids:** Pitfall 1 (capability-loader mismatch) — bridge now explicit

**Research needed:** Hands-on: postinstall hook environment/API if choosing hook-based bridge

### Phase 5: README & Documentation
**Rationale:** Write after all technical phases, validated by clean-environment install test. README is trust anchor.
**Delivers:**
- README.md: purpose, requirements (`bd` on PATH, Python 3, gsd-core >=1.6.0), install/uninstall commands, links, caveats, license
- Clean-environment install test: install, verify skills appear, remove, confirm cleanup
- README transcribed from verified commands, not aspirational

**Addresses:** All table-stake features from FEATURES.md; should-have differentiators if time allows

**Avoids:** Pitfall 6 (README/reality mismatch) — tested on clean machine first

### Phase 6: License & Final Validation
**Rationale:** Lightweight but necessary — LICENSE file required for GitHub OSS detection and plugin.json `license` field. Final ship gate.
**Delivers:**
- LICENSE file at repo root (MIT or Apache-2.0)
- `claude plugin validate . --strict` clean
- `/plugin marketplace add ./` + `/plugin install gsd-beads@gsd-beads` succeeds locally
- Archive zip validation: contains only allowlisted paths, no `.planning/`/`.beads/`

**Avoids:** All pitfalls (comprehensive checklist pass before release)

### Phase Ordering Rationale

1. **Manifests first (Phase 1):** Architectural decisions gate everything; must decide before implementing
2. **Packaging mechanism (Phase 2):** Depends on Phase 1 decisions
3. **Git cleanup (Phase 3):** One-time-only step; window closes after first push; must happen before Phase 4
4. **Hooks & bridge (Phase 4):** Implements critical integration (capability-loader bridge); needs Phase 1 decision
5. **Documentation (Phase 5):** Can only validate after Phases 1-4 real and testable; cannot write accurate install commands until install actually works
6. **License & validation (Phase 6):** Ship gate; depends on all prior phases

### Research Flags

Phases likely needing deeper research:
- **Phase 1:** Capability-loader bridge design (Pitfall 1) — decide between postinstall-hook strategy vs. documented separate `gsd capability install` step before writing plugin.json
- **Phase 4:** If choosing postinstall-hook bridge, research how Claude Code's plugin system invokes postinstall hooks, environment variables available, symlink persistence across cache invalidation

Phases with standard patterns (skip research-phase):
- **Phase 2:** Archive mechanism fully documented in Architecture research
- **Phase 3:** Standard git hygiene; no research needed
- **Phase 5:** Content sourced from PROJECT.md and FEATURES.md research
- **Phase 6:** License selection is choice (MIT/Apache-2.0); validation commands are mechanical

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| **Stack** | HIGH | Official `code.claude.com/docs` fetched directly; manifest schema, `plugin validate` tool, no external dependencies all verified against primary sources |
| **Features** | MEDIUM | Table-stake features from official Anthropic docs (HIGH); README content research used websearch summary sources (LOW). Core install/uninstall commands official, competitive differentiators community-consensus only |
| **Architecture** | HIGH | Official `code.claude.com/docs` for plugin system; repo layout verified directly against `git ls-files` and working tree; archive pattern corroborated by secondary sources |
| **Pitfalls** | HIGH | Critical pitfalls sourced from official Claude Code docs + direct git state inspection + corroboration with PROJECT.md; Pitfall 1 (capability-loader bridge) is MEDIUM-HIGH (inference from comparing two independent systems, but reasoning sound) |

**Overall confidence:** HIGH

### Gaps to Address

- **Pitfall 1 bridge design:** Research identified risk but not *how* to bridge native-plugin install with gsd-core capability resolution. Must decide explicitly before Phase 1. Recommended: SessionStart hook or documented manual step, but exact mechanism needs Phase 1 discussion
- **Postinstall hook environment/API:** If choosing postinstall-hook bridge, research did not verify what Claude Code passes to postinstall hooks (env vars, working directory, `${CLAUDE_PLUGIN_ROOT}` availability). Phase 4 will need hands-on experimentation
- **Clean-environment test logistics:** Phase 5 assumes clean machine for install/removal testing. Setting one up (VM, container, fresh OS user) not specified in research; Phase 5 planning must address

## Sources

### Primary (HIGH confidence)
- code.claude.com/docs/en/plugins-reference — official plugin.json/marketplace.json schema, directory structure, version resolution, caching behavior
- code.claude.com/docs/en/plugin-marketplaces — official marketplace catalog schema, plugin source types (archive, git-subdir, npm, command, relative path)
- .planning/PROJECT.md — authoritative project scope, constraints (N5 no extra deps, engines.gsd >=1.6.0, fail-open), Key Decisions table with real incidents
- Direct repo inspection: `git ls-files`, working-tree state, `.gitignore` coverage

### Secondary (MEDIUM confidence)
- code.claude.com/docs/en/discover-plugins — official install/uninstall/update command syntax
- anthropics/claude-plugins-official — official plugin template and examples (WebFetch summary)
- Standard-readme spec and curated examples — community best practices for plugin/tool READMEs

### Tertiary (LOW confidence, needs validation)
- WebSearch summaries of Claude plugin best practices — community consensus but no official authority
- GitHub topic-tag analysis — community-driven, non-canonical guidance

---

*Research completed: 2026-08-16*
*Ready for roadmap planning: yes*
