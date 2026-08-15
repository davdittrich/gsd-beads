## REQ-B1
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: One beads issue per PLAN.md task, parented to a phase epic.
- acceptance: After planning an N-task phase, `bd list --parent <epic>` returns exactly N issues whose titles match the plan's tasks.
- scope: P0 — the substrate (F1)

## REQ-B2
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: Plan task ordering becomes beads dependencies.
- acceptance: Task 3 depending on task 1 shows task 1 as a blocker in `bd show`; `bd ready` excludes task 3 until task 1 closes.
- scope: P0 — the substrate (F1)

## REQ-B3
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: Task completion closes its issue automatically.
- acceptance: After a wave completes task 2, that issue is `closed` and no other issue changed.
- scope: P0 — the substrate (F1)

## REQ-B4
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: Identity is bound explicitly, never by title matching.
- acceptance: Each plan task block carries a `beads-id:` written on first sync; re-sync resolves by that id. Renaming a task title does not create a second issue.
- scope: P0 — the substrate (F1)

## REQ-B5
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: Sync is idempotent.
- acceptance: Two syncs over an unchanged plan create zero issues and modify zero issues, proven by a `bd list --json` diff.
- scope: P0 — the substrate (F1)

## REQ-B6
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: `bd` absent, failing or locked degrades to a no-op with one visible notice.
- acceptance: With `bd` off `PATH`, every gsd command completes normally, one line explains the skip, no phase is blocked, and `BEADS.md` is absent rather than stale.
- scope: P0 — the substrate (F1)

## REQ-B7
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: The planner sees open issues before planning.
- acceptance: With an open issue touching a file in the phase's scope, `BEADS-RECALL.md` exists before the planner runs and names that issue.
- scope: P0 — visibility and enforcement (F2, F3, F4)

## REQ-B8
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: The executor's prompt carries live issue state.
- acceptance: The `execute:wave:pre` fragment is present in the composed orchestrator prompt and names the issues in the wave — verified by inspecting the prompt, not by inferring from behaviour.
- scope: P0 — visibility and enforcement (F2, F3, F4)

## REQ-B9
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: A phase with unfinished blocking issues cannot ship.
- acceptance: With one open blocking issue, `ship:pre` blocks and names it. `beads.ship_gate=false` allows the ship and records that it was overridden.
- scope: P0 — visibility and enforcement (F2, F3, F4)

## REQ-B10
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: Divergence blocks and is reported; it is never auto-reconciled.
- acceptance: An issue closed in beads whose task is incomplete (or the reverse) sets `diverged>0`, blocks ship, and reports both sides. Nothing changes until the operator decides.
- scope: P0 — visibility and enforcement (F2, F3, F4)

## REQ-B11
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: `BEADS.md` is regenerated, never hand-edited.
- acceptance: A hand edit is overwritten at the next step; frontmatter always reflects a real `bd` query at generation time.
- scope: P0 — visibility and enforcement (F2, F3, F4)

## REQ-B12
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: One-shot migration of existing `.planning/todos/pending/` entries into beads, reporting what moved and what could not be interpreted.
- acceptance: (absent — PRD lists no acceptance criterion for P1 requirements)
- scope: P1 — adoption

## REQ-B13
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: `beads-status` runnable on demand, printing the plan-task ↔ issue mapping including orphans on both sides.
- acceptance: (absent — PRD lists no acceptance criterion for P1 requirements)
- scope: P1 — adoption

## REQ-B14
- source: /home/dd/Gemini/gsd-beads/docs/prd-beads-capability.md
- description: Milestone-level epic option (`beads.epic_per=milestone`) for users who prefer one epic per release.
- acceptance: (absent — PRD lists no acceptance criterion for P1 requirements)
- scope: P1 — adoption
