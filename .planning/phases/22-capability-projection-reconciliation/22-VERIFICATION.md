---
phase: 22-capability-projection-reconciliation
verified: 2026-09-03T01:08:26Z
verified_head: ed547388ecfc3fa8ce7d35cbed795337b02c4bb4
status: passed
score: 7/7 must-haves verified
behavior_unverified: 0
overrides_applied: 0
gaps: []
human_verification: []
decision_coverage:
  honored: 0
  total: 0
  not_honored: []
---

# Phase 22: Capability Projection Reconciliation Verification Report

**Phase Goal:** Installer updates reconcile every selected runtime skill projection with the one active global Beads capability generation without touching user-owned or unrelated capability content.
**Verified:** 2026-09-03T01:08:26Z
**Verified HEAD:** `ed547388ecfc3fa8ce7d35cbed795337b02c4bb4`
**Status:** PASSED
**Re-verification:** No — no previous `22-VERIFICATION.md` existed.

## Verdict

PASSED. The current code and independently supplied exact-HEAD execution evidence prove the Phase 22 goal and GitHub issue #9 acceptance contract. The public hook suite finished with `ALL PASS`; the archived full Python run finished 292/292; independent code review returned PASS; and the security audit at this exact HEAD returned SECURED with 7/7 threats closed. No runtime behavior remains present-but-unverified. **Confidence: 99/100.**

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence | Confidence |
|---:|---|---|---|---:|
| 1 | A stale marker-owned projection is repaired through the runtime-native installed-capability surface; selected commands are accepted and retired `execute-plan` is absent. | VERIFIED | The hook invokes public `capability install` and runtime-targeted `capability set` at lines 570-580, then executes every selected command prefix and rejects `execute-plan` at lines 299-367. Focused cases 1, 3, 3d, 10, and real-runtime case 24 passed; case 24 starts from a selected Generation A containing `check-patch execute-plan`, proves a distinct stale fingerprint, and compares the repaired tree with an independently materialized native Generation B oracle. | 100/100 |
| 2 | Cooperating hook participants serialize observation, native mutation, verification, and publication under a nonblocking crash-released kernel lock. | VERIFIED | Lines 138-205 acquire `fcntl.flock(LOCK_EX | LOCK_NB)` and re-exec the hook with inheritable FD 9; lines 207-248 validate the descriptor/path identity and confirm/acquire the flock before transaction work. Cases 12, 12a, 12b, 15, and 16 passed, covering forged state, same-open-description confirmation, contention, descriptor isolation, and SIGKILL release. | 99/100 |
| 3 | Receipt validity is bound to both the active installed generation and observed selected-surface fingerprint; generation changes invalidate stale runtime rows and repeat updates are byte-idempotent. | VERIFIED | `ledger_has_current_row` requires source=installed and an exact `projection-v2 <runtime> <generation> <fingerprint>` row at lines 377-397. Publication retains only same-generation sibling-runtime rows at lines 497-502. The fast path recomputes installed and selected hashes at lines 547-560. Cases 2, 2b, 7, 22, 23, 23b, and 24 passed; case 24 proves stale-row removal and a silent repeat with byte-identical selected tree and ledger. | 100/100 |
| 4 | Ledger publication is secure and atomic, rejects nonregular targets, and preserves legacy/canonical state on failure. | VERIFIED | Lines 400-420 reject unsafe canonical targets. Lines 422-539 read through no-follow/type/owner/inode checks, use same-directory `NamedTemporaryFile`, flush and `fsync`, call `os.replace`, clean only the created temporary on failure, and remove eligible legacy state only after success. Cases 19-21b passed with internal spies and injected failure. | 100/100 |
| 5 | Symlinked markers and same-name user-owned destinations are rejected before native mutation; user, sibling, unrelated, and unselected-runtime state is preserved. | VERIFIED | `guard_skill_ownership` at lines 284-297 requires real directories and regular non-symlink exact owner markers. Cases 9 and 18 passed with zero native writes and byte preservation. Real-runtime case 24 hash-checks a plain user skill, unrelated state, unselected-runtime same-name content, and a genuinely installed sibling capability before/after reconciliation and repeat. | 100/100 |
| 6 | The compatibility floor is immutable gsd-core v1.10.0 provenance while current reconciliation and CI are pinned to public v1.12.0. | VERIFIED | The manifest declares `gsd >=1.10.0` at `capability.json:17-19`; README lines 39-47 distinguishes floor from current runtime. CI lines 19-40 checks out `open-gsd/gsd-core` `v1.12.0` with history, installs exact `@opengsd/gsd-core@1.12.0`, asserts runtime identity, exports `GSD_CORE_REPO`, then runs the hook suite. Case 24 proves tag `v1.10.0` peels to `68a04ccf8ef74803bdb651e12c3b85b218bbccdf` with package `1.10.0`; cases 24a/24 prove current `1.12.0` without skipping. | 99/100 |
| 7 | The external-writer guarantee is truthful: already-visible drift blocks receipt publication; drift after the final observation is detected and repaired on the next SessionStart rather than falsely claimed atomic. | VERIFIED | Final installed and selected observations occur immediately before publication at lines 596-606. Cases 22 and 23 prove visible drift preserves prior receipts; case 23b injects drift after observation, proves the resulting row mismatches, and proves next-start native repair plus a corrected, then idempotent, receipt. README lines 239-243 states the advisory boundary explicitly. | 99/100 |

**Score:** 7/7 truths verified; 0 present-but-behavior-unverified.

### Roadmap Success Criteria

| Criterion | Status | Evidence | Confidence |
|---|---|---|---:|
| Legacy stale projection is replaced natively; current commands work; `execute-plan` is absent. | VERIFIED | Truth 1 and real-runtime case 24. | 100/100 |
| Receipts bind to the active generation, serialize across runtimes, and repeated updates are byte-idempotent. | VERIFIED | Truths 2-4; cases 2, 7, 12-17, 19-23b, and 24. | 99/100 |
| User-owned skills, non-GSD skills, installed siblings, and unrelated runtime state remain intact. | VERIFIED | Truth 5; cases 9, 18, and 24 use exact byte/tree-hash preservation assertions. | 100/100 |

### Required Artifacts

`gsd-tools query verify.artifacts 22-01-PLAN.md` reported 5/5 substantive artifacts with no issues.

| Artifact | Expected | Status | Details | Confidence |
|---|---|---|---|---:|
| `plugins/beads-lifecycle/hooks/capability-auto-install.sh` | Fail-open runtime-native projection, ownership guard, kernel lock, receipt validation/publication | VERIFIED | 618 substantive lines; public entry point is wired from SessionStart, and the focused suite exercises success, idempotence, failure, concurrency, crash, ownership, publication, drift, and real-runtime paths. | 99/100 |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` | Minimum gsd-core 1.10.0 declaration and selected skill list | VERIFIED | Valid JSON; exact floor at lines 17-19 and four selected skills at lines 26-31. | 100/100 |
| `tests/test-capability-auto-install.sh` | Public-hook and real-runtime behavioral proof | VERIFIED | 30 active named PASS endpoints plus terminal `ALL PASS`; no disabled-test marker; includes internal-call spies and the no-skip v1.10/v1.12 real fixture. | 99/100 |
| `README.md` | Compatibility, ownership, locking, receipt, and recovery contract | VERIFIED | Lines 39-47 and 207-243 agree with executable source and explicitly bound the advisory-writer guarantee. | 100/100 |
| `.github/workflows/ci.yml` | Clean pinned v1.12.0 provisioning before hook tests | VERIFIED | Lines 19-40 establish source history, exact package/version identity, isolated `CODEX_HOME`, fixture export, and smoke ordering. | 99/100 |

### Key Link Verification

`gsd-tools query verify.key-links 22-01-PLAN.md` reported 3/3 links verified.

| From | To | Via | Status | Details | Confidence |
|---|---|---|---|---|---:|
| Hook | gsd-core installed-capability CLI | Public skills-root query, install, set, and command acceptance | WIRED | Hook lines 106-125, 277-279, 299-367, and 570-580; real case 24 spies exact argv. | 100/100 |
| Hook | projection-v2 ledger | Locked generation/fingerprint observation and secure publish | WIRED | Lock entry at lines 138-249 encloses hash/fast-path/native/final-check/publication logic through line 618. | 99/100 |
| Test harness | CI | `GSD_CORE_REPO`, pinned 1.12.0 identity, then public hook suite | WIRED | CI lines 19-40; case 24a verifies required ordering and case 24 consumes the exported source. | 99/100 |

### Data-Flow Trace

| Value | Source | Flow | Sink | Status | Confidence |
|---|---|---|---|---|---:|
| Installed generation | Current plugin bundle and global installed bundle bytes | Type-tagged, length-framed SHA-256 at hook lines 24-64; recomputed before and after native install | Generation-bound ledger row | FLOWING | 100/100 |
| Selected fingerprint | Runtime public skills root and manifest-selected skill directories | Manifest validation → native `capability set` → selected command verification → framed tree hash | Fast-path validation and ledger row | FLOWING | 99/100 |
| Runtime authority | Validated `GSD_RUNTIME` or unambiguous plugin-cache owner | Runtime allowlist → runtime-owned gsd-core executable → canonical public skills-root equality | Exactly one runtime-targeted native set | FLOWING | 99/100 |

No UI/rendered dynamic data exists; the Level-4 trace concerns the internal projection/receipt data path.

## Behavioral Evidence

The verifier did not rerun tests, per the orchestrator instruction. It used independently supplied exact-HEAD results and inspected the assertions that produced them.

| Behavior | Evidence | Result | Status | Confidence |
|---|---|---|---|---:|
| Complete public-hook contract | Independent `TMPDIR=/dev/shm bash tests/test-capability-auto-install.sh` result at this HEAD | Terminal `ALL PASS`; all 30 named endpoints active | PASS | 99/100 |
| Existing capability behavior regression | Archived stdlib unittest execution | `Ran 292 tests`; 292/292 passed | PASS | 99/100 |
| Syntax/manifest/diff gates | Inherited execution evidence | Bash syntax, JSON parse, scoped `git diff --check`, and scratch cleanup passed | PASS | 99/100 |
| Full-context code review | Independent exact-HEAD review receipt supplied to verifier | PASS; prior eight blockers and later forged-FD blocker closed; writer-generation warning withdrawn as outside GH-9 | PASS | 98/100 |
| Security verification | `22-SECURITY.md`, audited at exact HEAD | SECURED; 7/7 threats closed; 0 open; 0 accepted risks | PASS | 100/100 |

### Probe Execution

No separate `probe-*.sh` is declared. The phase's runnable probe is the public hook harness above, and its independent exact-HEAD result is `ALL PASS`. **Confidence: 99/100.**

## GitHub Issue #9 Requirement Coverage

The live issue is `bug: stale global beads-recall skill can shadow the current plugin contract` and remains the plan's sole requirement. `.planning/REQUIREMENTS.md` maps only Phases 19-21 and contains no additional Phase 22 requirement IDs, so there are no orphaned Phase 22 IDs.

| Issue acceptance point | Source Plan | Status | Evidence | Confidence |
|---|---|---|---|---:|
| Reproduce an upgrade from the legacy global projection to the current plugin layout. | 22-01 | SATISFIED | Cases 7 and 24 begin from legacy/stale state and prove native repair to the current generation. | 100/100 |
| Prove no stale same-name skill remains selectable after update. | 22-01 | SATISFIED | Case 24 starts with retired command content, then proves native-oracle equality and absence of `execute-plan`; cases 9/18 distinguish and preserve user-owned collisions. | 100/100 |
| Tie projected skill commands to the active `sync.py` CLI. | 22-01 | SATISFIED | Hook lines 318-365 discover every declared prefix, execute each with `--help`, and require retired-command rejection; cases 10 and 24 exercise this against the installed CLI. | 100/100 |
| Preserve user-owned non-GSD skills and unrelated runtime state. | 22-01 | SATISFIED | Cases 9, 18, and 24 assert exact bytes/tree hashes for user, non-GSD, sibling, unrelated, and unselected-runtime state. | 100/100 |

## Test Quality Audit

| Test File | Linked Requirement | Active | Skipped | Circular | Strongest Assertion | Verdict |
|---|---|---:|---:|---|---|---|
| `tests/test-capability-auto-install.sh` | GitHub issue #9 | 30 named PASS endpoints | 0 | No | Behavioral multi-step state, argv, byte/tree-hash, failure-preservation, and concurrency assertions | PASS |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` | Regression suite | 292 archived passing tests | 0 reported | No identified requirement oracle generation | Behavioral/value | PASS |

The real parity oracle is not circular: the hook is the system under test, while expected Generation B is materialized independently by the authoritative public gsd-core `capability install/set` path in a separate runtime root. Only the oracle copy's fixture-local absolute config prefix is normalized; subject output and production fingerprints are untouched. **Confidence: 98/100.**

### TDD Deviation

The implementation is behavior-first but not perfectly test-immutable. R1 GREEN `009226c` corrected the crash fixture's process-group ownership; R2 GREEN `bdd1227` corrected the post-observation mismatch oracle and manifest-derived migrated-skill path. Those fixes changed faulty test oracles in GREEN commits rather than adding the production behavior under test. The subsequent forged-descriptor regression is a strict test-only RED `6edc999` followed by hook-only GREEN `eea65ea`; historical Slice 7 is accurately classified as verification-only and did not fabricate a RED. No test is disabled or weakened in the current tree. This is a documented process deviation and audit warning, not a failure of the current goal or requirement behavior. **Confidence: 100/100.**

## Anti-Patterns and Disconfirmation

| Check | Finding | Severity | Status | Confidence |
|---|---|---|---|---:|
| Debt/stub markers in five implementation files | No unreferenced `TBD`, `FIXME`, or `XXX`; no shipped placeholder/stub identified. | None | CLEAR | 99/100 |
| Speculative dependency/abstraction | No new dependency, custom projector, cross-runtime copier, polling loop, PID registry, or stale-lock takeover. The implementation reuses native gsd-core and Python stdlib primitives. | None | CLEAR | 99/100 |
| Partial requirement sought | Direct writers racing after final observation are not atomically excluded, but neither the issue nor documentation claims they are; case 23b proves next-start invalidation/repair. The earlier writer-generation warning was correctly withdrawn as outside GH-9. | Info | IN-SCOPE CONTRACT SATISFIED | 99/100 |
| Misleading passing test sought | CI case 24a is a static ordering assertion alone, but it is backed by the independent exact-HEAD real-runtime case 24 and the pinned executable CI steps; it is not the sole behavioral proof. | Info | ADEQUATELY BACKED | 98/100 |
| Uncovered error path sought | No goal-critical uncovered path identified: install/set failure, unsafe ownership/lock/ledger targets, helper failure, replacement failure, visible external drift, post-observation drift, contention, and crash are all explicitly exercised. | None | CLEAR | 97/100 |

## Decision Coverage

No Phase 22 `CONTEXT.md` exists; `check.decision-coverage-verify` returned `skipped: true`, `total: 0`, `honored: 0`. No decision-coverage warning applies. **Confidence: 100/100.**

## Human Verification

N/A — infrastructure/tooling phase with no user-facing UI or manual-only behavior. Every state transition and ordering invariant in the merged must-haves has automated behavioral evidence; `behavior_unverified` is 0.

## Review and Threat Closure

- The independent full-context code-review receipt is PASS at `ed547388ecfc3fa8ce7d35cbed795337b02c4bb4`. It closes the prior eight blockers and the subsequent forged-FD blocker. **Confidence: 98/100.**
- `22-SECURITY.md` is bound to the same HEAD and reports SECURED, 7/7 threats closed, zero open threats, and zero accepted risks. **Confidence: 100/100.**
- The earlier writer-generation warning was withdrawn because a non-cooperating direct writer lies outside GitHub issue #9. The shipped implementation makes no atomic promise across that boundary and still provides final-observation rejection plus next-start repair. **Confidence: 99/100.**

## Gaps Summary

No blocking or human-verification gaps. The only retained note is the explicit TDD audit deviation above; it does not alter current behavior, disable evidence, or reduce the GitHub issue #9 acceptance contract.

---

_Verified: 2026-09-03T01:08:26Z_
_Verifier: gsd-verifier_
