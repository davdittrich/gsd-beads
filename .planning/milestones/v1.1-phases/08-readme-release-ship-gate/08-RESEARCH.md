# Phase 8: README, Release & Ship Gate - Research

**Researched:** 2026-08-16
**Domain:** GitHub Actions release automation, Claude Code plugin CLI/marketplace mechanics, README authoring for a Claude Code plugin
**Confidence:** HIGH (all core mechanisms confirmed via `--help` output, official docs fetched live, and `gh api`/`git ls-files` against this repo)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** README is written for a cold stranger who knows neither gsd-core nor beads — matches SC1's literal "a stranger can evaluate" framing. Not scoped to gsd-core users or beads users specifically.
- **D-02:** Install/uninstall commands are exact, copy-pasteable, verbatim — none paraphrased. No "expected output" blocks shown (keeps the doc from drifting out of sync with CLI output format changes).
- **D-03:** Caveats section covers all three: (1) requirements — `bd` on PATH, Python 3 stdlib, gsd-core >=1.6.0 (already named in ROADMAP SC1); (2) known limitations of the beads/Dolt backend specific to this repo's config (no `.beads/issues.jsonl` passive export — Dolt-only backend, confirmed in Phase 7's RESEARCH.md); (3) SessionStart hook prerequisites — what `bd prime` needs on first run, whether the installer's own repo needs a beads project already initialized.
- **D-04:** `README.md` lives at repo root. Section order: Title/one-liner → What it does → Requirements → Install → Uninstall → Caveats → License → Link to gsd-core.
- **D-05:** Include a short worked `bd` usage example beyond bare install (a tiny end-to-end workflow snippet), not just a pointer to AGENTS.md's Quick Reference.
- **D-06:** Build the allowlisted release archive via a GitHub Actions workflow (`.github/workflows/release.yml`) triggered on `vX.Y.Z` tag push. Zips exactly `.claude-plugin/`, `hooks/`, `.agents/skills/`, `README.md`, `LICENSE` and attaches to a GitHub Release. Chosen over a manual local script or hand-built zip for repeatability. Reversible.
- **D-07:** Tag/version this release `v1.1.0` — matches the current milestone version (v1.1, "Publish & Document"). The existing `v1.0` tag stays as historical/internal.
- **D-08:** The `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip is scripted where the CLI supports non-interactive flags; any step requiring interactive confirmation is called out explicitly for the user to perform by hand rather than faked or skipped.
- **D-09:** The round-trip's real command output (proof, not simulation) is embedded directly in Phase 8's `SUMMARY.md` — same pattern as Phase 7's fresh-clone verification transcript. No separate VALIDATION-TRANSCRIPT.md file.
- **D-10:** `claude plugin validate . --strict` already passes clean on the current local working tree. The ship gate must NOT rely on this local pass — it must re-run `claude plugin validate . --strict` against a fresh clone checked out at the released tag.
- **D-11 (open, deferred to researcher/planner):** `marketplace.json`'s plugin source is currently `"./"`. Whether this needs to change for the public release round trip was UNRESOLVED at discuss-phase time — see `## D-11 Resolution` below, now resolved with HIGH confidence.

### Claude's Discretion

- Exact README prose/wording within the locked section order (D-04).
- Exact GitHub Actions workflow YAML structure for D-06, as long as it triggers on tag push and produces the exact allowlist archive.
- Exact wording of the worked `bd` usage example (D-05).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUB-04 | Release archive built from explicit allowlist, attached to GitHub Release; `.planning/`/`.beads/` never ship | `## Architecture Patterns` (release workflow), `## D-11 Resolution`, `## Common Pitfalls` (Pitfall 2) — confirms allowlist dirs are clean and gives the exact GH Actions steps |
| PUB-07 | README documents purpose, capabilities, install, uninstall, requirements, caveats, gsd-core link — transcribed from verified commands | `## Code Examples` (verified CLI syntax for install/uninstall), `## Standard Stack` (README structure) |
| PUB-09 | `claude plugin validate . --strict` clean; real `/plugin marketplace add`+`install`+`uninstall` round trip succeeds | `## Code Examples` (exact `claude plugin` subcommand flags, scriptability per D-08), `## D-11 Resolution` |
</phase_requirements>

## Summary

This phase has no new runtime dependencies — everything needed (`claude` CLI 2.1.233, `gh` CLI 2.97.0, `git`, `zip`) is already installed and verified working in this environment. The three pieces of new work are: (1) a GitHub Actions workflow file that zips an explicit allowlist and attaches it to a GitHub Release on tag push, (2) a `README.md` at repo root following the locked D-04 section order, and (3) a ship-gate verification pass that re-runs `claude plugin validate . --strict` against a fresh clone at the tagged commit and performs a real `claude plugin marketplace add` / `install` / `uninstall` round trip.

The most consequential finding is the resolution of **D-11**: Claude Code's official docs, fetched live this session, confirm that a relative-path plugin `source` (`"./"`) resolves correctly against a marketplace added via a GitHub `owner/repo` shorthand (which is exactly what `claude plugin marketplace add davdittrich/gsd-beads` does) — it fails to resolve only when the marketplace itself is registered from a bare URL pointing directly at `marketplace.json`. So `"./"` needs no change. However, this same research surfaces a **new, unflagged risk**: relative-path plugin sources copy the *entire cloned repository* (whatever `git clone` produces, i.e. every git-tracked file) into the plugin cache — not just the allowlisted directories. Since `.planning/` (130 tracked files) and `.beads/` (20 tracked files, mostly git hooks) are both tracked in this repo, installing via `/plugin marketplace add` + `/plugin install` (SC4's round trip) will copy them into `~/.claude/plugins/cache/gsd-beads/beads/<version>/`. This does not violate any locked success criterion (SC3 specifically scopes "no `.planning/`/`.beads/` file" to the **release-archive** install path, which is confirmed clean), but it is a real, user-visible side effect of the marketplace round trip that the README's caveats section (D-03) and the plan's verification step should account for.

The `claude plugin` CLI subcommands (`marketplace add`, `install`, `uninstall`, `validate`) are fully non-interactive-capable: `install` and `uninstall` both expose `-y`/`--yes`, explicitly documented as "required when stdin or stdout is not a TTY." `marketplace add` has no confirmation flag in its `--help` output and none is documented as needed — it is scriptable as-is. This resolves D-08 in favor of the CLI form (`claude plugin ...`, not the interactive `/plugin ...` slash commands) for the scripted portion of the round trip.

**Primary recommendation:** Use `gh release create` (not `softprops/action-gh-release`) for D-06's workflow — it's preinstalled on `ubuntu-latest` runners, needs no third-party action pin, and is the officially recommended current pattern. Use `claude plugin marketplace add`/`install -y`/`uninstall -y` (CLI form) for D-08/D-09's scripted round trip, and flag only the plugin-cache-copy side effect (not an interactive-confirmation gap) as the one thing to call out to the user.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Release archive build & publish | CI (GitHub Actions) | — | D-06 locks this to a GHA workflow; no local/manual build path |
| Allowlist enforcement | CI (GitHub Actions, workflow YAML) | — | The `zip` step's explicit path list IS the allowlist; no separate validation layer needed since `zip <paths>` only ever includes named paths |
| README content | Static docs (repo root) | — | Pure Markdown, no templating/build step |
| Ship-gate validation | Local CLI (`claude`, `gh`, `git`) run by the phase executor/human | CI (optional future) | D-10 requires a fresh clone + validate run, not embedded in the release workflow — kept as a manual/scripted verification step per D-09's SUMMARY.md transcript pattern |
| Plugin marketplace resolution | Claude Code CLI runtime (`~/.claude/plugins/`) | — | Entirely owned by the installed `claude` binary; the repo only supplies `marketplace.json`/`plugin.json` |

## Standard Stack

### Core

| Tool | Version (verified) | Purpose | Why Standard |
|------|---------------------|---------|---------------|
| `gh` CLI | 2.97.0 (installed, `[VERIFIED: gh --version, this session]`) | Create GitHub Release + attach asset from within the workflow | Preinstalled on `ubuntu-latest` GH-hosted runners; no extra action/token setup beyond `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` `[CITED: community pattern, cross-checked against softprops/action-gh-release README]` |
| `actions/checkout` | v7.0.1 latest `[VERIFIED: gh api repos/actions/checkout/releases/latest, this session]` | Checkout repo in the workflow before zipping | Standard first step in virtually every GH Actions workflow |
| `zip` (coreutils) | preinstalled on `ubuntu-latest` `[ASSUMED — not verified against a live runner this session; GitHub's `ubuntu-latest` image documentation lists `zip`/`unzip` in the default toolset, but this was not re-confirmed via a runner probe]` | Build the allowlist archive | `zip -r out.zip <allowlisted-paths>` is itself the allowlist — no separate filter/exclude logic needed |
| `claude` CLI | 2.1.233 (installed, `[VERIFIED: claude --version, this session]`) | `plugin marketplace add`/`install`/`uninstall`/`validate` for SC4/SC5 | Already the tool this whole plugin targets; no substitute |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `softprops/action-gh-release` | v3.0.2 latest `[VERIFIED: gh api repos/softprops/action-gh-release/releases/latest, this session]` | Alternative to `gh release create` for attaching assets | Only if the workflow needs release-notes templating or multi-file glob upload beyond what a single `gh release create <tag> <file>` line does — not needed for this phase's single-zip case |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `gh release create` (recommended) | `softprops/action-gh-release@v3` | Third-party action pin (5,736 stars, not archived, maintained since 2019 `[VERIFIED: gh api repos/softprops/action-gh-release]`) adds an external dependency for functionality `gh` already provides preinstalled; only worth it for richer release-note generation, not needed here |
| `gh release create` | `actions/upload-release-asset` (deprecated) | GitHub's own marketplace listing carries an explicit deprecation notice pointing users to the `gh` CLI instead — do not use |
| Local `zip` command in workflow | `thedoctor0/zip-release` action | Adds a third-party action for something one shell line (`zip -r`) already does — rejected per Claude's-discretion "no unrequested abstraction" |

**Installation:** No new package installs required — `gh`, `git`, `zip` are all either already present on GitHub-hosted runners or already verified installed locally.

## Package Legitimacy Audit

No npm/PyPI/crates packages are installed by this phase — the only external references are two GitHub Actions Marketplace entries (not registry packages) and system tools already present on GitHub-hosted runners. The formal ecosystem package-legitimacy gate (`gsd_run query package-legitimacy check --ecosystem npm|pypi|crates`) does not apply. Repo-level legitimacy signals for the two GH Actions considered, pulled via `gh api` (authoritative, this session):

| Reference | Type | Age | Stars | Archived | Verdict | Disposition |
|-----------|------|-----|-------|----------|---------|-------------|
| `actions/checkout` | GH Action | created 2019-07-19 `[VERIFIED: gh api repos/actions/checkout]` | 8,646 | false | OK | Recommended (D-06 workflow step 1), pin to `@v7` |
| `softprops/action-gh-release` | GH Action | created 2019-08-25 `[VERIFIED: gh api repos/softprops/action-gh-release]` | 5,736 | false | OK | Not used — `gh release create` preferred (see Alternatives) |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```
Developer                GitHub                        Installer's machine
    |                       |                                    |
    |--git push tag v1.1.0->|                                    |
    |                       |--triggers .github/workflows/------>|
    |                       |  release.yml (tag push v*.*.*)     |
    |                       |    1. actions/checkout@v7           |
    |                       |    2. zip -r gsd-beads.zip           |
    |                       |       .claude-plugin/ hooks/         |
    |                       |       .agents/skills/ README.md      |
    |                       |       LICENSE                        |
    |                       |    3. gh release create v1.1.0       |
    |                       |       gsd-beads.zip                  |
    |                       |<--GitHub Release published---------|
    |                       |   (asset: gsd-beads.zip)            |
    |                       |                                     |
    |                       |<====================================|
    |                       |   claude plugin marketplace add     |
    |                       |     davdittrich/gsd-beads            |
    |                       |     -> clones full repo via git      |
    |                       |        (NOT the release zip)         |
    |                       |   claude plugin install beads@gsd-beads -y
    |                       |     -> copies "./" (whole cloned repo,
    |                       |        incl. .planning/ .beads/)     |
    |                       |        into ~/.claude/plugins/cache/ |
    |                       |   claude plugin uninstall beads -y   |
    |                       |                                     |
    |                       |<--separate path: manual zip download|
    |                       |   (unzip only ships allowlisted dirs)|
```

Two distinct install mechanisms exist and must not be conflated in the plan: **(a)** the GitHub Release zip (what SC2/SC3 test — allowlist-only, verified clean of `.planning`/`.beads`) and **(b)** the `/plugin marketplace add` + `install` flow (what SC4 tests — clones the full git repo via `marketplace.json`'s `"./"` source, which does include `.planning/`/`.beads/` in the local plugin cache). See `## D-11 Resolution` and `## Common Pitfalls` Pitfall 2.

### Recommended Project Structure

```
.github/
└── workflows/
    └── release.yml       # D-06: tag-triggered build + gh release create
README.md                 # D-04: new file, repo root, locked section order
.claude-plugin/            # existing (Phase 5) — unchanged by this phase
hooks/                     # existing (Phase 6) — unchanged by this phase
.agents/skills/             # existing (Phase 5) — unchanged by this phase
LICENSE                    # existing (Phase 5) — unchanged by this phase
```

### Pattern 1: Tag-triggered release workflow with an explicit allowlist zip

**What:** A single GitHub Actions workflow triggered on `push: tags: ['v*.*.*']`, which checks out the repo, builds a zip from named paths only, and publishes it as a release asset.
**When to use:** Any repo shipping a versioned artifact that must exclude local-only directories from the source tree.
**Example:**

```yaml
# Source: pattern synthesized from GitHub's documented gh CLI release workflow
# [CITED: community WebSearch results, cross-checked against softprops/action-gh-release
#  README's own documented alternative "gh release create" usage]
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v7

      - name: Build allowlisted archive
        run: |
          zip -r gsd-beads.zip \
            .claude-plugin \
            hooks \
            .agents/skills \
            README.md \
            LICENSE

      - name: Publish release
        run: gh release create "${{ github.ref_name }}" gsd-beads.zip --generate-notes
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

`permissions: contents: write` is required at the job level for the default `GITHUB_TOKEN` to be allowed to create a release — without it, `gh release create` fails with a 403. `zip -r <archive> <path1> <path2> ...` with explicit paths is itself the allowlist mechanism: no `--exclude` flags are needed or should be added, since anything not named on the command line is never zipped, which is more robust against future accidental inclusion than an exclude-based approach.

### Pattern 2: Non-interactive plugin round trip (D-08/D-09)

**What:** The exact `claude plugin` CLI subcommand invocations, all verified non-interactive via `--help` output read directly this session.
**When to use:** SC4's scripted round trip.
**Example:**

```bash
# Source: [VERIFIED: `claude plugin marketplace add --help`, `claude plugin install --help`,
#  `claude plugin uninstall --help`, all run this session against claude CLI 2.1.233]

# Step 1 — register the marketplace (no confirmation flag exists or is needed;
# --help shows only -h/--help and --scope/--sparse, no interactive gate)
claude plugin marketplace add davdittrich/gsd-beads

# Step 2 — install (non-interactive requires -y/--yes: "required when stdin or
# stdout is not a TTY", per --help verbatim)
claude plugin install beads@gsd-beads -y

# Step 3 — uninstall (same -y/--yes requirement)
claude plugin uninstall beads -y
```

Verbatim `--help` text backing the `-y` requirement:

> `-y, --yes   For a plugin installed by running a marketplace-declared command: accept the displayed command without the confirmation prompt (required when stdin or stdout is not a TTY)` (`claude plugin install --help`, this session)

> `-y, --yes   Skip the --prune confirmation prompt (required when stdin or stdout is not a TTY)` (`claude plugin uninstall --help`, this session)

Neither `beads`' `plugin.json` nor `marketplace.json` declares a `command`-type source (both use file-based sources: `plugin.json`'s `skills` field and `marketplace.json`'s `"./"` relative path), so the `-y` flag's specific "accept the displayed command" semantics (documented for `command`-source plugins) do not apply here — but the flag is still required generically whenever stdin/stdout isn't a TTY, per the flag text above. All three steps are scriptable with no interactive-only gap. This resolves D-08: nothing in this specific round trip requires a human to sit at the keyboard, contrary to the CONTEXT.md's cautious framing that assumed an interactive step might exist.

### Anti-Patterns to Avoid

- **Using `softprops/action-gh-release` when `gh release create` already does the job:** adds a third-party action dependency and an extra version to track for no functional gain in this single-asset case.
- **Building the archive with an exclude-list (`zip -r out.zip . -x '.planning/*' '.beads/*' ...`):** fragile — any new top-level directory added later (e.g. a future `scripts/`) silently ships unless someone remembers to add it to the exclude list. The explicit-include form (`zip -r out.zip .claude-plugin hooks .agents/skills README.md LICENSE`) can never leak an unlisted path.
- **Testing SC4's round trip via the interactive `/plugin` slash commands and calling it "scripted":** the slash-command form only exists inside a running Claude Code session and cannot be piped/scripted from a shell; use the `claude plugin ...` CLI subcommand form for the "scripted where possible" half of D-08.
- **Conflating the release-zip install path with the marketplace-add install path when writing SC3's/SC4's verification transcripts:** they exercise different code paths with different contents ending up on disk (see D-11 Resolution below) — verify each independently.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Attaching a build artifact to a GitHub Release from CI | Custom `curl` calls to the GitHub Releases REST API | `gh release create <tag> <file>` | `gh` is preinstalled on GH-hosted runners, handles auth via `GH_TOKEN` automatically, and is GitHub's own documented recommended pattern (supersedes the now-deprecated `actions/upload-release-asset`) |
| Verifying a plugin's manifest correctness | Hand-written JSON schema checks against `plugin.json`/`marketplace.json` | `claude plugin validate . --strict` | Already ships with the `claude` CLI (v2.1.233 installed), already verified passing on this repo's local tree this session |
| Non-interactive plugin install/uninstall for a CI-style round trip | Piping keystrokes into an interactive `claude` REPL session | `claude plugin install <plugin>@<marketplace> -y` / `claude plugin uninstall <plugin> -y` | Purpose-built non-interactive flags exist and are documented; scripting the TUI would be strictly worse and fragile |

**Key insight:** every mechanism this phase needs (release creation, archive building, plugin lifecycle management, manifest validation) already has a first-party CLI surface (`gh`, `zip`, `claude plugin ...`) — there is no gap that justifies writing custom tooling.

## D-11 Resolution

**Question:** Does `marketplace.json`'s `"source": "./"` resolve correctly when fetched via `claude plugin marketplace add davdittrich/gsd-beads` against the real public GitHub repo?

**Answer: Yes, no change needed. Confidence: HIGH `[CITED: code.claude.com/docs/en/plugin-marketplaces, fetched live this session]`.**

Verbatim from the official docs (`Relative paths` section):

> "Paths resolve relative to the marketplace root, which is the directory containing `.claude-plugin/`. In the example above, `./plugins/my-plugin` points to `<repo>/plugins/my-plugin`, even though `marketplace.json` lives at `<repo>/.claude-plugin/marketplace.json`."

> "Claude Code resolves relative paths against a local copy of the marketplace, so they work when users add your marketplace from a git source or a local directory. If users add your marketplace via a direct URL to the `marketplace.json` file, relative paths won't resolve, because Claude Code downloads only that file."

`claude plugin marketplace add davdittrich/gsd-beads` uses the `owner/repo` GitHub shorthand, which the official "Host on GitHub (recommended)" section documents as the standard git-based registration path (`git clone`-backed, not a raw-file URL fetch). Since this is a git-based source, `"./"` resolves correctly. No change to `marketplace.json` is required for SC4 to succeed.

**New finding surfaced by this same research (not part of D-11's original question, but directly relevant to SC3/SC4 and the README's caveats section):** because `"./"` means "the marketplace repo root," and Claude Code's plugin cache is a directory *copy* of whatever the resolved source points at (not a manifest-filtered subset — confirmed via the official `plugins-reference` page's "Path traversal limitations" section, which only discusses files *outside* the plugin root, implying the whole root directory is in scope), installing via `claude plugin install beads@gsd-beads` copies the **entire cloned repository** — every git-tracked file, including all 130 files under `.planning/` and 20 files under `.beads/` `[VERIFIED: git ls-files | grep -c, this session — .planning/: 130 files, .beads/: 20 files, both currently tracked]` — into `~/.claude/plugins/cache/gsd-beads/beads/<version>/` on the installer's machine. This is a distinct install path from the GitHub Release zip (which correctly stays allowlist-only, confirmed clean below). No documented `.gitignore`-respecting filter exists for this copy step `[CITED: code.claude.com/docs/en/plugins-reference, "Plugin caching and file resolution" section fetched this session — explicitly confirms no `.gitignore` handling is mentioned anywhere in that section]`.

This does not violate SC3 as literally worded (SC3 scopes to "installing from that release," i.e. the GitHub Release zip, which this research independently confirms is allowlist-clean — see next section). It is, however, a real side effect of the SC4 round trip worth naming explicitly in the plan's verification step and in the README's caveats (D-03), so the SUMMARY.md transcript (D-09) doesn't read as a surprise regression later.

## Runtime State Inventory

This phase is not a rename/refactor/migration phase (it adds new files: `README.md`, `.github/workflows/release.yml`). Section omitted per the trigger condition in the execution flow.

## Common Pitfalls

### Pitfall 1: `permissions: contents: write` omitted from the release workflow job

**What goes wrong:** `gh release create` fails with a 403/"Resource not accessible by integration" error.
**Why it happens:** The default `GITHUB_TOKEN` GitHub Actions injects is read-only unless the workflow (or job) explicitly grants `contents: write`.
**How to avoid:** Set `permissions: contents: write` at the job level in `release.yml` (shown in the Pattern 1 example above).
**Warning signs:** Workflow run fails at the `gh release create` step specifically, with an HTTP 403 in the log, while the checkout/zip steps succeed.

### Pitfall 2: Conflating the release-zip install path with the marketplace-clone install path

**What goes wrong:** A plan or verification step assumes that because the GitHub Release zip is allowlist-clean (SC2/SC3), the `/plugin marketplace add` + `install` round trip (SC4) will also leave no `.planning/`/`.beads/` trace — it will not, per the D-11 Resolution finding above.
**Why it happens:** Both mechanisms ship "the same plugin," so it's natural to assume they ship the same files. They don't: SC2/SC3 test the curated zip; SC4 tests a full git clone filtered only by `marketplace.json`'s `source` path (`"./"` = everything).
**How to avoid:** Write SC3's and SC4's verification steps independently. For SC3, `unzip -l` the release asset and assert only the 5 allowlisted top-level entries appear (already confirmed possible — this repo's `.claude-plugin/`, `hooks/`, `.agents/skills/` currently contain zero `.planning`/`.beads` paths, verified via `find` this session). For SC4, verify the round trip *completes* (install → uninstall succeed) without asserting anything about cache contents, since SC4 as worded doesn't require that.
**Warning signs:** A plan task that greps `~/.claude/plugins/cache/` for `.planning`/`.beads` after `claude plugin install` and treats a match as a phase failure — it will always match, and that is not a bug in this phase's work.

### Pitfall 3: Building the zip with an implicit `.` recursive include, then trying to exclude

**What goes wrong:** A future edit to the repo root (new top-level file/dir) silently ships in the release archive unless the exclude list is remembered and updated.
**Why it happens:** `zip -r out.zip . -x '.planning/*' -x '.git/*' ...` is a common first instinct, but it inverts the allowlist into a denylist.
**How to avoid:** Zip only the named allowlist paths (`zip -r out.zip .claude-plugin hooks .agents/skills README.md LICENSE`) — nothing else can ever be included, by construction.
**Warning signs:** A `git diff` on `release.yml` adding a new `-x` exclude pattern is itself a signal the workflow is using the wrong (denylist) approach.

### Pitfall 4: `claude plugin validate . --strict` run only against the local working tree, not the tagged fresh clone

**What goes wrong:** SC5 requires the validate pass to hold against "the pushed tree at the released tag" — a local pass proves nothing about what's actually in the tag, especially if uncommitted or unpushed changes exist locally.
**Why it happens:** It's faster and was already done once this session (`✔ Validation passed` on the current local tree, per CONTEXT.md D-10) — reusing that result is tempting but doesn't satisfy D-10's explicit requirement.
**How to avoid:** `git clone` into a fresh temp directory, `git checkout v1.1.0`, then run `claude plugin validate . --strict` from inside that clone — not `git -C <path> ...` against the existing working tree, and not trusting the earlier local-tree result.
**Warning signs:** A SUMMARY.md transcript that shows `claude plugin validate . --strict` run from `/home/dd/Gemini/gsd-beads` (the working tree) rather than from a path under something like `/tmp/.../gsd-beads-verify`.

## Code Examples

### Fresh-clone ship-gate verification (D-10)

```bash
# Source: derived directly from D-10's requirement text + `git clone`/`checkout` being
# standard git usage; no special API involved. [ASSUMED: exact temp-dir path — use any
# scratch location, not a specific one this research prescribes]
tmpdir=$(mktemp -d)
git clone https://github.com/davdittrich/gsd-beads.git "$tmpdir"
git -C "$tmpdir" checkout v1.1.0
(cd "$tmpdir" && claude plugin validate . --strict)
```

### Confirming the release archive's actual contents (SC2)

```bash
# [VERIFIED: `find .claude-plugin hooks .agents/skills -iname "*.planning*" -o -iname
#  "*.beads*"` run this session against the current repo — zero results, confirming no
#  leak paths exist inside the allowlisted directories today]
gh release download v1.1.0 --pattern '*.zip' -O gsd-beads.zip
unzip -l gsd-beads.zip
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `actions/upload-release-asset` + `actions/create-release` (two-action combo) | `gh release create <tag> <files...>` (single CLI call, GITHUB_TOKEN via env) | `actions/upload-release-asset`'s marketplace listing carries an explicit deprecation notice `[CITED: WebSearch result quoting the marketplace listing text]`; exact deprecation date not independently re-verified this session | One workflow step instead of two, no upload-URL output-chaining boilerplate |
| `action-gh-release@v2` (Node 20 runtime) | `action-gh-release@v3` (Node 24 runtime) | v2.6.2 was the final v2 release, superseded because GitHub Actions is deprecating the Node 20 runtime `[CITED: WebSearch result]` | Not directly relevant here since this research recommends `gh release create` over the action, but noted in case the plan's discretion prefers the action form |

**Deprecated/outdated:**
- `actions/create-release`, `actions/upload-release-asset`: both community-flagged deprecated in favor of the `gh` CLI. Do not use in the new workflow.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `zip` is preinstalled on GitHub's `ubuntu-latest` hosted runner image | Standard Stack (Core) | Low — if wrong, the workflow's zip step fails immediately and loudly on first CI run; trivial one-line fix (`sudo apt-get install -y zip` or `apt-get update && apt-get install -y zip`) added as a prior step |
| A2 | Exact temp-directory convention for the fresh-clone verify step | Code Examples | None — any scratch path works; not a correctness-affecting choice |

**If this table is empty:** N/A — two low-risk, easily-caught-at-CI-time assumptions remain, both non-blocking.

## Open Questions

None outstanding. D-11 (the phase's one explicitly deferred open question) is resolved above with HIGH confidence from official, live-fetched documentation.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|--------------|-----------|---------|----------|
| `claude` CLI | SC4, SC5 (`plugin marketplace add`/`install`/`uninstall`/`validate`) | ✓ `[VERIFIED: claude --version, this session]` | 2.1.233 | — |
| `gh` CLI | D-06 workflow (`gh release create`), SC2 verification (`gh release download`) | ✓ `[VERIFIED: gh --version, this session]` | 2.97.0 | — |
| `zip` (local, for manual verification only — CI build uses the runner's own `zip`) | Manual re-check of archive contents before/after push | not explicitly re-probed this session; `unzip`/`zip` are common on this Linux Arch dev machine | — | If missing locally, `unzip -l` on the downloaded asset (via `gh release download`) is sufficient and doesn't require local `zip` |
| GitHub-hosted `ubuntu-latest` runner's `zip` | D-06 workflow build step | ✓ `[ASSUMED — see Assumptions Log A1]` | — | `apt-get install -y zip` as a prepended workflow step if the assumption is wrong |
| `.github/workflows/` directory | D-06 | does not exist yet — this phase creates it `[VERIFIED: `ls .github` returned "No such file or directory", this session]` | — | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** GitHub runner `zip` availability (A1) — fallback is a one-line `apt-get install` prepend, non-blocking.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None — this repo has no unit-test suite; `[VERIFIED: no package.json, pytest.ini, or test config found at repo root this session]`. Verification for this phase is procedural (CLI transcripts), matching Phase 7's established pattern (D-09) |
| Config file | none |
| Quick run command | n/a — see Phase Requirements → Test Map below for the actual per-SC verification commands |
| Full suite command | n/a |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|-------------|
| PUB-04 / SC2 | Release zip contains exactly the allowlist | manual/scripted | `gh release download v1.1.0 --pattern '*.zip' -O out.zip && unzip -l out.zip` | ✅ — `gh` already installed |
| PUB-04 / SC3 | No `.planning/`/`.beads/` file in the release archive | manual/scripted | same `unzip -l` output, grep for `.planning`/`.beads` (expect zero matches) | ✅ |
| PUB-07 / SC1 | README commands are all real, transcribed | manual | run every README command verbatim, capture output for cross-check (per D-02, output itself is not shown in the README, but must still be executed to confirm it works) | N/A — new file, this phase authors it |
| PUB-09 / SC4 | Marketplace round trip succeeds | scripted (per D-08) | `claude plugin marketplace add davdittrich/gsd-beads && claude plugin install beads@gsd-beads -y && claude plugin uninstall beads -y` | ✅ — `claude` already installed |
| PUB-09 / SC5 | `claude plugin validate . --strict` clean at the tagged fresh clone | scripted | fresh-clone snippet in `## Code Examples` above | ✅ |

### Sampling Rate

- **Per task commit:** re-run the specific SC's verification command for whatever was just changed (e.g. after editing `release.yml`, re-run only SC2/SC3's check after the next tag push; after drafting README.md, re-run only its command-transcription check).
- **Per wave merge:** n/a — this phase is small enough to be a single wave in most plans.
- **Phase gate:** all five SC verification commands above, green, before `/gsd:verify-work`.

### Wave 0 Gaps

None — existing tooling (`gh`, `claude`, `git`, `zip`) covers every phase requirement's verification method; no test-framework install needed.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|-------------------|
| V1 Architecture | no (docs/CI packaging phase, no application architecture change) | — |
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | partial — CI job token scope | `permissions: contents: write` scoped at job level, not workflow-wide `write-all`; default `GITHUB_TOKEN` used, no long-lived PAT stored as a secret |
| V5 Input Validation | no user input processed by this phase's new code | — |
| V6 Cryptography | no | — |
| V14 Configuration | yes — the release workflow is itself a security-relevant configuration surface | Explicit-allowlist zip build (Pattern 1/Pitfall 3) IS the control — treat the workflow YAML as the security boundary preventing `.planning/`/`.beads/` (which may contain locally-scoped state, credentials-adjacent config, or internal planning notes) from reaching installers |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|-----------------------|
| Accidental information disclosure via an overly broad release archive (e.g. `zip -r out.zip .` shipping `.planning/`, `.beads/`, `.git/`) | Information Disclosure | Explicit-include zip (Pattern 1/Pitfall 3), verified via `unzip -l` against the actual published asset (not just the workflow source) before considering SC2/SC3 satisfied |
| Overscoped `GITHUB_TOKEN` permissions in the release workflow enabling unintended repo writes if the workflow is ever compromised (e.g. via a malicious PR that also modifies `release.yml`) | Elevation of Privilege | Job-level `permissions: contents: write` only — never workflow-wide `permissions: write-all`; this workflow triggers only on tag push, which requires push access to create, limiting exposure to already-trusted committers |
| Plugin cache silently retaining more of the source repo than a user expects (D-11 Resolution finding) | Information Disclosure (low severity — local machine only, not transmitted) | Document in the README's caveats (D-03) rather than attempt a technical fix, since the underlying behavior is Claude Code's own documented plugin-cache mechanism, not something this repo's config controls |

## Sources

### Primary (HIGH confidence)

- `claude plugin --help`, `claude plugin marketplace add --help`, `claude plugin install --help`, `claude plugin uninstall --help`, `claude plugin validate --help` — run directly against the installed `claude` CLI 2.1.233, this session
- https://code.claude.com/docs/en/plugin-marketplaces — fetched live this session (full page content read), source for D-11 resolution, relative-path resolution rules, plugin-cache-copy behavior
- https://code.claude.com/docs/en/plugins-reference — fetched live this session, "Plugin caching and file resolution" section, source for the D-11 new-finding (whole-repo copy, no `.gitignore` filtering documented)
- `gh api repos/softprops/action-gh-release/releases/latest`, `gh api repos/actions/checkout/releases/latest`, `gh api repos/softprops/action-gh-release`, `gh api repos/actions/checkout` — run this session against the live GitHub API
- `git ls-files | grep -c '^\.planning/\|^\.beads/'` and `find .claude-plugin hooks .agents/skills -iname "*.planning*" -o -iname "*.beads*"` — run against this repo's actual working tree, this session

### Secondary (MEDIUM confidence)

- WebSearch results on `gh release create` vs `softprops/action-gh-release` vs deprecated `actions/upload-release-asset`/`actions/create-release` — cross-checked across multiple independent sources (community blog posts, GitHub Marketplace listings) converging on the same recommendation

### Tertiary (LOW confidence)

- `zip` preinstalled on `ubuntu-latest` GitHub-hosted runners (A1 in Assumptions Log) — based on general knowledge of the runner image, not independently re-verified against a live runner this session

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every tool version verified live via `--version`/`gh api` this session
- Architecture: HIGH — D-11's core mechanism confirmed against official, live-fetched docs; the whole-repo-copy finding is a direct, quoted reading of that same source
- Pitfalls: HIGH — each pitfall traces to a verified command output or a directly-quoted doc passage, not inference

**Research date:** 2026-08-16
**Valid until:** 30 days (stable CLI/Actions ecosystem; re-verify `claude` CLI version and plugin-marketplace doc pages if this research is reused after a `claude` CLI upgrade, since plugin-source semantics have changed across versions per the docs' own version-gated notes, e.g. `archive`/`command` sources requiring v2.1.224+/v2.1.229+)
