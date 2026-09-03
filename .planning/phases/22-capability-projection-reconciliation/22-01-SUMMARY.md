---
phase: 22-capability-projection-reconciliation
plan: 01
subsystem: beads-lifecycle
tags: [gsd-core, capability-projection, fcntl, atomic-publication, native-install]

requires:
  - phase: 21-installed-cutover-and-patch-2-retirement
    provides: Native installed capability authority with the retired execute-plan surface absent
provides:
  - Runtime-native Beads capability reconciliation serialized by an inherited kernel lock
  - Secure generation/fingerprint receipt publication with ownership-preserving failure behavior
  - Immutable gsd-core 1.10.0 floor evidence and pinned public 1.12.0 current-runtime CI proof
affects: [capability-install, session-start, selected-skills, gsd-core-runtime]

actuals:
  tokens: 27212
  tasks: 1
  commits: 19

tech-stack:
  added: []
  patterns: [native-projection-authority, inherited-fcntl-lock, generation-bound-receipt, secure-atomic-replace]

key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/hooks/capability-auto-install.sh
    - plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
    - tests/test-capability-auto-install.sh
    - README.md
    - .github/workflows/ci.yml

key-decisions:
  - "Keep gsd-core as the sole installed and selected-skill writer; the hook owns guards, serialization, observation, and receipts only."
  - "Hold one nonblocking fcntl lock across same-process hook re-exec and the complete observe/install/set/verify/publish transaction."
  - "Publish through a secure same-directory NamedTemporaryFile and os.replace; preserve legacy state until canonical publication succeeds."
  - "Separate immutable 1.10.0 compatibility-floor provenance from the pinned public 1.12.0 current-runtime behavior gate."

patterns-established:
  - "Native writer boundary: resolve one runtime-owned public CLI and never copy or prune selected skills in plugin code."
  - "Receipt authority: bind each runtime row to installed generation and observed post-native-set selected fingerprint."
  - "Direct-writer boundary: reject drift visible at final observation; repair a later external race from receipt mismatch on the next SessionStart."

requirements-completed:
  - "GitHub issue #9"

coverage:
  - id: D1
    description: "Stale selected Beads projections reconcile through native install/set while same-name user content, siblings, and unrelated state remain unchanged."
    requirement: "GitHub issue #9"
    verification:
      - kind: integration
        ref: "tests/test-capability-auto-install.sh#cases 1-11, 24"
        status: pass
    human_judgment: false
  - id: D2
    description: "The shared generation/fingerprint receipt is serialized by inherited kernel flock and securely published without risking prior canonical or legacy state."
    requirement: "GitHub issue #9"
    verification:
      - kind: integration
        ref: "tests/test-capability-auto-install.sh#cases 7, 12-23b"
        status: pass
    human_judgment: false
  - id: D3
    description: "Immutable 1.10.0 floor evidence and clean-CI public 1.12.0 reconciliation use a genuinely stale selected Generation A."
    requirement: "GitHub issue #9"
    verification:
      - kind: e2e
        ref: "tests/test-capability-auto-install.sh#cases 24a, 24"
        status: pass
    human_judgment: false

duration: 237 min
completed: 2026-09-03
status: complete
---

# Phase 22 Plan 01: Capability Projection Reconciliation Summary

**Runtime-native Beads projection repair with inherited kernel serialization, secure atomic receipts, and distinct gsd-core 1.10.0 floor versus public 1.12.0 current-runtime proof**

## Performance

- **Duration:** 237 min across the historical implementation, review, and remediation
- **Started:** 2026-09-02T20:13:11Z
- **Completed:** 2026-09-03T00:09:49Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments

- Delegated all installed and selected-skill mutation to the active runtime's public gsd-core capability surface while preserving sibling, user-owned, unrelated, and unselected-runtime content.
- Replaced custom PID/process-start stale-lock recovery with one nonblocking kernel `fcntl.flock` inherited across same-process hook re-exec and automatically released on exit, signal, or crash.
- Hardened marker ownership and canonical ledger publication with non-symlink/type/inode checks, secure same-directory temporary creation, flush plus file `fsync`, atomic `os.replace`, and post-success-only legacy cleanup.
- Proved genuinely stale selected content is repaired from Generation A to B through public gsd-core 1.12.0 install/set, independently matched the transformed oracle, and retained exact immutable v1.10.0 compatibility-floor provenance.
- Pinned CI to official gsd-core `v1.12.0`, installed exact public `@opengsd/gsd-core@1.12.0` into runner-temporary `CODEX_HOME`, checked runtime identity, and exported the tagged source fixture before the smoke harness.

## Task Commits

The one cohesive task preserves the full TDD chronology:

1. **Runtime projection contract RED** — `f72c625`
2. **Native runtime surface GREEN** — `2f9a6be`
3. **Unsafe selected projections RED** — `d13cdfa`
4. **Observed selected surface GREEN** — `7477587`
5. **Generation-bound ledger RED** — `5255002`
6. **Generation-bound certification GREEN** — `79e54a8`
7. **Process-identity ownership RED** — `11ecca3`
8. **Serialized projection transaction GREEN** — `d18ab6b`
9. **Crash-stale recovery RED** — `90cac24`
10. **Bounded stale recovery GREEN** — `0f91f16`
11. **External-writer drift RED** — `b41cca7`
12. **Final drift rejection GREEN** — `2d66fc7`
13. **Immutable-floor/current-runtime proof** — `887e671` (verification-only test; no production delta)
14. **R1 insecure-locking RED** — `1122e95`
15. **R1 inherited-kernel-lock GREEN** — `009226c`
16. **R2 unsafe-publication RED** — `70ae2fc`
17. **R2 secure-publication GREEN** — `bdd1227`
18. **R3 unpinned-CI/genuine-generation RED** — `2eb1c2d`
19. **R3 pinned-current-runtime GREEN** — `9271dea`

## Verification Evidence

- Every R1-R3 RED ran the exact whole public harness and failed nonzero at a newly introduced case before its test-only commit:
  - R1: `FAIL: case12: lock path is not a persistent regular file`
  - R2: `FAIL: case18: symlink marker did not produce the fixed ownership diagnostic`
  - R3: `FAIL: case24a: CI does not provision and prove the pinned gsd-core 1.12.0 runtime before smoke`
- Every following GREEN reran that same whole harness and reached `ALL PASS`.
- The final real fixture proved official `v1.10.0` commit `68a04ccf8ef74803bdb651e12c3b85b218bbccdf`, tagged package `@opengsd/gsd-core@1.10.0`, active/current `@opengsd/gsd-core@1.12.0`, genuine stale-A repair, selected-command execution, retired-command rejection, transformed-oracle equality, sibling/user/unrelated/unselected preservation, silent idempotence, no skip, and clean scratch.
- Full capability suite: `Ran 292 tests in 8.528s`, `OK`, no skips.
- Both Bash syntax checks, manifest JSON parsing, scoped five-file `git diff --check`, and `/dev/shm` cleanup passed.
- The suite's known `.gsd-capabilities.json` timestamp side effect was restored exactly; no generated Phase 22 scratch remains.

## Files Created/Modified

- `plugins/beads-lifecycle/hooks/capability-auto-install.sh` — Active-runtime resolution, inherited kernel lock, native reconciliation, ownership checks, final observations, and secure receipt publication.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` — Exact `gsd >=1.10.0` compatibility floor.
- `tests/test-capability-auto-install.sh` — Public hook, internal-call spies, concurrency/crash, secure publication, external-writer, genuine-generation, exact-runtime, preservation, command, idempotence, and CI-order regressions.
- `README.md` — Executable lock, publication, recovery, ownership, and compatibility/current-runtime contract.
- `.github/workflows/ci.yml` — Pinned tagged-source checkout plus public gsd-core 1.12.0 provision-and-identify gate before the smoke suite.

## Decisions Made

- Production observes runtime-selected bytes; it does not attempt to derive transformed expected output or maintain a second projection writer.
- The lock file persists as an owner-controlled regular file. Kernel descriptor lifetime, not PID metadata or stale takeover, controls ownership.
- Canonical publication never uses predictable temporary names or rollback renames. A failed replacement preserves prior canonical and legacy bytes.
- The advisory lock coordinates this hook's participants only. Non-cooperating direct writers are bounded by final observation and next-start receipt invalidation, not falsely claimed as atomically excluded.

## Deviations from Plan

### Approved evidence correction

- Released gsd-core v1.10.0 predates `runtime-identity`. The user-approved correction proves the floor from official tag `v1.10.0`, immutable commit `68a04ccf...`, and tagged package version `1.10.0`, then independently proves current behavior through public gsd-core 1.12.0.
- **What does it bias?** NONE. Floor provenance and current executable behavior remain separate and exact.

### Approved historical Slice 7 correction

- The real subject and independent oracle embed distinct fixture config roots. Only a test-owned oracle copy normalizes its absolute root to the subject root; subject output, production fingerprints, installed/source data, and preservation controls remain untouched.
- Slice 7 stayed verification-only/test-only because the corrected assertion was already green against Slices 1-6; no fabricated RED or production change was created.
- **What does it bias?** NONE. The correction removes only the fixture-local path confound.

The revised R1-R3 remediation plan itself was executed without scope or mechanism deviation.

## TDD Gate Compliance

- Historical Slices 1-6 retain six ordered RED→GREEN production pairs; historical Slice 7 remains truthfully classified as verification-only.
- Remediation adds exactly three ordered whole-public-harness RED→GREEN pairs: R1 `1122e95`→`009226c`, R2 `70ae2fc`→`bdd1227`, and R3 `2eb1c2d`→`9271dea`.
- No regression was skipped, fabricated, or combined with its implementation commit.

## Issues Encountered

- The R1 crash fixture initially terminated only its shell parent rather than the inherited lock-holding child. The GREEN commit corrected the deterministic fixture to own and terminate the process group; production locking mechanism did not change.
- R2 exposed two independent oracle defects during GREEN: native repair legitimately restored the same selected bytes after a post-observation race, so mismatch had to be asserted between the published row and actual state; and one selected path used `gsd-migrate-todos` instead of manifest-declared `gsd-beads-migrate-todos`. Both fixture assertions were corrected before the passing commit; secure publisher behavior was unchanged.
- The final full suite passed, then sandboxed Git denied its first exact-file cleanup attempt. The targeted `.gsd-capabilities.json` restore was rerun with authorized Git index access and confirmed clean; no test was rerun or reclassified.

## Known Stubs

None. Empty shell variables found by the stub scan are deterministic test-state resets, not shipped placeholders.

## User Setup Required

None.

## Next Phase Readiness

Plan 22-01 implementation and automated execution gates are complete. Bead `gsd-beads-210` intentionally remains open for independent code/security verification. This Summary records execution evidence and does not self-certify the Phase 22 review or security verdict.

## Self-Check: PASSED

- All five implementation files and the three updated Phase 22 evidence artifacts exist.
- All nineteen task commits resolve as Git commits in the current history.
- Summary completion metadata, actuals, independent-review boundary, and validation false-state are present and diff-clean.

---

*Phase: 22-capability-projection-reconciliation*
*Completed: 2026-09-03*
