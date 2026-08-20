# Phase 18: Address tech debt: patch-check doc accuracy + CHANGELOG - Context

**Gathered:** 2026-08-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Close out the open tech-debt items surfaced by `.planning/phases/17-config-code-truth/17-REVIEW.md`
and confirmed still open by `.planning/v1.3-MILESTONE-AUDIT.md`'s 2026-08-20 audit of milestone
v1.3 (status: `tech_debt`). WR-04 and WR-05 from that review are **already resolved** (commits
`373e7fb`, `0f8decb`, landed via `/gsd-validate-phase 17` before this discussion) — not in scope
here. In scope: WR-01, WR-02, WR-03, plus the 4 ship-step-check items ROADMAP.md's Phase 17
section lists under "Ship-step checks (release-hygiene debt inherited by this milestone)" — folded
in during discussion because item #2 of that list is the same CHANGELOG fix as WR-03, and the user
chose to close the remaining 3 alongside it rather than leave them to a separate ship task.

No new capability, no behavior change to what the beads capability *does* — every item here is a
doc-accuracy fix, a test/comment durability fix, or release-hygiene cleanup on already-shipped
mechanisms.

</domain>

<decisions>
## Implementation Decisions

### WR-01 — `check_sync_mode_value` docstring falsely claims a stderr convention
**File:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:802-804` (docstring) vs.
`sync.py:2296-2322` (`check_patch` body, the actual behavior)

- **D-01:** Rewrite the docstring to state the true, current behavior — `check_patch` (which both
  `check_shipmd_patch`/`check_execute_plan_patch` thin-wrap) prints all four message paths
  (`not_found_msg`, `could_not_read_msg`, `present_msg`, `missing_msg`) to **stdout**
  unconditionally, same as `check_sync_mode_value`. Drop the "opposite of / stderr-only
  benign-skip convention" framing entirely — it does not exist in the code.
- **D-02:** Additionally add a one-line comment on `check_patch`'s final `print(...)` call pinning
  "stdout is deliberate; the hook promotes only stdout" so the docstring and the implementation
  cannot drift apart again the way they did this time.

### WR-02 — `not_found_msg`/`could_not_read_msg` never carry the "⚠" marker the SKILL.md files gate surfacing on
**File:** `sync.py:142-179` (`PATCH_CHECKS` — both `ship-md` and `execute-plan` entries) vs.
`plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md:76` and
`plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md:149`

- **D-03:** Do **both** halves of the fix, not either/or:
  1. Prefix `not_found_msg` and `could_not_read_msg` with `"⚠ "` in both `PATCH_CHECKS` entries
     (4 message templates total: ship-md × 2, execute-plan × 2), matching the convention
     `missing_msg` already follows.
  2. Broaden both SKILL.md files' instruction from "if output contains the '⚠' warning line" to
     key off exit code (non-zero) or absence of the string `"present"`, so the surfacing rule is
     robust even if a future message template forgets the marker prefix.
  — **Reversibility:** reversible — local code + doc text, no external contract.

### WR-03 — CHANGELOG.md gaps (0.4.0 omission + 0.3.1 miscategorization)
**Files:** `CHANGELOG.md` (0.4.0 section, entirely missing TRUTH-03; 0.3.1 section, timeout entry
still nested under `### Performance`)

- **D-04:** Add a 0.4.0 entry (Added or Changed) documenting `check_native_step_dispatch`, its two
  module constants, and the `plan:post`/`verify:post` stand-down mechanism — name PR #3687 the way
  `GSD-CORE-PATCH.md` already does.
- **D-05:** Also move the 120 s hook-timeout entry (currently `CHANGELOG.md:70-73`, under
  `### Performance`) so it's filed under Fixed or Changed instead — it is a deliberate *reduction*
  from Claude Code's 600 s default hook timeout, not a throughput optimization; the entry's own
  text already says as much but the heading still misfiles it. This decision widens WR-03's literal
  ask (which named only the 0.4.0/TRUTH-03 gap) to also cover ROADMAP.md's Phase 17 "Ship-step
  checks" item #2, which is the same underlying defect — the user chose to fold it in rather than
  leave two open trackers for one fix.
  — **Reversibility:** reversible — docs only.

### Phase 18 outer boundary — folding in the other 3 ship-step-check items
ROADMAP.md's Phase 17 section (lines 274-311) lists 5 items under "Ship-step checks
(release-hygiene debt inherited by this milestone)" as "mechanical command[s] in the ship task, not
a prose reminder." Item #2 is WR-03's CHANGELOG fix (already captured as D-05 above). Item #5
(assert `>= 164` tests and runtime-mirror tree identity before trusting CI-green) stays a
verification action at ship time, not a phase deliverable — no decision needed. Items #1, #3, #4
are locked into this phase's scope:

- **D-06 (item #1 — version bump):** `main` carries a behavioral change since the `v1.3.1` tag
  (`966315a` moved `SHIP_MD_PATCH_MARKER` v1 → v2) plus all of Phase 17's TRUTH-01..04 work.
  `capability.json` is already bumped to `0.4.0` (done in plan 17-01); `plugin.json`
  (`plugins/beads-lifecycle/.claude-plugin/plugin.json`) is still `1.3.1` and unbumped. Bump
  `plugin.json`'s version to reflect the cumulative shipped-since-v1.3.1 changes, in the same
  commit that lands this phase's CHANGELOG entries. Exact new version number is the planner's/
  executor's call (semver minor vs. patch) — not a user decision.
  — **Reversibility:** reversible — a version string, no tag cut yet.
- **D-07 (item #3 — withdrawn `v1.3.0` tag):** Delete the tag from `origin`
  (`git push origin :refs/tags/v1.3.0` + local delete), not document-and-keep. The GitHub Release
  for `v1.3.0` is already deleted; marketplace installs read the branch, not the tag zip, so the
  real exposure window (`55855cd`→`049da5b`) is already closed — this is cleanup of a
  resolvable-but-withdrawn artifact, not an active-risk fix.
  — **Reversibility:** one-way — `release.yml` fires on **any** `v*.*.*` push, so recreating the
  tag later would trigger a brand-new release action, not a clean undo of the deletion.
- **D-08 (item #4 — local gsd-core patches, REVISED during plan-phase 18 discovery):**
  Originally scoped from ROADMAP.md as "stale local ship.md v1 patch, refresh to v2." Live
  discovery during this plan-phase run's `beads-recall` dispatch (`sync.py check-patch ship-md` /
  `check-patch execute-plan`, 2026-08-20) found the real state is worse: **both patches are
  entirely absent from the live installed workflow files**, not merely stale.
  `grep -c "beads\|SHIP_MD_PATCH" ~/.codex/gsd-core/workflows/ship.md` and the same grep against
  `~/.claude/gsd-core/workflows/ship.md` both return 0; `execute-plan.md` in both homes is
  similarly clean. All four files (plus `~/.claude/gsd-local-patches/backup-meta.json`) carry an
  `11:15` timestamp from this session's start — an automatic gsd-core update wiped the patches on
  both runtime homes before this discussion began. Revised scope:
  1. Reapply Patch 1 (`ship:pre` generic gate/step dispatch) and Patch 2 (bd task-content read
     path) verbatim, per `GSD-CORE-PATCH.md`'s "Patch Content (verbatim)" sections and insertion
     anchors, to **both** `~/.codex/gsd-core/workflows/{ship,execute-plan}.md` **and**
     `~/.claude/gsd-core/workflows/{ship,execute-plan}.md` — both homes are live and both are
     wiped, not just one.
  2. Refresh `~/.claude/gsd-local-patches/` to match the reapplied v2 `ship.md` patch and update
     `backup-meta.json`'s `from_version` field — do not delete the backup.
  3. Name the reapply-verification mechanism (`verify-reapply-patches.cjs` + `check-patch`) in
     `GSD-CORE-PATCH.md`, which currently references it nowhere and reads as if manual
     reapplication is the only path (the fix's own stated follow-up in the ROADMAP item text).
  4. After reapplying, re-run `sync.py check-patch ship-md` / `check-patch execute-plan` on both
     homes as the task's acceptance check — must exit 0 with no `⚠` line.
  — **Reversibility:** reversible — local machine files, not shared/tracked state. But **urgency
  is real**: until reapplied, `ship_override` won't fire at `ship:pre` and `gsd-executor` won't
  read task content from `bd` on either runtime home, right now, for any phase — not just Phase 18.

### the agent's Discretion
- Exact wording of the WR-01 docstring rewrite and the WR-01 pinning comment — content direction
  is locked (D-01/D-02), phrasing is the executor's call.
- Exact new `plugin.json` version number (D-06) — minor vs. patch bump, planner's call based on
  the full scope of Phase 18's changes once broken into tasks.
- Whether the `plugin.json` version bump (D-06) lands in its own task/commit or is folded into
  whichever task already touches `CHANGELOG.md` — planner's call.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source of this phase's scope
- `.planning/phases/17-config-code-truth/17-REVIEW.md` — WR-01 through WR-05 findings in full,
  with file:line locations, confidence scores, and suggested fixes. WR-04/WR-05 already resolved;
  WR-01/WR-02/WR-03 are this phase's core scope.
- `.planning/v1.3-MILESTONE-AUDIT.md` — confirms WR-04/WR-05 resolution (commits `373e7fb`,
  `0f8decb`) and the 3 remaining open items, with the exact same file:line references.
- `.planning/ROADMAP.md` lines 274-311 (Phase 17, "Ship-step checks" subsection) — the 5-item
  release-hygiene list; items #1, #3, #4 folded into this phase per the outer-boundary decision
  above; item #2 = D-05; item #5 stays a ship-time verification only.

### Code and docs touched
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` — `PATCH_CHECKS` table
  (lines 136-179), `check_sync_mode_value` docstring (802-804+), `check_patch` body (2296-2322+).
  Note: this is the git-tracked plugin source. `.gsd/capabilities/beads/` (no `plugins/` prefix) is
  a **gitignored runtime mirror** — Phase 16 plan 01 edited the wrong tree once; do not repeat
  that mistake (see STATE.md's "grounding" decision entry).
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md:76` and
  `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md:149` — the "⚠"
  surfacing instructions WR-02 broadens.
- `CHANGELOG.md` — 0.4.0 section (currently lines 5-30ish) and 0.3.1 section (lines 47-87), header
  states versions track `capability.json`.
- `plugins/beads-lifecycle/.claude-plugin/plugin.json` — version field for D-06.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` — needs the reapply-mechanism
  naming addition per D-08.
- `~/.claude/gsd-local-patches/` (outside repo, local machine state) — the stale patch backup D-08
  refreshes; not tracked in git.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PATCH_CHECKS` dict (`sync.py:136-179`) is the existing table-driven pattern for both patch
  targets (`ship-md`, `execute-plan`) — WR-02's fix extends entries already in this table, no new
  structure needed.
- `check_patch()` (`sync.py:2296-2322`) is the single function both `check_shipmd_patch`/
  `check_execute_plan_patch` already thin-wrap (from Phase 17's TRUTH-02 collapse) — WR-01's
  pinning comment attaches to this one function, covers both wrapper call sites.

### Established Patterns
- Test-per-behavior-change discipline: WR-04/WR-05's resolution each landed with a paired
  RED-then-GREEN or parity test (`373e7fb`, `0f8decb`) — same expected discipline for any WR-02
  message-template change (existing `TestPatchChecksTable`-style tests likely need updated
  assertions for the new `⚠` prefixes).
- Doc-sweep-in-same-commit convention: Phase 17's TRUTH-01 plan explicitly did "the full doc sweep
  in the same commit" as the code change — same expectation applies to WR-01/WR-02's SKILL.md and
  docstring edits.

### Integration Points
- `lifecycle_dispatch`'s `plan:pre` branch (`sync.py` ~936-937, ~942) calls `check_shipmd_patch`/
  `check_execute_plan_patch`/`check_sync_mode_value` inside one `try/except Exception` — WR-01/
  WR-02 changes stay inside functions already wired there; no new call sites.
- `hooks/lifecycle-dispatch.sh` promotes only stdout into `additionalContext` — this is *why*
  WR-01's docstring correction matters (a future stderr "fix" would silently break this promotion
  path) and why WR-02's exit-code-based SKILL.md instruction is safe (exit code is already the
  reliable signal `check_patch` returns regardless of message text).

</code_context>

<specifics>
## Specific Ideas

No UI/UX specifics — this is a backend/docs tech-debt phase. The "specific idea" that shaped scope
was the user's own call to widen WR-03 from "add the missing entry" to "also fix the adjacent
miscategorized entry," and then to widen the phase itself to absorb the 3 other ship-hygiene items
rather than leave them as a separate future ship task.

</specifics>

<deferred>
## Deferred Ideas

- ROADMAP.md item #5 (assert `>= 164` tests and runtime-mirror tree identity before trusting
  CI-green) — explicitly kept as a ship-time verification action, not a Phase 18 deliverable. No
  new phase needed; this is the existing ship gate's job.
- Nothing else came up outside phase scope during discussion — all 4 areas stayed within the
  tech-debt/release-hygiene boundary established at the start.

### Reviewed Todos (not folded)
None — `todo.match-phase 18` returned zero matches.

</deferred>

---

*Phase: 18-address-tech-debt-patch-check-doc-accuracy-changelog*
*Context gathered: 2026-08-20*
