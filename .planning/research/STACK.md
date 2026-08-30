# Technology Stack

**Project:** gsd-beads v1.4 — Native Task Content Resolution
**Researched:** 2026-08-30
**Overall confidence:** MEDIUM (the source-hierarchy classifier returned
MEDIUM; the critical runtime observations were made against the installed
binaries).

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|---|---:|---|---|
| gsd-core native `taskContentResolver` | 1.12.0 | Resolve external task content at `gsd-tools task resolve-content` | This is the upstream-supported replacement for Patch 2. It parses `tracker-id` verbatim, invokes one matching feature-capability resolver through an argv-only, bounded subprocess, and hard-halts on ambiguity, non-zero exit, timeout, or malformed output. |
| Beads capability manifest | 0.4.0 → next patch release | Declare `trackerPrefix: "beads"` and the resolver invocation | The capability is already `role: "feature"`, the only role permitted to declare this field. Keep the existing overlay model; do not modify gsd-core. |
| Python stdlib adapter in existing `scripts/sync.py` | Python 3.14.7 observed | Convert one live `bd show <id> --json` response into gsd-core's one-object resolver contract | It reuses the only existing Beads protocol adapter and its subprocess/error-handling conventions. It avoids a second implementation of Beads JSON parsing, a new package, and another release surface. |

### Database / Tracker

| Technology | Version | Purpose | Why |
|---|---:|---|---|
| Beads `bd` CLI | 1.2.2 (live) | Authoritative task record and JSON read boundary | `bd show <id> --json` is the supported automation interface and returns the live issue `description` and `acceptance_criteria`. Do not read `.beads/issues.jsonl`; it is an export, not the database API. |

### Infrastructure

| Technology | Version | Purpose | Why |
|---|---:|---|---|
| `spawnSync` boundary inside gsd-core | 1.12.0 | Execute resolver with deterministic argv and timeout | gsd-core replaces only whole `"{{id}}"` argument tokens, sets a timeout, and rejects non-object JSON. The adapter must emit one JSON object; raw `bd show --json` emits an array and is therefore invalid. |
| `tracker-id="beads:<id>"` | v1.4 migration format | Native lookup identity on `auto` and `tracer` tasks | The core parser retains it verbatim and splits only at the first colon. Keep `<beads-id>` in parallel for legacy execution and existing Beads lifecycle logic. Never add it to `checkpoint:*` tasks. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---|---:|---|---|
| Python `json`, `subprocess`, `argparse`, `pathlib` | stdlib / Python 3.14.7 observed | Decode the single-row CLI response, validate its shape, expose a narrow resolver subcommand | Use only these existing modules. No SDK, `pydantic`, `requests`, `jq`, or Node package is justified. |

## Required Resolver Mechanism

Declare one `taskContentResolver` on the `beads` feature capability. Use
`binary: "python3"` and an `args` array of `"-c"`, a stdlib-only locator
program, and `"{{id}}"` as a separate final argv element. The locator must
resolve exactly. The `-c` value is one newline-delimited Python source string
whose content is:

```python
import os
import sys
from pathlib import Path

p = Path(os.environ.get("GSD_HOME") or Path.home()) / \
    ".gsd/capabilities/beads/scripts/sync.py"
os.execv(sys.executable, [
    sys.executable,
    str(p),
    "resolve-task-content",
    sys.argv[1],
])
```

Set `timeoutMs` to 10,000. The effective declaration is therefore
`python3 -c <source-above> {{id}}`, with `{{id}}` still one distinct element in
the manifest's `args` array.

This keeps `{{id}}` an isolated argv token throughout gsd-core expansion and
the Python bootstrap. The adapter must return exactly one JSON object with at
least a non-blank `description`; optional supported fields are `verify`,
`acceptance_criteria`, `read_first`, and `done`.

The adapter must invoke `bd show <id> --json`, require exactly one object with
the requested id, map its structured fields, write JSON only to stdout, and
exit non-zero for an absent/ambiguous result, `bd` failure, invalid JSON, or
unusable content. That preserves core's hard-halt behavior; it must not fall
back to stripped or legacy `PLAN.md` prose. The bootstrap provides the required
installed-capability path without a source-tree-relative assumption.

Live proof, run from non-root cwd
`/home/dd/projects/gsd-beads/plugins/beads-lifecycle` on 2026-08-30:

```text
locator=/home/dd/.gsd/capabilities/beads/scripts/sync.py
is_file=True
```

The broader upstream improvement—a documented capability-root placeholder in
the resolver contract—is deferred. It is useful generalization work, not a
blocker for this fixed, runtime-owned `GSD_HOME` locator.

## Alternatives Considered

Ranking is by: (1) performance, (2) implementation size/simplicity,
(3) ecosystem support, and (4) maintenance burden. Performance matters only
after contract correctness; an invalid direct call cannot win.

| Rank | Category | Option | Performance | Lines / simplicity | Ecosystem support | Maintenance | Decision |
|---:|---|---|---|---|---|---|---|
| 1 | Bootstrap + adapter | `python3 -c` locator then existing stdlib `sync.py` | One Python bootstrap, one adapter, one `bd` read; adequate for one task | No new file; locator is a static manifest value and reuses `run_bd`, parsing, and error conventions | Uses installed Python and official `bd --json` boundary | One owner for all Beads protocol translation | **Choose.** |
| 2 | Path | Project-relative `plugins/.../scripts/sync.py` | Same process cost | Short in a source checkout | Does not describe an installed capability | Breaks from another project cwd, runtime, or installed copy | Reject: source-tree-only paths are too narrow. |
| 3 | Executable | Add a PATH shim for `sync.py` | Similar or faster startup only if separately installed | Requires a wrapper and install plumbing | No existing resolver executable; live `sync.py` mode is 0644 | Must manage install, update, uninstall, PATH precedence, and name collisions | Reject: larger lifecycle surface for no capability gain. |
| 4 | Adapter | New standalone Python resolver module/script | Same process cost | Duplicates invocation, validation, and path rules | No added dependency | Two parsers can drift | Reject: no capability gained. |
| 5 | Adapter | New Node/TypeScript resolver | Comparable or worse cold-start cost; still spawns `bd` | New program, build/test surface, and JSON bridge | Node is present with gsd-core but is not this capability's existing adapter runtime | Cross-language duplication and release coupling | Reject: no measurable benefit. |
| 6 | Manifest | Invoke `bd show {{id}} --json` directly | Fastest possible subprocess chain | One manifest declaration | Official CLI command, but output is an array | Low only if it worked | Reject: gsd-core requires a plain JSON object and treats the Beads array as malformed output. |
| 7 | Upstream | Add a capability-root invocation placeholder to gsd-core | Potentially removes the bootstrap later | More core design, validation, and compatibility work | General ecosystem improvement | New upstream dependency and release coordination | Defer: beneficial, but not a v1.4 blocker. |
| 8 | Dependency | Add an SDK/schema library (`pydantic`, a Beads client, or `jq`) | No material gain | More dependency and packaging work | Unneeded for one typed object | Dependency/version/security upkeep | Reject: violates the project’s stdlib-only constraint. |

## Ponytail Ladder Review

1. **Need:** Yes. Patch 2 conflicts with the upstream seam on each gsd-core upgrade.
2. **Already present:** Yes. `sync.py` is the current, tested Beads CLI adapter.
3. **Stdlib:** Sufficient for argv execution and JSON mapping.
4. **New dependency:** Not justified.

Result: use the `python3 -c` stdlib locator and extend the existing adapter by
the smallest resolver-only command. Do not construct a PATH shim, abstraction,
SDK wrapper, or fallback layer.

## Critical Contract and Live Constraints

| Constraint | Stack consequence | Evidence confidence |
|---|---|---:|
| Resolver registration is feature-only; a prefix must be unique; invocation requires `binary`, string `args` containing `{{id}}`, and `0 < timeoutMs <= 120000`. | Keep one `beads` resolver with a bounded argv declaration; validate the final manifest using the installed validator. | 95/100 |
| Core finds a task by exact `tracker-id`, then hard-fails resolver ambiguity, command failure, timeout, and malformed/non-object stdout. | Add identity only to executable `auto`/`tracer` tasks and treat adapter errors as non-zero exits. Do not provide a PLAN fallback. | 95/100 |
| Live `bd show gsd-beads-xy2 --json` (v1.2.2) returned a one-element JSON array containing `id`, `description`, and `acceptance_criteria`. | The adapter—not the manifest—must unwrap and validate the row before emitting the core object. | 100/100 |
| Current `sync.py` reads/writes `<beads-id>` and already routes all `bd` commands through `run_bd`; it has no resolver CLI yet. | Add one narrowly scoped subcommand rather than alter lifecycle commands or issue ownership semantics. | 95/100 |
| From non-root cwd, the prescribed locator resolved `/home/dd/.gsd/capabilities/beads/scripts/sync.py` and `is_file=True`. | The declared bootstrap reaches the globally installed capability without relying on the project checkout path. | 100/100 |
| The installed script is mode 0644 and neither `beads-resolve-task-content` nor `beads-sync` is on `PATH`. | Do not invent an executable shim and its install/update/uninstall/collision lifecycle. | 100/100 |

## Installation

No new packages.

```bash
# Required runtime already observed in this workspace
bd --version                 # 1.2.2
python3 --version            # 3.14.7
node /home/dd/.codex/gsd-core/bin/gsd-tools.cjs runtime-identity \\
  --raw  # gsd-core 1.12.0
```

## Evidence Appraisal

The central claim—native core resolution plus the existing stdlib adapter—is
**strong**. The installed gsd-core source directly establishes the resolver
contract and failure semantics, the live CLI establishes the Beads output
shape, and the non-root locator proof establishes the chosen static invocation
path. A source-tree-only invocation would be a false success; the approved
`GSD_HOME` bootstrap avoids it.

Competing explanations considered:

- Direct `bd` invocation could remove the adapter, but its array output
  violates the core's plain-object contract.
- A fresh Node/Python adapter could make packaging look cleaner, but it
  duplicates the existing trusted boundary without improving the required
  output or failure behavior.
- A PATH shim could hide the capability location, but no suitable executable
  exists today and the shim would create unmanaged lifecycle and collision
  risks that the stdlib locator does not have.

## Sources

- Installed `@opengsd/gsd-core` 1.12.0: [task command router](/home/dd/.codex/gsd-core/bin/lib/task-command-router.cjs:92),
  [task-content resolution](/home/dd/.codex/gsd-core/bin/lib/task-content-resolution.cjs:302),
  [plan document parser](/home/dd/.codex/gsd-core/bin/lib/plan-document.cjs:123),
  and [capability validator](/home/dd/.codex/gsd-core/bin/lib/capability-validator.cjs:733).
  Source-hierarchy confidence: MEDIUM; direct installed-runtime match: 95/100.
- Live `bd` 1.2.2 `show --help` and `bd show gsd-beads-xy2 --json`, run
  2026-08-30. Direct observation confidence: 100/100.
- [Official Beads documentation](https://github.com/gastownhall/beads/blob/main/docs/index.md)
  and [official reference index](https://github.com/gastownhall/beads/blob/main/docs/reference/index.md),
  current crawl checked 2026-08-30. Source-hierarchy confidence: MEDIUM.
- Existing capability [manifest](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json:1)
  and [sync adapter](/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py:300).
  Direct code match confidence: 95/100.
- Live locator proof and mode/PATH inspection, run 2026-08-30 from
  `plugins/beads-lifecycle`: installed target exists; `sync.py` mode is 0644;
  no `beads-resolve-task-content` or `beads-sync` executable is present.
  Direct observation confidence: 100/100.
