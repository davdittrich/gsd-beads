# Feature Landscape

**Domain:** Native task-content resolution for the `beads` gsd-core capability overlay
**Milestone:** v1.4
**Researched:** 2026-08-30
**Overall confidence:** MEDIUM — active `@opengsd/gsd-core` 1.12.0 is primary evidence.
Context7 was unavailable; upstream source pages did not fetch through search.

<!-- rumdl-disable MD013 -->

## Decision Boundary

The milestone is a migration from a machine-local executor patch to gsd-core's declared
`taskContentResolver` seam. It is not a new task system, content cache, or fallback mechanism.
The minimum viable outcome is one typed resolver declaration, one legacy-safe identity migration,
and proof that live Beads content reaches the native public command while resolver faults halt.
Confidence 95.

## Table Stakes

Features required for this migration to be truthful. Omitting any one leaves Patch 2 necessary or
changes existing task semantics.

| Feature | Why Expected | Complexity | Notes | Confidence |
|---------|--------------|------------|-------|------------|
| **Declared Beads resolver** | gsd-core only selects external content by an installed feature capability's `taskContentResolver`; the declaration must claim the unique `beads` prefix. | Low | Declare `trackerPrefix: "beads"` and a bounded typed invocation. `invoke.binary` must be non-empty; `invoke.args` must be strings and include the whole-element `{{id}}`; `timeoutMs` is a positive integer no greater than 120,000. | 98 |
| **Single-object resolver output** | Native resolution accepts JSON only when stdout is one plain object. A non-empty `description` produces `resolved: true`; blank/missing description is the explicit `empty` data outcome. | Med | Produce `description` from live `bd show <id> --json`. Also map `verify`, `acceptance_criteria`, `read_first`, and `done` when present. They are optional-to-core fields, not excuses to manufacture task prose. | 97 |
| **Exact, additive task identity migration** | The command finds its target by exact `tracker-id`, which the plan parser preserves verbatim. Existing `beads-id` is still the legacy identity consumed by current plans. | Med | Sync emits `tracker-id="beads:<issue-id>"` on `auto` and `tracer` tasks while retaining `<beads-id>`. The change must be idempotent: re-sync changes neither task identity nor duplicate issues. | 96 |
| **Checkpoint exclusion** | A `checkpoint:*` task has a different grammar and is a human decision boundary, not tracker-backed executable content. | Low | Do not add `tracker-id` to checkpoints. The resolver must therefore be uncallable for checkpoints through the exact-ID command lookup. | 98 |
| **Hard resolver-failure contract** | Native core distinguishes absence of resolution from a broken resolver. Choosing inline `PLAN.md` content after an attempted resolver fails would falsely claim success and revive the retired patch's ambiguity. | Med | Ambiguous prefix, missing/unavailable/non-zero resolver command, timeout, malformed JSON, and JSON arrays/scalars must exit non-zero. No silent fallback is permitted. `no-resolver`, malformed tracker identity, and empty description are distinct `resolved:false` data outcomes. | 99 |
| **Public-boundary and live proof before Patch 2 removal** | Unit tests alone cannot prove manifest loading, live `bd` data, command routing, or the exact migration path. | High | Validate the manifest; verify a legacy `<beads-id>`-only plan still executes; test malformed stdout and unavailable `bd` as non-zero; then call `task resolve-content --plan <real plan> --task-id beads:<real id> --raw` and require `resolved:true` plus non-empty content. Only then retire Patch 2; keep Patch 1 unchanged. | 94 |

## Differentiators

These make the migration safer or cleaner than merely moving code. They remain inside the native
seam rather than adding a second content pipeline.

| Feature | Value Proposition | Complexity | Notes | Confidence |
|---------|-------------------|------------|-------|------------|
| **One canonical typed adapter** | The Python CLI transforms Beads JSON into gsd-core's content object; gsd-core owns routing, validation, timeout, and process error policy. | Med | Prefer this over executor Markdown surgery because it removes the recurring reapply conflict and leaves one auditable external boundary. | 94 |
| **Negative-path proof matrix** | Separately exercising `empty`/`no-resolver` and actual resolver faults prevents the common confound of treating every `resolved:false` result as safe degradation. | Med | Each test arm changes exactly one variable: resolver registration, exit status, timeout, or stdout shape. | 93 |
| **Compatibility window with two identities** | Keeping `<beads-id>` alongside native `tracker-id` lets old execution paths continue while new core resolves natively. | Low | Remove the legacy element only in a later milestone with evidence that no installed runtime consumes it. | 92 |

## Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead | Confidence |
|--------------|-----------|-------------------|------------|
| **A replacement executor patch or a second resolver path** | It recreates the release-conflict and splits responsibility for content selection. | Use the declared gsd-core `taskContentResolver` only. | 98 |
| **Fallback to inline `PLAN.md` content after a resolver fault** | It converts unavailable or corrupt authoritative Beads state into an apparent successful execution. | Propagate the native non-zero hard halt; distinguish it from `empty` and `no-resolver`. | 99 |
| **Migrating checkpoint tasks** | Checkpoints are structurally different and may prompt for human choices rather than execute tracker instructions. | Limit backfill to `auto` and `tracer`; assert no checkpoint gains `tracker-id`. | 98 |
| **Direct Dolt/JSONL parsing or plan-authored command execution** | Both bypass the supported `bd` JSON boundary and weaken the typed-value command construction / untrusted-input boundary. | Invoke a fixed adapter command with the resolver ID substituted as a whole argv element; consume `bd show --json`. | 94 |
| **New dependencies, cache, retry loop, or cross-tracker abstraction** | No evidence requires them; each widens the failure surface of a targeted migration. | Python 3 standard library plus the existing `bd` binary and native core timeout are sufficient. | 91 |
| **Retiring Patch 1 with Patch 2** | Patch 1 covers the separate `ship:pre` generic dispatch gap and remains necessary according to the scoped ticket. | Remove only Patch 2 wiring and marker after its native proof gates pass. | 96 |

## Feature Dependencies

```text
fixed Beads JSON adapter + capability declaration
    -> native resolver registration and validator acceptance
    -> tracker-id backfill on auto/tracer tasks
    -> exact-ID native command can find a real task
    -> resolved:true end-to-end proof
    -> Patch 2 deletion and its wiring removal

checkpoint exclusion --------------------------> all migration/proof stages
legacy <beads-id> preservation ----------------> legacy-plan execution proof
negative-path matrix --------------------------> Patch 2 deletion gate
```

## MVP Recommendation

Prioritize:

1. **Resolver contract and validator gate** — declare the bounded resolver and prove the native
   manifest contract before changing plan identity.
2. **Idempotent additive identity migration** — write `tracker-id` for only `auto`/`tracer`, retain
   `<beads-id>`, and prove checkpoints remain unmodified.
3. **One live end-to-end resolution plus isolated failure arms** — prove the actual public command
   and its hard halt branches before removing Patch 2.

Defer:

- **Legacy `<beads-id>` removal:** no evidence yet that every installed execution path accepts only
  `tracker-id`.
- **Generic multi-tracker framework:** a single `beads` declaration is the first Ponytail rung that
  satisfies the scope; no second tracker or shared abstraction is evidenced.
- **Caching/retry/telemetry:** core already bounds execution; retries could hide authoritative-state
  failures and caching would make content non-live.

## Evidence Appraisal

**Central claim:** native resolution can replace Patch 2 without weakening authoritative Beads
content or hard-failure behavior. **Assessment: Moderate / Accept with conditions.** The installed
official 1.12.0 core directly establishes the parser, validator, dispatch, result taxonomy, and
hard-halt semantics. Official Beads documentation directly establishes `bd show <id> --json` as
the programmatic CLI surface. The missing independent replication is a real capability-installed
end-to-end execution against this bundle, which is therefore a release gate rather than an assumed
result. Confidence 90.

Two rejected explanations were considered:

1. *“All resolver errors may be represented as `resolved:false`.”* Rejected: core explicitly throws
   for ambiguity, process failure, timeout, and malformed stdout; only no resolver, invalid identity,
   and empty content are non-throwing outcomes. Confidence 99.
2. *“Backfilling every task is simpler.”* Rejected: parser semantics and milestone scope distinguish
   checkpoint tasks; adding identity there would manufacture an executable lookup where none exists.
   Confidence 98.

The main bias risk is confirmation from the implementation ticket. This document treats ticket
claims only as scope; command/router/validator behavior was checked independently in the installed
core and Beads' public CLI documentation. Confidence 92.

## Sources

- [Installed official `@opengsd/gsd-core` 1.12.0: resolver contract and error taxonomy](/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs:3) — primary runtime source; confidence 98.
- [Installed official `@opengsd/gsd-core` 1.12.0: exact task lookup and CLI results](/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92) — primary runtime source; confidence 99.
- [Installed official `@opengsd/gsd-core` 1.12.0: plan parser task kinds and verbatim `tracker-id`](/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:3) — primary runtime source; confidence 98.
- [Installed official `@opengsd/gsd-core` 1.12.0: resolver-manifest validation](/home/dd/.codex/gsd-core/bin/lib/capability-validator.cjs:726) — primary runtime source; confidence 98.
- [Official Beads documentation: JSON command surface](https://github.com/gastownhall/beads/blob/main/docs/index.md) — verified web source; confidence 90.
- [Scoped milestone requirements](/home/dd/projects/gsd-beads/.planning/PROJECT.md:16) and [implementation ticket `gsd-beads-xy2`](/home/dd/projects/gsd-beads/.beads/) — scope only, not independent proof.
