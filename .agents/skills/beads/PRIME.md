# gsd-core + beads

This project runs gsd-core's plan/execute/verify/ship lifecycle on top of `bd`. Bare `bd` CLI usage (`bd ready`, `bd show`, `bd update --claim`, etc.) lives in the `beads` skill — this file covers gsd-core integration only, nothing that repeats.

## Ownership

- `bd` owns task **state** — status, assignee, dependencies.
- `.planning/` owns **intent** — `PLAN.md`, `SUMMARY.md`, `ROADMAP.md` are the source of truth for what a task is and why.
- Task status is never mirrored into a markdown checklist.
- If it's not in `bd`, it isn't tracked.

## Phase epics

- One epic per phase.
- One bd issue per `<task>` element in a `PLAN.md`.
- Identity binds through the plan's `beads_epic` frontmatter key and each task's `<beads-id>` element — never by title match.
- A renamed task resolves to the same issue.
- `PLAN.md` frontmatter carries `beads_epic` once the phase's tasks have synced.
- `beads.epic_per` (`phase` default, or `milestone`) controls whether epics are per-phase or shared across a milestone.

## Sync points

Six `capability.json` lifecycle steps dispatch bd integration automatically — none of them can fail a phase (`onError: skip` on every one):

| Point | Skill | Effect |
|---|---|---|
| `plan:pre` | `beads-recall` | Scans open bd issues, writes `BEADS-RECALL.md` naming any that may touch the phase about to be planned; consumed by the planner. |
| `plan:post` | `beads-sync` | Parses the just-written `PLAN.md`, creates/resolves the phase epic and one issue per task, rewrites the plan with `beads_epic`/`<beads-id>`. |
| `execute:wave:pre` | `beads-status` | Regenerates `BEADS.md` from a live `bd` query and composes the wave's `<beads_status>` block for the orchestrator to paste into each executor's prompt. |
| `execute:wave:post` | `beads-status` | Batch-closes every completed task's bd issue across every plan that finished in the wave. |
| `verify:post` | `beads-status` | Regenerates `BEADS.md` read-only — no wave/plan context, no close dispatch. |
| `ship:pre` | `beads-status` | Records a `ship_override` if the ship gate was bypassed with open/diverged issues, and confirms the local `ship.md` patch is intact. |

## Ship gate

`beads.ship_gate` (default `true`) blocks `ship:pre` when `BEADS.md`'s frontmatter shows `blocking_open > 0` or `diverged > 0`. Disable via `.planning/config.json`'s `beads.ship_gate: false` — a bypass under that setting gets recorded as a `ship_override` (git trailer + bd comment) rather than silently ignored.

## Failure mode

- Every sync-point dispatch above is `onError: skip`.
- A `bd` failure (binary absent, locked, unreachable) degrades the lifecycle to no-op for that step.
- The step appends a `### Blockers/Concerns` note to `STATE.md` when it degrades.
- No sync-point dispatch ever fails a phase.

## Config keys

- `beads.enabled` (default `true`) — master toggle for this whole integration.
- `beads.sync_mode` (default `authoritative`) — `bd` owns task content after first sync; `PLAN.md` task text is never re-synced from later `bd` edits.
- `beads.ship_gate` (default `true`) — see Ship gate above.
- `beads.epic_per` (default `phase`) — see Phase epics above.
