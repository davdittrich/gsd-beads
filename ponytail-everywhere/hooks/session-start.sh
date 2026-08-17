#!/usr/bin/env bash
set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

if [ -f "$PLUGIN_ROOT/hooks/gsd-tools.sh" ]; then
  . "$PLUGIN_ROOT/hooks/gsd-tools.sh"
  ENABLED="$(gsd_tools config-get ponytail.enabled --default true 2>/dev/null || echo true)"
  LEVEL="$(gsd_tools config-get ponytail.level --default full 2>/dev/null || echo full)"
else
  ENABLED=true
  LEVEL=full
fi
ENABLED="$(printf '%s' "$ENABLED" | tr -d '"')"
LEVEL="$(printf '%s' "$LEVEL" | tr -d '"')"

if [ "$ENABLED" != "true" ]; then
  exit 0
fi

case "$LEVEL" in
  lite|full|ultra) ;;
  *) LEVEL=full ;;
esac

cat <<'EOF'
PONYTAIL LADDER — advisory, not a gate (level: full)
1. Does this need to exist at all? YAGNI
2. Already in this codebase? Reuse it
3. Stdlib does it? Use it
4. Native platform feature covers it? Use it
5. Already-installed dependency solves it? Use it — never add one for what a few lines can do
6. Can it be one line? One line
7. Only then: the minimum code that works
Stop at the first rung that holds.
Never simplify away: input validation at trust boundaries, error handling that prevents data loss, security controls, accessibility basics, or anything explicitly requested.
EOF

exit 0
