# 14-GATE-SMOKE-TEST.md: Live proof of `pr-workflow`'s `ship:pre` gate firing tri-state (PRW-02)

**Recorded:** 2026-08-18
**Purpose:** live proof that `pr-workflow`'s `ship:pre` gate evaluates `pr_gate_ok`
tri-state-correctly across all four `pr_status` states, using the exact predicate shipped in
`.gsd/capabilities/pr-workflow/capability.json`'s single `gates[]` entry -- the second capability
(after Phase 13's `markdown-linting`) to exercise the generic `ship:pre` dispatch loop.

## Step 1 -- Confirm the ship.md patch marker is present

The installed `$HOME/.claude/gsd-core/workflows/ship.md` was directly read this session (this
task's own `<read_first>` requirement) and re-grepped after the read, since the patch is
machine-local and unmerged upstream (open-gsd/gsd-core#3559, filed by the `beads` capability).
Phase 13's earlier confirmation (`13-GATE-SMOKE-TEST.md` Step 1) is independently re-verified
here again, per the v1.2 cross-cutting constraint:

```text
$ grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' "$HOME/.claude/gsd-core/workflows/ship.md"
2
```

(2 = the opening `<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->` marker at line 157 and
the closing `<!-- /gsd-beads-patch:ship-pre-generic-dispatch v1 -->` marker at line 242 -- the
same line numbers Phase 13 recorded, confirming the installed file has not drifted between
Phase 13 and Phase 14's execution.) The generic dispatch loop is confirmed present and live on
this machine.

## Step 2 -- Four-case predicate smoke test

The predicate JSON used below was extracted directly from the shipped capability manifest, not
hand-typed:

```text
$ jq -c '.gates[0].check.predicate' .gsd/capabilities/pr-workflow/capability.json
{"kind":"artifact-frontmatter-equals","artifact":"PR.md","field":"pr_gate_ok","equals":true}
```

This is byte-identical to the `check.predicate` object in
`.gsd/capabilities/pr-workflow/capability.json`'s `ship:pre` gate entry.

All four runs used a scratch phase directory (outside `.planning/`, under this session's temp
scratchpad), each containing a synthetic `14-PR.md` with one of the four `pr_status`/`pr_gate_ok`
pairs. The real `.planning/phases/14-pr-workflow-capability-dogfood/14-PR.md` produced by Task 1
was left unmodified throughout (confirmed via `git status --short` before and after all four
runs: no diff, output empty both times).

### `pr_status: none` / `pr_gate_ok: true` (satisfied)

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"PR.md","field":"pr_gate_ok","equals":true}' \
    --phase-dir <scratch-dir-with-14-PR.md-pr_status:none-pr_gate_ok:true> \
    --phase-number 14 --raw
{
  "block": false,
  "message": "Frontmatter field \"pr_gate_ok\" matches expected value (true)",
  "details": {
    "kind": "artifact-frontmatter-equals",
    "match": true
  }
}
```

### `pr_status: passing` / `pr_gate_ok: true` (satisfied)

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"PR.md","field":"pr_gate_ok","equals":true}' \
    --phase-dir <scratch-dir-with-14-PR.md-pr_status:passing-pr_gate_ok:true> \
    --phase-number 14 --raw
{
  "block": false,
  "message": "Frontmatter field \"pr_gate_ok\" matches expected value (true)",
  "details": {
    "kind": "artifact-frontmatter-equals",
    "match": true
  }
}
```

### `pr_status: pending` / `pr_gate_ok: false` (unsatisfied)

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"PR.md","field":"pr_gate_ok","equals":true}' \
    --phase-dir <scratch-dir-with-14-PR.md-pr_status:pending-pr_gate_ok:false> \
    --phase-number 14 --raw
{
  "block": true,
  "message": "Frontmatter field \"pr_gate_ok\" in PR.md is false, expected true",
  "details": {
    "kind": "artifact-frontmatter-equals",
    "match": false,
    "actual": "false",
    "expected": true
  }
}
```

### `pr_status: failing` / `pr_gate_ok: false` (unsatisfied)

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"PR.md","field":"pr_gate_ok","equals":true}' \
    --phase-dir <scratch-dir-with-14-PR.md-pr_status:failing-pr_gate_ok:false> \
    --phase-number 14 --raw
{
  "block": true,
  "message": "Frontmatter field \"pr_gate_ok\" in PR.md is false, expected true",
  "details": {
    "kind": "artifact-frontmatter-equals",
    "match": false,
    "actual": "false",
    "expected": true
  }
}
```

## Step 3 -- Result

ROADMAP Success Criterion 2 is satisfied by observed predicate output, not by manifest
inspection: `block: false`/`match: true` for both `none` and `passing`, `block:
true`/`match: false` (`actual: "false"`) for both `pending` and `failing` -- the exact tri-state
split PRW-02 requires.

The two satisfied cases (`none`, `passing`) are the direct proof that RESEARCH Pitfall 1 was
avoided in this capability's shipped manifest. Pitfall 1's failure mode is a gate that targets
the raw four-state `pr_status` field directly with `equals: "passing"` -- such a predicate would
report the `none` case (`pr_status: none`, no open PR at all) as `block: true`, incorrectly
flagging "no PR yet" as a failing check-status. Because the shipped gate instead targets the
pre-reduced `pr_gate_ok` boolean (`pr_gate_ok: true` for both `none` and `passing`, computed by
`derive_gate_ok()` as `pr_status in {"none", "passing"}`), the `none` case above returns
`block: false` exactly like `passing` does -- the single-scalar `equals` predicate never had to
express an OR condition, because the OR was already collapsed into the artifact's own frontmatter
before the gate ever ran.

`pr-workflow`'s shipped gate is `"blocking": false` (advisory-only, PRW-02/PRW-05), so per
`ship.md`'s patched dispatch loop (verified present in Step 1), a `block: true` result here would
surface as an advisory line and never halt a ship -- the same `blocking: false` behavior
`13-GATE-SMOKE-TEST.md` Step 3 already demonstrated live for `markdown-linting`'s gate.
