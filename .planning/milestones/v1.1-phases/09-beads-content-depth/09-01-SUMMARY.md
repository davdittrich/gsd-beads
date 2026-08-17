---
phase: 09-beads-content-depth
plan: 01
subsystem: infra
tags: [beads, bd, hooks, session-start, plugin]

requires:
  - phase: 08-publish-package
    provides: allowlisted release archive build (.claude-plugin, hooks, .agents/skills, README.md, LICENSE)
provides:
  - gsd-tailored bd prime override, materialised via a self-healing SessionStart hook
affects: [09-04-release]

actuals:
  tokens: 8000
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Self-healing runtime artifact: tracked source in the allowlisted skill tree, gitignored runtime copy materialised on demand"
    - "Single-process hook chaining (copy-then-exec) to guarantee ordering instead of relying on hooks.json array order"

key-files:
  created:
    - .agents/skills/beads/PRIME.md
    - hooks/session-start.sh
  modified:
    - hooks/hooks.json
    - .gitignore

key-decisions:
  - "PRIME.md source lives in .agents/skills/beads/ (already allowlisted) — no release.yml edit needed (D-01)"
  - ".beads/PRIME.md is gitignored; the tracked source is the sole copy of truth (D-08)"
  - "Copy-if-missing runs inside session-start.sh before exec bd prime --hook-json, guaranteeing D-09's ordering via single-process chaining rather than hooks.json array order"
  - "CLAUDE_PLUGIN_ROOT fallback resolves from the script's own location so the hook is testable without exporting anything (review finding)"

patterns-established:
  - "Pattern: gitignored runtime copy + tracked source, self-healed by a hook — reusable for any other plugin override that must materialise into an installer's working directory"

requirements-completed: [PUB-12]

coverage:
  - id: D1
    description: "bd prime prints the gsd-tailored override naming all six capability.json lifecycle steps, instead of bd's generic default"
    requirement: "PUB-12"
    verification:
      - kind: other
        ref: "bd prime | grep -qF 'execute:wave:post' (09-01-PLAN.md Task 1 <verify>)"
        status: pass
      - kind: other
        ref: "test \"$(bd prime | cksum)\" != \"$(bd prime --export | cksum)\" (09-01-PLAN.md Task 1 <verify>)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Self-heal hook is idempotent, non-clobbering, inert in a non-bd project, and works with CLAUDE_PLUGIN_ROOT set or unset"
    requirement: "PUB-12"
    verification:
      - kind: other
        ref: "scratch-directory guard matrix (09-01-PLAN.md Task 2 <verify>: ordering, content-match, non-clobbering, no-op-without-.beads, both across CLAUDE_PLUGIN_ROOT set/unset)"
        status: pass
    human_judgment: false
  - id: D3
    description: ".beads/PRIME.md gitignored and absent from the release archive; .agents/skills/beads/PRIME.md present in it"
    requirement: "PUB-12"
    verification:
      - kind: other
        ref: "git check-ignore -q .beads/PRIME.md; release.yml allowlist replica zip/unzip listing check (09-01-PLAN.md Task 2 <verify>)"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-08-16
status: complete
---

# Phase 09 Plan 01: Beads Content Depth — Tracer Summary

**Self-healing `bd prime` override: `.agents/skills/beads/PRIME.md` ships in the allowlisted skill tree, `hooks/session-start.sh` materialises it into `.beads/PRIME.md` on demand and hands off to `bd prime --hook-json`, and a plain `bd prime` now names all six gsd-core lifecycle sync points instead of printing beads' generic default.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-16T20:31:00Z
- **Completed:** 2026-08-16T20:56:24Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `.agents/skills/beads/PRIME.md` documents ownership, phase-epic identity binding, all six `capability.json` sync points (including `plan:pre`/`beads-recall`, which the reviewed first draft risked omitting), the ship gate, failure mode, and config keys — 50 lines, terse bullets/table per D-05.
- `hooks/session-start.sh` self-heals `.beads/PRIME.md` from the shipped source whenever it's missing, guarded by three conditions (`.beads/` exists, destination absent, source present), then `exec`s into `bd prime --hook-json` so ordering is guaranteed by single-process chaining rather than hooks.json array order.
- `hooks/hooks.json` rewired to invoke the wrapper via `bash "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"`, JSON shape otherwise byte-identical.
- `.gitignore` gained a `.beads/PRIME.md` stanza so the runtime copy never re-enters tracking, alongside the existing Phase 7 `.beads/config.yaml`/`.beads/metadata.json` precedent.

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end "bd prime prints gsd guidance" — one path only** - `905ac7b` (feat)
2. **Task 2: Harden the self-heal guards and prove the shipping path** - `cdd697e` (chore)

**Plan metadata:** (this commit)

## Files Created/Modified
- `.agents/skills/beads/PRIME.md` - shipped source of the gsd-tailored `bd prime` override
- `hooks/session-start.sh` - self-heal + handoff wrapper (D-02/D-09)
- `hooks/hooks.json` - SessionStart rewired to invoke the wrapper
- `.gitignore` - `.beads/PRIME.md` runtime-copy stanza (D-08)

## Decisions Made
- Kept the fallback `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"` exactly as the cross-AI review suggested — verified in three modes (relative invocation unset, absolute invocation from an unrelated cwd unset, explicit set) during Task 2's matrix.
- Used a stub `bd` on PATH for the guard matrix rather than a real Dolt workspace, since the guards only need to observe file-presence timing, not real `bd` behavior.

## Deviations from Plan

None - plan executed exactly as written. Both cross-AI review findings scoped to this plan (`CLAUDE_PLUGIN_ROOT` fallback, six-vs-five sync points) were already folded into the plan text by the `--reviews` replan before execution began, so no in-flight deviation was needed.

## Issues Encountered

Execution ran inline (main context, sequential) rather than via a spawned `gsd-executor` subagent: this repository is nested inside a parent git repository (`/home/dd/Gemini`), and the harness's `isolation="worktree"` dispatch resolved the worktree against the parent repo instead of `gsd-beads`, cutting a worktree with no `.planning/` at all. The mis-scoped executor detected this immediately and halted before touching any files (no damage). User approved falling back to inline sequential execution for this phase's remaining plans, matching the project's `workflow.use_worktrees: false` config intent. Tracked as a known repo-layout pitfall (nested-repo worktree isolation), not a plan defect.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Wave 2 (09-02) can proceed: six resource documents + SKILL.md index.
- No blockers.

---
*Phase: 09-beads-content-depth*
*Completed: 2026-08-16*
