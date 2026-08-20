---
schema_version: 1
open_count: 4
waived_count: 0
fixed_count: 0
total_count: 4
last_updated: 2026-08-20T11:02:41.000Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | unrun-verify | .gsd/capabilities/beads/capability.json |  | Task 3 'Live trace' acceptance criterion (grep a real planner Agent() prompt for the recall-pointer.md fragment) not exercised in execute-plan; recorded as SUMMARY coverage.D6 with human_judgment true | open |  | 2026-08-15T13:15:33.240Z |  |
| 2 | 02 | unrun-verify | .gsd/capabilities/beads/skills/beads-status/SKILL.md |  | B8's literal acceptance criterion (grep the real prompt= text an executor's Agent() call receives for this wave's issue ids) not exercised inside execute-plan -- a spawned executor subagent cannot dispatch a real execute-phase wave to inspect its own orchestrator's Agent() calls. Strengthened evidence recorded instead: capability re-installed/re-consented, render-hooks execute:wave:pre confirms the beads-status step is active, and a real (non-mocked) bd database round-trip (bd init, create-issues for a 2-plan wave sharing one epic, regenerate-beads-md, wave-status-block) produced the exact <beads_status> block text SKILL.md Step 2a instructs the orchestrator to paste into each executor's prompt=. See 02-02-SUMMARY.md coverage.D7. | open |  | 2026-08-15T13:30:43.719Z |  |
| 3 | 17 | deviation | plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py |  | Overlay-tree suite run (cd .gsd/capabilities/beads) hits 2 pre-existing, TRUTH-04-unrelated defects: TestLifecycleDispatchHook's PLUGIN_ROOT=parents[4] assumes plugin-tree nesting depth (wrong from a shallower overlay tree), and TestShipPreGenericDispatch's capability-reinstall side effect deletes the cwd the whole process is running from when invoked from inside .gsd/capabilities/beads. Both predate this plan (commits ecf9004d 2026-08-19, ddb7f894 2026-08-15). Runtime code proven identical via diff -rq (byte-for-byte) and the plugin-tree suite (180/180 OK). | open |  | 2026-08-19T23:57:18.564Z |  |
| 4 | 18 | unmet-truth | plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py |  | Overlay-tree suite run (.gsd/capabilities/beads/) fails 14/252 (PLUGIN_ROOT parents[4] resolves outside the vendored subtree) while the identical plugin-tree run is 252/OK and diff -rq is byte-silent; see gsd-beads-2e2. | open |  | 2026-08-20T11:02:41.000Z |  |

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
  },
  {
    "id": 3,
    "kind": "deviation",
    "phase": "17",
    "file": "plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py",
    "line": null,
    "description": "Overlay-tree suite run (cd .gsd/capabilities/beads) hits 2 pre-existing, TRUTH-04-unrelated defects: TestLifecycleDispatchHook's PLUGIN_ROOT=parents[4] assumes plugin-tree nesting depth (wrong from a shallower overlay tree), and TestShipPreGenericDispatch's capability-reinstall side effect deletes the cwd the whole process is running from when invoked from inside .gsd/capabilities/beads. Both predate this plan (commits ecf9004d 2026-08-19, ddb7f894 2026-08-15). Runtime code proven identical via diff -rq (byte-for-byte) and the plugin-tree suite (180/180 OK).",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-19T23:57:18.564Z",
    "resolved_at": null
  },
  {
    "id": 4,
    "kind": "unmet-truth",
    "phase": "18",
    "file": "plugins/beads-lifecycle/.gsd/capabilities/beads/tests/test_sync.py",
    "line": null,
    "description": "Overlay-tree suite run (.gsd/capabilities/beads/) fails 14/252 (PLUGIN_ROOT parents[4] resolves outside the vendored subtree) while the identical plugin-tree run is 252/OK and diff -rq is byte-silent; see gsd-beads-2e2.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-20T11:02:41.000Z",
    "resolved_at": null
  }
]
````
