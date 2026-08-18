---
phase: 9
reviewers: [antigravity]
reviewed_at: 2026-08-16T22:37:00Z
plans_reviewed: [09-01-PLAN.md, 09-02-PLAN.md, 09-03-PLAN.md, 09-04-PLAN.md]
---

# Cross-AI Plan Review — Phase 9

## Consensus Summary

Single reviewer (antigravity/Gemini) ran with full repo access and cited concrete `file:line` evidence throughout. Overall verdict: plans are sound, LOW risk, ready to execute with three LOW-severity fixes recommended before or during wave 1.

### Agreed Strengths

(single-reviewer run — no cross-reviewer agreement to report)
- Source of truth for PRIME.md correctly placed in the already-allowlisted `.agents/skills/beads/` tree; `.beads/PRIME.md` gitignored as a derived runtime copy — preserves the Phase 7/8 `.beads/` packaging exclusion invariant with zero `release.yml` changes.
- Self-healing hook wrapper (`hooks/session-start.sh`) runs copy-if-missing before `bd prime --hook-json` in the same execution chain, guaranteeing `bd prime` never reads a stale/absent override.
- Scope correctly anchored to PUB-11's literal 13 named topics, not upstream's grown 29-command surface — avoids scope creep while still hitting the requirement.
- Plan 04 replicates Phase 8's full release verification matrix (strict plugin validate, tag teardown/recut, provenance check, fresh-clone install, marketplace round trip).

### Agreed Concerns

(single-reviewer run — no cross-reviewer agreement to report)

**[LOW] `CLAUDE_PLUGIN_ROOT` fallback missing in `hooks/session-start.sh`** (09-01-PLAN.md Tasks 1–2)
`${CLAUDE_PLUGIN_ROOT:-}` is unset during direct local dev/testing outside the marketplace runner. Suggested fix:
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SOURCE="$PLUGIN_ROOT/.agents/skills/beads/PRIME.md"
```

**[LOW] PRIME.md sync-point table may be missing `plan:pre` (`beads-recall`)** (09-01-PLAN.md Task 1 vs `.gsd/capabilities/beads/capability.json:59-71`)
`capability.json` defines **six** lifecycle steps, not five as the plan's action text states: `plan:pre` (`beads-recall`, produces `BEADS-RECALL.md`), `plan:post` (`beads-sync`), `execute:wave:pre` (`beads-status`), `execute:wave:post` (`beads-status`), `verify:post` (`beads-status`), `ship:pre` (`beads-status`). Verify PRIME.md's table includes `plan:pre` alongside the other five.

**[LOW] MIT attribution check inconsistent between Plan 02 and Plan 03** (09-02-PLAN.md vs 09-03-PLAN.md)
Plan 02's automated verification greps for MIT attribution on adapted `resources/*.md`; Plan 03 has no equivalent check for `commands/*.md`. Recommend adding the same attribution assertion to Plan 03's verification for consistency.

### Divergent Views

N/A — single reviewer.

---

## Antigravity Review

# Cross-AI Plan Review: Phase 9 (Beads Content Depth)

## 1. Summary

The implementation plans (`09-01-PLAN.md` through `09-04-PLAN.md`) for Phase 9 provide an airtight, disciplined approach to expanding `.agents/skills/beads/` toward upstream parity (PUB-11) and materializing a gsd-tailored `bd prime` lifecycle override (PUB-12), followed by a clean re-release as `v1.1.1` (PUB-04/PUB-09/PUB-10). The architecture respects the repository's strict hygiene boundary—storing the override source in the already-allowlisted `.agents/skills/beads/PRIME.md` tree and deploying a self-healing hook wrapper in `hooks/session-start.sh` rather than breaking the `.beads/` packaging exclusion. The progressive-disclosure split into `resources/` (6 files) and `commands/` (8 files) cleanly anchors against the literal 13-topic scope of PUB-11 without bloating to upstream's 29 commands. Every plan contains robust automated verification checks and STRIDE threat models.

---

## 2. Strengths

- **Surgical Packaging & Zero Allowlist Changes:**
  - Placing the source of truth at `.agents/skills/beads/PRIME.md` leverages the existing recursive zip rule in `.github/workflows/release.yml:21` (`.agents/skills`), preserving the invariant established in Phase 7/8 that `.beads/` never ships to installers.
  - Adding `.beads/PRIME.md` to `.gitignore` (Plan 01 Task 2) prevents runtime self-healing from polluting working tree status or causing drift.
- **Robust Self-Healing Mechanics:**
  - `hooks/session-start.sh` executes the copy-if-missing check prior to invoking `bd prime --hook-json` in the same execution chain (Plan 01 Task 1), ensuring `bd prime` never runs with a missing override.
  - Guard conditions (asserting `.beads/` exists, destination absent, source present) ensure that non-beads workspaces are never polluted and user customizations are never clobbered.
- **Accurate Scope Anchor & Defensive Documentation:**
  - Correctly avoids duplicating unstable CLI flag tables that would drift across `bd` releases, referencing live `bd <subcommand> --help` while providing high-value conceptual wiring (e.g. mapping `bd blocked` and dependencies to `capability.json`'s `blocking_open` ship gate).
  - Preserves entry-point conciseness in `.agents/skills/beads/SKILL.md` via markdown links to `resources/` and `commands/`.
- **End-to-End Release & Marketplace Verification:**
  - Plan 04 replicates the full release verification matrix from Phase 8 (`claude plugin validate . --strict`, GitHub Release teardown and tag re-cut, artifact provenance verification against workflow run duration, fresh clone checkout, and `/plugin marketplace add` / `/plugin install` round trip).

---

## 3. Concerns

- **[LOW] Hook Execution Environment Fallback (`CLAUDE_PLUGIN_ROOT` resolution in non-plugin runs):**
  - *Location:* `09-01-PLAN.md` (Task 1 & Task 2)
  - *Concern:* In direct local development (or when run outside Claude Code's marketplace runner), `${CLAUDE_PLUGIN_ROOT}` may be unset or empty. The plan specifies using `${CLAUDE_PLUGIN_ROOT:-}` but should ensure that a local fallback (e.g. searching relative to the script directory `${BASH_SOURCE[0]%/*}/..`) allows the script to function consistently during testing without manually exporting `CLAUDE_PLUGIN_ROOT`.
- **[LOW] `plan:pre` / `beads-recall` Representation in `PRIME.md`:**
  - *Location:* `09-01-PLAN.md` Task 1 action (d) vs `.gsd/capabilities/beads/capability.json:59-71`
  - *Concern:* Task 1's action text mentions the sync points table with entries from `capability.json`'s `steps[]` ("all five points including execute:wave:pre"). `capability.json` actually lists **six** lifecycle steps: `plan:pre` (`beads-recall`), `plan:post` (`beads-sync`), `execute:wave:pre` (`beads-status`), `execute:wave:post` (`beads-status`), `verify:post` (`beads-status`), and `ship:pre` (`beads-status`). The plan should make sure `plan:pre` (`beads-recall` producing `BEADS-RECALL.md`) is included in the table alongside the other five.
- **[LOW] Upstream Attribution Consistency:**
  - *Location:* `09-02-PLAN.md` & `09-03-PLAN.md`
  - *Concern:* Plan 02 includes MIT license blockquote attribution checks (`grep -qi 'MIT' "$f"`) for adapted resource files. Plan 03's automated verification does not explicitly assert MIT attribution on `commands/*.md`. While command files are minimal reference wrappers, adding the standard attribution block across all adapted files maintains uniform copyright hygiene.

---

## 4. Suggestions

- **Clarify Script Root Fallback in `hooks/session-start.sh`:**
  ```bash
  PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
  SOURCE="$PLUGIN_ROOT/.agents/skills/beads/PRIME.md"
  ```
  This makes `hooks/session-start.sh` seamlessly testable when run directly by developers or automated test scripts without requiring `CLAUDE_PLUGIN_ROOT` to be set explicitly.
- **Ensure Full 6-Step Sync Point Alignment:**
  Verify that `PRIME.md` includes `plan:pre` (`beads-recall`) so the full lifecycle pipeline from `capability.json` (`plan:pre` -> `plan:post` -> `execute:wave:pre` -> `execute:wave:post` -> `verify:post` -> `ship:pre`) is documented.

---

## 5. Risk Assessment: LOW

- **Justification:** The phase introduces no foreign dependencies, touches no core C/Rust/Python extensions, and makes zero changes to `gsd-core`. The packaging, tagging, and validation procedures are direct reruns of proven Phase 8 workflows. Threat modeling and automated test coverage across all 4 plans are comprehensive and well-grounded in repository evidence.
