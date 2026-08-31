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

The capability is on by default: `beads.enabled` defaults to `true`, so a fresh install runs
with issue tracking on. Opt out by setting `beads.enabled: false` in the project's
`.planning/config.json` — every step below checks that gate first and no-ops with a visible
notice when a project has opted out. See [Configuration](#configuration) below for the full key
list.

gsd-core's own lifecycle commands drive `bd` state directly:

1. `/gsd:plan-phase` — before planning, `beads-recall` queries existing open issues so
   already-ticketed work isn't planned twice; after the plan is written, `beads-sync` creates
   one phase epic plus one `bd` issue per plan-task block, and writes the ids back into the plan
   (a `beads_epic` frontmatter key and a `<beads-id>` element per task).
2. `/gsd:execute-phase` — before a wave of tasks runs, `beads-status` puts that wave's live
   issue state into the orchestrator's context; after the wave finishes, it closes the `bd`
   issues for every task the wave completed.
3. `/gsd:verify-work` — after verification, `beads-status` refreshes the projected `BEADS.md`
   state from `bd`.
4. Shipping — immediately before ship, two blocking gates read `BEADS.md` frontmatter and
   refuse to ship while `blocking_open` or `diverged` is non-zero.

Steps 1–3 run from a `PostToolUse` hook the plugin installs; step 4 runs from gsd-core itself.
That split is not cosmetic — see [How the lifecycle steps get dispatched](#how-the-lifecycle-steps-get-dispatched).

The bare `bd` CLI still works as a manual escape hatch for inspecting or driving the same
issues by hand between lifecycle steps:

```bash
bd ready
bd update <id> --claim
bd close <id> --reason="Completed"
```

See `AGENTS.md` in this repo for the full command reference.

### How the lifecycle steps get dispatched

`capability.json` declares six `kind: "step"` hooks, one per lifecycle
point. Current gsd-core dispatches `plan:post` and `verify:post` steps
natively. The compatibility dispatcher probes the installed workflow files at
those two points and stands down when native dispatch is present, preventing
duplicate `bd` mutations.

The remaining compatibility points enter through
`gsd_run loop render-hooks <point> --raw`. The plugin's `PostToolUse` hook
(`hooks/lifecycle-dispatch.sh`) matches that Bash call and runs the declared
operation for `plan:pre`, `execute:wave:pre`, and `execute:wave:post`.
`ship:pre` remains covered by this capability's installed `ship.md`
step-dispatch patch. Every hook is `onError: skip`; before v0.3.0 the missing
compatibility dispatch was silent, so a phase could plan and execute end-to-end
with zero `bd` issues and nothing reporting it
([#2](https://github.com/davdittrich/gsd-beads/issues/2)).

The equivalent manual invocation, for a runtime with no `PostToolUse` support or for driving a
point by hand:

```bash
python3 .gsd/capabilities/beads/scripts/sync.py lifecycle-dispatch plan:post
```

Valid points are `plan:pre`, `plan:post`, `execute:wave:pre`, `execute:wave:post` and
`verify:post`. The verb always exits `0` — it honors the same `onError: skip` contract the hooks
declare — and re-reads `beads.enabled` itself, because entering from a harness hook bypasses the
capability registry that would normally evaluate each step's `when` condition.

The hook matches only a real invocation: a recognised tools shim (`gsd_run`, `gsd-tools`, or
`node …/gsd-tools.cjs`) in shell command position, followed by `loop render-hooks <point> --raw`.
A command that merely quotes or greps that string does not dispatch. And a hook-driven
`plan:post` never strips `<task>` bodies out of `PLAN.md`, whatever the read-path patch says —
only an explicit `sync.py create-issues <plan>` does that. Both guards exist because the trigger
is ultimately a substring of a shell command, so a spurious match can never be ruled out
entirely; creating a `bd` issue by mistake is recoverable, deleting task prose is not.

## Configuration

Every gsd-beads setting lives in the project's `.planning/config.json` under a single `beads`
object, and the shipped defaults are declared in
`plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`.

| Key | Type | Values | Default | Effect |
| :--- | :--- | :--- | :--- | :--- |
| `beads.enabled` | boolean | `true` / `false` | `true` | Master toggle for the beads issue-tracking capability. |
| `beads.sync_mode` | enum | `authoritative`, `mirror` | `"authoritative"` | Governs whether an explicit `sync.py create-issues <plan>` strips synced task bodies out of `PLAN.md`: `authoritative` strips once the read-path patch is present, `mirror` never strips. Never governs the hook-driven `plan:post` dispatch, which never strips either way. |
| `beads.ship_gate` | boolean | `true` / `false` | `true` | When true, `ship:pre` blocks on `BEADS.md`'s `blocking_open` or `diverged` frontmatter fields being non-zero; both gates are blocking. |
| `beads.epic_per` | enum | `phase`, `milestone` | `"phase"` | `phase`: one epic per phase, as today. `milestone`: one epic shared across every phase in the current milestone. |

```json
{
  "beads": {
    "enabled": true,
    "sync_mode": "authoritative",
    "ship_gate": true,
    "epic_per": "phase"
  }
}
```

### How a value is resolved

All four capability skills implement an identical enabled gate: the capability is disabled only
when `.planning/config.json` exists, has a `beads` object, and that object's `enabled` is
explicitly the boolean `false`. A missing file, a missing `beads` object, and a present `beads`
object with no `enabled` key all fall through to the `capability.json` default of `true`, so a
fresh install runs with tracking on.

When disabled, every lifecycle step prints a visible notice and no-ops rather than fails, since
all six steps are declared `onError: skip`.

`epic_per` is re-read fresh from `.planning/config.json` at each epic-creation call site, not
resolved once per session, and falls back to `phase` when the file is absent, the JSON is
malformed, or the key is missing.

`ship_gate` is read at `ship:pre` alongside `BEADS.md`'s `blocking_open`/`diverged` fields.
Setting it to `false` while either field is non-zero does not silently skip the gate: the bypass
is recorded as a `Beads-Override:` git trailer on the amended ship commit plus a best-effort `bd`
comment on the phase epic, and the amend is refused when HEAD is already pushed.

### Caveats

- Under `authoritative`, task content originates in PLAN.md at first sync; PLAN.md task text is
  never re-synced from later `bd` edits.
- `epic_per: milestone` is forward-only — it does not retroactively fold existing per-phase
  epics into the milestone epic.

### Environment variables

| Variable | Read by | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `CLAUDE_PLUGIN_ROOT` | `hooks/session-start.sh`, `hooks/capability-auto-install.sh` | `$(cd "$(dirname "$0")/.." && pwd)` | Resolves the plugin's own root directory. |
| `CLAUDE_CONFIG_DIR` | `hooks/capability-auto-install.sh`, `scripts/sync.py` | `$HOME/.claude` | Locates the gsd-tools resolver and the local-patch checks against `gsd-core/workflows/ship.md` and `gsd-core/workflows/execute-plan.md`. |
| `GSD_HOME` | `hooks/capability-auto-install.sh` | `$HOME` | Locates the per-capability bundle-drift hash sidecar (`.gsd/capability-auto-install-$CAP_ID.hash`). |

gsd-beads only reads these — it never sets them — and every one has a working default, so none
is required. The two `CLAUDE_CONFIG_DIR` consumers in `sync.py` probe the Claude runtime home
only; they do not check other runtime homes such as `CODEX_HOME` or `CURSOR_CONFIG_DIR`.
`sync.py`'s 15-second `bd` subprocess timeout is a module constant, not a configurable
environment variable.

### Not gsd-beads configuration

`BEADS_DIR` and `bd config set …` are `bd`-owned knobs that change `bd`'s own behaviour for
every consumer, documented in the bundled `bd` skill resources; gsd-beads neither reads nor
writes them, and they have no `.planning/config.json` equivalent. `BEADS_DIR` points a worktree
or a whole project at a beads workspace outside the tree; `bd config set no-git-ops true` keeps
`bd prime` output in stealth mode.

## Uninstall

```bash
claude plugin uninstall beads-lifecycle@gsd-beads -y
```

## Caveats

- **`bd` must be on `PATH`.** If it isn't, the SessionStart hook's `bd prime --hook-json`
  call fails, and every gsd lifecycle step that reads live `bd` state degrades to a no-op
  with a visible notice instead of crashing — beads support is fail-open by design, not a
  hard dependency.
- **Five of the six lifecycle points are dispatched by a Claude Code `PostToolUse` hook, not by
  gsd-core.** gsd-core has no generic `kind: "step"` dispatch at those points (see [How the
  lifecycle steps get dispatched](#how-the-lifecycle-steps-get-dispatched)). On a runtime with no
  `PostToolUse` support, those five points stay undispatched and only `ship:pre` runs — drive the
  rest with `sync.py lifecycle-dispatch <point>`. The `execute:wave:pre` `<beads_status>` block is
  phase-wide rather than wave-scoped for the same reason: the hook's trigger carries no wave
  plan-id list. That is a superset of the wave's issues, so no ticket pointer is lost, just less
  narrowly scoped.
- **This repository's own beads backend is Dolt-only.** There is no `.beads/issues.jsonl`
  passive export file in this repo at all — not merely a stale one. Dolt is the sole store;
  `bd dolt push`/`pull` is the sync path.
- **The SessionStart hook runs `bd prime --hook-json` on every session start.** In a project
  with no beads workspace yet, this prints nothing until `bd init` (or an existing
  `.beads/` directory) creates one — see `bd where` to check whether a workspace is active.
- **Installing via the marketplace flow (`claude plugin install`) copies the entire cloned
  repository into the installer's local plugin cache** under `~/.claude/plugins/cache/`,
  including this project's own `.planning/` and `.beads/` directories — this is a documented
  Claude Code cache behavior, not something this repo controls. The plugin *root* itself is
  the scoped `plugins/beads-lifecycle/` subdirectory, so `.planning/` and `.beads/` are not
  part of the loaded plugin. Installing is distinct from the GitHub Release archive, which
  ships only `.claude-plugin/`, `plugins/beads-lifecycle/` (the plugin's own manifest, hooks,
  skill, and `beads` capability bundle), `README.md`, and `LICENSE`.
- **`gsd-beads` is the source of exactly one capability, `beads`.** `ponytail-everywhere` and
  `sota-numerics` are separate projects living in their own repositories
  (`davdittrich/ponytail-everywhere`, `davdittrich/sota-numerics`), listed in this
  marketplace only as url-type entries pointing at those repositories. This project
  *consumes* them the same way any other user would — a normal plugin install — with no copy
  of their content vendored here.

## License

MIT — see [LICENSE](LICENSE).

## gsd-core

`gsd-beads` is a capability for [gsd-core](https://github.com/open-gsd/gsd-core). See that
project for the base planning framework this capability extends.
