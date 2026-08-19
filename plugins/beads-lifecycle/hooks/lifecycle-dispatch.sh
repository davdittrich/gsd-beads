#!/usr/bin/env bash
# gh-2: dispatch this capability's lifecycle steps from a PostToolUse hook.
#
# capability.json declares six `kind: "step"` hooks. gsd-core 1.10.0 reaches
# exactly one of them (`ship:pre`, and only because GSD-CORE-PATCH.md patches
# the dispatch loop in). At the other five it renders the hook JSON and then
# discards every `kind: "step"` entry: `plan:post` and `execute:wave:post`
# dispatch gates only, `execute:wave:pre` checks solely for a contribution,
# `verify:post` hardcodes `ref.skill == "secure-phase"`, and `plan:pre`'s
# generic step contract sits behind an AUTO_CHAIN + frontend-detection branch.
# Every hook is `onError: "skip"`, so the miss is silent -- a phase plans and
# executes with zero bd issues and nothing anywhere reports it.
#
# What gsd-core still does at all five points is run
# `gsd_run loop render-hooks <point> --raw`. This hook matches that Bash call
# and runs the operation itself. That is the whole design: the trigger is a
# call gsd-core must keep making for its own hook system to work at all, so a
# gsd-core update cannot silently strip it the way it can strip a patch.
#
# Never aborts the session: no `set -e`, and every exit is 0. PostToolUse
# cannot block a tool call in any case -- the tool has already run.
set -u

PAYLOAD="$(cat)"

# Extract the lifecycle point in one python3 call -- python3 is already this
# capability's hard dependency (sync.py), whereas jq is not.
#
# Matching is on `render-hooks <point>` as a whole token rather than on the
# full `gsd_run loop render-hooks ... --raw` line, so it survives the shim
# resolving to `gsd-tools` or `node .../gsd-tools.cjs` instead of the
# `gsd_run` shell function. A command that merely *mentions* the string (a
# grep while debugging, say) is a false positive, and an accepted one: every
# operation below is idempotent, so a spurious run costs a few bd queries and
# changes nothing.
#
# `ship:pre` is deliberately not matched -- it already dispatches through this
# capability's ship.md patch, and matching it here would double-record a
# ship_override.
POINT="$(printf '%s' "$PAYLOAD" | python3 -c '
import json, re, sys

POINTS = ("plan:pre", "plan:post", "execute:wave:pre", "execute:wave:post", "verify:post")
try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, UnicodeDecodeError):
    sys.exit(0)
if not isinstance(payload, dict):
    sys.exit(0)
tool_input = payload.get("tool_input")
command = tool_input.get("command") if isinstance(tool_input, dict) else None
if not isinstance(command, str):
    sys.exit(0)
for point in POINTS:
    if re.search(r"render-hooks\s+" + re.escape(point) + r"(?!\S)", command):
        print(point)
        break
' 2>/dev/null)"

[ -n "$POINT" ] || exit 0

# Defense in depth (ASVS V5), matching capability-auto-install.sh's CAP_ID
# guard: re-validate against the literal allowlist before the value reaches an
# argv list, rather than trusting the extractor above to be the only writer.
case "$POINT" in
  plan:pre|plan:post|execute:wave:pre|execute:wave:post|verify:post) ;;
  *) exit 0 ;;
esac

# Run from the project the tool call ran in -- sync.py resolves both the
# project root and the current phase by walking up from its own cwd.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$PROJECT_DIR" ]; then
  PROJECT_DIR="$(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
try:
    payload = json.load(sys.stdin)
except (json.JSONDecodeError, UnicodeDecodeError):
    sys.exit(0)
cwd = payload.get("cwd") if isinstance(payload, dict) else None
if isinstance(cwd, str):
    print(cwd)
' 2>/dev/null)"
fi
[ -n "$PROJECT_DIR" ] || PROJECT_DIR="$PWD"
[ -d "$PROJECT_DIR/.planning" ] || exit 0
cd "$PROJECT_DIR" || exit 0

# gsd-core's own capability resolution order: a project-scope install wins over
# a global one, so a project pinning an older bundle keeps getting that bundle's
# behavior. The plugin's own tree is the last resort, for a machine where the
# capability was never installed but the plugin is loaded.
SYNC_PY=""
for candidate in \
  "$PROJECT_DIR/.gsd/capabilities/beads/scripts/sync.py" \
  "${GSD_HOME:-$HOME}/.gsd/capabilities/beads/scripts/sync.py" \
  "${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}/.gsd/capabilities/beads/scripts/sync.py"
do
  if [ -f "$candidate" ]; then SYNC_PY="$candidate"; break; fi
done
[ -n "$SYNC_PY" ] || exit 0

# sync.py bounds every bd subprocess itself (BD_TIMEOUT), and always exits 0 --
# the `onError: "skip"` contract every one of these hooks declares.
#
# Only stdout is captured. sync.py routes its benign dispatch-level skips
# ("no phase directory resolved", "no PLAN.md in ...") to stderr precisely so
# they stay out of the promotion below: a repository between milestones has no
# `.planning/phases/` at all, and those skips would otherwise fire on every
# render-hooks call. Inherited stderr still reaches the hook debug log.
OUTPUT="$(python3 "$SYNC_PY" lifecycle-dispatch "$POINT")"

[ -n "$OUTPUT" ] || exit 0

# A PostToolUse hook's plain-text stdout on exit 0 reaches the debug log only
# -- Claude never sees it (only UserPromptSubmit, UserPromptExpansion and
# SessionStart promote plain stdout). `hookSpecificOutput.additionalContext` is
# the documented way to put text next to the tool result, which is exactly
# where it belongs here: `execute:wave:pre`'s <beads_status> block exists purely
# to reach the orchestrator composing the wave's executor prompts, and
# `plan:pre`'s patch-loss warnings are worthless in a log nobody reads.
#
# Emitted through python3 rather than printf so the payload is JSON-escaped
# rather than hand-quoted, and so stdout carries the object and nothing else --
# Claude Code parses stdout as JSON only when its first non-whitespace
# character is `{`, and any stray line breaks that. Exit stays 0: this hook
# reports, it never blocks (PostToolUse cannot block regardless, the tool has
# already run).
POINT="$POINT" OUTPUT="$OUTPUT" python3 -c '
import json, os

# 10,000 characters is the documented cap on a hook output string; anything
# past it is spilled to a file and replaced with a preview, which would split
# a <beads_status> block in half. Truncate here instead, visibly.
LIMIT = 9000
body = os.environ["OUTPUT"]
if len(body) > LIMIT:
    body = body[:LIMIT] + "\n[truncated -- see the phase BEADS.md for the full table]"
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "beads ({}):\n{}".format(os.environ["POINT"], body),
    }
}))
' || exit 0
exit 0
