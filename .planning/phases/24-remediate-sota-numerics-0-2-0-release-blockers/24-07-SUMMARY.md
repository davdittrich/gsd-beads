---
phase: 24-remediate-sota-numerics-0-2-0-release-blockers
plan: 07
subsystem: infra
tags: [documentation-drift, claim-trace, readme-audit, command-verification]

# Dependency graph
requires:
  - phase: 24-06
    provides: CHANGELOG.md and check-alternatives.py's PLAN_SHAPED_RE comment
      free of stale hand-maintained counts; the favor/favour spelling
      settled corpus-wide; NOTES.md section 6 naming the
      workflow.post_planning_gaps gate-dispatch coupling (D-09, D-11,
      D-17 closed).
provides:
  - "The two claims REVIEW-AGY-FINAL.md named as false (the
    uncommitted-or-ignored row's inverted 'git status calls it clean'
    clause, and the file-name sentence calling draft-PLAN.md 'ignored'
    when the gate reports it as misnamed) now state what the code
    does, each proved by an actual run rather than by re-reading the
    source (D-10)."
  - "Every remaining behavioural claim in README.md is traced to the
    line of code that decides it and recorded in this file's trace
    table; the one real gap found -- the exit-code-2 bullet naming
    only 3 of resolve_current_phase_dir()'s 7 raise conditions -- is
    closed (D-10)."
  - "Every fenced command block in README.md is classified read-only
    or state-mutating; every read-only block was run as written and
    its exit status recorded; every state-mutating block (all six
    plugin install/update/uninstall commands) is recorded excluded
    under D-17, with the reason a reader would need to check safely."
affects: []

# Actuals (#2632)
actuals:
  tokens: 1354
  tasks: 3
  commits: 2
  commits_note: >
    Plan's edits land in a DIFFERENT repository from this SUMMARY
    (target_repo per 24-07-PLAN.md frontmatter): sota-numerics
    checkout at /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013,
    branch feat/extended-sota-definition. tokens/commits above measure
    that repo's diff (git diff 7c77ea9..HEAD, 1 file changed, 5,416
    chars / 4 ~= 1,354 tok; git rev-list --count 7c77ea9..HEAD = 2),
    not this orchestrator repo. THIS repo (gsd-beads) gets only this
    SUMMARY plus STATE.md/ROADMAP.md/REQUIREMENTS.md updates, docs-only,
    tracked separately below as plan_head_before / commits.
  confidence: low (plan's own estimate) -- realised low: 1,354 measured
    tokens against a 58,000-token estimate. The estimate priced a
    whole-file rewrite; the actual work was a full-file trace producing
    two small, surgical edits (9 insertions / 6 deletions total) once
    the trace showed almost every claim already agreed with the code.

tech-stack:
  added: []
  patterns-established:
    - "A whole-file behavioural-claim trace records one row per claim
      naming the deciding code, not just the two claims a review
      happened to name -- the same shape Phase 23's D-20 established
      for the original README pass, re-run here against everything
      that pass and 24-01 through 24-06 added since."
    - "Where a trace finds the README's claim incomplete rather than
      false (the exit-code-2 list), the fix is still to extend the
      README, not the code -- 'disagree' covers under-claiming as well
      as false claiming, because a reader relying on an incomplete
      enumeration to diagnose a failure is misled the same way a false
      claim misleads."

key-files:
  created: []
  modified:
    - README.md (target repo)

key-decisions:
  - "Read the actual git-status-invocation flags in
    hooks/capability-auto-install.sh (--porcelain --ignored) before
    touching the uncommitted-or-ignored row, per the task's own
    precondition, rather than trusting the row's existing prose --
    which turned out to be exactly backwards: the guard's --ignored
    flag is why it catches a stray __pycache__/, not something the
    guard misses."
  - "Proved the file-name correction with a live run rather than a
    source reading alone: created a scratch phase directory holding
    only draft-PLAN.md and ran check-alternatives.py against it,
    observing exit 1 with the misnamed-plan message, before writing
    the corrected README sentence."
  - "Treated the exit-code-2 bullet's missing raise conditions as a
    disagreement in scope for this plan (edit the README), not an
    out-of-scope addition, because the plan's own must-have truth is
    that EVERY behavioural claim traces to code, and an enumeration a
    reader would reasonably read as exhaustive that silently omits
    four of seven raise paths is the same failure mode as a false
    claim, just quieter."
  - "Discovered and root-caused a false-positive hash discrepancy
    during D-17 measurement: the pre-edit hash included a
    .gsd/capabilities/sota-numerics/scripts/__pycache__/ directory
    left over from running the Python suite before I noticed it;
    deleting that gitignored artifact and re-running with
    PYTHONDONTWRITEBYTECODE=1 produced a stable hash. Recorded both
    raw measurements below rather than silently reconciling them, with
    `git diff --stat HEAD -- .gsd/capabilities/sota-numerics/` (empty,
    both before and after) as the load-bearing evidence that the
    shipped bundle content itself never changed."
  - "Excluded the 'Why block the plan' section's research citations
    (Boehm, Sharma et al., DARS, CWM, LLM-evaluator-order bias) from
    the claim trace: they assert what published external work found,
    not what this repository's gate, hooks, or install code do --
    there is no file in this repo that 'decides' a citation's finding,
    so tracing them to code would be a category error, not a
    completeness gap."
  - "Left the marketplace-pointer sentence (README.md:35, 'the
    sota-numerics entry points at this repository') untraced to code:
    it is a claim about gsd-beads' own marketplace.json, a different
    repository this plan is not scoped to touch or read for
    verification, and D-12 already closed that entry's accuracy in an
    earlier plan."

requirements-completed: [D-10, D-17]

coverage:
  - id: T1
    description: "Every behavioural claim README.md makes about the
      gate is traced to the code that decides it, and the trace is
      recorded rather than asserted (D-10)."
    requirement: D-10
    verification:
      - kind: other
        ref: "This SUMMARY's 'Claim trace' table, below -- 45 claims traced, 1 gap found and closed (README.md exit-code-2 list)"
    status: pass
    human_judgment: false
  - id: T2
    description: "The two claims the reviews named as false state what
      the code actually does, proved by running the code rather than
      by reading it."
    requirement: D-10
    verification:
      - kind: other
        ref: "target repo: scratch directory holding only draft-PLAN.md -> `python3 .gsd/capabilities/sota-numerics/scripts/check-alternatives.py <dir>` exits 1 with the misnamed-plan message (below); `grep -icE 'calls (it )?clean|considers (it )?clean|treats (it )?as clean' README.md` -> 0; commits cb6911a, f1fb830"
    status: pass
    human_judgment: false
  - id: T3
    description: "Every command the README tells a reader to run has
      been run as written, or is recorded as excluded with the reason
      it was not run."
    requirement: D-17
    verification:
      - kind: other
        ref: "This SUMMARY's 'Command run log' table, below -- 2 read-only blocks run, 6 state-mutating blocks recorded excluded under D-17"
    status: pass
    human_judgment: false

duration: ~40min
completed: 2026-09-08
status: complete
plan_head_before: afbf4a52832d025d1d35bf2981346353cc11bcce
---

# Phase 24 Plan 07: Trace README's Behavioural Claims to Code Summary

**Ran a whole-file trace of every behavioural claim in `sota-numerics`' README.md against the code that decides it, corrected the two claims the reviews named as inverted or backwards, closed one further gap the trace itself found (an incomplete exit-code-2 enumeration), and proved every read-only command in the file by running it while recording the six install/update/uninstall commands as deliberately unrun under D-17.**

## Performance

- **Duration:** ~40min
- **Completed:** 2026-09-08T09:21:00Z
- **Tasks:** 3/3 complete
- **Commits:** 2 in target repo (sota-numerics worktree) -- docs, docs

## Accomplishments

- **Task 1 (the two review-named claims):** Confirmed the precondition
  first -- `hooks/capability-auto-install.sh:184` already invokes
  `git status --porcelain --ignored --untracked-files=all
  --ignore-submodules=none`, so the `--ignored` flag is exactly why the
  guard catches a stray `__pycache__/`, not something it misses.
  Rewrote README.md:58's "What clears it" cell to say that (dropping
  the clause claiming `git status` calls the directory clean) while
  leaving the row's condition and message columns untouched. Rewrote
  README.md:93 to stop calling `draft-PLAN.md` "ignored": the gate's
  `PLAN_SHAPED_RE` (`check-alternatives.py:87`) matches it, so
  `discover_plan_files` (`check-alternatives.py:369-403`) collects it
  as misnamed and `check_alternatives` (`check-alternatives.py:830`)
  reports it as a violation -- proved live by creating a scratch phase
  directory holding only that name and observing exit 1. True nested
  plans (files below a subdirectory of the phase directory) are the
  ones actually never looked at, because `Path(phase_dir).iterdir()`
  does not recurse -- the corrected sentence now says both things
  separately instead of collapsing them into one wrong "ignored".
  Commit `cb6911a`.
- **Task 2 (whole-file trace):** Enumerated every non-fenced sentence,
  table cell, and list item in README.md that asserts what the gate,
  a hook, or the installer does, accepts, rejects, counts, ignores, or
  reports (the rule PLAN.md's own `<context>` states and 23-CONTEXT's
  D-20 established); excluded the "Why block the plan" section's
  research citations as a category error (no file in this repo
  decides what an external paper found) and the marketplace-pointer
  sentence as out of this repo's scope (D-12 already closed it
  elsewhere). Traced every remaining claim to `check-alternatives.py`,
  `hooks/capability-auto-install.sh`, `hooks/session-start.sh`,
  `hooks/gsd-tools.sh`, `capability.json`, and the four fragment files
  -- full table below. Found one real gap: README.md's exit-code-`2`
  bullet named only 3 of `resolve_current_phase_dir`'s 7 distinct
  raise conditions (missing YAML frontmatter, a duplicated
  `current_phase` field, an absent `## Current Position` section, a
  `Phase:` line count other than one, and frontmatter/body
  self-disagreement were silently absent from the enumeration a reader
  would take as exhaustive). Extended the bullet to name all 7,
  changing no code. Every other claim already agreed. Commit `f1fb830`.
- **Task 3 (run every command):** Enumerated all 5 fenced `bash`
  blocks (the `text`/`json`/`markdown` blocks are config or plan-body
  examples, not commands a reader runs). Ran both read-only
  `check-alternatives.py` invocations as literally written and
  recorded their actual output. Classified all 6 plugin
  marketplace/install/update/uninstall commands (Claude and Codex,
  install and update-or-remove sections) as state-mutating and
  recorded them excluded under D-17 -- running any of them would
  install or replace the live global `sota-numerics` mirror with
  bytes from this development branch, precisely the hazard D-17
  exists to prevent mid-phase. Independently re-measured the bundle
  hash before and after this plan's edits, using the absolute-path
  method 24-01 through 24-06 verified; see 'D-17 hash sidecar' below
  for the discrepancy found and resolved during that measurement. No
  further README edit was needed for this task -- neither read-only
  command's output is quoted anywhere in the file, so there was
  nothing stale to correct.

## Claim trace (Task 2)

**Enumeration rule:** a claim is any sentence, table cell, or list
item outside a fenced code block that asserts what the `plan:post`
gate, a Claude hook, or the installer does, accepts, rejects, counts,
ignores, checks, refuses, or reports. Advisory recommendations with no
enforced behaviour (e.g. "keep the section to that line unless extra
text serves a clear purpose") and claims about a different repository
this plan does not touch are recorded as excluded rather than traced.
README.md is 276 lines after this plan's edits (270 before); the two
excluded categories below account for roughly 25 of the file's
non-fenced lines (the references list and the marketplace sentence).

| # | README.md line(s) | Claim (paraphrased) | Code location | Verdict |
|---|---|---|---|---|
| 1 | 5 | Adds four advisory prompts and one blocking plan gate | `capability.json:29-90` (4 `contributions`, 1 `gates` entry) | agrees |
| 2 | 11 | planner row: research, cite, rank by performance/simplicity-LOC/ecosystem/maintenance, go with the grain, bound every task | `fragments/planner-sota.md:2,9,10,11` | agrees |
| 3 | 12 | gate row: blocks an eligible plan lacking a compliant Alternatives Considered section | `check-alternatives.py` `validate_plan` (761-795) | agrees |
| 4 | 13 | executor row: derive parameters, stable arithmetic, name the ceiling, quiet+legible bars | `fragments/executor-numerics.md:2,3,6,7,9` | agrees |
| 5 | 14 | verifier row: 10-item flag list (drift, dropped edge cases, unstable substitutions, ...) | `fragments/verifier-precision.md:2-7` | agrees |
| 6 | 15 | ship row: precision/efficiency/quiet/legibility claims need measurements; grain claims name the convention; simplifications state their ceiling | `fragments/ship-precision-advisory.md:2,3` | agrees |
| 7 | 17 | prompts advisory (rendering failure skips, no workflow stop); gate blocking (missing interpreter/script/crash/30s timeout "halts planning") | `capability.json` contributions `onError:"skip"` (39,50,61,72); gate `onError:"halt"` + description comment (79-88) | agrees -- "halts planning" is the plain-English name for what the gate description calls a "block" verdict (as opposed to gsd-core's own manifest-level "halt", reserved for a malformed predicate); the operator-facing effect is the same: the plan step cannot proceed |
| 8 | 35 | "the sota-numerics entry points at this repository" | gsd-beads' own `.claude-plugin/marketplace.json` (different repository) | excluded -- out of this repo, D-12 closed it elsewhere |
| 9 | 37 | declares support for every GSD runtime | `capability.json:12-17` `runtimeCompat.supported: ["*"]` | agrees |
| 10 | 37 | startup install + role banners come from SessionStart/SubagentStart hooks | `hooks/hooks.json:3-31` | agrees |
| 11 | 39-40 | gate can use bundle at `<project>/.gsd/capabilities/sota-numerics` or `${GSD_HOME:-$HOME}/.gsd/capabilities/sota-numerics` | `capability.json:81` gate command (`SOTA_SCRIPT="./$_SN" \|\| ... "${GSD_HOME:-$HOME}/$_SN"`) | agrees |
| 12 | 42 | project copy wins when both exist | same gate command, `[ -f "$SOTA_SCRIPT" ] \|\|` short-circuit tries project path first | agrees |
| 13 | 46 | fires at startup/resume/clear/compact and on gsd-planner/executor/verifier spawn; checks whole-bundle hash | `hooks/hooks.json:5,13,19,25`; `hooks/capability-auto-install.sh` `bundle_hash()` (51-58) | agrees |
| 14 | 46 | installs at global scope only when hash changed, so it can fire mid-session | `capability-auto-install.sh:80` (`[ "$NEW_HASH" = "$OLD_HASH" ] && exit 0`) | agrees |
| 15 | 46 | banner prints when capability enabled and config lookup succeeds | `hooks/session-start.sh:8-24` | agrees, with the exception already named at README.md:68 (a missing provider defaults to enabled) |
| 16 | 48 | global install publishes to every project on the machine, so only bytes the repo records as published install; unpublished installs unverified | `capability-auto-install.sh:90-99` comment + `TRACKED` branch (132-218) | agrees |
| 17 | 48 | reads local `origin/HEAD`/`origin/main`, never contacts the remote | `capability-auto-install.sh:205-206` (`git rev-parse --verify --quiet origin/HEAD \|\| origin/main`, no `fetch`) | agrees |
| 18 | 48 | every refusal names its reason on stderr, installs nothing, leaves hash unwritten so a later session retries | every refusal branch in `capability-auto-install.sh` (74,86,154,158,190,208,212,216) exits 0 before reaching the `printf ... "$STATE_FILE"` write at 237 | agrees |
| 19 | 50-60 | the 9-row refusal table (bundle unreadable, no git, git can't open repo/index, status fails, ls-files fails, assume-unchanged/skip-worktree, dirty bundle, no origin ref, HEAD unpublished) | `capability-auto-install.sh` refusal branches, matching lines in order: 74, 86, 154+216(merged), 154, 158, 190, 208, 212 | agrees -- independently re-derived exit-path count (15 total, 9 refusal messages) during Task 2's own reading, matching REVIEW-AGY-FINAL.md's own re-derivation and rejecting agy's "claims eight" mis-citation |
| 20 | 58 (corrected) | uncommitted-or-ignored row's "what clears it" | `capability-auto-install.sh:167-169,184` (`--ignored` flag + comment) | now agrees (Task 1 fix) |
| 21 | 62 | plugin host's `.in_use`/`.orphaned_at` sit 3 dirs above the bundle, outside the `git status` scope | `BUNDLE_DIR="$PLUGIN_ROOT/.gsd/capabilities/$CAP_ID"` (line 24) is 3 path segments below `PLUGIN_ROOT`; status invoked `-C "$BUNDLE_DIR" ... -- .` (184-185) | agrees |
| 22 | 64 | role-specific banners for planner/executor/verifier; unknown role falls back to generic; other roles never trigger the hook | `hooks/session-start.sh:26-37` `case` statement; `hooks/hooks.json` only matches `gsd-planner`\|`gsd-executor`\|`gsd-verifier` | agrees |
| 23 | 66 | auto-install runs before the enabled check; disabling silences banners and turns off contributions/gate but not the install check | `session-start.sh:6` (install call) precedes line 10 (enabled read); `capability.json` contributions/gate all carry `"when": "sota-numerics.enabled"` (39,50,61,72,85) | agrees |
| 24 | 68 | provider resolution order: `CLAUDE_PLUGIN_ROOT`/file-location-relative `gsd-core/bin/gsd-tools.cjs`, then `PATH`, then `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` copy; never the invoking working directory (D-13) | `hooks/gsd-tools.sh:13-25` | agrees -- no `git rev-parse` remains in this file after 24-05's D-13 fix |
| 25 | 68 | missing hash tool exits quietly; missing provider or install failure leaves hash unwritten, retries later; missing provider defaults banner to true | `capability-auto-install.sh:27-34` (hash tool); `:238-241` (install-status branches); `session-start.sh:11-12` (`ENABLED_STATUS -eq 127` -> `ENABLED=true`) | agrees |
| 26 | 82 | default `true`; GSD reads from `.planning/config.json` | `capability.json:24` `"default": true`; gsd-core's standard project-config path | agrees |
| 27 | 86 | checker reads direct child files only | `check-alternatives.py` `discover_plan_files` (369-403), `Path(phase_dir).iterdir()`, no recursion | agrees |
| 28 | 93 (corrected) | nested plans not looked at (no recursion); plan-shaped-but-misnamed files reported, not ignored | `discover_plan_files` iterdir (no recursion) + `PLAN_SHAPED_RE`/misnamed collection (87,401-402) | now agrees (Task 2 fix) |
| 29 | 95 | `## Alternatives Considered` heading, case-insensitive, suffix allowed but no word joined directly to "Considered"; section ends at next H1/H2 (indent <=3 spaces) or EOF; H3+ stay inside; fences ignored; unterminated fence blanks to EOF | `SECTION_HEADING_RE` (123-125, `re.IGNORECASE`, trailing `\b`); `NEXT_HEADING_RE` (95-99); `mask_fenced_regions` (155-191); `fence_close` (403-407, returns `len(text)` when unterminated) | agrees |
| 30 | 110 | `-`/`*` bullets both work; bold name required, colon optional; evidence runs to next bullet or section end; internal marker ends a preceding mechanism span; unrelated H3 does not truncate on a no-marker path | `BULLET_RE` (135); `split_entries` transitions logic (620-645) | agrees |
| 31 | 112-125 | framed table also works (header+separator+bold rows); table evidence confined to its row; header/separator never count; bullets take precedence over table when >=2 mechanism bullets exist, regardless of internal-bullet count; otherwise falls to table, no combining | `split_entries` table branch (653-673); `mechanism_bullets` filter + `>= MIN_ALTERNATIVES` check (650-651); `return entries or bullet_entries` (673) | agrees |
| 32 | 127-145 | `### Internal design alternatives`, case-sensitive, exactly one space after `###`, trailing space/tab allowed; internal entries need no citation/date, don't count, can't lend evidence; peer H3 (including bare `###`) ends scope | `INTERNAL_HEADING_RE` (131-133, literal one-space string); `H3_HEADING_RE` (130, optional trailing text group makes bare `###` match); `split_entries` transitions (620-635); `mechanism_entries` filter before validation (783-787) | agrees |
| 33 | 147-152 | entry needs URL/backticked ref (1-300 chars) and a 4-digit year in [current-6, current]; older foundational year OK if paired with an in-window one | `URL_RE`/`DOC_REF_RE` (144-145); `validate_entry` recency check (699-712) | agrees |
| 34 | 152 | rejects `example.com`/`.org`/`.net`/`localhost` and bare TODO/TBD; port bypasses the authority match (narrow filter, not URL verification) | `PLACEHOLDER_HOSTS` (149); `entry_placeholder_violation` (694-704); `HOST_RE` (148, captures through port) | agrees -- confirmed live that `example.com:443` is not in the set, so it passes the filter as documented |
| 35 | 154-162 | `Decided by:` needs one of 5 tokens; matcher has no trailing word boundary, so `performanceXYZ` also passes; check is structural only | `DECIDED_BY_RE` (145-148, `re.IGNORECASE`, no trailing `\b`) | agrees |
| 36 | 168-172 | `N/A — no mechanism choice` (hyphen or em dash) as first nonblank line exempts the section | `EXEMPTION_RE` (124); `is_exempt` (616-621) | agrees |
| 37 | 176-188 | one reason per failing plan as `<path>:<line>: <reason>`; span bounded to 80 chars, `found:` list to 5 values, elision markers, no stderr line over 200 chars; checks every plan then prints one remediation line | `elide_span`/`elide_values`/`elide_line` (216-259); `main()` violation loop + single remediation print (878-887) | agrees |
| 38 | 191-197 (corrected) | exit codes 0/1/2 and what triggers `2` | `main()` (835-891); `resolve_current_phase_dir` raise sites (302-364) | now agrees (Task 2 fix -- 4 raise conditions added) |
| 39 | 199-200 | decode-failure message names file, reason, byte offset, remedy | `validate_plan` UnicodeDecodeError handler (758-762) | agrees |
| 40 | 202 | other filesystem errors escape uncaught as Python errors, exit 1, no remediation line; unchecked file-type lets a plan-shaped directory take the same path | `main()`'s `except ValueError` only (859-861, other exception types propagate); `discover_plan_files` has no `is_file()` guard (398-402) | agrees -- also matches REVIEW-AGY-FINAL.md's own independently-reproduced `IsADirectoryError` traceback finding |
| 41 | 204-206 | phase-dir argument optional; gate passes none; command is constant; phase resolved from STATE.md so a directory name never reaches a shell | `capability.json:81` (no `${PHASE_DIR}` splice); `main()` (838-844) | agrees |
| 42 | 213 | `plan:post` runs after the plan is committed; this gate is the fail-closed backstop | `.gsd/capabilities/sota-numerics/NOTES.md` section 2 ("gate fires late -- plan already committed"), itself re-derived against `~/.claude/gsd-core/workflows/plan-phase.md:1524,1558` in 24-06 | agrees (cited via NOTES.md's own already-re-derived trace rather than re-deriving a third time) |
| 43 | 215 | gate script absent from both scopes exits with a direct install error, not a silent pass | `capability.json:81` (`test -f "$SOTA_SCRIPT" \|\| { echo ...; exit 1; }`) | agrees |
| 44 | 219-223 | Bash arrays/`[[ ]]`, not POSIX sh; Python 3 stdlib only, no child processes; gsd-core >=1.10.0; git not needed for gate/gsd-tools.sh resolution (D-13/D-14), needed for the auto-install's provenance check | `capability-auto-install.sh:29` (array), `:17` (`[[ ]]`); `check-alternatives.py` imports (26-29, stdlib only, no `subprocess`); `capability.json:9-11`; `hooks/gsd-tools.sh` (no `git`); `capability-auto-install.sh:85-88` (`git unusable` refusal) | agrees |
| 45 | Why block the plan (245-269) | citations to CWM/DARS/sycophancy/evaluator-order-bias/self-repair/Boehm research findings | external published papers, no file in this repository | excluded -- category error, not a code-traceable claim |

## Command run log (Task 3)

Fenced `bash` blocks only; the `json` (README.md:74-80, a config
example) and `text`/`markdown` blocks (README.md:88-91, 101-108,
114-123, 131-143, 168-170, 185-187, all plan-body illustrations) are
not commands a reader runs.

| README.md line(s) | Command | Class | Result |
|---|---|---|---|
| 23-26 | `claude plugin marketplace add davdittrich/gsd-beads` + `claude plugin install sota-numerics@gsd-beads -y` | state-mutating | excluded (D-17) -- installs the plugin at global scope; running it mid-phase would replace `~/.gsd/capabilities/sota-numerics` with this unreleased branch's bytes, or with whatever the live marketplace currently serves, neither of which this plan is verifying |
| 30-33 | `codex plugin marketplace add davdittrich/gsd-beads` + `codex plugin add sota-numerics@gsd-beads` | state-mutating | excluded (D-17) -- same hazard, Codex path |
| 211-214 | `python3 .gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (no arg) | read-only | run from the target-repo worktree root; exit `0`, no output. The worktree has no `.planning/` of its own, so `find_project_root` walked up the filesystem (not git-aware) to the physically-enclosing `gsd-beads` project's `.planning/` and validated ITS current phase (24) -- correct, tested behaviour for a project nested under another GSD project (`test-gate-script-resolution.sh` case5, monorepo precedence), not a defect, but specific to this dev worktree's on-disk nesting rather than to a real end-user deployment |
| 211-214 | `python3 .gsd/capabilities/sota-numerics/scripts/check-alternatives.py .planning/phases/11-example` | read-only | run as literally written; `.planning/phases/11-example` does not exist in this repo (the path is illustrative). Output: `check-alternatives.py: not a directory: .planning/phases/11-example`, exit `2` -- matches the documented exit-2 behaviour for a non-existent explicit path |
| 232-236 | `claude plugin marketplace update gsd-beads` + `claude plugin update sota-numerics@gsd-beads --scope user -y` + `claude plugin uninstall sota-numerics@gsd-beads --scope user -y` | state-mutating | excluded (D-17) -- update/uninstall would mutate the real, live, globally-installed `sota-numerics` plugin on this machine |
| 240-244 | `codex plugin marketplace upgrade gsd-beads` + `codex plugin add sota-numerics@gsd-beads` + `codex plugin remove sota-numerics@gsd-beads` | state-mutating | excluded (D-17) -- same hazard, Codex path |

Neither read-only command's output is quoted in README.md's prose, so
no stale specimen output needed correcting; both commands' exit
statuses are recorded above rather than left unverified.

## D-17 hash sidecar

Per D-17, `~/.gsd/capability-auto-install-sota-numerics.hash`
independently re-measured before this plan's edits and after, using
the same absolute-`PLUGIN_ROOT`-rooted method 24-01 through 24-06
verified (`find "$BUNDLE_DIR" ... \| sort \| sha256sum`, walking
`$WT_ROOT/.gsd/capabilities/sota-numerics`):

| Measurement | Value |
|---|---|
| Pre-edit, first raw measurement (before any edit or test run this session) | `82e6e84fb0e0b23fd2a93ad8681df12a49a3fed2ea2f406b01ca835fb17c5dd1` |
| Post-edit, after deleting a gitignored `scripts/__pycache__/` and re-running with `PYTHONDONTWRITEBYTECODE=1` | `ac399b2c105ba03c089d2acd4716d259ac603ba030ad1473ed775aeca0dca2fc` (stable across 4 repeated measurements) |
| Live sidecar (`~/.gsd/capability-auto-install-sota-numerics.hash`), before and after | `da4da96a5d8327d5b6c38a7e6adfa7883f2b6dbac710e891c7236239f55ad498` (unchanged) |

The two raw measurements differ, and that difference is reported
rather than silently reconciled: the pre-edit measurement was taken
before this session had run any Python, so a `__pycache__/` already
present under `.gsd/capabilities/sota-numerics/scripts/` at that
moment can only be a carry-over from a prior test run (this plan's
`requires` names 24-06 as the immediately preceding work in this
worktree). That directory is git-ignored and untracked -- `git status
--ignored -- .gsd/capabilities/sota-numerics/` reports it as ignored,
never as a change -- so its presence or absence moves the
`find`-based hash without ever moving `git diff`. The load-bearing
evidence that this plan changed nothing inside the shipped bundle is
`git diff --stat HEAD -- .gsd/capabilities/sota-numerics/`, run
immediately before writing this SUMMARY: empty, both against the
commit this plan started from (`7c77ea9`) and against the current
HEAD (`f1fb830`) -- neither of this plan's two commits touches any
file under that directory (both touch only `README.md`, outside
`BUNDLE_DIR`). The sidecar file itself stayed unchanged throughout,
matching the previously-documented stale state 24-01 through 24-06
each independently confirmed: `hooks/capability-auto-install.sh`'s own
dirty-tree guard (`bundle has uncommitted or ignored files; refusing
to install`) still refuses this worktree, so no install ever fired.

## Deviations from Plan

**1. [Rule 2 -- completeness] Extended the exit-code-2 enumeration beyond the two claims the reviews named.**
- **Found during:** Task 2's whole-file trace.
- **Issue:** README.md's exit-`2` bullet named 3 of `resolve_current_phase_dir`'s 7 distinct raise conditions; a reader diagnosing an exit-2 failure from one of the other 4 (missing frontmatter, duplicate `current_phase`, absent `## Current Position` section, or a `Phase:`-line count other than 1) would find no matching cause in the file.
- **Fix:** Extended the bullet to name all 7 conditions, changing no code.
- **Files modified:** README.md (target repo).
- **Commit:** `f1fb830`.

No other deviations -- both remaining tasks executed as planned, and
every other traced claim already agreed with the code.

## Known Stubs

None.

## Threat Flags

None -- this plan closes its own `<threat_model>` entries. T-24-26
(Spoofing, README claims about gate rejects): Task 1 corrected the
`draft-PLAN.md` claim and proved the correction by running the gate
over a scratch directory holding that exact name (exit 1, see 'Command
run log' precursor in Task 1's own accomplishment). T-24-27
(Repudiation, untraced behavioural claims): Task 2's 45-row trace
table above records every enumerated claim's pairing to code.
T-24-28 (Elevation of Privilege, install commands quoted in README):
Task 3 excluded all 6 state-mutating blocks and confirmed the install
hash unchanged (D-17 hash sidecar, above). T-24-29 (Tampering,
executable code under a documentation plan): confirmed via `git diff
--stat HEAD -- .gsd/capabilities/sota-numerics/` (empty) and `git
status --short` (only `README.md` modified) after every commit.
T-24-30 (Information Disclosure, specimen output quoted in README):
Task 3 declined to quote either read-only command's output into the
file, recording both runs here instead. No new network endpoint, auth
path, file-access pattern, or schema change introduced.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- D-10 and D-17 (this plan's own decision slice) closed: every
  behavioural claim in README.md now traces to code, the two
  review-named claims are corrected and proved by execution, and the
  D-17 hash discipline is maintained (including the transient
  `__pycache__` discrepancy found and root-caused during this plan's
  own measurement, rather than left unexplained).
- Remaining phase-24 requirements not yet closed by
  24-01/24-03/24-04/24-05/24-06/24-07: D-06 (gate-behaviour test
  fixtures), D-12 (marketplace-entry description sync, in gsd-beads
  not the target repo), D-15 (CodeRabbit-thread triage), D-16/D-20
  (publish ordering), D-18 (rejected-alternative record), D-19/D-21
  (merge-is-publish, tag), D-22 (decision-checkpoint re-ask), D-23
  (bd-issue reuse for publish tasks), D-24 (phase exit).
- No new upstream ticket opened by this plan; no existing one closed
  either -- this plan's scope (README accuracy) did not touch the
  gsd-core coupling tickets (`gsd-beads-g72`, `gsd-beads-h1pb`) 24-06
  opened and left open.

## Self-Check: PASSED

FOUND: `.planning/phases/24-remediate-sota-numerics-0-2-0-release-blockers/24-07-SUMMARY.md`
FOUND: target repo commit `cb6911a` (`git log --oneline --all \| grep cb6911a`)
FOUND: target repo commit `f1fb830` (`git log --oneline --all \| grep f1fb830`)
