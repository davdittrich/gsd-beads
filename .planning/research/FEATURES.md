# Feature Research

**Domain:** gsd-core capability plugins (PR-workflow automation, markdown-lint gating, pre-phase resource advisory)
**Researched:** 2026-08-18
**Confidence:** HIGH (pattern precedent: three shipped capabilities in this repo — `beads`, `ponytail-everywhere`, `sota-numerics` — establish binding mechanics; MEDIUM on external tool defaults, grounded via one live web search on GitHub required-checks semantics)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `pr-workflow`: `ship:pre` gate blocks on failing OR pending checks | GitHub itself treats "pending" as a hard block for required checks — a perpetually-unresolved check blocks merge exactly like a failure (confirmed via GitHub Docs). A gate that ignores pending checks would let a phase ship mid-CI-run, which is worse than no gate at all. | LOW | Gate predicate reads `gh pr checks --json` (or a generated `PR.md` artifact, matching `BEADS.md`'s shape) for a tri-state `passing/pending/failing`; both `pending` and `failing` fail the predicate, `passing` and `no-checks-configured` pass. `onError: skip` covers `gh` absent/unauthenticated/no PR. |
| `pr-workflow`: draft-PR creation is opt-in via an explicit action step, not automatic | `pr-workflow` SKILL.md's own Step 6 always creates as draft, but only after 5 prior steps (branch, commit, rebase, push) the user explicitly triggered. Auto-creating a PR as a side effect of `ship:post` on every phase would spam PRs for phases the user isn't ready to open a PR for yet, and the capability has no branch/commit-strategy awareness (that's git, out of gsd's binding model). | LOW-MED | `ship:post` step with `when: pr_workflow.autoCreateDraft` (default **false** — warn-only: print "no open PR for this branch; run `gh pr create --draft` to open one" instead of forcing a `gh pr create` call). Matches the beads/ponytail precedent of config-gated, off-by-default aggressive behavior. |
| `markdown-linting`: `verify:post` fragment reporting MD0XX violation counts | Every comparable doc-lint integration (markdownlint-cli2's own pre-commit hook, the `markdown-lint.yml` GitHub Action pattern in the SKILL.md itself) surfaces violations at the point content changes, not silently. `sota-numerics`' advisory-fragment pattern (four steering fragments, no gate) is the direct precedent for "surface, don't necessarily block." | LOW | `contributions[]` entry at `verify:post` into `verifier`, `onError: skip` — non-gate, matches N3 in `beads`' Out-of-Scope ("this capability tracks/reports, it does not decide how work is planned"). |
| `markdown-linting`: config lives in a single `.markdownlint-cli2.jsonc`, never hand-edited per rule without approval | The skill's own "CRITICAL: Configuration Policy" section — "fix content to comply with rules, not rules to accommodate content" — is the industry-standard stance (mirrored by every pre-commit-framework markdown hook: violations are the actionable signal, not a reason to relax config). | LOW | Ship a curated default `config` block (see Anti-Features below for why "all defaults" is wrong for `.planning/`), documented as the single source of truth, consistent with `beads`' single-config-namespace constraint. |
| `get-available-resources`: advisory-only, no gate | `beads.enabled` defaults false and `ponytail.enabled` defaults true, but neither ever *blocks* a lifecycle point on resource state — this class of signal (like CI runner sizing hints, `nproc`-based `make -j$(nproc)`, `pytest-xdist -n auto`) is universally advisory in comparable tooling; none of it auto-fails a build. | LOW | `contributions[]` fragment only, empty `gates[]` — matches `ponytail`'s `capability.json` shape exactly (see `.gsd/capabilities/ponytail/capability.json:83`, `"gates": []`). |
| All three: `onError: skip` on every non-gate contribution | Established, tested pattern across all three existing capabilities (`beads`, `ponytail`, `sota-numerics`) — a missing binary, absent artifact, or non-zero exit must never strand a phase. This is now house style, not optional. | LOW | Reuse verbatim; no new failure-handling design needed. |
| All three: config keys namespaced under `<id>.*` (e.g. `pr_workflow.*`, `markdown_linting.*`, `resources.*`) | `beads`' Constraints section explicitly calls out config-key collision as loader-rejected — every shipped manifest must be checked before reuse. | LOW | Trivial naming discipline, but must be verified against `beads.json`/`ponytail`/`sota-numerics` manifests before finalizing key names. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `pr-workflow`: tri-state check gate (`passing`/`pending`/`failing`) instead of the skill's binary pass/fail framing | The source SKILL.md (Step 8-9) treats CI monitoring as a live `--watch` loop inside one long-running command — wrong shape for a one-shot lifecycle gate that fires once at `ship:pre`. A tri-state predicate read from a generated `PR.md` artifact (mirroring `BEADS.md`) is more correct than either "ignore pending" or "block forever waiting." | MEDIUM | This is the single most important design improvement over the source skill: it decouples "did CI finish" (artifact staleness — regenerate `PR.md` every step, same as `BEADS.md`) from "did CI pass" (the gate predicate). |
| `markdown-linting`: curated default rule subset for `.planning/**/*.md`, not markdownlint-cli2's "all defaults true" | `.planning/` is agent-generated planning prose (PLAN.md, CONTEXT.md, ROADMAP.md), not hand-authored docs for human readers with strict style needs. Several defaults are actively hostile to this content: MD013 (line-length) fights long agent-generated bullet points and table rows; MD033 (no inline HTML) fights `<details>` collapsible sections gsd-core itself uses; MD041 (first-line-must-be-heading) fights frontmatter-led files. A curated subset (structural rules only: MD001 heading-increment, MD003 heading-style, MD009 trailing-spaces, MD012 no-multiple-blanks, MD022 blanks-around-headings, MD024 dupe-headings scoped to siblings, MD040 fenced-code-language) catches real defects without fighting the corpus. | LOW-MED | Directly disagrees with the source skill's "all defaults true, MD013 false" starting config — that config is tuned for human-authored READMEs, not machine-generated planning trees. Ship the curated list as this capability's opinionated default, adjustable via the existing `.markdownlint-cli2.jsonc` precedence the tool already supports. |
| `markdown-linting`: violation count surfaced as a number in the fragment, not the full DavidAnson rule-explanation apparatus | The skill's ~850-line document (VS Code setup, GitHub Actions integration, "intelligent fix handling" with parallel Task agents, nested-code-block backtick-counting guidance) is scoped for an interactive human-fixing-errors session, not an automated lifecycle checkpoint. | LOW | Capability wraps the CLI call and count only; it does not carry over auto-fix orchestration, VS Code integration, or the manual-fix decision tree — those stay in the interactive skill, which remains usable standalone. |
| `get-available-resources`: emits a structured recommendation object the fragment can quote verbatim, not prose the planner has to reinterpret | Matches how CI runner sizing hints work in mature tooling (e.g., GitHub Actions' `runner.os`/`ImageOS` env vars, `nproc`-based auto-parallelism in build tools) — machine-readable signal, human/agent decides. Never auto-sets a build config value in any comparable tool surveyed (CI sizing hints, `cargo build -j`, `pytest-xdist -n auto` all *read* a hint but leave the invocation to the caller). | LOW | Reuse the source skill's JSON shape (`cpu`, `memory`, `gpu`, `recommendations`) almost as-is — it's already structured correctly; strip the K-Dense upsell and the Dask/Zarr/scientific-computing library recommendations that don't apply to gsd's actual workload (agent orchestration, not dataset processing). |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|------------------|-------------|
| `pr-workflow`: auto-merge on green CI | Feels like the natural end of "automate the PR lifecycle" | `pr-workflow` SKILL.md's own Critical Rules #1 says "Never merge a PR... the user decides when to merge" — carrying this over would violate the source skill's own hardest constraint, and no CI system defaults to auto-merge without explicit opt-in (GitHub's own auto-merge is a per-PR toggle, never a repo default) | Ship-gate + report only. Auto-merge stays permanently out of scope, not "future" — it's a decision the source skill itself already made and this capability should not re-open. |
| `pr-workflow`: auto-assign-reviewers, review-thread addressing (Phase 2/3 of the source skill), thread bulk-resolution | Looks like "full lifecycle coverage" per the skill's own scope | These require live conversational judgment (categorizing threads, drafting replies, deciding what's addressed) that a lifecycle *gate/fragment* cannot exercise — a `contributions[]` fragment or `gates[]` predicate is a one-shot, non-interactive check, not an agent loop. Building this into the capability would mean embedding an agent inside a gate predicate, which is architecturally impossible in gsd-core's current gate model (predicates are `command-exists` / `artifact-frontmatter-equals` only). | Leave PR review-thread handling to the existing interactive `pr-workflow` *skill* (already installed, unaffected by this capability). The capability only wraps creation status + check status for the ship gate. |
| `pr-workflow`: `gh pr-review` extension dependency (`agynio/gh-pr-review`) | The source skill requires it for Phases 2-3 | This capability plugin only needs Phase 1's `gh pr create`/`gh pr checks`/`gh api` surface — pulling in a third-party `gh` extension as a hard dependency for functionality this capability doesn't use would violate the same "any dependency beyond the minimum" discipline `beads` holds itself to (N5: "Any dependency beyond the `bd` binary and Python 3 standard library" is explicitly out of scope for that capability) | Depend only on `gh` CLI + `gh auth status`, already a prerequisite check pattern in the source skill's own Section 1. |
| `markdown-linting`: "NO AUTOMATED SCRIPTS" / mandatory Edit-tool-per-violation manual-fix workflow, carried into the capability | The skill's philosophy is right for interactive human-in-the-loop fixing sessions | A lifecycle gate is not a fixing session — it reports a count and (optionally) blocks; it must never itself attempt fixes, scripted or manual, because a gate firing inside `verify:post`/`ship:pre` has no mandate to edit content | Capability is read-only: run `markdownlint-cli2` in check mode, report the count. Fixing (auto or manual) stays entirely in the pre-existing interactive skill, invoked by the user/agent separately if they choose. |
| `markdown-linting`: hard violation-count gate at `ship:pre`, enabled by default | Superficially mirrors `beads.ship_gate`'s pattern, and the milestone brief explicitly asks for one | Neither `markdownlint-cli2`'s own pre-commit integration nor typical doc-lint CI gates (the SKILL.md's own GitHub Actions example just runs on PR/push, no branch-protection requirement implied) default to blocking merges/ships — they default to reporting; teams opt into required-status-check enforcement deliberately, after tuning the rule-set to their corpus, because getting the config wrong (see MD013/MD033/MD041 above) produces false-positive blocks on legitimate content. Defaulting `.planning/` linting to hard-block would repeat that mistake on day one, before the curated rule-set has been validated against this repo's actual planning tree. | Ship the gate (predicate exists, `gates[]` entry present, matching the brief), but default `markdown_linting.ship_gate` to **advisory/false** — same shape as `beads.ship_gate` before it was proven, letting the user flip it to blocking once the curated rule-set has run clean against the existing `.planning/` corpus at least once. |
| `get-available-resources`: auto-setting build/parallelism config values (e.g. writing `n_jobs` into a project config file) | "Why stop at a recommendation, just apply it" | No comparable tool surveyed does this by default — GitHub Actions runner sizing, `nproc`-based `make -j`, `pytest-xdist -n auto` all *compute* a hint at invocation time and leave the decision/application to the caller (build tool flag, not a persisted config mutation). Auto-writing config also collides with `beads`' own N3 precedent ("this capability tracks work, it does not decide how work is planned") extended to compute: a resource capability should inform, not decide. | Fragment presents the recommendation object inline in planner/executor context; nothing is written back into project config. |
| `get-available-resources`: running before every `plan:pre`/`execute:wave:pre` unconditionally | Matches the milestone brief's literal ask and is the simplest to build | Genuinely useful only for compute-heavy phases (model training, large-scale parallel processing, dataset transforms) — for a typical gsd phase (editing markdown, wiring a capability manifest, writing a skill), CPU/GPU/disk detection is pure noise in the fragment and adds a subprocess call (`psutil`, `nvidia-smi`, `rocm-smi`) to every single lifecycle step for zero decision value. **Real gap, not resolved by research:** gsd-core has no phase-classification signal today (no `phase.compute_heavy: true` frontmatter, no tag surface) — there is nothing for a `when:` condition to key off. | **Scope narrowing recommendation:** ship the fragment gated on `resources.enabled` (default **false**, mirroring `beads.enabled`'s default-false precedent, not `ponytail.enabled`'s default-true) so it is opt-in per-project rather than firing unconditionally; flag the missing phase-compute-heavy signal as a real upstream gsd-core gap (candidate follow-up: a `phase.tags: [compute-heavy]` frontmatter field feeding a `when:` predicate) rather than pretending a heuristic in this capability can infer it reliably. |

## Feature Dependencies

```
pr-workflow.ship_gate (tri-state check predicate)
    └──requires──> pr-workflow.pr_status_artifact (generated PR.md, regenerated every step)
                       └──requires──> `gh` CLI present + authenticated (command-exists gate precedent from beads' `bd`-absence handling)

markdown-linting.ship_gate (violation-count gate)
    └──requires──> markdown-linting.verify_post_report (count surfaced first, non-blocking)
                       └──requires──> curated `.markdownlint-cli2.jsonc` validated clean against existing .planning/ corpus

get-available-resources.fragment
    └──enhances──> plan:pre / execute:wave:pre context (same injection points as ponytail's three fragments)
    └──conflicts (scope)──> "run on every phase" — narrowed to `resources.enabled` opt-in, no compute-heavy phase signal exists yet

All three ──require (binding pattern)──> capability-loader.cts contribution/gate mechanics already proven by beads + ponytail + sota-numerics
```

### Dependency Notes

- **`pr-workflow.ship_gate` requires a generated `PR.md` artifact:** gsd-core's gate predicates (`command-exists`, `artifact-frontmatter-equals`) never query an external tool directly — this is the same constraint `beads` documents in its Context section ("there is no predicate that queries an external tool directly, which is why the capability must project live `bd` state into a generated `BEADS.md` artifact at every step for gates to read"). `pr-workflow` must follow the identical shape: a `ship:pre` step (or `execute:wave:post`) that shells out to `gh pr checks --json`/`gh pr view --json` and writes `PR.md` frontmatter (`pr_status: passing|pending|failing|none`), then the gate reads that frontmatter via `artifact-frontmatter-equals`.
- **`markdown-linting.ship_gate` requires the report step to run first:** never gate on a value nothing has computed yet in the same lifecycle pass — mirrors `beads.ship_gate`'s dependency on `BEADS.md` regeneration "every step, never hand-edited" (B11).
- **`get-available-resources.fragment` enhances but does not gate:** no dependency chain into `gates[]` at all — this is a leaf contribution, matching `ponytail`'s `capability.json` (`"gates": []`) exactly, not `beads`' pattern.
- **All three conflict with:** inventing a second gate-enforcement mechanism outside `gates[]` (e.g., a shell script that `exit 1`s from inside a fragment, or a hook that blocks independently of the `capability.json` schema). The milestone brief's own constraint — "must not introduce a second gate-enforcement mechanism outside `gates[]`" — rules this out explicitly; all blocking behavior must flow through the declared `gates[]` array and the same `ship:pre` dispatch patch (`$HOME/.claude/gsd-core/workflows/ship.md`) that `beads` already required and shipped in Phase 3. **These three capabilities inherit that same dependency: none of their gates can fire without the machine-local `ship.md` patch already in place from `beads`' Phase 3** (or the upstream fix, open-gsd/gsd-core#3559, if merged first) — this is a hard prerequisite, not just a shared pattern.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept, dogfooded in this repo first (matching the Phase 10/11 → Phase 12 precedent).

- [ ] `pr-workflow`: `PR.md` artifact generation (status: none/passing/pending/failing) at `execute:wave:post` or `ship:pre` — essential, everything else depends on it
- [ ] `pr-workflow`: `ship:pre` gate, tri-state, `onError: skip`, default **advisory** (warn, don't block) until proven against a real PR cycle in this repo — essential to prove the artifact-gate wiring works before trusting it to block
- [ ] `pr-workflow`: `ship:post` warn-only notice when no PR exists (not auto-create) — essential, matches the source skill's own "ask before creating" spirit and avoids PR spam
- [ ] `markdown-linting`: curated rule subset `.markdownlint-cli2.jsonc`, validated clean (0 violations) against the existing `.planning/` tree before shipping the gate — essential, an unvalidated rule-set would make the gate noise from day one
- [ ] `markdown-linting`: `verify:post` violation-count report, `onError: skip` — essential, this is the report the gate later reads
- [ ] `markdown-linting`: `ship:pre` gate reading the count, default **advisory** — essential per the brief, but off-by-default per the anti-features analysis above
- [ ] `get-available-resources`: fragment at `plan:pre`/`execute:wave:pre`, `resources.enabled` default **false**, `onError: skip` — essential per the brief, but opt-in given the noise-for-non-compute-phases problem identified above

### Add After Validation (v1.x)

Features to add once core is working and the dogfooded gates have run through at least one real ship cycle each.

- [ ] `pr-workflow.ship_gate` flips to blocking-by-default — trigger: at least one real PR cycle in this repo confirms the tri-state predicate reads `PR.md` correctly and doesn't false-block on a `gh` auth hiccup
- [ ] `markdown-linting.ship_gate` flips to blocking-by-default — trigger: curated rule-set has run clean across a full milestone's worth of `.planning/` edits with zero false positives
- [ ] `get-available-resources`: `phase.tags: [compute-heavy]` frontmatter + `when:` predicate narrowing the fragment to fire only on tagged phases — trigger: gsd-core ships (or this project patches, upstream-first per N2's precedent) a phase-classification signal; until then this stays opt-in-global, not phase-scoped

### Future Consideration (v2+)

Features to defer until the above prove themselves — explicitly deferred, not silently dropped.

- [ ] `pr-workflow`: `gh pr ready` auto-promotion from draft — defer indefinitely; the source skill itself gates this on explicit user ask ("Only do this when the user explicitly asks"), a lifecycle step firing automatically would violate that
- [ ] `pr-workflow`: review-thread addressing/resolution (source skill Phases 2-3) — defer permanently to the standalone interactive skill; architecturally cannot live in a `contributions[]`/`gates[]` shape (requires conversational judgment)
- [ ] `markdown-linting`: VS Code / GitHub Actions setup automation from the source skill — defer permanently; out of a lifecycle capability's scope, stays in the interactive skill
- [ ] `get-available-resources`: GPU-backend-specific library recommendations (PyTorch-MPS, JAX-Metal, RAPIDS) — defer/drop; gsd's own workload is agent orchestration, not model training, so this part of the source skill's output is dead weight for this consumer even though harmless to keep in the JSON shape

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `pr-workflow`: `PR.md` artifact + tri-state gate (advisory default) | HIGH | MEDIUM | P1 |
| `pr-workflow`: no-PR warn-only notice | MEDIUM | LOW | P1 |
| `markdown-linting`: curated rule-set + `verify:post` report | HIGH | LOW-MEDIUM | P1 |
| `markdown-linting`: `ship:pre` gate (advisory default) | MEDIUM | LOW | P1 |
| `get-available-resources`: opt-in fragment, default off | MEDIUM | LOW | P1 |
| `pr-workflow.ship_gate` flip to blocking | HIGH | LOW (config-only) | P2 |
| `markdown-linting.ship_gate` flip to blocking | MEDIUM | LOW (config-only) | P2 |
| `get-available-resources`: compute-heavy phase tagging | MEDIUM | MEDIUM (needs upstream gsd-core signal) | P2 |
| `pr-workflow`: draft-PR auto-create | LOW | LOW | P3 |
| `pr-workflow`: review-thread automation | LOW (for a gate/fragment shape) | HIGH (needs agent loop, not a gate) | P3 (out of capability scope entirely) |
| `get-available-resources`: GPU library recommendations | LOW (wrong workload) | already built (reuse) | P3 |

**Priority key:**
- P1: Must have for launch (dogfood-ready, matches Phase 10/11 precedent)
- P2: Should have, add when validated (post-dogfood, pre-public-extraction)
- P3: Nice to have or explicitly out of scope for this capability's shape

## Competitor Feature Analysis

| Feature | GitHub branch protection (native) | pre-commit framework (markdown hooks) | Our Approach |
|---------|-----------------------------------|----------------------------------------|--------------|
| Pending-check handling | Blocks merge on pending, same as failing — but pending-forever is a known operational trap (path-filter/branch-filter misconfiguration) | N/A (pre-commit is local, synchronous — no pending state) | Tri-state gate blocks on both `pending` and `failing`; `onError: skip` prevents the "stuck pending forever" trap from stranding a phase indefinitely — a missing/stale `PR.md` degrades to skip, not an infinite block |
| Lint enforcement default | N/A | Hooks are opt-in per-repo; once installed, blocking is the whole point (that's why you installed the hook) — but rule *selection* is always curated per-repo, never "all defaults" | Curated rule subset by default (not markdownlint-cli2's `"default": true`), gate itself advisory-by-default until proven — splits the two decisions (which rules vs. do they block) that pre-commit frameworks bundle together |
| Resource sizing hints | GitHub Actions runner sizing is a labeled runner choice (`ubuntu-latest`, `ubuntu-latest-4-cores`, etc.) — a config decision the user makes, never auto-applied by CI itself | N/A | Same posture: recommendation surfaced in context, never auto-written into config; narrowed to opt-in because most gsd phases aren't compute-heavy |

## Sources

- `/home/dd/projects/gsd-beads/.planning/PROJECT.md` — existing capability precedent (`beads`, `ponytail-everywhere`, `sota-numerics`), binding mechanics (`steps[]`/`contributions[]`/`gates[]`), `onError: skip` convention, N1-N6 Out-of-Scope reasoning reused above by analogy
- `/home/dd/projects/gsd-beads/.gsd/capabilities/ponytail/capability.json` — advisory-only, zero-gate shape confirmed live (`"gates": []`, three `contributions[]` entries, all `onError: skip`)
- `/home/dd/.claude/skills/pr-workflow/SKILL.md` — source skill's own scope boundaries (never-merge, never-force-push, draft-first, Phase 2/3 review-thread handling) mined for what NOT to carry into the capability
- `/home/dd/.claude/skills/markdown-linting/SKILL.md` — source skill's configuration policy, "no automated scripts" philosophy, default rule-set (`"default": true, MD013: false`) — deliberately diverged from for `.planning/` content
- `/home/dd/.claude/skills/get-available-resources/SKILL.md` — source skill's JSON output shape and recommendation categories, reused structurally; GPU/scientific-computing recommendation content flagged as not applicable to this workload
- [GitHub Docs — Troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks) — confirms pending-vs-failing semantics (both block merge; pending-forever is a known misconfiguration trap), grounding the tri-state gate design (MEDIUM-HIGH confidence, single web search, cross-checked against multiple result snippets in the same query)

---
*Feature research for: gsd-core capability plugins — PR-workflow automation, markdown-lint gating, pre-phase resource advisory*
*Researched: 2026-08-18*
