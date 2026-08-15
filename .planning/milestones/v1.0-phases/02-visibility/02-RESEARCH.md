# Phase 2: Visibility - Research

**Researched:** 2026-08-15
**Domain:** gsd-core `contributions[]`/`steps[]` prompt-injection mechanics + `bd` v1.2.1 read-query surface
**Confidence:** HIGH (every load-bearing mechanism claim verified against a live shallow clone of
`open-gsd/gsd-core` @ v1.10.0 — same version as the installed runtime — plus live `bd` v1.2.1
CLI/JSON output captured this session; two claims are flagged MEDIUM where the source is silent
and a design choice is being recommended, not a fact reported)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Determine whether an open issue "touches the phase's scope" by file-path overlap
  first: compare the issue's linked/referenced file paths against the phase's expected
  `files_modified`. If an issue carries no file references, fall back to epic/label match
  (parented under a prior phase's epic that shares files, or a bd label naming the capability
  area).
  **⚠ NUANCED BY THIS RESEARCH** — see "Critical correction: bd has no file-path field" below.
  `bd` has no structured "linked files" field; the primary criterion resolves in practice to two
  concrete techniques, not one generic comparison — see the corrected section for both.
- **D-02:** An issue matching neither file-path nor epic/label is never silently dropped — list
  it under a separate "Unscoped" heading in BEADS-RECALL.md so the planner can judge relevance
  without a false claim that it definitely touches this phase.
- **D-03:** When BEADS-RECALL.md finds a relevant open issue, planning does not pause for the
  user — the file is written silently and the planner agent reads it the same way it already
  reads RESEARCH.md/PATTERNS.md at `plan:pre`. No new checkpoint UX.
  **⚠ NUANCED BY THIS RESEARCH** — see "Critical correction: the planner's `<files_to_read>` list
  is closed, not a directory scan" below. The literal reading mechanism differs from RESEARCH.md's;
  the "no checkpoint" UX intent is unaffected and remains correct as written.
- **D-04:** BEADS-RECALL.md is always written when `bd` is available, even when zero issues
  match — an explicit "none found" body, not a skipped file. This keeps file-presence
  unambiguous: absent means `bd` was unavailable (B6's existing fail-open convention), present
  always means the scope-match ran, whether or not anything was found.
- **D-05:** Build BEADS.md's frontmatter to the full future shape now — `phase`, `epic`, `open`,
  `closed`, `blocking_open`, `diverged`, `generated_from`, `generated_at` — not just what Phase 2
  reads. `blocking_open`/`diverged` stay at `0` until Phase 3 wires the real counting logic.
- **D-06:** The placeholder `blocking_open`/`diverged` zeros are marked explicitly in BEADS.md's
  body text (e.g. "blocking_open/diverged: not yet computed, Phase 3") so a human reading
  BEADS.md mid-Phase-2 doesn't mistake an unimplemented field for a verified zero.
- **D-07:** BEADS.md lives at `${phase_dir}/${padded_phase}-BEADS.md`, matching every other
  per-phase artifact (SUMMARY.md, VERIFICATION.md) so existing phase-dir globbing picks it up
  without new discovery logic.
  **✓ CONFIRMED BY THIS RESEARCH** — directory listing of `.planning/phases/01-substrate/` this
  session shows exactly this convention for every phase-level artifact (01-RESEARCH.md,
  01-VERIFICATION.md, 01-UAT.md, 01-SECURITY.md, etc.). Plan-level artifacts add a second ordinal
  (`01-01-PLAN.md`); BEADS.md/BEADS-RECALL.md are phase-level, so `02-BEADS.md`/
  `02-BEADS-RECALL.md` is correct.
- **D-08:** The issue table carries 5 columns: issue / title / status / plan task / blocked-by.
  The blocked-by column surfaces Phase 1's dependency edges (B2) without requiring a manual
  `bd show` per issue.
  **✓ CONFIRMED BY THIS RESEARCH** — `bd list --parent <epic> --json` already returns each
  issue's `dependencies[]` array with a `type` field (`"blocks"` vs `"parent-child"`), so the
  blocked-by column needs zero extra `bd` calls beyond the one Phase 1 already makes for orphan
  detection — filter `dependencies[]` to `type == "blocks"`.

### Claude's Discretion

- Exact BEADS-RECALL.md/BEADS.md markdown formatting beyond the locked column/field lists above.
- Whether the fragment's status list is inline prose or a small table — pick whichever reads
  cleaner in the composed orchestrator prompt.
- Internal helper function names/shapes in `sync.py` for the new BEADS.md/BEADS-RECALL.md
  generation paths, as long as they reuse Phase 1's existing `bd` call and path-confinement
  patterns rather than duplicating them.

### Deferred Ideas (OUT OF SCOPE)

- **Claim behavior** — marking a bd issue `in_progress` when a wave starts, beyond the
  read-only status fragment this phase builds. Not in B7/B8/B11's scope; Phase 2 makes no new
  `bd` write calls.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| B7 | Planner sees open issues before planning; `BEADS-RECALL.md` exists and names any matching issue | Real `bd list` filter flags for status/label/parent/description-substring queries verified live; two concrete file-matching techniques identified (`bd` has no structured file field); verified the planner's `<files_to_read>` block will NOT auto-discover BEADS-RECALL.md — a `contributions[]` entry at `plan:pre` `into: "planner"` is the confirmed-working way to guarantee the planner actually sees it, on top of the file always existing |
| B8 | `execute:wave:pre` fragment present in composed orchestrator prompt, names wave issues, verified by direct prompt inspection | Read `execute-phase.md` step 2.75 line-by-line: no template slot exists for `contribution`-kind fragment text there (unlike `plan:pre`'s confirmed line-731 slot); first-party `claude-orchestration` capability is the only real precedent for a `contributions[]` entry at this exact point, and it works by instructing the orchestrator's own subsequent actions, not by string-substitution; primary recommendation is a `step`-only design (matches D-11) that sidesteps the ambiguity entirely |
| B11 | `BEADS.md` regenerated from a real `bd` query at every step; hand edits overwritten | Verified `bd list --parent <epic> --all --json` JSON shape live (id/title/status/type/dependencies[]); verified phase-level artifact naming convention against real files on disk; identified a `-n 0` truncation pitfall present in Phase 1's own `sync.py` that Phase 2's larger queries must not repeat |

</phase_requirements>

## Summary

Phase 2 adds two new artifacts (`BEADS-RECALL.md` at `plan:pre`, a regenerated `BEADS.md` at
`execute:wave:pre`) and one prompt-visibility requirement (B8) to the `beads` capability built in
Phase 1. The `bd` side is straightforward: every flag D-01/D-08 need (`--status`, `--label`,
`--label-any`, `--parent`, `--desc-contains`, `--exclude-type`) is a real, verified flag on the
locally installed `bd` v1.2.1, and `bd list --json`'s response shape (captured live this session)
already carries everything BEADS.md's 5-column table needs — including dependency edges — from a
single query, with no new `bd` subcommand required beyond what Phase 1's `sync.py` already calls.

The gsd-core side is where this phase's real risk lives, and it is **not** where CONTEXT.md's
D-03/D-09 assumed. Reading `execute-phase.md` and `plan-phase.md` verbatim (same 1.10.0 source
Phase 1 verified) shows the two `plan:pre`/`execute:wave:pre` extension points do **not** behave
symmetrically for prompt injection: `plan:pre` has a literal, working template slot
(`plan-phase.md:731`) that injects `contributions[]` fragments directly into the planner
subagent's prompt — but `execute:wave:pre` has no equivalent slot anywhere in `execute-phase.md`;
the JSON is fetched into a bash variable and never referenced again except for one terse
"alternate wave dispatch" branch. A real first-party capability
(`capabilities/claude-orchestration/`) is the only shipped precedent for using
`execute:wave:pre`'s `contributions[]` point, and it works by writing prose that tells the
**orchestrator itself** what to do next — not by any automatic text-substitution gsd-core
performs. Given this, B8 is more reliably and more simply satisfied by extending the
already-planned `step`-kind `beads-status` skill (D-11) with explicit instructions telling the
orchestrator to read the freshly regenerated `BEADS.md` and copy the wave's issue list directly
into the text it composes for each executor's `Agent()` dispatch — a mechanism this project
already knows works (Phase 1's entire skill-mediated dispatch model), rather than depending on
`execute:wave:pre`'s unverified/unprecedented-for-`into:"orchestrator"` contribution rendering.

Separately, this research found that the planner's own `<files_to_read>` block
(`plan-phase.md:684-708`) is a **closed, hardcoded list of named path variables** — RESEARCH.md
and PATTERNS.md are on that list by name; a third-party capability's own artifact is not, and
never will be without a gsd-core patch (forbidden, N2). D-03's claim that the planner reads
BEADS-RECALL.md "the same way" it reads RESEARCH.md is therefore not literally accurate as a
mechanism claim, though B7's actual acceptance criterion (file exists and names the issue) does
not require the planner to have read it — only that the artifact exist. Since `plan:pre`'s
contribution-into-planner slot IS confirmed working (unlike execute:wave:pre's), adding a small
static contribution fragment there is a low-risk way to close the gap between B7's literal test
and the phase goal's actual intent ("the planner ... sees live beads issue state").

**Primary recommendation:** Ship `BEADS-RECALL.md`/`BEADS.md` generation purely through
`steps[]` (two new skill dispatches: `beads-recall` at `plan:pre`, a read-only `execute:wave:pre`
branch added to the existing `beads-status` skill per D-11) with **zero new `contributions[]`
entries required to pass B7/B8/B11's literal acceptance criteria** — B7 is satisfied by the file
existing (already true under D-03/D-04), and B8 is satisfied by having `beads-status`'s own
SKILL.md instruct the orchestrator to paste the wave's issue-status text directly into each
executor's composed prompt at step 3, verified by grepping that composed `prompt=` string. A
single small `contributions[]` entry at `plan:pre` `into: "planner"` is offered as a
low-risk, PRD-aligned strengthening for B7 (not required to pass B7's test, but closes the gap to
the phase's stated goal) — do **not** add the PRD's `execute:wave:pre` contribution
(`claim-and-close.md`/D-09's fragment) at all, given the unverified/undocumented rendering
behavior at that specific point for `into:"orchestrator"`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Open-issue scope matching (B7) | `beads-recall` skill + Python helper | `bd` (query engine) | No gsd-core involvement — pure capability-internal query + text-match logic, same shape as Phase 1's sync logic |
| Planner awareness of BEADS-RECALL.md (B7 goal, beyond the literal test) | gsd-core loop (`plan:pre` contribution-into-planner dispatch, confirmed working) | `beads-recall` skill (fragment content author) | The injection mechanism is gsd-core's (verified template slot); the fragment's static prose is capability-owned |
| BEADS.md regeneration (B11) | `beads-status` skill + Python helper | `bd` (query engine) | Same shape as B7 — capability-owned query + render, no gsd-core involvement |
| Wave-issue visibility in composed executor prompts (B8) | `beads-status` skill (explicit orchestrator instruction) | gsd-core loop (`step` dispatch mechanism only — NOT contribution rendering at this point) | Verified gsd-core has no template slot for `contribution`-kind text at `execute:wave:pre`; the orchestrator must be told, by the skill's own prose, to manually carry the content into the next prompt it composes — this is capability-owned, gsd-core only provides the Skill-tool dispatch |
| Prompt-injection mechanics generally | gsd-core loop (`loop-resolver.cts` + each workflow's own template) | — | Per-point behavior differs; verified NOT uniform across the 12-point vocabulary despite the point-agnostic dispatch *contract* being uniform — see Critical corrections below |

## Standard Stack

### Core

| Component | Version | Purpose | Why Standard |
|---|---|---|---|
| `bd` (beads CLI) | 1.2.1 [VERIFIED: `bd --version`, this session — unchanged since Phase 1] | Issue query surface for recall + status | Already the project's substrate; no new tool needed |
| Python 3 stdlib | 3.14.7 [VERIFIED: `python3 --version`, this session, unchanged since Phase 1] | BEADS-RECALL.md/BEADS.md generation logic, extending `sync.py` | N5 forbids any other dependency |
| gsd-core capability manifest (`capability.json`) | schema current as of gsd-core 1.10.0 [VERIFIED: local `~/.claude/gsd-core/VERSION` == `npm view @opengsd/gsd-core version` == `1.10.0`, this session] | Declares the two new `steps[]` entries | Only supported extension mechanism |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `steps[]`-only design for B8 (this research's primary recommendation) | PRD's original `contributions[]` entry at `execute:wave:pre` `into:"orchestrator"` (`claim-and-close.md`) | The PRD's own §11 Risks table already flags this exact risk ("`contributions[]` may not carry F2 ... If fragments prove weak, fall back to `BEADS-RECALL.md` as a consumed artifact") and recommends exactly the fallback this research arrives at independently. The `contributions[]` form is not proven broken — a real first-party capability (`claude-orchestration`) uses it successfully at this exact point — but that capability's fragment works by directing the orchestrator's *subsequent behavior*, not by literal text substitution, and `execute-phase.md` has zero explicit `into=="orchestrator"` handling to point to. The `steps[]`-only design uses only mechanisms this project has already proven work (Phase 1's entire skill-dispatch model). |
| File-path substring matching via `bd list --desc-contains <fragment>` | A structured `--metadata '{"files":[...]}'` JSON blob set at issue-create time, queried via `--has-metadata-key files` | `bd`'s `--metadata-field` filter is exact key=value match, not substring/array-membership match — awkward for path lists. Phase 1's `sync.py` never sets `--description`/`--metadata` on task issues today (title-only), so this technique only helps for issues *not* created by this capability's own sync flow; substring matching against `--desc-contains` is simpler and needs no schema change to Phase 1's issue-creation call. |

**Installation:** No package installation — `bd` binary + Python 3 stdlib only, per N5, unchanged
from Phase 1.

## Package Legitimacy Audit

**Not applicable.** This phase installs zero external packages — same N5 constraint as Phase 1.
No `package-legitimacy check` run was needed.

## Critical correction: `bd` has no file-path field — D-01's "file-path overlap" resolves to two concrete techniques

`bd list --help` and `bd create --help` (both captured live this session) show the full flag
surface of `bd` v1.2.1: there is **no** `--file`/`--files` filter and no structured "linked
files" field on an issue. The only content-substring filters are `--desc-contains`,
`--notes-contains`, and `--external-contains`; the only structured tag mechanism is `--label`/
`--label-any`/`--label-pattern`/`--label-regex`.

```
--desc-contains string         Filter by description substring (case-insensitive)
--notes-contains string        Filter by notes substring (case-insensitive)
-l, --label strings            Filter by labels (AND: must have ALL). Can combine with --label-any
--label-any strings            Filter by labels (OR: must have AT LEAST ONE). Can combine with --label
--parent string                Filter by parent issue ID (shows children of specified issue)
```
[VERIFIED: `bd list --help` output, this session, locally installed `bd` v1.2.1]

Furthermore, Phase 1's own `sync.py::resolve_issue` creates every task issue with **title only**
— no `--description`, no `--metadata` (confirmed by reading `resolve_issue` in
`.gsd/capabilities/beads/scripts/sync.py`, this session: the only `bd create` call passes
`title`, `--type`, `--parent`, `--silent`). This means **file-path text does not exist anywhere
on a beads-sync-created issue** — a `--desc-contains` scan will never match one of this project's
own issues.

D-01's "file-path overlap" therefore resolves in practice to two distinct, non-overlapping
techniques, both of which `beads-recall` needs to implement — this is a genuine design decision
the plan must make explicit, not a single `bd` query:

1. **Reverse lookup via `<beads-id>` (covers this capability's own issues).** For each open
   issue, find the `PLAN.md` task (in any prior phase directory) whose `<beads-id>` matches, and
   read that task's `<files>` element (verified real field, Phase 1 research:
   `<files>path/to/file.ext, another/file.ext</files>`). Compare those paths against the current
   phase's expected `files_modified`. This is the only reliable file-scope source for issues this
   project itself created.
2. **`bd list --desc-contains <path-fragment>` (covers externally/hand-filed issues).** For an
   issue not created by `beads-sync` (no matching `<beads-id>` anywhere), the only file-path
   signal `bd` can supply is a substring match against free-text `description`/`notes` fields, if
   the filer happened to mention a path there.

Neither technique needs a new `bd` subcommand; both are read-only `bd list`/`bd show --json`
calls layered with Python-side text matching in the beads-recall script.

## Critical correction: the planner's `<files_to_read>` list is closed, not a directory scan

`plan-phase.md`'s planner subagent dispatch (`◆ Spawning planner...`) builds an explicit
`<files_to_read>` block from a **fixed, named set** of path variables:

> "**File paths (for `<files_to_read>` blocks):** `state_path`, `roadmap_path`,
> `requirements_path`, `context_path`, `research_path`, `verification_path`, `uat_path`,
> `reviews_path`."
[VERIFIED: `gsd-core/workflows/plan-phase.md:95`]

```
<files_to_read>
- {state_path} (Project State)
- {roadmap_path} (Roadmap)
- {requirements_path} (Requirements)
- {context_path} (USER DECISIONS from /gsd-discuss-phase)
- {research_path} (Technical Research)
- {PATTERNS_PATH} (Pattern Map ...)
...
</files_to_read>
```
[VERIFIED: `gsd-core/workflows/plan-phase.md:684-708`, full block — no wildcard/glob entry]

This list has no entry for a third-party capability's own artifact, and none is added
dynamically — RESEARCH.md/PATTERNS.md appear because gsd-core's own template names them
explicitly, not because the planner "reads whatever's in the phase directory." A file named
`BEADS-RECALL.md` sitting in `.planning/phases/02-visibility/` will **not** be read by the
planner subagent through this mechanism, regardless of D-04's guarantee that it always exists.

**What actually is confirmed working** at `plan:pre` is the contribution-injection slot two
sections below the `<files_to_read>` block, in the same prompt template:

```
731: {For each active entry in `PLAN_PRE_HOOKS_JSON` where `kind == "contribution"` and
     `into == "planner"` (in array order): inject the entry's `fragment.inline` verbatim here.
     This delivers all planner-targeted contributions — including tdd's `<tdd_mode_active>`
     block ... If no active planner contributions exist, omit this block entirely.}
```
[VERIFIED: `gsd-core/workflows/plan-phase.md:731`, literal quote]

**Consequence:** D-03's underlying UX intent ("no checkpoint, written silently") is unaffected
and remains correct — but its stated mechanism ("the planner reads it the same way it already
reads RESEARCH.md") does not hold literally. B7's acceptance criterion only requires the file to
exist and name the issue (it does), so this does not block B7's test. But if the phase's actual
goal statement — "the planner ... sees live beads issue state as part of their normal
operation" — is meant literally, the low-risk way to guarantee that is a small, **static**
`contributions[]` entry at `plan:pre`, `into: "planner"` (fragment text along the lines of "an
open-issue recall for this phase exists at `BEADS-RECALL.md` in this phase's directory — read it
before finalizing task scope"), using the confirmed-working slot above. This is a pointer, not an
attempt to embed live per-issue data in a static fragment (see next section for why that
distinction matters).

## Critical correction: `execute:wave:pre` has no equivalent contribution-rendering slot

Unlike `plan:pre`, `execute-phase.md`'s handling of `execute:wave:pre` is a single terse line:

```
641:   2.75. **Execute:wave:pre capability dispatch:**
644:   WAVE_PRE_HOOKS_JSON=$(gsd_run loop render-hooks execute:wave:pre --raw)
647:   If a contribution's `activeHooks` entry provides an alternate wave dispatch, follow it
       instead of step 3's inline loop; otherwise proceed to step 3.
```
[VERIFIED: `gsd-core/workflows/execute-phase.md:641-647`, literal quote]

A full-file search for `kind == "contribution"`, `fragment.inline`, or any `into=="orchestrator"`
handling in `execute-phase.md` returns **zero matches** [VERIFIED: repo-wide grep against the
1.10.0 clone, this session]. The variable `WAVE_PRE_HOOKS_JSON` is assigned once at line 644 and
never referenced again anywhere else in the file. Step 3's `Agent()` prompt template for
executors (lines 703-777, read in full this session) has a fixed, closed set of blocks
(`<objective>`, `<worktree_branch_check>`, `<parallel_execution>`, `<execution_context>`,
`<files_to_read>`, `${AGENT_SKILLS}`, `<mcp_tools>`, `<success_criteria>`) — no placeholder of any
kind for capability-contributed content.

This is not merely a gap this project happened to hit — it is independently confirmed by a real
first-party gsd-core capability. `capabilities/external-job/capability.json`'s own description
states, verbatim:

> "NOTE on contribution point: #1164 specifies execute:wave:pre, but execute-phase.md only
> dispatches execute:wave:post today (wave:pre is declared in the loop host contract but not
> rendered); wiring wave:pre dispatch is a core-loop change #1164 explicitly puts out of scope,
> so this capability registers at wave:post instead."
[VERIFIED: `gsd-core/capabilities/external-job/capability.json`, `description` field, this
session]

The **one** shipped capability that does successfully use `execute:wave:pre`'s `contributions[]`
point is `capabilities/claude-orchestration/`, registered `into: "executor"` (not
`"orchestrator"`):

```json
"contributions": [{
  "point": "execute:wave:pre", "into": "executor",
  "fragment": { "path": "fragments/execute-wave-pre.md" },
  "produces": [], "consumes": ["PLAN.md"],
  "when": "claude_orchestration.enabled", "onError": "skip"
}]
```
[VERIFIED: `gsd-core/capabilities/claude-orchestration/capability.json:56-70`]

Its fragment file explains **why** this mechanism works despite `execute-phase.md` having no
literal template slot for it — the fragment's own prose *is* the mechanism, read and acted on by
the orchestrator directly:

> "Before spawning executor agents for the current wave (execute-phase.md step 3), resolve the
> dispatch backend through the single composed CLI seam..."
[VERIFIED: `gsd-core/capabilities/claude-orchestration/fragments/execute-wave-pre.md`, this
session]

**Consequence for B8:** `execute:wave:pre`'s `contributions[]` mechanism is real (the fragment
text does reach the orchestrator's own context, because the orchestrator itself runs the
`render-hooks` bash call and its stdout becomes part of the orchestrator's transcript) — but
there is **no gsd-core-provided step that automatically forwards that text into the executor's
composed `Agent()` prompt**. The only working precedent achieves its effect by instructing the
orchestrator's *subsequent manual actions*, not by text substitution. `into: "orchestrator"`
(D-09's choice, matching the PRD) is syntactically legal — `into` values are not validated
against a fixed enum anywhere in the loader/validator source [VERIFIED: zero matches for a
literal `'orchestrator'`/`"orchestrator"` string constant anywhere in `src/*.cts`, this session]
— but its rendering behavior at this specific point has no first-party precedent to point to, and
the "must be a role published by that loop extension point in the host contract" line in the
manifest reference doc is **documentation guidance only, not code-enforced**.

There is also a materialization-timing subtlety worth flagging even if `contributions[]` were
used: `fragment.path` content is "materialised (read and inlined) at **load time**" [VERIFIED:
`gsd-core/docs/reference/capability-manifest.md:84`] — i.e. once per `gsd_run` process
invocation, from whatever is on disk *before* that invocation starts. `execute-phase.md` calls
`render-hooks execute:wave:pre` exactly once per wave, before `beads-status`'s own `step` has had
a chance to run and (if it tried to) rewrite a fragment file with the current wave's live issue
list — so a `contributions[]`-based design risks carrying stale (previous-wave) data even where
the rendering mechanism itself works. **Static, pointer-style fragment text is safe; embedding
live per-invocation data directly in a contribution fragment is not**, for either B7 or B8.

**Primary recommendation (matches D-11, adds nothing new to the manifest's `contributions[]`
array):** Extend `beads-status`'s `step`-kind dispatch (already registered at `execute:wave:post`,
now also at `execute:wave:pre` per D-11's read-only branch) with an explicit instruction in its
own SKILL.md: after regenerating BEADS.md, **read it back with the Read tool**, then **compose a
short block (e.g. `<beads_status>`) naming this wave's issue ids/titles/status** and instruct the
orchestrator to include that block verbatim inside each executor `Agent()` call's `prompt=`
string at step 3. This is provably inspectable (grep the literal `prompt=` text any Agent() call
receives) and depends on nothing beyond the Skill-tool + Read-tool dispatch model this project's
Phase 1 already proved works end-to-end.

## Architecture Patterns

### System Architecture Diagram

```
plan:pre                                          execute:wave:pre (per wave, before Agent() spawns)
  │                                                  │
  ▼                                                  ▼
gsd_run loop render-hooks plan:pre --raw       gsd_run loop render-hooks execute:wave:pre --raw
  │  (fetched once, cached in PLAN_PRE_HOOKS_JSON)   │  (WAVE_PRE_HOOKS_JSON — captured, never
  ▼                                                  │   referenced again by execute-phase.md)
Skill(skill="gsd-beads-recall")                      ▼
  │                                            Skill(skill="gsd-beads-status", args=[phase_dir,
  │ SKILL.md instructs the agent:                    wave plan ids])
  │  1. command -v bd || skip (B6)                   │
  │  2. python3 sync.py beads-recall <phase_dir>      │ SKILL.md instructs the agent:
  │     - list all open issues (bd list --status      │  1. bd-availability gate (delegated to
  │       open,in_progress,blocked,deferred            │     sync.py, B6)
  │       --exclude-type epic --json -n 0)            │  2. python3 sync.py wave-status
  │     - for each: reverse-lookup <beads-id> across   │     <phase_dir> <plan ids...>
  │       every phase's PLAN.md <files> elements        │     - bd list --parent <epic> --all
  │       (technique 1); else bd list --desc-contains   │       --json -n 0 (same call Phase 1's
  │       <fragment> (technique 2)                       │       orphan sweep already makes)
  │     - match against this phase's files_modified     │     - regenerate BEADS.md (D-05..D-08
  │     - write BEADS-RECALL.md (D-01..D-04)             │       frontmatter/table)
  ▼                                                       │     - filter to this wave's plan ids'
BEADS-RECALL.md written to                                │       <beads-id>s for the status block
${phase_dir}/${padded_phase}-BEADS-RECALL.md               ▼
  │                                                  BEADS.md regenerated at
  │ planner subagent spawned (◆ Spawning planner...)  ${phase_dir}/${padded_phase}-BEADS.md
  │  <files_to_read> is a CLOSED list — does NOT       │
  │  auto-include BEADS-RECALL.md (verified)           │ 3. Read BEADS.md back; compose
  │  (optional, low-risk addition: a static             │    <beads_status> block naming this
  │   contributions[] pointer fragment into:"planner"    │    wave's issues
  │   at plan:pre — confirmed-working slot at            ▼
  │   plan-phase.md:731 — pointing at the file,     Orchestrator proceeds to step 3, includes
  │   NOT embedding live data)                       <beads_status> block verbatim in each
  ▼                                                  executor Agent() prompt=... string
Planner may independently Read                       (this is the literal text B8's acceptance
BEADS-RECALL.md if instructed to by the               criterion is checked against)
contribution fragment above, or if the plan's
own task-scoping surfaces it
```

### Recommended Project Structure (additions to Phase 1's tree)

```
.gsd/capabilities/beads/
├── capability.json              # +2 steps[] entries: plan:pre -> beads-recall,
│                                 #   execute:wave:pre -> beads-status (read-only branch)
├── skills/
│   ├── beads-sync/SKILL.md      # unchanged (Phase 1)
│   ├── beads-status/SKILL.md    # extended: branches on lifecycle point (D-11); read-only
│   │                             #   regen at execute:wave:pre, regen+close at execute:wave:post
│   └── beads-recall/SKILL.md    # new (Phase 2): plan:pre scope-matching skill
└── scripts/
    └── sync.py                  # +beads-recall subcommand, +wave-status/BEADS.md-render helpers
                                  #   (reuse run_bd/bd_available/confined/discover_plan_files)
```

### Pattern 1: Static contribution fragments are pointers, not payloads

**What:** A `contributions[]` fragment's text is materialized once per `gsd_run` process
invocation from a file on disk — it cannot reliably carry per-invocation live data computed by a
`step` dispatched in the *same* render-hooks response, because the fragment materialization and
the step dispatch are not ordered relative to each other by anything in `execute-phase.md`/
`plan-phase.md`. Fragment text should point at a regenerated artifact ("check BEADS.md"), never
attempt to embed the artifact's current content directly.
**When to use:** Any contribution this capability ever adds, at any point.
**Example:** See `capabilities/claude-orchestration/fragments/execute-wave-pre.md` — its prose
tells the orchestrator to run a **fresh command** (`resolve-wave-dispatch`) rather than embedding
any dispatch decision as static text.

### Pattern 2: Skill-mediated dispatch is the reliable channel; contributions are the unreliable one

**What:** Every mechanism this project's Phase 1 already used (Skill-tool dispatch of
`ref.skill`, the skill's own SKILL.md prose directing subsequent Bash/Read/Write tool calls) is
verified working end-to-end (27 passing tests, a real `bd` database proof). The `contributions[]`
mechanism's reliability varies **by point** — confirmed working with a literal template slot at
`plan:pre` `into:"planner"`, confirmed working-but-informal (fragment content read into the
orchestrator's own context, no template slot) at `execute:wave:pre`, and confirmed **not
rendered at all** at `execute:wave:pre` for `execute:wave:post`-style consumers per the
`external-job` capability's own admission.
**When to use:** Prefer `steps[]` + explicit SKILL.md instructions for anything load-bearing;
reserve `contributions[]` for short, static, non-critical pointer text.

### Anti-Patterns to Avoid

- **Embedding live per-wave issue data directly in a `contributions[]` fragment file.** The
  materialization timing (`load time` == process start, not "after this wave's step ran") makes
  this a source of silently-stale data. Regenerate the artifact (BEADS.md); point to it.
- **Assuming `<files_to_read>` auto-discovers new phase-directory files.** It is a closed,
  hardcoded list (`plan-phase.md:95,684-708`). A capability's own artifact needs either an
  explicit contribution-into-planner pointer, or reliance purely on the file's existence
  satisfying the requirement's literal test (which is what B7 actually requires).
- **Treating `execute:wave:pre` and `plan:pre` as symmetric extension points.** They share a
  JSON schema (`loop-hook-dispatch.md`'s point-agnostic envelope) but not equivalent workflow-file
  wiring. Verify each point's actual consuming workflow file before assuming a mechanism "just
  works" because it works at a different point.
- **`bd list` without `-n 0`.** Default limit is 50 [VERIFIED: `bd list --help`, `-n, --limit int
  ... (default 50)`]. Phase 1's own `sync.py` orphan sweep (`run_bd(["bd", "list", "--parent",
  epic_id, "--all", "--json"])`) already omits `-n`, silently capping at 50 results for a large
  epic — Phase 2's larger, cross-phase BEADS-RECALL.md queries must explicitly pass `-n 0` (or an
  intentionally high bound) to avoid the same latent truncation, and it is worth flagging the
  existing Phase 1 call site for a follow-up fix even though it is out of this phase's scope to
  rewrite.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dependency-edge lookup for the blocked-by column | A second `bd dep` traversal query | `dependencies[]` already present in `bd list --parent <epic> --json`'s response, filtered to `type=="blocks"` | Verified live this session — zero extra `bd` calls needed |
| Open-issue status enum handling | A custom "what counts as open" list | The verified real status enum: `open, in_progress, blocked, deferred, closed` [VERIFIED: `bd list --help`, `-s, --status string` flag description] — matches what Phase 1's `filter_open_ids` already uses | Consistency with Phase 1's existing filter string avoids a second, possibly-drifting definition of "open" |
| Cross-phase PLAN.md scanning for `<beads-id>` reverse lookup | A new indexing/caching layer | `discover_plan_files`-style directory scan, reused per-phase-directory across `.planning/phases/*/`, same regex (`BEADS_ID_RE`, `TASK_RE`) already in `sync.py` | Phase 1 already wrote and tested this exact parsing logic for one phase directory; extending it to iterate every phase directory is a loop, not new logic |

**Key insight:** every new capability this phase needs (file-scope matching, wave-status
rendering) decomposes into `bd list --json` + string/regex matching Python already has from
Phase 1 — the only genuinely new engineering is process-level (which lifecycle point, which
prompt actually receives the text), not query-level.

## Common Pitfalls

### Pitfall 1: Trusting `contributions[]` at `execute:wave:pre` to reach the executor's prompt automatically
**What goes wrong:** A capability.json entry `{"point": "execute:wave:pre", "into":
"orchestrator", "fragment": {...}}` is added, `render-hooks execute:wave:pre --raw` correctly
returns it in `activeHooks`, and the implementer assumes B8 is now satisfied — but nothing in
`execute-phase.md` forwards that text into any `Agent()` call's `prompt=` string, so a literal
inspection of the composed executor prompt shows no trace of it.
**Why it happens:** `plan:pre` has a working template slot for the analogous case, creating a
false expectation that every point behaves the same way.
**How to avoid:** Use the `step`-only design (Pattern 2) for B8; verify by grepping the actual
`prompt=` string an `Agent()` call receives, not the `render-hooks --raw` JSON output alone.
**Warning signs:** `WAVE_PRE_HOOKS_JSON` is set and non-empty, but the wave's `Agent()` prompt
contains no issue ids when inspected directly.

### Pitfall 2: Capability-consent hash invalidation after adding Phase 2's new files
**What goes wrong:** Phase 2 adds a new `beads-recall/SKILL.md`, extends `capability.json`'s
`steps[]` array, and extends `sync.py` — every one of these edits changes the bundle's content
hash. Phase 1's own VERIFICATION.md documents this exact failure hitting this project already:
a post-consent code-review fix silently deactivated the capability until `capability install
--scope project` was re-run.
**Why it happens:** Project-scope consent binds to a recomputed sha512 over the *whole* bundle
[VERIFIED: `gsd-core/src/capability-loader.cts:685-693,704-714`, this session — same lines Phase
1's research cited], so any file edit inside `.gsd/capabilities/beads/` after the last consent
grant deactivates every step/contribution/gate the manifest declares, silently.
**How to avoid:** The plan must include a re-install/re-consent task (or checkpoint) as one of
the last steps of the phase, after all file edits land, mirroring Phase 1's own remediation
(`85aff2a`).
**Warning signs:** `gsd_run loop render-hooks plan:pre --raw` (or `execute:wave:pre`) returns an
`activeHooks` array missing the new beads-recall/beads-status entries even though
`capability.json` on disk correctly declares them.

### Pitfall 3: `bd list` default limit of 50 silently truncating BEADS-RECALL.md's scan
**What goes wrong:** A project with more than 50 open issues across all phases gets a
BEADS-RECALL.md that silently omits some open, in-scope issues — no error, just fewer rows than
reality.
**Why it happens:** `-n, --limit int` defaults to 50 on every `bd list` call unless explicitly
overridden [VERIFIED: `bd list --help`, this session].
**How to avoid:** Every new `bd list` call this phase adds (the recall scan, the wave-status
regen) must pass `-n 0` explicitly.
**Warning signs:** `bd list --status open,... --json | jq length` returns exactly 50 in a project
known to have more open issues.

### Pitfall 4: Assuming `into` values are validated against a fixed per-point role enum
**What goes wrong:** Choosing an `into` value based on what "sounds right" (e.g. `"orchestrator"`
vs `"executor"`) and expecting the loader to reject an invalid choice with a clear error if wrong.
**Why it happens:** The manifest reference doc says "Must be a role published by that loop
extension point in the host contract," implying enforcement.
**How to avoid:** Treat that line as documentation guidance, not a code-enforced contract —
verified zero matches for any hardcoded role-enum check anywhere in `src/*.cts` this session. The
real test is whether some workflow file's prose actually branches on that `into` value, not
whether the loader accepted the manifest.
**Warning signs:** A manifest with a semantically wrong `into` value loads and installs without
any warning; the only symptom is silent absence downstream.

## Code Examples

### `capability.json` additions for Phase 2 (steps only, no new contributions)

```json
// Source: schema verified against gsd-core/docs/reference/capability-manifest.md (steps table)
// and this repo's own Phase 1 capability.json shape, extended per D-11.
{
  "steps": [
    { "point": "plan:pre", "ref": { "skill": "beads-recall" },
      "produces": ["BEADS-RECALL.md"], "consumes": ["CONTEXT.md"],
      "when": "beads.enabled", "onError": "skip" },
    { "point": "plan:post", "ref": { "skill": "beads-sync" },
      "produces": ["BEADS.md"], "consumes": ["PLAN.md"],
      "when": "beads.enabled", "onError": "skip" },
    { "point": "execute:wave:pre", "ref": { "skill": "beads-status" },
      "produces": ["BEADS.md"], "consumes": ["PLAN.md"],
      "when": "beads.enabled", "onError": "skip" },
    { "point": "execute:wave:post", "ref": { "skill": "beads-status" },
      "produces": ["BEADS.md"], "consumes": ["PLAN.md"],
      "when": "beads.enabled", "onError": "skip" }
  ]
}
```
*Note:* both `execute:wave:pre` and `execute:wave:post` entries point at the same
`ref.skill: "beads-status"` — D-11's design; the skill branches internally on which lifecycle
point invoked it (its own `$ARGUMENTS`/dispatch context tells it which), matching the existing
`beads-sync`/`beads-status` two-skill split already shipped in Phase 1.

### Optional low-risk `plan:pre` contribution for B7 (static pointer only, per Pattern 1)

```json
{
  "contributions": [
    { "point": "plan:pre", "into": "planner",
      "produces": [], "consumes": ["BEADS-RECALL.md"],
      "fragment": { "path": "fragments/recall-pointer.md" },
      "when": "beads.enabled", "onError": "skip" }
  ]
}
```
`fragments/recall-pointer.md` should be **short, static prose** — e.g. "This phase's
BEADS-RECALL.md (open beads issues that may touch this phase's scope) is at
`{phase_dir}/{padded_phase}-BEADS-RECALL.md` — read it before finalizing task scope." — never an
attempt to embed the live issue list itself (Pattern 1). This uses the confirmed-working
`plan-phase.md:731` slot.

### Verified `bd` invocations for BEADS-RECALL.md / BEADS.md generation

```bash
# Open-issue scan for BEADS-RECALL.md (B7) — exclude epics, no truncation
bd list --status open,in_progress,blocked,deferred --exclude-type epic --json -n 0

# Technique 2 fallback: description-substring file-path match (for non-sync-created issues)
bd list --status open,in_progress,blocked,deferred --desc-contains "src/foo.ts" --json -n 0

# BEADS.md issue table (B11) — same call Phase 1's orphan sweep already makes, add -n 0
bd list --parent "$EPIC_ID" --all --json -n 0
```
[VERIFIED: every flag quoted from `bd list --help` output captured this session against the
locally installed `bd` v1.2.1 binary; JSON response shape (id/title/status/issue_type/
dependencies[]/parent) captured live against a scratch `bd init` database this session]

### Real `bd list --json` response shape (blocked-by column source, D-08)

```json
[
  {
    "id": "bd-probe-fi6.2",
    "title": "Task two",
    "status": "open",
    "issue_type": "task",
    "parent": "bd-probe-fi6",
    "dependencies": [
      { "issue_id": "bd-probe-fi6.2", "depends_on_id": "bd-probe-fi6",
        "type": "parent-child", "created_at": "...", "created_by": "...", "metadata": "{}" },
      { "issue_id": "bd-probe-fi6.2", "depends_on_id": "bd-probe-fi6.1",
        "type": "blocks", "created_at": "...", "created_by": "...", "metadata": "{}" }
    ],
    "dependency_count": 1, "dependent_count": 0, "comment_count": 0
  }
]
```
[VERIFIED: `bd list --parent <epic> --json` output, captured live this session against a scratch
`bd init` database — the "blocked-by" column is `dependencies[]` filtered to `type == "blocks"`;
`type == "parent-child"` is the epic-parent edge and must be excluded from that column]

## State of the Art

| Old (assumed) | Corrected (verified) | When Changed | Impact |
|--------------|------------------|-----------|--------|
| `contributions[]` behaves uniformly across all 12 loop points | Confirmed working at `plan:pre` `into:"planner"` (literal template slot); confirmed real-but-informal at `execute:wave:pre` (fragment text reaches orchestrator's own context, no automatic forwarding to spawned executor prompts); confirmed **not rendered at all** for one first-party capability's originally-intended `execute:wave:pre` use case | Always — never uniform in any version this session could inspect | B8's mechanism choice must be point-specific, not copied from B7's PRD framing |
| BEADS-RECALL.md is read by the planner "the same way" as RESEARCH.md | The planner's `<files_to_read>` block is a closed, hardcoded list; RESEARCH.md is on it by name, BEADS-RECALL.md is not and cannot be without a gsd-core patch | Always | B7's literal acceptance criterion (file exists) is unaffected; the phase's stated goal needs an explicit contribution pointer to actually be met |
| `bd` issues carry structured file-path metadata for scope matching | No such field exists; Phase 1's own issue-creation call sets title only | Always (bd v1.2.1) | D-01's "file-path overlap" needs two explicit techniques (`<beads-id>` reverse-lookup + `--desc-contains`), not one generic comparison |

**Deprecated/outdated:** none newly found this session beyond what Phase 1 already corrected
(`command-exists` → `command-exit-zero`, not relevant to this phase's gateless scope).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `into: "orchestrator"` at `execute:wave:pre` is legal (unvalidated by the loader) but has no first-party rendering precedent to confirm behavior beyond "reaches the orchestrator's own render-hooks call output" | Critical correction: `execute:wave:pre` has no equivalent contribution-rendering slot | If wrong in either direction (works better or worse than described), the risk is contained by this research's own primary recommendation to avoid depending on it for B8 — low severity |
| A2 | A `contributions[]` fragment materializes once per `gsd_run` process invocation ("load time"), making live per-wave data embedding unsafe | Pattern 1 / Critical correction sections | If gsd-core's actual caching is per-command-family rather than per-process, the staleness risk is smaller than described — but the recommended design (pointer, not payload) is safe either way, so this assumption does not gate any recommendation's correctness, only its stated rationale |
| A3 | The optional `plan:pre` contribution-pointer fragment for B7 is worth adding despite not being required by B7's literal test | Summary / Optional contribution code example | If the planner judges the extra manifest surface not worth it for a non-required criterion, dropping it costs nothing — B7 still passes on file-existence alone |

## Open Questions

1. **(RESOLVED)** Should `beads-recall`'s file-scope match also consult phase-level `files_modified` from
   ROADMAP.md, or must it be computed fresh from CONTEXT.md/REQUIREMENTS.md for the *current*
   phase (since the phase being planned has no PLAN.md yet at `plan:pre` time)?
   - What we know: `beads-recall` runs at `plan:pre`, before any PLAN.md for phase 2 exists —
     there is no `<files>` list to compare against for *this* phase yet, only for *other*
     phases' already-synced issues.
   - **RESOLVED (02-CONTEXT.md, "Post-research corrections", D-01 revised):** no PLAN.md exists
     yet at `plan:pre` time, so `beads-recall`'s file-path tier greps the phase's ROADMAP.md
     section text + CONTEXT.md for file paths/module names mentioned there instead — weaker
     signal than a real `files_modified` list, but available pre-plan. Epic/label match (D-01's
     second tier) and the Unscoped fallback (D-02) are unchanged. Implemented in
     02-01-PLAN.md Task 2.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `bd` binary | All of B7/B8/B11 | ✓ | 1.2.1 [VERIFIED: `bd --version`, this session] | B6's existing fail-open path |
| `.beads/*.db` in this repo | Any live `bd` query against real project data | ✗ — [VERIFIED: `bd list --json -n 1` in the project root returns "Error: no beads database found", this session] | — | `bd_available()`'s existing check (`bd list --json -n 1` returncode==0) already returns `False` here, so every new BEADS-RECALL.md/BEADS.md generation call in this repo today hits the fail-open path (B6) until an operator runs `bd init` — expected, not a Phase 2 defect |
| Python 3 | Sync/recall/status scripts | ✓ | 3.14.7 [VERIFIED: `python3 --version`, this session] | None — N5 |
| gsd-core (source checkout, research-only) | Verifying workflow-file mechanics for this research | ✓ (scratch shallow clone of `open-gsd/gsd-core` @ same 1.10.0 tag as the installed runtime) | 1.10.0 [VERIFIED: local VERSION file == npm registry latest] | Research-only tooling, not a build dependency |

**Missing dependencies with no fallback:** none blocking Phase 2 implementation.

**Missing dependencies with fallback:** `.beads/*.db` absence in *this* project — B6's fail-open
path already covers it; a real end-to-end proof of B7/B8/B11 needs `bd init` run first (same
precondition Phase 1's own `TestEndToEndTracer` needed).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib) — unchanged from Phase 1, per N5 |
| Config file | none |
| Quick run command | `python3 -m unittest discover -s .gsd/capabilities/beads/tests -p 'test_*.py' -q` |
| Full suite command | same as quick run |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| B7 | An open issue whose `<beads-id>`-linked task's `<files>` overlaps this phase's scope appears in BEADS-RECALL.md; an issue matching neither file nor epic/label appears under "Unscoped" | unit (mock `bd` JSON responses; fixture PLAN.md files across two phase dirs) | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestBeadsRecall -v` | ❌ Wave 0 |
| B7 | Zero open issues still produces a BEADS-RECALL.md with an explicit "none found" body (D-04) | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestBeadsRecall.test_no_matches -v` | ❌ Wave 0 |
| B8 | The composed `prompt=` string an `Agent()` call would receive contains the wave's issue ids after `beads-status`'s execute:wave:pre branch runs | integration/e2e (since the "prompt" is produced by following SKILL.md prose, this is best proven by a manual/checkpoint trace of one real wave dispatch, not a pure unit test of Python code) | manual trace: run a real 2-plan wave with `beads.enabled=true` and a real `.beads` db, grep the actual `Agent()` prompt text for the synced issue ids | ❌ Wave 0 — flag as `checkpoint:human-verify`, not purely automatable given B8's own acceptance criterion demands prompt inspection, not behavior inference |
| B11 | BEADS.md frontmatter (`phase`, `epic`, `open`, `closed`, `blocking_open=0`, `diverged=0`, `generated_from`, `generated_at`) matches a live `bd` query at generation time; a hand edit is overwritten at the next regeneration | unit + one e2e (mirrors Phase 1's `TestEndToEndTracer` pattern: real `bd init` scratch db, real regeneration, diff against a hand-edited copy) | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestBeadsMdRegeneration -v` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** quick run command above
- **Per wave merge:** full suite (identical command — small surface, matches Phase 1's precedent)
- **Phase gate:** full suite green before `/gsd-verify-work`; B8's checkpoint trace must also be
  performed at least once before phase completion, since it cannot be fully proven by unit tests
  alone (the acceptance criterion is about a composed LLM-agent prompt, not pure code output)

### Wave 0 Gaps

- [ ] `.gsd/capabilities/beads/tests/test_sync.py` — extend with `TestBeadsRecall`,
  `TestBeadsMdRegeneration` classes, reusing Phase 1's `_make_bd_side_effect` mock pattern
- [ ] `.gsd/capabilities/beads/tests/fixtures/` — a second phase-directory fixture tree (to prove
  the cross-phase `<beads-id>` reverse-lookup technique) and a multi-issue `bd list --json` fixture
  covering both `parent-child` and `blocks` dependency types (D-08's blocked-by column)
- [ ] No framework install needed — `unittest` ships with Python 3 stdlib

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface |
| V3 Session Management | No | N/A |
| V4 Access Control | No | Operates within the user's own repo/bd database, same as Phase 1 |
| V5 Input Validation | Yes | Same N4 mandate as Phase 1: every `bd` invocation built from typed Python values via `subprocess.run([...], shell=False)`, never a formatted shell string — applies identically to the new `bd list --desc-contains`/`--status`/`--exclude-type` calls this phase adds |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command injection via an issue's `description`/`notes` text (now read back and echoed into BEADS-RECALL.md/BEADS.md) | Tampering | Same N4 rule as Phase 1: issue text is data displayed in a generated markdown table, never interpolated into a shell command or `bd` argv; escape `\|`/newlines when rendering into a markdown table cell, matching the pattern gsd-core's own `ship.md` uses for commit-subject table cells [VERIFIED: `gsd-core/workflows/ship.md:301`, "escape `\|` as `\|` and strip `\r`/`\n` from ... the rendered ... value"] |
| Path traversal via a cross-phase `<beads-id>` reverse-lookup that walks every `.planning/phases/*/` directory | Tampering | Confine every scanned path to the resolved `.planning/phases/` root, reusing `confined()`/`find_project_root()` from Phase 1's `sync.py`, never trusting a `phase`/`plan` frontmatter string as a raw path component |

## Sources

### Primary (HIGH confidence — read directly from a shallow clone of `open-gsd/gsd-core` @
v1.10.0, this session, same version as the installed runtime overlay)
- `src/loop-resolver.cts` — full read of `resolveLoopHooks`/`renderLoopHooks`, fragment
  materialization vs. rendering distinction
- `src/capability-loader.cts` — targeted read, `materializeHookFragments` call site and its
  ordering relative to the project-consent gate
- `docs/reference/capability-manifest.md` — targeted read, `steps`/`contributions` field tables,
  fragment materialization semantics, 12-point vocabulary table
- `docs/reference/loop-hook-dispatch.md` (local runtime copy, `~/.claude/gsd-core/references/`)
  — full read, point-agnostic envelope/dispatch-rules contract
- `workflows/plan-phase.md` (local runtime copy) — targeted read, `<files_to_read>` fixed-list
  definition (line 95), planner subagent prompt template (lines 670-739) including the confirmed
  contribution-injection slot at line 731
- `workflows/execute-phase.md` (local runtime copy) — targeted read, step 2.75 execute:wave:pre
  dispatch (lines 641-649), full executor `Agent()` prompt template (lines 703-777)
- `capabilities/claude-orchestration/capability.json` and
  `capabilities/claude-orchestration/fragments/execute-wave-pre.md` — full read, the one
  first-party precedent for `contributions[]` at `execute:wave:pre`
- `capabilities/external-job/capability.json` — targeted read, `description` field's own
  admission that `execute:wave:pre` "is declared in the loop host contract but not rendered"
- `bd list --help`, `bd show --help`, `bd create --help`, `bd epic --help`, `bd label --help` —
  captured directly from the locally installed `bd` v1.2.1 binary, this session
- Live `bd init` scratch database (created and destroyed in the session scratchpad this run) —
  `bd show <id> --json` and `bd list --parent <epic> --json` response shapes captured directly
- This project's own `.gsd/capabilities/beads/scripts/sync.py`,
  `.gsd/capabilities/beads/skills/*/SKILL.md`, `.planning/phases/01-substrate/01-RESEARCH.md`,
  `.planning/phases/01-substrate/01-VERIFICATION.md`, `.planning/PROJECT.md`,
  `docs/prd-beads-capability.md` — full reads, this session

### Secondary (MEDIUM confidence)
- `npm view @opengsd/gsd-core version` — used only to cross-check the local runtime's VERSION
  file matches the latest published release, not as a factual source for any claim above

### Tertiary (LOW confidence)
- None used for load-bearing claims in this document.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `bd`/Python versions unchanged and re-verified live; no new dependency.
- Architecture (contributions/steps mechanics): HIGH — every claim traces to a specific quoted
  source line from the same gsd-core version as the installed runtime, cross-checked against two
  independent real first-party capabilities (`claude-orchestration`, `external-job`) rather than
  a single example.
- Pitfalls: HIGH — every pitfall traces to a specific, quoted or directly-observed source.
- Open question (A1's file-scope source for the phase being planned): MEDIUM — a genuine
  unresolved design point, not a verified fact, flagged explicitly rather than guessed.

**Research date:** 2026-08-15
**Valid until:** 30 days (gsd-core is actively developed; re-verify contribution-rendering
mechanics against the then-current `open-gsd/gsd-core` release before Phase 3 planning if more
than a few weeks have elapsed — this phase's central finding is version-specific behavior, not a
stable architectural invariant)
