# 15-GATE-REPROOF.md: Live re-proof of both `ship:pre` gates from the marketplace-installed copies

**Recorded:** 2026-08-18
**Purpose:** re-prove, from the marketplace-installed copies of `markdown-linting` and `pr-workflow`
rather than from this repo's working tree, that ROADMAP success criterion 3 still holds after
extraction: each capability's `ship:pre` gate still evaluates exactly as `13-GATE-SMOKE-TEST.md`
and `14-GATE-SMOKE-TEST.md` proved it, with every predicate read from the installed plugin cache
and every synthetic artifact placed outside `.planning/`.

**No predicate below was read from this repository's working tree.** Every `--predicate` value
passed to `gsd_run check predicate` was extracted with `jq` from the plugin cache path quoted in
each capability's own section, not from `.gsd/capabilities/<id>/capability.json` in this repo.

## Step 0 -- Marketplace install and three-stage consent cycle (Task 1)

Both plugins were installed from the real, pushed `davdittrich/gsd-beads` marketplace:

```text
$ claude plugin marketplace update gsd-beads
✔ Successfully updated marketplace: gsd-beads

$ claude plugin install markdown-linting@gsd-beads -y
✔ Successfully installed plugin: markdown-linting@gsd-beads (scope: user)

$ claude plugin install pr-workflow@gsd-beads -y
✔ Successfully installed plugin: pr-workflow@gsd-beads (scope: user)

$ claude plugin list | grep -E 'markdown-linting|pr-workflow'
❯ markdown-linting@gsd-beads
❯ pr-workflow@gsd-beads
```

Both installed copies were resolved by search inside the local plugin cache, not by assuming the
version segment:

```text
$ find "$HOME/.claude/plugins/cache/gsd-beads/markdown-linting" -name plugin.json -path '*/.claude-plugin/*'
/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0/.claude-plugin/plugin.json

$ find "$HOME/.claude/plugins/cache/gsd-beads/pr-workflow" -name plugin.json -path '*/.claude-plugin/*'
/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0/.claude-plugin/plugin.json
```

Resolved plugin roots (both contain `.claude-plugin/plugin.json`, `hooks/session-start.sh`, and
`.gsd/capabilities/<id>/capability.json`):

- `markdown-linting`: `/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0`
- `pr-workflow`: `/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0`

Before the first hook run, neither consent sidecar existed:

```text
$ test -f "$HOME/.gsd/capability-auto-install-markdown-linting.hash" || echo ABSENT
ABSENT
$ test -f "$HOME/.gsd/capability-auto-install-pr-workflow.hash" || echo ABSENT
ABSENT
```

### markdown-linting: grant / no-op / re-grant

Each installed copy's own `hooks/session-start.sh` was invoked directly with `CLAUDE_PLUGIN_ROOT`
set to its resolved cache root -- the exact invocation `hooks/hooks.json` registers for
`SessionStart`.

```text
$ CLAUDE_PLUGIN_ROOT="/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0" \
    bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh"
Auto-installed capability: markdown-linting (user scope)
$ echo $?
0
$ cat "$HOME/.gsd/capability-auto-install-markdown-linting.hash"
79d2785e32f2ab75f2bb6f7d94e1d7cd1913c5196e2bf2cdb923362d7dd3fb87
```

Grant confirmed: sidecar created, auto-install line printed naming the capability and user scope.

```text
$ CLAUDE_PLUGIN_ROOT="/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0" \
    bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh"
$ echo $?
0
```

No auto-install line on the second run (fast path); the sidecar content was verified
byte-identical to its post-first-run value via `diff` (exit 0, no output) before and after this
run.

```text
$ rm "$HOME/.gsd/capability-auto-install-markdown-linting.hash"
$ CLAUDE_PLUGIN_ROOT="/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0" \
    bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh"
Auto-installed capability: markdown-linting (user scope)
$ cat "$HOME/.gsd/capability-auto-install-markdown-linting.hash"
79d2785e32f2ab75f2bb6f7d94e1d7cd1913c5196e2bf2cdb923362d7dd3fb87
```

Re-consent path: after deleting the sidecar, the third run re-created it with the identical hash
value (`79d2785e...`, unchanged from the first run) and re-emitted the auto-install line.

### pr-workflow: grant / no-op / re-grant

Same three-stage sequence, driven from the `pr-workflow` cache root:

```text
$ CLAUDE_PLUGIN_ROOT="/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0" \
    bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh"
Auto-installed capability: pr-workflow (user scope)
$ cat "$HOME/.gsd/capability-auto-install-pr-workflow.hash"
380ab6b54589bc927fc01bedc028e90d8fce23f4d5991d4a40cbd0af7c2a20d9

$ CLAUDE_PLUGIN_ROOT="/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0" \
    bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh"
$ echo $?
0
```

No auto-install line on the second run; sidecar byte-identical (`diff`, exit 0, no output).

```text
$ rm "$HOME/.gsd/capability-auto-install-pr-workflow.hash"
$ CLAUDE_PLUGIN_ROOT="/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0" \
    bash "$CLAUDE_PLUGIN_ROOT/hooks/session-start.sh"
Auto-installed capability: pr-workflow (user scope)
$ cat "$HOME/.gsd/capability-auto-install-pr-workflow.hash"
380ab6b54589bc927fc01bedc028e90d8fce23f4d5991d4a40cbd0af7c2a20d9
```

Re-consent path: identical hash value re-created (`380ab6b5...`), auto-install line re-emitted.

### Cross-checks

```text
$ node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability list --raw | grep -c '"id": "markdown-linting"'
1
$ node "$HOME/.claude/gsd-core/bin/gsd-tools.cjs" capability list --raw | grep -c '"id": "pr-workflow"'
2
```

`markdown-linting` appears once, at `scope: "global"`, `source` pointing at the installed cache
bundle. `pr-workflow` appears **twice**: once at `scope: "global"` (this task's grant, `source`
pointing at the installed cache bundle) and once at `scope: "project"` (this repository's
pre-existing `.gsd-capabilities.json` entry, `source: "./.gsd/capabilities/pr-workflow"`, granted
by Phase 14 before this plan ran). Both entries report `"status": "active"` independently -- the
user-scope grant this task performed did not overwrite, conflict with, or get shadowed by the
pre-existing project-scope entry, and vice versa. This is the observed interaction Task 1's
`<action>` asked to be recorded verbatim: **the two scopes coexist as independent ledger entries
for the same capability id, with no observed collision** -- direct input to Plan 05's decision
about whether the repo-root bundle can safely be removed once the marketplace-installed copy is
the primary distribution channel.

```text
$ diff "/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0/.gsd/capabilities/markdown-linting/capability.json" \
       "$HOME/.gsd/capabilities/markdown-linting/capability.json"
(no output)
$ diff "/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0/.gsd/capabilities/pr-workflow/capability.json" \
       "$HOME/.gsd/capabilities/pr-workflow/capability.json"
(no output)
```

Both user-scope grant destinations are byte-identical to the installed cache bundle -- the grant
came from the installed copy, not from anything in this repository.

**Note on the primary checkout's own working tree:** `git -C /home/dd/projects/gsd-beads status
--porcelain -- .gsd .gsd-capabilities.json` reports one line, `M .gsd-capabilities.json`. This
predates this plan entirely: the file's on-disk mtime is `2026-08-18 19:57:47 +0200`, over three
hours before this task's first command ran, and the diff is a single `updatedAt` timestamp bump
carried over from a prior session (already present, unrelated, in the primary checkout's working
tree before Task 1 began, and separately called out in `15-03-SUMMARY.md`'s session 3 capture).
`git -C /home/dd/projects/gsd-beads status --porcelain -- .gsd` (directory only, entries excluded)
reports nothing -- the `.gsd/` tree itself is untouched. No file under `~/.claude/plugins/cache/`
was modified: `find <cache-root> -newer <pre-run-marker> -type f` returned no results for either
plugin after all three hook runs.

## Step 1 -- Confirm the ship.md patch marker is present

```text
$ grep -c 'gsd-beads-patch:ship-pre-generic-dispatch v1' "$HOME/.claude/gsd-core/workflows/ship.md"
2
```

(2 = the opening `<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->` marker at line 157 and
the closing `<!-- /gsd-beads-patch:ship-pre-generic-dispatch v1 -->` marker at line 242 -- the
**same line numbers** `13-GATE-SMOKE-TEST.md` and `14-GATE-SMOKE-TEST.md` both recorded, confirming
no drift in the installed file across Phases 13, 14, and 15.) The generic dispatch loop is
confirmed present and live on this machine, re-verified rather than cited.

## Step 2 -- markdown-linting: two-case predicate smoke test (reproducing 13-GATE-SMOKE-TEST.md Step 2)

Predicate extracted from the **installed** copy, not the repo copy:

```text
$ jq -c '.gates[0].check.predicate' \
    "/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0/.gsd/capabilities/markdown-linting/capability.json"
{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}
```

**Predicate source (absolute, installed cache path):**
`/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0/.gsd/capabilities/markdown-linting/capability.json`

**Installed-vs-repo predicate diff:**

```text
$ diff <(jq -cS '.gates[0].check.predicate' "/home/dd/.claude/plugins/cache/gsd-beads/markdown-linting/0.1.0/.gsd/capabilities/markdown-linting/capability.json") \
       <(jq -cS '.gates[0].check.predicate' "<this repo's .gsd/capabilities/markdown-linting/capability.json>")
(no output)
```

Byte-identical after `jq -cS` normalisation -- extraction altered no gate semantics. Result
confirmed independently for both plugins in Step 0's earlier check on this worktree's own repo
copy.

Both cases below ran against a synthetic `15-LINT-REPORT.md` in a scratch phase directory outside
`.planning/`, under this session's temporary scratchpad
(`/tmp/claude-*/.../scratchpad/15-gate-reproof/`). `git status --porcelain` for
`.planning/phases/13-markdown-linting-capability-dogfood` was empty both before and after (see
Step 4).

### Satisfied case (`violation_count: 0`)

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"LINT-REPORT.md","field":"violation_count","equals":0}' \
    --phase-dir /tmp/.../scratchpad/15-gate-reproof/mdl-zero \
    --phase-number 15 --raw
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
    --phase-dir /tmp/.../scratchpad/15-gate-reproof/mdl-seven \
    --phase-number 15 --raw
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

**Result:** byte-identical to `13-GATE-SMOKE-TEST.md` Step 2: `block: false`/`match: true` at
`violation_count: 0`, `block: true`/`match: false` with `actual: "7"` (string) against
`expected: 0` (integer) at `violation_count: 7`. The string-versus-integer asymmetry, run this
time against the installed predicate, still holds -- the property that makes the tool-absent
non-numeric `"unavailable"` sentinel safe is unaffected by extraction.

## Step 3 -- pr-workflow: four-case predicate smoke test (reproducing 14-GATE-SMOKE-TEST.md Step 2)

Predicate extracted from the **installed** copy, not the repo copy:

```text
$ jq -c '.gates[0].check.predicate' \
    "/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0/.gsd/capabilities/pr-workflow/capability.json"
{"kind":"artifact-frontmatter-equals","artifact":"PR.md","field":"pr_gate_ok","equals":true}
```

**Predicate source (absolute, installed cache path):**
`/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0/.gsd/capabilities/pr-workflow/capability.json`

**Installed-vs-repo predicate diff:**

```text
$ diff <(jq -cS '.gates[0].check.predicate' "/home/dd/.claude/plugins/cache/gsd-beads/pr-workflow/0.1.0/.gsd/capabilities/pr-workflow/capability.json") \
       <(jq -cS '.gates[0].check.predicate' "<this repo's .gsd/capabilities/pr-workflow/capability.json>")
(no output)
```

Byte-identical after `jq -cS` normalisation.

All four cases ran against synthetic `15-PR.md` files in scratch phase directories outside
`.planning/`, one per `pr_status` state, each paired with the `pr_gate_ok` boolean Phase 14
recorded for it. Assertion is against the derived `pr_gate_ok` boolean, not the raw `pr_status`
field -- a single-scalar equality predicate cannot express the OR across the two passing states
(`none`, `passing`), which is why the derived field exists.

### `pr_status: none` / `pr_gate_ok: true` (satisfied)

```text
$ gsd_run check predicate \
    --predicate '{"kind":"artifact-frontmatter-equals","artifact":"PR.md","field":"pr_gate_ok","equals":true}' \
    --phase-dir /tmp/.../scratchpad/15-gate-reproof/prw-none \
    --phase-number 15 --raw
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
    --phase-dir /tmp/.../scratchpad/15-gate-reproof/prw-passing \
    --phase-number 15 --raw
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
    --phase-dir /tmp/.../scratchpad/15-gate-reproof/prw-pending \
    --phase-number 15 --raw
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
    --phase-dir /tmp/.../scratchpad/15-gate-reproof/prw-failing \
    --phase-number 15 --raw
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

**Result:** byte-identical to `14-GATE-SMOKE-TEST.md` Step 2 across all four states: `block:
false`/`match: true` for both `none` and `passing`, `block: true`/`match: false` (`actual:
"false"`) for both `pending` and `failing` -- the exact tri-state split PRW-02 requires,
reproduced from the installed predicate.

## Step 4 -- Untouched-artifact invariant

```text
$ git status --porcelain -- .planning/phases/13-markdown-linting-capability-dogfood \
                            .planning/phases/14-pr-workflow-capability-dogfood
(no output)
```

Empty, both before and after all six `gsd_run check predicate` invocations above. Every synthetic
artifact (`15-LINT-REPORT.md` x2, `15-PR.md` x4) lived exclusively under
`/tmp/claude-*/.../scratchpad/15-gate-reproof/`, outside `.planning/` entirely -- neither Phase
13's nor Phase 14's real report was read, written, or otherwise touched by this task.

## Result

| # | ROADMAP Success Criterion | Evidence |
|---|---------------------------|----------|
| 3 (auto-install half) | Installing from the real marketplace and running the installed copy's SessionStart hook grants each capability at user scope | Step 0: both plugins installed from `gsd-beads`; both hooks printed `Auto-installed capability: <id> (user scope)` on first run; both user-scope destinations byte-identical to the installed bundle |
| 3 (re-consent half) | The content-hash re-consent cycle (grant / no-op / re-grant) still works from the installed copy | Step 0: both capabilities show grant (sidecar created, line printed), no-op (second run silent, sidecar byte-identical), and re-grant (cleared sidecar re-produces the identical hash and re-prints the line) |
| 3 (gate half, markdown-linting) | `gsd_run check predicate` with the installed predicate reproduces Phase 13's two-case outcome | Step 2: `block:false`/`match:true` at 0, `block:true`/`match:false`/`actual:"7"` at 7 -- byte-identical to `13-GATE-SMOKE-TEST.md` |
| 3 (gate half, pr-workflow) | `gsd_run check predicate` with the installed predicate reproduces Phase 14's four-case outcome | Step 3: `block:false` for `none`/`passing`, `block:true`/`actual:"false"` for `pending`/`failing` -- byte-identical to `14-GATE-SMOKE-TEST.md` |
| (extraction-fidelity check) | The predicate shipped in each installed copy is byte-identical to the one Phases 13-14 proved | Steps 2 and 3: `diff <jq -cS installed> <jq -cS repo>` produced no output for both capabilities |
| (confound control) | Every predicate read from the cache, every artifact outside `.planning/` | Steps 2-4: predicate source paths quoted absolutely; scratch directory paths shown for every case; Phase 13/14 real directories confirmed untouched |

Extraction did not silently break either gate or invalidate consent. Both `markdown-linting` and
`pr-workflow` auto-install, re-consent, and gate exactly as they did before extraction, now proven
from the marketplace-installed copy rather than from this repository's working tree.
