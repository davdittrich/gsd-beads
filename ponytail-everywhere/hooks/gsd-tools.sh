gsd_tools() {
  if [ -z "${_GSD_TOOLS_CMD+x}" ]; then
    local _root
    _root="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [ -n "$_root" ] && [ -f "$_root/gsd-core/bin/gsd-tools.cjs" ]; then
      _GSD_TOOLS_CMD="node $_root/gsd-core/bin/gsd-tools.cjs"
    elif command -v gsd-tools >/dev/null 2>&1; then
      _GSD_TOOLS_CMD="gsd-tools"
    elif [ -f "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs" ]; then
      _GSD_TOOLS_CMD="node ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gsd-core/bin/gsd-tools.cjs"
    else
      _GSD_TOOLS_CMD=""
    fi
  fi
  [ -n "$_GSD_TOOLS_CMD" ] || return 127
  $_GSD_TOOLS_CMD "$@"
}
