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
