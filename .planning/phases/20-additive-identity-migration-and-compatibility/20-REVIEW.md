---
phase: 20-additive-identity-migration-and-compatibility
reviewed: 2026-08-31T17:28:39Z
depth: deep
files_reviewed: 2
files_reviewed_list:
  - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
findings:
  critical: 3
  warning: 0
  info: 0
  total: 3
status: issues_found
---

# Phase 20: Code Review Report

**Reviewed:** 2026-08-31T17:28:39Z  
**Depth:** deep  
**Files Reviewed:** 2  
**Status:** issues_found

## Summary

Phase 20 must not ship. The additive splice is small and correctly orders offsets, but the migration path does not enforce the Phase 19 resolver's identity-validation boundary, text-mode I/O changes unrelated line-ending bytes, and the attribute scanner accepts lexical forms that the locked exact-attribute contract rejects. The supplied negative and byte-preservation tests cannot detect the first two failures.

## Full-context evidence

The review inspected the complete changed modules and traced these production paths:

- `parse_plan -> create_issues -> resolve_issue -> rewrite_plan -> Path.write_text`, including preflight, descending-offset insertion, task-body stripping, dependency updates, orphan reconciliation, and both the direct `create-issues` CLI and `plan:post` lifecycle dispatch.
- Every production `parse_plan` consumer plus its direct test consumer. Existing callers consume named task keys; the additive keys do not break an exact-dict contract.
- The Phase 19 native consumer path: `capability.json` `taskContentResolver` -> installed gsd-core `parsePlanDocument` -> tracker routing -> `sync.py resolve-task-content` -> `resolve_task_content`.
- Related identity, idempotence, exclusion, parser-compatibility, failure, lifecycle, dependency, and orphan tests; `plan-synced.md` and `plan-single.md` fixtures; capability/config metadata; Beads sync/status documentation; and `.github/workflows/ci.yml` conventions.

Ponytail lens: the chosen reuse of the existing parser/resolver/writer seam, Python standard library, and one descending splice list is the minimum mechanism. There is no new dependency, abstraction, or speculative pipeline to remove. The blockers below are trust-boundary and byte-contract defects; simplifying away their validation would make the implementation less correct, not more minimal.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Migration projects unvalidated and unverified Beads identities

**Classification:** BLOCKER  
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1366-1370,1389-1392,1847-1857`; `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:81-85,1940-1953`  
**Issue:** The migration trusts any existing identity whenever `bd show` exits zero and trusts task-create stdout verbatim:

```python
if task["beads_id"]:
    check = run_bd(["bd", "show", task["beads_id"], "--json"])
    if check.returncode != 0:
        return task["beads_id"], False, True
    return task["beads_id"], False, False
```

```python
return result.stdout.strip(), True, False
```

That is weaker than the actual Phase 19 consumer, which first requires `SAFE_BD_ID_RE.fullmatch(issue_id)` and then validates JSON shape and `row.get("id") != issue_id` at lines 575-600. `create_issues` nevertheless queues every non-divergent value for `tracker-id` at lines 1852-1857. An existing `<beads-id>bad id</beads-id>` was therefore projected as `tracker-id="beads:bad id"` when the mock returned zero, while `resolve_task_content("bad id")` rejected it as `invalid id`. A real `bd show --help --json` also exits zero, so `<beads-id>--help</beads-id>` is interpreted as a CLI option and is treated as live authority by this path.

The test double reinforces the gap: successful `bd show` returns only `"{}\n"` at lines 81-82, a response the Phase 19 resolver rejects. The purported malformed arm changes two factors at once: lines 1940-1953 change the ID to `bad id` *and* force `bd show` to return nonzero. It therefore proves stale lookup behavior, not malformed-ID rejection when the command exits zero.

**Fix:** Before any `bd show` call or native update, require the same `SAFE_BD_ID_RE.fullmatch` used by `resolve_task_content`. Validate successful `bd show --json` output as one record whose `id` exactly equals the requested ID. Apply the same grammar check to `bd create --silent` stdout before inserting either identity. Fail closed with no plan write on any invalid shape, mismatch, or unsafe value. Split the stale and malformed tests: keep a valid exact successful response constant in the malformed arm, assert an unsafe ID never reaches `run_bd`, and add invalid-JSON, mismatched-ID, and unsafe-create-output cases.

**Confidence:** 100/100.

### CR-02: The migration rewrites unrelated CRLF bytes

**Classification:** BLOCKER  
**Files:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:310,1872-1895`; `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:134-149,1685-1710`  
**Issue:** The code reads and writes the whole plan in text mode:

```python
text = Path(path).read_text(encoding="utf-8")
```

```python
plan_path.write_text(new_text, encoding="utf-8")
```

Python's text read performs universal-newline conversion. Once Phase 20 adds a missing native identity and reaches the write, every CRLF in the document is serialized as LF, despite `rewrite_plan` itself making only local string splices. An isolated CRLF plan containing nine CRLF sequences reproduced `before_crlf=9`, `after_crlf=0`, and `unrelated_bytes_preserved=False` after a successful existing-bound migration. This violates the locked local-splice/raw-byte contract and can create a whole-file diff unrelated to identity migration.

The test helper writes fixtures through `plan_copy.write_text(plan_text, encoding="utf-8")` at line 149, while the migration assertion compares `read_text` results at lines 1685-1710. Both normalize line endings, so the test cannot observe this data change. The byte assertion at lines 1735-1745 covers only the already-canonical no-write path.

**Fix:** Preserve newline bytes on the mutation path, minimally by opening with `newline=""` for both read and write (or by using a byte-preserving decode/splice/encode path) while retaining the existing descending offsets. Add a CRLF existing-bound fixture or construct CRLF bytes directly, invoke `create_issues`, and compare raw bytes against the original plus only the expected attribute insertion.

**Confidence:** 100/100.

### CR-03: Preflight does not recognize only exact `tracker-id` attributes or exact values

**Classification:** BLOCKER  
**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:57-59,322-325,1786-1813`  
**Issue:** The scanner is deliberately broader than the locked lexical contract:

```python
TRACKER_ID_RE = re.compile(
    r'''\btracker-id\s*=\s*(?:"([^"]*)"|'([^']*)')''', re.IGNORECASE
)
```

and then normalizes the captured value:

```python
next(group for group in tracker_m.groups() if group is not None).strip()
```

`\btracker-id` matches the suffix of `data-tracker-id`; an isolated parse confirmed that `<task type="auto" data-tracker-id="beads:issue-1">` produces `['beads:issue-1']`. `re.IGNORECASE` also accepts a differently cased name, and `.strip()` makes `tracker-id=" beads:issue-1 "` compare equal to the expected canonical value at lines 1806-1807. In each single-attribute case, preflight treats a non-exact representation as canonical and suppresses insertion of the required exact `tracker-id="beads:<id>"`. With both a prefixed attribute and a real attribute, it can instead report a false duplicate and halt.

**Fix:** Match an exact, case-sensitive `tracker-id` attribute token delimited by opening-tag whitespace, retain the raw value for exact comparison, and do not strip it. Add public-boundary tests for `data-tracker-id`, case variants, and leading/trailing value whitespace; each must fail preflight without a write or Beads mutation rather than count as canonical.

**Confidence:** 100/100.

---

_Reviewed: 2026-08-31T17:28:39Z_  
_Reviewer: gsd-code-reviewer_  
_Depth: deep_
