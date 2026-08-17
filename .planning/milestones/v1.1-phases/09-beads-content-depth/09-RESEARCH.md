# Phase 9: Beads Content Depth - Research

**Researched:** 2026-08-16
**Domain:** Claude Code skill/plugin documentation depth + `bd prime` override mechanism + GitHub Release re-cut
**Confidence:** HIGH (every claim below was read from a live file or live command output this session; no web search was needed — the "upstream" comparison target and the override mechanism both exist locally on this machine)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### PRIME.md shipping mechanism
- **D-01:** `PRIME.md`'s source file lives at `.agents/skills/beads/PRIME.md` — inside the already-allowlisted `.agents/skills/` tree, so `release.yml`'s zip allowlist needs NO change. This deliberately avoids reopening the `.beads/` exclusion Phase 7/8 established (Phase 7's whole premise was that `.beads/` never ships).
- **D-02:** The file is copied to `.beads/PRIME.md` via a **self-healing check that runs whenever it's missing** — not a one-shot install-time action. User explicitly rejected "copy once at install" in favor of "copy whenever missing" (survives a user deleting/regenerating `.beads/`, a fresh `bd init` in an existing install, etc.). Likely wired into the existing SessionStart hook (`hooks/hooks.json`, alongside `bd prime --hook-json`) so it self-heals every session start, not just first install. — **Reversibility:** reversible — a hook script change, no migration.

#### SKILL.md scope
- **D-03:** Split structure: `resources/` + `commands/` directories, matching the upstream `beads` skill's progressive-disclosure convention (e.g. `resources/BOUNDARIES.md`, `commands/dep.md`). SKILL.md itself stays a short entry point; detail loads on demand. PUB-11's success criterion explicitly allows this (not required verbatim single-file).
- **D-04:** Full parity with upstream's command coverage — `bd dep` (dependencies), labels, comments, search, `compact`, `import`, `stats`, `blocked`, worktrees, async gates, resumability, `--stealth`/`BEADS_DIR` git-free mode, troubleshooting. No curation/cutting — matches PUB-11's success criterion literally, no judgment calls about what to omit.

#### PRIME.md content
- **D-05:** PRIME.md covers all 4 gsd-core lifecycle sync points (`plan:post`, `execute:wave:post`, `verify:post`, `ship:pre`) inline — but **minimal and token-efficient**: terse bullets, not prose explanations. User explicitly rejected the "Full inline reference" framing (long-form) in favor of a compact version carrying the same substance. Matches beads' own `bd prime`'s token-budget design intent (MCP mode ~50 tokens, CLI mode ~1-2k tokens — this override should stay lean, not balloon it).
- **D-06:** PRIME.md is gsd-integration-only — assumes the reader already knows bare `bd` CLI essentials (`bd ready`, `bd show`, `bd update --claim`) from the base `beads` skill. No duplication between PRIME.md and SKILL.md.

#### v1.1.1 re-release process
- **D-07:** Delete the existing `v1.1.0` GitHub Release and tag (`gh release delete v1.1.0 --cleanup-tag`) before cutting `v1.1.1` — matches Phase 7's precedent of deleting the throwaway `v0.0.0-rc1` rehearsal tag/release after use (**research correction: the `v0.0.0-rc1` transcript is actually Phase 8 Plan 01's, not Phase 7's — see Common Pitfalls / Pitfall 3 below; the delete-then-recut mechanism itself is unaffected**). Avoids a stranger installing the known-short `v1.1.0` by mistake. — **Reversibility:** one-way for the deleted release/tag itself (GitHub doesn't restore deleted releases), but `v1.1.1` fully supersedes it with no functional loss — the content is a strict superset. Not rated one-way in the blocking-checkpoint sense: this is routine release hygiene, not the kind of irreversible-and-consequential action Phase 7's history rewrite was.

### Claude's Discretion
- Exact `resources/`/`commands/` file names and per-file content depth within upstream's established pattern (D-03/D-04).
- Exact wording/bullet structure of PRIME.md's terse sync-point summaries (D-05).
- Exact hook-script mechanics for the self-healing copy-if-missing check (D-02) — e.g. a shell one-liner appended to `hooks/hooks.json`'s existing SessionStart command, or a small script file it calls.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUB-11 | `.agents/skills/beads/SKILL.md` expanded toward upstream `beads` skill parity (dependencies, labels, comments, search, `compact`, `import`, `stats`, `blocked`, worktrees, async gates, resumability, `--stealth`/`BEADS_DIR` git-free mode, troubleshooting); a `resources/`/`commands/` progressive-disclosure structure is acceptable, not required verbatim | Real upstream directory inventory verified (15 `resources/` files, 29 `commands/` files — see Summary/Pitfall 1 for the correct scope-anchor subset); `--stealth`/`BEADS_DIR` sourced from live `bd init --help`/`bd prime --help` output, not a nonexistent upstream file (Pitfall 4); path-confinement and no-shell-string conventions to reuse documented in Architecture Patterns/Don't Hand-Roll |
| PUB-12 | A gsd-tailored `.beads/PRIME.md` ships with the plugin, overriding beads' generic `bd prime` default output with content specific to gsd-core integration (phase epics, `plan:post`/`execute:wave:post`/`verify:post` sync points, `ship:pre` gates); `bd prime --help` confirms `.beads/PRIME.md` is beads' supported override mechanism | Override mechanism verified verbatim against live `bd prime --help` (bd v1.2.2); all 4 sync points' exact `capability.json` definitions and `beads-sync`/`beads-status` `SKILL.md` behavior quoted verbatim in Architecture Patterns/Pattern 2; open git-tracking question for `.beads/PRIME.md` flagged in Pitfall 2/Open Questions — needs resolution before D-02's hook task is planned |

</phase_requirements>

## Summary

Phase 9 has two content deliverables (PUB-11 SKILL.md depth, PUB-12 `.beads/PRIME.md` override) and one release deliverable (`v1.1.1` replacing `v1.1.0`). CONTEXT.md already locked the shipping mechanism (D-01/D-02), the SKILL.md structure (D-03/D-04), the PRIME.md content scope (D-05/D-06), and the re-release process (D-07). This research verifies every factual premise those decisions depend on, against the real files — and finds two of CONTEXT.md's supporting facts are imprecise (an upstream skill inventory that's now stale, and a Phase-7-vs-Phase-8 misattribution), plus one gap CONTEXT.md doesn't address (git-tracking status of the runtime-generated `.beads/PRIME.md`).

The real upstream `beads` skill lives at `/home/dd/.claude/plugins/marketplaces/beads-marketplace/plugins/beads/skills/beads/` (installed from the `beads-marketplace` marketplace, MIT, author Steve Yegge) — not at `~/.claude/skills/beads/`, which does not exist on this machine. Its `SKILL.md` frontmatter declares `version: "0.60.0"` (matching CONTEXT.md's citation) even though the installed `bd` binary is `1.2.2` — the skill's own "Validation" section says this makes it self-flagged as potentially stale. The `resources/` directory (15 files) matches CONTEXT.md's inventory exactly, verified by directory listing. The `commands/` directory does **not** match CONTEXT.md's "13 files" claim — it has grown to **29** command files. PUB-11's actual requirement text names a specific topic subset (`bd dep`, labels, comments, search, `compact`, `import`, `stats`, `blocked`, worktrees, async gates, resumability, `--stealth`/`BEADS_DIR`, troubleshooting) — that subset, not literal 1:1 parity with all 29 upstream command files, is the correct scope boundary (see Common Pitfall 1).

`bd prime --help` (installed binary v1.2.2) confirms the override mechanism verbatim: *"Place a `.beads/PRIME.md` file in the local clone or resolved workspace to override the default output entirely."* No env var, no other filename — this is the single documented override path, confirming PUB-12's premise exactly as CONTEXT.md states.

The four gsd-core sync points PRIME.md must describe (`plan:post`, `execute:wave:post`, `verify:post`, `ship:pre`) are defined verbatim in `.gsd/capabilities/beads/capability.json`'s `steps[]` array (quoted in full below) and their behavior is documented in `beads-sync/SKILL.md` and `beads-status/SKILL.md`. This is the canonical, machine-readable source of truth for PRIME.md's content — not a paraphrase, but the literal `point`/`ref.skill`/`produces`/`consumes`/`onError` values.

**Primary recommendation:** Build SKILL.md/resources/commands against PUB-11's literal named-topic list (not all 29 upstream commands); source `.gsd/capabilities/beads/capability.json` + the two dispatch `SKILL.md` files verbatim for PRIME.md's sync-point bullets; resolve the `.beads/PRIME.md` git-tracking question explicitly with the user before D-02's hook script is written, since it is currently un-gitignored and CONTEXT.md doesn't decide it.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SKILL.md/resources/commands content (PUB-11) | Plugin content (static files shipped in `.agents/skills/`) | — | Pure documentation; no runtime component |
| `.beads/PRIME.md` source authoring (PUB-12) | Plugin content (`.agents/skills/beads/PRIME.md`) | — | Ships via the already-allowlisted `.agents/skills/` tree (D-01) |
| `.beads/PRIME.md` runtime materialization (D-02 self-heal) | Claude Code hook runtime (`hooks/hooks.json` SessionStart) | Local filesystem (`.beads/`) | Copy-if-missing logic must run every session, in the installer's own project tree, not at plugin-install time |
| `bd prime` output selection | External binary (`bd`, not this repo's code) | — | `bd` itself resolves `.beads/PRIME.md` vs. its built-in default; this repo only supplies the file |
| Release archive assembly | CI (`.github/workflows/release.yml`) | — | Zip allowlist already covers `.agents/skills` recursively; no change needed for PUB-11/PUB-12 file additions |
| Release publication (`v1.1.1`) | GitHub Releases (via `gh` CLI / Actions) | Git tags | Delete-then-recut pattern, not an amend |

## Standard Stack

No new runtime dependency. This phase adds markdown content, one small hook-script addition (bash or Python 3 stdlib, matching this repo's existing `no runtime dependency beyond bd + Python 3 stdlib` constraint — REQUIREMENTS.md "Out of Scope"), and a CI-driven release re-cut using the existing `.github/workflows/release.yml` (unchanged). No package installation occurs in this phase.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Bash one-liner appended to `hooks/hooks.json`'s SessionStart command (D-02 discretion) | A small Python script under `.gsd/capabilities/beads/scripts/` calling the existing `confined()`/`find_project_root()` helpers | A bash one-liner is zero-dependency and matches the existing `bd prime --hook-json` sibling command's style; a Python script gets path-confinement and testability for free from `sync.py`'s existing helpers but adds an extra file and a `python3` invocation to a currently single-command hook entry. Either is compatible with the "Python 3 stdlib only" constraint — this is a style choice, not a legitimacy question. |

## Package Legitimacy Audit

**Not applicable.** This phase installs no new packages (npm, pip, or otherwise) in any ecosystem. All content is markdown; the only executable addition is a shell command or stdlib Python inside this repo's existing hook/script infrastructure.

## Architecture Patterns

### System Architecture Diagram

```
Installer's project tree (after `/plugin install beads@gsd-beads`)
│
├── .agents/skills/beads/                    (shipped, static — this phase's PUB-11/PUB-12 output)
│   ├── SKILL.md                             (entry point, short)
│   ├── PRIME.md                             (NEW — D-01 source-of-truth for the override)
│   ├── resources/*.md                       (progressive disclosure — D-03/D-04)
│   └── commands/*.md
│
├── hooks/hooks.json  →  SessionStart: "bd prime --hook-json"
│                        + D-02's self-healing copy-if-missing check (sibling command)
│                                │
│                                ▼
│                     if .beads/PRIME.md missing:
│                       copy .agents/skills/beads/PRIME.md → .beads/PRIME.md
│                                │
│                                ▼
│   .beads/PRIME.md  (runtime, generated — NOT the shipped source)
│                                │
│                                ▼
│   `bd prime` (any invocation, hook or manual) reads .beads/PRIME.md
│   if present → overrides bd's built-in default entirely (verified: `bd prime --help`)
│
└── (separately) .github/workflows/release.yml
       tag push `v*.*.*` → zip [.claude-plugin, hooks, .agents/skills, README.md, LICENSE]
                          → gh release create
       .agents/skills/beads/PRIME.md is inside the zipped tree automatically (no allowlist edit)
       .beads/PRIME.md is NEVER zipped (not in allowlist, by design — D-01)
```

### Recommended Project Structure (D-03)

```
.agents/skills/beads/
├── SKILL.md              # short entry point (current: 80 lines, single file)
├── PRIME.md              # NEW — .beads/PRIME.md's shipped source (D-01)
├── agents/
│   └── openai.yaml        # unchanged, existing
├── resources/             # NEW — progressive disclosure, upstream-pattern names
│   ├── DEPENDENCIES.md    # bd dep — matches upstream resources/DEPENDENCIES.md pattern
│   ├── WORKTREES.md
│   ├── ASYNC_GATES.md
│   ├── RESUMABILITY.md
│   ├── TROUBLESHOOTING.md
│   └── ... (per Claude's discretion, D-03)
└── commands/               # NEW — one file per PUB-11 topic that maps to a `bd` subcommand
    ├── dep.md
    ├── label.md
    ├── comments.md
    ├── search.md
    ├── compact.md
    ├── import.md
    ├── stats.md
    └── blocked.md
```

### Pattern 1: `.beads/PRIME.md` override (verified via live `bd prime --help`, bd v1.2.2)

**What:** `bd prime` auto-detects MCP vs CLI mode and prints workflow context; if `.beads/PRIME.md` exists in "the local clone or resolved workspace," its content is printed **instead of** `bd`'s built-in default — entirely, not merged.
**When to use:** Any project wanting to replace bd's generic CLI-mode reference (~1-2k tokens) with project-specific guidance.
**Verified flags** (source: `bd prime --help`, this session):
```
      --export          Output default content (ignores PRIME.md override)
      --full            Force full CLI output (ignore MCP detection)
      --hook-json       Wrap output in the SessionStart hook JSON envelope (Claude Code, Gemini CLI, Codex)
      --mcp             Force MCP mode (minimal output)
      --memories-only   Output only persistent memories for compact hook contexts
      --stealth         Stealth mode (no git operations, flush only)
```
This confirms PUB-12's success criterion 3 verification path exactly: `bd prime --export` bypasses the override (used to inspect bd's own default for comparison), while a bare `bd prime` (no flag) is the one that must print PRIME.md's content once it exists.

### Pattern 2: gsd-core sync-point dispatch (verified verbatim — `.gsd/capabilities/beads/capability.json` lines 57-140)

The four points PUB-12 requires PRIME.md to describe are defined exactly as:

```json
{ "point": "plan:post",         "ref": {"skill": "beads-sync"},   "produces": ["PLAN.md"], "consumes": ["PLAN.md"], "when": "beads.enabled", "onError": "skip" },
{ "point": "execute:wave:pre",  "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"], "consumes": ["PLAN.md"], "when": "beads.enabled", "onError": "skip" },
{ "point": "execute:wave:post", "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"], "consumes": ["PLAN.md"], "when": "beads.enabled", "onError": "skip" },
{ "point": "verify:post",       "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"], "consumes": ["UAT.md"],  "when": "beads.enabled", "onError": "skip" },
{ "point": "ship:pre",          "ref": {"skill": "beads-status"}, "produces": [],           "consumes": ["BEADS.md"],"when": "beads.enabled", "onError": "skip" }
```
[VERIFIED: .gsd/capabilities/beads/capability.json:72-139]

Plain-English behavior at each point (D-05's terse-bullet substance), from `beads-sync/SKILL.md` and `beads-status/SKILL.md` (read in full this session):

- **`plan:post`** (`beads-sync`): parses every `<task>` in the just-written PLAN.md, resolves or creates one phase epic, creates one `bd` issue per task (skipping tasks that already carry `<beads-id>`), rewrites PLAN.md in place with `beads_epic` frontmatter + per-task `<beads-id>`. Identity is bound by `<beads-id>` only, never by title match. `onError: skip` — never fails a phase.
- **`execute:wave:pre`** (`beads-status`, branch 2a): regenerates `BEADS.md` from a live `bd` query and prints a `<beads_status>` block naming the wave's synced issues; the orchestrator must paste that block into every executor `Agent()` prompt for the wave (no automatic fragment forwarding at this point).
- **`execute:wave:post`** (`beads-status`, branch "Step 2"): batch-closes every `<beads-id>` in every plan of the wave whose `SUMMARY.md` now exists — one `bd close` call across all plan ids in the wave, never per-task.
- **`verify:post`** (`beads-status`, branch 2b): regenerates `BEADS.md` read-only (recomputes `blocking_open`/`diverged`) — no wave/plan-id context, no close dispatch.
- **`ship:pre`** (`beads-status`, branches 2c/2d): (c) if `beads.ship_gate` is `false` and (`blocking_open>0` or `diverged>0`), records a `ship-override` git trailer + `bd` comment; (d) always verifies the local `ship.md` dispatch patch (`GSD-CORE-PATCH.md`) is still present, surfacing a `⚠` warning (non-blocking) if it was silently dropped by a `gsd-core` update.
- **Ship gate itself** (`capability.json` `gates[]`, lines 156-184): blocks (`blocking: true`) when `BEADS.md`'s frontmatter `blocking_open != 0` or `diverged != 0`, gated by `beads.ship_gate` (default `true`).

### Pattern 3: Path-confined file writes (established in-repo convention — reuse for D-02's self-heal)

`.gsd/capabilities/beads/scripts/sync.py` already establishes the pattern any new file-copy logic (D-02) should follow:
```python
# Source: .gsd/capabilities/beads/scripts/sync.py:116-139
def find_project_root(start):
    """Walk up from `start` to the nearest ancestor containing `.planning/`."""
    current = start.resolve()
    for _ in range(10):
        if (current / ".planning").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise ValueError(f"could not locate a .planning/ ancestor above {start}")

def confined(root, *parts):
    """Join parts onto root and reject any resolved escape (T-01-02)."""
    candidate = root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError(f"path escapes project root: {candidate} not under {root}")
    return candidate
```
[VERIFIED: .gsd/capabilities/beads/scripts/sync.py:116-139] — if D-02's self-heal is implemented as a Python script (one of the two discretionary options), it should reuse this exact helper pair rather than re-deriving a project root or destination path ad hoc.

### Anti-Patterns to Avoid

- **Treating PUB-11 as "ship literally every upstream command file":** upstream now has 29 command files (`audit`, `close`, `decision`, `delete`, `epic`, `export`, `init`, `list`, `quickstart`, `rename-prefix`, `restore`, `show`, `sync`, `template`, `version`, `workflow`, plus the 13 PUB-11 names). PUB-11's literal requirement text names a specific subset; D-04's "no curation, no cutting" applies to that named subset, not to the full upstream command surface, which has grown beyond gsd-core's stated needs (`bd mol`/`bd pour`/`bd gate create`-adjacent commands like `template`, `decision`, `sync`, `formula` are beads-project meta-features, not part of PUB-11's list).
- **Duplicating `bd <command> --help` output into a resource file:** upstream's own `CLI_REFERENCE.md` explicitly refuses to do this ("does not bundle a copied CLI command reference ... would drift if duplicated here") and points to `bd help --all` / `bd <command> --help` as the live source instead. Any new `commands/*.md` files in this repo's skill should follow the same discipline — describe usage patterns and gsd-core-specific framing, not a frozen copy of flag tables that will drift on the next `bd` release.
- **Shelling out with string-interpolated `bd` invocations:** every existing `bd` call in this repo's scripts uses a typed argv list via `subprocess.run([...])`, never a shell string built from file content (N4, threat T-01-01, `beads-sync/SKILL.md` Anti-Pattern 2). Any new script code in this phase (D-02) must follow the same discipline if it shells out to `bd` at all — though the self-heal check itself is a pure filesystem copy and need not invoke `bd`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detecting `bd`'s version/CLI surface for docs | A hardcoded command list frozen in a resource file | `bd help --all`, `bd <command> --help`, upstream's own `CLI_REFERENCE.md` pointer pattern | Upstream already solved this exact staleness problem by refusing to duplicate it; copying their refusal is cheaper than copying their table |
| Resolving the project root before writing `.beads/PRIME.md` | A new `.planning/`-walk-up loop | `find_project_root()` / `confined()` in `sync.py` (already imported nowhere outside that file, but the pattern is copy-paste-safe — 24 lines total) | Re-deriving path confinement risks reintroducing T-01-02 (path escape) in a second place |

**Key insight:** Nothing in this phase needs a new abstraction — it is markdown content plus, at most, a ~10-20 line idempotent copy-if-missing check. The existing `sync.py` helpers already cover the one piece of actual logic (safe path resolution) this phase might need.

## Common Pitfalls

### Pitfall 1: Over-scoping PUB-11 to "all upstream commands"
**What goes wrong:** A planner reading D-04's "No curation/cutting" literally against the *current* upstream skill (29 command files) produces a much larger deliverable than PUB-11 actually requires, wasting effort on gsd-core-irrelevant beads meta-features (`template`, `decision`, `sync`, `formula`, `epic`, `list`, `show`, `close`, `create`, `init`, `quickstart`, `rename-prefix`, `restore`, `version`, `workflow`, `audit`, `export`).
**Why it happens:** CONTEXT.md's canonical_refs cites "13 files" for `commands/`, which was accurate against an older upstream snapshot but is stale against the currently-installed v1.2.2 marketplace copy (29 files). The requirement text itself (ROADMAP.md Phase 9 SC1, REQUIREMENTS.md PUB-11) is the actual scope anchor and lists a specific, smaller set.
**How to avoid:** Treat the literal PUB-11/ROADMAP topic list — dependencies (`bd dep`), labels, comments, search, `compact`, `import`, `stats`, `blocked`, worktrees, async gates, resumability, `--stealth`/`BEADS_DIR`, troubleshooting — as the command/resource inventory to build, cross-checked against the *matching* upstream files (which do exist for every one of these topics: `commands/dep.md`, `commands/label.md`, `commands/comments.md`, `commands/search.md`, `commands/compact.md`, `commands/import.md`, `commands/stats.md`, `commands/blocked.md`, `resources/WORKTREES.md`, `resources/ASYNC_GATES.md`, `resources/RESUMABILITY.md`, `resources/TROUBLESHOOTING.md`).
**Warning signs:** A plan task listing 20+ new files, or referencing upstream commands not named in PUB-11's text.

### Pitfall 2: `.beads/PRIME.md` is not currently gitignored — self-healing generates an untracked file
**What goes wrong:** D-02 wires a copy-if-missing check into the SessionStart hook. Once it runs in this repo, `.beads/PRIME.md` appears as a new file. `git check-ignore -v .beads/PRIME.md` (run this session) exits 1 — **no pattern in `.beads/.gitignore` currently matches it** — so it will show as untracked in `git status`, which conflicts with this project's git-hygiene discipline (PUB-05's audit explicitly untracked `.beads/config.yaml`/`.beads/metadata.json` for the same reason: machine/session-generated `.beads/` content should not silently accumulate as dirty tree state).
**Why it happens:** CONTEXT.md's D-01/D-02 decide *where the source lives* and *when the copy happens*, but do not decide whether the runtime-generated destination (`.beads/PRIME.md`) should be git-tracked (committed once, satisfying ROADMAP SC2's "`.beads/PRIME.md` exists in the repo" literally) or gitignored (treated as a pure runtime artifact, consistent with Phase 7's "`.beads/` never ships" premise and PUB-05's precedent of untracking generated `.beads/` files).
**How to avoid:** Surface this explicitly to the user before the planner locks a task list — it's a real design fork, not a Claude's-discretion item under the current CONTEXT.md. Two coherent options: (a) add `.beads/PRIME.md` to `.beads/.gitignore` and treat "exists in the repo" as "exists in the working tree after the hook runs once" (matches the self-healing framing literally); (b) commit `.beads/PRIME.md` once as a checked-in convenience copy in *this* repo only (dogfooding), while every downstream installer still relies purely on the self-heal hook since their `.beads/` starts empty from `bd init`. Either is defensible; CONTEXT.md doesn't pick one.
**Warning signs:** `git status` showing `.beads/PRIME.md` as untracked after any task in this phase runs the hook for verification.

### Pitfall 3: Misattributing the rehearsal-tag-deletion precedent to the wrong phase
**What goes wrong:** CONTEXT.md's D-07 says the delete-then-recut pattern "matches Phase 7's precedent of deleting the throwaway `v0.0.0-rc1` rehearsal tag/release after use." Verified this session: `v0.0.0-rc1` was created and torn down in **Phase 8 Plan 01** (`08-01-PLAN.md`/`08-01-SUMMARY.md`; `gh release delete v0.0.0-rc1 --yes --cleanup-tag`), not in any Phase 7 file. Phase 7's actual irreversible action was a `git filter-repo` history rewrite (mirror-backup-then-rehearse pattern, `07-01-SUMMARY.md`), which is the correct contrast target for "this is lower-risk than Phase 7's history rewrite" — but the *tag-deletion* precedent itself is Phase 8's, not Phase 7's.
**Why it happens:** Both phases established similar-looking "rehearse then delete the throwaway artifact" disciplines; CONTEXT.md conflated the specific `v0.0.0-rc1` precedent with the phase number of the general discipline.
**How to avoid:** Cite `08-01-PLAN.md`/`08-01-SUMMARY.md` (not Phase 7) as the process precedent for the `v1.1.1` release-recut task; Phase 7 remains the correct citation only for the *general* "rehearse destructive/one-way operations on a throwaway artifact first" philosophy.
**Warning signs:** None functional — this only matters if a plan or SUMMARY.md cites "Phase 7" as the source of the release-delete transcript pattern; a reviewer checking that citation against `07-*` files will find nothing.

### Pitfall 4: Assuming `--stealth`/`BEADS_DIR` git-free mode has dedicated upstream documentation to copy from
**What goes wrong:** PUB-11 names "`--stealth`/`BEADS_DIR` git-free mode" as a topic to cover, implying a substantial upstream section exists. Verified this session: upstream mentions `BEADS_DIR` exactly once (`resources/WORKTREES.md` line 52, in the worktree-external-workspace context, not as a dedicated git-free-mode guide) and `--stealth` exactly once in `SKILL.md`'s Prerequisites line (`"Git repository (optional — use BEADS_DIR + --stealth for git-free operation)"`). The fuller documentation is in `bd init --help`'s own `--stealth` description (verified: *"configures per-repository git settings for invisible beads usage: `.git/info/exclude` to prevent beads files from being committed... To set up a specific AI tool, run: `bd setup <claude|cursor|aider|...> --stealth`"*) and `bd prime --help`'s `--stealth` flag (*"Stealth mode (no git operations, flush only)"*).
**Why it happens:** The topic exists and is real, but its authoritative source is the live `bd --help` output (two different `--stealth` flags on two different subcommands: `bd init --stealth` and `bd prime --stealth` are not the same flag), not a single upstream skill file to transcribe.
**How to avoid:** Write this topic from `bd init --help` + `bd prime --help` + the two one-line upstream mentions, not from a nonexistent upstream "STEALTH.md."
**Warning signs:** A plan task pointing at an upstream file for this topic that doesn't primarily cover it.

## Code Examples

### Current shipped `.agents/skills/beads/SKILL.md` frontmatter (baseline to preserve/extend)
```yaml
---
name: beads
description: Use when working in a repository that uses bd or Beads for durable project task tracking, issue dependencies, blocker management, multi-session handoff, or shared work memory. Trigger when the user asks to find ready work, claim or close tasks, create follow-up work, inspect blockers, recover project context, or choose between local planning and persistent project tracking.
---
```
[VERIFIED: .agents/skills/beads/SKILL.md:1-4]

### Current `hooks/hooks.json` (D-02's self-heal is a sibling addition here)
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "command": "bd prime --hook-json", "type": "command" }
        ],
        "matcher": ""
      }
    ]
  }
}
```
[VERIFIED: hooks/hooks.json:1-15]

### `.github/workflows/release.yml` (unchanged by this phase — allowlist already covers the new files)
```yaml
- name: Build allowlisted archive
  run: |
    zip -r gsd-beads.zip \
      .claude-plugin \
      hooks \
      .agents/skills \
      README.md \
      LICENSE
```
[VERIFIED: .github/workflows/release.yml:16-23] — `.agents/skills` is zipped recursively (`zip -r`), confirmed by the actual `v1.1.0` archive listing (`08-02-SUMMARY.md`) which already contains `.agents/skills/beads/agents/openai.yaml` — a file two directories deep. Adding `.agents/skills/beads/PRIME.md`, `resources/*.md`, `commands/*.md` requires zero `release.yml` edits.

### `.claude-plugin/plugin.json` (version bump target for the release task)
```json
{
  "name": "beads",
  "version": "1.1.0",
  "description": "Beads issue tracking for gsd-core's plan→execute→verify→ship lifecycle",
  "author": { "name": "Dennis A. V. Dittrich", "email": "davdittrich@gmail.com" },
  "license": "MIT",
  "skills": ["./.agents/skills/beads"]
}
```
[VERIFIED: .claude-plugin/plugin.json:1-11] — `version` is the only field the release task changes (same pattern as `08-02-SUMMARY.md` Task 1: `0.1.0` → `1.1.0`, byte-identical elsewhere).

### Release re-cut command sequence (from the proven `08-01`/`08-02` transcripts)
```bash
# Tear down the short v1.1.0 release/tag (D-07)
gh release delete v1.1.0 --yes --cleanup-tag

# Bump version, commit, push
# [.claude-plugin/plugin.json: "version": "1.1.0" -> "1.1.1"]
git commit -am "feat(09): bump plugin.json version to 1.1.1"
git push origin main

# Tag and let release.yml build+publish
git tag v1.1.1 && git push origin v1.1.1
gh run watch <run-id> --exit-status

# Verify allowlist-exact + PRIME.md/resources/commands present
gh release download v1.1.1 --pattern '*.zip' -O /tmp/gsd-beads-1.1.1.zip
unzip -Z1 /tmp/gsd-beads-1.1.1.zip | grep -E 'PRIME\.md|resources/|commands/'
```
[Pattern verified: `08-01-SUMMARY.md` lines 137-206, `08-02-SUMMARY.md` lines 157-224 — actual transcripts from the two most recent real release cycles on this repo]

### `bd prime --help` override + flags (verified against installed bd v1.2.2)
```
Workflow customization:
- Place a .beads/PRIME.md file in the local clone or resolved workspace to override the default output entirely.
- Use --export to dump the default content for customization.
- Use --memories-only for hook contexts that should inject only persistent memories.

Flags:
      --export          Output default content (ignores PRIME.md override)
      --full            Force full CLI output (ignore MCP detection)
      --hook-json       Wrap output in the SessionStart hook JSON envelope (Claude Code, Gemini CLI, Codex)
      --mcp             Force MCP mode (minimal output)
      --memories-only   Output only persistent memories for compact hook contexts
      --stealth         Stealth mode (no git operations, flush only)
```
[VERIFIED: live `bd prime --help` output, this session, bd version 1.2.2]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Upstream skill pinned at `bd >= 0.60.0` | Installed `bd` binary is `1.2.2` | Upstream `SKILL.md`'s own "Validation" section self-flags this drift and defers to `bd prime` as the "canonical source of truth" (ADR-0001) rather than trying to keep the skill file current | This repo's PRIME.md/SKILL.md should follow the same discipline — describe stable mechanisms (sync points, override file), not a frozen `bd --help` transcript that will drift on the next `bd` release |
| Single-file `SKILL.md` (current shipped state, 80 lines) | Progressive-disclosure `SKILL.md` + `resources/` + `commands/` split (upstream's model, D-03's target) | This phase | Matches PUB-11's explicit allowance; keeps the entry-point skill file's token cost low while depth loads on demand |

**Deprecated/outdated:** None — `bd`'s SQLite backend is deprecated in favor of Dolt (`bd init --help`: *"Dolt is the default (and only supported) storage backend. The legacy SQLite backend has been removed."*), but this repo's existing `.beads/` is already Dolt-based (`embeddeddolt.gate.lock` present) — not a concern for this phase's content.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact wording/bullet phrasing for PRIME.md's terse sync-point summaries — left to Claude's discretion per D-05, drafted from the verified `capability.json`/`SKILL.md` sources above but the final prose is not itself verified against a written artifact (none exists yet) | Architecture Patterns / Pattern 2 | Low — the underlying facts are verified; only phrasing choice is unconfirmed, and D-05 explicitly delegates phrasing to Claude's discretion |
| A2 | Which of the two `.beads/PRIME.md` git-tracking resolutions (gitignore vs. commit-once) the user prefers — not assumed here, flagged as Open Question / Pitfall 2 instead | Common Pitfalls / Pitfall 2 | N/A — not asserted as fact, explicitly surfaced as unresolved |

**If this table is empty:** N/A — one low-risk discretion item logged; no unverified factual claims were made in this research (every stack/mechanism claim was confirmed by reading a live file or live command output).

## Open Questions

1. **Should `.beads/PRIME.md` be git-tracked in this repo, or gitignored as a pure runtime artifact?**
   - What we know: `.beads/.gitignore` currently has no pattern matching `PRIME.md`; `.beads/` already has *some* tracked files (`.gitignore`, `README.md`, `hooks/*`) and some deliberately-untracked ones (`config.yaml`, `metadata.json`, per PUB-05). Either precedent exists in this repo.
   - What's unclear: ROADMAP SC2's "`.beads/PRIME.md` exists in the repo" could be satisfied either way — by a one-time commit, or by "exists in the working tree once the SessionStart hook has run at least once."
   - Recommendation: Ask the user directly before the plan locks a task list for D-02's hook implementation; this determines whether the plan needs a `.gitignore` edit task and whether verification checks `git ls-files` or just filesystem presence.

2. **Does the self-healing hook need to invoke `bd` at all, or is it a pure filesystem copy?**
   - What we know: `bd prime --help` resolves `.beads/PRIME.md` itself once present — the hook's only job is to ensure the file exists before or independent of the `bd prime --hook-json` call already in `hooks/hooks.json`.
   - What's unclear: Whether the check should run *before* `bd prime --hook-json` in the same hook entry (so the very first `bd prime` call already sees the override) or as an independent hook step — ordering matters for SessionStart hook arrays.
   - Recommendation: Order the copy-if-missing check before the existing `bd prime --hook-json` command in the same `hooks/hooks.json` entry (two commands in the `hooks[]` array, or a single shell command chaining `&&`), so the first `bd prime` invocation of a session already benefits from the override.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `bd` CLI | `bd prime` override verification, release round-trip | ✓ | 1.2.2 | — |
| `gh` CLI | Release delete/tag/watch/download sequence | ✓ | (used successfully in Phase 8 transcripts; available on this machine) | — |
| GitHub Actions (`release.yml`) | Zip build + release publish | ✓ | Unchanged from Phase 8 | — |
| Upstream `beads` skill (comparison target) | PUB-11 parity check | ✓ | v1.2.2 marketplace copy at `/home/dd/.claude/plugins/marketplaces/beads-marketplace/plugins/beads/skills/beads/` | — |

**Missing dependencies with no fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | No dedicated content-test framework; this project's established pattern is grep-based `<verify>` blocks inside PLAN.md tasks (see `08-03-SUMMARY.md`, `08-02-SUMMARY.md`) plus e2e transcript verification (fresh clone + `claude plugin validate` + real `bd prime` run). A pytest suite exists at `.gsd/capabilities/beads/tests/test_sync.py` for `sync.py`'s Python logic only — applicable if D-02's self-heal is implemented as a Python script. |
| Config file | none — see Wave 0 |
| Quick run command | `grep -rli "<topic>" .agents/skills/beads/` per PUB-11 topic (content coverage) |
| Full suite command | fresh-clone `claude plugin validate . --strict` + `gh release download` + `unzip -Z1` listing check (Phase 8 pattern) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PUB-11 | SKILL.md/resources/commands cover all named topics | content-grep | `grep -rlqi "worktree\|async.gate\|resumab\|stealth\|BEADS_DIR" .agents/skills/beads/` per topic | ❌ Wave 0 — no coverage-check script exists yet |
| PUB-12 (SC2) | `.beads/PRIME.md` exists + shipped source is in the release allowlist | filesystem + archive listing | `test -f .beads/PRIME.md`; `unzip -Z1 gsd-beads.zip \| grep 'PRIME.md'` | ❌ Wave 0 |
| PUB-12 (SC3) | fresh `bd prime` (no `--export`) prints PRIME.md content | e2e | install into scratch project, delete `.beads/PRIME.md`, trigger SessionStart hook, run `bd prime`, grep for a PRIME.md-unique marker string | ❌ Wave 0 |
| SC4 (v1.1.1 tag) | `v1.1.1` release replaces `v1.1.0`, README-driven install works | e2e | Same Gate A/Gate B sequence as `08-02-SUMMARY.md` (fresh-clone validate + marketplace add/install/uninstall round trip) | ✅ — proven script/transcript pattern exists (08-02), just needs re-running at the new tag |

### Sampling Rate
- **Per task commit:** content-grep checks for the specific topic(s) that task added
- **Per wave merge:** full `claude plugin validate . --strict` (local, no allowlist involved) + `.beads/PRIME.md` presence check
- **Phase gate:** Full Phase 8-pattern release round trip (Gate A + Gate B) at the new `v1.1.1` tag before closing the phase

### Wave 0 Gaps
- [ ] A content-coverage grep script/checklist enumerating each PUB-11 topic against the shipped files (no such script exists in this repo yet — Phase 8's checks were all one-off transcript greps, not a reusable script)
- [ ] If D-02's self-heal is a Python script: a `test_*.py` addition to `.gsd/capabilities/beads/tests/` exercising the copy-if-missing idempotency (create when absent, no-op when present, refuses to escape `.beads/`)
- [ ] Framework install: none — no new framework needed, reuses grep + existing `gh`/`claude` CLI-driven e2e pattern

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface in this phase |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | Yes (narrow) | The self-heal copy destination (`.beads/PRIME.md`) must be a hardcoded relative path under a resolved project root, never derived from any external/untrusted input — reuse `confined()`/`find_project_root()` from `sync.py` (Pattern 3 above) |
| V6 Cryptography | No | — |
| V12 File and Resources | Yes | Path confinement for the copy-if-missing write (T-01-02, already an established threat ID in this repo's threat model) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via unvalidated destination path in a file-copy hook | Tampering | Hardcode the destination as `.beads/PRIME.md` relative to a `find_project_root()`-resolved root; never construct the path from hook arguments, env vars, or file content (mirrors `sync.py`'s existing `confined()` discipline, T-01-02) |
| Shell-string-interpolated command construction (if the hook shells out at all) | Tampering | Use a typed argv list (`subprocess.run([...])`) or Claude Code's `hooks.json` `command`/`type: "command"` fields directly — never build a shell string from file content (N4, T-01-01, established throughout `beads-sync/SKILL.md`'s Anti-Patterns) |

## Sources

### Primary (HIGH confidence — verified this session via `Read` or live command output)
- `/home/dd/.claude/plugins/marketplaces/beads-marketplace/plugins/beads/skills/beads/SKILL.md` and `resources/`, `commands/` directory listings — the real upstream comparison target
- `bd prime --help`, `bd init --help`, `bd --help`, `bd --version` (installed bd v1.2.2) — override mechanism and `--stealth` semantics
- `.gsd/capabilities/beads/capability.json` — sync-point definitions (`steps[]`, `gates[]`)
- `.gsd/capabilities/beads/skills/beads-sync/SKILL.md`, `beads-status/SKILL.md` — sync-point behavior
- `.gsd/capabilities/beads/scripts/sync.py` — path-confinement pattern (`confined()`, `find_project_root()`)
- `hooks/hooks.json`, `.github/workflows/release.yml`, `.claude-plugin/plugin.json` — current shipping mechanism
- `.beads/.gitignore`, `git check-ignore -v .beads/PRIME.md`, `git ls-files .beads/` — git-tracking state of `.beads/`
- `.planning/phases/08-readme-release-ship-gate/08-01-SUMMARY.md`, `08-02-SUMMARY.md` — proven release-recut transcript pattern
- `.planning/phases/07-hygiene-publication/07-01-SUMMARY.md` — Phase 7's actual history-rewrite precedent (for the Pitfall 3 correction)
- `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/config.json`, `.planning/phases/09-beads-content-depth/09-CONTEXT.md`

### Secondary (MEDIUM confidence)
- None used — no web search was necessary this session; every fact was verifiable locally.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependency, nothing to verify beyond "no packages added"
- Architecture (sync points, override mechanism): HIGH — every value quoted verbatim from a file read or command run this session
- Pitfalls: HIGH — each pitfall is backed by a direct comparison against a verified source (upstream directory listing, `git check-ignore` output, `08-01`/`07-01` file contents)

**Research date:** 2026-08-16
**Valid until:** 14 days — `bd` releases frequently (currently 1.2.2, upstream skill pinned at 0.60.0) and the upstream marketplace skill could update independently of this research

