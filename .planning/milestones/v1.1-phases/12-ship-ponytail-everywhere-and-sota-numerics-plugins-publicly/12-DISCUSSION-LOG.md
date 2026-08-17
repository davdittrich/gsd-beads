# Phase 12: Ship ponytail-everywhere and sota-numerics plugins publicly - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-17
**Phase:** 12-ship-ponytail-everywhere-and-sota-numerics-plugins-publicly
**Areas discussed:** Release archive scope, Versioning & tagging, README depth per plugin, Validation & round-trip scope, Old subdirectory disposition (added mid-discussion)

---

## Release archive scope

| Option | Description | Selected |
|--------|-------------|----------|
| Marketplace-only, no archive | Subdirectory Directory-source install already clean; skip separate archives | ✓ |
| Give them archives too | Match beads-lifecycle's dual-path pattern exactly | |
| One combined archive for all 3 | Single release asset containing all three plugin trees | |

**User's choice:** Marketplace-only, no archive.
**Notes:** None initially — but the immediate follow-up question revealed the real architecture: each plugin needs its own GitHub repo, not a shared repo with subdirectories. See below.

---

## Release CI change

| Option | Description | Selected |
|--------|-------------|----------|
| No change needed | release.yml keeps building only the beads-lifecycle archive | |
| Add version-bump check across all 3 plugin.json | Extend release.yml to verify versions match tag | |

**User's choice:** Free-text revision — "revision, all three need their own github repo, there share one marketplace"
**Notes:** This overturned the phase's working assumption that the existing in-repo subdirectory + Directory-source marketplace entries already constituted "shipped." Triggered a full re-scope of the remaining discussion around 3 separate repos sharing 1 marketplace (see CONTEXT.md D-01 through D-04).

---

## Marketplace host

| Option | Description | Selected |
|--------|-------------|----------|
| gsd-beads hosts marketplace.json | Keep marketplace.json here; other 2 entries become git-sources | ✓ |
| New dedicated marketplace repo | 4th repo just for marketplace.json | |

**User's choice:** gsd-beads hosts marketplace.json.
**Notes:** None.

---

## History (split-out repos)

| Option | Description | Selected |
|--------|-------------|----------|
| Extract with git filter-repo | Preserve Phase 10/10.1/11 commit history via subdirectory-filtered extraction | |
| Fresh init, no history | New repos start clean at current file state | ✓ |

**User's choice:** Fresh init, no history.
**Notes:** None.

---

## Versioning

| Option | Description | Selected |
|--------|-------------|----------|
| Independent per repo | Each plugin versions/tags on its own schedule | ✓ |
| Lockstep versions across all 3 | Shared version number bumped together | |

**User's choice:** Independent per repo.
**Notes:** None.

---

## v1.2.0 tag

| Option | Description | Selected |
|--------|-------------|----------|
| Leave it alone | v1.2.0 stays as-is; no new gsd-beads release required by this phase | ✓ |
| Cut a new gsd-beads release for the marketplace.json change | Bump/tag gsd-beads again once marketplace.json changes | |

**User's choice:** Leave it alone.
**Notes:** None.

---

## READMEs

| Option | Description | Selected |
|--------|-------------|----------|
| Same full structure | Match beads-lifecycle's README section order exactly | ✓ |
| Thinner — install + what-it-does only | Skip caveats/uninstall detail | |

**User's choice:** Same full structure.
**Notes:** None.

---

## Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, full proof per new repo | validate --strict + live marketplace add/install/uninstall round trip, per repo | ✓ |
| Validate only, skip live round-trip | Skip the live install/uninstall proof | |

**User's choice:** Yes, full proof per new repo.
**Notes:** None.

---

## Old subdirs

| Option | Description | Selected |
|--------|-------------|----------|
| Remove them from gsd-beads | Delete the plugin subdirectories once pushed to their own repos | ✓ |
| Keep them as the authoring source | Leave subdirectories in gsd-beads as the edit source, sync to standalone repos on release | |

**User's choice:** Remove them from gsd-beads.
**Notes:** The `.gsd/capabilities/<id>/` dogfood copies at repo root are explicitly a separate, untouched concern — confirmed not to be affected by this removal.

---

## Claude's Discretion

- Exact repo names (default assumption stated: `davdittrich/ponytail-everywhere`,
  `davdittrich/sota-numerics`) — confirm before creating if any doubt.
- Whether gsd-beads itself needs a new tag/release for the marketplace.json update.
- Starting version number for each new repo (v0.1.0 vs v1.0.0).
- Exact marketplace.json git-source schema for cross-repo entries — flagged as a research
  question for gsd-phase-researcher, not a discretion call.
- Order of operations across the two plugins (parallel vs sequential).

## Deferred Ideas

None — discussion stayed within phase scope (after the mid-discussion topology correction, which
is a scope correction, not new work deferred elsewhere).
