# Roadmap: beads capability for gsd-core

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 (shipped 2026-08-16)
- 🚧 **v1.1 Publish & Document** — Phases 5-8 (in progress)

## Phases

<details>
<summary>✅ v1.0 milestone (Phases 1-4) — SHIPPED 2026-08-16</summary>

- [x] Phase 1: Substrate (3/3 plans) — completed 2026-08-15
- [x] Phase 2: Visibility (2/2 plans) — completed 2026-08-15
- [x] Phase 3: Enforcement (3/3 plans) — completed 2026-08-15
- [x] Phase 4: Adoption (3/3 plans) — completed 2026-08-16

Full detail: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### v1.1 Publish & Document (Phases 5-8)

- [ ] **Phase 5: Plugin Manifest** - Repo declares itself a valid, discoverable, MIT-licensed Claude Code plugin
- [ ] **Phase 6: Runtime Integration** - A plugin install delivers a working capability and its session hook, not just cached files
- [ ] **Phase 7: Hygiene & Publication** - Public GitHub repo whose history carries zero machine-local dev state
- [ ] **Phase 8: README, Release & Ship Gate** - A stranger can evaluate, install, and remove it from the README alone

## Phase Details

### Phase 5: Plugin Manifest
**Goal**: Claude Code recognizes this repo as a valid, discoverable, licensed plugin
**Depends on**: Nothing (first phase of v1.1; builds on shipped v1.0 capability)
**Requirements**: PUB-01, PUB-02, PUB-08
**Success Criteria** (what must be TRUE):
  1. `claude plugin validate . --strict` exits clean — run in the mode that actually inspects skill
     frontmatter (marketplace.json temporarily absent), not only the mode that trivially passes
  2. `/plugin marketplace add ./` from a scratch project lists a `beads` entry with its description,
     and `/plugin install` on that entry completes
  3. The installed plugin surfaces the `beads` skill resolved from the existing
     `.agents/skills/beads/`, with no duplicated copy of the skill in the repo
  4. `LICENSE` (MIT) exists at repo root and `plugin.json`'s `license` field names it as a string
**Plans**: 1 plan
- [ ] 05-01-PLAN.md — Author `plugin.json` + `LICENSE` (tracer: validated in frontmatter-checking
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
**Plans**: TBD

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
**Plans**: TBD

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
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. Plugin Manifest | 0/1 | Planned | - |
| 6. Runtime Integration | 0/? | Not started | - |
| 7. Hygiene & Publication | 0/? | Not started | - |
| 8. README, Release & Ship Gate | 0/? | Not started | - |

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
