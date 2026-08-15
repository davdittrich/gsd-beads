---
phase: 02-visibility
verified: 2026-08-15T13:39:58Z
status: human_needed
score: 2/3 must-haves verified
behavior_unverified: 1
overrides_applied: 0
behavior_unverified_items:
  - truth: "The composed orchestrator prompt at execute:wave:pre includes the beads fragment and names the issues in the wave, verified by inspecting the prompt directly (B8)"
    test: "Dispatch a real /gsd:execute-phase wave with beads.enabled=true against a real bd database (bd init in this repo or a scratch dir), let the orchestrator run the beads-status skill at execute:wave:pre, then capture and grep the actual prompt= text passed to each executor's Agent() call for the synced issue ids that appear in that wave's BEADS.md"
    expected: "Each executor's composed prompt literally contains the <beads_status> block naming this wave's issue ids/titles/statuses"
    why_human: "No party in this session can produce this evidence: a spawned executor/verifier subagent has no path to inspect the outer orchestrator's own Agent() call arguments, and this project's own 02-02-PLAN.md Task 3 (a blocking checkpoint:human-verify gate requiring a human to type \"approved\" after performing exactly this trace) was never actually gated by a human response — no 02-UAT.md exists, 02-VALIDATION.md's two manual-only rows (02-02-02, 02-02-03) remain unchecked with Approval: pending, and both WINDOWS.md ledger entries recording this gap are still status: open"
human_verification:
  - test: "Dispatch a real /gsd:execute-phase wave (2+ plans sharing an epic) with beads.enabled=true and a real bd database; grep the actual prompt= text each executor's Agent() call receives for the wave's synced issue ids"
    expected: "The composed executor prompt names the issue ids, matching BEADS.md's table for that wave — B8's literal acceptance criterion"
    why_human: "Structurally unreachable from inside any subagent; requires the outer orchestrator itself to dispatch and a human (or later tooling) to inspect the resulting Agent() call, per 02-02-PLAN.md Task 3 and 02-VALIDATION.md's own manual-only rows"
  - test: "Dispatch a real /gsd:plan-phase run; grep the actual composed planner-subagent prompt for the recall-pointer.md fragment text (not just capability.json's manifest correctness)"
    expected: "The planner's real prompt contains the BEADS-RECALL.md pointer prose"
    why_human: "Same class of gap as B8 — 02-VALIDATION.md row 02-02-03 and WINDOWS.md entry #1, both still open/pending"
---

# Phase 02: Visibility Verification Report

**Phase Goal:** The planner and executor see live beads issue state as part of their normal
operation, and the projection they read from is always freshly generated.
**Verified:** 2026-08-15T13:39:58Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Before planning a phase, `BEADS-RECALL.md` exists and names any open issue touching that phase's scope (B7) | ✓ VERIFIED | `beads-recall` subcommand (`sync.py:631-706`) implements the D-04 "always write, even zero issues" shape and the two-technique scope match (`scope_match`/`desc_contains_match`, `sync.py:599-629`); 7 `TestBeadsRecall` unit tests pass; live-traced against a real (non-mocked) `bd` v1.2.1 database — an open issue correctly matched via the `<beads-id>` reverse-lookup technique (02-02-SUMMARY.md §Live Trace Evidence step 4); `plan:pre` step + `contributions[]` pointer confirmed present in `capability.json` and, once the capability is active, rendering live via `render-hooks plan:pre --raw` (verified directly this session, see Anti-Patterns/Notes below) |
| 2 | The composed orchestrator prompt at `execute:wave:pre` includes the beads fragment and names the issues in the wave, verified by inspecting the prompt directly (B8) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `render_wave_status_block`/`regenerate_beads_md` (`sync.py:768-892`) are fully implemented and unit-tested (`TestWaveStatusBlock`, `TestBeadsMdRegeneration`, 8 tests combined); `capability.json`'s `execute:wave:pre` step and `beads-status/SKILL.md`'s Step 1.5/2a orchestrator instruction are confirmed present and — once the capability is active — confirmed *registered* via `render-hooks execute:wave:pre --raw` (this session). But the roadmap's literal acceptance clause ("verified by inspecting the prompt directly") has never been satisfied by anyone: not by the executor (structurally can't inspect its own orchestrator's `Agent()` calls), not by a human (02-02-PLAN.md Task 3 is a `checkpoint:human-verify gate="blocking"` requiring a human to type "approved" after this exact trace — no `02-UAT.md` exists, `02-VALIDATION.md`'s two manual-only rows are unchecked with `Approval: pending`, and both `WINDOWS.md` entries for this gap remain `status: open`). See Human Verification below |
| 3 | `BEADS.md` is regenerated from a real `bd` query at every step; a hand edit is overwritten at the next step rather than preserved (B11) | ✓ VERIFIED | `regenerate_beads_md` (`sync.py:768-834`) always fully overwrites the file from a fresh `bd list --parent <epic> --all --json -n 0` query, never reading/merging the prior body; `TestBeadsMdRegeneration.test_hand_edit_is_absent_after_next_regeneration` passes (planted-hand-edit-then-regenerate assertion); live-traced against a real `bd` v1.2.1 database producing correct D-05..D-08 frontmatter (`open: 1, closed: 1, blocking_open: 0, diverged: 0`) — this is a purely deterministic, code-level behavior with no LLM-prompt dependency, so unit test + live trace together are sufficient evidence |

**Score:** 2/3 truths verified (1 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gsd/capabilities/beads/scripts/sync.py` | `beads-recall`, `regenerate-beads-md`, `wave-status-block` subcommands | ✓ VERIFIED | 937 lines; all functions present with real logic (not stubs); `python3 -m unittest discover -s .gsd/capabilities/beads/tests -q` → 39/39 pass |
| `.gsd/capabilities/beads/skills/beads-recall/SKILL.md` | Four-step scaffold dispatching `beads-recall` | ✓ VERIFIED | Present, matches `beads-status`'s shape, dispatches `sync.py beads-recall` |
| `.gsd/capabilities/beads/skills/beads-status/SKILL.md` | Lifecycle-point branch (D-11): `execute:wave:pre` regen-only, `execute:wave:post` regen+close | ✓ VERIFIED | Step 1.5 branch present; instructs the orchestrator to paste the `<beads_status>` block into `prompt=` |
| `.gsd/capabilities/beads/fragments/recall-pointer.md` | Static pointer fragment, no embedded live data | ✓ VERIFIED | Pointer-only prose confirmed; `grep -cE '(open|matched|Unscoped) issue'` returns 0 as required |
| `.gsd/capabilities/beads/capability.json` | `plan:pre`→`beads-recall` step + contribution; `execute:wave:pre`→`beads-status` step | ✓ VERIFIED | All entries present, well-formed JSON, confirmed rendering live via `render-hooks` this session |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `capability.json` | `beads-recall/SKILL.md` | `plan:pre` step, `ref.skill: beads-recall` | ✓ WIRED | Confirmed by direct invocation and, after re-consent, by `render-hooks plan:pre --raw` |
| `beads-recall/SKILL.md` | `sync.py` | `sync.py beads-recall <phase_dir>` | ✓ WIRED | Confirmed by direct invocation |
| `capability.json` | `fragments/recall-pointer.md` | `plan:pre` contribution, `into: planner` | ✓ WIRED | `render-hooks plan:pre --raw` output includes the full `<contribution from="beads" into="planner">` block with the fragment's literal text |
| `capability.json` | `beads-status/SKILL.md` | `execute:wave:pre` step, `ref.skill: beads-status` (same skill id as `execute:wave:post`, D-11) | ✓ WIRED | `render-hooks execute:wave:pre --raw` names `capId: beads, ref.skill: beads-status` |
| `beads-status/SKILL.md`'s Step 2a instruction | executor `Agent()` `prompt=` | orchestrator manually pastes the printed block per SKILL.md prose | ⚠️ UNVERIFIED | This final hop — the orchestrator actually acting on the instruction inside a real wave dispatch — is the one link nobody has traced end-to-end (see Truth #2) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full capability test suite | `python3 -m unittest discover -s .gsd/capabilities/beads/tests -q` | `Ran 39 tests ... OK` | ✓ PASS |
| `beads-recall` fails open with no `bd` database | `python3 sync.py beads-recall .planning/phases/02-visibility` | `bd unavailable -- sync skipped`, exit 0, no file written | ✓ PASS (correct B6/D-08 behavior — this project has no `.beads` database; see Notes) |
| `capability.json` well-formed | `python3 -m json.tool .gsd/capabilities/beads/capability.json` | exits 0 | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| B7 | 02-01 | Planner sees open issues before planning | ✓ SATISFIED | Mechanism fully implemented/tested/live-traced; wiring confirmed active |
| B8 | 02-02 | Executor's prompt carries live issue state, verified by direct prompt inspection | ? NEEDS HUMAN | Mechanism implemented/tested/registered; literal acceptance clause (direct prompt inspection) never exercised by anyone — see Truth #2 |
| B11 | 02-02 | `BEADS.md` regenerated, never hand-edited | ✓ SATISFIED | Fully unit-tested + live-traced; deterministic code behavior |

No orphaned requirements — B7/B8/B11 are the only ones this phase's roadmap section maps, and all three appear in a plan's `requirements` frontmatter.

### Anti-Patterns Found

None. Scanned `sync.py`, both `SKILL.md` files, `capability.json`, and `recall-pointer.md` for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER|not yet implemented|coming soon` — zero matches.

## Notes: Capability Activation Was Found Inactive at Verification Start

At the start of this verification session, before any change was made, `gsd-tools capability list`
reported the `beads` capability as **`status: inactive, reason: "discovered — no user consent
record (inactive)"`**, and `render-hooks execute:wave:pre --raw` returned **zero active hooks**
(`beads-recall` was similarly absent from `render-hooks plan:pre --raw`). This directly contradicts
both plans' SUMMARY.md claims of "Confirmed active via render-hooks" recorded at commit `927e9de`
(13:27:59Z) and `770950f`.

Root-caused: the working tree's `.gsd/capabilities/beads/` bundle is byte-for-byte identical to what
it was immediately after that re-install commit (`git diff 927e9de..HEAD -- .gsd/capabilities/beads`
is empty; no untracked files; removing stray `__pycache__` bytecode — the only non-tracked
content — made no difference). The external, user-owned consent store
(`~/.gsd/consent.json`) does hold a record from that exact timestamp, but its bound
`bundleContentHash` no longer matches what the loader recomputes now, so the record is treated as
absent. This is gsd-core's own project-scope capability-consent mechanism (`capability-consent.cjs`,
issue #1459's content-binding design) — not code this phase's plans touch or own (N1/N2 out-of-scope
boundary) — and re-running `gsd-tools capability install ./.gsd/capabilities/beads --scope project`
immediately restored `status: active` and both hook registrations, confirming the underlying
mechanism (Truths #1 and #3, and the wiring half of Truth #2) is correct once consent holds.

This is flagged as a **WARNING**, not a blocker: STATE.md's own Key Decisions already documents this
exact gsd-core behavior ("any post-consent file edit silently deactivates it; re-run capability
install --scope project after any such edit, every phase") as a known operational step, and the
phase's own artifacts are unaffected. But it does mean the specific "Confirmed active" evidence
recorded in both SUMMARYs is not a durable state — a fresh session (like this verification) can
find the capability inactive with zero code changes, and nothing in this phase's own deliverables
detects or self-heals that drift. Recommend either a `gsd-verify`-time gate that checks
`capability list`'s `beads` status before trusting `beads.enabled`, or explicit documentation in
`beads`'s own `README`/`SKILL.md` that a lapsed consent silently degrades every downstream step to
its fail-open no-op (which is safe, but silent).

## Notes: Never Exercised Against This Project's Own Real State

This project (`gsd-beads`) has no `.beads` database of its own (`bd list` → "no beads database
found"). Every "live trace" cited in both SUMMARYs ran `bd init --prefix live`/`mock-e1`/`tp0` in a
disposable scratch directory, never against this project's own Phase 1/Phase 2 plan tasks. This
means B7's and B11's mechanisms are proven correct in isolation but have never produced a real
`BEADS-RECALL.md` or `BEADS.md` for this project's own phase directories (neither file exists
anywhere under `.planning/phases/`). This is consistent with — not a violation of — B6's fail-open
design (confirmed directly this session: `beads-recall` against this project's own phase dir prints
`bd unavailable -- sync skipped`, exit 0, no stale file left behind) but it does mean the project's
own stated Core Value ("gsd's lifecycle writes to and reads from `bd` exclusively for task state")
has not yet been dogfooded end-to-end on itself. Not a Phase 2 blocker (both 02-01-SUMMARY.md and
02-02-SUMMARY.md already flag this as an environment precondition, not a defect) but worth a
deliberate `bd init` + real sync before Phase 3's ship-gate work needs a populated database to test
against.

## Two Pre-Existing Phase 1 Defects (Discovered, Not Fixed, This Phase)

Both discovered during 02-02's live trace and documented in 02-02-SUMMARY.md Deviations #3/#4:

1. `create_issues` resolves each plan's epic independently from its own frontmatter rather than
   sharing one phase-level epic when `beads_epic` isn't pre-set on every plan in a phase.
2. The orphan sweep (`find_orphans`) auto-closes a sibling plan's already-synced issue when two
   plans intentionally share one epic (`current_ids` is computed from only the plan being synced).

Confirmed: both live entirely in `create_issues`/`resolve_epic`/`find_orphans` — Phase 1 functions
this phase's plans never modify (not in either plan's `<files>` scope) — so they do not block Phase
2's own B7/B8/B11 acceptance, which all pass on their own literal mechanism-level criteria
independent of these two gaps.

Tracking status: recorded in `STATE.md` Blockers/Concerns ("[Backlog] Phase 1 sync.py: create_issues
resolves each plan's epic independently... discovered during 02-02's live trace, unticketed,
unfixed") and in the Decisions log. This is a markdown note, not a formal `bd`/GitHub issue — given
this project has no live `.beads` database of its own (see above), that is the only tracking
mechanism currently available to it. **Recommend filing a real ticket before Phase 3** begins,
since Phase 3's ship-gate divergence detection (B10) will read the same `epic`/orphan-sweep code
path these two gaps live in, and an unticketed markdown note is easy to lose across a phase
boundary.

## Human Verification Required

### 1. Executor prompt names the wave's issues (B8 literal acceptance criterion)

**Test:** Dispatch a real `/gsd:execute-phase` wave (2+ plans sharing one epic) with
`beads.enabled=true` against a real `bd` database (`bd init` in this repo, or a scratch directory).
Capture the actual `prompt=` argument passed to each executor's `Agent()` call.

**Expected:** The composed prompt contains the `<beads_status>` block naming this wave's synced
issue ids/titles/statuses (matching that wave's `BEADS.md` table).

**Why human:** No subagent — including this verifier — has a path to inspect the text of its own
orchestrator's `Agent()` call arguments. This is the same limitation the plan's own author recorded
(`02-02-PLAN.md` Task 3, a blocking `checkpoint:human-verify` gate) and that gate was never actually
closed: no `02-UAT.md` exists for this phase, and `02-VALIDATION.md`'s manual-only row for this exact
check is still `⬜ pending` with `Approval: pending`.

### 2. Planner prompt includes the recall-pointer fragment (B7 goal-level strengthening)

**Test:** Dispatch a real `/gsd:plan-phase` run and capture the composed planner-subagent prompt.

**Expected:** The prompt contains the `recall-pointer.md` fragment's prose pointing at
`BEADS-RECALL.md`.

**Why human:** Same structural limitation as above; `02-VALIDATION.md` row `02-02-03` and
`WINDOWS.md` entry #1 both remain open.

## Gaps Summary

No FAILED truths, no missing/stub artifacts, no broken wiring, no debt markers — the phase's
literal, mechanism-level deliverables (B7, B11, and the wiring half of B8) are solidly implemented,
unit-tested, and live-traced against a real (if scratch) `bd` v1.2.1 database. The phase does not
fail; it is **incomplete pending human verification** of the one requirement (B8) whose acceptance
criterion is explicitly "verified by inspecting the [real, LLM-composed] prompt directly" — a check
that structurally cannot be performed by any subagent, that the plan itself scheduled as a blocking
human checkpoint, and that checkpoint was never actually gated by a human response. The capability's
current-session inactivity (see Notes) and the never-dogfooded-on-itself state (see Notes) are both
flagged as warnings for awareness, not scored as gaps against this phase's own success criteria.

---

*Verified: 2026-08-15T13:39:58Z*
*Verifier: Claude (gsd-verifier)*
