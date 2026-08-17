---
phase: 11-sota-numerics-capability-plugin-sota-efficiency-numerical-st
plan: 01
subsystem: infra
tags: [claude-code-plugin, capability-loader, command-exit-zero, gate, python, bash, stdlib]

# Dependency graph
requires:
  - phase: 10.1-capability-auto-install
    provides: vendored capability-auto-install.sh / gsd-tools.sh pattern (Phase 10.1 D-05), reused byte-identically as the third instance
provides:
  - "sota-numerics capability plugin: a working plan:post command-exit-zero blocking gate, its check-alternatives.py validator, a dogfood install, and full plugin packaging"
affects: [11-02-fragments-contributions, 11-03-checker-spotcheck-decision]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 14822
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "command-exit-zero blocking gate at plan:post — first blocking gate this repo declares outside ship:pre"
    - "Gate command guards its own missing-script case with a shell `test -f` before invoking the interpreter, printing an actionable `capability install` remediation instead of a bare interpreter error"
    - "Vendored capability-auto-install.sh / gsd-tools.sh copies (Phase 10.1 D-05 pattern) — third byte-identical instance alongside beads-lifecycle and ponytail-everywhere"

key-files:
  created:
    - sota-numerics/.gsd/capabilities/sota-numerics/capability.json
    - sota-numerics/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py
    - sota-numerics/tests/test_check_alternatives.py
    - sota-numerics/tests/fixtures/ (7 fixtures: compliant, missing-section, uncited, exempt, foundational, multiplan/, dotted/)
    - sota-numerics/.claude-plugin/plugin.json
    - sota-numerics/hooks/hooks.json
    - sota-numerics/hooks/session-start.sh
    - sota-numerics/hooks/capability-auto-install.sh
    - sota-numerics/hooks/gsd-tools.sh
    - sota-numerics/tests/test-session-start.sh
    - .gsd/capabilities/sota-numerics/capability.json (dogfood copy)
    - .gsd/capabilities/sota-numerics/scripts/check-alternatives.py (dogfood copy)
  modified:
    - .claude-plugin/marketplace.json

key-decisions:
  - "onError: \"halt\" on the plan:post gate — deliberate divergence from every other gate in this repo (beads' two ship:pre gates both use \"skip\"). This governs only the check COMMAND itself failing to run (missing python3, crash, timeout); the block decision is derived separately, from the exit code, by gsd-core's generic command-exit-zero evaluator. A blocking gate that silently skips on its own command failure would defeat its purpose (CONTEXT.md Established Patterns). Documented in the manifest's gate `description` field so a future edit does not \"fix\" it back to skip."
  - "Gate script path resolved via $(git rev-parse --show-toplevel), not ${CLAUDE_PLUGIN_ROOT} — the gate subprocess's environment is unverified (RESEARCH Open Question 1) while its cwd is the project root, and the dogfood install (D-04) has a fixed relative path from repo root."
  - "validate_plan reports only the FIRST offending alternative entry per plan (with that entry's citation + date + placeholder issues combined into one message), not every entry across the plan — fail-fast per plan, consistent with the gate being a structural backstop (RESEARCH Pitfall 1: the checker's revision loop is the primary enforcement point, this gate is the last-resort catch)."

patterns-established:
  - "Pattern: a command-exit-zero gate script performs zero subprocess/eval calls of its own and treats all PLAN.md body text as untrusted input — mirrors sync.py's T-01-01 discipline for a script whose input crosses a different-principal trust boundary."
  - "Pattern: the missing-script guard is built as a `;`-joined shell command string (assign path to a variable, `test -f` guard, then invoke) rather than relying on the interpreter's own file-not-found error, so gate failures are always actionable."

requirements-completed: [D-01, D-02, D-03, D-04, D-06, D-07, D-09, D-10, D-11]

coverage:
  - id: D1
    description: "plan:post command-exit-zero gate mechanically blocks a phase directory containing a non-compliant plan and passes a compliant one, evaluated through gsd-core's real generic predicate evaluator (not a hand simulation)"
    requirement: D-01
    verification:
      - kind: other
        ref: "gsd_run check predicate --predicate <gate's declared predicate> --phase-dir sota-numerics/tests/fixtures/multiplan --raw -> block:true; --phase-dir sota-numerics/tests/fixtures/dotted --raw -> block:false"
        status: pass
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestMultiPlanCoverage.test_multiplan_dir_exits_1_even_though_first_plan_compliant"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every *-PLAN.md in a phase directory is validated, not just the first readdir match; dotted phase segments (10.1-02-PLAN.md) are matched"
    requirement: D-02
    verification:
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestMultiPlanCoverage.test_multiplan_dir_exits_1_even_though_first_plan_compliant"
        status: pass
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestDottedFilenames.test_dotted_phase_segment_matched"
        status: pass
    human_judgment: false
  - id: D3
    description: "D-03 exemption text (\"N/A — no mechanism choice\") passes with no further checks"
    requirement: D-03
    verification:
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestExemption.test_exempt_plan_exits_0"
        status: pass
    human_judgment: false
  - id: D4
    description: "Citation (URL/doc-ref) and at-least-one-in-window recency-year requirements, including the REVIEWS finding 2 foundational-citation pairing rule (a canonical out-of-window year paired with an in-window current source passes; canonical years alone fail)"
    requirement: D-06
    verification:
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestCitationAndDate.test_uncited_undated_exits_1_names_both_issues"
        status: pass
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestFoundationalCitationPairing.test_generated_pairing_with_live_year_exits_0"
        status: pass
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestFoundationalCitationPairing.test_canonical_years_only_exits_1"
        status: pass
    human_judgment: false
  - id: D5
    description: "Decided by: line naming a ranked criterion is required; D-08 mechanical plausibility rejects example.com-class placeholder URLs and bare TODO/TBD citations"
    requirement: D-09
    verification:
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestDecidedBy.test_missing_decided_by_exits_1"
        status: pass
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestCitationAndDate.test_example_com_placeholder_url_exits_1"
        status: pass
    human_judgment: false
  - id: D6
    description: "Every exit-1 run prints a --force remediation line naming the phase number (or the <phase> placeholder fallback) exactly once; the gate command guards a missing script with an actionable capability-install message instead of a bare interpreter error"
    verification:
      - kind: unit
        ref: "sota-numerics/tests/test_check_alternatives.py#TestRemediationOutput (3 tests: phase-number-named, placeholder-fallback, exactly-once)"
        status: pass
      - kind: other
        ref: "gate command run via bash with check-alternatives.py temporarily renamed -> prints 'gate script not found ... capability install ...' on stderr, exits non-zero"
        status: pass
    human_judgment: false
  - id: D7
    description: "sota-numerics.enabled is the sole config key, defaults true, and the session-start banner prints by default with no config present (D-10, D-11); the dogfood copy at .gsd/capabilities/sota-numerics/ is byte-identical to the plugin bundle (D-04)"
    requirement: D-04
    verification:
      - kind: other
        ref: "bash sota-numerics/tests/test-session-start.sh (7 PASS cases: no-config default-true, enabled=false silent, per-role framing x3, bogus-role/injection fallback)"
        status: pass
      - kind: other
        ref: "diff sota-numerics/.gsd/capabilities/sota-numerics/{capability.json,scripts/check-alternatives.py} .gsd/capabilities/sota-numerics/{...} -> no differences"
        status: pass
    human_judgment: false
  - id: D8
    description: "sota-numerics is discoverable as a third plugin entry in .claude-plugin/marketplace.json with the two pre-existing entries unmodified"
    verification:
      - kind: other
        ref: "jq -e '[.plugins[].name] == [\"beads-lifecycle\",\"ponytail-everywhere\",\"sota-numerics\"]' .claude-plugin/marketplace.json; git diff .claude-plugin/marketplace.json shows additions only"
        status: pass
    human_judgment: false

duration: 35min
completed: 2026-08-17
status: complete
---

# Phase 11 Plan 01: sota-numerics Gate Spine Summary

**Built and proved the `sota-numerics` capability's `command-exit-zero` `plan:post` blocking gate — a stdlib-only Python validator, its JSON manifest, a dogfood install, and full Claude Code plugin packaging — verified end-to-end through gsd-core's real generic predicate evaluator, not a simulation.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-08-17T10:31:37Z
- **Completed:** 2026-08-17T11:06:42Z
- **Tasks:** 3
- **Files modified:** 20 (19 created, 1 modified)

## Accomplishments

- `check-alternatives.py`: a stdlib-only, no-subprocess Python validator that globs every `*-PLAN.md` in a phase directory (dotted phase segments included), enforces >=2 named alternatives each with a URL/doc-ref citation and an at-least-one-in-window recency year (REVIEWS finding 2's foundational-citation-pairing rule), a `Decided by:` line naming a ranked criterion, the D-03 exemption text, and D-08's placeholder-host/TODO-TBD mechanical rejection — exits 0/1/2 for `evaluateCommandExitZero` to read directly, with no hand-rolled JSON result.
- `capability.json` declares the capability's sole gate: `plan:post`, `command-exit-zero`, `blocking: true`, `onError: "halt"` (a documented, deliberate divergence from every other gate in this repo). The gate command guards against a missing script with a `test -f` check and an actionable `capability install` remediation message, and the script itself prints a `--force` remediation line exactly once on every exit-1 run.
- Verified live through `gsd_run check predicate` (the real evaluator, invoked exactly as the workflow would): `block: true` against a fixture directory with one non-compliant plan, `block: false` against a fully compliant one — proving the mechanism works before any advisory content (Plan 02) is written on top of it.
- 19 stdlib `unittest` cases covering every locked decision (D-01/D-02/D-03/D-06/D-07/D-08/D-09), the multi-plan-per-phase coverage requirement, dotted filenames, path safety, and the REVIEWS findings 1-3 remediation/pairing/missing-script fixes.
- Full plugin packaging: `plugin.json`, `hooks.json`, a vendored `session-start.sh` with D-11's single config key (no intensity knob), byte-identical vendored `capability-auto-install.sh`/`gsd-tools.sh` copies, a 7-case smoke test, and a third `marketplace.json` entry alongside `beads-lifecycle` and `ponytail-everywhere`.

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "the plan:post gate blocks a non-compliant plan" — one path only** (tracer) - `246dfbc` (feat)
2. **Task 2: Unit-test the validator against every locked decision** - `aedac09` (test)
3. **Task 3: Package the plugin — manifest, hooks, vendored auto-install, marketplace entry** - `850d38d` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `sota-numerics/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` - the gate validator
- `sota-numerics/.gsd/capabilities/sota-numerics/capability.json` - the gate manifest
- `sota-numerics/tests/test_check_alternatives.py` - 19 unittest cases
- `sota-numerics/tests/fixtures/*` - compliant, missing-section, uncited, exempt, foundational fixtures plus `multiplan/` and `dotted/` directories
- `sota-numerics/.claude-plugin/plugin.json` - plugin manifest (no `skills` key)
- `sota-numerics/hooks/hooks.json` - SessionStart + 3 SubagentStart matchers
- `sota-numerics/hooks/session-start.sh` - config-gated advisory banner
- `sota-numerics/hooks/capability-auto-install.sh`, `sota-numerics/hooks/gsd-tools.sh` - byte-identical vendored copies
- `sota-numerics/tests/test-session-start.sh` - 7-case smoke test
- `.gsd/capabilities/sota-numerics/capability.json`, `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` - dogfood copies (D-04), byte-identical to the bundle copies
- `.claude-plugin/marketplace.json` - third `plugins[]` entry appended

## Decisions Made

- `onError: "halt"` on the `plan:post` gate, diverging from every other gate in this repo (both `beads` `ship:pre` gates use `"skip"`) — a blocking gate that silently skips on its own command crash defeats its purpose. Documented in the gate's own `description` field in `capability.json`.
- Gate script path resolved via `$(git rev-parse --show-toplevel)`, not `${CLAUDE_PLUGIN_ROOT}` — the gate subprocess's environment is unverified while its `cwd` is the project root (RESEARCH Open Question 1); the dogfood install (D-04) gives a fixed relative path from repo root regardless.
- `validate_plan` reports the first offending alternative entry per plan (combining that entry's citation/date/placeholder issues into one message) rather than aggregating across every entry — a fail-fast design consistent with the gate being a structural backstop, not an exhaustive linter (RESEARCH Pitfall 1: the checker's revision loop, run before commit, is the primary enforcement point).

## Deviations from Plan

None — plan executed as written. Two implementation-detail fixes surfaced during self-verification, both within Rule 1 (auto-fix bugs) scope and resolved before any task commit:

**1. [Rule 1 - Bug] Docstring literally contained the substring "subprocess", tripping the script's own ASVS V5 acceptance grep**
- **Found during:** Task 1, running `grep -rn 'subprocess\|os.system\|eval(' check-alternatives.py`
- **Issue:** The module docstring's prose ("no subprocess calls anywhere in this module") accidentally matched the very pattern the acceptance criteria greps for, even though the script performs no actual subprocess invocations.
- **Fix:** Reworded to "no child-process invocations" — same meaning, no longer trips the literal grep.
- **Files modified:** `sota-numerics/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (and the byte-identical dogfood copy)
- **Verification:** `grep -rn 'subprocess\|os.system\|eval(' check-alternatives.py` returns no matches; re-ran the full Task 1 verification suite, all passing.
- **Committed in:** `246dfbc` (part of Task 1 commit — caught before commit, no separate fix commit needed)

**2. [Rule 1 - Bug] Test-suite temp directories under system `/tmp` broke the script's own project-root resolution**
- **Found during:** Task 2, first test run (15/19 failures, all exit 2)
- **Issue:** `tempfile.TemporaryDirectory()` defaults to system `/tmp`, which has no `.planning/` ancestor — every test using it hit the script's own (correct) exit-2 path meant for genuinely out-of-project directories, masking the actual behavior under test.
- **Fix:** Added a `scratch_dir()` test helper that creates the `TemporaryDirectory` under the project root (`dir=PROJECT_ROOT`, a sibling of `.planning/`, never inside it) so `find_project_root()` resolves correctly; the one test that deliberately wants an out-of-project directory (`TestPathSafety.test_phase_dir_outside_project_root_exits_2`) keeps the default system-temp location.
- **Files modified:** `sota-numerics/tests/test_check_alternatives.py`
- **Verification:** All 19 tests pass; temp dirs are cleaned up automatically (context manager / `finally: shutil.rmtree`), confirmed no stray directories left in the repo tree.
- **Committed in:** `aedac09` (part of Task 2 commit — caught before commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1, both caught and resolved before their task's commit — no separate fix commits, no scope creep).

## Issues Encountered

- The sandbox's shell-command allowlist blocks `python3 -c`, `bash -c`, and `cmp` (inline-interpreter and unlisted-binary restrictions). Every ad hoc verification that needed inline code or byte comparison was rewritten as a script file (`bash /path/to/script.sh`) or `diff` (allowed) instead — no functional impact, just a different invocation shape for manual verification steps. The plan itself anticipated the `python3 -c`/`node -e` restriction in its acceptance criteria note; the `bash -c` and `cmp` restrictions were discovered live and worked around the same way.
- Executed as a Pattern B (checkpoint) plan: Task 1 is `type="tracer"`, and `workflow.auto_advance`/`workflow._auto_chain_active` were both `false`, so per the tracer feedback gate the executor stopped after Task 1's commit and returned a `checkpoint:human-verify`. The coordinator reviewed the automated verification output and approved continuation; Tasks 2-3 then executed and committed in the same session as a continuation.

## User Setup Required

None - no external service configuration required. The capability auto-installs at user scope on next SessionStart via the vendored `capability-auto-install.sh` (Phase 10.1 D-05 mechanism), or can be installed immediately with `gsd capability install sota-numerics`.

## Next Phase Readiness

- The gate spine is proven end-to-end; Plan 02 can now populate the four advisory `contributions[]` fragments (`planner-sota.md`, `executor-numerics.md`, `verifier-precision.md`, `ship-precision-advisory.md`) and their `capability.json` entries without further gate-mechanism risk.
- Plan 03's D-08 checker plausibility spot-check decision (patch vs. fold-in) is unblocked — the mechanical layer (`check-alternatives.py`'s placeholder/TODO rejection, step 8) already ships in this plan as the deterministic half of that decision.
- No blockers. The `sota-numerics.enabled` config key and its default (`true`) are the only surface Plan 02/03 need to gate their own new contributions against — already declared and tested here.

---
*Phase: 11-sota-numerics-capability-plugin-sota-efficiency-numerical-st*
*Completed: 2026-08-17*

## Self-Check: PASSED

All 20 claimed created/modified files verified present on disk; all 3 task commit hashes (`246dfbc`, `aedac09`, `850d38d`) verified present in `git log --oneline --all`.
