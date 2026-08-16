---
status: testing
phase: 06-runtime-integration
source: [06-VERIFICATION.md]
started: 2026-08-16T00:00:00Z
updated: 2026-08-16T00:00:00Z
---

## Current Test

number: 1
name: Interactive TTY session — single-fire backstop
expected: |
  The beads context block (from `bd prime --hook-json`) appears exactly once in the session's
  context — matching the headless-probe result of exactly one fire.
awaiting: user response

## Tests

### 1. Interactive TTY session — single-fire backstop
expected: Start one real interactive Claude Code session (not `claude -p`) inside this repository. The beads SessionStart context (bd prime output) appears exactly once — no double-fire, no missing fire.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
