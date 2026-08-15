---
phase: 02
slug: visibility
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-15
---

# Phase 02 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| `bd` issue title/description/notes text -> BEADS-RECALL.md / BEADS.md table cells | Issue text originates from whoever filed it in `bd`, a different principal than the process rendering the generated artifact | Untrusted text -> markdown table cell |
| Cross-phase `PLAN.md` directory scan (`.planning/phases/*/`) | `collect_all_task_files` walks every phase directory to build the reverse `<beads-id>` lookup index | Filesystem path traversal |
| Phase-mention tokens -> `bd list --desc-contains` argv | Tokens extracted from ROADMAP.md/CONTEXT.md text cross into an external process's argv | Text -> subprocess argv |
| Wave plan ids -> filesystem plan lookup | `render_wave_status_block` resolves plan ids against discovered plan files | Plan id -> file lookup |
| Capability re-install -> user's project | Re-consenting after this phase's edits grants the newly extended instruction surface | Extended capability instruction surface |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-02-01 | Tampering / Elevation of Privilege | `beads-recall` bd invocation | high | mitigate | Every bd call is an argv list passed to `run_bd`/`subprocess.run` with shell interpretation disabled; confirmed `grep -c "shell=True" sync.py` == 0, all bd argv lists literal (e.g. `_beads_recall_argv`, `_beads_md_argv`) | closed |
| T-02-02 | Tampering | `collect_all_task_files` cross-phase directory scan | medium | mitigate | Every scanned path confined to `.planning/phases/` root via `confined(project_root, ".planning", "phases")` (sync.py:202), never joined from untrusted artifact/frontmatter text | closed |
| T-02-03 | Information Disclosure | `bd` issue title/description echoed into BEADS-RECALL.md | low | mitigate | `_escape_table_cell` (sync.py:628) escapes `\|` and strips `\r`/`\n` before every issue title/status enters a markdown table cell; confirmed called at recall render sites (sync.py:650-652) | closed |
| T-02-04 | Tampering | BEADS.md regeneration | medium | mitigate | `regenerate_beads_md` always fully overwrites via `out_path.write_text(...)` (sync.py:960) from a fresh bd query — never reads/merges the existing file body; matches `TestBeadsMdRegeneration`'s hand-edit-then-regenerate assertion | closed |
| T-02-05 | Information Disclosure | `bd` issue title/description echoed into BEADS.md / the wave-status block | low | mitigate | Same `_escape_table_cell` control applied in `_render_beads_md_table` (sync.py:878-880) | closed |
| T-02-06 | Elevation of Privilege | Project-scope capability re-install/re-consent after this phase's file edits | high | mitigate | `gsd capability install --scope project` re-run at a blocking human checkpoint (Task 3, 02-02); `.gsd-capabilities.json` `updatedAt: 2026-08-15T19:58:58.155Z` confirms re-consent occurred after this phase's edits | closed |
| T-02-07 | Tampering | `bd list --parent <epic> --all --json` without `-n 0` (Pitfall 3) | medium | mitigate | All three new/modified `bd list` call sites pass `-n 0` explicitly, confirmed at sync.py:639, 738, 845 | closed |
| T-02-SC | Tampering | Supply chain | low | accept | No package-manager install this phase — N5 unchanged from Phase 1; not applicable per 02-RESEARCH.md's Package Legitimacy Audit | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-02-SC | T-02-SC | No package-manager install this phase; supply-chain surface unchanged from Phase 1 | gsd-secure-phase (L1, asvs_level=1 short-circuit) | 2026-08-15 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-15 | 8 | 8 | 0 | gsd-secure-phase (L1 grep-depth, asvs_level=1 short-circuit — register_authored_at_plan_time: true) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-15
