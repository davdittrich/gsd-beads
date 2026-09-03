# Phase 22: Capability Projection Reconciliation - Research

**Researched:** 2026-09-02 [VERIFIED: `date --iso-8601=seconds`, 2026-09-02]
**Domain:** Version-gated gsd-core capability surface materialization, installer-owned skill migration, and concurrent runtime-scoped hook state.
**Confidence:** HIGH for repository and tagged-source findings; MEDIUM for performance ordering because no benchmark was run.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GH-9 | Installing or updating gsd-beads replaces a stale installer-owned lifecycle skill with the current selected implementation without restoring retired commands or changing user-owned, other-capability, other-runtime, or unrelated state. | The tag comparison proves gsd-core `1.10.0` is the first verified release combining installed third-party materialization, the corrected Codex destination, and the shipped `query skills-root` boundary required by this phase. [VERIFIED: GitHub issue `davdittrich/gsd-beads#9`; gsd-core tags `v1.8.0` and `v1.10.0`] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Track the implementation under Bead `gsd-beads-210`; each plan task requires its own Beads issue. [VERIFIED: supplied `AGENTS.md`; Bead identifier supplied by orchestrator]
- Use GSD planning and plan-check before this multi-file/config change. [VERIFIED: supplied `AGENTS.md`]
- Use strict public-boundary TDD and internal-call spies; green results produced by a workaround are invalid. [VERIFIED: supplied `AGENTS.md`]
- Preserve user-owned and unrelated files; deletion based only on a `gsd-*` prefix is forbidden. [VERIFIED: supplied `AGENTS.md`; GitHub issue `davdittrich/gsd-beads#9`]
- Prefer the native platform mechanism and minimum code; do not reintroduce `execute-plan`, copy skills between runtimes, or build a second projection system. [VERIFIED: supplied Ponytail ladder; GitHub issue `davdittrich/gsd-beads#9`]
- Research must compare at least two current mechanisms and rank performance, simplicity/LOC, ecosystem support, and maintenance. [VERIFIED: supplied `AGENTS.md`]

## Summary

The original defect was a version-boundary failure, not a missing copy operation in gsd-beads. Before the Phase 22 baseline, the capability declared `"gsd": ">=1.6.0"`, but tagged gsd-core `v1.6.0` cannot surface an installed third-party skill: `capability set` validates against the frozen first-party registry, its skill stager reads only gsd-core's own command directory, and its conservative prune preserves an unknown same-name `gsd-*` directory. The current baseline already declares the corrected `">=1.10.0"` floor; the remaining work is the reviewed locking, publication, ownership, fixture, diagnostics, and CI remediation. [VERIFIED: current manifest; `git show v1.6.0:src/capability-writer.cts:153-160`; `git show v1.6.0:src/install-profiles.cts:459-523`; `git show v1.6.0:src/surface.cts:383-429`]

Tagged gsd-core `v1.8.0` contains owner-bound third-party staging and runtime body rewriting, but it is not a sufficient floor: its Codex surface resolves the obsolete destination rather than Codex's current `~/.agents/skills`, and its installed `gsd-tools` lacks `query skills-root`. Tagged gsd-core `v1.10.0` is the first release verified here to combine the native third-party surface with the corrected Codex destination and shipped `gsd-tools query skills-root`; floor provenance is the immutable official tag commit `68a04ccf8ef74803bdb651e12c3b85b218bbccdf` plus that commit's `package.json` version `1.10.0`, not an exact-floor `runtime-identity` result. Production must trust successful native set, verify exact ownership and CLI contracts, and record the observed selected-surface fingerprint; only the isolated real integration test against verified active/current gsd-core `1.12.0` independently materializes runtime-transformed expected output. Its subject and oracle require distinct absolute config roots to prevent cross-mutation, so only a test-owned oracle copy normalizes the embedded oracle root to the subject root before comparison. Raw installed `SKILL.md` bytes are never the selected-output oracle, and no production or subject bytes are normalized. [VERIFIED: gsd-core `v1.8.0` commit `e4df05126deaf5ad1c29bf35b9dfe2193c80cb0b`; `v1.10.0` commit `68a04ccf8ef74803bdb651e12c3b85b218bbccdf`; `git grep skills-root v1.10.0 -- gsd-core/bin/gsd-tools.cjs`; `git show v1.8.0:src/install-profiles.cts:596-603`; `git show v1.8.0:src/surface.cts:393-401`; active `runtime-identity --raw` version `1.12.0`]

**Primary recommendation:** Keep the proven `">=1.10.0"` floor, invoke native `capability set` for the explicit runtime, and hold one Python stdlib nonblocking `fcntl.flock` across the re-executed hook's complete transaction. Publish the shared `projection-v2` generation/fingerprint ledger through a secure same-directory `NamedTemporaryFile` and `os.replace` only after install, materialization, selected-skill verification, and final observations succeed; remove legacy state only after canonical success. Do not add a custom projection writer, PID/stale-owner recovery protocol, or production transformed-output oracle. [User-approved remediation; Python stdlib contracts]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Install the capability bundle | gsd-core capability lifecycle | Global capability storage | Existing `capability install` owns source validation, atomic promotion, and ledger state. [VERIFIED: `/home/dd/projects/gsd-core/src/capability-lifecycle.cts:997-1171`] |
| Select the active runtime | Plugin SessionStart hook | gsd-core runtime descriptors | The hook knows the executing plugin cache/root; materialization must pass explicit runtime/config scope rather than affect every installed runtime. [VERIFIED: `plugins/beads-lifecycle/hooks/session-start.sh:5-13`; `plugins/beads-lifecycle/hooks/capability-auto-install.sh:18-20`; GitHub issue `davdittrich/gsd-beads#9` out-of-scope rules] |
| Reconcile projected skills | gsd-core surface engine | Runtime skills directory | v1.8.0 already performs owner-bound staging, overwrite, and owned-only pruning. [VERIFIED: `git show v1.8.0:src/install-profiles.cts:710-755`; `git show v1.8.0:src/surface.cts:475-513,570-588`] |
| Cache completed generation | Plugin hook | Shared locked ledger | One `projection-v2` ledger records runtime-to-installed-generation and observed-selected-fingerprint rows; one inherited `fcntl.flock` serializes cooperating hooks. The final observation rejects drift already visible; a later direct-writer race is repaired from row mismatch on the next SessionStart. [Phase 22 design decision] |
| Validate skill/CLI compatibility | Existing shell integration test | Capability `sync.py` parser | The selected skill is the consumer contract; every declared command must parse under the installed CLI. [VERIFIED: GitHub issue `davdittrich/gsd-beads#9`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:156-182`] |

## Standard Stack

### Core

| Tool | Proven version | Purpose | Why standard |
|------|----------------|---------|--------------|
| gsd-core compatibility floor | `1.10.0` minimum | Manifest compatibility and first-shipped-mechanism provenance | Official tag `v1.10.0` peels to `68a04ccf8ef74803bdb651e12c3b85b218bbccdf`, whose `package.json` version is exactly `1.10.0`; no installed runtime is required to self-report the minimum. [VERIFIED: immutable tag/source metadata] |
| Active/current gsd-core | `1.12.0` | Real public `query skills-root`, capability install/set, transformation, composed sibling surface, and CLI contract proof | `runtime-identity --raw` verifies package `@opengsd/gsd-core` version `1.12.0`; this is the executable integration boundary, distinct from the 1.10.0 compatibility floor. [VERIFIED: active runtime identity] |
| Bash | Existing project dependency | SessionStart orchestration and sidecar commit | The hook and its test already use Bash; no dependency is added. [VERIFIED: `plugins/beads-lifecycle/hooks/capability-auto-install.sh:1-99`; `tests/test-capability-auto-install.sh:1-198`] |
| Python standard library | Existing capability dependency | `sync.py` command-contract parser, nonblocking `fcntl.flock` wrapper, and secure atomic ledger publisher | Current project requirements already require Python 3 without third-party packages; the approved remediation deletes the custom PID/start-time recovery protocol. [VERIFIED: `README.md:39-43`; `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:5-11`; Python stdlib documentation linked under Sources] |

### Supporting

| Tool / seam | Purpose | When to use |
|-------------|---------|-------------|
| `gsd-tools capability set` | Re-materialize the selected runtime's surface after the bundle install. | Invoke with the selected runtime after install success; bind `--config-dir` only where the public command supports it. In v1.8.0 it accepts composed third-party capabilities and passes the registry through the whole surface path. [VERIFIED: `git show v1.8.0:src/capability-writer.cts:153-169,351-380`] |
| `.gsd-capability-skill` marker | Persist narrow installer ownership. | Native gsd-core writes it beside every materialized third-party skill and later uses it only for absent retained entries. [VERIFIED: `git show v1.8.0:src/install-profiles.cts:550-564,750-754`; `git show v1.8.0:src/surface.cts:481-513`] |
| Existing shell smoke test | Public hook boundary. | Extend it; do not create a parallel migration framework. [VERIFIED: `tests/test-capability-auto-install.sh:1-59`]

The production hook adds no external package. CI deliberately provisions the already-established public package `@opengsd/gsd-core@1.12.0` at an exact version so the real-runtime gate is reproducible on a clean runner.

### Package Legitimacy Audit

| Package | Version | Status | Evidence | Use |
|---|---:|---|---|---|
| `@opengsd/gsd-core` | `1.12.0` | VERIFIED | Official package identity is asserted through `runtime-identity --raw`; exact-version install syntax is documented by npm; official tagged source is checked out separately. | CI-only public runtime provision before the Phase 22 hook suite. |

## Alternatives Considered

| Rank | Mechanism | Performance | Simplicity / LOC | Ecosystem support | Maintenance | Decision |
|-----:|-----------|-------------|------------------|-------------------|-------------|----------|
| 1 | Raise engine floor to proven gsd-core `>=1.10.0`; install then invoke native `capability set` materialization | One bounded native full-surface pass. It writes more than a targeted copier, but no duplicate discovery or ownership pass is added. | Lowest compliant implementation: one engine-field edit plus hook sequencing/state changes. | Canonical composed registry, corrected Codex destination, shipped skills-root query, and ownership marker. | Upstream gsd-core owns future layout and pruning changes. | **Use.** Ponytail rung 4: native platform feature already covers the repair. |
| 2 | Custom gsd-beads projection writer that copies/removes only Beads skills | Probably the least I/O for this one capability, but unbenchmarked. | Highest LOC: must duplicate runtime path resolution, owner validation, atomic copying, prune policy, and error handling. | Competes with rather than uses gsd-core's surface contract. | High drift/data-loss risk; must track every runtime descriptor change. | Reject despite likely raw-speed advantage: correctness and ownership cannot be demonstrated without recreating gsd-core. |
| 3 | Run `capability set`, then verify/fail closed without raising the engine floor or repairing projection | Lowest successful write cost. | Low LOC. | Uses the public CLI but assumes behavior the declared `>=1.6.0` range does not provide. | Leaves compatible-looking but unrepaired installations retrying forever. | Reject: detection alone cannot satisfy GH-9 on v1.6.0. |

**Selection by mandated ordering:** Performance does not decide the mechanism because the fastest compliant candidate is unbenchmarked and duplicates security-sensitive lifecycle code; the verify-only candidate is not compliant. Among mechanisms that are proven correct, native gsd-core wins simplicity/LOC, ecosystem support, and maintenance by a wide margin. [Confidence: 92/100]

### Remediation Mechanism Alternatives

| Rank | Mechanism | Performance | Simplicity / LOC | Ecosystem support | Maintenance | Decision |
|-----:|-----------|-------------|------------------|-------------------|-------------|----------|
| 1 | Python stdlib `fcntl.flock` held across same-process hook re-exec; secure `NamedTemporaryFile` plus `os.replace` ledger publish | One nonblocking lock syscall on the fast path; no stale-owner probes | Deletes PID/start-time, quarantine, retry, and predictable shell-temp logic | Standard POSIX/Python contracts with primary documentation | Kernel owns crash release; no stale-token schema | **Use.** |
| 2 | External `flock(1)` plus shell publisher | Comparable lock cost | Short lock command, but safe structured publication still needs Python | Common on Linux but not guaranteed by the declared runtime | Adds an optional executable and split failure semantics | Reject. |
| 3 | PID/process-start symlink token with stale quarantine | Extra procfs/`ps`, readlink, rename, and recovery work | Highest LOC and most race-sensitive | Custom cross-platform identity protocol | Permanent stale-owner/replacement-race burden | Remove. |
| 4 | Always run native install/set and remove the receipt | Repeats full reconciliation on every SessionStart | Least state | Native gsd-core only | Avoids ledger code but discards the required fast path and does not serialize hook participants | Reject. |

**Selection by mandated ordering:** stdlib `flock` wins performance first, then simplicity/LOC, ecosystem support, and maintenance. It removes custom stale-lock recovery rather than replacing it with another ownership algorithm. [User-approved remediation; Confidence: 100/100]

## Architecture Patterns

### System Architecture Diagram

```text
SessionStart for runtime R
        |
        v
derive explicit R + config root
        |
        v
acquire inherited nonblocking Python fcntl.flock
        |
        v
compute bundle hash + selected fingerprint + read sidecar schema/R row
        |
        +-- exact current generation --> silent success
        |
        v
gsd capability install (shared global bundle/ledger)
        |
        v
gsd capability set beads --runtime R --scope global
        |
        v
composed registry --owner binding--> stage every accepted capability skill
        |                                      |
        |                                      +--> other installed capability retained
        v
overwrite retained dirs + prune absent marker-owned dirs
        |
        v
verify selected Beads skill commands against installed sync.py CLI
        |
        v
secure same-directory NamedTemporaryFile + os.replace of canonical ledger
```

### Recommended Project Structure

No new production module is justified. Keep implementation and TDD in the minimum existing seams:

```text
plugins/beads-lifecycle/
├── .gsd/capabilities/beads/capability.json  # retain proven >=1.10.0 floor
└── hooks/capability-auto-install.sh         # kernel lock -> native reconcile -> secure ledger
tests/
└── test-capability-auto-install.sh          # remediation, public-boundary, and real-runtime cases
.github/workflows/
└── ci.yml                                   # pinned public gsd-core 1.12.0 provision/identity gate
```

The hook, manifest, test, README, and CI workflow are the five implementation seams. README changes accompany behavior because the minimum/current versions and shared locked-ledger contract are operator-visible; add no separate documentation file. [Confidence: 100/100]

### Pattern 1: Owner-bound native re-materialization

**What:** Let the composed registry define `stem -> capability id`; read only the declaring capability's installed `SKILL.md`; stage every accepted stem; apply gsd-core's runtime-targeted body rewrite to the complete staged skills directory; overwrite current retained directories; prune only absent marker-owned directories.

**Why:** It makes a stale Beads directory current while preserving a genuinely installed second capability and unmarked user content.

**Evidence:**

- Exact v1.8.0 registry load: `loadRegistry({ includeInstalled: true, cwd, gsdHome: process.env['GSD_HOME'] })`. [VERIFIED: `git show v1.8.0:src/capability-writer.cts:153-169`]
- Exact owner lookup: `_owningCapabilityId(stem, registry.capabilityClusters)`. [VERIFIED: `git show v1.8.0:src/install-profiles.cts:605-625`]
- Exact marker name: `.gsd-capability-skill`. [VERIFIED: `git show v1.8.0:src/install-profiles.cts:550-564`]
- Exact transformation boundary: installed capability content is staged as authored at the copy step, then `applySurface` calls `rewriteStagedSkillBodies` for the selected runtime/config/scope before copying to the destination. [VERIFIED: `git show v1.8.0:src/install-profiles.cts:596-603`; `git show v1.8.0:src/surface.cts:393-401`]
- Exact retained-first rule: `if (retainedNames.has(entry)) continue`. [VERIFIED: `git show v1.8.0:src/surface.cts:481-500`]

### Pattern 2: Shared `projection-v2` ledger under one hook transaction lock

**What:** Replace the legacy capability-only raw hash with one shared ledger at `${GSD_HOME:-$HOME}/.gsd/capability-auto-install-$CAP_ID.projections`. Its canonical rows are `projection-v2 <runtime> <64-lowercase-hex-installed-generation> <64-lowercase-hex-selected-surface-fingerprint>`, sorted by runtime with exactly one row per runtime. The fingerprint is a canonical SHA-256 over sorted root-relative paths and file bytes in exactly the four manifest-declared Beads selected directories, including owner markers but excluding sibling/user directories, observed after successful native set and verification. The first successful migration securely publishes this ledger before removing an eligible regular non-symlink legacy file. [Phase 22 design decision]

**Required semantics:**

- **Serialization scope:** before any ledger read or projection mutation, a Python stdlib wrapper opens a plugin-owned regular lock file without following symlinks, validates the path and descriptor identify the same object, and performs exactly one `fcntl.flock(fd, LOCK_EX | LOCK_NB)`. On success it marks the descriptor inheritable and replaces itself with the same Bash hook in locked-child mode, which validates and retains that descriptor through fast-path observation, native install/set, post-set verification, and receipt publication. Kernel descriptor lifetime releases ownership on normal exit, signal, or crash; there is no PID/start identity, stale-owner probe, quarantine, polling, sleep, or reacquire. This serializes cooperating hook participants only.
- **Contention and diagnostics:** `EACCES` or `EAGAIN` produces one fixed busy diagnostic and immediate exit-zero fail-open. A symlink/nonregular lock target, missing `fcntl`, invalid inherited descriptor, or wrapper failure produces one fixed bounded diagnostic with no raw helper stderr, traceback, or uncontrolled path.
- **Merge/overwrite:** while locked, replace only the selected runtime's row and retain every other valid runtime row. Reject an existing canonical target unless it is a regular non-symlink file. Create a secure unpredictable `NamedTemporaryFile` in the canonical ledger directory, write canonical sorted state, flush and file-`fsync`, then atomically `os.replace` it over the target in that same directory. Remove the temporary on every failure.
- **Legacy ordering:** leave the legacy file byte-identical until canonical `os.replace` succeeds. Only then remove it when it is a regular non-symlink plugin-owned file; failed or unsafe legacy cleanup cannot roll back the already-authoritative canonical ledger.
- **External-writer detection:** immediately before ledger publish, recompute the installed bundle generation and selected-surface fingerprint. If either already differs from the prepared active-runtime row, publish nothing. A direct writer that races after that final observation is outside the advisory-lock guarantee: the next SessionStart must detect the row mismatch, invoke native reconciliation, and replace the receipt. Do not claim atomic exclusion of non-cooperating writers.
- **Idempotency:** an exact `projection-v2` row whose installed generation and selected-surface fingerprint both match freshly recomputed state takes the silent fast path while under the shared lock. Production never independently materializes expected transformed output.
- **Failure:** any install, materialization, verification, final recheck, or publish failure leaves the prior valid ledger and legacy file unchanged. Remove only the securely created temporary; lock release is automatic with the inherited descriptor.

**Why the shared lock is mandatory:** the installed capability generation is shared across runtimes, so independent receipts can each truthfully describe a different instant while a concurrent hook replaces the shared installation. The inherited kernel lock makes participating install/set/verify/publish operations serial and has crash release without custom stale ownership. The final observation catches already-visible external drift, while the next-start mismatch gate repairs a later direct-writer race. [VERIFIED: current shared global install and premature fast path at `plugins/beads-lifecycle/hooks/capability-auto-install.sh:42-53,81-97`; Python stdlib `fcntl` contract; Confidence: 99/100]

### Pattern 3: Explicit runtime boundary

**What:** Resolve one active runtime from the executing installed plugin cache owner before reading its ledger row or invoking gsd-core, then pass that runtime explicitly and bind `--config-dir` only where the public command supports it. If runtime identity is not provable, fail open with a precise warning and do not publish a receipt. Do not promise an unsupported `GSD_RUNTIME` override.

**Why:** Defaulting to or sweeping another installed runtime violates GH-9's cross-runtime prohibition. The confirmed Codex plugin root is under `/home/dd/.codex/plugins/cache/...`; this repository documents Claude marketplace cache under `~/.claude/plugins/cache/`. [VERIFIED: GitHub issue `davdittrich/gsd-beads#9`; `README.md:264-271`]

### Anti-Patterns to Avoid

- **Raise the engine floor without materializing:** installation updates the shared bundle but does not itself prove the runtime projection changed.
- **Materialize on gsd-core v1.6.0:** the frozen registry and first-party-only stager cannot repair the third-party directory. [VERIFIED: tag evidence above]
- **Delete every `gsd-*` directory:** v1.8.0 deliberately preserves unmarked unknown entries; prefix alone is not ownership. [VERIFIED: `git show v1.8.0:src/surface.cts:475-515`]
- **Use a synthetic marker as the other-capability proof:** retention depends on that capability being present in the composed registry and staged set. Install a real second fixture capability.
- **Unlocked shared ledger:** atomic rename prevents torn bytes but does not prevent lost runtime rows or a receipt for an installation another hook replaced.
- **Restore `check-patch execute-plan`:** the stale instruction is the defect, not an API compatibility target. [VERIFIED: GitHub issue `davdittrich/gsd-beads#9`]

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Skill ownership | Prefix scanner or first-match directory scan | v1.8.0 `capabilityClusters` owner binding | Registry composition rejects collisions and binds the read to the declaring capability. [VERIFIED: `git show v1.8.0:src/install-profiles.cts:499-625`] |
| Projection copying/pruning | Beads-specific recursive copier | Native `applySurface` | It already handles runtime conversion, overwrite, retained sets, and marker-owned pruning. [VERIFIED: `git show v1.8.0:src/capability-writer.cts:351-380`; `git show v1.8.0:src/surface.cts:570-588`] |
| Hook transaction synchronization | Polling, PID/start-time tokens, stale-owner takeover, external `flock(1)`, or independent receipts | Python stdlib nonblocking `fcntl.flock` held across same-process hook re-exec | One kernel primitive serializes cooperating hooks, has no half-published owner record, and releases automatically on exit or crash. |
| Ledger publication | Predictable PID-suffixed temporary files or moving legacy state before success | Same-directory `NamedTemporaryFile`, file `fsync`, and `os.replace` after nonregular-target rejection | Secure creation removes name races; same-filesystem replacement publishes atomically; legacy remains recoverable until canonical success. |
| Command compatibility layer | Alias for retired targets | Execute every selected skill declaration against current `sync.py` parser | The selected instruction must match the active CLI; stale instructions must disappear. |

**Key insight:** gsd-beads should orchestrate the native lifecycle, not become a second lifecycle implementation.

## Runtime State Inventory

| Category | Items found | Action required |
|----------|-------------|-----------------|
| Stored data | Global capability bundle and ledger under the gsd capability home; current Beads bundle is internally current. | Reinstall normally; do not migrate Beads/Dolt data. [VERIFIED: live ledger observation in GitHub issue `davdittrich/gsd-beads#9`] |
| Live service config | None. No service/UI configuration participates in skill projection. | None. [Confidence: 96/100]
| OS-registered state | Runtime skill directories, including the confirmed stale `/home/dd/.agents/skills/gsd-beads-recall/`. | Native materialization overwrites the retained Beads skill in the selected runtime only. [VERIFIED: GitHub issue `davdittrich/gsd-beads#9`; v1.8.0 surface evidence]
| Secrets/env vars | `GSD_HOME`, `CODEX_HOME`, and `CLAUDE_CONFIG_DIR` scope capability/config roots; no secret value changes. | Derive runtime from the executing installed plugin cache owner; bind only public supported config flags. [VERIFIED: current hook and active gsd-core runtime descriptors]
| Build artifacts / installed packages | Legacy raw-hash sidecar, shared installed generation, runtime-projected skill directories, persistent regular lock inode, and canonical ledger. | Hold the regular lock inode through kernel `flock`; securely replace the v2 ledger; remove an eligible legacy hash only after canonical success. No stale-lock artifact requires recovery. |

## Common Pitfalls

### Pitfall 1: Declared engine range exceeds actual mechanism support

**What goes wrong:** a floor below `">=1.10.0"` admits either a host without third-party staging or v1.8.0's wrong Codex destination/unshipped `query skills-root` boundary. **Avoidance:** require the proven `">=1.10.0"` floor before relying on this transaction. **Warning:** an unknown capability, absent query verb, or successful surface pass targeting the obsolete Codex root. [Confidence: 99/100]

### Pitfall 2: Marker-only second-capability fixture

**What goes wrong:** a test says another capability is preserved even though native staging never saw it. **Why:** the retained set comes from the composed registry, not the marker. **Avoidance:** in the isolated active/current 1.12.0 integration test, install a genuine second capability with a distinct declared skill and verify its selected bytes against independently materialized runtime-transformed expected output after Beads reconciliation. [Confidence: 98/100]

### Pitfall 3: Sidecar committed before the postcondition

**What goes wrong:** an install succeeds, materialization or command verification fails, and future SessionStart runs skip permanently. **Avoidance:** publish the shared canonical ledger last and atomically, after the final generation recheck. [VERIFIED: current premature success boundary at `plugins/beads-lifecycle/hooks/capability-auto-install.sh:81-97`; Confidence: 99/100]

### Pitfall 4: Unserialized shared-generation publication

**What goes wrong:** independent or unlocked receipts certify runtime projections around competing replacements of the one shared installed bundle. **Avoidance:** one shared ledger and hook-participant transaction lock cover install through publish; immediately recheck installed generation and observed selected-surface fingerprint before publish to detect external native writers. [VERIFIED: `plugins/beads-lifecycle/hooks/capability-auto-install.sh:42-53`; Confidence: 99/100]

### Pitfall 5: Post-set state is reported but selected skill is incompatible

**What goes wrong:** registry/surface status is green while a selected skill still declares a retired target. **Avoidance:** production verifies exact owner markers, executes every extracted `check-patch` target through `sync.py ... --help`, asserts `execute-plan` is absent, and fingerprints the observed selected surface. The isolated active/current 1.12.0 integration test separately compares native output with independently transformed expected output. [VERIFIED: GitHub issue `davdittrich/gsd-beads#9`; `git show v1.8.0:src/install-profiles.cts:596-603`; `git show v1.8.0:src/surface.cts:393-401`; Confidence: 98/100]

### Pitfall 6: A custom stale-lock identity protocol outlives its assumptions

**What goes wrong:** PID reuse, process-start parsing, quarantine ownership, and crash timing create a second synchronization system whose safety depends on procfs/`ps` dialects and multi-step recovery. **Avoidance:** acquire Python stdlib `fcntl.flock` once in nonblocking mode and keep its descriptor open across same-process hook re-exec; the kernel arbitrates contention and releases the lock on termination. [User-approved remediation; Python stdlib contract; Confidence: 100/100]

## State of the Art

| Old approach | Current approach | Proven transition | Impact |
|--------------|------------------|-------------------|--------|
| Frozen registry plus first-party-only skill staging | Composed installed-overlay registry threaded through layout and surface staging | Absent in tag `v1.6.0`; present in tag `v1.8.0` | Native surface application can refresh third-party skills. |
| Manifest-only ownership of projected directories | Declared owner binding plus `.gsd-capability-skill` marker | Present in tag `v1.8.0` | Current accepted capabilities are retained; orphaned marker-owned projections can be removed; unmarked user content is preserved. |
| One capability-only raw hash plus custom PID/start-time symlink recovery | Shared canonical `projection-v2` ledger under inherited Python stdlib `fcntl.flock`, securely published with `NamedTemporaryFile`/`os.replace` | Required by Phase 22 remediation | Runtime rows merge without loss; cooperating hooks serialize shared-generation mutation; crashes release ownership without takeover logic. |

**Deprecated/outdated:** `check-patch execute-plan` is retired and must not be restored. The stale global skill containing it is migration input, never compatibility authority. [VERIFIED: GitHub issue `davdittrich/gsd-beads#9`]

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Native materialization's wall-clock cost is acceptable for a one-time changed-generation SessionStart. No benchmark was run. | Alternatives Considered | SessionStart may be slower during upgrades; correctness is unaffected because unchanged generations retain the fast path. |

No architectural claim depends on A1; performance must be measured if a regression threshold is later specified.

## Open Questions (RESOLVED)

No implementation decision remains open. Use the exact shared ledger `${GSD_HOME:-$HOME}/.gsd/capability-auto-install-$CAP_ID.projections`, canonical rows `projection-v2 <runtime> <64-lowercase-hex-installed-generation> <64-lowercase-hex-selected-surface-fingerprint>`, and regular lock file `${LEDGER}.lock`. Sort rows by runtime and retain exactly one valid row per runtime. The first successful migration securely writes a same-directory `NamedTemporaryFile`, flushes and file-`fsync`s it, atomically calls `os.replace`, and only then removes an eligible regular non-symlink legacy `${GSD_HOME:-$HOME}/.gsd/capability-auto-install-$CAP_ID.hash`; failure preserves prior canonical and legacy state. Completion is valid only after the locked transaction's final installed-generation and observed-selected-fingerprint observation. Production never constructs an independent transformed-output oracle. [Phase 22 design decision; transformation verified at `git show v1.8.0:src/install-profiles.cts:596-603` and `git show v1.8.0:src/surface.cts:393-401`]

The user-approved evidence correction separates the minimum from the executable runtime. The `1.10.0` floor is proven by official tag `v1.10.0` resolving to immutable commit `68a04ccf8ef74803bdb651e12c3b85b218bbccdf` and that commit's `package.json` version being exactly `1.10.0`; no plan gate requires `runtime-identity --raw` to report the floor. The active/current integration separately requires `runtime-identity --raw` to prove `@opengsd/gsd-core` version `1.12.0`, then runs the real public skills-root, install/set, transformed-output, sibling, preservation, and command gates without skipping. Bias: NONE; provenance and live behavior remain independently fail-closed. [User-approved deviation]

The second user-approved correction makes Slice 7 verification-only/test-only because the corrected real-runtime test is already green against production delivered by Slices 1-6. The execution contract therefore retains six genuine audited RED/GREEN production pairs and forbids manufacturing a seventh RED, production delta, or production commit. The real-runtime oracle's separate absolute config root is a known comparison confound: normalize only a test-owned independent-oracle copy from oracle root to subject root, require every non-root difference to remain visible, and never normalize the subject projection, production selected fingerprint, installed/source data, or sibling/user/unselected controls. What does it bias? NONE; the correction preserves actual TDD provenance and removes only an independent-test-fixture path artifact. [User-approved deviation]

Lock ownership is resolved through Python stdlib `fcntl.flock`: open a no-follow regular lock file, verify descriptor/path identity, acquire `LOCK_EX | LOCK_NB` exactly once, mark the descriptor inheritable, and `exec` the same Bash hook in locked-child mode. The child revalidates and retains the descriptor across the entire observe/install/set/verify/publish transaction. `EACCES`/`EAGAIN` is busy and fails open immediately; every other unsafe-target or wrapper failure also fails open with one fixed line. Kernel descriptor lifetime releases ownership on normal exit, signal, or crash, so the design has no PID/process-start identity, stale quarantine, polling, sleep, or reacquire path. The guarantee is deliberately bounded to hook participants. Installed generation and observed selected fingerprint are sampled immediately before publication; a later non-cooperating write is detected and repaired by the next SessionStart rather than falsely claimed atomic. [User-approved remediation; Python `fcntl` contract; Confidence: 100/100]

All fail-open diagnostics are exactly one bounded stderr line and expose no path, subprocess output, task content, or secret. Use these literal templates and stage tokens:

| Failure | Exact diagnostic template |
|---------|---------------------------|
| Runtime cannot be selected | `capability-auto-install: runtime selection failed for <capability>; projection not recorded` |
| Runtime-bound CLI cannot be resolved | `capability-auto-install: gsd-tools resolution failed for <capability> on <runtime>; projection not recorded` |
| Install subprocess fails | `capability-auto-install: capability install failed for <capability> on <runtime>; projection not recorded` |
| Native skills root is unavailable or ambiguous | `capability-auto-install: skills-root query failed for <capability> on <runtime>; projection not recorded` |
| Destination is a symlink, non-directory, unmarked user directory, or owned by another capability | `capability-auto-install: destination ownership check failed for <capability> on <runtime>; projection not recorded` |
| Native materialization fails | `capability-auto-install: capability set failed for <capability> on <runtime>; projection not recorded` |
| Installed bundle differs from the source generation | `capability-auto-install: installed generation verification failed for <capability> on <runtime>; projection not recorded` |
| Owner marker, selected command contract, or selected-surface fingerprint is invalid | `capability-auto-install: selected projection verification failed for <capability> on <runtime>; projection not recorded` |
| A selected command is rejected or the retired command is accepted | `capability-auto-install: selected command contract verification failed for <capability> on <runtime>; projection not recorded` |
| Atomic ledger publication fails | `capability-auto-install: ledger publish failed for <capability> on <runtime>; projection not recorded` |
| A live hook transaction owns the lock | `capability-auto-install: projection transaction busy for <capability>; projection not recorded` |
| Lock target, inherited descriptor, or lock helper is unsafe/unavailable | `capability-auto-install: projection lock failed for <capability>; projection not recorded` |
| Any bounded Python/hash helper fails | Use the one existing stage-specific template above; never forward helper output or traceback. |

Substitute only validated lowercase capability/runtime tokens. Preserve the existing success notice and the SessionStart exit-zero boundary. Do not include raw subprocess stderr or exit status because neither changes the recovery action and both would make the diagnostic contract unstable. [Phase 22 design decision; security boundary verified in GitHub issue `davdittrich/gsd-beads#9` and `plugins/beads-lifecycle/hooks/session-start.sh:5-13`; Confidence: 98/100]

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Bash | Hook and smoke test | Yes | Existing runtime | None required |
| Python 3 stdlib | `sync.py`, `fcntl.flock` wrapper, and secure ledger publisher | Required | POSIX Python with `fcntl`, `tempfile`, and `os.replace` | Missing/unsafe lock support yields one bounded fail-open diagnostic and no projection work |
| gsd-core tags | Version comparison | Yes | `v1.6.0`, `v1.8.0`, `v1.10.0` at exact commits recorded below | None required |
| gsd-core floor provenance | Minimum compatibility proof | Yes | Official `v1.10.0` tag at immutable commit `68a04ccf8ef74803bdb651e12c3b85b218bbccdf`, with exact `package.json` version `1.10.0` | Hard-fail on tag SHA or package-version mismatch; do not ask an installed runtime to report the minimum |
| Active/current gsd-core | Real integration proof | Yes | `1.12.0` observed through `runtime-identity --raw` | Hard-require package `@opengsd/gsd-core` version `1.12.0`, then exercise real public `query skills-root`, install/set, transformation, sibling, preservation, and command boundaries without skipping |
| GitHub Actions runner | Clean public-runtime proof | CI | Checkout plus Node/npm | Pin gsd-core tag and npm package to `1.12.0`; assert official runtime identity before tests |

No new production package is introduced. Python's POSIX stdlib is already required; the hook fails open if `fcntl` is unavailable. CI alone installs the exact verified public gsd-core package into an isolated runner-temporary config root.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Existing stdlib Bash smoke harness plus real gsd-core CLI scratch integration |
| Config file | None |
| Quick run command | `TMPDIR=/dev/shm bash tests/test-capability-auto-install.sh` |
| Full suite command | `cd plugins/beads-lifecycle/.gsd/capabilities/beads && TMPDIR=/dev/shm PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t tests` |

### Phase Requirements -> Test Map

| Case | Behavior | Test seam | Required proof |
|------|----------|-----------|----------------|
| Legacy migration and secure publish | A raw capability-only hash cannot take the `projection-v2` fast path. | Public hook plus test-only `sitecustomize.py` spies | `NamedTemporaryFile` is created in the ledger directory; one same-directory `os.replace` publishes canonical state; injected replacement failure preserves canonical and legacy bytes; legacy cleanup occurs only after success. |
| Differing-version sequential update | Generation A has genuinely stale selected command content; current generation B converges to the current runtime projection. | Verified active/current 1.12.0 gsd-core CLI in isolated home | A and B selected fingerprints differ before reconciliation; raw B subject output equals the independent runtime-transformed oracle after oracle-only absolute-root normalization; stale target absent. This is test-only oracle construction. |
| Concurrent ledger | Same-runtime and cross-runtime cooperating hooks serialize the shared installed-generation transaction. | Public hook with controlled rendezvous | One inherited kernel lock covers the entire transaction; live contention returns immediately; canonical ledger retains valid completed rows without loss. No simultaneous cross-runtime projection is promised. |
| Kernel lock and crash release | Acquisition cannot expose partial owner metadata, and process termination cannot leave a stale owner. | Public hook with inherited-fd and deterministic barrier fixtures | Exactly one `LOCK_EX | LOCK_NB` acquisition; half-published-owner state is structurally impossible; child termination releases the lock; following invocation acquires without recovery, polling, or sleep. |
| Unsafe filesystem targets | Lock, marker, or canonical ledger path is a symlink or nonregular object. | Public hook with adversarial isolated paths | No native install/set or replacement; target bytes remain unchanged; one bounded fixed diagnostic; no raw helper output. |
| Non-cooperating external writer | Direct mutation may occur before or after the final observable gate. | Public hook plus `os.replace` barrier shim | Pre-observation drift prevents publication; post-observation drift is not claimed atomic and forces next-start mismatch, native reconciliation, and corrected receipt. |
| True installed second capability | Native surface includes another accepted capability during Beads repair. | Verified active/current 1.12.0 gsd-core CLI with two installed fixture capabilities | Second capability's selected skill equals its independently generated runtime-transformed expected output after oracle-only absolute-root normalization, on both first and repeated runs. This is test-only oracle construction. |
| Independent-oracle absolute root | Subject and oracle require different absolute config roots to avoid cross-mutation, and native rewriting may embed that root. | Test-owned independent-oracle copy | Replace only the oracle root with the subject root before comparison; every non-root mismatch fails; raw subject, production fingerprint, installed/source data, and preservation controls remain unnormalized. |
| User-owned preservation | Unmarked `gsd-*`, non-GSD skill, unrelated file, and other runtime root remain unchanged. | Pre/post complete-tree hashes | Byte-identical sentinels and trees; no prefix-only deletion. |
| Retired command | `execute-plan` is not reintroduced. | Selected skill text plus parser test | No selected declaration contains `execute-plan`; active CLI rejects it. |
| Selected CLI | Every command declared by the selected Beads skill is accepted by the installed `sync.py`. | Extract declarations, invoke parser with `--help` | Every declared target exits successfully at the parser boundary; no undeclared compatibility alias. |
| Idempotence | Second identical run is silent and byte-stable. | Public hook plus complete-tree/ledger hashes | Exact installed-generation/selected-fingerprint row yields zero install/materialize calls; selected tree and canonical ledger remain byte-identical. |
| Failure ordering | Lock/helper, install, materialize, contract, final observation, or ledger publication failure never certifies completion. | Stub status matrix plus Python call spies | One fixed bounded warning names the stage; raw stderr/traceback is absent; hook remains fail-open; prior ledger and legacy state are unchanged. |
| Engine floor | v1.8.0 is rejected because it lacks the complete Codex destination/query contract. | Manifest engine-gate integration or exact tag fixture | Nonzero/blocked install names engine incompatibility; no projected state mutation. |
| Clean CI runtime | Repository checkout does not rely on a developer's adjacent gsd-core checkout or home install. | GitHub Actions workflow | Official gsd-core `v1.12.0` checkout and exact public npm provision occur first; `runtime-identity --raw` proves name/version; `GSD_CORE_REPO` is exported before the hook suite. |

### Confound Controls

- Sequential before/after arms differ only in bundled/installed generation, and generation A changes selected command content rather than version metadata alone.
- Each failure arm changes one subprocess result from the known-good baseline.
- The second-capability arm uses a genuinely installed, registry-accepted bundle; a loose marker directory is not evidence.
- Cross-runtime preservation records complete pre/post hashes and does not run materialization against the non-target runtime.
- Concurrent tests coordinate with a blocking stub/event seam and bounded shell process waits, not polling loops or arbitrary sleeps. They vary only holder lifetime/contention, prove the inherited `flock` has no owner-publication window, and show kernel release after termination.
- Secure-publication tests inject only the `NamedTemporaryFile`/`os.replace` observation or failure through a test-owned `sitecustomize.py`, delegate every non-injected call, and compare exact canonical/legacy bytes before and after.
- External-writer tests separate drift before final observation from drift after it; only the latter expects publication followed by mandatory next-SessionStart invalidation and repair.
- The subject and independent oracle use distinct absolute config roots so neither native materialization mutates the other's state. Runtime rewriting may therefore embed different roots in otherwise equivalent output.
- Normalize only a test-owned copy of the independent oracle by replacing its absolute oracle root with the subject root immediately before comparison. Require every non-root mismatch to remain observable. Never normalize the raw subject projection, production selected-surface fingerprint, installed/source bundle, sibling capability, same-name user tree, unrelated tree, or unselected runtime.

### Sampling Rate

- **Historical baseline:** retain the six genuine Slice 1-6 production RED/GREEN pairs and the already-green verification-only Slice 7 transcript; do not relabel either as remediation work.
- **Per remediation pair:** the existing harness has no selector. Run exact command `cd /home/dd/projects/gsd-beads && TMPDIR=/dev/shm bash tests/test-capability-auto-install.sh` for each R1, R2, and R3 RED and GREEN; each test-only RED commit precedes its minimal GREEN fix, and each whole-harness GREEN reruns prior slices.
- **Per wave merge:** focused hook suite plus full capability unittest suite.
- **Slice 7 verification gate:** run the already-corrected real-runtime test last and retain its green transcript; create no RED, production change, or production commit.
- **Phase gate:** both suites green; official v1.10.0 provenance matches immutable commit `68a04ccf8ef74803bdb651e12c3b85b218bbccdf` and exact package version `1.10.0`; CI provisions and identifies public `@opengsd/gsd-core` `1.12.0` before the suite; the real fixture proves genuinely stale A selected content, independent runtime-transformed output after oracle-only root normalization, sibling/user preservation, command gates, idempotence, secure publication, and three new RED/GREEN remediation pairs.

### Wave 0 Gaps

- R1 adds failing public regressions for inherited nonblocking `flock`, live contention, crash release, unsafe lock targets, acquisition-window impossibility, and bounded helper diagnostics before deleting the PID/symlink protocol.
- R2 adds failing marker-symlink, secure `NamedTemporaryFile`/`os.replace`, nonregular target, legacy ordering, and two-phase external-writer recovery regressions before changing publication and ownership code.
- R3 adds failing genuine-stale-generation and clean-CI-input regressions before parameterizing the fixture and provisioning pinned public gsd-core v1.12.0 in CI.
- Historical Slices 1-6 remain six production RED/GREEN pairs. Historical Slice 7 remains verification-only/test-only and may normalize only its independent oracle copy's absolute config root; neither is a substitute for R1-R3.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard control |
|---------------|---------|------------------|
| V2 Authentication | No | No authentication boundary exists. |
| V3 Session Management | No | SessionStart is a local hook, not an authenticated session store. |
| V4 Access Control | Yes | Declared capability ownership and selected-runtime confinement control which generated directories may change. |
| V5 Input Validation | Yes | Validate capability id and runtime tokens before path construction; gsd-core binds skill stems to accepted registry owners and confines paths. [VERIFIED: current hook `plugins/beads-lifecycle/hooks/capability-auto-install.sh:11-20`; `git show v1.8.0:src/install-profiles.cts:490-496,605-625`] |
| V6 Cryptography | No | SHA-256 here detects generation drift; it is not an authentication control. Use existing system tools, not custom cryptography. |

### Known Threat Patterns

| Pattern | STRIDE | Standard mitigation |
|---------|--------|---------------------|
| Prefix-based deletion removes user data | Tampering / denial of service | Native marker and registry ownership; preserve unmarked entries. |
| Undeclared sibling skill hijacks another capability's stem | Spoofing / tampering | Resolve the declaring owner through `capabilityClusters`, then read only that capability directory. [VERIFIED: `git show v1.8.0:src/install-profiles.cts:499-625`] |
| Runtime confusion mutates another host's surface | Tampering | Explicit selected runtime/config root and one runtime row in the shared canonical ledger. |
| Torn, lost, premature, or path-substituted ledger suppresses repair | Tampering / denial of service | Inherited kernel lock, nonregular-target rejection, secure same-directory temporary, atomic `os.replace`, and legacy cleanup only after canonical success. |
| Symlinked ownership marker redirects trust | Spoofing / tampering | Require marker to be a regular non-symlink with exact owner content before native install/set. |
| Direct writer races after final observation | Tampering | Make no atomic-exclusion claim; the next SessionStart recomputes generation/fingerprint and repairs a mismatched row. |

## Sources

### Primary (HIGH confidence)

- gsd-core tag `v1.6.0`, commit `7cbd26682dc0ce464dc3e2ce56589ce3d0a6aa13` — first-party-only writer, stager, and conservative prune behavior.
- gsd-core tag `v1.8.0`, commit `e4df05126deaf5ad1c29bf35b9dfe2193c80cb0b` — composed-registry writer, declared-owner third-party staging, marker ownership, and retention/prune behavior.
- gsd-core tag `v1.10.0`, commit `68a04ccf8ef74803bdb651e12c3b85b218bbccdf`, whose `package.json` declares `1.10.0` — immutable compatibility-floor provenance for the corrected runtime destination plus shipped `gsd-tools query skills-root` boundary.
- Active/current gsd-core `runtime-identity --raw` — package `@opengsd/gsd-core`, version `1.12.0`; executable public integration boundary.
- `plugins/beads-lifecycle/hooks/capability-auto-install.sh` — current native projection/receipt baseline plus the reviewed custom-lock, predictable-publication, legacy-order, marker-type, external-writer, and diagnostic remediation points.
- `tests/test-capability-auto-install.sh` — current public hook and real-runtime seams; historical 24-case baseline requiring R1-R3 regressions.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` — current engine floor `">=1.10.0"` and skill declarations.
- Python [`fcntl.flock`](https://docs.python.org/3/library/fcntl.html) — `LOCK_EX | LOCK_NB` advisory locking and contention error contract; descriptor lifetime supplies crash release.
- Python [`tempfile.NamedTemporaryFile`](https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile) — securely created visible named temporary file contract.
- Python [`os.replace`](https://docs.python.org/3/library/os.html#os.replace) — same-filesystem atomic replacement contract on POSIX.
- npm [`install`](https://docs.npmjs.com/cli/install/) — exact published package-version syntax used for CI-only `@opengsd/gsd-core@1.12.0` provisioning.
- GitHub [Building and testing Node.js](https://docs.github.com/en/actions/tutorials/build-and-test-code/nodejs) — clean runner checkout/setup/install sequencing.
- `.github/workflows/ci.yml` — required pinned public-runtime provision and identity gate before the hook test.
- GitHub issue [davdittrich/gsd-beads#9](https://github.com/davdittrich/gsd-beads/issues/9) — observed mixed-version failure and authoritative acceptance/out-of-scope contract.

### Secondary (MEDIUM confidence)

- [gsd-core Capability Command Reference](https://github.com/open-gsd/gsd-core/blob/next/docs/reference/gsd-capability-command.md) — public `capability set --runtime --scope` materialization contract. Current source supersedes its stale statement that `set` is first-party-only.
- [gsd-core Capability Overlay Model](https://github.com/open-gsd/gsd-core/blob/next/docs/explanation/capability-overlay-model.md) — install, compose, surface, and config activation layers.

## Metadata

**Confidence breakdown:**

- Version boundary: HIGH — exact v1.8.0/v1.10.0 tagged-source comparison, immutable v1.10.0 SHA/package metadata, and distinct active/current 1.12.0 runtime identity.
- Native preservation semantics: HIGH — complete owner/stage/retain/prune call path read at v1.8.0.
- Ledger migration and hook-participant serialization: HIGH for correctness; MEDIUM for performance because no timing benchmark was run.
- Runtime boundary: HIGH for the prohibition and observed roots; receipt spelling and exact diagnostic templates are resolved above.

**Research date:** 2026-09-02
**Valid until:** 2026-10-02 for the pinned tag comparison; re-verify active gsd-core and plugin runtime paths immediately before execution.
