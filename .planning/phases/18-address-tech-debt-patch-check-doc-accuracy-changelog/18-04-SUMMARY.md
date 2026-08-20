---
phase: 18-address-tech-debt-patch-check-doc-accuracy-changelog
plan: 04
subsystem: release-hygiene
tags: [changelog, semver, doc-accuracy, plugin-json]
dependency-graph:
  requires:
    - phase: 18-01
      provides: "verify-reapply-patches.cjs naming in GSD-CORE-PATCH.md, documented in the 0.4.0 Changed entry"
    - phase: 18-02
      provides: "the checkpoint answer (option-a: v1.3.0 tag deleted) that determines no withdrawal line is needed"
    - phase: 18-03
      provides: "the PATCH_CHECKS marker change and SKILL.md re-keying, documented in the 0.4.0 Changed entry"
  provides:
    - "CHANGELOG 0.4.0 section documents all four Phase 17 requirements (TRUTH-01..04) plus Phase 18's own changes"
    - "CHANGELOG 0.3.1 files the hook-timeout reduction under Changed instead of Performance"
    - "plugin.json declares 1.4.0, closing ROADMAP Ship-step check #1"
  affects:
    - "CHANGELOG.md"
    - "plugins/beads-lifecycle/.claude-plugin/plugin.json"
tech-stack:
  added: []
  patterns:
    - "awk-region-scoped acceptance criteria (heading-to-heading) to prove a doc edit landed in the right section without disturbing neighbors"
key-files:
  created: []
  modified:
    - "CHANGELOG.md"
    - "plugins/beads-lifecycle/.claude-plugin/plugin.json"
decisions:
  - "18-02's checkpoint recorded option-a (v1.3.0 tag deleted from origin and locally), so Task 1's conditional withdrawal-line branch does not apply — confirmed by grep '55855cd' CHANGELOG.md returning 0"
metrics:
  duration: "~15min"
  completed: "2026-08-20"
actuals:
  tokens: 9500
  tasks: 3
  commits: 3
status: complete
---

# Phase 18 Plan 04: CHANGELOG accuracy + plugin version bump Summary

Closed `17-REVIEW.md` WR-03 and ROADMAP Phase 17 Ship-step checks #1 and #2: added the missing
TRUTH-03 entry (plus Phase 18's own message-marker and reapply-verification changes) to the 0.4.0
section, relocated the 0.3.1 hook-timeout entry from `### Performance` to `### Changed`, and
bumped `plugin.json` from `1.3.1` to `1.4.0`.

## What Was Built

**Task 1** — Added an `### Added` subsection to CHANGELOG's `## 0.4.0` section (placed before the
existing `### Fixed`), documenting `check_native_step_dispatch`, its two module constants
(`NATIVE_STEP_DISPATCH_WORKFLOW_FILES`, `NATIVE_STEP_DISPATCH_REGION_LINES`), the
`plan:post`/`verify:post` stand-down mechanism, the deliberately-ungated `execute:wave:pre`/
`execute:wave:post`/`plan:pre` points, the region-scoped-not-whole-file rationale, and
`open-gsd/gsd-core#3687`. Also added two entries to the existing `### Changed` subsection
documenting Phase 18's own changes: the `⚠ ` marker added to all four `PATCH_CHECKS`
`not_found_msg`/`could_not_read_msg` templates plus the exit-code-based SKILL.md surfacing rule
(18-03), and `GSD-CORE-PATCH.md` naming `verify-reapply-patches.cjs`/`check-patch` as the
reapply-verification path with the two-runtime-homes-never-cross-copied rule (18-01).

**Checkpoint branch taken:** 18-02's SUMMARY records `option-a` — the `v1.3.0` tag was deleted
from `origin` and locally. Per the plan's explicit instruction, no withdrawal line was added; the
tag deletion already closes that ROADMAP item. Verified: `grep -c '55855cd' CHANGELOG.md` returns
0.

**Task 2** — Split the hook-timeout sentence out of 0.3.1's `### Performance` bullet ("Separately,
the hook's own timeout is set explicitly to 120 s...") and refiled it as its own bullet under
0.3.1's existing `### Changed` subsection, dropping the now-redundant trailing clause that pointed
back at the Performance heading (no heading above it to disclaim after the move). The Performance
bullet keeps every measured figure untouched: `13.00 ms`, `0.91 ms`, `LC_ALL=C`, `4 MB`.

**Task 3** — Changed `plugin.json`'s `version` field from `1.3.1` to `1.4.0`. Nothing else in the
file touched — `name`, `description`, `author`, `license`, `skills` byte-identical (`git diff
--numstat` confirms exactly 1 line added, 1 removed). `capability.json` untouched, still `0.4.0`.

## Verification

All acceptance criteria from the plan re-run live after each task:

- `awk '/^## 0.4.0$/,/^## 0.3.1$/' CHANGELOG.md | grep -c check_native_step_dispatch` → 1
- Same region contains `NATIVE_STEP_DISPATCH_WORKFLOW_FILES`, `NATIVE_STEP_DISPATCH_REGION_LINES`,
  `open-gsd/gsd-core#3687`, `plan:post` (2), `verify:post`, `execute:wave:pre`,
  `execute:wave:post` — all present
- `grep -c '^### Added$' CHANGELOG.md` → 2 (0.4.0's new one + 0.3.0's pre-existing one);
  0.4.0's subsection order is `### Added`, `### Fixed`, `### Changed`, `### Breaking`
- Same region contains `PATCH_CHECKS` and `check-patch` (3×), and `verify-reapply-patches.cjs`
- `grep -c '^## 1.4.0' CHANGELOG.md` → 0 — no invented version heading
- `grep -c '^## 0.3.1$' CHANGELOG.md` → 1, `grep -c '^## 0.3.0$' CHANGELOG.md` → 1 — undisturbed
- `grep -c '55855cd' CHANGELOG.md` → 0 (option-a branch confirmed)
- `awk '/^### Performance$/,/^### Changed$/' CHANGELOG.md | grep -c '120 s'` → 0 (was 1)
- `awk '/^## 0.3.1$/,/^## 0.3.0$/' CHANGELOG.md | grep -c '120 s'` → 1 (relocated, not deleted)
- Performance region still contains `13.00 ms`, `0.91 ms`, `LC_ALL=C`, `4 MB`
- Relocated text contains `reduction` and still names the 600 s default it reduces from
- `grep -c '^### Performance$' CHANGELOG.md` → 1; 0.3.1 subsection order:
  `### Fixed`, `### Performance`, `### Changed`, `### Known issues` — unchanged
- `python3 -m json.tool plugins/beads-lifecycle/.claude-plugin/plugin.json` → exit 0
- `grep -c '"version": "1.4.0"'` → 1, `grep -c '"version": "1.3.1"'` → 0
- `git diff --numstat plugins/beads-lifecycle/.claude-plugin/plugin.json` → `1  1`
- `grep -c '"version": "0.4.0"' capability.json` → 1 (untouched)
- `git diff --quiet v1.3.1..HEAD -- plugins .claude-plugin README.md` → exit 1 (non-zero, changes
  exist) — ROADMAP Ship-step check #1's three conditions (version bump, capability.json diff,
  CHANGELOG 0.4.0 section) all hold together

## Deviations from Plan

None — plan executed exactly as written for all three tasks, including the conditional branch
(18-02 recorded `option-a`, so the withdrawal-line addition was correctly skipped).

## Known Stubs

None.

## Threat Flags

None — both plan-declared trust boundaries (repo → marketplace consumer via `plugin.json`'s
version string; CHANGELOG → future maintainer) are the ones this plan closes, not new surface.

## Self-Check: PASSED

- FOUND: CHANGELOG.md (check_native_step_dispatch, NATIVE_STEP_DISPATCH_WORKFLOW_FILES,
  NATIVE_STEP_DISPATCH_REGION_LINES, PATCH_CHECKS, check-patch, verify-reapply-patches.cjs all
  present in the 0.4.0 region; `120 s` absent from Performance, present in 0.3.1 overall)
- FOUND: plugins/beads-lifecycle/.claude-plugin/plugin.json declares `"version": "1.4.0"`
- FOUND: commit 357c677 (`git log --oneline` — Task 1, docs(18-04))
- FOUND: commit 996f276 (`git log --oneline` — Task 2, docs(18-04))
- FOUND: commit d389d91 (`git log --oneline` — Task 3, chore(18-04))
