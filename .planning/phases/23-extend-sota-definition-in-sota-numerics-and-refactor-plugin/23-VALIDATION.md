---
phase: "23"
slug: "extend-sota-definition-in-sota-numerics-and-refactor-plugin"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-06"
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

**Working tree for every command below:** `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013` — the `sota-numerics` clone. This phase changes no file in `gsd-beads`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (stdlib) + two Bash smoke scripts — all pre-existing |
| **Config file** | none — CI invokes the scripts directly (`.github/workflows/ci.yml`) |
| **Quick run command** | `python3 -m unittest tests/test_check_alternatives.py` |
| **Full suite command** | `bash tests/test-session-start.sh && bash tests/test-gate-script-resolution.sh && python3 -m unittest tests/test_check_alternatives.py` |
| **Estimated runtime** | ~3 seconds (measured 2026-09-06: unittest 1.5s over 50 tests, both smoke scripts under 1s each) |

Baseline captured 2026-09-06 on `origin/main` `eccad87`, before any Phase 23 edit: 50 tests `OK`, both smoke scripts `ALL PASS`. Any red after a Phase 23 commit is caused by that commit.

---

## Sampling Rate

- **After every task commit:** Run `python3 -m unittest tests/test_check_alternatives.py`
- **After every plan wave:** Run the full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 3 seconds

The whole suite is faster than the quick command on most projects, so there is no reason for any task to skip it.

---

## Per-Task Verification Map

No `REQ-ID` maps to this phase — `REQUIREMENTS.md`'s traceability table covers only the beads-capability v1.4 requirements (`RES-01`..`CUT-02`), none of which reference Phase 23. Coverage is therefore traced to CONTEXT.md decision IDs instead.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| assigned by planner | — | — | D-01 (gate behavior unchanged) | — | Untrusted `PLAN.md` parsing unchanged | unit | `python3 -m unittest tests/test_check_alternatives.py` | ✅ | ⬜ pending |
| assigned by planner | — | — | D-05, D-07 (fragments still materialize) | — | N/A | smoke | `bash tests/test-session-start.sh` | ✅ | ⬜ pending |
| assigned by planner | — | — | D-17 (gate script still resolves at both scopes) | — | Global-scope fallback intact | smoke | `bash tests/test-gate-script-resolution.sh` | ✅ | ⬜ pending |
| assigned by planner | — | — | D-08 (fragment line budget ≤ 45) | — | N/A | unit | `test "$(cat .gsd/capabilities/sota-numerics/fragments/*.md \| wc -l)" -le 45` | ✅ | ⬜ pending |
| assigned by planner | — | — | D-19, D-23 (both version fields agree, manifests parse) | — | N/A | unit | `python3 -c "import json;a=json.load(open('.claude-plugin/plugin.json'))['version'];b=json.load(open('.gsd/capabilities/sota-numerics/capability.json'))['version'];assert a==b=='0.2.0',(a,b)"` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

The last two rows are one-line shell assertions over files this phase edits, not new test infrastructure — D-21 forbids a test framework for prose, not a `wc -l` comparison the plan already owes as evidence under D-20.

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.* The Python suite and both smoke scripts already cover every behavior this phase can regress: gate logic, fragment materialization at session start, and gate-script path resolution across project and global scope. D-21 forbids adding test infrastructure for the prose changes themselves.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Every behavioral claim in `README.md` traces to a line of code or config | D-20 | Tracing prose to source is a judgment, not a predicate — the same reason D-01 keeps the six added dimensions out of the blocking gate | For each claim in `README.md`'s "What it changes" table and prose, name the file and line that makes it true; a claim with no such line is either wrong or the code is missing |
| The four fragments read as one grown standard rather than two standards sharing a file | CONTEXT `<specifics>` | Coherence of prose has no automated predicate | Read all four fragments end to end in one sitting; the added dimensions must use the same leading words (`with the grain`, `quiet`, `legible`) the phase defines, not synonyms |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 3s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
