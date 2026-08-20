# Requirements: beads capability for gsd-core — v1.3 Config/Code Truth

**Defined:** 2026-08-19
**Core Value:** `bd` is the single source of truth for gsd task state — no duplicated
task-state bookkeeping survives in `.planning/`.

## v1.3 Requirements

**Revised 2026-08-19 after the research phase that should have run before the first roadmap.**
The original two requirements were written against gsd-core 1.10.0 while 1.11.0 was already
released. Research then found a second, larger miss: PR **#3687** (generic `kind: "step"` dispatch
at `plan:post` and `verify:post`) merged to the `next` default branch at 20:41:28Z, **6h50m after
the v1.11.0 release cut** — unreleased, but landing next cut. Planning from releases alone would
have had this phase re-invent two of the hook's five dispatch points.

Four requirements now. TRUTH-01/02 close declaration-vs-code divergences; TRUTH-03 keeps the gh-2
hook correct across an upstream change already merged; TRUTH-04 fixes a P1 correctness bug that
gsd-core 1.11.0 made reachable.

### Config Truth

- [ ] **TRUTH-01**: Every value `capability.json` declares for `beads.sync_mode` has an
  observable effect, or is not declared. Today `authoritative | mirror | off` are declared and
  **no code reads the key at all** — `mirror` and `off` silently do nothing, and README describes
  the key as controlling "who owns task status and content", which no code enforces. Closing this
  means either the enum becomes real or the declaration plus every doc describing it narrows to
  what the code actually does.
  *(bd: `gsd-beads-v43`, P1)*

  **Direction still undecided, but research narrowed it sharply.** The plan must present an
  Alternatives Considered table covering (a) narrow the declaration and docs, (b) implement
  `mirror` and `off`, (c) drop the key entirely — and must state what happens to a project that
  already wrote `"sync_mode": "mirror"` or `"off"`. Research findings the table must engage with:

  - **(b) has no declarative wiring channel.** `configValues` is resolved for
    `kind: "contribution"` only — the steps loop never calls it, and `beads-sync` is a step.
    `when:` is boolean-coerced, so `"off"` is truthy. `config-equals` is documented but
    unimplemented (`EVALUATOR_KINDS` frozen to two kinds). Only a self-read in `sync.py` remains
    — which is exactly how `beads.enabled` already works, so (b) is *possible*, just unwired.
    Separately, `off` largely duplicates `beads.enabled: false`.

  - **Enum values ARE validated on write** — verified live, not from docs:
    `config-set beads.sync_mode bogus` → `Error: Invalid beads.sync_mode 'bogus'. Valid values:
    authoritative, mirror, off`, and the value is not stored. They are **not** validated on read;
    a value hand-written into `.planning/config.json` is returned verbatim.

  - **Therefore (c) removes the only error surface the key has.** Dropping it makes
    `config-set beads.sync_mode …` fail with a generic `Unknown config key` whose ~2000-char
    valid-key dump contains no `beads.*` entry at all; and an orphaned value left on disk is read
    back silently forever, since gsd-core's unknown-key warning inspects only top-level keys and
    never descends into a namespace. **(a) keeps `Error: Invalid beads.sync_mode 'banana'` alive.**

  - **Precedent:** 0 orphan config keys across all four sibling plugins; removal precedent exists
    (`runtime.hostBehaviors.reviewerCli` — one release as a derived alias, then deletion, warning
    never error); narrowing an enum has no precedent either way.

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

  **Research-supplied constraints — the merge is less safe than it looks:**

  - The two markers are at **different versions** (`ship-pre-generic-dispatch v2`,
    `execute-plan-bd-task-read v1`). A shared table needs a per-entry version field; no test
    asserts marker version today.

  - `--execute-plan-path` is pinned by a CLI test; **`--ship-md-path` is not.** A unified CLI verb
    would therefore keep the suite at 164/164 green while silently breaking
    `beads-status/SKILL.md` Step 2d, which invokes `check-shipmd-patch` by name. Add the missing
    coverage *before* merging, not after.

  - The two messages differ in consequence text ("the ship_override step will not fire" vs
    "gsd-executor will not read task content from bd"); users and docs may grep either.

### Forward Compatibility

- [x] **TRUTH-03**: The `lifecycle-dispatch` PostToolUse hook stays correct when gsd-core ships
  PR **#3687**, which adds native generic `kind: "step"` dispatch at `plan:post` and
  `verify:post`. Merged to `next` 2026-08-19T20:41:28Z; unreleased as of v1.11.0.

  Two distinct problems, both of which must be answered:

  1. **Double dispatch.** Once native dispatch exists at those two points, the hook fires *and*
     gsd-core dispatches. `create_issues` is idempotent so duplicate issues are not created, but
     the work is wasted and the `additionalContext` output doubles.

  2. **The `allow_strip` protection is bypassed, silently.** Native dispatch invokes the
     `beads-sync` *skill*, which runs `sync.py create-issues` with `allow_strip` defaulting to
     **True** — so `strip_task_bodies` returns via the native path even though the hook path
     deliberately disables it (0.3.1, gh-2). Whether that is correct (an explicit dispatch is a
     different principal than a string-matched hook) is a decision this requirement must make and
     record, not a detail to discover in production.

  `execute:wave:pre` and `execute:wave:post` are **not** covered by #3687 and have no upstream fix
  released, merged, or in an open PR — the hook remains necessary for those.
  *(bd: `gsd-beads-he1`, P1)*

### Correctness

- [x] **TRUTH-04**: A phase with a decimal number (`1.5`, `10.1`, `11.1` — as produced by
  `gsd-phase --insert`) works at all three beads lifecycle points. Today all three break:
  `PLAN_FILE_RE` is `^(\d{2}-\d{2})-PLAN\.md$`, too narrow, failing **silently** to an empty
  result at `execute:wave:*`; and `int(phase_num)` raises `ValueError: invalid literal for int()
  with base 10: '01.5'` in both `get_phase_header` (`plan:post`) and `extract_phase_mentions`
  (`plan:pre`). The `int()` is a leading-zero strip, not a type requirement.
  *(bd: `gsd-beads-bzl`, P1)*

  **This repository's own history contains decimal phases** (`10.1-capability-auto-install…`,
  `11.1-beads-enabled-default-flip-to-true`), and the sibling `sota-numerics` capability already
  widened its own regex with a comment naming beads' pattern as too narrow — so the fix has a
  precedent to match. Every hook is `onError: skip`, so all three degrade quietly: the reporter
  observed 6 plans / 16 tasks complete with zero tickets and no failure surfaced.

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

| Requirement | Phase | Plan | bd | Status |
|-------------|-------|------|-----|--------|
| TRUTH-01 | Phase 17 | 17-03 | `gsd-beads-v43` (P1) | Pending |
| TRUTH-02 | Phase 17 | 17-04 | `gsd-beads-t7a` (P3) | Pending |
| TRUTH-03 | Phase 17 | 17-02 | `gsd-beads-he1` (P1) | Complete |
| TRUTH-04 | Phase 17 | 17-01 | `gsd-beads-bzl` (P1) | Complete |

Plan order is deliberate and argued in ROADMAP.md Phase 17: TRUTH-04 first (P1, silent failure,
and it unblocks `/gsd-phase --insert` as this phase's own escape hatch), TRUTH-03 second
(time-boxed by an upstream release), then TRUTH-01, then TRUTH-02 (P3, riskiest refactor, lands on
a stabilised `sync.py`).

**Coverage:**

- v1.3 requirements: 4 total
- Mapped to phases: 4
- Unmapped: 0 ✓

## Release-hygiene debt carried into this milestone

Not requirements — defects in the CURRENT repo state that this milestone's ship step must clear,
surfaced by the same research pass:

- **`main` is ahead of `v1.3.1` with a behavioral change and no version bump or CHANGELOG entry.**
  Commit `966315a` moved `SHIP_MD_PATCH_MARKER` from v1 to v2 — a constant that changes what
  `check_shipmd_patch` reports. Ship must bump and changelog it.

- **CHANGELOG 0.3.1 mis-files the hook `timeout`.** It reads "set an explicit 120 s hook timeout"
  under **Performance**, implying protection was added. The command-hook default is **600 s**, so
  120 is a *reduction*. Same false-claim class as TRUTH-01.

- **Deleting the `v1.3.0` GitHub Release withdrew less than it appeared to.** `marketplace.json`
  declares `"source": "./plugins/beads-lifecycle"` — a branch source — so marketplace installs
  never came from the release zip. The real exposure was the branch window between `55855cd` and
  the fix in `049da5b`.

- **`~/.claude/gsd-local-patches/` holds a stale v1 copy of the ship.md patch** while the live file
  carries v2, and gsd-core's own `verify-reapply-patches.cjs` gate exits 1. Nothing in this repo
  references that directory. Machine-local, not tracked — but it will mislead the next upgrade.

---
*Requirements defined: 2026-08-19*
*Last updated: 2026-08-19 after the Phase 17 roadmap revision (baselines re-verified on gsd-core 1.11.0 at commit 966315a)*
