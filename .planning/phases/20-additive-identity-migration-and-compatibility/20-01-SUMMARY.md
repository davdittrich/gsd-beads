---
phase: 20-additive-identity-migration-and-compatibility
plan: 01
subsystem: beads-lifecycle
tags: [beads, task-identity, tracker-id, compatibility, fail-closed]

requires:
  - phase: 19-native-resolver-contract-and-failure-boundary
    provides: Native task-content resolver contract and fail-closed execution boundary
provides:
  - Canonical native tracker identity projected from authoritative Beads identity
  - Byte-preserving identity migration for existing and newly created eligible tasks
  - Fail-closed conflict checks and exact checkpoint/unknown-type preservation
affects: [phase-21-installed-cutover, task-content-resolver, beads-lifecycle]

actuals:
  tokens: 6534
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns: [additive-identity-projection, descending-offset-lexical-splice]

key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py

key-decisions:
  - "Keep <beads-id> authoritative and derive tracker-id only as beads:<issue-id>."
  - "Reuse the existing parse_plan -> create_issues -> rewrite_plan seam and its sole writer."
  - "Retain fail-closed preflight for ambiguous native identity and exact-type exclusion for human and unknown tasks."

patterns-established:
  - "Named-field parser extension: all parse_plan callers consume named fields, so identity metadata extends the task record without positional coupling."
  - "Single lexical writer: merge legacy and native insertions by descending source offset and write only when an update exists."

requirements-completed: [ID-01, ID-02]

coverage:
  - id: D1
    description: "Existing and newly created exact auto/tracer tasks receive one canonical native identity while retaining authoritative Beads identity, and repeat synchronization is byte-identical."
    requirement: ID-01
    verification:
      - kind: unit
        ref: "TMPDIR=/run/user/1000/codex-scratch-01a0583c-f3f3-76e2-98c3-a0d64094c310 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sync.TestIdentityBinding -v"
        status: pass
      - kind: integration
        ref: "TMPDIR=/run/user/1000/codex-scratch-01a0583c-f3f3-76e2-98c3-a0d64094c310 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t tests"
        status: pass
    human_judgment: false
  - id: D2
    description: "Conflicting or unsafe authority fails without mutation, while checkpoint, missing-type, partial-type, and unknown-type blocks remain byte-exact."
    requirement: ID-02
    verification:
      - kind: unit
        ref: "TMPDIR=/run/user/1000/codex-scratch-01a0583c-f3f3-76e2-98c3-a0d64094c310 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sync.TestIdentityBinding -v"
        status: pass
      - kind: integration
        ref: "TMPDIR=/run/user/1000/codex-scratch-01a0583c-f3f3-76e2-98c3-a0d64094c310 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t tests"
        status: pass
    human_judgment: false

duration: 32 min
completed: 2026-08-31
status: complete
---

# Phase 20 Plan 01: Additive Identity Migration and Compatibility Summary

Deterministic native task identity projected from live Beads authority through
the existing lexical sync writer, with fail-closed conflicts and byte-exact
compatibility boundaries.

## Performance

- **Duration:** 32 min
- **Started:** 2026-08-31T17:56:14+02:00
- **Completed:** 2026-08-31T18:28:44+02:00
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Existing and newly created exact `auto`/`tracer` tasks receive one canonical
  `tracker-id="beads:<issue-id>"` while retaining their authoritative
  `<beads-id>`; a canonical second sync performs no create, update, or write
  and preserves raw bytes.
- Wrong, duplicate, authority-free, stale, malformed, unavailable, and failing
  authority cases do not produce unsafe projection; checkpoint, missing-type,
  partial-type, and unknown-type blocks remain byte-exact beside migrated
  tasks.

## Task Commits

Each task followed strict RED/GREEN commits:

1. **Task 1 RED: Existing-bound identity projection contract** - `b7b347b` (test)
2. **Task 1 GREEN: Existing-bound identity projection** - `2e01465` (feat)
3. **Task 2 RED: Newly created identity and preservation boundaries** -
   `3fcad44` (test)
4. **Task 2 GREEN: Identity projection on task creation** - `a4f0b08` (feat)

**Plan metadata:** Recorded in this summary's docs commit.

## Files Created/Modified

- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` - Parses
  native identity, performs conflict preflight, and merges eligible native
  insertions into the existing descending-offset writer.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` - Proves
  existing/new projection, second-pass idempotence, fail-closed conflicts,
  active native-parser compatibility, and exact excluded-block preservation.

## Decisions Made

- Caller trace result: `named-fields-only`; every `parse_plan` consumer reads
  named task fields, so the existing task record could be extended without a
  fallback traversal.
- `<beads-id>` remains the sole live authority. Native `tracker-id` is added
  only as the deterministic `beads:<issue-id>` projection after successful
  exact resolution.
- Native and legacy insertions share `rewrite_plan`, descending source
  offsets, and the existing sole write predicate. No serializer, second
  migrator, cache, retry, registry, or gsd-core source edit was introduced.

## Verification

- `TestIdentityBinding`: 10/10 passed under the mandated session scratch.
- Full capability suite: 283/283 passed under the mandated session scratch.
- `git diff --check` passed for the implementation and test files.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- One resume halted with `SPEC_FAILURE` before mutation because the mandated
  scratch root was not writable in that sandbox. Execution resumed without a
  workaround after the root became writable.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- ID-01 and ID-02 are complete through the source synchronizer and active
  native-parser seam.
- Phase 21 can perform installed-runtime cutover and Patch 2 retirement; no
  blocker remains from this plan.

## Self-Check: PASSED

- Both modified source/test files exist.
- Task commits `b7b347b`, `2e01465`, `3fcad44`, and `a4f0b08` exist in order.
- Focused verification passed 10/10 and the authoritative full capability
  suite passed 283/283.
- `STATE.md`, `ROADMAP.md`, validation artifacts, source, tests, tickets, and
  `.gsd-capabilities.json` were not edited during summary creation.

---

*Phase: 20-additive-identity-migration-and-compatibility*
*Completed: 2026-08-31*
