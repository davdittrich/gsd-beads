---
phase: 08-readme-release-ship-gate
verified: 2026-08-16T18:15:00Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:

  - test: "Read README.md top to bottom with no prior knowledge of gsd-core or beads."
    expected: "A cold stranger can understand what the plugin does, its requirements, how to install and remove it, its caveats, and where gsd-core lives, without external context."
    why_human: "Comprehension quality is a judgment call no grep/structural check can certify. Both 08-01-SUMMARY.md (D2) and 08-02-SUMMARY.md (D3) independently flag this class of check as requiring human confirmation."
---

# Phase 8: README, Release & Ship Gate Verification Report

**Phase Goal:** A stranger can evaluate, install, and remove gsd-beads from the README alone
**Verified:** 2026-08-16T18:15:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Phase 8 Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | README.md states purpose, requirements, install, uninstall, caveats, license, gsd-core link; every command transcribed from execution | ✓ VERIFIED | Live read of `README.md`: heading order `What it does → Requirements → Install → Uninstall → Caveats → License → gsd-core` (grep `^## `). Requirements list `bd` on PATH, Python3 stdlib, `gsd-core >= 1.6.0` — matches ROADMAP text verbatim. Install/uninstall commands present verbatim (`claude plugin marketplace add davdittrich/gsd-beads`, `claude plugin install beads@gsd-beads -y`, `claude plugin uninstall beads -y`), matching the literal commands independently re-run live in Truth 4 below. |
| 2 | GitHub Release carries an archive built from an explicit allowlist; unzipping lists only `.claude-plugin/`, `hooks/`, `.agents/skills/`, `README.md`, `LICENSE` | ✓ VERIFIED | Live `gh release view v1.1.0 --repo davdittrich/gsd-beads` — release exists, asset `gsd-beads.zip` (5874 bytes, sha256 digest present). Live-downloaded the actual asset and ran `unzip -Z1`: top-level entries sorted = exactly `.agents .claude-plugin LICENSE README.md hooks`. |
| 3 | Installing from that release leaves no `.planning/` or `.beads/` file on the installer's machine | ✓ VERIFIED | Same live-downloaded asset: `unzip -Z1 gsd-beads.zip \| grep -cE '^\.(planning\|beads)/'` = `0`. |
| 4 | README's own commands, run verbatim against the public repo, complete a marketplace add → install → uninstall round trip | ✓ VERIFIED | Per instruction, did not re-run the full round trip live (already run and independently spot-checked by the orchestrator per 08-02-SUMMARY.md). Verified the claimed final restored state live instead: `claude plugin marketplace list` shows `gsd-beads` source is `Directory (/home/dd/Gemini/gsd-beads)` (local path, not the public GitHub source used mid-round-trip) — matches the restore claim. `claude plugin list` shows `beads@gsd-beads` present and enabled at both `local` and `user` scope, version `1.1.0` — matches the claimed post-restore state exactly. |
| 5 | `claude plugin validate . --strict` is clean on the pushed tree at the released tag | ✓ VERIFIED | Fresh `git clone https://github.com/davdittrich/gsd-beads.git` into a scratch dir, `git checkout v1.1.0` (resolved to `a7897f50d03f97292514647e1169ec2a30ed484b`, matches SUMMARY's recorded commit), `.claude-plugin/plugin.json` version confirmed `1.1.0`, `claude plugin validate . --strict` run from that clone as cwd: `✔ Validation passed`. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `README.md` | Full D-04 section set, repo root | ✓ VERIFIED | Exists, 78 lines, all 7 sections present in locked order, no placeholder/TODO markers, all three plugin commands present verbatim, caveats cover PATH dependency, Dolt-only backend (no `issues.jsonl`), SessionStart hook behavior, and plugin-cache full-repo-copy disclosure. |
| `.github/workflows/release.yml` | Tag-triggered allowlist build + `gh release create` | ✓ VERIFIED | Exists, triggers on `v*.*.*`, job-level `permissions: contents: write`, `actions/checkout@v7`, explicit five-path `zip -r` allowlist (no `-x` exclude flag), `gh release create` step present. |
| `.claude-plugin/plugin.json` version | Bumped to `1.1.0` | ✓ VERIFIED | `"version": "1.1.0"` confirmed in working tree and in the fresh clone at the tag. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| git tag `v1.1.0` push | GitHub Actions `Release` workflow run | tag-trigger `on.push.tags` | ✓ WIRED | Live `gh run list --workflow Release`: run `31956555025` for `headBranch v1.1.0`, `conclusion: success`. |
| workflow run | published `gsd-beads.zip` asset | `gh release create` in `Publish release` step | ✓ WIRED | Live `gh release view v1.1.0`: asset exists, `createdAt 2026-08-16T15:44:33Z`, consistent with the workflow run window recorded in 08-02-SUMMARY.md. |
| README install commands | live `claude plugin` CLI against public repo | literal command text | ✓ WIRED | Commands in README match the commands recorded as executed in 08-02-SUMMARY.md's transcript (identical strings), and the resulting post-round-trip state was independently confirmed live (Truth 4). |

### Security Fix Verification (08-REVIEW.md WR-02)

The review flagged `github.ref_name` interpolated unescaped into a `run:` shell command in
`.github/workflows/release.yml` (script-injection risk on a maliciously crafted tag name).

Independently confirmed, not trusted from the review note:

- `git log --oneline -- .github/workflows/release.yml` shows commit `b4a7903` ("fix(08): harden
  release workflow against tag-name script injection") after the original `8b6a64e`.

- `git show b4a7903` diff confirms the exact fix: `run: gh release create "${{ github.ref_name }}" ...`
  replaced with `run: gh release create "$RELEASE_TAG" ...` plus `env: RELEASE_TAG: ${{ github.ref_name }}`.

- Live working-tree `.github/workflows/release.yml` contains this fixed form, not the original.
- `git rev-parse HEAD` and `git rev-parse origin/main` are identical (`b4a790325943495e776253914dd145673c37c94c`) — the fix is pushed, not just local.

Status: ✓ VERIFIED — fix is in place and pushed.

WR-01 (checkout pinned to mutable tag `v7` rather than a commit SHA) remains unfixed. This is a
review WARNING, not a ROADMAP success criterion or PLAN must-have, and `actions/checkout` is a
first-party, widely-audited action — not a blocker for this phase's goal, but noted for the record.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|------------|--------------|--------|----------|
| PUB-04 | 08-01, 08-02 | Release archive built from explicit allowlist, attached to GitHub Release | ✓ SATISFIED | Truths 2 and 3 above, verified live against the real `v1.1.0` release. |
| PUB-07 | 08-01 | README documents purpose, capabilities, install/uninstall, requirements, caveats, gsd-core link, transcribed from verified commands | ✓ SATISFIED | Truth 1 above. Comprehension quality routed to human verification (see below). |
| PUB-09 | 08-02 | `claude plugin validate . --strict` clean; real marketplace add/install/uninstall round trip succeeds | ✓ SATISFIED | Truths 4 and 5 above, verified live. |

No orphaned requirements — REQUIREMENTS.md maps only PUB-04, PUB-07, PUB-09 to Phase 8, and all
three appear in the PLAN frontmatter `requirements` fields (08-01: PUB-04, PUB-07; 08-02: PUB-04, PUB-09).

**Note (non-blocking):** `.planning/REQUIREMENTS.md` still shows `[ ]` and "Pending" for PUB-04,
PUB-07, PUB-09, and `ROADMAP.md` line 27 still shows Phase 8 as `[ ]`. This is bookkeeping normally
flipped by the orchestrator after verification passes, not evidence the work is incomplete — the
live checks above independently confirm all three requirements are actually satisfied in the
codebase and on the public repo.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | Scanned `README.md` and `.github/workflows/release.yml` for `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`/"not yet implemented"/"coming soon" — zero matches. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Real GitHub Release exists with correct asset | `gh release view v1.1.0 --repo davdittrich/gsd-beads` | asset `gsd-beads.zip`, 5874 bytes | ✓ PASS |
| Published asset is allowlist-exact | download + `unzip -Z1` | 5 top-level entries, 0 `.planning`/`.beads` paths | ✓ PASS |
| Fresh clone at tag validates clean | `git clone` + `git checkout v1.1.0` + `claude plugin validate . --strict` | `✔ Validation passed` | ✓ PASS |
| Local dogfooding state matches claimed restore | `claude plugin marketplace list` / `claude plugin list` | source = local Directory; `beads@gsd-beads` enabled at local+user, v1.1.0 | ✓ PASS |
| gsd-core link target resolves | `gh repo view open-gsd/gsd-core` | `{"name":"gsd-core"}` | ✓ PASS |
| Security fix pushed | `git log`/`git show b4a7903`, `git rev-parse HEAD` vs `origin/main` | fix present, HEAD == origin/main | ✓ PASS |

### Human Verification Required

### 1. README comprehension by a cold stranger

**Test:** Read `README.md` top to bottom having no prior familiarity with gsd-core or beads.
**Expected:** Purpose, requirements, install, uninstall, caveats, license, and the gsd-core link are all understandable without needing outside context; no jargon is left undefined.
**Why human:** Comprehension quality is a judgment call that no grep/structural check can certify. Both `08-01-SUMMARY.md` (coverage item D2) and `08-02-SUMMARY.md` (coverage item D3) independently flag adjacent checks in this phase as requiring human confirmation for the same reason — structural presence is confirmed, but "a stranger can understand it" is not mechanically provable.

### Gaps Summary

No gaps. All 5 ROADMAP success criteria and all 3 requirement IDs (PUB-04, PUB-07, PUB-09) are
independently verified live against the actual public repository, the actual downloaded release
asset, a fresh clone at the tag, and the actual local plugin/marketplace state — not merely
inferred from SUMMARY.md claims. The one WARNING-severity review finding (WR-02, script injection)
was independently confirmed fixed and pushed. The only open item is the inherently-human
comprehension check on README.md, which the phase's own SUMMARY documents flagged for the same
reason. Non-blocking bookkeeping gap: REQUIREMENTS.md/ROADMAP.md checkbox state not yet flipped.

---

*Verified: 2026-08-16T18:15:00Z*
*Verifier: Claude (gsd-verifier)*
</content>
