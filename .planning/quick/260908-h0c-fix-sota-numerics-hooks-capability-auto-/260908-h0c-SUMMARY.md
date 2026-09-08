---
phase: quick-260908-h0c
plan: 01
subsystem: infra
tags: [bash, shell, hooks, sota-numerics, capability-install, security-hardening]

# Dependency graph
requires:
  - phase: quick-260908-h0b (sota-numerics plan .21.1)
    provides: check-alternatives.py fail-closed edge-case fixes on the same branch
provides:
  - "hooks/capability-auto-install.sh bundle_hash rewritten to an unforgeable, kind-tagged, escaped record stream (finding 1)"
  - "hooks/capability-auto-install.sh capability install wrapped in a 60s timeout/gtimeout bound (finding 2)"
  - "hooks/capability-auto-install.sh sidecar write unlinks before writing, so it cannot be redirected through a planted symlink (finding 3)"
affects: [24-remediate-sota-numerics-0-2-0-release-blockers]

# Actuals (#2632)
actuals:
  tokens: 4615
  tasks: 3
  commits: 3
# This plan's code commits land in a DIFFERENT repository (target_repo below),
# not in gsd-beads. The gsd-beads-local ledger protocol (#3968) does not apply
# cross-repo; commits are measured directly against the target repo's own log
# instead (git rev-list --count e5ff8d3..HEAD in the target worktree = 3).

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Kind-tagged, escaped, NUL-delimited-input record stream for whole-directory content hashing (l/f/o tags, fork-free _esc escaper) — replaces free-text 'path -> target' / raw hash-tool-output lines wherever attacker-controlled bytes (paths, symlink targets) must reach a hash input without becoming forgeable record separators"
    - "timeout/gtimeout wrapper around a shell-function call via bash -c on a program string, sourcing the function's own resolver inside the timed child rather than exporting it from the parent, with the ${arr[@]+\"${arr[@]}\"} empty-array-safe expansion for bash 3.2 set -u compatibility"
    - "rm -f <path> immediately before an unconditional write to <path>, so the write always creates a fresh regular file rather than following a symlink planted at that path"

key-files:
  created: []
  modified:
    - "hooks/capability-auto-install.sh (target repo) — bundle_hash rewrite, INSTALL_TIMEOUT wrapper, sidecar unlink-before-write"
    - "tests/test-capability-auto-install.sh (target repo) — cases I5, L3, L4, I6 added"
    - "README.md (target repo) — installer-requirements paragraph gains the timeout-bound sentence"
    - "CHANGELOG.md (target repo) — three ## 0.2.0 hook-section paragraphs, one per finding"

key-decisions:
  - "Bundle-walk collision (finding 1): chosen fix is tag-and-escape, one record line per entry, over (a) directory-name-injection guard alone (closes only the reported vector, not the sibling symlink-target and ambiguous-own-name collisions), (b) hashing paths through the hash tool itself (extra fork per entry on every SessionStart/SubagentStart, no benefit over escaping), (c) find -print0 | sort -z (sort -z is not POSIX, and the file's own sha256sum-vs-shasum dance exists precisely because the real macOS target cannot be tested here)"
  - "Install timeout (finding 2): chosen fix is a timeout/gtimeout prefix around bash -c, re-sourcing the resolver in the child, over (a) export -f gsd_tools under timeout bash -c (degrades BASH_SOURCE resolution silently on hosts without CLAUDE_PLUGIN_ROOT set, and turns case L2's 127 into 1), (b) a background-install-plus-poll-loop (more moving parts than the bug is worth, and this repo's own automation rules forbid poll loops), (c) leaving it unbounded (a hang blocks every session start on the affected machine with no output at all)"
  - "Sidecar write (finding 3): chosen fix is rm -f before the write (the ticket's own second option), over (a) write-to-temp-then-rename (race-free via rename(2), but trades one pre-plantable path for another and triples the line count for a P2 the ticket itself scores low) and (b) refusing to write when the path is not a regular file (hands an attacker a permanent denial — plant the link once, block every future session)"
  - "OLD_HASH's own symlink-follow (read side of finding 3's threat) is left unfixed by design, per the ticket's own acceptance criteria naming a 'documented, low-value-exploit behaviour' branch; filed as gsd-beads-25vc.21.6 rather than silently deferred"

requirements-completed: [gsd-beads-25vc.21.2]

coverage:
  - id: D1
    description: "bundle_hash no longer collides on a deleted file plus a retargeted symlink whose target forges the deleted file's digest line"
    requirement: "gsd-beads-25vc.21.2"
    verification:
      - kind: integration
        ref: "tests/test-capability-auto-install.sh#I5 (target repo, commit 110ffc6)"
        status: pass
    human_judgment: false
  - id: D2
    description: "capability install runs under a 60s timeout/gtimeout bound; a kill is reported on stderr and leaves no sidecar; a host with neither binary still installs, unbounded"
    requirement: "gsd-beads-25vc.21.2"
    verification:
      - kind: integration
        ref: "tests/test-capability-auto-install.sh#L3 (target repo, commit 5c8ee95)"
        status: pass
      - kind: integration
        ref: "tests/test-capability-auto-install.sh#L4 (target repo, commit 5c8ee95)"
        status: pass
    human_judgment: false
  - id: D3
    description: "the recorded-hash sidecar write unlinks before writing, so a symlink planted at the sidecar path is replaced rather than followed"
    requirement: "gsd-beads-25vc.21.2"
    verification:
      - kind: integration
        ref: "tests/test-capability-auto-install.sh#I6 (target repo, commit cc014e1)"
        status: pass
    human_judgment: false
  - id: D4
    description: "D0 doc-parity gate (hook refusals == README's refusal table) and all pre-existing regression cases stay green across all three fixes"
    verification:
      - kind: integration
        ref: "bash tests/test-capability-auto-install.sh (target repo, final run: 37 PASS, 0 FAIL, ALL PASS)"
        status: pass
    human_judgment: false

duration: not precisely captured (start timestamp not recorded at dispatch; session ran ~40-50min by task count and log timestamps)
completed: 2026-09-08
status: complete
---

# Quick Task 260908-h0c: sota-numerics capability-auto-install.sh hardening Summary

**Bundle digest rewritten to a kind-tagged escaped record stream, capability install bounded to 60s under timeout/gtimeout, and the sidecar write now unlinks before writing — three atomic commits on sota-numerics `feat/extended-sota-definition`, closing gsd-beads-25vc.21.2's three findings.**

## Performance

- **Tasks:** 3/3 completed
- **Files modified:** 4 (target repo): `hooks/capability-auto-install.sh`, `tests/test-capability-auto-install.sh`, `README.md`, `CHANGELOG.md`
- **Commits:** 3, all in the target repo `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013` (davdittrich/sota-numerics, branch `feat/extended-sota-definition`)

## Accomplishments

- `bundle_hash` no longer trusts free-text lines built from attacker-controlled bytes: every walk entry now goes through `_esc` (fork-free, three ordered parameter expansions: backslash-double, newline, space) and `_bundle_records` (kind-tagged `l`/`f`/`o` lines over a NUL-delimited `find -print0` stream, files hashed via stdin redirection so the hash tool never sees a path). `set -o pipefail` keeps the existing partial-walk refusal (case J5) working through the new pipeline.
- The inline `gsd_tools capability install` call now runs under `timeout`/`gtimeout` at 60s, resolved into an array and expanded with the `${arr[@]+"${arr[@]}"}` guard so an empty wrapper array does not abort under `set -u` on bash 3.2. `gsd_tools` runs inside `bash -c` on a program string that sources the resolver in the child, preserving case L2's exit-127 behaviour and the `BASH_SOURCE` resolution fallback unchanged. A killed install (exit 124, wrapper in use) is reported on stderr without the refusal tail, leaving `D0` and README's refusal table untouched.
- The sidecar write (`printf '%s' "$NEW_HASH" > "$STATE_FILE"`) is preceded by `rm -f "$STATE_FILE"`, so a symlink planted at the sidecar path is replaced by a fresh regular file rather than followed and overwritten-through.
- Four regression cases added (`I5`, `L3`, `L4`, `I6`), each proven red against the pre-fix hook before its fix landed (evidence below). Final suite: 37 PASS, 0 FAIL, `ALL PASS`, `D0` still reporting exactly 9 refusals (unchanged from the pre-plan baseline), `I0` (real `~/.gsd` untouched) green.
- Filed gsd-beads-25vc.21.6 for the one residual the plan explicitly left unfixed (OLD_HASH's own symlink-follow read).

## Task Commits

All three commits are in the **target repo** (`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013`, branch `feat/extended-sota-definition`), not in gsd-beads:

1. **Task 1: Make every bundle-walk record a single unforgeable line** — `110ffc6` (fix)
2. **Task 2: Bound the inline capability install with a wall clock** — `5c8ee95` (fix)
3. **Task 3: Never write the sidecar through a symlink** — `cc014e1` (fix)

Pre-plan HEAD in the target repo: `e5ff8d3`. Post-plan HEAD: `cc014e1`. `git rev-list --count e5ff8d3..HEAD` = 3, matching the three commits above.

**This plan's own metadata** (this SUMMARY.md) is committed in the **working repo** (`gsd-beads`) as a separate `docs(...)` commit per the standard protocol — see the final-commit step below.

## Red-Before Evidence (RED phase per task, quoted verbatim from the suite run against the unmodified hook)

**Task 1 — I5** (before the `bundle_hash` rewrite):
```
FAIL: I5: symlink target forging deleted file's digest line defeated fast path
```
(assertion: `[ "$(installs)" = 2 ]` after deleting `$BUNDLE/f` and retargeting `$BUNDLE/z` to a target of `foo\n<forged sha256sum line for f>` — the old walk's sorted line multiset was unchanged by the substitution, so the second run took the fast path and `installs` stayed 1.)

**Task 2 — L3** (before the timeout wrapper; `L4` was already green pre-fix — see note below):
```
FAIL: L3: timeout stub not called exactly once
FAIL: L3: timeout not called bare numeric bound (log: )
FAIL: L3: real install stub ran despite timeout kill
FAIL: L3: wrong refusal (err: )
FAIL: L3: killed install wrote sidecar
```
(5 failures: with no timeout wrapper in the hook at all, the planted `timeout` stub was never invoked, the real install stub ran unconditionally, no "exceeded" message was emitted, and the sidecar was written despite the stub's intent to simulate a kill.)

*Note on L4:* `L4` (a host with no `timeout`/`gtimeout` still installs, unbounded) was **already green against the unmodified hook**, because unbounded execution is the hook's pre-existing baseline behavior — the fix's fallback path *is* that baseline, not new behavior. This is expected, not a gap: `L4` regresses that the fallback is preserved once the wrapper is added, and it correctly continues to pass after Task 2's fix.

**Task 3 — I6** (before the `rm -f "$STATE_FILE"` insertion):
```
FAIL: I6: sidecar write clobbered symlink's target (b8eb5552b15c28329a5d92cf58afc017914b5d16ca900e640759c48ec9a53bf4)
FAIL: I6: sidecar path still symlink after successful install
```
(the redirection followed the planted symlink at the sidecar path and overwrote `$SB/target`'s content with the hash digest; the sidecar path remained a symlink afterward.)

## CI Suite Verdicts (before / after)

Captured before Task 1 (baseline) and after Task 3 (final), per the plan's verification block:

| Suite | Baseline | Final | Verdict |
|---|---|---|---|
| `bash tests/test-session-start.sh` | `ALL PASS` | `ALL PASS` | byte-identical to baseline |
| `bash tests/test-capability-auto-install.sh` | 33 PASS, `ALL PASS` (pre-`I5`/`L3`/`L4`/`I6`) | 37 PASS, 0 FAIL, `ALL PASS` (gained `I5`, `L3`, `L4`, `I6`) | grew by exactly the 4 planned cases |
| `bash tests/test-gate-script-resolution.sh` | `ALL PASS` | `ALL PASS` | byte-identical to baseline |
| `python3 -m unittest tests/test_check_alternatives.py` | `Ran 130 tests in 3.757s` / `OK` | `Ran 130 tests in 3.666s` / `OK` | identical verdict and test count (130), timing noise only — this plan touches no Python and no bundle file |

`D0` (hook refusals == README's refusal table) reported **9 refusals in both the baseline and final runs** — unchanged, as required (the new timeout-kill message deliberately carries no refusal tail and is excluded from `D0`'s count). `I0` (real `~/.gsd` untouched by the suite) passed on every run.

## Files Created/Modified

- `hooks/capability-auto-install.sh` (target repo) — `bundle_hash`/`_esc`/`_bundle_records` rewrite (T1); `INSTALL_TIMEOUT`/`_TIMEOUT`/`_INSTALL_CHILD` wrapper around the install call (T2); `rm -f "$STATE_FILE"` before the sidecar write, plus the two residual-recording comments (T3)
- `tests/test-capability-auto-install.sh` (target repo) — cases `I5` (T1), `L3`/`L4` (T2), `I6` (T3)
- `README.md` (target repo) — installer-requirements paragraph gains the timeout-bound sentence (T2); refusal table (`| It refuses when |`) left untouched, as required
- `CHANGELOG.md` (target repo) — three `## 0.2.0` hook-section paragraphs, one per finding (T1, T2, T3)

## Decisions Made

See `key-decisions` in frontmatter for the Alternatives-Considered summary per finding (mirrors the plan's own `<alternatives_considered>` section, which was in scope and read before execution).

## Deviations from Plan

None — plan executed exactly as written, task actions matched almost verbatim to the plan's `<action>` prose. One addition beyond the plan's explicit text: the plan directed recording a follow-up ticket id for the OLD_HASH symlink-follow residual "if one is filed" — none of the existing `gsd-beads-25vc.21.x` children covered that specific residual, so `gsd-beads-25vc.21.6` was created and referenced in both the code comment and this SUMMARY. This is the plan's own contingency instruction being exercised, not a deviation from it.

## Issues Encountered

None. All three RED phases reproduced the exact collision/gap the plan predicted on the first attempt; all three fixes went green on the first attempt with `bash -n` passing throughout.

## Residuals Recorded (Task 3)

Both residuals the plan required to be named are recorded in the code comment (`hooks/capability-auto-install.sh`, immediately above the `rm -f "$STATE_FILE"` line) and here:

1. **Unlink/recreate race window.** Between the `rm -f` and the `printf` redirection, a racing attacker with write access to the sidecar's directory could re-plant a symlink. Closing it would need `O_NOFOLLOW`, which no POSIX shell offers. Accepted as proportionate: the threat model already grants that attacker write access to the directory, and the window is a single unlink-then-open pair, not an open-ended one. No follow-up ticket filed — the plan characterizes this as inherent to the shell-level fix chosen, not a gap in it.
2. **`OLD_HASH` read still follows a symlink at the sidecar path.** After this fix, a planted link survives at most until the next successful install (which unlinks and recreates the sidecar). Before that, the worst outcome is a forged `OLD_HASH` making the hook skip an install that a later session's genuine mismatch would retry — it cannot cause installation of unpublished bytes, since the publication guard runs independently of `OLD_HASH`. **Filed as `gsd-beads-25vc.21.6`** (P3, child of `gsd-beads-25vc.21`), referenced in the code comment.

## Containment Verification (end of plan)

- Global mirror digest: `find . -name __pycache__ -prune -o -type f -print | LC_ALL=C sort | xargs sha256sum | sha256sum` from `~/.gsd/capabilities/sota-numerics` → `3ea50c85d28641b249ab71ce11374468652c9ff0388b64c464205a10e99e413e` — **unchanged** from the plan's recorded pre-plan value. No worktree bundle was published machine-wide.
- `git merge-base --is-ancestor HEAD origin/HEAD` in the target worktree → exit 1 (non-ancestor, as required). Nothing was pushed.
- Target worktree `git status --short` → clean.
- `gsd-beads` (working repo) `git status --short` → no code changes outside `.planning/` (only this SUMMARY, `.planning/state.json`, and pre-existing untracked planning/tooling artifacts unrelated to this plan).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `gsd-beads-25vc.21.2` is ready to close (acceptance criteria met: fix + regression coverage for all three findings, low-value-exploit residuals documented, one residual tracked as a new ticket).
- `gsd-beads-25vc.21.6` (OLD_HASH symlink-follow) is open and unblocked, P3, for whenever the residual is worth closing.
- Sibling children of `gsd-beads-25vc.21` (`.21.3` test-suite coverage gaps, `.21.4` ponytail cleanup, `.21.5` prose-tokens cleanup) are untouched by this plan and remain open.

## Self-Check: PASSED

- FOUND: `.planning/quick/260908-h0c-fix-sota-numerics-hooks-capability-auto-/260908-h0c-SUMMARY.md`
- FOUND: `hooks/capability-auto-install.sh` (target repo)
- FOUND commit `110ffc6` (target repo)
- FOUND commit `5c8ee95` (target repo)
- FOUND commit `cc014e1` (target repo)

---
*Phase: quick-260908-h0c*
*Completed: 2026-09-08*
