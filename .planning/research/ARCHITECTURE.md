# Architecture Patterns: v1.4 Native Task Content Resolution

**Project:** gsd-beads
**Domain:** GSD capability overlay integrating Beads task content
**Researched:** 2026-08-30
**Overall confidence:** HIGH for current local/runtime contracts;
MEDIUM for upstream documentation.

## Recommended Architecture

Use gsd-core's native `taskContentResolver` seam. Extend the existing,
stdlib-only `sync.py` CLI with one narrow resolver subcommand; do not add a
second executable, cache, or task-content store. Its manifest declaration
invokes this adapter, which maps live `bd show <id> --json` data to gsd-core's
single-object resolver schema.

```text
PLAN.md <task type="auto|tracer" tracker-id="beads:<id>">
        │                     ▲
        │ sync/backfill        │ task resolve-content --task-id beads:<id>
        ▼                     │
sync.py create-issues ────────┴── gsd-core router
        │                          │ resolves installed beads capability
        │ bd create/show            ▼
        ▼                    sync.py resolver <id>
live Beads issue ────────────────► bd show <id> --json
                                     │
                                     ▼
             {description, verify, acceptance_criteria, read_first, done}
```

`tracker-id` is routing identity, not a replacement for `<beads-id>`.
Keep both: existing lifecycle status/dependency/closure functions read
`<beads-id>`, whereas native gsd-core content resolution reads the exact
`tracker-id` attribute. The resolver splits only on the first colon and passes
the remaining Beads id verbatim. **Confidence: 98.**

### Component Boundaries

| Component | Responsibility | Communicates With | Contract / confidence |
|---|---|---|---|
| `capability.json` | Declare `trackerPrefix: "beads"`, bounded adapter argv, and retain lifecycle steps/gates. | GSD capability loader/validator | Feature-role only; `args` contains `{{id}}`; `timeoutMs` is positive and ≤120000. HIGH 99. |
| `sync.py create-issues` | Create/resolve Beads issues and backfill plan identity. | `PLAN.md`, `bd` | Add routing id only to auto/tracer; leave checkpoint tasks untouched. HIGH 95. |
| `sync.py` resolver command | Read one live issue and emit exactly one mapped JSON object. | `bd show --json`, stdout/stderr | Current `main()` has no resolver command: it must be added; a manifest-only change cannot work. HIGH 99. |
| gsd-core task router | Exact `tracker-id` lookup, resolver selection, bounded process call, output mapping. | Parser, installed capability registry, adapter CLI | Empty description is unresolved; failure modes are hard halts. HIGH 99. |
| `GSD-CORE-PATCH.md` | Own only remaining machine-local ship-pre patch. | installed `ship.md`, `check-patch` | Retire all Patch 2 code/docs/wiring; retain independent Patch 1 v2. HIGH 97. |

### Data Flow

1. `create-issues` resolves a task's existing `<beads-id>` or creates the
   issue, then writes `tracker-id="beads:<issue-id>"` for eligible tasks.
   It must backfill already-synced tasks: current `rewrite_plan()` only receives
   updates for newly created issues, so the migration requires a separate,
   idempotent identity write set. **Confidence: 98.**
2. gsd-core parses the `tracker-id` verbatim, finds the task by its exact value,
   locates the one matching installed resolver, and substitutes the id token in
   the resolver's argv. **Confidence: 99.**
3. The adapter invokes `bd show <id> --json`, parses live output, and emits
   `description`, optional `verify`, `acceptance_criteria`, `read_first`, and
   `done`. **Confidence: 95.**
4. A non-empty `description` resolves task content. Empty/missing description
   is the legitimate pre-migration boundary (`resolved:false`, reason `empty`),
   leaving inline content available to legacy plans. **Confidence: 96.**
5. Non-zero exit, timeout, malformed/non-object JSON, or duplicate resolver
   prefix is a hard halt: never synthesize `resolved:false` and never fall back
   silently. **Confidence: 99.**

Treat `tracker-id` and Beads stdout/stderr as untrusted input. Pass the id only
as one argv element, parse JSON before mapping, keep stdout strictly
machine-readable, and emit concise stderr diagnostics. The native runtime
sanitizes diagnostic rendering; the adapter must not bypass it with prose on
stdout. **Confidence: 93.**

## Patterns to Follow

### Pattern 1: Thin in-place adapter (Ponytail ladder, rung 2)

**What:** Add the resolver verb to `sync.py`, reusing its current `run_bd`,
standard-library JSON, and capability-relative executable path.

**When:** For every native resolver call.

**Why:** This module already owns Beads issue creation, live `bd show --json`
reads, and plan rewriting. A wrapper/new dependency duplicates the mapping risk
and adds an invocation boundary. **Confidence: 96.**

```json
{
  "description": "required non-empty action to resolve",
  "verify": "optional verification",
  "acceptance_criteria": ["optional criterion"],
  "read_first": ["optional path"],
  "done": "optional completion condition"
}
```

### Pattern 2: Forward-compatible dual identity

**What:** Preserve `<beads-id>` while adding `tracker-id` only to auto/tracer
opening tags.

**When:** New-task sync and legacy backfill.

**Why:** Current status, dependency, close-wave, and reconciliation paths read
`<beads-id>`. gsd-core explicitly makes checkpoint `trackerId` null; adding one
would mutate its distinct control-flow contract. **Confidence: 99.**

### Pattern 3: Public-boundary tests before Patch 2 retirement

| Boundary | Required proof |
|---|---|
| Manifest | Validator accepts Beads' resolver and rejects duplicate prefix. |
| Sync writer | New and legacy auto/tracer tasks gain one `tracker-id`; checkpoints are byte-identical; rerun changes nothing. |
| Adapter | Fake `bd` proves field mapping; unavailable `bd`, unknown id, and malformed data exit non-zero with no JSON stdout. |
| Native seam | Real plan + `task resolve-content --raw` returns `resolved:true` and non-empty content. |
| Legacy plan | A `<beads-id>`-only plan retains established execution behavior; no resolver is selected without `tracker-id`. |
| Patch boundary | No Patch 2 marker or wiring remains; Patch 1 v2 still applies and verifies. |

Current gsd-core public tests characterize exact tracker-id lookup, non-empty and
empty descriptions, non-zero exit, timeout, malformed output, first-colon
splitting, and no stdout `resolved:false` on hard failure. Mirror those outcomes
at the Beads boundary rather than relying on helper-only tests. **Confidence: 98.**

## Anti-Patterns to Avoid

### Direct `bd` manifest invocation

**What:** Declare `bd` directly as the resolver binary.

**Why bad:** gsd-core expects `description`, `acceptance_criteria`,
`read_first`, and `done`; Beads uses a different issue shape. This can resolve
empty or silently lose fields.

**Instead:** Keep `sync.py` as the thin schema adapter. **Confidence: 95.**

### Backfilling only newly created issues

**What:** Reuse the existing `task_updates` list unchanged.

**Why bad:** It contains only tasks whose issues were created in that run;
valid existing `<beads-id>` tasks would never receive `tracker-id`.

**Instead:** Derive a distinct eligible backfill set. **Confidence: 99.**

### Softening resolver failure

**What:** Return an empty object or read stripped PLAN content after `bd` fails.

**Why bad:** It violates native hard-halt semantics and breaks the
authoritative-content guarantee.

**Instead:** Adapter failure exits non-zero; only a successful, empty
description takes the documented legacy boundary. **Confidence: 99.**

### Removing both local patches

**What:** Treat Patch 1 and Patch 2 as one migration unit.

**Why bad:** Patch 1 v2 provides an independent `ship:pre` generic step
dispatch; Patch 2 is only the old executor read path.

**Instead:** Retire Patch 2 only. **Confidence: 99.**

## Dependency Order

1. Add and validator-prove the resolver declaration plus adapter CLI contract.
2. Implement/test idempotent tracker-id backfill, preserving `<beads-id>` and
   checkpoint behavior.
3. Prove the public boundary: adapter mappings/failures, native hard halts,
   legacy-plan behavior, and one real resolution.
4. Remove Patch 2 and every Patch-2-specific detector/apply/document reference.
5. Re-prove Patch 1, then update release docs in the same change.

This order prevents removal of the only working read path before the native path
has evidence. **Confidence: 99.**

## Unchanged Components

`beads.enabled`, `beads.sync_mode`, epic resolution, dependency edges,
close-wave, `reconcile-stale-closed`, BEADS.md generation, lifecycle dispatch,
ship gates, and Patch 1's ship-pre dispatch are outside the migration. The only
plan-format addition is `tracker-id` on eligible task opening tags.
**Confidence: 96.**

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---|---|---|---|
| Resolver lookup | One bounded local `bd show`; no new service. | Same; measure latency before changing timeout. | Out of scope; protocol stays stable if Beads becomes remote. |
| Plan rewrite | One-file idempotent backfill per sync. | Same; no global migration scan. | Needs separate migration design. |
| Failure visibility | Hard halt with concise diagnostic. | Same. | Add telemetry only if operational evidence requires it. |

## Evidence Appraisal and Open Risk

**Central claim:** native resolution can replace Patch 2 safely. **Assessment:
Strong.** Installed 1.12.0 router/resolver source, current gsd-core tests/docs,
the live manifest, and ticket requirements agree on the load-bearing contracts.

**Rejected alternative:** “manifest-only change.” **Invalid.** Current `sync.py`
has no resolver subcommand, while raw `bd` output is not gsd-core's mapped
schema. **Confidence: 99.**

**Execution research flag:** verify the real current Beads acceptance field
before coding. Repository comments name `acceptance_criteria`; the current
upstream resolver guide illustrates `acceptance`. Normalize the observed live
shape deliberately and lock it with a test—do not guess. **Confidence: 70.**

## Sources

- [gsd-core resolver capability guide](https://github.com/open-gsd/gsd-core/blob/next/docs/how-to/develop-a-task-content-resolver-capability.md)
  — MEDIUM web confidence; cross-checked with installed 1.12.0 source.
- [gsd-core capability manifest reference](https://github.com/open-gsd/gsd-core/blob/next/docs/reference/capability-manifest.md)
  — MEDIUM web confidence; cross-checked locally.
- [Beads README](https://github.com/gastownhall/beads/blob/main/README.md)
  and [FAQ](https://github.com/gastownhall/beads/blob/main/docs/FAQ.md)
  — MEDIUM web confidence.
- Installed `task-content-resolution.cjs`, `task-command-router.cjs`,
  `plan-document.cjs`, and `capability-validator.cjs` from gsd-core
  — HIGH live-runtime confidence.
- Local gsd-core resolver docs/tests plus local Beads manifest, `sync.py`,
  `GSD-CORE-PATCH.md`, and ticket `gsd-beads-xy2` — HIGH confidence.
