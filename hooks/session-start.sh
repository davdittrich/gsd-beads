#!/usr/bin/env bash
# D-02/D-09: self-heal .beads/PRIME.md from the shipped source before bd prime reads it.
set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SOURCE="$PLUGIN_ROOT/.agents/skills/beads/PRIME.md"
DEST=".beads/PRIME.md"

# Review finding: `[ ! -e "$DEST" ]` alone follows symlinks and is false for
# a dangling one, so a planted dangling symlink at $DEST used to pass this
# guard and reach `cp`. GNU coreutils' `cp` independently refuses to write
# through a dangling symlink by default (verified: not every `cp` does --
# BusyBox and some BSD `cp` builds do not), so `[ ! -L "$DEST" ]` here is
# portability defense-in-depth, not the only thing standing between this
# guard and a write-through on every platform this hook might run on.
if [ -d ".beads" ] && [ ! -L ".beads" ] && [ ! -e "$DEST" ] && [ ! -L "$DEST" ] && [ -f "$SOURCE" ]; then
  cp "$SOURCE" "$DEST" 2>/dev/null || true
fi

# stdout is parsed as hook JSON; the installer's notices belong on stderr.
# Claude Code shows exit-0 hook stderr only in its debug log, so a consent
# request also goes out as systemMessage, which both runtimes show the user.
# The message tells the user to run the command themselves, never an agent.
{ INSTALL_ERR="$(bash "$PLUGIN_ROOT/hooks/capability-auto-install.sh" beads 2>&1 1>&3)"; } 3>&2
[ -z "$INSTALL_ERR" ] || printf '%s\n' "$INSTALL_ERR" >&2
CONSENT_COMMAND=""
while IFS= read -r _line; do
  case "$_line" in
    "capability-auto-install: beads needs your consent before install; run: "*) CONSENT_COMMAND="${_line#*; run: }" ;;
  esac
done <<<"$INSTALL_ERR"

if [ -z "$CONSENT_COMMAND" ]; then
  command -v bd >/dev/null 2>&1 || exit 0
  exec bd prime --hook-json
fi
PRIME_JSON='{}'
command -v bd >/dev/null 2>&1 && PRIME_JSON="$(bd prime --hook-json)"
printf '%s' "$PRIME_JSON" | python3 -I -c '
import json, sys
try:
    out = json.load(sys.stdin)
except ValueError:
    out = {}
if not isinstance(out, dict):
    out = {}
out["systemMessage"] = sys.argv[1]
print(json.dumps(out))
' "gsd-beads: the beads capability needs your consent before install. Run this yourself in a shell; an agent must not run it for you: $CONSENT_COMMAND"
