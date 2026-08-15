# Phase 1: Substrate - Pattern Map

**Mapped:** 2026-08-15
**Files analyzed:** 5 (capability.json, 2x SKILL.md, sync.py, test_sync.py + fixtures)
**Analogs found:** 3 exact/role-match / 5

**Note (greenfield repo):** `gsd-beads` has no source code of its own. All analogs below come
from the real, shipped `gsd-core` v1.10.0 checkout at
`/home/dd/.claude/plugins/marketplaces/gsd-core` (same source RESEARCH.md cites), specifically the
`mempalace` capability — the only shipped `role: "feature"` capability that (a) declares `skills`,
(b) is `onError: skip` throughout, and (c) hooks lifecycle points structurally identical to what
beads needs (`plan:post`, `execute:wave:post`).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.gsd/capabilities/beads/capability.json` | config (manifest) | request-response (declarative, loader-consumed) | `capabilities/mempalace/capability.json` | exact (same envelope shape, same `role: feature`, same `onError: skip` pattern, same `skills[]` + `steps[]` shape) |
| `.gsd/capabilities/beads/skills/beads-sync/SKILL.md` | controller (agent-invoked instruction file) | request-response (config-gate → resolve → act → report) | `skills/gsd-mempalace-capture/SKILL.md` | exact (same 4-step shape: banner → config gate → resolve target → act idempotently → report) |
| `.gsd/capabilities/beads/skills/beads-status/SKILL.md` | controller (agent-invoked instruction file) | batch/event-driven (wave-scoped) | `skills/gsd-mempalace-capture/SKILL.md` | role-match (capture is per-artifact single-shot; beads-status is a wave-scoped batch loop over multiple plans — no shipped skill in gsd-core does batch-over-N-plans, so structure is borrowed, iteration logic is not) |
| `.gsd/capabilities/beads/scripts/sync.py` | service/utility (stdlib parsing + subprocess dispatch) | transform + event-driven | **none** | no analog — no shipped gsd-core capability ships a Python helper script; this is new territory for the ecosystem |
| `.gsd/capabilities/beads/tests/test_sync.py` + fixtures | test | batch | **none** | no analog — no shipped capability ships a `tests/` dir; `unittest` conventions must come from Python stdlib docs, not codebase precedent |

## Pattern Assignments

### `.gsd/capabilities/beads/capability.json` (config, declarative)

**Analog:** `/home/dd/.claude/plugins/marketplaces/gsd-core/capabilities/mempalace/capability.json`

**Envelope + required fields** (lines 1-21):
```json
{
  "id": "mempalace",
  "role": "feature",
  "version": "1.10.0",
  "title": "MemPalace memory",
  "description": "...",
  "tier": "full",
  "requires": [],
  "engines": { "gsd": ">=1.6.0" },
  "runtimeCompat": { "supported": ["*"], "unsupported": [] },
  "skills": ["mempalace-recall", "mempalace-capture"],
  "agents": ["gsd-mempalace-curator"],
  "hooks": []
}
```
Copy verbatim shape for beads: `"id": "beads"`, `"skills": ["beads-sync", "beads-status"]`,
`"agents": []` (no agent needed — RESEARCH.md confirms Phase 1 dispatch is skill-only).
`runtimeCompat` and per-key `description` are non-optional — this analog proves both are always
present in a real shipped manifest, corroborating RESEARCH.md's correction of the PRD's draft.

**Config block pattern** (lines 26-82): every config key is an object with `type`,
`default`, and a mandatory `description` string — including for `enum` type, a `values` array:
```json
"mempalace.memory_mode": {
  "type": "enum",
  "values": ["augment", "kg_backend", "replace"],
  "default": "augment",
  "description": "How MemPalace relates to GSD native memory during recall/capture. ..."
}
```
Beads' `beads.sync_mode` (enum: `authoritative`/`mirror`/`off`) should mirror this exact shape.

**Steps pattern — `onError: skip` on every entry, `when` gated on the master toggle** (lines 83-133):
```json
{
  "point": "plan:post",
  "ref": { "skill": "mempalace-capture" },
  "produces": [],
  "consumes": ["CONTEXT.md"],
  "when": "mempalace.enabled",
  "onError": "skip"
}
```
Beads' `plan:post` step: `ref: {skill: "beads-sync"}`, `consumes: ["PLAN.md"]`,
`produces: ["BEADS.md"]` (per RESEARCH.md's verified skeleton), `when: "beads.enabled"`,
`onError: "skip"` — identical shape to this analog line-for-line.

**No `contributions[]`/`gates[]` needed** — mempalace's `gates: []` (line 171) confirms an empty
array is valid and expected when a feature capability has no ship-blocking checks, consistent with
RESEARCH.md's B1-B6 scope needing none.

---

### `.gsd/capabilities/beads/skills/beads-sync/SKILL.md` (controller, request-response)

**Analog:** `/home/dd/.claude/plugins/marketplaces/gsd-core/skills/gsd-mempalace-capture/SKILL.md`

**Frontmatter + STOP-reading banner pattern** (lines 1-21):
```markdown
---
name: gsd-mempalace-capture
description: "File a phase artifact into MemPalace; mirror decision facts into its temporal KG"
argument-hint: "[CONTEXT.md|PLAN.md|SUMMARY.md]"
allowed-tools:
  - Read
  - Bash
---

**STOP -- DO NOT READ THIS FILE. You are already reading it. ... Begin executing Step 0 immediately.**

## Step 0 -- Banner

**Before ANY tool calls**, display this banner:
\`\`\`
GSD > MEMPALACE CAPTURE
\`\`\`
```
Copy directly: `allowed-tools: [Read, Bash]` (sync.py is invoked via Bash; no Write needed if
sync.py itself does the PLAN.md rewrite) and the banner convention (`GSD > BEADS SYNC`).

**Config gate pattern — the load-bearing B6 fail-open mechanism** (lines 23-41):
```markdown
## Step 1 -- Config Gate

Check whether the MemPalace capability is enabled by reading `.planning/config.json` directly with the Read tool.

1. Read `.planning/config.json` with the Read tool.
2. If the file does not exist, or `config.mempalace` is absent, or `config.mempalace.enabled !== true`, ...: display the disabled message and **STOP**.
3. Otherwise proceed to Step 2.

**Disabled message:**
\`\`\`
GSD > MEMPALACE CAPTURE

MemPalace capture is disabled (mempalace.enabled / mempalace.capture_artifacts).
Nothing was filed; the loop proceeds normally.
\`\`\`

This step is `onError: skip` at `discuss:post` / `plan:post` / `verify:post` -- capture never fails a phase.
```
Beads-sync's Step 1 must be the config gate (`beads.enabled`) PLUS the B6 `command -v bd` check
RESEARCH.md specifies — same two-tier fail-open shape: config-disabled (silent, expected) vs.
`bd`-absent (the one required visible stdout notice + STATE.md append per D-08). This analog
proves the disabled-message convention; the `bd`-absent notice is new content layered on the same
gate mechanism.

**Idempotent action + dedup-first pattern** (lines 53-90, Step 3):
```markdown
## Step 3 -- File verbatim (idempotent)

On any error or timeout, stop and let the phase continue -- capture is best-effort.

1. **Dedup first.** Interactive: `mempalace_check_duplicate` on the artifact's deterministic drawer id. Headless: rely on `mempalace mine`'s content-hash idempotency.
2. **Add the drawer (verbatim).** ...
4. Re-running a phase MUST NOT create duplicate drawers (deterministic ids + `check_duplicate`).
```
Directly maps to B4/B5: beads-sync's Step 3 must resolve-by-`<beads-id>`-first, same "dedup
before create" ordering, same "re-running MUST NOT duplicate" invariant.

**Report pattern** (lines 92-94):
```markdown
## Step 4 -- Report

Print a one-line summary: `Filed <artifact> → <wing>/<room> (<n> KG facts)` or `MemPalace unavailable -- capture skipped`.
```
Beads-sync's final line: `Synced <n> issues, <m> deps → epic <id>` or
`bd unavailable — sync skipped` (the B6/D-08 notice).

**Anti-Patterns footer pattern** (lines 96-101) — copy the numbered-list-of-DO-NOTs convention
verbatim as a section, tailored to beads' own anti-patterns from RESEARCH.md (no title-match
create, no shell-string subprocess calls, no per-task close-wave assumption).

---

### `.gsd/capabilities/beads/skills/beads-status/SKILL.md` (controller, event-driven/batch)

**Analog:** same `gsd-mempalace-capture/SKILL.md` for structure (banner/gate/act/report), but the
**iteration shape differs** — no shipped skill in this gsd-core checkout batches over multiple
plans in one dispatch. RESEARCH.md's own resolved finding (`execute:wave:post` fires once per
wave carrying `WAVE_PLAN_IDS`, a space-separated list) is the authoritative source for Step 2's
loop body; there is no codebase analog to copy the loop mechanics from. Reuse only: frontmatter
shape, banner convention, config-gate Step 1, Anti-Patterns footer convention.

---

### `.gsd/capabilities/beads/scripts/sync.py` (service/utility, transform + event-driven)

**No analog in gsd-core** — zero `.py` files anywhere under
`/home/dd/.claude/plugins/marketplaces/gsd-core` (confirmed via repo-wide find). RESEARCH.md's own
Code Examples section (verified `bd` invocations, `<beads-id>` insertion XML) is the primary
source of truth for this file; N4/N5 (typed argv `subprocess.run([...], shell=False)`, stdlib
only: `re`/`json`/`subprocess`/`argparse`) governs implementation, not any prior project file.

---

### `.gsd/capabilities/beads/tests/test_sync.py` (test, batch)

**No analog in gsd-core** — no `tests/` directory ships inside any capability folder in this
checkout (mempalace's tests, e.g. `tests/mempalace-capture-headless-invocation.test.cjs`, live at
the *gsd-core repo root* `tests/` and are `.cjs`/Node-based, not a pattern beads' Python/stdlib
`unittest` file can or should follow). Use RESEARCH.md's Validation Architecture section directly
(`unittest.mock.patch` on `subprocess.run`, fixture PLAN.md files under `tests/fixtures/`) as the
sole source of truth.

## Shared Patterns

### Config-gate-first (`.planning/config.json` read via Read tool, not Bash)
**Source:** `skills/gsd-mempalace-capture/SKILL.md` lines 23-41
**Apply to:** both `beads-sync` and `beads-status` SKILL.md files — Step 1 in each must be this
gate before any other action.

### `onError: "skip"` + disabled/unavailable message convention
**Source:** `capabilities/mempalace/capability.json` (every `steps[]` entry) +
`skills/gsd-mempalace-capture/SKILL.md` lines 31-38 (disabled-message block)
**Apply to:** `capability.json`'s `steps[]` entries (mechanical `onError: "skip"`) AND both
SKILL.md files' final Report step (human-readable one-liner on skip/disabled — this is the B6/D-08
visible-notice requirement's structural template, though the *content* — `bd`-absent vs.
config-disabled — is new to beads, not copied verbatim).

### Idempotent-dedup-before-create
**Source:** `skills/gsd-mempalace-capture/SKILL.md` lines 53-58, 90
**Apply to:** `beads-sync`'s Step 3 and `sync.py`'s `create-issues` subcommand — resolve identity
first (dedup / `<beads-id>` lookup), only create on confirmed absence.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `.gsd/capabilities/beads/scripts/sync.py` | service/utility | transform + event-driven | No `.py` file exists anywhere in the gsd-core checkout; use RESEARCH.md's verified `bd` CLI invocations and N4/N5 constraints directly |
| `.gsd/capabilities/beads/tests/test_sync.py` + `tests/fixtures/*.md` | test | batch | No `tests/` dir ships inside any capability; gsd-core's own root-level `tests/*.cjs` are Node-based and not a structural fit for a Python stdlib `unittest` file |
| `.gsd/capabilities/beads/skills/beads-status/SKILL.md` iteration logic (Step 2 loop body over `WAVE_PLAN_IDS`) | controller | event-driven/batch | No shipped skill batches over multiple plans in one dispatch; only the outer SKILL.md scaffold (banner/gate/report) has a codebase analog — the wave-iteration body must be derived from RESEARCH.md's `execute-phase.md` citations |

## Metadata

**Analog search scope:** `/home/dd/.claude/plugins/marketplaces/gsd-core/capabilities/*`,
`/home/dd/.claude/plugins/marketplaces/gsd-core/skills/gsd-mempalace-*`
**Files scanned:** `capability.json` (mempalace + spot-checked tdd/graphify for scripts/tests dirs
— none found), 2 SKILL.md files (mempalace-recall skimmed, mempalace-capture read in full),
repo-wide `find -iname "*.py"` (zero results)
**Pattern extraction date:** 2026-08-15
