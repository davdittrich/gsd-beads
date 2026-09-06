---
status: blocked
trigger: "ponytail-everywhere does not effectively change the behavior of gsd-review and gsd-plan-review-convergence; ponytail instructions appear not to be injected for reviewers"
created: 2026-08-28T15:33:02+02:00
updated: 2026-08-28T15:33:37+02:00
beads_id: gsd-beads-a7w
---

# Debug Session: Ponytail Reviewer Injection

## Symptoms

- **Expected behavior:** Active ponytail-everywhere instructions are included in every external reviewer prompt used by `$gsd-review` and each `$gsd-plan-review-convergence` cycle.
- **Actual behavior:** Enabling ponytail-everywhere does not effectively change reviewer behavior; its instructions appear absent from reviewer context.
- **Error messages:** None reported.
- **Timeline:** Reported as current behavior on 2026-08-28; whether it previously worked is unknown.
- **Reproduction:** Run `$gsd-review` directly or through `$gsd-plan-review-convergence` with ponytail-everywhere active, then inspect the exact prompt sent to each reviewer.

## Current Focus

- **hypothesis:** Confirmed: external review has no capability hook point or prompt-fragment insertion seam.
- **test:** A RED test is deferred: this repository has no owned implementation path for the required host-loop change.
- **expecting:** A gsd-core change must add a review hook point, render its active contributions during prompt construction, and Ponytail must then declare a reviewer contribution.
- **next_action:** obtain scope and ownership for the upstream gsd-core review-hook contract before editing or adding the regression test.
- **reasoning_checkpoint:**
- **tdd_checkpoint:** regression test must fail before implementation

## Evidence

- timestamp: 2026-08-28T15:33:37+02:00 — `ponytail-everywhere/.gsd/capabilities/ponytail/capability.json` declares contributions only at `plan:pre`, `execute:wave:pre`, and `execute:wave:post`; it has no review contribution or reviewer fragment. (100)
- timestamp: 2026-08-28T15:33:37+02:00 — `/home/dd/.codex/gsd-core/bin/lib/loop-resolver.cjs` enumerates exactly twelve valid points ending in `ship:post`; `gsd-tools loop render-hooks review:pre --raw` returns `Error: Invalid loop point: "review:pre"`. (100)
- timestamp: 2026-08-28T15:33:37+02:00 — `/home/dd/.codex/gsd-core/workflows/review.md` builds `gsd-review-prompt.md` and passes it to every lane, but contains no `loop render-hooks` call. The shared prompt therefore cannot contain active capability instructions. (100)
- timestamp: 2026-08-28T15:33:37+02:00 — Ponytail's only runtime hooks are `UserPromptExpansion`, `SessionStart`, and four `SubagentStart` matchers (`gsd-planner`, `gsd-executor`, `gsd-code-reviewer`, `gsd-verifier`). They do not intercept prompt-file construction or external reviewer invocation. (100)
- timestamp: 2026-08-28T15:33:37+02:00 — The only repository-local gsd-core patch register is `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md`; it explicitly limits ownership to Beads' `ship.md` and `execute-plan.md` patches. No Ponytail review patch surface exists. (100)

## Eliminated

- A Ponytail manifest-only contribution: impossible because `review:pre` is not a valid loop point and `review.md` never renders hooks. (100)
- Per-reviewer-adapter patches: rejected because all prompt-bearing lanes consume the same already-built prompt file; it would duplicate behavior and still omit non-prompt lanes. (95)

## Resolution

- **root_cause:** gsd-core has no review lifecycle point or review-prompt contribution dispatch, while Ponytail only declares lifecycle contributions that are never consulted by `$gsd-review`. (100)
- **fix:** not applied — requires an upstream/core-owned change to the loop-host contract, capability validator/registry, and `workflows/review.md`, followed by a Ponytail reviewer contribution and an end-to-end prompt-capture regression test. (95)
- **verification:** capability state confirms Ponytail is active, while the review hook probe fails before adapter invocation; static source inspection proves prompt assembly has no hook-render call. (100)
- **files_changed:** `.planning/debug/ponytail-reviewer-injection.md`, `.wolf/buglog.json`, `.wolf/cerebrum.md`.
