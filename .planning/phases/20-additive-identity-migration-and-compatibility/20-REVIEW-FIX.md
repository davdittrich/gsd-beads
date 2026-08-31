---
phase: 20-additive-identity-migration-and-compatibility
fixed_at: 2026-08-31T22:03:49+02:00
review_path: .planning/phases/20-additive-identity-migration-and-compatibility/20-REVIEW.md
iteration: 2
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 20: Code Review Fix Report

## Fixed Issues

### CR-01: Late authority failure left an earlier created issue unbound

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `722c1f5`  
**Applied fix:** Every bound task is now read-only validated before epic or task
creation. Verified results are reused during mutation. A two-task public-boundary
test proves malformed later authority yields zero creates, zero writes, and
unchanged plan bytes.

### CR-02: Prefixed task type was treated as exact

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `256a623`  
**Applied fix:** Task type matching is whitespace-delimited, case-sensitive, and
restricted to the opening tag. `data-type`, `TYPE`, missing, partial, checkpoint,
and unknown types remain byte-identical.

### CR-03: No-write tests spied an obsolete writer

**File modified:**
`plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`  
**Commit:** `4da6708`  
**Applied fix:** Negative and no-op controls now reuse one `Path.open` spy and
assert zero mode-`w` calls. The positive control proves the same spy observes
exactly one write.

### CR-04: Sync documentation contradicted runtime behavior

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md`
- `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md`

**Commit:** `a10b3be`  
**Applied fix:** Both operator documents now state that `<beads-id>` remains
authoritative, bound IDs are verified before mutation, exact `auto` and `tracer`
tasks receive deterministic native identity, and excluded task types remain
unchanged.

## Skipped Issues

None.

## Verification

```text
TMPDIR=/run/user/1000/codex-scratch-01a0583c-f3f3-76e2-98c3-a0d64094c310 \
PYTHONDONTWRITEBYTECODE=1 \
python3 -m unittest discover -s tests -t tests
Ran 288 tests in 8.614s
OK
```

`py_compile` and `git diff --check` also passed. The test run used only the
mandated session scratch directory.

---

_Fixed: 2026-08-31T22:03:49+02:00_  
_Iteration: 2_
