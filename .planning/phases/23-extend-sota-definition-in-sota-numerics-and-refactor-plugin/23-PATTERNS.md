# Phase 23: Extend SOTA definition in sota-numerics - Pattern Map

**Mapped:** 2026-09-06
**Files analyzed:** 7
**Analogs found:** 7 / 7

**Repository note:** all target files live in the `sota-numerics` clone at
`/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013` (relative
paths below are relative to that clone's root), NOT in `gsd-beads`. That
worktree is untracked from `gsd-beads`'s perspective (see CONTEXT.md
Deferred `gsd-beads-9tg`) — run `git -C .worktrees/sota-numerics-release-013
ls-files` to confirm tracked status inside that clone's own history, not
`git ls-files` from `gsd-beads`. The `gsd-beads` sibling capability
(`plugins/beads-lifecycle/.gsd/capabilities/beads/`) IS tracked in this repo
and is cited only as a cross-capability shape/convention analog, never as a
file to edit.

## File Classification

| File to modify (in sota-numerics clone) | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.gsd/capabilities/sota-numerics/fragments/planner-sota.md` | config (prompt fragment) | transform (advisory text → prompt injection) | itself, prior revision (self-analog) + `plugins/beads-lifecycle/.gsd/capabilities/beads/fragments/recall-pointer.md` for tone/density | exact (self) |
| `.gsd/capabilities/sota-numerics/fragments/executor-numerics.md` | config (prompt fragment) | transform | `planner-sota.md` (sibling fragment, same repo) | exact (sibling) |
| `.gsd/capabilities/sota-numerics/fragments/verifier-precision.md` | config (prompt fragment) | transform | `planner-sota.md` / `executor-numerics.md` (sibling fragments) | exact (sibling) |
| `.gsd/capabilities/sota-numerics/fragments/ship-precision-advisory.md` | config (prompt fragment) | transform | `verifier-precision.md` (sibling fragment) | exact (sibling) |
| `.gsd/capabilities/sota-numerics/capability.json` | config (manifest) | CRUD (declarative, no logic) | `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` | role-match (cross-capability, same schema) |
| `.claude-plugin/plugin.json` | config (manifest) | CRUD | itself, prior revision + beads' `.claude-plugin/plugin.json` (not read; same 4-field shape as sota-numerics') | exact (self) |
| `.gsd/capabilities/sota-numerics/NOTES.md` | utility (contributor doc) | transform (prose prune only, D-18) | itself, prior revision (self-analog) | exact (self) |
| `.gsd/capabilities/sota-numerics/scripts/check-alternatives.py` (docstring/comments only, D-01/D-17 — no behavior change) | utility/config (gate script) | request-response (stdin=PLAN.md text, stdout/stderr=exit code + message) | `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` (docstring style, "untrusted input" framing) | role-match (cross-capability) |
| `README.md` | config (human+agent doc) | transform | itself, prior revision (self-analog) | exact (self) |

## Pattern Assignments

### The four fragments (config, transform) — D-05, D-07, D-08, D-09, D-10

**Analog:** each other (all four live in `.gsd/capabilities/sota-numerics/fragments/`, same directory, same voice, same contribution-point wiring). Read in full above; current totals: planner 13 lines / 5 sentences of dense compound clauses, executor 5, verifier 5, ship 4 (27 total, D-08 budget raises ceiling to 45).

**Existing register to preserve (do not introduce a new voice):**
- No headings, no bullets, no code fences — each fragment is 1-3 dense prose paragraphs.
- First sentence names the lifecycle point and its gate status in one clause, e.g. planner's opening: `"SOTA-numerics research discipline planning advisory here, but blocking plan:post gate mechanically enforces will halt planning if plan not compliant."` — every fragment opens by disambiguating advisory-vs-blocking before any instruction.
- Verifier and ship both open with the identical disclaimer pattern: `"...advisory only — capability declares no gate at <point> ...; everything below [a] finding, not blocker."` Reuse this exact clause shape when the D-04 compliance-evidence dimensions are added to verifier/ship — it is the load-bearing sentence that keeps advisory fragments from reading like new gates.
- Directive sentences are imperative/telegraphic, dropping articles (e.g. `"Derive numeric parameters ... from first principles or problem's actual scale, not by tuning value until test happens pass."`) — matches the terse register CONTEXT.md D-10 asks for (state target behavior, not prohibition already partially present, e.g. "Prefer numerically stable formulations over merely convenient ones").
- **D-09 leading-word mechanism has no existing precedent in this repo** — introducing "with the grain" / "quiet" / "legible" as reusable, once-defined leading words is new to this phase; there is no analog fragment using a repeated leading word today. Define each inline the first time it appears (a short appositive clause, matching how `ceiling` is already defined inline in executor: `"label ceiling (the condition under breaks)"`), then reuse bare in later fragments/sentences.
- `ceiling` is already a defined term in executor-numerics.md — verifier-precision.md and ship-precision-advisory.md already reuse it bare (`"named ceiling (the condition under breaks)"` in ship) without re-defining it. This is the existing precedent for D-09's "define once, repeat the word" rule — extend the same pattern to the new leading words rather than inventing a different citation style.

**Role-specific extension per D-07 (where the six new dimensions attach):**
- `planner-sota.md` → append project-consistency + plan-completeness language after the existing alternatives-considered prose, in the same paragraph register (no new heading).
- `executor-numerics.md` → append agent-facing-prose + quiet-runtime-output + efficiency language after the existing "Where efficiency simplicity conflict..." sentence.
- `verifier-precision.md` → append one more "Flag ..." clause parallel to the three that already exist (`"Flag silent scope precision reductions..."`, `"...hardcoded constants..."`, `"...superlative performance overhead claims..."`) for the matching findings.
- `ship-precision-advisory.md` → extend the existing "confirm every ... claim ... backed" sentence to cover the new claim types, reusing its exact verb (`confirm`).

### `capability.json` (config, CRUD) — D-05, D-23

**Analog:** `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` (this repo, tracked, same schema family: `id`, `role`, `version`, `title`, `tier`, `requires`, `engines`, `contributions`/`gates` or `config`).

**What to hold fixed per D-05:** `contributions` array shape, `fragment.path` values, `when`/`onError` per contribution, and the single `gates[0]` entry — none of these change. Only `version` moves, `0.1.3` → `0.2.0` (D-23), together with the same field in `plugin.json`.

**Version-field synchronization pattern (cross-capability convention, from beads' `capability.json` vs `.claude-plugin/plugin.json`):** both manifests carry an independent top-level `"version"` string; nothing in gsd-core enforces they match, so synchronization is a manual discipline enforced only by review — grep both files for `"version"` after editing and confirm identical values before commit. Current sota-numerics values (verified this session): `capability.json` version `0.1.3`, `.claude-plugin/plugin.json` version `0.1.3` — both must become `0.2.0`.

**Gate description and predicate command (D-17: `description` string is in scope for prose refactor, predicate `command` shell script is NOT — behavior-frozen by D-01):**
- `gates[0].description` (current, full text captured above) is the one manifest-level prose field this phase touches. Refactor it for the D-11/D-14 "quiet"/"legible" standard the fragments now carry, but do not touch `gates[0].check.predicate.command` (the bash one-liner that locates and invokes `check-alternatives.py`) — that is gate mechanics, D-01 forbids new checks or gate changes.

### `.claude-plugin/plugin.json` (config, CRUD) — D-17, D-23

**Analog:** itself (prior revision) — 4 flat fields (`name`, `version`, `description`, `author`, `license`). `description` is the one field in scope (D-17); it currently duplicates `capability.json`'s gate description almost verbatim (`"...plus a blocking plan:post gate that mechanically enforces a compliant Alternatives Considered section..."`). Apply the same prose-refactor pass to this field as to `gates[0].description`, keeping both descriptions consistent in claim (not necessarily identical string) since they describe the same gate to two different audiences (marketplace listing vs. capability internals).

### `check-alternatives.py` docstring/comments (utility, request-response) — D-01, D-17, D-19

**Analog:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py`'s module docstring (this repo, tracked). Both scripts share the identical threat-model framing worth preserving verbatim in spirit:
```
sync.py (lines 1-9):
"""Beads sync: translate PLAN.md tasks into bd issues.

stdlib-only (N5: no dependency beyond the `bd` binary and the Python 3
standard library). Every `bd` invocation is an argv list passed to
`subprocess.run` with shell execution left at its (disabled) default --
PLAN.md text is authored by a different principal than the process running
`bd`, so no `bd` command is ever assembled as a shell string (N4, threat
T-01-01).
"""
```
`check-alternatives.py`'s own docstring already cross-references this exact sync.py sentence verbatim: `"...exactly as .gsd/capabilities/beads/scripts/sync.py's module docstring states for bd argv construction..."`. This is a **live cross-file citation** — if this phase's prose refactor changes that sentence's wording in `check-alternatives.py`, the citation target and shape (module docstring, opening paragraph) is unaffected since `sync.py` is out of scope, so no coordinated edit is needed there; just don't invalidate the cross-reference's claim.

**D-11 quiet-output precedent, cited directly by D-13 for the executor fragment's illustration:** `check-alternatives.py`'s own docstring already states its own contract in the exact terms D-11 wants generalized: `"Exit 0 = every discovered plan passes. Exit 1 = one or more violations, printed to stderr as <plan_path>: <reason>, followed by exactly one remediation: ... line. Exit 2 = usage/IO error..."` — this three-exit-code, one-line-diagnosis pattern is the concrete illustration to inline (not reference) into `executor-numerics.md` per D-13/D-14.

**Scope boundary:** only the module docstring and inline comments may be reworded for the legible/quiet standard (D-17); `PLAN_FILE_RE`, `RECENCY_WINDOW_YEARS`, `MIN_ALTERNATIVES`, and every regex/exit-code/behavior stay byte-identical (D-01, D-20 — `wc -l` and the existing test suite are the regression guard, so line-count-changing or logic-touching edits here fail the "existing suites pass unchanged" criterion).

### `NOTES.md` (utility, transform — prune only) — D-18

**Analog:** itself, prior revision. Current NOTES.md §1 (`gates[0].onError is "halt", deliberately`) and §2 (`plan:post gate fires late`) are captured in full above. D-18 says: remove only what README.md already independently states; keep every anti-regression entry intact otherwise. Concretely — README.md's line `"The plan:post check is different: it is blocking, and a missing interpreter, missing script, crash, or 30-second timeout halts planning."` already covers part of what NOTES.md §1 explains at greater length; NOTES.md's justification depth (the `command-exit-zero` evaluator mechanics, the "do not fix this back to skip" instruction) is NOT restated in README.md and must stay. Do line-by-line diff against README.md's final text before deleting anything from NOTES.md, not a bulk cut.

### `README.md` (config doc, transform) — D-17, D-20

**Analog:** itself, prior revision (240 lines, table-driven "What it changes" section captured above in full). The `## What it changes` table's `Behavior` column is the natural place for the six new dimensions to surface as one added clause per row (planner row already ends with the ranking criteria list; append project-consistency wording there per D-07's `planner-sota.md` mapping). D-20 requires every behavioral claim here trace to a line of code/config — after editing, grep each new README clause's key noun (e.g. "quiet", "legible") back into the corresponding fragment file to confirm the claim isn't invented prose divorced from the fragment text.

## Shared Patterns

### Advisory-disclaimer opening clause
**Source:** `verifier-precision.md` line 1, `ship-precision-advisory.md` line 1 (both in `.gsd/capabilities/sota-numerics/fragments/`)
**Apply to:** any fragment sentence that could be misread as a new blocking requirement — reuse the `"...advisory only — capability declares no gate at <point>..."` clause shape verbatim when introducing the six new dimensions, so the extension reads as more of the same advisory, not a new mechanism (D-02, D-03).

### Defined-term-then-bare-reuse citation style
**Source:** `executor-numerics.md`'s `ceiling` definition, reused bare by `verifier-precision.md` and `ship-precision-advisory.md`
**Apply to:** the three new D-09 leading words (`with the grain`, `quiet`, `legible`) — define each once with an inline appositive at first use, then use the bare word in every subsequent fragment/sentence, exactly as `ceiling` already does across three of the four files.

### Version-field synchronization (manual, unenforced)
**Source:** `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` vs its own `.claude-plugin/plugin.json` (not read this session, but same top-level `"version"` key convention confirmed present in sota-numerics' pair)
**Apply to:** `capability.json` + `.claude-plugin/plugin.json` version bump to `0.2.0` (D-23) — no tooling checks this; grep both files post-edit.

### Untrusted-input / no-shell-string threat framing
**Source:** `plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py` docstring lines 1-9
**Apply to:** `check-alternatives.py` docstring wording, if reworded for legibility — preserve the "PLAN.md text is authored by a different principal, treated as untrusted input, never eval'd/shelled out" claim exactly, since it is cross-cited by name from `check-alternatives.py`'s current docstring.

## No Analog Found

None. All 7 files under change have either a self-analog (their own prior revision, same repo, same directory) or a cross-capability sibling analog in the tracked `plugins/beads-lifecycle/.gsd/capabilities/beads/` tree.

## Metadata

**Analog search scope:** `/home/dd/projects/gsd-beads/.worktrees/sota-numerics-release-013` (full `.gsd/capabilities/sota-numerics/` tree + `README.md` + `.claude-plugin/plugin.json`); `plugins/beads-lifecycle/.gsd/capabilities/beads/` (full tree, this repo, tracked).
**Files scanned:** 4 fragments, 1 capability.json, 1 plugin.json, 1 NOTES.md, 1 check-alternatives.py (sota-numerics side); 1 capability.json, 1 sync.py, 1 recall-pointer.md (beads-lifecycle side).
**Pattern extraction date:** 2026-09-06
</content>
