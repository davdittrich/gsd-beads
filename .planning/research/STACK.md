# Stack Research

**Domain:** Claude Code plugin packaging & GitHub publishing (distribution tooling, not application code)
**Researched:** 2026-08-16
**Confidence:** MEDIUM (official docs fetched directly from code.claude.com and cross-checked against independent community sources; no Anthropic-versioned changelog was diffed against a specific Claude Code build, so exact field-availability version gates below are trusted from the docs page, not independently reproduced)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `.claude-plugin/plugin.json` manifest | schema current as of Claude Code v2.1.229+ docs | Declares the plugin's identity (`name`) and points Claude Code at the beads capability's existing skills | Only file Claude Code's plugin loader requires to recognize a directory as a plugin; `name` is genuinely the only mandatory field, so this is the minimum viable manifest |
| `.claude-plugin/marketplace.json` catalog | same schema family | Makes the same repo self-installable via `/plugin marketplace add <owner>/<repo>` — no separate marketplace repo needed | A single-plugin repo can be its own marketplace (`source: "./"` entry); this is a documented, supported pattern, not a workaround |
| GitHub repository (public) | — | Distribution transport — plugin/marketplace sources resolve as `github` (owner/repo shorthand) | Anthropic's own docs name GitHub as "the recommended way to host and distribute a marketplace"; `/plugin marketplace add owner/repo` is the shortest install path for a stranger |

### Supporting Libraries

None. This milestone adds zero runtime dependencies — `plugin.json` and `marketplace.json` are static JSON files interpreted by Claude Code itself, not by any package manager or build step.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `claude plugin validate ./` | Lints `plugin.json` against the schema before publishing | Run with `--strict` to turn unrecognized-field warnings into hard errors — catches typos (e.g. `discription`) that the default mode only suggests-corrects for |
| `hesreallyhim/claude-code-json-schema` (unofficial, on schemastore.org as `claude-code-plugin-manifest.json` / `claude-code-marketplace.json`) | Editor autocomplete/validation via `$schema` field | Optional — add `"$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json"` to `plugin.json` for IDE hints; ignored by Claude Code at load time, so it costs nothing to include and nothing to omit |

## Installation

Not an `npm install` — these are hand-authored JSON files placed in the repo. No package manager step exists in this pipeline:

```bash
# Structure to create (see Architecture section for exact placement)
mkdir -p .claude-plugin
# then write plugin.json and marketplace.json by hand (see field tables below)
```

## Manifest Schema — `plugin.json`

**Location:** `.claude-plugin/plugin.json` (this directory may contain *only* `plugin.json` — every other component directory sits at plugin root, not inside `.claude-plugin/`).

**Required field:** `name` (string, kebab-case) — this is the *only* mandatory field. Everything else is optional.

| Field | Type | Purpose | gsd-beads recommendation |
|---|---|---|---|
| `name` | string | Unique id, used for namespacing (`plugin-name:skill-name`) | `"beads"` — matches the capability id already registered in `.gsd-capabilities.json` |
| `version` | string | Semver; **pins the install** — users get updates only when this string changes | Start at `"0.1.0"` to match the capability's existing `version` in `.gsd-capabilities.json` |
| `description` | string | Shown in `/plugin` UI | One line: what beads-sync does for gsd's lifecycle |
| `author` | object | `{name}` required if present; `email`/`url` optional | `{"name": "..."}` |
| `homepage`, `repository`, `license` | string | Doc/source/license links | `repository` = the GitHub URL once pushed; `license` = SPDX id matching the `LICENSE` file |
| `keywords` | array | Discovery tags | e.g. `["gsd", "gsd-core", "beads", "task-tracking"]` |
| `skills` | string\|array | **Adds to** (does not replace) the default `skills/` scan | Set explicitly to `"./.gsd/capabilities/beads/skills/"` — the four existing skills (`beads-recall`, `beads-sync`, `beads-status`, `beads-migrate-todos`) live there, not at repo-root `skills/`, and moving them is out of scope for this milestone |
| `commands`, `agents`, `workflows`, `outputStyles` | string\|array | **Replace** the default scan for that component | Leave unset — gsd-beads ships no plugin-level slash commands or agents; setting these to an empty/absent value keeps default (empty) scans, which is correct since none exist |
| `metadata` | object | Free-form, unread by Claude Code | Skip — no known consumer for it in this project |
| `dependencies`, `userConfig`, `channels` | — | Plugin-to-plugin deps, config prompts, chat-bot channels | Skip — `beads` has one real runtime dependency (the `bd` binary), which is a `command-exists` *gate*, not a Claude Code plugin dependency; there is no field for "external CLI binary must be on PATH," so this stays documented in README, not the manifest |

### What NOT to set

| Field | Why not |
|---|---|
| `dependencies` | No other Claude Code *plugin* is required — `bd` is a system binary, out of this schema's scope entirely |
| `commands` / `agents` (declared but empty) | Declaring an empty array actively suppresses auto-discovery semantics for other tooling reading the manifest; simply omit the key |
| `userConfig` | No user-supplied secrets/config exist for this capability (config lives in `beads.*` gsd-core settings, not plugin install-time prompts) |
| `strict: false` (marketplace entry) | Would make the marketplace entry the sole source of truth and forbid `plugin.json` from declaring anything — the opposite of what's needed since `plugin.json` is the authoritative source here |

## Manifest Schema — `marketplace.json`

**Location:** `.claude-plugin/marketplace.json`, repo root (same `.claude-plugin/` directory as `plugin.json` is a valid, documented pattern for a single-plugin self-hosting repo — real-world precedent confirmed, e.g. MemoryStore's marketplace repo).

**Required top-level fields:** `name`, `owner` (object, `name` required), `plugins` (array).

```json
{
  "name": "gsd-beads",
  "owner": { "name": "<github-username-or-org>" },
  "plugins": [
    {
      "name": "beads",
      "source": "./",
      "description": "Syncs gsd's PLAN.md tasks to beads (bd) issues",
      "version": "0.1.0"
    }
  ]
}
```

Key rules that affect this repo specifically:
- `source: "./"` means "the marketplace root is also the plugin root" — correct here since there is exactly one plugin and it is the repo itself.
- **Reserved names are rejected**: `claude-code-marketplace`, `claude-code-plugins`, `anthropic-*`, and several others cannot be used as the marketplace `name` — `gsd-beads` is clear of all of them.
- Never declare `version` in *both* `plugin.json` and the marketplace entry — `plugin.json`'s value silently wins with no warning if they diverge, which would mask an intended bump. Pick one place; `plugin.json` is recommended since it travels with the plugin regardless of which marketplace lists it.

## Install Command (what a stranger runs)

```
/plugin marketplace add <github-owner>/gsd-beads
/plugin install beads@gsd-beads
```

This is the exact sequence the README's "Installation" section must document. `/plugin marketplace add` accepts GitHub `owner/repo` shorthand directly — no separate marketplace repo, no publishing to the official Anthropic catalog, and no approval/review step required for this path (that review process only applies to inclusion in Anthropic's curated `claude-plugins-official`/`claude-community` catalogs, which is explicitly out of scope for this milestone per PROJECT.md's goal of "installable... on GitHub").

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|--------------------------|
| Single repo self-hosts both `plugin.json` and `marketplace.json` at root (`source: "./"`) | Separate `plugins/beads/` subdirectory with its own nested `.claude-plugin/plugin.json`, marketplace at repo root | Use the nested form only if this repo will ever host a *second*, unrelated plugin — premature here since gsd-beads ships exactly one capability and nesting would relocate the existing `.gsd/capabilities/beads/` tree for no functional gain |
| `skills` field pointing at the existing `.gsd/capabilities/beads/skills/` path | Physically move/duplicate the four skill directories to a root-level `skills/` to match Claude Code's default auto-discovery path | Moving is a larger, riskier diff (breaks the gsd-core capability loader's expected path `.gsd/capabilities/<id>/`) for zero benefit — the explicit path field exists precisely to avoid this move |
| GitHub `owner/repo` self-hosted marketplace, no submission to Anthropic's official catalog | Submit to `claude-plugins-official` external-plugins review queue | Only worth it later if broader discoverability beyond direct GitHub install is desired; adds a multi-day review process and a `CODEOWNERS` file requirement that this milestone does not ask for |
| Static `.mit`/`Apache-2.0` `LICENSE` + plain README | Automated marketplace-scanning tooling (e.g. `ccpi` CLI generators) to scaffold the manifest | Those tools solve "publish many plugins fast"; gsd-beads has exactly one plugin and hand-writing ~15 lines of JSON is faster than adopting a generator dependency |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| A `CODEOWNERS` file | Only required for submissions into Anthropic's official/community marketplace review queue — not for a self-hosted GitHub marketplace, which is this milestone's actual target | Skip it; add later only if submitting to the official catalog |
| `strict: false` in the marketplace entry | Forces the marketplace entry to be the sole component definition and forbids `plugin.json` from declaring `skills` — breaks the explicit skills-path override this repo needs | Default `strict: true` (or omit the field) |
| Placing `commands/`, `agents/`, or `skills/` directories inside `.claude-plugin/` | Directly contradicts the documented structural rule; Claude Code will not discover components placed there | Keep `.claude-plugin/` containing only `plugin.json` (and, for this repo, `marketplace.json`); everything functional stays at existing paths under `.gsd/capabilities/beads/` |
| GitHub topic tag `claude-code-marketplace` alone for discoverability | Ecosystem discoverability is fragmented across 5–6 overlapping, non-canonical topic tags (`claude-code-plugin`, `claude-code-plugin-marketplace`, `claude-marketplace`, `claude-plugins`, `claude-code-plugins-marketplace`) — no single tag is authoritative | Apply the topic *set*: `claude-code-plugin`, `claude-code-plugin-marketplace`, `claude-plugins` — stacking multiple tags is the observed real-world convention, not over-tagging |

## GitHub Repo Conventions for Discoverability

| Convention | Status for gsd-beads | Action |
|---|---|---|
| Public repository | Not yet — no git remote configured (per milestone context) | Required before `/plugin marketplace add` can work for anyone but the author; must be public unless distributed only through org-managed settings |
| `LICENSE` file | Missing | Add one (MIT or Apache-2.0 are the two community-observed defaults for open-source Claude Code plugins) — referenced by `plugin.json`'s `license` field |
| `README.md` | Missing (this milestone's own deliverable) | Must cover: what it does, install command (`/plugin marketplace add` + `/plugin install`), requirements (`bd` on PATH, gsd-core `>=1.6.0`), uninstall, link to gsd-core — this is both a UX requirement and a documented trust signal reviewers/users check before installing a plugin that ships hooks/scripts |
| GitHub topics | Not set (no remote yet) | Set after push: `claude-code-plugin`, `claude-code-plugin-marketplace`, `claude-plugins`, `gsd`, `beads` |
| Releases / tags | None yet | Optional for this milestone — `version` pinning in `plugin.json` works without GitHub Releases; a tagged `v0.1.0` release is a nice-to-have that lets the marketplace entry's `source.ref` pin to a tag instead of tracking `main`, but is not required for `/plugin install` to work |
| `${CLAUDE_PLUGIN_ROOT}` path discipline | N/A — this plugin ships no hooks/scripts referencing plugin-relative paths outside `.gsd/capabilities/beads/` | Confirm at implementation time that nothing in the capability's `scripts/` assumes an absolute repo-root path that would break once the plugin is copied into `~/.claude/plugins/cache/` on install |

## Version Compatibility

| Component | Compatible With | Notes |
|-----------|------------------|-------|
| `plugin.json` `skills` explicit-path field | Any Claude Code version supporting the plugin system (component path overrides are core, not gated behind a specific version note in the docs) | No version floor found for this specific field beyond general plugin-system availability |
| `defaultEnabled`, `displayName`, `relevance` | Require Claude Code v2.1.154+, v2.1.143+, v2.1.152+ respectively | None of these are needed for this milestone's minimal manifest — noted only so a future editor doesn't add them assuming universal support |
| `archive` / `command` plugin sources | Require v2.1.224+ / v2.1.229+ | Irrelevant here — gsd-beads uses a plain relative-path source (`"./"`), which has no version gate |

## Sources

- https://code.claude.com/docs/en/plugins-reference — fetched directly (WebFetch), full `plugin.json` schema, directory structure, versioning resolution order — MEDIUM confidence (official docs, single fetch, not diffed against a live Claude Code binary)
- https://code.claude.com/docs/en/plugin-marketplaces — fetched directly (WebFetch), full `marketplace.json` schema, plugin source types, install command semantics, reserved-name list — MEDIUM confidence
- WebSearch corroboration across `hesreallyhim/claude-code-json-schema`, `anthropics/claude-code` reference repo, `systemprompt.io` publishing guide, GitHub topic pages — used to cross-check field lists and discoverability conventions, not as primary source
- Repo layout verified directly: `find .gsd/capabilities/beads -maxdepth 3 -type d` — confirms actual skill paths this manifest must reference

---
*Stack research for: Claude Code plugin packaging + GitHub publishing*
*Researched: 2026-08-16*
