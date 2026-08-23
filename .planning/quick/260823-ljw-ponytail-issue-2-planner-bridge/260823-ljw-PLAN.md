---
quick_id: 260823-ljw
slug: ponytail-issue-2-planner-bridge
date: 2026-08-23
type: tdd
wave: 1
depends_on: []
files_modified:
  - ponytail-everywhere/.gsd/capabilities/ponytail/skills/quick-planner/SKILL.md
  - ponytail-everywhere/.gsd/capabilities/ponytail/skills/quick-planner/render.cjs
  - ponytail-everywhere/tests/test-quick-planner-bridge.sh
  - ponytail-everywhere/.github/workflows/ci.yml
  - ponytail-everywhere/README.md
  - ponytail-everywhere/.gsd/capabilities/ponytail/NOTES.md
  - ponytail-everywhere/.gsd/capabilities/ponytail/capability.json
  - ponytail-everywhere/.claude-plugin/plugin.json
autonomous: true
must_haves:
  truths:
    - A project-configured Ponytail bridge delivers the active plan:pre planner contribution exactly once to standard, validate, and full Quick planning.
    - The bridge emits no Ponytail guidance when the capability is disabled, runtime-incompatible, or has no active planner contribution.
    - lite, full, and ultra use the existing capability fragment and resolved configValues.level; no ladder text is copied into the bridge.
    - Existing gsd-planner skill entries remain present and ordered before the appended bridge.
    - The implementation changes no gsd-core source or installed runtime.
  artifacts:
    - ponytail-everywhere/.gsd/capabilities/ponytail/skills/quick-planner/SKILL.md
    - ponytail-everywhere/.gsd/capabilities/ponytail/skills/quick-planner/render.cjs
    - ponytail-everywhere/tests/test-quick-planner-bridge.sh
    - ponytail-everywhere/README.md
  key_links:
    - .planning/config.json agent_skills.gsd-planner -> .gsd/capabilities/ponytail/skills/quick-planner/SKILL.md
    - SKILL.md -> gsd-tools loop render-hooks plan:pre --raw -> render.cjs stdin
    - render.cjs -> activeHooks capId=ponytail kind=contribution into=planner -> fragment.inline
---

- **Mechanism:** Project-relative planner bridge skill piping the authoritative `plan:pre` hook registry into a pure Node-stdlib stdin selector.
- **Forbidden:** Copied ladder prose, gsd-core source/runtime patches, runtime-specific global skill paths, replacement of existing planner skills, new dependencies.
- **Audit:** PATH spy proves the skill command's exact `gsd-tools loop render-hooks plan:pre --raw` internal call; real disposable-project integration proves public planner-skill and capability behavior.

<objective>
Implement and push [ponytail-everywhere issue #2](https://github.com/davdittrich/ponytail-everywhere/issues/2): deliver Ponytail's existing planner ladder to every GSD Quick mode through the supported per-project `agent_skills.gsd-planner` seam, without changing gsd-core.
</objective>

## Alternatives Considered

- **Project-relative bridge skill (selected)**: Reuse gsd-core 1.11.0's existing `agent_skills.gsd-planner` include and `loop render-hooks plan:pre --raw` registry; the approved downstream contract is documented in [ponytail-everywhere #2, 2026](https://github.com/davdittrich/ponytail-everywhere/issues/2). One tiny stdlib renderer centralizes filtering and makes exact behavior executable.
  Decided by: simplicity and LOC.
- **Native Quick plan:pre dispatch**: The clean final architecture is specified in [open-gsd/gsd-core #3778, 2026](https://github.com/open-gsd/gsd-core/issues/3778), but it is open and unreleased; downstream adoption is explicitly deferred in [ponytail-everywhere #5, 2026](https://github.com/davdittrich/ponytail-everywhere/issues/5).
  Decided by: ecosystem support; unavailable today.
- **Patch installed gsd-core quick.md**: A local workflow patch could add native dispatch immediately, but [open-gsd/gsd-core #3778, 2026](https://github.com/open-gsd/gsd-core/issues/3778) identifies this as upstream-owned shared behavior, making downstream patches drift-prone and runtime-install-specific.
  Decided by: maintenance overhead; rejected.
- **Claude SubagentStart hook only**: Existing Claude hooks can mask the gap, but issue #2's [2026 agent brief](https://github.com/davdittrich/ponytail-everywhere/issues/2#issuecomment-5386207713) requires runtime-neutral delivery and explicitly excludes runtime-specific hook workarounds.
  Decided by: ecosystem support; rejected.

<tasks>
<task type="tracer" tdd="true">
<name>Task 1: Prove, implement, document, version, and publish the Quick planner bridge</name>
<beads-id>gsd-beads-xx8</beads-id>
<reversibility rating="reversible">All behavior is additive inside the Ponytail bundle and its test/docs metadata; reverting the nested-repository commit restores 0.2.0 behavior without data migration.</reversibility>
<files>ponytail-everywhere/.gsd/capabilities/ponytail/skills/quick-planner/SKILL.md, ponytail-everywhere/.gsd/capabilities/ponytail/skills/quick-planner/render.cjs, ponytail-everywhere/tests/test-quick-planner-bridge.sh, ponytail-everywhere/.github/workflows/ci.yml, ponytail-everywhere/README.md, ponytail-everywhere/.gsd/capabilities/ponytail/NOTES.md, ponytail-everywhere/.gsd/capabilities/ponytail/capability.json, ponytail-everywhere/.claude-plugin/plugin.json</files>
<behavior>
- RED: a disposable project with an existing planner skill cannot currently resolve a Ponytail project-relative bridge or receive its planner fragment in any Quick mode.
- GREEN: the bridge command invokes exactly `gsd-tools loop render-hooks plan:pre --raw`, pipes JSON to the selector, selects only the first active `capId=ponytail`, `kind=contribution`, `into=planner` entry, and emits its `fragment.inline` once.
- GREEN: standard, `--validate`, and `--full` Quick initialization all retain the same ordered planner-skill block and produce the ladder once.
- GREEN: disabled, runtime-incompatible, and absent-contribution fixtures emit zero bytes.
- GREEN: lite, full, and ultra each match the authoritative active hook's inline fragment and resolved `configValues.level`.
- GREEN: plugin and capability versions match at 0.3.0; CI runs the new real-gsd-core integration check plus both existing suites.
</behavior>
<action>
Write `tests/test-quick-planner-bridge.sh` first. Use `mktemp -d`, project-scope capability installation, and gsd-core 1.11.0; create a pre-existing planner skill, append the bridge path, and compare ordered `agent-skills` blocks across standard/validate/full Quick initialization. Add a PATH spy fixture that records exact renderer argv before returning controlled hook JSON. Cover disabled, runtime-incompatible, absent contribution, duplicate matching hooks, and lite/full/ultra without mutating real user state.

Then add one skill and one Node-stdlib stdin selector inside the capability bundle. The skill tells the planner to run `gsd-tools loop render-hooks plan:pre --raw | node .gsd/capabilities/ponytail/skills/quick-planner/render.cjs` once and apply non-empty stdout as advisory planning guidance. The selector reads stdin only, parses JSON, filters exact hook identity/type/target, emits at most one `fragment.inline`, and fails silent for parse, shape, or absence failures to preserve `onError: skip`. The shell owns process execution because Codex sandbox rejects nested Node `spawnSync` with `EPERM`; direct shell execution is verified working. Do not copy any ladder sentence.

Replace CI's config-only gsd-tools stub with the official pinned `@opengsd/gsd-core@1.11.0` CLI, then run the new integration test and existing tests. Document project-scope capability installation, the additive `.planning/config.json` entry, non-inheritance from user defaults, runtime-neutral Quick coverage, and future removal after #3778/#5. Update NOTES.md's delivery truth. Bump both Ponytail manifests from 0.2.0 to 0.3.0. Do not edit gsd-core, parent marketplace metadata, executor/verifier delivery, or unrelated files.
</action>
<verify>
<automated>cd ponytail-everywhere &amp;&amp; bash tests/test-quick-planner-bridge.sh &amp;&amp; bash tests/test-session-start.sh &amp;&amp; bash tests/test-proportionality-check.sh &amp;&amp; test "$(jq -r .version .claude-plugin/plugin.json)" = "$(jq -r .version .gsd/capabilities/ponytail/capability.json)"</automated>
</verify>
<done>Issue #2's eight acceptance checks pass in disposable projects; only the eight named Ponytail files change; gsd-core and installed runtime remain unchanged; nested main is committed and fast-forward pushed.</done>
</task>
</tasks>

<threat_model>
| ID | Category | Component | Severity | Disposition | Mitigation |
|---|---|---|---|---|---|
| T-LJW-01 | Tampering | Hook JSON | high | mitigate | Parse JSON, validate array/object/string shapes, filter exact capId/kind/into fields, never eval content. |
| T-LJW-02 | Elevation of privilege | Skill command pipeline | high | mitigate | Fixed `gsd-tools` and project-relative selector argv, no interpolation or user-derived arguments; selector never spawns a process. |
| T-LJW-03 | Denial of service | Missing or failing gsd-tools | low | accept | Return zero with empty stdout, matching the declared `onError: skip` contract. |
| T-LJW-04 | Spoofing | Duplicate active hooks | medium | mitigate | Emit only the first exact Ponytail planner contribution; spy fixture proves exactly-once output. |
| T-LJW-05 | Information disclosure | Diagnostics | low | mitigate | Do not forward gsd-tools stderr or JSON parse errors into planner prompt. |
</threat_model>

<verification>
Run the task's automated command, inspect the nested diff against `origin/main`, then verify GitHub remote SHA equals the local nested HEAD after a normal push. Verify the parent quick plan/summary/state commit stages no pre-existing dirty file and push parent main normally.
</verification>

<success_criteria>
- Exactly one authoritative Ponytail planner fragment reaches all three Quick modes when configured.
- Disabled, incompatible, and absent cases are silent; level resolution comes from capability state.
- Existing planner skills remain ordered and no global runtime skill root is required.
- Tests, documentation, version parity, nested push, parent GSD state, and bead closure are complete.
</success_criteria>

<output>
Create `260823-ljw-SUMMARY.md` and `260823-ljw-VERIFICATION.md`; record the nested commit and remote SHA. Keep `gsd-beads-xx8` authoritative.
</output>
