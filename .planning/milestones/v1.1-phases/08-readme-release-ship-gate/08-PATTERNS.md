# Phase 8: README, Release & Ship Gate - Pattern Map

**Mapped:** 2026-08-16
**Files analyzed:** 2 (both net-new; zero pre-existing analogs of the same file type exist in this repo)
**Analogs found:** 2 / 2 (role/content-source analogs, not same-file-type analogs — no README.md or *.yml workflow exists anywhere in this repo to copy structurally)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|---------------|
| `README.md` | config/docs (static content, no code) | request-response (human reads, follows verbatim commands) | `.agents/skills/beads/SKILL.md` + `AGENTS.md` (content sourcing), `.gitignore` (comment-header grouping style) | content-source (no structural analog — first README in repo) |
| `.github/workflows/release.yml` | config (CI pipeline definition) | event-driven (tag push trigger → build → publish) | `.claude-plugin/marketplace.json` / `hooks/hooks.json` (JSON config formatting conventions only) | no structural analog — first GH Actions workflow in repo; content fully specified by RESEARCH.md Pattern 1 |

Both files are genuinely new file *types* for this repo (no prior README, no prior `.github/workflows/`). There is nothing to copy structurally. What follows documents (a) the repo's established conventions these new files must match stylistically, and (b) the fully-specified external pattern (from RESEARCH.md, already vetted against `--help` output and official docs) to use verbatim for the workflow.

## Pattern Assignments

### `README.md` (docs, request-response)

**No same-file-type analog exists.** Content must be synthesized from three existing sources per CONTEXT.md D-05 and canonical_refs. Do not duplicate wholesale — summarize and point to the fuller docs.

**Source 1 — `.agents/skills/beads/SKILL.md`** (lines 1-8, frontmatter + intro): defines what the plugin *is*, for the README's "What it does" section:
```yaml
---
name: beads
description: Use when working in a repository that uses bd or Beads for durable project task tracking, issue dependencies, blocker management, multi-session handoff, or shared work memory. Trigger when the user asks to find ready work, claim or close tasks, create follow-up work, inspect blockers, recover project context, or choose between local planning and persistent project tracking.
---

# Beads

Use Beads as the shared project task system. Local plans, scratch files, and personal memories are useful, but they are not the durable source of truth for project work.
```

**Source 2 — `.agents/skills/beads/SKILL.md`** (lines 28-60, Core CLI Workflow): source material for D-05's worked `bd` usage example (short end-to-end snippet, not the whole block):
```bash
bd ready
bd list --status=open
bd show <id>
bd update <id> --claim
bd create "Short title" --description="Why this exists and what needs to be done" --type=task --priority=2
bd close <id> --reason="Completed"
```

**Source 3 — `AGENTS.md`** (lines 1-24, architecture note + Quick Reference): source for D-03's Dolt-backend caveat language and the "point to AGENTS.md for the full command set" cross-reference:
```markdown
> **Architecture in one line:** Issues live in a local Dolt database
> (`.beads/dolt/`); cross-machine sync uses `bd dolt push/pull` (a
> git-compatible protocol), stored under `refs/dolt/data` on your git
> remote — separate from `refs/heads/*` where your code lives.
> `.beads/issues.jsonl` is a passive export, not the wire protocol.
```
Note: this repo's actual config has **no** `.beads/issues.jsonl` at all (Dolt-only, confirmed Phase 7 RESEARCH.md) — README's caveat must say the export doesn't exist here, not merely "is passive," per D-03(2).

**Source 4 — `.claude-plugin/plugin.json`** (full file, 10 lines) and **`.claude-plugin/marketplace.json`** (full file, 15 lines): source for exact install command targets (plugin name `beads`, marketplace name `gsd-beads`, repo `davdittrich/gsd-beads`) — install/uninstall commands must reference these exact literal names, not paraphrase:
```json
"name": "beads"        // plugin.json
"name": "gsd-beads"     // marketplace.json
```
Exact commands (from RESEARCH.md Code Examples, already verified against `--help`):
```bash
claude plugin marketplace add davdittrich/gsd-beads
claude plugin install beads@gsd-beads -y
claude plugin uninstall beads -y
```

**Source 5 — `hooks/hooks.json`** (full file, 15 lines): source for D-03(3)'s SessionStart hook caveat — the hook runs `bd prime --hook-json` on every session start, which requires an initialized beads workspace (`bd where`/`bd init`) to produce meaningful output:
```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "command": "bd prime --hook-json", "type": "command" }], "matcher": "" }
    ]
  }
}
```

**Style precedent — `.gitignore`** (full file, 22 lines): this repo's established convention for grouping related config lines under a short `#`-prefixed comment header (established Phase 7). No direct Markdown equivalent, but confirms this repo favors short, purpose-labeled groupings over unlabeled blocks — apply the same discipline to README section headers already locked by D-04.

---

### `.github/workflows/release.yml` (CI config, event-driven)

**No structural analog exists in this repo** (first `.github/workflows/` file). RESEARCH.md's Pattern 1 is already fully specified, source-cited, and pitfall-checked (Pitfalls 1 and 3) — use verbatim as the base, do not re-derive:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v7

      - name: Build allowlisted archive
        run: |
          zip -r gsd-beads.zip \
            .claude-plugin \
            hooks \
            .agents/skills \
            README.md \
            LICENSE

      - name: Publish release
        run: gh release create "${{ github.ref_name }}" gsd-beads.zip --generate-notes
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**JSON config formatting convention (style precedent only, not structural)** — `.claude-plugin/marketplace.json` and `hooks/hooks.json` both use 2-space indent, no trailing commas, double-quoted keys. YAML has no direct equivalent, but confirms this repo's config files favor minimal, flat structure over nesting — the workflow above matches that (no matrix builds, no reusable-workflow abstraction, single job, single named step per action per RESEARCH.md's "no unrequested abstraction" framing).

**Critical constraints already locked (do not deviate):**
- `permissions: contents: write` at job level (Pitfall 1) — omitting causes 403 on `gh release create`.
- Explicit include-list zip (Pitfall 3) — never `zip -r out.zip . -x ...`; the five named paths are the allowlist by construction (`.claude-plugin`, `hooks`, `.agents/skills`, `README.md`, `LICENSE` — verbatim from ROADMAP SC2/D-06).
- `gh release create` (preinstalled CLI), not `softprops/action-gh-release` (RESEARCH.md Alternatives Considered — third-party pin adds no value for a single-asset release).

---

## Shared Patterns

### Verified-command discipline (D-02, D-09)

**Source:** `.planning/phases/07-hygiene-publication/07-02-SUMMARY.md` lines 118-146 (Task 2: "Exact commands run, in order" + captured Output block)
**Apply to:** README.md's install/uninstall commands (must be the literal commands actually executed, not paraphrased — D-02) and the phase's SUMMARY.md verification transcript (D-09 explicitly reuses this exact pattern: fenced command block, then fenced real-output block, no synthetic/simulated output).
```markdown
**Exact commands run, in order:**
\`\`\`
gh repo create davdittrich/gsd-beads --public --source=.
git push -u origin main --tags
\`\`\`

**Output:**
\`\`\`
$ gh repo create davdittrich/gsd-beads --public --source=.
https://github.com/davdittrich/gsd-beads
...
\`\`\`
```
Note: D-02 for the README itself additionally forbids showing output blocks in README.md (keeps doc from drifting) — the transcript-with-output pattern applies to SUMMARY.md only, not to README.md's command examples.

### Fresh-clone-is-the-only-evidence discipline (D-10)

**Source:** `.planning/phases/07-hygiene-publication/07-02-SUMMARY.md` lines 148-149 (Task 3 header) and the tech-stack pattern recorded at line 25: *"Fresh clone into a throwaway /tmp path is the only trustworthy verification of what a push actually put on the remote — local state is not evidence of remote state."*
**Apply to:** The ship gate's `claude plugin validate . --strict` re-run (D-10) and SC5 verification — must run from a fresh `git clone` + `git checkout v1.1.0` in a scratch dir (RESEARCH.md's own Code Examples block already gives the exact commands), never from the working tree, mirroring Phase 7's identical discipline for its own remote-state proof.

### Config JSON/YAML minimalism

**Source:** `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `hooks/hooks.json` — all flat, no nesting beyond what's functionally required, no comments (JSON), 2-space indent.
**Apply to:** `.github/workflows/release.yml` — single job, no reusable-workflow/matrix abstraction, matches RESEARCH.md's explicit anti-pattern guidance against unrequested abstraction.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `README.md` | docs | request-response | First README in this repo — no structural analog; content assembled from SKILL.md/AGENTS.md/plugin.json/marketplace.json/hooks.json per Pattern Assignments above |
| `.github/workflows/release.yml` | CI config | event-driven | No `.github/workflows/` directory exists yet — first GH Actions workflow; RESEARCH.md Pattern 1 is the authoritative, already-vetted source to use verbatim |

## Metadata

**Analog search scope:** repo root, `.claude-plugin/`, `hooks/`, `.agents/skills/beads/`, `AGENTS.md`, `.gitignore`, `.planning/phases/07-hygiene-publication/`
**Files scanned:** `.gitignore`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `hooks/hooks.json`, `AGENTS.md`, `.agents/skills/beads/SKILL.md`, `.planning/phases/07-hygiene-publication/07-02-SUMMARY.md`
**Pattern extraction date:** 2026-08-16
