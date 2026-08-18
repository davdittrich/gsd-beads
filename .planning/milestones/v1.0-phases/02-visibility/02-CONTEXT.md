# Phase 2: Visibility - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning

<domain>

## Phase Boundary

The planner and executor see live beads issue state as part of their normal operation, and the
projection they read from is always freshly generated, never hand-edited. Covers REQ-B7, REQ-B8,
REQ-B11. Read-only visibility only — no bd write calls beyond what Phase 1 already built
(create-issues, dependency edges, close-wave). No ship-blocking, no gating (that's Phase 3, F3).

</domain>

<decisions>

## Implementation Decisions

### BEADS-RECALL.md scope-matching (B7)
- **D-01:** Determine whether an open issue "touches the phase's scope" by file-path overlap
  first: compare the issue's linked/referenced file paths against the phase's expected
  `files_modified`. If an issue carries no file references, fall back to epic/label match
  (parented under a prior phase's epic that shares files, or a bd label naming the capability
  area).
- **D-02:** An issue matching neither file-path nor epic/label is never silently dropped — list
  it under a separate "Unscoped" heading in BEADS-RECALL.md so the planner can judge relevance
  without a false claim that it definitely touches this phase.
- **D-03:** When BEADS-RECALL.md finds a relevant open issue, planning does not pause for the
  user — the file is written silently and the planner agent reads it the same way it already
  reads RESEARCH.md/PATTERNS.md at `plan:pre`. No new checkpoint UX.
- **D-04:** BEADS-RECALL.md is always written when `bd` is available, even when zero issues
  match — an explicit "none found" body, not a skipped file. This keeps file-presence
  unambiguous: absent means `bd` was unavailable (B6's existing fail-open convention), present
  always means the scope-match ran, whether or not anything was found.

### BEADS.md frontmatter shape (B11)
- **D-05:** Build BEADS.md's frontmatter to the full future shape now — `phase`, `epic`, `open`,
  `closed`, `blocking_open`, `diverged`, `generated_from`, `generated_at` — not just what Phase 2
  reads. `blocking_open`/`diverged` stay at `0` until Phase 3 wires the real counting logic.
  — **Reversibility:** costly — **rationale:** Phase 3's ship gates read this same file via
  `artifact-frontmatter-equals`; adding fields later would mean re-touching every generation call
  site plus every existing BEADS.md on disk, versus getting the schema right once.
- **D-06:** The placeholder `blocking_open`/`diverged` zeros are marked explicitly in BEADS.md's
  body text (e.g. "blocking_open/diverged: not yet computed, Phase 3") so a human reading
  BEADS.md mid-Phase-2 doesn't mistake an unimplemented field for a verified zero. Nothing
  consumes these fields yet (`gates[]` stays empty until Phase 3), so this is a documentation
  safeguard, not a live correctness issue today.
- **D-07:** BEADS.md lives at `${phase_dir}/${padded_phase}-BEADS.md`, matching every other
  per-phase artifact (SUMMARY.md, VERIFICATION.md) so existing phase-dir globbing picks it up
  without new discovery logic.
- **D-08:** The issue table carries 5 columns: issue / title / status / plan task / blocked-by.
  The blocked-by column surfaces Phase 1's dependency edges (B2) without requiring a manual
  `bd show` per issue.

### claim-and-close fragment content (B8)
- **D-09:** The `execute:wave:pre` contribution fragment lists each wave plan's already-synced
  issue ids, titles, and current status (open/closed) read from the current BEADS.md. No soft
  instruction line ("don't create duplicates" etc.) — contributions are prompt text that can
  inform but never force `bd` command compliance (per PRD §"contributions[] may not carry F2"),
  so the fragment states facts only and B8's acceptance criterion ("names the issues in the
  wave") is satisfied by inspection of the composed prompt, not by inferred behavior.
- **D-10:** "Claim" behavior (marking a bd issue `in_progress` when a wave starts) is out of
  scope for Phase 2 — not in B7/B8/B11's acceptance criteria, and Phase 2 makes no new bd write
  calls. The fragment is named for what it actually does (e.g. `wave-issue-status.md`), not the
  PRD's literal `claim-and-close.md`, since that name describes a capability this phase doesn't
  build. See Deferred Ideas.

### beads-status skill reuse vs. new skill
- **D-11:** `beads-status` (built in Phase 1 for `execute:wave:post` batch-close) is reused at
  `execute:wave:pre` too — the skill branches on which lifecycle point it's dispatched from:
  `execute:wave:pre` only regenerates BEADS.md (read-only), `execute:wave:post` regenerates AND
  closes (existing Phase 1 behavior, unchanged). One skill file, matches Phase 1's pattern of
  sharing `sync.py` helpers rather than duplicating them.
- **D-12:** `beads-recall` (the `plan:pre` → BEADS-RECALL.md step) stays a separate, third skill,
  matching the PRD's own three-skill list (`beads-sync`, `beads-recall`, `beads-status`). Its
  scope-matching logic (file-path/epic overlap against open issues) doesn't share meaningfully
  with BEADS.md's plain wave-id lookup — folding it into `beads-status` would be branching for
  its own sake, not real reuse.

### Post-research corrections (02-RESEARCH.md, superseding conflicting decisions above)
- **D-03 (revised):** planner's `<files_to_read>` block is closed/hardcoded — BEADS-RECALL.md is
  NOT auto-read the way D-03 assumed. Add a `plan:pre` `contributions[]` entry (`into: "planner"`,
  confirmed-working slot per RESEARCH.md finding 3) that points the planner at BEADS-RECALL.md.
- **D-09/D-10 (revised):** `execute:wave:pre` has no working contribution-render slot in
  `execute-phase.md` — a `contributions[]` text fragment will not reach the composed executor
  prompt there (unlike `plan:pre`). Drop the fragment approach; `beads-status`'s
  `execute:wave:pre` branch instead explicitly instructs the orchestrator to paste wave-status
  text (issue ids/titles/status) into each executor's composed prompt itself — the pattern the
  one first-party capability that works at this point (`claude-orchestration`) actually uses.
- **D-01 (revised):** no PLAN.md exists yet at `plan:pre` time, so "phase's expected
  `files_modified`" doesn't exist as a field to compare against. `beads-recall`'s file-path tier
  instead greps the phase's ROADMAP.md section text + CONTEXT.md for file paths/module names
  mentioned there. Weaker signal than a real files_modified list, available pre-plan. Epic/label
  match (D-01's second tier) and the "Unscoped" fallback (D-02) are unchanged.

### Claude's Discretion
- Exact BEADS-RECALL.md/BEADS.md markdown formatting beyond the locked column/field lists above.
- Whether the fragment's status list is inline prose or a small table — pick whichever reads
  cleaner in the composed orchestrator prompt.
- Internal helper function names/shapes in `sync.py` for the new BEADS.md/BEADS-RECALL.md
  generation paths, as long as they reuse Phase 1's existing `bd` call and path-confinement
  patterns rather than duplicating them.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product requirements
- `docs/prd-beads-capability.md` §5.2-5.4 — `contributions[]` mechanism, `steps[]` point list,
  BEADS.md example frontmatter/table shape (source for D-05/D-08's baseline, since revised above)
- `docs/prd-beads-capability.md` lines 144-172 — full `capability.json` example showing
  `beads-recall`/`beads-sync`/`beads-status` skill split and the `claim-and-close.md` fragment
  reference (superseded by D-10's rename)
- `.planning/REQUIREMENTS.md` — REQ-B7, REQ-B8, REQ-B11 with acceptance criteria; this phase's
  scope
- `.planning/PROJECT.md` — locked project decisions, constraints, binding model, Phase 1 outcomes

### Phase 1 verified findings (carry forward, do not re-derive)
- `.planning/phases/01-substrate/01-RESEARCH.md` — verified real `capability.json` schema,
  `capability-loader.cts` mechanics (`steps[]`/`contributions[]`/`gates[]`, `when`/`onError`
  semantics), real `bd` v1.2.1 CLI behavior corrections (no `--id`, hierarchical child ids,
  `bd list --parent` hides closed by default), corrected PLAN.md task XML schema
- `.planning/phases/01-substrate/01-01-SUMMARY.md`, `01-02-SUMMARY.md`, `01-03-SUMMARY.md` —
  what `sync.py`/`capability.json`/`beads-sync`/`beads-status` already implement; Phase 2 extends
  this, does not rebuild it
- `.gsd/capabilities/beads/scripts/sync.py` — read before writing any new function; reuse
  `run_bd`, `bd_available`, `confined`, `discover_plan_files`, `append_state_blocker` rather than
  duplicating them
- `.gsd/capabilities/beads/capability.json` — current two-step manifest (`plan:post`,
  `execute:wave:post`); this phase adds `plan:pre` and `execute:wave:pre` entries

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets
- `.gsd/capabilities/beads/scripts/sync.py` — `run_bd`/`bd_available` (single subprocess call
  site, argv-only), `confined`/`find_project_root` (path confinement, T-01-02 pattern),
  `discover_plan_files` (plan-id-to-path resolution, T-01-04/T-01-07 pattern),
  `append_state_blocker` (B6 fail-open notice). Every new BEADS.md/BEADS-RECALL.md generation
  path should call into these, not reimplement subprocess or path handling.
- `.gsd/capabilities/beads/skills/beads-sync/SKILL.md`, `beads-status/SKILL.md` — four-step
  scaffold (banner, config gate, dispatch, one-line report) to copy for the new `beads-recall`
  skill and the `execute:wave:pre` branch of `beads-status`.
- `.gsd/capabilities/beads/tests/test_sync.py` — 27 existing tests, `_make_bd_side_effect`
  pattern for mocking `bd` argv responses; extend rather than replace for BEADS.md/
  BEADS-RECALL.md generation tests.

### Established Patterns
- Every `bd` invocation is argv-list, `shell=False`, single call site (`run_bd`) — T-01-01
  pattern, must extend to any new `bd list`/`bd show` calls this phase adds for issue-state
  reads.
- Fail-open is per-script, not per-call: a mid-operation `bd` failure degrades to the B6 notice +
  STATE.md bullet + exit 0 pattern established in Phase 1's CR-01 fix
  (`.gsd/capabilities/beads/scripts/sync.py:414-440`), not an uncaught exception.

### Integration Points
- `capability.json`'s `steps[]` array gains two entries: `plan:pre` → `beads-recall` (produces
  `BEADS-RECALL.md`, consumes `CONTEXT.md`) and `execute:wave:pre` → `beads-status` (produces
  `BEADS.md`, consumes `PLAN.md`).
- `capability.json`'s `contributions[]` array (currently empty) gains one entry: `execute:wave:pre`
  → `into: orchestrator`, the renamed status fragment (D-10).

</code_context>

<specifics>

## Specific Ideas

No specific UI/UX references — this phase produces markdown artifacts and a prompt fragment, not
user-facing interaction. The gray areas discussed were implementation-shape decisions (scope
matching, frontmatter fields, skill boundaries), already captured above.

</specifics>

<deferred>

## Deferred Ideas

- **Claim behavior** — marking a bd issue `in_progress` when a wave starts, beyond the
  read-only status fragment this phase builds. Not in B7/B8/B11's scope; Phase 2 makes no new
  `bd` write calls. Revisit only if a future phase needs the executor to actively coordinate
  issue ownership across parallel waves.

### Reviewed Todos (not folded)

None — `todo.match-phase` returned zero matches for this phase.

</deferred>

---

*Phase: 2-Visibility*
*Context gathered: 2026-08-15*
