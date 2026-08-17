# Phase 12: Ship ponytail-everywhere and sota-numerics plugins publicly - Research

**Researched:** 2026-08-17
**Domain:** Claude Code plugin marketplace distribution (multi-repo split of an existing monorepo)
**Confidence:** HIGH (primary research question resolved against official Anthropic docs, fetched and quoted verbatim this session; repo-split mechanics verified against this repo's own files and `gh`/`git`/`claude` CLI help text)

## Summary

This phase splits two already-complete, already-dogfooded plugin subdirectories
(`ponytail-everywhere/`, `sota-numerics/`) out of `gsd-beads` into their own standalone public
GitHub repos, then repoints `gsd-beads`' shared `.claude-plugin/marketplace.json` at those repos
instead of local paths. The primary open question — what JSON shape a cross-repo `plugins[]`
`source` entry takes — is fully resolved: it is a `github`-type source object, `{"source":
"github", "repo": "owner/repo"}`, confirmed verbatim from Anthropic's official
`plugin-marketplaces` doc page fetched live this session.

The mechanical split itself is the harder part. Unlike Phase 7 (which ran `gh repo create
--source=.` in-place against `gsd-beads` itself, already a standalone git repo), `ponytail-everywhere/`
and `sota-numerics/` are subdirectories with **no `.git` of their own** — `gh repo create --source=<dir>`
requires the source directory to already be a git repository. The planner must sequence: copy each
subdirectory's tracked files to a location **outside** `gsd-beads`' working tree, `git init` fresh
there (D-03: no history extraction), commit, `gh repo create --source=<path> --public --push`, verify
from a clean clone, only then `git rm -r` the subdirectory from `gsd-beads` and edit
`marketplace.json`. Initializing `git init` directly inside the subdirectory in place is an anti-pattern
(nested/embedded git repo warning from the parent's git) and must be avoided.

A concrete, verified bug was found during research: both plugins' `tests/test-session-start.sh`
compute `REPO_ROOT` via `dirname "$0"/../..` — two levels up from `tests/`, correct only because
today `tests/` sits two levels below the `gsd-beads` repo root (`<repo>/ponytail-everywhere/tests/`).
Once the subdirectory becomes a standalone repo root, `tests/` is only **one** level below the new
repo root; the existing `../..` climbs one level too far, outside the new repo entirely, and every
`SCRIPT=`/`PLUGIN_DIR=` path built from `REPO_ROOT` breaks. This is a required code edit, not a
copy-as-is move — it was not called out in CONTEXT.md's "moves as-is" language, which applied
specifically to `plugin.json`.

**Primary recommendation:** Use a `github`-type marketplace source (`{"source": "github", "repo":
"davdittrich/ponytail-everywhere"}`, no `ref`/`sha` pin — matches this repo's existing unpinned
Directory-source style and gets updates on every push, consistent with D-05's independent versioning).
Extract each subdirectory to a fresh location, `git init` there, push via `gh repo create --source=<path>
--public --push`, fix the two `REPO_ROOT` off-by-one bugs before pushing, then remove the subdirectories
from `gsd-beads` and edit `marketplace.json` last.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Standalone plugin repo creation (`ponytail-everywhere`, `sota-numerics`) | Git/GitHub (external repo) | — | Each plugin becomes its own git-hosted unit; no application tiers involved, this is a distribution/packaging concern |
| Marketplace catalog (`marketplace.json`) | `gsd-beads` repo (marketplace host) | — | Stays in `gsd-beads` per D-02; only the two `source` fields change from local path to `github` object |
| Plugin runtime (hooks, capability fragments) | Claude Code plugin cache (`~/.claude/plugins/cache`) | Installer's project (`.planning/config.json` for `ponytail.enabled`/`sota-numerics.enabled`) | Unchanged by this phase — D-04 confirms `.gsd/capabilities/<id>/` dogfood copies at `gsd-beads` root are a separate, untouched concern |
| Test harness (`tests/test-session-start.sh`, `test_check_alternatives.py`) | New repo root (post-split) | — | Must be edited during extraction (bash `REPO_ROOT` bug) or verified path-safe (Python test already resolves correctly relative to its own file, no fix needed) |

## User Constraints

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Each of the 3 plugins gets its own separate public GitHub repo — `ponytail-everywhere`
  and `sota-numerics` are NOT staying as subdirectories of `gsd-beads`. One-way door.
- **D-02:** `gsd-beads` keeps hosting the shared `marketplace.json`. `beads-lifecycle` stays a local
  Directory source (`"./"`). `ponytail-everywhere` and `sota-numerics` switch to git-hosted sources.
  Exact schema was a research question (now resolved — see Standard Stack / Code Examples below).
- **D-03:** Fresh init, no history extraction. Do NOT `git filter-repo` Phase 10/10.1/11 commit
  history out of `gsd-beads`; the two new repos start clean at current file state.
- **D-04:** Once each new repo is live and pushed, remove `ponytail-everywhere/` and
  `sota-numerics/` subdirectories from `gsd-beads` — no dual-copy authoring source left. The
  repo-root dogfood copies (`.gsd/capabilities/ponytail/`, `.gsd/capabilities/sota-numerics/`) are
  untouched — do not confuse with the removed plugin subdirectories.
- **D-05:** Independent versioning per repo, no coupling to `gsd-beads`' version/tag cadence.
- **D-06:** `gsd-beads`' existing ad-hoc `v1.2.0` tag is left alone; this phase does not touch it.
- **D-07:** Neither new plugin needs a GitHub Release archive — a plugin's own repo IS the clean
  scope already. Marketplace install is the only install path needed.
- **D-08:** `gsd-beads`' `.github/workflows/release.yml` needs no change — it keeps building only
  the `beads-lifecycle` archive.
- **D-09:** Each new repo's README matches `beads-lifecycle`'s full structure (Phase 8 PUB-07
  pattern): purpose, requirements, install, uninstall, caveats, license, gsd-core link.
- **D-10:** Each new repo needs the same full proof Phase 8 did: `claude plugin validate . --strict`
  clean on the pushed repo, AND a real `/plugin marketplace add` → `/plugin install` →
  `/plugin uninstall` round trip against the public repo.

### Claude's Discretion
- Exact repo names (default: `davdittrich/ponytail-everywhere`, `davdittrich/sota-numerics`) —
  confirm with user before creating if any doubt.
- Whether `gsd-beads` itself needs a new tag/release once `marketplace.json` is updated.
- Starting version number for each new repo (`v0.1.0` vs `v1.0.0`) — either defensible.
- Order of operations across the two plugins (parallel vs sequential) — no dependency between them.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. D-01's mid-discussion repo-topology revision is a
correction to the phase's own scope, not new work deferred elsewhere.
</user_constraints>

<phase_requirements>
## Phase Requirements

No formal requirement IDs exist for this project; traceability is via CONTEXT.md decisions
D-01..D-10 (all reproduced verbatim above). Every decision maps directly to a task the planner
must schedule:

| Decision | Research Support |
|----------|------------------|
| D-01, D-03 | Code Examples §"Extracting a subdirectory into a standalone repo" — the `git init` + `gh repo create --source` sequence, verified against `gh repo create --help` and this repo's existing tracked-file state |
| D-02 | Code Examples §"Marketplace github-source entry" — exact JSON confirmed from official docs |
| D-04 | Runtime State Inventory below — confirms what does/doesn't need touching |
| D-09 | Code Examples §"README structure" — extracted from this repo's own README.md (Phase 8 precedent) |
| D-10 | Common Pitfalls §"validate --strict semantics" and §"marketplace round trip" |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version (verified this session) | Purpose | Why Standard |
|------|-----------|---------|--------------|
| `gh` CLI | 2.97.0 | Create + push new GitHub repos, verify visibility/remote | Official GitHub CLI, already used identically in Phase 7 |
| `git` | 2.55.0 | Fresh `git init`, commit, push | Standard, no alternative |
| `claude` CLI | 2.1.233 (Claude Code) | `claude plugin validate . --strict` pre-publish gate | Only tool that runs Claude Code's own plugin manifest validator |

No new libraries or packages are introduced by this phase — it is pure repo/file operations plus
two already-written plugin trees. `npm view`/`pip index` verification does not apply (no package
installs).

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `github`-type marketplace source | `git-subdir` type (pointing `gsd-beads` itself with a `path`) | Would let the two plugins keep living as subdirectories of `gsd-beads` with no separate repos — directly contradicts locked D-01, not applicable |
| `git init` in a scratch copy outside `gsd-beads` | `git init` in-place inside the subdirectory, then `gh repo create --source=./ponytail-everywhere` | In-place `git init` creates a nested/embedded git repository inside `gsd-beads`' own working tree while the subdirectory's files are still tracked by the parent repo — `git status` in `gsd-beads` reports an "embedded git repository" warning and a stray `git add` in the parent risks committing a broken gitlink. Extracting to a location outside the tree avoids this entirely. |
| Unpinned `github` source (no `ref`/`sha`) | Pin `ref`/`sha` for reproducibility | This repo's existing 3 marketplace entries are all unpinned (`"./"`-style, always latest); D-05's independent-versioning framing and D-02's "matches the existing style" intent favor staying unpinned — Claude Code resolves the unpinned source's commit SHA as the version, so updates flow automatically on every push (per official docs §"Version resolution") |

## Package Legitimacy Audit

**Not applicable.** This phase installs no new npm/pip/cargo packages — it relocates existing,
already-verified plugin code (Phase 10/11 shipped) into new repos and edits one JSON file. No
`package-legitimacy check` run was needed.

## Architecture Patterns

### System Architecture Diagram

```
gsd-beads (git repo, unchanged root)
  .claude-plugin/marketplace.json  ── hosts 3 entries ──┐
       │                                                 │
       ├─ beads-lifecycle  → source: "./"  (unchanged, local Directory)
       ├─ ponytail-everywhere → source: {github, repo: "davdittrich/ponytail-everywhere"}  (NEW)
       └─ sota-numerics    → source: {github, repo: "davdittrich/sota-numerics"}  (NEW)
                                                 │
                    ┌────────────────────────────┴────────────────────────────┐
                    ▼                                                          ▼
     github.com/davdittrich/ponytail-everywhere        github.com/davdittrich/sota-numerics
     (NEW public repo, fresh git history)               (NEW public repo, fresh git history)
     .claude-plugin/plugin.json   ← moved as-is          .claude-plugin/plugin.json   ← moved as-is
     hooks/{hooks.json,session-start.sh,                 hooks/{...same pattern...}
       gsd-tools.sh,capability-auto-install.sh}          .gsd/capabilities/sota-numerics/
     .gsd/capabilities/ponytail/                         tests/ (bash + Python; REPO_ROOT FIXED)
     tests/ (bash smoke test; REPO_ROOT FIXED)
                    │                                                          │
                    └──────────── user: /plugin marketplace add ───────────────┘
                                  davdittrich/gsd-beads
                                  /plugin install ponytail-everywhere@gsd-beads
                                  /plugin install sota-numerics@gsd-beads
                                          │
                                          ▼
                         ~/.claude/plugins/cache/gsd-beads/<plugin>/<version>/
                         (Claude Code copies each plugin here; hooks read
                          ${CLAUDE_PLUGIN_ROOT} at runtime, portable already)
```

### Recommended Extraction Sequence (per plugin, repeat for the other)
```
1. mkdir -p /tmp/<plugin>-extract && cp -r <repo>/<plugin>/. /tmp/<plugin>-extract/
2. Fix REPO_ROOT bug in /tmp/<plugin>-extract/tests/test-session-start.sh (see Pitfall 1)
3. cd /tmp/<plugin>-extract && git init -b main
4. Add LICENSE (MIT, copied verbatim from gsd-beads root)
5. git add -A && git commit -m "..."   (D-03: single fresh-init commit, no imported history)
6. gh repo create davdittrich/<plugin> --public --source=. --push
7. Fresh-clone verify (Phase 7 pattern): claude plugin validate . --strict clean;
   /plugin marketplace add / install / uninstall round trip (D-10)
8. Only after 7 passes: cd <repo> && git rm -r <plugin>/ && edit marketplace.json && commit
```

### Anti-Patterns to Avoid
- **`git init` inside the still-tracked subdirectory of `gsd-beads`:** creates a nested/embedded
  git repository the parent repo's git flags with a warning; extract to a separate location first.
- **Editing `marketplace.json` before the new repo passes D-10's validate+round-trip gate:** if the
  new repo push fails or `claude plugin validate --strict` fails on it, a premature marketplace edit
  points installers at a broken source. Sequence marketplace.json last, per Phase 7's own precedent
  of gating the irreversible/external step behind local verification.
- **Reusing Phase 7's `--source=.` form literally:** Phase 7 ran that command from `gsd-beads`' own
  root (already a git repo being republished in place). For this phase, `--source` must point at the
  extraction location (`/tmp/<plugin>-extract`, or wherever staged), not `.` inside `gsd-beads`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-repo plugin discovery | A custom fetch/download shim in `marketplace.json` | The documented `github`-type `source` object | Claude Code natively resolves `{"source": "github", "repo": "owner/repo"}` — no custom automation needed, verified against official docs |
| New-repo creation from existing local files | Manual `git remote add` + empty-repo dance | `gh repo create --source=<path> --public --push` | One command creates the repo, wires the remote, and pushes; documented and already the Phase 7 precedent in this repo |

**Key insight:** every mechanism this phase needs (cross-repo marketplace source, repo creation
from existing local content, `--strict` validation) is already documented, first-party tooling —
no library, wrapper, or automation script is warranted.

## Runtime State Inventory

> Included because D-04 requires removing tracked subdirectories from `gsd-beads` — a structural
> extraction, not a pure add.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no database, no Dolt/beads state inside `ponytail-everywhere/` or `sota-numerics/` | None |
| Live service config | None — the only "live" config is `marketplace.json` itself, already the phase's explicit target (D-02) | Code edit, sequenced last (see extraction sequence) |
| OS-registered state | None found | None |
| Secrets/env vars | None — both plugins are stdlib-only (bash + Python 3), no API keys or tokens | None |
| Build artifacts | `sota-numerics/tests/__pycache__/` — untracked already (`.gitignore` line 1: `__pycache__/`, verified `git ls-files sota-numerics/tests/__pycache__/` returns empty) | None — already excluded, new repo needs its own `__pycache__/`/`*.pyc` gitignore lines carried over |
| Machine-local capability copies | `~/.gsd/capabilities/ponytail/`, `~/.gsd/capabilities/sota-numerics/` (global-scope installs, per Phase 10.1 D-05) and this repo's own `.gsd/capabilities/<id>/` dogfood copies | **Explicitly out of scope per D-04** — do not touch; these are separate from the plugin subdirectories being removed |
| Cross-reference comments | `hooks/capability-auto-install.sh` in BOTH plugins carries a header comment naming the *sibling* plugin by relative path (`"see ponytail-everywhere/hooks/capability-auto-install.sh for the byte-identical sibling copy"` in `sota-numerics`'s copy, and the mirror in `ponytail-everywhere`'s) — becomes a stale/dangling reference once the two plugins are separate repos with no sibling directory. Not functionally broken (the script never reads that path at runtime), but confusing to a reader of the standalone repo. | Optional cleanup: reword the comment to drop the sibling-repo relative path, or leave as historical note — planner's call, not blocking |

**Canonical question answered:** after `git rm -r ponytail-everywhere/ sota-numerics/` in `gsd-beads`,
nothing outside those two directories references them except `marketplace.json` (the phase's own
edit target) and this repo's `.gsd/capabilities/<id>/` dogfood copies, which are a separate,
explicitly-untouched concern per D-04.

## Common Pitfalls

### Pitfall 1: `REPO_ROOT` off-by-one in `tests/test-session-start.sh` after extraction
**What goes wrong:** Both `ponytail-everywhere/tests/test-session-start.sh` (line 7) and
`sota-numerics/tests/test-session-start.sh` (line 8) compute:
```
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
```
verified by direct `Read` this session. Today `dirname "$0"` resolves to
`<gsd-beads>/ponytail-everywhere/tests` (or the `sota-numerics` equivalent), so `../..` climbs
exactly to `<gsd-beads>` — correct today, because the plugin directory sits **two** levels below
the enclosing repo root. `SCRIPT="$REPO_ROOT/ponytail-everywhere/hooks/session-start.sh"` and
`PLUGIN_DIR="$REPO_ROOT/ponytail-everywhere"` (verified, same file, lines 8-9) both depend on that.

**Why it happens:** Once the subdirectory becomes a standalone repo root, `tests/` sits only
**one** level below the new repo root. `../..` from `tests/` now climbs one level above the new
repo entirely (into whatever directory contains it, e.g. `/tmp` or a user's projects folder),
and `$REPO_ROOT/ponytail-everywhere/...` / `$REPO_ROOT/sota-numerics/...` no longer exist there.

**How to avoid:** Before pushing either new repo, edit the test script to reflect the new depth:
```bash
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"     # one level up, not two
SCRIPT="$REPO_ROOT/hooks/session-start.sh"          # no plugin-name segment
PLUGIN_DIR="$REPO_ROOT"                             # the repo root IS the plugin
```
Apply identically to both plugins' copies (`sota-numerics/tests/test-session-start.sh` lines 8-10
carry the exact same pattern, verified by `Read` this session).

**Warning signs:** Running `bash tests/test-session-start.sh` in the extracted repo before pushing
fails immediately with "No such file or directory" on the `session-start.sh` invocation — catch
this in the extraction sequence's local-verification step, before `gh repo create`.

**Not affected:** `sota-numerics/tests/test_check_alternatives.py` (line 17-19) resolves its script
path via `Path(__file__).resolve().parent.parent / ".gsd" / "capabilities" / ...` — one level up
from `tests/`, correct both today (as a subdirectory) and after extraction (as a repo root).
Verified by `Read` this session; no fix needed for this file.

### Pitfall 2: `claude plugin validate --strict` semantics — the flag promotes warnings, not a separate check mode
**What goes wrong:** Assuming `--strict` runs additional checks beyond what plain `claude plugin
validate .` runs.
**Why it happens:** The flag's actual behavior (confirmed via official `plugins-reference` docs,
fetched this session): unrecognized/misspelled top-level fields in `plugin.json` are **warnings**
by default and still pass validation; `--strict` promotes those warnings to hard errors. It is the
same check, run in a stricter pass/fail mode — not new checks.
**How to avoid:** Run `claude plugin validate . --strict` from each new repo's root (which IS the
plugin root post-extraction — no subdirectory ambiguity, unlike `gsd-beads`' own root which mixes
plugin files with `.planning/`/`.beads/`). Since `plugin.json` already has exactly the standard
fields (`name`, `version`, `description`, `author`, `license` — verified by `Read` this session,
no unrecognized fields), `--strict` is expected to pass clean on both, matching CONTEXT.md's
expectation that no analogous `gsd-beads`-root-style exception applies to the new repos.
**Warning signs:** A stray field left over from copy-paste (e.g. a `metadata` key with a non-object
value) would only surface under `--strict`, not plain `validate` — always test both plugin repos
with `--strict`, never skip it because plain `validate` passed.

### Pitfall 3: `gh repo create --source` requires an *already-initialized* git repo
**What goes wrong:** Running `gh repo create davdittrich/ponytail-everywhere --public
--source=ponytail-everywhere --push` directly from `gsd-beads`' root, expecting `gh` to `git init`
the subdirectory itself.
**Why it happens:** `gh repo create --help` (verified this session): "To create a remote repository
from an existing local repository, specify the source directory with `--source`." The subdirectory
has no `.git` of its own — it's tracked entirely within `gsd-beads`' object database.
**How to avoid:** Extract to a fresh location, `git init` there explicitly, `git add -A && git
commit` (this is D-03's "fresh init" step, not an extra one), only then run `gh repo create
--source=<extracted-path> --public --push`.
**Warning signs:** `gh repo create --source=<subdir-still-inside-gsd-beads>` errors immediately
(no `.git` found) rather than silently doing the wrong thing — fails loud, easy to catch.

### Pitfall 4: Marketplace `source` object shape — string vs object, and field name collision
**What goes wrong:** Writing `"source": "github:owner/repo"` (a string) or `"source": {"repo":
"owner/repo"}` (missing the nested `"source": "github"` discriminator field).
**Why it happens:** The relative-path form uses a bare string (`"./ponytail-everywhere"`); the
git-hosted forms use an object whose own `source` key (`"github"`, `"url"`, `"git-subdir"`, `"npm"`,
`"archive"`, `"command"`) is easy to omit by analogy with the simpler string form.
**How to avoid:** Use exactly the confirmed shape:
```json
{
  "name": "ponytail-everywhere",
  "source": { "source": "github", "repo": "davdittrich/ponytail-everywhere" },
  "description": "Advisory-only lazy-ladder discipline reminders across gsd's plan/execute/verify/ship lifecycle"
}
```
The outer `"source"` key of the plugin entry and the inner `"source": "github"` discriminator are
different fields with the same name at different nesting levels — both are required.
**Warning signs:** `claude plugin marketplace add davdittrich/gsd-beads` followed by `/plugin
install` failing to find the plugin, or `claude plugin validate` on `marketplace.json` flagging an
unrecognized source shape.

## Code Examples

### Marketplace github-source entry (D-02, resolves CONTEXT.md's flagged research question)
```json
// Source: https://code.claude.com/docs/en/plugin-marketplaces (official Anthropic docs,
// fetched and quoted verbatim this session — §"GitHub repositories")
{
  "name": "github-plugin",
  "source": {
    "source": "github",
    "repo": "owner/plugin-repo"
  }
}
```
Optional pin fields (not recommended here per D-05/Alternatives Considered, but documented for
completeness):
```json
{
  "source": {
    "source": "github",
    "repo": "owner/plugin-repo",
    "ref": "v2.0.0",
    "sha": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
  }
}
```
`repo` (string, required) is `owner/repo` format. `ref` (optional) is a branch or tag, defaults to
the repo's default branch. `sha` (optional) pins an exact commit; when both are set, `sha` is the
effective pin.

### Full target `marketplace.json` (both new entries applied)
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
    },
    {
      "name": "ponytail-everywhere",
      "source": { "source": "github", "repo": "davdittrich/ponytail-everywhere" },
      "description": "Advisory-only lazy-ladder discipline reminders across gsd's plan/execute/verify/ship lifecycle"
    },
    {
      "name": "sota-numerics",
      "source": { "source": "github", "repo": "davdittrich/sota-numerics" },
      "description": "SOTA-research/numerical-stability advisory steering across gsd's plan/execute/verify/ship lifecycle, plus a blocking plan:post gate that mechanically enforces a compliant Alternatives Considered section on every plan in a phase"
    }
  ]
}
```
Base file content verified via direct `Read` of `/home/dd/projects/gsd-beads/.claude-plugin/marketplace.json`
this session (the `beads-lifecycle` entry and `owner`/`name`/`description` fields are quoted
verbatim, unchanged); only the two `source` field values change.

### Extracting a subdirectory into a standalone repo (D-01, D-03; adapts Phase 7's `07-02-PLAN.md` pattern)
```bash
# Source: gh repo create --help (verified this session, gh 2.97.0) + Phase 7 precedent
# (.planning/phases/07-hygiene-publication/07-02-PLAN.md Task 2, this repo)
PLUGIN=ponytail-everywhere   # repeat for sota-numerics
EXTRACT_DIR="/tmp/${PLUGIN}-extract"

rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
cp -r "${PLUGIN}/." "$EXTRACT_DIR/"
cp LICENSE "$EXTRACT_DIR/LICENSE"          # MIT text, verbatim from gsd-beads root

# Fix Pitfall 1's REPO_ROOT depth bug before committing
# (edit $EXTRACT_DIR/tests/test-session-start.sh: "../.." -> "..", drop the
#  "$PLUGIN/" path segment from SCRIPT= and PLUGIN_DIR=)

cat > "$EXTRACT_DIR/.gitignore" <<'EOF'
__pycache__/
*.pyc
EOF

cd "$EXTRACT_DIR"
bash tests/test-session-start.sh   # local verification before any push (catches Pitfall 1 live)

git init -b main
git add -A
git commit -m "chore: initial commit — extracted from gsd-beads (fresh history, no import)"

gh repo create "davdittrich/${PLUGIN}" --public --source=. --push
# --source=. requires an already-initialized repo (Pitfall 3); --push carries the one commit
```

### Fresh-clone / round-trip verification (D-10; mirrors Phase 7 Task 3 and Phase 8's D-10 precedent)
```bash
# Source: adapted from 07-02-PLAN.md Task 3 (this repo's own precedent)
rm -rf /tmp/${PLUGIN}-verify
git clone -q "https://github.com/davdittrich/${PLUGIN}.git" "/tmp/${PLUGIN}-verify"
cd "/tmp/${PLUGIN}-verify"
claude plugin validate . --strict

claude
# inside a Claude Code session:
#   /plugin marketplace add /tmp/${PLUGIN}-verify         (or the pushed GitHub URL)
#   /plugin install ${PLUGIN}@<local-marketplace-name>
#   /plugin uninstall ${PLUGIN}
```

### README structure template (D-09; extracted verbatim from this repo's own README.md)
```markdown
# <plugin-name>

<one-line description, matching plugin.json's "description">

## What it does
<purpose>

## Requirements
- Bash (POSIX shell)
- Python 3, standard library only    <!-- sota-numerics only; ponytail-everywhere is bash-only -->
- gsd-core >= 1.10.0                  <!-- from capability.json engines.gsd, verified this session -->

## Install
\`\`\`bash
claude plugin marketplace add davdittrich/gsd-beads
claude plugin install <plugin-name>@gsd-beads -y
\`\`\`

## Uninstall
\`\`\`bash
claude plugin uninstall <plugin-name> -y
\`\`\`

## Caveats
<advisory-only, fail-open behavior; config toggle name>

## License
MIT — see [LICENSE](LICENSE).

## gsd-core
`<plugin-name>` is a capability for [gsd-core](https://github.com/open-gsd/gsd-core).
```
Section order and headings verified by direct `Read` of `/home/dd/projects/gsd-beads/README.md`
this session (Install/Uninstall/Caveats/License/gsd-core sections quoted structurally, not
verbatim text — content differs per plugin).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Local Directory `source` for every plugin (`"./ponytail-everywhere"`) | `github`-type object source for externally-hosted plugins | N/A — both forms are current, documented, and coexist in the same `marketplace.json` (per official docs: "a marketplace hosted at one repository can list a plugin fetched from a completely different repository") | This phase's whole mechanism — no deprecation involved |

**Deprecated/outdated:** None identified. The marketplace source-type table (relative path,
`github`, `url`, `git-subdir`, `npm`, `archive`, `command`) is the full current (2026) set per the
official docs page fetched this session; `archive` and `command` are the newest additions
(documented as requiring Claude Code v2.1.224+ and v2.1.229+ respectively) but are not applicable
here — `github` is the correct, simplest type for this phase's use case.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Default repo names `davdittrich/ponytail-everywhere` and `davdittrich/sota-numerics` (CONTEXT.md's own stated default, not independently re-verified against the user this session) | Standard Stack, Code Examples | Low — CONTEXT.md already flags this as "confirm with user before creating if any doubt"; the planner should carry that confirmation forward as a checkpoint, same as Phase 7 Task 1's pattern |
| A2 | `davdittrich` GitHub account has capacity/permission to create two more public repos (no org limits checked) | Code Examples | Low — `gh auth status` confirms an authenticated account with repo-creation access was already used successfully in Phase 7; no evidence of a plan/quota constraint |

**All other claims in this research were verified this session** — either by direct `Read` of
repo files (marketplace.json, plugin.json ×2, capability.json ×2, test scripts, README.md,
LICENSE, .gitignore), by `Bash` execution (`gh --version`, `git --version`, `claude --version`,
`gh auth status`, `gh repo create --help`, `git ls-files`, `git status`), or by `WebFetch` of
Anthropic's official `code.claude.com/docs/en/plugin-marketplaces.md` and
`plugins-reference.md` pages this session, with content quoted verbatim above.

## Open Questions

1. **Should the two new repos get `ref`/`sha` pinning in the marketplace entry, or stay unpinned?**
   - What we know: This repo's existing entries are all unpinned; D-05 wants independent versioning
     with no coupling to `gsd-beads`.
   - What's unclear: Whether "independent versioning" (D-05) implies the marketplace entry should
     pin to a tag once one exists, vs. staying unpinned (tracking the default branch) indefinitely.
   - Recommendation: Stay unpinned initially (matches current style, simplest, and Claude Code
     resolves the unpinned source's commit SHA as the version automatically per official docs) —
     revisit pinning only if release-channel behavior (stable vs. latest) becomes a real need.

2. **Does `gh repo create --source=. --push` push the `main` branch by name, or whatever branch `git
   init -b main` created?**
   - What we know: `git init -b main` explicitly names the initial branch `main`; `gh repo create`'s
     default branch matches "the configured repository default branch" per its own `--help` text.
   - What's unclear: Whether GitHub's account-level default branch setting for `davdittrich` is
     already `main` (making this a non-issue) — not checked this session.
   - Recommendation: The extraction sequence's explicit `git init -b main` sidesteps ambiguity
     regardless of the account default; verify post-push with `git remote show origin` or
     `gh repo view --json defaultBranchRef`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `gh` CLI | Repo creation, push, verification | ✓ | 2.97.0 | — |
| `git` | Fresh init, commit, clone-verify | ✓ | 2.55.0 | — |
| `claude` CLI | `plugin validate --strict`, marketplace round trip | ✓ | 2.1.233 | — |
| `gh auth status` (GitHub auth) | All `gh` operations | ✓ | Logged in as `davdittrich`, `repo` scope implied by successful Phase 7 push | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None — every dependency this phase needs is already
present and authenticated on this machine.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Stdlib-only bash smoke test (`tests/test-session-start.sh`, both plugins) + stdlib `unittest` (`sota-numerics/tests/test_check_alternatives.py`) — no third-party test framework, matches this repo's N5 constraint |
| Config file | None — no pytest.ini/jest.config; scripts are self-contained, `set -u` bash and plain `unittest` |
| Quick run command | `bash tests/test-session-start.sh` (both plugins); `python3 -m unittest tests/test_check_alternatives.py` (sota-numerics only) |
| Full suite command | Same as quick run — the entire test surface for each plugin is these 1-2 files |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-01/D-03 (extraction correctness) | Extracted repo's `session-start.sh` still resolves paths correctly post-move | smoke | `bash tests/test-session-start.sh` (run inside `$EXTRACT_DIR` before `gh repo create`) | ✅ exists, needs Pitfall 1 fix applied first |
| D-10 (validate clean) | `plugin.json` + hooks pass strict validation | manual (CLI, not scriptable as a unit test) | `claude plugin validate . --strict` | N/A — CLI tool, not a test file |
| D-10 (round trip) | marketplace add → install → uninstall succeeds against the real pushed repo | manual/E2E | `/plugin marketplace add`, `/plugin install`, `/plugin uninstall` inside a live Claude Code session | N/A — requires an interactive session, cannot be scripted headlessly |
| sota-numerics `check-alternatives.py` (unrelated to the split, but must still pass post-move) | Existing plan:post gate logic unaffected by directory relocation | unit | `python3 -m unittest tests/test_check_alternatives.py` (uses `Path(__file__).resolve().parent.parent`, unaffected by extraction — Pitfall 1's "Not affected" note) | ✅ exists, no fix needed |

### Sampling Rate
- **Per extraction (each plugin):** `bash tests/test-session-start.sh` (+ `python3 -m unittest
  tests/test_check_alternatives.py` for `sota-numerics`) run inside the extracted staging
  directory, before `gh repo create`.
- **Per push:** `claude plugin validate . --strict` against the freshly cloned public repo.
- **Phase gate:** Full D-10 round trip (marketplace add/install/uninstall) against both pushed
  repos, plus the existing `beads-lifecycle` entry re-verified unaffected (its `source: "./"` is
  untouched, but the whole `marketplace.json` file changes, so a re-parse sanity check is cheap
  insurance).

### Wave 0 Gaps
None — existing test infrastructure (bash smoke test + Python unittest, both already present in
each plugin subdirectory) covers all phase requirements once the extraction sequence includes the
Pitfall 1 fix and runs the existing tests locally before each push.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface introduced |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Yes (pre-existing, unaffected) | `ponytail-everywhere/hooks/session-start.sh`'s config-value handling and the CLAUDE_CONFIG_DIR space-path resolution already have regression coverage (`test-session-start.sh` cases 4 and 11, verified by `Read` this session) — this phase must not regress them, only relocate them correctly (Pitfall 1) |
| V6 Cryptography | No | N/A — no secrets, no crypto in either plugin |

### Known Threat Patterns for this phase's stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Public push exposing machine-local state (same class as Phase 7's threat register) | Information Disclosure | Both plugin subdirectories are already stdlib-only with no secrets, no `.env`, no machine-local paths baked in (verified via `grep -rn "gsd-beads\|\.\./\.\.|/home/dd"` across both trees this session — only the two known test-script/comment hits found, neither is a secret) — lower risk than Phase 7's whole-repo history rewrite, but the extraction step should still run a final `git ls-files` audit on the staged copy before push, mirroring Phase 7 Task 3's pattern at smaller scale |
| Nested/embedded git repo left behind by a failed extraction attempt | Tampering (of `gsd-beads`' own working tree) | Always extract to a location **outside** `gsd-beads`' working tree (`/tmp/<plugin>-extract`, not `<repo>/<plugin>/.git`) — see Pitfall 3 and the Anti-Patterns section |
| Premature marketplace edit pointing at an unverified/broken new repo | Denial of Service (to installers) | Sequence marketplace.json edit strictly after D-10's validate+round-trip gate passes on the pushed repo, per the Recommended Extraction Sequence step 8 |

**Supply chain:** No `npm`/`pip`/`cargo` install occurs anywhere in this phase. No package-legitimacy
checkpoint applies (see Package Legitimacy Audit above).

## Sources

### Primary (HIGH confidence — official Anthropic documentation, fetched and quoted verbatim this session)
- `https://code.claude.com/docs/en/plugin-marketplaces` (fetched as `.md`) — full marketplace
  schema, `github`/`url`/`git-subdir`/`npm`/`archive`/`command` source types, `strict` field
  semantics, version resolution
- `https://code.claude.com/docs/en/plugins-reference` (fetched as `.md`) — `claude plugin validate
  --strict` flag semantics, minimal `plugin.json` required-field rules, `.claude-plugin/` layout
  requirements

### Secondary (repo-internal, verified via direct tool execution this session)
- `/home/dd/projects/gsd-beads/.claude-plugin/marketplace.json` — current 3-entry state, `Read`
- `/home/dd/projects/gsd-beads/ponytail-everywhere/.claude-plugin/plugin.json`,
  `/home/dd/projects/gsd-beads/sota-numerics/.claude-plugin/plugin.json` — `Read`
- `/home/dd/projects/gsd-beads/ponytail-everywhere/tests/test-session-start.sh` (lines 1-136),
  `/home/dd/projects/gsd-beads/sota-numerics/tests/test-session-start.sh` (lines 1-15) — `Read`,
  source of the Pitfall 1 finding
- `/home/dd/projects/gsd-beads/sota-numerics/tests/test_check_alternatives.py` (lines 1-30) — `Read`
- `/home/dd/projects/gsd-beads/README.md`, `/home/dd/projects/gsd-beads/LICENSE`,
  `/home/dd/projects/gsd-beads/.gitignore` — `Read`
- `/home/dd/projects/gsd-beads/.planning/phases/07-hygiene-publication/07-02-PLAN.md` — `Read`,
  Phase 7's own `gh repo create`/push precedent
- `gh --version`, `git --version`, `claude --version`, `gh auth status`, `gh repo create --help`,
  `git ls-files`, `git status` — `Bash`, this session

### Tertiary (LOW confidence per the classify-confidence seam — provider `websearch`/`webfetch`
report LOW regardless of content authority since no `context7`/`ref`/docs-MCP provider is
configured in `.planning/config.json` (all search-provider flags `false`); the underlying content
is nonetheless first-party official documentation, quoted verbatim, not community/blog material)
- Initial `WebSearch` pass (superseded by the direct `WebFetch` of the official docs pages above,
  which is the actual source of every schema claim in this document)

## Metadata

**Confidence breakdown:**
- Standard stack / marketplace schema: HIGH — resolved directly against official Anthropic docs,
  fetched and quoted verbatim this session; not inferred, not from training memory
- Architecture / extraction sequence: HIGH — every command verified against `gh`/`git`/`claude`
  CLI help text and this repo's own Phase 7 precedent, all read this session
- Pitfalls: HIGH — Pitfall 1 (REPO_ROOT bug) and Pitfall 3 (`--source` requires existing repo) are
  both directly verified (file `Read` and CLI `--help` respectively), not speculative

**Research date:** 2026-08-17
**Valid until:** 30 days (Claude Code plugin/marketplace docs are actively revised; re-verify the
`github` source schema if this phase's execution slips past mid-September 2026)
