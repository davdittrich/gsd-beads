---
phase: 06-runtime-integration
verified: 2026-08-16T13:10:00Z
status: human_needed
score: 6/6 must-have truths verified
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Start one real interactive Claude Code session (TTY, not `claude -p`) inside this repo and confirm the beads context block appears exactly once."
    expected: "The beads SessionStart context (bd prime output) appears exactly once — no double-fire, no missing fire."
    why_human: "The plan's own acceptance criteria (Task 1) designate this as a required backstop distinct from the headless `-p --debug hooks` probes, specifically to catch any divergence between the headless and TTY code paths. A non-interactive agent (executor or verifier) cannot open a TTY session. SUMMARY.md explicitly documents this as unperformed and recommends it before treating Phase 6 as unconditionally closed."
---

# Phase 6: Runtime Integration Verification Report

**Phase Goal:** Installing the plugin gives a user the working capability and its session hook, without manual config
**Verified:** 2026-08-16
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A project that installs `beads@gsd-beads` gets a SessionStart hook running `bd prime --hook-json` with no user edit to `.claude/settings.json` | ✓ VERIFIED | `hooks/hooks.json` exists, canonically byte-equal (via `jq -S` diff) to the retired `.claude/settings.json` block at baseline `2b09c1b7`; `.claude/settings.json` absent from tree and index (`git ls-files` empty). Live re-run of `claude -p --debug hooks` with `beads@gsd-beads` installed at local scope shows `Read hooks.json for plugin beads` and exactly one `Hook SessionStart (bd prime --hook-json) provided additionalContext` line — independently reproduced by the verifier, not just cited from SUMMARY. |
| 2 | A session started inside gsd-beads itself fires `bd prime --hook-json` exactly once — never twice | ✓ VERIFIED | Same live probe above: fire count = 1 (not 0, not 2). `.claude/settings.json` confirmed absent, so there is no second registration source to double-fire from. |
| 3 | A session started with `bd` absent from PATH still completes successfully, emitting one non-blocking hook notice and zero `bd prime` context | ✓ VERIFIED | Independently rebuilt the PATH shim (4480 `/usr/bin` symlinks minus `bd`), re-ran `claude -p --debug hooks` under that PATH: process exit code 0, `grep -c` for the bd-prime success pattern = 0, and the debug log contains the exact line `Hook SessionStart:startup (SessionStart) error:\n/bin/sh: line 1: bd: command not found` — byte-for-byte the same notice SUMMARY.md transcribes verbatim. |
| 4 | From a project with no prior gsd-beads state, one written-down command makes gsd-core's capability loader report `beads` as installed and active | ✓ VERIFIED | Independently re-ran the documented bridge command (`gsd-tools.cjs capability install "$R/.gsd/capabilities/beads" --scope project --yes`) from a fresh, empty scratch directory outside the repo. Install returned `{"status":"installed","id":"beads",...}`; `capability state --raw` + `jq -e` confirmed `installed:true, active:true` for `beads`. |
| 5 | The bridge command is recorded verbatim, with its real observed output, so Phase 8's README can transcribe it | ✓ VERIFIED | 06-01-SUMMARY.md's "Verbatim Transcripts" section 1 carries the exact command (with clone-root correctly parameterized rather than hardcoded) and the exact `capability install`/`capability state --raw` JSON output, matching what the verifier's independent re-run produced. |
| 6 | `.gsd/capabilities/beads/` is bit-for-bit unchanged by this phase | ✓ VERIFIED | `git status --porcelain .gsd/capabilities/beads/` empty both before and after the verifier's independent re-run of the bridge command. |

**Score:** 6/6 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `hooks/hooks.json` | SessionStart block, canonically equal to `2b09c1b7fed7c4a89c1bbb8f38d889d792375fff:.claude/settings.json` | ✓ VERIFIED | `diff <(git show $BASE:.claude/settings.json | jq -S .) <(jq -S . hooks/hooks.json)` produces no output. Content: one `SessionStart` entry, `matcher: ""`, one `command`-type hook, `command: "bd prime --hook-json"`. No shell chaining, no PATH guard. |
| `.claude/settings.json` | absent from working tree and index | ✓ VERIFIED | `test ! -e` passes; `git ls-files .claude/settings.json` empty. |
| `.claude/settings.local.json` | untouched, unrelated `headroom` hook survives | ✓ VERIFIED | File present, content unchanged, carries its own `headroom` SessionStart hook plus `enabledPlugins.beads@gsd-beads: true` (local-scope install record — confirms the plugin is genuinely installed, not just claimed). |
| `.claude-plugin/plugin.json` | untouched, no `hooks` key added | ✓ VERIFIED | `git diff --exit-code $BASE -- .claude-plugin/plugin.json` exits 0; `jq 'has("hooks")'` returns `false`. |
| `.planning/PROJECT.md` | Key Decisions row for PUB-03 manual-bridge decision | ✓ VERIFIED | Line 140: full row present with the three-reason rationale and verified-command outcome. |
| `.planning/STATE.md` | Phase-6 open decision closed; PUB-04 allowlist gap opened for Phase 7/8 | ✓ VERIFIED | Line 102-105: "[Resolved 2026-08-16, Phase 6]" entry. Line 107-112: new Phase 7/8 entry naming the PUB-04 allowlist omission. |
| `.planning/phases/06-runtime-integration/06-01-SUMMARY.md` | verbatim transcripts of bridge command, fail-open notice, auto-load answer | ✓ VERIFIED | All three transcripts present and cross-checked against the verifier's own independent re-runs — content matches exactly. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `.claude-plugin/plugin.json` (no `hooks` key) | Claude Code's convention discovery of `hooks/hooks.json` | plugin install + session start | ✓ WIRED | Live probe with the plugin installed at local scope shows `Read hooks.json for plugin beads` in the debug log and the hook actually fires — convention discovery works without a manifest `hooks` key. |
| Claude Code plugin cache copy of `hooks/hooks.json` | the running session | plugin install | ✓ WIRED | Live probe reproduces exactly one fire; `claude plugin list` confirms `beads@gsd-beads` installed and enabled at local scope. |
| `capability install` spec path | `<spec>/capability.json` | CLI argument | ✓ WIRED | Independently re-ran with `"$R/.gsd/capabilities/beads"` as the spec — resolves and installs correctly; `.gsd/capabilities/beads/capability.json` confirmed to exist at that path. |
| this repo's own dev sessions | the locally installed plugin | local-scope install (post `.claude/settings.json` deletion) | ✓ WIRED | `claude plugin list` shows `beads@gsd-beads`, Scope: local, Status: enabled — the disclosed dependency the plan calls out is real and in effect. |
| `claude plugin validate . --strict` | `marketplace.json` presence | two-mode validate run | ✓ WIRED | Reproduced both runs live: with `marketplace.json` present, validator only inspects the marketplace manifest and passes clean; with it moved aside, validator inspects the plugin manifest and produces only the pre-accepted CLAUDE.md warning (D-10, Phase 5) — `grep -i hook` over both outputs matches nothing in either. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Plugin installed → hook fires exactly once | `claude -p --debug hooks --debug-file` with plugin at local scope | `Read hooks.json for plugin beads` + 1 fire | ✓ PASS |
| `bd` unreachable → fail-open | `claude -p --debug hooks` under a `bd`-free PATH shim | exit 0, 0 fires, verbatim notice captured | ✓ PASS |
| Clean project → capability bridge activates `beads` | `capability install ... --scope project --yes` + `capability state --raw` from fresh `/tmp` dir | `installed:true, active:true` | ✓ PASS |
| `claude plugin validate . --strict` (both modes) | run twice, marketplace.json present then absent | clean / one pre-accepted CLAUDE.md warning, no hook-related output | ✓ PASS |
| `.gsd/capabilities/beads/` untouched | `git status --porcelain` before/after bridge re-run | empty both times | ✓ PASS |

All five spot-checks were executed live by the verifier in this session (not merely cited from SUMMARY.md), reproducing the same pass/fail outcomes SUMMARY.md claims.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| PUB-03 | 06-01-PLAN.md | Capability-loader bridge explicitly decided and implemented (or manual alternative documented) | ✓ SATISFIED | Manual bridge command documented, independently re-executed successfully by the verifier from a clean project; PROJECT.md decision row records the three-reason rationale. |
| PUB-06 | 06-01-PLAN.md | `hooks/hooks.json` ships the SessionStart `bd prime` hook so plugin installers get it without manual config | ✓ SATISFIED | `hooks/hooks.json` ships canonically-equal content; `.claude/settings.json` retired; live probes confirm single fire when installed, zero fire without install, fail-open with `bd` absent. |

No orphaned requirements — REQUIREMENTS.md's traceability table maps exactly PUB-03 and PUB-06 to Phase 6, matching the PLAN frontmatter `requirements: [PUB-03, PUB-06]`.

### Anti-Patterns Found

None. `hooks/hooks.json` scanned for TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers — none found. No empty-return stubs, no hardcoded-empty props (the file is a static config artifact by design, not application logic).

### Code Review Findings (06-REVIEW.md)

One WARNING (WR-01, non-blocking): the commit message and 06-RESEARCH.md both claimed `hooks/hooks.json` is "byte-identical" to the retired `.claude/settings.json`, but a literal byte count differs by one trailing newline (218 bytes vs 217). The functional/acceptance-criteria check (`jq -S` canonical-JSON diff) is unaffected and passes — the verifier reproduced this canonical-diff match independently. This is a documentation-precision issue, not a functional gap: it does not affect hook firing, dedup, or any must-have truth. Not elevated to a gap.

### Human Verification Required

### 1. Interactive TTY session — single-fire backstop

**Test:** Start one real interactive Claude Code session (not `claude -p`) inside this repository and observe the session start.
**Expected:** The beads context block (from `bd prime --hook-json`) appears exactly once in the session's context — matching the headless-probe result of exactly one fire.
**Why human:** The plan's Task 1 explicitly designates this as a required backstop check distinct from the headless `-p --debug hooks` probes, specifically to catch any divergence between the headless and TTY code paths. A non-interactive verifier cannot open a TTY session. This is the only acceptance criterion neither the executor nor this verification could complete — SUMMARY.md itself flags it as outstanding and recommends running it "before `/gsd-verify-work` treats Phase 6 as fully closed."

### Gaps Summary

No gaps. All 6 must-have truths, all 7 required artifacts, and all 5 key links are verified — independently reproduced by the verifier via live command execution, not accepted on SUMMARY.md's word alone. The only open item is the plan's own explicitly-flagged TTY backstop check, which requires a human with an interactive terminal and is routed to human verification per the decision tree (a present-and-wired, behaviorally-strong result on the headless equivalent, but the specific acceptance criterion calling for a TTY session was not run by anyone, human or automated, before this report).

---

_Verified: 2026-08-16_
_Verifier: Claude (gsd-verifier)_
