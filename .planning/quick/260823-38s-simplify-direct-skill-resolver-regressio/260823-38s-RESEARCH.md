---
quick_id: 260823-38s
date: 2026-08-23
status: complete
confidence: high
---

# Research: direct-skill resolver regression simplification and release

## Scope

GitHub issue #4 requests a test-only refactor. The four direct skill sources,
their resolver blocks, command suffixes, lifecycle dispatch, `sync.py`,
capability installation, dependencies, and production manifests remain
unchanged except the separately requested plugin release version bump.

## Findings

1. `TestDirectSkillSyncResolver` currently discovers generic Markdown Bash
   fences, maps them back to a ten-entry inventory, transforms five placeholder
   forms into executable Bash, and runs all copied resolvers for every selection
   boundary. The targeted baseline passes two tests in 0.742 seconds, while an
   intentional AST gate is red because `_direct_fences`, `_selected_fences`,
   `_derive`, and `_run_all` still exist.
2. Static source identity needs no Markdown interpreter. For each inventory
   entry, construct the exact expected fenced block from the canonical resolver
   and exact command lines, then require `text.count(block) == 1`. This directly
   proves ten expected fences, one canonical resolver per fence, and unchanged
   suffixes without executing copied source.
3. Dynamic checks have two independent contracts:
   - resolver selection/failure: run the canonical resolver once for each
     project, explicit global, unset HOME fallback, empty HOME fallback, plugin,
     and directory-rejection boundary;
   - argv: run one concrete command for each unique suffix shape, including
     `status` both with and without its optional phase argument.
   A two-field JSON spy (`__file__`, `sys.argv[1:]`) is minimal because the first
   field proves selection and the second proves argv.
4. The plugin manifest is `1.4.0`, while the latest GitHub Release is `v1.3.1`;
   the configured Claude Marketplace and installed `beads-lifecycle@gsd-beads`
   already resolve `1.4.0`. The user's explicit bump therefore means the patch
   version `1.4.1`.
5. Claude resolves a plugin version first from `plugin.json`, then from the
   marketplace entry, then from the source commit. Official guidance says an
   explicit manifest version must be bumped for installed users to receive an
   update and warns against declaring a second marketplace version because the
   manifest silently wins. Keep `marketplace.json` versionless and update it
   through the configured marketplace CLI after publication.

## Sources

- [GitHub issue #4 owner brief](https://github.com/davdittrich/gsd-beads/issues/4#issuecomment-5383322199)
- [Claude Code plugin marketplace version resolution](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude Code plugin manifest versioning](https://code.claude.com/docs/en/plugins-reference)
- [Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html)

## Recommendation

Use literal static fence equality plus table-driven canonical dynamic cases.
Patch-bump only `plugins/beads-lifecycle/.claude-plugin/plugin.json` to `1.4.1`.
After full-suite verification, fast-forward the isolated branch to
`origin/main`, publish only `v1.4.1`, wait for `release.yml`, update the
configured `gsd-beads` marketplace and installed plugin, then close issue #4.
