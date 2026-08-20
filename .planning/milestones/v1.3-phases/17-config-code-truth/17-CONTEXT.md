# Phase 17: Config/Code Truth - Context

**Gathered:** 2026-08-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Every declaration this capability makes — config keys, upstream citations, patch state — is true
against the code that actually runs; plus one P1 correctness fix (decimal phases) and
forward-compatibility with an upstream change already merged but unreleased.

Four requirements, four plans: TRUTH-04 (decimal phases), TRUTH-03 (#3687 forward-compat),
TRUTH-01 (`sync_mode`), TRUTH-02 (patch-checker merge). Scope is fixed by ROADMAP.md Phase 17.

</domain>

<decisions>
## Implementation Decisions

### `beads.sync_mode` disposition (TRUTH-01)

- **D-01: Implement `mirror`, drop `off`.** `values` becomes `["authoritative", "mirror"]`.
  `off` is removed because it duplicates `beads.enabled: false`, which is already implemented and
  already the documented opt-out. This rejects all three options the research converged on
  (narrow / drop / implement-both) in favour of a hybrid: the key stays, gains a second value that
  genuinely does something, and sheds the value that never had independent meaning.
  — **Reversibility:** costly — `values` is a published declaration in `capability.json`; removing
  `off` after users could have set it means a later re-add is a second config-contract change, and
  restoring it would require re-deciding what it means relative to `beads.enabled`.

- **D-02: `mirror` means "never strip PLAN.md task bodies".** `authoritative` keeps today's
  behavior — create issues, write back `beads_epic` / `<beads-id>`, and strip `<task>` bodies once
  `check_execute_plan_patch()` verifies the read-path patch is present. `mirror` does everything
  except the strip: bd receives the content, `PLAN.md` keeps it too.

  This maps exactly onto the existing `allow_strip` parameter added in 0.3.1, so implementation is
  wiring a config read to a flag that already exists — not new machinery. It also makes
  `capability.json`'s current description true rather than aspirational: "bd owns task status and
  task content after first sync" is precisely what `mirror` does *not* do.
  — **Reversibility:** costly — once `mirror` is real, a project relying on it to preserve
  `PLAN.md` prose depends on it; withdrawing it later re-enables destructive stripping for them.

- **D-03: The PostToolUse hook forces `mirror` behavior regardless of config.** The hook keeps
  passing `allow_strip=False` unconditionally, even under `authoritative`. Rationale: the hook
  fires on a **string match against a shell command** — a materially weaker principal than an
  explicit dispatch — and irreversible prose deletion must never be triggered by pattern matching.
  This is the exact failure that made v1.3.0 destroy `PLAN.md` content from a stray `rg` invocation.

  Config therefore governs the **explicit** paths only: `sync.py create-issues` invoked directly,
  and native gsd-core dispatch of the `beads-sync` skill once #3687 ships. The hook path is
  permanently conservative. Document this asymmetry — it is deliberate, not an oversight, and a
  future reader will otherwise "fix" it.
  — **Reversibility:** reversible — a one-line flag change at a single call site.

- **D-04: The migration answer is Claude's discretion, but must be stated explicitly in the plan.**
  Note the question inverted during discussion: implementing `mirror` means an existing
  `"sync_mode": "mirror"` project is no longer *stale* — it **starts behaving differently on
  upgrade** (stripping stops). That is presumably what such a user wanted, but it is a live
  behavior change on upgrade, not a no-op, and the CHANGELOG must say so. `off` is now the only
  value that needs a true removal-migration answer.

### Forward-compatibility with upstream #3687 (TRUTH-03)

- **D-05: Detect native dispatch by probing the installed workflow file, not by version number.**
  Grep the installed `plan-phase.md` / `verify-work.md` for the generic-dispatch text #3687 adds,
  exactly as `check_shipmd_patch` already greps for a patch marker. Chosen over version-sniffing
  because the release carrying #3687 does not exist yet, so a version constant cannot be filled in
  today; and over accepting double-dispatch because that leaves no signal when the hook becomes
  redundant.

  Failure mode is benign and must stay that way: a false negative (upstream reworded the prose)
  degrades to the current, working double-dispatch — never to a missed dispatch. Reuses this
  repo's established patch-detection discipline (Phase 16 D-05: re-verify every run, never assume).
  — **Reversibility:** reversible — a detection helper with one call site per point.

- **D-06: Native dispatch is a trusted principal; config governs it.** When #3687 ships, gsd-core
  dispatches the `beads-sync` skill explicitly. That is the intended mechanism and the strongest
  principal available, so `sync_mode` governs whether it strips — unlike the hook (D-03).

### Decimal-phase support (TRUTH-04)

- **D-07: Replace `int(phase_num)` with string leading-zero stripping plus `re.escape`.**
  `"01.5"` → strip leading zeros from the integer part → `"1.5"` → `re.escape` → `"1\.5"`, keeping
  the existing `0*` regex prefix so `Phase\s+0*1\.5\s*:` still matches both `### Phase 1.5:` and
  `### Phase 01.5:`. Preserves today's matching semantics for integer phases exactly while adding
  decimals.

  **`re.escape` is non-negotiable.** Both sites (`sync.py:634` `get_phase_header`, `sync.py:1489`
  `extract_phase_mentions`) interpolate the value straight into a regex. A bare `"11.1"` makes `.`
  a metacharacter matching any character — so `Phase 11X1:` would match. Rejected float/Decimal
  parsing: the value is only ever used to build a regex, so numeric typing buys nothing and
  reintroduces a parse that can raise plus formatting risk (`1.50`, `1.5000000001`).
  — **Reversibility:** reversible.

### Patch-checker merge (TRUTH-02)

- **D-08: Collapse to one parameterized CLI verb — hard break, no aliases.** The two public verbs
  `check-shipmd-patch` / `check-execute-plan-patch` are replaced by a single parameterized verb,
  and every caller is updated in the **same commit**, per this repo's "update all docs in the SAME
  commit as code changes" rule.

  Defensible because the break is fully contained: grep confirms **no README exposure and no
  caller outside this repo**. All call sites are `beads-recall/SKILL.md:72-73`,
  `beads-status/SKILL.md:146`, `test_sync.py:3069`, `GSD-CORE-PATCH.md` (4 mentions), and
  `.planning/intel/API-SURFACE.md:55-58` (regenerate). The `reviewerCli` alias-for-one-release
  precedent was considered and deliberately not followed, because it exists for externally-visible
  contracts and this one is not.
  — **Reversibility:** one-way — this is a published-plugin CLI contract change with no alias
  window. Undoing it means re-adding both verbs and a second round of doc updates. Anyone who
  scripted against `intel/API-SURFACE.md` breaks with no deprecation warning.

- **D-09: Add the missing `--ship-md-path` test coverage BEFORE the merge, not after.** Research
  found `--execute-plan-path` is pinned by a CLI test but `--ship-md-path` is not — so a careless
  merge keeps the suite at 164/164 green while silently breaking `beads-status/SKILL.md` Step 2d.
  The suite must be able to detect the contract break before the break is possible.

- **D-10: The table carries a per-entry marker version, and a new test asserts the literal marker strings.**
  The two markers are already at different versions (`ship-pre-generic-dispatch v2`,
  `execute-plan-bd-task-read v1`), so a single shared version field is wrong. No test asserts
  either marker today — which is how commit `966315a` changed `SHIP_MD_PATCH_MARKER` from v1 to v2
  with the suite still reporting green. That edit could have been a typo. Closing this satisfies
  the roadmap's tightened `>= 164` criterion.

### Claude's Discretion

- **Migration handling for an existing `sync_mode` value** (D-04) — silent no-op plus release note,
  or a one-time warning. Constrained: the plan must state the chosen answer explicitly, must cover
  both the `mirror`-becomes-meaningful case and the `off`-removed case, and must not invent a
  reader purely to deprecate.
- **The exact shape of the parameterized verb** (name, whether the target is a positional or a
  flag, how per-target path overrides are spelled) — constrained only by D-08's same-commit
  caller update and D-09's pre-merge coverage.
- **The internal table's data shape** (dict, list of tuples, dataclass) — constrained by D-10's
  per-entry version requirement.
- **Whether the release-hygiene debt lands as its own plan or folds into the last plan's ship
  step** — the debt is listed at the end of `REQUIREMENTS.md`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### This milestone's research (all written 2026-08-19, all verified against installed gsd-core 1.11.0)
- `.planning/research/STACK.md` — upstream gsd-core state. **Read first.** Establishes that #3687
  is merged to `next` but unreleased, that 1.11.0's #3608 fixed `ship:pre` **gate** dispatch only,
  and which local artifacts each finding does and does not make redundant.
- `.planning/research/ARCHITECTURE.md` — how `capability.json`'s `config` block actually works:
  `configValues` is contribution-only, `when:` is boolean-coerced, `config-equals` is documented
  but unimplemented. This is why D-02 uses a self-read rather than declarative wiring.
- `.planning/research/FEATURES.md` — config precedent across all installed and sibling
  capabilities. **Contains a correction block at item 2** written by the orchestrator: its original
  claim that `config-set` never validates enum values is FALSE and was verified false live. Read
  the correction, not the struck-through text.
- `.planning/research/PITFALLS.md` — observed-behavior hazards. §C1 (config removal is silent),
  the `--ship-md-path` coverage gap behind D-09, and the `gsd-local-patches` staleness.

### Prior phase decisions that carry forward
- `.planning/milestones/v1.2-phases/16-beads-issue-content-parity/16-CONTEXT.md` — D-05 (file
  upstream, run the local patch until merged, re-verify the marker every run rather than assuming),
  D-04 (bd-unreachable at execute time is a hard failure), D-07 (forward-only migration).

### The artifacts being changed
- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` — the `beads.sync_mode`
  declaration TRUTH-01 changes.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` — patch register; its
  "Scope" section states why only two patches exist, and Patch 1 is at v2 (step dispatch only).
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` — all four requirements touch
  this file.
- `plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh` — the hook D-03 and D-05 govern.

### Upstream, for verification not modification
- `open-gsd/gsd-core` PR **#3687** (merged to `next` 2026-08-19T20:41:28Z, unreleased) — the change
  D-05 probes for.
- `open-gsd/gsd-core` issue **#3559** / PR **#3608** — shipped in v1.11.0; fixed `ship:pre` gate
  dispatch. Note **#3554 is NOT the upstream track** — closed NOT_PLANNED, unreviewed.
- `open-gsd/gsd-core` **#3646** — OPEN, gated behind **#3647**; `check_execute_plan_patch` has a
  future, so TRUTH-02 merges two live checkers, not one scheduled for deletion.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`allow_strip` parameter** (`create_issues`, added 0.3.1) — D-02's `mirror` is exactly this flag
  driven by config instead of hardcoded. The behavior already exists and is already tested.
- **`read_beads_config(project_root, key, default)`** (`sync.py`, added 0.3.1) — the self-read
  helper `beads.enabled` and `beads.epic_per` already use. `sync_mode` slots straight in; each
  shipped default lives beside its key.
- **`check_shipmd_patch`'s marker-grep shape** — the model for D-05's native-dispatch probe. Same
  read-only, fail-open, name-the-path-checked discipline.
- **`sota-numerics`' widened regex** — `~/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:34-37`
  already solves TRUTH-04's pattern problem as `^\d+(?:\.\d+)?-\d+-PLAN\.md$`, with a comment
  naming beads' own pattern as the too-narrow one. Precedent to match rather than invent — but note
  it also drops the two-digit constraint, which is a deliberate choice to evaluate, not copy blindly.

### Established Patterns
- **Fail-open everywhere** — every lifecycle hook is `onError: skip`; `lifecycle_dispatch` always
  returns 0. Nothing added in this phase may break that.
- **Benign skips go to stderr, real output to stdout** — the hook promotes stdout to
  `additionalContext` and leaves stderr in the debug log.
- **The tracked source is `plugins/beads-lifecycle/.gsd/capabilities/beads/`.** `.gsd/capabilities/*`
  is gitignored (`.gitignore:41`) — it is a per-machine runtime overlay refreshed by the
  SessionStart hash-drift hook. Phase 16 plan 01 edited the wrong copy; do not repeat it.

### Integration Points
- `sync.py:72` `PLAN_FILE_RE`; `sync.py:634` `get_phase_header`; `sync.py:1489`
  `extract_phase_mentions` — TRUTH-04's three sites.
- `sync.py:737-738` (the `plan:pre` checker pair), `:1380` (the `strip_task_bodies` gate),
  `:2263`/`:2265` (CLI routes) — TRUTH-02's five call sites, line numbers re-verified at `966315a`.
- `hooks/lifecycle-dispatch.sh` gate 2 — where D-05's probe result gates `plan:post` / `verify:post`.

</code_context>

<specifics>
## Specific Ideas

- The user rejected all three researched options for `sync_mode` and supplied a fourth
  (`implement mirror, drop "off"`). The reasoning that makes it coherent: `off` was never a
  distinct behavior — it duplicated `beads.enabled: false` — while `mirror` names a behavior the
  capability already implements privately as `allow_strip=False`. The key stops being a dead
  declaration by *exposing existing behavior*, not by adding new machinery.
- The user overrode the recommendation on D-08 (collapse the CLI rather than keep both verbs).
  The recommendation had been made before grepping the callers; once it was established that
  nothing outside the repo references them, collapsing became the better-supported choice.

</specifics>

<deferred>
## Deferred Ideas

- **`REACH-01` — lifecycle dispatch on runtimes without `PostToolUse`.** Recorded in
  REQUIREMENTS.md under Future Requirements. Five of six points are Claude Code-only today;
  `.codex/hooks.json` and `.cursor/hooks.json` establish the per-runtime pattern. Explicitly out of
  v1.3, which is a truth-in-declaration milestone, not a reach milestone.
- **`RES-01` — `get-available-resources` capability.** Deferred from v1.2.
- **Refiling the generic `kind: "step"` dispatch gap upstream.** #3687 covers `plan:post` and
  `verify:post` only; `execute:wave:pre` / `execute:wave:post` have no upstream track at all, and
  #3554 was closed unreviewed for lacking the issue template. Filing a properly-templated issue is
  outward-facing work needing its own decision — not folded into this phase.

</deferred>

---

*Phase: 17-Config/Code Truth*
*Context gathered: 2026-08-20*
