# Phase 19: Native Resolver Contract and Failure Boundary - Context

**Gathered:** 2026-08-30
**Status:** Ready for planning

<domain>

## Phase Boundary

Declare one native `beads` task-content resolver and add one existing-adapter
verb that translates a live Beads issue into gsd-core's five consumed content
fields. This phase establishes the resolver contract and its fail-closed
boundary. Task identity migration belongs to Phase 20; installed cutover and
Patch 2 retirement belong to Phase 21.

</domain>

<decisions>

## Implementation Decisions

### Description Boundary

- **D-01:** Return non-duplicated authored execution prose in `description`.
  Extracted `Read First`, `Verify`, and `Done` content appears only in its
  dedicated resolver field.
- **D-02:** Preserve retained section headings, bodies, relative order, and
  leading prose. Retain `Precondition`, `Behavior`, `Action`, `Files`, and
  unknown sections rather than flattening or reinterpreting them.
- **D-03:** Do not synthesize Beads title, id, status, priority, or other
  metadata into `description`; the plan already carries task identity and
  name.
- **D-04:** A source description and its retained post-partition description
  must both be nonblank. A task containing only extracted sections is unusable
  and halts rather than returning gsd-core's non-throwing empty outcome.

### Heading Grammar

- **D-05:** Implement the smallest correct inverse of `_task_description`, not
  a general Markdown parser. Recognize the exact, case-sensitive, column-zero
  `## Read First`, `## Verify`, and `## Done` headings outside fenced code.
- **D-06:** Treat canonical column-zero H2 headings as section delimiters so
  unknown sections remain intact in `description`. Near-match headings remain
  authored content; no case, indentation, or closing-hash tolerance is added.
- **D-07:** Recognized sections may occur in any order, but a duplicate
  recognized heading is ambiguous and halts. Backtick and tilde fences protect
  heading-like content; an unclosed fence consumes the remainder literally.
- **D-08:** `acceptance_criteria` remains Beads' separate structured field. An
  authored `## Acceptance Criteria` description section is retained as prose;
  it is never silently merged with or substituted for the structured field.

### List Normalization

- **D-09:** Parse `Read First` only as the writer's canonical zero-indent
  dash-space (`-`) list. Strip the marker and surrounding item whitespace;
  preserve item order and duplicates. Mixed or malformed nonblank lines halt.
- **D-10:** Normalize scalar Beads `acceptance_criteria` with gsd-core's own
  `splitCriteria` semantics: split CRLF/LF lines, trim, discard blanks, strip
  one optional `-` or `*` marker, and preserve order and duplicates.
- **D-11:** Missing or null acceptance criteria becomes `[]`; a string is
  normalized; every other type halts. Missing `Read First`, `Verify`, or
  `Done` remains valid because those native fields are optional.
- **D-12:** Preserve internal newlines in scalar `Verify` and `Done` bodies
  while trimming only their surrounding separator whitespace.

### Failure Boundary and Wire Contract

- **D-13:** Reuse the existing safe Beads-id grammar and fixed typed argv:
  `bd show <id> --json`. Require the returned row id to equal the requested id.
- **D-14:** Accept both documented Beads shapes: the current raw array and the
  versioned object whose `data` is that array. Require exactly one plain-object
  row; reject zero, multiple, malformed, error, or id-mismatched results.
- **D-15:** Missing scripts, invalid ids, unavailable or non-zero `bd`, outer
  resolver timeout, invalid JSON/UTF-8, invalid envelopes, wrong field types,
  ambiguous Markdown, and unusable descriptions all exit nonzero. Errors write
  one bounded diagnostic to stderr and nothing to stdout.
- **D-16:** On success, stdout contains exactly one JSON object with only
  `description`, `read_first`, `verify`, `acceptance_criteria`, and `done`.
  Ignore unrelated Beads fields. Do not cache, retry, add telemetry, or expose
  another interface.
- **D-17:** Keep the approved manifest invocation: `python3 -c`, resolve the
  installed script through `GSD_HOME` or `Path.home()`, replace the bootstrap
  with `os.execv`, pass the id as a separate argv element, and use a 10,000 ms
  gsd-core timeout.

### Verification Discipline

- **D-18:** The primary oracle is a producer-to-adapter round trip using
  `_task_description`; tests also spy the exact `bd` argv and assert JSON-only
  stdout.
- **D-19:** Negative fixtures isolate one variable per arm: envelope shape,
  row count/type/id, source-field type, heading duplication, fence handling,
  list grammar, subprocess exit, and timeout. A green result from a confounded
  multi-fault fixture is not evidence for any individual failure contract.

### the agent's Discretion

The user selected D-01 through D-03 directly, then delegated all remaining
questions to Ponytail, scientific-critical-thinking, Beads, and
codebase-design. The planner may choose private helper names and exact
diagnostic wording, but not broaden the supported grammar or weaken the
failure classes above.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Intent

- `.planning/PROJECT.md` — v1.4 scope, fixed bootstrap, and patch boundaries.
- `.planning/REQUIREMENTS.md` — RES-01 through RES-03 and exclusions.
- `.planning/ROADMAP.md` — Phase 19 goal and observable success criteria.
- `.planning/research/SUMMARY.md` — validated mechanism, alternatives, risks,
  and installed-runtime evidence.
- `https://github.com/davdittrich/gsd-beads/issues/6` — full originating issue
  and comments; scope evidence, not runtime proof.

### Existing Beads Module

- `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` — feature
  manifest and resolver declaration seam.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` — existing
  adapter, `_task_description`, `run_bd`, and safe id grammar.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` — current
  writer, strip, subprocess, and failure-test patterns.

### External Contracts

- `/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs` — installed
  resolver invocation, coercion, timeout, and hard-failure behavior.
- `/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs` — installed
  `splitCriteria` behavior to match exactly.
- `https://github.com/open-gsd/gsd-core/blob/next/docs/how-to/develop-a-task-content-resolver-capability.md`
  — official resolver capability guide.
- `https://github.com/gastownhall/beads/blob/main/docs/reference/json-schema.md`
  — current array contract and versioned-envelope migration.
- `https://spec.commonmark.org/0.31.2/` — fenced-code and ATX-heading semantics
  used only to avoid false section boundaries.

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets

- `_task_description(task)`: canonical producer grammar and round-trip oracle.
- `run_bd(argv, timeout=BD_TIMEOUT)`: fixed-argv subprocess seam.
- `SAFE_BD_ID_RE`: existing input validation for Beads identifiers.
- `TestStripTaskBodies` and create-issue tests: established fixtures for every
  task shape, byte preservation, idempotence, and subprocess spies.

### Established Patterns

- `sync.py` centralizes all Beads CLI invocation and uses typed argv without a
  shell.
- Task descriptions use ordered H2 sections; acceptance criteria travels in
  Beads' separate scalar field.
- Capability manifests are feature-role JSON, validated by installed gsd-core,
  with no runtime dependency beyond Python 3 and `bd`.

### Integration Points

- Add the sole `taskContentResolver` declaration to the Beads capability
  manifest.
- Add one `resolve-task-content` dispatch verb to the existing `sync.py`
  command interface.
- Add focused adapter and manifest tests beside the existing sync tests.

</code_context>

<specifics>

## Specific Ideas

Scientific appraisal:

- Central claim: a canonical writer inverse is the minimum scope-complete
  adapter. Direct source, live CLI, installed runtime, and official contract
  evidence support it. **Confidence: 96/100 (Strong).**
- Alternative explanation 1: arbitrary hand-authored Markdown needs a broad
  parser. Rejected because no evidence establishes that input contract, and a
  parser cannot infer duplicate reserved-heading intent. **Confidence:
  94/100.**
- Alternative explanation 2: gsd-core should coerce raw Beads output. Rejected
  because tracker-specific translation belongs behind this adapter seam and
  core changes are out of scope. **Confidence: 99/100.**
- Residual uncertainty: an unfenced top-level reserved heading authored inside
  prose can be indistinguishable from protocol structure. The canonical
  grammar and duplicate rejection constrain but cannot eliminate that semantic
  ambiguity. **Confidence in heading policy: 90/100.**

</specifics>

<deferred>

## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

Phase: 19-native-resolver-contract-and-failure-boundary
Context gathered: 2026-08-30
