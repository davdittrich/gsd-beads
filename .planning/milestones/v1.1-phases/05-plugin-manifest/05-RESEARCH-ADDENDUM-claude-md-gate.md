# Addendum: `claude plugin validate --strict` vs. root `CLAUDE.md`

**Scope:** answers the 5 sub-questions in the research brief. Read-only investigation, no repo files touched.

## Confirmed mechanism

The check is hardcoded in the `claude` binary (compiled, `/opt/claude-code/bin/claude`, v2.1.233). Extracted string table around the warning (`grep -a -bo` + raw byte read at offset 162488833):

```
claude.md
claude.local.md
Remove it from the plugin root.
To ship context with your plugin, use a skill (skills/<name>/SKILL.md) instead.
root
 at the plugin root is not loaded as project context.
```

Reassembled message (matches the reproduced failure exactly):
> "CLAUDE.md at the plugin root is not loaded as project context. To ship context with your plugin, use a skill (skills/\<name\>/SKILL.md) instead. Remove it from the plugin root."

This is also stated verbatim in the **official docs** (code.claude.com/docs/en/plugins-reference), confirming it is intentional, documented validator behavior, not a bug:

> "A `CLAUDE.md` file at the plugin root is not loaded as project context. Plugins contribute context through skills, agents, and hooks rather than CLAUDE.md. To ship instructions that load into Claude's context, put them in a skill."

## Answers

**1. Is there an allowlist/ignore mechanism (`plugin.json` field, `.claudeignore`, etc.)?**
No. Searched the docs (plugins-reference) and the binary's string table for `ignore`/`allowlist`/`.claudeignore` patterns near this check — none exists. The only related documented tolerance is for **unrecognized `plugin.json` fields** (warning, not error) and **unrecognized default-folder names** — neither applies to a stray root file. There is no field in `plugin.json` or any sidecar config that suppresses this specific check.

**2. Does the warning also fire without `--strict`?**
Yes, it always fires as a `⚠` warning (confirmed by the reproduced output: `⚠ root: CLAUDE.md at the plugin root is not loaded as project context.`). `--strict` only changes whether the warning is promoted to a validation failure (exit 1). Per `claude plugin validate --help`:
> `--strict  Treat warnings as errors (exit 1). Use in CI to fail on unrecognized fields, missing metadata, and other issues that the runtime tolerates.`
Non-strict `claude plugin validate .` will show the warning but exit 0.

**3. Is the check filename-literal, and does relocating/renaming avoid it?**
The binary's string table contains exactly two lowercase filename literals adjacent to this check: `claude.md` and `claude.local.md` — i.e. the validator flags **both** `CLAUDE.md` and `CLAUDE.local.md` at the plugin root (case-insensitive match on the exact filename, evidenced by lowercase storage). It is scoped to the plugin **root** directory listing (the message literally says "at the plugin root" / "Remove it from the plugin root", and the docs section is titled for root-level files). Two ways this scoping can be exploited without touching content:
- **Any other filename** (e.g. `AGENTS.md`, `DEVELOPMENT.md`) at plugin root does not match `claude.md`/`claude.local.md` and is not flagged — but Claude Code's own auto-load-CLAUDE.md-as-project-context behavior (the reason this repo has the file) only fires for the literal name `CLAUDE.md`, so renaming defeats the repo's own use of the file for interactive dev sessions.
- **A subdirectory** is not "the plugin root" — the check is a root-level directory-listing check only, not a recursive scan (no `CLAUDE.md` string match found scoped to nested directories in the binary's logic, and the message text is explicit about "root"). If the file lived one level down, it would not trigger.

**4. Is this intentional validator behavior, confirmed against the actual installed CLI?**
Yes. `claude plugin validate --help` documents `--strict` as "treat warnings as errors... issues that the runtime tolerates" — i.e. the CLI author's own framing confirms this class of warning is deliberately non-fatal by default and only escalated in CI-strict mode by design. The message text itself ("To ship context with your plugin, use a skill... instead") is prescriptive guidance, not an error-recovery hint for a bug. Combined with the docs quote in Q1/Q2, this is confirmed intentional, not a defect.

**5. Official docs statement.**
code.claude.com/docs/en/plugins-reference, verbatim (fetched this session):
> "A `CLAUDE.md` file at the plugin root is not loaded as project context. Plugins contribute context through skills, agents, and hooks rather than CLAUDE.md. To ship instructions that load into Claude's context, put them in a skill."

No ignore/allowlist field is documented anywhere in that reference for plugin-root files.

## Root cause of the conflict

The plugin's root (`.claude-plugin/plugin.json`) is currently the **git repo root** (`/home/dd/Gemini/gsd-beads/.claude-plugin/plugin.json`, confirmed present this session). "Plugin root" and "repo root" are the same directory. The validator's root-only, filename-literal check therefore always sees this repo's own dev-workflow `CLAUDE.md` and flags it — the check is doing exactly what it's documented to do; the conflict is structural (repo root == plugin root), not a validator gap.

## Recommended fix

**No `plugin.json`/validator-config mechanism exists to suppress this — do not invent one.** Two real options, in order of invasiveness:

1. **(Non-invasive, recommended for this phase) Run validation without `--strict` in CI/local gates**, or explicitly document/accept the warning. The warning is cosmetic at the plugin-packaging level: it only says the file won't be auto-loaded as context *when the repo is installed as a plugin* — which is true and irrelevant to this repo's own use of `CLAUDE.md` for interactive dev sessions in this working tree. This preserves `CLAUDE.md` at the repo root exactly as-is; zero change to other tooling.
2. **(Invasive, only if `--strict` CI cleanliness is a hard requirement) Move the plugin root to a subdirectory** (e.g. `plugin/.claude-plugin/plugin.json`, with `skills/`, `commands/`, etc. under `plugin/`), leaving `CLAUDE.md` at the true repo root, outside the validated plugin directory. This is a structural repackaging (marketplace.json source path, install instructions, CI paths all change) — out of scope for a one-file addendum; would need its own ticket if pursued.

Given the stated constraint ("other tooling in this repo depends on [CLAUDE.md] staying at the repo root"), **option 1 is the concrete recommended fix**: drop `--strict` (or accept the single warning) rather than rename/relocate `CLAUDE.md`. There is no config-based suppression available; renaming defeats the file's own purpose; relocating the plugin root is a larger restructuring decision for the user, not a research-phase fix.
