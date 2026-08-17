---
phase: 08
slug: readme-release-ship-gate
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-16
---

# Phase 08 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| local git object DB → published `gsd-beads.zip` | The release workflow's zip-build step selects what leaves this repo's working tree and reaches every installer | Repo file contents |
| public git source → local plugin cache | The marketplace add/install flow copies the whole cloned repo onto the installer's machine | Full repo contents (not filtered by the release allowlist) |
| CI job → GitHub API | `GITHUB_TOKEN` creates a public release resource | Auth token scope |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-08-01 | Information Disclosure | `.github/workflows/release.yml` zip step | high | mitigate | Explicit five-path include list; verified against the published asset's own `unzip -Z1` listing this session — exactly `.agents .claude-plugin LICENSE README.md hooks`, zero `.planning`/`.beads` paths | closed |
| T-08-02 | Elevation of Privilege | `release.yml` job token scope | medium | mitigate | Job-level `permissions: contents: write` only, never workflow-wide `write-all` — confirmed in `.github/workflows/release.yml` | closed |
| T-08-03 | Information Disclosure | installer's local plugin cache | low | accept | Claude Code's own documented cache-copy behavior, not controllable from this repo — disclosed in README.md's Caveats section (confirmed: "repository into the installer's local plugin cache") | closed |
| T-08-04 | Tampering | third-party GitHub Action supply chain | medium | mitigate | Only `actions/checkout@v7` (GitHub first-party); `gh` CLI runner-preinstalled; no third-party release action. Non-blocking hardening gap noted (WR-01, 08-REVIEW.md): pinned to a mutable tag, not a commit SHA — below block threshold, tracked not blocking | closed |
| T-08-05 | Information Disclosure | published `gsd-beads.zip` | high | mitigate | Independently verified this session via `gh release view v1.1.0` + downloaded-asset `unzip -Z1` listing, not the workflow source | closed |
| T-08-06 | Spoofing | ship gate evidence | medium | mitigate | Gate A independently re-run this session: fresh `git clone` + `git checkout v1.1.0` + `claude plugin validate . --strict` → passed, from a scratch clone not the working tree | closed |
| T-08-07 | Tampering | this machine's local plugin state | low | mitigate | Pre/post state capture verified this session: `claude plugin marketplace list` shows `gsd-beads` restored to its local Directory source, `beads@gsd-beads` present in `claude plugin list` at local+user scope, matching pre-round-trip state | closed |
| T-08-08 | Information Disclosure | installer's plugin cache holding a full repo copy | low | accept | Documented Claude Code behavior outside this repo's control, disclosed in README.md's Caveats section (same disclosure as T-08-03) | closed |
| T-08-09 | Tampering | `github.ref_name` interpolated into a `run:` shell command | high | mitigate | Script-injection pattern found by code review (08-REVIEW.md); fixed via `env:` indirection (commit `b4a7903`), independently confirmed pushed to `origin/main` during Phase 8 goal verification | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-08-01 | T-08-03 / T-08-08 | Claude Code's marketplace-install flow copies the full source repo (not the release allowlist) into `~/.claude/plugins/cache/` on the installer's machine — a low-severity, local-only, documented Claude Code behavior outside this repo's control. Mitigated by disclosure, not code. | User (via Phase 8 CONTEXT.md D-03/D-11 discussion) | 2026-08-16 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-16 | 9 | 9 | 0 | orchestrator (short-circuit: plan-time register, ASVS L1, all evidence independently re-verified live during Phase 8 execution/verification/code-review) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-16
