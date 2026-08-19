#!/usr/bin/env bash
# gh-2: dispatch this capability's lifecycle steps from a PostToolUse hook.
#
# gsd-core 1.10.0 declares six `kind: "step"` hooks in capability.json and
# reaches exactly one (`ship:pre`, via GSD-CORE-PATCH.md). At the other five it
# renders the hook JSON and discards every step entry -- silently, since every
# hook is `onError: "skip"`. What it still does at all five is run
# `gsd_run loop render-hooks <point> --raw`, so this hook keys on that call and
# runs the operation itself. The trigger is one gsd-core must keep making for
# its own hook system to work, so a gsd-core update cannot strip it.
#
# Wired as `matcher: "Bash"`, so this runs after EVERY Bash tool call in every
# session, and the payload carries the tool's full output -- megabytes, at
# times. Hence the two-gate shape below: a locale-pinned builtin first, an
# interpreter only once that has passed.
#
# Never aborts the session: no `set -e`, and every exit is 0. PostToolUse
# cannot block a tool call in any case -- the tool has already run.
set -u

# Gate 1 (builtin, no spawn). Almost every Bash call has nothing to do with
# gsd-core; reject it before paying for an interpreter. Measured on the
# non-matching path: 13.0 ms/call when python decided, 0.9 ms/call here.
#
# LC_ALL=C is load-bearing, not hygiene: bash pattern matching decodes UTF-8,
# which costs ~34 ms on a 4 MB payload and ~0 in the C locale. It is safe
# because the literal is ASCII.
#
# Safe as a pre-filter only because it is strictly wider than gate 2 -- it
# scans the raw payload (a superset of the command) so it can only over-match,
# and gate 2 re-checks the decoded string.
export LC_ALL=C
PAYLOAD="$(cat)"
case "$PAYLOAD" in
  *render-hooks*) ;;
  *) exit 0 ;;
esac

# Gate 2: decode the JSON and require an actual gsd tools invocation, not a
# mention of one. Matching `render-hooks <point>` anywhere in the command was
# far too wide -- `rg "render-hooks plan:post --raw" .`, an unquoted grep, and
# an `echo` of the line all fired it, and a spurious `plan:post` is not free
# (it creates bd issues and closes orphans; see the `allow_strip` note in
# sync.py's `lifecycle_dispatch` for the part that used to be destructive).
#
# Three things must line up: the tools token in COMMAND POSITION (start of
# line, or after `;`/`&`/`|`/`(`/backtick -- so a quoted `echo` cannot reach
# it), the `loop` subcommand, and the trailing `--raw`. That still matches
# whichever shim resolved: the `gsd_run` shell function, a `gsd-tools` on
# PATH, or `node .../gsd-tools.cjs`.
#
# `ship:pre` is deliberately absent from POINTS -- it already dispatches
# through this capability's ship.md patch, and matching it here would
# double-record a ship_override.
#
# One python3 call extracts both fields; re-parsing the same payload for `cwd`
# would double the cost of the path that got this far.
read -r POINT PROJECT_DIR <<<"$(printf '%s' "$PAYLOAD" | python3 -c '
import json, re, sys

POINTS = ("plan:pre", "plan:post", "execute:wave:pre", "execute:wave:post", "verify:post")
COMMAND_POSITION = r"(?:^|[;&|(`\n])\s*"
# The `gsd_run` shell function, a `gsd-tools` resolved on PATH or by absolute
# path, or `node <path>/gsd-tools.cjs` -- the three shims the workflow preamble
# can resolve to. `\S*?` absorbs a leading path but cannot cross whitespace, so
# `echo gsd-tools loop ...` stays out of command position and is rejected.
TOOLS = r"(?:gsd_run|(?:node\s+)?\S*?gsd-tools(?:\.cjs)?)"
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
    # (?![-\w]) not (?!\S): the real call is `VAR=$(gsd_run ... --raw)`, so
    # `--raw` is followed by the closing paren of the substitution.
    pattern = (COMMAND_POSITION + TOOLS + r"\s+loop\s+render-hooks\s+"
               + re.escape(point) + r"\s+--raw(?![-\w])")
    if re.search(pattern, command):
        cwd = payload.get("cwd")
        print(point, cwd if isinstance(cwd, str) and cwd else "-")
        break
' 2>/dev/null)"

[ -n "${POINT:-}" ] || exit 0

# Run from the project the tool call ran in -- sync.py resolves both the
# project root and the current phase by walking up from its own cwd.
[ -n "${CLAUDE_PROJECT_DIR:-}" ] && PROJECT_DIR="$CLAUDE_PROJECT_DIR"
[ "${PROJECT_DIR:--}" != "-" ] || PROJECT_DIR="$PWD"
[ -d "$PROJECT_DIR/.planning" ] || exit 0
cd "$PROJECT_DIR" || exit 0

# gsd-core's own capability resolution order: project scope beats global, so a
# project pinning an older bundle keeps that bundle's behavior. The plugin's
# own tree is the last resort.
SYNC_PY=""
for candidate in \
  "$PROJECT_DIR/.gsd/capabilities/beads/scripts/sync.py" \
  "${GSD_HOME:-$HOME}/.gsd/capabilities/beads/scripts/sync.py" \
  "${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}/.gsd/capabilities/beads/scripts/sync.py"
do
  if [ -f "$candidate" ]; then SYNC_PY="$candidate"; break; fi
done
[ -n "$SYNC_PY" ] || exit 0

# Only stdout is captured. sync.py routes its benign dispatch-level skips to
# stderr so they stay out of the promotion below -- a repository between
# milestones has no `.planning/phases/` at all and would otherwise annotate
# every render-hooks call. Inherited stderr still reaches the hook debug log.
# sync.py bounds each bd subprocess itself (BD_TIMEOUT) and always exits 0.
OUTPUT="$(python3 "$SYNC_PY" lifecycle-dispatch "$POINT")"

[ -n "$OUTPUT" ] || exit 0

# A PostToolUse hook's plain stdout on exit 0 reaches the debug log only --
# Claude never sees it. `hookSpecificOutput.additionalContext` is the documented
# way to put text next to the tool result, which is where `execute:wave:pre`'s
# <beads_status> block has to land to reach the executor prompts it exists for.
# Emitted through python3 so the payload is JSON-escaped rather than
# hand-quoted, and so stdout carries the object and nothing else -- Claude Code
# parses stdout as JSON only when its first non-whitespace character is `{`.
POINT="$POINT" OUTPUT="$OUTPUT" python3 -c '
import json, os

# 10,000 characters is the documented cap on a hook output string; past it the
# text spills to a file and is replaced by a preview, which would cut a
# <beads_status> block in half. Truncate here instead, visibly.
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
