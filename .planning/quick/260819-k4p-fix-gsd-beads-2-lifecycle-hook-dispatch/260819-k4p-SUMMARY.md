---
quick_id: 260819-k4p
slug: fix-gsd-beads-2-lifecycle-hook-dispatch
date: 2026-08-19
status: complete
beads_epic: gsd-beads-l5k
github_issue: 2
commits:
  - 547111a
  - 6961eb8
  - ecf9004
  - 62162d4
  - 55855cd
  - 0c65d69
  - 049da5b
released: v1.3.1
---

# Summary: make the four dead lifecycle hooks dispatch

Closes [#2](https://github.com/davdittrich/gsd-beads/issues/2). Shipped as capability `0.3.0`
/ plugin `1.3.0`.

## What was wrong

Verified against the installed gsd-core 1.10.0, not inferred:

| Point | Site | What is there | Fired? |
|---|---|---|---|
| `plan:pre` | `plan-phase.md:441` | Generic step contract, but §5.6 Branch 2 returns to step 6 when `frontend == false` and Branch 5 needs `AUTO_CHAIN` | No (manual mode) |
| `plan:post` | `plan-phase.md:1355` | `kind == "gate"` only; also short-circuits when `gap-analysis` is inactive | No |
| `execute:wave:pre` | `execute-phase.md:647` | Renders the JSON, then checks only for a *contribution* | No |
| `execute:wave:post` | `execute-phase.md:1016` | `kind == "gate"` only | No |
| `verify:post` | `execute-phase.md:1202` | Step loop hardcoded to `ref.skill == "secure-phase"` | No |
| `ship:pre` | `ship.md:226` | Generic step loop, installed by this capability's own patch | Yes |

## What was built

`hooks/lifecycle-dispatch.sh`, a `PostToolUse` hook matching the
`gsd_run loop render-hooks <point> --raw` call gsd-core still makes at each dead point, driving
`sync.py lifecycle-dispatch <point>`. Output returns through
`hookSpecificOutput.additionalContext` — confirmed against the raw docs source, since a
`PostToolUse` hook's plain stdout on exit 0 reaches the debug log only and would never have
delivered `execute:wave:pre`'s `<beads_status>` block to the executor briefs it exists for.

Every point maps onto a verb that already existed, all derivable from `phase_dir` alone since the
trigger carries no wave plan-id list.

## Why not the issue's suggested fix

The issue proposed two more marker-bracketed patches into `plan-phase.md` and `execute-phase.md`.
Rejected, and `GSD-CORE-PATCH.md` now records why: dispatch would still depend on a model reading
and obeying workflow prose, a gsd-core update could still strip it, and the loss detector that
guards against exactly that (`beads-recall` Step 3.5, at `plan:pre`) was itself one of the dead
points. The hook's trigger is a call gsd-core must keep making for its own hook system to work at
all, so there is nothing left to strip.

## Verification

- 162 unit tests pass (134 pre-existing + 28 new); `tests/test-capability-auto-install.sh` still ALL PASS.
- CI now runs the sync suite. It had 134 cases and ran none of them. Wiring it in turned `main`
  red and surfaced a pre-existing gap: ~15 cases mock `bd`'s subprocess calls but not
  `bd_available()`, which probes `shutil.which("bd")`, so on a runner without the binary they
  short-circuit onto the fail-open path and their assertions fail. Fixed by installing the pinned
  upstream release binary (`0c65d69`) rather than stubbing one — `_bd_on_path()` is evaluated at
  import time and gates the cases that drive a genuine `bd` database, so a stub would un-skip
  exactly the tests it cannot satisfy. CI green with all 162 cases executing, not skipping.
- End-to-end against a real `bd` database in a scratch project: `bd list` went from
  `No issues found.` (the reported symptom, verbatim) to an epic plus one issue per `<task>`, with
  `beads_epic` and both `<beads-id>` elements written back into `PLAN.md`. A second identical hook
  run left the count at 3 — idempotent.

## Post-release review (v1.3.0 → v1.3.1)

A four-lens adversarial review found a defect in the fix worse than the bug it fixed.

**Blocking — data loss.** v1.3.0 matched `render-hooks <point>` anywhere in a Bash command. `rg
"render-hooks plan:post --raw" .`, an unquoted `grep`, and an `echo` of the line all fired it.
One fire created bd issues *and* ran `strip_task_bodies`, deleting `<behavior>`/`<action>`/
`<acceptance_criteria>` from every unsynced task in the phase's `PLAN.md`. The shipped comment
asserting a spurious run "changes nothing" was never verified and was wrong — the exact
unearned-confidence pattern the review lens exists to catch. A quoted grep escaped only because
the closing quote tripped a `(?!\S)` lookahead: luck, not design.

Fixed in two independent layers, either sufficient alone: the matcher now requires a recognised
shim in shell command position plus `loop … --raw`, and `lifecycle_dispatch` passes
`allow_strip=False` so hook-driven dispatch never performs the authoritative strip at all.
Seven innocent command shapes and five real ones are pinned by regression tests.

**Performance.** `matcher: "Bash"` means the hook ran after every Bash call in every session,
starting a Python interpreter each time. A locale-pinned builtin pre-filter now rejects the
common case before any spawn: 13.00 → 0.91 ms small payload, 64.3 → 22.9 ms at 4 MB. `LC_ALL=C`
is load-bearing — PostToolUse payloads carry the tool's full output and UTF-8 pattern matching
alone cost ~34 ms on 4 MB.

**Cleanups applied.** One shared `read_beads_config` behind both accessors; two JSON parses
merged into one; the dead `--phase-dir` flag and `phase_dir_override` parameter removed (nothing
but a test used them); a redundant bash `case` re-validating its own hardcoded tuple deleted; an
explicit 120 s hook timeout; comment bloat trimmed. Net −76 lines across the touched files while
adding two regression suites.

**Rejected.** Rewriting the hook wholesale in Python — the bash pre-filter is precisely what
makes bash worth keeping, and a `.py` hook loses the silent fail-open when `python3` is absent.

**Surfaced, not fixed (pre-existing, ticketed).** `beads.sync_mode` is declared in
`capability.json` and read by no code — `mirror`/`off` do nothing (`gsd-beads-v43`).
`check_shipmd_patch` and `check_execute_plan_patch` are structural clones, ~50 lines recoverable
(`gsd-beads-t7a`).

## Deliberate limits

- **Claude Code only.** `PostToolUse` is a Claude Code hook; `runtimeCompat.supported` is still
  `["*"]`. On another runtime the five points stay undispatched and only `ship:pre` runs. The
  manual escape hatch is `sync.py lifecycle-dispatch <point>`, documented in README. `.codex/` and
  `.cursor/` hook variants already exist in this repo as the pattern for a later pass.
- **`execute:wave:pre` renders a phase-wide `<beads_status>` block, not a wave-scoped one**, and
  `execute:wave:post` uses the phase-wide idempotent `reconcile-stale-closed` rather than
  `close-wave`. Both because the render-hooks call carries no wave plan-id list. Phase-wide is a
  superset, so no ticket pointer is lost.
- **No retroactive backfill.** A project that planned phases before 0.3.0 still has no issues for
  them. CHANGELOG records the hazard: `create-issues` under `sync_mode: authoritative` strips
  `<task>` bodies out of `PLAN.md`, so on such a project the only copy of task content moves into
  a `bd` database `.beads/` may be gitignoring. Confirm content landed in `bd` before committing.
- **The upstream fix is still the right one.** `open-gsd/gsd-core#3554` tracks generic
  `kind == "step"` dispatch for `ship:pre`; the same is needed at the other five. This change makes
  the capability work today without waiting for it.
