---
phase: 10-ponytail-everywhere-capability-plugin-advisory-only-ladder-d
reviewed: 2026-08-17T00:45:02Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - .claude-plugin/marketplace.json
  - .gsd-capabilities.json
  - .gsd/capabilities/ponytail/NOTES.md
  - .gsd/capabilities/ponytail/capability.json
  - .gsd/capabilities/ponytail/fragments/executor-ladder.md
  - .gsd/capabilities/ponytail/fragments/planner-ladder.md
  - .gsd/capabilities/ponytail/fragments/verifier-ladder.md
  - ponytail-everywhere/.claude-plugin/plugin.json
  - ponytail-everywhere/hooks/gsd-tools.sh
  - ponytail-everywhere/hooks/hooks.json
  - ponytail-everywhere/hooks/session-start.sh
  - ponytail-everywhere/tests/test-session-start.sh
findings:
  critical: 1
  warning: 2
  info: 3
  total: 6
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-08-17T00:45:02Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Reviewed the ponytail capability (gsd-core contribution mechanism) and the sibling
`ponytail-everywhere` Claude Code plugin (SessionStart/SubagentStart hooks). The JSON
manifests (`marketplace.json`, `.gsd-capabilities.json`, `capability.json`, `plugin.json`,
`hooks.json`) are internally consistent, schema-plausible, and match the design intent
recorded in `NOTES.md`. The prose fragments contain no injection vectors. `test-session-start.sh`
was executed live in this environment and all 10 cases genuinely pass against the real
`gsd-tools.cjs` binary (not a hollow/false-positive pass — confirmed by tracing which
resolution branch of `gsd_tools()` fires in this sandbox).

The one load-bearing defect is in `ponytail-everywhere/hooks/gsd-tools.sh`: the resolver
builds a `node <path>` command as a single unquoted string and invokes it unquoted. This is
empirically broken (reproduced below) whenever the resolved path — the git repo root, or the
`CLAUDE_CONFIG_DIR`/`$HOME` fallback — contains a space, which is a realistic real-world
condition (usernames/company drive mounts with spaces, e.g. `/home/john doe/.claude`, WSL
mounts under `/mnt/c/Users/...`). The failure is silent: `node` crashes with `MODULE_NOT_FOUND`,
stderr is discarded, and the caller's `|| echo true` / `|| echo full` fallback masks it —
meaning an explicit `ponytail.enabled: false` in the user's own project config silently stops
taking effect and the banner reappears regardless of what the user configured.

## Critical Issues

### CR-01: Unquoted multi-word command variable breaks `gsd_tools()` and silently overrides an explicit `ponytail.enabled: false` whenever the resolved path contains a space

**File:** `ponytail-everywhere/hooks/gsd-tools.sh:6,9-10,16`
**Issue:**

```sh
6:       _GSD_TOOLS_CMD="node $_root/gsd-core/bin/gsd-tools.cjs"
...
9:     elif [ -f "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs" ]; then
10:       _GSD_TOOLS_CMD="node ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs"
...
16:   $_GSD_TOOLS_CMD "$@"
```

`_GSD_TOOLS_CMD` stores `"node <path>"` as one string, then is expanded unquoted at line 16
to split it back into `node` + `<path>` as separate argv words. This relies on IFS
word-splitting: if `<path>` (the git toplevel, or `${CLAUDE_CONFIG_DIR:-$HOME/.claude}`)
contains a space, the path itself is split into multiple bogus argv words and `node` is
invoked with a truncated/garbage module path.

Reproduced empirically in this sandbox: with a git repo whose toplevel is
`.../gsd test space2` and a real `gsd-core/bin/gsd-tools.cjs` inside it, `gsd_tools config-get
ponytail.enabled --default true` fails with:

```
node:internal/modules/cjs/loader:1573
Error: Cannot find module '.../gsd'
    ...
exit code: 1
```

(`node` receives `.../gsd` as its entry-point argument because ` test space2` word-split off.)

In `session-start.sh:8-9` this failure's stderr is discarded (`2>/dev/null`) and its non-zero
exit triggers `|| echo true` / `|| echo full`, so the hook does not crash or error visibly —
it silently behaves as if `ponytail.enabled` were `true` and `ponytail.level` were `full`,
**even when the user's real `.planning/config.json` explicitly sets `ponytail.enabled: false`**.
The toggle this capability exists to provide (D-03's `ponytail.enabled`) is defeated with no
error surfaced to the user, for any project whose repo root, or whose `$HOME`/
`CLAUDE_CONFIG_DIR`, contains a space. This is not a hypothetical edge case — corporate/WSL
home directories with spaces are common, and the failure is 100% reproducible and silent
under that condition.

**Fix:** Store the resolved command as a bash array, not a joined string, and expand it with
`"${arr[@]}"`:

```sh
gsd_tools() {
  if [ -z "${_GSD_TOOLS_CMD_SET+x}" ]; then
    _GSD_TOOLS_CMD_SET=1
    local _root
    _root="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [ -n "$_root" ] && [ -f "$_root/gsd-core/bin/gsd-tools.cjs" ]; then
      _GSD_TOOLS_ARGS=(node "$_root/gsd-core/bin/gsd-tools.cjs")
    elif command -v gsd-tools >/dev/null 2>&1; then
      _GSD_TOOLS_ARGS=(gsd-tools)
    elif [ -f "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs" ]; then
      _GSD_TOOLS_ARGS=(node "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs")
    else
      _GSD_TOOLS_ARGS=()
    fi
  fi
  [ "${#_GSD_TOOLS_ARGS[@]}" -gt 0 ] || return 127
  "${_GSD_TOOLS_ARGS[@]}" "$@"
}
```

Add a regression case to `tests/test-session-start.sh` that runs `mk_scratch` under a
`mktemp -d --suffix=' space'`-style directory (or equivalently sets `CLAUDE_CONFIG_DIR` to a
path containing a space) with `enabled: false` and asserts the hook still exits silently —
today's 10 cases give this bug zero coverage.

## Warnings

### WR-01: `gsd_tools`/`config-get` fail-open masks *any* upstream error, not just a missing key — an unrelated failure silently re-enables the capability

**File:** `ponytail-everywhere/hooks/session-start.sh:8-9`
**Issue:**

```sh
8:   ENABLED="$(gsd_tools config-get ponytail.enabled --default true 2>/dev/null || echo true)"
9:   LEVEL="$(gsd_tools config-get ponytail.level --default full 2>/dev/null || echo full)"
```

`--default true`/`--default full` is presumably `gsd_tools config-get`'s own mechanism for
defaulting when the config key is *absent*. The `|| echo true` / `|| echo full` here is a
second, independent fail-open layer that fires on *any* non-zero exit from `gsd_tools` —
binary not found (127, per CR-01), a corrupt/unparsable `.planning/config.json`, a `node`
crash, a permissions error, etc. In every one of those cases the script assumes
`ponytail.enabled: true` and `ponytail.level: full`, even if the real config on disk says
`ponytail.enabled: false`. Because this is advisory-only (no gate), the blast radius is
"an unwanted banner appears," not data loss — but it is a silent config-bypass with no
diagnostic, and it is what makes CR-01 fail closed-to-the-user's-preference rather than just
erroring loudly.

**Fix:** At minimum, only fall back to the hardcoded default when `gsd_tools` itself is
unavailable (`return 127`), and let a real config-parse failure surface (or explicitly log
to stderr, even if hook stdout must stay clean) rather than being conflated with "key absent."

### WR-02: Unguarded `cd` in test harness risks assertions silently running against the real repo instead of the scratch dir

**File:** `ponytail-everywhere/tests/test-session-start.sh:28,34`
**Issue:** `mk_scratch()` (line 28: `cd "$SCRATCH"`) and `run_and_cleanup()` (line 34:
`cd "$REPO_ROOT"`) do not check `cd`'s exit status (shellcheck SC2164). The file's own header
comment states the explicit design intent: "this repo's own project config is never written
to." If `cd "$SCRATCH"` ever fails (permissions, a `mktemp` on a filesystem the shell can't
enter, etc.), every subsequent command in that test case — including the invocation of
`session-start.sh` under test — silently runs from whatever the previous working directory
was, which could be this repo's own root, defeating the stated isolation guarantee and
producing a false pass/fail against the wrong config file.
**Fix:**
```sh
cd "$SCRATCH" || { echo "FAIL: cd to scratch dir failed"; exit 1; }
...
cd "$REPO_ROOT" || { echo "FAIL: cd back to repo root failed"; exit 1; }
```

## Info

### IN-01: `gsd-tools.sh` has no shebang or shell directive

**File:** `ponytail-everywhere/hooks/gsd-tools.sh:1`
**Issue:** The file is meant to be `.`-sourced (never executed directly), but lacks both a
shebang and a `# shellcheck shell=bash` directive, so static analysis tools (shellcheck: `SC2148`)
and editors can't determine the target shell from the file alone.
**Fix:** Add a leading comment such as `# shellcheck shell=bash` (or `#!/usr/bin/env bash` —
harmless even though the file is sourced, not executed) to make the intended shell explicit.

### IN-02: Ladder-discipline copy is duplicated between `fragments/*.md` and `session-start.sh`'s inline strings

**File:** `.gsd/capabilities/ponytail/fragments/{planner,executor,verifier}-ladder.md`,
`ponytail-everywhere/hooks/session-start.sh:33-55`
**Issue:** The two delivery mechanisms (gsd-core capability contribution vs. the Claude Code
plugin's `SubagentStart` hook) each carry their own independently authored copy of the same
7-rung ladder and the same "never simplify away" floor list. They are already worded
differently today (prose paragraphs in the fragments vs. an enumerated list plus a `lite`/`full`/
`ultra` `case` in the script), so a future change to the ladder's wording/rungs requires
remembering to update both, with no single source of truth and no test tying them together.
**Fix:** Not urgent given the advisory-only nature and current small size, but worth a
one-line pointer comment in each file noting the sibling copy exists, or a shared source file
generated into both at build/install time if the two ever need to converge in future work.

### IN-03: `.gsd-capabilities.json`'s `integrity` field is an empty string

**File:** `.gsd-capabilities.json:9`
**Issue:** `"integrity": ""` — the consent record's content-integrity hash is empty. This file
is generated by the external `capability install` tool (not authored by hand in this phase),
so this may simply be that tool's current behavior for locally-sourced (non-registry)
capabilities, in which case this is a non-issue. Flagging at low confidence because an empty
integrity value, if `gsd-core`'s loader ever treats empty-string as "skip verification" rather
than "fail closed," would mean the capability's whole-bundle re-consent invariant that
`NOTES.md` documents ("editing any file here ... silently deactivates the capability until
`capability install` is re-run") isn't actually enforced by a real hash — worth a one-line
confirmation from whoever owns `capability install`'s implementation, no action needed in
these files if it's confirmed expected.

---

_Reviewed: 2026-08-17T00:45:02Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
