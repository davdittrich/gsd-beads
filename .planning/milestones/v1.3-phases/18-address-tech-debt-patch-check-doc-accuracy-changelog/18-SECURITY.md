---
phase: 18
slug: address-tech-debt-patch-check-doc-accuracy-changelog
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-20
---

# Phase 18 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| repo doc → agent runtime instructions | Text copied out of `GSD-CORE-PATCH.md` into `~/.claude/gsd-core/workflows/*.md` becomes instructions a future agent session executes | patch-block markdown |
| this repo → second runtime home | `~/.codex/` is a separate installed runtime this repo does not own and cannot test in CI | patch-block markdown |
| local repo → public `origin` | A destructive ref operation (tag deletion) against a shared, public remote (`davdittrich/gsd-beads`) | git ref state |
| local repo → `bd` issue store | Issue closures are durable project state; `.beads/` is gitignored, so a wrong close is not recoverable from git | bd issue state |
| `sync.py` stdout → agent context | `hooks/lifecycle-dispatch.sh` promotes this module's stdout into `additionalContext`, so every message template becomes text an agent reads as context | log/message strings |
| tracked source → gitignored runtime overlay | The overlay under `.gsd/capabilities/beads/` is what the hook executes; the tracked tree is what CI tests — divergence means the tested code is not the running code | Python source files |
| filesystem → `check_patch` | Reads an arbitrary path supplied via `--path` or resolved from `CLAUDE_CONFIG_DIR` | file path |
| repo → marketplace consumer | `.claude-plugin/marketplace.json` resolves this plugin from the branch, so `plugin.json`'s version string is what an installing consumer sees for code already on `main` | version string |
| CHANGELOG → future maintainer | The changelog is the only durable record of why a behavioral change shipped once the phase directory ages out of working memory | markdown prose |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-18-01-01 | Tampering | Text inserted into `~/.{claude,codex}/gsd-core/workflows/{ship,execute-plan}.md` | high | mitigate | Insert-only from `GSD-CORE-PATCH.md`'s marker blocks. Live-verified: `check-patch ship-md`/`execute-plan` both report present (v2/v1); `diff` against the independent pre-update backup is byte-empty for `ship.md`. | closed |
| T-18-01-02 | Denial of Service | Unrelated 1.11.0 workflow content silently reverted or deleted by a whole-file copy | high | mitigate | Insert-only edits, byte-equality diff. Live-verified: `wc -l ~/.claude/gsd-core/workflows/ship.md` = 638 (matches target), diff clean. | closed |
| T-18-01-03 | Tampering | Claude-templated instructions installed into the Codex runtime home | medium | mitigate | Explicit cross-home copy prohibition. Live-verified: `grep -c '/gsd-secure-phase' ~/.codex/gsd-core/workflows/ship.md` returns 0. | closed |
| T-18-01-04 | Information Disclosure | Machine-local absolute paths (`$HOME/...`) recorded in a git-tracked SUMMARY | low | accept | Developer's own home directory on their own machine; already recorded throughout `.planning/` and `GSD-CORE-PATCH.md`. No new exposure. | closed |
| T-18-02-01 | Denial of Service | `git push origin :refs/tags/v1.3.0` against a public remote | high | mitigate | Blocking `checkpoint:decision` fired before the command and was answered live by the user (option-a) via `AskUserQuestion`; remote-before-local ordering; no `--force`, no bulk push. Live-verified: `git ls-remote --tags origin \| grep -c v1.3.0` = 0, `v1.3.1` untouched. | closed |
| T-18-02-02 | Tampering | Unintended release publication | medium | mitigate | `release.yml` triggers on tag *pushes*, not deletions. Live-verified: `gh run list --workflow release.yml` shows no run newer than the pre-existing `v1.3.1` release (2026-08-19) — no run triggered by the Phase 18 tag deletion. | closed |
| T-18-02-03 | Repudiation | A live bug silently closed by misidentifying an issue id | medium | mitigate | Mandatory `bd show` identity check against a written id-to-TRUTH mapping table before each close (executor transcript confirms all 4 titles matched). Live-verified: `bd show <id> --json` reports `"status": "closed"` for all four (`gsd-beads-he1/bzl/v43/t7a`). | closed |
| T-18-02-04 | Information Disclosure | Deleting the tag removes public evidence that a withdrawn v1.3.0 existed | low | accept | CHANGELOG and `.planning/STATE.md`/PROJECT.md both record the withdrawal and dereferenced commit `55855cd`. | closed |
| T-18-03-01 | Spoofing | Message text promoted into agent context via `additionalContext` | medium | mitigate | Four changed templates gained only a two-character `⚠ ` prefix; no interpolated field added. Pinned by 4 new RED-then-GREEN tests in `test_sync.py`; deep code review independently confirmed no new interpolation surface. | closed |
| T-18-03-02 | Tampering | Tested code diverging from executed code | high | mitigate | `diff -rq` between tracked plugin tree and gitignored runtime overlay. Live-verified: empty diff, both trees byte-identical. Full suite green at 252 tests from the tracked tree. | closed |
| T-18-03-03 | Repudiation | A silently lost patch that the surfacing rule fails to report | high | mitigate | Both `beads-recall`/`beads-status` SKILL.md rules re-keyed off `check_patch`'s exit code / `"present"`-substring instead of the `⚠` glyph. Deep code review independently traced `check_patch`'s control flow and confirmed `"present"` appears only in the present-case template. | closed |
| T-18-03-04 | Information Disclosure | `check_patch` messages print the probed absolute path and raw exception text | low | accept | Pre-existing, deliberate (WR-03) — names the exact path probed. Unchanged by this plan. | closed |
| T-18-03-05 | Elevation of Privilege | `check_patch` reading an arbitrary `--path` | low | accept | Read-only, no execution of file contents, developer-supplied at a local CLI. Unchanged by this plan. | closed |
| T-18-04-01 | Repudiation | A shipped behavioral change with no changelog record | medium | mitigate | Plan adds the missing TRUTH-03 entry to CHANGELOG 0.4.0. Live-verified: `grep -c check_native_step_dispatch CHANGELOG.md` >= 1. | closed |
| T-18-04-02 | Tampering | Version string misdeclaring what a consumer installs | medium | mitigate | `plugin.json` bumped to `1.4.0`. Live-verified: `git show d389d91 --numstat` shows exactly 1 line changed in `plugin.json`. | closed |
| T-18-04-03 | Tampering | An editing pass silently dropping or reordering existing changelog history | medium | mitigate | Explicit prohibitions against touching 0.3.0-and-earlier sections. Live-verified: `## 0.3.1` and `## 0.3.0` each appear exactly once in CHANGELOG.md. | closed |
| T-18-04-04 | Information Disclosure | Changelog text naming internal identifiers and an upstream PR | low | accept | Repository is public by design; `GSD-CORE-PATCH.md` already names the same PR and identifiers. | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-18-01 | T-18-01-04 | Machine-local absolute paths are the developer's own, already recorded throughout `.planning/`. | Plan 18-01 threat model | 2026-08-20 |
| AR-18-02 | T-18-02-04 | Withdrawal and dereferenced commit recorded in CHANGELOG/PROJECT.md before the ref was removed. | Plan 18-02 threat model, confirmed at checkpoint (option-a) | 2026-08-20 |
| AR-18-03 | T-18-03-04 | Pre-existing, deliberate (WR-03) — names the exact path probed for diagnosability. | Plan 18-03 threat model | 2026-08-20 |
| AR-18-04 | T-18-03-05 | Read-only, local-CLI-only, unchanged by this plan. | Plan 18-03 threat model | 2026-08-20 |
| AR-18-05 | T-18-04-04 | Repository is public by design; identifiers already named elsewhere. | Plan 18-04 threat model | 2026-08-20 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-20 | 17 | 17 | 0 | /gsd-secure-phase (orchestrator, L1 grep-depth verification against implementation; asvs_level: 1 — every mitigate-dispositioned threat live-reverified via direct command re-execution, not just SUMMARY.md claims) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-20
