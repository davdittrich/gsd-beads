---
phase: 19
reviewers: [claude, antigravity]
reviewed_at: "2026-08-31T01:16:18+02:00"
plans_reviewed: [19-01-PLAN.md]
models:
  claude: "unknown"
  antigravity: "unknown"
model_sources:
  claude: "unknown"
  antigravity: "unknown"
reviewed_plan_sha256: "62e87009ed92cf333e6f8a2130d523cf8145eba1d55baa95222da0c63c7b88ae"
review_prompt_sha256: "d104cac60d0a5bcb8397eaf0bf82bde9b71103e2cbb77e2cafbe5fabdadf14f4"
---
# Cross-AI Plan Review — Phase 19

Both explicit, source-grounded lanes succeeded. The reviewed `19-01-PLAN.md` stayed at the SHA-256 recorded in frontmatter. Each lane used the same run-scoped prompt whose SHA-256 is recorded above; that prompt contains the required `/ponytail` ladder verbatim.

## Claude Review

# Cross-AI Plan Review — Phase 19 (19-01-PLAN.md)

Repo access: **yes**. Claims below traced to source, not plan text.

## 1. Summary

Plan does two things: add `resolve-task-content <id>` verb to existing `sync.py`, add sole `taskContentResolver` to `capability.json`. Both TDD, both in tracked plugin source. Scope tight, boundaries (Phase 20 identity, Phase 21 cutover) explicit and repeated.

Verified against installed core:

- Five-field contract correct. `mapResolverOutput` reads exactly `description`/`verify`/`acceptance_criteria`/`read_first`/`done` (`/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs:292-300`).
- `{{id}}` is whole-element replacement, not substring interpolation (`task-content-resolution.cjs:237-242`). Plan's "separate argv element" requirement matches mechanism.
- Blank `description` → non-throwing `EMPTY` outcome (`:350-355`). Plan D-04's "halt instead" is a real, needed adapter-side choice, not paranoia.
- Nonzero exit / spawn error → `ResolverFailedError` with `stderr.trim().slice(-2000)` (`:336-339`). Plan's 2000-char stderr bound matches core exactly.
- `timeoutMs: 10000` passes validator; ceiling is 120000 (`capability-validator.cjs:762`), `{{id}}` presence and positive-int timeout both enforced (`:780-836`).
- `trackerPrefix` must be kebab-case AND is globally unique across merged first-party ∪ overlay set (`capability-validator.cjs:3305-3360`). Plan's "sole resolver" language is right for the wrong-ish reason — collision is enforced cross-capability, not just within beads.
- `splitCriteria` semantics as plan states (`plan-document.cjs:95-104`): CRLF/LF split, trim, drop blanks, strip one `^[-*]\s*`, drop blanks again. D-10 accurate.

Goal reachable. Two real problems below.

## 2. Strengths

- **Ponytail-honest.** Rung 2 (reuse `sync.py`'s `run_bd:237-240`, `SAFE_BD_ID_RE:113`, `_task_description`, `main`) and rung 4 (native seam) both cited with evidence, not asserted. No new module, no parser dep, no PATH shim. Concur — nothing to cut.
- **Round-trip oracle is the right oracle.** `_task_description` is the producer; using it instead of hand-written expected strings kills the class of test that passes because test and impl share a wrong assumption.
- **One-factor negative fixtures (D-19).** Correct and unusually well-stated. Confounded fixture proves nothing about individual guards.
- **Fail-closed choice is justified by source, not taste.** Core's `EMPTY` path is genuinely non-throwing; the adapter is the only place to convert unusable content into a halt.
- **Explicit refusal to touch Patch 2 / tracker-id.** Prevents the common milestone failure where phase 19 quietly becomes phase 19+20+21.

## 3. Concerns

### HIGH — Gate is currently red; plan delivers nothing as written

`bd show gsd-beads-byp --json` → `status: open` (checked live, this session). The plan's Wave 0 command uses `set -euo pipefail` + `jq -e '.[0].status == "closed"'`, so an autonomous executor halts before Task 1 with zero output. Plan is correct to gate — but it ships as a no-op today. This is a scheduling defect, not a plan-text defect.

Ponytail rung considered: 1 (YAGNI — does the gate need to exist?). **No change**: gate protects a real signal (263 tests, 8F+1E). Don't weaken it. Sequence `byp` first.

### HIGH — Inner `bd` timeout (15s) exceeds outer resolver timeout (10s)

`sync.py:21` `BD_TIMEOUT = 15`; manifest declares `timeoutMs: 10000` (D-17). Core kills via `spawnSync({timeout})` (`task-content-resolution.cjs:245-255`) → `ResolverTimeoutError`. Consequence: on a slow/hung `bd`, the adapter's own `TimeoutExpired` arm **can never fire in production** — the process is SIGTERM'd first, so the "one bounded diagnostic to stderr" (D-15) is never written. The plan's Task 2 timeout test uses a sleeping probe under the outer bound, which proves core's behavior, not the adapter's.

Fix: pass an explicit inner timeout strictly below the outer bound (e.g. `run_bd(argv, timeout=8)`) so the adapter owns its own diagnostic, and assert the two bounds' ordering in a test. Ponytail rung 2 (reuse existing `run_bd` timeout parameter — it already takes one). No new machinery.

### MEDIUM — "Not active until Phase 21" is true by accident, not by construction

`hooks/capability-auto-install.sh` hashes the bundle and re-installs to **global scope** on drift at SessionStart (PROJECT.md Key Decisions, Phase 10.1). So the moment Task 2 commits, the next session ships the resolver declaration into `$GSD_HOME`. The declaration is inert only because no PLAN task carries `tracker-id` yet (Phase 20). The plan's reversibility rating ("removing this single manifest field restores the prior registry") reads as if installation were gated. It isn't.

Not a blocker — inert is inert — but state it in the plan so Phase 21 doesn't later "discover" the global copy and treat it as evidence of cutover. Ponytail: **no change** to code; this is a documentation correction only.

### MEDIUM — Bootstrap resolves `$GSD_HOME/.gsd/capabilities/beads/scripts/sync.py`, which is a *different file* from the one under test

Task 1 tests `sync.main([...])` on tracked source. Task 2's bootstrap execs the global install. Phase 19 therefore never proves the two are the same bytes — that's explicitly CUT-01 (Phase 21). Fine as scoped, but the plan's success criterion 3 ("exact public adapter seam, exact typed subprocess call, and exact manifest invocation agree") overstates what Phase 19 can prove. Downgrade that criterion to "agree by construction; byte-identity proven in Phase 21."

### MEDIUM — Three `must_haves` rows shipped `status: unresolved, flagged: true`

RES-01/02/03 edge-coverage rows are unresolved because no phase SPEC exists. Plan's own reasoning for preserving them is sound (don't fabricate taxonomy). But an executor running `must_haves` verification will see three permanently-red rows and must not "fix" them by flipping status. Add one line telling the executor these stay unresolved through phase close.

### LOW — `acceptance_criteria` must be a JSON **array** on the wire

`coerceStringArray` (`task-content-resolution.cjs:280-282`) returns `[]` for any non-array. So a scalar string emitted by the adapter is silently dropped by core, not rejected. D-10/D-11 already say normalize-to-list, so plan is right — but add one assertion that stdout's `acceptance_criteria` is a JSON array, since the failure mode here is silent, not loud. Same for `read_first`.

### LOW — Verification step 5 runs an external capability's script

`python3 /home/dd/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py …` — a machine-local path from an unrelated capability, in a plan whose whole discipline is "no machine-local dependencies." Guard it (skip when absent) or drop it. Ponytail rung 1: this check adds nothing Phase 19 needs.

### LOW — `git ls-files --` in verification step 2 is not a real command

Bare `git ls-files --` with no pathspec lists the entire index; it can't "return exactly the five tracked paths." Give it the five paths explicitly.

## 4. Suggestions

1. Close `gsd-beads-byp` first; re-run the exact suite; then start 19-01. Don't re-scope Phase 19 to absorb it.
2. `run_bd(argv, timeout=8)` in the resolver path + a test asserting inner < outer. Highest-value single change.
3. Add `assertIsInstance(payload["acceptance_criteria"], list)` and same for `read_first`.
4. Reword success criterion 3 and Task 2's reversibility note per MEDIUM items above.
5. Add a cross-capability `trackerPrefix` uniqueness note (validator enforces globally, `capability-validator.cjs:3305-3360`) — cheap insurance if another installed capability ever claims `beads`.

## 5. Risk Assessment

| Risk | Severity | Likelihood | Note |
|---|---|---|---|
| Blocked on open `byp`, zero delivery | High | **Certain today** | Verified live |
| Adapter timeout diagnostic unreachable | High | High | 15s inner vs 10s outer, both verified in source |
| Global auto-install activates declaration early | Medium | High | Inert until Phase 20 adds `tracker-id` |
| Silent `[]` on non-array criteria | Low | Low | Adapter already emits lists |
| Scope creep into Phase 20/21 | Low | Low | Fences are explicit and repeated |
| Lossy Markdown partition | Low | Low | Round-trip oracle + one-factor fixtures are the right controls |

**Verdict:** plan reaches the phase goal. Fix the timeout ordering and sequence the prerequisite; the rest is wording.

---

## Antigravity Review

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

---

## Consensus Summary

### Agreed Strengths
- Both reviewers confirm that the plan reuses the existing `sync.py` seams and the native resolver capability rather than introducing a module, dependency, or wrapper.
- Both reviewers credit the canonical `_task_description` round trip, one-factor negative fixtures, and the fail-closed five-field contract.
- Both accept the separate `gsd-beads-byp` readiness gate as the correct scope boundary.

### Agreed Concerns
- **HIGH — timeout ordering:** `sync.py` currently gives `bd` 15 seconds, while the planned native resolver has a 10,000 ms outer timeout. The outer process can kill the adapter before its required bounded timeout diagnostic. Both lanes cite this mechanism; use the existing `run_bd(..., timeout=8)` parameter (or an equivalently bounded existing seam) and prove inner < outer in a public-boundary test.

### Divergent Views
- Claude alone raised the currently-open `gsd-beads-byp` gate as HIGH. The source-grounding pass independently confirms the issue is open, so it counts as an unresolved existence-class HIGH. Antigravity treats the same gate as a valid pending prerequisite.
- Claude alone raised the automatic global-install boundary, global-source-versus-tracked-source proof gap, permanently unresolved `must_haves`, JSON-array assertions, external checker path, and bare `git ls-files --`; Antigravity instead raised a specific zero-exit non-data envelope fixture and manifest-escaping validation. These remain actionable non-HIGH concerns because they are not yet incorporated, deferred, or rejected in `19-01-PLAN.md`.
- The fact-drift pass found only the deterministic `STATE.md` Ready-to-execute versus ROADMAP Not-started **lag** verdict. It is explicitly advisory and not a finding.

## Verification Coverage
- Effective source-grounding authority: `intel`; both successful reviews are unmarked by `[reviewed-without-repo-access]` and `[reviewed-without-source-citations]`.
- Live prerequisite verification: `bd show gsd-beads-byp` reports `OPEN`; this confirms the execution gate stated in `19-01-PLAN.md:297` is currently unsatisfied.
- Timeout fact: `sync.py:21` sets `BD_TIMEOUT = 15`; the plan fixes the outer resolver to `timeoutMs: 10000` at `19-01-PLAN.md:139`, while gsd-core executes with its supplied timeout at `task-content-resolution.cjs:245-255`.
- Cross-artifact fact-drift: `drift-guard phase-status --phase 19` returned `lag` (`STATE.md` Ready to execute, ROADMAP Not started); no success-criterion, requirement-ID, or CONTEXT-term contradiction was found.
- Diagnostics preservation: the lane reviews and nonempty Antigravity stderr are preserved under `.review-diagnostics/` and are deliberately excluded from the workflow commit.

## Review Invocation Provenance
- Exact Ponytail prompt bytes: `d104cac60d0a5bcb8397eaf0bf82bde9b71103e2cbb77e2cafbe5fabdadf14f4`; the immutable source plan bytes: `62e87009ed92cf333e6f8a2130d523cf8145eba1d55baa95222da0c63c7b88ae`.
- Claude received `gsd-review-prompt.md` by the declared stdin channel. Antigravity received the declared absolute-file-reference command and read that same file in full. The prompt explicitly requires the Ponytail ladder and a rung/effect statement for every concern and suggestion.
- Transport deviation record: the host terminates foreground reviewer processes at 30 seconds, below the declared lane timeout. `setsid` wrapped only the unchanged `node ... gsd-tools.cjs query review-lane invoke --slug antigravity ... --explicit --json` process; it did not alter its command, prompt bytes, timeout, repository, or output paths. **what does it bias? NONE.** Evidence: the result is `ok:true`, `stubbed:false`, the prompt SHA is unchanged, and the normal GSD lane files were produced.
