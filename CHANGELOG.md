# Changelog

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

Versions in this file track `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`.

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
