---
phase: 01-substrate
plan: 05
type: execute
wave: 3
depends_on: []
beads_epic: tracer-wave1
files_modified:
  - src/other.py
autonomous: true
requirements: [B3]
---

<objective>
Second plan of the same two-plan wave fixture -- two tasks, both already
carrying a beads-id, used only by TestCloseWave to exercise the multi-plan
batch-close case (B3).
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do wave-b thing 1</name>
  <beads-id>tracer-wave1.3</beads-id>
  <files>src/other.py</files>
  <read_first>src/other.py</read_first>
  <action>Implement wave-b thing 1.</action>
  <verify>python3 -m py_compile src/other.py</verify>
  <acceptance_criteria>
    - src/other.py exists
  </acceptance_criteria>
  <done>Wave-b thing 1 is implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Do wave-b thing 2</name>
  <beads-id>tracer-wave1.4</beads-id>
  <files>src/other.py</files>
  <read_first>src/other.py</read_first>
  <action>Implement wave-b thing 2.</action>
  <verify>python3 -m py_compile src/other.py</verify>
  <acceptance_criteria>
    - src/other.py exists
  </acceptance_criteria>
  <done>Wave-b thing 2 is implemented.</done>
</task>

</tasks>
