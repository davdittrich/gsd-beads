# Phase 6: Runtime Integration - Pattern Map

**Mapped:** 2026-08-16
**Files analyzed:** 2 (`hooks/hooks.json` new, `.claude/settings.json` modified/deleted)
**Analogs found:** 1 exact / 2 (the second file IS its own analog — a delete, not a content-pattern problem)

## Search Confirmation

Confirmed via filesystem: `hooks/` does not exist yet in this repo (only `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json` exist under the plugin root, no `hooks.json`). `.claude/settings.json` exists today as a 15-line file containing exactly one `hooks.SessionStart` block. RESEARCH.md's Pattern 2 and Code Examples already identify the exact analog: this phase's new file is a byte-identical copy of the existing file's content, so no broader codebase search for a "hooks.json" analog is needed or possible (no other plugin-hooks file exists in this repo).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `hooks/hooks.json` | config (plugin hook manifest) | event-driven (Claude Code `SessionStart` event → shell command) | `.claude/settings.json` (this repo, read in full this session) | exact — byte-identical content, different container/location only |
| `.claude/settings.json` | config (project-local hook manifest) | event-driven | itself (deletion target, not a content-pattern problem) | n/a — delete file (or its `SessionStart` key) once `hooks/hooks.json` ships |

No controller/component/service/model/middleware files in this phase — RESEARCH.md confirms "No new libraries or CLI tools... edits two JSON files... documents one existing gsd-core CLI invocation." No test framework applies (Validation Architecture: "None (no application code produced this phase)").

## Pattern Assignments

### `hooks/hooks.json` (config, event-driven)

**Analog:** `/home/dd/Gemini/gsd-beads/.claude/settings.json` (full file, 15 lines, read this session)

**Exact content to copy verbatim** (source: `.claude/settings.json`, all 15 lines):
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "command": "bd prime --hook-json",
            "type": "command"
          }
        ],
        "matcher": ""
      }
    ]
  }
}
```

**Schema authority (no in-repo prior art for this exact container):** `code.claude.com/docs/en/plugins-reference` — `hooks/hooks.json` at plugin root, format `{"hooks": {"<EventName>": [{"hooks": [{"type": "command", "command": "..."}], "matcher": "..."}]}}`. This matches `.claude/settings.json`'s existing shape field-for-field, so the settings-file content is both the style analog and the literal content source — do not paraphrase or restructure it.

**Do NOT add:** a `command -v bd` PATH guard (RESEARCH.md Pitfall 4 / Anti-Patterns — Claude Code's own `SessionStart` exit-code contract already fails open with one non-blocking notice; a guard diverges from the exact command already proven across Phases 1-5 and is unrequested scope).

---

### `.claude/settings.json` (config, event-driven) — deletion, not creation

**Action:** Delete the file outright (it contains only the `hooks.SessionStart` key today — read in full this session, 15 lines, no other content) once `hooks/hooks.json` ships, in the same phase/commit.

**Why not just remove the key and keep `{}`:** RESEARCH.md Code Examples: "the file currently contains only the `hooks.SessionStart` block... removing that key empties the file's meaningful content — delete the file outright rather than leave `{}` behind, unless a later phase needs it for something else (none known)."

**Why this must happen in the same change:** RESEARCH.md Pitfall 3 (verbatim from `code.claude.com/docs/en/hooks`): "A plugin's or skill's copy of the same handler stays separate" — dedup does NOT cross a settings-file/plugin-hooks.json boundary. Leaving both files double-fires `bd prime` in this repo's own dev sessions the moment the plugin is also locally installed.

---

## Shared Patterns

### Event-driven hook config shape

**Source:** `.claude/settings.json` (this repo) == `hooks/hooks.json` target shape (Claude Code plugins-reference schema)
**Apply to:** Both files in this phase — they are the same pattern instance, one being retired, one being introduced.
```json
{"hooks": {"<EventName>": [{"hooks": [{"type": "command", "command": "..."}], "matcher": ""}]}}
```

### Fail-open contract — do not re-implement

**Source:** `code.claude.com/docs/en/hooks` (verbatim, fetched this session, RESEARCH.md Pitfall 4)
**Apply to:** `hooks/hooks.json`'s `bd prime --hook-json` command only — no wrapper/guard needed; Claude Code's own `SessionStart` exit-code handling already produces "one visible notice, session proceeds" when `bd` is absent.

### Manual capability-install bridge (PUB-03) — no file pattern, CLI-only

**Source:** `bin/lib/capability-command-router.cjs:262-296` (gsd-core, read this session) + this project's own Phase 1 precedent (`.planning/milestones/v1.0-phases/01-substrate/01-03-PLAN.md:174`)
**Not a file this phase creates** — this phase documents (in the plan/README, not new source) the existing command:
```bash
node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability install \
  <path-to-.gsd/capabilities/beads> --scope project --yes
```
No new CLI wrapper should be built (RESEARCH.md Don't Hand-Roll table) — this is a documentation deliverable, not a code file, so it is out of scope for this PATTERNS.md's file-classification table but flagged here because RESEARCH.md treats it as equally load-bearing as PUB-06.

## No Analog Found

None. Both files in scope have a direct, exact, in-repo content source (`.claude/settings.json` itself). The capability-install bridge (PUB-03) is a documented CLI invocation, not a new source file, so it has no "role/data-flow" classification to search an analog for.

## Metadata

**Analog search scope:** `.claude/`, `.claude-plugin/`, `hooks/` (does not yet exist), repo root
**Files scanned:** `.claude/settings.json` (full read), `.claude-plugin/plugin.json` (full read), `.gsd/capabilities/beads/capability.json` (referenced via RESEARCH.md, not re-read — content confirmed there)
**Pattern extraction date:** 2026-08-16
