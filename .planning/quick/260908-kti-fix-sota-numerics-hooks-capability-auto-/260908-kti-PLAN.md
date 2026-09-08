---
beads_epic: gsd-beads-25vc.21.6
phase: quick-260908-kti
plan: 01
type: execute
wave: 1
depends_on: []
target_repo: /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013
target_branch: feat/extended-sota-definition
files_modified:
  - hooks/capability-auto-install.sh
  - tests/test-capability-auto-install.sh
  - CHANGELOG.md
autonomous: true
requirements: [gsd-beads-25vc.21.6]

estimate:
  tokens: 30000
  raw_tokens: 30000
  tasks: 1
  confidence: low

must_haves:
  truths:
    - "A symlink planted at the sidecar path, pointing at content equal to the bundle's real current digest, does not make the hook skip the install."
    - "A regular-file sidecar holding the bundle's current digest still takes the unchanged-bundle fast path, byte-for-byte the prior behaviour (case I1)."
    - "The hook no longer carries a comment claiming the read side is unfixed."
  artifacts:
    - "hooks/capability-auto-install.sh — OLD_HASH read guarded against a symlinked STATE_FILE"
    - "tests/test-capability-auto-install.sh — new case I7, red before the hook change"
    - "CHANGELOG.md — the 0.2.0 sidecar paragraph covers the read side as well as the write side"
  key_links:
    - "The `[ ! -L ]` guard and case I7: I7 is the only test that fails if the guard is dropped."
    - "The success branch's residual comment and the guard: the comment must describe what the code now does, not what it used to defer."
---

<objective>
Close `gsd-beads-25vc.21.6`: the `OLD_HASH` read in `hooks/capability-auto-install.sh` still
follows a symlink planted at the sidecar path, so an attacker with write access to
`${GSD_HOME:-$HOME}/.gsd/` can supply an arbitrary "already installed" digest. Read the sidecar
only when it is a regular file, and pin the property with a regression case.

Purpose: `gsd-beads-25vc.21.2` closed the write side (unlink-and-recreate) and explicitly left
the read side open, recorded in a code comment. That comment is the last false statement in the
file once this lands, so it goes with the fix.
Output: one commit on `feat/extended-sota-definition` carrying the guard, case I7, and the
CHANGELOG sentence.
</objective>

<target_repo>
## READ THIS BEFORE THE FIRST EDIT — the files you edit are NOT in this repository

Every `<files>` path in this plan is **relative to**:

```
/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013
```

That is a checkout of `https://github.com/davdittrich/sota-numerics.git` on branch
`feat/extended-sota-definition` (currently clean, HEAD `ce855f9`). It is a **separate
repository** that happens to sit under this project's directory tree. `hooks/`, `tests/` and
`CHANGELOG.md` mean **that** repository's copies. This repository (`gsd-beads`) has files with
some of the same names; they are not the targets.

Concretely: every edit, every `git commit`, and every `<verify>` command runs with that
directory as the working directory. The Bash tool resets the working directory between calls, so
prefix each command:

```
cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && <command>
```

The only files this plan writes into `gsd-beads` are this `PLAN.md` and its `SUMMARY.md`, both
under `.planning/quick/260908-kti-fix-sota-numerics-hooks-capability-auto-/`.

**Working-tree hazard.** Claude Code loads any in-tree `.claude-plugin/plugin.json` as a plugin,
and this bundle's own `SessionStart`/`SubagentStart` hooks run the very script this plan edits,
which installs the bundle at global scope once the repository tracks and publishes it. A commit
in this worktree can therefore publish these bytes machine-wide at the next subagent spawn. What
keeps this plan clear of that: it touches nothing under `.gsd/capabilities/`, so the bundle
digest the hook compares against does not move and no reinstall is triggered. The last
`<verify>` check asserts exactly that about the commit rather than assuming it.
</target_repo>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Read `bd show gsd-beads-25vc.21.6` for the ticket's own statement of the mechanism, the bounded
impact, the candidate fix, and the suggested test case. The plan below is that candidate fix; if
the ticket and this plan disagree, the ticket wins and you stop and say so.

Facts already established, do not re-derive:

- `hooks/capability-auto-install.sh:124` sets `STATE_FILE`, `:126-127` read it, `:135` is the
  fast path `[ "$NEW_HASH" = "$OLD_HASH" ] && exit 0`.
- The write side is already fixed (commit `cc014e1`, `rm -f "$STATE_FILE"` before the `printf`
  at the end of the success branch) and pinned by case I6.
- Case I1 (`tests/test-capability-auto-install.sh:739-744`) already pins the regular-file fast
  path: two runs over an unchanged bundle produce exactly one install. That is the "preserve
  existing behaviour" guarantee; this plan adds no second test for it.
- Case D0 (end of the test file) greps the hook for its refusal messages and requires each to
  appear in `README.md`. This change adds **no** refusal message, so `README.md` is not touched
  and D0 keeps passing. Do not add a refusal for this case — a planted link is handled silently
  by installing, which is the safe direction.
- CI runs four commands (`.github/workflows/ci.yml`); they are the `<verify>` block below.
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: Refuse to read a symlinked sidecar, and pin it with case I7</name>
  <files>tests/test-capability-auto-install.sh, hooks/capability-auto-install.sh, CHANGELOG.md</files>

  <read_first>
Read `hooks/capability-auto-install.sh` lines 115-137 (the `STATE_FILE` block through the fast
path) and lines 300-330 (the success branch and its residual comment). Read
`tests/test-capability-auto-install.sh` lines 196-225 (`new_sandbox`, `run_hook`, `installs`,
`sidecar` helpers) and lines 800-815 (case I6, whose shape case I7 follows).
  </read_first>

  <behavior>
    Drive this test-first. Write case I7, run the suite, and confirm it is red **for the right
    reason** before touching the hook.

    Case I7, appended immediately after case I6 in `tests/test-capability-auto-install.sh`:

    - `new_sandbox i7`, then `run_hook`; assert `[ "$(installs)" = 1 ]` as the precondition, so a
      sandbox that fails to install for an unrelated reason reports as a precondition failure
      rather than as a passing guard.
    - Capture the digest the successful install just recorded: `REAL_HASH="$(cat "$(sidecar)")"`.
      This is the bundle's true current hash, which is exactly what an attacker would need to
      plant in order to forge a match.
    - Write it to a file the hook does not own (`printf '%s' "$REAL_HASH" > "$SB/forged"`,
      matching the no-trailing-newline form the hook itself writes) and replace the sidecar with
      a link to it: `ln -sfn "$SB/forged" "$(sidecar)"`.
    - `run_hook` again and assert `[ "$(installs)" = 2 ]`. Fail message names the property, not
      the mechanism: a sidecar symlink holding the real hash took the fast path.
    - Add nothing else. Do not re-assert that the sidecar is a regular file afterwards or that
      the link's target is intact — case I6 already pins both, over the identical write-side code
      path, and a second copy would only be a second thing to update.
    - Head the case with a short comment saying what it adds over I6: I6 pins the write, I7 pins
      the read, and the read is what decides whether the install happens at all.

    RED evidence: with only the test added,
    `bash tests/test-capability-auto-install.sh` must fail on I7 and exit non-zero, because the
    unguarded `cat` follows the link, reads `REAL_HASH` into `OLD_HASH`, matches `NEW_HASH`, and
    exits at the fast path with `installs` still 1. Capture that transcript for the SUMMARY. A
    green run at this point means the test is not testing anything — stop and diagnose.
  </behavior>

  <action>
Step 1 — write case I7 exactly as `<behavior>` describes. Run
`bash tests/test-capability-auto-install.sh`, capture the red output.

Step 2 — the hook change, `hooks/capability-auto-install.sh` line 127. The read currently tests
readability only, which is true of a symlink to a readable file. Add a symlink test in front of
it in the same one-line `&&` chain, so the assignment runs only for a non-symlink readable path
and `OLD_HASH` otherwise stays the empty string it was initialised to on line 126. Keep the
existing `2>/dev/null` on the substitution and keep the chain on one line; do not convert it to
an `if` block and do not touch line 126 or lines 128-135.

Only two operators are involved: a `!`-negated `-L` test on `$STATE_FILE`, joined by `&&` to the
existing `-r` test and assignment. Use POSIX `test` brackets as the rest of the file does — bash
3.2 still has to run this.

Step 3 — a short comment directly above that line stating, in this order: a symlink at the
sidecar path is read as no recorded hash rather than followed; the reason is that an attacker
who can write in that directory could otherwise point the link at the bundle's current digest
and make the fast path fire, switching the auto-install off without touching the bundle;
"no recorded hash" is the fail-safe direction because it installs rather than skips; and the
suppression does not persist, because the successful install unlinks and recreates the sidecar
as a regular file. Add one sentence recording the residual honestly: the `-L` test and the `cat`
are two syscalls, so a racing attacker could still swap a regular file for a link between them,
which is the same unclosable window already recorded on the write side and for the same reason
(no shell offers `O_NOFOLLOW`). Do not cite a ticket id in this comment — it describes present
behaviour, not a deferral; the ticket belongs in the commit message.

Step 4 — delete the stale residual paragraph in the success branch, currently lines 319-324, the
one that describes the read as still following a planted link and names the tracking ticket. It
is false once step 2 lands. Leave the paragraph above it (the unlink-and-recreate race window)
exactly as it is — that residual is still real. Adjust nothing else in that comment block.

Step 5 — `CHANGELOG.md`, the `## 0.2.0` paragraph at lines 115-118 that already describes the
sidecar being unlinked and recreated. Append one sentence to that same paragraph — do not start
a new one, it is the same subject — saying the sidecar is now also only read when it is a
regular file, so a link planted to hold the bundle's current digest makes the hook install
rather than take the unchanged-bundle fast path. Match the paragraph's existing voice. Do not
add a version heading; 0.2.0 is unreleased.

Do not touch `README.md`, `hooks/session-start.sh`, `hooks/hooks.json`, or any other test file.

Commit everything as one commit, `fix(hooks): read the sidecar only when it is a regular file`,
with a body that states the mechanism (a planted link could supply an attacker-chosen `OLD_HASH`
and, matched against `NEW_HASH`, suppress the install), the fix, the fail-safe direction, the
residual TOCTOU window that stays, and the ticket
<!-- planner-discipline-allow: gsd-beads-25vc.21.6 -->
`gsd-beads-25vc.21.6`. No `Co-Authored-By` trailer, no AI attribution, no emoji.
  </action>

  <verify>
    <automated>cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && bash tests/test-session-start.sh && bash tests/test-capability-auto-install.sh && bash tests/test-gate-script-resolution.sh && python3 -m unittest tests/test_check_alternatives.py</automated>
    <automated>cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && bash tests/test-capability-auto-install.sh | grep -q 'I7'</automated>
    <automated>cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && grep -n 'OLD_HASH=' hooks/capability-auto-install.sh | grep -q -- '-L'</automated>
    <automated>cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && [ "$(grep -c 'gsd-beads-25vc\.21\.6' hooks/capability-auto-install.sh)" = 0 ]</automated>
    <automated>cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && [ -z "$(git status --porcelain)" ]</automated>
    <automated>cd /home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013 && CHANGED="$(git show --name-only --format= HEAD)" && [ -z "$(printf '%s\n' "$CHANGED" | grep '^\.gsd/')" ]</automated>
  </verify>

  <done>
`bash tests/test-capability-auto-install.sh` prints `ALL PASS` and its output includes a passing
I7; the other three CI commands pass. Case I7 is red on the pre-change hook and green after —
both transcripts captured in the SUMMARY. The `OLD_HASH` assignment on line 127 is reached only
for a non-symlink readable `STATE_FILE`, and the comment above it records the fail-safe direction
and the surviving TOCTOU window. The hook contains no remaining reference to the ticket id. The
0.2.0 sidecar paragraph in `CHANGELOG.md` covers the read side. One commit, clean worktree, no
`Co-Authored-By` trailer, and the commit touches no path under `.gsd/capabilities/`.
  </done>

  <reversibility rating="reversible">One `&&`-joined test, one test case, one comment swap and one
  CHANGELOG sentence; `git revert` restores the prior behaviour exactly and case I7 goes red
  again, which is the point.</reversibility>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| `${GSD_HOME:-$HOME}/.gsd/` -> hook | Any process able to write in the user's `.gsd/` directory controls the bytes the hook reads as its record of what is installed. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-kti-01 | Spoofing | `OLD_HASH` read, `capability-auto-install.sh:127` | low | mitigate | Read the sidecar only when it is not a symlink, so a planted link cannot supply a forged "already installed" digest; pinned by case I7. |
| T-kti-02 | Tampering | `[ ! -L ]` then `cat`, same line | low | accept | Two syscalls cannot be made one in shell; no `O_NOFOLLOW` is available. Same window already accepted on the write side, and the threat model already grants the attacker write access to that directory. Recorded in the code comment, not claimed away. |
| T-kti-03 | Denial of Service | fast path, `capability-auto-install.sh:135` | low | accept | A link left in place makes every session reinstall until the first success replaces it with a regular file. Reinstalling is the safe direction and self-heals in one run. |

No package-manager installs in this plan, so no legitimacy gate applies.
</threat_model>

<verification>
The four CI commands from `.github/workflows/ci.yml` are the whole gate; they are reproduced in
the task's `<verify>` block. The load-bearing evidence beyond "green" is the red-then-green
transcript for case I7: green-only proves the suite runs, not that the guard is doing anything.
</verification>

<success_criteria>
`gsd-beads-25vc.21.6` is closable on evidence: the forged-sidecar path installs, the regular-file
fast path is untouched (case I1 still passes), the hook's comments describe what the code now
does, and the whole suite is green on a clean worktree.
</success_criteria>

<output>
Create `.planning/quick/260908-kti-fix-sota-numerics-hooks-capability-auto-/260908-kti-SUMMARY.md`
in the **gsd-beads** repository when done, carrying both transcripts (I7 red, then the full
green run) and the accepted residuals T-kti-02 and T-kti-03 verbatim from the register above, so
the ticket's closure comment can cite them.
</output>
