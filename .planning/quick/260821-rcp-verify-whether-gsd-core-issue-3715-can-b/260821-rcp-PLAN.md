---
quick_id: 260821-rcp
slug: verify-whether-gsd-core-issue-3715-can-be-replicated
date: 2026-08-21
phase: quick-260821-rcp
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md
autonomous: true
estimate:
  tokens: 12000
  raw_tokens: 12000
  tasks: 1
  confidence: low
must_haves:
  truths:
    - The original issue's sequential project-A/project-B overwrite claim is reported separately from the maintainer's no-model-line diagnosis.
    - At gsd-core commit adb46cdd85add7928977a5664793267efdfca83f, project-local model overrides are tested sequentially against one disposable global Codex home.
    - The positive control places the same override at the disposable HOME's ancestor .planning/config.json and proves the installer can emit the model when configuration discovery can reach it.
    - The real user HOME and global Codex installation are unchanged, and no repository source file is modified.
    - Bead gsd-beads-6kl records the observed verdict and is closed only after the evidence summary exists.
  artifacts:
    - .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md
  key_links:
    - exact SHA checkout -> bin/install.js --codex --global
    - disposable HOME/.codex/agents/gsd-planner.toml -> negative A, negative B, positive-control assertions
    - 260821-rcp-SUMMARY.md -> bd comment and closure for gsd-beads-6kl
---

<objective>
Determine whether open-gsd/gsd-core#3715's reported cross-project model overwrite reproduces under the exact environment described by maintainer comment 5372430413.

Purpose: Distinguish the issue's claimed "project B overwrites project A" behavior from the maintainer's separate finding that an ordinary project-local configuration is not discovered at all by a global Codex install.

Output: A concise quick SUMMARY containing the exact-SHA commands, the two negative-control results, the positive-control result, the real-HOME integrity check, and the bead disposition. This is diagnosis only; no gsd-core or gsd-beads source patch is authorized.
</objective>

<execution_context>
@/home/dd/.codex/gsd-core/workflows/execute-plan.md
@/home/dd/.codex/gsd-core/templates/summary.md
</execution_context>

<context>
@AGENTS.md
@.planning/STATE.md

External evidence:
- Original report (2026): https://github.com/open-gsd/gsd-core/issues/3715 — claims that two project-local `model_overrides.gsd-planner` values are baked sequentially into the same global `~/.codex/agents/gsd-planner.toml`, with project B overwriting project A.
- Maintainer diagnosis (2026): https://github.com/open-gsd/gsd-core/issues/3715#issuecomment-5372430413 — reports no `model =` line after either project-local install at exact next SHA `adb46cdd85add7928977a5664793267efdfca83f`; a `$HOME/.planning/config.json` positive control emits the model because it is an ancestor of `$HOME/.codex`.

Pinned installer contract at that SHA:
- `package.json` version is `1.11.0`, requires Node.js >=24, and maps the `gsd-core` bin to `bin/install.js`.
- Invoke the checked-out bundle directly as `node bin/install.js --codex --global`; do not substitute `@latest`, an npm tag, or a different commit.
</context>

## Alternatives Considered

- **Secure `/tmp` HOME fixture with direct exact-SHA installer invocation (chosen).** GNU Coreutils documents `mktemp -d` as the safe directory-creation primitive and warns against predictable temporary names ([GNU Coreutils 9.10 `mktemp`, 2026](https://manpages.debian.org/testing/coreutils/mktemp.1.en.html)); the maintainer's reproduction explicitly used a sandboxed `HOME` with no `CODEX_HOME` override ([issue comment 5372430413, 2026](https://github.com/open-gsd/gsd-core/issues/3715#issuecomment-5372430413)). This exactly matches the evidence under review while containing all installer writes.
- **Containerized installer run.** A container could isolate filesystem writes and bind only an evidence directory ([Docker `docker container run` reference, accessed 2026-08-21](https://docs.docker.com/reference/cli/docker/container/run/)), but adds an image/runtime dependency and changes more environmental variables than the maintainer's stated setup.
- **Real user HOME with backup and restore.** This most literally exercises the existing global install path described in the original report ([open-gsd/gsd-core#3715, 2026](https://github.com/open-gsd/gsd-core/issues/3715)), but is rejected by the task's safety boundary: backup/restore cannot make an installer run against the live home risk-free.

Decided by: simplicity/LOC. The first two approaches both isolate writes; the disposable HOME uses only `mktemp`, `env`, Git, and the pinned Node entry point, and reproduces the maintainer's environment without container-specific confounders.

<tasks>

<task type="tracer">
  <name>Task 1: Run the exact-SHA two-project reproduction and record the verdict</name>
  <files>.planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md</files>
  <precondition>`node -p 'Number(process.versions.node.split(".")[0]) &gt;= 24'` prints `true`, Git can fetch public commit `adb46cdd85add7928977a5664793267efdfca83f`, and bead `gsd-beads-6kl` is `in_progress`.</precondition>
  <action>
Create one secure fixture with `mktemp -d /tmp/gsd-3715.XXXXXX` and store its path in a task-specific variable such as `repro_root`; never assign to the shell's own `HOME` variable. Before any installer call, record whether the real `$HOME/.codex/agents/gsd-planner.toml` exists and, when it exists, its SHA-256. Also capture the repository's current porcelain status in the fixture so pre-existing user changes are not mistaken for task changes.

Fetch gsd-core into `$repro_root/gsd-core`, detach at exactly `adb46cdd85add7928977a5664793267efdfca83f`, and make `git rev-parse HEAD` equality a blocking assertion. Do not install dependencies: the repository's bundled `bin/install.js` is the pinned executable. Create `$repro_root/home/projA/.planning/config.json` with `runtime: "codex"`, `resolve_model_ids: "omit"`, and `model_overrides.gsd-planner: "gpt-5.6-sol"`; create the equivalent project-B config with `"gpt-5.6-luna"`.

From project A, run `node $repro_root/gsd-core/bin/install.js --codex --global` through `env -u CODEX_HOME HOME=$repro_root/home`. Assert the command succeeds, copy the generated `$repro_root/home/.codex/agents/gsd-planner.toml` to a fixture evidence file with `cp -f`, and assert it contains no line matching `^model[[:space:]]*=`. Repeat from project B against the same disposable HOME and same global target, preserve the second TOML separately, and assert it also contains no model line. These are two distinct negative assertions: project A did not bake `gpt-5.6-sol`, and project B did not bake or overwrite it with `gpt-5.6-luna`.

For the positive control, write `$repro_root/home/.planning/config.json` with the same Codex settings and `model_overrides.gsd-planner: "gpt-5.6-sol"`, rerun the exact installer under the same disposable HOME, preserve the resulting TOML, and assert it now contains exactly `model = "gpt-5.6-sol"`. This control proves the pin mechanism and harness work when the configuration is an ancestor of the global target; do not interpret it as evidence for the original overwrite claim.

Re-check the real global planner TOML's existence and SHA-256 and require exact equality with the pre-run state. Compare the repository porcelain status with the captured pre-run status while allowing only this quick task's PLAN/SUMMARY artifact; leave every existing unrelated dirty or untracked path untouched.

Create the SUMMARY with: date and platform versions; exact checkout SHA; exact installer invocation; the original issue claim as an `ASSERTION UNDER TEST`, not an observed fact; negative A and B results as separate rows; positive-control result; the real-HOME integrity result; and a two-part verdict stating (1) whether the issue's overwrite symptom reproduced and (2) whether maintainer comment 5372430413 reproduced. State the likely mechanism only as evidence-backed diagnosis: global target `$HOME/.codex` searches ancestors, so ordinary descendant project configs are not incorporated. Explicitly state that no source patch was attempted or authorized.

After the SUMMARY passes all checks, add one concise `bd comments add gsd-beads-6kl` comment containing both verdicts and the SUMMARY path, then close the bead with `bd close gsd-beads-6kl --reason "Exact-SHA reproduction recorded in 260821-rcp-SUMMARY.md"`. Do not commit, push, or run Dolt remote sync.
  </action>
  <verify>
    <automated>test -f .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md &amp;&amp; rg -q 'adb46cdd85add7928977a5664793267efdfca83f' .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md &amp;&amp; rg -q 'gpt-5\.6-sol' .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md &amp;&amp; rg -q 'gpt-5\.6-luna' .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md &amp;&amp; rg -qi 'real.*HOME.*unchanged|unchanged.*real.*HOME' .planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md &amp;&amp; test "$(bd show gsd-beads-6kl --json | jq -r '.[0].status')" = closed</automated>
  </verify>
  <done>The exact commit has two separately captured project-local negative results and one ancestor-config positive result; SUMMARY distinguishes the original claim from the maintainer diagnosis, proves the real global Codex target stayed unchanged, records that no patch was made, and bead gsd-beads-6kl is closed with the evidence path.</done>
</task>

</tasks>

<threat_model>

## Trust Boundaries

| Boundary | Description |
|---|---|
| Public gsd-core commit -> local Node process | A fetched upstream installer executes filesystem writes. |
| Fixture project configs -> global-install resolver | Project-controlled JSON influences generated agent TOML content. |
| Disposable HOME -> real user HOME | A mistaken environment or `CODEX_HOME` value could redirect writes into the live Codex installation. |
| Reproduction evidence -> bd state | A wrong or conflated verdict could prematurely close the tracked diagnosis task. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| T-RCP-01 | Tampering | Upstream checkout identity | high | mitigate | Detach and assert the full 40-character SHA before executing `bin/install.js`; never use a mutable npm tag. |
| T-RCP-02 | Elevation of Privilege / Tampering | Installer destination | high | mitigate | Every installer invocation uses process-scoped `env -u CODEX_HOME HOME=$repro_root/home`; the real planner TOML existence/hash is checked before and after. |
| T-RCP-03 | Repudiation | Sequential observations | medium | mitigate | Preserve A, B, and positive-control TOMLs separately inside the fixture and report them as three rows, preventing the last run from erasing the earlier evidence. |
| T-RCP-04 | Tampering | Existing repository worktree | high | mitigate | Snapshot porcelain status before the reproduction and compare after it; permit only the requested quick artifacts and preserve all unrelated user changes. |
| T-RCP-05 | Spoofing | Positive-control interpretation | medium | mitigate | SUMMARY labels the ancestor config as a harness control, never as reproduction of cross-project overwrite. |
| T-RCP-06 | Denial of Service | Public Git fetch | low | accept | A network failure leaves the bead open and produces no diagnosis; no retry/download framework is warranted for this one-shot verification. |

</threat_model>

## Multi-Source Coverage Audit

| Source | Item | Covered by | Status |
|---|---|---|---|
| GOAL | Verify whether issue 3715 reproduces from maintainer comment 5372430413 | Task 1 | COVERED |
| REQ | Preserve the original sequential overwrite claim as a separate assertion | Task 1 SUMMARY contract | COVERED |
| REQ | Test exact SHA adb46cdd85add7928977a5664793267efdfca83f | Task 1 checkout assertion | COVERED |
| REQ | Run project A and project B against the same disposable global Codex home | Task 1 negative controls | COVERED |
| REQ | Run `$HOME/.planning/config.json` positive control | Task 1 positive control | COVERED |
| REQ | Never alter real HOME or global Codex installation | Task 1 isolation and hash assertions | COVERED |
| REQ | Diagnosis only; no source patch | Objective, Task 1 SUMMARY contract | COVERED |
| REQ | Track implementation state in gsd-beads-6kl | Task 1 final bd comment and close | COVERED |
| RESEARCH | No research phase requested; official issue/comment and pinned package entry point provide sufficient Level 1 evidence | Context, Alternatives Considered | COVERED |
| CONTEXT | No CONTEXT.md, locked D-XX decisions, or deferred ideas supplied; all orchestrator constraints are represented above | Entire plan | COVERED |

<verification>
Run Task 1's automated check. Then inspect the SUMMARY once to confirm the two verdicts are explicit and separate: original overwrite symptom reproduced or not; maintainer no-model-line behavior reproduced or not.
</verification>

<success_criteria>

- Both project-local installs and the ancestor-config positive control run from the same exact gsd-core commit and same disposable HOME.
- Evidence supports each assertion independently; no last-run-only inspection can mask the A or B result.
- The real global Codex planner definition is byte-identical in existence/content before and after.
- The repository receives only PLAN/SUMMARY evidence, no source change, and all pre-existing user changes remain untouched.
- Bead gsd-beads-6kl carries the result and closes only after the SUMMARY is verifiable.
</success_criteria>

<output>
Create `.planning/quick/260821-rcp-verify-whether-gsd-core-issue-3715-can-b/260821-rcp-SUMMARY.md` when done. Do not commit or push; hand off changed-file and validation status under the repository's conservative Beads profile.
</output>
