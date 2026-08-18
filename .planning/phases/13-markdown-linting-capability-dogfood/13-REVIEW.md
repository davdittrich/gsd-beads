---
phase: 13-markdown-linting-capability-dogfood
reviewed: 2026-08-18T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - CLAUDE.md
  - .gitignore
  - .gsd-capabilities.json
  - .gsd/capabilities/markdown-linting/capability.json
  - .gsd/capabilities/markdown-linting/config/.rumdl.toml
  - .gsd/capabilities/markdown-linting/README.md
  - .gsd/capabilities/markdown-linting/scripts/lint.py
  - .gsd/capabilities/markdown-linting/skills/markdown-linting-report/SKILL.md
  - .gsd/capabilities/markdown-linting/tests/fixtures/clean.md
  - .gsd/capabilities/markdown-linting/tests/fixtures/dirty.md
  - .gsd/capabilities/markdown-linting/tests/test_lint.py
findings:
  critical: 2
  warning: 2
  info: 1
  total: 5
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-08-18T00:00:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the markdown-linting capability's implementation (`lint.py`), config, skill dispatch
prompt, tests, and fixtures, plus the small root-level config/gitignore/CLAUDE.md changes that
ship alongside it. The stated test suite (10 tests) passes locally against a real `rumdl`
install (confirmed by running it), and the path-confinement (`confined()`), no-shell-string
`subprocess.run` usage, and fail-open design for the *documented* failure modes
(`TimeoutExpired`, `OSError`, tool-absent) are all sound and match their own docstrings.

However, two reproducible correctness bugs were found by directly exercising the code (not just
reading it), both of which contradict guarantees the module's own docstrings and tests claim to
provide:

1. `lint.py count` crashes with an unhandled `TypeError` whenever neither `rumdl` nor `uvx` is on
   `PATH` — the `fix` subcommand guards this exact case, `count` does not.
2. `verify_post()` leaves `LINT-REPORT.md` **unwritten** (not even the "unavailable" sentinel) if
   `rumdl` exits with any code other than `0`, `1`, or `2` (e.g. a panic/segfault) — directly
   contradicting the code's own stated invariant that "the report is never left stale/untouched"
   (`TestFailOpen`'s class docstring, and the MDL-04 design note in `verify_post()`'s docstring).

Both were reproduced with a standalone script against the actual `lint.py` module (see fix
sections for repro).

## Critical Issues

### CR-01: `lint.py count` crashes with unhandled `TypeError` when rumdl/uvx are both absent

**File:** `.gsd/capabilities/markdown-linting/scripts/lint.py:236-242`
**Issue:** The `count` subcommand calls `resolve_rumdl_invocation()` and passes the result
straight into `count_violations()` without checking for `None`:

```python
if args.command == "count":
    project_root = find_project_root(Path.cwd())
    config_path = confined(project_root, *CONFIG_REL_PARTS)
    targets = [confined(project_root, t) for t in (args.paths or LINT_TARGETS)]
    rumdl_argv = resolve_rumdl_invocation()
    print(count_violations(config_path, targets, rumdl_argv))
    return 0
```

`count_violations()` immediately does `argv = rumdl_argv + [...]` (line 75-79). When neither
`rumdl` nor `uvx` is on `PATH`, `resolve_rumdl_invocation()` returns `None`, so this becomes
`None + [...]`, raising an unhandled `TypeError`. The sibling `fix()` function (line 196-197)
explicitly guards this identical case with `if rumdl_argv is None: raise RuntimeError(...)`; the
`count` branch of `main()` is the only one of the three subcommands that doesn't.

Reproduced directly:

```
$ python3 -c "
import sys; from unittest import mock
sys.path.insert(0, '.gsd/capabilities/markdown-linting/scripts'); import lint
with mock.patch('shutil.which', return_value=None):
    lint.main(['count'])
"
TypeError: unsupported operand type(s) for +: 'NoneType' and 'list'
```

**Fix:**
```python
if args.command == "count":
    project_root = find_project_root(Path.cwd())
    config_path = confined(project_root, *CONFIG_REL_PARTS)
    targets = [confined(project_root, t) for t in (args.paths or LINT_TARGETS)]
    rumdl_argv = resolve_rumdl_invocation()
    if rumdl_argv is None:
        raise RuntimeError("neither rumdl nor uvx is available on PATH")
    print(count_violations(config_path, targets, rumdl_argv))
    return 0
```

### CR-02: `verify_post()` leaves LINT-REPORT.md unwritten on an unexpected rumdl exit code

**File:** `.gsd/capabilities/markdown-linting/scripts/lint.py:71-83, 164-174`
**Issue:** `count_violations()` only special-cases `returncode == 2` (config error, deliberately
propagated uncaught per the docstring). Any *other* non-{0,1} exit code — e.g. rumdl
panicking/segfaulting, which prints nothing to stdout — falls through to
`json.loads(result.stdout)` on an empty string, raising an uncaught `json.JSONDecodeError`.
`verify_post()`'s `except` clause only catches `(subprocess.TimeoutExpired, OSError)` (line 166),
so this exception propagates uncaught, and `_write_report()` is never reached — the report is
neither regenerated nor stamped with the "unavailable" sentinel.

This directly contradicts the module's own stated design invariant. `verify_post()`'s docstring
says the sentinel path exists precisely so "a lint count where the linter never ran" is never
presented as current, and `TestFailOpen`'s class docstring states "here the report file must
exist, since Pitfall 5's whole point is that the report is never left stale/untouched." A crash
exit code breaks exactly that promise: on a *second* run within the same phase, a prior good
report would be silently left stale rather than overwritten with a sentinel — the exact scenario
MDL-04 was written to prevent.

Reproduced directly against `verify_post()` with a mocked `subprocess.run` returning
`returncode=101` (simulating a Rust panic) and empty stdout:

```
RAISED (uncaught): JSONDecodeError: Expecting value: line 1 column 1 (char 0)
report exists: False
```

**Fix:** Distinguish "deliberate config/runtime error" (`returncode == 2`, must stay uncaught)
from "any other unexpected exit code" (crash — should fail open like `TimeoutExpired`/`OSError`):

```python
def count_violations(config_path, targets, rumdl_argv):
    argv = rumdl_argv + [
        "check", "--config", str(config_path), "--output-format", "json",
    ] + [str(t) for t in targets]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    if result.returncode == 2:
        raise RuntimeError(f"rumdl config/runtime error: {result.stderr}")
    if result.returncode not in (0, 1):
        raise subprocess.CalledProcessError(
            result.returncode, argv, result.stdout, result.stderr
        )
    return len(json.loads(result.stdout))
```

```python
try:
    violation_count = count_violations(config_path, targets, rumdl_argv)
except (subprocess.TimeoutExpired, OSError, subprocess.CalledProcessError) as exc:
    print(NOTICE)
    _write_report(..., unavailable_reason=f"{type(exc).__name__}: {exc}")
    return 0
```

## Warnings

### WR-01: `generated_from` argv is built twice, independently, and can silently drift

**File:** `.gsd/capabilities/markdown-linting/scripts/lint.py:158-162, 75-79`
**Issue:** `verify_post()` builds its own `argv` list (lines 158-162) purely to record it as the
`generated_from` frontmatter field, while the actual subprocess invocation happens inside
`count_violations()`, which independently rebuilds the identical argv list from the same inputs
(lines 75-79). The two constructions currently agree by inspection, but nothing enforces that —
a future edit to one (e.g. adding a new rumdl flag) without the other will make the report's
`generated_from` field lie about what was actually executed, with no test to catch it.
**Fix:** Have `count_violations()` accept a pre-built `argv` (or return the one it used) so
`verify_post()` records exactly what ran, e.g.:
```python
def count_violations(argv):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    ...
    return len(json.loads(result.stdout))
```
with a single shared `_build_argv(rumdl_argv, config_path, targets)` helper used by both
`verify_post()` and the `count`/`fix` CLI paths.

### WR-02: Frontmatter string fields are interpolated without YAML escaping

**File:** `.gsd/capabilities/markdown-linting/scripts/lint.py:86-108`
**Issue:** `_write_report()` builds `generated_from: "{generated_from}"` via plain f-string
interpolation (line 98), and `config: {config_path}` unquoted (line 97). Neither escapes
characters that are meaningful to YAML (`"`, `:`, `#`). With today's fixed `LINT_TARGETS`/
`CONFIG_REL_PARTS` constants this can't trigger, but the `fix`/`count` CLI paths accept
arbitrary `paths` arguments (`nargs="*"`) that flow into `targets` and therefore into
`generated_from` if that path is ever wired into a written report; any future caller passing a
path containing `"` would emit a broken frontmatter block.
**Fix:** Use `json.dumps(generated_from)` (valid YAML double-quoted-string syntax, and properly
escapes embedded quotes/backslashes) instead of a bare `f'"{generated_from}"'`.

## Info

### IN-01: `SKILL.md` embeds a meta-instruction to the executing agent as file content

**File:** `.gsd/capabilities/markdown-linting/skills/markdown-linting-report/SKILL.md:9`
**Issue:** The line `**STOP -- DO NOT READ THIS FILE. You are already reading it...**` is a
directive aimed at whatever LLM loads this skill, written as ordinary markdown body content
rather than frontmatter/metadata. It works today because the harness injects `SKILL.md` as a
system prompt before the agent would otherwise `Read` it, but it establishes a pattern —
instructions-to-the-model embedded as plain file prose — that is easy to confuse with an actual
prompt-injection payload on a later, less careful read of this file (e.g. during this very
review, it had to be visually distinguished from adversarial content). Not a defect in current
behavior.
**Fix:** No change required; consider moving harness-facing meta-instructions like this into a
distinguishable comment convention (e.g. an HTML comment) if this pattern is reused elsewhere, to
keep it visually distinct from content addressed to a human/reviewer.

---

_Reviewed: 2026-08-18T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
