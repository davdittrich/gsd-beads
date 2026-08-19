# Roadmap: beads capability for gsd-core

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 (shipped 2026-08-16) — `.planning/milestones/v1.0-ROADMAP.md`
- ✅ **v1.1 Publish & Document** — Phases 5-12 (shipped 2026-08-18) — `.planning/milestones/v1.1-phases/`
- ✅ **v1.2 New Capability Plugins** — Phases 13-16 (shipped 2026-08-19) — `.planning/milestones/v1.2-ROADMAP.md`
- 🔨 **v1.3 Config/Code Truth** — Phase 17 (in progress, started 2026-08-19)

## Phases

<details>
<summary>✅ v1.0 milestone (Phases 1-4) — SHIPPED 2026-08-16</summary>

- [x] Phase 1: Substrate (3/3 plans)
- [x] Phase 2: Visibility (2/2 plans)
- [x] Phase 3: Enforcement (3/3 plans)
- [x] Phase 4: Adoption (3/3 plans)

</details>

<details>
<summary>✅ v1.1 Publish & Document (Phases 5-12) — SHIPPED 2026-08-18</summary>

- [x] Phase 5: Plugin Manifest
- [x] Phase 6: Runtime Integration
- [x] Phase 7: Hygiene & Publication
- [x] Phase 8: README, Release & Ship Gate
- [x] Phase 9: Beads Content Depth
- [x] Phase 10: ponytail-everywhere capability plugin
- [x] Phase 10.1: capability auto-install (INSERTED)
- [x] Phase 11: sota-numerics capability plugin
- [x] Phase 11.1: beads.enabled default flip to true (INSERTED)
- [x] Phase 12: Ship ponytail-everywhere and sota-numerics plugins publicly

</details>

<details>
<summary>✅ v1.2 New Capability Plugins (Phases 13-16) — SHIPPED 2026-08-19</summary>

- [x] Phase 13: markdown-linting capability (dogfood) (4/4 plans)
- [x] Phase 14: pr-workflow capability (dogfood) (3/3 plans)
- [x] Phase 15: Ship markdown-linting and pr-workflow plugins publicly (5/5 plans)
- [x] Phase 16: beads issue content parity (4/4 plans)

</details>

### v1.3 Config/Code Truth (Phase 17) — IN PROGRESS

- [ ] **Phase 17: Config/Code Truth** - Every declared config value has an observable effect, and the two patch-check clones become one reader

## Phase Details

### Phase 17: Config/Code Truth

**Goal**: A reader of this capability's `capability.json`, `README.md`, and `CHANGELOG.md` can
trust every statement they make about `beads.sync_mode` against the code that actually runs, and
the two structurally-identical patch detectors are served by one table-driven reader with no
behavior change at any call site.

**Depends on**: Phase 16 (shipped) — `check_execute_plan_patch` and the `strip_task_bodies` gate
it feeds both landed there; TRUTH-02 collapses that phase's deliberate clone, and TRUTH-01's doc
sweep corrects claims written across 0.3.0/0.3.1.

**Requirements**: TRUTH-01, TRUTH-02

**Success Criteria** (what must be TRUE):

1. **No declared-but-dead `sync_mode` value survives.** A repo-wide `grep -rn "sync_mode"`
   (excluding `.git/` and `.planning/`) resolves to exactly one of two end states: either every
   value `capability.json` still declares is read by a code path in `sync.py` that a test
   exercises, or the key is no longer declared anywhere. No hit sits in a third state where a
   declaration has no reader.
2. **No doc claims an effect the code does not have.** Every surviving `sync_mode` mention reads
   true against the shipped code. The known offenders as of 2026-08-19 are each resolved:
   `CHANGELOG.md:37` (0.3.0 Known-issues entry), `CHANGELOG.md:83`, `README.md:137` (config table
   row, "controls who owns task status and content"), `README.md:175`, `docs/prd-beads-capability.md:41`
   and `:149`, `.beads/PRIME.md:48`, `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md:59`,
   and the `create_issues` docstring at `sync.py:1289`. Specifically: nothing in the repo claims
   `beads.sync_mode` gates `strip_task_bodies` — the real gate is `check_execute_plan_patch()`
   plus the `allow_strip` flag. Corrected in the same commit as the code change.
3. **An existing `"sync_mode": "mirror"` / `"off"` project is answered, not orphaned.** The
   documented outcome for a project that already wrote either value into its
   `.planning/config.json` is demonstrated by an actual run against such a config (starts, no
   crash, behaves as documented), not asserted in prose only.
4. **One reader serves both patch checks.** `check_shipmd_patch` and `check_execute_plan_patch`
   no longer carry two copies of the same ~39-line body — the duplicated control flow exists once,
   parameterized by filename, marker constant, and the four message strings. `sync.py` is
   measurably shorter (~50 lines recoverable).
5. **Every existing call site behaves identically.** All five call sites
   (`lifecycle_dispatch`'s back-to-back `plan:pre` pair at `sync.py:726-727`, the
   `strip_task_bodies` gate at `:1369`, and the two CLI subcommands at `:2252`/`:2254`) produce
   unchanged output, and `python3 -m unittest discover -s tests -t tests` from the capability root
   reports the recorded pre-change baseline of **164 tests, OK**, with the assertions in
   `TestCheckShipmdPatch` and `TestCheckExecutePlanPatch` unedited.

**Constraints carried into planning** (these are why this milestone exists):

- **TRUTH-01's direction is deliberately undecided.** The roadmap does not pre-decide it. The plan
  MUST present an Alternatives Considered table covering at least (a) narrow the declaration and
  docs to what the code does, (b) implement `mirror` and `off`, (c) drop the key entirely — and
  MUST state, for the chosen option, what happens to a project that has already set
  `"sync_mode": "mirror"` or `"off"` expecting an effect. That migration answer is part of the
  requirement, not a follow-up. Precedent worth weighing: 0.3.1 already collapsed `read_epic_per`
  and `read_beads_enabled` into one `read_beads_config` reader, so a real reader for `sync_mode`
  has a shipped shape to slot into if (b) wins.
- **This milestone is explicitly gated.** `workflow.plan_check` and `workflow.verifier` are both
  on and stay on. The gh-2 fix shipped the same day on the quick path (no plan-check, no verifier)
  as v1.3.0, and a post-release four-lens review found a data-loss bug in the fix itself — a hook
  matcher firing on any command that merely *mentioned* its trigger string, reaching
  `strip_task_bodies` and deleting `PLAN.md` task prose. That needed a second tag (v1.3.1) and
  v1.3.0 was withdrawn. **No release tag is cut until CI is green on the exact commit being
  tagged.**
- **Edit the tracked source, not the runtime mirror.** `.gsd/capabilities/beads/` is gitignored
  (`.gitignore:41`) and re-synced from `plugins/beads-lifecycle/.gsd/capabilities/beads/`, which
  is the 17 git-tracked files. Phase 16 plan 01 got this backwards and it was caught in review.
- **Scope is truth-in-declaration, not reach.** No new config keys (Out of Scope), no rework of
  the `lifecycle-dispatch` hook matcher (shipped and regression-pinned in 0.3.1), REACH-01
  deferred.

**Plans**: 2 planned — one per requirement (17-01 → TRUTH-01 config truth + doc sweep;
17-02 → TRUTH-02 table-driven patch reader). TBD until `/gsd-plan-phase 17`.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 17. Config/Code Truth | 0/2 | Not started | - |

## Coverage

| Requirement | Phase |
|-------------|-------|
| TRUTH-01 | Phase 17 |
| TRUTH-02 | Phase 17 |

v1.3 requirements: 2 total, 2 mapped, 0 unmapped ✓
