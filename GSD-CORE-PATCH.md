# Local gsd-core patch (machine-local)

The one patch this capability carries to an installed gsd-core workflow file, `ship.md`. The patched file is outside this repository's history; this file holds the reapply source.

## Scope: why only `ship.md` is patched

Which mechanism dispatches each lifecycle point is in README, "How the lifecycle steps get dispatched". `ship:pre` is the one point that still needs a patch: it stays out of the `PostToolUse` hook's point list because it already dispatches through Patch 1, and the hook would double-record a `ship_override`.

## Patch 1: `ship.md` — `ship:pre` generic gate/step dispatch

**Target file:** `$HOME/.claude/gsd-core/workflows/ship.md` — machine-local, shared across
every gsd-core project on this machine.

### Why this patch exists

gsd-core's `ship.md` `preflight_checks` has no generic loop over `gsd_run loop render-hooks ship:pre --raw`'s `activeHooks` for `kind == "step"` entries (unlike `ship:post`'s `ship_post_capability_dispatch`), and no upstream issue tracks it. Without the patch a real `/gsd-ship` run never dispatches `beads-status`'s `ship:pre` step, so `ship_override` recording and the `check-patch` diagnostic never run. The project's "no fork/patch to gsd-core" constraint was overridden on 2026-08-15 for this one file.

### Upstream status and revert condition

The `ship:pre` **gate** half is upstream: open-gsd/gsd-core#3559 (PR #3608), shipped in gsd-core v1.11.0, so v2 of the patch carries only the **step** half. A machine still carrying the v1 marker runs a redundant gate loop; `check_patch` reporting "missing" is the signal to reapply v2.

Revert: once gsd-core ships a native generic `ship:pre` step dispatch, delete this patch, `check_patch`'s `ship-md` target, `beads-status` Step 2d, and `beads-recall` Step 3.5.

### Patch-loss detection

`beads-status` Step 2d runs `check-patch ship-md` at `ship:pre`, a call site reachable only through the dispatch loop this patch installs: it confirms an intact patch and cannot detect a lost one. The detector is `beads-recall` Step 3.5, the same call at `plan:pre`, dispatched by `hooks/lifecycle-dispatch.sh` independently of this patch.

### Insertion anchor

Inside `preflight_checks`, immediately after step 6's final line (ending `"...continue to the next preflight check."`) and before the step's closing `</step>`. The added step is numbered **7**, continuing gsd-core 1.11.0's 1-6 list.

### Patch marker

```
<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->
<!-- /gsd-beads-patch:ship-pre-generic-dispatch v2 -->
```

`sync.py`'s `check_patch` checks for the opening marker string's presence in the live
`ship.md` to detect whether this patch survived a `gsd-core` update or capability reinstall —
both of which can silently overwrite `ship.md` and drop the patch with no error.

### Patch Content (verbatim)

The fenced block below is byte-for-byte identical to the text between the two markers in the live
`$HOME/.claude/gsd-core/workflows/ship.md`. If a future `gsd-core` update or reinstall strips the
patch, paste this block back in at the anchor above.

````markdown
<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->
7. **Generic `ship:pre` step dispatch (capability-driven).** This runs here — before
   `push_branch` — specifically so a step that amends the not-yet-pushed HEAD commit (e.g. an
   override-audit trailer) lands before the push.

   `SHIP_PRE_HOOKS_JSON` (resolved in step 6) carries every active `ship:pre` entry, not only
   gates. Step 6 above enforces the `kind == "gate"` entries and explicitly ignores every other
   kind; this step handles `kind == "step"`, which gsd-core has no native dispatch for at
   `ship:pre` (unlike `ship:post`, which does).

   For each active `SHIP_PRE_HOOKS_JSON` entry where `kind == "step"`: honor `consumes` exactly as
   `ship_post_capability_dispatch` already does below — resolve `ls "${PHASE_DIR}"/*-<name>
   2>/dev/null | head -1` per consumed name; if any consumed artifact is absent, skip that hook
   entirely.

   - If `ref.agent` is set, dispatch is identical to `ship:post`'s "Generic step hook dispatch
     contract" below (spawn banner, runtime-aware dispatch, #2684 model resolution, and the
     input-validation rule against `^[A-Za-z0-9][A-Za-z0-9._-]*$`), substituting ship:pre banner
     wording — see that section by name rather than duplicating it here.
   - If `ref.skill` is set, dispatch with `Skill(skill="gsd-${hook.ref.skill}", args="${PHASE_NUMBER}
     --auto ${GSD_WS}")`.

   Each dispatch is best-effort (`onError: "skip"` — the only value the beads-status entry
   declares): a failure is recorded as a warning and preflight continues, never re-raised.

   If `activeHooks` has no `kind == "step"` entry, skip this step silently.
<!-- /gsd-beads-patch:ship-pre-generic-dispatch v2 -->
````

## Probe (not a patch): native step dispatch (PR #3687)

open-gsd/gsd-core#3687 adds native `kind == "step"` dispatch at `plan:post` and `verify:post` (merged to `next` after the v1.11.0 cut). `sync.py`'s `check_native_step_dispatch` reads the installed `plan-phase.md` or `verify-work.md`, never edits it, and stands the hook down at those two points when the point's own `render-hooks <point> --raw` region (to the next non-fenced `##` heading, at most 120 lines) holds an unqualified `kind == "step"` line. Lines carrying a `capId ==` or `ref.skill ==` qualifier do not count, and a whole-file scan is wrong: both shipped 1.11.0 files hold unrelated `kind == "step"` mentions.

Every miss (unmapped point, missing or unreadable file, no anchor, no qualifying line) returns not-detected, which degrades to a harmless double dispatch. `execute:wave:pre`, `execute:wave:post` and `plan:pre` are never probed: no upstream work covers them.

Revert: once a released gsd-core is detected at both `plan:post` and `verify:post`, retire the gate branches in `lifecycle_dispatch`, `check_native_step_dispatch`, and `NATIVE_STEP_DISPATCH_WORKFLOW_FILES`. The hook stays for the three uncovered points.
