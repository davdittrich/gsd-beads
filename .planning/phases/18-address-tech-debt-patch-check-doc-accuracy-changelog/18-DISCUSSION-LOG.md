# Phase 18: Address tech debt: patch-check doc accuracy + CHANGELOG - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-20
**Phase:** 18-address-tech-debt-patch-check-doc-accuracy-changelog
**Areas discussed:** WR-02 fix mechanism, WR-03 CHANGELOG scope, Phase 18 outer boundary, WR-01 fix depth

---

## WR-02 fix mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Prefix messages with ⚠ | Add "⚠ " to not_found_msg/could_not_read_msg in both PATCH_CHECKS entries — sync.py only | |
| Broaden SKILL.md to key off exit code | Change both SKILL.md files' instruction to key off exit code instead of a "⚠" substring grep | |
| Both | Prefix the messages AND broaden the SKILL.md instruction | ✓ |

**User's choice:** Both
**Notes:** None.

---

## WR-03 CHANGELOG scope

| Option | Description | Selected |
|--------|-------------|----------|
| 0.4.0 TRUTH-03 entry only | Add the missing 0.4.0 entry for check_native_step_dispatch / PR #3687 only | |
| Also fix the 0.3.1 miscategorization | Additionally move the 120s hook-timeout entry from Performance to Fixed/Changed | ✓ |

**User's choice:** Also fix the 0.3.1 miscategorization
**Notes:** This decision turned out to be the same underlying fix as ROADMAP.md's Phase 17 "Ship-step checks" item #2 — surfaced immediately after in the outer-boundary question.

---

## Phase 18 outer boundary

| Option | Description | Selected |
|--------|-------------|----------|
| No — stay on WR-01/02/03 only | Leave the other 3 release-hygiene items to Phase 17's ship-step checks | |
| Yes — fold all 4 release-hygiene items in too | Phase 18 absorbs both the review's tech debt and the ship-time hygiene checklist | ✓ |

**User's choice:** Yes — fold all 4 release-hygiene items in too

Follow-up questions asked once the boundary was widened:

**Withdrawn v1.3.0 tag:**

| Option | Description | Selected |
|--------|-------------|----------|
| Delete the tag from origin | git push origin :refs/tags/v1.3.0 + local delete | ✓ |
| Keep the tag, document the withdrawal | Add a CHANGELOG line stating v1.3.0 is withdrawn and why | |

**User's choice:** Delete the tag from origin

**Stale local ship.md v1 patch:**

| Option | Description | Selected |
|--------|-------------|----------|
| Refresh the backup to v2 | Update ~/.claude/gsd-local-patches/ to match live v2 ship.md patch | ✓ |
| Delete the stale backup | Remove the local patch backup outright | |

**User's choice:** Refresh the backup to v2

**Notes:** ROADMAP.md item #5 (test-count/tree-identity assertion) was explicitly kept out — it's a ship-time verification action, not a phase deliverable.

---

## WR-01 fix depth

| Option | Description | Selected |
|--------|-------------|----------|
| Docstring + pinning comment | Rewrite the docstring AND add a pinning comment on check_patch's print() call | ✓ |
| Docstring only | Just correct the false claim in the docstring | |

**User's choice:** Docstring + pinning comment
**Notes:** None.

---

## the agent's Discretion

- Exact wording of the WR-01 docstring rewrite and pinning comment.
- Exact new `plugin.json` version number (minor vs. patch bump).
- Whether the `plugin.json` version bump lands in its own commit or folds into the CHANGELOG task.

## Deferred Ideas

- None outside the phase boundary — all 4 areas stayed within tech-debt/release-hygiene scope.
