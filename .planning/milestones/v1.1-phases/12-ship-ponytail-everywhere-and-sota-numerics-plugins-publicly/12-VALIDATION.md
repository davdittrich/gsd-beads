---
phase: 12
slug: ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-17
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Stdlib-only bash smoke test (`tests/test-session-start.sh`, both plugins) + stdlib `unittest` (`sota-numerics/tests/test_check_alternatives.py`) — no third-party framework, matches N5 constraint |
| **Config file** | None — self-contained `set -u` bash + plain `unittest` |
| **Quick run command** | `bash tests/test-session-start.sh` (both plugins); `python3 -m unittest tests/test_check_alternatives.py` (sota-numerics only) |
| **Full suite command** | Same as quick run — entire test surface per plugin is these 1-2 files |
| **Estimated runtime** | ~5 seconds per plugin |

---

## Sampling Rate

- **Per extraction (each plugin):** run `bash tests/test-session-start.sh` (+ `python3 -m unittest tests/test_check_alternatives.py` for sota-numerics) inside the staged extraction directory, before `gh repo create` — must pass with the Pitfall 1 `REPO_ROOT` path fix already applied
- **Per push:** `claude plugin validate . --strict` against the freshly cloned/pushed public repo
- **Phase gate (before `/gsd-verify-work`):** full D-10 round trip (`/plugin marketplace add` → `/plugin install` → `/plugin uninstall`) against both pushed repos, plus a re-parse sanity check that `beads-lifecycle`'s untouched `source: "./"` entry still resolves after the marketplace.json edit
- **Max feedback latency:** ~10 seconds (local script + CLI validate, no network round trip until the push/round-trip steps)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-01-* | 01 | 1 | D-01/D-03/D-04 (ponytail-everywhere extraction) | — | Extracted repo's `session-start.sh` resolves paths post-move (REPO_ROOT fix applied) | smoke | `bash tests/test-session-start.sh` | ✅ exists, needs Pitfall 1 fix | ⬜ pending |
| 12-02-* | 02 | 1 | D-01/D-03/D-04 (sota-numerics extraction) | — | Same, plus gate logic unaffected by relocation | smoke + unit | `bash tests/test-session-start.sh`; `python3 -m unittest tests/test_check_alternatives.py` | ✅ both exist, smoke test needs Pitfall 1 fix; unit test unaffected | ⬜ pending |
| 12-03-* | 03 | 2 | D-02 (marketplace.json git-source entries) | Nested-repo tampering; premature marketplace edit (see Security Domain) | Two `{"source": "github", "repo": "owner/repo"}` entries replace local Directory sources, only after both repos pass D-10 | manual (CLI) | `claude plugin validate . --strict` (gsd-beads root, confirms marketplace.json still parses) | N/A — CLI tool | ⬜ pending |
| 12-04-* | 04 | 2 | D-09/D-10 (validate + round trip, both new repos) | Public push exposing machine-local state | Clean `validate --strict`; real install/uninstall round trip | manual/E2E | `claude plugin validate . --strict`; `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` | N/A — requires interactive session, cannot be scripted headlessly | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Exact task IDs assigned by the planner — this map anchors on decision IDs, not final task numbers.*

---

## Wave 0 Requirements

*None — existing test infrastructure (bash smoke test + Python unittest, both already present in each plugin subdirectory) covers all phase requirements once the extraction sequence includes the Pitfall 1 fix and runs the existing tests locally before each push.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|--------------------|
| Marketplace add → install → uninstall round trip | D-10 | Requires a live interactive Claude Code session against the real pushed public repo; cannot be scripted headlessly | Run `/plugin marketplace add davdittrich/gsd-beads` (or re-add if already present), then `/plugin install ponytail-everywhere@gsd-beads -y`, confirm the plugin loads, then `/plugin uninstall`. Repeat for `sota-numerics@gsd-beads`. |
| `claude plugin validate . --strict` clean at each new repo root | D-10 | CLI tool output, not a scriptable unit-test assertion | Run from inside each freshly cloned/pushed repo; confirm exit 0 with no warnings promoted to errors |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references — N/A, none identified
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s (local checks); manual round-trip is the one exception, documented above
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
