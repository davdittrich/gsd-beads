---
phase: 17-config-code-truth
reviewed: 2026-08-20T00:00:00Z
depth: deep
files_reviewed: 11
files_reviewed_list:
  - CHANGELOG.md
  - docs/prd-beads-capability.md
  - .gsd-capabilities.json
  - plugins/beads-lifecycle/.agents/skills/beads/PRIME.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
  - plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
  - README.md
findings:
  critical: 0
  warning: 5
  info: 0
  total: 5
status: issues_found
---

# Phase 17: Code Review Report

**Reviewed:** 2026-08-20
**Depth:** deep
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed `sync.py`'s TRUTH-01..04 changes (decimal phase resolution via `phase_regex_token`/
`phase_dir_prefix`, the `check_native_step_dispatch` version-skew probe, `beads.sync_mode` truth
via `check_sync_mode_value`/`SYNC_MODE_VALUES`, and the `check_patch`/`PATCH_CHECKS`
table-driven collapse), cross-checked against `capability.json`, both `SKILL.md` files,
`GSD-CORE-PATCH.md`, `README.md`, `CHANGELOG.md`, the PRD, and `PRIME.md`, and traced call
chains through `lifecycle_dispatch` and `main()`.

The core algorithmic changes are correct: `phase_regex_token`/`phase_dir_prefix` handle every
boundary case in `TestDecimalPhase` (leading zeros, decimal vs. integer adjacency, `re.escape`
discipline, empty input) without ever calling `int()`/`float()`/`Decimal()`; `SYNC_MODE_VALUES`
membership logic in `check_sync_mode_value` correctly distinguishes "key absent" from
"key present, wrong type" via a raw membership test as its own docstring requires; the
`check_patch`/`PATCH_CHECKS` collapse preserves every pinned message string and exit-code
contract from the two functions it replaces; no `shell=True`, `eval`, hardcoded secret, or
unbounded subprocess call was introduced. No security or correctness BLOCKER was found.

What did surface, ironically given this phase's own "config/code truth" theme, is a cluster of
doc-vs-code and test-vs-implementation truth gaps *within this same diff*: a docstring that
misdescribes a sibling function's actual output stream, two failure-message templates that
silently fall outside the "⚠ triggers surfacing" convention the SKILL.md files instruct the
orchestrator to follow, a `CHANGELOG.md` 0.4.0 entry that omits an entire new mechanism this
phase added, and a duplicated enum (`SYNC_MODE_VALUES` vs. `capability.json`) with no direct
parity test binding the two copies together. All five are WARNING-level: none causes incorrect
runtime behavior today, but each is exactly the class of silent drift this phase exists to close.

## Warnings

### WR-01: `check_sync_mode_value`'s docstring misdescribes `check_patch`'s actual output stream

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:802-804` (docstring) vs.
`plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:2296-2322` (`check_patch` body)

**Issue:** `check_sync_mode_value`'s docstring states: *"Prints to STDOUT -- the opposite of
`check_shipmd_patch`/`check_execute_plan_patch`'s stderr-only benign-skip convention."* This is
false. `check_patch` (the function both `check_shipmd_patch` and `check_execute_plan_patch` now
thin-wrap, per the 17-04 collapse) prints every one of its four message paths —
`not_found_msg`, `could_not_read_msg`, `present_msg`, `missing_msg` — via a bare `print(...)`
with no `file=` argument, i.e. **stdout in every case**, never stderr. This is confirmed by
`TestCheckShipmdPatch`/`TestCheckExecutePlanPatch` (test_sync.py:3206-3374), which both capture
these calls with `contextlib.redirect_stdout` and assert the message lands there. The claimed
"stderr-only benign-skip convention" does not exist anywhere in the current implementation.

Confidence: 95 (exact code read; contradicted directly by the test suite's own redirect target).

**Why it matters:** the current *behavior* (stdout) is actually the correct one — it's what lets
`hooks/lifecycle-dispatch.sh` promote a "⚠ patch missing" warning into `additionalContext`, per
this same file's own comments elsewhere ("the whole point of this notice is that a user
encounters it without taking any action"). But a future maintainer who trusts this docstring's
claim about the *sibling* functions, rather than reading `check_patch` itself, could "fix"
`check_patch` to route through stderr to match the described convention — which would silently
stop patch-loss warnings from ever reaching the hook's `additionalContext`, the exact silent
failure mode `GSD-CORE-PATCH.md` and Step 3.5 of `beads-recall/SKILL.md` were built to prevent.

**Fix:** correct the docstring to state the true, current behavior — `check_shipmd_patch`/
`check_execute_plan_patch` also print unconditionally to stdout, same as `check_sync_mode_value`
— and drop the "opposite of / stderr-only" framing, or add a one-line explicit code comment on
`check_patch`'s final `print(...)` call pinning "stdout is deliberate; the hook promotes only
stdout" so the two docstrings cannot drift apart from the code again.

### WR-02: `not_found_msg`/`could_not_read_msg` never carry the "⚠" marker the SKILL.md files gate surfacing on

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:142-179` (`PATCH_CHECKS`
`not_found_msg`/`could_not_read_msg`/`missing_msg` entries) vs.
`plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md:76` and
`plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md:149`

**Issue:** Both `SKILL.md` files instruct the orchestrator: *"If either output contains the '⚠'
warning line, surface it to the user verbatim."* Only `missing_msg` (both `ship-md` and
`execute-plan` entries) is prefixed with `"⚠ ..."`. `not_found_msg` and `could_not_read_msg` —
the cases where the target workflow file doesn't exist at all (e.g. a misconfigured
`CLAUDE_CONFIG_DIR`, or gsd-core not installed where expected) or can't be decoded — are plain
text with no `⚠` prefix, even though `check_patch` returns the identical exit code `1` for all
three non-present cases. Per the SKILL.md's literal instruction, an LLM orchestrator following
it would surface a "missing marker" warning but silently skip a "file not found" or
"could not be read" one — arguably the more severe, harder-to-self-diagnose failure of the two,
since it means the patch state could not even be checked.

Confidence: 85 (verified against the literal message templates and the literal SKILL.md
instruction text; the gap is not new to this phase's refactor — `TestPatchChecksTable` pins the
message text verbatim from before the 17-04 collapse — but it remains present in the reviewed
code and both reviewed `SKILL.md` files).

**Fix:** either (a) prefix `not_found_msg` and `could_not_read_msg` with `"⚠ "` too, so every
non-present outcome is uniformly surfaced under the existing convention, or (b) broaden the
SKILL.md instruction from "contains '⚠'" to "exit code is non-zero" / "does not contain
'present'", since `check_patch`'s exit code already distinguishes present (0) from every other
case (1) more reliably than a substring grep on the message text.

### WR-03: `CHANGELOG.md`'s 0.4.0 entry omits the native-step-dispatch-probe feature this phase added

**File:** `CHANGELOG.md` (0.4.0 section, entirely absent) vs.
`plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:193-216,2342-2460` and
`plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md:245-302`

**Issue:** `CHANGELOG.md` (whose own header states "Versions in this file track
`capability.json`") documents TRUTH-04 (decimal phase resolution) under Fixed, TRUTH-02
(patch-check collapse) under Breaking, and the `beads.sync_mode` truth work under Changed — but
contains zero mentions of `native`, `3687`, or "step dispatch" anywhere. `check_native_step_dispatch`,
its two module constants (`NATIVE_STEP_DISPATCH_WORKFLOW_FILES`,
`NATIVE_STEP_DISPATCH_REGION_LINES`), and `lifecycle_dispatch`'s new stand-down branches at
`plan:post`/`verify:post` were added in this same phase (`git log -S"NATIVE_STEP_DISPATCH_WORKFLOW_FILES"`
→ commit `2e788ea feat(17-02): gate plan:post on native-step-dispatch probe (Task 1)`, followed
by `45146ac feat(17-02): gate verify:post on native-step-dispatch probe (Task 2)`), and are
extensively documented in `GSD-CORE-PATCH.md`'s "Probe (not a patch)" section and covered by 13
test classes/methods (`TestNativeStepDispatchProbe`,
`TestNativeStepDispatchProbeAgainstInstalledTree`, `TestLifecycleDispatchNativeGate`). None of
this reaches `CHANGELOG.md`.

Confidence: 85 (confirmed via `git log -S` against the actual introducing commits, and a direct
grep of `CHANGELOG.md` for every plausible keyword).

**Why it matters:** this is the exact "declared/implemented but nowhere documented" pattern this
whole phase's theme (config/code truth) exists to eliminate — applied here to the changelog
itself rather than to `capability.json`. A user reading 0.4.0's changelog to understand what
changed has no way to learn that `sync.py` now silently stands down at `plan:post`/`verify:post`
once gsd-core ships PR #3687, which is exactly the kind of behavior change (new dispatch
skip-condition) the changelog exists to surface.

**Fix:** add a `CHANGELOG.md` 0.4.0 entry (Added or Changed) describing
`check_native_step_dispatch` and the `plan:post`/`verify:post` stand-down behavior, naming PR
#3687 the way `GSD-CORE-PATCH.md` already does, in the same commit that ships the rest of this
phase's changelog updates.

### WR-04: `SYNC_MODE_VALUES` has no direct parity test against `capability.json`'s declared array

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:770-776` vs.
`plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:32-40` vs.
`plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:4993-5032`
(`TestSyncModeDeclarationParity`)

**Issue:** `SYNC_MODE_VALUES = frozenset({"authoritative", "mirror"})` is `check_sync_mode_value`'s
sole runtime source of truth for "is this a declared value," and its own comment explains it is
a **deliberate duplicate** of `capability.json`'s `beads.sync_mode.values` array ("sync.py never
reads that file"). `TestSyncModeDeclarationParity` pins `capability.json`'s array against a
hardcoded `["authoritative", "mirror"]` literal and a hardcoded `COVERING_TESTS` dict — but no
test anywhere asserts `sync.SYNC_MODE_VALUES == frozenset(capability.json's declared values)`
directly. `TestPatchChecksTable`'s own docstring names this exact class of gap ("the blind spot
commit `966315a` exploited... because no test asserted either marker's literal string") as the
reason that class of test exists — the same blind spot is open here, one enum over.

Confidence: 75 (confirmed no test references `sync.SYNC_MODE_VALUES` anywhere in the test file;
the risk itself — someone editing one copy of the enum without the other — is inferred, not
directly observed).

**Fix:** add one test asserting `sync.SYNC_MODE_VALUES == frozenset(json.loads(capability.json)["config"]["beads.sync_mode"]["values"])`, mirroring `TestSyncModeDeclarationParity`'s existing
`CAPABILITY_PATH` fixture, so a future edit to either copy without the other fails immediately.

### WR-05: `check_native_step_dispatch`'s detection loop does not exclude fenced-block lines from the `kind == "step"` match

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:2426-2453`

**Issue:** The function tracks `in_fence` state carefully to decide *where the scanned region
ends* (a heading inside a fenced output template must not prematurely terminate the region — the
docstring calls this out explicitly and `test_shipped_1_11_0_verify_work_shape_is_not_detected`
covers the analogous heading case). But the final detection loop —
`for line in lines[anchor_idx:region_end]: if _GENERIC_STEP_KIND_RE.search(line) and not
_STEP_QUALIFIER_RE.search(line): return 1` — does not consult `in_fence` at all. An unqualified,
literal `kind == "step"` mention inside a fenced code/documentation example that happens to fall
within the anchor's region (rather than in live dispatch prose) would still register as
"detected," causing `lifecycle_dispatch` to stand down at `plan:post`/`verify:post` even though
gsd-core does not actually dispatch generic `kind == "step"` hooks there — the wrong failure
direction per this function's own stated contract ("every miss... returns 0 (not detected)...
the only acceptable failure direction"). No test in `TestNativeStepDispatchProbe` exercises an
unqualified `kind == "step"` line that sits specifically *inside* a fence within the region
(only the region-boundary-heading-in-fence case and the whole-file, outside-region false
positives from the real 1.11.0 files are covered).

Confidence: 55 (the control-flow gap is directly verifiable in the code; whether it manifests
against the *actual* installed `plan-phase.md`/`verify-work.md` content is unverified — those
files are outside this review's file list, and `TestNativeStepDispatchProbeAgainstInstalledTree`
currently passes against them, so this is a latent gap rather than a confirmed live defect).

**Fix:** either add `if in_fence: continue` inside the final detection loop (excluding fenced
lines from the `kind == "step"` match, not just from heading detection), or add a regression
test constructing a region that contains an unqualified `kind == "step"` string inside a fenced
example block, to pin whichever behavior is intended.

---

_Reviewed: 2026-08-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
