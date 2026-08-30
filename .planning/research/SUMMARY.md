# Project Research Summary

**Project:** gsd-beads v1.4 — Native Task Content Resolution  
**Domain:** GSD capability overlay backed by live Beads task content  
**Researched:** 2026-08-30  
**Confidence:** MEDIUM

<!-- rumdl-disable MD013 -->

## Executive Summary

v1.4 is a bounded migration, not a new task system: replace the
machine-local executor read-path known as Patch 2 with gsd-core 1.12.0's native
`taskContentResolver` seam. The capability should register exactly one `beads`
resolver and invoke a narrow, proposed resolver verb in the existing
Python-standard-library adapter. That adapter alone translates live Beads issue
data into the single JSON object gsd-core requires; gsd-core continues to own
exact task lookup, resolver selection, timeouts, and hard failure. This
preserves the overlay model, live Beads authority, and the no-new-dependency
constraint. **[96/100]**

The migration must be additive and fail closed. `auto` and `tracer` task
opening tags should gain `tracker-id="beads:<id>"` while retaining
`<beads-id>` for existing lifecycle consumers; `checkpoint:*` tasks remain
byte-for-byte outside the migration. Raw `bd show <id> --json` is the approved
live Beads read boundary but is *invalid as a direct resolver command*, because
the observed payload is an array whereas native gsd-core accepts one JSON
object. Faults after resolver selection—ambiguous prefix, unavailable `bd`,
non-zero child exit, timeout, or malformed stdout—must terminate non-zero rather
than fall back to stale or stripped `PLAN.md` text. **[99/100]**

The central risk is operational, not architectural: source validation does not
prove the installed capability path, loaded registry, working directory, or both
runtime homes. Retire Patch 2 only after an installed-bundle public-command
proof succeeds, all negative paths hard-halt, source and installed copies are
byte-identical, and Patch 1's independent ship-pre dispatcher remains present.
**[96/100]**

## Key Findings

Detailed evidence: [STACK.md](STACK.md), [FEATURES.md](FEATURES.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [PITFALLS.md](PITFALLS.md).

### Recommended Stack

Use gsd-core's native resolver in the existing Beads feature capability; do not
patch or fork gsd-core. The feature-role manifest should declare the unique
`beads` tracker prefix with a literal `{{id}}` argv element and a positive
timeout no greater than 120,000 ms. The existing adapter is the approved
protocol boundary: it already owns Beads CLI invocation and JSON handling, and
the proposed small resolver verb avoids duplicate parsing, subprocess policy,
packaging, or release surface. **[96/100]**

**Core technologies:**

- `@opengsd/gsd-core` 1.12.0 native `taskContentResolver` — supported resolver router and hard-failure semantics; replaces Patch 2. **[95/100]**
- Beads feature capability manifest, 0.4.0 to next patch — declares the sole `beads` prefix and bounded adapter invocation. **[99/100]**
- Existing Python-standard-library adapter — should transform one live `bd show`
  row into the native result schema; no new module or dependency. **[95/100]**
- Beads `bd` CLI 1.2.2 — authoritative issue read boundary through `bd show <id> --json`, never JSONL/Dolt internals. **[100/100]**

**Scientific appraisal:** Installed gsd-core router, parser, resolver, and
validator sources are direct primary implementation evidence. The live
`bd show gsd-beads-xy2 --json` observation directly establishes the array
envelope and fields, but that raw output cannot satisfy gsd-core's plain-object
resolver contract. The ticket establishes scope only; it is not proof of runtime
behavior. Official web documentation corroborates the contracts, while
installed-path behavior still requires an end-to-end gate. **[95/100]**

### Expected Features

**Must have (table stakes):**

- One declared Beads resolver with validator-compliant binary, args, `{{id}}`, and timeout. **[98/100]**
- Adapter output of exactly one object with non-blank `description` to resolve, plus correctly shaped optional fields. **[97/100]**
- Idempotent `tracker-id` backfill for only `auto`/`tracer`, retaining `<beads-id>`. **[96/100]**
- Explicit checkpoint exclusion and legacy-plan preservation. **[98/100]**
- Native non-zero hard halts for resolver defects, proven at the public command before Patch 2 removal. **[99/100]**

**Should have (safety differentiators):**

- A single canonical, typed Beads-to-gsd mapping boundary. **[94/100]**
- A negative-path matrix whose arms isolate registration, exit status, timeout, and stdout shape. **[93/100]**
- A compatibility window with both identity forms until every installed consumer is proven native. **[92/100]**

**Defer (v2+):**

- Removing legacy `<beads-id>`.
- Multi-tracker abstraction, content cache, retry loop, telemetry, SDK/schema package, or a second resolver path. None solves a demonstrated v1.4 requirement; all violate Ponytail's no-new-dependency and minimum-mechanism constraints. **[91/100]**

### Architecture Approach

The proposed data path is deliberately short: the existing issue-sync command
writes an eligible task's additive `tracker-id`; gsd-core finds that exact
identity and launches the installed capability's resolver; the proposed adapter
verb executes fixed-argv `bd show <id> --json`, validates one issue, and prints
the mapped JSON object to stdout only. `<beads-id>` remains the identity used by
lifecycle status, dependencies, close-wave, and reconciliation. The patch
documentation should retain Patch 1 only after all Patch-2 marker, checker,
route, and documentation references are removed together. **[98/100]**

**Major components:**

1. Beads capability manifest — planned native resolver registration while
   preserving existing lifecycle gates. **[99/100]**
2. Existing issue-sync command — planned distinct idempotent
   eligibility/backfill set for task routing identity. **[98/100]**
3. Existing adapter's proposed resolver verb — one-object schema adapter with
   JSON-only stdout and stderr diagnostics. **[99/100]**
4. gsd-core task router — exact lookup, prefix selection, bounded invocation, result classification. **[99/100]**
5. Patch documentation/checking — retire Patch 2; preserve the independent Patch 1 v2 contract. **[97/100]**

### Critical Pitfalls

1. **Passing raw Beads JSON to gsd-core** — unwrap and validate exactly one issue object; do not emit arrays or diagnostic text on stdout. **[95/100]**
2. **Criteria/Markdown normalization silently loses task contract** — define one deterministic scalar-to-string-array policy and adversarially test empty, multiline, CRLF, duplicate-heading, code-fence, and unknown-heading cases. **[91/100]**
3. **Overbroad `tracker-id` rewrite** — only parsed `auto`/`tracer` tasks with one valid `<beads-id>` qualify; snapshots must show checkpoints and legacy headings untouched and a second run byte-identical. **[96/100]**
4. **Soft fallback after a resolver fault** — retain gsd-core's error taxonomy; only a successful schema-valid empty description may be an explicit legacy boundary. **[97/100]**
5. **Retiring Patch 2 only in source** — prove active installed bundles and both runtime homes lack Patch 2, match source bytes, and still pass the Patch 1 check. **[96/100]**

## Implications for Roadmap

### Phase 1: Native Resolver Contract and Failure Boundary

**Rationale:** The manifest and adapter contract are prerequisites for every migration action; they establish native routing before plan identities change.  
**Delivers:** One feature-capability resolver declaration; one narrow stdlib
adapter resolver command; validator and public-boundary tests for output mapping,
malformed stdout, unavailable/non-zero `bd`, timeout, prefix collision, and no
stdout pollution.  
**Addresses:** Declared resolver, single-object output, hard failure, and canonical typed-adapter features.  
**Avoids:** Array-envelope misuse, scalar/array loss, direct JSONL/Dolt access, false `resolved:false`, and new dependencies.  
**Research flag:** Standard core patterns are already directly characterized; skip generic framework research. Re-check the installed-capability executable-path mechanism and observe the live criteria field before implementation. **[95/100]**

### Phase 2: Additive Identity Migration and Compatibility

**Rationale:** Native lookup is useless until executable task identities are present, but existing lifecycle consumers and checkpoints must keep their current semantics.  
**Delivers:** A distinct, idempotent backfill of `tracker-id="beads:<id>"` for eligible modern `auto`/`tracer` tasks; retained `<beads-id>`; fixtures for legacy heading plans, legacy `<beads-id>`-only plans, checkpoint forms, and rerun byte identity.  
**Addresses:** Exact additive identity migration, checkpoint exclusion, and dual-identity compatibility.  
**Avoids:** Broad regex rewrites, task-kind corruption, duplicate creation, and lost legacy execution.  
**Research flag:** Plan a focused research pass against actual legacy fixture shapes and the observed Beads criteria representation; do not infer either from prose. **[96/100]**

### Phase 3: Installed Cutover, Patch 2 Retirement, and Release Proof

**Rationale:** Patch 2 must remain until the actual installed bundle has proved native resolution; source-tree tests cannot establish runtime loading or environment correctness.  
**Delivers:** Installed-bundle resolution from a real plan and live issue; main-checkout and worktree failure visibility; merged-registry uniqueness; byte-manifest parity across active copies; Patch 2 route/checker/docs removal; independent Patch 1 re-proof and release documentation.  
**Addresses:** Public end-to-end proof and removal of only the superseded machine-local patch.  
**Avoids:** Stale installation, wrong Beads database/cwd, Patch 1 collateral removal, and a source-only retirement claim.  
**Research flag:** Requires fresh operational discovery immediately before execution because active runtime paths, registries, `PATH`, Beads schema/version, and installed copies are volatile. **[96/100]**

### Phase Ordering Rationale

- The native contract must validate before a plan can safely gain a routable identity. **[99/100]**
- Dual identity is the compatibility bridge: old lifecycle semantics continue while native resolution begins. **[99/100]**
- Installed-runtime proof is the terminal gate because it simultaneously tests registry loading, executable path, current database discovery, hard halts, and Patch 2's actual absence. **[96/100]**

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 2:** inspect live/fixture `acceptance_criteria` representation and all legacy plan shapes before defining normalization and backfill tests.
- **Phase 3:** re-observe installed runtime homes, capability registry, cwd/database discovery, and byte parity immediately before retirement.

Phases with standard patterns (skip broad research-phase):

- **Phase 1:** gsd-core's 1.12 resolver contract, exact identity lookup, validator bounds, and hard-failure taxonomy have direct installed-runtime evidence. Limit research to the stated path/field validations.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | The core/CLI contracts are directly observed; static installed-adapter path still needs live proof. |
| Features | MEDIUM | Requirements map directly to native semantics, but no installed end-to-end execution has yet replicated them. |
| Architecture | HIGH | Installed router/parser/validator plus local adapter and manifest support one thin-adapter architecture. |
| Pitfalls | MEDIUM | Failure and migration risks are well grounded; runtime database and installation behavior remains version/environment sensitive. |

**Overall confidence:** MEDIUM. The chosen mechanism is high-confidence; release readiness is intentionally conditional on Phase 3 evidence.

### Gaps to Address

- **Installed adapter path:** prove the manifest can invoke the adapter from every active installed capability copy without relying on a source-tree cwd. Handle this as a design/acceptance gate, not an invitation to add a wrapper. **[70/100]**
- **Acceptance field representation:** inspect current real Beads data, select an explicit lossless normalization policy, and lock it with fixtures before coding. **[70/100]**
- **Current runtime state:** revalidate installed resolver-prefix uniqueness, `bd` version/database discovery, Patch 1 presence, and Patch 2 absence at execution time; planning artifacts and tickets are not authority for those volatile facts. **[93/100]**

## Sources

### Primary (HIGH confidence)

- Installed [gsd-core task router](/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92), [task-content resolution](/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs:302), [plan parser](/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:123), and [capability validator](/home/dd/.codex/gsd-core/bin/lib/capability-validator.cjs:733) — native contract, routing, and validation bounds.
- Existing Beads [capability manifest](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:1) and [sync adapter](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:300) — current overlay and protocol boundary.
- Live `bd` 1.2.2 `show gsd-beads-xy2 --json` observation on 2026-08-30 — array envelope plus issue fields; direct data evidence only.

### Secondary (MEDIUM confidence)

- [GSD resolver capability guide](https://github.com/open-gsd/gsd-core/blob/next/docs/how-to/develop-a-task-content-resolver-capability.md) and [capability manifest reference](https://github.com/open-gsd/gsd-core/blob/next/docs/reference/capability-manifest.md) — official documentation corroborating local runtime behavior.
- [GSD capability-system ADR](https://github.com/open-gsd/gsd-core/blob/next/docs/adr/857-capability-system.md) — capability architecture context.
- [Beads documentation](https://github.com/gastownhall/beads/blob/main/docs/index.md), [reference index](https://github.com/gastownhall/beads/blob/main/docs/reference/index.md), [releases and upgrade guidance](https://github.com/gastownhall/beads/releases), and [agent instructions](https://github.com/gastownhall/beads/blob/main/AGENT_INSTRUCTIONS.md) — supported CLI boundary and operational guidance.

### Scope-only evidence

- [v1.4 project brief](../PROJECT.md) and `gsd-beads-xy2` — define intended scope; they do not establish a current runtime contract.

---

*Research completed: 2026-08-30*  
*Ready for roadmap: yes*
