---
name: gsd-pr-workflow-report
description: "Regenerates PR.md from a live gh PR/check status read for the current branch (execute:wave:post lifecycle dispatch)"
allowed-tools:
  - Read
  - Bash
---

**STOP -- DO NOT READ THIS FILE. You are already reading it. This prompt was injected into your context by the command system. Using the Read tool on this file wastes tokens. Begin executing Step 1 immediately.**

## Step 1 -- Config Gate

Check whether the pr-workflow capability is enabled by reading `.planning/config.json` directly
with the Read tool.

1. Read `.planning/config.json` with the Read tool.
2. If the file exists, `config["pr-workflow"]` is present, and
   `config["pr-workflow"]["enabled"]` is explicitly the boolean `false`: display the disabled
   message below and **STOP**.
3. Otherwise -- the file is missing, `config["pr-workflow"]` is absent, or it is present with no
   `enabled` key -- fall through to the shipped default (`pr-workflow.enabled: true` in
   `capability.json`) and proceed to Step 2.

**Disabled message:**

```
GSD > PR WORKFLOW REPORT

PR workflow reporting is disabled (pr-workflow.enabled).
Nothing was regenerated; the loop proceeds normally.
```

This step is `onError: skip` at its single dispatch point (`execute:wave:post`) -- no dispatch
ever fails a phase.

## Step 2 -- execute:wave:post: Regenerate PR.md

This skill has exactly one `capability.json` `steps[]` entry (`execute:wave:post`), so there is no
lifecycle-point branch to resolve -- unlike `beads-status`, which dispatches at four points.

Run one Bash call passing only the phase directory:

```bash
python3 .gsd/capabilities/pr-workflow/scripts/pr_status.py verify-post <phase directory>
```

Print `pr_status.py`'s stdout summary verbatim (`PR.md regenerated: pr_status=<state>` or
`PR.md regenerated: no open PR (pr_status=none)`).

## Anti-Patterns

1. DO NOT write `PR.md` at a project-root path (`.planning/PR.md`) -- the generic gate evaluator
   only resolves artifacts inside `phaseDir` (14-RESEARCH.md Pitfall 4). `pr_status.py verify-post`
   already writes the correct phase-scoped path; this skill must never override that with a
   different destination.
2. DO NOT re-run the config gate's check more than once per invocation, and DO NOT call any other
   `pr_status.py` subcommand from this dispatch point -- this dispatch point only regenerates the
   report.
