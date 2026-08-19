# Milestones

## v1.2 New Capability Plugins (Shipped: 2026-08-19)

**Phases completed:** 4 phases, 16 plans, 38 tasks

**Key accomplishments:**

- `markdown-linting` capability wired verify:post -> skill -> lint.py -> LINT-REPORT.md, with a live-recorded proof that the generic `ship:pre` gate dispatch loop actually evaluates its `artifact-frontmatter-equals` predicate for a non-`security`/`broken-windows` `capId`.
- `lint.py verify_post()` now degrades honestly when rumdl can't run -- exit 0, one notice, and a non-numeric `violation_count: unavailable` sentinel that the ship:pre gate correctly reads as `block:true`, backed by a 10-test stdlib suite pinning MDL-01/02/04 against checked-in `clean.md`/`dirty.md` fixtures.
- Fixed 488/489 rumdl violations mechanically across 114 `.planning/`+`README.md`+`CLAUDE.md` files, hand-resolved the one MD024 residual, published the capability's README with a freshly measured 0-vs-309 rumdl/markdownlint-cli2 divergence table, and live-proved both the advisory-ship and rumdl-absent gate behaviors against the real `LINT-REPORT.md`.
- Closed both VERIFICATION.md-FAILED defects in `lint.py` — a rumdl crash exit code no longer leaves LINT-REPORT.md stale, and `count` now fails as cleanly as `fix()` when rumdl/uvx are both absent — pinned by two new regression tests, suite green at 12.
- `pr-workflow` capability wired `execute:wave:post` -> skill -> `pr_status.py` -> `14-PR.md`, with a live-recorded four-state proof that the derived `pr_gate_ok` boolean (not the raw `pr_status`) is what the `ship:pre` gate actually evaluates.
- `pr_status.py` now fails open (one notice, exit 0, sentinel report) across all three `gh`-degraded paths PRW-04 requires, and `ship:post` gets a live, read-only, warn-only notice when no open PR exists for the branch (PRW-03) -- never creating, reading a stale artifact for, or mutating anything.
- Re-consented the `pr-workflow` bundle (edited by 14-01/14-02), then ran and recorded four live cycles against this repo's real `main` branch (baseline, `gh`-absent, `gh`-unauthenticated, no-open-PR) plus a live advisory-gate proof, closing all five ROADMAP Phase 14 Success Criteria with recorded transcripts rather than unit assertions alone.
- Public repo `davdittrich/markdown-linting` created and pushed (commit `d30ab57`), fresh HTTPS clone passes `claude plugin validate . --strict` and all 12 capability unit tests.
- Published `davdittrich/pr-workflow` as a public, independently installable Claude Code plugin — fresh single-commit history, `claude plugin validate . --strict` and the bundle's 27-test suite both green from a fresh HTTPS clone.
- Tasks 1-2 complete and committed (`676e835`, itself carrying `2b3d46d`): `.claude-plugin/marketplace.json` now carries five entries, and both new plugins round-tripped install/uninstall over HTTPS with no SSH key against a scratch marketplace. Task 3, session 2: the operator approved publishing local HEAD in full; `git push origin HEAD:main` succeeded and `origin/main`'s tip is verified as `676e835`, matching local HEAD exactly. The real-marketplace round trip is blocked: `gsd-beads` is a Directory-source marketplace reading the primary checkout at `/home/dd/projects/gsd-beads`, which is still at the pre-Task-1 commit `a922c12` and has not been fast-forwarded — `claude plugin marketplace update gsd-beads` succeeds but the subsequent install fails with "Plugin not found," confirming the primary checkout, not origin, is what the Directory source reads. Followup for the orchestrator: fast-forward `/home/dd/projects/gsd-beads` to `676e835`, then re-run the marketplace-update + install/uninstall round trip for both plugins.
- Both `markdown-linting` and `pr-workflow` were installed from the real, pushed `davdittrich/gsd-beads` marketplace and left installed. Each installed copy's own `hooks/session-start.sh` was invoked directly (the exact command `hooks/hooks.json` registers) three times per capability, proving grant, unchanged-bundle no-op, and cleared-sidecar re-grant at user scope. `15-GATE-REPROOF.md` then reproduced Phase 13's two-case and Phase 14's four-case `ship:pre` gate outcomes exactly, using predicates extracted with `jq` from the installed cache path (never this repo's working tree) against six synthetic artifacts in a scratch directory outside `.planning/`. A separate installed-vs-repo predicate diff confirmed byte-identical output for both capabilities — extraction changed no gate semantics.
- Both `.gsd/capabilities/markdown-linting/` (8 files) and `.gsd/capabilities/pr-workflow/` (9 files) were removed from tracking and disk in one commit (`1e2ef59`) alongside the two `.gitignore` un-ignore-line deletions and the `.gsd-capabilities.json` `pr-workflow` entry removal. Pushed to `origin/main` (170a427..1e2ef59), CI green on the pushed head, `beads-lifecycle` uninstall/reinstall round trip clean, and both extracted capabilities remain active from their global (user-scope) grants after the removal. No tag or release created.
- Every new `bd create` for a task or epic now carries a real `-d` description (and `--acceptance` for tasks), closing the write-path half of D-06 — proven by a live `bd show --json` round trip, not a mocked assertion.
- A phase-wide, idempotent `reconcile-stale-closed` backstop, wired into `verify:post`, closed the four Phase 14 issues that `execute:wave:post`'s per-wave dispatch had silently left open — live data, not a fixture.
- 1. [Rule 3 - Blocking] Edited `plugins/beads-lifecycle/.gsd/capabilities/beads/` instead of the plan's `.gsd/capabilities/beads/`
- A machine-local, marker-bracketed patch now makes `gsd-executor` read an `auto`/`tracer` task's instructions from `bd show <beads-id> --json` — halting hard when bd can't answer — closing the loop plan 16-01 (write content to bd) and 16-03 (strip it from PLAN.md) opened, and the read-path change is filed upstream as open-gsd/gsd-core#3646 with a second, unrelated issue (#3647) reporting a capability-dispatch reliability finding.

---

## v1.0 milestone (Shipped: 2026-08-16)

**Phases completed:** 4 phases, 11 plans, 20 tasks

**Key accomplishments:**

- Every `PLAN.md` task becomes a real, idempotent beads issue bound by explicit `<beads-id>`, with automatic dependency edges and wave-close batching (B1-B6, Phase 1)
- Planner and executor see live beads state before/during work — `BEADS-RECALL.md` at `plan:pre`, regenerated `BEADS.md` and a composed wave-status block at `execute:wave:pre/post` (B7/B8/B11, Phase 2)
- A phase with unfinished blocking issues cannot ship — `ship:pre` gates enforce `blocking_open==0`/`diverged==0`, with a recorded, auditable override path (B9/B10, Phase 3)
- One-shot migration moves hand-tracked todos into beads with priority/label mapping; `beads-status` runs on demand printing the full plan-task↔issue mapping with orphans on both sides; epic granularity is now a per-milestone option (B12/B13/B14, Phase 4)
- Discovered and recovered a real bd database schema-version skew mid-milestone (v65 DB vs v53 binary) via beads' own official recovery doc — the first genuine end-to-end trace against this project's real database
- Milestone audit found and fixed a real `capability.json` metadata bug via cross-phase integration checking

---
