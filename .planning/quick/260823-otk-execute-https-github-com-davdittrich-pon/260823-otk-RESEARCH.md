# Quick Task 260823-otk: Plan-Review Verification Proportionality Research

<!-- rumdl-disable MD013 -->

**Researched:** 2026-08-23
**Domain:** gsd-core capability contribution and plan-checker prompt contract
**Confidence:** HIGH for repository and gsd-core 1.11.0 contract; MEDIUM for general testing guidance

<user_constraints>

## User Constraints

- Preserve the existing Claude `UserPromptExpansion` pre-expansion hook and its regression suite. Do not patch gsd-core. [CITED: https://github.com/davdittrich/ponytail-everywhere/issues/4#issuecomment-5386872743]
- Do not build a general parser, interpreter, fixture framework, or exhaustive execution matrix; do not reduce user-visible product scope to make verification smaller. [CITED: https://github.com/davdittrich/ponytail-everywhere/issues/4#issuecomment-5386872743]
- The checker must accept static identity proof for byte-identical mechanisms plus one dynamic execution per genuinely distinct behavior; invocation argv is part of behavioral identity. [CITED: https://github.com/davdittrich/ponytail-everywhere/issues/4]
</user_constraints>

## Summary

Use the capability contract that already exists: add one `plan:pre` contribution with `into: "checker"`, a static checker fragment, and resolved `ponytail.enforcement`. Do not add executable production logic. gsd-core 1.11.0 validates the contribution because the plan role list is exactly `"researcher", "planner", "checker"`, and its generic contract says a contribution injects `fragment.inline` verbatim into the named role. [VERIFIED: /home/dd/.codex/gsd-core/bin/lib/loop-host-contract.cjs:29-38; /home/dd/.codex/gsd-core/references/loop-hook-dispatch.md:25-30] (confidence 99/100)

The missing seam is dispatch, not schema. Standard `plan-phase.md` gathers planner-targeted fragments for the planner prompt, while its checker prompt has no checker-contribution block; Quick full similarly passes only `${AGENT_SKILLS_CHECKER}`. The declared checker contribution is therefore forward-compatible but inactive until gsd-core adds dispatch. Document [open-gsd/gsd-core#3771](https://github.com/open-gsd/gsd-core/issues/3771); do not work around it in core or duplicate the existing Quick planner bridge. [VERIFIED: /home/dd/.codex/gsd-core/workflows/plan-phase.md:734-744,951-1006; /home/dd/.codex/gsd-core/workflows/quick/steps/plan-checker-loop.md:17-54] (confidence 99/100)

**Primary recommendation:** ship a declarative checker contribution and executable contract tests now; state honestly that automatic checker delivery depends on #3771. (confidence 98/100)

## Existing Contract and Boundaries

1. The live capability already declares `plan:pre → planner`, with `when: "ponytail.enabled"`, `onError: "skip"`, and `configValues.level → ponytail.level`. Reuse that exact contribution shape for `checker`; do not modify `skills/quick-planner/render.cjs`, whose selector is deliberately `entry.into === 'planner'`. [VERIFIED: ponytail-everywhere/.gsd/capabilities/ponytail/capability.json:51-65; ponytail-everywhere/.gsd/capabilities/ponytail/skills/quick-planner/render.cjs:6-16] (confidence 99/100)
2. The existing enforcement values are exactly `"advisory", "warn", "block"`, default `"warn"`. Map them to the checker’s existing severities `"info", "warning", "blocker"`; do not invent a new output schema. [VERIFIED: ponytail-everywhere/.gsd/capabilities/ponytail/capability.json:39-47; /home/dd/.codex/agents/gsd-plan-checker.toml:901-907,950-981] (confidence 98/100)
3. The current command-expansion test already covers its five-command allowlist, all three enforcement modes, one-shot override, bounded GitHub GETs, timeouts, fail-open behavior, and unchanged project state. Baseline on 2026-08-23: all three repository test scripts pass. Leave `hooks/proportionality-check.js` and `tests/test-proportionality-check.sh` unchanged. [VERIFIED: ponytail-everywhere/tests/test-proportionality-check.sh:117-180; live run 2026-08-23] (confidence 99/100)
4. The revision loop forwards structured checker issues verbatim and tells the planner to make targeted updates; `fix_hint` is currently presented as an implementation suggestion. Until #3771 changes that upstream contract, the new fragment must require `description` to state the violated property plus evidence and require `fix_hint` to be explicitly non-binding (for example, “one valid proof is …; any smaller equivalent proof is acceptable”). [VERIFIED: /home/dd/.codex/gsd-core/workflows/quick/steps/plan-checker-loop.md:71-100; /home/dd/.codex/gsd-core/references/planner-revision.md:15-45] (confidence 97/100)

## Implementation-Ready Change Surface

| File | Required change |
|---|---|
| `.gsd/capabilities/ponytail/capability.json` | Add `plan:pre`, `into: "checker"`, `fragment.path: "fragments/checker-proportionality.md"`, `when: "ponytail.enabled"`, `configValues.enforcement: "ponytail.enforcement"`, `onError: "skip"`; broaden the enforcement description. Keep the planner contribution unchanged. |
| `.gsd/capabilities/ponytail/fragments/checker-proportionality.md` | Define the proportionality property, behavior identity (`mechanism bytes + argv/control-path semantics`), direct-proof preference, scope-reduction prohibition, non-binding remediation wording, and `advisory→info`, `warn→warning`, `block→blocker`. |
| `tests/test-plan-review-contribution.sh` | Use the real gsd-core 1.11.0 registry in a disposable project. Assert exactly one active Ponytail checker contribution, exact fragment resolution, all three resolved enforcement values, disabled silence, and the two executable examples below. No Markdown parser. |
| `.github/workflows/ci.yml` | Run the new focused shell test beside the three existing scripts. |
| `README.md`, `.gsd/capabilities/ponytail/NOTES.md` | Document semantics, current no-dispatch status, and #3771. Do not claim the checker receives the fragment today. |
| `.claude-plugin/plugin.json`, capability manifest | Bump both feature versions together from the exact current `"0.3.0"` to `"0.4.0"` so marketplace/cache consumers can distinguish the feature release. [VERIFIED: ponytail-everywhere/.claude-plugin/plugin.json:1-4; ponytail-everywhere/.gsd/capabilities/ponytail/capability.json:2-4] |

The focused executable examples should be literal and tiny: (a) two byte-identical resolver copies with the same argv tail require one dynamic call plus `cmp`/hash identity proof; (b) the same resolver bytes with different argv tails that select different commands require one call per tail. Assert spy argv directly, matching the repository’s existing exact-internal-call style. [VERIFIED: ponytail-everywhere/tests/test-quick-planner-bridge.sh:95-114] (confidence 95/100)

## Alternatives Considered

| Rank | Mechanism | Performance | Simplicity / LOC | Ecosystem support | Maintenance |
|---:|---|---|---|---|---|
| 1 | Existing `plan:pre → checker` contribution (recommended) | Best: static prompt only; no extra process | Best: one fragment + manifest entry | Native gsd-core schema and resolver | Lowest; upstream dispatch activates it |
| 2 | `agent_skills.gsd-plan-checker` bridge mirroring Quick planner | One extra shell/Node render per checker run | More skill/renderer/config/test code | Works only where each project appends the bridge | Temporary seam must later be removed; duplicates #3771 responsibility |
| 3 | `plan:post` executable gate | Runs after every checker/revision loop and needs a check implementation | Highest LOC; tends toward the forbidden parser | Native gate API, wrong lifecycle timing | Own parser/check semantics indefinitely |

Patching `plan-phase.md` would provide immediate native dispatch but is explicitly out of scope and creates a local fork, so it is rejected before ranking. [CITED: <https://github.com/davdittrich/ponytail-everywhere/issues/4#issuecomment-5386872743>] (confidence 100/100)

## Verification and Pitfalls

- Prefer narrow assertions and avoid repeating behavior already proven at a lower level; retain a higher-level execution only when it adds confidence unavailable from static identity. This matches Google’s narrow-assertion guidance and the Practical Test Pyramid’s “avoid test duplication” rule. [CITED: <https://testing.googleblog.com/2024/04/prefer-narrow-assertions-in-unit-tests.html>] [CITED: <https://martinfowler.com/articles/practical-test-pyramid.html#avoid-test-duplication>] (confidence 88/100)
- Do not conflate identical source with identical behavior: different argv tails are different behavior even when resolver bytes match. Conversely, do not Cartesian-product shells, paths, hosts, and fixtures when those dimensions do not alter behavior. [CITED: <https://github.com/davdittrich/ponytail-everywhere/issues/4>] (confidence 97/100)
- Do not add `required_property` or `evidence` YAML keys as if gsd-core 1.11.0 guarantees them; encode both in `description` until #3771 lands. [VERIFIED: /home/dd/.codex/agents/gsd-plan-checker.toml:950-981] (confidence 96/100)
- Editing any capability-bundle file changes the consent hash; re-install/re-consent during integration verification. [VERIFIED: ponytail-everywhere/.gsd/capabilities/ponytail/NOTES.md:82-86] (confidence 99/100)

## Security and Project Constraints

No new package, network call, parser, executable gate, authentication, session, access-control, or cryptography surface is needed. The only trust-boundary value is already registry-validated enum configuration; the new fragment remains static installed content and must not interpolate or execute plan text. [VERIFIED: ponytail-everywhere/.gsd/capabilities/ponytail/capability.json:23-48; /home/dd/.codex/gsd-core/references/loop-hook-dispatch.md:27-30] (confidence 97/100)

Honor `AGENTS.md`: bead `gsd-beads-3c6` is the edit lock; use the full GSD/checker gate already in progress; tests first; exact spy assertions; no unrelated cleanup; conventional commit without attribution; no push unless separately authorized. [VERIFIED: AGENTS.md:1-125; `bd show gsd-beads-3c6` on 2026-08-23] (confidence 99/100)

## Sources

- [Owner issue and acceptance contract](https://github.com/davdittrich/ponytail-everywhere/issues/4) and [owner brief](https://github.com/davdittrich/ponytail-everywhere/issues/4#issuecomment-5386872743). [CITED]
- [gsd-core v1.11.0 loop host contract](https://github.com/open-gsd/gsd-core/blob/v1.11.0/gsd-core/bin/lib/loop-host-contract.cjs#L29-L38), [generic dispatch contract](https://github.com/open-gsd/gsd-core/blob/v1.11.0/gsd-core/references/loop-hook-dispatch.md#L25-L30), [plan workflow](https://github.com/open-gsd/gsd-core/blob/v1.11.0/gsd-core/workflows/plan-phase.md), [Quick checker loop](https://github.com/open-gsd/gsd-core/blob/v1.11.0/gsd-core/workflows/quick/steps/plan-checker-loop.md), and [planner revision reference](https://github.com/open-gsd/gsd-core/blob/v1.11.0/gsd-core/references/planner-revision.md). Tag `v1.11.0` resolves to commit `182f60b4c170785d96f1deb87fea8b108e9b985f`. [VERIFIED: GitHub API 2026-08-23]
- [Upstream revision-contract issue #3771](https://github.com/open-gsd/gsd-core/issues/3771). [CITED]
- Web query performed: `plan verification proportionality best practice 2026`; the relevant software-testing evidence selected from the results is Google’s narrow-assertion guidance and Fowler/Thoughtworks’ test-duplication guidance above. [VERIFIED: web search 2026-08-23] (confidence 90/100)
