---
phase: "20"
slug: "additive-identity-migration-and-compatibility"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-08-31"
---

# Phase 20 — Security

> Verified plan-time STRIDE mitigations for native task identity migration.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PLAN opening tag to synchronizer | Authored type and identity select migration eligibility | Untrusted plan text |
| Synchronizer to Beads CLI | Legacy identity is checked against live authority | Typed issue-id argument and JSON result |
| Synchronizer to PLAN write | Native identity becomes durable routing metadata | Canonical tracker attribute |
| Migrated PLAN to gsd-core | The native parser consumes projected identity | Task routing metadata |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-20-01 | Tampering | eligible opening tag | high | mitigate | Preflight rejects wrong, duplicate, or authority-free native identity before Beads or file mutation; public tests spy on both boundaries. | closed |
| T-20-02 | Tampering | legacy-to-native projection | high | mitigate | Safe typed Beads resolution precedes projection; stale and malformed controls remain unmigrated. | closed |
| T-20-03 | Elevation of Privilege | checkpoint and unknown types | high | mitigate | Exact `auto`/`tracer` allow-list; excluded blocks are asserted byte-identical. | closed |
| T-20-04 | Repudiation | repeat synchronization | medium | mitigate | Same-path second pass proves byte identity and zero create, update, or write. | closed |
| T-20-05 | Denial of Service | unavailable or failing Beads | medium | accept | Existing visible fail-open and no-plan-write behavior is retained and tested. | closed |
| T-20-06 | Information Disclosure | diagnostics | low | mitigate | Diagnostics expose category and task name only; typed argv prevents shell interpolation. | closed |

*All six classifications and mitigations are supported by exact source and passing
public-boundary tests. Confidence: 98/100.*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-20-01 | T-20-05 | Beads unavailability skips synchronization visibly and preserves PLAN bytes; retry and alternate authority are outside the approved contract. | Phase 20 plan | 2026-08-31 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-31 | 6 | 6 | 0 | GSD execute-phase ASVS L1 review |

---

## Verification Evidence

- Focused identity and milestone-authority controls passed, including
  malformed, duplicate, mismatched, incomplete, and blank authority cases.
- The complete capability suite passed 305/305.
- `sync.py` uses fixed typed `bd` argument lists and one lexical writer.

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks are documented.
- [x] `threats_open: 0` is confirmed.
- [x] `status: verified` is set in frontmatter.

**Approval:** verified 2026-08-31
