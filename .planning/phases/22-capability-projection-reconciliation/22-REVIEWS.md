---
phase: 22
review_cycle: 1
reviewers: [antigravity]
reviewed_at: "2026-09-02T20:54:33+02:00"
plans_reviewed: [22-01-PLAN.md]
models:
  antigravity: "unknown"
model_sources:
  antigravity: "unknown"
reviewed_head: "bc8b8840e15a7cacdbef8337b05e344862a894d6"
reviewed_plan_sha256: "8ce090191e4672fc7ae8ee9bf211dea5585f43cc782008e90e89c81215ca02f8"
review_prompt_sha256: "c08b0476b597c31e6d1ad56588bb58c5b904bc44137aefe3b20e64967d19adcb"
review_output_sha256: "842ba2288c177d2b0d498d2ff4e3aa1dfa1d3fb8ad909651c3816e553f87e360"
lane_result_sha256: "a956ed0e5645a37e65de720d12392711380e923475c89f94cd242f976b78a2a3"
---

# Cross-AI Plan Review — Phase 22

The explicitly requested Antigravity lane returned `ok:true`, `stubbed:false` against the plan and repository identities recorded above. No Claude or Codex review output was included.

## Antigravity Review

`VERDICT: BLOCKED`

`CURRENT_HIGH: 4`

`CURRENT_ACTIONABLE: 3`

### Reviewer-Reported HIGH Concerns

- **HIGH — claimed execution-blocking missing Bead (confidence 99/100).** The reviewer read `.beads/interactions.jsonl` and `.beads/metadata.json`, inferred that `gsd-beads-210` did not exist, and concluded the plan precondition at `22-01-PLAN.md:158-161` would halt execution.
- **HIGH — production transformed-projection oracle conflicts with the zero-native-call fast path (confidence 98/100).** The plan requires an independently materialized runtime-transformed expected projection during fast-path and pre-publication checks (`22-01-PLAN.md:25-26,109-110,182-183,198-199`), while gsd-core performs that rewrite inside its staging path (`/home/dd/projects/gsd-core/src/runtime-artifact-conversion.cts:3307`) and exposes no dry-run transformed-output command in the installed CLI (`/home/dd/.codex/gsd-core/bin/gsd-tools.cjs:4110-4127`). Materializing an independent expected tree on every fast path would violate the plan's zero-install/set requirement.
- **HIGH — custom hook transaction lock duplicates native platform locking (confidence 95/100).** The reviewer cites the plan's `mkdir`/PID/start/quarantine protocol (`22-01-PLAN.md:48-51,107-109,180-181,196-198`) and gsd-core's per-operation capability lock (`/home/dd/projects/gsd-core/src/capability-lifecycle.cts:310-323,1047-1050`), arguing the shell lock adds deadlock and orphan-quarantine risks.
- **HIGH — seven RED/GREEN slices are bundled into one task (confidence 95/100).** The reviewer treats `22-01-PLAN.md:156-207` as conflicting with `AGENTS.md`'s one-ticket-per-task rule and says the single task is too broad to be a tracer.

### Reviewer-Reported Actionable Non-HIGH Concerns

- **MEDIUM — sibling capability fixture is not pre-existing or specified (confidence 92/100).** The reviewer notes that `plugins/` contains only `beads-lifecycle` and reads `22-01-PLAN.md:199` as lacking a concrete source for the generated real sibling fixture.
- **MEDIUM — `ps -o lstart=` portability is under-proved (confidence 88/100).** The reviewer warns that process-start formatting and command availability can differ across Linux, BSD/macOS, and restricted environments (`22-01-PLAN.md:107-108,181`).
- **LOW — Codex gsd-tools resolution is absent from the current hook (confidence 95/100).** `plugins/beads-lifecycle/hooks/capability-auto-install.sh:68-85` checks the repo, PATH, and Claude installation but not `${CODEX_HOME:-$HOME/.codex}/gsd-core/bin/gsd-tools.cjs`; the plan assigns this repair to its first RED/GREEN slice.

### Reviewer-Reported Resolved or Non-Actionable Observations

- The reviewer confirmed the current manifest's `>=1.6.0` floor is stale and that `>=1.10.0` is the first researched floor combining installed third-party materialization, the current Codex root, and the shipped skills-root query.
- The live selected `gsd-beads-recall/SKILL.md` still contains the retired `check-patch execute-plan` instruction, confirming the reported production defect.
- The reviewer confirmed the plan correctly delegates selected-skill materialization and pruning to native gsd-core, recognizes runtime rewriting, and preserves same-name user-owned content through the ownership guard.
- The current partial hook/test diff already covers native set orchestration and Cases 7-11; it does not itself satisfy the phase's revised floor, resolver, ledger, concurrency, or real-CLI proof.

### Reviewer Risk Assessment

The reviewer rated execution risk **HIGH**, based on its four reported HIGH concerns and recommended dropping the hook lock/ledger design, splitting the task, and defining a sibling fixture.

---

## Consensus Summary

CYCLE_SUMMARY: current_high=1 current_actionable=0

This single-lane cycle preserves Antigravity's raw classifications above, then reconciles them against the authoritative live tracker and the phase's locked research/orchestrator constraints. One source-grounded execution contradiction remains current. The other reported concerns are false, already assigned implementation work, or direct objections to locked scope rather than missing plan coverage.

### Current HIGH Concerns

- **HIGH — the production fast path cannot satisfy the independently materialized runtime-transformed oracle while also making zero native set calls.** The plan applies the independent oracle to production fast-path and final-recheck behavior (`22-01-PLAN.md:109-110,182-184`) and separately requires zero install/set on an exact fast path (`22-01-PLAN.md:183`). Antigravity traced runtime transformation to gsd-core's internal staging implementation and found no non-mutating CLI output seam. The plan must separate the test oracle from executable production checks, or name a real non-mutating public transformation seam. Confidence: 98/100.

### Current Actionable Non-HIGH Concerns

None.

---

## Post-Implementation Review — Superseding Remediation

All cross-AI `PASS` entries in this file evaluated a pre-execution plan only. The later full-context implementation review supersedes them as terminal evidence.

`IMPLEMENTATION_REVIEW: BLOCKED`

`CURRENT_BLOCKERS: 8`

`OPEN_THREATS: 3`

### Current Blocking Concerns

1. **Custom PID/process-start symlink recovery is not a safe crash-lock primitive (100/100).** It expands the trusted synchronization surface across procfs/`ps`, stale classification, quarantine, and reacquisition instead of obtaining kernel-managed ownership.
2. **Canonical ledger publication uses a predictable process-derived temporary name (100/100).** An attacker or concurrent filesystem actor can precreate/substitute that path; secure same-directory creation is missing.
3. **Legacy state is moved before canonical publication succeeds (100/100).** A failed replacement transiently or permanently removes the only retry evidence rather than preserving both prior states.
4. **The ownership preguard accepts a symlinked marker (100/100).** File-type/content checks can follow the marker into another object, violating the ownership proof before native mutation.
5. **Clean CI does not provision the real runtime assumed by the no-skip integration test (100/100).** The workflow currently depends on a developer-adjacent gsd-core checkout and active home install.
6. **Generation A is stale only in metadata, not selected command content (100/100).** The real-runtime test therefore does not prove repair of the actual stale projection defect.
7. **The non-cooperating external-writer guarantee exceeds an advisory lock's atomic boundary (100/100).** A direct writer can race after the final observation; correctness must be stated as immediate observation plus next-start invalidation and repair.
8. **Python/hash/native-helper diagnostics are not uniformly bounded (95/100).** Raw multiline stderr, tracebacks, or uncontrolled paths can escape the public fail-open boundary.

### User-Approved Remediation

| Concern | Approved mechanism | Required proof |
|---|---|---|
| Locking | Python stdlib nonblocking `fcntl.flock` held on an inherited descriptor across same-process hook re-exec; kernel auto-release on termination | Acquisition-window impossibility, live contention, crash release, unsafe target, no polling/sleep/stale recovery |
| Ledger | Nonregular-target rejection plus secure same-directory `NamedTemporaryFile`, flush/file-`fsync`, and `os.replace`; legacy cleanup only after canonical success | Call spies, operation ordering, injected replacement failure, exact canonical/legacy preservation |
| Ownership | Require marker to be regular and non-symlink before reading exact owner content | Symlink marker prevents install/set and preserves marker target/destination |
| Reproducibility | CI checks out official gsd-core `v1.12.0`, provisions exact public `@opengsd/gsd-core@1.12.0`, and verifies runtime identity before tests | Clean-runner no-skip integration using runtime-derived `GSD_CORE_REPO` |
| Real defect | Generation A contains genuinely stale selected command content | Distinct A/B selected fingerprints and native B reconciliation with command/sibling/preservation/idempotence gates |
| External writer | Final observation rejects already-visible drift; a later direct-write race is detected and repaired on next SessionStart | Separate before-observation and after-observation timing fixtures |
| Diagnostics | Map every helper failure to one fixed bounded stage line and suppress raw helper output | Hostile multiline helper fixtures yield exactly one stable line |

The remediation adds three new genuine RED→GREEN pairs R1-R3. Historical Slices 1-6 remain six genuine production pairs; historical Slice 7 remains verification-only/test-only. Bias assessment: **NONE**. No implementation or completion claim exists until the revised plan is executed and independently reviewed.

### Reconciled Non-Current Findings

- **Missing Bead: disproved.** Live `TMPDIR=/dev/shm bd show gsd-beads-210 --json` returned the bug as `in_progress`. `.beads/issues.jsonl` and interaction logs are passive/history surfaces, not the Dolt-backed tracker authority. Confidence: 100/100.
- **Duplicate lock: not established.** The cited native lock bounds one capability operation; it does not span the hook's install -> set -> verify -> shared-ledger publication transaction. Updated `22-RESEARCH.md:135-149,229-231` explicitly assigns the outer lock to hook-participant serialization and retains a final recheck for external native writers. Confidence: 96/100.
- **Task bundling: excluded by locked scope.** The current planning contract explicitly requires exactly one cohesive TDD task bound to `gsd-beads-210`; the plan complies. This review cannot widen the ticket/task boundary. Confidence: 100/100.
- **Sibling fixture: already assigned.** `22-01-PLAN.md:199` directs the test to build valid Beads A/B and sibling bundles inside isolated `/dev/shm`, install/set them through the public CLI, and reject a loose marker as proof. A checked-in second plugin is unnecessary. Confidence: 98/100.
- **Process-start portability: no demonstrated current defect.** The protocol stores and later compares the same host command's complete identity string; it does not parse date fields. The plan also requires missing/invalid metadata to fail through the bounded stale-recovery contract. Cross-platform execution remains part of the specified focused test seam, not an uncovered behavior. Confidence: 90/100.
- **Codex resolver: planned work, not a plan gap.** The compatibility/runtime RED/GREEN slice explicitly repairs active-runtime gsd-tools resolution and proves exact argv/root behavior. Confidence: 100/100.

## Invocation Provenance

- Selection: explicit `--phase 22 --agy`; only the `antigravity` lane was planned and invoked.
- Scratch: one run-scoped directory under `/dev/shm`, removed after immediate result capture.
- Result envelope: `ok:true`, `stubbed:false`, model/source `unknown`.
- Plan SHA-256 after the lane remained `8ce090191e4672fc7ae8ee9bf211dea5585f43cc782008e90e89c81215ca02f8`; reviewed Git HEAD remained `bc8b8840e15a7cacdbef8337b05e344862a894d6`.
- No plan, source, Beads issue, commit, push, or Dolt sync mutation occurred during review.

---

## Cycle 2 Direct Claude Convergence Review

- Reviewer: Claude CLI (`sonnet`, high effort)
- Reviewed Git HEAD: `bc8b8840e15a7cacdbef8337b05e344862a894d6`
- Reviewed plan SHA-256: `3ac35260dbdea679fe04dfb9f772ae3b1ed45f9a719e7d4a336a0ce19e01a60e`
- Scope: `AGENTS.md`, `ROADMAP.md`, `STATE.md`, current Phase 22 plan/research/validation, live `bd show gsd-beads-210`, all four target files, and gsd-core v1.6.0/v1.8.0/v1.10.0 source.
- Prior oracle concern: resolved; production fingerprints observed selected bytes and independent transformed materialization remains test-only.
- Process identity, symlink lock, v1.10 seams, vertical TDD, sibling capability, GH-9 coverage, and Ponytail scope: passed.

`VERDICT: PASS`

`CYCLE_SUMMARY: current_high=0 current_actionable=0`

### Current HIGH Concerns

None.

### Current Actionable Non-HIGH Concerns

None.

---

## User-Approved Post-Review Execution Correction — Slice 7

- This is an execution-contract correction, not a new external-review verdict. The current reviewed concern count remains `current_high=0 current_actionable=0`.
- Slice 7 is explicitly verification-only/test-only because the corrected real-runtime test is already green against the production behavior delivered by Slices 1-6. The plan retains six genuine audited RED/GREEN production pairs and forbids a fabricated seventh RED, production delta, or production commit.
- The independent transformed oracle and subject require distinct absolute config roots to prevent cross-mutation. Native rewriting may embed those roots, so comparison normalizes only a test-owned copy of the independent oracle from oracle root to subject root. Every non-root mismatch must remain visible. The raw subject projection, production selected-surface fingerprint, installed/source data, and sibling/user/unrelated/unselected controls remain unnormalized.
- What does it bias? **NONE.** The correction preserves real TDD provenance and removes only the independent test oracle's absolute-path confound; it does not weaken production ownership, fingerprint, preservation, command, floor, current-runtime, or no-skip gates.

`CYCLE_SUMMARY: current_high=0 current_actionable=0`

### Current HIGH Concerns

None.

### Current Actionable Non-HIGH Concerns

None.

---

## Current Terminal Status

`IMPLEMENTATION_REMEDIATION: COMPLETE`

`IMPLEMENTATION_REVIEW: PENDING`

`CURRENT_BLOCKERS: NOT_REASSESSED`

`OPEN_THREATS: NOT_REASSESSED`

The executor landed the approved test-first remediation pairs R1
`1122e95`→`009226c`, R2 `70ae2fc`→`bdd1227`, and R3
`2eb1c2d`→`9271dea`. The final public harness reached `ALL PASS`; the full
capability suite ran 292 tests with `OK` and no skips; Bash syntax, manifest
JSON, five-file diff hygiene, and `/dev/shm` cleanup passed. Bead
`gsd-beads-210` remains open.

This section records executor evidence only. It does not supersede or
self-certify the prior security/code-review findings. A fresh independent
review must reassess the eight historical blockers and three threats against
the remediated HEAD before Phase 22 receives a review or security verdict.
