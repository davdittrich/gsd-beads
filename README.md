# gsd-beads

Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle

## What it does

[gsd-core](https://github.com/open-gsd/gsd-core) is a Claude Code planning framework that
turns a feature request into phased plans, tracked execution, and a ship gate, orchestrated
through `/gsd:*` commands and markdown under a project's `.planning/` directory.
[Beads](https://github.com/gastownhall/beads) (`bd`) is a durable, git-native issue tracker
with a local Dolt database, issue dependencies, and blocker tracking, built for work that
has to survive multi-session handoff between people and agents.

`gsd-beads` is a gsd-core capability — an installable overlay, not a fork — that makes `bd`
the single source of truth for gsd's task state: one beads issue per plan task, task
dependencies become `bd dep` links, task completion closes its issue, and gsd's
planner/executor/ship gate all read live `bd` state instead of duplicating it as
hand-maintained `.planning/` prose.

### Why not just use gsd-core's built-in tracking?

gsd-core's `.planning/` markdown is a good fit for plan *content* — what a phase is for, how a
task should be approached, what "done" means. It is a poor fit for task *state*. Without a
bridge, a developer who uses both trackers maintains two hand-written representations of the
same work by hand: every planned task gets re-typed as an issue, every finished task gets
closed twice, and the two drift silently because nothing compares them. `gsd-beads` makes `bd`
the single source of truth for task state, so no duplicated task-state bookkeeping survives in
`.planning/`.

| Need | `.planning/` markdown | beads |
| :--- | :--- | :--- |
| Query "what can I work on now?" | read files, reason | `bd ready` |
| Dependencies and blocking | prose ordering | first-class, enforced |
| Status across phases | per-phase files | one query |
| Survives milestone archival | archived away | persists |
| Visible outside one project | no | yes |
| Machine-updatable without rewriting prose | no | yes |

## Requirements

- `bd` on `PATH`
- Python 3 (standard library only)
- gsd-core >= 1.6.0

## Install

```bash
claude plugin marketplace add davdittrich/gsd-beads
claude plugin install beads-lifecycle@gsd-beads -y
```

### Example workflow

The capability is off until `beads.enabled` is set `true` in the project's
`.planning/config.json` — every step below checks that gate first and no-ops with a visible
notice otherwise.

With it on, gsd-core's own lifecycle commands drive `bd` state directly:

1. `/gsd-plan-phase` — before planning, `beads-recall` queries existing open issues so
   already-ticketed work isn't planned twice; after the plan is written, `beads-sync` creates
   one phase epic plus one `bd` issue per plan-task block, and writes the ids back into the plan
   (a `beads_epic` frontmatter key and a `<beads-id>` element per task).
2. `/gsd-execute-phase` — before a wave of tasks runs, `beads-status` puts that wave's live
   issue state into the orchestrator's context; after the wave finishes, it closes the `bd`
   issues for every task the wave completed.
3. `/gsd-verify-work` — after verification, `beads-status` refreshes the projected `BEADS.md`
   state from `bd`.
4. Shipping — immediately before ship, two blocking gates read `BEADS.md` frontmatter and
   refuse to ship while `blocking_open` or `diverged` is non-zero.

The bare `bd` CLI still works as a manual escape hatch for inspecting or driving the same
issues by hand between lifecycle steps:

```bash
bd ready
bd update <id> --claim
bd close <id> --reason="Completed"
```

See `AGENTS.md` in this repo for the full command reference.

## Uninstall

```bash
claude plugin uninstall beads -y
```

## Caveats

- **`bd` must be on `PATH`.** If it isn't, the SessionStart hook's `bd prime --hook-json`
  call fails, and every gsd lifecycle step that reads live `bd` state degrades to a no-op
  with a visible notice instead of crashing — beads support is fail-open by design, not a
  hard dependency.
- **This repository's own beads backend is Dolt-only.** There is no `.beads/issues.jsonl`
  passive export file in this repo at all — not merely a stale one. Dolt is the sole store;
  `bd dolt push`/`pull` is the sync path.
- **The SessionStart hook runs `bd prime --hook-json` on every session start.** In a project
  with no beads workspace yet, this prints nothing until `bd init` (or an existing
  `.beads/` directory) creates one — see `bd where` to check whether a workspace is active.
- **Installing via the marketplace flow (`claude plugin install`) copies the entire cloned
  repository into the installer's local plugin cache** under `~/.claude/plugins/cache/`,
  including this project's own `.planning/` and `.beads/` directories — this is a documented
  Claude Code cache behavior, not something this repo controls. It is distinct from the
  GitHub Release archive, which ships only `.claude-plugin/`, `hooks/`, `.agents/skills/`,
  `README.md`, and `LICENSE`.

## License

MIT — see [LICENSE](LICENSE).

## gsd-core

`gsd-beads` is a capability for [gsd-core](https://github.com/open-gsd/gsd-core). See that
project for the base planning framework this capability extends.
