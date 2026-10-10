---
phase: 01-substrate
plan: 03
type: execute
wave: 2
depends_on: ["01-01"]
files_modified:
  - src/example.py
autonomous: true
requirements: [B2]
---

<objective>
Three-task fixture with pre-assigned beads-id elements and a plan-level
depends_on entry, used only by TestDependencyMapping to exercise edge
derivation without exercising creation. wave is 2 deliberately: D-04
requires wave number to never be read as an edge source, and this fixture
is the one place that is asserted directly.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do thing 1</name>
  <beads-id>tracer-f5x.10</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement thing 1.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Thing 1 is implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Do thing 2</name>
  <beads-id>tracer-f5x.11</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement thing 2.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Thing 2 is implemented.</done>
</task>

<task type="auto">
  <name>Task 3: Do thing 3</name>
  <beads-id>tracer-f5x.12</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement thing 3.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Thing 3 is implemented.</done>
</task>

</tasks>
