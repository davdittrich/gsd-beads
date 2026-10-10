# Stealth / Git-Free Mode

> This skill otherwise adapts topics from the upstream `beads` skill (MIT License, gastownhall/beads), but upstream has no dedicated document for `--stealth`/`BEADS_DIR`. This file's content is original, sourced entirely from the live `bd init --help` and `bd prime --help` output (bd v1.2.2), not transcribed from any upstream doc.

`--stealth` is **two different flags on two different subcommands**, with two different effects. Do not conflate them.

## `bd init --stealth`

Configures per-repository git settings for invisible beads usage:

- Writes `.git/info/exclude` entries so beads files are never committed for this clone.
- Never affects other collaborators — it's local-only, per-repo config.
- Companion setup: `bd setup <claude|cursor|aider|...> --stealth` wires up the matching AI tool for the same invisible-usage pattern.

This is the choice when you want to use `bd` in a repository whose collaborators haven't adopted it, without ever proposing a beads-tracked file in a diff.

## `bd prime --stealth`

A single-invocation flag, unrelated to `bd init --stealth`: it suppresses git operations for that one `bd prime` run — no commit/flush side effects from priming context. It does not touch `.git/info/exclude` and has no lasting effect beyond the invocation.

Related: `bd config set no-git-ops true` makes `bd prime`'s session-close protocol output stay in stealth mode (no git commands suggested) for every future run, not just one invocation.

## `BEADS_DIR`

An environment variable pointing `bd` at a workspace entirely outside the current repository tree. Combine with `bd init` run from that external directory to keep issue data off-disk in the repo altogether — the strongest form of git-free operation, since there's no `.beads/` inside the repo to exclude in the first place.

## Choosing between them

| Goal | Use |
|---|---|
| Use `bd` in a shared repo without ever committing beads files | `bd init --stealth` |
| Suppress git side effects for one `bd prime` call | `bd prime --stealth` |
| Suppress git side effects for every future `bd prime` call | `bd config set no-git-ops true` |
| Keep issue data completely outside the repository | `BEADS_DIR` pointed at an external path |

## Setting up an AI tool for stealth use

```bash
bd init --stealth              # per-repo git-exclude config
bd setup claude --stealth      # wires Claude-specific integration the same way
bd setup cursor --stealth
bd setup aider --stealth
```

Each `bd setup <tool> --stealth` call follows the same invisible-usage pattern for that tool's own integration points, without requiring a separate manual config step per tool.

## gsd-core framing

This project does not run in stealth mode — `.beads/` is a normal, partially-tracked workspace here (see `.gitignore`'s beads stanzas). Stealth mode matters for a *downstream* install where a user adopts `bd` inside a repo they don't want beads-tracked-file noise in; gsd-core's own capability integration is agnostic to whether the underlying workspace is stealth or not.
