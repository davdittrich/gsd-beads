---
title: Two-plugin capability design — ponytail-everywhere + sota-numerics
date: 2026-08-17
context: /gsd-explore session, routed to phases 10 and 11
---

## Decisions

**No gsd-core patch.** `/gsd-explore` and `/gsd-spec-phase` dispatch zero capability
lifecycle hooks (only `discuss:{pre,post}`, `plan:{pre,post}`,
`execute:{pre,wave:pre,wave:post,post}`, `verify:{pre,post}`, `ship:{pre,post}` exist).
Patching core to add hook points there would mirror `beads-lifecycle`'s existing
`ship:pre` patch (`.gsd/capabilities/beads/GSD-CORE-PATCH.md`) — heavyweight: local
patch file, upstream issue, drift-detection skill step, explicit constraint-override
record. Rejected for both new plugins.

**Reach every stage via SessionStart hook instead.** Each plugin ships its own
`hooks/session-start.sh` (same pattern as this repo's existing `beads-lifecycle` hook,
and as `ponytail`/`caveman` plugins already do — see the reminder blocks injected at
session start in this very session). This is session-scoped, not lifecycle-scoped, so
it reaches `/gsd-explore` and `/gsd-spec-phase` too, without touching gsd-core.

**Layered mechanism for both plugins:**
1. SessionStart hook — broad, always-on reminder text.
2. `capability.json` `contributions[]` fragments at the six real lifecycle points
   (`plan:pre/post`, `execute:pre/wave:pre/wave:post/post`, `verify:pre/post`,
   `ship:pre/post`) — targeted reinforcement injected into the actual agent prompt
   at the moment it matters (planner drafting tasks, executor writing code, etc).

**Gate decisions (per-capability, diverge):**
- `sota-numerics`: **blocking** `plan:post` gate — `artifact-content` check that
  PLAN.md/SPEC.md contains an Alternatives-Considered section. Rejected plans fail
  closed. This codifies the user's existing global CLAUDE.md rule ("Plan submitted to
  the plan gate without this analysis MUST be rejected for 'Insufficient Research'")
  as a portable, mechanically-enforced gate any project installing the plugin gets,
  independent of that user's personal CLAUDE.md being present.
- `ponytail-everywhere`: **advisory only**, no gate. "Did you pick the laziest rung
  that works" isn't mechanically checkable (diff-size/line-count gates considered and
  rejected as blunt false-positive-prone proxies).

## Not done here

Phases 10/11 (`.planning/phases/10-*`, `.planning/phases/11-*`) still need
`/gsd-plan-phase` to produce PLAN.md before any implementation — this note and the
phase entries are routing only, not a plan.
