# Phase 5: Plugin Manifest - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-16
**Phase:** 5-Plugin Manifest
**Areas discussed:** Plugin identity, LICENSE holder, Marketplace entry wording, Skills-path mechanism risk

---

## Plugin identity

| Option | Description | Selected |
|--------|-------------|----------|
| beads | Matches capability id, matches PUB-02 install command `beads@gsd-beads` | ✓ |
| gsd-beads | Matches repo/GitHub name; risks reserved-prefix confusion | |

**User's choice:** beads

| Option | Description | Selected |
|--------|-------------|----------|
| davdittrich@gmail.com only | Email only | ✓ |
| Name + email object | Requires display name too | |

**User's choice:** davdittrich@gmail.com only (author field)

| Option | Description | Selected |
|--------|-------------|----------|
| 0.1.0 | Matches capability.json's current version | ✓ |
| 1.0.0 | v1.0 milestone already shipped | |

**User's choice:** 0.1.0 (starting version)
**Notes:** None.

---

## LICENSE holder

| Option | Description | Selected |
|--------|-------------|----------|
| dd | Matches git user.name in this repo | |
| Other name | Type exact name/entity | ✓ |

**User's choice:** Dennis A. V. Dittrich
**Notes:** Year defaulted to 2026 (current system date) without a separate question — only one sane value existed.

---

## Marketplace entry wording

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse PROJECT.md "Core Value" | Verbatim, already-approved wording | |
| Short install-page blurb | New one-liner written for installers | ✓ |

**User's choice:** Short install-page blurb
**Notes:** Marketplace entry id defaulted to `beads` (same as plugin.json name) without a separate question — locked by REQUIREMENTS.md PUB-02's install command, no genuine alternative.

---

## Skills-path mechanism risk

| Option | Description | Selected |
|--------|-------------|----------|
| Research decides | Let phase-researcher find Claude Code's actual supported mechanism | ✓ |
| Symlink under .claude-plugin/ | Pre-commit to symlink structure now | |

**User's choice:** Research decides

| Option | Description | Selected |
|--------|-------------|----------|
| Run validate twice | Once with marketplace.json absent, once normal — both must be clean | ✓ |
| Single strict run only | Accept the known blind spot | |

**User's choice:** Run validate twice

---

## Claude's Discretion

- Exact JSON formatting/key ordering in `plugin.json` and `marketplace.json`.
- Whether `LICENSE` uses the canonical MIT template verbatim or a lightly reformatted equivalent.

## Deferred Ideas

None — discussion stayed within phase scope.
