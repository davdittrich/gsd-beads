# Phase 15: Ship markdown-linting and pr-workflow plugins publicly - Pattern Map

**Mapped:** 2026-08-18
**Files analyzed:** 8 (2 new `.claude-plugin/plugin.json`, 2 new `hooks/` wrappers, 2 new READMEs,
2 new LICENSE copies, 1 `marketplace.json` edit)
**Analogs found:** 8 / 8 (all cross-repo/historical — no live in-repo plugin-tree analog exists,
see CRITICAL DIVERGENCE below)

## CRITICAL DIVERGENCE FROM 15-CONTEXT.md's ASSUMPTION — READ FIRST

15-CONTEXT.md and the phase framing ("following Phase 12's extraction playbook verbatim") assume
`markdown-linting/` and `pr-workflow/` exist today as **subdirectories with the same shape
`ponytail-everywhere/` and `sota-numerics/` had before Phase 12 extracted them** — i.e. a
`.claude-plugin/plugin.json` + `hooks/` (SessionStart auto-install) + `.gsd/capabilities/<id>/` +
`tests/` tree at `<repo-root>/<plugin>/`.

**That is false as of this repo's current state.** Verified via `git ls-files` and `find`:

- `ponytail-everywhere/` and `sota-numerics/` no longer exist at all (Phase 12 Plan 04 already
  removed them after extraction — confirmed absent).
- `markdown-linting/` and `pr-workflow/` **never existed as top-level plugin-tree subdirectories**.
  Phase 13/14 built them directly as `.gsd/capabilities/markdown-linting/` and
  `.gsd/capabilities/pr-workflow/` bundles only — `capability.json`, `scripts/`, `skills/`,
  `tests/`, (markdown-linting also has `config/` and `README.md`). Neither has a
  `.claude-plugin/plugin.json`, a `hooks/` directory, or any `CLAUDE_PLUGIN_ROOT`-relative
  wrapper. Confirmed: both capability.json files declare `"hooks": []`.
- `beads-lifecycle` itself was also relocated since Phase 12: it now lives at
  `plugins/beads-lifecycle/` (not repo root), and `marketplace.json`'s `beads-lifecycle` entry
  source changed to `"./plugins/beads-lifecycle"`.

**Consequence for the planner:** this phase is NOT a copy-and-fix-two-lines extraction like
Phase 12. It requires **constructing a new plugin wrapper from scratch** for each capability
(`.claude-plugin/plugin.json` + `hooks/hooks.json` + `hooks/session-start.sh` +
`hooks/capability-auto-install.sh`, vendored per Phase 10.1 D-05) around the existing
`.gsd/capabilities/<id>/` bundle, THEN run Phase 12's extraction sequence (staging outside the
tree, fresh git init, `gh repo create --source=. --push`, validate, marketplace edit). The
`.claude-plugin/plugin.json` and `hooks/` analogs below are therefore drawn from
`plugins/beads-lifecycle/` (the only live in-repo plugin-tree example) and from Phase 12's
SUMMARY files (the ponytail/sota-numerics shape, no longer present locally but documented there),
not from a `markdown-linting/`-local file that does not exist.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `markdown-linting/.claude-plugin/plugin.json` (new, in staging) | config | CRUD (manifest) | `plugins/beads-lifecycle/.claude-plugin/plugin.json` | role-match (shape only — beads-lifecycle has no `config`/`steps`/`gates` keys to copy) |
| `pr-workflow/.claude-plugin/plugin.json` (new, in staging) | config | CRUD | same | role-match |
| `markdown-linting/hooks/{hooks.json,session-start.sh,capability-auto-install.sh}` (new, in staging) | middleware | event-driven (SessionStart) | `plugins/beads-lifecycle/hooks/*` | role-match (session-start.sh content differs — beads-lifecycle's is PRIME.md self-heal + capability grant; markdown-linting/pr-workflow need only the capability grant call) |
| `pr-workflow/hooks/*` (new, in staging) | middleware | event-driven | same | role-match |
| `markdown-linting/README.md` (new, in new repo) | doc | transform | Phase 12's `ponytail-everywhere/README.md`/`sota-numerics/README.md` (12-01/02-PLAN.md Task 2 `<action>` block — structure only, files no longer exist locally) + `.gsd/capabilities/markdown-linting/README.md` (content source, still exists) | exact structure / exact content source |
| `pr-workflow/README.md` (new, in new repo) | doc | transform | same pattern, content from `.gsd/capabilities/pr-workflow/capability.json` (no README.md exists for pr-workflow — must be authored from capability.json + scripts, not copied) | exact structure, partial content source |
| `markdown-linting/LICENSE`, `pr-workflow/LICENSE` (new, copy) | config | file-I/O | `gsd-beads/LICENSE` (repo root, still exists) | exact (byte-identical copy, same as Phase 12) |
| `.claude-plugin/marketplace.json` (edit in `gsd-beads`) | config | CRUD | itself — current 3-entry file (`beads-lifecycle` local, `ponytail-everywhere`/`sota-numerics` already `"source":"url"` git sources) | exact — the target shape already exists twice in the same file |

## Pattern Assignments

### `.claude-plugin/plugin.json` for markdown-linting / pr-workflow

**Analog:** `/home/dd/projects/gsd-beads/plugins/beads-lifecycle/.claude-plugin/plugin.json` (full file, 9 lines)

```json
{
  "name": "beads-lifecycle",
  "version": "1.2.1",
  "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle",
  "author": {
    "name": "Dennis A. V. Dittrich",
    "email": "davdittrich@gmail.com"
  },
  "license": "MIT",
  "skills": ["./.agents/skills/beads"]
}
```

Adapt for each new plugin (per D-01 of 15-CONTEXT.md: start both at `"version": "0.1.0"`, not
beads-lifecycle's `1.2.1`):
```json
{
  "name": "markdown-linting",
  "version": "0.1.0",
  "description": "Wraps rumdl over .planning/, README.md, and CLAUDE.md; verify:post writes a gate-readable violation-count report, ship:pre gates advisorily on it.",
  "author": { "name": "Dennis A. V. Dittrich", "email": "davdittrich@gmail.com" },
  "license": "MIT",
  "skills": ["./.agents/skills/markdown-linting-report"]
}
```
`description` is copied verbatim from `.gsd/capabilities/markdown-linting/capability.json`'s
`description` field (already read and quoted above). Same for `pr-workflow`, description from
`.gsd/capabilities/pr-workflow/capability.json`.

**Open question the planner must resolve (not this mapper's call):** beads-lifecycle's
`skills` array points at `.agents/skills/beads` (a Claude Code *skill* dir), while
markdown-linting/pr-workflow's skills (`markdown-linting-report`, `pr-workflow-report`) currently
live at `.gsd/capabilities/<id>/skills/<id>-report/` — a gsd-core capability skill, different
directory convention. Whether the new plugin manifest's `skills` key should point there, be
omitted, or whether the whole `.gsd/capabilities/<id>/` tree needs relocating to
`.agents/skills/` inside the staged repo needs research/planner resolution — flag for
RESEARCH-equivalent scrutiny during planning since RESEARCH.md doesn't exist for this phase.

---

### `hooks/` wrapper for markdown-linting / pr-workflow

**Analog:** `/home/dd/projects/gsd-beads/plugins/beads-lifecycle/hooks/hooks.json` and `session-start.sh` (full files, both short)

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"", "type": "command" } ], "matcher": "" }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
set -u
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
bash "$PLUGIN_ROOT/hooks/capability-auto-install.sh" beads || true
```
(beads-lifecycle's version also self-heals `.beads/PRIME.md` and execs `bd prime` — that part is
beads-specific and must NOT be copied; markdown-linting/pr-workflow need only the
`capability-auto-install.sh <cap-id>` call, matching Phase 10.1 D-05's vendored-copy-per-plugin
pattern that `ponytail-everywhere`/`sota-numerics` already used before their own extraction.)

`capability-auto-install.sh` itself: **vendor a byte-identical copy** per Phase 10.1 D-05 (the
comment in beads-lifecycle's own copy explicitly names `ponytail-everywhere`'s sibling copy as
the byte-identical reference — same vendoring rule applies here, just with a third and fourth
sibling). Source: `/home/dd/projects/gsd-beads/plugins/beads-lifecycle/hooks/capability-auto-install.sh`
(full file — validates `CAP_ID` shape, hashes the bundle dir, grants at user scope, `set -u`, no
`set -e`, never aborts the session). Only the `CAP_ID="${1:-}"` caller argument changes
(`markdown-linting` / `pr-workflow` instead of `beads`), passed by the new `session-start.sh`.

---

### `README.md` for the two new repos

**Analog (structure):** Phase 12's D-09 section order, per `12-01-PLAN.md` Task 2 `<action>`
block (files themselves no longer exist locally, but the mandated order is documented verbatim
there): H1 title, one-line description, `## What it does`, `## Requirements`, `## Install`,
`## Uninstall`, `## Caveats`, `## License`, `## gsd-core`.

**Analog (content, markdown-linting only):** `.gsd/capabilities/markdown-linting/README.md`
(still exists, 40+ lines) already contains accurate "What it does" prose (verify:post step,
LINT-REPORT.md regeneration, advisory ship:pre gate, both config keys with defaults) and an
"Install" section describing the 3-tier `rumdl` resolution (`PATH` → `uvx rumdl` → fallback) —
reuse this prose directly rather than inventing it, just re-home it under the mandated section
headers and drop anything referencing gsd-beads-internal paths.

**Content for pr-workflow:** no equivalent README.md exists in `.gsd/capabilities/pr-workflow/`
— author from `capability.json` (steps: `execute:wave:post` writes `PR.md`, `ship:post` also
runs; gate: advisory `ship:pre` on `pr_gate_ok`, config keys `pr-workflow.enabled` /
`pr-workflow.ship_gate`) and `.gsd/capabilities/pr-workflow/scripts/pr_status.py` for the `gh`
CLI requirement and auth precondition — do not invent, both files were read this pass.

Install/Uninstall lines, same substitution pattern as Phase 12:
```bash
claude plugin marketplace add davdittrich/gsd-beads
claude plugin install markdown-linting@gsd-beads -y
# ...
claude plugin uninstall markdown-linting -y
```
(swap `pr-workflow` for the sibling repo).

Caveats must state plainly (drawn from capability.json, not invented): both gates are
**advisory, never blocking** (`"blocking": false`, `onError: "skip"`) — this is the opposite
emphasis of sota-numerics' README (which had to call out a *blocking* gate) — do not copy that
framing.

---

### `LICENSE` (config, file-I/O)

**Analog:** `/home/dd/projects/gsd-beads/LICENSE` (root, still present, MIT, unchanged since
Phase 12). Byte-identical copy for both new repos, same as Phase 12's `LICENSE` pattern:
```text
MIT License

Copyright (c) 2026 Dennis A. V. Dittrich
```

---

### `.claude-plugin/marketplace.json` (config, CRUD — edit in place)

**Analog:** itself — current state already shows the exact target shape twice
(`/home/dd/projects/gsd-beads/.claude-plugin/marketplace.json`, full file, read this pass):
```json
{
  "name": "ponytail-everywhere",
  "source": { "source": "url", "url": "https://github.com/davdittrich/ponytail-everywhere.git" },
  "description": "..."
}
```
**Note the schema actually shipped diverges from 12-PATTERNS.md's `{"source":"github","repo":"owner/repo"}`
prediction** — the live file uses `{"source":"url","url":"https://github.com/<owner>/<repo>.git"}`.
Follow the live file, not the stale 12-PATTERNS.md prediction. New entries to append (after
`ponytail-everywhere`/`sota-numerics`, same array):
```json
{
  "name": "markdown-linting",
  "source": { "source": "url", "url": "https://github.com/davdittrich/markdown-linting.git" },
  "description": "Wraps rumdl over .planning/, README.md, and CLAUDE.md; verify:post writes a gate-readable violation-count report, ship:pre gates advisorily on it."
},
{
  "name": "pr-workflow",
  "source": { "source": "url", "url": "https://github.com/davdittrich/pr-workflow.git" },
  "description": "Wraps gh CLI to read PR/check status for the current branch; execute:wave:post writes a gate-readable PR.md report, ship:pre gates advisorily on it."
}
```
`beads-lifecycle` entry stays untouched (still `"./plugins/beads-lifecycle"` — note its own
source path already moved since Phase 12, independent of this phase, do not touch it).

Sequencing rule unchanged from Phase 12: edit `marketplace.json` **last**, only after both new
repos pass `claude plugin validate . --strict` and the D-10 round trip (per 15-CONTEXT.md D-03,
both repos are created in parallel but each still needs its own full proof before this edit).

## Shared Patterns

### Wrapper-then-extract sequence (differs from Phase 12 — extra step 0)

**Source:** synthesized from `plugins/beads-lifecycle/` (live plugin-tree analog) +
`.gsd/capabilities/<id>/` (live capability bundle) + Phase 12's `12-01-PLAN.md`/`12-02-PLAN.md`
extraction sequence (steps 1-8, still valid once step 0 produces a plugin-tree-shaped source dir)
**Apply to:** both `markdown-linting` and `pr-workflow` plan tasks
```text
0. Construct /tmp/<plugin>-extract/{.claude-plugin/plugin.json, hooks/hooks.json,
   hooks/session-start.sh, hooks/capability-auto-install.sh} from the beads-lifecycle analog
   above, then copy .gsd/capabilities/<plugin>/ into /tmp/<plugin>-extract/.gsd/capabilities/<plugin>/
   verbatim (this part IS a straight copy, same as Phase 12's step 1)
1. Add LICENSE (MIT, copied verbatim from gsd-beads root)
2. Write README.md (D-09 structure; content from .gsd/capabilities/<plugin>/README.md if it
   exists, else authored from capability.json + scripts/)
3. cd /tmp/<plugin>-extract && git init -b main
4. git add -A && git commit -m "..."   (fresh-init commit, no imported history, per Phase 12 D-03)
5. gh repo create davdittrich/<plugin> --public --source=. --push
6. Fresh-clone verify: claude plugin validate . --strict; marketplace add/install/uninstall round trip (D-10)
7. Only after both repos pass: edit marketplace.json, append both new entries (schema above)
```
Note: Phase 12's steps 2 ("fix REPO_ROOT bug in tests/test-session-start.sh") does not apply
here — `.gsd/capabilities/markdown-linting/tests/test_lint.py` and
`.gsd/capabilities/pr-workflow/tests/test_pr_status.py` resolve paths via `Path(__file__)`-style
resolution already proven relocation-safe by the sota-numerics precedent (12-02-PLAN.md's explicit
non-edit of `test_check_alternatives.py`) — verify this holds for these two test files during
planning/implementation rather than assuming, since they were not read line-by-line this pass.

### Anti-pattern: nested/embedded git repo

**Source:** Phase 12 `12-PATTERNS.md` (still valid, unchanged)
Never `git init` in place inside `gsd-beads/.gsd/capabilities/<plugin>/` while tracked by the
parent repo. Always stage outside the working tree (`/tmp/<plugin>-extract`).

## No Analog Found

None outright, but flagged above under CRITICAL DIVERGENCE: the `.claude-plugin/plugin.json` and
`hooks/` files have no `markdown-linting`/`pr-workflow`-local analog (they don't exist yet) — the
closest live analog is cross-plugin (`plugins/beads-lifecycle/`), and content must be adapted, not
copied verbatim, unlike every file Phase 12 touched.

## Metadata

**Analog search scope:** `gsd-beads` repo root (`LICENSE`, `.claude-plugin/marketplace.json`),
`plugins/beads-lifecycle/` (live plugin-tree structural analog), `.gsd/capabilities/markdown-linting/`,
`.gsd/capabilities/pr-workflow/` (live capability-bundle content source), Phase 12's
`12-01-PLAN.md`/`12-02-PLAN.md`/`12-PATTERNS.md` (documented but no-longer-locally-present
extraction precedent)
**Files scanned:** `.claude-plugin/marketplace.json`, `plugins/beads-lifecycle/.claude-plugin/plugin.json`,
`plugins/beads-lifecycle/hooks/{hooks.json,session-start.sh,capability-auto-install.sh}`,
`.gsd/capabilities/markdown-linting/{capability.json,README.md}`,
`.gsd/capabilities/pr-workflow/capability.json`, `LICENSE`, Phase 12 CONTEXT/PLAN/PATTERNS files
**Pattern extraction date:** 2026-08-18
</content>
