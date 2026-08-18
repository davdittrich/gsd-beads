---
phase: 13-markdown-linting-capability-dogfood
verified: 2026-08-18T12:57:01Z
status: gaps_found
score: 5/7 must-haves verified
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "verify_post() never leaves LINT-REPORT.md stale/unwritten on any rumdl subprocess failure (plan 02's own must_haves.prohibitions statement and the TestFailOpen class's documented invariant: 'the report is never left stale/untouched')"
    status: failed
    reason: >
      count_violations() (lint.py:71-83) only special-cases returncode == 2 (deliberate config
      error, correctly kept uncaught). Any OTHER unexpected exit code -- e.g. rumdl
      panicking/segfaulting, which prints nothing to stdout -- falls through to
      json.loads(result.stdout) on an empty string, raising an uncaught json.JSONDecodeError.
      verify_post()'s except clause (lint.py:166) only catches (subprocess.TimeoutExpired,
      OSError), so this propagates uncaught and _write_report() is never reached. A pre-existing
      good report is left completely untouched and would be silently presented as current on the
      next ship -- exactly the "stale count presented as clean" failure MDL-04 and the phase's own
      prohibitions clause exist to prevent. Live-reproduced during this verification (2026-08-18):
      a mocked subprocess.run(returncode=101, stdout="") against a phase dir carrying a
      pre-existing "violation_count: 0" report raised an uncaught JSONDecodeError, and the report
      file's content was byte-identical (still stale) afterward. This exact bug was already found
      and documented as CR-02 in 13-REVIEW.md (committed 135e8be); no commit has touched
      scripts/lint.py since (last touching commit: 7b94129, plan 02), so it remains unresolved.
    artifacts:
      - path: .gsd/capabilities/markdown-linting/scripts/lint.py
        issue: "count_violations()/verify_post() (lines 71-83, 111-182) do not fail-open on an unexpected (non-0/1/2) rumdl exit code; the resulting uncaught exception leaves LINT-REPORT.md stale instead of overwriting it with the documented 'unavailable' sentinel."
    missing:
      - "Distinguish returncode == 2 (deliberate config error, must stay uncaught) from any other non-{0,1} exit code (crash) and route the latter through the same NOTICE + sentinel-report fail-open branch already used for TimeoutExpired/OSError -- the fix 13-REVIEW.md's CR-02 already specifies verbatim."
      - "A regression test exercising an unexpected/crash exit code (e.g. returncode=101, empty stdout) that asserts the report is still overwritten with the sentinel rather than left untouched -- TestFailOpen has no such test today."
  - truth: "lint.py's documented `count` CLI subcommand degrades safely rather than raising an unhandled exception when rumdl and uvx are both absent from PATH"
    status: failed
    reason: >
      main()'s `count` branch (lint.py:236-242) passes resolve_rumdl_invocation()'s return value
      straight into count_violations() with no None check. When both rumdl and uvx are absent,
      this becomes `None + [...]` inside count_violations(), raising an unhandled TypeError. The
      sibling fix() function (lint.py:195-197) explicitly guards this identical case with a clear
      RuntimeError; `count` is the only one of the three subcommands that doesn't. Live-reproduced
      during this verification (2026-08-18): `python3 lint.py count` with shutil.which patched to
      return None for both tools raised `TypeError: unsupported operand type(s) for +: 'NoneType'
      and 'list'`. This exact bug was already found and documented as CR-01 in 13-REVIEW.md
      (committed 135e8be); no fix commit exists since.
    artifacts:
      - path: .gsd/capabilities/markdown-linting/scripts/lint.py
        issue: "main()'s 'count' branch (lines 236-242) has no None-guard on resolve_rumdl_invocation()'s result, unlike fix() (lines 195-197)."
    missing:
      - "Same None-guard fix() already has (raise RuntimeError('neither rumdl nor uvx is available on PATH')) applied to the 'count' branch of main() -- the fix 13-REVIEW.md's CR-01 already specifies verbatim."
      - "A regression test for `count` with both tools absent."
---

# Phase 13: markdown-linting capability (dogfood) Verification Report

**Phase Goal:** This repo's own lifecycle measures and reports `.planning/` markdown quality, and
the first live proof exists that a generic `ship:pre` gate fires for a capId other than `security`
/ `broken-windows`.
**Verified:** 2026-08-18T12:57:01Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | MDL-01: curated rumdl config with always-explicit `--config` reports 0 violations against `.planning/`+`README.md`+`CLAUDE.md`; README names all 7 enabled + 3 disabled rules with reasons and a freshly measured, date+sha-stamped markdownlint-cli2 divergence disclosure | ✓ VERIFIED | Live-run `lint.py count` (combined + 3 independent scopes) all print `0`. `.gsd/capabilities/markdown-linting/README.md` (113 lines) names MD001/003/009/012/022/024/040 enabled and MD013/033/041 disabled with reasons; divergence table stamped `2026-08-18, commit 866d071` (matches `git log` for that file); no `45%`/`14 vs 1` stale figures present. |
| 2 | MDL-02: after a real `verify:post` run, `LINT-REPORT.md` exists with `violation_count` matching a hand-run `rumdl` count, and carries the "regenerated every step, never hand-edited" banner | ✓ VERIFIED | Committed `13-LINT-REPORT.md` frontmatter: `violation_count: 0`, `config`, `generated_from`, `generated_at`; body contains `> Regenerated every step. Do not hand-edit.`; `test_report_matches_handrun_count` passes live. |
| 3 | MDL-03 (SC3): installed `ship.md` confirmed to contain the generic gate-dispatch marker before trust; live `gsd_run check predicate` smoke test against a synthetic report shows the gate satisfied at `violation_count:0` and unsatisfied at `violation_count:7` | ✓ VERIFIED | `grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' ship.md` → 2 (re-confirmed live this session). `13-GATE-SMOKE-TEST.md` Step 2 records both raw evaluator JSON outputs (`block:false`/`match:true` at 0; `block:true`/`match:false`/`actual:"7"` at 7) using the predicate extracted verbatim via `jq` from `capability.json`. |
| 4 | MDL-03 (SC4): the gate is advisory — a phase with a nonzero `LINT-REPORT.md` count still ships, with a visible warning naming the count | ✓ VERIFIED | `13-GATE-SMOKE-TEST.md` Step 3: real report temporarily set to `violation_count:12`, evaluator returns `block:true`; gate's `blocking:false` means `ship.md` step 8(c) never halts, only prints the advisory line `⚠ markdown-linting advisory: ...is 12, expected 0`. Real report restored to `0` afterward (confirmed by current file content). Note: this is a reconstructed application of ship.md's literal template against live evaluator output, not a captured transcript of an actual `/gsd-ship` run — reasonable given running a real ship would push a branch, but slightly weaker than a fully live capture. |
| 5 | MDL-04 (SC5): with `rumdl` removed from PATH, one visible notice, exit 0, no hang, and no stale `LINT-REPORT.md` presented as current | ✓ VERIFIED | `13-GATE-SMOKE-TEST.md` Step 4: PATH-scoped run with only `python3` on PATH → `NOTICE` printed once, exit 0, report rewritten with `violation_count: unavailable`; gate reads it as `block:true` (not a clean pass). `test_tool_absent_fail_open` / `test_tool_absent_overwrites_stale_zero_report_sentinel` pass live (10/10 suite green, confirmed this session). |
| 6 | The capability's own documented no-stale-report guarantee (plan 02 `must_haves.prohibitions`; `TestFailOpen`'s class docstring: "the report is never left stale/untouched") holds for **any** rumdl subprocess failure, not just the tool-absent/timeout/OSError cases the tests cover | ✗ FAILED | Reproduced live: an unexpected rumdl exit code (e.g. a crash returning 101 with empty stdout) raises an uncaught `json.JSONDecodeError` inside `count_violations()`, which `verify_post()`'s `except (TimeoutExpired, OSError)` clause does not catch. `_write_report()` is never reached; a pre-existing report is left byte-identical (stale) rather than overwritten with the sentinel. Matches 13-REVIEW.md's CR-02, still unresolved (see Gaps). |
| 7 | `lint.py`'s documented `count` CLI subcommand degrades safely (no unhandled exception) when both `rumdl` and `uvx` are absent from PATH, matching the guard its sibling `fix` subcommand already has | ✗ FAILED | Reproduced live: `lint.py count` with both tools mocked absent raises an unhandled `TypeError` (`None + [...]`) instead of the clean `RuntimeError` `fix()` raises for the identical case. Matches 13-REVIEW.md's CR-01, still unresolved (see Gaps). |

**Score:** 5/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gsd/capabilities/markdown-linting/capability.json` | id/config/steps/gates manifest | ✓ VERIFIED | Exists; `id:"markdown-linting"`, one `verify:post` step producing `LINT-REPORT.md`, one advisory (`blocking:false`) `ship:pre` gate with `artifact-frontmatter-equals` predicate; no `contributions[]` entries with `produces`. |
| `.gsd/capabilities/markdown-linting/config/.rumdl.toml` | curated 7-rule allowlist, no `disable` key | ✓ VERIFIED | `[global] enable = ["MD001","MD003","MD009","MD012","MD022","MD024","MD040"]`; no `disable` key. |
| `.gsd/capabilities/markdown-linting/scripts/lint.py` | stdlib-only wrapper: `resolve_rumdl_invocation`, `count_violations`, `verify_post`, `fix`, CLI subcommands | ⚠ STUB-LIKE (2 unresolved crash bugs) | Exists, 249 lines, substantive and wired into the skill and the `fix`/`verify-post` paths; however `count_violations`/`verify_post` and `main()`'s `count` branch each have an unguarded failure mode (CR-02, CR-01) that produces an unhandled exception instead of the documented fail-open behavior. Not a stub, but a correctness defect in a claimed invariant. |
| `.gsd/capabilities/markdown-linting/skills/markdown-linting-report/SKILL.md` | config gate + single `verify:post` dispatch | ✓ VERIFIED | Frontmatter `name: gsd-markdown-linting-report`, `allowed-tools: [Read, Bash]`; Step 1 config gate reads `.planning/config.json`; Step 2 dispatches `lint.py verify-post <phase_dir>`; anti-patterns section correctly forbids the project-root report path and extra `count`/`fix` calls. |
| `.gsd/capabilities/markdown-linting/tests/test_lint.py` + fixtures | stdlib unittest suite, MDL-01/02/04 coverage | ✓ VERIFIED | 10 tests, `python3 -m unittest discover` → `Ran 10 tests ... OK` (re-run live this session). `clean.md`/`dirty.md` fixtures present and match the counts asserted (0 / 5). Suite does not cover the CR-01/CR-02 failure modes (a real gap in the suite's own completeness, separate from the code gap). |
| `.gsd/capabilities/markdown-linting/README.md` | ruleset, install tiers, artifact-path rationale, dated divergence disclosure | ✓ VERIFIED | 113 lines; documents both config keys (with the MDL-05 note), all 3 D-04 install tiers, the phase-scoped-artifact rationale, and a `2026-08-18, commit 866d071`-stamped rumdl-vs-markdownlint-cli2 table (0 vs 309, all MD022/MD024). |
| `{phase_dir}/13-LINT-REPORT.md` | generated artifact | ✓ VERIFIED | Committed, `violation_count: 0`, correct frontmatter shape and banner; regenerated live during this verification with an unchanged result. |
| `13-GATE-SMOKE-TEST.md` | recorded gate-proof transcript (SC3/SC4/SC5) | ✓ VERIFIED | Contains Steps 1-4 covering marker confirmation, the two-case predicate test, the advisory-ship demonstration, and the rumdl-absent cycle, all with concrete evaluator JSON. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `capability.json` `steps[]` `verify:post` | `markdown-linting-report` skill → `lint.py verify-post` → `{phase_dir}/13-LINT-REPORT.md` | Live run this session | ✓ WIRED | `lint.py verify-post .planning/phases/13-markdown-linting-capability-dogfood` exits 0, rewrites the report with `violation_count: 0`. |
| `capability.json` `gates[]` `ship:pre` | `artifact-frontmatter-equals` → `LINT-REPORT.md`/`violation_count` | `gsd_run check predicate` transcripts | ✓ WIRED | `13-GATE-SMOKE-TEST.md` Steps 2-4 show the evaluator correctly reading `0`, `7`, `12`, and `unavailable` against the shipped predicate, all matching expected `block`/`match` values. |
| `$HOME/.claude/gsd-core/workflows/ship.md` step 8 | generic non-security/broken-windows gate dispatch | Direct grep + read | ✓ WIRED | Marker present (2 occurrences, open/close); step 8's logic explicitly branches on `hook.blocking`/`GATE_RESULT.block` exactly as `13-GATE-SMOKE-TEST.md` Step 3 applies it. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `13-LINT-REPORT.md` | `violation_count` | `len(json.loads(subprocess.run(rumdl ... --output-format json).stdout))` | Yes — live rumdl run over the real `.planning/`+`README.md`+`CLAUDE.md` tree | ✓ FLOWING |
| ship:pre gate decision | `GATE_RESULT.block` | generic evaluator reading `LINT-REPORT.md` frontmatter via `artifact-frontmatter-equals` | Yes — confirmed against 4 distinct live report states (0/7/12/unavailable) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full lint scope reports 0 violations | `lint.py count` (combined + 3 scopes) | `0` x4 | ✓ PASS |
| Regression suite green | `python3 -m unittest discover -s .gsd/capabilities/markdown-linting/tests -v` | `Ran 10 tests ... OK` | ✓ PASS |
| ship.md generic dispatch marker present | `grep -c '...v1' ship.md` | `2` | ✓ PASS |
| `count` with rumdl/uvx absent degrades safely | mocked `shutil.which` → `None`, `lint.main(['count'])` | `TypeError: unsupported operand type(s) for +: 'NoneType' and 'list'` (unhandled) | ✗ FAIL (CR-01) |
| `verify_post()` never leaves a stale report on rumdl crash | mocked `subprocess.run(returncode=101, stdout="")` against a phase dir with a pre-existing `violation_count: 0` report | `JSONDecodeError` raised uncaught; report content unchanged (stale) | ✗ FAIL (CR-02) |

### Probe Execution

Not applicable — this phase has no `scripts/*/tests/probe-*.sh` convention; its own `tests/test_lint.py` suite serves the equivalent role and was run above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| MDL-01 | 13-01, 13-03 | Curated MD0XX ruleset, always-explicit `--config`, 0 violations on real tree, README divergence disclosure | ✓ SATISFIED | Truth #1, artifacts table (`.rumdl.toml`, README). |
| MDL-02 | 13-01, 13-02 | `verify:post` fragment reports violation count, `onError: skip` | ✓ SATISFIED | Truth #2; happy-path count/report match proven live and by test. |
| MDL-03 | 13-01, 13-03 | `ship:pre` gate reads violation count, advisory by default | ✓ SATISFIED | Truths #3, #4; `13-GATE-SMOKE-TEST.md`. |
| MDL-04 | 13-02, 13-03 | rumdl absent degrades to no-op with one notice; report never stale | ⚠ PARTIALLY SATISFIED | The literal SC5 scenario ("rumdl removed from PATH") is proven (Truth #5). The requirement's own broader "never stale" design guarantee — asserted by the module's own docstrings/tests and the plan's `must_haves.prohibitions` — is violated for an unhandled rumdl-crash exit code (Truth #6, gap). `REQUIREMENTS.md` marks this "Complete"; this verification disputes that for the reason above. |

No orphaned requirements: `grep "Phase 13" REQUIREMENTS.md` returns exactly MDL-01..04, all of which are claimed by at least one of the three plans' `requirements` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `.gsd/capabilities/markdown-linting/scripts/lint.py` | 236-242 | `main()`'s `count` branch has no `None`-guard on `resolve_rumdl_invocation()`, unlike `fix()` | 🛑 Blocker | Unhandled `TypeError` on tool-absent `count` invocation (CR-01, reproduced) |
| `.gsd/capabilities/markdown-linting/scripts/lint.py` | 71-83, 164-174 | `count_violations()`/`verify_post()` only special-case `returncode==2`; any other unexpected exit code raises uncaught `JSONDecodeError`, skipping `_write_report()` | 🛑 Blocker | `LINT-REPORT.md` left stale/unwritten on a rumdl crash, contradicting MDL-04's and the module's own documented "never stale" invariant (CR-02, reproduced) |
| `.gsd/capabilities/markdown-linting/scripts/lint.py` | 158-162, 75-79 | `generated_from` argv built independently in two places (`verify_post()` and `count_violations()`); nothing enforces they stay identical | ⚠ Warning | Provenance field (`generated_from`) could silently drift from the argv actually executed on a future edit (WR-01, from 13-REVIEW.md, unresolved but non-blocking today) |
| `.gsd/capabilities/markdown-linting/scripts/lint.py` | 86-108 | Frontmatter string fields (`generated_from`, `config`) are f-string interpolated without YAML escaping | ⚠ Warning | Only reachable via arbitrary `paths` CLI args today; no live exploit path found, but no escaping exists if that path is ever wired into a written report (WR-02, from 13-REVIEW.md, unresolved but non-blocking today) |
| `.gsd/capabilities/markdown-linting/skills/markdown-linting-report/SKILL.md` | 9 | Meta-instruction to the executing agent embedded as plain markdown body content | ℹ Info | Cosmetic/pattern-hygiene note only (IN-01, from 13-REVIEW.md); no functional defect |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` debt markers found in `.gsd/capabilities/markdown-linting/` (grep run this session, zero matches).

### Human Verification Required

None. Both gaps below are machine-reproduced defects, not judgment calls.

### Gaps Summary

Two of the three plans' work is solid and the phase's headline claim — "the generic `ship:pre` gate
fires for a non-`security`/`broken-windows` capId, live" — is genuinely proven (Truths #1-5, all
artifacts and key links wired and confirmed by direct evaluator/subprocess execution). The 0-violation
cleanup, the README, and the fail-open behavior for the two rumdl-absence paths the plans explicitly
tested (`PATH`-absent, `TimeoutExpired`, `OSError`) all hold up under direct re-execution.

However, `13-REVIEW.md` (committed after all three plans, `135e8be`) found two reproducible,
still-unresolved critical bugs in `scripts/lint.py`, and no commit has touched that file since
(`git log` shows the last change to it is plan 02's `7b94129`, predating the review). This
verification independently re-reproduced both:

1. **CR-02** — `verify_post()` leaves `LINT-REPORT.md` completely stale (not even the "unavailable"
   sentinel) when rumdl exits with any code the code doesn't explicitly enumerate (0, 1, 2). This is
   a direct violation of MDL-04's and the plan's own stated design invariant that a lint count where
   the linter never ran must never be presented as current — the exact failure mode the whole
   fail-open design exists to prevent, and the module's own `TestFailOpen` class docstring claims is
   impossible.
2. **CR-01** — the `count` CLI subcommand crashes with an unhandled `TypeError` under the identical
   tool-absent condition its sibling `fix()` already guards against cleanly.

Both fixes are already fully specified (with working code) in `13-REVIEW.md`'s Critical Issues
section and were not applied. Given these are live, reproducible defects in shipped code — not
theoretical edge cases — and they directly touch the phase's central "the gate's number is honest"
promise, this phase does not pass verification as-is. The fix for both is small (the review's own
patches are ~10-15 lines total) and does not require replanning; it is a closure task against this
phase's own already-diagnosed findings.
