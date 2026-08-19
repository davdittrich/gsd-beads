---
phase: 13-markdown-linting-capability-dogfood
reviewed: 2026-08-18T00:00:00Z
depth: deep
files_reviewed: 2
files_reviewed_list:
  - .gsd/capabilities/markdown-linting/scripts/lint.py
  - .gsd/capabilities/markdown-linting/tests/test_lint.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
status: issues_found
---

# Phase 13: Code Review Report (re-review after gap-closure plan 13-04)

**Reviewed:** 2026-08-18T00:00:00Z
**Depth:** deep
**Files Reviewed:** 2
**Status:** issues_found

## Summary

This is a re-review of `lint.py` / `test_lint.py` after gap-closure plan 13-04
applied fixes for the two Critical findings (CR-01, CR-02) from the prior
`13-REVIEW.md`. Both fixes were verified by direct code read and by running
the full test suite live (real `rumdl` and `uvx` present on this machine):
all 12 tests pass, including the two tests specifically added to prove the
returncode==2 config-error path is unaffected by the widened except clause.

**CR-01 (resolved):** `main()`'s `count` branch (`lint.py:253-254`) now
raises `RuntimeError("neither rumdl nor uvx is available on PATH")` when
`resolve_rumdl_invocation()` returns `None`, before calling
`count_violations()`. This mirrors the pre-existing guard in `fix()`
(`lint.py:208-209`) and `verify_post()`'s own guard
(`lint.py:160-168`). Verified against `TestToolResolution.test_count_cli_tool_absent_raises_runtime_error`, which passes.

**CR-02 (resolved):** `count_violations()` (`lint.py:87-92`) now
distinguishes three outcomes: returncode 2 raises `RuntimeError` (config/runtime
error, deliberately NOT fail-open), returncode not in `(0, 1)` raises
`subprocess.CalledProcessError` (an unexpected crash), and `0`/`1` proceed to
`json.loads`. `verify_post()`'s except clause (`lint.py:178`) was widened
from `(TimeoutExpired, OSError)` to `(TimeoutExpired, OSError, CalledProcessError)`,
so unexpected crash codes (e.g. a panic exiting 101) now fail open with the
sentinel report, while returncode 2 still propagates uncaught and leaves the
report untouched. Verified against
`TestFailOpen.test_unexpected_exit_code_fail_open_overwrites_stale_report`
(new crash-code case) and `TestFailOpen.test_config_error_raises` (regression
guard for the returncode==2 path), both passing.

No regression found in the returncode==2 config-error path, and no
interaction bug between the two fixes (the `None`-guard and the widened
except clause touch disjoint code paths — CLI arg parsing vs. subprocess
result classification).

Three new Warnings surfaced during this deep pass — none reopen CR-01/CR-02,
all are pre-existing gaps in code the gap-closure diff did not touch, found
while tracing the full call chain from `main()` through `fix()` and
`count_violations()`.

## Warnings

### WR-01: `fix()` ignores the `check --fix` subprocess's returncode and drops its stderr

**File:** `.gsd/capabilities/markdown-linting/scripts/lint.py:215-217`
**Issue:** `fix()` runs `rumdl check --fix ...` and unconditionally proceeds:

```python
result = subprocess.run(check_argv, capture_output=True, text=True, timeout=60)
print(result.stdout, end="")
post_fix_count = count_violations(config_path, targets, rumdl_argv)
```

Unlike `count_violations()` (which now classifies returncode 2 vs. other
non-{0,1} codes per CR-02), this call never inspects `result.returncode`,
and `result.stderr` is never printed or surfaced anywhere. If the fix pass
itself crashes or panics (e.g. a rumdl bug triggered specifically by
`--fix`, or a genuine config error), the failure is silently discarded here.
The very next line calls `count_violations()` — a separate, non-`--fix`
invocation — which happens to re-validate the same config and would likely
reproduce a deterministic config error, but would NOT catch a transient or
`--fix`-specific crash, since that second call takes a different code path
(no `--fix` flag). The diagnostic stderr from the actual failing invocation
is lost either way.
**Fix:** Apply the same returncode discipline used in `count_violations()`:

```python
result = subprocess.run(check_argv, capture_output=True, text=True, timeout=60)
print(result.stdout, end="")
if result.returncode == 2:
    raise RuntimeError(f"rumdl config/runtime error: {result.stderr}")
if result.returncode not in (0, 1):
    raise subprocess.CalledProcessError(
        result.returncode, check_argv, result.stdout, result.stderr
    )
post_fix_count = count_violations(config_path, targets, rumdl_argv)
```

### WR-02: `verify_post()`'s fail-open except clause does not cover malformed JSON on a nominally successful returncode

**File:** `.gsd/capabilities/markdown-linting/scripts/lint.py:93, 178`
**Issue:** `count_violations()`'s final line is `return len(json.loads(result.stdout))`,
reached whenever `result.returncode` is 0 or 1. If rumdl ever emits
non-JSON or truncated stdout while still exiting 0/1 (disk-full mid-write,
an upstream rumdl regression, a pipe/encoding edge case), `json.loads`
raises `json.JSONDecodeError` (a `ValueError` subclass). `verify_post()`'s
except tuple is `(subprocess.TimeoutExpired, OSError, subprocess.CalledProcessError)`
(`lint.py:178`) — `JSONDecodeError` is not a member of any of those, so it
propagates uncaught out of `verify_post()` and crashes the `ship:pre` gate
invocation entirely, which is exactly the outcome MDL-04's fail-open design
is meant to prevent ("a lint count where the linter never ran" should
degrade to the `unavailable` sentinel, not a hard crash). This is a narrow
edge case (it requires rumdl to violate its own exit-code/output contract),
but it is a real gap in the enumerated fail-open trigger set the docstring
describes ("TimeoutExpired/OSError, ... unexpected crash code").
**Fix:** Add `json.JSONDecodeError` to the except tuple in `verify_post()`
(and document it in the docstring's enumerated trigger list):

```python
except (subprocess.TimeoutExpired, OSError, subprocess.CalledProcessError,
        json.JSONDecodeError) as exc:
```

### WR-03: `fix()` has zero test coverage

**File:** `.gsd/capabilities/markdown-linting/tests/test_lint.py` (whole file)
**Issue:** No test class in `test_lint.py` calls `lint.fix()`. All five test
classes (`TestFailOpen`, `TestCuratedRuleset`, `TestReportMatchesHandRun`,
`TestToolResolution`, `TestEmptyTargetSet`) exercise `verify_post()`,
`count_violations()`, or `main(["count"])`, but the third CLI subcommand —
`fix`, the one that actually mutates files via `--fix` — is entirely
untested. This is why WR-01 (returncode/stderr dropped in `fix()`) shipped
undetected: there is no test that would fail if `fix()` silently swallowed
a crashing `check --fix` invocation.
**Fix:** Add at minimum one test mocking `subprocess.run` to return a
non-{0,1} returncode for the `check --fix` call and asserting `fix()`
raises (once WR-01 is fixed), plus one happy-path test asserting the
post-fix count is printed. A `unittest.mock.patch("subprocess.run", ...)`
with `side_effect` keyed on `"--fix" in args[0]` (mirroring the existing
`shutil.which` side_effect pattern already used elsewhere in this file)
is sufficient — no new fixtures needed.

---

_Reviewed: 2026-08-18T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
