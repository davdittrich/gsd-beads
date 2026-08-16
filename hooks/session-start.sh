#!/usr/bin/env bash
# D-02/D-09: self-heal .beads/PRIME.md from the shipped source before bd prime reads it.
set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SOURCE="$PLUGIN_ROOT/.agents/skills/beads/PRIME.md"
DEST=".beads/PRIME.md"

if [ -d ".beads" ] && [ ! -e "$DEST" ] && [ -f "$SOURCE" ]; then
  cp "$SOURCE" "$DEST" 2>/dev/null || true
fi

exec bd prime --hook-json
