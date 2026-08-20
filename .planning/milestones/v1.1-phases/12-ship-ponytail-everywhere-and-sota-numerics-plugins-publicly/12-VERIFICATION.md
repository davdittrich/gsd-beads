---
phase: 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
verified: 2026-08-17T18:00:00Z
status: human_needed
score: 15/15 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:

  - test: "Open https://github.com/davdittrich/ponytail-everywhere and https://github.com/davdittrich/sota-numerics in a browser and read the rendered README (not raw markdown)."
    expected: "A stranger with no gsd-beads context can tell what each plugin does, install it, and uninstall it from the README alone (D-09's stated bar — matches the beads-lifecycle/Phase 8 precedent)."
    why_human: "README comprehension by an unfamiliar reader is a judgment call on rendering/clarity, not something grep or a structural heading check can certify. Section presence (7/7 headings, correct order) was verified programmatically; comprehension quality was not, and 12-04-SUMMARY.md explicitly deferred this exact check to a human (its own plan-level `<human-check>`, never executed)."
audit_acknowledged:
  milestone: v1.3
  at: 2026-08-20
  status: human_needed
---

# Phase 12: Ship ponytail-everywhere and sota-numerics plugins publicly Verification Report

**Phase Goal:** `ponytail-everywhere` and `sota-numerics` each get their own public GitHub repo, published exactly as `beads-lifecycle` was in Phase 5-8 (README, LICENSE, `claude plugin validate . --strict`, a real marketplace round trip). `gsd-beads`'s `.claude-plugin/marketplace.json` keeps hosting the shared marketplace, with the two entries switched from local Directory sources to git-sources pointing at the new repos.

**Verified:** 2026-08-17T18:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

All truths below were checked against the live codebase and the two live public GitHub repos independently — not taken from SUMMARY.md claims. Where a SUMMARY.md cited a specific command/output, that command was re-run in this verification session and its output compared.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `davdittrich/ponytail-everywhere` is a public repo whose root IS the plugin root (D-01) | ✓ VERIFIED | `gh repo view` → `visibility: PUBLIC, defaultBranchRef: main, isPrivate: false`; fresh `git clone` shows `.claude-plugin/plugin.json` at repo root |
| 2 | `davdittrich/sota-numerics` is a public repo whose root IS the plugin root (D-01) | ✓ VERIFIED | Same check, same result: `PUBLIC`, `main`, plugin root at repo root |
| 3 | Both new repos' git history is a fresh init — no commit imported from gsd-beads (D-03) | ✓ VERIFIED | `git rev-list --count HEAD` = 1 in both fresh clones |
| 4 | `bash tests/test-session-start.sh` passes from the new repo root, not only inside gsd-beads (both plugins) | ✓ VERIFIED | Re-ran in fresh clones: ponytail 11/11 PASS; sota-numerics 7/7 PASS |
| 5 | `python3 -m unittest tests/test_check_alternatives.py` passes from the sota-numerics repo root (blocking gate's own test survives relocation) | ✓ VERIFIED | Re-ran: `Ran 19 tests ... OK` |
| 6 | `claude plugin validate . --strict` exits 0 from a fresh clone of each pushed repo (D-10, half) | ✓ VERIFIED | Re-ran in both fresh clones: `✔ Validation passed`, exit 0 |
| 7 | Each README carries the seven mandated D-09 sections, in order (What it does, Requirements, Install, Uninstall, Caveats, License, gsd-core) | ✓ VERIFIED | `grep '^## '` on both fresh clones' README.md returns exactly 7 headings, correct order and text |
| 8 | `.claude-plugin/marketplace.json` in gsd-beads resolves `ponytail-everywhere`/`sota-numerics` to `{source: github, repo: davdittrich/...}` objects; `beads-lifecycle` still `"./"` (D-02) | ✓ VERIFIED | Live file read: both entries are github-source objects naming the correct repos, `beads-lifecycle.source` unchanged `"./"`, no `ref`/`sha` pin (matches Plan 03's explicit no-pin decision) |
| 9 | `claude plugin install` fetches each plugin from its own repo via the real, pushed `gsd-beads` marketplace and `claude plugin uninstall` removes it cleanly (D-10, round-trip half) | ✓ VERIFIED (coincidental-reliance) | Independently re-ran (not just trusted SUMMARY): first attempt failed with `Permission denied (publickey)` — confirms the SSH-clone quirk 12-03-SUMMARY documented is real on this machine. Re-ran with the documented `GIT_CONFIG_COUNT`/`KEY_0`/`VALUE_0` HTTPS-rewrite workaround — both installs succeeded, both appeared in `claude plugin list`, both uninstalled cleanly, `beads-lifecycle@gsd-beads` untouched throughout. See reliance note below. |
| 10 | `gsd-beads` tracks no file under `ponytail-everywhere/` or `sota-numerics/`; no dual-copy authoring source survives (D-04) | ✓ VERIFIED | `git ls-files ponytail-everywhere sota-numerics` → 0; `ls -d` on both paths → "No such file or directory" |
| 11 | `.gsd/capabilities/ponytail/` and `.gsd/capabilities/sota-numerics/` at gsd-beads root remain tracked and unchanged — the D-04 carve-out (dogfood copies are a separate concern from the removed plugin subdirectories) | ✓ VERIFIED | `git ls-files .gsd/capabilities/ponytail .gsd/capabilities/sota-numerics` → 12 files present; `check-alternatives.py` present at its expected path; `capability.json`'s plan:post gate command still resolves via `git rev-parse --show-toplevel` in this repo |
| 12 | gsd-beads' CI is green on the commit that performs the removal — no workflow step references a path that no longer exists | ✓ VERIFIED | `gh run list --branch main --limit 3` shows `completed / success` for head SHA `52b53d28b8...` (the removal commit); locally re-ran `bash tests/test-capability-auto-install.sh` → `ALL PASS` |
| 13 | `.github/workflows/ci.yml` and `.github/workflows/release.yml` no longer reference the removed subdirectories | ✓ VERIFIED | `ci.yml` now has exactly one step (`capability-auto-install smoke test`), no vendored-copy-parity or ponytail-subdirectory step; `release.yml`'s zip step lists exactly 6 arguments (`.claude-plugin`, `hooks`, `.agents/skills`, `.gsd`, `README.md`, `LICENSE`), none naming `ponytail-everywhere/`; repo-wide grep for `ponytail-everywhere/` or `sota-numerics/` (excluding `.planning/` history docs) found zero stale references |
| 14 | `v1.2.0` tag is untouched and no new gsd-beads tag/release was created (D-06) | ✓ VERIFIED | `git tag --list 'v*'` → `v1.0, v1.1.1, v1.2.0` (unchanged); `gh release list` → only the pre-existing `v1.2.0`/`v1.1.1` releases, nothing new |
| 15 | Neither new plugin has a release archive (D-07); `gsd-beads`' release workflow still builds only the beads-lifecycle archive (D-08, corrected form) | ✓ VERIFIED | No release exists for either new repo (they have no `.github/workflows/release.yml` of their own per the plan); gsd-beads' `release.yml` zip step unchanged in intent (6 args, all beads-lifecycle content) |
| 16 | A stranger can evaluate, install, and uninstall each plugin from its README alone (D-09's comprehension bar) | ⚠️ deferred to human | Structural check (heading presence/order) passed (truth #7); comprehension of *rendered* GitHub markdown by an unfamiliar reader cannot be verified by grep — routed to Human Verification below, per the plan's own unactioned `<human-check>` |

**Score:** 15/15 structurally/behaviorally verifiable truths verified (1 additional truth is a human-judgment README-comprehension check, tracked separately and not counted against the score per the verifier's behavior-vs-presence split)

### Reliance Note (advisory — truth #9)

Truth #9's evidence path (SSH clone failing, HTTPS env-var rewrite succeeding) depends on this specific machine's git auth configuration (`gh` HTTPS-only, no registered SSH key) — not a property gsd-beads' code declares or defaults. On a machine with a registered SSH key, the same `claude plugin install` command would succeed via the hardcoded `git@github.com:` URL without the workaround. This is flagged `undeclared-precondition`: the round trip *works*, but its success path is dependent on host git configuration that no artifact in this phase declares or normalizes. Not a phase gap — `claude plugin install`'s SSH-URL behavior is upstream (Claude Code CLI), out of this phase's scope — but worth carrying forward if a CI-based install verification is ever added (a CI runner may have different git-auth defaults than this workstation).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `davdittrich/ponytail-everywhere` (public GitHub repo) | Public, `main` branch, plugin root at repo root | ✓ VERIFIED | Confirmed live via `gh repo view` + fresh clone |
| `davdittrich/sota-numerics` (public GitHub repo) | Public, `main` branch, plugin root at repo root | ✓ VERIFIED | Confirmed live via `gh repo view` + fresh clone |
| `.claude-plugin/marketplace.json` (gsd-beads) | Two github-source entries, one Directory source unchanged | ✓ VERIFIED | Read live file, matches Plan 03's claimed diff exactly |
| `.github/workflows/ci.yml` (gsd-beads) | No reference to removed subdirectories | ✓ VERIFIED | One step remains, self-contained |
| `.github/workflows/release.yml` (gsd-beads) | No reference to removed subdirectories | ✓ VERIFIED | 6 of original 9 zip args remain, correctly trimmed |
| `hooks/capability-auto-install.sh` (gsd-beads) | Comments re-anchored, no executable-line change | ✓ VERIFIED | Grep shows no stale `ponytail-everywhere/` path text; smoke test still passes |
| `ponytail-everywhere/`, `sota-numerics/` (gsd-beads, should NOT exist) | Removed entirely from tracking and disk | ✓ VERIFIED | Confirmed absent both from `git ls-files` and filesystem |
| `.gsd/capabilities/ponytail/`, `.gsd/capabilities/sota-numerics/` (gsd-beads, should still exist) | Untouched dogfood bundles | ✓ VERIFIED | 12 tracked files present, gate script resolves |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `marketplace.json` `ponytail-everywhere.source` | `davdittrich/ponytail-everywhere` | `{source: github, repo: ...}` | ✓ WIRED | Repo exists, public, matches name exactly |
| `marketplace.json` `sota-numerics.source` | `davdittrich/sota-numerics` | `{source: github, repo: ...}` | ✓ WIRED | Repo exists, public, matches name exactly |
| `marketplace.json` `beads-lifecycle.source` | gsd-beads repo root | `"./"` (unchanged) | ✓ WIRED | `beads-lifecycle@gsd-beads` still installed/enabled throughout this verification's install/uninstall cycles |
| `.gsd/capabilities/sota-numerics/capability.json` plan:post gate command | `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (this repo) | `$(git rev-parse --show-toplevel)/.gsd/capabilities/...` | ✓ WIRED | Path exists, command pattern intact, unaffected by the plugin-subdirectory removal (D-04's carve-out holds) |
| `tests/test-session-start.sh` `REPO_ROOT` (both extracted repos) | new repo root (one-level climb, not two) | relocation-path fix | ✓ WIRED | Both fresh-clone smoke tests pass, confirming the climb-depth fix landed correctly |

### Requirements Coverage (D-01..D-10, phase-local per 12-CONTEXT.md)

| Requirement | Source Plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| D-01 | 12-01, 12-02 | Each plugin gets its own public repo, not a subdirectory | ✓ SATISFIED | Both repos live, public, verified |
| D-02 | 12-03 | Marketplace stays in gsd-beads; new entries become git sources | ✓ SATISFIED | Live marketplace.json confirmed |
| D-03 | 12-01, 12-02 | Fresh init, no history extraction | ✓ SATISFIED | 1 commit each, confirmed |
| D-04 | 12-04 | Subdirectories removed; root `.gsd/capabilities/` untouched | ✓ SATISFIED | Confirmed both halves |
| D-05 | 12-01, 12-02 | Independent versioning per repo | ✓ SATISFIED | Each `plugin.json` carries its own `0.1.0`; no coupling to gsd-beads version; marketplace source unpinned (resolves live HEAD, not a version number) |
| D-06 | 12-04 | `v1.2.0` left alone; no gsd-beads mandate to re-tag | ✓ SATISFIED | Tag list unchanged, no new release |
| D-07 | 12-01, 12-02 | Neither new plugin needs a release archive | ✓ SATISFIED | No release exists for either new repo |
| D-08 | 12-04 | `release.yml` needs "no change" — CORRECTED by 12-04 to "needs 3-arg trim"; corrected form verified | ✓ SATISFIED (as corrected) | 12-04-SUMMARY explicitly documents the CONTEXT.md premise was wrong; verifier confirms the corrected `release.yml` is now internally consistent (6 remaining args, none dangling) |
| D-09 | 12-01, 12-02 | README full-structure parity with beads-lifecycle | ⚠️ STRUCTURALLY SATISFIED, comprehension unverified | 7/7 sections present and ordered correctly in both repos; the "stranger can evaluate/install/uninstall" bar itself needs human eyes on rendered markdown |
| D-10 | 12-01, 12-02, 12-03, 12-04 | `validate --strict` clean + real marketplace round trip | ✓ SATISFIED | Validate confirmed on fresh clones; round trip independently re-run against the live pushed marketplace by this verifier (not just SUMMARY-trusted) |

No orphaned requirements: all D-01..D-10 IDs from 12-CONTEXT.md appear in at least one plan's `requirements` frontmatter and were checked above.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `hooks/capability-auto-install.sh` (both new repos + gsd-beads) | comment lines | Claims a "byte-identical sibling copy" exists across repos, with no CI mechanism enforcing it post-split | ⚠️ Warning (carried from 12-REVIEW.md WR-01, independently confirmed: the pre-phase `ci.yml` step that `cmp`'d the two copies was correctly removed, and nothing replaces it) | A future edit to either copy can silently drift undetected by any CI in either repo. Non-blocking for this phase's goal (the goal was publication, not drift-proofing) but worth a follow-up ticket. |
| `.claude-plugin/marketplace.json` | `source` objects | No `ref`/tag pin on the two new github sources | ℹ️ Info (carried from 12-REVIEW.md IN-01, independently confirmed, and matches Plan 03's explicit deliberate no-pin decision) | Every install resolves the current default-branch HEAD of the external repo; acceptable per D-05/D-06's stated intent while both repos are single-owner and immature. |

Neither finding blocks the phase goal (public availability + validated round trip); both were already surfaced by 12-REVIEW.md and are reproduced here for completeness, not newly discovered.

### Human Verification Required

### 1. README comprehension by a stranger (D-09's stated bar)

**Test:** Open `https://github.com/davdittrich/ponytail-everywhere` and `https://github.com/davdittrich/sota-numerics` in a browser (rendered GitHub markdown, not raw text). Read only the README.
**Expected:** Without any other context, you can tell (a) what the plugin does, (b) how to install it, (c) how to uninstall it — matching the bar `beads-lifecycle`'s README set in Phase 8.
**Why human:** This is a judgment call about clarity/rendering quality that structural heading checks (already passed, see truth #7) cannot certify. 12-04-SUMMARY.md explicitly names this its own unexecuted `<human-check>` item — it was never performed by any executor or reviewer, only deferred.

## Gaps Summary

No blocking gaps. All 15 structurally/behaviorally checkable truths were independently re-verified against the live codebase, the live GitHub repos, and a live re-run of the marketplace install/uninstall round trip (not merely trusted from SUMMARY.md). The one remaining item — README comprehension by an unfamiliar reader — is inherently a human-judgment check that was correctly identified and deferred by the executor but never actually performed by anyone; it routes to human verification rather than blocking phase completion.

---

_Verified: 2026-08-17T18:00:00Z_
_Verifier: Claude (gsd-verifier)_
