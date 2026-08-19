# Pitfalls Research — Milestone v1.3 (Phase 17: Config/Code Truth)

**Researched:** 2026-08-19 (system time verified: `2026-08-19T21:36:59Z`)
**Environment observed:** gsd-core `1.11.0` (latest available), Claude Code `2.1.235`,
plugin `beads-lifecycle` 1.3.1 / capability `beads` 0.3.1, test baseline `Ran 164 tests … OK`.
**Method:** every claim below is either a command + its output, or is labelled `UNVERIFIED`.

---

## Critical Pitfalls

### C1. Removing `sync_mode` from `capability.json` is 100% silent for existing users — the only place it surfaces is a *misleading* error on the write path

**Confidence: 95** (directly demonstrated).

I simulated the removal against the *registered* global capability
(`~/.gsd/capabilities/beads/capability.json`), restored afterward:

```
=== installed global capability BEFORE ===
0.3.1 ['beads.enabled', 'beads.sync_mode', 'beads.ship_gate', 'beads.epic_per']
dropped -> ['beads.enabled', 'beads.ship_gate', 'beads.epic_per']

--- A) config-get of the now-undeclared key (existing user keeps their value) ---
"mirror" exit=0
--- B) all stderr on that call ---
(end stderr)                       # ← nothing. Zero warnings.
--- C) config-set the removed key ---
Error: Unknown config key: "beads.sync_mode". Valid keys: agent_skills_security.trusted…
 exit=0
```

Three separate observed facts:

1. **Read path is silent forever.** `gsd_run config-get beads.sync_mode` returns `"mirror"`,
   exit 0, no stderr — with the key gone from the schema. The stale value sits in
   `.planning/config.json` indefinitely.
2. **gsd-core's unknown-key warning is TOP-LEVEL-ONLY and cannot help.** From
   `~/.claude/gsd-core/bin/config-loader.cjs:727` the check is
   `Object.keys(parsed).filter(k => !KNOWN_TOP_LEVEL.has(k))` — it never descends into a
   namespace. Demonstrated: with `{"beads":{"sync_mode":"banana","ghost_key":42},"zzzfakecap":{}}`,
   the warning names only `zzzfakecap`; `beads.sync_mode: "banana"` and a wholly invented
   `beads.ghost_key` produce nothing. `config-get beads.ghost_key` returns `42`, exit 0.
3. **`validate health` has no capability-config rule at all.** `health-diagnostic-rules/config-validation.cjs`
   covers W003/W004/W008/W016/W012-W015/E005 — `model_profile`, `workflow.*`,
   `branching_strategy`, `models`. Nothing reads capability schemas. A full scratch project
   with `sync_mode: "banana"` reports `"warnings"` containing only PROJECT.md-section and
   phase-naming items.

The *only* surface is `config-set`, and its message misleads: the "Valid keys" dump is ~2000
characters of gsd-core's own keys and **contains no `beads.*` entry whatsoever**. A user reads that
as "beads config does not exist", not "this one key retired".

**Contrast — narrowing behaves much better.** Keeping the key and shrinking `values` yields
`Error: Invalid beads.sync_mode 'banana'. Valid values: authoritative, mirror, off` (exit 1) on the
write path — but a **hand-edited** config still bypasses it entirely (fact 1 applies unchanged).

**Prevention — belongs to the TRUTH-01 decision task (Phase 17, the Alternatives Considered
task), and its migration sub-task:**

- Whichever of (a)/(b)/(c) wins, **`config-set` validation is not a migration path** — it fires
  only when a user re-writes the key, which by definition they will not do. The migration answer
  must be a channel the user hits without acting.
- The cheapest channel that actually fires is `sync.py` itself, which already reads config on
  every dispatch via `read_beads_config` (`sync.py:641`). One `read_beads_config(root,
  "sync_mode", "")`-style probe printing a one-line deprecation notice when the value is
  non-empty and non-`authoritative` costs ~6 lines and reaches the user through the existing
  `hookSpecificOutput.additionalContext` channel. **Success Criterion 3 ("demonstrated by an
  actual run against such a config") is not satisfiable without something like this** — with
  option (c) as currently framed, an actual run produces *no observable output at all*, which is
  indistinguishable from the notice being broken.
- Prefer **(a) narrow** over **(c) drop** on this evidence alone: (a) keeps `config-set`
  validation as a live guard and keeps the key discoverable; (c) converts every existing
  `.planning/config.json` in the wild into permanently-unwarned dead weight.

### C2. The stale `gsd-local-patches/` backup is a live landmine that will fight this milestone's own v2 trim

**Confidence: 92** (verifier run; the reinstatement outcome is inference from the verifier's
documented gate role).

gsd-core 1.11.0 ships a patch-preservation system that **gsd-beads references nowhere**:

```
$ grep -rn "reapply-patches\|gsd-local-patches\|gsd-pristine" /home/dd/projects/gsd-beads …
(end)                                   # ← zero hits across all .md/.json/.py/.sh
```

Yet it is already active on this machine, holding *this capability's* patches:

```
$ cat ~/.claude/gsd-local-patches/backup-meta.json
{ "backed_up_at": "2026-08-19T21:20:36.288Z",
  "from_version": "1.10.0",
  "files": ["gsd-core/workflows/execute-plan.md", "gsd-core/workflows/ship.md"], … }
```

The backup is **stale relative to today's work**:

```
-- backup ship.md:  gsd-beads-patch:ship-pre-generic-dispatch v1
-- live   ship.md:  gsd-beads-patch:ship-pre-generic-dispatch v2
```

Commit `966315a` trimmed the ship.md patch to v2 (dropping the generic GATE loop now native in
1.11.0 — live `ship.md:107`). The backup still carries v1, **including that gate loop**
(backup `ship.md:219`: `If activeHooks has no qualifying kind == "gate" entry…`).

gsd-core's deterministic gate already fails against the current tree:

```
$ node ~/.claude/gsd-core/bin/verify-reapply-patches.cjs \
    --patches-dir ~/.claude/gsd-local-patches --config-dir ~/.claude
# Hunk Verification Gate (#2969)
Checked: 2 file(s)
Failures: 2
- gsd-core/workflows/execute-plan.md   reason: fail_user_lines_missing  (…60+ lines…)
- gsd-core/workflows/ship.md           reason: fail_user_lines_missing
EXIT=1
```

No `~/.claude/gsd-pristine/` exists, so the verifier is in its documented over-broad fallback
("treating every significant backup line as required"). Most of the 60+ "missing" lines are
1.10.0 upstream text that legitimately changed in 1.11.0 — **false positives that bury the two
real signals**. On the next `/gsd-update --reapply`, Step 5's gate either halts the update or
demands a human triage of 60+ noisy hunks, and the v1 gate loop is a live candidate for
reinstatement alongside 1.11.0's native one — undoing `966315a` silently.

**Prevention — add a task to Phase 17 (not currently in the roadmap's five criteria):**

- Refresh `~/.claude/gsd-local-patches/` after the patch work lands (re-run the backup, or delete
  the stale one so the next update re-snapshots from the correct v2 baseline). One line in
  `GSD-CORE-PATCH.md`'s reapply procedure naming `gsd-local-patches/` closes the doc gap
  permanently and costs nothing.
- `GSD-CORE-PATCH.md` should state that gsd-core has a first-class reapply path and that this
  capability's markers are what makes it auditable. Right now the doc reads as if manual
  reapplication is the only mechanism.

### C3. This repo dogfoods a **stale copy** of `sync.py` whenever `capability.json`'s version is not bumped — and CI cannot see it

**Confidence: 96** (directly demonstrated, reverted cleanly).

`hooks/lifecycle-dispatch.sh:102-105` resolves the script **project-scope first**:

```
"$PROJECT_DIR/.gsd/capabilities/beads/scripts/sync.py"        ← preferred
"${GSD_HOME:-$HOME}/.gsd/capabilities/beads/scripts/sync.py"
"${CLAUDE_PLUGIN_ROOT:-…}/.gsd/capabilities/beads/scripts/sync.py"
```

`.gsd/` is gitignored (`.gitignore:39-41`) and is a copy of
`plugins/beads-lifecycle/.gsd/capabilities/beads/`. CI runs the tests in the **plugin** tree only
(`ci.yml`, `working-directory: plugins/beads-lifecycle/.gsd/capabilities/beads`).

I appended a marker line to the plugin-tree `sync.py` **without bumping any version** and ran
the update path:

```
== marking the SOURCE tree (no version bump) ==
fed9ab66…  plugins/beads-lifecycle/.gsd/…/sync.py     ← changed
77f0b40f…  .gsd/…/sync.py                              ← unchanged

$ gsd_run capability update beads
{ "status": "upgraded", "id": "beads", "fromVersion": "0.3.1", "toVersion": "0.3.1", …

== after ==
fed9ab66…  plugins/…/sync.py
77f0b40f…  .gsd/…/sync.py
DST does NOT have the marker -> project copy is STALE
```

**`capability update` reported `"status": "upgraded"` and copied nothing.** `0.3.1 → 0.3.1` is a
no-op the tool reports as success. `.gsd-capabilities.json` pins `"version": "0.3.1"` with
`"integrity": ""`, so there is no content hash to fall back on.

This is exactly the "tests pass, reality broken" shape that produced the v1.3.0 incident: during
Phase 17 the developer edits `sync.py`, CI goes green on the plugin tree, and every `plan:pre`
hook firing **in this very repo** keeps executing the pre-change code — including the old
two-clone patch checkers TRUTH-02 is collapsing.

**Prevention — a precondition on every Phase 17 task that edits `sync.py`:**

- Bump `capability.json` `version` **in the first commit that touches `sync.py`**, not at ship
  time. `0.3.1 → 0.4.0` immediately, then re-run `gsd_run capability update beads`.
- Add a mechanical check to the verify task: `diff -q .gsd/capabilities/beads/scripts/sync.py
  plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` must be silent before any
  behavioral claim about hook dispatch is accepted. (Both trees are identical *today* —
  `diff -rq` → `IDENTICAL` — so this is a guard, not a repair.)

---

## Moderate Pitfalls

### M1. `PostToolUse` no longer fires on failed tool calls — `PostToolUseFailure` split off

**Confidence: 78** (live docs at https://code.claude.com/docs/en/hooks, fetched 2026-08-19; the
per-event schema section was truncated in the fetch, so the `PostToolUse`-specific
`hookSpecificOutput` contract is `UNVERIFIED` from that page).

The current event table reads `PostToolUse | After tool call succeeds`, with a sibling
`PostToolUseFailure | After tool call fails`. Consequence for gh-2: if
`gsd_run loop render-hooks plan:pre --raw` exits non-zero, the dispatch hook does not fire and
`check_shipmd_patch` / `check_execute_plan_patch` never run. That is arguably correct
(fail-open), but it is a *new* narrowing of the trigger the whole gh-2 design rests on, and it is
undocumented in this repo.

Everything else the fix depends on is confirmed current:

- `matcher` is still the field name; `"Bash"` is pure `[A-Za-z]` so it takes the **exact-string**
  branch, not the new unanchored-regex branch. Safe as written.
- `hookSpecificOutput.additionalContext` is still live and model-visible; **no deprecation notice
  found**.
- The **10,000-character cap is confirmed** ("Hook output strings, including `additionalContext`
  … capped at 10,000 characters. Output that exceeds this limit is saved to a file and replaced
  with a preview and file path"). `lifecycle-dispatch.sh`'s `LIMIT = 9000` and its comment are
  accurate. No change needed.

**Prevention:** one sentence in `hooks/lifecycle-dispatch.sh`'s header noting the success-only
firing. No code change. Attach to the TRUTH-02 task's doc pass (it already touches this area) or
skip — this is documentation debt, not a defect.

### M2. `timeout: 120` is a *reduction* from the default, and the changelog implies the opposite

**Confidence: 88** for the semantics; **60** for the truncated-write consequence (`UNVERIFIED`).

Live docs: `timeout` is **seconds**; command-hook default is **600**, and `PostToolUse` is not in
the list of events that lower it. `hooks.json` sets `120`.

CHANGELOG 0.3.1 lists this under **Performance**: "set an explicit 120 s hook timeout." That
reads as *added protection*. It is the opposite — it removes 480 s of headroom that was already
there by default. Nothing is broken today, but the changelog line is exactly the kind of
"documentation claiming an effect the code does not have" that TRUTH-01's doc sweep exists to
purge, and it sits two lines from the entries the sweep is already correcting.

The consequence worth flagging: on expiry, "Claude Code discards the hook's output, and the hook
renders no decision" — the process is cancelled. `create_issues` writes PLAN.md with a plain
non-atomic `plan_path.write_text(new_text, encoding="utf-8")` (`sync.py:1388`). A cancellation
landing inside that call truncates PLAN.md. Reaching 120 s requires ~8 consecutive `BD_TIMEOUT`
(15 s) stalls, so this is remote — but the blast radius is *the same file the v1.3.0 incident
destroyed*, and `allow_strip=False` does not protect against it (that flag prevents *stripping*,
not the write).

**Prevention — two independent, both cheap:**

- Correct the CHANGELOG line during the TRUTH-01 doc sweep task: state it as a deliberate
  tightening from the 600 s default, with the reason.
- If the plan touches `create_issues` at all: write to `plan_path.with_suffix('.tmp')` then
  `os.replace()`. Two lines, makes truncation structurally impossible. **Do not add this as a
  standalone task** — it is out of TRUTH-01/TRUTH-02 scope; file it as a bd ticket unless the
  merge task already opens that function.

### M3. Merging the two checkers: the tests constrain **five exact strings**, not the structure

**Confidence: 97** (read directly from `tests/test_sync.py`).

Criterion 5 requires `TestCheckShipmdPatch` / `TestCheckExecutePlanPatch` **unedited**. Read
literally, the merge must preserve these assertions (`tests/test_sync.py:2937-3072`):

| Case | Assertion | What it pins |
|------|-----------|--------------|
| marker found (both) | `assertIn("present", …)`, exit `0` | substring `present` in the success line |
| marker absent — ship | `assertIn("GSD-CORE-PATCH.md", …)` **and** `assertIn("ship_override", …)`, exit `1` | ship's message must name `ship_override` |
| marker absent — exec | `assertIn("GSD-CORE-PATCH.md", …)` **and** `assertIn("gsd-executor", …)`, exit `1` | exec's message must name `gsd-executor` |
| file absent (both) | `assertIn(str(missing_path), …)`, exit `1` | the probed path is interpolated |
| non-UTF-8 (both) | `assertIn("could not be read", …)`, exit `1` | shared substring |
| exec only | `test_never_writes_to_target_file` | read-only discipline |
| exec only | `sync.main(["check-execute-plan-patch", "--execute-plan-path", …])` → exit `0` | **CLI flag name is pinned by test** |

**The real hazards, in order:**

1. **`--ship-md-path` has no CLI test; `--execute-plan-path` does.** Only
   `test_cli_routes_through_main_and_returns_function_exit_code` exercises a flag, and only the
   execute-plan one. A table-driven merge that unifies the CLI into a single
   `check-patch <target>` verb would keep 164/164 green **while silently breaking
   `--ship-md-path`** — which `beads-status/SKILL.md` Step 2d depends on. **Keep both
   subcommands and both flag spellings.** If the merge unifies the CLI, that is an interface
   break on a published plugin and needs its own changelog entry plus a preserved alias.
2. **Four divergent message strings users may grep.** `ship_override` / `gsd-executor` are
   asserted, so they survive by test. But the *unasserted* halves are the ones that vanish
   quietly under a shared template: ship's `"the ship_override step will not fire. The two
   ship:pre GATES are unaffected: gsd-core >= 1.11.0 dispatches those natively (#3559 / PR
   #3608)"` and its `"(v2)"` version suffix; exec's `"gsd-executor will not read task content
   from bd"` and `"(v1)"`. **The version suffix is the one to watch** — the two markers are at
   *different* versions (ship v2, execute-plan v1), so the table needs a per-entry version field,
   not a shared constant.
3. **No test asserts the marker *version*.** Both suites reference `sync.SHIP_MD_PATCH_MARKER` /
   `sync.EXECUTE_PLAN_PATCH_MARKER` symbolically, so a wrong version string passes 164/164 while
   `check_shipmd_patch` reports "missing" against every real install forever. `966315a` changed
   this constant with no test able to catch a typo. The merge is the moment to add one literal
   assertion per entry.
4. **Both are called back-to-back at `sync.py:737-738`** inside `lifecycle_dispatch`'s
   `try/except Exception` — an exception in a merged reader now takes out `beads_recall` too
   (same `try` block), degrading the whole `plan:pre` to one notice line. Keep the merged reader
   total (it already catches `OSError`/`UnicodeDecodeError`); do not introduce a `KeyError` path
   on an unknown table key.

**Prevention — the TRUTH-02 task:** parameterize on `(filename, marker, version, missing_reason)`
where `missing_reason` is the per-target clause (`"the ship_override step will not fire…"` /
`"gsd-executor will not read task content from bd"`). Keep the two CLI subcommands and their two
flag names as thin wrappers. Add two literal-marker assertions. Do **not** unify the CLI.

### M4. `check_shipmd_patch` at `plan:pre` fires early enough — but only if you plan a phase

**Confidence: 90** (call sites read directly; the "silently stripped" premise is confirmed by the
backup-meta.json above).

The trigger is real and reached three times in a manual run —
`workflows/plan-phase.md:348, 411, 441`, all `gsd_run loop render-hooks plan:pre --raw`, the
first at "Spawn gsd-phase-researcher" (before any planning work). So *within* a `/gsd:plan-phase`
run, detection is early enough to matter.

The gap is **between** plan runs:

- The ship.md patch protects `ship:pre`. Its detector runs at `plan:pre`. A patch lost right
  after planning is undetected through the entire execute→verify→ship cycle — `ship_override`
  silently does not fire, and the ship gate records nothing. Discovery is at the **next phase's
  planning**, i.e. one full phase later. On this repo's cadence that is days.
- The execute-plan.md patch fails *safe*: `create_issues` re-checks it live at `sync.py:1380`
  (`if check_execute_plan_patch() == 0:`) and leaves task content in PLAN.md when absent. Good
  design — preserve it verbatim through the TRUTH-02 merge; it is the last line of defense
  against the v1.3.0 failure mode.
- Neither detector fires at `ship:pre` independently: `beads-status/SKILL.md` Step 2d is
  reachable only *through* the patch it checks (documented in `check_shipmd_patch`'s own
  docstring).

**Prevention — no new task needed, but a verify-task assertion:** confirm after the merge that
`lifecycle_dispatch`'s `plan:pre` arm still calls both checks and that `create_issues`'s live
re-check at `:1380` still routes through the merged reader with unchanged `== 0` semantics.

---

## Release Hygiene — what this milestone's ship step must check that the last one did not

**Confidence: 94** (all observed via `git` / `gh`).

### R1. `main` is *already* ahead of `v1.3.1` with unversioned, unchangelogged shipped code

```
$ git log --oneline v1.3.1..HEAD
966315a fix(beads): trim ship.md patch to v2, correct the upstream citation
…
$ git diff --stat v1.3.1..HEAD -- plugins .claude-plugin README.md
 README.md                                      |   6 +-
 …/beads/GSD-CORE-PATCH.md                      | 137 +++++--------
 …/beads/scripts/sync.py                        |  20 ++-
 …/beads/skills/beads-status/SKILL.md           |  15 ++-

$ grep -n "v2\|1\.11\.0\|3608\|3559" CHANGELOG.md
NONE — the v2 trim is unchangelogged

versions at HEAD:  plugin.json 1.3.1   capability.json 0.3.1   (unchanged from the v1.3.1 tag)
```

`966315a` changed a **behavioral constant** — `SHIP_MD_PATCH_MARKER` v1→v2, which flips
`check_shipmd_patch`'s verdict on every machine still carrying v1 — with no version bump and no
changelog entry. Marketplace install resolves `"source": "./plugins/beads-lifecycle"` from the
repo, so consumers tracking the default branch already have this while `plugin.json` tells them
they have 1.3.1.

**Ship step must check:** `git diff --quiet <last-tag>..HEAD -- plugins .claude-plugin README.md`
→ if non-empty, both `plugin.json` and `capability.json` versions differ from the last tag, and
CHANGELOG has a section for the new capability version. This is mechanical; make it a shell
command in the ship task, not a prose reminder.

### R2. The withdrawn `v1.3.0` tag still resolves — and deleting the GitHub Release did not withdraw the code

```
$ git merge-base --is-ancestor v1.3.0 HEAD && echo "YES ancestor"
YES ancestor
$ gh release list
v1.3.1   Latest   2026-08-19T20:39:47Z
v1.2.0            2026-08-16T21:57:40Z
v1.1.1            2026-08-16T21:07:36Z      # ← no v1.3.0 release
```

The GitHub *Release* is gone; the **tag remains and is reachable**. Anything resolving
`v1.3.0` — a pin, a `git checkout`, a mirror — gets the data-loss build. Meanwhile marketplace
users install from the *branch*, not the release, so deleting the release withdrew nothing that
mattered; the actual remedy was the v1.3.1 branch commit.

**Ship step must check:** either delete the `v1.3.0` tag from `origin` (and say so in
CHANGELOG), or add an explicit CHANGELOG line stating that `v1.3.0` is withdrawn, must not be
used, and why. Silence plus a live tag is the worst of both. Also note `release.yml` fires on
**any** `v*.*.*` tag push — a retag is a re-release, so the tag cannot simply be moved.

### R3. Green CI is necessary and was not sufficient — but this time it is not even necessary yet

The roadmap already carries "No release tag is cut until CI is green on the exact commit being
tagged." Two additions this incident argues for:

- **CI green on the plugin tree does not mean the running code is the tested code** (see C3).
  The ship task should assert the two trees are identical *and* the version was bumped.
- **164 tests, OK is the pre-change baseline** — assert the post-change count is
  `>= 164`, not `== 164`. The TRUTH-02 merge should *add* the two literal-marker assertions from
  M3.3; a task that leaves the count at exactly 164 has added no coverage for the thing it
  changed.

---

## Phase-Task Mapping

| Pitfall | Confidence | Phase 17 task that owns it | Prevention in one line |
|---------|-----------|---------------------------|------------------------|
| C1 silent config removal | 95 | TRUTH-01 decision + migration | Emit a deprecation line from `sync.py`'s existing config read; prefer (a) narrow over (c) drop |
| C2 stale `gsd-local-patches/` | 92 | **new task** (not in the 5 criteria) | Refresh/clear the backup after the v2 trim; name the mechanism in `GSD-CORE-PATCH.md` |
| C3 stale project-scope copy | 96 | precondition on every `sync.py` task | Bump `capability.json` version in the *first* such commit; `diff -q` the two trees in verify |
| M1 PostToolUse success-only | 78 | doc pass (optional) | One header sentence in `lifecycle-dispatch.sh` |
| M2 `timeout: 120` mischaracterized | 88 / 60 | TRUTH-01 doc sweep | Correct the CHANGELOG line; atomic PLAN.md write only if that function is already open |
| M3 merge breaks unasserted strings / CLI | 97 | TRUTH-02 | Per-entry `version` + `missing_reason`; keep both subcommands and both flags; add literal-marker assertions |
| M4 detector cadence | 90 | TRUTH-02 verify | Preserve `create_issues`'s live `check_… == 0` gate verbatim |
| R1 unversioned shipped code on main | 94 | ship task | Mechanical `git diff --quiet <tag>..HEAD -- plugins` + version + CHANGELOG check |
| R2 live withdrawn tag | 94 | ship task | Delete `v1.3.0` from origin or document the withdrawal |
| R3 CI sufficiency | 90 | ship task | Assert tree identity, version bump, and test count `>= 164` |

---

## Sources

- **Observed here** (HIGH): `config-get`/`config-set`/`validate health` runs; `verify-reapply-patches.cjs`; the `capability update beads` no-op test; `git`/`gh` tag and release state; the 164-test baseline.
- **Read directly** (HIGH): `sync.py`, `lifecycle-dispatch.sh`, `hooks.json`, `test_sync.py:2937-3072`, `capability.json`, `CHANGELOG.md`, `.gitignore`, `.github/workflows/*`, `marketplace.json`; gsd-core 1.11.0's `config-loader.cjs`, `health-diagnostic-rules/config-validation.cjs`, `workflows/plan-phase.md`, `workflows/reapply-patches.md`.
- **Live docs** (MEDIUM — page truncated before the per-event `PostToolUse` schema): https://code.claude.com/docs/en/hooks, fetched 2026-08-19. The `PostToolUse` `hookSpecificOutput` field list is UNVERIFIED from that fetch; the 10,000-char cap, `timeout` units/defaults, matcher semantics and the `PostToolUseFailure` split are quoted from visible text.
