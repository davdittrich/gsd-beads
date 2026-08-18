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

## Step 3 -- Live advisory-gate run against the real report (MDL-03 success criterion 4, plan 03 Task 3)

Unlike Step 2's scratch-directory two-case test, this run injects a nonzero `violation_count`
into the **real** `.planning/phases/13-markdown-linting-capability-dogfood/13-LINT-REPORT.md`
(backed up first) and evaluates the shipped gate against it, to observe the live advisory
behavior `ship.md`'s generic dispatch loop actually produces for a `blocking: false` gate.

Real report's `violation_count` temporarily set to `12` (was `0`):

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}' \
    --phase-dir .planning/phases/13-markdown-linting-capability-dogfood --phase-number 13 --raw
{
  "block": true,
  "message": "Frontmatter field \"violation_count\" in LINT-REPORT.md is 12, expected 0",
  "details": {
    "kind": "artifact-frontmatter-equals",
    "match": false,
    "actual": "12",
    "expected": 0
  }
}
```

`markdown-linting`'s shipped gate is `"blocking": false`. Per `ship.md`'s patched step 8(c),
Step 2 ("block evaluation"): `hook.blocking == false` never halts; if `GATE_RESULT.block` is
`true` the dispatch prints an advisory line and continues. Applying that literal template
(`⚠ {hook.capId} advisory: {GATE_RESULT.message}`) to this run's own `GATE_RESULT.message`
produces the exact transcript line a live `/gsd-ship` run would print:

```text
⚠ markdown-linting advisory: Frontmatter field "violation_count" in LINT-REPORT.md is 12, expected 0
```

**Result:** the ship proceeds — `blocking: false` means step 8(c) never sets the halt condition
regardless of `GATE_RESULT.block`, so this advisory is printed and the preflight sequence
continues to the next hook / to `push_branch`, exactly as MDL-03 success criterion 4 requires.

The real report was restored immediately after this test via `lint.py verify-post` (a fresh live
`rumdl` run), so the committed `13-LINT-REPORT.md` never carries the injected `12` value.

## Step 4 -- rumdl-absent cycle (MDL-04 success criterion 5, plan 03 Task 3)

Neither `rumdl` nor `uvx` was uninstalled. Absence was simulated for one process invocation only,
by resolving both binaries' real location (`/usr/bin`, both) and constructing a scratch `PATH`
containing a symlink to `python3` only — `python3` itself lives in the same directory as both
tools, so the whole directory could not simply be dropped from `PATH` without also breaking the
Python interpreter `lint.py` needs to run.

```text
$ PATH=<scratch-dir-containing-only-a-python3-symlink> python3 \
    .gsd/capabilities/markdown-linting/scripts/lint.py verify-post \
    .planning/phases/13-markdown-linting-capability-dogfood
rumdl unavailable (checked PATH and uvx) -- lint skipped, LINT-REPORT.md marked unavailable
$ echo $?
0
```

The notice (`lint.py`'s module-level `NOTICE` constant) appeared exactly once in the captured
stdout, the process exited `0`, and nothing hung. The resulting `13-LINT-REPORT.md` carried:

```text
violation_count: unavailable
unavailable_reason: rumdl and uvx both absent from PATH
generated_from: "none (rumdl and uvx both absent from PATH)"
```

Evaluating the shipped predicate against that sentinel confirms the gate reads it as
unsatisfied, not as a clean pass:

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}' \
    --phase-dir .planning/phases/13-markdown-linting-capability-dogfood --phase-number 13 --raw
{
  "block": true,
  "message": "Frontmatter field \"violation_count\" in LINT-REPORT.md is unavailable, expected 0",
  "details": {
    "kind": "artifact-frontmatter-equals",
    "match": false,
    "actual": "unavailable",
    "expected": 0
  }
}
```

`block: true` with `actual: "unavailable"` — because `markdown-linting`'s gate is `blocking:
false`, `ship.md`'s dispatch would print this as an advisory ("could not verify") rather than a
hard halt, exactly like Step 3's nonzero-count case, never as a false-clean pass. The real
`13-LINT-REPORT.md` was regenerated immediately afterward with `rumdl` back on the normal `PATH`,
ending this test at a real `violation_count: 0`.
