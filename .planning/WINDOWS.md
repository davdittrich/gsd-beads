---
schema_version: 1
open_count: 2
waived_count: 0
fixed_count: 0
total_count: 2
last_updated: 2026-08-15T13:30:43.719Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | unrun-verify | .gsd/capabilities/beads/capability.json |  | Task 3 'Live trace' acceptance criterion (grep a real planner Agent() prompt for the recall-pointer.md fragment) not exercised in execute-plan; recorded as SUMMARY coverage.D6 with human_judgment true | open |  | 2026-08-15T13:15:33.240Z |  |
| 2 | 02 | unrun-verify | .gsd/capabilities/beads/skills/beads-status/SKILL.md |  | B8's literal acceptance criterion (grep the real prompt= text an executor's Agent() call receives for this wave's issue ids) not exercised inside execute-plan -- a spawned executor subagent cannot dispatch a real execute-phase wave to inspect its own orchestrator's Agent() calls. Strengthened evidence recorded instead: capability re-installed/re-consented, render-hooks execute:wave:pre confirms the beads-status step is active, and a real (non-mocked) bd database round-trip (bd init, create-issues for a 2-plan wave sharing one epic, regenerate-beads-md, wave-status-block) produced the exact <beads_status> block text SKILL.md Step 2a instructs the orchestrator to paste into each executor's prompt=. See 02-02-SUMMARY.md coverage.D7. | open |  | 2026-08-15T13:30:43.719Z |  |

````json
[
  {
    "id": 1,
    "kind": "unrun-verify",
    "phase": "02",
    "file": ".gsd/capabilities/beads/capability.json",
    "line": null,
    "description": "Task 3 'Live trace' acceptance criterion (grep a real planner Agent() prompt for the recall-pointer.md fragment) not exercised in execute-plan; recorded as SUMMARY coverage.D6 with human_judgment true",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-15T13:15:33.240Z",
    "resolved_at": null
  },
  {
    "id": 2,
    "kind": "unrun-verify",
    "phase": "02",
    "file": ".gsd/capabilities/beads/skills/beads-status/SKILL.md",
    "line": null,
    "description": "B8's literal acceptance criterion (grep the real prompt= text an executor's Agent() call receives for this wave's issue ids) not exercised inside execute-plan -- a spawned executor subagent cannot dispatch a real execute-phase wave to inspect its own orchestrator's Agent() calls. Strengthened evidence recorded instead: capability re-installed/re-consented, render-hooks execute:wave:pre confirms the beads-status step is active, and a real (non-mocked) bd database round-trip (bd init, create-issues for a 2-plan wave sharing one epic, regenerate-beads-md, wave-status-block) produced the exact <beads_status> block text SKILL.md Step 2a instructs the orchestrator to paste into each executor's prompt=. See 02-02-SUMMARY.md coverage.D7.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-15T13:30:43.719Z",
    "resolved_at": null
  }
]
````
