# Phase 13: markdown-linting capability (dogfood) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 13-markdown-linting-capability-dogfood
**Areas discussed:** Existing-violation cleanup, Lint scope boundary, LINT-REPORT.md depth, rumdl install method

---

## Existing-violation cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-fix via rumdl --fix, spot-check diff | Fast, mechanical, low-risk for the curated MD0XX set | ✓ |
| Hand-review every changed file | Safer for dense decision-log docs, slow given ~13 phases of history | |
| Auto-fix, full diff review | Middle ground — mechanical fix, complete (not spot-check) review | |

**User's choice:** Auto-fix via `rumdl --fix`, spot-check diff.
**Notes:** None.

---

## Lint scope boundary

| Option | Description | Selected |
|--------|-------------|----------|
| .planning/ only | Matches success criteria/MDL-01 wording exactly | |
| .planning/ + README.md + CLAUDE.md | Extend to the two root docs agents touch most often | ✓ |
| .planning/ + docs/ (full docs tree) | Extend to the whole docs/ directory | |

**User's choice:** `.planning/` + README.md + CLAUDE.md.
**Notes:** Flagged for the planner in CONTEXT.md — ROADMAP.md's Phase 13 success criteria only
name the `.planning/` tree explicitly; README.md/CLAUDE.md must independently reach 0 violations
too since they're now in scope.

---

## LINT-REPORT.md depth

| Option | Description | Selected |
|--------|-------------|----------|
| Count-only | Frontmatter + banner only, matches BEADS.md's minimalism | ✓ |
| Per-rule breakdown table | Body table: rule id → count | |
| Per-file breakdown table | Body table: file path → violation count | |

**User's choice:** Count-only.
**Notes:** None.

---

## rumdl install method

| Option | Description | Selected |
|--------|-------------|----------|
| uvx (recommended) | Zero-footprint, document uvx as primary | |
| pip (pinned) | Reproducible exact version, adds a Python env pin | |
| Document all four equally | No preference, list uvx/pip/cargo/brew equally | |
| Other (free text) | User's own answer | ✓ |

**User's choice:** "locally installed version first, uvx as fallback. graceful non-blocking fail if uvx fails."
**Notes:** Composes with MDL-04's existing `shutil.which("rumdl")` B6 fail-open requirement:
check PATH first, then `uvx rumdl` fallback, then fail open with one notice if `uvx` also fails.

---

## Claude's Discretion

- Exact rumdl config file location/internal TOML structure under `.gsd/capabilities/markdown-linting/`.
- Whether `verify:post` is implemented as a Python script or another mechanism.
- Exact wording of the advisory ship-transcript warning naming the violation count.

## Deferred Ideas

None raised beyond the roadmap's own v2 backlog (MDL-05, blocking gate — already tracked in
REQUIREMENTS.md).
