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

- [x] **Phase 17: Config/Code Truth** - Every declared config value has an observable effect, decimal phases stop failing silently, the hook survives the upstream release that natively covers two of its five dispatch points, and the two patch-check clones become one reader (completed 2026-08-20)

## Phase Details

### Phase 17: Config/Code Truth

**Goal**: Everything this capability *declares* — a config enum, a set of lifecycle dispatch
points, a phase-number format, a patch marker — matches what its code actually does, verified by a
run rather than by prose. Four independent divergences close: a declared-but-unread config key
(plus every doc that describes its imagined effect), a phase-number format the code rejects while
this repo's own history contains it, a hook that will start double-dispatching the moment upstream
ships PR #3687, and two structurally-identical patch detectors carrying two copies of one body.

**Depends on**: Phase 16 (shipped) — `check_execute_plan_patch` and the `strip_task_bodies` gate it
feeds both landed there; TRUTH-02 collapses that phase's deliberate clone. Also depends on quick
task 260819-k4p (shipped as 0.3.1 / v1.3.1) — it created the `PostToolUse` `lifecycle-dispatch`
hook that TRUTH-03 makes forward-compatible, and the `allow_strip=False` protection whose bypass
TRUTH-03 must rule on.

**Requirements**: TRUTH-01, TRUTH-02, TRUTH-03, TRUTH-04 (4 of 4 — full v1.3 coverage)

#### Baselines — re-verified 2026-08-19 at commit `966315a`, gsd-core **1.11.0**

The prior revision of this section recorded its numbers on gsd-core 1.10.0 and before `966315a`.
Every one below was re-run for this revision. `966315a` inserted 11 lines above the `sync.py` call
sites, so **three previously-cited line numbers were wrong and are corrected here**.

| Baseline | Recorded on 1.10.0 | Observed now | Status |
|---|---|---|---|
| Test suite (`python3 -m unittest discover -s tests -t tests` from the capability root) | `Ran 164 tests … OK` | `Ran 164 tests in 4.740s … OK`, exit 0 | unchanged ✓ |
| `lifecycle_dispatch`'s back-to-back `plan:pre` pair | `sync.py:726-727` | **`sync.py:737-738`** | corrected (+11) |
| `strip_task_bodies` live re-gate inside `create_issues` | `sync.py:1369` | **`sync.py:1380`** (`if check_execute_plan_patch() == 0:`) | corrected (+11) |
| CLI dispatch for the two patch checks | `sync.py:2252` / `:2254` | **`sync.py:2263` / `:2265`** (parsers registered at `:2220` / `:2225`, flags at `:2223` / `:2228`) | corrected (+11) |
| `check_shipmd_patch` / `check_execute_plan_patch` definitions | not recorded | `sync.py:2049` / `sync.py:2114`; file is 2286 lines | new |
| Patch markers | not recorded | `SHIP_MD_PATCH_MARKER` `…v2` at `sync.py:110`; `EXECUTE_PLAN_PATCH_MARKER` `…v1` at `sync.py:115` — **different versions**, so a shared table needs a per-entry version field | new |
| Shipped versions | — | `plugin.json` `1.3.1`, `capability.json` `0.3.1` — both unchanged since the `v1.3.1` tag despite `966315a` on `main` | see ship checks |

**Success Criteria** (what must be TRUE):

1. **No declared-but-dead `sync_mode` value survives.** *(TRUTH-01)* A repo-wide
   `git grep -n sync_mode -- . ':!.planning'` resolves to exactly one of two end states: either
   every value `capability.json` still declares (today `authoritative | mirror | off` at
   `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:32-41`) is read by a code path
   in `sync.py` that a test exercises, or the key is no longer declared anywhere. No hit sits in a
   third state where a declaration has no reader. The description string at `capability.json:40`
   — *"'mirror' and 'off' are reserved for later phases"* — does not survive in any form that
   contradicts what `gsd-tools config-set beads.sync_mode <value>` accepts on the same day.

2. **No doc claims an effect the code does not have.** *(TRUTH-01)* Every surviving `sync_mode`
   mention reads true against the shipped code. The offender list, **re-grepped for this revision**
   (line numbers shifted since the prior draft): `CHANGELOG.md:37`, `CHANGELOG.md:83`,
   `README.md:139` (config-table row, *"Controls who owns task status and content"*),
   `README.md:147` (the sample `.planning/config.json` block), `README.md:177`,
   `docs/prd-beads-capability.md:41`, `docs/prd-beads-capability.md:149`, `.beads/PRIME.md:48`,
   `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md:59`, and the `create_issues` docstring +
   comment at `sync.py:1291-1302`. Specifically: nothing in the repo claims `beads.sync_mode` gates
   `strip_task_bodies` — the real gate is `check_execute_plan_patch()` at `sync.py:1380` plus the
   `allow_strip` flag added in 0.3.1. **Also in this sweep:** CHANGELOG 0.3.1's `timeout: 120`
   entry, currently filed under **Performance** as if it added protection, when the command-hook
   default is 600 s and 120 is a deliberate *reduction* — same false-claim class, two lines from
   the entries already being corrected. All corrected in the same commit as the code change.

3. **An existing `"sync_mode": "mirror"` / `"off"` project is answered, not orphaned.**
   *(TRUTH-01)* The documented outcome for a project that already wrote either value into its
   `.planning/config.json` is demonstrated by an actual run against such a config — it starts, does
   not crash, and behaves as documented. Research makes this criterion sharper than it looks: with
   the key dropped, an actual run produces **no observable output at all** (`config-get` returns
   the stale value, exit 0, zero stderr; gsd-core's unknown-key warning is top-level-only and never
   descends into a namespace; `validate health` has no capability-config rule), which is
   indistinguishable from a broken notice. So the demonstration must be of a channel the user hits
   **without acting** — `config-set` validation does not qualify, because it fires only when a user
   re-writes a key they will never re-write.

4. **One reader serves both patch checks, and both Python function names survive.**
   *(TRUTH-02)* `check_shipmd_patch` and `check_execute_plan_patch` no longer carry two copies of
   the same ~39-line body — the duplicated control flow exists once, in a `PATCH_CHECKS` table plus
   one parameterized reader (`check_patch`), each entry carrying its own `filename`, `marker`,
   `version` and message templates. `sync.py` is measurably shorter than its plan-17-03-end
   baseline. **One CLI verb reaches both targets**: `check-patch ship-md [--path]` and `check-patch
   execute-plan [--path]` replace the two prior single-target verbs and their per-target
   `--*-path` flags — a hard break with no alias window. Every caller (`beads-recall/SKILL.md`,
   `beads-status/SKILL.md`, `GSD-CORE-PATCH.md`) was updated in the same commit as the CLI change,
   and Task 1 of plan 17-04 landed the missing `--ship-md-path`-equivalent CLI coverage *before*
   the break was possible (D-09), closing this criterion's original untested-load-bearing worry.
   **D-08 (locked 2026-08-20, after a caller grep found no README exposure and no caller outside
   this repo) supersedes this criterion's original "both CLI subcommands and both flag spellings
   survive" clause** — what actually survives, and is what Criterion 5 depends on, is the two
   *Python function names* as thin wrappers over the shared reader.

5. **Every existing call site behaves identically, and the suite gains coverage rather than just
   staying green.** *(TRUTH-02)* All five call sites — the `lifecycle_dispatch` `plan:pre` pair at
   `sync.py:737-738`, the live `strip_task_bodies` re-gate at `sync.py:1380` (`== 0` semantics
   preserved verbatim; it is the last line of defence against the v1.3.0 data-loss mode), and the
   two CLI routes at `sync.py:2263`/`:2265` — produce unchanged output, with the assertions in
   `TestCheckShipmdPatch` and `TestCheckExecutePlanPatch` unedited. The suite reports **`>= 164`
   tests, OK** — *not* `== 164`: no test asserts either marker's literal version string today, so
   `966315a`'s v1→v2 change could have been a typo and 164/164 would still have passed. The merge
   adds one literal-marker assertion per table entry. A run that leaves the count at exactly 164
   has added no coverage for the thing it changed.

6. **A decimal-numbered phase works at all three beads lifecycle points.** *(TRUTH-04, P1)*
   Verified failing today, three ways, on this machine: `PLAN_FILE_RE` (`sync.py:72`, used at
   `:546`) matches `17-01-PLAN.md` but returns `False` for `11.1-01-PLAN.md` and `10.1-02-PLAN.md`,
   failing **silently** to an empty result at `execute:wave:*`; and `int(phase_num)` at
   `sync.py:634` (`get_phase_header`, `plan:post`) and `sync.py:1489` (`extract_phase_mentions`,
   `plan:pre`) raises `ValueError: invalid literal for int() with base 10: '01.5'`. After the fix,
   all three points resolve a decimal phase, exercised against this repo's **own** history as
   fixtures — `.planning/milestones/v1.1-phases/10.1-capability-auto-install-…` and
   `11.1-beads-enabled-default-flip-to-true`. Every hook is `onError: skip`, so today all three
   degrade quietly; the reporter observed 6 plans / 16 tasks complete with zero tickets and no
   failure surfaced. The `int()` is a leading-zero strip, not a type requirement. Precedent to
   match, not invent: the sibling `sota-numerics` capability already widened its own copy to
   `^\d+(?:\.\d+)?-\d+-PLAN\.md$` with a comment at `check-alternatives.py:34-37` naming beads'
   pattern as the too-narrow one.

7. **The `lifecycle-dispatch` hook does not double-dispatch when upstream PR #3687 ships.**
   *(TRUTH-03)* `POINTS` at `plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh:61` is currently
   `("plan:pre", "plan:post", "execute:wave:pre", "execute:wave:post", "verify:post")`. After this
   phase, `plan:post` and `verify:post` dispatch from the hook **only** on a gsd-core that does not
   dispatch them natively — gated on the installed version, not on a date — while
   `execute:wave:pre` and `execute:wave:post` dispatch unconditionally, because no upstream work
   covers those two anywhere (not released, not merged to `next`, not in an open PR). Checkable
   before #3687 releases: the gate is exercised by a test that simulates both an old and a new
   gsd-core. Separately and explicitly recorded, not discovered in production: **the `allow_strip`
   ruling.** Native dispatch invokes the `beads-sync` *skill*, which runs `sync.py create-issues`
   with `allow_strip` defaulting to `True`, whereas the hook path deliberately passes
   `allow_strip=False` (`sync.py:749`, added in 0.3.1 for gh-2). Whether an explicit registry
   dispatch is a different principal than a string-matched hook — and therefore whether the strip
   should return via the native path — is a decision this phase makes and writes down.

**Criterion → requirement coverage:** 1, 2, 3 → TRUTH-01 · 4, 5 → TRUTH-02 · 7 → TRUTH-03 ·
6 → TRUTH-04. All four requirements carry at least one criterion; every criterion traces to a
requirement.

#### Constraints carried into planning

**TRUTH-01's direction stays undecided at roadmap level.** This roadmap does not pre-decide
narrow / implement / drop. The plan MUST present an Alternatives Considered table covering at
least (a) narrow the declaration and docs to what the code does, (b) implement `mirror` and `off`,
(c) drop the key entirely — and MUST state, for the chosen option, what happens to a project that
already set `"sync_mode": "mirror"` or `"off"`. That migration answer is part of the requirement,
not a follow-up. **Research produced three findings the table has to engage with rather than
restate, and the three research documents do not agree with each other — the table must resolve
that disagreement, not average it:**

- **(b) has no declarative wiring channel.** `configValues` is resolved for `kind: "contribution"`
  only (`loop-resolver.cjs:244` is its sole call site) — the steps loop never calls it, and
  `beads-sync` is a step. `when:` is boolean-coerced (`capability-activation.cjs:104-107`), so the
  string `"off"` is truthy. `config-equals` is documented (`capability-manifest.md:117`) but
  unimplemented (`EVALUATOR_KINDS` frozen to two kinds at `gate-predicate-evaluator.cjs:37`). Only
  a self-read in `sync.py` remains — which is exactly how `beads.enabled` and `beads.epic_per`
  already work, so (b) is *possible*, just unwired. Separately, `off` largely duplicates
  `beads.enabled: false`, which already gates all six hooks.

- **Enum values ARE validated on write** — verified live, and this **corrects a claim the
  precedent research originally made in the opposite direction**: `config-set beads.sync_mode
  bogus` → `Error: Invalid beads.sync_mode 'bogus'. Valid values: authoritative, mirror, off`, and
  the value is not stored. They are **not** validated on read; a value hand-written into
  `.planning/config.json` is returned verbatim, forever, with no warning. So (a) is not
  mechanically inert — it starts rejecting a *new* `config-set … mirror` — but it detects no stale
  on-disk value either.

- **(c) removes the only error surface the key has.** Dropping it makes `config-set
  beads.sync_mode …` fail with a generic `Unknown config key` whose ~2000-character valid-key dump
  contains **no `beads.*` entry at all** — a user reads that as "beads config does not exist", not
  "this one key retired".

- **Precedent cuts toward (c); mechanism research cuts toward (a).** Precedent: 0 orphan keys
  across all four sibling plugins; `sota-numerics/capability.json:22` states the "declare one key,
  mean it" stance outright; gsd-core's one removal precedent (`runtime.hostBehaviors.reviewerCli`,
  #2801) is deletion-after-one-release-of-alias with a *warning, never an error*; narrowing an
  enum has **no precedent anywhere** in the corpus. Mechanism: narrowing keeps a live guard and
  keeps the key discoverable, dropping converts every existing `.planning/config.json` in the wild
  into permanently-unwarned dead weight. The plan picks one and says why the losing evidence loses.

**Includes the doc sweep, in the same commit as the code change.** Per the repo's "update all docs
in the SAME commit" rule. Leaving them would re-seed the divergence the requirement exists to close.

**TRUTH-02's merge is less safe than it looks.** The tests constrain five exact strings, not the
structure. `ship_override` and `gsd-executor` survive by assertion; the *unasserted* halves are
what vanish quietly under a shared template — ship's *"the ship_override step will not fire. The
two ship:pre GATES are unaffected…"* and its `(v2)` suffix, exec's *"gsd-executor will not read
task content from bd"* and its `(v1)`. Both are called back-to-back at `sync.py:737-738` inside
`lifecycle_dispatch`'s single `try/except Exception`, so an exception in a merged reader now takes
out `beads_recall` too — keep the merged reader total (it already catches `OSError` /
`UnicodeDecodeError`); do not introduce a `KeyError` path on an unknown table key.

**Neither patch is going away — the prior draft's open worry is RESOLVED.** The v1.2-era note read
*"if #3646 merges, `check_execute_plan_patch` is scheduled for deletion — re-check before planning
17-02."* Re-checked 2026-08-19 against the live repo: **#3646 is OPEN**, labelled
`approved-feature`, with **no PR**, and the maintainer's triage verdict attaches an explicit
blocking condition: *"Either resolution moves to a code-side seam in the executor's plan-reading
path, or this work sequences behind a fix to the dispatch-reliability family (#3606, #3647)."*
#3606 is fixed (PR #3687); **#3647 is open with no PR**. Condition 1 additionally requires an ADR
to land first. Therefore **Patch 2 and `check_execute_plan_patch` persist through v1.3 and beyond**,
and TRUTH-02 merges a function with a future, not one scheduled for deletion. Likewise Patch 1
(`ship.md` v2): #3687 does not touch `ship.md`, `ship:pre` is still gate-only on `next`, and no
upstream issue tracks the remaining half. The duplication to remove is **between** the two
checkers, not either checker itself.

**Edit the tracked source, not the runtime mirror — and prove they agree.** `.gsd/capabilities/beads/`
is gitignored (`.gitignore:41`) and re-synced from `plugins/beads-lifecycle/.gsd/capabilities/beads/`
(the 17 git-tracked files). Phase 16 plan 01 got this backwards and it was caught in review.
Worse, demonstrated this pass: `capability update beads` reports `"status": "upgraded"` for a
`0.3.1 → 0.3.1` no-op and **copies nothing**, and `.gsd-capabilities.json` pins `"integrity": ""`
so there is no content hash to fall back on. The hook resolves project-scope first
(`lifecycle-dispatch.sh:102-105`) while CI tests the plugin tree only — the exact "tests pass,
reality broken" shape that produced the v1.3.0 incident. **Precondition on every plan that touches
`sync.py`:** bump `capability.json` `version` in the *first* such commit (0.3.1 → 0.4.0), not at
ship time, then re-run `capability update beads`; and `diff -q` the two trees must be silent before
any behavioral claim about hook dispatch is accepted. (Both trees are identical today — this is a
guard, not a repair.)

**This milestone is explicitly gated.** `workflow.plan_check` and `workflow.verifier` are both on
and stay on. The gh-2 fix shipped the same day on the quick path (no plan-check, no verifier) as
v1.3.0, and a post-release four-lens review found a data-loss bug in the fix itself — a hook
matcher firing on any command that merely *mentioned* its trigger string, reaching
`strip_task_bodies` and deleting `PLAN.md` task prose. That needed a second tag (v1.3.1) and
v1.3.0 was withdrawn. **No release tag is cut until CI is green on the exact commit being tagged.**

**Scope is truth-in-declaration, not reach.** No new config keys (Out of Scope), no rework of the
`lifecycle-dispatch` hook *matcher* (shipped and regression-pinned in 0.3.1 — TRUTH-03 changes the
`POINTS` list, not the matcher), REACH-01 deferred.

#### Ship-step checks (release-hygiene debt inherited by this milestone)

Not requirements — defects in the current repo state that this milestone's ship step must clear.
Each is a mechanical command in the ship task, not a prose reminder.

1. **`main` is ahead of `v1.3.1` with a behavioral change, no version bump, no CHANGELOG entry.**
   `966315a` moved `SHIP_MD_PATCH_MARKER` v1 → v2 — a constant that flips `check_shipmd_patch`'s
   verdict on every machine still carrying v1 — while `plugin.json` still says `1.3.1` and
   `capability.json` still says `0.3.1`. Marketplace installs resolve `"source":
   "./plugins/beads-lifecycle"` from the **branch**, so consumers already have it. Check:
   `git diff --quiet <last-tag>..HEAD -- plugins .claude-plugin README.md` → if non-empty, both
   versions must differ from the last tag and CHANGELOG must have a section for the new capability
   version.

2. **CHANGELOG 0.3.1 mis-files the hook `timeout`** under Performance as added protection; 120 s is
   a *reduction* from the 600 s command-hook default. Corrected by Success Criterion 2's sweep;
   ship verifies it landed.

3. **The withdrawn `v1.3.0` tag still resolves** (`git merge-base --is-ancestor v1.3.0 HEAD` →
   yes) even though the GitHub Release is deleted — and deleting the release withdrew nothing that
   mattered, since marketplace installs came from the branch, not the zip. The real exposure was
   the branch window between `55855cd` and the fix in `049da5b`. Ship must either delete the tag
   from `origin` (noting that `release.yml` fires on **any** `v*.*.*` push, so a retag is a
   re-release and the tag cannot simply be moved) or add an explicit CHANGELOG line stating v1.3.0
   is withdrawn and why. Silence plus a live tag is the worst of both.

4. **`~/.claude/gsd-local-patches/` holds a stale v1 copy of the ship.md patch** while the live
   file carries v2; `backup-meta.json` records `"from_version": "1.10.0"`, and
   `node ~/.claude/gsd-core/bin/verify-reapply-patches.cjs` exits 1 on both files. Most of the 60+
   "missing" lines are 1.10.0 text that legitimately changed in 1.11.0 — false positives burying
   two real signals. On the next `/gsd-update --reapply` the v1 gate loop is a live candidate for
   reinstatement *alongside* 1.11.0's native one, silently undoing `966315a`. Refresh or delete the
   backup after the patch work lands, and name the mechanism in `GSD-CORE-PATCH.md`, which
   currently references it nowhere and reads as if manual reapplication is the only path.

5. **Assert `>= 164` tests, and that the two capability trees are identical**, before accepting any
   claim that CI green means the running code is the tested code (see the runtime-mirror
   constraint above).

**Plans**: 4 plans — one per requirement, one wave each, executed in the argued order below.

Plans:
**Wave 1**

- [x] 17-01-PLAN.md — decimal-phase support at all lifecycle points, plus the `capability.json` 0.3.1 → 0.4.0 bump and the runtime-mirror identity proof (TRUTH-04)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 17-02-PLAN.md — region-scoped native-dispatch probe gating `plan:post`/`verify:post`, and the `allow_strip` ruling wired to config on the explicit path only (TRUTH-03)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 17-03-PLAN.md — `beads.sync_mode` narrowed to values that do something, the D-04 migration notice, and the full doc sweep in the same commit (TRUTH-01)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 17-04-PLAN.md — one table-driven patch reader behind one collapsed CLI verb, with the missing coverage landing before the merge (TRUTH-02)

| Plan | Requirement | bd | Priority | Why here in the order |
|---|---|---|---|---|
| 17-01 | **TRUTH-04** — decimal-phase support at all three lifecycle points | `gsd-beads-bzl` | P1 | Highest severity, lowest cost, zero design ambiguity — and it is this phase's own insurance policy (see below) |
| 17-02 | **TRUTH-03** — hook forward-compatibility with upstream #3687 | `gsd-beads-he1` | P1 | Time-boxed by a release that can land at any cut |
| 17-03 | **TRUTH-01** — config truth + doc sweep | `gsd-beads-v43` | P1 | Not urgent; needs the Alternatives Considered table, which is thinking time, not clock time |
| 17-04 | **TRUTH-02** — table-driven patch reader | `gsd-beads-t7a` | P3 | Riskiest-per-unit-value change; lands on a `sync.py` the other three have already stabilised |

**Why four plans and not fewer.** Each requirement has its own bd ticket, its own verification
surface, and a different risk profile: a mechanical P1 bug fix, a time-boxed upstream-compat
change, an undecided design decision, and a pure refactor. Bundling any two would couple an
undecided direction (TRUTH-01) to a P1 correctness fix (TRUTH-04), or hide a P3 refactor's risk
inside a change that must ship fast. The one grouping worth considering — TRUTH-02 + TRUTH-04, both
`sync.py` — is rejected because they touch disjoint functions (`PLAN_FILE_RE`/`int()` at
`sync.py:72,634,1489` vs. `check_*_patch` at `:2049,:2114`) and merging them would put a P1 fix
behind a P3 refactor's review.

**Why this order, and why the phase does not split.** The urgency spread is real: TRUTH-04 is a P1
correctness bug that fails *silently* (`onError: skip` on every hook, so it has already cost this
repo 6 plans / 16 tasks of missing tickets with nothing surfaced); TRUTH-03 is time-boxed by an
upstream release that could land at any cut, after which the hook double-dispatches and the
`allow_strip` protection is bypassed without notice; TRUTH-01 and TRUTH-02 are not urgent by any
clock. That argues for **plan order**, not for a phase split, because all four share one
verification surface (the 164-test suite plus the two-tree identity check) and one ship gate —
splitting would duplicate that gate for no gain.

One concrete reason TRUTH-04 goes first rather than merely early: if #3687 ships mid-phase and
TRUTH-03 has to jump the queue, the mechanism for that is `/gsd-phase --insert`, which produces a
**decimal phase number** — precisely the input that is broken today. Fixing it first is what makes
the escape hatch usable. It is also the first commit to touch `sync.py`, so it carries the
`capability.json` 0.3.1 → 0.4.0 bump that every later plan depends on for a non-stale runtime
mirror.

Plans execute **sequentially, one wave each** — all four touch `sync.py` or its bundle, and each
must re-prove the two-tree identity and test-count guards before the next begins.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 17. Config/Code Truth | 4/4 | Complete    | 2026-08-20 |

## Coverage

| Requirement | Phase | Plan | bd |
|-------------|-------|------|-----|
| TRUTH-01 | Phase 17 | 17-03 | `gsd-beads-v43` (P1) |
| TRUTH-02 | Phase 17 | 17-04 | `gsd-beads-t7a` (P3) |
| TRUTH-03 | Phase 17 | 17-02 | `gsd-beads-he1` (P1) |
| TRUTH-04 | Phase 17 | 17-01 | `gsd-beads-bzl` (P1) |

v1.3 requirements: 4 total, 4 mapped, 0 unmapped ✓

### Phase 18: Address tech debt: patch-check doc accuracy + CHANGELOG

**Goal:** Every claim this capability makes about itself is true again, and nothing withdrawn,
stale, or already-fixed is still resolving: the patch-check docstring matches the code, every
patch-check problem message is uniformly marked and no consumer depends on that mark, the
CHANGELOG documents all four of Phase 17's requirements and files its own entries correctly, both
version declarations match what `main` actually carries, the withdrawn `v1.3.0` tag is gone, the
four already-shipped bd issues are closed, and both machine-local gsd-core patches are live again
on both runtime homes.

**Requirements**: None — this phase maps to no REQUIREMENTS.md ID. Its scope is audit-sourced:
`17-REVIEW.md` WR-01/WR-02/WR-03 (confirmed still open by `.planning/v1.3-MILESTONE-AUDIT.md`),
Ship-step checks #1/#2/#3/#4 from the Phase 17 section above, and a live bd-staleness finding
surfaced by this phase's own `beads-recall` dispatch. Decisions D-01..D-09 in `18-CONTEXT.md`.
**Depends on:** Phase 17
**Plans:** 4/4 plans complete

Plans:

**Wave 1**

- [x] 18-01-PLAN.md — reapply both machine-local gsd-core patches to both live runtime homes,
  reconcile the backup, and name the reapply-verification mechanism in `GSD-CORE-PATCH.md` (D-08).
  Highest urgency in the phase: both homes are currently unpatched, so `ship_override` does not
  fire and `gsd-executor` cannot read task content from `bd` for any phase, and the repo's own
  suite reports 6 failures because of it.

- [x] 18-02-PLAN.md — close the four already-shipped Phase 17 bd issues with verified identity, and
  delete the withdrawn `v1.3.0` tag from `origin` behind a one-way `checkpoint:decision`
  (D-09, D-07). Closes Ship-step check #3.

**Wave 2** *(blocked on 18-01: the suite-green gate cannot pass until the local patch is restored)*

- [x] 18-03-PLAN.md — mark all four unmarked `PATCH_CHECKS` problem messages with per-target tests,
  re-key both SKILL.md surfacing rules to `check-patch`'s exit code, and correct the false
  output-stream claim at both sites where it is made (D-01, D-02, D-03). Closes WR-01 and WR-02.

**Wave 3** *(blocked on 18-01, 18-02, 18-03 — it documents what they shipped)*

- [x] 18-04-PLAN.md — add the missing TRUTH-03 entry plus Phase 18's own changes to CHANGELOG 0.4.0,
  refile the 0.3.1 hook-timeout reduction under a correct heading, and bump `plugin.json` to
  `1.4.0` (D-04, D-05, D-06). Closes WR-03 and Ship-step checks #1 and #2.
