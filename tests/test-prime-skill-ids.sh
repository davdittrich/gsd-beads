#!/usr/bin/env bash
# Every skill id in PRIME.md's "Sync points" table must be invocable. The Skill tool
# resolves a skill only by its SKILL.md `name:` (gsd-beads-*); a bare directory
# name like `beads-sync` fails with "Unknown skill" (#23).
set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PRIME="$REPO_ROOT/.agents/skills/beads/PRIME.md"

# Skill column (2nd) of the table rows under "## Sync points", backticks stripped.
ids="$(awk -F'|' '/^## /{t=($0=="## Sync points"); next} t && /^\| `/{gsub(/[ `]/,"",$3); print $3}' "$PRIME" | sort -u)"
[ -n "$ids" ] || { echo "FAIL: no skill ids parsed from $PRIME"; exit 1; }

rc=0
for id in $ids; do
  if grep -qx "name: $id" "$REPO_ROOT"/skills/*/SKILL.md; then echo "PASS: $id"
  else echo "FAIL: '$id' matches no skills/*/SKILL.md 'name:'; Skill tool returns Unknown skill"; rc=1; fi
done
exit "$rc"
