# Requirements: gsd-beads — Milestone v1.2

**Defined:** 2026-08-18
**Core Value:** gsd's lifecycle writes to and reads from `bd` exclusively for task state; zero
duplicated task-state bookkeeping survives in `.planning/`.

## v1 Requirements

Two new gsd-core capability plugins, each dogfooded in this repo then extracted to its own
public GitHub repo and marketplace entry, following the proven Phase 10/11 → Phase 12 pattern
already shipped for `ponytail-everywhere` and `sota-numerics`. `get-available-resources` (a
third candidate surfaced during scoping) is explicitly deferred — see Out of Scope.

### PR-WORKFLOW

- [ ] **PRW-01**: A `PR.md` artifact is generated at `execute:wave:post` reporting PR status
      (`none`/`passing`/`pending`/`failing`), regenerated every step — mirrors `BEADS.md`'s
      "regenerated every step, never hand-edited" discipline (B11), required because gsd-core's
      gate predicates cannot query `gh` directly

- [ ] **PRW-02**: A `ship:pre` gate reads `PR.md`'s frontmatter via `artifact-frontmatter-equals`,
      tri-state (blocks on both `pending` and `failing`, matching GitHub's own required-check
      semantics), `onError: skip`, default **advisory** (warn, don't block) until proven against
      a real PR cycle in this repo

- [ ] **PRW-03**: `ship:post` prints a warn-only notice when no open PR exists for the current
      branch — never auto-creates one (matches the source `pr-workflow` skill's own "ask before
      creating" spirit; avoids PR spam)

- [ ] **PRW-04**: `gh` absent or unauthenticated degrades to a no-op with one visible notice
      (B6's fail-open pattern, `shutil.which("gh")` + `gh auth status` guard)

### MARKDOWN-LINTING

- [ ] **MDL-01**: A curated `rumdl` config (MD001/MD003/MD009/MD012/MD022/MD024/MD040-equivalent
      rules only — structural rules; line-length/inline-HTML/first-line-heading explicitly
      disabled, they fight `.planning/`'s frontmatter-led, agent-generated, `<details>`-using
      content) is invoked with an always-explicit `--config` path (rumdl's config auto-discovery
      was measured to silently ignore `.markdownlint-cli2.jsonc` otherwise), validated at 0
      violations against this repo's own `.planning/` tree before the gate ships. The plugin's
      own README documents rumdl's measured detection-logic divergence from markdownlint-cli2 on
      this exact ruleset (45% miss rate measured in this repo, e.g. MD001: 14 vs 1) as a known,
      accepted behavior difference — not silently glossed over

- [ ] **MDL-02**: A `verify:post` fragment reports the violation count, `onError: skip`
- [ ] **MDL-03**: A `ship:pre` gate reads the violation count via `artifact-frontmatter-equals`,
      default **advisory** (no comparable tool defaults to hard-blocking on install; teams opt
      into required-status-check enforcement after tuning)

- [x] **MDL-04**: `rumdl` absent degrades to a no-op with one visible notice (B6 pattern,
      `shutil.which("rumdl")`) — single static binary (`uvx`/`pip`/`cargo`/`brew`-installable),
      introduces no Node/npm dependency class, unlike the markdownlint-cli2 alternative

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Ship Gate Maturity

- **PRW-05**: `pr-workflow.ship_gate` flips to blocking-by-default — trigger: at least one real
  PR cycle in this repo confirms the tri-state predicate reads `PR.md` correctly and doesn't
  false-block on a `gh` auth hiccup

- **MDL-05**: `markdown-linting.ship_gate` flips to blocking-by-default — trigger: curated
  rule-set has run clean across a full milestone's worth of `.planning/` edits with zero false
  positives

### get-available-resources

- **RES-01**: Fragment-only advisory capability (CPU/GPU/memory/disk, stdlib-only detection —
  `psutil` explicitly excluded per N5-style dependency discipline) at `plan:pre`/
  `execute:wave:pre`, zero gates, mirroring `ponytail`'s pattern

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| `get-available-resources` capability | Deferred, not cut — FEATURES.md flagged a real gap: gsd-core has no "this phase is compute-heavy" signal today, so nothing would consume the advisory automatically yet. Build it once that signal exists, not before (user decision, 2026-08-18) |
| `pr-workflow`: auto-merge on green CI | Violates the source skill's own hardest constraint ("never merge a PR, the user decides"); no CI system defaults to auto-merge without explicit opt-in |
| `pr-workflow`: auto-assign-reviewers, review-thread addressing/resolution | Requires live conversational judgment a one-shot `gates[]`/`contributions[]` predicate architecturally cannot exercise; stays in the existing interactive `pr-workflow` skill |
| `pr-workflow`: `gh pr-review` extension dependency | Only needed for review-thread automation, which is out of scope; this capability depends on `gh` CLI only |
| `pr-workflow`: draft-PR auto-create on `ship:post` | Would spam PRs for phases the user isn't ready to open one for; capability has no branch/commit-strategy awareness (that's git, out of gsd's binding model) |
| `markdown-linting`: `markdownlint-cli2` as the linting engine | Superseded by `rumdl` after a real head-to-head benchmark (2026-08-18): ~80x faster, single static binary vs. a new Node≥20 dependency class this repo has never required. Accepted tradeoff: rumdl's 45% detection-logic gap on the curated ruleset vs. markdownlint-cli2, documented in the plugin's own README rather than silently accepted |
| `markdown-linting`: `mdsmith` as the linting engine | Ruled out — real project (`jeduden/mdsmith`, Go) but uses its own `MDSxxx` rule namespace, not MD0XX-compatible, defeating the "curate an MD0XX subset" requirement outright; 12-star early-stage adoption. (Note: `npm mdsmith` is an unrelated README-generator by a different author — a real name-collision trap, not the linter) |
| `markdown-linting`: "NO AUTOMATED SCRIPTS" manual-fix workflow from the source skill | A lifecycle gate reports and (optionally) blocks; it must never itself attempt fixes — fixing stays in the pre-existing interactive skill |
| `markdown-linting`: VS Code / GitHub Actions setup automation from the source skill | Out of a lifecycle capability's scope; stays in the interactive skill |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MDL-01 | Phase 13 | Gaps Found |
| MDL-02 | Phase 13 | Gaps Found |
| MDL-03 | Phase 13 | Gaps Found |
| MDL-04 | Phase 13 | Complete |
| PRW-01 | Phase 14 | Pending |
| PRW-02 | Phase 14 | Pending |
| PRW-03 | Phase 14 | Pending |
| PRW-04 | Phase 14 | Pending |

**Coverage:**

- v1 requirements: 8 total
- Mapped to phases: 8 ✓
- Unmapped: 0

Phase 15 (public extraction of both plugins) carries no requirement IDs of its own — it delivers
PROJECT.md's stated v1.2 milestone goal ("extracted to its own public GitHub repo and marketplace
entry"), following Phase 12's extraction playbook (D-01..D-10). This mirrors the Phase 10/11 →
Phase 12 precedent, where dogfood-build and public-extraction were separate, requirement-free
phases.

---
*Requirements defined: 2026-08-18*
*Last updated: 2026-08-18 after initial definition — markdown-linting's engine changed from
markdownlint-cli2 to rumdl following a real, sandboxed head-to-head benchmark against this
repo's own `.planning/` tree; get-available-resources scoped out to v2 pending a
compute-heavy-phase signal in gsd-core.*
