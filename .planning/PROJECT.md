# beads capability for gsd-core

## What This Is

A gsd-core capability that makes [beads](https://github.com/gastownhall/beads) (`bd`) the task
substrate for gsd's plan → execute → verify → ship lifecycle: gsd's markdown holds the plan,
`bd` holds task status, and the planner/executor/ship gate all read live `bd` state instead of
`.planning/` prose. Installed as a runtime capability overlay — a directory drop under
`.gsd/capabilities/beads/` — with no fork and no patch to gsd-core itself.

## Core Value

gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero duplicated
task-state bookkeeping survives in `.planning/`.

## Requirements

### Validated

- ✓ **B1**: One beads issue per `PLAN.md` task, parented to a phase epic — Phase 1
- ✓ **B2**: Plan task ordering becomes beads dependencies — Phase 1
- ✓ **B3**: Task completion closes its issue automatically — Phase 1
- ✓ **B4**: Identity is bound explicitly via `beads-id:`, never by title matching — Phase 1
- ✓ **B5**: Sync is idempotent — Phase 1
- ✓ **B6**: `bd` absent, failing or locked degrades to a no-op with one visible notice — Phase 1
- ✓ **B9**: A phase with unfinished blocking issues cannot ship — Phase 3
- ✓ **B10**: Divergence blocks and is reported; never auto-reconciled — Phase 3
- ✓ **B7**: The planner sees open issues before planning (`BEADS-RECALL.md`) — Phase 2
- ✓ **B8**: The executor's prompt carries live issue state — Phase 2
- ✓ **B11**: `BEADS.md` is regenerated every step, never hand-edited — Phase 2
- ✓ **B12**: One-shot migration of `.planning/todos/pending/` into beads — Phase 4
- ✓ **B13**: `beads-status` prints the plan-task ↔ issue mapping on demand — Phase 4
- ✓ **B14**: Milestone-level epic option (`beads.epic_per=milestone`) — Phase 4
- ✓ **PUB-01**: `.claude-plugin/plugin.json` declares identity, points `skills` at
  `.agents/skills/beads/`, passes `claude plugin validate . --strict` (one documented, permanent
  exception: root `CLAUDE.md` warning, see 05-CONTEXT.md D-10) — Phase 5
- ✓ **PUB-02**: `.claude-plugin/marketplace.json` self-hosted entry; local
  `/plugin marketplace add` + `/plugin install beads@gsd-beads` round trip confirmed — Phase 5
- ✓ **PUB-08**: `LICENSE` (MIT) present at repo root, referenced in `plugin.json`'s `license` field
  — Phase 5
- ✓ **PUB-03**: The capability-loader bridge is a documented, verified manual `capability install`
  step — Phase 6
- ✓ **PUB-06**: `hooks/hooks.json` ships the SessionStart `bd prime` hook, `.claude/settings.json`
  retired — Phase 6

### Active

v1.1 remaining requirements (PUB-04, PUB-05, PUB-07, PUB-09, PUB-10) — see
`.planning/REQUIREMENTS.md` for full traceability. Phase 6 (Runtime Integration) complete.

### Out of Scope

- Overriding any first-party gsd-core behavior — the overlay is additive only; first-party always
  wins on collision (N1)
- Forking or patching gsd-core — if a core change proves necessary, raise it upstream first (N2)
- A second planning or gating pipeline — this capability tracks work, it does not decide how work
  is planned (N3)
- Executing command strings that originate in a plan, ticket, or other authored artifact — `bd`
  invocations are built from typed values only, never assembled from artifact text, because the
  artifact's author and the workflow's runner are frequently different principals (N4)
- Any dependency beyond the `bd` binary and Python 3 standard library (N5)
- Syncing beads onward to GitHub Issues, Jira, or any other tracker — one tracker only (N6)
- A deterministic plan-checker reviewer capability (PRD Appendix A) — benefit is unmeasured and
  the failure mode is a second review pipeline nobody asked for; revisit only after `beads` has
  shipped and only if the LLM plan-checker is observed spending judgement on decidable properties

## Current Milestone: v1.1 Publish & Document

**Goal:** Ship gsd-beads as an installable Claude Code plugin on GitHub, with a README that lets
a stranger evaluate, install, and remove it without reading the source.

**Target features:**
- Claude Code plugin manifest (`.claude-plugin/plugin.json`, marketplace-installable structure)
- GitHub repository with remote, pushed history
- README.md: purpose, capabilities, installation, deinstallation, requirements, caveats, link to
  gsd-core

## Context

gsd-core currently has zero issue-tracker integration (`grep -rli "beads\|bd create\|bd ready"`
across the distribution returns 0 hits). Task state lives entirely in hand-maintained
`.planning/` markdown, archived away at milestone close, with no query surface, no enforced
dependencies, and nothing that detects drift between plan and reality.

gsd-core ships a runtime capability registry overlay (`src/capability-loader.cts`, tested by
`tests/capability-loader.test.cjs`) that composes third-party capability directories onto the
frozen first-party registry at either `$GSD_HOME/.gsd/capabilities/<id>/` (global) or
`<projectRoot>/.gsd/capabilities/<id>/` (project). Capabilities bind through three mechanisms:
`steps[]` (run a skill/agent at a lifecycle point), `contributions[]` (inject a prompt fragment
into the orchestrator or verifier — the mechanism that makes this integration first-class rather
than a side effect), and `gates[]` (block a lifecycle point on a predicate). Gate predicates are
restricted to `command-exists` and `artifact-frontmatter-equals` — there is no predicate that
queries an external tool directly, which is why the capability must project live `bd` state into
a generated `BEADS.md` artifact at every step for gates to read.

The closest shipped analogue for shape and degrade-cleanly behavior is
`capabilities/mempalace/capability.json` — read it before implementing.

Binding model: phase ↔ epic, `PLAN.md` task ↔ issue (bound by an explicit `beads-id:`, never by
title), task dependency ↔ `bd dep add`, requirement id ↔ issue label. In `authoritative` mode
beads owns task *status* AND task *content* (title/description) — content originates in
`PLAN.md` at first sync, but the bd issue is authoritative from then on; `PLAN.md`'s task text
is not re-edited to follow later bd edits. Content divergence (B10) is therefore defined as a
`PLAN.md` task description that no longer matches its issue's content at the time the issue was
last synced from `PLAN.md`, not an ongoing two-way merge.

## Constraints

- **Installation**: Runtime overlay only, no fork/patch to gsd-core — reserved id prefixes
  (`gsd-`, `gsd-core-`, `anthropic-`) are rejected by the loader, so the capability id is `beads`.
  **Overridden 2026-08-15 (user decision, Phase 3 planning):** installed `ship.md` hardcodes
  `ship:pre` gate dispatch to `capId=='security'/'broken-windows'` only — no generic loop exists,
  so Phase 3's declared `gates[]` can never fire without a local, global `ship.md` patch. User
  explicitly authorized a machine-local patch as in-scope Phase 3 work (plan `03-03`, not deferred
  follow-up), plus an upstream feature request (open-gsd/gsd-core#3554) that would make the local
  patch unnecessary if merged. Phase 3 is not complete until `03-03` lands — the override covers
  this phase's execution scope, not this constraint's default going forward.
  Tracked via `.planning/` PLAN.md files only (no `bd` ticket) — this project's actual workflow
  has never routed its own dev-task tracking through the `beads` capability being built; `bd` is
  reserved for standalone bug reports (e.g. `gsd-beads-bgb`, `gsd-beads-uh1`), not phase task
  tracking.
- **Runtime**: Requires the `bd` binary on `PATH`; no dependency beyond `bd` and Python 3 stdlib
- **Compatibility**: Declares `engines.gsd: ">=1.6.0"`; a version mismatch must skip with a
  warning, never crash
- **Config namespace**: All config keys live under `beads.*` — must be checked against every
  shipped manifest before use to avoid a collision (collisions are rejected by the loader)
- **Fail-open**: `bd` absent, non-zero exit, or a locked DB must never block a gsd phase — gates
  use `onError: skip`, and a missing/unreadable `BEADS.md` means the gate simply does not fire
- **Global-scope installs**: Pass a consent gate (CB-3) before use; ship project-scoped first

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Overlay capability (`beads`), not a gsd-core fork | Forking buys maintenance of 79 skills / 45 capabilities to add one integration and diverges from upstream permanently; overlays are a supported, tested extension point | Shipped Phase 1 — project-scope install/consent confirmed working against real gsd-core 1.10.0 |
| `beads.sync_mode` defaults to `authoritative` for status and content | Discuss-phase 1 reversal (2026-08-15) of the original status-only split: bd is the single editable record post-creation, `PLAN.md` is not re-synced from it — avoids a two-way content merge while keeping one authoritative owner | Shipped Phase 1 (D-01) |
| Gate predicates read only generated artifact frontmatter (`BEADS.md`), never query `bd` directly | The only two shipped predicate kinds are `command-exists` and `artifact-frontmatter-equals`; no predicate calls an external tool | — Pending (BEADS.md generation and gates are Phase 2/3 scope; `capability.json`'s `gates[]`/`contributions[]` intentionally empty in Phase 1) |
| `gates[].onError: skip`, never `halt` | A missing/unreadable `BEADS.md` (capability disabled, `bd` absent, first run) must never strand a finished phase — the gate blocks only on a known bad state | — Pending (Phase 2/3 scope) |
| Real `bd` v1.2.1 CLI diverges from initial RESEARCH.md in three ways, discovered live during Phase 1 execution | `--id` on issue create fails (ids are DB-prefix-derived, not passable); child ids are hierarchical/sequential so a duplicate create yields a *new* id rather than erroring (resolve-by-`beads-id`-before-create is mandatory, not just tidy); `bd list --parent` hides closed issues by default (an orphan sweep on the default listing would silently break B5 idempotency — must pass an explicit status filter) | Shipped Phase 1 — `sync.py` built against the verified real behavior, not the stale doc; RESEARCH.md corrected in-place |
| gsd-core project-scope capability consent is a content hash over the whole bundle | Any file edit inside an already-consented bundle (even a legitimate bug fix) silently deactivates the capability — `render-hooks` just stops naming it, no error. Discovered when a post-code-review fix invalidated Phase 1's own install/consent 11 minutes after the checkpoint closed; caught only because the verifier independently re-ran `render-hooks` live instead of trusting green tests | Operational gotcha, not a beads-specific behavior — re-run `capability install --scope project` after any post-consent bundle edit, every phase, going forward |
| Installed `ship.md`'s `ship:pre` dispatch hardcodes `capId=='security'/'broken-windows'`, no generic gate-enumeration loop (unlike `ship:post`'s steps) | Discovered during Phase 3 planning (plan-checker blocker) via a full-file read of the installed workflow, not inference — Phase 3's declared `gates[]` would otherwise silently never fire, making ROADMAP.md Success Criteria 1/2 false-but-unnoticed at ship time | User overrode the no-fork-patch constraint for a machine-local `ship.md` patch, folded in as in-scope Phase 3 work (plan `03-03`) rather than deferred; also filed upstream (open-gsd/gsd-core#3554, closed 2026-08-15 as filed-without-template; re-filed as open-gsd/gsd-core#3559 with `beads`' own `capability.json` gates as the concrete repro). **Shipped and live-verified** — patch present at `$HOME/.claude/gsd-core/workflows/ship.md`, `check-shipmd-patch` exits 0, ship:pre gates confirmed to actually block/pass via a live `gsd_run check predicate` smoke test against a synthetic `BEADS.md`. Tracked via PLAN.md only, no `bd` ticket (see Constraints note above) |
| bd's real schema-version skew (DB migrated to v65 by an accidentally-shipped v1.2.1 binary; this project's v1.2.2 binary only understood v53) blocked every real `bd` operation for the full duration of Phases 1-3 and part of Phase 4 | Discovered live during Phase 4 execution when the user pointed out `bd` was actually installed with a real database, contradicting every "bd unavailable" fail-open message the project had printed since Phase 1 | Recovered via beads' own official `RECOVERY-1.2.1.md` doc: backed up `.beads/` to `.beads.backup-pre-recovery`, rolled the schema cursor back to v53 via a `dolt sql` `DELETE FROM schema_migrations WHERE version > 53` + commit. `bd` now fully functional; Phase 4's 3 plans' tasks were retroactively synced to and closed in the real database (epic `gsd-beads-i3i`), the first real end-to-end `bd` round-trip this project has ever had against its own actual database (not a scratch/`bd init --prefix live` dir) |
| `capability.json`'s `plan:post` `beads-sync` step declared `"produces": ["BEADS.md"]` — wrong; `create_issues()` only ever rewrites `PLAN.md` in place | Found by `gsd-integration-checker` during the v1.0 milestone audit, independently confirmed via direct source read (sync.py:828-892) before accepting the finding | Fixed same session (commit `4230234`): corrected to `"produces": ["PLAN.md"]`, re-installed/re-consented at project scope, 88/88 tests still green |
| PUB-03 satisfied by the documented manual `capability install` step, not an automatic bridge | Three reasons converge: REQUIREMENTS.md's own Future Requirements section already defers postinstall-hook environment research as out of scope; an automated `--yes` grant fired from a hook would defeat gsd-core's CB-3 human-gated consent check by design; PUB-04's Phase-8 ship allowlist omits `.gsd/capabilities/beads/`, so an automation targeting that path would work today and silently break at first public release | Verified 2026-08-16 from a clean `/tmp` scratch project with no prior gsd-beads state: `node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability install "<clone-root>/.gsd/capabilities/beads" --scope project --yes` followed by `capability state --raw` reported `beads` `installed: true, active: true`. Transcript in `06-01-SUMMARY.md` |
| `hooks/hooks.json` ships the bare `bd prime --hook-json` command, `.claude/settings.json` deleted in the same change | Claude Code's own SessionStart contract already fails open on a missing binary (no hand-rolled PATH guard needed); keeping both files would double-fire `bd prime` every session, since hook dedup does not cross a settings-file/plugin-hooks.json boundary | Shipped Phase 6. Live-verified twice: headless `claude -p --debug hooks` probe (executor) and a real interactive TTY session with `--debug hooks --debug-file` (user, 2026-08-16) both show `Hook SessionStart (bd prime --hook-json) provided additionalContext` exactly once. SessionStart `additionalContext` is injected silently into model context, not printed to the terminal — absence of a visible startup banner is expected, not a fire-count of zero |
| A merely checked-out gsd-beads repo (no `/plugin install` ever run) does not auto-load `hooks/hooks.json` | Resolved RESEARCH.md's open Assumption A1 empirically rather than assuming either outcome | This repo's own dev sessions now depend on the `beads@gsd-beads` plugin staying installed at local scope — left installed (not uninstalled) at the end of Phase 6 for exactly that reason |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

## v1.0 Ship Summary

Shipped 2026-08-16. 4 phases, 11 plans, 20 tasks, ~4,400 LOC (`sync.py` + `test_sync.py`).
Milestone audit: 14/14 requirements satisfied, 4/4 phases integration-verified, status `tech_debt`
(one capability.json metadata bug found and fixed same session; two minor items backlogged —
Phase 4 SUMMARY.md files missing `requirements-completed` frontmatter, and Phases 2-3-4 missing
reconciled Nyquist `VALIDATION.md` coverage — neither blocks shipped functionality).

---
*Last updated: 2026-08-16 — Phase 6 (Runtime Integration) complete: PUB-03/PUB-06 shipped and verified.*
