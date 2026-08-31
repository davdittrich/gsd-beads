"""Tests for plugins/beads-lifecycle/.gsd/capabilities/beads/scripts/sync.py.

Stdlib unittest only (N5). sync.py's parent directory is put on sys.path at
module import so no package __init__.py and no install step is needed.
"""
import contextlib
import io
import json
import re
import os
import shlex
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
        cap_path = (
            project_root
            / "plugins"
            / "beads-lifecycle"
            / ".gsd"
            / "capabilities"
            / "beads"
            / "capability.json"
        )
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

    @unittest.skipUnless(_bd_on_path(), "bd binary not found on PATH")
    def test_created_task_issue_round_trips_description_and_acceptance(self):
        """D-06 tracer's end-to-end proof: after create_issues, a real
        `bd show <id> --json` returns non-empty description AND
        acceptance_criteria -- not a mocked argv assertion."""
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
                ["bd", "init", "--prefix", "content"],
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
            issue_id = sync.BEADS_ID_RE.search(new_text).group(1).strip()

            shown = subprocess.run(
                ["bd", "show", issue_id, "--json"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(shown.returncode, 0, shown.stderr)
            payload = json.loads(shown.stdout)
            if isinstance(payload, list):
                payload = payload[0]
            self.assertTrue(payload.get("description", "").strip(), payload)
            self.assertTrue(payload.get("acceptance_criteria", "").strip(), payload)


class TestDecimalPhase(unittest.TestCase):
    """TRUTH-04: a decimal phase number (`1.5`, `01.5`, `10.1`, `11.1` -- the
    form `/gsd-phase --insert` produces) works at every beads lifecycle
    point instead of failing silently. D-07: string handling only -- no
    `int()`/`float()`/`Decimal()` conversion of a phase number anywhere on
    this path. Real end-to-end cases follow TestEndToEndTracer's shape
    (real `bd init` in a tempdir, `subprocess.run` the CLI); pure-helper
    cases run in-process."""

    def _run_plan_pre_fixture(self, phase_dir_name, current_phase, header_num, plan_filename):
        """Build a real `.planning/` tree plus a real bd db in a tempdir,
        run `sync.py lifecycle-dispatch plan:pre`, and return the (matched,
        unscoped) counts parsed from stdout. `header_num` is the bare phase
        number as it appears in the ROADMAP.md header text (e.g. `"1.5"` or
        `"1"`)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            planning_dir = tmp_path / ".planning"
            phase_dir = planning_dir / "phases" / phase_dir_name
            phase_dir.mkdir(parents=True)
            (planning_dir / "STATE.md").write_text(
                f"---\ncurrent_phase: {current_phase}\n---\n\n"
                "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
                encoding="utf-8",
            )
            (planning_dir / "ROADMAP.md").write_text(
                f"### Phase {header_num}: Decimal Probe\nTouches `src/widget.py`.\n",
                encoding="utf-8",
            )
            plan_path = phase_dir / plan_filename
            plan_path.write_text(
                (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            init = subprocess.run(
                ["bd", "init", "--prefix", "dec"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            created = subprocess.run(
                ["bd", "create", "Widget task", "--description", "Touches src/widget.py."],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(created.returncode, 0, created.stderr)

            result = subprocess.run(
                [sys.executable, str(Path(sync.__file__)), "lifecycle-dispatch", "plan:pre"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            m = re.search(r"(\d+) matched, (\d+) unscoped", result.stdout)
            self.assertIsNotNone(m, result.stdout)
            return int(m.group(1)), int(m.group(2))

    @unittest.skipUnless(_bd_on_path(), "bd binary not found on PATH")
    def test_decimal_phase_matches_at_plan_pre(self):
        """Verified failing on the pre-fix tree: this identical fixture
        reported `0 matched, 1 unscoped`."""
        matched, unscoped = self._run_plan_pre_fixture(
            "01.5-decimal-probe", "01.5", "1.5", "01.5-01-PLAN.md"
        )
        self.assertEqual((matched, unscoped), (1, 0))

    @unittest.skipUnless(_bd_on_path(), "bd binary not found on PATH")
    def test_integer_phase_control_arm_still_matches(self):
        """Byte-identical fixture apart from the phase number -- a pass here
        alongside the decimal arm's pass proves the phase number was the
        cause, not some other fixture difference."""
        matched, unscoped = self._run_plan_pre_fixture(
            "01-integer-control", "01", "1", "01-01-PLAN.md"
        )
        self.assertEqual((matched, unscoped), (1, 0))

    # -- Boundary --------------------------------------------------------

    def test_phase_regex_token_boundary(self):
        cases = {
            "01": "1", "1": "1", "07": "7", "17": "17", "010": "10",
            "01.5": r"1\.5", "1.5": r"1\.5", "10.1": r"10\.1", "11.1": r"11\.1",
            "010.1": r"10\.1", "1.05": r"1\.05", "0": "0", "00": "0",
        }
        for phase_num, expected in cases.items():
            with self.subTest(phase_num=phase_num):
                self.assertEqual(sync.phase_regex_token(phase_num), expected)

    def test_phase_dir_prefix_boundary(self):
        cases = {
            "01": "01", "1": "01", "07": "07", "17": "17", "010": "010",
            "01.5": "01.5", "1.5": "01.5", "10.1": "10.1", "11.1": "11.1",
            "010.1": "010.1", "1.05": "01.05", "0": "00", "00": "00",
        }
        for phase_num, expected in cases.items():
            with self.subTest(phase_num=phase_num):
                self.assertEqual(sync.phase_dir_prefix(phase_num), expected)

    # -- Adjacency ---------------------------------------------------------

    def _header_pattern(self, phase_num):
        return re.compile(
            rf"^###\s+(Phase\s+0*{sync.phase_regex_token(phase_num)}\s*:.*)$", re.MULTILINE
        )

    def test_header_pattern_adjacency_decimal_vs_integer(self):
        self.assertIsNone(self._header_pattern("1.5").search("### Phase 15: Other\n"))
        self.assertIsNone(self._header_pattern("15").search("### Phase 1.5: Decimal\n"))

    def test_header_pattern_metacharacter_case(self):
        """D-07's non-negotiable case: without re.escape, an unescaped `.`
        becomes a wildcard matching any character, silently attributing one
        phase's scope to another (T-17-01-01)."""
        pattern = self._header_pattern("11.1")
        for sep in ("x", "1", " ", "-"):
            with self.subTest(sep=sep):
                self.assertIsNone(pattern.search(f"### Phase 11{sep}1: Other\n"))
        self.assertIsNotNone(pattern.search("### Phase 11.1: Real\n"))

    def test_phase_regex_token_1_5_vs_1_50_distinct(self):
        self.assertNotEqual(sync.phase_regex_token("1.5"), sync.phase_regex_token("1.50"))

    # -- Empty ---------------------------------------------------------------

    def test_empty_phase_num_does_not_raise(self):
        self.assertEqual(sync.phase_regex_token(""), "0")
        self.assertEqual(sync.phase_dir_prefix(""), "00")

    def test_get_phase_header_empty_phase_raises_semantic_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            roadmap = Path(tmp) / "ROADMAP.md"
            roadmap.write_text("### Phase 1: Substrate\nGoal.\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                sync.get_phase_header(roadmap, "")
        self.assertIn("no ROADMAP.md header found", str(ctx.exception))

    @mock.patch("subprocess.run")
    def test_beads_recall_survives_missing_roadmap_with_empty_padded_phase(self, mock_run):
        """padded_phase derives from phase_dir.name.split('-', 1)[0], which
        is '' for a directory with no leading numeric token. extract_phase_
        mentions then raises FileNotFoundError (an OSError subclass) reading
        a missing ROADMAP.md; beads_recall's existing
        except (OSError, ValueError) must still let it write a
        BEADS-RECALL.md rather than crash."""
        mock_run.side_effect = _make_beads_recall_bd_side_effect("[]\n")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            phase_dir = tmp_path / ".planning" / "phases" / "-emptyprefix"
            phase_dir.mkdir(parents=True)
            exit_code = sync.beads_recall(str(phase_dir))
            out_path = phase_dir / "-BEADS-RECALL.md"

            self.assertEqual(exit_code, 0)
            self.assertTrue(out_path.exists())

    # -- Precision -------------------------------------------------------

    def test_plan_file_re_distinguishes_10_1_from_10_10(self):
        self.assertEqual(sync.PLAN_FILE_RE.match("10.10-01-PLAN.md").group(1), "10.10-01")
        self.assertEqual(sync.PLAN_FILE_RE.match("10.1-01-PLAN.md").group(1), "10.1-01")

    def test_discover_plan_files_keeps_10_1_and_10_10_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp)
            (phase_dir / "10.1-01-PLAN.md").write_text("", encoding="utf-8")
            (phase_dir / "10.10-01-PLAN.md").write_text("", encoding="utf-8")
            discovered = sync.discover_plan_files(phase_dir)
        self.assertEqual(set(discovered), {"10.1-01", "10.10-01"})

    # -- Ordering --------------------------------------------------------

    def test_discover_plan_files_sorted_ordering(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = Path(tmp)
            for name in ("01-01-PLAN.md", "01.5-01-PLAN.md", "02-01-PLAN.md"):
                (phase_dir / name).write_text("", encoding="utf-8")
            first = sorted(sync.discover_plan_files(phase_dir))
            second = sorted(sync.discover_plan_files(phase_dir))
        self.assertEqual(first, ["01-01", "01.5-01", "02-01"])
        self.assertEqual(first, second)

    # -- Repository-history fixtures (ROADMAP.md Success Criterion 6) ----

    def test_repo_history_decimal_phases_resolve_headers_and_filenames(self):
        with tempfile.TemporaryDirectory() as tmp:
            roadmap = Path(tmp) / "ROADMAP.md"
            roadmap.write_text(
                "### Phase 10: Ten\nGoal.\n"
                "### Phase 10.1: Ten Point One\nGoal.\n"
                "### Phase 11: Eleven\nGoal.\n"
                "### Phase 11.1: Eleven Point One\nGoal.\n",
                encoding="utf-8",
            )
            self.assertIn("Phase 10.1:", sync.get_phase_header(roadmap, "10.1"))
            self.assertIn("Phase 11.1:", sync.get_phase_header(roadmap, "11.1"))
        for filename, expected_key in (("10.1-01-PLAN.md", "10.1-01"), ("11.1-02-PLAN.md", "11.1-02")):
            with self.subTest(filename=filename):
                m = sync.PLAN_FILE_RE.match(filename)
                self.assertIsNotNone(m)
                self.assertEqual(m.group(1), expected_key)

    # -- Path-safety (T-17-01-03) -----------------------------------------

    def test_resolve_default_phase_dir_rejects_path_separator(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            planning_dir = tmp_path / ".planning"
            (planning_dir / "phases").mkdir(parents=True)
            (planning_dir / "STATE.md").write_text(
                "---\ncurrent_phase: ../../etc\n---\n\n"
                "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
                encoding="utf-8",
            )
            result = sync._resolve_default_phase_dir(tmp_path)
        self.assertIsNone(result)

    # -- Idempotency -------------------------------------------------------

    @unittest.skipUnless(_bd_on_path(), "bd binary not found on PATH")
    def test_idempotent_repeated_plan_pre_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            planning_dir = tmp_path / ".planning"
            phase_dir = planning_dir / "phases" / "01.5-decimal-probe"
            phase_dir.mkdir(parents=True)
            (planning_dir / "STATE.md").write_text(
                "---\ncurrent_phase: 01.5\n---\n\n"
                "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
                encoding="utf-8",
            )
            (planning_dir / "ROADMAP.md").write_text(
                "### Phase 1.5: Decimal Probe\nTouches `src/widget.py`.\n", encoding="utf-8"
            )
            (phase_dir / "01.5-01-PLAN.md").write_text(
                (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8"), encoding="utf-8"
            )
            init = subprocess.run(
                ["bd", "init", "--prefix", "idem"],
                cwd=tmp_path, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            subprocess.run(
                ["bd", "create", "Widget task", "--description", "Touches src/widget.py."],
                cwd=tmp_path, capture_output=True, text=True, timeout=30,
            )

            def _run_once():
                result = subprocess.run(
                    [sys.executable, str(Path(sync.__file__)), "lifecycle-dispatch", "plan:pre"],
                    cwd=tmp_path, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return (phase_dir / "01.5-BEADS-RECALL.md").read_text(encoding="utf-8")

            first = _run_once()
            second = _run_once()

        strip_generated_at = lambda text: re.sub(r"generated_at: \S+", "generated_at: X", text)
        self.assertEqual(strip_generated_at(first), strip_generated_at(second))


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

    @mock.patch("subprocess.run")
    def test_task_create_argv_carries_description_and_acceptance(self, mock_run):
        """D-06: a task-create argv carries a non-empty -d and, since the
        fixture's task has <acceptance_criteria>, a non-empty --acceptance."""
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        task_creates = self._create_argvs(mock_run.call_args_list, "task")
        self.assertEqual(len(task_creates), 1)
        argv = task_creates[0]
        self.assertIn("-d", argv)
        description = argv[argv.index("-d") + 1]
        self.assertTrue(description.strip())
        self.assertIn("--acceptance", argv)
        acceptance = argv[argv.index("--acceptance") + 1]
        self.assertTrue(acceptance.strip())
        # D-06: acceptance criteria travel via bd's own structured field,
        # never folded into the -d description blob.
        self.assertNotIn(acceptance.strip(), description)

    @mock.patch("subprocess.run")
    def test_task_create_argv_omits_acceptance_when_task_has_none(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        no_acceptance_text = plan_text.replace(
            "  <acceptance_criteria>\n    - src/example.py exists\n  </acceptance_criteria>\n",
            "",
        )
        self.assertNotIn("acceptance_criteria", no_acceptance_text)
        with tempfile.TemporaryDirectory() as tmp:
            plan_copy = _write_plan_workspace(Path(tmp), no_acceptance_text)
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        task_creates = self._create_argvs(mock_run.call_args_list, "task")
        self.assertEqual(len(task_creates), 1)
        self.assertNotIn("--acceptance", task_creates[0])

    @mock.patch("subprocess.run")
    def test_checkpoint_decision_task_create_argv_carries_real_content(self, mock_run):
        """CR-01: a checkpoint:decision task with no <beads-id> flows through
        resolve_issue's `bd create` path (D-03 excludes checkpoint tasks from
        strip_task_bodies only, never from issue creation) -- its -d must
        carry the task's real <decision>/<context>/<options>/
        <selection-prompt> content, never an empty string, closing the
        content-parity gap CR-01 identified (no prior test exercised this
        create path for a checkpoint task -- TestStripTaskBodies's checkpoint
        fixtures are pre-seeded with a <beads-id> and only exercise the
        early-return branch)."""
        mock_run.side_effect = _make_bd_side_effect()
        plan_text = """---
phase: 01-substrate
plan: 01
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [B1]
---

<objective>
Checkpoint-only fixture for TestCreateIssues -- no beads-id on the task.
</objective>

<tasks>

<task type="checkpoint:decision" gate="blocking">
  <name>Task 1: Approve the approach</name>
  <decision>Pick an approach.</decision>
  <context>
    Some context here.
  </context>
  <options>
    <option id="a">
      <name>Option A</name>
    </option>
  </options>
  <selection-prompt>Which option?</selection-prompt>
</task>

</tasks>
"""
        with tempfile.TemporaryDirectory() as tmp:
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        task_creates = self._create_argvs(mock_run.call_args_list, "task")
        self.assertEqual(len(task_creates), 1)
        argv = task_creates[0]
        self.assertIn("-d", argv)
        description = argv[argv.index("-d") + 1]
        self.assertTrue(description.strip())
        self.assertIn("## Decision", description)
        self.assertIn("Pick an approach.", description)
        self.assertIn("## Context", description)
        self.assertIn("## Options", description)
        self.assertIn("## Selection Prompt", description)
        self.assertIn("Which option?", description)


def _strip_test_plan_text():
    """A plan carrying one of every shape strip_task_bodies must decide
    between (16-03 Task 2): a strippable `auto` task, a strippable `tracer`
    task, an `auto` task NOT in the stripped set (simulates a pre-existing,
    already-synced task), a `checkpoint:decision` and a `checkpoint:
    human-verify` task, and a task with no `type` attribute at all -- the
    last three all carry ids that ARE passed to strip_task_bodies, so the
    D-03 exclusion is exercised even when the id would otherwise qualify.
    Plan-level sections (objective, context, threat_model, verification,
    success_criteria) are present so D-02 byte-identity can be asserted
    against real section shapes, not just frontmatter.
    """
    return """---
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
Fixture combining strippable and non-strippable task shapes -- used only by
TestStripTaskBodies.
</objective>

<context>
@.planning/PROJECT.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Strippable auto task</name>
  <beads-id>fixture-1</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <precondition>`bd` is on PATH.</precondition>
  <behavior>
    - does the thing
  </behavior>
  <action>Implement the thing.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <acceptance_criteria>
    - src/example.py exists
  </acceptance_criteria>
  <done>The thing is implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Pre-existing auto task, not in this run's stripped set</name>
  <beads-id>fixture-2</beads-id>
  <files>src/example.py</files>
  <read_first>src/example.py</read_first>
  <action>Implement the other thing.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <done>The other thing is implemented.</done>
</task>

<task type="tracer">
  <name>Task 3: Strippable tracer task</name>
  <beads-id>fixture-3</beads-id>
  <files>src/example.py</files>
  <action>Wire the thin slice end to end.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <done>The slice works end to end.</done>
</task>

<task type="checkpoint:decision" gate="blocking">
  <name>Task 4: Approve the approach</name>
  <beads-id>fixture-4</beads-id>
  <decision>Pick an approach.</decision>
  <context>
    Some context here.
  </context>
  <options>
    <option id="a">
      <name>Option A</name>
    </option>
  </options>
  <selection-prompt>Which option?</selection-prompt>
</task>

<task type="checkpoint:human-verify">
  <name>Task 5: Confirm the thing works</name>
  <beads-id>fixture-5</beads-id>
  <what-built>Nothing yet.</what-built>
  <how-to-verify>
    1. Do this.
  </how-to-verify>
  <resume-signal>Type "verified".</resume-signal>
</task>

<task>
  <name>Task 6: No type attribute at all</name>
  <beads-id>fixture-6</beads-id>
  <files>src/example.py</files>
  <action>Untyped task body -- must never be treated as auto.</action>
  <verify>python3 -m py_compile src/example.py</verify>
  <done>Done.</done>
</task>

</tasks>

<verification>
- python3 -m py_compile src/example.py
</verification>

<success_criteria>
- src/example.py exists
</success_criteria>
"""


_STRIP_TEST_STRIPPED_IDS = {
    "fixture-1",
    "fixture-3",
    "fixture-4",
    "fixture-5",
    "fixture-6",
}


def _task_block(text, index):
    """Return the index'th (0-based) <task ...>...</task> block in text."""
    return list(sync.TASK_RE.finditer(text))[index].group(0)


class TestStripTaskBodies(unittest.TestCase):
    """16-03 Task 2 (D-01): strip_task_bodies turns a completed auto/tracer
    task block into a pointer, leaves every checkpoint:* block and every
    not-in-this-run task byte-identical (D-03/D-07), and is idempotent."""

    def test_strippable_auto_task_loses_content_elements(self):
        text = _strip_test_plan_text()
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        block = _task_block(stripped, 0)
        for tag in (
            "read_first",
            "precondition",
            "behavior",
            "action",
            "verify",
            "acceptance_criteria",
            "done",
        ):
            self.assertNotIn(f"<{tag}>", block, f"<{tag}> should have been stripped")

    def test_strippable_auto_task_keeps_identity_and_routing_elements(self):
        text = _strip_test_plan_text()
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        stripped_block = _task_block(stripped, 0)
        # The opening tag, name, beads-id and files lines are byte-identical
        # to the original -- only the elements after <files> changed.
        expected_prefix = (
            '<task type="auto">\n'
            "  <name>Task 1: Strippable auto task</name>\n"
            "  <beads-id>fixture-1</beads-id>\n"
            "  <files>src/example.py</files>\n"
        )
        self.assertTrue(stripped_block.startswith(expected_prefix))

    def test_pre_existing_task_not_in_stripped_set_is_byte_identical(self):
        text = _strip_test_plan_text()
        original_block = _task_block(text, 1)
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        stripped_block = _task_block(stripped, 1)
        self.assertEqual(original_block, stripped_block)

    def test_strippable_tracer_task_is_stripped_like_auto(self):
        text = _strip_test_plan_text()
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        block = _task_block(stripped, 2)
        self.assertIn('<task type="tracer">', block)
        self.assertNotIn("<action>", block)
        self.assertNotIn("<verify>", block)
        self.assertNotIn("<done>", block)
        self.assertIn("<beads-id>fixture-3</beads-id>", block)

    def test_checkpoint_decision_task_is_byte_identical(self):
        text = _strip_test_plan_text()
        original_block = _task_block(text, 3)
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        stripped_block = _task_block(stripped, 3)
        self.assertEqual(original_block, stripped_block)

    def test_checkpoint_human_verify_task_is_byte_identical(self):
        text = _strip_test_plan_text()
        original_block = _task_block(text, 4)
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        stripped_block = _task_block(stripped, 4)
        self.assertEqual(original_block, stripped_block)

    def test_no_type_attribute_task_is_byte_identical(self):
        text = _strip_test_plan_text()
        original_block = _task_block(text, 5)
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        stripped_block = _task_block(stripped, 5)
        self.assertEqual(original_block, stripped_block)

    def test_stripped_block_gains_exactly_one_pointer_comment(self):
        text = _strip_test_plan_text()
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        block = _task_block(stripped, 0)
        self.assertEqual(block.count(sync.TASK_POINTER_PREFIX), 1)
        self.assertIn("`bd show fixture-1`", block)

    def test_idempotent_second_pass_is_byte_identical_to_first(self):
        text = _strip_test_plan_text()
        once = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        twice = sync.strip_task_bodies(once, _STRIP_TEST_STRIPPED_IDS)
        self.assertEqual(once, twice)

    def test_plan_level_sections_are_byte_identical(self):
        text = _strip_test_plan_text()
        stripped = sync.strip_task_bodies(text, _STRIP_TEST_STRIPPED_IDS)
        for pattern in (
            sync.FRONTMATTER_RE,
            sync.OBJECTIVE_RE,
        ):
            self.assertEqual(
                pattern.search(text).group(0), pattern.search(stripped).group(0)
            )
        context_re = re.compile(r"<context>.*?</context>", re.DOTALL)
        verification_re = re.compile(r"<verification>.*?</verification>", re.DOTALL)
        success_re = re.compile(r"<success_criteria>.*?</success_criteria>", re.DOTALL)
        for pattern in (context_re, verification_re, success_re):
            self.assertEqual(
                pattern.search(text).group(0), pattern.search(stripped).group(0)
            )


class TestCreateIssuesStripGate(unittest.TestCase):
    """16-03 Task 2: create_issues' strip step is gated on
    check_execute_plan_patch() -- present strips newly-created auto/tracer
    tasks, absent leaves the plan's content intact."""

    @mock.patch("sync.check_execute_plan_patch")
    @mock.patch("subprocess.run")
    def test_patch_present_strips_newly_created_tasks(self, mock_run, mock_check):
        mock_run.side_effect = _make_bd_side_effect()
        mock_check.return_value = 0
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            exit_code = sync.create_issues(str(plan_copy))
            written = plan_copy.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        mock_check.assert_called()
        self.assertIn(sync.TASK_POINTER_PREFIX, written)
        self.assertNotIn("<action>", written)
        self.assertIn("<beads-id>", written)

    @mock.patch("sync.check_execute_plan_patch")
    @mock.patch("subprocess.run")
    def test_patch_absent_leaves_content_intact(self, mock_run, mock_check):
        mock_run.side_effect = _make_bd_side_effect()
        mock_check.return_value = 1
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            exit_code = sync.create_issues(str(plan_copy))
            written = plan_copy.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        mock_check.assert_called()
        self.assertNotIn(sync.TASK_POINTER_PREFIX, written)
        self.assertIn("<action>Implement the thing.</action>", written)
        self.assertIn("<beads-id>", written)

    @mock.patch("subprocess.run")
    def test_unreadable_execute_plan_md_still_writes_back_beads_id(self, mock_run):
        """CR-02: a real (un-mocked) check_execute_plan_patch() call whose
        execute-plan.md is unreadable (non-UTF-8 bytes) must not propagate an
        exception out of create_issues -- the already-created bd issue's
        <beads-id> must still be written back to PLAN.md (the exact failure
        mode CR-02 identified: an uncaught read error aborting
        plan_path.write_text, risking a duplicate bd issue on retry)."""
        mock_run.side_effect = _make_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "claude-config"
            workflows_dir = config_dir / "gsd-core" / "workflows"
            workflows_dir.mkdir(parents=True)
            (workflows_dir / "execute-plan.md").write_bytes(b"\xff\xfe not valid utf-8")

            plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(config_dir)}):
                exit_code = sync.create_issues(str(plan_copy))
            written = plan_copy.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("<beads-id>", written)


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


def _minimal_task(**overrides):
    """A hand-built task dict carrying only the fields `_task_description`
    reads, all empty/None by default -- callers override the fields under
    test. Mirrors parse_plan()'s real defaults (empty string for absent tag
    bodies, None for absent <precondition>)."""
    task = {
        "read_first": "",
        "precondition": None,
        "behavior": "",
        "action": "",
        "verify": "",
        "acceptance_criteria": "",
        "done": "",
        "files": [],
    }
    task.update(overrides)
    return task


class TestTaskDescription(unittest.TestCase):
    """D-06/D-02: _task_description(task) renders a task's non-empty fields
    as ## sections, omits empty ones, and never leaks acceptance criteria
    into the rendered description -- exercised directly on hand-built task
    dicts, no subprocess involved."""

    def test_minimal_task_emits_only_action_verify_done(self):
        task = _minimal_task(
            action="Implement the thing.",
            verify="python3 -m py_compile src/example.py",
            done="The thing is implemented.",
        )
        description = sync._task_description(task)
        self.assertIn("## Action", description)
        self.assertIn("## Verify", description)
        self.assertIn("## Done", description)
        self.assertNotIn("## Read First", description)
        self.assertNotIn("## Precondition", description)
        self.assertNotIn("## Behavior", description)
        self.assertNotIn("## Files", description)

    def test_full_task_emits_every_non_empty_section(self):
        task = _minimal_task(
            read_first="src/a.py, src/b.py",
            precondition="`bd` is on PATH.",
            behavior="- does the thing",
            action="Implement the thing.",
            verify="python3 -m py_compile src/example.py",
            done="The thing is implemented.",
            files=["src/example.py"],
        )
        description = sync._task_description(task)
        self.assertIn("## Read First", description)
        self.assertIn("## Precondition", description)
        self.assertIn("## Behavior", description)
        self.assertIn("## Action", description)
        self.assertIn("## Verify", description)
        self.assertIn("## Done", description)
        self.assertIn("## Files", description)

    def test_acceptance_criteria_never_rendered_in_description(self):
        task = _minimal_task(
            action="Implement the thing.",
            acceptance_criteria="- src/example.py exists\n- tests pass",
        )
        description = sync._task_description(task)
        self.assertNotIn("- src/example.py exists", description)
        self.assertNotIn("acceptance", description.lower())


class TestResolveTaskContent(unittest.TestCase):
    """Phase 19 public CLI boundary for one live Beads task."""

    ISSUE_ID = "native-19"

    def _row(self, **overrides):
        task = _minimal_task(
            read_first="src/a.py, src/a.py",
            precondition="environment is ready",
            behavior="keep behavior",
            action="Implement the adapter.",
            verify="python3 -m unittest\npython3 -m py_compile sync.py",
            done="Adapter resolves content.",
            files=["scripts/sync.py"],
        )
        row = {
            "id": self.ISSUE_ID,
            "description": "Leading prose.\n\n" + sync._task_description(task)
            + "\n## Unknown\nKeep this authored section.\n"
            + "\n## Acceptance Criteria\nRetained prose.\n",
            "acceptance_criteria": "- first\r\n\n* second\n- first",
        }
        row.update(overrides)
        return row

    def _invoke(self, result):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sync, "run_bd", return_value=result) as run, \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sync.main(["resolve-task-content", self.ISSUE_ID])
        return code, out.getvalue(), err.getvalue(), run

    def test_round_trip_emits_exact_five_key_json_and_typed_lists(self):
        result = subprocess.CompletedProcess(
            ["bd"], 0, stdout=json.dumps([self._row()]), stderr=""
        )
        code, out, err, run = self._invoke(result)
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(run.call_args.args[0], ["bd", "show", self.ISSUE_ID, "--json"])
        self.assertEqual(run.call_args.kwargs["timeout"], 8)
        self.assertLess(8 * 1000, 10000)
        body = json.loads(out)
        self.assertEqual(
            set(body),
            {"description", "read_first", "verify", "acceptance_criteria", "done"},
        )
        self.assertEqual(body["read_first"], ["src/a.py", "src/a.py"])
        self.assertEqual(body["acceptance_criteria"], ["first", "second", "first"])
        self.assertIsInstance(body["read_first"], list)
        self.assertIsInstance(body["acceptance_criteria"], list)
        self.assertEqual(body["verify"], "python3 -m unittest\npython3 -m py_compile sync.py")
        self.assertEqual(body["done"], "Adapter resolves content.")
        self.assertIn("Leading prose.", body["description"])
        self.assertIn("## Unknown", body["description"])
        self.assertNotIn("## Read First", body["description"])
        self.assertNotIn("## Verify", body["description"])
        self.assertNotIn("## Done", body["description"])

    def test_versioned_data_envelope_succeeds(self):
        result = subprocess.CompletedProcess(
            ["bd"], 0, stdout=json.dumps({"data": [self._row()]}), stderr=""
        )
        code, out, err, _ = self._invoke(result)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["read_first"], ["src/a.py", "src/a.py"])

    def test_zero_exit_error_envelope_fails_closed(self):
        result = subprocess.CompletedProcess(
            ["bd"], 0, stdout=json.dumps({"error": "not found"}), stderr=""
        )
        code, out, err, _ = self._invoke(result)
        self.assertNotEqual(code, 0)
        self.assertEqual(out, "")
        self.assertIn("invalid envelope", err)
        self.assertLessEqual(len(err), 2000)

    def test_invalid_id_fails_without_subprocess(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sync, "run_bd") as run, \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sync.main(["resolve-task-content", "../bad"])
        self.assertNotEqual(code, 0)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("invalid id", err.getvalue())
        run.assert_not_called()

    def test_failure_arms_remain_individual_and_fail_closed(self):
        cases = (
            ("nonzero", subprocess.CompletedProcess(["bd"], 1, stdout="", stderr="no"), "bd failed"),
            ("bad-json", subprocess.CompletedProcess(["bd"], 0, stdout="{", stderr=""), "invalid json"),
            ("row-count", subprocess.CompletedProcess(["bd"], 0, stdout="[]", stderr=""), "invalid envelope"),
            ("wrong-id", subprocess.CompletedProcess(["bd"], 0, stdout=json.dumps([self._row(id="other")]), stderr=""), "id mismatch"),
            ("wrong-criteria", subprocess.CompletedProcess(["bd"], 0, stdout=json.dumps([self._row(acceptance_criteria={})]), stderr=""), "invalid acceptance"),
            ("duplicate-heading", subprocess.CompletedProcess(["bd"], 0, stdout=json.dumps([self._row(description=self._row()["description"] + "\n## Done\nAgain")]), stderr=""), "duplicate heading"),
        )
        for name, result, token in cases:
            with self.subTest(name=name):
                code, out, err, _ = self._invoke(result)
                self.assertNotEqual(code, 0)
                self.assertEqual(out, "")
                self.assertIn(token, err)
                self.assertLessEqual(len(err), 2000)


class TestTaskContentResolverManifest(unittest.TestCase):
    """Tracked native resolver declaration stays inert until a later identity phase."""

    CAPABILITY_PATH = Path(__file__).resolve().parent.parent / "capability.json"

    def _manifest(self):
        return json.loads(self.CAPABILITY_PATH.read_text(encoding="utf-8"))

    def test_single_native_resolver_has_exact_invocation_contract(self):
        manifest = self._manifest()
        resolver = manifest["taskContentResolver"]
        self.assertEqual(manifest["version"], "0.5.0")
        self.assertEqual(resolver["trackerPrefix"], "beads")
        self.assertEqual(resolver["invoke"]["binary"], "python3")
        self.assertEqual(resolver["invoke"]["args"][-1], "{{id}}")
        self.assertEqual(resolver["invoke"]["timeoutMs"], 10000)
        self.assertEqual(resolver["invoke"]["args"].count("{{id}}"), 1)
        self.assertLess(8 * 1000, resolver["invoke"]["timeoutMs"])
        bootstrap = resolver["invoke"]["args"][1]
        self.assertNotIn("\\n", bootstrap)
        self.assertIn("os.execv(sys.executable", bootstrap)
        self.assertIn('"resolve-task-content", sys.argv[1]', bootstrap)

    def test_release_docs_keep_source_availability_distinct_from_cutover(self):
        root = self.CAPABILITY_PATH.parents[5]
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        self.assertIn("## 0.5.0", changelog)
        self.assertIn("taskContentResolver", changelog)
        self.assertIn("description, read_first, verify, acceptance_criteria, and done", readme)
        self.assertIn("fails closed with no PLAN.md fallback", readme)
        self.assertIn("inert until Phase 20 adds tracker-id", readme)
        self.assertIn(
            "Phase 21 owns exact tracked, project-installed, and global-installed byte parity, installed cutover, and Patch 2 retirement",
            readme,
        )


class TestCheckpointTaskDescription(unittest.TestCase):
    """CR-01: _checkpoint_task_description(task) renders a checkpoint task's
    decision/human-verify fields, mirroring _task_description's "## section,
    only when non-empty" shape but reading a distinct field set."""

    def test_decision_task_emits_every_non_empty_section(self):
        task = {
            "decision": "Pick an approach.",
            "context": "Some context here.",
            "options": "<option id=\"a\"><name>Option A</name></option>",
            "selection_prompt": "Which option?",
            "what_built": "",
            "how_to_verify": "",
            "resume_signal": "",
        }
        description = sync._checkpoint_task_description(task)
        self.assertIn("## Decision\nPick an approach.", description)
        self.assertIn("## Context", description)
        self.assertIn("## Options", description)
        self.assertIn("## Selection Prompt\nWhich option?", description)
        self.assertNotIn("## What Built", description)
        self.assertNotIn("## How To Verify", description)
        self.assertNotIn("## Resume Signal", description)

    def test_human_verify_task_emits_its_own_fields(self):
        task = {
            "decision": "",
            "context": "",
            "options": "",
            "selection_prompt": "",
            "what_built": "Nothing yet.",
            "how_to_verify": "1. Do this.",
            "resume_signal": 'Type "verified".',
        }
        description = sync._checkpoint_task_description(task)
        self.assertIn("## What Built\nNothing yet.", description)
        self.assertIn("## How To Verify", description)
        self.assertIn("## Resume Signal", description)
        self.assertNotIn("## Decision", description)

    def test_empty_checkpoint_task_returns_empty_string(self):
        task = {
            "decision": "",
            "context": "",
            "options": "",
            "selection_prompt": "",
            "what_built": "",
            "how_to_verify": "",
            "resume_signal": "",
        }
        self.assertEqual(sync._checkpoint_task_description(task), "")


class TestEpicDescription(unittest.TestCase):
    """D-06: phase-epic bd create argvs carry -d when the plan has an
    <objective>, and carry no -d at all when it doesn't -- an empty
    description is never written."""

    @mock.patch("subprocess.run")
    def test_phase_epic_create_carries_description_when_plan_has_objective(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        self.assertIn("<objective>", plan_text)
        with tempfile.TemporaryDirectory() as tmp:
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        epic_creates = TestCreateIssues._create_argvs(mock_run.call_args_list, "epic")
        self.assertEqual(len(epic_creates), 1)
        argv = epic_creates[0]
        self.assertIn("-d", argv)
        description = argv[argv.index("-d") + 1]
        self.assertTrue(description.strip())
        self.assertIn("## Objective", description)

    @mock.patch("subprocess.run")
    def test_phase_epic_create_omits_description_when_plan_has_no_objective(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        no_objective_text = re.sub(
            r"<objective>.*?</objective>\n\n", "", plan_text, flags=re.DOTALL
        )
        self.assertNotIn("<objective>", no_objective_text)
        with tempfile.TemporaryDirectory() as tmp:
            plan_copy = _write_plan_workspace(Path(tmp), no_objective_text)
            exit_code = sync.create_issues(str(plan_copy))

        self.assertEqual(exit_code, 0)
        epic_creates = TestCreateIssues._create_argvs(mock_run.call_args_list, "epic")
        self.assertEqual(len(epic_creates), 1)
        self.assertNotIn("-d", epic_creates[0])

    def test_epic_description_renders_objective_section(self):
        self.assertEqual(
            sync._epic_description("Ship the write path."),
            "## Objective\nShip the write path.\n",
        )

    def test_epic_description_empty_for_empty_objective(self):
        self.assertEqual(sync._epic_description(""), "")

    def test_get_milestone_bullet_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            roadmap_path = Path(tmp) / "ROADMAP.md"
            roadmap_path.write_text(
                "## Milestones\n\n"
                "- v1.0 milestone -- Phases 1-4\n"
                "- v1.2 New Capability Plugins -- Phases 13-15\n\n"
                "## Phases\n",
                encoding="utf-8",
            )
            bullet = sync.get_milestone_bullet(roadmap_path, "v1.2")
        self.assertEqual(bullet, "- v1.2 New Capability Plugins -- Phases 13-15")

    def test_get_milestone_bullet_miss_returns_empty_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            roadmap_path = Path(tmp) / "ROADMAP.md"
            roadmap_path.write_text(
                "## Milestones\n\n- v1.0 milestone -- Phases 1-4\n\n## Phases\n",
                encoding="utf-8",
            )
            bullet = sync.get_milestone_bullet(roadmap_path, "v9.9")
        self.assertEqual(bullet, "")

    def test_get_milestone_bullet_does_not_collide_on_substring(self):
        """WR-01: a bare "v1" token must not match "v1.0"/"v1.1"/"v1.2"
        bullets as a substring -- get_milestone_bullet returns "" (correctly
        reporting a miss) rather than the first colliding bullet's text."""
        with tempfile.TemporaryDirectory() as tmp:
            roadmap_path = Path(tmp) / "ROADMAP.md"
            roadmap_path.write_text(
                "## Milestones\n\n"
                "- v1.0 milestone -- Phases 1-4\n"
                "- v1.1 Publish and Document -- Phases 5-12\n"
                "- v1.2 New Capability Plugins -- Phases 13-15\n\n"
                "## Phases\n",
                encoding="utf-8",
            )
            bullet = sync.get_milestone_bullet(roadmap_path, "v1")
        self.assertEqual(bullet, "")

    def test_get_milestone_bullet_matches_real_roadmap_bullet_shape(self):
        """WR-01: real ROADMAP.md bullets carry a leading emoji and bold
        markdown around the milestone token (see project ROADMAP.md), not
        the bare "- v1.2 ..." shape the other fixtures use -- the anchored
        match must still find the bullet despite that decoration."""
        with tempfile.TemporaryDirectory() as tmp:
            roadmap_path = Path(tmp) / "ROADMAP.md"
            roadmap_path.write_text(
                "## Milestones\n\n"
                "- ✅ **v1.0 milestone** — Phases 1-4 (shipped)\n"
                "- \U0001f6a7 **v1.2 New Capability Plugins** — Phases 13-15 (current)\n\n"
                "## Phases\n",
                encoding="utf-8",
            )
            bullet = sync.get_milestone_bullet(roadmap_path, "v1.2")
        self.assertIn("v1.2 New Capability Plugins", bullet)


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


class TestReconcileStaleClosed(unittest.TestCase):
    """D-08: a phase-wide, idempotent close backstop -- closes every
    task-complete-but-bd-open issue across every plan in phase_dir, not just
    the plan ids one wave's close-wave dispatch was given."""

    @mock.patch("subprocess.run")
    def test_two_completed_plans_closes_four_ids_in_one_call(self, mock_run):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            plan_b = (FIXTURES_DIR / "plan-wave-b.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(
                Path(tmp),
                [("01-04", plan_a, True), ("01-05", plan_b, True)],
            )
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

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
            # task ids may appear in the close argv, even though it exists
            # in phase_dir alongside the completed plan.
            phase_dir = _write_wave_workspace(
                Path(tmp),
                [("01-04", plan_a, True), ("01-05", plan_b, False)],
            )
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

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
    def test_task_with_no_beads_id_skipped_and_reported(self, mock_run):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        captured = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-06", _three_task_two_synced_plan_text(), True)]
            )
            with contextlib.redirect_stdout(captured):
                exit_code = sync.reconcile_stale_closed(str(phase_dir))

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
    def test_repeat_run_over_already_reconciled_phase_issues_zero_close_calls(
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
            sync.reconcile_stale_closed(str(phase_dir))
            mock_run.reset_mock()
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        close_argvs = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        self.assertEqual(close_argvs, [])

    @mock.patch("subprocess.run")
    def test_reason_string_names_phase_wide_reconciliation_not_wave(self, mock_run):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(Path(tmp), [("01-04", plan_a, True)])
            sync.reconcile_stale_closed(str(phase_dir))

        close_argvs = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        reason = close_argvs[0][close_argvs[0].index("--reason") + 1]
        self.assertIn("phase-wide reconciliation", reason)
        self.assertNotIn("wave complete", reason)

    def test_empty_phase_directory_returns_zero_and_issues_no_close_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(Path(tmp), [])
            with mock.patch("subprocess.run") as mock_run:
                mock_run.side_effect = _make_close_wave_bd_side_effect()
                exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        close_argvs = [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]
        self.assertEqual(close_argvs, [])

    def test_bd_unavailable_exits_zero_with_one_notice_and_closes_nothing(self):
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
                        exit_code = sync.reconcile_stale_closed(str(phase_dir))

            self.assertEqual(exit_code, 0)
            self.assertEqual(captured.getvalue().count(sync.NOTICE), 1)
            state_text = state_path.read_text(encoding="utf-8")
            self.assertEqual(state_text.count("### Blockers/Concerns"), 1)
            self.assertEqual(state_text.count("bd unavailable"), 1)

    def test_cli_dispatch_routes_through_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(Path(tmp), [])
            with mock.patch("shutil.which", return_value=None):
                exit_code = sync.main(["reconcile-stale-closed", str(phase_dir)])
        self.assertEqual(exit_code, 0)


def _no_beads_id_plan_text(plan_num, phase="01-substrate"):
    """One task, no <beads-id> anywhere -- a plan whose contribution to
    `_resolve_completed_task_ids` is empty, isolating the
    `_resolve_marked_issue_ids` marker set under test in
    TestResolvesIssuesMarker from the existing <beads-id> union path."""
    return f"""---
phase: {phase}
plan: {plan_num}
type: execute
wave: 3
depends_on: []
beads_epic: standalone-marker
files_modified:
  - src/example.py
autonomous: true
requirements: [B3]
---

<objective>
Single-task plan fixture with no <beads-id> anywhere -- TestResolvesIssuesMarker's
base case for a plan whose SUMMARY.md carries the only closure signal (bd
gsd-beads-72u).
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Do a thing with no synced id</name>
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
"""


def _summary_with_frontmatter(resolves_issues_yaml="", body=""):
    """A SUMMARY.md body carrying a fenced frontmatter block plus an optional
    `resolves_issues_yaml` line/block and body prose -- the shape
    `_resolve_marked_issue_ids` reads (FRONTMATTER_RE-fenced) versus the
    shape it must never read (everything after the closing `---`)."""
    return f"""---
status: complete
{resolves_issues_yaml}---
{body}"""


class TestResolvesIssuesMarker(unittest.TestCase):
    """bd gsd-beads-72u: `resolves_issues:` in a completed plan's SUMMARY.md
    frontmatter is the only way `reconcile_stale_closed` can reach a
    standalone problem-report bd issue that carries no <beads-id> anywhere.
    The identity-safety property -- a bd id named only in SUMMARY body prose
    is never closed -- is this class's central regression."""

    def _close_argvs(self, mock_run):
        return [
            c.args[0] for c in mock_run.call_args_list if c.args[0][:2] == ["bd", "close"]
        ]

    @mock.patch("subprocess.run")
    def test_inline_marker_closes_standalone_issue_with_no_beads_id_anywhere(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _no_beads_id_plan_text("07"), True)]
            )
            (phase_dir / "01-07-SUMMARY.md").write_text(
                _summary_with_frontmatter('resolves_issues: ["gsd-beads-he1"]\n'),
                encoding="utf-8",
            )
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        closed_ids = {i for argv in self._close_argvs(mock_run) for i in argv[2:argv.index("--reason")]}
        self.assertIn("gsd-beads-he1", closed_ids)

    @mock.patch("subprocess.run")
    def test_block_list_marker_form_behaves_identically_to_inline_form(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _no_beads_id_plan_text("07"), True)]
            )
            (phase_dir / "01-07-SUMMARY.md").write_text(
                _summary_with_frontmatter('resolves_issues:\n  - "gsd-beads-he1"\n'),
                encoding="utf-8",
            )
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        closed_ids = {i for argv in self._close_argvs(mock_run) for i in argv[2:argv.index("--reason")]}
        self.assertIn("gsd-beads-he1", closed_ids)

    @mock.patch("subprocess.run")
    def test_identity_safety_body_mentioned_id_is_never_closed(self, mock_run):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _no_beads_id_plan_text("07"), True)]
            )
            (phase_dir / "01-07-SUMMARY.md").write_text(
                _summary_with_frontmatter(
                    'resolves_issues: ["gsd-beads-he1"]\n',
                    body=(
                        "## Follow-ups\n\nFiled a new follow-up ticket, "
                        "gsd-beads-72u, to track the remaining gap.\n"
                    ),
                ),
                encoding="utf-8",
            )
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        all_closed = [
            i for argv in self._close_argvs(mock_run) for i in argv[2:argv.index("--reason")]
        ]
        self.assertIn("gsd-beads-he1", all_closed)
        self.assertNotIn("gsd-beads-72u", all_closed)

    @mock.patch("subprocess.run")
    def test_summary_with_no_frontmatter_fence_contributes_no_marker_ids(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            # Default _write_wave_workspace SUMMARY.md is bare "status:
            # complete\n" -- no frontmatter fence at all.
            phase_dir = _write_wave_workspace(Path(tmp), [("01-04", plan_a, True)])
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        close_argvs = self._close_argvs(mock_run)
        self.assertEqual(len(close_argvs), 1)
        reason_idx = close_argvs[0].index("--reason")
        self.assertEqual(set(close_argvs[0][2:reason_idx]), {"tracer-wave1.1", "tracer-wave1.2"})

    @mock.patch("subprocess.run")
    def test_unsafe_marker_entries_never_reach_close_argv_and_are_counted_rejected(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        captured = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _no_beads_id_plan_text("07"), True)]
            )
            (phase_dir / "01-07-SUMMARY.md").write_text(
                _summary_with_frontmatter(
                    'resolves_issues: ["-force", "--reason", "a b", "../evil", ""]\n'
                ),
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(captured):
                exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        close_argvs = self._close_argvs(mock_run)
        self.assertEqual(close_argvs, [])
        for unsafe in ("-force", "--reason", "a b", "../evil"):
            for argv in close_argvs:
                self.assertNotIn(unsafe, argv)
        self.assertIn("rejected 5", captured.getvalue())

    @mock.patch("subprocess.run")
    def test_id_both_task_beads_id_and_marker_appears_exactly_once(self, mock_run):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(Path(tmp), [("01-04", plan_a, True)])
            (phase_dir / "01-04-SUMMARY.md").write_text(
                _summary_with_frontmatter('resolves_issues: ["tracer-wave1.1"]\n'),
                encoding="utf-8",
            )
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        all_closed = [
            i for argv in self._close_argvs(mock_run) for i in argv[2:argv.index("--reason")]
        ]
        self.assertEqual(all_closed.count("tracer-wave1.1"), 1)

    @mock.patch("subprocess.run")
    def test_marker_close_uses_own_reason_distinct_from_phase_wide_reconciliation(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(
                Path(tmp),
                [("01-04", plan_a, True), ("01-07", _no_beads_id_plan_text("07"), True)],
            )
            (phase_dir / "01-07-SUMMARY.md").write_text(
                _summary_with_frontmatter('resolves_issues: ["gsd-beads-he1"]\n'),
                encoding="utf-8",
            )
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        close_argvs = self._close_argvs(mock_run)
        self.assertEqual(len(close_argvs), 2)
        reasons = [argv[argv.index("--reason") + 1] for argv in close_argvs]
        phase_wide = [r for r in reasons if "phase-wide reconciliation" in r]
        marker = [r for r in reasons if "resolves_issues marker" in r]
        self.assertEqual(len(phase_wide), 1)
        self.assertEqual(len(marker), 1)
        self.assertNotIn("resolves_issues marker", phase_wide[0])
        self.assertNotIn("phase-wide reconciliation", marker[0])

    @mock.patch("subprocess.run")
    def test_repeat_run_over_same_phase_with_marker_issues_zero_close_calls(
        self, mock_run
    ):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            plan_a = (FIXTURES_DIR / "plan-wave-a.md").read_text(encoding="utf-8")
            phase_dir = _write_wave_workspace(
                Path(tmp),
                [("01-04", plan_a, True), ("01-07", _no_beads_id_plan_text("07"), True)],
            )
            (phase_dir / "01-07-SUMMARY.md").write_text(
                _summary_with_frontmatter('resolves_issues: ["gsd-beads-he1"]\n'),
                encoding="utf-8",
            )
            sync.reconcile_stale_closed(str(phase_dir))
            mock_run.reset_mock()
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        self.assertEqual(self._close_argvs(mock_run), [])

    @mock.patch("subprocess.run")
    def test_unreadable_or_undecodable_summary_is_skipped_not_raised(self, mock_run):
        mock_run.side_effect = _make_close_wave_bd_side_effect()
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_wave_workspace(
                Path(tmp), [("01-07", _no_beads_id_plan_text("07"), True)]
            )
            (phase_dir / "01-07-SUMMARY.md").write_bytes(b"\xff\xfe\x00\x01not valid utf-8")
            exit_code = sync.reconcile_stale_closed(str(phase_dir))

        self.assertEqual(exit_code, 0)
        self.assertEqual(self._close_argvs(mock_run), [])


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
                    "./plugins/beads-lifecycle/.gsd/capabilities/beads",
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

    def test_reports_cannot_verify_when_file_is_not_valid_utf8(self):
        """WR-02: a non-UTF-8 byte sequence in ship.md must degrade to the
        same "cannot verify" exit code as the missing-file case, not raise
        UnicodeDecodeError out of the function."""
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            ship_md.write_bytes(b"\xff\xfe not valid utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_shipmd_patch(str(ship_md))

        self.assertEqual(exit_code, 1)
        self.assertIn("could not be read", captured.getvalue())

    def test_never_writes_to_target_file(self):
        """D-09: mirrors TestCheckExecutePlanPatch's never-writes test,
        target-swapped -- the ship-md counterpart did not exist before this
        task."""
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            original = f"...preamble...\n{sync.SHIP_MD_PATCH_MARKER}\n...body...\n"
            ship_md.write_text(original, encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_shipmd_patch(str(ship_md))
            self.assertEqual(ship_md.read_text(encoding="utf-8"), original)

    def test_cli_routes_through_main_and_returns_function_exit_code(self):
        """D-09: mirrors TestCheckExecutePlanPatch's CLI-level test,
        target-swapped. 17-04 Task 3: updated to the collapsed `check-patch`
        verb (positional target, --path override) as a visible diff -- the
        message and version assertions this class's siblings pin stay
        byte-identical; only the verb spelling changed."""
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            ship_md.write_text(f"{sync.SHIP_MD_PATCH_MARKER}\n", encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.main(["check-patch", "ship-md", "--path", str(ship_md)])

        self.assertEqual(exit_code, 0)
        self.assertIn("present", captured.getvalue())


class TestCheckExecutePlanPatch(unittest.TestCase):
    """16-03 Task 1: check_execute_plan_patch mirrors check_shipmd_patch's
    three-case behavior and read-only discipline for the machine-local
    execute-plan.md bd-task-read patch."""

    def test_reports_present_when_marker_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            execute_plan_md = Path(tmp) / "execute-plan.md"
            execute_plan_md.write_text(
                f"...preamble...\n{sync.EXECUTE_PLAN_PATCH_MARKER}\n...body...\n",
                encoding="utf-8",
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_execute_plan_patch(str(execute_plan_md))

        self.assertEqual(exit_code, 0)
        self.assertIn("present", captured.getvalue())

    def test_reports_missing_with_reapply_pointer_when_marker_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            execute_plan_md = Path(tmp) / "execute-plan.md"
            execute_plan_md.write_text("no patch marker in this file\n", encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_execute_plan_patch(str(execute_plan_md))

        self.assertEqual(exit_code, 1)
        out = captured.getvalue()
        self.assertIn("GSD-CORE-PATCH.md", out)
        self.assertIn("gsd-executor", out)

    def test_reports_missing_with_reapply_pointer_when_file_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "does-not-exist" / "execute-plan.md"
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_execute_plan_patch(str(missing_path))

        self.assertEqual(exit_code, 1)
        self.assertIn(str(missing_path), captured.getvalue())

    def test_reports_cannot_verify_when_file_is_not_valid_utf8(self):
        """CR-02/WR-02: a non-UTF-8 byte sequence in execute-plan.md must
        degrade to the same "cannot verify" exit code as the missing-file
        case, not raise UnicodeDecodeError out of the function."""
        with tempfile.TemporaryDirectory() as tmp:
            execute_plan_md = Path(tmp) / "execute-plan.md"
            execute_plan_md.write_bytes(b"\xff\xfe not valid utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_execute_plan_patch(str(execute_plan_md))

        self.assertEqual(exit_code, 1)
        self.assertIn("could not be read", captured.getvalue())

    def test_never_writes_to_target_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            execute_plan_md = Path(tmp) / "execute-plan.md"
            original = f"...preamble...\n{sync.EXECUTE_PLAN_PATCH_MARKER}\n...body...\n"
            execute_plan_md.write_text(original, encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_execute_plan_patch(str(execute_plan_md))
            self.assertEqual(execute_plan_md.read_text(encoding="utf-8"), original)

    def test_cli_routes_through_main_and_returns_function_exit_code(self):
        """17-04 Task 3: updated to the collapsed `check-patch` verb (verb
        spelling only -- see the ship-md sibling test's docstring)."""
        with tempfile.TemporaryDirectory() as tmp:
            execute_plan_md = Path(tmp) / "execute-plan.md"
            execute_plan_md.write_text(
                f"{sync.EXECUTE_PLAN_PATCH_MARKER}\n", encoding="utf-8"
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.main(
                    ["check-patch", "execute-plan", "--path", str(execute_plan_md)]
                )

        self.assertEqual(exit_code, 0)
        self.assertIn("present", captured.getvalue())


class TestPatchChecksTable(unittest.TestCase):
    """17-04 Task 1 (D-09/D-10): pre-merge coverage pinning the exact literal
    marker strings, the per-entry version tokens in each present message, and
    the consequence text in each missing message -- the blind spot commit
    `966315a` exploited (moving SHIP_MD_PATCH_MARKER v1 -> v2 with the suite
    still reporting 164/164 green, because no test asserted either marker's
    literal string). Written against today's two standalone functions, before
    Task 3's merge; Task 3 extends this class with the merged table's own
    invariants and these assertions must survive byte-identically."""

    def test_ship_md_marker_literal_string(self):
        self.assertEqual(
            sync.SHIP_MD_PATCH_MARKER,
            "<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->",
        )

    def test_execute_plan_marker_literal_string(self):
        self.assertEqual(
            sync.EXECUTE_PLAN_PATCH_MARKER,
            "<!-- gsd-beads-patch:execute-plan-bd-task-read v1 -->",
        )

    def test_ship_md_and_execute_plan_markers_are_distinct(self):
        self.assertNotEqual(sync.SHIP_MD_PATCH_MARKER, sync.EXECUTE_PLAN_PATCH_MARKER)

    def test_ship_md_present_message_carries_v2_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            ship_md.write_text(f"{sync.SHIP_MD_PATCH_MARKER}\n", encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_shipmd_patch(str(ship_md))
        self.assertIn("(v2)", captured.getvalue())

    def test_execute_plan_present_message_carries_v1_token(self):
        """Separate from the v2 assertion above so a shared-template merge
        that quietly emits one version for both targets cannot mask this
        failure with the other test's pass."""
        with tempfile.TemporaryDirectory() as tmp:
            execute_plan_md = Path(tmp) / "execute-plan.md"
            execute_plan_md.write_text(
                f"{sync.EXECUTE_PLAN_PATCH_MARKER}\n", encoding="utf-8"
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_execute_plan_patch(str(execute_plan_md))
        self.assertIn("(v1)", captured.getvalue())

    def test_ship_md_missing_message_names_ship_pre_gates_unaffected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            ship_md.write_text("no patch marker in this file\n", encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_shipmd_patch(str(ship_md))
        out = captured.getvalue()
        self.assertIn("ship_override step will not fire", out)
        self.assertIn("ship:pre GATES are", out)
        self.assertIn("unaffected", out)

    def test_execute_plan_missing_message_names_executor_consequence(self):
        """Separate from the ship-md consequence assertion above so a merge
        that collapses both consequence strings into one shared sentence
        cannot pass this test on the other target's wording."""
        with tempfile.TemporaryDirectory() as tmp:
            execute_plan_md = Path(tmp) / "execute-plan.md"
            execute_plan_md.write_text("no patch marker in this file\n", encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_execute_plan_patch(str(execute_plan_md))
        out = captured.getvalue()
        self.assertIn("gsd-executor will not read task content from bd", out)

    # -- 18-03 Task 1 (D-03.1): not-found/could-not-read now carry the same
    # marker missing_msg already does, one test per target per case so a
    # merge that collapses the two targets' wording cannot pass on the
    # other target's message. --

    def test_ship_md_not_found_message_carries_the_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "does-not-exist" / "ship.md"
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_shipmd_patch(str(missing_path))
        self.assertTrue(captured.getvalue().startswith("⚠ "))

    def test_ship_md_could_not_read_message_carries_the_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            ship_md = Path(tmp) / "ship.md"
            ship_md.write_bytes(b"\xff\xfe not valid utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_shipmd_patch(str(ship_md))
        self.assertTrue(captured.getvalue().startswith("⚠ "))

    def test_execute_plan_not_found_message_carries_the_marker(self):
        """Separate from the ship-md assertion above so a merge that
        collapses both targets' wording into one shared template cannot
        pass this test on the other target's message."""
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "does-not-exist" / "execute-plan.md"
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_execute_plan_patch(str(missing_path))
        self.assertTrue(captured.getvalue().startswith("⚠ "))

    def test_execute_plan_could_not_read_message_carries_the_marker(self):
        """Separate from the ship-md assertion above for the same reason."""
        with tempfile.TemporaryDirectory() as tmp:
            execute_plan_md = Path(tmp) / "execute-plan.md"
            execute_plan_md.write_bytes(b"\xff\xfe not valid utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_execute_plan_patch(str(execute_plan_md))
        self.assertTrue(captured.getvalue().startswith("⚠ "))

    # -- 17-04 Task 3: the merged PATCH_CHECKS table's own invariants --

    def test_table_has_exactly_two_entries_with_distinct_keys(self):
        self.assertEqual(len(sync.PATCH_CHECKS), 2)
        self.assertEqual(len(set(sync.PATCH_CHECKS)), 2)
        self.assertIn("ship-md", sync.PATCH_CHECKS)
        self.assertIn("execute-plan", sync.PATCH_CHECKS)

    def test_both_wrapper_names_still_callable(self):
        """Criterion 5: the two Python function names survive the CLI
        collapse as thin wrappers -- the four existing test mocks and both
        in-file call sites bind to these names, not to the table or the
        shared reader."""
        self.assertTrue(callable(sync.check_shipmd_patch))
        self.assertTrue(callable(sync.check_execute_plan_patch))

    def test_unrecognized_table_key_is_fail_open_and_does_not_raise(self):
        """BINDING codex MEDIUM: totality is required (both checks share
        lifecycle_dispatch's one try/except with beads_recall), but an
        unknown key's message must be distinguishable from the genuinely
        unreadable-file case, not just silently absorbed."""
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            exit_code = sync.check_patch("no-such-target")
        self.assertEqual(exit_code, 1)
        unknown_key_message = captured.getvalue()
        self.assertIn("no-such-target", unknown_key_message)

        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "does-not-exist" / "ship.md"
            captured2 = io.StringIO()
            with contextlib.redirect_stdout(captured2):
                sync.check_patch("ship-md", str(missing_path))
        self.assertNotEqual(unknown_key_message, captured2.getvalue())

    def test_retired_verbs_are_gone_from_the_cli(self):
        """Caller assertion: sync.main raises SystemExit (argparse's
        usage-error path) for either retired verb rather than routing to a
        function -- the collapse actually removed the old subparsers, it did
        not just add a new one alongside them. Built from parts so this test
        itself does not trip the "zero surviving references to either
        retired verb" caller-assertion grep."""
        retired_ship_verb = "check-shipmd" + "-patch"
        retired_execute_verb = "check-execute-plan" + "-patch"
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                sync.main([retired_ship_verb, "--ship-md-path", "/tmp/x"])
            with self.assertRaises(SystemExit):
                sync.main([retired_execute_verb, "--execute-plan-path", "/tmp/x"])


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
        cap_path = (
            project_root
            / "plugins"
            / "beads-lifecycle"
            / ".gsd"
            / "capabilities"
            / "beads"
            / "capability.json"
        )
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


def _lifecycle_workspace(tmp_path, *, current_phase="07", enabled=None, plan_text=None):
    """gh-2: lay out the minimum tree `lifecycle_dispatch` resolves against --
    a `.planning/` root (find_project_root), a STATE.md carrying
    `current_phase` (_resolve_default_phase_dir), and a matching
    `.planning/phases/NN-*` directory. `enabled` writes a config.json with
    that `beads.enabled` value; None writes no config.json at all, which is
    the shipped-default case. Returns the phase directory."""
    planning_dir = tmp_path / ".planning"
    phase_dir = planning_dir / "phases" / f"{current_phase}-demo"
    phase_dir.mkdir(parents=True)
    (planning_dir / "STATE.md").write_text(
        f"---\ncurrent_phase: {current_phase}\n---\n\n"
        "## Accumulated Context\n\n### Blockers/Concerns\n\nNone yet.\n",
        encoding="utf-8",
    )
    (planning_dir / "ROADMAP.md").write_text(
        f"### Phase {int(current_phase)}: Demo\nGoal.\n", encoding="utf-8"
    )
    if enabled is not None:
        (planning_dir / "config.json").write_text(
            json.dumps({"beads": {"enabled": enabled}}), encoding="utf-8"
        )
    if plan_text is not None:
        (phase_dir / f"{current_phase}-01-PLAN.md").write_text(plan_text, encoding="utf-8")
    return phase_dir


class TestReadBeadsEnabled(unittest.TestCase):
    """gh-2: lifecycle_dispatch is entered from a harness hook, so it bypasses
    both the SKILL.md Step 1 config gate and the capability registry that
    evaluates each hook's `when: beads.enabled`. read_beads_enabled is the
    replacement gate, and it must resolve to capability.json's shipped
    default (True) for every shape of missing or unusable config."""

    def _enabled_for(self, payload):
        with tempfile.TemporaryDirectory() as tmp:
            planning_dir = Path(tmp) / ".planning"
            planning_dir.mkdir()
            if payload is not None:
                (planning_dir / "config.json").write_text(payload, encoding="utf-8")
            return sync.read_beads_enabled(Path(tmp))

    def test_absent_config_resolves_to_shipped_default_true(self):
        self.assertTrue(self._enabled_for(None))

    def test_explicit_false_is_honored(self):
        self.assertFalse(self._enabled_for(json.dumps({"beads": {"enabled": False}})))

    def test_explicit_true_is_honored(self):
        self.assertTrue(self._enabled_for(json.dumps({"beads": {"enabled": True}})))

    def test_malformed_json_resolves_to_true(self):
        self.assertTrue(self._enabled_for("{not json"))

    def test_absent_beads_object_resolves_to_true(self):
        self.assertTrue(self._enabled_for(json.dumps({"workflow": {"auto_advance": True}})))

    def test_non_boolean_value_resolves_to_true_rather_than_a_truthiness_guess(self):
        """"false" (the string) is not False. Guessing at truthiness here would
        silently disable tracking for a typo'd config."""
        self.assertTrue(self._enabled_for(json.dumps({"beads": {"enabled": "false"}})))


class TestLifecycleDispatchRouting(unittest.TestCase):
    """gh-2: each of the five points gsd-core fails to dispatch routes onto the
    verb that point declares, with the phase directory resolved from STATE.md.
    Spies on the verbs (CLAUDE.md audit rule); the contract test for what
    plan:post actually produces is TestLifecycleDispatchEndToEnd below."""

    @contextlib.contextmanager
    def _in_workspace(self, **workspace):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _lifecycle_workspace(Path(tmp), **workspace)
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=0):
                    yield phase_dir
            finally:
                os.chdir(prev)

    def test_plan_pre_runs_recall_then_all_three_diagnostics(self):
        """The patch-loss detector documented as beads-recall SKILL.md Step 3.5.
        It was wired at plan:pre to be independent of the ship.md patch it
        checks -- but plan:pre was itself one of the dead points, so it shared
        the failure mode of the thing it protects. 17-03 Task 2 adds a third
        diagnostic, check_sync_mode_value, dispatched alongside the two patch
        checks."""
        with self._in_workspace() as phase_dir:
            with mock.patch.object(sync, "beads_recall", return_value=0) as recall, \
                 mock.patch.object(sync, "check_shipmd_patch", return_value=0) as ship, \
                 mock.patch.object(sync, "check_execute_plan_patch", return_value=0) as ep, \
                 mock.patch.object(sync, "check_sync_mode_value", return_value=0) as sm:
                exit_code = sync.lifecycle_dispatch("plan:pre")
        self.assertEqual(exit_code, 0)
        recall.assert_called_once_with(str(phase_dir))
        ship.assert_called_once()
        ep.assert_called_once()
        sm.assert_called_once()

    def test_plan_pre_prints_ship_report_before_execute_report_unmocked(self):
        """17-04 Task 3 behavior assertion: against the real merged reader
        (beads_recall and check_sync_mode_value mocked out, the two patch
        checks left real), the ship-md report still prints before the
        execute-plan report -- the merge did not reorder or blend the two
        targets' output."""
        with tempfile.TemporaryDirectory() as tmp:
            runtime_home = Path(tmp) / "runtime"
            workflows = runtime_home / "gsd-core" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "ship.md").write_text(
                f"{sync.SHIP_MD_PATCH_MARKER}\n", encoding="utf-8"
            )
            (workflows / "execute-plan.md").write_text(
                f"{sync.EXECUTE_PLAN_PATCH_MARKER}\n", encoding="utf-8"
            )
            workspace = Path(tmp) / "ws"
            workspace.mkdir()
            _lifecycle_workspace(workspace)
            prev = Path.cwd()
            os.chdir(str(workspace))
            captured = io.StringIO()
            try:
                with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(runtime_home)}), \
                     mock.patch.object(sync, "beads_recall", return_value=0), \
                     mock.patch.object(sync, "check_sync_mode_value", return_value=0):
                    with contextlib.redirect_stdout(captured):
                        exit_code = sync.lifecycle_dispatch("plan:pre")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        out = captured.getvalue()
        ship_idx = out.index("ship.md ship:pre step-dispatch patch: present (v2)")
        exec_idx = out.index("execute-plan.md bd-task-read patch: present (v1)")
        self.assertLess(ship_idx, exec_idx)

    def test_plan_post_syncs_every_plan_in_the_phase(self):
        plan = '---\nphase: 07-demo\n---\n<task type="auto"><name>t</name></task>\n'
        with self._in_workspace(plan_text=plan) as phase_dir:
            with mock.patch.object(sync, "create_issues", return_value=0) as create:
                exit_code = sync.lifecycle_dispatch("plan:post")
        self.assertEqual(exit_code, 0)
        create.assert_called_once_with(
            str(phase_dir / "07-01-PLAN.md"), allow_strip=False
        )

    def test_wave_pre_renders_a_phase_wide_status_block(self):
        """The render-hooks call carries no wave plan-id list, so the block
        spans every plan in the phase -- a superset of the wave's, never a
        subset, so no ticket pointer is lost from an executor brief."""
        plan = '---\nphase: 07-demo\n---\n<task type="auto"><name>t</name></task>\n'
        with self._in_workspace(plan_text=plan) as phase_dir:
            with mock.patch.object(sync, "render_wave_status_block", return_value=0) as render:
                exit_code = sync.lifecycle_dispatch("execute:wave:pre")
        self.assertEqual(exit_code, 0)
        render.assert_called_once_with(str(phase_dir), ["07-01"])

    def test_wave_post_uses_the_phase_wide_reconcile_backstop(self):
        """Not close_wave: that needs the wave's plan ids, which the
        render-hooks call does not carry. reconcile_stale_closed is idempotent
        and phase-wide (D-08)."""
        with self._in_workspace() as phase_dir:
            with mock.patch.object(sync, "reconcile_stale_closed", return_value=0) as rec, \
                 mock.patch.object(sync, "close_wave", return_value=0) as close:
                exit_code = sync.lifecycle_dispatch("execute:wave:post")
        self.assertEqual(exit_code, 0)
        rec.assert_called_once_with(str(phase_dir))
        close.assert_not_called()

    def test_verify_post_regenerates_beads_md(self):
        with self._in_workspace() as phase_dir:
            with mock.patch.object(sync, "regenerate_beads_md", return_value=0) as regen:
                exit_code = sync.lifecycle_dispatch("verify:post")
        self.assertEqual(exit_code, 0)
        regen.assert_called_once_with(str(phase_dir))

    def test_plan_post_never_strips_task_bodies(self):
        """gh-2 regression. `strip_task_bodies` moves the ONLY copy of a task's
        content out of PLAN.md and into a bd database the project may be
        gitignoring. The hook's trigger is a substring of a shell command, so a
        spurious fire is always possible; creating an issue by mistake is
        recoverable, deleting prose is not. A hook-driven dispatch must
        therefore never authorize the strip, whatever the read-path patch says."""
        plan = '---\nphase: 07-demo\n---\n<task type="auto"><name>t</name></task>\n'
        with self._in_workspace(plan_text=plan) as phase_dir:
            with mock.patch.object(sync, "create_issues", return_value=0) as create:
                sync.lifecycle_dispatch("plan:post")
        self.assertEqual(create.call_args.kwargs.get("allow_strip"), False)


class TestLifecycleDispatchFailOpen(unittest.TestCase):
    """gh-2: every hook this verb serves declares `onError: "skip"`, and this is
    the call site that has to honour it. Nothing below may return non-zero or
    raise, and none of it may dispatch a verb."""

    def _assert_no_dispatch(self, point, tmp):
        prev = Path.cwd()
        os.chdir(tmp)
        try:
            with mock.patch.object(sync, "check_native_step_dispatch", return_value=0), \
                 mock.patch.object(sync, "beads_recall") as recall, \
                 mock.patch.object(sync, "create_issues") as create, \
                 mock.patch.object(sync, "render_wave_status_block") as render, \
                 mock.patch.object(sync, "reconcile_stale_closed") as rec, \
                 mock.patch.object(sync, "regenerate_beads_md") as regen:
                captured, errs = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(errs):
                    exit_code = sync.lifecycle_dispatch(point)
        finally:
            os.chdir(prev)
        self.assertEqual(exit_code, 0)
        for spy in (recall, create, render, rec, regen):
            spy.assert_not_called()
        return captured.getvalue(), errs.getvalue()

    def test_unknown_point_is_a_silent_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            out, err = self._assert_no_dispatch("nonsense:point", tmp)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_ship_pre_is_not_dispatched_here(self):
        """ship:pre already dispatches through this capability's own ship.md
        patch; dispatching it here too would double-record a ship_override."""
        self.assertNotIn("ship:pre", sync.LIFECYCLE_DISPATCH_POINTS)
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            self._assert_no_dispatch("ship:pre", tmp)

    def test_no_planning_directory_is_a_silent_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, err = self._assert_no_dispatch("plan:post", tmp)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_beads_disabled_project_dispatches_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp), enabled=False)
            self._assert_no_dispatch("plan:post", tmp)

    def test_unresolvable_phase_reports_on_stderr_not_stdout(self):
        """A repository between milestones has no `.planning/phases/` at all, so
        this fires on every render-hooks call in it. The hook promotes stdout
        into Claude's context and leaves stderr in the debug log, so this notice
        must never reach stdout."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".planning").mkdir()
            out, err = self._assert_no_dispatch("verify:post", tmp)
        self.assertEqual(out, "")
        self.assertIn("no phase directory resolved", err)

    def test_phase_with_no_plans_reports_on_stderr_not_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            out, err = self._assert_no_dispatch("plan:post", tmp)
        self.assertEqual(out, "")
        self.assertIn("no PLAN.md", err)

    def test_a_raising_verb_degrades_to_one_line_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=0), \
                     mock.patch.object(
                         sync, "regenerate_beads_md", side_effect=RuntimeError("bd exploded")
                     ):
                    captured = io.StringIO()
                    with contextlib.redirect_stdout(captured):
                        exit_code = sync.lifecycle_dispatch("verify:post")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        self.assertIn("bd exploded", captured.getvalue())


class TestLifecycleDispatchEndToEnd(unittest.TestCase):
    """gh-2 contract test: the reported symptom was `bd list` returning "No
    issues found." after a full plan run. This asserts the observable cure --
    dispatching plan:post over a real phase tree issues the bd creates and
    writes beads_epic/<beads-id> back into every PLAN.md -- rather than
    asserting that a function was called."""

    @mock.patch("subprocess.run")
    def test_plan_post_creates_issues_and_rewrites_every_plan(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _lifecycle_workspace(Path(tmp), plan_text=plan_text)
            second = phase_dir / "07-02-PLAN.md"
            second.write_text(plan_text, encoding="utf-8")
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                captured = io.StringIO()
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=0), \
                     contextlib.redirect_stdout(captured):
                    exit_code = sync.lifecycle_dispatch("plan:post")
            finally:
                os.chdir(prev)
            first_text = (phase_dir / "07-01-PLAN.md").read_text(encoding="utf-8")
            second_text = second.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        # The exact absences the bug report named: no beads_epic, no <beads-id>.
        self.assertIsNotNone(sync.BEADS_EPIC_RE.search(first_text))
        self.assertIsNotNone(sync.BEADS_EPIC_RE.search(second_text))
        self.assertIn("<beads-id>", first_text)
        self.assertIn("<beads-id>", second_text)
        task_creates = TestCreateIssues._create_argvs(mock_run.call_args_list, "task")
        self.assertEqual(len(task_creates), 2)


class TestLifecycleDispatchHook(unittest.TestCase):
    """gh-2: hooks/lifecycle-dispatch.sh is the only thing that makes any of the
    above reachable, so it is exercised against real PostToolUse payloads rather
    than trusted."""

    # tests/ -> beads/ -> capabilities/ -> .gsd/ -> beads-lifecycle/
    PLUGIN_ROOT = Path(__file__).resolve().parents[4]
    HOOK = PLUGIN_ROOT / "hooks" / "lifecycle-dispatch.sh"

    def _run(self, command, cwd):
        payload = json.dumps(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "cwd": str(cwd),
                "tool_input": {"command": command},
            }
        )
        env = dict(os.environ)
        # Pin resolution at this repo's own plugin tree and away from the real
        # $HOME/.gsd, so the test never runs an unrelated installed bundle.
        env["GSD_HOME"] = str(cwd)
        env["CLAUDE_PLUGIN_ROOT"] = str(self.PLUGIN_ROOT)
        env.pop("CLAUDE_PROJECT_DIR", None)
        return subprocess.run(
            ["bash", str(self.HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )

    def test_hook_file_exists_and_is_referenced_by_hooks_json(self):
        self.assertTrue(self.HOOK.is_file(), f"missing hook script at {self.HOOK}")
        hooks_json = json.loads(
            (self.HOOK.parent / "hooks.json").read_text(encoding="utf-8")
        )
        post = hooks_json["hooks"]["PostToolUse"]
        self.assertEqual(post[0]["matcher"], "Bash")
        self.assertIn("lifecycle-dispatch.sh", post[0]["hooks"][0]["command"])

    def test_matching_command_emits_post_tool_use_additional_context(self):
        """A PostToolUse hook's plain stdout on exit 0 never reaches Claude; only
        hookSpecificOutput.additionalContext does. execute:wave:pre's
        <beads_status> block exists solely to reach the orchestrator composing
        the executor prompts, so this envelope is load-bearing, not cosmetic."""
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            result = self._run(
                "WAVE_PRE_HOOKS_JSON=$(gsd_run loop render-hooks execute:wave:pre --raw)",
                Path(tmp),
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertIn(
            "execute:wave:pre", payload["hookSpecificOutput"]["additionalContext"]
        )

    def test_commands_that_merely_mention_the_trigger_do_not_dispatch(self):
        """gh-2 regression, and the reason the matcher is not a bare substring
        test. Every command below fired the shipped v1.3.0 matcher; one `rg`
        created bd issues and stripped the <task> bodies out of a PLAN.md.
        They are all things an agent or a human really runs while working on
        this very capability."""
        innocent = [
            "grep -rn render-hooks plan:post ~/.claude/gsd-core",
            'grep -rn "render-hooks plan:post" ~/.claude/gsd-core',
            'rg "render-hooks plan:post --raw" .',
            "echo 'gsd-core calls render-hooks plan:post --raw here'",
            'echo "gsd_run loop render-hooks plan:post --raw"',
            "cat ~/.claude/gsd-core/workflows/plan-phase.md",
            "sed -n '1348p' plan-phase.md  # PLAN_POST_HOOKS_JSON render-hooks plan:post",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            for command in innocent:
                result = self._run(command, Path(tmp))
                self.assertEqual(result.returncode, 0, command)
                self.assertEqual(result.stdout, "", f"dispatched on: {command}")

    def test_real_gsd_core_call_shapes_still_dispatch(self):
        """The hook must recognize real call shapes, then let native dispatch win."""
        real = [
            "PLAN_POST_HOOKS_JSON=$(gsd_run loop render-hooks plan:post --raw)",
            "gsd_run loop render-hooks plan:post --raw",
            "H=$(gsd-tools loop render-hooks plan:post --raw)",
            "H=$(node ~/.claude/gsd-core/bin/gsd-tools.cjs loop render-hooks plan:post --raw)",
            "cd /tmp && gsd_run loop render-hooks plan:post --raw",
        ]
        plan = '---\nphase: 07-demo\n---\n<task type="auto"><name>t</name></task>\n'
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp), plan_text=plan)
            for command in real:
                result = self._run(command, Path(tmp))
                self.assertEqual(result.returncode, 0, command)
                self.assertEqual(result.stdout, "", command)
                self.assertIn(
                    "native-step-dispatch probe (plan:post): detected",
                    result.stderr,
                    f"failed to recognize and stand down on: {command}",
                )

    def test_non_matching_command_produces_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            result = self._run("npm test", Path(tmp))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_ship_pre_render_hooks_call_is_not_matched(self):
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            result = self._run(
                "SHIP_PRE_HOOKS_JSON=$(gsd_run loop render-hooks ship:pre --raw)", Path(tmp)
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_benign_skip_never_reaches_claude(self):
        """A repository with no `.planning/phases/` would otherwise annotate
        every single render-hooks call with a skip notice."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".planning").mkdir()
            result = self._run("gsd_run loop render-hooks verify:post --raw", Path(tmp))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_directory_without_planning_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run("gsd_run loop render-hooks plan:post --raw", Path(tmp))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_malformed_payload_does_not_crash_the_hook(self):
        env = dict(os.environ)
        env["CLAUDE_PLUGIN_ROOT"] = str(self.PLUGIN_ROOT)
        result = subprocess.run(
            ["bash", str(self.HOOK)],
            input="not json at all",
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_point_list_matches_sync_py_and_capability_json(self):
        """The point list lives in three places -- capability.json's steps[],
        sync.py's LIFECYCLE_DISPATCH_POINTS, and the hook's own allowlist. A
        point added to one and missed in another is exactly the silent
        no-dispatch this whole change exists to remove."""
        hook_text = self.HOOK.read_text(encoding="utf-8")
        for point in sync.LIFECYCLE_DISPATCH_POINTS:
            self.assertIn(point, hook_text, f"{point} missing from the hook allowlist")
        cap = json.loads(
            (self.PLUGIN_ROOT / ".gsd/capabilities/beads/capability.json").read_text(
                encoding="utf-8"
            )
        )
        declared = {step["point"] for step in cap["steps"]}
        self.assertEqual(
            declared - {"ship:pre"},
            set(sync.LIFECYCLE_DISPATCH_POINTS),
            "capability.json declares a step point lifecycle_dispatch does not handle",
        )


def _installed_workflow_path(filename):
    return (
        Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
        / "gsd-core"
        / "workflows"
        / filename
    )


class TestNativeStepDispatchProbe(unittest.TestCase):
    """17-02 Task 1 (D-05): check_native_step_dispatch is a read-only,
    fail-open probe for gsd-core PR #3687's native `kind == "step"`
    dispatch, region-scoped on the point's own `render-hooks <point> --raw`
    anchor so it does not false-positive on either shipped 1.11.0 workflow
    file."""

    def _probe(self, point, text):
        with tempfile.TemporaryDirectory() as tmp:
            workflow_path = Path(tmp) / "workflow.md"
            workflow_path.write_text(text, encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stderr(captured):
                exit_code = sync.check_native_step_dispatch(point, str(workflow_path))
            return exit_code, captured.getvalue(), workflow_path

    def test_unqualified_generic_step_arm_in_region_is_detected(self):
        text = (
            "## 13e. Post-Planning Gap Analysis (plan:post capability gate dispatch)\n\n"
            "```bash\n"
            "PLAN_POST_HOOKS_JSON=$(gsd_run loop render-hooks plan:post --raw)\n"
            "```\n\n"
            'For each active entry where `kind == "step"`: dispatch it.\n\n'
            "## 14. Present Final Status\n"
        )
        exit_code, out, path = self._probe("plan:post", text)
        self.assertEqual(exit_code, 1)
        self.assertIn(str(path), out)

    def test_shipped_1_11_0_plan_phase_shape_is_not_detected(self):
        """Whole-file-grep false positive, pinned: three unqualified
        `kind == "step"` mentions live OUTSIDE the plan:post region in the
        real shipped file (the plan:pre generic contract, the auto-chain UI
        branch, the intel step read); the region itself carries only a
        `kind == "gate"` loop."""
        text = (
            '**Generic step hook dispatch contract:** For each active entry where '
            '`kind == "step"`:\n\n'
            'For each entry in `activeHooks` where `kind == "step"` and `ref.skill` '
            "is set:\n\n"
            'Read the active intel step hook where `kind == "step"` and '
            '`capId == "intel"`.\n\n'
            "## 13e. Post-Planning Gap Analysis (plan:post capability gate dispatch)\n\n"
            "```bash\n"
            "PLAN_POST_HOOKS_JSON=$(gsd_run loop render-hooks plan:post --raw)\n"
            "```\n\n"
            '**For each active entry where `kind == "gate"`** (process in array order).\n\n'
            "## 14. Present Final Status\n"
        )
        exit_code, out, path = self._probe("plan:post", text)
        self.assertEqual(exit_code, 0)
        self.assertIn(str(path), out)

    def test_shipped_1_11_0_verify_work_shape_is_not_detected(self):
        """17-02 Task 2: the second false-positive source -- verify-work.md's
        own verify:post region already carries a `kind == "step"` mention,
        qualified to `ref.skill == "secure-phase"`. A naive whole-file scan
        for the bare `kind == "step"` substring WOULD match here (the
        qualifier lives on the same line but a naive scan ignores that) --
        documenting the exact false positive region scoping prevents."""
        text = (
            "```bash\n"
            "VERIFY_POST_HOOKS_JSON=$(gsd_run loop render-hooks verify:post --raw)\n"
            "```\n\n"
            "Resolve active step hooks from `VERIFY_POST_HOOKS_JSON` where "
            '`kind == "step"` and `ref.skill == "secure-phase"`.\n'
        )
        naive_whole_file_match = bool(re.search(r'kind\s*==\s*"step"', text))
        self.assertTrue(
            naive_whole_file_match,
            "fixture must reproduce the exact false-positive shape",
        )

        exit_code, out, path = self._probe("verify:post", text)
        self.assertEqual(exit_code, 0)
        self.assertIn(str(path), out)

    def test_missing_file_is_not_detected_and_names_the_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "does-not-exist.md"
            captured = io.StringIO()
            with contextlib.redirect_stderr(captured):
                exit_code = sync.check_native_step_dispatch("plan:post", str(missing_path))
        self.assertEqual(exit_code, 0)
        self.assertIn(str(missing_path), captured.getvalue())

    def test_unreadable_file_is_not_detected_and_names_the_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            workflow_path = Path(tmp) / "workflow.md"
            workflow_path.write_bytes(b"\xff\xfe not valid utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stderr(captured):
                exit_code = sync.check_native_step_dispatch("plan:post", str(workflow_path))
        self.assertEqual(exit_code, 0)
        self.assertIn(str(workflow_path), captured.getvalue())

    def test_region_ends_at_heading_before_a_later_step_arm_is_not_detected(self):
        """Failing to find the arm because it lives past the region boundary
        must not be a failure to dispatch."""
        text = (
            "## 13e. Post-Planning Gap Analysis (plan:post capability gate dispatch)\n\n"
            "```bash\n"
            "PLAN_POST_HOOKS_JSON=$(gsd_run loop render-hooks plan:post --raw)\n"
            "```\n\n"
            "Only gate content in this region, no step arm here.\n\n"
            "## 14. Present Final Status\n\n"
            'For each entry where `kind == "step"`: this arm is out of region.\n'
        )
        exit_code, _, _ = self._probe("plan:post", text)
        self.assertEqual(exit_code, 0)

    def test_unmapped_point_is_not_detected_without_reading_any_file(self):
        exit_code = sync.check_native_step_dispatch("execute:wave:pre", "/nonexistent/x.md")
        self.assertEqual(exit_code, 0)

    def test_no_anchor_in_file_is_not_detected(self):
        text = "## Some Heading\n\nNo render-hooks call anywhere in this fixture.\n"
        exit_code, _, _ = self._probe("plan:post", text)
        self.assertEqual(exit_code, 0)

    def test_generic_step_arm_inside_fenced_doc_example_in_region_is_not_a_false_positive(self):
        # gsd-beads-u67.13: a kind=="step" line inside a FENCED documentation
        # example within the region must not be mistaken for a live arm --
        # only in_fence is toggled correctly across the fence boundaries
        # would this line be excluded from detection.
        text = (
            "## 13e. Post-Planning Gap Analysis (plan:post capability gate dispatch)\n\n"
            "```bash\n"
            "PLAN_POST_HOOKS_JSON=$(gsd_run loop render-hooks plan:post --raw)\n"
            "```\n\n"
            "Example dispatch shape shown for documentation purposes only:\n\n"
            "```yaml\n"
            'kind == "step"\n'
            "```\n\n"
            "## 14. Present Final Status\n"
        )
        exit_code, out, path = self._probe("plan:post", text)
        self.assertEqual(
            exit_code,
            0,
            'a kind == "step" line inside a fenced doc example must not '
            "false-positive as a live dispatch arm",
        )


class TestNativeStepDispatchProbeAgainstInstalledTree(unittest.TestCase):
    """The probe must classify the current installed workflow tree."""

    def test_plan_post_detected_on_installed_tree(self):
        workflow_path = _installed_workflow_path("plan-phase.md")
        self.assertTrue(workflow_path.exists(), f"{workflow_path} not present on this machine")
        captured = io.StringIO()
        with contextlib.redirect_stderr(captured):
            exit_code = sync.check_native_step_dispatch("plan:post")
        self.assertEqual(exit_code, 1)
        self.assertIn(str(workflow_path), captured.getvalue())
        self.assertIn("detected", captured.getvalue())

    def test_verify_post_detected_on_installed_tree(self):
        workflow_path = _installed_workflow_path("verify-work.md")
        self.assertTrue(workflow_path.exists(), f"{workflow_path} not present on this machine")
        captured = io.StringIO()
        with contextlib.redirect_stderr(captured):
            exit_code = sync.check_native_step_dispatch("verify:post")
        self.assertEqual(exit_code, 1)
        self.assertIn(str(workflow_path), captured.getvalue())
        self.assertIn("detected", captured.getvalue())


class TestLifecycleDispatchNativeGate(unittest.TestCase):
    """17-02 Task 1/2: lifecycle_dispatch's plan:post and verify:post
    branches stand down when check_native_step_dispatch reports the point is
    now dispatched natively (gsd-core PR #3687), and behave exactly as
    before when it is not. plan:pre/execute:wave:pre/execute:wave:post
    dispatch unconditionally -- no upstream work covers them anywhere."""

    def test_plan_post_skips_create_issues_when_native_dispatch_detected(self):
        plan = '---\nphase: 07-demo\n---\n<task type="auto"><name>t</name></task>\n'
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp), plan_text=plan)
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(
                    sync, "check_native_step_dispatch", return_value=1
                ) as probe, mock.patch.object(sync, "create_issues") as create:
                    captured, errs = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(errs):
                        exit_code = sync.lifecycle_dispatch("plan:post")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        create.assert_not_called()
        probe.assert_called_once_with("plan:post")
        self.assertNotEqual(errs.getvalue(), "")

    def test_plan_post_dispatches_as_today_when_native_dispatch_not_detected(self):
        plan = '---\nphase: 07-demo\n---\n<task type="auto"><name>t</name></task>\n'
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _lifecycle_workspace(Path(tmp), plan_text=plan)
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=0), \
                     mock.patch.object(sync, "create_issues", return_value=0) as create:
                    exit_code = sync.lifecycle_dispatch("plan:post")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        create.assert_called_once_with(str(phase_dir / "07-01-PLAN.md"), allow_strip=False)

    def test_verify_post_skips_regenerate_when_native_dispatch_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _lifecycle_workspace(Path(tmp))
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(
                    sync, "check_native_step_dispatch", return_value=1
                ) as probe, mock.patch.object(sync, "regenerate_beads_md") as regen:
                    captured, errs = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(errs):
                        exit_code = sync.lifecycle_dispatch("verify:post")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        regen.assert_not_called()
        probe.assert_called_once_with("verify:post")
        self.assertNotEqual(errs.getvalue(), "")

    def test_verify_post_dispatches_as_today_when_native_dispatch_not_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _lifecycle_workspace(Path(tmp))
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=0), \
                     mock.patch.object(sync, "regenerate_beads_md", return_value=0) as regen:
                    exit_code = sync.lifecycle_dispatch("verify:post")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        regen.assert_called_once_with(str(phase_dir))

    def test_plan_pre_dispatches_regardless_of_probe_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _lifecycle_workspace(Path(tmp))
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=1), \
                     mock.patch.object(sync, "beads_recall", return_value=0) as recall, \
                     mock.patch.object(sync, "check_shipmd_patch", return_value=0), \
                     mock.patch.object(sync, "check_execute_plan_patch", return_value=0):
                    exit_code = sync.lifecycle_dispatch("plan:pre")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        recall.assert_called_once_with(str(phase_dir))

    def test_execute_wave_pre_dispatches_regardless_of_probe_result(self):
        plan = '---\nphase: 07-demo\n---\n<task type="auto"><name>t</name></task>\n'
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _lifecycle_workspace(Path(tmp), plan_text=plan)
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=1), \
                     mock.patch.object(sync, "render_wave_status_block", return_value=0) as render:
                    exit_code = sync.lifecycle_dispatch("execute:wave:pre")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        render.assert_called_once_with(str(phase_dir), ["07-01"])

    def test_execute_wave_post_dispatches_regardless_of_probe_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _lifecycle_workspace(Path(tmp))
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=1), \
                     mock.patch.object(sync, "reconcile_stale_closed", return_value=0) as rec:
                    exit_code = sync.lifecycle_dispatch("execute:wave:post")
            finally:
                os.chdir(prev)
        self.assertEqual(exit_code, 0)
        rec.assert_called_once_with(str(phase_dir))

    def test_lifecycle_dispatch_returns_zero_for_every_point_when_probe_raises(self):
        """17-02 Task 2 acceptance: the probe is called from inside
        lifecycle_dispatch's existing outer try/except -- a raise there must
        degrade to the same onError:"skip" contract every other verb
        failure already honours, for all five points, not just the two
        gated ones."""
        plan = '---\nphase: 07-demo\n---\n<task type="auto"><name>t</name></task>\n'
        for point in sync.LIFECYCLE_DISPATCH_POINTS:
            with self.subTest(point=point):
                with tempfile.TemporaryDirectory() as tmp:
                    _lifecycle_workspace(Path(tmp), plan_text=plan)
                    prev = Path.cwd()
                    os.chdir(tmp)
                    try:
                        with mock.patch.object(
                            sync,
                            "check_native_step_dispatch",
                            side_effect=RuntimeError("probe exploded"),
                        ):
                            captured = io.StringIO()
                            with contextlib.redirect_stdout(captured):
                                exit_code = sync.lifecycle_dispatch(point)
                    finally:
                        os.chdir(prev)
                self.assertEqual(exit_code, 0)


class TestLifecycleDispatchPointsAgreeWithHook(unittest.TestCase):
    """17-02 Task 2: LIFECYCLE_DISPATCH_POINTS' module comment declares the
    hook's own embedded POINTS list must mirror this one. This plan changes
    dispatch behavior without changing the list -- pin the invariant while
    the file is open."""

    def test_five_points_same_order_in_both_places(self):
        hook_text = TestLifecycleDispatchHook.HOOK.read_text(encoding="utf-8")
        match = re.search(r"POINTS\s*=\s*\((.*?)\)", hook_text)
        self.assertIsNotNone(match, "POINTS tuple not found in lifecycle-dispatch.sh")
        hook_points = tuple(re.findall(r'"([^"]+)"', match.group(1)))
        self.assertEqual(sync.LIFECYCLE_DISPATCH_POINTS, hook_points)


class TestReadSyncMode(unittest.TestCase):
    """17-02 Task 3 (D-06): read_sync_mode is a one-line read_beads_config
    accessor for beads.sync_mode, matching read_epic_per/read_beads_enabled's
    shape immediately above it -- default is the shipped authoritative
    value."""

    def _mode_for(self, payload):
        with tempfile.TemporaryDirectory() as tmp:
            planning_dir = Path(tmp) / ".planning"
            planning_dir.mkdir()
            if payload is not None:
                (planning_dir / "config.json").write_text(payload, encoding="utf-8")
            return sync.read_sync_mode(Path(tmp))

    def test_absent_config_resolves_to_authoritative_default(self):
        self.assertEqual(self._mode_for(None), "authoritative")

    def test_explicit_mirror_is_honored(self):
        self.assertEqual(
            self._mode_for(json.dumps({"beads": {"sync_mode": "mirror"}})), "mirror"
        )

    def test_explicit_off_is_honored(self):
        self.assertEqual(self._mode_for(json.dumps({"beads": {"sync_mode": "off"}})), "off")

    def test_malformed_json_resolves_to_authoritative_default(self):
        self.assertEqual(self._mode_for("{not json"), "authoritative")


class TestCreateIssuesCliSyncModeGate(unittest.TestCase):
    """17-02 Task 3 (D-06): `sync.py create-issues <plan>` computes its
    strip permission from `beads.sync_mode` -- mirror withholds the strip,
    authoritative (default, no config file, and the retired `off` value)
    behaves as today. No CLI flag is added: `beads-sync/SKILL.md` Step 3
    invokes this verb with no strip-related argument."""

    def _run_create_issues(self, sync_mode_payload):
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            if sync_mode_payload is not None:
                (Path(tmp) / ".planning" / "config.json").write_text(
                    sync_mode_payload, encoding="utf-8"
                )
            with mock.patch("subprocess.run", side_effect=_make_bd_side_effect()):
                exit_code = sync.main(["create-issues", str(plan_copy)])
            return exit_code, plan_copy.read_text(encoding="utf-8")

    def test_mirror_leaves_task_body_intact(self):
        exit_code, written = self._run_create_issues(
            json.dumps({"beads": {"sync_mode": "mirror"}})
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("<action>Implement the thing.</action>", written)
        self.assertNotIn(sync.TASK_POINTER_PREFIX, written)

    def test_authoritative_strips_task_body(self):
        exit_code, written = self._run_create_issues(
            json.dumps({"beads": {"sync_mode": "authoritative"}})
        )
        self.assertEqual(exit_code, 0)
        self.assertIn(sync.TASK_POINTER_PREFIX, written)
        self.assertNotIn("<action>", written)

    def test_no_config_file_behaves_like_authoritative(self):
        exit_code, written = self._run_create_issues(None)
        self.assertEqual(exit_code, 0)
        self.assertIn(sync.TASK_POINTER_PREFIX, written)
        self.assertNotIn("<action>", written)

    def test_retired_off_value_behaves_like_authoritative(self):
        """codex MEDIUM (17-REVIEWS.md, BINDING per 17-02-PLAN.md's
        review_dispositions): a stored retired `off` value must produce the
        same outcome as the no-config fixture -- allow_strip =
        ("off" != "mirror") = True, today's default, so nothing regresses
        mid-phase ahead of 17-03's schema narrowing."""
        exit_code, written = self._run_create_issues(json.dumps({"beads": {"sync_mode": "off"}}))
        self.assertEqual(exit_code, 0)
        self.assertIn(sync.TASK_POINTER_PREFIX, written)
        self.assertNotIn("<action>", written)


class TestSyncModeDeclarationParity(unittest.TestCase):
    """17-03 Task 1 (D-01/D-02): capability.json's declared beads.sync_mode
    values array narrows to the two values that do something -- pin the
    array by equality and order (gsd-core echoes it back in that exact
    order in its rejection message for an invalid config-set write), and
    prove every declared value has a covering behavioral test by iterating
    the declaration itself rather than hardcoding a count, so a future
    value added to the declaration without a covering reader goes red
    here."""

    CAPABILITY_PATH = Path(__file__).resolve().parent.parent / "capability.json"
    # Each key is a declared value; each value names the arm-proving test
    # method already exercising it in TestCreateIssuesCliSyncModeGate above.
    COVERING_TESTS = {
        "authoritative": "test_authoritative_strips_task_body",
        "mirror": "test_mirror_leaves_task_body_intact",
    }

    def _sync_mode_config(self):
        return json.loads(self.CAPABILITY_PATH.read_text(encoding="utf-8"))["config"][
            "beads.sync_mode"
        ]

    def test_declared_values_array_is_exactly_authoritative_then_mirror(self):
        self.assertEqual(self._sync_mode_config()["values"], ["authoritative", "mirror"])

    def test_default_is_unchanged(self):
        self.assertEqual(self._sync_mode_config()["default"], "authoritative")

    def test_every_declared_value_has_a_covering_test(self):
        declared = self._sync_mode_config()["values"]
        self.assertEqual(set(declared), set(self.COVERING_TESTS))
        for value in declared:
            method_name = self.COVERING_TESTS[value]
            self.assertTrue(
                hasattr(TestCreateIssuesCliSyncModeGate, method_name),
                f"declared value {value!r} has no covering test "
                f"TestCreateIssuesCliSyncModeGate.{method_name}",
            )

    def test_sync_module_constant_matches_capability_json(self):
        # gsd-beads-u67.12: capability.json's declared array and sync.py's
        # runtime SYNC_MODE_VALUES frozenset must agree, or an edit to one
        # without the other goes undetected until an unrelated arm test
        # happens to fail.
        declared = frozenset(self._sync_mode_config()["values"])
        self.assertEqual(declared, sync.SYNC_MODE_VALUES)


class TestSyncModeAdjacencyAndEncoding(unittest.TestCase):
    """17-03 Task 1: comparison against the mirror value (main()'s
    `sync_mode != "mirror"`) is exact code-point string equality -- no
    case-folding, no whitespace trimming, no Unicode normalization. A
    value that merely LOOKS like "mirror" must fall through to today's
    authoritative (stripping) behavior: a config value may only ever
    withhold strip permission, never grant it (T-17-03-01), so treating a
    near-miss as "mirror" would be the wrong failure direction."""

    def _run_create_issues(self, sync_mode_value):
        with tempfile.TemporaryDirectory() as tmp:
            plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
            plan_copy = _write_plan_workspace(Path(tmp), plan_text)
            (Path(tmp) / ".planning" / "config.json").write_text(
                json.dumps({"beads": {"sync_mode": sync_mode_value}}), encoding="utf-8"
            )
            with mock.patch("subprocess.run", side_effect=_make_bd_side_effect()):
                exit_code = sync.main(["create-issues", str(plan_copy)])
            return exit_code, plan_copy.read_text(encoding="utf-8")

    def _assert_strips_like_authoritative(self, sync_mode_value):
        exit_code, written = self._run_create_issues(sync_mode_value)
        self.assertEqual(exit_code, 0)
        self.assertIn(sync.TASK_POINTER_PREFIX, written)
        self.assertNotIn("<action>", written)

    def test_case_variant_of_mirror_strips_like_authoritative(self):
        self._assert_strips_like_authoritative("Mirror")

    def test_whitespace_padded_mirror_strips_like_authoritative(self):
        self._assert_strips_like_authoritative(" mirror ")

    def test_homoglyph_value_strips_like_authoritative(self):
        """Cyrillic U+043E (о) in place of "mirror"'s fifth-character Latin
        'o' -- renders identically to "mirror" in most fonts, is a
        different sequence of code points, and Python string equality
        (used by main()'s `sync_mode != "mirror"` comparison) applies no
        normalization that would collapse the two."""
        homoglyph = "mirr" + "о" + "r"
        self.assertNotEqual(homoglyph, "mirror")  # sanity: genuinely different code points
        self._assert_strips_like_authoritative(homoglyph)


class TestLifecycleDispatchNeverConsultsSyncMode(unittest.TestCase):
    """17-02 Task 3 (D-06/D-03): the hook path's plan:post allow_strip stays
    the literal False regardless of beads.sync_mode -- config can only ever
    govern the explicit native `create-issues` CLI path, never the
    substring-matched hook (the D-03 asymmetry)."""

    @mock.patch("subprocess.run")
    def test_authoritative_config_still_leaves_task_bodies_intact_via_hook(self, mock_run):
        mock_run.side_effect = _make_bd_side_effect()
        plan_text = (FIXTURES_DIR / "plan-single.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _lifecycle_workspace(Path(tmp), plan_text=plan_text)
            (Path(tmp) / ".planning" / "config.json").write_text(
                json.dumps({"beads": {"sync_mode": "authoritative"}}), encoding="utf-8"
            )
            prev = Path.cwd()
            os.chdir(tmp)
            try:
                with mock.patch.object(sync, "check_native_step_dispatch", return_value=0):
                    exit_code = sync.lifecycle_dispatch("plan:post")
            finally:
                os.chdir(prev)
            written = (phase_dir / "07-01-PLAN.md").read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertIn("<action>", written)
        self.assertNotIn(sync.TASK_POINTER_PREFIX, written)


class TestCheckSyncModeValue(unittest.TestCase):
    """17-03 Task 2 (D-04 Case 2): check_sync_mode_value is a read-only,
    never-raises stdout notice for a beads.sync_mode value outside the
    declared enum -- the D-04 migration answer for a project that already
    wrote a retired or otherwise invalid value into .planning/config.json."""

    def _notice_for(self, beads_payload):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            planning_dir = project_root / ".planning"
            planning_dir.mkdir()
            if beads_payload is not None:
                (planning_dir / "config.json").write_text(
                    json.dumps({"beads": beads_payload}), encoding="utf-8"
                )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_sync_mode_value(project_root)
        return exit_code, captured.getvalue()

    def test_absent_config_file_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / ".planning").mkdir()
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_sync_mode_value(project_root)
        self.assertEqual(exit_code, 0)
        self.assertEqual(captured.getvalue(), "")

    def test_absent_beads_object_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            planning_dir = project_root / ".planning"
            planning_dir.mkdir()
            (planning_dir / "config.json").write_text(
                json.dumps({"workflow": {"auto_advance": True}}), encoding="utf-8"
            )
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                exit_code = sync.check_sync_mode_value(project_root)
        self.assertEqual(exit_code, 0)
        self.assertEqual(captured.getvalue(), "")

    def test_absent_key_is_silent(self):
        exit_code, out = self._notice_for({"enabled": True})
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "")

    def test_declared_authoritative_value_is_silent(self):
        exit_code, out = self._notice_for({"sync_mode": "authoritative"})
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "")

    def test_declared_mirror_value_is_silent(self):
        exit_code, out = self._notice_for({"sync_mode": "mirror"})
        self.assertEqual(exit_code, 0)
        self.assertEqual(out, "")

    def test_retired_value_produces_one_notice_naming_it(self):
        exit_code, out = self._notice_for({"sync_mode": "off"})
        self.assertEqual(exit_code, 0)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("'off'", lines[0])

    def test_empty_string_produces_a_notice(self):
        _, out = self._notice_for({"sync_mode": ""})
        self.assertNotEqual(out, "")

    def test_case_variant_produces_a_notice(self):
        _, out = self._notice_for({"sync_mode": "Mirror"})
        self.assertIn("'Mirror'", out)

    def test_whitespace_variant_produces_a_notice(self):
        _, out = self._notice_for({"sync_mode": " mirror "})
        self.assertNotEqual(out, "")

    def test_non_string_value_produces_a_notice(self):
        """codex MEDIUM (BINDING, 17-REVIEWS.md): a present-but-wrong-typed
        key is exactly as invisible to the user as a present-but-wrong-
        string one, and it is the same authoring mistake."""
        exit_code, out = self._notice_for({"sync_mode": True})
        self.assertEqual(exit_code, 0)
        self.assertNotEqual(out, "")

    def test_newline_bearing_value_yields_a_single_line_notice(self):
        exit_code, out = self._notice_for({"sync_mode": "off\nrm -rf /"})
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(out.splitlines()), 1)

    def test_notice_states_authoritative_default_still_applies_and_may_strip(self):
        """codex MEDIUM (BINDING): the notice must say execution continues
        under the shipped authoritative behavior and that task bodies may
        therefore still be stripped once the read-path patch gate passes,
        not merely "value not recognized"."""
        _, out = self._notice_for({"sync_mode": "off"})
        self.assertIn("authoritative default applies", out)
        self.assertIn("stripped", out)

    def test_notice_names_the_remedy_command(self):
        _, out = self._notice_for({"sync_mode": "off"})
        self.assertIn("config-set beads.sync_mode", out)

    def test_two_consecutive_dispatches_produce_the_same_single_notice(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            planning_dir = project_root / ".planning"
            planning_dir.mkdir()
            (planning_dir / "config.json").write_text(
                json.dumps({"beads": {"sync_mode": "off"}}), encoding="utf-8"
            )
            captured_first, captured_second = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(captured_first):
                sync.check_sync_mode_value(project_root)
            with contextlib.redirect_stdout(captured_second):
                sync.check_sync_mode_value(project_root)
        self.assertEqual(captured_first.getvalue(), captured_second.getvalue())
        self.assertEqual(len(captured_first.getvalue().splitlines()), 1)

    def test_absent_key_vs_wrong_typed_key_produce_different_stdout(self):
        """BINDING new AC (17-REVIEWS.md, both cross-AI reviewers):
        read_beads_config's isinstance(value, type(default)) wrong-type
        guard collapses "key absent" and "key present, wrong type" into the
        identical effective default -- this asserts check_sync_mode_value
        tells the two states apart via a raw membership test even though
        read_sync_mode cannot."""
        with tempfile.TemporaryDirectory() as tmp_absent:
            absent_root = Path(tmp_absent)
            (absent_root / ".planning").mkdir()
            (absent_root / ".planning" / "config.json").write_text(
                json.dumps({"beads": {}}), encoding="utf-8"
            )
            captured_absent = io.StringIO()
            with contextlib.redirect_stdout(captured_absent):
                sync.check_sync_mode_value(absent_root)

        with tempfile.TemporaryDirectory() as tmp_wrong_type:
            wrong_type_root = Path(tmp_wrong_type)
            (wrong_type_root / ".planning").mkdir()
            (wrong_type_root / ".planning" / "config.json").write_text(
                json.dumps({"beads": {"sync_mode": True}}), encoding="utf-8"
            )
            captured_wrong_type = io.StringIO()
            with contextlib.redirect_stdout(captured_wrong_type):
                sync.check_sync_mode_value(wrong_type_root)

        # Both resolve to the identical effective value via read_sync_mode...
        self.assertEqual(
            sync.read_sync_mode(absent_root), sync.read_sync_mode(wrong_type_root)
        )
        # ...but check_sync_mode_value tells them apart: silence vs. one notice.
        self.assertEqual(captured_absent.getvalue(), "")
        self.assertNotEqual(captured_wrong_type.getvalue(), "")

    def test_never_raises_and_returns_zero_when_config_is_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / ".planning").mkdir()
            (project_root / ".planning" / "config.json").write_text(
                "{not json", encoding="utf-8"
            )
            exit_code = sync.check_sync_mode_value(project_root)
        self.assertEqual(exit_code, 0)

    def test_no_config_write_path_exists(self):
        """Behavioral mirror of the source assertion: a call against a
        project holding the retired value must not modify config.json."""
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            (project_root / ".planning").mkdir()
            config_path = project_root / ".planning" / "config.json"
            original = json.dumps({"beads": {"sync_mode": "off"}})
            config_path.write_text(original, encoding="utf-8")
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                sync.check_sync_mode_value(project_root)
            self.assertEqual(config_path.read_text(encoding="utf-8"), original)

    def test_lifecycle_dispatch_plan_pre_calls_it_and_stays_fail_open_on_raise(self):
        """Fail-open assertion: lifecycle_dispatch('plan:pre') still returns
        0 and still writes BEADS-RECALL.md when check_sync_mode_value
        raises -- the outer try/except Exception around the whole plan:pre
        branch cannot let a failure here take out beads_recall, which runs
        first."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = _make_beads_recall_bd_side_effect("[]\n")
            with tempfile.TemporaryDirectory() as tmp:
                phase_dir = _lifecycle_workspace(Path(tmp))
                prev = Path.cwd()
                os.chdir(tmp)
                try:
                    with mock.patch.object(
                        sync, "check_sync_mode_value", side_effect=RuntimeError("boom")
                    ):
                        exit_code = sync.lifecycle_dispatch("plan:pre")
                finally:
                    os.chdir(prev)
                recall_files = list(phase_dir.glob("*BEADS-RECALL.md"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(recall_files), 1)


class TestDirectSkillSyncResolver(unittest.TestCase):
    """Direct skills must select sync.py exactly as lifecycle dispatch does."""

    ROOT = Path(__file__).resolve().parents[4]
    RELATIVE_SYNC = ".gsd/capabilities/beads/scripts/sync.py"
    DIAGNOSTIC = "gsd-beads: sync.py not found in project, global, or plugin capability roots"
    RESOLVER = '''SYNC_PY=""
for candidate in \\
  "${CLAUDE_PROJECT_DIR:-}/.gsd/capabilities/beads/scripts/sync.py" \\
  "${GSD_HOME:-$HOME}/.gsd/capabilities/beads/scripts/sync.py" \\
  "${CLAUDE_PLUGIN_ROOT:-}/.gsd/capabilities/beads/scripts/sync.py"
do
  if [ -f "$candidate" ]; then SYNC_PY="$candidate"; break; fi
done
if [ -z "$SYNC_PY" ]; then
  echo "gsd-beads: sync.py not found in project, global, or plugin capability roots" >&2
  exit 1
fi'''
    RAW_FENCES = (
        ("beads-sync:create-issues", "beads-sync/SKILL.md", ("create-issues <PLAN.md path>",)),
        ("beads-recall:recall", "beads-recall/SKILL.md", ("beads-recall <phase directory>",)),
        ("beads-recall:patch-checks", "beads-recall/SKILL.md", ("check-patch ship-md", "check-patch execute-plan")),
        ("beads-migrate-todos:migrate", "beads-migrate-todos/SKILL.md", ("migrate-todos",)),
        ("beads-status:wave-status", "beads-status/SKILL.md", ("wave-status-block <phase directory> <plan id> [<plan id> ...]",)),
        ("beads-status:reconcile-regenerate", "beads-status/SKILL.md", ("reconcile-stale-closed <phase directory>", "regenerate-beads-md <phase directory>")),
        ("beads-status:ship-override", "beads-status/SKILL.md", ("ship-override <phase directory>",)),
        ("beads-status:patch-check", "beads-status/SKILL.md", ("check-patch ship-md",)),
        ("beads-status:status", "beads-status/SKILL.md", ("status [phase directory]",)),
        ("beads-status:close-wave", "beads-status/SKILL.md", ("close-wave <phase directory> <plan id> [<plan id> ...]",)),
    )
    PLACEHOLDERS = {
        "<PLAN.md path>", "<phase directory>", "<plan id>",
        "[<plan id> ...]", "[phase directory]",
    }

    def _skill_path(self, relative):
        return self.ROOT / ".gsd/capabilities/beads/skills" / relative

    def _direct_fences(self):
        prefix = r'(?:\.gsd/capabilities/beads/scripts/sync\.py|"\$SYNC_PY")'
        direct = []
        for relative in dict.fromkeys(relative for _, relative, _ in self.RAW_FENCES):
            path = self._skill_path(relative)
            text = path.read_text(encoding="utf-8")
            for raw in re.findall(r"```bash\n(.*?)\n```", text, re.DOTALL):
                tails = tuple(re.findall(rf'^python3 {prefix}(?: (.*))?$', raw, re.MULTILINE))
                if tails:
                    direct.append((path, raw, tails))
        return direct

    def _selected_fences(self):
        expected = [
            (name, self._skill_path(relative), tails)
            for name, relative, tails in self.RAW_FENCES
        ]
        selected = {}
        for path, raw, tails in self._direct_fences():
            matches = [item for item in expected if item[1] == path and item[2] == tails]
            self.assertEqual(
                len(matches), 1,
                f"unmatched or duplicate direct-sync fence in {path}: {tails}",
            )
            name = matches[0][0]
            self.assertNotIn(name, selected, f"duplicate direct-sync fence: {name}")
            selected[name] = raw
        self.assertEqual(set(selected), {name for name, _, _ in expected})
        return selected

    def _assert_raw_contract(self):
        selected = self._selected_fences()
        for name, _, tails in self.RAW_FENCES:
            raw = selected[name]
            self.assertEqual(raw.count(self.RESOLVER), 1, f"{name} resolver differs")
            actual = tuple(re.findall(r'^python3 "\$SYNC_PY"(?: (.*))?$', raw, re.MULTILINE))
            self.assertEqual(actual, tails, f"{name} command tail changed")
        return selected

    def _derive(self, raw, values, status_phase=True):
        discovered = set(re.findall(r"<[^>]+>|\[[^\]]+\]", "\n".join(
            re.findall(r'^python3 "\$SYNC_PY"(?: (.*))?$', raw, re.MULTILINE)
        )))
        self.assertTrue(discovered <= self.PLACEHOLDERS, discovered - self.PLACEHOLDERS)
        derived = raw
        if not status_phase:
            derived = derived.replace(" [phase directory]", "")
        for token in ("[<plan id> ...]", "<PLAN.md path>", "<phase directory>", "<plan id>", "[phase directory]"):
            if token in derived:
                self.assertIn(token, values)
                derived = derived.replace(token, shlex.quote(values[token]))
        command_tails = "\n".join(
            re.findall(r'^python3 "\$SYNC_PY"(?: (.*))?$', derived, re.MULTILINE)
        )
        self.assertFalse(re.search(r"<[^>]+>|\[[^\]]+\]", command_tails))
        return derived

    def _write_spy(self, root):
        path = root / self.RELATIVE_SYNC
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "import json, os, sys\n"
            "with open(os.environ['SPY_LOG'], 'a', encoding='utf-8') as log:\n"
            "    log.write(json.dumps([__file__, sys.argv[1:]]) + '\\n')\n",
            encoding="utf-8",
        )
        return path.resolve()

    def _run_all(self, selected, env, values, status_phase=True):
        results = []
        for name, _, _ in self.RAW_FENCES:
            phase_options = (True, False) if name == "beads-status:status" else (status_phase,)
            for include_phase in phase_options:
                results.append(subprocess.run(
                    ["bash", "-c", self._derive(selected[name], values, include_phase)],
                    cwd=env["UNRELATED_CWD"], env=env, capture_output=True, text=True, timeout=15,
                ))
        return results

    def test_raw_fences_require_one_canonical_resolver_before_execution(self):
        self._assert_raw_contract()

    def test_resolution_precedence_argv_and_failure_boundary(self):
        selected = self._assert_raw_contract()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project, global_root, plugin = (base / "project root", base / "global root", base / "plugin root")
            unrelated = base / "unrelated cwd"
            unrelated.mkdir()
            spy_log = base / "spy.jsonl"
            plan, phase = base / "PLAN path.md", base / "phase directory"
            values = {
                "<PLAN.md path>": str(plan), "<phase directory>": str(phase),
                "<plan id>": "01", "[<plan id> ...]": "02",
                "[phase directory]": str(phase),
            }
            base_env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project), GSD_HOME=str(global_root), HOME=str(base / "home root"), CLAUDE_PLUGIN_ROOT=str(plugin), SPY_LOG=str(spy_log), UNRELATED_CWD=str(unrelated))
            expected_argv = []
            for name, _, _ in self.RAW_FENCES:
                options = (True, False) if name == "beads-status:status" else (True,)
                for include_phase in options:
                    suffixes = re.findall(
                        r'^python3 "\$SYNC_PY"(?: (.*))?$',
                        self._derive(selected[name], values, include_phase),
                        re.MULTILINE,
                    )
                    expected_argv.extend(shlex.split(suffix or "") for suffix in suffixes)
            for root in (project, global_root, plugin):
                self._write_spy(root)
            results = self._run_all(selected, base_env, values)
            self.assertTrue(all(result.returncode == 0 for result in results), results)
            calls = [json.loads(line) for line in spy_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(calls), len(expected_argv))
            self.assertTrue(all(call[0] == str((project / self.RELATIVE_SYNC).resolve()) for call in calls))
            self.assertEqual([call[1] for call in calls], expected_argv)

            spy_log.unlink()
            (project / self.RELATIVE_SYNC).unlink()
            results = self._run_all(selected, base_env, values)
            self.assertTrue(all(result.returncode == 0 for result in results), results)
            calls = [json.loads(line) for line in spy_log.read_text(encoding="utf-8").splitlines()]
            self.assertTrue(all(call[0] == str((global_root / self.RELATIVE_SYNC).resolve()) for call in calls))

            spy_log.unlink()
            (global_root / self.RELATIVE_SYNC).unlink()
            home_sync = self._write_spy(base / "home root")
            for gsd_home in (None, ""):
                spy_log.unlink(missing_ok=True)
                env = dict(base_env)
                if gsd_home is None:
                    env.pop("GSD_HOME")
                else:
                    env["GSD_HOME"] = gsd_home
                results = self._run_all(selected, env, values)
                self.assertTrue(all(result.returncode == 0 for result in results), results)
                calls = [json.loads(line) for line in spy_log.read_text(encoding="utf-8").splitlines()]
                self.assertTrue(all(call[0] == str(home_sync) for call in calls))

            spy_log.unlink()
            home_sync.unlink()
            results = self._run_all(selected, base_env, values)
            self.assertTrue(all(result.returncode == 0 for result in results), results)
            calls = [json.loads(line) for line in spy_log.read_text(encoding="utf-8").splitlines()]
            self.assertTrue(all(call[0] == str((plugin / self.RELATIVE_SYNC).resolve()) for call in calls))

            spy_log.unlink()
            (plugin / self.RELATIVE_SYNC).unlink()
            (project / self.RELATIVE_SYNC).mkdir(parents=True)
            results = self._run_all(selected, base_env, values)
            self.assertTrue(all(result.returncode != 0 for result in results), results)
            self.assertTrue(all(result.stderr == self.DIAGNOSTIC + "\n" for result in results))
            self.assertFalse(spy_log.exists())


if __name__ == "__main__":
    unittest.main()
