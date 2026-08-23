---
quick_id: 260823-otk
slug: execute-https-github-com-davdittrich-pon
date: 2026-08-23
phase: quick-260823-otk
plan: 01
type: tdd
wave: 1
depends_on: []
files_modified:
  - ponytail-everywhere/.gsd/capabilities/ponytail/capability.json
  - ponytail-everywhere/.gsd/capabilities/ponytail/fragments/checker-proportionality.md
  - ponytail-everywhere/tests/test-plan-review-contribution.sh
  - ponytail-everywhere/.github/workflows/ci.yml
  - ponytail-everywhere/.claude-plugin/plugin.json
  - ponytail-everywhere/README.md
  - ponytail-everywhere/.gsd/capabilities/ponytail/NOTES.md
autonomous: true
beads_epic: gsd-beads-3c6
estimate:
  tokens: 30000
  raw_tokens: 30000
  tasks: 1
  confidence: low
must_haves:
  truths:
    - "An enabled Ponytail registry resolves exactly one plan:pre checker contribution whose inline fragment is byte-identical to the shipped source and whose resolved enforcement is advisory, warn, or block as configured."
    - "The checker guidance treats byte-identical mechanisms with identical invocation argv and control-path semantics as one behavior proved by static identity plus one dynamic execution, while different argv or control paths receive one execution each."
    - "Checker findings map advisory to info, warn to warning, and block to blocker; state the violated property and evidence; and present remediation examples as non-binding."
    - "Verification proportionality never reduces user-visible product scope, replaces contract assertions, or adds a parser, interpreter, fixture framework, or Cartesian execution matrix."
    - "Existing command-expansion enforcement and the Quick planner bridge remain unchanged and their regression suites pass."
    - "README and capability notes state that automatic checker delivery depends on open-gsd/gsd-core#3771 and do not claim dispatch exists today."
    - "Capability and Claude plugin versions advance together from 0.3.0 to 0.4.0."
  artifacts:
    - path: "ponytail-everywhere/.gsd/capabilities/ponytail/capability.json"
      provides: "Schema-valid plan:pre checker contribution and synchronized capability version"
    - path: "ponytail-everywhere/.gsd/capabilities/ponytail/fragments/checker-proportionality.md"
      provides: "Checker-targeted proportionality and enforcement contract"
    - path: "ponytail-everywhere/tests/test-plan-review-contribution.sh"
      provides: "Real-registry contract, static identity, enforcement, disabled-state, and distinct-behavior proof"
    - path: "ponytail-everywhere/.github/workflows/ci.yml"
      provides: "Continuous execution of the focused plan-review contribution test"
    - path: "ponytail-everywhere/.claude-plugin/plugin.json"
      provides: "Claude marketplace-visible 0.4.0 feature version"
    - path: "ponytail-everywhere/README.md"
      provides: "User-facing semantics and explicit upstream dispatch dependency"
    - path: "ponytail-everywhere/.gsd/capabilities/ponytail/NOTES.md"
      provides: "Maintainer-facing contribution reach and re-consent consequences"
  key_links:
    - from: "ponytail-everywhere/.gsd/capabilities/ponytail/capability.json"
      to: "ponytail-everywhere/.gsd/capabilities/ponytail/fragments/checker-proportionality.md"
      via: "plan:pre contribution with into=checker and fragment.path"
      pattern: '"into": "checker"'
    - from: "ponytail-everywhere/.gsd/capabilities/ponytail/capability.json"
      to: "ponytail.enforcement"
      via: "configValues.enforcement resolution"
      pattern: '"enforcement": "ponytail.enforcement"'
    - from: "ponytail-everywhere/tests/test-plan-review-contribution.sh"
      to: "ponytail-everywhere/.gsd/capabilities/ponytail/fragments/checker-proportionality.md"
      via: "exact source-to-rendered-fragment comparison and public outcome assertions"
      pattern: "cmp"
    - from: "ponytail-everywhere/.github/workflows/ci.yml"
      to: "ponytail-everywhere/tests/test-plan-review-contribution.sh"
      via: "dedicated bash test step"
      pattern: "test-plan-review-contribution.sh"
    - from: "ponytail-everywhere/.claude-plugin/plugin.json"
      to: "ponytail-everywhere/.gsd/capabilities/ponytail/capability.json"
      via: "exact 0.4.0 version parity"
      pattern: '"version": "0.4.0"'
---

<objective>
Deliver Ponytail plan-review verification proportionality as one native, checker-targeted capability contribution with executable contract proof, synchronized release metadata, and honest dispatch documentation.

Purpose: Plan approval should require only the smallest proof that establishes each genuinely distinct behavior, without duplicating executions or shrinking the product being verified.
Output: One checker fragment, one manifest contribution, one focused test and CI step, synchronized 0.4.0 versions, and user/maintainer documentation tied to upstream dispatch issue #3771.
</objective>

## Mechanism

Use the existing gsd-core `plan:pre` contribution contract with `into: "checker"`, a static Markdown fragment, `when: "ponytail.enabled"`, resolved `ponytail.enforcement`, and `onError: "skip"`. This adds no production executable: the real registry resolves and returns the fragment verbatim.

## Forbidden

Do not patch gsd-core, modify or replace `hooks/proportionality-check.js`, change `tests/test-proportionality-check.sh`, alter the existing planner contribution or Quick planner bridge, add a checker bridge, add a `plan:post` gate, build a parser/interpreter/fixture framework/execution matrix, add a dependency, or reduce user-visible scope to make verification smaller.

## Audit

Assert the public contribution contract through the real gsd-core 1.11.0 registry in a disposable project: top-level render result `point` is exactly `plan:pre`; exactly one active hook matches `capId=ponytail`, `kind=contribution`, and `into=checker` without requiring a per-hook point; its inline fragment is extracted byte-preservingly with `jq -j` and is identical to source; resolved enforcement is exact for each of the three public values; `ponytail.enforcement.description` truthfully covers command-expansion and plan-review checker outcomes; disabled state is silent; versions and CI wiring are synchronized. Keep exact whole-line assertions for normative fragment lines, but use fixed-string containment for embedded contract tokens (`violated property`, `evidence`, `fix_hint`, `non-binding`, and the upstream issue), and use case-insensitive fixed-string matching for the re-consent warning. Demonstrate proportionality with exact static identity checks and exactly one execution per distinct `(mechanism bytes, argv, control-path)` behavior. Use an argv spy only for the example whose internal invocation is itself part of behavioral identity; do not spy on static fragment resolution or assert unrelated top-level capability prose. Enforce restoration of unrelated top-level `.description` only at final acceptance, outside the focused test, by comparing the current value with the pinned nested-repository baseline object `6ff2f36685ab608dedd61930d6264c47ee8e1ace`.

## SPEC_FAILURE Recovery Evidence

The first deterministic failure was isolated to a non-behavioral top-level `.description` substring predicate: two exit-1 runs emitted `FAIL: checker contribution contract differs`; isolated predicates were `version_ok=true`, `checker_count=1`, and `description_ok=false`; normalizing only that prose in memory made the combined jq gate pass. The complete focused-test diagnosis then established four contract mismatches: (1) real `loop render-hooks plan:pre --raw` returns top-level `point: plan:pre` while each matching `activeHooks[]` contribution has `point: null`; (2) `jq -r .fragment.inline` appends a serialization newline, so a byte-identical fragment fails `cmp`; (3) full normative lines already pass `grep -Fqx`, while embedded tokens fail only because they are not entire lines and pass `grep -Fq`; and (4) NOTES contains `Re-consent`, so the required warning is present but a case-sensitive check misses it. An in-memory transformed run applying exactly these four test corrections produced every focused `PASS`, `ALL PASS`, and exit `0`. Recovery therefore removes the unrelated top-level prose predicate, restores that prose to the pinned pre-task value, asserts the top-level render point once, filters checker hooks without per-hook point, extracts fragment bytes with `jq -j`, separates normative whole-line checks from stable token containment, matches the warning case-insensitively, and keeps the truthful dual-outcome assertion on `ponytail.enforcement.description`.

## Alternatives Considered

Ranks are ordinal (`1` is best) and follow the repository's decision order: performance, simplicity/LOC, ecosystem support, then maintenance overhead.

| Mechanism | Performance | Simplicity / LOC | Ecosystem | Maintenance | Current dated evidence | Disposition |
|---|---:|---:|---:|---:|---|---|
| Existing `plan:pre -> checker` contribution | 1 | 1 | 1 | 1 | gsd-core v1.11.0 defines `checker` as a legal plan contribution role and resolves fragments verbatim ([Loop Host contract, accessed 2026-08-23](https://github.com/open-gsd/gsd-core/blob/v1.11.0/gsd-core/references/loop-hook-dispatch.md)); owner acceptance selects this seam ([issue #4, 2026-08-23](https://github.com/davdittrich/ponytail-everywhere/issues/4)). | **Selected.** No extra process or downstream adapter; upstream #3771 can activate it without repository changes. |
| Project `agent_skills.gsd-plan-checker` bridge mirroring the existing Quick planner bridge | 2 | 2 | 3 | 3 | Ponytail's current bridge is project-scoped and requires configuration per project ([repository README at `6ff2f36`, accessed 2026-08-23](https://github.com/davdittrich/ponytail-everywhere/blob/6ff2f36/README.md#quick-planner-bridge)); the owner explicitly requires native checker contribution plus documented dispatch dependency ([issue #4, 2026-08-23](https://github.com/davdittrich/ponytail-everywhere/issues/4)). | Rejected: adds a render process, renderer/config/test code, and a removal obligation when native dispatch lands. |
| Executable `plan:post` proportionality gate | 3 | 3 | 2 | 3 | gsd-core runs post gates after checker/revision rather than inside checker review ([v1.11.0 dispatch contract, accessed 2026-08-23](https://github.com/open-gsd/gsd-core/blob/v1.11.0/gsd-core/references/loop-hook-dispatch.md)); the owner excludes a parser or bespoke enforcement engine ([issue #4, 2026-08-23](https://github.com/davdittrich/ponytail-everywhere/issues/4)). | Rejected: wrong lifecycle timing and permanent executable policy surface. |

**Decision:** Performance decides the selection: the native contribution injects static content with no extra per-review process. It also wins simplicity/LOC and maintenance; ecosystem support is schema-complete, while automatic checker dispatch remains explicitly dependent on [open-gsd/gsd-core#3771](https://github.com/open-gsd/gsd-core/issues/3771).

<execution_context>
@/home/dd/.codex/gsd-core/workflows/execute-plan.md
@/home/dd/.codex/gsd-core/templates/summary.md
</execution_context>

<context>
@AGENTS.md
@.planning/STATE.md
@.planning/quick/260823-otk-execute-https-github-com-davdittrich-pon/260823-otk-RESEARCH.md
@ponytail-everywhere/.gsd/capabilities/ponytail/capability.json
@ponytail-everywhere/.gsd/capabilities/ponytail/fragments/planner-ladder.md
@ponytail-everywhere/tests/test-quick-planner-bridge.sh
@ponytail-everywhere/tests/test-proportionality-check.sh
@ponytail-everywhere/.github/workflows/ci.yml
@ponytail-everywhere/README.md
@ponytail-everywhere/.gsd/capabilities/ponytail/NOTES.md

Authoritative task state: `bd show gsd-beads-3c6`. The owner-authored issue brief dated 2026-08-23 is ready for execution; discussion found no unresolved decisions and created no CONTEXT.md. The nested repository has no CodeGraph/OpenWolf index, so the executor may use targeted reads after recording that miss.
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: Prove and ship the native checker contribution</name>
  <beads-id>gsd-beads-3c6</beads-id>
  <files>ponytail-everywhere/.gsd/capabilities/ponytail/capability.json, ponytail-everywhere/.gsd/capabilities/ponytail/fragments/checker-proportionality.md, ponytail-everywhere/tests/test-plan-review-contribution.sh, ponytail-everywhere/.github/workflows/ci.yml, ponytail-everywhere/.claude-plugin/plugin.json, ponytail-everywhere/README.md, ponytail-everywhere/.gsd/capabilities/ponytail/NOTES.md</files>
  <behavior>
    - RED/GREEN: With Ponytail enabled, the real registry result has top-level `point=plan:pre` and exactly one hook matching `capId=ponytail`, `kind=contribution`, and `into=checker`; the hook is not filtered by its null `point`, its inline fragment is extracted with `jq -j` and is byte-identical to source, and resolved `enforcement` equals the configured `advisory`, `warn`, or `block` value.
    - RED/GREEN: `ponytail.enforcement.description` truthfully covers both Claude command-expansion decisions and plan-review checker issue severities; no test depends on unrelated top-level capability-description wording.
    - RED/GREEN: With Ponytail disabled, the registry returns no active Ponytail checker contribution.
    - RED/GREEN: The fragment defines behavior identity as mechanism bytes plus invocation argv plus control-path semantics; identical identity accepts static identity plus one execution, while different argv/control paths require one execution each.
    - RED/GREEN: Exact normative fragment lines remain whole-line assertions; embedded `violated property`, `evidence`, `fix_hint`, `non-binding`, and upstream-issue tokens use fixed-string containment; the fragment maps `advisory -> info`, `warn -> warning`, and `block -> blocker` and requires evidence-bearing, non-binding checker findings.
    - RED/GREEN: A tiny copied-resolver example proves two byte-identical copies with the same argv by `cmp` plus hash equality and executes one representative exactly once; a second example keeps identical bytes but uses two behavior-selecting argv tails, executes each tail exactly once, and asserts the spy log's exact argv sequence.
    - GREEN: Capability and plugin metadata are both exactly `0.4.0`; CI runs the focused test; README and NOTES document semantics, a case-insensitively detected re-consent warning after bundle changes, and the inactive-until-#3771 automatic dispatch boundary.
    - REGRESSION: The pre-expansion hook, its test, the planner contribution, and the Quick planner bridge remain byte-unchanged and their existing tests pass; final acceptance proves top-level capability `.description` equals the value stored in nested baseline `6ff2f36685ab608dedd61930d6264c47ee8e1ace` without adding that predicate to the focused test.
  </behavior>
  <action>Work tests-first and commit the seven tightly coupled files once, after all gates pass. SPEC_FAILURE recovery RED: preserve the complete deterministic evidence from `## SPEC_FAILURE Recovery Evidence` in execution notes. Apply only these focused-test contract corrections in `tests/test-plan-review-contribution.sh`: remove the top-level capability `.description` substring predicate without replacing it with any prose-format predicate; assert once that the top-level `loop render-hooks plan:pre --raw` result has `.point == "plan:pre"`; select exactly one checker hook by `capId == "ponytail"`, `kind == "contribution"`, and `into == "checker"` without filtering on the hook's null `.point`; extract `.fragment.inline` with `jq -j` before `cmp`; keep `grep -Fqx` for complete normative lines but use `grep -Fq` for embedded `violated property`, `evidence`, `fix_hint`, `non-binding`, and upstream-issue tokens; and use case-insensitive fixed-string matching for the README/NOTES re-consent warning. Retain public version, contribution schema/cardinality, resolved enforcement, disabled-state, behavioral identity/outcome, documentation, CI, and version assertions. Add or retain the correctly targeted assertion that `ponytail.enforcement.description` covers both command-expansion decisions and plan-review checker outcomes. Run the focused test before the product correction and require RED only where the live enforcement description remains incomplete; do not change product prose or mechanism to accommodate test serialization, nesting, line layout, or capitalization.

GREEN: in `capability.json`, restore unrelated top-level `.description` to the value in pinned baseline `6ff2f36685ab608dedd61930d6264c47ee8e1ace`; changing unrelated product prose solely to satisfy test formatting is forbidden. Update only `config["ponytail.enforcement"].description` so it truthfully covers the existing Claude command-expansion result and the new plan-review checker severity outcome. Preserve the live schema-valid `plan:pre` checker contribution exactly: `produces`/`consumes` empty, `fragment.path` `fragments/checker-proportionality.md`, `when` `ponytail.enabled`, `configValues.enforcement` `ponytail.enforcement`, and `onError` `skip`; preserve every pre-existing contribution byte-for-byte. Keep the focused test using Bash, jq, Node already required by gsd-core, a disposable `mktemp -d` project, and disposable `GSD_HOME`; install the repository capability project-scope with the real gsd-core 1.11.0 CLI, never touching the user's consent store. Resolve `plan:pre --raw` for each public enforcement value and once with Ponytail disabled. Assert the top-level render point separately, exact checker hook cardinality/identity without per-hook point, resolved `configValues.enforcement`, and byte-identical fragment extraction via `jq -j` plus `cmp`; do not add a Markdown parser or general prose-format contract. Retain the normative-line and stable-token assertions, the two copied-resolver audit examples, static `cmp`/SHA-256 proof, one representative execution for equal behavior, and one execution for each behavior-selecting argv tail. The evidence-backed in-memory transformed run of exactly these test corrections already produced every focused `PASS`, `ALL PASS`, and exit `0`; the real GREEN run must reproduce that result after the enforcement-description correction.

Retain the static fragment's exact public contract from `<behavior>`: direct contract assertions before machinery, static proof for byte-identical mechanisms, argv/control-path-sensitive behavior identity, one execution per distinct behavior, no product-scope reduction, evidence-bearing findings, non-binding remediation examples, and the three issue severities. Do not add executable production logic or interpolate plan content. Keep the focused CI step, both `0.4.0` versions, README semantics, NOTES maintainer reach/re-consent text, and explicit #3771 boundary unchanged except for no documentation edit needed by the test redesign. Keep every top-level capability-description predicate out of `tests/test-plan-review-contribution.sh`. At final acceptance, outside that test, compare `.description` extracted from `git show 6ff2f36685ab608dedd61930d6264c47ee8e1ace:.gsd/capabilities/ponytail/capability.json` with `.description` extracted from the current worktree manifest; this pinned object comparison remains valid after the task commit. Run the focused test, all three existing test scripts, enforcement metadata check, version checks, pinned-baseline description check, and unchanged-path diff gate. Keep code, test, CI, release metadata, and docs in this one task commit because separating any of them would ship an unproved or undiscoverable contract.</action>
  <verify>
    <automated>cd ponytail-everywhere &amp;&amp; bash tests/test-plan-review-contribution.sh &amp;&amp; bash tests/test-quick-planner-bridge.sh &amp;&amp; bash tests/test-session-start.sh &amp;&amp; bash tests/test-proportionality-check.sh &amp;&amp; jq -e '.version == "0.4.0" and ([.contributions[] | select(.point == "plan:pre" and .into == "checker")] | length == 1) and (.config["ponytail.enforcement"].description | ascii_downcase | contains("command") and contains("plan") and contains("checker"))' .gsd/capabilities/ponytail/capability.json &amp;&amp; jq -e '.version == "0.4.0"' .claude-plugin/plugin.json &amp;&amp; test "$(git show 6ff2f36685ab608dedd61930d6264c47ee8e1ace:.gsd/capabilities/ponytail/capability.json | jq -r '.description')" = "$(jq -r '.description' .gsd/capabilities/ponytail/capability.json)" &amp;&amp; git diff --exit-code -- hooks/proportionality-check.js tests/test-proportionality-check.sh .gsd/capabilities/ponytail/skills/quick-planner/render.cjs .gsd/capabilities/ponytail/fragments/planner-ladder.md</automated>
  </verify>
  <done>The focused test asserts top-level render `point=plan:pre`, selects exactly one Ponytail checker contribution without a per-hook point predicate, extracts fragment bytes with `jq -j` for exact `cmp`, uses whole-line matching only for normative lines, uses stable containment for embedded contract tokens, and detects the re-consent warning case-insensitively; it prints every focused `PASS`, `ALL PASS`, and exits `0`. No unrelated top-level capability-description predicate remains in that test; final acceptance instead proves current top-level `.description` exactly equals pinned baseline `6ff2f36685ab608dedd61930d6264c47ee8e1ace`. `ponytail.enforcement.description` truthfully covers command-expansion and plan-review checker outcomes. The real registry still proves exact fragment identity, all three resolved enforcement values, disabled silence, and the two one-execution-per-distinct-behavior examples; fragment findings preserve scope and use evidence plus non-binding remediation; versions remain both 0.4.0; CI, README, and NOTES remain synchronized; #3771 is explicit; all existing tests pass; the pre-expansion hook, planner contribution, Quick bridge, and gsd-core remain unchanged.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Project configuration -> capability registry | Registry-validated `ponytail.enabled` and enforcement enum select whether and how the checker guidance applies. |
| Installed capability fragment -> checker prompt | Static repository content enters the checker prompt; no plan text is executed or interpolated by this contribution. |
| Test scratch project -> real user environment | Capability install and consent records must remain inside disposable project and `GSD_HOME` paths. |
| Example argv -> resolver spy | Invocation arguments are intentionally observable because they define distinct behavior in the acceptance contract. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-OTK-01 | Tampering | Fragment resolution | medium | mitigate | Compare registry-rendered inline content byte-for-byte against the shipped fragment and assert exactly one matching contribution. |
| T-OTK-02 | Elevation of Privilege | Checker fragment | medium | mitigate | Keep contribution declarative; do not execute/interpolate plan text or add an executable gate/parser. |
| T-OTK-03 | Information Disclosure | Capability consent test | medium | mitigate | Set disposable `GSD_HOME`, project, and cleanup trap so tests never read or write the user's consent store. |
| T-OTK-04 | Spoofing | Behavior identity proof | medium | mitigate | Bind identity to bytes, argv, and control path; exact spy records distinguish equal code invoked with behavior-changing tails. |
| T-OTK-05 | Denial of Service | Verification design | low | mitigate | Require one dynamic execution per genuinely distinct behavior and static identity for duplicates; reject Cartesian matrices without weakening contract assertions. |
| T-OTK-SC | Tampering | npm/pip/cargo installs | low | accept | No dependency or package-manager operation is in scope; CI already provides gsd-core 1.11.0. |
</threat_model>

## Multi-Source Coverage Audit

| Source | ID | Feature / Requirement | Covered by | Status | Notes |
|---|---|---|---|---|---|
| GOAL | ponytail-everywhere#4 | Checker evaluates verification machinery against genuinely distinct behavior before plan approval | Task 1 fragment and registry contract | COVERED | Native contribution is declared; current dispatch boundary is documented. |
| REQ | gsd-beads-3c6 | Preserve command-expansion enforcement; add checker-targeted guidance, outcomes, tests, and dependency docs | Task 1 behavior/action/verify | COVERED | One atomic task owns the complete vertical slice. |
| REQ | owner brief 2026-08-23 | Static identity plus one dynamic execution for equal bytes/argv; distinct argv tails execute separately | Task 1 focused copied-resolver examples | COVERED | Exact static and spy assertions, no duplicate execution. |
| REQ | owner brief 2026-08-23 | Advisory/info, warn/warning, block/blocker; property/evidence; non-binding remediation | Task 1 fragment contract and static assertions | COVERED | Uses existing checker severity/output contract. |
| REQ | owner brief 2026-08-23 | Do not patch core, replace hook, build machinery, or reduce product scope | Forbidden, Task 1 action, unchanged-path gate | COVERED | gsd-core#3771 remains upstream responsibility. |
| RESEARCH | 260823-otk-RESEARCH.md | Reuse `plan:pre -> checker` contribution with resolved enforcement | Mechanism and Task 1 GREEN | COVERED | No new executable production logic. |
| RESEARCH | 260823-otk-RESEARCH.md | Test real registry, exact fragment resolution, enforcement values, disabled silence | Task 1 RED/GREEN and verify | COVERED | Disposable project and consent root. |
| RESEARCH | 260823-otk-RESEARCH.md | Bump capability and plugin versions together; document #3771 and re-consent | Task 1 metadata/docs | COVERED | Both versions become 0.4.0. |
| CONTEXT | — | Discussion gate resolved all-clear; no CONTEXT.md or D-XX decisions | Entire plan | COVERED | No deferred ideas or unresolved choices exist. |

<verification>
1. Run Task 1's automated command from the top-level repository and require zero exit status.
2. Preserve RED evidence: the focused script fails because the checker contribution/fragment is absent before product edits, then passes after GREEN.
3. Inspect the final nested-repository diff once: only the seven declared files change; no gsd-core path, pre-expansion hook, existing proportionality test, planner contribution, or Quick bridge changes.
4. Require the quick-full plan checker to approve this plan before execution and the post-execution verifier to prove every `must_haves` truth and key link.
</verification>

<success_criteria>
- Enabled registry resolution exposes exactly one byte-identical checker fragment with the configured enforcement value; disabled configuration is silent.
- Focused contract proof asserts the top-level `plan:pre` point separately, does not filter contributions on their null per-hook point, uses `jq -j` for byte-preserving fragment comparison, distinguishes normative whole-line checks from embedded-token containment, and matches the re-consent warning without capitalization coupling.
- The checker contract distinguishes behavior by bytes, argv, and control path and requires exactly one execution per distinct behavior without reducing product scope.
- Public outcome severity, evidence, and non-binding remediation semantics are exact and regression-tested.
- Final acceptance compares current top-level capability `.description` with the pinned `6ff2f36685ab608dedd61930d6264c47ee8e1ace` object and passes; the focused test contains no predicate for that unrelated prose, and `ponytail.enforcement.description` covers both command and plan-checker outcomes.
- CI runs the focused proof; capability and plugin versions are both 0.4.0; README and NOTES state the #3771 dependency and re-consent requirement.
- Existing command-expansion and Quick planner bridge behavior remains unchanged and all repository test scripts pass.
</success_criteria>

<output>
Create `.planning/quick/260823-otk-execute-https-github-com-davdittrich-pon/260823-otk-SUMMARY.md` when done and keep bead `gsd-beads-3c6` authoritative for execution state.
</output>
