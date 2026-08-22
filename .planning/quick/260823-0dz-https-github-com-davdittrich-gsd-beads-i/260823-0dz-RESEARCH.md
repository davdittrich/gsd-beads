# Quick 260823-0dz: Direct Skill `sync.py` Resolution - Research

**Researched:** 2026-08-23
**Bead:** `gsd-beads-elt.4`
**Overall confidence:** HIGH (97/100)

## Recommendation

Reuse the lifecycle hook's ordered candidate scan in every executable Bash
block of the four direct skills: project-local first, global
`${GSD_HOME:-$HOME}` second, plugin-bundled third. In skill content, express
the project and plugin roots with Claude Code's `${CLAUDE_PROJECT_DIR}` and
`${CLAUDE_PLUGIN_ROOT}` placeholders; the official plugin reference defines
those as the project root and absolute plugin installation directory and
substitutes them anywhere in skill content. Keep each selected path
double-quoted, retain the existing `python3 "$SYNC_PY" <subcommand> ...`
argument suffix verbatim, and emit a stable stderr message plus non-zero exit
when no regular-file candidate exists. [VERIFIED:
plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh:98-109] [CITED:
code.claude.com/docs/en/plugins-reference] **Confidence: 99/100.**

Do not add a helper, wrapper, dependency, auto-install branch, or second path
policy. A helper would itself need locating before it could locate `sync.py`;
repeating the small canonical prelude in the skill command blocks and enforcing
parity in one table-driven test is the smallest closed solution. [VERIFIED:
`bd show gsd-beads-elt.4`] **Confidence: 96/100.**

### Plan Header Implications

- **Mechanism:** Canonical ordered regular-file resolver:
  `${CLAUDE_PROJECT_DIR}` -> `${GSD_HOME:-$HOME}` -> `${CLAUDE_PLUGIN_ROOT}`,
  followed by the unchanged `python3` argv. **Confidence: 99/100.**

- **Forbidden:** Project-relative-only execution, `PATH`/`command -v` lookup
  for `sync.py`, a new resolver file, gsd-core edits, auto-install changes,
  dependency additions, or changed subcommands/arguments. **Confidence:
  99/100.**

- **Audit:** A fake `sync.py` spy records the selected script path and exact
  `sys.argv[1:]`; exact-equality assertions cover every skill, every precedence
  arm, and the no-candidate error. Existing lifecycle-hook tests remain an
  independent regression gate. **Confidence: 98/100.**

## Existing Mechanism with Exact File Evidence

The lifecycle hook already searches these values verbatim and stops at the
first regular file:
`"$PROJECT_DIR/.gsd/capabilities/beads/scripts/sync.py"`,
`"${GSD_HOME:-$HOME}/.gsd/capabilities/beads/scripts/sync.py"`, then
`"${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}/.gsd/capabilities/beads/scripts/sync.py"`.
Its no-candidate contract is the verbatim fail-open guard
`[ -n "$SYNC_PY" ] || exit 0`; that hook behavior is out of scope and must not
change. [VERIFIED:
plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh:98-116] **Confidence:
100/100.**

The four direct skills bypass that resolver and currently hard-code the
project-relative prefix:

| Skill | Existing command suffixes that must remain verbatim | Evidence | Confidence |
|---|---|---|---:|
| `gsd-beads-sync` | `create-issues <PLAN.md path>` | [VERIFIED: plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-sync/SKILL.md:51-60] | 100/100 |
| `gsd-beads-recall` | `beads-recall <phase directory>`; `check-patch ship-md`; `check-patch execute-plan` | [VERIFIED: plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-recall/SKILL.md:49-74] | 100/100 |
| `gsd-migrate-todos` | `migrate-todos` | [VERIFIED: plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-migrate-todos/SKILL.md:47-54] | 100/100 |
| `gsd-beads-status` | `wave-status-block ...`; `reconcile-stale-closed`; `regenerate-beads-md`; `ship-override ...`; `check-patch ship-md`; `status ...`; `close-wave ...` | [VERIFIED: plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md:74-105] [VERIFIED: plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md:164-200] [VERIFIED: plugins/beads-lifecycle/.gsd/capabilities/beads/skills/beads-status/SKILL.md:231-248] | 100/100 |

## Alternatives Considered

Ranks are 1 = best. Performance is ranked first, then simplicity/LOC,
ecosystem support, and maintenance, matching the repository's required
decision order.

| Approach | Performance | LOC / simplicity | Ecosystem | Maintenance | Verdict | Confidence |
|---|---:|---:|---:|---:|---|---:|
| Reuse the ordered prelude in skill Bash blocks | 1 | 1 | 1 | 2 | **Use.** Three bounded `-f` checks, no extra process or file, and official skill placeholders cover project/plugin roots. [CITED: https://code.claude.com/docs/en/plugins-reference] | 97/100 |
| Add `resolve-sync.sh` and source/call it | 2 | 3 | 2 | 1 | Reject. Centralizes text but creates a bootstrap path-resolution problem and another shipped artifact. [VERIFIED: bd show gsd-beads-elt.4] | 95/100 |
| Add a plugin `bin/` wrapper and rely on `PATH` | 2 | 2 | 1 | 3 | Reject. Claude Code supports plugin executables on Bash `PATH`, but the wrapper still needs the same project/global/plugin policy and weakens standalone project/global capability behavior. [CITED: https://code.claude.com/docs/en/plugins-reference] | 93/100 |
| Keep `.gsd/.../sync.py` relative to cwd | 1 | 1 | 3 | 3 | Reject: it is the global-only failure mechanism recorded by the bead. [VERIFIED: bd show gsd-beads-elt.4] | 100/100 |

## Testing Strategy

Add one table-driven stdlib `unittest` class to the existing `test_sync.py`;
the suite already uses only standard-library `tempfile`, `subprocess`,
environment maps, and `unittest`, and the lifecycle-hook harness already runs
Bash against isolated temporary workspaces. [VERIFIED:
plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:1-20]
[VERIFIED:
plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:4718-4748]
**Confidence: 99/100.**

For each of the four skill files, execute the exact resolver/invocation block
from an unrelated temporary cwd with fake project, global, and plugin roots.
Assert exact selected path and exact argument vector for: global-only; local
plus global plus plugin (local wins); plugin-only; and no candidates (non-zero,
clear stderr, spy not called). Add a static exact-suffix inventory assertion so
every pre-existing subcommand and placeholder argument survives the Markdown
rewrite. [VERIFIED: `bd show gsd-beads-elt.4`] **Confidence: 98/100.**

Tests-first gate: the global-only and plugin-only cases must fail against the
current project-relative commands before implementation. After implementation,
run the focused new class, existing `TestLifecycleDispatchHook`, then the
repository's canonical full command from the capability root:
`python3 -m unittest discover -s tests -t tests`. [VERIFIED:
.github/workflows/ci.yml:36-40] [VERIFIED:
plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py:4718-4888]
**Confidence: 99/100.**

## Security Domain

Security enforcement is enabled at ASVS level 1. The applicable control is
path/input handling and OS-command injection prevention: use only the three
fixed candidate suffixes, quote every expanded root/path, avoid `eval` and
shell-built argv strings, and pass subcommand arguments as distinct words.
Authentication, sessions, access control, and cryptography do not apply to this
local resolver. [VERIFIED: .planning/config.json:50-53] [CITED:
owasp.org/www-project-application-security-verification-standard/] **Confidence:
96/100.**

## Project Constraints (from AGENTS.md)

- Beads is the authoritative task tracker; `gsd-beads-elt.4` already provides
  the required open task, and this research must not create parallel Markdown
  task lists. [VERIFIED: AGENTS.md:45-60] **Confidence: 100/100.**

- The conservative profile forbids commit/push without authority; this research
  produces only the assigned file. [VERIFIED: AGENTS.md:64-94] **Confidence:
  100/100.**

- Any later file operations must use non-interactive forms, and OpenWolf
  requires targeted anatomy lookup before unfamiliar file reads. [VERIFIED:
  AGENTS.md:18-40] [VERIFIED: AGENTS.md:121-125] **Confidence: 100/100.**

## Pitfalls

- Do not copy the lifecycle hook's `$0`-relative plugin fallback into skill Bash.
  In a shell command, `$0` denotes the shell/script invocation, while Claude
  Code directly supplies `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PROJECT_DIR}`
  inside skill content. [CITED: GNU Bash Reference Manual] [CITED:
  code.claude.com/docs/en/plugins-reference] **Confidence: 97/100.**

- Do not change the hook's silent `[ -n "$SYNC_PY" ] || exit 0`; only direct
  human-invoked skills adopt the clear non-zero missing-candidate contract.
  [VERIFIED: plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh:101-109]
  [VERIFIED: `bd show gsd-beads-elt.4`] **Confidence: 100/100.**

- Use `-f`, not `-x`: `sync.py` is passed to `python3`, so an executable bit is
  not required. `${GSD_HOME:-$HOME}` deliberately treats an unset or null
  `GSD_HOME` as fallback to `HOME`. [CITED:
  pubs.opengroup.org/onlinepubs/9799919799/utilities/test.html] [CITED:
  GNU Bash Shell Parameter Expansion]
  **Confidence: 96/100.**

- Resolver drift is the main maintenance risk. Prevent it with one normalized
  candidate-order assertion across all four skills and the lifecycle hook,
  while allowing the direct-skill missing case to fail and the hook missing
  case to remain fail-open. [VERIFIED:
  plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh:98-109] **Confidence:
  96/100.**

## Sources

### Primary

- [Claude Code Plugins Reference](https://code.claude.com/docs/en/plugins-reference)
  - project/plugin root meanings, skill-content substitution, and plugin `bin/`
  behavior. **Confidence: MEDIUM (provider-classified), 95/100.**

- [GNU Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html)
  - `$0`, quoting, conditional expressions, and shell execution behavior.
  **Confidence: MEDIUM (provider-classified), 94/100.**

- [GNU Bash Shell Parameter Expansion](https://www.gnu.org/software/bash/manual/html_node/Shell-Parameter-Expansion.html)
  - `${parameter:-word}` unset-or-null semantics. **Confidence: MEDIUM
  (provider-classified), 94/100.**

- [POSIX `test`](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/test.html)
  - regular-file predicate semantics. **Confidence: MEDIUM
  (provider-classified), 94/100.**

- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
  - current security-control verification guidance and OS-command-injection
  control. **Confidence: MEDIUM, 93/100.**

### Repository Evidence

- `plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh` - canonical precedence
  and lifecycle fail-open behavior.
- Four capability `SKILL.md` files - current direct command inventory.
- `plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py` and
  `.github/workflows/ci.yml` - existing isolated stdlib test architecture and
  full-suite command.
