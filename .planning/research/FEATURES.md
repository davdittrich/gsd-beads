# Config-Precedent Research — milestone v1.3 (`beads.sync_mode`)

**Question:** what does established practice look like for a gsd-core capability config key, and
which option does precedent favour — implement, narrow, or drop?

**Researched:** 2026-08-19. All claims verified against files on this machine and the four live
GitHub repos. Confidence scores (0-100) are per finding.

**Verdict up front:** precedent favours **drop the key** (remove `beads.sync_mode` from
`capability.json`) rather than implement or narrow it. Three independent lines of evidence:
a declared-but-unread key is a known, tolerated, *unblessed* state in this ecosystem (§3);
gsd-core's own removal precedent is deletion-with-a-warning, not narrowing (§5); and every
sibling capability that this author ships declares only keys it actually consumes (§4).

---

## §0 — How a gsd-core capability key gets "read" at all

Three distinct consumption mechanisms exist. This matters because "no Python reads it" is not
the same as "nothing reads it".

| Mechanism | Declared as | Resolved by | Example |
|---|---|---|---|
| **Declarative gate** | `"when": "<key>"` on a step/contribution/gate | `loop-resolver.cjs` | `beads.enabled` → capability.json:69,83,97,111,125,137,152 |
| **Fragment interpolation** | `"configValues": { alias: "<key>" }` | `loop-resolver.cjs:169-259` | `ponytail.level` → ponytail/capability.json:49-50 |
| **Imperative read** | code calls `config-get` / parses `.planning/config.json` | capability's own script or SKILL prose | `beads.epic_per` → `sync.py:669-671,919` |

A key with **none** of the three is inert. Confidence 95 — mechanisms read directly from
`/home/dd/.claude/gsd-core/bin/lib/loop-resolver.cjs:169-259` and `capability-validator.cjs:84-166`.

`activationKey` is a fourth, formal mechanism (`capability-validator.cjs:695-716`: a capability may
name one dotted key from its own config slice as its master gate). **No capability on this machine
uses it** — not beads, not the four siblings, not one of the 44 first-party ones. Everyone hand-wires
`"when": "<id>.enabled"` instead. Confidence 90.

---

## §1 — Every installed capability: declared keys and who reads them

Scope: `~/.gsd/capabilities/*/capability.json` (5 capabilities) plus the project-scope
`/home/dd/projects/gsd-beads/.gsd/capabilities/beads/` (identical bytes to the user-scope copy;
canonical source is `plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json`, whose line
numbers are cited below).

| Capability | Key | Declared values | Read by code? |
|---|---|---|---|
| beads 0.3.1 | `beads.enabled` | boolean, default `true` | **YES** — declarative `when` ×7 (capability.json:69,83,97,111,125,137,152); imperative `sync.py:674-676` + `:712`; SKILL gates at `beads-recall/SKILL.md:27-28`, `beads-sync/SKILL.md:27-28`, `beads-status/SKILL.md:27-28`, `beads-migrate-todos/SKILL.md:27-28` |
| beads 0.3.1 | **`beads.sync_mode`** | enum `authoritative\|mirror\|off`, default `authoritative` | **NO** — declared at capability.json:32; the only other occurrence in the entire bundle is a comment stating it is unread: `scripts/sync.py:1300` ("the strip is NOT gated on `beads.sync_mode` -- that key is declared in capability.json and read by nothing (gsd-beads-v43)") |
| beads 0.3.1 | `beads.ship_gate` | boolean, default `true` | **YES** — declarative `when` ×2 on the two `ship:pre` gates (capability.json:167,181); imperative bypass-recording path `sync.py:1979,2204`; documented read at `beads-status/SKILL.md:131` |
| beads 0.3.1 | `beads.epic_per` | enum `phase\|milestone`, default `phase` | **YES** — imperative only, no `when`: `sync.py:669-671` (`read_epic_per`) called at `sync.py:919`; 8 tests at `tests/test_sync.py:3503-3660` |
| markdown-linting 0.1.0 | `markdown-linting.enabled` | boolean, default `true` | **YES** — `when` at capability.json:45; SKILL gate `markdown-linting-report/SKILL.md:21`; documented `README.md:30` |
| markdown-linting 0.1.0 | `markdown-linting.ship_gate` | boolean, default `true` | **YES (declarative only)** — `when` at capability.json:61; documented `README.md:31`. No imperative read; `scripts/lint.py` never touches it |
| ponytail 0.1.0 | `ponytail.enabled` | boolean, default `true` | **YES** — `when` ×3 at capability.json:48,62,76 |
| ponytail 0.1.0 | `ponytail.level` | enum `lite\|full\|ultra`, default `full` | **YES** — `configValues` ×3 at capability.json:49-50,63-64,77-78; consumed in prose by `fragments/planner-ladder.md:3`, `fragments/executor-ladder.md:3`, `fragments/verifier-ladder.md:3` |
| pr-workflow 0.1.0 | `pr-workflow.enabled` | boolean, default `true` | **YES** — `when` ×2 at capability.json:45,55; SKILL gate `pr-workflow-report/SKILL.md:21` |
| pr-workflow 0.1.0 | `pr-workflow.ship_gate` | boolean, default `true` | **YES (declarative only)** — `when` at capability.json:71. `scripts/pr_status.py` never reads it |
| sota-numerics 0.1.1 | `sota-numerics.enabled` | boolean, default `true` | **YES** — `when` ×5 at capability.json:38,49,60,71,85 |

**Total: 11 declared keys across 5 installed capabilities. Exactly one — `beads.sync_mode` — has
zero consumers of any kind.** Confidence 97 — every cell is a grep hit or a verified absence over
the complete file list of each bundle.

Two secondary observations the planner can use:

- `beads.epic_per` is the ecosystem's only **imperatively-read enum**, and it is read *fresh at
  each call site* (`sync.py:919`, per D-11) rather than cached. It is the working model for what an
  implemented `sync_mode` would have to look like. Confidence 92.
- `ponytail.level` is the only **fragment-interpolated enum**, and it is the cheapest possible
  enum implementation: zero code, three `configValues` lines, three prose sentences. Confidence 92.

---

## §2 — gsd-core's own first-party capabilities

gsd-core ships **no `capability.json` files**. Its 44 first-party capabilities are inlined in the
generated registry `/home/dd/.claude/gsd-core/bin/lib/capability-registry.cjs` (7556 lines), exported
as `capabilities` / `configKeys` / `configSchema`. Confidence 95.

Enumerated programmatically: **62 first-party config keys**. Classified by consumer:

| Consumption | Count | Notes |
|---|---|---|
| Declarative (`when` / `activationKey` / `configValues`) | 25 | e.g. `workflow.tdd`, `workflow.security` |
| Imperative (read by a `.cjs` or a workflow `.md` outside the registry) | 24 | e.g. `review.ollama_host` → `workflows/review.md:30`; `refactor.complexity_threshold` → `bin/lib/refactor-trigger-command-router.cjs:222`; `claude_orchestration.min_agent_sdk_version` → `bin/lib/claude-orchestration.cjs:208` |
| Referenced only in the registry's own **inline step prose** (documented, agent-interpreted) | 6 | `external_job.backend`, `external_job.submit_timeout_ms`, `mempalace.memory_mode`, `mempalace.recall_on_discuss`, `mempalace.capture_artifacts`, `mempalace.mirror_kg` |
| **Zero consumers anywhere — declared and never read** | **7** | listed below |

The seven orphans, with declaration line in `capability-registry.cjs`:

| Capability | Key | Decl. line | Type / default |
|---|---|---|---|
| external-job | `external_job.artifact_dir` | :1565 | string, `"Artifacts/jobs"` |
| external-job | `external_job.poll_timeout_ms` | :1575 | number, `15000` |
| mempalace | `mempalace.recall_on_plan` | :2460 | boolean, `true` |
| mempalace | `mempalace.cross_project_tunnels` | :2475 | boolean, `false` |
| mempalace | `mempalace.diary_journal` | :2480 | boolean, `true` |
| mempalace | `mempalace.auto_capture_hooks` | :2485 | boolean, `false` |
| profile-pipeline | `profile-pipeline.enabled` | :3014 | boolean, `false` |

Method: extracted every `config` slice + every `when`/`configValues`/`activationKey` from the
registry via Node, then grepped all of `~/.claude/gsd-core/**/*.{cjs,md,json}` for each key,
excluding the registry's own declaration block and the two generated manifests
(`bin/shared/config-schema.manifest.json`, `config-defaults.manifest.json`). Confidence 90 — an
orphan could in principle be read by an out-of-tree MCP server (mempalace notably ships elsewhere),
which is why `mempalace.*` orphans are the weakest four of the seven.

Note `profile-pipeline.enabled` — an `.enabled` master toggle with **no `when` clause referencing
it and no `activationKey`**. Even the canonical "always-read" key shape gets orphaned in first-party
code. Confidence 88.

---

## §3 — Is "declared but never read" unique to `beads.sync_mode`?

**No. It is a widespread, tolerated pattern.** 7 of 62 first-party keys (11.3%) are orphans, plus
`beads.sync_mode` makes 8 of 73 across everything installed on this machine (11.0%). Confidence 90.

But three qualifications decide the milestone, and they all cut the same way:

1. **Nothing detects or punishes it.** `capability-validator.cjs:84-166` validates a config slice's
   *shape* (type present, default present, default's type matches, enum default is a member of
   `values`, description non-empty) — never whether anything consumes the key. There is no
   orphan-key lint anywhere in gsd-core. Confidence 95.
2. ~~**Nothing validates a user's *value* against the declared enum either.**~~ **CORRECTED
   2026-08-19 by the orchestrator — this claim was FALSE and the recommendation below rests on it.**

   The original text asserted that `config-set` checks only key existence and never compares the
   value to the slice's `values` array. Tested live against installed gsd-core 1.11.0 in a
   throwaway project carrying a copy of this capability's bundle:

   ```
   $ gsd_run query config-set beads.sync_mode bogus_not_in_enum
   Error: Invalid beads.sync_mode 'bogus_not_in_enum'. Valid values: authoritative, mirror, off
   ```

   The value was rejected and NOT written. `authoritative` and `mirror` were both accepted and
   stored. So the **write path does enforce the enum**, and it is distinct from the
   unknown-key error (`Unknown config key: "beads.totally_made_up"`), which was also reproduced
   as a control.

   What IS true: the **read path does not validate**. A value hand-written straight into
   `.planning/config.json` is returned verbatim — `sync_mode: "mirror"` written directly to the
   file read back as `"mirror"` with no complaint. And `/gsd-health` has no orphan- or
   invalid-capability-value check.

   **Consequence for the recommendation below:** narrowing `values` to `["authoritative"]` is
   NOT mechanically inert. It would cause `config-set beads.sync_mode mirror` to start failing —
   a real, user-visible behavior change on the write path. The "narrowing wouldn't even detect an
   existing mirror" argument is void; narrowing does not detect a *stale on-disk* value, but it
   does block a *new* one. Weigh narrow-vs-drop on precedent and semantics, not on this. Confidence 99.
3. **This repo has already published the orphan as a defect, not a feature.** `CHANGELOG.md:36-39`,
   under a "Known issues (pre-existing, now tracked)" heading: *"`beads.sync_mode` is declared in
   `capability.json` and read by no code. `mirror` and `off` do nothing; only `beads.enabled: false`
   stops dispatch. 0.3.0's changelog implied the strip was gated on it — it never was. Tracked as
   `gsd-beads-v43`."* Confidence 99.

So v1.3 is **not fighting a convention** — the convention is indifferent. It is closing a defect the
project itself already classified as a defect and ticketed. That framing rules out "leave it";
it does not by itself choose between implement / narrow / drop.

---

## §4 — The author's four sibling plugins

All four repos are public and were verified live via `gh api`, not from the local bundles.
Local installed bundles are byte-identical in their `config` blocks to the live `HEAD`. Confidence 95.

| Repo | Path in repo | Version | Keys declared | All read? |
|---|---|---|---|---|
| [davdittrich/markdown-linting](https://github.com/davdittrich/markdown-linting) | `.gsd/capabilities/markdown-linting/capability.json` | 0.1.0 | 2 | yes |
| [davdittrich/pr-workflow](https://github.com/davdittrich/pr-workflow) | `.gsd/capabilities/pr-workflow/capability.json` | 0.1.0 | 2 | yes |
| [davdittrich/ponytail-everywhere](https://github.com/davdittrich/ponytail-everywhere) | `.gsd/capabilities/ponytail/capability.json` | 0.1.0 | 2 | yes |
| [davdittrich/sota-numerics](https://github.com/davdittrich/sota-numerics) | `.gsd/capabilities/sota-numerics/capability.json` | 0.1.1 | 1 | yes |

**Seven keys across four sibling plugins; zero orphans.** Confidence 96.

The pattern is uniform and minimal:

- Every plugin declares exactly one `<id>.enabled` boolean, defaulting `true`, wired as `"when"` on
  every step it owns. No plugin uses `activationKey`.
- A second key exists only when there is a second *independently switchable* behaviour:
  `.ship_gate` (markdown-linting, pr-workflow) toggles gate registration separately from the
  reporting step; `ponytail.level` parameterises an already-active fragment.
- **`sota-numerics` is the direct counter-example to declaring aspirational keys.** It ships one
  key and says so in the key's own description: *"Master toggle for both the advisory steering
  fragments and the blocking `plan:post` Alternatives Considered gate (D-10, D-11) — **the only
  config key this capability declares**."* (`sota-numerics/capability.json:22`, live at HEAD). The
  author has already articulated "declare one key, mean it" as a design stance in a shipped
  artefact. Confidence 94.
- None of the four ships a `CHANGELOG.md` (verified: `gh api repos/<r>/contents/CHANGELOG.md`
  returns empty for all four), so they offer no key-removal precedent of their own. Confidence 90.

Read against §1, the sibling corpus says: **a capability's key count equals its switchable-behaviour
count.** `beads.sync_mode` has zero switchable behaviours behind it. Confidence 88.

---

## §5 — Precedent for removing / renaming / narrowing a key

### 5a. The canonical removal: `runtime.hostBehaviors.reviewerCli` (gsd-core, ADR-2782 D9 / #2801)

This is a manifest *field*, not a `config` key, but it is the closest and best-documented analogue
in the ecosystem — same problem (a declared knob in a capability manifest that must go away), same
blast radius (out-of-tree third-party manifests already carrying it).

The full sequence, from `bin/lib/review-reviewer-selection.cjs:30-37`:

> *"`runtime.hostBehaviors.reviewerCli` is GONE (Phase 7, #2801). It survived one release as a
> derived legacy alias — a capability setting only the flag contributed its capability id as a slug
> — and that window closed when 1.10.0 shipped after Phase 5a's 1.9.0. A declared `reviewer` body is
> now the ONLY route onto the roster. A manifest still carrying the key contributes no lane and is
> told so: `collectReviewerWarnings` (`gsd-core/bin/lib/capability-validator.cjs`) emits a removal
> notice on both the build-time registry generation and the third-party overlay load path."*

Four-step pattern, each step verifiable:

1. **Ship the replacement first**, keep the old name working as a derived alias for **one full
   release** (1.9.0 → 1.10.0). Confidence 95.
2. **Delete the behaviour in the next minor.** A manifest still carrying the key gets nothing.
3. **Emit a warning, never an error.** `capability-validator.cjs:1720-1726` is explicit that erroring
   was rejected: *"An error would hard-break an out-of-tree descriptor carrying a bespoke key, with no
   deprecation window — the exact mistake #2801's own alias removal spent a full release avoiding."*
   Confidence 96.
4. **Make the warning a typed record, keyed to the removal, naming the replacement and the docs.**
   `capability-validator.cjs:1816-1817` keeps the removed path as a named constant
   (`REMOVED_REVIEWER_CLI_FIELD`); the warning-record shape at :1949-1951 carries
   `{ code: REMOVED_HOST_BEHAVIOR, capId, field, replacement, docs, message }`; it is emitted
   **presence-based at any value** (:1997-2001), and surfaces on both the build path and the overlay
   load path because *"a warning written only to a build log nobody reads is not a warning"* (:1975).
   Confidence 94.

### 5b. The rename precedent: `review.models.antigravity` → `review.models.agy`

`bin/lib/review-lane-descriptor.cjs:301-303` — the shipped key is `review.models.agy`, and the code
carries a standing comment forbidding the intuitive longer name, with the reason that the short name
is what was federated. Migration handled by **never shipping the other name at all**, plus a
permanent comment at the one site that would otherwise drift. Confidence 90.

### 5c. Narrowing an enum: **no precedent exists anywhere.**

No capability on this machine, first-party or third-party, has ever removed a member from an enum's
`values` array. Searched: full git history of this repo for `capability.json`, all four sibling repo
HEADs, and every deprecation/migration mention in `~/.claude/gsd-core/bin/lib/capability-*.cjs` +
`config-schema.cjs`. Confidence 85 (absence of evidence over a corpus this small).

This matters directly: **"narrow `beads.sync_mode` to `authoritative` only" is the one option with
zero precedent**, and it would leave a single-valued enum — a key whose only legal value is its
default, i.e. a key that cannot change anything. That is the same inert state as today, with extra
machinery. And because §3.2 established nothing validates a user's value against `values` anyway,
narrowing the array would not even *detect* an existing `mirror`, let alone reject it.

---

## §6 — This repo's own precedent: the 0.2.0 `beads.enabled` default flip

The only prior config change in this repo's history. Both artefacts read in full.

**Commit `252984f`** — `feat(11.1-01): flip beads.enabled default to true, invert beads-recall gate`
(dd, 2026-08-17). Two files, 4 insertions / 4 deletions:

- `capability.json`: `"version": "0.1.0"` → `"0.2.0"` **in the same commit**, and
  `beads.enabled` `"default": false` → `true`.
- `beads-recall/SKILL.md` Step 1: gate polarity inverted from *opt-in* (`config.beads.enabled !== true`
  → stop) to *opt-out* (stop only when the value is **explicitly the boolean `false`**; a missing
  file, a missing `config.beads`, or a present `config.beads` with no `enabled` key all fall
  through to the shipped default).
- Commit message carries the end-to-end verification: *"a scratch project with no beads key now
  resolves all 7 `beads.enabled`-gated hooks active; explicit `beads.enabled:false` still disables
  all 7."*

Confidence 99 — read from `git show 252984f`.

**CHANGELOG entry** (`CHANGELOG.md:86-96`, written separately in `b69b335`) gives the migration
contract its own top-level heading, not a bullet buried in Changed:

```markdown
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
```

The house rule this establishes, in the author's own words: **an explicitly-set value always wins
over the shipped default; a config change may only move the behaviour of installs that never set
the key.** Note `CHANGELOG.md:3` scopes the whole file to `capability.json`'s version, so the
capability version is the migration unit. Confidence 97.

---

## §7 — The concrete migration pattern for an already-set `beads.sync_mode`

Synthesising §5a (gsd-core's removal ritual) with §6 (this repo's own no-regression contract), and
constrained by §3.2 (a stale value on disk is already inert and nothing will ever re-validate it):

1. **Bump `capability.json` to 0.4.0 in the same commit as the key removal.** Precedent: `252984f`
   bumped `version` in the same 4-line diff as the config change.
2. **Delete the `beads.sync_mode` slice** from `capability.json` (currently lines 32-41). Do not
   narrow `values` — §5c: no precedent, and it produces a single-valued enum that still changes
   nothing.
3. **Convert `sync.py:1300`'s comment from a defect note into a removal note.** It already names the
   key and the ticket; it becomes the `REMOVED_REVIEWER_CLI_FIELD` analogue — the one permanent,
   greppable record of why the name is gone, in the exact function whose behaviour the key claimed
   to gate.
4. **Do not write a migration.** A leftover `"sync_mode": "..."` inside `.planning/config.json`'s
   `beads` object is harmless: `read_beads_config` (`sync.py:641`) only ever fetches named keys, and
   nothing enumerates the object. Deleting a user's config entry is a bigger action than the defect
   warrants, and gsd-core's own removal precedent (§5a step 3) is *warn, never break* — here there is
   not even anything to warn about at runtime, because no read path exists to warn from.
   Confidence 88 — this is the one judgement call rather than a cited precedent.
5. **Give the removal its own CHANGELOG heading under 0.4.0, mirroring `## 0.2.0`'s two-heading
   shape**, and state the disposition of an already-set value explicitly:

   ```markdown
   ### Removed
   - **`beads.sync_mode` is gone.** It was declared in `capability.json` since 0.1.0 and read by no
     code; `mirror` and `off` never did anything (tracked as `gsd-beads-v43`, disclosed in 0.3.1's
     Known issues). `beads.enabled: false` remains the only way to stop dispatch.

   ### No regression for existing installs
   - A project whose `.planning/config.json` still sets `beads.sync_mode` needs no action. The key
     was never read, so removing the declaration changes no behaviour; the leftover entry is inert
     and may be deleted at leisure. Note `gsd-tools config-set beads.sync_mode <value>` will now
     fail with `Unknown config key` (bin/lib/config.cjs:657) — the key is no longer in the
     federated schema.
   ```

   That last sentence is the only user-visible break in the whole change, and it is a break in
   *writing* a value that never had an effect. Confidence 92.
6. **If `mirror`/`off` are ever genuinely wanted, `beads.epic_per` is the template** — declare the
   key in the same commit as `read_<key>` + its call site + its tests, read fresh at each call site
   (`sync.py:669-671,919`, D-11), never ahead of the implementation.

---

## §8 — Precedent scoreboard for the Alternatives Considered table

| Option | Precedent for it | Precedent against it | Verdict |
|---|---|---|---|
| **Implement** `mirror` / `off` | `beads.epic_per` shows the shape works (`sync.py:669-671,919` + 8 tests) | No sibling plugin declares a key it does not need (§4, 7/7 clean); `sota-numerics/capability.json:22` states the one-key stance outright; nothing in v1.3's scope requires a second sync semantic | Rejected — builds machinery for a demand no artefact evidences |
| **Narrow** `values` to `["authoritative"]` | none found anywhere (§5c) | Produces a single-valued enum = still inert; §3.2 shows nothing validates user values against `values`, so it detects no existing `mirror`; adds a version bump and a doc change for zero behaviour delta | Rejected — the only option with zero precedent |
| **Drop** the key | gsd-core `#2801` removed `runtime.hostBehaviors.reviewerCli` outright (§5a); repo already published it as a defect (`CHANGELOG.md:36-39`); orphan keys are tolerated but never *blessed* (§2-3) | The removal ritual (§5a) normally spends a release on a deprecation alias — but that exists to protect *working* behaviour, and there is none here | **Recommended** |

Confidence in the overall recommendation: **88.** The residual 12% is the possibility that a
downstream consumer outside this machine reads `beads.sync_mode` from the federated config schema
(the same uncertainty that weakens the `mempalace.*` orphan findings in §2). Mitigated by the fact
that a value read from a schema no code acts on still cannot change behaviour.

---

## Gaps

- The four sibling repos ship no CHANGELOGs, so the author has exactly one key-migration precedent
  of his own (§6) and it is a default flip, not a removal. Confidence 90.
- gsd-core's `#2801` is a *manifest field*, not a `config` key. No removal of a `config`-slice key
  was found in any corpus. The transfer is by analogy — strong (same manifest, same third-party
  blast radius, same validator) but not exact. Confidence 80.
- The `mempalace.*` orphans may be consumed by an out-of-tree MCP server not on this machine. If a
  planner wants the 11% orphan rate to be load-bearing, the safe floor is the three non-mempalace
  orphans (`external_job.artifact_dir`, `external_job.poll_timeout_ms`, `profile-pipeline.enabled`)
  — still enough to establish the pattern is not unique to beads. Confidence 90.
