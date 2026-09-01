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
Two-task fixture plan used by sync.py's GH#7 regression tests -- task 1
carries an unbound placeholder identity element, task 2 carries a real,
already-synced id, isolating the placeholder-vs-stale distinction to a
single variable.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do the first thing</name>
  <beads-id>TBD</beads-id>
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
