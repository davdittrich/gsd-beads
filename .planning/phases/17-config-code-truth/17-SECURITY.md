---
phase: 17
slug: config-code-truth
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-20
---

# Phase 17 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| filesystem -> regex construction | A phase-number token derived from a directory name or a `PLAN.md` filename is interpolated into a compiled regex | phase-number string |
| `.planning/STATE.md` -> directory resolution | `current_phase` frontmatter selects which phase directory every lifecycle point operates on | phase-number string |
| filesystem -> `discover_plan_files` | Directory entries are matched against `PLAN_FILE_RE` and become dict keys | filenames |
| `$CLAUDE_CONFIG_DIR` -> filesystem read | An environment variable selects which runtime home's workflow files the probe reads | file path |
| installed gsd-core workflow prose -> dispatch decision | Third-party file content decides whether this capability performs a lifecycle dispatch | workflow markdown |
| `.planning/config.json` -> strip decision | A user-editable config value decides whether irreversible PLAN.md prose deletion is permitted on the native/explicit path | `beads.sync_mode` string |
| `.planning/config.json` -> notice output | A user-controlled string is echoed into the hook's `additionalContext` (agent-readable context) | `beads.sync_mode` raw value |
| `capability.json` declaration -> gsd-core validator | The declared values array is the write-time enum gsd-core enforces for every future `config-set` | enum array |
| installed workflow file content -> reported verdict | Third-party file content decides whether a patch is reported present, gating the destructive strip at the live re-gate | markdown marker string |
| CLI verb name -> skill callers | `beads-recall/SKILL.md` and `beads-status/SKILL.md` invoke the collapsed patch-check verb by name | CLI argv |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-17-01-01 | Tampering | `get_phase_header`, `extract_phase_mentions` | high | mitigate | `phase_regex_token` applies `re.escape()` to the phase-number token before interpolation — `sync.py:864` — so a literal `.` cannot become a regex wildcard. | closed |
| T-17-01-02 | Denial of Service | `PLAN_FILE_RE` | medium | mitigate | Widened pattern `^(\d+(?:\.\d+)?-\d+)-PLAN\.md$` (`sync.py:86`) is anchored at both ends with no adjacent unbounded quantifiers over the same span — no catastrophic backtracking. | closed |
| T-17-01-03 | Elevation of Privilege | `_resolve_default_phase_dir` | medium | mitigate | Resolution goes through `confined(project_root, ".planning", "phases")` and a directory-name prefix comparison (`sync.py:2001-2018`) — never a path join off `current_phase`. | closed |
| T-17-01-04 | Information Disclosure | `beads_recall` output | low | accept | Widened discovery surfaces only the user's own planning artifacts inside the already-confined `.planning/phases/` root; no new read surface outside it. | closed |
| T-17-01-SC | Tampering | npm/pip/cargo installs | low | accept | Zero packages installed this phase — `sync.py` stays pure stdlib. | closed |
| T-17-02-01 | Denial of Service | `check_native_step_dispatch` -> `lifecycle_dispatch` | high | mitigate | Region-scoped probe (`sync.py:2342-2398`), fence-aware, excludes `capId ==`/`ref.skill ==`-qualified lines; every miss (unmapped point, missing/unreadable file, no anchor, no qualifying line) returns 0 (not-detected), which degrades to today's working double dispatch — never raises. | closed |
| T-17-02-02 | Tampering | native `create-issues` path -> `strip_task_bodies` | high | mitigate | Hook path keeps the literal `allow_strip=False` (`sync.py:965`, D-03); the explicit CLI/native path alone consults `read_sync_mode` (`sync.py:2546`, D-06). The live `check_execute_plan_patch() == 0` re-gate is untouched. | closed |
| T-17-02-03 | Elevation of Privilege | `$CLAUDE_CONFIG_DIR` path resolution | low | accept | A caller controlling the process environment already controls whether the hook runs at all; every probe message names the exact path read (WR-03). | closed |
| T-17-02-04 | Information Disclosure | probe output | low | accept | Prints an absolute path under the user's own runtime home into the hook's own `additionalContext` — same exposure class as the two pre-existing patch checkers. | closed |
| T-17-02-SC | Tampering | npm/pip/cargo installs | low | accept | Zero packages installed — stdlib only. | closed |
| T-17-03-01 | Tampering | `read_sync_mode` -> `create_issues` `allow_strip` | high | mitigate | Comparison only ever withholds strip permission (`allow_strip=(sync_mode != "mirror")`, `sync.py:2546`); the live `check_execute_plan_patch() == 0` re-gate stays the last line of defence. | closed |
| T-17-03-02 | Tampering | out-of-enum notice output | medium | mitigate | `_sanitize_notice_value` (`sync.py:779-789`) strips every non-printable character (`str.isprintable()` covers control chars and newlines) and truncates to 80 chars before the value is echoed into `additionalContext`. | closed |
| T-17-03-03 | Information Disclosure | notice output | low | accept | Notice reveals one value from the user's own project config into the user's own session context — no third-party exposure. | closed |
| T-17-03-04 | Denial of Service | `check_sync_mode_value` at `plan:pre` | low | mitigate | Reuses the already-performed config read, adds no new file I/O/subprocess/network call, and runs inside `lifecycle_dispatch`'s existing `try/except Exception` (`sync.py:825-830` catches `OSError`/`UnicodeDecodeError`/`JSONDecodeError` and returns 0). | closed |
| T-17-03-SC | Tampering | npm/pip/cargo installs | low | accept | Zero packages installed — stdlib and doc edits only. | closed |
| T-17-04-01 | Spoofing | merged reader's present/absent verdict | high | mitigate | `check_patch` (`sync.py:2286-2322`) does a plain code-point substring test (`entry["marker"] in text`) against a per-entry version-labeled literal constant — never a regex, never fuzzy — with `SHIP_MD_PATCH_MARKER` (v2) and `EXECUTE_PLAN_PATCH_MARKER` (v1) independently versioned (`sync.py:124,129,136-170`). | closed |
| T-17-04-02 | Denial of Service | merged reader inside `lifecycle_dispatch` | high | mitigate | Unrecognized `target` returns the fail-open exit code with a diagnostic distinct from the unreadable-file message (`sync.py:2297-2301`) — total by construction, never raises. | closed |
| T-17-04-03 | Tampering | CLI verb rename across two SKILL.md callers | high | mitigate | Both `beads-status/SKILL.md:146` and `beads-recall/SKILL.md:72-73` call the surviving `check-patch ship-md`/`check-patch execute-plan` verb; a repo-wide grep for either retired verb name outside `.planning/` returns zero hits. | closed |
| T-17-04-04 | Elevation of Privilege | `--path` override | low | accept | Reader is strictly read-only; it emits only a present/absent verdict plus the path it read; any caller able to pass the flag already controls the process (WR-03 discipline preserved). | closed |
| T-17-04-05 | Information Disclosure | verdict messages | low | accept | Messages disclose an absolute path under the user's own runtime home into their own session context — unchanged from the pre-merge functions. | closed |
| T-17-04-SC | Tampering | npm/pip/cargo installs | low | accept | Zero packages installed — stdlib refactor plus markdown edits. | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-17-01 | T-17-01-04 | Widened `PLAN_FILE_RE` only makes more of the user's own already-confined planning artifacts discoverable; no new read surface outside `.planning/phases/`. | Plan 17-01 threat model | 2026-08-19 |
| AR-17-02 | T-17-01-SC | Zero packages installed this phase (`sync.py` pure stdlib). | Plan 17-01 threat model | 2026-08-19 |
| AR-17-03 | T-17-02-03 | Controlling `$CLAUDE_CONFIG_DIR` already implies controlling whether the hook runs; every message names the exact path probed. | Plan 17-02 threat model | 2026-08-19 |
| AR-17-04 | T-17-02-04 | Probe output discloses only an absolute path under the user's own runtime home, into their own session — same class as pre-existing patch checkers. | Plan 17-02 threat model | 2026-08-19 |
| AR-17-05 | T-17-02-SC | Zero packages installed this phase. | Plan 17-02 threat model | 2026-08-19 |
| AR-17-06 | T-17-03-03 | Notice discloses one value from the user's own project config into the user's own session context. | Plan 17-03 threat model | 2026-08-19 |
| AR-17-07 | T-17-03-SC | Zero packages installed this phase. | Plan 17-03 threat model | 2026-08-19 |
| AR-17-08 | T-17-04-04 | `--path` override reader is strictly read-only and only reachable by a caller who already controls the process. | Plan 17-04 threat model | 2026-08-19 |
| AR-17-09 | T-17-04-05 | Verdict messages disclose only an absolute path under the user's own runtime home — unchanged from pre-merge behavior. | Plan 17-04 threat model | 2026-08-19 |
| AR-17-10 | T-17-04-SC | Zero packages installed this phase. | Plan 17-04 threat model | 2026-08-19 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-20 | 21 | 21 | 0 | /gsd-secure-phase (orchestrator, L1 grep-depth verification against implementation; asvs_level: 1 short-circuit — auditor subagent not spawned per workflow Step 3) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-20
