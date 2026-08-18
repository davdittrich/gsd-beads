# Phase 14: pr-workflow capability (dogfood) - Research

**Researched:** 2026-08-18
**Domain:** gsd-core lifecycle capability plugin; `gh` CLI PR-check status shelled out to a
gate-readable artifact
**Confidence:** HIGH (gh CLI behavior verified live against installed `gh 2.97.0` and against
`cli/cli`'s own `v2.97.0` source tree; gsd-core gate-evaluator behavior verified by reading the
installed `gate-predicate-evaluator.cjs`/`check-command-router.cjs` this session)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `gh pr checks` results roll up into the four-state `pr_status` value with
  precedence **failing > pending > passing**: any `FAILURE`/`ERROR` check anywhere → `failing`;
  else any `PENDING`/`IN_PROGRESS`/`QUEUED` check → `pending`; else all `SUCCESS` (including the
  case of zero checks configured on an otherwise-open PR) → `passing`. Matches GitHub's own
  required-check semantics and `gh pr checks`' own exit-code precedence. — Reversibility:
  reversible — rollup logic is a pure function inside the step script, not a stored contract.
  "zero checks configured" is `passing`, not `none` — `none` is reserved for "no open PR exists
  for this branch" (PRW-03), keeping the two failure modes (no CI vs no PR) distinguishable in
  the frontmatter.
- **D-02 (Claude's discretion):** exact `gh` invocation (`gh pr view --json` vs
  `gh pr list --head <branch>`) deferred to research/planning. Must (a) resolve cleanly to "no
  open PR" as the `none` signal PRW-03 needs, without spamming or guessing, and (b) handle
  zero-or-one PR per branch as the common case — note if more than one PR can target a branch
  and how that's handled.
- **D-03 (Claude's discretion):** PR.md count-only-vs-breakdown-table depth deferred to planner,
  driven by what the `ship:pre` advisory warning needs to say (PRW-02 success criterion 3:
  "visible warning naming the status"). At minimum the frontmatter must carry `pr_status`,
  matching MDL's `LINT-REPORT.md` "regenerated every step, never hand-edited" banner convention.
- **D-04:** Two distinct, differently-worded notices — `gh` missing from `PATH`
  (`shutil.which("gh")` guard, install-focused message) vs `gh` present but `gh auth status`
  failing (login-focused message) — so the user can tell which fix applies. Exact wording left
  to the executor. — Reversibility: reversible — message text only.

### Claude's Discretion

- Exact `gh` invocation for PR lookup (D-02).
- PR.md body depth beyond the mandatory `pr_status` frontmatter field (D-03).
- Exact wording of both PRW-04 notices (D-04) and the PRW-02 `ship:pre` advisory warning text.
- Whether `execute:wave:post` is a Python script (beads-sync/markdown-linting style) or another
  mechanism — must still produce `.planning/PR.md` with the `pr_status` frontmatter contract.

### Deferred Ideas (OUT OF SCOPE)

None raised beyond the roadmap's own v2 backlog (PRW-05, blocking gate — already tracked in
REQUIREMENTS.md). Also out of scope per REQUIREMENTS.md's Out of Scope table: auto-merge,
auto-assign-reviewers/review-thread automation, `gh pr-review` extension dependency, draft-PR
auto-create on `ship:post`.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRW-01 | `PR.md` artifact generated at `execute:wave:post`, `pr_status` ∈ {none,passing,pending,failing}, regenerated every step | See Architecture Patterns (PR.md contract), Code Examples (verified `gh` invocations + rollup logic), Pitfall 4 (path scoping) |
| PRW-02 | `ship:pre` gate reads `PR.md` via `artifact-frontmatter-equals`, tri-state, `onError: skip`, advisory | See Pitfall 1 (single-scalar `equals` cannot express tri-state directly — derived boolean field required), Code Examples (live smoke-test invocation form) |
| PRW-03 | `ship:post` warn-only notice when no open PR exists, never auto-creates | See Pitfall 2 (`gh pr view` silently resolves closed/merged PRs — do not use for existence check), Code Examples (`gh pr list --head <branch> --state open`) |
| PRW-04 | `gh` absent or unauthenticated degrades to no-op, one visible notice each | See Pitfall 5 (`gh auth status --json` always exits 0 even when unauthenticated — do not use `--json` for the auth check), Environment Availability |
</phase_requirements>

## Summary

This phase wraps the pre-installed `gh` CLI (verified present, `gh version 2.97.0`, authenticated
as `davdittrich`) in a Python step script that shells out at `execute:wave:post`, writes a
gate-readable `PR.md` artifact, and is read by a `ship:pre` gate using the same
`artifact-frontmatter-equals` predicate kind Phase 13 (`markdown-linting`) and `beads` already
ship. The shape is a near-exact structural clone of `.gsd/capabilities/markdown-linting/scripts/lint.py`
and its `verify-post` skill: `shutil.which()` fail-open guard, full-overwrite artifact write,
phase-dir-scoped output path, one notice per failure mode, `onError: skip`.

Two load-bearing findings emerged only from live verification and reading the installed
gate-predicate-evaluator source, not from the source `pr-workflow` skill or training knowledge:

1. **`artifact-frontmatter-equals`'s `equals` key takes exactly one scalar value** — there is no
   list/OR support in the evaluator (`gate-predicate-evaluator.cjs` line 114:
   `const expectedValue = predicate['equals'];` compared via strict `===`/stringified equality,
   singular). PRW-02's tri-state requirement ("satisfied for `passing` **and** `none`,
   unsatisfied for `pending` **and** `failing`") cannot be expressed as a single gate on
   `pr_status` directly. `PR.md` must carry a second, pre-reduced frontmatter field (e.g.
   `pr_gate_ok: true`/`false`) that the gate compares with `equals: true` — the same reduction
   pattern `markdown-linting` already uses (`violation_count` collapses N rumdl findings down to
   one int gated with `equals: 0`).
2. **`gh pr checks --json <fields>` and the plain-text/table mode have divergent exit-code
   semantics** — verified by reading `cli/cli`'s `pkg/cmd/pr/checks/checks.go` at the exact
   installed tag `v2.97.0`. In JSON mode, `opts.Exporter.Write(...)` returns **before** the
   function ever reaches its `counts.Failed > 0 → SilentError` / `counts.Pending > 0 →
   PendingError` branches — those special exit codes (documented as "8: Checks pending" in
   `gh pr checks --help`) **only fire in table-printing mode**. With `--json`, the command exits
   `0` for any mix of pass/fail/pending checks, and only exits non-zero (plain error, no special
   code) when there are **zero checks reported at all** — the exact "zero checks configured"
   case D-01 maps to `passing`. The rollup script must therefore read the `bucket` field from a
   successful JSON parse, not branch on `gh pr checks`'s own exit code.

**Primary recommendation:** Structurally clone `lint.py`/`markdown-linting-report` (Python
stdlib-only step script + thin dispatch skill), use `gh pr list --head <branch> --state open
--json number,url` for existence (empty array ⇒ `none`, cleanly distinguishing "no open PR" from
"merged/closed PR exists" — `gh pr view` does not make this distinction), then `gh pr checks
<number> --json bucket` for the rollup, and write both `pr_status` (display) and a derived
`pr_gate_ok` boolean (gate predicate target) into `PR.md`'s frontmatter.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| PR check-status lookup (`gh pr checks`) | External CLI (subprocess) | — | `gh` owns GitHub API auth/pagination/normalization; the step script only shells out and parses JSON, never calls the GitHub API directly |
| Status rollup → `pr_status`/`pr_gate_ok` | gsd-core capability step script (Python, `execute:wave:post`) | — | Pure reduction function, mirrors `lint.py::count_violations` — no state, no I/O beyond the one subprocess call |
| `PR.md` artifact write | gsd-core capability step script | Filesystem (`.planning/phases/<phase>/`) | Regenerated-every-step discipline (B11), phase-dir-scoped so the generic gate evaluator's `findPhaseArtifact` can resolve it |
| `ship:pre` gate evaluation | gsd-core generic evaluator (`gate-predicate-evaluator.cjs`, already installed, not phase-owned code) | — | Declarative `capability.json` `gates[]` entry only; no phase code implements evaluation itself |
| `ship:post` no-PR notice | gsd-core capability step script (`ship:post` dispatch point) | — | Same B6 fail-open notice discipline as PRW-04, just a different lifecycle point and trigger condition |
| `gh` credential/session management | External CLI (`gh auth status`, `~/.config/gh/hosts.yml`) | — | Out of this capability's binding model entirely — never read/write `gh`'s own token store |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `gh` CLI | 2.97.0 (verified installed, `/usr/bin/gh`) | PR/check status source of truth | Already the sole external dependency for `beads`'s `bd` precedent and `markdown-linting`'s `rumdl`/`uvx` precedent — no new dependency class introduced |
| Python 3 stdlib (`subprocess`, `json`, `shutil`, `argparse`, `pathlib`, `datetime`) | matches this repo's `python3` (used by `lint.py`/`sync.py`) | Step script implementation | N5 dependency discipline already established in Phase 13 (`lint.py` docstring: "stdlib-only... no dependency beyond the rumdl/uvx binaries") — no reason to diverge for `gh` |

### Supporting

None — no new package installs for this phase. `gh` is a pre-installed system binary, not a
project dependency declared in any manifest (same status as `bd`/`rumdl`).

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Parsing `gh pr checks --json bucket` (already-normalized) | Parsing `gh pr view --json statusCheckRollup` raw (`CheckRun`/`StatusContext` union types) | Raw `statusCheckRollup` mixes two GraphQL node shapes (`CheckRun`: `status`/`conclusion`; legacy `StatusContext`: `state`) — verified live against `cli/cli`'s own PRs, both shapes appear in the same array. `gh pr checks --json bucket` already does this union-type normalization server-side in the CLI; hand-rolling it here is exactly the "Don't Hand-Roll" trap this section exists to flag |
| `gh pr list --head <branch> --state open` for existence | `gh pr view <branch-or-none>` for existence | `gh pr view` (verified live) returns exit 0 and valid JSON for a **merged/closed** PR on that branch with no error — it does not filter by state. Using it for "does an open PR exist" silently misclassifies a merged-PR branch as "PR exists" unless the caller also inspects the `state` field. `gh pr list --head <branch> --state open` filters server-side and returns `[]` cleanly |
| Two separate `gh` calls (list-for-existence, then checks-for-status) | One `gh pr list --head <branch> --state open --json number,url,statusCheckRollup` call | Single-call is fewer subprocess invocations but forces hand-parsing the raw `statusCheckRollup` union (see above) instead of `gh pr checks`'s normalized `bucket`. Recommend the two-call form: cheap existence probe first (skips the second call entirely on `none`, which is the common early-phase case), then the checks call only when a PR is confirmed open |

**Installation:** none — `gh` is assumed present in the environment per PRW-04's own fail-open
requirement (its absence is a first-class supported state, not an error).

**Version verification:** `gh --version` → `gh version 2.97.0 (2026-07-31)`, confirmed installed
and on `PATH` this session (`/usr/bin/gh`). `pkg/cmd/pr/checks/checks.go` was read at git tag
`v2.97.0` specifically — the exit-code/JSON-export ordering finding is tied to that exact
version's source, not to gh's changelog claims about a version range.

## Package Legitimacy Audit

Not applicable — this phase installs no new package (npm/PyPI/crates or otherwise). `gh` is a
pre-existing system CLI binary, identical in kind to the `bd`/`rumdl` dependencies already
audited and shipped in Phases 12/13. No `package-legitimacy check` run required.

## Architecture Patterns

### System Architecture Diagram

```
execute:wave:post (lifecycle dispatch point)
        │
        ▼
pr-workflow-report skill (thin dispatch, mirrors markdown-linting-report)
        │  reads .planning/config.json for pr-workflow.enabled gate
        ▼
scripts/pr_status.py verify-post <phase_dir>
        │
        ├─ shutil.which("gh") is None? ──yes──► print PRW-04 "gh absent" NOTICE
        │                                        write PR.md: pr_status=unavailable,
        │                                        pr_gate_ok=false, unavailable_reason=...
        │                                        (return 0, fail-open)
        │  no
        ▼
`gh auth status` (plain text, NOT --json) exit code check
        │
        ├─ exit != 0? ──yes──► print PRW-04 "gh unauthenticated" NOTICE
        │                       write PR.md: pr_status=unavailable, pr_gate_ok=false
        │                       (return 0, fail-open)
        │  exit 0
        ▼
`gh pr list --head <current-branch> --state open --json number,url`
        │
        ├─ [] (empty)? ──yes──► pr_status = none, pr_gate_ok = true (advisory-satisfied)
        │  non-empty
        ▼
`gh pr checks <number> --json bucket`
        │
        ├─ non-zero exit, stderr matches
        │  "no checks reported"/"no commit found"? ──yes──► pr_status = passing (D-01: zero
        │                                                     checks configured = passing)
        │  exit 0, JSON array of {bucket}
        ▼
rollup: any bucket=="fail" or "cancel" → failing
        else any bucket=="pending" → pending
        else (all "pass"/"skipping") → passing
        │
        ▼
_write_report(): full overwrite of <phase_dir>/<padded_phase>-PR.md
        frontmatter: pr_status, pr_gate_ok (derived: true iff pr_status in {none,passing}),
                     generated_at, generated_from
        │
        ▼
ship:pre gate (declarative, gsd-core generic evaluator — no phase code)
        artifact-frontmatter-equals { artifact: "PR.md", field: "pr_gate_ok", equals: true }
        blocking: false (advisory) → ⚠ pr-workflow advisory: {message} on mismatch, never halts
        │
        ▼
ship:post (separate dispatch point, PRW-03)
        `gh pr list --head <branch> --state open` again (fresh check, not reusing PR.md's
        possibly-stale value) → empty ⇒ print exactly one warn-only notice, create nothing
```

### Recommended Project Structure

```
.gsd/capabilities/pr-workflow/
├── capability.json              # id: pr-workflow; steps[execute:wave:post, ship:post];
│                                 # gates[ship:pre]; config: pr-workflow.enabled, .ship_gate
├── scripts/
│   └── pr_status.py             # verify-post (writes PR.md) + no-pr-notice (ship:post) +
│                                 # shared rollup/lookup helpers
├── skills/
│   └── pr-workflow-report/
│       └── SKILL.md             # thin dispatch, config-gate check, calls pr_status.py
└── tests/
    ├── fixtures/                # synthetic gh --json stdout captures: pass/pending/fail/
    │                             # zero-checks/no-open-pr, one fixture file per state
    └── test_pr_status.py
```

### Pattern 1: Two-tier `gh` availability guard, then plain (non-JSON) auth probe

**What:** `shutil.which("gh")` first (PRW-04 "absent" case); only if present, run `gh auth
status` **without `--json`** and check the process exit code (PRW-04 "unauthenticated" case).
**When to use:** Every `gh`-shelling script entry point, before any PR lookup.
**Why not `--json`:** `gh auth status --json hosts` was verified live this session (`GH_CONFIG_DIR`
pointed at an empty directory) to still print the "not logged in" text to stderr **but exit 0**
and return `{"hosts":{}}` — `gh`'s own `--json` documentation states this explicitly ("when using
the `--json` option, the command will always exit with zero regardless of any authentication
issues"). The plain-text invocation exited `1` in the same test. Detecting PRW-04's
unauthenticated case therefore requires the non-`--json` invocation.
```python
# Source: verified live this session against installed gh 2.97.0
import shutil, subprocess

if shutil.which("gh") is None:
    # PRW-04 notice A: "gh not found — install: https://cli.github.com"
    ...
auth = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=15)
if auth.returncode != 0:
    # PRW-04 notice B: "gh not authenticated — run: gh auth login"
    ...
```

### Pattern 2: Existence probe before status probe

**What:** `gh pr list --head <branch> --state open --json number,url` first; only call
`gh pr checks` if that array is non-empty.
**When to use:** Every `execute:wave:post` regeneration.
**Example:**
```python
# Source: verified live this session against davdittrich/gsd-beads (empty case) and
# cli/cli (non-empty case, via --repo override for the live-shape check only)
import subprocess, json

branch = subprocess.run(
    ["git", "branch", "--show-current"], capture_output=True, text=True, timeout=10
).stdout.strip()

result = subprocess.run(
    ["gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number,url"],
    capture_output=True, text=True, timeout=30,
)
prs = json.loads(result.stdout) if result.returncode == 0 else []
if not prs:
    pr_status, pr_gate_ok = "none", True
    # PRW-03: emit the ship:post warn-only notice from this same signal, never create a PR
else:
    pr_number = prs[0]["number"]  # D-02 note: >1 open PR per head branch is possible if the
                                   # same branch targets multiple base branches — take the
                                   # first result; document this as a known edge case, do not
                                   # silently pick "the most recent" without logging it
    ...
```

### Pattern 3: `gh pr checks --json bucket` rollup, exit-code aware

**What:** Parse `bucket` (not raw `state`/`conclusion`) from `gh pr checks <number> --json
bucket`; treat a non-zero exit **with empty stdout** as the D-01 "zero checks configured"
case, distinct from any other failure.
**Example:**
```python
# Source: verified this session by reading cli/cli v2.97.0
# pkg/cmd/pr/checks/checks.go (populateStatusChecks / checksRun control flow)
checks = subprocess.run(
    ["gh", "pr", "checks", str(pr_number), "--json", "bucket"],
    capture_output=True, text=True, timeout=30,
)
if checks.returncode != 0:
    stderr = checks.stderr.lower()
    if "no checks reported" in stderr or "no commit found" in stderr:
        pr_status = "passing"  # D-01: zero checks configured = passing
    else:
        raise RuntimeError(f"gh pr checks failed: {checks.stderr}")  # genuine failure —
        # do not silently map to any pr_status; fall through to the script's own
        # tool-failure fail-open path (mirrors lint.py's CalledProcessError handling)
else:
    buckets = {c["bucket"] for c in json.loads(checks.stdout)}
    if buckets & {"fail", "cancel"}:
        pr_status = "failing"
    elif "pending" in buckets:
        pr_status = "pending"
    else:  # only "pass" and/or "skipping" remain
        pr_status = "passing"
pr_gate_ok = pr_status in ("none", "passing")
```

### Anti-Patterns to Avoid

- **Gating directly on `pr_status`:** a single `artifact-frontmatter-equals` gate with
  `equals: "passing"` fails PRW-02's own success criteria (it would incorrectly flag `none` as
  unsatisfied). Always gate on the derived `pr_gate_ok` boolean.
- **Writing `PR.md` at the `.planning/` project root:** the generic gate evaluator's
  `findPhaseArtifact` resolves artifacts relative to `phaseDir` only (verified by reading
  `check-command-router.cjs`'s `findPhaseArtifact`, which tries `<phaseDir>/PR.md`,
  `<phaseDir>/.planning/PR.md`, and `<phaseDir>/*-PR.md` — never the true project-root
  `.planning/PR.md`). `13-RESEARCH.md`'s own Pitfall 1 already documents this trap for
  `LINT-REPORT.md`; PRW-01's roadmap wording ("`.planning/PR.md` exists") must be read as
  shorthand for the phase-dir-scoped `.planning/phases/<phase>/<padded>-PR.md`, matching
  `13-LINT-REPORT.md`'s real on-disk location — see Pitfall 4.
- **Using `gh pr view` (no `--state` filter) to detect "no open PR":** verified live to return
  exit 0 for a merged PR on that branch. Use `gh pr list --head <branch> --state open` instead.
- **Trusting `gh pr checks`'s own exit code (8=pending, etc.) in `--json` mode:** those special
  exit codes are a table-mode-only feature (verified from source); `--json` mode exits 0 for any
  mix of check states and only errors on zero-checks. Branch on parsed `bucket` values, not exit
  code, once JSON is successfully returned.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Check-state normalization across GitHub's two check-status node types (`CheckRun` vs legacy `StatusContext`) | A parser for raw `statusCheckRollup` GraphQL nodes | `gh pr checks --json bucket` | `gh` already performs this union-type normalization server-side (`bucket` ∈ {pass, fail, pending, skipping, cancel}, documented in `gh pr checks --help`'s JSON FIELDS/description); hand-parsing the raw rollup means re-implementing that same union logic and re-discovering the same edge cases `gh`'s maintainers already closed |
| Tri-state (or N-state) gate predicate logic | A new `predicate.kind` (e.g. `artifact-frontmatter-in`) in the gate evaluator | A derived single-scalar boolean field in the artifact's own frontmatter, gated with the existing `artifact-frontmatter-equals` | Adding a new predicate kind touches shared gsd-core evaluator code outside this capability's boundary and duplicates what `markdown-linting`/`beads` already solved by pre-reducing to a scalar in the *artifact*, not the *predicate* |
| PR existence + auth-failure detection heuristics | Regex-scraping `gh pr view`'s human-readable stderr for "no pull requests found" as the sole signal | `gh pr list --head <branch> --state open --json ...` (structured, state-filtered) for existence; plain (non-`--json`) `gh auth status` exit code for auth | Structured/exit-code signals are stable API surface; scraping human-readable text (which `gh` itself flags as sometimes buggy — see `cli/cli#5284`, an empty-branch-name edge case in that exact message) is fragile |

**Key insight:** every "don't hand-roll" here traces back to one theme: `gh`'s own `--json`
output and exit-code taxonomy already solved the parsing/rollup problem this phase needs; the
`gh pr-review` extension referenced in the source `pr-workflow` skill is explicitly out of scope
(REQUIREMENTS.md), so no `gh` extension dependency should be introduced anywhere in this
capability.

## Common Pitfalls

### Pitfall 1: `artifact-frontmatter-equals` cannot express tri-state directly

**What goes wrong:** A plan writes `{"kind":"artifact-frontmatter-equals","artifact":"PR.md",
"field":"pr_status","equals":"passing"}` as the `ship:pre` gate, expecting it to also treat
`none` as satisfied.
**Why it happens:** `gate-predicate-evaluator.cjs::evaluateArtifactFrontmatterEquals` reads a
single `predicate['equals']` value and compares with strict/stringified equality — verified by
reading the installed evaluator this session (line 114 onward). There is no array/OR support.
**How to avoid:** Write a second, pre-reduced frontmatter field (`pr_gate_ok: true|false`,
computed as `pr_status in {"none","passing"}`) in `PR.md`, and gate on that field with
`equals: true`. `pr_status` remains for the human-readable advisory message body/warning text
(D-03), not for the gate predicate itself.
**Warning signs:** A smoke test (mirroring `13-GATE-SMOKE-TEST.md`) where the `none` case
returns `block: true` — that's the tell this pitfall was hit.

### Pitfall 2: `gh pr view`/`gh pr view <branch>` succeeds for closed/merged PRs

**What goes wrong:** Using `gh pr view` (or `gh pr view <branch>`) with no `--state` filter to
answer "does an open PR exist for this branch", and treating any successful exit as "PR exists,
proceed to check status".
**Why it happens:** Verified live this session against a real merged PR
(`cli/cli#14193`, branch `bagtoad/pre-release-tag-validation`): `gh pr view
bagtoad/pre-release-tag-validation --repo cli/cli --json state,number` returned exit `0` and
`{"number":14193,"state":"MERGED"}` — no error, despite the PR being closed.
**How to avoid:** Use `gh pr list --head <branch> --state open --json number,url` for the
existence check (server-side state filter, verified to return `[]` cleanly with exit 0 for a
branch with only a merged PR). Reserve `gh pr view`/`gh pr checks <number>` for the follow-up
call once a specific open PR number is already known.
**Warning signs:** `pr_status` reads `passing`/`failing` on a branch the user knows has no open
PR — check whether the existence probe filtered by state.

### Pitfall 3: `gh pr checks --json` exit codes do not carry pass/fail/pending information

**What goes wrong:** Branching on `gh pr checks <number> --json bucket`'s exit code (expecting
`0`=passing, `8`=pending, nonzero=failing, per the documented table-mode exit codes).
**Why it happens:** Verified this session by reading `cli/cli`'s `v2.97.0` source
(`pkg/cmd/pr/checks/checks.go`): the `opts.Exporter != nil` (JSON) branch returns immediately
after `populateStatusChecks` succeeds, **before** the function ever reaches the
`counts.Failed>0`/`counts.Pending>0` branches that produce `SilentError`/`PendingError` (exit
codes referenced in `--help`'s "Additional exit codes: 8: Checks pending"). In JSON mode the
command exits `0` regardless of the check-state mix, and only exits non-zero (a plain error, no
special code) when zero checks are reported at all.
**How to avoid:** On exit `0`, always parse `bucket` values from stdout and apply D-01's
precedence in the script, never the exit code. On non-zero exit, inspect stderr for "no checks
reported"/"no commit found" as the zero-checks-configured signal (→ `passing` per D-01);
treat any other non-zero exit as a genuine tool failure (fail-open, do not guess a `pr_status`).
**Warning signs:** A synthetic zero-checks fixture in tests that asserts on `checks.returncode`
alone without a stderr string match will misclassify a real failed-check exit (which, per source,
is `SilentError`/exit-related in table mode but behaves as **exit 0 with JSON body** in `--json`
mode) as the zero-checks case, or vice versa.

### Pitfall 4: Roadmap's literal `.planning/PR.md` wording is not the real artifact path

**What goes wrong:** A plan takes PRW-01 success criterion 1 ("`.planning/PR.md` exists")
literally and writes a single project-root file, unscoped to any phase directory.
**Why it happens:** Every existing generated-artifact precedent (`BEADS.md`, `LINT-REPORT.md`)
actually lives phase-dir-scoped with a padded-phase prefix — confirmed by directory listing:
`.planning/phases/13-markdown-linting-capability-dogfood/13-LINT-REPORT.md` is the real on-disk
path, and `13-RESEARCH.md`'s own Pitfall 1 explicitly warns against a project-root path for this
exact reason (the gate evaluator's `findPhaseArtifact` never resolves there).
**How to avoid:** Write `.planning/phases/<phase-dir>/<padded_phase>-PR.md`, exactly like
`13-LINT-REPORT.md`. Read the roadmap's `.planning/PR.md` as shorthand, not a literal path
requirement — the `artifact: "PR.md"` suffix in `capability.json`'s `steps[].produces` /
`gates[].check.predicate.artifact` matches this via `findPhaseArtifact`'s suffix-fallback
(`f.endsWith('-' + artifactSuffix)`), verified by reading `check-command-router.cjs`.
**Warning signs:** The `ship:pre` gate reports `Artifact matching PR.md not found in <phaseDir>`.

### Pitfall 5: `gh auth status --json` cannot detect authentication failure

**What goes wrong:** Using `gh auth status --json hosts` and checking the process exit code to
distinguish PRW-04's "unauthenticated" notice from the happy path.
**Why it happens:** Verified live this session (`GH_CONFIG_DIR` pointed at an empty directory):
`gh auth status --json hosts` printed "You are not logged into any GitHub hosts." to stderr but
exited `0`, returning `{"hosts":{}}`. `gh auth status --help` documents this explicitly: "when
using the `--json` option, the command will always exit with zero regardless of any
authentication issues." The plain (non-`--json`) invocation exited `1` in the identical test.
**How to avoid:** Use the plain `gh auth status` (no `--json`) and check `returncode != 0` for
PRW-04's unauthenticated case. If a machine-readable signal is also wanted, parse `{"hosts":{}}`
(empty) from the `--json` output as a secondary confirmation, never as the primary gate.
**Warning signs:** PRW-04's live-verification success criterion ("exactly one visible notice per
case") fails silently for the auth-failure case specifically (the absent-`gh` case is unaffected,
since `shutil.which` never invokes `gh` at all).

### Pitfall 6: `skipping`/`cancel` buckets are not literally named in D-01's three states

**What goes wrong:** D-01 defines precedence over `FAILURE`/`ERROR`/`PENDING`/`IN_PROGRESS`/
`QUEUED`/`SUCCESS` (GitHub's raw check-run vocabulary) but `gh pr checks --json bucket` emits a
different, already-normalized five-value vocabulary: `pass`, `fail`, `pending`, `skipping`,
`cancel` (per `gh pr checks --help`'s own description of the `bucket` field, and confirmed live:
`pass` and `skipping` were both observed in a real PR's output this session). Neither
`skipping` nor `cancel` appears in D-01's literal state list.
**Why it happens:** D-01 was written against GitHub's raw check-run states, not `gh`'s
CLI-level `bucket` reduction, which is a distinct (if closely related) vocabulary the CONTEXT.md
author likely was not aware of when writing D-01 (the source `pr-workflow` skill only shows
`gh pr checks <pr-number> --watch`, not `--json bucket`).
**How to avoid:** Map `bucket` values onto D-01's three states: `pass` → passing-contributing,
`skipping` → passing-contributing (GitHub's own documented required-check semantics treat a
skipped job as equivalent to success for merge purposes — a `[CITED: docs.github.com]` claim,
see Sources), `pending` → pending, and `fail`/`cancel` → failing (a cancelled check generally
blocks merge per the same GitHub docs, grouped with failure/timeout/action-required
conclusions). Flag this mapping explicitly in the plan/PLAN.md rather than silently
reinterpreting D-01 — it is a real gap in the locked decision, not a free implementation choice.
**Warning signs:** A synthetic fixture with only `skipping`/`cancel` buckets produces an
unexpected `pr_status`, or the discuss-phase CONTEXT.md is re-read expecting `skipping`/`cancel`
literal handling that isn't there.

## Code Examples

Verified patterns from this session's live `gh` invocations and the installed gsd-core evaluator:

### Existence check (verified: empty case against this repo, non-empty case against `cli/cli`)
```bash
# Source: verified live this session
$ gh pr list --head main --json number,state
[]
$ gh pr list --repo cli/cli --head dependabot/github_actions/aw-actions-6814edcebc \
    --state open --json number,statusCheckRollup
[{"number":14192,"statusCheckRollup":[{"__typename":"CheckRun","status":"COMPLETED",
  "conclusion":"SKIPPED", ...}, ...]}]
```

### `gh auth status` — plain vs `--json`, verified both branches
```bash
# Source: verified live this session (GH_CONFIG_DIR pointed at an empty dir)
$ GH_CONFIG_DIR=/tmp/empty-gh-config gh auth status
You are not logged into any GitHub hosts. To log in, run: gh auth login
$ echo $?
1
$ GH_CONFIG_DIR=/tmp/empty-gh-config gh auth status --json hosts
You are not logged into any GitHub hosts. To log in, run: gh auth login
{"hosts":{}}
$ echo $?
0
```

### `gh pr checks --json bucket` — normalized rollup field
```bash
# Source: verified live this session against cli/cli#14192
$ gh pr checks 14192 --repo cli/cli --json bucket,state,name,workflow
[{"bucket":"pass","name":"CodeQL","state":"SUCCESS","workflow":""},
 {"bucket":"skipping","name":"label-external","state":"SKIPPED","workflow":"PR Triaging"}, ...]
```

### Live `gsd_run check predicate` smoke-test invocation form (PRW-02 success criterion 2)
```bash
# Source: 13-GATE-SMOKE-TEST.md (exact form to replicate against a derived pr_gate_ok field,
# using scratch phase-dir fixtures for each of the four pr_status states)
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"PR.md","field":"pr_gate_ok","equals":true}' \
    --phase-dir <scratch-dir-with-PR.md-pr_gate_ok:true> \
    --phase-number 14 --raw
{
  "block": false,
  "message": "Frontmatter field \"pr_gate_ok\" matches expected value (true)",
  "details": { "kind": "artifact-frontmatter-equals", "match": true }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-parsing GitHub commit-status/check-run API responses | `gh pr checks --json bucket` normalized field | Available since `gh`'s `--json` support for `pr checks` (long-shipped, present in installed 2.97.0) | Removes the union-type (`CheckRun` vs `StatusContext`) parsing burden entirely |

**Deprecated/outdated:** none identified — this is a thin wrapper phase, not a phase introducing
or replacing a library.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `bucket` values `fail` and `pending` behave identically to the observed `pass`/`skipping` (i.e., these are the only five bucket values and their names are stable) — not observed live this session, only documented in `gh pr checks --help`'s field list | Pitfall 6, Architecture Patterns Pattern 3 | If `gh` ever emits an undocumented sixth bucket value, the rollup's `else → passing` fallback would silently treat it as passing; low risk since `--help` is authoritative CLI documentation for the installed version |
| A2 | GitHub's "skipped counts as passing, cancelled generally blocks" required-check semantics (used to justify the `skipping`→passing, `cancel`→failing mapping in Pitfall 6) — sourced from GitHub's public docs and community discussion, not from a live test against a branch-protected repo with an actual skipped/cancelled required check | Pitfall 6, Architecture Patterns Pattern 3 | If wrong, `cancel` should map to `pending` instead of `failing`, or `skipping` should be excluded from the rollup entirely rather than treated as passing-neutral — low-to-medium risk, only affects the rare skipped/cancelled-check edge case, not the common pass/fail/pending path |
| A3 | "no commit found on the pull request" (the other zero-checks error string, alongside "no checks reported on the '%s' branch") is reachable and worth matching — read from source, not observed live | Code Examples, Pattern 3 | Low risk: matching on the substring "no checks reported" alone would still cover the common case; the second string only matters for a freshly-opened PR before its first commit's checks register at all |
| A4 | More than one open PR can target the same head branch (different base branches) — noted per D-02's own instruction to document this edge case, not independently verified live this session (no such PR was found to test against) | Standard Stack Alternatives Considered, Pattern 2 | Low risk: GitHub does allow multiple open PRs from the same head branch to different base branches; taking `prs[0]` (list order is unspecified by `gh`) could pick a less-relevant PR in that rare case — acceptable per D-02's "note it, don't need to solve it" framing |

**If this table is empty:** N/A — table is populated; see above.

## Open Questions

1. **Should `pr_status` and `pr_gate_ok` both live in `PR.md` frontmatter, or should `pr_gate_ok`
   be computed transitively without a stored field?**
   - What we know: the gate evaluator only reads a literal frontmatter field via `equals`; it
     cannot itself compute `pr_status in {"none","passing"}`.
   - What's unclear: whether the planner prefers naming it `pr_gate_ok` (boolean) vs. an
     alternative single-scalar encoding (e.g. `pr_gate_state: "ok"|"warn"`) compared with
     `equals: "ok"` — functionally equivalent, purely a naming/readability choice.
   - Recommendation: `pr_gate_ok: true|false` is the more legible boolean and matches
     `beads`'s existing boolean-flavored fields (`blocking_open`, `diverged` — both
     `equals: 0`-style numeric booleans); either is fine, planner's call.

2. **Does this repo's own `ship:pre` dispatch loop need a per-gate patch verification step,
   the way Phase 13 required (re-confirming the `gsd-beads-patch:ship-pre-generic-dispatch v1`
   marker in the installed `ship.md`)?**
   - What we know: Phase 13 explicitly re-verified this marker live before trusting its own
     gate would fire (STATE.md Blockers/Concerns, `13-RESEARCH.md`, `13-GATE-SMOKE-TEST.md`
     Step 1). The patch is machine-local, unmerged upstream (`open-gsd/gsd-core#3559`).
   - What's unclear: whether that verification is a one-time-per-machine check (already done
     for Phase 13, still valid) or needs re-confirming per-phase.
   - Recommendation: planner should include the same Step-1-style re-verification (cheap grep,
     already the exact command in `13-GATE-SMOKE-TEST.md`) as a first task, matching precedent
     rather than assuming it's still valid unchecked.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `gh` CLI | PRW-01/02/03/04 (entire capability) | ✓ | 2.97.0 (2026-07-31), `/usr/bin/gh` | PRW-04 IS the fallback path: `shutil.which("gh") is None` → notice + `pr_status: unavailable`/`pr_gate_ok: false`, `onError: skip` |
| `gh auth` (session) | PR lookup/checks calls | ✓ | Logged in as `davdittrich`, scopes `gist, read:org, repo, workflow` | PRW-04's second notice path: `gh auth status` (plain) exit != 0 → same fail-open write |
| `git` (for current-branch detection) | Existence probe (Pattern 2) | ✓ | present, used throughout this repo already | none needed — `git` is an existing hard dependency of every other lifecycle step |
| Python 3 | Step script runtime | ✓ | matches `lint.py`/`sync.py`'s interpreter, already required | none needed — established project dependency |

**Missing dependencies with no fallback:** none — every dependency here already has a designed
fallback (PRW-04 covers `gh`/auth; `git`/Python 3 are pre-existing hard project dependencies with
no independent fallback path needed since every other capability already assumes them).

**Missing dependencies with fallback:** `gh` absent or unauthenticated — see PRW-04 fail-open
path above.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (matches `.gsd/capabilities/markdown-linting/tests/test_lint.py`'s established pattern in this repo) |
| Config file | none dedicated — reuses whatever root pytest config already collects `.gsd/capabilities/*/tests/` (verify at Wave 0; `markdown-linting`'s `tests/test_lint.py` is the direct precedent to confirm collection against) |
| Quick run command | `pytest .gsd/capabilities/pr-workflow/tests/ -x` |
| Full suite command | `pytest .gsd/capabilities/pr-workflow/tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRW-01 | Rollup precedence (failing>pending>passing) over synthetic `gh pr checks --json bucket` stdout fixtures, one per state incl. zero-checks | unit | `pytest .gsd/capabilities/pr-workflow/tests/test_pr_status.py::test_rollup_precedence -x` | ❌ Wave 0 |
| PRW-01 | `PR.md` full-overwrite (not append) on re-run | unit | `pytest .gsd/capabilities/pr-workflow/tests/test_pr_status.py::test_regenerate_overwrites -x` | ❌ Wave 0 |
| PRW-02 | Gate predicate satisfied for `none`/`passing`, unsatisfied for `pending`/`failing` via `gsd_run check predicate` | smoke (live subprocess against real evaluator, mirrors `13-GATE-SMOKE-TEST.md`) | manual/scripted `gsd_run check predicate --predicate '...' --phase-dir <scratch> --raw` per state | ❌ Wave 0 (fixture scratch dirs) |
| PRW-03 | No-open-PR notice printed exactly once, no PR created, `gh pr list` empty before/after | integration (real `gh pr list` subprocess against this repo's actual `main` branch, which has no open PR) | `pytest .gsd/capabilities/pr-workflow/tests/test_pr_status.py::test_no_open_pr_notice -x` (skip if no `gh`/auth, mirrors `markdown-linting`'s `unittest.skipUnless` pattern) | ❌ Wave 0 |
| PRW-04 | `gh` absent → one notice, no hang; `gh auth status` failing → one different notice | unit (scratch `PATH` without `gh`, mirrors `13-GATE-SMOKE-TEST.md` Step 4's scratch-`PATH` technique; `GH_CONFIG_DIR` pointed at an empty dir for the auth-failure case, verified viable live this session) | `pytest .gsd/capabilities/pr-workflow/tests/test_pr_status.py::test_gh_absent -x` / `::test_gh_unauthenticated -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest .gsd/capabilities/pr-workflow/tests/ -x`
- **Per wave merge:** full suite, same command (small suite, no need to split quick/full further)
- **Phase gate:** full suite green before `/gsd:verify-work`, plus the live
  `gsd_run check predicate` smoke test (not pytest-automatable against the real evaluator binary
  without shelling out — keep it as the documented manual/scripted smoke-test step Success
  Criterion 2 requires, matching `13-GATE-SMOKE-TEST.md`'s form exactly)

### Wave 0 Gaps
- [ ] `.gsd/capabilities/pr-workflow/tests/test_pr_status.py` — covers PRW-01/02/04 unit-level rollup/notice logic
- [ ] `.gsd/capabilities/pr-workflow/tests/fixtures/` — synthetic `gh pr checks --json bucket` stdout captures for pass/pending/fail/zero-checks, and a synthetic empty `gh pr list` capture for the no-open-PR case
- [ ] `14-GATE-SMOKE-TEST.md` (doc, not a test file) — live `gsd_run check predicate` two/four-case run, same form as `13-GATE-SMOKE-TEST.md`, required to satisfy PRW-02's "predicate is observed firing" success criterion literally (a passing pytest suite alone does not satisfy it — STATE.md's own Blockers/Concerns note: "a green ship is not evidence the gate works")

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | This capability never handles credentials directly — `gh`'s own token store (`~/.config/gh/hosts.yml`) is read only by `gh` itself, never touched by the step script |
| V5 Input Validation | Yes | All `gh`/`git` invocations pass as argv lists to `subprocess.run` (never `shell=True`, never an interpolated shell string) — mirrors `lint.py`'s documented discipline ("no rumdl command is ever assembled as a shell string"). The current-branch name (from `git branch --show-current`) and PR number (from parsed `gh` JSON, always an integer field) are the only externally-influenced values reaching a subprocess argv; both are passed as discrete argv elements, never string-concatenated into a shell command |
| V6 Cryptography | No | No cryptographic operations in this capability |
| V12 File/Path handling | Yes | `PR.md`'s output path must be confined to the resolved phase directory the same way `lint.py::confined()` guards `LINT-REPORT.md`'s path — reuse that exact pattern (`find_project_root` + `confined()`), do not hand-roll a new path-confinement helper (Don't Hand-Roll principle applies here too, even though it's not in the main table since it's an intra-repo pattern, not an external library) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Shell-string command injection via a branch name or PR title containing shell metacharacters | Tampering | argv-list `subprocess.run`, never `shell=True` / f-string-built commands (already the established pattern in `lint.py`/`sync.py`) |
| PR.md path escape (a crafted `phase_dir` argument pointing outside `.planning/`) | Tampering | Reuse `lint.py`'s `confined()` helper verbatim (path resolved and checked via `.relative_to(root)`, raising on escape) |
| Token/credential leakage into `PR.md` or step-script stdout | Information Disclosure | Never invoke `gh auth status --show-token` or capture/log the value of `GH_TOKEN`; only capture `stdout`/`stderr` of the specific read-only calls listed in this document (`gh pr list`, `gh pr checks`, `gh auth status` without `--show-token`) |

## Sources

### Primary (HIGH confidence — live-verified this session)
- Installed `gh` CLI, version 2.97.0 (`/usr/bin/gh`) — `gh --version`, `gh pr checks --help`,
  `gh auth status --help`, `gh pr list --head <branch> --state open --json ...`,
  `gh pr checks <n> --json bucket`, `gh auth status` (plain and `--json`, both auth-success and
  auth-failure via `GH_CONFIG_DIR` override) — all commands run and their exact stdout/exit
  codes captured this session.
- `github.com/cli/cli` source, tag `v2.97.0`, `pkg/cmd/pr/checks/checks.go` — fetched and read
  this session (`WebFetch`) to confirm the JSON-export-vs-table-mode exit-code divergence
  (Pitfall 3).
- Installed gsd-core `gate-predicate-evaluator.cjs` and `check-command-router.cjs` — read
  directly this session (single-scalar `equals` behavior, `findPhaseArtifact` resolution rules,
  `gsd_run check predicate` invocation contract).
- `.planning/phases/13-markdown-linting-capability-dogfood/13-GATE-SMOKE-TEST.md`,
  `13-RESEARCH.md`, `.gsd/capabilities/markdown-linting/scripts/lint.py`,
  `.gsd/capabilities/markdown-linting/capability.json`,
  `.gsd/capabilities/beads/capability.json` — read directly this session as the structural
  precedent this phase clones.

### Secondary (MEDIUM confidence)
- GitHub Docs — "Troubleshooting required status checks" / "Status checks" reference pages and
  community discussion on skipped/cancelled check semantics for required-status-check merge
  gating (Pitfall 6's `skipping`→passing, `cancel`→failing mapping). [CITED: docs.github.com]
- `cli/cli` GitHub issues #5284, #9390, #7401, #9691 — corroborate the "no checks reported"
  error-text/exit-code history and confirm PR #9691's proposed exit-code-16 change was **not**
  merged (verified via a direct `WebFetch` of the PR itself, not just the search summary).

### Tertiary (LOW confidence)
- None used as load-bearing claims — every claim in this document is either live-verified,
  sourced from installed code read directly, or explicitly logged in the Assumptions table
  above.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependency, `gh` version and auth state directly verified
- Architecture: HIGH — gate-evaluator single-scalar-equals constraint and artifact path
  resolution rules read directly from installed gsd-core source, not inferred
- Pitfalls: HIGH for gh-CLI-behavior pitfalls (1,2,3,5 verified live or from exact-version
  source); MEDIUM for pitfall 6 (skipped/cancelled semantics cited from GitHub docs, not
  live-tested against a real branch-protected repo)

**Research date:** 2026-08-18
**Valid until:** 30 days (gh CLI is a fast-moving but backward-compatible tool; the JSON-export
exit-code behavior is tied to the exact installed `v2.97.0` and should be re-checked if `gh` is
upgraded before this phase executes)
