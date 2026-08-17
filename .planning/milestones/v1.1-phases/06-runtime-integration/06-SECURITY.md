---
phase: 6
slug: runtime-integration
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-16
---

# Phase 6 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| gsd-beads plugin → installer's machine | `hooks/hooks.json` is executed by Claude Code on every session start on someone else's machine. Everything in it crosses this boundary. | A static shell command string (`bd prime --hook-json`) |
| Claude Code plugin runtime → gsd-core capability loader | No code path connects them. The gap is bridged only by a human running a command; automating that crossing is what T-06-01 describes. | Human-typed CLI invocation only |
| `bd`'s local database → session context | `bd prime` output is injected as `additionalContext` into every session. | Local issue-tracker data (titles, descriptions, project state) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-06-01 | Elevation of Privilege | An automated postinstall/SessionStart bridge running `capability install --yes` | high | mitigate | Not built. gsd-core's CB-3 human consent gate stays human-run. Task 3's acceptance criterion — `git status --porcelain --untracked-files=all` shows changes only under `.planning/` — verified by both the executor and the independent verifier; no new invoking file exists. | closed |
| T-06-02 | Tampering | `hooks/hooks.json`'s command string — arbitrary shell executed on every session start on every installer's machine | high | mitigate | Shipped command asserted byte-equal (canonical `jq -S` diff) to the string already proven across Phases 1-5: a bare binary invocation, no shell chaining, no interpolation, no network fetch. Hook-entry count pinned at 1. Independently re-verified by the code reviewer (WR-01 noted a literal trailing-newline byte-count difference, which does not affect the canonical-diff acceptance criterion) and the phase verifier (live `jq -S` diff re-run). | closed |
| T-06-03 | Denial of Service | A malformed or oversized `hooks/hooks.json` shipped to installers | low | mitigate | `claude plugin validate . --strict` double-run (marketplace.json present + moved aside) confirmed clean both times; `jq` parse on every criterion touching the file. Degraded-UX only — Claude Code's SessionStart contract already fails open (Task 2 proved this live, both by the executor and independently by the verifier). | closed |
| T-06-04 | Information Disclosure | `bd prime` output injected into session context | low | accept | The user's own local issue database, injected into the user's own session. No transport, no persistence, no new reader added this phase. Unchanged from v1.0, where the same hook already ran from `.claude/settings.json`. | closed |
| T-06-05 | Spoofing | Marketplace source resolution — `marketplace.json` names `"source": "./"` | low | accept | Local relative path only; no remote source fetched this phase. Re-evaluate in Phase 8 when the source is re-pointed at a release archive URL (PUB-04). | closed |
| T-06-SC | Tampering | npm/pip/cargo installs (supply-chain) | n/a | n/a | No package manager runs in this phase, in any ecosystem (06-RESEARCH.md Package Legitimacy Audit: "Not applicable"). No `[ASSUMED]`/`[SUS]`/`[SLOP]` package exists to gate. | n/a |

*Status: open · closed · open — below `high` threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (`high`) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-06-01 | T-06-04 | Local-only data, same-session reader, no new transport/persistence — identical exposure to v1.0's pre-existing `.claude/settings.json` hook. | Phase 6 plan author | 2026-08-16 |
| R-06-02 | T-06-05 | Local relative marketplace source only; no remote fetch this phase. Scheduled for re-evaluation at Phase 8 (PUB-04 release-archive source change). | Phase 6 plan author | 2026-08-16 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-16 | 5 (+1 n/a) | 5 | 0 | Claude (orchestrator, short-circuit per threats_open:0 + register_authored_at_plan_time:true + asvs_level:1 — L1 grep-depth sufficient, no auditor spawn required) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-16
