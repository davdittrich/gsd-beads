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

## Live Cycle Evidence

**Recorded:** 2026-08-18 (plan 14-03, Task 1). Converts plans 14-01/14-02's unit-level PRW-03/
PRW-04 guarantees into live, recorded evidence: an actual degrade cycle with `gh` removed, an
actual degrade cycle with `gh` unauthenticated, and an actual no-open-PR ship, all run against
this repo's real `main` branch.

### Step 0 -- Re-establish capability consent

The `pr-workflow` bundle directory was edited by plans 14-01 and 14-02 (`pr_status.py`,
`capability.json`, `SKILL.md`, `test_pr_status.py` all changed after the project-scope consent
recorded when the capability was first installed). Per the v1.2 cross-cutting constraint
("Re-consent after every bundle edit"), the project-scope install was re-run before trusting any
live dispatch below:

```text
$ node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability install ./.gsd/capabilities/pr-workflow --scope project --yes --raw
{
  "status": "installed",
  "id": "pr-workflow",
  "version": "0.1.0",
  "scope": "project",
  "disclosure": [
    "This capability ships no executable surfaces (declarative only)."
  ]
}
```

`"status": "installed"` confirms the content hash recorded against this session's bundle state
matches what is now on disk -- the capability is active for the runs below, not silently
deactivated by 14-01/14-02's edits.

### Run (a) -- Baseline: `verify-post` with `gh` present and authenticated

```text
$ git branch --show-current
main
$ gh pr list --head main --state open --json number
[]
$ python3 .gsd/capabilities/pr-workflow/scripts/pr_status.py verify-post .planning/phases/14-pr-workflow-capability-dogfood
PR.md regenerated: no open PR (pr_status=none)
$ echo $?
0
```

Resulting `14-PR.md`:

```text
phase: 14-pr-workflow-capability-dogfood
pr_status: none
pr_gate_ok: true
pr_number: null
open_pr_count: 0
generated_from: "gh pr list --head main --state open --json number,url"
generated_at: 2026-08-18T16:58:27Z
```

This repo's `main` branch has no open PR, so `pr_status: none` / `pr_gate_ok: true` is the correct
live result. **This run's output (re-run a second time below, after runs (b)/(c), to restore the
baseline) is the `14-PR.md` committed for this phase.**

### Run (b) -- `gh` absent: `verify-post` with `PATH` overridden to a scratch directory

Matching `13-GATE-SMOKE-TEST.md` Step 4's technique: neither `gh` nor `python3` was uninstalled;
a scratch directory was populated with a symlink to the real `python3` binary only (so the
interpreter itself keeps running), and `PATH` was overridden to that scratch directory for this
one invocation:

```text
$ SCRATCH=<scratch-dir>
$ mkdir -p "$SCRATCH" && ln -sf "$(command -v python3)" "$SCRATCH/python3"
$ env PATH="$SCRATCH" "$SCRATCH/python3" .gsd/capabilities/pr-workflow/scripts/pr_status.py verify-post .planning/phases/14-pr-workflow-capability-dogfood
gh not found on PATH -- install: https://cli.github.com
$ echo $?
0
```

The install-focused notice (`NOTICE_GH_ABSENT`) appears exactly once in the captured stdout above
(one line, no repetition), and the process exited `0` promptly -- no hang. Resulting `14-PR.md`:

```text
phase: 14-pr-workflow-capability-dogfood
pr_status: unavailable
pr_gate_ok: false
pr_number: null
open_pr_count: 0
unavailable_reason: gh not found on PATH -- install: https://cli.github.com
generated_from: "none (gh not found on PATH -- install: https://cli.github.com)"
generated_at: 2026-08-18T16:58:53Z
```

`pr_status: unavailable` / `pr_gate_ok: false` as PRW-04 requires -- a fail-open write, not a
stale carry-forward of run (a)'s `none`/`true`. The baseline artifact was restored immediately
afterward by re-running (a):

```text
$ python3 .gsd/capabilities/pr-workflow/scripts/pr_status.py verify-post .planning/phases/14-pr-workflow-capability-dogfood
PR.md regenerated: no open PR (pr_status=none)
$ echo $?
0
```
(`14-PR.md` back to `pr_status: none` / `pr_gate_ok: true`, `generated_at: 2026-08-18T16:59:01Z`.)

### Run (c) -- `gh` unauthenticated: `verify-post` with `GH_CONFIG_DIR` pointed at an empty scratch directory

Per `14-RESEARCH.md` Pitfall 5, the plain (non-`--json`) `gh auth status` invocation is what
detects this state; `GH_CONFIG_DIR` was pointed at an empty scratch directory for this one
invocation, leaving the real `gh` credential store at its normal location untouched:

```text
$ GH_SCRATCH=<empty-scratch-dir>
$ mkdir -p "$GH_SCRATCH"
$ env GH_CONFIG_DIR="$GH_SCRATCH" python3 .gsd/capabilities/pr-workflow/scripts/pr_status.py verify-post .planning/phases/14-pr-workflow-capability-dogfood
gh not authenticated -- run: gh auth login
$ echo $?
0
```

The login-focused notice (`NOTICE_GH_UNAUTH`) appears exactly once in the captured stdout above,
and it is **not** the same string as run (b)'s notice (`gh not found on PATH -- install:
https://cli.github.com` vs `gh not authenticated -- run: gh auth login` -- distinct wording,
neither a substring of the other, matching D-04). Resulting `14-PR.md`:

```text
phase: 14-pr-workflow-capability-dogfood
pr_status: unavailable
pr_gate_ok: false
pr_number: null
open_pr_count: 0
unavailable_reason: gh not authenticated -- run: gh auth login
generated_from: "none (gh not authenticated -- run: gh auth login)"
generated_at: 2026-08-18T16:59:12Z
```

Again `pr_status: unavailable` / `pr_gate_ok: false`. The baseline artifact was restored
immediately afterward by re-running (a):

```text
$ python3 .gsd/capabilities/pr-workflow/scripts/pr_status.py verify-post .planning/phases/14-pr-workflow-capability-dogfood
PR.md regenerated: no open PR (pr_status=none)
$ echo $?
0
```
(`14-PR.md` back to `pr_status: none` / `pr_gate_ok: true`, `generated_at: 2026-08-18T16:59:16Z`
-- restored immediately after run (c). This task's own `<verify>` command re-runs `verify-post`
once more as its final automated check, which regenerates `14-PR.md` a final time with the same
`pr_status: none` / `pr_gate_ok: true` result and `generated_at: 2026-08-18T17:00:35Z` -- **this
is the exact content committed for this phase**, still falling within this task's own execution
window alongside runs (a)-(d) above.)

### Run (d) -- No open PR: `ship-post-notice` with a `gh pr list` capture bracketing it

```text
$ gh pr list --head main --state open --json number
[]
$ python3 .gsd/capabilities/pr-workflow/scripts/pr_status.py ship-post-notice .planning/phases/14-pr-workflow-capability-dogfood
no open PR exists for this branch -- ship proceeding, nothing created (branch: main)
$ echo $?
0
$ gh pr list --head main --state open --json number
[]
```

The two `gh pr list` captures bracketing the `ship-post-notice` call are byte-identical (`[]` both
times), and exactly one notice line (`NOTICE_NO_OPEN_PR`, naming the branch) was printed between
them -- direct evidence that `ship_post_notice()` created nothing: no PR was opened, drafted, or
mutated by this run. `git status --short .planning/phases/14-pr-workflow-capability-dogfood/14-PR.md`
showed only the `generated_at` timestamp differing from the last-committed value afterward (this
run reads `gh pr list`/`gh auth status` only -- it never touches `PR.md` at all, per
`ship_post_notice()`'s own docstring; the `14-PR.md` diff observed is entirely attributable to
runs (a)/(b)/(c) above, not to this run).

### Result (Live Cycle Evidence)

ROADMAP Success Criteria 4 and 5 are satisfied by recorded live transcripts, not by unit
assertions alone:

- **SC5 (PRW-04):** runs (b) and (c) each print exactly one notice, the two notices are distinct
  and neither is a substring of the other, both processes exit `0` promptly (no hang), and both
  write `pr_status: unavailable` / `pr_gate_ok: false` -- never a stale `none`/`passing` carried
  forward from the baseline.
- **SC4 (PRW-03):** run (d)'s two `gh pr list` captures are byte-identical (`[]`/`[]`) and exactly
  one warn-only notice was printed between them -- nothing was created, and the capability's own
  read-only discipline (`gh_available()`'s `auth status`, `find_open_pr()`'s `pr list`, never a
  `gh pr create`) holds live, not just in the mocked unit suite.
- The committed `14-PR.md` is run (a)'s output (re-run identically to restore the baseline after
  (b)/(c), then once more by this task's own `<verify>` command), with
  `generated_at: 2026-08-18T17:00:35Z` falling inside this task's own execution window.
