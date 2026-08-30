# Requirements: beads capability for gsd-core — v1.4 Native Task Content Resolution

**Defined:** 2026-08-30
**Core Value:** `bd` is the single source of truth for gsd task state; no
duplicated task-state bookkeeping survives in `.planning/`.
**Scope:**
[davdittrich/gsd-beads#6](https://github.com/davdittrich/gsd-beads/issues/6)
and Beads issue `gsd-beads-xy2` only.

## v1.4 Requirements

### Resolver Invocation

- [ ] **RES-01**: An eligible task invokes the globally installed `sync.py`
  through the approved Python standard-library bootstrap, resolving the install
  through `GSD_HOME` or `Path.home()`, replacing the bootstrap process with
  `os.execv`, and passing the tracker id as a separate argv element.
- [ ] **RES-02**: Live `bd show --json` content is losslessly normalized into
  gsd-core's `description`, `read_first`, `verify`,
  `acceptance_criteria`, and `done` fields, including deterministic
  singleton-envelope validation, Markdown-section extraction, and scalar
  criteria splitting compatible with gsd-core.
- [ ] **RES-03**: Missing installed scripts, unavailable or failing `bd`,
  timeouts, ambiguous results, malformed JSON, invalid envelopes, and unusable
  content halt execution with a precise diagnostic and never fall back to
  `PLAN.md` task prose.

### Task Identity

- [ ] **ID-01**: Every eligible `auto` or `tracer` task gains
  `tracker-id="beads:<id>"` while retaining `<beads-id>`; repeated
  synchronization produces a byte-identical plan and never duplicates Beads
  issues.
- [ ] **ID-02**: Checkpoint tasks never gain `tracker-id` and preserve their
  existing human-decision and human-verification behavior.

### Native Cutover

- [ ] **CUT-01**: The installed capability resolves a real task from live Beads
  through gsd-core's public `task resolve-content` command, with source,
  project-installed, and global-installed capability bytes proven identical.
- [ ] **CUT-02**: Patch 2 and all of its checker, marker, installer, and
  documentation wiring are removed only after CUT-01 and the isolated
  negative-path checks pass; Patch 1 remains installed and independently
  verified.

## Future Requirements

None. Capability-root-relative resolver execution may be proposed upstream if
another capability demonstrates the same need; it is not required by or tracked
in this milestone.

## Out of Scope

| Feature | Reason |
|---|---|
| PATH shim or installed console command | Adds executable ownership, PATH, collision, update, and uninstall machinery when the Python stdlib bootstrap already resolves the owned global bundle. |
| New runtime dependency | Python 3 and `bd` already cover the complete adapter; no SDK, `jq`, package, or wrapper is justified. |
| Direct raw-`bd` resolver output | The live envelope, criteria type, and Markdown-encoded task sections do not satisfy gsd-core's resolver schema without translation. |
| gsd-core capability-root or cwd extension | Architecturally useful but unnecessary for the documented global auto-install contract. |
| Removal of legacy `<beads-id>` | Existing lifecycle status, dependency, close-wave, and reconciliation paths still consume it. |
| Cache, retry loop, telemetry, or multi-tracker abstraction | No observed requirement justifies non-live content, hidden authoritative-state failures, or a generalized second pipeline. |
| Patch 1 retirement | Patch 1 covers an independent `ship:pre` dispatch gap and is explicitly preserved. |

## Traceability

| Requirement | Phase | Plan | Beads | Status |
|---|---|---|---|---|
| RES-01 | Phase 19 | TBD | TBD | Pending |
| RES-02 | Phase 19 | TBD | TBD | Pending |
| RES-03 | Phase 19 | TBD | TBD | Pending |
| ID-01 | Phase 20 | TBD | TBD | Pending |
| ID-02 | Phase 20 | TBD | TBD | Pending |
| CUT-01 | Phase 21 | TBD | TBD | Pending |
| CUT-02 | Phase 21 | TBD | TBD | Pending |

**Coverage:**

- v1.4 requirements: 7 total
- Mapped to phases: 7
- Unmapped: 0

---

Requirements defined: 2026-08-30
