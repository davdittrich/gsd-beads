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

Six `capability.json` lifecycle steps dispatch bd integration automatically — none of them can fail a phase (`onError: skip` on every one). The **Dispatched by** column matters: gsd-core reaches only `ship:pre` on its own (and only through this capability's `ship.md` patch), so the other five run from the plugin's `PostToolUse` hook instead — see **Dispatch mechanism** below.

| Point | Skill | Dispatched by | Effect |
|---|---|---|---|
| `plan:pre` | `beads-recall` | PostToolUse hook | Scans open bd issues, writes `BEADS-RECALL.md` naming any that may touch the phase about to be planned; consumed by the planner. Also runs both gsd-core patch-loss checks. |
| `plan:post` | `beads-sync` | PostToolUse hook | Parses every `PLAN.md` in the phase, creates/resolves the phase epic and one issue per task, rewrites each plan with `beads_epic`/`<beads-id>`. |
| `execute:wave:pre` | `beads-status` | PostToolUse hook | Regenerates `BEADS.md` from a live `bd` query and composes a `<beads_status>` block for the orchestrator to paste into each executor's prompt. Phase-wide, not wave-scoped — the hook's trigger carries no wave plan-id list. |
| `execute:wave:post` | `beads-status` | PostToolUse hook | Closes every task-complete bd issue across every plan in the phase (`reconcile-stale-closed`, idempotent). |
| `verify:post` | `beads-status` | PostToolUse hook | Regenerates `BEADS.md` read-only — no wave/plan context, no close dispatch. |
| `ship:pre` | `beads-status` | gsd-core (patched `ship.md`) | Records a `ship_override` if the ship gate was bypassed with open/diverged issues, and confirms the local `ship.md` patch is intact. |

## Dispatch mechanism

gsd-core (through 1.11.0) has no generic `kind: "step"` dispatch loop at five of these six points: `plan:post` and `execute:wave:post` dispatch `kind == "gate"` entries only, `execute:wave:pre` checks solely for a *contribution*, `verify:post` hardcodes `ref.skill == "secure-phase"`, and `plan:pre`'s generic contract sits behind an auto-chain + frontend-detection branch. Because every hook is `onError: skip`, a declared-but-undispatched step is silent (gh-2).

What gsd-core does still do at all five is run `gsd_run loop render-hooks <point> --raw`. `hooks/lifecycle-dispatch.sh` is a `PostToolUse` hook that matches that Bash call and runs `sync.py lifecycle-dispatch <point>` itself, returning output through `hookSpecificOutput.additionalContext`. The trigger is a call gsd-core must keep making for its own hook system to function, so a gsd-core update cannot silently strip it.

Two consequences worth knowing:

- **Claude Code only.** `PostToolUse` is a Claude Code hook. On another runtime these five points stay undispatched; run the `sync.py` verbs by hand, or use `python3 .gsd/capabilities/beads/scripts/sync.py lifecycle-dispatch <point>`.
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
