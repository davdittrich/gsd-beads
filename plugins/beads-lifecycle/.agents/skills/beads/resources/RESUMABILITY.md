# Resumability Across Sessions

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

`bd` state — issue status, dependencies, comments — survives a thread reset, a context compaction, or a handoff to a different agent entirely. A scratch checklist in a chat transcript does not. This is the whole reason to route durable state through `bd` instead of a markdown TODO.

## Recovery sequence at the start of a cold session

1. `bd prime` — reasserts workflow context (or the gsd-tailored override, if `.beads/PRIME.md` is present; see `.beads/PRIME.md`).
2. `bd ready` / `bd list --status=in_progress` — see what's actually available versus already claimed.
3. `bd show <id>` on anything already `in_progress` — read its comments before touching it. Comments are the durable handoff channel: a finding, a partial result, or a "stopped here because X" note left by a prior session lives there, not in a transcript that's gone.
4. Decide: **resume** (the claim is stale or was yours) or **release** (`bd update <id> --assignee=` clears it) if the work looks abandoned or superseded.

## Anatomy of a resumable issue

**Minimal, always:**
```
Description: what needs to be built and why
Acceptance Criteria: concrete, testable outcomes (WHAT, not HOW)
```

**Enhanced, for complex or multi-session technical work:** add an implementation guide to the issue's notes — working (tested) code, a real API response sample, the desired output shape, and the research context that led to the approach. The test: would a fresh agent instance, or you after two weeks, struggle to resume from the description alone? If yes, add the detail; if the work is a simple bug fix with an obvious scope, skip it — over-documenting a typo fix wastes tokens without helping anyone.

## Optional notes template for complex technical work

```markdown
IMPLEMENTATION GUIDE FOR FUTURE SESSIONS:

WORKING CODE (tested):
# actual code that runs, with imports and setup, showing what it returns

API/DATA RESPONSE SAMPLE:
# real structure, not a description of the structure

DESIRED OUTPUT FORMAT:
# what the final result should look like, concretely

RESEARCH CONTEXT:
# why this approach, what alternatives were considered, what was discovered
```

## Anti-patterns

- **Over-documenting simple work.** A one-line typo fix doesn't need an implementation guide. Match the detail to the actual resumption risk.
- **Design details in Acceptance Criteria.** "Use approach X, call API Y, format as Z" locks the implementation instead of stating the outcome. Put design reasoning in Notes; keep Acceptance Criteria about the observable result.
- **Raw, unformatted dumps.** A 100-line unformatted JSON blob pasted into notes is hard to resume from. Extract the relevant fields and show the structure, not the whole payload.

## When to add resumability detail

- **At creation:** if you already have working code or a clear output shape from research, put it in the notes immediately.
- **Mid-work:** just got something working, or discovered important context? Update the notes before moving on — don't wait for session end.
- **At session end:** if resuming will plainly be hard for whoever picks this up next, add the guide. If it's obvious, skip it.

## gsd-core framing

`.planning/`'s `PLAN.md`/`SUMMARY.md` record **intent** — what a phase is and why. `bd` records **status** — what's done, what's claimed, what's blocked. Neither substitutes for the other: resuming a gsd phase after a reset means reading both, not just one. A task's `<beads-id>` element is the durable link between the two; use it to find the bd issue for a plan task, or `bd show`'s dependency listing to find which plan task an orphaned bd issue belongs to.
