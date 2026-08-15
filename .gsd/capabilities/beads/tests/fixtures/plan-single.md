---
phase: 01-substrate
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/example.py
autonomous: true
requirements: [B1]
---

<objective>
Minimal single-task fixture plan used by sync.py's tests -- one task, no
beads-id element yet (first-sync input).
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do the thing</name>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement the thing.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>The thing is implemented.</done>
</task>

</tasks>
