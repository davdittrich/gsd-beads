# Phase 21: Installed Cutover and Patch 2 Retirement - Context

**Gathered:** 2026-09-01
**Status:** Ready for planning

<domain>

## Phase Boundary

Prove that gsd-core's public task-content command resolves one naturally
synced Phase 21 task from live Beads through the active global capability,
with tracked source, project install, and global install byte-identical. Only
after fresh positive and isolated negative proofs may Phase 21 remove Patch 2.
Patch 1 remains installed, documented, tested, and independently verified.

</domain>

<decisions>

## Implementation Decisions

### Cutover transaction

- **D-01:** Treat cutover as one fresh fail-closed transaction at one exact
  source SHA. Runtime paths, active registry state, installed bytes, live Beads
  discovery, the public positive proof, and every negative arm must be observed
  immediately before retirement. Evidence from earlier runs is context, never a
  gate result.
- **D-02:** Resolve tracked, project-installed, and global-installed bundle
  paths from the current runtime and installer output. Do not hard-code a
  Claude, Codex, plugin-cache, or `$HOME/.gsd` location. Compare the complete
  bundle trees, not only `capability.json`; require byte identity and no
  source-only or install-only paths.
- **D-03:** The public positive proof must run outside repository ancestry so a
  project overlay cannot satisfy a claim about the global install. Pass the
  absolute real plan path and bind the supported live Beads database locator;
  require the active registry to name the runtime-derived global bundle. Do not
  copy, import, or replay Beads data.
- **D-04:** Gate order is binding: complete bundle parity and active-registry
  proof; live database discovery; public positive resolution; isolated public
  negative matrix; only then Patch 2 removal; then repeat native positive proof,
  the negative matrix, complete capability tests, and Patch 1 verification.
- **D-05:** Any pre-removal failure emits `SPEC_FAILURE` and leaves Patch 2
  installed. Before changing a machine-local workflow, capture its exact bytes
  in the session scratchpad. If a post-removal check fails, restore only those
  exact bytes and halt with `SPEC_FAILURE`; do not improvise a fallback. —
  **Reversibility:** costly — the live workflow is shared across projects, so a
  failed cutover must not propagate a partially retired read path.

### Live proof task

- **D-06:** Use the first exact `auto` or `tracer` task that Phase 21's normal
  `plan:post` Beads sync creates or resolves. Before proof, require its plan
  block to contain both exact `tracker-id="beads:<id>"` and `<beads-id><id>`
  identities and require `bd show <id> --json` to return the same live row.
- **D-07:** Do not use a synthetic task. Do not use the current Phase 20 plan as
  proof: direct live inspection found no persisted native identity in its task
  opening tags. The Phase 21 task is naturally accumulated workflow data and
  exercises the code that will actually ship.
- **D-08:** The proof succeeds only when the public command reports resolved
  content containing the live task's authored fields. Direct adapter output,
  parser-only success, unit mocks, or a project-overlay resolution are
  supporting evidence, not CUT-01 completion.

### Negative-path matrix

- **D-09:** Before retirement, require four public-boundary arms: unknown native
  task id; a real legacy `<beads-id>`-only plan task; unavailable/failing `bd`;
  and malformed resolver stdout. The existing Phase 19 suite remains
  responsible for missing script, timeout, ambiguous envelope, wrong field
  type, duplicate heading, and unusable-content branches; do not duplicate its
  whole matrix in Phase 21.
- **D-10:** Each negative arm changes exactly one factor from the known-good
  installed baseline. Use bounded outside-ancestry scratch, keep the live
  database and live install read-only, and assert nonzero exit, no resolved
  object, and no fallback task content. A combined multi-fault fixture, skip,
  xfail, warning-only result, or environment dismissal is not evidence.
- **D-11:** Spy exact internal `bd` argv in focused adapter tests and test the
  external contract through `task resolve-content`. Internal spies prove how;
  the public command proves what.

### Patch 2 retirement and history

- **D-12:** Delete every active Patch 2 surface: installed marker-bracketed
  workflow blocks; marker constant; `PATCH_CHECKS["execute-plan"]` entry;
  wrapper and call sites; CLI target; installer or detector invocation;
  Patch-2-specific tests; and active operational documentation. Add no alias,
  inert marker, tombstone command, compatibility branch, or new cutover
  framework.
- **D-13:** Preserve historical truth in `CHANGELOG.md`, archived planning
  artifacts, Beads records, and Git history, and add the current retirement
  entry. Historical statements remain historical; active instructions must no
  longer tell operators to install, check, or restore Patch 2.
- **D-14:** Patch 1 is outside the deletion set. Preserve its marker, live
  workflow block, checker behavior, tests, documentation, and installer wiring
  byte-for-byte unless a mechanically inseparable call-site deletion is
  required. Do not collapse or redesign the surviving one-entry checker table;
  adjacent cleanup is not part of cutover.
- **D-15:** Keep code, tests, and operational documentation in the same task and
  commit. Do not create a standalone documentation work unit or a reusable
  migration utility.

### the agent's Discretion

The user delegated all four areas to Ponytail, scientific-critical-thinking,
Beads, and codebase-design. The planner may choose exact test names, diagnostic
wording, the deterministic whole-tree comparison command, and the supported
runtime-derived database locator. It may not weaken the fresh-evidence order,
use synthetic task data, let the project overlay prove the global install,
combine negative variables, retain active Patch 2 residue, or alter Patch 1.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone contract

- `.planning/PROJECT.md` — v1.4 target features, failure boundary, and Patch 1
  exclusion.
- `.planning/REQUIREMENTS.md` — CUT-01, CUT-02, and explicit out-of-scope list.
- `.planning/ROADMAP.md` — Phase 21 goal and three observable success criteria.
- `.planning/STATE.md` — fresh registry, installed-byte, database-discovery,
  and public-command proof requirement.
- `.planning/research/SUMMARY.md` — validated native resolver mechanism,
  alternatives, risks, and installed-runtime findings.
- `.planning/phases/19-native-resolver-contract-and-failure-boundary/19-CONTEXT.md`
  — locked resolver schema, failure classes, and verification discipline.
- `.planning/phases/20-additive-identity-migration-and-compatibility/20-CONTEXT.md`
  — locked additive identity and checkpoint-preservation contract.

### Beads capability source

- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` — sole
  resolver declaration and installed feature manifest.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` — adapter,
  patch checker table, wrapper, call sites, and CLI routing.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` — current
  public/adapter tests and Patch 1/Patch 2 checker coverage.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/GSD-CORE-PATCH.md` — active
  Patch 1 and Patch 2 operational blocks and retirement inventory.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md`
  — plan-time Patch 2 detector invocation.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md`
  — surviving patch verification and status integration.
- `plugins/beads-lifecycle/hooks/capability-auto-install.sh` — runtime-derived
  global installation mechanism and whole-bundle drift check.
- `README.md` — active installed-cutover user contract.
- `CHANGELOG.md` — append-only release history and retirement record.

### Installed gsd-core contract

- `/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs` — public exact-id
  routing for `task resolve-content`.
- `/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs` — active
  registry selection, invocation, timeout, and hard-failure result classes.
- `/home/dd/.codex/gsd-core/bin/lib/capability-loader.cjs` — project/global
  overlay composition and precedence.
- `https://github.com/open-gsd/gsd-core/blob/next/docs/reference/capability-manifest.md`
  — current official resolver declaration, unique prefix, argv placeholder,
  and bounded timeout contract.
- `https://docs.python.org/3/library/os.html#os.execv` — current `os.execv`
  process-replacement and argv semantics.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets

- `gsd_run task resolve-content`: the only accepted public cutover oracle.
- `gsd_run capability list --raw`: current active-registry and installed-source
  evidence; it already exposes scope and source path.
- `capability-auto-install.sh`: existing whole-bundle hashing and global install
  path; extend no installer framework.
- `check_patch`, `PATCH_CHECKS`, and Patch 1 tests: retain the existing deep
  checker interface while deleting only the Patch 2 variant.
- Existing Phase 19 adapter tests: retain their exhaustive internal failure
  matrix instead of rebuilding it at the installed layer.

### Established Patterns

- `bd` remains the live authority; plan identity is an explicit projection,
  never title-matched.
- Resolver invocation uses typed argv, Python's standard library, bounded
  execution, JSON-only success output, and nonzero fail-closed errors.
- Real Beads tests use outside-repository scratch; repository-ancestry scratch
  contaminates database and phase discovery.
- Project overlays can shadow a global bundle, so registry-source proof is part
  of the experiment rather than an assumption.

### Integration Points

- Normal Phase 21 `plan:post` sync supplies the real proof task and Beads row.
- The public router, active capability registry, and live Beads database form
  the positive end-to-end path.
- `sync.py`, its tests, patch documentation, detector skills, and installed
  workflow files form the Patch 2 deletion set.
- Patch 1's `ship.md` marker/checker path is the independent preservation gate.

</code_context>

<specifics>

## Specific Ideas

- **Ponytail:** deletion at the existing seams is sufficient. No cutover
  framework, alias, cache, retry, dependency, or generalized install verifier.
  **Confidence: 98/100.**
- **Scientific argument:** native installed resolution can replace Patch 2 only
  if global selection, current bytes, the live database, and resolver output
  are each observed independently. **Evidence grade: Strong; accept with the
  D-01 through D-11 conditions; confidence 97/100.**
- **Primary confounds:** project-overlay shadowing, stale global bytes, wrong
  Beads discovery, Patch 2 silently satisfying the read path, and evidence
  accumulated at another SHA. Each has a direct control above. **Confidence:
  99/100.**
- **Alternative 1:** retain Patch 2 as fallback. Rejected because it masks
  native failure and makes CUT-01 unfalsifiable. **Confidence: 99/100.**
- **Alternative 2:** remove Patch 2 before installed proof. Rejected because a
  failed native path would leave pointer-only tasks unreadable. **Confidence:
  99/100.**
- **Alternative 3:** build a reusable cutover harness. Rejected because the
  existing public command, capability listing, directory comparison, and tests
  already expose every required seam. **Confidence: 96/100.**

</specifics>

<deferred>

## Deferred Ideas

None — discussion stayed within Phase 21 scope.

</deferred>

---

*Phase: 21-installed-cutover-and-patch-2-retirement*
*Context gathered: 2026-09-01*
