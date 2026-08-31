---
phase: 20-additive-identity-migration-and-compatibility
reviewed: 2026-08-31T19:42:31Z
depth: deep
files_reviewed: 2
files_reviewed_list:
  - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
findings:
  critical: 4
  warning: 0
  info: 0
  total: 4
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-08-31T19:42:31Z
**Depth:** deep
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Phase 20 must not ship. The three earlier findings were repaired at their direct sites: unsafe IDs and malformed/mismatched `bd show` payloads are rejected, CRLF bytes survive the migration writer, and non-exact `tracker-id` spellings fail preflight. The fresh cross-task and lexical review nevertheless found four blockers: authority validation can still occur after an earlier issue was created, the type scanner treats `data-type="auto"` as an exact executable type, the no-write tests spy on a writer the implementation no longer calls, and the shipped sync skill still documents the pre-Phase-20 behavior.

The requested aggregate `20-PLAN.md` and `20-SUMMARY.md` do not exist in the live phase directory. This review used `20-01-PLAN.md` and `20-01-SUMMARY.md`.

## Full-context evidence

- Traced `parse_plan -> create_issues -> resolve_issue -> rewrite_plan -> Path.open("w")`, all named-field `parse_plan` consumers, preflight, epic/task mutation, divergence, stripping, orphan/dependency handling, the direct CLI, and `lifecycle_dispatch("plan:post")`.
- Traced `capability.json` `taskContentResolver` -> installed gsd-core `parsePlanDocument`/`tagAttribute` -> `resolveTaskContent` -> `sync.py resolve-task-content` through active `/home/dd/projects/gsd-core/gsd-core/bin/gsd_run`.
- Inspected the full identity/idempotence/fail-open/parser tests, fixtures, capability metadata, lifecycle hook/manifest, sync skill, PRIME, patch docs, CI, and fix commits `c1d37a0`, `cf73aa4`, `280bb0b`, `4fe77b0`.
- Outside-repository scratch verification: `py_compile` passed; `TestIdentityBinding` passed 14/14; the full suite passed 287/287 in 9.168s; `git diff --check` passed.
- Public-boundary harness reproduced `data_type={exit:0,migrated:true}` and `partial_mutation={exit:0,task_creates:1,plan_unchanged:true}`.

Ponytail lens: reuse of the existing parser/resolver/writer seam, stdlib, and installed parser is minimal. Fixes should stay in that seam; no serializer, second migrator, cache, registry, dependency, or writer abstraction is justified.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: A later authority failure leaves an earlier created issue unbound

**Classification:** BLOCKER
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1375-1396,1894-1914`; `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:2094-2127`
**Issue:** Authority validation is interleaved with mutation:

```python
for i, task in enumerate(tasks, start=1):
    issue_id, created, divergent = resolve_issue(task, epic_id, ordinal_prefix, i)
    if created:
        task_updates.append((task["name_end"], issue_id))
```

A malformed later `bd show` raises at lines 1382-1396, but the handler discards `task_updates`, returns 0, and never binds the prior create:

```python
except RuntimeError as exc:
    print(NOTICE)
    append_state_blocker(...)
    return 0
```

A two-task public-boundary run created task 1, then received malformed JSON for bound task 2: `task_creates=1`, `plan_unchanged=true`, `exit=0`. The next run can create a duplicate. The one-task test at lines 2094-2127 cannot expose the ordering failure.

**Fix:** Before `resolve_epic` or any create, read-only validate every existing task ID and exact `bd show --json` row. Retain verified results locally and let `resolve_issue` consume them. Add a two-task test with an unbound first task and malformed/mismatched bound second task; require zero creates, zero writes, and unchanged bytes.

**Confidence:** 100/100.

### CR-02: `data-type="auto"` is treated as an exact executable type

**Classification:** BLOCKER
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:52-55,319-362,1825-1826,1899-1904`; `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:2155-2201`
**Issue:** The regex is not attribute-token delimited:

```python
TASK_TYPE_RE = re.compile(r'<task\b[^>]*\btype="([^"]*)"')
```

`\btype` matches the suffix of `data-type`. A one-factor public-boundary run rewrote `<task data-type="auto">` as `<task data-type="auto" tracker-id="beads:tracer-f5x.1">`. This violates the exact allow-list and missing/partial/unknown byte-preservation contract. Existing tests cover missing `type`, `type="aut"`, and `type="manual"`, but not prefixed or case-variant names.

**Fix:** Match a whitespace-delimited, case-sensitive type on `opening_tag`, e.g. `re.compile(r'(?<=\s)type="([^"]*)"')`, and derive the insertion offset from that exact match. Add `data-type="auto"`, `TYPE="auto"`, and missing-exact-type public controls; each must stay byte-identical with no native identity.

**Confidence:** 100/100.

### CR-03: No-write tests spy on an API production no longer calls

**Classification:** BLOCKER
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1942-1943`; `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1763-1775,1827-1845,1957-1978,2000-2069`
**Issue:** Production writes via:

```python
with plan_path.open("w", encoding="utf-8", newline="") as plan_file:
    plan_file.write(new_text)
```

Six canonical/conflict/idempotence/stale/unavailable/failing controls still patch `Path.write_text` and assert it was not called. Those assertions cannot observe a rewrite. Byte equality detects changed output, not an identical truncate-and-rewrite, so the explicit no-write contract is unproved despite 287/287 green. This is a non-waivable TDD audit failure.

**Fix:** Reuse the positive test's existing `Path.open` spy with the real method as `side_effect`; filter mode `"w"` calls and assert none in each negative/no-op arm. Retain a positive control proving the same spy observes exactly one write.

**Confidence:** 100/100.

### CR-04: Shipped sync documentation contradicts Phase 20 behavior

**Classification:** BLOCKER
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md:68-72`; `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md:24-28`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1375-1397,1894-1904`
**Issue:** The skill says the synchronizer skips tasks already carrying `<beads-id>` and writes only `beads_epic` plus `<beads-id>`:

```markdown
resolves or creates one beads issue per task (skipping any task that
already carries a `<beads-id>`), and rewrites the plan file in place with the resolved
`beads_epic` frontmatter key and per-task `<beads-id>` elements.
```

Source now validates already-bound tasks and adds `tracker-id="beads:<id>"` for exact eligible tasks. `PRIME.md` also omits the new `plan:post` projection. These are executable operator/agent instructions; source/document divergence is non-waivable.

**Fix:** Update both documents in the same fix commit: `<beads-id>` remains authoritative; bound tasks are verified, not skipped; exact auto/tracer tasks gain deterministic `tracker-id`; checkpoints/unknown types remain unchanged. Verify the wording against source.

**Confidence:** 100/100.

---

_Reviewed: 2026-08-31T19:42:31Z_
_Reviewer: gsd-code-reviewer_
_Depth: deep_
