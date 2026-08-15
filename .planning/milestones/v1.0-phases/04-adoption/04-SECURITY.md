---
phase: 04
slug: adoption
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-16
---

# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| todo file text -> bd argv | A `.planning/todos/pending/*.md` file's title/problem/solution/files/area/severity text (human- or Claude-authored) crosses into a `bd create` invocation -- a different principal than the process running `bd` | Untrusted text -> subprocess argv |
| `files:` frontmatter values -> bd description prose | Todo `files:` block-list values fold into the created issue's description | Untrusted text -> issue description |
| bd issue rows -> rendered markdown | Issue title/status text (authored by whoever filed it in bd) crosses into the printed on-demand status view | Untrusted text -> markdown table cell |
| on-demand status view -> bd mutation surface | The read-only status/mapping path must never reach a bd mutation command | N/A (absence boundary) |
| `.planning/config.json` -> `resolve_epic()`'s branch decision | A project-level config file, writable by any repo contributor, read directly by `sync.py` for the first time in this capability's history | Config value -> control-flow branch |
| plan frontmatter `beads_epic` values (cross-phase) -> `resolve_milestone_epic`'s candidate scan | Every plan's own frontmatter across every phase directory is scanned as untrusted candidate data before a live `bd` title-match confirms or rejects each one | Frontmatter values -> epic-id candidates |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-04-01 | Tampering | `migrate_todos()`'s bd create argv (title/desc/labels from untrusted todo text) | high | mitigate | Every field is one element of a typed argv list to `run_bd` (`subprocess.run`, `shell=False`) — confirmed `grep -c "shell=True" sync.py` == 0; identical discipline to `create_issues` | closed |
| T-04-02 | Tampering / Information Disclosure | `files:` frontmatter folded into bd description as prose | low | accept | Never used as a filesystem path (never opened/read/confined) — only interpolated as opaque description text; no path-traversal surface | closed |
| T-04-03 | Denial of Service | unbounded `todos/pending/*.md` directory scan | low | accept | Local dev tool; bounded by the same filesystem `.planning/` already lives in; no externally-triggered growth | closed |
| T-04-04 | Tampering | on-demand status's bd list argv (`_beads_md_argv`, reused) | high | mitigate | Reuses `run_bd()`'s typed-argv contract verbatim — confirmed zero new subprocess call sites in `render_status_mapping` (sync.py:1288-1338) | closed |
| T-04-05 | Elevation of Privilege / Repudiation | on-demand status accidentally mutating bd state (e.g. auto-closing a reported orphan) | high | mitigate | `render_status_mapping` never calls `bd close`/`update`/`comment` — confirmed directly: all 3 such call sites in sync.py (lines 816, 905, 1544) are outside `render_status_mapping`'s body (1288-1338); `TestOnDemandStatus::test_read_only_guarantee_no_bd_close_update_comment_calls` test-verifies the same | closed |
| T-04-06 | Tampering | issue title/status text rendered into the printed table/orphan lists | medium | mitigate | `_escape_table_cell` (reused verbatim via `_render_beads_md_table`/`_render_issue_table`) strips `\r`/`\n` and escapes `\|` before any bd-supplied text enters a table cell | closed |
| T-04-07 | Tampering | `resolve_milestone_epic()`'s new `.planning/config.json` read | medium | mitigate | Path resolved via `confined()`/`find_project_root()` before read; `json.JSONDecodeError` caught, defaults to `"phase"`; a non-dict `beads` config shape (code-review CR-02) is now also guarded via `isinstance()` checks (sync.py:481-489) — never crashes, never reads outside the project root | closed |
| T-04-08 | Tampering / Repudiation | accidental retroactive fold of an existing per-phase epic into milestone scope (D-10) | high | mitigate | `resolve_milestone_epic()` only reuses a candidate whose live `bd` title exactly matches the computed milestone title; a per-phase epic's title is always a ROADMAP phase header, structurally distinct — regression-tested (`test_existing_phase_epic_not_reused_as_milestone_epic`); a missing `STATE.md` now fails open via `RuntimeError` (code-review CR-01, sync.py:519-521) instead of an uncaught `FileNotFoundError` | closed |
| T-04-09 | Tampering | `resolve_milestone_epic()`'s `bd create`/`bd show` argv | high | mitigate | Reuses `run_bd()`'s typed-argv contract verbatim — zero new subprocess call sites | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-04-01 | T-04-02 | `files:` values are opaque description prose, never a filesystem path; no traversal surface | gsd-secure-phase (L1, asvs_level=1 short-circuit) | 2026-08-16 |
| R-04-02 | T-04-03 | Local dev tool, filesystem-bounded, no external growth vector | gsd-secure-phase (L1, asvs_level=1 short-circuit) | 2026-08-16 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-16 | 9 | 9 | 0 | gsd-secure-phase (L1 grep-depth, asvs_level=1 short-circuit — register_authored_at_plan_time: true; 5 code-review-fix commits (CR-01/02/03, WR-01/02) independently confirmed present in source before closing T-04-05/T-04-07/T-04-08) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-16
