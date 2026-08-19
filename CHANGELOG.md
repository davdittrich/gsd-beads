# Changelog

Versions in this file track `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`.

## 0.3.0

### Fixed
- **Four of the six declared lifecycle hooks never dispatched, silently**
  ([#2](https://github.com/davdittrich/gsd-beads/issues/2)). `capability.json` declares six
  `kind: "step"` hooks; gsd-core 1.10.0 reaches only `ship:pre`, and only because this capability
  patches a dispatch loop into `ship.md`. At `plan:post` and `execute:wave:post` gsd-core
  dispatches `kind == "gate"` entries only, at `execute:wave:pre` it checks solely for a
  *contribution*, and at `verify:post` its step loop is hardcoded to
  `ref.skill == "secure-phase"`. `plan:pre`'s generic step contract exists but sits behind an
  auto-chain + frontend-detection branch a manual `/gsd:plan-phase` never enters. Every hook is
  `onError: skip`, so a phase could plan and execute end-to-end with **zero bd issues created**
  and nothing anywhere reporting it: no `PLAN.md` carrying `beads_epic`, no task carrying
  `<beads-id>`, no `BEADS.md` or `BEADS-RECALL.md` written, `bd list` returning
  `No issues found.` throughout.
- **The patch-loss detector shared the failure mode of the thing it protects.**
  `beads-recall`'s Step 3.5 was placed at `plan:pre` on the grounds that `plan:pre` was natively
  dispatched — it was not, for a manual invocation. It now runs from the same hook as the rest.

### Added
- **`hooks/lifecycle-dispatch.sh`** — a `PostToolUse` hook that matches the
  `gsd_run loop render-hooks <point> --raw` call gsd-core still makes at each dead point and runs
  the operation itself, returning output through `hookSpecificOutput.additionalContext`. The
  trigger is a call gsd-core must keep making for its own hook system to function, so unlike a
  patched workflow file it cannot be silently dropped by a gsd-core update.
- **`sync.py lifecycle-dispatch <point>`** — the verb the hook drives, also usable by hand on a
  runtime without `PostToolUse`. Always exits `0`, honoring the `onError: skip` contract every
  hook declares, and re-reads `beads.enabled` itself since entering from a harness hook bypasses
  the capability registry that evaluates each step's `when` condition.
- CI now runs the `sync.py` test suite. It had 134 cases and none of them ran there.

### Known limits
- `PostToolUse` is a Claude Code hook. On another runtime the five points stay undispatched and
  only `ship:pre` runs; drive the rest with `sync.py lifecycle-dispatch <point>`.
- The `execute:wave:pre` `<beads_status>` block is phase-wide rather than wave-scoped, because
  the render-hooks call carries no wave plan-id list. A superset of the wave's issues, so no
  ticket pointer is lost. For the same reason `execute:wave:post` uses the phase-wide idempotent
  `reconcile-stale-closed` backstop rather than `close-wave`.
- A project that planned phases before 0.3.0 has no issues for them. Backfill with
  `sync.py create-issues <plan>` per plan — and note that under `sync_mode: authoritative` this
  strips `<task>` bodies out of `PLAN.md`, so confirm the content landed in `bd` before
  committing, particularly if `.beads/` is gitignored.

## 0.2.0

### Changed
- **`beads.enabled` now defaults to `true`**: a fresh install runs with issue tracking on out of
  the box. Opting out is now the explicit action — set `beads.enabled: false` in a project's
  `.planning/config.json`. The four beads skills' Step 1 config gates were inverted to match, so
  an absent key resolves to the shipped default rather than stopping at the gate.

### No regression for existing installs
- A project that already sets `beads.enabled` explicitly in `.planning/config.json` keeps its
  current behavior unchanged — an explicit value always wins over the shipped default. Only
  installs that never set the key pick up the new default.
