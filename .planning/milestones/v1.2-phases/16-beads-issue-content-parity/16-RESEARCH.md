# Phase 16: beads-issue-content-parity - Research

**Researched:** 2026-08-19
**Domain:** GSD lifecycle internals (`sync.py` write-path, `execute-plan.md` read-path, wave-completion hook dispatch reliability)
**Confidence:** HIGH for Priority 1 (D-08 root cause) and Priority 3 (write-path mechanism) — every claim is grounded in a file read or a live `bd`/`git` command this session. MEDIUM for Priority 2 (patch shape) — the target file (`execute-plan.md`) was read in full and the insertion point is unambiguous, but the exact prose the patch should contain is a design choice, not a verified fact.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01: True full inversion — `bd` is the source, `PLAN.md` becomes a pointer for `auto`/`tracer` tasks.** After sync, `gsd-executor` reads a task's `<objective>`/`<action>`/`<verify>`/`<acceptance_criteria>` content from `bd show <task-id>`, not from `PLAN.md`'s `<task>` block. `PLAN.md` retains only `<name>` and `<beads-id>` per task (identity-binding anchor, unchanged mechanism — B4/B5's resolve-by-id-never-title still applies). — **Reversibility:** costly.
- **D-02: Plan-level content stays in `PLAN.md`.** Only *per-task* content (`<objective>`, `<action>`, `<verify>`, `<acceptance_criteria>`, `<read_first>`, `<precondition>`, `<done>`) moves into that task's `bd` description. Plan-level sections that have no natural per-task home — `<threat_model>`, `<alternatives_considered>`, `<success_criteria>`, `<context>` — stay in `PLAN.md` exactly as today.
- **D-03: Checkpoint tasks are excluded from the inversion.** `type="checkpoint:decision"`/`"checkpoint:human-verify"` tasks keep their full structure in `PLAN.md`, unchanged. Only `type="auto"` and `type="tracer"` tasks invert.
- **D-04: bd-unreachable at execute time is a hard failure, stated plainly.** If `bd show` fails for a task `gsd-executor` needs to read, the executor halts with a clear error naming the missing/unreachable issue. No `PLAN.md` fallback.
- **D-05: File the gsd-core patch upstream immediately; run the local patch until merged.** Same pattern as the `ship.md` generic-gate-dispatch patch already in use. — **Reversibility:** reversible.
- **D-06: Forward-only backfill.** Fix `sync.py::resolve_issue`/`resolve_or_create_epic` so all NEW task/epic creation writes a real `--description`. ~40 already-closed historical issues from Phases 1-15 stay title-only.
- **D-07: Forward-only migration.** Only phases *planned after* this change get the `PLAN.md`-becomes-pointer treatment. Phases 1-15's `PLAN.md` files are not rewritten retroactively.
- **D-08: Root-cause the `close_wave()` gap, fix it, and close the 4 stale issues as proof.** Phase 14's epic (`gsd-beads-bu0`) shows 2/6 tasks closed (wave 1) and 4/6 still open (waves 2-3) despite `git log` confirming all three waves were fully committed. Not a design decision — flagged for `gsd-phase-researcher` to investigate and `gsd-planner` to scope a fix task around. — **Reversibility:** reversible.

### Claude's Discretion

- Exact `bd` description markdown formatting (how `<objective>`/`<action>`/`<verify>`/`<acceptance_criteria>` XML-ish PLAN.md tags render as clean bd-description markdown) — following the existing `_write_report`-style "one place writes the shape" discipline already established in `sync.py`.
- Whether the gsd-core patch to `execute-plan.md` is a single unified diff or split into a read-path change plus a separate `PLAN.md`-stripping-at-sync change — based on what's independently testable.

### Deferred Ideas (OUT OF SCOPE)

- Retroactive backfill of Phases 1-15's bd issue descriptions (deferred by D-06).
- Retroactive `PLAN.md` stripping for Phases 1-15 (deferred by D-07).

</user_constraints>

<phase_requirements>
## Phase Requirements

No formal REQUIREMENTS.md entries exist for Phase 16 — CONTEXT.md's D-01 through D-08 are the requirements source of truth.

| ID | Description | Research Support |
|----|-------------|------------------|
| D-01 | Full inversion: executor reads task content from `bd show`, not `PLAN.md` | `execute-plan.md`'s `load_prompt`/`execute` steps read in full (Priority 2 below); exact insertion point identified, line-cited |
| D-02 | Plan-level content stays in `PLAN.md`; only per-task fields move | **Correction found**: `<objective>` is plan-level only in the real schema, not per-task — see Pitfall 1 |
| D-03 | Checkpoint tasks excluded from inversion | `parse_segments`/`execute` step already branches on `type="checkpoint*"` via existing regex; no new mechanism needed, confirmed by reading `execute-plan.md` |
| D-04 | bd-unreachable is a hard failure | `bd show <bad-id> --json` verified live: exit code 1, JSON `{"error": "..."}"`, no data array — exact failure signature the patch must check |
| D-05 | Upstream-patch-with-local-copy pattern | `GSD-CORE-PATCH.md` and `check_shipmd_patch()` read in full — exact precedent to replicate for the new patch |
| D-06 | Forward-only write-path fix (`resolve_issue`/epic resolvers gain `-d`) | `sync.py::resolve_issue`, `resolve_epic`, `resolve_phase_epic`, `resolve_milestone_epic`, `parse_plan` all read in full; `bd create -d`/`--acceptance` flags verified live |
| D-07 | Forward-only PLAN.md migration | No code change needed beyond D-01's patch only applying to phases planned after this one; PLAN.md schema for old phases is unaffected since the patch reads `<beads-id>` presence, not a schema version marker (see Open Question 1) |
| D-08 | Root-cause `close_wave()` gap, fix it, close 4 stale issues as proof | **Root cause found and both leading hypotheses in CONTEXT.md refuted** — see dedicated section below |

</phase_requirements>

## Summary

This phase touches three narrow, already-well-understood surfaces of the existing `beads` capability
(`.gsd/capabilities/beads/`): the write-path (`sync.py`'s `bd create` calls), the read-path
(`execute-plan.md`'s per-task loop), and a historical dispatch-reliability gap (`close_wave()`
never firing for Phase 14's waves 2-3). No new external dependency is introduced — everything is a
change to two files already in this repo's tree (`sync.py`, its test suite) plus a new machine-local
patch to a `$HOME`-installed gsd-core workflow file, following an existing, proven precedent
(`ship.md`'s `gsd-beads-patch:ship-pre-generic-dispatch v1`).

The most consequential finding is **D-08's root cause is not what CONTEXT.md's leading hypothesis
predicted.** Both the worktree/fork-base-divergence hypothesis (#683-class) and a capability-consent
invalidation hypothesis were checked against live `git log` history and both are refuted for Phase
14's specific execution — no worktree merge commits exist in Phase 14's time window, and
`.gsd/capabilities/beads/` was never touched during Phase 14 (so beads' own capability-consent hash
never changed). The actual evidence points to a broader and more concerning pattern: **no
`*-BEADS.md` file has ever been produced for any phase since Phase 4** (verified via `git log --all
--diff-filter=A -- '*-BEADS.md'`, one hit total, in `04-adoption/`) — meaning the entire
`beads-status` skill's four lifecycle dispatch points (`execute:wave:pre`, `execute:wave:post`,
`verify:post`, `ship:pre`) have been unreliable across Phases 5-15, with wave 1 of Phase 14's
`execute:wave:post` (which correctly closed `.1`/`.2`) as the sole confirmed exception. This is an
LLM-orchestrator prompt-following reliability gap, not a Python bug — `sync.py`'s `close_wave()`
logic is correct and was proven live this session (re-running it against Phase 14's already-committed
SUMMARY.md files is the concrete, safe way to satisfy D-08's "close the 4 stale issues as proof"
requirement).

**Primary recommendation:** Fix D-06/D-01 as straightforward, testable code changes to `sync.py` and
a new machine-local patch to `execute-plan.md` (both closely modeled on existing precedent in the same
file). For D-08, do NOT attempt to "fix" LLM instruction-following fidelity directly — instead (1) add
a defensive, idempotent phase-wide reconciliation pass reachable at `verify:post` that closes any bd
issue whose owning plan's `SUMMARY.md` exists but whose bd issue is still open (extending, not
replacing, `regenerate_beads_md`'s existing divergence computation), and (2) manually close the 4
stale issues now by directly invoking the already-correct `sync.py close-wave` command as live proof
the underlying mechanism works.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Task content write-path (`bd create -d`) | GSD lifecycle script (`sync.py`, project-local Python) | bd CLI (external process) | `sync.py` is the sole writer of task/epic content into bd; bd itself is an external subprocess boundary, never called via shell string (T-01-01) |
| Task content read-path (`bd show`) | gsd-core orchestrator workflow (`execute-plan.md`, machine-local, patched) | gsd-executor subagent (consumes the patched read) | The read happens inside the orchestrating LLM's own instruction-following of a markdown workflow file — not a code boundary, a prompt-following boundary (this is exactly what makes D-08's finding relevant to D-01's design, see Pitfall 3) |
| Wave-completion issue closing (`close_wave`) | GSD lifecycle script (`sync.py`) | Orchestrator dispatch loop (`execute-phase.md` step 5.75, natural-language) | The Python logic is correct; the dispatch that INVOKES it is a natural-language instruction the orchestrating agent must follow every wave — this is the actual point of failure found in D-08 |
| Phase-wide reconciliation backstop (new, recommended) | GSD lifecycle script (`sync.py`, extends `regenerate_beads_md`) | `verify:post` dispatch (already proven to exist generically in the loop, per `render-hooks verify:post`) | `verify:post` fires once per phase regardless of wave count/session boundaries — the natural backstop point for missed per-wave closes |

## Standard Stack

### Core

No new libraries. This phase extends existing stdlib-only Python (`sync.py`, N5 constraint: no
dependency beyond the `bd` binary and the Python 3 standard library — confirmed by the module
docstring at `sync.py:1-10`) and a markdown workflow-file patch (`execute-plan.md`).

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|---------------|
| `bd` CLI | live-installed, `bd create --help`/`bd show --help` verified this session | Issue creation/read with `-d/--description` and `--acceptance` flags | Already the project's sole task-tracking substrate (PROJECT.md Core Value); `-d` and `--acceptance` confirmed to exist and round-trip via a live scratch-db test this session `[VERIFIED: live bd CLI]` |
| Python 3 stdlib (`re`, `json`, `subprocess`, `pathlib`) | whatever `sync.py` already targets | Parser extension + description rendering | N5 constraint; `sync.py` already stdlib-only |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Folding `<acceptance_criteria>` into the free-text `-d` description | `bd create --acceptance <text>` (bd's own structured field) | **Recommended**: `--acceptance` is a first-class bd field, verified live this session (`bd show --json` returns a separate `acceptance_criteria` key when `--acceptance` is used at creation) `[VERIFIED: live bd CLI, scratch-db test]`. Using it keeps acceptance criteria machine-queryable in bd instead of buried in markdown prose inside `description`. |
| A single unified `execute-plan.md` patch | Two independent patches (read-path change + a separate detector) | The GSD-CORE-PATCH.md precedent for `ship.md` splits "patch content" from "patch-loss detection" into two independently-testable pieces (Step 2d confirms, a SEPARATE dispatch point at `plan:pre` detects loss) — the same split should apply here (see Priority 2 section) |

**Installation:** None — no new package installs. `bd` is already present and consented (`.gsd/capabilities/beads/`).

## Package Legitimacy Audit

**Not applicable.** This phase introduces zero new external packages/dependencies — only edits to
`sync.py` (stdlib-only) and a machine-local patch to an existing gsd-core workflow file. No `npm
view`/`pip index` verification is needed.

## D-08 Root Cause Investigation (Priority 1)

### Evidence gathered, in order

1. **The bd data itself.** `bd show gsd-beads-bu0.3/.4/.5/.6 --json` (live query this session)
   shows `updated_at` **identical to** `created_at` for all four issues — meaning none of them was
   ever touched (not even an attempted-and-failed `bd close`) after creation at
   `2026-08-18T15:39:2[89]Z`/`15:39:3[34]Z`. `.1`/`.2` (wave 1), by contrast, carry
   `close_reason` fields quoting the actual wave-1 commit hashes (`3995088`, `0b31063`).
   `[VERIFIED: live bd show gsd-beads-bu0.1..6 --json]`

2. **All 6 issues were created in one shot, before any wave executed.** `git log` shows a single
   commit `10a4857` (`chore(14): sync plan tasks to beads issues under epic gsd-beads-bu0`,
   `2026-08-18T17:39:42+02:00`) that inserted `<beads-id>` into all three of `14-01/02/03-PLAN.md`
   simultaneously — matching the bd `created_at` timestamps exactly (`15:39:2x`/`15:39:3x` UTC =
   `17:39:2x`/`17:39:3x` local). `[VERIFIED: git show 10a4857 --stat, bd created_at fields]`

3. **Worktree/fork-base-divergence (#683) hypothesis: REFUTED for this execution.**
   `git log --all --pretty --grep="merge executor worktree"` shows five such commits in this repo's
   history, but the earliest is `2026-08-18T23:13:57+02:00` — over 4 hours AFTER Phase 14's last
   commit (`92d1320` at `20:02:14+02:00`). A full `git log` of every commit in Phase 14's execution
   window (`18:23:29` to `19:14:42`) shows 15 sequential commits landing directly on `main`, with
   zero `chore: merge executor worktree` commits interleaved. Phase 14 was executed sequentially
   in the primary checkout, not via isolated worktrees. gsd-core issue #683
   ("Worktrees Only work if you are developing in the default branch") is a real, closed upstream
   bug — but its mechanism (a worktree forking from a stale `origin/HEAD`) never had an
   opportunity to trigger here, because no worktree was ever created during Phase 14's execution.
   `[VERIFIED: git log --all --grep, git log --since/--until, gh issue view 683]`

4. **Capability-consent invalidation hypothesis: REFUTED for `beads`' own dispatch.**
   `capability-consent.cjs` (read in full) binds consent to a `bundleContentHash` computed **per
   capability id**, over that capability's own bundle directory only (`hasProjectConsent({..., id,
   contentHash})`, keyed by `(projectRoot, id)`). STATE.md's own Decisions log documents that
   `.gsd/capabilities/pr-workflow/` files WERE edited mid-phase and DID silently deactivate
   `pr-workflow`'s own consent ("14-01/14-02 both edited files inside the bundle after the
   original consent, silently deactivating it until re-installed" — re-consented at commit
   `8e0a758`, `19:40:31`, well after wave 3 had already finished at `19:08:24`). But `git log
   --name-only` for Phase 14's entire execution window shows **zero commits touching
   `.gsd/capabilities/beads/`** — only `.gsd/capabilities/pr-workflow/` files changed. Since
   consent is scoped per-id, `beads`' own consent (and hence the `beads-status` skill's
   dispatch eligibility) was never affected by pr-workflow's bundle edits.
   `[VERIFIED: git log --name-only --since/--until -- .gsd/capabilities/pr-workflow/, capability-consent.cjs read in full]`

5. **The actual mechanism (`sync.py`, `capability.json`, `beads-status/SKILL.md`) is correct.**
   `close_wave()` (sync.py:784-825) determines completion via
   `find_completed_task_ids()` (sync.py:727-750), which checks `{plan_id}-SUMMARY.md`
   **file existence in `phase_dir`** — NOT a git-log grep (CONTEXT.md's D-08 note describing
   "`close_wave()`'s `find_completed_task_ids` grep pattern matching git log commit subjects" is
   imprecise; the actual mechanism has never used git log at all, only `SUMMARY.md` existence).
   `[VERIFIED: sync.py:727-750, full function body read]`. `beads-status/SKILL.md`'s Step 1.5
   correctly routes `execute:wave:post` to Step 2 (`close-wave`), separately from
   `execute:wave:pre` (Step 2a, wave-status-block) and `verify:post` (Step 2b, **explicitly
   never** calling close-wave — "Then stop; do not call `close-wave` from this branch" — Anti-Pattern
   6). `capability.json` registers all four dispatch points generically (`steps[]`, `onError:
   "skip"`), and per `GSD-CORE-PATCH.md`'s own framing, `execute:wave:post`'s generic dispatch
   is (unlike `ship:pre` before its patch) already native in gsd-core — no patch is needed for
   the mechanism itself to exist. `[VERIFIED: sync.py, capability.json, beads-status/SKILL.md, all read in full]`

6. **The systemic finding: `*-BEADS.md` has been produced exactly once in this repo's entire git
   history.** `git log --all --oneline --diff-filter=A -- '*-BEADS.md'` returns a single commit,
   `81c3fe7` (`chore(04): sync phase 4 tasks to bd, regenerate BEADS.md`), and the resulting file
   lives only at `.planning/milestones/v1.0-phases/04-adoption/04-BEADS.md`. No phase since —
   including Phase 13 and Phase 15, which also run under `beads.enabled: true` — has ever produced
   a `*-BEADS.md` file, tracked or untracked. Since `regenerate_beads_md()` is invoked at THREE of
   the four dispatch points (`execute:wave:pre` via `wave-status-block`, `verify:post` directly,
   and implicitly refreshed data feeds `ship:pre`'s gate), this means the entire
   `beads-status` skill's dispatch has been unreliable across every phase from Phase 5 onward, with
   wave 1 of Phase 14's `execute:wave:post` call (which DID close `.1`/`.2`) standing out as
   the one confirmed positive case in the whole project's history. `[VERIFIED: git log --all
   --diff-filter=A -- '*-BEADS.md'; git ls-files | grep -i BEADS.md; find .planning/phases -iname '*BEADS.md' -> empty]`

### Conclusion

The gap is **not a code defect** in `sync.py`/`close_wave()`/`find_completed_task_ids()` — every
function was read in full and is logically correct, and `close_wave()` did fire correctly exactly
once (Phase 14 wave 1). The gap is that `execute-phase.md` step 5.75 ("Execute:wave:post capability
dispatch") and its siblings at `execute:wave:pre`/`verify:post` are **natural-language instructions
inside a long, multi-step orchestrator workflow document** that the orchestrating LLM agent must
faithfully execute every wave, every phase — and the empirical record (one success out of what should
be dozens of dispatch opportunities across Phases 5-15) shows this instruction is easy for an
orchestrating agent to silently skip, especially deep into a long session or across a
wave/session boundary. This is consistent with `execute-phase.md`'s own documented `<resumption>`
model (`discover_plans finds completed SUMMARYs -> skips them`, filtered at **plan** granularity
per line 339's `has_summary: true` filter) providing no explicit guarantee that wave-level
housekeeping (5.6 post-merge-gate / 5.7 tracking update / 5.75 capability dispatch) re-runs for a
wave whose only plan was found already-`has_summary` at the start of a resumed/continuation session.

### Recommended fix (for the planner to scope as a task)

1. **Immediate remediation (satisfies D-08's "close the 4 stale issues as proof" literally, with
   zero new code):** run the existing, already-correct command directly —
   `python3 .gsd/capabilities/beads/scripts/sync.py close-wave
   .planning/phases/14-pr-workflow-capability-dogfood 14-02 14-03` — since both plans' `SUMMARY.md`
   files already exist and are already committed. This both closes the 4 issues AND is itself the
   "prove the fix works" live evidence, because it exercises the exact code path this section
   verified is correct.
2. **Defensive backstop (the actual "fix" — code, not orchestrator-prompt engineering):** add a new,
   idempotent, phase-wide reconciliation subcommand to `sync.py` (e.g. `reconcile-stale-closed
   <phase_dir>`) that reuses `_resolve_completed_task_ids(phase_dir)` (already computes the
   task-done side of the divergence, sync.py:696-705) and `filter_open_ids()` (already computes the
   bd-still-open side, sync.py:753-781) to find and close any issue that is task-complete but still
   bd-open, **across the whole phase, not scoped to one wave's plan-id list**. Dispatch this at
   `verify:post` (a lifecycle point that fires exactly once per phase, regardless of how many
   sessions/waves it took to get there) — this requires **revising** `beads-status/SKILL.md`'s
   Anti-Pattern 6 ("verify:post ... never dispatches close-wave"), which is precisely the rule that
   made this historical gap invisible until now. Do not simply delete the rule — replace it with an
   explicit note that `verify:post` dispatches the NEW phase-wide reconciliation pass (idempotent,
   safe to re-run), while the per-wave `close-wave` dispatch at `execute:wave:post` remains
   unchanged (it is still the fast path; the reconciliation pass is the backstop for when it was
   missed).
3. **Do not attempt to fix orchestrator prompt-following fidelity itself within this phase's scope**
   — that is a gsd-core-level concern (arguably worth a separate upstream issue, distinct from
   #3554) and is not something `sync.py`/`execute-plan.md` changes can guarantee. Flag it as an
   Open Question below so the planner can decide whether to file it.

## Priority 2: Full-Inversion Read-Path Mechanism (D-01/D-04/D-05)

### Where the read currently happens

`execute-plan.md` (558 lines, read in full) has exactly ONE place that loads task content:
`<step name="load_prompt">` (lines 168-175):

```
cat .planning/phases/XX-name/{phase}-{plan}-PLAN.md
```
"This IS the execution instructions. Follow exactly."

This is a whole-file `cat`, not a per-task read — so PLAN.md's plan-level sections (`<objective>`,
`<threat_model>`, etc., which D-02 keeps in PLAN.md) are still loaded this same way; nothing about
`load_prompt` itself needs to change for D-02's plan-level content.

The actual per-task consumption happens later, inside `<step name="execute">` (lines 187-207), item
3, "Per task:" — this is where the executor currently relies on the task's inline
`<action>`/`<verify>`/`<acceptance_criteria>`/`<read_first>`/`<done>` text that `load_prompt`'s `cat`
already put in context. **This is the correct insertion point for the D-01 patch**: a new sub-step
inserted before the `type="auto":`/`type="tracer":` bullets, gated on task `type` and the presence of
`<beads-id>`, that resolves task detail via `bd show <beads-id> --json` and treats its `description`/
`acceptance_criteria` fields as authoritative for those task types — instead of (now largely-absent,
per D-01/D-07) inline PLAN.md task-body text.

`parse_segments` (lines 90-123) and its `TASK_COUNT`/checkpoint-type detection (`grep -n
"type=\"checkpoint"`) both operate on the `<task ...>` tag's attributes and count, **not** its body —
so D-01's stripping of task-body content does not break task counting, inline-vs-subagent routing, or
checkpoint detection. `<name>` and `<beads-id>` (which D-01 keeps in PLAN.md) are sufficient for these
existing mechanisms.

### D-04's hard-fail signature (verified live)

```
$ bd show nonexistent-id --json
{"error": "no issues found matching the provided IDs", "schema_version": 1}
exit code: 1
```
`[VERIFIED: live bd CLI, this session]`

The patch's hard-fail branch should check for BOTH a non-zero exit code AND (defensively) an
`"error"` key in the parsed JSON — matching the existing convention `sync.py` already uses
everywhere else (`result.returncode != 0`).

### bd's actual field surface (verified live, scratch db)

```json
{
  "id": "td-6al",
  "title": "test task",
  "description": "This is a test description with **markdown**.",
  "acceptance_criteria": "- criterion one\n- criterion two",
  ...
}
```
`bd create` accepts `-d/--description` and (separately) `--acceptance` — both surface as distinct
top-level keys on `bd show --json`, not folded together. `[VERIFIED: live bd CLI, scratch db this
session — bd init --prefix td; bd create ... -d ... --acceptance ...; bd show --json]`. This means
the read-path patch should read TWO fields off the `bd show --json` payload for an inverted task:
`description` (rendered `<action>`/`<read_first>`/`<precondition>`/`<done>` markdown) and
`acceptance_criteria` (bd's own structured field) — not one undifferentiated blob.

### Patch precedent to replicate (D-05)

`GSD-CORE-PATCH.md` (read in full) and `sync.py::check_shipmd_patch` establish the exact,
already-proven pattern:

1. A machine-local patch to the `$HOME`-installed gsd-core workflow file, bracketed by a versioned
   HTML-comment marker (`<!-- gsd-beads-patch:<name> v1 -->` ... `<!-- /gsd-beads-patch:<name> v1
   -->`), inserted at a named anchor (for `ship.md`: "immediately after step 7's final line").
2. `GSD-CORE-PATCH.md` itself, containing: why the patch exists (which N-constraint it overrides
   and when that override was granted), the byte-identical patch content (for reapplication if a
   `gsd-core` update strips it), the upstream issue number it was filed as, and an explicit revert
   condition.
3. A detector function in `sync.py` (`check_shipmd_patch`) that greps the live installed file for
   the marker string — called from a lifecycle point **independent of the patch's own dispatch
   loop** (critical: `ship.md`'s own Step 2d can only confirm-while-intact, not detect-when-lost,
   because Step 2d is itself only reachable through the patched loop — the actual detector is
   `beads-recall/SKILL.md`'s Step 3.5, dispatched at `plan:pre`, a point gsd-core dispatches
   natively regardless of whether the `ship.md` patch survived).

**Applying this to the new `execute-plan.md` patch:** name it distinctly (e.g.
`gsd-beads-patch:execute-plan-bd-task-read v1`), write a new `GSD-CORE-PATCH-EXECUTE.md` (or extend
the existing `GSD-CORE-PATCH.md` with a second marker section — Claude's Discretion, D-05's own
framing), add a second detector function to `sync.py` alongside `check_shipmd_patch`, and — following
the SAME independence principle — dispatch the new detector from a point gsd-core reaches natively
regardless of the new patch's own health. `plan:pre`'s existing Step 3.5 (beads-recall) is already
proven to fire reliably and is a natural place to add a second, independent marker check.

### File upstream (D-05)

File a new gsd-core issue (distinct from #3554, which is the `ship.md` generic-gate-dispatch gap) —
the ask: `execute-plan.md`'s per-task read should have a native seam for "read `<beads-id>`-identified
task content from an external tracker" so this patch isn't needed permanently. Do this immediately per
D-05, using the exact `GSD-CORE-PATCH.md` revert-condition framing as a template.

## Priority 3: Write-Path Mechanism (D-06)

### Current gap, confirmed live

`bd list --json -n 200 | jq -r '.[] | select(.description != null and .description != "") | .id'`
returns **zero rows** — every issue in this project's live bd database has an empty description,
confirming CONTEXT.md's motivating claim with a live query, not just a read of `sync.py`'s source.
`[VERIFIED: live bd query, this session]`

`resolve_issue()` (sync.py:615-634) creates a task issue with:
```python
["bd", "create", title, "--type", "task", "--parent", epic_id, "--silent"]
```
No `-d`. `resolve_epic()` (sync.py:564-612) and `resolve_milestone_epic()` (sync.py:506-561) both
create epics the same way — `["bd", "create", title, "--type", "epic", "--silent"]`, no `-d`.

### Correction to D-02's per-task field list — `<objective>` is plan-level, not per-task

`[VERIFIED: .gsd/capabilities/beads/tests/fixtures/plan-single.md:13-16 and
.planning/phases/14-pr-workflow-capability-dogfood/14-01-PLAN.md:70,100-204 and
$HOME/.claude/gsd-core/templates/phase-prompt.md:33,61-104]`

`<objective>` appears **exactly once per PLAN.md**, before `<tasks>`, describing the whole plan —
never inside an individual `<task>` block. Verbatim from `phase-prompt.md`'s canonical template
(the source of truth for what a `<task>` block actually contains):

```
<task type="auto">
  <name>Task 1: [Action-oriented name]</name>
  <files>path/to/file.ext, another/file.ext</files>
  <read_first>path/to/reference.ext, path/to/source-of-truth.ext</read_first>
  <action>[Specific implementation ...]</action>
  <verify>[Command or check to prove it worked]</verify>
  <acceptance_criteria>
    ...
  </acceptance_criteria>
  <done>[Measurable acceptance criteria]</done>
</task>
```

And confirmed against a REAL, already-executed plan (`14-01-PLAN.md`, lines 100-204): the task block
carries `<name>`, `<beads-id>`, `<read_first>`, `<action>`, `<verify>`, `<acceptance_criteria>`,
`<done>` — no `<objective>` tag anywhere inside it. `<precondition>` is a real, optional per-task
element too — confirmed via `$HOME/.claude/gsd-core/references/planner-preconditions.md:15,46-53`
("`<precondition>` (optional element on `<task>`) ... placed right after `<name>` and before
`<files>`") — but it is rare (emitted "ONLY when a task relies on state the plan's own `depends_on`
doesn't already guarantee").

**Corrected per-task field list for D-02's write-path (what the parser must extract and what the
renderer must fold into `bd create -d`):** `<precondition>` (optional), `<files>`, `<read_first>`,
`<action>`, `<verify>`, `<done>` → `description`; `<acceptance_criteria>` → bd's own `--acceptance`
flag (see Priority 2's live-verified field surface). `<objective>` stays exactly where D-02 already
says plan-level content with "no natural per-task home" stays: in `PLAN.md`. This is not a new
decision — it's a factual correction to CONTEXT.md's list of which tags are per-task, surfaced here
because the planner needs the accurate schema to scope the parser-extension task correctly.

### Parser extension needed (`parse_plan`, sync.py:142-170)

Currently extracts only `name`, `name_end`, `beads_id`, `files` per task (via `NAME_RE`,
`BEADS_ID_RE`, `FILES_RE`, all `<tag>(.*?)</tag>` DOTALL patterns matched against each `<task>` block
captured by `TASK_RE`). Two things are missing entirely, not just the content fields:

1. **Task `type` attribute is never captured.** `TASK_RE = re.compile(r"<task\b[^>]*>.*?</task>",
   re.DOTALL)` captures the whole block including the opening tag's attributes, but no existing
   regex extracts `type="..."` from it — this is REQUIRED for D-01/D-03 (only `auto`/`tracer` tasks
   invert; `checkpoint:*` types must be identifiable from the parsed task dict, not re-derived by a
   second string search elsewhere). `[VERIFIED: sync.py:26, 142-170 — full function body read; no
   TASK_TYPE_RE exists]`
2. **Content fields** (`<precondition>`, `<action>`, `<verify>`, `<acceptance_criteria>`, `<done>`,
   plus the already-parsed `<read_first>`... wait, `<read_first>` is ALSO not currently parsed by
   `parse_plan` — only referenced by name in comments/docs, never regex-extracted). Add
   `ACTION_RE`, `VERIFY_RE`, `ACCEPTANCE_CRITERIA_RE`, `READ_FIRST_RE`, `DONE_RE`,
   `PRECONDITION_RE` — same `<tag>(.*?)</tag>` DOTALL pattern already established for
   `NAME_RE`/`BEADS_ID_RE`/`FILES_RE`, no new parsing technique needed.

### Rendering function — "one place writes the shape"

Follow the exact precedent already in `sync.py`: `_todo_description()` (sync.py:278-285) folds a
todo's problem/solution/files into one `-d` string, called from exactly one call site
(`migrate_todos`). A new `_task_description(task)` function should do the same for the new per-task
fields, called from the (also-new) task-creation call site inside `create_issues`/`resolve_issue`.
Matches the discipline `_render_beads_recall_body`/`_render_beads_md_table` already establish for
every other generated-artifact shape in this file.

**Recommended `bd create` shape** (Claude's Discretion per CONTEXT.md, but concretely specified here
given the live-verified `--acceptance` flag):

```python
run_bd([
    "bd", "create", title,
    "-d", _task_description(task),       # precondition/read_first/action/verify/done, rendered
    "--acceptance", task["acceptance_criteria"],  # bd's own structured field, when non-empty
    "--type", "task", "--parent", epic_id, "--silent",
])
```

### Epic-level description gap (same fix, different content source)

`resolve_epic()`/`resolve_phase_epic()`/`resolve_milestone_epic()` also create epics with no `-d`.
Since a phase epic has no per-task home to draw from, and `<objective>` is confirmed plan-level (see
correction above), the natural content source for an epic's description is the plan's own
`<objective>` text (or, for a milestone epic, `milestone_epic_title()`'s existing title-composition
pattern extended similarly) — **flagged here as Claude's Discretion during planning**, consistent with
CONTEXT.md's own delegation of exact markdown-shape decisions, but grounded in the verified fact that
`<objective>` is the one plan-level field that naturally maps to "what is this epic for."

### Test patterns to extend (not replace)

`.gsd/capabilities/beads/tests/test_sync.py` (2738 lines) already has `TestCreateIssues`,
`TestPhaseScopedEpic`, `TestMilestoneEpic`, `TestCloseWave` classes with an established mocking
convention: `@mock.patch("subprocess.run")` + a shared `_make_bd_side_effect()` fixture-based side
effect, argv-list assertions (e.g. `self.assertIn("--parent", task_creates[0])`). New tests for `-d`/
`--acceptance` presence should follow this exact pattern — assert the argv list built by
`resolve_issue`/`resolve_epic` contains `"-d"` followed by non-empty content, not a full end-to-end
bd invocation. `[VERIFIED: test_sync.py:301-378, full TestCreateIssues/TestPhaseScopedEpic classes
read]`

## Architecture Patterns

### System Architecture Diagram

```
WRITE PATH (D-06, this phase)
  PLAN.md <task> blocks
       │  parse_plan() [sync.py] -- extended to capture type + content fields
       ▼
  resolve_issue() / resolve_epic() [sync.py]
       │  NEW: -d <_task_description(task)> --acceptance <criteria>
       ▼
  bd create  ──────────────────────────────────►  bd database
                                                        │
READ PATH (D-01, this phase — new patch)                │
  gsd-executor subagent                                 │
       │  load_prompt: cat PLAN.md (plan-level sections only, per D-02)
       │  execute step, per task:
       │    type in {auto, tracer} AND <beads-id> present?
       │       │ yes                              │ no (checkpoint:*)
       │       ▼                                  ▼
       │  bd show <id> --json  ◄───────────────────────┘  read from PLAN.md as today (D-03)
       │       │
       │       ├─ success: description + acceptance_criteria = task instructions
       │       └─ failure (exit!=0 or "error" key): HALT, name the issue (D-04)
       ▼
  task execution proceeds

WAVE-COMPLETION CLOSE PATH (D-08, existing + new backstop)
  execute:wave:post (per-wave, orchestrator step 5.75)
       │  close_wave(phase_dir, wave_plan_ids) -- correct, but dispatch is
       │  an LLM-followed instruction, empirically unreliable (see D-08 section)
       ▼
  bd close <issue-ids>

  verify:post (once per phase, orchestrator-native, proven more reliable)
       │  NEW backstop: reconcile-stale-closed(phase_dir) -- phase-wide,
       │  idempotent, catches anything execute:wave:post missed
       ▼
  bd close <issue-ids>
```

### Recommended Project Structure

No new files/directories — all changes land inside the existing tree:

```
.gsd/capabilities/beads/
├── scripts/sync.py           # parse_plan extension, resolve_issue/-epic -d, new reconcile subcommand
├── skills/beads-status/SKILL.md   # revise Anti-Pattern 6, wire new verify:post reconciliation step
├── GSD-CORE-PATCH.md         # extend with a second marker section for the execute-plan.md patch
└── tests/test_sync.py        # extend TestCreateIssues/TestPhaseScopedEpic/TestCloseWave, add new class for reconcile
```

Machine-local (not in this repo's git history):
```
$HOME/.claude/gsd-core/workflows/execute-plan.md   # new patch, per-task bd-read insertion
```

### Anti-Patterns to Avoid

- **Assuming the D-08 gap is a `sync.py` bug and "fixing" the wrong layer:** every function
  involved was read in full and is logically correct. Spending plan effort re-verifying/rewriting
  `close_wave()`/`find_completed_task_ids()` themselves would not address the actual gap
  (orchestrator dispatch reliability) — see the D-08 section's recommended fix instead.
- **Trusting CONTEXT.md's exact per-task field list (`<objective>` included) without checking the
  real schema.** Verified this session: `<objective>` is plan-level only. Building the parser
  extension against the CONTEXT.md list verbatim would add a regex for a tag that never appears
  inside a `<task>` block in practice.
- **Folding `<acceptance_criteria>` into the free-text `-d` blob** instead of using bd's own
  `--acceptance` flag (verified to exist and round-trip live this session) — loses the structured
  field for no benefit.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting whether a machine-local gsd-core patch survived an update/reinstall | A new ad-hoc file-diff or hash check | The exact `check_shipmd_patch`-style substring grep against a versioned HTML-comment marker, dispatched from an independent lifecycle point | Already proven correct and tested (`TestCheckShipmdPatch` class in test_sync.py) for the identical problem shape |
| Rendering task/todo content into a `bd -d` string | A new bespoke formatter | `_todo_description()`'s existing pattern, cloned for tasks (`_task_description()`) | "One place writes the shape" discipline already established; avoids two divergent renderers producing subtly different markdown |
| Computing which bd issues are stale-open vs. task-complete | A new diff/reconciliation algorithm | `_resolve_completed_task_ids()` + `filter_open_ids()`, already built and already used by `close_wave()`/`_compute_diverged()` | Both functions already exist, are tested, and compute exactly this; the only new code needed is a phase-wide (not wave-scoped) call site |

**Key insight:** Every mechanism this phase needs (patch-marker detection, description rendering,
stale-issue detection) already has a proven, tested precedent inside this exact file. The work is
extension, not invention.

## Common Pitfalls

### Pitfall 1: Trusting CONTEXT.md's per-task field list verbatim

**What goes wrong:** Building `parse_plan()`'s extension to look for a per-task `<objective>` tag
that never occurs inside a real `<task>` block — wasted regex, and a false sense that plan-level
content was captured when it wasn't.
**Why it happens:** CONTEXT.md's D-02 was written from memory/summary during `/gsd-discuss-phase`,
not from a fresh read of the canonical template.
**How to avoid:** Use the corrected field list in the Priority 3 section above, grounded in
`phase-prompt.md`'s canonical template and a real executed PLAN.md.
**Warning signs:** A parser that finds zero `<objective>` matches inside every `<task>` block it
processes (which is the CORRECT behavior — but only if the code expects it).

### Pitfall 2: Assuming `bd show --json`'s default output includes `description`

**What goes wrong:** The read-path patch reads a field that silently isn't there because the issue
was created without `-d` (true for every currently-open issue in this project) or because a flag
like `--long` was assumed necessary when it isn't.
**Why it happens:** `bd show --json`'s default output (verified live) already includes `description`
and `acceptance_criteria` whenever they're non-empty — `--long` adds "extended metadata, agent
identity, gate fields," not description content. No extra flag is needed for D-01's read.
**How to avoid:** The verified example JSON in Priority 2 above is the ground truth for what
fields to expect and when.
**Warning signs:** A patch that always passes `--long` "just in case" — harmless but unnecessary.

### Pitfall 3: Designing D-01's patch as if instruction-following is guaranteed

**What goes wrong:** D-08's own root cause (Priority 1 above) is direct, concrete proof that a
natural-language dispatch instruction inside a long gsd-core workflow file can be silently skipped
by the orchestrating LLM, repeatedly, across many phases. D-01's read-path patch is the SAME kind of
instruction (a new per-task branch inside `execute-plan.md`'s `execute` step). D-04's hard-fail
requirement protects against `bd` being genuinely unreachable, but does NOT protect against the
executor simply not noticing/following the new branch and falling back to old habits.
**Why it happens:** Prose-embedded instructions in a long multi-step workflow compete with dozens of
other instructions for the orchestrating LLM's attention across a long session.
**How to avoid:** Recommend the planner add a verification step to the SUMMARY self-check (already an
existing pattern — `execute-plan.md`'s `create_summary` step already has a "Self-Check: PASSED"
block) that proves the executor actually read from bd for an inverted task (e.g., a grep-able marker
in the SUMMARY, or a acceptance-criteria-style check comparing task content against `bd show`
output) — the same "detector independent of the mechanism itself" principle D-05's `check_shipmd_patch`
already uses.
**Warning signs:** A plan that implements D-01 with no independent way to confirm it actually fired
on a real task, relying purely on "the patch is in the file" as proof it executes correctly every time.

## Code Examples

### Existing `-d` usage pattern to clone (`_todo_description`, sync.py:278-285)

```python
# Source: .gsd/capabilities/beads/scripts/sync.py, read in full this session
def _todo_description(todo):
    """Fold problem/solution (and files, when present) into one `-d` prose
    string ..."""
    desc = f"## Problem\n{todo['problem']}\n\n## Solution\n{todo['solution']}\n"
    if todo["files"]:
        desc += "\n## Files\n" + "\n".join(f"- {f}" for f in todo["files"]) + "\n"
    return desc
```

### Live-verified bd description/acceptance round trip

```bash
# Source: live bd CLI, this session, scratch db
$ bd init --prefix td
$ bd create "test task" -d "This is a test description with **markdown**." \
    --acceptance "- criterion one
- criterion two" -t task --silent
td-6al
$ bd show td-6al --json
[
  {
    "id": "td-6al",
    "title": "test task",
    "description": "This is a test description with **markdown**.",
    "acceptance_criteria": "- criterion one\n- criterion two",
    ...
  }
]
```

### Live-verified bd-unreachable failure signature

```bash
# Source: live bd CLI, this session
$ bd show nonexistent-id --json; echo "exit=$?"
{"error": "no issues found matching the provided IDs", "schema_version": 1}
exit=1
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `bd create <title> --type task --parent <epic> --silent` (no description) | Add `-d`/`--acceptance` | This phase (D-06) | Every synced issue becomes self-sufficient without `PLAN.md` open |
| `gsd-executor` reads `PLAN.md`'s inline `<task>` body | `gsd-executor` reads `bd show <id>` for `auto`/`tracer` tasks | This phase (D-01), via machine-local patch | `bd` becomes actual source of truth per PROJECT.md's Core Value |
| `close_wave()` dispatched only at `execute:wave:post`, no backstop | Add a `verify:post` phase-wide reconciliation pass | This phase (D-08 fix) | Recovers from the exact historical gap found in Phase 14 |

**Deprecated/outdated:**
- None — this phase extends existing, currently-shipped mechanisms; nothing is being replaced
  wholesale.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The epic-level description's best content source is the plan's `<objective>` text (rather than, e.g., ROADMAP.md's phase-section prose) | Priority 3, "Epic-level description gap" | Low — explicitly flagged as Claude's Discretion in CONTEXT.md; either source produces a reasonable epic description, and the choice doesn't block D-06's core fix (task-level `-d`) |
| A2 | Splitting the `execute-plan.md` patch into "content" + "independent detector" (mirroring `ship.md`'s Step 2d/beads-recall Step 3.5 split) is the right shape for the new patch, rather than a single combined check | Priority 2, "Patch precedent to replicate" | Low-Medium — if the planner instead combines them, the risk is exactly the "detector reachable only through its own patch" flaw `GSD-CORE-PATCH.md` explicitly warns against; worth calling out at plan-check time |
| A3 | Adding a `verify:post`-dispatched reconciliation pass is preferable to trying to make `execute:wave:post` dispatch more reliable directly | D-08 section, "Recommended fix" | Medium — if orchestrator instruction-following genuinely cannot be trusted at ANY lifecycle point, even `verify:post`'s dispatch could be skipped; the systemic finding (BEADS.md never produced since Phase 4) means `verify:post`'s OWN dispatch has also apparently never fired successfully via `regenerate_beads_md`, which weakens confidence that adding logic to that same dispatch point solves the reliability problem rather than just moving it |

## Open Questions

1. **Should the orchestrator-prompt-following reliability gap (D-08's systemic finding) be filed
   upstream to gsd-core as its own issue, separate from #3554?**
   - What we know: the `execute:wave:pre`/`execute:wave:post`/`verify:post`/`ship:pre` dispatch loop
     is documented as "native/generic" (unlike `ship:pre` before its patch) — the MECHANISM exists
     and is correctly wired in `capability.json`. The gap is in whether the orchestrating LLM
     actually executes the documented step every time.
   - What's unclear: whether this is a gsd-core framework problem (worth filing) or something
     `beads`-specific plans can mitigate entirely on their own via the reconciliation backstop
     (Assumption A3 above raises doubt that even `verify:post` is fully reliable).
   - Recommendation: scope A3's reconciliation pass as this phase's concrete, testable fix; raise
     the upstream-filing question as a discuss-phase/plan-check decision point rather than deciding
     it here, since it's a process/reporting choice, not a code fact.

2. **Does the new `execute-plan.md` patch need its own `GSD-CORE-PATCH.md`-style file, or should it
   extend the existing one with a second marker section?**
   - What we know: `GSD-CORE-PATCH.md` currently documents exactly one patch (`ship.md`'s). Its
     structure (why/upstream-tracking/insertion-anchor/marker/verbatim-content) is fully reusable
     for a second patch.
   - What's unclear: purely a file-organization choice with no functional difference — CONTEXT.md
     already delegates the split-vs-combined DIFF question to Claude's Discretion; this is the
     analogous question for the DOCUMENTATION file.
   - Recommendation: extend the existing file with a second `##`-level section (keeps one canonical
     "what's patched on this machine" reference) unless the planner has a reason to prefer separate
     files.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `bd` CLI | Write-path (`-d`/`--acceptance`), read-path (`bd show --json`) | Yes | live-installed, `-d`/`--acceptance`/`--json` flags confirmed via `bd create --help`/live scratch-db test this session | None needed — `bd` is already this project's required substrate |
| `gsd-core` (`execute-plan.md`, `ship.md`) | D-01/D-05's machine-local patch | Yes | `$HOME/.claude/gsd-core/VERSION` = `1.10.0` | None — patch target file confirmed present and read in full |
| Python 3 | `sync.py` extension | Yes | whatever this project's existing test suite already targets (unittest, confirmed via `test_sync.py`) | None |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

## Validation Architecture

`.planning/config.json`'s `workflow.nyquist_validation` is `true` (absent-defaults-to-enabled rule
also applies, but it's explicit here) — this section is included.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib), with `unittest.mock.patch("subprocess.run")` for `bd` isolation |
| Config file | none — plain `unittest discover` |
| Quick run command | `python3 -m unittest discover -s .gsd/capabilities/beads/tests -v` (do NOT add `-t .` — verified defect, already documented in STATE.md as fixed at the plan-doc level for Phase 14/15, not the code) |
| Full suite command | same command — the whole suite runs in well under 30s per prior phases' recorded durations |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-06 | `resolve_issue`/`resolve_epic` calls include `-d`/`--acceptance` with non-empty content | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestCreateIssues -v` (extend this class) | ✅ class exists, extend with new test methods |
| D-01 | (gsd-core patch, not testable via this repo's unittest suite — see Note) | manual/live | `grep -c 'gsd-beads-patch:execute-plan-bd-task-read v1' "$HOME/.claude/gsd-core/workflows/execute-plan.md"` | ❌ Wave 0 — new patch-detector function needed |
| D-04 | `bd show` failure halts with a clear error | integration (live bd, scratch db) | pattern already proven this session: `bd show <bad-id> --json; echo $?` | ❌ Wave 0 — no existing test covers the read-path since it lives in gsd-core, not this repo |
| D-08 | Reconciliation pass closes stale-open, task-complete issues | unit | new `TestReconcileStaleClosed` class, mirroring `TestCloseWave`'s mocking pattern | ❌ Wave 0 |

**Note on D-01 testability:** the read-path itself lives in a machine-local gsd-core file, outside
this repo's `unittest` suite entirely — it cannot be unit-tested the way `sync.py` changes can. The
existing precedent (`TestShipPreGenericDispatch`, `TestCheckShipmdPatch` classes) tests `sync.py`'s
own *detector* functions (the marker-grep), not the patched workflow's actual runtime behavior. The
planner should scope D-01 similarly: unit-test the new detector function in `sync.py`, and rely on a
live, manual "does the patch actually redirect a real task read" smoke test (matching Phase 14's own
`14-GATE-SMOKE-TEST.md` precedent) as the acceptance evidence for the patch content itself.

### Sampling Rate

- **Per task commit:** `python3 -m unittest discover -s .gsd/capabilities/beads/tests -v`
- **Per wave merge:** same (full suite already fast)
- **Phase gate:** full suite green + the live smoke tests above (D-01's patch redirect, D-08's
  reconciliation pass, D-04's hard-fail signature) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `test_sync.py::TestReconcileStaleClosed` — new class for the D-08 backstop
- [ ] `sync.py`'s new patch-detector function for `execute-plan.md`'s marker (paired unit test)
- [ ] A live smoke-test record (mirroring `14-GATE-SMOKE-TEST.md`) proving D-01's patched read
      actually redirects a real `auto`/`tracer` task's execution to `bd show` — cannot be a unit
      test since the patched file lives outside this repo

## Security Domain

`.planning/config.json`'s `workflow.security_enforcement` is `true` — this section is included.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No new auth surface — `bd` invocations are local subprocess calls under the existing project identity |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Yes | Every `bd` invocation must remain a typed argv list passed to `subprocess.run`, never a shell string (existing N4/T-01-01 constraint, unchanged by this phase — the new `-d`/`--acceptance` content originates from PLAN.md text authored by a different principal than the process running `bd`, same threat class `sync.py`'s module docstring already documents) |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| PLAN.md task text (untrusted relative to the `bd`-invoking process) injected into a shell-interpreted `bd` command via the new `-d`/`--acceptance` content | Tampering | Continue the existing pattern: `subprocess.run(argv_list, ...)` with shell execution left disabled — never build a `bd` command as an interpolated shell string, even for the new description content (this is the SAME mitigation `sync.py`'s docstring already states for every other `bd` call; the new content fields don't introduce a new threat, they extend an already-mitigated one) |
| A malformed/oversized task description causing an unbounded `bd create -d` argv | Denial of Service | Not currently a concern at this project's scale (PLAN.md task bodies are typically a few hundred words); if this becomes a concern, `--body-file`/`--stdin` (both verified to exist on `bd create --help`) provide an alternative to a giant `-d` argv string |

## Sources

### Primary (HIGH confidence — file read in full this session, or live tool output)

- `.gsd/capabilities/beads/scripts/sync.py` — full file read (both halves, lines 1-1318 and
  remainder), every function cited above verified by direct line reference
- `.gsd/capabilities/beads/capability.json` — full file read
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md` — full file read
- `.gsd/capabilities/beads/GSD-CORE-PATCH.md` — full file read
- `.gsd/capabilities/beads/tests/test_sync.py` — class listing + `TestCreateIssues`/
  `TestPhaseScopedEpic` bodies read in full
- `.gsd/capabilities/beads/tests/fixtures/plan-single.md` — full file read
- `$HOME/.claude/gsd-core/workflows/execute-plan.md` — full file read (558 lines)
- `$HOME/.claude/gsd-core/workflows/execute-phase.md` — targeted sections read (wave-post dispatch,
  resumption model, failure handling)
- `$HOME/.claude/gsd-core/workflows/verify-work.md` — targeted section read (verify:post dispatch)
- `$HOME/.claude/gsd-core/templates/phase-prompt.md` — task template grep + read, canonical
  `<task>` schema source
- `$HOME/.claude/gsd-core/references/planner-preconditions.md` — full file read (precondition tag)
- `$HOME/.claude/gsd-core/bin/lib/capability-consent.cjs` — full file read
- `.planning/phases/14-pr-workflow-capability-dogfood/*` (all PLAN/SUMMARY/CONTEXT/STATE-adjacent
  files) — read/grepped for the D-08 investigation
- `.planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/*` — read for the
  #683/worktree hypothesis check
- `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/config.json` — read in full
- Live `git log`/`git show` commands against this repo's actual history (commit hashes, timestamps,
  `--name-only`, `--diff-filter=A`, `--grep`) — this session
- Live `bd` CLI commands (`bd show`, `bd create --help`, `bd show --help`, a scratch-db round-trip
  test) — this session
- `gh issue view 683 --repo open-gsd/gsd-core` — live query confirming #683 is real, closed, and
  worktree-fork-base-related (title: "Worktrees Only work if you are developing in the default
  branch")

### Secondary (MEDIUM confidence)

- None — every claim in this document traces to a file read or live command this session; no
  WebSearch was needed or used (this is an internal-mechanism research task, not an
  external-library task).

### Tertiary (LOW confidence)

- None.

## Metadata

**Confidence breakdown:**
- D-08 root cause (Priority 1): HIGH — every claim verified via live `git`/`bd` commands or full
  file reads this session; both leading hypotheses explicitly tested and refuted with evidence.
- Write-path mechanism (Priority 3): HIGH — parser/renderer extension points, bd CLI flag surface,
  and test patterns all verified via file reads and a live scratch-db round trip.
- Read-path patch shape (Priority 2): MEDIUM — the insertion point and D-04's failure signature are
  verified facts; the exact prose/diff the patch should contain is a design choice CONTEXT.md
  explicitly delegates to planning, not something "verifiable" in the same sense.

**Research date:** 2026-08-19
**Valid until:** ~14 days (this research is about the current state of this repo's own code and this
machine's gsd-core installation, both of which can change with any commit or `gsd-core` update —
shorter validity window than a typical external-library research doc)
