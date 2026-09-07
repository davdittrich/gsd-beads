# PONYTAIL LADDER review — davdittrich/sota-numerics `feat/extended-sota-definition`

Worktree `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, HEAD `1de851c`.
Read: all 35 tracked files. Scope: over-engineering only — correctness/security/perf routed elsewhere.

## Standing measurements

| file | total | comment lines | code lines |
| --- | ---: | ---: | ---: |
| `hooks/capability-auto-install.sh` | 244 | 135 (55%) | 94 |
| `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` | 675 | 109 `#` + ~130 docstring | ~380 |
| `tests/test-capability-auto-install.sh` | 893 | 330 (37%) | 510 |
| `tests/test_check_alternatives.py` | 1515 | 144 | ~1300 |

Test:implementation line ratio is 2408:919 = **2.6:1**.

## What I will NOT recommend cutting (checked, load-bearing)

- The eight refusal branches in `capability-auto-install.sh`. This bundle installs at
  `--scope global`; a guard that answers "safe" when it could not measure would publish an
  uncommitted worktree machine-wide. Every `exit 0` after an `echo ... >&2` is fail-closed and
  every one writes no `STATE_FILE` so the next session retries. Do not thin these.
- `unverifiable_repo()`'s `[ ! -e "$_g/HEAD" ]` refinement (`hooks/capability-auto-install.sh:120`).
  It looks like a speculative special case; it is not. Case A3 pins the reason: a stray empty
  `/tmp/.git` would otherwise refuse every bundle unpacked under `/tmp`, "this suite included".
- `[[ "$CAP_ID" =~ ^[a-z][a-z0-9-]*$ ]]` (`:17`) — input validation before path construction.
- The three-rung `SOTA_SCRIPT` chain in `capability.json`. `test-gate-script-resolution.sh` case5
  pins all three shapes (monorepo, non-Git, absent-copy). No rung is dead.
- `mask_fenced_regions` and friends. stdlib has no CommonMark reader, and adding one to blank
  two constructs is a heavier answer than the 24 lines it replaces. Ladder rung 7, correctly reached.

---

## P1 findings

### P1-1 `delete:` D0 doc-parity case is a Python program inside a heredoc inside a shell test

`tests/test-capability-auto-install.sh:794-889` (96 lines: 22 comment, 74 code).

```sh
REPO_ROOT_D0="$(cd "$(dirname "$0")/.." && pwd)"
d0_report="$(python3 - "$REPO_ROOT_D0" "$CAP_ID" <<'PYEOF'
import re, sys, pathlib
...
for i, line in enumerate(lines):
    if line.startswith("| It refuses when |"):
        for row in lines[i + 2:]:
            if not row.startswith("|"):
                break
            readme_rows.append(row)
        break
else:
    problems.append("README.md has no table headed '| It refuses when |'")
```

A bash test shells to Python to hand-parse a Markdown table, to set-compare its third-cell code
spans against `echo` strings grepped out of the hook. Then 20 more lines of bash to demux
`D0-PROBLEM:`/`D0-TOTAL:` lines back out, plus a comment explaining why `read` is used instead of
`set --`. Three languages and a private wire protocol for one assertion.

The comment names the real defect honestly: *"the hook grew from five refusals to eight while
README and CHANGELOG were being written against it"*. That is the **forward** direction only.
Equality-in-both-directions, the duplicate check, and the header-anchoring are the speculative half.

Lazier — same forward guarantee, no Python, no protocol:

```sh
# D0: every refusal the hook emits is documented in README's table
grep -o 'capability-auto-install: [^"]*; refusing to install it at global scope' "$HOOK" |
  sed 's/^capability-auto-install: //; s/; refusing.*//; s/\$CAP_ID/'"$CAP_ID"'/g' |
  while IFS= read -r _m; do
    grep -qF "$_m" "$REPO_ROOT/README.md" || fail "D0: README does not document refusal: $_m"
  done
pass "D0: every hook refusal appears in README"
```

Net: **-90 lines**. Confidence 92 (quoted exact code; the 6-line replacement is written not measured).

### P1-2 `delete:` the same rationale is written twice or three times — comment, test comment, NOTES.md

The strongest evidence is verbatim-adjacent triplication of the boundary rationale.

`check-alternatives.py:85-88`:
> `# Deliberately not `#{1,6}`: `### Internal design alternatives` is an`
> `# in-section construct, so bounding on H3 would cut the body short and drop`
> `# the `Decided by:` line that follows it.`

`tests/test_check_alternatives.py:576-579` says the same thing again:
> `is a documented in-section construct, so widening the boundary scan to`
> ``#{1,6}` would truncate the body at that H3 and drop the `Decided by:``
> `line following it.`

Same pattern for the setext rule — `check-alternatives.py:95` *"A bare `=+` run with no preceding
text line is a horizontal rule, not a heading"* vs `tests/test_check_alternatives.py:626`
*"`===` with nothing above it is a horizontal rule, not a heading"*; and for the thematic break —
`check-alternatives.py:102` vs `tests/test_check_alternatives.py:620`, both spelling out
"thematic break AND a frontmatter fence".

Same in the shell pair. `hooks/capability-auto-install.sh:177-180`:
> `# What this still cannot see: a `.gitattributes` clean filter maps edited`
> `# worktree bytes onto the committed blob ... (gsd-beads-5yy).`

`tests/test-capability-auto-install.sh:39-44` repeats it, ticket number and all. And
`hooks/capability-auto-install.sh:165-175` prose-lists the four `status` flags that
`tests/test-capability-auto-install.sh:26-31` already tabulates against case IDs.

The capability's own `verifier-precision.md` fragment ships the rule this violates: *"Flag prose
that is not legible: a comment restating what the code already says"* — and `planner-sota.md`:
*"keep each meaning in exactly one place"*.

Lazier: where a test pins the behaviour, the test is the record — it is executable and the comment
is not. Collapse each code-side block to one line naming the case:

```python
# Not `#{1,6}`: H3 is in-section (`### Internal design alternatives`). Pinned:
# TestSectionBoundary.test_h3_does_not_end_the_section.
```

```sh
  # Each option states what this question needs rather than inheriting the repo's config.
  # Flag -> case map and the .gitattributes residual: see tests/test-capability-auto-install.sh header.
```

Concretely deletable, keeping one pointer line each:
`check-alternatives.py` L42-67 (26), L80-104 (25), L144-157 (14), L198-220 (23), L330-356 (27) = 115 → ~30.
`capability-auto-install.sh` L36-50 (15), L90-113 (24), L135-152 (18), L161-183 (23), L193-204 (12) = 92 → ~22.

Net: **-155 lines** (-85 checker, -70 hook). Confidence 90 (all quotes exact; the split between
"pinned by a test" and "only recorded here" was checked case by case, not exhaustively).

### P1-3 `delete:` a test that asserts a file contains its own docstring

`tests/test_check_alternatives.py:493-531`, `test_readme_and_planner_name_exact_mixed_contract`.

```python
        readme_text = (root / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Each parsed entry must contain:", readme_text)

        checker_text = (
            root / ".gsd/capabilities/sota-numerics/scripts/check-alternatives.py"
        ).read_text(encoding="utf-8")
        normalized_checker_text = " ".join(checker_text.split())
        self.assertIn(
            "at least two named mechanism alternatives", normalized_checker_text
        )
        self.assertIn(
            "Internal entries are excluded from the count and evidence validation.",
            normalized_checker_text,
        )
```

Three assertions, zero behaviour. The last two open `check-alternatives.py` to prove its own module
docstring still contains two phrases of its own prose — circular, and it makes any reword of a
docstring a red suite. `assertNotIn("Each parsed entry must contain:")` is a tombstone for a
sentence someone deleted; it can only ever fire if someone reintroduces that exact string.

The `marker`/`contract` two-file check (L501-516) is the part with a purpose — README and the
shipped planner fragment must teach one rule, per NOTES.md §5. Keep that, drop the rest:

```python
class TestDocumentedSyntax(unittest.TestCase):
    def test_readme_and_planner_name_exact_mixed_contract(self):
        root = Path(__file__).resolve().parent.parent
        contract = (
            "Internal entries need no external citation or date, do not count toward "
            "the two mechanism alternatives, and cannot lend evidence to a mechanism entry."
        )
        for path in (root / "README.md",
                     root / ".gsd/capabilities/sota-numerics/fragments/planner-sota.md"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("### Internal design alternatives", text, path)
            self.assertIn(contract, text, path)
```

The `control, _ = bullet_plan()` smoke run at L494-498 is also redundant — `test_bullet_control_remains_accepted`
(L741) and `TestSupportedEntryShapes.test_table_accepts_same_semantics_as_bullets` both assert it.

Net: **-25 lines**. Confidence 94 (quoted exact code; the two-file check's purpose traced to NOTES.md §5).

---

## P2 findings

### P2-4 `shrink:` `validate_entry` builds a list to hold exactly one string, and the caller reads `[0]`

`check-alternatives.py:520-545` and `:580-583`.

```python
    if issues:
        return [f"alternative '{name}': {'; '.join(issues)}"]
    return []
```
```python
    for name, entry_text in mechanism_entries:
        issues = validate_entry(name, entry_text, today_year)
        if issues:
            return issues[0]
```

The list is a one-element container built to be immediately unwrapped. The docstring *"Return a
list of issue strings for one alternative entry (empty = pass)"* documents a plurality that never
reaches the caller.

```python
def validate_entry(name, entry_text, today_year):
    """Return a violation reason for one alternative entry, or None."""
    issues = []
    ...
    return f"alternative '{name}': {'; '.join(issues)}" if issues else None
```
```python
    for name, entry_text in mechanism_entries:
        reason = validate_entry(name, entry_text, today_year)
        if reason:
            return reason
```

Net: **-4 lines**. Confidence 95 (exact code, both sides).

### P2-5 `yagni:` two single-expression helpers with one caller each

`check-alternatives.py:499-504`.

```python
def entry_has_citation(entry_text):
    return bool(URL_RE.search(entry_text) or DOC_REF_RE.search(entry_text))


def entry_years(entry_text):
    return [int(m.group(0)) for m in YEAR_RE.finditer(entry_text)]
```

Both are called exactly once, ten lines below, inside `validate_entry`. Inline:

```python
    if not (URL_RE.search(entry_text) or DOC_REF_RE.search(entry_text)):
        issues.append("missing URL or doc-ref citation")
    years = [int(m.group(0)) for m in YEAR_RE.finditer(entry_text)]
```

`entry_placeholder_violation` stays — it has a loop and a real docstring.

Net: **-8 lines**. Confidence 95 (call sites confirmed by reading the whole module).

### P2-6 `shrink:` two entry parsers and a precedence rule where one scan would do

`check-alternatives.py:433-496` (64 lines) plus `TABLE_SEPARATOR_RE` at `:119-121`.

Bullets are parsed first; if fewer than two mechanism bullets survive, a second engine
reconstructs the body line-by-line with `raw_lines` / `lines` / `line_starts` offset bookkeeping,
detects a separator row, validates the header above it, then walks rows — and the H3 `transitions`
walk is written twice, once per engine (L452-454 and L489-494).

```python
    mechanism_bullets = [entry for entry in bullet_entries if not entry[2]]
    if len(mechanism_bullets) >= MIN_ALTERNATIVES:
        return bullet_entries
```
```python
    return entries or bullet_entries
```

That produces the contract README states at L125: *"Bullets and table rows are fallback formats,
not additive"*. Nobody asked for that rule; it fell out of having two engines. A bullet line starts
`-`/`*` and a row starts `|`, so the two shapes cannot collide — one alternating scan collects both
and tags internal once:

```python
ENTRY_RE = re.compile(r"^[ \t]*(?:[-*][ \t]+|\|[^\n]{0,500}?)\*\*(.{1,200}?)\*\*", re.MULTILINE)
```

then the existing bullet loop, unchanged, over `ENTRY_RE.finditer(body)`. `TABLE_SEPARATOR_RE`,
`line_starts`, the header lookback and the second transitions walk all go.

**Cost, stated honestly:** this changes the contract, not just the code. Three tests pin the
current behaviour — `test_two_bullets_override_valid_table`, `test_one_bullet_selects_valid_table`,
`test_pipe_rows_without_separator_are_not_a_markdown_table` — and README:125 documents it. This is
a P2 because it is a "should this contract exist" question for the author, not a free deletion.
If the answer is "keep the contract", the two transitions walks should still be factored into one.

Net: **-39 lines** (64 → ~28, minus 3 for `TABLE_SEPARATOR_RE`). Confidence 78 (exact code read;
the merged regex is proposed, not run).

### P2-7 `delete:` CHANGELOG narrates its own revision history

`CHANGELOG.md:20-22`.

```
Counts here name the commit they were measured at, because every earlier
revision of this paragraph went stale within hours of being written and one
shipped a fix that did not exist.
```

The `Measured at 253bbdc` in the paragraph above already says the commit. This is process
confession addressed to the authors, shipped to consumers.

Net: **-3 lines**. Confidence 96 (exact quote).

### P2-8 `delete:` redundant bullet control test

`tests/test_check_alternatives.py:741-747`, `test_bullet_control_remains_accepted` writes
`bullet_plan()` and asserts exit 0. `test_table_accepts_same_semantics_as_bullets` (L683) already
asserts `bullet_result.returncode == 0` on the same fixture six methods above, and
`TestMixedCompatibility` asserts it again.

Net: **-6 lines**. Confidence 88 (all three read; no mutant needs the third).

### P2-9 `shrink:` `find_project_root` is walked twice on the gate's own code path

`check-alternatives.py:608-610`.

```python
    # Called for its raise, not its result: it rejects a phase_dir sitting
    # outside any GSD project.
    find_project_root(phase_dir_path)
```

On the no-argument path (the only one the gate uses), `resolve_current_phase_dir` already called
`find_project_root` at L221 and the result is discarded. Move the guard into `main()`'s explicit-arg
`else` branch (L648-649), where it is the only branch that needs it.

Net: **-3 lines**, one fewer filesystem walk per gate run. Confidence 85 (control flow traced end
to end; both call sites read).

---

## Total

**net: -333 lines possible.**
(-294 if P2-6 is rejected as a contract change rather than a simplification.)

Three highest-value deletions:

1. **-155** — P1-2, delete the code-comment copies of rationale that a test comment or NOTES.md
   already carries (`capability-auto-install.sh` 5 blocks, `check-alternatives.py` 5 blocks).
   Biggest single win, zero behaviour change, and it is the capability's own shipped rule.
2. **-90** — P1-1, replace the 96-line embedded-Python D0 doc-parity case with a 6-line grep loop
   that keeps the only direction that ever went stale.
3. **-85** — the `check-alternatives.py` half of P1-2 on its own, if the hook is left alone:
   115 comment lines guarding five regex constants collapse to ~30.
