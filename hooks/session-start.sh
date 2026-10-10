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
if [ -d ".beads" ] && [ ! -e "$DEST" ] && [ ! -L "$DEST" ] && [ -f "$SOURCE" ]; then
  cp "$SOURCE" "$DEST" 2>/dev/null || true
fi

bash "$PLUGIN_ROOT/hooks/capability-auto-install.sh" beads || true

exec bd prime --hook-json
