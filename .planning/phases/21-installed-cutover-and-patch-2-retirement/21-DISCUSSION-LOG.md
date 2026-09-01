# Phase 21: Installed Cutover and Patch 2 Retirement - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-01
**Phase:** 21-installed-cutover-and-patch-2-retirement
**Areas discussed:** Cutover transaction, Live proof task, Negative-path matrix, Historical references

---

## Cutover transaction

| Option | Description | Selected |
|--------|-------------|----------|
| One fresh fail-closed transaction | Re-observe all gates at one exact SHA immediately before retirement; exact runtime rollback on post-removal failure. | ✓ |
| Accumulate evidence across runs | Accept prior hashes, registry output, or test results as current cutover evidence. | |
| Continue with warnings | Remove Patch 2 despite a failed or indeterminate gate. | |

**User's choice:** Delegated to Ponytail, scientific-critical-thinking, Beads, and codebase-design; selected one fresh fail-closed transaction.
**Notes:** Project/global overlay precedence and stale installed copies make cross-run evidence confounded.

---

## Live proof task

| Option | Description | Selected |
|--------|-------------|----------|
| First naturally synced Phase 21 task | Use the first exact auto/tracer task created by normal plan:post sync and its live Beads row. | ✓ |
| Existing Phase 20 task | Reuse a prior task regardless of its current plan identity. | |
| Synthetic fixture task | Create or replay a special task solely for cutover proof. | |

**User's choice:** Delegated; selected the naturally synced Phase 21 task.
**Notes:** Direct inspection found no persisted native identity in the current Phase 20 task opening tags. Global proof must run outside repository ancestry so the project overlay cannot satisfy it.

---

## Negative-path matrix

| Option | Description | Selected |
|--------|-------------|----------|
| Four public arms plus existing unit matrix | Unknown id, legacy-only plan, unavailable bd, and malformed stdout at the public command; keep Phase 19's deeper unit matrix. | ✓ |
| Repeat every unit failure publicly | Rebuild the entire adapter failure suite at installed-command level. | |
| Minimal unavailable-bd check | Treat one failure class as sufficient for all negative behavior. | |

**User's choice:** Delegated; selected the discriminating public matrix.
**Notes:** Every arm changes one factor from a known-good baseline and must exit nonzero without resolved or fallback content.

---

## Historical references

| Option | Description | Selected |
|--------|-------------|----------|
| Zero active residue, preserve history | Delete operational Patch 2 code, markers, calls, tests, and instructions while retaining historical records. | ✓ |
| Keep compatibility residue | Retain an alias, inert marker, tombstone command, or fallback branch. | |
| Purge all mentions | Rewrite changelogs, archived plans, issues, and Git history. | |

**User's choice:** Delegated; selected zero active residue with preserved historical truth.
**Notes:** Patch 1 remains byte-preserved and independently verified; no adjacent checker redesign.

## the agent's Discretion

- Exact test names and diagnostic wording.
- Deterministic whole-tree byte-comparison command.
- Supported runtime-derived live database locator used outside repository ancestry.

## Deferred Ideas

None.
