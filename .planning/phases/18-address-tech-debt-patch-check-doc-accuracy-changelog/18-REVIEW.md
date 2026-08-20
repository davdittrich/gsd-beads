---
phase: 18-address-tech-debt-patch-check-doc-accuracy-changelog
reviewed: 2026-08-20T11:18:17Z
depth: deep
files_reviewed: 10
files_reviewed_list:
  - .gsd-capabilities.json
  - .planning/WINDOWS.md
  - .planning/phases/18-address-tech-debt-patch-check-doc-accuracy-changelog/deferred-items.md
  - CHANGELOG.md
  - plugins/beads-lifecycle/.claude-plugin/plugin.json
  - plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-08-20T11:18:17Z
**Depth:** deep
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Phase 18 is a narrow, documentation/messaging-accuracy phase: `sync.py`'s functional diff
(vs. `ae8ce6c`) is limited to adding a leading `⚠ ` marker to four previously-unmarked
`PATCH_CHECKS` message templates and updating comments/docstrings; no control flow, regex,
or data-handling logic changed. `beads-recall/SKILL.md` and `beads-status/SKILL.md` were
updated in lockstep to key their surfacing rule on `check-patch`'s exit code / the substring
`"present"` rather than the `⚠` glyph, `GSD-CORE-PATCH.md` gained a new "Reapply verification"
section, `CHANGELOG.md` gained/moved several 0.4.0 entries, and `plugin.json`/
`.gsd-capabilities.json` had version/timestamp bumps only. Four new tests were added to
`TestPatchChecksTable` covering the four newly-marked templates.

I traced every changed message template against `check_patch`'s actual control flow, confirmed
programmatically that the word `"present"` appears in `present_msg` and in no other message
template (i.e. the SKILL.md instructions' `"present"`-substring heuristic cannot false-positive
or false-negative against any current template), ran the full `test_sync.py` suite from the
tracked plugin tree (252/252, `OK`), and independently reproduced the overlay-tree run
(`.gsd/capabilities/beads/`) to confirm the `deferred-items.md`/`WINDOWS.md` claim of
`failures=12, errors=2` (14/252) — both match exactly. I did not find any newly-introduced
correctness or security defect. The one finding below is a documentation/bookkeeping hygiene
issue in `WINDOWS.md`, not a functional bug, plus two minor informational notes.

## Warnings

### WR-01: `WINDOWS.md` entries 3 and 4 describe the same root-cause defect without cross-referencing each other

**File:** `.planning/WINDOWS.md:20-21`
**Issue:** Entry 3 (phase 17, `kind: deviation`, recorded 2026-08-19) and entry 4 (phase 18,
`kind: unmet-truth`, recorded 2026-08-20, added by this phase) both describe the identical
`PLUGIN_ROOT = Path(__file__).resolve().parents[4]` fixed-depth-traversal defect in
`test_sync.py` (`TestLifecycleDispatchHook`, and — per entry 3 — `TestShipPreGenericDispatch`;
entry 4 additionally names `TestLifecycleDispatchPointsAgreeWithHook`, confirmed by inspection to
also depend on `TestLifecycleDispatchHook.PLUGIN_ROOT` via its `HOOK` class attribute). Entry 4
is more precise (exact `failures=12, errors=2` count, live ticket `gsd-beads-2e2`) but neither
entry points at the other. Entry 3 additionally covers a second, distinct defect
(`TestShipPreGenericDispatch`'s capability-reinstall side effect deleting the process's own cwd)
that entry 4 does not, so entry 3 cannot simply be deleted or merged wholesale — but as written, a
future maintainer resolving `gsd-beads-2e2` and marking entry 4 fixed has no signal that entry 3's
`PLUGIN_ROOT` portion is the same underlying bug and should be checked/closed too (or vice versa).
I confirmed this by running both the plugin-tree suite (`Ran 252 tests`, `OK`) and the overlay-tree
suite (`Ran 252 tests`, `FAILED (failures=12, errors=2)`) directly — the failure signature matches
`deferred-items.md`'s claim exactly, so the underlying defect description is accurate; this finding
is about ledger cross-referencing, not defect accuracy.
**Fix:** Add a one-line cross-reference in entry 3's description (e.g. "PLUGIN_ROOT portion of this
entry is tracked precisely by entry 4 / `gsd-beads-2e2`; the capability-reinstall cwd-deletion
defect remains open here only"), or split entry 3 into two rows (one per distinct defect) so each
can be waived/fixed independently without ambiguity.

## Info

### IN-01: Overlay-tree `test_sync.py` failures are pre-existing, correctly diagnosed, and out of this phase's declared scope

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
**Issue:** Not a new finding — recording verification only, since the phase's stated goal
includes doc/truth accuracy. `TestLifecycleDispatchHook`, `TestShipPreGenericDispatch`, and
`TestLifecycleDispatchPointsAgreeWithHook` all compute
`PLUGIN_ROOT = Path(__file__).resolve().parents[4]`, which resolves correctly from the git-tracked
plugin tree (`plugins/beads-lifecycle/`) but resolves to the repo worktree root — one level too
shallow — when the identical file is executed from the gitignored runtime overlay
(`.gsd/capabilities/beads/`), which is what `hooks/lifecycle-dispatch.sh` actually executes at
runtime. I independently reproduced both runs: plugin tree `Ran 252 tests` / `OK`; overlay tree
`Ran 252 tests` / `FAILED (failures=12, errors=2)`, with the two `ERROR`s falling exactly in
`TestLifecycleDispatchHook.test_point_list_matches_sync_py_and_capability_json` and
`TestLifecycleDispatchPointsAgreeWithHook.test_five_points_same_order_in_both_places` — matching
`deferred-items.md`'s claim precisely. `18-03-PLAN.md` Task 3's declared `<files>` is
`.gsd-capabilities.json` only, confirmed by direct read, so fixing `test_sync.py`'s path resolution
was correctly out of scope for this task and is correctly deferred/ticketed (`gsd-beads-2e2`)
rather than silently left undocumented.
**Fix:** No action needed within this phase; tracked by `gsd-beads-2e2` per `deferred-items.md`.

### IN-02: `⚠ `-marker addition is internally consistent but relies on an un-enforced invariant

**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:142-179`
**Issue:** `beads-recall/SKILL.md` and `beads-status/SKILL.md` now key their surfacing rule on
"exit code non-zero, or output does not contain the substring `present`" rather than the `⚠`
glyph — deliberately, per D-03.2, so a future template that forgets the marker still surfaces. I
verified programmatically that today's four failure-path templates (`not_found_msg`,
`could_not_read_msg`, `missing_msg` for both `ship-md` and `execute-plan`) contain no `"present"`
substring and both `present_msg` templates do. This correctness depends on an invariant
(`"present"` never appearing in a non-success template) that is enforced only by convention, not
by a test that would fail if a future edit accidentally introduced the substring "represents",
"presently", etc. into a failure-path message.
**Fix:** Optional hardening only — a test asserting `"present" not in entry[key]` for every
`PATCH_CHECKS` entry's `not_found_msg`/`could_not_read_msg`/`missing_msg`, alongside the existing
`⚠`-prefix tests, would pin this invariant explicitly rather than leaving it implicit.

---

_Reviewed: 2026-08-20T11:18:17Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
