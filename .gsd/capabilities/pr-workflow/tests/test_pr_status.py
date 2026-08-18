"""Tests for .gsd/capabilities/pr-workflow/scripts/pr_status.py.

Stdlib unittest only (N5, mirrors markdown-linting/tests/test_lint.py's R-01
finding): the suite must pass under `python3 -m unittest discover` with no
third-party test runner. pr_status.py's parent directory is put on sys.path
at module import so no package __init__.py and no install step is needed --
mirrors test_lint.py's own sys.path.insert technique.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pr_status  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

PR_LIST_ONE_OPEN = json.dumps([{"number": 42, "url": "https://github.com/x/y/pull/42"}])


def _write_phase_dir(tmp_path, phase_dir_name="14-pr-workflow-capability-dogfood"):
    """Lay out a minimal .planning/phases/<phase_dir_name>/ tree under
    tmp_path so find_project_root resolves -- mirrors test_lint.py's
    _write_phase_dir, scoped to just what verify_post needs."""
    phase_dir = tmp_path / ".planning" / "phases" / phase_dir_name
    phase_dir.mkdir(parents=True)
    return phase_dir


def _completed(stdout, returncode=0, stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def _fixture(name):
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class TestRollupPrecedence(unittest.TestCase):
    """D-01 precedence (failing > pending > passing) plus Pitfall 6's
    skipping/cancel bucket mapping, as pure-function assertions with no I/O."""

    def test_all_pass_is_passing(self):
        self.assertEqual(pr_status.rollup_pr_status({"pass"}), "passing")

    def test_pass_and_skipping_is_passing(self):
        self.assertEqual(pr_status.rollup_pr_status({"pass", "skipping"}), "passing")

    def test_pass_and_pending_is_pending(self):
        self.assertEqual(pr_status.rollup_pr_status({"pass", "pending"}), "pending")

    def test_pass_pending_fail_precedence_is_failing(self):
        self.assertEqual(pr_status.rollup_pr_status({"pass", "pending", "fail"}), "failing")

    def test_cancel_is_failing(self):
        self.assertEqual(pr_status.rollup_pr_status({"cancel"}), "failing")

    def test_empty_set_is_passing(self):
        # D-01: zero checks configured on an otherwise-open PR is passing,
        # never none -- none is reserved for "no open PR exists".
        self.assertEqual(pr_status.rollup_pr_status(set()), "passing")


class TestDeriveGateOk(unittest.TestCase):
    def test_none_and_passing_are_gate_ok(self):
        self.assertTrue(pr_status.derive_gate_ok("none"))
        self.assertTrue(pr_status.derive_gate_ok("passing"))

    def test_pending_failing_unavailable_are_not_gate_ok(self):
        self.assertFalse(pr_status.derive_gate_ok("pending"))
        self.assertFalse(pr_status.derive_gate_ok("failing"))
        self.assertFalse(pr_status.derive_gate_ok("unavailable"))


class TestVerifyPost(unittest.TestCase):
    """verify_post() end-to-end against a mocked subprocess.run -- one
    fake_run dispatcher per test, branching on the argv prefix so each test
    only asserts the calls its own scenario actually needs."""

    def test_no_open_pr_writes_none_and_gate_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_phase_dir(Path(tmp))

            def fake_run(argv, **kwargs):
                if argv[:3] == ["gh", "auth", "status"]:
                    return _completed("", 0)
                if argv[:3] == ["git", "branch", "--show-current"]:
                    return _completed("main\n", 0)
                if argv[:3] == ["gh", "pr", "list"]:
                    return _completed(_fixture("pr_list_empty.json"), 0)
                raise AssertionError(f"unexpected call: {argv}")

            with mock.patch("shutil.which", return_value="/usr/bin/gh"):
                with mock.patch("subprocess.run", side_effect=fake_run):
                    exit_code = pr_status.verify_post(str(phase_dir))

            self.assertEqual(exit_code, 0)
            report_path = phase_dir / "14-PR.md"
            self.assertTrue(report_path.exists())
            text = report_path.read_text(encoding="utf-8")
            self.assertIn("pr_status", text)
            self.assertIn("pr_gate_ok", text)
            self.assertIn("generated_at", text)
            self.assertIn("generated_from", text)
            self.assertIn("pr_status: none", text)
            self.assertIn("pr_gate_ok: true", text)

    def test_open_pr_failing_checks_writes_failing_and_gate_not_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_phase_dir(Path(tmp))

            def fake_run(argv, **kwargs):
                if argv[:3] == ["gh", "auth", "status"]:
                    return _completed("", 0)
                if argv[:3] == ["git", "branch", "--show-current"]:
                    return _completed("feature-x\n", 0)
                if argv[:3] == ["gh", "pr", "list"]:
                    return _completed(PR_LIST_ONE_OPEN, 0)
                if argv[:3] == ["gh", "pr", "checks"]:
                    return _completed(_fixture("checks_fail.json"), 0)
                raise AssertionError(f"unexpected call: {argv}")

            with mock.patch("shutil.which", return_value="/usr/bin/gh"):
                with mock.patch("subprocess.run", side_effect=fake_run):
                    exit_code = pr_status.verify_post(str(phase_dir))

            self.assertEqual(exit_code, 0)
            text = (phase_dir / "14-PR.md").read_text(encoding="utf-8")
            self.assertIn("pr_status: failing", text)
            self.assertIn("pr_gate_ok: false", text)

    def test_rerun_overwrites_not_appends(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_phase_dir(Path(tmp))

            def fake_run(argv, **kwargs):
                if argv[:3] == ["gh", "auth", "status"]:
                    return _completed("", 0)
                if argv[:3] == ["git", "branch", "--show-current"]:
                    return _completed("main\n", 0)
                if argv[:3] == ["gh", "pr", "list"]:
                    return _completed(_fixture("pr_list_empty.json"), 0)
                raise AssertionError(f"unexpected call: {argv}")

            with mock.patch("shutil.which", return_value="/usr/bin/gh"):
                with mock.patch("subprocess.run", side_effect=fake_run):
                    pr_status.verify_post(str(phase_dir))
                    first_text = (phase_dir / "14-PR.md").read_text(encoding="utf-8")
                    pr_status.verify_post(str(phase_dir))
                    second_text = (phase_dir / "14-PR.md").read_text(encoding="utf-8")

            self.assertEqual(len(first_text), len(second_text))
            self.assertEqual(first_text.count("---"), 2)
            self.assertEqual(second_text.count("---"), 2)
            self.assertEqual(first_text, second_text)


class TestConfined(unittest.TestCase):
    """T-14-03: confined() must reject any resolved escape from the
    project root -- copied verbatim from lint.py, re-tested independently
    here per this capability's own threat register entry."""

    def test_confined_raises_for_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            with self.assertRaises(ValueError):
                pr_status.confined(root, "..", "..", "etc", "passwd")


if __name__ == "__main__":
    unittest.main()
