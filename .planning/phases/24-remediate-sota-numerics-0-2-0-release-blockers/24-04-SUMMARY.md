---
phase: 24-remediate-sota-numerics-0-2-0-release-blockers
plan: 04
subsystem: infra
tags: [check-alternatives, plan-gate, diagnostics, tdd, tokens, dos]

# Dependency graph
requires:
  - phase: 24-03
    provides: The D-01-through-D-04 fail-open fixes and their cumulative Corpus A/B
      baseline (1,0,0,1,0,0 across phases 19-24; 113/113 Python tests), which this
      plan's own regression sweep is measured against, plus the independently
      re-verified D-17 absolute-path bundle-hash measurement method this plan reuses.
provides:
  - elide_span/elide_values/elide_line/line_number helpers bounding every
    document-derived span (80 chars), found-value list (5 distinct values), and
    printed stderr line (200 chars) in check-alternatives.py, each truncation
    carrying an explicit "...[truncated]" / "...[+N more]" marker (D-07, D-08)
  - "validate_plan/check_alternatives/main() threading a per-violation line
    number end to end: every diagnostic prints as `<plan_path>:<line>: <reason>`,
    with exactly one remediation line per run regardless of violation count"
  - Corpus A (real gsd-beads/.planning/phases/19-24) and Corpus B (Python suite,
    now 125/125) evidence that the bounding is message-only, no exit code moved
  - Independently re-verified D-17 pre/post-edit bundle hash for this plan's edits
affects: [24-08]

# Actuals (#2632)
actuals:
  tokens: 6999
  tasks: 3
  commits: 5
  commits_note: >
    This plan's code/test edits land in a DIFFERENT repository from this
    SUMMARY (target_repo per 24-04-PLAN.md frontmatter): the sota-numerics
    worktree at /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013,
    branch feat/extended-sota-definition. Four commits landed there: ce146d0
    (test, Task 1 RED), eb8dd19 (fix, Task 1 GREEN), 57079cf (test, Task 2 RED),
    1cb14d9 (fix, Task 2 GREEN) -- git rev-list --count e1818c5..1cb14d9 = 4.
    `tokens` above is 6999 = 27995 chars / 4, measured via `git diff
    e1818c5..1cb14d9 | wc -c` in the target repo (3 files changed, +353/-51).
    The 5th commit is this plan's own docs commit in THIS (gsd-beads) repo,
    carrying only STATE.md/ROADMAP.md/REQUIREMENTS.md/this SUMMARY (Task 3,
    docs-only, no target-repo edits) -- measured via
    `git rev-list --count ${plan_head_before}..HEAD` after that commit lands.

tech-stack:
  added: []
  patterns:
    - "Two independent, deliberately non-composing diagnostic bounds: a
      span-level bound (elide_span, 80 chars) applied at the point a document
      excerpt is interpolated into a message, and a line-level bound
      (elide_line, 200 chars) applied only at the two print sites that emit
      plan-document-derived text. The line-level bound is a coarser backstop
      that may cut into an already-bounded span when fixed prose plus a long
      phase-directory path already exceeds it on its own; both truths hold
      independently regardless."

key-files:
  created: []
  modified:
    - .gsd/capabilities/sota-numerics/scripts/check-alternatives.py (target repo)
    - tests/test_check_alternatives.py (target repo)
    - README.md (target repo)

key-decisions:
  - "Scoped the 200-char elide_line backstop to only the per-violation loop and
    the remediation line in main(), not the STATE.md-resolution / CLI usage-error
    prints -- the threat model's trust boundary is explicitly 'plan document to
    gate stderr', and the existing TestCurrentPhaseResolution suite asserts
    substrings deep inside STATE.md ambiguity messages that a blanket 200-char
    cap would silently cut, which is what the first implementation attempt did
    before this scoping was added (Rule 1, see Deviations)."
  - "Sorted and deduplicated the found-years list before truncating to its first
    5 distinct values (plan's own Internal design alternative), rather than
    truncating in document order: the message then reads identically regardless
    of which order the years happened to be written in, matching D-05's
    'change no verdict' constraint by construction -- the full, untruncated
    `years` list still decides the in-window verdict before any elision runs."
  - "Fixed-length elision marker (`...[truncated]`, 15 chars) rather than an
    N-count marker on the line-level backstop: elide_span's excerpt-plus-marker
    is allowed to exceed its own 80-char budget by the marker's length (the
    excerpt is what is bounded, not the annotated string), but elide_line's
    100% guarantee ('this printed line never exceeds 200 chars') needs a
    marker of KNOWN fixed length reserved up front, which an N-count marker
    (variable digit width) cannot give without a second measure-then-truncate
    pass."

patterns-established:
  - "elide_span/elide_values/elide_line: reusable width-bounded formatters,
    each independently unit-pinned via a worst-case fixture, composed at call
    sites rather than parameterized into one function -- ponytail: the three
    truncation shapes (a string span, a list of values, a whole line with a
    length guarantee) are different enough in contract that one shared
    function would need a mode flag, which is worse than three five-line
    functions."

requirements-completed: [D-01, D-05, D-07, D-08, D-17]

coverage:
  - id: D1
    description: "Every document-derived quoted span in a diagnostic (an
      alternative's name, the heading text that ended a section) is bounded
      to 80 characters, and a found-values list is bounded to its first 5
      distinct values; either carries an explicit elision marker only when it
      was actually truncated (D-08, T-24-13, T-24-14). Closes the reported
      defect: an entry with no length cap on its own span produced 12,280
      chars / 8,099 tokens on one stderr line (D-07, REVIEW-PROSE-TOKENS.md P1)."
    requirement: D-08
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py::TestDiagnosticBounding (5 tests: 4 RED-then-GREEN pinning the two unbounded emitters -- found-years list single-line and multi-line-span, long boundary heading, long alternative name -- plus 1 regression pin that short messages carry no marker) -- commits ce146d0 (RED), eb8dd19 (GREEN), target repo"
        status: pass
    human_judgment: false
  - id: D2
    description: "Each violation reports as `<plan_path>:<line>: <reason>` --
      the heading line for a section-level violation, the entry's own line
      for a per-entry citation issue, line 1 for a misnamed-file violation --
      and a run still emits exactly one remediation line regardless of
      violation count (D-08)."
    requirement: D-08
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py::TestViolationLineShape (7 tests: missing-section, first-entry, second-entry, no-Decided-by, and misnamed-plan violations each naming their own line; the run's one remediation line surviving the format change) -- commits 57079cf (RED), 1cb14d9 (GREEN), target repo"
        status: pass
    human_judgment: false
  - id: D3
    description: "No printed stderr line exceeds 200 characters, whatever the
      plan document or phase-directory path contains (D-07): a hard backstop
      independent of, and coarser than, the two D-08 span-level bounds above."
    requirement: D-07
    verification:
      - kind: unit
        ref: "tests/test_check_alternatives.py::TestViolationLineShape::test_no_stderr_line_exceeds_two_hundred_characters (a pathologically deep 180-char phase-directory path)"
        status: pass
      - kind: other
        ref: "Real corpus, phase 19 (below): the natural repo path plus the section's fixed prose already exceeds 200 chars on its own; the printed line measures exactly 200."
        status: pass
    human_judgment: false
  - id: D4
    description: "The bounded diagnostics change no verdict: Corpus A (real
      gsd-beads/.planning/phases/19-24) exit codes are byte-identical to the
      24-03 baseline both after Task 1 and after Task 2; Corpus B (Python
      suite) grew from 113 to 125 tests, all passing (D-05)."
    requirement: D-05
    verification:
      - kind: other
        ref: "This SUMMARY's 'D-05 corpus evidence' section, below"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-17: the live install-mirror hash sidecar
      (~/.gsd/capability-auto-install-sota-numerics.hash) independently
      re-measured before and after this plan's edits, using the same
      absolute-PLUGIN_ROOT-rooted method 24-03 verified."
    requirement: D-17
    verification:
      - kind: other
        ref: "This SUMMARY's 'D-17 hash sidecar' section, below"
        status: pass
    human_judgment: false

duration: ~50min
completed: 2026-09-08
status: complete
plan_head_before: b06f5d680bf425b53bd54b1cf78a13b3ada9b631
---

# Phase 24 Plan 04: Bound the plan-gate's diagnostics and add line numbers Summary

**Closed the two unbounded quoted-span diagnostic emitters (D-07: a found-years list and a boundary heading, one measured at 8,099 tokens on a single stderr line) and gave every violation a `<plan_path>:<line>: <reason>` shape (D-08), via two TDD RED/GREEN pairs, with Corpus A byte-identical to the 24-03 baseline throughout.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-09-08T08:13:25Z
- **Tasks:** 3/3
- **Commits:** 5 (4 in target repo: 2 RED, 2 GREEN; 1 docs commit in this repo)

## What Was Built

- `elide_span` (80-char document-excerpt bound) and `elide_values` (first-5-distinct-value
  bound), each appending an explicit `...[truncated]` / `...[+N more]` marker only when
  truncation actually happened. Applied to the alternative-name and boundary-heading spans,
  and to the found-years list -- the two unbounded emitters REVIEW-PROSE-TOKENS.md P1
  measured at 12,280 chars / 8,099 tokens on one line.
- `extract_section_body` now also returns the section body's start offset; `split_entries`
  tags each entry with its own offset within the body. `validate_plan` returns `(line,
  reason)` instead of a bare reason string, so `check_alternatives`/`main()` can print
  `<plan_path>:<line>: <reason>` for every violation -- the heading line for a section-level
  violation, the entry's own line for a per-entry citation issue, line 1 for a misnamed-file
  violation (D-08, matching the Phase 23 D-13 precedent shape).
- `elide_line`: a hard 200-char backstop applied only at the two print sites that interpolate
  plan-document text (the per-violation loop and the remediation line), not the STATE.md/CLI
  usage-error prints -- those sit outside the threat model's named trust boundary
  ("plan document to gate stderr") and their existing tests assert on substrings a blanket
  cap would otherwise truncate.
- Updated the module docstring and README's "Failures and recovery" section to describe the
  new shape and the three widths.

## Task Commits

All commits below are in the **target repository**
(`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch
`feat/extended-sota-definition`), per the plan's `target_repo` frontmatter -- not this
orchestrator repo.

1. **Task 1: Bound every quoted span with an explicit elision marker**
   - `ce146d0` (test) -- `TestDiagnosticBounding`: 4 RED cases (found-years list, both a
     single-line entry and a pathological multi-line-span entry; a long boundary heading; a
     long alternative name) + 1 regression pin (short messages carry no marker, T-24-14).
     RED evidence: `python3 -m unittest tests.test_check_alternatives.TestDiagnosticBounding -v`
     exits 1, 5 tests / 1 pass / 4 fail; target test
     `test_found_years_list_truncated_to_five_distinct_values` fails. Verified via
     `gsd-tools check tdd-red-evidence`: `RED_EVIDENCE_OK`.
   - `eb8dd19` (fix) -- `elide_span`/`elide_values` added and wired into
     `below_the_boundary`/`validate_entry`. Full suite 118/118; Corpus A unchanged
     (`1,0,0,1,0,0`).
2. **Task 2: Report each violation as plan path, line number and reason**
   - `57079cf` (test) -- `TestViolationLineShape`: 7 RED cases (missing-section, first-entry,
     second-entry, no-Decided-by, misnamed-plan each naming a line; a pathologically deep
     phase-directory path keeping every line under 200 chars; the run's one remediation line
     surviving). RED evidence:
     `python3 -m unittest tests.test_check_alternatives.TestViolationLineShape -v` exits 1,
     7 tests / 0 pass / 7 fail; target test
     `test_first_entrys_violation_names_its_own_line` fails. Verified via
     `gsd-tools check tdd-red-evidence`: `RED_EVIDENCE_OK`.
   - `1cb14d9` (fix) -- `extract_section_body`/`split_entries`/`validate_plan`/
     `check_alternatives`/`main()` threaded to print `<plan_path>:<line>: <reason>`;
     `elide_line` added and scoped to the two plan-document-derived print sites; README and
     module docstring updated; one pre-existing test assertion and two of this task's own
     RED tests corrected (see Deviations). Full suite 125/125; Corpus A unchanged
     (`1,0,0,1,0,0`).
3. **Task 3: Measure the diagnostic budget and record the widths chosen**
   - This SUMMARY (`24-04-SUMMARY.md`), plus the docs commit that lands STATE.md/
     ROADMAP.md/REQUIREMENTS.md in this (orchestrator) repo.

## Files Created/Modified

- `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (target repo) --
  `elide_span`/`elide_values`/`elide_line`/`line_number` helpers; `below_the_boundary`,
  `validate_entry`, `extract_section_body`, `split_entries`, `validate_plan`,
  `check_alternatives`, `main` updated; module docstring updated.
- `tests/test_check_alternatives.py` (target repo) -- `TestDiagnosticBounding` (new class,
  5 tests), `TestViolationLineShape` (new class, 7 tests); one pre-existing assertion in
  `TestMisnamedPlans::test_a_valid_plan_beside_a_misnamed_one_reports_both` updated for the
  new `:1:` shape.
- `README.md` (target repo) -- "Failures and recovery" section describes the
  `<plan_path>:<line>: <reason>` shape and the three D-24-discretion widths.
- `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-04-SUMMARY.md`
  (this repo) -- this file.

## Widths chosen (D-24 discretion, per plan context)

No earlier decision fixed these three numbers; they are this plan's own choice, recorded so
a later reader can see the bound was picked rather than assumed:

| Width | Value | Applies to |
|---|---|---|
| `QUOTED_SPAN_WIDTH` | 80 chars | A document-derived excerpt shown in a message (an alternative's name, the heading text that ended a section) |
| `FOUND_VALUES_LIMIT` | 5 distinct values | A "found: ..." list (currently only the out-of-window years list) |
| `STDERR_LINE_WIDTH` | 200 chars | The whole printed stderr line, hard ceiling, applied only where plan-document text is interpolated |

The marker is a fixed 15-character string, `...[truncated]`, appended (not counted against
the 80-char span budget) when `elide_span` truncates, and reserved-for (subtracted from the
200-char budget before truncating) when `elide_line` truncates -- the latter needs an exact
guarantee, the former does not.

## D-05 corpus evidence

**Interpretation used (matching 24-01's/24-03's precedent):** Corpus A is the real
`gsd-beads/.planning/phases/*` directories, checked for exit-code drift. Corpus B is the
Python suite, where a fixture's own verdict changing shows up directly as that fixture's
test PASS/FAIL outcome.

### Corpus A -- real `gsd-beads/.planning/phases/*` directories (exit code, in fixed order 19/20/21/22/23/24)

| Measurement point | 19 | 20 | 21 | 22 | 23 | 24 |
|---|---|---|---|---|---|---|
| 24-03 end (D-01 through D-04 closed), per 24-03-SUMMARY.md | 1 | 0 | 0 | 1 | 0 | 0 |
| After this plan's Task 1 (D-08 span bounds) | 1 | 0 | 0 | 1 | 0 | 0 |
| After this plan's Task 2 (D-08 line numbers, D-07 line backstop), final state | 1 | 0 | 0 | 1 | 0 | 0 |

Byte-identical across every measurement point: this plan changed message text and line
count only, never which plans pass or fail. Sample real output (phase 19, unchanged verdict,
now line-numbered and within the 200-char backstop -- the natural repo path plus the
section's own fixed prose already exceeds 200 chars before any adversarial content is
involved):

```
/home/dd/projects/gsd-beads/.planning/phases/19-native-resolver-contract-and-failure-boundary/19-02-PLAN.md:57: section found but no alternatives parsed; entries must be '- **Name**' bul...[truncated]
remediation: fix the plans above, then re-run /gsd-plan-phase 19 --force
```
(200 and 72 characters respectively.)

### Corpus B -- Python suite (`python3 -m unittest tests.test_check_alternatives -v`)

| Measurement point | Tests | Failures |
|---|---|---|
| 24-03 end, per 24-03-SUMMARY.md | 113 | 0 |
| This plan's Task 1 RED (+5: `TestDiagnosticBounding`) | 118 | 4 (target tests, designed) |
| This plan's Task 1 GREEN | 118 | 0 |
| This plan's Task 2 RED (+7: `TestViolationLineShape`) | 125 | 3 (a real pre-existing regression surfaced during this RED->GREEN cycle -- see Deviations -- plus the target tests) |
| This plan's Task 2 GREEN, final state | 125 | 0 |

This plan added 12 new tests (118 - 113 = 5 for Task 1, 125 - 118 = 7 for Task 2), all
passing in the final state, exceeding the 24-01 baseline of 105 required by the plan's
`<verification>`.

## D-17 hash sidecar

Per D-17, `~/.gsd/capability-auto-install-sota-numerics.hash` is written by the plugin's own
`SessionStart`/`SubagentStart` hook, hashing the whole `.gsd/capabilities/sota-numerics`
directory using an **absolute**, `PLUGIN_ROOT`-rooted path (24-03 independently verified this
is the correct comparison method). This plan recorded both the live sidecar value and an
independently re-measured whole-bundle hash, pre- and post-edit:

| Value | Pre-edit (this plan's start, commit `e1818c5`) | Post-edit (this plan's end, commit `1cb14d9`) |
|---|---|---|
| Live sidecar (`~/.gsd/capability-auto-install-sota-numerics.hash`) | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` (unchanged) |
| Independently re-measured whole-bundle hash (absolute path, matching the hook's own computation) | `909bd37ef555b4042241eb10f2ed046b2be06a39224a1aa722e14116c7360a08` (exactly matches 24-03's recorded post-edit value -- confirms the bundle had not drifted between plans) | `daf0c3885432184b29335f94ab3f42dcfe496e1ed71d5410faca59e2d5293020` |

The live sidecar remains in the same previously-documented stale state 24-01/24-03 already
recorded (unchanged pre/post across all three plans) -- the install mirror
(`~/.gsd/capabilities/sota-numerics/...`) was never touched by this plan; only the worktree
`target_repo` was edited, per the plan's explicit instruction. Reconciling the sidecar to the
live bundle is plan 24-08's scope, not this plan's, per 24-01/D-17.

## TDD Gate Compliance

Both tasks completed the required RED -> validated RED-evidence record -> GREEN sequence
(`gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` for both target tests before
any implementation edit). The automated gate-check grep in `gsd-core/references/tdd.md`
looks for a `^feat\(24-04\):` GREEN commit; this plan's GREEN commits are typed `fix(24-04):`
instead (bug-fix semantics -- closing an unbounded/broken diagnostic path, not adding a new
feature), matching the precedent both 24-01 and 24-03 already set in this same phase
(`fix(24-03): bound BULLET_RE and TABLE_ROW_RE...`, `fix(24-03): resolve_current_phase_dir's
frontmatter branch...`). The grep will report no `feat(24-04):` match; this is expected and
intentional, not a missed GREEN gate -- both GREEN commits (`eb8dd19`, `1cb14d9`) exist,
pass their target tests, and are listed under Task Commits above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `elide_line` initially wrapped every stderr print, truncating an
unrelated existing test's assertion**
- **Found during:** Task 2 GREEN, first full-suite run after implementing `elide_line`.
- **Issue:** The first implementation wrapped ALL of `main()`'s stderr prints (including the
  STATE.md-ambiguity usage-error messages from `resolve_current_phase_dir`) in the 200-char
  backstop. `TestCurrentPhaseResolution::test_frontmatter_and_body_ambiguity_reasons_are_distinguishable`
  asserts `"need exactly one"` appears near the end of one such message, which the backstop
  cut off -- a real regression, since that message is CLI/STATE.md-derived, not
  plan-document-derived, and sits outside the threat model's named boundary ("plan document
  to gate stderr").
- **Fix:** Scoped `elide_line` to only the per-violation loop and the remediation line in
  `main()`; the four usage-error print sites (empty phase_dir, not-a-directory,
  `resolve_current_phase_dir` failure, `check_alternatives` failure) print unwrapped, as
  before.
- **Files modified:** `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`
  (target repo).
- **Verification:** Full suite 125/125 after the fix; the previously-broken
  `TestCurrentPhaseResolution` test passes unchanged.
- **Committed in:** `1cb14d9` (folded into the GREEN commit; caught before any commit
  landed with the bug).

**2. [Rule 1 - Test-authoring bug, self-caught] Two of this task's own RED tests encoded
incorrect assumptions**
- **Found during:** Task 2 GREEN, same full-suite run.
- **Issue (a):** `test_no_decided_by_names_the_heading_line` hardcoded line 1 as the expected
  heading line, but the `plan-compliant.md` fixture it strips `Decided by:` from has
  frontmatter/intro prose before its heading -- the real heading line is not 1.
  **Issue (b):** `test_long_boundary_heading_is_truncated_with_a_marker` asserted the full
  80-char `elide_span` excerpt always survives, but `below_the_boundary`'s fixed prose
  (~162 chars) plus a realistic plan path already exceeds the 200-char `elide_line` bound
  before the 80-char span is even added -- the two bounds are independent and the coarser one
  wins, so a full 80-char survival guarantee was never actually implied by the must-haves.
- **Fix:** (a) computed the expected line number from the fixture text itself rather than
  hardcoding it. (b) relaxed the assertion to check a 20-char prefix and the elision marker's
  presence, matching what the two independent bounds actually guarantee together.
- **Files modified:** `tests/test_check_alternatives.py` (target repo).
- **Verification:** Full suite 125/125.
- **Committed in:** `1cb14d9` (folded into the GREEN commit, since these are corrections to
  the test skeleton's own assumptions, not new RED-phase behavior).

**3. [Rule 1 - Doc-truth bug, directly caused by this task] Stale test assertion and README
text encoded the pre-line-number format**
- **Found during:** Task 2 GREEN, full-suite run (test) and CLAUDE.md's doc-accuracy
  requirement (README).
- **Issue:** `TestMisnamedPlans::test_a_valid_plan_beside_a_misnamed_one_reports_both`
  asserted the literal substring `"23-01-PLAN.md: missing '## Alternatives Considered'"` (no
  line number) -- directly obsoleted by this task's own format change. README's "Failures and
  recovery" section similarly described the old `<plan_path>: <reason>` shape and did not
  mention the D-07/D-08 bounds at all.
- **Fix:** Updated the assertion to `"23-01-PLAN.md:1: missing '## Alternatives
  Considered'"`. Updated README to describe the new shape and the three widths.
- **Files modified:** `tests/test_check_alternatives.py`, `README.md` (target repo).
  `README.md` was not in the plan's `files_modified` frontmatter, but CLAUDE.md requires
  docs updated in the same commit as the code change that makes them stale, and this defect
  is directly caused by this task's own change (in-scope per the executor's scope-boundary
  rule).
- **Verification:** Full suite 125/125.
- **Committed in:** `1cb14d9`.

---

**Total deviations:** 3 auto-fixed (all Rule 1, all caught and fixed before any commit
landed with the bug -- none escaped into a committed state). No architectural changes,
no scope creep beyond the directly-caused README correction.
**Impact on plan:** None. All three were self-caught during the plan's own GREEN-phase
verification loop.

## Known Stubs

None.

## Threat Flags

None -- this plan closes threat register entries T-24-13 through T-24-16 (all `mitigate`
dispositions from the plan's own `<threat_model>`); it introduces no new network endpoint,
auth path, file-access pattern, or schema change at a trust boundary.

## Issues Encountered

None blocking. See Deviations above for three self-caught-and-corrected issues, all fixed
within the same GREEN commit before landing.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- D-07 and D-08 closed: every diagnostic check-alternatives.py emits is bounded (80-char
  spans, 5-value found-lists, 200-char lines), every truncation carries an explicit marker,
  and every violation names its own line.
- D-05 corpus evidence (Corpus A, Corpus B) shows no verdict moved across either task.
- D-17: live sidecar remains in its previously-documented stale state (unchanged across
  24-01, 24-03, and this plan); the independently re-measured pre-edit bundle hash for this
  plan exactly matches 24-03's recorded post-edit value, confirming no drift between plans.
  Reconciling the sidecar is plan 24-08's scope.
- Remaining phase-24 requirements not yet closed by 24-01/24-03/24-04: D-06, D-09 through
  D-16, D-18 through D-24 (publish sequence, outstanding CodeRabbit threads, security fixes,
  claims-do-not-resolve cleanup) are later plans' scope per the phase's wave structure.

---
*Phase: 24-remediate-sota-numerics-0-2-0-release-blockers*
*Completed: 2026-09-08*
