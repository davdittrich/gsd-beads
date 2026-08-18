"""Tests for .gsd/capabilities/markdown-linting/scripts/lint.py.

Stdlib unittest only (N5, review finding R-01): the suite must pass under
`python3 -m unittest discover` with no third-party test runner installed.
lint.py's parent directory is put on sys.path at module import so no
package __init__.py and no install step is needed -- mirrors
beads/tests/test_sync.py's own sys.path.insert technique.
"""
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _write_phase_dir(tmp_path, phase_dir_name="13-markdown-linting-capability-dogfood"):
    """Lay out a minimal .planning/phases/<phase_dir_name>/ tree under
    tmp_path so find_project_root resolves -- mirrors test_sync.py's
    _write_plan_workspace, scoped to just what verify_post needs."""
    phase_dir = tmp_path / ".planning" / "phases" / phase_dir_name
    phase_dir.mkdir(parents=True)
    return phase_dir


class TestFailOpen(unittest.TestCase):
    """MDL-04/Pitfall 5: rumdl+uvx both absent, or a live rumdl call raising
    TimeoutExpired/OSError, degrades to exit 0, exactly one NOTICE, and a
    sentinel report that overwrites any prior content -- deliberately
    unlike beads/scripts/sync.py's TestFailOpen, which asserts the
    analogous artifact (BEADS.md) does NOT exist on the fail-open path;
    here the report file must exist, since Pitfall 5's whole point is that
    the report is never left stale/untouched."""

    def test_tool_absent_fail_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_phase_dir(Path(tmp))
            captured = io.StringIO()
            with mock.patch("shutil.which", return_value=None):
                with mock.patch(
                    "subprocess.run",
                    side_effect=AssertionError("rumdl/uvx must not be invoked when absent"),
                ):
                    with mock.patch("sys.stdout", captured):
                        exit_code = lint.verify_post(str(phase_dir))

            self.assertEqual(exit_code, 0)
            self.assertEqual(captured.getvalue().count(lint.NOTICE), 1)
            report_path = phase_dir / "13-LINT-REPORT.md"
            self.assertTrue(report_path.exists())
            text = report_path.read_text(encoding="utf-8")
            self.assertIn("violation_count: unavailable", text)
            self.assertNotIn("violation_count: 0\n", text)

    def test_tool_absent_overwrites_stale_zero_report_sentinel(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_phase_dir(Path(tmp))
            report_path = phase_dir / "13-LINT-REPORT.md"
            report_path.write_text(
                "---\nviolation_count: 0\n---\n\nstale\n", encoding="utf-8"
            )
            with mock.patch("shutil.which", return_value=None):
                with mock.patch(
                    "subprocess.run",
                    side_effect=AssertionError("rumdl/uvx must not be invoked when absent"),
                ):
                    lint.verify_post(str(phase_dir))

            text = report_path.read_text(encoding="utf-8")
            self.assertIn("unavailable", text)
            self.assertNotIn("violation_count: 0\n", text)

    def test_rumdl_timeout_fail_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_phase_dir(Path(tmp))
            captured = io.StringIO()
            with mock.patch(
                "shutil.which",
                side_effect=lambda name: "/usr/bin/rumdl" if name == "rumdl" else None,
            ):
                with mock.patch(
                    "subprocess.run",
                    side_effect=subprocess.TimeoutExpired(cmd=["rumdl"], timeout=60),
                ):
                    with mock.patch("sys.stdout", captured):
                        exit_code = lint.verify_post(str(phase_dir))

            self.assertEqual(exit_code, 0)
            self.assertEqual(captured.getvalue().count(lint.NOTICE), 1)
            text = (phase_dir / "13-LINT-REPORT.md").read_text(encoding="utf-8")
            self.assertIn("violation_count: unavailable", text)

    def test_rumdl_oserror_fail_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_phase_dir(Path(tmp))
            captured = io.StringIO()
            with mock.patch(
                "shutil.which",
                side_effect=lambda name: "/usr/bin/rumdl" if name == "rumdl" else None,
            ):
                with mock.patch("subprocess.run", side_effect=OSError("boom")):
                    with mock.patch("sys.stdout", captured):
                        exit_code = lint.verify_post(str(phase_dir))

            self.assertEqual(exit_code, 0)
            self.assertEqual(captured.getvalue().count(lint.NOTICE), 1)
            text = (phase_dir / "13-LINT-REPORT.md").read_text(encoding="utf-8")
            self.assertIn("violation_count: unavailable", text)

    def test_config_error_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            phase_dir = _write_phase_dir(Path(tmp))
            completed = subprocess.CompletedProcess(
                args=["rumdl"], returncode=2, stdout="", stderr="bad config"
            )
            with mock.patch(
                "shutil.which",
                side_effect=lambda name: "/usr/bin/rumdl" if name == "rumdl" else None,
            ):
                with mock.patch("subprocess.run", return_value=completed):
                    with self.assertRaises(RuntimeError):
                        lint.verify_post(str(phase_dir))

            report_path = phase_dir / "13-LINT-REPORT.md"
            self.assertFalse(report_path.exists())


if __name__ == "__main__":
    unittest.main()
