---
status: resolved
trigger: "UAT gap G-08-1: the README does not explain at all what the benefit of using beads with gsd is instead of using gsd's built-in tracking."
created: 2026-08-16T00:00:00Z
updated: 2026-08-19T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED — README's "What it does" section states the mechanism (beads becomes
the single source of truth for gsd task state) but never states the problem/benefit — why a
gsd-core user, who already has working built-in `.planning/` markdown tracking, would want to
switch to `bd`. That comparison already exists, fully written, in docs/prd-beads-capability.md
§3.1 and .planning/PROJECT.md's "Core Value" line, but was never pulled into the README.
test: read README.md in full, grep it for any mention of "built-in", "TodoWrite", "why", "benefit",
"instead of", ".planning/ prose" comparison; cross-check against docs/prd-beads-capability.md and
PROJECT.md for existing value-prop material.
expecting: README contains zero contrastive/benefit language; PRD contains a ready-made
comparison table.
next_action: none — diagnose-only mode, root cause confirmed, returning to caller.

## Symptoms

expected: A stranger with no prior gsd-core/beads knowledge can read README.md end to end and
come away able to evaluate, install, and remove gsd-beads (ROADMAP Phase 8 SC1, CONTEXT.md D-01).
actual: "the README does not explain at all what the benefit of using beads with gsd is instead
of using gsd's built-in tracking." (verbatim UAT report, Test 1, .planning/phases/08-readme-release-ship-gate/08-UAT.md)
errors: none
reproduction: Read .planning/phases/08-readme-release-ship-gate/08-UAT.md Test 1 / read README.md
"What it does" section end to end as a cold stranger.
started: Discovered during UAT for Phase 8 (README authored fresh in Phase 8, per 08-CONTEXT.md
code_context: "README.md doesn't exist yet — this phase creates it from scratch").

## Eliminated

(none — first hypothesis confirmed directly from source text, no false starts)

## Evidence

- timestamp: 2026-08-16T00:00:00Z
  checked: README.md "What it does" section (full text, lines 5-16)
  found: |
    Two paragraphs. Paragraph 1 defines gsd-core and beads independently (neutral, encyclopedic).
    Paragraph 2: "`gsd-beads` is a gsd-core capability — an installable overlay, not a fork — that
    makes `bd` the single source of truth for gsd's task state: one beads issue per plan task, task
    dependencies become `bd dep` links, task completion closes its issue, and gsd's
    planner/executor/ship gate all read live `bd` state instead of duplicating it as hand-maintained
    `.planning/` prose."
    This sentence states the MECHANISM (what changes technically) but never states the PROBLEM this
    solves or the BENEFIT to the reader. It mentions ".planning/ prose" only as the thing being
    replaced, not as a described pain point (no query surface, drift, doesn't survive archival,
    invisible outside the project). No occurrence of "TodoWrite", "native", "why", "benefit",
    "instead of using", or any comparison framing anywhere in the file.
  implication: Confirms the UAT report verbatim — the value proposition (why choose beads over
    gsd's built-in tracking) is genuinely absent from the shipped README, not just badly worded.

- timestamp: 2026-08-16T00:00:00Z
  checked: docs/prd-beads-capability.md §3.1 "Where gsd-core keeps task state today"
  found: |
    Contains a ready-made comparison table, already reviewed/approved PRD content:
    | Need | `.planning/` markdown | beads |
    | Query "what can I work on now?" | read files, reason | `bd ready` |
    | Dependencies and blocking | prose ordering | first-class, enforced |
    | Status across phases | per-phase files | one query |
    | Survives milestone archival | archived away | persists |
    | Visible outside one project | no | yes |
    | Machine-updatable without rewriting prose | no | yes |
    Plus §3.2 "The cost, concretely": "With no bridge, a developer who uses both maintains two
    representations of the same work by hand... the two drift silently, because nothing compares
    them."
  implication: The exact missing content already exists, fully articulated, in this repo. It was
    never pulled into the README when Phase 8 authored it from scratch — this is a content-transfer
    gap, not a missing-research gap.

- timestamp: 2026-08-16T00:00:00Z
  checked: .planning/PROJECT.md "## Core Value" line
  found: |
    "gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero duplicated
    task-state bookkeeping survives in `.planning/`."
  implication: A second, shorter formulation of the same value prop, also available and unused
    in the README.

- timestamp: 2026-08-16T00:00:00Z
  checked: .agents/skills/beads/SKILL.md preamble
  found: |
    "Use Beads as the shared project task system. Local plans, scratch files, and personal
    memories are useful, but they are not the durable source of truth for project work."
  implication: A third framing (durability/handoff angle: "must survive thread reset, compaction,
    or handoff") exists but is agent-instruction-voiced, not reader-facing — usable as
    supplementary material but the PRD table is the primary source since it directly names
    "gsd's built-in tracking" (`.planning/` markdown) as the explicit comparison target the UAT
    report asked about.

- timestamp: 2026-08-16T00:00:00Z
  checked: .planning/phases/08-readme-release-ship-gate/08-CONTEXT.md decisions D-01 through D-05
    (locked README scope/structure)
  found: |
    D-04 locks section order: Title/one-liner → What it does → Requirements → Install → Uninstall
    → Caveats → License → Link to gsd-core. Nothing in D-01–D-05 explicitly excludes a
    beads-vs-built-in-tracking comparison; D-01 ("cold stranger... matches SC1's literal 'a
    stranger can evaluate' framing") if anything requires it, since "evaluate" implies the reader
    needs to know why this exists before deciding to install it.
  implication: The gap is not a locked-decision conflict — a value-prop addition fits cleanly
    inside the existing "What it does" section without violating D-04's section order. No
    re-planning of structure is needed, only content.

## Resolution

root_cause: |
  README.md's "What it does" section (authored fresh in Phase 8 per 08-CONTEXT.md code_context
  "README.md doesn't exist yet — this phase creates it from scratch") describes the mechanism of
  gsd-beads (one issue per task, `bd dep` links, live state reads replacing ".planning/ prose")
  but never states the underlying problem or benefit — why a reader who already has gsd-core's
  built-in `.planning/`-markdown task tracking working would want to add beads. That comparison
  was never authored into the README; it exists only in docs/prd-beads-capability.md §3.1-3.2
  (comparison table + drift-cost paragraph) and PROJECT.md's "Core Value" line, both of which
  predate Phase 8 and were not consulted/pulled forward when the README was drafted.

fix: |
  Already shipped, prior to this session, in commit 83b3897 "docs(readme): add
  beads-vs-planning-markdown value proposition" — added a "Why not just use gsd-core's
  built-in tracking?" subsection plus the PRD's comparison table to README.md's
  "What it does" section. This debug session was diagnose-only and was never marked
  resolved once the fix landed via a separate commit; closing it now at milestone v1.2
  close, since verification below confirms the shipped README matches the diagnosis's
  `expecting` criteria.

verification: |
  Read README.md lines 5-38 directly: the "Why not just use gsd-core's built-in tracking?"
  section states the problem (two hand-written representations, silent drift, no shared
  comparison) and the benefit (single source of truth for task state), followed by the
  same comparison table identified in Evidence as existing in docs/prd-beads-capability.md
  §3.1. Matches the diagnosis's root cause and the missing content it identified.

files_changed:
  - README.md (commit 83b3897, prior to this debug session's closure)
