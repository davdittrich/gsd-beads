# Phase 8: README, Release & Ship Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-16
**Phase:** 8-README, Release & Ship Gate
**Areas discussed:** README structure & audience, Release archive build mechanism, Round-trip validation approach, Ship gate scope

---

## README structure & audience

| Option | Description | Selected |
|--------|-------------|----------|
| gsd-core users evaluating beads | Assumes reader already knows gsd-core; shorter | |
| Beads users evaluating this gsd-core bridge | Assumes reader knows beads already | |
| Cold stranger, assume neither | Explains both from scratch; matches SC1 literally | ✓ |

**User's choice:** Cold stranger, assume neither
**Notes:** Matches ROADMAP SC1's literal "a stranger can evaluate" framing.

| Option | Description | Selected |
|--------|-------------|----------|
| Exact copy-pasteable commands only | Verbatim, nothing paraphrased | ✓ |
| Commands plus expected output shown | More reassuring, more to keep in sync | |

**User's choice:** Exact copy-pasteable commands only

| Option | Description | Selected |
|--------|-------------|----------|
| Requirements (bd on PATH, Python3, gsd-core>=1.6.0) | Named explicitly in ROADMAP SC1 | ✓ |
| Known limitations of the beads/Dolt backend | Repo-specific config quirks | ✓ |
| Prerequisites for the SessionStart hook | First-run bd prime behavior | ✓ |

**User's choice:** All three (multiSelect)

| Option | Description | Selected |
|--------|-------------|----------|
| Repo root, standard order | Title -> What -> Requirements -> Install -> Uninstall -> Caveats -> License -> Link | ✓ |
| Repo root, quickstart-first | Lead with copy-paste block before explanation | |

**User's choice:** Repo root, standard order

| Option | Description | Selected |
|--------|-------------|----------|
| No — install + bd Quick Reference is enough | Point to AGENTS.md, no duplication | |
| Yes — include a short worked example | Tiny end-to-end bd workflow snippet in README | ✓ |

**User's choice:** Yes — include a short worked example

---

## Release archive build mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| GitHub Actions workflow on tag push | Repeatable, no manual step to forget | ✓ |
| Local build script, manually run + uploaded | No CI dependency | |
| Manual zip, no script | Fastest once, no repeatable enforcement | |

**User's choice:** GitHub Actions workflow on tag push

| Option | Description | Selected |
|--------|-------------|----------|
| v1.1.0 | Matches current milestone version | ✓ |
| v1.0.0 | Restart semver at public launch | |
| Something else | — | |

**User's choice:** v1.1.0

---

## Round-trip validation approach

| Option | Description | Selected |
|--------|-------------|----------|
| You run it manually, once, at ship time | Real transcript = the proof | |
| Scripted where possible + manual for interactive parts | CLI non-interactive flags where available | ✓ |

**User's choice:** Scripted where possible + manual for interactive parts

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 8 SUMMARY.md | Same pattern as Phase 7's fresh-clone transcript | ✓ |
| Separate VALIDATION-TRANSCRIPT.md | Keeps SUMMARY.md shorter | |

**User's choice:** Phase 8 SUMMARY.md

---

## Ship gate scope

| Option | Description | Selected |
|--------|-------------|----------|
| Re-run validate at the released tag, on a fresh clone | Proves SC5 literally | ✓ |
| Trust the current local pass, don't re-run | Assume it stays clean | |

**User's choice:** Re-run validate at the released tag, on a fresh clone
**Notes:** `claude plugin validate . --strict` was verified live during this discussion — already passes clean on the current working tree (`✔ Validation passed`), but that alone does not satisfy SC5's literal "at the released tag" requirement.

| Option | Description | Selected |
|--------|-------------|----------|
| Leave as "./" | Repo-relative, should resolve correctly either way | |
| Not sure — investigate during planning | Verify empirically against real /plugin marketplace add flow | ✓ |

**User's choice:** Not sure — investigate during planning
**Notes:** Left as an explicit open question (D-11 in CONTEXT.md) rather than decided — flagged for the researcher/planner to test against the real flow.

---

## Claude's Discretion

- Exact README prose/wording within the locked section order
- Exact GitHub Actions workflow YAML structure, as long as it triggers on tag push and produces the exact allowlist archive
- Exact wording of the worked `bd` usage example

## Deferred Ideas

None — discussion stayed within phase scope.
