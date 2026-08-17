# Phase 11: sota-numerics capability plugin - Pattern Map

**Mapped:** 2026-08-17
**Files analyzed:** 14 (new plugin bundle) + 1 (dogfood copy, byte-identical to bundle) + 1 (marketplace.json edit)
**Analogs found:** 14 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `sota-numerics/.claude-plugin/plugin.json` | config | request-response (manifest, no runtime flow) | `ponytail-everywhere/.claude-plugin/plugin.json` | exact |
| `sota-numerics/.gsd/capabilities/sota-numerics/capability.json` | config | event-driven (lifecycle-point dispatch) | `.gsd/capabilities/ponytail/capability.json` for contributions shape; `.gsd/capabilities/beads/capability.json` for `gates[]` shape | role-match (composite: no single analog covers both contributions AND a gate) |
| `sota-numerics/.gsd/capabilities/sota-numerics/fragments/planner-sota.md` | component (prompt fragment) | transform (static text → rendered into planner prompt) | `.gsd/capabilities/ponytail/fragments/planner-ladder.md` | exact |
| `sota-numerics/.gsd/capabilities/sota-numerics/fragments/executor-numerics.md` | component (prompt fragment) | transform | `.gsd/capabilities/ponytail/fragments/executor-ladder.md` | exact |
| `sota-numerics/.gsd/capabilities/sota-numerics/fragments/verifier-precision.md` | component (prompt fragment) | transform | `.gsd/capabilities/ponytail/fragments/verifier-ladder.md` | exact |
| `sota-numerics/.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md` | component (prompt fragment) | transform | `.gsd/capabilities/beads/fragments/recall-pointer.md` (only existing single-audience advisory fragment; ponytail has no `ship:pre` fragment to copy) | role-match |
| `sota-numerics/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` | utility (gate predicate script) | batch (glob `*-PLAN.md`, validate, exit 0/1) | `.gsd/capabilities/beads/scripts/sync.py` (stdlib-only Python conventions: `argparse`, `confined()`/`find_project_root()` path-safety, bounded `subprocess` timeouts, frontmatter regex parsing) — no existing `command-exit-zero` script analog in this repo, this is genuinely new plumbing | role-match (conventions only; no gate-script precedent exists) |
| `sota-numerics/hooks/hooks.json` | config | event-driven | `ponytail-everywhere/hooks/hooks.json` | exact |
| `sota-numerics/hooks/session-start.sh` | middleware (SessionStart hook) | event-driven | `ponytail-everywhere/hooks/session-start.sh` | exact |
| `sota-numerics/hooks/capability-auto-install.sh` | middleware (auto-install) | event-driven | `ponytail-everywhere/hooks/capability-auto-install.sh` (byte-identical vendored copy, Phase 10.1 D-05 pattern — do not modify, only substitute nothing, `CAP_ID` is passed as an argv, not hardcoded in the script) | exact |
| `sota-numerics/hooks/gsd-tools.sh` | utility (config resolver) | request-response | `ponytail-everywhere/hooks/gsd-tools.sh` | exact |
| `sota-numerics/tests/test-check-alternatives.{sh,py}` | test | batch | `.gsd/capabilities/beads/tests/test_sync.py` (stdlib `unittest`, `sys.path.insert` to import script under test, fixtures dir pattern) and `ponytail-everywhere/tests/test-session-start.sh` (stdlib-only bash scratch-dir smoke test pattern, if a shell-level hook test is also needed) | role-match |
| `sota-numerics/tests/fixtures/*.md` (compliant/non-compliant/exempt/multi-plan PLAN.md fixtures) | test (fixture) | file-I/O | `.gsd/capabilities/beads/tests/fixtures/plan-wave-a.md` + `plan-wave-b.md` (multi-plan-per-phase fixture pair), `plan-single.md` | exact |
| `.claude-plugin/marketplace.json` (modified, not new) | config | request-response | itself — add third `plugins[]` entry mirroring the existing `ponytail-everywhere` entry | exact |
| `.gsd/capabilities/sota-numerics/` (repo-root dogfood copy, D-04) | config (deployment, not new source) | event-driven | `.gsd/capabilities/beads/` + `.gsd/capabilities/ponytail/` (both already dogfooded at repo root alongside their plugin-dir originals) | exact |

## Pattern Assignments

### `sota-numerics/.claude-plugin/plugin.json` (config)

**Analog:** `ponytail-everywhere/.claude-plugin/plugin.json`

**Full pattern** (verbatim structure to copy, values changed):
```json
{
  "name": "sota-numerics",
  "version": "0.1.0",
  "description": "<one-line advisory+gate description>",
  "author": {
    "name": "Dennis A. V. Dittrich",
    "email": "davdittrich@gmail.com"
  },
  "license": "MIT"
}
```
Note: `beads-lifecycle`'s root `plugin.json` additionally carries `"skills": ["./.agents/skills/beads"]` — sota-numerics has no top-level skills directory (its logic lives in `scripts/`, not `skills/`), so omit that key, matching ponytail's shape exactly, not beads'.

---

### `sota-numerics/.gsd/capabilities/sota-numerics/capability.json` (config)

**Analogs:** `.gsd/capabilities/ponytail/capability.json` (contributions/config shape) + `.gsd/capabilities/beads/capability.json` (gates shape)

**Top-level manifest fields** (from ponytail, lines 1-20):
```json
{
  "id": "sota-numerics",
  "role": "feature",
  "version": "0.1.0",
  "title": "SOTA/efficiency/numerical-stability steering",
  "description": "...",
  "tier": "full",
  "requires": [],
  "engines": { "gsd": ">=1.10.0" },
  "runtimeCompat": { "supported": ["*"], "unsupported": [] },
  "skills": [],
  "agents": [],
  "hooks": []
}
```

**Config block pattern** — single boolean key per D-11 (ponytail's two-key `config` block is the shape to follow, but sota-numerics needs only one key):
```json
"config": {
  "sota-numerics.enabled": {
    "type": "boolean",
    "default": true,
    "description": "Master toggle for both the advisory steering fragments and the blocking plan:post Alternatives Considered gate (D-10, D-11)."
  }
}
```

**Contributions pattern** (copy ponytail's four-entry shape verbatim, one entry per D-12 lifecycle point — `point`/`into`/`fragment.path`/`when`/`onError` fields, no `configValues` needed since there is no intensity knob per D-11):
```json
"contributions": [
  {
    "point": "plan:pre",
    "into": "planner",
    "produces": [],
    "consumes": [],
    "fragment": { "path": "fragments/planner-sota.md" },
    "when": "sota-numerics.enabled",
    "onError": "skip"
  },
  {
    "point": "execute:wave:pre",
    "into": "executor",
    "produces": [],
    "consumes": [],
    "fragment": { "path": "fragments/executor-numerics.md" },
    "when": "sota-numerics.enabled",
    "onError": "skip"
  },
  {
    "point": "execute:wave:post",
    "into": "verifier",
    "produces": [],
    "consumes": [],
    "fragment": { "path": "fragments/verifier-precision.md" },
    "when": "sota-numerics.enabled",
    "onError": "skip"
  },
  {
    "point": "ship:pre",
    "into": "orchestrator",
    "produces": [],
    "consumes": [],
    "fragment": { "path": "fragments/ship-precision-advisory.md" },
    "when": "sota-numerics.enabled",
    "onError": "skip"
  }
]
```
Note: `into: "orchestrator"` for the `ship:pre` advisory fragment — RESEARCH.md's Architecture Patterns confirm `ship:pre` contribution rendering is an existing generic call site (unlike the checker-spot-check channel); verify the exact `into` value gsd-core expects at `ship:pre` against `loop-host-contract.cjs`'s `agentRoles` for the `ship` step before finalizing (not traced in this pattern pass — flag for the planner).

**Gate pattern** — structurally modeled on beads' `gates[]` array shape (point/check/when/blocking/onError fields) but with a **different predicate kind**, per RESEARCH.md Pattern 1/Pitfall 2 (verified against `gate-predicate-evaluator.cjs`, not the beads example — beads' own `artifact-frontmatter-equals` example is the wrong predicate kind for this gate's needs):
```json
"gates": [
  {
    "point": "plan:post",
    "check": {
      "predicate": {
        "kind": "command-exit-zero",
        "command": "python3 \"${CLAUDE_PLUGIN_ROOT:-.}/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py\" \"${PHASE_DIR}\"",
        "timeout": 30
      }
    },
    "when": "sota-numerics.enabled",
    "blocking": true,
    "onError": "halt"
  }
]
```
Critical divergence from every existing gate in this repo (beads' two `ship:pre` gates both use `onError: "skip"`): this gate must NOT be `onError: "skip"` — CONTEXT.md's Established Patterns section explicitly calls out that a blocking gate with fail-open `onError` "would defeat its own purpose" and flags this as a deliberate divergence to document, not silently "fix" back to skip.

---

### `sota-numerics/.gsd/capabilities/sota-numerics/fragments/planner-sota.md` (component, transform)

**Analog:** `.gsd/capabilities/ponytail/fragments/planner-ladder.md` (full text, 4 lines):
```
Ponytail lazy-ladder discipline for planning (advisory, not a gate).
Pick the laziest viable task shape: fewest files, fewest new artifacts, drop tasks whose need is speculative — do not plan an abstraction with a single implementation or scaffolding built "for later."
At the resolved ponytail.level: lite applies rungs 1-2 only (does this need to exist at all, is it already in this codebase); full climbs the whole ladder — stdlib, then a native platform feature, then an already-installed dependency, before anything new; ultra also prefers deleting existing code over adding new code.
Never simplify away input validation at trust boundaries, error handling that prevents data loss, security controls, accessibility basics, or anything explicitly requested.
```
**Structure to copy:** short (3-5 line) plain-prose fragment, line 1 states "advisory, not a gate" (or, for this capability's plan:pre point specifically, note that the *later* plan:post gate DOES block — this is the one fragment where the "advisory only" framing must be qualified, since D-12 pairs it with a real blocking gate later in the same lifecycle point sequence). Content per D-12/D-13: SOTA-research framing — "before writing PLAN.md, identify 2+ current alternatives per non-trivial mechanism choice, with citations carrying a discoverable date, and name which ranked criterion (performance > simplicity/LOC > ecosystem > maintenance) decided each pick" (mirrors CLAUDE.md's Alternatives Mandatory / SOTA Verification / Mechanism Justification sections verbatim per CONTEXT.md canonical_refs).

---

### `sota-numerics/.gsd/capabilities/sota-numerics/fragments/executor-numerics.md` (component, transform)

**Analog:** `.gsd/capabilities/ponytail/fragments/executor-ladder.md` — same 4-line shape, framing swapped to numerical-stability/no-cancellation per D-12 ("derive numeric parameters from first principles, avoid cancellation and error propagation, prefer stable algorithms over convenient ones — mirrors CLAUDE.md's global 'SOTA, elegant, mathematic correctness... no cancelations, avoid propagation of errors' rule").

---

### `sota-numerics/.gsd/capabilities/sota-numerics/fragments/verifier-precision.md` (component, transform)

**Analog:** `.gsd/capabilities/ponytail/fragments/verifier-ladder.md` — same shape, framing swapped: "flag unjustified simplification or precision loss as findings, not blockers (D-12) — this capability declares its only gate at plan:post, not here."

---

### `sota-numerics/.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md` (component, transform)

**Analog:** `.gsd/capabilities/beads/fragments/recall-pointer.md` (structural precedent for a single-purpose pointer/advisory fragment, 5 lines) — content framing per D-12/D-13 instead follows ponytail's verifier-ladder tone (advisory, no gate): "confirm precision/efficiency claims before shipping — this capability declares no ship:pre gate (advisory only, D-12)."

---

### `sota-numerics/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (utility, batch)

**Analog:** `.gsd/capabilities/beads/scripts/sync.py` — no existing `command-exit-zero` gate script exists anywhere in this repo to copy wholesale; this file is genuinely new logic, but must follow `sync.py`'s established stdlib-only security/reliability conventions:

**Path confinement pattern** (`sync.py` lines 116-139):
```python
def find_project_root(start):
    """Walk up from `start` to the nearest ancestor containing `.planning/`."""
    current = start.resolve()
    for _ in range(10):
        if (current / ".planning").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise ValueError(f"could not locate a .planning/ ancestor above {start}")

def confined(root, *parts):
    """Join parts onto root and reject any resolved escape (T-01-02)."""
    candidate = root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError(f"path escapes project root: {candidate} not under {root}")
    return candidate
```
Apply the same pattern to `check-alternatives.py`'s `${PHASE_DIR}` argument — never trust it unconfined before globbing.

**Frontmatter/regex extraction pattern** (`sync.py` lines 30, 149-150):
```python
FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
# ...
fm_match = FRONTMATTER_RE.match(text)
frontmatter = fm_match.group(1) if fm_match else ""
```
Reuse this exact regex shape for locating each `*-PLAN.md`'s `## Alternatives Considered` section — anchor on the markdown heading the same way `TASK_RE`/`NAME_RE` anchor on XML-ish tags elsewhere in `sync.py`.

**Multi-file glob pattern** (`sync.py`'s `discover_plan_files`, lines 369-381 — adapt the *pattern*, not the exact regex, since this script targets `*-PLAN.md` broadly rather than the strict `NN-NN-PLAN.md` beads uses):
```python
PLAN_FILE_RE = re.compile(r"^(\d{2}-\d{2})-PLAN\.md$")

def discover_plan_files(phase_dir):
    discovered = {}
    for candidate in Path(phase_dir).iterdir():
        m = PLAN_FILE_RE.match(candidate.name)
        if m:
            discovered[m.group(1)] = candidate
    return discovered
```
This is the concrete fix for RESEARCH.md Pitfall 3/Pattern 3 (the multi-plan-per-phase coverage requirement) — glob and loop over every match, never take `readdir`'s first hit.

**Exit-code contract** (new, no existing analog — `sync.py`'s functions all `return 0` and print, since they feed `onError: "skip"` steps; `check-alternatives.py` is different: it must actually distinguish pass/fail via process exit code for `command-exit-zero` to read):
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase_dir")
    args = parser.parse_args()
    violations = validate_all_plans(args.phase_dir)  # returns list of (plan_path, reason) tuples
    if violations:
        for plan_path, reason in violations:
            print(f"{plan_path}: {reason}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
```
Follow `sync.py`'s `argparse` top-level dispatch pattern (not shown above in full but present at module bottom, not read this pass — grep `argparse.ArgumentParser` in `sync.py` at implementation time) for consistency if multiple subcommands end up needed.

**Security note (ASVS V5, carried from RESEARCH.md):** never `eval`/shell out on content read FROM a PLAN.md body (citation URLs, dated text) — treat all PLAN.md content as untrusted input when parsing, exactly as `sync.py`'s own docstring states for `bd` argv construction (T-01-01). Bounded, anchored, non-nested-quantifier regex only for date/URL heuristics (ReDoS mitigation).

---

### `sota-numerics/hooks/hooks.json` (config, event-driven)

**Analog:** `ponytail-everywhere/hooks/hooks.json` (full file, copy verbatim structure, only `session-start.sh` command string needs no changes since `${CLAUDE_PLUGIN_ROOT}` is resolved per-plugin already):
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          { "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"" }
        ]
      }
    ],
    "SubagentStart": [
      {
        "matcher": "gsd-planner",
        "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\" planner" }]
      },
      {
        "matcher": "gsd-executor",
        "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\" executor" }]
      },
      {
        "matcher": "gsd-verifier",
        "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\" verifier" }]
      }
    ]
  }
}
```
No `ship:pre`/checker-role SubagentStart matcher exists in ponytail's example — if sota-numerics needs a `SubagentStart` matcher for `gsd-plan-checker` (D-08's citation spot-check, if the core-patch route is taken), this is new territory requiring a new matcher entry, not copyable.

---

### `sota-numerics/hooks/session-start.sh` (middleware, event-driven)

**Analog:** `ponytail-everywhere/hooks/session-start.sh` (full file, 72 lines) — copy verbatim, substitute `ponytail` → `sota-numerics`, `ponytail.enabled`/`ponytail.level` → `sota-numerics.enabled` (drop the `.level` config-read block entirely per D-11, no intensity knob), and swap the four `FRAMING`/`RUNGS`/`BODY` case-statement strings for sota-numerics' own banner text. Key structural pieces to preserve exactly:

**Auto-install + config-read pattern** (lines 1-27):
```bash
#!/usr/bin/env bash
set -u
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
bash "$PLUGIN_ROOT/hooks/capability-auto-install.sh" sota-numerics || true
if [ -f "$PLUGIN_ROOT/hooks/gsd-tools.sh" ]; then
  . "$PLUGIN_ROOT/hooks/gsd-tools.sh"
  ENABLED="$(gsd_tools config-get sota-numerics.enabled --default true 2>/dev/null)"; ENABLED_STATUS=$?
  if [ "$ENABLED_STATUS" -eq 127 ]; then
    ENABLED=true
  elif [ "$ENABLED_STATUS" -ne 0 ]; then
    echo "sota-numerics: gsd_tools config-get sota-numerics.enabled failed (exit $ENABLED_STATUS); disabling advisory banner" >&2
    ENABLED=false
  fi
else
  ENABLED=true
fi
ENABLED="$(printf '%s' "$ENABLED" | tr -d '"')"
if [ "$ENABLED" != "true" ]; then
  exit 0
fi
```

**Role-dispatch pattern** (lines 38-49, same `case "$ROLE"` shape, swap FRAMING text per D-13's stage-tailored wording):
```bash
ROLE="${1:-}"
case "$ROLE" in
  planner|executor|verifier) ;;
  *) ROLE=generic ;;
esac
case "$ROLE" in
  planner) FRAMING='...SOTA-research framing...' ;;
  executor) FRAMING='...numerical-stability/no-cancellation framing...' ;;
  verifier) FRAMING='...flag unjustified simplification/precision loss framing...' ;;
  *) FRAMING='...' ;;
esac
```

**Fail-safe injection guard (T-10-01 precedent, tested by ponytail's test case 4):** any config value used inside a `case` statement must fall through to a safe default on an unrecognized/injection-shaped value — never `eval` a config-sourced string.

---

### `sota-numerics/hooks/capability-auto-install.sh` and `sota-numerics/hooks/gsd-tools.sh` (middleware/utility, event-driven)

**Analogs:** `ponytail-everywhere/hooks/capability-auto-install.sh` (99 lines) and `ponytail-everywhere/hooks/gsd-tools.sh` (18 lines) — **byte-identical vendored copies**, per Phase 10.1 D-05 and CONTEXT.md's Reusable Assets. Do not parametrize or modify: `CAP_ID` is already passed as `$1` from the caller (`session-start.sh`), and the script's own `[[ "$CAP_ID" =~ ^[a-z][a-z0-9-]*$ ]]` guard (line 15) already accepts `sota-numerics` cleanly (confirmed in RESEARCH.md Pitfall 4). Copy the files unchanged, do not edit a single line.

---

### `sota-numerics/tests/test-check-alternatives.{sh,py}` (test, batch)

**Analogs:**
- `.gsd/capabilities/beads/tests/test_sync.py` (stdlib `unittest`, import-under-test pattern, lines 1-20):
```python
"""Tests for .../scripts/check-alternatives.py. Stdlib unittest only (N5)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_alternatives  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
```
- `ponytail-everywhere/tests/test-session-start.sh` (stdlib-only bash smoke-test pattern, scratch-dir isolation, `mk_scratch`/`fail`/`pass` helpers, lines 1-30) — use this shape if a shell-level `session-start.sh` smoke test is also needed (mirrors ponytail's own `.enabled` default-true coverage, D-10).

**Test coverage required** (from RESEARCH.md's Phase Requirements → Test Map, directly actionable):
- D-01/D-06/D-07/D-09/min-count: blocks a PLAN.md with <2 cited+dated alternatives, no ranked criterion.
- D-03: accepts literal `"N/A — no mechanism choice"` exemption text.
- D-10: `sota-numerics.enabled` defaults `true` at fresh install (scratch-dir case, no config present).
- Multi-plan coverage (RESEARCH Pattern 3): a phase with 2+ `*-PLAN.md` files — gate must check ALL, not just the first `readdir` match.

---

### `sota-numerics/tests/fixtures/*.md` (test fixture, file-I/O)

**Analogs:** `.gsd/capabilities/beads/tests/fixtures/plan-wave-a.md` + `plan-wave-b.md` (multi-plan-in-one-phase fixture pair — copy this pairing pattern for the multi-plan-coverage test) and `plan-single.md` (single-plan minimal fixture). Build four new fixtures: one compliant (2+ cited+dated alternatives, ranked criterion named), one non-compliant (missing citation/date/criterion), one D-03-exempt (`"N/A — no mechanism choice"`), one multi-plan pair mirroring `plan-wave-a.md`/`plan-wave-b.md`'s two-file shape.

---

### `.claude-plugin/marketplace.json` (config, modified not new)

**Analog:** itself — append a third `plugins[]` entry mirroring the existing `ponytail-everywhere` entry exactly (full current file content, 3 entries → target):
```json
{
  "name": "sota-numerics",
  "source": "./sota-numerics",
  "description": "SOTA-verification, efficiency, and numerical-stability steering with a blocking plan:post Alternatives Considered gate"
}
```
Append after the existing `ponytail-everywhere` entry (index 2, zero-based) inside the `plugins` array — do not reorder or touch the `beads-lifecycle`/`ponytail-everywhere` entries.

---

## Shared Patterns

### Vendored auto-install (byte-identical, no modification)
**Source:** `ponytail-everywhere/hooks/capability-auto-install.sh`, `ponytail-everywhere/hooks/gsd-tools.sh`
**Apply to:** `sota-numerics/hooks/capability-auto-install.sh`, `sota-numerics/hooks/gsd-tools.sh`
Copy verbatim, zero edits — Phase 10.1 D-05's per-plugin vendoring already proven working for two capabilities; a third `CAP_ID` argument is the only variable, and it's supplied by the caller, not hardcoded in these files.

### `onError: "skip"` fail-open, EXCEPT the blocking gate itself
**Source:** every existing `steps[]`/`contributions[]` entry in `beads`/`ponytail` `capability.json` (all `onError: "skip"`)
**Apply to:** all four `contributions[]` entries in `sota-numerics/capability.json` — use `onError: "skip"`.
**Deliberate divergence:** the `plan:post` gate itself must use `onError: "halt"` (or otherwise not silently skip on command failure) — CONTEXT.md's Established Patterns section explicitly flags this as intentional, not an oversight to "fix" later. Document this divergence in the plan text itself.

### Two-step gate contract (read, do not reinvent)
**Source:** RESEARCH.md's verified excerpt of `~/.claude/gsd-core/workflows/plan-phase.md:1369-1379`
**Apply to:** the `check-alternatives.py` script's exit-code semantics and the gate's `check.predicate` declaration — Step 1 is command-success (script's own exit code + valid stdout), Step 2 is `GATE_RESULT.block` (derived from that exit code by the generic `command-exit-zero` evaluator, not by the script itself). Do not hand-roll a JSON `GATE_RESULT` output from the script — `evaluateCommandExitZero` (verified in RESEARCH.md's Code Examples) derives `block` purely from the process exit code, exit 0 = pass, non-zero = block.

### Path confinement / untrusted-content handling
**Source:** `.gsd/capabilities/beads/scripts/sync.py`'s `find_project_root`/`confined` (T-01-02 threat model) and its module docstring's N4/T-01-01 rule ("PLAN.md text is authored by a different principal... no `bd` command is ever assembled as a shell string")
**Apply to:** `check-alternatives.py` — confine all path joins to the resolved phase directory; never `eval`/shell-interpolate content read from a `PLAN.md` body (citation text, dates) when constructing the gate's own subprocess calls (there should be none needed — this script only reads and regex-matches, it does not shell out).

## No Analog Found

None — every planned file has at least a role-match analog in the `beads`/`ponytail` bundles per the classification table above. The one file with the weakest analog coverage is `check-alternatives.py` (no existing `command-exit-zero` gate script exists anywhere in this repo to copy structurally) — see its Pattern Assignments section above for the composited conventions to follow instead (sync.py's security/parsing idioms + a new exit-code contract).

## Metadata

**Analog search scope:** `.gsd/capabilities/beads/`, `.gsd/capabilities/ponytail/`, `ponytail-everywhere/` (plugin-dir original of the ponytail bundle), repo-root `hooks/`/`.claude-plugin/` (beads-lifecycle plugin), RESEARCH.md's verified gsd-core source excerpts (`gate-predicate-evaluator.cjs`, `plan-phase.md`, `loop-host-contract.cjs`).
**Files scanned:** 24 (14 beads-dir files, 6 ponytail-dir/plugin-dir files, 3 root plugin files, plus GSD-CORE-PATCH.md and beads-sync SKILL.md read for the gate-dispatch/patch-precedent question).
**Pattern extraction date:** 2026-08-17
