# Phase 8: README, Release & Ship Gate - Context

**Gathered:** 2026-08-16
**Status:** Ready for planning

<domain>

## Phase Boundary

A stranger can evaluate, install, and remove `gsd-beads` from the README alone. Three requirements: PUB-04 (versioned release archive built from an explicit allowlist, attached to a GitHub Release), PUB-07 (README covering purpose, requirements, install, uninstall, caveats, license, gsd-core link — every command transcribed from one actually executed), PUB-09 (final `claude plugin validate . --strict` clean at the released tag, plus a real `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip).

</domain>

<decisions>

## Implementation Decisions

### README audience & structure
- **D-01:** README is written for a cold stranger who knows neither gsd-core nor beads — matches SC1's literal "a stranger can evaluate" framing. Not scoped to gsd-core users or beads users specifically.
- **D-02:** Install/uninstall commands are exact, copy-pasteable, verbatim — none paraphrased. No "expected output" blocks shown (keeps the doc from drifting out of sync with CLI output format changes).
- **D-03:** Caveats section covers all three: (1) requirements — `bd` on PATH, Python 3 stdlib, gsd-core >=1.6.0 (already named in ROADMAP SC1); (2) known limitations of the beads/Dolt backend specific to this repo's config (e.g. no `.beads/issues.jsonl` passive export exists here — Dolt-only backend, confirmed in Phase 7's RESEARCH.md); (3) SessionStart hook prerequisites — what `bd prime` needs on first run, whether the installer's own repo needs a beads project already initialized.
- **D-04:** `README.md` lives at repo root. Section order: Title/one-liner → What it does → Requirements → Install → Uninstall → Caveats → License → Link to gsd-core.
- **D-05:** Include a short worked `bd` usage example beyond bare install (a tiny end-to-end workflow snippet), not just a pointer to AGENTS.md's Quick Reference.

### Release archive build mechanism
- **D-06:** Build the allowlisted release archive via a GitHub Actions workflow (`.github/workflows/release.yml`) triggered on `vX.Y.Z` tag push. Zips exactly `.claude-plugin/`, `hooks/`, `.agents/skills/`, `README.md`, `LICENSE` (ROADMAP SC2's explicit allowlist) and attaches to a GitHub Release. Chosen over a manual local script or hand-built zip for repeatability — no step to forget on future releases. — **Reversibility:** reversible — a CI workflow file can be edited/replaced freely; no migration cost.
- **D-07:** Tag/version this release `v1.1.0` — matches the current milestone version (v1.1, "Publish & Document") already used in ROADMAP.md/STATE.md. The existing `v1.0` tag (pre-dating this milestone) stays as historical/internal.

### Round-trip validation approach (SC4)
- **D-08:** The `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip is scripted where the CLI supports non-interactive flags; any step requiring interactive confirmation is called out explicitly for the user to perform by hand rather than faked or skipped.
- **D-09:** The round-trip's real command output (proof, not simulation) is embedded directly in Phase 8's `SUMMARY.md` — same pattern as Phase 7's fresh-clone verification transcript. No separate VALIDATION-TRANSCRIPT.md file.

### Ship gate scope (SC5)
- **D-10:** `claude plugin validate . --strict` already passes clean on the current local working tree (verified live during this discussion: `✔ Validation passed`). The ship gate must NOT rely on this local pass — it must re-run `claude plugin validate . --strict` against a **fresh clone checked out at the released tag**, proving SC5 literally rather than trusting an in-progress working tree.
- **D-11 (open, deferred to researcher/planner):** `marketplace.json`'s plugin source is currently `"./"` (repo-relative, works for both local dev and the public GitHub clone in principle). Whether this needs to change for the public release round trip is UNRESOLVED — user explicitly deferred this to be verified empirically against the real `/plugin marketplace add davdittrich/gsd-beads` flow during research/planning, not decided here. Do not assume `"./"` is correct without testing it.

### Claude's Discretion
- Exact README prose/wording within the locked section order (D-04).
- Exact GitHub Actions workflow YAML structure for D-06, as long as it triggers on tag push and produces the exact allowlist archive.
- Exact wording of the worked `bd` usage example (D-05).

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 8: README, Release & Ship Gate" — the 5 success criteria are fully mechanism-specified; plan against them verbatim.
- `.planning/REQUIREMENTS.md` — PUB-04, PUB-07, PUB-09 (traceability table maps all three to Phase 8)

### Prior phase precedent
- `.planning/phases/07-hygiene-publication/07-CONTEXT.md` — D-04/D-05 (repo owner/name/branch, no auto-init) and D-03 (mirror-backup-before-mutate pattern) are directly relevant precedent for how this phase should treat the release/validate operations.
- `.planning/phases/07-hygiene-publication/07-RESEARCH.md` — documents this repo's beads/Dolt backend specifics (no `.beads/issues.jsonl`) referenced in D-03 above.
- `.planning/phases/07-hygiene-publication/07-01-SUMMARY.md`, `07-02-SUMMARY.md` — the fresh-clone verification transcript pattern D-09 explicitly reuses.

### Existing plugin identity files (read before touching)
- `.claude-plugin/plugin.json` — current plugin identity (`beads`, v0.1.0, MIT, skill at `./.agents/skills/beads`)
- `.claude-plugin/marketplace.json` — current marketplace manifest; source field `"./"` is D-11's open question
- `LICENSE` — MIT, already present (Phase 5)
- `hooks/hooks.json` — SessionStart `bd prime --hook-json` hook (Phase 6), must be referenced accurately in caveats (D-03)
- `AGENTS.md` — existing Quick Reference (`bd ready`, `bd show`, `bd update --claim`, `bd close`, `bd dolt push`) and the sync-concepts architecture note — source material for D-05's worked example, do not duplicate wholesale

No other external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets
- `.agents/skills/beads/SKILL.md` and `.agents/skills/beads/agents/openai.yaml` — the skill content the README's "What it does" section should accurately summarize (not duplicate).
- `AGENTS.md`'s Quick Reference block — source for D-05's worked example; keep README's version short, point to AGENTS.md for the full command set.

### Established Patterns
- Phase 7 set the precedent of re-verifying claims live against real infrastructure (fresh clone, `gh repo view`) rather than trusting a prior SUMMARY — D-10 applies the same discipline to the plugin-validate gate.

### Integration Points
- README.md doesn't exist yet — this phase creates it from scratch (verified via `ls README.md` → not found).
- `claude plugin validate . --strict` binary is already available (`claude` CLI v2.1.233) and passes clean on the current tree — confirms the tool itself needs no separate install step.
- No `.github/workflows/` directory exists yet — D-06's release workflow is a new file, no prior CI to conflict with.

</code_context>

<specifics>

## Specific Ideas

No particular UI/behavior references — this is a documentation, packaging, and validation-gate phase. Standard README conventions and GitHub Actions release patterns apply as specified in the decisions above.

</specifics>

<deferred>

## Deferred Ideas

- **Expand `.agents/skills/beads/SKILL.md` toward upstream parity** — the shipped skill (80 lines, single file: `bd prime`/`ready`/`show`/`update --claim`/`create`/`close` only) is materially thinner than the official upstream `beads` skill by Steve Yegge (`~/.claude/skills/beads/`, v0.60.0, MIT — 110-line SKILL.md plus a `resources/` progressive-disclosure directory and a `commands/` per-subcommand reference directory). Missing entirely: `bd dep` (dependencies), labels, comments, search, `compact`, `import`, `stats`, `blocked`, worktrees, async gates, resumability, `--stealth`/`BEADS_DIR` git-free mode, `dolt push` detail, and a troubleshooting guide. Checked `.planning/PROJECT.md` and Phase 5's plan — no recorded decision to keep the shipped skill deliberately minimal; this looks like an unaddressed gap, not an intentional scope cut. Out of scope for Phase 8 (README/release/ship-gate, not skill content) — candidate for its own follow-up phase or a Phase 5/6 revisit.

</deferred>

---

*Phase: 8-README, Release & Ship Gate*
*Context gathered: 2026-08-16*
