# Phase 10: ponytail-everywhere capability plugin - Research

**Researched:** 2026-08-17
**Domain:** gsd-core capability plugin authoring (Claude Code plugin + capability.json lifecycle hooks + Claude Code hook events)
**Confidence:** HIGH (mechanism verified by reading gsd-core's own runtime source this session, not inferred from docs)

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** No gsd-core patch. `/gsd-explore` and `/gsd-spec-phase` dispatch zero capability
  lifecycle hooks — only `discuss:{pre,post}`, `plan:{pre,post}`,
  `execute:{pre,wave:pre,wave:post,post}`, `verify:{pre,post}`, `ship:{pre,post}` exist. Reach
  is instead layered: a SessionStart hook (broad, always-on, reaches every stage including
  explore/spec) plus `capability.json` `contributions[]` fragments at the six real lifecycle
  points (targeted, injected into the actual agent prompt). — **Reversibility:** reversible —
  config/content change, no migration.
- **D-02:** Advisory only — no gate. "Did you pick the laziest rung that works" isn't
  mechanically checkable; a diff-size/line-count gate was considered and rejected as a blunt,
  false-positive-prone proxy.
- **D-03:** `ponytail.enabled` defaults to **true** (on by default post-install) — diverges
  from this repo's own `beads.enabled` (default false) convention deliberately. User's
  reasoning: the capability's whole point is "used at all stages"; silently-off-by-default
  would defeat that purpose. — **Reversibility:** reversible — a config default, flippable per
  project via `.planning/config.json`.
- **D-04:** Injected fragments read a configurable `ponytail.level` config key (values:
  `lite`/`full`/`ultra`, default `full`) rather than hardcoding one fixed ladder text —
  mirrors `/ponytail`'s own intensity levels, so a project running `/ponytail ultra` gets
  capability reminders matching that level instead of a mismatched fixed text.
- **D-05:** Stage-tailored fragment text, not one shared generic reminder repeated verbatim at
  every lifecycle point. Each contribution's text matches what the agent at that point is
  actually doing — e.g. the planner gets a "pick the laziest viable task shape" framing, the
  executor gets a "climb the ladder before writing code" framing, the verifier gets a "flag
  unrequested abstractions found" framing. Exact per-point wording and exact stage-to-point
  mapping is Claude's discretion.

### Claude's Discretion

- Exact per-lifecycle-point fragment wording within the stage-tailored framings above (D-05).
- Exact mapping of which of the 10 available lifecycle points (`plan:pre/post`,
  `execute:pre/wave:pre/wave:post/post`, `verify:pre/post`, `ship:pre/post`) receive a
  contribution vs. rely on the SessionStart hook alone.
- Config key naming beyond the two named above (`ponytail.enabled`, `ponytail.level`) — e.g.
  whether any additional keys are needed.
- Capability id / directory name (e.g. `ponytail-everywhere`) and how the
  `<available_agent_types>`-style fragment insertion point (`into: "planner"` /
  `"executor"` / `"verifier"`) is chosen per hook.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. (Phase 11's `sota-numerics` capability is a
separate, already-scoped phase — not a deferred idea, just not this phase's concern.)

</user_constraints>

## Summary

This phase has no `REQUIREMENTS.md` entries (`phase_req_ids` = TBD, confirmed by CONTEXT.md's
canonical_refs) — it is new scope routed directly from `/gsd-explore`. There is no
`<phase_requirements>` table in this document because none were provided.

The phase builds a second Claude Code plugin (`beads-lifecycle` is the first, already shipped)
in the same self-hosted marketplace, using the same two building blocks the `beads` capability
already demonstrates in this exact repo: a `hooks/hooks.json` + `hooks/session-start.sh` pair for
session-wide reach, and a `.gsd/capabilities/<id>/capability.json` for lifecycle-point-targeted
prompt injection. **The single most important finding of this research is that these two
mechanisms have very different, and non-overlapping, actual reach** — verified this session by
reading gsd-core's own workflow markdown (the orchestrator prompts) and its JS resolver source,
not assumed from documentation:

1. **SessionStart hooks reach the top-level orchestrator session only.** They do **not**
   propagate into Task-tool-spawned subagents (`gsd-planner`, `gsd-executor`, `gsd-verifier`).
   This is confirmed both by Claude Code's own hooks documentation and, directly, by the
   installed `/ponytail` plugin's own source comment: `hooks/ponytail-subagent.js` line 4-5
   reads verbatim: *"SessionStart context is parent-thread only and never reaches subagents, so
   without this every Task-spawned agent runs ponytail-unaware (issue #252)."* `/ponytail`
   solves this by **also** registering a `SubagentStart` hook (`hooks/claude-codex-hooks.json`,
   read this session) — this repo's own live system-reminder for this very research task shows
   that hook firing right now. **`ponytail-everywhere` needs the same second hook registration**
   to actually reach `gsd-planner`/`gsd-executor`/`gsd-verifier` — D-01's SessionStart-only
   design reaches the orchestrator's own workflow-control-flow context but not the subagents
   that actually write code, which is where the ladder discipline matters most.
2. **`capability.json` `contributions[]` fragments are functionally delivered at exactly one
   lifecycle point today: `plan:pre` → `into: "planner"`.** Verified by reading
   `plan-phase.md` line 731 (the only literal `kind == "contribution"` injection loop across
   all of `discuss-phase.md`, `plan-phase.md`, `execute-phase.md`, `verify-work.md`, `ship.md`).
   `discuss-phase.md`'s `discuss:pre`/`discuss:post` also generically dispatch contributions (it
   delegates to `references/loop-hook-dispatch.md`), but `/gsd-explore` and `/gsd-spec-phase` —
   the two entry points D-01 calls out by name — do not call `render-hooks` at all, so this is
   moot for them. Every other point (`execute:{wave:pre,wave:post,post}`, `verify:{pre,post}`,
   `ship:{pre,post}`, `plan:post`) calls `render-hooks` and gets a valid `activeHooks` JSON
   array back (the resolver is fully generic — verified in `loop-resolver.cjs`), but the
   **workflow prompt at those points only reads `kind == "gate"` entries** (plus a small number
   of hardcoded named `kind == "step"` skills). A `kind == "contribution"` entry declared at any
   of those points is schema-valid, resolvable, and **silently never read by any agent** — this
   is stated explicitly in `loop-resolver.cjs`'s own source comment (line ~496-499): *"no host
   workflow generically surfaces an arbitrary gate's message at ship:pre / verify:post
   (consumers dispatch on specific capIds / ref.skills)"*. The same non-generic dispatch applies
   to contributions. This is exactly the same class of gap this repo's own `beads` capability
   hit and had to work around with `GSD-CORE-PATCH.md` (for gates/steps at `ship:pre`) — except
   D-01 forbids repeating that patch here, and correctly so: a fragment reminder is not worth a
   core patch.

**Primary recommendation:** register **two** hooks (`SessionStart` for the top-level
orchestrator, `SubagentStart` matched to `gsd-planner|gsd-executor|gsd-verifier` for the actual
subagents) as the real "broad, always-on" reach layer, exactly mirroring the installed
`/ponytail` plugin's own architecture. Declare exactly **one** functional `contributions[]`
entry, at `plan:pre` → `into: "planner"` (the only point proven to inject `fragment.inline` text
into an agent's prompt today). Contributions at the other 9 points may still be declared in
`capability.json` for forward-compatibility/self-documentation (they cost nothing and will
"light up" automatically if gsd-core ever adds generic dispatch there — the beads capability's
own `steps[]` array already does exactly this, declaring entries at points that also don't
generically dispatch), but the plan must not claim they deliver reach today, and the two-hook
mechanism above is what must carry the actual advisory weight at execute/verify/ship stages.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Broad, every-turn reminder (orchestrator) | Claude Code SessionStart hook | — | Fires once per top-level session; injected text persists in the main conversation for every subsequent slash command (`/gsd-explore`, `/gsd-plan-phase`, etc.) run in that session. |
| Broad, every-turn reminder (subagents) | Claude Code SubagentStart hook | — | Fires once per Task-tool spawn; SessionStart text does **not** propagate here (verified, see Summary) — this is the only mechanism that reaches `gsd-planner`/`gsd-executor`/`gsd-verifier` without a gsd-core patch. |
| Targeted, stage-specific reminder text | `capability.json` `contributions[]` at `plan:pre` | SessionStart/SubagentStart (fallback) | Only verified functional prompt-injection point; delivers `fragment.inline` verbatim into the planner's own prompt, richer/longer text than a hook can practically carry. |
| Config (`ponytail.enabled`, `ponytail.level`) | `.planning/config.json` | `capability.json` `config` block (declares schema/defaults) | Single source of truth read by both the hook script (`gsd-tools config-get`) and the capability registry's `when`/`configValues` resolution — same precedence chain the `beads` capability already uses. |
| Marketplace/plugin packaging | `.claude-plugin/marketplace.json` `plugins[]` + a new plugin subdirectory's own `.claude-plugin/plugin.json` | — | Claude Code plugin system, not gsd-core; installs/uninstalls independently of the `beads-lifecycle` plugin already in this marketplace. |

## Standard Stack

No new runtime dependency. This phase produces JSON manifests, one POSIX shell script, and
Markdown fragment files — the exact same artifact types the `beads` capability already ships in
this repo, verified by reading `.gsd/capabilities/beads/capability.json`,
`hooks/hooks.json`, `hooks/session-start.sh`, and `.claude-plugin/marketplace.json` in full this
session.

### Core

| Component | Version/Format | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| `.claude-plugin/plugin.json` (new, in a new subdirectory) | Claude Code plugin manifest schema | Declares the second plugin's identity (`name`, `version`, `description`, `author`, `license`) | Exact schema already proven in this repo's own root `.claude-plugin/plugin.json` [VERIFIED: /home/dd/projects/gsd-beads/.claude-plugin/plugin.json] |
| `hooks/hooks.json` (new, plugin-scoped) | Claude Code hooks manifest | Registers `SessionStart` + `SubagentStart` command hooks | Auto-discovered by Claude Code plugin convention; `beads-lifecycle`'s own `hooks/hooks.json` needs no explicit declaration in `plugin.json` to be picked up [VERIFIED: root plugin.json has no `hooks` key, yet PUB-06 confirms the SessionStart hook ships and works] |
| `hooks/session-start.sh` (new) | POSIX shell | Emits the ladder-discipline reminder to stdout for context injection | Same pattern as `beads-lifecycle`'s own `hooks/session-start.sh` [VERIFIED: /home/dd/projects/gsd-beads/hooks/session-start.sh, read in full] |
| `.gsd/capabilities/ponytail/capability.json` (new) | gsd-core capability manifest schema | Declares `config`, and one functional `contributions[]` entry at `plan:pre` | Exact schema proven by `.gsd/capabilities/beads/capability.json` [VERIFIED: read in full this session] |
| `.gsd/capabilities/ponytail/fragments/*.md` (new) | Markdown | Fragment body referenced by `fragment.path` | Same pattern as `.gsd/capabilities/beads/fragments/recall-pointer.md` [VERIFIED: read in full this session] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SessionStart + SubagentStart dual-hook | SessionStart only (as D-01 literally names) | Simpler, but demonstrably fails to reach `gsd-executor`/`gsd-planner`/`gsd-verifier` — the exact subagents where lazy-ladder discipline is most relevant. Confirmed by the real `/ponytail` plugin's own bugfix (issue #252) for identically-shaped gap. |
| SubagentStart matcher via native `matcher` field | Custom stdin-parsing JS/shell (what `/ponytail` itself does) | `/ponytail` needs a custom matcher because it ships cross-runtime (Cursor, Codex, Windsurf, …) and wants opt-in env-var scoping across all of them. `ponytail-everywhere` is Claude-Code/gsd-core-specific — the native `hooks.json` `"matcher"` field (regex against `agent_type`, confirmed by Claude Code hooks docs and by this repo's own `SessionStart` matcher `"startup\|resume\|clear\|compact"`) is sufficient and far simpler: `"matcher": "gsd-planner\|gsd-executor\|gsd-verifier"`. |
| One `contributions[]` entry at `plan:pre` | `contributions[]` entries at all 10 available points, believed to be delivered everywhere | Would ship a capability.json whose 9 non-`plan:pre` entries are inert today (confirmed via source read) — a false-confidence trap if not disclosed. Declaring them anyway (as forward-compatible no-ops, like `beads`'s own `steps[]` array already does for some points) is fine; claiming they deliver reach today is not. |

**Installation:** none — no `npm install`. Files are authored directly; the capability is
activated via `gsd-tools capability install --scope project --yes` (the same manual step
already documented for `beads` — PROJECT.md/STATE.md, PUB-03 decision, [VERIFIED: read
`.planning/PROJECT.md` and `.planning/STATE.md` this session]), and the plugin via
`/plugin marketplace add` + `/plugin install` (same as PUB-02/PUB-09's proven round trip).

**Version verification:** `gsd-core` VERSION on this machine is `1.10.0`
[VERIFIED: /home/dd/.claude/gsd-core/VERSION, read this session]. Recommend
`"engines": { "gsd": ">=1.10.0" }` (the `beads` capability declares `>=1.6.0`, written when that
was current — [VERIFIED: .gsd/capabilities/beads/capability.json]).

## Package Legitimacy Audit

**N/A — this phase installs no external packages.** No `npm install`, `pip install`, or
`cargo add` of any kind. All artifacts (`plugin.json`, `hooks.json`, `capability.json`,
`session-start.sh`, fragment `.md` files) are authored directly, in the same pattern as the
`beads` capability already in this repository. The Package Legitimacy Gate protocol is not
triggered.

## Architecture Patterns

### System Architecture Diagram

```text
┌─────────────────────────────── Claude Code top-level session ───────────────────────────────┐
│                                                                                                │
│  SessionStart event (fires once: startup/resume/clear/compact)                                │
│         │                                                                                      │
│         ▼                                                                                      │
│  hooks/session-start.sh  ──►  gsd-tools config-get ponytail.enabled --default true             │
│         │                     gsd-tools config-get ponytail.level   --default full             │
│         ▼                                                                                      │
│  stdout ──► injected as context into the MAIN conversation only                                │
│         │   (reaches /gsd-explore, /gsd-spec-phase, /gsd-discuss-phase, and the orchestrator    │
│         │    control-flow portions of /gsd-plan-phase, /gsd-execute-phase, /gsd-verify-work,    │
│         │    /gsd-ship — but NOT any Task-tool subagent spawned from within them)               │
│                                                                                                │
│  ── orchestrator dispatches a subagent (Task tool) ──────────────────────────────────────►┐    │
│                                                                                              │   │
└──────────────────────────────────────────────────────────────────────────────────────────┼───┘
                                                                                              │
┌──────────────────────────────── each Task-tool subagent's OWN context ────────────────────┼───┐
│                                                                                              ▼   │
│  SubagentStart event (fires once per spawn; matcher: gsd-planner|gsd-executor|gsd-verifier)      │
│         │                                                                                        │
│         ▼                                                                                        │
│  hooks/session-start.sh (same script, reused)  ──►  same config-get calls                        │
│         ▼                                                                                        │
│  stdout ──► injected into THIS subagent's own transcript (additionalContext)                     │
│                                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────── gsd-core plan:pre orchestration (plan-phase.md) ──────────────────────┐
│                                                                                                     │
│  PLAN_PRE_HOOKS_JSON = gsd_run loop render-hooks plan:pre --raw                                   │
│         │                                                                                          │
│         ▼                                                                                          │
│  for each activeHooks[] entry where kind=="contribution" AND into=="planner":                      │
│      inject fragment.inline VERBATIM into the gsd-planner subagent's prompt   ◄── ponytail's ONE   │
│                                                                                    functional entry │
│                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────── execute:{wave:pre,wave:post,post} / verify:{pre,post} / ship:{pre,post} ─────────┐
│                                                                                                      │
│  {POINT}_HOOKS_JSON = gsd_run loop render-hooks {point} --raw   (resolver returns activeHooks fine) │
│         │                                                                                            │
│         ▼                                                                                            │
│  workflow prompt ONLY reads entries where kind=="gate" (or a few hardcoded named kind=="step")        │
│         │                                                                                            │
│         ▼                                                                                            │
│  a kind=="contribution" entry here is NEVER read by any agent — inert (confirmed via source)          │
│                                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```text
.claude-plugin/
└── marketplace.json                     # add one entry to plugins[]

ponytail-everywhere/                     # new plugin subdirectory (sibling to repo root, which
│                                         # is itself the beads-lifecycle plugin's source)
├── .claude-plugin/
│   └── plugin.json                      # new plugin manifest — name: "ponytail-everywhere"
└── hooks/
    ├── hooks.json                       # SessionStart + SubagentStart registrations
    └── session-start.sh                 # shared reminder-emitting script (both events point here)

.gsd/capabilities/ponytail/              # new capability directory — id: "ponytail"
├── capability.json                      # config schema + 1 functional contribution (plan:pre)
└── fragments/
    └── planner-ladder.md                # fragment.path referenced by the plan:pre contribution
```

**Directory-name / id-vs-name precedent (verified, not assumed):** the existing plugin's
`plugin.json` declares `"name": "beads-lifecycle"` while its capability.json declares
`"id": "beads"` and config keys `"beads.enabled"`, `"beads.sync_mode"`, etc. — plugin name and
capability id are **already different strings in this exact repo**
[VERIFIED: `.claude-plugin/plugin.json` vs `.gsd/capabilities/beads/capability.json`]. This
directly supports naming the plugin `ponytail-everywhere` (matches the phase title, human-facing)
while giving the capability `"id": "ponytail"` (matches the locked config keys `ponytail.enabled`
/ `ponytail.level` exactly, no key/id mismatch) — consistent with the existing precedent and with
the collision-check rule below.

### Pattern 1: Dual hook registration (SessionStart + SubagentStart) for full reach

**What:** Register the *same* reminder-emitting script under two Claude Code hook events in one
`hooks.json`.
**When to use:** Any plugin whose advisory content needs to reach both the top-level orchestrator
session and Task-tool-spawned subagents — exactly this phase's requirement.
**Example (verified from the installed `/ponytail` plugin's own shipped hooks file):**
```json
// Source: /home/dd/.claude/plugins/marketplaces/ponytail/hooks/claude-codex-hooks.json (read this session)
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          { "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"" }
        ]
      }
    ],
    "SubagentStart": [
      {
        "matcher": "gsd-planner|gsd-executor|gsd-verifier",
        "hooks": [
          { "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"" }
        ]
      }
    ]
  }
}
```
This repo's own `beads-lifecycle` `hooks/hooks.json` registers `SessionStart` with an empty-string
matcher (`"matcher": ""`, meaning "always") [VERIFIED: `hooks/hooks.json`, quoted in full above in
Sources]. A ponytail-everywhere `SessionStart` entry can copy that pattern (or add the
`startup|resume|clear|compact` matcher `/ponytail` itself uses — functionally the same set of
SessionStart sub-reasons).

### Pattern 2: Single functional `contributions[]` entry at `plan:pre`

**What:** One `contributions[]` array entry, `point: "plan:pre"`, `into: "planner"`.
**When to use:** The only lifecycle point where a capability's `fragment.inline`/`fragment.path`
text is proven to reach an agent's prompt verbatim.
**Example:**
```json
// Source: .gsd/capabilities/beads/capability.json, adapted to this phase's shape
// (beads' own single contribution is at exactly this point — read verbatim this session)
{
  "point": "plan:pre",
  "into": "planner",
  "produces": [],
  "consumes": [],
  "fragment": { "path": "fragments/planner-ladder.md" },
  "when": "ponytail.enabled",
  "onError": "skip"
}
```
The `when` field is a **single dotted config key resolved for truthiness** — not an arbitrary
boolean expression [VERIFIED: `loop-resolver.cjs` `isActive()`, lines 126-135, read this
session: `"when` present but not a non-empty string → malformed → INACTIVE"` /
`_resolveActivationValue(when, config, cwd, registry)`]. `ponytail.level`'s three-way value
(`lite`/`full`/`ultra`) **cannot** be used as a `when` predicate directly — instead declare it via
`configValues` and let the fragment text branch on the resolved value:
```json
"configValues": { "level": "ponytail.level" }
```
This is the exact mechanism the `security` capability already uses to surface
`security_asvs_level`/`security_block_on` to the planner [VERIFIED: `plan-phase.md` line 731,
`loop-resolver.cjs` `resolveConfigValues()`, lines 168-192]. The fragment's own Markdown text then
instructs the planner: *"Use the `full` block below unless `ponytail.level` resolved above says
otherwise."* — same technique `security`'s contribution uses for its two resolved config values.

### Anti-Patterns to Avoid

- **Assuming `contributions[]` reach at `execute:*`/`verify:*`/`ship:*`:** schema-valid, resolver-
  returns it, zero agents ever read it. Do not write planner tasks that treat these as delivering
  the "climb the ladder" / "flag unrequested abstractions" reminders D-05 describes for
  execute/verify — that job belongs to the SubagentStart hook (Pattern 1), not a dormant
  contribution.
- **A patch to gsd-core's workflow `.md` files to make contributions generic everywhere:**
  explicitly forbidden by D-01, and this repo's own `GSD-CORE-PATCH.md` documents exactly how
  heavyweight that precedent is (a machine-local patch file, an upstream issue, a drift-detection
  skill step). Not worth it for advisory text.
- **One shared generic fragment string repeated at every point:** explicitly rejected by D-05.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reading `.planning/config.json` from a shell hook | Custom `jq`/`grep` JSON parsing of `.planning/config.json` | `gsd-tools config-get <key.path> --default <value>` | Already the canonical CLI seam; confirmed working this session (`config-get ponytail.level --default full` → `"full"`) and handles the same precedence chain (`config.json` → capability default → hardcoded fallback) every other capability relies on. |
| Detecting whether the config-driven contribution should fire | Custom boolean parsing inside the fragment or hook script | `when: "ponytail.enabled"` on the `contributions[]`/hook entries | The registry already fails safely (missing/malformed `when` → inactive) — reimplementing this in a shell script duplicates logic the resolver already owns and risks drifting out of sync with the four-level precedence `resolveConfigKey` implements. |
| Detecting which agent type a `SubagentStart` fired for | Custom stdin JSON parsing (regex against `agent_type`) as `/ponytail` itself does | Native `hooks.json` `"matcher"` field | `/ponytail`'s custom JS parser exists because it needs cross-runtime + opt-in env-var scoping. Claude-Code-native `matcher` regex against `agent_type` is documented, simpler, and already proven by this repo's own `SessionStart` matcher usage. |
| Config-key collision detection across capabilities | A manual grep-every-manifest check repeated by hand each time | Rely on `capability-loader.cjs`'s built-in collision guard | Verified: a capability that "owns config key ... already owned by another capability" is **skipped entirely** at load time [VERIFIED: `capability-loader.cjs` line 576] — the loader itself is the source of truth, not a one-time manual audit (though the manual audit below still confirms no *pre-existing* collision before authoring). |

**Key insight:** every piece of plumbing this phase needs (config read, activation-truthiness,
collision safety) already exists as a proven seam in gsd-core or the Claude Code hooks system —
the only genuinely new work is the fragment *text* and the two manifest files that wire it up.

## Common Pitfalls

### Pitfall 1: Believing D-01's "six real lifecycle points" delivers reach uniformly

**What goes wrong:** A plan/executor writes `contributions[]` entries at all of `plan:post`,
`execute:wave:pre`, `execute:wave:post`, `execute:post`, `verify:pre`, `verify:post`, `ship:pre`,
`ship:post`, believing each is "injected into the actual agent prompt" per D-01's own wording, and
declares the phase done once `capability.json` validates and `gsd_run loop render-hooks <point>
--raw` returns the entry in `activeHooks`.
**Why it happens:** `render-hooks` genuinely does return the entry — the resolver is fully
generic across all 12 canonical points (verified: `loop-resolver.cjs` processes `contributions`
identically regardless of `point`). The registry-level success masks the workflow-prompt-level
silence.
**How to avoid:** Treat `render-hooks` returning the entry as necessary but not sufficient. The
sufficient check is: does the *workflow markdown* at that exact point contain an explicit
`kind == "contribution"` read-and-inject instruction? Verified present only at `plan-phase.md`
line 731 (`plan:pre` → `into: "planner"`) and, generically via delegation, at `discuss-phase.md`'s
`discuss:pre`/`discuss:post` (moot here — `/gsd-explore`/`/gsd-spec-phase` never call
`render-hooks` at all).
**Warning signs:** A plan task whose verification step is only "capability.json validates" or
"`render-hooks` shows the entry active" rather than "the executor subagent's own transcript shows
the reminder text."

### Pitfall 2: SessionStart-only reach silently excludes every subagent

**What goes wrong:** The SessionStart hook fires, prints the ladder reminder, the orchestrator
sees it — and everyone assumes `gsd-executor`/`gsd-planner`/`gsd-verifier` subagents saw it too,
because "the session" is loosely understood as "everything in this run." They did not.
**Why it happens:** SessionStart's injected context is scoped to the main conversation thread;
each Task-tool subagent spawn is a **separate context** that only sees hooks registered under
`SubagentStart` (or the one proven `plan:pre` contribution). This is not a gsd-core-specific
quirk — it is Claude Code's own hook architecture, and the real `/ponytail` plugin had to fix
this exact bug (issue #252) by adding a second hook.
**How to avoid:** Register `SubagentStart` alongside `SessionStart` (Pattern 1). Verify by reading
an actual executor subagent's transcript/SUMMARY.md context, not just the orchestrator's own
output.
**Warning signs:** UAT/verification only checks the top-level session's visible output; no check
inspects what an actual `gsd-executor` Task invocation received as `additionalContext`.

### Pitfall 3: Using `ponytail.level` directly as a `when` predicate

**What goes wrong:** Writing `"when": "ponytail.level == 'ultra'"` or similar, expecting
conditional activation per intensity level.
**Why it happens:** Natural expectation from other enum-typed capability config keys (e.g.
`beads.epic_per`, `beads.sync_mode`) — but those are read via `configValues`, never via `when`.
**How to avoid:** `when` resolves a single dotted key for **truthiness only**
[VERIFIED: `loop-resolver.cjs` `isActive()`]. Use `when: "ponytail.enabled"` (boolean) for
activation, and `configValues: { level: "ponytail.level" }` to surface the enum value into the
fragment/planner context for the fragment's own text to branch on.
**Warning signs:** A capability.json that fails registry load / never activates despite
`ponytail.enabled: true` in config.

### Pitfall 4: Config-key namespace collision with the capability id

**What goes wrong:** Naming the capability `"id": "ponytail-everywhere"` while config keys stay
`ponytail.enabled`/`ponytail.level` (as locked by D-03/D-04) — a mismatch that works today (no
enforced id-prefix rule found in `capability-loader.cjs`) but breaks the established
id-matches-config-prefix convention every other capability in this repo follows (`id: "beads"` ↔
`beads.*`).
**Why it happens:** CONTEXT.md's own example capability id is `ponytail-everywhere`, and the
config keys were locked separately as `ponytail.*` — nothing forces them to agree.
**How to avoid:** Set `"id": "ponytail"` in `capability.json` (plugin `name` stays
`ponytail-everywhere`) — see the Recommended Project Structure precedent note above.
**Warning signs:** none functional (no collision, no load failure) — this is a consistency/
maintainability finding, not a hard blocker; flagging it so the planner makes the choice
deliberately rather than by accident.

## Code Examples

### `hooks/hooks.json` (new plugin subdirectory)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"", "type": "command" }
        ]
      }
    ],
    "SubagentStart": [
      {
        "matcher": "gsd-planner|gsd-executor|gsd-verifier",
        "hooks": [
          { "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"", "type": "command" }
        ]
      }
    ]
  }
}
```
`"matcher": ""` for `SessionStart` copies this repo's own working `hooks/hooks.json` verbatim
shape [VERIFIED: `hooks/hooks.json`, quoted in full in Sources]. `${CLAUDE_PLUGIN_ROOT}` is the
existing plugin-root env var this repo's own `session-start.sh` already relies on
[VERIFIED: `hooks/session-start.sh` line 4: `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"`].

### `hooks/session-start.sh` (skeleton — config-driven, fail-open)

```bash
#!/usr/bin/env bash
set -u
ENABLED=$(gsd-tools config-get ponytail.enabled --default true 2>/dev/null || echo true)
[ "$ENABLED" = "true" ] || exit 0
LEVEL=$(gsd-tools config-get ponytail.level --default full 2>/dev/null || echo full)
LEVEL=$(printf '%s' "$LEVEL" | tr -d '"')   # config-get returns JSON-quoted strings, e.g. "full"
case "$LEVEL" in lite|full|ultra) ;; *) LEVEL=full ;; esac
# ... emit $LEVEL-specific reminder text to stdout ...
```
Verified this session: `gsd-tools config-get ponytail.level --default full` on this repo's live
config returns the literal string `"full"` (JSON-quoted) — the `tr -d '"'` unquoting step above is
required, not decorative. Mirrors the existing `hooks/session-start.sh`'s fail-open posture
(`|| true`, never a hard error that blocks the session) [VERIFIED: `hooks/session-start.sh`,
`cp ... 2>/dev/null || true` line].

### `capability.json` (new — `.gsd/capabilities/ponytail/capability.json`)

```json
{
  "id": "ponytail",
  "role": "feature",
  "version": "0.1.0",
  "title": "Ponytail lazy-ladder discipline",
  "description": "Advisory-only ladder-discipline reminders (YAGNI, reuse, stdlib/native before dependencies, shortest working diff) surfaced at plan:pre.",
  "tier": "full",
  "requires": [],
  "engines": { "gsd": ">=1.10.0" },
  "runtimeCompat": { "supported": ["*"], "unsupported": [] },
  "skills": [],
  "agents": [],
  "hooks": [],
  "config": {
    "ponytail.enabled": {
      "type": "boolean",
      "default": true,
      "description": "Master toggle for the ponytail lazy-ladder capability. Defaults true (D-03) — diverges from beads.enabled's default-false."
    },
    "ponytail.level": {
      "type": "enum",
      "values": ["lite", "full", "ultra"],
      "default": "full",
      "description": "Intensity of injected ladder-discipline reminders, mirrors /ponytail's own levels (D-04)."
    }
  },
  "steps": [],
  "contributions": [
    {
      "point": "plan:pre",
      "into": "planner",
      "produces": [],
      "consumes": [],
      "fragment": { "path": "fragments/planner-ladder.md" },
      "when": "ponytail.enabled",
      "configValues": { "level": "ponytail.level" },
      "onError": "skip"
    }
  ],
  "gates": []
}
```
`"config"` block shape, `"steps"`/`"gates"` empty-array conventions, and the top-level field set
(`id`, `role`, `version`, `title`, `description`, `tier`, `requires`, `engines`, `runtimeCompat`,
`skills`, `agents`, `hooks`) are copied field-for-field from
`.gsd/capabilities/beads/capability.json`, read in full this session (quoted in Sources below).

### `.claude-plugin/marketplace.json` — new `plugins[]` entry

```json
{
  "name": "ponytail-everywhere",
  "source": "./ponytail-everywhere",
  "description": "Advisory-only lazy-ladder discipline reminders wired into gsd-core's plan/execute/verify/ship lifecycle."
}
```
Appended to the existing `plugins[]` array alongside the current single entry
(`{"name": "beads-lifecycle", "source": "./", ...}` [VERIFIED: `.claude-plugin/marketplace.json`,
quoted in full below]). `"source": "./ponytail-everywhere"` follows the documented Claude Code
marketplace convention of a plugin subdirectory containing its own `.claude-plugin/plugin.json`
[CITED: web — code.claude.com/docs/en/plugin-marketplaces and community write-ups on multi-plugin
marketplace layout, LOW/MEDIUM confidence per `classify-confidence --provider websearch` → LOW;
corroborated at HIGH confidence by this repo's own working precedent: the existing entry's
`"source": "./"` already proves "source points at a directory containing `.claude-plugin/plugin.json`"
is the mechanism Claude Code actually uses for *this* marketplace].

## State of the Art

Not applicable in the conventional "framework version" sense — there is no external framework
here to go stale. The one genuinely time-sensitive fact is gsd-core's own hook/registry
capabilities, which are actively evolving (see `capability-registry.cjs`'s in-source ADR
references — ADR-857, ADR-1244, ADR-2008, #2009, #2493, etc., all touching exactly the
contribution/gate dispatch mechanism this research investigated). **Re-verify the "contributions
only reach `plan:pre`" finding if this phase is planned more than ~2-4 weeks after this research
date** — a gsd-core update could add generic contribution dispatch at other points (the resolver
already supports it structurally; only the workflow-prompt-side consumption is missing today).

**Deprecated/outdated:** none identified — the `beads` capability's own `GSD-CORE-PATCH.md`
documents a since-superseded gap (`ship:pre` gate/step dispatch), already resolved for that repo
via a local patch; irrelevant to this phase since D-01 forbids repeating that approach.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `"source": "./ponytail-everywhere"` (a relative subdirectory path) is the correct `marketplace.json` convention for a second co-located plugin, as opposed to some other required shape (e.g. an object form). | Code Examples — marketplace.json entry | LOW — this repo's own existing entry already proves relative-path `source` resolution works for this marketplace; worst case the executor discovers the exact required shape via `claude plugin validate . --strict` (the same gate PUB-01/PUB-09 already use) and self-corrects before shipping. |
| A2 | `hooks.json`'s `SubagentStart` `"matcher"` field filters natively on the `agent_type` string reported by Claude Code (e.g. `gsd-planner`), without needing the custom stdin-JSON-parsing approach `/ponytail` itself uses. | Pattern 1 / Don't Hand-Roll | MEDIUM — if the native matcher does not actually filter on `agent_type` (only WebSearch-cited, not read from Claude Code's own hooks.json JSON-schema source), the hook would either fire for every subagent type (noisy but harmless, since content is advisory) or fail to fire at all (silently losing subagent reach) — either way, recoverable by falling back to `/ponytail`'s own proven custom-matcher script pattern, which is on-hand as a working reference in this same machine's plugin cache. |

## Open Questions

1. **Should the `SubagentStart` matcher scope to `gsd-planner\|gsd-executor\|gsd-verifier` only, or fire unscoped (reach every subagent type, including e.g. `gsd-codebase-mapper`, research agents like this one, etc.)?**
   - What we know: D-05 explicitly frames the reminder per-role for planner/executor/verifier. The real `/ponytail` plugin defaults to unscoped (fires for every subagent) and only scopes down via opt-in env var (issue #506).
   - What's unclear: whether reminding a codebase-mapper or a research agent (like the one producing this document) with lazy-ladder coding advice is useful noise or harmless noise — it isn't wrong, just possibly irrelevant to non-coding subagent roles.
   - Recommendation: scope to `gsd-planner|gsd-executor|gsd-verifier` (matches D-05's named roles exactly); the planner can widen this trivially later since it's a one-line regex, not an architectural commitment.

2. **Should the 9 non-`plan:pre` `contributions[]` entries be declared in `capability.json` at all, given they are confirmed inert today?**
   - What we know: declaring them costs nothing (schema-valid, `onError: skip`), self-documents D-01's intended stage-tailored mapping (D-05), and will activate automatically if/when gsd-core adds generic dispatch at those points — this is exactly the posture the `beads` capability's own `steps[]` array already takes at some of its declared points.
   - What's unclear: whether declaring inert entries creates false confidence for a future maintainer skimming `capability.json` who assumes "it's in the file, so it must work" (this very research had to read four separate workflow `.md` files and one resolver `.cjs` file to discover otherwise).
   - Recommendation: declare them, but require a prominent code comment in `capability.json` (or an adjacent `NOTES.md`, mirroring `GSD-CORE-PATCH.md`'s own documentation posture) stating plainly which points are functional today and which are forward-compatible placeholders — this is a plan/executor-level decision, not something research should silently resolve.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `gsd-tools` CLI (`gsd-core/bin/gsd-tools.cjs`) | `config-get`, `capability install`, `loop render-hooks` | ✓ | 1.10.0 | — |
| Claude Code plugin/hooks runtime | `SessionStart`/`SubagentStart` hook events | ✓ (proven live — this very research session received a `SubagentStart`-injected ponytail banner) | — | — |
| `bash` | `hooks/session-start.sh` | ✓ | — | — |
| Node.js | `gsd-tools.cjs` itself | ✓ (already required by the existing `beads-lifecycle` plugin) | — | — |

No missing dependencies. Nothing in this phase requires a runtime not already proven working in
this exact repository.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None — this repo has no unit-test framework for capability/plugin manifests; validation is CLI-driven smoke testing, the same posture `beads`'s own Phase 5/8 plans used (`claude plugin validate . --strict`, `/plugin marketplace add`/`install`/`uninstall` round trips). |
| Config file | none |
| Quick run command | `node gsd-core/bin/gsd-tools.cjs loop render-hooks plan:pre --raw` (checks the one functional contribution appears in `activeHooks`) |
| Full suite command | `claude plugin validate . --strict` + a real `/plugin marketplace add` → `/plugin install ponytail-everywhere@gsd-beads` → `/plugin uninstall` round trip (same shape as PUB-09) |

### Phase Requirements → Test Map

No `REQUIREMENTS.md` entries exist for this phase (TBD, confirmed). The planner should instead
derive its own must-have checks directly from D-01 through D-05; a suggested minimal set:

| Check | Behavior | Test Type | Automated Command | File Exists? |
|-------|----------|-----------|-------------------|-------------|
| Plugin installs cleanly | `claude plugin validate` passes for the new plugin | smoke | `claude plugin validate . --strict` | ✅ existing gate, reused |
| SessionStart reaches orchestrator | Reminder text appears in top-level session context on a fresh `SessionStart` | manual/UAT | inspect session transcript after `/plugin install` + new session | ❌ Wave 0 — no automated harness for hook stdout injection exists in this repo |
| SubagentStart reaches a real gsd subagent | Reminder text appears in a `gsd-executor` (or `gsd-planner`) subagent's own transcript | manual/UAT | run any `/gsd-execute-phase` and inspect the spawned executor's context | ❌ Wave 0 — same gap |
| `plan:pre` contribution fires | `activeHooks` from `render-hooks plan:pre --raw` contains the `ponytail` entry when `ponytail.enabled` is true, absent when false | smoke | `gsd-tools loop render-hooks plan:pre --raw` (toggle config between runs) | ✅ CLI already exists, no new file needed |
| Config-key collision | `ponytail.*` keys do not collide with any existing shipped manifest | smoke | grep `.gsd/capabilities/*/capability.json` and `.claude-plugin/marketplace.json` for `ponytail` before authoring (already done this session — no collision found) | ✅ |

### Sampling Rate

- **Per task commit:** `node gsd-core/bin/gsd-tools.cjs loop render-hooks plan:pre --raw`
- **Per wave merge:** `claude plugin validate . --strict`
- **Phase gate:** the full `/plugin marketplace add` → `/plugin install` → `/plugin uninstall`
  round trip, plus manual SubagentStart-transcript inspection (no automated harness exists for
  the latter — flag as a UAT step, not a scripted test).

### Wave 0 Gaps

- No existing automated way to assert hook-injected `additionalContext` reached a specific
  subagent transcript in this repo — this is a manual/UAT check, not a scriptable gap to close;
  do not invent a test framework for it (ponytail's own rule: minimum code that works, no
  scaffolding "for later").

## Security Domain

`workflow.security_enforcement` is `true` in `.planning/config.json` (absent-means-enabled rule
also applies, but it's explicitly `true` here) [VERIFIED: `.planning/config.json`, read this
session].

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | no | No auth surface introduced. |
| V3 Session Management | no | No session/token handling. |
| V4 Access Control | no | No access-control surface. |
| V5 Input Validation | yes (narrow) | `ponytail.level` must be validated against the enum `lite\|full\|ultra` before use in the shell script (an unexpected value must fall back to `full`, never be interpolated unsanitized into any command) — mirrors the `case "$LEVEL" in lite|full|ultra) ;; *) LEVEL=full ;; esac` guard in the Code Examples skeleton above. |
| V6 Cryptography | no | No cryptographic material involved. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Config-value shell injection (a malicious `.planning/config.json` sets `ponytail.level` to a shell-metacharacter-laden string) | Tampering | `gsd-tools config-get` returns a JSON-quoted string; the shell script must whitelist against the 3-value enum (`case` statement) before using the value in any output or command, never `eval`/`source` it. |
| Advisory text mistaken for a security control | (not STRIDE — a design-clarity risk) | D-02 already locks this as advisory-only, no gate — no mitigation needed beyond documentation; do not let a future contributor add gate semantics to `ponytail.*` without a fresh discussion. |

## Sources

### Primary (HIGH confidence — read directly this session)

- `.gsd/capabilities/beads/capability.json` — full JSON quoted above, structural template.
- `.gsd/capabilities/beads/GSD-CORE-PATCH.md` — the one gsd-core-patch precedent this phase avoids repeating.
- `.gsd/capabilities/beads/fragments/recall-pointer.md` — fragment-file convention.
- `hooks/hooks.json`, `hooks/session-start.sh` — existing SessionStart registration pattern.
- `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json` — existing plugin manifest shapes.
- `.planning/notes/two-plugin-capability-design.md` — the `/gsd-explore` session's design rationale, read in full.
- `.planning/PROJECT.md`, `.planning/STATE.md` — PUB-03 capability-install precedent, N1-N5 constraints.
- `/home/dd/.claude/gsd-core/references/loop-hook-dispatch.md` — generic dispatch contract (contribution/step/gate).
- `/home/dd/.claude/gsd-core/workflows/discuss-phase.md` (lines ~290-330, ~410-420) — generic `loop-hook-dispatch.md` delegation at `discuss:pre`/`discuss:post`.
- `/home/dd/.claude/gsd-core/workflows/plan-phase.md` (line 731, 441, 1340-1379) — the ONE functional `kind=="contribution"` injection loop; generic step dispatch; `plan:post` gate-only dispatch.
- `/home/dd/.claude/gsd-core/workflows/execute-phase.md` (lines 641-648, 995-1047, 1198-1230) — `execute:wave:pre`/`wave:post`/`post` gate-only + hardcoded named-step dispatch; no generic contribution consumption.
- `/home/dd/.claude/gsd-core/workflows/verify-work.md` (lines 55-93, 527-531) — `verify:pre`/`post` gate-only + hardcoded named-step dispatch.
- `/home/dd/.claude/gsd-core/workflows/ship.md` (lines 90-129, 220-241, 554-561) — `ship:pre`/`post` gate + step dispatch (note: `ship:pre` generic step dispatch is THIS repo's local `GSD-CORE-PATCH.md`, not native core; `ship:post` generic step dispatch IS native).
- `/home/dd/.claude/gsd-core/bin/lib/loop-resolver.cjs` (lines 1-289, 414-520) — the pure resolver; confirms contributions are structurally generic across all 12 points at the registry level, and that `when` is single-key truthiness only, and `configValues` resolution mechanism.
- `/home/dd/.claude/gsd-core/bin/lib/capability-loader.cjs` (line 576, comment block ~478-499) — config-key collision guard; explicit source comment confirming non-generic gate/contribution dispatch at `ship:pre`/`verify:post`.
- `/home/dd/.claude/gsd-core/bin/lib/capability-registry.cjs` (lines 683-697, 2417-2439, and `"into":` grep across the file) — core-bundled capabilities' own `contributions[]` usage (`claude_orchestration` at `execute:wave:pre` → `into: executor`; `mempalace` at `discuss:pre` → `into: orchestrator` and `execute:wave:post` → `into: verifier`), used as corroborating evidence that these `into` targets exist in the schema even where the workflow prompt doesn't yet generically consume them.
- `/home/dd/.claude/gsd-core/references/agent-contracts.md` (lines 13, 14, 24) — exact subagent type strings `gsd-planner`, `gsd-executor`, `gsd-verifier`.
- `/home/dd/.claude/gsd-core/references/planning-config.md`, `/home/dd/.claude/gsd-core/references/gates.md` — config-field reference, confirms no dedicated capability-authoring doc exists (source code is the ground truth here).
- `/home/dd/.claude/gsd-core/VERSION` — `1.10.0`.
- `/home/dd/.claude/plugins/marketplaces/ponytail/skills/ponytail/SKILL.md` — full level table (lite/full/ultra), quoted verbatim in the system prompt and re-confirmed by direct file read.
- `/home/dd/.claude/plugins/marketplaces/ponytail/hooks/claude-codex-hooks.json` — dual SessionStart+SubagentStart+UserPromptSubmit hook registration, used as Pattern 1's template.
- `/home/dd/.claude/plugins/marketplaces/ponytail/hooks/ponytail-subagent.js` (lines 1-11) — verbatim source comment confirming SessionStart-does-not-reach-subagents (issue #252), and the opt-in `PONYTAIL_SUBAGENT_MATCHER` scoping pattern (issue #506).
- Live CLI verification: `node gsd-core/bin/gsd-tools.cjs config-get beads.enabled --default false` → `true`; `config-get ponytail.level --default full` → `"full"`; `capability`/`loop` subcommand listings.
- `find` over `.claude/plugins/*` and the repo tree — confirmed zero pre-existing `ponytail.*` occurrences anywhere in this repo's shipped manifests (no collision risk today).

### Secondary (MEDIUM confidence)

- Claude Code hooks documentation (`code.claude.com/docs/en/hooks`), via WebSearch — SessionStart vs. SubagentStart scope, matcher-on-agent_type behavior. Corroborated by the primary-source `/ponytail` code comment above, raising effective confidence to HIGH for the core claim (SessionStart does not reach subagents) even though the search itself is MEDIUM/LOW per the confidence-classifier seam.

### Tertiary (LOW confidence)

- Community blog posts on multi-plugin `marketplace.json` subdirectory layout (`dev.to`, `alexop.dev`, etc.), via WebSearch — `classify-confidence --provider websearch` returned `LOW`. Used only to corroborate a pattern already independently evidenced by this repo's own working `"source": "./"` entry; the subdirectory-source claim itself should be re-confirmed at execution time via `claude plugin validate . --strict` before considering it load-bearing.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no external packages; every artifact type is directly modeled on this repo's own already-shipped, already-validated `beads` capability.
- Architecture (hook/contribution reach mechanism): HIGH — verified by reading gsd-core's own JS resolver and every relevant workflow markdown file this session, plus corroborated by a second independent primary source (the installed `/ponytail` plugin's own bugfix comment).
- Pitfalls: HIGH — each pitfall is backed by an exact file+line citation, not inference.
- Marketplace subdirectory layout for a second plugin: MEDIUM — best-evidenced by this repo's own existing entry shape plus community documentation; not independently tested by actually creating a second plugin in this session.

**Research date:** 2026-08-17
**Valid until:** 2026-09-14 (30 days) for the plugin/manifest mechanics; the contribution-dispatch
finding specifically should be spot-re-checked against gsd-core's `VERSION` if planning is
deferred, since `capability-registry.cjs`'s own in-source ADR trail shows this exact area (ADR-857,
ADR-1244, ADR-2008) is under active development.
