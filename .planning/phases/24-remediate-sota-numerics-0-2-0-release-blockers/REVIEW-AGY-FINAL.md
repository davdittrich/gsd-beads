# Adversarial review — sota-numerics `feat/extended-sota-definition` @ 1de851c

Delegated to agy (Google Antigravity, gemini-3.1-pro-high) with **direct read access to the
real worktree** (`--add-dir /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`).
Read access verified before the review runs: agy returned line 1 and line 50 of
`hooks/capability-auto-install.sh` verbatim. No file was summarised for agy at any point.

Every agy finding below was re-verified by me against the real file, and most by live
reproduction against the real script. Findings agy asserted without quoted evidence, or that
my own measurement contradicted, are marked REJECTED/REFUTED and are not relayed as defects.

Read-only: no file in the reviewed repository was modified. `git status --porcelain` is empty
after the review; probes ran in the scratchpad against copies of plan fixtures, and the gate
script was invoked with `PYTHONDONTWRITEBYTECODE=1` where it could have written bytecode.

## Coverage and delegation failures

| Area | agy run | Result |
| --- | --- | --- |
| hooks (auto-install, session-start, hooks.json, gsd-tools) | r1 | completed |
| gate script + capability.json + fixtures | r2 | completed |
| README / CHANGELOG / NOTES fact-check | r4a | completed |
| **test suite** | r3, r3a, r5, r6 | **all four timed out — NOT COVERED BY AGY** |

agy could not process `tests/test-capability-auto-install.sh` (893 lines) or
`tests/test_check_alternatives.py` (1515 lines) within 900 s, in-sandbox or with the full file
inlined, even scoped to three narrow questions. The test-suite category is therefore **my own
work, explicitly labelled as such** — it is not an agy result and should not be reported as one.

---

## CONFIRMED — gate bypasses (`check-alternatives.py`)

All four reproduce live against the real script. Each `exit 0` is a **false PASS**: a blocking
plan gate letting an unresearched plan through.

### P1 — Alternatives inside a 4-space indented code block pass the gate
`.gsd/capabilities/sota-numerics/scripts/check-alternatives.py:561`

```python
    body, boundary = extract_section_body(mask_fenced_regions(text))
```

`mask_fenced_regions` masks ``` / ~~~ fences and `<!-- -->` comments only. CommonMark's
indented code block is not masked, so bullets that render as literal code are counted as real
alternatives. Reproduction (**exit 0**):

```markdown
## Alternatives Considered

    - **FakeAlpha** see `docs/alpha.md` 2024 for details
    - **FakeBeta** see `docs/beta.md` 2024 for details
    Decided by: performance
```

This one matters because the masking docstring argues at length that a plan must not be
credited for content the rendered page hides — and this is exactly that class, missed.

### P1 — A YAML frontmatter block satisfies the gate for a plan whose body has no section
Same line. PLAN.md frontmatter is never stripped (only STATE.md's is, via
`STATE_FRONTMATTER_RE:138`). Reproduction (**exit 0**), body contains no alternatives at all:

```markdown
---
title: sneaky
## Alternatives Considered
- **FakeAlpha** `docs/alpha.md` 2024
- **FakeBeta** `docs/beta.md` 2024
Decided by: performance
---

# Real Plan

No alternatives here at all.
```

### P2 — Setext H2 (`---` underline) is not a section boundary
`check-alternatives.py:105-109`

```python
NEXT_HEADING_RE = re.compile(
    r"^[ \t]{0,3}#{1,2}[ \t]+"
    r"|^[ \t]{0,3}[^\s][^\n]*\n[ \t]{0,3}=+[ \t]*$",
    re.MULTILINE,
)
```

Only `=` underlines close the section. Entries under an unrelated `---`-underlined heading are
donated into `Alternatives Considered`. Reproduction: **exit 0** on a plan whose
`## Alternatives Considered` section body is the sentence "This section is empty on purpose."

Deliberate, and argued in the source comment ("`-` underlines deliberately NOT a boundary at
all: they break frontmatter and fences, and treating one would false-block the commonest
horizontal rule"). Relayed as a residual bypass of a documented trade-off, not as a mistake.
Note HEAD (1de851c) is `fix(gate): require a paragraph above a setext underline` — this exact
area was the last thing touched before the release.

### P2 — Lowercase plan name is skipped silently, exit 0
`check-alternatives.py:68`

```python
PLAN_SHAPED_RE = re.compile(r"(?:^|-)PLAN\.md$")
```

A phase whose only plan is `11-01-plan.md` yields **exit 0 with no output** — byte-identical to
a clean pass. Confirmed on this (case-sensitive) filesystem. The source comment concedes the
residual case: on a case-insensitive filesystem gsd-core's `*-PLAN.md` glob *would* load the
plan while the gate would not. **The macOS/Windows half is UNCONFIRMED** — not testable on this
Linux host — but it is acknowledged in the code, so it is a known live gap, not speculation.

### P2 — Symlinked phase directory escapes the `.planning` tree
`check-alternatives.py:276` (`entry.is_dir()` follows symlinks). Confirmed: with
`ln -s "$R/outside" .planning/phases/16-sym`, the gate validated
`$R/outside/11-01-PLAN.md` and printed that outside path on stderr. Low impact — it validates
and names a foreign file rather than leaking its contents — but the traversal is real.

### P2 — A directory named `NN-NN-PLAN.md` crashes with a raw traceback
`check-alternatives.py:551` — `text = path.read_text(encoding="utf-8")` is unguarded against
`OSError`. `mkdir 11-01-PLAN.md` produces an uncaught `IsADirectoryError` and a full Python
traceback, exit 1. Fails **closed**, and `capability.json:88` documents that a crash exits 1 and
maps to block — so this is a diagnostics defect, not a security hole: the author gets a
traceback instead of the careful `<plan_path>: <reason>` + `remediation:` contract the module
docstring promises.

### By design, but the practical bypass a hostile reviewer should name
- One line — `N/A - no mechanism choice is involved here.` — disables the gate for that plan
  entirely (**exit 0** confirmed) on a plan that then says "We will use FancyLib. No other
  library was considered." For an LLM planner that has learned the gate exists, this is the
  cheapest route through it, and nothing checks that the exemption is honest.
- A phase directory containing **no plan files at all** exits 0 silently (confirmed).

### Working as documented — verified, not defects
- HTML-comment masking correctly **blocks** (exit 1) a plan whose whole section is inside
  `<!-- -->`. The defence is real.
- Placeholder-host detection correctly rejects `https://example.org/...`.

### REFUTED — agy's ReDoS claim on `TABLE_ROW_RE`
agy rated this P1. I measured the exact regex it quoted against its own pathological input
(`| **a0** **a1** ...`, no trailing pipe): 971 chars → **1.9 ms**, growth linear across
n = 8/40/120. No backtracking blowup. Not relayed as a defect.

---

## CONFIRMED — `hooks/capability-auto-install.sh`

### P2 — `bundle_hash` can be forged: directory paths are never escaped
`hooks/capability-auto-install.sh:53-57`

```bash
  _list="$(find "$BUNDLE_DIR" \
       -type l -exec sh -c 'for p in "$@"; do printf "%s -> %s\n" "$p" "$(readlink "$p")"; done' _ {} + \
    -o -type f -exec "${HASH_CMD[@]}" {} + \
    -o -print 2>/dev/null)" || return 1
```

agy called this P1 but its reproduction did not demonstrate a collision. I verified the
underlying asymmetry empirically, which is the part that matters:

- `sha256sum` **escapes** a file whose name contains a newline — the line is prefixed with `\`
  and the newline becomes a literal `\n`:
  `\e3b0c442...  <D>/b/file\nweird`
- `find -o -print` **does not escape** directory paths. A directory created with
  `mkdir -p "$B/x"$'\n'"deadbeef  /spoofed/path"` emitted these raw lines into the digest input:

```
<D>/b/x
deadbeef  /spoofed
deadbeef  /spoofed/path
```

So a directory name can inject lines that are byte-indistinguishable from genuine `sha256sum`
output, while a genuine newline-bearing file cannot. That makes a same-hash / different-content
bundle constructible, and a hash match takes the fast path at line 80 — `[ "$NEW_HASH" = "$OLD_HASH" ] && exit 0`
— which skips **every** git guard. Rated P2 rather than P1 because it needs write access inside
the bundle directory and a prior recorded install.

### P2 — No timeout on the install call
`hooks/capability-auto-install.sh:228`

```bash
gsd_tools capability install "$BUNDLE_DIR" --scope global --yes >/dev/null 2>&1
```

Runs inline in a SessionStart hook with no `timeout`. The file's own header claims "Never
aborts the session: no `set -e`" (line 9) — true, but a hang is not an abort, and a hung
provider blocks session start with no feedback.

### P2 — Sidecar write follows symlinks
`hooks/capability-auto-install.sh:237` — `printf '%s' "$NEW_HASH" > "$STATE_FILE" 2>/dev/null`
with no regular-file check. A symlink pre-planted at
`${GSD_HOME:-$HOME}/.gsd/capability-auto-install-sota-numerics.hash` is followed and its target
overwritten with the digest. Requires write access to `~/.gsd` first, so low value.

### Exit-path enumeration — re-derived, and the docs are RIGHT
15 exit points: `17, 23, 25, 33, 75, 80, 87, 155, 159, 187, 191, 209, 213, 217, 244`, of which
**9** print a `refusing to install it at global scope` message (lines 74, 86, 154, 158, 186,
190, 208, 212, 216).

agy asserted the script "claims to have eight distinct refusals" and rated the discrepancy P2.
**REJECTED — the premise is false.** `grep -rniE "eight"` across README, CHANGELOG and NOTES
returns nothing, and README's refusal table has exactly **9 rows**, one per stderr message. agy
supplied no quote for the "eight" claim, so it fails the evidence bar. The enumeration itself is
correct and is relayed as confirmation that the documentation matches the code here.

### REJECTED as findings — real mechanisms, explicitly disclosed
agy rated both P0. Both are real, and both are documented in the same README paragraph, so
neither is a doc/code mismatch:

- **Local `origin/main` forgery.** `git update-ref refs/remotes/origin/main HEAD` satisfies the
  publication check. README:48: *"Anyone who can write that ref can therefore satisfy the check
  — the guard is aimed at running a plugin out of a development worktree by accident, not at an
  adversary with write access to your own repository."* Code comment 193-201 says the same.
- **Untracked bundle installs unguarded.** `TRACKED=1` makes `[ "$TRACKED" -ne 1 ]` false and
  the whole `elif` is skipped. README:48: *"Where none tracks it, there is nothing to check
  against and the bytes install unverified."*

The honest way to state this: the guard is not weak *by accident*, it is narrow *on purpose* and
says so. But 130 lines of hardening buy protection only against one accident, and a reader who
sees a nine-row refusal table may over-read what they are getting.

---

## MY OWN FINDING — agy did not surface this

### P1 — The bundle's bytes are verified; the program that installs them is not
`hooks/gsd-tools.sh:5-7`

```bash
    _root="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [ -n "$_root" ] && [ -f "$_root/gsd-core/bin/gsd-tools.cjs" ]; then
      _GSD_TOOLS_ARGS=(node "$_root/gsd-core/bin/gsd-tools.cjs")
```

`git rev-parse --show-toplevel` resolves against **the user's current working directory**, i.e.
whatever repository the session was opened in. Opening a session inside any repository that
contains `gsd-core/bin/gsd-tools.cjs` causes that repository's JavaScript to be executed with
`node` at session start.

`hooks/session-start.sh:8-10` reaches it on **every** session start, independent of the bundle
guard's verdict:

```bash
if [ -f "$PLUGIN_ROOT/hooks/gsd-tools.sh" ]; then
  . "$PLUGIN_ROOT/hooks/gsd-tools.sh"
  ENABLED="$(gsd_tools config-get sota-numerics.enabled --default true 2>/dev/null)"; ENABLED_STATUS=$?
```

`capability-auto-install.sh:224-228` then hands the *global-scope install itself* to that same
unverified provider, immediately after the guard finished proving the bundle is published.

Resolution order is documented at README:68, but only as mechanics — the consequence (repository
content chooses the binary that performs a machine-wide install) is nowhere in the refusal table
or the security prose.

**Pre-existing, not introduced here.** `git diff --name-only origin/main..HEAD | grep hooks`
returns only `hooks/capability-auto-install.sh`; `gsd-tools.sh`, `session-start.sh` and
`hooks.json` are untouched by this release. It is still the largest hole in the shipped surface.

### Contested — `SubagentStart`
agy rated P2, claiming `SubagentStart` is not a Claude Code lifecycle event and that the
role-specific hooks in `hooks/hooks.json:11` never fire. Supporting evidence exists: gsd-core's
own `CONTEXT.md` enumerates "all seven Claude Code lifecycle events: SessionStart, PreToolUse,
PostToolUse, SubagentStop, Stop, PreCompact ... and FileChanged" — no `SubagentStart` — and
mentions `SubagentStart` only for Codex, Qwen and CodeBuddy.

**Marked UNCONFIRMED and most likely wrong.** This project has a recorded first-hand observation
that these hooks *do* fire in Claude Code (the in-tree worktree auto-publish incident: "the next
executor spawn re-installs"). agy's proposed alternatives (`AgentStart`, `ToolUse`) are
speculation with no quote. Not relayed as a defect.

What *is* solid: `grep -rn "hooks.json\|SubagentStart" tests/ .github/workflows/ci.yml` returns
**nothing**. The wiring that makes every hook in this plugin fire has zero test coverage, so
neither agy's claim nor its refutation can be settled from the repository.

---

## CONFIRMED — documentation

### P1 — README says `draft-PLAN.md` is ignored; the gate blocks on it
README.md:93

> Both numeric segments are required; the phase segment may contain one decimal point. Nested
> plans and names such as `draft-PLAN.md` are ignored.

`check-alternatives.py:68` + `304`:

```python
PLAN_SHAPED_RE = re.compile(r"(?:^|-)PLAN\.md$")
...
        elif PLAN_SHAPED_RE.search(candidate.name):
            misnamed.append(candidate)
```

Reproduced — a phase containing a compliant plan plus `draft-PLAN.md` exits **1**:

```
.../draft-PLAN.md: named like a plan but not `<phase>-<NN>-PLAN.md`, so no plan reader
-- this gate included -- will ever open it; rename it or remove it
```

The *nested* half of the sentence is correct (a plan in a subdirectory exits 0, verified). The
`draft-PLAN.md` half is the exact opposite of the behaviour. A user who trusts README:93 and
leaves a draft in the phase directory has their phase blocked by a gate the README told them
would ignore it. agy found this; I confirmed it by reproduction.

### P2 — CHANGELOG describes a 94-test suite; the release ships 97
CHANGELOG.md:12-13

> Measured at `253bbdc`: running this release's 94-test suite against the 0.1.3
> checker, 62 pass unchanged and 32 fail.

Re-derived: `253bbdc` has **94** tests, HEAD (`1de851c`) has **97**. `253bbdc..HEAD` is 3
commits; 5 tests were removed and 8 added (`d460b0b test(gate): drop five tests no mutant needs`,
then `1de851c`). I ran the CI command — `python3 -m unittest tests/test_check_alternatives.py`
→ `Ran 97 tests ... OK`.

The paragraph pins its measurement commit and warns two lines later that "every earlier revision
of this paragraph went stale within hours of being written" — and the commit that wrote it,
`2c6466e docs(changelog): re-measure the comparison, and stop asserting a count that ages`, was
followed by two commits that aged it again. The 62/32 split has not been re-derived for the 8
tests added since. Found by me; agy was blocked from this by a scope restriction I imposed.

### P2 — "installs only bytes that repository records as published" vs the clean-filter gap
README.md:48 states the "only" claim; `capability-auto-install.sh:177-180` concedes:

```bash
  # What this still cannot see: a `.gitattributes` clean filter maps edited
  # worktree bytes onto the committed blob, so `status` is honestly clean while
  # the copy carries the edit.
```

Real overclaim on the word "only". agy rated P0; **downgraded** — the same paragraph hedges
heavily (the ref-forgery and untracked-bundle carve-outs), and the code notes the filter driver
lives in local config and so does not travel with a clone.

### P2 (weak) — CHANGELOG:89 "tabulates every refusal"
The README table covers the 9 stderr refusals; the silent `exit 0` paths (no hash tool at
line 33, bad capability id at 17, unresolvable plugin root at 23) are not in it. README:68 does
cover the hash-tool case in prose. Pedantic but literally true.

### REJECTED — agy findings without adequate support
- **README:149, "1–300 characters after the URL scheme"** vs `URL_RE = re.compile(r"https?://[^\s)>\]]{1,300}")`.
  agy read this as a claim about *which* characters; the prose reads as a claim about *length*,
  which is accurate. Imprecise at worst.
- **NOTES.md:136 exit-2 table "incomplete."** The table is introduced by "Measured:" and is not
  claimed exhaustive; NOTES.md then says "Do not oversell that." Not a false claim.
- **capability.json:6 description is "marketing."** It is a plugin description field. agy
  supplied no falsified claim.

---

## Test suite — MY OWN WORK (agy timed out four times)

Reported as mine, not as an agy result.

**Isolation is genuinely strong — the brief's concern does not reproduce.** There is a single
entry point to the code under test, `tests/test-capability-auto-install.sh:196-202`:

```bash
run_hook() {
  local _root="${1:-$ROOT}"
  ( cd "$_root" &&
    PATH="${PATH_OVERRIDE:-$SB/bin:$PATH}" \
    HOME="$SB/home" GSD_HOME="$SB/home" GSD_TOOLS_LOG="$SB/installs" \
    GIT_CEILING_DIRECTORIES="$SANDBOX_ROOT" \
    CLAUDE_PLUGIN_ROOT="${2:-$_root}" \
    bash "$HOOK" "$CAP_ID" ) >"$SB/out" 2>"$SB/err"
}
```

Subshell-scoped, with `HOME`, `GSD_HOME`, `PATH` and `GIT_CEILING_DIRECTORIES` all redirected.
On top of that, `check_containment` hashes the *real* global mirror before and after the run and
fails the suite if it changed — with an honest comment that the failure it guards against "has
happened on this project". This is better than the brief assumed. I found no path that touches
the real `~/.gsd` or `~/.claude`.

Two real gaps:
- `real_gsd_state()` uses `find . -name __pycache__ -prune -o -type f -print`, so bytecode
  leaked into the real mirror would not trip the containment check. Minor.
- Zero tests reference `hooks/hooks.json`. The event wiring is untested (see the `SubagentStart`
  item above).

CI (`.github/workflows/ci.yml`) does run all four suites as separate steps, each a bare `run:`
whose failure fails the job. I verified the Python step is not vacuous: it collects and passes
97 tests.

---

## Verdict

agy never produced a consolidated ship/no-ship statement — the run that would have asked for it
was the test-suite pass, which timed out four times. What follows is **mine**, built on the
findings above.

**Weakest part of the release: the gate's markdown parsing.** The masking layer is the whole
basis of the gate's claim to mean something, and its own docstring states the principle
correctly — "what the rendered plan does not say, the gate must not read." It then enforces that
principle for fenced blocks and HTML comments and misses two other constructs that hide content
from the rendered page: 4-space indented code blocks and YAML frontmatter. Both produce a
**silent exit 0** on a plan with no genuine alternatives analysis, which is the single failure
mode the module docstring identifies as worst. These are not exotic inputs; frontmatter is
present in ordinary GSD plans.

**Should it ship?** Not as-is, but the blocking set is small and cheap:

1. **README:93 is factually wrong** and will block users' phases on a file the docs promise is
   ignored. One-sentence fix, no code change.
2. **Indented-code-block and frontmatter masking** — both are additions to
   `mask_fenced_regions`, both have obvious tests, and both are exactly the class of defect this
   release was written to close.
3. **CHANGELOG's 94/62/32 numbers** describe a suite the release does not ship. Re-derive at
   `1de851c` or delete the counts.

Everything else is a legitimate P2 backlog item. Nothing here is a P0: the auto-install hook's
sharpest limitations are real but disclosed in plain language in the README, the gate fails
closed on every error path I could construct, and the test suite's isolation is sound and
self-checking.

The `gsd-tools.sh` provider-resolution issue (P1, mine) is the largest security exposure in the
shipped surface, but it is **pre-existing and untouched by this diff**, so it should be a
tracked ticket rather than a release blocker for this branch.

**One process note, outside the code.** PR #4's head `e3d253a` is eleven commits behind local
HEAD `1de851c`, and two of those eleven changed the gate's setext-boundary behaviour and the
test count. Any external review already performed against #4 was performed against bytes this
release does not ship.
