---
phase: 04-adoption
reviewed: 2026-08-16T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - .gsd/capabilities/beads/scripts/sync.py
  - .gsd/capabilities/beads/capability.json
  - .gsd/capabilities/beads/tests/test_sync.py
  - .gsd/capabilities/beads/skills/beads-migrate-todos/SKILL.md
  - .gsd/capabilities/beads/skills/beads-status/SKILL.md
  - .gsd/capabilities/beads/tests/fixtures/todo-wellformed.md
  - .gsd/capabilities/beads/tests/fixtures/todo-malformed.md
findings:
  critical: 3
  warning: 2
  info: 1
  total: 6
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-08-16T00:00:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Reviewed Phase 4's additions to `sync.py` — todo migration (`migrate_todos`/`parse_todo`),
on-demand status/orphan mapping (`render_status_mapping`), and milestone-scoped epic
resolution (`resolve_milestone_epic`/`read_epic_per`) — plus the two SKILL.md files and test
fixtures that drive them. `capability.json`'s `beads.epic_per` config declaration matches
`read_epic_per`'s default and both enum values, and `test_sync.py`'s new test classes
(`TestMigrateTodos`, `TestMigrateTodosReport`, `TestMilestoneEpic`, `TestOnDemandStatus`)
exercise the documented happy paths and several fail-open paths well.

The core concern: this whole script is built around one hard invariant, tested extensively
elsewhere in the file — `bd` being absent, locked, or failing degrades every command to exit 0
with a single notice line and a `STATE.md` blocker bullet, never an uncaught exception (B6/D-08).
Three new code paths in this phase's additions break that invariant on inputs that are entirely
plausible in production (a milestone-mode sync run before `STATE.md` exists, a hand-edited
`config.json` with the wrong shape for `beads`, and a phase directory containing one malformed
`PLAN.md`) and none of them are covered by a test that proves the fail-open behavior actually
holds for the new code, unlike every comparable pre-existing code path.

## Critical Issues

### CR-01: `resolve_milestone_epic` crashes uncaught when `STATE.md` is missing

**File:** `.gsd/capabilities/beads/scripts/sync.py:499-513` (via `milestone_epic_title` at `:485-496`)
**Issue:** `resolve_milestone_epic` calls `milestone_epic_title(state_path)`, which does
`Path(state_path).read_text(encoding="utf-8")` with no existence check. `resolve_milestone_epic`
is reached from `resolve_epic` (line 579-581) whenever `beads.epic_per == "milestone"`, and
`resolve_epic` is called from inside `create_issues`'s single `try/except RuntimeError` block
(lines 838-866) — but a missing `STATE.md` raises `FileNotFoundError`, not `RuntimeError`, so it
is **not caught**. The whole point of that try/except, per its own comment ("Any RuntimeError
raised by resolve_epic/resolve_issue below is exactly that case: degrade to the same fail-open
notice, not a crash"), is the B6/D-08 fail-open contract every other bd-adjacent function in this
file is built and tested around. This one code path breaks it: a project that turns on
`beads.epic_per=milestone` before `STATE.md` exists (e.g. a very early sync, or a project that
doesn't use GSD's `STATE.md` convention at all) gets an unhandled traceback out of `create_issues`
instead of exit 0 + notice + `STATE.md` blocker bullet.
No test in `TestMilestoneEpic` exercises a missing `STATE.md` — `_write_milestone_workspace`
unconditionally writes one, so this gap has zero test coverage.
**Fix:**
```python
def milestone_epic_title(state_path):
    state_path = Path(state_path)
    if not state_path.exists():
        return "Milestone : "  # or route the caller through the same RuntimeError path
    text = state_path.read_text(encoding="utf-8")
    ...
```
or, more consistent with the rest of the file's error taxonomy, wrap the read in
`resolve_milestone_epic` and raise `RuntimeError` on a missing `STATE.md` so `create_issues`'s
existing fail-open catch handles it the same way a `bd create` failure already does.

### CR-02: `read_epic_per` crashes on a malformed (but validly-parsed) `config.json`

**File:** `.gsd/capabilities/beads/scripts/sync.py:467-482`
**Issue:** `read_epic_per` catches `json.JSONDecodeError` but not a schema mismatch:
`cfg.get("beads", {}).get("epic_per", "phase")` assumes `cfg["beads"]` is a dict when present.
A `config.json` containing `{"beads": true}` or `{"beads": "yes"}` (both trivially producible by
a hand-edit, since nothing in this script validates `config.json` against `capability.json`'s
schema before writing) parses successfully as JSON, so the existing `except
json.JSONDecodeError` never fires, and `.get("epic_per", "phase")` on a non-dict raises
`AttributeError`. `read_epic_per` is called from `resolve_epic` inside `create_issues`'s
try/except, which — same as CR-01 — only catches `RuntimeError`, so this crashes the whole sync
uncaught instead of degrading fail-open.
**Fix:**
```python
def read_epic_per(project_root):
    config_path = confined(project_root, ".planning", "config.json")
    if not config_path.exists():
        return "phase"
    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        beads_cfg = cfg.get("beads", {}) if isinstance(cfg, dict) else {}
        return beads_cfg.get("epic_per", "phase") if isinstance(beads_cfg, dict) else "phase"
    except json.JSONDecodeError:
        return "phase"
```

### CR-03: `render_status_mapping`'s task-side orphan scan is the only `parse_plan` call site in the file with no `(OSError, UnicodeDecodeError)` guard

**File:** `.gsd/capabilities/beads/scripts/sync.py:1318-1323`
**Issue:**
```python
task_side_orphans = []
for plan_path in discover_plan_files(phase_dir).values():
    _, _, tasks = parse_plan(plan_path)
    for task in tasks:
        if not task["beads_id"]:
            task_side_orphans.append((plan_path.name, task["name"]))
```
Every other place this file iterates `discover_plan_files(...).values()` and calls `parse_plan`
on each result wraps the call in `try: ... except (OSError, UnicodeDecodeError): continue` —
`collect_all_task_files` (:393-397), `resolve_milestone_epic`'s own candidate scan (:519-523),
`collect_epic_task_ids` (:643-647), `resolve_phase_epic` (:1105-1109), `_resolve_task_ordinal_map`
(:1126-1130), `render_wave_status_block` (:1392-1396). This one — new in this phase, per its own
docstring ("new logic, no existing function surfaces this") — is the sole exception. A single
unreadable or non-UTF-8 `PLAN.md` anywhere in the phase directory (e.g. a `.bak` copy someone left
with a `PLAN.md`-matching name and stale/binary content, or a permissions issue) takes down the
entire on-demand `status` report with an uncaught exception, where the read-only nature of this
command (T-04-05, explicitly designed never to touch bd state) makes a hard crash a particularly
poor failure mode for what's meant to be a safe diagnostic view.
**Fix:**
```python
    for plan_path in discover_plan_files(phase_dir).values():
        try:
            _, _, tasks = parse_plan(plan_path)
        except (OSError, UnicodeDecodeError):
            continue
        for task in tasks:
            if not task["beads_id"]:
                task_side_orphans.append((plan_path.name, task["name"]))
```

## Warnings

### WR-01: `resolve_milestone_epic` gives no divergence signal when it creates a second epic for the same milestone

**File:** `.gsd/capabilities/beads/scripts/sync.py:499-542`
**Issue:** When none of the scanned candidate epic ids' live `bd show` titles match the freshly
computed `milestone_epic_title`, `resolve_milestone_epic` silently falls through to `bd create` a
brand-new epic (lines 539-542) with no printed message at all. Contrast this with the parallel
per-phase case in `resolve_epic` (the `stale_epic_id` path, lines 569-593), where an epic id that
no longer resolves prints `"divergence: stored beads_epic ... not found in bd"` specifically so a
resync after external state drift is never silent (this is the exact WR-02 fix from an earlier
phase, called out by name in that code's own docstring). If `STATE.md`'s `milestone`/
`milestone_name` frontmatter is edited mid-milestone (a typo fix, a rename), every subsequent sync
in that milestone will fail every title match and quietly fork the milestone across a second epic
with zero visible signal to the user — the same failure shape WR-02 exists to prevent one level
down, reintroduced here one level up.
**Fix:** Print a divergence notice (mirroring the `stale_epic_id` message) whenever
`candidate_ids` is non-empty but none matched, before creating the fresh epic — e.g.:
```python
    if candidate_ids:
        print(
            f"divergence: {len(candidate_ids)} existing epic(s) found for this milestone but "
            f"none matched title {title!r} -- creating a new epic (STATE.md milestone/"
            "milestone_name may have changed)"
        )
```

### WR-02: `parse_todo`'s `## Problem` section is silently dropped to empty when a todo has no `## Solution` heading

**File:** `.gsd/capabilities/beads/scripts/sync.py:50, 257-258`
**Issue:** `PROBLEM_RE = re.compile(r"^##\s*Problem\s*\n(.*?)(?=^##\s*Solution\s*$)", ...)`
requires a literal `## Solution` heading to exist later in the body as its lookahead anchor. A
hand-authored or slightly malformed todo that has a `## Problem` section but no `## Solution`
heading (missing entirely, or spelled/cased differently) makes `PROBLEM_RE.search(body)` return
`None`, so `problem` silently becomes `""` — the real problem text is dropped from the migrated
bd issue's description with no error, no "could not be interpreted" report entry, and no signal
that anything was lost. This is a real (if narrow) data-loss risk in a one-shot, delete-on-success
migration (`todo_path.unlink()` at line 343 fires right after a successful `bd create`, so the
original text is gone once this happens). `parse_todo`'s own docstring already treats a missing
`severity`/`title` as a hard `ValueError`-raising precondition; a `## Problem` section with no
matching `## Solution` should arguably fail the same way rather than degrade silently.
**Fix:** Either require both sections to be present (raise `ValueError` when `problem_m` is
`None`, matching the `title`/`severity` precondition style already used), or fall back to
capturing everything after `## Problem` to end-of-body when no `## Solution` heading is found,
so the text is never dropped:
```python
problem_m = PROBLEM_RE.search(body) or re.search(r"^##\s*Problem\s*\n(.*)", body, re.MULTILINE | re.DOTALL)
```

## Info

### IN-01: `read_epic_per`/new-function `run_bd` calls don't catch `subprocess.TimeoutExpired`, consistent with (but not fixed by) the rest of the file

**File:** `.gsd/capabilities/beads/scripts/sync.py` (e.g. `migrate_todos:322-337`, `resolve_milestone_epic:529, 539`)
**Issue:** `bd_available()` (the up-front probe) is the only place in the entire file that catches
`subprocess.TimeoutExpired`/`OSError` around a `run_bd`/`subprocess.run` call. Every subsequent
`run_bd` call — including the new ones in `migrate_todos`'s per-todo `bd create` loop and
`resolve_milestone_epic`'s candidate `bd show`/`bd create` calls — has no such guard, so a `bd`
process that hangs or times out mid-run (rather than failing fast with a non-zero exit, which
*is* handled) raises `subprocess.TimeoutExpired` uncaught. This is a pre-existing, file-wide
pattern rather than something newly introduced by this phase (confirmed: only `bd_available`
line 87 and `_head_already_pushed` line 1467 catch it anywhere in the file), so it is not
attributed as a regression here, but the new functions inherit the same gap and a `migrate_todos`
mid-batch timeout would abort the whole migration with some todos already deleted+migrated and
others left in an unreported, ambiguous state (no "could not be interpreted" nor "bd create
failed" entry — the process just dies).
**Fix:** Out of scope for a surgical fix to this phase alone (would touch every `run_bd` call
site file-wide); worth a follow-up ticket to wrap `run_bd` itself with a `TimeoutExpired` ->
treated-as-failure translation at the single call-through point, so every caller inherits the
fix for free instead of needing N individual try/excepts.

---

_Reviewed: 2026-08-16T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
