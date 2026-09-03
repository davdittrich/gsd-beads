---
phase: "22"
slug: "capability-projection-reconciliation"
# status lifecycle: draft (seeded by plan-phase) -> validated (set by validate-phase)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-02"
revised: "2026-09-03"
---

# Phase 22 — Validation Strategy

> Remediation validation contract for Bead `gsd-beads-210` and plan task `22-01-01`.

## Test Infrastructure

| Property | Value |
|---|---|
| **Framework** | Existing Bash public-hook harness plus Python 3 stdlib `unittest`; one isolated official gsd-core CLI fixture remains in the Bash harness |
| **Quick command** | `TMPDIR=/dev/shm bash tests/test-capability-auto-install.sh` |
| **Full command** | `cd plugins/beads-lifecycle/.gsd/capabilities/beads && TMPDIR=/dev/shm PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t tests` |
| **Internal-call audit** | Existing gsd-tools argv spy plus test-owned `sitecustomize.py` interception that records and delegates `tempfile.NamedTemporaryFile` and `os.replace` |
| **Lock primitive** | Python stdlib `fcntl.flock(fd, LOCK_EX | LOCK_NB)` held on an inheritable descriptor across same-process hook re-exec |
| **Scratch** | One bounded `/dev/shm` tree per invocation; cleanup is mandatory |
| **Estimated runtime** | Measure during remediation; no unsupported estimate |

## Evidence Status

- Historical Slices 1-6 retain six genuine test-first RED commits followed by their production GREEN commits.
- Historical Slice 7 remains verification-only/test-only: its corrected real-runtime assertion was already green against Slices 1-6, so it has no fabricated RED or production delta.
- R1-R3 now have three auditable RED→GREEN pairs and the executor's complete automated gate is green. `status`, `nyquist_compliant`, and `wave_0_complete` remain unchanged until independent review re-evaluates the implementation and threat findings.

## Sampling Rate

- **Exact per-slice command:** the current harness has no selector. R1 RED/GREEN, R2 RED/GREEN, and R3 RED/GREEN each run `cd /home/dd/projects/gsd-beads && TMPDIR=/dev/shm bash tests/test-capability-auto-install.sh`; do not add or claim a selector.
- **Each RED:** add only that slice's public-boundary cases, run the exact whole-harness command, and retain nonzero output naming at least one newly added R1, R2, or R3 case before the test-only commit.
- **Each GREEN:** after the minimal fix, run the same exact whole-harness command and require exit zero plus `ALL PASS`. Because the entire harness runs, R2 GREEN includes R1 and R3 GREEN includes R1-R2 plus the genuine stale-generation, official real-runtime, preservation, command, idempotence, and CI-input cases.
- **Wave gate:** run the complete shell suite, full Python suite, Bash syntax, manifest JSON, and five-file `git diff --check` command from `22-01-PLAN.md`.
- **Feedback bound:** blocking runs only; deterministic descriptors/barriers/FIFOs plus bounded process waits, never watch mode, polling, or arbitrary sleep.

## Per-Task Verification Map

| Task ID | Bead | Requirement | Threat refs | TDD evidence | Automated command | Status |
|---|---|---|---|---|---|---|
| 22-01-01 | `gsd-beads-210` | GitHub issue #9 | T-22-01 through T-22-06, T-22-SC | R1 `1122e95`→`009226c`; R2 `70ae2fc`→`bdd1227`; R3 `2eb1c2d`→`9271dea`; historical six pairs and verification-only Slice 7 remain accurately labeled | `cd /home/dd/projects/gsd-beads && TMPDIR=/dev/shm bash tests/test-capability-auto-install.sh && cd plugins/beads-lifecycle/.gsd/capabilities/beads && TMPDIR=/dev/shm PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t tests && cd /home/dd/projects/gsd-beads && bash -n plugins/beads-lifecycle/hooks/capability-auto-install.sh tests/test-capability-auto-install.sh && python3 -m json.tool plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json >/dev/null && git diff --check -- plugins/beads-lifecycle/hooks/capability-auto-install.sh plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json tests/test-capability-auto-install.sh README.md .github/workflows/ci.yml` | automated gate passed; independent review pending |

## Required Focused Cases

| Slice | Case | Deterministic oracle / failure condition |
|---|---|---|
| R1 | Acquisition window | One public invocation either holds a fully acquired kernel lock or does no projection work; there is no separately published owner metadata to observe half-written. Spy the wrapper acquisition and the locked child's harmless confirmation on the same inherited open-file description. |
| R1 | Forged locked-child state | With a real participant holding the lock, a separate FD 9 opened on the correct inode plus forged internal environment cannot enter gsd-tools or publish. With no owner, the same descriptor acquires through the child check before projection. |
| R1 | Live contention | Pause the lock holder at the existing deterministic native-call barrier, invoke a contender, and require immediate exit zero, one exact busy line, zero contender install/set/publish calls, and unchanged ledger. |
| R1 | Crash release | Terminate the re-executed lock holder, then invoke again. The second call acquires and completes without stale detection, quarantine, polling, sleep, or retry logic. |
| R1 | Unsafe lock/helper diagnostics | Symlink and nonregular lock targets plus missing/raising Python helper emit exactly one fixed line, expose no hostile multiline stderr, traceback, or uncontrolled path, invoke no native mutation, and exit zero. |
| R2 | Symlink ownership marker | A real destination whose `.gsd-capability-skill` marker is a symlink fails ownership preguard before install/set; destination and marker target hashes remain identical. |
| R2 | Secure canonical publication | Test-only `sitecustomize.py` spies prove `NamedTemporaryFile` is created inside the canonical ledger directory, receives an unpredictable name, is flushed/file-`fsync`ed, and is the source of exactly one same-directory `os.replace`. The shim delegates all uninjected calls. |
| R2 | Nonregular target / replacement failure | Canonical symlink, directory, FIFO, or device target is rejected. Injected `os.replace` failure removes the secure temporary and preserves exact previous canonical and legacy bytes. No rollback rename is needed. |
| R2 | Legacy ordering | The `os.replace` spy observes legacy state still present and unchanged when canonical publication occurs. Only after success may an eligible regular non-symlink legacy file disappear; unsafe legacy objects remain untouched. |
| R2 | External writer before final observation | Change installed generation or selected surface before the last observation; publication is rejected and prior ledger remains byte-identical. |
| R2 | External writer after final observation | Block the replace call after final observation, mutate selected/installed state directly, then allow publish. This race is explicitly outside atomic exclusion. The next SessionStart must reject the row fast path, invoke native reconciliation, and publish a corrected row. |
| R2 | Generation ledger | Every row stores both installed bundle generation and observed post-set selected fingerprint. A global installed-generation change invalidates all runtime rows before only the active runtime is certified; runtime-native rewrites remain valid and no production transformed oracle exists. |
| R3 | Compatibility floor | Official tag `v1.10.0` peels to immutable commit `68a04ccf8ef74803bdb651e12c3b85b218bbccdf` and that commit's `package.json` declares `1.10.0`. The floor does not rely on historical `runtime-identity`. |
| R3 | Genuine stale generation A | Generation A changes selected command content, contains the retired target, and produces a selected fingerprint distinct from B before reconciliation; a metadata-only version change does not satisfy the case. |
| R3 | Real native reconciliation | Public v1.12.0 `query skills-root`, install, and set convert A to B. Raw B subject equals an independently runtime-transformed oracle after normalization of the oracle copy's absolute config root only; every non-root difference remains visible. |
| R3 | Sibling/user/preservation | A genuinely installed registry-accepted sibling remains selected across repair/repeat; a same-name user-owned destination, unrelated skill/file, and unselected runtime remain byte-identical. |
| R3 | Commands and idempotence | All selected current declarations are accepted by installed `sync.py`; the retired command is absent and rejected. The next identical SessionStart performs zero install/set calls and leaves selected tree/ledger byte-identical. |
| R3 | Clean CI | `.github/workflows/ci.yml` checks out official gsd-core `v1.12.0` with tag history, installs exact public `@opengsd/gsd-core@1.12.0` into runner-temporary `CODEX_HOME`, asserts exact official runtime identity, exports the fixture as `GSD_CORE_REPO`, and only then runs the shell suite. |

## Confound Controls

- Generation A and B differ in selected command content; assert pre-reconciliation selected hashes differ. Do not use version metadata alone.
- The real subject and independent oracle use distinct absolute config roots. Normalize only a test-owned oracle copy from oracle root to subject root; never normalize subject output, production fingerprint, installed/source data, sibling, user, unrelated, or unselected-runtime controls.
- R1 contention/crash arms differ only in holder lifetime; all synchronize at the same deterministic barrier and use bounded process waits.
- R2 publication arms differ only in the `os.replace` observation/failure or external-write timing. The `sitecustomize.py` shim delegates every unrelated stdlib call.
- A non-cooperating writer after the final observation is not expected to be atomically excluded. Its oracle is next-start invalidation and native repair.
- Helper-diagnostic fixtures use hostile multiline content, but the expected public output is one exact fixed template with validated capability/runtime tokens only.

## Wave 0 Requirements

- [x] R1 test-only commit witnesses failure of inherited nonblocking kernel locking, contention/crash semantics, unsafe-target rejection, and bounded diagnostics against the current implementation; its following GREEN commit replaces the PID/symlink recovery code.
- [x] R2 test-only commit witnesses marker-symlink trust, predictable/unsafe publication, legacy ordering, and direct-writer recovery failures; its following GREEN commit implements the secure publisher and corrected boundary.
- [x] R3 test-only commit witnesses metadata-only generation A and missing clean-runner provisioning; its following GREEN commit creates genuine stale selected content, parameterizes `GSD_CORE_REPO`, and adds the pinned CI setup.
- [x] The manifest remains `gsd >=1.10.0`; the real floor proof uses the immutable official SHA and package metadata, while the active/current local and CI runtime proves exact public version `1.12.0`.
- [x] The genuine sibling, same-name user guard, selected/retired command gates, preservation hashes, runtime-transformed test oracle, shared generation ledger, and idempotence gates remain no-skip.
- [x] Production and tests contain no polling/sleep lock recovery, runtime-to-runtime copying, custom skill copying/deletion, retired-command restoration, user-owned removal, or production transformed-output oracle.

The executor observed every Wave 0 implementation condition above. The frontmatter remains deliberately false pending independent review evidence, as required by the sign-off contract below.

## Manual-Only Verifications

All product behaviors have automated verification. Review the TDD commit order and the CI step order manually because they are repository-history/workflow properties rather than hook outputs. Bead status is an evidence sink, not a substitute for tests.

## Validation Sign-Off

- [ ] Exact plan command passes with `/dev/shm` scratch and five-file diff scope.
- [ ] Three new remediation RED/GREEN pairs are independently auditable; historical Slice 7 remains test-only.
- [ ] Kernel lock is held across re-exec and the complete transaction; crash release requires no custom stale-owner protocol.
- [ ] Secure publication calls and order are spy-proven; nonregular canonical/marker targets and failed replacement preserve data.
- [ ] Direct-writer guarantee stops at final observation plus next-start invalidation/repair.
- [ ] Official v1.10.0 floor provenance and public v1.12.0 active/current identity are both no-skip and distinct.
- [ ] CI provisions the pinned runtime before hook tests; the real generation A is genuinely stale in selected content.
- [ ] `wave_0_complete: true`, `nyquist_compliant: true`, and Summary completion are set only after implementation plus independent review evidence exists.

**Approval:** implementation evidence recorded; independent review pending
