# Pitfalls Research

**Domain:** Packaging an existing local dev tool (gsd-beads) as an installable Claude Code plugin and publishing it to GitHub for the first time
**Researched:** 2026-08-16
**Confidence:** HIGH (official Claude Code docs + direct inspection of this repo's actual `git ls-files` / working-tree state)

## Critical Pitfalls

### Pitfall 1: Wrapping the existing `.gsd/capabilities/beads/` tree in `plugin.json` without a bridge — two incompatible install mechanisms collide

**What goes wrong:**
This repo's payload is a **gsd-core capability overlay** (`.gsd/capabilities/beads/{capability.json,skills/,scripts/,fragments/}`), loaded by gsd-core's own `capability-loader.cts` from `<projectRoot>/.gsd/capabilities/<id>/` after an explicit `capability install --scope project` + content-hash consent step. This is a **completely different mechanism** from a native Claude Code plugin, whose skills/agents/hooks are auto-discovered from `skills/`, `agents/`, `hooks/hooks.json` **at the plugin root**, and which Claude Code copies into `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` on install — never into the target project's `.gsd/capabilities/`. If Phase work simply drops a `.claude-plugin/plugin.json` at repo root, `/plugin install gsd-beads@<marketplace>` will succeed, Claude Code will cache the repo, but the capability will **not** end up where gsd-core's loader looks for it, and gsd's own `capability install` step still has to be run manually against the cached copy (path unpredictable — cache paths include a resolved version segment) or a symlink/copy step (e.g. an `install`/`SessionStart` hook script) has to bridge the two.

**Why it happens:**
"Claude Code plugin" and "gsd-core capability" are two different, unrelated distribution formats that happen to share vocabulary (`skills/`, manifest, install). Nothing in gsd-core's docs states this explicitly — it was discovered here only by checking this session's environment for any existing `.claude-plugin/plugin.json` or `marketplace.json` under `$HOME/.claude` and finding **none**: gsd-core itself is installed via `npx -y @opengsd/gsd-core@latest --claude --local`, not via `/plugin install`. There is no confirmed prior art in this codebase for "capability shipped as a native Claude Code plugin."

**How to avoid:**
Decide explicitly, before writing `plugin.json`, which of two shapes this milestone means:
- (a) A thin native plugin whose `hooks/hooks.json` or a `command`-source / postinstall step invokes gsd-core's own capability-install CLI against `${CLAUDE_PLUGIN_ROOT}/.gsd/capabilities/beads` to complete the real installation, or
- (b) Drop native-plugin packaging entirely and instead document (in README) that this repo is added as a gsd-core capability source (`git clone` + point gsd-core's capability installer at the checked-out path), not through `/plugin install` at all.
Whichever is chosen, prove it end-to-end against a real `/plugin install` (or the documented alternative) — do not assume the auto-discovery in the "Standard Plugin Directory Structure" table applies to a capability nested two levels down (`.gsd/capabilities/beads/skills/`) without an explicit `skills:` path override in `plugin.json`.

**Warning signs:**
`plugin.json` exists and `claude plugin validate .` passes, but after `/plugin install`, `bd`-related skills never appear in `/help`, or `capability install --scope project` still has to be run by hand with no automation tying it to the plugin lifecycle.

**Phase to address:**
The packaging phase itself (first phase of this milestone) — this is an architecture decision, not a detail to patch later.

---

### Pitfall 2: First public push leaks machine-local dev/runtime state already tracked in git

**What goes wrong:**
`git ls-files` in this repo **today** shows `.beads/hooks/*`, `.beads/config.yaml`, `.beads/metadata.json`, `.beads/README.md`, `.claude/.headroom_wrap_marker.json`, and `.gsd-capabilities.json` are all **already tracked**, not merely present on disk:
- `.claude/.headroom_wrap_marker.json` contains a local process PID, port, and the *name* of an env var (`ANTHROPIC_BASE_URL`) — machine-run metadata with zero reason to be in a public repo.
- `.beads/metadata.json` embeds a `project_id` UUID and Dolt database name — an internal identifier with no value to a plugin consumer.
- `.gsd-capabilities.json`'s `integrity` field is currently `""` (empty) — a locally-in-progress consent artifact, not a value any other machine should inherit.
- `.beads/config.yaml` documents (in comments) where secrets like `github.token`/`linear.api_key` would go if ever set — currently empty, but the file's presence normalizes editing it in place rather than via env vars.

Separately, **untracked but present in the working tree**: `.beads.backup-pre-recovery/` (2.7 MB — a full Dolt DB backup taken during this project's own schema-recovery incident) and `.beads/interactions.jsonl` are **not covered by any `.gitignore` pattern**. `.gitignore` only excludes `.dolt/`, `*.db`, `.beads-credential-key`, `.beads/proxieddb/`, `*.gate.lock*` — none of which match `.beads.backup-pre-recovery/` or `.beads/interactions.jsonl`. A first `git add -A` (or `git add .` before the promised `git ls-files` audit runs) commits an entire historical Dolt database snapshot into permanent git history.

**Why it happens:**
The repo evolved as a working dev tree for building the gsd-beads capability itself, using `bd`/beads for the project's own local task tracking (hooks auto-install this way) alongside building the beads *capability*. Files that make sense for a local dev checkout (hooks that auto-run, DB metadata, a debug wrap-marker) were never separated from what a stranger cloning the repo as an installable plugin should receive.

**How to avoid:**
Run the `git ls-files` audit this milestone already calls for (per CLAUDE.md team-maintainer profile) **before** any `git push` to a new remote, and treat it as a checklist, not a formality:
1. Untrack (`git rm --cached`) anything under `.beads/` that is this-repo's-own dev-tracking state, not shipped payload — the shipped payload is `.gsd/capabilities/beads/`, which is already correctly tracked and separate.
2. Extend `.gitignore` to cover `.beads.backup-pre-recovery/`, `.beads/interactions.jsonl`, `.beads/metadata.json.bak`, and any `*.backup*` / `*-pre-recovery*` glob, so a future recovery incident can't repeat this leak.
3. Untrack `.claude/.headroom_wrap_marker.json` and `.gsd-capabilities.json` (or gitignore them) — both are machine/session-local, regenerated on install, not source.
4. Confirm no real value was ever set in `.beads/config.yaml`'s commented secret keys (`github.token`, `linear.api_key`) — currently clean, verify it stays that way.

**Warning signs:**
`git status` shows a large untracked directory (`.beads.backup-pre-recovery/`) sitting next to files that *are* tracked and named almost identically (`.beads/`) — a strong signal the ignore rules haven't kept pace with what actually accumulates in this working tree.

**Phase to address:**
Immediately before the first `git push` to the new GitHub remote — should be its own gated step, not folded silently into the packaging phase.

---

### Pitfall 3: Shipping only `plugin.json` — no `marketplace.json` — makes the plugin uninstallable

**What goes wrong:**
Claude Code has no "install a single plugin directly from a repo" path. Every `/plugin install` resolves a plugin through a **marketplace catalog** (`.claude-plugin/marketplace.json`), which lists plugins and their `source`. A repo that ships only `.claude-plugin/plugin.json` (correctly describing itself as a plugin) but no `.claude-plugin/marketplace.json` at the repo root cannot be installed with `/plugin marketplace add <owner>/<repo>` — that command needs `marketplace.json` to exist at that exact path, or it fails with `File not found: .claude-plugin/marketplace.json`.

**Why it happens:**
`plugin.json` and `marketplace.json` are easy to conflate because a *marketplace plugin entry* can inline nearly every field from the plugin manifest schema (`description`, `version`, `author`, `commands`, `hooks`, ...). It looks like one file should suffice. It doesn't: they serve different roles — `plugin.json` describes one plugin; `marketplace.json` is the catalog a user's Claude Code actually fetches and parses to *find* that plugin (or any plugin) in the first place.

**How to avoid:**
For a single-plugin repo, ship both, self-referencing:
- `.claude-plugin/plugin.json` at repo root (or under a `plugins/gsd-beads/` subdirectory) with `name`, `version`, `description`, `author`.
- `.claude-plugin/marketplace.json` at repo root with `name` (marketplace name, distinct from — but can equal — the plugin name; avoid the reserved-name list: `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `claude-plugins-community`, `claude-community`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, and others that impersonate Anthropic), `owner`, and one `plugins[]` entry with `source: "./"` (or the subdirectory path) pointing at the plugin.
Run `claude plugin validate .` and `/plugin marketplace add ./` locally, then `/plugin install gsd-beads@gsd-beads`, before ever pushing.

**Warning signs:**
`/plugin marketplace add owner/repo` errors with a file-not-found on `.claude-plugin/marketplace.json`, or the marketplace adds successfully but `/plugin install` reports "Plugin not found in any marketplace."

**Phase to address:**
Packaging phase — both files are produced and validated together, not sequentially.

---

### Pitfall 4: Manifest field-name/type mistakes fail silently, not loudly

**What goes wrong:**
Claude Code's manifest loader is **lenient by default**: an unrecognized top-level field in `plugin.json` (a typo like `"authors"` instead of `"author"`, or a field invented by copying another ecosystem's manifest) is silently **ignored**, not rejected — the plugin still loads, just without that field taking effect. `claude plugin validate` reports this as a **warning**, not a blocking error, unless run with `--strict`. Separately, some *recognized* fields have strict shape requirements that, if violated, do hard-fail the plugin: `repository` and `license` must be plain **strings** (`"https://github.com/..."`, `"MIT"`), not objects (`{"type": "git", "url": "..."}` — a common npm `package.json` habit — is rejected); `author`, when present, must be an **object** with at least `name` (a bare string author is rejected, unlike some other ecosystems' manifests).

**Why it happens:**
Authors familiar with npm's `package.json` (`repository: {type, url}`, `author: "Name <email>"`) copy those shapes by habit; Claude Code's schema looks similar but diverges on exactly these two fields. The lenient-unless-`--strict` validation behavior means a typo can sit undetected through casual testing, since the plugin still "works" — just missing the metadata that would have populated a marketplace listing field.

**How to avoid:**
Run `claude plugin validate . --strict` (or `/plugin validate .`) as a required step before every push that touches `plugin.json` or `marketplace.json` — not just once at initial packaging. Use the field tables in this research (or the official schema at `code.claude.com/docs/en/plugins-reference`) as the source of truth over any other ecosystem's manifest conventions.

**Warning signs:**
`claude plugin validate .` (without `--strict`) reports zero errors, but a field visibly fails to render where expected (e.g., no repository link shown in `/plugin` UI) — that gap is the signal to re-run with `--strict`.

**Phase to address:**
Packaging phase, as a mandatory gate (mechanical validator, not a reviewer judgment call).

---

### Pitfall 5: Version pinning mistakes silently strand users on stale code

**What goes wrong:**
Two distinct footguns, both silent:
1. **Declaring `version` in both `plugin.json` and the marketplace entry.** Claude Code always prefers the `plugin.json` value with no warning — if the marketplace entry is bumped but `plugin.json`'s `version` string is forgotten, every install continues to resolve the old `plugin.json` version and users see no update, with no error surfaced anywhere.
2. **Declaring a `version` at all and then forgetting to bump it.** Setting `"version": "1.0.0"` in `plugin.json` and then pushing new commits without changing that string means existing installs keep the **cached, stale copy** forever — Claude Code sees an identical version string and skips the update. The alternative (omitting `version` entirely) makes Claude Code resolve to the git commit SHA of the source instead, so every new commit is picked up automatically — simpler for an actively-developed plugin, at the cost of no stable release boundary.

**Why it happens:**
Both mistakes look correct at the moment of the commit (the version *is* set correctly at commit time); the failure only appears on the *next* release cycle, once someone edits code without touching the version field, or edits the wrong one of two files that both carry a `version` key.

**How to avoid:**
Pick one authority for `version` and document it: either (a) never set `version` in `marketplace.json`, only in `plugin.json`, and bump it as part of every release commit, or (b) omit `version` entirely for now (early-stage plugin, git SHA gates updates) and revisit once release cadence stabilizes. Either choice removes the two-file-disagreement class of bug outright.

**Warning signs:**
A user reports a fixed bug is still present after they ran `/plugin marketplace update`; check whether `version` changed in the commit that "fixed" it.

**Phase to address:**
Packaging phase decides the policy; every subsequent release (out of scope for this milestone but worth a phase note) must follow it.

---

### Pitfall 6: README claims outrun what a fresh install actually does

**What goes wrong:**
The milestone's own success criterion is a README that "lets a stranger evaluate, install, and remove it without reading the source." Given Pitfall 1, the literal install mechanism here is unusual (a native-plugin shell around a gsd-core capability overlay, or a documented non-`/plugin` install path) — a README that describes a generic "`/plugin install gsd-beads@gsd-beads`, then it just works" experience, without stating the `bd` binary prerequisite, the `gsd.engines >= 1.6.0` compatibility requirement, and whatever bridge step Pitfall 1 resolved to, will not match reality on a stranger's machine. This is the single most common way a first-time plugin publish erodes trust: the described install path silently diverges from the actual one the moment the plugin does anything beyond dropping flat `skills/`/`agents/` files.

**Why it happens:**
README is usually written from the author's mental model of "how it's supposed to work," drafted before or without a truly clean-machine install test; the author's own dev machine already has `bd` on `PATH` and gsd-core installed, masking missing-prerequisite failures a stranger would hit immediately.

**How to avoid:**
Write the README's install section only after running the literal install/removal steps on a machine (or container) with none of this project's existing state — no `bd`, no prior gsd-core capability consent, no cached `.gsd/capabilities/`. State explicitly: `bd` binary required on `PATH`, Python 3 stdlib only (no other deps per constraint N5), gsd-core `>=1.6.0`, and the exact commands for install, verify-it-worked, and uninstall/removal. Include the fail-open behavior (bd absent → no-op, not a crash) as a caveat, since it directly affects what "installed but doing nothing" looks like to a stranger.

**Warning signs:**
No one on the team has run the README's install steps from a machine that never had this project's `.gsd/capabilities/beads/` or `.beads/` state present.

**Phase to address:**
README phase, gated on a literal clean-environment install/removal dry run, not just a proofread.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|------------------|
| Ship `plugin.json` without `marketplace.json`, telling early testers to use `claude plugin marketplace add ./local-path` | Faster to demo locally | Public GitHub install is broken for every real user (Pitfall 3) | Never for the actual publish — fine only for local dev iteration |
| Omit `version` from `plugin.json`, resolve via git SHA | No release-bump discipline needed yet | No stable "install v1.0" story; a bad commit can propagate to users immediately on next update | Acceptable for this milestone (pre-1.0, single maintainer) — revisit once there are external installs to protect |
| Leave `.beads/` (this repo's own dev-tracking state) tracked in git rather than fully separating dev-repo concerns from shipped-plugin concerns | No restructuring work now | Every clone of the "plugin" repo also clones an unrelated project's task-tracking history and hooks, bloating and confusing it | Never — untrack before first push (Pitfall 2) |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|-----------------|--------------------|
| GitHub (first push to new remote) | Running `git push` before an explicit `git ls-files` review, trusting `.gitignore` alone to have caught everything | Run `git ls-files` and diff it mentally against "what should a stranger installing this plugin receive," per CLAUDE.md's own team-maintainer audit requirement — this research already found 3+ files that pass `.gitignore` but shouldn't ship |
| Claude Code plugin marketplace | Assuming `/plugin install owner/repo` works without a marketplace.json (Pitfall 3), or that a `source: "."` entry is universally supported (it fails on Claude Code versions between v2.1.120 and the version that added `source: "."`/`archive`/`command` support) | Ship both manifest files; use `source: "./"` for a root-level plugin (not bare `"."` unless targeting v2.1.221+); validate with `claude plugin validate .` |
| gsd-core capability loader | Treating "Claude Code plugin install" and "gsd-core capability install" as the same event (Pitfall 1) | Explicitly wire or document the bridge between the two install flows before calling packaging done |
| `bd` (beads) external binary | Not stating it as a hard runtime prerequisite anywhere in `plugin.json` (there is no manifest field for "external binary required") | State it in `description`/`keywords` and, non-negotiably, in the README's Requirements section |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|-----------------|
| Committing Dolt DB backups/snapshots (`.beads.backup-pre-recovery/`, 2.7 MB and growing with every future recovery incident) into git history | Repo clone time grows; `git log --all --  ` on binary blobs bloats `.git` | `.gitignore` every backup/snapshot pattern before first push (Pitfall 2); if already committed, this needs history rewrite before the *first* public push (trivial now, effectively impossible once the remote has other clones) | Breaks the moment a second recovery incident doubles the committed backup size, or the moment any external clone exists and history can no longer be rewritten cleanly |
| Full Dolt DB copy-mode caching per Claude Code plugin install/update — every install/update creates a new versioned cache directory | `~/.claude/plugins/cache` grows unbounded across many version bumps | Orphaned versions are swept automatically ~14 days after superseding, per Claude Code's own cache design — no action needed here, just don't rely on the old version's files remaining reachable sooner than that | N/A at this project's scale; documented for awareness only |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Tracking `.beads/config.yaml` in git while its commented-out template documents exactly where `github.token`/`linear.api_key` would go | A future contributor pastes a real token into the "obvious" place shown in a tracked file | Prefer env vars for any future secret config (the file's own comments already recommend this); keep the file's secret-key fields empty/commented, and consider gitignoring `.beads/config.yaml` entirely once it's no longer needed for the public plugin repo |
| Tracking `.claude/.headroom_wrap_marker.json` — leaks a local PID/port and an env-var *name* (`ANTHROPIC_BASE_URL`) | Low direct risk (no secret value), but signals sloppy separation between "my machine's session state" and "what ships to the public" — invites closer scrutiny of what else leaked | Untrack; gitignore `.headroom_wrap_marker.json` |
| No `LICENSE` file at repo/plugin root yet | Not a Claude Code install blocker technically, but blocks GitHub's own license detection, blocks any org's automated OSS-compliance gate, and is the single most common reason a stranger won't trust/adopt an unfamiliar plugin | Add a `LICENSE` file at repo root (physical file, separate from `plugin.json`'s `license: "MIT"` string field — both are expected, per Claude Code's own reference structure) before or alongside first push |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|--------------|-------------------|
| README documents "install" but not "verify it worked" | User installs, sees nothing different, assumes it's broken (especially likely here since the fail-open design means a missing `bd` binary produces near-silence, not an error) | README states an explicit post-install check (e.g., a specific skill/command becoming available, or a one-line `bd`-presence check) |
| README documents "install" but not "uninstall/remove" | User who wants to back out doesn't know whether `/plugin uninstall` alone is sufficient, or whether the gsd-core capability install (Pitfall 1) leaves state behind in their project's `.gsd/capabilities/` | README's Deinstallation section covers both layers explicitly, matching whatever the packaging phase decided in Pitfall 1 |

## "Looks Done But Isn't" Checklist

- [ ] **plugin.json present and validates:** run `claude plugin validate . --strict`, not just default (non-strict) validate, before considering the manifest correct — default mode hides typo'd/unrecognized fields (Pitfall 4)
- [ ] **marketplace.json present:** confirm `.claude-plugin/marketplace.json` exists at repo root, not only `.claude-plugin/plugin.json` — test with a real `/plugin marketplace add ./` + `/plugin install` round trip, not just JSON-syntax validation (Pitfall 3)
- [ ] **git ls-files audited against what a stranger should receive:** re-run `git ls-files` after any `.gitignore` change and manually check each new file against "does an installer need this" — don't assume `.gitignore` alone caught everything (Pitfall 2 found 3 tracked files and 1 untracked 2.7 MB directory that don't belong)
- [ ] **Clean-machine install test performed:** README's install steps were actually run somewhere without pre-existing `bd`, gsd-core consent state, or cached `.gsd/capabilities/beads/` (Pitfall 6)
- [ ] **LICENSE file exists at repo root** and its SPDX identifier matches `plugin.json`'s `license` field (Security Mistakes table)
- [ ] **Version policy stated and followed once, as a smoke test:** bump `version`, confirm `/plugin marketplace update` + `/plugin update` actually picks up the change (Pitfall 5)

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|----------------|------------------|
| Files already leaked into git history *before* first push to a real remote (current state) | LOW | `git rm --cached` the offending files/dirs, extend `.gitignore`, commit — no history rewrite needed because no remote has cloned it yet. This window closes the moment the first `git push` to GitHub happens. |
| Files leaked into git history *after* first push (hypothetical future mistake) | HIGH | Requires `git filter-repo`/BFG history rewrite + force-push + every existing clone/fork re-cloning — explicit user approval required per CLAUDE.md's force-push policy; treat as a genuine incident, not a routine fix |
| `marketplace.json` missing after a "working" `plugin.json`-only publish | LOW | Add `.claude-plugin/marketplace.json`, push — no breaking change for anyone, since nobody could have installed it before |
| Version-pin mismatch stranding users on stale cache (Pitfall 5) | MEDIUM | Bump `version` in `plugin.json` (the authoritative file per resolution order) to a new, higher string; users must explicitly `/plugin update` or wait for auto-update, since Claude Code won't retroactively detect the earlier omission |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|----------------|
| Capability-loader vs native-plugin mismatch (Pitfall 1) | Packaging phase | A real `/plugin install` (or documented alternative) followed by confirming the `bd`-related skill(s) actually load/execute in a fresh project |
| Leaked local dev/runtime state (Pitfall 2) | Pre-push audit phase (gated, explicit — not folded into packaging) | `git ls-files` reviewed line-by-line against "does a plugin installer need this"; `.beads.backup-pre-recovery/` and `.beads/interactions.jsonl` confirmed gitignored or removed |
| Missing marketplace.json (Pitfall 3) | Packaging phase | `/plugin marketplace add ./` + `/plugin install <name>@<name>` succeeds locally before push |
| Manifest field mistakes (Pitfall 4) | Packaging phase | `claude plugin validate . --strict` exits clean |
| Version pinning mistakes (Pitfall 5) | Packaging phase (policy decision) + every future release (out of milestone scope, note for later) | One real bump-and-update cycle tested |
| README/reality mismatch (Pitfall 6) | README phase | Clean-environment install/verify/uninstall dry run performed and its exact commands transcribed into the README |

## Sources

- [Create and distribute a plugin marketplace — Claude Code Docs](https://code.claude.com/docs/en/plugin-marketplaces) — official marketplace.json schema, plugin sources, version resolution, troubleshooting table (HIGH confidence, official first-party docs)
- [Plugins reference — Claude Code Docs](https://code.claude.com/docs/en/plugins-reference) — official plugin.json schema, directory structure, caching/version-resolution rules (HIGH confidence, official first-party docs)
- Direct inspection of this repo's actual git state: `git ls-files`, `git status`, `.gitignore` contents, `.beads/config.yaml`, `.beads/metadata.json`, `.claude/.headroom_wrap_marker.json`, `.gsd-capabilities.json`, `du -sh .beads.backup-pre-recovery` (HIGH confidence — read directly, not inferred)
- `.planning/PROJECT.md` — capability-loader architecture description, milestone goal, constraints (N5 no extra deps, engines.gsd >=1.6.0, fail-open behavior) (HIGH confidence — project's own source of truth)
- User's persisted memory note: gsd-core installed via `npx -y @opengsd/gsd-core@latest --claude --local`, not via any existing `.claude-plugin/`/`marketplace.json` on this machine — corroborated by a live filesystem search finding none (HIGH confidence)

---
*Pitfalls research for: Claude Code plugin packaging + GitHub publish (gsd-beads v1.1 milestone)*
*Researched: 2026-08-16*
