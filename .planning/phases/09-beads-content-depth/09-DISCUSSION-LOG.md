# Phase 9: Beads Content Depth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-16
**Phase:** 9-Beads Content Depth
**Areas discussed:** PRIME.md shipping mechanism, SKILL.md scope — full parity vs curated subset, PRIME.md content — what goes in it, v1.1.1 re-release process

---

## PRIME.md shipping mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Ship at .agents/skills/beads/PRIME.md, copy at install-time | Stays inside allowlisted tree, no allowlist change | ✓ (modified) |
| Carve a narrow .beads/PRIME.md-only allowlist exception | Ships directly at expected path, reopens .beads/ exclusion | |

**User's choice:** Option 1, modified — copy whenever missing, not just at install time (self-healing check, likely wired into the existing SessionStart hook).

---

## SKILL.md scope — full parity vs curated subset

| Option | Description | Selected |
|--------|-------------|----------|
| Split: resources/ + commands/ | Matches upstream's progressive-disclosure convention | ✓ |
| Single expanded SKILL.md file | Everything in one file | |

**User's choice:** Split: resources/ + commands/

| Option | Description | Selected |
|--------|-------------|----------|
| Full parity with upstream's command list | Matches PUB-11 literally | ✓ |
| Curated subset most relevant to gsd-core users | Smaller, requires cutting decisions | |

**User's choice:** Full parity with upstream's command list

---

## PRIME.md content — what goes in it

| Option | Description | Selected |
|--------|-------------|----------|
| Full inline reference | Long-form, self-contained | ✓ (modified) |
| Short summary + pointer to README/AGENTS.md | Brief, points elsewhere for depth | |

**User's choice:** Content substance of option 1 (all 4 sync points inline), but minimal/token-efficient delivery — terse bullets, not prose.

| Option | Description | Selected |
|--------|-------------|----------|
| Assume known, gsd-integration only | No duplication with SKILL.md | ✓ |
| Include both | Re-state CLI essentials too | |

**User's choice:** Assume known, gsd-integration only

---

## v1.1.1 re-release process

| Option | Description | Selected |
|--------|-------------|----------|
| Delete v1.1.0 release + tag | Clean state, matches Phase 7 rc-tag precedent | ✓ |
| Mark v1.1.0 as pre-release/deprecated, keep it | Leaves a paper trail | |
| Leave v1.1.0 as-is, publish v1.1.1 alongside | Simplest, no extra commands | |

**User's choice:** Delete v1.1.0 release + tag

---

## Claude's Discretion

- Exact resources/commands/ file names and per-file content depth within upstream's established pattern
- Exact wording/bullet structure of PRIME.md's terse sync-point summaries
- Exact hook-script mechanics for the self-healing copy-if-missing check

## Deferred Ideas

None — discussion stayed within phase scope.
