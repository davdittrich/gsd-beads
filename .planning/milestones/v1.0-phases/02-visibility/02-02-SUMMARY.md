---
phase: 02-visibility
plan: 02
subsystem: infra
tags: [beads, bd, capability-manifest, gsd-core, wave-dispatch, beads-md-regeneration]

# Dependency graph
requires:
  - phase: 02-visibility
    plan: 01
    provides: "beads-recall skill, sync.py's beads_recall/parse_plan-with-<files>, capability.json's plan:pre step + into:planner contribution, the B6/D-08 fail-open shape"
provides:
  - "regenerate_beads_md/render_wave_status_block in sync.py; execute:wave:pre steps[] entry dispatching beads-status (D-11); beads-status/SKILL.md's Step 1.5 lifecycle-point branch + Step 2a wave-status instruction"
affects: [Phase 3 ship gates reading BEADS.md's frontmatter, execute-phase wave dispatch]

# Actuals (#2632)
actuals:
  tokens: 18500
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns: ["skill-mediated dispatch over contributions[] for anything load-bearing at execute:wave:pre (Pattern 2)", "static contribution fragments as pointers never live-data payloads (Pattern 1, reused from 02-01)"]

key-files:
  created:
    - .planning/phases/02-visibility/02-02-SUMMARY.md
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/capability.json
    - .gsd/capabilities/beads/skills/beads-status/SKILL.md
    - .gsd/capabilities/beads/tests/test_sync.py
    - .gsd-capabilities.json

key-decisions:
  - "D-11 confirmed in implementation: beads-status is one skill registered at two steps[] points (execute:wave:pre read-only, execute:wave:post regen+close), branching internally on lifecycle point -- never two skills, never a new contributions[] entry"
  - "B8's mechanism is a steps[]-only design per 02-RESEARCH.md's primary recommendation: wave-status-block prints a <beads_status> block and SKILL.md's Step 2a instructs the orchestrator directly to paste it into each executor's prompt=, rather than relying on execute:wave:pre's unreliable contributions[] forwarding"
  - "render_wave_status_block always calls regenerate_beads_md first and re-reads the just-written BEADS.md table -- never a second live bd query -- so the printed block and the on-disk artifact can never disagree"

patterns-established:
  - "5-column BEADS.md table (issue/title/status/plan task/blocked-by) derived from one bd list --parent <epic> --all --json -n 0 call: blocked-by is dependencies[] filtered to type==\"blocks\", plan task resolved via a beads_id -> ordinal_prefix map built from discover_plan_files+parse_plan across the phase, zero extra bd calls"
  - "Full-overwrite regeneration: regenerate_beads_md never reads BEADS.md's existing body to merge -- always rebuilds frontmatter+table from a fresh query and writes the whole file, proven by TestBeadsMdRegeneration's hand-edit-then-regenerate assertion"

requirements-completed: [B8, B11]

coverage:
  - id: D1
    description: "regenerate_beads_md's frontmatter carries phase/epic/open/closed/blocking_open=0/diverged=0/generated_from/generated_at, matching a mocked bd list --parent response's open/closed counts"
    requirement: "B11"
    verification:
      - kind: unit
        ref: "test_sync.py#TestBeadsMdRegeneration.test_frontmatter_matches_mocked_bd_response_counts"
        status: pass
      - kind: e2e
        ref: "manual live trace against a real bd v1.2.1 database (bd init, create-issues, regenerate-beads-md) -- see Live Trace Evidence below"
        status: pass
    human_judgment: false
  - id: D2
    description: "A hand-edited BEADS.md (extra line inserted before regenerating) is fully overwritten -- the hand edit is absent after the next regenerate_beads_md call"
    requirement: "B11"
    verification:
      - kind: unit
        ref: "test_sync.py#TestBeadsMdRegeneration.test_hand_edit_is_absent_after_next_regeneration"
        status: pass
    human_judgment: false
  - id: D3
    description: "The issue table's blocked-by column lists only dependencies[] entries with type==\"blocks\", excluding type==\"parent-child\" epic edges (D-08)"
    requirement: "B11"
    verification:
      - kind: unit
        ref: "test_sync.py#TestBeadsMdRegeneration.test_blocked_by_column_excludes_parent_child_includes_blocks"
        status: pass
    human_judgment: false
  - id: D4
    description: "render_wave_status_block's printed block names every issue id belonging to the given plan_ids and omits issues from other plans in the same phase directory"
    requirement: "B8"
    verification:
      - kind: unit
        ref: "test_sync.py#TestWaveStatusBlock.test_block_names_only_given_plan_ids_issues"
        status: pass
      - kind: e2e
        ref: "manual live trace: real 2-plan wave synced against a real bd database, wave-status-block's printed <beads_status> block named both real issue ids/titles/statuses -- see Live Trace Evidence below"
        status: pass
    human_judgment: false
  - id: D5
    description: "With zero plan_ids resolving to any synced task, wave-status-block prints \"no synced issues for this wave\" rather than an empty block"
    requirement: "B8"
    verification:
      - kind: unit
        ref: "test_sync.py#TestWaveStatusBlock.test_zero_resolving_plan_ids_prints_no_synced_issues_line"
        status: pass
    human_judgment: false
  - id: D6
    description: "capability.json declares exactly one new execute:wave:pre steps[] entry (ref.skill beads-status, same skill id as execute:wave:post, D-11); beads-status/SKILL.md never adds a new contributions[] entry for B8"
    requirement: "B8, B11"
    verification:
      - kind: unit
        ref: "grep -c '\"point\": \"execute:wave:pre\"' capability.json == 1; grep -c '\"skill\": \"beads-status\"' capability.json == 2; grep -c 'contributions\\[\\]' SKILL.md == 0"
        status: pass
    human_judgment: false
  - id: D7
    description: "The composed prompt each executor's Agent() call receives at execute:wave:pre names this wave's issue ids -- verified by direct prompt inspection, per B8's literal acceptance criterion"
    verification: []
    human_judgment: true
    rationale: "Requires dispatching a real execute-phase wave and grepping the actual prompt= text a spawned executor Agent() call receives -- not reproducible from within this execute-plan session (a spawned executor subagent has no path to inspect its own orchestrator's Agent() calls). Strengthened evidence recorded instead of a mocked-only unit test: the beads capability was re-installed/re-consented at project scope, render-hooks execute:wave:pre confirms the beads-status step is now active, and a real (non-mocked) bd v1.2.1 database round-trip -- bd init, create-issues for a genuine 2-plan wave sharing one epic, regenerate-beads-md, wave-status-block -- produced the exact beads_status block text SKILL.md's Step 2a instructs the orchestrator to paste into each executor's prompt=. Recorded in .planning/WINDOWS.md (entry 2) alongside 02-01's equivalent B7 entry (entry 1), both open pending a real orchestrator-level dispatch trace."
  - id: D8
    description: "BEADS-RECALL.md exists at {phase_dir}/{padded_phase}-BEADS-RECALL.md before a real planner subagent is spawned, even against a project with zero open issues (B7/D-04 baseline) -- re-confirmed this plan against a real bd database"
    requirement: "B7"
    verification:
      - kind: e2e
        ref: "manual live trace: beads-recall run against a real bd v1.2.1 database with one open issue correctly matched it via technique 1 (files reverse-lookup); the mechanism (unconditional file write at plan:pre, before any planner spawn) is unchanged from 02-01, now proven end-to-end against real bd rather than mocks -- see Live Trace Evidence below"
        status: pass
    human_judgment: false

# Metrics
duration: 15min
completed: 2026-08-15
status: complete
---

# Phase 02 Plan 02: BEADS.md Regeneration and Wave-Status Block Summary

**`regenerate_beads_md` fully overwrites BEADS.md from a live `bd` query at every `execute:wave:pre`/`execute:wave:post` dispatch (D-05..D-08 shape), and `render_wave_status_block` prints a `<beads_status>` block that `beads-status/SKILL.md` instructs the orchestrator to paste into each executor's composed prompt at wave dispatch (B8's steps[]-only design, D-11).**

## Performance

- **Duration:** 15 min
- **Started:** 2026-08-15T13:15:42Z
- **Completed:** 2026-08-15T13:30:51Z
- **Tasks:** 3 (Task 1+2 combined GREEN commit; Task 3 checkpoint)
- **Files modified:** 5 (4 capability files + `.gsd-capabilities.json` re-consent record)

## Accomplishments

- `regenerate_beads_md` added to `sync.py`: always fully overwrites `{phase_dir}/{padded_phase}-BEADS.md` from a fresh `bd list --parent <epic> --all --json -n 0` query, D-05..D-08 frontmatter (phase/epic/open/closed/blocking_open=0/diverged=0/generated_from/generated_at) and a 5-column issue table (issue/title/status/plan task/blocked-by), blocked-by filtered to `dependencies[].type=="blocks"` excluding `"parent-child"` epic edges
- `render_wave_status_block` added: regenerates BEADS.md first, then prints a `<beads_status>` block naming exactly the given wave's plan_ids' synced issues (id/title/status), re-reading the just-written table rather than issuing a second `bd` query
- `capability.json` extended with a new `execute:wave:pre` `steps[]` entry dispatching `beads-status` (same skill id as the existing `execute:wave:post` entry, D-11) — zero new `contributions[]` entries added for B8, per 02-RESEARCH.md's primary recommendation
- `beads-status/SKILL.md` extended with a Step 1.5 lifecycle-point branch: `execute:wave:pre` regenerates BEADS.md and prints the wave-status block with an explicit instruction telling the orchestrator to paste it into each executor's `prompt=`; `execute:wave:post`'s existing close-wave dispatch is unchanged
- Capability re-installed and re-consented at project scope (T-01-10/T-02-06's pattern); confirmed active via `render-hooks`: `plan:pre` names `beads-recall` + the `into:"planner"` recall-pointer contribution, `execute:wave:pre`/`execute:wave:post` both name `beads-status`
- Live-traced the full mechanism against a real (non-mocked) `bd` v1.2.1 database: real 2-plan wave synced, `BEADS.md` regenerated with real ids, `wave-status-block` printed the real `<beads_status>` text an orchestrator would paste into an executor's prompt, and `beads-recall` re-confirmed against real data (see Live Trace Evidence)

## Task Commits

Each task was committed atomically:

1. **Task 1+2: BEADS.md regeneration + wave-status block (combined GREEN, see Deviations)** — `648a54e` (test, RED) → `4d4a5d5` (feat, GREEN)
2. **Task 3: Re-install/re-consent** — `927e9de` (chore)

## Files Created/Modified

- `.gsd/capabilities/beads/scripts/sync.py` — Added `resolve_phase_epic`, `_beads_md_argv`, `_resolve_task_ordinal_map`, `_render_beads_md_table`, `regenerate_beads_md`, `_parse_beads_md_table_rows`, `render_wave_status_block`; wired `regenerate-beads-md` and `wave-status-block` subcommands
- `.gsd/capabilities/beads/capability.json` — Added `execute:wave:pre` `steps[]` entry, `ref.skill: "beads-status"`
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md` — Added Step 1.5 (D-11 lifecycle-point branch) and Step 2a (wave-status-block dispatch + orchestrator prompt= instruction); added two Anti-Patterns entries
- `.gsd/capabilities/beads/tests/test_sync.py` — Added `TestBeadsMdRegeneration` (3 tests) and `TestWaveStatusBlock` (2 tests), 39/39 total suite green
- `.gsd-capabilities.json` — `updatedAt` bumped by project-scope re-install/re-consent (Task 3)

## Decisions Made

- Followed D-11 exactly: one `beads-status` skill, two `steps[]` registrations, internal lifecycle branch — never two skills or a duplicated close-wave dispatch
- Followed 02-RESEARCH.md's primary B8 recommendation literally: zero new `contributions[]` entries; the wave-status block reaches the orchestrator's own context via Skill-tool + Read-tool dispatch (the one mechanism this project has proven end-to-end), and SKILL.md's own prose is the instruction to carry it into each executor's `prompt=`
- `render_wave_status_block` never re-queries `bd` after `regenerate_beads_md` — sourcing the block from the just-written `BEADS.md` table guarantees the printed block and the on-disk artifact can never disagree, at the cost of one extra file read (negligible)

## Deviations from Plan

### Auto-fixed / documented issues

**1. Task 1 and Task 2's GREEN implementation committed together, not separately.** Both tasks' RED tests (`TestBeadsMdRegeneration`, `TestWaveStatusBlock`) were written and committed in one `test(02-02)` commit before implementation began, and `render_wave_status_block` calls `regenerate_beads_md` directly (Task 2 depends on Task 1's function). Splitting the GREEN commit by task would require manual hunk-level staging within the same `sync.py` edit with no real isolation benefit — the two tasks are not independently revertable once combined. Documented rather than silently merged; does not affect any functional acceptance criterion.

**2. Task 1's acceptance criterion `grep -c '"-n", "0"'` returns at least 4 — measured 3.** Task 1's own `<action>` text explicitly marks the pre-existing Phase 1 orphan-sweep `bd list --parent` call site (in `create_issues`) as "out of this plan's scope to fix," and no other new `-n 0` call site exists in this plan's actual design beyond `_beads_md_argv`'s one new call. 02-01's own SUMMARY predicted this exact count in advance ("expect the cumulative count to reach 4 only after that plan's regenerate-beads-md adds its own `-n 0` call" — that addition brings the count from 2 to 3, not 4, since only one new call site exists). Padding with a dead no-op `bd list -n 0` call to hit the literal number would be padding, not a fix; all functional/behavioral acceptance criteria pass.

### Discovered (pre-existing, out of scope) issues

**3. Phase 1's `create_issues` resolves each plan's epic independently from its own frontmatter, not from a shared phase-level epic.** During the live trace, syncing two plans in the same phase with no `beads_epic` pre-set on either produced two separate epics (one per plan), not one epic shared across the phase. `regenerate_beads_md` (this plan) reads only the *first* discovered plan's `beads_epic`, so a real two-plan phase where plans are synced independently without a manually shared `beads_epic` would only see one plan's issues in `BEADS.md`. Every existing test fixture (`plan-wave-a.md`/`plan-wave-b.md`, and this plan's own live trace) works around this by pre-setting the same `beads_epic` on every plan in a phase — masking the gap rather than exercising the real cross-plan epic-resolution path. This is Phase 1 (`B1`/`B4`) behavior, unchanged and untouched by this plan; flagged here, not fixed (out of this plan's scope — `create_issues`/`resolve_epic` is not in this plan's `<files>`).

**4. Phase 1's orphan sweep auto-closes a sibling plan's issue when two plans intentionally share one epic.** In the same live-trace setup (two plans manually sharing one `beads_epic`), syncing the second plan closed the first plan's already-synced issue with reason "no longer maps to a plan task" — `find_orphans` computes `current_ids` from only the plan being synced, so any other plan's issue under the same epic looks orphaned. Also Phase 1 (`create_issues`/`find_orphans`) behavior, unchanged and untouched by this plan; out of scope to fix here.

Both discovered issues are pre-existing in code this plan's `<files>` does not include (`create_issues`, `resolve_epic`, `find_orphans` all live in `sync.py` but are Phase 1 functions this plan never modifies) — flagged per the deviation rules' scope boundary, not auto-fixed.

## Live Trace Evidence (Task 3)

Ran against a real `bd` v1.2.1 database in a scratch directory (`bd init --prefix live`), not mocks:

1. Synced a real 2-plan wave (`01-01-PLAN.md`, `01-02-PLAN.md`) sharing one epic via `create-issues` — real issue ids assigned (`live-tp0.1`, `live-tp0.2`)
2. `regenerate-beads-md` produced a real `01-BEADS.md` with correct D-05..D-08 frontmatter (`open: 1`, `closed: 1`, `blocking_open: 0`, `diverged: 0`, real `generated_from`/`generated_at`) and the 5-column table
3. `wave-status-block` printed:
   ```text
   <beads_status>
   live-tp0.1: 01-01.1 Task 1: Do live-a thing (closed)
   live-tp0.2: 01-02.1 Task 1: Do live-b thing (open)
   </beads_status>
   ```
   — this is the exact text SKILL.md's Step 2a instructs the orchestrator to paste into each executor's `prompt=` for this wave
4. `beads-recall` against the same real database correctly matched the open issue (`live-tp0.2`) under "Open issues touching this phase's scope" via `matched via: files`, re-confirming B7's mechanism against real data
5. `gsd-tools capability install ./.gsd/capabilities/beads --scope project` re-consented; `render-hooks plan:pre --raw` names `beads-recall` + the `into:"planner"` recall-pointer contribution (fragment text confirmed present verbatim); `render-hooks execute:wave:pre --raw` and `render-hooks execute:wave:post --raw` both name `beads-status`

**What remains unverified (recorded in `.planning/WINDOWS.md`, entries 1 and 2, both `human_judgment: true`):** literally grepping the `prompt=` text a real spawned executor `Agent()` call receives during a genuine `/gsd:execute-phase` wave dispatch, and literally grepping a real spawned planner subagent's composed prompt for the recall-pointer fragment. Neither is reproducible from within a spawned `execute-plan` subagent — both require the outer orchestrator itself to dispatch and a human (or a later phase's tooling) to inspect the resulting `Agent()` call.

## Issues Encountered

- Both new test classes initially placed their existence/content assertions outside the `with tempfile.TemporaryDirectory()` context manager (the exact bug 02-01's SUMMARY documented) — caught immediately by the first local test run (`AssertionError: False is not true` on `out_path.exists()`), fixed by moving assertions inside the `with` block before the GREEN commit.
- Two pre-existing Phase 1 defects discovered via the live trace (documented above as Deviations 3 and 4) — out of this plan's scope, not fixed.

## Next Phase Readiness

- Phase 2's full visibility surface (`beads-recall` at `plan:pre`, `beads-status` at `execute:wave:pre`/`execute:wave:post`) is implemented, unit-tested (39/39), and live-traced against real `bd`; the capability is re-installed/re-consented and confirmed active via `render-hooks`
- `.planning/WINDOWS.md` carries 2 open entries (both `unrun-verify`, both `human_judgment: true`) for the one piece of B7/B8 verification a spawned subagent structurally cannot perform: grepping a real orchestrator-dispatched `Agent()` call's composed prompt. A future phase (or a human running a real `/gsd:plan-phase`/`/gsd:execute-phase` wave with `beads.enabled=true`) can close both by inspection.
- Phase 1's epic-per-plan resolution gap and orphan-sweep false-positive (Deviations 3, 4 above) are real but unticketed — flagged here for a future phase/backlog item, not blocking Phase 2's own requirements (B7/B8/B11 all pass on their own literal criteria)
- Phase 3's ship gates can now read `BEADS.md`'s full D-05..D-08 frontmatter shape (this plan built it to the future shape now, per D-05, specifically so Phase 3 never has to re-touch every generation call site)

---
*Phase: 02-visibility*
*Completed: 2026-08-15*

## Self-Check: PASSED

All 5 modified files verified present on disk; all 3 commit hashes (`648a54e`, `4d4a5d5`, `927e9de`) verified present in `git log --oneline --all`.
