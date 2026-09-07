# Critical code review — sota-numerics `feat/extended-sota-definition` @ `1de851c`

Worktree reviewed: `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`
Baseline: `origin/main` (`eccad87`, v0.1.3). 110 commits ahead, tree clean, 35 tracked files, all read or executed.
All four suites run green locally at HEAD: 97 Python tests, 3 shell suites, `ALL PASS`.

Every count below was re-derived by me from the tree, not taken from prose.

---

## Summary (BLUF)

The gate hardening in this release is genuinely good work — the `${PHASE_DIR}` splice removal is
correct and the reasoning in `NOTES.md` §6 is measured rather than asserted. I verified
gsd-core's `evaluateCommandExitZero` (`~/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs:62-102`)
and `NOTES.md` §1's description of it is exactly right, line for line.

But the release does not ship. Three things block it:

1. An **unconditional arbitrary-code-execution path** fires on every session start, from
   `hooks/session-start.sh`. I reproduced it. It is pre-existing (unchanged since 0.1.3), but
   this is the release whose stated theme is provenance hardening, and it publishes that hook
   machine-wide.
2. The blocking gate's central invariant — "at least two named mechanism alternatives" — is
   **fail-open bypassable two ways**, one of which is the exact defect class the CHANGELOG
   claims to have closed. I reproduced both.
3. Three prose claims are **false against the shipped tree**, measured: the test-suite
   comparison, the `__pycache__` example, and the completeness of the CHANGELOG's
   behaviour-change enumeration.

---

## P0 (blocking)

### P0-1 — `hooks/session-start.sh` executes arbitrary code from the user's current repository, on every session start

**File:** `hooks/session-start.sh:8-10` → `hooks/gsd-tools.sh:5-7`

```bash
# hooks/session-start.sh:8-10
if [ -f "$PLUGIN_ROOT/hooks/gsd-tools.sh" ]; then
  . "$PLUGIN_ROOT/hooks/gsd-tools.sh"
  ENABLED="$(gsd_tools config-get sota-numerics.enabled --default true 2>/dev/null)"; ENABLED_STATUS=$?
```

```bash
# hooks/gsd-tools.sh:5-7
    _root="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [ -n "$_root" ] && [ -f "$_root/gsd-core/bin/gsd-tools.cjs" ]; then
      _GSD_TOOLS_ARGS=(node "$_root/gsd-core/bin/gsd-tools.cjs")
```

**Mechanism.** `git rev-parse --show-toplevel` carries no `-C`, so it resolves against the
*hook's* working directory, which is the user's project — not `$PLUGIN_ROOT`. Any repository
that contains a file at `gsd-core/bin/gsd-tools.cjs` therefore has that file executed under
`node` by the plugin, unconditionally, at `SessionStart` (`hooks/hooks.json:6-10`) and again at
every `gsd-planner` / `gsd-executor` / `gsd-verifier` `SubagentStart`
(`hooks/hooks.json:13-30`). There is no hash fast path in front of it — unlike
`capability-auto-install.sh`, `session-start.sh` calls `gsd_tools` on every single invocation.
It fires before the user's first prompt and asks for no consent.

**Reproduced**, not inferred. I built a bare repo containing only
`gsd-core/bin/gsd-tools.cjs` (a payload writing `$HOME/PWNED-PROOF.txt`), ran
`bash hooks/session-start.sh planner` with that repo as cwd, and got:

```
executed with args: config-get sota-numerics.enabled --default true
```

The repo had no commits and no remote. `git init` alone is enough.

**Same path, second call site:** `hooks/capability-auto-install.sh:224-228` sources the same
resolver and runs `gsd_tools capability install "$BUNDLE_DIR" --scope global --yes`. The new
provenance guard (lines 82-218) runs *before* this, which is correct as far as it goes — but the
guard proves things about the *bundle*, and then hands execution to a `.cjs` file chosen by the
*user's cwd*. On the common marketplace shape (plain-directory plugin cache → not a repo →
`ls-files` 128 → `unverifiable_repo` returns 1 → install proceeds) this is reached on first use.

**Why this is P0 and not a note.** `README.md:68` documents the resolution order
("Resolution checks the current repository's `gsd-core/bin/gsd-tools.cjs`, …") but nowhere
states that this is a code-execution channel from untrusted repository content. A release that
adds 241 lines of hook code to prove that *bundle bytes* are published, while executing
*arbitrary repository bytes* two lines later, has its threat model inverted. The auto-install
guard's own comment (`capability-auto-install.sh:90-92`) names the accident it defends against;
this is a strictly larger one.

**Minimal fix.** Anchor the first rung to the plugin, not the cwd:

```bash
-    _root="$(git rev-parse --show-toplevel 2>/dev/null)"
+    _root="$(git -C "${CLAUDE_PLUGIN_ROOT:-.}" rev-parse --show-toplevel 2>/dev/null)"
```

or delete the rung outright and keep only `command -v gsd-tools` and
`${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs` — the rung exists only for
gsd-core monorepo development. Either way `README.md:68` and `README.md:216` must change with it,
and `tests/test-session-start.sh` needs a red case (a repo-local `gsd-core/bin/gsd-tools.cjs`
must NOT be executed).

**Pre-existing:** yes. `hooks/gsd-tools.sh` is byte-identical to `origin/main`
(`git diff --quiet origin/main..HEAD -- hooks/gsd-tools.sh` → identical), and
`origin/main:hooks/capability-auto-install.sh:63` carries the same line. It is not introduced by
this diff. It is shipped by this release. Per the project's own standing rule, it needs a fix or
an explicit approved deferral with a ticket — not silence.

**Confidence: 95** (empirically reproduced; both call sites quoted verbatim).

---

## P1 (required)

### P1-1 — The gate's "at least two named alternatives" invariant is fail-open bypassable; one bypass is the exact class the CHANGELOG says it closed

**Files:** `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:115`, `:329-380`

```python
# :115
BULLET_RE = re.compile(r"^[ \t]*[-*][ \t]+\*\*(.{1,200}?)\*\*", re.MULTILINE)
```

```python
# :329-331
def mask_fenced_regions(text):
    """Blank fenced blocks and HTML comments, preserving offsets.
```

**Mechanism.** `BULLET_RE` accepts unbounded leading whitespace (`^[ \t]*`), and
`mask_fenced_regions` masks only *fenced* code blocks and HTML comments. CommonMark has a second
code-block form — the four-space **indented** code block — and it is not masked. Two consequences,
both reproduced against the shipped script:

**(a) An indented-code example satisfies the gate. Exit 0.**

```markdown
## Alternatives Considered

Example of the required shape:

    - **Householder QR**: stable. `NumPy QR docs` (2025).
    - **Pivoted LU**: baseline. https://docs.scipy.org/ (2025).

    Decided by: performance -- QR is the stable first choice.

That is all; this plan makes no real comparison.
```
→ `python3 check-alternatives.py <dir>` → **exit 0**.

`CHANGELOG.md:45-52` states categorically:

> "Fenced code blocks no longer count as plan content. … A plan quoting an example in its
> README-style prose could therefore pass on the example's own text."

That defect is closed for fences and open for indented blocks. The claim as written is false.

**(b) A nested sub-bullet counts as the second alternative. Exit 0.**

```markdown
## Alternatives Considered

- **Householder QR**: stable. `NumPy QR docs` (2025).
  - **sub-consideration**: pivoting order. `LAPACK guide` (2025).

Decided by: performance.
```
→ **exit 0**, on a plan naming exactly **one** alternative. This is precisely the failure the
gate exists to catch, in `README.md:244`'s own words: *"the agent generated one option and moved
on."*

Neither case is recorded anywhere — `grep -rn "indented code\|4-space\|four-space" README.md
CHANGELOG.md .gsd/ tests/` returns nothing. It is an unrecorded fail-open gap, not a documented
limit like the placeholder-host narrowness.

**Minimal fix.** Bound both scans to CommonMark's non-code indentation: change `BULLET_RE`'s
`^[ \t]*` to `^[ \t]{0,3}` (matching the bound already used by `NEXT_HEADING_RE:106` and
`FENCE_LINE_RE:169`), and either mask indented code blocks in `mask_fenced_regions` or state the
gap in `NOTES.md`. Add red cases for both fixtures.

**Confidence: 95** (both bypasses executed against the shipped script; exit codes observed).

### P1-2 — CHANGELOG's measured comparison does not describe the tree being released

**File:** `CHANGELOG.md:12-22`

> "Measured at `253bbdc`: running this release's 94-test suite against the 0.1.3 checker, 62 pass
> unchanged and 32 fail. … 12 phase-resolution cases …, 9 section-boundary cases …, 4
> HTML-comment cases, 4 rejected-plan-name cases, the 2 empty-argument cases, and 1
> error-message case."
>
> "Counts here name the commit they were measured at, because every earlier revision of this
> paragraph went stale within hours of being written and one shipped a fix that did not exist."

**Mechanism.** I reproduced the ablation properly (full tree at each rev, only
`check-alternatives.py` swapped for `origin/main`'s):

| commit | tests | pass vs 0.1.3 | fail vs 0.1.3 |
| --- | --- | --- | --- |
| `3e9fa2e` | 89 | 61 | 28 |
| `253bbdc` | 94 | 62 | 32 |
| `1de851c` (HEAD, the release) | **97** | **62** | **35** |

The numbers are correct *at `253bbdc`* and stale *at HEAD*, two commits later. The paragraph that
warns about going stale went stale. Diffing the failing-test sets, the release ships **four**
behaviour-changing cases the enumeration does not cover and drops one:

- `test_a_truncating_heading_is_named_in_the_count_message`
- `test_a_truncating_heading_is_named_rather_than_a_missing_field`
- `test_current_phase_in_prose_does_not_redirect_the_gate`
- `test_state_md_without_frontmatter_blocks`
- (removed: `test_empty_arg_exits_2_instead_of_scanning_cwd`)

Two of those are user-visible **and security-relevant**, and appear in no CHANGELOG paragraph at
all: `current_phase` is now read only from STATE.md's YAML frontmatter (`:235-241`), so a
`current_phase:` line in prose or inside a fenced example can no longer redirect the gate to a
different phase; and a STATE.md with no frontmatter now exits `2`. A consumer upgrading learns
neither from the CHANGELOG. Similarly the setext-underline boundary shipped in the final commit
`1de851c` is absent from the "9 section-boundary cases" tally.

**Minimal fix.** Re-measure at the commit that reaches `main`, and add one paragraph each for the
frontmatter-only `current_phase` scoping and the setext boundary. `2c6466e`'s stated intent —
"stop asserting a count that ages" — was not achieved; pinning a commit does not stop the count
ageing, it only records which age it is.

**Confidence: 97** (measurements reproduced three times; test-name diff computed).

### P1-3 — README and CHANGELOG assert a `__pycache__` failure mode the test suite does not produce

**Files:** `README.md:58`, `CHANGELOG.md:93-95`

> `README.md:58` — "Running the test suite trips this: it leaves `__pycache__/` inside the
> bundle, which `git status` calls clean but a directory copy would still publish. Delete it."
>
> `CHANGELOG.md:93-95` — "The ignored-files case catches contributors by surprise: running the
> test suite leaves `__pycache__/` inside the bundle … Delete it and reopen the session."

**Mechanism.** No test imports `check-alternatives.py` as a module — `run_check`
(`tests/test_check_alternatives.py:45-53`) shells out with
`subprocess.run([sys.executable, str(SCRIPT), ...])`, and CPython writes no `__pycache__` for a
script run as `__main__`. Measured, after running the full suite:

```
$ python3 -m unittest tests/test_check_alternatives.py   # 97 tests, OK
$ find .gsd -name '__pycache__' -o -name '*.pyc'
(empty)
$ git status --porcelain --ignored --untracked-files=all -- .gsd/capabilities/sota-numerics
(empty)
```

`tests/__pycache__` is created; the bundle's is not. The remediation advice in the release's own
refusal table is for a condition the release cannot produce. (The *guard* is correct and is
correctly pinned by `tests/test-capability-auto-install.sh:351-355`, which synthesises the
ignored file. Only the worked example is wrong.)

This matters more than a typo would, because D-20 makes it a phase acceptance criterion: "every
behavioural claim in `README.md` traces to a line of code or config." This one traces to nothing.

**Minimal fix.** Replace the example with one that is reachable (e.g. an editor swap file, or a
locally-generated artefact inside the bundle), or delete the sentence from both files.

**Confidence: 96** (measured; harness code quoted).

### P1-4 — The blocking gate's dispatch is conditioned on another capability's config key, and nothing records it

**Evidence:** `~/.claude/gsd-core/workflows/plan-phase.md:1558-1560`

> "## 13e. Post-Planning Gap Analysis (plan:post capability gate dispatch)
>
> Proactive, non-blocking coverage report gated on `workflow.post_planning_gaps`
> (default `true`)."

and `~/.claude/gsd-core/bin/lib/capability-registry.cjs:4936`:

```js
  "workflow.post_planning_gaps": "gap-analysis",
```

**Mechanism.** Step 13e is the *only* dispatch point for `plan:post` gates, and it is
LLM-executed prose whose opening sentence names a config key owned by the **gap-analysis**
capability. `render-hooks` will still return sota-numerics' gate (its `when` is
`sota-numerics.enabled`, `capability.json:86`), so the gate is registered — but a runtime that
reads "gated on `workflow.post_planning_gaps`" as gating the *step* will skip the whole
dispatch, and this capability's only blocking gate silently never fires. There is no verdict, no
error, and no way for the author to notice.

`NOTES.md` §2 quotes §13e and §6's "Residual" section carefully records the *other* gsd-core
coupling (13b/13e write ordering, ticketed `gsd-beads-g72`). This coupling — the one that can
turn the gate off entirely — is recorded nowhere. `grep -rn "post_planning" README.md
CHANGELOG.md NOTES.md` returns nothing.

Both `plugin.json:3` and `capability.json:6` sell the gate as enforcing "on every plan in a
phase". That claim is conditional on a key this capability neither owns nor mentions.

**Minimal fix.** Add a `NOTES.md` §6 residual entry naming `workflow.post_planning_gaps`, with a
tracking ticket, in the same shape as the existing `gsd-beads-g72` entry. Soften the two
`description` strings, or state the precondition in `README.md`'s Requirements section.

**Confidence: 78** (gsd-core source quoted exactly; the skip is an inference about LLM execution
of ambiguous workflow prose, not a proven code path — hence not 90+).

### P1-5 — PR #4 is eleven commits behind the tree, and four of them are gate fixes (D-26 breach)

PR head `e3d253a`; local HEAD `1de851c`. `git log --oneline e3d253a..HEAD`:

```
1de851c fix(gate): require a paragraph above a setext underline, and name the boundary
d460b0b test(gate): drop five tests no mutant needs, restore one pin
2c6466e docs(changelog): re-measure the comparison, and stop asserting a count that ages
253bbdc fix(gate): report plan-shaped files the name filter rejects
3e9fa2e docs: hold one spelling locale, en-GB
7e580f6 fix(gate): mask HTML comments the way fenced regions are masked
a4c171e docs: state the three-rung gate script resolution the command actually has
bcdc7ab docs: cut prose that restates the table and rule beside it
7234007 fix(gate): require STATE.md's two phase witnesses to agree
c88ddf5 test(hook): cut comment restatement and one duplicated D0 check
4da2e47 docs(hook): cut four comment blocks that restate what is already stated
```

**Mechanism.** D-26 (`23-CONTEXT.md:62`) is explicit: "Internal review and every fix it accepts
land on the branch before the pull request opens, so an external reviewer's first pass sees a
finished diff rather than a known-incomplete one." Four `fix(gate)` commits — HTML-comment
masking, the two-witness `current_phase` agreement (a redirect hardening), misnamed-plan
reporting, and the setext boundary — plus the CHANGELOG re-measurement are invisible to anyone
reviewing PR #4. That is the precise waste D-26 was written to prevent, on the release D-26 was
written for. It is also why the CHANGELOG count in P1-2 diverged.

**Minimal fix.** Push the branch before any further external review pass; re-verify
not-behind-base at the open instant, per the same rule.

**Confidence: 92** (commit list is exact; PR head supplied by the caller and consistent with the
local graph).

---

## P2 (suggestions)

### P2-1 — A backticked `<!--` blanks the rest of the plan, producing a false block with a wrong diagnostic

`check-alternatives.py:173`, `:361-367`

```python
HTML_COMMENT_OPEN = "<!--"
...
        comment = text.find(HTML_COMMENT_OPEN, pos)
```

Plain `str.find`, with no awareness of inline code spans. Reproduced: a plan containing the
sentence ``We discuss `<!--` markers here.`` before its section blanks everything to EOF (no
`-->` follows) and the gate reports:

```
11-01-PLAN.md: missing '## Alternatives Considered' section
```

The section is plainly present three lines below. The direction is fail-closed, so this is not a
bypass — but `NOTES.md` and the section-boundary tests treat exactly this failure shape (a false
block whose diagnostic names neither the rule nor the truncation) as worth a code change for the
`===` case; the same standard should apply here. Minimal fix: skip comment openers inside a
backtick span, or state the limitation next to the docstring's fail-closed note.
**Confidence: 92** (reproduced).

### P2-2 — `Decided by:` inside `### Internal design alternatives` satisfies the mechanism requirement

`check-alternatives.py:584` searches `DECIDED_BY_RE` over the whole `body`, including the internal
subsection that `split_entries` (`:433-496`) is careful to exclude from the entry count. Reproduced:
two compliant mechanism bullets plus a `Decided by:` line that appears only under the internal H3
→ exit 0. `README.md:145` and `planner-sota.md:4` both say internal entries "cannot lend evidence
to a mechanism entry"; neither says they can supply the decision line, and the intent is clearly
that they cannot. Minimal fix: search only the non-internal spans, or document it.
**Confidence: 90** (reproduced).

### P2-3 — `${GSD_HOME:-$HOME}` with both unset resolves the third rung to `/`

`capability.json:81`. With `HOME` and `GSD_HOME` both unset (`sh -c` has no `set -u`), the third
rung becomes `/.gsd/capabilities/sota-numerics/scripts/check-alternatives.py`. Direction is
fail-closed (`test -f` → exit 1 → block), so this is a robustness note, not a hole — but
`tests/test-gate-script-resolution.sh` never exercises it; every case sets `GSD_HOME` or `HOME`.
Add `env -u HOME -u GSD_HOME` to case 2.
**Confidence: 88.**

### P2-4 — `NOTES.md` pins gsd-core line numbers that will drift

`NOTES.md:128-130` cites `plan-phase.md:1524` and `plan-phase.md:1558`. Against the installed
gsd-core **1.13.0** those land within a few lines of the right headings, but `capability.json:12`
declares `"gsd": ">=1.10.0"`, so the citation is only valid for one point release of a range the
capability claims to support. Cite the section headings ("13b", "13e") without line numbers.
**Confidence: 90** (both files read).

### P2-5 — The capability's own "quiet" rule is not applied to its hooks

`executor-numerics.md:7` defines quiet as "on success it prints a compact machine-readable result
or nothing at all"; `verifier-precision.md:5` says to flag "progress chatter on the success path".
`capability-auto-install.sh:235` prints `Auto-installed capability: sota-numerics (user scope)` to
stdout on success, and `session-start.sh:39` prints a two-line banner on every SessionStart *and*
every planner/executor/verifier SubagentStart — duplicating, for those three roles, the steering
that `capability.json`'s contributions already inject at `plan:pre` / `execute:wave:pre` /
`execute:wave:post`. D-19 exempts `hooks/*.sh` from prose refactor, so this is a note, not a
required change; but a release whose theme is "low token cost at runtime" pays for the same
framing twice per subagent.
**Confidence: 85.**

### P2-6 — `tests/.planning/.gitkeep` is vestigial

Tracked since the initial extraction commit `31608f2`. The Python suite creates its own
`.planning` under `tempfile.mkdtemp` (`tests/test_check_alternatives.py:28-31`) and no test
references `tests/.planning`. Pre-existing dead file — flagging, not deleting.
**Confidence: 90.**

---

## What I checked and found correct (so the above is not mistaken for the whole picture)

- **`NOTES.md` §1 vs gsd-core.** Verified against
  `gate-predicate-evaluator.cjs:62-102`: timeout → `block:true`, `exitCode === 0` → `block:false`,
  everything else (including 127 and signal-kill `null`) → `block:true`; `throw` only from a
  malformed predicate or unknown kind (`:65`, `:68`, `:74`, `:189`). §1 is accurate line for line.
- **`NOTES.md` §6's "grep -c PHASE_DIR capability.json is 0"** — verified, 0.
- **The refusal set.** The hook emits exactly **9** refusals (`capability-auto-install.sh:74, 86,
  154, 158, 186, 190, 208, 212, 216`); `README.md:52-60` tabulates exactly 9; case `D0`
  (`tests/test-capability-auto-install.sh:820-874`) compares the two as sets in both directions
  and fails loudly on a degenerate parse. This is the best test in the repo.
- **"Eleven rows."** `capability-auto-install.sh:104-105` says the three `ls-files` exit codes
  split into eleven rows; the test header enumerates twelve numbered rows, of which row 1 is the
  pre-`ls-files` git check. 2-8 (7) + 9 (1) + 10-12 (3) = 11. Consistent.
- **Fragment line budget (D-08).** planner 11 + executor 10 + verifier 7 + ship 4 = **32** ≤ 45.
- **Counts.** 4 contributions and 1 gate in `capability.json`; "four advisory prompts and one
  blocking plan gate" in `README.md:5`; "four advisory fragments" in `NOTES.md:16`; "the single
  blocking plan:post gate" in `capability.json:6`. All agree. Version `0.2.0` in both manifests
  (D-23 satisfied).
- **Recency window.** `RECENCY_WINDOW_YEARS = 6` with `today_year - 6 <= y <= today_year` is
  exactly `README.md:150`'s "current year through six years earlier, counting both endpoints"
  (7 distinct years). `NOTES.md` §5's at-least-one-in-window rule is pinned by
  `TestFoundationalCitationPairing` (`tests/test_check_alternatives.py:1437`), as §5 claims.
- **Placeholder-host narrowness, structural-only checking, year-not-linked-to-citation** — all
  three admitted limits in `README.md:152, 162` match the code (`HOST_RE:130`, `YEAR_RE:124`).
- **Test quality.** Substantially better than typical. `TestSectionBoundary`
  (`tests/test_check_alternatives.py:569-680`) asserts the *reason* string and asserts the
  donated entry's name is **absent** — it would fail if the boundary broke even where the exit
  code stayed 1. `test_a_boundary_is_not_blamed_when_the_field_is_simply_absent` (`:662`) pins the
  negative direction of the same diagnostic. I found **no** test that would still pass with the
  code under test deleted, and no structurally-unfailable assertion. The shell suites build their
  own repos, bare origins and stub `gsd-tools` under `mktemp -d`, redirect `HOME`/`GSD_HOME`, and
  set `GIT_CEILING_DIRECTORIES` — and both `test-session-start.sh` case5 and
  `test-capability-auto-install.sh` case `I0` assert the real `GSD_HOME` was untouched, by
  content digest rather than existence. `tests/test-gate-script-resolution.sh` extracts the gate
  command from `capability.json` by JSON parse rather than hand-copying it, so it cannot go stale.
- **CRLF plans** pass correctly (probed).
- **`normalize_phase`** (`:189-193`) correctly makes `06 == 6` and `10.1 != 10.10`.
- **A-01's re-derived numbers** ("at `3e9fa2e`, 89 checker tests, 61 pass, 28 fail") reproduce
  **exactly**. The amendment record is honest; only the CHANGELOG drifted after it.

---

## Decisions D-01..D-27: shipped vs recorded

Satisfied and verifiable: D-02, D-05, D-07, D-08 (32 ≤ 45), D-09..D-17, D-22, D-23.
Amended with a recorded amendment: D-01 (A-01), D-18 (A-02), D-19 + D-21 (A-03). The amendment
section is well done — it names the breach, the cause, and pins its counts to a commit.

Not satisfied:

- **D-20** — "every behavioural claim in `README.md` traces to a line of code or config."
  Falsified by **P1-3** (`README.md:58`) and, in the categorical form the CHANGELOG restates it,
  by **P1-1**.
- **D-26** — "Internal review and every fix it accepts land on the branch before the pull request
  opens." Falsified by **P1-5**: four gate fixes landed after PR #4's head.
- **D-27** (tag `v0.2.0`) — no tags exist in the worktree (`git tag` is empty). Phase-end action,
  not yet due, but note it is the item 0.1.3 also missed.

Amended without a recorded amendment: none found. A-01's "the current set is the commit history …
not a number cached here" correctly anticipates further gate changes, so `1de851c` and `253bbdc`
are inside the amendment's stated envelope.

---

## Against the repo's own SOTA definition

Judged by the standard `capability.json:6` sets — "internally and project-consistent,
unambiguous, complete, efficient, quiet-running, agent-facing":

- **Consistent:** fails. The 94-vs-97 count (P1-2) and the `__pycache__` example (P1-3) are prose
  the code contradicts. `check-alternatives.py`'s own module docstring, `NOTES.md` and the test
  headers are otherwise unusually well synchronised with the code — which is what makes the two
  divergences stand out rather than blend in.
- **Complete:** fails. The gate's central count invariant has two undocumented fail-open holes
  (P1-1), and its dispatch precondition is unrecorded (P1-4).
- **Unambiguous:** largely passes. `NOTES.md` §6's enumeration of `sh` quoting contexts, and its
  explicit correction of its own earlier false claim about single quotes, is the strongest prose
  in the release.
- **Efficient / quiet:** passes for the gate (fast path at `capability-auto-install.sh:80` avoids
  spawning node on unchanged bundles; `check-alternatives.py` prints nothing on success and
  exactly one `remediation:` line on failure), with the P2-5 caveat.
- **Secure:** fails. P0-1.

---

## Verdict

**DO-NOT-SHIP.**

Blocking before merge to `main` (which is the publish, per D-25):

1. **P0-1** — fix the cwd-rooted `gsd-tools` resolution, or get explicit approval to defer it with
   a filed ticket. Add a red test.
2. **P1-1** — close or document the indented-code-block and nested-bullet count bypasses; the
   `CHANGELOG.md:45-52` claim is currently false as written.
3. **P1-2** — re-measure the comparison at the commit that reaches `main`, and add the missing
   paragraphs for the frontmatter-only `current_phase` scoping and the setext boundary.
4. **P1-3** — remove or replace the `__pycache__` example in `README.md:58` and `CHANGELOG.md:93`.
5. **P1-4** — record the `workflow.post_planning_gaps` coupling in `NOTES.md` §6 with a ticket.
6. **P1-5** — push the branch and re-verify not-behind-base immediately before any external
   review pass, per D-26.

P2 items are genuinely optional, except that P2-1 and P2-2 are cheap and touch the same functions
P1-1 must change anyway.
