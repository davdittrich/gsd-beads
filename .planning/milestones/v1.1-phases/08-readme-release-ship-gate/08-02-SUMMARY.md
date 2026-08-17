---
phase: 08-readme-release-ship-gate
plan: 02
subsystem: infra
tags: [github-actions, release, claude-plugin, ship-gate]

requires:
  - phase: 08-readme-release-ship-gate
    plan: 01
    provides: "README.md and .github/workflows/release.yml, rehearsed end-to-end on a throwaway tag"
provides:
  - "Real v1.1.0 GitHub Release on davdittrich/gsd-beads carrying an allowlist-exact gsd-beads.zip"
  - "Ship gate transcripts: fresh-clone strict validate at the tag (SC5), and a live marketplace add/install/uninstall round trip against the public repo (SC4)"
affects: [ship-gate, v1.1-milestone-close]

actuals:
  tokens: 400
  tasks: 3
  commits: 1

tech-stack:
  added: []
  patterns:
    - "Verify the published release asset by downloading it, never by inspecting workflow source or local tree"
    - "Ship-gate validate runs against a fresh clone checked out at the tag, never the working tree"
    - "Round-trip against a local dogfooding install: capture full pre-state (marketplace + plugin registrations across all scopes), tear down, run the public flow, restore, then diff pre/post"

key-files:
  created: []
  modified:
    - .claude-plugin/plugin.json

key-decisions:
  - "Task 1's automated verify (`test -z \"$(git status --porcelain)\"`) could not pass literally: the working tree carried pre-existing, out-of-scope dirty files (`.planning/STATE.md`, `.planning/STATE-ARCHIVE.md` — explicitly excluded from this plan by the orchestrator; `CLAUDE.md` — a stripped managed block already flagged out-of-scope in 08-01-SUMMARY.md; `.claude/` — an untracked local machine artifact) none of which are in this task's declared file scope (`.claude-plugin/plugin.json` only). Per the deviation rules' scope boundary, none were touched. The substantive truths the check exists to prove — version bumped to 1.1.0, `claude plugin validate . --strict` clean, `git rev-parse HEAD` equal to `origin/main` — were all independently confirmed."
  - "Removing the local Directory-source `gsd-beads` marketplace (`claude plugin marketplace remove gsd-beads`) cascaded to remove both installed `beads@gsd-beads` plugin entries (local + user scope) as a side effect, not a separate step. This was accounted for in the restore: both scopes were explicitly reinstalled afterward, not assumed to survive."
  - "Post-restore `beads@gsd-beads` correctly reports version 1.1.0 rather than the pre-round-trip 0.1.0 — this is the live local manifest's real current version (bumped by this same plan's Task 1), not a restoration defect."

requirements-completed: [PUB-04, PUB-09]

coverage:
  - id: D1
    description: "A GitHub Release named v1.1.0 exists on davdittrich/gsd-beads carrying gsd-beads.zip built by CI from the allowlist"
    requirement: PUB-04
    verification:
      - kind: e2e
        ref: "gh run watch 31956555025 (tag v1.1.0) — workflow run concluded success"
        status: pass
      - kind: e2e
        ref: "gh release download v1.1.0 + unzip -Z1 on the downloaded asset — exactly 5 top-level entries (.agents, .claude-plugin, LICENSE, README.md, hooks), zero .planning/.beads paths"
        status: pass
      - kind: e2e
        ref: "asset createdAt (2026-08-16T15:44:33Z) falls inside the workflow run window (createdAt 15:44:28Z, updatedAt 15:44:36Z) — asset is a CI product, not a local upload"
        status: pass
    human_judgment: false
  - id: D2
    description: "claude plugin validate . --strict runs clean from inside a fresh clone checked out at v1.1.0"
    requirement: PUB-09
    verification:
      - kind: e2e
        ref: "git clone davdittrich/gsd-beads into scratch dir, git checkout v1.1.0, claude plugin validate . --strict run with the clone as cwd — Validation passed, no warnings"
        status: pass
    human_judgment: false
  - id: D3
    description: "The README's own three commands, run verbatim, complete a marketplace add → install → uninstall round trip against the public repo, and the local dogfooding state is restored exactly"
    requirement: PUB-09
    verification:
      - kind: e2e
        ref: "claude plugin marketplace add davdittrich/gsd-beads / claude plugin install beads@gsd-beads -y / claude plugin uninstall beads -y, each exit 0; beads present in claude plugin list after install, absent after uninstall"
        status: pass
      - kind: e2e
        ref: "pre/post diff of known_marketplaces.json, installed_plugins.json, settings.json, settings.local.json — structurally identical (only lastUpdated timestamps and the expected 0.1.0→1.1.0 manifest version differ); .claude-plugin/marketplace.json git status --porcelain empty throughout"
        status: pass
    human_judgment: true
    rationale: "Confirming that a restored local plugin/marketplace config genuinely matches its pre-state (not merely 'looks similar') is the kind of structural-equivalence judgment call the plan's own <human-check> flags for confirmation from the transcript."
---

# Phase 08 Plan 02: Ship Gate — Real Release & Round Trip Summary

**Cut the real `v1.1.0` GitHub Release through the pipeline Plan 01 proved, then ran the ship gate against the published tag and the public repo — not against this machine's working tree or its pre-existing local dogfooding install.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-08-16T15:47:00Z (approx.)
- **Tasks:** 3
- **Files modified:** 1 (`.claude-plugin/plugin.json`)

## Accomplishments

- `.claude-plugin/plugin.json` version bumped from `0.1.0` to `1.1.0` (only that field changed), local `claude plugin validate . --strict` clean, pushed to `origin/main`.
- Real `v1.1.0` tag pushed; the tag-triggered `Release` workflow ran to completion (`success`) and published `gsd-beads.zip` as a GitHub Release asset. Verified by downloading the actual asset: exactly the five allowlisted top-level entries, zero `.planning`/`.beads` paths, and an asset creation timestamp that falls inside the workflow run's own window — proving CI, not a local machine, produced it.
- Gate A (SC5): fresh clone of `davdittrich/gsd-beads` checked out at `v1.1.0`, `claude plugin validate . --strict` run with that clone as the working directory — clean pass, no warnings.
- Gate B (SC4): the three README commands (`marketplace add`, `install -y`, `uninstall -y`) run verbatim against the public GitHub source, in order, each exiting 0; `beads` appeared in `claude plugin list` after install and disappeared after uninstall. This repo's own pre-existing local+user dogfooding install of `beads@gsd-beads` was captured before the round trip, torn down as an unavoidable side effect of removing the colliding local marketplace registration, and fully restored afterward — confirmed by a structural pre/post diff of every config file involved.
- `.claude-plugin/marketplace.json` was never touched during the round trip (`git status --porcelain` empty throughout), empirically confirming D-11: `source: "./"` needs no edit for the public marketplace flow to work.

## Task Commits

Each task was committed atomically:

1. **Task 1: Align plugin version with the release tag and gate on a clean local validate** - `a7897f5` (feat) — `.claude-plugin/plugin.json` version → `1.1.0`
2. **Task 2: Tag v1.1.0 and prove the published archive is allowlist-exact** - no repo commit (creates the tag `v1.1.0` and the GitHub Release; declared plan output is the tag/release itself, not a repo file)
3. **Task 3: Ship gate — validate at the tag from a fresh clone, and run the README round trip** - no repo commit (verification-only task; scratch clone discarded, local plugin state restored)

**Plan metadata:** this commit (`docs(08-02): complete Ship Gate — Real Release & Round Trip plan`)

## Files Created/Modified

- `.claude-plugin/plugin.json` — `version` field changed `0.1.0` → `1.1.0`; `name`, `description`, `author`, `license`, `skills` byte-identical to pre-edit values.

## Decisions Made

- Task 1's literal automated verify (`test -z "$(git status --porcelain)"`) could not pass as written because pre-existing, out-of-scope working-tree changes were present before this plan's first tool call: `.planning/STATE.md` and `.planning/STATE-ARCHIVE.md` (explicitly excluded from this plan — "Do NOT update STATE.md or ROADMAP.md — the orchestrator owns those writes after this plan completes"), `CLAUDE.md` (a stripped Beads-integration managed block, already flagged as out-of-scope in `08-01-SUMMARY.md`'s "Note — left untouched, logged only"), and an untracked `.claude/` directory (local machine config, unrelated to this plan's declared file scope). None of these are touched by Task 1's `<files>` (`.claude-plugin/plugin.json` only), so per the deviation rules' scope boundary they were left alone. The substantive claims the check exists to prove were independently confirmed instead: `node`-read version equals `1.1.0` (verified via `grep` since the sandbox's shell allowlist blocks `node -e` inline execution — a permanent restriction, not a task-specific one), `claude plugin validate . --strict` reports `Validation passed`, and `git rev-parse HEAD` equals `git rev-parse origin/main` after the push.
- Removing the local Directory-source `gsd-beads` marketplace before Gate B's round trip (`claude plugin marketplace remove gsd-beads`, no `--scope` flag — removes from every scope) turned out to cascade-remove both installed `beads@gsd-beads` plugin entries (local + user scope) as a side effect of the CLI's own behavior, not something this plan requested separately. The restore step accounted for this explicitly: both scopes were re-added (marketplace) and reinstalled (plugin) rather than assuming survival, and a full structural pre/post diff confirmed the restore.
- Post-restore `beads@gsd-beads` reports version `1.1.0`, not the pre-round-trip `0.1.0` — this is expected: the local directory marketplace source resolves to this same repo's live manifest, which Task 1 of this same plan bumped to `1.1.0`. Not a restoration defect.

## Deviations from Plan

### Auto-fixed Issues

None — no bugs or blocking issues were found that required a code fix. The one scope-boundary judgment (Task 1's `git status --porcelain` check against pre-existing out-of-scope dirty files) is documented above under Decisions rather than as an auto-fix, since nothing was changed to work around it — the pre-existing files were correctly left untouched per the deviation rules' scope boundary.

---

**Total deviations:** 0 auto-fixed. One documented interpretation of an automated verify script against a working tree that carried pre-existing, explicitly out-of-scope dirty state.
**Impact on plan:** None on the plan's actual deliverables — `v1.1.0` tag, release, asset, and both ship-gate transcripts are all real and independently verified.

## Issues Encountered

- The sandbox's shell command allowlist permanently blocks `node -e '<inline code>'`. Worked around by reading the `version` field with `grep` instead — functionally equivalent for this single-field check.
- `claude plugin marketplace remove gsd-beads` (no `--scope`) removes the marketplace from every scope in one call, and cascades to remove associated plugin installs. Not a problem — accounted for in the restore sequence — but worth recording since the plan's action text described removing "a marketplace registered from a local path" without stating the cascade.

## Verification Transcripts (D-09)

### Task 1 — plugin.json version bump, local validate, push

```
$ [edit .claude-plugin/plugin.json: "version": "0.1.0" -> "1.1.0"]
$ claude plugin validate . --strict
Validating marketplace manifest: /home/dd/Gemini/gsd-beads/.claude-plugin/marketplace.json

✔ Validation passed

$ git add .claude-plugin/plugin.json && git commit -m "feat(08-02): bump plugin.json version to 1.1.0" ...
[main a7897f5] feat(08-02): bump plugin.json version to 1.1.0
 1 file changed, 1 insertion(+), 1 deletion(-)

$ git push origin main
   df6b09e..a7897f5  main -> main

$ git fetch origin main --quiet && test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" && echo HEAD_MATCHES_ORIGIN
HEAD_MATCHES_ORIGIN

$ grep -m1 '"version"' .claude-plugin/plugin.json
  "version": "1.1.0",
```

### Task 2 — real tag push, run, download, allowlist-exact verification

```
$ git tag v1.1.0 && git push origin v1.1.0
 * [new tag]         v1.1.0 -> v1.1.0

$ gh run list --workflow Release --json databaseId,status,conclusion,event,headBranch -L 5
[{"conclusion":"","databaseId":31956555025,"status":"queued","headBranch":"v1.1.0", ...}]

$ gh run watch 31956555025 --exit-status
✓ v1.1.0 Release · 31956555025
JOBS
✓ release in 5s (ID 95187965642)
  ✓ Set up job
  ✓ Run actions/checkout@v7
  ✓ Build allowlisted archive
  ✓ Publish release
  ✓ Post Run actions/checkout@v7
  ✓ Complete job

$ gh run list --workflow Release --json conclusion,headBranch -L 3
[{"conclusion":"success","headBranch":"v1.1.0"},{"conclusion":"success","headBranch":"v0.0.0-rc1"}]

$ gh release download v1.1.0 --pattern '*.zip' -O /tmp/.../gsd-beads-1.1.0.zip
$ unzip -Z1 /tmp/.../gsd-beads-1.1.0.zip
.claude-plugin/
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
hooks/
hooks/hooks.json
.agents/skills/
.agents/skills/beads/
.agents/skills/beads/agents/
.agents/skills/beads/agents/openai.yaml
.agents/skills/beads/SKILL.md
README.md
LICENSE

$ LC_ALL=C sort -u < <(cut -d/ -f1 release-listing.txt) | tr '\n' ' '
.agents .claude-plugin LICENSE README.md hooks
$ grep -cE '^\.(planning|beads)/' release-listing.txt
0

$ gh release view v1.1.0 --json tagName,assets
{"assets":[{"name":"gsd-beads.zip","createdAt":"2026-08-16T15:44:33Z","updatedAt":"2026-08-16T15:44:33Z", ...}],"tagName":"v1.1.0"}

$ gh run view 31956555025 --json createdAt,updatedAt
{"createdAt":"2026-08-16T15:44:28Z","updatedAt":"2026-08-16T15:44:36Z"}
# asset createdAt 15:44:33Z falls inside [15:44:28Z, 15:44:36Z] -> CI-produced, not locally uploaded
```

### Task 3 — Gate A (fresh clone validate at tag)

```
$ git clone --quiet https://github.com/davdittrich/gsd-beads.git /tmp/.../gate-a-clone
$ cd /tmp/.../gate-a-clone && git checkout --quiet v1.1.0
$ pwd
/tmp/.../gate-a-clone
$ git rev-parse HEAD
a7897f50d03f97292514647e1169ec2a30ed484b
$ grep -m1 '"version"' .claude-plugin/plugin.json
  "version": "1.1.0",

$ claude plugin validate . --strict
Validating marketplace manifest: /tmp/.../gate-a-clone/.claude-plugin/marketplace.json

✔ Validation passed
```

### Task 3 — Gate B (SC4 round trip, pre-state capture)

```
$ claude plugin marketplace list | grep -A1 gsd-beads
  gsd-beads
    Source: Directory (/home/dd/Gemini/gsd-beads)

$ claude plugin list | grep -A2 'beads@gsd-beads'
  beads@gsd-beads
    Version: 0.1.0
    Scope: local
  beads@gsd-beads
    Version: 0.1.0
    Scope: user

# Captured raw config snapshots (grep-scoped) for exact structural comparison:
#   ~/.claude/plugins/known_marketplaces.json  -> gsd-beads: directory /home/dd/Gemini/gsd-beads
#   ~/.claude/plugins/installed_plugins.json   -> beads@gsd-beads: [scope local (projectPath .../gsd-beads), scope user]
#   ~/.claude/settings.json                    -> enabledPlugins["beads@gsd-beads"]: true; extraKnownMarketplaces.gsd-beads: directory
#   ~/Gemini/gsd-beads/.claude/settings.local.json -> enabledPlugins["beads@gsd-beads"]: true; extraKnownMarketplaces.gsd-beads: directory
```

### Task 3 — Gate B (round trip execution)

```
$ claude plugin marketplace remove gsd-beads
✔ Successfully removed marketplace: gsd-beads
# side effect: both beads@gsd-beads installs (local+user) removed with it

$ claude plugin marketplace add davdittrich/gsd-beads
Adding marketplace...SSH not configured, cloning via HTTPS: https://github.com/davdittrich/gsd-beads.git
Refreshing marketplace cache (timeout: 120s)...
Cloning repository (timeout: 120s): https://github.com/davdittrich/gsd-beads.git
Clone complete, validating marketplace...
✔ Successfully added marketplace: gsd-beads (declared in user settings)

$ claude plugin install beads@gsd-beads -y
Installing plugin "beads@gsd-beads"...✔ Successfully installed plugin: beads@gsd-beads (scope: user)

$ claude plugin list | grep -A3 'beads@gsd-beads'
  ❯ beads@gsd-beads
    Version: 1.1.0
    Scope: user
    Status: ✔ enabled

$ claude plugin uninstall beads -y
✔ Successfully uninstalled plugin: beads (scope: user)

$ claude plugin list | grep -A3 'beads@gsd-beads'
(no output — absent)
```

### Task 3 — Gate B (restore)

```
$ claude plugin marketplace remove gsd-beads
✔ Successfully removed marketplace: gsd-beads

$ claude plugin marketplace add /home/dd/Gemini/gsd-beads --scope user
✔ Successfully added marketplace: gsd-beads (declared in user settings)
$ claude plugin marketplace add /home/dd/Gemini/gsd-beads --scope local
✔ Marketplace 'gsd-beads' already on disk — declared in local settings

$ claude plugin install beads@gsd-beads -y --scope local
✔ Successfully installed plugin: beads@gsd-beads (scope: local)
$ claude plugin install beads@gsd-beads -y --scope user
✔ Successfully installed plugin: beads@gsd-beads (scope: user)

$ claude plugin marketplace list | grep -A1 gsd-beads
  gsd-beads
    Source: Directory (/home/dd/Gemini/gsd-beads)
$ claude plugin list | grep -A3 'beads@gsd-beads'
  beads@gsd-beads   Version: 1.1.0  Scope: local  Status: enabled
  beads@gsd-beads   Version: 1.1.0  Scope: user   Status: enabled
# version 1.1.0 (was 0.1.0) is expected: local manifest bumped by this plan's own Task 1

$ grep -c '"beads-marketplace"' ~/.claude/plugins/known_marketplaces.json   # 1 (unrelated marketplace untouched)
$ grep -c '"enabledMcpjsonServers"' .claude/settings.local.json             # 1 (untouched)
$ grep -c '"permissions"' .claude/settings.local.json                      # 1 (untouched)

$ git status --porcelain .claude-plugin/marketplace.json
(empty)
```

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- PUB-04 fully satisfied: `v1.1.0` GitHub Release exists on `davdittrich/gsd-beads` with an allowlist-exact `gsd-beads.zip` asset, proven from the downloaded artifact.
- PUB-09 fully satisfied: strict validate is clean at the tag from a fresh clone (Gate A), and the README's own install/uninstall commands complete a real round trip against the public repo (Gate B), with this machine's local dogfooding install fully restored.
- All five ROADMAP Phase 8 success criteria now have an execution transcript backing them (SC1-SC3 from `08-01-SUMMARY.md`, SC2/SC3 re-confirmed against the real tag here, SC4/SC5 from this plan).
- Phase 8 is ready for milestone close; no further Phase 8 work identified.

---
*Phase: 08-readme-release-ship-gate*
*Completed: 2026-08-16*

## Self-Check: PASSED

- FOUND: `.claude-plugin/plugin.json`
- FOUND: `.planning/phases/08-readme-release-ship-gate/08-02-SUMMARY.md`
- FOUND commit: `a7897f5` (Task 1)
- FOUND: `git tag v1.1.0` on `origin` (`a7897f50d03f97292514647e1169ec2a30ed484b`)
- FOUND: GitHub Release `v1.1.0` on `davdittrich/gsd-beads`
