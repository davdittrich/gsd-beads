# Worktrees

> Adapted from the upstream `beads` skill (MIT License, gastownhall/beads).

`bd worktree` is a convenience wrapper around Git worktrees, first-class since bd v0.40+.

## When is a worktree worth it

| Scenario | Worktree? | Why |
|---|---|---|
| A single wave of gsd executors sharing one checkout | No | Sequential/inline executors share the main working tree already; adding worktrees adds isolation you don't need |
| Parallel gsd executors in the same wave (`workflow.use_worktrees: true`) | Yes | Each executor needs an isolated working directory to commit without stepping on siblings |
| Long-running side branch outside the current phase | Yes | Avoids the stash/switch dance for interruptions |
| Quick branch switch on the same checkout | No | `git switch` is simpler |

## Creating and removing

```bash
# bd's convenience command — creates the Git worktree and adds an in-repo
# path to .gitignore automatically.
bd worktree create .worktrees/{name} --branch feature/{name}
bd worktree remove .worktrees/{name}

# Plain Git commands work identically; bd only adds the .gitignore step.
git worktree add -b feature/{name} .worktrees/{name}
git worktree remove .worktrees/{name}
```

`bd worktree remove` refuses to remove a worktree with uncommitted changes or unpushed commits unless forced.

## Architecture — worktrees share one `.beads/`

By default, every linked worktree shares the main repository's `.beads/` workspace through Git's common-directory discovery. There is no per-worktree redirect file to manage:

```
main-repo/
├── .git/        ← shared Git directory
├── .beads/      ← shared beads config and local Dolt data
└── .worktrees/
    ├── feature-a/
    └── feature-b/
```

`bd` resolves the effective workspace the same way from every linked worktree. Set `BEADS_DIR` on a specific worktree to point it at a beads workspace outside the tree entirely, or give a worktree its own `.beads/` explicitly — otherwise discovery falls back to the shared workspace.

## Protected branches need no special handling

Issue data lives in Dolt under `refs/dolt/data`, entirely separate from code branches, so protected Git branches impose no beads-specific constraint:

```bash
bd init                  # standard setup, or:
bd init --contributor    # OSS fork setup with contributor routing

bd dolt pull              # pull shared issue data
bd dolt push               # push shared issue data
```

Keep using normal Git feature branches and worktrees for code; beads' sync model does not care which branch you're on.

## Debugging

```bash
bd where          # effective .beads workspace location for the current worktree
bd doctor --deep  # validates full graph integrity
```

## gsd-core framing

The orchestrator creates a worktree per parallel executor when `workflow.use_worktrees: true` and a wave has 2+ agents whose plans don't share a modified file. If the repo the executor is dispatched into is itself nested inside a parent Git repository, worktree creation can resolve against the wrong repository root — verify `git rev-parse --show-toplevel` inside a freshly created worktree names the project repo, not its parent, before trusting isolated dispatch in a nested-repo layout. See TROUBLESHOOTING.md.
