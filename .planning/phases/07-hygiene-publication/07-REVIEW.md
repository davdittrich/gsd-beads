---
phase: 07-hygiene-publication
reviewed: 2026-08-16T14:44:21Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - .gitignore
  - .planning/phases/06-runtime-integration/06-PATTERNS.md
  - .planning/phases/07-hygiene-publication/07-PATTERNS.md
  - .planning/STATE-ARCHIVE.md
  - .planning/config.json
  - .planning/research/.cache/255dcad363ccf0b782ea7c97a6975466963460aed6ac2b1019bcc2ecc49869fb.json
  - .planning/ROADMAP.md
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-08-16T14:44:21Z
**Depth:** standard
**Files Reviewed:** 7 (git/repo hygiene artifacts; no application source in scope)
**Status:** issues_found

## Summary

Phase 7 rewrote git history with `git filter-repo` to strip 4 machine-local files (`.beads/config.yaml`, `.beads/metadata.json`, `.claude/.headroom_wrap_marker.json`, `.gsd-capabilities.json`) from every commit, extended `.gitignore`, and published the repo publicly via `gh repo create` + `git push`. The rewrite itself, the new `.gitignore` patterns, and the fresh-clone publication verification were checked directly against the live repository (not just the plan/summary narrative).

`.gitignore` additions are well-scoped: none of the 5 new patterns (`.beads.backup-pre-recovery/`, `.beads/interactions.jsonl`, `*.bak`, `.serena/`, `.gsd/dispatch-isolation-sentinel.json`) shadow any currently-tracked file (`git ls-files` cross-checked against each pattern — zero matches), and they correctly avoid widening `*.bak` into `*.backup` (which would have shadowed 5 tracked `.beads/hooks/*.backup` files). `.git/config` and `.planning/config.json` contain no secrets; the newly-tracked research cache JSON is a plain websearch summary with no credentials. `STATE-ARCHIVE.md` change is a benign pruned-metrics append.

One critical gap: **the two files that were the actual reason for the irreversible history rewrite were never added to any `.gitignore`**, so a routine `bd` operation + `git add` will silently re-commit them, defeating the rewrite. One warning: `ROADMAP.md`'s phase-status table was left stale (Phase 7 shows "Planned"/"0/2" despite both plans being complete), which will mislead downstream phase-tracking automation reading that table.

## Critical Issues

### CR-01: `.beads/config.yaml` and `.beads/metadata.json` are not gitignored — the just-purged files can silently re-enter history

**File:** `.gitignore` (root, all lines); confirmed against `.beads/.gitignore:70-72`

**Issue:** Phase 07-01's entire purpose (per its own SUMMARY: *"Every commit in local history stripped of `.beads/config.yaml`, `.beads/metadata.json`, ... Root `.gitignore` extended so those + sibling local-only artifacts cannot re-enter tracking"*) was to remove these two files from history and prevent recurrence. Verified directly:

- Neither file currently exists on disk (`ls .beads/config.yaml .beads/metadata.json` → No such file or directory) — they were deleted, not just untracked.
- `git check-ignore -v .beads/config.yaml .beads/metadata.json` → **no match, exit 1**. Neither the root `.gitignore` nor the nested `.beads/.gitignore` ignores them.
- `.beads/.gitignore` contains this explicit comment at the bottom (lines 70-72): `"Config files (metadata.json, config.yaml) are tracked by git by default since no pattern above ignores them."` — i.e. beads' own shipped `.gitignore` documents that these files are tracked-by-default and relies on the *consuming project* to opt out if desired.
- Root `.gitignore` was extended with 5 new patterns this phase (`.beads.backup-pre-recovery/`, `.beads/interactions.jsonl`, `*.bak`, `.serena/`, `.gsd/dispatch-isolation-sentinel.json`) — none of which cover `config.yaml` or `metadata.json`.

`bd` regenerates both files on next use (they are core beads state: `metadata.json` carries `project_id` — a stable per-repo UUID — plus backend/db settings; `config.yaml` is the bd config file). The next `git add .` / `git add -A` in this now-public repo will re-track them, and the next commit re-introduces the exact content that a mirror-backed, rehearsed, irreversible `filter-repo` pass was run specifically to remove. This is a direct contradiction between the phase's stated intent and its actual `.gitignore` diff — the fix was never applied to the two files that mattered, only to their "siblings" (the backup/interaction-log artifacts).

**Fix:**
```gitignore
# Beads config/metadata (machine-local; stripped from history in Phase 7 — do not re-track)
.beads/config.yaml
.beads/metadata.json
```
Add this under a new group in root `.gitignore`, then verify with `git check-ignore -v .beads/config.yaml .beads/metadata.json` (must both match) before any further `bd` command runs in this repo. If either file is desired to be shareable in principle (e.g. `issue-prefix`), split out only the non-sensitive keys rather than leaving the whole file trackable by default.

## Warnings

### WR-01: `ROADMAP.md` phase-status table left stale after Phase 7 completion

**File:** `.planning/ROADMAP.md:26,155`

**Issue:** Line 26 still shows `- [ ] **Phase 7: Hygiene & Publication**` (unchecked) and line 155's status table shows `| 7. Hygiene & Publication | 0/2 | Planned | - |`, even though both `07-01-SUMMARY.md` and `07-02-SUMMARY.md` record `status: complete` with all coverage items (D1-D3 for plan 01, D1-D3 for plan 02) passing, and the repo has already been published (verified: `gh repo view` reports `PUBLIC`, `origin/main` matches the pre-final local commit). Tools/agents that read `ROADMAP.md`'s status table (e.g. `gsd-progress`, `gsd-next`) to decide what phase to work on next will see Phase 7 as not-yet-done.

**Fix:** Update `.planning/ROADMAP.md` line 26 to `- [x]` and line 155 to `| 7. Hygiene & Publication | 2/2 | Complete | 2026-08-16 |`, matching the pattern used for Phases 5 and 6 in the same table.

---

_Reviewed: 2026-08-16T14:44:21Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
