---
phase: "19"
slug: "native-resolver-contract-and-failure-boundary"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-08-30"
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python standard-library `unittest` |
| **Config file** | none |
| **Quick run command** | `cd plugins/beads-lifecycle/.gsd/capabilities/beads && python3 -m unittest discover -s tests -t tests` |
| **Full suite command** | `cd plugins/beads-lifecycle/.gsd/capabilities/beads && python3 -m unittest discover -s tests -t tests` |
| **Estimated runtime** | Measure during execution; no unsupported estimate |

---

## Sampling Rate

- **Before Phase 19 execution:** Validated prerequisite ticket
  `gsd-beads-byp` must report live status `closed`, then the exact full
  capability suite must exit 0. The combined fail-closed Wave 0 command below
  checks both before Task 1.
  The 2026-08-30 current-state run produced 263 tests with eight failures and
  one error in lifecycle-dispatch/native-step-detection behavior after
  installed gsd-core changed. Separate Beads-tracked prerequisite work must
  reconcile that subsystem first; Phase 19 must halt rather than absorb it or
  call the failures informational.
- **After every task commit:** Run the focused resolver or manifest test, then
  require the full capability suite to remain green.
- **After every plan wave:** Run the full capability suite and installed
  manifest validator.
- **Before `$gsd-verify-work`:** Full capability suite must be green.
- **Max feedback latency:** One blocking test invocation; no watch mode.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | Observable failure | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|--------------------|-------------|--------|
| Task 1 | 19-01 | 1 | RES-02, RES-03 | T-19-02 | Canonical producer output plus independent leading-prose, unknown-H2, near-match-H2, and single-failure arms prove the five-field/fail-closed adapter. | public CLI/unit | Focused `TestResolveTaskContent`, then full capability discovery | Missing class; mapping/byte retention differs; a failure arm returns zero or writes stdout; exact `bd` argv differs; focused or full command exits nonzero. | ✅ extend `tests/test_sync.py` | ⬜ pending |
| Task 2 | 19-01 | 1 | RES-01, RES-03 | T-19-01, T-19-04 | Exact `["-c", bootstrap, "{{id}}"]` declaration is validator-clean and preserves `sys.argv == ["-c", id]`; one reused public-resolver subprocess wrapper over isolated `GSD_HOME` fixtures proves missing script as `ResolverFailedError` plus `missing script`, and timeout as a separately observed thrown `ResolverTimeoutError` plus wrapper-level `ResolverTimeoutError`/`resolver timeout`, with each command nonzero, stdout exactly empty, and exactly one stderr diagnostic no longer than 2000 characters. | manifest/integration | Both focused Phase 19 classes, then full capability discovery | Exact argv/version or `sys.argv[1]` differs; validator/execv transfer fails; either failure category token is absent; either command returns zero, stdout is nonempty, stderr has other than one diagnostic, or stderr exceeds 2000 characters; timeout throw is conflated with wrapper exit/streams; fixtures differ beyond missing script versus sleeping probe; focused or full command exits nonzero. | ✅ extend `tests/test_sync.py` | ⬜ pending |

---

## Wave 0 Requirements

Existing test infrastructure covers all phase requirements. Wave 0 is
conditionally complete only when `bash -lc "set -euo pipefail; cd
/home/dd/projects/gsd-beads; bd show gsd-beads-byp --json | jq -e
'.[0].status == \"closed\"'; cd
plugins/beads-lifecycle/.gsd/capabilities/beads; python3 -m unittest discover
-s tests -t tests"` exits 0. This proves both that the validated distinct
lifecycle-dispatch compatibility ticket `gsd-beads-byp` is live-closed and
that the exact full capability suite is green; `set -euo pipefail` halts before
Task 1 when either observation fails. The ticket owns repair outside Phase 19,
while focused resolver/bootstrap fixtures remain inside the two Phase 19 TDD
tasks.

---

## Manual-Only Verifications

All Phase 19 behaviors have automated verification. Installed cutover evidence
belongs to Phase 21.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify commands with explicit
  `<fails_when>` signals.
- [ ] Sampling continuity: no task lacks automated verification.
- [ ] Blocking prerequisite: live `bd show gsd-beads-byp --json` reports
  `status: closed` and the exact full capability suite exits 0 in the current
  installed-runtime environment before Task 1 starts; either failure halts
  autonomous Phase 19 execution.
- [x] Wave 0 needs no new Phase 19 test infrastructure.
- [x] No watch-mode flags.
- [ ] Feedback latency measured during execution.
- [ ] `nyquist_compliant: true` set after execution evidence exists.

**Approval:** pending
