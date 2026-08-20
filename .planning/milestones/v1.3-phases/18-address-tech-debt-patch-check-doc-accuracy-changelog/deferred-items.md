# Deferred Items — Phase 18

## From plan 18-03, Task 3

**gsd-beads-2e2** — `hooks/lifecycle-dispatch.sh` `PLUGIN_ROOT` resolution breaks when
`plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`'s suite runs from the
gitignored runtime overlay (`.gsd/capabilities/beads/`) instead of the git-tracked plugin tree.

Three test classes (`TestLifecycleDispatchHook`, `TestShipPreGenericDispatch`,
`TestLifecycleDispatchPointsAgreeWithHook`) compute
`PLUGIN_ROOT = Path(__file__).resolve().parents[4]` to locate `hooks/lifecycle-dispatch.sh`. That
fixed-depth traversal is correct from the plugin tree (`parents[4]` lands on
`plugins/beads-lifecycle/`, which has a `hooks/` sibling) but wrong from the overlay
(`parents[4]` lands on the repo worktree root, which has no `hooks/` belonging to this
capability — `hooks/` is never vendored into `.gsd/capabilities/beads/`, only the capability
subtree is).

**Out of scope for 18-03** — Task 3's declared `<files>` is `.gsd-capabilities.json` only; fixing
this would mean editing `test_sync.py` (not this task's file) or changing what the capability
vendors into the overlay (an architectural change to the vendoring manifest). Not caused by
18-03's Task 1/2 edits — the three failing classes are gh-2/17-02 vintage, untouched by this
plan's `PATCH_CHECKS`/docstring changes.

Observed 2026-08-20: `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/`
is byte-silent (file contents are identical between the two trees) — this is a path-resolution
bug in the tests, not a content-sync bug. Plugin-tree run: `Ran 252 tests`, `OK`. Overlay-tree
run: `Ran 252 tests`, `FAILED (failures=12, errors=2)`, all 14 in the three `PLUGIN_ROOT`-dependent
classes.

Fix direction (ticketed, not implemented here): either vendor `hooks/lifecycle-dispatch.sh` into
the overlay under `capability.json`'s manifest, or make `PLUGIN_ROOT` resolution robust to the
overlay's shallower ancestor chain (search upward for `hooks/lifecycle-dispatch.sh` rather than a
fixed `parents[4]` depth).
