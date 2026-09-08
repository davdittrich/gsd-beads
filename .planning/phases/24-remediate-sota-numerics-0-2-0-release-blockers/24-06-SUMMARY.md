---
phase: 24-remediate-sota-numerics-0-2-0-release-blockers
plan: 06
subsystem: infra
tags: [documentation-drift, changelog, prose-review, gate-dispatch-coupling]

# Dependency graph
requires:
  - phase: 24-05
    provides: hooks/gsd-tools.sh and capability.json anchored to their own
      location instead of the caller's working directory (D-13, D-14
      closed); Corpus A/B baseline unchanged (1,0,0,1,0,0 across phases
      19-24, 125/125 Python tests). This plan's own regression sweep
      re-confirms unchanged, since none of its three tasks touch gate
      verdict logic.
provides:
  - "CHANGELOG.md's 0.2.0 section no longer states a hand-maintained
    suite/pass/fail/per-category count -- it names which behaviour
    categories changed verdict, in prose, pinned only to the commit the
    claim was measured at (D-09)."
  - "check-alternatives.py's PLAN_SHAPED_RE comment keeps its
    narrower-than-any-markdown-file reasoning without the corpus-size
    measurement that drifted from 76/10 to 73/9 within the phase (D-09)."
  - "Exactly one spelling of favor/favour survives the tracked bundle --
    hooks/session-start.sh's executor framing sentence now reads
    'favour', settled by a fresh corpus-wide measurement rather than the
    stale D-11 count (D-11)."
  - ".gsd/capabilities/sota-numerics/NOTES.md section 6's residual now
    names a second, larger gsd-core coupling: gate dispatch (step 13e)
    is itself conditioned on workflow.post_planning_gaps, a config key
    the gap-analysis capability owns, so turning it off silently
    disables this capability's only blocking gate with no verdict and
    no error. Tracked as gsd-beads-h1pb, alongside the existing
    ordering-coupling ticket gsd-beads-g72."
affects: []

# Actuals (#2632)
actuals:
  tokens: 1737
  tasks: 3
  commits: 3
  commits_note: >
    Plan's code/doc edits land in a DIFFERENT repository from this
    SUMMARY (target_repo per 24-06-PLAN.md frontmatter): sota-numerics
    checkout at /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013,
    branch feat/extended-sota-definition. tokens/commits above measure
    that repo's diff (git diff f405303..HEAD, 4 files changed, 6,949
    chars / 4 ~= 1,737 tok; git rev-list --count f405303..HEAD = 3),
    not this orchestrator repo. THIS repo (gsd-beads) gets only this
    SUMMARY plus STATE.md/ROADMAP.md/REQUIREMENTS.md updates, docs-only,
    target-repo-external to the plan's own estimate (which quoted
    54,000 tok, low-confidence, against a much larger anticipated diff
    that did not materialize once each task turned out to be a small,
    bounded edit).

tech-stack:
  added: []
  patterns-established:
    - "A residual entry that documents a workflow coupling gets extended
      with a second case rather than replaced when a second, unrelated
      coupling to the same host mechanism is found -- each case is its
      own paragraph, its own upstream ticket, and its own citation of
      the exact host-source lines it was derived against, so a later
      gsd-core upgrade can re-verify one case without disturbing the
      other."
    - "A stale corpus-size claim (D-09) is deleted, not corrected --
      correcting it just re-stages the next staleness at a new number;
      only counts something recomputes survive."

key-files:
  created: []
  modified:
    - CHANGELOG.md (target repo)
    - .gsd/capabilities/sota-numerics/scripts/check-alternatives.py (target repo)
    - hooks/session-start.sh (target repo)
    - .gsd/capabilities/sota-numerics/NOTES.md (target repo)

key-decisions:
  - "Rewrote the CHANGELOG's verdict-change paragraph as prose naming
    categories (phase-resolution, section-boundary, HTML-comment,
    rejected-plan-name, empty-argument, error-message) instead of a
    subtraction with the numbers removed, per the task's own
    instruction not to leave a sentence shaped like a count with the
    count cut out."
  - "Measured favor/favour fresh (1 occurrence each way, matching the
    stale D-11 note) rather than trusting the prior count, and used a
    second word (behaviour/behavior, 6 to 0) to settle which convention
    the corpus follows before changing the drifted word, exactly as
    the task required rather than guessing en-GB from the fragment
    file alone."
  - "Opened a new bd ticket (gsd-beads-h1pb) for the post_planning_gaps
    coupling rather than reusing gsd-beads-g72 -- the task named this a
    second, larger case of the same residual, not the same defect, and
    the existing ticket's own title and body describe the argv-splice
    fix, not the dispatch-gating fix this case needs."
  - "Left plugin.json's and capability.json's 'enforcing on every plan
    in a phase' description strings untouched. REVIEW-CRITICAL-FINAL.md
    P1-4 offered softening those strings as an alternative fix, but
    this task's Files list names only NOTES.md and this SUMMARY --
    the description-string edit is out of this task's scope, not
    silently dropped: the residual itself now states the exception
    plainly, which was P1-4's stated minimal fix."

requirements-completed: [D-09, D-11, D-17]

coverage:
  - id: D1
    description: "No hand-maintained count survives in CHANGELOG.md's
      0.2.0 section or in check-alternatives.py's PLAN_SHAPED_RE
      comment (D-09)."
    requirement: D-09
    verification:
      - kind: unit
        ref: "target repo: `sed -n '/^## 0\\.2\\.0/,/^## 0\\.1/p' CHANGELOG.md | grep -cE '\\b(94|97|62|32|35)\\b'` -> 0; `grep -rnE '\\b7[36] entries\\b' .gsd/capabilities/sota-numerics/scripts/check-alternatives.py` -> 0; commit e7179dd"
        status: pass
    human_judgment: false
  - id: D2
    description: "Exactly one spelling of favor/favour occurs anywhere
      in the tracked bundle, chosen by a fresh corpus-wide measurement
      (D-11)."
    requirement: D-11
    verification:
      - kind: unit
        ref: "target repo: `git grep -hoiwE 'favou?r' -- . | awk ...` -> 1; `bash tests/test-session-start.sh` -- ALL PASS; commit ae46ff1"
        status: pass
    human_judgment: false
  - id: D3
    description: "NOTES.md section 6's residual names the
      workflow.post_planning_gaps configuration key, its default, the
      silent consequence of turning it off, and carries a tracked bd
      ticket for the upstream fix, without softening the existing
      fail-closed text (D-17 residual completeness, REVIEW-CRITICAL-FINAL.md
      P1-4)."
    requirement: D-17
    verification:
      - kind: unit
        ref: "target repo: `grep -c post_planning_gaps .gsd/capabilities/sota-numerics/NOTES.md` -> 3; `grep -n 'Fail-closed covers'` unchanged at line 152; commit 7c77ea9"
        status: pass
    human_judgment: false
  - id: D4
    description: "The two step positions the residual cites (13b, 13e)
      are re-derived live against the installed gsd-core rather than
      trusted from an earlier note, and the version they were derived
      against is recorded beside them."
    verification:
      - kind: other
        ref: "This SUMMARY's 'Step-position re-derivation' section, below"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-17 hash sidecar re-measured before this plan's
      edits and after, using the same absolute-PLUGIN_ROOT-rooted
      method 24-01/24-03/24-04/24-05 verified."
    requirement: D-17
    verification:
      - kind: other
        ref: "This SUMMARY's 'D-17 hash sidecar' section, below"
        status: pass
    human_judgment: false

duration: ~20min
completed: 2026-09-08
status: complete
plan_head_before: f4053035305a3df9f8c6da14f3648d81d89a699b
---

# Phase 24 Plan 06: Remove Stale Claims and Complete the Gate-Dispatch Residual Summary

**Deleted two hand-maintained counts that drift by construction (CHANGELOG's suite/pass/fail split and check-alternatives.py's corpus-size comment), settled a one-word spelling drift on the corpus's own measured convention, and extended NOTES.md's gate-dispatch residual with a second, larger gsd-core coupling -- the `workflow.post_planning_gaps` key that can silently turn this capability's only blocking gate off, now named with its default, its silent consequence, and a new tracked upstream ticket (gsd-beads-h1pb).**

## Performance

- **Duration:** ~20min
- **Completed:** 2026-09-08T08:59:28Z
- **Tasks:** 3/3 complete
- **Commits:** 3 in target repo (sota-numerics worktree) -- docs, docs, docs

## Accomplishments

- **Task 1 (D-09):** `CHANGELOG.md`'s 0.2.0 section no longer states the
  94-test suite size, the 62/32 pass/fail split, or the six per-category
  counts (12/9/4/4/2/1). It names the same six behaviour categories
  (phase-resolution, section-boundary, HTML-comment, rejected-plan-name,
  empty-argument, error-message) as prose, keeps the pinned commit
  (`253bbdc`) the claim was measured at, and rewrote the sentence
  explaining why a commit is named rather than a count so it no longer
  refers to "counts" that are no longer there. `check-alternatives.py`'s
  `PLAN_SHAPED_RE` comment lost the "76 entries across its phase
  directories, 10 plan-shaped, 0 of them misnamed" clause -- a number
  measured against `253bbdc` that was already 73/9 by the time this task
  ran, per the plan's own re-measurement note -- while keeping the
  reasoning the comment introduces (why `PLAN_SHAPED_RE` is narrower than
  "any markdown file"). No test added, per Phase 23 D-21 (no test
  infrastructure for prose): the fix is deletion, not a mechanism.
- **Task 2 (D-11):** Measured the `favor`/`favour` drift fresh rather
  than trusting the stale D-11 note: `git grep -hoiwE 'favou?r'`
  returned one occurrence each way (`hooks/session-start.sh:34` had
  `favor`; `.gsd/capabilities/sota-numerics/fragments/executor-numerics.md:4`
  already had `favour`). Because that count is a tie, it cannot settle
  its own case, so a second word was measured to establish which
  convention the corpus follows: `behaviour`/`behavior` stood at 6 to 0
  for the en-GB spelling. Changed `hooks/session-start.sh`'s executor
  framing sentence from `favor` to `favour` -- the one word the task
  authorized, with the sentence's wording, length and punctuation
  otherwise unchanged (it is echoed into a `SubagentStart` banner whose
  token cost `REVIEW-PROSE-TOKENS.md` already measured). Did not extend
  into a general spelling sweep: D-11 names this one drift, and the
  corpus showed no other.
- **Task 3 (D-17):** Re-derived, live against the installed gsd-core
  1.13.0, the two step positions `.gsd/capabilities/sota-numerics/NOTES.md`
  section 6's residual cites -- step 13b ("Record Planning Completion in
  STATE.md") at `plan-phase.md:1524` and the `plan:post` gate dispatch,
  step 13e, at `plan-phase.md:1558` -- both unchanged from the prior
  note's numbers, and annotated the citation with the version they were
  derived against instead of leaving it implicit. Added a second residual
  subsection, "the same step can be turned off, which silently disables
  this gate": step 13e is the *only* `plan:post` dispatch point for any
  capability's gate, not just gap-analysis's own coverage report, and its
  own opening sentence conditions the whole step on
  `workflow.post_planning_gaps` (default `true`), a config key
  `gap-analysis` owns and `sota-numerics` cannot see or refuse. A project
  that turns that key off never reaches gate dispatch at all -- no
  verdict, no error, nothing an operator would see -- while
  `plugin.json` and `capability.json` still sell the gate as enforcing
  "on every plan in a phase." Opened `gsd-beads-h1pb` for the upstream
  fix (decouple `plan:post` dispatch from `gap-analysis`'s own report
  toggle) and recorded it beside the existing ordering-coupling ticket
  `gsd-beads-g72`. The existing fail-closed text ("Fail-closed covers the
  cases where the phase cannot be identified...") is unchanged, per the
  task's instruction not to soften it.

All work landed in the target repo
(`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`,
branch `feat/extended-sota-definition`), starting from `f405303` (24-05's
final commit, clean tree).

**Task 1: location**
- `e7179dd` (docs) -- `CHANGELOG.md`'s 0.2.0 section rewritten as prose
  naming categories, no counts; `check-alternatives.py`'s
  `PLAN_SHAPED_RE` comment lost its corpus-size clause. Verify:
  `sed -n '/^## 0\.2\.0/,/^## 0\.1/p' CHANGELOG.md | grep -cE '\b(94|97|62|32|35)\b'`
  -> `0`. Python suite unaffected by a comment/docs-only change:
  `python3 -m pytest tests/test_check_alternatives.py -q` -- 125 passed,
  8 subtests passed (unchanged from 24-05's own count).

**Task 2: location**
- `ae46ff1` (docs) -- `hooks/session-start.sh`'s executor framing
  sentence: `favor` -> `favour`. Verify:
  `git grep -hoiwE 'favou?r' -- . | awk ...` -> `1`.
  `bash tests/test-session-start.sh` -- 9/9 cases pass (case6/case7 from
  24-05 unaffected, since this task touches only the executor `FRAMING`
  string, not the resolution logic either pinned).

**Task 3: location**
- `7c77ea9` (docs) -- `.gsd/capabilities/sota-numerics/NOTES.md`
  section 6 residual: step-position citation annotated with the
  gsd-core version it was re-derived against; new second residual
  subsection naming `workflow.post_planning_gaps`. Verify:
  `grep -c post_planning_gaps .gsd/capabilities/sota-numerics/NOTES.md`
  -> `3`. Full regression before commit: `bash tests/test-session-start.sh`,
  `bash tests/test-gate-script-resolution.sh`,
  `bash tests/test-capability-auto-install.sh` -- ALL PASS on all three;
  `python3 -m pytest tests/test_check_alternatives.py -q` -- 125 passed,
  8 subtests passed. Sanity sweep for the literal string the 24-05 note
  warns about (`show-toplevel`) run again across `README.md`,
  `.gsd/capabilities/sota-numerics/NOTES.md`, `hooks/`, and
  `.gsd/capabilities/sota-numerics/capability.json` -- no matches;
  this task's own edits never touch that resolution mechanism.

## Decisions Made

See `key-decisions` in frontmatter -- prose-not-subtraction rewrite for
CHANGELOG (Task 1's own instruction), fresh-measurement-over-trusting-D-11
for the spelling (Task 2's own instruction), new ticket rather than
reusing `gsd-beads-g72` (Task 3's own instruction to record the new
ticket "next" the existing one, implying a distinct identifier), and
leaving the description-string softening in `plugin.json`/`capability.json`
out of scope (Task 3's own Files list names only `NOTES.md` and this
SUMMARY).

## Step-position re-derivation

Re-measured live rather than trusting the residual's existing numbers,
per the task's own instruction and per the project rule against
accepting a prior note as terminal evidence for a currently-installed
runtime file:

```
$ grep -n "^## step\|post_planning_gaps\|Record Planning Completion\|plan:post" \
    ~/.claude/gsd-core/workflows/plan-phase.md
1524:## 13b. Record Planning Completion in STATE.md
1558:## 13e. Post-Planning Gap Analysis (plan:post capability gate dispatch)
1560:Proactive, non-blocking coverage report gated on `workflow.post_planning_gaps`
1561:(default `true`). Dispatched via the `plan:post` capability gate owned by the
```

Confirmed via `node ~/.claude/gsd-core/bin/gsd-tools.cjs runtime-identity --raw`:
`{"packageName":"@opengsd/gsd-core","version":"1.13.0"}` -- the same
version the prior note's numbers were implicitly measured against
(`plan-phase.md:1524`/`:1558` match byte-for-byte), so no line-number
correction was needed; only the missing version annotation was added.

## D-17 hash sidecar

Per D-17, `~/.gsd/capability-auto-install-sota-numerics.hash`
independently re-measured before this plan's edits and after, using the
same absolute-`PLUGIN_ROOT`-rooted method 24-01/24-03/24-04/24-05
verified (`find "$BUNDLE_DIR" ... | sort | sha256sum`, walking
`$WT_ROOT/.gsd/capabilities/sota-numerics`):

| Measurement | Value |
|---|---|
| Pre-edit (independently re-measured, absolute-path method) | `4f7e518bd92473752aa4e6063b1f8b46845bb0c1bbffa0cd20ba6541b4382143` |
| Post-edit (independently re-measured, absolute-path method) | `82e6e84fb0e0b23fd2a93ad8681df12a49a3fed2ea2f406b01ca835fb17c5dd1` |
| Live sidecar (`~/.gsd/capability-auto-install-sota-numerics.hash`), before and after | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` (unchanged) |

The sidecar stayed unchanged across this plan's three commits, matching
the previously-documented stale state 24-01/24-03/24-04/24-05 each
independently confirmed: `hooks/capability-auto-install.sh`'s own
dirty-tree guard (`bundle has uncommitted or ignored files; refusing to
install it at global scope`, observed live in every
`test-session-start.sh`/`test-capability-auto-install.sh` run this plan
executed) keeps the worktree's uncommitted state -- which persisted for
the plan's entire duration between commits -- from ever reaching the
global mirror. The pre-edit and post-edit independently-measured values
differ from each other and from the sidecar for the same
`__pycache__`-mtime-instability reason 24-05-SUMMARY documented in its
own "D-17 hash sidecar" section: this is a pre-existing measurement gap
in `bundle_hash()` itself, not a defect this plan's tasks introduced,
and reconciling the sidecar with a live install remains a later plan's
scope, unchanged from every prior plan's own note.

## Deviations from Plan

None -- plan executed exactly as written. All three tasks' `<verify>`
commands passed on the first run; the only extra work performed was the
D-17 hash re-measurement and the step-position re-derivation, both of
which the plan's own top-level `<context>` and Task 3's own Action
required.

## Known Stubs

None.

## Threat Flags

None -- this plan closes the phase's `<threat_model>` entries T-24-22
(`mitigate`, Task 3 names the key, default and consequence, and files a
tracked ticket), T-24-23 (`mitigate`, Task 1 deletes the stale counts),
T-24-24 (`mitigate`, the Python suite ran after every code-adjacent
comment edit and stayed at 125/125), and T-24-25 (`accept`, the banner
sentence changed in one word and carries no environment-derived
content). No new network endpoint, auth path, file-access pattern, or
schema change introduced.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- D-09, D-11, D-17 (this plan's residual-completeness slice) closed:
  no stale count survives in the two files the review named, one
  spelling of the drifted word survives corpus-wide with its
  measurement recorded, and the NOTES residual now names the
  `workflow.post_planning_gaps` coupling plainly with a tracked
  upstream ticket.
- New upstream ticket `gsd-beads-h1pb` opened (P1, unowned by any
  further phase-24 plan) alongside the pre-existing `gsd-beads-g72`;
  neither blocks this phase's own remaining work, both are gsd-core
  fixes outside this repository's control.
- Remaining phase-24 requirements not yet closed by 24-01/24-03/24-04/24-05/24-06:
  D-06, D-10, D-12, D-15, D-16, D-18 through D-24 (D-06's gate-behaviour
  fixtures, D-10's README claim trace, D-12's marketplace-entry commit
  in this repo, D-15's CodeRabbit-thread triage, D-16/D-20's publish
  ordering, D-18's rejected-alternative record, D-19/D-21's merge-is-publish
  and tag, D-22's decision-checkpoint re-ask, D-23's bd-issue reuse for
  the publish plan, D-24's phase-exit gate).

## Self-Check: PASSED

- FOUND: `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-06-SUMMARY.md`
- FOUND (target repo commits): `e7179dd`, `ae46ff1`, `7c77ea9`
- FOUND (new bd ticket): `gsd-beads-h1pb`
</content>
