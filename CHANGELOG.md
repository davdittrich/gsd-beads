# Changelog

Versions in this file track `.gsd/capabilities/beads/capability.json`.

## 0.2.0

### Changed
- **`beads.enabled` now defaults to `true`**: a fresh install runs with issue tracking on out of
  the box. Opting out is now the explicit action — set `beads.enabled: false` in a project's
  `.planning/config.json`. The four beads skills' Step 1 config gates were inverted to match, so
  an absent key resolves to the shipped default rather than stopping at the gate.

### No regression for existing installs
- A project that already sets `beads.enabled` explicitly in `.planning/config.json` keeps its
  current behavior unchanged — an explicit value always wins over the shipped default. Only
  installs that never set the key pick up the new default.
