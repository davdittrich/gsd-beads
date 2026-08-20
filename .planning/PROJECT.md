# beads capability for gsd-core

## What This Is

A gsd-core capability that makes [beads](https://github.com/gastownhall/beads) (`bd`) the task
substrate for gsd's plan → execute → verify → ship lifecycle: gsd's markdown holds the plan,
`bd` holds task status, and the planner/executor/ship gate all read live `bd` state instead of
`.planning/` prose. Installed as a runtime capability overlay — a directory drop under
`.gsd/capabilities/beads/` — with no fork and no patch to gsd-core itself.

## Core Value

gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero duplicated
task-state bookkeeping survives in `.planning/`.

## Requirements

### Validated

- ✓ **B1**: One beads issue per `PLAN.md` task, parented to a phase epic — Phase 1
- ✓ **B2**: Plan task ordering becomes beads dependencies — Phase 1
- ✓ **B3**: Task completion closes its issue automatically — Phase 1
- ✓ **B4**: Identity is bound explicitly via `beads-id:`, never by title matching — Phase 1
- ✓ **B5**: Sync is idempotent — Phase 1
- ✓ **B6**: `bd` absent, failing or locked degrades to a no-op with one visible notice — Phase 1
- ✓ **B9**: A phase with unfinished blocking issues cannot ship — Phase 3
- ✓ **B10**: Divergence blocks and is reported; never auto-reconciled — Phase 3
- ✓ **B7**: The planner sees open issues before planning (`BEADS-RECALL.md`) — Phase 2
- ✓ **B8**: The executor's prompt carries live issue state — Phase 2
- ✓ **B11**: `BEADS.md` is regenerated every step, never hand-edited — Phase 2
- ✓ **B12**: One-shot migration of `.planning/todos/pending/` into beads — Phase 4
- ✓ **B13**: `beads-status` prints the plan-task ↔ issue mapping on demand — Phase 4
- ✓ **B14**: Milestone-level epic option (`beads.epic_per=milestone`) — Phase 4
- ✓ **PUB-01**: `.claude-plugin/plugin.json` declares identity, points `skills` at
  `.agents/skills/beads/`, passes `claude plugin validate . --strict` (one documented, permanent
  exception: root `CLAUDE.md` warning, see 05-CONTEXT.md D-10) — Phase 5
- ✓ **PUB-02**: `.claude-plugin/marketplace.json` self-hosted entry; local
  `/plugin marketplace add` + `/plugin install beads@gsd-beads` round trip confirmed — Phase 5
- ✓ **PUB-08**: `LICENSE` (MIT) present at repo root, referenced in `plugin.json`'s `license` field
  — Phase 5
- ✓ **PUB-03**: The capability-loader bridge is a documented, verified manual `capability install`
  step — Phase 6
- ✓ **PUB-06**: `hooks/hooks.json` ships the SessionStart `bd prime` hook, `.claude/settings.json`
  retired — Phase 6
- ✓ **PUB-05**: Pre-push git hygiene audit; 4 machine-local files stripped from every commit via
  `git filter-repo`, `.gitignore` extended — Phase 7
- ✓ **PUB-10**: `github.com/davdittrich/gsd-beads` public, remote configured, history pushed —
  Phase 7
- ✓ **PUB-04**: Release archive built from the explicit 5-path allowlist, attached to GitHub
  Release `v1.1.0` — Phase 8
- ✓ **PUB-07**: `README.md` ships purpose, requirements, install, uninstall, caveats, license,
  gsd-core link — every command transcribed from execution; gap-closure round (G-08-1) added the
  beads-vs-built-in-tracking value prop and a gsd-lifecycle-integration example after UAT found
  both missing — Phase 8
- ✓ **PUB-09**: `claude plugin validate . --strict` clean at the released tag from a fresh clone;
  real `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip executed
  against the public repo — Phase 8

- ✓ **PUB-11**: `.agents/skills/beads/SKILL.md` expanded toward upstream `beads` skill parity —
  Phase 9
- ✓ **PUB-12**: A gsd-tailored `.beads/PRIME.md` ships, overriding beads' generic `bd prime`
  default output — Phase 9 (`v1.1.1` released)
- ✓ **MDL-01**: `markdown-linting` capability wraps `rumdl` over `.planning/**/*.md`, reports
  violations at `verify:post` — Phase 13
- ✓ **MDL-02**: `LINT-REPORT.md` regenerated every run, degrades honestly (non-numeric
  `violation_count: unavailable` sentinel) when `rumdl` can't run — Phase 13
- ✓ **MDL-03**: `ship:pre` gate on lint violations, advisory by default — Phase 13
- ✓ **MDL-04**: `rumdl` invoked with an always-explicit `--config` path, never
  `markdownlint-cli2` — Phase 13
- ✓ **PRW-01**: `pr-workflow` capability wraps `gh pr create`/`gh pr checks`/`gh api`, projects
  PR check status into `14-PR.md` at `execute:wave:post` — Phase 14
- ✓ **PRW-02**: `ship:pre` gate on the derived `pr_gate_ok` boolean, advisory by default —
  Phase 14
- ✓ **PRW-03**: `ship:post` warn-only notice when no open PR exists for the branch — Phase 14
- ✓ **PRW-04**: Fails open (one notice, exit 0, sentinel report) across all `gh`-degraded paths
  — Phase 14
- ✓ **Beads issue content parity** (D-01 through D-08, no `REQ-*` IDs — decision-tracked per the
  Phase 15 precedent): every `bd create` for a task/epic carries a real description and
  acceptance criteria instead of a title-only stub; `gsd-executor` reads `auto`/`tracer` task
  instructions from `bd show <beads-id> --json`, hard-halting when bd can't answer; a
  phase-wide `reconcile-stale-closed` backstop closes issues left open by per-wave dispatch —
  Phase 16
- ✓ **TRUTH-04**: Decimal-numbered phases (`01.5`, `10.1`) resolve at `plan:pre`/`plan:post` and
  through `_resolve_default_phase_dir` — `phase_regex_token`/`phase_dir_prefix` replace numeric
  conversion at all four break sites — Phase 17
- ✓ **TRUTH-03**: `lifecycle-dispatch` hook stands down correctly once gsd-core ships native
  `plan:post`/`verify:post` step dispatch (upstream PR #3687) — `check_native_step_dispatch`
  gates on live probing, not version guessing; `allow_strip` stays permanently `False` on the
  hook path — Phase 17
- ✓ **TRUTH-01**: `beads.sync_mode` narrowed to `["authoritative", "mirror"]`, both values now
  behaviorally distinct; a project holding the retired `off` value gets one `plan:pre` notice,
  never a silent no-op or a config write — Phase 17
- ✓ **TRUTH-02**: `check_shipmd_patch`/`check_execute_plan_patch` collapsed into one
  `PATCH_CHECKS`-table reader (`check_patch`) and one CLI verb (`check-patch <target> [--path]`)
  — a deliberate one-way hard break (D-08, user-confirmed live via checkpoint), ROADMAP Criterion
  4 amended to record the supersession — Phase 17

### Active

(v1.4 requirements pending definition — see Step 9 of `/gsd-core:new-milestone`)

### Out of Scope

- Overriding any first-party gsd-core behavior — the overlay is additive only; first-party always
  wins on collision (N1)
- Forking or patching gsd-core — if a core change proves necessary, raise it upstream first (N2)
- A second planning or gating pipeline — this capability tracks work, it does not decide how work
  is planned (N3)
- Executing command strings that originate in a plan, ticket, or other authored artifact — `bd`
  invocations are built from typed values only, never assembled from artifact text, because the
  artifact's author and the workflow's runner are frequently different principals (N4)
- Any dependency beyond the `bd` binary and Python 3 standard library (N5)
- Syncing beads onward to GitHub Issues, Jira, or any other tracker — one tracker only (N6)
- A deterministic plan-checker reviewer capability (PRD Appendix A) — benefit is unmeasured and
  the failure mode is a second review pipeline nobody asked for; revisit only after `beads` has
  shipped and only if the LLM plan-checker is observed spending judgement on decidable properties
- `get-available-resources` capability — originally a target feature for v1.2 (CPU/GPU/memory/disk
  detection, advisory-only `plan:pre`/`execute:wave:pre` fragment); Phase 16 (beads issue content
  parity) was discovered as a higher-priority gap mid-milestone and took its place, so this was
  never planned or built in v1.2. Not invalidated, just deferred — revisit as a future milestone's
  target if the need resurfaces

## Current State

Phase 17 (v1.3's only phase) complete 2026-08-20 — all 4 requirements (TRUTH-01..04) shipped, 4/4
plans, deep code review clean of blockers (5 non-blocking doc/test-truth warnings), phase
verification passed 4/4 against live-executed checks. v1.3 milestone is feature-complete;
`/gsd-complete-milestone v1.3` not yet run.

## Current Milestone: v1.3 Config/Code Truth — Phase 17 complete, ready to close

**Status:** All target features shipped (Phase 17, 2026-08-20). Awaiting `/gsd-complete-milestone
v1.3` to formally archive.

**Goal:** Every config key this capability declares is one the code actually reads, and the
patch-checker duplication the gh-2 post-release review flagged is gone.

**Target features:**
- `beads.sync_mode` stops being a declared-but-dead config surface — either the enum becomes
  real or the declaration and its README description narrow to what the code does
  (`gsd-beads-v43`, P1). Direction is deliberately undecided here: the planner must produce an
  Alternatives Considered table and clear the plan-checker before anything is written.
- `check_shipmd_patch` and `check_execute_plan_patch` collapse into one table-driven reader
  (`gsd-beads-t7a`, P3) — ~39 body lines each, differing only in filename, marker constant and
  four message strings.

**No new features.** Both items are pre-existing divergences surfaced by the four-lens review of
the gh-2 fix, not new capability.

**Why this milestone is explicitly gated:** the gh-2 fix shipped on the quick path (no
plan-check, no verifier) on 2026-08-19 as v1.3.0, and a post-release review found a data-loss
bug in the fix itself — a hook matcher firing on any command that merely *mentioned* its trigger
string, reaching `strip_task_bodies` and deleting `PLAN.md` task prose. That needed a second tag
(v1.3.1) and the v1.3.0 release was withdrawn. Plan-check and verification are both on for this
milestone, and no tag is cut until CI is green on the exact commit being tagged.

**Deferred, still open:** `get-available-resources` (dropped from v1.2, see Out of Scope) remains
a candidate for a later milestone if the need resurfaces.

<details>
<summary>v1.2 New Capability Plugins — SHIPPED 2026-08-19</summary>

**Goal:** Ship three new gsd-core capability plugins — `pr-workflow`, `markdown-linting`,
`get-available-resources` — each dogfooded in this repo then extracted to its own public GitHub
repo and marketplace entry, exactly matching the proven Phase 10/11 (build) → Phase 12 (extract
+ publish) pattern already shipped for `ponytail-everywhere` and `sota-numerics`.

**Target features:**
- `pr-workflow` capability: wraps `gh pr create`/`gh pr checks --watch`/`gh api`; `ship:pre` gate
  (advisory by default) on failing/pending checks, `ship:post` action to open a draft PR
- `markdown-linting` capability: wraps `markdownlint-cli2` over `.planning/**/*.md`; `verify:post`
  report of MD0XX violations, `ship:pre` gate (mirrors `beads.ship_gate`'s pattern)
- `get-available-resources` capability: wraps a CPU/GPU/memory/disk detection script producing
  `.claude_resources.json`; advisory-only fragment at `plan:pre`/`execute:wave:pre`, no gate —
  **dropped**, never planned; Phase 16 (beads issue content parity) took its place, see Out of
  Scope
- Each ships first as a dogfooded `.gsd/capabilities/<id>/` subdirectory in this repo, then gets
  its own public repo (`davdittrich/<id>`) and a `git`-source `marketplace.json` entry alongside
  `beads`, `ponytail-everywhere`, `sota-numerics`

**Milestone v1.1 status:** Publish & Document — Phases 5-9 shipped and verified; Phase 10/11/11.1
(ponytail-everywhere, sota-numerics, beads-default-flip) shipped; Phase 12 (public extraction of
those two plugins) has all 4 plans' work done and pushed per the decision log below, but
ROADMAP.md's checkboxes are stale (a known upstream gsd-core plan-scan misclassification, see
STATE.md) — not formally closed via `/gsd-complete-milestone`. User explicitly chose to proceed to
v1.2 rather than block on that formality (2026-08-18).

**Phase 14 (pr-workflow capability, dogfood) complete (2026-08-18):** PRW-01..04 validated in
this repo (`.gsd/capabilities/pr-workflow/`) — 27/27 unit tests, live four-state gate smoke test,
code review (4 findings fixed post-review), phase verification passed 6/6. Dogfooding surfaced a
gsd-core capability-consent defect (bytecode-cache artifacts silently invalidate consent);
interim in-scope mitigation applied, root cause filed upstream as
[open-gsd/gsd-core#3631](https://github.com/open-gsd/gsd-core/issues/3631).

**Phase 15 (public extraction of markdown-linting + pr-workflow) complete (2026-08-18):** both
capabilities shipped as standalone public repos — `davdittrich/markdown-linting` and
`davdittrich/pr-workflow`, fresh single-commit history, MIT LICENSE, `claude plugin validate .
--strict` clean from a fresh HTTPS clone. `gsd-beads`' shared `marketplace.json` repointed at both
via `url`-type HTTPS sources (no SSH-shorthand regression), real marketplace add/install/uninstall
round trip proven twice (scratch pre-push, real marketplace post-push). Both `ship:pre` gates
re-proven live from the marketplace-installed copy, reproducing Phase 13's/14's smoke-test outcomes
exactly (`15-GATE-REPROOF.md`). Per an explicit operator instruction superseding this phase's own
locked D-00 "stay untouched" clause, both in-repo dogfood bundles were then removed from
`gsd-beads` entirely (tracked and on disk) — CI green on the removal commit, `beads-lifecycle`
still installs from the same marketplace, both capabilities remain active here from their
user-scope grants. Phase verification passed 10/10 (all four ROADMAP success criteria SC-1..SC-4
independently re-checked against live `gh`/`claude plugin`/CI state, not just SUMMARY narration).

**Phase 16 (beads issue content parity) complete (2026-08-19):** `bd show <issue-id>` is now
self-sufficient. Write path (16-01): every `bd create` for a task/epic carries a real description
and `--acceptance`, closing the title-only gap. D-08 backstop (16-02): a phase-wide idempotent
`reconcile-stale-closed` step at `verify:post` closed Phase 14's four stale-open issues as live
proof. Read path (16-03/16-04): `sync.py`'s `check_execute_plan_patch` detector gates
`strip_task_bodies`, which turns a synced `PLAN.md`'s `auto`/`tracer` task blocks into
name+beads-id+files pointers; a machine-local `execute-plan.md` patch makes `gsd-executor` read
those tasks' instructions from `bd show`, hard-halting on an unreachable bd. Filed upstream as
open-gsd/gsd-core#3646 (the read-path change) and #3647 (an unrelated capability-dispatch
reliability finding). UAT (3/3 passed) verified the branch-trigger conditions live against real
bd rather than a synthetic mock — no stripped plan exists yet in this repo for a full
`gsd-executor` end-to-end run, which remains open as the one unverified path.

</details>

## Context

gsd-core currently has zero issue-tracker integration (`grep -rli "beads\|bd create\|bd ready"`
across the distribution returns 0 hits). Task state lives entirely in hand-maintained
`.planning/` markdown, archived away at milestone close, with no query surface, no enforced
dependencies, and nothing that detects drift between plan and reality.

gsd-core ships a runtime capability registry overlay (`src/capability-loader.cts`, tested by
`tests/capability-loader.test.cjs`) that composes third-party capability directories onto the
frozen first-party registry at either `$GSD_HOME/.gsd/capabilities/<id>/` (global) or
`<projectRoot>/.gsd/capabilities/<id>/` (project). Capabilities bind through three mechanisms:
`steps[]` (run a skill/agent at a lifecycle point), `contributions[]` (inject a prompt fragment
into the orchestrator or verifier — the mechanism that makes this integration first-class rather
than a side effect), and `gates[]` (block a lifecycle point on a predicate). Gate predicates are
restricted to `command-exists` and `artifact-frontmatter-equals` — there is no predicate that
queries an external tool directly, which is why the capability must project live `bd` state into
a generated `BEADS.md` artifact at every step for gates to read.

The closest shipped analogue for shape and degrade-cleanly behavior is
`capabilities/mempalace/capability.json` — read it before implementing.

Binding model: phase ↔ epic, `PLAN.md` task ↔ issue (bound by an explicit `beads-id:`, never by
title), task dependency ↔ `bd dep add`, requirement id ↔ issue label. In `authoritative` mode
beads owns task *status* AND task *content* (title/description) — content originates in
`PLAN.md` at first sync, but the bd issue is authoritative from then on; `PLAN.md`'s task text
is not re-edited to follow later bd edits. Content divergence (B10) is therefore defined as a
`PLAN.md` task description that no longer matches its issue's content at the time the issue was
last synced from `PLAN.md`, not an ongoing two-way merge.

## Constraints

- **Installation**: Runtime overlay only, no fork/patch to gsd-core — reserved id prefixes
  (`gsd-`, `gsd-core-`, `anthropic-`) are rejected by the loader, so the capability id is `beads`.
  **Overridden 2026-08-15 (user decision, Phase 3 planning):** installed `ship.md` hardcodes
  `ship:pre` gate dispatch to `capId=='security'/'broken-windows'` only — no generic loop exists,
  so Phase 3's declared `gates[]` can never fire without a local, global `ship.md` patch. User
  explicitly authorized a machine-local patch as in-scope Phase 3 work (plan `03-03`, not deferred
  follow-up), plus an upstream feature request (open-gsd/gsd-core#3554) that would make the local
  patch unnecessary if merged. Phase 3 is not complete until `03-03` lands — the override covers
  this phase's execution scope, not this constraint's default going forward.
  Tracked via `.planning/` PLAN.md files only (no `bd` ticket) — this project's actual workflow
  has never routed its own dev-task tracking through the `beads` capability being built; `bd` is
  reserved for standalone bug reports (e.g. `gsd-beads-bgb`, `gsd-beads-uh1`), not phase task
  tracking.
- **Runtime**: Requires the `bd` binary on `PATH`; no dependency beyond `bd` and Python 3 stdlib
- **Compatibility**: Declares `engines.gsd: ">=1.6.0"`; a version mismatch must skip with a
  warning, never crash
- **Config namespace**: All config keys live under `beads.*` — must be checked against every
  shipped manifest before use to avoid a collision (collisions are rejected by the loader)
- **Fail-open**: `bd` absent, non-zero exit, or a locked DB must never block a gsd phase — gates
  use `onError: skip`, and a missing/unreadable `BEADS.md` means the gate simply does not fire
- **Global-scope installs**: Pass a consent gate (CB-3) before use; ship project-scoped first

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Overlay capability (`beads`), not a gsd-core fork | Forking buys maintenance of 79 skills / 45 capabilities to add one integration and diverges from upstream permanently; overlays are a supported, tested extension point | Shipped Phase 1 — project-scope install/consent confirmed working against real gsd-core 1.10.0 |
| `beads.sync_mode` defaults to `authoritative` for status and content | Discuss-phase 1 reversal (2026-08-15) of the original status-only split: bd is the single editable record post-creation, `PLAN.md` is not re-synced from it — avoids a two-way content merge while keeping one authoritative owner | Shipped Phase 1 (D-01) |
| Gate predicates read only generated artifact frontmatter (`BEADS.md`), never query `bd` directly | The only two shipped predicate kinds are `command-exists` and `artifact-frontmatter-equals`; no predicate calls an external tool | — Pending (BEADS.md generation and gates are Phase 2/3 scope; `capability.json`'s `gates[]`/`contributions[]` intentionally empty in Phase 1) |
| `gates[].onError: skip`, never `halt` | A missing/unreadable `BEADS.md` (capability disabled, `bd` absent, first run) must never strand a finished phase — the gate blocks only on a known bad state | — Pending (Phase 2/3 scope) |
| Real `bd` v1.2.1 CLI diverges from initial RESEARCH.md in three ways, discovered live during Phase 1 execution | `--id` on issue create fails (ids are DB-prefix-derived, not passable); child ids are hierarchical/sequential so a duplicate create yields a *new* id rather than erroring (resolve-by-`beads-id`-before-create is mandatory, not just tidy); `bd list --parent` hides closed issues by default (an orphan sweep on the default listing would silently break B5 idempotency — must pass an explicit status filter) | Shipped Phase 1 — `sync.py` built against the verified real behavior, not the stale doc; RESEARCH.md corrected in-place |
| gsd-core project-scope capability consent is a content hash over the whole bundle | Any file edit inside an already-consented bundle (even a legitimate bug fix) silently deactivates the capability — `render-hooks` just stops naming it, no error. Discovered when a post-code-review fix invalidated Phase 1's own install/consent 11 minutes after the checkpoint closed; caught only because the verifier independently re-ran `render-hooks` live instead of trusting green tests | Operational gotcha, not a beads-specific behavior — re-run `capability install --scope project` after any post-consent bundle edit, every phase, going forward |
| Installed `ship.md`'s `ship:pre` dispatch hardcodes `capId=='security'/'broken-windows'`, no generic gate-enumeration loop (unlike `ship:post`'s steps) | Discovered during Phase 3 planning (plan-checker blocker) via a full-file read of the installed workflow, not inference — Phase 3's declared `gates[]` would otherwise silently never fire, making ROADMAP.md Success Criteria 1/2 false-but-unnoticed at ship time | User overrode the no-fork-patch constraint for a machine-local `ship.md` patch, folded in as in-scope Phase 3 work (plan `03-03`) rather than deferred; also filed upstream (open-gsd/gsd-core#3554, closed 2026-08-15 as filed-without-template; re-filed as open-gsd/gsd-core#3559 with `beads`' own `capability.json` gates as the concrete repro). **Shipped and live-verified** — patch present at `$HOME/.claude/gsd-core/workflows/ship.md`, `check-shipmd-patch` exits 0, ship:pre gates confirmed to actually block/pass via a live `gsd_run check predicate` smoke test against a synthetic `BEADS.md`. Tracked via PLAN.md only, no `bd` ticket (see Constraints note above) |
| bd's real schema-version skew (DB migrated to v65 by an accidentally-shipped v1.2.1 binary; this project's v1.2.2 binary only understood v53) blocked every real `bd` operation for the full duration of Phases 1-3 and part of Phase 4 | Discovered live during Phase 4 execution when the user pointed out `bd` was actually installed with a real database, contradicting every "bd unavailable" fail-open message the project had printed since Phase 1 | Recovered via beads' own official `RECOVERY-1.2.1.md` doc: backed up `.beads/` to `.beads.backup-pre-recovery`, rolled the schema cursor back to v53 via a `dolt sql` `DELETE FROM schema_migrations WHERE version > 53` + commit. `bd` now fully functional; Phase 4's 3 plans' tasks were retroactively synced to and closed in the real database (epic `gsd-beads-i3i`), the first real end-to-end `bd` round-trip this project has ever had against its own actual database (not a scratch/`bd init --prefix live` dir) |
| `capability.json`'s `plan:post` `beads-sync` step declared `"produces": ["BEADS.md"]` — wrong; `create_issues()` only ever rewrites `PLAN.md` in place | Found by `gsd-integration-checker` during the v1.0 milestone audit, independently confirmed via direct source read (sync.py:828-892) before accepting the finding | Fixed same session (commit `4230234`): corrected to `"produces": ["PLAN.md"]`, re-installed/re-consented at project scope, 88/88 tests still green |
| PUB-03 satisfied by the documented manual `capability install` step, not an automatic bridge | Three reasons converge: REQUIREMENTS.md's own Future Requirements section already defers postinstall-hook environment research as out of scope; an automated `--yes` grant fired from a hook would defeat gsd-core's CB-3 human-gated consent check by design; PUB-04's Phase-8 ship allowlist omits `.gsd/capabilities/beads/`, so an automation targeting that path would work today and silently break at first public release | **Superseded 2026-08-17 (see next row) — this row is retained for audit trail, not current policy.** Originally verified 2026-08-16 from a clean `/tmp` scratch project: `node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability install "<clone-root>/.gsd/capabilities/beads" --scope project --yes` followed by `capability state --raw` reported `beads` `installed: true, active: true`. Transcript in `06-01-SUMMARY.md` |
| **Correction:** the row above was never actually decided by the user | Phase 6 (`06-01-PLAN.md` Task 3) had no `06-CONTEXT.md` (discuss-phase skipped) and no `AskUserQuestion` checkpoint — the planner unilaterally chose "do not build an auto-install bridge," rated it a `high`-severity threat (T-06-01) to justify the choice, then the executor wrote it into this table as a settled architectural decision. User flagged this 2026-08-17 during Phase 10 debugging (beads had silently degraded — `.gsd-capabilities.json` isn't git-tracked, so its consent record doesn't survive across sessions/checkouts, and a `capability.json` edit after the last manual install invalidates it with zero error, per the row two above) | User explicitly re-decided 2026-08-17, presented the real CB-3 tradeoff (auto-grant bypasses human bundle review) and chose **auto-install, scope user**, accepting that tradeoff — and extended it beyond `beads` to `ponytail-everywhere` (Phase 10) too, plus `sota-numerics` (Phase 11, not yet planned) reusing the same mechanism from the start. Phase 10.1 (`capability auto-install`) inserted between Phase 10 and Phase 11 to implement it once, shared across all three capabilities — reverses T-06-01, must also close the silent-invalidation gap (detect-and-re-grant, not grant-once) |
| Phase 10.1 (`capability auto-install`) shipped: `hooks/capability-auto-install.sh` vendored into both `beads-lifecycle` (root) and `ponytail-everywhere`, called from each `session-start.sh` before `exec`. Hashes the whole bundle dir (content + structure) against a per-id sidecar at `${GSD_HOME:-$HOME}/.gsd/capability-auto-install-<id>.hash`; on drift/absence runs `capability install <abs-bundle-dir> --scope global --yes` and prints a one-line notice — closes the detect-and-re-grant gap this row's predecessor left open | Plan-checker + verifier + code review (1 blocker, fixed) + a real `claude plugin marketplace add`/`install ponytail-everywhere@gsd-beads` cycle run live on this machine, closing RESEARCH Assumption A2 (subdirectory-sourced plugin cache layout matches root-sourced) | Shipped 2026-08-17 (commits `c305941`..`1661289`). Code review CR-01 (release.yml zip omitted `ponytail-everywhere/`) fixed same session (`383bbc2`) and independently re-verified by the verifier. Assumption A3 (macOS `shasum -a 256` fallback) is an accepted, documented, untested gap — no macOS hardware available. 3 advisory code-review warnings (symlink-blind bundle hashing, test-isolation fragility, ladder-level text inconsistency between `session-start.sh` and its fragment files) left open, non-blocking |
| `hooks/hooks.json` ships the bare `bd prime --hook-json` command, `.claude/settings.json` deleted in the same change | Claude Code's own SessionStart contract already fails open on a missing binary (no hand-rolled PATH guard needed); keeping both files would double-fire `bd prime` every session, since hook dedup does not cross a settings-file/plugin-hooks.json boundary | Shipped Phase 6. Live-verified twice: headless `claude -p --debug hooks` probe (executor) and a real interactive TTY session with `--debug hooks --debug-file` (user, 2026-08-16) both show `Hook SessionStart (bd prime --hook-json) provided additionalContext` exactly once. SessionStart `additionalContext` is injected silently into model context, not printed to the terminal — absence of a visible startup banner is expected, not a fire-count of zero |
| A merely checked-out gsd-beads repo (no `/plugin install` ever run) does not auto-load `hooks/hooks.json` | Resolved RESEARCH.md's open Assumption A1 empirically rather than assuming either outcome | This repo's own dev sessions now depend on the `beads@gsd-beads` plugin staying installed at local scope — left installed (not uninstalled) at the end of Phase 6 for exactly that reason |
| `.beads/config.yaml`/`.beads/metadata.json` were stripped from git history in Phase 7 but never added to `.gitignore` | Found by code review (07-REVIEW.md CR-01): untracked-by-omission is fragile — a future `bd` regen + `git add .` would silently re-track and re-push both files to the now-public repo | Fixed same session (commit `1cfa2fc`), independently re-verified via `git check-ignore -v`, pushed to `origin/main` before the phase was marked complete |
| `.github/workflows/release.yml` interpolated `github.ref_name` directly into a `run:` shell command | Found by code review (08-REVIEW.md WR-02): classic GitHub Actions tag-name script-injection pattern, not mitigated via `env:` indirection | Fixed same session (commit `b4a7903`), independently confirmed pushed during Phase 8 goal verification |
| README's beads-vs-gsd value proposition and lifecycle-integration example were missing entirely | Phase 8 UAT (human comprehension test) reported the README explains the mechanism of gsd-beads but never why a reader would choose it over gsd-core's built-in `.planning/` tracking, and the worked example showed only bare `bd` commands, not the `/gsd-plan-phase` → `/gsd-execute-phase` → `/gsd-verify-work` integration | Diagnosed (root cause: content existed in `docs/prd-beads-capability.md` §3.1-3.2 and PROJECT.md's own Core Value line but was never pulled into README), fixed via gap-closure plan `08-03-PLAN.md` (commits `83b3897`, `3e0e31f`), re-verified, UAT passed |
| Two new hard requirements (PUB-11 SKILL.md parity, PUB-12 gsd-tailored PRIME.md) surfaced during Phase 8 UAT, after `v1.1.0` had already shipped | User explicitly ruled these hard requirements for v1.1, not deferred ideas — despite the public release already existing | Added to REQUIREMENTS.md, new Phase 9 (Beads Content Depth) created via `gsd_run phase add`; Phase 9 must complete before v1.1 is considered done, followed by a `v1.1.1` patch release replacing the public `v1.1.0` archive |
| `get-available-resources` dropped from v1.2's originally-scoped three plugins, replaced by Phase 16 (beads issue content parity) | Discuss-phase (2026-08-19) surfaced that every synced `bd` issue was title-only (no description/acceptance criteria), a gap discovered mid-milestone and judged higher-priority than the third planned plugin — beads is this project's own core dependency, not a new capability, so fixing it compounds | `get-available-resources` moved to Out of Scope (deferred, not invalidated); Phase 16 shipped in its place (D-01..D-08, 4/4 plans) |
| Phase 16 chose full inversion (task content lives in `bd`, `PLAN.md` becomes a pointer) over a minimal one-shot `--description` write | Discuss-phase resolved two competing proposals surfaced 2026-08-18; full inversion closes the drift-forever problem a one-shot write would leave open (D-01) | Shipped Phase 16 — write path (16-01), read path (16-03/16-04), `gsd-executor` patch filed upstream (open-gsd/gsd-core#3646). One gap: no real stripped `PLAN.md` has run through a live `gsd-executor` session yet in this repo, so branch-trigger conditions are UAT-verified live against real `bd`, not full end-to-end |
| Phase 17 (17-04) D-08: collapse `check_shipmd_patch`/`check_execute_plan_patch`'s two CLI verbs into one, hard break, no alias window | A published-plugin CLI contract change with no external callers (confirmed by grep before the plan was written) — the checkpoint existed to confirm the source-artifact conflict (ROADMAP Criterion 4 said both verbs survive; CONTEXT.md D-08 said collapse) and the verb shape, not to re-litigate whether to collapse | User confirmed live via `AskUserQuestion` mid-execution (2026-08-20): option-a, recommended shape (`check-patch <target> [--path]`). ROADMAP Criterion 4 amended in the same commit to record D-08 supersession; zero surviving references to either retired verb; 246/246 tests green |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

## v1.0 Ship Summary

Shipped 2026-08-16. 4 phases, 11 plans, 20 tasks, ~4,400 LOC (`sync.py` + `test_sync.py`).
Milestone audit: 14/14 requirements satisfied, 4/4 phases integration-verified, status `tech_debt`
(one capability.json metadata bug found and fixed same session; two minor items backlogged —
Phase 4 SUMMARY.md files missing `requirements-completed` frontmatter, and Phases 2-3-4 missing
reconciled Nyquist `VALIDATION.md` coverage — neither blocks shipped functionality).

## v1.2 Ship Summary

Shipped 2026-08-19. 4 phases (13-16), 16 plans, 57 tasks, 58 files changed (+1640/-785 lines).
8/8 v1 requirements (MDL-01..04, PRW-01..04) satisfied; Phase 16's D-01..D-08 decision set
satisfied with no `REQ-*` IDs (mirrors the Phase 15 precedent). Two capabilities
(`markdown-linting`, `pr-workflow`) shipped as public, independently installable plugins. One
scope change mid-milestone: `get-available-resources` (originally the third target plugin)
dropped in favor of Phase 16 (beads issue content parity) — deferred, not invalidated. One open
gap carried forward: Phase 16's `gsd-executor` bd-read patch is UAT-verified live against real
`bd` but not yet exercised end-to-end against a real stripped `PLAN.md` in this repo.

---
*Last updated: 2026-08-20 — Phase 17 (v1.3's only phase, Config/Code Truth) complete:
TRUTH-01..04 moved to Validated. Deep code review clean of blockers; phase verification passed
4/4 against live-executed checks. Milestone v1.3 is feature-complete, `/gsd-complete-milestone
v1.3` not yet run. See Current State / Current Milestone above.*

*Previously: 2026-08-19 — v1.2 milestone (New Capability Plugins) shipped: Phase 16 (beads
issue content parity) complete, `get-available-resources` moved to Out of Scope (deferred), MDL/PRW
requirements and Phase 16's D-01..D-08 moved to Validated. See Current State / Next Milestone Goals
above.*

*Previously: 2026-08-18 — Phase 15 (public extraction of markdown-linting + pr-workflow) complete:
both plugins public, marketplace-reachable, gate-proven from the installed copy; both in-repo
dogfood bundles removed per explicit operator instruction.*

*Previously: 2026-08-18 — Phase 14 (pr-workflow dogfood) complete. Milestone v1.2 (New Capability Plugins) started: PUB-11/PUB-12 moved
to Validated (Phase 9 shipped, `v1.1.1` released); Current Milestone section repointed at v1.2's
three new capability plugins (`pr-workflow`, `markdown-linting`, `get-available-resources`).*

*Previously: 2026-08-17 — Phase 10.1 (capability auto-install) complete: shared
SessionStart-triggered auto-install/re-grant mechanism shipped for both `beads` and
`ponytail-everywhere`, reversing the T-06-01 "do not build it" decision and closing the
silent-invalidation gap discovered debugging Phase 10 (see Key Decisions). No PUB-XX requirement
IDs (CAP-01..CAP-07 minted at planning, tracked in ROADMAP.md/PLAN.md only, matching the Phase 10
D-01..D-05 precedent). Does not touch beads' Active requirements list or Out of Scope.

Phase 10 (ponytail-everywhere capability plugin) complete: a second, unrelated capability +
Claude Code plugin (`ponytail-everywhere` / `.gsd/capabilities/ponytail/`) shipped in this repo,
out of the v1.1 milestone's requirement set (new scope routed directly from `/gsd-explore`, no
PUB-XX requirement IDs — decisions tracked locally in `10-CONTEXT.md` as D-01..D-05, not here).
Does not touch beads' requirements, Active list, or Out of Scope. Phase 8 (README, Release & Ship
Gate) complete: PUB-04/PUB-07/PUB-09 shipped, verified, and gap-closed (G-08-1). `v1.1.0` public
on GitHub. Phase 9 (Beads Content Depth) created for PUB-11/PUB-12, required before v1.1 is
considered done.*
