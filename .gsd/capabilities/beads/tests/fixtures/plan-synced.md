---
phase: 01-substrate
plan: 01
type: execute
wave: 1
depends_on: []
beads_epic: tracer-f5x
files_modified:
  - src/example.py
  - src/other.py
autonomous: true
requirements: [B4]
---

<objective>
Two-task fixture plan used by sync.py's tests -- both tasks already carry a
beads-id element, for the re-sync and rename cases (B4/B5).
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do the first thing</name>
  <beads-id>tracer-f5x.1</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement the first thing.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>The first thing is implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Do the second thing</name>
  <beads-id>tracer-f5x.2</beads-id>
  <files>src/other.py</files>
  <read_first>src/other.py</read_first>
  <action>Implement the second thing.</action>
  <verify>python3 -m py_compile src/other.py</verify>
  <acceptance_criteria>
    - src/other.py exists
  </acceptance_criteria>
  <done>The second thing is implemented.</done>
</task>

</tasks>
