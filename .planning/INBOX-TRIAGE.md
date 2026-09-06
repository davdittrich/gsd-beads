# GSD Inbox Triage — davdittrich/gsd-beads — 2026-08-30

## Scope

- Target: [davdittrich/gsd-beads#6](https://github.com/davdittrich/gsd-beads/issues/6)
- Mode: report only
- Open issues reviewed: 1 of 2
- Open pull requests checked for gate linkage: 0

## Standards discovered

The default branch has no issue templates, pull-request templates, or
`CONTRIBUTING.md`; `.github/` contains only `workflows/`. Consequently, there
is no repository-defined submission checklist against which issue #6 can fail
compliance. The advisory score below uses the generic GSD enhancement checklist.

Confidence: 100/100 — confirmed from the live default-branch tree.

## Gate violations

None. The repository has no open pull requests, and issue #6 has no pull-request
cross-reference.

Confidence: 100/100 — confirmed from the live open-PR list and issue timeline.

## Issue review

### #6 [Enhancement] Native task-content resolver migration

- Repository compliance: **PASS**
- Generic GSD completeness: **89% (8/9) — MOSTLY COMPLETE**
- Labels: none
- Suggested labels: `enhancement`; `needs-triage` until maintainer review
- Created: 2026-08-30T12:44:33Z
- Updated: 2026-08-30T12:44:33Z
- Age: 0 days

Present:

- Improvement target is exact: replace Patch 2 with gsd-core's native
  `taskContentResolver` seam.
- Current behavior and failure mechanism are concrete: the body states that the
  1.11.0 to 1.12.0 update produced a merge conflict and explains why it recurs.
- Proposed behavior is concrete: declare the resolver, emit
  `tracker-id="beads:<issue-id>"`, retain `<beads-id>` during migration, and
  exclude `checkpoint:*` tasks.
- Benefit is explicit: retire an upstream workflow patch and its recurring
  conflict while using the upstream-validated capability declaration.
- Scope names the capability manifest, sync script, patch inventory and wiring,
  changelog, and inventory documentation; Patch 1 is explicitly out of scope.
- Compatibility is addressed by retaining `<beads-id>` and leaving checkpoint
  tasks untouched.
- Alternatives are compared implicitly: retaining Patch 2 versus adopting the
  native resolver seam, with the recurring-conflict cost of the former stated.
- Verification is testable: successful real-task resolution plus non-zero
  hard-halt behavior for unknown IDs and unavailable `bd`, removal of the Patch
  2 marker, and continued Patch 1 verification.

Advisory gap:

- No four-item pre-submission checkbox block is present. Because the repository
  supplies no issue template, this is not repository non-compliance.

Confidence: 96/100 — the issue body directly supports eight checklist items;
the enhancement classification is semantic because no type label or template
heading exists.

## Ready state

Issue #6 is sufficiently specified for maintainer triage, but it is not marked
approved or ready for implementation. Apply labels only after maintainer review.

Confidence: 100/100 — the live issue has no labels.

## Stale items

None in the requested scope.

Confidence: 100/100 — issue #6 was created and last updated today.
