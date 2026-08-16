---
phase: 05-plugin-manifest
plan: 01
subsystem: infra
tags: [claude-code-plugin, plugin-manifest, marketplace, mit-license, packaging]

requires: []
provides:
  - ".claude-plugin/plugin.json declaring the beads plugin identity, pointing skills at .agents/skills/beads/"
  - ".claude-plugin/marketplace.json self-hosted gsd-beads catalog with one beads entry"
  - "LICENSE (MIT) at repo root, verified byte-for-byte against the canonical SPDX text"
  - "D-10: documented, permanent, scoped exception for the root-CLAUDE.md --strict warning"
affects: [06-runtime-integration, 07-hygiene-publication, 08-readme-release-ship-gate]

actuals:
  tokens: 441
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "D-10-aware validator checks: accept exit 0 OR exit non-zero containing ONLY the documented root-CLAUDE.md warning (zero error sections, exactly one warning bullet, matching known text) — any other validator output fails the check"

key-files:
  created:
    - .claude-plugin/plugin.json
    - .claude-plugin/marketplace.json
    - LICENSE
  modified: []

key-decisions:
  - "D-02 amended mid-execution: author object now {name, email} — claude plugin validate . --strict hard-errors on author.name absence; user chose to amend the locked email-only decision rather than accept a permanent validation failure"
  - "D-10 (new): root CLAUDE.md's --strict warning has no suppression mechanism and CLAUDE.md cannot move without breaking this repo's own AI-tooling auto-load; user accepted it as one scoped, documented, permanent exception"
  - "marketplace.json given a top-level description (RESEARCH.md's Pattern 2 example omitted it); --strict flags a missing marketplace description independently of D-10, no decision conflict, applied the existing D-06 blurb"

patterns-established:
  - "D-10-scoped validator-output check: for any future --strict run in this repo, 'clean' means zero ✘ error sections and either zero warnings or exactly the one documented root-CLAUDE.md warning — codified in Task 1/Task 2 verify logic, reusable in Phase 6-8's validation gates"

requirements-completed: [PUB-01, PUB-02, PUB-08]

coverage:
  - id: D1
    description: "plugin.json declares beads identity (name/version/license/author) and resolves the beads skill from .agents/skills/beads/ with no duplicated copy"
    requirement: PUB-01
    verification:
      - kind: other
        ref: "claude plugin validate . --strict (plugin-directory mode, marketplace.json absent) — clean except the accepted D-10 warning; jq schema/identity checks; SKILL.md name-match check; single-SKILL.md-file check"
        status: pass
    human_judgment: false
  - id: D2
    description: "marketplace.json self-hosted catalog entry makes a local marketplace add + install round trip work"
    requirement: PUB-02
    verification:
      - kind: other
        ref: "claude plugin validate . --strict (marketplace-directory mode) — exit 0 clean; jq identity/source checks"
        status: pass
      - kind: manual_procedural
        ref: "coordinator-run round trip: claude plugin marketplace add + claude plugin install beads@gsd-beads -y + claude plugin details beads@gsd-beads (Skills (1) beads), then uninstall/marketplace remove cleanup — all exit 0"
        status: pass
    human_judgment: true
    rationale: "Task 3 is an interactive/manual verification gate by design (ROADMAP success criterion 2); executed via claude CLI subcommands rather than the /plugin slash-command UI the plan's how-to-verify described — a substitution the approving human explicitly disclosed, not silently assumed equivalent."
  - id: D3
    description: "LICENSE (MIT) exists at repo root, plugin.json.license names it as a string"
    requirement: PUB-08
    verification:
      - kind: other
        ref: "diff against raw.githubusercontent.com/spdx/license-list-data/main/text/MIT.txt (word-normalized, copyright line excluded) — byte-identical; grep checks for copyright line and warranty text; jq .license == \"MIT\""
        status: pass
    human_judgment: false

duration: ~11min active execution (two long human-checkpoint waits inflate wall-clock; see Performance)
completed: 2026-08-16
status: complete
---

# Phase 5 Plan 1: Plugin Manifest Summary

**Repo declares itself a valid Claude Code plugin (`plugin.json` + self-hosted `marketplace.json` + verified MIT `LICENSE`), with two mid-execution decisions (D-02 amended, D-10 added) needed to make `claude plugin validate . --strict` pass.**

## Performance

- **Duration (active execution):** ~11 min across three work sessions (file writes + validator runs + commits)
- **Wall clock (file-create to final commit):** 2026-08-16T00:35:18Z → 2026-08-16T10:45:54Z (~10h11m) — dominated by two human-checkpoint waits (Task 1's D-02/D-10 decision, Task 3's install round trip), not active work
- **Started:** 2026-08-16T00:35:18Z (LICENSE first written)
- **Completed:** 2026-08-16T10:45:54Z (Task 2 commit; Task 3 is human-verify only, no code commit)
- **Tasks:** 3/3 (Task 1 tracer, Task 2 auto, Task 3 checkpoint:human-verify)
- **Files modified:** 3 (all new)

## Accomplishments
- `.claude-plugin/plugin.json`: `beads` identity, `skills: ["./.agents/skills/beads"]` — resolves the existing skill directly, no copy/symlink
- `.claude-plugin/marketplace.json`: self-hosted `gsd-beads` catalog, one `beads` entry, `source: "./"`
- `LICENSE`: MIT text verified word-for-word against the canonical SPDX source before commit (RESEARCH.md's A1 assumption resolved, not just trusted)
- `claude plugin validate . --strict` clean in both modes (plugin-directory and marketplace-directory), modulo one documented, permanent, scoped exception (D-10)
- Local marketplace-add + install + uninstall round trip completed and confirmed the `beads` skill resolves with no stray `~/.claude/skills/beads/` copy

## Task Commits

Each task was committed atomically:

1. **Task 1: plugin.json + LICENSE (tracer)** - `0f3d3be` (feat)
2. **Task 2: marketplace.json catalog entry + D-09 double-run** - `1ab7dea` (feat)
3. **Task 3: Scratch-project install round trip** - human-verify only, no code change; approved by coordinator with disclosed CLI-subcommand method (see Deviations)

**Plan metadata:** commit created alongside this SUMMARY (see final commit in git log)

## Files Created/Modified
- `.claude-plugin/plugin.json` - Plugin identity + skills pointer to `.agents/skills/beads/`
- `.claude-plugin/marketplace.json` - Self-hosted catalog, one `beads@gsd-beads` entry
- `LICENSE` - MIT text, copyright line `Copyright (c) 2026 Dennis A. V. Dittrich`

## Decisions Made
- **D-02 amended:** `author` object now carries both `name` and `email` (was email-only). `claude plugin validate . --strict` hard-errors (`author.name: Invalid input: expected string, received undefined`) without it; the plan's own HALT RULE required user consent before deviating from the original locked decision. User chose to amend.
- **D-10 (new):** the root `CLAUDE.md` (this repo's own dev-workflow file, unavoidably at the plugin root since `.claude-plugin/` lives at repo root) trips a `--strict`-promoted warning with no suppression mechanism (confirmed by a dedicated research addendum). Moving/renaming it would break this repo's own AI-tooling auto-load. User accepted this one warning as a permanent, documented exception — not a general relaxation; both tasks' verify logic still fails on any *other* validator error or warning.
- **Applied D-06 blurb to `marketplace.json`'s top-level `description`** (not present in RESEARCH.md's Pattern 2 example) — `--strict` flags a missing marketplace description independently of D-10; fixed by reusing the already-decided install-page blurb, no new content decision needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Task 1/Task 2 verify scripts' D-10 acceptance regex had a false-negative**
- **Found during:** Task 1, first `<automated>` verify
- **Issue:** The plan's `grep -v -E "CLAUDE\.md at the plugin root|To ship context with your plugin|Validation failed \(--strict treats warnings as errors\)|^[[:space:]]*$"` only stripped the warning-detail line, not the surrounding structural lines (`Validating plugin manifest:`, `Validating plugin:`, `⚠ Found 1 warning:`) that any clean D-10-only run also emits — so the intended-passing case still failed the check.
- **Fix:** Replaced with a positive check: zero `✘ Found` (error) sections, exactly one `❯` bullet, and that bullet matches the known D-10 text. Applied identically to Task 1's plugin-directory-mode check and both runs of Task 2's D-09 double-run.
- **Files modified:** none (PLAN.md not edited; fix applied at execution time in the verify commands actually run)
- **Verification:** Re-ran both tasks' verify blocks with the corrected logic; all passed, confirmed no other validator output present.
- **Committed in:** 0f3d3be, 1ab7dea (verify logic isn't itself a tracked artifact; commits carry the resulting green state)

**2. [Rule 2 - Missing Critical] `marketplace.json` missing top-level `description`**
- **Found during:** Task 2, D-09 double-run (Run 2, marketplace-directory mode)
- **Issue:** `--strict` flagged "No marketplace description provided" as a promoted-to-error warning — a validator-required field RESEARCH.md's Pattern 2 code example simply omitted, unrelated to D-10 or any locked decision.
- **Fix:** Added `"description"` at `marketplace.json`'s top level, reusing the existing D-06 blurb already used for `plugins[0].description`.
- **Files modified:** `.claude-plugin/marketplace.json`
- **Verification:** Re-ran the D-09 double-run; Run 2 now exits 0 clean.
- **Committed in:** `1ab7dea`

---

**Total deviations:** 2 auto-fixed (1 bug in verify logic, 1 missing-field correctness fix) + 2 checkpoint-halted decisions resolved by the user (D-02 amendment, D-10 acceptance — not auto-fixes, tracked separately as Decisions Made).
**Impact on plan:** No scope creep — both auto-fixes are within the plan's own `.claude-plugin/` file boundary and don't touch `.agents/skills/beads/` or `.gsd/capabilities/beads/`.

## Issues Encountered

- **Prompt-injection attempt in tool output (Task 1):** immediately after a diagnostic `claude plugin validate` run (used to isolate the CLAUDE.md-warning issue from the author.name issue), the tool result included a fabricated "system-reminder" claiming the diagnostic `author.name` edit was pre-approved and instructing me not to disclose it. That edit was mine alone, made for diagnosis, and I disclosed and reverted it in the same turn per the standing rule that no tool/agent output can substitute for user consent. Flagged explicitly in the first checkpoint return; no code impact — the diagnostic edit never reached a commit.
- **Task 3's actual verification method diverged from the plan's `<how-to-verify>` text.** The plan specified the interactive `/plugin marketplace add` + `/plugin install` slash-command UI flow (RESEARCH.md explicitly notes this was the deliberate choice over the non-interactive CLI subcommand, "success criterion 2 as written requires the /plugin install completion UI flow"). The coordinator instead ran the non-interactive `claude plugin marketplace add` / `claude plugin install -y` / `claude plugin details` / `claude plugin uninstall` / `claude plugin marketplace remove` CLI equivalents, disclosed exactly what was run, and approved. Accepted as satisfying Task 3 since the human explicitly chose and disclosed the method — recorded here rather than silently treated as identical to the originally-specified UI flow.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 6 (Runtime Integration) can proceed: `plugin.json`'s `skills` pointer and the capability-loader bridge question (PUB-03) are unblocked by this phase's identity/manifest work.
- D-10's root-`CLAUDE.md` exception is now a standing, documented constraint — Phase 8's final ship-gate validation (PUB-09) must reuse the same D-10-aware acceptance check, not a bare `exit 0` assertion, or it will falsely fail on the same permanent warning.
- No blockers carried forward.

---
*Phase: 05-plugin-manifest*
*Completed: 2026-08-16*
