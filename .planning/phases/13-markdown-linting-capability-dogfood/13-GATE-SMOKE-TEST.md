# 13-GATE-SMOKE-TEST.md: Live proof of generic `ship:pre` gate dispatch (MDL-03)

**Recorded:** 2026-08-18
**Purpose:** the first live proof that a generic `ship:pre` gate fires for a `capId` other than
`security`/`broken-windows`, using the exact predicate shipped in
`.gsd/capabilities/markdown-linting/capability.json`'s single `gates[]` entry.

## Step 1 -- Confirm the ship.md patch marker is present

The installed `$HOME/.claude/gsd-core/workflows/ship.md` was directly read this session (this
task's own `<read_first>` requirement) and re-grepped after the read, since the patch is
machine-local and unmerged upstream (open-gsd/gsd-core#3559, filed by the `beads` capability):

```text
$ grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' "$HOME/.claude/gsd-core/workflows/ship.md"
2
```

(2 = the opening `<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->` marker at line 157 and
the closing `<!-- /gsd-beads-patch:ship-pre-generic-dispatch v1 -->` marker at line 242.) The
generic dispatch loop is confirmed present and live on this machine -- 13-RESEARCH.md's earlier
confirmation (same lines) is independently re-verified here, not just cited.

## Step 2 -- Two-case predicate smoke test

The predicate JSON used below was extracted directly from the shipped capability manifest, not
hand-typed:

```text
$ jq -c '.gates[0].check.predicate' .gsd/capabilities/markdown-linting/capability.json
{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}
```

This is byte-identical to the `check.predicate` object in
`.gsd/capabilities/markdown-linting/capability.json`'s `ship:pre` gate entry (same `artifact`,
`field`, `equals` values).

Both runs used a scratch phase directory (outside `.planning/`, under this session's temp
scratchpad, containing a synthetic `13-LINT-REPORT.md`) -- the real
`.planning/phases/13-markdown-linting-capability-dogfood/13-LINT-REPORT.md` produced by Task 2
was left unmodified (confirmed via `git status --short` before and after: no diff).

### Satisfied case (`violation_count: 0`)

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}' \
    --phase-dir <scratch-dir-with-13-LINT-REPORT.md-violation_count:0> \
    --phase-number 13 --raw
{
  "block": false,
  "message": "Frontmatter field \"violation_count\" matches expected value (0)",
  "details": {
    "kind": "artifact-frontmatter-equals",
    "match": true
  }
}
```

### Unsatisfied case (`violation_count: 7`)

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}' \
    --phase-dir <same scratch dir, violation_count now 7> \
    --phase-number 13 --raw
{
  "block": true,
  "message": "Frontmatter field \"violation_count\" in LINT-REPORT.md is 7, expected 0",
  "details": {
    "kind": "artifact-frontmatter-equals",
    "match": false,
    "actual": "7",
    "expected": 0
  }
}
```

## Result

Both outcomes match the roadmap's success criterion 3 and 13-RESEARCH.md's Code Examples section
exactly: `block: false`/`match: true` at `violation_count: 0`, `block: true`/`match: false` with
`actual: "7"` at `violation_count: 7`. The evaluator reports `actual` as the string `"7"` against
the integer `expected: 0` -- strict inequality is what makes a non-numeric sentinel safe for plan
02's tool-absent fail-open path (RESEARCH.md Pitfall 5).

This discharges the Phase 13 hard-prerequisite blocker recorded in `.planning/STATE.md`'s
Blockers/Concerns section (see that file's diff in this plan's commit history for the removed
bullet).
