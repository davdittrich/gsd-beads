---
phase: 10
reviewers: [antigravity]
reviewed_at: 2026-08-16T23:22:56Z
plans_reviewed: [10-01-PLAN.md, 10-02-PLAN.md]
---

# Cross-AI Plan Review — Phase 10

## Antigravity Review

# Plan Review: Phase 10 — `ponytail-everywhere` Capability Plugin

## 1. Summary

The implementation plans (`10-01-PLAN.md` and `10-02-PLAN.md`) establish a well-structured, two-tier architecture for delivering lazy-ladder discipline reminders across the `gsd-core` workflow without patching core files (`D-01`, `D-02`). Plan 10-01 packages the `ponytail-everywhere` Claude Code plugin with `SessionStart` and role-matched `SubagentStart` hooks (`gsd-planner`, `gsd-executor`, `gsd-verifier`) to solve subagent context isolation, while Plan 10-02 defines the `.gsd/capabilities/ponytail/` capability bundle with a live prompt contribution at `plan:pre` and forward-compatible declarations at execution and verification phases. The plans are grounded in verified repository patterns (matching `.claude-plugin/marketplace.json:8-14`, `hooks/hooks.json:1-16`, and `.gsd/capabilities/beads/capability.json:141-155`), enforce rigorous fail-open execution, and mandate a blocking human consent checkpoint for project-level capability installation.

---

## 2. Strengths

* **Layered Reach Architecture without Core Patches (10-01-PLAN.md:1100-1108):** Accurately accounts for the fact that `SessionStart` context does not propagate to Task-spawned subagents by pairing it with role-matched `SubagentStart` hooks (`matcher: "gsd-planner|gsd-executor|gsd-verifier"`), ensuring coverage for subagents without mutating `gsd-core` workflow scripts.
* **Architectural Honesty and Forward-Compatibility (10-02-PLAN.md:1437-1442):** Plan 10-02 transparently acknowledges that only `plan:pre` currently performs functional prompt injection in `gsd-core 1.10.0`, while explicitly documenting in `NOTES.md` that `execute:wave:pre` and `verify:pre` entries are forward-compatible declarations backed by `SubagentStart` hooks at runtime.
* **Adherence to Repository Structural Precedents:**
  * Reuses plugin identity structure (`.claude-plugin/plugin.json:5-9`) and marketplace extension format (`.claude-plugin/marketplace.json:8-14`).
  * Follows the `PLUGIN_ROOT` fallback pattern from `hooks/session-start.sh:5`.
  * Conforms to manifest field requirements and fail-open `onError: "skip"` patterns demonstrated in `.gsd/capabilities/beads/capability.json:141-155`.
* **Defensive Shell Scripting & Security Hygiene (10-01-PLAN.md:1345-1350):** Restricts `ponytail.level` and `ROLE` inputs against explicit whitelist cases (`case "$LEVEL" in lite|full|ultra)...`), unquotes JSON output via `tr -d '"'`, omits `set -e` to avoid crashing agent sessions, and uses single-quoted heredocs to prevent accidental shell interpolation.
* **Strict Consent Gate (10-02-PLAN.md:1578-1609):** Treats capability installation as an instruction surface boundary change (T-10-03) requiring explicit user consent via a blocking checkpoint before running `capability install --scope project`.

---

## 3. Concerns

* **[MEDIUM] Inconsistent CLI Discovery across Test Runner and Hook Scripts:**
  * *Location:* `ponytail-everywhere/hooks/session-start.sh` vs `10-02-PLAN.md:1646`
  * *Mechanism:* Plan 10-01 Task 1 explicitly notes `gsd-tools` is not on `$PATH` and implements a 3-step fallback resolution for `session-start.sh` (`./gsd-core/bin/gsd-tools.cjs`, `command -v gsd-tools`, `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs`). However, `10-02-PLAN.md:1646` directly invokes `GT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs"`. If a developer or CI environment uses a repo-local or npm-global installation where `$HOME/.claude` is absent or different, automated verification commands in Plan 10-02 will fail despite `session-start.sh` succeeding.
* **[LOW] Fragility of `test-session-start.sh` Config Manipulation during Concurrent Workflows:**
  * *Location:* `10-01-PLAN.md:1305-1312` and `10-02-PLAN.md:1629-1632`
  * *Mechanism:* Both test tasks mutate the primary project file `.planning/config.json` directly in place and rely on `trap ... EXIT` to restore backups. While `trap` handles script terminations, an abrupt process SIGKILL or interrupted subagent execution could leave `.planning/config.json` modified or missing, inadvertently toggling repository-wide workflow flags (e.g., `.planning/config.json:48-51`).
* **[LOW] Absence of `CLAUDE_PLUGIN_ROOT` in Standalone Hook Execution during Test:**
  * *Location:* `ponytail-everywhere/hooks/hooks.json` (10-01-PLAN.md:1191-1193) vs `test-session-start.sh`
  * *Mechanism:* When invoked via Claude Code, `${CLAUDE_PLUGIN_ROOT}` is set by the plugin runtime. When `test-session-start.sh` directly invokes `bash ponytail-everywhere/hooks/session-start.sh`, `${CLAUDE_PLUGIN_ROOT}` is unset. The script's fallback `PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"` handles this correctly, but verifying the hook definition from `hooks.json` via simulated execution should ensure `CLAUDE_PLUGIN_ROOT` expansion works as expected.

---

## 4. Suggestions

* **Standardize `GSD_TOOLS` Helper Path across All Test Commands:**
  * In `10-02-PLAN.md` Task 2 & Task 3 verification blocks, adopt the same resolution chain as Plan 10-01:
    ```bash
    GT="$(command -v gsd-tools || echo "gsd-core/bin/gsd-tools.cjs")"
    [ -f "$GT" ] || GT="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs"
    ```
* **Use an Isolated Mock Config for Test Runs where Possible:**
  * Instead of modifying `.planning/config.json` in the live repository tree, test scripts can pass an isolated directory context (e.g., `GSD_CONFIG_DIR` or a temporary working directory sandbox) when exercising `config-get` / `config-set` behavior, eliminating any blast radius on repo-level planning state.
* **Include a Verification for `marketplace.json` Schema Integrity:**
  * Ensure `test-session-start.sh` or the plan verify block includes `claude plugin validate . --strict` from root to assert that both plugins (`beads-lifecycle` and `ponytail-everywhere`) validate simultaneously within `.claude-plugin/marketplace.json`.

---

## 5. Risk Assessment

* **Overall Risk Level: LOW**
* **Justification:**
  * The implementation is completely additive and decoupled from existing core logic.
  * No core files or workflows are patched.
  * The hook scripts and capability definitions are strictly advisory and fail-open (`onError: "skip"`, `exit 0` on error/disable, empty `gates: []`).
  * Input parsing is rigorously sanitized against shell injection attacks.
  * Reversibility is 100% via standard git reverts.

---

## Consensus Summary

Single reviewer this run (antigravity) — no cross-reviewer consensus to synthesize. Its verdict: LOW overall risk, no blockers, one MEDIUM concern (inconsistent `gsd-tools` path resolution between `session-start.sh`'s 3-step fallback and Plan 10-02's test commands, which hardcode the `$HOME/.claude` branch only).

### Agreed Strengths
N/A — single reviewer.

### Agreed Concerns
N/A — single reviewer. See antigravity's Concerns section above for the full list (1 MEDIUM, 2 LOW).

### Divergent Views
N/A — single reviewer.
