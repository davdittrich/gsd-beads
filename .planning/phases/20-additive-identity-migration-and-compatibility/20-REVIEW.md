---
phase: 20-additive-identity-migration-and-compatibility
reviewed: 2026-09-01T09:27:54Z
reviewed_sha: 9fc842cd27637316228260bb118f3c8ddf8c0597
depth: deep
files_reviewed: 17
files_reviewed_list:
  - plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/fixtures/plan-single.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/fixtures/plan-synced.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md
  - plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json
  - plugins/beads-lifecycle/.agents/skills/beads/PRIME.md
  - plugins/beads-lifecycle/.claude-plugin/plugin.json
  - plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh
  - plugins/beads-lifecycle/hooks/hooks.json
  - README.md
  - .github/workflows/ci.yml
  - .github/workflows/release.yml
  - .planning/phases/20-additive-identity-migration-and-compatibility/20-CONTEXT.md
  - .planning/phases/20-additive-identity-migration-and-compatibility/20-01-PLAN.md
  - .planning/phases/20-additive-identity-migration-and-compatibility/20-01-SUMMARY.md
  - .planning/phases/20-additive-identity-migration-and-compatibility/20-SECURITY.md
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 20: Code Review Report

**Reviewed:** 2026-09-01T09:27:54Z
**Reviewed SHA:** `9fc842cd27637316228260bb118f3c8ddf8c0597`
**Depth:** deep
**Status:** clean

## Verdict

Phase 20 is clean at the reviewed SHA. The final fix closes the remaining
milestone-title authority gap without changing valid forward-only behavior.
No correctness, security, standards, specification, integration, release, or
over-engineering finding remains. Review confidence: **99/100**.

## Findings

None.

## Exact Authority Evidence

The milestone-specific consumer now separates malformed successful authority
from a genuine nonempty title mismatch:

```python
candidate_title = row.get("title")
if not isinstance(candidate_title, str) or not candidate_title.strip():
    raise EpicAuthorityError(
        f"bd show returned invalid title for {candidate_id!r}"
    )
if candidate_title == title:
    return candidate_id
```

This is at
`plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1369-1375`.
It preserves exact comparison after validating that the live title is usable.

The shared row helper at lines 1394-1413 accepts either the live one-row list or
the optional `data` envelope, then requires exactly one object whose `id`
matches the requested ID. Nonzero `bd show` remains absence; malformed JSON,
direct dictionaries without the envelope, zero/multiple rows, non-object rows,
and mismatched IDs raise.

Stored task identity reaches the same helper through
`_bd_show_identifies()`. Stored and shared phase epics do likewise through
`resolve_epic()` at lines 1424-1451. The milestone caller alone adds the
title contract, so task/phase consumers are not burdened with fields they do
not need.

## Full-Context Evidence

- Traced all eleven `parse_plan()` consumers: task-file collection,
  prerequisite resolution, milestone candidate discovery, epic task
  collection, completed-task discovery, local/milestone authority preflight,
  `create_issues()`, phase-epic resolution, ordinal mapping, status mapping,
  and wave-status rendering. All remain named-field consumers.
- Traced `parse_beads_epic()` through target preflight, foreign-plan
  preflight, stored epic resolution, and milestone candidate discovery.
  Candidate discovery uses the same syntax/cardinality mechanism as the target
  plan.
- Confirmed unbound milestone mode runs `_milestone_authority_error()` over
  every discovered phase plan before `bd_available()`. Malformed and
  conflicting foreign declarations therefore perform no Beads call and no
  plan write.
- Confirmed stored-epic exact success returns before milestone discovery. A
  stored absence may fall through to configured resolution; malformed
  successful task authority retains its established visible fail-open/no-plan-
  mutation boundary, while malformed successful epic authority returns
  nonzero.
- Traced every mutation path through
  `create_issues() -> resolve_issue()/resolve_epic() -> rewrite_plan()`:
  task/epic create, orphan close, dependency add, and the sole raw-text plan
  writer. Epic authority errors return at lines 2128-2130 before those
  downstream paths.
- Inspected identity, idempotence, malformed-authority, milestone, orphan,
  dependency, availability, lifecycle, and native-parser tests plus both
  fixtures. The new public regression includes empty and whitespace-only
  titles beside missing and numeric cases.
- Inspected README, PRIME, beads-sync skill, capability/plugin metadata, hook
  launcher/configuration, CI, release allowlist, and Phase 20
  context/plan/summary/security contracts. They remain consistent with the
  implementation and phase boundary.
- Active launcher integration is coherent. The hook resolves project, global,
  then plugin scope. The project-installed `sync.py` SHA-256
  `21765705747996956f71f14bd208739ec62fdff9a78717efeff637ea973cfe41`
  matches the exact reviewed source. The global copy differs but is shadowed
  by project-first resolution. The active `gsd_run` parser proof in the suite
  resolves the launcher, derives `plan-document.cjs`, and verifies exact
  eligible identity plus checkpoint `null`.
- CI runs the same stdlib discovery command used here. Release packaging
  allowlists the plugin tree containing this source and its tests.

## Independent Milestone Title Matrix

The public `create_issues()` boundary was exercised against the exact archive
with one foreign `beads_epic: candidate-epic`:

| Live exact-ID title state | Exit | Mutations | Epic creates | Target changed | Result |
|---|---:|---:|---:|---|---|
| missing | 1 | 0 | 0 | no | fail closed |
| `null` | 1 | 0 | 0 | no | fail closed |
| number | 1 | 0 | 0 | no | fail closed |
| list | 1 | 0 | 0 | no | fail closed |
| object | 1 | 0 | 0 | no | fail closed |
| empty string | 1 | 0 | 0 | no | fail closed |
| whitespace-only string | 1 | 0 | 0 | no | fail closed |
| genuine nonempty mismatch | 0 | 2 | 1 | yes | intended forward-only replacement |
| exact title, one-row list | 0 | 1 | 0 | yes | candidate reused; unbound task created |
| exact title, `data` envelope | 0 | 1 | 0 | yes | candidate reused; unbound task created |

The exact-title controls changed the target only to bind the reused epic and
new task; neither created another epic.

## Standards

No documented-standard violation or baseline code smell was found. The fix is
one local predicate at the consumer that owns title semantics and two adjacent
public regression cases. It preserves typed argv, the existing helper, the
single mutation seam, named-field parser compatibility, and the repository's
fail-closed/no-speculative-abstraction rules.

The code-review skill requested parallel Standards and Spec subreviews, but the
shared agent thread limit was full. Both axes were completed directly against
the same exact SHA and full repository context.

## Spec

Phase 20's locked requirements remain satisfied: canonical
`tracker-id="beads:<beads-id>"` projection is additive; legacy identity stays
authoritative; exact `auto`/`tracer` tasks migrate; excluded task types
remain byte-preserved; conflicts and malformed authority halt before mutation;
repeat synchronization stays idempotent; installed cutover remains outside
this phase. No scope creep was introduced by the final one-condition fix.

## Verification

- Exact isolated tree:
  `9fc842cd27637316228260bb118f3c8ddf8c0597`.
- Focused milestone gate:
  `python3 -m unittest discover -s tests -t tests -k milestone` —
  **10/10 passed in 0.009s**.
- Full gate:
  `python3 -m unittest discover -s tests -t tests` —
  **305/305 passed in 9.078s**.
- Complete independent title/list/envelope matrix: all ten arms matched the
  table above.
- `git diff --check 086af2a..9fc842c -- <source> <tests>` passed.
- The final commit changes only the synchronizer and its existing unittest
  module.
- Every exact-SHA archive and diagnostic workspace used only
  `/run/user/1000/codex-scratch-01a0583c-f3f3-76e2-98c3-a0d64094c310`
  and was deleted. Tests ran against the archive, not the dirty main checkout.
  Source and tests were not modified.

## Security and Ponytail

Security verdict: **SECURED**. Typed argv, safe-ID checks, declaration
preflight, exact response cardinality/identity, nonblank milestone title
authority, and pre-mutation error returns cover the reviewed trust boundary.
No new disclosure, command injection, path traversal, or mutation-order issue
was found.

Ponytail verdict: **Lean already. Ship.** The local predicate reuses the
existing consumer and helper; the two table cases are the minimum regression
proof.

`net: -0 lines possible.`

---

_Reviewed: 2026-09-01T09:27:54Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
