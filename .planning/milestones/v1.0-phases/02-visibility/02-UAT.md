---
status: complete
phase: 02-visibility
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md]
started: 2026-08-15T20:00:00Z
updated: 2026-08-15T20:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. BEADS-RECALL.md written at plan:pre with zero open issues
expected: BEADS-RECALL.md is always written at plan:pre when bd is available, even with zero open issues (D-04 "none found" body)
result: pass
source: automated
coverage_id: D1

### 2. Files-reverse-lookup match listed under matched heading
expected: An open issue whose <beads-id>-linked task's <files> overlaps this phase's ROADMAP.md/CONTEXT.md mentions is listed under the matched heading, tagged "matched via: files"
result: pass
source: automated
coverage_id: D2

### 3. Desc-contains fallback match listed under matched heading
expected: An open issue with no matching <beads-id> anywhere, but whose description substring-matches a phase-mentioned token, is listed under the matched heading, tagged "matched via: description"
result: pass
source: automated
coverage_id: D3

### 4. Unmatched issue stays Unscoped
expected: An issue matching neither technique is listed under a separate Unscoped heading, never dropped (D-02)
result: pass
source: automated
coverage_id: D4

### 5. capability.json declares plan:pre step and pointer contribution
expected: capability.json declares the plan:pre -> beads-recall step and a plan:pre -> planner static pointer contribution using the confirmed-working plan-phase.md:731 slot
result: pass
source: automated
coverage_id: D5

### 6. regenerate_beads_md frontmatter matches bd counts
expected: regenerate_beads_md's frontmatter carries phase/epic/open/closed/blocking_open=0/diverged=0/generated_from/generated_at, matching a real bd list --parent response's open/closed counts
result: pass
source: automated
coverage_id: D1

### 7. Hand-edited BEADS.md fully overwritten on regeneration
expected: A hand-edited BEADS.md (extra line inserted before regenerating) is fully overwritten -- the hand edit is absent after the next regenerate_beads_md call
result: pass
source: automated
coverage_id: D2

### 8. Blocked-by column excludes parent-child edges
expected: The issue table's blocked-by column lists only dependencies[] entries with type=="blocks", excluding type=="parent-child" epic edges (D-08)
result: pass
source: automated
coverage_id: D3

### 9. Wave-status block names only this wave's issues
expected: render_wave_status_block's printed block names every issue id belonging to the given plan_ids and omits issues from other plans in the same phase directory
result: pass
source: automated
coverage_id: D4

### 10. Wave-status block handles zero resolving plan_ids
expected: With zero plan_ids resolving to any synced task, wave-status-block prints "no synced issues for this wave" rather than an empty block
result: pass
source: automated
coverage_id: D5

### 11. capability.json declares one execute:wave:pre steps[] entry (D-11)
expected: capability.json declares exactly one new execute:wave:pre steps[] entry (ref.skill beads-status, same skill id as execute:wave:post, D-11); beads-status/SKILL.md never adds a new contributions[] entry for B8
result: pass
source: automated
coverage_id: D6

### 12. BEADS-RECALL.md exists before planner spawn (re-confirmed live)
expected: BEADS-RECALL.md exists at {phase_dir}/{padded_phase}-BEADS-RECALL.md before a real planner subagent is spawned, even against a project with zero open issues (B7/D-04 baseline) -- re-confirmed against a real bd database
result: pass
source: automated
coverage_id: D8

### 13. Recall-pointer fragment reaches planner's composed prompt
expected: Dispatching a real /gsd:plan-phase run (or tracing a real planner subagent Agent() call) shows the plan:pre -> planner recall-pointer contribution fragment (naming BEADS-RECALL.md) present verbatim in the composed prompt text.
result: pass
verified_by: static mechanism inspection (not a live orchestrator trace)
evidence: |
  capability.json declares a plan:pre -> into:"planner" contribution (fragment.path: fragments/recall-pointer.md, when: beads.enabled).
  `gsd_run loop render-hooks plan:pre --raw` shows this entry active, rendered verbatim as <contribution from="beads" into="planner">...</contribution>, text matching recall-pointer.md exactly.
  plan-phase.md:731 is a real orchestrator template line that literally loops PLAN_PRE_HOOKS_JSON entries with kind=="contribution" and into=="planner", injecting fragment.inline verbatim into the planner Agent() prompt -- the same shared slot ai-integration/assumption-delta/schema-gate/security already use, confirmed working.
  Remaining gap: no live grep of an actual dispatched planner subagent's rendered prompt text (structurally not possible from within a spawned subagent) -- wiring correctness confirmed statically, not via live trace.

### 14. Wave-status block reaches executor's composed prompt
expected: The composed prompt each executor's Agent() call receives at execute:wave:pre names this wave's issue ids -- verified by direct prompt inspection, per B8's literal acceptance criterion.
result: pass
verified_by: static mechanism inspection (not a live orchestrator trace)
evidence: |
  execute-phase.md:641-648 fetches WAVE_PRE_HOOKS_JSON but has no automatic template slot that forwards a step-hook's output into an executor's Agent() prompt= (unlike plan-phase.md:731's contribution loop used by D6/Test 13).
  beads-status/SKILL.md Step 2a explicitly names this a deliberate design choice ("Pattern 2: skill-mediated dispatch, not automatic manifest-level fragment forwarding") and Anti-Pattern 7 restates it: pasting the <beads_status> block into each executor's prompt= is the orchestrator's own next action, not framework-automatic.
  Confirmed intentional (02-RESEARCH.md evaluated and chose skill-mediated dispatch over a nonexistent auto-forwarding slot) -- but structurally weaker than Test 13: correctness depends on the orchestrator agent following SKILL.md's instruction on every real dispatch, not a guaranteed substitution. This is why SUMMARY correctly flags D7 human_judgment: true instead of auto-passing it.
  Remaining gap: no live grep of an actual dispatched executor subagent's rendered prompt text.

## Summary

total: 14
passed: 14
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
