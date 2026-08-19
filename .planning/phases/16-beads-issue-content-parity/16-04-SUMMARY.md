---
phase: 16-beads-issue-content-parity
plan: 04
subsystem: infra
tags: [beads, bd, gsd-core-patch, execute-plan.md, D-01, D-02, D-03, D-04, D-05, D-07]

# Dependency graph
requires:
  - phase: 16-beads-issue-content-parity
    provides: "plan 16-03's check_execute_plan_patch()/EXECUTE_PLAN_PATCH_MARKER (the detector this plan wires at plan:pre) and strip_task_bodies (the writer half of the inversion this plan's read-path patch makes safe to trust)"
provides:
  - "Machine-local execute-plan.md bd-task-read patch (gsd-beads-patch:execute-plan-bd-task-read v1) -- gsd-executor now reads an auto/tracer task's instructions from `bd show <beads-id> --json`, halting hard when bd cannot answer (D-01, D-04)"
  - "GSD-CORE-PATCH.md restructured into a two-patch register; Patch 2 documents the new patch verbatim with anchor, marker, upstream issue (open-gsd/gsd-core#3646) and revert condition (D-05)"
  - "beads-recall/SKILL.md Step 3.5 dispatches check-execute-plan-patch alongside check-shipmd-patch at plan:pre -- the independent loss-detector for both patches"
  - "open-gsd/gsd-core#3646 (read-path seam) and open-gsd/gsd-core#3647 (capability lifecycle-dispatch reliability finding) filed upstream, both recorded in STATE.md"
affects: [gsd-executor on this machine for every future plan, phase 16 (this was its final plan), any future phase whose PLAN.md carries stripped/pointer tasks from plan 16-03's sync.py]

# Actuals (#2632)
actuals:
  tokens: 5064
  tasks: 3
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Machine-local marker-bracketed patch, second instance of the ship.md precedent: same six documented parts (target, why, upstream+revert, independence argument, anchor, verbatim content), same PROJECT.md N2 exception already in use, same detector-dispatched-from-an-independent-lifecycle-point discipline (plan:pre here, same as Step 3.5's existing ship.md check)"
    - "Patch register over patch-per-file: GSD-CORE-PATCH.md holds both patches as sibling ## sections under one # register heading, chosen for simplicity (rank 2) over a second GSD-CORE-PATCH-EXECUTE.md file, per 16-RESEARCH.md Open Question 2's recommendation"
    - "Upstream-first framework reporting: two issues filed in the same authenticated gh session -- one a feature ask tied to the local patch (with an explicit revert condition), one a pure observational finding (dispatch reliability) with no corresponding local patch, filed because the evidence was cheap to report and a maintainer cannot gather it from inside one project"

key-files:
  created: []
  modified:
    - "$HOME/.claude/gsd-core/workflows/execute-plan.md (machine-local, outside this repository's git history)"
    - plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md
    - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md
    - .planning/STATE.md

key-decisions:
  - "Edited plugins/beads-lifecycle/.gsd/capabilities/beads/ (git-tracked plugin source) instead of the plan-specified .gsd/capabilities/beads/ -- same gitignored runtime-install mirror footgun 16-01/16-02/16-03 already documented, confirmed via git ls-files before the first edit, and further confirmed the two paths' sync.py were byte-identical (empty diff) before editing, so all live verification commands issued against .gsd/capabilities/beads/scripts/sync.py exercised the same code the tracked source ships"
  - "Task 1 produced no in-repo commit, per the plan's own explicit instruction -- the patched execute-plan.md lives outside this repository's git history, so there is nothing in-repo to commit for that task; its evidence (line counts, marker verification, D-04 signature) is recorded here instead"
  - "Second upstream issue (#3647, capability lifecycle-dispatch reliability) filed distinct from the pre-existing open-gsd/gsd-core#3606, despite both being in the 'wired+enabled capability silently never runs' failure family -- #3606 diagnoses a different, more specific root cause (consumer call sites filtering by kind=='gate' or hardcoding one capability's skill name, making a step-kind hook structurally unreachable at that call site); this project's evidence (wave 1 of Phase 14 fired beads-status's dispatch correctly, waves 2/3 of the SAME phase and SAME call site did not) is inconsistent with a static per-call-site filter and instead points at the dispatch instruction itself (natural language inside a long orchestrator document) being missed on some runs -- reported as a related but mechanistically distinct finding, cross-referenced both ways rather than either filed as a duplicate or silently dropped"

patterns-established:
  - "A second machine-local gsd-core patch under the same N2-exception discipline as the first: this project's constraint override is not a one-off carve-out for ship.md, it is a reusable pattern (documented six-part register section, independent plan:pre/verify:post-class detector, revert condition naming every artifact) any future phase can extend for a third patch without re-litigating the exception"

requirements-completed: [D-01, D-02, D-03, D-04, D-05, D-07]

coverage:
  - id: D1
    description: "gsd-executor reads an auto/tracer task's instructions from bd show <beads-id> --json, not from the PLAN.md task block"
    requirement: "D-01"
    verification:
      - kind: unit
        ref: "live: patch installed at $HOME/.claude/gsd-core/workflows/execute-plan.md, first bullet under item 3 (Per task:), confirmed by sed -n '190,203p' inspection in this session"
        status: pass
    human_judgment: false
  - id: D2
    description: "A failing bd show halts execution with an error naming the unreachable issue -- never a silent fall-back to PLAN.md"
    requirement: "D-04"
    verification:
      - kind: integration
        ref: "live: bd show gsd-beads-no-such-id-16 --json on this machine's bd -- exit=1, stdout {\"error\": \"no issues found matching the provided IDs\", \"schema_version\": 1}, matching 16-RESEARCH.md's recorded signature exactly; the patch's halt branch checks precisely this shape"
        status: pass
    human_judgment: false
  - id: D3
    description: "checkpoint:* tasks are read from PLAN.md exactly as before, and plan-level sections are always read from PLAN.md"
    requirement: "D-02, D-03"
    verification:
      - kind: unit
        ref: "live: grep -c '<step name=\"load_prompt\">' returns 1 with its cat line unchanged; the inserted block's closing paragraph states the checkpoint:* and plan-level-section exclusions verbatim, unrenumbered items 1-5 confirmed by re-reading the surrounding step"
        status: pass
    human_judgment: false
  - id: D4
    description: "A bd issue with an empty description routes to the PLAN.md inline body with a printed notice -- the pre-inversion boundary for Phases 1-15"
    requirement: "D-07"
    verification:
      - kind: unit
        ref: "installed patch text, third branch: 'Success with an empty or absent description -> pre-migration issue... print one line: beads: <beads-id> carries no description -- using inline PLAN.md task body (pre-migration plan)'"
        status: pass
    human_judgment: true
    rationale: "The branch text is installed and byte-verified against GSD-CORE-PATCH.md, but this plan carries no PLAN.md whose tasks were actually stripped with an empty-description bd issue to exercise it live -- the first real inverted plan a future phase runs is the live exercise of this branch"
  - id: D5
    description: "sync.py check-execute-plan-patch reports the patch present after this plan runs, and is dispatched at plan:pre -- a point reached independently of the patch itself; the gsd-core change is filed upstream with an explicit revert condition"
    requirement: "D-05"
    verification:
      - kind: unit
        ref: "live: python3 .gsd/capabilities/beads/scripts/sync.py check-execute-plan-patch exits 0, 'present (v1)'; grep -c 'check-execute-plan-patch' beads-recall/SKILL.md returns 2; python3 -m unittest discover -s plugins/beads-lifecycle/.gsd/capabilities/beads/tests -v -- 125 tests, 0 failures, 0 errors"
        status: pass
      - kind: integration
        ref: "gh issue view 3646 --repo open-gsd/gsd-core --json number,title,state,url -- OPEN, title names the per-task external-tracker read seam"
        status: pass
    human_judgment: false

duration: ~10min
completed: 2026-08-19
status: complete
---

# Phase 16 Plan 04: Install the bd Task-Read Patch, Register It, File It Upstream — Summary

**A machine-local, marker-bracketed patch now makes `gsd-executor` read an `auto`/`tracer` task's instructions from `bd show <beads-id> --json` — halting hard when bd can't answer — closing the loop plan 16-01 (write content to bd) and 16-03 (strip it from PLAN.md) opened, and the read-path change is filed upstream as open-gsd/gsd-core#3646 with a second, unrelated issue (#3647) reporting a capability-dispatch reliability finding.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-08-19T00:07:34Z
- **Tasks:** 3
- **Files modified:** 4 (1 machine-local outside this repo, 3 in-repo)
- **Commits:** 2 (Task 1 produced none, per the plan's own instruction — see Deviations/Decisions)

## Accomplishments

- **Task 1 — the patch itself.** Inserted `<!-- gsd-beads-patch:execute-plan-bd-task-read v1 -->`
  byte-for-byte into `$HOME/.claude/gsd-core/workflows/execute-plan.md`, as the first bullet under
  `<step name="execute">` item 3 ("Per task:"), immediately before the pre-existing `MANDATORY
  read_first gate` bullet. File grew from 558 to 567 lines (9 lines added, purely additive — no
  other line touched). The block installs three mutually exclusive branches: HALT on unreachable
  bd (D-04), read content from a non-empty `description`+`acceptance_criteria` (D-01), or fall
  back to the inline PLAN.md body for a pre-migration issue with an empty description (D-07).
  `checkpoint:*` tasks and all plan-level sections stay untouched (D-02, D-03).
- **Task 2 — the register.** `GSD-CORE-PATCH.md` restructured from a single-patch document into a
  two-patch register: a new top-level intro, the existing `ship.md` content reframed as "Patch 1"
  with its subsections demoted from `##` to `###` (content byte-unchanged), and a new "Patch 2"
  section for `execute-plan.md` carrying the same six parts — target, why (dated to the same
  2026-08-15 N2 override), upstream tracking + a revert condition naming all four artifacts,
  the independence argument, the insertion anchor in prose, the marker pair, and the verbatim
  patch content (confirmed byte-identical to the installed copy by direct diff). `beads-recall/
  SKILL.md`'s Step 3.5 now runs `check-execute-plan-patch` alongside the existing
  `check-shipmd-patch`, both diagnostic-only under `onError: skip`; Anti-Pattern 5 extended to
  protect both. `beads-status/SKILL.md`'s `ship:pre` Step 2d deliberately gets no counterpart —
  confirmed by a zero grep hit.
- **Task 3 — filed upstream.** Searched for an existing equivalent issue first (none found across
  four search-term passes), then filed **open-gsd/gsd-core#3646** ("native per-task
  external-tracker content-resolution seam"), distinct from #3554, cross-referencing it. Filled
  the placeholder left in `GSD-CORE-PATCH.md` with the real number in both the upstream-tracking
  line and the revert condition. Filed a second, separate **open-gsd/gsd-core#3647** reporting
  16-RESEARCH.md's capability lifecycle-dispatch reliability finding (git evidence: exactly one
  `*-BEADS.md`-adding commit across the project's history despite three wired dispatch points and
  eleven phases; Phase 14 wave 1 closed issues, waves 2/3 of the same phase did not), cross-
  referenced against the mechanistically-different but related pre-existing #3606. Both numbers
  recorded in `.planning/STATE.md`'s Blockers/Concerns with the same re-check-before-trusting
  discipline the existing #3559 entry already carries.

## Task Commits

Each in-repo task change was committed atomically; Task 1 touched only the machine-local file
outside this repository and produced no repo commit, per the plan's explicit instruction (see
Deviations):

1. **Task 1: Install the bd task-read patch** — no repo commit (target file outside repository;
   evidence recorded in this SUMMARY)
2. **Task 2: Record the patch in GSD-CORE-PATCH.md and dispatch its detector at plan:pre** —
   `1f587f2` (docs)
3. **Task 3: File the gsd-core change upstream and record its issue number** — `0d1343d` (docs)

**Plan metadata:** committed alongside this SUMMARY (see final commit).

## Files Created/Modified

- `$HOME/.claude/gsd-core/workflows/execute-plan.md` (machine-local, NOT in this repository's git
  history) — the marker-bracketed bd-task-read block, 558→567 lines
- `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` — restructured into a
  two-patch register; new Patch 2 section
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md` — Step 3.5
  extended, Anti-Pattern 5 extended
- `.planning/STATE.md` — two new Blockers/Concerns entries naming both filed issue numbers

## Decisions Made

See `key-decisions` in frontmatter — the path deviation (same footgun as 16-01/16-02/16-03,
pre-verified byte-identical mirror before any edit), Task 1's no-commit rule as stated by the
plan itself, and the reasoning for filing #3647 as distinct from the pre-existing #3606 rather
than adopting it as a duplicate.

## Live Verification Evidence

**Pre/post line count (Task 1 acceptance criterion — additive change):**
```
$ wc -l "$HOME/.claude/gsd-core/workflows/execute-plan.md"   # before edit
558 /home/dd/.claude/gsd-core/workflows/execute-plan.md
$ wc -l "$HOME/.claude/gsd-core/workflows/execute-plan.md"   # after edit
567 /home/dd/.claude/gsd-core/workflows/execute-plan.md
```
9 lines added, none removed or altered — anchor `3. Per task:` count stays 1,
`<step name="load_prompt">` count stays 1 with its `cat` line unchanged (D-02).

**check-execute-plan-patch, before this plan ran (from 16-03-SUMMARY.md, reproduced for
contrast) vs. after:**
```
# before (16-03 close-out)
⚠ execute-plan.md's bd-task-read patch (beads) is missing at ... -- exit code: 1

# after (this plan, Task 1)
$ python3 .gsd/capabilities/beads/scripts/sync.py check-execute-plan-patch
execute-plan.md bd-task-read patch: present (v1) at /home/dd/.claude/gsd-core/workflows/execute-plan.md
exit=0
```

**Marker/anchor counts:**
```
$ grep -c 'gsd-beads-patch:execute-plan-bd-task-read v1' "$HOME/.claude/gsd-core/workflows/execute-plan.md"
2
$ grep -c '3\. Per task:' "$HOME/.claude/gsd-core/workflows/execute-plan.md"
1
```

**D-04 failure signature, re-confirmed live on this machine's `bd` (matches 16-RESEARCH.md
exactly):**
```
$ bd show gsd-beads-no-such-id-16 --json; echo "exit=$?"
Error fetching gsd-beads-no-such-id-16: no issue found matching "gsd-beads-no-such-id-16"
{
  "error": "no issues found matching the provided IDs",
  "schema_version": 1
}
exit=1
```

**Byte-identity between the installed block and `GSD-CORE-PATCH.md`'s recorded copy:**
```
$ diff /tmp/installed_block.txt /tmp/recorded_block_trimmed.txt
(no output)
BYTE-IDENTICAL (9 lines each, only trailing fence artifact excluded from the extraction script)
```

**GSD-CORE-PATCH.md marker counts (Task 2 acceptance criteria):**
```
$ grep -c 'gsd-beads-patch:execute-plan-bd-task-read v1' GSD-CORE-PATCH.md   # >= 2 required
4
$ grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' GSD-CORE-PATCH.md   # >= 3 required, ship.md record survived intact
4
$ grep -c 'check-execute-plan-patch' beads-recall/SKILL.md                  # >= 1 required
2
$ grep -c 'check-shipmd-patch' beads-recall/SKILL.md                        # >= 1 required, existing check joined not replaced
1
$ grep -c 'check-execute-plan-patch' beads-status/SKILL.md                  # == 0 required, deliberately not wired at ship:pre
0
```

**Full test suite, unchanged by this doc-only plan (Task 2 acceptance criterion):**
```
$ python3 -m unittest discover -s plugins/beads-lifecycle/.gsd/capabilities/beads/tests -v
...
Ran 125 tests in 4.118s
OK
```

**Upstream issues filed and confirmed OPEN (Task 3 acceptance criteria):**
```
$ gh issue view 3646 --repo open-gsd/gsd-core --json number,title,state,url
{"number":3646,"state":"OPEN","title":"feat(execute-plan): native per-task external-tracker content-resolution seam","url":"https://github.com/open-gsd/gsd-core/issues/3646"}
$ gh issue view 3647 --repo open-gsd/gsd-core --json number,title,state,url
{"number":3647,"state":"OPEN","title":"obs(dispatch): capability lifecycle-dispatch steps intermittently skipped (beads capability, 3/4 wave-close dispatches missed)","url":"https://github.com/open-gsd/gsd-core/issues/3647"}
$ grep -cE 'open-gsd/gsd-core#[0-9]+' GSD-CORE-PATCH.md   # >= 2 required
4
$ grep -cE 'open-gsd/gsd-core#[0-9]+' .planning/STATE.md  # >= 2 required
3
$ grep -n "PENDING" GSD-CORE-PATCH.md                     # placeholder must be gone
(no match)
```

**Plan-level `<verification>` re-run in full at close-out:**
```
$ python3 .gsd/capabilities/beads/scripts/sync.py check-shipmd-patch
ship.md ship:pre patch: present (v1) at /home/dd/.claude/gsd-core/workflows/ship.md
exit=0   # the pre-existing patch was not disturbed by this plan's edits
```
Human-check items from `<verification>`: read the installed patch in place — confirmed above via
`sed -n '190,203p'` inspection: first bullet under "3. Per task:", halt branch names the
unreachable issue and forbids a PLAN.md fall-back, items 1-5 unrenumbered. Opened both new
upstream issues' text via `gh issue view`/`gh issue create` output — #3646 reads as a
gsd-core-general request (not beads-specific) and cross-references #3554 as related-but-
independent; #3647 is factual, proposes no fix, and cross-references #3606 as related-but-
mechanistically-distinct.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Edited `plugins/beads-lifecycle/.gsd/capabilities/beads/` instead of the plan's `.gsd/capabilities/beads/`**
- **Found during:** Task setup, before any edit (pre-empted via 16-01/16-02/16-03's documented
  root cause and this plan's own `<path_note>`)
- **Issue:** `.gsd/capabilities/beads/GSD-CORE-PATCH.md` and `.gsd/capabilities/beads/skills/
  beads-recall/SKILL.md` are gitignored runtime-install mirrors of the tracked
  `plugins/beads-lifecycle/.gsd/capabilities/beads/` source; edits at the mirror path are
  invisible to git and get silently reverted on the next capability re-sync.
- **Fix:** All edits made directly against
  `plugins/beads-lifecycle/.gsd/capabilities/beads/{GSD-CORE-PATCH.md,skills/beads-recall/SKILL.md}`.
  Additionally confirmed (via `diff`) that the mirror `.gsd/capabilities/beads/scripts/sync.py`
  was byte-identical to the tracked source before running any verify command against the mirror
  path, so the plan's stated `.gsd/capabilities/beads/scripts/sync.py` verify commands exercised
  the same code the commits ship.
- **Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md`,
  `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md`
- **Verification:** `python3 -m unittest discover -s plugins/beads-lifecycle/.gsd/capabilities/beads/tests -v`
  — 125 tests, 0 failures, 0 errors; both commits present in `git log`
- **Committed in:** `1f587f2` (Task 2), `0d1343d` (Task 3)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The plan's task content, patch text, and upstream filings are implemented
exactly as specified — only the on-disk location of the in-repo edits changed, matching the same
footgun 16-01, 16-02, and 16-03 already documented and pre-empted by this plan's own
`<path_note>`.

## Issues Encountered

None beyond the anticipated path deviation above, avoided proactively (confirmed via `git
ls-files` and a byte-identical mirror diff before the first edit).

## User Setup Required

None post-hoc — the plan's `user_setup` entry (gh authenticated against github.com with
issue-create permission on `open-gsd/gsd-core`) was already satisfied at session start
(`gh auth status` confirmed `davdittrich`, active, `repo` scope present) before Task 3 ran.

## Phase 16 Completion

This was phase 16's final plan (4 of 4). All six requirements this phase declared across its
plans (D-01 through D-08, scoped across 16-01/16-02/16-03/16-04) are now implemented and
live-verified on this machine:

- D-01 (task content inverted to bd, stripped from PLAN.md, read back from bd at execute time) —
  16-01 (write), 16-03 (strip), 16-04 (read) — complete, end-to-end
- D-02/D-03 (plan-level sections and checkpoint:* tasks stay in PLAN.md, unaffected by the
  inversion) — 16-04 — complete
- D-04 (hard halt on unreachable bd, no silent fall-back) — 16-04 — complete
- D-05 (upstream-first: filed immediately, revert condition recorded, independent loss detection)
  — 16-03 (detector) + 16-04 (patch + filing) — complete
- D-07 (pre-migration boundary: an empty-description bd issue still routes to inline PLAN.md) —
  16-04 — complete (installed and byte-verified; live exercise deferred to the first future phase
  whose plan is actually inverted and synced — noted under coverage D4's `human_judgment: true`)

No further plans are queued for this phase. Next: `/gsd-verify-work` for phase 16, per the
project's standard phase-completion flow.

---
*Phase: 16-beads-issue-content-parity*
*Completed: 2026-08-19*

## Self-Check: PASSED

- FOUND: `$HOME/.claude/gsd-core/workflows/execute-plan.md` (patch installed, verified present)
- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md`
- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md`
- FOUND: `.planning/STATE.md`
- FOUND: commit `1f587f2`
- FOUND: commit `0d1343d`
- FOUND: open-gsd/gsd-core#3646 (OPEN)
- FOUND: open-gsd/gsd-core#3647 (OPEN)
