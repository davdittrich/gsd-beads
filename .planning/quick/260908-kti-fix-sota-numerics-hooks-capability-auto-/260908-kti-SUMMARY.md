---
phase: quick-260908-kti
plan: 01
subsystem: sota-numerics/hooks
tags: [security, symlink, toctou, capability-auto-install]
dependency-graph:
  requires: [gsd-beads-25vc.21.2]
  provides: [gsd-beads-25vc.21.6]
  affects: [hooks/capability-auto-install.sh, tests/test-capability-auto-install.sh]
tech-stack:
  added: []
  patterns: ["-L guard before cat on an attacker-writable sidecar path"]
key-files:
  created: []
  modified:
    - /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/hooks/capability-auto-install.sh
    - /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/tests/test-capability-auto-install.sh
    - /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013/CHANGELOG.md
decisions:
  - "OLD_HASH read gated with `[ ! -L \"$STATE_FILE\" ] && [ -r \"$STATE_FILE\" ]` in the same one-line && chain, no if-block, matching the file's existing style."
  - "Stale write-side comment naming gsd-beads-25vc.21.6 as unfixed deleted; the unlink-and-recreate race paragraph above it kept verbatim."
metrics:
  duration: "~25min"
  completed: 2026-09-08
status: complete
commits: 1
plan_head_before: ce855f9140ff1765c6ed176a816ac046da85750d
actuals:
  tokens: 1431
  tasks: 1
  commits: 1
---

# Quick Task 260908-kti: Guard the sidecar read against a planted symlink Summary

Closed `gsd-beads-25vc.21.6` in the `sota-numerics` worktree: `hooks/capability-auto-install.sh`'s `OLD_HASH` read no longer follows a symlink planted at the sidecar path, pinned by new regression case I7.

## What Changed

`hooks/capability-auto-install.sh:127` previously read `STATE_FILE` (the per-capability hash sidecar under `${GSD_HOME:-$HOME}/.gsd/`) with only a `-r` (readable) test. A symlink at that path pointing at a file holding the bundle's *current* digest was therefore readable, so `OLD_HASH` picked up the forged value, matched `NEW_HASH` at the fast-path check, and the hook exited without installing — an attacker with write access to `.gsd/` could suppress auto-install indefinitely without touching the bundle itself.

The fix adds a `! -L "$STATE_FILE"` test to the same `&&`-joined one-liner in front of the existing `-r` test and assignment, so a symlinked sidecar is read as "no recorded hash" (fail-safe: causes an install, not a skip) rather than followed. `OLD_HASH=""` (line 126) and the fast-path/failure-handling code below (lines 128-135) were untouched, as scoped.

The stale comment in the success branch (previously lines 319-324) that described the read as "not fixed here; tracked as gsd-beads-25vc.21.6" was deleted — it is false once the guard lands. The paragraph above it, describing the surviving unlink-and-recreate TOCTOU window on the write side, was left exactly as written; that residual is still real and unrelated to this fix.

`CHANGELOG.md`'s existing `## 0.2.0` sidecar paragraph gained one sentence covering the read side, matching its existing voice, without a new version heading (0.2.0 remains unreleased).

## TDD Evidence

**RED** (case I7 added, hook unchanged): `bash tests/test-capability-auto-install.sh` reported exactly one failure —
```
FAIL: I7: a sidecar symlink holding the real hash took the fast path
...
1 FAILED
```
`installs` stayed at `1` after the second `run_hook`, confirming the unguarded `cat` followed the planted link, read the real hash into `OLD_HASH`, matched `NEW_HASH`, and exited at the fast path without installing — red for the reason the plan specified, not an inert assertion.

**GREEN** (hook fix applied): all four CI commands pass —
```
PASS: I7: the OLD_HASH read refuses a symlinked sidecar even when its target holds the real hash
...
ALL PASS
```
- `bash tests/test-session-start.sh` — `ALL PASS`
- `bash tests/test-capability-auto-install.sh` — `ALL PASS`, including I1 (regular-file fast path, unchanged), I6 (write-side symlink guard, unchanged), and I7 (new)
- `bash tests/test-gate-script-resolution.sh` — `ALL PASS`
- `python3 -m unittest tests/test_check_alternatives.py` — `Ran 131 tests ... OK`

## Verification Beyond Green

- `grep -n 'OLD_HASH=' hooks/capability-auto-install.sh | grep -q -- '-L'` — guard present.
- `grep -c 'gsd-beads-25vc\.21\.6' hooks/capability-auto-install.sh` = `0` — no remaining ticket reference in the file.
- `git status --porcelain` empty after commit — clean worktree, one commit.
- `git show --name-only --format= HEAD` = `CHANGELOG.md`, `hooks/capability-auto-install.sh`, `tests/test-capability-auto-install.sh` — no path under `.gsd/` touched, so the D-17 install-mirror bundle hash the plugin-scaffolding hook compares against does not move and no machine-wide reinstall is triggered by this commit.

## STRIDE Residual Register (from PLAN.md threat_model, unchanged by this fix)

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-kti-01 | Spoofing | `OLD_HASH` read, `capability-auto-install.sh:127` | low | mitigate | Read the sidecar only when it is not a symlink, so a planted link cannot supply a forged "already installed" digest; pinned by case I7. **Closed by this commit.** |
| T-kti-02 | Tampering | `[ ! -L ]` then `cat`, same line | low | accept | Two syscalls cannot be made one in shell; no `O_NOFOLLOW` is available. Same window already accepted on the write side, and the threat model already grants the attacker write access to that directory. Recorded in the code comment, not claimed away. |
| T-kti-03 | Denial of Service | fast path, `capability-auto-install.sh:135` | low | accept | A link left in place makes every session reinstall until the first success replaces it with a regular file. Reinstalling is the safe direction and self-heals in one run. |

## Deviations from Plan

None — plan executed exactly as written. Task type was `tracer`; no expansion task exists in this single-task plan, so no tracer feedback gate applied beyond the plan's own `<verify>` block, which was run in full.

## Commits

- `f46ebc3` (sota-numerics, `feat/extended-sota-definition`, not pushed): `fix(hooks): read the sidecar only when it is a regular file`

## Known Stubs

None.

## Threat Flags

None — this change closes an existing threat register entry (T-kti-01) rather than introducing new surface.

## Self-Check: PASSED
