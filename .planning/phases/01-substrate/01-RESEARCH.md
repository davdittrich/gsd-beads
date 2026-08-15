# Phase 1: Substrate - Research

**Researched:** 2026-08-15
**Domain:** gsd-core capability registry overlay (ADR-1244) + beads (`bd`) CLI issue tracker
**Confidence:** HIGH (all load-bearing claims verified against a live `open-gsd/gsd-core` v1.10.0 checkout and a live `bd` v1.2.1 binary — see Sources)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `beads.sync_mode` (`authoritative`) now covers task *status AND content*, not status
  only. A bd issue's title/description originates from `PLAN.md` at first sync, but the bd issue
  is authoritative from that point forward — `PLAN.md`'s task text is never re-synced from later
  bd edits. Reversibility: one-way.
- **D-02:** Issue title is prefixed with the task's id/number from `PLAN.md` (not verbatim task
  title) — supports sort/search across phases in `bd list`.
- **D-03:** `beads-id:` lives as a one-line metadata field directly under the task heading in
  `PLAN.md` (e.g. `beads-id: bd-123` right after `### Task 3: ...`) — visible, greppable, minimal
  format change to existing `PLAN.md` structure.
  **⚠ CORRECTED BY THIS RESEARCH — see "Critical correction: PLAN.md has no `### Task` heading"
  below. There is no markdown heading to place a line "right after." The underlying intent
  (visible, greppable, minimal format change) is preserved; only the literal placement mechanism
  must change to an XML child element inside `<task>`.**
- **D-04:** Only explicit "depends on" edges in `PLAN.md` become `bd dep add` calls. Wave
  grouping (parallel-batch scheduling) is NOT treated as an implicit dependency — a task in wave
  N+1 with no explicit edge to wave N is not blocked on it in `bd ready`.
  **⚠ CORRECTED BY THIS RESEARCH — see "Critical correction: `depends_on` is plan-level, not
  task-level" below. There is no per-task `depends_on` field in the real schema.**
- **D-05:** Phase epic title in bd is the phase header verbatim from `ROADMAP.md`, e.g.
  `"Phase 1: Substrate"` — zero translation/mapping logic between roadmap and bd.
- **D-06:** When a phase is replanned and a previously-synced issue no longer matches any current
  task, the orphaned issue is closed with a note explaining it no longer maps to a plan task.
  Reversibility: costly.
- **D-07:** If a task's `beads-id:` points at an issue that no longer exists in bd (deleted
  externally), treat it as B10 divergence: block ship, report both sides. Never silently
  recreate a fresh id and never hard-error the sync step itself.
- **D-08:** The one required visible notice (B6) is a stdout line at the point `bd` is found
  absent/failing/locked, AND a corresponding entry is appended under `.planning/STATE.md`'s
  "Blockers/Concerns" section.

### Claude's Discretion

- Exact stdout notice wording/format.
- Exact `bd dep add` invocation shape (batched vs. per-edge) as long as B5 idempotency holds.
- Whether the epic is created eagerly at first sync or lazily on first issue — pick whichever is
  simpler given how `plan:post` hooks fire in gsd-core (technical, not user-facing).

### Deferred Ideas (OUT OF SCOPE)

- PRD §12: does `execute:wave:post` fire per task or per wave? **RESOLVED by this research —
  per wave. See below.**
- PRD §12: packaging (Python entry point vs. JS shell-out). **RESOLVED by this research — neither;
  see below.**
- PRD §12: where a `beads.ship_gate=false` override gets recorded — relevant to Phase 3, not
  Phase 1.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| B1 | One beads issue per `PLAN.md` task, parented to a phase epic | Real `<task>` XML schema (docs/reference/plan-md.md), real epic-creation flow via `bd create --type epic` + `bd create --parent <epic-id>`, verified locally against `bd` v1.2.1 `--help` output |
| B2 | Plan task ordering → `bd dep add` | **Corrected**: no per-task `depends_on` field exists; dependency must be derived from (a) implicit sequential task order within one plan (verified: executor blocks on task N+1 until task N's acceptance criteria pass) and (b) plan-level `depends_on` frontmatter for cross-plan ordering |
| B3 | Task completion closes its issue automatically | **Resolved**: hook fires at `execute:wave:post`, once per wave, after ALL plans in that wave have merged — so the `beads-status`/`beads-sync` skill must close potentially many issues in one dispatch, not one at a time |
| B4 | Identity bound by explicit `beads-id:`, never title | Real `<task>` element has no `id` attribute; `beads-id` must be a new optional child element (precedent: `<precondition>`/`<reversibility>` are already-shipped optional child elements the structural validator accepts without rejection) |
| B5 | Sync is idempotent | `bd create --id` explicit-id flag + read-before-write via `beads-id` element are the mechanism; `bd list --json` diff proof pattern verified against real CLI flags |
| B6 | `bd` absent/failing/locked degrades to no-op with one visible notice | `steps[].onError: "skip"` is the sole gsd-core mechanism (verified: required field, only `"skip"`\|`"halt"` allowed); combine with D-08's stdout line + STATE.md entry, both authored by the skill itself, not by gsd-core |

</phase_requirements>

## Summary

This phase installs `beads` as a **project-scoped, `role: "feature"` capability overlay** at
`.gsd/capabilities/beads/`, per ADR-1244 (implemented in `src/capability-loader.cts`,
schema-documented in `docs/reference/capability-manifest.md`). Phase 1's B1–B6 requires exactly
three `steps[]` entries — `plan:post` (create issues), `execute:wave:pre` (optional status
refresh), `execute:wave:post` (close completed tasks) — dispatched to three Claude-Code Skills
(`beads-sync`, `beads-status`) whose `SKILL.md` bodies are markdown instructions read and acted
on by the agent, not code gsd-core's runtime invokes directly. No `contributions[]` or `gates[]`
are needed until Phase 2/3.

Three claims in the upstream PRD/CONTEXT.md/PROJECT.md are **factually wrong** against the real
gsd-core v1.10.0 source and are corrected below with citations: (1) `PLAN.md` tasks are XML
`<task>` elements, not markdown `### Task N:` headings; (2) `depends_on` is a **plan-level**
frontmatter field only — there is no per-task dependency field; (3) the shipped gate predicate
kind is `command-exit-zero`, not `command-exists`. A fourth finding resolves an open question
definitively: `execute:wave:post` fires **once per wave**, after every plan in that wave has
merged — never per task.

**Primary recommendation:** Ship three Python-stdlib-only scripts under
`.gsd/capabilities/beads/scripts/` (invoked by the skills' bash instructions, never by gsd-core
directly), a `capability.json` matching the verified schema exactly (including the
now-known-required `runtimeCompat` field the PRD's draft manifest omitted), and store `beads-id`
as a new optional `<beads-id>` child element placed between `<name>` and `<files>` inside each
`<task>` — the same slot convention gsd-core itself uses for `<precondition>`/`<reversibility>`.

## Critical correction: PLAN.md has no `### Task` heading

`docs/reference/plan-md.md` (canonical schema reference, shipped in gsd-core 1.10.0) states the
task block is an XML-style element inside `<tasks>`:

> `<task type="auto"> <name>Task 1: Create PostCard component</name> ... </task>`
> [VERIFIED: gsd-core/docs/reference/plan-md.md:259-275]

The literal template a real planner fills in (`gsd-core/templates/phase-prompt.md`) confirms the
same shape with no `id`/`number` attribute on `<task>` — only `type` and optional `gate`:

```
63	<task type="auto">
64	  <name>Task 1: [Action-oriented name]</name>
65	  <files>path/to/file.ext, another/file.ext</files>
66	  <read_first>path/to/reference.ext, path/to/source-of-truth.ext</read_first>
67	  <action>[Specific implementation ...]</action>
68	  <verify>[Command or check to prove it worked]</verify>
69	  <acceptance_criteria>
70	    - [Grep-verifiable condition...]
71	  </acceptance_criteria>
72	  <done>[Measurable acceptance criteria]</done>
73	</task>
```
[VERIFIED: gsd-core/templates/phase-prompt.md:63-73]

A repo-wide search for `### Task` across the entire 1.10.0 source tree returns **zero matches**;
`<task type=` returns matches in every canonical reference file (`phase-prompt.md`,
`planner-reversibility.md`, `planner-preconditions.md`, `planner-interface-context.md`,
`checkpoints.md`, `docs/reference/plan-md.md`). [VERIFIED: repo-wide grep, this session]

**Consequence for D-03:** `beads-id:` cannot be "a line right after `### Task 3: ...`" because
that heading style does not exist anywhere in the real format. It must be a new child element
inside `<task>`. Precedent exists for exactly this pattern — `<precondition>` and `<reversibility>`
are both optional child elements gsd-core added later, and the docs state explicitly:

> "Plans that include `<precondition>` pass `verify plan-structure` unchanged — the structural
> validator checks for the presence of required tags and does not reject unknown optional tags."
[VERIFIED: gsd-core/docs/reference/plan-md.md:199]

> "Plans that include it pass `verify plan-structure` unchanged; the structural validator checks
> for the presence of required tags and does not reject unknown optional tags."
[VERIFIED: gsd-core/docs/reference/plan-md.md:233 (same rule stated for `<reversibility>`)]

**Recommended placement:** `<beads-id>bd-123</beads-id>` as a new optional child element, in the
same slot documented for `<precondition>`/`<reversibility>` — "Optional `<precondition>` ... and
`<reversibility>` ... elements may sit between `<name>` and `<files>`" [VERIFIED:
gsd-core/docs/reference/plan-md.md:180]. This satisfies both the structural-validator
non-rejection guarantee and D-03's underlying intent (visible, greppable, minimal format change).

## Critical correction: `depends_on` is plan-level, not task-level

The PLAN.md frontmatter reference table is unambiguous:

> `wave` | Yes | integer | Execution wave. Plans in wave 1 run in parallel (no dependencies).
> Plans in wave 2+ wait for all plans in the previous wave to complete. Pre-computed at plan time
> by `gsd-planner`.
> `depends_on` | Yes | array of plan IDs | Plans this plan must wait for. Empty array = wave 1.
> Example: `["03-01"]` means this plan runs after Plan 01 in Phase 3.
[VERIFIED: gsd-core/docs/reference/plan-md.md:69-70]

There is no equivalent field documented (or found by grep) on the `<task>` element itself. Task
ordering *within* one plan is enforced procedurally by the executor, not declared in the plan:

> "3. Per task: ... **HARD GATE — acceptance_criteria verification:** After completing each task
> ... you are BLOCKED from starting the next task until this gate clears"
[VERIFIED: gsd-core/gsd-core/workflows/execute-plan.md:219-230, quoting the literal text "you are
BLOCKED from starting the next task until this gate clears"]

**Consequence for D-04/B2:** `bd dep add` calls must be synthesized from two distinct sources,
neither of which is a literal "depends on" field the planner writes per task:
1. **Intra-plan order** — task *k* (for k > 1) is blocked-by task *k-1* within the same plan,
   derived from array position in `<tasks>`, because the executor already enforces this order
   procedurally. This is what D-04's "explicit depends-on edges" most plausibly meant in practice.
2. **Inter-plan order** — the plan-level `depends_on: ["03-01"]` frontmatter field, which the
   beads-sync skill maps to: every task in the dependent plan (03-02) is blocked-by the *last*
   task of every plan in `depends_on` (03-01) — or, more simply and defensibly, the dependent
   plan's *epic-scoped first task* is blocked-by the prerequisite plan's *last task*, letting `bd
   ready`'s blocker-aware semantics naturally gate the whole downstream chain.

This is a genuine design decision the planner must make explicitly (not a fact to verify further)
— flagged here as the single largest scope decision left for `/gsd-plan-phase` to resolve, because
CONTEXT.md's D-04 was written against an assumed schema that does not exist.

## Resolved: `execute:wave:post` fires once per wave, not per task

`gsd-core/workflows/execute-phase.md` step "5.75. Execute:wave:post capability dispatch" is
positioned explicitly **after** worktree merge, post-merge tests, and tracking updates for the
**entire wave**:

> "After worktree merge, post-merge tests, and tracking updates, dispatch capability hooks
> registered at `execute:wave:post`."
[VERIFIED: gsd-core/gsd-core/workflows/execute-phase.md:1007]

```
WAVE_POST_HOOKS_JSON=$(gsd_run loop render-hooks execute:wave:post --raw)
```
[VERIFIED: gsd-core/gsd-core/workflows/execute-phase.md:1010]

Immediately preceding this step, the tracking-update commit is built from a *list* of plans that
completed in the wave: "Where `WAVE_PLAN_IDS` is the space-separated list of plan IDs that
completed in this wave." [VERIFIED: gsd-core/gsd-core/workflows/execute-phase.md:1005, quoting
"space-separated list of plan IDs that completed in this wave"]. This is a per-**wave**
invocation carrying data about potentially several **plans**, each of which can carry several
**tasks**.

The canonical manifest schema doc lists the point's position identically:

> `execute:wave:post` | Execute | After each execution wave
[VERIFIED: gsd-core/docs/reference/capability-manifest.md:134]

**This resolves PRD §12 open question 2 definitively: per wave.** `execute:wave:pre`/`post` are
the *only* two execute-phase extension points a capability can hook — there is no
`execute:plan:post` or `execute:task:post` point in the closed 12-point vocabulary
[VERIFIED: gsd-core/docs/reference/capability-manifest.md:126-139, full table of 12 points].

**Consequence for B3:** the `beads-status` (or `beads-sync`) skill dispatched at
`execute:wave:post` must, in one invocation, discover **every task that completed across every
plan in the just-finished wave** and close all of the corresponding beads issues — a batch
operation, not "close issue N." The skill has to re-read each `PLAN.md` in the wave, find every
task whose `<beads-id>` is set and whose task is now checked off complete (per the plan's
SUMMARY.md or the plan's own completion marker), and issue one `bd close` per completed task
(or a single multi-id `bd close id1 id2 id3`, since `bd close [id...]` accepts multiple positional
IDs — [VERIFIED: `bd close --help` output, this session, "Usage: bd close [id...] [flags]"]).

## Resolved: packaging is neither "Python entry point" nor "JS shell-out"

The PRD's framing of the packaging question — "may an overlay ship a Python entry point, or must
a JS hook shell out to it?" — presupposes gsd-core's runtime directly invokes capability code.
It does not, for `steps[].ref: {skill: ...}`. The develop-a-capability guide states:

> "A skill your Capability declares is not an inert asset. Its `SKILL.md` body is copied
> **verbatim** into the user's runtime skills directory at install, where it becomes an
> agent-invocable instruction file."
[VERIFIED: gsd-core/docs/how-to/develop-a-capability.md:124]

And the universal (point-agnostic) dispatch contract confirms the invocation mechanism is the
Skill tool, not a subprocess call from gsd-core's own JS:

> "`ref.skill` present → dispatch via the Skill tool with skill id `gsd-<ref.skill>`."
[VERIFIED: gsd-core/gsd-core/references/loop-hook-dispatch.md:36]

**Consequence:** gsd-core's loop never executes capability code itself for `ref.skill` steps —
the orchestrator (an LLM agent, e.g. Claude Code) reads the skill's markdown instructions and
then runs whatever tool calls (Bash, Read, etc.) the SKILL.md tells it to. This means:
- No JS wrapper is required at all — gsd-core's own JS never shells out to anything the beads
  capability ships.
- No "Python entry point" registration mechanism is needed either — there is no manifest field
  for "the thing gsd-core execs on your behalf" for a `skill` step (that concept only exists for
  `role: "runtime"` capabilities' `hooksSurface`/hook scripts, and for `role: reviewer` lanes'
  `invoke.binary` — neither applies to a `role: "feature"` capability like `beads`).
- N5's "bd binary + Python 3 stdlib only, no other runtime deps" constraint is satisfied trivially:
  the `SKILL.md` for `beads-sync` instructs the agent to run `bd` directly via Bash for simple
  operations, and to invoke a bundled stdlib-only Python script
  (`.gsd/capabilities/beads/scripts/sync.py`) via `python3 <path>` for anything too structured for
  inline bash (parsing `<task>` blocks, idempotent diffing, `beads-id` insertion). No Node/npm
  dependency of any kind is shipped.
- `commands[]` (the JS command-family mechanism gated by `commandRoots`/ledger `committed` state
  in `capability-loader.cts:837-844`) is **not needed** for Phase 1 and should be omitted from
  the manifest entirely — it exists for capabilities that add new `gsd <family> <verb>` CLI
  surfaces, which B1–B6 does not require.

**Skill directory layout, verified precedent:** first-party skills declared by a capability's
bare stem (e.g. mempalace declares `"skills": ["mempalace-recall", "mempalace-capture"]`
[VERIFIED: gsd-core/capabilities/mempalace/capability.json:18-21]) are staged on disk with a
`gsd-` prefix (`skills/gsd-mempalace-recall/`, `skills/gsd-mempalace-capture/` — [VERIFIED:
repo-wide `find skills -maxdepth 1`, this session]), matching the dispatch id `gsd-<ref.skill>`.
The develop-a-capability guide instructs third-party authors to co-locate: "Co-locate prompt
fragments, owned skills, owned agents, and other owned artefacts under the Capability folder when
the schema allows it." [VERIFIED: gsd-core/docs/how-to/develop-a-capability.md:38]. The beads
manifest should therefore declare bare stems (`"skills": ["beads-sync", "beads-status"]`) and ship
`SKILL.md` bodies under `capabilities/beads/skills/beads-sync/SKILL.md` etc.; the install step
stages them into the runtime's skills directory, and dispatch always resolves the `gsd-`-prefixed
id regardless of first-party/third-party origin.

## Corrected: gate predicate kinds

PROJECT.md and the PRD both name the two shipped predicate kinds as `command-exists` and
`artifact-frontmatter-equals`. The real, frozen dispatch table is:

```
208	const KIND_TABLE: Record<string, (p: Record<string, unknown>, ctx: PredicateContext, deps: PredicateDeps) => PredicateResult> = {
209	  'command-exit-zero': evaluateCommandExitZero,
210	  'artifact-frontmatter-equals': evaluateArtifactFrontmatterEquals,
211	};
```
[VERIFIED: gsd-core/src/gate-predicate-evaluator.cts:208-211]

The kind is `command-exit-zero`, not `command-exists` — it runs a **declared shell command** in a
bounded `sh -c` subprocess and blocks if the exit code is non-zero (default 30s timeout)
[VERIFIED: gsd-core/src/gate-predicate-evaluator.cts:31-32,101-151]. This is not merely "does a
binary exist on PATH" — it can run an arbitrary bounded command, including `bd` itself. The design
choice already locked in PROJECT.md — gates read only `BEADS.md` frontmatter via
`artifact-frontmatter-equals`, never call `bd` directly from a gate — remains the right call for
fail-open composability (a blocking gate that shells out live to `bd` couples ship-blocking to
`bd`'s live availability, defeating B6's fail-open guarantee), but the *reason* it's safe is not
"the mechanism forbids it," because it doesn't; it's a deliberate, still-correct design choice.
**Not relevant to Phase 1** (B1–B6 use no gates), but material for Phase 3 (B9/B10) planning.

Additionally, `check.query` (the other check form, e.g. `{"query": "ui.safety-gate"}`) dispatches
to a **closed, first-party-only** subcommand set in `check-command-router.cts`:

> "Unknown check subcommand. Available: api-coverage-verify-pre, auto-mode,
> decision-coverage-plan, decision-coverage-verify, gap-analysis-plan-post, predicate,
> prohibition-enforcement, tdd-review-checkpoint, ui-plan-gate, ui-safety-gate,
> verify-schema-drift, verify-codebase-drift"
[VERIFIED: gsd-core/src/check-command-router.cts:1576]

A third-party capability cannot add a new `query` name — that requires patching gsd-core, which
N2 forbids. **Only `check: {"predicate": {...}}` is available to `beads`.** This is consistent
with — and confirms — PROJECT.md's existing design intent.

## Correction: consent-gate scope in PROJECT.md is inverted

PROJECT.md's Constraints section states: "**Global-scope installs**: Pass a consent gate (CB-3)
before use; ship project-scoped first." The real gate applies to the opposite scope. In
`capability-loader.cts`:

> "5. #1459 — USER-OWNED CONSENT GATE (TRUST-1 + TRUST-3). For a PROJECT-scope overlay the
> authoritative consent signal is NOT the in-repo ledger ... GLOBAL scope is under the user's own
> home and is trusted as before (no consent record required)."
[VERIFIED: gsd-core/src/capability-loader.cts:685-693, quoting "GLOBAL scope is under the user's
own home and is trusted as before (no consent record required)"]

```
726	      if (root.scope === 'project') {
727	        let consented = false;
...
746	          warnings.push({ id, scope: root.scope, kind: 'unconsented', reason: 'discovered — no user consent record (inactive)' });
747	          continue;
```
[VERIFIED: gsd-core/src/capability-loader.cts:726-747]

**Consequence:** because Phase 1 ships **project-scoped** (per PROJECT.md's own stated rollout),
the beads capability's `steps[]` (and any future `contributions[]`/`gates[]`) will not activate
at all — including for a manual smoke test — until the user runs
`gsd capability install ./capabilities/beads --scope project` (or the equivalent path/URL form)
and passes through the consent flow, because `beads` declares `skills[]`, which is classified as
an instruction surface requiring disclosure:

> "A skill your Capability contributes [is] named, by stem, in their own section of the
> pre-install consent summary." [VERIFIED: gsd-core/docs/how-to/develop-a-capability.md:131]

By contrast, a fully declarative capability with empty `skills[]`/`agents[]`/`hooks[]` installs
with **no** consent prompt at all — confirmed by the tutorial's own worked example: "Because
`hello-note` declares no executable surfaces (no hook scripts, no MCP servers, no command
modules) it installs without a consent prompt." [VERIFIED:
gsd-core/docs/tutorials/build-your-first-capability.md, "GSD copies the bundle into
`.gsd/capabilities/hello-note/`... Because `hello-note` declares no executable surfaces... it
installs without a consent prompt."]. `beads` is not in this category — it must declare `skills`,
so an install+consent step is a hard operational precondition for any Phase 1 verification, and
should appear explicitly as a task/checkpoint in the plan (likely `checkpoint:human-verify` or
`checkpoint:human-action`, since `gsd capability install ... --yes` in autonomous mode would skip
disclosure review — the planner should decide which).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Issue creation (B1) | gsd-core loop (`plan:post` step dispatch) | `beads-sync` skill + Python helper | The loop only dispatches; all bd-facing logic (parsing `<task>` blocks, calling `bd create`) lives in the skill/script, not gsd-core |
| Dependency mapping (B2) | `beads-sync` skill + Python helper | `bd` (dependency graph storage) | gsd-core has zero dependency-graph concept for tasks below the plan level; all derivation is capability-owned |
| Task-close-on-completion (B3) | gsd-core loop (`execute:wave:post` step dispatch) | `beads-status`/`beads-sync` skill | Trigger timing (once per wave) is gsd-core's; the batch-close logic is capability-owned |
| Identity binding (B4) | `PLAN.md` (`<beads-id>` element, on-disk source of truth) | `beads-sync` skill (writer) | The element lives in the artifact gsd-core already treats as ground truth; the skill is the sole writer |
| Idempotency (B5) | `beads-sync` skill + Python helper | `bd` (query for existing issue by id) | No gsd-core involvement — pure capability-internal contract |
| Fail-open degrade (B6) | gsd-core loop (`onError: "skip"` on every step) | `beads-sync`/`beads-status` skill (the stdout notice + STATE.md append) | The mechanism (skip) is gsd-core's; the *content* of the one visible notice is authored by the skill itself, since gsd-core's `onError: skip` is silent by default at the loop level |

## Standard Stack

### Core

| Component | Version | Purpose | Why Standard |
|---|---|---|---|
| `bd` (beads CLI) | 1.2.1 locally installed [VERIFIED: `bd --version` output, this session] | Issue creation, dependency graph, close, query | Named substrate per PRD/PROJECT.md; already on PATH in this environment |
| Python 3 stdlib | 3.14.7 locally installed [VERIFIED: `python3 --version` output, this session] | All non-trivial logic invoked by the skills (parsing, diffing, `beads-id` insertion) | N5 forbids any other dependency; stdlib (`re`, `json`, `subprocess`, `argparse`) is fully sufficient for this scope |
| gsd-core capability manifest (`capability.json`) | schema current as of gsd-core 1.10.0 | Declares the overlay's steps/config/skills | The only supported extension mechanism (ADR-1244); no alternative exists that avoids forking |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python stdlib parsing of `<task>` XML-lite blocks | `lxml`/`xml.etree` full XML parser | `<task>` blocks are not well-formed XML across a whole PLAN.md (the file is markdown with embedded pseudo-XML blocks); a full XML parser would need to isolate blocks first anyway. Regex/line-scan against the documented, stable tag set is simpler and needs zero non-stdlib dependency (N5). |
| `bd create`/`bd dep add` shelled out per-call from Python `subprocess` | A `bd` batch/graph JSON input (`bd create --graph <file>`) | `--graph` exists and reduces process-spawn count, but couples the sync script to a JSON schema not yet verified in this session; per-call `subprocess.run([...], shell=False)` with argv lists is simpler, is what N4 already mandates (typed values, never a shell string), and defers batching as a possible future optimization, not a Phase 1 requirement. |
| A single monolithic `sync.py` doing create+dep+close | Three separate scripts by lifecycle point | A single script with subcommands (`sync.py create-issues`, `sync.py close-wave`) is simpler to keep idempotent-safe (one shared "read PLAN.md, resolve beads-id" core) than three independent scripts risking drift; recommend one script, multiple subcommands. |

**Installation:** No package installation — `bd` binary + Python 3 stdlib only, per N5. Verify
`bd` is on PATH in the skill's bash instructions before any other action (`command -v bd`), which
is also the fail-open detection point for B6.

## Package Legitimacy Audit

**Not applicable.** This phase installs zero external packages (no `npm install`, no `pip
install`) — N5 restricts the capability to the `bd` binary (already installed, user-managed) and
Python 3 standard library only. No `package-legitimacy check` run was needed.

## Architecture Patterns

### System Architecture Diagram

```
PLAN.md written by gsd-planner
        │
        │ (plan:post loop point fires after planning completes)
        ▼
gsd-core orchestrator: gsd_run loop render-hooks plan:post --raw
        │
        │ activeHooks[] contains { kind: "step", ref: { skill: "beads-sync" }, capId: "beads" }
        ▼
Skill(skill="gsd-beads-sync", args="<phase> ...")   ← dispatch id is ALWAYS gsd-<ref.skill>
        │
        │ SKILL.md instructs the agent:
        ▼
  1. command -v bd || { echo "bd not found — skipping beads sync"; exit 0 }   (B6)
  2. python3 .gsd/capabilities/beads/scripts/sync.py create-issues <PLAN.md path>
        │
        │ sync.py (stdlib only):
        │   - parse <tasks> block, extract each <task>...<beads-id>?...</task>
        │   - if <beads-id> present → `bd show <id>` to confirm existence (B4/D-07)
        │   - if absent → `bd create <title> --parent <epic-id> --type task`  (B1)
        │   - derive bd dep add edges from intra-plan order + plan-level depends_on (B2)
        │   - re-write PLAN.md inserting/confirming <beads-id> element         (B4)
        ▼
`bd` database (.beads/*.db)
        │
        │ (later: execute:wave:post fires ONCE after all plans in a wave merge)
        ▼
Skill(skill="gsd-beads-status") or beads-sync close-wave subcommand
        │
        │ 1. for each PLAN.md in WAVE_PLAN_IDS: find completed tasks (SUMMARY.md exists)
        │ 2. bd close <id1> <id2> ... --reason "..."                          (B3)
        ▼
`bd` database updated — issues closed
```

### Recommended Project Structure

```
.gsd/capabilities/beads/
├── capability.json              # role: feature, verified schema (see Code Examples)
├── skills/
│   └── beads-sync/
│       └── SKILL.md             # markdown instructions the agent executes via Bash
├── scripts/
│   └── sync.py                  # stdlib-only: create-issues / close-wave subcommands
└── fragments/                   # empty for Phase 1 — no contributions[] needed yet
```

### Pattern 1: Skill-mediated dispatch (not code dispatch)

**What:** `steps[].ref.skill` never causes gsd-core's own JS to execute anything belonging to the
capability. It causes the orchestrating LLM agent to load and follow `SKILL.md` prose, which then
issues its own tool calls (Bash, Read, Write).
**When to use:** Every Phase 1 step (`plan:post`, `execute:wave:pre`, `execute:wave:post`).
**Example:**
```
- `ref.skill` present → dispatch via the Skill tool with skill id `gsd-<ref.skill>`.
```
[VERIFIED: gsd-core/gsd-core/references/loop-hook-dispatch.md:36]

### Pattern 2: Idempotent create via explicit id lookup, never title match

**What:** B4/B5 require identity by `<beads-id>`, not title. `bd` supports an explicit-id create
(`--id`) and a plain `bd show <id>` existence check.
**When to use:** Every `create-issues` run.
**Example:**
```
--id string   Explicit issue ID (e.g., 'bd-42' for partitioning)
```
[VERIFIED: `bd create --help` output, this session]
```
Usage:
  bd show [id...] [--id=<id>...] [--current] [flags]
```
[VERIFIED: `bd show --help` output, this session]

### Anti-Patterns to Avoid

- **Building command strings and shelling through `sh -c`:** N4 explicitly forbids executing any
  command string sourced from an artifact (PLAN.md content). Always build `subprocess.run([...])`
  argv lists from typed Python values (issue id strings, title strings) — never string-format a
  shell command and hand it to `shell=True`.
- **Matching by title:** B4 is explicit — title changes must never spawn a duplicate issue.
  Always resolve via `<beads-id>` first; only fall back to create when no `<beads-id>` element
  exists on that task.
- **Assuming `execute:wave:post` maps 1:1 to a single completed task:** confirmed above — it is a
  wave-scoped batch event. A close-one-issue design will silently miss every task past the first
  in a multi-plan or multi-task wave.
- **Reaching for `check.query`:** a third-party capability cannot register a new named query;
  only `check.predicate` is available, and Phase 1 needs neither (no gates).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dependency-graph enforcement between issues | A custom blocked/ready tracker | `bd dep add` + `bd ready`'s built-in blocker-aware semantics | `bd` already implements exactly this; reinventing it duplicates B2's acceptance criterion's own verification tool |
| Detecting whether `bd` is usable | A custom health-check protocol | `command -v bd` + a single cheap read command (`bd status` or `bd list -n 1`) wrapped in the skill's own timeout/error handling | N5 forbids extra tooling; a two-line bash check is sufficient and matches B6's "one visible notice" requirement directly |
| Cycle detection across plan dependency edges | Custom graph-cycle code in Python | `bd dep cycles` (shipped subcommand: "Detect dependency cycles") [VERIFIED: `bd dep --help` output, this session, "Available Commands: ... cycles Detect dependency cycles"] | `bd` already owns and enforces this against its own graph; do not duplicate |

**Key insight:** every piece of "tracker" logic (dependency ordering, ready-work computation,
cycle detection) belongs to `bd`, which already implements it correctly and is the entire reason
this capability exists. The capability's own code should be limited to translation (PLAN.md ↔ bd
issue) and orchestration (when to translate), never tracker logic.

## Common Pitfalls

### Pitfall 1: Treating `execute:wave:post` as task-level
**What goes wrong:** A `beads-sync` implementation that expects one task/one issue per dispatch
silently drops every task after the first plan/task in any wave with more than one completed
task.
**Why it happens:** The requirement text ("B3: after a wave completes task 2, that issue is
closed") reads task-singular, and the PRD's own risk table called wave granularity "assumed,"
inviting the same assumption downstream.
**How to avoid:** Design `close-wave` to accept a **list** of plan paths (or re-derive them from
`WAVE_PLAN_IDS`) and iterate every task in every plan, always.
**Warning signs:** A plan checker or manual test with a 2-task-in-one-wave plan shows only one
issue closed.

### Pitfall 2: Assuming a markdown heading exists to anchor `beads-id:`
**What goes wrong:** A regex like `^### Task \d+:` used to locate insertion points matches
nothing in any real PLAN.md, silently producing zero writes.
**Why it happens:** CONTEXT.md's D-03 was authored before this research verified the real schema.
**How to avoid:** Anchor on `<name>Task N: ...</name>` inside a `<task ...>` block instead; insert
`<beads-id>` immediately after the closing `</name>` tag (or after `<precondition>`/
`<reversibility>` if present, consistent with the documented insertion slot).
**Warning signs:** `git diff` after a sync run shows zero PLAN.md changes despite issues having
been created in `bd`.

### Pitfall 3: Gate predicate name typo (`command-exists` vs `command-exit-zero`)
**What goes wrong:** Not relevant to Phase 1 directly (no gates), but any Phase 3 planning that
copies PROJECT.md's `command-exists` name verbatim into a manifest will fail
`validateCapability()` — `command-exists` is not a recognized `kind`.
**Why it happens:** The name was carried over from the PRD without verification against source.
**How to avoid:** Always use `command-exit-zero`.
**Warning signs:** Capability load warning: "Unknown predicate kind."

### Pitfall 4: Forgetting the consent gate blocks a project-scoped install
**What goes wrong:** A Phase 1 plan that assumes dropping `capability.json` into
`.gsd/capabilities/beads/` is sufficient for the loop to pick it up. It is not — for a
skill-declaring, project-scoped capability, `gsd capability install ... --scope project` (with
its consent step) must run first, or every step silently reports `unconsented`/inactive.
**Why it happens:** Global-scope capabilities (which most first-party dogfooding examples use in
this environment) never hit this gate, making it easy to miss.
**How to avoid:** Include an explicit install+consent task/checkpoint in the plan.
**Warning signs:** `gsd_run loop render-hooks plan:post --raw` returns an empty `activeHooks`
array even though `capability.json` is present on disk.

## Code Examples

### Verified `capability.json` skeleton for Phase 1 scope (B1–B6 only)

```json
// Source: schema verified against gsd-core/docs/reference/capability-manifest.md (envelope +
// feature-body field tables) and gsd-core/capabilities/mempalace/capability.json (structural
// analog), gsd-core v1.10.0.
{
  "id": "beads",
  "role": "feature",
  "version": "0.1.0",
  "title": "Beads issue tracking",
  "description": "Beads is the task substrate: gsd plan tasks exist as beads issues, their status lives in beads.",
  "tier": "full",
  "requires": [],
  "engines": { "gsd": ">=1.6.0" },
  "runtimeCompat": { "supported": ["*"], "unsupported": [] },
  "skills": ["beads-sync", "beads-status"],
  "agents": [],
  "hooks": [],
  "config": {
    "beads.enabled": {
      "type": "boolean",
      "default": false,
      "description": "Master toggle for the beads issue-tracking capability."
    },
    "beads.sync_mode": {
      "type": "enum",
      "values": ["authoritative", "mirror", "off"],
      "default": "authoritative",
      "description": "authoritative: bd owns status and content after first sync. mirror/off reserved for later phases."
    }
  },
  "steps": [
    {
      "point": "plan:post",
      "ref": { "skill": "beads-sync" },
      "produces": ["BEADS.md"],
      "consumes": ["PLAN.md"],
      "when": "beads.enabled",
      "onError": "skip"
    },
    {
      "point": "execute:wave:post",
      "ref": { "skill": "beads-status" },
      "produces": ["BEADS.md"],
      "consumes": ["PLAN.md"],
      "when": "beads.enabled",
      "onError": "skip"
    }
  ],
  "contributions": [],
  "gates": []
}
```
*Notes:* `runtimeCompat` and `description` (per-config-key) are **required** fields the PRD's
draft manifest omitted [VERIFIED: gsd-core/docs/reference/capability-manifest.md:25 ("Validated
for every `role: "feature"` capability (a feature manifest without it fails validation)") and
:69 (`description` listed as a config-entry property with no "optional" marker, consistent with
every shipped example carrying one)]. `execute:wave:pre` is omitted from this minimal Phase 1 set
since B1–B6 do not require a pre-wave status refresh — add it only if Phase 2's B8 needs it.

### `<beads-id>` insertion point inside a real `<task>` block

```xml
<!-- Source: gsd-core/templates/phase-prompt.md:63-73, with <beads-id> added per the documented
     optional-child-element slot used by <precondition>/<reversibility> (plan-md.md:180,199,233) -->
<task type="auto">
  <name>Task 1: Create PostCard component</name>
  <beads-id>bd-a1b2c3</beads-id>
  <files>src/components/PostCard.tsx</files>
  <read_first>src/components/UserCard.tsx</read_first>
  <action>...</action>
  <verify>npx tsc --noEmit</verify>
  <acceptance_criteria>
    - src/components/PostCard.tsx exports named export PostCard
  </acceptance_criteria>
  <done>PostCard renders post content with author and timestamp</done>
</task>
```

### Verified `bd` invocations for the sync script

```bash
# Epic creation (D-05: title = ROADMAP.md phase header verbatim)
bd create "Phase 1: Substrate" --type epic --silent   # --silent prints only the new id

# Task issue creation, parented to the epic (B1)
bd create "01-01.1 Create PostCard component" --type task --parent "$EPIC_ID" --silent

# Dependency edge (B2): task 2 depends on (is blocked by) task 1
bd dep add "$TASK2_ID" --depends-on "$TASK1_ID"

# Idempotency check before create (B4/B5): does this beads-id still exist?
bd show "$EXISTING_ID" --json >/dev/null 2>&1 || echo "diverged: issue missing (D-07)"

# Batch close after a wave (B3) — bd close accepts multiple positional ids
bd close "$ID1" "$ID2" "$ID3" --reason "wave complete"
```
[VERIFIED: every flag above quoted from `bd create --help`, `bd dep add --help`, `bd show --help`,
`bd close --help` output captured this session against the locally installed `bd` v1.2.1 binary]

## State of the Art

| Old (assumed) | Corrected (verified) | When Changed | Impact |
|--------------|------------------|-----------|--------|
| `### Task N:` markdown heading | `<task type="auto"><name>Task N: ...</name>` XML element | Always — CONTEXT.md's assumption was never accurate for any shipped gsd-core version this session could locate | `<beads-id>` placement mechanism must change |
| Per-task `depends_on` field | Plan-level `depends_on` (array of plan ids); intra-plan order is implicit/sequential | Always | B2's dependency derivation needs an explicit design decision at plan time |
| `command-exists` predicate kind | `command-exit-zero` | Always (name was never `command-exists` in any shipped version) | Only matters for Phase 3, but the wrong name is now corrected everywhere in this doc |
| "Global-scope needs consent" | Project-scope needs consent; global-scope is trusted | Always | Phase 1's install+verify path needs an explicit consent step since it ships project-scoped |

**Deprecated/outdated:** `reviewerCli` boolean field (unrelated to this phase, replaced by the
`reviewer` body in 1.10.0) — noted only because it appeared during source review; not relevant to
`beads`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Cross-plan dependency mapping (last-task-of-prerequisite blocks first-task-of-dependent, vs. blocking every task) is a reasonable default when `depends_on` is plan-level | "Critical correction: depends_on is plan-level" | If wrong, `bd ready` either over-blocks (annoying) or under-blocks (lets an agent claim work whose prerequisite plan hasn't shipped) — low severity, correctable in a later sync run since it's a graph-edge choice, not data loss |
| A2 | A single `sync.py` with subcommands is preferable to three separate scripts | Standard Stack / Alternatives Considered | Purely a code-organization choice; wrong call costs refactor time only, no correctness risk |
| A3 | `checkpoint:human-verify`/`checkpoint:human-action` (rather than an unattended `--yes` install) is the right task type for the capability-install+consent step | "Correction: consent-gate scope" | If Phase 1's plan runs fully autonomous and skips this, every subsequent step silently no-ops with `unconsented` — high-severity but self-evident once one `bd list` shows zero issues created |

**If this table is empty:** N/A — see above.

## Open Questions

1. **Packaging (Python entry point vs. JS shell-out)** *(RESOLVED)*
   - What we know: Neither — the dispatch mechanism is a Claude-Code Skill (markdown
     instructions), verified against `loop-hook-dispatch.md` and `develop-a-capability.md`.
   - What's unclear: Nothing remaining that blocks planning.
   - Recommendation: Ship `SKILL.md` + a stdlib Python helper script; no JS.

2. **Wave granularity for `execute:wave:post`** *(RESOLVED)*
   - What we know: Fires once per wave, after all plans in the wave merge — verified against
     `execute-phase.md` step 5.75 and the closed 12-point vocabulary.
   - What's unclear: Nothing remaining that blocks planning.
   - Recommendation: `beads-status`/`beads-sync close-wave` must iterate every plan/task in the
     wave, never assume singular.

3. **Cross-plan dependency mapping shape (B2)** *(unresolved — planner decision required)*
   - What we know: `depends_on` is plan-level; intra-plan task order is implicit and
     procedurally enforced by the executor.
   - What's unclear: Whether every task in a dependent plan should block on every task of every
     prerequisite plan, or only first-blocks-on-last (see A1).
   - Recommendation: Default to first-blocks-on-last (fewer `bd dep add` calls, `bd ready`'s
     transitive blocker-awareness makes the distinction moot for `bd ready`'s output either way);
     record as a `Claude's Discretion` item if `/gsd-discuss-phase` is re-run, otherwise the
     planner should state the choice explicitly in PLAN.md.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `bd` binary | All of B1–B6 | ✓ | 1.2.1 [VERIFIED: `bd --version`, this session] | B6's fail-open path (skip + notice) when absent on a different machine |
| Python 3 | Sync/close-wave scripts | ✓ | 3.14.7 [VERIFIED: `python3 --version`, this session] | None — N5 forbids any alternative runtime |
| gsd-core (this project) | Capability loader itself | ✗ — no source checkout in `gsd-beads`, only the runtime skill overlay at `~/.claude/gsd-core/` (no `src/`) | 1.10.0 confirmed via a scratch clone of `open-gsd/gsd-core` for this research session only | This phase does not need a local gsd-core source checkout to *implement* — it only needs the capability.json to be schema-correct, which this research now guarantees; the scratch clone was research-only tooling, not a build dependency |
| `git` (for scratch clone) | This research session only | ✓ | — | N/A |

**Missing dependencies with no fallback:** none blocking Phase 1 implementation.

**Missing dependencies with fallback:** `bd` itself, via B6's designed degrade path — this is not
a gap, it is the requirement.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` (stdlib) — no pytest/other framework, per N5's "no dependency beyond bd + Python 3 stdlib" |
| Config file | none — `unittest discover` needs no config |
| Quick run command | `python3 -m unittest discover -s .gsd/capabilities/beads/tests -p 'test_*.py' -q` |
| Full suite command | same as quick run (test surface is small enough that quick == full for this phase) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| B1 | N-task plan produces N issues under one epic | unit (parses a fixture PLAN.md, asserts `bd create` argv built correctly via a fake/mock subprocess) | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestCreateIssues -v` | ❌ Wave 0 |
| B2 | Dependency edges match intra-plan order + `depends_on` | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestDependencyMapping -v` | ❌ Wave 0 |
| B3 | Wave-batch close touches only completed tasks in the wave | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestCloseWave -v` | ❌ Wave 0 |
| B4 | Re-sync resolves by `<beads-id>`, never creates a duplicate on title rename | unit | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestIdentityBinding -v` | ❌ Wave 0 |
| B5 | Two syncs over an unchanged plan create/modify nothing | unit (mock subprocess call-count assertion) | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestIdempotency -v` | ❌ Wave 0 |
| B6 | `bd` absent → skip with one notice, no exception | unit (PATH-mocked) | `python3 -m unittest .gsd.capabilities.beads.tests.test_sync.TestFailOpen -v` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** quick run command above
- **Per wave merge:** full suite (identical command — small surface)
- **Phase gate:** full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `.gsd/capabilities/beads/tests/test_sync.py` — covers B1–B6, using `unittest.mock.patch` on
  `subprocess.run` so no real `bd` database is touched by unit tests
- [ ] `.gsd/capabilities/beads/tests/fixtures/*.md` — at least one minimal real-schema PLAN.md
  fixture (XML `<task>` blocks, per the corrected schema above) and one multi-plan wave fixture
  for B3's batch-close test
- [ ] No framework install needed — `unittest` ships with Python 3 stdlib

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface — local CLI tooling only |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A — operates within the user's own repo/bd database |
| V5 Input Validation | Yes | All `bd` invocations built from typed Python values passed as `subprocess.run([...], shell=False)` argv lists — never a formatted shell string. This is N4's explicit mandate, not merely good practice. |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command injection via task title/description sourced from `PLAN.md` (an artifact, potentially authored by a different principal than the one running `bd`) | Tampering / Elevation of Privilege | Never interpolate PLAN.md text into a shell string; always pass as a discrete argv element to `subprocess.run([...], shell=False)` — exactly N4's rule, verified consistent with the loop-hook-dispatch.md's own guidance for `ref.command` validation ("never by pasting it into a shell command to be tested there") [VERIFIED: gsd-core/gsd-core/references/loop-hook-dispatch.md:45-51] |
| Path traversal via a maliciously-crafted `PLAN.md` frontmatter `phase`/`plan` field used to build a file path | Tampering | Confine all file reads/writes to the resolved `.planning/phases/<phase>/` directory; reject any path component containing `..` before use, matching gsd-core's own path-confinement invariant [VERIFIED: gsd-core/docs/reference/capability-manifest.md:286, "Path confinement. Declared module paths may not use parent-directory traversal (../)"] |

## Sources

### Primary (HIGH confidence — read directly from a shallow clone of `open-gsd/gsd-core` @ v1.10.0, this session)
- `src/capability-loader.cts` — full read, loader/consent/reserved-prefix mechanics
- `src/loop-resolver.cts` — full read, hook activation/rendering mechanics
- `src/gate-predicate-evaluator.cts` — full read, gate predicate kind table
- `src/check-command-router.cts` — targeted read, `check.query` closed subcommand set
- `docs/reference/capability-manifest.md` — full read, canonical schema reference
- `docs/reference/plan-md.md` — full read, canonical PLAN.md schema reference
- `docs/how-to/develop-a-capability.md` — full read, authoring guide
- `docs/tutorials/build-your-first-capability.md` — targeted read, consent-gate worked example
- `capabilities/mempalace/capability.json` — full read, structural analog
- `gsd-core/templates/phase-prompt.md` — targeted read, literal planner-facing `<task>` template
- `gsd-core/workflows/execute-phase.md` — targeted read, wave dispatch mechanics (steps 2.75, 5.75)
- `gsd-core/workflows/plan-phase.md` — targeted read, `plan:pre`/`plan:post` dispatch mechanics
- `gsd-core/workflows/execute-plan.md` — targeted read, per-task sequential execution gate
- `gsd-core/references/loop-hook-dispatch.md` — full read, canonical point-agnostic dispatch contract
- `bd --help`, `bd create --help`, `bd dep --help`, `bd dep add --help`, `bd list --help`,
  `bd close --help`, `bd show --help`, `bd epic --help` — captured directly from the locally
  installed `bd` v1.2.1 binary, this session

### Secondary (MEDIUM confidence)
- WebSearch confirming `open-gsd/gsd-core` GitHub location and npm package `@opengsd/gsd-core`
  version list (used only to locate the source, not as a factual claim source — all factual
  claims above are sourced from the cloned repo directly)

### Tertiary (LOW confidence)
- None used for load-bearing claims in this document.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `bd` and Python versions verified live on this machine; capability
  schema verified against source, not training memory.
- Architecture: HIGH — loader, loop-resolver, gate-predicate, and dispatch-contract source read
  in full for the load-bearing modules; workflow prose read at the exact line ranges cited.
- Pitfalls: HIGH — every pitfall traces to a specific, quoted source line, not inference.

**Research date:** 2026-08-15
**Valid until:** 30 days (gsd-core is an actively developed, versioned ecosystem — re-verify
schema/dispatch facts against the then-current `open-gsd/gsd-core` release before Phase 2/3
planning if more than a few weeks have elapsed)
