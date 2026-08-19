---
phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly
plan: 05
subsystem: infra
tags: [capability-removal, marketplace-topology, ci-verification, blast-radius-audit]

# Dependency graph
requires:
  - phase: 15-04
    provides: both plugins installed from the real gsd-beads marketplace, user-scope grants proven live, both ship:pre gates re-proven from the installed copy
provides:
  - repo-root `.gsd/capabilities/markdown-linting/` and `.gsd/capabilities/pr-workflow/` bundles removed from tracking and disk (ROADMAP SC-4)
  - `.gitignore` and `.gsd-capabilities.json` reconciled in the same commit as the removal
  - green CI on the pushed head, working `beads-lifecycle` marketplace round trip, continued global-scope activation of both extracted capabilities
affects: []

actuals:
  tokens: 22723
  tasks: 2
  commits: 1

tech-stack:
  added: []
  patterns:
    - "three-part single-commit removal (bundle git rm + .gitignore un-ignore-line deletion + ledger entry deletion), same shape as 4d83504's ponytail/sota-numerics removal after their own extraction"
    - "exhaustive tracked-file content audit outside .planning/ and .gsd/capabilities/ before any file is touched, with a per-file resolves/breaks verdict, so every repair lands in the same commit as the removal that orphans it"

key-files:
  created: []
  modified:
    - .gitignore
    - .gsd-capabilities.json
  removed:
    - .gsd/capabilities/markdown-linting/
    - .gsd/capabilities/pr-workflow/

key-decisions:
  - "D-00's 'stay untouched' clause for the repo-root dogfood copies is superseded by the operator's direct in-session instruction (quoted verbatim below), recorded on the record per the plan's objective rather than silently applied"
  - "Task 1's exhaustive reference audit found 3 tracked files outside .planning/ and .gsd/capabilities/ naming either capability id, not the 2 the plan's own verify step assumed -- the third, .claude-plugin/marketplace.json, is a url-type marketplace listing pointing at the external davdittrich/markdown-linting and davdittrich/pr-workflow repos and is correctly unaffected by local bundle removal. Recorded as a planning-verify discrepancy, not a code defect: no repair was needed for this file, and the finding is evidence the audit was exhaustive rather than assumed."
  - "The gsd-beads marketplace registered on this machine is a local Directory source (/home/dd/projects/gsd-beads, the primary checkout), not a URL fetch of the pushed repo. The primary checkout's local main branch remains at 170a427 (this plan's worktree base) after this plan's push -- a worktree push to origin/main does not fast-forward a sibling checkout's local branch. The beads-lifecycle round-trip below therefore proves the marketplace mechanism and beads-lifecycle's own scoped plugin source (plugins/beads-lifecycle/, untouched by this plan) work correctly; it is not proof that the round trip read the freshly-pushed commit's tree. CI-on-pushed-head (gh run list) is the check that verifies the actual push, independently."
  - "The pre-existing uncommitted .gsd-capabilities.json modification recorded in 15-04-SUMMARY (a bare updatedAt timestamp bump in the primary checkout) is NOT present in this plan's worktree at all -- worktrees only inherit committed state, and this worktree was forked from the already-committed 170a427. git status --porcelain was empty at the start of Task 2, confirmed before any edit. Nothing needed resolving/reverting here; the primary checkout's separate uncommitted state was untouched by this plan (worktree isolation), and is a fact about the primary checkout, not something this plan's own commit encountered or needed to reconcile."

requirements-completed: [D-00, D-02]

coverage:
  - id: T1
    description: "Absence proof, exhaustive reference audit, release-archive path verdicts, and ledger/ignore coupling recorded before any file changed"
    requirement: "D-00"
    verification:
      - kind: other
        ref: "git ls-files | grep -E '^(markdown-linting|pr-workflow)/' -> 0; test ! -e markdown-linting && test ! -e pr-workflow -> both absent; git log --all --diff-filter=A --name-only -- 'markdown-linting/*' 'pr-workflow/*' -> 0 (never existed as top-level dirs, in tracked history)"
        status: pass
      - kind: other
        ref: "git ls-files -z | xargs -0 grep -lE 'markdown-linting|pr-workflow' | grep -v '^\\.planning/' | grep -v '^\\.gsd/capabilities/' | sort -> .claude-plugin/marketplace.json, .gitignore, .gsd-capabilities.json (3 files, not the plan-assumed 2 -- see key-decisions)"
        status: pass
      - kind: other
        ref: "git grep -nE 'markdown-linting|pr-workflow' -- .github -> no match, exit 1"
        status: pass
      - kind: other
        ref: "git ls-files .gsd/capabilities/markdown-linting | wc -l -> 8; git ls-files .gsd/capabilities/pr-workflow | wc -l -> 9; git ls-files .gsd | wc -l -> 17"
        status: pass
    human_judgment: false
  - id: T2
    description: "Both bundles removed with every repair in one commit, pushed, CI green, beads-lifecycle round trip, both capabilities still active from user scope, no tag/release"
    requirement: "D-00, D-02"
    verification:
      - kind: other
        ref: "git rm -r .gsd/capabilities/markdown-linting .gsd/capabilities/pr-workflow (8+9 files); .gitignore's 2 un-ignore lines deleted; .gsd-capabilities.json's pr-workflow entry deleted; all 3 in commit 1e2ef59, git show --stat HEAD confirms"
        status: pass
      - kind: other
        ref: "bash tests/test-capability-auto-install.sh -> ALL PASS (6/6 cases); claude plugin validate . --strict -> Validation passed"
        status: pass
      - kind: other
        ref: "git push origin HEAD:main -> 170a427..1e2ef59 HEAD -> main; git ls-remote origin main -> 1e2ef59; git log origin/main..HEAD --oneline -> 0"
        status: pass
      - kind: other
        ref: "gh run list --branch main --limit 1 -> conclusion success, headSha 1e2ef591d42bd29f72e6d70afed70ad1d74722ec"
        status: pass
      - kind: other
        ref: "claude plugin marketplace update gsd-beads -> Successfully updated; claude plugin uninstall beads-lifecycle -y -> Successfully uninstalled (scope: user); claude plugin install beads-lifecycle@gsd-beads -y -> Successfully installed (scope: user); claude plugin list -> beads-lifecycle@gsd-beads present"
        status: pass
      - kind: other
        ref: "gsd-tools capability list --raw after removal -> markdown-linting and pr-workflow both present, status active, scope global, sourced from /home/dd/.claude/plugins/cache/gsd-beads/{id}/*/.gsd/capabilities/{id}"
        status: pass
      - kind: other
        ref: "git tag --points-at HEAD -> empty; gh release list --repo davdittrich/gsd-beads -> v1.2.0/v1.1.1 only, both predate this phase"
        status: pass
      - kind: other
        ref: "git log -1 --format=%B | grep -ciE 'co-authored-by|anthropic' -> 0"
        status: pass
    human_judgment: false

duration: ~25min
completed: 2026-08-18
status: complete
---

# Phase 15 Plan 05: Remove Repo-Root Dogfood Bundles Summary

**Both `.gsd/capabilities/markdown-linting/` (8 files) and `.gsd/capabilities/pr-workflow/` (9 files) were removed from tracking and disk in one commit (`1e2ef59`) alongside the two `.gitignore` un-ignore-line deletions and the `.gsd-capabilities.json` `pr-workflow` entry removal. Pushed to `origin/main` (170a427..1e2ef59), CI green on the pushed head, `beads-lifecycle` uninstall/reinstall round trip clean, and both extracted capabilities remain active from their global (user-scope) grants after the removal. No tag or release created.**

## Correction on the Record: D-00's "Stay Untouched" Clause Is Superseded

15-CONTEXT.md's D-00 contained the clause "the repo-root dogfood copies under `.gsd/capabilities/<id>/` stay untouched, same as Phase 12 D-04's distinction." **That clause no longer holds.** The operator gave an explicit direct instruction in-session, after D-00 was locked and after the plan-checker surfaced the conflict:

> "markdown-linting and pr-workflow must not be part of the gsd-beads repo. avoid any files leaking into that repo that do not belong there. markdown-linting and pr-workflow need to be in their own, separate repo each."

That instruction is the authority this plan executed under. Every other clause of D-00 is unaffected: separate public repo per plugin, fresh init with no history extraction, `gsd-beads` keeping the shared `marketplace.json`, `url`-type sources, README depth, and the validate + round-trip proof. D-02 (no new tag/release) is untouched and independently verified below.

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-18
- **Tasks:** 2/2
- **Files modified:** 2 (`.gitignore`, `.gsd-capabilities.json`); 17 removed (8 + 9 bundle files)

## Task 1: Audit Evidence (No File Changed)

### 1. History-Wide Absence Proof

```
$ git ls-files | grep -E '^(markdown-linting|pr-workflow)/' | wc -l
0
$ test ! -e markdown-linting && echo "no top-level dir on disk"
no top-level dir on disk
$ test ! -e pr-workflow && echo "no top-level dir on disk"
no top-level dir on disk
$ git log --all --diff-filter=A --name-only --format= -- 'markdown-linting/*' 'pr-workflow/*' | wc -l
0
```

Neither capability id ever existed as a top-level plugin subdirectory anywhere in this repository's tracked history. ROADMAP success criterion 4's literal wording ("both dogfood subdirectories") never had a literal referent — the bundles under `.gsd/capabilities/<id>/` are what the criterion was actually reaching for, confirmed as fact rather than asserted.

### 2. Exhaustive Reference Audit

```
$ git ls-files -z | xargs -0 grep -lE 'markdown-linting|pr-workflow' 2>/dev/null \
    | grep -v '^\.planning/' | grep -v '^\.gsd/capabilities/' | sort
.claude-plugin/marketplace.json
.gitignore
.gsd-capabilities.json
```

**3 files, not the 2 the plan's own verify step (`wc -l | grep -qx 2`) assumed.** Per-file verdict:

| File | Line(s) | Reference | Verdict |
|------|---------|-----------|---------|
| `.claude-plugin/marketplace.json` | 31, 34, 39, 42 | `"name": "markdown-linting"` / `"url": "https://github.com/davdittrich/markdown-linting.git"`; `"name": "pr-workflow"` / `"url": "https://github.com/davdittrich/pr-workflow.git"` | **Does not break.** These are `url`-type marketplace listings pointing at the two external, already-published repos (Plans 01/02). Nothing about local bundle presence/absence affects them. No repair. |
| `.gitignore` | 41, 42 | `!.gsd/capabilities/markdown-linting/`, `!.gsd/capabilities/pr-workflow/` | **Breaks (dangling negation)** once the bundles are gone. Repair: delete both lines, keep the surrounding block and comment. |
| `.gsd-capabilities.json` | 15-24 | `pr-workflow` entry, `"source": "./.gsd/capabilities/pr-workflow"` | **Breaks** — source path stops existing. Repair: delete the entry. `markdown-linting` has no entry to begin with (nothing to repair there). |

Both workflow files, checked explicitly by name per the plan's requirement:

```
$ git grep -nE 'markdown-linting|pr-workflow' -- .github
$ echo $?
1
```

No match in `.github/workflows/ci.yml` or `.github/workflows/release.yml` — neither references either capability. This is stated as an explicit finding, not passed over.

The third hit (`.claude-plugin/marketplace.json`) is a genuine discovery beyond the plan's own assumption and is recorded above rather than silently reconciled with the plan's expected count.

### 3. Release-Archive Path Check

`.github/workflows/release.yml`'s archive step:

```yaml
zip -r gsd-beads.zip \
  .claude-plugin \
  plugins/beads-lifecycle \
  README.md \
  LICENSE
```

| Path argument | Names either capability? | Resolves post-removal? |
|---|---|---|
| `.claude-plugin` | No | Yes — unaffected, contains only `marketplace.json` |
| `plugins/beads-lifecycle` | No | Yes — scoped to the beads-lifecycle plugin tree, no dependency on `.gsd/capabilities/{markdown-linting,pr-workflow}` |
| `README.md` | No | Yes |
| `LICENSE` | No | Yes |

All 4 archive path arguments resolve identically before and after the removal. No silent wrong-archive risk at the next `v*.*.*` tag.

### 4. Ledger and Ignore-Rule Coupling

`.gsd-capabilities.json` (project-scope ledger) before removal:
- `beads` entry, `source: "./plugins/beads-lifecycle/.gsd/capabilities/beads"` — retained, untouched.
- `pr-workflow` entry, `source: "./.gsd/capabilities/pr-workflow"` — removed (source path stops existing).
- `markdown-linting` — **no entry exists at all** in this ledger (confirmed by `jq` inspection and consistent with 15-04-SUMMARY's finding that only `pr-workflow` had a project-scope grant recorded here before this plan).

`.gitignore`'s capability-ignore block (lines 38-42 before removal):
```
.gsd/*
!.gsd/capabilities/
.gsd/capabilities/*
!.gsd/capabilities/markdown-linting/
!.gsd/capabilities/pr-workflow/
```
Required edit: delete the two un-ignore lines (41, 42) only. The block itself and its explanatory comment (which describes the mechanism, unchanged) stay byte-identical.

**Pre-existing uncommitted `.gsd-capabilities.json` modification:** 15-04-SUMMARY recorded a pre-existing uncommitted edit to `.gsd-capabilities.json` in the **primary checkout** (a bare `updatedAt` timestamp bump, predating Phase 15 entirely). This plan executes inside an isolated git worktree forked from the already-committed base commit `170a4279b08d3182cf9dceb470bb84a0c9763be2` — worktrees only inherit committed state, never a sibling checkout's uncommitted working-tree diff. `git status --porcelain` at the start of Task 2 in this worktree was empty, confirmed before any edit. The primary checkout's separate uncommitted state was never present here to resolve or revert; it remains whatever it was in the primary checkout, untouched by this plan.

## Task 2: Removal, Commit, Push, and Proof

### Removal and Repair (One Commit)

```
$ git rm -r .gsd/capabilities/markdown-linting .gsd/capabilities/pr-workflow
[8 files removed under markdown-linting/, 9 under pr-workflow/ -- exact counts Task 1's audit predicted]
```

`.gitignore` edited: deleted lines 41-42 (`!.gsd/capabilities/markdown-linting/`, `!.gsd/capabilities/pr-workflow/`); block and comment (lines 25-40) byte-identical to before.

`.gsd-capabilities.json` edited: deleted the `pr-workflow` entry (lines 15-24 of the pre-edit file); `beads` entry untouched; file re-validated as parseable JSON via `jq .`.

Local CI step run before commit:
```
$ bash tests/test-capability-auto-install.sh
PASS: case1 .. case6
ALL PASS
```

Plugin manifest validation before commit:
```
$ claude plugin validate . --strict
Validating marketplace manifest: .../.claude-plugin/marketplace.json
✔ Validation passed
```

Committed as `1e2ef591d42bd29f72e6d70afed70ad1d74722ec`:

```
$ git show --stat HEAD
 .gitignore                                         |   2 -
 .gsd-capabilities.json                             |  10 -
 .gsd/capabilities/markdown-linting/README.md       | 113 -----
 .gsd/capabilities/markdown-linting/capability.json |  67 ---
 .../markdown-linting/config/.rumdl.toml            |   7 -
 .gsd/capabilities/markdown-linting/scripts/lint.py | 263 -----------
 .../skills/markdown-linting-report/SKILL.md        |  61 ---
 .../markdown-linting/tests/fixtures/clean.md       |  27 --
 .../markdown-linting/tests/fixtures/dirty.md       |  17 -
 .../markdown-linting/tests/test_lint.py            | 308 ------------
 .gsd/capabilities/pr-workflow/capability.json      |  77 ---
 .gsd/capabilities/pr-workflow/scripts/pr_status.py | 330 -------------
 .../pr-workflow/skills/pr-workflow-report/SKILL.md |  80 ----
 .../pr-workflow/tests/fixtures/checks_fail.json    |   1 -
 .../pr-workflow/tests/fixtures/checks_pass.json    |   1 -
 .../pr-workflow/tests/fixtures/checks_pending.json |   1 -
 .../tests/fixtures/checks_skipping.json            |   1 -
 .../pr-workflow/tests/fixtures/pr_list_empty.json  |   1 -
 .../pr-workflow/tests/test_pr_status.py            | 521 ---------------------
 19 files changed, 1888 deletions(-)
```

All 3 edits (bundle removal x2, `.gitignore`, `.gsd-capabilities.json`) landed in this ONE commit, verifiable above. Commit body states explicitly that both workflow files were audited and needed no change.

### Push

```
$ git push origin HEAD:main
   170a427..1e2ef59  HEAD -> main
$ git ls-remote origin main
1e2ef591d42bd29f72e6d70afed70ad1d74722ec  refs/heads/main
$ git log origin/main..HEAD --oneline | wc -l
0
```

Plain push, no `--force`, local HEAD and `origin/main` identical afterward.

### CI on the Pushed Head

```
$ gh run list --branch main --limit 1 --json conclusion,headSha
[{"conclusion":"success","headSha":"1e2ef591d42bd29f72e6d70afed70ad1d74722ec"}]
```

Green on exactly the pushed commit (waited for the in-progress run to complete via `gh run watch`).

### `beads-lifecycle` Round Trip

```
$ claude plugin marketplace update gsd-beads
✔ Successfully updated marketplace: gsd-beads
$ claude plugin uninstall beads-lifecycle -y
✔ Successfully uninstalled plugin: beads-lifecycle (scope: user)
$ claude plugin install beads-lifecycle@gsd-beads -y
✔ Successfully installed plugin: beads-lifecycle@gsd-beads (scope: user)
$ claude plugin list | grep beads-lifecycle
  ❯ beads-lifecycle@gsd-beads
```

Ends installed and enabled — the machine ends in the state it started in.

**Caveat recorded on the record:** `claude plugin marketplace list` shows `gsd-beads`'s registered source is `Directory (/home/dd/projects/gsd-beads)` — the **primary checkout**, not a URL fetch of the pushed repo. A `git push` from this worktree updates `origin/main` on the remote only; it does not fast-forward a sibling checkout's local `main` branch. Confirmed read-only: the primary checkout's `git rev-parse --abbrev-ref HEAD` is `main` at `170a427` (this plan's own worktree base commit, i.e. pre-removal), with its own pre-existing unrelated `M .gsd-capabilities.json` (the bare timestamp bump 15-04-SUMMARY described). This plan's worktree isolation means that file was never touched here. The round trip above therefore proves the marketplace mechanism and `beads-lifecycle`'s own scoped plugin source (`plugins/beads-lifecycle/`, entirely untouched by this plan's removal) both work — it is not proof that the round trip specifically read the freshly-pushed tree. The `gh run list` check above is the independent proof that CI evaluated the actual pushed commit.

### Post-Removal Capability Activation

```
$ node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability list --raw
```

Relevant entries (full output is long — both extracted capabilities plus first-party runtime/feature entries):

```json
{
  "id": "markdown-linting", "role": "feature", "version": "0.1.0", "tier": "full",
  "source": "/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0/.gsd/capabilities/markdown-linting",
  "scope": "global", "status": "active", "surfaced": true, "title": "Markdown linting"
},
{
  "id": "pr-workflow", "role": "feature", "version": "0.1.0", "tier": "full",
  "source": "/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0/.gsd/capabilities/pr-workflow",
  "scope": "global", "status": "active", "surfaced": true, "title": "PR workflow"
}
```

Both remain listed and `active` from their global (user-scope) grants after the repo-copy removal — confirming the removal is safe rather than merely tidy, as Plan 04's dual-scope observation predicted. `pr-workflow`'s previous project-scope duplicate entry (visible in 15-04-SUMMARY's dual-listing finding) is correctly gone now that `.gsd-capabilities.json`'s project-scope entry for it was removed in this plan's commit.

### D-02: No Tag, No Release

```
$ git tag --points-at HEAD
[empty]
$ git tag --list
v1.0
v1.1.1
v1.2.0
$ gh release list --repo davdittrich/gsd-beads
v1.2.0   Latest   v1.2.0   2026-08-16T21:57:40Z
v1.1.1            v1.1.1   2026-08-16T21:07:36Z
```

No tag points at the removal commit; the only two GitHub releases both predate this phase (2026-08-16). D-02 satisfied.

### No AI Attribution

```
$ git log -1 --format=%B | grep -ciE 'co-authored-by|anthropic'
0
```

## Deviations from Plan

### 1. Task 1's exhaustive-reference-audit count is 3, not the plan's assumed 2

**Found during:** Task 1.
**Issue:** The plan's own `<verify>` automated check (`... | wc -l | grep -qx 2`) assumed exactly 2 tracked files outside `.planning/` and `.gsd/capabilities/` would name either capability id. The actual exhaustive `git grep` returned 3: `.claude-plugin/marketplace.json`, `.gitignore`, `.gsd-capabilities.json`.
**Root cause:** The plan author did not anticipate that the two capabilities' `url`-type marketplace listings (added by Plans 01/02, present since before this plan started) would also match the grep — a legitimate, expected reference that the removal does not affect.
**Resolution:** No code or file change needed — `marketplace.json`'s listings correctly continue to point at the external `davdittrich/markdown-linting` and `davdittrich/pr-workflow` repos regardless of local bundle presence. Recorded as a planning-verify-assumption correction, per-file verdict given in full in the audit section above, rather than silently reconciling the count to match the plan's stated number. This is not a Rule 1-4 code deviation (no file was touched in Task 1 by design) — it's a finding that the plan's own verify command undercounted, documented here so a future reader does not assume the audit stopped short.

No other deviations. Task 2 executed exactly as written, all edits landed in the single required commit, and every verification step in the plan passed as specified.

## Known Stubs

None.

## Threat Flags

None. All 8 threats registered in this plan's `<threat_model>` (T-15-29 through T-15-36) were mitigated exactly as their disposition specified: the removal named only the two per-capability paths (verified via `git ls-files .gsd | wc -l` = 0 and the `beads` ledger entry surviving); every repair landed in the same commit as the removal (`git show --stat HEAD`); the local CI step and `claude plugin validate . --strict` both ran and passed before the push; `gh run list` confirmed the pushed head green; the release-archive path list was enumerated with a resolve verdict per argument; the `beads-lifecycle` round trip ended installed and enabled; `git tag --points-at HEAD` / `gh release list` confirmed no new tag/release (D-02); and the pre-existing uncommitted `.gsd-capabilities.json` edit was recorded as not present in this worktree at all (T-15-36), rather than swept into the commit via a whole-tree stage.

## Self-Check: PASSED

- `.gitignore` — FOUND, `!.gsd/capabilities/{markdown-linting,pr-workflow}/` lines confirmed absent (`grep -c '^!\.gsd/capabilities/[a-z]'` = 0).
- `.gsd-capabilities.json` — FOUND, parses as valid JSON (`jq .`), `entries` keys = `beads` only.
- `.gsd/capabilities/markdown-linting/`, `.gsd/capabilities/pr-workflow/` — MISSING (as intended): `test ! -e` confirmed both, `git ls-files .gsd` = 0.
- Commit `1e2ef59` — FOUND: `git log --oneline --all | grep 1e2ef59` matches; `git ls-remote origin main` returns the same SHA.
- `.planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-05-SUMMARY.md` — this file, committed in the plan's final metadata commit.

---
*Phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly*
*Plan: 05*
*Completed: 2026-08-18*
