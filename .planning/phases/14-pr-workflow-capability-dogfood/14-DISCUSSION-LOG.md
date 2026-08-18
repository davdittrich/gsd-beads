# Phase 14: pr-workflow capability (dogfood) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 14-pr-workflow-capability-dogfood
**Areas discussed:** Status mapping precedence, gh detection scope, Notice wording & PR.md shape, gh auth/absence distinction

---

## Status mapping precedence

| Option | Description | Selected |
|--------|-------------|----------|
| Failing dominates, then pending, then passing | Any FAILURE/ERROR check anywhere → failing. Else any PENDING/IN_PROGRESS/QUEUED → pending. Else all SUCCESS (or zero checks configured) → passing. Matches GitHub's own required-check semantics and gh pr checks' own exit-code precedence. | ✓ |
| Zero checks configured → none, not passing | Same precedence, but a PR with no CI configured reports none rather than passing. | |
| Claude's discretion | Don't lock this now — let the planner/researcher pick the rollup rule from gh's documented exit codes. | |

**User's choice:** Failing dominates, then pending, then passing (zero checks = passing).
**Notes:** None.

---

## gh detection scope (PR lookup for this branch)

| Option | Description | Selected |
|--------|-------------|----------|
| gh pr view --json | Resolves current branch's PR directly; errors cleanly when none exists. | |
| gh pr list --head <branch> | Explicit branch filter, returns a list (possibly empty or multiple). | |
| Claude's discretion | Let the researcher/planner pick based on gh's actual documented behavior. | ✓ |

**User's choice:** Claude's discretion.
**Notes:** Must still resolve cleanly to "no open PR" as the `none` signal PRW-03 needs.

---

## Notice wording & PR.md shape

| Option | Description | Selected |
|--------|-------------|----------|
| Count-only frontmatter, like LINT-REPORT.md | pr_status/pr_number/pr_url/timestamp + standard banner, no per-check breakdown table in body. | |
| Include a per-check breakdown table in the body | Body lists each check name and its individual state. | |
| Claude's discretion | Planner decides based on what the ship:pre warning needs to say. | ✓ |

**User's choice:** Claude's discretion.
**Notes:** Minimum requirement — `pr_status` frontmatter field is mandatory regardless.

---

## gh auth/absence distinction

| Option | Description | Selected |
|--------|-------------|----------|
| Two distinct notices | Separate install-focused vs login-focused messages so the user knows which fix applies. | ✓ |
| Claude's discretion on exact wording | Lock the two-cases-must-differ requirement, leave phrasing to the executor. | |

**User's choice:** Two distinct notices (exact wording left to executor).
**Notes:** None.

---

## Claude's Discretion

- Exact `gh` invocation for PR lookup (branch → PR resolution).
- PR.md body depth beyond the mandatory `pr_status` frontmatter field.
- Exact wording of both PRW-04 notices and the PRW-02 ship:pre advisory warning text.
- Whether `execute:wave:post` is a Python script or another mechanism.

## Deferred Ideas

None raised beyond the roadmap's own v2 backlog (PRW-05, blocking gate — already tracked in
REQUIREMENTS.md).
