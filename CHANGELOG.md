# Changelog

Versions in this file track `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`.

## 0.4.0

### Fixed
- **A decimal-numbered phase (`1.5`, `01.5`, `10.1`, `11.1` — the form `/gsd-phase --insert`
  produces) failed silently at every beads lifecycle point.** `PLAN_FILE_RE` never matched a
  `NN.N-NN-PLAN.md` filename, `get_phase_header`/`extract_phase_mentions` raised `ValueError` from
  `int("01.5")`, and `_resolve_default_phase_dir`'s bare `.zfill(2)` was a no-op on an
  already-3-character unpadded token (`"1.5"`), so it never matched an `01.5-` directory. Fixed
  with two string-only helpers, `phase_regex_token` and `phase_dir_prefix` — no `int()`/`float()`/
  `Decimal()` conversion of a phase number survives on the fixed path (TRUTH-04).

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
  ~34 ms. Also merged two JSON parses into one, and set an explicit 120 s hook timeout.

### Changed
- `read_epic_per` and `read_beads_enabled` now share one `read_beads_config` reader; each
  shipped default is written down once, beside the key it belongs to.
- Dropped the `--phase-dir` flag and `phase_dir_override` parameter from `lifecycle-dispatch` —
  nothing but a test ever used them.

### Known issues (pre-existing, now tracked)
- **`beads.sync_mode` is declared in `capability.json` and read by no code.** `mirror` and `off`
  do nothing; only `beads.enabled: false` stops dispatch. 0.3.0's changelog implied the strip was
  gated on it — it never was. Tracked as `gsd-beads-v43`.

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
  before committing, particularly if `.beads/` is gitignored. (The strip is gated on that patch
  check, not on `beads.sync_mode` — see 0.3.1's Known issues.) Hook-driven dispatch never strips.

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
