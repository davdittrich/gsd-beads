---
phase: 14-pr-workflow-capability-dogfood
reviewed: 2026-08-18T17:13:46Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - .gsd/capabilities/pr-workflow/capability.json
  - .gsd/capabilities/pr-workflow/scripts/pr_status.py
  - .gsd/capabilities/pr-workflow/skills/pr-workflow-report/SKILL.md
  - .gsd/capabilities/pr-workflow/tests/test_pr_status.py
  - .gsd/capabilities/pr-workflow/tests/fixtures/*.json
  - .planning/phases/14-pr-workflow-capability-dogfood/14-GATE-SMOKE-TEST.md
  - .planning/phases/14-pr-workflow-capability-dogfood/14-PR.md
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-08-18T17:13:46Z
**Depth:** standard
**Files Reviewed:** 7 (plus 5 JSON fixtures)
**Status:** issues_found

## Summary

Reviewed the `pr-workflow` capability's full vertical slice (`capability.json`, `pr_status.py`,
`pr-workflow-report/SKILL.md`, `test_pr_status.py` + fixtures) plus the two phase docs
(`14-GATE-SMOKE-TEST.md`, `14-PR.md`). No `shell=True`, no string-assembled `subprocess`
commands, and no hardcoded credentials were found -- every `gh`/`git` invocation uses an argv
list, and the two `gh`-unavailable notice strings are fixed constants that never echo captured
`gh`/`git` stderr, so the plan's own "no captured stderr in a notice" prohibition holds. The
core defect found is a real asymmetry between `verify_post()` (which has a documented,
partially-tested fail-open boundary) and `ship_post_notice()` (which has none at all, despite its
own docstring claiming "Returns 0 on every path"). A second, related gap is that `find_open_pr()`'s
blanket `RuntimeError`-on-any-nonzero-exit is not covered by `verify_post()`'s fail-open `except`
tuple and is untested, unlike the analogous (and deliberately-tested) case in `check_buckets()`.

## Critical Issues

### CR-01: `ship_post_notice()` has no fail-open handling and can crash the `ship:post` dispatch, contradicting its own docstring

**File:** `.gsd/capabilities/pr-workflow/scripts/pr_status.py:249-269`
**Issue:** `ship_post_notice()`'s docstring states "Returns 0 on every path" (line 255), but the
function body has no `try`/`except` around `current_branch()` (line 265) or `find_open_pr()`
(line 266). Contrast with `verify_post()` (lines 199-238), which wraps the equivalent calls in
`try: ... except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):` specifically to
satisfy PRW-04's fail-open guarantee. `ship_post_notice()` has no such guard:
- If `find_open_pr()` raises `RuntimeError` (any `gh pr list` non-zero exit -- rate limiting,
  transient API 5xx, network hiccup after `gh_available()`'s earlier `auth status` call already
  succeeded), the exception propagates uncaught out of `ship_post_notice()` and out of `main()`,
  producing a traceback and non-zero process exit instead of the "warn-only, never fails a phase"
  behavior the `SKILL.md` and `capability.json` (`ship:post` step, `onError: "skip"`) assume the
  script itself provides at the process level.
- Same for `subprocess.TimeoutExpired`/`OSError`/`json.JSONDecodeError` raised by `current_branch()`
  or `find_open_pr()` -- these are the exact three transient-error types `verify_post()` explicitly
  guards against, but `ship_post_notice()` has zero handling for any of them.
- `test_pr_status.py`'s `TestShipPostNotice` (4 cases: no-open-PR, open-PR, gh-absent,
  never-reads-PR.md) has no test exercising a `gh pr list` failure/timeout during
  `ship_post_notice()`, so this gap shipped without a red test ever forcing the question.

**Fix:** Wrap the two live calls the same way `verify_post()` does:
```python
    try:
        branch = current_branch()
        prs = find_open_pr(branch)
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        print(NOTICE_GH_ERROR)
        return 0
    if not prs:
        print(f"{NOTICE_NO_OPEN_PR} (branch: {branch})")
    return 0
```
Add a `TestShipPostNotice` case mocking a `TimeoutExpired`/nonzero `gh pr list` to prove the new
guard, mirroring `TestFailOpen::test_gh_pr_list_timeout_fail_open`.

## Warnings

### WR-01: `find_open_pr()`'s blanket `RuntimeError` on any `gh pr list` failure is not covered by `verify_post()`'s fail-open except tuple, and is untested

**File:** `.gsd/capabilities/pr-workflow/scripts/pr_status.py:88-98`, called from `verify_post()` at line 202 inside the `try` at line 229
**Issue:** `find_open_pr()` raises `RuntimeError(f"gh pr list failed: {result.stderr}")` for
*any* non-zero exit of `gh pr list`, with no distinction between "genuine tool failure" and a
transient/rate-limit condition -- unlike `check_buckets()` (lines 108-121), which explicitly
carves out the documented "zero checks" stderr strings as benign before raising for anything else,
and which has a dedicated deliberately-uncaught-exception test
(`test_checks_unrelated_stderr_raises`). `verify_post()`'s `except (subprocess.TimeoutExpired,
OSError, json.JSONDecodeError)` at line 229 does **not** catch `RuntimeError`, so a `gh pr list`
call that fails with a non-zero exit for a reason that is not a raised `OSError`/`TimeoutExpired`
(e.g. an HTTP 403 rate-limit or a transient 5xx surfaced by `gh` as a clean non-zero exit with
stderr text, not an OS-level exception) crashes `verify_post()` with an uncaught `RuntimeError`
instead of degrading to the `pr_status: unavailable` sentinel PRW-04 requires. There is no test
in `test_pr_status.py` covering this specific path (a `gh pr list` non-zero exit that is *not* a
`TimeoutExpired`), so this asymmetry with `check_buckets()`'s (tested, intentional) behavior is
unproven either way.
**Fix:** Either (a) explicitly document + test that a `gh pr list` non-zero exit is intentionally
left uncaught (matching `check_buckets()`'s documented rationale), or (b) fold `RuntimeError` from
`find_open_pr()` into the same fail-open path as the other transient errors, since from the
caller's perspective a `gh pr list` failure is exactly as "gh call blew up after the availability
guard passed" as a timeout. Given `PRW-04`'s stated scope ("gh degraded" should fail open broadly),
option (b) is the safer default:
```python
except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError, RuntimeError) as exc:
```
(Note: this would need to explicitly re-exclude `check_buckets()`'s deliberate-uncaught case if
merged this way, e.g. by having `check_buckets()` raise a distinct exception type from
`find_open_pr()`.)

### WR-02: `current_branch()` does not check `subprocess.run`'s `returncode`

**File:** `.gsd/capabilities/pr-workflow/scripts/pr_status.py:81-85`
**Issue:** `current_branch()` returns `result.stdout.strip()` unconditionally, with no check of
`result.returncode`. If `git branch --show-current` fails (corrupted repo, git binary present but
misbehaving, worktree edge case), `stdout` is typically empty and the function silently returns
`""`. That empty string is then used as the `--head` value for `gh pr list --head "" --state
open`, which will most likely resolve to `[]` ("no open PR") -- masking a genuine git failure as
`pr_status: none` / `pr_gate_ok: true` (a **passing** gate result) rather than surfacing it as
`unavailable`. This is the one live-`git`-call path in the script with no error signal at all,
unlike every `gh` call site, which all check `returncode`.
**Fix:**
```python
def current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git branch --show-current failed: {result.stderr}")
    return result.stdout.strip()
```
This raised `RuntimeError` would then need the same fail-open treatment as WR-01's fix in both
`verify_post()` and `ship_post_notice()` (see CR-01).

### WR-03: Branch name is interpolated unescaped into a double-quoted YAML frontmatter value; git allows `"` in ref names

**File:** `.gsd/capabilities/pr-workflow/scripts/pr_status.py:203-204` (`generated_from` built from `branch`), written via `_write_report()`'s `f'generated_from: "{generated_from}"'` at line 158
**Issue:** `generated_from = f"gh pr list --head {branch} --state open --json number,url"`
embeds the live branch name verbatim, and `_write_report()` wraps it in a plain double-quoted
YAML scalar with no escaping of embedded quote characters. `git check-ref-format` does **not**
forbid `"` in branch names (it forbids space, `~^:?*[\`, control characters, and a few
structural patterns, but not double quotes). A branch such as `feature"pwn` -- plausible on a
fork-PR head branch in a CI context where this script's `execute:wave:post`/`ship:post` dispatch
could run against externally-controlled branch names -- produces a `generated_from` line whose
quoted string is terminated early, followed by trailing unquoted text on the same line, which is
invalid YAML for any parser stricter than the ad-hoc frontmatter reader this predicate relies on.
Worst observed impact given `blocking: false`/`onError: "skip"` is a silently-skipped gate
evaluation, but the underlying defect (unescaped interpolation of external-ish text into a
quoted-string frontmatter field) is still a correctness/robustness gap, and it is unaddressed by
any test in `test_pr_status.py`.
**Fix:** Escape embedded double quotes and backslashes before writing, or switch to
`json.dumps(generated_from)` (still valid inside a YAML string scalar and handles all C-string-style escaping):
```python
lines.append(f"generated_from: {json.dumps(generated_from)}")
```

## Info

### IN-01: Three of five test fixtures (`checks_pass.json`, `checks_pending.json`, `checks_skipping.json`) are unused dead files

**File:** `.gsd/capabilities/pr-workflow/tests/fixtures/checks_pass.json`, `checks_pending.json`, `checks_skipping.json`
**Issue:** `grep` confirms none of these three fixture files is referenced anywhere in
`test_pr_status.py` (only `checks_fail.json` and `pr_list_empty.json` are loaded via `_fixture()`).
14-01-SUMMARY.md's "Files Created" table describes these as "one per state," but the unit suite
only exercises 2 of the 5 committed fixtures -- the other 3 (`pass`, `pending`, `skipping`
bucket states) exist on disk with no test consuming them, and are not referenced by
`14-GATE-SMOKE-TEST.md`'s live evidence either (those runs use synthetic `PR.md` files directly,
not these fixtures).
**Fix:** Either add the missing `TestRollupPrecedence`/`TestVerifyPost` cases that actually load
`checks_pass.json`/`checks_pending.json`/`checks_skipping.json` (the rollup-precedence pure-function
tests currently construct `set` literals inline instead, e.g. `{"pass", "skipping"}` at
`test_pr_status.py`'s `test_pass_and_skipping_is_passing`, duplicating what the fixture already
encodes), or delete the three unused fixture files.

### IN-02: Raw exception text written into the committed `PR.md` artifact's `unavailable_reason` field

**File:** `.gsd/capabilities/pr-workflow/scripts/pr_status.py:236` (`unavailable_reason=f"{type(exc).__name__}: {exc}"`)
**Issue:** On the transient-`gh`-failure fail-open path, the raw exception's `str()` is written
directly into `PR.md`'s frontmatter, which is a generated-and-committed artifact (per
`14-01-SUMMARY.md`, `14-PR.md` is committed to the phase directory each run). For
`json.JSONDecodeError`, this can include a snippet of the malformed JSON payload; for `OSError`,
it can include local filesystem paths or errno text from the executing machine. None of this is
`gh` credential material (the two guard-path notices are correctly fixed strings with no captured
stderr, per D-04's stated design), but it is still local-environment detail being persisted into
a artifact that gets committed to version control on every fail-open run.
**Fix:** Low priority given the advisory-only blast radius; if tightened, truncate/sanitize the
exception text (e.g. `type(exc).__name__` only, dropping `str(exc)`) before writing it to the
committed report.

---

_Reviewed: 2026-08-18T17:13:46Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
