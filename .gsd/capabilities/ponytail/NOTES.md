# ponytail capability — what actually reaches an agent

This capability declares three `contributions[]` entries at `plan:pre`, `execute:wave:pre`, and
`verify:pre`. Only one of them is functional at gsd-core 1.10.0.

## Functional today

`plan:pre` → `into: "planner"` is the sole `kind == "contribution"` injection loop that exists
anywhere in the shipped gsd-core workflow markdown (`plan-phase.md`). When `ponytail.enabled`
resolves true, `fragments/planner-ladder.md` is read and injected verbatim into the `gsd-planner`
subagent's own prompt, along with the resolved `ponytail.level` value via `configValues`.

## Forward-compatible no-ops today

`execute:wave:pre` → `into: "executor"` and `verify:pre` → `into: "verifier"` are schema-valid and
are returned by `gsd_run loop render-hooks <point> --raw` in `activeHooks` exactly like the
`plan:pre` entry — the resolver is generic across all lifecycle points. But no workflow markdown at
either of those points contains a `kind == "contribution"` read-and-inject instruction, so today
these two entries are read by nobody. They are declared anyway, matching D-05's role-tailored intent
and this repo's own `beads` capability precedent of declaring `steps[]` entries beyond the minimum
functional set — should a future gsd-core version add generic contribution dispatch at those points,
these entries activate with no change to this capability.

Actual execute-time and verify-time reach in this repo comes from a different mechanism entirely:
the sibling `ponytail-everywhere` Claude Code plugin's role-matched `SubagentStart` hooks (Plan 01),
which fire directly on `gsd-executor` and `gsd-verifier` subagent spawn regardless of what any
`capability.json` `contributions[]` entry declares.

## Why no gsd-core patch (D-01)

`.gsd/capabilities/beads/GSD-CORE-PATCH.md` records this repo's one precedent for patching a
machine-local gsd-core workflow file to add missing generic dispatch (`ship:pre` gate dispatch). That
patch is deliberately not repeated here: D-01 scopes this capability to the one lifecycle point that
already has real generic contribution dispatch, and the `ponytail-everywhere` plugin's hooks cover
the remaining reach without touching gsd-core at all. Patching `plan-phase.md`/`execute-plan.md` to
add contribution dispatch at more points is out of scope for this phase.

## Re-consent after any edit

Project-scope consent (`capability install ./.gsd/capabilities/ponytail --scope project --yes`) is a
whole-bundle content hash over every file under `.gsd/capabilities/ponytail/`. Editing any file here
— including this one — silently deactivates the capability until `capability install` is re-run.
