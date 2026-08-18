---
phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly
reviewed: 2026-08-18T21:48:52Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - .claude-plugin/marketplace.json
  - .gitignore
  - .gsd-capabilities.json
  - .gsd/capabilities/markdown-linting/ (removed by this phase)
  - .gsd/capabilities/pr-workflow/ (removed by this phase)
  - .planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-01-SUMMARY.md
  - .planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-02-SUMMARY.md
  - .planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-03-SUMMARY.md
  - .planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-04-SUMMARY.md
  - .planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-05-SUMMARY.md
  - .planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-GATE-REPROOF.md
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-08-18T21:48:52Z
**Depth:** standard
**Files Reviewed:** 11 (3 tracked config files touched in gsd-beads, 2 bundle trees removed, 6 planning docs)
**Status:** issues_found

## Summary

Phase 15's footprint inside `gsd-beads` itself is small and mechanical: append two `url`-type
entries to `.claude-plugin/marketplace.json`, delete two now-dangling un-ignore lines from
`.gitignore`, delete the `pr-workflow` entry from `.gsd-capabilities.json`, and `git rm -r` the two
extracted capability bundles (`.gsd/capabilities/markdown-linting/`, `.gsd/capabilities/pr-workflow/`).
The substantive plugin-tree code (manifests, hooks, README, CI) that these entries point at lives in
two brand-new external repos and is out of scope per the review brief.

Cross-checked the removal commit (`1e2ef59`) and the marketplace-append commit (`2b3d46d`) against
`git show --stat` / `git show -- <path>` directly rather than trusting the SUMMARYs' own narration:
both diffs are exactly as purely additive/subtractive as claimed, an exhaustive
`git ls-files -z | xargs grep` sweep for both capability ids across the whole tracked tree turns up
only the three files the SUMMARYs already enumerate, `.github/workflows/ci.yml` and `release.yml`
reference neither id and were correctly left untouched, and `git ls-files .gsd/` is empty post-removal
(nothing under `.gsd/` remains tracked). No orphaned reference, no broken path, no leftover dead
config was found.

Two genuine, provable defects were found, both introduced by commit `1e2ef59`: a stale ledger
timestamp that bypassed the ledger's own write-path invariant, and an unpinned supply-chain surface
on the two newly-added `url` marketplace sources (an existing pattern in this file, but one this
phase doubled the exposure of, so it is called out rather than waved through). One documentation
staleness item is Info-level. No Critical findings.

## Warnings

### WR-01: `.gsd-capabilities.json`'s `updatedAt` was not bumped when the `pr-workflow` entry was deleted

**File:** `.gsd-capabilities.json:3`
**Issue:** Commit `1e2ef59` hand-edited `.gsd-capabilities.json` to delete the `pr-workflow` entry
(`git show 1e2ef59 -- .gsd-capabilities.json` confirms a clean 10-line removal, entry only). It left
`"updatedAt": "2026-08-18T17:40:20.232Z"` untouched. That value is a timestamp from *before* the
entry it now claims currency over was removed — every prior mutation of this file in the repo's
history (`git log -p -- .gsd-capabilities.json`) shows `updatedAt` bumped on every single edit,
because the file is normally written through `~/.claude/gsd-core/bin/lib/capability-ledger.cjs`,
whose mutation functions unconditionally set `ledger.updatedAt = new Date().toISOString()` on every
add/remove (lines 722, 726, 747 of that file) — that is the invariant this file's schema is designed
to uphold, and this commit's manual edit broke it. The ledger's own validator only checks that
`updatedAt` is a non-empty string (lines 246, 370), so nothing will flag this at write time, but any
downstream logic that treats `updatedAt` as "last time this ledger's contents actually changed"
(staleness checks, cache-busting, audit dating) now reads a value that is stale by construction for
this entry deletion.
**Fix:** Re-run the removal through `capability-ledger.cjs`'s own remove/mutate path instead of a
hand-edit, or at minimum bump `updatedAt` to the commit's actual timestamp when hand-editing this
file:
```diff
-  "updatedAt": "2026-08-18T17:40:20.232Z",
+  "updatedAt": "2026-08-18T21:40:12.000Z",
```

### WR-02: Two new `url`-type marketplace sources have no ref/sha/tag pin

**File:** `.claude-plugin/marketplace.json:30-45`
**Issue:** The `markdown-linting` and `pr-workflow` entries added by this phase are:
```json
{ "name": "markdown-linting", "source": { "source": "url", "url": "https://github.com/davdittrich/markdown-linting.git" }, ... }
```
with no `ref`, `sha`, or `tag` field. Every `claude plugin install .../markdown-linting@gsd-beads` (or
`pr-workflow@gsd-beads`) resolves whatever commit is on that repo's default branch at install time —
there is no pin recorded anywhere in this manifest and no integrity check performed. This mirrors the
pre-existing `ponytail-everywhere`/`sota-numerics` entries in the same file (same shape, same gap), so
it is not a regression unique to this change, but this phase doubles the number of unpinned external
git sources this marketplace vouches for, and the phase's own design intent (D-10, "validated,
round-tripped, reproducible install") is weakened by the fact that nothing here fixes *which* commit
was validated to the commit that will actually be fetched on a future install. A force-push, account
compromise, or accidental bad push to either new repo's `main` silently changes what every consumer
gets, with no version pin or hash to detect drift.
**Fix:** If the marketplace source schema supports a `ref`/`sha` field (worth checking against
`claude plugin` docs), pin both new entries to the exact commit each SUMMARY already records as
verified (`d30ab57` for markdown-linting, `0dc4855` for pr-workflow) rather than tracking `main`
unpinned. If the schema does not support pinning, this is a systemic gap worth a follow-up ticket
against all four `url`-type entries, not just these two.

## Info

### IN-01: `.gitignore`'s capability-ignore comment now describes a dormant mechanism

**File:** `.gitignore:36-37`
**Issue:** The block comment ending "...Ignore capability subdirectories by default, then explicitly
un-ignore each capability actively being dogfooded in this repo right now" was written when two
`!.gsd/capabilities/<id>/` un-ignore lines existed under it. Commit `1e2ef59` deleted both un-ignore
lines (by design — `.gsd-beads` no longer dogfoods either capability in-tree) but left the comment
verbatim, per the SUMMARY's explicit intent ("block and its explanatory comment unchanged"). The
comment is not factually wrong (it still correctly describes the *mechanism*), but it now reads as if
an active un-ignore is in effect directly above it when there are currently zero — a future reader
skimming for a live example of the pattern will find none.
**Fix:** Optional: append one clause noting the block is currently dormant (no capability presently
uses it), e.g. "...right now (none currently do — this block activates again the next time a
capability is dogfooded in-repo before extraction)."

---

_Reviewed: 2026-08-18T21:48:52Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
