---
phase: quick
plan: 260820-wdk
subsystem: claude-code-hooks
tags: [claude-code, hooks, gsd, ponytail, proportionality]
requires: []
provides:
  - Pre-expansion proportionality decisions for five scope-expanding GSD commands
  - Deterministic-first routing with bounded GitHub and Claude ambiguity fallback
  - Documented advisory, warn, and block enforcement contract
affects: [ponytail-everywhere, gsd-command-routing]
actuals:
  tokens: 6559
  tasks: 3
  commits: 4
tech-stack:
  added: []
  patterns: [dependency-free UserPromptExpansion hook, fail-open external classification]
key-files:
  created:
    - ponytail-everywhere/hooks/proportionality-check.js
    - ponytail-everywhere/tests/test-proportionality-check.sh
  modified:
    - ponytail-everywhere/hooks/hooks.json
    - ponytail-everywhere/.gsd/capabilities/ponytail/capability.json
    - ponytail-everywhere/.claude-plugin/plugin.json
    - ponytail-everywhere/README.md
key-decisions:
  - "Use one dependency-free Node hook and the existing gsd-tools.sh resolver."
  - "Treat only narrower recommendations as mismatches and fail open on insufficient evidence or external-tool failure."
  - "Keep the one-shot milestone override entirely in the current hook payload."
patterns-established:
  - "Deterministic-first routing: invoke external evidence and model classification only for ambiguous requests."
  - "Untrusted evidence is bounded, GET-only, schema-validated, and never executed."
requirements-completed: []
status: complete
completed: 2026-08-20
duration: 9m15s
---

# Quick Task 260820-wdk: GSD Command Proportionality Summary

Claude Code now intercepts five scope-expanding GSD commands before expansion, recommends the smallest justified route, and applies configurable fail-open enforcement without creating durable decision artifacts.

## Accomplishments

- Registered an exact `UserPromptExpansion` allowlist for `gsd-new-project`, `gsd-new-milestone`, `gsd-manager`, `gsd-mvp-phase`, and `gsd-discuss-phase`.
- Added deterministic direct/quick/phase/milestone routing, bounded GET-only GitHub evidence, one schema-validated Claude print-mode call for ambiguity, and a one-shot inline override.
- Added 11 proportionality cases covering routes, commands, enforcement modes, disabled behavior, timeouts, missing tools, malformed or low-confidence results, and artifact-free execution while preserving all 11 existing session-start cases.
- Published the default-warn capability enum and the full operator contract, including the Claude-only surface boundary.

## Task Commits

1. **Task 1 RED: Prove one proportionality decision command-expansion boundary** — `6d3f1c2` (test)
2. **Task 1 GREEN: Prove one proportionality decision command-expansion boundary** — `a9d240d` (feat)
3. **Task 2: Complete hybrid classification, enforcement, override, and fail-open coverage** — `787108f` (feat)
4. **Task 3: Publish configuration and operator contract** — `65db0ad` (docs)

## Files Created/Modified

- `hooks/proportionality-check.js` — classifies requests, gathers bounded evidence, and emits valid allow/block hook JSON.
- `hooks/hooks.json` — registers the exact five-command pre-expansion matcher.
- `tests/test-proportionality-check.sh` — dependency-free process-level coverage for the decision contract and failure paths.
- `.gsd/capabilities/ponytail/capability.json` — exposes `ponytail.enforcement` with `advisory`, `warn`, and `block` values, defaulting to `warn`.
- `.claude-plugin/plugin.json` — describes the plugin's enforced proportionality behavior.
- `README.md` — documents timing, routes, modes, override semantics, lookups, fail-open behavior, no-artifact guarantee, and Codex limitation.

## Decisions Made

- Reused `hooks/gsd-tools.sh` through a constant shell invocation instead of duplicating its resolver.
- Kept classification conservative: contradictory or weak cues stay ambiguous, and confidence below 0.6 cannot block work.
- Limited recognized GitHub evidence to four URLs, two kilobytes per response, fixed REST endpoints, GET requests, and three seconds per subprocess.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test bug] Made Claude invocation counting line-safe**

- **Found during:** Task 2
- **Issue:** The test stub logged the multiline classifier prompt, so one invocation appeared as five log lines.
- **Fix:** Log one constant line per invocation.
- **Files modified:** `tests/test-proportionality-check.sh`
- **Verification:** The ambiguity case observes exactly one call and the complete hook suite passes.
- **Committed in:** `787108f`

**2. [Rule 1 - Runtime compatibility] Trusted successful subprocess status despite sandbox EPERM metadata**

- **Found during:** Task 2
- **Issue:** The managed sandbox attached an `EPERM` error object to a completed stub process while also returning status 0 and valid stdout.
- **Fix:** Treat exit status as authoritative; missing, failed, and timed-out processes still return nonzero or null and fail open.
- **Files modified:** `hooks/proportionality-check.js`
- **Verification:** Success, missing-tool, explicit-error, and timeout cases all pass.
- **Committed in:** `787108f`

**3. [Rule 1 - Documentation accuracy] Updated capability description alongside plugin description**

- **Found during:** Task 3
- **Issue:** The capability manifest still described Ponytail as advisory-only after adding blocking modes.
- **Fix:** Updated the existing manifest description without changing its version or adding release machinery.
- **Files modified:** `.gsd/capabilities/ponytail/capability.json`
- **Verification:** Manifest parses and README/config assertions pass.
- **Committed in:** `65db0ad`

**Total deviations:** 3 auto-fixed Rule 1 issues. All were required for accurate tests or shipped behavior; no scope expansion.

## Issues Encountered

- The repository lacked a local Git author identity. The existing repository author name and email were copied into this nested checkout's local config only.
- `lean-ctx` blocks inline `node -e` execution, so the plan's equivalent JSON parse was run with `jq empty`; both shell suites then passed normally.

## Verification

- `jq empty hooks/hooks.json .gsd/capabilities/ponytail/capability.json .claude-plugin/plugin.json` — passed.
- `bash tests/test-proportionality-check.sh` — 11/11 cases passed.
- `bash tests/test-session-start.sh` — 11/11 cases passed.
- Stub scan across all six changed files found no TODOs, placeholders, empty render data, or unfinished production paths.
- Nested repository is clean after commits; the parent repository's nested checkout remains untracked and unstaged.

## Self-Check: PASSED

- All six planned files exist.
- Commits `6d3f1c2`, `a9d240d`, `787108f`, and `65db0ad` exist in the standalone repository.
- No production stubs or new unmodeled threat surfaces remain.
