---
status: complete
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
awaiting: closed

## Tests

### 1. Interactive TTY session — single-fire backstop

expected: Start one real interactive Claude Code session (not `claude -p`) inside this repository. The beads SessionStart context (bd prime output) appears exactly once — no double-fire, no missing fire.
result: PASS — user started a fresh `claude --debug hooks --debug-file` session; debug log confirms `Hook SessionStart (bd prime --hook-json) provided additionalContext (4856 chars)` exactly once (`grep -c` == 1), with full bd-prime markdown content present. No visible terminal banner is expected — SessionStart additionalContext is injected silently into model context, not printed to the user; the user initially misread the absence of a printed banner as a non-fire. Debug log is authoritative and confirms correct single-fire behavior.

## Summary

total: 1
passed: 1
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
