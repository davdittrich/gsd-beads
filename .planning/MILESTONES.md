# Milestones

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
