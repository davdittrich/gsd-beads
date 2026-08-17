# Roadmap: beads capability for gsd-core

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 (shipped 2026-08-16)
- 🚧 **v1.1 Publish & Document** — Phases 5-9 (in progress)

## Phases

<details>
<summary>✅ v1.0 milestone (Phases 1-4) — SHIPPED 2026-08-16</summary>

- [x] Phase 1: Substrate (3/3 plans) — completed 2026-08-15
- [x] Phase 2: Visibility (2/2 plans) — completed 2026-08-15
- [x] Phase 3: Enforcement (3/3 plans) — completed 2026-08-15
- [x] Phase 4: Adoption (3/3 plans) — completed 2026-08-16

Full detail: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### v1.1 Publish & Document (Phases 5-9)

- [x] **Phase 5: Plugin Manifest** - Repo declares itself a valid, discoverable, MIT-licensed Claude Code plugin (completed 2026-08-16)
- [x] **Phase 6: Runtime Integration** - A plugin install delivers a working capability and its session hook, not just cached files (completed 2026-08-16)
- [x] **Phase 7: Hygiene & Publication** - Public GitHub repo whose history carries zero machine-local dev state (completed 2026-08-16)
- [x] **Phase 8: README, Release & Ship Gate** - A stranger can evaluate, install, and remove it from the README alone (completed 2026-08-16)
- [ ] **Phase 9: Beads Content Depth** - The shipped plugin's beads guidance matches upstream depth and is tailored to gsd-core

## Phase Details

### Phase 5: Plugin Manifest

**Goal**: Claude Code recognizes this repo as a valid, discoverable, licensed plugin
**Depends on**: Nothing (first phase of v1.1; builds on shipped v1.0 capability)
**Requirements**: PUB-01, PUB-02, PUB-08
**Success Criteria** (what must be TRUE):

  1. `claude plugin validate . --strict` exits clean, with one documented, permanent exception: the
     root `CLAUDE.md` warning (this repo's own dev-workflow file lives at the plugin root by D-07's
     design; no suppression mechanism exists in Claude Code's validator, and relocating the file
     would break this repo's own AI-tooling auto-load — accepted 2026-08-16, see 05-CONTEXT.md) — run
     in the mode that actually inspects skill frontmatter (marketplace.json temporarily absent), not
     only the mode that trivially passes

  2. `/plugin marketplace add ./` from a scratch project lists a `beads` entry with its description,
     and `/plugin install` on that entry completes

  3. The installed plugin surfaces the `beads` skill resolved from the existing
     `.agents/skills/beads/`, with no duplicated copy of the skill in the repo

  4. `LICENSE` (MIT) exists at repo root and `plugin.json`'s `license` field names it as a string

**Plans**: 1/1 plans executed

- [x] 05-01-PLAN.md — Author `plugin.json` + `LICENSE` (tracer: validated in frontmatter-checking
      mode), add the `marketplace.json` catalog entry, run the D-09 double-run, and human-verify a
      scratch-project install round trip

### Phase 6: Runtime Integration

**Goal**: Installing the plugin gives a user the working capability and its session hook, without manual config
**Depends on**: Phase 5
**Requirements**: PUB-03, PUB-06
**Success Criteria** (what must be TRUE):

  1. After a real install into a project with no prior gsd-beads state, the `beads` capability is
     reachable by gsd-core's loader — or, if the manual path is the chosen answer, the exact manual
     step is written down and executed successfully from that clean project

  2. A new session in a project with the plugin installed runs `bd prime` from `hooks/hooks.json`
     with no edit to the user's own `.claude/settings.json`

  3. The SessionStart hook fires exactly once inside this repo, which already carries its own
     dev-session hook — no double prime

  4. With `bd` absent from PATH, install and session start still succeed with one visible notice;
     v1.0's fail-open guarantee survives packaging

**Plans**: 1/1 plans executed

Plans:

- [x] 06-01-PLAN.md — Ship `hooks/hooks.json` and delete `.claude/settings.json` (tracer: install
      the plugin locally and count exactly one `bd prime` fire), prove fail-open with `bd` off PATH,
      and execute + record the manual `capability install` bridge from a clean scratch project

### Phase 7: Hygiene & Publication

**Goal**: The project is public on GitHub and its history contains nothing machine-local
**Depends on**: Phase 6
**Requirements**: PUB-05, PUB-10
**Success Criteria** (what must be TRUE):

  1. `git ls-files` lists no `.beads/config.yaml`, `.beads/metadata.json`,
     `.claude/.headroom_wrap_marker.json`, or `.gsd-capabilities.json`

  2. `.gitignore` covers the backup and Dolt artifacts that exist in the working tree today
     (`.beads.backup-pre-recovery/`, `.beads/interactions.jsonl`, `*.bak`)

  3. History is rewritten (`git filter-repo --path <each of the 4 files> --invert-paths`), not
     merely untracked — every past commit's tree is stripped, so `git log -p -- <path>` on any of
     the 4 files returns nothing at any commit, not just HEAD. All local branches/tags are rebuilt
     on the new history before push; this is a one-way door taken deliberately (user decision,
     v1.1 requirements gathering) because these files already have real content in pushed-adjacent
     history and untrack-only leaves it recoverable via `git log -p`

  4. `github.com/<owner>/gsd-beads` exists as a public repo, `git remote -v` points at it, and the
     rewritten history is pushed (force-push required — commit hashes changed; confirm with user
     before force-pushing per standing git-safety rules)

  5. A fresh `git clone` of the pushed repo contains no file from criteria 1-2 in its working tree
     AND no trace of them in `git log -p` across full history

**Plans**: 2 plans

Plans:

- [x] 07-01-PLAN.md — Clean the working tree into one pre-rewrite commit (extended root
      `.gitignore`, D-01/D-02 resolutions), take the D-03 mirror backup and rehearse the full
      strip-and-verify pipeline on a throwaway clone with a negative control (tracer), then run
      `git filter-repo` in place and verify locally — SC 1-3

- [x] 07-02-PLAN.md — Blocking one-way-door checkpoint, then `gh repo create davdittrich/gsd-beads
      --public --source=.` and a plain `git push -u origin main --tags`, gated by a fresh-clone
      verification of the pushed history — SC 4-5

### Phase 8: README, Release & Ship Gate

**Goal**: A stranger can evaluate, install, and remove gsd-beads from the README alone
**Depends on**: Phase 7
**Requirements**: PUB-04, PUB-07, PUB-09
**Success Criteria** (what must be TRUE):

  1. `README.md` states purpose, requirements (`bd` on PATH, Python 3 stdlib, gsd-core >=1.6.0),
     install, uninstall, caveats, license, and a link to gsd-core — every command transcribed from
     one actually executed, none aspirational

  2. A GitHub Release carries a plugin archive built from an explicit allowlist; unzipping it lists
     only `.claude-plugin/`, `hooks/`, `.agents/skills/`, `README.md`, `LICENSE`

  3. Installing from that release leaves no `.planning/` or `.beads/` file on the installer's machine
  4. The README's own commands, run verbatim against the public repo, complete a
     `/plugin marketplace add` → `/plugin install` → `/plugin uninstall` round trip

  5. `claude plugin validate . --strict` is clean on the pushed tree at the released tag

**Plans**: 2 plans

Plans:

- [x] 08-01-PLAN.md — Tracer: `.github/workflows/release.yml` plus a thin real README, rehearsed
      end-to-end on a throwaway `v0.0.0-rc1` tag and torn down, then every README command executed
      and the README expanded to D-04's locked section order — SC1-SC3 mechanism

- [x] 08-02-PLAN.md — Bump `plugin.json` to 1.1.0, cut the real `v1.1.0` tag and prove the published
      archive is allowlist-exact, then the ship gate: `claude plugin validate . --strict` from a
      fresh clone at the tag plus the marketplace add/install/uninstall round trip — SC2-SC5

### Phase 9: Beads Content Depth

**Goal**: The shipped plugin's beads guidance matches upstream depth and is tailored to gsd-core, not generic defaults
**Depends on**: Phase 8
**Requirements**: PUB-11, PUB-12
**Success Criteria** (what must be TRUE):

  1. `.agents/skills/beads/SKILL.md` covers dependencies (`bd dep`), labels, comments, search,
     `compact`, `import`, `stats`, `blocked`, worktrees, async gates, resumability, and
     `--stealth`/`BEADS_DIR` git-free mode — matching the upstream `beads` skill's command coverage
     (a `resources/`/`commands/` progressive-disclosure split is acceptable, not required verbatim)

  2. `.beads/PRIME.md` exists in the repo and is included in the release archive allowlist,
     overriding `bd prime`'s generic default output with gsd-core-specific guidance: phase epics,
     the `plan:post`/`execute:wave:post`/`verify:post` sync points, and `ship:pre` gate behavior

  3. A fresh `bd prime` run inside an installed copy of the plugin (not `bd prime --export`) prints
     the gsd-tailored `.beads/PRIME.md` content, confirmed via `bd prime --help`'s documented
     override mechanism

  4. `v1.1.1` is tagged, released, and replaces `v1.1.0` as the public archive a stranger installs
     from the README

**Plans**: 4/4 plans executed

Plans:

- [x] 09-01-PLAN.md — Tracer: ship `.agents/skills/beads/PRIME.md`, self-heal it into `.beads/`
      from the SessionStart hook, and prove `bd prime` prints it

- [x] 09-02-PLAN.md — Six `resources/` documents (dependencies, worktrees, async gates,
      resumability, git-free mode, troubleshooting) indexed from SKILL.md

- [x] 09-03-PLAN.md — Eight `commands/` documents (dep, label, comments, search, compact, import,
      stats, blocked) indexed from SKILL.md

- [x] 09-04-PLAN.md — Bump to 1.1.1, retire `v1.1.0`, cut and verify the `v1.1.1` release, and
      round-trip the README install

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. Plugin Manifest | 1/1 | Complete    | 2026-08-16 |
| 6. Runtime Integration | 1/1 | Complete    | 2026-08-16 |
| 7. Hygiene & Publication | 2/2 | Complete    | 2026-08-16 |
| 8. README, Release & Ship Gate | 3/3 | Complete    | 2026-08-16 |
| 9. Beads Content Depth | 4/4 | In Progress|  |

## Notes

**Ordering is causal, not preferential.** Phase 7's audit is a one-way door: the window to remove
machine-local state from history closes at the first public push, so it precedes publication and
publication precedes everything that needs a public URL.

**Research ordering corrected.** `research/SUMMARY.md` placed the release archive (its Phase 2)
before the git cleanup and first push (its Phase 3), but a GitHub Release requires the repo to
exist. The archive moved to Phase 8, after publication.

**PUB-02 is authored in Phase 5, re-pointed in Phase 8.** The marketplace entry is written and
round-tripped locally against a relative source in Phase 5; Phase 8's PUB-04 work re-points it at
the release archive URL so `.planning/` and `.beads/` cannot reach an installer.

**Known gate hazard.** `claude plugin validate` skips skill-frontmatter checks when a
`marketplace.json` is present, and only `--strict` promotes field warnings to errors. A green run
in the wrong mode is indistinguishable from a check that never ran.

**Consent-hash hazard carries over.** Editing any file inside an already-consented capability
bundle silently deactivates it. Any phase that touches `.gsd/capabilities/beads/` must re-run
`capability install --scope project` and re-verify `render-hooks` before claiming done.

**Phase 9 exists because v1.1.0 already shipped short.** Phase 8 UAT (2026-08-16) surfaced two
content gaps in the already-published `v1.1.0` release: `.agents/skills/beads/SKILL.md` is
materially thinner than the upstream `beads` skill it's derived from, and the plugin ships no
`.beads/PRIME.md` override, so installers get beads' generic `bd prime` output instead of
gsd-tailored guidance. The user ruled these hard requirements for v1.1, not deferred — Phase 9
must complete before v1.1 is considered done, followed by a `v1.1.1` patch release replacing the
public archive.

### Phase 10: ponytail-everywhere capability plugin: advisory-only ladder-discipline reminders (SessionStart hook + plan/execute/verify/ship contribution fragments) wired to /ponytail

**Goal:** Lazy-ladder discipline (YAGNI, reuse before writing, stdlib/native before dependencies,
shortest working diff) reaches every gsd stage as advisory text and no gate — carried by a second
marketplace plugin's SessionStart + role-matched SubagentStart hooks, plus a `ponytail` capability
contributing a stage-tailored fragment into the planner's prompt at `plan:pre`, all config-driven
via `ponytail.enabled` (default true) and `ponytail.level` (`lite`/`full`/`ultra`), with zero
gsd-core patches.
**Requirements**: D-01, D-02, D-03, D-04, D-05 (CONTEXT.md decisions — no REQUIREMENTS.md entries
exist for this phase; it is new scope routed directly from /gsd-explore)
**Depends on:** Phase 9
**Plans:** 2/2 plans complete

Plans:

- [x] 10-01-PLAN.md — `ponytail-everywhere` plugin: dual-event hooks, config-driven level/role reminder script, marketplace entry
- [x] 10-02-PLAN.md — `ponytail` capability: config keys, three stage-tailored contributions, consent gate, `plan:pre` reach proof

### Phase 10.1: capability auto-install (INSERTED)

**Goal:** A shared SessionStart-triggered mechanism grants `capability install --scope user --yes`
automatically for a capability the first time it's needed — no manual command required. Applied
to both capabilities that exist today: `beads` (Phase 6) and `ponytail` (Phase 10). Must close
the silent-invalidation gap discovered debugging Phase 10: `.gsd-capabilities.json` isn't
git-tracked, so a bundle edit after consent (or a fresh checkout/session) currently degrades a
capability with zero visible warning — detect-and-re-grant, not grant-once. Reverses Phase 6's
T-06-01 decision (previously "do not build it," decided by the planner without user sign-off,
never actually put to the user — see PROJECT.md Key Decisions, corrected 2026-08-17). The
resulting pattern is what Phase 11 (sota-numerics) should reuse from the start rather than
retrofit.
**Requirements**: CAP-01, CAP-02, CAP-03, CAP-04, CAP-05, CAP-06, CAP-07 (minted at planning
2026-08-17; revisits PUB-03 disposition — CB-3 human-gated consent tradeoff explicitly
re-decided by user 2026-08-17: auto-install accepted at user scope. Note: the goal text above
says `.gsd-capabilities.json` "isn't git-tracked" — that is stale; this repo's root copy IS
git-tracked and is deliberately kept so, per RESEARCH.md's Runtime State Inventory. The
mechanism writes to the end user's *global* ledger, a different file.)
**Depends on:** Phase 10 (needs both `beads`, shipped Phase 6, and `ponytail-everywhere`, shipped
Phase 10, as concrete targets)
**Plans:** 2/2 plans complete

Plans:

- [x] 10.1-01-PLAN.md — Author the auto-install hook script, wire it into the `beads` plugin's SessionStart, prove it end-to-end with bash smoke tests
- [x] 10.1-02-PLAN.md — Vendor the bundle + script copy into `ponytail-everywhere`, add CI byte-parity and release-artifact guards

### Phase 11: sota-numerics capability plugin: SOTA/efficiency/numerical-stability steering with blocking plan:post Alternatives-Considered gate (SessionStart hook + plan/execute/verify/ship contribution fragments)

**Goal:** A third capability plugin, `sota-numerics`, installed and dogfooded in this repo, that
steers every gsd lifecycle stage toward SOTA verification, efficiency, and numerical stability —
and mechanically blocks at `plan:post` any PLAN.md lacking a cited, dated, ranked-criterion
"Alternatives Considered" section. Reuses Phase 10.1's auto-install mechanism from the start
rather than retrofitting it later.
**Requirements**: TBD
**Depends on:** Phase 10, Phase 10.1
**Plans:** 3/3 plans complete

Plans:

**Wave 1**

- [x] 11-01-PLAN.md — Gate spine: `check-alternatives.py`, `capability.json` with the blocking
      `plan:post` `command-exit-zero` gate, unit tests, plugin packaging, dogfood install,
      marketplace entry

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 11-02-PLAN.md — D-12's four stage-tailored steering fragments and their `contributions[]`
      entries at `plan:pre`, `execute:wave:pre`, `execute:wave:post`, `ship:pre`

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 11-03-PLAN.md — D-08 citation-plausibility route decision (core patch vs deterministic-only)
      and NOTES.md documenting the two deliberate divergences

Cross-cutting constraints:

- The plugin bundle under `sota-numerics/.gsd/capabilities/sota-numerics/` and the repo-root
  dogfood copy under `.gsd/capabilities/sota-numerics/` must stay byte-identical (D-04).

- `sota-numerics.enabled` is the single config key governing both steering and the gate (D-11),
  default `true` (D-10).

- `gates[0].onError` is `halt` while every `contributions[].onError` is `skip` — a deliberate,
  documented divergence.

### Phase 11.1: beads.enabled default flip to true (INSERTED)

**Goal:** Flip the beads capability's shipped default `beads.enabled` from `false` to `true`, so a
fresh install runs with beads issue tracking on out of the box instead of requiring a manual
opt-in — and make the four beads skills' own config gates honor that default, so the flip actually
reaches them. Covers the config default, the skill gates that duplicate it, the live documentation
surface, and a new repo-root CHANGELOG.
**Requirements**: TBD (no requirement IDs defined for this project; traceability is via CONTEXT.md decisions D-01..D-04)
**Depends on:** Phase 11
**Plans:** 2/2 plans complete

Plans:
**Wave 1**

- [x] 11.1-01-PLAN.md — Flip the shipped default to `true` (capability.json v0.2.0) and invert the four beads skills' Step 1 config gates to opt-out polarity

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 11.1-02-PLAN.md — Sweep the live docs (README, both PRIME.md twins, PRD schema) to the new default and create CHANGELOG.md
