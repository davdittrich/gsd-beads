# Phase 6: Runtime Integration - Research

**Researched:** 2026-08-16
**Domain:** Claude Code plugin hooks (`hooks/hooks.json`) + gsd-core's capability-loader overlay system — two structurally separate runtimes this phase must bridge
**Confidence:** HIGH — the capability-loader bridge question (PUB-03) was answered by directly reading gsd-core's own source (`capability-loader.cjs`, `capability-source.cjs`, `capability-command-router.cjs`) this session, not inferred from docs. The `hooks.json` schema and hook-dedup/fail-open semantics were fetched verbatim from `code.claude.com/docs/en/plugins-reference` and `code.claude.com/docs/en/hooks` this session.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUB-03 | The capability-loader bridge is explicitly decided and implemented (or the manual alternative documented) so a Claude plugin install actually surfaces the gsd-core `beads` capability, not just a cached repo copy | Architecture Patterns → Pattern 1 (two-system architecture, source-verified), Pitfall 1 (plugin install ≠ capability install), Pitfall 2 (PUB-04 ship-allowlist gap), Code Examples → capability install command |
| PUB-06 | `hooks/hooks.json` ships the SessionStart `bd prime` hook (lifted from `.claude/settings.json`) so plugin installers get it without manual config | Architecture Patterns → Pattern 2 (hooks.json schema, verbatim), Pitfall 3 (hook dedup does NOT cross a settings-file/plugin boundary), Code Examples → `hooks/hooks.json` |

</phase_requirements>

## Summary

This phase bridges two runtimes that share no code path. **Claude Code's plugin system** (skills, `hooks/hooks.json`, `/plugin install`) is entirely separate from **gsd-core's capability-loader overlay system** (`.gsd/capabilities/<id>/capability.json`, `gsd-tools capability install`). I confirmed this by reading `capability-loader.cjs` directly: its `overlayRoots()` function scans exactly two locations — `$GSD_HOME/.gsd/capabilities/<id>/` (global) and `<projectRoot>/.gsd/capabilities/<id>/` (project) — and has zero awareness of Claude Code's plugin cache, `${CLAUDE_PLUGIN_ROOT}`, or anything `/plugin install` writes. **A `/plugin install beads@gsd-beads` in some other project gives that project the `beads` Claude Code *skill* and (once PUB-06 ships) the `bd prime` SessionStart hook — it does NOT register `.gsd/capabilities/beads/` with gsd-core's loader in that project, because Claude Code never writes there.** PUB-03's "cached repo copy" framing is exactly correct: the plugin install is inert with respect to the capability lifecycle (`plan:pre`/`plan:post`/`execute:wave:*`/`verify:post`/`ship:pre` steps, contributions, gates) until a *second*, separate step runs.

That second step already exists and is exactly what this project used on itself in Phase 1 (`01-03-PLAN.md`) and re-ran after every post-consent edit since: `gsd-tools capability install <path-to-.gsd/capabilities/beads> --scope project --yes`, run once inside the target project, at a human checkpoint (never auto-approved — gsd-core's own consent gate, CB-3, is deliberately human-gated, confirmed by reading `capability-loader.cjs`'s consent-check block and `capability-command-router.cjs`'s `--yes` flag handling). **Recommendation: PUB-03 is satisfied by the manual-alternative path, not an automatic bridge.** Three independent facts converge on this: (1) REQUIREMENTS.md's own "Future Requirements" section already flags "postinstall-hook environment verification" as *out of scope*, requiring dedicated research not done this session — building an automatic hook-driven bridge now would silently exceed that boundary; (2) an automatic `--yes` consent grant fired from a hook would defeat the human-checkpoint design the loader's own code comments describe as intentional (CB-3); (3) `.gsd/capabilities/beads/` is **not** in PUB-04's Phase-8 ship allowlist (`.claude-plugin/`, `hooks/`, `.agents/skills/`, `README.md`, `LICENSE`) — so once the public release archive ships, there will be no capability bundle inside the installed plugin directory for a hook to point at anyway. The durable, testable-today manual step is documented in Code Examples below.

PUB-06 is comparatively simple: `hooks/hooks.json`'s schema is `{"hooks": {"SessionStart": [...]}}`, structurally identical to the block already in `.claude/settings.json`. I recommend copying it verbatim rather than adding a `command -v bd` guard — Claude Code's own hook runtime already fails open with exactly one visible notice when a hook command can't start (confirmed verbatim from `code.claude.com/docs/en/hooks`: a missing/non-executable command hits shell exit 127, which for `SessionStart` "doesn't block on its own... the action proceeds" and the transcript shows `Failed with non-blocking status code: ...`). Adding a manual PATH guard would be unrequested defensive code duplicating a guarantee Claude Code's hook contract already provides. **The one real risk is criterion 3 (no double prime):** I confirmed verbatim that Claude Code does **not** dedupe a hook across a settings-file and a plugin's `hooks.json` ("A plugin's or skill's copy of the same handler stays separate") — so once `hooks/hooks.json` ships, `.claude/settings.json`'s identical `SessionStart` block must be **removed**, not left in place, or this repo's own dev sessions fire `bd prime` twice the moment the plugin is also installed locally (as Phase 5's Task 3 round trip did).

**Primary recommendation:** Ship `hooks/hooks.json` as a byte-identical copy of `.claude/settings.json`'s current `SessionStart` block, then delete `.claude/settings.json` (or at minimum its `SessionStart` key) in the same phase. Satisfy PUB-03 by documenting and executing the `gsd-tools capability install ./.gsd/capabilities/beads --scope project --yes` manual step from a clean scratch project, and record the exact command in the plan/README rather than building any postinstall automation.

## Architectural Responsibility Map

Not a multi-tier web app — the standard Browser/Frontend-Server/API/CDN/DB tiers do not apply. This phase spans two independent local-runtime tiers plus the packaging tier from Phase 5.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SessionStart `bd prime` context injection | Claude Code hooks runtime (`hooks/hooks.json`, read by the Claude Code CLI itself) | `.claude/settings.json` (dev-only fallback, being retired by this phase) | Only Claude Code's own hook engine reads and fires `hooks/hooks.json`; nothing in gsd-core or `bd` participates |
| `beads` Claude Code skill surfacing | Claude Code plugin runtime (`plugin.json`'s `skills` field, shipped Phase 5) | — | Already wired; unaffected by this phase |
| gsd-core capability lifecycle (`plan:pre`/`plan:post`/`execute:wave:*`/`verify:post`/`ship:pre` steps, contributions, gates) | gsd-core capability-loader (`bin/lib/capability-loader.cjs`, overlay scan of `.gsd/capabilities/<id>/`) | `gsd-tools capability install` CLI (the write path into that overlay dir) | The loader is the SOLE consumer of `capability.json`; it never reads anything Claude Code's plugin system writes |
| The bridge between "plugin installed" and "capability active" | Human-run CLI (`gsd-tools capability install ... --scope project --yes`), NOT an automated hook | — | gsd-core's own consent gate (CB-3) is deliberately human-gated per source comments in `capability-loader.cjs`; an automatic hook-driven `--yes` would defeat that design and is explicitly out of this phase's scope per REQUIREMENTS.md's Future Requirements note |

## Standard Stack

### Core

No new libraries or CLI tools. This phase edits two JSON files (`hooks/hooks.json`, delete `.claude/settings.json`'s hook) and documents one existing gsd-core CLI invocation (`gsd-tools.cjs capability install`). No `npm install`/`pip install` step.

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|---------------|
| `claude` CLI | `2.1.233` [VERIFIED: local `claude --version`, run this session] | Loads `hooks/hooks.json` at plugin install/session start; the only runtime that reads this file | Anthropic's own plugin hook loader — no alternative |
| `gsd-tools.cjs` (`node $HOME/.claude/gsd-core/bin/gsd-tools.cjs`) | installed at `/home/dd/.claude/gsd-core` [VERIFIED: local filesystem check this session] | `capability install`/`capability state`/`loop render-hooks` — the entire verification surface for PUB-03 | It is gsd-core's own capability lifecycle CLI; there is no other way to activate an overlay capability |
| `bd` | already present on PATH in this dev environment [VERIFIED: `.claude/settings.json`'s existing `bd prime --hook-json` hook, live-verified across Phases 1-4 per PROJECT.md] | The binary the SessionStart hook invokes | Existing project dependency, unchanged by this phase (N5 constraint: no new runtime dependency) |

### Supporting

None.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual `gsd-tools capability install --scope project --yes` step, documented | An automatic postinstall/SessionStart hook that runs `capability install ... --yes` silently | REQUIREMENTS.md's own Future Requirements section flags this as needing dedicated "hands-on Claude Code hook API research" not done this session — attempting it now is scope creep past what this phase's own project planning already decided to defer. It also silently grants consent (`--yes`) with no human in the loop, defeating gsd-core's CB-3 consent gate by design, and would target a `.gsd/capabilities/beads/` path that (per PUB-04) will not exist in the public release archive once Phase 8 ships — the automation would work today and silently break at first public release. |
| `hooks/hooks.json` bare `bd prime --hook-json` (byte-identical to the existing dev hook) | `hooks/hooks.json` with a `command -v bd >/dev/null 2>&1 &&` guard | Unnecessary: Claude Code's own hook exit-code contract already treats a shell-127 "command not found" as non-blocking for `SessionStart` and surfaces exactly one `<hook name> hook error` notice — precisely ROADMAP criterion 4's "one visible notice." A hand-rolled guard duplicates a guarantee the platform already provides and diverges from the exact command already proven correct by this repo's own dev hook across Phases 1-5. |
| Deleting `.claude/settings.json`'s `SessionStart` hook once `hooks/hooks.json` ships | Leaving both in place | Confirmed verbatim (Pitfall 3): Claude Code dedupes an identical hook only *within* settings files, never across a settings file and a plugin's `hooks.json` — leaving both means this repo's own dev sessions fire `bd prime` twice whenever the plugin is also installed locally, directly violating ROADMAP criterion 3. |

**Installation:** None.

**Version verification:** N/A — no packages.

## Package Legitimacy Audit

**Not applicable.** Zero external packages installed by this phase in any ecosystem.

**Packages removed due to [SLOP] verdict:** none (N/A)
**Packages flagged as suspicious [SUS]:** none (N/A)

## Architecture Patterns

### System Architecture Diagram

```
                         ┌───────────────────────────────────────┐
                         │   /plugin install beads@gsd-beads       │
                         │   (target project, ANY OTHER repo)       │
                         └───────────────────┬───────────────────┘
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     │      Claude Code plugin runtime (own tier)         │
                     │                                                     │
                     │  reads plugin.json.skills → surfaces `beads` skill    │
                     │  reads hooks/hooks.json → registers SessionStart       │
                     │       hook: `bd prime --hook-json`                      │
                     │                                                          │
                     │  Claude Code has NO knowledge of `.gsd/capabilities/`     │
                     │  and never writes to it.  <<< PUB-03's exact gap >>>       │
                     └────────────────────────┬────────────────────────────────┘
                                              │  (this arrow does NOT exist —
                                              │   confirmed by reading
                                              │   capability-loader.cjs)
                                              ✕
                     ┌────────────────────────┼────────────────────────┐
                     │   gsd-core capability-loader overlay (own tier)    │
                     │                                                     │
                     │  overlayRoots() scans ONLY:                          │
                     │    $GSD_HOME/.gsd/capabilities/<id>/  (global)        │
                     │    <projectRoot>/.gsd/capabilities/<id>/  (project)    │
                     │                                                          │
                     │  loop render-hooks / plan:pre / execute:wave:* / ship:pre │
                     │  all read from THIS overlay — never from anywhere         │
                     │  Claude Code's plugin cache writes                          │
                     └────────────────────────▲────────────────────────────────┘
                                              │
                                 ONE explicit, human-run command
                                 bridges the gap (PUB-03's actual answer):
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     │  gsd-tools capability install                       │
                     │    <path-to-.gsd/capabilities/beads>                  │
                     │    --scope project --yes                                │
                     │  (run once, inside the target project, at a               │
                     │   human checkpoint — never auto-approved)                   │
                     └───────────────────────────────────────────────────────────┘

  Dogfooding double-fire risk (criterion 3), same repo, two hook sources:
  ┌────────────────────────────┐        ┌────────────────────────────┐
  │ .claude/settings.json        │        │ hooks/hooks.json             │
  │ SessionStart: bd prime         │  +   │ SessionStart: bd prime         │  = TWO fires
  │ (existing dev-only hook)         │      │ (this phase's new hook)          │    (confirmed:
  └────────────────────────────┘        └────────────────────────────┘     Claude Code does
                                                                              NOT dedupe a handler
                                                                              across a settings file
                                                                              and a plugin's hooks.json)
  Fix: DELETE .claude/settings.json's SessionStart block once hooks/hooks.json ships.
```

### Recommended Project Structure

```
gsd-beads/
├── hooks/
│   └── hooks.json           # NEW — SessionStart: bd prime --hook-json (lifted verbatim)
├── .claude/
│   └── settings.json        # MODIFIED — SessionStart key removed (or file deleted if now empty)
├── .claude-plugin/
│   └── plugin.json          # EXISTING (Phase 5) — no changes needed for PUB-06
└── .gsd/capabilities/beads/ # EXISTING — untouched by this phase; referenced by the
                              # documented manual `capability install` step, not shipped
                              # via the Claude Code plugin path
```

### Pattern 1: The manual capability-install bridge (PUB-03)

**What:** After `/plugin install beads@gsd-beads` in a target project, run a second, explicit, human-approved command that registers `.gsd/capabilities/beads/` with gsd-core's own loader for THAT project.
**When to use:** Any project that wants the `beads` gsd-core *capability* (lifecycle steps/gates), not just the Claude Code *skill*.
**Example (this session, verified against this exact repo):**
```bash
# Source: bin/lib/capability-command-router.cjs:262-296 (read this session) — CLI shape
# Source: .planning/milestones/v1.0-phases/01-substrate/01-03-PLAN.md:174 (this project's own
#         Phase 1 precedent for the identical command)
# [VERIFIED: bin/lib/capability-command-router.cjs:262-296 — "capability install <spec>
#  [--integrity sha512-…] [--scope global|project] [--yes] [--shared-file <rel>]…"]
cd /path/to/target-project
node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability install \
  /path/to/gsd-beads-checkout/.gsd/capabilities/beads \
  --scope project --yes

# Confirm it registered:
node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability state --raw
# → capabilities[] should contain { "id": "beads", "installed": true, "active": true, ... }
```
**Why the spec argument is a path ending in `.gsd/capabilities/beads`, not the plugin root:** `resolveLocal()` in `capability-source.cjs` (read this session, lines 704-724) reads `capability.json` directly from `<spec>/capability.json` — the spec must point at the directory *containing* `capability.json`, exactly as this project's own `.gsd/capabilities/beads/capability.json` sits. Pointing the spec at the plugin's repo root would fail (`capability.json` missing at that path).
**Do NOT** attempt to derive this path from `${CLAUDE_PLUGIN_ROOT}` inside an automated hook for this phase — see Pitfall 1 and Pitfall 2 for why that's deferred, not solved here.

### Pattern 2: `hooks/hooks.json` — lift verbatim from `.claude/settings.json`

**What:** `hooks/hooks.json`'s schema is `{"hooks": {"<EventName>": [{"hooks": [{"type": "command", "command": "..."}], "matcher": "..."}]}}` — structurally identical to a project's `.claude/settings.json` hooks block.
**When to use:** Exactly this phase's situation — an existing, proven `.claude/settings.json` SessionStart hook needs to ship inside the plugin.
**Example:**
```json
// Source: code.claude.com/docs/en/plugins-reference, "Location: hooks/hooks.json in plugin
// root... Format: JSON configuration event matchers actions" [CITED — fetched this session]
// Content below is byte-identical to the existing .claude/settings.json (read this session):
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
`[VERIFIED: .claude/settings.json (read this session, full file, 15 lines) — the block above is byte-identical to the file's current content.]`

### Anti-Patterns to Avoid
- **Adding a `command -v bd` PATH guard to the packaged hook:** unnecessary — Claude Code's own hook exit-code contract already fails open with one visible notice on a missing binary (see Pitfall 4). This would diverge the packaged hook from the exact command already proven working in this repo's own dev hook.
- **Leaving `.claude/settings.json`'s `SessionStart` hook in place after `hooks/hooks.json` ships:** confirmed to double-fire whenever both are active in the same session (Pitfall 3) — must be removed, not merely left as a "harmless duplicate."
- **Building a postinstall/SessionStart-triggered automatic `capability install --yes`:** explicitly deferred by this project's own REQUIREMENTS.md Future Requirements section; also targets a path (`.gsd/capabilities/beads/`) not present in PUB-04's ship allowlist, so it would work today and silently stop working after Phase 8's public release.
- **Pointing the manual `capability install` spec at the plugin's repo root instead of `.gsd/capabilities/beads/`:** `resolveLocal()` requires `capability.json` at the spec root exactly (Pattern 1).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bridging "plugin installed" to "capability active" | A custom postinstall script, a wrapper CLI, or a hook that shells out to reimplement consent logic | `gsd-tools capability install <path> --scope project --yes` (already exists, already used by this project 5+ times across Phases 1-3) | It already implements staging, validation, the consent gate, and the ledger write correctly — a hand-rolled equivalent would have to re-derive all of `capability-lifecycle.cjs`'s atomicity/consent logic, badly |
| Detecting whether `bd` is on PATH before firing the SessionStart hook | A `command -v bd` guard clause | Nothing — rely on Claude Code's built-in non-blocking exit-code contract for `SessionStart` (Pitfall 4) | The platform already guarantees "one visible notice, session proceeds" for a hook command that can't start; adding a guard is dead code duplicating an existing guarantee |

**Key insight:** Both requirements in this phase are satisfied by *documenting and reusing* mechanisms that already exist and are already proven (this project's own Phase 1 capability-install precedent, Claude Code's own hook fail-open contract) — the risk in this phase is entirely in correctly wiring existing pieces together and verifying the two double-fire/gap scenarios, not in writing new logic.

## Common Pitfalls

### Pitfall 1: `/plugin install` and `capability install` are two unrelated systems — a plugin install alone does nothing for the gsd-core lifecycle
**What goes wrong:** A user installs the Claude Code plugin, sees the `beads` skill available, and assumes the `beads` gsd-core capability (plan/execute/ship lifecycle wiring) is now active in their project. It is not — `bd prime`, `bd ready`, etc. work via the skill, but nothing writes `BEADS-RECALL.md`/`BEADS.md` or gates `ship:pre` on `blocking_open`.
**Why it happens:** Confirmed by reading `capability-loader.cjs`'s `overlayRoots()` this session: it scans exactly `$GSD_HOME/.gsd/capabilities/<id>/` and `<projectRoot>/.gsd/capabilities/<id>/`. Nothing in that function, or anywhere else in `capability-loader.cjs`/`capability-source.cjs`, reads Claude Code's plugin install location. The two systems share no code.
**How to avoid:** PUB-03's manual step (Pattern 1) is mandatory and must be documented prominently — likely in the eventual README (Phase 8) and explicitly verified in this phase's own success criterion 1.
**Warning signs:** `capability state --raw` does not list `beads` as `active: true` in a project where only `/plugin install` was run.

### Pitfall 2: `.gsd/capabilities/beads/` is not in PUB-04's ship allowlist — the manual bridge has no stable public source yet
**What goes wrong:** Once Phase 8 builds the release archive from PUB-04's allowlist (`.claude-plugin/`, `hooks/`, `.agents/skills/`, `README.md`, `LICENSE`), the resulting archive will **not** contain `.gsd/capabilities/beads/capability.json`. Any bridge mechanism (manual or automated) that assumes the capability bundle sits alongside the installed plugin's files will find nothing there.
**Why it happens:** PUB-04's requirement text (`.planning/REQUIREMENTS.md`) lists the allowlist explicitly and it omits `.gsd/`. This is a genuine, currently-unresolved gap between Phase 6 (this phase, PUB-03) and Phase 8 (PUB-04) — Phase 6 cannot fix Phase 8's allowlist, but must not silently assume it will be fixed.
**How to avoid:** Document the manual step (Pattern 1) as requiring a **git clone of the full gsd-beads repository** (not the plugin archive) as the source of `.gsd/capabilities/beads/` — this works today (local path, this exact checkout) and will keep working after publication (`git clone` + local-path `capability install` against the clone). Flag explicitly, in this phase's plan and PROJECT.md's Blockers/Concerns, that Phase 8 should either (a) add `.gsd/capabilities/beads/` to PUB-04's allowlist, or (b) confirm the README's documented bridge step directs users to clone the repo rather than rely on the release archive for this piece.
**Warning signs:** A future phase's README draft describes installing the capability "from the downloaded plugin" without mentioning a separate clone.

### Pitfall 3: Hook dedup does not cross a settings-file / plugin boundary — shipping `hooks/hooks.json` without removing `.claude/settings.json`'s copy double-fires `bd prime` in this repo
**What goes wrong:** Once `hooks/hooks.json` exists and the plugin is (re-)installed while working inside this repo (as Phase 5's Task 3 round trip already did once), `bd prime --hook-json` fires twice on session start — visible as duplicated prime output.
**Why it happens:** Verbatim, `code.claude.com/docs/en/hooks`, fetched this session: "All matching hooks run in parallel. If you define the same handler in more than one settings file, it runs once. **A plugin's or skill's copy of the same handler stays separate.**" `.claude/settings.json` and `hooks/hooks.json` are exactly this case — one is a settings file, the other is a plugin's hook file — so Claude Code's own dedup rule explicitly does not apply.
**How to avoid:** Delete `.claude/settings.json`'s `SessionStart` key (the file currently contains only this one hooks block — read this session, 15 lines total — so the file can likely be deleted outright) in the same phase that adds `hooks/hooks.json`. Verify criterion 3 by installing the plugin locally (Phase 5's own proven round-trip commands) while working in this repo and confirming exactly one `bd prime` fires per session — this is a live, human-observable check, not something a static file diff can prove alone.
**Warning signs:** Two `bd prime --hook-json`-sourced context blocks appearing in a single session transcript.

### Pitfall 4: Do not add a PATH guard to the packaged hook — Claude Code's own hook contract already fails open correctly
**What goes wrong (if "fixed" unnecessarily):** Adding `command -v bd >/dev/null 2>&1 && bd prime --hook-json || echo "bd not found"` (or similar) to `hooks/hooks.json` diverges the packaged command from the exact, already-proven `.claude/settings.json` command, for no behavioral gain.
**Why it happens / why it's unnecessary:** Verbatim, `code.claude.com/docs/en/hooks`, fetched this session: "A hook that can't start lands in the same non-blocking bucket. When the script path doesn't exist or isn't executable, the shell exits with a code like 127 and you see the same notice with the interpreter's message... For most hook events, the action proceeds." And specifically for `SessionStart`: "exit code 2 is the only exit code that blocks through the code alone... Claude Code treats exit code 1 as a non-blocking error and proceeds with the action." A bare `bd` on a PATH without the binary produces exactly this: a non-blocking `<hook name> hook error` notice, and the session proceeds — satisfying ROADMAP criterion 4 ("install and session start still succeed with one visible notice") with zero extra code.
**How to avoid:** Ship the bare command (Pattern 2), matching this repo's own existing, already-verified `.claude/settings.json` hook exactly.
**Warning signs:** A plan task proposing to "add error handling" to the hook command — this is unrequested scope against an already-satisfied platform guarantee.

### Pitfall 5: Any edit to `.gsd/capabilities/beads/` this phase silently deactivates the capability until re-consented
**What goes wrong:** If this phase's plan touches any file under `.gsd/capabilities/beads/` (it should not need to — PUB-03/PUB-06 are packaging/hooks work, not capability-content work — but if a future task does), the project-scope consent hash (bound to full bundle content) goes stale and `beads` silently drops out of `render-hooks` output with no error.
**Why it happens:** Documented and previously hit by this exact project (memory `gsd-capability-consent-hash-invalidation`; also `.planning/PROJECT.md` Key Decisions table, "gsd-core project-scope capability consent is a content hash over the whole bundle" entry) — any file edit inside an already-consented bundle invalidates the hash.
**How to avoid:** This phase's scope should not touch `.gsd/capabilities/beads/` at all. If it must, re-run `capability install ./.gsd/capabilities/beads --scope project --yes` and re-verify `loop render-hooks <point> --raw` names `capId: "beads"` before closing the phase.
**Warning signs:** `capability state --raw` shows `beads` present but `active: false`, or `render-hooks` output silently drops the `beads` capId.

## Code Examples

### `hooks/hooks.json` (complete file, PUB-06)
```json
// Source: code.claude.com/docs/en/plugins-reference — "Location: hooks/hooks.json in plugin
// root... Format: JSON configuration event matchers actions" [CITED, fetched this session]
// Content is byte-identical to .claude/settings.json's current SessionStart block
// [VERIFIED: .claude/settings.json — read in full this session, 15 lines]
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

### `.claude/settings.json` after this phase (SessionStart key removed)
Since the file (read this session, verbatim) currently contains only the `hooks.SessionStart` block, removing that key empties the file's meaningful content — delete the file outright rather than leave `{}` behind, unless a later phase needs `.claude/settings.json` for something else (none is known to this session).

### Manual capability-install bridge command (PUB-03, run from a clean scratch project)
```bash
# Source: bin/lib/capability-command-router.cjs:262-296 (read this session)
# [VERIFIED: bin/lib/capability-command-router.cjs:262-296 — "capability install <spec>
#  [--integrity sha512-…] [--scope global|project] [--yes] [--shared-file <rel>]…"]
mkdir -p /tmp/gsd-beads-clean-test && cd /tmp/gsd-beads-clean-test
git init -q   # optional — findProjectRoot() falls back to cwd with no .git/.planning marker too
              # [VERIFIED: bin/lib/project-root.cjs:26-54, read this session — "findProjectRoot
              #  is total — it returns cwd itself when no marker exists"]

node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability install \
  /home/dd/Gemini/gsd-beads/.gsd/capabilities/beads \
  --scope project --yes

node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability state --raw
# expect: capabilities[] contains {"id":"beads", "installed":true, "active":true, ...}
```

### Verifying no double prime (criterion 3, live check inside this repo)
```bash
# Precondition: hooks/hooks.json shipped, .claude/settings.json's SessionStart key removed.
# 1. Locally install the plugin (Phase 5's own proven round trip, 05-01-SUMMARY.md):
claude plugin marketplace add ./ --scope local
claude plugin install beads@gsd-beads -y
# 2. Start a fresh Claude Code session inside this repo and inspect the transcript/session log
#    for the number of bd-prime-sourced SessionStart context blocks — must be exactly 1.
# 3. Clean up:
claude plugin uninstall beads
claude plugin marketplace remove gsd-beads
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| This repo's own `bd prime` SessionStart hook lived only in `.claude/settings.json` (project-local, not shipped) | Lifted into `hooks/hooks.json` so it ships with the plugin (PUB-06) | This phase | Any project that installs the plugin gets the hook with zero manual `.claude/settings.json` editing — but this repo's own dev workflow must switch from the settings-file hook to relying on the plugin being locally installed (see Pitfall 3) |
| Hook dedup assumption | Confirmed narrow: only dedupes identical handlers *within* settings files, never across a settings file and a plugin's `hooks.json` | Documented behavior, unchanged recently, verified this session | Directly drives Pitfall 3's fix (delete the settings.json copy, don't just add the plugin copy) |

**Deprecated/outdated:** None — this is additive packaging work over an already-shipped v1.0 capability.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Deleting `.claude/settings.json`'s `SessionStart` key means this repo's own dev sessions rely on the plugin being locally installed (via `/plugin marketplace add ./` + `/plugin install`) to get `bd prime` at all — I could not verify this session whether Claude Code auto-loads `hooks/hooks.json` merely from cwd containing `.claude-plugin/plugin.json`, without an explicit `/plugin install`. The two verbatim doc quotes fetched this session ("Changes to hooks/... do not [take effect immediately]... run /reload-plugins") describe behavior for an *already-installed* plugin's live checkout, not a never-installed repo. | Architecture Patterns → Pattern 2 anti-pattern note; Pitfall 3 | If auto-load does NOT happen for a merely-checked-out repo, deleting `.claude/settings.json` without keeping the plugin persistently installed locally would silently remove `bd prime` from this repo's own daily dev sessions. Recommend the plan verify this live (start a fresh session with the plugin uninstalled and `.claude/settings.json`'s hook removed, confirm whether `bd prime` context still appears) before deleting the settings.json hook, and keep the plugin installed locally going forward if it does not auto-load. |
| A2 | The full text of the `### SessionStart` event's dedicated input/output schema section on `code.claude.com/docs/en/hooks` was truncated in this session's fetch (the tool noted a truncation marker) — I relied on the events table, matcher table, and exit-code tables instead, which were untruncated and directly answered the three questions asked. | Common Pitfalls → Pitfall 4 | Low — the exit-code/non-blocking behavior was quoted verbatim and cross-confirmed by two separate table excerpts (exit-code-0 section and exit-code-2-per-event table); a missing schema field (e.g., a `hookSpecificOutput.additionalContext` option) would only matter if this phase tried to customize the hook's *output*, which it does not — the hook stays a bare `command` type unchanged from the existing dev hook. |

## Open Questions (RESOLVED)

1. **Does `hooks/hooks.json` fire for a plain `cd`-into-this-repo Claude Code session that has never run `/plugin install`?**
   - What we know: `hooks/hooks.json` is defined as part of the plugin bundle, loaded when the plugin is installed/active. A prior Phase 5 pitfall noted `claude plugin init`-scaffolded plugins under `~/.claude/skills/<name>/` "auto-load next session" — a different location convention than this repo's root.
   - What's unclear: Whether Claude Code treats *any* repo with `.claude-plugin/plugin.json` at cwd root as an implicitly-active plugin for hook purposes, or strictly requires an explicit `/plugin install` record.
   - Recommendation: The plan's tracer/verification task should test this directly — open a fresh session in this repo with the plugin NOT installed and `.claude/settings.json`'s hook already removed, and observe whether `bd prime` context still appears. If not, keep the plugin persistently installed locally (via the marketplace, not uninstalled after testing) as this repo's own dogfooding setup, and document that as an explicit, disclosed decision.
   - **RESOLVED:** Empirically tested in Phase 6 Task 1 (Probe A/Probe B, `claude -p ... --debug hooks --debug-file`); findings recorded in `06-01-SUMMARY.md` and, per the recommendation above, the plugin is kept installed at local scope as this repo's disclosed dogfooding setup.

2. **Should PUB-04's ship allowlist (Phase 8) be amended to include `.gsd/capabilities/beads/`?**
   - What we know: Today's allowlist (`REQUIREMENTS.md` PUB-04) omits it; this phase's manual bridge (Pattern 1) works around the gap by requiring a full git clone rather than the release archive.
   - What's unclear: Whether Phase 8 planning already accounts for this, or whether it's a genuinely new finding from this phase.
   - Recommendation: Record this finding in `PROJECT.md`'s Blockers/Concerns (as this research does) so Phase 7/8 planning sees it before the ship-allowlist decision is finalized.
   - **RESOLVED (Forward):** Gap recorded in `STATE.md` Blockers/Concerns by Phase 6 Task 3, for Phase 7/8 planning to pick up; no automation built in this phase per REQUIREMENTS.md's Future Requirements deferral.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `claude` CLI | Loading `hooks/hooks.json`, `/plugin install`/`uninstall` round trip (criteria 2, 3) | ✓ | `2.1.233` [VERIFIED: local `claude --version`, this session] | — |
| `gsd-tools.cjs` (gsd-core) | `capability install`/`capability state` (criterion 1) | ✓ | installed at `$HOME/.claude/gsd-core` [VERIFIED: local filesystem check, this session] | — |
| `bd` binary | Session-start hook target; also the deliberate absent-case test for criterion 4 | ✓ (present in this dev environment) | — | Criterion 4's test needs a PATH-manipulated shell (`PATH=/usr/bin:/bin claude ...` or similar, excluding wherever `bd` actually lives) to exercise the absent case — not a missing dependency, a deliberate test setup |
| `git` | Cloning gsd-beads for the durable (post-publication) form of the manual bridge (Pattern 1, Pitfall 2) | ✓ | — | Not required for THIS phase's own local-path verification (the checkout already exists on disk) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none — all required tools are present in this dev environment.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None (no application code produced this phase) — verification is via `claude plugin validate`, `capability state --raw`, `loop render-hooks --raw`, and live session observation, matching Phase 5's own precedent |
| Config file | none |
| Quick run command | `node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability state --raw \| grep -A3 '"id": "beads"'` |
| Full suite command | The full sequence in Code Examples → "Manual capability-install bridge command" + "Verifying no double prime" |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PUB-03 | `beads` capability reachable by gsd-core's loader after the documented manual step, from a clean project | manual-only (CLI, no test framework) — no application code, the CLI's own state query IS the test | `capability install <path> --scope project --yes && capability state --raw` (Code Examples) | N/A — commands exist today |
| PUB-06 | `hooks/hooks.json` fires `bd prime` with no `.claude/settings.json` edit; fires exactly once; fails open with one notice when `bd` is absent | manual-only (interactive Claude Code session, live transcript inspection) — SessionStart hook firing is not scriptable via a non-interactive CLI call | Local marketplace install/uninstall round trip (Code Examples → "Verifying no double prime") + a PATH-restricted session for the fail-open case | N/A |

### Sampling Rate
- **Per task commit:** `capability state --raw` quick check (JSON validity of `hooks/hooks.json`, presence of `beads` in loader output where applicable)
- **Per wave merge:** Full local install/uninstall round trip + live session double-prime check
- **Phase gate:** All four ROADMAP success criteria demonstrated against a genuinely clean scratch project, before `/gsd-verify-work`

### Wave 0 Gaps
None — existing `claude` CLI and `gsd-tools.cjs` installations cover this phase's entire verification surface. No test framework install needed.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | Not applicable |
| V3 Session Management | No | Not applicable |
| V4 Access Control | Yes (narrow) | gsd-core's own CB-3 project-scope consent gate (`capability-loader.cjs`'s `hasProjectConsent` check, `capability-command-router.cjs`'s `--yes` flag) — this phase must NOT bypass it via automation; the manual step (Pattern 1) preserves the existing human-checkpoint control this project has used since Phase 1 |
| V5 Input Validation | Yes (narrow) | `hooks/hooks.json`'s JSON is validated by `claude plugin validate --strict` (same D-09-style double-run discipline established in Phase 5, since `hooks/hooks.json` presence is one of the checks that mode covers) |
| V6 Cryptography | No | Not applicable |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| An automated hook silently granting capability-install consent (`--yes`) with no human review | Elevation of Privilege | Do not build this (Pattern 1 anti-pattern, Pitfall 1) — keep the manual, human-checkpointed `capability install --scope project --yes` step, matching this project's own established T-01-10/T-02-06 security controls from Phases 1-2 |
| A malformed or overlong `hooks/hooks.json` shipped to installers | Denial of Service (degraded UX, not a crash — Claude Code's own hook loader already fails open per Pitfall 4) | `claude plugin validate . --strict` (Phase 5's D-09 double-run pattern) catches JSON/schema errors before commit |

## Sources

### Primary (HIGH confidence)
- `bin/lib/capability-loader.cjs` (`$HOME/.claude/gsd-core`) — read in full this session (825 lines); `overlayRoots()`, the consent gate, and the never-crash contract are the direct source of the "two separate systems" finding underlying PUB-03
- `bin/lib/capability-source.cjs` — read this session (through line ~962 of 1258); `resolveLocal`/`resolveGit`/`stageValidated` confirm the exact spec-path semantics used in Pattern 1
- `bin/lib/capability-command-router.cjs` — read this session; exact `capability install <spec> [--scope] [--yes]` CLI shape (lines 262-296), confirms `--scope project` resolves `runtimeDir = cwd`
- `bin/lib/project-root.cjs` — read this session; confirms `findProjectRoot` is total (falls back to cwd with no `.git`/`.planning` marker)
- `.claude/settings.json` — read in full this session (15 lines); source of the byte-identical `hooks/hooks.json` content in Pattern 2
- `code.claude.com/docs/en/plugins-reference` — fetched this session; `hooks/hooks.json` location/format, `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_PLUGIN_DATA}`/`${CLAUDE_PROJECT_DIR}` variables, "changes to hooks/... do not take effect immediately" note
- `code.claude.com/docs/en/hooks` — fetched this session; exit-code-0/exit-code-2/other-exit-code tables (verbatim, the source of Pitfall 4), and the settings-file-vs-plugin dedup rule (verbatim, the source of Pitfall 3)
- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` — read in full this session; requirement text, the four ROADMAP success criteria, the PUB-04 ship allowlist, the "Future Requirements" deferral note, prior Key Decisions (consent-hash gotcha, fail-open B6, `ship.md` patch)
- `.planning/milestones/v1.0-phases/01-substrate/01-03-PLAN.md` and `01-03-SUMMARY.md` — read (grep + targeted read) this session; this project's own precedent for the exact `capability install ./.gsd/capabilities/beads --scope project` command and its human-checkpoint discipline
- `.planning/phases/05-plugin-manifest/05-RESEARCH.md` and `05-01-SUMMARY.md` — read in full this session; Phase 5's local marketplace-add/install/uninstall round-trip commands reused verbatim in this phase's verification examples

### Secondary (MEDIUM confidence)
- None beyond the primary sources above — no WebSearch-only claims in this document.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all tooling already verified installed this session
- Architecture (two-system bridge, PUB-03): HIGH — established by directly reading gsd-core's own loader/source/router code this session, not inferred
- Pitfalls (hook dedup, fail-open exit codes): HIGH — verbatim doc quotes fetched this session
- Open Question 1 (dogfooding auto-load without explicit install): MEDIUM — could not fully resolve from documentation alone this session; flagged as Assumption A1 requiring a live test during planning/execution

**Research date:** 2026-08-16
**Valid until:** 30 days (Claude Code's plugin/hooks schema is actively evolving per Phase 5's own "State of the Art" table showing frequent version-gated field additions; re-verify hook dedup/exit-code behavior if plan execution slips past ~2026-09-15)
