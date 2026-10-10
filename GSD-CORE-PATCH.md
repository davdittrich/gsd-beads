# Local gsd-core patches (machine-local, this project)

A register of the local, marker-bracketed patch this machine carries to an installed
`gsd-core` workflow file. The patched file is not part of this repository's git history (the
`beads` capability's own files, listed in `PROJECT.md`'s Constraints as the only in-repo
artifacts, do not include it). The section below documents six parts: the
targeted file, why the patch exists and which PROJECT.md constraint override permits it,
upstream tracking plus an explicit revert condition, the patch-loss-detection independence
argument, the insertion anchor stated in prose, and the marker pair with verbatim content for
reapplication.

## Scope: why only `ship.md` remains patched

`capability.json` declares six `kind: "step"` hooks and gsd-core 1.11.0 still has no generic
`kind == "step"` dispatch at five of those points (gh-2). That is the same defect Patch 1 below
was written for, at four more call sites — `plan-phase.md`'s §13e (`plan:post`, gate-only) and
§5.6 (`plan:pre`, behind an auto-chain + frontend-detection branch), and `execute-phase.md`'s
2.75 (`execute:wave:pre`, contribution-only), 5.75 (`execute:wave:post`, gate-only) and its
`verify:post` step loop (hardcoded to `ref.skill == "secure-phase"`).

**Those four are deliberately NOT patched.** They are dispatched instead by
`hooks/lifecycle-dispatch.sh`, a `PostToolUse` hook matching the
`gsd_run loop render-hooks <point> --raw` call gsd-core makes at each of them, which runs
`sync.py lifecycle-dispatch <point>` directly. Three reasons that mechanism was chosen over four
more patches:

1. **Dispatch stops depending on prose.** A marker-bracketed patch is a paragraph a model has to
   read and obey inside a workflow file. The hook is a script the harness runs.
2. **It cannot be silently dropped.** Its trigger is a call gsd-core must keep making for its own
   hook system to work at all, so there is nothing for a gsd-core update to strip — which is what
   the patch-loss machinery below exists to detect, imperfectly.
3. **The detector's own independence argument was false.** Patch 1 below names
   `beads-recall`'s Step 3.5 at `plan:pre` as the loss detector *because `plan:pre` is natively
   dispatched*. It is not, for a manual `/gsd:plan-phase` — so the detector shared the failure
   mode of the thing it protects. Step 3.5 now runs from the hook, which restores the
   independence the argument assumed.

`ship:pre` still needs Patch 1 and is deliberately excluded from the hook's point list: it
already dispatches through that patch, and adding it would double-record a `ship_override`.
## Patch 1: `ship.md` — `ship:pre` generic gate/step dispatch

**Target file:** `$HOME/.claude/gsd-core/workflows/ship.md` — machine-local, shared across
every gsd-core project on this machine.

### Why this patch exists

This project's N2 constraint ("no fork/patch to gsd-core — raise a core change upstream
first") was **overridden 2026-08-15** (user decision, Phase 3 planning; see
`.planning/PROJECT.md` Constraints, "Overridden 2026-08-15" entry) specifically for this one
file. The installed `ship.md`'s `preflight_checks` step hardcodes `ship:pre` gate/step
dispatch to `capId == "security"` and `capId == "broken-windows"` only — there is no generic
enumeration loop over `gsd_run loop render-hooks ship:pre --raw`'s `activeHooks`, unlike
`ship:post`'s `ship_post_capability_dispatch` step, which already dispatches any active
`kind == "step"` hook generically.

Without this patch, `03-01`'s real `blocking_open`/`diverged` `BEADS.md` fields and `03-02`'s
declared `ship:pre` `gates[]`/`ship_override` primitive are schema-valid but **inert** — a real
`/gsd-ship` run never evaluates them, silently making ROADMAP.md's Phase 3 Success Criteria 1
and 2 false at ship time regardless of how correct Plan 01/02's own code is.

### Upstream tracking + revert condition

**Corrected 2026-08-19.** This section previously cited **open-gsd/gsd-core#3554** as the live
upstream track. It is not: #3554 was closed **NOT_PLANNED** on 2026-08-15 *"on the form, not the
merits"* — filed without the repository's issue template. The properly-filed version is
**open-gsd/gsd-core#3559**, which was closed **COMPLETED** on 2026-08-18 by **PR #3608**
(`fix(#3559): dispatch every ship:pre capability gate, not two hardcoded capIds`) and shipped in
**gsd-core v1.11.0**.

**The revert condition has therefore half-fired, and this patch was trimmed accordingly (v1 → v2).**

| Half of the v1 patch | Status on gsd-core >= 1.11.0 |
|---|---|
| step 8 — generic `ship:pre` **gate** dispatch | **Upstream.** `ship.md` preflight step 6 now carries an "Every other `capId`" arm. **Deleted from this patch; not reapplied.** |
| step 9 — generic `ship:pre` **step** dispatch | **Still required.** PR #3608 added no step dispatch anywhere — verified: every `kind == "step"` occurrence in 1.11.0's `ship.md` belongs to `ship:post`. Reapplied as the whole of v2. |

**Remaining revert condition:** once gsd-core ships a native generic `ship:pre` **step** dispatch
loop (the same kind `ship:post` already has), this patch — the marker-bracketed block below, this
section, `sync.py`'s `check_shipmd_patch`, `beads-status/SKILL.md`'s Step 2d, and
`beads-recall/SKILL.md`'s Step 3.5 — becomes unnecessary and should be deleted, not kept as
permanent duplication. No upstream issue currently tracks that remaining half.

**Marker version bumped to `v2` deliberately.** A machine still carrying the v1 marker is running
a redundant gate loop alongside 1.11.0's native one; `check_shipmd_patch` reporting "missing" is
the signal to reapply the trimmed v2, not a false alarm.

### Patch-loss detection is independent of the patch itself (CR-01, 03-03 code review)

`beads-status/SKILL.md`'s Step 2d runs `check-patch ship-md` at `ship:pre`, but that call site is
itself only reachable through the dispatch loop this patch installs — if a `gsd-core` update or
capability reinstall silently strips the patch, Step 2d never runs either, so it *confirms* an
intact patch immediately before a ship attempt but cannot *detect* a lost one. The actual detector
is `beads-recall/SKILL.md`'s new Step 3.5, which runs the identical `check-patch ship-md` call at
`plan:pre` — a lifecycle point dispatched by gsd-core's own native generic step-dispatch loop
(the same kind of loop `ship:post` already has and `ship:pre` lacked before this patch), not by
anything this patch installs. That independence is what makes Step 3.5 fire even when this patch
has been silently dropped.

### Insertion anchor

The patch is inserted inside `preflight_checks`, immediately after step 6's (capability ship
gates, generic dispatch) final line — the line ending `"...continue to the next preflight
check."` — and before the step's closing `</step>` tag. The step it adds is numbered **7**,
continuing gsd-core 1.11.0's existing 1–6 numbered list.

Note the renumber: under gsd-core 1.10.0 this patch added steps **8 and 9** after that version's
step 7 (broken-windows). 1.11.0 folded security and broken-windows into a single generic step 6,
and absorbed this patch's old step 8 outright, so only the step-dispatch half remains and it now
lands as step 7.

### Patch marker

```
<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->
<!-- /gsd-beads-patch:ship-pre-generic-dispatch v2 -->
```

`sync.py`'s `check_shipmd_patch` checks for the opening marker string's presence in the live
`ship.md` to detect whether this patch survived a `gsd-core` update or capability reinstall —
both of which can silently overwrite `ship.md` and drop the patch with no error. The v1.11.0
upgrade did exactly that, which is how this trim was discovered.

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

## Probe (not a patch): native `kind == "step"` dispatch detection (PR #3687)

**Target files (read-only):** `$HOME/.claude/gsd-core/workflows/plan-phase.md` and
`$HOME/.claude/gsd-core/workflows/verify-work.md` — machine-local, shared across every gsd-core
project on this machine. Unlike Patch 1 above, this mechanism never edits either file; it
only reads them. There is no marker to insert and nothing to reapply after an update.

### Why this exists

**open-gsd/gsd-core#3687** (<https://github.com/open-gsd/gsd-core/pull/3687>) merged to `next` on
2026-08-19T20:41:28Z — 6h50m after the v1.11.0 release cut, so it is unreleased today and lands at
the next cut. It adds native generic `kind == "step"` dispatch at **`plan:post`** and
**`verify:post`** only. Once that release ships, `lifecycle_dispatch`'s existing unconditional
dispatch at those two points would double-dispatch alongside gsd-core's own native loop, and
(before 17-02 Task 3's D-06 wiring) risked silently bypassing the hook's deliberate
`allow_strip=False` protection at `plan:post` if the native path were ever reached with a weaker
principal than the one it actually uses. `sync.py`'s `check_native_step_dispatch(point,
workflow_path_override=None)` closes the double-dispatch half: it reads the installed workflow
file the point maps onto, scopes its search to that point's own `render-hooks <point> --raw`
region (never a whole-file scan — see below), and reports whether a generic, unqualified `kind ==
"step"` arm already exists there.

**`execute:wave:pre` and `execute:wave:post` are deliberately NOT gated by this probe and never
will be by this same mechanism.** No upstream work — released, merged, or in an open PR anywhere —
covers either point. Gating them would risk disabling the hook's only working dispatch path there
with nothing behind it. `plan:pre` is likewise ungated: PR #3687 does not touch it.

**Why region-scoped, not whole-file.** A whole-file `kind == "step"` grep is a *verified* false
positive on both shipped 1.11.0 workflow files: `plan-phase.md` carries three such mentions
outside the `plan:post` region (the plan:pre generic dispatch contract, the auto-chain UI step
branch, and the intel step read), and `verify-work.md`'s own `verify:post` region already carries
one, qualified to `ref.skill == "secure-phase"`. A whole-file scan would misreport "native dispatch
present" on an install that has none of it at `plan:post`/`verify:post`, causing the hook to stand
down and the sync to be silently missed — the one failure direction D-05 forbids. The probe
therefore anchors on the point's own `render-hooks <point> --raw` call, scopes to the region ending
at the earlier of the next non-fenced level-two heading or 120 lines past the anchor (fence
awareness matters: `verify-work.md` prints heading-shaped lines inside fenced output templates),
and excludes any `kind == "step"` line that also carries a `capId ==` or `ref.skill ==` qualifier
on the same line.

### Fail-open contract

Every miss — an unmapped point, a missing workflow file, an unreadable workflow file, no anchor
found, or no qualifying line in the region — returns not-detected (0), which degrades to today's
working double dispatch: the only acceptable failure direction. `check_native_step_dispatch` never
raises; a raise from inside it (a stubbed test double, or an unforeseen filesystem error) is still
caught by `lifecycle_dispatch`'s own outer `except Exception`, so the hook keeps its
`onError: "skip"` contract regardless.

### Revert condition

When `check_native_step_dispatch` reports detected on a **released** gsd-core for **both**
`plan:post` and `verify:post`, the corresponding gate branches in `lifecycle_dispatch` (and this
probe function, `check_native_step_dispatch`, and its `NATIVE_STEP_DISPATCH_WORKFLOW_FILES`
mapping) can be retired. The hook itself cannot be deleted while `execute:wave:pre` and
`execute:wave:post` remain uncovered by any upstream mechanism — retiring the probe only removes
the now-redundant double-dispatch guard at the two points PR #3687 covers, not the hook's other
three dispatch points.
