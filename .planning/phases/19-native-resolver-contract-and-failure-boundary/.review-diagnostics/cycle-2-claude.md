## Review: `19-01-PLAN.md` @ `872dde1`

**SHA verified.** `fe9cee6a4efc9483d0ec0e92682723ecdb39bf7a039644d3440bfa9999faf19c` matches the stated bytes; worktree file clean at that commit. Proceeding.

### Summary

Plan is convergent on cycle 1. All eight cycle-1 concerns are **incorporated** — none deferred, none rejected, zero carried forward. The two-task shape holds at the right Ponytail rungs (rung 2 for the adapter, rung 4 for the manifest seam), and I independently confirmed the load-bearing external contracts against source: `splitCriteria` semantics (`plan-document.cjs:95-103`) match D-10 exactly; `coerceStringArray` (`task-content-resolution.cjs:280-282`) silently maps non-arrays to `[]`, so the added array-type assertions are genuinely necessary rather than belt-and-braces; `{{id}}` whole-element replacement is enforced twice (`task-content-resolution.cjs:190,240` and `capability-validator.cjs:806-819`); the 10000 ms timeout is under the 120000 ms validator ceiling (`capability-validator.cjs:763,829`); and the SessionStart drift installer really does `capability install --scope global --yes` (`hooks/capability-auto-install.sh:81`, called from `hooks/session-start.sh:13`), so the "auto-install but inert" README requirement is grounded, not defensive. Two new HIGH concerns surfaced that cycle 1 did not reach, both mechanical rather than architectural: the plan asserts an `os.execv` argv shape the tracked file mode cannot support, and the Wave-0 gate is currently unsatisfiable by its own declared owner. Both are fixable inside the existing task structure. The plan is not ready to dispatch as written; it is close.

### Cycle 1 audit trail

| Cycle-1 concern | Label | Evidence |
|---|---|---|
| Inner timeout must be below 10000 ms outer | **incorporated** | `19-01-PLAN.md:183` resolver-only `timeout=8`; assertion `8*1000 < 10000`; shared `BD_TIMEOUT = 15` (`sync.py:21`) explicitly untouched |
| Zero-exit non-data envelope | **incorporated** | `19-01-PLAN.md:187` isolated `{"error": "not found"}` arm requiring `invalid envelope` |
| List-wire assertions | **incorporated** | `19-01-PLAN.md:189,193` array types asserted on stdout — necessary per `coerceStringArray` |
| Global auto-install inertness / Phase 21 parity boundary | **incorporated** | Task 2 behavior + README `rg` assertions; hook behavior confirmed at `capability-auto-install.sh:81` |
| SPEC-less must_haves unresolved through close | **incorporated** | Success criteria pin 3 applicable / 0 resolved / 3 unresolved |
| No external unrelated checker | **incorporated** | `sota-numerics` survives only as a rejected row in the audit table (`19-01-PLAN.md:304`), not as an executable command |
| Precise `git ls-files` pathspec | **incorporated** | Verification item 2 passes five exact pathspecs and set-compares; I ran it — exits 0 |
| Sole `trackerPrefix` validation note | **incorporated** | Task 2 read_first cites `validateTaskContentResolverFields` (`capability-validator.cjs:764`) and merged uniqueness (`capability-validator.cjs:3308-3359`) — both real |

**Unresolved from cycle 1: 0.**

### Strengths

- **One-factor negative discipline is real, not stated.** Each failure arm names its single varied input, and the zero-exit envelope arm is explicitly required to differ from its valid control only by envelope. This is the discipline that makes a green failure matrix mean something.
- **The timeout-ordering fix is minimal and correct.** Parameterizing only the resolver call rather than lowering `BD_TIMEOUT` preserves every existing caller's behavior — rung 2, no collateral.
- **Byte-parity scope is honestly bounded.** Task 2 proves manifest semantics against scratch `GSD_HOME` layouts and says so; it does not claim installed equivalence. The README `rg` assertions make that boundary machine-checked rather than narrative.
- **`_task_description` as producer oracle** avoids the classic trap of hand-authoring the expected parse, which would test the test.

### Concerns

**HIGH — `os.execv` argv assertion is incompatible with the tracked file mode.**
`19-01-PLAN.md:214` and `:228` require observing exact execv argv `[script, "resolve-task-content", id]`. That shape only arises from `os.execv(script, [script, ...])`, which requires the target to be executable. `git ls-files -s` reports `100644` for `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`; on-disk mode is `-rw-r--r--`. That call raises `PermissionError` regardless of the `#!/usr/bin/env python3` shebang on line 1. The executor is therefore forced to choose between an unstated mode change (which also drifts the auto-install bundle hash, since `bundle_hash()` covers content and structure) or `os.execv(sys.executable, [sys.executable, script, verb, id])` — whose argv does not match the asserted literal, failing Task 2's own acceptance criterion. Ponytail lens: this is rung 3 (stdlib) misapplied — `sys.executable` is the portable stdlib answer and needs no file-mode ownership; the exec-bit route adds lifecycle state the milestone explicitly excludes. **Fix:** state the interpreter-relaunch argv (`[sys.executable, script, "resolve-task-content", id]`) as the asserted shape, or, if the direct-exec shape is genuinely wanted, make the mode change an explicit in-scope Task 2 step with its own assertion.

**HIGH — the Wave-0 gate cannot clear by closing `gsd-beads-byp`.**
The plan's gate requires `gsd-beads-byp` closed *and* the exact full suite exiting 0, and assigns all repair to that one ticket. I ran the exact command: **263 tests, 15 failures + 1 error**. Three of those failures — `TestEndToEndTracer.test_single_task_creates_one_issue_under_epic`, `TestEndToEndTracer.test_created_task_issue_round_trips_description_and_acceptance`, `TestLiveDependencies.test_ready_excludes_blocked_tasks_until_blockers_close` — fail at `test_sync.py:184,246,573` on `bd init` returning 1 with `⚠ Found existing Dolt database: /home/dd/projects/gsd-beads/.beads/embeddeddolt/gsd_beads`. That is workspace discovery walking up out of the test tmpdir into this repo — a different failure class from lifecycle-dispatch/native-step-detection, and outside the scope `gsd-beads-byp`'s own description declares ("reconciling lifecycle-dispatch/native-step-detection expectations with the currently installed gsd-core native `plan:post`/`verify:post` dispatch"). As written, the executor halts at Wave 0 with no owner for three of the blockers. This is a plan defect, distinct from the "byp is open, therefore not execution-ready" state you correctly flagged as non-defective — an open prerequisite is fine; a prerequisite that provably cannot satisfy the gate is not. **Fix:** either widen `gsd-beads-byp`'s scope to cover the bd-workspace-discovery failures, or file a second prerequisite and name both in the gate.

**MEDIUM — `<known_baseline>` understates the current red set.**
The plan records "eight failures plus one error" as of 2026-08-30 and characterizes every failure as lifecycle-dispatch/native-step-detection. Live today: 15 failures + 1 error, spanning three distinct classes. The 263-test count is right; the failure inventory is not. Because Task 1's precondition is a bare `exit 0` check this does not admit a wrong result, but it does mean the plan's readiness narrative — and `19-VALIDATION.md`'s matching paragraph — misrepresent how much work stands between here and green. **Fix:** re-run and re-record the baseline with its failure classes before dispatch.

**MEDIUM — Task 1's cited D-18 analog is itself currently red.**
`TestEndToEndTracer` is named in Task 1's read_first as the pattern for the producer-to-adapter round trip, and it is one of the `bd init` casualties above. The new `TestResolveTaskContent` can mock `run_bd` and stay green regardless, so this does not block Task 1 — but an executor reading a red analog for structural guidance is a foreseeable source of copied-in fragility. Worth one sentence in Task 1 saying the analog is copied for shape, not run.

**LOW — `19-PATTERNS.md` and the plan disagree on `invoke.args`.**
`19-PATTERNS.md:190` specifies `["-c", <bootstrap>, "resolve-task-content", "{{id}}"]`; the plan specifies `["-c", bootstrap, "{{id}}"]` with the verb owned by the bootstrap. The plan's three-element form is the better one (fewer moving parts, and `sys.argv == ["-c", id]` is a cleaner assertion), and the plan is authoritative — but the executor reads both files, and Task 2's literal-args assertion will contradict the pattern doc. One line reconciling them removes the ambiguity.

**LOW — the 8-second inner budget is asserted, not measured.**
`8000 < 10000` leaves ~2 s for interpreter start, `sync.py` import (120 KB module), `execv`, and bounded-diagnostic emission after a `bd` timeout fires. Almost certainly ample, but nothing in the plan measures it, and the whole point of the ordering fix is that the adapter's own diagnostic is reachable. A single wall-clock assertion on the timeout arm would close it cheaply.

**LOW — `_gsd_tools_path()` resolves the Claude home only.**
`test_sync.py:30-40` reads `CLAUDE_CONFIG_DIR` defaulting to `~/.claude`, while this phase's contract evidence was read from `~/.codex`. I diffed them: `task-content-resolution.cjs` is byte-identical across both homes and `~/.claude`'s `capability-validator.cjs` carries `validateTaskContentResolverFields`, so Task 2's precondition holds today. It is a silent single-home dependency, not a current failure — note it, do not restructure for it.

### Verdict

Plan convergence: **achieved** on cycle 1. Execution readiness: **blocked** on the two HIGH items — the execv argv shape must match a mode the tracked file actually has, and the Wave-0 gate must name an owner for every failure it gates on. Neither requires re-planning; both are edits inside the existing tasks.
