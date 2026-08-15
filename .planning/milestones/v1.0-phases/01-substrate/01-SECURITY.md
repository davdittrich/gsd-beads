---
phase: 1
slug: substrate
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-15
---

# Phase 1 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PLAN.md text → `bd` process argv | Task titles/descriptions originate in an artifact whose author is frequently not the principal running `bd` (N4, primary untrusted-input crossing) | Task/plan text → subprocess argv |
| PLAN.md frontmatter → filesystem paths | `phase`/`plan` frontmatter values resolve which files sync reads and rewrites | Frontmatter values → file paths |
| `bd` stdout/stderr → `.planning/STATE.md` | External process output appended to a tracked planning artifact | Subprocess output → tracked file |
| PLAN.md `depends_on` values → filesystem plan lookup | Prerequisite plan ids from frontmatter locate and open other plan files | depends_on entries → file paths |
| `WAVE_PLAN_IDS` → filesystem plan lookup | Plan ids from the orchestrator's wave context locate plan files | Wave-context ids → file paths |
| Capability install → user's project | Installing an overlay grants it instruction surfaces the agent will later follow | Bundle files → active instruction surface |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Tampering / Elevation of Privilege | `sync.py` bd invocation helper (`run_bd`) | high | mitigate | Single call site (`sync.py:35`, `run_bd`) — every `bd` invocation passes a typed argv list to `subprocess.run` with shell interpretation left at its disabled default; zero `shell=True` in the file (grep-confirmed) and zero PLAN.md text is ever formatted into a command string. Independently confirmed by 01-REVIEW.md's code review, which read every call site directly rather than trusting the plan text. | closed |
| T-01-02 | Tampering | `sync.py` plan-path resolution | medium | mitigate | `confined()` (`sync.py:85`) resolves and rejects any path escaping the project root; used at every `.planning/STATE.md`/`ROADMAP.md` resolution point (`sync.py:355,399,406,437`). | closed |
| T-01-03 | Information Disclosure | STATE.md Blockers/Concerns append (D-08) | low | accept | The appended notice is a fixed capability-authored sentence naming bd as unavailable/failing; raw bd stderr is never copied into the tracked artifact — confirmed in both `append_state_blocker` call sites (probe-failure and mid-sync-failure paths added by the CR-01 fix). Accepted at ASVS L1 per the plan's own disposition. | closed |
| T-01-SC | Tampering | Supply chain | low | accept | No package-manager install in this phase — N5 restricts the capability to the `bd` binary (user-installed) and Python 3 stdlib. 01-RESEARCH.md's Package Legitimacy Audit recorded as not applicable. | closed |
| T-01-04 | Tampering | Prerequisite-plan resolution from `depends_on` | medium | mitigate | `discover_plan_files()` (`sync.py:136`) globs the phase directory once; `depends_on` entries are looked up in that discovered-file map (`sync.py:160`), never joined onto a path. An entry with no match resolves to `None` and is reported, not opened. | closed |
| T-01-05 | Tampering / Elevation of Privilege | `bd dep add` and `bd close` invocation | high | mitigate | Same single-call-site argv-list control as T-01-01 — ids and reason strings are discrete argv elements, never interpolated. | closed |
| T-01-06 | Denial of Service | Orphan sweep over a large epic | low | accept | Sweep bounded by one epic's children, listed in a single `bd` call — tens of records at gsd-phase scale; no pagination/rate control warranted at ASVS L1. | closed |
| T-01-07 | Tampering | `close-wave` plan-id resolution | medium | mitigate | Same `discover_plan_files()` pattern as T-01-04, reused in `find_completed_task_ids` (`sync.py:298`) — incoming plan ids matched against discovered files, never joined onto a path. | closed |
| T-01-08 | Tampering / Elevation of Privilege | `bd close` invocation (wave-batch) | high | mitigate | Same single-call-site argv-list control as T-01-01/T-01-05 — confirmed at `sync.py:378` (`["bd", "close", *to_close, "--reason", reason]`). | closed |
| T-01-09 | Repudiation | Automatic wave close | medium | mitigate | Every close carries a `--reason` string naming the wave/cause — confirmed at `sync.py:378` (wave reason) and `sync.py:458` (orphan-sweep reason) — bd's own history records why an issue closed. | closed |
| T-01-10 | Elevation of Privilege | Project-scope capability install and consent | high | mitigate | Installation went through `gsd-tools.cjs capability install --scope project` and its consent disclosure at a blocking human checkpoint (01-03-PLAN.md Task 3), never auto-approved. Independently re-confirmed live during phase verification: `capability list --raw` shows `beads` `status: "active"`, and both `plan:post`/`execute:wave:post` render-hooks name `capId: "beads"`. Re-run once after the CR-01 post-consent bundle edit re-invalidated the hash (commit `85aff2a`), then re-verified. | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-01 | T-01-03 | Fixed, non-attacker-controlled notice sentence appended to STATE.md; raw bd stderr never copied in | Plan 01-01 threat model | 2026-08-15 |
| R-02 | T-01-SC | No package-manager install in Phase 1; capability restricted to `bd` binary + Python 3 stdlib (N5) | Plan 01-01 threat model | 2026-08-15 |
| R-03 | T-01-06 | Orphan sweep bounded by one epic's children (tens of records at this scale); no rate control warranted at ASVS L1 | Plan 01-02 threat model | 2026-08-15 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-15 | 10 | 10 | 0 | /gsd-secure-phase orchestrator, L1 grep-depth verification (register authored at plan time; short-circuit per workflow rule, asvs_level==1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-15
