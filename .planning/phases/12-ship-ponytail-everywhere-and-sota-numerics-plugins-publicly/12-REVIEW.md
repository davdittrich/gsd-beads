---
phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
reviewed: 2026-08-17T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - .claude-plugin/marketplace.json
  - .github/workflows/ci.yml
  - .github/workflows/release.yml
  - hooks/capability-auto-install.sh
findings:
  critical: 0
  warning: 1
  info: 1
  total: 2
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-08-17
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the four gsd-beads-side files touched by the extraction of `ponytail-everywhere/` and `sota-numerics/` into standalone public repos: the marketplace repoint, the two CI/release workflow repairs, and the two stale-comment fixes in the vendored hook script.

Verified against the pre-removal (`82b55ac`) version of `.github/workflows/release.yml`: the original `zip` step listed 9 arguments; exactly the 3 naming the removed `ponytail-everywhere/` tree (`ponytail-everywhere/.claude-plugin`, `ponytail-everywhere/hooks`, `ponytail-everywhere/.gsd`) were dropped, and the remaining 6 (`.claude-plugin`, `hooks`, `.agents/skills`, `.gsd`, `README.md`, `LICENSE`) are unchanged — matches the plan's claim exactly. `ci.yml` correctly drops the two subdirectory-testing steps (vendored-copy parity, ponytail-everywhere session-start smoke test) and keeps the one step (`bash tests/test-capability-auto-install.sh`) that doesn't reference either removed tree — confirmed `tests/test-capability-auto-install.sh` is self-contained (mktemp scratch root, stub `gsd-tools`) and never referenced `ponytail-everywhere/`. Grepped the working tree for any remaining `ponytail-everywhere/` path references outside `.planning/` — none found; the comment repairs in `hooks/capability-auto-install.sh` are the only prose that needed updating and both were updated correctly with zero executable-line changes.

`marketplace.json`'s two `source` blocks were converted from local relative paths to `{"source": "github", "repo": "davdittrich/..."}` objects — syntactically valid JSON, and per 12-04-SUMMARY.md this was verified against the real, pushed marketplace via an actual install/uninstall round trip for both plugins, not just visual inspection.

No blocking defects found in this scope. One warning: the drift-detection mechanism this repo used to rely on (byte-identical vendored copy across repos) is now unenforced anywhere. One info-level note on supply-chain pinning.

## Warnings

### WR-01: No CI mechanism verifies the two hook copies stay byte-identical after extraction

**File:** `.github/workflows/ci.yml:13` (removed step), cross-referenced with `hooks/capability-auto-install.sh:2-4`
**Issue:** Before this phase, `ci.yml` ran a "Vendored-copy parity (D-06 / CAP-07)" step that `cmp`'d `hooks/capability-auto-install.sh` against `ponytail-everywhere/hooks/capability-auto-install.sh` and diffed the two `.gsd/capabilities/ponytail` bundles, mechanically enforcing D-05 ("vendored copy per plugin ... byte-identical sibling copy"). That step was deleted (correctly, since the sibling file no longer lives in this repo) but nothing replaces it. `hooks/capability-auto-install.sh`'s own comment still asserts a "byte-identical sibling copy" exists in `davdittrich/ponytail-everywhere`, but that claim is now unverifiable from either repo's CI — a future edit to either copy can silently drift with no automated signal in either repository.
**Fix:** If D-05's byte-identical invariant still matters, add a scheduled or on-push cross-repo check (e.g. a workflow in `davdittrich/ponytail-everywhere` that fetches `davdittrich/gsd-beads`'s `hooks/capability-auto-install.sh` via raw GitHub URL and `cmp`s it), or downgrade the comment to note the invariant is no longer CI-enforced so a future reader doesn't trust a claim nothing checks.

## Info

### IN-01: marketplace.json github sources are unpinned (track mutable branch HEAD)

**File:** `.claude-plugin/marketplace.json:16-19, 24-27`
**Issue:** Both new `source` objects (`{"source": "github", "repo": "davdittrich/ponytail-everywhere"}` / `sota-numerics`) have no `ref`/tag/commit pin. Every `claude plugin install ponytail-everywhere@gsd-beads` resolves to whatever is currently on the default branch of the external repo at install time — a push to either standalone repo changes installed behavior for gsd-beads marketplace users with no corresponding commit or review in gsd-beads itself.
**Fix:** If reproducible installs matter, pin to a tag/ref once each standalone repo cuts a first release (e.g. `"ref": "v1.0.0"`), bump it deliberately when the extracted plugin changes. Low urgency while both repos are single-owner and immature.

---

_Reviewed: 2026-08-17_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
