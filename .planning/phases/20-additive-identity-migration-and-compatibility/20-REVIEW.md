---
phase: 20-additive-identity-migration-and-compatibility
reviewed: 2026-08-31T20:21:39Z
depth: deep
files_reviewed: 4
files_reviewed_list:
  - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md
  - plugins/beads-lifecycle/.agents/skills/beads/PRIME.md
findings:
  critical: 3
  warning: 0
  info: 0
  total: 3
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-08-31T20:21:39Z
**Depth:** deep
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Phase 20 must not ship. The seven previously reproduced defects are repaired at
their direct sites: task authority validation, CRLF preservation, the covered
tracker/type name cases, all-bound-authority-before-create ordering, active
writer spies, and documentation are present. A fresh full-context pass
reproduced two uncovered lexical failures and one live integration failure:
quoted attribute values and `<task-extra>` cross the identity boundary,
the destructive stripper discovers `type=` in task bodies, and the mandatory
active-parser test cannot load its current gsd-core dependency graph.

## Full-context evidence

- Traced `lifecycle_dispatch("plan:post")` and direct `main create-issues` into
  `create_issues -> parse_plan -> resolve_issue/resolve_epic -> rewrite_plan ->
  Path.open("w")`, all ten production `parse_plan` callers, stripping, orphan
  reconciliation, dependency application, and fail-open handling.
- Inspected all 15 `TestIdentityBinding` controls, fixtures, capability
  metadata, lifecycle hook, shipped sync skill, PRIME, CI, and the active
  `/home/dd/projects/gsd-core/gsd-core/bin/lib/plan-document.cjs` consumer.
- Public runs returned 0 and produced
  `<task note=' type="auto" tracker-id="beads:e1.1"'>`, treated
  `note=' tracker-id="beads:e1.1"'` as canonical without an exact attribute,
  and rewrote `<task-extra type="auto">` as
  `<task-extra type="auto" tracker-id="beads:e1.1">`.
- A stripping trace converted a missing-type task whose action merely contained
  `type="auto"` into a pointer and deleted its action.
- `py_compile` and `git diff --check` passed. The focused class ran 15 tests
  with one failure; the full suite ran 288 tests with the same failure. All
  review execution used the mandated session scratch, and the review-created
  pycache was removed.

Ponytail lens: keep the single parser/resolver/writer seam. Do not add XML
serialization, a second migrator, registry, or dependency. The minimum safe
change is one local quote-aware opening-tag scanner reused by `parse_plan` and
`strip_task_bodies`.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Identity scanners accept text that is not an exact task attribute

**Classification:** BLOCKER
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:26,55-63,319-362`; `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1796-1854,2200-2254`; `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md:68-75`; `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md:14-18,30`
**Issue:** The exact-name fixes delimit names with whitespace but do not track
quoting context, while the task element is still delimited with `\b`:

```python
TASK_RE = re.compile(r"<task\b[^>]*>.*?</task>", re.DOTALL)
TASK_TYPE_RE = re.compile(r'(?<=\s)type="([^"]*)"')
TRACKER_ID_RE = re.compile(
    r'''(?<=\s)tracker-id\s*=\s*(?:"([^"]*)"|'([^']*)')'''
)
```

Whitespace inside another quoted value satisfies the lookbehind. Sync inserted
native identity inside `note` for `<task note=' type="auto"'>`, accepted
`note=' tracker-id="beads:e1.1"'` as canonical, and mutated `<task-extra>`.
The active consumer uses `/<task(?=[\s>])[^>]*>/`, so the last case is also
source/consumer divergence. Existing tests cover prefixed/case names but not
quoted-value or element-boundary controls; the shipped exact-task docs are
therefore false.

**Fix:** Use one minimum opening-tag scanner that accepts only `<task` followed
by whitespace or `>`, walks quoted values without recognizing their contents
as attributes, returns exact case-sensitive `type`/`tracker-id` spans, and
rejects malformed/duplicate exact attributes before any Beads call. Keep raw
splicing. Add public tests for quoted `type`, quoted `tracker-id`,
`<task-extra>`, and `>` inside a quoted value, including active-parser parity.

**Confidence:** 100/100.

### CR-02: The destructive stripper discovers task type in body text

**Classification:** BLOCKER
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1509-1548`; `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:975-980,2200-2254`; `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md:68-75`
**Issue:** `strip_task_bodies` applies the attribute regex to the whole block:

```python
block = m.group(0)
type_m = TASK_TYPE_RE.search(block)
task_type = type_m.group(1).strip() if type_m else None
```

A missing-type task containing literal `type="auto"` in `<action>` was
classified as auto, lost its action, and gained the synced-content pointer.
This is data loss on the explicit authoritative CLI. Current missing-type tests
contain no attribute-shaped body text, and the coexistence test uses
`allow_strip=False`.

**Fix:** Reuse CR-01's opening-tag result; never search the task body for
attributes. Add direct stripper and `allow_strip=True` public controls where
missing/unknown task bodies contain literal `type="auto"`; require body and
unrelated bytes to survive.

**Confidence:** 100/100.

### CR-03: The mandatory active-parser integration gate is red

**Classification:** BLOCKER
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1856-1913`; `/home/dd/projects/gsd-core/gsd-core/bin/lib/cli-exit.cjs:16-22`
**Issue:** Focused and full suites fail
`test_installed_parser_reads_migrated_identity_and_checkpoint_null`. It
correctly resolves live `gsd_run` to
`/home/dd/projects/gsd-core/gsd-core/bin/gsd_run`, but loading its sibling
parser reaches:

```javascript
const exitCodeRegistryModule = require("./exit-code-registry.cjs");
```

`/home/dd/projects/gsd-core/gsd-core/bin/lib/exit-code-registry.cjs` is absent,
so Node exits 1 with `MODULE_NOT_FOUND`. Phase 20 has no current proof that the
active consumer can load. The plan makes require failure a hard failure;
historical green output cannot override current state.

**Fix:** Restore or regenerate the active gsd-core build/install so every
runtime dependency of `plan-document.cjs` exists at the launcher-derived path,
then rerun the unchanged parser test, focused class, and full suite. Do not
skip, hard-code another home, or select another parser copy.

**Confidence:** 100/100.

---

_Reviewed: 2026-08-31T20:21:39Z_
_Reviewer: gsd-code-reviewer_
_Depth: deep_
