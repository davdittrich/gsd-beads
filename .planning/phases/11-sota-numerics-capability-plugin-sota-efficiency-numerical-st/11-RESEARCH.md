# Phase 11: sota-numerics capability plugin - Research

**Researched:** 2026-08-17
**Domain:** gsd-core capability-plugin authoring (loop-hook contributions, capability gates, SessionStart auto-install) — no external language/framework stack
**Confidence:** HIGH on the mechanical/dispatch questions (read installed gsd-core source directly), MEDIUM on exact frontmatter field naming (Claude's Discretion per CONTEXT.md), LOW/ASSUMED on nothing load-bearing — every mechanism claim below traces to a specific file+line read this session.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** The blocking gate is universal — fires at `plan:post` for every phase's `PLAN.md` once `sota-numerics.enabled` is true, regardless of domain.
- **D-02:** Scope is per-plan, not per-task. One "Alternatives Considered" section per `PLAN.md`.
- **D-03:** Trivial plans (pure config/doc/mechanical-rename, no real mechanism choice) are exempt: the planner may write "N/A — no mechanism choice" and the gate accepts that as satisfying the section-presence check.
- **D-04:** Dogfooded in this repo — install and enable `sota-numerics` in gsd-beads' own `.gsd/capabilities/` once shipped; this repo's own future phase plans go through the gate too.
- **D-05:** A phase with a `SPEC.md` still independently requires `PLAN.md`'s own Alternatives Considered section — SPEC.md's analysis does not satisfy it.
- **D-06:** The gate requires cited grounding per alternative — attached source (URL, doc ref, dated citation), not just section-presence.
- **D-07:** Citations require a recency marker (a date, or the source itself being visibly current). A source with no discoverable date does not satisfy the check.
- **D-08:** Truthfulness of citations cannot be verified by a frontmatter predicate — gsd-core's predicate kinds are structural checks only. Verification is layered: a structural predicate checks presence/well-formedness, and `gsd-plan-checker` gets a contribution fragment to spot-check plausibility before the gate is allowed to pass. Soft, human-adjacent check, not a hard guarantee.
- **D-09:** The check also requires the plan to name which ranked criterion (performance / simplicity-LOC / ecosystem / maintenance, in that order) decided each mechanism pick.
- **Minimum count:** at least 2 named, cited, dated alternatives per non-trivial mechanism choice.
- **D-10:** `sota-numerics.enabled` defaults **true** — blocks immediately post-install, including in this repo per D-04. Diverges from `beads.enabled`'s default-false.
- **D-11:** One single config key controls both advisory steering and the blocking gate — no separate `gate_enabled` split.
- **D-12:** Full four-point spread: `plan:pre` (planner — SOTA-research framing), `execute:wave:pre` (executor — numerical-stability/no-cancellation framing), `execute:wave:post` (verifier — "flag unjustified simplification/precision loss" framing), `ship:pre` (ship reviewer — advisory only, no gate).
- **D-13:** Stage-tailored fragment text, not one shared generic reminder.

### Claude's Discretion

- Exact per-lifecycle-point fragment wording within the D-12/D-13 framings.
- Exact schema/field names for the frontmatter/derived-check the `plan:post` step writes and the exact predicate expression(s) the gate evaluates against it.
- Exact wording of the `gsd-plan-checker` contribution fragment for citation-plausibility spot-checking (D-08).
- Config key naming beyond `sota-numerics.enabled` (D-11).
- Capability id / directory name and exact `into:` targeting per contribution point.
- How the `plan:post` step distinguishes "trivial, exempt" (D-03) plans from ones requiring the gate.

### Deferred Ideas (OUT OF SCOPE)

- **`beads.enabled` default flip to `true`** — routed to Phase 11.1, not part of Phase 11.

</user_constraints>

<phase_requirements>
## Phase Requirements

No REQUIREMENTS.md entries exist for this phase (Requirements: TBD, same as Phase 10/10.1 — new scope outside the v1.1 milestone's tracked requirement set). No `phase_req_ids` to map.
</phase_requirements>

## Summary

This phase authors a third capability plugin (`sota-numerics`) in this repo's marketplace, following the `beads`/`ponytail-everywhere` structural precedent exactly for packaging, SessionStart auto-install, and advisory contribution fragments. The one genuinely new mechanism is a **blocking `plan:post` gate** — the first blocking gate this repo has declared outside `ship:pre`.

The single highest-priority open question the phase brief flagged — "does `plan:post` have a generic gate dispatch loop, or does this phase need a `GSD-CORE-PATCH.md`-style local patch like beads' `ship:pre` fix?" — resolves to **partially, with a twist that changes the recommended design**:

1. **The `plan:post` GATE dispatch loop already exists natively** (`plan-phase.md` §13e, "Post-Planning Gap Analysis (plan:post capability gate dispatch)"), and it is generic — it enumerates every active `kind=="gate"` hook, not just the built-in `gap-analysis` capability that currently owns it. **No core patch is needed for the gate itself to fire and block.** [VERIFIED: ~/.claude/gsd-core/workflows/plan-phase.md:1340-1379]
2. **But there is no `plan:post` STEP dispatch loop** — nothing in the installed workflow executes a `kind=="step"` hook at `plan:post` (the mechanism CONTEXT.md's D-08 implicitly assumed would compute derived frontmatter before the gate runs). This is not hypothetical: `beads` itself declares exactly this shape (`plan:post` step, skill `beads-sync`) and it has **zero dispatch call sites anywhere in gsd-core's workflows** — confirmed by grep across every workflow file. It is schema-valid, installed, and silently inert today, in this very repo. [VERIFIED: ~/.claude/gsd-core/workflows/plan-phase.md (no `beads-sync`/`gsd-beads-sync` match); /home/dd/projects/gsd-beads/.gsd/capabilities/beads/capability.json:72-85]
3. **There is also no contribution-rendering call site for `into: "checker"`** at `plan:pre` or `plan:post` — the `checker` agent role is schema-valid there (Loop Host Contract lists `["researcher","planner","checker"]` for the `plan` step), but zero existing capability uses it, and `plan-phase.md` step 10 (checker spawn) never renders `kind=="contribution"` hooks into the checker prompt. D-08's "citation-plausibility spot-check fragment for gsd-plan-checker" is therefore genuinely inert without a small local patch — same category of gap as the `ship:pre` patch, but scoped to one prompt-construction step, not gate dispatch. [VERIFIED: ~/.claude/gsd-core/bin/lib/loop-host-contract.cjs:28-47; ~/.claude/gsd-core/workflows/plan-phase.md:937-996 (no contribution render call)]
4. **The `artifact-frontmatter-equals` predicate cannot do the real validation work anyway** — it only supports strict equality on one field of one artifact (no `>=`, no multi-file aggregation), and `findPhaseArtifact` resolves to the *first* `*-PLAN.md` match in `readdir` order when a phase has multiple plans — not deterministic, not "all plans." [VERIFIED: ~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs:104-146; ~/.claude/gsd-core/bin/lib/check-command-router.cjs:859-889]

**Primary recommendation:** skip the frontmatter-STEP-then-GATE design implied by CONTEXT.md's D-08 phrasing entirely. Declare the blocking gate as a **`command-exit-zero` predicate** whose command invokes a small project-local script (`.gsd/capabilities/sota-numerics/scripts/check-alternatives.{py,sh}`) that globs `${PHASE_DIR}/*-PLAN.md` itself, validates every plan's Alternatives Considered section directly against its markdown body (count ≥2, citation, date, ranked-criterion, or the D-03 exemption string), and exits 0/1. This needs **zero core patches**, sidesteps the multi-plan-artifact ambiguity, and reuses `${PHASE_DIR}` interpolation gsd-core already provides. The D-08 plan-checker plausibility spot-check is a separate, smaller decision — see Pitfall 3 and Architecture Pattern 2 below for the patch-vs-fold-into-script tradeoff.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Blocking Alternatives-Considered gate | gsd-core workflow (`plan-phase.md` §13e, generic dispatch) | Project-local capability script (`command-exit-zero`) | Gate *dispatch* is core-owned infrastructure already generic; gate *logic* must live in a capability-owned script since core cannot host project-specific validation without a patch |
| Advisory steering fragments (plan/execute/verify/ship) | Capability `contributions[]`, rendered by existing `plan:pre`/`execute:wave:pre`/`execute:wave:post`/`ship:pre` render-hook call sites | — | Identical to `ponytail`'s already-working pattern — no new dispatch machinery needed |
| Citation-plausibility spot-check (D-08) | Either: (a) a local patch adding `into:"checker"` rendering to `plan-phase.md` step 10, or (b) folded into the deterministic check script as regex/date heuristics | `gsd-plan-checker` agent (if (a) chosen) | Genuine LLM judgment (real URL plausibility) only reachable via (a); (b) is mechanical and patch-free but weaker |
| SessionStart auto-install | Vendored `capability-auto-install.sh` (byte-identical copy per plugin, Phase 10.1 D-05) | `hooks/session-start.sh` | Fully reusable as-is — generic, takes `CAP_ID` as `$1`, zero modification needed |
| Marketplace registration | `.claude-plugin/marketplace.json` `plugins[]` | `sota-numerics/.claude-plugin/plugin.json` | Same shape as `ponytail-everywhere`'s existing third-listed... second-listed entry |

## Standard Stack

Not applicable in the conventional sense — this phase authors gsd-core capability-plugin artifacts (JSON manifests, markdown fragments, a shell/Python validation script), not application code against a third-party library stack. No npm/pip packages are introduced.

### Core (internal mechanisms, not packages)

| Mechanism | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| gsd-core capability schema (`capability.json`) | gsd `>=1.10.0` (installed version, confirmed) | Declares config, steps, contributions, gates | Same schema `beads`/`ponytail` already validate against | 
| `command-exit-zero` predicate kind | gsd-core 1.10.0, `gate-predicate-evaluator.cjs` | Runs a bounded shell command; block iff non-zero exit | Only predicate kind expressive enough for count/date/citation logic without a core patch |
| `capability-auto-install.sh` (Phase 10.1) | vendored, byte-identical per plugin | SessionStart auto-grant at user scope | Already proven working for `beads`/`ponytail`; zero changes needed for a third `CAP_ID` |

### Package Legitimacy Audit

**Not applicable.** This phase installs no external npm/PyPI/crates packages. The validation script may use Python 3 stdlib only (already an accepted project dependency per REQUIREMENTS.md v1.1's N5 constraint — "no new runtime dependency beyond the `bd` binary and Python 3 stdlib" — and precedented by `.gsd/capabilities/beads/scripts/sync.py`) [VERIFIED: /home/dd/projects/gsd-beads/.planning/REQUIREMENTS.md:81-82; /home/dd/projects/gsd-beads/.gsd/capabilities/beads/scripts/sync.py (file exists, read directory listing)], or POSIX `sh`/`bash` (already used by every existing hook/script in this repo).

## Architecture Patterns

### System Architecture Diagram

```
/gsd-plan-phase N
  │
  ├─ step 5.6  plan:pre render-hooks  ──► planner prompt
  │              (into: "planner")         gets sota-numerics D-12/D-13 SOTA-research
  │                                         framing fragment  [EXISTING dispatch, reused]
  │
  ├─ step 8    gsd-planner writes *-PLAN.md
  │              (with "## Alternatives Considered" section per D-02/D-03)
  │
  ├─ step 10   gsd-plan-checker spawned
  │              ├─ (a) PATCHED: render plan:post "into: checker" contribution
  │              │       → LLM spot-checks citation plausibility (D-08)
  │              └─ (b) UNPATCHED fallback: checker's existing generic
  │                      "review *-PLAN.md content" instructions already see
  │                      the Alternatives Considered section as ordinary plan
  │                      content — no dedicated capability channel required
  │
  ├─ steps 10-12  Revision loop (max 3 iterations) — BLOCKER/WARNING from
  │                checker can force the planner to fix Alternatives Considered
  │                BEFORE anything commits — this is the cheap, pre-commit
  │                enforcement point
  │
  ├─ step 13a  Decision Coverage Gate (hardcoded, blocks HERE, before commit)
  ├─ step 13b  STATE.md marked "Ready to execute"
  ├─ step 13c  ROADMAP annotated
  ├─ step 13d  Plans committed to git (if commit_docs)
  │
  └─ step 13e  plan:post GATE dispatch (GENERIC, existing)
                 ├─ render-hooks plan:post --raw
                 ├─ for each active kind=="gate" hook (sota-numerics' new entry):
                 │     check.predicate.kind == "command-exit-zero"
                 │     command: globs ${PHASE_DIR}/*-PLAN.md, validates each
                 │     plan's Alternatives Considered section directly
                 │     (no reliance on frontmatter or a plan:post STEP)
                 └─ block==true + blocking==true  →  HALT
                      (⚠ this halt fires AFTER 13b/13d — plans are already
                      committed and STATE.md already says "Ready to execute"
                      when the hard block happens — see Pitfall 1)
```

### Recommended Project Structure

```
sota-numerics/                          # top-level plugin dir, sibling to ponytail-everywhere/
├── .claude-plugin/
│   └── plugin.json                     # name/version/author/license, mirrors ponytail-everywhere's
├── .gsd/capabilities/sota-numerics/    # vendored bundle (Phase 10.1 D-05 pattern)
│   ├── capability.json
│   ├── fragments/
│   │   ├── planner-sota.md             # plan:pre, into: planner
│   │   ├── executor-numerics.md        # execute:wave:pre, into: executor
│   │   ├── verifier-precision.md       # execute:wave:post, into: verifier
│   │   ├── ship-precision-advisory.md  # ship:pre, into: orchestrator (advisory only)
│   │   └── checker-citation-spotcheck.md   # ONLY if the plan-checker patch (option a) is taken
│   └── scripts/
│       └── check-alternatives.py       # the command-exit-zero gate's actual logic
├── hooks/
│   ├── hooks.json                      # SessionStart + SubagentStart, copy ponytail's shape
│   ├── session-start.sh                # calls capability-auto-install.sh sota-numerics
│   ├── capability-auto-install.sh      # BYTE-IDENTICAL vendored copy (Phase 10.1 pattern)
│   └── gsd-tools.sh                    # resolver, copy verbatim
└── tests/
    └── test-check-alternatives.sh      # stdlib-only smoke test, mirrors ponytail's test-session-start.sh

.gsd/capabilities/sota-numerics/        # repo-root dogfood copy (D-04) — same bundle content,
└── ...                                 # installed via /gsd capability install here directly
```

### Pattern 1: Blocking gate via `command-exit-zero`, not `artifact-frontmatter-equals`

**What:** Declare the `plan:post` gate's `check.predicate` as `{"kind": "command-exit-zero", "command": "...", "timeout": <seconds>}` rather than `artifact-frontmatter-equals`.

**When to use:** Whenever the check logic (a) needs to inspect content across multiple files matching a glob, (b) needs anything beyond strict equality (counts, regex, date parsing), or (c) has no upstream `plan:post` STEP actually writing derived state — all three apply here.

**Example** (verified predicate contract, not aspirational):
```json
{
  "point": "plan:post",
  "check": {
    "predicate": {
      "kind": "command-exit-zero",
      "command": "python3 \"${CLAUDE_PLUGIN_ROOT:-.}/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py\" \"${PHASE_DIR}\"",
      "timeout": 30
    }
  },
  "blocking": true,
  "onError": "skip"
}
```
Source: mechanism verified against `~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs:41-103` (the `${PHASE_DIR}` interpolation and `command-exit-zero` field contract) — this exact JSON shape is my own composition from that contract, not copied from an existing capability (no existing capability in this install uses `command-exit-zero` at `plan:post`; `gap-analysis` uses a core-only `check.query` not available to project-local capabilities, and `beads`/`ponytail` only use `artifact-frontmatter-equals`). Treat the field names as `[VERIFIED]` and the specific `command`/`timeout` values as illustrative.

**`onError: "skip"` is the correct precedent value**, not `"halt"` — it governs the *check command itself failing to run* (crash, timeout, malformed output), not the block decision. Every existing gate in this repo (`beads`'s two `ship:pre` gates) uses `onError: "skip"`; the "not fail-open by design" language in CONTEXT.md's code_context refers to `blocking: true` (the block decision itself, which is a separate field never touched by `onError`), not to swapping `onError` to `"halt"`. [VERIFIED: /home/dd/projects/gsd-beads/.gsd/capabilities/beads/capability.json:156-185; ~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs:14-19 comment: "the workflow's two-step gate contract treats [a thrown error] as a step-1 command failure (routed per the gate's onError)"]

### Pattern 2: Checker plausibility spot-check — patch vs. fold-in

**What:** D-08 wants `gsd-plan-checker` to independently spot-check that cited URLs/dates "look plausible" before the gate is allowed to pass.

**Two viable designs, both defensible — flag for planner/user decision, do not silently pick one:**

- **(a) Small local patch** to `~/.claude/gsd-core/workflows/plan-phase.md` step 10 (`## 10. Spawn gsd-plan-checker Agent`), adding a render call for `plan:post`/`plan:pre` `kind=="contribution"` hooks where `into=="checker"`, injected into `checker_prompt` before the `Agent()` call — same *category* of local patch as `.gsd/capabilities/beads/GSD-CORE-PATCH.md`'s `ship.md` patch, but far smaller: one new paragraph, one new render call, no new gate-evaluation logic (that already exists generically). Should be documented the same way: its own `GSD-CORE-PATCH.md` under `.gsd/capabilities/sota-numerics/`, with an upstream issue filed, a revert condition, and a patch-loss detector (mirroring `beads-recall/SKILL.md`'s Step 3.5 pattern — run a cheap presence-check for the patch marker at a point the *generic* dispatch already reaches, e.g. `plan:pre`).
- **(b) Fold plausibility heuristics into `check-alternatives.py` directly** — a URL-shape regex, a "date within N months of today" check, rejection of obvious placeholder domains (`example.com`, `TODO`, `TBD`). Zero patch, zero new dispatch surface, ships in Phase 11 with no core-repo risk. Weaker than genuine LLM judgment (cannot detect a syntactically-valid but hallucinated URL), but honest about that limitation and fully mechanical — consistent with this repo's own ladder-discipline precedent (`ponytail`'s ladder: reach for a deterministic check before an LLM-mediated one).

**Recommendation:** (b) first, ship Phase 11 patch-free; treat (a) as a follow-up only if (b)'s false-negative rate on hallucinated-but-well-formed URLs proves unacceptable in dogfood use (D-04). This mirrors D-08's own "soft, human-adjacent check, not a hard guarantee" framing — (b) already meets that bar.

### Pattern 3: Multi-plan-per-phase aggregation

**What:** A phase can have multiple `*-PLAN.md` files (e.g. `10-01-PLAN.md`, `10-02-PLAN.md` in Phase 10's own directory — confirmed on disk). `findPhaseArtifact` (the function backing `artifact-frontmatter-equals`) returns only the *first* filesystem-order match for a glob suffix like `"PLAN.md"` — not deterministic, not "all of them." [VERIFIED: ~/.claude/gsd-core/bin/lib/check-command-router.cjs:859-889, `for (const f of files)` returns on first match; confirmed multi-plan phase precedent at /home/dd/projects/gsd-beads/.planning/phases/10-ponytail-everywhere-capability-plugin-advisory-only-ladder-d/ containing both `10-01-PLAN.md` and `10-02-PLAN.md`]

**When to use:** Any gate that must hold for *every* plan in a phase (this one does — D-02 is per-plan).

**How to avoid the pitfall:** Do not use `artifact-frontmatter-equals` against a `"PLAN.md"` suffix for this gate at all (see Pattern 1) — a `command-exit-zero` script that globs `"${PHASE_DIR}"/*-PLAN.md` itself and loops over every match is the only correct way to guarantee full-phase coverage with the predicate kinds this schema actually supports.

### Anti-Patterns to Avoid

- **Declaring a `plan:post` `steps: [{skill: ...}]` entry expecting it to run automatically:** it will not. No `kind=="step"` dispatch loop exists for `plan:post` in the installed `plan-phase.md` — proven by `beads`'s own identically-shaped `plan:post` step (`beads-sync`) being schema-valid, installed, and never invoked by any workflow file in this gsd-core install. Do not copy `beads`'s `steps[]` shape for `plan:post` and assume it works differently for a new capability id.
- **Relying on `check.query` for a project-local capability:** `gap-analysis`'s `plan:post` gate uses `check.query: "gap-analysis.plan-post"` — a name registered inside gsd-core's own `check-command-router.cjs`. A project-local `.gsd/capabilities/` bundle cannot register a new query name without a core-side code change; only `check.predicate` (the ADR-2008 generic evaluator) is extensible from a capability manifest alone. [VERIFIED: ~/.claude/gsd-core/bin/lib/capability-registry.cjs:1542-1551 (gap-analysis's core-registered `tier: "standard"` entry, `version: "1.10.0"` matching the installed core version exactly, confirming it ships as PART of gsd-core, not as an installable project bundle)]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SessionStart auto-install of the capability bundle | A new auto-install script | Byte-identical vendored copy of `ponytail-everywhere/hooks/capability-auto-install.sh`, called with `CAP_ID=sota-numerics` | Script already takes `CAP_ID` as a generic `$1` argument — zero modification needed, proven working for two capabilities already |
| Config toggle read in `session-start.sh` | Custom config parsing | `gsd_tools config-get sota-numerics.enabled --default true`, same pattern as `ponytail`'s own `session-start.sh` | Existing `gsd-tools.sh` resolver + `config-get` subcommand handles the runtime-detection fallback chain already |
| Gate/block halt semantics | A custom exit-code / message contract | The existing "two-step gate contract" (`Step 1 — command failure` / `Step 2 — block evaluation`) already implemented in `plan-phase.md` §13e | Identical contract already used by `gap-analysis` and (for `ship:pre`) `beads` — reinventing it risks a subtly different halt message shape the plan-checker/verifier don't recognize |

**Key insight:** every piece of *infrastructure* this phase needs (auto-install, config resolution, gate dispatch, fragment rendering at `plan:pre`/`execute:wave:pre`/`execute:wave:post`/`ship:pre`) already exists and works. The only genuinely new code this phase writes is (1) four short markdown fragments, (2) one JSON `capability.json`, (3) one validation script (`check-alternatives.py`) that the *existing* `command-exit-zero` gate mechanism calls.

## Common Pitfalls

### Pitfall 1: `plan:post` gate fires AFTER commit and AFTER STATE.md says "Ready to execute"

**What goes wrong:** §13e (the gate dispatch) runs *after* §13b (STATE.md marked planned) and §13d (plans committed to git, if `commit_docs`). A block at §13e halts the workflow, but the non-compliant `PLAN.md` is already committed and `STATE.md` already claims the phase is ready to execute.

**Why it happens:** §13e is a late-added generic gate loop, originally built only for the non-blocking, purely-informational `gap-analysis` capability (its own code comment says as much: "gap-analysis is always `blocking: false` so this branch is informational only"). sota-numerics is the first capability to actually exercise the `blocking: true` branch of that loop — an untested code path in production terms. [VERIFIED: ~/.claude/gsd-core/workflows/plan-phase.md:1306-1379, exact step order and the "(gap-analysis is always blocking: false...)" comment]

**How to avoid:** Treat the checker's revision loop (steps 10-12, which run *before* §13a-13e) as the PRIMARY enforcement point — a plan missing/malformed Alternatives Considered should already be a checker BLOCKER, forcing revision before anything commits. The `plan:post` `command-exit-zero` gate is then a structural backstop, consistent with the fact that its own late position makes it a last-resort catch, not the first line of defense. Document this ordering explicitly in the plan so a future contributor doesn't assume the gate alone is sufficient.

**Warning signs:** A dogfood run (D-04) where the gate blocks and the user is confused that `git log` already shows a "planned" commit for a phase STATE.md still calls "Ready to execute" is expected behavior under this design — surface a clear remediation message in the gate's failure output (`GATE_RESULT.message`) telling the user to fix `PLAN.md` and re-run `/gsd-plan-phase N --force` (the closed-phase gate at §1.5 permits re-planning a non-`Complete` phase).

### Pitfall 2: Predicate kind name is `command-exit-zero`, not `command-exists`

**What goes wrong:** CONTEXT.md's canonical_refs paraphrases the two predicate kinds as `command-exists` and `artifact-frontmatter-equals`. The actual registered kind name in the evaluator's `KIND_TABLE` is **`command-exit-zero`** — using `"command-exists"` in `capability.json` will throw `Unknown predicate kind` at gate-evaluation time (the evaluator throws for any kind not in its table, which the workflow's step-1 error handling then routes per `onError`). [VERIFIED: ~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs:37,148-151,187-190 — `EVALUATOR_KINDS = Object.freeze(['command-exit-zero', 'artifact-frontmatter-equals'])`]

**How to avoid:** Use the literal string `"command-exit-zero"` in every `check.predicate.kind` field.

### Pitfall 3: `artifact-frontmatter-equals`'s `equals` is strict-equality only

**What goes wrong:** There is no `gte`/`contains`/numeric-comparison predicate kind. A design that tries to check "at least 2 alternatives" via frontmatter equality needs an intermediate STEP to reduce that count to a boolean/enum first — and (per the Summary above) no `plan:post` STEP dispatch exists to run that reduction automatically. [VERIFIED: ~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs:114-146 — `evaluateArtifactFrontmatterEquals` only ever compares `actualValue === expectedValue` or their stringified forms]

**How to avoid:** See Pattern 1 — do all counting/validation logic inside the `command-exit-zero` script itself, which can run arbitrary Python/shell logic and simply `exit 0`/`exit 1`.

### Pitfall 4: Auto-install state-file collisions across vendored copies

**What goes wrong:** Each plugin's vendored `capability-auto-install.sh` writes a hash sidecar keyed by `CAP_ID` at `${GSD_HOME:-$HOME}/.gsd/capability-auto-install-$CAP_ID.hash` — already correctly namespaced per capability id, confirmed working for `beads`/`ponytail` with zero observed collisions. A **new** risk specific to this phase: if `sota-numerics` is chosen as both the capability id AND accidentally reused as a config-key prefix that collides with an existing key, the capability loader rejects the install. [VERIFIED: /home/dd/projects/gsd-beads/ponytail-everywhere/hooks/capability-auto-install.sh:42-46 for the namespacing; capability-id collision-check confirmed absent from the registry via the "No collision" grep above]

**How to avoid:** Confirmed clear — `sota-numerics` does not collide with any of the ~45 ids currently registered in gsd-core's own `capability-registry.cjs` or this repo's two project-local capabilities (`beads`, `ponytail`).

## Code Examples

### Verified predicate evaluator dispatch shape (`command-exit-zero`)

```javascript
// Source: ~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs:62-103 (read verbatim this session)
function evaluateCommandExitZero(predicate, ctx, deps) {
    const command = predicate['command'];
    // ... interpolates ${PHASE_NUMBER} / ${PHASE_DIR} / ${PHASE_REQ_IDS} into `command`
    const res = deps.runBoundedShell({ command: interpolated, cwd: ctx.cwd, timeoutMs });
    if (res.exitCode === 0) {
        return { block: false, message: 'command exited 0', ... };
    }
    // non-zero (or timeout) => block: true, message carries stderr/stdout tail (max 2000 chars)
}
```

### Verified two-step gate contract (workflow-side)

```markdown
<!-- Source: ~/.claude/gsd-core/workflows/plan-phase.md:1369-1379 (read verbatim this session) -->
**Step 1 — did the CHECK COMMAND itself succeed?**
If the check command failed (non-zero CHECK_EXIT, empty output, or unparseable JSON):
- onError == "halt" -> halt and surface command error.
- onError == "skip" -> log a warning and continue to the next hook.

**Step 2 — read GATE_RESULT.block (boolean).** Only reached when command succeeded.
- If hook.blocking == true and GATE_RESULT.block == true: halt.
- If hook.blocking == false (advisory): output the table and continue, never blocks.
- If hook.blocking == true and GATE_RESULT.block == false: continue silently.
```

### Verified Loop Host Contract entry for the `plan` step

```javascript
// Source: ~/.claude/gsd-core/bin/lib/loop-host-contract.cjs:28-47 (read verbatim this session)
{
  "step": "plan",
  "points": ["plan:pre", "plan:post"],
  "agentRoles": ["researcher", "planner", "checker"],   // "checker" IS valid here
  "coreArtifacts": { "produces": ["PLAN.md"], "consumes": ["CONTEXT.md"] }
}
```
No existing capability contribution anywhere in `capability-registry.cjs` targets `"into": "checker"` — confirmed by an exhaustive grep returning zero matches. This is genuinely new territory, not an established-but-unnoticed pattern.

## State of the Art

| Old Approach (what CONTEXT.md's canonical_refs assumed) | Current Approach (verified this session) | When Changed | Impact |
|--------------|------------------|--------------|--------|
| "gsd-core's only predicate kinds are `command-exists` and `artifact-frontmatter-equals`" | The actual kind name is `command-exit-zero` | N/A — CONTEXT.md paraphrase was imprecise, not stale | Using the wrong literal string throws at gate-evaluation time |
| "plan:post lacks generic gate dispatch, needing a `GSD-CORE-PATCH.md` like `ship:pre`'s" | `plan:post` GATE dispatch is generic and already exists (§13e); only the CONTRIBUTION-into-checker channel and the STEP dispatch are missing | N/A — the open question in the phase brief was answered by direct source read, not by a version change | Materially smaller patch surface than assumed, if a patch is taken at all (Pattern 2 offers a patch-free alternative) |

**Deprecated/outdated:** Nothing in this domain is deprecated — this is all live, current-version (`gsd 1.10.0`) infrastructure read directly from the installed workflow and library source this session.

## Runtime State Inventory

Not applicable — this is a greenfield capability-authoring phase (new plugin directory, new capability id), not a rename/refactor/migration. No existing runtime state references `sota-numerics` anywhere to migrate.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The `command-exit-zero` gate's specific `command`/`timeout` JSON values shown in Pattern 1's example are illustrative, not copied from an existing working capability (no existing capability in this install uses `command-exit-zero` at `plan:post`) | Architecture Patterns → Pattern 1 | Low — the field *names* and *kind* string are verified against the evaluator source; only the exact command string is the planner's to fill in |
| A2 | Recommendation to prefer Pattern 2(b) (fold plausibility heuristics into the script) over 2(a) (core patch) is a judgment call, not dictated by CONTEXT.md, which left this to discretion | Architecture Patterns → Pattern 2 | Medium — if the user actually wants genuine LLM-mediated plausibility checking (closer to D-08's literal wording), 2(a)'s patch is the correct call instead; flag this choice explicitly to the user during planning rather than silently defaulting to 2(b) |
| A3 | `${CLAUDE_PLUGIN_ROOT:-.}` is the correct way to resolve the script path inside a `command-exit-zero` command string cross-plugin — inferred from how `session-start.sh`/`capability-auto-install.sh` resolve `PLUGIN_ROOT`, not independently verified for the gate-predicate execution context (which runs via `gsd_run check predicate`, a different code path than the hooks) | Architecture Patterns → Pattern 1 | Medium — the planner should verify at implementation time whether `CLAUDE_PLUGIN_ROOT` is set in the gate-evaluation subprocess's environment, or use an absolute/`git rev-parse --show-toplevel`-relative path instead (the dogfood install under `.gsd/capabilities/sota-numerics/` at repo root, per D-04, sidesteps this entirely since it has a fixed relative path from repo root) |

## Open Questions

1. **Does the gate-evaluation subprocess (`gsd_run check predicate`) run with `CLAUDE_PLUGIN_ROOT` set, when triggered from a plugin-installed (not repo-root-dogfooded) capability?**
   - What we know: the SessionStart/SubagentStart hooks (`hooks.json`) definitely receive `CLAUDE_PLUGIN_ROOT` (Claude Code sets it for hook commands). The gate-predicate command runs from a different call site (`plan-phase.md` §13e's `gsd_run check predicate` invocation), whose environment was not traced this session.
   - What's unclear: whether that subprocess inherits the plugin's root path the same way, or whether the script path must instead be resolved relative to the *installed capability bundle's* location (which `capability install` copies somewhere under `.gsd/` or a user-scope directory — the exact install-destination path was not traced this session).
   - Recommendation: at plan time, either (a) trace `capability install`'s actual copy destination for a `scripts/` subdirectory precedent (does `beads`'s already-installed `scripts/sync.py` get copied verbatim, and where does the installed copy live relative to a phase's `cwd`?), or (b) sidestep entirely by using `git rev-parse --show-toplevel`-relative paths inside the command string, mirroring `capability-auto-install.sh`'s own `git rev-parse --show-toplevel` fallback pattern for locating `gsd-tools.cjs`.

2. **Exact frontmatter/config field names for `sota-numerics.enabled` and any strictness knob** — left to Claude's Discretion per CONTEXT.md; no existing precedent to verify against since no comparable ranked-criterion/citation config exists elsewhere in this install. Recommend `sota-numerics.enabled` (boolean, default `true` per D-10) as the sole key per D-11 — no `sota-numerics.min_alternatives` etc. unless the fixed "at least 2" requirement (locked by CONTEXT.md's "Minimum count") needs to become configurable later.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `gsd-tools.cjs` / `gsd_run` | Config reads, capability install, gate dispatch | ✓ | gsd-core 1.10.0 (confirmed via `~/.claude/gsd-core` VERSION file) | — |
| Python 3 | `check-alternatives.py` (if Python chosen over bash) | Assumed present (already a project-accepted dependency, used by `beads/scripts/sync.py`) | not directly probed this session | POSIX `sh`/`bash` regex/awk if Python unavailable — no new dependency either way |
| `sha256sum` / `shasum` | `capability-auto-install.sh` bundle-hash | Already handled by existing vendored script's own portable fallback | — | — (script already handles both, and exits silently if neither present) |

No missing dependencies with no fallback — every piece of tooling this phase needs is either already present in this repo or has a documented, already-implemented fallback.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None (stdlib-only bash smoke tests — N5 constraint) [VERIFIED: /home/dd/projects/gsd-beads/ponytail-everywhere/tests/test-session-start.sh:1-2 comment "Stdlib-only smoke test (N5): no framework, no fixtures dir"] |
| Config file | none |
| Quick run command | `bash ponytail-everywhere/tests/test-session-start.sh` (pattern to replicate for `sota-numerics/tests/`) |
| Full suite command | Same — no separate quick/full split exists in this repo's test convention |

### Phase Requirements → Test Map

No `REQUIREMENTS.md` entries exist for this phase (Requirements: TBD). Test coverage instead maps to CONTEXT.md's locked decisions:

| Decision | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-01/D-06/D-07/D-09/Min-count | `check-alternatives.py` blocks a PLAN.md with <2 cited+dated alternatives, no ranked criterion | unit (stdlib) | `python3 -c "..."` or a `tests/test_check_alternatives.py` mirroring `beads/tests/test_sync.py`'s fixture pattern | ❌ Wave 0 |
| D-03 | `check-alternatives.py` accepts the literal "N/A — no mechanism choice" exemption text | unit | same file | ❌ Wave 0 |
| D-10 | `sota-numerics.enabled` defaults `true` at fresh install | smoke | `bash tests/test-session-start.sh` scratch-dir case (no config present → default true) | ❌ Wave 0 |
| Pattern 3 (multi-plan coverage) | A phase with 2+ `*-PLAN.md` files — gate must check ALL, not just the first-matched | integration/fixture | new fixture pair mirroring `beads/tests/fixtures/plan-wave-a.md` + `plan-wave-b.md` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** run `check-alternatives.py`/`.sh`'s own smoke test directly.
- **Per wave merge:** full `tests/` directory for the plugin.
- **Phase gate:** the dogfood install (D-04) against this repo's own next real phase plan is the highest-value end-to-end check — treat it as a manual UAT step, not an automated test.

### Wave 0 Gaps

- [ ] `sota-numerics/tests/test-check-alternatives.{sh,py}` — covers D-01/D-03/D-06/D-07/D-09/Min-count
- [ ] `sota-numerics/tests/fixtures/` — at least one compliant PLAN.md fixture, one non-compliant, one exempt (D-03), one multi-plan-phase pair (Pattern 3)
- [ ] `sota-numerics/tests/test-session-start.sh` — mirror `ponytail-everywhere`'s scratch-dir pattern for D-10's default-true behavior
- [ ] No framework install needed — stdlib only, consistent with N5

## Security Domain

`security_enforcement: true` (confirmed in `.planning/config.json`, `security_asvs_level: 1`, `security_block_on: "high"`). [VERIFIED: /home/dd/projects/gsd-beads/.planning/config.json:38-40]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface in this phase |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | Yes | The `command-exit-zero` gate's `command` string must not interpolate untrusted content — `${PHASE_DIR}`/`${PHASE_NUMBER}` are gsd-core-controlled path segments already validated by `findPhaseArtifact`'s own path-safety checks elsewhere in the router, but the capability's own script (`check-alternatives.py`) must not `eval`/shell-out on content it reads FROM the PLAN.md body (citation URLs, dated text) — treat all PLAN.md content as untrusted input when parsing, never pass it through a shell |
| V6 Cryptography | No | — |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command injection via a malformed `command` string in `capability.json` (e.g. a plan's title/path containing shell metacharacters reaching the interpolated `${PHASE_DIR}`) | Tampering | `interpolate()` only substitutes three named placeholders (`PHASE_NUMBER`/`PHASE_DIR`/`PHASE_REQ_IDS`) via a fixed regex, not arbitrary string interpolation — the existing evaluator already mitigates this; do not add ad-hoc `${...}` substitution inside `check-alternatives.py` itself when parsing plan content [VERIFIED: ~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs:41-53] |
| ReDoS in citation/date-validation regex (Pattern 2(b)'s heuristic) | Denial of Service | Use simple, bounded regex (anchored, no nested quantifiers) for URL/date matching; the gate has a `timeout` field (default 30s) as a backstop regardless |
| `CAP_ID` argument injection into `capability-auto-install.sh` | Tampering | Already mitigated by the existing vendored script's own regex guard `[[ "$CAP_ID" =~ ^[a-z][a-z0-9-]*$ ]] || exit 0` — `sota-numerics` matches this pattern cleanly, no change needed [VERIFIED: /home/dd/projects/gsd-beads/ponytail-everywhere/hooks/capability-auto-install.sh:13-16] |

## Sources

### Primary (HIGH confidence — read verbatim this session)

- `~/.claude/gsd-core/workflows/plan-phase.md` (full file, 1506 lines) — §5.6 (plan:pre contribution rendering), §10 (checker spawn, no contribution rendering), §13a-13e (decision-coverage gate, STATE.md update, commit, plan:post gate dispatch)
- `~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs` (full file, 203 lines) — predicate kind table, interpolation contract, `command-exit-zero`/`artifact-frontmatter-equals` implementations
- `~/.claude/gsd-core/bin/lib/loop-host-contract.cjs` (full file) — per-point `agentRoles` contract, confirming `"checker"` validity at the `plan` step
- `~/.claude/gsd-core/bin/lib/check-command-router.cjs:840-898` — `findPhaseArtifact`/`readFrontmatter` deps backing the predicate evaluator
- `~/.claude/gsd-core/bin/lib/capability-registry.cjs` (grep passes) — `gap-analysis`'s core-only `check.query` gate, confirming project-local capabilities cannot use `check.query`; exhaustive `"id"` grep confirming no `sota-numerics` collision
- `~/.claude/gsd-core/bin/lib/capability-validator.cjs:2287,2365-2387` — `contrib.into` validated against `agentRoles`
- `/home/dd/projects/gsd-beads/.gsd/capabilities/beads/capability.json`, `.gsd/capabilities/ponytail/capability.json`, `.gsd/capabilities/beads/GSD-CORE-PATCH.md` — structural analogues, read in full
- `/home/dd/projects/gsd-beads/ponytail-everywhere/hooks/capability-auto-install.sh`, `session-start.sh`, `hooks.json`, `.claude-plugin/plugin.json` — reusable auto-install/hook pattern, read in full
- `/home/dd/projects/gsd-beads/.gsd/capabilities/beads/skills/beads-sync/SKILL.md` — confirms `beads-sync` (the `plan:post` STEP precedent) is a manually-invoked skill, not workflow-dispatched
- `/home/dd/projects/gsd-beads/.planning/phases/11-sota-numerics-capability-plugin-sota-efficiency-numerical-st/11-CONTEXT.md` (full file) — locked decisions, discretion, deferred ideas
- `/home/dd/projects/gsd-beads/.planning/config.json` — `nyquist_validation: true`, `security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: "high"`
- `/home/dd/projects/gsd-beads/.planning/REQUIREMENTS.md` — N5 constraint (Python 3 stdlib / `bd` binary only)

### Secondary (MEDIUM confidence)

- Existing `*-PLAN.md` samples (`10.1-02-PLAN.md`, Phase 10's two-plan directory) — used to confirm multi-plan-per-phase precedent exists on disk, not exhaustively cross-checked against every historical phase

### Tertiary (LOW confidence / unresolved)

- Open Question 1 (gate-subprocess `CLAUDE_PLUGIN_ROOT` availability) — not traced this session; flagged explicitly rather than guessed

## Metadata

**Confidence breakdown:**
- Gate/dispatch mechanism findings (the phase's central risk): HIGH — every claim traces to a specific file+line read this session, several cross-checked by grep against the FULL gsd-core workflow tree (not just the one workflow file)
- Predicate schema (`command-exit-zero` field names, `equals` strictness): HIGH — read the evaluator source directly, not inferred
- Exact frontmatter/config field naming for the new capability: MEDIUM — genuinely open (Claude's Discretion per CONTEXT.md), no existing precedent to verify against
- Auto-install/marketplace packaging: HIGH — directly copies an already-working, already-tested pattern with zero required changes

**Research date:** 2026-08-17
**Valid until:** Tied to the installed `gsd-core` version (1.10.0) — re-verify the `plan:post` dispatch findings (Summary points 1-4) if `gsd-core` is upgraded before this phase is planned/executed, since a future core release could add the missing STEP/contribution dispatch loops this research found absent.
