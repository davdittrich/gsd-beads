---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-08-15T13:15:33.240Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | unrun-verify | .gsd/capabilities/beads/capability.json |  | Task 3 'Live trace' acceptance criterion (grep a real planner Agent() prompt for the recall-pointer.md fragment) not exercised in execute-plan; recorded as SUMMARY coverage.D6 with human_judgment true | open |  | 2026-08-15T13:15:33.240Z |  |

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
  }
]
````
