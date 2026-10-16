# Changelog

## Unreleased

### Changed
- **`close-phase-epic` closes the phase epic at `verify:post` and `ship:pre`.** A new `gsd-beads-close` skill, dispatched by two new `produces: []` capability steps, runs it. gsd-core 1.17 dispatches `verify:post` before the verifier writes `VERIFICATION.md` in execute-phase, and `--after-fingerprint` skips steps whose produced file exists, so the `BEADS.md`-producing status step is skipped in verify-work; `[]` never skips, and `ship:pre` steps run only when no gate blocks, after `VERIFICATION.md` is final. `close-phase-epic` regenerates `BEADS.md` first (acts only if that succeeds), then runs `bd close` on the epic only when `<NN>-VERIFICATION.md` has `status: passed` (case-insensitive), `beads.epic_per` is `phase`, `BEADS.md` shows `blocking_open: 0` and `diverged: 0`, the epic has at least one child, all closed, and it is not a milestone epic. Otherwise the epic stays open and open child ids are printed; already closed is a no-op. A `bd` timeout or failure appends a Blockers/Concerns note and never fails the phase. `beads-status` Step 2b is regenerate-only again. This supersedes the 0.9.0 "closes nothing" line. Refs #26.
- **`gsd-beads-close` also prints a reconcile report.** New read-only `sync.py reconcile-report <phase directory>` runs in the same fence right after `close-phase-epic`, at the same two dispatch points (`verify:post`, `ship:pre`; `produces: []`, so `--after-fingerprint` never skips them). It prints "Reconcile before completing" with id, status and age of every non-closed ticket (deferred counts as open) that `BEADS-RECALL.md` matched or that is an epic child no plan task names, never the phase epic itself; with `epic_per=milestone` every phase lists all milestone-epic children no plan names. Silent when none and nothing degraded; a degraded source prints a note; a `bd` failure adds a `STATE.md` blocker and exits `0`. No dedup. It never closes or updates and does not touch `blocking_open` or `ship_override`. Closes #27.

## 0.9.3

Plugin 1.8.3, capability 0.9.3.

### Fixed
- **Prose in `<read_first>` reaches bd unaltered.** The task description split `<read_first>` on every comma into `- ` bullets, so `(recipe, dispositions, OOM rule)` became three bullets with a doubled `- -`. A single line now splits on commas only when every piece is a bare path; otherwise each line is one item, verbatim, and interior blank lines are kept.
- **`authoritative` strips a task body only after bd confirms it.** One batched `bd show` must return the description and acceptance criteria that were sent (line endings and trailing spaces ignored). A mismatch gets one `bd update` repair and a re-check; if it still differs, or `bd` fails, the task stays in `PLAN.md` and gets no native `tracker-id`. Refs #24.

## 0.9.2

Plugin 1.8.2, capability 0.9.2.

### Fixed
- **`PRIME.md` names the beads skills by their invocable ids.** The Sync points table listed `beads-recall`, `beads-sync` and `beads-status`; the Skill tool resolves only `gsd-beads-recall`, `gsd-beads-sync` and `gsd-beads-status`, so an agent following the table got `Unknown skill`. `tests/test-prime-skill-ids.sh` now fails CI when a table id matches no skill `name:`. Fixes #23.

## 0.9.1

Plugin 1.8.1, capability 0.9.1.

### Added
- **`lifecycle-dispatch` accepts an explicit phase.** `sync.py lifecycle-dispatch <point> [phase]` takes a phase token (`2`, `02`) or a directory under `.planning/phases/` and uses it instead of `STATE.md`'s `current_phase`; omitting it keeps the old behaviour. The argument is resolved once and confined to a direct child of `.planning/phases` for token, name and path alike (a symlinked child is refused); invalid input exits 0 with a stderr notice. The `PostToolUse` hook still cannot supply it until gsd-core carries phase context (gsd-core#4030). Refs #5.

### Changed
- Marketplace pins: ponytail-everywhere 0.9.4, sota-numerics 0.2.3.

## 0.9.0

Plugin 1.8.0, capability 0.9.0. Ticket ids are `gsd-beads-cjbc.N`.

### Changed (behaviour)
- **`verify:post` is read-only.** It regenerates `BEADS.md` and closes nothing; plan completion is defined once (.6).
- **Skills fail closed.** The resolver fence runs the installed global `sync.py`, then the plugin copy, and stops with an error when neither exists. It never runs the project's own copy. Fences run `python3 -I`, and an unset `CLAUDE_PLUGIN_ROOT` leaves the plugin rung empty (.23, .40).
- **Auto-install narrowed.** The SessionStart hook no longer installs from a `--plugin-dir` or local path without a matching owner, rolls back half-installs, refuses downgrades, waits boundedly for the lock, and installs from a stable source path so `capability update` can re-fetch (.22, .23, .29).
- **Ship gate fails closed.** A failed `bd list` or unavailable `bd` writes `unknown` counts, which block the gate. Blocking `ship:pre` gates carry `onError: halt`, so a gate that errors halts the ship (.2). The override prose now covers `unknown`: `ship_gate: false` records an override whenever a field is not `0` (.36).
- **Ship re-checks live state.** gsd-core evaluates the `ship:pre` gates on the `verify:post` snapshot and runs steps only after them. Step 2c now regenerates `BEADS.md` first and stops the ship when the fresh counts are not `0`; with the local `ship.md` patch lost, only the snapshot gate remains (.70).
- **Root-manifest layout.** `capability.json` and `.claude-plugin/` sit at the repository root, so install by git URL works and the whole clone is copied (.28).
- **Orphan sweep closes only `gsd-sync`-labelled children.** Task issues created before 0.8.0 carry no label: when one is removed from a plan it stays open and counts in `blocking_open`, so the ship gate blocks. Close such issues by hand (.21).
- **Milestone scoping.** With `epic_per: milestone`, the orphan sweep and the `open`/`closed` counts cover only the current phase's issues (.9). An open issue under the milestone epic that no plan of any phase names counts in every phase's `blocking_open`, and an unreadable plan in a sibling phase makes the counts `unknown` (.47).
- **Release is gated.** `release.yml` runs CI at the tagged commit, requires tag == `plugin.json` version, requires the tagged commit to be an ancestor of `origin/main`, and never republishes a release made from a different commit. Rerunning the workflow on the same commit re-uploads `gsd-beads.zip` with `--clobber`; the release notes carry `Release commit: <sha>` to tell the two cases apart (.4, .39, .59). `ci.yml` runs on branch pushes and pull requests, so a tag runs CI once (.39).
- **One skill is exposed.** The `beads-lifecycle` marketplace entry lists `skills: ["./.agents/skills/beads"]`; a real install showed 5 skills before and 1 after (.37). That limit holds for Claude Code only: Codex ignores the marketplace-entry key and loads every `plugin.json` `skills` path. Listing the four `gsd-beads-*` skills there (.62) made Codex show each twice (`beads-lifecycle:gsd-beads-sync` beside the capability's `gsd-beads-sync`), and `capability set beads --disable` left the plugin copies visible. `plugin.json` lists only `./.agents/skills/beads` again; the capability projects the four others and `--disable` hides them. Checked with Claude Code 2.1.296 (`claude plugin details`: 1 skill) and Codex CLI 0.162.1 (`skills/list`: 4 skills enabled, 0 after disable besides `beads`) (.67).
- **`.gsd-capabilities.json` is deleted.** It pointed at a removed path; the version test now reads `capability.json` and `plugin.json` (.38).

- **Phase mentions are files, not prose.** A token with a `/` counts, except one starting with `../` or `/`, a numeric-only or very short one, and one whose first segment looks like a hostname unless that directory exists (`example.com/docs`, URLs). A bare name (no `/`) counts only when it is an existing file in the project root (`README.md`, `main.c`, `capability.json`), so `example.com` and `Node.js` do not count unless a root file has that name; it matches other plans' files by exact path, so `README.md` does not match `docs/README.md`. A nested file or one not created yet needs a path with a slash (`./CONTRIBUTING.md`) (.26, .36, .41).
- **gsd-core floor is 1.11.0.** `capability.json` `engines.gsd`, the README and the registry entry required `>=1.10.0`, but 1.10 `ship.md` has no generic gate arm and silently drops the whole `ship:pre` gate; `onError: halt` is honoured from 1.11.0 (.61).
- **Issue creation is idempotent.** Every `bd create` carries a `gsd-key:` label (`<phase>-<plan>-t<n>` per task, `<phase>-epic`, `milestone-<slug>`, `todo-<hash>`) and is preceded by a lookup on that label plus the exact title, so a rerun after a kill, timeout or failed plan write adopts the open issue instead of creating a duplicate the orphan sweep then closes. A closed match is never reused, and a closed milestone epic is no longer reused by title. A `bd create` timeout now takes the fail-open notice path; it used to be uncaught in `create-issues`. Issues created before this release carry no key and still resolve only through their stored `<beads-id>`/`beads_epic`. A task that resolves to an issue another task in the plan already holds (a duplicate task name) stops the sync with a STATE blocker (.44).
- **One BEADS file per phase.** gsd-core's ship gate reads the first of `<phase>/BEADS.md`, `<phase>/.planning/BEADS.md` and any `*-BEADS.md`, so any file besides the generated `NN-BEADS.md` could answer it. `regenerate-beads-md` now removes extras it generated (a renumbered phase's `NN-BEADS.md`) and renames any other one to `<name>.rejected-<timestamp>` (content kept), with a stderr notice naming the files, a stdout notice that gives only their count (.68), a STATE blocker, `unknown` counts and exit 1. Every later run repeats all of that while any `*BEADS.md.rejected-*` file remains in the phase dir or its `.planning/`, until the user removes it (.67). A hand-written plain `BEADS.md` used to be kept with a warning. `ship-override` records nothing while another candidate exists or when `NN-BEADS.md` lacks `generated_from:` frontmatter (.43).
- **Plan completion is an allowlist.** A SUMMARY.md marks its plan's tasks done only when its top-level `status` is `complete` (case, quotes and a trailing ` # comment` ignored) or absent, as in SUMMARYs written before the field. Any other value -- `halted`, `incomplete`, an empty or unknown status -- skips every task of the plan and its `resolves_issues:` marker; `blocked` still contributes nothing. Unknown values used to close every task (.48).
- **CI verifies its tools.** The gsd-core runtime installs from the lockfile in `.github/ci/gsd-core/` with `npm ci --ignore-scripts`, so the top package and every dependency (`claude-agent-sdk`, `ws`, ...) are checked against sha512 integrity values and none runs an install script. An earlier tarball sha512 gate covered only the top package. `ci.yml` also runs actionlint, a release binary pinned by sha256 (.60, .67).
- **Minimum `bd` is 1.2.2.** `sync.py` checks `bd --version` once per process; an older `bd` prints one notice and takes the bd-unavailable path. Version output it cannot parse proceeds to the usual availability probe (.63).

### Fixed
- **Repository-controlled text no longer reaches the agent's context.** `hooks/lifecycle-dispatch.sh` promotes `sync.py`'s stdout into `additionalContext`, and the rejected-file notice printed planted file names there, which can carry newlines and `<beads_status>` tags. Repository-controlled file names, `bd` stderr, and the `bd list` and plan-read error text of `beads-recall` now go only to stderr. Repository-controlled values that stay on stdout lose control characters, `<`, `>` and backticks: task names, the milestone title, `depends_on` and beads ids, and the phase directory name in the dispatch verbs, and file, plan and task names in `ship-override`, `migrate-todos`, `close-wave` and `status`. Those skill verbs sanitize rather than move text, because the agent that runs them reads both streams. `check-patch` still prints its `ship.md` path, which comes from `CLAUDE_CONFIG_DIR`, not the repository (.68).
- `bd list` passes `-n 0`, so rows past 50 are seen (.7). Stored task ids are verified with one `bd` call and existing edges are skipped (.14).
- `beads_epic` is replaced rather than duplicated, and only a confirmed not-found counts as absent (.3).
- `create_issues` persists plan identity per created issue with atomic writes (.5).
- `migrate-todos` deletes a todo only after a confirmed bd id and survives per-file `bd` errors (.20).
- Task stripping ignores tags quoted in code spans (.8).
- Frontmatter parsing, table-cell escaping, recall decoding and root guards are hardened (.27). Seven `bd`-unavailable tails fold into one helper and dead `check_patch` branches go (.15).
- Generated artifacts are never written through a symlink; epic ids and counts are validated before `bd` or `git` runs; dispatch skips an interrupted `render-hooks` call (.11).
- SessionStart stdout stays pure hook JSON and a symlinked `.beads` is refused (.24).
- `ship_override`, recall, dispatch and the `bd` cwd are hardened (.26).
- Every hook and resolver `python3` runs isolated, so a planted stdlib module cannot execute (.1).
- Docs: `blocking_open` has one definition and `bd` 1.3.1 behaviour is corrected (.25); stale step pointers and the stale `check_shipmd_patch` name are fixed, README states what happens when `bd` is missing, and the ship gate reads the `verify:post` `BEADS.md` snapshot (.16, .40); agent prose is cut (.16).
- CI: bd tarball sha256 check, commit-pinned actions and gsd-core fixture, read-only token, session-start test, skip guard also matches `expected failures=` (.10, .12, .39). Repo hygiene (.17). Hook tests fail on hook errors (.13).
- Hook spy tests run the hook's real `python3 -I`: a PATH wrapper execs a venv whose `sitecustomize` loads the case's spy, so no flag is stripped (.58).
- A SIGKILLed hook no longer leaks its staging or parked-source dir: the next run sweeps them under the lock. The 30s lock-wait clamp is tested (.55).
- The leaked-source sweep restores the parked source unless both tree hashes succeed and match; two failed hashes used to compare equal and keep an unhashable candidate recorded (.67).
- The hook parks an empty prev dir even when no stable source existed, so a SIGKILL after the candidate is swapped in is swept and the unconsented first source removed (.67).
- The CI-order test also requires the lockfile integrity check against `GSD_CORE_INTEGRITY` before the gsd-core install (.67, .68). It ignores comment lines, so a token in a `ci.yml` comment no longer satisfies it, requires `npm ci --ignore-scripts` after that check, and requires `.github/ci/gsd-core/package.json` to pin exactly `1.12.0`. `ci.yml` drops its separate lockfile-version check: `npm ci` fails when `package.json` and the lockfile disagree (.68).
- `capability-auto-install.sh --consent` without a capability id prints usage to stderr; it used to exit silently (.67).
- The consent command reaches the user: SessionStart adds it as `systemMessage` to the hook JSON (bd's or its own), because Claude Code shows stderr from a hook that exits 0 only in its debug log. The user, not an agent, runs it (.67). A `systemMessage` that `bd prime` already set is kept and the request is appended; `bd prime` output that is not a JSON object passes through unchanged and the request goes to stderr only (.68).
- A consent-blocked install leaves the recorded source untouched and prints one command, `bash <plugin-root>/hooks/capability-auto-install.sh --consent beads`, which installs under the same lock with `--yes`. An already-consented install converges without asking (.42).
- Two runtimes whose caches carry the same capability version with different bytes no longer reinstall on every switch: the hook keeps the other runtime's verified install unless its own cache is newer, and still projects and records that kept install for its own runtime, since the other runtime's install never projects this one's skills root (.54, .67). The kept install's own `capability.json` selects the skills the hook guards, projects and fingerprints; this cache's list used to, so a skill only the cache listed failed the ownership check (.68). A Codex cache still on plugin 1.6.0 runs the old hook, which downgrades the shared install; update that plugin (.54).
- Recall matches a slash mention to a file by equality or as a whole-segment suffix, never by substring, and ignores a leading `./` on both sides and in the description fallback (.45).
- The milestone-epic divergence notice names a closed epic whose title matched and was ignored, instead of claiming none matched (.67).
- STATE.md blocker notes are appended under a lock with an atomic replace, so two concurrent appenders both land, and a `### Blockers/Concerns` heading inside a code fence is ignored (.50).
- Concurrent `create-issues` and STATE.md notes lock the regular file `.planning/.gsd-beads.lock` instead of a directory fd, which fails with EBADF on NFS. A lock that cannot be taken prints one stderr notice and the call proceeds unlocked; a STATE.md note that cannot be written is dropped with a notice, and no `OSError` escapes `create-issues` (.67). Add `.planning/.gsd-beads.lock` to the project's `.gitignore`: `bd init` (1.3.1) does not ignore it, and `/gsd:fast` stages it with `git add -A` unless `commit_docs` is `false` (.68).
- `close-wave` and `reconcile-stale-closed` close nothing, and print the bd-unavailable notice, when the bd status query fails; they used to treat every id as open and try to close it (.51).
- Every `sync.py` verb runs `bd` from the project root; `status`, `migrate-todos`, `lifecycle-dispatch` and `resolve-task-content` used to use the process cwd (.52). Every phase or plan argument finds that root from the phase directory's parent through one helper, so a planted `<phase>/.planning/` can no longer redirect `bd`, the config read or the STATE.md blocker (.67).
- `migrate-todos` reports a todo whose issue was created but whose file could not be deleted under its own heading, not as a `bd create` failure (.53).


## 0.8.1

### Security
- **A cloned repository could run its own `.gsd/capabilities/beads/scripts/sync.py` through the lifecycle hook and every beads skill.** `hooks/lifecycle-dispatch.sh` and the ten skill resolver fences tried the project copy first, so any repository shipping that path ran arbitrary code on a `render-hooks` call or a skill invocation. Selection is now keyed on the global manifest, which a repository cannot plant: with `${GSD_HOME:-$HOME}/.gsd/capabilities/beads/capability.json` present (any filesystem entry, including a dangling symlink or a directory) the global script runs and a missing or non-file script fails closed; otherwise the plugin copy; the project copy only last, so project-scope-only installs keep working. Without an absolute `GSD_HOME` or `HOME` nothing runs (skills exit 1 naming the cause; the hook exits 0 silently), so an empty `HOME` or a relative `GSD_HOME` cannot redirect resolution into the project. `PRIME.md` and the README no longer document a cwd-relative manual `sync.py lifecycle-dispatch` command; they point at the `gsd-beads-sync` resolver fence instead. Inside a gsd-beads development checkout the skills and hook now run the installed global `sync.py`, not the working tree's: reinstall the capability after editing `scripts/sync.py`. ([GH#20](https://github.com/davdittrich/gsd-beads/issues/20))

## 0.8.0

### Added
- **Every bd epic and task that `beads-sync` creates from a `PLAN.md` now carries the `gsd-sync` label.** External tools (for example the planning-with-beads ticket-template validator) could not tell PLAN.md-rendered issues from hand-written ones, so synced issues -- whose bodies are machine-rendered from task tags and parsed back by `resolve_task_content` -- were flagged as malformed tickets. `resolve_milestone_epic`, `resolve_epic` and `resolve_issue` pass `-l gsd-sync`; hand-shaped todo migrations stay unlabelled. Rendered bodies and parsing are unchanged; historical issues are not relabelled.

## 0.7.4

### Fixed
- **`parse_plan` counted a `<task>` literal quoted in prose (backticked or fenced) as a real opener, failing the one-to-one opener/closer invariant for the whole plan -- and, since the cross-plan authority preflight parses every sibling plan, for the whole phase.** Because every lifecycle dispatch point is `onError: skip`, the failure was invisible: `create-issues` failed for every plan in the phase, `regenerate-beads-md` crashed outright (uncaught `PlanParseError`) so `BEADS.md` silently froze, and `execute:wave:pre`'s `<beads_status>` block crashed the same way. `parse_plan` now runs the opener/closer check and task-block discovery against a length-preserving masked copy of the plan text with every fenced code block and inline code span blanked out, so a documented `<task>` literal in prose is ignored and a whole balanced example block quoted inside a fence is no longer discovered as a live task; a genuinely unbalanced/unclosed real `<task>` (outside any code span) still raises. `create_issues`'s own two preflight failure paths, and the `resolve_phase_epic`/`_resolve_task_ordinal_map`/`render_wave_status_block` reads that previously let an uncaught `PlanParseError` crash the process, now degrade to a one-line `.planning/STATE.md` `### Blockers/Concerns` note instead of failing silently or crashing. ([GH#17](https://github.com/davdittrich/gsd-beads/issues/17))

## 0.7.3

### Fixed
- **A `tracker-id`-bound task's stripped block had no literal `<action>` element, so gsd-core's structural plan validator (`verify.plan-structure`) rejected every synced task as incomplete even though its content was fully resolvable through `bd`.** `strip_task_bodies` now wraps the bd pointer in a literal `<action>...</action>` element instead of an HTML comment. Idempotency comes from checking the pointer marker on the block before any stripping runs and skipping an already-stripped block entirely (the same way checkpoint/no-type blocks already are), not from a strip-then-reinsert cycle happening to reach a fixed point — the earlier post-strip check was tautological and could drift on non-blank-line-terminated task blocks. ([GH#14](https://github.com/davdittrich/gsd-beads/issues/14))
- **`TestShipPreGenericDispatch`'s live `check predicate` tests used a bare system-`/tmp` directory as `--phase-dir`, which gsd-tools.cjs's path sandbox (`--phase-dir` must resolve inside a `--project-dir` that itself has `.planning/`) correctly rejects as escaping its allowed directory.** Each temp dir now gets its own `.planning/` marker, making it a fully isolated project root in its own right, with `--project-dir` passed explicitly.

## 0.7.2

### Fixed
- **`close_wave`/`reconcile_stale_closed` auto-closed every task in a `status: halted` plan, including tasks the halt deliberately left open.** `find_completed_task_ids` decided plan completion from `SUMMARY.md` existence alone, never reading its `status` frontmatter. It now mirrors gsd-core's `plan-dependency-graph.cjs` contract: `status: halted` skips the whole plan's tasks (the `SUMMARY` template has no per-task completion field to disambiguate which ones are actually done), and `status: blocked` (#3345, a failure record) is treated as no completion record at all, same as no `SUMMARY.md` existing. A `resolves_issues:` marker from a halted or blocked plan is no longer trusted to close a standalone issue either. Quoted status values (`status: "halted"`) are unquoted before comparison. ([GH#10](https://github.com/davdittrich/gsd-beads/issues/10))
- **`hooks/lifecycle-dispatch.sh` re-fired lifecycle dispatch from a Bash call that only quoted the trigger command in prose.** Its `COMMAND_POSITION` regex included backtick and bare newline as valid command-start positions, both of which occur inside quoted markdown code spans or a JSON-decoded multi-line `--body`/`--description` argument without the shell ever parsing a real command boundary there. Both are now dropped from the character class. ([GH#10](https://github.com/davdittrich/gsd-beads/issues/10))

## 0.7.1

### Fixed
- **`beads-recall`'s description-substring fallback spawned one `bd` subprocess per (open issue, phase-mention token) pair, so `plan:pre` timed out and silently left a stale `BEADS-RECALL.md`.** Measured at 1813 subprocess calls (~9 minutes) on a real repo, past `run_bd`'s aggregate timeout budget even though each call individually was fast. `desc_contains_match` now matches in-process, case-insensitively, against each issue's description already returned by `beads_recall`'s single upfront `bd list` call -- zero subprocesses, independent of issue or token count. A bare version number (e.g. a CmdStan version like `2.39`) is no longer extracted as a phase-mention token, removing a source of spurious description matches. A failed or timed-out recall (including `bd` being unavailable) now overwrites `BEADS-RECALL.md` with an explicit `recall_status: failed` marker instead of leaving a stale prior-run file in place looking fresh; `fragments/recall-pointer.md` now tells the planner to check that key before trusting the file. ([GH#11](https://github.com/davdittrich/gsd-beads/issues/11))

## 0.7.0

### Added
- **Runtime-owned native capability projection.** Each Claude or Codex SessionStart now projects
  only that runtime's selected Beads skills through gsd-core's native writer, records the installed
  generation and selected-surface fingerprint, publishes the shared receipt atomically, and
  serializes concurrent publishers with an inherited kernel lock. ([GH#9](https://github.com/davdittrich/gsd-beads/issues/9))

## 0.6.2

### Fixed
- **`<beads-id>` placeholder (e.g. `TBD`) read as a bound identity, syncing zero issues.** `resolve_issue` treated any non-empty `<beads-id>` as already-bound, so a plan authored with a placeholder (rather than an absent element) diverged every task against `bd` and created nothing, while still exiting 0. A new `BEADS_ID_SHAPE_RE` distinguishes a value that could never have come from `bd create` (unbound -- create normally, replacing the placeholder element in place) from one that matches bd's id shape but doesn't resolve (stale -- unchanged D-07 divergence behavior, never replaced). An all-diverged sync now also prints an explicit `beads-sync: 0 of <n> task(s) bound` summary line instead of only per-task divergence noise. `skills/beads-sync/SKILL.md` now states the contract: an unbound task omits `<beads-id>` entirely. ([GH#7](https://github.com/davdittrich/gsd-beads/issues/7))

## 0.6.1

- Make installed-runtime integration checks portable to clean CI runners while
  retaining a self-contained native-dispatch fixture.

## 0.6.0

### Changed
- **Published the installed native task-content cutover.** The Beads resolver is now the
  installed content authority in Claude and Codex, while the retired `execute-plan.md` Patch 2
  remains absent and the independent `ship.md` Patch 1 contract remains intact.
- **Documented native marketplace installation for both supported runtimes.** The README now
  gives separate Claude and Codex install and uninstall commands for the same plugin source.

## 0.5.0

### Added
- **Tracked `taskContentResolver` source contract.** The Beads capability declares the native resolver bootstrap for exact five-field, fail-closed task-content resolution.

### Changed
- **Installed native task-content cutover is complete and Patch 2 is retired.** The tracked, project-active, global-active, and bootstrap capability trees are byte-identical; the native resolver is the executed content authority. The local `execute-plan.md` marker block, detector, tests, and active documentation were removed together while the independent `ship.md` Patch 1 contract remains intact.

Versions in this file track `capability.json`.

## 0.4.0

### Added
- **`check_native_step_dispatch(point, workflow_path_override=None)` — a region-scoped probe that
  detects when gsd-core starts natively dispatching `kind == "step"` hooks, so this capability's
  own hook can stand down instead of double-dispatching.** Two module constants back it:
  `NATIVE_STEP_DISPATCH_WORKFLOW_FILES` (the lifecycle-point-to-installed-workflow-filename map)
  and `NATIVE_STEP_DISPATCH_REGION_LINES` (the 120-line region bound the probe scopes its search
  to, anchored on the point's own `render-hooks <point> --raw` call). `lifecycle_dispatch` now
  gates its `plan:post` and `verify:post` branches on this probe, standing down rather than
  double-dispatching alongside gsd-core's own native loop once the upstream change ships.
  `execute:wave:pre` and `execute:wave:post` are deliberately NOT gated — no upstream work covers
  either point — and `plan:pre` is likewise ungated. The probe is region-scoped rather than a
  whole-file scan because a whole-file `kind == "step"` grep is a verified false positive on both
  shipped 1.11.0 workflow files, and a false native-dispatch verdict would make the hook stand
  down and silently miss the sync — the one failure direction the design forbids. Every miss
  reports not-detected and degrades to the working double dispatch instead. Detects
  [open-gsd/gsd-core#3687](https://github.com/open-gsd/gsd-core/pull/3687), merged to `next` on
  2026-08-19 and unreleased at the time of writing (TRUTH-03).
- **`resolves_issues:` frontmatter key lets `reconcile-stale-closed` close a standalone
  problem-report bd issue that carries no `<beads-id>` anywhere.** A completed plan's `SUMMARY.md`
  frontmatter may now declare `resolves_issues: ["id"]` (inline flow) or the block-list form
  (`resolves_issues:` / `  - "id"`); `_resolve_marked_issue_ids` unions every marked id across the
  phase into a second candidate set, issued through its own separately-reasoned `bd close` call
  (`--reason "resolves_issues marker: <phase>"`, distinct from the existing `--reason
  "phase-wide reconciliation: <phase>"`) so the two closure paths stay distinguishable in bd's
  audit trail — the only forensic handle on a wrong close, since `.beads/` is untracked. Each raw
  id is validated against `SAFE_BD_ID_RE` (leading alphanumeric, then `[A-Za-z0-9._-]*`) before it
  can reach a `bd close` argv, and the marker search is restricted to the SUMMARY.md frontmatter
  fence only — never the body — so a bd id merely *mentioned* in prose (e.g. as a newly filed
  follow-up, the exact shape `18-02-SUMMARY.md` has for bd `gsd-beads-72u`) can never be closed.
  Closes bd `gsd-beads-72u`.

### Fixed
- **A decimal-numbered phase (`1.5`, `01.5`, `10.1`, `11.1` — the form `/gsd-phase --insert`
  produces) failed silently at every beads lifecycle point.** `PLAN_FILE_RE` never matched a
  `NN.N-NN-PLAN.md` filename, `get_phase_header`/`extract_phase_mentions` raised `ValueError` from
  `int("01.5")`, and `_resolve_default_phase_dir`'s bare `.zfill(2)` was a no-op on an
  already-3-character unpadded token (`"1.5"`), so it never matched an `01.5-` directory. Fixed
  with two string-only helpers, `phase_regex_token` and `phase_dir_prefix` — no `int()`/`float()`/
  `Decimal()` conversion of a phase number survives on the fixed path (TRUTH-04).

### Changed
- **`beads.sync_mode` is resolved: the declared `values` array narrows to `authoritative` and
  `mirror` — the `off` value is retired (it duplicated `beads.enabled: false`, already implemented
  and already the documented opt-out).** `mirror` now does something for the first time: an
  explicit `sync.py create-issues <plan>` withholds the `<task>`-body strip that `authoritative`
  performs, exposing the `allow_strip` parameter that has existed since 0.3.1 under the name
  already declared for it. Neither value ever governs the hook-driven `plan:post` dispatch, which
  never strips regardless of config (D-03) — see 0.3.1's Fixed entry below.
- **On-upgrade behavior change for a project that already wrote `"sync_mode": "mirror"` into
  `.planning/config.json` before this release.** That value was previously inert (read by no
  code); it is now honored. The next explicit `sync.py create-issues <plan>` in that project stops
  stripping task bodies — the behavior someone who wrote that value was asking for, but a live
  behavior change on upgrade, not a no-op.
- **A project whose stored `sync_mode` falls outside the declared list (the retired `off` value,
  or any other value) now gets exactly one notice.** `check_sync_mode_value` prints it on stdout
  at the next `plan:pre` dispatch, naming the stored value, stating that the shipped
  `authoritative` default applies — so task bodies may still be stripped once the read-path patch
  gate passes — and giving the one-command remedy (`gsd-tools config-set beads.sync_mode
  authoritative`, or `mirror`). Never an error; never writes to the project's config.
- **Resolves the 0.3.1 Known-issue below**: `beads.sync_mode` is no longer declared-but-dead.
- **All four previously-unmarked `PATCH_CHECKS` problem-report templates now carry the same
  leading `⚠ ` marker the `missing_msg` templates already used** — `not_found_msg` and
  `could_not_read_msg`, for both the `ship-md` and `execute-plan` targets. Both consuming skills
  (`beads-recall`, `beads-status`) now key their surfacing rule off `check-patch`'s exit code (0
  present, non-zero absent) or the absence of `present` in its output, so a future template that
  forgets the marker is a cosmetic miss rather than a silent one.
- **`GSD-CORE-PATCH.md` now names `verify-reapply-patches.cjs` and the `check-patch` verb as the
  two-part path for confirming a machine-local patch reapply**, and records that the two runtime
  homes (`$HOME/.claude`, `$HOME/.codex`) are separately templated, so neither a patched file nor
  a backup may be copied across them.

### Breaking
- **The two prior single-target patch-check CLI verbs are retired, replaced by one verb:
  `check-patch <ship-md|execute-plan> [--path]`.** D-08: a hard break, no alias window --
  every caller (`beads-recall/SKILL.md`, `beads-status/SKILL.md`, `GSD-CORE-PATCH.md`) was
  updated in this same release. **This is a subprocess/CLI interface change only** -- the
  Python helper functions `check_shipmd_patch` and `check_execute_plan_patch` are retained
  under their existing names as thin wrappers over the new `check_patch(target, path)`
  reader, and both in-file call sites (`lifecycle_dispatch`'s `plan:pre` pair,
  `create_issues`'s `strip_task_bodies` re-gate) are unaffected (TRUTH-02).

## 0.3.1

### Fixed
- **Data loss: a command that merely *mentioned* the trigger string ran a full `plan:post` sync.**
  0.3.0's hook matched `render-hooks <point>` anywhere in a Bash command. `rg "render-hooks
  plan:post --raw" .`, an unquoted `grep`, and an `echo` of the line all fired it — routine
  commands while working on this capability. One such fire created bd issues **and ran
  `strip_task_bodies`, deleting `<behavior>`/`<action>`/`<acceptance_criteria>` from every
  unsynced task in the current phase's `PLAN.md`**. With `.beads/` gitignored that is
  unrecoverable. Two independent fixes, either of which would have prevented it:
  - The matcher now requires a real invocation — a recognised tools shim (`gsd_run`,
    `gsd-tools`, `node …/gsd-tools.cjs`) **in shell command position**, the `loop` subcommand,
    and the trailing `--raw`. A quoted or grepped mention can no longer reach command position.
  - `lifecycle_dispatch` passes `allow_strip=False`, so a hook-driven `plan:post` never performs
    the authoritative strip at all. Creating a bd issue by mistake is recoverable; deleting the
    only copy of task prose is not. An explicit `sync.py create-issues <plan>` still strips.

### Performance
- **The hook no longer starts a Python interpreter on every Bash tool call.** It is wired
  `matcher: "Bash"`, so it runs after every Bash call in every session in every repo with the
  plugin loaded. A locale-pinned bash-builtin pre-filter now rejects the common case before any
  spawn: **13.00 ms → 0.91 ms** per non-matching call. `LC_ALL=C` matters because PostToolUse
  payloads carry the tool's full output — on a 4 MB payload, UTF-8 pattern matching alone cost
  ~34 ms. Also merged two JSON parses into one.

### Changed
- `read_epic_per` and `read_beads_enabled` now share one `read_beads_config` reader; each
  shipped default is written down once, beside the key it belongs to.
- Dropped the `--phase-dir` flag and `phase_dir_override` parameter from `lifecycle-dispatch` —
  nothing but a test ever used them.
- **The hook's own timeout is set explicitly to 120 s** — a deliberate reduction from Claude
  Code's 600 s default hook timeout, bounding the hook's own worst-case blocking time.

### Known issues (pre-existing, now tracked)
- **`beads.sync_mode` is declared in `capability.json` and read by no code.** `mirror` and `off`
  do nothing; only `beads.enabled: false` stops dispatch. 0.3.0's changelog implied the strip was
  gated on it — it never was. Tracked as `gsd-beads-v43`. **Resolved in 0.4.0** — see 0.4.0's
  `### Changed` section: the declaration narrows to `authoritative`/`mirror` and `mirror` now does
  something.

## 0.3.0

### Fixed
- **Four of the six declared lifecycle hooks never dispatched, silently**
  ([#2](https://github.com/davdittrich/gsd-beads/issues/2)). `capability.json` declares six
  `kind: "step"` hooks; gsd-core 1.10.0 reaches only `ship:pre`, and only because this capability
  patches a dispatch loop into `ship.md`. At `plan:post` and `execute:wave:post` gsd-core
  dispatches `kind == "gate"` entries only, at `execute:wave:pre` it checks solely for a
  *contribution*, and at `verify:post` its step loop is hardcoded to
  `ref.skill == "secure-phase"`. `plan:pre`'s generic step contract exists but sits behind an
  auto-chain + frontend-detection branch a manual `/gsd:plan-phase` never enters. Every hook is
  `onError: skip`, so a phase could plan and execute end-to-end with **zero bd issues created**
  and nothing anywhere reporting it: no `PLAN.md` carrying `beads_epic`, no task carrying
  `<beads-id>`, no `BEADS.md` or `BEADS-RECALL.md` written, `bd list` returning
  `No issues found.` throughout.
- **The patch-loss detector shared the failure mode of the thing it protects.**
  `beads-recall`'s Step 3.5 was placed at `plan:pre` on the grounds that `plan:pre` was natively
  dispatched — it was not, for a manual invocation. It now runs from the same hook as the rest.

### Added
- **`hooks/lifecycle-dispatch.sh`** — a `PostToolUse` hook that matches the
  `gsd_run loop render-hooks <point> --raw` call gsd-core still makes at each dead point and runs
  the operation itself, returning output through `hookSpecificOutput.additionalContext`. The
  trigger is a call gsd-core must keep making for its own hook system to function, so unlike a
  patched workflow file it cannot be silently dropped by a gsd-core update.
- **`sync.py lifecycle-dispatch <point>`** — the verb the hook drives, also usable by hand on a
  runtime without `PostToolUse`. Always exits `0`, honoring the `onError: skip` contract every
  hook declares, and re-reads `beads.enabled` itself since entering from a harness hook bypasses
  the capability registry that evaluates each step's `when` condition.
- CI now runs the `sync.py` test suite. It had 134 cases and none of them ran there.

### Known limits
- `PostToolUse` is a Claude Code hook. On another runtime the five points stay undispatched and
  only `ship:pre` runs; drive the rest with `sync.py lifecycle-dispatch <point>`.
- The `execute:wave:pre` `<beads_status>` block is phase-wide rather than wave-scoped, because
  the render-hooks call carries no wave plan-id list. A superset of the wave's issues, so no
  ticket pointer is lost. For the same reason `execute:wave:post` uses the phase-wide idempotent
  `reconcile-stale-closed` backstop rather than `close-wave`.
- A project that planned phases before 0.3.0 has no issues for them. Backfill with
  `sync.py create-issues <plan>` per plan — note this strips `<task>` bodies out of `PLAN.md`
  once the `execute-plan.md` read-path patch is present, so confirm the content landed in `bd`
  before committing, particularly if `.beads/` is gitignored. (At 0.3.0 the strip was gated only
  on that patch check, not on `beads.sync_mode` — `sync_mode` began governing this CLI path's
  strip decision as of 0.4.0; see 0.4.0's `### Changed` section.) Hook-driven dispatch never
  strips.

## 0.2.0

### Changed
- **`beads.enabled` now defaults to `true`**: a fresh install runs with issue tracking on out of
  the box. Opting out is now the explicit action — set `beads.enabled: false` in a project's
  `.planning/config.json`. The four beads skills' Step 1 config gates were inverted to match, so
  an absent key resolves to the shipped default rather than stopping at the gate.

### No regression for existing installs
- A project that already sets `beads.enabled` explicitly in `.planning/config.json` keeps its
  current behavior unchanged — an explicit value always wins over the shipped default. Only
  installs that never set the key pick up the new default.
