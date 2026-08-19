# Phase 13: markdown-linting capability (dogfood) - Research

**Researched:** 2026-08-18
**Domain:** gsd-core capability plugin (lifecycle gate + step), Rust-based Markdown linter (rumdl) invoked as a subprocess from a Python step script
**Confidence:** HIGH — the two riskiest unknowns (does the generic `ship:pre` dispatch actually fire for a non-`security`/`broken-windows` `capId`, and what does rumdl actually detect on this repo's own tree) were both verified this session by live execution, not by reading docs.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (existing-violation cleanup):** Bring `.planning/` (and README.md/CLAUDE.md, per D-02) to 0 violations via `rumdl --fix` (mechanical auto-fix), then spot-check the diff before committing — not a full line-by-line hand-review of every changed file. Reversible (working-tree diff).
- **D-02 (lint scope boundary):** Lint globs for v1: `.planning/**/*.md` **plus** root `README.md` and `CLAUDE.md`. `docs/` and any other markdown is excluded from v1. Reversible (config value). ROADMAP.md's success criteria only name the `.planning/` tree explicitly; since scope also includes README.md/CLAUDE.md, both must independently pass 0 violations before the gate ships, and plan verification steps must cover all three paths.
- **D-03 (LINT-REPORT.md depth):** `.planning/LINT-REPORT.md` is count-only: frontmatter (`violation_count`, timestamp, config path used) plus the standard "regenerated every step, never hand-edited" banner (matches `BEADS.md`'s established minimalism). No per-rule or per-file breakdown table in the body. Reversible.
- **D-04 (rumdl install/invocation method):** Prefer a locally-installed `rumdl` already on `PATH`. If absent, fall back to `uvx rumdl` (no persistent install). If `uvx` itself fails or is unavailable, degrade non-blocking with exactly one visible notice — composes with MDL-04's `shutil.which("rumdl")` B6 fail-open requirement: check PATH first, then attempt the `uvx` fallback, then fail open. README documents both paths; `uvx` is not the sole/primary method. Reversible (script-level detail).

### Claude's Discretion

- Exact rumdl config file location under `.gsd/capabilities/markdown-linting/` (e.g. `config/.rumdl.toml`) and its internal TOML structure.
- Whether the `verify:post` step is a Python script (beads-sync style) or another mechanism — must still produce `.planning/LINT-REPORT.md` with the frontmatter contract in D-03.
- Exact wording of the advisory ship-transcript warning naming the violation count (MDL-03, success criterion 4).

### Deferred Ideas (OUT OF SCOPE)

None raised beyond the roadmap's own v2 backlog (MDL-05, blocking gate — already tracked in REQUIREMENTS.md). Also out of scope per REQUIREMENTS.md: `markdownlint-cli2` as the engine (superseded by rumdl), `mdsmith` as the engine (non-MD0XX rule namespace), any auto-fix behavior inside the lifecycle gate itself (fixing stays in the pre-existing interactive skill), VS Code/GitHub Actions setup automation.
</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MDL-01 | Curated `rumdl` config (MD001/MD003/MD009/MD012/MD022/MD024/MD040 only; line-length/inline-HTML/first-line-heading disabled with reasons), always-explicit `--config`, 0 violations against `.planning/` (+README.md/CLAUDE.md per D-02), README documents measured detection divergence vs markdownlint-cli2 | Rule-name/TOML-syntax confirmed via official docs; MD013/MD033/MD041 identity confirmed; **live dual-tool measurement performed this session** on the real 213-file tree gives concrete, current per-rule counts (see State of the Art) — supersedes the stale REQUIREMENTS.md figure |
| MDL-02 | `verify:post` fragment/step produces `.planning/LINT-REPORT.md` with `violation_count` frontmatter, `onError: skip` | beads' `verify:post` step (`beads-status` skill → `sync.py regenerate-beads-md`) is the exact structural analog, read and quoted verbatim; JSON output parsing (`len(rumdl --output-format json array)`) verified live as the count source |
| MDL-03 | `ship:pre` gate reads violation count via `artifact-frontmatter-equals`, advisory | Generic dispatch marker's presence in the installed `ship.md` confirmed by direct read (not assumed); `gsd_run check predicate` live-tested against a synthetic `LINT-REPORT.md` at both `violation_count: 0` and `violation_count: 7` — both outcomes reproduced exactly as ROADMAP.md's success criterion 3 describes |
| MDL-04 | `rumdl` absent degrades to no-op, one visible notice, B6 pattern | `beads/scripts/sync.py`'s `bd_available()`/`NOTICE` pattern read verbatim as the template; a gap in that same precedent (leaves a stale artifact untouched) is flagged as a Pitfall, since MDL-04's success criterion explicitly forbids it here |
</phase_requirements>

## Summary

This phase has two independent risk classes, and both were resolved empirically rather than by inference. First, the generic `ship:pre` gate-dispatch patch (`<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->`) **is present** in the installed `$HOME/.claude/gsd-core/workflows/ship.md` (confirmed by direct read, lines 157–242), and a live `gsd_run check predicate` call against a synthetic `LINT-REPORT.md` reproduces exactly the satisfied/unsatisfied behavior MDL-03's success criterion demands — this de-risks the phase's hardest prerequisite before any code is written. Second, `rumdl` is already installed on this machine (v0.2.53) and a real, same-tree, same-ruleset comparison against `markdownlint-cli2` (v0.23.2, via `npx`) was run this session: on the curated 7-rule set, across the real 213-file `.planning/`+README.md+CLAUDE.md corpus, rumdl found 471 violations vs. cli2's 708 — a 33.5% aggregate miss rate, with MD001 (heading-increment) the worst offender (rumdl: 1, cli2: 15 — a 93% miss on that rule alone, closely corroborating REQUIREMENTS.md's pre-existing "MD001: 14 vs 1" figure, which is now one measurement-cycle stale). This is empirical, not textbook: the numbers the README must cite have to be re-measured at execution time (the corpus changes every session), not copied from this document or from REQUIREMENTS.md.

The capability itself is structurally a near-clone of `beads`: a `capability.json` with a `verify:post` **step** (not a `contributions[]` fragment, despite REQUIREMENTS.md's use of the word "fragment" — only `steps[]` entries have a `produces` field and can write a real file) dispatching a skill whose SKILL.md shells out to a Python script (`scripts/lint.py`, mirroring `beads/scripts/sync.py`), plus a `ship:pre` gate declaring `artifact-frontmatter-equals` against `violation_count == 0`, `blocking: false` (advisory). The one genuine structural risk requiring an explicit planning decision is a path-resolution mismatch: the generic gate evaluator (`gate-predicate-evaluator.cjs` + `findPhaseArtifact`) only resolves a declared artifact **inside `ctx.phaseDir`** (the phase's own subdirectory, e.g. `.planning/phases/13-.../`), never a literal project-root `.planning/LINT-REPORT.md` — but MDL-02's own wording names exactly that root-level path. Left unreconciled, the gate's fail-open pre-check (missing-artifact → skip silently) would make the `ship:pre` gate never fire in practice, silently defeating MDL-03's entire "first live proof" claim. The recommended fix — verified structurally sound against the same code — is to write the artifact as `{phase_dir}/{padded_phase}-LINT-REPORT.md`, exactly mirroring `BEADS.md`'s own path convention, and treat REQUIREMENTS.md's `.planning/LINT-REPORT.md` phrasing as the same kind of loose shorthand `BEADS.md` already uses (BEADS.md is also "a file under `.planning/`", just phase-scoped).

**Primary recommendation:** Clone `beads`'s `capability.json`/`scripts/sync.py`/`skills/beads-status` shape almost verbatim for `markdown-linting` — same `steps[]`+`gates[]` split, same `shutil.which()`/argv-subprocess/confined-path discipline, same phase-scoped artifact path (`{phase_dir}/{padded_phase}-LINT-REPORT.md`) — and treat the rumdl-vs-markdownlint-cli2 divergence numbers as something the execution phase must re-measure fresh (using the `--output-format json` array length as the count), not something to hardcode from this document.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Markdown linting execution (rumdl invocation, fix-application) | CLI / local tooling (not a runtime tier — this is a build/lifecycle-time capability plugin, not the application under development) | — | This project has no browser/server/API tiers of its own in scope; the "architecture" here is gsd-core's own capability-plugin lifecycle (steps/gates/contributions), analogous to a CI tool integration |
| Violation-count artifact generation (`LINT-REPORT.md`) | gsd-core `verify:post` step (Python subprocess script, dispatched via a Skill) | — | Matches `BEADS.md`'s established pattern: a step-produced, frontmatter-bearing, regenerated-every-run artifact |
| Ship-time gate evaluation | gsd-core `ship:pre` capability-gate dispatch (generic, patched into `ship.md`) | — | Reuses the exact generic dispatch loop `beads` already proved live; no new dispatch mechanism needed |
| Config/ruleset ownership | Capability-local config file (`.gsd/capabilities/markdown-linting/config/*.toml`) | — | Namespace-collision-checked `markdown-linting.*` config keys, matching every other capability in this repo |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `rumdl` | 0.2.53 installed locally this session; crates.io lists a mature history back to 2025-02-28 [VERIFIED: `rumdl --version` live output; `package-legitimacy check --ecosystem crates rumdl` → verdict `OK`] | Markdown linter/formatter (Rust, single static binary) | Chosen over `markdownlint-cli2` in REQUIREMENTS.md's own Out-of-Scope table (~80x faster per the cited benchmark, no Node≥20 dependency class); this phase does not re-litigate that choice |
| Python 3 (stdlib only) | whatever `python3` on `PATH` resolves to (confirmed present, blocked-shell-safe: subprocess calls made *inside* a Python script are not intercepted by this project's `lean-ctx` Bash-tool allowlist — only a literal top-level `rumdl ...` Bash invocation is) | `verify:post` step script (`scripts/lint.py`), argv-subprocess `rumdl` invocation, frontmatter read/write | Matches `beads/scripts/sync.py`'s N5 constraint ("stdlib-only, no dependency beyond the linted-tool binary and the Python 3 standard library") — the exact same constraint applies here |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `uv`/`uvx` | present locally (`/usr/bin/uvx`, `/usr/bin/uv`) [VERIFIED: `command -v uvx`/`uv` live] | No-persistent-install fallback runner (`uvx rumdl ...`) when `rumdl` is absent from `PATH` | D-04's second tier of the fail-open chain |

### Alternatives Considered

Already resolved and locked at the REQUIREMENTS.md level — not re-opened by this research:

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `rumdl` | `markdownlint-cli2` | Slower, adds a Node≥20 dependency class this repo has never required; **but** measurably stricter (see State of the Art) — the accepted tradeoff, disclosed per MDL-01 |
| `rumdl` | `mdsmith` (`jeduden/mdsmith`, Go) | Uses its own `MDSxxx` rule namespace, not MD0XX-compatible — defeats the "curate an MD0XX subset" requirement outright; ruled out in REQUIREMENTS.md |

**Installation** (D-04's two-tier chain — no persistent install step belongs in the plan; this is invoked at runtime by the step script):

```bash
# Tier 1 (preferred): already on PATH
rumdl check --config <path> ...

# Tier 2 (fallback, no persistent install):
uvx rumdl check --config <path> ...

# Tier 3: neither available -> exactly one visible notice, exit 0 (fail-open)
```

Other install methods exist (`cargo install rumdl`, `pip install rumdl`, `brew install rumdl`, `npm install -g rumdl`) [CITED: rumdl.dev, github.com/rvben/rumdl, live `npm view rumdl` — confidence LOW per the `webfetch` tier / MEDIUM per `websearch --verified`, see Metadata] — the README should mention these exist without presenting any of them as the primary method, per D-04.

**Version verification performed:**
- `crates.io` (the authoritative distribution — rumdl is fundamentally a Rust crate): verdict `OK`, first published 2025-02-28, 1,277 weekly downloads, repo matches `github.com/rvben/rumdl` exactly [VERIFIED: `gsd_run query package-legitimacy check --ecosystem crates rumdl`].
- `npm view rumdl` (a real, if secondary, distribution channel — not part of D-04's chain): `0.2.56`, published by `rvben <ruben.jongejan@gmail.com>` via GitHub Actions CI, matches the same repo URL [VERIFIED: live `npm view rumdl` full metadata].
- `pypi` (the channel `uvx rumdl` actually pulls from): package exists, repo URL matches, but the legitimacy seam flags it `SUS` (`too-new`, `unknown-downloads`) — see Package Legitimacy Audit below for why this is a rolling-release false positive, not a real risk signal.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `rumdl` | crates.io | ~1.5 yr (first published 2025-02-28) | 1,277/wk | `github.com/rvben/rumdl` | **OK** | Approved — authoritative cross-check |
| `rumdl` | PyPI (the D-04 `uvx` fallback channel) | flagged "too-new" by the seam | unknown (registry didn't report a download count) | `github.com/rvben/rumdl` (matches) | **SUS** | Flagged — see note below |
| `rumdl` | npm (not part of D-04's chain; informational only) | flagged "too-new" by the seam | 9,098/wk | `git+https://github.com/rvben/rumdl.git` (matches) | **SUS** | Not used by this phase's decisions — informational |

**Why the SUS verdicts are a rolling-release artifact, not a real risk signal:** `rumdl`'s PyPI/npm listings show a `publishedAt` timestamp of "minutes/hours ago" because the project's CI republishes every version tag to every registry on each release (142 versions on npm alone) — the "too-new" heuristic measures the latest version's publish time, not the package's first-appearance age. The crates.io listing (the tool's native/primary distribution, unaffected by this republish cadence in the same way) independently confirms `OK` with ~1.5 years of history and a matching repository. **Recommendation for the plan:** proceed with `uvx rumdl` as D-04 specifies, but add a `checkpoint:human-verify` task before the first `uvx rumdl` invocation is wired into the `verify:post` script, per this protocol's standard handling of a `SUS` verdict — the human check is "confirm `uvx rumdl --version` resolves to the same `rvben/rumdl` project" (one command, already demonstrated safe in this session).

**Packages removed due to `SLOP` verdict:** none.
**Packages flagged as suspicious `SUS`:** `rumdl` on PyPI (the channel `uvx` actually uses) — see above; planner must add the `checkpoint:human-verify` task before wiring the `uvx` fallback path into the script.

## Architecture Patterns

### System Architecture Diagram

```text
 gsd lifecycle event                  markdown-linting capability                    ship.md (patched)
┌──────────────────┐                 ┌─────────────────────────────┐               ┌────────────────────────┐
│                   │                 │                             │               │                        │
│  verify:post      │──dispatch────▶  │ skill: markdown-linting-    │               │                        │
│  (per phase)      │  (steps[])      │  report → scripts/lint.py   │               │                        │
│                   │                 │                             │               │                        │
└──────────────────┘                 │  1. shutil.which("rumdl")   │               │                        │
                                      │     -> found? use directly  │               │                        │
                                      │     -> else which("uvx")    │               │                        │
                                      │     -> else: 1 notice, exit0│               │                        │
                                      │  2. rumdl check --config    │               │                        │
                                      │     <cfg> --output-format   │               │                        │
                                      │     json <globs>            │               │                        │
                                      │  3. violation_count =       │               │                        │
                                      │     len(json_array)         │               │                        │
                                      │  4. write                   │               │                        │
                                      │     {phase_dir}/{padded}-   │               │                        │
                                      │     LINT-REPORT.md          │               │                        │
                                      │     (frontmatter + banner)  │               │                        │
                                      └──────────────┬──────────────┘               │                        │
                                                     │ produces                     │  ship:pre step 8:      │
                                                     ▼                              │  generic gate dispatch │
                                       {phase_dir}/{padded}-LINT-REPORT.md ────read─▶  (artifact-frontmatter- │
                                       violation_count: N                          │   equals, capId=       │
                                                                                     │   markdown-linting,    │
                                                                                     │   blocking: false)     │
                                                                                     │        │               │
                                                                                     │        ▼               │
                                                                                     │  block==true & !blocking│
                                                                                     │  -> advisory line only,│
                                                                                     │     ship proceeds      │
                                                                                     └────────────────────────┘
```

### Recommended Project Structure

```text
.gsd/capabilities/markdown-linting/
├── capability.json              # id, config keys, steps[] (verify:post), gates[] (ship:pre), contributions[] (README-hint fragment, optional)
├── config/
│   └── .rumdl.toml              # [global] enable = ["MD001","MD003","MD009","MD012","MD022","MD024","MD040"]
├── scripts/
│   └── lint.py                  # mirrors beads/scripts/sync.py: argv-subprocess, confined paths, B6 fail-open
├── skills/
│   └── markdown-linting-report/
│       └── SKILL.md             # dispatches `python3 .../scripts/lint.py verify-post <phase_dir>`, mirrors beads-status/SKILL.md
├── tests/
│   └── test_lint.py             # mirrors beads/tests/test_sync.py
└── README.md                    # documents install methods (D-04), curated ruleset + disabled-rule reasons (MDL-01), measured divergence vs markdownlint-cli2
```

### Pattern 1: Step-produced, frontmatter-bearing, regenerated-every-run artifact

**What:** A `capability.json` `steps[]` entry (NOT a `contributions[]` fragment — only `steps[]` entries carry a `produces` field) dispatches a skill at a lifecycle point; the skill shells out to a stdlib-only Python script that fully overwrites a target `.md` file's frontmatter + body every time, never merging a prior hand-edit.

**When to use:** Any lifecycle artifact whose freshness must be provable at gate-evaluation time (matches B11's discipline).

**Example — exact analog, read verbatim this session:**
```json
// Source: .gsd/capabilities/beads/capability.json (read this session, lines 114-127)
{
  "point": "verify:post",
  "ref": { "skill": "beads-status" },
  "produces": ["BEADS.md"],
  "consumes": ["UAT.md"],
  "when": "beads.enabled",
  "onError": "skip"
}
```
For `markdown-linting`, the direct analog:
```json
{
  "point": "verify:post",
  "ref": { "skill": "markdown-linting-report" },
  "produces": ["LINT-REPORT.md"],
  "consumes": [],
  "when": "markdown-linting.enabled",
  "onError": "skip"
}
```

### Pattern 2: Advisory `ship:pre` gate via `artifact-frontmatter-equals`

**What:** A `gates[]` entry with `check.predicate.kind == "artifact-frontmatter-equals"`, `blocking: false` (advisory — never halts shipping), read generically by `ship.md`'s patched dispatch loop.

**Example — exact analog, read verbatim this session (`beads`' two gates are both `blocking: true`; this phase needs `blocking: false`):**
```json
// Source: .gsd/capabilities/beads/capability.json (read this session, lines 156-170), adapted to advisory
{
  "point": "ship:pre",
  "check": {
    "predicate": {
      "kind": "artifact-frontmatter-equals",
      "artifact": "LINT-REPORT.md",
      "field": "violation_count",
      "equals": 0
    }
  },
  "when": "markdown-linting.ship_gate",
  "blocking": false,
  "onError": "skip"
}
```

### Pattern 3: B6 fail-open tool-detection

**What:** `shutil.which()` guard before any subprocess call to an external binary; absence prints exactly one notice and exits 0, never raising.

**Example — exact analog, read verbatim this session:**
```python
# Source: .gsd/capabilities/beads/scripts/sync.py (read this session, lines 85-95)
def bd_available():
    """B6/D-08 fail-open detection point: locate the binary, run one cheap read
    command. Absent, non-zero exit, or timeout all take the same "unavailable"
    path -- this function is the single point of truth for that decision."""
    if shutil.which("bd") is None:
        return False
    try:
        result = run_bd(["bd", "list", "--json", "-n", "1"])
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0
```
Adapted for `markdown-linting`'s two-tier chain (D-04):
```python
def resolve_rumdl_invocation():
    """D-04's two-tier chain: PATH first, then uvx, else None (fail-open)."""
    if shutil.which("rumdl"):
        return ["rumdl"]
    if shutil.which("uvx"):
        return ["uvx", "rumdl"]
    return None
```

### Anti-Patterns to Avoid

- **Treating REQUIREMENTS.md's word "fragment" as `contributions[]`:** MDL-02 says "A `verify:post` fragment reports the violation count" — but `contributions[]` entries in this codebase never carry a `produces` field (confirmed by reading every `contributions[]` entry in both `beads/capability.json` and `sota-numerics/capability.json` this session — all declare `"produces": []`). Only `steps[]` write real files. Use `steps[]`, not `contributions[]`, or `LINT-REPORT.md` will never actually be written.
- **Assuming a raw `script`-typed `ref` exists in `capability.json`:** it does not, in any capability read this session or in `capability-registry.cjs`'s own built-in hook definitions — only `ref.skill` and `ref.agent` are supported. The step must dispatch a Skill whose SKILL.md shells out to the Python script (exactly as `beads-status` does), not declare the script path directly in `capability.json`.
- **Placing `LINT-REPORT.md` at the literal project-root path `.planning/LINT-REPORT.md`:** see Pitfall 1 below — this breaks the generic gate's artifact resolution entirely.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown rule checking (heading increments, blank-line-around-heading, duplicate headings, fenced-code-language, trailing whitespace, multiple-blank-lines) | A custom regex-based Markdown structural linter | `rumdl` (already installed, already benchmarked against this repo's real tree) | This phase's whole point is dogfooding `rumdl`, not reimplementing linting logic; a hand-rolled equivalent would also need to be re-benchmarked from zero, discarding this session's empirical baseline |
| `ship:pre` gate dispatch for a non-`security`/`broken-windows` `capId` | A second, capability-specific patch to `ship.md` | The existing generic dispatch loop (`<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->`), already live-verified this session | `beads` already built and proved this exact mechanism; a second patch would duplicate it and risk drifting out of sync |
| Frontmatter parsing/writing for `LINT-REPORT.md` | A YAML library dependency | The same regex-based approach `sync.py` already uses (`FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)`) plus plain f-string frontmatter construction | Matches N5 (stdlib-only); the existing evaluator's `readFrontmatter` dependency already parses this exact shape correctly (confirmed via the live `gsd_run check predicate` test) |

**Key insight:** every mechanism this phase needs already has a proven, read-verbatim precedent in this exact repository (`beads`). The engineering risk here is *reconciliation* (making the literal artifact path and the "fragment" wording match the real, working machinery), not invention.

## Common Pitfalls

### Pitfall 1: `.planning/LINT-REPORT.md` (as literally named in MDL-02/ROADMAP.md) is unreachable by the generic gate evaluator

**What goes wrong:** If the `verify:post` script writes a single project-root file at `.planning/LINT-REPORT.md`, the `ship:pre` gate's `artifact-frontmatter-equals` predicate will never find it, and the gate will silently no-op (never fire), defeating MDL-03's entire "first live proof" claim — with no error, no warning, nothing in the transcript to say so.

**Why it happens:** `evaluateArtifactFrontmatterEquals` [VERIFIED: `gate-predicate-evaluator.cjs:105-146`, read this session] resolves `targetDir = ctx.phaseDir` (never the project root) and calls `deps.findPhaseArtifact(targetDir, artifactSuffix)`. `findPhaseArtifact` [VERIFIED: `check-command-router.cjs:859-889`, read this session] tries exactly three resolutions, all rooted at `phaseDir`:
1. `{phaseDir}/{artifactSuffix}` directly,
2. `{phaseDir}/.planning/{artifactSuffix}` (a nested `.planning` subfolder inside the phase dir — in practice never exists),
3. any file in `phaseDir` whose name is exactly `artifactSuffix` or ends with `-{artifactSuffix}`.

None of these three reaches a literal `{project_root}/.planning/LINT-REPORT.md` when `ctx.phaseDir` is `.planning/phases/13-markdown-linting-capability-dogfood/` (confirmed this session via `init.phase-op`). When the artifact is missing, `ship.md`'s own patched dispatch step 8(a) [VERIFIED: `ship.md:165-180`, read this session] treats a missing artifact as "not yet computed" and **skips the gate entirely** for `onError: "skip"` gates — by design, so this failure mode produces zero visible signal.

**How to avoid:** Write the artifact at `{phase_dir}/{padded_phase}-LINT-REPORT.md`, exactly mirroring `BEADS.md`'s own path (`{phase_dir}/{padded_phase}-BEADS.md`, confirmed via `sync.py:1253` read this session). This satisfies resolution path 3 above and is empirically confirmed working — the live smoke test in this session's Code Examples used exactly this shape and both the satisfied and unsatisfied cases evaluated correctly. Treat REQUIREMENTS.md's `.planning/LINT-REPORT.md` phrasing the same way `BEADS.md` is colloquially "a file under `.planning/`" — phase-scoped, not root-singleton.

**Warning signs:** A `ship:pre` run that never prints any `markdown-linting` advisory line at all, even when `LINT-REPORT.md`'s `violation_count` is nonzero — silence where MDL-03 success criterion 4 demands a visible warning is the tell.

### Pitfall 2: rumdl's own "0 violations" is not proof of a clean tree — measured 33.5% aggregate miss rate vs. markdownlint-cli2 on this exact ruleset

**What goes wrong:** Someone reads MDL-01's "0 violations" success criterion and treats a clean `rumdl check` run as equivalent to a clean tree. It is not, and the gap is large enough to matter (worst case measured: 93% of MD001 violations missed).

**Why it happens:** Empirically measured this session, same 213-file tree (`.planning/**/*.md` + `README.md` + `CLAUDE.md`), same curated 7-rule allowlist, both tools:

| Rule | rumdl 0.2.53 | markdownlint-cli2 0.23.2 | rumdl miss rate |
|------|-------------:|-------------------------:|-----------------:|
| MD001 (heading-increment) | 1 | 15 | 93.3% |
| MD003 (heading-style) | 0 | 0 | — |
| MD009 (no-trailing-spaces) | 2 | 2 | 0% |
| MD012 (no-multiple-blanks) | 2 | 2 | 0% |
| MD022 (blanks-around-headings) | 366 | 582 | 37.1% |
| MD024 (no-duplicate-heading) | 1 | 8 | 87.5% |
| MD040 (fenced-code-language) | 99 | 99 | 0% |
| **Total** | **471** | **708** | **33.5%** |

Both tools were run this session with an identical rule-allowlist (rumdl: `[global] enable = [...]` TOML; cli2: `"default": false` + explicit `true` per rule), against the identical file set, from the identical repo state. rumdl's single MD001 hit is at `06-REVIEWS.md:27`; cli2's 15 hits include locations rumdl reports zero violations for, including **this very phase's own `13-CONTEXT.md:23`** (`## Implementation Decisions` → `### Existing-violation cleanup` skip-level issue that cli2 catches and rumdl does not). REQUIREMENTS.md's pre-recorded figure ("45% miss rate, MD001: 14 vs 1") is close to but not identical to this session's numbers (15 vs 1, not 14 vs 1) — the underlying `.planning/` corpus changes every session (this phase's own `13-CONTEXT.md` is new since that figure was recorded), so the numbers drift.

**How to avoid:** MDL-01's README disclosure must be **re-measured at execution time**, immediately before the README is finalized — do not copy either this document's numbers or REQUIREMENTS.md's numbers verbatim into the README; both will be stale by then. Script the comparison (both tools, `--output-format json`, curated rule allowlist) as a one-off verification step in the plan, not a manual eyeball.

**Warning signs:** A README that cites "45%" or "14 vs 1" without a fresh `generated_at`/measurement-date stamp next to it.

### Pitfall 3: The "regenerated every step, never hand-edited" banner has no literal precedent text to copy

**What goes wrong:** D-03 says `LINT-REPORT.md` should carry "the standard 'regenerated every step, never hand-edited' banner (matches `BEADS.md`'s established minimalism)" — implying `BEADS.md` contains this literal sentence somewhere. It does not.

**Why it happens:** `regenerate_beads_md` [VERIFIED: `sync.py:1192-1257`, read this session, full function body] constructs `BEADS.md`'s body as exactly `f"# BEADS.md: {phase_dir.name}\n\n{table}\n"` — no banner sentence anywhere in the generated text. The phrase "regenerated every step, never hand-edited" is **B11**, a named engineering *principle* documented in `PROJECT.md` (`- ✓ **B11**: `BEADS.md` is regenerated every step, never hand-edited — Phase 2`) [VERIFIED: `PROJECT.md:30`, read this session], not literal in-file content.

**How to avoid:** The plan must decide explicitly: either (a) add a genuinely new literal banner line to `LINT-REPORT.md`'s body (e.g. `> Regenerated every step. Do not hand-edit.`) since none exists to copy, or (b) reinterpret D-03 as "follow the same regeneration discipline as B11", with no literal text requirement. Given MDL-02's success criterion explicitly says the file "carries the ... banner", (a) is the safer literal reading — but this is a genuine gap between the locked decision's wording and the actual precedent it cites, worth flagging to the user/planner rather than silently picking one.

### Pitfall 4: The referenced `mempalace` capability.json precedent does not exist in this repository

**What goes wrong:** CONTEXT.md's canonical_refs names `.gsd/capabilities/mempalace/capability.json` as "the closest shipped analogue for shape and degrade-cleanly behavior" to read before implementing.

**Why it happens:** `.gsd/capabilities/` in this repo contains exactly three capability directories: `beads`, `ponytail`, `sota-numerics` [VERIFIED: `ls .gsd/capabilities/`, run this session] — no `mempalace` directory exists anywhere in this repository or on the local filesystem search performed this session. `mempalace` is referenced only as an *external* agent name (`gsd-mempalace-curator`) inside the installed, machine-local `ship.md` and `capability-registry.cjs` (gsd-core's own built-in hooks) — it is not a capability shipped or dogfooded inside this repo.

**How to avoid:** Use `beads` as the actual structural analog (as this document does throughout) — it is real, in-repo, and read verbatim this session. Flag the `mempalace` reference to the user as likely a stale cross-reference in CONTEXT.md rather than chasing a file that does not exist.

### Pitfall 5: Naively porting `beads`' tool-absence handling leaves a stale `LINT-REPORT.md` — violates MDL-04's own success criterion

**What goes wrong:** `beads`' own `regenerate_beads_md` [VERIFIED: `sync.py:1197-1208`, read this session], on `bd` unavailability, prints the notice, appends a `STATE.md` blocker, and **returns without touching `BEADS.md` at all** — the previous file (however old) is left exactly as-is. Porting this pattern verbatim for `markdown-linting` would leave a `LINT-REPORT.md` with a stale (possibly `violation_count: 0`) frontmatter value, which the advisory `ship:pre` gate would then read as "clean" — silently misrepresenting a run where rumdl never actually executed. MDL-04's success criterion 5 explicitly forbids this ("no stale `LINT-REPORT.md` presented as current").

**Why it happens:** `beads`' precedent optimizes for "never lie about `bd`'s live state by regenerating from stale data" — but that precedent assumes the *previous* file is still meaningfully accurate until a real sync happens, which is a reasonable assumption for `bd`'s issue-tracking data. It is not a reasonable assumption for a lint count, where "the tool couldn't run this time" is itself the information that must be surfaced.

**How to avoid:** On the tool-absent path, still rewrite `LINT-REPORT.md`'s frontmatter — do not leave the file untouched. Recommended minimal shape (still compatible with D-03's count-only minimalism): set `violation_count` to a sentinel that cannot equal `0` by the predicate's strict-equality semantics (e.g. omit the field, or set it to a non-zero-like value/string), so the advisory gate's `artifact-frontmatter-equals` naturally reports `block: true` with a "could not verify" message rather than a false "0 violations" pass. This is a **deliberate divergence from the `beads` precedent**, not a bug in the plan — flag it as such in the capability's code comments so a future editor does not "fix" it back to match `beads`.

### Pitfall 6: `--fix` lives on the `check` subcommand, not as a bare top-level flag

**What goes wrong:** D-01 says "via `rumdl --fix`" — read literally, that is not a valid invocation.

**Why it happens:** Confirmed via live `rumdl check --help` [VERIFIED: live execution, v0.2.53] — `-f, --fix` is an option of the `check` subcommand (`rumdl check --fix --config <path> <paths>`), not a standalone top-level flag. There is also a separate `rumdl fmt` command with different exit-code semantics (`fmt` always exits 0; `check --fix` exits 1 if unfixable issues remain).

**How to avoid:** Use `rumdl check --fix --config <path> <curated globs>` for the D-01 cleanup task. This session's live run confirms 470 of 471 current violations are auto-fixable this way; the remaining 1 (the `06-REVIEWS.md:27` MD001 heading-increment) requires a human judgment call about the intended heading level and is exactly the kind of thing D-01's "spot-check the diff" step exists to catch.

## Code Examples

### rumdl curated config (TOML) — verified working shape

```toml
# Source: rumdl.dev/global-settings/ [CITED], syntax confirmed working via live
# execution this session against the real .planning/ tree (471 violations found,
# matching the expected curated-rule scope — MD013/MD033/MD041 correctly excluded).
[global]
enable = ["MD001", "MD003", "MD009", "MD012", "MD022", "MD024", "MD040"]
```

MD013 = line-length, MD033 = inline-HTML, MD041 = first-line-heading [CITED: rumdl.dev/global-settings/ and rumdl.dev/rules/] — these three are the ones MDL-01 requires be named with reasons in the README; they are implicitly excluded by the `enable` allowlist above (everything not listed is off), so the README's job is to explain *why*, not to add a redundant `disable = [...]` line.

### Violation-count extraction — verified live shape

```python
# Verified this session: `rumdl check --config <path> --output-format json <paths>`
# emits a flat JSON array, one object per violation, with keys:
# file, line, column, rule, message, severity, fixable, fix.
# len(array) IS the violation count -- no text-parsing of the human-readable
# "Issues: Found N issues in M/T files" summary line needed.
import json, subprocess

def count_violations(config_path, targets, rumdl_argv):
    args = rumdl_argv + ["check", "--config", config_path, "--output-format", "json"] + targets
    r = subprocess.run(args, capture_output=True, text=True, timeout=60)
    if r.returncode == 2:
        raise RuntimeError(f"rumdl config/runtime error: {r.stderr}")
    return len(json.loads(r.stdout))
```

### Live `gsd_run check predicate` smoke test — MDL-03 success criterion 3, reproduced this session

```bash
# Satisfied case (violation_count: 0)
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}' \
    --phase-dir <synthetic-phase-dir-containing-13-LINT-REPORT.md-with-violation_count:0> \
    --phase-number "13" --raw
{
  "block": false,
  "message": "Frontmatter field \"violation_count\" matches expected value (0)",
  "details": { "kind": "artifact-frontmatter-equals", "match": true }
}

# Unsatisfied case (violation_count: 7)
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}' \
    --phase-dir <same dir, violation_count now 7> \
    --phase-number "13" --raw
{
  "block": true,
  "message": "Frontmatter field \"violation_count\" in LINT-REPORT.md is 7, expected 0",
  "details": { "kind": "artifact-frontmatter-equals", "match": false, "actual": "7", "expected": 0 }
}
```
Both outcomes were produced by real execution this session, against a synthetic file named `13-LINT-REPORT.md` inside a scratch directory passed as `--phase-dir` — confirming resolution path 3 of `findPhaseArtifact` (suffix match) works for this exact naming convention. This IS the MDL-03/Pitfall-1 smoke test the roadmap's success criterion 3 describes; the plan's own verification task should re-run it inside the real phase directory once the capability is wired up.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `markdownlint-cli2` as the intended engine | `rumdl` | 2026-08-18, per REQUIREMENTS.md's own last-updated note, following a real head-to-head benchmark | Faster, single-binary, but measurably less strict (33.5% aggregate miss on the curated ruleset, measured fresh this session) — the tradeoff REQUIREMENTS.md already accepted, now with current numbers to cite |

**Not deprecated, still current:** `rumdl`'s `--output-format json` shape and `-c/--config` flag are stable per the live `--help` output this session (v0.2.53) and match the documented CLI reference [CITED: rumdl.dev/usage/cli/] with one correction: the docs page fetched this session claimed `--statistics` was undocumented, but the live binary's own `--help` confirms it exists (`--statistics: Show statistics summary of rule violations`) — trust the live `--help` output over the fetched docs page where they disagree.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `.gsd/capabilities/markdown-linting/` is the correct directory root for the new capability (matching `beads`'/`sota-numerics`' sibling layout) | Architecture Patterns | Low — directly observed sibling pattern, only the exact directory name (`markdown-linting` vs. some other slug) is unconfirmed against any written convention doc |
| A2 | The `checkpoint:human-verify` task the planner adds for the PyPI `SUS` verdict is sufficient mitigation, vs. e.g. pinning a specific rumdl version hash | Package Legitimacy Audit | Low-medium — if `rvben/rumdl`'s PyPI publish pipeline were ever compromised, a human eyeballing `--version` output would not catch a supply-chain substitution; pinning is stronger but out of scope for what D-04 asked for |
| A3 | Other install methods (cargo/pip/brew/npm) mentioned in the README per D-04 are accurately described — sourced via `WebFetch`, tier LOW per `classify-confidence --provider webfetch`, not independently re-verified against each registry beyond crates/npm/pypi already checked | Standard Stack | Low — these are documentation-only mentions, not load-bearing for any gate logic; wrong wording here does not break MDL-01..04 |

## Open Questions

1. **Root-level vs. phase-scoped `LINT-REPORT.md` — needs an explicit planning decision, not a silent pick**
   - What we know: the generic gate evaluator can only resolve an artifact inside `phaseDir` (Pitfall 1); `BEADS.md`'s own precedent is phase-scoped.
   - What's unclear: whether the user's locked MDL-02 wording (`.planning/LINT-REPORT.md`, project-root) was intentional (e.g., because lint scope spans the whole tree, not just the current phase) or just loose phrasing matching `BEADS.md`'s own colloquial naming.
   - Recommendation: plan for `{phase_dir}/{padded_phase}-LINT-REPORT.md` (matches the proven-working mechanism) and surface this exact reconciliation to the user during plan review, since it is a locked-decision-adjacent wording gap, not a pure implementation detail.

2. **The literal banner text for `LINT-REPORT.md` (Pitfall 3)**
   - What we know: `BEADS.md` has no literal "regenerated every step, never hand-edited" sentence in its body; B11 is a principle-name, not file content.
   - What's unclear: whether D-03 wants new literal text added, or just the same regeneration discipline.
   - Recommendation: add a one-line literal banner (option (a) in Pitfall 3) — cheapest way to satisfy MDL-02's literal "carries the ... banner" success-criterion wording without inventing new scope.

3. **Exact README wording for the divergence disclosure**
   - What we know: this session's fresh measurement (471 vs. 708, 33.5% aggregate) is more current than REQUIREMENTS.md's recorded figure (45%, MD001 14 vs 1), but both were run against a moving corpus.
   - What's unclear: whether the README should cite a specific numeric snapshot (frozen at whatever the corpus looks like when the README is finalized) or describe the divergence qualitatively with a "measured at commit X" pointer.
   - Recommendation: cite numbers with an explicit measurement-date/commit-sha caveat, generated by the same comparison script the plan should build as part of MDL-01's verification task (not hand-typed).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `rumdl` | Core linting | ✓ | 0.2.53 | `uvx rumdl` (D-04 tier 2) |
| `uvx`/`uv` | D-04 fallback tier | ✓ | present at `/usr/bin/uvx`, `/usr/bin/uv` | — |
| `python3` | `verify:post` step script | ✓ | present at `/usr/bin/python3` | — |
| `bd` | Existing `beads` capability this phase composes alongside | ✓ | present | — |
| `gh` | Ship-time preflight (unrelated to this phase, already required by `ship.md`) | ✓ | present | — |
| `markdownlint-cli2` (via `npx`) | One-off comparison measurement for the README's divergence disclosure — NOT a runtime dependency of the shipped capability | ✓ (via `npx --yes`, no persistent install) | 0.23.2 | Not required at runtime; only needed when re-measuring the divergence figure |

**Missing dependencies with no fallback:** none — every dependency this phase needs is present on this machine.

**Note on this session's shell sandbox:** a raw top-level `rumdl ...` Bash-tool invocation is blocked by this project's `lean-ctx` shell allowlist policy (`~/.config/lean-ctx/config.toml`) — confirmed this session (`rumdl --version` as a direct Bash command was rejected with exit 126). This does **not** affect the actual capability: a `subprocess.run(["rumdl", ...])` call made *from inside* a Python script invoked as `python3 lint.py` is not intercepted (confirmed working this session, and is exactly the architecture `scripts/lint.py` will use, mirroring `sync.py`'s existing `subprocess.run(["bd", ...])` pattern). No action needed, but worth knowing if a future debugging session sees a confusing "rumdl blocked" error that only reproduces via a *direct* Bash call, not via the real script.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` (matches `beads/tests/test_sync.py`'s existing convention — no new framework needed) |
| Config file | none dedicated; reuse whatever `pytest` config (if any) already governs `.gsd/capabilities/beads/tests/` |
| Quick run command | `python3 -m pytest .gsd/capabilities/markdown-linting/tests/test_lint.py -x` |
| Full suite command | `python3 -m pytest .gsd/capabilities/markdown-linting/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MDL-01 | curated config produces 0 violations on the real tree | integration (real subprocess against fixture files) | `python3 -m pytest .gsd/capabilities/markdown-linting/tests/test_lint.py::test_curated_config_zero_violations -x` | ❌ Wave 0 |
| MDL-02 | `LINT-REPORT.md` frontmatter `violation_count` matches a hand-run count | integration | `python3 -m pytest .gsd/capabilities/markdown-linting/tests/test_lint.py::test_report_matches_handrun_count -x` | ❌ Wave 0 |
| MDL-03 | `ship:pre` gate evaluates satisfied/unsatisfied via `gsd_run check predicate` | manual/live smoke test (see Code Examples — already reproduced once this session; the plan's verification task should re-run it against the real capability, not a hand-built predicate JSON) | N/A — this is inherently a live-tool smoke test, not a unit test | ❌ Wave 0 |
| MDL-04 | `rumdl` absent -> exactly one notice, exit 0, no stale report | unit (mock `shutil.which` to return `None` for both `rumdl`/`uvx`) | `python3 -m pytest .gsd/capabilities/markdown-linting/tests/test_lint.py::test_tool_absent_fail_open -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest .gsd/capabilities/markdown-linting/tests/test_lint.py -x`
- **Per wave merge:** full suite command above
- **Phase gate:** full suite green, plus a real (non-mocked) `gsd_run check predicate` smoke test against the actual generated `LINT-REPORT.md`, before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `.gsd/capabilities/markdown-linting/tests/test_lint.py` — covers MDL-01, MDL-02, MDL-04
- [ ] `.gsd/capabilities/markdown-linting/tests/fixtures/` — small synthetic `.md` fixtures with known violation counts (mirrors `beads/tests/fixtures/plan-*.md`), so unit tests don't depend on the live `.planning/` tree's ever-changing content
- [ ] Framework install: none — `pytest` presence should be confirmed the same way `beads/tests/` already assumes it (no new install step identified as missing)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Every `rumdl`/`uvx` invocation is an argv list passed to `subprocess.run([...])` with shell execution left at its disabled default — mirrors `sync.py`'s own documented T-01-01 threat closure (module docstring, read this session: "no `bd` command is ever assembled as a shell string"). The same discipline applies to `rumdl` argv construction |
| V12 Files and Resources (path handling) | yes | Reuse `sync.py`'s `confined()`/`find_project_root()` pattern (read this session, lines 116-139) to keep every path this new script reads or writes confined to the resolved project root — same T-01-02 threat class |
| V2/V3/V4/V6 (auth/session/access-control/crypto) | no | This capability has no auth, session, or crypto surface — it shells out to a local linter and writes a local file |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Argv injection via filenames/paths fed into `rumdl`/`uvx` subprocess calls | Tampering | argv-list `subprocess.run`, never a shell string (matches T-01-01 precedent) |
| Path traversal via a maliciously-named artifact suffix or glob result | Tampering | `confined()`-style path validation before any read/write (matches T-01-02 precedent); note the generic evaluator's own `findPhaseArtifact` already rejects any `artifactSuffix` containing path separators [VERIFIED: `check-command-router.cjs:862-867`] |
| Supply-chain substitution of the `rumdl` binary via a compromised PyPI publish | Tampering / Spoofing | `checkpoint:human-verify` before wiring the `uvx` fallback (Package Legitimacy Audit); prefer the PATH-installed tier when available, since that install path is under the operator's own control |

## Sources

### Primary (HIGH confidence — live execution / direct file reads this session)

- `.gsd/capabilities/beads/capability.json` — full file read, `steps[]`/`gates[]`/`contributions[]` shape
- `.gsd/capabilities/sota-numerics/capability.json` — full file read, alternate gate shape (`command-exit-zero`), confirms `contributions[]` never has `produces`
- `.gsd/capabilities/beads/scripts/sync.py` — `bd_available()`, `regenerate_beads_md()`, `check_shipmd_patch()`, `confined()`/`find_project_root()` read in full
- `.gsd/capabilities/beads/skills/beads-status/SKILL.md` — full lifecycle-point dispatch logic read
- `.gsd/capabilities/beads/GSD-CORE-PATCH.md` — full patch-history document read
- `$HOME/.claude/gsd-core/workflows/ship.md` — full file read; generic dispatch marker confirmed present at lines 157-242
- `$HOME/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs` — full file read
- `$HOME/.claude/gsd-core/bin/lib/check-command-router.cjs` (`findPhaseArtifact`, `buildPredicateDeps`) — read in full
- `$HOME/.claude/gsd-core/bin/lib/security.cjs` (`validatePath`) — read in full
- Live `gsd_run check predicate` execution — synthetic satisfied/unsatisfied smoke test reproduced
- Live `rumdl 0.2.53` execution (`--version`, `check --help`, `init --help`, real run against the 213-file corpus, `--output-format json` shape)
- Live `npx markdownlint-cli2@0.23.2` execution — real run against the identical corpus with an equivalent curated ruleset
- `gsd_run query package-legitimacy check` (crates/pypi/npm) and `gsd_run query classify-confidence` — live seam calls
- `.planning/PROJECT.md`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/config.json` — read directly

### Secondary (MEDIUM confidence — `websearch --verified`)

- WebSearch summaries of rumdl CLI flags/exit codes — cross-checked against and largely confirmed by the live `--help` output above (one correction noted: `--statistics` does exist, contrary to an earlier fetched-docs claim)

### Tertiary (LOW confidence — `webfetch`, per the `classify-confidence` seam)

- `rumdl.dev/usage/cli/`, `rumdl.dev/global-settings/`, `rumdl.dev/rules/`, `github.com/rvben/rumdl` — fetched and summarized; treated as `[CITED]` in-text but tier LOW per this project's `classify-confidence --provider webfetch` seam output, superseded by live `--help` output wherever the two disagreed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — rumdl version, install methods, and CLI contract all confirmed by live execution, not just docs
- Architecture: HIGH — every pattern claimed has a verbatim, line-cited source read this session; the one genuine open item (LINT-REPORT.md path) is flagged, not silently resolved
- Pitfalls: HIGH — all six are grounded in either live execution or direct source reads, not inference from documentation

**Research date:** 2026-08-18
**Valid until:** ~7 days for the specific violation-count numbers (the `.planning/` corpus changes every session; treat State of the Art's table as a snapshot, not a fact to hardcode) — 30 days for the architectural/mechanism findings (capability.json shape, gate evaluator behavior), which are code-level and change only on a `gsd-core` update.
