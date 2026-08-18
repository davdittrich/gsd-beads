# Phase 10: ponytail-everywhere capability plugin - Pattern Map

**Mapped:** 2026-08-17
**Files analyzed:** 6
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `ponytail-everywhere/.claude-plugin/plugin.json` | config | request-response (manifest) | `.claude-plugin/plugin.json` | exact |
| `ponytail-everywhere/hooks/hooks.json` | config | event-driven | `hooks/hooks.json` (SessionStart-only) + `ponytail/hooks/claude-codex-hooks.json` (dual SessionStart+SubagentStart) | role-match, richer analog available |
| `ponytail-everywhere/hooks/session-start.sh` | utility | event-driven | `hooks/session-start.sh` | exact (shape), diverges in content — no self-heal/exec-into-CLI step, this is a pure config-read + static text emitter |
| `.gsd/capabilities/ponytail/capability.json` | config | event-driven | `.gsd/capabilities/beads/capability.json` | exact |
| `.gsd/capabilities/ponytail/fragments/planner-ladder.md` | utility (prompt fragment) | transform | `.gsd/capabilities/beads/fragments/recall-pointer.md` | exact |
| `.claude-plugin/marketplace.json` (modified — add `plugins[]` entry) | config | CRUD (append) | itself, existing `plugins[0]` entry | exact |

## Pattern Assignments

### `ponytail-everywhere/.claude-plugin/plugin.json` (config)

**Analog:** `/home/dd/projects/gsd-beads/.claude-plugin/plugin.json`

Full file (12 lines) — copy shape verbatim, change `name`/`description`, drop `skills` key (no `.agents/skills` dir needed for this plugin, no skills defined):
```json
{
  "name": "beads-lifecycle",
  "version": "1.2.0",
  "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle",
  "author": {
    "name": "Dennis A. V. Dittrich",
    "email": "davdittrich@gmail.com"
  },
  "license": "MIT",
  "skills": ["./.agents/skills/beads"]
}
```
New file: same `author`/`license` block, `"name": "ponytail-everywhere"`, `"version": "0.1.0"`, description summarizing D-01 advisory-only ladder reminders. No `hooks` key needed — confirmed by RESEARCH.md: `hooks/hooks.json` is auto-discovered by Claude Code plugin convention without declaration in `plugin.json` (root `plugin.json` has no `hooks` key, yet the SessionStart hook ships and works).

---

### `ponytail-everywhere/hooks/hooks.json` (config, event-driven)

**Primary analog:** `/home/dd/projects/gsd-beads/hooks/hooks.json` (this repo's own SessionStart-only registration — matches directory/key shape exactly)
**Secondary analog (for the SubagentStart entry CONTEXT.md/RESEARCH.md require):** `/home/dd/.claude/plugins/marketplaces/ponytail/hooks/claude-codex-hooks.json`

This repo's existing shape (full file, 16 lines):
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"",
            "type": "command"
          }
        ],
        "matcher": ""
      }
    ]
  }
}
```

Dual-hook pattern to graft on (from the real `/ponytail` plugin, `SessionStart` + `SubagentStart` blocks only — omit its `UserPromptSubmit` block, out of scope):
```json
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
Note the schema divergence: this repo's own `hooks/hooks.json` uses `"matcher": ""` (empty string, key placed after `hooks[]`) while the upstream `/ponytail` plugin uses a real regex matcher placed before `hooks[]`. Both are valid Claude Code hooks-manifest shapes; RESEARCH.md's Pattern 1 recommends the regex-matcher form (`"gsd-planner|gsd-executor|gsd-verifier"`) since it's the only mechanism confirmed to reach Task-spawned subagents — use that form, not the empty-string form.

---

### `ponytail-everywhere/hooks/session-start.sh` (utility, event-driven)

**Analog:** `/home/dd/projects/gsd-beads/hooks/session-start.sh`

Full file (14 lines):
```bash
#!/usr/bin/env bash
# D-02/D-09: self-heal .beads/PRIME.md from the shipped source before bd prime reads it.
set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SOURCE="$PLUGIN_ROOT/.agents/skills/beads/PRIME.md"
DEST=".beads/PRIME.md"

if [ -d ".beads" ] && [ ! -e "$DEST" ] && [ -f "$SOURCE" ]; then
  cp "$SOURCE" "$DEST" 2>/dev/null || true
fi

exec bd prime --hook-json
```
Structural pattern to reuse: `set -u`, `PLUGIN_ROOT` resolved via `${CLAUDE_PLUGIN_ROOT:-...}` fallback, final line is the sole stdout producer. This new script has no self-heal step and no external CLI delegate (`bd prime`) — instead it must call `gsd-tools config-get` per RESEARCH.md's Don't-Hand-Roll table:
```text
gsd-tools config-get ponytail.enabled --default true
gsd-tools config-get ponytail.level   --default full
```
then print level-appropriate static reminder text to stdout (or exit 0 silently if `ponytail.enabled` resolves false) — same fail-open posture as `beads`'s `onError: "skip"` convention (RESEARCH.md Architectural Responsibility Map / CONTEXT.md Established Patterns: "a missing config value should default silently, never error the session").

---

### `.gsd/capabilities/ponytail/capability.json` (config, event-driven)

**Analog:** `/home/dd/projects/gsd-beads/.gsd/capabilities/beads/capability.json` (full file read, 186 lines)

Top-level manifest shape to copy (lines 1-25):
```json
{
  "id": "beads",
  "role": "feature",
  "version": "0.1.0",
  "title": "Beads issue tracking",
  "description": "...",
  "tier": "full",
  "requires": [],
  "engines": { "gsd": ">=1.6.0" },
  "runtimeCompat": { "supported": ["*"], "unsupported": [] },
  "skills": [ "beads-sync", "beads-status", "beads-recall", "beads-migrate-todos" ],
  "agents": [],
  "hooks": []
```
New file: `"id": "ponytail"`, empty `"skills": []` (no skills authored this phase), `"agents": []`, `"hooks": []`.

`config` block shape (lines 26-56) — copy the per-key structure (`type`, `default`, `description`), diverging on `default: true` per D-03 (explicit divergence from `beads.enabled`'s `default: false`):
```json
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
    "description": "..."
  }
}
```
New keys: `ponytail.enabled` (boolean, default `true` — D-03), `ponytail.level` (enum `["lite","full","ultra"]`, default `"full"` — D-04).

`contributions[]` shape — this repo's ONE functional entry (lines 141-155), the exact schema to copy for `plan:pre`:
```json
"contributions": [
  {
    "point": "plan:pre",
    "into": "planner",
    "produces": [],
    "consumes": ["BEADS-RECALL.md"],
    "fragment": { "path": "fragments/recall-pointer.md" },
    "when": "beads.enabled",
    "onError": "skip"
  }
]
```
New entry: `"point": "plan:pre"`, `"into": "planner"`, `"produces": []`, `"consumes": []`, `"fragment": {"path": "fragments/planner-ladder.md"}`, `"when": "ponytail.enabled"`, `"onError": "skip"`. Per RESEARCH.md's Alternatives table, additional non-functional `contributions[]` entries for `execute:*`/`verify:*`/`ship:*` may be declared as forward-compatible no-ops (mirroring how `beads`'s own `steps[]` array declares entries at points beyond the minimum) but must not be represented as delivering reach today — D-05's "Claude's Discretion" note leaves the exact point-set open; document any inert entries with an inline comment-equivalent (JSON has no comments — use the `description`-less convention `beads` itself uses, i.e. no extra marker, just don't overclaim in surrounding docs).

Note: `beads.enabled`'s `onError: "skip"` / fail-open posture (present on every `steps[]`, `contributions[]`, and `gates[]` entry in the analog) is the one pattern to replicate on every ponytail entry — this phase has no `gates[]` array at all (D-02: advisory only, no gate), so omit that key entirely rather than declaring an empty array (the analog's own `gates[]` array — lines 156-185 — is a fully populated example of what NOT to add here).

---

### `.gsd/capabilities/ponytail/fragments/planner-ladder.md` (utility, transform)

**Analog:** `/home/dd/projects/gsd-beads/.gsd/capabilities/beads/fragments/recall-pointer.md`

Full file (5 lines):
```text
An open-issue recall for this phase — `BEADS-RECALL.md` — was just generated in this phase's own
directory (`.planning/phases/<this-phase>/<NN>-BEADS-RECALL.md`, where `<NN>` is the phase's
two-digit ordinal prefix). It names every currently open bd task that scope-matched this phase,
plus a separate Unscoped heading listing everything that could not be confidently matched but was
never dropped. Read `BEADS-RECALL.md` before finalizing this phase's task scope.
```
Pattern: short (~5 line) plain-Markdown paragraph, no frontmatter, no headings — injected verbatim into the planner's prompt via `fragment.path`. New fragment must carry the D-05 planner framing ("pick the laziest viable task shape") and should reference `ponytail.level` if the text is meant to vary — but since `contributions[]` fragments are static files (not templated), any level-variance must instead be handled by the SubagentStart hook script (which CAN read config dynamically), not this static fragment. Keep this fragment level-agnostic, generic ladder-discipline framing for the planner stage only.

---

### `.claude-plugin/marketplace.json` (config, CRUD-append)

**Analog:** itself — `/home/dd/projects/gsd-beads/.claude-plugin/marketplace.json` (full file, 16 lines)

```json
{
  "name": "gsd-beads",
  "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle",
  "owner": {
    "name": "Dennis A. V. Dittrich",
    "email": "davdittrich@gmail.com"
  },
  "plugins": [
    {
      "name": "beads-lifecycle",
      "source": "./",
      "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle"
    }
  ]
}
```
Append one entry to `plugins[]` (do not touch `name`/`description`/`owner` at top level — those describe the marketplace itself, per RESEARCH.md's recommended structure the new plugin lives in its own `ponytail-everywhere/` subdirectory, sibling to root):
```json
{
  "name": "ponytail-everywhere",
  "source": "./ponytail-everywhere",
  "description": "Advisory-only lazy-ladder discipline reminders across gsd's plan/execute/verify/ship lifecycle"
}
```

---

## Shared Patterns

### Fail-open / advisory posture

**Source:** `.gsd/capabilities/beads/capability.json` — every `steps[]`/`contributions[]`/`gates[]` entry carries `"onError": "skip"`.
**Apply to:** `capability.json`'s `contributions[]` entry, and `session-start.sh`'s config-read logic (missing/malformed config value → default silently, never error the session — RESEARCH.md Don't-Hand-Roll table, CONTEXT.md Established Patterns).

### Config-key namespacing

**Source:** `beads.enabled`, `beads.sync_mode`, `beads.ship_gate`, `beads.epic_per` — all namespaced `<capability-id>.*` in `.gsd/capabilities/beads/capability.json` lines 27-55.
**Apply to:** `ponytail.enabled`, `ponytail.level` — must be checked against every shipped manifest before use per CONTEXT.md ("collisions rejected by gsd-core's capability loader"). `grep -r '"ponytail\.' .gsd/` before finalizing (only this phase's own new file will match, confirmed no prior `ponytail.*` key exists in the repo as of this read).

### `${CLAUDE_PLUGIN_ROOT}` path resolution

**Source:** `hooks/hooks.json` line 7, `hooks/session-start.sh` line 5 — hooks always reference scripts via `"${CLAUDE_PLUGIN_ROOT}/hooks/<script>.sh"` in the JSON command string, and the script itself resolves its own root via `${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}` for standalone-invocation fallback.
**Apply to:** `ponytail-everywhere/hooks/hooks.json` and `ponytail-everywhere/hooks/session-start.sh` — identical fallback line.

### Config CLI seam

**Source:** RESEARCH.md Don't-Hand-Roll table — `gsd-tools config-get <key.path> --default <value>` is the canonical seam for reading `.planning/config.json` from a shell hook (confirmed working: `config-get ponytail.level --default full` → `"full"` this session per RESEARCH.md).
**Apply to:** `ponytail-everywhere/hooks/session-start.sh` — never hand-parse `.planning/config.json` with `jq`/`grep`.

## No Analog Found

None. All 6 files/changes have a direct structural analog in this repo (`beads-lifecycle` plugin + `beads` capability) or, where this repo's own analog is incomplete (dual-hook SubagentStart registration), a verified working analog in the installed upstream `/ponytail` plugin (`~/.claude/plugins/marketplaces/ponytail/hooks/claude-codex-hooks.json`, `hooks/ponytail-subagent.js`).

## Metadata

**Analog search scope:** `/home/dd/projects/gsd-beads/.gsd/capabilities/beads/`, `/home/dd/projects/gsd-beads/hooks/`, `/home/dd/projects/gsd-beads/.claude-plugin/`, `/home/dd/.claude/plugins/marketplaces/ponytail/hooks/` and `/home/dd/.claude/plugins/marketplaces/ponytail/.claude-plugin/`
**Files scanned:** 6 read in full (all ≤ 186 lines, single-pass reads, no re-reads)
**Pattern extraction date:** 2026-08-17
</content>
