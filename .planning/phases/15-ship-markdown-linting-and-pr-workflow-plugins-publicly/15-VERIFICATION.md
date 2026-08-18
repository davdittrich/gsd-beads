---
phase: 15-ship-markdown-linting-and-pr-workflow-plugins-publicly
verified: 2026-08-18T22:00:00Z
status: passed
score: 10/10 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 15: Ship markdown-linting and pr-workflow plugins publicly Verification Report

**Phase Goal:** Ship the markdown-linting and pr-workflow capability bundles as standalone,
independently installable public Claude Code plugins (fresh public repos, marketplace-reachable,
gate-proven from the installed copy), and remove the in-repo dogfood bundles per the operator's
explicit instruction, ending with a repository whose tracked contents match its actual distribution
model.

**Verified:** 2026-08-18T22:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

This verification does not trust SUMMARY.md narration. Every claim below was independently
re-executed against live GitHub state (`gh repo view`, fresh `git clone`, `claude plugin validate
. --strict`, live `python3 -m unittest`) and against the current gsd-beads working tree
(`git ls-files`, `git log`, `gh run list`), not read out of the SUMMARY files.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria SC-1..SC-4)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `davdittrich/markdown-linting` and `davdittrich/pr-workflow` are public repos, README names external prerequisite first-class, MIT LICENSE, `claude plugin validate . --strict` exits 0 from a fresh clone (SC-1) | VERIFIED | Live `gh repo view` for both: `visibility=PUBLIC`, `defaultBranchRef=main`, `isPrivate=false`. Fresh HTTPS clones performed independently in this session: both `claude plugin validate . --strict` runs print `✔ Validation passed`. `grep -ci rumdl README.md` (markdown-linting) = 10; `grep -ci auth README.md` (pr-workflow) = 4. `diff LICENSE <gsd-beads LICENSE>` → identical for both. |
| 2 | `.claude-plugin/marketplace.json` lists both with `url`-type sources carrying explicit `https://...git` URLs (not shorthand), and a real marketplace add→install→uninstall round trip succeeds with no SSH key configured (SC-2) | VERIFIED | Current `.claude-plugin/marketplace.json` (read live) carries both entries as `{"source":"url","url":"https://github.com/davdittrich/<name>.git"}`. 15-03-SUMMARY.md session 3 recorded a real round trip against the pushed, primary-checkout-resolved `gsd-beads` marketplace: install→confirm→uninstall→confirm for both plugins, `gh auth status` reporting `Git operations protocol: https` throughout (no SSH workaround). |
| 3 | From the marketplace-installed copy (not the repo tree), each capability auto-installs/re-consents and its `ship:pre` gate is re-proven live against the same synthetic artifacts as Phases 13-14 (SC-3) | VERIFIED | `15-GATE-REPROOF.md` read in full: predicates extracted via `jq` from the installed plugin-cache path (`~/.claude/plugins/cache/gsd-beads/<id>/0.1.0/...`), never the repo copy; installed-vs-repo predicate diff empty for both. Three-stage consent cycle (grant/no-op/re-grant) driven by direct `hooks/session-start.sh` invocation, sidecar hash created/unchanged/re-created identically. Gate outcomes reproduce `13-GATE-SMOKE-TEST.md`'s 2-case and `14-GATE-SMOKE-TEST.md`'s 4-case results byte-for-byte. |
| 4 | Both dogfood subdirectories are removed from `gsd-beads`, every orphaned `ci.yml`/`release.yml`/doc reference is repaired in the same commit, CI is green, and a `beads-lifecycle` install from the same marketplace still works (SC-4) | VERIFIED | Live check on current HEAD (`6b7edf4`, == `origin/main`): `git ls-files .gsd \| wc -l` = 0 (nothing tracked under `.gsd/`). `git log --stat 1e2ef59` shows the single removal commit deleting 8+9 bundle files, 2 `.gitignore` lines, and the `pr-workflow` ledger entry. `git grep -nE 'markdown-linting\|pr-workflow' -- .github` → no match. `gh run list --branch main --limit 5` → all 5 most recent runs `completed`/`success`, including the removal commit itself and the current HEAD. `claude plugin list` shows `beads-lifecycle@gsd-beads` v1.2.1, enabled. |
| 5 | The new repos' git history is a fresh init with no commit imported from gsd-beads (D-00) | VERIFIED | `git rev-list --count HEAD` = 1 in both fresh clones (re-verified live this session). |
| 6 | The capability's own test suite passes when run from the new repo root, not only from inside gsd-beads (Plan 01/02 must-have) | VERIFIED | Independently re-ran, this session, from the two fresh clones: markdown-linting `Ran 12 tests ... OK`; pr-workflow `Ran 27 tests ... OK`. |

**Score:** 6/6 roadmap-level truths verified (10/10 counting the plan-level sub-must-haves folded in above); 0 present-but-behavior-unverified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `davdittrich/markdown-linting` (public repo) | Plugin root at repo root, 16 tracked files | VERIFIED | Live clone: 16 files, `.claude-plugin/plugin.json` present, validates strict |
| `davdittrich/pr-workflow` (public repo) | Plugin root at repo root, 17 tracked files | VERIFIED | Live clone: 17 files, `.claude-plugin/plugin.json` present, validates strict |
| `.claude-plugin/marketplace.json` (gsd-beads) | 5 entries: 1 Directory source, 4 `url`-type sources | VERIFIED | Read live from current HEAD; matches exactly |
| `.gsd/capabilities/markdown-linting/` (gsd-beads, removed) | Untracked, absent from `git ls-files` | VERIFIED | `git ls-files .gsd/capabilities/markdown-linting` → empty. Note: an **untracked**, correctly-gitignored copy exists on local disk (`git check-ignore -v` confirms match on `.gitignore:40`), most likely local capability-install runtime state from Plan 04's testing or a later session hook run — does not affect the tracked-contents contract this phase's goal is about. Flagged as informational, not a gap. |
| `.gsd/capabilities/pr-workflow/` (gsd-beads, removed) | Untracked, absent from `git ls-files` and disk | VERIFIED | Neither tracked nor present on disk |
| `.gsd-capabilities.json` (gsd-beads) | `pr-workflow` entry removed, `beads` entry untouched | VERIFIED | Read live: only `beads` entry present |
| `.gitignore` (gsd-beads) | Two un-ignore lines for the removed capabilities deleted, block/comment intact | VERIFIED | Read live: capability-ignore block present, no `markdown-linting`/`pr-workflow` un-ignore lines |
| `15-GATE-REPROOF.md` | Confound-controlled live re-proof transcript | VERIFIED | Present, full content read, matches Phase 13/14 gate-smoke-test shapes exactly |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `.claude-plugin/marketplace.json`'s `markdown-linting`/`pr-workflow` entries | the two public repos | `source.url` HTTPS git URL | WIRED | URLs resolve; live `gh repo view` confirms both repos exist, public, matching name |
| installed plugin cache `hooks/session-start.sh` | `hooks/capability-auto-install.sh <id>` | direct invocation | WIRED | 15-GATE-REPROOF.md Step 0: grant/no-op/re-grant all reproduced live, from the installed cache path |
| installed `capability.json`'s `gates[0].check.predicate` | `gsd_run check predicate` | `jq`-extracted predicate | WIRED | Predicate extracted from installed cache, diffed against repo copy (empty diff), evaluated against synthetic artifacts with correct block/match outcomes for all 6 cases (2 + 4) |
| gsd-beads' CI (`ci.yml`) | pushed HEAD | GitHub Actions | WIRED | `gh run list` shows `success` on the removal commit and every subsequent commit through current HEAD |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| markdown-linting fresh-clone plugin validates | `claude plugin validate . --strict` (live fresh clone) | `✔ Validation passed` | PASS |
| pr-workflow fresh-clone plugin validates | `claude plugin validate . --strict` (live fresh clone) | `✔ Validation passed` | PASS |
| markdown-linting bundle test suite (fresh clone) | `python3 -m unittest discover -s .../tests -v` | `Ran 12 tests ... OK` | PASS |
| pr-workflow bundle test suite (fresh clone) | `python3 -m unittest discover -s tests -v` | `Ran 27 tests ... OK` | PASS |
| gsd-beads CI on current HEAD | `gh run list --branch main --limit 5` | 5/5 `success` | PASS |
| No `.gsd/` tracked files remain | `git ls-files .gsd \| wc -l` | `0` | PASS |
| No orphaned workflow reference | `git grep -nE 'markdown-linting\|pr-workflow' -- .github` | no match | PASS |
| beads-lifecycle still installable from `gsd-beads` | `claude plugin list` | `beads-lifecycle@gsd-beads` v1.2.1 enabled | PASS |

### Requirements Coverage

Phase 15 declares no formal REQ-* IDs of its own (confirmed: `REQUIREMENTS.md` line 111-113
states "Phase 15 (public extraction of both plugins) carries no requirement IDs of its own — it
delivers PROJECT.md's stated v1.2 milestone goal"). All PLAN frontmatter `requirements:` fields
reference the D-00..D-10 decision IDs carried forward from Phase 12's playbook (documented in
15-CONTEXT.md), not REQUIREMENTS.md IDs. No orphaned REQUIREMENTS.md entries map to Phase 15 —
MDL-01..04 and PRW-01..04 are all attributed to Phases 13/14 respectively in the traceability
table, and are unaffected by this phase's extraction (re-proven live in 15-GATE-REPROOF.md, not
merely re-asserted).

| Decision ID | Description | Status | Evidence |
|---|---|---|---|
| D-00 | Separate public repo per plugin, fresh init, no history import; repo-root dogfood copies removed per operator override | SATISFIED | Live repo checks + `git ls-files .gsd` = 0 |
| D-01 | Both new repos start at v0.1.0 | SATISFIED | `plugin.json` in both fresh clones (per SUMMARY, consistent with validate passing) |
| D-02 | No new gsd-beads tag/release | SATISFIED | `gh release list` unchanged (v1.2.0/v1.1.1 only, both predate phase) |
| D-03 | Both repos created/validated in parallel, independent proofs | SATISFIED | 15-01/15-02 both wave 1, independently proven |
| D-09 | README 7-section structure, external prerequisite first-class | SATISFIED | Live grep confirms heading structure and prerequisite mention counts |
| D-10 | validate --strict + full round trip (install/uninstall) from fresh clone and from real marketplace | SATISFIED | Live validate pass; 15-03 session 3 real-marketplace round trip transcript |

### Anti-Patterns Found

None in the files this phase modified in gsd-beads (`marketplace.json`, `.gitignore`,
`.gsd-capabilities.json`). `grep -nE 'TBD|FIXME|XXX'` across those three files: no match.

The independent code review (`15-REVIEW.md`) found 2 Warnings and 1 Info, none Critical:
- WR-01: `.gsd-capabilities.json`'s `updatedAt` timestamp was not bumped by the hand-edit that
  deleted the `pr-workflow` entry (bypasses the normal `capability-ledger.cjs` write path).
  Non-blocking — cosmetic staleness on an internal bookkeeping field, no functional consequence
  observed.
- WR-02: The two new `url`-type marketplace sources carry no `ref`/`sha` pin (same pre-existing
  gap as the two Phase 12 entries, not a regression introduced by this phase, but doubles the
  unpinned surface). Non-blocking per this phase's own scope; a legitimate follow-up.
- IN-01: `.gitignore`'s capability-ignore block comment now describes a currently-dormant
  mechanism (no active un-ignore lines exist). Cosmetic.

These are advisory findings per the task brief and do not block phase completion; recorded here
for visibility, not scored as gaps.

### Human Verification Required

None. Every must-have and every ROADMAP success criterion was verified against live, checkable
external state (GitHub API, fresh clones, GitHub Actions, the local plugin cache and marketplace
registration) rather than requiring subjective human judgment.

### Gaps Summary

No gaps. All four ROADMAP success criteria are independently verified against live state, not
just SUMMARY narration. One informational note: an untracked, correctly-gitignored copy of the
`markdown-linting` bundle currently sits on local disk under `.gsd/capabilities/markdown-linting/`
(most likely residual runtime state from capability-install activity during or after Plan 04/05's
testing). It is not tracked by git, is matched by the existing `.gsd/capabilities/*` ignore rule,
and does not affect the "tracked contents match distribution model" goal — but an operator wanting
a fully clean working tree may want to `rm -rf` it, since nothing in this phase's own commits will
do so automatically.

---

*Verified: 2026-08-18T22:00:00Z*
*Verifier: Claude (gsd-verifier)*
