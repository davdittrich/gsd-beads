# Domain Pitfalls

**Domain:** GSD Core native task-content resolution for the Beads capability
(milestone v1.4)
**Researched:** 2026-08-30
**Overall confidence:** MEDIUM — the native GSD contract was inspected in the installed
1.12 runtime and cross-checked against official GSD/Beads materials. Beads CLI payload
and migration behavior remain version-sensitive.

<!-- rumdl-disable MD013 -->

## Critical Pitfalls

### Pitfall 1: Passing Beads' JSON envelope through as the resolver result

**What goes wrong:** `bd show <id> --json` commonly exposes an issue inside an array, while GSD requires the resolver process to print exactly one JSON object. Returning the raw array, prose diagnostics on stdout, or a multi-object stream makes the native resolver reject the invocation as malformed.

**Why it happens:** The previous workflow patch consumed `bd show` directly and normalized the envelope in prompt logic. The native seam moves that boundary to `sync.py`; its output is now an API, not an incidental CLI transcript.

**Consequences:** GSD treats malformed output as a resolver defect and exits non-zero; task execution stops. Converting the error to `resolved: false` would violate the hard-halt contract and risks executing an inverted plan with no instructions.

**Warning signs:** A real `bd show` works, but `gsd_run task resolve-content ... --raw` reports malformed output; stdout has a leading log line; the adapter assumes an object while a real payload is `[issue]`.

**Prevention:** Make the adapter select and validate exactly one issue object, put diagnostics only on stderr, and emit a single JSON object with the GSD field names. Test array, object, empty array, malformed JSON, and non-zero `bd` output at the public `resolve-content` command.

**Detection:** Assert `exit 0`, `resolved: true`, and non-empty `content` for a live issue; assert non-zero for array/malformed-output fixtures. [95/100]

**Roadmap owner:** Phase 1 — native resolver adapter and manifest contract.

### Pitfall 2: Losing scalar criteria or creating the wrong shape during normalization

**What goes wrong:** Beads stores `acceptance_criteria` as issue prose, while GSD maps `acceptance_criteria` and `read_first` only from arrays of strings. A scalar passed through unchanged becomes `[]`; a split-on-newline implementation can invent or merge criteria.

**Why it happens:** GSD deliberately coerces resolver fields defensively instead of trusting third-party CLI output. This protects the host, but it makes a nominally successful adapter silently lose incorrectly shaped content.

**Consequences:** The executor can receive action text but no acceptance gate, producing a green-looking run without the task’s original verification contract.

**Warning signs:** Resolver returns `resolved: true`, but `content` lacks acceptance criteria; a single criterion with embedded newlines becomes multiple requirements; blank bullets survive as meaningful criteria.

**Prevention:** Define one documented, deterministic renderer/parser pair: Beads’ canonical acceptance text → trimmed non-empty string array, preserving ordering and multiline bullets. Cover empty, one, many, CRLF, and embedded Markdown examples; reject an unrecognized representation rather than guessing.

**Detection:** Round-trip fixture assertions compare the original criteria vector byte-for-byte after normalization, except for an explicitly specified line-ending normalization. [91/100]

**Roadmap owner:** Phase 1 — adapter contract tests.

### Pitfall 3: Parsing Markdown headings as unambiguous task structure

**What goes wrong:** The Phase 16 representation puts task fields into Beads description headings. Naïve regex extraction treats a heading in user-authored prose, a code fence, an escaped heading, or a repeated heading as a section boundary.

**Why it happens:** The old patch accepted the whole Beads description as task instructions. The native resolver must construct named fields; an informal Markdown parser turns content into control syntax.

**Consequences:** Actions, verification, or `read_first` may be truncated, moved to the wrong field, or silently erased. This is worse than a clean failure because the resolver still returns `resolved: true`.

**Warning signs:** A description contains `## Action` inside a fenced example; the same section label appears twice; headings are reordered; parser tests cover only the happy-path renderer.

**Prevention:** Parse only the exact canonical heading grammar produced by `sync.py`, once per allowed heading and outside fenced blocks; require every unconsumed/duplicate control heading to fail closed. Prefer storing a machine-readable task-content projection in issue metadata if Beads supports it later, rather than expanding a Markdown grammar.

**Detection:** Adversarial fixtures for duplicate labels, headings in code fences, heading-like prose, missing sections, and unknown headings must either reconstruct the original fields exactly or exit non-zero. [88/100]

**Roadmap owner:** Phase 1 — adapter parsing boundary; Phase 2 — adversarial compatibility suite.

### Pitfall 4: Backfilling `tracker-id` into the wrong plan tasks

**What goes wrong:** A broad text rewrite adds `tracker-id="beads:<id>"` to legacy headings, already-synced tasks, or `checkpoint:*` blocks. GSD’s parser treats checkpoint blocks as a different task kind and deliberately assigns them no tracker id; legacy `## Task N` headings likewise have no attribute carrier.

**Why it happens:** `<beads-id>` was the former identity anchor, whereas native resolution selects tasks by the opening `<task>` tag’s literal `tracker-id`. Migration needs both syntactic and semantic discrimination.

**Consequences:** A checkpoint can be sent to a non-interactive resolver, losing its decision/options/resume semantics. A rewritten legacy task can become unreachable or acquire a mismatched issue identity. Re-running sync may cause noisy diffs rather than idempotent convergence.

**Warning signs:** `tracker-id` appears on a `checkpoint:` task; historical plans with only `<beads-id>` stop executing; second sync changes bytes; a fixture uses only modern auto tasks.

**Prevention:** Restrict writes to parsed `<task type="auto|tracer">` blocks with exactly one valid `<beads-id>`, preserve `<beads-id>` during the migration window, and make a second run byte-identical. Explicitly test legacy heading plans and both checkpoint forms.

**Detection:** Parser-level before/after snapshots must show tracker ids only for eligible auto/tracer tasks and null tracker ids for every checkpoint/legacy-heading task. [96/100]

**Roadmap owner:** Phase 2 — legacy identity migration and checkpoint preservation.

### Pitfall 5: Softening a resolver failure into a PLAN.md fallback

**What goes wrong:** An unavailable `bd`, unknown issue, duplicate resolver prefix, timeout, malformed stdout, or missing executable is treated as empty content and execution falls back to stripped or stale PLAN.md text.

**Why it happens:** Earlier behavior allowed an explicit pre-migration fallback when a *successful* `bd show` had no description. That narrow compatibility case is easy to confuse with transport failure.

**Consequences:** The two stores again become competing sources of truth; an executor may act on stale directions precisely when the authoritative tracker cannot be read.

**Warning signs:** Tests expect `resolved: false` for a subprocess failure; error handling catches all exceptions; a missing `bd` prints a notice then continues; the migration test does not distinguish an empty description from a failed lookup.

**Prevention:** Preserve GSD’s error taxonomy: only not-applicable/no-resolver/empty are values; ambiguity, failed spawn/non-zero exit, timeout, and malformed output must produce non-zero termination. If legacy inline fallback is retained, permit it only after a successful, schema-valid response explicitly establishes an empty legacy description.

**Detection:** Public-command tests observe non-zero exits for every hard-failure class and separately show the intentional legacy-empty behavior, if it remains in scope. [97/100]

**Roadmap owner:** Phase 1 — hard-halt implementation; Phase 2 — migration boundary tests.

### Pitfall 6: Resolving against the wrong Beads database because runtime cwd/PATH differs

**What goes wrong:** The native resolver inherits the GSD process environment. It may run in an executor worktree, from an installed capability copy, or with a different `PATH`; `bd` then finds no database, a different database, or a binary incompatible with the project schema.

**Why it happens:** GSD invokes a bounded argv command but does not add a resolver-specific cwd. Beads’ database discovery and historical schema migrations are environment-dependent; project worktrees do not carry untracked `.beads/` state.

**Consequences:** False hard halts, or worse, a valid response for an issue in the wrong repository. A `bd` upgrade can also fail due to migration policy even though adapter code is correct.

**Warning signs:** `bd show` succeeds in an interactive shell but fails under `task resolve-content`; issue prefixes differ; `bd version` or `bd doctor` differs across hosts; a worktree resolver has no `.beads/` database.

**Prevention:** Resolve project root once, run the adapter with an explicit repository/database policy, and include non-secret diagnostics for resolved root, `bd version`, and failure class. Pin test invocations to the actual main repository when validating live state; use `bd`’s documented upgrade/bootstrap/migration procedure rather than storage edits.

**Detection:** Exercise resolver from the main checkout and an isolated worktree, with `bd` missing and with a controlled incompatible/migrating database; each must fail visibly and never query an unintended database. [93/100]

**Roadmap owner:** Phase 1 — invocation contract; Phase 3 — live installed-path validation.

### Pitfall 7: Retiring Patch 2 in source while it remains live—or retiring Patch 1 by collateral cleanup

**What goes wrong:** A repository edit deletes Patch 2 documentation/wiring but leaves the machine-local execute-plan marker or an installed capability copy unchanged. The inverse is also possible: the source patch is removed before native resolution works in the active runtime. A broad cleanup can remove the still-required Patch 1 ship-pre dispatcher.

**Why it happens:** Patch state spans source bundle, installed copies, machine-local GSD workflows, both runtime homes, and detector wiring. Source-tree tests cannot prove the bytes executed by a real session.

**Consequences:** Double resolution, obsolete hard-halt logic, future upgrade conflicts, or a silent loss of ship-pre behavior. The project’s former patch checker can falsely report health if it checks only one copy.

**Warning signs:** Zero source markers but a live `execute-plan.md` still contains the marker; source and installed `sync.py` hashes differ; Patch 1’s marker disappears; reapply verification is the sole proof despite known base-version noise.

**Prevention:** Treat retirement as a two-sided change: delete the Patch 2 marker, checker table entry, CLI route, and docs together only after the real native command succeeds and negative paths halt. Independently prove Patch 1’s marker/check still exists. Compare a manifest of tracked source files with every active installed/dogfood capability copy and inspect both GSD runtime homes.

**Detection:** Required gate: (1) repository-wide zero Patch 2 markers, (2) zero markers in active runtime workflows, (3) installed-byte manifest equality, (4) Patch 1 check passes, and (5) a real resolver proof from the installed copy. [96/100]

**Roadmap owner:** Phase 3 — patch retirement, install parity, release evidence.

## Moderate Pitfalls

### Pitfall 1: Capability validation is necessary but does not prove the active bundle

**What goes wrong:** `capability-validator` accepts the source manifest while GSD loads a stale installed capability or skips it due to version/consent/integrity drift.

**Warning signs:** Validation is clean but `resolve-content` says `no-resolver`; source and installed manifests carry different versions or hashes; the merged registry does not list the Beads resolver.

**Prevention:** Bump the capability version with any resolver behavior change, reinstall/re-consent as required, verify the merged installed registry contains one `beads` resolver, then run the real command. [94/100]

**Roadmap owner:** Phase 1 (manifest) and Phase 3 (installation gate).

### Pitfall 2: Resolver-prefix collision becomes an ambiguity halt at execution time

**What goes wrong:** Two installed capabilities claim `beads`; GSD refuses to choose one.

**Warning signs:** The source manifest validates alone, but the real command reports ambiguous resolution; a second capability appears in the installed registry after an update.

**Prevention:** Validate the merged registry—not merely the single source manifest—and add a collision fixture. This should remain a hard halt. [95/100]

**Roadmap owner:** Phase 1.

### Pitfall 3: Treating Beads internal storage as a stable integration API

**What goes wrong:** The adapter reads `.beads/issues.jsonl`, a database file, or raw schema tables to bypass a CLI shape change.

**Warning signs:** The implementation mentions internal Beads storage paths; an upgrade changes a database path or schema and resolver tests need storage-specific repair.

**Prevention:** Consume `bd show --json` only; normalize the documented CLI output at one adapter boundary and use the official export/upgrade/bootstrap path for recovery. [89/100]

**Roadmap owner:** Phase 1 and Phase 3 operational documentation.

## Minor Pitfalls

### Pitfall 1: Diagnostic text pollutes stdout

**What goes wrong:** A debug line makes otherwise valid JSON malformed.

**Warning signs:** The first stdout byte is not `{`; debug logging uses `print`/stdout; a human-readable success line is emitted before the JSON object.

**Prevention:** JSON only on stdout; concise diagnostics on stderr; test both streams. [96/100]

**Roadmap owner:** Phase 1.

### Pitfall 2: Treating a passing unit test as installed-runtime proof

**What goes wrong:** Pure parser tests pass while the launcher points to a stale copy or cannot find `bd`.

**Warning signs:** Unit tests pass but no test invokes `gsd_run task resolve-content` through the installed capability; source and installed byte manifests differ.

**Prevention:** Require the Ponytail ladder below before retirement. [94/100]

**Roadmap owner:** Phase 3.

## Ponytail Verification Ladder

| Level | Required evidence | Blocks | Owner |
|-------|-------------------|--------|-------|
| L0 — contract | Manifest validator plus pure adapter tests for object/array, criteria, headings, and tracker-id eligibility | schema/normalization defects | Phase 1 |
| L1 — adversarial | Negative public-boundary tests: malformed stdout, ambiguous resolver, missing binary, non-zero `bd`, timeout, and checkpoints | silent fallback and parser overreach | Phase 1 |
| L2 — compatibility | Real Beads fixture: legacy `<beads-id>` plans, heading fallback, auto/tracer idempotence, and checkpoint byte preservation | migration regressions | Phase 2 |
| L3 — installed reality | Actual installed bundle and both runtime homes: successful real resolution, hard-halt branches, Patch 2 absence, Patch 1 presence, byte manifest parity | stale install/patch and cwd failures | Phase 3 |

## Phase-Specific Warnings

| Phase topic | Likely pitfall | Mitigation |
|-------------|---------------|------------|
| Native adapter | JSON envelope, scalar/array coercion, Markdown headings | Single-object schema adapter with adversarial fixtures; stdout-only JSON |
| Legacy migration | Broad regex writes and checkpoint corruption | Parsed eligibility rule, dual identity during migration, second-run byte identity |
| Hard-failure contract | Empty result conflated with failure | Assert native non-zero exits for all resolver defects |
| Installed validation | cwd/PATH/database/schema drift | Main-checkout and worktree probes plus `bd version`/doctor diagnostics |
| Patch retirement | Source/runtime divergence or Patch 1 removal | Independent marker searches and installed-byte parity manifest |

## Sources

- Installed GSD Core 1.12 runtime, `bin/lib/task-content-resolution.cjs`, `task-command-router.cjs`, `plan-document.cjs`, and `capability-validator.cjs` (directly inspected 2026-08-30; primary implementation evidence).
- [GSD Core capability manifest reference](https://github.com/open-gsd/gsd-core/blob/next/docs/reference/capability-manifest.md) (official; current crawl 2026-08).
- [GSD Core capability-system ADR](https://github.com/open-gsd/gsd-core/blob/next/docs/adr/857-capability-system.md) (official; current crawl 2026-08).
- [Beads releases and upgrade guidance](https://github.com/gastownhall/beads/releases) (official; current crawl 2026-08).
- [Beads agent instructions](https://github.com/gastownhall/beads/blob/main/AGENT_INSTRUCTIONS.md) (official; current crawl 2026-08).

**Source confidence:** Installed first-party runtime evidence is HIGH; official web corroboration is MEDIUM (provider confidence after verification). Community issue/discussion reports were used only to identify tests, not as authoritative contract claims.
