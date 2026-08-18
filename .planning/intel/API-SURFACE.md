# API Surface

> Generated from `.planning/intel/api-map.json`. Do not edit by hand.

> **Warning:** api-map.json is stale (>24 hours old). Data below may be out of date.

## `CLI sync.py create-issues`

- **method:** CLI
- **path:** sync.py create-issues <plan_path>
- **params:** plan_path
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** Sync a PLAN.md's <task> elements into bd issues under a phase (or milestone) epic; writes back <beads-id>/beads_epic into PLAN.md. Invoked by beads-sync SKILL.md at plan:post.

## `CLI sync.py close-wave`

- **method:** CLI
- **path:** sync.py close-wave <phase_dir> <plan_ids...>
- **params:** phase_dir, plan_ids
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** Batch-close every completed task's bd issue across every plan in a wave, idempotently (filter_open_ids).

## `CLI sync.py beads-recall`

- **method:** CLI
- **path:** sync.py beads-recall <phase_dir>
- **params:** phase_dir
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** Scan every open, non-epic bd issue and write {padded_phase}-BEADS-RECALL.md, scoping issues to this phase via file-path match or description substring match. Invoked at plan:pre.

## `CLI sync.py regenerate-beads-md`

- **method:** CLI
- **path:** sync.py regenerate-beads-md <phase_dir>
- **params:** phase_dir
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** Fully overwrite {padded_phase}-BEADS.md from a live `bd list --parent <epic>` query: open/closed/blocking_open/diverged frontmatter plus a per-issue table. Invoked at execute:wave:pre, execute:wave:post, verify:post.

## `CLI sync.py wave-status-block`

- **method:** CLI
- **path:** sync.py wave-status-block <phase_dir> <plan_ids...>
- **params:** phase_dir, plan_ids
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** Regenerate BEADS.md then print a <beads_status> block naming exactly this wave's synced issues, for injection into the executor prompt.

## `CLI sync.py ship-override`

- **method:** CLI
- **path:** sync.py ship-override <phase_dir>
- **params:** phase_dir
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** Record a beads.ship_gate=false bypass via `git commit --amend --trailer` (refuses if HEAD is already pushed) plus a best-effort `bd comment` mirror on the phase epic. Invoked at ship:pre when the ship gate is bypassed.

## `CLI sync.py check-shipmd-patch`

- **method:** CLI
- **path:** sync.py check-shipmd-patch [--ship-md-path <path>]
- **params:** --ship-md-path
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** Read-only diagnostic: reports whether GSD-CORE-PATCH.md's ship:pre dispatch patch is present in the installed ship.md. Called from beads-status (ship:pre) and beads-recall (plan:pre).

## `CLI sync.py migrate-todos`

- **method:** CLI
- **path:** sync.py migrate-todos
- **params:** 
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** One-shot migration of every parseable .planning/todos/pending/*.md file into a mapped bd issue, deleting the source file on success.

## `CLI sync.py status`

- **method:** CLI
- **path:** sync.py status [phase_dir]
- **params:** phase_dir
- **file:** .gsd/capabilities/beads/scripts/sync.py
- **description:** On-demand, read-only plan-task <-> bd issue mapping view for a phase (defaults to STATE.md's current_phase), including bd-side and task-side orphans. Never mutates bd.
