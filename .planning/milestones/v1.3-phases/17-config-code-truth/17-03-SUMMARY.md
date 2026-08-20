---
phase: 17-config-code-truth
plan: 03
subsystem: beads-lifecycle-sync
tags: [config-truth, sync-mode, declaration-narrowing, truth-01, d-04-migration]
requires:
  - phase: 17-config-code-truth
    provides: "read_sync_mode wired into create-issues path (17-02)"
provides:
  - "capability.json beads.sync_mode narrowed to [\"authoritative\", \"mirror\"] -- the retired \"off\" value is gone from the declaration (D-01/D-02)"
  - "check_sync_mode_value(project_root) -- read-only, never-raises stdout notice for a project holding an out-of-enum sync_mode value, dispatched at plan:pre (D-04 Case 2)"
  - "Every doc, comment, and changelog entry describing beads.sync_mode reads true against the shipped code -- zero surviving 'reserved for later'/'not yet implemented'/ownership-framing claims"
affects:
  - "capability.json's config.beads.sync_mode block"
  - "lifecycle_dispatch's plan:pre branch"
  - "README.md, CHANGELOG.md, docs/prd-beads-capability.md, PRIME.md"
actuals:
  tokens: 8355
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - "Presence-vs-effective-value split (BINDING, both cross-AI reviewers): check_sync_mode_value answers 'is this key present' with a membership test against the raw parsed beads mapping, before and independently of read_beads_config's isinstance(value, type(default)) effective-value read -- the latter alone collapses 'key absent' and 'key present, wrong type' into the identical default and cannot tell a silent case from a notice case apart"
    - "Stdout-for-notices-that-must-be-seen vs stderr-for-benign-skips: check_sync_mode_value deliberately breaks from check_shipmd_patch/check_execute_plan_patch's stderr-only convention because hooks/lifecycle-dispatch.sh promotes only stdout into additionalContext, and the whole point of a D-04 Case 2 notice is that a user encounters it without acting"
    - "Sanitize-then-repr() rendering for an untrusted config value entering agent-readable context: strip non-printable characters (str.isprintable() catches both control chars and newlines), truncate to a bounded length, then wrap in repr() so the notice always shows a quoted, single-line, unambiguous token even for an empty or newline-bearing value"
key-files:
  created: []
  modified:
    - plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
    - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - CHANGELOG.md
    - README.md
    - docs/prd-beads-capability.md
    - plugins/beads-lifecycle/.agents/skills/beads/PRIME.md
    - .gsd-capabilities.json
key-decisions:
  - "Implemented CONTEXT.md's chosen option (d): keep the key, retire 'off' (duplicated beads.enabled: false), make 'mirror' real by exposing the allow_strip parameter that has existed since 0.3.1 -- not narrow-only (a) and not implement-both (b), per the plan's Alternatives Considered table"
  - "D-04 Case 1 (a project already holding 'mirror') gets no code path at all -- the value was inert and becomes meaningful for free, recorded only as a CHANGELOG on-upgrade behavior-change note, not a migration mechanism"
  - "D-04 Case 2 (a project holding the retired 'off' value or any other undeclared value) gets exactly one stdout notice per plan:pre dispatch, never an error, and the capability still never writes to .planning/config.json -- verified live and by a source-assertion grep"
patterns-established:
  - "A retired enum value is removed from the declaration in the same commit as every doc describing it, with a preceding RED test commit that fails against the pre-narrowing declaration -- doc correctness is treated as a testable artifact (capability.json is read by the test suite itself), not a manual sweep trusted to memory"
requirements-completed: [TRUTH-01]
coverage:
  - id: D1
    description: "capability.json's beads.sync_mode.values array equals exactly [\"authoritative\", \"mirror\"] by equality and order, default unchanged, and gsd-tools config-set's live enum validator enumerates exactly the same two values after the overlay re-sync"
    requirement: "TRUTH-01"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestSyncModeDeclarationParity.test_declared_values_array_is_exactly_authoritative_then_mirror"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestSyncModeDeclarationParity.test_default_is_unchanged"
        status: pass
      - kind: command
        ref: "live: gsd-tools config-set beads.sync_mode bogus -> 'Valid values: authoritative, mirror' (was 'authoritative, mirror, off' before this plan); gsd-tools config-set beads.sync_mode mirror succeeds"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every declared value is read by a code path a test exercises -- a parity assertion that iterates capability.json's own declared array, so a future value added without a covering test goes red"
    requirement: "TRUTH-01"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestSyncModeDeclarationParity.test_every_declared_value_has_a_covering_test"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestCreateIssuesCliSyncModeGate (test_authoritative_strips_task_body, test_mirror_leaves_task_body_intact -- the two arm-proving tests the parity assertion checks for)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Comparison against the mirror value is exact code-point string equality: a case variant, a whitespace-padded variant, and a Cyrillic homoglyph of \"mirror\" all fall through to authoritative (stripping) behavior rather than being silently treated as mirror"
    requirement: "TRUTH-01"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestSyncModeAdjacencyAndEncoding (case/whitespace/homoglyph arms, all asserting the strip still happens)"
        status: pass
    human_judgment: false
  - id: D4
    description: "No doc, comment, or changelog entry in the repo describes an effect beads.sync_mode does not have -- the roadmap's re-grepped offender list (README, CHANGELOG x3 spots, docs/prd-beads-capability.md, PRIME.md) is fully swept in the same commit as the declaration change"
    requirement: "TRUTH-01"
    verification:
      - kind: command
        ref: "! grep -Eqi 'reserved for later|not yet implemented' README.md and the same on capability.json -> clean"
        status: pass
      - kind: command
        ref: "! git grep -n 'sync_mode' -- . ':!.planning' | grep -Eiq 'owns (task )?status|controls who owns' -> clean"
        status: pass
      - kind: command
        ref: "grep -c '### Changed' CHANGELOG.md >= 1 within the 0.4.0 section, naming the on-upgrade behavior change and the resolved Known-issue"
        status: pass
    human_judgment: true
    rationale: "The CHANGELOG Performance-section timeout correction and the 0.3.0 entry's stale cross-reference fix are prose corrections whose accuracy was verified by reading the corrected section, not by a single mechanical grep -- recorded as human_judgment per this plan's own acceptance-criteria wording ('verified by reading the corrected section')."
  - id: D5
    description: "check_sync_mode_value's full silent/notice truth table: absent config file, absent beads object, and absent key are silent; both declared values are silent; the retired value, an empty string, a case variant, a whitespace variant, and a non-string value each produce exactly one notice; a newline-bearing value still yields a single line; two consecutive dispatches against an unchanged project produce the identical single notice"
    requirement: "TRUTH-01"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestCheckSyncModeValue (18 methods covering every shape in the truth table)"
        status: pass
    human_judgment: false
  - id: D6
    description: "BINDING cross-AI-review acceptance criterion: an absent sync_mode key and a present-but-wrong-typed one (JSON literal true) produce different stdout -- silence vs. exactly one notice -- even though read_sync_mode resolves both to the identical effective default, because presence is answered by a membership test against the raw parsed beads mapping"
    requirement: "TRUTH-01"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestCheckSyncModeValue.test_absent_key_vs_wrong_typed_key_produce_different_stdout"
        status: pass
    human_judgment: false
  - id: D7
    description: "check_sync_mode_value never raises, never writes to .planning/config.json, and lifecycle_dispatch('plan:pre') stays fail-open (returns 0, still writes BEADS-RECALL.md) when it raises"
    requirement: "TRUTH-01"
    verification:
      - kind: unit
        ref: "tests/test_sync.py#TestCheckSyncModeValue.test_never_raises_and_returns_zero_when_config_is_malformed_json"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestCheckSyncModeValue.test_no_config_write_path_exists"
        status: pass
      - kind: unit
        ref: "tests/test_sync.py#TestCheckSyncModeValue.test_lifecycle_dispatch_plan_pre_calls_it_and_stays_fail_open_on_raise"
        status: pass
      - kind: command
        ref: "! grep -Eq 'config\\.json.*write_text|write_text.*config\\.json' scripts/sync.py -> clean (no config-write path introduced)"
        status: pass
    human_judgment: false
  - id: D8
    description: "A live lifecycle-dispatch plan:pre in a scratch bd project holding the retired value prints exactly one stdout notice naming it and exits 0; the same project reconfigured to a declared value prints no such line"
    requirement: "TRUTH-01"
    verification:
      - kind: command
        ref: "live scratch project (bd init, .planning/config.json {\"beads\":{\"sync_mode\":\"off\"}}): python3 scripts/sync.py lifecycle-dispatch plan:pre -> exit 0, exactly one stdout line naming 'off'; reconfigured to \"authoritative\" -> exit 0, no such line"
        status: pass
    human_judgment: false
duration: ~23min
completed: 2026-08-20
status: complete
---

# Phase 17 Plan 03: sync_mode Value Truth Summary

**`beads.sync_mode` narrows to `["authoritative", "mirror"]` with both values now doing something distinct (mirror withholds the `create-issues` strip), and a project holding the retired `off` value gets exactly one `plan:pre` stdout notice -- never a write to its config, never an error.**

## Performance
- **Duration:** ~23min (worktree base e46b86d 02:27:17 -> final task commit 804a662 02:50:38, 2026-08-20)
- **Started:** 2026-08-20T02:27:17+02:00
- **Completed:** 2026-08-20T02:50:38+02:00
- **Tasks:** 2/2
- **Files modified:** 8 (capability.json, sync.py, test_sync.py, CHANGELOG.md, README.md, docs/prd-beads-capability.md, PRIME.md, .gsd-capabilities.json)

## Accomplishments
- `capability.json`'s `beads.sync_mode.values` narrows from `["authoritative", "mirror", "off"]`
  to exactly `["authoritative", "mirror"]` (D-01) -- the retired `off` value duplicated
  `beads.enabled: false`, already implemented and already the documented opt-out. The
  `description` is rewritten to state what each value does to the `create-issues` strip decision
  instead of "reserved for later phases."
- Every remaining doc, comment, and changelog entry describing the key is swept in the same
  commit as the declaration change: `README.md`'s config table row and Caveats bullet,
  `docs/prd-beads-capability.md`'s F1 row and JSON schema excerpt, `PRIME.md`'s config-keys
  bullet, and `CHANGELOG.md`'s new 0.4.0 `### Changed` section (declaration narrowing + D-04
  Case 1), plus corrections to the 0.3.1 Performance timeout bullet, the 0.3.1 Known-issue
  (marked resolved), and the 0.3.0 entry's stale cross-reference.
- `check_sync_mode_value(project_root)` (Task 2, D-04 Case 2): a read-only, never-raises stdout
  notice for a project whose stored `sync_mode` falls outside the declared enum. Answers presence
  via a membership test against the raw parsed `beads` mapping -- before and independently of any
  effective-value read -- so it correctly distinguishes an absent key from a present-but-wrong-typed
  one, which `read_sync_mode` alone cannot do (BINDING, both cross-AI reviewers). Wired into
  `lifecycle_dispatch`'s `plan:pre` branch beside the two existing patch checks, inside the same
  `try/except Exception`.
- `_sanitize_notice_value` strips non-printable characters and bounds length before the offending
  value is rendered with `repr()`, so a crafted or newline-bearing config value cannot inject lines
  or fabricate structure into the notice, and always shows a quoted, single-line, unambiguous token.
- Live-verified end to end in a scratch `bd` project: a stored retired `off` value produces exactly
  one stdout notice at `lifecycle-dispatch plan:pre` and exits 0; a declared `authoritative` value
  produces none. `gsd-tools config-set beads.sync_mode bogus` now enumerates exactly the two
  declared values (was three before this plan).

## Task Commits
1. **Task 1 RED: failing tests for sync_mode declaration parity** - `29be614`
2. **Task 1 GREEN: narrow declaration, sweep every doc** - `2184f51`
3. **Task 2 RED: failing tests for check_sync_mode_value** - `a182cfb`
4. **Task 2 GREEN: check_sync_mode_value wired at plan:pre** - `804a662`

**Plan metadata:** committed separately after this SUMMARY.

## Files Created/Modified
- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` - `beads.sync_mode.values`
  narrowed to two entries, `description` rewritten
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` - `SYNC_MODE_VALUES`,
  `_sanitize_notice_value`, `check_sync_mode_value`, wired into `lifecycle_dispatch`'s `plan:pre`
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` -
  `TestSyncModeDeclarationParity`, `TestSyncModeAdjacencyAndEncoding`, `TestCheckSyncModeValue`
  (24 new test methods total), `TestLifecycleDispatchRouting`'s plan:pre routing test extended
  to a third diagnostic
- `CHANGELOG.md` - new 0.4.0 `### Changed` section (declaration narrowing, D-04 Case 1 and
  Case 2), 0.3.1 Performance/Known-issues corrections, 0.3.0 stale cross-reference fix
- `README.md`, `docs/prd-beads-capability.md`,
  `plugins/beads-lifecycle/.agents/skills/beads/PRIME.md` - every remaining false claim about the
  key corrected
- `.gsd-capabilities.json` - `updatedAt` bump, the hook-regenerated byproduct of re-syncing the
  project-scope runtime overlay to the narrowed declaration (`capability update beads --scope
  project`), required so `gsd-tools config-set` validates against the true declaration

## Decisions Made
- Implemented CONTEXT.md's chosen option (d) from the plan's Alternatives Considered table: keep
  the key, retire `off`, make `mirror` real -- not narrow-only and not implement-both. See
  key-decisions in frontmatter for the full D-04 Case 1/Case 2 split.
- Split each task into its own RED-then-GREEN commit pair (4 commits for 2 tasks), matching
  17-02's precedent for this repo's mandatory TDD discipline (`workflow.tdd_mode: true`).
  Genuine RED was proven by temporarily reverting the single file each task's tests depend on
  (`capability.json` for Task 1, `sync.py` for Task 2) to its pre-plan `HEAD` content via
  `git show HEAD:<path> > <path>`, confirming the new tests failed (2/3 parity tests failed on
  the old 3-value declaration; all 18 `TestCheckSyncModeValue` tests failed with `AttributeError`
  on the pre-Task-2 `sync.py`), then restoring the edited content before staging the RED commit
  -- so the RED commit's own tree (test file staged, dependency file still at its prior committed
  content) is genuinely red if checked out and run.

## Deviations from Plan

None - plan executed exactly as written, including every BINDING cross-AI review disposition from
`17-REVIEWS.md` (the presence-vs-effective-value membership test, the non-string-value notice
decision, the `repr()`-after-sanitization rendering, and the "execution continues under
authoritative" notice/CHANGELOG wording).

## Issues Encountered

The local development machine's `capability.json` overlay is installed at **global** scope
(`~/.gsd/capabilities/beads/`), not project scope -- a live CLI verification (`gsd-tools
config-set beads.sync_mode bogus`) against a scratch project with no `.gsd/capabilities/` of its
own falls back to that global copy, and `gsd-tools capability update beads` (no `--scope` flag)
reports `"upgraded"` for an equal-version (`0.4.0` -> `0.4.0`) no-op and copies nothing -- the
same stale-copy pitfall STATE.md records for the project-scope overlay. Resolved by running
`gsd-tools capability install ./plugins/beads-lifecycle/.gsd/capabilities/beads --scope global
--yes` (force-reinstall, not `update`) before the live CLI check; the project-scope overlay this
plan's own precondition governs (`.gsd/capabilities/beads/`) was kept in sync throughout via
`capability update beads --scope project`, verified `diff -rq` silent after every edit. Not a
plan deviation -- a machine-local verification detail, recorded here for the next plan that needs
a live `config-set` check on this machine.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 17-04 (TRUTH-02, a checkpoint plan). This plan's scope (TRUTH-01) is closed: ROADMAP.md
Phase 17 Success Criteria 1, 2, and 3 are all met by the coverage above.

## Self-Check: PASSED

- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py (SYNC_MODE_VALUES, _sanitize_notice_value, check_sync_mode_value)
- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py (TestSyncModeDeclarationParity, TestSyncModeAdjacencyAndEncoding, TestCheckSyncModeValue)
- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json (beads.sync_mode.values narrowed)
- FOUND commit 29be614 (Task 1 RED)
- FOUND commit 2184f51 (Task 1 GREEN)
- FOUND commit a182cfb (Task 2 RED)
- FOUND commit 804a662 (Task 2 GREEN)

---
*Phase: 17-config-code-truth*
*Completed: 2026-08-20*
