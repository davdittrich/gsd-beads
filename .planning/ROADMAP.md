# Roadmap: beads capability for gsd-core

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 (shipped 2026-08-16) — `.planning/milestones/v1.0-ROADMAP.md`
- ✅ **v1.1 Publish & Document** — Phases 5-12 (shipped 2026-08-18) — `.planning/milestones/v1.1-phases/`
- ✅ **v1.2 New Capability Plugins** — Phases 13-16 (shipped 2026-08-19) — `.planning/milestones/v1.2-ROADMAP.md`
- ✅ **v1.3 Config/Code Truth** — Phases 17-18 (shipped 2026-08-20) — `.planning/milestones/v1.3-ROADMAP.md`

## Phases

<details>
<summary>✅ v1.0 milestone (Phases 1-4) — SHIPPED 2026-08-16</summary>

- [x] Phase 1: Substrate (3/3 plans)
- [x] Phase 2: Visibility (2/2 plans)
- [x] Phase 3: Enforcement (3/3 plans)
- [x] Phase 4: Adoption (3/3 plans)

</details>

<details>
<summary>✅ v1.1 Publish & Document (Phases 5-12) — SHIPPED 2026-08-18</summary>

- [x] Phase 5: Plugin Manifest
- [x] Phase 6: Runtime Integration
- [x] Phase 7: Hygiene & Publication
- [x] Phase 8: README, Release & Ship Gate
- [x] Phase 9: Beads Content Depth
- [x] Phase 10: ponytail-everywhere capability plugin
- [x] Phase 10.1: capability auto-install (INSERTED)
- [x] Phase 11: sota-numerics capability plugin
- [x] Phase 11.1: beads.enabled default flip to true (INSERTED)
- [x] Phase 12: Ship ponytail-everywhere and sota-numerics plugins publicly

</details>

<details>
<summary>✅ v1.2 New Capability Plugins (Phases 13-16) — SHIPPED 2026-08-19</summary>

- [x] Phase 13: markdown-linting capability (dogfood) (4/4 plans)
- [x] Phase 14: pr-workflow capability (dogfood) (3/3 plans)
- [x] Phase 15: Ship markdown-linting and pr-workflow plugins publicly (5/5 plans)
- [x] Phase 16: beads issue content parity (4/4 plans)

</details>

<details>
<summary>✅ v1.3 Config/Code Truth (Phases 17-18) — SHIPPED 2026-08-20</summary>

- [x] Phase 17: Config/Code Truth (4/4 plans) — TRUTH-01..04: every declared config value has an
  observable effect, decimal phases stop failing silently, the hook survives the upstream release
  that natively covers two of its five dispatch points, and the two patch-check clones become one
  reader
- [x] Phase 18: Address tech debt: patch-check doc accuracy + CHANGELOG (4/4 plans) — every claim
  the capability makes about itself is true again: patch-check docstring/messages match the code,
  CHANGELOG documents all four of Phase 17's requirements, both version declarations match `main`,
  the withdrawn `v1.3.0` tag is gone, the four already-shipped bd issues are closed, and both
  machine-local gsd-core patches are live again

</details>

