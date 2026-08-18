---
phase: quick-260818-h2h
plan: 01
subsystem: plugin-packaging
tags: [plugin-marketplace, capability-loader, dogfood-cleanup]
dependency-graph:
  requires: []
  provides:
    - "plugins/beads-lifecycle/ scoped plugin root"
    - "beads-lifecycle release archive scoped to owned trees"
  affects:
    - .claude-plugin/marketplace.json
    - .github/workflows/release.yml
    - .gsd-capabilities.json
    - .gitignore
tech-stack:
  added: []
  patterns:
    - "Scoped plugin subdirectory (source: ./plugins/beads-lifecycle) instead of a publish-time filter script"
key-files:
  created:
    - plugins/beads-lifecycle/.claude-plugin/plugin.json
    - plugins/beads-lifecycle/hooks/hooks.json
    - plugins/beads-lifecycle/hooks/session-start.sh
    - plugins/beads-lifecycle/hooks/capability-auto-install.sh
    - plugins/beads-lifecycle/.agents/skills/beads/
    - plugins/beads-lifecycle/.gsd/capabilities/beads/
  modified:
    - .claude-plugin/marketplace.json
    - .github/workflows/release.yml
    - tests/test-capability-auto-install.sh
    - plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py
    - plugins/beads-lifecycle/.agents/skills/beads/resources/TROUBLESHOOTING.md
    - README.md
    - CHANGELOG.md
    - .gitignore
    - .gsd-capabilities.json
    - .planning/STATE.md (edited, not committed by this executor — see below)
decisions:
  - "Scoped plugin subdirectory over a publish-time filter script: exclusion holds by construction, verifiable statically with `claude plugin validate --strict`."
  - "sota-numerics and ponytail removed from the repo entirely (git rm -r), not just excluded from the package — both have their own external repos and were pure duplication of the already-working global installs."
  - "Task 0 (blocking-human decision) resolved by the user as fix-upstream-first before this executor started: davdittrich/sota-numerics fixed and pushed (65e42f8), global install refreshed to 0.1.1 on this machine."
  - "`.gsd-capabilities.json`'s `files` field left as the tool-regenerated `.gsd/capabilities/beads` (project-scope install destination), not hand-forced to the plugin source path — confirmed by a live `capability install` run that the field always tracks the install destination, not the source tree."
metrics:
  duration: "~8 min"
  completed: 2026-08-18
status: complete
actuals:
  tokens: 32000
  tasks: 3
  commits: 1
---

# Phase quick-260818-h2h Plan 01: Scope beads-lifecycle plugin source Summary

Moved the four trees `beads-lifecycle` actually owns into `plugins/beads-lifecycle/`, repointed `marketplace.json` and `release.yml` at the new root, deleted the two foreign capability trees (`sota-numerics`, `ponytail`) from the repo entirely, and reconciled every stale path reference this created — including a false decision record in `STATE.md`.

## What Was Built

**Task 1 — Relocate and repoint.** `git mv`'d `.claude-plugin/plugin.json`, `hooks/`, `.agents/skills/beads/`, and `.gsd/capabilities/beads/` into `plugins/beads-lifecycle/`. `git rm -r`'d `.gsd/capabilities/{sota-numerics,ponytail}/` (11 tracked files) — both are pure duplicates of the standalone repos `davdittrich/sota-numerics` and `davdittrich/ponytail-everywhere`, already consumed via global plugin installs. Repointed `marketplace.json`'s `beads-lifecycle.source` to `./plugins/beads-lifecycle` and bumped `plugin.json` to `1.2.1`. Left the `ponytail-everywhere`/`sota-numerics` url-type marketplace entries and the global installs under `$HOME/.gsd/capabilities/` untouched, as required.

**Task 2 — Repoint mechanical consumers.** Fixed `tests/test-capability-auto-install.sh`'s hardcoded `$REPO_ROOT/hooks/...` path and narrowed `release.yml`'s archive zip list from `.claude-plugin hooks .agents/skills .gsd README.md LICENSE` to `.claude-plugin plugins/beads-lifecycle README.md LICENSE`.

**Task 3 — Reconcile manifest, sweep stale claims, record findings.** Deleted the `ponytail` entry from `.gsd-capabilities.json`, repointed `beads`'s `source`. Corrected README's false release-archive claim and added a capability-ownership disclosure bullet. Repointed `CHANGELOG.md`, `.gitignore`'s comment, and `TROUBLESHOOTING.md`'s restore instruction. Corrected the false Phase 12 claim in `.planning/STATE.md` (no deletion commit for these two paths ever existed before this task). Recorded three `bd comments` on `gsd-beads-1iq`: the corrected root cause, the duplication-removal findings, and Task 0's resolution (upstream fix commit `65e42f8`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two `test_sync.py` assertions still hardcoded the pre-move repo-root path**
- **Found during:** Task 2 verify (pytest run after the move: 1 failed, 86 passed, 1 skipped)
- **Issue:** `test_capability_json_declares_epic_per_enum_key` and the module-level helper `_capability_json_has_beads_md_gate` both built `cap_path` as `project_root / ".gsd" / "capabilities" / "beads" / "capability.json"` — the pre-move path. The first raised `FileNotFoundError`; the second silently caught it and returned `False`, corrupting a `skipUnless` guard for a different test. A third occurrence in `test_beads_gate_hooks_excluded_step_hook_retained_when_ship_gate_false` ran a real `capability install ./.gsd/capabilities/beads --scope project` subprocess against the now-deleted path, which failed with `Local capability path does not exist`.
- **Fix:** Repointed all three to `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` (or the equivalent install-source arg). Also fixed the module docstring's stale path reference (Task 3 item 5, done inline since already in the file).
- **Files modified:** `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`
- **Verified:** Suite went from 1 failed/86 passed/1 skipped to 88 passed, matching the measured baseline.

**2. [Rule 2 - Missing critical functionality] `.gsd/` was untracked but not gitignored, risking re-tracking the exact defect this task fixes**
- **Found during:** Task 3, after the pytest suite's own reconsent step (see below) recreated `.gsd/capabilities/beads/` on disk as an untracked project-scope install copy.
- **Issue:** With zero tracked files under `.gsd/` but no ignore rule, `git status` would show `.gsd/` as untracked noise on every session, and a careless `git add -A` could re-track a foreign or vendored capability bundle — reintroducing the packaging defect this plan removes.
- **Fix:** Added a `.gsd/` ignore rule to `.gitignore` with an explanatory comment, replacing the narrower pre-existing `.gsd/dispatch-isolation-sentinel.json` line (now redundant, since it's covered by the broader rule).
- **Files modified:** `.gitignore`

### Evidence-based correction to the plan's literal instruction

**`.gsd-capabilities.json`'s `beads.files` field.** The plan (Task 3, item 0) instructed setting `files` to `"plugins/beads-lifecycle/.gsd/capabilities/beads"` (mirroring `source`). I made that edit, then Task 2's own pytest suite ran its "reconsent" step (`gsd-tools capability install ./plugins/beads-lifecycle/.gsd/capabilities/beads --scope project --yes`) as part of its own test setup, and the real tool regenerated `files` back to `.gsd/capabilities/beads`. Reading `~/.claude/gsd-core/bin/lib/capability-lifecycle.cjs:892/919` confirmed `files` is always set to `relCapDir` — the project-scope install *destination* (`<projectRoot>/.gsd/capabilities/<id>`), never the source tree. Forcing it back to the plugin path would have made the manifest lie about where the tool actually writes, and the very next real install would silently revert it anyway. Left the tool-generated value in place; `source` correctly still points at `./plugins/beads-lifecycle/.gsd/capabilities/beads`. All of Task 3's automated gates (no dangling `./.gsd/` source, no `ponytail` entry, correct `source`) still pass with this value.

### Out-of-scope discovery (not fixed, per SCOPE BOUNDARY rule)

Running the (now-working) `sota-numerics` `check-alternatives.py` gate directly against `.planning/phases/13-markdown-linting-capability-dogfood/` (to prove the Task 0 disposition end-to-end, per the plan's gate caveat) surfaced three pre-existing citation-date findings in Phase 13's plans (`13-01`, `13-02`, `13-03` — "no citation date" on named alternatives), unrelated to this quick task. Not fixed here; flagging for whoever next touches Phase 13's plans.

## Task 0 Disposition (resolved before this executor started)

Per the plan's `<resolution>` block: `fix-upstream-first` was selected and completed by the user prior to this run. `davdittrich/sota-numerics` fixed (script resolution now falls back project-scope-first, then global), committed as `65e42f8` and pushed to `origin/main`; this machine's global install refreshed to `0.1.1`, verified by direct file read. Confirmed post-deletion in this session: `render-hooks plan:post` shows the `sota-numerics` gate's rendered command resolving project-scope-first with a global fallback, `test -f "$HOME/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py"` succeeds, and running the gate command directly returns a real content-based exit code (not "gate script not found") — the gate evaluates, not skips, not fails closed.

## Verification Results

| Check | Result |
|---|---|
| `claude plugin validate ./plugins/beads-lifecycle --strict` | exit 0, names `plugins/beads-lifecycle/.claude-plugin/plugin.json` |
| `claude plugin validate .claude-plugin/marketplace.json --strict` | exit 0 |
| `find plugins/beads-lifecycle -iname capability.json` | exactly one, `beads` bundle |
| `git ls-files .gsd \| wc -l` | 0 |
| Global installs (`$HOME/.gsd/capabilities/{sota-numerics,ponytail}`) | untouched, present |
| `render-hooks plan:post` id-collision | 0 (baseline was 1) |
| `bash tests/test-capability-auto-install.sh` | ALL PASS, 6/6 (baseline 6/6) |
| `python3 -m pytest .../test_sync.py -q` | 88 passed (baseline 88, after Rule-1 fix) |
| Local release archive rebuild | `beads` bundle + manifest + hooks present, 0 foreign entries |
| `git log --follow` on relocated `sync.py` | 28 commits, history preserved |
| `git show HEAD^:.gsd/capabilities/{sota-numerics,ponytail}/capability.json` | both print, recoverable from history |
| Hand-review grep `.agents/skills/beads` bare-root survivors | only the documented `AGENTS.md:108` generator-owned exception |

## Self-Check: PASSED

- FOUND: `plugins/beads-lifecycle/.claude-plugin/plugin.json`
- FOUND: `plugins/beads-lifecycle/hooks/hooks.json`
- FOUND: `plugins/beads-lifecycle/.agents/skills/beads/SKILL.md`
- FOUND: `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`
- FOUND: commit `4d83504` in `git log --oneline`
- FOUND: `bd comments` on `gsd-beads-1iq` (3 comments added this session)

## Notes for Orchestrator

- This executor did **not** commit `.planning/STATE.md`, despite Task 3 requiring an edit to it (correcting the false Phase 12 decision record) — per this run's constraints, docs artifacts are left for the orchestrator's separate docs commit. The STATE.md edit is present on disk, uncommitted.
- Pre-existing unrelated uncommitted changes present at session start (`.planning/STATE-ARCHIVE.md`, `.planning/intel/API-SURFACE.md`, `CLAUDE.md`) were left untouched and unstaged — out of this task's scope.
- `.gsd-capabilities.json` carried a pre-existing uncommitted `beads` entry addition at session start (per the plan's own note); this task's edits were made surgically on top of that live state, not by regenerating the file.
