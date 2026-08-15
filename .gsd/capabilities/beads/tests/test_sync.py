"""Tests for .gsd/capabilities/beads/scripts/sync.py.

Stdlib unittest only (N5). sync.py's parent directory is put on sys.path at
module import so no package __init__.py and no install step is needed.
"""
import contextlib
import io
import json
import os
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


def _gsd_tools_path():
    """Resolve the installed gsd-core CLI shim, or None when absent -- guards
    every live `gsd_run`-based test the same way `_bd_on_path` guards the
    bd-based ones (03-03 Task 1)."""
    path = (
        Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
        / "gsd-core"
        / "bin"
        / "gsd-tools.cjs"
    )
    return path if path.exists() else None


def _capability_json_has_beads_md_gate():
    """True when this project's real capability.json already declares a
    ship:pre gate whose predicate reads BEADS.md (i.e. 03-02 has landed) --
    the skip condition for TestShipPreGenericDispatch's fourth test."""
    try:
        project_root = sync.find_project_root(Path(__file__).resolve().parent)
        cap_path = project_root / ".gsd" / "capabilities" / "beads" / "capability.json"
        cap = json.loads(cap_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    for gate in cap.get("gates", []):
        predicate = gate.get("check", {}).get("predicate", {})
        if predicate.get("artifact") == "BEADS.md":
            return True
    return False


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


class TestLiveDependencies(unittest.TestCase):
    """B2 proven against a real bd database: bd ready excludes a blocked
    task until its blocker closes. Named apart from TestEndToEndTracer so a
    -k filter targeting one class never accidentally picks up the other."""

    @unittest.skipUnless(_bd_on_path(), "bd binary not found on PATH")
    def test_ready_excludes_blocked_tasks_until_blockers_close(self):
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
            plan_copy.write_text(_three_task_plan_text(), encoding="utf-8")

            init = subprocess.run(
                ["bd", "init", "--prefix", "livedep"],
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
            ids = [m.strip() for m in sync.BEADS_ID_RE.findall(new_text)]
            self.assertEqual(len(ids), 3, ids)
            task1_id, task2_id, task3_id = ids

            epic_id = sync.BEADS_EPIC_RE.search(new_text).group(1)
            listed = subprocess.run(
                ["bd", "list", "--parent", epic_id, "--json"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(len(json.loads(listed.stdout)), 3)

            def _ready_ids():
                r = subprocess.run(
                    ["bd", "ready", "--json"],
                    cwd=tmp_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
                return {row["id"] for row in json.loads(r.stdout)}

            ready_before = _ready_ids()
            self.assertIn(task1_id, ready_before)
            self.assertNotIn(task2_id, ready_before)
            self.assertNotIn(task3_id, ready_before)

            close1 = subprocess.run(
                ["bd", "close", task1_id, "--reason", "task 1 done"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(close1.returncode, 0, close1.stderr)

            ready_after = _ready_ids()
            self.assertIn(task2_id, ready_after)
            self.assertNotIn(task3_id, ready_after)


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


class TestPhaseScopedEpic(unittest.TestCase):
    """gsd-beads-uh1: two plans in one phase, neither pre-set with
    beads_epic, sync to exactly one shared epic -- resolve_epic falls back
    to resolve_phase_epic (a sibling plan's already-recorded epic) before
    ever creating a fresh one."""

    @mock.patch("subprocess.run")
    def test_second_plan_in_phase_reuses_first_plans_epic_when_neither_preset_one(
        self, mock_run
    ):
        mock_run.side_effect = _make_bd_side_effect()
        plan_a_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        plan_b_text = plan_a_text.replace("plan: 01", "plan: 02", 1)
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = _write_plan_workspace(Path(tmp), plan_a_text)
            plan_b = plan_a.parent / "01-02-PLAN.md"
            plan_b.write_text(plan_b_text, encoding="utf-8")

            exit_a = sync.create_issues(str(plan_a))
            exit_b = sync.create_issues(str(plan_b))

            text_a = plan_a.read_text(encoding="utf-8")
            text_b = plan_b.read_text(encoding="utf-8")

        self.assertEqual(exit_a, 0)
        self.assertEqual(exit_b, 0)
        epic_creates = TestCreateIssues._create_argvs(mock_run.call_args_list, "epic")
        self.assertEqual(len(epic_creates), 1)

        epic_a = sync.BEADS_EPIC_RE.search(text_a).group(1)
        epic_b = sync.BEADS_EPIC_RE.search(text_b).group(1)
        self.assertEqual(epic_a, epic_b)


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

    def test_block_list_depends_on_is_parsed_not_silently_dropped(self):
        # WR-04: YAML's block-list form (key on its own line, `- item`
        # entries below it) previously matched neither DEPENDS_ON_RE nor
        # anything else, returning [] -- indistinguishable from a
        # legitimately empty dependency list.
        block_frontmatter = 'wave: 2\ndepends_on:\n  - "01-01"\n  - "02-03"\n'
        self.assertEqual(sync.parse_depends_on(block_frontmatter), ["01-01", "02-03"])

    def test_block_list_depends_on_single_item_no_quotes(self):
        block_frontmatter = "depends_on:\n  - 01-01\n"
        self.assertEqual(sync.parse_depends_on(block_frontmatter), ["01-01"])

    def test_inline_depends_on_still_wins_over_block_form_when_both_absent(self):
        # No depends_on key at all -- neither regex matches -- must stay [].
        self.assertEqual(sync.parse_depends_on("wave: 1\n"), [])

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


class TestIdempotency(unittest.TestCase):
    """B5: re-running sync over an unchanged plan writes nothing new; D-06
    closes an orphaned epic child once with a reason and never re-closes an
    already-closed one; D-07 reports (never heals) a stale <beads-id>."""

    @mock.patch("subprocess.run")
    def test_second_sync_over_unchanged_plan_issues_no_create_or_update_calls(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-synced.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            sync.create_issues(str(plan_copy))
            mock_run.reset_mock()
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        writes = [
            c.args[0]
            for c in mock_run.call_args_list
            if len(c.args[0]) > 1 and c.args[0][1] in ("create", "update")
        ]
        self.assertEqual(writes, [])

    @mock.patch("subprocess.run")
    def test_second_sync_over_unchanged_plan_leaves_plan_bytes_identical(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-synced.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            sync.create_issues(str(plan_copy))
            before = plan_copy.read_bytes()
            sync.create_issues(str(plan_copy))
            after = plan_copy.read_bytes()

        self.assertEqual(before, after)

    def test_orphaned_epic_child_closes_once_with_reason(self):
        def _side_effect(argv, **kwargs):
            if argv[:2] == ["bd", "list"]:
                return _completed(
                    0,
                    stdout=json.dumps(
                        [
                            {"id": "tracer-f5x.1", "status": "open"},
                            {"id": "tracer-f5x.2", "status": "open"},
                            {"id": "tracer-f5x.99", "status": "open"},
                        ]
                    ),
                )
            if argv[:2] == ["bd", "show"]:
                return _completed(0, stdout="{}\n")
            if argv[:2] == ["bd", "close"]:
                return _completed(0)
            if argv[:3] == ["bd", "dep", "add"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected bd invocation: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-orphan.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            with mock.patch("subprocess.run", side_effect=_side_effect) as mock_run:
                exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        close_calls = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        self.assertEqual(len(close_calls), 1)
        self.assertEqual(close_calls[0][2], "tracer-f5x.99")
        self.assertIn("--reason", close_calls[0])

    def test_orphan_sweep_skips_already_closed_children_on_repeat_run(self):
        def _side_effect(argv, **kwargs):
            if argv[:2] == ["bd", "list"]:
                return _completed(
                    0,
                    stdout=json.dumps(
                        [
                            {"id": "tracer-f5x.1", "status": "open"},
                            {"id": "tracer-f5x.2", "status": "open"},
                            {"id": "tracer-f5x.99", "status": "closed"},
                        ]
                    ),
                )
            if argv[:2] == ["bd", "show"]:
                return _completed(0, stdout="{}\n")
            if argv[:3] == ["bd", "dep", "add"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected bd invocation: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-orphan.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            with mock.patch("subprocess.run", side_effect=_side_effect) as mock_run:
                exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        close_calls = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        self.assertEqual(close_calls, [])

    def test_stale_beads_id_reports_divergence_without_recreating(self):
        def _side_effect(argv, **kwargs):
            if argv[:2] == ["bd", "show"] and argv[2] == "tracer-f5x.1":
                return _completed(1, stderr="no issue found matching tracer-f5x.1")
            if argv[:2] == ["bd", "show"]:
                return _completed(0, stdout="{}\n")
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:3] == ["bd", "dep", "add"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected bd invocation: {argv}")

        captured = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-synced.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            with mock.patch("subprocess.run", side_effect=_side_effect) as mock_run:
                with contextlib.redirect_stdout(captured):
                    exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        self.assertIn("tracer-f5x.1", captured.getvalue())
        create_calls = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "create"]
        ]
        self.assertEqual(create_calls, [])

    def test_stale_beads_epic_reports_divergence_instead_of_healing_silently(self):
        """WR-02: resolve_epic's stale-`beads_epic` fallback must report the
        split the same way resolve_issue's stale-<beads-id> fallback does
        (D-07 applied one level up) -- a silent replacement is what let a
        resync after an external epic deletion fork the phase across
        epics with zero visible signal."""

        def _side_effect(argv, **kwargs):
            if argv[:2] == ["bd", "show"] and argv[2] == "tracer-f5x":
                return _completed(1, stderr="no issue found matching tracer-f5x")
            if argv[:2] == ["bd", "show"]:
                return _completed(0, stdout="{}\n")
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:2] == ["bd", "create"]:
                return _completed(0, stdout="fresh-epic-01\n")
            if argv[:3] == ["bd", "dep", "add"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected bd invocation: {argv}")

        captured = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-synced.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            with mock.patch("subprocess.run", side_effect=_side_effect):
                with contextlib.redirect_stdout(captured):
                    exit_code = sync.create_issues(str(plan_copy))
            new_text = plan_copy.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        out = captured.getvalue()
        self.assertIn("divergence: stored beads_epic", out)
        self.assertIn("tracer-f5x", out)
        self.assertIn("not found in bd", out)
        self.assertEqual(sync.BEADS_EPIC_RE.search(new_text).group(1), "fresh-epic-01")


class TestEpicScopedOrphans(unittest.TestCase):
    """gsd-beads-bgb: syncing a second plan under a shared epic must never
    close a sibling plan's already-synced issue -- current_ids has to span
    every plan sharing the epic being synced, not just the plan in hand."""

    def test_syncing_second_plan_never_closes_first_plans_issue_under_shared_epic(self):
        plan_a_text = """---
phase: 01-substrate
plan: 01
type: execute
wave: 1
depends_on: []
beads_epic: shared-epic-01
files_modified:
  - src/example.py
autonomous: true
requirements: [B5]
---

<objective>
Plan A: already synced, one task carrying a beads-id under a shared epic.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do the first thing</name>
  <beads-id>shared-epic-01.1</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement the first thing.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>The first thing is implemented.</done>
</task>

</tasks>
"""
        plan_b_text = """---
phase: 01-substrate
plan: 02
type: execute
wave: 1
depends_on: []
beads_epic: shared-epic-01
files_modified:
  - src/other.py
autonomous: true
requirements: [B5]
---

<objective>
Plan B: same shared epic as plan A, one task not yet synced.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do the second thing</name>
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
"""

        def _side_effect(argv, **kwargs):
            if argv[:2] == ["bd", "show"]:
                return _completed(0, stdout="{}\n")
            if argv[:2] == ["bd", "create"] and "--type" in argv:
                if argv[argv.index("--type") + 1] == "task":
                    return _completed(0, stdout="shared-epic-01.2\n")
                return _completed(1, stderr=f"unexpected epic create: {argv}")
            if argv[:2] == ["bd", "list"]:
                return _completed(
                    0,
                    stdout=json.dumps(
                        [
                            {"id": "shared-epic-01.1", "status": "open"},
                            {"id": "shared-epic-01.2", "status": "open"},
                        ]
                    ),
                )
            if argv[:3] == ["bd", "dep", "add"]:
                return _completed(0)
            if argv[:2] == ["bd", "close"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected bd invocation: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            plan_a = _write_plan_workspace(Path(tmp), plan_a_text)
            plan_b = plan_a.parent / "01-02-PLAN.md"
            plan_b.write_text(plan_b_text, encoding="utf-8")
            with mock.patch("subprocess.run", side_effect=_side_effect) as mock_run:
                exit_code = sync.create_issues(str(plan_b))

        self.assertEqual(exit_code, 0)
        close_calls = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        closed_ids = {argv[2] for argv in close_calls}
        self.assertNotIn("shared-epic-01.1", closed_ids)


def _three_task_two_synced_plan_text():
    """Three tasks, only the first two carrying a <beads-id> -- the third was
    never synced (e.g. a checkpoint task), exercising the "of which two
    completed" wording from 01-03-PLAN.md's <behavior> block: two ids are
    closeable, the third contributes nothing because it never had one."""
    tasks = []
    for i in (1, 2, 3):
        beads_id_line = (
            f"\n  <beads-id>tracer-wave2.{i}</beads-id>" if i in (1, 2) else ""
        )
        tasks.append(
            f'''<task type="auto">
  <name>Task {i}: Do thing {i}</name>{beads_id_line}
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement thing {i}.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Thing {i} is implemented.</done>
</task>'''
        )
    return f"""---
phase: 01-substrate
plan: 06
type: execute
wave: 3
depends_on: []
beads_epic: tracer-wave2
files_modified:
  - src/example.py
autonomous: true
requirements: [B3]
---

<objective>
Single-plan wave fixture, three tasks, only two synced -- TestCloseWave's
partial-completion case.
</objective>

<tasks>

{chr(10).join(tasks)}

</tasks>
"""


def _write_wave_workspace(tmp_path, plans, with_state=False):
    """Lay out a minimal .planning/ tree and drop each (plan_id, plan_text,
    has_summary) entry at .planning/phases/01-substrate/<plan_id>-PLAN.md
    (+ a minimal SUMMARY.md when has_summary is True). Returns phase_dir."""
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
    for plan_id, plan_text, has_summary in plans:
        (phase_dir / f"{plan_id}-PLAN.md").write_text(plan_text, encoding="utf-8")
        if has_summary:
            (phase_dir / f"{plan_id}-SUMMARY.md").write_text(
                "status: complete\n", encoding="utf-8"
            )
    return phase_dir


def _make_close_wave_bd_side_effect():
    """A subprocess.run stand-in for close-wave tests: the bd_available probe
    (`bd list --json -n 1`) always succeeds; `bd list --id ... --status ...`
    answers only with ids not yet in the running `closed` set; `bd close`
    records every id it's given into that same set, so a second close_wave
    call over the same ids sees them as already closed (idempotency)."""
    closed = set()

    def _side_effect(argv, **kwargs):
        if argv[:3] == ["bd", "list", "--json"]:
            return _completed(0, stdout="[]\n")
        if argv[:3] == ["bd", "list", "--id"]:
            requested = argv[argv.index("--id") + 1].split(",")
            open_rows = [{"id": i, "status": "open"} for i in requested if i not in closed]
            return _completed(0, stdout=json.dumps(open_rows))
        if argv[:2] == ["bd", "close"]:
            reason_idx = argv.index("--reason")
            closed.update(argv[2:reason_idx])
            return _completed(0)
        return _completed(1, stderr=f"unexpected bd invocation: {argv}")

    return _side_effect


class TestCloseWave(unittest.TestCase):
    """B3: execute:wave:post fires once per wave carrying a list of plan
    ids, never once per task -- close_wave must batch-close every completed
    task's issue across every plan in that list in one dispatch."""

    @mock.patch("subprocess.run")
    def test_two_plan_wave_two_completed_tasks_each_closes_four_ids_in_one_call(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            plan_b = (FIXTURES_DIR / "plan-wave-b.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(
                Path(tmp),
                [("01-04", plan_a, True), ("01-05", plan_b, True)],
            )
            exit_code = sync.close_wave(str(phase_dir), ["01-04", "01-05"])

        self.assertEqual(exit_code, 0)
        close_argvs = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        self.assertEqual(len(close_argvs), 1)
        reason_idx = close_argvs[0].index("--reason")
        closed_ids = close_argvs[0][2:reason_idx]
        self.assertEqual(
            set(closed_ids),
            {"tracer-wave1.1", "tracer-wave1.2", "tracer-wave1.3", "tracer-wave1.4"},
        )

    @mock.patch("subprocess.run")
    def test_incomplete_plan_contributes_nothing_and_never_appears_in_close_argv(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            plan_b = (FIXTURES_DIR / "plan-wave-b.md").read_text(encoding="utf-8")
            # plan-wave-b is NOT yet complete (no SUMMARY.md) -- none of its
            # task ids may appear in the close argv.
            phase_dir = _write_wave_workspace(
                Path(tmp),
                [("01-04", plan_a, True), ("01-05", plan_b, False)],
            )
            exit_code = sync.close_wave(str(phase_dir), ["01-04", "01-05"])

        self.assertEqual(exit_code, 0)
        close_argvs = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        self.assertEqual(len(close_argvs), 1)
        reason_idx = close_argvs[0].index("--reason")
        closed_ids = set(close_argvs[0][2:reason_idx])
        self.assertEqual(closed_ids, {"tracer-wave1.1", "tracer-wave1.2"})
        self.assertNotIn("tracer-wave1.3", closed_ids)
        self.assertNotIn("tracer-wave1.4", closed_ids)

    @mock.patch("subprocess.run")
    def test_task_with_no_beads_id_skipped_and_reported_two_of_three_close(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        captured = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-06", _three_task_two_synced_plan_text(), True)]
            )
            with contextlib.redirect_stdout(captured):
                exit_code = sync.close_wave(str(phase_dir), ["01-06"])

        self.assertEqual(exit_code, 0)
        close_argvs = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        self.assertEqual(len(close_argvs), 1)
        reason_idx = close_argvs[0].index("--reason")
        closed_ids = set(close_argvs[0][2:reason_idx])
        self.assertEqual(closed_ids, {"tracer-wave2.1", "tracer-wave2.2"})
        self.assertIn("skipped 1 task(s)", captured.getvalue())

    @mock.patch("subprocess.run")
    def test_repeat_run_over_already_closed_wave_issues_zero_close_calls(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            plan_b = (FIXTURES_DIR / "plan-wave-b.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(
                Path(tmp),
                [("01-04", plan_a, True), ("01-05", plan_b, True)],
            )
            sync.close_wave(str(phase_dir), ["01-04", "01-05"])
            mock_run.reset_mock()
            exit_code = sync.close_wave(str(phase_dir), ["01-04", "01-05"])

        self.assertEqual(exit_code, 0)
        close_argvs = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        self.assertEqual(close_argvs, [])

    def test_bd_unavailable_close_wave_exits_zero_with_one_notice_and_closes_nothing(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(
                tmp_path, [("01-04", plan_a, True)], with_state=True
            )
            state_path = tmp_path / ".planning" / "STATE.md"

            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                with mock.patch("shutil.which", return_value=None):
                    with mock.patch(
                        "subprocess.run",
                        side_effect=AssertionError("bd must not be invoked when absent"),
                    ):
                        exit_code = sync.close_wave(str(phase_dir), ["01-04"])

            self.assertEqual(exit_code, 0)
            self.assertEqual(captured.getvalue().count(sync.NOTICE), 1)
            state_text = state_path.read_text(encoding="utf-8")
            self.assertEqual(state_text.count("### Blockers/Concerns"), 1)
            self.assertEqual(state_text.count("bd unavailable"), 1)


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

    def test_bd_probe_succeeds_but_create_fails_mid_sync(self):
        # Planted failure: the up-front bd_available() probe (`bd list`) must
        # succeed here so create_issues proceeds past it -- the prior two
        # tests both fail the probe itself and therefore never exercise this
        # path. `bd create` (called from resolve_epic) then fails, which
        # must degrade fail-open (exit 0, one notice, one STATE.md bullet),
        # not raise an uncaught RuntimeError.
        def _probe_ok_then_create_fails(argv, **kwargs):
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:2] == ["bd", "create"]:
                return _completed(1, stderr="simulated: bd locked mid-sync")
            return _completed(1, stderr=f"unexpected bd invocation: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            exit_code, stdout_text, state_text, beads_md = self._run(
                tmp, which_return="/usr/bin/bd", run_side_effect=_probe_ok_then_create_fails
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout_text.count(sync.NOTICE), 1)
        self.assertEqual(state_text.count("### Blockers/Concerns"), 1)
        self.assertIn("bd failing mid-sync", state_text)
        self.assertFalse(beads_md.exists())


def _make_beads_recall_bd_side_effect(issues_json="[]\n", desc_contains_matches=frozenset()):
    """A subprocess.run stand-in for beads-recall tests: the bd_available
    probe (`bd list --json -n 1`) always succeeds; the D-04 open-issue scan
    (`bd list --status ... --exclude-type epic --json -n 0`) answers with
    issues_json; a `bd list --id <id> --desc-contains <token> ...` call
    answers non-empty only when <id> is in desc_contains_matches (technique
    2's per-token fallback query)."""

    def _side_effect(argv, **kwargs):
        if argv[:3] == ["bd", "list", "--json"]:
            return _completed(0, stdout="[]\n")
        if "--desc-contains" in argv:
            issue_id = argv[argv.index("--id") + 1]
            if issue_id in desc_contains_matches:
                return _completed(0, stdout=json.dumps([{"id": issue_id}]))
            return _completed(0, stdout="[]\n")
        if argv[:3] == ["bd", "list", "--status"]:
            return _completed(0, stdout=issues_json)
        return _completed(1, stderr=f"unexpected bd invocation: {argv}")

    return _side_effect


def _write_recall_phase_workspace(tmp_path, phase_dir_name="02-visibility", roadmap_section=None, context_text=None):
    """Lay out a minimal .planning/ tree with a phase directory named
    phase_dir_name, a ROADMAP.md carrying that phase's section text, and an
    optional CONTEXT.md -- the pre-plan file-scope signal source (D-01
    revised, since no PLAN.md exists yet at plan:pre time for the phase
    being planned)."""
    planning_dir = tmp_path / ".planning"
    phase_dir = planning_dir / "phases" / phase_dir_name
    phase_dir.mkdir(parents=True)
    phase_num = phase_dir_name.split("-", 1)[0]
    section = roadmap_section or "Goal.\n"
    (planning_dir / "ROADMAP.md").write_text(
        f"### Phase {int(phase_num)}: Visibility\n{section}\n### Phase {int(phase_num) + 1}: Next\nGoal.\n",
        encoding="utf-8",
    )
    if context_text is not None:
        (phase_dir / f"{phase_num}-CONTEXT.md").write_text(context_text, encoding="utf-8")
    return phase_dir


class TestBeadsRecall(unittest.TestCase):
    """B7: BEADS-RECALL.md is always written when bd is available (D-04); an
    open issue touching this phase's scope is named under a matched heading,
    everything else under Unscoped, never dropped (D-02)."""

    @mock.patch("subprocess.run")
    def test_zero_open_issues_writes_none_found_body(self, mock_run):
        mock_run.side_effect = _make_beads_recall_bd_side_effect("[]\n")
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_recall_phase_workspace(Path(tmp))
            exit_code = sync.beads_recall(str(phase_dir))
            out_path = phase_dir / "02-BEADS-RECALL.md"

            self.assertEqual(exit_code, 0)
            self.assertTrue(out_path.exists())
            self.assertIn("No open issues found.", out_path.read_text(encoding="utf-8"))

    @mock.patch("subprocess.run")
    def test_multi_issue_response_lists_every_issue_under_unscoped(self, mock_run):
        issues = json.dumps(
            [
                {"id": "bd-1", "title": "Fix thing one", "status": "open"},
                {"id": "bd-2", "title": "Fix thing two", "status": "in_progress"},
            ]
        )
        mock_run.side_effect = _make_beads_recall_bd_side_effect(issues)
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_recall_phase_workspace(Path(tmp))
            exit_code = sync.beads_recall(str(phase_dir))
            out_path = phase_dir / "02-BEADS-RECALL.md"

            self.assertEqual(exit_code, 0)
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("## Unscoped", text)
            unscoped_section = text.split("## Unscoped", 1)[1]
            self.assertIn("bd-1", unscoped_section)
            self.assertIn("bd-2", unscoped_section)

    def test_bd_unavailable_writes_no_file_and_one_notice(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            phase_dir = _write_recall_phase_workspace(tmp_path)
            (tmp_path / ".planning" / "STATE.md").write_text(
                "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
                encoding="utf-8",
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                with mock.patch("shutil.which", return_value=None):
                    with mock.patch(
                        "subprocess.run",
                        side_effect=AssertionError("bd must not be invoked when absent"),
                    ):
                        exit_code = sync.beads_recall(str(phase_dir))
            out_path = phase_dir / "02-BEADS-RECALL.md"

            self.assertEqual(exit_code, 0)
            self.assertFalse(out_path.exists())
            self.assertEqual(captured.getvalue().count(sync.NOTICE), 1)

    @mock.patch("subprocess.run")
    def test_files_reverse_lookup_match_appears_under_matched_heading(self, mock_run):
        """Technique 1: an issue whose <beads-id>-linked task's <files>
        overlaps this phase's ROADMAP.md/CONTEXT.md mentions is listed under
        the matched heading, tagged "matched via: files" -- constructed from
        a second phase directory's PLAN.md under the same .planning/phases/
        tree (cross-phase fixture, in-test, no new fixture files on disk)."""
        issues = json.dumps(
            [{"id": "bd-scoped.1", "title": "Touches sync.py", "status": "open"}]
        )
        mock_run.side_effect = _make_beads_recall_bd_side_effect(issues)
        other_phase_plan_text = """---
phase: 01-substrate
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .gsd/capabilities/beads/scripts/sync.py
autonomous: true
requirements: [B1]
---

<objective>
Fixture task carrying a <beads-id> and <files> for the reverse-lookup test.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Touch sync.py</name>
  <beads-id>bd-scoped.1</beads-id>
  <files>.gsd/capabilities/beads/scripts/sync.py</files>
  <read_first>.gsd/capabilities/beads/scripts/sync.py</read_first>
  <action>Do the thing.</action>
  <verify>python3 -m py_compile .gsd/capabilities/beads/scripts/sync.py</verify>
  <acceptance_criteria>
    - sync.py exists
  </acceptance_criteria>
  <done>Done.</done>
</task>

</tasks>
"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            phase_dir = _write_recall_phase_workspace(
                tmp_path,
                roadmap_section="Extends `.gsd/capabilities/beads/scripts/sync.py`.\n",
            )
            other_phase_dir = tmp_path / ".planning" / "phases" / "01-substrate"
            other_phase_dir.mkdir(parents=True)
            (other_phase_dir / "01-01-PLAN.md").write_text(other_phase_plan_text, encoding="utf-8")

            exit_code = sync.beads_recall(str(phase_dir))
            out_path = phase_dir / "02-BEADS-RECALL.md"

            self.assertEqual(exit_code, 0)
            text = out_path.read_text(encoding="utf-8")
            matched_section = text.split("## Open issues touching this phase's scope", 1)[1]
            matched_section = matched_section.split("## Unscoped", 1)[0]
            self.assertIn("bd-scoped.1", matched_section)
            self.assertIn("matched via: files", matched_section)
            unscoped_section = text.split("## Unscoped", 1)[1]
            self.assertNotIn("bd-scoped.1", unscoped_section)

    @mock.patch("subprocess.run")
    def test_desc_contains_fallback_match_appears_under_matched_heading(self, mock_run):
        """Technique 2: an issue with no matching <beads-id> anywhere, but
        whose description substring-matches a phase-mentioned token, is
        listed under the matched heading, tagged "matched via: description"."""
        issues = json.dumps(
            [{"id": "bd-desc.1", "title": "Hand-filed issue", "status": "open"}]
        )
        mock_run.side_effect = _make_beads_recall_bd_side_effect(
            issues, desc_contains_matches={"bd-desc.1"}
        )
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_recall_phase_workspace(
                Path(tmp),
                roadmap_section="Extends `.gsd/capabilities/beads/scripts/sync.py`.\n",
            )
            exit_code = sync.beads_recall(str(phase_dir))
            out_path = phase_dir / "02-BEADS-RECALL.md"

            self.assertEqual(exit_code, 0)
            text = out_path.read_text(encoding="utf-8")
            matched_section = text.split("## Open issues touching this phase's scope", 1)[1]
            matched_section = matched_section.split("## Unscoped", 1)[0]
            self.assertIn("bd-desc.1", matched_section)
            self.assertIn("matched via: description", matched_section)

    @mock.patch("subprocess.run")
    def test_unmatched_issue_stays_unscoped_never_dropped(self, mock_run):
        """An issue matching neither technique 1 nor technique 2 stays under
        Unscoped -- D-02, never omitted from the file entirely."""
        issues = json.dumps(
            [{"id": "bd-neither.1", "title": "Unrelated issue", "status": "open"}]
        )
        mock_run.side_effect = _make_beads_recall_bd_side_effect(issues)
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_recall_phase_workspace(
                Path(tmp),
                roadmap_section="Extends `.gsd/capabilities/beads/scripts/sync.py`.\n",
            )
            exit_code = sync.beads_recall(str(phase_dir))
            out_path = phase_dir / "02-BEADS-RECALL.md"

            self.assertEqual(exit_code, 0)
            text = out_path.read_text(encoding="utf-8")
            unscoped_section = text.split("## Unscoped", 1)[1]
            self.assertIn("bd-neither.1", unscoped_section)

    @mock.patch("subprocess.run")
    def test_zero_open_issues_still_writes_none_found_body_with_scope_matching_wired(
        self, mock_run
    ):
        """Regression check against Task 1's baseline: a zero-open-issues run
        still writes the D-04 "none found" body once scope-matching (Task 2)
        is wired in."""
        mock_run.side_effect = _make_beads_recall_bd_side_effect("[]\n")
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_recall_phase_workspace(Path(tmp))
            exit_code = sync.beads_recall(str(phase_dir))
            out_path = phase_dir / "02-BEADS-RECALL.md"

            self.assertEqual(exit_code, 0)
            self.assertIn("No open issues found.", out_path.read_text(encoding="utf-8"))


def _regen_two_task_plan_text():
    """Two-task fixture carrying `beads_epic: regen-epic` and both tasks
    already synced -- used only by TestBeadsMdRegeneration/TestWaveStatusBlock
    to drive regenerate_beads_md/render_wave_status_block without touching a
    real bd database."""
    return """---
phase: 01-substrate
plan: 07
type: execute
wave: 1
depends_on: []
beads_epic: regen-epic
files_modified:
  - src/example.py
autonomous: true
requirements: [B11]
---

<objective>
Two-task fixture for TestBeadsMdRegeneration -- both tasks carry a beads-id.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Regen thing 1</name>
  <beads-id>regen-epic.1</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement regen thing 1.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Regen thing 1 is implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Regen thing 2</name>
  <beads-id>regen-epic.2</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement regen thing 2.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Regen thing 2 is implemented.</done>
</task>

</tasks>
"""


def _make_beads_md_bd_side_effect(rows_json="[]\n"):
    """A subprocess.run stand-in for BEADS.md regeneration tests: the
    bd_available probe (`bd list --json -n 1`) always succeeds; `bd list
    --parent <epic> --all --json -n 0` answers with rows_json."""

    def _side_effect(argv, **kwargs):
        if argv[:3] == ["bd", "list", "--json"]:
            return _completed(0, stdout="[]\n")
        if argv[:3] == ["bd", "list", "--parent"]:
            return _completed(0, stdout=rows_json)
        return _completed(1, stderr=f"unexpected bd invocation: {argv}")

    return _side_effect


def _find_table_row(text, issue_id):
    """Return the pipe-split, stripped cell list of the one markdown table
    row in text whose first cell equals issue_id, or raise if absent."""
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] == issue_id:
            return cells
    raise AssertionError(f"no table row found for {issue_id!r} in:\n{text}")


class TestBeadsMdRegeneration(unittest.TestCase):
    """B11: BEADS.md is regenerated from a live bd query at execute:wave:pre
    (read-only) -- D-05..D-08 frontmatter/table shape, full-file overwrite
    every run, blocked-by column excludes parent-child epic edges."""

    def test_render_beads_md_table_escapes_issue_id_and_blocked_by(self):
        """WR-01: _render_issue_table escapes id/title/status (T-02-03); this
        sibling renderer must match for issue_id and the blocked_by cell --
        both are re-parsed by _parse_beads_md_table_rows into a
        <beads_status> block pasted verbatim into a spawned Agent() prompt,
        so an unescaped `|` would shift table columns."""
        rows = [
            {
                "id": "evil|id",
                "title": "safe title",
                "status": "open",
                "dependencies": [
                    {"depends_on_id": "blocker|1", "type": "blocks"},
                    {"depends_on_id": "parent-epic", "type": "parent-child"},
                ],
            }
        ]
        table = sync._render_beads_md_table(rows, ordinal_map={}, task_status_by_id={})
        self.assertIn("evil\\|id", table)
        self.assertNotIn("| evil|id |", table)
        self.assertIn("blocker\\|1", table)
        # parent-child dependency must still be excluded from blocked_by.
        self.assertNotIn("parent-epic", table)

    def test_render_beads_md_table_lookups_survive_escaping(self):
        """The task_status/plan_task lookups key on bd's raw (unescaped)
        id -- escaping issue_id for display must not break them. Uses the
        raw table string directly rather than the naive `_find_table_row`
        test helper, since that helper's own unescape-unaware `split("|")`
        is exactly the bug WR-01 fixes in `_parse_beads_md_table_rows`."""
        rows = [{"id": "evil|id", "title": "t", "status": "open", "dependencies": []}]
        table = sync._render_beads_md_table(
            rows, ordinal_map={"evil|id": "01-01"}, task_status_by_id={"evil|id": "done"}
        )
        self.assertIn("| evil\\|id | t | open | done | 01-01 |  |", table)

    def test_parse_beads_md_table_rows_survives_pipe_in_id(self):
        """WR-01: _parse_beads_md_table_rows must recover the original,
        unescaped id/title/status -- a naive split("|") on the escaped
        `\\|` still shifts columns, which is exactly the corruption this
        fix closes (the reconstructed row feeds render_wave_status_block's
        <beads_status> block, pasted verbatim into a spawned Agent()
        prompt)."""
        rows = [{"id": "evil|id", "title": "safe title", "status": "open", "dependencies": []}]
        table = sync._render_beads_md_table(rows, ordinal_map={}, task_status_by_id={})
        parsed = sync._parse_beads_md_table_rows(table)
        self.assertEqual(parsed, [{"id": "evil|id", "title": "safe title", "status": "open"}])

    @mock.patch("subprocess.run")
    def test_frontmatter_matches_mocked_bd_response_counts(self, mock_run):
        rows = json.dumps(
            [
                {"id": "regen-epic.1", "title": "Regen thing 1", "status": "open", "dependencies": []},
                {"id": "regen-epic.2", "title": "Regen thing 2", "status": "closed", "dependencies": []},
            ]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _regen_two_task_plan_text(), True)]
            )
            exit_code = sync.regenerate_beads_md(str(phase_dir))
            out_path = phase_dir / "01-BEADS.md"

            self.assertEqual(exit_code, 0)
            self.assertTrue(out_path.exists())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("phase: 01-substrate", text)
            self.assertIn("epic: regen-epic", text)
            self.assertIn("open: 1", text)
            self.assertIn("closed: 1", text)
            self.assertIn("blocking_open: 1", text)
            self.assertIn("diverged: 1", text)
            self.assertIn("generated_from:", text)
            self.assertIn("generated_at:", text)

    @mock.patch("subprocess.run")
    def test_hand_edit_is_absent_after_next_regeneration(self, mock_run):
        rows = json.dumps(
            [{"id": "regen-epic.1", "title": "Regen thing 1", "status": "open", "dependencies": []}]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _regen_two_task_plan_text(), True)]
            )
            sync.regenerate_beads_md(str(phase_dir))
            out_path = phase_dir / "01-BEADS.md"
            hand_edited = out_path.read_text(encoding="utf-8") + "\nHAND EDITED LINE\n"
            out_path.write_text(hand_edited, encoding="utf-8")

            sync.regenerate_beads_md(str(phase_dir))
            after_text = out_path.read_text(encoding="utf-8")

        self.assertNotIn("HAND EDITED LINE", after_text)

    @mock.patch("subprocess.run")
    def test_blocked_by_column_excludes_parent_child_includes_blocks(self, mock_run):
        rows = json.dumps(
            [
                {"id": "regen-epic.1", "title": "Regen thing 1", "status": "open", "dependencies": []},
                {
                    "id": "regen-epic.2",
                    "title": "Regen thing 2",
                    "status": "open",
                    "dependencies": [
                        {"issue_id": "regen-epic.2", "depends_on_id": "regen-epic", "type": "parent-child"},
                        {"issue_id": "regen-epic.2", "depends_on_id": "regen-epic.1", "type": "blocks"},
                    ],
                },
            ]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _regen_two_task_plan_text(), True)]
            )
            sync.regenerate_beads_md(str(phase_dir))
            text = (phase_dir / "01-BEADS.md").read_text(encoding="utf-8")

        row = _find_table_row(text, "regen-epic.2")
        blocked_by_cell = row[-1]
        self.assertEqual(blocked_by_cell, "regen-epic.1")
        self.assertNotIn("regen-epic |", text)


class TestWaveStatusBlock(unittest.TestCase):
    """B8: render_wave_status_block prints a wave-scoped <beads_status> block
    naming only the given plan_ids' synced issues, sourced from the
    just-regenerated BEADS.md table (never a second bd query)."""

    @mock.patch("subprocess.run")
    def test_block_names_only_given_plan_ids_issues(self, mock_run):
        rows = json.dumps(
            [
                {"id": "tracer-wave1.1", "title": "Do wave-a thing 1", "status": "open", "dependencies": []},
                {"id": "tracer-wave1.2", "title": "Do wave-a thing 2", "status": "open", "dependencies": []},
                {"id": "tracer-wave1.3", "title": "Do wave-b thing 1", "status": "open", "dependencies": []},
                {"id": "tracer-wave1.4", "title": "Do wave-b thing 2", "status": "open", "dependencies": []},
            ]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            plan_b = (FIXTURES_DIR / "plan-wave-b.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(
                Path(tmp),
                [("01-04", plan_a, True), ("01-05", plan_b, True)],
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.render_wave_status_block(str(phase_dir), ["01-04"])

            self.assertEqual(exit_code, 0)
            out = captured.getvalue()
            self.assertIn("tracer-wave1.1", out)
            self.assertIn("tracer-wave1.2", out)
            self.assertNotIn("tracer-wave1.3", out)
            self.assertNotIn("tracer-wave1.4", out)
            self.assertTrue((phase_dir / "01-BEADS.md").exists())

    @mock.patch("subprocess.run")
    def test_zero_resolving_plan_ids_prints_no_synced_issues_line(self, mock_run):
        mock_run.side_effect = _make_beads_md_bd_side_effect("[]\n")
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-04", plan_a, True)]
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.render_wave_status_block(str(phase_dir), ["01-99"])

        self.assertEqual(exit_code, 0)
        self.assertIn("no synced issues for this wave", captured.getvalue())


class TestBlockingOpen(unittest.TestCase):
    """B9: blocking_open counts every open issue under the phase's shared
    epic, no priority/type filtering (D-01/D-02) -- equal to open_count,
    the same figure BEADS.md's existing `open:` field already reports."""

    @mock.patch("subprocess.run")
    def test_zero_row_epic_yields_blocking_open_zero(self, mock_run):
        mock_run.side_effect = _make_beads_md_bd_side_effect("[]\n")
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _regen_two_task_plan_text(), True)]
            )
            sync.regenerate_beads_md(str(phase_dir))
            text = (phase_dir / "01-BEADS.md").read_text(encoding="utf-8")

        self.assertIn("blocking_open: 0", text)

    @mock.patch("subprocess.run")
    def test_two_open_one_closed_yields_blocking_open_two(self, mock_run):
        rows = json.dumps(
            [
                {"id": "regen-epic.1", "title": "Regen thing 1", "status": "open", "dependencies": []},
                {"id": "regen-epic.2", "title": "Regen thing 2", "status": "open", "dependencies": []},
                {"id": "regen-epic.3", "title": "Regen thing 3", "status": "closed", "dependencies": []},
            ]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _regen_two_task_plan_text(), True)]
            )
            sync.regenerate_beads_md(str(phase_dir))
            text = (phase_dir / "01-BEADS.md").read_text(encoding="utf-8")

        self.assertIn("blocking_open: 2", text)


class TestDivergence(unittest.TestCase):
    """B10: diverged counts each synced issue whose bd closed-ness disagrees
    with its linked task's completion state, in either direction (D-04);
    the table's Task Status column names the task-completion side of a
    diverged row without cross-referencing PLAN.md/SUMMARY.md (D-06)."""

    @mock.patch("subprocess.run")
    def test_closed_issue_with_incomplete_task_diverges(self, mock_run):
        rows = json.dumps(
            [
                {"id": "regen-epic.1", "title": "Regen thing 1", "status": "closed", "dependencies": []},
                {"id": "regen-epic.2", "title": "Regen thing 2", "status": "open", "dependencies": []},
            ]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            # has_summary=False: no plan in this phase has completed, so
            # neither issue's linked task counts as done -- the closed
            # regen-epic.1 row disagrees (closed but incomplete), the open
            # regen-epic.2 row agrees (open and incomplete).
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _regen_two_task_plan_text(), False)]
            )
            sync.regenerate_beads_md(str(phase_dir))
            text = (phase_dir / "01-BEADS.md").read_text(encoding="utf-8")

        self.assertIn("diverged: 1", text)
        row = _find_table_row(text, "regen-epic.1")
        self.assertEqual(row[3], "incomplete")

    @mock.patch("subprocess.run")
    def test_zero_row_epic_yields_diverged_zero(self, mock_run):
        mock_run.side_effect = _make_beads_md_bd_side_effect("[]\n")
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _regen_two_task_plan_text(), True)]
            )
            sync.regenerate_beads_md(str(phase_dir))
            text = (phase_dir / "01-BEADS.md").read_text(encoding="utf-8")

        self.assertIn("diverged: 0", text)


def _write_ship_override_workspace(tmp_path, beads_md_text=None):
    """Lay out a minimal .planning/ tree (find_project_root's ancestor) with
    a phase_dir and, when given, a hand-written {padded_phase}-BEADS.md at
    the exact path ship_override reads -- no regenerate_beads_md call, since
    ship_override must source its values from the file on disk only."""
    planning_dir = tmp_path / ".planning"
    phase_dir = planning_dir / "phases" / "01-substrate"
    phase_dir.mkdir(parents=True)
    if beads_md_text is not None:
        (phase_dir / "01-BEADS.md").write_text(beads_md_text, encoding="utf-8")
    return phase_dir


def _ship_override_beads_md_text(epic="ship-epic", blocking_open=2, diverged=1):
    return (
        "---\n"
        "phase: 01-substrate\n"
        f"epic: {epic}\n"
        "open: 3\n"
        "closed: 1\n"
        f"blocking_open: {blocking_open}\n"
        f"diverged: {diverged}\n"
        'generated_from: "bd list --parent ship-epic --all --json -n 0"\n'
        "generated_at: 2026-08-15T00:00:00Z\n"
        "---\n\n"
        "# BEADS.md: 01-substrate\n\n"
        "| Issue | Title | Status | Task Status | Plan Task | Blocked By |\n"
        "|-------|-------|--------|-------------|-----------|------------|\n"
    )


class TestShipOverride(unittest.TestCase):
    """D-05: ship_override records a ship_gate bypass via a durable git
    trailer (always attempted, load-bearing) plus a best-effort bd comment
    (fail-open, B6) -- both sourced only from BEADS.md's own generated
    frontmatter, never a fresh live bd query."""

    def test_full_success_records_trailer_and_bd_comment(self):
        calls = []

        def _side_effect(argv, **kwargs):
            calls.append(argv)
            if argv[0] == "git":
                return _completed(0)
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:2] == ["bd", "comment"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_ship_override_workspace(
                Path(tmp),
                _ship_override_beads_md_text(epic="ship-epic", blocking_open=2, diverged=1),
            )
            with mock.patch("shutil.which", return_value="/usr/bin/bd"):
                with mock.patch("subprocess.run", side_effect=_side_effect):
                    exit_code = sync.ship_override(str(phase_dir))

        self.assertEqual(exit_code, 0)
        git_call = next(c for c in calls if c[:2] == ["git", "commit"])
        trailer_idx = git_call.index("--trailer") + 1
        self.assertEqual(
            git_call[trailer_idx],
            "Beads-Override: ship_gate bypassed, blocking_open=2, diverged=1",
        )
        comment_call = next(c for c in calls if c[:2] == ["bd", "comment"])
        self.assertEqual(comment_call[2], "ship-epic")

    def test_git_failure_still_records_bd_comment_and_exits_one(self):
        calls = []

        def _side_effect(argv, **kwargs):
            calls.append(argv)
            if argv[0] == "git":
                return _completed(1, stderr="amend failed")
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:2] == ["bd", "comment"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_ship_override_workspace(
                Path(tmp), _ship_override_beads_md_text()
            )
            with mock.patch("shutil.which", return_value="/usr/bin/bd"):
                with mock.patch("subprocess.run", side_effect=_side_effect):
                    exit_code = sync.ship_override(str(phase_dir))

        self.assertEqual(exit_code, 1)
        self.assertTrue(any(c[0] == "git" for c in calls))
        self.assertTrue(any(c[:2] == ["bd", "comment"] for c in calls))

    def test_head_already_pushed_refuses_amend_still_attempts_bd_comment(self):
        """New-01 (agy adversarial review): a ship retry after a prior run already
        completed push_branch means HEAD is already on the remote -- amending it
        would diverge local from origin with no fast-forward path. Must refuse the
        amend (never even attempt it), still try the best-effort bd comment (B6),
        and exit 1 since the durable trailer was NOT recorded."""
        calls = []

        def _side_effect(argv, **kwargs):
            calls.append(argv)
            if argv[:2] == ["git", "rev-parse"]:
                return _completed(0, stdout="origin/main\n")
            if argv[:2] == ["git", "rev-list"]:
                return _completed(0, stdout="0\n")
            if argv[0] == "git":
                return _completed(1, stderr="should not amend when HEAD already pushed")
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:2] == ["bd", "comment"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_ship_override_workspace(
                Path(tmp), _ship_override_beads_md_text(epic="ship-epic")
            )
            with mock.patch("shutil.which", return_value="/usr/bin/bd"):
                with mock.patch("subprocess.run", side_effect=_side_effect):
                    exit_code = sync.ship_override(str(phase_dir))

        self.assertEqual(exit_code, 1)
        self.assertFalse(any(c[:3] == ["git", "commit", "--amend"] for c in calls))
        self.assertTrue(any(c[:2] == ["bd", "comment"] for c in calls))

    def test_head_not_pushed_amends_normally(self):
        """No upstream divergence risk -- HEAD has 2 unpushed commits -- must
        proceed with the amend exactly as before this guard was added."""
        calls = []

        def _side_effect(argv, **kwargs):
            calls.append(argv)
            if argv[:2] == ["git", "rev-parse"]:
                return _completed(0, stdout="origin/main\n")
            if argv[:2] == ["git", "rev-list"]:
                return _completed(0, stdout="2\n")
            if argv[0] == "git":
                return _completed(0)
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:2] == ["bd", "comment"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_ship_override_workspace(
                Path(tmp), _ship_override_beads_md_text(epic="ship-epic")
            )
            with mock.patch("shutil.which", return_value="/usr/bin/bd"):
                with mock.patch("subprocess.run", side_effect=_side_effect):
                    exit_code = sync.ship_override(str(phase_dir))

        self.assertEqual(exit_code, 0)
        self.assertTrue(any(c[:3] == ["git", "commit", "--amend"] for c in calls))

    def test_no_upstream_configured_amends_normally(self):
        """git rev-parse @{u} fails (no upstream branch) -- treat as unknown/safe
        and proceed with the amend, matching prior behavior on a detached or
        unpushed-ever branch."""
        calls = []

        def _side_effect(argv, **kwargs):
            calls.append(argv)
            if argv[:2] == ["git", "rev-parse"]:
                return _completed(128, stderr="no upstream configured")
            if argv[0] == "git":
                return _completed(0)
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:2] == ["bd", "comment"]:
                return _completed(0)
            return _completed(1, stderr=f"unexpected: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_ship_override_workspace(
                Path(tmp), _ship_override_beads_md_text(epic="ship-epic")
            )
            with mock.patch("shutil.which", return_value="/usr/bin/bd"):
                with mock.patch("subprocess.run", side_effect=_side_effect):
                    exit_code = sync.ship_override(str(phase_dir))

        self.assertEqual(exit_code, 0)
        self.assertTrue(any(c[:3] == ["git", "commit", "--amend"] for c in calls))

    def test_bd_unavailable_still_writes_git_trailer_skips_comment(self):
        calls = []

        def _side_effect(argv, **kwargs):
            calls.append(argv)
            if argv[0] == "git":
                return _completed(0)
            if argv[:2] == ["bd", "list"]:
                return _completed(1, stderr="bd locked")
            return _completed(1, stderr=f"unexpected: {argv}")

        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_ship_override_workspace(
                Path(tmp), _ship_override_beads_md_text()
            )
            with mock.patch("shutil.which", return_value="/usr/bin/bd"):
                with mock.patch("subprocess.run", side_effect=_side_effect):
                    exit_code = sync.ship_override(str(phase_dir))

        self.assertEqual(exit_code, 0)
        self.assertTrue(any(c[0] == "git" for c in calls))
        self.assertFalse(any(c[:2] == ["bd", "comment"] for c in calls))

    def test_missing_beads_md_makes_zero_subprocess_calls_and_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_ship_override_workspace(Path(tmp), beads_md_text=None)
            with mock.patch("subprocess.run") as mock_run:
                exit_code = sync.ship_override(str(phase_dir))

        self.assertEqual(exit_code, 1)
        mock_run.assert_not_called()


class TestShipPreGenericDispatch(unittest.TestCase):
    """03-03 Task 1: live (non-mocked) proof that the two real `gsd_run`
    primitives ship.md's new preflight_checks steps 8/9 invoke -- `check
    predicate` (block/allow) and `loop render-hooks` (activeHooks source,
    including the beads.ship_gate gate-exclusion path) -- behave exactly as
    those new steps specify. subprocess.run is never mocked in this class."""

    @staticmethod
    def _beads_md_text(phase="03-enforcement", epic="epic-1", blocking_open=0, diverged=0):
        return (
            "---\n"
            f"phase: {phase}\n"
            f"epic: {epic}\n"
            "open: 0\n"
            "closed: 0\n"
            f"blocking_open: {blocking_open}\n"
            f"diverged: {diverged}\n"
            'generated_from: "bd list"\n'
            "generated_at: 2026-08-15T00:00:00Z\n"
            "---\n\n# BEADS.md\n"
        )

    @staticmethod
    def _run_predicate(phase_dir, field, equals):
        predicate = json.dumps(
            {
                "kind": "artifact-frontmatter-equals",
                "artifact": "BEADS.md",
                "field": field,
                "equals": equals,
            }
        )
        return subprocess.run(
            [
                "node",
                str(_gsd_tools_path()),
                "check",
                "predicate",
                "--predicate",
                predicate,
                "--phase-dir",
                str(phase_dir),
                "--raw",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

    @unittest.skipUnless(
        _gsd_tools_path() is not None and shutil.which("node") is not None,
        "gsd-tools.cjs / node not found",
    )
    def test_predicate_blocks_on_nonzero_blocking_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp) / "03-enforcement"
            phase_dir.mkdir()
            (phase_dir / "03-BEADS.md").write_text(
                self._beads_md_text(blocking_open=1), encoding="utf-8"
            )
            result = self._run_predicate(phase_dir, "blocking_open", 0)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["block"])
        self.assertIn("blocking_open", payload["message"])

    @unittest.skipUnless(
        _gsd_tools_path() is not None and shutil.which("node") is not None,
        "gsd-tools.cjs / node not found",
    )
    def test_predicate_passes_on_zero_blocking_open_and_diverged(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp) / "03-enforcement"
            phase_dir.mkdir()
            (phase_dir / "03-BEADS.md").write_text(
                self._beads_md_text(blocking_open=0, diverged=0), encoding="utf-8"
            )
            result_blocking = self._run_predicate(phase_dir, "blocking_open", 0)
            result_diverged = self._run_predicate(phase_dir, "diverged", 0)

        self.assertEqual(result_blocking.returncode, 0, result_blocking.stderr)
        self.assertEqual(result_diverged.returncode, 0, result_diverged.stderr)
        self.assertFalse(json.loads(result_blocking.stdout)["block"])
        self.assertFalse(json.loads(result_diverged.stdout)["block"])

    @unittest.skipUnless(
        _gsd_tools_path() is not None and shutil.which("node") is not None,
        "gsd-tools.cjs / node not found",
    )
    def test_fail_open_precheck_skips_missing_artifact_before_evaluator_would_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp) / "03-enforcement"
            phase_dir.mkdir()

            # (a) the exact pre-check ship.md's step 8 specifies: a bare glob
            # over the phase dir finds nothing when no *-BEADS.md exists yet.
            glob_result = subprocess.run(
                ["bash", "-c", f'ls "{phase_dir}"/*-BEADS.md 2>/dev/null | head -1'],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(glob_result.stdout.strip(), "")

            # (b) calling the real evaluator anyway independently confirms it
            # fails CLOSED (block: true) on the same missing artifact -- proving
            # the pre-check in (a) is load-bearing, not redundant.
            result = self._run_predicate(phase_dir, "blocking_open", 0)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["block"])
        self.assertTrue(payload.get("details", {}).get("artifactNotFound"))

    @unittest.skipUnless(
        _gsd_tools_path() is not None
        and shutil.which("node") is not None
        and _capability_json_has_beads_md_gate(),
        "gsd-tools.cjs / node not found, or Plan 02's ship:pre gates not yet in capability.json",
    )
    def test_beads_gate_hooks_excluded_step_hook_retained_when_ship_gate_false(self):
        project_root = sync.find_project_root(Path(__file__).resolve().parent)
        config_path = project_root / ".planning" / "config.json"
        original_text = config_path.read_text(encoding="utf-8")
        config = json.loads(original_text)
        try:
            # Running this pytest process writes __pycache__/*.pyc under this
            # bundle (sync.py's and this file's own import) -- the capability
            # loader's project-scope consent is a whole-bundle content hash, so
            # that write silently deactivates beads before this test's own
            # activeHooks check ever runs. Re-consenting here (same operational
            # fix this project already applies after any bundle edit) makes the
            # check reflect the CURRENT bundle content, not a stale hash.
            reconsent = subprocess.run(
                [
                    "node",
                    str(_gsd_tools_path()),
                    "capability",
                    "install",
                    "./.gsd/capabilities/beads",
                    "--scope",
                    "project",
                    "--yes",
                ],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(reconsent.returncode, 0, reconsent.stderr)

            config.setdefault("beads", {})["ship_gate"] = False
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            result = subprocess.run(
                ["node", str(_gsd_tools_path()), "loop", "render-hooks", "ship:pre", "--raw"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(project_root),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            active_hooks = payload.get("activeHooks", [])
            gate_hooks = [
                h for h in active_hooks if h.get("capId") == "beads" and h.get("kind") == "gate"
            ]
            step_hooks = [
                h
                for h in active_hooks
                if h.get("capId") == "beads"
                and h.get("kind") == "step"
                and h.get("ref", {}).get("skill") == "beads-status"
            ]
            self.assertEqual(gate_hooks, [])
            self.assertGreaterEqual(len(step_hooks), 1)
        finally:
            config_path.write_text(original_text, encoding="utf-8")


class TestCheckShipmdPatch(unittest.TestCase):
    """03-03 Task 2: check_shipmd_patch is a pure read-and-warn function
    (never edits ship.md) reporting whether the local ship.md patch is
    present, absent, or the file itself is missing."""

    def test_reports_present_when_marker_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            ship_md.write_text(
                f"...preamble...\n{sync.SHIP_MD_PATCH_MARKER}\n...body...\n",
                encoding="utf-8",
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_shipmd_patch(str(ship_md))

        self.assertEqual(exit_code, 0)
        self.assertIn("present", captured.getvalue())

    def test_reports_missing_with_reapply_pointer_when_marker_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            ship_md.write_text("no patch marker in this file\n", encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_shipmd_patch(str(ship_md))

        self.assertEqual(exit_code, 1)
        out = captured.getvalue()
        self.assertIn("GSD-CORE-PATCH.md", out)
        self.assertIn("ship_override", out)

    def test_reports_missing_with_reapply_pointer_when_file_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "does-not-exist" / "ship.md"
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_shipmd_patch(str(missing_path))

        self.assertEqual(exit_code, 1)
        self.assertIn(str(missing_path), captured.getvalue())


def _write_todo_pending_workspace(tmp_path, with_state=True):
    """Lay out a minimal .planning/todos/pending/ tree under tmp_path
    (B12) -- migrate_todos' find_project_root climb reaches tmp_path/
    .planning the same way close_wave/beads_recall's phase_dir climb does."""
    planning_dir = tmp_path / ".planning"
    pending_dir = planning_dir / "todos" / "pending"
    pending_dir.mkdir(parents=True)
    if with_state:
        (planning_dir / "STATE.md").write_text(
            "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
            encoding="utf-8",
        )
    return pending_dir


def _write_fixture_todo(pending_dir, fixture_name, dest_name=None):
    text = (FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")
    dest = pending_dir / (dest_name or fixture_name)
    dest.write_text(text, encoding="utf-8")
    return dest


def _status_mixed_task_plan_text():
    """One task carrying a <beads-id> (matches a bd row), one task with no
    <beads-id> at all -- the task-side orphan render_status_mapping must
    surface under "Plan tasks with no bd issue" (B13)."""
    return """---
phase: 01-substrate
plan: 09
type: execute
wave: 1
depends_on: []
beads_epic: status-epic
files_modified:
  - src/example.py
autonomous: true
requirements: [B13]
---

<objective>
Fixture for TestOnDemandStatus -- task 1 synced, task 2 never synced.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Status thing 1</name>
  <beads-id>status-epic.1</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement status thing 1.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Status thing 1 is implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Status thing 2</name>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement status thing 2.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>Status thing 2 is implemented.</done>
</task>

</tasks>
"""


def _write_status_workspace(tmp_path, phase_dir_name, plans, current_phase=None):
    """Lay out a minimal .planning/ tree with one phase dir (phase_dir_name)
    holding each (plan_id, plan_text) pair, plus a STATE.md -- carrying
    `current_phase` frontmatter (D-08's default-resolution source) when
    given, otherwise the plain Blockers/Concerns-only shape every other
    class's workspace helper already writes. Returns (project_root,
    phase_dir)."""
    planning_dir = tmp_path / ".planning"
    phase_dir = planning_dir / "phases" / phase_dir_name
    phase_dir.mkdir(parents=True)
    (planning_dir / "ROADMAP.md").write_text(
        "### Phase 1: Substrate\nGoal.\n", encoding="utf-8"
    )
    if current_phase is not None:
        (planning_dir / "STATE.md").write_text(
            f"---\ncurrent_phase: {current_phase}\n---\n\n"
            "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
            encoding="utf-8",
        )
    else:
        (planning_dir / "STATE.md").write_text(
            "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
            encoding="utf-8",
        )
    for plan_id, plan_text in plans:
        (phase_dir / f"{plan_id}-PLAN.md").write_text(plan_text, encoding="utf-8")
    return tmp_path, phase_dir


class TestOnDemandStatus(unittest.TestCase):
    """B13: render_status_mapping is a read-only, on-demand view of the
    plan-task <-> bd issue mapping for a phase -- the same table
    regenerate_beads_md builds, plus two orphan sections (D-09)."""

    @mock.patch("subprocess.run")
    def test_bd_side_orphan_listed_under_issues_with_no_matching_plan_task(self, mock_run):
        rows = json.dumps(
            [
                {"id": "status-epic.1", "title": "Status thing 1", "status": "open", "dependencies": []},
                {"id": "status-epic.99", "title": "Orphan issue", "status": "open", "dependencies": []},
            ]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            _, phase_dir = _write_status_workspace(
                Path(tmp), "01-substrate", [("01-09", _status_mixed_task_plan_text())]
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.render_status_mapping(str(phase_dir))

        self.assertEqual(exit_code, 0)
        out = captured.getvalue()
        self.assertIn("## Issues with no matching plan task", out)
        orphan_section = out.split("## Issues with no matching plan task", 1)[1]
        orphan_section = orphan_section.split("## Plan tasks with no bd issue", 1)[0]
        self.assertIn("status-epic.99", orphan_section)
        self.assertNotIn("status-epic.1 ", orphan_section)

    @mock.patch("subprocess.run")
    def test_task_with_no_beads_id_listed_under_plan_tasks_with_no_bd_issue(self, mock_run):
        rows = json.dumps(
            [{"id": "status-epic.1", "title": "Status thing 1", "status": "open", "dependencies": []}]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            _, phase_dir = _write_status_workspace(
                Path(tmp), "01-substrate", [("01-09", _status_mixed_task_plan_text())]
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.render_status_mapping(str(phase_dir))

        self.assertEqual(exit_code, 0)
        out = captured.getvalue()
        self.assertIn("## Plan tasks with no bd issue", out)
        self.assertIn("01-09-PLAN.md: Task 2: Status thing 2", out)

    @mock.patch("subprocess.run")
    def test_status_command_with_no_argument_resolves_default_phase_dir(self, mock_run):
        rows = json.dumps(
            [{"id": "status-epic.1", "title": "Status thing 1", "status": "open", "dependencies": []}]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _, phase_dir = _write_status_workspace(
                tmp_path,
                "01-substrate",
                [("01-09", _status_mixed_task_plan_text())],
                current_phase="1",
            )
            cwd = os.getcwd()
            os.chdir(str(tmp_path))
            try:
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    exit_code = sync.main(["status"])
            finally:
                os.chdir(cwd)

        self.assertEqual(exit_code, 0)
        self.assertIn("Status thing 1", captured.getvalue())

    @mock.patch("subprocess.run")
    def test_task_side_orphan(self, mock_run):
        """RESEARCH's Test Map row (Phase Requirements -> Test Map): a
        dedicated regression asserting the task-side orphan list names the
        correct plan filename and task name pair -- no existing function
        computed this before this plan."""
        rows = json.dumps(
            [{"id": "status-epic.1", "title": "Status thing 1", "status": "open", "dependencies": []}]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            _, phase_dir = _write_status_workspace(
                Path(tmp), "01-substrate", [("01-09", _status_mixed_task_plan_text())]
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.render_status_mapping(str(phase_dir))

        out = captured.getvalue()
        plan_task_lines = out.split("## Plan tasks with no bd issue", 1)[1]
        self.assertIn("01-09-PLAN.md: Task 2: Status thing 2", plan_task_lines)
        self.assertNotIn("Task 1: Status thing 1", plan_task_lines)

    @mock.patch("subprocess.run")
    def test_read_only_guarantee_no_bd_close_update_comment_calls(self, mock_run):
        """T-04-05: render_status_mapping only reports, it never reconciles
        -- inspect every argv run_bd was called with across a full run and
        assert none has close/update/comment as its second element."""
        rows = json.dumps(
            [
                {"id": "status-epic.1", "title": "Status thing 1", "status": "open", "dependencies": []},
                {"id": "status-epic.99", "title": "Orphan issue", "status": "open", "dependencies": []},
            ]
        )
        mock_run.side_effect = _make_beads_md_bd_side_effect(rows)
        with tempfile.TemporaryDirectory() as tmp:
            _, phase_dir = _write_status_workspace(
                Path(tmp), "01-substrate", [("01-09", _status_mixed_task_plan_text())]
            )
            sync.render_status_mapping(str(phase_dir))

        for call in mock_run.call_args_list:
            argv = call.args[0]
            second_element = argv[1] if len(argv) > 1 else None
            self.assertNotIn(second_element, ("close", "update", "comment"))


class TestMigrateTodos(unittest.TestCase):
    """B12: parse_todo/migrate_todos happy-path -- a well-formed todo becomes
    one mapped `bd create` argv and its file is deleted; a malformed todo
    (missing `severity`) is left in place, never sent to `bd create`."""

    def test_parse_todo_wellformed_returns_expected_fields(self):
        todo = sync.parse_todo(FIXTURES_DIR / "todo-wellformed.md")
        self.assertEqual(todo["severity"], "major")
        self.assertEqual(todo["area"], "sync")
        self.assertEqual(
            todo["files"], [".gsd/capabilities/beads/scripts/sync.py:120-140"]
        )
        self.assertIn("retry loop", todo["problem"])
        self.assertIn("completed flag", todo["solution"])

    def test_parse_todo_missing_severity_raises(self):
        with self.assertRaises(ValueError):
            sync.parse_todo(FIXTURES_DIR / "todo-malformed.md")

    def test_parse_todo_missing_closing_frontmatter_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.md"
            broken.write_text(
                "---\ntitle: X\nseverity: major\n\n## Problem\nY\n", encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                sync.parse_todo(broken)

    @mock.patch("subprocess.run")
    def test_wellformed_migrates_and_deletes_file(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pending_dir = _write_todo_pending_workspace(tmp_path)
            todo_path = _write_fixture_todo(pending_dir, "todo-wellformed.md")

            exit_code = sync.migrate_todos(str(pending_dir))

            self.assertEqual(exit_code, 0)
            create_calls = [
                c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "create"]
            ]
            self.assertEqual(len(create_calls), 1)
            argv = create_calls[0]
            self.assertEqual(argv[argv.index("-p") + 1], "1")  # severity: major -> priority 1
            self.assertEqual(argv[argv.index("-l") + 1], "area-sync")
            desc = argv[argv.index("-d") + 1]
            self.assertTrue(desc.startswith("## Problem"))
            self.assertFalse(todo_path.exists())

    @mock.patch("subprocess.run")
    def test_malformed_neither_deleted_nor_sent_to_bd_create(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pending_dir = _write_todo_pending_workspace(tmp_path)
            malformed_path = _write_fixture_todo(pending_dir, "todo-malformed.md")

            exit_code = sync.migrate_todos(str(pending_dir))

            self.assertEqual(exit_code, 0)
            self.assertTrue(malformed_path.exists())
            create_calls = [
                c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "create"]
            ]
            self.assertEqual(len(create_calls), 0)


class TestMigrateTodosReport(unittest.TestCase):
    """D-04/Pitfall 2: a bd-create failure, bd-unavailable, and a missing
    pending/ directory are three independently reported/handled outcomes --
    none of them deletes a todo file or raises."""

    @mock.patch("subprocess.run")
    def test_bd_create_failure_reported_separately_and_file_kept(self, mock_run):
        def _side_effect(argv, **kwargs):
            if argv[:2] == ["bd", "list"]:
                return _completed(0, stdout="[]\n")
            if argv[:2] == ["bd", "create"]:
                return _completed(1, stderr="bd: database locked")
            return _completed(1, stderr=f"unexpected bd invocation: {argv}")

        mock_run.side_effect = _side_effect
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pending_dir = _write_todo_pending_workspace(tmp_path)
            todo_path = _write_fixture_todo(pending_dir, "todo-wellformed.md")

            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.migrate_todos(str(pending_dir))

            self.assertEqual(exit_code, 0)
            self.assertTrue(todo_path.exists())
            report = captured.getvalue()
            self.assertIn("bd create failed", report)
            self.assertNotIn("could not be interpreted:", report)

    def test_bd_unavailable_issues_zero_subprocess_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pending_dir = _write_todo_pending_workspace(tmp_path)
            todo_path = _write_fixture_todo(pending_dir, "todo-wellformed.md")

            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                with mock.patch("shutil.which", return_value=None):
                    with mock.patch(
                        "subprocess.run",
                        side_effect=AssertionError("bd must not be invoked when absent"),
                    ):
                        exit_code = sync.migrate_todos(str(pending_dir))

            self.assertEqual(exit_code, 0)
            self.assertTrue(todo_path.exists())
            self.assertEqual(captured.getvalue().count(sync.NOTICE), 1)

    @mock.patch("subprocess.run")
    def test_missing_pending_dir_returns_zero_not_exception(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / ".planning").mkdir()
            missing_pending = tmp_path / ".planning" / "todos" / "pending"

            exit_code = sync.migrate_todos(str(missing_pending))

        self.assertEqual(exit_code, 0)


def _make_milestone_bd_side_effect(seed_titles=None):
    """subprocess.run stand-in for TestMilestoneEpic: `bd show <id> --json`
    answers with the title recorded either by seed_titles (pre-existing
    epics, simulating an epic created before this test's mock ever ran) or
    by a prior `bd create` call this same side_effect already answered -- so
    a second resolve_milestone_epic scan's title-match check sees the exact
    title the first call created. `bd create --type epic` hands back a
    fresh `milestone-epic.N` id and records (id -> title) for later `bd
    show` lookups; a task create gets a `mock-task.N` id and is not
    recorded (never looked up by id in these tests)."""
    known_titles = dict(seed_titles or {})
    counter = {"n": 0}

    def _side_effect(argv, **kwargs):
        if argv[:2] == ["bd", "show"]:
            issue_id = argv[2]
            if issue_id in known_titles:
                return _completed(
                    0, stdout=json.dumps({"id": issue_id, "title": known_titles[issue_id]})
                )
            return _completed(1, stderr="not found")
        if argv[:2] == ["bd", "create"]:
            counter["n"] += 1
            title = argv[2]
            if "--type" in argv and argv[argv.index("--type") + 1] == "epic":
                new_id = f"milestone-epic.{counter['n']}"
                known_titles[new_id] = title
                return _completed(0, stdout=f"{new_id}\n")
            return _completed(0, stdout=f"mock-task.{counter['n']}\n")
        if argv[:3] == ["bd", "dep", "add"]:
            return _completed(0)
        if argv[:2] == ["bd", "list"]:
            return _completed(0, stdout="[]\n")
        if argv[:2] == ["bd", "close"]:
            return _completed(0)
        return _completed(1, stderr=f"unexpected bd invocation: {argv}")

    return _side_effect


def _write_milestone_workspace(
    tmp_path, phase_dir_names, milestone="v1.0", milestone_name="milestone", epic_per=None
):
    """Lay out a .planning/ tree (B14) with STATE.md carrying milestone/
    milestone_name frontmatter, an optional beads.epic_per config.json
    override, and one empty phase directory per name in phase_dir_names.
    Returns (project_root, {phase_dir_name: phase_dir_path}) -- callers
    write their own *-PLAN.md files into the returned phase dirs."""
    planning_dir = tmp_path / ".planning"
    planning_dir.mkdir(parents=True)
    (planning_dir / "ROADMAP.md").write_text(
        "### Phase 1: Substrate\nGoal.\n\n### Phase 3: Enforcement\nGoal.\n",
        encoding="utf-8",
    )
    (planning_dir / "STATE.md").write_text(
        f"---\nmilestone: {milestone}\nmilestone_name: {milestone_name}\n---\n\n"
        "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
        encoding="utf-8",
    )
    if epic_per is not None:
        (planning_dir / "config.json").write_text(
            json.dumps({"beads": {"epic_per": epic_per}}), encoding="utf-8"
        )
    phase_dirs = {}
    for name in phase_dir_names:
        phase_dir = planning_dir / "phases" / name
        phase_dir.mkdir(parents=True)
        phase_dirs[name] = phase_dir
    return tmp_path, phase_dirs


class TestMilestoneEpic(unittest.TestCase):
    """B14: `beads.epic_per=milestone` shares one epic across every phase in
    the current milestone (D-10 forward-only, D-11 read-fresh); the default
    ("phase", or the key absent) is byte-for-byte unchanged from Phases
    1-3's existing per-phase-epic behavior."""

    def test_read_epic_per_defaults_to_phase_when_config_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / ".planning").mkdir()
            self.assertEqual(sync.read_epic_per(tmp_path), "phase")

    def test_read_epic_per_returns_configured_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            planning_dir = tmp_path / ".planning"
            planning_dir.mkdir()
            (planning_dir / "config.json").write_text(
                json.dumps({"beads": {"epic_per": "milestone"}}), encoding="utf-8"
            )
            self.assertEqual(sync.read_epic_per(tmp_path), "milestone")

    def test_read_epic_per_defaults_to_phase_on_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            planning_dir = tmp_path / ".planning"
            planning_dir.mkdir()
            (planning_dir / "config.json").write_text("{not valid json", encoding="utf-8")
            self.assertEqual(sync.read_epic_per(tmp_path), "phase")

    def test_milestone_epic_title_matches_state_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "STATE.md"
            state_path.write_text(
                "---\nmilestone: v1.0\nmilestone_name: milestone\n---\n\n# State\n",
                encoding="utf-8",
            )
            self.assertEqual(
                sync.milestone_epic_title(state_path), "Milestone v1.0: milestone"
            )

    @mock.patch("subprocess.run")
    def test_two_phases_share_one_milestone_epic_and_second_sync_creates_no_second_epic(
        self, mock_run
    ):
        mock_run.side_effect = _make_milestone_bd_side_effect()
        plan_a_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        plan_b_text = plan_a_text.replace("plan: 01", "plan: 02", 1)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path, phase_dirs = _write_milestone_workspace(
                Path(tmp), ["01-substrate", "02-visibility"], epic_per="milestone"
            )
            plan_a = phase_dirs["01-substrate"] / "01-01-PLAN.md"
            plan_a.write_text(plan_a_text, encoding="utf-8")
            plan_b = phase_dirs["02-visibility"] / "02-01-PLAN.md"
            plan_b.write_text(plan_b_text, encoding="utf-8")

            exit_a = sync.create_issues(str(plan_a))
            exit_b = sync.create_issues(str(plan_b))

            text_a = plan_a.read_text(encoding="utf-8")
            text_b = plan_b.read_text(encoding="utf-8")

        self.assertEqual(exit_a, 0)
        self.assertEqual(exit_b, 0)
        epic_creates = TestCreateIssues._create_argvs(mock_run.call_args_list, "epic")
        self.assertEqual(len(epic_creates), 1)

        epic_a = sync.BEADS_EPIC_RE.search(text_a).group(1)
        epic_b = sync.BEADS_EPIC_RE.search(text_b).group(1)
        self.assertEqual(epic_a, epic_b)

    @mock.patch("subprocess.run")
    def test_resolve_epic_routes_to_milestone_when_epic_per_milestone(self, mock_run):
        """Direct proof of the routing behavior (not just its consequence):
        the one epic-create call issued names the milestone title, never a
        ROADMAP phase header -- resolve_phase_epic/get_phase_header's
        fallback path was never reached."""
        mock_run.side_effect = _make_milestone_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path, phase_dirs = _write_milestone_workspace(
                Path(tmp), ["01-substrate"], epic_per="milestone"
            )
            epic_id, needs_write, stale = sync.resolve_epic(
                "",
                str(tmp_path / ".planning" / "ROADMAP.md"),
                "01",
                phase_dirs["01-substrate"],
                tmp_path,
            )

        self.assertTrue(needs_write)
        self.assertIsNone(stale)
        epic_creates = TestCreateIssues._create_argvs(mock_run.call_args_list, "epic")
        self.assertEqual(len(epic_creates), 1)
        self.assertEqual(epic_creates[0][2], "Milestone v1.0: milestone")
        self.assertEqual(epic_id, "milestone-epic.1")

    def test_capability_json_declares_epic_per_enum_key(self):
        project_root = sync.find_project_root(Path(__file__).resolve().parent)
        cap_path = project_root / ".gsd" / "capabilities" / "beads" / "capability.json"
        cap = json.loads(cap_path.read_text(encoding="utf-8"))
        epic_per_cfg = cap["config"]["beads.epic_per"]
        self.assertEqual(epic_per_cfg["type"], "enum")
        self.assertEqual(epic_per_cfg["values"], ["phase", "milestone"])
        self.assertEqual(epic_per_cfg["default"], "phase")

    @mock.patch("subprocess.run")
    def test_default_unchanged(self, mock_run):
        """With .planning/config.json absent, resolve_epic's edited
        signature (+project_root) introduces zero regression on the default
        per-phase-epic path -- byte-for-byte the same outcome
        TestPhaseScopedEpic::test_second_plan_in_phase_reuses_first_plans_epic_when_neither_preset_one
        already asserts."""
        mock_run.side_effect = _make_bd_side_effect()
        plan_a_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        plan_b_text = plan_a_text.replace("plan: 01", "plan: 02", 1)
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = _write_plan_workspace(Path(tmp), plan_a_text)
            plan_b = plan_a.parent / "01-02-PLAN.md"
            plan_b.write_text(plan_b_text, encoding="utf-8")

            exit_a = sync.create_issues(str(plan_a))
            exit_b = sync.create_issues(str(plan_b))

            text_a = plan_a.read_text(encoding="utf-8")
            text_b = plan_b.read_text(encoding="utf-8")

        self.assertEqual(exit_a, 0)
        self.assertEqual(exit_b, 0)
        epic_creates = TestCreateIssues._create_argvs(mock_run.call_args_list, "epic")
        self.assertEqual(len(epic_creates), 1)
        epic_a = sync.BEADS_EPIC_RE.search(text_a).group(1)
        epic_b = sync.BEADS_EPIC_RE.search(text_b).group(1)
        self.assertEqual(epic_a, epic_b)

    @mock.patch("subprocess.run")
    def test_existing_phase_epic_not_reused_as_milestone_epic(self, mock_run):
        """D-10 forward-only guard, the direct regression test named by
        Task 1's reversibility note: a per-phase epic already recorded on a
        sibling phase's plan (its live title a ROADMAP-style phase header,
        not the milestone title format) is never adopted as the milestone
        epic -- a fresh epic is created instead."""
        seed_titles = {"existing-phase-epic.1": "Phase 3: Enforcement"}
        mock_run.side_effect = _make_milestone_bd_side_effect(seed_titles)
        plan_a_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path, phase_dirs = _write_milestone_workspace(
                Path(tmp), ["03-enforcement", "04-adoption"], epic_per="milestone"
            )
            seeded_plan_text = plan_a_text.replace(
                "---\nphase: 01-substrate\n",
                "---\nphase: 03-enforcement\nbeads_epic: existing-phase-epic.1\n",
                1,
            )
            (phase_dirs["03-enforcement"] / "03-01-PLAN.md").write_text(
                seeded_plan_text, encoding="utf-8"
            )

            synced_plan_text = plan_a_text.replace("phase: 01-substrate", "phase: 04-adoption", 1)
            synced_plan = phase_dirs["04-adoption"] / "04-01-PLAN.md"
            synced_plan.write_text(synced_plan_text, encoding="utf-8")

            exit_code = sync.create_issues(str(synced_plan))
            resolved_text = synced_plan.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        resolved_epic = sync.BEADS_EPIC_RE.search(resolved_text).group(1)
        self.assertNotEqual(resolved_epic, "existing-phase-epic.1")
        epic_creates = TestCreateIssues._create_argvs(mock_run.call_args_list, "epic")
        self.assertEqual(len(epic_creates), 1)
        self.assertEqual(epic_creates[0][2], "Milestone v1.0: milestone")


if __name__ == "__main__":
    unittest.main()
