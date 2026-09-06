---
phase: 19-native-resolver-contract-and-failure-boundary
verified: 2026-08-31T12:52:51Z
status: passed
score: 6/6 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/6
  gaps_closed:
    - "The public CLI seam and every specified fail-closed resolver defect are proved by one-factor TDD fixtures."
  gaps_remaining: []
  regressions: []
---

# Phase 19: Native Resolver Contract and Failure Boundary Verification Report

**Phase Goal:** Live Beads content resolves losslessly through the stdlib adapter.
**Verified:** 2026-08-31T12:52:51Z
**Status:** passed
**Re-verification:** Yes — after gap closure

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | The capability's sole `beads` resolver is accepted by gsd-core and invokes the standard-library bootstrap with whole-element id transfer. | VERIFIED | `capability.json:5-12` has one `taskContentResolver`, `trackerPrefix: "beads"`, `python3 -c`, `GSD_HOME`/`Path.home()`, `os.execv`, and one separate `{{id}}` element. The manifest test passes. |
| 2 | Resolving a valid Beads issue returns one schema-valid object preserving `description`, `read_first`, `verify`, `acceptance_criteria`, and `done`. | VERIFIED | `sync.py:656-665` emits exactly those five keys. Passing public tests cover raw and versioned envelopes, duplicate lists, CRLF criteria, retained prose, and scalar sections. |
| 3 | Missing scripts, unavailable or failing `bd`, timeouts, ambiguous results, malformed JSON, invalid envelopes, and unusable content stop with diagnostics and never expose PLAN fallback prose. | VERIFIED | `sync.py:563-653` rejects each class. The missing-script bootstrap exits 2 with zero stdout. The 10 public-main tests exercise timeout, `OSError`, malformed Read First, blank/extracted-only description, plus existing nonzero, JSON, envelope, id, acceptance, and duplicate-heading failures. |
| 4 | The public CLI seam and exact typed `bd` argv are proved by isolated fixtures. | VERIFIED | `_invoke()` calls `sync.main(["resolve-task-content", issue_id])` at `test_sync.py:1206-1212`. New tests at `1222-1261` assert nonzero, empty stdout, bounded one-line stderr, stable token, and no task-body prose; the valid test asserts typed argv and `timeout=8`. |
| 5 | The inner resolver timeout is mechanically below the outer 10000 ms timeout. | VERIFIED | `sync.py:567` passes `timeout=8`; manifest `timeoutMs` is `10000` at `capability.json:10`; passing tests assert the inequality. |
| 6 | The source declaration remains inert before Phase 20 / installed cutover. | VERIFIED | `README.md:179-182` assigns tracker-id to Phase 20 and installed byte parity/cutover/Patch 2 retirement to Phase 21. Phase 19 commits contain no installed-runtime artifact. |

**Score:** 6/6 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` | Resolver and public CLI dispatch | VERIFIED | Substantive resolver, bounded diagnostics, and `main()` dispatch at `2763-2764`. |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` | Public resolver and manifest tests | VERIFIED | `TestResolveTaskContent` has 10 passing public-seam tests, including every prior RES-03 gap. |
| `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` | Sole native resolver declaration | VERIFIED | One resolver declares the stdlib bootstrap and 10000 ms outer bound. |
| `CHANGELOG.md` | 0.5.0 source-contract note | VERIFIED | States source availability only. |
| `README.md` | Inert-before-cutover boundary | VERIFIED | Documents five fields, fail-closed behavior, and Phase 20/21 ownership. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `capability.json` | `sync.py` | Python stdlib bootstrap | WIRED | The manifest bootstrap resolves the owned script and `os.execv`s `sync.py resolve-task-content` with `sys.argv[1]`. A nonexistent `GSD_HOME` target exited 2 with zero stdout. |
| `sync.py` | `bd show` | `run_bd(["bd", "show", id, "--json"], timeout=8)` | WIRED | Source at `567` and public-main argv/timeout assertion at `1270-1272`. |
| `TestResolveTaskContent._invoke` | `sync.main(["resolve-task-content", issue_id])` | Mocked `sync.run_bd` exception or payload | WIRED | `_invoke` calls the public dispatch directly; all new failure fixtures use this seam. The generic key-link query cannot resolve a test method as a file path, but source inspection proves the declared link. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- |
| `sync.py` | `payload` / `row` | `bd show <id> --json` through `run_bd` | One normalized five-field JSON object, or bounded failure | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Public resolver including all RES-03 failure classes | `TMPDIR=/dev/shm python3 -m unittest tests.test_sync.TestResolveTaskContent -v` | 10 passed | PASS |
| Capability regression suite | `TMPDIR=/dev/shm python3 -m unittest discover -s tests -t tests` | 275 passed | PASS |
| Missing installed script | Manifest bootstrap with nonexistent `GSD_HOME` | Exit 2; stdout 0 bytes; Python missing-script diagnostic | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| RES-01 | 19-01 | Standard-library installed resolver invocation | SATISFIED | Manifest bootstrap and missing-script spot-check. |
| RES-02 | 19-01 | Lossless five-field normalization | SATISFIED | Resolver output and public raw/versioned-envelope tests. |
| RES-03 | 19-01, 19-02 | Fail closed for all specified defects; no PLAN fallback | SATISFIED | Source failure branches and 10 public-main behavioral fixtures, including the four formerly absent classes. |

### Anti-Patterns Found

None in Phase 19 implementation or resolver-test additions. The Ponytail lens found no new abstraction, dependency, retry, fallback, or production change in Plan 19-02; it reuses the existing public seam and stdlib mock.

### Human Verification Required

None. This infrastructure contract's behavior is exercised by passing public-boundary tests; it has no visual or external-service UAT requirement.

### Gaps Summary

The prior RES-03 coverage gap is closed. No remaining Phase 19 gap was found.

---

_Verified: 2026-08-31T12:52:51Z_
_Verifier: the agent (gsd-verifier)_
