# Plan Review: Phase 19 — Native Resolver Contract and Failure Boundary (`19-01-PLAN.md`)

## 1. Summary

Implementation plan `19-01-PLAN.md` defines the contract and failure boundary for the native `beads` task-content resolver (`RES-01`, `RES-02`, `RES-03`), resolving [davdittrich/gsd-beads#6](https://github.com/davdittrich/gsd-beads/issues/6) and Beads epic `gsd-beads-0y4`.

The plan is structured into two test-driven tasks:
1. **Task 1 (`gsd-beads-0y4.1`, Tracer)**: Implements `resolve_task_content(issue_id)` and CLI dispatch `sync.py resolve-task-content <id>` in [`plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py), verified by comprehensive round-trip and single-fault fixtures in [`plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py).
2. **Task 2 (`gsd-beads-0y4.2`, Auto)**: Declares the sole `taskContentResolver` in [`plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json) with Python stdlib bootstrap via `os.execv`, bumps capability version to `0.5.0`, and synchronizes [`CHANGELOG.md`](file:///home/dd/projects/gsd-beads/CHANGELOG.md) and [`README.md`](file:///home/dd/projects/gsd-beads/README.md).

Scope is strictly fenced: no `tracker-id` plan migration (Phase 20), no installed runtime cutover or Patch 2 deletion (Phase 21), no gsd-core source edits, and no new runtime packages or PATH shims.

---

## 2. Strengths

- **Surgical Locality and Reuse (Ponytail Rung 2 & 4)** [Confidence: 98/100]:
  Reuses existing module [`sync.py`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L113) (`SAFE_BD_ID_RE:113`, `run_bd:237-240`, `_task_description:513-552`, `main:2573-2690`) rather than creating new modules or abstractions. Integrates directly into gsd-core's native platform seam [`taskContentResolver`](file:///home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs#L213-L242).
- **Rigorous Hard-Halt & Anti-Fallback Enforcement** [Confidence: 99/100]:
  Matches gsd-core's hard-halt contract ([`task-content-resolution.cjs:24-30`](file:///home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs#L24-L30)). Prohibits fallback to `PLAN.md` prose. Enforces empty stdout and bounded stderr (≤ 2000 chars) on every failure branch (missing ID, non-zero `bd`, malformed JSON, invalid row envelope, duplicate H2 headings, malformed lists, or empty retained description).
- **High-Fidelity Oracle & Anti-Confound Test Discipline** [Confidence: 96/100]:
  Uses canonical producer [`_task_description`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L513-L552) for round-trip validation. Requires isolated, single-variable negative fixtures (D-19) so multi-fault confounding is prevented.
- **Unambiguous Precondition Gate** [Confidence: 100/100]:
  Explicitly identifies that capability test suite failures from upstream native step dispatch changes must be resolved via prerequisite ticket `gsd-beads-byp` before Phase 19 execution begins ([`19-01-PLAN.md:126`](file:///home/dd/projects/gsd-beads/.planning/phases/19-native-resolver-contract-and-failure-boundary/19-01-PLAN.md#L126)), preventing test failure conflation.

---

## 3. Concerns

### [MEDIUM] Subprocess Timeout Ordering Divergence
- **Evidence:** [`sync.py:21`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L21) defines `BD_TIMEOUT = 15` seconds for `run_bd(argv, timeout=BD_TIMEOUT)`. Meanwhile, `19-01-PLAN.md:1048` and `capability.json` define `invoke.timeoutMs: 10000` (10 seconds) for gsd-core's outer resolver call ([`task-content-resolution.cjs:330-335`](file:///home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs#L330-L335)).
- **Mechanism:** If `bd show` stalls (e.g. locked Dolt database) for 12 seconds, gsd-core's supervisor process kills the Python resolver process via Node `spawnSync` timeout (`ETIMEDOUT` / `ResolverTimeoutError`) before `run_bd`'s internal 15s timeout can fire. `sync.py` will never emit its internal bounded diagnostic to stderr before being terminated.
- **Confidence:** 95/100 (exact code comparison).
- **Ponytail Lens (Rung 2 - Reuse / Parameterize):** Set the `timeout` parameter in `resolve_task_content`'s `run_bd` call to a bound lower than the manifest's `timeoutMs` (e.g. `timeout=8` seconds), ensuring internal diagnostics are emitted to stderr before outer termination.

### [LOW] JSON Object Envelope Guard vs Non-Array Error Payloads
- **Evidence:** [`task-content-resolution.cjs:347-349`](file:///home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs#L347-L349) and [`19-CONTEXT.md:70-72`](file:///home/dd/projects/gsd-beads/.planning/phases/19-native-resolver-contract-and-failure-boundary/19-CONTEXT.md#L70-L72) (D-14).
- **Mechanism:** Versioned `bd` envelopes provide `{"data": [...]}`. If `bd show` emits a non-data object envelope (e.g. `{"error": "issue not found"}` with exit code 0), `resolve_task_content` must reject it immediately as an invalid envelope rather than raising an unhandled `KeyError` or misinterpreting top-level keys.
- **Confidence:** 92/100 (contract analysis).
- **Ponytail Lens (Rung 3 - Stdlib validation):** Ensure the envelope extractor validates that the container is either a `list` or a `dict` with a `list`-typed `"data"` key before inspecting rows.

### [LOW] Manifest JSON Escaping for Multiline Python Bootstrap
- **Evidence:** [`capability.json:1`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json#L1) and [`capability-validator.cjs:802-818`](file:///home/dd/.codex/gsd-core/bin/lib/capability-validator.cjs#L802-L818).
- **Mechanism:** The inline `python3 -c` script must be a valid single-line string in JSON with properly escaped quotes and separators so `json.loads` in `validateCapability` and `spawnSync` preserve exact argv tokens.
- **Confidence:** 94/100.
- **Ponytail Lens (Rung 3 - Stdlib):** Verified; `TestTaskContentResolverManifest` must validate both the raw manifest JSON decoding and the actual `spawnSync`/`execv` invocation.

---

## 4. Suggestions

1. **Align Resolver `run_bd` Timeout with Manifest Ceiling (Ponytail Rung 2 - Reuse / Parameterize)**:
   Pass `timeout=8` (or `RESOLVER_BD_TIMEOUT = 8`) in `resolve_task_content`'s `run_bd` invocation so `sync.py` can catch `subprocess.TimeoutExpired`, log a structured diagnostic to stderr, and exit nonzero before gsd-core's 10,000ms ceiling kills the process.
   *(Ponytail impact: Reuses existing `timeout` argument in `run_bd`, 0 new dependencies).*

2. **Explicit Fixture for `{"error": "..."}` Zero-Exit bd Output (Ponytail Rung 2 - Existing Test Harness)**:
   Include an isolated test arm in `TestResolveTaskContent` for `bd show` returning `{"error": "not found"}` with returncode 0 to verify it triggers the invalid-envelope diagnostic.
   *(Ponytail impact: Adds 1 test method to `test_sync.py`, no change to production logic).*

3. **Verify `{{id}}` Standalone Array Element in Manifest Tests (Ponytail Rung 4 - Native Platform Seam)**:
   In `TestTaskContentResolverManifest`, assert that `"{{id}}"` is a distinct element in `invoke.args` and not an embedded substring, matching [`task-content-resolution.cjs:240`](file:///home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs#L240) (`a === '{{id}}'`).
   *(Ponytail impact: Preserves gsd-core's exact substitution model without string interpolation).*

---

## 5. Risk Assessment

| Risk Area | Severity | Mitigation in Plan | Residual Risk |
|---|---|---|---|
| **Authoritative State Loss** | HIGH | Strict five-field mapping, canonical round-trip oracle, zero fallback to `PLAN.md` | Minimal; fail-closed behavior ensures corrupted data halts execution. |
| **Upstream Baseline Confounding** | MEDIUM | Precondition gate checks `gsd-beads-byp` closure and full suite green before Task 1 | Low; stops execution if baseline is red. |
| **Process Hang / Deadlock** | LOW | Manifest 10,000ms timeout + internal subprocess bounds | Low; both layers enforce non-hanging bounds. |
| **Scope Creep (Phases 20/21)** | LOW | Explicit negative lists in task names and frontmatter | None; tracker ID migration and cutover are excluded. |

---

## 6. Verdict

**APPROVED (Ready for Execution pending `gsd-beads-byp` prerequisite closure).**

The plan is minimal, mathematically sound, strictly respects architectural boundaries, and adheres to Ponytail principles across all tasks. Execution may proceed once the `gsd-beads-byp` gate passes.
