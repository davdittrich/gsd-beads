---
phase: 03-enforcement
fixed_at: 2026-08-15T18:10:00Z
review_path: .planning/phases/03-enforcement/03-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 3: Code Review Fix Report

**Fixed at:** 2026-08-15T18:10:00Z
**Source review:** .planning/phases/03-enforcement/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (fix_scope: critical_warning -- 1 critical + 4 warnings; IN-01/IN-02 excluded)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: `check_shipmd_patch`'s self-check cannot fire in the scenario it exists to detect

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`, `.gsd/capabilities/beads/skills/beads-recall/SKILL.md`, `.gsd/capabilities/beads/skills/beads-status/SKILL.md`, `.gsd/capabilities/beads/GSD-CORE-PATCH.md`
**Commit:** `eee6db7` (combined with WR-03 -- see note below)
**Applied fix:** Implemented the review's Option 1: added a new independent call site. `beads-recall/SKILL.md` gained Step 3.5, which runs `sync.py check-shipmd-patch` at `plan:pre` -- a lifecycle point dispatched by gsd-core's own **native** generic step-dispatch loop (the same kind `ship:post` already has), entirely independent of the patched `ship:pre` dispatch loop. `beads-status/SKILL.md`'s Step 2d and `GSD-CORE-PATCH.md` were updated to document that Step 2d is now a *confirmation* (runs immediately before a ship attempt) while Step 3.5 is the actual *detector* (fires even when the patch itself has been silently stripped by a `gsd-core` update or capability reinstall).

**Verification of reachability break (per explicit instruction):** traced the failure scenario end to end -- `plan:pre` is registered in `capability.json` for `beads-recall`, and that skill's dispatch does not depend on anything `GSD-CORE-PATCH.md`'s patch installs (the patch only touches `ship.md`'s `ship:pre` `preflight_checks` step). If a `gsd-core` update strips the patch, `beads-recall`'s Step 3.5 still runs on the next `/gsd-plan-phase` invocation and still calls `check-shipmd-patch`, which still detects the missing marker and prints the "⚠" warning -- unlike Step 2d, which is gated behind the very dispatch loop being verified. Confirmed by reading `capability.json`'s `steps[]` array (plan:pre / beads-recall vs ship:pre / beads-status) and `GSD-CORE-PATCH.md`'s own stated motivation (ship.md previously had *no* generic `kind == "step"` enumeration at `ship:pre`, unlike other lifecycle points).

### WR-01: `_render_beads_md_table` skips escaping that `_render_issue_table` applies, and the result is re-parsed into a subagent prompt

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`, `.gsd/capabilities/beads/tests/test_sync.py`
**Commit:** `ceea964`
**Applied fix:** Escaped `issue_id` and the `blocked_by` cell via the existing `_escape_table_cell`, matching `_render_issue_table`. Kept the `task_status_by_id`/`ordinal_map` lookups keyed on the raw (unescaped) id -- escaping `issue_id` for display only would otherwise have silently broken those two lookups (both dicts are built from bd's own unescaped ids elsewhere), a corruption the review's literal patch would have introduced.

**Deviation from the review's literal suggestion (verified, not assumed):** the review's Fix section claimed escaping alone made `_parse_beads_md_table_rows`'s cell values "guaranteed-pipe-free," so no parser change was needed. Empirically this is false: `_escape_table_cell` replaces `|` with `\|`, which still contains a raw `|` byte -- I reproduced the exact column-shift the finding describes (`sync._parse_beads_md_table_rows` returned `{'id': 'evil\\', 'title': 'id', ...}` for an id `evil|id` even after escaping). Fixed `_parse_beads_md_table_rows` to split on an unescaped `|` only (negative-lookbehind regex `CELL_SPLIT_RE`) and un-escape `\|` -> `|` per cell, which correctly recovers `{'id': 'evil|id', 'title': 'safe title', 'status': 'open'}`. Verified with a direct probe script before and after, plus new unit tests.

### WR-02: Stale `beads_epic` fallback is silent -- unlike the analogous stale-task-id path

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`, `.gsd/capabilities/beads/tests/test_sync.py`
**Commit:** `d6acb6d`
**Applied fix:** `resolve_epic` now returns `(epic_id, needs_write, stale_epic_id)` -- `stale_epic_id` carries the frontmatter's own `beads_epic` value whenever it fails to resolve in `bd`, `None` otherwise (including when it fell through and `resolve_phase_epic` supplied a still-valid replacement, so the divergence is reported even when a working shared epic was reused rather than a fresh one created). `create_issues` prints `divergence: stored beads_epic 'X' not found in bd -- resolving to a replacement epic`, matching D-07's existing task-level pattern.

### WR-03: `check_shipmd_patch`'s default path ignores the multi-runtime resolution `ship.md` itself uses

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`
**Commit:** `eee6db7` (combined with CR-01 -- see note below)
**Applied fix:** Implemented the review's minimal Option (b): every message (`present`, `missing at ship:pre`, `not found`) now names the exact `ship_md_path` checked and states that other runtime homes (`CODEX_HOME`, `CURSOR_CONFIG_DIR`, etc.) were not probed. Did not implement Option (a) (factoring `ship.md`'s bash-embedded 18-way runtime resolution into a shared lookup callable from Python) -- `GSD-CORE-PATCH.md`'s patch is itself explicitly scoped to the Claude runtime only, so replicating full multi-runtime detection here would check a location the patch was never applied to; naming the checked path is the proportionate fix until the patch itself is generalized.

### WR-04: `parse_depends_on` silently drops multi-line YAML `depends_on:` lists

**Files modified:** `.gsd/capabilities/beads/scripts/sync.py`, `.gsd/capabilities/beads/tests/test_sync.py`
**Commit:** `11d6d51`
**Applied fix:** Added `DEPENDS_ON_BLOCK_RE` (as the review suggested) as a fallback when the inline-bracket `DEPENDS_ON_RE` doesn't match, and extended `parse_depends_on` to parse block-list items (stripping `-`, quotes, whitespace). Added three test cases: multi-item block list, single unquoted item, and confirmation that a wholly absent `depends_on` key still returns `[]`.

**Note on CR-01/WR-03 commit consolidation:** both findings modify the same function (`check_shipmd_patch`) in the same file in immediately adjacent lines (its docstring and its three `print()` call sites) -- they could not be split into two commits without interactive hunk-level surgery of a single already-merged docstring paragraph. They are committed together as `eee6db7`; each finding's actual code change is called out separately above and both are independently verifiable in that commit's diff.

## Skipped Issues

None -- all 5 in-scope findings were fixed.

## Notes for the developer

- **IN-01/IN-02** were out of `fix_scope` (`critical_warning`) and left untouched, per the review: `filter_open_ids`'s hardcoded status string duplicating `BEADS_RECALL_STATUSES`, and `BD_TIMEOUT` being reused for the unrelated `git commit --amend` call in `ship_override`.
- **Pre-existing latent bug found while verifying WR-02, not fixed (out of REVIEW.md's scope):** `rewrite_plan` unconditionally prepends a new `beads_epic:` line whenever `epic_created=True`, without first removing a stale one already present in frontmatter. In the stale-epic-replacement path this fix adds test coverage for, the plan file ends up with two `beads_epic:` lines (the new one first, so `BEADS_EPIC_RE.search` -- and therefore every real caller -- still resolves correctly, which is why this was not treated as a regression blocking the fix). Worth a follow-up ticket to strip the old line during rewrite.
- **Pre-existing test flakiness observed, not caused by this session's changes:** `TestShipPreGenericDispatch`'s three live `gsd-tools.cjs` subprocess tests fail intermittently when run in-place inside this active repo (`ENOENT: process.cwd failed ... the current working directory was likely removed`), but pass when the same baseline `sync.py`/`test_sync.py` pair (checked out from commit `5e1ee91`, pre-dating this session) are run from an isolated scratch copy. This points to a cwd race from something else running concurrently in this session's environment (background scheduled tasks / other worktrees), not to any of the four fix commits above -- confirmed by running the identical test class against both the pre-fix and post-fix `sync.py` with the same result.

---

_Fixed: 2026-08-15T18:10:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
