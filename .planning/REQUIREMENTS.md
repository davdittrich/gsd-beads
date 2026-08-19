# Requirements: beads capability for gsd-core — v1.3 Config/Code Truth

**Defined:** 2026-08-19
**Core Value:** `bd` is the single source of truth for gsd task state — no duplicated
task-state bookkeeping survives in `.planning/`.

## v1.3 Requirements

Both requirements close a divergence between what this capability *declares* and what its code
*does*. Neither adds capability. Both were surfaced by the four-lens adversarial review of the
gh-2 lifecycle-dispatch fix on 2026-08-19, and both pre-date that fix.

### Config Truth

- [ ] **TRUTH-01**: Every value `capability.json` declares for `beads.sync_mode` has an
  observable effect, or is not declared. Today `authoritative | mirror | off` are declared and
  **no code reads the key at all** — `mirror` and `off` silently do nothing, and README describes
  the key as controlling "who owns task status and content", which no code enforces. Closing this
  means either the enum becomes real or the declaration plus every doc describing it narrows to
  what the code actually does.
  *(bd: `gsd-beads-v43`, P1)*

  **Direction deliberately undecided.** The plan must present an Alternatives Considered table
  covering at least: (a) narrow the declaration and docs, (b) implement `mirror` and `off`,
  (c) drop the key entirely — and must state, for the chosen option, what happens to a project
  that has already written `"sync_mode": "mirror"` or `"off"` into its `.planning/config.json`
  expecting an effect. That migration answer is part of the requirement, not an afterthought.

  **Includes the doc sweep.** No doc, comment, or changelog entry in this repo may survive
  claiming `beads.sync_mode` gates `strip_task_bodies` — the real gate is
  `check_execute_plan_patch()` plus the `allow_strip` flag added in 0.3.1. Known offenders as of
  today: `CHANGELOG.md`'s 0.3.0 Known-limits entry, `README.md`'s config table row, and the
  `create_issues` docstring. Corrected in the same commit as the code change, per the repo's
  "update all docs in the SAME commit" rule — leaving them would re-seed the divergence this
  requirement exists to close.

### Internal Consistency

- [ ] **TRUTH-02**: `check_shipmd_patch` and `check_execute_plan_patch` are served by one
  table-driven reader. They are structural clones — ~39 body lines each, identical control flow,
  differing only in filename, marker constant, and four message strings (~50 lines recoverable).
  `lifecycle_dispatch` now calls them back-to-back at `plan:pre`, which is exactly the table
  shape. Behavior at both existing call sites, and every existing patch-check test, must be
  unchanged.
  *(bd: `gsd-beads-t7a`, P3)*

## Future Requirements

Deferred, tracked, not in this roadmap.

### Resource Awareness

- **RES-01**: `get-available-resources` capability (CPU/GPU/memory/disk detection, advisory-only
  `plan:pre`/`execute:wave:pre` fragment). Dropped from v1.2 when Phase 16 displaced it. Not
  invalidated — revisit when the need resurfaces.

### Runtime Reach

- **REACH-01**: Lifecycle dispatch on runtimes without Claude Code's `PostToolUse` hook. Today
  five of the six declared lifecycle points dispatch only under Claude Code; other runtimes get
  `ship:pre` alone and must drive the rest via `sync.py lifecycle-dispatch <point>`.
  `.codex/hooks.json` and `.cursor/hooks.json` already establish the per-runtime pattern.
  Surfaced by the gh-2 review; deliberately out of v1.3, which is a truth-in-declaration
  milestone, not a reach milestone.

## Out of Scope

| Feature | Reason |
|---------|--------|
| New config keys of any kind | v1.3 removes a declaration/behavior gap; adding surface would widen the very thing being closed |
| Reworking the `lifecycle-dispatch` hook matcher | Shipped and regression-pinned in 0.3.1; no open defect |
| Upstreaming generic `kind: "step"` dispatch to gsd-core | No upstream issue tracks it. `#3559`/PR `#3608` fixed only `ship:pre` **gate** dispatch (shipped v1.11.0); `#3554` was closed NOT_PLANNED without review. Not shippable from this repo |
| Retroactive bd backfill for pre-0.3.0 phases | Needs a per-project decision about `strip_task_bodies`; not a config-truth concern |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRUTH-01 | Phase 17 | Pending |
| TRUTH-02 | Phase 17 | Pending |

**Coverage:**
- v1.3 requirements: 2 total
- Mapped to phases: 2
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-19*
*Last updated: 2026-08-19 after milestone v1.3 start*
