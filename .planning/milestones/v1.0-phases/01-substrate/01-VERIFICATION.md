---
phase: 01-substrate
verified: 2026-08-15T02:48:47Z
status: passed
score: 6/6 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "The capability is installed and consented at project scope, so the loop actually dispatches the beads steps (01-03-PLAN.md must_have; phase goal clause 'without anyone running bd by hand')"
  gaps_remaining: []
  regressions: []
human_verification: []
---

# Phase 01: Substrate Verification Report

**Phase Goal:** Every gsd task exists as a beads issue, with correct status, without anyone running
`bd` by hand — and `bd` being absent, failing, or locked never blocks a phase.
**Verified:** 2026-08-15T02:48:47Z
**Status:** passed
**Re-verification:** Yes — after gap closure

## Goal Achievement

### Re-Verification Scope

This pass re-checks only the single blocking gap from the prior verification
(2026-08-15T02:45:56Z): the beads capability's project-scope consent record was
invalidated when the CR-01 code-review fix (commit `3c8a62a`) edited files inside
the consented bundle (`.gsd/capabilities/beads/`) after the original install/consent
checkpoint (commit `e75153b`) — `capability-consent.cjs` binds project-scope consent
to a recomputed sha512 hash over the whole bundle, so any post-consent edit silently
deactivates it. The remediation (`capability install ./.gsd/capabilities/beads --scope
project`, commit `85aff2a`) re-ran consent against the post-fix bundle content.

The other 5/6 must-haves (mechanism-level B1-B6, artifacts, requirements traceability,
27/27 unit tests) were independently confirmed correct in the prior pass and are not
re-derived here — only re-checked for regression via the full test-suite re-run below
and a clean `git status` on the bundle directory.

### Observable Truths (ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Planning an N-task phase creates exactly N beads issues parented to a phase epic | VERIFIED | `sync.py:resolve_epic`/`resolve_issue` (create_issues, lines 214-250, 390-471); `TestCreateIssues`, `TestEndToEndTracer` (real `bd` tracer, not mocked) — re-run, all pass |
| 2 | Task ordering declared in PLAN.md becomes enforced beads dependencies (`bd ready` excludes blocked task) | VERIFIED | `derive_dependency_edges`/`apply_dependency_edges` (lines 169-201); `TestDependencyMapping` + `TestLiveDependencies.test_ready_excludes_blocked_tasks_until_blockers_close` (real `bd ready` invocation) — re-run, pass |
| 3 | Completing a task automatically closes exactly its own beads issue and no other | VERIFIED | `close_wave`/`filter_open_ids` (lines 315-387); `TestCloseWave` (5 tests) — re-run, pass |
| 4 | Each task block carries an explicit `beads-id:` binding on first sync; renaming never creates a duplicate | VERIFIED | `resolve_issue` resolves by `<beads-id>` first, never by title (lines 231-250); `TestIdentityBinding` — re-run, pass |
| 5 | Re-running sync over an unchanged plan creates zero issues and modifies zero | VERIFIED | `TestIdempotency` (2 tests) — re-run, pass |
| 6 | With `bd` off PATH (or failing, or locked), every gsd command completes normally, one line explains the skip, no phase is blocked, `BEADS.md` absent | VERIFIED | `bd_available()` probe + fail-open `try/except RuntimeError` (CR-01 fix, commit `3c8a62a`) degrade to notice + `STATE.md` bullet + exit 0. `TestFailOpen` (3 cases, incl. the CR-01 planted-failure regression test) — re-run, pass |
| — (phase-goal clause) | "...without anyone running `bd` by hand" — i.e. `plan:post`/`execute:wave:post` actually dispatch automatically | **VERIFIED (gap closed)** | See "Gap Closure Evidence" below. `capability list --raw` now reports `beads` `"status": "active"`; both render-hooks points name `capId: "beads"`. |

**Score:** 6/6 ROADMAP success criteria verified, including the previously-failing
"without anyone running `bd` by hand" clause.

### Gap Closure Evidence (live, re-run now)

| Check | Command | Prior result (2026-08-15T02:45:56Z) | Current result (2026-08-15T02:48:47Z) | Status |
|-------|---------|--------------------------------------|-----------------------------------------|--------|
| Capability activation state | `node gsd-tools.cjs capability list --raw` | `beads`: `"status":"inactive"`, `"reason":"discovered — no user consent record (inactive)"` | `beads`: `"status":"active"`, `"reason":null`, `"source":"./.gsd/capabilities/beads"`, `"scope":"project"` | **FIXED** |
| `plan:post` dispatch | `node gsd-tools.cjs loop render-hooks plan:post --raw` | Only `capId:"gap-analysis"` | `activeHooks[0]` = `{"capId":"beads","kind":"step","ref":{"skill":"beads-sync"},"when":"beads.enabled","onError":"skip"}`, plus `gap-analysis` gate | **FIXED** |
| `execute:wave:post` dispatch | `node gsd-tools.cjs loop render-hooks execute:wave:post --raw` | Only `capId:"drift"` (×2) and `"ui"` | `activeHooks[0]` = `{"capId":"beads","kind":"step","ref":{"skill":"beads-status"},"when":"beads.enabled","onError":"skip"}`, plus `drift` (×2) and `ui` gates | **FIXED** |
| Regression: unit suite still green | `python3 -m unittest discover -s .gsd/capabilities/beads/tests -q` | `Ran 27 tests ... OK` | `Ran 27 tests ... OK` | **NO REGRESSION** |
| Regression: bundle untouched since re-consent | `git status --short` (repo root) | n/a | No modified/staged files under `.gsd/capabilities/beads/` — only unrelated untracked scratch files (`.claude/scheduled_tasks.lock`, `.gsd/dispatch-isolation-sentinel.json`) plus this report itself | **NO REGRESSION** |

Root cause of the original gap and its fix, confirmed via `git log`:
- `e75153b` (04:30:57+02:00) — original install/consent checkpoint closed.
- `3c8a62a` (04:41:58+02:00, 11 min later) — CR-01 fix edits `sync.py`/`test_sync.py` inside the already-consented bundle, silently invalidating the content-hash-bound consent.
- `85aff2a` (04:47:59+02:00) — `capability install ./.gsd/capabilities/beads --scope project` re-run, recording a fresh consent hash over the post-fix bundle content, closing the gap. `.gsd-capabilities.json` diff for this commit: 1 line changed (the ledger hash bump).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gsd/capabilities/beads/capability.json` | Manifest: `beads.enabled`/`beads.sync_mode` config, `plan:post` + `execute:wave:post` steps | VERIFIED | Both `steps[]` entries present, `onError: skip`, `when: beads.enabled` |
| `.gsd/capabilities/beads/skills/beads-sync/SKILL.md` | Banner, config gate, bd-availability gate, dispatch, report | VERIFIED | ≥60 lines, instructs `python3 .../sync.py create-issues <path>` |
| `.gsd/capabilities/beads/skills/beads-status/SKILL.md` | Banner, config gate, iterate wave plan ids, batch close, report | VERIFIED | ≥50 lines, instructs `python3 .../sync.py close-wave <phase_dir> <plan_ids...>` |
| `.gsd/capabilities/beads/scripts/sync.py` | stdlib-only create-issues + close-wave, epic/issue resolution, dependency edges, orphan closure, divergence reporting, fail-open | VERIFIED | 497 lines; all described behaviors present and exercised by tests |
| `.gsd/capabilities/beads/tests/test_sync.py` | Unit coverage for B1-B6 | VERIFIED | 27 tests; independently re-run, all pass |
| `.gsd/capabilities/beads/tests/fixtures/*.md` (6 fixtures) | Real-schema PLAN.md fixtures for each test class | VERIFIED | All present, referenced by their respective tests |
| `.planning/config.json` (`beads.enabled: true`) | Enables the capability | VERIFIED and ACTIVE | Key is present; capability is now consent-active, so the overlay's config schema is composed into the registry and `beads.enabled` actually gates dispatch (previously present-but-inert) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `capability.json` `steps[]` | `beads-sync/SKILL.md` | `ref.skill: "beads-sync"` at `plan:post` | **WIRED AND DISPATCHED** | Confirmed live: `render-hooks plan:post --raw` names `capId:"beads"`, `ref.skill:"beads-sync"` |
| `capability.json` `steps[]` | `beads-status/SKILL.md` | `ref.skill: "beads-status"` at `execute:wave:post` | **WIRED AND DISPATCHED** | Confirmed live: `render-hooks execute:wave:post --raw` names `capId:"beads"`, `ref.skill:"beads-status"` |
| `beads-sync/SKILL.md` | `sync.py` | `python3 .../sync.py create-issues <path>` | WIRED | Confirmed via direct grep: SKILL.md line 54 |
| `beads-status/SKILL.md` | `sync.py` | `python3 .../sync.py close-wave <phase_dir> <plan_ids...>` | WIRED | Confirmed via direct grep: SKILL.md line 57 |
| `sync.py` | `bd` database | `subprocess.run(argv, ...)` — no shell string ever built from PLAN.md text | WIRED | Confirmed: `run_bd` (line 32-35) is the sole `bd` invocation point; every call site passes a typed argv list |
| `gsd-core` loop (`plan:post`, `execute:wave:post`) | `beads` capability | Overlay registry composition → consent gate → activation | **WIRED (active)** | `capability list --raw` reports `"status":"active"`; both `render-hooks` outputs name `capId:"beads"` as the first active hook |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| B1 | 01-01 | One beads issue per PLAN.md task, parented to a phase epic | SATISFIED | `TestCreateIssues`, `TestEndToEndTracer`; now dispatched automatically via `plan:post` |
| B2 | 01-02 | Plan task ordering becomes beads dependencies | SATISFIED | `TestDependencyMapping`, `TestLiveDependencies` |
| B3 | 01-03 | Task completion closes its issue automatically | SATISFIED | `TestCloseWave`; now dispatched automatically via `execute:wave:post` |
| B4 | 01-01 | Identity bound explicitly via `beads-id:`, never by title | SATISFIED | `TestIdentityBinding` |
| B5 | 01-02 | Sync is idempotent | SATISFIED | `TestIdempotency` |
| B6 | 01-01 | `bd` absent/failing/locked degrades to no-op with one notice | SATISFIED | `TestFailOpen` (3/3, incl. CR-01 regression test) |

No orphaned requirements: REQUIREMENTS.md's Traceability table maps exactly B1-B6 to
Phase 1, and each of the three plans' `requirements:` frontmatter fields cover exactly
that set with no gaps or duplicates (`01-01: [B1, B4, B6]`, `01-02: [B2, B5]`, `01-03: [B3]`).

All six requirements are now satisfied both as *mechanisms* (unchanged from the prior
pass) and at the "runs automatically without a human invoking `sync.py` directly"
level the phase goal's own sentence promises — the capability is active and both
dispatch points name the `beads` step.

### Requirements-Completed Frontmatter Cross-Check

`01-01-SUMMARY.md: [B1, B4, B6]` + `01-02-SUMMARY.md: [B2, B5]` + `01-03-SUMMARY.md: [B3]`
= `{B1, B2, B3, B4, B5, B6}` — exactly the phase's declared requirement set, no gaps,
no duplicates. Matches REQUIREMENTS.md's Traceability table (all six marked Complete).

### Behavioral Spot-Checks / Probe Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full unit suite is green (regression re-run) | `python3 -m unittest discover -s .gsd/capabilities/beads/tests -q` | `Ran 27 tests ... OK` | PASS |
| Capability is active (gap-closure re-check) | `node gsd-tools.cjs capability list --raw` | `"id":"beads","status":"active","reason":null,"scope":"project"` | PASS |
| `plan:post` render-hooks names the beads step (gap-closure re-check) | `node gsd-tools.cjs loop render-hooks plan:post --raw` | `capId:"beads"`, `ref.skill:"beads-sync"` present as first active hook | PASS |
| `execute:wave:post` render-hooks names the beads step (gap-closure re-check) | `node gsd-tools.cjs loop render-hooks execute:wave:post --raw` | `capId:"beads"`, `ref.skill:"beads-status"` present as first active hook | PASS |
| Bundle untouched since re-consent (no fresh invalidation) | `git status --short` | No changes under `.gsd/capabilities/beads/` | PASS |

No probes (`scripts/*/tests/probe-*.sh`) exist or are declared for this phase — SKIPPED
(none applicable; this is a Python-stdlib capability, not a probe-based migration/tooling phase).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `sync.py` | 376-386 (`close_wave`) | `bd close` failure is printed but the final summary line unconditionally reports `len(to_close)` as closed | Warning (carried from 01-REVIEW.md WR-01, unresolved) | An operator reading only the final stdout line could believe a close succeeded when `bd close` actually failed. Does not affect the automated test suite or block B3, but undermines the "correct status" clause in the specific case of a `bd close` failure. Not a phase-blocking gap; not part of the must-have set re-verified here. |
| `sync.py` | 282-285 (`rewrite_plan`) | `fm_match.start(1)` on a possibly-`None` match when a PLAN.md has no frontmatter | Warning (carried from 01-REVIEW.md WR-02, unresolved) | Would crash with `AttributeError` on a malformed PLAN.md rather than degrading gracefully — narrower/lower-likelihood than CR-01, not covered by any stated must-have truth. |
| `capability.json` | steps[].produces | `"produces": ["BEADS.md"]` on both steps; no code path ever writes `BEADS.md` | Info (carried from 01-REVIEW.md WR-04, unresolved) | Inert today (`produces`/`consumes` only drive topological step ordering); misleading to a future engineer wiring a `consumes: ["BEADS.md"]` step. |

These three are unchanged from the prior pass, carried forward from `01-REVIEW.md`
(same-day code review). They were explicitly out of scope for this re-verification
(only the consent-invalidation gap), do not block any of the six phase success
criteria as written, and remain informational.

### Human Verification Required

None. The gap-closure checks are all machine-verifiable and were confirmed by direct,
live re-execution of the exact commands the prior verification specified as the
remediation's success test.

### Gaps Summary

No gaps remain. The single blocking gap from the prior pass — the beads capability's
project-scope consent being invalidated by the CR-01 fix editing the bundle after the
initial consent checkpoint — is closed: `capability install ./.gsd/capabilities/beads
--scope project` was re-run (commit `85aff2a`), producing a fresh consent hash bound to
the current (post-CR-01-fix) bundle content. Live re-execution of the exact three checks
the prior verification specified now shows the beads capability `"status":"active"` and
both `plan:post`/`execute:wave:post` naming `capId:"beads"` as an active dispatch step.
The full 27-test unit suite remains green, and `git status` confirms no further
uncommitted edits to the bundle that could re-invalidate consent.

Phase 1's goal — "Every gsd task exists as a beads issue, with correct status, without
anyone running `bd` by hand — and `bd` being absent, failing, or locked never blocks a
phase" — is now fully achieved at both the mechanism level (B1-B6, unchanged from the
prior pass) and the automatic-dispatch level (the previously-failing clause).

**Process note (carried forward, non-blocking):** any future code change to a file
inside `.gsd/capabilities/beads/` (a fix, a review remediation, a refactor) will again
invalidate the project-scope consent hash and silently deactivate the capability until
re-consented. Re-running `capability list --raw` / `render-hooks` after any such change
is the cheap, deterministic check to catch this before it ships.

---
*Verified: 2026-08-15T02:48:47Z*
*Verifier: Claude (gsd-verifier)*
