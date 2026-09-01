---
phase: "21"
slug: "installed-cutover-and-patch-2-retirement"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-09-01"
---

# Phase 21 — Security

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Non-project proof root → installed registry | Project overlays must not substitute for the active global capability | Capability paths and bundle bytes |
| Public router → resolver subprocess | Third-party resolver output crosses the task-content schema boundary | Structured task content |
| Resolver subprocess → Beads | A plan-authored identifier reaches the local task authority | Validated issue id and task content |
| Tracked source → machine-local workflow | Patch retirement changes shared runtime behavior | Workflow bytes and marker state |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-21-01 | Spoofing/Tampering | Capability overlay selection | high | mitigate | Fresh release verification proved one active global resolver and byte-identical source, project, Claude, Codex, and bootstrap trees. | closed |
| T-21-02 | Tampering | Resolver stdout | high | mitigate | The resolver and public router reject malformed output without content substitution; the isolated malformed-output arm exits nonzero with empty stdout. | closed |
| T-21-03 | Tampering/Elevation | Tracker/Beads identifier | high | mitigate | `SAFE_BD_ID_RE` validates the id before fixed argv `bd show <id> --json`; the argv spy and unsafe-id tests pass. | closed |
| T-21-04 | Denial of Service | Partial Patch 2 retirement | high | accept | Patch 2 is absent from both runtimes and Patch 1 passes independently; the historical pre-gate ordering has no immutable raw receipt. | closed |
| T-21-05 | Tampering/Denial of Service | Rollback integrity | high | accept | Current workflow bytes and post-removal behavior are verified; the unused rollback branch has no surviving executable receipt after the successful one-time cutover. | closed |
| T-21-06 | Repudiation | Stale or combined evidence | medium | accept | The canonical verification records exact implementation and release SHAs plus independently repeated live outcomes, but not raw transient command logs. | closed |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-21-01 | T-21-04 | Reconstructing the completed one-time pre-gate ordering would require a new synthetic transaction harness; current end state and public behavior are independently verified. | Release owner via explicit fix-and-proceed and update instruction | 2026-09-01 |
| AR-21-02 | T-21-05 | The rollback path was contingency-only and did not execute; retaining no raw receipt does not change current runtime behavior. | Release owner via explicit fix-and-proceed and update instruction | 2026-09-01 |
| AR-21-03 | T-21-06 | Exact SHAs and verified outcomes are durable; transient raw command logs are not. | Release owner via explicit fix-and-proceed and update instruction | 2026-09-01 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-01 | 6 | 6 | 0 | gsd-security-auditor + release orchestrator |

## Sign-Off

- [x] All threats have a disposition
- [x] Accepted risks documented
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set

**Approval:** verified 2026-09-01
