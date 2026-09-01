---
phase: 20-additive-identity-migration-and-compatibility
fixed_at: 2026-09-01T11:24:40+02:00
review_path: .planning/phases/20-additive-identity-migration-and-compatibility/20-REVIEW.md
iteration: 12
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 20: Code Review Fix Report

## Iteration 12 Fixed Issues

### CR-01: Blank milestone titles authorized replacement creation

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `9fc842c`
**Applied fix:** The existing title-authority guard now rejects empty and
whitespace-only strings. Both public cases fail closed with zero mutation and
unchanged target bytes.

## Iteration 11 Fixed Issues

### CR-01: Incomplete milestone metadata authorized replacement creation

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `57067c9`
**Applied fix:** An exact-ID milestone row must now carry a string title before
title mismatch can be interpreted. Missing and non-string titles fail closed
without task, epic, dependency, close, or plan-write mutation.

## Iteration 10 Fixed Issues

### CR-01: Milestone candidate confirmation trusted title without exact identity

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `7d00fc1`
**Applied fix:** One exact one-row JSON parser now returns the identified row
for task, phase-epic, and milestone consumers. Milestone title matching occurs
only after exact candidate-ID validation. A mismatched ID with the expected
title cannot authorize task creation, dependency mutation, or plan writes; the
milestone fixtures now exercise the live list envelope.

## Iteration 9 Fixed Issues

### CR-01: Milestone-wide epic discovery bypassed authority preflight

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `affdef8`
**Applied fix:** When an unbound plan resolves a milestone epic, the existing
plan-authority validator now scans every phase plan before Beads availability.
Milestone candidate discovery also uses the same cardinality-aware epic parser.
Malformed and conflicting foreign declarations make zero `run_bd` calls and
leave both foreign and target plan bytes unchanged.

## Iteration 8 Fixed Issues

### CR-01: Epic frontmatter authority was syntax- and cardinality-blind

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `939d279`
**Applied fix:** One declaration parser now rejects malformed, empty, and
duplicate `beads_epic` authority before any Beads probe or plan write. Public
controls prove spaced values plus same-value and conflicting duplicates make
zero `run_bd` calls and preserve plan bytes.

## Iteration 7 Fixed Issues

### CR-01: Missing task closures were invisible to authority gates

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `28c486c`
**Applied fix:** `parse_plan` now requires raw exact `<task` openings to map
one-to-one to structurally closed task blocks. Creation, wave closure, and
reconciliation handle the typed parse failure before any Beads call.

### CR-02: Cross-plan consumers bypassed task authority validation

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `8f5b081`
**Applied fix:** One task-authority validator now preflights every sibling and
prerequisite plan before Beads availability, orphan detection, or dependency
mutation. Unsafe and duplicate authority leave all plan bytes unchanged.

### CR-03: Epic identity was unchecked

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `8f5b081`
**Applied fix:** Stored, shared, milestone, and created epic IDs require the
safe-ID contract; successful epic shows require exact one-row JSON authority.
Unsafe stored IDs fail before Beads, and mismatched or unsafe returned identity
cannot trigger downstream mutation or plan writes.

## Iteration 6 Fixes

### CR-01: Closure paths bypassed malformed and duplicate authority validation

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commits:** `58ce989`, `68406f8`
**Applied fix:** `close_wave`, reconciliation, and completed-task resolution now
validate malformed, unsafe, and duplicate legacy authority before even probing
Beads availability. Public controls prove unclosed quotes and same/conflicting
duplicates cause zero `run_bd` calls across both mutation paths.

### CR-02: README and hook header retained obsolete dispatch ownership

**Files modified:**

- `README.md`
- `plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `d091403`
**Applied fix:** The overview, caveat, and hook header now agree with source and
PRIME. Negative contract assertions prohibit the obsolete one-native-point,
five-of-six, and Steps-1-through-3 PostToolUse claims.

## Iteration 5 Fixes

### CR-01: Unclosed task openings bypassed preflight

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `d3941fb`
**Applied fix:** Task block discovery now enumerates every exact `<task`
opening through its closing task while the existing quote-aware scanner remains
the sole validity seam. Unclosed single- and double-quoted openings fail before
any Beads call or plan write.

### CR-02: Duplicate legacy authority was silently collapsed

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `044eaf0`
**Applied fix:** Parsing retains legacy `<beads-id>` cardinality and preflight
rejects both same-value and conflicting duplicates before any mutation.

### CR-03: PRIME documented obsolete dispatch ownership

**Files modified:**

- `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `a72df9a`
**Applied fix:** PRIME now assigns native `plan:post` and `verify:post` to
current gsd-core, the compatibility hook to `plan:pre` and both execute-wave
points, and the installed patch to `ship:pre`. A semantic contract test keeps
PRIME aligned with README.

## Iteration 4 Fixes

### CR-01: Malformed task openings crossed task boundaries

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `0ab65e2`
**Applied fix:** The existing scanner now requires whitespace before every
attribute and rejects self-closing task openings. Public no-call/no-write
controls prove adjacent attributes and self-closing cross-capture fail before
Beads mutation or plan writes.

### CR-02: Quoted delimiters broke active native-parser parity

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `f83b94d`
**Applied fix:** Eligible task openings containing a quoted greater-than before
the native parser's delimiter now fail closed. Both attribute orders are tested
against the unchanged launcher-derived parser; only native-readable identity is
projected.

### CR-03: Operator documentation and its contract test were stale

**Files modified:**

- `README.md`
- `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commits:** `de2a6ea`, `37d07bf`
**Applied fix:** Operator docs now distinguish legacy `<beads-id>` insertion
from native `tracker-id` projection and describe Phase 20 as current. The
release-doc contract normalizes Markdown whitespace before asserting the exact
normative prose, so hard wrapping cannot create false failures.

## Iteration 3 Fixes

### CR-01: Identity scanners accepted text outside exact task attributes

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `814c766`
**Applied fix:** One quote-aware opening-tag scanner now recognizes only the
exact `<task>` element and exact, case-sensitive attributes. Public controls
cover quoted attribute-shaped text, `<task-extra>`, quoted `>` characters,
duplicate attributes, and unquoted attributes.

### CR-02: The destructive stripper discovered task type in body text

**Files modified:**

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`

**Commit:** `0792634`
**Applied fix:** `strip_task_bodies` reuses the opening-tag scan and never
searches body text for attributes. Direct and public `allow_strip=True`
controls prove a literal `type="auto"` in an excluded task body survives.

### CR-03: The mandatory active-parser integration gate was red

**External runtime artifacts restored:**

- `/home/dd/projects/gsd-core/gsd-core/bin/lib/exit-code-registry.cjs`
- `/home/dd/projects/gsd-core/gsd-core/bin/lib/vendor/js-yaml.cjs`

**Beads:** `gsd-beads-5jk.12`
**Applied fix:** A full-tree inventory identified the two missing untracked
generated dependencies. They were restored from the installed Codex gsd-core
copy only after proving their direct consumers (`cli-exit.cjs` and
`frontmatter.cjs`) byte-identical. The unchanged launcher-derived parser
integration test now passes. No existing external dirty file was overwritten.

## Earlier Iteration Fixes

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
Ran 1 focused milestone metadata matrix
OK
Ran 305 tests in 8.828s
OK
```

`py_compile` and `git diff --check` also passed. The test run used only the
mandated session scratch directory.

---

_Fixed: 2026-09-01T11:24:40+02:00_
_Iteration: 12_
