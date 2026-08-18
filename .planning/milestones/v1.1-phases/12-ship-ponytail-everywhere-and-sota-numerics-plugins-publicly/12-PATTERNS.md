# Phase 12: Ship ponytail-everywhere and sota-numerics plugins publicly - Pattern Map

**Mapped:** 2026-08-17
**Files analyzed:** 6 (2 new READMEs, 2 bug-fixed test scripts, 1 marketplace.json edit, 2 new LICENSE copies counted as one pattern)
**Analogs found:** 6 / 6

This is a repo-topology/publishing phase, not a feature phase — no new application logic. All
"files to create" are either (a) verbatim copies of already-shipped code with zero content
change, (b) a JSON edit to an existing file, or (c) a one-line bug fix in an already-existing
test script. Pattern extraction below is scoped to those three categories.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `davdittrich/ponytail-everywhere` repo (fresh `git init` + push) | config/scaffold | batch (one-shot repo creation) | Phase 7 `07-02-PLAN.md` `gh repo create --source=.` sequence | role-match (adapted: external dir, not `.`) |
| `davdittrich/sota-numerics` repo (fresh `git init` + push) | config/scaffold | batch | same as above | role-match |
| `ponytail-everywhere/README.md` (new file in new repo) | doc | transform (template fill) | `gsd-beads/README.md` | exact (D-09 mandates identical structure) |
| `sota-numerics/README.md` (new file in new repo) | doc | transform | `gsd-beads/README.md` | exact |
| `ponytail-everywhere/LICENSE` (new file, copy) | config | file-I/O (verbatim copy) | `gsd-beads/LICENSE` | exact (byte-identical, only line 3 copyright year/name stays same) |
| `sota-numerics/LICENSE` (new file, copy) | config | file-I/O | `gsd-beads/LICENSE` | exact |
| `ponytail-everywhere/tests/test-session-start.sh` (edit: `REPO_ROOT`) | test | request-response (shell smoke test) | itself, pre-extraction version (this repo) — `sota-numerics/tests/test-session-start.sh` as sibling analog for the exact line shape | exact (same bug, same fix, both files) |
| `sota-numerics/tests/test-session-start.sh` (edit: `REPO_ROOT`) | test | request-response | sibling `ponytail-everywhere/tests/test-session-start.sh` | exact |
| `.claude-plugin/marketplace.json` (edit in `gsd-beads`) | config | CRUD (2 of 3 entries updated) | itself — current 3-entry file already at `gsd-beads` root | exact (in-place edit, no new file) |

## Pattern Assignments

### `davdittrich/ponytail-everywhere` and `davdittrich/sota-numerics` repo creation

**Analog:** `.planning/phases/07-git-history-hygiene-public-release-prep/07-02-PLAN.md` (lines ~31-42, 135-137, 245)

Phase 7 precedent, run **in-place** against `gsd-beads` itself (already a git repo):
```text
gh repo create davdittrich/gsd-beads --public --source=.
```
No `--add-readme`, `--gitignore`, or `--license` flags (D-05 of Phase 7 — avoids a conflicting
initial commit on the remote that would force a non-fast-forward push). No `--push` flag either
in that plan — push was a separate explicit step gated behind a human checkpoint (P-07: never
push before explicit approval — a public repo's history is not un-publishable).

**Adaptation required for Phase 12** (per 12-RESEARCH.md's own recommended sequence — do not
literally reuse `--source=.`): `ponytail-everywhere/` and `sota-numerics/` are subdirectories
with no `.git` of their own, so the source directory must first be an independent git repo:
```bash
mkdir -p /tmp/<plugin>-extract && cp -r <repo>/<plugin>/. /tmp/<plugin>-extract/
# fix REPO_ROOT bug in tests/test-session-start.sh here (see below) before first commit
cp <repo>/LICENSE /tmp/<plugin>-extract/LICENSE
# write README.md here (see README pattern below)
cd /tmp/<plugin>-extract && git init -b main
git add -A && git commit -m "..."
gh repo create davdittrich/<plugin> --public --source=. --push
```
Same P-07 rule applies: do not edit `marketplace.json` (the irreversible discovery step) until
`claude plugin validate . --strict` and the marketplace add/install/uninstall round trip (D-10)
both pass against the pushed repo.

---

### `ponytail-everywhere/README.md`, `sota-numerics/README.md` (doc, transform)

**Analog:** `/home/dd/projects/gsd-beads/README.md` (full file, 116 lines)

Exact section order to replicate per D-09, taken verbatim from the analog's headings:
```text
# <plugin-name>

<one-line description>

## What it does
...
## Requirements
- <plugin-specific requirements — ponytail/sota-numerics are stdlib-only bash+Python,
  no `bd` dependency; do not copy the `bd on PATH` bullet, it is beads-lifecycle-specific>
- gsd-core >= <version>

## Install

\`\`\`bash
claude plugin marketplace add davdittrich/gsd-beads
claude plugin install <plugin-name>@gsd-beads -y
\`\`\`

## Uninstall

\`\`\`bash
claude plugin uninstall <plugin-name> -y
\`\`\`

## Caveats
- <plugin-specific caveats — e.g. advisory-only, no blocking behavior for ponytail;
  sota-numerics DOES have a blocking plan:post gate, must be called out per its own
  plugin.json description>

## License

MIT — see [LICENSE](LICENSE).

## gsd-core

`<plugin-name>` is a capability for [gsd-core](https://github.com/open-gsd/gsd-core). See that
project for the base planning framework this capability extends.
```

Key deviations from the analog to make explicit in the plan (do not blindly copy beads-specific
prose):
- Install/marketplace source is still `davdittrich/gsd-beads` (marketplace stays hosted there per
  D-02) — only the plugin `name`/`source` differs, not the marketplace repo.
- Drop the analog's "Why not just use gsd-core's built-in tracking?" comparison table (lines
  20-38) — that section is `beads-lifecycle`-specific content, no equivalent needed for an
  advisory-only or gate-only plugin.
- Drop the analog's beads-specific Caveats bullets (lines 92-107, `bd` on PATH, Dolt backend,
  `bd prime --hook-json`) — replace with `ponytail-everywhere`'s/`sota-numerics`'s own caveats
  drawn from each plugin's `.claude-plugin/plugin.json` description and `hooks/session-start.sh`
  behavior (already-written, read those files for the accurate caveat text — do not invent).

---

### `ponytail-everywhere/LICENSE`, `sota-numerics/LICENSE` (config, file-I/O)

**Analog:** `/home/dd/projects/gsd-beads/LICENSE` (full file, 21 lines, MIT)

Byte-identical copy, no edits — `plugin.json` in both subdirectories already declares
`"license": "MIT"`, and the copyright holder (`Dennis A. V. Dittrich`) is the same person/repo
owner across all three repos:
```text
MIT License

Copyright (c) 2026 Dennis A. V. Dittrich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
...
```

---

### `ponytail-everywhere/tests/test-session-start.sh`, `sota-numerics/tests/test-session-start.sh` (test, request-response)

**Analog:** the file itself (sibling copy already shows the exact fix shape) —
`/home/dd/projects/gsd-beads/sota-numerics/tests/test-session-start.sh` line 8:

**Current (buggy after extraction) line:**
```bash
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
```
This resolves two levels up from `tests/`, correct only while `tests/` sits at
`<gsd-beads>/sota-numerics/tests/` (two levels below the `gsd-beads` root). Once
`sota-numerics/` becomes its own repo root, `tests/` is one level below the new root, and `../..`
climbs one level too far — outside the new repo entirely — breaking every path built from
`SCRIPT=`/`PLUGIN_DIR=` (lines 9-10) that depends on `REPO_ROOT`.

**Required fix (both files, same edit):**
```bash
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
```
And correspondingly, `SCRIPT`/`PLUGIN_DIR` lines drop the now-redundant `<plugin>/` path
component (since `REPO_ROOT` now already points at the plugin's own new-repo root):
```bash
SCRIPT="$REPO_ROOT/hooks/session-start.sh"
PLUGIN_DIR="$REPO_ROOT"
```
Verified confirmed bug from 12-RESEARCH.md — apply this fix to the **extracted copy** in
`/tmp/<plugin>-extract/tests/test-session-start.sh` before the first `git commit` (per the
extraction sequence above), not after. The rest of the test file (the `mk_scratch`/injection-guard
cases, lines 12-93) needs no change — untouched analog.

---

### `.claude-plugin/marketplace.json` (config, CRUD — edit in place)

**Analog:** itself, current state (`/home/dd/projects/gsd-beads/.claude-plugin/marketplace.json`, full 26 lines)

Current 2 entries to change (lines 14-23):
```json
{
  "name": "ponytail-everywhere",
  "source": "./ponytail-everywhere",
  "description": "Advisory-only lazy-ladder discipline reminders across gsd's plan/execute/verify/ship lifecycle"
},
{
  "name": "sota-numerics",
  "source": "./sota-numerics",
  "description": "SOTA-research/numerical-stability advisory steering across gsd's plan/execute/verify/ship lifecycle, plus a blocking plan:post gate that mechanically enforces a compliant Alternatives Considered section on every plan in a phase"
}
```
Target shape (per 12-RESEARCH.md's confirmed official schema — `github`-type source object,
unpinned, no `ref`/`sha`, matching this repo's existing unpinned-source style):
```json
{
  "name": "ponytail-everywhere",
  "source": { "source": "github", "repo": "davdittrich/ponytail-everywhere" },
  "description": "Advisory-only lazy-ladder discipline reminders across gsd's plan/execute/verify/ship lifecycle"
},
{
  "name": "sota-numerics",
  "source": { "source": "github", "repo": "davdittrich/sota-numerics" },
  "description": "SOTA-research/numerical-stability advisory steering across gsd's plan/execute/verify/ship lifecycle, plus a blocking plan:post gate that mechanically enforces a compliant Alternatives Considered section on every plan in a phase"
}
```
`beads-lifecycle` entry (lines 9-13, `"source": "./"`) is untouched (D-02) — do not edit it.
`description` strings are untouched — copied verbatim from the current file, only `source` changes.

Sequencing rule (P-07 analog from Phase 7, restated by 12-RESEARCH.md's Anti-Patterns section):
this edit happens **last**, only after both new repos pass `claude plugin validate . --strict`
and the D-10 marketplace add/install/uninstall round trip. A premature edit here points
installers at a source that may not exist yet or may fail validation.

## Shared Patterns

### Repo-split extraction sequence (applies to both new repos identically)

**Source:** 12-RESEARCH.md "Recommended Extraction Sequence" (verbatim 8-step sequence, confirmed
against `gh repo create --help` and this repo's Phase 7 precedent)
**Apply to:** both `ponytail-everywhere` and `sota-numerics` plan tasks
```text
1. mkdir -p /tmp/<plugin>-extract && cp -r <repo>/<plugin>/. /tmp/<plugin>-extract/
2. Fix REPO_ROOT bug in /tmp/<plugin>-extract/tests/test-session-start.sh
3. cd /tmp/<plugin>-extract && git init -b main
4. Add LICENSE (MIT, copied verbatim from gsd-beads root)
5. Write README.md (D-09 structure, see pattern above)
6. git add -A && git commit -m "..."   (D-03: single fresh-init commit, no imported history)
7. gh repo create davdittrich/<plugin> --public --source=. --push
8. Fresh-clone verify: claude plugin validate . --strict; marketplace add/install/uninstall round trip (D-10)
```
Only after step 8 passes for a given plugin: `git rm -r <plugin>/` from `gsd-beads` and edit
`marketplace.json` for that plugin's entry.

### Anti-pattern: nested/embedded git repo

**Source:** 12-RESEARCH.md Standard Stack "Alternatives Considered" table
**Apply to:** both extractions
Never run `git init` in place inside `gsd-beads/<plugin>/` while its files are still tracked by
the parent repo — this creates an embedded-gitlink warning in the parent's `git status` and risks
committing a broken gitlink on a stray `git add`. Always extract to a location outside the
`gsd-beads` working tree (`/tmp/<plugin>-extract` or equivalent) first.

## No Analog Found

None — every file this phase touches has a byte-for-byte or structurally exact precedent already
in this repo (Phase 5/7/8's `beads-lifecycle` publication, or the plugin subdirectories' own
already-written content).

## Metadata

**Analog search scope:** `gsd-beads` repo root (`README.md`, `LICENSE`, `.claude-plugin/marketplace.json`),
`ponytail-everywhere/`, `sota-numerics/` subdirectories, `.planning/phases/07-*` and `.planning/phases/08-*`
**Files scanned:** README.md, LICENSE, marketplace.json, both `tests/test-session-start.sh`, Phase 7 `07-02-PLAN.md`
**Pattern extraction date:** 2026-08-17
</content>
