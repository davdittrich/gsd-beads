# sota-numerics `feat/extended-sota-definition` — prose + token review

Scope: axis A (agent-facing prose, `writing-for-agents` rubric) and axis B (token cost at
execution time). Worktree `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`,
HEAD `1de851c`. Read-only; nothing in the reviewed tree was touched.

**Measurement method.** All token counts are real counts from `tiktoken` `cl100k_base`, not
estimates. Claude's tokenizer differs by roughly ±10% on English prose, so treat every number
as accurate to two significant figures. Line/char counts are `wc`. Gate-output sizes marked
"probed" were produced by running the shipped `check-alternatives.py` against fixtures written
into the scratchpad — the reviewed repository was never written to.

---

## 0. Baseline measurements

### Fragment sizes, `origin/main` → HEAD

| fragment | base tok | head tok | Δ |
| --- | ---: | ---: | ---: |
| `planner-sota.md` | 716 | 616 | −100 |
| `executor-numerics.md` | 169 | 436 | **+267** |
| `verifier-precision.md` | 167 | 279 | +112 |
| `ship-precision-advisory.md` | 137 | 154 | +17 |
| **total** | **1189** | **1485** | **+296 (+25%)** |

### Per-injection cost

`loop-hook-dispatch.md:29` — "Inject `fragment.inline` verbatim into the context for the role
named in `into`" — confirms each fragment lands in the named role's prompt, and
`execute-phase.md:664` puts `execute:wave:pre` dispatch before the per-plan `Agent()` spawn
loop, so `executor-numerics.md` is paid **once per executor prompt**, not once per wave.
`hooks/hooks.json` adds a `SubagentStart` banner on `gsd-planner`, `gsd-executor`,
`gsd-verifier`; `session-start.sh:39` always `printf`s it to stdout, so it enters the same
context as the fragment.

| spawn | fragment | banner | total |
| --- | ---: | ---: | ---: |
| `gsd-planner` | 616 | 113 | **729** |
| `gsd-executor` (each plan) | 436 | 60 | **496** |
| `gsd-verifier` (each wave) | 279 | 72 | **351** |
| `ship:pre` orchestrator | 154 | 0 | **154** |

Worked phase, 3 waves × 2 plans/wave (6 executor prompts, 3 verifier prompts):
`729 + 6×496 + 3×351 + 154 = 4,912 tok`. Same shape on `origin/main`:
`829 + 6×229 + 3×239 + 137 = 3,057 tok`. **This release adds ~1,855 tok per phase (+61%)**,
because the two fragments that grew are the two paid per-plan and per-wave.

### Prose share of the gate script

`check-alternatives.py` is 675 lines / 7,447 tok. Docstrings 1,675 tok, `#` comment blocks
1,787 tok — **46% of the file is prose**. Longest blocks: L42–67 (26 lines, 417 tok),
L80–104 (25 lines, 435 tok), module docstring (25 lines, 374 tok).

---

## Findings

### P1 — SubagentStart banners restate the fragments verbatim, in the same context window

`hooks/session-start.sh:33-36` and `:39`.

```
  planner) FRAMING='Planning: name 2+ current alternatives per non-trivial mechanism choice,
  each with a dated citation, and state which ranked criterion (performance > simplicity/LOC >
  ecosystem > maintenance) decided the pick -- pair foundational citations (Kahan, IEEE 754)
  with a current in-window source. ...'
```

That is `planner-sota.md:2` and `planner-sota.md:7` compressed, and the trailing clause
("This capability ALSO declares a blocking plan:post gate ... not purely advisory") is
`planner-sota.md:1` a third time. The executor banner is `executor-numerics.md:2+3+4`
compressed; the verifier banner is `verifier-precision.md:1-4` compressed.

Defect: duplication, the rubric's single-source-of-truth failure. Both copies land in one
context. The banner adds nothing the fragment does not say better, and it inflates the rule's
apparent rank by stating it twice. It also creates a second maintenance seat that has already
drifted — see the next finding.

Fix: cut the role bodies to a pointer and keep the 23-tok header. Measured replacements:
`"Planning: the plan:post gate blocks a plan whose \`## Alternatives Considered\` section is
non-compliant."` = 24 tok (was 90); executor pointer = 21 tok (was 37).

Saving, measured: planner −90/spawn, executor −37/spawn, verifier −49/spawn. On the worked
phase above: **−535 tok**.

What breaks: if a contribution fails to render (`onError: "skip"` on all four), the banner is
today the only steering the subagent gets. The pointer form keeps the capability's existence
and its blocking behaviour visible in that case; it loses the rule text. That is the honest
trade and should be a deliberate call, not an oversight.

Confidence: 92 (quoted both sides; injection co-location inferred from `hooks.json` matchers
plus `loop-hook-dispatch.md:29`, which I read).

---

### P1 — the banner is a stale copy: `favor` survived the en-GB sweep

`hooks/session-start.sh:34`:

```
... and favor efficiency over simplicity where they conflict.
```

`.gsd/capabilities/sota-numerics/fragments/executor-numerics.md:4`:

```
Where efficiency and simplicity conflict, favour efficiency and speed, per this project's own
priority order.
```

Commit `3e9fa2e` ("docs: hold one spelling locale, en-GB") changed the fragment and missed the
banner. I grepped the whole tree for `favor|favour|behavior|behaviour|recognized|recognised|
honour|honor`: `session-start.sh:34` is the **only** en-US spelling left in shipped prose
(the rest — `behaviour`, `honours`, `recognised` — are all en-GB). This is the duplication
above producing its first drift, one commit after it was created.

Fix: it disappears with the previous finding. If the banner bodies stay, change `favor` →
`favour`.

Confidence: 96 (exact grep of the shipped tree, both lines quoted).

---

### P1 — `executor-numerics.md:7` is one 491-char sentence with a nested exception

```
Code an agent runs directly by hand is **quiet**: on success it prints a compact
machine-readable result or nothing at all; on failure it prints one line per problem and
exactly one line naming the fix, except for an input it cannot resolve at all, which gets one
diagnostic and no fix line because there is nothing to fix; it signals through its exit code
with no progress chatter; and when a result would flood the context window it writes the
result to a file and prints that file's path.
```

100 tok, 491 chars, one sentence, five semicolon-joined clauses, one mid-clause exception, and
a trailing causal ("because there is nothing to fix") the reader does not need. This is the
clearest one-idea-per-sentence violation in the corpus and the highest mis-parse risk: the
exception attaches to the *failure* clause but sits adjacent to the *exit code* clause.

Rewrite (measured 88 tok, −12, and four short sentences instead of one long one):

```
Code an agent runs directly by hand is **quiet**. On success it prints a compact
machine-readable result, or nothing. On failure it prints one line per problem plus exactly
one line naming the fix; an input it cannot resolve at all gets the diagnostic and no fix
line. It signals through its exit code and prints no progress chatter. When a result would
flood the context window it writes the result to a file and prints that path.
```

The token saving is small; the parse-reliability gain is the point. Nothing breaks — the
content is identical.

Confidence: 95 (quoted exact, counted both).

---

### P1 — gate diagnostics are unbounded: 8,099 tok from one violation, probed

`check-alternatives.py:537-540`:

```python
        found = ", ".join(str(y) for y in years)
        issues.append(
            f"no citation dated within the last {RECENCY_WINDOW_YEARS} years (found: {found})"
        )
```

`years` comes from `entry_years(entry_text)`, and `entry_text` is `body[match.start():end]` —
the whole span from one bullet to the next, with no length cap. Every four-digit year in that
span is joined into the message.

Probed against the shipped script: a plan whose first bullet carries 2,000 out-of-window years
emits **12,280 chars / 8,099 tokens on a single stderr line**, exit 1. That flows straight
back to the orchestrator agent reading the gate output.

Second unbounded path, `check-alternatives.py:410-421`:

```python
    heading, tail = boundary
    ...
        f"; the section ended at the heading '{heading}' and what it needs is"
```

`heading` is `text[end:].split("\n", 1)[0].strip()` (`extract_section_body:407`). Under the new
setext branch of `NEXT_HEADING_RE` (`:107`, `^[ \t]{0,3}[^\s][^\n]*\n[ \t]{0,3}=+[ \t]*$`) the
boundary lands on a **paragraph** line, not a heading line, so the echoed text is an arbitrary
prose line. Probed with a 7,800-char paragraph above a `===` underline: **1,323 tokens on one
line**.

Everything else is bounded and fine, and worth saying: `validate_plan` returns exactly one
reason per plan (`:583` returns `issues[0]`, not all issues), the violation list is one entry
per file in the phase directory (`discover_plan_files:614-618`), and there is exactly one
`remediation:` line (`:667-670`). Measured on the real corpus — `.planning/phases/` holds 73
entries, 10 plan-shaped, max 5 in one directory — realistic worst case is 5 reasons (9–34 tok
each) + 21 tok remediation ≈ **170 tok**. The bound is the *content* of a reason, not the
count.

Fix, two lines:

```python
found = ", ".join(str(y) for y in sorted(set(years))[:5])
```
plus `heading[:80]` at `:415`. Caps the two unbounded emitters at ~40 tok each.

What breaks: an author with six distinct out-of-window years sees five. That is strictly better
than an 8k-token dump, and the fix line is unchanged.

Confidence: 95 (code quoted verbatim; both sizes produced by running the shipped script).

---

### P1 — `.claude-plugin/plugin.json:4` is a noun pile where the README already has the sentence

```
"description": "SOTA-research/numerical-stability advisory steering across gsd's
plan/execute/verify/ship lifecycle -- steering toward internal/project consistency,
unambiguity, completeness, efficiency, and agent-facing quiet code -- plus a blocking
plan:post gate that mechanically enforces a compliant Alternatives Considered section on every
plan in a phase"
```

69 tok, 345 chars, five abstract nominalisations in a row ("consistency, unambiguity,
completeness, efficiency"), and "steering" twice in one sentence. This is the first and often
only prose an installer or a plugin-search agent sees, and it describes the capability by its
adjectives rather than by what it does.

`README.md:3` already contains the right sentence and it is the best line in the release:

```
Make GSD compare mechanisms before execution, then keep numerical precision and measured
performance visible through shipping.
```

Rewrite (45 tok, −24):

```
Makes GSD compare mechanisms before execution and keeps numerical precision and measured
performance visible through shipping: four advisory prompts, plus a blocking plan:post gate
that requires a compliant Alternatives Considered section on every plan in a phase.
```

Confidence: 90 (both strings quoted, both counted; "installer reads this first" is from the
task brief, not verified against a host).

---

### P2 — `capability.json:6` ships a changelog line and a broken compound adjective

```
"description": "Advisory steering across gsd's plan/execute/verify/ship lifecycle toward SOTA
numerics: internally and project-consistent, unambiguous, complete, efficient, quiet-running,
agent-facing code -- plus the single blocking plan:post gate ... No new gate covers the added
dimensions."
```

Two defects. **"internally and project-consistent"** does not parse — the coordination splits a
hyphenated compound, so "internally" is left modifying nothing ("internally consistent and
project-consistent" is what is meant). **"No new gate covers the added dimensions."** is a
release note in a permanent manifest field: "added" relative to 0.1.3, a baseline no reader of
an installed 0.2.0 manifest has. It is stale on the day it ships. The same fact is stated
where it belongs — the four fragments each open by naming their own non-gating status
(`executor-numerics.md:1`, `verifier-precision.md:1`, `ship-precision-advisory.md:1`).

Fix (71 tok, −5): fix the compound, delete the last sentence.

Confidence: 92 (quoted exact; grammar judgement is mine).

---

### P2 — `planner-sota.md:1` spends 91 tok re-listing what lines 2–3 already require

```
SOTA-numerics research discipline for planning is advisory, except for the structure below: a
blocking plan:post gate mechanically checks the `## Alternatives Considered` section's shape,
its alternative count, citation syntax and year, and the `Decided by:` line, and blocks the
plan step when those are absent. Whether you actually consulted the sources, and whether the
comparison is any good, no gate can check — that part is yours.
```

The middle clause enumerates shape, count, citation syntax, year, `Decided by:` — every one of
which lines 2 and 3 then state as a requirement. The enumeration is a second copy at a
different altitude. The second sentence is the load-bearing half and should stay: it is the
only thing in the fragment that counters gate-gaming.

Rewrite (45 tok, −46):

```
A blocking plan:post gate checks the structure below and blocks the plan step when it is
absent. Whether you actually consulted the sources, and whether the comparison is any good, no
gate can check — that part is yours.
```

Confidence: 94.

---

### P2 — `ship-precision-advisory.md` states "advisory" twice in four lines

L1 (34 tok) "advisory only — this capability declares no gate at ship:pre; its only gate
already fired at plan:post." and L4 (23 tok) "note it for the record rather than blocking the
ship." L4 already tells the orchestrator the operational consequence, in imperative form; L1
states the same thing as background. L2 additionally packs two separate confirmations into one
347-char sentence with an em-dash aside wedged between them.

Rewrite of L1+L2 measured at 59 tok vs 102 (**−43 on a 154-tok fragment, 28% of it**):

```
Confirm every precision, efficiency, quiet-output, or legibility claim in this milestone's
SUMMARY.md files is backed by a measurement, a benchmark, or a cited source — not an unverified
adjective.
Confirm every claim that a change goes with the grain of project convention names the
convention it follows.
```

Nothing breaks: L4 keeps the non-blocking contract.

Confidence: 93.

---

### P2 — `executor-numerics.md:9-10` is the weakest 78 tok in the release, and it is unscoped

```
Agent-facing prose is **legible** when it is unambiguous and complete: keep each meaning in
exactly one place so a comment states why and the code states what, and delete any line the
reader would already honour by default.
Phrase every instruction as the target behaviour, give every completion criterion a bound the
reader can check, and keep a definition next to the caveats that qualify it.
```

Two problems. **Unscoped**: the **quiet** rule immediately above it gets an explicit boundary
(`:8` "This rule governs scripts, CLIs, test harnesses, and hooks an agent invokes; library
internals an agent never runs by hand are outside it"). **legible** gets none, so an executor
writing ordinary application code has no signal about whether "delete any line the reader would
already honour by default" applies to production comments. **No-op risk**: L10 is a restatement
of general prose-writing standards, and "keep a definition next to the caveats that qualify it"
is unlikely to change what a competent model already produces. L9's first clause (comment says
why, code says what) does change behaviour and should stay.

Rewrite, merging the two lines and adding the missing scope (68 tok, −10):

```
Agent-facing prose you write — comments, docs, and the instructions in agent-invoked scripts —
is **legible**: keep each meaning in one place so a comment states why and the code states
what, phrase instructions as the target behaviour, give every completion criterion a checkable
bound, and delete any line the reader would honour by default.
```

Confidence: 82 (text and counts exact; the no-op judgement is model-relative and, per the
rubric, settled by running it, not by argument).

---

### P2 — `verifier-precision.md:4` breaks the fragment's own sentence shape

L5, L6, L7 all follow one pattern: `Flag <class> that is not <adjective>: <a>, <b>, or <c>.`
L4 (68 tok, 367 chars) instead chains four heterogeneous `flag ...` clauses in one sentence:

```
Flag hardcoded constants standing in for a value that should be derived from first principles
or measured, flag superlative performance or overhead claims ("zero overhead", "negligible
error") that no benchmark or measurement in the diff backs up, flag an unreachable or unwritten
branch, and flag an argument whose accepted values are undocumented at its definition.
```

The last two clauses are the new 0.2.0 dimensions bolted onto a pre-existing sentence. Split
into two lines (measured 65 tok, −3) so the shape matches its neighbours:

```
Flag hardcoded constants standing in for a value that should be derived from first principles
or measured, and superlative performance or overhead claims ("zero overhead", "negligible
error") that no benchmark in the diff backs up.
Flag an unreachable or unwritten branch, and an argument whose accepted values are
undocumented at its definition.
```

Confidence: 93.

---

### P2 — `planner-sota.md:7` states one rule three ways

```
An entry passes the date check when at least one of its cited years falls inside the six-year
window; extra out-of-window years never fail it, and an entry whose every cited year is out of
window fails.
```

Clauses two and three are the logical complement of clause one. 81 tok for a rule that needs
~30. Rewrite (57 tok, −24) keeps clause one plus the actionable "So pair a canonical source
(Kahan summation, IEEE 754, a classic BLAS paper) with a current doc, release note, or
benchmark that supplies an in-window year."

Related, and worth noting rather than fixing: this same rule now exists in **five** places —
`planner-sota.md:7`, `NOTES.md:66-79` (243 tok), `README.md:150-152`, the script docstring
(`check-alternatives.py:5-7`), and the code comment at `:533-536`. `NOTES.md:78-79` is
explicitly aware of two of them ("If either is edited, update the other — they teach and
enforce one rule from two seats"), which is the right instinct, but three more copies exist
that the note does not name. Only `planner-sota.md`'s copy costs runtime tokens; the rest is
maintenance surface.

Confidence: 90.

---

### P2 — `planner-sota.md:4` closes on a no-op, and 96 tok goes to an optional branch

Final sentence:

```
Mechanism entries outside that exact subsection retain every citation, date, count, and
`Decided by:` requirement.
```

That is the default already established by lines 2 and 3; it changes nothing. The line is
96 tok / 504 chars total and describes the `### Internal design alternatives` escape hatch,
which most plans never use — the rubric's disclosure candidate, except a flat injected fragment
has nowhere to disclose to, so it is a flat per-planner-spawn cost. Dropping the closing
sentence and the "including a bare `###`" parenthetical: 65 tok, **−31**.

Confidence: 88.

---

### P2 — `planner-sota.md:5` restates its own instruction as a prohibition

```
... may write `N/A — no mechanism choice` as the entire section body instead of fabricating a
comparison — do not invent alternatives to satisfy the gate when none genuinely exist.
```

"instead of fabricating a comparison" and "do not invent alternatives to satisfy the gate" are
the same instruction, the second in negated form. Per the rubric, negation is the weaker
modifier and drags the forbidden behaviour into context; the positive form is already present.
Cutting the trailing clause: 39 tok, **−14**.

Same pattern, weaker case, at `:8` ("do not pad the section with alternatives that are
obviously worse"). That one I would keep — padding is a real, frequent failure mode and I do
not see a positive phrasing that carries the same force.

Confidence: 88.

---

### P2 — `capability.json:88` and `NOTES.md:6-21` argue the same point at two lengths

The gate's `description` field is a 106-tok / 491-char paragraph defending `onError: "halt"`.
`NOTES.md` §1 (265 tok) makes the same argument at 2.5× the length, down to the same closing
imperative — `capability.json:88` "Do not \"fix\" this back to \"skip\"." vs `NOTES.md:20-21`
"Do not \"fix\" `gates[0].onError` back to \"skip\" to match the contributions."

Neither is injected into an agent prompt, so the cost is maintenance and one-time-read, not
per-spawn. But it is two authoritative statements of one decision, and a future editor sees
only whichever they open. Keep the manifest copy — it sits at the point of edit — and reduce
`NOTES.md` §1 to the one thing it adds that the manifest does not: the contrast with
`contributions[].onError: "skip"`. Saves ~200 tok of `NOTES.md`, which ships in the bundle.

Confidence: 90 (both quoted; "not injected" verified against `capability.json`'s
`contributions[]`, which lists four fragments and no notes file).

---

### P2 — `check-alternatives.py` module docstring: 374 tok, one 5-clause sentence

`:15-19`:

```
Exit 2 = usage/IO error: an empty, missing or non-directory phase_dir, a phase_dir with no
`.planning/` ancestor within 10 levels, a discovered plan file that is not valid UTF-8, or --
when no phase_dir is given -- a STATE.md whose frontmatter `current_phase` and
`## Current Position` `Phase:` line do not corroborate each other.
```

One sentence, ~70 words, five conditions, with a nested "-- when no phase_dir is given --"
aside that scopes only the fifth. A reader parsing linearly attaches the aside to the whole
list. Fix: put the exit-2 conditions on their own lines and move the conditional out front of
the clause it governs. No token change worth reporting; the parse risk is the defect.

The two long comment blocks (`:42-67`, 417 tok; `:80-104`, 435 tok) I am **not** flagging.
Every paragraph in them records a measured failure and its direction — "Measured before this
predicate: a `===` rule between two compliant entries reported \"fewer than 2 named
alternatives (found 1)\"" — which is exactly the rubric's *cache*: knowledge an agent cannot
recover by looking at the code. At 46% prose the file is unusual, but this is a security-
relevant gate whose every regex bound was chosen against an observed false verdict, and the
rationale is the expensive part.

One aging number inside them, `:47-48`:

```
# Measured on this project's own corpus: 76 entries across its phase directories, 10
# plan-shaped, 0 of them misnamed.
```

I counted the live corpus: **73 entries, 10 plan-shaped**. The plan-shaped figure — the one the
bound depends on — still holds; the 76 has drifted in under a week. Commit `2c6466e` was
titled "stop asserting a count that ages" and did that job in `CHANGELOG.md`; this one was
missed. Either drop "76 entries across its phase directories" or date it the way `CHANGELOG.md`
now dates every count ("Measured at `253bbdc`").

Confidence: 94 (both counts run by me; the 10 matches exactly).

---

### P2 — auto-install refusals repeat per spawn, but probably never reach the model

`hooks/capability-auto-install.sh` has nine refusal messages, measured 24–39 tok each
(largest, `:158`, 39 tok / 181 chars). Frequency:

- The fast path (`:80`, `[ "$NEW_HASH" = "$OLD_HASH" ] && exit 0`) fires before every refusal,
  so an unchanged bundle is silent. Good design, and it is why this is P2 not P1.
- No refusal writes `STATE_FILE` (deliberate, `:93-94`). So a **persistent** refusal condition
  re-emits on every trigger indefinitely. Triggers per `hooks.json`: `SessionStart`
  (`startup|resume|clear|compact` — note `compact`, so it re-fires after every compaction)
  plus every `gsd-planner` / `gsd-executor` / `gsd-verifier` spawn. On the worked phase that
  is 10 spawns → 240–390 tok of the same sentence, and it never stops.
- The realistic trigger is documented at `README.md:58`: running the test suite leaves
  `__pycache__/` inside the bundle, which `--ignored` catches. A developer who runs the tests
  once gets this on every subagent spawn until they delete it. (`.pytest_cache/` and
  `tests/__pycache__/` are both present in this worktree right now.)

Mitigating: every message goes to **stderr** and the script always `exit 0`. Claude Code feeds
hook stderr to the model on a blocking exit code, not on 0, so these most likely never enter a
context window at all — the cost is user-visible noise, and the real hazard is the inverse
(the agent never learns the capability is uninstalled). Only the success line reaches stdout
and therefore context: `:235` `Auto-installed capability: sota-numerics (user scope)` = 14 tok,
once per hash change. That one is correctly sized.

Fix: write a *refusal* sidecar (distinct from `STATE_FILE`) keyed on `NEW_HASH` + refusal
reason, and stay silent when the same refusal repeats for the same hash. Preserves the retry
semantics `:93-94` wants — a new hash re-emits — and caps a permanent condition at one message.

Confidence: 88 on the counts and frequency (all quoted from the script and `hooks.json`); 65 on
the stderr-not-in-context claim, which is inferred from Claude Code hook semantics I did not
verify against this host.

---

## Did the added dimensions buy their cost?

Per-phase runtime cost of the release is **+1,855 tok** (3,057 → 4,912 on a 3-wave/6-plan
phase). Breaking the +296 fragment growth down by dimension:

| dimension | where | tok | verdict |
| --- | --- | ---: | --- |
| **go with the grain** | `planner:10` 48, `verifier:7` 45, `ship:2` ~20 | ~113 | **Bought it.** Well-chosen leading word — pretrained, one token, reused across three roles with consistent meaning. `planner:10` gives it a checkable bound ("a reader cannot tell from the code which file is new"); `verifier:7` gives three concrete instances. This is the model the other additions should follow. |
| **complete / unambiguous** | `executor:5` 49, `verifier:4` ~25 | ~74 | **Bought it.** Three concrete, checkable obligations (every reachable branch written, every argument defined, no silent default). Behaviour-changing, not restatement. |
| **quiet** | `executor:7` 100 + `executor:8` 31, `verifier:5` 37, `ship:2` ~15 | ~183 | **Bought it, at ~20% overpay.** The rule is real, checkable, and correctly scoped by `executor:8`. But `executor:7` is the single worst-parsing sentence in the release, and its cost is paid on *every* executor prompt for a rule that fires only when the executor writes agent-invoked code. Fix the sentence (P1 above); the presence is justified. |
| **legible** | `executor:9` 46 + `executor:10` 32 | 78 | **Did not buy it as written.** Unscoped where its neighbour **quiet** is scoped, and `executor:10` restates general prose standards a competent model largely already follows — the highest no-op risk in the corpus. Merge and scope it (P2 above) or cut `executor:10` outright. |

The framing cost is where the release actually leaks. `planner:1` (91), the three "advisory
only" preambles (`executor:1` 28, `verifier:1` 36, `ship:1` 34), and the three SubagentStart
banner bodies (90 + 37 + 49) come to **365 tok of meta-commentary about whether the rules
bind** — more than the 296 tok of new rules the release adds. That is the finding I would act
on first.

---

## Reductions, itemised

| # | site | cut | tok saved | per what | breaks |
| --- | --- | --- | ---: | --- | --- |
| 1 | `session-start.sh:33-36` | role bodies → pointer | 90 / 37 / 49 | per planner / executor / verifier spawn | steering text lost if a fragment fails to render |
| 2 | `planner-sota.md:1` | drop the re-enumeration | 46 | per planner spawn | nothing |
| 3 | `planner-sota.md:4` | drop closing no-op + parenthetical | 31 | per planner spawn | nothing |
| 4 | `planner-sota.md:7` | one statement, not three | 24 | per planner spawn | nothing |
| 5 | `planner-sota.md:5` | drop the negated restatement | 14 | per planner spawn | nothing |
| 6 | `ship-*.md:1-2` | fold L1 into L4; split L2 | 43 | per ship:pre | nothing |
| 7 | `executor-numerics.md:7` | four sentences, not one | 12 | per executor prompt | nothing (parse gain is the point) |
| 8 | `executor-numerics.md:9-10` | merge + scope | 10 | per executor prompt | nothing |
| 9 | `verifier-precision.md:4` | split to match L5–L7 shape | 3 | per verifier spawn | nothing |
| 10 | `plugin.json:4` | use `README.md:3`'s sentence | 24 | install-time only | nothing |
| 11 | `capability.json:6` | fix compound; drop changelog line | 5 | install-time only | nothing |
| 12 | `check-alternatives.py:537,415` | cap `found` at 5, `heading` at 80 ch | up to **8,059** | per gate failure, worst case | author sees 5 of >5 out-of-window years |
| 13 | `NOTES.md:6-21` | point at `capability.json:88` | ~200 | bundle size / one-time read | nothing |

Fragment + banner total on the worked phase (3 waves × 2 plans):
`4,912 → 4,148 tok`, **−764 (−16%)**, with no rule removed except `executor-numerics.md:10`.

Gate output on the same phase: bounded ~170 tok today in the normal case, capped at ~200 tok
worst case after #12, down from an 8,099-tok single line that I produced by running the shipped
script.
