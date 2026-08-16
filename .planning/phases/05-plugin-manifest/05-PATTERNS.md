# Phase 5: Plugin Manifest - Pattern Map

**Mapped:** 2026-08-16
**Files analyzed:** 3 (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `LICENSE`)
**Analogs found:** 0 exact / 3 (greenfield — see below)

## Search Confirmation

Confirmed via filesystem search: no `.claude-plugin/` directory, no `plugin.json`, no `marketplace.json`, no `LICENSE*` file exists anywhere in this repo (`find . -iname ".claude-plugin" -o -iname "marketplace.json"` and `find . -iname "LICENSE*"` both returned empty). This phase is the first to introduce Claude Code plugin manifests into this codebase — there is no prior in-repo example of this exact artifact type. This matches CONTEXT.md's own note: "None yet — no `.claude-plugin/` directory exists in the repo. This phase creates it from scratch."

Because no in-repo analog exists for the manifest *content/schema*, RESEARCH.md's tool-verified schema (fetched directly from `code.claude.com/docs/en/plugins-reference` and `code.claude.com/docs/en/plugin-marketplaces` this session) is the authoritative source for field names, types, and structure — not a codebase analog. Below, closest in-repo files are used only for **JSON formatting/style conventions** and **identity-value sourcing**, per role classification.

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|-----------------|---------------|
| `.claude-plugin/plugin.json` | config (manifest) | request-response (read by `claude plugin validate` / plugin loader) | `.gsd/capabilities/beads/capability.json` (identity fields only); `.planning/config.json` (JSON style) | role-match (identity fields), no analog (schema) |
| `.claude-plugin/marketplace.json` | config (catalog manifest) | request-response (read by `/plugin marketplace add`) | `.gsd-capabilities.json` (JSON style, entry-list shape) | no analog (schema), style-match only |
| `LICENSE` | config (legal text) | static file, no data flow | none in repo | no analog — canonical external template only |

## Pattern Assignments

### `.claude-plugin/plugin.json` (config, request-response)

**No in-repo schema analog.** Schema authority is RESEARCH.md's verbatim doc quotes (Standard Stack, Pattern 1, Code Examples sections) — these are HIGH-confidence, tool-fetched this session from `code.claude.com/docs/en/plugins-reference`.

**Identity-value source** — `.gsd/capabilities/beads/capability.json` (read in full this session):
```json
{
  "id": "beads",
  "version": "0.1.0",
  ...
}
```
Confirms D-01 (`name: "beads"`) and D-03 (`version: "0.1.0"`) are consistent with the existing capability's own identity fields — copy these literal values, do not invent new ones.

**JSON formatting convention** — `.planning/config.json` (read in full this session): 2-space indentation, double-quoted keys/strings, no trailing commas, nested objects for grouped config (e.g. `"git": {...}`, `"workflow": {...}`). Apply the same style to `plugin.json`'s `author` object.

**Skills-path pattern** (RESEARCH.md Pattern 1, verbatim doc quote, `code.claude.com/docs/en/plugins-reference`):
```json
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
**Do not** add `.gsd/capabilities/beads/skills/{beads-sync,beads-status,beads-recall,beads-migrate-todos}` to this `skills` array — those are gsd-core's internal lifecycle-step skills, a separate mechanism (confirmed via `capability.json`'s own `"skills"` array, read this session, lines 20-25). Reference **only** `.agents/skills/beads/` per CONTEXT.md canonical_refs.

**Open item to resolve during implementation (not silently override):** RESEARCH.md Open Questions #1 flags that `author.name` may be schema-required even though D-02 specifies email-only. Run `claude plugin validate . --strict` immediately after writing this file and read the exact output before treating PUB-01 as satisfied.

---

### `.claude-plugin/marketplace.json` (config, request-response)

**No in-repo schema analog.** Schema authority is RESEARCH.md's verbatim doc quotes (Pattern 2, Code Examples sections), tool-fetched this session from `code.claude.com/docs/en/plugin-marketplaces`.

**Style/shape reference** — `.gsd-capabilities.json` (read in full this session, 13 lines): flat top-level object with a `version` string, an `entries`/`plugins`-style keyed or listed collection, 2-space indent — same JSON conventions as `.planning/config.json`. No structural equivalence to marketplace.json's schema (different domain), used for formatting-consistency only.

**Core pattern** (RESEARCH.md Pattern 2, verbatim quote):
```json
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
- `source: "./"` per D-07 — local relative path only, do not point at a GitHub URL this phase (re-pointed in Phase 8 per PROJECT.md).
- Omit `strict` field entirely (defaults to `true`) — setting `strict: false` causes a documented load error ("conflicting manifests") since `plugin.json` already declares `skills`.
- `"gsd-beads"` marketplace name confirmed not on the reserved-name list (RESEARCH.md Code Examples, verbatim list checked this session).

---

### `LICENSE` (config, static)

**No in-repo analog** — no LICENSE file exists anywhere in this repo currently.

**Source:** Canonical MIT template (RESEARCH.md Code Examples, flagged LOW confidence / A1 — reproduced from training knowledge, not tool-fetched verbatim this session due to WebFetch's reproduction-length policy).

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

**Mandatory pre-commit step (per RESEARCH.md Assumptions Log A1):** diff this text against `https://opensource.org/license/mit` or `https://spdx.org/licenses/MIT.html` before committing — this is the one claim in RESEARCH.md not independently tool-verified this session.

## Shared Patterns

### JSON formatting convention (repo-wide)
**Source:** `.planning/config.json`, `.gsd-capabilities.json` (both read in full this session)
**Apply to:** `plugin.json`, `marketplace.json`
- 2-space indentation
- Double-quoted keys and string values
- No trailing commas
- Nested objects for grouped fields (e.g. `author`, `owner`)

### Identity consistency (name/version)
**Source:** `.gsd/capabilities/beads/capability.json` (`id: "beads"`, `version: "0.1.0"`)
**Apply to:** `plugin.json` (`name`, `version`), `marketplace.json` (`plugins[0].name`)
Keep all three literal values byte-identical to `capability.json`'s existing `id`/`version` — do not drift.

### Validation-as-test (no analog needed, no framework)
**Source:** RESEARCH.md Validation Architecture section
**Apply to:** both manifest files
`claude plugin validate . --strict` run twice per D-09 (marketplace.json present/absent) is the sole verification surface — no unit test file to write, no test framework to configure.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.claude-plugin/plugin.json` | config | request-response | First Claude Code plugin manifest in this repo; schema is external (Anthropic-defined), not derivable from existing code |
| `.claude-plugin/marketplace.json` | config | request-response | Same — first self-hosted marketplace catalog in this repo |
| `LICENSE` | config | static | Repo has never had a LICENSE file; content is a fixed external legal template, not a codebase pattern |

For all three, RESEARCH.md's Code Examples section (verbatim, tool-fetched schema) supersedes any in-repo analog search — this is architecturally correct given the artifact type is a standardized external format, not project-specific code.

## Metadata

**Analog search scope:** entire repo root (`find . -iname ".claude-plugin" -o -iname "marketplace.json"`, `find . -iname "LICENSE*"`), `.gsd/capabilities/beads/capability.json`, `.agents/skills/beads/SKILL.md`, `.planning/config.json`, `.gsd-capabilities.json`
**Files scanned:** 6 (0 direct hits, 4 style/identity-value analogs used)
**Pattern extraction date:** 2026-08-16
