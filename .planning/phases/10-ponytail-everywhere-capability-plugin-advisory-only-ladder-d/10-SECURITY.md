---
phase: 10
slug: ponytail-everywhere-capability-plugin-advisory-only-ladder-d
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-17
---

# Phase 10 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| `.planning/config.json` → hook shell scripts | `ponytail.enabled`/`ponytail.level` read via `gsd_tools config-get` and interpolated into stdout banner text | config-driven strings, enum-validated before any use |
| Hook stdout → agent session context | `ponytail-everywhere/hooks/session-start.sh` output is injected verbatim into every SessionStart/SubagentStart context | static advisory text + one of 3 enum-constrained level names |
| Project-scope capability install → `gsd-planner` prompt | `.gsd/capabilities/ponytail/` fragments injected via `capability.json` `contributions[]` at `plan:pre` | repo-tracked markdown, whole-bundle content-hash consent gated |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-10-01 | Tampering | `ponytail-everywhere/hooks/session-start.sh` — `ponytail.level` / `ROLE` args | high | mitigate | `case` enum whitelist (`lite\|full\|ultra`→`full`; `planner\|executor\|verifier`→`generic`) before any use; never passed to `eval`/`source`/command substitution; single-quoted heredoc banner. Asserted by injection-case test (`x; touch /tmp/ponytail-pwned` → `level: full`, no file created). | closed |
| T-10-02 | Denial of Service | `ponytail-everywhere/hooks/session-start.sh` — runs every SessionStart/SubagentStart | medium | mitigate | Fail-open by construction: no `set -e`, every external call has `\|\| echo <default>` + `2>/dev/null`, always `exit 0`. Strengthened post-review (WR-01, `fc273ff`): distinguishes exit 127 (binary unavailable → safe default) from any other `gsd_tools` failure (now fails *closed* — `enabled=false` — instead of silently re-enabling on a corrupt-config or other error). | closed |
| T-10-03 | Information Disclosure | Hook stdout injected into every session/subagent | low | accept | Static text + enum-constrained level name only; no repo content, paths, or credentials. No mitigation warranted. | closed |
| T-10-03b* | Elevation of Privilege | Project-scope capability consent (`capability install ./.gsd/capabilities/ponytail --scope project --yes`) — activates prompt injection into `gsd-planner` | high | mitigate | Blocking human checkpoint required operator to read all 5 bundle files before consent (mirrors T-02-06 from Phase 02). `workflow.auto_advance: false`, never auto-approvable. Whole-bundle content-hash consent invalidates on any later edit. **Verified live, not just planned**: reviewed `capability.json` + 3 fragments + NOTES.md this session, presented via `AskUserQuestion`, user selected "Approved" before install ran (commit `6ccda1b`). | closed |
| T-10-04 | Tampering | `.gsd/capabilities/ponytail/fragments/*.md` — content injected verbatim into `gsd-planner`'s prompt | medium | mitigate | Repo-tracked, reviewed at the same consent checkpoint as T-10-03b, re-consent forced by content hash on any change. Fragment text carries an explicit floor line forbidding simplification of input validation/error handling/security controls/accessibility — the injected instruction cannot argue for removing a security control. | closed |
| T-10-05 | Denial of Service | Contribution resolution at `plan:pre` | low | accept | Every `contributions[]` entry carries `onError: "skip"` (fail-open, same posture as every `beads` capability entry). A malformed fragment/missing file makes the entry inert; cannot fail the planning run. No further mitigation warranted. | closed |

*Note: `10-01-PLAN.md` and `10-02-PLAN.md` independently assigned the label `T-10-03` to two distinct threats (Information Disclosure vs. Elevation of Privilege) — a labeling collision across the two plans within this phase, not a security gap. Disambiguated here as `T-10-03` / `T-10-03b`. Both are closed; flagging only so a future audit doesn't conflate them.

*Status: open · closed · open — below `high` threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` (`high`) count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-10-01 | T-10-03 | Hook stdout carries only static advisory text + an enum-constrained level name — no information worth disclosing. | Planner (10-01-PLAN.md), confirmed at audit | 2026-08-17 |
| AR-10-02 | T-10-05 | `onError: "skip"` fail-open posture is this repo's established pattern (every `beads` capability entry uses it); a malformed fragment cannot fail a planning run. | Planner (10-02-PLAN.md), confirmed at audit | 2026-08-17 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-17 | 6 | 6 | 0 | Orchestrator (short-circuit: `register_authored_at_plan_time: true`, `asvs_level: 1`, `threats_open: 0` — auditor spawn not required per gate rule) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-17
