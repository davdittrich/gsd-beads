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
- Existing `<beads-id>` values are verified before any create. Exact `auto` and
  `tracer` tasks project that authority as `tracker-id="beads:<id>"`; excluded
  task types never gain `tracker-id`. A newly created excluded task still gains
  its missing `<beads-id>` on first sync; otherwise its task bytes remain unchanged.
- A renamed task resolves to the same issue.
- `PLAN.md` frontmatter carries `beads_epic` once the phase's tasks have synced.
- `beads.epic_per` (`phase` default, or `milestone`) controls whether epics are per-phase or shared across a milestone.

## Sync points

Six `capability.json` lifecycle steps dispatch bd integration automatically — none of them can fail a phase (`onError: skip` on every one). The **Dispatched by** column distinguishes current gsd-core native dispatch, compatibility-hook dispatch, and the installed ship patch.

| Point | Skill | Dispatched by | Effect |
|---|---|---|---|
| `plan:pre` | `beads-recall` | PostToolUse hook | Scans open bd issues, writes `BEADS-RECALL.md` naming any that may touch the phase about to be planned; consumed by the planner. Also runs both gsd-core patch-loss checks. |
| `plan:post` | `beads-sync` | gsd-core native step dispatch | Parses every `PLAN.md`, verifies bound task identities before mutation, creates/resolves the epic and task issues, writes missing `beads_epic`/`<beads-id>` values, and projects exact `auto`/`tracer` tasks as `tracker-id="beads:<id>"`. |
| `execute:wave:pre` | `beads-status` | PostToolUse hook | Regenerates `BEADS.md` from a live `bd` query and composes a `<beads_status>` block for the orchestrator to paste into each executor's prompt. Phase-wide, not wave-scoped — the hook's trigger carries no wave plan-id list. |
| `execute:wave:post` | `beads-status` | PostToolUse hook | Closes every task-complete bd issue across every plan in the phase (`reconcile-stale-closed`, idempotent). |
| `verify:post` | `beads-status` | gsd-core native step dispatch | Regenerates `BEADS.md` read-only — no wave/plan context, no close dispatch. |
| `ship:pre` | `beads-status` | installed `ship.md` step-dispatch patch | Records a `ship_override` if the ship gate was bypassed with open/diverged issues, and confirms the local `ship.md` patch is intact. |

## Dispatch mechanism

Current gsd-core dispatches `plan:post` and `verify:post` steps natively. The compatibility dispatcher probes the installed workflow files at those two points and stands down when native dispatch is present, preventing duplicate `bd` mutations.

The remaining compatibility points enter through `gsd_run loop render-hooks <point> --raw`. `hooks/lifecycle-dispatch.sh` is a `PostToolUse` hook that matches that Bash call and runs `sync.py lifecycle-dispatch <point>` for `plan:pre`, `execute:wave:pre`, and `execute:wave:post`. `ship:pre` remains covered by the installed `ship.md` step-dispatch patch.

Two consequences worth knowing:

- On a runtime without `PostToolUse`, `plan:post` and `verify:post` still dispatch natively. Drive `plan:pre`, `execute:wave:pre`, and `execute:wave:post` with `python3 .gsd/capabilities/beads/scripts/sync.py lifecycle-dispatch <point>`; `ship:pre` still depends on the installed `ship.md` patch.
- **`beads.enabled` is re-read by `sync.py`**, not by the capability registry — the hook bypasses the registry that evaluates each step's `when` condition.

## Ship gate

`beads.ship_gate` (default `true`) blocks `ship:pre` when `BEADS.md`'s frontmatter shows `blocking_open > 0` or `diverged > 0`. Disable via `.planning/config.json`'s `beads.ship_gate: false` — a bypass under that setting gets recorded as a `ship_override` (git trailer + bd comment) rather than silently ignored.

## Failure mode

- Every sync-point dispatch above is `onError: skip`.
- A `bd` failure (binary absent, locked, unreachable) degrades the lifecycle to no-op for that step.
- The step appends a `### Blockers/Concerns` note to `STATE.md` when it degrades.
- No sync-point dispatch ever fails a phase.

## Config keys

- `beads.enabled` (default `true`) — master toggle for this whole integration.
- `beads.sync_mode` (default `authoritative`) — governs whether an explicit `create-issues` strips synced `<task>` bodies out of `PLAN.md`. `authoritative`: strips once the read-path patch is present; `bd` owns task content after first sync, and `PLAN.md` task text is never re-synced from later `bd` edits. `mirror`: never strips. The hook-driven `plan:post` dispatch never strips either way.
- `beads.ship_gate` (default `true`) — see Ship gate above.
- `beads.epic_per` (default `phase`) — see Phase epics above.
