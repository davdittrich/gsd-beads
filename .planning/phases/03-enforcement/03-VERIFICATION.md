---
phase: 03-enforcement
verified: 2026-08-15T22:10:00Z
status: passed
score: 8/8 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 3: Enforcement Verification Report

**Phase Goal:** Beads state can block a ship — a phase with unfinished or diverged issues does
not pass unless the operator overrides deliberately, and the override is recorded.
**Verified:** 2026-08-15T22:10:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | With one open blocking issue, `ship:pre` blocks and names it | ✓ VERIFIED | Live `node gsd-tools.cjs check predicate --predicate '{"kind":"artifact-frontmatter-equals","artifact":"BEADS.md","field":"blocking_open","equals":0}'` against a synthetic `BEADS.md` (`blocking_open: 1`) — the exact command `ship.md` step 8(b) issues — returned `block: true, message: 'Frontmatter field "blocking_open" in BEADS.md is 1, expected 0'`. The patched `ship.md` (live at `$HOME/.claude/gsd-core/workflows/ship.md`, marker present exactly twice) contains steps 8/9 wiring this call into `preflight_checks`, verified byte-identical to `GSD-CORE-PATCH.md`'s reapply source (independently diffed, 4860 bytes both sides, `IDENTICAL: True`). |
| 2 | Setting `beads.ship_gate=false` allows the ship and records that it was overridden | ✓ VERIFIED | Live toggle of `.planning/config.json`'s `beads.ship_gate` to `false` and `node gsd-tools.cjs loop render-hooks ship:pre --raw` shows both `capId=="beads" and kind=="gate"` entries excluded from `activeHooks` while the `capId=="beads" and kind=="step"` entry (`ref.skill=="beads-status"`, the `ship_override` dispatch path) remains present — restored to `true` afterward, no residual diff. `ship_override` itself live-tested against a disposable git repo: `sync.py ship-override <phase_dir>` wrote a real, parseable `Beads-Override: ship_gate bypassed, blocking_open=2, diverged=1` trailer (`git log -1 --format=%(trailers)` confirms) and failed open on `bd` unavailability exactly as specified. |
| 3 | An issue closed in beads while its task is incomplete (or the reverse) sets `diverged>0`, blocks ship, and reports both sides without anything being auto-reconciled | ✓ VERIFIED | `_compute_diverged` (sync.py:415) implements the per-issue disagreement predicate exactly as specified, feeding `diverged` into `BEADS.md`'s frontmatter and a `Task Status` (done/incomplete) table column (sync.py:863, `_render_beads_md_table`) so both sides are named without cross-referencing another file. The `diverged` gate uses the identical `artifact-frontmatter-equals` evaluator as `blocking_open` (same code path live-tested above — `diverged: 0` passes; a nonzero value blocks via the identical mechanism), declared in `capability.json`'s `gates[]`. `TestDivergence`/`TestBlockingOpen` unit tests pass (66/66 full suite). No auto-reconciliation code path exists anywhere in `sync.py` — divergence is computed and reported only. |

### Deferred Items

None.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gsd/capabilities/beads/scripts/sync.py` | `_resolve_completed_task_ids`, `_compute_diverged`, `_render_beads_md_table` (6-col), `ship_override`, `_read_beads_md_frontmatter`, `check_shipmd_patch`, `_head_already_pushed`, `SHIP_MD_PATCH_MARKER`, `GIT_TIMEOUT` | ✓ VERIFIED | All symbols present at the exact line numbers SUMMARYs claim (checked via `grep -n`). |
| `.gsd/capabilities/beads/tests/test_sync.py` | `TestBlockingOpen`, `TestDivergence`, `TestShipOverride`, `TestShipPreGenericDispatch`, `TestCheckShipmdPatch` classes | ✓ VERIFIED | All 5 classes present; full suite `python3 -m pytest ... -q` → 66 passed, 0 failed, run once. |
| `.gsd/capabilities/beads/capability.json` | 2 `ship:pre` gates (`blocking_open==0`, `diverged==0`), `beads.ship_gate` config (default `true`), `ship:pre` step entry | ✓ VERIFIED | Parsed directly — both gates present with exact shape (`blocking: true`, `onError: skip`, `when: beads.ship_gate`); config key present; 6 `steps[]` entries total including `ship:pre`→`beads-status`. Valid JSON. |
| `.gsd/capabilities/beads/skills/beads-status/SKILL.md` | Step 2b/2c/2d, "Patch Status" section | ✓ VERIFIED | Read in full — Step 1.5's four-way branch, Step 2b (verify:post), Step 2c (ship-override dispatch), Step 2d (patch confirmation), "Patch Status" section with CR-01 caveat, all present and worded as SUMMARYs describe. |
| `.gsd/capabilities/beads/skills/beads-recall/SKILL.md` | Step 3.5 (independent patch-loss detector, CR-01 fix) | ✓ VERIFIED | Read in full — Step 3.5 present at `plan:pre`, correctly documents itself as the actual detector (vs. Step 2d's confirmation-only role). |
| `$HOME/.claude/gsd-core/workflows/ship.md` (machine-local) | `preflight_checks` steps 8/9, marker-bracketed | ✓ VERIFIED | Live file: marker string count = 2 (open+close); steps 8/9 content read in full and matches plan's `<action>` spec; steps 6/7 (security/broken-windows) unmodified in the surrounding text. |
| `.gsd/capabilities/beads/GSD-CORE-PATCH.md` | Verbatim reapply source, revert condition | ✓ VERIFIED | Present, 157 lines; fenced "Patch Content (verbatim)" block independently diffed byte-for-byte identical (4860 bytes) against the live marker-bracketed `ship.md` slice. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `regenerate_beads_md` | BEADS.md frontmatter (`blocking_open`, `diverged`) | direct f-string write, sync.py:952-953 | ✓ WIRED | Read source directly. |
| `capability.json gates[]` | BEADS.md frontmatter | `artifact-frontmatter-equals` predicate, evaluated by `gate-predicate-evaluator.cjs` | ✓ WIRED | Live-executed via `gsd_run check predicate` against synthetic fixtures — confirmed both block and pass paths. |
| `ship.md` preflight_checks step 8 | `gsd_run check predicate` | exact command form documented in ship.md prose | ✓ WIRED | Ran the literal command from ship.md's own step 8(b) text — output matches the two-step gate contract's expectations. |
| `ship.md` preflight_checks step 9 | `Skill(gsd-beads-status)` | `ref.skill` dispatch on active `kind=="step"` hook | ✓ WIRED | `loop render-hooks ship:pre --raw` confirms the beads step hook (`ref.skill=="beads-status"`) is present in `activeHooks` under both `ship_gate=true` and `ship_gate=false`, and step 9's prose in the live `ship.md` dispatches exactly that hook shape. |
| `beads-status SKILL.md Step 2c` | `sync.py ship_override` | CLI subcommand invocation | ✓ WIRED | Live-executed `ship-override` against a disposable git repo — trailer written and parseable. |
| `beads-status SKILL.md Step 2d` / `beads-recall SKILL.md Step 3.5` | `sync.py check_shipmd_patch` | CLI subcommand invocation | ✓ WIRED | `python3 sync.py check-shipmd-patch` run for real against the live patched `ship.md` — exits 0, prints "present ... at /home/dd/.claude/gsd-core/workflows/ship.md". |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Gate blocks on nonzero `blocking_open` | `gsd_run check predicate` against synthetic BEADS.md (`blocking_open: 1`) | `block: true`, message names the field | ✓ PASS |
| Gate passes on zero `blocking_open`/`diverged` | Same command, `blocking_open: 0`/`diverged: 0` | `block: false` both fields | ✓ PASS |
| Fail-open pre-check vs. evaluator's own fail-closed default | `ls <phase>/*-BEADS.md` (empty) vs. `gsd_run check predicate` on same missing artifact | glob empty (pre-check would skip); evaluator alone returns `block: true, artifactNotFound: true` | ✓ PASS (proves pre-check load-bearing) |
| `beads.ship_gate=false` excludes gates, retains step | `loop render-hooks ship:pre --raw` before/after toggling config | gate entries removed, step entry retained | ✓ PASS |
| `ship_override` writes a real, parseable trailer | `sync.py ship-override` against disposable git repo | `git log -1 --format=%(trailers)` → `Beads-Override: ship_gate bypassed, blocking_open=2, diverged=1` | ✓ PASS |
| `ship_override` fails open when `bd` unavailable | same run (no `bd` on PATH in scratch env) | printed B6 skip notice, git half still succeeded, exit 0 | ✓ PASS |
| `check-shipmd-patch` against real installed `ship.md` | `python3 sync.py check-shipmd-patch` | exit 0, "present" | ✓ PASS |
| Full test suite (run once) | `python3 -m pytest .gsd/capabilities/beads/tests/test_sync.py -q` | 66 passed | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| B9 | 03-01, 03-02, 03-03 | A phase with unfinished blocking issues cannot ship; `beads.ship_gate=false` allows + records override | ✓ SATISFIED | Live-tested block/pass/override behavior above; matches REQUIREMENTS.md wording exactly. |
| B10 | 03-01, 03-02, 03-03 | Divergence blocks and is reported; never auto-reconciled | ✓ SATISFIED | `_compute_diverged` + Task Status column + identical gate mechanism; no reconciliation code path found. |

No orphaned requirements — REQUIREMENTS.md maps only B9/B10 to Phase 3, both declared in all three plans' frontmatter `requirements: [B9, B10]`.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers found in any phase-modified file | — | Clean |

One pre-existing latent bug was disclosed (not introduced by this phase, not blocking B9/B10):
`rewrite_plan` (sync.py:383) prepends a fresh `beads_epic:` line without stripping a stale one on
the epic-replacement path WR-02 added coverage for — `BEADS_EPIC_RE.search` still resolves
correctly (finds the first, newest line), so this is cosmetic duplication, not a correctness
regression against B9/B10. Documented in `03-REVIEW-FIX.md`'s "Notes for the developer" as a
follow-up ticket candidate, not silently dropped. ℹ️ INFO — worth a follow-up ticket, does not
block phase completion.

### Code Review Findings (03-REVIEW.md / 03-REVIEW-FIX.md)

All 7 original findings (CR-01, WR-01..04, IN-01, IN-02) plus 1 independent-review finding
(New-01, `ship_override`'s unconditional HEAD amend) were fixed, each spot-checked directly
against the current source rather than trusted from the fix report:

- CR-01 (patch-loss detector unreachable in the scenario it exists to catch) — confirmed fixed:
  `beads-recall/SKILL.md` Step 3.5 exists and correctly documents itself as the independent
  detector (`plan:pre`, native dispatch, not gated behind the patch it verifies).
- WR-01/WR-02/WR-04 — confirmed present in source (escaping, stale-epic divergence reporting,
  block-list `depends_on:` parsing) via direct code read.
- New-01 (`_head_already_pushed`) — confirmed present at sync.py:1063, matches described guard.
- IN-01/IN-02 (`BEADS_RECALL_STATUSES` reuse, `GIT_TIMEOUT` split) — confirmed via module
  constants at sync.py:21-22.
- All 6 fix commits (`eee6db7`, `ceea964`, `d6acb6d`, `11d6d51`, `2657519`, `f19b447`) confirmed
  present in `git log`.

### Human Verification Required

None. Every truth in this phase was independently, live-verified against real running commands
(not SUMMARY narration): the gate predicate evaluator, the gate-exclusion/step-retention behavior
under `beads.ship_gate=false`, the `ship_override` git-trailer write against a disposable repo,
and `check-shipmd-patch` against the actual installed `ship.md`. No visual, real-time, or
external-service behavior is in scope for this phase.

### Gaps Summary

None. All three ROADMAP Success Criteria are true in the live codebase, not merely declared.
The one known limitation carried forward from Plan 02 (declared gates being inert against the
installed `ship.md`) was fully closed by Plan 03's machine-local patch, independently confirmed
live in this verification (marker present, byte-identical patch content, gate/step dispatch
mechanics all execute correctly against real `gsd_run` commands). The N2 (no fork/patch gsd-core)
constraint override is properly recorded in `PROJECT.md`'s Constraints section with an explicit
scope limitation ("covers this phase's execution scope, not this constraint's default going
forward") and an upstream tracking issue (open-gsd/gsd-core#3554) with a stated revert condition.

---

_Verified: 2026-08-15T22:10:00Z_
_Verifier: Claude (gsd-verifier)_
