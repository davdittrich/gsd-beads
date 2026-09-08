# Phase 24 Plan 08: Disposition Ledger

Every review thread on pull request #4 (`davdittrich/sota-numerics`) and every finding in
`REVIEW-CRITICAL-FINAL.md`, `REVIEW-PONYTAIL-FINAL.md`, `REVIEW-AGY-FINAL.md`, and
`REVIEW-PROSE-TOKENS.md`, given a disposition: **fixed**, **declined**, or **tracked**. No row
was closed by assertion alone — each names the commit, live re-verification, or existing test
that settled it. Counts and thread state were re-queried live against the GitHub API and the
worktree on 2026-09-08, not taken from any prose in this phase's context or earlier summaries.

## Part 1 — Pull request #4 review threads

Live query (`gh api graphql`, `reviewThreads`) on 2026-09-08 found **12 threads, 7 already
resolved on GitHub, 5 unresolved** — the context file's "roughly eight" was explicitly a
starting point, not the answer; the live count matched the phase context's separately-stated
12/7/5 breakdown exactly. All 12 now carry a disposition below; the 5 that were unresolved were
each replied to and resolved via the GitHub API as part of this plan (reply URLs recorded).

| # | Thread | File:line | Status before | Disposition | Evidence |
|---|--------|-----------|---------------|-------------|----------|
| 1 | Apostrophe-terminated `${PHASE_DIR}` splice | `capability.json:81` | unresolved | **declined (stale)** | `capability.json`'s gate command carries no `${PHASE_DIR}` token at all — Phase 23 already removed the splice; the script resolves its own phase from `STATE.md` (D-13/D-14). `tests/test-gate-script-resolution.sh` case3 exercises an apostrophe-containing phase directory name end-to-end today and asserts exit 0. Replied + resolved: https://github.com/davdittrich/sota-numerics/pull/4#discussion_r3956617840 |
| 2 | Executor banner failure-cardinality wording | `fragments/executor-numerics.md:8` | resolved (GH) | **resolved-on-pr** | Already closed by CodeRabbit before this plan ran; not re-litigated. |
| 3 | Publication guarantee vs untracked-bundle behavior | `README.md:48` | resolved (GH) | **resolved-on-pr, spot-verified** | Current wording ("where none tracks it, there is nothing to check against and the bytes install unverified") already states the caveat precisely; matches AGY's own downgrade of this from P0 to P2 as "disclosed, not a false claim." |
| 4 | D0 result parsed with `read` | `tests/test-capability-auto-install.sh:613` | resolved (GH) | **resolved-on-pr** | File is outside 24-08's bounded scope; GitHub's resolution predates this plan and is accepted as-is. |
| 5 | Non-apostrophe cases must assert `rc=0` | `tests/test-gate-script-resolution.sh:100` | unresolved | **declined (superseded)** | Current case3 loop already requires `rc -eq 0` for every case including apostrophe (which used to exit 2 and now correctly exits 0, the underlying D-13/D-14 fix) — stronger than the ask, no case exempted. Replied + resolved: https://github.com/davdittrich/sota-numerics/pull/4#discussion_r3956618160 |
| 6 | current_phase read not bounded to frontmatter | `capability.json:81` (data integrity) | resolved (GH) | **resolved-on-pr** | Superseded by the frontmatter-exactly-one-match fix (D-04, commit `e1818c5`). |
| 7 | Separate plan violations from operational errors | `fragments/executor-numerics.md:8` | resolved (GH) | **resolved-on-pr** | Out of scope; accepted as resolved. |
| 8 | Limit enforcement claim to structural checks | `fragments/planner-sota.md:2` | resolved (GH) | **resolved-on-pr** | Out of scope; accepted as resolved. |
| 9 | Trailing `\r` on setext boundary (CRLF) | `check-alternatives.py:61` | unresolved | **declined (unreachable)** | Reproduced: in isolation `NEXT_HEADING_RE`'s setext branch does fail to match `=+\r\n`. But `validate_plan()` reads every plan via `Path.read_text(encoding="utf-8")`, which performs universal-newline translation and normalizes all `\r\n` to `\n` before any regex sees the text. Full-pipeline reproduction (CRLF plan, donating setext heading) correctly exits 1, matching REVIEW-CRITICAL-FINAL's own note ("CRLF plans pass correctly, probed"). Replied + resolved: https://github.com/davdittrich/sota-numerics/pull/4#discussion_r3956618452 |
| 10 | Bound current_phase read to frontmatter block | `check-alternatives.py:90/94` | resolved (GH) | **resolved-on-pr** | Superseded by D-04's fix, same as #6. |
| 11 | Label the 68-test suite as a subset of 76 | `CHANGELOG.md:10` | unresolved | **fixed** | Plan 24-06 (commit `e7179dd`) removed all hand-maintained pass/fail counts from CHANGELOG.md entirely (D-09) — the entry now names the commit it was measured at and enumerates categories without a number. Verified 2026-09-08: no `68`/`76`/count string remains. Replied + resolved: https://github.com/davdittrich/sota-numerics/pull/4#discussion_r3956618695 |
| 12 | Reject duplicate `current_phase` fields | `check-alternatives.py:157` | unresolved | **fixed** | Plan 24-03 (commit `e1818c5`, D-04): `resolve_current_phase_dir`'s frontmatter branch uses `STATE_CURRENT_PHASE_RE.findall()` and requires exactly one match, raising the same error on zero or multiple matches — matches the suggested patch almost verbatim. Covered by `TestCurrentPhaseResolution`. Replied + resolved: https://github.com/davdittrich/sota-numerics/pull/4#discussion_r3956618992 |

Live re-query after the replies above: **12/12 threads resolved, 0 unresolved.**
`gh pr view 4` head: `f1fb8304113a172bf0f97149b70d3d494c6bd457` (pushed during this plan; see Part 3).

## Part 2 — Internal review findings

### REVIEW-CRITICAL-FINAL.md

| Finding | Disposition | Evidence |
|---|---|---|
| P0-1 — `hooks/session-start.sh`/`hooks/gsd-tools.sh` unconditional code exec from caller's cwd | **fixed** | Plan 24-05 (commits `55c44e7`, `6b61d4b`, D-13/D-14): `gsd-tools.sh` now resolves via `${CLAUDE_PLUGIN_ROOT}` then `BASH_SOURCE[0]`'s own location, never `git rev-parse --show-toplevel` of the caller's cwd; `capability.json`'s gate command dropped the enclosing-repository rung entirely. Verified 2026-09-08 by reading both files. |
| P1-1 — indented-code-block and nested-bullet count-invariant fail-opens | **fixed** | Plans 24-01/24-03 (D-01, D-02, D-03; commits `c6a52a2`, `2321b74`, `14307c0`): `mask_indented_code_blocks`, frontmatter masking, and `BULLET_RE`/`TABLE_ROW_RE` bounded to `[ \t]{0,3}` (CommonMark's own top-level range). 8 new regression tests. |
| P1-2 — CHANGELOG's measured comparison stale two commits after being written | **fixed** | Plan 24-06 (commit `e7179dd`, D-09): all hand-maintained counts deleted; entry now names the commit and enumerates categories. |
| P1-3 — README/CHANGELOG's `__pycache__` failure mode is unreachable via the test suite | **fixed** | This plan (commit `c8c8a1b`): reproduced the claim is false (subprocess-invoked script never bytecode-caches itself); reproduced the true mechanism (`python3 -m check-alternatives` does); rewrote both files' wording. |
| P1-4 — blocking gate's dispatch conditioned on `gap-analysis`'s `workflow.post_planning_gaps` key, unrecorded | **fixed** | Plan 24-06 (commit `7c77ea9`): NOTES.md residual entry added naming the key and tracking ticket `gsd-beads-h1pb` (verified open). |
| P1-5 — PR #4 eleven commits behind local HEAD, four of them gate fixes (D-26 breach) | **fixed** | This plan: `git push origin feat/extended-sota-definition` (`e3d253a..f1fb830`); `gh pr view 4` now reports `headRefOid` == local HEAD. |
| P2-1 — backticked `<!--` blanks the rest of the plan (false block, fail-closed) | **tracked** | `gsd-beads-25vc.21.1`. In-scope file, but the correct fix (backtick-span-aware comment detection) is non-trivial and this is a fail-closed diagnostics defect, not a bypass; deferred rather than rushed. |
| P2-2 — `Decided by:` inside `### Internal design alternatives` satisfies the requirement | **declined** | Attempted the suggested fix (mask internal H3 spans before `DECIDED_BY_RE.search`); it broke 5 existing tests (`TestMixedAlternatives.test_mixed_bullets_exits_0`, `test_mixed_table_exits_0`, `test_internal_bullets_do_not_suppress_mechanism_table`, `TestDocumentedSyntax.test_documented_mixed_body_exits_0`, `TestMixedCompatibility.test_exact_marker_allows_trailing_horizontal_whitespace`). The project's own tested contract already permits a `Decided by:` line physically after an unterminated internal H3; README.md:145 and planner-sota.md:4 only require citations/dates/counts stay outside the internal subsection, not the `Decided by:` line itself. Reverted the fix; disposition is decline, not silent drop. |
| P2-3 — `${GSD_HOME:-$HOME}` with both unset resolves the third rung to `/` | **fixed** | This plan (commit `c8c8a1b`): added case2b to `tests/test-gate-script-resolution.sh`, confirming fail-closed (exit 1) behavior with both env vars unset. |
| P2-4 — NOTES.md pins gsd-core line numbers that will drift across point releases | **fixed (mitigated)** | Plan 24-06 (commit `7c77ea9`): NOTES.md now states "Both positions re-derived 2026-09-08 against the installed gsd-core 1.13.0, not assumed from an earlier note" — the staleness risk this finding cared about (silent drift) is closed by explicit version+date disclosure, even though line numbers remain. |
| P2-5 — capability's own "quiet" rule not applied to its own hooks (banner duplication) | **declined** | Out of scope (`hooks/session-start.sh`); the review itself states "D-19 exempts `hooks/*.sh` from prose refactor, so this is a note, not a required change." |
| P2-6 — `tests/.planning/.gitkeep` is vestigial | **declined** | Out of scope test fixture; the review itself states "flagging, not deleting." |

### REVIEW-PONYTAIL-FINAL.md

| Finding | Disposition | Evidence |
|---|---|---|
| P1-1 — D0 doc-parity check: 96-line embedded Python replaceable by a 6-line grep loop (-90 lines) | **tracked** | `gsd-beads-25vc.21.4`. File (`tests/test-capability-auto-install.sh`) outside 24-08's bounded scope. |
| P1-2 — rationale duplicated verbatim across code comment/test comment/NOTES.md (-155 lines) | **tracked** | `gsd-beads-25vc.21.4`. Spans out-of-scope files. |
| P1-3 — circular test asserting check-alternatives.py's own docstring text (-25 lines) | **tracked** | `gsd-beads-25vc.21.4`. File (`tests/test_check_alternatives.py`) outside 24-08's bounded scope. |
| P2-4 — `issues[0]` single-element list immediately unwrapped (-4 lines) | **tracked** | `gsd-beads-25vc.21.4`. In-scope file, but bundled with the related P2-5 for one coordinated pass rather than two more late-phase edits to production logic. |
| P2-5 — two single-use single-expression helpers inlineable (-8 lines) | **tracked** | `gsd-beads-25vc.21.4`. Same reasoning as P2-4. |
| P2-6 — bullet and table-row parsing mergeable into one scan | **declined** | The review itself frames this as "a P2 'should the contract exist' question for the author, not a free deletion" (three tests pin the current keep-both-when-mixed behavior; README:125 documents it). Author call: keep current shape. |
| P2-7 — CHANGELOG narrates its own revision history (-3 lines) | **fixed** | This plan (commit `c8c8a1b`): deleted the self-referential "the commit is named here... every earlier revision went stale" paragraph — a process note addressed to the authors, not useful to a shipped-changelog reader. |
| P2-8 — redundant `bullet_result.returncode` assertion | **tracked** | `gsd-beads-25vc.21.4`. File (`tests/test_check_alternatives.py`) outside scope. |
| P2-9 — `find_project_root()` called twice on the no-argument path (-3 lines, one fewer filesystem walk) | **tracked** | `gsd-beads-25vc.21.4`. In-scope file; bundled for the same coordinated pass as P2-4/P2-5. |

### REVIEW-AGY-FINAL.md

| Finding | Disposition | Evidence |
|---|---|---|
| CONFIRMED — indented-code-block bypass | **fixed** | Same as CRITICAL P1-1 (D-02). |
| P1 — YAML frontmatter never stripped, satisfies gate with no real section | **fixed** | Plan 24-01 (commit `2321b74`, D-01). |
| P2 — setext H2 (`---` underline) not a section boundary | **declined** | Intentional by design: code comment at `check-alternatives.py:120-124` explains `-` is deliberately never a boundary (it is simultaneously a setext H2 underline, a thematic break, and a frontmatter fence — treating it as a boundary would false-block a plan using a horizontal rule between alternatives). Pinned by `test_thematic_break_does_not_end_the_section`. |
| P2 — case-insensitive filesystem (macOS/Windows) `*-PLAN.md` glob gap | **tracked** | `gsd-beads-25vc.21.3`. Untestable on this project's Linux host; needs a macOS/Windows CI leg or an explicit accepted-risk note, both outside 24-08's scope. |
| P2 — symlinked phase directory escapes the `.planning` tree | **tracked** | `gsd-beads-25vc.21.1`. In-scope file, low impact (validates names, prints no content), deferred with the other check-alternatives.py hardening items rather than risked late. |
| P2 — directory named `NN-NN-PLAN.md` crashes with a raw traceback | **tracked** | `gsd-beads-25vc.21.1`. Attempted the fix (catch `OSError` alongside the existing `UnicodeDecodeError` handler); it produces a clean exit-2 message correctly, but breaks `tests/test_check_alternatives.py::TestUnreadablePlanFiles.test_directory_named_like_a_plan_exits_1`, whose docstring explicitly pins the current raw-traceback/exit-1 behavior as a known, accepted discrepancy. Reverted; needs a coordinated fix+test+doc update outside 24-08's scope. |
| REFUTED — ReDoS claim on `TABLE_ROW_RE` | **no action** | Already refuted by the reviewer (measured 1.9ms on a pathological 971-char input, linear growth). Not relayed as a defect. |
| CONFIRMED — `bundle_hash` forgeable via directory-name newline injection | **tracked** | `gsd-beads-25vc.21.2`. File (`hooks/capability-auto-install.sh`) outside 24-08's bounded scope. |
| capability install runs inline with no `timeout` | **tracked** | `gsd-beads-25vc.21.2`. Same file, same scope reason. |
| P2 — hash sidecar write follows symlinks | **tracked** | `gsd-beads-25vc.21.2`. Same file, same scope reason. |
| REJECTED — "eight distinct refusals" claim | **no action** | Already rejected by the reviewer (premise false; no quote found for "eight" anywhere in the docs; the actual count, 9, matches everywhere). |
| REJECTED — local `origin/main` forgery via `git update-ref` | **no action** | Real mechanism, but already disclosed in the same README paragraph; reviewer explicitly did not relay it as an undisclosed defect. |
| MY OWN FINDING P1 — `gsd-tools.sh` unverified provider resolution | **fixed** | Same as CRITICAL P0-1 (D-13). |
| P1 — README says `draft-PLAN.md` is ignored; gate actually blocks on it | **fixed** | Plan 24-07 (commit `cb6911a`, D-10): README.md:93 now correctly states a misnamed plan "is not ignored: it is collected as misnamed and reported as a violation." Verified 2026-09-08 by reading the live text and re-running the reviewer's own reproduction (scratch phase dir with only `draft-PLAN.md`, exit 1 with the misnamed-plan message). |
| CHANGELOG 94-test vs 97 stale | **fixed** | Same as CRITICAL P1-2 (D-09). |
| P2 — "only bytes repository records published" vs `.gitattributes` clean-filter gap | **declined** | Current README wording already states the caveat precisely; reviewer itself downgraded this from P0 given the disclosure. |
| P2 — CHANGELOG:89's refusal tabulation doesn't cover the silent exit-0 paths | **declined** | Reviewer's own assessment: "pedantic but literally true" — README:68 already covers the hash-tool case in prose. |
| REJECTED — `URL_RE` 1–300 char claim | **no action** | Already rejected by the reviewer. |
| REJECTED — NOTES.md exit-2 table "incomplete" claim | **no action** | Already rejected by the reviewer (table is introduced by "Measured:", not claimed exhaustive, and NOTES.md itself says "do not oversell that"). |
| REJECTED — capability.json description "marketing" claim | **no action** | Already rejected by the reviewer (it is the plugin description field; no falsified claim supplied). |
| `real_gsd_state()` doesn't catch a `__pycache__` bytecode leak into the real mirror | **tracked** | `gsd-beads-25vc.21.3`. File (`tests/test-capability-auto-install.sh`) outside scope; minor. |
| `hooks.json` `SubagentStart` wiring has zero test coverage | **tracked** | `gsd-beads-25vc.21.3`. File (`hooks/hooks.json`) outside scope. |

### REVIEW-PROSE-TOKENS.md

| Finding | Disposition | Evidence |
|---|---|---|
| P1 — SubagentStart banners restate fragment contributions verbatim (-535 tok/phase) | **tracked** | `gsd-beads-25vc.21.5`. File (`hooks/session-start.sh`) outside 24-08's bounded scope. |
| P1 — `favor` survived the en-GB spelling sweep | **fixed** | Plan 24-06 (commit `ae46ff1`, D-11). Verified 2026-09-08: `grep -rn favor\b` across `hooks/session-start.sh` and all four fragments returns nothing; both sites now read `favour`. |
| P1 — `executor-numerics.md:7`'s 491-char, five-clause, one-sentence quiet rule | **tracked** | `gsd-beads-25vc.21.5`. Fragment file outside scope. |
| P1 — gate diagnostics unbounded (8,099 tok on one stderr line) | **fixed** | Plan 24-04 (D-07/D-08, commits `eb8dd19`/`ce146d0`/`1cb14d9`/`57079cf`): `elide_span`/`elide_line` bound every document-derived quoted span to 80 chars and every printed line to 200 chars. Verified 2026-09-08: both functions present in the live script. |
| P1 — `plugin.json:4`'s noun-pile description | **tracked** | `gsd-beads-25vc.21.5`. File (`.claude-plugin/plugin.json`) outside 24-08's bounded scope. |
| P2 — `capability.json:6`'s broken compound adjective and stale "No new gate" sentence | **fixed** | This plan (commit `c8c8a1b`): "internally and project-consistent" → "internally consistent and project-consistent"; deleted the release-note-in-a-permanent-field sentence. |
| P2 — `planner-sota.md:1` re-lists what lines 2–3 already state | **tracked** | `gsd-beads-25vc.21.5`. Fragment file outside scope. |
| P2 — `ship-precision-advisory.md` states "advisory" twice in four lines | **tracked** | `gsd-beads-25vc.21.5`. Fragment file outside scope. |
| P2 — `executor-numerics.md:9-10` unscoped, highest no-op risk in the corpus | **tracked** | `gsd-beads-25vc.21.5`. Fragment file outside scope. |
| P2 — `verifier-precision.md:4` chains four heterogeneous clauses in one sentence | **tracked** | `gsd-beads-25vc.21.5`. Fragment file outside scope. |
| P2 — `planner-sota.md:7` states one rule three ways | **tracked** | `gsd-beads-25vc.21.5`. Fragment file outside scope. |
| P2 — `planner-sota.md:4` closes on a no-op sentence | **tracked** | `gsd-beads-25vc.21.5`. Fragment file outside scope. |
| P2 — `planner-sota.md:5` restates its own prohibition in negated form | **tracked** | `gsd-beads-25vc.21.5`. Fragment file outside scope. |
| P2 — `capability.json:88` and `NOTES.md:6-21` argue the same point at two lengths | **tracked** | `gsd-beads-25vc.21.5`. Requires trimming NOTES.md, which touches the same file this plan already edited for other reasons but was left for the consolidated ticket to avoid a third partial NOTES.md edit late in the phase. |
| P2 — module docstring: 374 tok, one 5-clause sentence | **tracked** | `gsd-beads-25vc.21.5`. (Its stale "76 entries across phase directories" companion claim, same finding's other half, is already fixed via D-09 — verified 2026-09-08, the string no longer exists in the script.) |
| P2 — auto-install refusals repeat on every spawn until cleared | **tracked (note only)** | `gsd-beads-25vc.21.5`. File (`hooks/capability-auto-install.sh`) outside scope; low actionability since Claude Code only feeds hook stderr to the model on a blocking exit code, which this hook never uses. |

## Part 3 — Actions taken by this plan

1. **Pushed the branch** (`git push origin feat/extended-sota-definition`, `e3d253a..f1fb830`) to close the D-26/P1-5 gap between PR #4's head and local HEAD before re-triaging its threads, per the standing rule that internal review and its accepted fixes land before external review sees them.
2. **Committed one fix-set** (`c8c8a1b`) in the target repo covering P1-3 (`__pycache__` claim), P2-3 (GSD_HOME/HOME-unset test case), PONYTAIL P2-7 (CHANGELOG self-reference), and PROSE-TOKENS P2 (capability.json description). Files: `.gsd/capabilities/sota-numerics/capability.json`, `CHANGELOG.md`, `README.md`, `tests/test-gate-script-resolution.sh` — all within the plan's bounded `files_modified` list.
3. **Replied to and resolved all 5 previously-unresolved PR review threads** via the GitHub GraphQL API, each reply naming the live evidence for its disposition.
5. **Created 5 tracking tickets** (`gsd-beads-25vc.21.1` through `.21.5`) under the phase epic, covering every finding whose fix would require touching a file outside 24-08's bounded `files_modified` list, or that this plan attempted and reverted after it broke an existing accepted test. No finding was silently dropped.
6. **Restored the global capability mirror** (`~/.gsd/capabilities/sota-numerics`) to the released plugin-cache 0.1.3 bundle via `gsd_tools capability install .../0.1.3/.gsd/capabilities/sota-numerics --scope global --yes`, verified content-identical to the plugin cache's 0.1.3 copy via `diff -rq` (D-17's phase-end restoration step). See `24-08-SUMMARY.md`'s D-17 section for the full hash trail and the caveat about cross-path hash comparison.

## Verification against this plan's own checklist

- [x] Live thread total (12) equals this ledger's thread-row count (12); every row carries a disposition.
- [x] Every finding across all four review artifacts has exactly one row above, and every deferral names a bd ticket (`gsd-beads-25vc.21.1`–`.21.5`).
- [x] No working-tree change lies outside the bounded file list: `git diff --stat` for commit `c8c8a1b` touches exactly `capability.json`, `CHANGELOG.md`, `README.md`, `tests/test-gate-script-resolution.sh` — all four are in `24-08-PLAN.md`'s `files_modified`.
- [x] Both corpora re-run after the last accepted fix, all suites pass, the branch is zero commits behind its base — see `24-08-SUMMARY.md`.
