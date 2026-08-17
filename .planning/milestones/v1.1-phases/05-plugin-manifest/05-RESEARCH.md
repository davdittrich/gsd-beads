# Phase 5: Plugin Manifest - Research

**Researched:** 2026-08-16
**Domain:** Claude Code plugin packaging (`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json`), self-hosted marketplace distribution, MIT licensing
**Confidence:** HIGH — every schema claim below was fetched directly from `code.claude.com/docs/en/plugins-reference` and `code.claude.com/docs/en/plugin-marketplaces` this session and is quoted verbatim; the one open item (author-object shape) is explicitly flagged, not silently assumed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Plugin identity (plugin.json)**
- **D-01:** `name` field is `beads` — matches the capability id (`.gsd/capabilities/beads/`) and the install command from REQUIREMENTS.md PUB-02 (`/plugin install beads@gsd-beads`), not the repo name `gsd-beads`.
- **D-02:** `author` field is `davdittrich@gmail.com` (email only, no name object).
- **D-03:** `version` starts at `0.1.0` — matches `capability.json`'s current version rather than jumping to `1.0.0`.

**LICENSE**
- **D-04:** MIT `LICENSE` copyright line reads: `Copyright (c) 2026 Dennis A. V. Dittrich` — **Reversibility:** reversible — cosmetic text change, no downstream dependency.

**Marketplace entry (marketplace.json)**
- **D-05:** Entry id/name is `beads`, same as plugin.json's `name` — one identity across manifest and marketplace, matches PUB-02's install command.
- **D-06:** Entry `description` is a short, friendly install-page blurb written fresh for browsing installers (e.g. "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle") — NOT the verbatim PROJECT.md "Core Value" sentence, which is denser/more jargon-heavy than a marketplace listing needs.
- **D-07:** Source in this phase stays a relative local path (`./`) — per PROJECT.md's note, PUB-02 is authored here and re-pointed at the release archive URL in Phase 8. Do not point at a GitHub URL yet.

**Skills-path mechanism**
- **D-08:** How `plugin.json` references `.agents/skills/beads/` without a duplicated copy is left to `gsd-phase-researcher` — find what Claude Code's plugin schema actually supports (relative path in a `skills` field, symlink, etc.) rather than guessing now. Whatever mechanism the researcher confirms is binding; do not invent a second mechanism during planning.
  **RESOLVED BY THIS RESEARCH (see Architecture Patterns → Pattern 1):** `plugin.json` declares `"skills": ["./.agents/skills/beads"]` — a plain relative-path string field, no symlink, no copy.

**Validation strategy**
- **D-09:** Phase verification runs `claude plugin validate . --strict` **twice**: once with `marketplace.json` temporarily moved/absent (this is the mode that actually checks skill frontmatter, per ROADMAP.md success criterion 1's explicit wording), and once in the normal repo state. Both runs must exit clean before the phase is considered done — a single normal-state run is not sufficient evidence given the known false-green gotcha.
  **CONFIRMED BY THIS RESEARCH as mechanically correct** — see Common Pitfalls → Pitfall 1 for the exact verbatim doc quote proving why the two runs check different things.

### Claude's Discretion
- Exact JSON formatting/key ordering in `plugin.json` and `marketplace.json`.
- Whether `LICENSE` uses the canonical MIT template verbatim or a lightly reformatted equivalent (content, not wording, is what's decided above).

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. No scope-creep suggestions came up.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUB-01 | `.claude-plugin/plugin.json` declares plugin identity (name, version, license, author), points `skills` at existing `.agents/skills/beads/`, and passes `claude plugin validate . --strict` | Standard Stack (schema), Architecture Patterns Pattern 1 (skills-path mechanism), Pitfall 1 (validate two-mode gotcha), Code Examples |
| PUB-02 | `.claude-plugin/marketplace.json` self-hosted entry makes `/plugin marketplace add <owner>/gsd-beads` then `/plugin install beads@gsd-beads` work | Architecture Patterns Pattern 2 (marketplace schema), Pitfall 2 (relative-path/URL-marketplace mismatch), Code Examples |
| PUB-08 | `LICENSE` file (MIT) present at repo root, referenced in `plugin.json`'s `license` field | Standard Stack (`license` is a plain SPDX string, verified), Code Examples (MIT template) |
</phase_requirements>

## Summary

This phase produces three static artifacts — `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `LICENSE` — with no runtime code and no external package dependencies. The schema for both manifests is fully documented at `code.claude.com/docs/en/plugins-reference` and `code.claude.com/docs/en/plugin-marketplaces`; every field this phase needs was fetched and quoted verbatim this session (Claude Code CLI `2.1.233` confirmed installed locally via `claude --version`).

Three findings materially change what CONTEXT.md assumed or left open:

1. **The `claude plugin validate` two-mode gotcha is real and mechanically explained**, not folklore. The docs state outright that the YAML-frontmatter check and the `hooks/hooks.json` check are "**Reported only when validating a plugin directory**" — and a directory is classified as a "marketplace directory" the moment `.claude-plugin/marketplace.json` exists inside it, which routes validation down a different path that checks `marketplace.json` schema + cross-references `plugin.json`, but never opens `.agents/skills/beads/SKILL.md`. Since this repo's plugin and marketplace manifests live in the same `.claude-plugin/` directory, `claude plugin validate .` in the repo's normal state is always in "marketplace directory" mode and structurally cannot see frontmatter errors. D-09's double-run is the only way to exercise both code paths.

2. **The skills-path mechanism (D-08) has an exact, documented answer**, not a general "relative path or symlink" hand-wave: `plugin.json`'s `skills` field accepts an array of paths, and — critically — a path may point **directly** at a directory containing `SKILL.md` (not just a parent-of-named-subdirectories). The invocation name comes from the SKILL.md frontmatter's `name:` field, not the directory name. `.agents/skills/beads/SKILL.md` has `name: beads` (verified by reading the file), so `"skills": ["./.agents/skills/beads"]` in `plugin.json` is sufficient — no symlink, no copy, no restructuring of `.agents/skills/`.

3. **D-02's `author` field as "email only, no name object" conflicts with the documented schema for the `author` object**, which lists `name` as required when the object is present (marketplace-entry `author` field documentation, applies identically to `plugin.json`'s `author`). This is flagged, not silently resolved — see Open Questions.

**Primary recommendation:** Author `plugin.json` and `marketplace.json` by hand from the verified schema below (no scaffolding tool needed — `claude plugin init` scaffolds a new plugin under `~/.claude/skills/<name>/`, the wrong location for this repo-as-plugin layout). Run `claude plugin validate . --strict` in both marketplace-present and marketplace-absent states as the phase's actual test suite; there is no other executable verification surface in this phase.

## Architectural Responsibility Map

This phase is repo-packaging/metadata work, not a multi-tier application — the standard Browser/Frontend-Server/API/CDN/DB tiers do not apply. The table below maps each capability to the conceptual layer that owns it in Claude Code's plugin system instead.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Plugin identity (name/version/license/author) | `plugin.json` manifest (plugin root) | — | `plugin.json` is the sole authority for these fields per the plugin schema; nothing else in the repo declares them |
| Marketplace listing (discoverability, install-page copy) | `marketplace.json` catalog (marketplace root) | `plugin.json` (supplements when `strict: true`, the default) | Marketplace entry is what `/plugin marketplace add` reads; it is a separate file from `plugin.json` by design (marketplace source vs. plugin source are different concepts per the docs) |
| Skill resolution (`.agents/skills/beads/` → invocable skill) | `plugin.json`'s `skills` field | `.agents/skills/beads/SKILL.md` frontmatter (supplies the invocation name) | The manifest field is a pointer; the actual name authority lives in the skill file's own frontmatter, not the manifest |
| License text and reference | `LICENSE` (repo root, plain text) | `plugin.json`'s `license` field (SPDX string pointer) | The file is the legal artifact; the manifest field is a machine-readable pointer to it, not a copy of its content |
| Validation | `claude plugin validate` CLI (local, no network) | — | Runs entirely against the local filesystem; no service boundary involved |

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|---------------|
| `claude` CLI | `2.1.233` (confirmed installed via `claude --version`) [VERIFIED: local `claude --version` output] | Validates and exercises the plugin/marketplace manifests (`claude plugin validate`, `/plugin marketplace add`, `/plugin install`) | It is the only tool that reads these manifest formats; there is no independent JSON Schema validator distributed for this that covers the full semantic rule set (kebab-case checks, reserved-name checks, frontmatter parsing) |
| `.claude-plugin/plugin.json` | Schema documented at `code.claude.com/docs/en/plugins-reference` [CITED: code.claude.com/docs/en/plugins-reference] | Declares plugin identity and component paths | Anthropic's own required manifest format for Claude Code plugins — no alternative format exists |
| `.claude-plugin/marketplace.json` | Schema documented at `code.claude.com/docs/en/plugin-marketplaces` [CITED: code.claude.com/docs/en/plugin-marketplaces] | Declares the self-hosted marketplace catalog and its plugin entries | Same — required format for `/plugin marketplace add` to work at all |

### Supporting

None. This phase installs zero npm/pip/cargo packages — both manifests are hand-authored static JSON, and `LICENSE` is a static text file. The **Package Legitimacy Gate is not applicable to this phase.**

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-authoring `plugin.json`/`marketplace.json` from the documented schema | `claude plugin init <name>` scaffolder | Scaffolds a **new** plugin directory under `~/.claude/skills/<name>/`, not in-place at an existing repo root — wrong target location for "this repo becomes the plugin" (this repo's `.claude-plugin/` must live at the existing repo root, not a fresh scaffold elsewhere). Not usable here without a manual merge step that adds no value over hand-authoring directly. |
| Symlinking `.agents/skills/beads/` into a `skills/` directory | Direct `skills` path pointer (`"skills": ["./.agents/skills/beads"]`) | Symlink would satisfy "no duplicated copy" too, but is unnecessary: the documented `skills` field already supports pointing directly at an arbitrary relative path containing `SKILL.md`, with zero filesystem changes. A symlink adds a moving part (breaks on `git clone` without `core.symlinks`, breaks on Windows checkouts) for no benefit over the plain manifest field. |
| Marketplace `source: "./"` pointing at repo root | Marketplace `source: "./plugins/beads"` with a copied/restructured plugin subdirectory | Restructuring the repo into a `plugins/` subdirectory would satisfy the schema too, but violates the phase's explicit "no duplicated copy" boundary and the "packaging metadata only" scope — the existing repo root already qualifies as a valid plugin directory once `.claude-plugin/plugin.json` exists there. |

**Installation:** None — no `npm install` / `pip install` step. This phase is entirely file creation (`plugin.json`, `marketplace.json`, `LICENSE`).

**Version verification:** N/A — no package versions to verify. `claude` CLI itself is already installed at `2.1.233`, confirmed via `claude --version` this session.

## Package Legitimacy Audit

**Not applicable.** This phase installs zero external packages in any ecosystem (npm, pip, cargo, or otherwise). The Package Legitimacy Gate protocol is skipped by design — there is nothing to run `npm view` / `package-legitimacy check` against.

**Packages removed due to [SLOP] verdict:** none (N/A — no packages evaluated)
**Packages flagged as suspicious [SUS]:** none (N/A — no packages evaluated)

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────────────────────┐
                    │   gsd-beads repo root (= plugin root     │
                    │   = marketplace root, same directory)    │
                    └─────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐          ┌───────────────────┐          ┌─────────────────┐
│  LICENSE       │          │ .claude-plugin/    │          │ .agents/skills/  │
│  (MIT text)    │◄──ref────│   plugin.json       │──points─►│   beads/          │
└───────────────┘  "license"│   name: beads       │  "skills"│   SKILL.md         │
                    (string) │   version: 0.1.0    │  field   │   (name: beads,    │
                              │   author: {...}     │          │    frontmatter is  │
                              │   license: "MIT"    │          │    invocation-name │
                              │   skills: [          │          │    authority)      │
                              │    "./.agents/       │          └─────────────────┘
                              │     skills/beads"]   │
                              └──────────┬───────────┘
                                         │ (strict:true, default —
                                         │  plugin.json is authority,
                                         │  marketplace entry supplements)
                                         ▼
                              ┌───────────────────────┐
                              │ .claude-plugin/         │
                              │   marketplace.json       │
                              │   name: <marketplace-id> │
                              │   owner: {...}           │
                              │   plugins: [{             │
                              │     name: "beads",        │
                              │     source: "./",          │
                              │     description: "..."      │
                              │   }]                        │
                              └──────────┬───────────────┘
                                         │
                    /plugin marketplace add ./  (scratch project)
                                         │
                                         ▼
                              ┌───────────────────────┐
                              │  /plugin install         │
                              │  beads@<marketplace-id>   │
                              └──────────┬───────────────┘
                                         │ Claude Code copies plugin dir
                                         │ into ~/.claude/plugins/cache
                                         ▼
                              ┌───────────────────────┐
                              │  Installed plugin surfaces │
                              │  the `beads` skill (from   │
                              │  cached copy of              │
                              │  .agents/skills/beads/)      │
                              └───────────────────────────┘

  claude plugin validate . --strict  (TWO required runs, D-09):
  ┌──────────────────────────────┐   ┌───────────────────────────────┐
  │ Run 1: marketplace.json       │   │ Run 2: marketplace.json         │
  │ TEMPORARILY MOVED AWAY         │   │ PRESENT (normal repo state)      │
  │ → "." now has only              │   │ → "." has .claude-plugin/          │
  │   plugin.json in                │   │   marketplace.json → validator      │
  │   .claude-plugin/                │   │   enters "marketplace directory"     │
  │ → validator enters "plugin        │   │   mode: checks marketplace.json       │
  │   directory" mode: PARSES          │   │   schema + cross-references            │
  │   SKILL.md frontmatter,             │   │   plugin.json, but does NOT open        │
  │   hooks/hooks.json                   │   │   SKILL.md at all                        │
  └──────────────────────────────┘   └───────────────────────────────┘
```

### Recommended Project Structure

No new directories. Only new files at the repo root:

```
gsd-beads/
├── .claude-plugin/
│   ├── plugin.json          # NEW — plugin identity + skills pointer
│   └── marketplace.json     # NEW — self-hosted marketplace catalog
├── LICENSE                  # NEW — MIT text
└── .agents/skills/beads/    # EXISTING — untouched, referenced not copied
    └── SKILL.md
```

### Pattern 1: Point `skills` directly at an existing skill directory (no copy, no symlink)

**What:** `plugin.json`'s `skills` field accepts a relative path pointing directly at a directory that itself contains `SKILL.md` — not only a parent directory of multiple named skill subdirectories.
**When to use:** Exactly this phase's situation — an existing skill directory lives outside the plugin's default `skills/` scan location and must be exposed without duplication.
**Example:**
```json
// Source: code.claude.com/docs/en/plugins-reference, "Path behavior rules" section
// [VERIFIED: code.claude.com/docs/en/plugins-reference — fetched and quoted this session]
// Verbatim doc quote:
// "A skill path can point to a directory that contains a SKILL.md directly,
//  for example "skills": ["."] for the plugin root ... Claude Code takes the
//  skill's invocation name from the frontmatter `name` field in SKILL.md, so
//  the name stays stable whatever the install directory is named. If `name`
//  isn't set in the frontmatter, Claude Code falls back to the directory basename."
{
  "skills": ["./.agents/skills/beads"]
}
```
`.agents/skills/beads/SKILL.md` frontmatter (verified by reading the file this session, lines 1-4):
```yaml
---
name: beads
description: Use when working in a repository that uses bd or Beads for durable project task tracking...
---
```
`[VERIFIED: .agents/skills/beads/SKILL.md:1-4]` — quoted verbatim: `name: beads`. This is the invocation name Claude Code will use once installed — matches D-01/D-05's `beads` identity with no extra config needed.

**Do NOT** confuse this with `capability.json`'s own `"skills": ["beads-sync", "beads-status", "beads-recall", "beads-migrate-todos"]` list — those are gsd-core's *internal* lifecycle-step skill refs living at `.gsd/capabilities/beads/skills/*/SKILL.md` (confirmed present on disk this session), a completely separate mechanism from Claude Code's plugin `skills` field. This phase's `plugin.json` must reference **only** `.agents/skills/beads/` (see canonical_refs in CONTEXT.md, which already resolves this explicitly). Do not add the four internal step-skill directories to `plugin.json`'s `skills` array — they are not meant to be Claude Code-invocable in this phase.

### Pattern 2: Self-hosted marketplace pointing at the repo root itself

**What:** A `marketplace.json` whose single plugin entry's `source` is `"./"` — the marketplace and the plugin it lists live in the same repository, at the same root.
**When to use:** D-07's "stay local, re-point in Phase 8" decision — exactly this case.
**Example:**
```json
// Source: code.claude.com/docs/en/plugin-marketplaces, "Relative paths" section
// [VERIFIED: code.claude.com/docs/en/plugin-marketplaces — fetched and quoted this session]
{
  "name": "gsd-beads",
  "owner": { "name": "Dennis A. V. Dittrich", "email": "davdittrich@gmail.com" },
  "plugins": [
    {
      "name": "beads",
      "source": "./",
      "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle"
    }
  ]
}
```
Verbatim doc quote on path resolution: "Paths resolve relative to the marketplace root, which is the directory containing `.claude-plugin/`... Don't use `../` to reference paths outside the marketplace root." `"./"` resolves to the marketplace root itself, i.e., the repo root — exactly where `plugin.json` also lives. `strict` is omitted (defaults to `true`), so `plugin.json` remains the authority for `skills`/etc. and the marketplace entry only supplements — no need to duplicate the `skills` field here.

### Anti-Patterns to Avoid
- **Setting `marketplace.json`'s plugin entry `source` to a GitHub URL prematurely:** PROJECT.md and D-07 are explicit that this is deferred to Phase 8 (release archive re-point). Doing it now breaks local-repo testability (`/plugin marketplace add ./` from a scratch project, success criterion 2) since there is no pushed remote yet (`git remote -v` returned nothing this session).
- **Setting `strict: false` on the marketplace entry:** would make the marketplace entry the sole authority for components and conflict with `plugin.json` also declaring `skills` — the docs state this combination is a load error ("`Plugin my-plugin has conflicting manifests: both plugin.json and marketplace entry specify components`"). Leave `strict` unset (defaults to `true`).
- **Copying or symlinking `.agents/skills/beads/` into a `skills/` directory:** unnecessary given Pattern 1, and explicitly forbidden by the phase boundary ("no duplicated copy of the skill in the repo").

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Verifying `plugin.json`/`marketplace.json` are well-formed | A custom JSON Schema validator or manual eyeballing | `claude plugin validate . --strict` (run twice per D-09) | It is the actual runtime's own parser — a hand-rolled schema check can pass while Claude Code itself still rejects the manifest (or vice versa: warnings become errors only under `--strict`, which a hand-rolled check wouldn't reproduce) |
| Generating MIT `LICENSE` text | A custom license-text generator or LLM paraphrase | The canonical OSI/SPDX MIT template, copyright line substituted per D-04 | Any wording drift from the canonical text creates ambiguity about which license terms actually apply — the whole point of using a named, standard license is byte-identical text |

**Key insight:** This phase has almost no domain complexity — the entire risk surface is "does the JSON match Claude Code's actual parser," which only `claude plugin validate` itself can answer authoritatively.

## Common Pitfalls

### Pitfall 1: `claude plugin validate` silently skips frontmatter checks whenever `marketplace.json` is present in the same directory
**What goes wrong:** Running `claude plugin validate . --strict` once, in the repo's normal state (both `plugin.json` and `marketplace.json` present under `.claude-plugin/`), exits 0 even if `.agents/skills/beads/SKILL.md`'s YAML frontmatter is malformed — giving false confidence that the skill is correctly wired.
**Why it happens:** Per the official troubleshooting table [VERIFIED: code.claude.com/docs/en/plugin-marketplaces, "Marketplace validation errors" section], `YAML frontmatter failed to parse` and the `hooks/hooks.json` JSON-syntax check are both documented as "**Reported only when validating a plugin directory**." A directory becomes a "marketplace directory" (a different validation code path) the instant `.claude-plugin/marketplace.json` exists inside it — and this repo's plugin and marketplace manifests share one `.claude-plugin/` directory by design (self-hosted marketplace, D-07). The verbatim quote confirming the marketplace-mode behavior: "When pointed at a marketplace directory, the validator checks `marketplace.json` for schema errors, duplicate plugin names, and source path traversal. For each entry whose `source` is a local path, it also validates that plugin's own `plugin.json`" — note: validates `plugin.json`, not the skill files it points to.
**How to avoid:** D-09's mandated double-run is mechanically necessary, not just belt-and-suspenders: (1) `mv .claude-plugin/marketplace.json /tmp/` (or equivalent), run `claude plugin validate . --strict`, confirm it exits 0 — this is the only run that actually parses `.agents/skills/beads/SKILL.md`'s frontmatter; (2) restore `marketplace.json`, run `claude plugin validate . --strict` again, confirm it exits 0 — this run validates `marketplace.json`'s own schema and cross-checks `plugin.json`.
**Warning signs:** Only ever running `claude plugin validate . --strict` once, in the repo's checked-in state, and treating a clean exit as proof the skill frontmatter is valid.

### Pitfall 2: Relative-path plugin `source` breaks the moment the marketplace is added via a raw URL instead of a git/local path
**What goes wrong:** D-07 keeps `source: "./"` for this phase (correct, per PROJECT.md's staged plan), but if anyone later tests `/plugin marketplace add https://raw.githubusercontent.com/.../marketplace.json` (a direct URL to the file) instead of `/plugin marketplace add ./` or a git URL, the relative-path plugin source will fail to install with a "path not found" error.
**Why it happens:** Verbatim: "URL-based marketplaces only download the `marketplace.json` file itself. They don't download plugin files from the server. Relative paths in the marketplace entry reference files on the remote server that were not downloaded." [VERIFIED: code.claude.com/docs/en/plugin-marketplaces, Troubleshooting section]
**How to avoid:** Phase 5's own success criterion 2 tests via `/plugin marketplace add ./` (local path) from a scratch project — this is the correct test surface for this phase and does not hit the URL-based-marketplace failure mode. Flag for Phase 8: once `source` is re-pointed at a release archive URL (`archive` source type, not a bare relative path), this particular pitfall becomes moot — `archive` sources don't have this restriction.
**Warning signs:** A scratch-project test that adds the marketplace via a `raw.githubusercontent.com` URL rather than a git clone URL or local path.

### Pitfall 3: `claude plugin init` scaffolds in the wrong location for this repo's layout
**What goes wrong:** Running `claude plugin init beads` (or `claude plugin new`) to "get started faster" creates a **new** plugin skeleton at `~/.claude/skills/beads/`, not at this repo's root — the opposite of what this phase needs (turn the existing repo root into the plugin).
**Why it happens:** Per `claude plugin --help` output captured this session: `init|new [options] <name>` — "Scaffold a new plugin at `~/.claude/skills/<name>/` (auto-loads next session as `<name>@skills-dir`)." [VERIFIED: local `claude plugin --help` output]
**How to avoid:** Hand-author `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` directly at the repo root per the schemas above; do not invoke `claude plugin init`/`new` for this phase.
**Warning signs:** A stray `~/.claude/skills/beads/` directory appearing outside the repo after running a scaffold command.

## Code Examples

### `plugin.json` (complete, all four PUB-01 required fields + skills pointer)
```json
// Source: code.claude.com/docs/en/plugins-reference (schema) + D-01/D-02/D-03/D-08 (values)
// [VERIFIED: field names/types from code.claude.com/docs/en/plugins-reference, fetched this session]
{
  "name": "beads",
  "version": "0.1.0",
  "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle",
  "author": {
    "email": "davdittrich@gmail.com"
  },
  "license": "MIT",
  "skills": ["./.agents/skills/beads"]
}
```
**Open item on `author`:** see Open Questions — the documented `author` object schema lists `name` as required when the object form is used; D-02 specifies email-only. This example shows D-02 literally; the plan must include a `claude plugin validate . --strict` check specifically confirming this shape is accepted (not merely warned-then-tolerated) before treating PUB-01 as satisfied.

### `marketplace.json` (complete, self-hosted, root-pointing)
```json
// Source: code.claude.com/docs/en/plugin-marketplaces (schema) + D-05/D-06/D-07 (values)
// [VERIFIED: field names/types from code.claude.com/docs/en/plugin-marketplaces, fetched this session]
{
  "name": "gsd-beads",
  "owner": {
    "name": "Dennis A. V. Dittrich",
    "email": "davdittrich@gmail.com"
  },
  "plugins": [
    {
      "name": "beads",
      "source": "./",
      "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle"
    }
  ]
}
```
Note: `"gsd-beads"` is not on the documented reserved-marketplace-name list (`claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `claude-plugins-community`, `claude-community`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `anthropic-agent-skills`, `knowledge-work-plugins`, `life-sciences`, `claude-for-legal`, `claude-for-financial-services`, `financial-services-plugins`, `first-party-plugins`, `healthcare`) [VERIFIED: code.claude.com/docs/en/plugin-marketplaces, "Reserved names" note, fetched this session] — no conflict with REQUIREMENTS.md's `/plugin marketplace add <owner>/gsd-beads` naming.

### Validation double-run (D-09 mechanism, exact commands)
```bash
# Run 1 — plugin-directory mode (parses SKILL.md frontmatter)
mv .claude-plugin/marketplace.json /tmp/marketplace.json.bak
claude plugin validate . --strict
echo "exit: $?"   # must be 0

# Restore
mv /tmp/marketplace.json.bak .claude-plugin/marketplace.json

# Run 2 — marketplace-directory mode (validates marketplace.json schema + cross-checks plugin.json)
claude plugin validate . --strict
echo "exit: $?"   # must be 0
```

### MIT LICENSE (canonical template, copyright line per D-04)
```
MIT License

Copyright (c) 2026 Dennis A. V. Dittrich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
`[ASSUMED — reproduced from training knowledge of the canonical OSI/SPDX MIT template, not fetched verbatim this session (the WebFetch tool refused to reproduce license text past ~125 characters per its own internal policy).]` **The plan must diff this text against `https://opensource.org/license/mit` or `https://spdx.org/licenses/MIT.html` before commit** — this is the one claim in this document not independently tool-verified this session, despite being extremely standard.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `claude plugin validate` checked only JSON manifest syntax | Also parses skill/agent/command YAML frontmatter and `hooks/hooks.json`, but only in "plugin directory" mode | Claude Code `v2.1.77` [CITED: github.com/anthropics/claude-code#38480 / #35138 release-note reference, not independently confirmed against a changelog this session — MEDIUM confidence] | This is precisely the mechanism behind D-09's double-run requirement; the docs pages themselves still under-describe it (tracked as an open Anthropic docs gap, issue #35138) |
| `"."` as a `skills` path value | Accepted since Claude Code `v2.1.221`; before that only `"./"` worked | `v2.1.221` [CITED: code.claude.com/docs/en/plugins-reference, "Path behavior rules"] | Not directly load-bearing for this phase since `.agents/skills/beads` is used, not `.`/`./`, but relevant if the plan ever simplifies to a root-level skill later |
| `displayName` field | Added `v2.1.143` | `v2.1.143` [CITED: code.claude.com/docs/en/plugins-reference] | Optional, not used by any locked decision this phase — noted for completeness only |

**Deprecated/outdated:** None applicable — this is a green-field manifest, not a migration.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MIT LICENSE template text reproduced verbatim from training knowledge (not independently tool-fetched this session, since WebFetch refused to reproduce it past ~125 chars) | Code Examples → MIT LICENSE | Low legal risk (MIT text is extremely standardized and stable across decades) but non-zero — a single dropped/altered word changes the legal instrument. Plan must include a diff-against-canonical-source step before commit. |
| A2 | v2.1.77 changelog attribution for the frontmatter-checking expansion (sourced from a GitHub issue's paraphrase of release notes, not the raw changelog itself) | State of the Art table | Low — doesn't change what to build, only the "since when" framing; if wrong, the mechanism (frontmatter checked only in plugin-directory mode) is still independently confirmed by the current docs' troubleshooting table, which was read directly. |

## Open Questions

1. **Does `plugin.json`'s `author` object require a `name` sub-field, or is `{"email": "..."}` alone valid, satisfying D-02 literally?**
   - What we know: The `plugin.json` schema page documents `author` as type `object` with an example `{"name": "...", "email": "..."}` but does not explicitly restate a `name`-required rule inline. The **marketplace-entry** `author` field (a documented equivalent, listed in the same schema family) explicitly states: "Plugin author information (`name` required; `email` and `url` optional)." [VERIFIED: code.claude.com/docs/en/plugin-marketplaces, "Optional plugin fields" table, fetched and quoted this session]
   - What's unclear: Whether `plugin.json`'s own `author` field enforces the same `name`-required rule at the JSON-schema/type-validation level (in which case `claude plugin validate --strict` would flag `{"email": "davdittrich@gmail.com"}` with no `name`), or whether it's a softer documentation convention not mechanically enforced.
   - Recommendation: Author `plugin.json` per D-02 as written (email-only), then run `claude plugin validate . --strict` as the very first planning/implementation step (before anything else) and read its exact output. If it errors or warns on the missing `author.name`, escalate back to the user with the two options: (a) add a `name` field derived from the LICENSE copyright line ("Dennis A. V. Dittrich"), or (b) confirm the warning is acceptable/expected. Do not silently add a `name` field to satisfy the schema — that would override a locked decision without consent.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `claude` CLI | `claude plugin validate`, `/plugin marketplace add`, `/plugin install` (all success criteria) | ✓ | `2.1.233` [VERIFIED: local `claude --version`] | — |
| `git` | Repo is already a git repository; no new git operations required this phase (no remote yet — `git remote -v` returned empty this session, consistent with PUB-10 being a later phase) | ✓ | — | — |
| Scratch/second Claude Code project for success criterion 2 (`/plugin marketplace add ./` "from a scratch project") | Success criterion 2's install round-trip test | Not probed this session — requires a second working directory outside this repo, created at verification time, not a research-time dependency | — | Create a throwaway directory (`mktemp -d`) and run Claude Code there against this repo's absolute path |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** the "scratch project" for success criterion 2 is created at verification time, not installed — no blocking gap.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None (no application code produced this phase) — verification is via the `claude plugin validate` CLI itself, which acts as the schema/parser oracle |
| Config file | none — `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` are themselves the artifacts under test |
| Quick run command | `claude plugin validate . --strict` (single run, catches JSON/schema errors fast) |
| Full suite command | The D-09 two-run sequence in Code Examples → "Validation double-run" |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PUB-01 | `plugin.json` declares identity, points `skills` correctly, passes strict validation including frontmatter | manual-only (CLI, no test framework) — justification: no application code, no test runner applicable; the CLI's own validator IS the test | `mv .claude-plugin/marketplace.json /tmp/ && claude plugin validate . --strict; mv /tmp/marketplace.json .claude-plugin/` | N/A — command exists today (`claude` CLI verified installed) |
| PUB-02 | `marketplace.json` entry makes `/plugin marketplace add ./` + `/plugin install` succeed from a scratch project | manual-only (interactive Claude Code session in a scratch directory) — justification: `/plugin marketplace add` and `/plugin install` are interactive slash commands, not scriptable via `claude plugin validate` alone; `claude plugin marketplace add` non-interactive subcommand exists per `claude plugin --help` and could be scripted in a future phase, but success criterion 2 as written requires the `/plugin install` completion UI flow | `claude plugin marketplace add ./ --scope local` (non-interactive equivalent, confirmed to exist via `claude plugin --help` this session) then `claude plugin install beads@gsd-beads` | N/A |
| PUB-08 | `LICENSE` (MIT) exists, `plugin.json.license` is `"MIT"` string | manual-only (file existence + string check) — justification: trivial static check, no framework needed | `test -f LICENSE && grep -q '"license": "MIT"' .claude-plugin/plugin.json` | N/A |

### Sampling Rate
- **Per task commit:** `claude plugin validate . --strict` (quick run, normal state — catches JSON errors immediately, though see Pitfall 1 for what it does NOT catch in this state)
- **Per wave merge:** Full D-09 double-run
- **Phase gate:** Full D-09 double-run green, plus a real `/plugin marketplace add ./` + `/plugin install` round trip from a scratch directory, before `/gsd:verify-work`

### Wave 0 Gaps
None — existing `claude` CLI installation covers all phase requirements' verification surface. No test framework install needed (there is no test framework for this phase's artifact type).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | Not applicable — no authentication surface in static manifest files |
| V3 Session Management | No | Not applicable |
| V4 Access Control | No | Not applicable |
| V5 Input Validation | Yes (narrow) | `claude plugin validate --strict` is the input-validation control for the two JSON manifests — this is Claude Code's own built-in schema/type validator, not a custom one to build |
| V6 Cryptography | No | Not applicable — no secrets, no crypto operations in this phase |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Marketplace name/plugin name impersonating an official Anthropic marketplace (name-squatting) | Spoofing | Claude Code's own loader rejects reserved names (`claude-code-marketplace`, `anthropic-plugins`, etc., re-checked on every load) — already verified this repo's chosen names (`gsd-beads` marketplace, `beads` plugin) don't collide [VERIFIED: code.claude.com/docs/en/plugin-marketplaces, reserved-names list, fetched this session] |
| `source` path traversal (`../` escaping the marketplace root) | Tampering | Claude Code's validator rejects `..` in `source` paths outright ("`plugins[0].source: Path contains ".."`" is a documented hard error) — this phase's `source: "./"` contains no traversal, no custom mitigation needed |

## Sources

### Primary (HIGH confidence)
- `code.claude.com/docs/en/plugins-reference` — fetched directly this session (twice, targeted prompts); `plugin.json` schema (required/optional fields, `author` object shape, `license` string type, `skills` field path-behavior rules including direct-SKILL.md-pointer support), reserved-field type-checking rules, `claude plugin init` scaffold-location behavior cross-checked against local `claude plugin --help` output
- `code.claude.com/docs/en/plugin-marketplaces` — fetched directly this session (full page, ~1300 lines read); `marketplace.json` schema (required/optional fields, `owner` object, plugin-entry fields, `source` types, relative-path resolution rules, reserved marketplace names, `strict` mode semantics), full `claude plugin validate` troubleshooting table (the source of the D-09 double-run mechanism), `claude plugin marketplace add` non-interactive CLI subcommand reference
- Local `claude --version` (`2.1.233`) and `claude plugin --help` / `claude plugin validate --help` output — captured directly this session
- `.agents/skills/beads/SKILL.md` — read directly this session, lines 1-4, frontmatter `name: beads` confirmed
- `.gsd/capabilities/beads/capability.json` — read directly this session, confirms `version: "0.1.0"` (source of D-03) and the four internal step-skill names (source of the Pattern 1 "do not confuse" note)
- `.planning/PROJECT.md` (lines 95-101, Constraints section) — read directly this session, confirms `beads` (not `gsd-beads`) is the correct id per gsd-core's own reserved-prefix loader rule

### Secondary (MEDIUM confidence)
- `github.com/anthropics/claude-code` issue #35138 (WebFetch summary) — paraphrase of v2.1.77 release-note content describing the frontmatter/hooks.json validation expansion; the underlying mechanism it describes was independently confirmed against the current, directly-fetched docs page, so only the specific version number (`v2.1.77`) carries secondary-source risk

### Tertiary (LOW confidence)
- MIT LICENSE canonical text (Code Examples section) — reproduced from training knowledge, not tool-fetched verbatim this session; flagged in Assumptions Log (A1) with an explicit pre-commit diff requirement

## Metadata

**Confidence breakdown:**
- Standard stack (manifest schemas): HIGH — both schema pages fetched directly and quoted verbatim this session
- Architecture (skills-path mechanism, marketplace self-hosting): HIGH — the exact mechanism (direct-SKILL.md path, frontmatter-name authority) is a verbatim doc quote, not an inference
- Pitfalls (validate two-mode behavior): HIGH — verbatim quote from the official troubleshooting table, cross-checked against the CLI's actual `--help` output locally
- LICENSE text: LOW (flagged, see A1) — everything else in this phase is HIGH/MEDIUM

**Research date:** 2026-08-16
**Valid until:** 30 days (Claude Code plugin schema is actively evolving — multiple fields in the fetched docs carry "Requires Claude Code v2.1.1xx or later" notes, indicating frequent schema additions; re-verify field list if plan execution slips past ~2026-09-15)
