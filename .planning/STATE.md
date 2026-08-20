---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Config/Code Truth (Phases 17-18) — FEATURE-COMPLETE
current_phase: 18
status: completed
stopped_at: Phase 18 complete — v1.3 feature-complete, awaiting /gsd-complete-milestone
last_updated: "2026-08-20T11:24:56.886Z"
last_activity: 2026-08-20
last_activity_desc: Completed quick task 260820-j6g (gsd-beads-72u fix)
state_head: 258cda685c0014da0d1f4962555657baa6051ca8
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 8
  completed_plans: 8
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-20)

**Core value:** gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero
duplicated task-state bookkeeping survives in `.planning/`.
**Current focus:** v1.3 milestone (Phases 17-18) feature-complete — awaiting `/gsd-complete-milestone v1.3`

## Current Position

Phase: 18
Plan: Not started
Status: All phases complete
Last activity: 2026-08-20 - Completed quick task 260820-j6g: Fix gsd-beads-72u: extend reconcile_stale_closed to also close standalone problem-report bd issues

Progress: [████████████████████] 8/8 plans (100%)

**Plan order is argued, not incidental** (full reasoning in ROADMAP.md Phase 17): TRUTH-04 is a P1
correctness bug that fails *silently* and it unblocks `/gsd-phase --insert` — the escape hatch this
phase itself would need if #3687 lands mid-flight; TRUTH-03 is time-boxed by an upstream release
that can land at any cut; TRUTH-01 and TRUTH-02 are not urgent by any clock. **Do not reorder
without re-reading that argument.** Note the numbering changed in this revision: 17-01/17-02 no
longer mean TRUTH-01/TRUTH-02.

**Gating for this milestone (non-negotiable):** `plan_check` and `verifier` both on; no release
tag until CI is green on the exact commit being tagged. Reason: the gh-2 fix shipped the quick
path on 2026-08-19 as v1.3.0 and a post-release review found a data-loss bug in the fix itself
(hook matcher fired on any command merely mentioning its trigger string, reaching
`strip_task_bodies` and deleting `PLAN.md` task prose). v1.3.0 withdrawn, v1.3.1 tagged.

**Phase 17 baselines — RE-VERIFIED 2026-08-19 on gsd-core 1.11.0 at commit `966315a`.** The
originals were recorded on 1.10.0 and before `966315a`, which inserted 11 lines above the `sync.py`
call sites:

- `python3 -m unittest discover -s tests -t tests` from
  `plugins/beads-lifecycle/.gsd/capabilities/beads/` → `Ran 164 tests in 4.740s ... OK`, exit 0.
  **Unchanged at 164.** Success Criterion 5 asserts `>= 164`, not `== 164` — no test asserts either
  marker's literal version string today.

- Corrected line numbers: `plan:pre` checker pair `726-727` → **`737-738`**; `strip_task_bodies`
  live re-gate `1369` → **`1380`**; CLI routes `2252`/`2254` → **`2263`/`2265`**.

- New, not previously recorded: `check_shipmd_patch` at `:2049`, `check_execute_plan_patch` at
  `:2114`, `SHIP_MD_PATCH_MARKER` (**v2**) at `:110`, `EXECUTE_PLAN_PATCH_MARKER` (**v1**) at
  `:115`, `sync.py` is 2286 lines. The two markers being at *different* versions is why a shared
  table needs a per-entry version field.

- TRUTH-04 failures reproduced directly: `PLAN_FILE_RE` (`:72`) → `11.1-01-PLAN.md` is `False`;
  `int('01.5')` → `ValueError` at `:634` and `:1489`.

## Performance Metrics

**Velocity:**

- Total plans completed (v1.2): 7
- Average duration: ~17min (Phase 13 P01-P04 + Phase 14 P01-P03)
- Total execution time: -

**Recent Trend:**

- Last 5 plans: -
- Trend: -

**Per-Plan Metrics (v1.0/v1.1, retained for velocity baseline):**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 09 P01 | 25min | 2 tasks | 4 files |
| Phase 09 P02 | 30min | 3 tasks | 7 files |
| Phase 09 P03 | 34min | 3 tasks | 9 files |
| Phase 09 P04 | 42min | 3 tasks | 1 files |
| Phase 10 P01 | 35min | 2 tasks | 6 files |
| Phase 10 P02 | ~20min | 3 tasks | 6 files |
| Phase 10.1 P01 | 15min | 2 tasks | 3 files |
| Phase 10.1 P02 | 12min | 3 tasks | 9 files |
| Phase 11 P01 | 35min | 3 tasks | 20 files |
| Phase 11 P02 | 30min | 2 tasks | 8 files |
| Phase 11 P03 | 20min | 3 tasks | 2 files |
| Phase 11.1 P01 | 12min | 2 tasks | 5 files |
| Phase 11.1 P02 | 8min | 3 tasks | 5 files |
| Phase 12 P01 | 18min | 4 tasks | 6 files |
| Phase 12 P02 | ~15min | 4 tasks | 7 files |
| Phase 12 P03 | ~20min | 2 tasks | 1 files |
| Phase 12 P04 | 12min | 2 tasks | 36 files |
| Phase 13 P01 | 20min | 3 tasks | 8 files |
| Phase 13 P02 | 15min | 2 tasks | 4 files |
| Phase 13 P03 | ~12min | 3 tasks | 118 files |
| Phase 13 P04 | 10min | 2 tasks | 2 files |
| Phase 14 P01 | ~25min | 2 tasks | 12 files |
| Phase 14 P02 | ~20min | 2 tasks | 4 files |
| Phase 14 P03 | ~25min | 2 tasks | 3 files |
| Phase 16 P01 | 14min | 2 tasks | 2 files |
| Phase 16 P02 | 5min | 3 tasks | 3 files |
| Phase 16 P03 | ~10min | 2 tasks | 2 files |
| Phase 16 P04 | 10 min | 3 tasks | 4 files |

Full v1.0/v1.1 per-plan history: `.planning/STATE-ARCHIVE.md`.

## Accumulated Context

### Decisions

Full decision log lives in PROJECT.md's Key Decisions table. Carried forward into v1.3 because
Phase 17 edits the exact surfaces these rows describe:

- **[v1.3, open]** TRUTH-01's direction is deliberately undecided at roadmap time. The plan must
  produce an Alternatives Considered table (narrow declaration+docs / implement `mirror` and `off`
  / drop the key) and must answer what happens to a project that already set
  `"sync_mode": "mirror"` or `"off"`. **The three research documents disagree, and the plan must
  resolve that rather than average it:** ARCHITECTURE.md recommends (a) narrow, FEATURES.md
  recommends (c) drop, PITFALLS.md C1 argues (a) over (c) on the grounds that dropping produces
  *zero* observable output for an existing user. Precedent for option (b): 0.3.1 already collapsed
  `read_epic_per` + `read_beads_enabled` into one `read_beads_config` reader, and `beads.epic_per`
  is the ecosystem's only working imperatively-read enum.

- **[v1.3, corrected]** `config-set` **does** validate enum values on write —
  `config-set beads.sync_mode bogus` → `Error: Invalid beads.sync_mode 'bogus'. Valid values: …`,
  value not stored. The earlier research claim that it validates only key existence was FALSE and
  was corrected by the orchestrator. The **read** path validates nothing: a hand-written value is
  returned verbatim forever, and gsd-core's unknown-key warning never descends into a namespace.

- **[v1.3, grounding]** `.gsd/capabilities/beads/` is a gitignored runtime mirror
  (`.gitignore:41`); the git-tracked source is `plugins/beads-lifecycle/.gsd/capabilities/beads/`
  (17 files). Phase 16 plan 01 edited the wrong one and it was caught in review. Compounding
  hazard found this pass: `capability update beads` reports `"status": "upgraded"` for a
  `0.3.1 → 0.3.1` no-op and copies **nothing**, and `.gsd-capabilities.json` pins
  `"integrity": ""`. Hence the precondition on every `sync.py` plan — bump `capability.json` to
  0.4.0 in the *first* such commit, then re-run `capability update`, then `diff -q` both trees.

  (upstream open-gsd/gsd-core#3559 filed, merge status unconfirmed). Any new gate must verify the
  patch marker is present and prove itself live via `gsd_run check predicate` before being trusted.

  post-consent edit silently deactivates the capability with no error. Re-consent after every edit.

  re-grants on drift; vendored into each plugin's `session-start.sh`.

  resolves its script path via `git rev-parse --show-toplevel`, not `${CLAUDE_PLUGIN_ROOT}`.

  stage-outside-tree → fix-relocation-paths → `gh repo create` + push → fresh-clone-verify sequence.

  URLs (commit `f706179`) — GitHub shorthand clones over SSH and breaks on SSH-keyless machines.

  `gsd-beads` in the same commit that repaired the orphaned `ci.yml` / `release.yml` references —
  was found false during quick-task 260818-h2h: `git log --follow` showed no deletion commit ever
  existed for `.gsd/capabilities/{ponytail,sota-numerics}`, only their Phase 10/11 authoring
  commits (`932cf34`, `246dfbc`). Whatever Phase 12 removed, it was not these two paths. They were
  actually removed in quick-task 260818-h2h, by `git rm -r`, in the same commit that scoped the
  `beads-lifecycle` plugin source to `plugins/beads-lifecycle/`.

- [Phase ?]: [Phase 16, plan 01]: Edited plugins/beads-lifecycle/.gsd/capabilities/beads/ (the git-tracked plugin source) instead of the plan-specified .gsd/capabilities/beads/, which is a gitignored runtime-install mirror silently re-synced from the tracked source
- [Phase ?]: [Phase 16, plan 01]: get_milestone_bullet fails open (returns empty string on a miss) unlike its get_phase_header model, since resolve_milestone_epic must stay fail-open per B6/D-08
- [Phase ?]: [Phase 16, plan 02]: reconcile_stale_closed composes existing _resolve_completed_task_ids + filter_open_ids as a phase-wide idempotent close backstop for D-08, dispatched at verify:post before regenerate-beads-md
- [Phase ?]: [Phase 16, plan 02]: closed the four stale Phase 14 issues (gsd-beads-bu0.3-.6) live via the new reconcile-stale-closed subcommand, proving the backstop on real data
- [Phase ?]: [Phase 16, plan 03]: check_execute_plan_patch clones check_shipmd_patch's exact detector shape for the machine-local execute-plan.md bd-task-read patch (D-05) — **this clone is exactly what TRUTH-02 collapses in Phase 17, plan 17-04**
- [Phase ?]: [Phase 16, plan 03]: strip_task_bodies turns a newly-created auto/tracer task block into name+beads-id+files+pointer, gated on check_execute_plan_patch()==0 and scoped to task_updates (this run's created ids only) -- checkpoint:* blocks and pre-existing tasks stay byte-identical (D-01/D-03/D-07)
- [Phase ?]: Second machine-local gsd-core patch (execute-plan.md bd task-read) installed under the same N2-exception discipline as ship.md; filed upstream as open-gsd/gsd-core#3646 with an explicit revert condition
- [Phase ?]: Filed open-gsd/gsd-core#3647 (capability lifecycle-dispatch reliability finding) as a distinct-but-related report alongside pre-existing #3606, rather than adopting it as a duplicate
- **[Phase 18, plan 18-02]** Checkpoint `v1.3.0` tag deletion answered live by user (2026-08-20): **option-a** — deleted from `origin` and locally. `v1.3.1` untouched, no `release.yml` run fired.
- **[Phase 18, plan 18-02]** `reconcile_stale_closed`'s bd backstop only reaches `<beads-id>`-linked plan-task issues, not standalone problem reports — filed as follow-up `gsd-beads-72u`, out of Phase 18 scope by design.
- **[Phase 18, orchestrator]** Worktree isolation does not carry `.beads/` (untracked) — `bd` calls inside an isolated executor worktree must be pinned with `-C <main-repo-root>` to reach the real issue database; `git` ref ops are unaffected (shared `.git` store).

### Pending Todos

None yet.

### Blockers/Concerns

- **[NEW 2026-08-19] `pr-workflow` sync-point dispatch degraded (execute:wave:post, phase 17 wave 1).** `capability.json` lists `pr-workflow.enabled: true`, but only the `beads` capability is actually vendored under `.gsd/capabilities/` in this repo — `pr_status.py` does not exist. The `onError: skip` contract absorbed it (no phase impact), but the config/vendoring mismatch is real: either disable `pr-workflow` in `.planning/config.json` or vendor the capability.

- **[RESOLVED 2026-08-19] [open-gsd/gsd-core#3646](https://github.com/open-gsd/gsd-core/issues/3646)
  — `check_execute_plan_patch` is NOT scheduled for deletion.** The prior standing worry was *"if
  #3646 merges, `check_execute_plan_patch` is scheduled for deletion — re-check before planning
  17-02."* Re-checked live: **#3646 is OPEN**, labelled `approved-feature`, with **no PR**, and the
  maintainer's triage verdict (trek-e, 2026-08-19) attaches an explicit blocking condition —
  *"Either resolution moves to a code-side seam in the executor's plan-reading path, or this work
  sequences behind a fix to the dispatch-reliability family (#3606, #3647)."* #3606 is fixed
  (PR #3687); **#3647 is open with no PR.** Condition 1 additionally requires an ADR to land first.
  **Therefore Patch 2 and `check_execute_plan_patch` persist through v1.3 and beyond**, and the
  TRUTH-02 merge (now plan 17-04) is safe: it collapses duplication *between* two checkers that
  both have a future, not one on death row. Patch 1 (`ship.md` v2) is likewise safe — #3687 does
  not touch `ship.md`, `ship:pre` is still gate-only on `next`, and no upstream issue tracks the
  remaining half.

- **[RESOLVED 2026-08-20, plan 17-02] [open-gsd/gsd-core#3687](https://github.com/open-gsd/gsd-core/pull/3687)**
  — merged to `next` 2026-08-19T20:41:28Z, still unreleased as of Phase 17 completion. `check_native_step_dispatch`
  now gates the hook's `plan:post`/`verify:post` branches on live probing of the installed gsd-core workflow
  files, not a version guess — correct today (1.11.0, no native dispatch, both correctly report not-detected,
  live-verified) and correct the moment #3687 releases. `allow_strip` stays a literal `False` on the hook path
  regardless. The hook itself was NOT deleted — `execute:wave:pre`/`execute:wave:post` still have no upstream
  fix. Re-run the upstream release check before shipping v1.3, as a final confirmation, not because the code
  depends on the outcome.

- **[open-gsd/gsd-core#3647](https://github.com/open-gsd/gsd-core/issues/3647)** filed as a
  framework-level observation (capability lifecycle-dispatch steps intermittently skipped). Open,
  labelled `bug` / `ready-for-human`, no PR. It now also gates #3646 (above). No local patch
  corresponds to it; this project's own `reconcile-stale-closed` backstop already covers the local
  symptom regardless of upstream disposition.

- **[RESOLVED 2026-08-20, Phase 18]** Release hygiene — all four items closed: (1) `plugin.json`
  bumped to `1.4.0`, CHANGELOG 0.4.0 now documents TRUTH-03; (2) CHANGELOG 0.3.1's 120s hook
  timeout refiled from Performance to Changed; (3) withdrawn `v1.3.0` tag deleted from `origin`
  and locally (18-02, option-a), `v1.3.1` untouched, no `release.yml` run fired; (4) both
  machine-local gsd-core patches (`ship.md` v2, `execute-plan.md` v1) reapplied and verified live
  on both `~/.claude` and `~/.codex` runtime homes (18-01) — `check-patch` exits 0 on all 4
  file×home combos, full suite green at 252 tests.

- **[v1.1 formality, carried forward]** Phase 12's work is done and pushed but the v1.1 milestone
  was never formally closed via `/gsd-complete-milestone` (user decision, 2026-08-18) — its
  RETROSPECTIVE.md section is also missing as a result. Not a v1.3 blocker, but worth a
  retroactive backfill if the gap starts costing real time.

- **[Phase 16, one unverified path]** No real stripped `PLAN.md` has run through a live
  `gsd-executor` session yet in this repo — the bd-read patch's branch-trigger conditions are
  UAT-verified live against real `bd` (throwaway fixture, simulated failure, a genuine
  pre-migration issue), not exercised end-to-end. Will self-resolve the first time a future
  phase's `auto`/`tracer` tasks actually get stripped and executed.

- **[carried, unresolved by research]** Whether a manually-invoked `/gsd:plan-phase` reaches
  `plan-phase.md` §5.6's generic `plan:pre` step loop. `GSD-CORE-PATCH.md` asserts it does not;
  the live 1.11.0 file text suggests it does. Bears on whether the hook's `plan:pre` entry is
  already redundant today. Needs a live run, not a read. Confidence in the repo's claim: low (60).

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260815-mm8 | Fix gsd-beads-uh1 and gsd-beads-bgb | 2026-08-15 | cb0741e | | [260815-mm8](./quick/260815-mm8-fix-gsd-beads-uh1-create-issues-epic-per/) |
| 260818-h2h | Fix gsd-beads-1iq: scope beads-lifecycle marketplace source to exclude sota-numerics/ponytail dev copies | 2026-08-18 | 4d83504 | Verified | [260818-h2h](./quick/260818-h2h-fix-gsd-beads-1iq-scope-beads-lifecycle-/) |
| 260819-e7a | Revise README.md with a full gsd-beads configuration reference section | 2026-08-19 | 640ccc3 | | [260819-e7a](./quick/260819-e7a-revise-readme-md-with-a-full-gsd-beads-c/) |
| 260819-k4p | Fix gh-2: dispatch the four lifecycle hooks gsd-core never reached (capability 0.3.0 / plugin 1.3.0) | 2026-08-19 | 62162d4 | Verified | [260819-k4p](./quick/260819-k4p-fix-gsd-beads-2-lifecycle-hook-dispatch/) |
| 260820-j6g | Fix gsd-beads-72u: extend reconcile_stale_closed to also close standalone problem-report bd issues via opt-in SUMMARY.md `resolves_issues:` frontmatter marker | 2026-08-20 | ed027be | | [260820-j6g](./quick/260820-j6g-extend-reconcile-stale-closed-to-also-cl/) |

### Roadmap Evolution

- Phase 18 added: Address tech debt: patch-check doc accuracy + CHANGELOG
- Phase 18 complete 2026-08-20 (4/4 plans) — v1.3 milestone (Phases 17-18) now fully feature-complete

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Capability | `get-available-resources` (RES-01) | Deferred to v2 — no "compute-heavy phase" signal exists in gsd-core to consume the advisory yet | v1.2 requirements, 2026-08-18 |
| Gate maturity | `pr-workflow.ship_gate` → blocking (PRW-05) | Deferred to v2 — needs one real PR cycle first | v1.2 requirements, 2026-08-18 |
| Gate maturity | `markdown-linting.ship_gate` → blocking (MDL-05) | Deferred to v2 — needs a clean full-milestone run first | v1.2 requirements, 2026-08-18 |
| Runtime reach | Lifecycle dispatch outside Claude Code (REACH-01) | Deferred — v1.3 is truth-in-declaration, not reach | v1.3 requirements, 2026-08-19 |
| Atomic write | `create_issues`' non-atomic `plan_path.write_text` (`sync.py:1388`) — a timeout cancellation inside it truncates `PLAN.md`, the same file the v1.3.0 incident destroyed | Not a standalone task; fold in only if a plan already opens that function, else file as bd | v1.3 pitfalls research, 2026-08-19 |
| Doc debt | `PostToolUse` no longer fires on failed tool calls (`PostToolUseFailure` split off) — one header sentence in `lifecycle-dispatch.sh` | Optional, attach to whichever plan already touches the hook | v1.3 pitfalls research, 2026-08-19 |

## Session Continuity

Last session: 2026-08-20T11:27:44.000Z
Stopped at: Phase 18 complete — v1.3 milestone (Phases 17-18) feature-complete, ready to plan next
All 4 plans executed and verified (9/9 must-haves, 252/252 tests green, deep code review clean of
blockers — 0 critical, 1 warning, 2 info). Plan 18-02's checkpoint:decision (withdrawn `v1.3.0` tag
deletion, D-07) was confirmed live by the user (option-a, delete from origin + local).
Resume file: None

## Operator Next Steps

- **[DONE 2026-08-20]** Security gate closed for both phases: `17-SECURITY.md` (21/21 threats
  closed, `threats_open: 0`) and `18-SECURITY.md` (17/17 threats closed, `threats_open: 0`,
  all mitigate-dispositioned threats live-reverified, not just claimed). `beads.ship_gate` is
  no longer blocked on security for either phase.

- The 5 non-blocking WARNING findings from `17-REVIEW.md` and the 1 from `18-REVIEW.md` remain
  open (all doc/test-truth gaps, none functional). Consider `/gsd-code-review 17 --fix` and/or
  `/gsd-code-review 18 --fix`, or a follow-up quick task.

- Follow-up bd issue `gsd-beads-72u` filed by Phase 18 (reconcile_stale_closed cannot reach
  standalone problem-report issues) is open and unscheduled — not a v1.3 blocker.

- Once ready: `/gsd-complete-milestone v1.3` — Phases 17 and 18 are both complete, no other
  active workstreams block the close.
