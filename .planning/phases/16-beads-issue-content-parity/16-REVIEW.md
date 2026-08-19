---
phase: 16-beads-issue-content-parity
reviewed: 2026-08-19T00:18:53Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md
findings:
  critical: 2
  warning: 2
  info: 1
  total: 5
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-08-19T00:18:53Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Phase 16 adds content-parity between PLAN.md and `bd`: `_task_description`/`_epic_description`
render real content into `bd create -d`/`--acceptance` (16-01), a phase-wide reconciliation
backstop closes stale issues (16-02), `strip_task_bodies` turns a synced `auto`/`tracer` task
block into a pointer once the machine-local `execute-plan.md` read patch is verified present
(16-03), and that patch is installed and registered (16-04). The 125-test suite is green and the
mechanics that ARE tested (strip/checkpoint-exclusion, patch detection, reconciliation
idempotency) are solid — the reverse-splice technique, the two-gate strip predicate, and the
fail-open scaffolding are all correctly implemented and well covered.

Two real gaps survived the test suite because both sit outside the paths the new tests actually
exercise: (1) `checkpoint:*`-typed tasks — which DO flow through `resolve_issue`'s create path,
unlike the *strip* path they are correctly excluded from — get an explicitly empty `bd`
description, silently failing the phase's own D-06 content-parity goal for a real, common task
type (blocking-approval gates); and (2) the new `check_execute_plan_patch()` call inside
`create_issues` sits outside the function's existing `try/except RuntimeError` fail-open zone, so
a file-read failure on the machine-local patch file leaves newly-created `bd` issues orphaned
from PLAN.md (their `<beads-id>` never gets written back), risking duplicate issue creation on
the next sync retry. A third, lower-confidence robustness gap (`get_milestone_bullet`'s
unanchored substring match) is noted as a warning.

## Critical Issues

### CR-01: `resolve_issue` writes an explicitly empty `bd` description for every checkpoint-typed task, silently failing D-06 for a real task type

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:331-370` (`_task_description`), `:762-783` (`resolve_issue`)

**Issue:** `create_issues` calls `resolve_issue(task, ...)` for **every** task in a plan, regardless
of `type` (sync.py:1130) — `checkpoint:decision`/`checkpoint:human-verify` tasks are not excluded
from issue *creation*, only from the *strip* step (D-03 correctly scopes the exclusion to
`strip_task_bodies` only, per `16-CONTEXT.md`'s D-03 entry and `strip_task_bodies`'s own
docstring). But `_task_description(task)` only knows about the `auto`/`tracer` field set
(`read_first`, `precondition`, `behavior`, `action`, `verify`, `done`, `files`) — `parse_plan()`
never extracts a checkpoint task's real content (`<decision>`, `<context>`, `<options>`,
`<selection-prompt>`, `<what-built>`, `<how-to-verify>`, `<resume-signal>`). For a freshly-created
checkpoint task, every one of those fields is empty/`None`, so `_task_description` returns `""`,
and `resolve_issue`'s `argv = ["bd", "create", title, "-d", _task_description(task)]` unconditionally
appends `-d ""` — unlike `resolve_epic`/`resolve_milestone_epic`, which both guard with
`if description: argv += ["-d", description]` specifically so an empty description is never
written (verified live: `bd create ... -d ""` exits 0 and produces no `description` key in
`bd show --json` at all, so the guard would have been free to add and is simply missing here).

This directly violates 16-01-PLAN.md's own must-have — `"A task issue created by sync.py
create-issues returns a non-empty description from bd show <id> --json (D-06)"` — for checkpoint
tasks, which are a real, common pattern in this project (Phase 15's public-repo-push blocking
gates). Zero test in `TestTaskDescription`/`TestCreateIssues`/`TestCreateIssuesStripGate` exercises
`resolve_issue`'s *create* path for a checkpoint-typed task — `TestStripTaskBodies`'s checkpoint
fixture tasks (`fixture-4`, `fixture-5`) are pre-seeded with a `<beads-id>`, so they only exercise
`resolve_issue`'s early-return (already-resolved) branch, never the `bd create` branch. Live
verification:

```
$ python3 - <<'PY'
import sync
task = {"name": "Task 4: Approve the approach", "name_end": 0, "beads_id": None, "files": [],
        "type": "checkpoint:decision", "read_first": "", "precondition": None, "behavior": "",
        "action": "", "verify": "", "acceptance_criteria": "", "done": ""}
print(repr(sync._task_description(task)))
PY
''
```

**Fix:** Either (a) give checkpoint tasks their own content renderer that folds in their real
fields (`decision`/`context`/`options`/`selection-prompt` or `what-built`/`how-to-verify`/
`resume-signal`) before `resolve_issue` calls `bd create`, matching the epic renderers' pattern of
"one renderer per content shape"; or, at minimum, (b) apply the same empty-guard `resolve_epic`
already uses so an empty description is never explicitly written:

```python
argv = ["bd", "create", title]
description = _task_description(task)
if description:
    argv += ["-d", description]
if task["acceptance_criteria"]:
    argv += ["--acceptance", task["acceptance_criteria"]]
```

Option (b) alone does not close the content-parity gap for checkpoint tasks (their issue would
still carry no real description) but at least matches this phase's own established discipline and
stops writing a value the code elsewhere treats as meaningfully absent.

### CR-02: `check_execute_plan_patch()`'s new call site in `create_issues` sits outside the function's fail-open guard, risking orphaned bd issues on failure

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1148-1164`

**Issue:** `create_issues` wraps `resolve_epic`/`resolve_issue` in a `try/except RuntimeError`
(sync.py:1115-1143) specifically so a `bd`-failing-mid-run leaves the system fail-open (print
`NOTICE`, append a `STATE.md` blocker, return 0 — B6/D-08's documented contract, applied
consistently everywhere else in this file). The rewrite-and-strip block that plan 16-03 added
(`check_execute_plan_patch()` at line 1156, `strip_task_bodies` at 1157) runs **after** that
`try/except` closes, guarding nothing:

```python
    except RuntimeError as exc:
        print(NOTICE)
        ...
        return 0
    ...
    if task_updates or epic_created:
        new_text = rewrite_plan(text, epic_id, epic_created, task_updates)
        newly_created_ids = {issue_id for _, issue_id in task_updates}
        if newly_created_ids:
            if check_execute_plan_patch() == 0:   # <-- unguarded file read
                new_text = strip_task_bodies(new_text, newly_created_ids)
            ...
        plan_path.write_text(new_text, encoding="utf-8")   # <-- beads-id never written on crash
```

`check_execute_plan_patch()` performs `Path(...).exists()` then `.read_text(encoding="utf-8")` on
a machine-local file this script does not control (`$HOME/.claude/gsd-core/workflows/
execute-plan.md`, or `CLAUDE_CONFIG_DIR`'s equivalent) — a permission error, a mid-write race (this
project's own `16-01-SUMMARY.md` documents an actual concurrent-session file-content race against
this same machine's `.gsd/capabilities/beads/` tree during this very phase), or a non-UTF-8 byte
sequence in that file raises an uncaught `OSError`/`UnicodeDecodeError`. By this point in
`create_issues`, `bd create` has **already succeeded** for every task in `task_updates` — real `bd`
issues exist. If the read then throws, the exception propagates all the way out of `create_issues`
(uncaught by anything in `main()` either), so `plan_path.write_text(new_text, ...)` never runs and
the just-created issues' `<beads-id>` values are never written back into PLAN.md. The next sync
run sees those tasks as still lacking a `<beads-id>` and creates a **second** `bd` issue for each,
duplicating work — the exact class of failure the rest of this script's B6/RuntimeError-catch
discipline exists to prevent.

**Fix:** Move the `check_execute_plan_patch()` call (and, for symmetry, the `strip_task_bodies`
call, though it is pure string manipulation and much lower risk) inside the existing fail-open
try/except, or wrap it in its own narrow `try/except (OSError, UnicodeDecodeError)` that degrades
to "leave content in place" (the same outcome the function already produces for the documented
absent-patch case) rather than letting an unrelated I/O error abort the write of already-created
issue ids:

```python
        newly_created_ids = {issue_id for _, issue_id in task_updates}
        if newly_created_ids:
            try:
                patch_present = check_execute_plan_patch() == 0
            except (OSError, UnicodeDecodeError) as exc:
                print(f"beads-sync: could not verify execute-plan.md patch ({exc}) -- "
                      "leaving task content in PLAN.md")
                patch_present = False
            if patch_present:
                new_text = strip_task_bodies(new_text, newly_created_ids)
        plan_path.write_text(new_text, encoding="utf-8")
```

## Warnings

### WR-01: `get_milestone_bullet` uses unanchored substring containment, risking a false match against an unrelated bullet

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:591-611`

**Issue:** `get_milestone_bullet` is explicitly documented as "modeled on `get_phase_header`", but
`get_phase_header`'s match is anchored (`r"^###\s+(Phase\s+0*{int(phase_num)}\s*:.*)$"` — an exact
numeric match, no substring risk), while `get_milestone_bullet`'s is a bare containment check:

```python
for line in section_m.group(1).splitlines():
    line = line.strip()
    if line.startswith("-") and milestone in line:
        return line
```

A milestone token that is a substring of another milestone's bullet text (e.g. a bare `"v1"`
matching `"v1.0"`, `"v1.1"`, and `"v1.2"` bullets indiscriminately, or any token that happens to
appear inside a *different* milestone's descriptive prose) returns the **first** such line, which
may not be the milestone actually named by `STATE.md`'s frontmatter. This silently writes the
wrong milestone's scope description into the milestone epic's `bd` `-d` field, and there is no
test in `TestEpicDescription` covering a collision case (`test_get_milestone_bullet_hit` uses two
bullets, `v1.0` and `v1.2`, that happen not to collide as substrings of each other, so the gap is
untested). The current single-milestone-in-flight ROADMAP.md (`v1.0`/`v1.1`/`v1.2`, each
minor-version-qualified) makes this unlikely to fire today, but the function makes no such
guarantee and nothing prevents a future milestone token that does collide.

**Fix:** Anchor the match to the bullet's own leading token, e.g. `re.match(rf"^-\s*\**{re.escape(milestone)}\b", line)`, or require a following word boundary/space after the token, mirroring `get_phase_header`'s precision rather than a bare `in` check.

### WR-02: `check_execute_plan_patch()` has no I/O error handling, breaking the file's otherwise-consistent B6 fail-open discipline

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1876-1924`

**Issue:** Every other filesystem read in `sync.py` that touches artifact-adjacent or
externally-editable content is wrapped in `try/except (OSError, UnicodeDecodeError)` (e.g.
`collect_all_task_files`, `resolve_milestone_epic`'s plan scan, `resolve_phase_epic`). Both
`check_shipmd_patch` (pre-existing) and its new sibling `check_execute_plan_patch` read a
machine-local file with a bare `.read_text(encoding="utf-8")` and no such guard. This was a latent,
low-traffic gap for `check_shipmd_patch` (invoked once per explicit CLI call or `ship:pre`
dispatch). Plan 16-03 clones the same unguarded pattern for `check_execute_plan_patch`, but now
wires it into `create_issues` (see CR-02) — a call site that fires on every `sync.py create-issues`
run with at least one new `auto`/`tracer` task, i.e. far more frequently than `check_shipmd_patch`
ever ran. The clone-without-hardening choice increases this gap's practical blast radius.

**Fix:** See CR-02's fix — wrapping the call site closes both issues at once; alternatively harden
`check_execute_plan_patch`/`check_shipmd_patch` themselves to catch `(OSError, UnicodeDecodeError)`
around the `.read_text()` call and report the same "cannot verify" outcome as the already-handled
missing-file case.

## Info

### IN-01: `_task_description`'s docstring doesn't disclose the checkpoint-task gap it silently produces

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:331-353`

**Issue:** The docstring documents the deliberate exclusion of `acceptance_criteria` and the
deliberate inclusion of `<behavior>`, but says nothing about what happens when it is called on a
task whose real content lives in fields it doesn't know how to read (checkpoint tasks — see
CR-01). A reader relying on the docstring alone would reasonably assume every task type is
handled.

**Fix:** Add a short note to the docstring (or to `resolve_issue`'s) stating that a
`checkpoint:*`-typed task's real content is not represented in this renderer's output today, and
pointing at the follow-up needed (see CR-01), so a future editor does not mistake the silent empty
string for intentional, documented behavior.

---

_Reviewed: 2026-08-19T00:18:53Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
