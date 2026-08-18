# Phase 7: Hygiene & Publication - Research

**Researched:** 2026-08-16
**Domain:** Git history rewriting (git-filter-repo) + GitHub repo creation/push (gh CLI)
**Confidence:** HIGH

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `.serena/` and `.gsd/dispatch-isolation-sentinel.json` exist in the working tree today but are not among ROADMAP's 4 named filter-repo targets or its 3 named `.gitignore` additions. User deferred the ignore-vs-delete call to Claude at plan/execute time — inspect actual file contents first, then decide gitignore vs. outright delete. Reversibility: reversible — untracked files, no history impact either way.
- **D-02:** `06-PATTERNS.md` (Phase 6 planning doc, currently untracked) — commit it. Consistent with the existing convention of tracking `*-PATTERNS.md`/`*-CONTEXT.md` files under `.planning/phases/`.
- **D-03:** Take a full `git clone --mirror` backup to a local path before running `git filter-repo`. Insurance against the rewrite going wrong, even though the repo has no remote yet. Reversibility: reversible if the mirror backup is taken first; one-way without it. Rationale: always take the mirror backup — do not skip this step.
- **D-04:** Owner is `davdittrich` (confirmed via `gh auth status`). Repo name `gsd-beads`, public, `main` as default branch (existing local branch name, single branch, no other branches/tags besides `v1.0`).
- **D-05:** Do NOT auto-init with a placeholder README on `gh repo create`. Create the repo empty; push the existing (rewritten) history as-is. README.md is Phase 8 scope.

### Claude's Discretion
- Exact `.gitignore` phrasing/grouping for the new entries (`.serena/`, `.gsd/dispatch-isolation-sentinel.json` if kept, plus ROADMAP's named `.beads.backup-pre-recovery/`, `.beads/interactions.jsonl`, `*.bak`).
- Mirror-backup local path and naming.
- Exact `git filter-repo` invocation order (one `--path ... --invert-paths` call per file, or combined) as long as the end state matches ROADMAP Success Criterion 3 exactly (all 4 named files gone from every commit's tree).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. README content, release archive allowlist, and final `claude plugin validate` gate are already correctly scoped to Phase 8 per ROADMAP.
</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUB-05 | Pre-push git hygiene audit — 4 named files untracked; `.gitignore` extended to cover backup/Dolt artifacts before first push | Runtime State Inventory (below) enumerates the live inventory beyond ROADMAP's 4 files; Architecture Patterns gives the exact `git filter-repo` invocation; Code Examples give the exact `.gitignore` diff |
| PUB-10 | GitHub repository created (public, personal account, `gsd-beads`), remote configured, history pushed | Architecture Patterns step 3 gives the verified `gh repo create` / push sequence; Common Pitfalls covers the force-push-vs-empty-remote nuance |
</phase_requirements>

## Summary

This phase is a git-plumbing operation, not an application build — the "stack" is `git` itself, the already-installed `git-filter-repo` binary, and the `gh` CLI. `git filter-repo` (the tool GitHub's own docs recommend over the deprecated `git filter-branch`) strips a path from every commit's tree in one pass; multiple targets combine into a single invocation (`--path A --path B --path C --path D --invert-paths`), matching the official usage example exactly. The operation is irreversible in place (reflogs and loose objects are pruned immediately) — the D-03 mirror-clone backup is the only undo path.

Live inspection of this exact repository (not assumed) surfaced two things the ROADMAP's 4-file list and 3-pattern `.gitignore` list do not cover: an unrelated `git stash` entry that snapshots one of the 4 target files (`.gsd-capabilities.json`) at an old timestamp, and 3 historical commits that become **fully empty** once the filter runs (they touched only target files) — these will vanish from `git log` entirely under the default `--prune-empty auto`, which is expected, not a bug. `git filter-repo` refuses to run in place on this repo without `--force`, confirmed empirically (loose objects present, no fresh pack) — this is expected and is bypassed correctly by `--force`, not worked around some other way.

**Primary recommendation:** clean the working tree and drop the stray stash first, take the D-03 mirror backup, run one combined `git filter-repo --force --path <4 files> --invert-paths`, verify with `git log -p --all -- <paths>` (empty) and `git ls-files` (absent), then `gh repo create davdittrich/gsd-beads --public --source=.` (no `--add-readme`/`--gitignore`/`--license`) followed by a plain (non-force) first push — force is not technically required against a genuinely empty new remote, but treat the push as the one-way-door confirmation gate regardless, per standing git-safety rules.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Strip 4 named files from all history | Local git object database (via `git filter-repo`) | — | History rewriting is a local, offline operation; nothing server-side is touched until push |
| Extend `.gitignore` | Working tree / git index | — | Prevents re-tracking after the rewrite; must land in a commit before or as part of the rewrite |
| Backup/insurance | Local filesystem (`git clone --mirror`) | — | Pure local copy, no network involved |
| Remote repo creation | GitHub (via `gh` CLI / GitHub API) | — | Server-side resource; requires existing `repo`-scope auth (already present) |
| Push rewritten history | Local git → GitHub remote | — | One-way transfer; first push to an empty repo, not a sync |
| Verification | Local (`git log -p`) + GitHub (fresh `git clone`) | — | Success criterion 5 explicitly requires checking the *pushed* copy, not just local state |

## Standard Stack

### Core

| Tool | Version (verified) | Purpose | Why Standard |
|------|---------|---------|--------------|
| `git-filter-repo` | commit `a40bce548d2c` (already installed at `/home/dd/.local/bin/git-filter-repo`) [VERIFIED: `git filter-repo --version` run in this repo, 2026-08-16] | Rewrite git history to strip paths | GitHub's own "Removing sensitive data from a repository" docs recommend it as the primary tool, explicitly over the deprecated `git filter-branch` [CITED: docs.github.com] |
| `gh` CLI | 2.97.0 (2026-07-31) [VERIFIED: `gh --version` run in this repo, 2026-08-16] | Create the GitHub repo, configure remote, push | Already authenticated (`davdittrich`, `repo` scope) [VERIFIED: `gh auth status` run in this repo, 2026-08-16] — no auth setup needed |
| `git` | (system git, already in use — 169 commits, single branch `main`, tag `v1.0`) [VERIFIED: `git log --oneline \| wc -l`, `git branch -a`, `git tag`, run in this repo, 2026-08-16] | Underlying VCS; filter-repo and gh CLI both shell out to it | N/A — not a choice, it's what's already there |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `git filter-repo` | `git filter-branch` | Deprecated by Git itself; orders of magnitude slower on repos of any size; git's own docs steer users to filter-repo. Not viable — rejected. |
| `git filter-repo` | BFG Repo-Cleaner | GitHub also documents BFG as an alternative [CITED: docs.github.com] — faster for simple "delete these files/blobs" cases, but requires a separate Java-based tool install; filter-repo is already installed and its `--path`/`--invert-paths` flags map 1:1 onto this phase's requirement with no extra install. Rejected — no reason to add a dependency the repo doesn't already have. |
| `gh repo create --source=. --push` | Manual `git remote add` + `git push` after creating repo via GitHub web UI | Functionally equivalent; `gh` is already authenticated and scriptable, so it is the more auditable, repeatable choice for this repo's git-plumbing-only phase. Either works; `gh` chosen for auditability. |

**No installation required** — `git-filter-repo` and `gh` are both already present and authenticated in this environment; this phase touches no package manager.

## Package Legitimacy Audit

No new external packages are installed by this phase. `git-filter-repo` is already installed and is the tool `docs.github.com` names by name for this exact task [CITED: docs.github.com "Removing sensitive data from a repository"]. Formal legitimacy-check tooling (npm/PyPI registry audit) does not apply — this is not a language-ecosystem package install.

## Architecture Patterns

### Operation Sequence Diagram

```text
[dirty working tree]
        │
        ▼
1. Resolve pending changes (D-01/D-02 decisions, .gitignore additions,
   .headroom_wrap_marker.json deletion) → single clean commit
        │
        ▼
2. git stash drop            (removes stray WIP stash that snapshots
                               .gsd-capabilities.json — see Pitfall 1)
        │
        ▼
3. git clone --mirror . <backup-path>     (D-03 insurance — untouched copy)
        │
        ▼
4. git filter-repo --force \
     --path .beads/config.yaml \
     --path .beads/metadata.json \
     --path .claude/.headroom_wrap_marker.json \
     --path .gsd-capabilities.json \
     --invert-paths
        │  (strips all 4 paths from every commit's tree on every ref;
        │   prunes now-empty commits; expires reflog; runs gc)
        ▼
5. Verify locally:
     git log -p --all -- <each of the 4 paths>   → must print nothing
     git ls-files | grep -E '<4 paths>'           → must print nothing
        │
        ▼
6. gh repo create davdittrich/gsd-beads --public --source=.
   (no --add-readme, no --gitignore, no --license → empty remote, per D-05)
        │
        ▼
7. git push -u origin main --tags     (empty remote → no --force needed;
                                        confirm with user first — one-way door)
        │
        ▼
8. Verify remotely:
     git clone <fresh temp dir> from the pushed URL
     git log -p --all -- <4 paths>   → must print nothing (Success Criterion 5)
```

### Recommended local layout for the backup
```text
/home/dd/Gemini/                       # sibling to the project root, not
├── gsd-beads/                         # nested inside it — avoids the mirror
└── gsd-beads-backup-pre-filter-repo/  # accidentally getting swept into
      (bare mirror clone)              # `git add` or matched by .gitignore
```
Per CLAUDE.md ("Worktrees are under the project root never outside") this is a backup mirror, not a worktree — it does not need to live under the project root, and placing it there would risk it being picked up by later `git add -A`-style operations if anyone runs one. A sibling directory keeps it isolated while remaining trivially discoverable (`namei` before any destructive op on it, per CLAUDE.md).

### Pattern: single combined `--invert-paths` invocation

**What:** One `git filter-repo` call listing all 4 `--path` flags followed by one `--invert-paths`, rather than 4 sequential invocations.
**When to use:** Whenever removing multiple, unrelated paths in one rewrite.
**Why:** This is the pattern in `git-filter-repo`'s own `--help` EXAMPLES section verbatim: `git filter-repo --path foo.zip --path bar/baz/zips/ --invert-paths` [VERIFIED: `git filter-repo -h` output, run in this repo, 2026-08-16 — reproduced in Code Examples below]. A single combined run also means the "fresh clone" / `--force` decision only has to be made once, and there is only one rewrite event to back up against, not four.

### Anti-Patterns to Avoid
- **Sequential filter-repo runs, one file at a time:** Each run re-triggers the "not a fresh clone" refusal (the repo is no longer freshly packed after the first run's `gc`), forcing `--force` (or a fresh re-clone) 4 times instead of once. No benefit over the combined invocation; strictly more operations on an irreversible tool.
- **Running `git rm --cached` on the 4 files as a "manual untrack" step before filtering:** Unnecessary — `git filter-repo --path X --invert-paths` already strips X from **every** commit's tree, including the tip/HEAD commit, and checks out the resulting tree afterward. A separate untrack commit adds a redundant step and, if done carelessly, could itself become one of the "empty commits" that then gets silently pruned by `--prune-empty auto`, muddying the commit-count accounting documented in Pitfall 2.
- **Pushing to the new GitHub remote with `--mirror` or before verifying locally:** Push only after step 5's local verification passes — a push cannot be un-pushed against a public repo (this is the phase's own stated one-way door).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stripping files from every historical commit | A custom script walking `git log` and rewriting commits by hand, or `git filter-branch` | `git filter-repo --path ... --invert-paths` | `filter-branch` is git-upstream-deprecated for exactly this task (slow, easy to get wrong with tree-filter scripts); `filter-repo` is the tool git's own docs point to |
| Verifying no trace remains | Trusting `git log` on the working copy alone | `git log -p --all -- <path>` locally **and** a genuinely fresh `git clone` of the pushed remote, then repeat the `git log -p` check there | Local verification only proves the local rewrite worked; the phase's actual acceptance criterion (Success Criterion 5) is about what a stranger's fresh clone contains |

**Key insight:** every mechanism this phase needs (multi-path strip, empty-commit pruning, reflog expiry, remote creation with no auto-init) is a documented flag on tools already installed and authenticated in this environment. There is no custom code to write in this phase.

## Runtime State Inventory

> Rename/refactor/migration-adjacent phase (history rewrite + untrack) — inventory completed against the live repo, 2026-08-16.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no database, no Dolt sync ref exists yet. `git for-each-ref refs/dolt` returns empty [VERIFIED: run in this repo, 2026-08-16]; `.beads/embeddeddolt/` (the actual Dolt DB) is already gitignored (`.beads/.gitignore` covers `embeddeddolt/`) and was never tracked, so filter-repo has nothing to touch there. | None this phase. Flagged as an Open Question below for future risk once `bd` sync starts pushing `refs/dolt/data`. |
| Live service config | None — no CI, no deployed service, no external dashboard references this repo yet (pre-publication). | None. |
| OS-registered state | None — no systemd/launchd/Task Scheduler entries reference this repo by path or name. | None. |
| Secrets/env vars | `.beads/config.yaml`'s comments document that `linear.api_key` / `github.token` *can* be stored in this file (commented-out template today, no live secret present) [VERIFIED: read `.beads/config.yaml` in full, this session — see quote in Pitfall 3]. `.gsd-capabilities.json` contains `"source": "./.gsd/capabilities/beads"`, a path tied to this specific checkout, and `.beads/metadata.json` contains `"project_id": "e2e560fc-48cf-4630-a43b-13199b6ed181"`, an install-specific UUID [VERIFIED: read `.beads/metadata.json` in full, this session — `{"database": "dolt", "backend": "dolt", "dolt_mode": "embedded", "dolt_database": "gsd_beads", "project_id": "e2e560fc-48cf-4630-a43b-13199b6ed181"}`]. None are live credentials today, but all 3 are exactly the class of file ROADMAP already targets for removal — filter-repo handles this, no extra step needed. | Covered by the planned filter-repo pass — no separate secret-rotation step needed since nothing live is present. |
| Build artifacts | `.gsd/capabilities/beads/` (17 tracked files: `capability.json`, skill fragments, test fixtures, `scripts/sync.py`) [VERIFIED: `git ls-files .gsd/` run in this repo, 2026-08-16] is a **legitimately tracked** subtree, distinct from the untracked `.gsd/dispatch-isolation-sentinel.json` sibling file. Any `.gitignore` addition for the sentinel file must be filename-scoped (`.gsd/dispatch-isolation-sentinel.json`), never a directory-level `.gsd/` ignore, or it silently un-tracks the capability bundle PUB-03 depends on. | `.gitignore` entry must be the exact filename, not the parent directory. |
| **Untracked items beyond ROADMAP's list** | `git status` shows 6 untracked/pending items beyond the 4 named files [VERIFIED: `git status --porcelain=v2 -uall` run in this repo, 2026-08-16]: `.beads.backup-pre-recovery/` (3 files), `.beads/interactions.jsonl`, `.beads/metadata.json.bak`, `.gsd/dispatch-isolation-sentinel.json`, `.planning/phases/06-runtime-integration/06-PATTERNS.md`, `.serena/` (5 files: `.gitignore`, `project.local.yml`, `project.yml`, `memories/`, `cache/python/`). Plus 2 modified-not-new files: `.planning/STATE-ARCHIVE.md`, `.planning/config.json`, and 1 deleted-not-staged: `.claude/.headroom_wrap_marker.json`. | `.beads.backup-pre-recovery/`, `.beads/interactions.jsonl`, `*.bak` → `.gitignore` (ROADMAP-named). `.gsd/dispatch-isolation-sentinel.json` → `.gitignore` (per D-01, filename-scoped — see above). `.serena/` → `.gitignore` wholesale (per D-01 — see Pitfall 4). `06-PATTERNS.md` → commit (D-02). `STATE-ARCHIVE.md`/`config.json`/the already-deleted marker → normal commit, ahead of the filter-repo rewrite so the pre-rewrite HEAD is clean. |
| **Stray git object referencing a target file** | `git stash list` shows 1 entry: `stash@{0}: WIP on main: 516581f fix(04)...` [VERIFIED: `git stash list` run in this repo, 2026-08-16]. `git stash show -p stash@{0}` touches only `.gsd-capabilities.json` (a 1-line `updatedAt` timestamp diff) [VERIFIED: `git stash show -p stash@{0}` run in this repo, 2026-08-16 — diff header `--- a/.gsd-capabilities.json` / `+++ b/.gsd-capabilities.json`]. This is a `refs/stash` entry, not a branch/tag commit — `git push` never transmits `refs/stash`, so it cannot reach the public GitHub repo either way — but `git filter-repo`'s own maintainers describe its handling of `refs/stash` as undocumented/error-prone, especially against mirror clones (newren/git-filter-repo issue #652) [CITED: github.com/newren/git-filter-repo/issues/652]. | `git stash drop` (or `git stash pop` if the WIP is still wanted) before running `git filter-repo`, to remove the ambiguity entirely rather than rely on filter-repo's undocumented stash behavior. |

**Nothing found in category:** Stored data, Live service config, OS-registered state — all confirmed empty by direct inspection, not assumed.

## Common Pitfalls

### Pitfall 1: Stray `git stash` entry snapshots a target file

**What goes wrong:** A leftover `stash@{0}` from an earlier session holds an old copy of `.gsd-capabilities.json`. It isn't pushed by normal `git push`, but it sits in the local object database untouched by filter-repo's documented behavior.
**Why it happens:** Stashes are commits under `refs/stash`, a namespace outside `refs/heads`/`refs/tags` that filter-repo's default path-filtering doesn't reliably process (confirmed by the tool's own issue tracker, not assumed).
**How to avoid:** `git stash drop` before running `git filter-repo`. Confirm with `git stash list` (must print nothing) before proceeding.
**Warning signs:** `git filter-repo -h`'s own refusal message references "reflogs and old objects" being pruned — if a stash survives that pruning unexpectedly, it means filter-repo silently didn't touch `refs/stash`, which is the documented-but-opaque behavior, not a filter-repo bug.

### Pitfall 2: Commit count will visibly drop by more than 4

**What goes wrong:** A plan or verification step that expects "history rewritten, same commit count, just smaller trees" will be surprised when `git log --oneline | wc -l` drops from 169 to as low as 166.
**Why it happens:** `--prune-empty auto` (the default) deletes any commit that becomes empty once its only changed path(s) are removed. In this repo, exactly 3 commits touch **only** files from the removal set: `2075c5f` (stray milestone archival cleanup), `927e9de` (capability re-install/re-consent), `85aff2a` (capability re-consent after bundle hash change) [VERIFIED: computed from `git log --oneline --name-only` run in this repo, 2026-08-16, filtering for commits whose changed-file set is a subset of `{.beads/config.yaml, .beads/metadata.json, .claude/.headroom_wrap_marker.json, .gsd-capabilities.json}`].
**How to avoid:** Treat this as expected, not a defect — do not write a verification step asserting "commit count unchanged." Assert instead on the specific criteria ROADMAP already gives (files absent from `git log -p`, files absent from `git ls-files`).
**Warning signs:** `git rev-list --count HEAD` before vs. after differing is correct behavior here, not a red flag.

### Pitfall 3: `.beads/config.yaml` is a secrets-capable file even though today it has no live secret

**What goes wrong:** Assuming this file is safe to leave tracked because "there's nothing sensitive in it right now."
**Why it happens:** The file is beads' own template, entirely commented out today, but its own inline comments document the exact fields that would hold live credentials: `# Secret keys (stored in this file but prefer env vars to avoid git exposure): # - linear.api_key  → use LINEAR_API_KEY env var instead # - github.token    → use GITHUB_TOKEN env var instead` [VERIFIED: `.beads/config.yaml` lines 64-73, read in full this session — quoted verbatim above].
**How to avoid:** This is exactly why ROADMAP already targets this file for removal from history, not just future-proofing against a hypothetical edit — confirm the plan doesn't relax this to "just add a warning comment" instead of the full untrack+rewrite.
**Warning signs:** N/A — this pitfall's mitigation is already the phase's Success Criterion 1 and 3; noted here so the planner doesn't second-guess the file's inclusion.

### Pitfall 4: Editing `.beads/.gitignore` instead of the root `.gitignore`

**What goes wrong:** `.beads/` already has its own nested `.gitignore` (58 lines, extensive Dolt/runtime coverage) that looks like the natural place to add `interactions.jsonl` and `*.bak` coverage.
**Why it happens:** The nested file is tool-managed (by `bd`) and carries an explicit self-warning against edits of this shape: `# NOTE: Do NOT add negation patterns here. # They would override fork protection in .git/info/exclude. # Config files (metadata.json, config.yaml) are tracked by git by default # since no pattern above ignores them.` [VERIFIED: `.beads/.gitignore`, read in full this session — quoted verbatim above]. This file is explicitly generated/maintained by `bd init`/`bd` tooling and risks being overwritten on a future `bd` upgrade.
**How to avoid:** Add the 3 ROADMAP-named patterns (`.beads.backup-pre-recovery/`, `.beads/interactions.jsonl`, `*.bak`) plus the D-01 `.serena/` and `.gsd/dispatch-isolation-sentinel.json` entries to the **root** `.gitignore`, not `.beads/.gitignore`.
**Warning signs:** If a future `bd` version regenerates `.beads/.gitignore` and any of these patterns silently disappear, the root `.gitignore` copy is unaffected.

### Pitfall 5: Assuming the first push needs `--force`

**What goes wrong:** ROADMAP's own phase description states "force-push required — commit hashes changed," which is true of the *local* rewrite but not necessarily of the *push mechanics* here.
**Why it happens:** Conflating "history was rewritten" (true, hashes changed) with "the remote already has history to overwrite" (false — per D-05, `gh repo create` is run with no `--add-readme`/`--gitignore`/`--license`, so the new remote has zero commits; `git push -u origin main` against a genuinely empty remote needs no `--force` at all — `gh repo create --help`'s own description confirms `--add-readme` is what would create a conflicting initial commit, and D-05 explicitly avoids that flag) [VERIFIED: `gh repo create --help`, run in this environment, 2026-08-16].
**How to avoid:** Attempt a plain `git push -u origin main --tags` first. If GitHub unexpectedly already has a commit (race condition, or a flag was passed that shouldn't have been), the push will be rejected and only then is `--force`/`--force-with-lease` appropriate — and per CLAUDE.md's standing git-safety rules, that still requires explicit user confirmation before running. Either way, treat the push itself (force or not) as the one-way-door moment requiring confirmation, since ROADMAP frames it that way regardless of the underlying git mechanics.
**Warning signs:** A push that succeeds without `-f`/`--force` is the expected, correct outcome here — do not add `--force` "just in case," since CLAUDE.md requires explicit user approval before any force-push and an unwarranted one would trip that gate for no reason.

## Code Examples

### Full filter-repo invocation (verified syntax, this repo's 4 target paths)
```bash
# Source: git filter-repo -h (installed binary, this repo, 2026-08-16) —
# EXAMPLES section: "To remove foo.zip and bar/baz/zips from every revision
# in history: git filter-repo --path foo.zip --path bar/baz/zips/ --invert-paths"
git filter-repo --force \
  --path .beads/config.yaml \
  --path .beads/metadata.json \
  --path .claude/.headroom_wrap_marker.json \
  --path .gsd-capabilities.json \
  --invert-paths
```

### Empirically-confirmed refusal without --force (this repo, this session)
```text
$ git filter-repo --path .beads/config.yaml --invert-paths
Aborting: Refusing to destructively overwrite repo history since
this does not look like a fresh clone.
  (expected freshly packed repo)
Please operate on a fresh clone instead.  If you want to proceed
anyway, use --force.
```
Confirms `--force` is required for this exact repo state (740 loose objects, 2 packs — not freshly packed) [VERIFIED: `git count-objects -v` run this session].

### Local verification (must return nothing for all 4 paths)
```bash
git log -p --all -- .beads/config.yaml .beads/metadata.json \
  .claude/.headroom_wrap_marker.json .gsd-capabilities.json
git ls-files | grep -E '\.beads/config\.yaml|\.beads/metadata\.json$|headroom_wrap_marker|\.gsd-capabilities\.json'
```

### Remote creation and first push (no README/gitignore/license per D-05)
```bash
# Source: gh repo create --help (installed CLI 2.97.0, this environment, 2026-08-16)
gh repo create davdittrich/gsd-beads --public --source=.
git push -u origin main --tags
```

### Fresh-clone remote verification (Success Criterion 5)
```bash
git clone https://github.com/davdittrich/gsd-beads.git /tmp/gsd-beads-verify
cd /tmp/gsd-beads-verify
git log -p --all -- .beads/config.yaml .beads/metadata.json \
  .claude/.headroom_wrap_marker.json .gsd-capabilities.json
# must print nothing; also confirm none of the 4 paths exist in the working tree
ls .beads/config.yaml .beads/metadata.json .claude/.headroom_wrap_marker.json .gsd-capabilities.json 2>&1
```

### `.gitignore` additions (root `.gitignore`, not `.beads/.gitignore` — Pitfall 4)
```diff
 __pycache__/
 *.pyc

 # Beads / Dolt files (added by bd init)
 .dolt/
 *.db
 .beads-credential-key
 .beads/proxieddb/
 *.gate.lock*
+
+# Backup and interaction-log artifacts (local-only, Phase 7 hygiene)
+.beads.backup-pre-recovery/
+.beads/interactions.jsonl
+*.bak
+
+# Local tool state (per-machine, not shared across clones)
+.serena/
+.gsd/dispatch-isolation-sentinel.json
```
(Base file content verified by reading `.gitignore` in full this session — 8 lines shown above match the current file exactly.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `git filter-branch` | `git filter-repo` | Git project itself has recommended against `filter-branch` for years; GitHub's official sensitive-data-removal docs name `filter-repo` first [CITED: docs.github.com] | `filter-branch` is dramatically slower (runs a subprocess per commit) and easier to misuse (tree-filter foot-guns); no reason to consider it for this phase |

**Deprecated/outdated:** `git filter-branch` — git's own manpage carries a deprecation warning; not evaluated further here since the repo already has `filter-repo` installed and working.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `git filter-repo`'s handling of `refs/stash` is "opaque/error-prone" based on a single third-party GitHub issue thread, not git-filter-repo's own official manual page text | Pitfall 1, Runtime State Inventory | Low — the mitigation (`git stash drop` first) is a strict superset of safety regardless of whether the underlying claim is fully precise; dropping the stash removes the question entirely rather than relying on the claim being exactly right |
| A2 | A first `git push -u origin main --tags` to a `gh repo create --source=.` (no auto-init flags) empty remote will succeed without `--force` | Pitfall 5, Architecture Patterns | Low-medium — if wrong, the push is simply rejected and the planner/executor falls back to a confirmed `--force`/`--force-with-lease`, which was going to require explicit user confirmation either way per ROADMAP's framing; no data loss risk either way since it's a brand-new repo |

## Open Questions

1. **Does the future `bd` Dolt sync ref (`refs/dolt/data`) need cleaning too?**
   - What we know: `refs/dolt/data` does not exist locally yet (`git for-each-ref refs/dolt` is empty) [VERIFIED: run this session] — beads' architecture note (CLAUDE.md) says this ref is created on the *remote* by `bd` sync, not present in a repo that has never synced.
   - What's unclear: once this repo starts running `bd` sync against the new GitHub remote (a Phase 8+ or later concern), whether the Dolt database pushed to that ref could independently re-embed config-equivalent data (e.g., if `bd` ever stores `config.yaml`-sourced settings inside the Dolt DB itself, not just the git-tracked file).
   - Recommendation: out of scope for Phase 7 (nothing to clean today, ref doesn't exist), but worth a one-line flag in Phase 8's README or a follow-up ticket — not a Phase 7 blocker since Phase 7's own success criteria are entirely about git-tracked file history, not the Dolt sync ref.

2. **`.serena/` — gitignore vs. delete (D-01)?**
   - What we know: `.serena/` is untracked, contains an existing nested `.serena/.gitignore` that already ignores `/cache` and `/project.local.yml` internally, plus `project.yml` (project-level Serena MCP config, not machine-specific — mostly comments/defaults) and `memories/` (empty at inspection time — `find .serena -maxdepth 3` showed no files under `memories/`).
   - What's unclear: whether `project.yml` should ever be tracked (it's arguably project-level config, not purely machine-local, unlike `project.local.yml` which Serena itself already gitignores by convention).
   - Recommendation: gitignore the whole `.serena/` directory at the root level (matches the IDE/tool-cache convention already used for `.beads/` runtime files) rather than deleting it — deletion would just cause Serena to regenerate it, and gitignoring is non-destructive. If a future contributor wants `.serena/project.yml` shared, that's a separate, explicit decision outside this phase's scope.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `git-filter-repo` | PUB-05 (history rewrite) | ✓ | commit `a40bce548d2c` at `/home/dd/.local/bin/git-filter-repo` | — (already installed, confirmed via `git filter-repo --version`) |
| `gh` CLI | PUB-10 (repo creation/push) | ✓ | 2.97.0 (2026-07-31) | — |
| `gh auth` (repo scope) | PUB-10 | ✓ | `davdittrich`, scopes `gist, read:org, repo, workflow` | — |
| Existing `origin` remote | N/A | ✗ (none configured) | — | Expected — this is a first-time repo creation, not a re-point (confirmed `git remote -v` empty) |

**Missing dependencies with no fallback:** none — everything required is already installed and authenticated.
**Missing dependencies with fallback:** none.

## Validation Architecture

This phase has no application code and no test framework — "tests" are the ROADMAP success criteria themselves, run as literal shell commands. `workflow.nyquist_validation: true` in `.planning/config.json` [VERIFIED: `.planning/config.json` read this session] still applies; the "test framework" here is git itself.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None (shell-command assertions against git/gh state) |
| Config file | n/a |
| Quick run command | `git ls-files \| grep -E '<4 target paths>'` (expect empty) |
| Full suite command | The 4-command sequence in Code Examples' "Fresh-clone remote verification" block |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PUB-05 | 4 files untracked, .gitignore extended | smoke | `git ls-files \| grep -E '\.beads/config\.yaml\|\.beads/metadata\.json$\|headroom_wrap_marker\|\.gsd-capabilities\.json'` (expect empty) + `git check-ignore -v .beads.backup-pre-recovery/ .beads/interactions.jsonl foo.bak` (expect all matched) | n/a — direct git commands |
| PUB-05 | History fully stripped, not just untracked | smoke | `git log -p --all -- <4 paths>` (expect empty output) | n/a |
| PUB-10 | Public repo exists, remote configured, history pushed | smoke | `gh repo view davdittrich/gsd-beads --json visibility,url` + `git remote -v` | n/a |
| PUB-10 (Success Criterion 5) | Fresh clone contains no trace | e2e | `git clone <url> /tmp/verify && cd /tmp/verify && git log -p --all -- <4 paths>` (expect empty) | n/a |

### Sampling Rate
- **Per task commit:** local `git log -p` / `git ls-files` checks after the filter-repo step
- **Per wave merge:** n/a — single-wave phase
- **Phase gate:** the fresh-clone check (Success Criterion 5) is the phase gate — must run once, after push, before declaring the phase done

### Wave 0 Gaps

None — existing git/gh tooling covers all phase requirements; no test infrastructure to build.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | n/a — no auth surface in this phase |
| V3 Session Management | No | n/a |
| V4 Access Control | No | n/a — GitHub repo visibility (`--public`) is a configuration choice already locked by D-04, not an access-control implementation |
| V5 Input Validation | No | n/a — no user-facing input |
| V6 Cryptography | No | n/a — no crypto implemented; `.beads-credential-key` (encryption key mentioned in `.beads/.gitignore`) is already gitignored and untouched by this phase |

### Known Threat Patterns for this phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secrets/machine-identifiers surviving in public git history | Information Disclosure | This phase's core mechanism (`git filter-repo --invert-paths`) *is* the mitigation — Pitfall 3 documents why `.beads/config.yaml` specifically is a secrets-capable file even though it holds no live secret today |
| Recontamination via a stale local clone pushing old history back | Information Disclosure / Tampering | Not applicable yet — brand-new repo, no other clones or collaborators exist at push time (GitHub's own docs flag this risk for repos with existing forks/collaborators [CITED: docs.github.com], which this repo does not have) |
| Force-push overwriting unexpected remote state | Tampering | Pitfall 5's plain-push-first approach + CLAUDE.md's standing rule requiring explicit user confirmation before any force-push |

## Sources

### Primary (HIGH confidence)
- `git filter-repo -h` — installed binary, this repo, 2026-08-16 (flag semantics, EXAMPLES section, refusal-without-`--force` message)
- `gh repo create --help` — installed CLI 2.97.0, this environment, 2026-08-16 (flag semantics, `--add-readme` behavior)
- `gh auth status`, `git remote -v`, `git branch -a`, `git tag`, `git stash list`, `git status --porcelain=v2 -uall`, `git count-objects -v`, `git for-each-ref refs/dolt`, `git log --oneline --name-only` — all run directly against this repo, 2026-08-16
- `.gitignore`, `.beads/.gitignore`, `.beads/config.yaml`, `.beads/metadata.json`, `.gsd-capabilities.json`, `.serena/project.yml`, `.serena/.gitignore`, `.gsd/dispatch-isolation-sentinel.json` — read in full this session

### Secondary (MEDIUM confidence)
- [Removing sensitive data from a repository — GitHub Docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) — recommends `git filter-repo` over `filter-branch`/BFG alternative noted, fresh-clone verification method, recontamination/rotate-secrets caveats
- [gh repo create — GitHub CLI manual](https://cli.github.com/manual/gh_repo_create) — `--source`/`--push`/`--remote` flag semantics, cross-checked against local `--help` output

### Tertiary (LOW confidence)
- [newren/git-filter-repo issue #652](https://github.com/newren/git-filter-repo/issues/652) — `refs/stash` handling described as opaque/error-prone by users and maintainers; not covered in the tool's own `--help` text, hence tagged LOW/community-sourced rather than official — mitigated by simply dropping the stash first (Pitfall 1) rather than depending on this claim being precisely correct

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — both tools already installed, authenticated, and their flag behavior verified directly against the installed binaries in this environment, not from memory
- Architecture: HIGH — the exact command sequence was empirically tested against this repo (including reproducing the `--force` refusal) and cross-checked against GitHub's official sensitive-data-removal guidance
- Pitfalls: HIGH for Pitfalls 2-5 (derived from direct inspection of this repo's actual commits/config/gitignore contents); MEDIUM for Pitfall 1 (the `refs/stash` claim rests on a community GitHub issue thread, not official docs — mitigation is robust regardless)

**Research date:** 2026-08-16
**Valid until:** Indefinite for the git-filter-repo/gh CLI mechanics (stable tools, not fast-moving); the live-repo inventory (stash contents, untracked file list, commit counts) is valid only until the next commit/session — re-verify `git status`/`git stash list` immediately before executing if any time has passed since this research.
