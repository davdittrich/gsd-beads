# Roadmap: beads capability for gsd-core

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 (shipped 2026-08-16) — `.planning/milestones/v1.0-ROADMAP.md`
- ✅ **v1.1 Publish & Document** — Phases 5-12 (shipped 2026-08-18) — `.planning/milestones/v1.1-phases/`
- 🚧 **v1.2 New Capability Plugins** — Phases 13-15 (current)

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

### v1.2 New Capability Plugins (Phases 13-15)

- [ ] **Phase 13: markdown-linting capability (dogfood)** - `.planning/` markdown quality is measured, reported, and gated advisory — on the already-proven `artifact-frontmatter-equals` mechanism
- [ ] **Phase 14: pr-workflow capability (dogfood)** - PR check status is projected into a generated artifact and gated advisory at `ship:pre`, degrading cleanly without `gh`
- [ ] **Phase 15: Ship markdown-linting and pr-workflow plugins publicly** - Both capabilities become public, marketplace-installable plugins with their gates still firing after extraction

## Phase Details

### Phase 13: markdown-linting capability (dogfood)

**Goal**: This repo's own lifecycle measures and reports `.planning/` markdown quality, and the
first live proof exists that a generic `ship:pre` gate fires for a capId other than `security` /
`broken-windows`.

**Depends on**: Nothing (first phase of v1.2; builds on the shipped `beads` and `sota-numerics`
gate precedent)

**Requirements**: MDL-01, MDL-02, MDL-03, MDL-04

**Success Criteria** (what must be TRUE):

  1. `rumdl` run with an always-explicit `--config <path>` against this repo's own `.planning/`
     tree reports **0 violations**, with the transcript recorded. Every rule in the curated set
     (MD001/MD003/MD009/MD012/MD022/MD024/MD040-equivalents) is present and every disabled rule
     (line-length, inline-HTML, first-line-heading) is named with its reason. The plugin's README
     states rumdl's measured detection divergence from markdownlint-cli2 on this exact ruleset
     (45% miss rate, MD001: 14 vs 1) as a known, accepted difference. (MDL-01)

  2. After a real `verify:post` run, `.planning/LINT-REPORT.md` exists with a `violation_count`
     frontmatter field whose value equals a hand-run `rumdl` count on the same tree, and the file
     carries the "regenerated every step, never hand-edited" banner. (MDL-02)

  3. Before any gate is trusted, the installed `$HOME/.claude/gsd-core/workflows/ship.md` is read
     and confirmed to contain the generic gate-dispatch marker (the machine-local patch from Phase
     3 / gsd-core#3559 — **not** assumed present). Then a live `gsd_run check predicate` smoke test
     against a **synthetic** `LINT-REPORT.md` shows the `markdown-linting` `ship:pre` gate actually
     evaluating: satisfied at `violation_count: 0`, unsatisfied at `violation_count: 7`. This is
     the first live proof of generic `ship:pre` dispatch for a non-`security`/`broken-windows`
     capId. (MDL-03, Pitfall 1)

  4. The gate is **advisory**: a phase whose `LINT-REPORT.md` reports a nonzero count still ships,
     and a visible warning naming the count appears in the ship transcript. (MDL-03)

  5. With `rumdl` removed from `PATH`, a full plan → verify → ship cycle completes with exactly
     **one** visible "rumdl absent" notice, no hang, no non-zero exit, and no stale
     `LINT-REPORT.md` presented as current. (MDL-04)

**Plans**: TBD

### Phase 14: pr-workflow capability (dogfood)

**Goal**: A phase's real GitHub PR check status reaches the ship decision as visible, advisory
information, and the absence of `gh` (or of a PR) never blocks or spams.

**Depends on**: Phase 13 (inherits a proven generic `ship:pre` dispatch baseline to diff against
when this phase's higher-risk gate is introduced)

**Requirements**: PRW-01, PRW-02, PRW-03, PRW-04

**Success Criteria** (what must be TRUE):

  1. After an `execute:wave:post` run on a branch with an open PR, `.planning/PR.md` exists with a
     `pr_status` frontmatter value in `none` / `passing` / `pending` / `failing` that matches what
     `gh pr checks` reports for that branch at that moment; re-running the step rewrites the file
     rather than appending. (PRW-01)

  2. A live `gsd_run check predicate` smoke test against **synthetic** `PR.md` files — one per
     state — shows the `pr-workflow` `ship:pre` gate evaluating tri-state via
     `artifact-frontmatter-equals`: satisfied for `passing` and `none`, unsatisfied for both
     `pending` and `failing`. Not "the manifest declares `gates[]`" — the predicate is observed
     firing. (PRW-02)

  3. The gate is **advisory**: a phase whose `PR.md` says `failing` still ships, with a visible
     warning naming the status. (PRW-02)

  4. Shipping a phase on a branch with no open PR prints exactly one warn-only notice, and
     `gh pr list` for that branch returns the same (empty) result before and after — nothing was
     created. (PRW-03)

  5. With `gh` absent from `PATH`, and again with `gh` present but `gh auth status` failing, a full
     execute → ship cycle completes with exactly one visible notice per case and no stale `PR.md`
     presented as current. (PRW-04)

**Plans**: TBD

### Phase 15: Ship markdown-linting and pr-workflow plugins publicly

**Goal**: Both capabilities stop being subdirectories of this repo and become independently
installable public plugins — with the gates proven in Phases 13-14 still firing from an
installed-from-marketplace copy.

**Depends on**: Phase 13, Phase 14

**Requirements**: None directly — this phase delivers PROJECT.md's stated v1.2 milestone goal
("each dogfooded in this repo then extracted to its own public GitHub repo and marketplace
entry"). Traceability follows Phase 12's extraction playbook decisions D-01..D-10, archived at
`.planning/milestones/v1.1-phases/12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly/`.

**Success Criteria** (what must be TRUE):

  1. `github.com/davdittrich/markdown-linting` and `github.com/davdittrich/pr-workflow` are public
     repos, each with a README naming its external prerequisite first-class (`rumdl`; `gh` +
     authentication), a MIT `LICENSE`, and `claude plugin validate . --strict` exiting 0 from a
     **fresh clone** of the pushed repo.

  2. This repo's `.claude-plugin/marketplace.json` lists both with `url`-type sources carrying
     explicit `https://` git URLs (not GitHub shorthand — per commit `f706179`), and a real
     `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip succeeds for
     each on a path with no SSH key configured. (Pitfall 3)

  3. From the marketplace-installed copy (not the repo working tree), each capability
     auto-installs/re-consents and its `ship:pre` gate is re-proven live with `gsd_run check
     predicate` against the same synthetic artifacts from Phases 13-14 — extraction did not
     silently break the gate or invalidate consent. (Pitfall 2)

  4. Both dogfood subdirectories are removed from `gsd-beads`, every orphaned `ci.yml` /
     `release.yml` / doc reference is repaired in the same commit, CI is green, and a
     `beads-lifecycle` install from the same marketplace still works.

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 13. markdown-linting capability (dogfood) | 0/? | Not started | - |
| 14. pr-workflow capability (dogfood) | 0/? | Not started | - |
| 15. Ship both plugins publicly | 0/? | Not started | - |

## Cross-Cutting Constraints (v1.2)

- **Verify the patch before trusting any gate.** The `ship:pre` generic gate-dispatch
  generalization is a **machine-local patch only**; upstream gsd-core#3559 is filed, not confirmed
  merged. Every phase that declares a gate must first confirm the marker in the installed
  `ship.md`, and must prove the gate live — never accept "the manifest declares `gates[]`" as
  evidence.

- **Re-consent after every bundle edit.** gsd-core's project/global capability consent is a content
  hash over the whole bundle; any post-consent edit silently deactivates the capability with no
  error. Re-run `capability install` (or the vendored `capability-auto-install.sh`) after every
  edit inside a bundle directory.

- **Both new gates default advisory, not blocking.** This is a v1 requirement (PRW-02, MDL-03), not
  a shortcut. Flipping to blocking is v2 (PRW-05, MDL-05) and is out of scope here.

- **Fail-open on every external tool.** `rumdl` and `gh` are external dependencies; every
  contribution and gate declares `onError: skip`, every script guards with `shutil.which()` (plus
  `gh auth status` for `pr-workflow`), and prints exactly one notice per missing tool (B6 pattern).

- **`markdown-linting` uses `rumdl`, never `markdownlint-cli2`**, invoked with an always-explicit
  `--config` path — auto-discovery was measured to silently ignore config. See REQUIREMENTS.md's
  Out of Scope table for the benchmark that decided this.

---
*Roadmap created: 2026-08-18 — milestone v1.2, 8/8 v1 requirements mapped*
