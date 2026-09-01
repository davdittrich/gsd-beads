# Phase 21: Installed Cutover and Patch 2 Retirement - Research

**Researched:** 2026-09-01 [VERIFIED: `date`, 2026-09-01]
**Domain:** Installed GSD capability cutover, live Beads task resolution, and bounded machine-local patch retirement.
**Confidence:** HIGH for the locked scope and tracked seams; MEDIUM for external operational guidance.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Cutover transaction

- **D-01:** Treat cutover as one fresh fail-closed transaction at one exact
  source SHA. Runtime paths, active registry state, installed bytes, live Beads
  discovery, the public positive proof, and every negative arm must be observed
  immediately before retirement. Evidence from earlier runs is context, never a
  gate result.
- **D-02:** Resolve tracked, project-installed, and global-installed bundle
  paths from the current runtime and installer output. Do not hard-code a
  Claude, Codex, plugin-cache, or `$HOME/.gsd` location. Compare the complete
  bundle trees, not only `capability.json`; require byte identity and no
  source-only or install-only paths.
- **D-03:** The public positive proof must run outside repository ancestry so a
  project overlay cannot satisfy a claim about the global install. Pass the
  absolute real plan path and bind the supported live Beads database locator;
  require the active registry to name the runtime-derived global bundle. Do not
  copy, import, or replay Beads data.
- **D-04:** Gate order is binding: complete bundle parity and active-registry
  proof; live database discovery; public positive resolution; isolated public
  negative matrix; only then Patch 2 removal; then repeat native positive proof,
  the negative matrix, complete capability tests, and Patch 1 verification.
- **D-05:** Any pre-removal failure emits `SPEC_FAILURE` and leaves Patch 2
  installed. Before changing a machine-local workflow, capture its exact bytes
  in the session scratchpad. If a post-removal check fails, restore only those
  exact bytes and halt with `SPEC_FAILURE`; do not improvise a fallback. —
  **Reversibility:** costly — the live workflow is shared across projects, so a
  failed cutover must not propagate a partially retired read path.

### Live proof task

- **D-06:** Use the first exact `auto` or `tracer` task that Phase 21's normal
  `plan:post` Beads sync creates or resolves. Before proof, require its plan
  block to contain both exact `tracker-id="beads:<id>"` and `<beads-id><id>`
  identities and require `bd show <id> --json` to return the same live row.
- **D-07:** Do not use a synthetic task. Do not use the current Phase 20 plan as
  proof: direct live inspection found no persisted native identity in its task
  opening tags. The Phase 21 task is naturally accumulated workflow data and
  exercises the code that will actually ship.
- **D-08:** The proof succeeds only when the public command reports resolved
  content containing the live task's authored fields. Direct adapter output,
  parser-only success, unit mocks, or a project-overlay resolution are
  supporting evidence, not CUT-01 completion.

### Negative-path matrix

- **D-09:** Before retirement, require four public-boundary arms: unknown native
  task id; a real legacy `<beads-id>`-only plan task; unavailable/failing `bd`;
  and malformed resolver stdout. The existing Phase 19 suite remains
  responsible for missing script, timeout, ambiguous envelope, wrong field
  type, duplicate heading, and unusable-content branches; do not duplicate its
  whole matrix in Phase 21.
- **D-10:** Each negative arm changes exactly one factor from the known-good
  installed baseline. Use bounded outside-ancestry scratch, keep the live
  database and live install read-only, and assert nonzero exit, no resolved
  object, and no fallback task content. A combined multi-fault fixture, skip,
  xfail, warning-only result, or environment dismissal is not evidence.
- **D-11:** Spy exact internal `bd` argv in focused adapter tests and test the
  external contract through `task resolve-content`. Internal spies prove how;
  the public command proves what.

### Patch 2 retirement and history

- **D-12:** Delete every active Patch 2 surface: installed marker-bracketed
  workflow blocks; marker constant; `PATCH_CHECKS["execute-plan"]` entry;
  wrapper and call sites; CLI target; installer or detector invocation;
  Patch-2-specific tests; and active operational documentation. Add no alias,
  inert marker, tombstone command, compatibility branch, or new cutover
  framework.
- **D-13:** Preserve historical truth in `CHANGELOG.md`, archived planning
  artifacts, Beads records, and Git history, and add the current retirement
  entry. Historical statements remain historical; active instructions must no
  longer tell operators to install, check, or restore Patch 2.
- **D-14:** Patch 1 is outside the deletion set. Preserve its marker, live
  workflow block, checker behavior, tests, documentation, and installer wiring
  byte-for-byte unless a mechanically inseparable call-site deletion is
  required. Do not collapse or redesign the surviving one-entry checker table;
  adjacent cleanup is not part of cutover.
- **D-15:** Keep code, tests, and operational documentation in the same task and
  commit. Do not create a standalone documentation work unit or a reusable
  migration utility.

### the agent's Discretion

The user delegated all four areas to Ponytail, scientific-critical-thinking,
Beads, and codebase-design. The planner may choose exact test names, diagnostic
wording, the deterministic whole-tree comparison command, and the supported
runtime-derived database locator. It may not weaken the fresh-evidence order,
use synthetic task data, let the project overlay prove the global install,
combine negative variables, retain active Patch 2 residue, or alter Patch 1.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 21 scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CUT-01 | The installed capability resolves a real task from live Beads through gsd-core's public `task resolve-content` command, with source, project-installed, and global-installed capability bytes proven identical. | The public router, resolver declaration, current registry, installer drift seam, and natural `plan:post` source are identified below. [VERIFIED: `.planning/REQUIREMENTS.md:39-41`; `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92-155`] |
| CUT-02 | Patch 2 and all of its checker, marker, installer, and documentation wiring are removed only after CUT-01 and the isolated negative-path checks pass; Patch 1 remains installed and independently verified. | The exact Patch 2 deletion inventory and independent Patch 1 surface are identified below. [VERIFIED: `.planning/REQUIREMENTS.md:42-45`; `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md:188-195`] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Use CodeGraph/Serena before manual source reads; use Serena for refactors and edits. [VERIFIED: `AGENTS.md`, supplied session instructions]
- Use GSD lifecycle and Beads tickets for every planning/execution task; one Beads ticket per plan task. [VERIFIED: `AGENTS.md`, supplied session instructions]
- Preserve evidence discipline: read target source, trace callers before changes, use public-boundary tests plus internal spies, and attach confidence. [VERIFIED: `AGENTS.md`, supplied session instructions]
- Research current best practice before planning; include at least two alternatives and rank the selected mechanism by performance, simplicity/LOC, ecosystem support, and maintenance. [VERIFIED: `AGENTS.md`, supplied session instructions]
- Never use a fallback or workaround after mechanism failure; emit `SPEC_FAILURE`, keep scope minimal, and do not alter Patch 1. [VERIFIED: `AGENTS.md`, supplied session instructions]
- Use bounded outside-ancestry session scratch for real `bd` work; do not use repository-ancestry scratch. [VERIFIED: `.wolf/cerebrum.md:14-15`]
- Do not commit or push as part of this research without explicit authority. [VERIFIED: `AGENTS.md`, supplied session instructions]

## Summary

Phase 21 is an evidence-gated deletion, not a new integration. The tracked source already declares a `beads` resolver whose exact invocation uses `python3`, a separate `"{{id}}"` argv element, and a `10000` ms timeout; its adapter performs `bd show <id> --json` with a typed argv and returns a single JSON object. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:5-11`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:676-782`]

The current registry is deliberately insufficient for CUT-01: live output shows global `beads` version `0.4.0` from a plugin cache and project `beads` version `0.5.0` from the tracked bundle. Therefore a planner must make parity and active-global-registry proof the first gate, rather than treating the working project overlay as proof. [VERIFIED: `gsd-tools capability list --raw`, observed 2026-09-01]

Patch 2 remains a distinct machine-local `execute-plan.md` marker path. Its current retirement boundary is already enumerated in the operational document: workflow marker block, Patch-2 section, marker constant, checker-table entry/wrapper/CLI, and `beads-recall` invocation. Patch 1 is the independent `ship-md` row and must remain exactly one entry. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md:188-195`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:145-201`]

**Primary recommendation:** Use one existing-seam transaction—runtime-derived bundle parity plus a naturally synced Phase 21 task through the public command, then the four isolated failures, then the smallest deletion of Patch 2 surfaces and re-run the same proof matrix. [VERIFIED: `21-CONTEXT.md`, D-01 through D-15]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Resolve authored task content | GSD CLI / frontend server | Database / storage | The public router locates the exact plan task and selects an installed resolver; Beads remains the live data authority. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:103-155`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:676-782`] |
| Discover the capability implementation | GSD runtime registry | Static bundle storage | `loadRegistry({ includeInstalled: true, cwd })` supplies the merged installed overlay to the router. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:65-74`] |
| Prove installed cutover | GSD CLI / frontend server | Filesystem / storage | The public command is the oracle; complete bundle-tree comparison and active-registry evidence eliminate project-overlay and drift confounds. [VERIFIED: `21-CONTEXT.md`, D-02 through D-04] |
| Retire Patch 2 | Machine-local workflow storage | Capability adapter | The marker lives in `execute-plan.md`; the tracked checker/documentation call sites must be deleted in the same transaction. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md:188-195`] |
| Preserve Patch 1 | Machine-local workflow storage | Capability adapter | The surviving `ship-md` entry has a separate marker and checker target. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:145-179`] |

## Standard Stack

### Core

| Library / tool | Observed version | Purpose | Why standard |
|----------------|------------------|---------|--------------|
| Installed gsd-core | `1.12.0` [VERIFIED: `gsd-tools capability list --raw`, observed 2026-09-01] | Owns public `task resolve-content`, registry loading, resolver execution, timeout, and hard-stop result handling. | It is the shipped public seam; adding another command would duplicate selection and error policy. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92-155`] |
| Beads CLI | `1.2.2` [VERIFIED: `bd --version`, observed 2026-09-01] | Reads the one live issue via `bd show <id> --json`. | The official Beads docs identify `bd show <id> --json` as a programmatic read path. [CITED: https://github.com/gastownhall/beads/blob/main/docs/index.md] |
| Python standard library | `3.14.7` [VERIFIED: `python3 --version`, observed 2026-09-01] | Runs the existing adapter/bootstrap; no dependency is added. | The existing manifest and adapter already use it. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:5-11`] |

### Supporting

| Tool | Purpose | When to use |
|------|---------|-------------|
| `capability-auto-install.sh` | Existing runtime-derived global installation and whole-bundle drift hash. | Use it or its existing installer output to derive paths; do not create an installation framework. [VERIFIED: `plugins/beads-lifecycle/hooks/capability-auto-install.sh:18-97`] |
| `python3 -m unittest discover -s tests -t tests` | Existing dependency-free full capability suite. | Run before and after retirement; CI uses exactly this command. [VERIFIED: `.github/workflows/ci.yml:36-40`] |

### Alternatives Considered

| Instead of | Could use | Tradeoff and decision date |
|------------|-----------|----------------------------|
| Existing native resolver cutover | Retain Patch 2 as a fallback | Rejected 2026-09-01: fallback can satisfy the read path and make CUT-01 unfalsifiable. [VERIFIED: `21-CONTEXT.md`, D-08, D-12 and Specific Ideas] |
| Prove then remove | Remove Patch 2 first | Rejected 2026-09-01: failure would leave pointer-only tasks unreadable and violates the binding gate order. [VERIFIED: `21-CONTEXT.md`, D-04-D05] |
| Existing commands and focused tests | Reusable generic cutover harness | Rejected 2026-09-01: it adds framework surface although existing public command, registry listing, installer, and test seams already cover the proof. [VERIFIED: `21-CONTEXT.md`, D-12 and Specific Ideas] |

**Ranked recommendation:** (1) performance—one existing resolver subprocess and no extra framework; (2) simplicity/LOC—reuse the router, installer, and test module; (3) ecosystem—use GSD's documented feature resolver contract and Beads' documented JSON CLI; (4) maintenance—delete the duplicate workflow path while retaining the independently needed Patch 1. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs:237-261`; [CITED: https://github.com/open-gsd/gsd-core/blob/next/docs/reference/capability-manifest.md]; [CITED: https://github.com/gastownhall/beads/blob/main/docs/index.md]]

**Installation:** No external package installation belongs in Phase 21. [VERIFIED: `21-CONTEXT.md`, D-12 and D-15]

## Architecture Patterns

### System Architecture Diagram

```text
tracked capability bundle ──install/derive paths──> project + global bundles
          │                                             │
          └──complete-tree byte comparison──────────────┘
                                                        │
normal Phase 21 plan:post ──> live bd issue + both IDs ─┼──> active global registry proof
                                                        │
outside-repo-parent public command ──> gsd router ──> beads resolver ──> bd show --json
                                                        │                    │
                                                        └──── resolved authored fields <────┘
                                                                  │
four isolated public failures <──── known-good baseline ─────────┤
                                                                  │
                                                    delete Patch 2 only after all pass
                                                                  │
                                 repeat positive + negative + suite + Patch 1 preservation
```

The public router resolves the supplied plan path relative to its working directory and rejects a path outside that directory. Therefore the global-only proof must use a runtime-derived directory that is outside the repository tree but still contains the absolute real plan path (for example, a parent directory); if no such containment-preserving location can be derived, halt before retirement. This is an inference from the router's containment check, not a permission to copy the plan. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:103-129`; `21-CONTEXT.md`, D-03]

### Recommended Project Structure

Do not add a new module or project structure. Extend only the tracked seams below, and delete only Patch-2-owned code/documentation after the D-04 proof gate. [VERIFIED: `21-CONTEXT.md`, D-12-D15]

| Responsibility | Existing seam | Planned action |
|----------------|---------------|----------------|
| Live resolver and public proof | `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` and `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs` | Preserve resolver; add focused cutover probes/tests around its public contract. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:676-782`; `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92-155`] |
| Manifest and bundle parity | `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`, `plugins/beads-lifecycle/hooks/capability-auto-install.sh` | Derive every runtime location; compare full trees; retain installer behavior. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:1-35`; `plugins/beads-lifecycle/hooks/capability-auto-install.sh:31-97`] |
| Patch 2 retirement | `sync.py`, `GSD-CORE-PATCH.md`, `skills/beads-recall/SKILL.md`, active workflow | Delete exact Patch 2 surfaces, no alias/tombstone. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md:188-195`] |
| Patch 1 regression gate | `sync.py` `ship-md` table entry and status path | Preserve and independently run after deletion. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:157-179`; `21-CONTEXT.md`, D-14] |

### Pattern 1: Public oracle plus internal argv spy

**What:** Use `task resolve-content` for CUT-01/CUT-02 behavior; retain focused `run_bd` spies to prove the adapter calls exactly `bd show <id> --json`.

**When to use:** Every positive/negative proof; unit tests isolate adapter mechanics, while the live cutover uses the public command. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1230-1307`; `21-CONTEXT.md`, D-08-D11]

**Code example:** The static tokens below are verbatim from the source-of-truth manifest; dynamic values are runtime-derived.

DATA_7KQ2M9VX_START
```json
"trackerPrefix": "beads"
"binary": "python3"
"timeoutMs": 10000
```
DATA_7KQ2M9VX_END

```bash
gsd_run task resolve-content --plan "$REAL_PLAN" --task-id "beads:$BEADS_ID" --raw
```

The command spelling and exact public arguments are verified in the router, while `beads`, `python3`, and `10000` are the exact declared values above. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:5-11`; `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92-105`]

### Pattern 2: One-variable fail-closed experiment

Start from the known-good installed baseline, mutate exactly one factor per arm, and assert nonzero exit, no resolved object, and no fallback task content. Treat project-overlay resolution, adapter-only output, warnings, skips, and xfails as invalid evidence. [VERIFIED: `21-CONTEXT.md`, D-09-D11]

### Anti-Patterns to Avoid

- **Project-tree proof of a global capability:** the loader uses `cwd` when building the installed registry, so the project overlay can shadow the global bundle. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:72-74`; `gsd-tools capability list --raw`, observed 2026-09-01]
- **Marker-only parity:** checking only `capability.json` misses source-only/install-only files; compare complete trees. [VERIFIED: `21-CONTEXT.md`, D-02]
- **Combined fault fixture:** it cannot attribute a failure to an individual control. [VERIFIED: `21-CONTEXT.md`, D-10]
- **Generic cutover abstraction:** no second installer, cache, retry, compatibility branch, alias, or tombstone. [VERIFIED: `21-CONTEXT.md`, D-12 and D-15]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Capability selection | A registry/parser in the Beads capability | `gsd_run task resolve-content` and installed gsd-core registry loader | Router already performs exact task lookup, loads installed capabilities, and maps resolver failures to nonzero CLI errors. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:103-155`] |
| Bundle installation | A migration/install framework | Existing `capability-auto-install.sh` / capability installer output | It already derives the bundle root, hashes the whole directory, and calls global-scope install. [VERIFIED: `plugins/beads-lifecycle/hooks/capability-auto-install.sh:18-97`] |
| Beads read parsing | A new database or JSONL reader | Existing adapter's `bd show <id> --json` typed argv path | Beads documents JSON CLI use; adapter already validates envelope/id and keeps stdout protocol-clean. [CITED: https://github.com/gastownhall/beads/blob/main/docs/index.md]; [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:676-782`] |
| Patch retirement compatibility | Alias, inert marker, fallback path | Complete deletion after gates | Any retained active Patch 2 surface masks the replacement and violates CUT-02. [VERIFIED: `21-CONTEXT.md`, D-12] |

**Key insight:** this phase earns confidence by observing independent existing seams, not by adding a coordinating mechanism. [VERIFIED: `21-CONTEXT.md`, Specific Ideas]

## Common Pitfalls

### Pitfall 1: Overlay shadowing

**What goes wrong:** a project-scoped bundle provides success while the global bundle is stale. **Why:** router registry loading receives `cwd`, and current registry output contains both global `0.4.0` and project `0.5.0` Beads entries. **How to avoid:** prove the active registry source from a non-overlay working location before the public proof. **Warning sign:** registry output names a project source or different versions. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:72-74`; `gsd-tools capability list --raw`, observed 2026-09-01]

### Pitfall 2: Breaking the router's plan containment rule

**What goes wrong:** an outside-ancestry CWD makes the real plan appear outside scope and the command fails before resolver selection. **Why:** the router rejects `relative(projectRoot, resolvedPlanPath)` beginning with `..`. **How to avoid:** derive a non-overlay parent that still contains the real absolute plan path; do not copy/replay the plan. **Warning sign:** `Plan file is outside project scope`. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:110-126`; `21-CONTEXT.md`, D-03]

### Pitfall 3: Treating an old gate result as fresh evidence

**What goes wrong:** a successful Phase 19/20 test or a prior install is used to authorize deletion. **Why:** source, runtime registry, global bytes, Beads DB, and workflow bytes may have changed. **How to avoid:** run D-04 in one exact-SHA transaction, capturing workflow bytes first. **Warning sign:** timestamps or SHA differ across proof artifacts. [VERIFIED: `21-CONTEXT.md`, D-01, D-04, D-05]

### Pitfall 4: Partial Patch 2 deletion

**What goes wrong:** `execute-plan` stays in `PATCH_CHECKS`, a wrapper/call site remains, or documentation continues to instruct reapplication. **Why:** the retirement inventory spans source, skills, docs, and a machine-local workflow. **How to avoid:** use the documented four-artifact inventory plus D-12's broader active-surface sweep, then search for all marker/checker tokens. **Warning sign:** any active `execute-plan` Patch-2 detector or marker remains. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md:188-195`; `21-CONTEXT.md`, D-12-D14]

### Pitfall 5: Destroying the surviving Patch 1 seam

**What goes wrong:** simplifying the table removes or changes the `ship-md` entry while deleting `execute-plan`. **Why:** both entries currently share a small fixed dictionary. **How to avoid:** retain the `ship-md` marker, version, path, checker, and test behavior byte-for-byte except for mechanically inseparable deletion. **Warning sign:** Patch 1 check no longer reports its existing marker. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:145-179`; `21-CONTEXT.md`, D-14]

## State of the Art

| Old approach | Current approach | When changed | Impact |
|--------------|------------------|--------------|--------|
| Machine-local Patch 2 reads task content from `execute-plan.md`. | Native `taskContentResolver` is declared by the Beads feature manifest and invoked by gsd-core's public router. | Tracked manifest currently `0.5.0`; current docs fetched 2026-09-01. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:1-11`; [CITED: https://github.com/open-gsd/gsd-core/blob/next/docs/reference/capability-manifest.md]] | The public command can be directly falsified; Patch 2 becomes removable only after installed proof. [VERIFIED: `21-CONTEXT.md`, D-04-D12] |

**External operational guidance:** NIST guidance supports retaining prior bytes for rollback/recovery and preserving release/configuration metadata; Phase 21 applies that narrowly as exact byte capture, full-tree parity, registry evidence, and restore-on-post-removal-failure. [CITED: https://nvlpubs.nist.gov/nistpubs/ir/2018/NIST.IR.8011-3.pdf]; [CITED: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204D.pdf]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A parent directory outside the repository tree can be used as the non-overlay CWD while still satisfying the router's absolute-plan containment check. | Architecture Patterns / Pitfall 2 | The public positive proof cannot run as designed; halt `SPEC_FAILURE` before retirement. [ASSUMED] |
| A2 | A focused installed-cutover test can be added in the existing `test_sync.py` module without a new test framework. | Validation Architecture | Test plan must change, but no product mechanism changes. [ASSUMED] |

## Open Questions (RESOLVED)

1. **Global-only containment root — resolved by an execution-time ancestor walk.**
   - Start from the real absolute `21-01-PLAN.md`, walk its ancestors nearest-first, and reject the repository root and every descendant of it. At each remaining ancestor, run the current public `gsd_run capability list --raw`; accept the first candidate only when the registry contains exactly one active global `beads` capability, contains no active project `beads` capability, the selected global manifest declares exactly one `taskContentResolver`, and the real plan remains contained beneath that candidate according to the router's `path.relative` containment rule. The public positive from that CWD is the final router-containment proof. [VERIFIED: `/home/dd/projects/gsd-core/src/task-command-router.cts:107-129`; `/home/dd/projects/gsd-core/src/task-content-resolution.cts:391-412`; `21-CONTEXT.md`, D-01-D03]
   - If no ancestor satisfies every condition, emit `SPEC_FAILURE` before source, Beads, installation, or workflow mutation. No fixed parent path or project-root fallback is permitted. [VERIFIED: `21-CONTEXT.md`, D-03-D05]

2. **Live Beads locator — resolved through the supported read-only CLI.**
   - Run `bd where --json`, require its `path` field to be one unambiguous current absolute directory, and bind execution-local `BEADS_DIR` to that exact path. Then require `BEADS_DIR="$BEADS_DIR" bd --readonly show "$ID" --json` to return exactly one row whose `id` equals the natural Phase 21 Beads id. [VERIFIED: `bd where --help`; `bd show --help`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:676-703`, observed 2026-09-01]
   - Missing/ambiguous paths, a missing or mismatched row, or any need to copy/import/replay data emits `SPEC_FAILURE` before source, installation, Beads, or workflow mutation. [VERIFIED: `21-CONTEXT.md`, D-03-D07]

3. **Beads recall status — resolved during planning.**
   - The normal `plan:pre` recall completed on 2026-09-01 and wrote `21-BEADS-RECALL.md`: 2 matched issues and 5 unscoped issues from 7 open issues total. [VERIFIED: `21-BEADS-RECALL.md`, generated 2026-09-01]
   - Planner action: consume the current recall, especially matched issue `gsd-beads-xy2`; do not infer scope from titles or drop the unscoped set. [VERIFIED: `21-BEADS-RECALL.md`; `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:52-61`]

## Environment Availability

| Dependency | Required By | Available | Version / observed state | Fallback |
|------------|-------------|-----------|--------------------------|----------|
| Node.js | gsd-core public command | ✓ | `v26.8.1` [VERIFIED: `node --version`, observed 2026-09-01] | — |
| Python | Existing resolver adapter/tests | ✓ | `3.14.7` [VERIFIED: `python3 --version`, observed 2026-09-01] | — |
| `bd` | Live Beads proof | ✓ | `1.2.2` [VERIFIED: `bd --version`, observed 2026-09-01] | No fallback; failure is a negative arm / `SPEC_FAILURE` pre-removal. [VERIFIED: `21-CONTEXT.md`, D-05, D-09] |
| Current global Beads bundle | CUT-01 parity | ✗ | Active global `0.4.0`, project `0.5.0`; parity is not currently established. [VERIFIED: `gsd-tools capability list --raw`, observed 2026-09-01] | Install from the runtime-derived tracked bundle through the existing installer, then prove complete-tree identity. [VERIFIED: `plugins/beads-lifecycle/hooks/capability-auto-install.sh:78-97`; `21-CONTEXT.md`, D-02] |

**Missing dependencies with no fallback:** none; a failed live `bd` is a required negative proof arm and blocks retirement, not a condition to bypass. [VERIFIED: `21-CONTEXT.md`, D-05 and D-09]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python standard-library `unittest`. [VERIFIED: `.github/workflows/ci.yml:36-40`] |
| Config file | none. [VERIFIED: `.github/workflows/ci.yml:36-40`] |
| Quick run command | `python3 -m unittest discover -s tests -t tests` from `plugins/beads-lifecycle/.gsd/capabilities/beads`. [VERIFIED: `.github/workflows/ci.yml:36-40`] |
| Full suite command | Same command; it is the CI capability suite. [VERIFIED: `.github/workflows/ci.yml:36-40`] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CUT-01 | Full-tree parity, active global registry, natural Phase 21 task with both identities, then public resolved content containing authored fields. | Fresh live public integration plus existing exact-argv spy. | Task 1's self-contained bounded `/dev/shm` transaction, then `python3 -m unittest tests.test_sync.TestResolveTaskContent.test_round_trip_emits_exact_five_key_json_and_typed_lists -v`. [VERIFIED: `21-01-PLAN.md`; `21-CONTEXT.md`, D-03, D-06-D11] | ✅ Inline command plus existing test. |
| CUT-02 | Four one-factor public failures before removal; exhaustive Patch-2 residue sweep; post-removal positive/negative repetition; Patch 1 check. | TDD retirement regression plus fresh live integration. | Task 2's execution-local residue/Patch-1/rollback transaction; exact Task 1 transaction repeated after removal; Python compile and `python3 -m unittest discover -s tests -t tests`. [VERIFIED: `21-01-PLAN.md`; `.github/workflows/ci.yml:36-40`; `21-CONTEXT.md`, D-04, D-09-D15] | ✅ Inline commands plus existing suite. |

### Sampling Rate

- **Per task commit:** each task's explicit inline transaction and focused exact-argv spy; Task 2 also routes `python3 -m py_compile scripts/sync.py` bytecode into its bounded evidence directory. [VERIFIED: `21-01-PLAN.md`]
- **Per wave merge:** `python3 -m unittest discover -s tests -t tests`. [VERIFIED: `.github/workflows/ci.yml:36-40`]
- **Phase gate:** repeat the public positive, the four isolated negative arms, and Patch 1 verification after removal; no suite result substitutes for the live proof. [VERIFIED: `21-CONTEXT.md`, D-04, D-08-D11]

### Wave 0 Gaps

- [x] No persisted Wave 0 harness is needed: Task 1's inline transaction exercises the public router against the current active-global bundle and reuses the existing exact-argv spy. [VERIFIED: `21-01-PLAN.md`]
- [x] Task 2's inline commands cover scoped Patch-2 residue, Patch-1 region/runtime identity, rollback hash behavior, the repeated public matrix, Python compile, and the inherited full suite. [VERIFIED: `21-01-PLAN.md`; `21-CONTEXT.md`, D-04, D-09-D15]
- [x] Every volatile path, row, capture, and negative arm is execution-local and bounded under `/dev/shm`; no copied Beads database, synthetic task, or reusable framework is persisted. [VERIFIED: `21-01-PLAN.md`; `21-CONTEXT.md`, D-01-D12]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No authentication mechanism is changed in Phase 21. [ASSUMED] |
| V3 Session Management | no | No session mechanism is changed in Phase 21. [ASSUMED] |
| V4 Access Control | no | Capability scope/consent is GSD-owned and out of phase scope. [VERIFIED: `21-CONTEXT.md`, D-12] |
| V5 Input Validation | yes | Preserve exact plan task-id lookup, manifest shape validation, safe Beads-id grammar, typed argv, and malformed-stdout hard failure. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:103-143`; `/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs:171-261`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:676-782`] |
| V6 Cryptography | no | Do not add cryptography; existing bundle hashing supports drift detection but does not replace the required runtime proof. [VERIFIED: `plugins/beads-lifecycle/hooks/capability-auto-install.sh:22-53`; `21-CONTEXT.md`, D-02] |

### Known Threat Patterns for the stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Project overlay shadows stale global bundle | Spoofing / Tampering | Derive active source and run the public proof from non-overlay context; compare complete trees. [VERIFIED: `21-CONTEXT.md`, D-02-D03] |
| Hostile/malformed resolver output | Tampering | Router fails nonzero for malformed resolver output; adapter emits no stdout on errors. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:96-143`; `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1238-1244`] |
| Identifier shell injection | Tampering | Adapter validates the id and calls `subprocess.run` through a fixed argv list. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:676-703`] |
| Patch deletion leaves unavailable content path | Denial of service | Pre-removal public positive and isolated failures; exact-byte rollback only after post-removal failure. [VERIFIED: `21-CONTEXT.md`, D-04-D05] |

## Sources

### Primary (HIGH confidence)

- [Installed task-command router](/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs) - public `resolve-content`, plan containment, installed registry loading, and hard-stop mapping. [VERIFIED: `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:65-155`]
- [Tracked Beads resolver](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py) - typed live Beads argv, resolver failures, Patch checker and both patch rows. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:145-201`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:676-782`; `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:2827-2883`]
- [Tracked retirement contract](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md) - Patch 2 marker, deletion set, and machine-local risk. [VERIFIED: `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md:162-270`]

### Secondary (MEDIUM confidence)

- [GSD capability manifest reference](https://github.com/open-gsd/gsd-core/blob/next/docs/reference/capability-manifest.md) - feature manifest validation, overlay roots, and tracker-prefix uniqueness. [CITED: https://github.com/open-gsd/gsd-core/blob/next/docs/reference/capability-manifest.md]
- [Beads documentation](https://github.com/gastownhall/beads/blob/main/docs/index.md) - programmatic `--json` read guidance and Dolt authority. [CITED: https://github.com/gastownhall/beads/blob/main/docs/index.md]
- [NIST IR 8011-3](https://nvlpubs.nist.gov/nistpubs/ir/2018/NIST.IR.8011-3.pdf) and [NIST SP 800-204D](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204D.pdf) - bounded rollback/recovery, release metadata, and drift principles. [CITED: https://nvlpubs.nist.gov/nistpubs/ir/2018/NIST.IR.8011-3.pdf]; [CITED: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204D.pdf]

### Tertiary (LOW confidence)

- None; unverified execution-local choices are recorded in the Assumptions Log.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - current source, runtime observations, and official docs align.
- Architecture: HIGH - direct router/adapter/installer source identifies the only required seams.
- Pitfalls: HIGH - each is a locked decision or directly traceable to the current code; external operational framing is MEDIUM.

**Research date:** 2026-09-01 [VERIFIED: `date`, 2026-09-01]
**Valid until:** Cutover-specific runtime observations expire immediately; re-observe them in the D-01 transaction. [VERIFIED: `21-CONTEXT.md`, D-01]
