---
phase: 14-pr-workflow-capability-dogfood
verified: 2026-08-18T20:20:00Z
status: passed
score: 6/6 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "The capability bundle's consent hash is re-established after the last edit inside the bundle directory, so a real lifecycle dispatch actually reaches the step and the gate rather than silently deactivating (14-03-PLAN.md must_haves truth #4)."
  gaps_remaining: []
  regressions: []
tracked_upstream:
  - defect: "capability-consent.cjs::bundleContentHash walks the full capability-bundle tree with no exclusion for .gitignore-listed paths or build artifacts (e.g. __pycache__/*.pyc), so a routine test run that leaves bytecode-cache files inside the bundle dir silently invalidates consent — reproduced twice against pr-workflow this session."
    scope: "~/.claude/gsd-core/bin/lib/capability-consent.cjs — outside this repo, outside every 14-01/14-02/14-03 files_modified list. Not a phase-14 plan defect."
    interim_mitigation_applied: "14-01/14-02/14-03-PLAN.md verify commands changed from `python3 -m unittest discover ...` to `python3 -B -m unittest discover ...` (commit 8cc4f4e), preventing bytecode-cache writes inside the bundle dir. Verified this session: with -B, __pycache__ is never created and `capability list --raw` stays \"active\" across a full 27-test run. Root cause is not fixed (any invocation without -B/PYTHONDONTWRITEBYTECODE=1 still reproduces it) — a bug report against gsd-core is the durable fix, tracked separately, not blocking this phase."
    disposition: "user-directed: mark phase 14 complete; verify, root-cause, and file the gsd-core bug upstream (this session's finding + interim mitigation constitute that verification and root-cause writeup)."
---

# Phase 14: pr-workflow capability (dogfood) Verification Report

**Phase Goal:** A phase's real GitHub PR check status reaches the ship decision as visible,
advisory information, and the absence of `gh` (or of a PR) never blocks or spams.
**Verified:** 2026-08-18T20:20:00Z
**Status:** passed
**Re-verification:** Yes — second re-verification, after applying the -B interim mitigation (see Gaps Summary)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1/PRW-01: `execute:wave:post` writes `PR.md` with a `pr_status` matching live `gh pr checks`; re-run rewrites, never appends | ✓ VERIFIED | `.gsd/capabilities/pr-workflow/scripts/pr_status.py::verify_post`/`_write_report` (full-overwrite); `14-PR.md` read directly this session — frontmatter `pr_status: none`, `pr_gate_ok: true`, `pr_number: null`, `open_pr_count: 0`, `generated_from`/`generated_at` present, consistent with this repo's real `main` branch having no open PR. 27-test unit suite re-run this session, `OK`. |
| 2 | SC2/PRW-02: gate tri-state — satisfied for `none`/`passing`, unsatisfied for `pending`/`failing` | ✓ VERIFIED | `jq -e '.gates[0].check.predicate.field == "pr_gate_ok" and .gates[0].blocking == false'` re-run this session, exits 0; `14-GATE-SMOKE-TEST.md`'s four-state live transcript unchanged since prior verification, contents re-read this session |
| 3 | SC3/PRW-02: gate is advisory — a `failing` status still ships, with a visible warning naming the status | ✓ VERIFIED | `capability.json` `gates[0].blocking == false` re-confirmed via `jq`; `14-GATE-SMOKE-TEST.md` Advisory section unchanged and re-read |
| 4 | SC4/PRW-03: shipping with no open PR prints exactly one warn-only notice; `gh pr list` identical before/after, nothing created | ✓ VERIFIED | `pr_status.py::ship_post_notice`; unit tests `TestShipPostNotice` (5 cases incl. the new fail-open case) re-run this session, all pass |
| 5 | SC5/PRW-04: `gh` absent and unauthenticated each degrade to exactly one visible, distinct notice, no stale `PR.md`, no hang | ✓ VERIFIED | `NOTICE_GH_ABSENT`/`NOTICE_GH_UNAUTH` distinct constants; unit tests `TestFailOpen`, `TestNoticeDistinctness` re-run this session, all pass |
| 6 | Capability bundle consent is currently re-established, so the step and gate actually dispatch from a real lifecycle run rather than being silently inactive (14-03-PLAN.md must_haves truth #4) | ✓ VERIFIED | `capability list --raw` shows `"status": "active"`. Verify commands now use `python3 -B ...` (commit 8cc4f4e) — confirmed this session: full 27-test run with `-B` writes no `__pycache__` and consent stays `active` throughout. `loop render-hooks execute:wave:post --raw` shows the `pr-workflow`/`pr-workflow-report` step present; `loop render-hooks ship:pre --raw` shows the `pr-workflow` gate (`pr_gate_ok`, `blocking: false`) present — both re-checked directly against the fresh-consent state this session. Root-cause fix (exclude bytecode-cache/gitignored paths from `bundleContentHash`) is a gsd-core defect outside this phase's scope; tracked upstream per user direction, not blocking. |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gsd/capabilities/pr-workflow/capability.json` | manifest: 2 `steps[]`, 1 `gates[]` | ✓ VERIFIED | `jq -e '[.steps[].point] == ["execute:wave:post","ship:post"] and (.gates|length)==1'` exits 0, re-run this session |
| `.gsd/capabilities/pr-workflow/scripts/pr_status.py` | stdlib-only `gh` wrapper, all symbols present | ✓ VERIFIED | Unchanged since prior verification; all four post-review fix commits' changes still present (git log confirms no further edits since 8e0a758) |
| `.gsd/capabilities/pr-workflow/skills/pr-workflow-report/SKILL.md` | config gate + two-lifecycle-point dispatch | ✓ VERIFIED | Unchanged, previously confirmed |
| `.gsd/capabilities/pr-workflow/tests/test_pr_status.py` | stdlib unittest, full behavior coverage | ✓ VERIFIED | 27 tests, re-run this session: `Ran 27 tests in 0.007s ... OK` |
| `.gsd/capabilities/pr-workflow/tests/fixtures/*.json` | 5 synthetic fixtures | ⚠️ PARTIAL | Unchanged (info-level, non-functional; see prior verification IN-01) |
| `14-GATE-SMOKE-TEST.md` | 4-state predicate transcript + live evidence | ✓ VERIFIED | Unchanged since prior verification, re-read this session |
| `14-PR.md` | generated artifact, live run output | ✓ VERIFIED | Re-read this session; frontmatter intact and consistent with a real run against this repo |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `capability.json` `steps[execute:wave:post]` | `pr-workflow-report` skill | `ref.skill` | ✓ WIRED | `node gsd-tools.cjs loop render-hooks execute:wave:post --raw` re-run this session with a fresh (no `__pycache__`) consent state: `activeHooks` includes `{"capId":"pr-workflow","kind":"step","ref":{"skill":"pr-workflow-report"},"produces":["PR.md"]}`. The prior pass's "absent from activeHooks" finding did not reproduce once `__pycache__` was cleared and consent re-established immediately beforehand — it was the same consent-staleness bug, not a second independent issue. |
| `pr-workflow-report` skill | `pr_status.py verify-post` | Step 2 Bash dispatch | ✓ WIRED | Unchanged, re-confirmed by direct read |
| `pr_status.py verify-post` | `14-PR.md` | `_write_report`/`confined` | ✓ WIRED | Live-executed this session via the unit-test run's side-effect prints and a direct read of the committed `14-PR.md` |
| `capability.json` `gates[ship:pre]` | `PR.md`/`pr_gate_ok` | `artifact-frontmatter-equals` | ✓ WIRED | `node gsd-tools.cjs loop render-hooks ship:pre --raw` re-run this session, fresh consent state: `activeHooks` includes the `pr-workflow` gate on `PR.md`/`pr_gate_ok`, `blocking: false`. Same resolution as above. |
| `ship.md` Step 8 generic gate dispatch | `SHIP_PRE_HOOKS_JSON`/`activeHooks` | `capId != security/broken-windows`, `kind==gate` | ✓ MECHANISM CONFIRMED | `grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1'` re-run this session: `2` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| PRW-01 | 14-01 | `PR.md` artifact at `execute:wave:post`, regenerated every step | ✓ SATISFIED (code) | See Truth #1; REQUIREMENTS.md marks `[x]` |
| PRW-02 | 14-01, 14-03 | `ship:pre` gate, tri-state, advisory | ✓ SATISFIED (code) | See Truths #2, #3 |
| PRW-03 | 14-02, 14-03 | `ship:post` warn-only no-open-PR notice | ✓ SATISFIED (code) | See Truth #4 |
| PRW-04 | 14-02, 14-03 | `gh` absent/unauthenticated fail-open | ✓ SATISFIED (code) | See Truth #5 |

No orphaned requirements: REQUIREMENTS.md's Traceability table maps all 4 PRW-* IDs to Phase 14, all `[x]`.

**Resolved from prior verification:** with the `-B` interim mitigation applied to all three plans' verify commands (commit 8cc4f4e), running the mandated test suite no longer creates `__pycache__` inside the bundle dir, consent stays `active` throughout, and both `execute:wave:post`'s step and `ship:pre`'s gate are confirmed present in `loop render-hooks` output. All four requirements' behavior is now reliably exercised by a real `/gsd-execute-phase` or `/gsd-ship` run on this repo, provided the bundle dir is not mutated by a test/tool invocation outside `-B`/`PYTHONDONTWRITEBYTECODE=1` — the durable, root-cause fix in gsd-core is tracked upstream, not blocking.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `.gsd/capabilities/pr-workflow/tests/fixtures/{checks_pass,checks_pending,checks_skipping}.json` | n/a | Unused fixture files (review IN-01) | ℹ️ Info | Unchanged, non-functional |
| `.gsd/capabilities/pr-workflow/scripts/pr_status.py` | 259 | Raw exception text in committed `PR.md` (review IN-02) | ℹ️ Info | Unchanged, low priority |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found in any file under `.gsd/capabilities/pr-workflow/`.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full unit suite with `-B` | `python3 -B -m unittest discover -s .gsd/capabilities/pr-workflow/tests --pattern 'test_*.py'` | `Ran 27 tests in 0.006s / OK`, no `__pycache__` created | ✓ PASS |
| Consent active immediately after re-install | `node gsd-tools.cjs capability install ./.gsd/capabilities/pr-workflow --scope project --yes` then `capability list --raw` | `"status": "active", "reason": null` | ✓ PASS |
| Consent stays active after `-B` test run | run the `-B` unit suite above, then re-run `capability list --raw` | `"status": "active"` (unchanged) | ✓ PASS — regression fixed by interim mitigation (commit 8cc4f4e) |
| `activeHooks` at `execute:wave:post`/`ship:pre` while freshly `active` | `node gsd-tools.cjs loop render-hooks <point> --raw` | pr-workflow's step present at `execute:wave:post`, gate present at `ship:pre` | ✓ PASS |
| `ship.md` generic gate-dispatch marker present | `grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' "$HOME/.claude/gsd-core/workflows/ship.md"` | `2` | ✓ PASS |

### Probe Execution

Not applicable — same as prior verification; no `scripts/*/tests/probe-*.sh` convention used by this phase.

## Gaps Summary

**The prior gap is closed.** Root cause traced to source:
`~/.claude/gsd-core/bin/lib/capability-consent.cjs::bundleContentHash` recomputes the consent-binding
content hash by walking every file under the capability directory on disk, with no exclusion for
`.gitignore`-listed paths or build artifacts. Running the test suite via plain
`python3 -m unittest discover` causes CPython's default bytecode caching to write
`scripts/__pycache__/pr_status.cpython-314.pyc` and `tests/__pycache__/test_pr_status.cpython-314.pyc`
inside the hashed bundle directory — both `.gitignore`-listed, but included anyway by the raw
filesystem walk — which silently invalidates consent with no error, exactly the failure mode
ROADMAP's v1.2 cross-cutting constraint names, triggered here by running tests rather than editing
source. Reproduced twice, deterministically, before mitigation.

**Interim mitigation applied and verified this session (commit 8cc4f4e):** all three plans'
`<verify>` blocks now use `python3 -B -m unittest discover ...` instead of the bare command. `-B`
suppresses bytecode-cache writes entirely — re-ran the full 27-test suite with `-B` after a fresh
`capability install --yes`, confirmed zero `__pycache__`/`*.pyc` files were created, and confirmed
`capability list --raw` stayed `"status": "active"` throughout. `loop render-hooks
execute:wave:post --raw` and `loop render-hooks ship:pre --raw`, re-run against this same fresh-consent
state, both show pr-workflow's step/gate present in `activeHooks` — the previous pass's "absent from
activeHooks" observation was the same consent-staleness bug caught mid-flicker, not a second
independent issue; it did not reproduce once consent was confirmed fresh immediately beforehand.

**Not durably fixed at the root.** `capability-consent.cjs` is part of the globally-installed
gsd-core tool (`~/.claude/gsd-core/`), not this project's git repository, and is outside every
14-01/14-02/14-03 plan's `files_modified` list — the durable fix (excluding bytecode-cache/gitignored
paths from `bundleContentHash`'s walk) is a gsd-core defect, not a phase-14 defect. Per user
direction, this phase is marked complete on the strength of the in-scope interim mitigation
(verified durable against this phase's own test command), and the root cause is to be filed as a bug
report against gsd-core upstream, following its own template, as a separate piece of work outside
this phase.

**Disposition:** phase 14's four requirements (PRW-01..04) are satisfied at the code level and now
demonstrated dispatching live through the real `activeHooks` mechanism under the mitigated verify
command. Marked complete.

---

_Verified: 2026-08-18T20:20:00Z_
_Verifier: Claude (gsd-verifier), re-verification adjudicated by orchestrator per user direction_
