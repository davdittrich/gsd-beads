---
phase: 17
reviewers: [codex, antigravity]
reviewed_at: 2026-08-19T23:23:03Z
plans_reviewed: [17-01-PLAN.md, 17-02-PLAN.md, 17-03-PLAN.md, 17-04-PLAN.md]
models:
  codex: "gpt-5.6-sol (reasoning=low)"
  antigravity: "unknown"
model_sources:
  codex: "banner"
  antigravity: "unknown"
---


# Cross-AI Plan Review — Phase 17

## Consensus Summary

Both reviewers independently confirm the phase's central diagnosis against live source: decimal phases break at three lifecycle call sites, `beads.sync_mode` is declared but unread, native `create-issues` always permits body-stripping, and the two patch checkers are structural clones. Both endorse the TRUTH-04 → TRUTH-03 → TRUTH-01 → TRUTH-02 sequencing as logically sound. Where they diverge is on execution readiness: Codex assesses the plan set as **not ready to execute unchanged** (HIGH risk, citing four specific defects to fix first), while Antigravity assesses the same plan set as **LOW risk**, treating the same defects as suggestions rather than blockers. Neither reviewer's citations were found to be fabricated — every `file:line` reference checked resolves to the claimed content.

**One editorial note on a Codex HIGH finding:** Codex's "declared documentation sweep is incomplete" concern (Plan 17-03, citing `.beads/PRIME.md:48`) is based on incomplete information — `.beads/PRIME.md` is gitignored (`.gitignore:23`), not a tracked file, and this session already made an explicit out-of-band scope decision (via `AskUserQuestion`, before this review ran) to fix only the tracked twin (`plugins/beads-lifecycle/.agents/skills/beads/PRIME.md`) in the commit and refresh the gitignored copy separately, machine-locally. Codex could not see that decision. This specific HIGH item is resolved, not a live plan defect — flagged here rather than silently dropped since Codex raised it in good faith against real (if incomplete) information.

### Agreed Strengths

- **TRUTH-04's three core defects are correctly and identically diagnosed by both reviewers**, down to the same `file:line` citations: `PLAN_FILE_RE` at `sync.py:72`, `get_phase_header`'s `int(phase_num)` at `sync.py:634`, `extract_phase_mentions` at `sync.py:1489`. Both independently confirm the `re.escape()` requirement is load-bearing, not decorative — an unescaped `.` in a decimal phase number would make the header regex match arbitrary characters.
- **TRUTH-03's principal-separation design is sound.** Both reviewers verified the hook path forces `allow_strip=False` unconditionally at `sync.py:749` while the native CLI path (`sync.py:2249`) is the actual gap the plan closes by consulting `read_sync_mode()`.
- **TRUTH-02's asymmetric test-coverage catch is real and correctly scoped.** Both reviewers independently verified `--execute-plan-path` is pinned by a CLI test (`test_sync.py:3060-3072`) while `--ship-md-path` has no equivalent, and that `beads-status/SKILL.md:146` is a live consumer of the CLI name being changed — confirming D-09's "coverage before merge" ordering is not precautionary, it is necessary.

### Agreed Concerns

- **[MEDIUM-HIGH] `read_beads_config`'s absent-vs-invalid ambiguity threatens Plan 17-03's Task 2 contract — flagged independently by both reviewers, same code region (`sync.py:641-664`).** `read_beads_config(project_root, key, default)` returns the default both when a key is genuinely absent AND when it is present with the wrong type — collapsing two states Plan 17-03 needs to tell apart (an absent key must stay silent; an invalid/malformed value must emit a notice). Both reviewers land on the same fix independently: `check_sync_mode_value` must inspect raw key presence (`"sync_mode" in beads_cfg`) directly rather than relying solely on `read_sync_mode()`'s collapsed return value. Two independent reviewers converging on the identical root cause and identical fix, unprompted, is a strong signal this needs to be addressed before or during execution of 17-03's Task 2.

### Divergent Views

- **Plan 17-01's `_resolve_default_phase_dir` fix — scope creep or a real 4th break site?** Codex asserts this is unnecessary scope expansion: `"01.5".zfill(2)` already equals `"01.5"`, so (in Codex's reading) the directory-resolution path "already supports decimal phase tokens" and the plan's added `phase_dir_prefix()` helper is unproven. Antigravity independently derives the opposite conclusion, tracing the same code (`sync.py:1774-1780`) to a genuine mismatch: `zfill(2)` only pads strings *shorter* than 2 characters, so it is a no-op on `"1.5"` (already 3 characters) — meaning a `STATE.md` value of `"1.5"` (unpadded, single-digit major) will NOT match a directory named `01.5-slug`, while `"01.5"` (pre-padded) would. This traces to the same root-cause finding the planner's own research surfaced independently ("`_resolve_default_phase_dir`'s `.zfill(2)` is a no-op on `'1.5'` and would not match an `01.5-` directory — it gates all five points, so it is root-cause, not scope creep"). The disagreement appears to hinge on which decimal-phase input Codex tested against (`"01.5"`, already-padded) versus the case Antigravity and the planner tested against (`"1.5"`, unpadded single-digit major) — worth a direct re-check of the plan's test matrix for exactly this single-digit-major case before treating either verdict as settled.
- **Plan 17-04's `checkpoint:decision` on the D-08/SC4 conflict — necessary governance or redundant friction?** Codex reads CONTEXT.md D-08 as an already-settled decision and recommends removing Task 2's blocking checkpoint entirely as non-autonomous busywork. Antigravity takes the opposite stance, describing the same checkpoint approvingly as gating "a one-way decision" — consistent with this session's `REVERSIBILITY_GATES=true` policy, under which D-08 was independently rated `one-way` by the planner and the checkpoint's presence and placement were separately verified as correct by this session's plan-checker pass (which read CONTEXT.md's dated D-08 override directly). Codex was not shown that independent verification. This is a legitimate values disagreement (safety-checkpoint discipline vs. execution-friction minimization), not a factual dispute — worth a human call before `/gsd-execute-phase 17` reaches wave 4, but the checkpoint's *technical construction* (correct source-conflict framing, correct file list for D-08's enumerated callers) is not in question by either reviewer.
- **Overall risk assessment: HIGH (Codex) vs. LOW (Antigravity).** The two verdicts largely reconcile once the individual findings above are accounted for: Codex's HIGH is driven primarily by the (now-resolved) PRIME.md finding, the `_resolve_default_phase_dir` disagreement, and the checkpoint-removal recommendation; Antigravity's LOW rests on the phase being capability-scoped with no core `gsd-core` engine changes, no new dependencies, and fail-open (`onError: skip`) semantics throughout. With the PRIME.md item resolved, the residual disagreement is narrower than the raw LOW/HIGH gap suggests.

### Confirmed independently during synthesis (not from either reviewer's self-report alone)

- **`.planning/ROADMAP.md` is absent from `17-04-PLAN.md`'s `files_modified` frontmatter**, verified directly against the plan file — yet the plan's own `<source_conflict>` block (and its closing success-criteria section) states Success Criterion 4 will be amended "in the same commit" as part of resolving the D-08/SC4 conflict. Whichever way the checkpoint divergence above resolves, if Option A (amend SC4) is the outcome selected at Task 2, `.planning/ROADMAP.md` needs to be added to `files_modified` and the task's file list before execution — this is a real gap independent of the checkpoint-necessity debate.

---

## Codex Review

# Cross-AI Plan Review

## Overall assessment

The phase is well researched, correctly sequenced, and generally grounded in the current implementation. The source confirms the central defects: decimal phases fail at three lifecycle paths, `sync_mode` is declared but unread, native `create-issues` always permits stripping, and the two patch checkers are structural clones.

However, the plans are not ready to execute unchanged. Plan 03 omits a required tracked documentation target, Plan 04 reopens a locked decision and omits the roadmap file it promises to amend, and Plan 01 adds unnecessary normalization machinery around a directory-resolution path that already supports decimal phase tokens. Overall risk is **HIGH until those planning defects are corrected**.

---

# Plan 17-01 — Decimal phase support

## Summary

The plan addresses the real TRUTH-04 failures and correctly prioritizes them first. The regex widening and replacement of numeric conversion with escaped string handling are sound. Its main weakness is scope expansion: `_resolve_default_phase_dir` already handles `01.5` correctly, so introducing a second helper for directory prefixes is not justified by the current defect.

## Strengths

- The three actual defects are correctly identified:

  - `PLAN_FILE_RE` accepts only `NN-NN-PLAN.md` at [sync.py:72](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:72).
  - `get_phase_header` calls `int(phase_num)` at [sync.py:634](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:634).
  - `extract_phase_mentions` repeats that conversion at [sync.py:1489](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1489).

- Requiring `re.escape()` is important. Both header functions interpolate the token directly into a regex, so an unescaped decimal point would match arbitrary characters.

- The widened filename regex preserves the existing captured plan identifier used by `discover_plan_files`, which stores `m.group(1)` at [sync.py:546](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:546).

- The version bump belongs in the first source-changing plan. The tracked manifest is currently still `0.3.1` at [capability.json:4](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:4).

- The proposed negative adjacency tests are valuable. They specifically protect against the `.` wildcard error that a superficial decimal fix could introduce.

## Concerns

- **MEDIUM — `_resolve_default_phase_dir` is not currently a decimal-phase break site.** It uses `zfill(2)` and exact string equality at [sync.py:1774](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1774) and [sync.py:1779](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1779). Python’s `"01.5".zfill(2)` remains `"01.5"`, so a directory named `01.5-slug` already resolves. Adding `phase_dir_prefix()` here expands the change beyond the demonstrated defect.

- **MEDIUM — the “all four break sites” claim is inaccurate.** The verified failures are the filename regex and the two `int()` conversions. Treating directory-prefix resolution as a fourth defect risks changing working semantics.

- **LOW — several must-haves are disproportionate to TRUTH-04.** Parallel artifact-write safety, Unicode digit preservation, all-zero input, and generated-report idempotency are broader than fixing decimal phases. The current generated-file write itself is not concurrency-safe, so a “backstop” assertion does not materially verify that truth.

- **LOW — sorting is asserted indirectly.** `discover_plan_files` returns a normal dictionary populated in filesystem iteration order at [sync.py:544](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:544). Sorting happens later at selected callers, such as `lifecycle_dispatch` at [sync.py:748](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:748). The plan should not imply the mapping itself is sorted.

## Suggestions

- Use one helper only for header-regex normalization, for example `phase_regex_token()`.
- Leave `_resolve_default_phase_dir` unchanged unless a failing test first demonstrates a real decimal-resolution defect.
- Test sorting at the actual sorted caller, not as a property of `discover_plan_files`.
- Reduce the test matrix to the load-bearing cases: `01.5`, `10.1`, `11.1`, `1.05`, adjacency against `15`, and literal-dot matching.
- Keep the source/runtime-tree identity check, but specify the exact resync command and fail if `diff -rq` is non-empty.

## Risk Assessment

**MEDIUM.** The core fix is straightforward and well tested, but unnecessary modification of already-working directory resolution increases regression risk.

---

# Plan 17-02 — Native dispatch compatibility

## Summary

This plan correctly separates trusted native dispatch from the conservative string-matched hook path. It also correctly leaves the hook matcher itself unchanged. The greatest risk is the proposed prose-region detector: it decides whether a required dispatch is suppressed, so its parsing contract must be much more concrete than “isolate the region” and exclude filtered step arms.

## Strengths

- The plan correctly preserves the hook’s non-destructive behavior. Current `plan:post` explicitly passes `allow_strip=False` at [sync.py:749](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:749), and the regression test already pins that at [test_sync.py:3819](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:3819).

- It correctly identifies the explicit CLI gap. `main()` currently calls `create_issues(args.plan_path)` without determining `allow_strip` from configuration at [sync.py:2249](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:2249).

- Reusing `read_beads_config` is appropriate. It already reads fresh, handles malformed and wrong-typed values, and supplies defaults at [sync.py:641-663](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:641).

- The plan correctly keeps `plan:pre` and both wave points unconditional. Current routing is explicit at [sync.py:728-755](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:728).

- Leaving the shell matcher byte-identical is a good scope boundary. Its five-point set is visible at [lifecycle-dispatch.sh:61](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh:61), while routing changes can remain within Python.

## Concerns

- **HIGH — the detection algorithm is underspecified for a dispatch-suppression guard.** The plan says to isolate a point-specific region and exclude `capId`/`ref.skill` filtering, but it does not define stable start/end markers or the precise generic-arm predicate. A false positive causes a missed dispatch, not merely duplicate work.

- **HIGH — “unexpected exception” handling may hide the wrong operation.** `lifecycle_dispatch` wraps the whole point operation in one broad `try` at [sync.py:728](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:728). If the probe raises before dispatch, the broad handler returns zero but skips the required operation. The probe itself must be total and return “not detected” on every error before the branch decision.

- **MEDIUM — Plan 02 introduces `read_sync_mode` before the schema is narrowed.** The intermediate behavior is intentionally compatible, but it deserves a direct test for an on-disk `"off"` value because the current declaration explicitly accepts it at [capability.json:32-40](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:32).

- **MEDIUM — the native path’s project-root derivation must be explicit.** `main()` has only `args.plan_path`; the plan should state that the config root is derived from the resolved plan path, matching `create_issues` at [sync.py:1317-1319](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1317), rather than from process CWD.

- **LOW — the “at most one strip decision” concurrency truth cannot be guaranteed by this design.** A timing race can still allow the hook and native path to enter concurrently; the probe only changes expected routing, not mutual exclusion.

## Suggestions

- Specify the detector contract in pseudocode or task acceptance criteria:

  1. Resolve the exact workflow file.
  2. Locate one unique point-specific anchor.
  3. Bound the scan to a named following anchor.
  4. Require a generic `kind == "step"` arm with no capability/skill qualifier.
  5. Return false on missing, duplicate, ambiguous, unreadable, or undecodable regions.

- Put error handling inside `check_native_step_dispatch`, not only around `lifecycle_dispatch`.
- Add fixtures copied from both actual pre-#3687 files and the exact post-#3687 regions.
- Test config lookup from a plan outside the current CWD.
- Rephrase the concurrency truth as “both paths remain idempotent and only the hook path is unconditionally non-stripping.”

## Risk Assessment

**HIGH.** The design is directionally correct, but a false-positive prose probe silently disables required lifecycle behavior. That deserves a precisely specified parser contract and exact upstream fixtures.

---

# Plan 17-03 — `sync_mode` truth and migration notice

## Summary

The chosen behavior is coherent: make `mirror` real, remove redundant `off`, and notify existing invalid configurations without mutating them. The passive `plan:pre` notice is well motivated. The plan nevertheless fails its own “full doc sweep” requirement because it omits the tracked root `.beads/PRIME.md`, which still contains a `sync_mode` claim.

## Strengths

- The source confirms the key is currently dead: the schema declares three values at [capability.json:32-40](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:32), while the only existing accessors are `read_epic_per` and `read_beads_enabled` at [sync.py:669-676](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:669).

- Mapping `mirror` to `allow_strip=False` is minimal and fits current structure. The destructive operation is already isolated behind `allow_strip` and a live patch check at [sync.py:1367-1387](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1367).

- The migration answer is explicit and appropriately non-mutating.

- The notice channel is technically valid: `plan:pre` already emits patch diagnostics on stdout at [sync.py:728-738](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:728), and the hook promotes captured stdout into additional context after [lifecycle-dispatch.sh:116](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh:116).

- Treating invalid strings as untrusted output and sanitizing control characters is a good precaution.

## Concerns

- **HIGH — the declared documentation sweep is incomplete.** The files list includes the plugin PRIME but omits the tracked root [.beads/PRIME.md:48](/home/dd/projects/gsd-beads/.beads/PRIME.md:48), which currently says `bd` owns task content under `sync_mode`. That file was explicitly named in the roadmap offender list.

- **MEDIUM — the notice/default contract needs one unambiguous helper.** `read_beads_config` returns the default for a wrong-typed value at [sync.py:662-663](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:662), losing whether the key was absent or invalid. Yet the plan wants absent values silent and invalid strings noticed. `check_sync_mode_value` therefore cannot rely solely on `read_sync_mode`; it must inspect raw key presence/type separately.

- **MEDIUM — the proposed invalid-value policy is destructive by default.** An existing `"off"` project becomes authoritative and may strip bodies, albeit with a notice. This is consistent with the written migration answer, but the changelog and notice must say explicitly that continued execution uses authoritative behavior and may strip after the patch gate succeeds.

- **MEDIUM — the plan does not list the top-level source skill or generated mirrors consistently.** The repository has both [.beads/PRIME.md:45](/home/dd/projects/gsd-beads/.beads/PRIME.md:45) and [plugin PRIME.md:56](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.agents/skills/beads/PRIME.md:56). Editing only one leaves inconsistent user guidance.

- **LOW — the notice says it will name arbitrary values verbatim while the threat model says output is truncated and sanitized.** Acceptance criteria should define the rendered representation, ideally `repr()` after bounded control-character replacement.

## Suggestions

- Add `.beads/PRIME.md` to `files_modified` and Task 1.
- Implement two separate concepts:

  - `read_sync_mode()` returns the effective mode.
  - `inspect_sync_mode()` reports whether the key was absent, valid, invalid type, or invalid string.

- Decide explicitly whether invalid non-string values should notify. The current must-haves say they silently default, while invalid strings notify.
- Make the warning say: invalid value, effective fallback, potential task-body stripping, and exact remedy.
- Make the verification command use `git grep -n sync_mode -- . ':!.planning'` exactly as the roadmap requires, so omitted tracked offenders fail the plan.

## Risk Assessment

**HIGH.** The behavioral design is solid, but the plan currently cannot satisfy the full documentation sweep because a known tracked offender is outside its edit scope.

---

# Plan 17-04 — Patch-checker consolidation

## Summary

The internal refactor is justified and the pre-merge coverage task is excellent. Keeping the two Python wrappers preserves current internal callers and mocks while removing duplicated control flow. The plan’s execution control is defective, however: it reopens a user decision that CONTEXT.md explicitly locks, and it promises to amend ROADMAP.md without declaring that file as modified.

## Strengths

- The source confirms near-identical checkers at [sync.py:2049](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:2049) and [sync.py:2114](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:2114).

- The marker versions really differ:

  - Ship marker v2 at [sync.py:110](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:110).
  - Execute-plan marker v1 at [sync.py:115](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:115).

- Existing tests use the constants to construct fixtures rather than asserting their literal values at [test_sync.py:2946](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:2946) and [test_sync.py:3003](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:3003). The plan correctly identifies that blind spot.

- The asymmetric CLI coverage is real. Execute-plan routing is tested at [test_sync.py:3060-3073](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:3060), while no equivalent ship-path test exists.

- Preserving wrapper names is sensible because `lifecycle_dispatch` calls both directly at [sync.py:737-738](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:737), and the current routing test mocks those names at [test_sync.py:3770-3777](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:3770).

- The tracked skill callers are correctly identified at [beads-recall/SKILL.md:72-73](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md:72) and [beads-status/SKILL.md:146](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md:146).

## Concerns

- **HIGH — the blocking decision checkpoint contradicts the locked user decision.** CONTEXT.md explicitly mandates a single parameterized verb with no aliases at [17-CONTEXT.md:98-111](/home/dd/projects/gsd-beads/.planning/phases/17-config-code-truth/17-CONTEXT.md:98). Reasking whether to do it makes the plan non-autonomous for a decision that has already been made.

- **HIGH — ROADMAP.md is missing from `files_modified` and Task 3.** The plan says Success Criterion 4 will be amended, and verification requires it to reflect the new contract, but the file is not declared in the frontmatter or task file list. The conflicting criterion exists at [ROADMAP.md:127](/home/dd/projects/gsd-beads/.planning/ROADMAP.md:127).

- **MEDIUM — “coverage lands before the CLI changes” is not guaranteed merely by task order unless Task 1 is committed independently.** The plan should require a separate atomic commit or an explicit red/green checkpoint before Task 3.

- **MEDIUM — the proposed reader being “total” for an unknown table key is questionable API design.** Unknown keys represent programmer errors, not runtime file failures. Silently mapping them to “unreadable” can conceal internal bugs. Because wrappers pass literals, validating table keys at construction and testing completeness may be safer than accepting arbitrary keys.

- **MEDIUM — retaining wrapper functions while hard-breaking only the CLI is coherent, but the terminology is confusing.** Several passages call the CLI “public” while asserting no external exposure. The changelog should precisely say the subprocess interface changed while the Python helpers remain.

- **LOW — a raw line-count target is a weak success criterion.** Removing duplication matters; being shorter than 2286 lines can be gamed by formatting or documentation changes and does not prove one reader serves both targets.

## Suggestions

- Remove Task 2’s decision checkpoint. Record that D-08 already resolves the conflict.
- Add `.planning/ROADMAP.md` to frontmatter, Task 3, and the same atomic commit as the CLI change.
- Make Task 1 an independently verified commit before changing the parser.
- Prefer a closed target type, such as an enum or validated literal table lookup. If unknown keys must fail open, emit a clear “unknown patch target” diagnostic rather than pretending a file was unreadable.
- Verify structural consolidation by asserting both wrappers call the shared reader with different keys, not by line count alone.
- Add a parser-level test for the final proposed shape, e.g. `check-patch ship-md --path …` and `check-patch execute-plan --path …`.

## Risk Assessment

**HIGH.** The code refactor itself is moderate risk and well motivated, but the plan’s governance is inconsistent: it blocks on an already-settled decision and cannot legally perform its promised roadmap amendment under its declared file scope.

---

# Phase-level recommendations

Before execution:

1. Remove Plan 01’s unproven `_resolve_default_phase_dir` refactor unless a failing test establishes the need.
2. Specify Plan 02’s region detector precisely and guarantee every ambiguous/error case returns “native dispatch not detected.”
3. Add `.beads/PRIME.md` to Plan 03’s documentation sweep.
4. Remove Plan 04’s blocking decision checkpoint.
5. Add `.planning/ROADMAP.md` to Plan 04’s declared modifications.
6. Require the Plan 04 coverage task to land as a separate commit before the CLI break.
7. Keep the current sequential order; the source supports TRUTH-04 → TRUTH-03 → TRUTH-01 → TRUTH-02.

With those corrections, the phase should achieve all four requirements without materially widening scope.


---

## Antigravity Review

# Cross-AI Implementation Plan Review: Phase 17 (Config/Code Truth)

## 1. Summary

The implementation plans for Phase 17 (`17-01-PLAN.md` through `17-04-PLAN.md`) provide a rigorous, well-sequenced strategy for resolving configuration, lifecycle dispatch, and patch-checking divergences in the `beads` capability for `gsd-core`. The phase is partitioned into 4 distinct sequential waves that align directly with requirements TRUTH-01 through TRUTH-04. Each plan exhibits strong TDD discipline, comprehensive STRIDE threat modeling, and explicit boundary/safety assertions. The ordering (TRUTH-04 decimal phases → TRUTH-03 upstream PR #3687 forward-compatibility → TRUTH-01 `sync_mode` narrowing/doc sweep → TRUTH-02 patch checker consolidation) is logical: it resolves high-severity correctness bugs and time-sensitive upstream interfaces before executing non-urgent refactorings.

---

## 2. Strengths

- **Surgical Bug Resolution (TRUTH-04)**: [Plan 17-01](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L72) accurately identifies the exact failure points for decimal-phase support: `PLAN_FILE_RE` regex mismatch at [`sync.py:72`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L72), `ValueError` on `int(phase_num)` in `get_phase_header` at [`sync.py:634`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L634), and `extract_phase_mentions` at [`sync.py:1489`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L1489). Mandating `re.escape()` prevents regex metacharacter injection (e.g., `.` matching arbitrary characters in `Phase 11X1:`).
- **Conservative Principal Separation (TRUTH-03 / D-03 / D-06)**: [Plan 17-02](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L749) maintains a strict safety boundary between string-matched hook dispatch and explicit workflow dispatch. The hook path permanently forces `allow_strip=False` at [`sync.py:749`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L749) to prevent unattended data loss, while the explicit CLI invocation at [`sync.py:2249`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L2249) consults `read_sync_mode()`.
- **Region-Scoped Workflow Probing**: Rather than relying on fragile version-sniffing or broad file greps that would trigger false positives on 1.11.0 (such as existing `kind == "step"` lines in `verify-work.md` for `secure-phase`), [Plan 17-02](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L2049) isolates the probe to the specific dispatch region and fails open to double-dispatch rather than missed dispatch.
- **Defensive Asymmetric Test Coverage (TRUTH-02 / D-09)**: [Plan 17-04](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py#L3060-L3072) catches the existing test imbalance where `--execute-plan-path` is pinned by a CLI test at [`tests/test_sync.py:3060-3072`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py#L3060-L3072) while `--ship-md-path` is completely absent. Enforcing test additions *prior* to CLI refactoring prevents silent regressions for callers like [`beads-status/SKILL.md:146`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md#L146).
- **Runtime Overlay Synchronization Guard**: Requiring the `capability.json` version bump (0.3.1 → 0.4.0) in the very first commit of Wave 1 and enforcing `diff -rq` checks between `.gsd/capabilities/beads/` and `plugins/beads-lifecycle/.gsd/capabilities/beads/` prevents testing against stale runtime overlays.

---

## 3. Concerns

- **[MEDIUM] Default Phase Directory Resolution with Decimal Numbers**:
  - *Location*: [`plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:1774-1780`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L1774-L1780)
  - *Mechanism*: `_resolve_default_phase_dir()` computes `padded = m.group(1).strip().zfill(2)` and evaluates `candidate.name.split("-", 1)[0] == padded`. In Python, `"1.5".zfill(2)` returns `"1.5"`. If a directory on disk is named `01.5-xxx` while `STATE.md` frontmatter has `current_phase: 1.5` (or vice versa), the exact string equality check fails and `status` returns `None`.
  - *Risk*: `sync.py status` without arguments will fail to locate default phase directories for inserted decimal phases when zero-padding differs between `STATE.md` and disk.

- **[LOW] In-Memory / Dict Lookups in Config Reader for Non-String Values**:
  - *Location*: [`plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:641-664`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L641-L664)
  - *Mechanism*: `read_beads_config(project_root, key, default)` returns `value if isinstance(value, type(default)) else default`. When `read_sync_mode` uses default `"authoritative"`, passing a non-string type (e.g. `{"sync_mode": true}` or `{"sync_mode": 1}`) falls back to `"authoritative"`.
  - *Risk*: In Plan 17-03 Task 2, `check_sync_mode_value` needs to distinguish between a key that is genuinely absent (which should not produce an out-of-enum notice) versus a key present with a malformed/non-declared value (which should emit the notice).

- **[LOW] CLI Subparser Refactoring Blast Radius (D-08)**:
  - *Location*: [`plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:2220-2228`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L2220-L2228) and [`skills/beads-status/SKILL.md:146`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md#L146)
  - *Mechanism*: Plan 17-04 collapses `check-shipmd-patch` and `check-execute-plan-patch` into a single subparser command without backwards-compatible CLI aliases.
  - *Risk*: While internal skill files ([`beads-status/SKILL.md:146`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md#L146) and [`beads-recall/SKILL.md:72-73`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md#L72-L73)) are updated in the same commit, any user scripts or external automations invoking the old verbs directly will immediately fail. The plan acknowledges this as a one-way decision gated by Task 2's blocking checkpoint.

---

## 4. Suggestions

- **Normalize Both Sides in Phase Prefix Resolution**:
  In `_resolve_default_phase_dir` ([`sync.py:1774-1780`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L1774-L1780)), replace the raw `zfill(2)` comparison with the new helper `phase_dir_prefix()` introduced in Plan 17-01. Ensure `phase_dir_prefix` strips leading zeros from the integer component of both the input phase string and the candidate directory prefix before comparison (e.g. normalizing both `01.5` and `1.5` to `1.5`).
- **Explicit Raw Key Presence Check for Out-of-Enum Notices**:
  In Plan 17-03's `check_sync_mode_value()` ([`sync.py:641`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py#L641)), inspect `beads_cfg` directly with `"sync_mode" in beads_cfg` before defaulting, so an absent key produces zero output while `"sync_mode": "off"` or invalid inputs cleanly emit the diagnostic notice.
- **Ensure CLI Test Verification Spans Both Flag Formats**:
  In Plan 17-04 Task 1, ensure tests verify both positional targets (`ship-md`, `execute-plan`) and override paths (`--path`) across valid, missing, and malformed marker files before removing legacy CLI subparsers.

---

## 5. Risk Assessment

- **Overall Risk Level**: **LOW**
- **Justification**:
  The changes are contained entirely within capability-level scripts, declarations, and documentation in [`plugins/beads-lifecycle/.gsd/capabilities/beads/`](file:///home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/). There are no core `gsd-core` engine modifications or external dependency additions. All operations preserve fail-open semantics (`onError: skip` / exit code 0). The phase design incorporates defensive regression testing (baseline 164 tests expanding to ≥179 tests), explicit runtime overlay synchronization gates, and targeted STRIDE mitigations for all untrusted input boundaries.


---
