# Project Research Summary

**Project:** gsd-beads milestone v1.2 — three new gsd-core capability plugins
**Domain:** gsd-core capability plugin architecture (pr-workflow, markdown-linting, get-available-resources)
**Researched:** 2026-08-18
**Confidence:** HIGH

## Executive Summary

This research covers three new gsd-core capability plugins intended to automate PR workflow management, enforce planning-document linting standards, and provide pre-phase resource advisory context. All three follow established precedent from shipped capabilities (beads, ponytail-everywhere, sota-numerics) and require no new runtime dependencies beyond already-available external tools (`gh` CLI, Node.js/npm for markdownlint-cli2) and Python 3 stdlib. The recommended approach uses three distinct architectural patterns (fragment-only, direct command-exit-zero gate, generated-artifact gate) based on each capability's fail-safe requirements and gate scope. Key risks cluster around lifecycle-hook integration — unattended hardware detection behaving differently than interactive skill invocation, consent-hash invalidation invalidating already-consented bundles after edits, and a critical gsd-core bug (ship:pre gate dispatch) that silently deactivates capid-aware gates on unpatched machines. All six documented pitfalls are avoidable by following tested B-series patterns from existing capabilities and confirming explicit success criteria (re-consent + live render-hooks check, not just manifest validation).

## Key Findings

### Recommended Stack

**Core technologies:**
- `gh` CLI (≥2.97.0, but any version with `pr checks --json` support works) — backs pr-workflow's PR status gate via direct `gh pr checks --json` invocation with `bucket` field tri-state normalization
- `markdownlint-cli2` (0.23.2, requires Node.js ≥20) — backs markdown-linting's `.planning/**/*.md` lint pass; single source of truth via `.markdownlint-cli2.jsonc` config, matching this repo's existing skill precedent
- Python 3 stdlib (`os`, `shutil`, `platform`, `subprocess`) — backs get-available-resources' CPU/GPU/memory/disk detection; zero new pip dependencies, matching beads' N5 constraint ("no dependency beyond bd and Python 3 stdlib")

**Development tools:**
- `gh pr checks --json` with `bucket` field (normalizes CI state to pass/pending/fail/skipping/cancel across all providers)
- `markdownlint-cli2` exit codes: 0=clean, 1=lint errors found (gate's real block signal), 2=tool/config failure
- `os.cpu_count()`, `shutil.disk_usage()`, `/proc/meminfo` (Linux), `sysctl`+`vm_stat` (macOS), `nvidia-smi`/`rocm-smi` (GPU)

**No new pip/npm packages at the capability level.** The only new dependency class is Node.js/npm as a prerequisite for markdown-linting. Both `gh` and Node+npm should degrade fail-open with one visible notice if absent, matching beads' B6 pattern.

### Expected Features

**Must have (table stakes):**
- `pr-workflow`: ship:pre gate blocks on both failing AND pending checks (GitHub treats pending as a hard block for required checks; gate must match that behavior)
- `pr-workflow`: draft-PR creation opt-in via explicit action step, not automatic (side-effect auto-PRs would spam branches not ready for PR yet)
- `markdown-linting`: verify:post fragment reports MD0XX violation counts (surface, don't necessarily block; matches sota-numerics' advisory pattern)
- `markdown-linting`: config in single `.markdownlint-cli2.jsonc`, never hand-edited per rule without approval (matches industry-standard "fix content to rules, not rules to content" stance)
- `get-available-resources`: advisory-only, zero gate (matches beads/ponytail's documented constraint: "track/report, never decide how work is planned")
- All three: `onError: skip` on every non-gate contribution (established house style across all shipped capabilities)

**Should have (competitive advantages):**
- `pr-workflow`: tri-state check gate (passing/pending/failing) instead of binary pass/fail; decouples "did CI finish" (artifact staleness) from "did CI pass" (gate predicate)
- `markdown-linting`: curated default rule subset for `.planning/**/*.md`, not markdownlint-cli2's hostile defaults (MD013 line-length, MD033 inline HTML, MD041 first-line-heading all fight agent-generated planning prose)
- `markdown-linting`: violation count surfaced as a number in fragment, not full rule-explanation apparatus
- `get-available-resources`: structured recommendation object quoted verbatim in fragment (machine-readable signal, agent decides)

**Defer (v2+):**
- `pr-workflow`: auto-merge on green CI (violates source skill's own constraint; no comparable tool defaults to auto-merge)
- `pr-workflow`: auto-assign-reviewers, review-thread addressing (requires conversational judgment incompatible with gsd-core's gate model)
- `markdown-linting`: hard violation-count gate enabled by default (correctly shipped advisory-only; hard-blocks only after corpus validation)
- `get-available-resources`: auto-setting build/parallelism config values (advisory hint only, caller decides)

### Architecture Approach

All three capabilities follow gsd-core's Loop Host Contract. Gate predicates support only `command-exit-zero` and `artifact-frontmatter-equals` (not `command-exists`). Capabilities can run external tools directly inside gates; each chooses its pattern based on fail-safe requirements.

**Three patterns:**

1. **Fragment-only, zero-gate** (get-available-resources): mirrors ponytail exactly — `contributions[]` only, `gates: []`. Purely advisory, no scripts/ or hooks/ needed.

2. **Direct command-exit-zero gate** (pr-workflow): gate runs `gh pr checks` directly; exit code is block decision. Must fail-open on "no PR found yet." No intermediate artifact; stdout/stderr tail surfaced on failure. Timeout 30s.

3. **Generated-artifact gate** (markdown-linting): mirrors beads — verify:post regenerates `.planning/LINT-REPORT.md` with YAML frontmatter (`violation_count`); ship:pre gate reads via `artifact-frontmatter-equals`. DRY because report is independently valuable.

**Major components:**
1. `capability.json` — `contributions[]`, `gates[]`, `config`, `steps[]`
2. `fragments/*.md` — literal prompt text at injection points
3. Generated artifacts (PR.md, LINT-REPORT.md) — optional, only if state reused
4. Gate scripts — run synchronously; exit code is block decision
5. Hooks — only if SessionStart behavior needed (none for these three)

### Critical Pitfalls

1. **Unpatched ship:pre gate dispatch (HIGH SEVERITY)** — Stock gsd-core only evaluates gates for capId="security" and "broken-windows"; all other `gates[]` entries invisible. This repo patched locally; upstream PR (open-gsd/gsd-core#3559) NOT confirmed merged. **How to avoid:** Confirm patch marker exists in installed workflow before trusting gates. Smoke-test gates against synthetic artifacts. Track upstream status explicitly.

2. **Consent-hash invalidation silently deactivating capability (HIGH SEVERITY)** — Any edit post-consent silently deactivates the capability. **How to avoid:** Re-run `capability install --scope project` after every bundle edit. Treat "does it actually fire?" as verification, not "did tests pass?". Bake re-consent into every plan touching bundle directories.

3. **Marketplace source type SSH default (MEDIUM SEVERITY)** — GitHub-shorthand source clones over SSH unconditionally, breaking on machines with no SSH key. **How to avoid:** Use `url` source type with explicit `https://` git URL for public-extraction phase. Test locally with HTTPS-only, no SSH key.

4. **External-tool dependencies blocking lifecycle (HIGH SEVERITY)** — `gh` and Node+`markdownlint-cli2` are new external dependencies. Naive port without beads' `onError: skip` discipline will hang or hard-fail. **How to avoid:** (1) Every step/gate declares `onError: skip`. (2) Wrapped scripts check `command -v`/`shutil.which()` first and exit with "tool absent" message. (3) Print exactly one notice per missing tool (B6 pattern). (4) `pr-workflow` additionally needs auth check: `gh auth status`.

5. **Unquoted shell invocation in gate scripts (MEDIUM SEVERITY)** — Unquoted path variables break silently; if error handling defaults to permissive, environment bugs become silent over-grants. **How to avoid:** (1) Quote every path variable (`"$VAR"`). (2) Test failure direction: bug/missing dependency must fail toward safe state. (3) Reuse test-capability-auto-install.sh template; include paths with spaces/non-ASCII/symlinks as first-class test cases.

6. **Resource detection behaving differently non-interactively (HIGH SEVERITY)** — Interactive skill has human watching for plausibility; lifecycle hook doesn't. Probe failures coerce to "0" instead of "unknown"; wrong core counts in CI silently propagate. **How to avoid:** (1) JSON schema distinguishes "0" (absent) from "unknown" (probe failed). (2) Fragment hedges "unknown" fields. (3) Test in restricted environment (container with `--cpus`, no GPU) during dogfood phase. (4) Confirm probe failure degrades to "no fragment injected," not empty JSON.

## Implications for Roadmap

Based on research, three capabilities share common dogfood-build phases (sequential, not parallel) followed by public extraction. Ordering driven by: (1) consent-hash pitfall requires re-consent after edits; (2) ship:pre gate dispatch pitfall requires explicit smoke-test; (3) external-tool degradation pitfall requires testing on clean machines.

**Correction (post-synthesis reconciliation):** the first draft of this section ordered pr-workflow
first, calling its `command-exit-zero` gate "simplest." Both ARCHITECTURE.md and FEATURES.md
independently converge on the opposite order — `command-exit-zero` is a predicate kind **no
shipped capability uses yet** (`beads`/`sota-numerics` both use `artifact-frontmatter-equals`),
making it the *less* proven mechanism, and `pr-workflow` carries the only genuinely new external
runtime dependency (`gh`, network-reachable). Reordered below to match the converging source
evidence.

### Phase 1: Dogfood get-available-resources capability

**Rationale:** Zero gates — fragment-only, structurally identical to the already-shipped
`ponytail` capability (Pattern 1). No new predicate kind, no external network dependency, no
consent/gate-dispatch risk. Lowest-risk phase; validates the three-capability build discipline
(bundle hashing, consent re-grant) before any gate is involved.

**Delivers:** `.gsd/capabilities/get-available-resources/` with capability.json (`plan:pre`,
`execute:wave:pre` contributions[], zero gates), fragments (structured recommendations, hedge
"unknown"), detect-resources.py (CPU/disk/memory/GPU detection, stdlib-only per STACK.md —
`psutil` explicitly dropped, distinguishes "0" from "unknown"), live verification (clean-machine
+ container test).

**Implements from ARCHITECTURE:** Pattern 1 (fragment-only, zero-gate, mirroring ponytail).

**Avoids:** Pitfall 4 (graceful probe failure → "unknown"), Pitfall 6 (JSON distinguishes "0"
from "unknown"; fragment hedging; sandboxed environment testing).

### Phase 2: Dogfood markdown-linting capability

**Rationale:** Reuses `beads`' own proven gate mechanism byte-for-byte — `artifact-frontmatter-equals`
against a generated `LINT-REPORT.md`, mirroring `BEADS.md`. This is the *proven* gate pattern
(shipped twice already: `beads`, and `sota-numerics`'s `plan:post` gate), so it validates the
generic `ship:pre` dispatch machinery (Pitfall 1) using a mechanism with zero open questions,
before Phase 3 attempts a genuinely new predicate kind.

**Delivers:** `.gsd/capabilities/markdown-linting/` with capability.json,
`.markdownlint-cli2.jsonc` (curated rules: MD001, MD003, MD009, MD012, MD022, MD024, MD040;
disable MD013/MD033/MD041 per FEATURES.md), `verify:post` step regenerating `LINT-REPORT.md`,
`ship:pre` gate (`artifact-frontmatter-equals`, advisory-default per FEATURES.md — no comparable
tool defaults to hard-blocking), lint-report.sh script, live verification (corpus validation
against this repo's own `.planning/` tree + re-consent).

**Implements from ARCHITECTURE:** Pattern 3 (generated-artifact gate mirroring beads),
`artifact-frontmatter-equals` predicate.

**Avoids:** Pitfall 1 (smoke-test with LINT-REPORT.md — the FIRST live proof the generic
`ship:pre` dispatch actually fires for a capId other than `security`/`broken-windows`, since
`beads`'s own gate predates and never tested that generalization), Pitfall 2 (re-consent after
config changes), Pitfall 4 (npx + shutil.which check), Pitfall 5 (explicit paths-with-spaces
tests).

### Phase 3: Dogfood pr-workflow capability

**Rationale:** Highest-risk phase, deliberately last: introduces the one genuinely new predicate
kind (`command-exit-zero`, unused by any shipped capability) AND the one genuinely new
network-dependent external tool (`gh`). Benefits from Phase 1's proven bundle-consent discipline
and Phase 2's proven generic-gate-dispatch baseline to diff against if something breaks.

**Delivers:** `.gsd/capabilities/pr-workflow/` with capability.json, `ship:pre` gate
(`command-exit-zero` running `gh pr checks`, tri-state pass/pending/fail per STACK.md's
`bucket`-field finding — block on both pending and failing), `ship:post` action (draft PR,
opt-in only, never auto-created per FEATURES.md), check-pr-status.sh script (`shutil.which("gh")`
+ `gh auth status` guard, B6 fail-open pattern), live verification (real PR against this repo).

**Implements from ARCHITECTURE:** Pattern 2 (direct `command-exit-zero` gate) — no intermediate
generated artifact required, unlike markdown-linting, since `command-exit-zero` can call `gh`
directly and surface its own stdout/stderr as the gate message.

**Avoids:** Pitfall 1 (explicit smoke-test, now against a second predicate kind), Pitfall 4
(`shutil.which` + `gh auth` check).

### Phase Ordering Rationale

- **Sequential, not parallel:** Consent-hash pitfall (Pitfall 2) and gate dispatch pitfall
  (Pitfall 1) require re-consent and live smoke-test, which serialize verification regardless of
  which capability goes first.
- **get-available-resources first:** Zero gate, zero new predicate kind, zero network dependency —
  validates the shared build/consent discipline at minimum risk.
- **markdown-linting second:** Proves the generic `ship:pre` dispatch fires for a non-`beads`
  capId using the one gate mechanism (`artifact-frontmatter-equals`) already shipped twice.
- **pr-workflow third:** Carries both open risks (new predicate kind, network-dependent tool) —
  ships last so it inherits a proven dispatch baseline to diff against, per ARCHITECTURE.md and
  FEATURES.md's independently converging recommendation.

### Research Flags

Phases likely needing deeper research:
- **Phase 3 (pr-workflow):** gate-dispatch patching status upstream — verify gsd-core#3559 merge status before kickoff; `command-exit-zero` predicate kind has no prior shipped example to copy
- **Phase 2 (markdown-linting):** `.markdownlint-cli2.jsonc` rule validation against existing `.planning/` corpus (MEDIUM confidence; likely needs one iteration)
- **Phase 1 (get-available-resources):** GPU detection cross-platform correctness under CI/container restrictions (needs sandboxed test, currently testable only on author's machine)

Phases with standard patterns (skip research):
- **Phase 2 (markdown-linting):** `artifact-frontmatter-equals` directly mirrors beads; capability.json structure is standard
- **Phase 1 (get-available-resources):** fragment contribution mirrors ponytail; zero gates/steps means no edge cases

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against official sources (cli.github.com, npm package.json, Python 3 stdlib); zero new pip/npm dependencies at capability layer confirmed |
| Features | HIGH | Grounded in beads/ponytail/sota-numerics precedent; table-stakes vs. should-have vs. defer derived from source skill and existing patterns; MEDIUM on curated rule-set (needs corpus validation in Phase 2) |
| Architecture | HIGH | Extracted directly from Loop Host Contract, gate-predicate-evaluator, and live reads of gsd-beads' shipped capabilities; correction (command-exit-zero + artifact-frontmatter-equals only) verified by reading EVALUATOR_KINDS constant |
| Pitfalls | HIGH | All six traced to real bugs (CR-01, Pitfall 1 gate dispatch, Pitfall 2 consent-hash, Pitfall 3 SSH-source, Pitfall 6 resource detection) documented in PROJECT.md or commits; MEDIUM on Pitfall 6 container behavior (community docs, not Anthropic reference) |
| **Overall** | **HIGH** | Project-specific, grounded in code reads. No generic best-practices guessing. Pitfalls documented. Only MEDIUM-confidence items (curated rules validation, CI-container hardware detection) scoped to specific phases and do not block architecture/stack decisions. |

### Gaps to Address

1. **Curated markdown rule-set validation:** Proposed structural-only rules sound in theory; MEDIUM confidence on "truly clean against .planning/ corpus." Phase 2 must run linter against current tree and hand-review violations. If corpus has violations the rules miss, iterate. **Action:** Phase 2 includes "validate rules against .planning/" task; violations either justify choices or surface missing rules.

2. **Gate dispatch upstream status:** Mitigation only complete if gsd-core#3559 merged before public extraction. Current status: "filed, not confirmed merged." **Action:** Before public-extraction phase, check PR merge status; if not merged, document patch as required manual local fix (like PROJECT.md already does) or defer public ship until upstream lands patch in released version.

3. **Hardware detection in CI/container:** HIGH on problem statement; MEDIUM on mitigation validation (tested only on bare-metal so far). Phase 3 must test in sandboxed environment before declaring success. **Action:** Phase 3 includes explicit "run detect-resources.py in container with `--cpus` limit and no GPU" test; verify JSON shows "unknown" (not 0) for GPU and shows cgroup-limited core count.

4. **Node.js prerequisite documentation:** First gsd-beads capability requiring Node.js; must document loudly. **Action:** markdown-linting's README.md prerequisites section lists Node.js ≥20 as first-class prerequisite; Phase 2 success criteria include "docs accurately reflect Node requirement."

## Sources

### Primary (HIGH confidence)
- gsd-core Loop Host Contract (`~/.claude/gsd-core/bin/lib/loop-host-contract.cjs`) — contribution injection points, agentRoles per step
- gsd-core gate-predicate-evaluator (`~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs`, EVALUATOR_KINDS constant) — supported gate kinds
- Official GitHub CLI docs (`cli.github.com/manual/gh_pr_checks`) — `gh pr checks --json` fields, exit codes
- markdownlint-cli2 npm package (npmjs.com or node_modules/) — version, Node.js ≥20 requirement
- gsd-beads shipped capabilities (`.gsd/capabilities/*/capability.json`, live reads) — precedent for shapes
- gsd-beads PROJECT.md Key Decisions table — documented pitfalls
- gsd-beads commit f706179 — marketplace source type fix

### Secondary (MEDIUM confidence)
- get-available-resources source skill SKILL.md — resource detection patterns, interactive constraints
- GitHub Docs on required checks — pending checks blocking merges

---
*Research completed: 2026-08-18*
*Ready for roadmap: yes*
