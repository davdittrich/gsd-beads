---
phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly
plan: 04
subsystem: infra
tags: [claude-plugin-marketplace, capability-consent, ship-gate, confound-controlled-proof]

# Dependency graph
requires:
  - phase: 15-03
    provides: real gsd-beads marketplace with markdown-linting and pr-workflow url-type entries, pushed to origin/main and round-trip-verified from the primary checkout
provides:
  - both plugins installed from the real marketplace and left installed (markdown-linting@gsd-beads, pr-workflow@gsd-beads)
  - three-stage consent-cycle proof (grant/no-op/re-grant) driven from each installed copy's own SessionStart hook, at user scope
  - 15-GATE-REPROOF.md, a confound-controlled live re-proof of both ship:pre gates (Phase 13's two-case and Phase 14's four-case outcomes), reproduced entirely from installed-cache predicates against scratch artifacts outside .planning/
affects: [15-05]

actuals:
  tokens: 4529
  tasks: 2
  commits: 1

tech-stack:
  added: []
  patterns:
    - "confound-controlled gate re-proof: extract the predicate with jq from the installed plugin cache path (never the repo copy), evaluate against synthetic artifacts in a scratch directory outside .planning/, and separately diff installed-vs-repo predicate to prove extraction altered no semantics -- this is what makes a passing result attributable to the installed copy and not to anything already committed in this repo"
    - "direct SessionStart hook invocation for consent-cycle proof: CLAUDE_PLUGIN_ROOT=<resolved cache root> bash <root>/hooks/session-start.sh is the exact command hooks/hooks.json registers, so running it by hand reproduces a real session start rather than approximating one"

key-files:
  created:
    - .planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-GATE-REPROOF.md
  modified: []

key-decisions:
  - "Resolved both installed plugin cache roots by search (find ... -name plugin.json -path '*/.claude-plugin/*'), not by assuming the version segment: markdown-linting at /home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0, pr-workflow at /home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0"
  - "Observed interaction between the new user-scope grants and this project's existing project-scope .gsd-capabilities.json entry for pr-workflow: gsd-tools capability list --raw now lists pr-workflow TWICE (scope: global from this task's grant, scope: project from Phase 14's prior grant), both status: active, with no observed collision or shadowing. markdown-linting appears once (scope: global only, since this repo's .gsd-capabilities.json carries no markdown-linting entry). Direct input to Plan 05's decision about the repo-root bundles: the two scopes coexist as independent ledger entries."
  - "The primary checkout's git status --porcelain -- .gsd .gsd-capabilities.json reports one pre-existing line (M .gsd-capabilities.json, a bare updatedAt timestamp bump) that predates this plan's first command by over three hours (file mtime 19:57:47+02:00 vs. this task's first command well after 23:00+02:00) -- confirmed unrelated to this task's user-scope installs, not caused by them. git status --porcelain -- .gsd (directory only) reports nothing; the .gsd/ tree itself is untouched."
  - "Both plugins left installed at the end of this plan per the plan's explicit instruction (no uninstall step) -- unlike 15-03's scratch-marketplace round trip, which uninstalled afterward."

requirements-completed: [D-00, D-10]

coverage:
  - id: T1
    description: "Both plugins install from the real gsd-beads marketplace; installed copy's own SessionStart hook grants each capability at user scope, no-ops on an unchanged bundle, and re-grants when the sidecar is cleared"
    requirement: "D-00"
    verification:
      - kind: other
        ref: "claude plugin install markdown-linting@gsd-beads -y / pr-workflow@gsd-beads -y -> both Successfully installed; claude plugin list shows both enabled at scope: user"
        status: pass
      - kind: other
        ref: "CLAUDE_PLUGIN_ROOT=<resolved cache root> bash <root>/hooks/session-start.sh, run three times per capability with the sidecar deleted between runs 2 and 3 -> grant (line printed, sidecar created), no-op (silent, sidecar byte-identical), re-grant (line printed again, sidecar re-created with the identical hash)"
        status: pass
      - kind: other
        ref: "diff <installed .gsd/capabilities/<id>/capability.json> <~/.gsd/capabilities/<id>/capability.json> -> no output for both capabilities (user-scope bundle byte-identical to the installed copy)"
        status: pass
    human_judgment: false
  - id: T2
    description: "Both ship:pre gates re-proven live with gsd_run check predicate against synthetic artifacts, using the predicate extracted from the INSTALLED copy's capability.json, reproducing Phase 13's two-case and Phase 14's four-case outcomes exactly"
    requirement: "D-10"
    verification:
      - kind: other
        ref: "grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' ship.md -> 2 (lines 157/242, unchanged from Phases 13-14)"
        status: pass
      - kind: other
        ref: "markdown-linting: gsd_run check predicate against synthetic 15-LINT-REPORT.md, violation_count 0 and 7 -> block:false/match:true and block:true/match:false/actual:\"7\", byte-identical to 13-GATE-SMOKE-TEST.md Step 2"
        status: pass
      - kind: other
        ref: "pr-workflow: gsd_run check predicate against synthetic 15-PR.md, all four pr_status states -> block:false for none/passing, block:true/actual:\"false\" for pending/failing, byte-identical to 14-GATE-SMOKE-TEST.md Step 2"
        status: pass
      - kind: other
        ref: "diff <jq -cS installed predicate> <jq -cS repo predicate> -> no output for both capabilities (extraction altered no gate semantics)"
        status: pass
      - kind: other
        ref: "git status --porcelain -- .planning/phases/13-markdown-linting-capability-dogfood .planning/phases/14-pr-workflow-capability-dogfood -> empty, before and after all six predicate runs"
        status: pass
    human_judgment: false

duration: ~15min
completed: 2026-08-18
status: complete
---

# Phase 15 Plan 04: Re-prove Both ship:pre Gates from the Installed Copy Summary

**Both `markdown-linting` and `pr-workflow` were installed from the real, pushed `davdittrich/gsd-beads` marketplace and left installed. Each installed copy's own `hooks/session-start.sh` was invoked directly (the exact command `hooks/hooks.json` registers) three times per capability, proving grant, unchanged-bundle no-op, and cleared-sidecar re-grant at user scope. `15-GATE-REPROOF.md` then reproduced Phase 13's two-case and Phase 14's four-case `ship:pre` gate outcomes exactly, using predicates extracted with `jq` from the installed cache path (never this repo's working tree) against six synthetic artifacts in a scratch directory outside `.planning/`. A separate installed-vs-repo predicate diff confirmed byte-identical output for both capabilities — extraction changed no gate semantics.**

## Performance

- **Duration:** ~15 min
- **Completed:** 2026-08-18T21:35:57Z
- **Tasks:** 2/2
- **Files modified:** 1 (`.planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-GATE-REPROOF.md`, new). Task 1 modifies no repository file by design — it writes only runtime state under `~/.gsd/` (consent sidecars, user-scope capability bundles) and the local plugin cache installs.

## Accomplishments

- Ran `claude plugin marketplace update gsd-beads` and installed both `markdown-linting@gsd-beads` and `pr-workflow@gsd-beads` from the real marketplace over the pushed `origin/main`. Left both installed at the end (no uninstall step, unlike 15-03's scratch round trip).
- Resolved both installed plugin cache roots by search rather than assuming the version segment:
  - `markdown-linting`: `/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0`
  - `pr-workflow`: `/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0`
- Drove each installed copy's `hooks/session-start.sh` directly with `CLAUDE_PLUGIN_ROOT` set to its resolved root, three times per capability, proving all three consent-cycle properties: grant (sidecar created, `Auto-installed capability: <id> (user scope)` printed), no-op (second run silent, sidecar byte-identical), re-grant (sidecar deleted, third run re-creates it with the identical hash and re-prints the line).
- Confirmed both `~/.gsd/capabilities/<id>/capability.json` destinations byte-identical to the installed cache bundle via `diff` (no output).
- Confirmed the ship.md generic gate-dispatch patch marker present at count 2, same lines (157/242) Phases 13-14 recorded.
- Extracted both predicates from the installed cache copies with `jq`, ran `gsd_run check predicate` against six synthetic artifacts (two for markdown-linting, four for pr-workflow) in a scratch directory outside `.planning/`, and got outcomes byte-identical to `13-GATE-SMOKE-TEST.md` and `14-GATE-SMOKE-TEST.md`.
- Diffed installed-vs-repo predicate for both capabilities (`jq -cS` normalised): no output, confirming extraction altered no gate semantics.
- Confirmed `.planning/phases/13-markdown-linting-capability-dogfood` and `.planning/phases/14-pr-workflow-capability-dogfood` untouched (`git status --porcelain` empty) throughout.
- Wrote and committed `15-GATE-REPROOF.md`.

## Task Commits

1. **Task 1: Install both plugins, prove auto-install and re-consent from the installed copy** — no repository file modified (writes only `~/.gsd/` runtime state, per the plan's own `<files>` spec); folded into Task 2's commit as combined evidence.
2. **Task 2: Re-prove both ship:pre gates and record the transcript** — `94cd04f` (docs, `15-GATE-REPROOF.md` only)

## Resolved Installed Plugin Cache Roots

- `markdown-linting`: `/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0`
- `pr-workflow`: `/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0`

## Three-Stage Consent-Cycle Evidence

### markdown-linting

| Stage | Result |
|-------|--------|
| Grant (1st run) | `Auto-installed capability: markdown-linting (user scope)`; sidecar created: `79d2785e32f2ab75f2bb6f7d94e1d7cd1913c5196e2bf2cdb923362d7dd3fb87` |
| No-op (2nd run) | Silent, exit 0; sidecar byte-identical (`diff`, no output) |
| Re-grant (3rd run, after `rm` sidecar) | `Auto-installed capability: markdown-linting (user scope)`; sidecar re-created with the identical hash `79d2785e...` |

### pr-workflow

| Stage | Result |
|-------|--------|
| Grant (1st run) | `Auto-installed capability: pr-workflow (user scope)`; sidecar created: `380ab6b54589bc927fc01bedc028e90d8fce23f4d5991d4a40cbd0af7c2a20d9` |
| No-op (2nd run) | Silent, exit 0; sidecar byte-identical (`diff`, no output) |
| Re-grant (3rd run, after `rm` sidecar) | `Auto-installed capability: pr-workflow (user scope)`; sidecar re-created with the identical hash `380ab6b5...` |

## ship.md Marker Count and Line Numbers

```
$ grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' "$HOME/.claude/gsd-core/workflows/ship.md"
2
```

Lines 157 (opening) and 242 (closing) — identical to `13-GATE-SMOKE-TEST.md` and `14-GATE-SMOKE-TEST.md`, confirming no drift in the installed file across all three phases.

## Observed Interaction: User-Scope Grant vs. Existing Project-Scope Entry

`node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability list --raw` after both grants lists `pr-workflow` **twice**:

- `scope: "global"`, `source: "/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0/.gsd/capabilities/pr-workflow"` (this task's grant)
- `scope: "project"`, `source: "./.gsd/capabilities/pr-workflow"` (Phase 14's pre-existing grant, recorded in `.gsd-capabilities.json`)

Both entries report `status: "active"` independently. `markdown-linting` appears once (`scope: "global"` only — this repo's `.gsd-capabilities.json` carries no `markdown-linting` entry). **No collision, overwrite, or shadowing was observed between the two scopes for the same capability id.** This is direct input to Plan 05's decision about whether the repo-root `.gsd/capabilities/pr-workflow/` bundle can be safely removed now that a marketplace-installed copy exists: the two scopes are independent ledger entries and either can be removed/kept without disturbing the other, as observed here.

## Primary Checkout Working-Tree Note

`git -C /home/dd/projects/gsd-beads status --porcelain -- .gsd .gsd-capabilities.json` reports one pre-existing line, `M .gsd-capabilities.json`. Verified this predates this plan entirely: the file's on-disk mtime is `2026-08-18 19:57:47 +0200`, more than three hours before this task's first command ran (well after `23:00 +0200`), and the diff is a bare `updatedAt` timestamp bump — the same pre-existing unrelated dirty state `15-03-SUMMARY.md`'s session 3 already called out. `git -C /home/dd/projects/gsd-beads status --porcelain -- .gsd` (directory-only, no `.gsd-capabilities.json`) reports nothing: the `.gsd/` tree itself is untouched by this task.

## Commit SHA of 15-GATE-REPROOF.md

`94cd04f` — `docs(15-04): record live gate re-proof from marketplace-installed copies`

## Deviations from Plan

None. Both tasks executed exactly as written; the plan's own `<action>` text for Task 1 anticipated and asked for the pr-workflow dual-scope observation to be "recorded verbatim," which is done above rather than smoothed over.

## Known Stubs

None.

## Threat Flags

None. All five threats registered in this plan's `<threat_model>` (T-15-23 through T-15-28) were mitigated exactly as their disposition specified: predicate source paths and the installed-vs-repo diff are both recorded in `15-GATE-REPROOF.md`; all synthetic artifacts stayed in a scratch directory outside `.planning/`, confirmed via empty `git status --porcelain` for the Phase 13/14 directories; the `ship.md` patch marker was actively re-grepped (count 2) rather than assumed; no file inside `~/.claude/plugins/cache/` was modified (confirmed via `find <cache-root> -newer <pre-run-marker> -type f`, no results).

## Self-Check: PASSED

- `.planning/phases/15-ship-markdown-linting-and-pr-workflow-plugins-publicly/15-GATE-REPROOF.md` — FOUND, committed in `94cd04f`.
- Commit `94cd04f` — FOUND: `git log --oneline --all | grep 94cd04f` matches.
- `~/.gsd/capability-auto-install-markdown-linting.hash` and `~/.gsd/capability-auto-install-pr-workflow.hash` — FOUND, both non-empty, both containing the re-granted hash values quoted above.
- `~/.gsd/capabilities/markdown-linting/capability.json` and `~/.gsd/capabilities/pr-workflow/capability.json` — FOUND, both byte-identical to their respective installed cache bundle copies.
- `claude plugin list` — FOUND: both `markdown-linting@gsd-beads` and `pr-workflow@gsd-beads` listed, enabled, scope user, left installed.

---
*Phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly*
*Plan: 04*
*Completed: 2026-08-18*
