# Local patch: `$HOME/.claude/gsd-core/workflows/ship.md`

**Target file:** `$HOME/.claude/gsd-core/workflows/ship.md` — machine-local, shared across
every gsd-core project on this machine (NOT part of this repository's git history; the
`beads` capability's own files, listed in `PROJECT.md`'s Constraints as the only
in-repo artifacts, do not include this file).

## Why this patch exists

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

## Upstream tracking + revert condition

Filed upstream as **open-gsd/gsd-core#3554** (generic `ship:pre` gate/step dispatch, natively).

**Revert condition:** once open-gsd/gsd-core#3554 ships a native generic `ship:pre` dispatch
loop, this local patch — the marker-bracketed block below, this file, `sync.py`'s
`check_shipmd_patch`, and `beads-status/SKILL.md`'s Step 2d — becomes unnecessary and should
be deleted, not kept as permanent duplication.

## Insertion anchor

The patch is inserted inside `preflight_checks`, immediately after step 7's (broken-windows
ship gate) final line — the line ending `"...skip this check silently."` — and immediately
before the step's closing `</step>` tag. The two steps this patch adds are numbered **8** and
**9**, continuing the existing 1–7 numbered list.

## Patch marker

```
<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->
<!-- /gsd-beads-patch:ship-pre-generic-dispatch v1 -->
```

`sync.py`'s `check_shipmd_patch` (03-03 Task 2) checks for the opening marker string's
presence in the live `ship.md` to detect whether this patch survived a `gsd-core` update or
capability reinstall — both of which can silently overwrite `ship.md` and drop the patch with
no error.

## Patch Content (verbatim)

The fenced block below is byte-for-byte identical to the text between the two markers in the
live `$HOME/.claude/gsd-core/workflows/ship.md`. If a future `gsd-core` update or reinstall
strips the patch, paste this block back in at the anchor above.

````markdown
<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->
8. **Generic `ship:pre` gate dispatch (capability-driven, beyond security/broken-windows).**

   `SHIP_PRE_HOOKS_JSON` (resolved in step 6) carries every active `ship:pre` gate, not only
   `security`/`broken-windows`. Inspect `activeHooks` in-context for every entry where `kind ==
   "gate"` and `capId` is neither `"security"` nor `"broken-windows"` (those two stay exclusively
   handled by steps 6/7 above — do NOT reprocess them here). For each such entry, in array order:

   **(a) Fail-open pre-check.** When `hook.check.predicate.kind == "artifact-frontmatter-equals"`
   and `hook.onError == "skip"`, resolve:

   ```bash
   MATCHED_ARTIFACT=$(ls "${PHASE_DIR}"/*-"${hook.check.predicate.artifact}" 2>/dev/null | head -1)
   ```

   (the same glob form `SECURITY_FILE` already uses at step 6). If `MATCHED_ARTIFACT` is empty,
   skip this gate entry entirely and move to the next active hook — do NOT call `gsd_run check
   predicate` for it. The generic evaluator's `artifact-frontmatter-equals` kind fails CLOSED
   (`block: true`, `artifactNotFound: true`) on a missing artifact by design — correct for an
   `onError: "halt"` gate like `security`'s own, but wrong for a capability that declared `onError:
   "skip"` specifically to mean "not yet computed, never block on it" (PROJECT.md's fail-open
   constraint). This one-line existence check preserves that promise generically, without naming
   any specific `capId`. A gate whose predicate kind is not `artifact-frontmatter-equals`, or whose
   `onError` is `"halt"`, skips this pre-check and goes straight to (b).

   **(b) Evaluate.** For a `check.query` gate:

   ```bash
   GATE_RESULT=$(gsd_run check ${hook.check.query} "${PHASE_NUMBER}" --raw)
   CHECK_EXIT=$?
   ```

   For a `check.predicate` gate:

   ```bash
   GATE_RESULT=$(gsd_run check predicate --predicate '<hook.check.predicate as JSON>' \
     --phase-dir "${PHASE_DIR}" --phase-number "${PHASE_NUMBER}" --raw)
   CHECK_EXIT=$?
   ```

   **(c) Two-step gate contract**, identical wording to `verify:pre`/`execute:wave:post`/
   `execute:post`:

   - **Step 1 — command failure:** non-zero `CHECK_EXIT`, empty output, or unparseable JSON routes
     by `hook.onError`. `onError == "halt"` blocks shipping with a command-error message: `⚠ Gate
     check command failed ({hook.capId}): command error. Resolve before continuing.` `onError ==
     "skip"` logs a warning and continues to the next hook — never reading `GATE_RESULT.block`.
   - **Step 2 — block evaluation** (only reached on command success): `hook.blocking == true` AND
     `GATE_RESULT.block == true` blocks shipping and presents:

     ```
     ⚠ Ship gate blocked ({hook.capId}): {GATE_RESULT.message}
     See {PHASE_DIR}/*-{hook.check.predicate.artifact} for detail (if the predicate is
     artifact-frontmatter-equals), or set {hook.when} to false in .planning/config.json to
     override, if this capability supports one and records it. Then re-run /gsd-ship.
     ```

     This halt is **not** bypassed by `onError` — `onError` governs step 1 only, never the gate's
     block decision. `hook.blocking == false` never halts; if `GATE_RESULT.block` is `true` print an
     advisory line `⚠ {hook.capId} advisory: {GATE_RESULT.message}` and continue. `hook.blocking ==
     true` AND `GATE_RESULT.block == false` continues silently.

   If `activeHooks` has no qualifying `kind == "gate"` entry after excluding `security`/
   `broken-windows`, skip step 8 silently.

9. **Generic `ship:pre` step dispatch (capability-driven).** This runs here — before
   `push_branch` — specifically so a step that amends the not-yet-pushed HEAD commit (e.g. an
   override-audit trailer) lands before the push.

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

   If `activeHooks` has no `kind == "step"` entry, skip step 9 silently.
<!-- /gsd-beads-patch:ship-pre-generic-dispatch v1 -->
````
