# Phase 17: Config/Code Truth - Research

**Researched:** 2026-08-20
**Domain:** Python capability internals (`sync.py`), gsd-core capability-config plumbing, upstream gsd-core lifecycle-dispatch PR tracking
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Implement `mirror`, drop `off`. `capability.json`'s `beads.sync_mode` `values` becomes `["authoritative", "mirror"]`.
- **D-02:** `mirror` means "never strip PLAN.md task bodies" — maps directly onto the existing `allow_strip` parameter.
- **D-03:** The `PostToolUse` hook forces `mirror` (`allow_strip=False`) regardless of config — the hook is a weaker principal (string match) than explicit dispatch.
- **D-04:** The migration answer for existing on-disk `sync_mode` values (e.g. `"off"`) is Claude's discretion, but must be stated explicitly — not left implicit.
- **D-05:** Detect native #3687 dispatch by probing the installed `plan-phase.md`/`verify-work.md` for the generic-dispatch text (marker-grep, not version-sniffing). Failure mode must degrade to double-dispatch (safe), never to missed dispatch.
- **D-06:** Native dispatch is a trusted principal — `sync_mode` governs its strip behavior (unlike the hook, which always forces `mirror`).
- **D-07:** The decimal-phase fix is a string leading-zero strip plus `re.escape`, NOT float/Decimal parsing. `re.escape` is non-negotiable. Sites: `sync.py:634` (`get_phase_header`) and `sync.py:1489` (`extract_phase_mentions`).
- **D-08:** Collapse to ONE parameterized CLI verb, hard break, no aliases, all callers updated in the same commit — justified because grep confirmed no README exposure and no caller outside this repo.
- **D-09:** Add missing `--ship-md-path` test coverage BEFORE the merge lands (currently `--execute-plan-path` is pinned by a CLI test; `--ship-md-path` is not).
- **D-10:** The internal table carries a per-entry marker version field (markers are at different versions: ship v2, execute-plan v1); a new test must assert the literal marker strings.

### Claude's Discretion

- Exact shape of the D-04 migration/notice mechanism for existing on-disk `sync_mode` values.
- Exact CLI verb shape/name for the TRUTH-02 merge.
- Internal table data type/structure for the merged patch-checker.
- Whether release-hygiene debt lands as its own plan or folds into the ship step.

### Deferred Ideas (OUT OF SCOPE)

- REACH-01: non-Claude-Code lifecycle dispatch (other runtimes get `ship:pre` only today; deliberately out of this truth-in-declaration milestone).
- RES-01: `get-available-resources` capability.
- Refiling the `execute:wave:*` upstream gap (no upstream issue tracks it; not shippable from this repo per REQUIREMENTS.md's Out of Scope table).
- New config keys of any kind.
- Reworking the `lifecycle-dispatch` hook matcher (shipped and regression-pinned in 0.3.1; no open defect).
- Upstreaming generic `kind: "step"` dispatch to gsd-core.
- Retroactive bd backfill for pre-0.3.0 phases.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TRUTH-01 | Every value `capability.json` declares for `beads.sync_mode` has an observable effect, or is not declared (`mirror` implemented per D-01/D-02, `off` dropped) — plus a full doc sweep of every false claim about the key's effect. | Alternatives Considered table (wiring mechanism), Pattern 2 (self-read via `read_beads_config`), Detection Channel Analysis, Pitfall 1, 10 confirmed doc-sweep offender lines (Summary) |
| TRUTH-02 | `check_shipmd_patch` and `check_execute_plan_patch` merge into one table-driven reader, preserving both CLI verbs' behavior and flag spellings, with zero regression at either existing call site (`beads-recall/SKILL.md`, `beads-status/SKILL.md`). | Pattern 1 (table-driven checker skeleton), Pitfall 2 (confirmed `--ship-md-path` test gap), Pitfall 3 (marker-version conflation), full blast-radius enumeration (Summary/prior session) |
| TRUTH-03 | The `PostToolUse` hook stays correct once gsd-core ships PR #3687 (double-dispatch + `allow_strip` bypass), while `execute:wave:pre/post` (not covered by #3687) keep working unchanged. | Fresh PR #3687 status verification (Summary, Sources), Architecture Diagram, Pattern 2 (D-06 call-site fix at `sync.py:2249`), Alternatives Considered (detection mechanism), Open Question 1 and 2 |
| TRUTH-04 | Decimal phase numbers (`1.5`, `10.1`, `11.1`) work at all three beads lifecycle points that currently break (`PLAN_FILE_RE`, `get_phase_header`, `extract_phase_mentions`). | Code Examples (`sota-numerics` precedent, verified exact source), Don't Hand-Roll, Security Domain (ReDoS/injection mitigations), git-history fixture verification (Sources) |

</phase_requirements>

## Summary

This phase closes four declaration-vs-code divergences in the `beads` gsd-core capability, all inside one file (`plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`, 2286 lines) plus its `capability.json` and doc twins. Every ROADMAP.md file:line citation was re-verified against the current working tree (commit `0bd5b9b`, unchanged since the roadmap's `966315a` baseline) — **zero drift found**, with one exception: `config-loader.cjs`'s unknown-key filter is at line 728, not 727 as PITFALLS.md (an earlier research doc) cited — a one-line correction, now confirmed by direct read.

TRUTH-04 (decimal-phase regex) is the smallest, most isolated fix and should land first: two `int(phase_num)` call sites raise `ValueError` on `"01.5"`, and `PLAN_FILE_RE` silently fails to match `"01.5-01-PLAN.md"`. The sibling `sota-numerics` capability already fixed the identical bug in its own regex with a widened pattern that is a direct drop-in model.

TRUTH-03 (hook forward-compatibility) is time-boxed by an upstream PR. Fresh verification today (2026-08-20, via WebFetch against the live GitHub PR page) confirms **gsd-core PR #3687 is merged** to the `next` branch (commit `ea59430`, 2026-08-19), unreleased as of v1.11.0. It adds generic `kind == "step"` dispatch coverage at `plan:post` and `verify:post` (plus `contribution`-kind coverage at `execute:wave:pre`/`execute:wave:post` — not `step`-kind, so the hook still fully owns those two points). This confirms the existing `.planning/research/STACK.md` finding with no correction needed, only a refinement: PR #3687's actual title is "fix(#3606): validate hook-kind coverage at call sites and dispatch generically" — a validator/scanner fix whose side effect closes the two step-dispatch gaps, not a PR named for step-dispatch directly.

TRUTH-01 (`sync_mode`) and TRUTH-02 (patch-checker merge) are both entirely mechanical given CONTEXT.md's locked decisions (D-01 through D-10) — this research supplies the missing empirical facts (exact call sites, blast radius, detection-channel behavior, test-coverage gaps) rather than re-litigating direction, which CONTEXT.md has already settled.

**Primary recommendation:** Sequence exactly as ROADMAP.md orders it — TRUTH-04, TRUTH-03, TRUTH-01, TRUTH-02 — implement `sync_mode` and the hook forward-compat probe as pure `sync.py` self-reads (the only wiring channel that exists), and treat the CLI-verb merge (TRUTH-02) as the highest-risk task because of one confirmed asymmetric test gap (`--ship-md-path` has no CLI-level test; `--execute-plan-path` does, confirmed at `tests/test_sync.py:3059-3072`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `sync_mode` behavior (strip gating) | Capability script (`sync.py`) | Claude Code hook (`lifecycle-dispatch.sh`) | Both the hook path and native-dispatch path ultimately call `sync.py create_issues()`; the hook path hardcodes the flag, the native path must read config itself — see Pattern 2 below |
| Patch-loss detection (`check_*_patch`) | Capability script (`sync.py`) | Skill markdown (`beads-recall/SKILL.md`, `beads-status/SKILL.md`) | Detection logic lives in `sync.py`; skills are pure callers, never reimplement the check |
| Hook-vs-native dispatch precedence | Claude Code `PostToolUse` hook (`lifecycle-dispatch.sh`) | gsd-core native step-dispatch loop (`plan-phase.md`/`verify-work.md`) | Neither tier owns the other; TRUTH-03's job is making the weaker principal (string-matched hook) defer/coexist safely once the stronger principal (native dispatch) exists |
| Decimal-phase parsing | Capability script (`sync.py`) | — | Pure regex/string fix, no cross-tier concern |
| Config schema declaration | `capability.json` (declarative) | `sync.py` (read-time consumer) | `capability.json`'s `config` block is schema + write-time validator only — it has **no delivery channel** to any step; every consumer must self-read via `read_beads_config()` |

## Standard Stack

No new external libraries. This phase is a Python stdlib refactor (`re`, `argparse`, `json`) inside an existing 2286-line script plus markdown/JSON doc edits. No `npm install`/`pip install` required.

### Alternatives Considered — TRUTH-01 `sync_mode` wiring mechanism

| Option | Performance | Simplicity/LOC | Ecosystem Support | Maintenance Overhead | Verdict |
|---|---|---|---|---|---|
| **(A) Self-read via `read_beads_config()`** (existing helper, `sync.py:641-671`) | No measurable cost — one JSON parse already happens at process start | Lowest: reuses the exact pattern `beads.enabled`/`beads.epic_per` already use, zero new plumbing | None needed — capability-internal | Lowest: one helper, one call site per consumer | **Chosen** — matches D-01/D-02, only wiring channel that exists |
| (B) `configValues` contribution | N/A — not reachable | N/A | N/A | N/A | **Ruled out**: `configValues` resolves for `kind: "contribution"` only; the steps loop never calls it and `beads-sync` is a `kind: "step"` entry (`.planning/research/ARCHITECTURE.md`, `loop-resolver.cjs:244` sole call site) |
| (C) `when:` gate on the enum value | N/A — not reachable | N/A | N/A | N/A | **Ruled out**: `capability-activation.cjs:104-107` boolean-coerces `when:`, so any non-empty string (including `"off"`) is truthy — an enum cannot be typed into a `when:` condition |
| (D) `config-equals` gate predicate | N/A — not implemented | N/A | N/A | N/A | **Ruled out**: documented at `capability-manifest.md:117` but `EVALUATOR_KINDS` in `gate-predicate-evaluator.cjs:37` is frozen to `['command-exit-zero', 'artifact-frontmatter-equals']` — `config-equals` does not exist in code |

**Decided by:** Ecosystem support (only (A) has any working channel) — the other three are architecturally absent, not merely inferior.

### Alternatives Considered — TRUTH-03 forward-compat detection mechanism

| Option | Performance | Simplicity/LOC | Ecosystem Support | Maintenance Overhead | Verdict |
|---|---|---|---|---|---|
| **(A) Marker-grep probe on installed workflow files** (D-05, models `check_shipmd_patch`'s shape) | One file read + one substring search, same cost class as the existing patch checkers already running at `plan:pre` | Lowest: literally the same function shape already in the file twice; a third table-driven entry (post-TRUTH-02 merge) costs ~15 lines | None needed — reads `$HOME/.claude/gsd-core/workflows/{plan-phase,verify-work}.md` directly, no gsd-core API dependency | Low: one string constant to update if upstream's dispatch-loop prose changes shape; failure mode is documented (D-05: degrade to double-dispatch, never to missed dispatch) | **Chosen** |
| (B) Version-sniffing (compare installed gsd-core version against a hardcoded "ships in 1.12.0" threshold) | Equivalent | Requires a version-comparison helper plus a hardcoded version string that goes stale the moment the release plan slips | None needed | High: this exact failure mode is why STACK.md exists — a wrong or stale version threshold makes the whole design wrong silently, and nothing re-checks it | **Ruled out** — CONTEXT.md D-05 explicitly rejects this: "detect native #3687 dispatch by probing... not version-sniffing" |
| (C) Accept double-dispatch permanently, do nothing | Wastes one `create_issues()` call and doubles `additionalContext` output at 2 of 5 points once #3687 ships | Zero new code | N/A | Zero — but permanently pays a small tax and never closes TRUTH-03's stated requirement | **Ruled out** — requirement explicitly requires the hook to "stay correct," not merely "stay safe"; TRUTH-03 also requires resolving the `allow_strip` bypass (problem 2), which (C) does not touch at all |

**Decided by:** Simplicity/LOC and Maintenance Overhead — (A) is both the least code and the only option whose failure mode is bounded and pre-declared.

## Package Legitimacy Audit

Not applicable — this phase adds zero external packages (Python stdlib only: `re`, `argparse`, `json`, already imported).

## Architecture Patterns

### System Architecture Diagram

```
Claude Code PostToolUse event
        |
        v
hooks/lifecycle-dispatch.sh  (bash substring pre-filter -> python3 command-position regex match)
        |
        | matches "gsd_run loop render-hooks <point> --raw" in Bash tool call
        v
sync.py lifecycle-dispatch <point>
        |
        +--> plan:pre  --> beads_recall() + check_shipmd_patch() + check_execute_plan_patch()
        |                     (TRUTH-02 merges these two into one table-driven call)
        |
        +--> plan:post --> create_issues(plan, allow_strip=False)   <-- HARDCODED, D-03: hook never strips
        |
        +--> execute:wave:pre/post, verify:post --> beads-status renders/reconciles

Separately, gsd-core's OWN native step-dispatch loop (plan-phase.md / verify-work.md workflows)
independently triggers the "beads-sync" SKILL, which runs:

        python3 sync.py create-issues <plan_path>   (NO --allow-strip flag exists on this CLI verb)
                |
                v
        create_issues(plan_arg, allow_strip=True)    <-- DEFAULT, at sync.py:2249's call site
                |                                          TRUTH-03/D-06 must make this read
                |                                          beads.sync_mode instead of hardcoding True
                v
        strip_task_bodies() gated on check_execute_plan_patch() == 0  (sync.py:1380)

Once gsd-core PR #3687 ships (merged to `next`, unreleased on 1.11.0), the native step-dispatch
loop ALSO reaches plan:post and verify:post directly -- both paths then fire for those two points.
D-05's marker-grep probe (Pattern below) is what lets the hook detect this and skip/degrade safely.
```

### Recommended Project Structure

No new files/directories. All work lands inside the existing `plugins/beads-lifecycle/.gsd/capabilities/beads/` tree:
```
scripts/sync.py           # all four fixes land here
capability.json           # TRUTH-01: version bump 0.3.1 -> 0.4.0 (FIRST commit, per ROADMAP constraint),
                           #           values: ["authoritative","mirror"], description rewrite
tests/test_sync.py         # +D-09 --ship-md-path CLI test, +D-10 marker-version assertion,
                           #  +TRUTH-04 decimal-phase cases, +TRUTH-03 probe cases
GSD-CORE-PATCH.md          # TRUTH-03: document the version-probe mechanism and its revert condition
README.md / CHANGELOG.md / docs/prd-beads-capability.md / .beads/PRIME.md /
  plugins/beads-lifecycle/.agents/skills/beads/PRIME.md   # TRUTH-01 doc sweep (10 confirmed offender lines)
```

### Pattern 1: Table-driven patch checker (TRUTH-02)

**What:** Replace `check_shipmd_patch()` (`sync.py:2049-2111`) and `check_execute_plan_patch()` (`sync.py:2114-2177`) with one parameterized function driven by a small table of `(name, path_env_default, marker_constant, marker_version, consequence_message)` tuples.

**When to use:** Any time two functions differ only in constants and message strings, per this repo's own DRY threshold (3+ occurrences triggers abstraction per CLAUDE.md; here it's 2, but ~50 of ~78 total body lines are byte-identical, and D-10 requires a per-entry version field the current duplication has no home for).

**Constraint (verified, not assumed) — the markers are at different versions:**
```python
# Source: sync.py:110, :115 (read this session)
SHIP_MD_PATCH_MARKER = "<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->"
EXECUTE_PLAN_PATCH_MARKER = "<!-- gsd-beads-patch:execute-plan-bd-task-read v1 -->"
```
The unified table's schema must carry marker text AND a literal version label per entry (D-10) — a shared "current marker" field without a version discriminant loses the fact these are independently versioned patches (ROADMAP's "Edit the tracked source" constraint plus the release-hygiene note that `966315a` already bumped v1→v2 for ship.md alone).

**Example (skeleton, not verbatim source — no such table exists yet):**
```python
PATCH_CHECKS = {
    "ship-md": {
        "path_arg_default": None,  # resolves via CLAUDE_CONFIG_DIR env + "gsd-core/workflows/ship.md"
        "marker": SHIP_MD_PATCH_MARKER,
        "version": "v2",
        "missing_consequence": "the ship_override step will not fire",
    },
    "execute-plan": {
        "path_arg_default": None,  # resolves via CLAUDE_CONFIG_DIR env + "gsd-core/workflows/execute-plan.md"
        "marker": EXECUTE_PLAN_PATCH_MARKER,
        "version": "v1",
        "missing_consequence": "gsd-executor will not read task content from bd",
    },
}
```

### Pattern 2: Config self-read for behavior gating (TRUTH-01, TRUTH-03/D-06)

**What:** `sync.py` already has the exact reusable helper — no new plumbing needed.
```python
# Source: sync.py:641 (read this session)
def read_beads_config(project_root, key, default):
```
`read_epic_per()` (`:669-671`) and `read_beads_enabled()` (`:676`) are both one-line callers of this helper. TRUTH-01's `sync_mode` consumer and TRUTH-03/D-06's native-dispatch strip-gate consumer should follow the identical shape:
```python
# Modeled on sync.py:669-671, verified this session
def read_sync_mode(project_root):
    return read_beads_config(project_root, "sync_mode", "authoritative")
```

**Where D-06 wires in:** the native-dispatch CLI call site is `sync.py:2249`, currently:
```python
# Source: sync.py:2249 (read this session, exact line)
    if args.command == "create-issues":
        return create_issues(args.plan_path)
```
This is the ONLY site where `create_issues()` is invoked with its `allow_strip=True` default — confirmed by reading `beads-sync/SKILL.md` Step 3, which shells out `python3 .gsd/capabilities/beads/scripts/sync.py create-issues <PLAN.md path>` with no strip-related flag. TRUTH-03/D-06 requires this call site to compute `allow_strip` from `read_sync_mode(project_root) != "mirror"` rather than accept the hardcoded default.

**When to use:** any time a capability declares a `config` key — `capability.json`'s `config` block is schema/validator/default only (verified: no consumer of `configValues` reaches a `kind: "step"` entry), so every behavioral consumer must self-read.

### Anti-Patterns to Avoid

- **Wiring `sync_mode` through `configValues` or `when:`:** both are structurally unreachable for a `kind: "step"` skill (verified above) — do not attempt either, it will silently do nothing, reproducing exactly the bug TRUTH-01 exists to close.
- **Version-sniffing gsd-core for TRUTH-03:** CONTEXT.md D-05 explicitly forbids this; a stale/wrong version threshold fails silently and is exactly the failure class STACK.md was written to prevent.
- **`int()`/`float()`/`Decimal()` parsing for TRUTH-04:** CONTEXT.md D-07 is explicit — this is a **leading-zero strip**, not a numeric-type requirement. `int("01.5")` raises; the fix is string-level (`re.escape` + regex widening), matching the `sota-numerics` precedent exactly (see Code Examples below).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Decimal-phase-number matching | A new numeric parser/regex from scratch | The `sota-numerics` capability's already-fixed pattern, `re.compile(r"^\d+(?:\.\d+)?-\d+-PLAN\.md$")` (verified at `~/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:37`, comment at `:35` explicitly names beads' `^(\d{2}-\d{2})-PLAN\.md$` as "too narrow") | Exact same bug, already solved, in a sibling capability in the same install — reusing the fix avoids re-deriving the regex and matches the precedent CONTEXT.md/REQUIREMENTS.md both cite |
| Config-value validation on write | A hand-rolled enum checker inside `sync.py` | gsd-core's existing `config-set` validator — **verified live** (session-prior, re-confirmed by REQUIREMENTS.md's quoted transcript): `config-set beads.sync_mode bogus` returns `Error: Invalid beads.sync_mode 'bogus'. Valid values: authoritative, mirror, off` and does not write the value | `capability.json`'s declared `type: "enum"`/`values` already drives this — dropping `"off"` from `values` (TRUTH-01) is sufficient; no new validation code needed |
| Patch/marker detection scaffolding | A generic file-diffing or AST-based patch-presence detector | Simple substring `in` check against a version-labeled marker constant, exactly as both existing `check_*_patch` functions already do | The existing mechanism is proven (it caught the v1→v2 ship.md drift in commit `966315a`); a fancier detector adds surface area without adding correctness |

**Key insight:** every "don't hand-roll" item in this phase already has a working precedent inside this repo or a sibling capability install on the same machine — the entire phase is closing gaps between what's declared and what those existing precedents actually wire up, not inventing new mechanisms.

## Runtime State Inventory

This phase is a config/code-truth correction, not a rename/rebrand/migration in the traditional sense — but TRUTH-01's `sync_mode` change and TRUTH-02's CLI hard-break both have migration-adjacent characteristics. Explicit answers per category:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None.** `sync_mode` is read from `.planning/config.json` at call time, never cached or written by `sync.py` itself outside explicit `config-set` calls (which go through gsd-core's own config-writer, not this capability). No database/datastore holds a copy. | None |
| Live service config | **One found, requires explicit answer (D-04).** An existing project's `.planning/config.json` may already contain `"sync_mode": "off"` (or, post-implementation, would silently keep meaning nothing under the OLD code — but TRUTH-01 makes `mirror` live and drops `off` from the enum). A project with `"off"` on disk, after this phase ships, will hit `config-set`'s validator only on the NEXT explicit write; a pre-existing on-disk `"off"` is read back via `read_beads_config()`'s plain dict lookup with **no read-time validation** (confirmed: `parsed[key]` lookup, no enum re-check on read) — meaning `read_sync_mode()` would return the literal string `"off"`, which is not `"mirror"`, so `allow_strip=("off" != "mirror")` evaluates `True` — the OLD "off" project silently gets full authoritative-strip behavior post-upgrade, a behavior change with no notice. This is the exact channel PITFALLS.md's C1 finding warns about and the task's mandated "detection channel" analysis (below) addresses. | Code edit (D-04's migration answer) + a genuinely-hit notice channel, not a silent code-only fix |
| OS-registered state | **None.** No Task Scheduler/pm2/launchd/systemd registration references `sync_mode` or the CLI verb names by exact string. | None |
| Secrets/env vars | **None.** No SOPS key, `.env` entry, or CI/CD env var references `sync_mode` or `check-shipmd-patch`/`check-execute-plan-patch` by name. `CLAUDE_CONFIG_DIR` is read (defaults to `~/.claude`) but is a pre-existing, unrelated env var, not touched by this phase. | None |
| Build artifacts | **None found requiring action.** `capability.json`'s version bump (0.3.1 → 0.4.0, per ROADMAP's "Edit the tracked source" constraint) does NOT require a package reinstall — confirmed via PITFALLS.md C3's direct empirical test this session's predecessor: `capability update beads` was found unreliable (reports "upgraded" but copies nothing), so the ROADMAP's own mitigation (bump version in the FIRST commit, then run `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/` as a mechanical verification task) is the correct action, not a reinstall. | Verification task (`diff -rq`), not a reinstall |

## Detection Channel Analysis (TRUTH-01 criterion 3 — mandated empirical check)

Concrete channels a user with a stale/removed config value hits **without acting**, verified this session by reading gsd-core's own source directly:

1. **Unknown top-level-key warning — does NOT catch this.** `config-loader.cjs:728` (verified this session, corrected from PITFALLS.md's earlier `:727` citation — off by one line):
   ```js
   // Source: /home/dd/.claude/gsd-core/bin/lib/config-loader.cjs:728 (read this session)
   const unknownKeys = Object.keys(parsed).filter(k => !KNOWN_TOP_LEVEL.has(k));
   ```
   `Object.keys(parsed)` enumerates only the **top-level** keys of `.planning/config.json` (e.g. `"beads"`), never descends into `parsed.beads.sync_mode`. Since `"beads"` itself is a valid top-level key (declared via `capability.json`'s federated schema, folded into `KNOWN_TOP_LEVEL` at line 720), an orphaned or invalid `beads.sync_mode` value **never triggers this warning under any circumstance** — confirmed by reading the full 40-line surrounding block (`:695-744`).

2. **`validate health` — has no capability-config rule at all.** Verified this session: `find /home/dd/.claude/gsd-core -iname "*health*"` returns exactly `workflows/health.md`, `bin/lib/health-diagnostic.cjs`, `bin/lib/health-diagnostic-types.cjs`, and one rule file, `bin/lib/health-diagnostic-rules/worktree-health.cjs`. A repo-wide grep of `/home/dd/.claude/gsd-core/bin/lib/*.cjs` for `sync_mode` or `beads.` returns **zero matches** — gsd-core's own code has no awareness of this capability's config keys at all, confirming there is no health-check channel to rely on.

3. **`config-get` for a dropped/invalid key — returns the raw stored value, unvalidated.** `read_beads_config()` (`sync.py:641`, this capability's own reader, not a gsd-core primitive) does a plain dict lookup with a default fallback — no enum re-validation on read. gsd-core's own `config-get` CLI (not read by this capability at all) is a distinct code path; this capability never calls it, so it is not a relevant channel for `sync.py`'s own behavior, only for a human manually running `gsd-tools config-get beads.sync_mode`, which is an ACTED channel, not a passive one, and out of scope for this criterion.

**Conclusion:** there is genuinely no passive/unacted detection channel in gsd-core itself. The only channel a user hits without acting is whatever this phase builds: PITFALLS.md's proposed answer — a deprecation-notice check inside `sync.py`'s own `plan:pre` dispatch (already running unconditionally at that point via `lifecycle_dispatch`), printed through `hookSpecificOutput.additionalContext` (the same output channel the hook already uses) — is the only mechanism this repo has that a user encounters passively, once per phase-plan, without taking any action. This is a **capability-owned** notice, not a gsd-core one, and should be scoped narrowly: fire only when `read_sync_mode()` returns a value outside `["authoritative", "mirror"]` (i.e., only the removed `"off"` case, since `"mirror"` becomes valid and needs no notice).

## Common Pitfalls

### Pitfall 1: Silent orphan-value drift (TRUTH-01, D-04)
**What goes wrong:** A project with `"sync_mode": "off"` written to `.planning/config.json` before this phase ships silently changes behavior after the upgrade — `off` used to be inert (no code read it), and post-fix, an absent/invalid enum value falls through to whatever the D-04 migration code decides, with no read-time error to alert the user.
**Why it happens:** `read_beads_config()`'s dict lookup has no enum validation on read (confirmed, `sync.py:641` area) — only `config-set`'s write-time validator enforces the enum, and it never re-runs against values already on disk.
**How to avoid:** Implement the `plan:pre`-scoped notice described above (Detection Channel Analysis), scoped to fire only for values outside the new two-value enum.
**Warning signs:** A phase plans/executes with no bd issues created and no error, purely because `sync_mode` silently resolved to an unexpected fallback.

### Pitfall 2: Asymmetric test coverage hides a real regression (TRUTH-02, D-09)
**What goes wrong:** A unified CLI verb ships, the full 164-test suite stays green, but `beads-status/SKILL.md:146`'s `check-shipmd-patch` invocation silently breaks because the merge didn't preserve `--ship-md-path`'s flag spelling.
**Why it happens:** **Verified empirically this session** — `grep -c "ship-md-path\|ship_md_path" tests/test_sync.py` returns **zero matches** across the entire 4129-line test file, while `--execute-plan-path` has a dedicated CLI-level test at `tests/test_sync.py:3059-3072` (`test_cli_routes_through_main_and_returns_function_exit_code`). The suite can be 100% green and still miss this exact regression class.
**How to avoid:** D-09 requires adding the missing `--ship-md-path` CLI-level test BEFORE the merge lands, not after — so the merge itself is red/green-cycled against real coverage.
**Warning signs:** Any patch-checker refactor PR where the diff to `tests/test_sync.py` does not include a new `--ship-md-path`-flagged test case.

### Pitfall 3: Marker-version conflation (TRUTH-02, D-10)
**What goes wrong:** A shared table loses the fact the two markers are independently versioned (`v2` for ship.md, `v1` for execute-plan.md) — a future bump to one marker's version could accidentally get applied to both if the table schema doesn't carry a per-entry version field.
**Why it happens:** The two functions today hardcode their own version-labeled marker constant (`SHIP_MD_PATCH_MARKER` at `sync.py:110`, `EXECUTE_PLAN_PATCH_MARKER` at `sync.py:115`) and no test asserts the literal marker STRING (only presence/absence, not exact text) — confirmed by reading both constants directly this session.
**How to avoid:** D-10's per-entry version field (Pattern 1 above) plus a new test asserting the literal marker text for both entries.
**Warning signs:** A refactor PR that introduces one shared marker constant instead of two.

### Pitfall 4: Stale runtime mirror invalidates every behavioral claim (release-hygiene, PITFALLS.md C3)
**What goes wrong:** `.gsd/capabilities/beads/` (project-scope, gitignored, what actually executes) can silently diverge from `plugins/beads-lifecycle/.gsd/capabilities/beads/` (git-tracked source) — `capability update beads` was directly observed (prior session) reporting `"status": "upgraded"` while copying nothing.
**Why it happens:** The updater's no-op detection is keyed on the declared `capability.json` version string; editing `sync.py` without bumping the version leaves the updater believing nothing changed.
**How to avoid:** Bump `capability.json`'s version (0.3.1 → 0.4.0) in the FIRST commit touching `sync.py`, per ROADMAP's explicit constraint. **Verified this session:** the two trees are currently byte-identical (`diff -rq` returns empty as of this session's start) — this is a guard state, not yet proof of correct future syncing.
**Warning signs:** Any commit that edits `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` without also touching `capability.json`'s `version` field in the same commit.

## Code Examples

### TRUTH-04: decimal-phase regex widening (precedent, verified this session)
```python
# Source: ~/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:35-37 (read this session)
# Phase segment widened to `\d+(?:\.\d+)?` (RESEARCH: beads' own
# `^(\d{2}-\d{2})-PLAN\.md$` is too narrow) so both `11-01-PLAN.md` and
# `10.1-02-PLAN.md` match.
PLAN_FILE_RE = re.compile(r"^\d+(?:\.\d+)?-\d+-PLAN\.md$")
```
The two `int(phase_num)` call sites needing the D-07 leading-zero-strip fix instead of a type cast:
```python
# Source: sync.py:634 (read this session, exact text)
pattern = re.compile(rf"^###\s+(Phase\s+0*{int(phase_num)}\s*:.*)$", re.MULTILINE)
```
D-07's mandated fix: strip a leading `"0"` from the phase-number STRING (not `int()` it) and pass it through `re.escape()` before interpolating into the pattern — `re.escape` is called out as "non-negotiable" in CONTEXT.md because an un-escaped decimal phase number's `.` is a regex metacharacter that would match any character, not a literal dot.

### TRUTH-02: existing patch-checker shape to preserve (verified this session, exact source)
```python
# Source: sync.py:2049-2058 (read this session — full function is longer, showing the shape)
def check_shipmd_patch(ship_md_path_override=None):
    ...
    # three-case return: missing file -> 1, OSError/UnicodeDecodeError -> 1,
    # marker present -> print "...present (v2) at {path}" -> 0,
    # marker absent -> print warning naming what won't fire -> 1
```

### TRUTH-01: config self-read pattern to extend (verified this session, exact source)
```python
# Source: sync.py:669-671, :676 (read this session, exact text)
def read_epic_per(project_root):
    return read_beads_config(project_root, "epic_per", "phase")

def read_beads_enabled(project_root):
    return read_beads_config(project_root, "enabled", True)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| gsd-core dispatches `ship:pre` gates only via two hardcoded `capId` checks | Generic `kind == "gate"` enumeration loop, "Every other capId" arm | PR #3608, shipped v1.11.0 | Patch 1's step-8 half (gate dispatch) was already trimmed from this repo's local patch — confirmed in `GSD-CORE-PATCH.md:75-78`, no action needed this phase |
| gsd-core's hook-kind coverage validator checked only call-site TEXT presence | Validator checks that the call-site's dispatch text actually COVERS the hook's declared kind, per-point | PR #3687, merged to `next` 2026-08-19 (`ea59430`), unreleased on 1.11.0 | Closes the `plan:post`/`verify:post` `step`-kind gaps this repo's hook currently plugs — TRUTH-03's forward-compat probe must detect this once it ships to a release, not before |

**Deprecated/outdated:**
- The original `.planning/research/STACK.md`'s framing of PR #3687 as a dispatch-feature PR is a slight mischaracterization now correctable: it is a validator/scanner-fix PR (`fix(#3606)`) whose consumer-site rewrites happen to close the two step-dispatch gaps as a side effect. The functional conclusion (native `plan:post`/`verify:post` step dispatch lands once `next` releases) is unchanged and re-confirmed today.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | D-04's exact migration UX (a `plan:pre`-scoped notice via `hookSpecificOutput.additionalContext`, firing only for values outside `["authoritative","mirror"]`) is this research's recommendation, not a locked CONTEXT.md decision — CONTEXT.md leaves the shape to "Claude's discretion but must be stated explicitly." | Detection Channel Analysis, Pitfall 1 | If the planner picks a different shape (e.g., a one-time migration script instead of a recurring notice), the notice-channel design here is advisory, not binding — low risk, since the underlying empirical finding (no passive gsd-core channel exists) holds regardless of chosen UX |
| A2 | Review-state text on the PR #3687 GitHub page ("all three reviewers still listed as awaiting review" despite Merged status) is treated as a GitHub UI artifact, not evidence the merge is provisional or reversible. | Summary, State of the Art | Low — the page's own "Merged" badge and commit SHA are the authoritative status signal; stale review-request badges on merged PRs are a common GitHub UI behavior, not a functional ambiguity |

## Open Questions

1. **Exact shape of TRUTH-03/D-06's native-dispatch strip-gate change**
   - What we know: the call site is confirmed exactly (`sync.py:2249`, `create_issues(args.plan_path)`, currently always `allow_strip=True` by default), and the config-read helper pattern to extend is confirmed (`read_beads_config`, `sync.py:641`).
   - What's unclear: whether the planner should add a new `--allow-strip`/`--no-strip` CLI flag to the `create-issues` subparser (giving `beads-sync/SKILL.md` explicit control) or have `main()`'s dispatch branch compute the flag internally from `read_sync_mode()` with no new CLI surface. CONTEXT.md's D-06 states the outcome ("native dispatch trusted, sync_mode governs strip") but not this implementation choice.
   - Recommendation: prefer the no-new-CLI-surface option (computing internally at `main()`'s dispatch line) — it requires zero change to `beads-sync/SKILL.md`'s Step 3 invocation and keeps the CLI surface area from growing, consistent with the ponytail-ladder "does this need to exist at all" check; a CLI flag adds an untested cross-product (flag present vs. absent vs. config value) for no consumer that needs it today.

2. **Whether TRUTH-03's marker-grep probe should live inside the unified TRUTH-02 patch-checker table or as a separate, third function**
   - What we know: D-05's probe targets `plan-phase.md`/`verify-work.md` (gsd-core's OWN installed workflow files, generic-dispatch text), which is architecturally distinct from Patch 1/Patch 2's targets (`ship.md`/`execute-plan.md`, this repo's OWN local patches).
   - What's unclear: whether reusing TRUTH-02's table schema for a conceptually different kind of probe (detecting upstream native capability, not detecting local-patch survival) is cohesion or conflation.
   - Recommendation: keep it a separate function — the table in Pattern 1 is scoped to "does our local patch still exist," while D-05's probe answers "does upstream now do this natively." Different questions, different failure-mode semantics (local-patch-missing is bad; upstream-now-native is good) — sharing a table risks a misleading unified pass/fail semantic.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All four requirements (`sync.py` is pure stdlib) | Yes (confirmed — test suite ran) | System python3, exact version not pinned by this phase | — |
| gsd-core install | TRUTH-03 (probe targets `$HOME/.claude/gsd-core/workflows/*.md`) | Yes, confirmed at `/home/dd/.claude/gsd-core/`, version 1.11.0 stack per `.planning/research/STACK.md` | 1.11.0 (`next` branch has PR #3687, unreleased) | — |
| `sota-numerics` capability install | TRUTH-04 precedent reference only, not a runtime dependency | Yes, confirmed at `~/.gsd/capabilities/sota-numerics/` | n/a — read-only reference | Not needed at runtime; the pattern is copied, not imported |
| Network access (GitHub) | Fresh PR #3687 status check (this research session only, not runtime) | Yes — WebFetch succeeded against `github.com/open-gsd/gsd-core/pull/3687` | — | — |

**Missing dependencies with no fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Python stdlib `unittest`, discover mode |
| Config file | none — directory convention (`tests/`) |
| Quick run command | `cd plugins/beads-lifecycle/.gsd/capabilities/beads && python3 -m unittest discover -s tests -t tests` |
| Full suite command | same command — single suite, no split unit/integration tiers |

**Baseline (verified this session, re-run):** `Ran 164 tests in 4.792s / OK` — exact match to ROADMAP.md's cited baseline, zero drift. `tests/test_sync.py` is 4129 lines, the sole test file besides `tests/fixtures/`.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRUTH-04 | `PLAN_FILE_RE` matches decimal phase filenames (`"01.5-01-PLAN.md"`) | unit | `python3 -m unittest tests.test_sync -k decimal_phase -v` (new test names, pattern TBD by planner) | ❌ Wave 0 — no decimal-phase test case exists yet |
| TRUTH-04 | `get_phase_header`/`extract_phase_mentions` do not raise `ValueError` on `"01.5"` | unit | same file, new cases | ❌ Wave 0 |
| TRUTH-03 | Hook probe correctly detects upstream native dispatch presence/absence at `plan:post`/`verify:post` | unit | new test module or new cases in `tests/test_sync.py` | ❌ Wave 0 |
| TRUTH-03 | Native-dispatch call site (`sync.py:2249`) honors `sync_mode` for `allow_strip` | unit | new cases in `tests/test_sync.py` | ❌ Wave 0 |
| TRUTH-01 | `sync_mode` enum values reduced to `["authoritative","mirror"]`; `mirror` behaves identically to today's `allow_strip=False` hook path | unit | new cases in `tests/test_sync.py` | ❌ Wave 0 |
| TRUTH-01 | Detection-channel notice fires for an on-disk `"off"` value | unit | new cases in `tests/test_sync.py` | ❌ Wave 0 |
| TRUTH-02 | Unified CLI verb preserves `--ship-md-path` flag spelling and behavior | unit (CLI-level, `sync.main([...])`) | `python3 -m unittest tests.test_sync -k ship_md_path -v` | ❌ Wave 0 — **confirmed empirically this session: zero existing coverage** |
| TRUTH-02 | Unified CLI verb preserves `--execute-plan-path` flag spelling and behavior | unit (CLI-level) | existing test at `tests/test_sync.py:3059-3072` (`test_cli_routes_through_main_and_returns_function_exit_code`) | ✅ exists — must still pass post-merge |
| TRUTH-02 | Marker version field asserted per entry (D-10) | unit | new cases in `tests/test_sync.py` | ❌ Wave 0 — no test today asserts the literal marker STRING, only presence/absence |

### Sampling Rate
- **Per task commit:** `python3 -m unittest discover -s tests -t tests` (full suite — the whole suite already runs in under 5 seconds, no quick/full split is warranted)
- **Per wave merge:** same full-suite command, plus `diff -rq .gsd/capabilities/beads/ plugins/beads-lifecycle/.gsd/capabilities/beads/` (release-hygiene / PITFALLS.md C3 guard, only meaningful once the version bump has landed)
- **Phase gate:** full suite green AND test count `>= 164` (growing past the current baseline is itself part of REQUIREMENTS' success criteria) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_sync.py` — add `--ship-md-path` CLI-level test (D-09, must land BEFORE the TRUTH-02 merge, not after)
- [ ] `tests/test_sync.py` — add decimal-phase-number test cases (TRUTH-04)
- [ ] `tests/test_sync.py` — add marker-version literal-string assertions for both patch entries (D-10)
- [ ] `tests/test_sync.py` — add TRUTH-03 probe test cases (both the upstream-native-detection logic and the `allow_strip`/`sync_mode` gating at the native `create-issues` call site)
- [ ] `tests/test_sync.py` — add TRUTH-01 `sync_mode` enum-narrowing and detection-channel-notice test cases
- No new test framework or fixture directory needed — `tests/fixtures/` already exists and the existing `unittest` harness covers every phase requirement's test TYPE (all are unit-level, no integration/e2e infrastructure gap)

## Security Domain

`security_asvs_level: 1`, `security_block_on: "high"` (confirmed from `.planning/config.json`).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | This phase touches no auth surface |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Yes | Regex-based phase-number parsing (TRUTH-04) and marker/config-string matching (TRUTH-01/02/03) — all inputs are either filesystem paths under project control or `.planning/config.json` values already gated by gsd-core's own `config-set` enum validator |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| ReDoS via unbounded/nested regex quantifiers in the widened decimal-phase pattern | Denial of Service | The `sota-numerics` precedent pattern `\d+(?:\.\d+)?-\d+-PLAN\.md$` is anchored, has no nested quantifiers, and no catastrophic-backtracking shape — confirmed by direct read of the precedent file, which explicitly documents this discipline: "Anchored, bounded, no nested quantifiers (ReDoS mitigation)" (`check-alternatives.py`, comment preceding `SECTION_HEADING_RE`). Reuse the same discipline for TRUTH-04's fix. |
| Regex metacharacter injection via un-escaped phase-number interpolation | Tampering | `re.escape()` on the phase-number string before interpolating into any pattern — CONTEXT.md D-07 already mandates this as "non-negotiable"; a decimal phase number's literal `.` is a regex metacharacter (matches any char) if not escaped, which could cause `get_phase_header`/`extract_phase_mentions` to match the wrong phase header |
| Shell/argv injection via marker or config-derived strings reaching `subprocess` | Tampering | Not newly introduced by this phase — `beads-sync/SKILL.md`'s existing Anti-Patterns section already states the invariant: "every `bd` call is a typed argv list passed to `subprocess.run([...])` with shell execution left disabled" (verified, read this session) — none of TRUTH-01/02/03/04's changes touch `subprocess` call construction, so no new surface here |

## Sources

### Primary (HIGH confidence — read directly this session)
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` — full re-verification of every ROADMAP-cited line (`:72, :110, :115, :634, :641, :669-671, :676, :679-758, :1291-1303, :1380, :2049-2111, :2114-2177, :2180-2266, :2249`), no drift found
- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` — lines 1-56, exact `sync_mode` enum/description text
- `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` — full 243-line read, both patches' upstream tracking, revert conditions, marker content
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md` — full read, confirms native-dispatch call site has no `--allow-strip` CLI surface today
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` — grepped/read for `--ship-md-path`/`--execute-plan-path` coverage counts and exact test line range
- `/home/dd/.claude/gsd-core/bin/lib/config-loader.cjs:695-744` — direct read, confirms unknown-key warning is top-level-only, corrects PITFALLS.md's `:727` citation to `:728`
- `/home/dd/.claude/gsd-core/bin/lib/health-diagnostic-rules/` — directory listing, confirms no capability-config health rule exists
- `~/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:1-60` — direct read, decimal-phase regex precedent, exact line numbers
- `github.com/open-gsd/gsd-core/pull/3687` — WebFetch, fresh 2026-08-20 verification, confirmed Merged to `next`, commit `ea59430`
- `git log` on `.planning/milestones/v1.1-phases/` — confirms `10.1-*` and `11.1-*` decimal-phase directories exist in this repo's own history

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/FEATURES.md`, `.planning/research/PITFALLS.md` — prior-phase research docs, read in full in an earlier part of this session; findings cross-checked against fresh reads where load-bearing for this phase's four requirements (config-loader.cjs line correction above being the one delta found)

### Tertiary (LOW confidence)
- None — every claim in this document is either a direct file read this session or a cross-checked citation from prior-session research

## Metadata

**Confidence breakdown:**
- Standard stack: N/A (no new stack) — HIGH, no packages to verify
- Architecture: HIGH — every call site and every architectural claim (configValues/when:/config-equals unreachability, native-dispatch call site, hook hardcoding) verified by direct read this session
- Pitfalls: HIGH — all four pitfalls trace to a specific, re-read source location; the two empirical gaps (no `--ship-md-path` test, config-loader.cjs off-by-one) were independently re-confirmed, not carried over from prior research uncritically

**Research date:** 2026-08-20
**Valid until:** 7 days (fast-moving: TRUTH-03 is time-boxed by an upstream PR that could ship to a release at any point; re-verify PR #3687's release status immediately before this phase's execution if more than a few days pass)
