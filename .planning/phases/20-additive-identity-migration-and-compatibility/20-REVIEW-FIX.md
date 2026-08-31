---
phase: 20-additive-identity-migration-and-compatibility
fixed_at: 2026-08-31T21:26:00+02:00
review_path: .planning/phases/20-additive-identity-migration-and-compatibility/20-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 20: Code Review Fix Report

## Fixed Issues

### CR-01: Migration projected unvalidated and unverified Beads identities

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commits:** `c1d37a0`, `cf73aa4`  
**Applied fix:** Reused the Phase 19 safe-ID grammar and exact
`bd show --json` envelope contract before native projection. Unsafe stored IDs
never reach `bd`; mismatched or malformed authority and unsafe create output
leave plan bytes unchanged. Legacy live-authority mocks now return the exact
requested issue ID.

### CR-02: Migration rewrote unrelated CRLF bytes

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `280bb0b`  
**Applied fix:** Read and write plans with newline translation disabled, made
frontmatter parsing accept CRLF, and preserved the document's newline sequence
when inserting frontmatter. A raw-byte regression proves that only the two
expected identity attributes change, with one audited write.

### CR-03: Preflight accepted non-exact tracker identity syntax

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `4fe77b0`  
**Applied fix:** Exact `tracker-id` recognition is now case-sensitive and
whitespace-delimited, retains the raw value, and separately detects tracker-like
attributes. Prefixed names, case variants, padded values, duplicates, conflicts,
and authority-free markers fail before Beads mutation or plan write.

## Skipped Issues

None.

## Verification

```text
TMPDIR=/run/user/1000/codex-scratch-01a0583c-f3f3-76e2-98c3-a0d64094c310 \
PYTHONDONTWRITEBYTECODE=1 \
python3 -m unittest discover -s tests -t tests
Ran 287 tests in 8.867s
OK
```

The compliant run used only the mandated session scratch directory.

---

_Fixed: 2026-08-31T21:26:00+02:00_  
_Iteration: 1_
