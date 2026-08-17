# Stack Research

**Domain:** gsd-core capability plugins (`pr-workflow`, `markdown-linting`, `get-available-resources`) for gsd-beads
**Researched:** 2026-08-18
**Confidence:** HIGH (verified against official `cli.github.com`/GitHub docs and `DavidAnson/markdownlint-cli2`
GitHub source/package.json; MEDIUM on stdlib-vs-psutil recommendation, corroborated across multiple sources but
no single canonical spec)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `gh` CLI | `>=2.97.0` current stable (2026-07-31); any `gh` supporting `pr checks --json` (shipped years ago) works | Backs `pr-workflow`'s `gh pr create`/`gh pr checks --watch`/`gh api` calls | Official GitHub CLI, already the transitive tool this repo's own git workflow assumes (`gh repo create`/`gh release create` appear in global CLAUDE.md); no alternative ships an equivalent authenticated, machine-parseable PR/checks API from the shell |
| `markdownlint-cli2` | `0.23.2` (npm, published ~2 weeks before research date) | Backs `markdown-linting`'s lint pass over `.planning/**/*.md` | Same engine used by the `davidanson.vscode-markdownlint` VS Code extension and the official `markdownlint-cli2-action`; config-file-driven (no CLI flag sprawl), fast, and is the tool this repo's own inspiring skill (`~/.claude/skills/markdown-linting/`) already standardizes on — no reason to diverge |
| Python 3 stdlib (`os`, `shutil`, `platform`, `subprocess`) | whatever Python 3 this repo already requires for `beads`/`sota-numerics` scripts | Backs `get-available-resources`'s CPU/GPU/memory/disk detection | Matches N5 exactly (beads' Out-of-Scope: "Any dependency beyond the `bd` binary and Python 3 standard library") — extending that same constraint to the two new Python-backed capabilities keeps one dependency policy across the whole repo instead of one-off exceptions |

### Supporting Libraries

None. All three capabilities are shell/stdlib wrappers around already-external CLIs (`gh`, `markdownlint-cli2`)
or the Python 3 standard library — no new pip package is needed for any of the three.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `gh pr checks --json bucket,state,name,link,workflow` | Machine-parseable check status for the `ship:pre` gate | `--json` accepts exactly these fields: `bucket`, `completedAt`, `description`, `event`, `link`, `name`, `startedAt`, `state`, `workflow`. `bucket` is the field to gate on — it collapses `state` into one of `pass`/`fail`/`pending`/`skipping`/`cancel`, so the gate script does not need to enumerate raw CI-provider state strings. Exit code `8` = "checks pending" (distinct from a genuine non-zero failure) — a gate script must branch on this before treating a non-zero exit as a hard failure. |
| `markdownlint-cli2 "**/*.md"` against `.planning/**/*.md` via `.markdownlint-cli2.jsonc` | Verify/ship-lifecycle lint gate | Exit codes: `0` clean, `1` lint errors found (this is the gate's real fail signal), `2` tool/config failure (crash, bad config — should route through `onError`, not "lint failed") |
| `os.cpu_count()`, `shutil.disk_usage()`, `/proc/meminfo` (Linux) / `sysctl`+`vm_stat` (macOS) / `nvidia-smi`/`rocm-smi` (GPU) | CPU/mem/disk/GPU detection with zero new deps | See "What NOT to Use" — `psutil` is the one dependency in the inspiring skill this capability must NOT inherit |

## Installation

No `npm install`/`pip install` step ships inside any of the three capability bundles. Each capability's
`capability.json` documents its external prerequisite the same way `beads` documents `bd`:

```bash
# pr-workflow prerequisite (not installed by the plugin — user-provided, like bd)
gh --version   # >=2.97.0 recommended; any gh with `pr checks --json` support works
gh auth status

# markdown-linting prerequisite (Node/npm — NEW class of dependency for this repo, see below)
npx markdownlint-cli2 --version   # or: npm install -g markdownlint-cli2

# get-available-resources: zero prerequisite beyond python3 already required by beads/sota-numerics
python3 --version
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|--------------------------|
| `gh pr checks --json` + `bucket` field | Polling `gh api repos/{owner}/{repo}/commits/{sha}/check-runs` directly | Only if a capability needs raw per-check-run metadata (log URLs, annotations) that `gh pr checks --json` doesn't expose — adds JSON-shape complexity for no benefit to a pass/fail/pending gate |
| `markdownlint-cli2` | `markdownlint-cli` (v1, the older/simpler CLI) | Only for flat rule-only linting with no glob/ignore config needs; `-cli2` is what the inspiring skill, the VS Code extension, and the official GitHub Action all standardize on today — no reason to pick the older tool |
| `markdownlint-cli2` | `remark-lint` / `remark-cli` | If the project needed AST-level custom lint rules or markdown transforms beyond style checking; pure style/MD0XX linting doesn't need a full unified/remark pipeline |
| stdlib + `/proc`/`sysctl`/`nvidia-smi` shell-outs | `psutil` (the inspiring skill's actual dependency) | Only if the capability needs live *process*-level metrics (per-process CPU%, memory maps) rather than one-shot host-level totals — a `plan:pre`/`execute:wave:pre` advisory snapshot never needs that, and `psutil` is a binary-wheel C-extension dependency this repo's N5 constraint exists specifically to avoid |
| stdlib + `nvidia-smi`/`rocm-smi` GPU shell-outs | `torch.cuda.is_available()` / `pynvml` | Only if the capability needs to run *inside* a Python process that already imports PyTorch — this is a standalone pre-execution advisory hook, so importing a multi-hundred-MB ML framework just to detect a GPU is the wrong tool for the job |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|--------------|
| `psutil` (the inspiring `get-available-resources` skill's actual runtime dependency, per its own SKILL.md `## Dependencies` section: `uv pip install psutil`) | Breaks N5 (beads' documented "no dependency beyond `bd` and Python 3 stdlib") the moment it's copied into this repo — introduces the first pip dependency across all four capabilities, plus platform-specific wheel-build risk (musl/ARM edge cases) for a lifecycle hook that must be zero-friction to auto-install | `os.cpu_count()`/`shutil.disk_usage()` for CPU count and disk; `/proc/meminfo` parse on Linux, `sysctl -n hw.memsize` + `vm_stat` parse on macOS for memory (see Stack Patterns below) |
| `detect_resources.py`'s bare `except Exception: pass` around every subprocess call | Silently swallows the *reason* a GPU/tool wasn't found (missing binary vs. permission error vs. malformed output) — fine for an interactive skill a human can re-run with `-v`, wrong for a non-interactive lifecycle hook where the only artifact anyone reads is the JSON file; a swallowed exception there is indistinguishable from "no GPU present" | Catch `FileNotFoundError` (binary absent — expected, silent) separately from any other exception (unexpected — log to stderr once, still degrade fail-open) |
| `detect_resources.py`'s non-deterministic `timestamp` field (`datetime.now().isoformat()`) as part of the JSON gsd fragments hash/diff against | A lifecycle hook's output feeds a *prompt fragment* injected every `plan:pre`/`execute:wave:pre`; a timestamp that changes every run defeats any future idempotency/caching check (the same class of bug the `beads` capability had to fix for its own generated artifacts — B5, "sync is idempotent") | Keep `timestamp` for human-readability in `.claude_resources.json` but do not let any gate/step declare it as a `produces`/cache key; the fragment consumed by the planner should summarize *ranges* ("8+ logical cores → high_parallelism"), not raw numbers, so the fragment text itself is stable run-to-run on an unchanged machine |
| A declarative `command-exists` gate predicate for detecting `gh`/`markdownlint-cli2`/GPU tools | **Does not exist.** Read directly from `gate-predicate-evaluator.cjs`: `EVALUATOR_KINDS = ['command-exit-zero', 'artifact-frontmatter-equals']` — no `command-exists` kind is implemented, despite PROJECT.md's Constraints section naming it as one of "only two predicate kinds" (that line is stale/wrong) | Presence-detection is a *runtime* check inside each capability's own script, exactly like `beads/scripts/sync.py:89`'s `shutil.which("bd") is None` fail-open branch — `pr-workflow` and `markdown-linting` scripts must open with `shutil.which("gh")`/`shutil.which("markdownlint-cli2")` and degrade to a no-op-with-notice (B6's pattern) before doing anything else; any *gate* still expressed declaratively uses `command-exit-zero` wrapping a script that internally handles the missing-binary case and exits 0 (pass/skip) rather than crashing |
| Auto-installing `markdownlint-cli2` (or Node itself) from inside a capability hook | gsd-core capabilities have no package-manager-invocation contribution point, and silently running `npm install -g` from a `plan:pre`/`ship:pre` hook is a supply-chain and consent problem worse than the one CB-3 already exists to gate for capability *bundles* themselves | Document `gh`/Node+`markdownlint-cli2` as an explicit prerequisite in each capability's README, exactly like `bd` is documented for `beads` — detect absence, degrade fail-open, never auto-provision |

## Stack Patterns by Variant

**If detecting memory on Linux:**
- Parse `/proc/meminfo` directly (`MemTotal`, `MemAvailable` keys) — no subprocess needed, stdlib `open()` only
- `MemAvailable` (not `MemFree`) is the correct "free for new allocation" figure — matches what `free -h` reports and what `psutil.virtual_memory().available` computes internally

**If detecting memory on macOS:**
- `sysctl -n hw.memsize` (bytes, total) via `subprocess.run` — stdlib-only, no new dependency
- `vm_stat` output parse for free/active/inactive page counts if "available" (not just "total") memory is needed; page size comes from the first line of `vm_stat`'s own output (`page size of 4096 bytes` — do not hardcode 4096, Apple Silicon can differ)

**If detecting GPUs:**
- NVIDIA: `nvidia-smi --query-gpu=... --format=csv,noheader,nounits` (already the inspiring skill's approach — this part is sound, keep it)
- AMD: `rocm-smi` (keep — same as inspiring skill)
- Apple Silicon: `sysctl -n machdep.cpu.brand_string` + `system_profiler SPDisplaysDataType` (keep — same as inspiring skill; `system_profiler` is slow (~1-2s) but this is a one-shot `plan:pre` hook, not a hot path)
- All three: wrap in a 3-5s `subprocess.run(..., timeout=N)` exactly as the inspiring skill already does — a hung `nvidia-smi` on a broken driver must not stall the whole gsd lifecycle step

**If a hook needs the resources JSON to feed a prompt fragment (not just a file on disk):**
- Follow `sota-numerics`' pattern (`contributions[]`, `fragment.path`, no `steps[]`, no `skills[]`) rather than `beads`' pattern (`steps[]` + `skills[]`) — `get-available-resources` is purely advisory with no state to sync, so it needs no skill invocation step, just a `plan:pre`/`execute:wave:pre` `contributions[]` entry whose fragment text is generated by a `scripts/detect-resources.py` the fragment template shells out to (or a pre-generated `.claude_resources.json` the fragment reads)

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| `markdownlint-cli2@0.23.2` | Node.js `>=20` (from upstream `package.json` `engines.node`) | This is a genuinely new dependency class for gsd-beads — every other capability in this repo (`beads`, `ponytail-everywhere`, `sota-numerics`) requires only `bd`/Python; `markdown-linting` is the first to require Node/npm. Document this explicitly and loudly in its own README's prerequisites section — do not bury it as a footnote |
| `gh@2.97.0` | No Node/Python dependency — single static Go binary | Orthogonal to the Node requirement above; `pr-workflow` stays dependency-light like `beads`/`sota-numerics` even though `markdown-linting` does not |
| `markdownlint-cli2-action@v22` | `actions/checkout@v5` | Only relevant if/when this repo also wires markdown linting into its own `.github/workflows/*.yml` — not required for the capability plugin itself, which runs via `verify:post`/`ship:pre` hooks inside the gsd lifecycle, not CI |

## Answers to the Specific Questions

**`gh pr checks --json` current fields/exit codes:** Confirmed via `cli.github.com/manual/gh_pr_checks`.
Fields: `bucket, completedAt, description, event, link, name, startedAt, state, workflow`. Exit code `8` =
"checks pending" — a gate script must treat this as a distinct outcome from a real failure, not `exit != 0
== block`. `bucket` (not raw `state`) is the field to build the gate predicate on, since it's already
normalized to `pass`/`fail`/`pending`/`skipping`/`cancel` across every CI provider gh talks to.

**`markdownlint-cli2` version/config/Node dependency:** `0.23.2` current stable. Config precedence for the
richer `.markdownlint-cli2.*` family (glob/ignore control, not just rule config) is `.jsonc` > `.yaml` >
`.cjs` > `.mjs`; use `.markdownlint-cli2.jsonc` — it is both first in precedence and what the inspiring skill
and this domain's ecosystem already converge on. It requires Node.js `>=20` — this **is** a new dependency
class for gsd-beads (every other capability requires only `bd`/Python). Document it as a hard, loud
prerequisite, not something auto-installed.

**Cross-platform resource detection, zero new pip/npm deps:** stdlib (`os.cpu_count`, `shutil.disk_usage`,
`platform`) covers CPU-count/disk/OS entirely with no subprocess. Memory has no stdlib equivalent — parse
`/proc/meminfo` on Linux, shell out to `sysctl`+`vm_stat` on macOS (both zero-dependency, subprocess-only).
GPU detection has no stdlib path on any platform — the inspiring skill's `nvidia-smi`/`rocm-smi`/
`system_profiler` shell-out approach is genuinely the current best practice here (no better stdlib-only
alternative exists) and should be kept largely as-is. What should change for a lifecycle-hook (deterministic,
non-interactive) context rather than an interactive-skill context: (1) drop `psutil` entirely — it's the one
piece of the inspiring skill that violates this repo's N5 constraint and has a stdlib-only substitute for
everything except memory, which subprocess-parsing covers; (2) stop swallowing all subprocess exceptions
identically — distinguish "binary absent" (expected, silent) from "binary present but errored" (log once,
still fail-open); (3) treat the JSON's `timestamp` field as human-readable metadata only, never as part of
any idempotency/cache key, and keep the prompt-fragment text itself expressed in stable qualitative buckets
rather than raw numbers that drift run-to-run on an otherwise-unchanged machine.

**`gh`/`markdownlint-cli2` as assumed-present prerequisites vs. auto-detect + graceful degrade:** Both should
be **documented prerequisites with runtime detect-and-degrade**, matching B6's `bd` pattern exactly — not
auto-installed (no safe mechanism exists inside a gsd capability hook for invoking `npm install -g` or
`brew install gh`), but also not silently assumed present without a check. Concretely: each capability's own
script opens with `shutil.which("gh")` / `shutil.which("markdownlint-cli2")`; on `None`, print one visible
notice and no-op (matching B6's exact wording), and any declarative gate wraps that same script via
`command-exit-zero` — the *evaluator* only supports `command-exit-zero`/`artifact-frontmatter-equals`
(verified by reading `gate-predicate-evaluator.cjs`'s `EVALUATOR_KINDS`; there is no `command-exists`
predicate kind despite PROJECT.md's Constraints section implying one exists), so presence-detection cannot
be pushed into a declarative gate — it must live in the wrapped script itself, one layer below the gate.
`gh` is the safer assumption of the two (near-ubiquitous on dev machines already using this repo's own
git/PR workflow per global CLAUDE.md; a single static binary, no runtime dependency chain).
`markdownlint-cli2` is the riskier assumption — it drags in an entire Node/npm toolchain this repo has never
required before — so its README prerequisite section should be the most explicit of the three capabilities
about what "missing" looks like and how the capability behaves when it's absent (silent skip + one notice,
never a blocking crash).

## Sources

- [gh pr checks — official CLI manual](https://cli.github.com/manual/gh_pr_checks) — verified `--json` field list and exit code 8, HIGH confidence (official docs, WebFetch-verified)
- [cli/cli GitHub Releases](https://github.com/cli/cli/releases) — verified current `gh` stable is `2.97.0` (2026-07-31), HIGH confidence
- [markdownlint-cli2 — npm](https://www.npmjs.com/package/markdownlint-cli2) — verified current version `0.23.2`, HIGH confidence
- [DavidAnson/markdownlint-cli2 — GitHub](https://github.com/DavidAnson/markdownlint-cli2) — verified config precedence, exit codes (0/1/2), Docker-implies-Node, HIGH confidence (official repo, WebFetch-verified)
- `DavidAnson/markdownlint-cli2/package.json` `engines.node` field (via web search corroboration) — Node `>=20` requirement, MEDIUM-HIGH confidence (not directly WebFetched, but consistent across multiple independent search results)
- Stdlib-vs-psutil resource-detection approach — synthesized from multiple independent sources (Sling Academy, BioErrorLog, psutil's own docs confirming no stdlib memory equivalent), MEDIUM confidence (no single canonical spec, but convergent across sources)
- `/home/dd/.claude/gsd-core/bin/lib/gate-predicate-evaluator.cjs` (local source read) — verified `EVALUATOR_KINDS = ['command-exit-zero', 'artifact-frontmatter-equals']`, HIGH confidence (direct source read, not inference)
- `/home/dd/.claude/gsd-core/workflows/ship.md` (local source read, Step 8) — verified the local `ship:pre` patch generically dispatches non-security/broken-windows gates via `command.query`/`command.predicate`, HIGH confidence
- `/home/dd/projects/gsd-beads/.gsd/capabilities/beads/scripts/sync.py:89` (local source read) — verified `shutil.which("bd") is None` as the actual B6 degrade-detection pattern to replicate for `gh`/`markdownlint-cli2`, HIGH confidence
- `~/.claude/skills/pr-workflow/SKILL.md`, `~/.claude/skills/markdown-linting/SKILL.md`, `~/.claude/skills/get-available-resources/SKILL.md` (local reads) — inspiring skills' mechanisms, used as a starting point and explicitly revised where current best practice or this repo's constraints diverge

---
*Stack research for: gsd-core capability plugins (pr-workflow, markdown-linting, get-available-resources)*
*Researched: 2026-08-18*
