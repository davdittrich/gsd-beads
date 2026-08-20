---
phase: 18
plan: 01
subsystem: gsd-core-local-patches
tags: [patch-reapply, machine-local, tracer, doc-accuracy]
dependency-graph:
  requires: []
  provides:
    - "ship:pre generic step dispatch patch (v2) restored on both runtime homes"
    - "execute-plan bd task-content read patch (v1) restored on both runtime homes"
    - "GSD-CORE-PATCH.md names the reapply-verification mechanism"
  affects:
    - "$HOME/.claude/gsd-core/workflows/ship.md (machine-local, not tracked)"
    - "$HOME/.claude/gsd-core/workflows/execute-plan.md (machine-local, not tracked)"
    - "$HOME/.codex/gsd-core/workflows/ship.md (machine-local, not tracked)"
    - "$HOME/.codex/gsd-core/workflows/execute-plan.md (machine-local, not tracked)"
    - "plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md"
tech-stack:
  added: []
  patterns:
    - "Insert-only marker-bracketed patch reapplication (never whole-file copy) against a verbatim block already registered in GSD-CORE-PATCH.md"
key-files:
  created: []
  modified:
    - "plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md"
    - "$HOME/.claude/gsd-core/workflows/ship.md (machine-local)"
    - "$HOME/.claude/gsd-core/workflows/execute-plan.md (machine-local)"
    - "$HOME/.codex/gsd-core/workflows/ship.md (machine-local)"
    - "$HOME/.codex/gsd-core/workflows/execute-plan.md (machine-local)"
decisions: []
metrics:
  duration: "~35min"
  completed: "2026-08-20"
actuals:
  tokens: 38000
  tasks: 3
  commits: 1
status: complete
---

# Phase 18 Plan 01: Restore machine-local gsd-core patches + name the reapply mechanism Summary

Reapplied both machine-local gsd-core patches (ship:pre step dispatch v2, execute-plan bd
task-read v1) verbatim to both live runtime homes (`~/.claude`, `~/.codex`) after an automatic
gsd-core update had silently wiped all four files, and added a new subsection to
`GSD-CORE-PATCH.md` naming `verify-reapply-patches.cjs` and `sync.py check-patch` as the
reapply-verification path.

## What Was Built

**Task 1 (tracer):** Inserted Patch 1 (`<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->`)
into `$HOME/.claude/gsd-core/workflows/ship.md` at the documented anchor (after preflight step 6's
final line, before `</step>`), copied byte-for-byte from `GSD-CORE-PATCH.md`'s verbatim block.
Insert-only — no whole-file copy. Verified: `check-patch ship-md` exits 0 (`present (v2)`), `diff`
against the pre-update backup is byte-empty, marker count is 2, `wc -l` is 638. Re-ran the same
verify block after the edit (tracer feedback gate, autonomous run) — passed, so expansion to Task
2 proceeded without a checkpoint.

**Task 2 (auto):** Repeated the proven procedure for the three remaining combinations: Patch 2
into `~/.claude/gsd-core/workflows/execute-plan.md`, Patch 1 into
`~/.codex/gsd-core/workflows/ship.md`, Patch 2 into `~/.codex/gsd-core/workflows/execute-plan.md`.
All copied verbatim from `GSD-CORE-PATCH.md`, no home-specific adaptation (both patch bodies are
confirmed runtime-agnostic). Backup reconciliation: read `backup-meta.json` first per the plan's
instruction — `from_version` already read `1.11.0` (matching `$HOME/.claude/gsd-core/VERSION`) and
`diff` against both live `~/.claude` files was already empty, so **no backup edit was made**,
matching the plan's explicit "if already correct, record the finding rather than manufacturing a
write" instruction. `python3 -m unittest discover -s tests -t tests` from the plugin tree:
`Ran 248 tests` / `OK` — replacing the pre-plan `FAILED (failures=6)`.

**Task 3 (auto):** Added a new "Reapply verification: two independent mechanisms" subsection to
`GSD-CORE-PATCH.md` naming `verify-reapply-patches.cjs` (its known version-churn false-positive
limitation, stated from reading the script directly) and `sync.py check-patch <target> [--path]`
(the authoritative marker-only detector, with the `--path` override documented for probing the
second runtime home). Also recorded the two facts this phase established: an automatic update can
silently back up patched files then install unpatched ones, and neither the backup nor a live
patched file may cross the two separately-templated runtime homes. Cross-referenced rather than
restated both patches' existing "Patch-loss detection is independent" subsections.

Re-synced the gitignored runtime overlay (`.gsd/capabilities/beads/GSD-CORE-PATCH.md`) by copying
the tracked file directly, since `diff -rq` showed drift and no `gsd-tools capability update`
invocation was needed for a single-file overlay copy — matches the acceptance criterion's own
documented fallback for the "reports upgraded but copies nothing" known behavior.

## Verification (all plan-level checks re-run live after all three tasks)

- `check-patch ship-md` (default `~/.claude`) → exit 0, `present (v2)`
- `check-patch execute-plan` (default `~/.claude`) → exit 0, `present (v1)`
- `check-patch ship-md --path ~/.codex/...` → exit 0, `present (v2)`
- `check-patch execute-plan --path ~/.codex/...` → exit 0, `present (v1)`
- `diff` of both `~/.claude` live files against `gsd-local-patches` backup → byte-empty
- `python3 -m unittest discover -s tests -t tests` → `Ran 248 tests`, `OK`
- `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/` → empty
- `GSD-CORE-PATCH.md` contains `verify-reapply-patches.cjs`, `--path`, `check-patch`,
  `gsd-local-patches`

## Deviations from Plan

**None functionally — one process note.** Tasks 1 and 2's target files
(`$HOME/{.claude,.codex}/gsd-core/workflows/{ship,execute-plan}.md`) are machine-local and, per
the plan's own "Artifacts this phase produces" section, "not tracked in git, not in
`.planning/intel/API-SURFACE.md` and never will be." There is therefore no in-repo diff to stage
or commit for Tasks 1 and 2 — `git status --short` was empty after each. This is expected given
the plan's explicit output description (four machine-local files + one tracked doc), not an
omission; only Task 3's edit to `GSD-CORE-PATCH.md` produced a commit. Fixed one self-introduced
indentation typo in the Task 1 insertion (5-space continuation instead of 3-space) immediately
after the first `diff` check caught it, before recording any acceptance criterion as passing.

## Known Stubs

None.

## Threat Flags

None — this plan's only new surface (text inserted into two machine-local runtime workflow files)
is explicitly covered by the plan's own `threat_model` (T-18-01-01 through T-18-01-04), all
mitigated as designed: insert-only edits from a git-tracked verbatim source, byte-equality proof
against an independent backup, and a cross-home leakage grep that returned 0.

## Self-Check: PASSED

- FOUND: plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md (verify-reapply-patches.cjs count 2, --path count 2, check-patch count 5, gsd-local-patches count 2)
- FOUND: commit e853a29 (`git log --oneline` confirms `docs(18-01): name verify-reapply-patches.cjs and check-patch as the reapply-verification path`)
- FOUND: $HOME/.claude/gsd-core/workflows/ship.md carries Patch 1 v2 (check-patch exit 0)
- FOUND: $HOME/.claude/gsd-core/workflows/execute-plan.md carries Patch 2 v1 (check-patch exit 0)
- FOUND: $HOME/.codex/gsd-core/workflows/ship.md carries Patch 1 v2 (check-patch --path exit 0)
- FOUND: $HOME/.codex/gsd-core/workflows/execute-plan.md carries Patch 2 v1 (check-patch --path exit 0)
