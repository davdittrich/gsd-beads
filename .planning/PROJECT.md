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

(None yet — ship to validate)

### Active

- [ ] **B1**: One beads issue per `PLAN.md` task, parented to a phase epic
- [ ] **B2**: Plan task ordering becomes beads dependencies
- [ ] **B3**: Task completion closes its issue automatically
- [ ] **B4**: Identity is bound explicitly via `beads-id:`, never by title matching
- [ ] **B5**: Sync is idempotent
- [ ] **B6**: `bd` absent, failing or locked degrades to a no-op with one visible notice
- [ ] **B7**: The planner sees open issues before planning (`BEADS-RECALL.md`)
- [ ] **B8**: The executor's prompt carries live issue state
- [ ] **B9**: A phase with unfinished blocking issues cannot ship
- [ ] **B10**: Divergence blocks and is reported; never auto-reconciled
- [ ] **B11**: `BEADS.md` is regenerated every step, never hand-edited
- [ ] **B12**: One-shot migration of `.planning/todos/pending/` into beads
- [ ] **B13**: `beads-status` prints the plan-task ↔ issue mapping on demand
- [ ] **B14**: Milestone-level epic option (`beads.epic_per=milestone`)

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
  (`gsd-`, `gsd-core-`, `anthropic-`) are rejected by the loader, so the capability id is `beads`
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
| Overlay capability (`beads`), not a gsd-core fork | Forking buys maintenance of 79 skills / 45 capabilities to add one integration and diverges from upstream permanently; overlays are a supported, tested extension point | — Pending |
| `beads.sync_mode` defaults to `authoritative` for status and content | Discuss-phase 1 reversal (2026-08-15) of the original status-only split: bd is the single editable record post-creation, `PLAN.md` is not re-synced from it — avoids a two-way content merge while keeping one authoritative owner | — Pending |
| Gate predicates read only generated artifact frontmatter (`BEADS.md`), never query `bd` directly | The only two shipped predicate kinds are `command-exists` and `artifact-frontmatter-equals`; no predicate calls an external tool | — Pending |
| `gates[].onError: skip`, never `halt` | A missing/unreadable `BEADS.md` (capability disabled, `bd` absent, first run) must never strand a finished phase — the gate blocks only on a known bad state | — Pending |

---
*Last updated: 2026-08-15 after initial ingest from docs/prd-beads-capability.md*
