---
phase: 18-address-tech-debt-patch-check-doc-accuracy-changelog
plan: 02
subsystem: release-hygiene
tags: [bd, git-tags, release-hygiene, beads-issue-closure]
dependency-graph:
  requires: []
  provides:
    - "four stale Phase 17 bd issues closed (gsd-beads-he1, gsd-beads-bzl, gsd-beads-v43, gsd-beads-t7a)"
    - "withdrawn v1.3.0 tag removed from origin and local"
  affects:
    - "beads.ship_gate — removes 3 P1 blocking-open issues that risked blocking Phase 18's ship step"
    - "ROADMAP.md Phase 17 Ship-step check #3 (withdrawn-tag/release.yml collision)"
tech-stack:
  added: []
  patterns:
    - "identity-verified bd close: bd show before bd close, matched against a written id-to-TRUTH mapping table"
    - "remote-before-local tag deletion ordering (partial-failure leaves intent recorded)"
key-files:
  created: []
  modified: []
decisions:
  - "Task 2 checkpoint answered option-a by the user: delete v1.3.0 from origin AND locally (not option-b keep-local, not option-c document-and-keep)"
metrics:
  duration: "~45min (includes one mid-plan worktree-recreation recovery cycle)"
  completed: 2026-08-20
status: complete
actuals:
  tokens: 2260
  tasks: 3
  commits: 1
---

# Phase 18 Plan 02: Close stale Phase 17 bd issues + delete withdrawn v1.3.0 tag Summary

Closed four already-shipped Phase 17 bd issues that `execute:wave:post` never auto-closed
(identity-verified against TRUTH-01..04 before each close), filed a follow-up issue for the
mechanism gap that caused them to go stale, and deleted the withdrawn `v1.3.0` git tag from
`origin` and locally after explicit user confirmation at a blocking checkpoint.

## What Was Built

This plan creates no repository files and no code symbols — both tasks are external-system
state changes only (`bd` issue store, `git` ref state on `origin`).

### Task 1 — Closed four stale Phase 17 issues, identity-verified

Ran the D-09 backstop first, from the main tree (`.beads/` is gitignored and this worktree's
copy is empty — every `bd` call in this plan targeted `-C /home/dd/projects/gsd-beads`, the
real database):

```
python3 plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py reconcile-stale-closed .planning/phases/17-config-code-truth
→ Closed 0 issue(s) across 4 plan(s) in 17-config-code-truth; skipped 0 task(s) with no beads-id
```

Expected result, not a failure: `reconcile_stale_closed` resolves its candidate set through
`_resolve_completed_task_ids` (`sync.py:1339-1348`), the union of every `<beads-id>` across a
phase's `PLAN.md` files. Phase 17's set is `gsd-beads-u67.1`..`.11`, all already closed. The four
target issues are standalone problem reports (created 2026-08-19, no `<beads-id>` in any
`PLAN.md`), so the backstop cannot reach them by construction — confirmed by reading
`_resolve_completed_task_ids` and `reconcile_stale_closed` before running it, not assumed.

Then verified identity via `bd show <id>` on each of the four before closing — every title
matched the plan's mapping table exactly, no mismatch:

| Issue | Confirmed subject | Shipped by | Close reason |
|-------|-------------------|-----------|---------------|
| `gsd-beads-he1` | hook double-dispatch of `plan:post`/`verify:post` once PR #3687 ships (TRUTH-03) | plan 17-02 | "shipped in Phase 17 plan 17-02 (TRUTH-03); never auto-closed at execute:wave:post" |
| `gsd-beads-bzl` | decimal phases break `PLAN_FILE_RE`, `int(phase_num)` (TRUTH-04) | plan 17-01 | "shipped in Phase 17 plan 17-01 (TRUTH-04); never auto-closed at execute:wave:post" |
| `gsd-beads-v43` | `beads.sync_mode` declared in `capability.json` but read by nothing (TRUTH-01) | plan 17-03 | "shipped in Phase 17 plan 17-03 (TRUTH-01); never auto-closed at execute:wave:post" |
| `gsd-beads-t7a` | `check_shipmd_patch`/`check_execute_plan_patch` structural clones (TRUTH-02) | plan 17-04 | "shipped in Phase 17 plan 17-04 (TRUTH-02); never auto-closed at execute:wave:post" |

All four closed via `bd close <id> --reason "..."`. Confirmed via `bd show <id> --json`'s
`"status"` field: all four report `"closed"`.

**Verify command note:** the plan's own literal automated verify command
(`bd list --status open,in_progress,blocked --exclude-type epic --json -n 0 | grep -c -E
'gsd-beads-(he1|bzl|v43|t7a)'`) returns 2, not 0, when run after closure. This is a false
positive, not a real divergence: the still-open plan-task issue `gsd-beads-0lu.4` (this task's own
bd ticket) quotes all four target ids verbatim inside its own `description` field (the id-to-TRUTH
mapping table copied into the task text), so the grep matches that unrelated open issue's body.
Direct per-id `bd show <id> --json` status-field checks are unambiguous and confirm all four are
`"closed"` — used as the authoritative check instead.

Idempotence verified: re-running `bd close` on all four already-closed ids succeeded (exit 0,
no error) each time.

Filed the required follow-up issue **`gsd-beads-72u`** — "reconcile_stale_closed cannot reach
standalone problem-report issues with no `<beads-id>`" (P3, bug) — naming `reconcile_stale_closed`
and `_resolve_completed_task_ids` by name and citing this plan, per the task's mandatory action.
Not fixed here — out of Phase 18's boundary, ticketed per the project's follow-up rule.

### Task 2 — Checkpoint: confirm deleting the withdrawn v1.3.0 tag

Blocking `checkpoint:decision` surfaced to the user with the plan's full options/pros/cons
(option-a: delete from origin+local / option-b: delete from origin, keep local / option-c: keep
tag, document withdrawal in CHANGELOG instead). **User answered option-a** — delete from `origin`
AND locally, as D-07 specifies.

### Task 3 — Deleted the tag (option-a)

Confirmed `release.yml`'s trigger before acting: `on: push: tags: ['v*.*.*']`, no job keys off a
specific tag name (`.github/workflows/release.yml:3-6`).

Baseline recorded before deletion:
```
70f4c37a...  refs/tags/v1.3.0
55855cd9432adab96a2ff644fc0362965a0b9c6d  refs/tags/v1.3.0^{}   <- dereferenced commit
4a9be6ff...  refs/tags/v1.3.1
049da5b9...  refs/tags/v1.3.1^{}
```

Executed in the required order — remote first, then local:
```
$ git push origin :refs/tags/v1.3.0
 - [deleted]         v1.3.0
$ git tag -d v1.3.0
Deleted tag 'v1.3.0' (was 70f4c37)
```

No `--force`, no bulk tag push, no tag created, `v1.3.1` untouched throughout.

**The withdrawn version's commit, for the record now that the ref is gone: `55855cd`**
(`refs/tags/v1.3.0^{}` before deletion — the annotated tag's dereferenced target).

**Post-deletion verification (all passed):**
- `git ls-remote --tags origin | grep -c 'refs/tags/v1\.3\.0'` → `0` (was 2 before)
- `git ls-remote --tags origin | grep -c 'refs/tags/v1\.3\.1'` → `2`, unchanged — surviving tag untouched
- `git tag -l v1.3.0` → empty; `git tag -l v1.3.1` → `v1.3.1`
- `gh release list` → `v1.3.1` (Latest), `v1.2.0`, `v1.1.1` — no `v1.3.0` release (was already gone before this task), no new release created
- `gh run list --workflow release.yml --limit 3` → byte-identical to the pre-deletion baseline (same 3 runs, same timestamps: `v1.3.1`, `v1.3.0`, `v1.2.0`) — confirms the deletion push fired zero `release.yml` runs, as the one-way rating's stated boundary predicted

## Deviations from Plan

### Auto-fixed Issues

None — plan executed as written for both tasks' actions.

### Infrastructure recovery (not a plan deviation, documented per orchestrator instruction)

Between the Task 2 checkpoint pause and this resume, this agent's assigned git worktree
(`agent-a8484719cf34ee198`) was found to have been entirely removed (directory and
`.git/worktrees/` metadata both gone) — an orchestrator-side lifecycle event unrelated to this
plan's own actions. Per the plan's `worktree_branch_check` protocol, execution halted rather than
self-recovering (no commit attempted on `main`, no worktree reconstruction attempted locally).
The orchestrator recreated the worktree at the same path/branch/base
(`ae8ce6c599d7f0d2467e7e1b894785d7881b655c`) and confirmed Task 1's `bd`-state work remained
durable (`bd` state lives in the real project database, independent of worktree lifecycle, and
was independently re-verified by the orchestrator before resuming). The re-run
`worktree_branch_check` passed cleanly against the recreated worktree before Task 3 proceeded.

### Auth gates

None encountered.

## Known Stubs

None.

## Self-Check: PASSED

- Commits verified: `git log --oneline -3` on `worktree-agent-a8484719cf34ee198` shows the
  SUMMARY.md commit at HEAD, correct branch, correct parent (`ae8ce6c`).
- `bd -C /home/dd/projects/gsd-beads show gsd-beads-he1/bzl/v43/t7a --json` — all four `"status": "closed"`.
- `bd -C /home/dd/projects/gsd-beads show gsd-beads-72u` — exists, open, P3.
- `git ls-remote --tags origin` — no `refs/tags/v1.3.0`, `refs/tags/v1.3.1` present twice.
- `git tag -l v1.3.0` — empty. `git tag -l v1.3.1` — `v1.3.1`.
- `gh run list --workflow release.yml --limit 3` — unchanged from pre-deletion baseline.
