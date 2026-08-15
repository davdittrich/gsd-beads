---
phase: 02-visibility
plan: 01
subsystem: infra
tags: [beads, bd, capability-manifest, gsd-core, plan-pre-hooks]

# Dependency graph
requires:
  - phase: 01-substrate
    provides: sync.py's run_bd/bd_available/find_project_root/confined/append_state_blocker helpers, parse_plan's <beads-id> anchoring, the B6/D-08 fail-open shape
provides:
  - "beads-recall skill + sync.py subcommand: two-technique open-issue scope matching (<beads-id> reverse lookup, --desc-contains fallback), Unscoped fallback, BEADS-RECALL.md writer"
  - "capability.json plan:pre step dispatching beads-recall, plus a plan:pre -> planner static pointer contribution using the confirmed-working plan-phase.md:731 slot"
affects: [02-02, beads-status, execute-phase wave dispatch]

# Actuals (#2632)
actuals:
  tokens: 7107
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns: [two-technique file-scope matching (cross-phase <beads-id> reverse lookup + bd --desc-contains fallback), static contribution fragments as pointers-not-payloads]

key-files:
  created:
    - .gsd/capabilities/beads/skills/beads-recall/SKILL.md
    - .gsd/capabilities/beads/fragments/recall-pointer.md
  modified:
    - .gsd/capabilities/beads/scripts/sync.py
    - .gsd/capabilities/beads/capability.json
    - .gsd/capabilities/beads/tests/test_sync.py

key-decisions:
  - "D-01 (revised): bd has no structured file-path field, so file-scope matching resolves to two concrete techniques -- a cross-phase <beads-id> reverse lookup against every PLAN.md's <files> element, and a bd list --desc-contains substring fallback -- not one generic comparison"
  - "The phase-being-planned's own file-scope signal comes from ROADMAP.md section text + CONTEXT.md mentions (regex path-token extraction), since no PLAN.md exists yet for it at plan:pre time"
  - "Contribution fragment (recall-pointer.md) is a static pointer only, per Pattern 1 -- names BEADS-RECALL.md's path pattern generically, never embeds live per-invocation issue data"

patterns-established:
  - "Two-technique scope match: scope_match() (pure, reverse-lookup) resolves first; desc_contains_match() (one bd call per phase-mention token) is the fallback only when scope_match returns None"
  - "_escape_table_cell() escapes | and strips \\r/\\n before issue text enters a markdown table cell (matches gsd-core's ship.md pattern, T-02-03)"

requirements-completed: [B7]

coverage:
  - id: D1
    description: "BEADS-RECALL.md is always written at plan:pre when bd is available, even with zero open issues (D-04 'none found' body)"
    requirement: "B7"
    verification:
      - kind: unit
        ref: "test_sync.py#TestBeadsRecall.test_zero_open_issues_writes_none_found_body"
        status: pass
      - kind: unit
        ref: "test_sync.py#TestBeadsRecall.test_zero_open_issues_still_writes_none_found_body_with_scope_matching_wired"
        status: pass
    human_judgment: false
  - id: D2
    description: "An open issue whose <beads-id>-linked task's <files> overlaps this phase's ROADMAP.md/CONTEXT.md mentions is listed under the matched heading, tagged 'matched via: files'"
    requirement: "B7"
    verification:
      - kind: unit
        ref: "test_sync.py#TestBeadsRecall.test_files_reverse_lookup_match_appears_under_matched_heading"
        status: pass
    human_judgment: false
  - id: D3
    description: "An open issue with no matching <beads-id> anywhere, but whose description substring-matches a phase-mentioned token, is listed under the matched heading, tagged 'matched via: description'"
    requirement: "B7"
    verification:
      - kind: unit
        ref: "test_sync.py#TestBeadsRecall.test_desc_contains_fallback_match_appears_under_matched_heading"
        status: pass
    human_judgment: false
  - id: D4
    description: "An issue matching neither technique is listed under a separate Unscoped heading, never dropped (D-02)"
    requirement: "B7"
    verification:
      - kind: unit
        ref: "test_sync.py#TestBeadsRecall.test_unmatched_issue_stays_unscoped_never_dropped"
        status: pass
      - kind: unit
        ref: "test_sync.py#TestBeadsRecall.test_multi_issue_response_lists_every_issue_under_unscoped"
        status: pass
    human_judgment: false
  - id: D5
    description: "capability.json declares the plan:pre -> beads-recall step and a plan:pre -> planner static pointer contribution using the confirmed-working plan-phase.md:731 slot"
    requirement: "B7"
    verification:
      - kind: unit
        ref: "python3 -c-equivalent script asserting exactly one plan:pre/into:planner contribution entry"
        status: pass
    human_judgment: false
  - id: D6
    description: "The plan:pre contribution fragment actually reaches the planner subagent's real composed prompt (goal-level intent beyond the literal B7 test)"
    verification: []
    human_judgment: true
    rationale: "Requires dispatching a real /gsd:plan-phase run (or tracing a real planner subagent Agent() call) and grepping its composed prompt text for the fragment content -- not reproducible inside this execute-plan session; the plan's own acceptance criteria mark this a 'Live trace' item."

# Metrics
duration: 13min
completed: 2026-08-15
status: complete
---

# Phase 02 Plan 01: Beads Recall Summary

**Two-technique open-issue scope matching (cross-phase `<beads-id>` reverse lookup + `bd --desc-contains` fallback) writes `BEADS-RECALL.md` at `plan:pre`, surfaced to the planner via a static pointer contribution.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-08-15T13:01:19Z
- **Completed:** 2026-08-15T13:14:01Z
- **Tasks:** 3
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments
- `beads-recall` subcommand added to `sync.py`, wired through a new `beads-recall` skill and a `capability.json` `plan:pre` step, writing a real `BEADS-RECALL.md` on disk (or the explicit "none found" body per D-04, or the B6/D-08 fail-open skip when `bd` is unavailable)
- Two-technique file-scope matching implemented: a cross-phase `<beads-id>` reverse lookup (`collect_all_task_files`/`scope_match`) against every phase's `PLAN.md` `<files>` elements, falling back to a `bd list --desc-contains` substring match (`extract_phase_mentions`/`desc_contains_match`) against ROADMAP.md/CONTEXT.md mentions for issues with no matching `<beads-id>` anywhere
- An issue matching neither technique is listed under a separate "Unscoped" heading, never silently dropped (D-02)
- A static `plan:pre` → `planner` contribution fragment (`recall-pointer.md`) added to `capability.json`, using the confirmed-working `plan-phase.md:731` injection slot to point the planner at `BEADS-RECALL.md` — a pointer only, never embedding live issue data (Pattern 1)

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end tracer (plan:pre → BEADS-RECALL.md)** - `a8bf3c9` (feat)
2. **Task 2: Two-technique file-scope matching** - `423000a` (test, RED) → `a9dbca7` (feat, GREEN)
3. **Task 3: Static plan:pre contribution pointer** - `50cd326` (feat)

_No REFACTOR commit needed for Task 2 — the GREEN implementation required no cleanup pass._

## Files Created/Modified
- `.gsd/capabilities/beads/scripts/sync.py` - Added `beads-recall` subcommand: `_beads_recall_argv`, `_render_beads_recall_body`/`_render_issue_table`/`_escape_table_cell`, `beads_recall`, `collect_all_task_files`, `extract_phase_mentions`, `scope_match`, `desc_contains_match`; extended `parse_plan` to capture each task's `<files>` list
- `.gsd/capabilities/beads/capability.json` - Added `plan:pre` step dispatching `beads-recall`, added `beads-recall` to the skills manifest, added a `plan:pre` → `into: "planner"` contribution entry
- `.gsd/capabilities/beads/skills/beads-recall/SKILL.md` - New four-step scaffold (banner, config gate, bd-availability delegation, recall dispatch, report) matching `beads-status`'s shape
- `.gsd/capabilities/beads/fragments/recall-pointer.md` - New static pointer fragment for the planner
- `.gsd/capabilities/beads/tests/test_sync.py` - Added `TestBeadsRecall` (7 tests): zero-issue "none found", multi-issue-all-Unscoped, bd-unavailable fail-open, files-reverse-lookup match, desc-contains fallback match, unmatched-stays-Unscoped, zero-issue regression with matching wired in

## Decisions Made
- Followed 02-RESEARCH.md's corrected D-01: `bd` v1.2.1 has no structured file-path field, so scope matching is genuinely two distinct techniques (reverse `<beads-id>` lookup, then `--desc-contains` fallback), not one generic comparison
- `desc_contains_match`'s dispatch condition matches the plan's `<action>` text literally: `desc_contains_match` runs whenever `scope_match` returns `None`, regardless of whether the issue has any `<beads-id>`-linked files at all — simpler than gating on files-index membership and matches the plan's stated wiring order
- `extract_phase_mentions` reads the phase's ROADMAP.md section (header to next `### Phase` heading) plus CONTEXT.md's full text — the only pre-plan file-scope signal available, per D-01 revised's Open Question resolution

## Deviations from Plan

None — plan executed as written, with one minor acceptance-criteria mismatch noted below (not a functional gap).

### Notes (not deviations, but worth flagging)

- **Task 2 acceptance criterion "`grep -c '\"-n\", \"0\"'` returns at least 3" measured 2.** Two genuine `bd list` call sites exist within this plan's actual scope and both pass `-n 0` explicitly per Pitfall 3: the D-04 baseline open-issue scan (`_beads_recall_argv`) and `desc_contains_match`'s per-token fallback query. A third call site does not exist anywhere in Task 1/2's actual design — RESEARCH.md's pitfall table explicitly names only these two new `bd list` calls this phase's `beads-recall` work introduces, and 02-02-PLAN.md's own Task 1 acceptance criteria expect the cumulative count to reach 4 only after that plan's `regenerate-beads-md` (BEADS.md/B11) adds its own `-n 0` call. Adding a third no-op call here purely to satisfy the grep count would be padding/dead code, contradicting the plan's own "no shortcuts" simplicity mandate. All functional `<verify>`/acceptance criteria that exercise real behavior (the full 34-test suite, `--desc-contains` grep ≥1, `collect_all_task_files` grep ≥2, the planted-failure check) pass exactly as specified.
- **Task 3's "Live trace" acceptance criterion (grepping a real `/gsd:plan-phase` planner subagent's composed prompt for the fragment content) is not exercised by this execute-plan session** — it requires dispatching a real planning run, out of scope for `/gsd:execute-phase`. Recorded as `coverage.D6` with `human_judgment: true` so `verify-work` routes it to a human/UAT pass rather than silently auto-passing. `capability.json`'s manifest correctness (the mechanical half of Task 3's criteria) is fully verified.
- **Capability-consent hash re-install** (RESEARCH.md Pitfall 2: editing `.gsd/capabilities/beads/` after project-scope consent silently deactivates the whole bundle) is not this plan's task — 02-02-PLAN.md's own frontmatter (`"The beads capability is re-installed and re-consented at project scope after every file edit this phase makes"`) already owns that remediation as a phase-closing step. Until that runs, the new `plan:pre` step/contribution this plan adds will not actually fire against a real `gsd_run` invocation of this project.

## Issues Encountered
- Two `TestBeadsRecall` positive-existence assertions were initially written outside the `tempfile.TemporaryDirectory()` context manager (matching a subtly different existing pattern in the file used only for negative `assertFalse(...exists())` checks) — the temp dir was already deleted by the time the file-existence assertion ran. Fixed by moving assertions inside the `with` block, matching `TestCloseWave`'s correct precedent. Caught immediately by the first local test run, before any commit.

## Next Phase Readiness
- `beads-recall`'s two-technique matching and the fail-open/D-04/D-02 shapes are fully unit-tested and ready for 02-02's `beads-status` extension (B11's `BEADS.md` regeneration) and B8's wave-status work, which reuse the same `collect_all_task_files`-style cross-phase scan pattern
- Real end-to-end proof against a live `bd` database is blocked on `bd init` in this repo (per 02-RESEARCH.md's Environment Availability table — `.beads/*.db` absent here today), same precondition Phase 1's own tracer needed; not a Phase 2 defect
- 02-02-PLAN.md's capability re-install/re-consent task must run before either plan's new `plan:pre`/`execute:wave:pre` steps actually activate against this project's own `gsd_run` invocations

---
*Phase: 02-visibility*
*Completed: 2026-08-15*

## Self-Check: PASSED

All 6 created/modified files verified present on disk; all 4 task commit hashes (`a8bf3c9`, `423000a`, `a9dbca7`, `50cd326`) verified present in `git log --oneline --all`.
