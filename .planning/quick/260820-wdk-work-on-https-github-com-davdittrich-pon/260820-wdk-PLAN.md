---
quick_id: 260820-wdk
slug: work-on-https-github-com-davdittrich-pon
date: 2026-08-20
type: execute
wave: 1
depends_on: []
files_modified:
  - ponytail-everywhere/hooks/hooks.json
  - ponytail-everywhere/hooks/proportionality-check.js
  - ponytail-everywhere/tests/test-proportionality-check.sh
  - ponytail-everywhere/.gsd/capabilities/ponytail/capability.json
  - ponytail-everywhere/.claude-plugin/plugin.json
  - ponytail-everywhere/README.md
autonomous: true
estimate:
  tokens: 28000
  raw_tokens: 28000
  tasks: 3
  confidence: low
must_haves:
  truths:
    - Only gsd-new-project, gsd-new-milestone, gsd-manager, gsd-mvp-phase, and gsd-discuss-phase receive a proportionality decision before command expansion.
    - Clearly disproportionate commands recommend exactly one of direct, quick, phase, or milestone, with enforcement determined by ponytail.enforcement.
    - Deterministic classification runs first; only ambiguous requests invoke the model-backed classifier, and unavailable evidence never blocks work.
    - The one-shot [ponytail:milestone] marker authorizes only the submitted command and creates no persistent bypass.
    - ponytail.enabled=false produces no output, lookup, model call, or command interruption.
    - Recommendations create no planning, audit, or decision artifacts, and the existing lazy-ladder guidance remains unchanged.
  artifacts:
    - ponytail-everywhere/hooks/proportionality-check.js
    - ponytail-everywhere/tests/test-proportionality-check.sh
    - ponytail-everywhere/hooks/hooks.json
    - ponytail-everywhere/.gsd/capabilities/ponytail/capability.json
    - ponytail-everywhere/README.md
  key_links:
    - hooks/hooks.json UserPromptExpansion matcher -> hooks/proportionality-check.js
    - hooks/proportionality-check.js -> hooks/gsd-tools.sh config-get for ponytail.enabled and ponytail.enforcement
    - ambiguous classifier -> read-only gh api subprocesses with per-call 3000 ms timeout -> Claude print-mode classifier
    - classifier result plus enforcement mode -> valid UserPromptExpansion JSON allow/block response
---

# Quick Task: gate scope-expanding GSD commands with a proportionality decision

<objective>
Add a Claude Code pre-expansion decision for the five specified GSD commands so small work is routed to direct or quick execution, phase-sized work stays phase-sized, and genuinely milestone-sized work proceeds without ceremony.

Purpose: Prevent durable planning machinery from being started for work whose demonstrated scope does not justify it, while failing open when evidence or classification is unavailable.

Output: One host hook, one dependency-free classifier, one smoke-test suite, the `ponytail.enforcement` configuration contract, and user documentation.
</objective>

## Plan Header

- **Root interception point:** Claude Code `UserPromptExpansion`, because it exposes `command_name`, `command_args`, and the submitted prompt before a slash command expands. `SessionStart` and GSD capability contributions run too early or too late for a per-command decision.
- **Exact allowlist:** `gsd-new-project`, `gsd-new-milestone`, `gsd-manager`, `gsd-mvp-phase`, `gsd-discuss-phase`. The hook matcher and the classifier both enforce it; every other command is untouched.
- **Implementation ladder:** Reuse `hooks/gsd-tools.sh` for config resolution, Node built-ins for JSON/URL/subprocess handling, Claude's installed print mode for ambiguous judgment, and `gh api --method GET` only for bounded evidence. Add no package, service, cache, policy framework, state store, or GSD lifecycle contract.
- **Repository boundary:** Modify and later commit source only inside the nested `ponytail-everywhere` repository. The parent repository receives this plan artifact only; never stage `ponytail-everywhere/` as a parent gitlink.
- **Discovery:** Level 1 host-contract verification. Claude Code documents `UserPromptExpansion` as a pre-expansion, block-capable hook and recommends it for intercepting direct slash-command invocation. No research artifact is required.

## Decision contract

### Route model

| Recommended route | Observable scope |
|---|---|
| `direct` | Read-only review, explanation, diagnosis, or a single action needing no durable task plan |
| `quick` | A bounded implementation or fix that is atomic and self-contained |
| `phase` | A coherent multi-step capability within an existing project or milestone |
| `milestone` | A new project direction or coordinated set of phases with durable roadmap impact |

The submitted command has an implied scope: `gsd-new-project`, `gsd-new-milestone`, and `gsd-manager` are milestone-scoped; `gsd-mvp-phase` and `gsd-discuss-phase` are phase-scoped. A **positive mismatch** exists only when the recommended route is narrower than the submitted command. A milestone recommendation is not a mismatch; insufficient evidence is `ambiguous`, not a mismatch.

### Enforcement matrix

| Classification | `advisory` | `warn` (default) | `block` |
|---|---|---|---|
| Proportionate | Allow silently | Allow silently | Allow silently |
| Positive mismatch | Allow with route recommendation in `additionalContext` | Block expansion and require the user to resubmit an explicit direct/quick/phase/milestone route | Block expansion; the same scope-expanding command proceeds only when that submission contains `[ponytail:milestone]` |
| Ambiguous, lookup failure, model failure, or malformed model result | Allow with concise advisory | Allow with concise advisory | Allow with concise advisory |
| Current submission contains `[ponytail:milestone]` | Allow current submission | Allow current submission | Allow current submission |

The marker is checked only in the current hook input. Do not write an approval file, config mutation, session flag, transcript annotation, or other durable bypass. A later command is classified independently.

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: Prove one proportionality decision at the command-expansion boundary</name>
  <files>ponytail-everywhere/hooks/hooks.json, ponytail-everywhere/hooks/proportionality-check.js, ponytail-everywhere/tests/test-proportionality-check.sh</files>
  <behavior>
    - Test 1: A non-allowlisted command never matches the hook; direct invocation of the classifier with a non-target command exits 0 with empty stdout and stderr.
    - Test 2: With default `warn`, a clearly small review request submitted through `gsd-new-milestone` returns valid UserPromptExpansion JSON with `decision: block`, a `direct` recommendation, and explicit route choices.
    - Test 3: A clearly milestone-sized request submitted through `gsd-new-milestone` exits 0 without a block decision.
    - Test 4: `ponytail.enabled=false` exits 0 before classification and produces no bytes on stdout or stderr.
  </behavior>
  <action>
Start by writing the four failing shell cases, using a temporary project, PATH stubs, and JSON stdin; then add the production path until they pass.

Add one `UserPromptExpansion` entry to `hooks/hooks.json` whose matcher covers exactly the five command names and whose command invokes `node "${CLAUDE_PLUGIN_ROOT}/hooks/proportionality-check.js"`. Keep the existing `SessionStart` and `SubagentStart` entries byte-for-byte equivalent.

Implement the classifier as a Node stdlib script. Read exactly one JSON object from stdin, validate `hook_event_name`, `command_name`, `command_args`, `prompt`, and `cwd` defensively, and exit without output for any event or command outside the allowlist. Resolve `ponytail.enabled` and `ponytail.enforcement` through the existing `hooks/gsd-tools.sh` helper rather than copying its GSD-tools search logic. Normalize only the documented booleans and enforcement enum (`advisory|warn|block`); default enforcement to `warn`.

Implement only enough deterministic classification for the tracer: recognize explicit milestone/project/roadmap scope as `milestone`, and read-only review/diagnosis language plus GitHub issue, PR, review, or issue-comment URLs as `direct`. Compare the recommended route with the command's implied scope and emit the enforcement-matrix response. Use JSON serialization for every hook response; never compose JSON with shell interpolation or evaluate prompt text.
  </action>
  <verify>
    <automated>cd ponytail-everywhere &amp;&amp; bash tests/test-proportionality-check.sh</automated>
  </verify>
  <done>The clear small-review mismatch is interrupted under the default mode before command expansion, clear milestone work proceeds, disabled Ponytail is silent, and non-target commands never enter the decision path.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Complete hybrid classification, enforcement, override, and fail-open coverage</name>
  <files>ponytail-everywhere/hooks/proportionality-check.js, ponytail-everywhere/tests/test-proportionality-check.sh</files>
  <behavior>
    - Test 1: Deterministic direct, quick, phase, and milestone examples produce the expected route without invoking the Claude stub.
    - Test 2: An ambiguous request invokes the Claude stub once and accepts only a schema-valid route/confidence/reason result.
    - Test 3: GitHub issue, pull-request, review, and issue-comment evidence uses only GET calls; every stubbed lookup receives a 3000 ms process timeout.
    - Test 4: Advisory permits a positive mismatch with context; warn interrupts only a positive mismatch; block permits proportionate work but requires the inline marker to override a positive mismatch.
    - Test 5: `[ponytail:milestone]` permits that submission, while the immediately following unmarked equivalent is independently blocked.
    - Test 6: Missing `gh`, lookup timeout/error, missing Claude, Claude timeout/error, invalid JSON, invalid route, and insufficient evidence all exit 0 with a concise non-blocking advisory in every enforcement mode.
    - Test 7: Each case leaves the temporary project tree unchanged apart from the test's pre-existing `.planning/config.json`.
  </behavior>
  <action>
Expand the tests first, preserving the stdlib-only shell style used by `tests/test-session-start.sh`. Put stub `gh`, `claude`, and `gsd-tools` executables on the temporary PATH and record calls in the test-owned temporary directory; do not add a fixture tree or test framework.

Complete deterministic routing with a short, ordered rule table inside the script: explicit one-shot marker; obvious milestone/project language; obvious read-only review/diagnosis language; bounded atomic fix language; existing-phase language; otherwise ambiguous. Keep the rules conservative: contradictory cues and weak single-word hits go to ambiguous rather than manufacturing confidence.

For ambiguity only, extract GitHub URLs with Node's URL parser, accept only `github.com`, convert recognized issue, pull, review, and issue-comment forms to fixed `gh api --method GET` endpoints, and run each lookup with Node's subprocess `timeout: 3000`. Treat external content as untrusted evidence, truncate it before classification, and never pass it to a shell command string. Invoke the locally installed Claude CLI in print mode once with a narrow prompt demanding a JSON object containing only `route`, `confidence`, and `reason`; parse and allowlist that result. Do not invoke the model when a deterministic route already exists.

Apply the enforcement matrix exactly. All operational errors and insufficient evidence return an allow response with advisory context, including in `block` mode. A positive mismatch in `warn` names all four route choices; a positive mismatch in `block` identifies the exact inline override. Do not write recommendation, audit, approval, cache, or planning files.
  </action>
  <verify>
    <automated>cd ponytail-everywhere &amp;&amp; bash tests/test-proportionality-check.sh &amp;&amp; bash tests/test-session-start.sh</automated>
  </verify>
  <done>All four routes, three modes, five target commands, unaffected commands, one-shot override, disabled behavior, small review work, milestone work, lookup limits, model-on-ambiguity-only behavior, and every failure fallback are executable regressions; the original ladder suite still passes.</done>
</task>

<task type="auto">
  <name>Task 3: Publish the configuration and operator contract</name>
  <files>ponytail-everywhere/.gsd/capabilities/ponytail/capability.json, ponytail-everywhere/.claude-plugin/plugin.json, ponytail-everywhere/README.md</files>
  <action>
Add `ponytail.enforcement` to the capability config as an enum with values `advisory`, `warn`, and `block`, defaulting to `warn`. Update the plugin description so it no longer claims the plugin is advisory-only. Do not bump versions or add a release workflow; source behavior and configuration are the requested deliverable, and the capability bundle hash already detects changed contents.

Document in README: the exact five-command allowlist; that the decision runs at Claude Code command expansion before durable planning artifacts; direct/quick/phase/milestone outcomes; the positive-mismatch definition; the three-mode matrix and default; exact `[ponytail:milestone]` resubmission semantics; deterministic-first and model-only-on-ambiguity behavior; optional read-only GitHub issue/PR/review lookups with an individual three-second timeout; fail-open advisory behavior; `ponytail.enabled=false` silence; and the no planning/audit artifact guarantee. State the current surface boundary plainly: Claude Code consumes this plugin's `UserPromptExpansion` hook, while Codex does not consume that Claude plugin hook and therefore does not receive this pre-command interception from this repository.

Keep the existing lazy-ladder level documentation and install/uninstall directions intact. Add no speculative Codex hook, shared policy engine, telemetry, or recommendation history.
  </action>
  <verify>
    <automated>cd ponytail-everywhere &amp;&amp; node -e 'for (const f of ["hooks/hooks.json",".gsd/capabilities/ponytail/capability.json",".claude-plugin/plugin.json"]) JSON.parse(require("fs").readFileSync(f,"utf8"))' &amp;&amp; bash tests/test-proportionality-check.sh &amp;&amp; bash tests/test-session-start.sh</automated>
  </verify>
  <done>The capability exposes the documented default-warn enum, the manifest description matches enforced behavior, README covers every requested operator outcome and limitation, both hook suites pass, and no dependency or release machinery was added.</done>
</task>

</tasks>

<threat_model>

## Trust Boundaries

| Boundary | Description |
|---|---|
| User prompt -> hook | Untrusted command arguments, prompt text, cwd, and marker text enter the classifier through stdin JSON. |
| Project config -> hook | Project-controlled `ponytail.enabled` and `ponytail.enforcement` values affect output and blocking. |
| GitHub/Claude -> classifier | Remote issue/PR/review content and model output are untrusted evidence, never authority or executable input. |
| Hook -> Claude Code | Hook stdout must remain valid event JSON because a malformed response can silently defeat or over-apply enforcement. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-WDK-01 | Tampering / Elevation | Prompt and command parsing | high | mitigate | Parse stdin with JSON.parse, use an exact command allowlist, validate enum/model outputs, never use eval, and pass all subprocess arguments as arrays. |
| T-WDK-02 | Spoofing | One-shot override | medium | mitigate | Recognize the exact marker only in the current submitted prompt and persist no approval state. |
| T-WDK-03 | Information disclosure | Model-backed ambiguity path | medium | mitigate | Send only bounded prompt/evidence excerpts needed for route classification; omit local file contents, transcripts, credentials, and environment values. |
| T-WDK-04 | Denial of service | GitHub/model subprocesses | medium | mitigate | Apply 3000 ms to each GitHub subprocess, a finite model timeout, and fail open with advisory context on every error. |
| T-WDK-05 | Tampering | Remote GitHub content or model response | high | mitigate | Treat both as data, constrain GitHub to recognized github.com URL shapes and GET endpoints, and accept only schema-valid route results. |
| T-WDK-06 | Repudiation | Recommendation persistence | low | accept | Recommendations intentionally create no audit artifact; the user sees the current hook response, and the product requirement forbids durable recommendation artifacts. |

</threat_model>

## Multi-Source Coverage Audit

| Source | Item | Covered by | Status |
|---|---|---|---|
| GOAL | Decide proportionality before scope-expanding GSD commands create durable planning artifacts | Task 1 | COVERED |
| REQ | Intercept exactly the five named commands; leave every other command unaffected | Task 1 | COVERED |
| REQ | Recommend direct, quick, phase, or milestone | Tasks 1-2 | COVERED |
| REQ | Deterministic checks first; model only for ambiguity | Task 2 | COVERED |
| REQ | Optional read-only GitHub issue/PR/review lookup with three-second timeout per call | Task 2 | COVERED |
| REQ | Failures and insufficient evidence continue advisably | Task 2 | COVERED |
| REQ | `ponytail.enforcement` advisory/warn/block, default warn | Tasks 1-3 | COVERED |
| REQ | Warn interrupts only positive mismatch and requires route choice; block requires override | Task 2 | COVERED |
| REQ | One-shot `[ponytail:milestone]` authorizes only the submitted command | Task 2 | COVERED |
| REQ | No recommendation planning/audit artifacts; disabled mode silent | Tasks 1-2 | COVERED |
| REQ | Preserve existing lazy-ladder guidance | Tasks 1-3 | COVERED |
| REQ | Tests cover allowlist, unaffected commands, review/milestone work, override, modes, disabled, and fallback | Tasks 1-2 | COVERED |
| REQ | README covers timing, outcomes, modes, override, lookups, no artifacts, and Codex limitation | Task 3 | COVERED |
| RESEARCH | No research phase; Level 1 verification established the existing Claude hook contract | Plan Header, Task 1 | COVERED |
| CONTEXT | No CONTEXT.md or deferred ideas were supplied; all task-source constraints are represented above | Entire plan | COVERED |

<verification>
Run from the nested repository:

`bash tests/test-proportionality-check.sh && bash tests/test-session-start.sh`

Then confirm `git status --short` lists only the six planned source files. Do not stage or commit from the parent repository.
</verification>

<success_criteria>

- A real Claude Code `UserPromptExpansion` payload for each allowlisted command reaches the proportionality hook before expansion; a non-target command does not.
- The complete enforcement matrix and failure fallback are proven through process-level tests using stdin/stdout and PATH stubs.
- No classifier path creates files in the test project, and `[ponytail:milestone]` has no effect on the next submission.
- Existing `tests/test-session-start.sh` stays green, demonstrating that lazy-ladder guidance was preserved.
- All JSON manifests parse and README documents the exact shipped contract without promising Codex interception.
</success_criteria>

<output>
Implementation commits belong only to the nested `ponytail-everywhere` repository. The executor should report the nested commit hash and leave the parent repository's untracked nested checkout unstaged.
</output>
