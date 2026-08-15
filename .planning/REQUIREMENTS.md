# Requirements — Milestone v1.1: Publish & Document

## v1.1 Requirements

### Plugin Packaging

- [ ] **PUB-01**: `.claude-plugin/plugin.json` declares plugin identity (name, version, license,
      author), points `skills` at existing `.agents/skills/beads/`, and passes
      `claude plugin validate . --strict`
- [ ] **PUB-02**: `.claude-plugin/marketplace.json` self-hosted entry makes
      `/plugin marketplace add <owner>/gsd-beads` then `/plugin install beads@gsd-beads` work
- [ ] **PUB-03**: The capability-loader bridge is explicitly decided and implemented (or the
      manual alternative documented) so a Claude plugin install actually surfaces the gsd-core
      `beads` capability, not just a cached repo copy

### Release & Repo Hygiene

- [ ] **PUB-04**: Release archive is built from an explicit allowlist (`.claude-plugin/`,
      `hooks/`, `.agents/skills/`, `README.md`, `LICENSE`) and attached to a GitHub Release —
      `.planning/` and `.beads/` never ship to installers
- [ ] **PUB-05**: Pre-push git hygiene audit completed — `.beads/config.yaml`,
      `.beads/metadata.json`, `.claude/.headroom_wrap_marker.json`, `.gsd-capabilities.json`
      untracked; `.gitignore` extended to cover backup/Dolt artifacts before first push

### Runtime Integration

- [ ] **PUB-06**: `hooks/hooks.json` ships the SessionStart `bd prime` hook (lifted from
      `.claude/settings.json`) so plugin installers get it without manual config

### Documentation

- [ ] **PUB-07**: `README.md` documents purpose, capabilities, installation, deinstallation,
      requirements, caveats, and a link to gsd-core — drafted via `authentic-writing` and edited
      via `academic-prose-editing`, transcribed from verified commands (not aspirational)

### Ship Gate

- [ ] **PUB-08**: `LICENSE` file (MIT) present at repo root, referenced in `plugin.json`'s
      `license` field
- [ ] **PUB-09**: Final validation gate passes: `claude plugin validate . --strict` clean, a real
      `/plugin marketplace add` + `/plugin install` + `/plugin uninstall` round trip succeeds
- [ ] **PUB-10**: GitHub repository created (public, personal account, `gsd-beads`), remote
      configured, history pushed

## Future Requirements

- CI badge / GitHub Actions test workflow — deferred until a public test workflow exists
  (FEATURES.md: "should have" once wired)
- Postinstall-hook environment verification if PUB-03's bridge turns out to require one —
  hands-on Claude Code hook API research, flagged as a Phase 4-equivalent gap in SUMMARY.md

## Out of Scope

- Submission to Anthropic's official curated plugin catalog — this ships as an independent,
  self-hosted marketplace only; no review/approval process invoked
- Multi-language README translations — zero non-English demand for a niche dev-tool plugin
  (FEATURES.md anti-feature)
- Any new runtime dependency beyond the `bd` binary and Python 3 stdlib — inherited from v1.0's
  N5 constraint, unchanged by packaging work

## Traceability

_Filled by roadmap during phase creation._
