# Phase 9: Beads Content Depth - Context

**Gathered:** 2026-08-16
**Status:** Ready for planning

<domain>

## Phase Boundary

The shipped plugin's beads guidance matches upstream depth and is tailored to gsd-core, not generic defaults. Two requirements: PUB-11 (expand `.agents/skills/beads/SKILL.md` toward upstream parity) and PUB-12 (ship a gsd-tailored `.beads/PRIME.md` override), followed by a `v1.1.1` patch release replacing the already-public but short `v1.1.0` archive.

</domain>

<decisions>

## Implementation Decisions

### PRIME.md shipping mechanism
- **D-01:** `PRIME.md`'s source file lives at `.agents/skills/beads/PRIME.md` — inside the already-allowlisted `.agents/skills/` tree, so `release.yml`'s zip allowlist needs NO change. This deliberately avoids reopening the `.beads/` exclusion Phase 7/8 established (Phase 7's whole premise was that `.beads/` never ships).
- **D-02:** The file is copied to `.beads/PRIME.md` via a **self-healing check that runs whenever it's missing** — not a one-shot install-time action. User explicitly rejected "copy once at install" in favor of "copy whenever missing" (survives a user deleting/regenerating `.beads/`, a fresh `bd init` in an existing install, etc.). Likely wired into the existing SessionStart hook (`hooks/hooks.json`, alongside `bd prime --hook-json`) so it self-heals every session start, not just first install. — **Reversibility:** reversible — a hook script change, no migration.

### SKILL.md scope
- **D-03:** Split structure: `resources/` + `commands/` directories, matching the upstream `beads` skill's progressive-disclosure convention (e.g. `resources/BOUNDARIES.md`, `commands/dep.md`). SKILL.md itself stays a short entry point; detail loads on demand. PUB-11's success criterion explicitly allows this (not required verbatim single-file).
- **D-04:** Full parity with upstream's command coverage — `bd dep` (dependencies), labels, comments, search, `compact`, `import`, `stats`, `blocked`, worktrees, async gates, resumability, `--stealth`/`BEADS_DIR` git-free mode, troubleshooting. No curation/cutting — matches PUB-11's success criterion literally, no judgment calls about what to omit.

### PRIME.md content
- **D-05:** PRIME.md covers all 4 gsd-core lifecycle sync points (`plan:post`, `execute:wave:post`, `verify:post`, `ship:pre`) inline — but **minimal and token-efficient**: terse bullets, not prose explanations. User explicitly rejected the "Full inline reference" framing (long-form) in favor of a compact version carrying the same substance. Matches beads' own `bd prime`'s token-budget design intent (MCP mode ~50 tokens, CLI mode ~1-2k tokens — this override should stay lean, not balloon it).
- **D-06:** PRIME.md is gsd-integration-only — assumes the reader already knows bare `bd` CLI essentials (`bd ready`, `bd show`, `bd update --claim`) from the base `beads` skill. No duplication between PRIME.md and SKILL.md.

### v1.1.1 re-release process
- **D-07:** Delete the existing `v1.1.0` GitHub Release and tag (`gh release delete v1.1.0 --cleanup-tag`) before cutting `v1.1.1` — matches Phase 7's precedent of deleting the throwaway `v0.0.0-rc1` rehearsal tag/release after use. Avoids a stranger installing the known-short `v1.1.0` by mistake. — **Reversibility:** one-way for the deleted release/tag itself (GitHub doesn't restore deleted releases), but `v1.1.1` fully supersedes it with no functional loss — the content is a strict superset. Not rated one-way in the blocking-checkpoint sense: this is routine release hygiene, not the kind of irreversible-and-consequential action Phase 7's history rewrite was.

### Resolved open questions (post-research)
- **D-08:** `.beads/PRIME.md` (the self-healing hook's *runtime copy* in D-02) is **gitignored**, not tracked. `.agents/skills/beads/PRIME.md` (D-01) is the sole source of truth and stays git-tracked in the already-allowlisted tree. Add `.beads/PRIME.md` to `.gitignore`. Prevents drift between two copies of the same content.
- **D-09:** Hook ordering — the copy-if-missing check runs **before** the existing `bd prime --hook-json` SessionStart command, so `bd prime` never reads a stale/absent override on first run in a fresh install.

### Claude's Discretion
- Exact `resources/`/`commands/` file names and per-file content depth within upstream's established pattern (D-03/D-04).
- Exact wording/bullet structure of PRIME.md's terse sync-point summaries (D-05).
- Exact hook-script mechanics for the self-healing copy-if-missing check (D-02) — e.g. a shell one-liner appended to `hooks/hooks.json`'s existing SessionStart command, or a small script file it calls.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 9: Beads Content Depth" — the 4 success criteria are fully mechanism-specified
- `.planning/REQUIREMENTS.md` — PUB-11, PUB-12 (traceability table maps both to Phase 9)
- `.planning/PROJECT.md` Key Decisions table — the Phase 9 creation rationale (hard requirement, not deferred, surfaced during Phase 8 UAT)

### Upstream comparison source (the parity target)
- `~/.claude/skills/beads/SKILL.md` and its `resources/` (15 files: `PATTERNS.md`, `ISSUE_CREATION.md`, `CHEMISTRY_PATTERNS.md`, `WORKFLOWS.md`, `TROUBLESHOOTING.md`, `BOUNDARIES.md`, `STATIC_DATA.md`, `WORKTREES.md`, `INTEGRATION_PATTERNS.md`, `ASYNC_GATES.md`, `RESUMABILITY.md`, `CLI_REFERENCE.md`, `MOLECULES.md`, `DEPENDENCIES.md`, `AGENTS.md`) and `commands/` (13 files: `ready.md`, `label.md`, `stats.md`, `update.md`, `blocked.md`, `comments.md`, `import.md`, `compact.md`, `search.md`, `dep.md`, `reopen.md`, `prime.md`, `create.md`) — this is the official upstream skill by Steve Yegge (v0.60.0, MIT), the literal parity target for D-04. Read the actual file contents, do not assume from names.

### Existing shipped files (read before touching)
- `.agents/skills/beads/SKILL.md` — current shipped skill (80 lines, single file) being expanded
- `hooks/hooks.json` — existing SessionStart hook (`bd prime --hook-json`) that D-02's self-healing copy likely wires into
- `.github/workflows/release.yml` — release allowlist (D-01 confirms no change needed here)
- `.claude-plugin/plugin.json` — current version `1.1.0`, will need bumping to `1.1.1` when the release is cut
- `bd prime --help` output — documents `.beads/PRIME.md` as beads' supported override mechanism, and the `--export`/`--memories-only`/`--hook-json` flags relevant to how the hook should invoke it

No other external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets
- `hooks/hooks.json`'s existing SessionStart `bd prime --hook-json` command — D-02's copy-if-missing check is a natural sibling addition here, not a new hook registration.
- Phase 8's `08-01-SUMMARY.md`/`08-02-SUMMARY.md` fresh-clone/allowlist-verification transcript pattern — reusable for verifying D-01's "no allowlist change" claim and the eventual `v1.1.1` release.

### Established Patterns
- Tracer-first rehearsal on a throwaway tag (Phase 7's mirror-backup rehearsal, Phase 8's `v0.0.0-rc1` rehearsal) — likely applies again before the real `v1.1.1` cut, though this phase's release step is lower-risk (content-only change, same proven workflow).
- Explicit-allowlist discipline (Phase 7/8's core security control) — D-01 is designed specifically to not weaken this.

### Integration Points
- `.beads/PRIME.md` doesn't exist yet in this repo either (`ls .beads/PRIME.md` confirms absent) — this phase creates both the shipped source (`.agents/skills/beads/PRIME.md`) and, via the self-healing hook, the runtime copy.
- `plugin.json`'s `version` field (currently `1.1.0`) needs bumping to `1.1.1` when the release ships (same pattern as Phase 8's `1.1.0` bump).

</code_context>

<specifics>

## Specific Ideas

No particular UI/behavior references — this is a documentation/skill-content and packaging phase. Upstream `~/.claude/skills/beads/` is the concrete content model to follow (D-03/D-04), not an abstract standard.

</specifics>

<deferred>

## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 9-Beads Content Depth*
*Context gathered: 2026-08-16*
