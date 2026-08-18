---
phase: 01-substrate
plan: 04
type: execute
wave: 3
depends_on: []
beads_epic: tracer-wave1
files_modified:
  - src/example.py
autonomous: true
requirements: [B3]
---

<objective>
First plan of a two-plan wave fixture -- two tasks, both already carrying a
beads-id, used only by TestCloseWave to exercise the multi-plan batch-close
case (B3).
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do wave-a thing 1</name>
  <beads-id>tracer-wave1.1</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement wave-a thing 1.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Wave-a thing 1 is implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Do wave-a thing 2</name>
  <beads-id>tracer-wave1.2</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement wave-a thing 2.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Wave-a thing 2 is implemented.</done>
</task>

</tasks>
