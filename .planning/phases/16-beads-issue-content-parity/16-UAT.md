---
status: testing
phase: 16-beads-issue-content-parity
source: [16-VERIFICATION.md]
started: 2026-08-19T00:37:06Z
updated: 2026-08-19T00:37:06Z
---

## Current Test

number: 1
name: gsd-executor reads task content from bd, not PLAN.md (D-01)
expected: |
  Run a plan whose PLAN.md tasks have been stripped to pointer form (per 16-03's
  strip_task_bodies) through a real gsd-executor. The executor should read the task's
  full description/acceptance_criteria from `bd show <id> --json`, not from PLAN.md
  (which now only carries a pointer). Patch text in execute-plan.md is installed and
  byte-verified; agent behavior against a real stripped plan has not yet been observed.
awaiting: user response

## Tests

### 1. gsd-executor reads task content from bd, not PLAN.md
expected: |
  Executor pulls task body from `bd show <id> --json`, not from a stripped PLAN.md pointer.
result: [pending]

### 2. Hard halt on unreachable bd (D-04)
expected: |
  When `bd` is unreachable, the executor hard-halts per the installed patch rather than
  silently proceeding with no task content. bd's own failure signature (exit 1, `error` key)
  is independently confirmed; agent halt-compliance on top of that signature is unobserved.
result: [pending]

### 3. Empty-description pre-migration fallback (D-07)
expected: |
  For a task issue created before this phase (no description ever written), the executor
  falls back sanely instead of erroring or halting incorrectly. Patch text installed;
  16-04-SUMMARY.md's own coverage table already flags this path as unexercised.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
