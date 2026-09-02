---
phase: 22-capability-projection-reconciliation
plan: 01
subsystem: beads-lifecycle
tags: [gsd-core, capability-projection, native-install, generation-ledger, process-lock]

requires:
  - phase: 21-installed-cutover-and-patch-2-retirement
    provides: Native installed capability authority with the retired execute-plan surface absent
provides:
  - One-runtime native capability reconciliation through the active gsd-core surface
  - Generation-bound selected-projection certification in a shared v2 ledger
  - Crash-stale hook serialization with final external-writer drift rejection
  - Real current-runtime two-capability transformation and preservation proof
affects: [capability-install, session-start, selected-skills, gsd-core-runtime]

actuals:
  tokens: 21915
  tasks: 1
  commits: 14

tech-stack:
  added: []
  patterns: [native-projection-authority, generation-bound-receipt, atomic-process-identity-lock]

key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/hooks/capability-auto-install.sh
    - plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
    - tests/test-capability-auto-install.sh
    - README.md

key-decisions:
  - "Keep gsd-core as the sole installed and selected-skill writer; the hook owns only guards, serialization, observation, and receipts."
  - "Certify the 1.10.0 floor from its immutable official tag/package metadata while proving live behavior against the active/current 1.12.0 runtime."
  - "Bind each runtime receipt to both the installed generation and observed selected-surface fingerprint under one atomic PID:start-identity symlink lock."

patterns-established:
  - "Native writer boundary: resolve one runtime-owned public CLI and never copy or prune selected skills in plugin code."
  - "Bounded recovery: one stale-token quarantine and one reacquire attempt, with unresolved identities treated as busy."
  - "Receipt publication: recheck installed and selected hashes immediately before atomic ledger publication."

requirements-completed: ["GitHub issue #9"]

coverage:
  - id: D1
    description: "Stale selected Beads projections reconcile through native install/set while same-name user content and unrelated state remain unchanged."
    requirement: "GitHub issue #9"
    verification:
      - kind: integration
        ref: "tests/test-capability-auto-install.sh#cases 1-11 and 24"
        status: pass
    human_judgment: false
  - id: D2
    description: "The shared v2 receipt is generation/fingerprint-bound and serialized by crash-recoverable process identity ownership."
    requirement: "GitHub issue #9"
    verification:
      - kind: integration
        ref: "tests/test-capability-auto-install.sh#cases 7 and 12-23"
        status: pass
    human_judgment: false
  - id: D3
    description: "The immutable 1.10.0 floor and active/current 1.12.0 two-capability transformed surface pass without skips or residual scratch."
    requirement: "GitHub issue #9"
    verification:
      - kind: e2e
        ref: "tests/test-capability-auto-install.sh#case 24"
        status: pass
    human_judgment: false

duration: 115 min
completed: 2026-09-03
status: complete
---

# Phase 22 Plan 01: Capability Projection Reconciliation Summary

The SessionStart hook now delegates one-runtime repair to gsd-core's native
install/set surface, certifies the observed generation and selected projection
under a crash-recoverable shared lock, and proves the contract against the real
current 1.12.0 runtime with a genuine sibling capability.

## Performance

- **Duration:** 115 min
- **Started:** 2026-09-02T20:13:11Z
- **Completed:** 2026-09-02T22:08:00Z
- **Tasks:** 1
- **Files modified:** 4

## Accomplishments

- Replaced the unlocked legacy receipt with canonical sorted `projection-v2`
  rows bound to installed-generation and selected-surface SHA-256 fingerprints.
- Serialized all hook-participant work with an atomically published
  `PID:process-start-identity` symlink token, conservative live contention, and
  one bounded crash-stale recovery attempt.
- Kept gsd-core as the sole projection writer, guarded user-owned same-name
  skills, checked exact owner markers and installed CLI commands, and rejected
  `execute-plan` before certification.
- Proved immutable v1.10.0 floor provenance and a no-skip active/current 1.12.0
  native install/set run with independent transformed output, sibling/user/
  unrelated/unselected preservation, and a byte-stable silent repeat.

## Task Commits

The single task was committed in strict implementation slices:

1. **Runtime projection contract RED** - `f72c625` (test)
2. **Native runtime surface GREEN** - `2f9a6be` (feat)
3. **Unsafe selected projections RED** - `d13cdfa` (test)
4. **Observed selected surface GREEN** - `7477587` (feat)
5. **Generation-bound ledger RED** - `5255002` (test)
6. **Generation-bound certification GREEN** - `79e54a8` (feat)
7. **Process-identity ownership RED** - `11ecca3` (test)
8. **Serialized projection transaction GREEN** - `d18ab6b` (feat)
9. **Crash-stale recovery RED** - `90cac24` (test)
10. **Bounded stale recovery GREEN** - `0f91f16` (feat)
11. **External-writer drift RED** - `b41cca7` (test)
12. **Final drift rejection GREEN** - `2d66fc7` (feat)
13. **Immutable-floor and real-current proof** - `887e671` (test)

## Verification

- Exact compound gate: PASS, then repeated unchanged for the tracer feedback
  gate: PASS.
- Focused public-hook suite: 24/24 cases, `ALL PASS`, twice.
- Full capability suite: 292/292 tests, `OK`, twice.
- Real CLI evidence: official `v1.10.0` peeled to
  `68a04ccf8ef74803bdb651e12c3b85b218bbccdf`; tagged package was
  `@opengsd/gsd-core@1.10.0`; active/current identity was
  `@opengsd/gsd-core@1.12.0`.
- Real selected CLI accepted ten declared prefixes and rejected
  `execute-plan`; transformed Beads and genuine sibling trees matched the
  independent native oracle after normalizing only its fixture-local config
  prefix.
- `bash -n`, manifest JSON parsing, scoped `git diff --check`, forbidden
  projector scan, stub/skip scan, and `/dev/shm` cleanup all passed.

## Files Created/Modified

- `plugins/beads-lifecycle/hooks/capability-auto-install.sh` - Native
  one-runtime reconciliation, ownership/command verification, v2 ledger,
  process-identity lock, bounded stale recovery, and final drift recheck.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` - Exact
  `>=1.10.0` gsd-core compatibility floor.
- `tests/test-capability-auto-install.sh` - Twenty-four public cases including
  deterministic contention/recovery and the real current two-capability proof.
- `README.md` - Operator contract for runtime selection, native authority,
  receipts, locking, recovery, drift detection, and preservation.

## Decisions Made

- Runtime selection is explicit `codex`/`claude` first, then unambiguous plugin
  cache ownership; no path or sibling-runtime fallback is permitted.
- Selected output is observed after native `capability set`; production never
  derives transformed expected bytes from raw installed skill bytes.
- Missing contender identity is live/busy, not stale. Recovery is allowed only
  for a malformed token, positively dead PID, or resolved identity mismatch.

## Deviations from Plan

### User-approved evidence correction

- **Issue:** Released gsd-core v1.10.0 predates the `runtime-identity` verb, so
  requiring that CLI to self-report 1.10.0 was impossible.
- **Approved correction:** Prove the compatibility floor from official tag
  `v1.10.0`, immutable commit `68a04ccf...`, and tagged package version
  `1.10.0`; independently prove current executable behavior through active
  gsd-core 1.12.0.
- **What does it bias?** NONE. Minimum-version provenance and current runtime
  behavior are separated without weakening any projection or preservation
  assertion.

### Slice 7 fail-fast result

- The first real-tree comparison exposed a fixture-only confound: gsd-core
  embeds the isolated runtime config root in the transformed status skill.
  Normalizing only that independently produced fixture-local prefix made the
  arms differ solely in projection generation.
- The corrected Slice 7 assertion passed immediately because Slices 1-6 had
  already implemented the behavior. No fictitious RED or unnecessary
  production change was created.

**Total deviations:** 1 user-approved evidence correction and 1 transparent
per-slice TDD exception; neither changed production scope or mechanism.

## TDD Gate Compliance

- Plan-level RED and GREEN gates are present and ordered in six implementation
  pairs (`f72c625` through `2d66fc7`).
- Slice 7 is a test-only real-runtime proof at `887e671`; its corrected test
  passed against the completed earlier slices, so it has no separate GREEN
  production commit.

## Issues Encountered

- The complete Python suite refreshes only the `updatedAt` field in the tracked
  root `.gsd-capabilities.json`. A Python-only reproduction confirmed this is a
  pre-existing out-of-scope verification side effect; the file was restored
  exactly after both successful gates.
- A copied compiled CLI without its source/runtime support tree cannot execute
  native capability materialization. The final fixture uses a current source
  archive with the exact active 1.12.0 compiled `bin` overlay inside
  `/dev/shm`, then removes the bounded tree.

## Known Stubs

None.

## User Setup Required

None.

## Next Phase Readiness

Phase 22's task bead `gsd-beads-210` is closed with the exact test evidence.
No implementation blocker, skipped verification, push, or Dolt sync remains.

## Self-Check: PASSED

- All four implementation files and this summary exist.
- All thirteen task commits resolve in Git in the recorded order.
- No tracked file deletion or residual Phase 22 scratch path was found.

---

*Phase: 22-capability-projection-reconciliation*
*Completed: 2026-09-03*
