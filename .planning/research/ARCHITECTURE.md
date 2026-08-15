# Architecture Research: Claude Code Plugin Packaging for gsd-beads

**Domain:** Claude Code plugin manifest integration into an existing multi-runtime agent-config repo
**Researched:** 2026-08-16
**Confidence:** HIGH (official `code.claude.com/docs` fetched directly, corroborated by 3 independent
secondary sources; repo layout verified against `git ls-files`/`du`, not inferred)

## Standard Architecture

### How Claude Code resolves a plugin

```
┌──────────────────────────────────────────────────────────────────┐
│  Marketplace catalog (.claude-plugin/marketplace.json)            │
│  — lists plugins + where to fetch each one ("source")             │
└───────────────────────────┬────────────────────────────────────────┘
                             │ source: relative path | github | url |
                             │ git-subdir | npm | archive | command
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  Plugin root  (dir containing .claude-plugin/plugin.json)         │
│  ┌───────────┐ ┌──────────┐ ┌────────┐ ┌────────────┐            │
│  │ skills/   │ │commands/ │ │agents/ │ │hooks/*.json│  ...        │
│  └───────────┘ └──────────┘ └────────┘ └────────────┘            │
│  Everything here is COPIED VERBATIM into ~/.claude/plugins/cache  │
│  on every install (except symlinks resolving outside the copied   │
│  tree, which are skipped).                                        │
└──────────────────────────────────────────────────────────────────┘
```

Two manifests, two jobs — do not conflate them:

| File | Job | Cardinality |
|------|-----|-------------|
| `.claude-plugin/plugin.json` | Describes **one plugin**: its components (skills/commands/agents/hooks/mcpServers) and metadata | One per plugin |
| `.claude-plugin/marketplace.json` | A **catalog** users add with `/plugin marketplace add`; lists one or more plugins and where to fetch each | One per marketplace repo (can list 1 plugin — the "self-hosted, single-plugin marketplace" pattern) |

### Component Responsibilities

| Component | Responsibility | This repo's status |
|-----------|-----------------|---------------------|
| `.claude-plugin/plugin.json` | Plugin identity, version, and component path declarations | **New** |
| `.claude-plugin/marketplace.json` | Makes the repo `/plugin marketplace add`-able; declares the plugin entry's fetch `source` | **New** |
| `skills/` (default scan) or a custom `skills` path in `plugin.json` | User- and agent-invocable `SKILL.md` bundles | **Reused** — point at existing `.agents/skills/beads/`, do not duplicate |
| `hooks/hooks.json` | Declarative lifecycle hooks (SessionStart, PostToolUse, …) | **New** — lift the existing `bd prime --hook-json` SessionStart hook out of `.claude/settings.json` so plugin installers get it too |
| `.gsd/capabilities/beads/` | gsd-core's own capability-overlay format (`capability.json`, `steps[]`, `gates[]`) — a **different consumer, different loader**, installed via gsd-core's capability mechanism, not Claude's `/plugin install` | **Untouched** — not a Claude plugin component; ships as inert repo content alongside the plugin (see Integration Points) |

## Recommended Project Structure

```
gsd-beads/                                   # repo root == plugin root (single-plugin repo)
├── .claude-plugin/
│   ├── plugin.json            # NEW — the plugin manifest
│   └── marketplace.json       # NEW — self-hosted single-plugin marketplace catalog
├── hooks/
│   └── hooks.json             # NEW — SessionStart: `bd prime --hook-json` (mirrors .claude/settings.json)
├── .agents/skills/beads/      # EXISTING, UNCHANGED — referenced by plugin.json's `skills` path,
│   ├── SKILL.md               #   not moved, not duplicated (frontmatter already matches Claude's
│   └── agents/openai.yaml     #   SKILL.md schema — see "Cross-runtime skill" below)
├── .gsd/capabilities/beads/   # EXISTING, UNCHANGED — gsd-core capability overlay (separate
│   ├── capability.json        #   distribution channel; not a plugin component)
│   ├── scripts/sync.py
│   ├── skills/*/SKILL.md      #   gsd-core's own internal skills, invoked by gsd-core's step
│   └── tests/                 #   system at lifecycle points — NOT user-facing Claude skills
├── .claude/settings.json      # EXISTING, UNCHANGED — this repo's own dev-session hook; stays
│                               #   (separate from the plugin's shipped hooks/hooks.json — see
│                               #   Anti-Patterns)
├── README.md                  # NEW (separate milestone target, referenced here for ordering)
├── LICENSE                    # NEW — required for plugin.json's `license` field to mean anything
├── .planning/                 # EXISTING, UNCHANGED — this project's own GSD dev planning.
├── .beads/                    # EXISTING, UNCHANGED — this project's own local Dolt DB + hooks.
└── (packaging step excludes .planning/ and .beads/ from what ships — see Data Flow)
```

### Structure Rationale

- **`.claude-plugin/` at repo root, not a `plugins/<name>/` subtree.** This is a *single-plugin*
  repo, not a multi-plugin marketplace monorepo. The docs draw a hard line: `.claude-plugin/`
  contains only `plugin.json` (and, for a self-hosted marketplace, `marketplace.json`); every
  component directory (`skills/`, `commands/`, `agents/`, `hooks/`) lives at **plugin root**, one
  level up — nesting a component dir inside `.claude-plugin/` is the single most common
  reported mistake and fails silently (plugin loads, components go missing).
- **No new `skills/` directory.** `.agents/skills/beads/SKILL.md` already has Claude-Code-shaped
  frontmatter (`name:`, `description:`) — it *is* a valid `<name>/SKILL.md` bundle today. Claude's
  default scan only looks in `skills/`, not `.agents/skills/`, so `plugin.json` must declare a
  custom path: `"skills": "./.agents/skills/"` (custom `skills` paths *add to* the default scan
  rather than replacing it, and accept any relative path starting with `./`). Duplicating the file
  into a second `skills/beads/SKILL.md` would create two sources of truth for one skill — reject
  that per repo's own DRY posture.
- **`hooks/hooks.json` is new, `.claude/settings.json` is untouched.** They serve different
  consumers: `.claude/settings.json` configures *this repo's own* dev Claude session (already
  fires `bd prime --hook-json` on SessionStart); `hooks/hooks.json` is what ships *inside the
  plugin* and fires that same hook in any project where a user installs `gsd-beads`. Merging them
  would either strip the repo's own dev hook or leak plugin-authoring hook config into every
  installer — keep them separate, accept the harmless double-fire when this repo's own Claude
  session also has the plugin installed locally for dev/testing (idempotent command, no state risk).
- **`.gsd/capabilities/beads/` is not wired into `plugin.json`.** It has its own manifest format
  (`capability.json` with `steps[]`/`gates[]`/`contributions[]`) consumed by gsd-core's
  `capability-loader.cts`, an entirely different loader than Claude's plugin system. There is no
  Claude component type (`skills`/`commands`/`agents`/`hooks`/`mcpServers`) that maps onto a
  capability overlay. It stays in the repo as product payload for gsd-core users (installed via
  gsd-core's own capability-install path), and rides along in the plugin's copied tree as inert,
  harmless content — it is *not* on the exclusion list (unlike `.planning/`/`.beads/`, it is
  product code, not this project's internal meta-state).

## Architectural Patterns

### Pattern 1: Self-hosted single-plugin marketplace

**What:** A repo ships both `.claude-plugin/plugin.json` (the plugin) and
`.claude-plugin/marketplace.json` (a one-entry catalog whose `source` for that entry resolves to
the plugin's own packaged payload). This is the documented pattern for "one repo, one plugin,
marketplace-installable" — distinct from a monorepo marketplace that lists N plugins under
`plugins/<name>/`.
**When to use:** Exactly gsd-beads' case — one plugin, one repo, wants both
`/plugin install https://github.com/owner/gsd-beads` (direct) **and**
`/plugin marketplace add owner/gsd-beads` → `/plugin install gsd-beads@gsd-beads` (discoverable,
versioned, update-tracked) to work.
**Trade-offs:** Two JSON files to keep in sync (`plugin.json`'s own `version`, if set, is always
authoritative over any `version` set in the matching `marketplace.json` entry — set it in exactly
one place to avoid a masked mismatch).

**Example (`marketplace.json`):**
```json
{
  "name": "gsd-beads",
  "owner": { "name": "<author>" },
  "plugins": [
    {
      "name": "gsd-beads",
      "description": "bd (beads) issue tracking for Claude Code, plus a gsd-core capability overlay",
      "source": { "source": "archive", "url": "https://github.com/<owner>/gsd-beads/releases/download/v1.1.0/gsd-beads-plugin.zip" }
    }
  ]
}
```

### Pattern 2: Payload-selecting `archive` source (packaging exclusion mechanism)

**What:** Instead of pointing the marketplace entry's `source` at `"./"` (whole repo, whatever is
git-tracked at the pinned ref) or a `github`/`url` source (same effect — full clone becomes the
plugin root), point it at a release-built zip via `"source": "archive"`, built by explicitly
including only the plugin payload paths.
**When to use:** Whenever the plugin's git repo also carries files that must never reach an
installer's `~/.claude/plugins/cache` — exactly gsd-beads' situation (see Data Flow below for the
concrete numbers that make this non-optional here, not cosmetic).
**Trade-offs:** Requires a release-time build step (one `zip` invocation is enough at this scale)
versus zero-build direct-git install. In exchange it gives an **allowlist** of what ships
(`.claude-plugin/`, `hooks/`, `.agents/skills/`, `README.md`, `LICENSE`) instead of a denylist that
has to be kept in sync with every future dev-only directory added to the repo.

**Example (build step, run before tagging a release):**
```bash
zip -r gsd-beads-plugin.zip \
  .claude-plugin hooks .agents/skills README.md LICENSE
```
Relative paths inside the zip are preserved, so `plugin.json`'s `"skills": "./.agents/skills/"`
resolves identically whether the plugin is loaded from the raw repo (for `claude plugin validate`
during development) or from the built archive.

### Pattern 3: Cross-runtime skill reused, not forked

**What:** `.agents/skills/beads/` is this repo's existing cross-runtime skill convention — one
`SKILL.md` (frontmatter-compatible with Claude's schema) plus per-runtime metadata blocks
(`agents/openai.yaml` for OpenAI-family runtimes). Claude Code's plugin `skills` loader reads only
`<dir>/SKILL.md`; sibling files/subdirectories inside a skill directory are inert to it. That means
the *same* directory that already serves Codex/Cursor via `.agents/skills/beads/` can be pointed at
directly by `plugin.json` with zero forking and zero format translation.
**When to use:** Any time an existing cross-runtime skill's `SKILL.md` frontmatter already
satisfies Claude's schema (`name`, `description` — verified present in
`.agents/skills/beads/SKILL.md`).
**Trade-offs:** None identified — this is strictly additive reuse, not a compromise.

## Data Flow

### Install-time packaging flow

```
git tag v1.1.0
    ↓
build script: zip { .claude-plugin/, hooks/, .agents/skills/, README.md, LICENSE }
    ↓
gh release upload  →  gsd-beads-plugin.zip attached to the GitHub Release
    ↓
marketplace.json's plugin entry: source: {source: "archive", url: "<release asset url>"}
    ↓
user: /plugin marketplace add <owner>/gsd-beads
      /plugin install gsd-beads@gsd-beads
    ↓
Claude Code downloads + verifies the zip, unpacks into ~/.claude/plugins/cache/
    (contains ONLY the 5 allowlisted paths — .planning/, .beads/, .gsd/, docs/,
     .codex/, .cursor/, .git* never leave this repo)
```

### Why "must not ship `.planning/`" is a real constraint, not cosmetic

Verified against this repo's actual git-tracked state (`git ls-files`), not assumed:

| Path | Tracked files | Size | Ships in a **whole-repo** (`github`/`url`/`"./"`) plugin source? |
|------|---------------|------|---------------------------------------------------------------|
| `.planning/` | 82 files | 1.2 MB | Yes — includes phase PLAN/SUMMARY/REVIEW/VALIDATION docs, milestone audits, this repo's own `RETROSPECTIVE.md` |
| `.beads/` (tracked subset) | 22 files (`config.yaml`, `metadata.json`, `hooks/*`, `README.md`) | small | Yes — git hook scripts and Dolt metadata that are meaningless (and confusing) outside this exact repo |
| `.beads/embeddeddolt` (the actual issue DB) | **untracked** (already excluded, just not via `.gitignore` — verify before relying on this) | ~3.5 MB on disk | No — but only by accident of never having been `git add`ed, not by a documented exclusion rule |
| `.pytest_cache/`, `__pycache__/` | **untracked** (nested `.pytest_cache/.gitignore` + top-level `__pycache__/`/`*.pyc` rules already work) | — | No — already correctly excluded, no action needed |
| `.gsd/capabilities/beads/` | 15 files | 752 KB | Yes, and **intentionally** — this is product payload, not dev meta-state (see Structure Rationale) |

Total tracked repo weight is ~1.5 MB, of which `.planning/` alone is ~80%. A whole-repo plugin
source would hand every installer this project's internal phase-by-phase planning history,
decision logs, and milestone audits — the milestone context's exclusion requirement is about not
leaking a stranger's internal project-management trail into their own `~/.claude/plugins/cache`,
independent of the (modest) byte cost.

## Anti-Patterns

### Anti-Pattern 1: Nesting component directories inside `.claude-plugin/`

**What people do:** Put `skills/`, `commands/`, `hooks/` under `.claude-plugin/skills/` etc.,
reasoning "it's all plugin metadata."
**Why it's wrong:** `.claude-plugin/` is reserved for the manifest file(s) only. Components nested
there are silently never discovered — the plugin still loads (no error), just missing.
**Do this instead:** `.claude-plugin/plugin.json` only; `skills/`, `hooks/`, `commands/`, `agents/`
sit as direct siblings of `.claude-plugin/` at plugin root.

### Anti-Pattern 2: Relying on `.gitignore` to retroactively exclude already-tracked dev directories

**What people do:** Add `.planning/` and `.beads/` to `.gitignore` and assume that keeps them out
of a `github`/`url`-sourced plugin install.
**Why it's wrong:** `.gitignore` only prevents *future* `git add`s. Both directories are already
committed in this repo's history; a whole-repo clone at any tagged ref still contains them
regardless of a `.gitignore` entry added afterward. Actually excluding them requires either (a)
`git rm --cached -r` plus `.gitignore` (removes them from tracking going forward — a real
workflow change, since `PROJECT.md`'s Key Decisions table cites specific commits for `.planning/`
provenance), or (b) never letting the plugin source be "whole repo" in the first place (Pattern 2
above).
**Do this instead:** Use an `archive` (or `git-subdir`, if the payload is physically relocated into
its own subdirectory) marketplace source with an explicit file allowlist, so exclusion doesn't
depend on git-tracking history at all.

### Anti-Pattern 3: Symlinking a plugin's `skills/` across a `git-subdir` sparse clone boundary

**What people do:** To reuse `.agents/skills/beads/` from inside a dedicated `git-subdir`-sourced
plugin folder, symlink `plugin/skills/beads -> ../../.agents/skills/beads`.
**Why it's wrong:** `git-subdir` does a **sparse, partial clone** of only the declared subdirectory
path; the symlink's target may never be fetched, and Claude's own docs state a symlink resolving
**outside the copied plugin directory is skipped for security** during caching — so this either
breaks at clone time or silently drops the skill at cache time.
**Do this instead:** If choosing `git-subdir` over `archive`, physically place (or generate at
build time) the skill file inside the dedicated plugin subdirectory rather than reaching outside it
— or prefer the `archive` pattern (Pattern 2), which has no sparse-clone edge case at all.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `.claude-plugin/plugin.json` ↔ `.agents/skills/beads/` | `plugin.json`'s `"skills": "./.agents/skills/"` path field | One-directional reference, zero duplication; `.agents/skills/beads/agents/openai.yaml` is inert to Claude's loader |
| `.claude-plugin/plugin.json` ↔ `hooks/hooks.json` | Default `hooks/hooks.json` scan location (no custom `hooks` field needed) | New file; content mirrors (does not replace) the SessionStart hook already in `.claude/settings.json` |
| `.claude-plugin/marketplace.json` ↔ packaged archive | `source: {source: "archive", url: ...}` | Decouples "where `plugin.json` is authored" (repo root, for `claude plugin validate` during dev) from "what ships" (the release zip's allowlisted contents) |
| Claude plugin surface ↔ `.gsd/capabilities/beads/` | None (no shared component type) | Two independent distribution channels living in one repo; do not wire together, do not merge manifests |
| This repo's own `.claude/settings.json` ↔ shipped `hooks/hooks.json` | None (both independently fire the same idempotent `bd prime --hook-json` command) | Accept the harmless double-fire if this repo ever installs its own built plugin locally for dev-testing |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| GitHub (repo host + Releases) | Marketplace source repo (`/plugin marketplace add owner/gsd-beads`); Release asset hosts the packaged `archive` zip | Recommended host per docs (version control, issue tracking, release assets in one place) |
| `claude plugin validate ./` | CLI smoke test before publishing | Run with `--strict` in CI/pre-push to catch unrecognized-field typos as errors instead of silent warnings |

## Suggested Build Order

1. **`.claude-plugin/plugin.json`** — `name: "gsd-beads"` (not `"beads"` — avoid colliding in
   users' minds with the gsd-core capability id `"beads"`, and with any unrelated third-party
   `bd`/beads plugin), `version`, `description`, `author`, `license`, `skills: "./.agents/skills/"`.
   No dependencies — do first.
2. **`hooks/hooks.json`** — lift the SessionStart hook out of `.claude/settings.json` verbatim.
   Depends on (1) only in that `plugin.json`'s default `hooks/hooks.json` scan must find it.
3. **`LICENSE`** — needed for `plugin.json`'s `license` field and for the public-repo push already
   planned as a milestone target; no code dependency, but blocks (1) being fully meaningful.
4. **Packaging-exclusion decision + mechanism** (Pattern 2: `archive` build script, or the
   `git-subdir` relocation alternative) — must land **before** the first public GitHub push/tag,
   since it's what makes the "must not ship `.planning/`/`.beads/`" requirement actually true at
   the moment a stranger first installs. Depends on (1)+(2) existing (the zip needs something to
   include).
5. **`.claude-plugin/marketplace.json`** — one plugin entry, `source` set to whatever (4) produced
   (an `archive` URL, or a `git-subdir` path). Depends on (4)'s decision.
6. **`README.md`** — separate milestone target (purpose/install/deinstall/requirements/caveats);
   no hard code dependency on the above, but should reference the exact `/plugin marketplace add`
   / `/plugin install` commands only after (5) is real, so the copy-pasted commands in the README
   are verified working, not aspirational.
7. **`claude plugin validate ./ --strict`** — run after (1)-(3), and again against the unpacked
   archive after (4), as the acceptance check before tagging/pushing.

## Sources

- [Plugins reference — code.claude.com](https://code.claude.com/docs/en/plugins-reference) — fetched directly; manifest schema, directory-layout rules, symlink/path-traversal caching behavior, lockfile handling (HIGH confidence, primary source)
- [Create and distribute a plugin marketplace — code.claude.com](https://code.claude.com/docs/en/plugin-marketplaces) — fetched directly; marketplace.json schema, all plugin `source` types (`relative path`, `github`, `url`, `git-subdir`, `npm`, `archive`, `command`), strict-mode semantics, version-pinning rules (HIGH confidence, primary source)
- [Plugin Structure and Manifest — DeepWiki (anthropics/claude-plugins-official)](https://deepwiki.com/anthropics/claude-plugins-official/4.1-plugin-structure-and-manifest) — corroborating secondary source (MEDIUM confidence)
- [Plugin Structure and Conventions — DeepWiki (melodic-software/claude-code-plugins)](https://deepwiki.com/melodic-software/claude-code-plugins/6.1-plugin-structure-and-conventions) — corroborating secondary source (MEDIUM confidence)
- Repo state verified directly via `git ls-files`, `du -sh`, and `find` against this working tree (2026-08-16) — not inferred (HIGH confidence, primary evidence)

---
*Architecture research for: Claude Code plugin packaging, gsd-beads repo*
*Researched: 2026-08-16*
