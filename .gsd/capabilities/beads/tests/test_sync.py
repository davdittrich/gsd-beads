"""Tests for .gsd/capabilities/beads/scripts/sync.py.

Stdlib unittest only (N5). sync.py's parent directory is put on sys.path at
module import so no package __init__.py and no install step is needed.
"""
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sync  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _bd_on_path():
    return shutil.which("bd") is not None


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def _make_bd_side_effect():
    """A subprocess.run stand-in that answers every bd subcommand this
    module's tests exercise: list/show succeed, create hands back a fresh
    hierarchical id each call (a realistic stdout shape for --silent)."""
    counter = {"n": 0}

    def _side_effect(argv, **kwargs):
        if argv[:2] == ["bd", "list"]:
            return _completed(0, stdout="[]\n")
        if argv[:2] == ["bd", "show"]:
            return _completed(0, stdout="{}\n")
        if argv[:2] == ["bd", "create"]:
            counter["n"] += 1
            return _completed(0, stdout=f"mock-e1.{counter['n']}\n")
        if argv[:3] == ["bd", "dep", "add"]:
            return _completed(0)
        if argv[:2] == ["bd", "close"]:
            return _completed(0)
        return _completed(1, stderr=f"unexpected bd invocation: {argv}")

    return _side_effect


def _three_task_plan_text():
    tasks = "\n\n".join(
        f'''<task type="auto">
  <name>Task {i}: Do thing {i}</name>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement thing {i}.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Thing {i} is implemented.</done>
</task>'''
        for i in (1, 2, 3)
    )
    return f"""---
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
Three-task fixture used only by TestCreateIssues -- no beads-id on any task.
</objective>

<tasks>

{tasks}

</tasks>
"""


def _write_plan_workspace(tmp_path, plan_text, with_state=False):
    """Lay out a minimal .planning/ tree under tmp_path and drop plan_text at
    .planning/phases/01-substrate/01-01-PLAN.md. Returns the plan copy path."""
    planning_dir = tmp_path / ".planning"
    phase_dir = planning_dir / "phases" / "01-substrate"
    phase_dir.mkdir(parents=True)
    (planning_dir / "ROADMAP.md").write_text(
        "### Phase 1: Substrate\nGoal.\n", encoding="utf-8"
    )
    if with_state:
        (planning_dir / "STATE.md").write_text(
            "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
            encoding="utf-8",
        )
    plan_copy = phase_dir / "01-01-PLAN.md"
    plan_copy.write_text(plan_text, encoding="utf-8")
    return plan_copy


class TestEndToEndTracer(unittest.TestCase):
    """B1 tracer: one PLAN.md task becomes one bd issue under a real epic,
    against a real bd database in a temporary directory."""

    @unittest.skipUnless(_bd_on_path(), "bd binary not found on PATH")
    def test_single_task_creates_one_issue_under_epic(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            planning_dir = tmp_path / ".planning"
            phase_dir = planning_dir / "phases" / "01-substrate"
            phase_dir.mkdir(parents=True)
            (planning_dir / "STATE.md").write_text(
                "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
                encoding="utf-8",
            )
            (planning_dir / "ROADMAP.md").write_text(
                "### Phase 1: Substrate\nGoal.\n", encoding="utf-8"
            )
            plan_copy = phase_dir / "01-01-PLAN.md"
            plan_copy.write_text(
                (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            init = subprocess.run(
                ["bd", "init", "--prefix", "tracer"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            result = subprocess.run(
                [sys.executable, str(Path(sync.__file__)), "create-issues", str(plan_copy)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            new_text = plan_copy.read_text(encoding="utf-8")
            id_match = sync.BEADS_ID_RE.search(new_text)
            self.assertIsNotNone(id_match, "no <beads-id> written back into the plan copy")
            issue_id = id_match.group(1).strip()

            epic_match = sync.BEADS_EPIC_RE.search(new_text)
            self.assertIsNotNone(epic_match, "no beads_epic written into frontmatter")
            epic_id = epic_match.group(1)

            listed = subprocess.run(
                ["bd", "list", "--parent", epic_id, "--json"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            children = json.loads(listed.stdout)
            self.assertEqual(len(children), 1)
            self.assertEqual(children[0]["id"], issue_id)


class TestCreateIssues(unittest.TestCase):
    """B1: syncing a plan builds one epic-create argv (no stored epic yet)
    and one task-create argv per task lacking a <beads-id>, every task-create
    argv carrying --parent <epic-id>. subprocess.run is mocked throughout --
    no real bd database is touched."""

    @staticmethod
    def _create_argvs(call_args_list, issue_type):
        argvs = [c.args[0] for c in call_args_list]
        result = []
        for argv in argvs:
            if len(argv) > 1 and argv[1] == "create" and "--type" in argv:
                if argv[argv.index("--type") + 1] == issue_type:
                    result.append(argv)
        return result

    @mock.patch("subprocess.run")
    def test_single_task_builds_one_epic_and_one_task_create(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        epic_creates = self._create_argvs(mock_run.call_args_list, "epic")
        task_creates = self._create_argvs(mock_run.call_args_list, "task")
        self.assertEqual(len(epic_creates), 1)
        self.assertEqual(len(task_creates), 1)
        self.assertIn("--parent", task_creates[0])

    @mock.patch("subprocess.run")
    def test_three_task_plan_builds_three_task_creates_same_parent(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_copy = _write_plan_workspace(Path(tmp), _three_task_plan_text())
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        task_creates = self._create_argvs(mock_run.call_args_list, "task")
        self.assertEqual(len(task_creates), 3)
        parents = {argv[argv.index("--parent") + 1] for argv in task_creates}
        self.assertEqual(len(parents), 1)


class TestDependencyMapping(unittest.TestCase):
    """B2: dependency edges come only from intra-plan order and plan-level
    depends_on -- the `wave` frontmatter key is never read as an edge
    source, even for a wave-2 plan with an empty depends_on (D-04)."""

    def test_three_task_plan_yields_two_intra_plan_edges(self):
        edges = sync.derive_dependency_edges(["t1", "t2", "t3"], [])
        self.assertEqual(edges, [("t2", "t1"), ("t3", "t2")])

    def test_depends_on_prereq_adds_first_task_blocked_by_prereq_last_task(self):
        edges = sync.derive_dependency_edges(["t1", "t2", "t3"], ["prereq-last"])
        self.assertEqual(edges, [("t2", "t1"), ("t3", "t2"), ("t1", "prereq-last")])

    def test_empty_depends_on_yields_zero_cross_plan_edges_at_wave_two(self):
        # plan-deps.md itself carries wave: 2 and a non-empty depends_on --
        # confirm parsing pulls the real prereq id out of it.
        _, frontmatter, tasks = sync.parse_plan(FIXTURES_DIR / "plan-deps.md")
        self.assertIn("wave: 2", frontmatter)
        self.assertEqual(sync.parse_depends_on(frontmatter), ["01-01"])
        task_ids = [t["beads_id"] for t in tasks]
        self.assertEqual(len(task_ids), 3)

        # Separately: an empty depends_on at wave 2 must still yield zero
        # cross-plan edges -- proving wave number is never read as an edge
        # source, independent of what this fixture's own depends_on says.
        empty_frontmatter = "wave: 2\ndepends_on: []\n"
        self.assertEqual(sync.parse_depends_on(empty_frontmatter), [])
        edges_without_prereq = sync.derive_dependency_edges(task_ids, [])
        edges_with_prereq = sync.derive_dependency_edges(task_ids, ["prereq-x"])
        self.assertEqual(len(edges_without_prereq), 2)
        self.assertEqual(len(edges_with_prereq), 3)

    def test_resolve_prereq_last_task_id_finds_prerequisite_plans_last_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp)
            (phase_dir / "01-01-PLAN.md").write_text(
                (FIXTURES_DIR / "plan-synced.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            last_id = sync.resolve_prereq_last_task_id(phase_dir, "01-01")
        self.assertEqual(last_id, "tracer-f5x.2")

    def test_resolve_prereq_last_task_id_returns_none_for_unsynced_prerequisite(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp)
            (phase_dir / "01-01-PLAN.md").write_text(
                (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            last_id = sync.resolve_prereq_last_task_id(phase_dir, "01-01")
        self.assertIsNone(last_id)

    def test_resolve_prereq_last_task_id_rejects_unmatched_plan_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            last_id = sync.resolve_prereq_last_task_id(Path(tmp), "99-99")
        self.assertIsNone(last_id)

    @mock.patch("subprocess.run")
    def test_apply_dependency_edges_invokes_bd_dep_add_with_depends_on_flag(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        sync.apply_dependency_edges([("t2", "t1"), ("t3", "t2")])
        dep_argvs = [c.args[0] for c in mock_run.call_args_list]
        self.assertEqual(len(dep_argvs), 2)
        self.assertEqual(dep_argvs[0], ["bd", "dep", "add", "t2", "--depends-on", "t1"])

    @mock.patch("subprocess.run")
    def test_create_issues_wires_cross_plan_edge_from_depends_on(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            planning_dir = tmp_path / ".planning"
            phase_dir = planning_dir / "phases" / "01-substrate"
            phase_dir.mkdir(parents=True)
            (planning_dir / "ROADMAP.md").write_text(
                "### Phase 1: Substrate\nGoal.\n", encoding="utf-8"
            )
            (phase_dir / "01-01-PLAN.md").write_text(
                (FIXTURES_DIR / "plan-synced.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            dependent_text = _three_task_plan_text().replace(
                "depends_on: []", 'depends_on: ["01-01"]'
            )
            dependent_copy = phase_dir / "01-02-PLAN.md"
            dependent_copy.write_text(dependent_text, encoding="utf-8")

            exit_code = sync.create_issues(str(dependent_copy))

        self.assertEqual(exit_code, 0)
        dep_add_argvs = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:3] == ["bd", "dep", "add"]
        ]
        # 2 intra-plan edges (task2<-task1, task3<-task2) + 1 cross-plan edge
        # (task1 <- prerequisite plan's last task, tracer-f5x.2)
        self.assertEqual(len(dep_add_argvs), 3)
        self.assertTrue(any(argv[-1] == "tracer-f5x.2" for argv in dep_add_argvs))


class TestIdentityBinding(unittest.TestCase):
    """B4: a task carrying <beads-id> is never re-created; renaming the task
    title still resolves to the same id and creates nothing."""

    @mock.patch("subprocess.run")
    def test_synced_plan_creates_nothing(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-synced.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        create_calls = [
            c for c in mock_run.call_args_list if len(c.args[0]) > 1 and c.args[0][1] == "create"
        ]
        self.assertEqual(len(create_calls), 0)

    @mock.patch("subprocess.run")
    def test_rename_then_resync_creates_nothing_and_keeps_id(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-synced.md").read_text(encoding="utf-8")
            renamed = plan_text.replace(
                "Task 1: Do the first thing", "Task 1: Do a totally different thing"
            )
            plan_copy = _write_plan_workspace(Path(tmp), renamed)
            exit_code = sync.create_issues(str(plan_copy))
            new_text = plan_copy.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        create_calls = [
            c for c in mock_run.call_args_list if len(c.args[0]) > 1 and c.args[0][1] == "create"
        ]
        self.assertEqual(len(create_calls), 0)
        self.assertIn("<beads-id>tracer-f5x.1</beads-id>", new_text)


class TestFailOpen(unittest.TestCase):
    """B6: bd absent, or every bd invocation failing, degrades to exit 0, one
    stdout notice, one STATE.md bullet, and no BEADS.md -- never an
    exception."""

    def _run(self, tmp, which_return, run_side_effect):
        plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        plan_copy = _write_plan_workspace(Path(tmp), plan_text, with_state=True)
        state_path = plan_copy.parent.parent.parent / "STATE.md"

        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            with mock.patch("shutil.which", return_value=which_return):
                with mock.patch("subprocess.run", side_effect=run_side_effect):
                    exit_code = sync.create_issues(str(plan_copy))

        return exit_code, captured.getvalue(), state_path.read_text(encoding="utf-8"), plan_copy.parent / "BEADS.md"

    def test_bd_missing_from_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            exit_code, stdout_text, state_text, beads_md = self._run(
                tmp, which_return=None, run_side_effect=AssertionError("bd must not be invoked when absent")
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout_text.count(sync.NOTICE), 1)
        self.assertEqual(state_text.count("### Blockers/Concerns"), 1)
        self.assertEqual(state_text.count("bd unavailable"), 1)
        self.assertFalse(beads_md.exists())

    def test_bd_present_but_every_invocation_fails(self):
        def _always_fails(argv, **kwargs):
            return _completed(1, stderr="simulated bd failure")

        with tempfile.TemporaryDirectory() as tmp:
            exit_code, stdout_text, state_text, beads_md = self._run(
                tmp, which_return="/usr/bin/bd", run_side_effect=_always_fails
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout_text.count(sync.NOTICE), 1)
        self.assertEqual(state_text.count("### Blockers/Concerns"), 1)
        self.assertEqual(state_text.count("bd unavailable"), 1)
        self.assertFalse(beads_md.exists())


if __name__ == "__main__":
    unittest.main()
