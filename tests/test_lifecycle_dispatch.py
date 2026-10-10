"""GH#10 (finding 2): `hooks/lifecycle-dispatch.sh`'s embedded gate-2 python
snippet decides "is this Bash command actually a
`gsd_run loop render-hooks <point> --raw` invocation" via a COMMAND_POSITION
regex. Before this fix, backtick and bare newline sat in that character
class, so text that merely *quotes* the trigger command (a markdown code
span, or a `\n` inside a JSON-decoded `--body`/`--description` argument)
satisfied "command position" without the shell ever parsing a command
boundary there.

These tests extract the snippet verbatim from the on-disk hook (never a
hand-copied duplicate that could silently drift from the real regex) and
run it standalone via `python3 -c`, feeding it the same
`{"tool_input": {"command": ...}}` shape Claude Code's PostToolUse payload
carries.
"""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "hooks" / "lifecycle-dispatch.sh"


def _extract_snippet():
    text = HOOK_PATH.read_text(encoding="utf-8")
    match = re.search(r"python3 -I -c '(.*?)'\s*2>/dev/null\)\"", text, re.DOTALL)
    if not match:
        raise AssertionError(f"could not find the python3 -c snippet in {HOOK_PATH}")
    return match.group(1)


SNIPPET = _extract_snippet()


def _run(command, **extra):
    payload = json.dumps({"tool_input": {"command": command}, "cwd": "/tmp", **extra})
    result = subprocess.run(
        [sys.executable, "-c", SNIPPET],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        raise AssertionError(f"snippet exited {result.returncode}: {result.stderr}")
    return result.stdout.strip()


class TestLifecycleDispatchCommandPosition(unittest.TestCase):
    def test_real_invocation_still_matches(self):
        out = _run("VAR=$(gsd_run loop render-hooks execute:wave:post --raw)")
        self.assertEqual(out, "execute:wave:post /tmp")

    def test_real_invocation_after_semicolon_still_matches(self):
        out = _run("cd /repo; gsd_run loop render-hooks plan:pre --raw")
        self.assertEqual(out, "plan:pre /tmp")

    def test_real_multiline_assignment_style_invocation_still_matches(self):
        # gsd-core's own workflows (e.g. ship.md, verify-work.md) always
        # trigger this way: `$(...)` on its own line after a prior
        # statement. The `(` immediately preceding the tools token already
        # satisfies COMMAND_POSITION regardless of the preceding newline, so
        # this is unaffected by dropping bare newline from the class.
        out = _run(
            'cd "$dir"\nEXECUTE_POST_HOOKS_JSON=$(gsd_run loop render-hooks execute:wave:post --raw)'
        )
        self.assertEqual(out, "execute:wave:post /tmp")

    def test_backtick_quoted_prose_no_longer_false_triggers(self):
        out = _run(
            'bd comment add gsd-beads-1 --body "seen via `gsd_run loop '
            'render-hooks execute:wave:post --raw` in the log"'
        )
        self.assertEqual(out, "")

    def test_newline_embedded_prose_no_longer_false_triggers(self):
        out = _run(
            "bd comment add gsd-beads-1 --body \"line one\n"
            "gsd_run loop render-hooks execute:wave:post --raw\n"
            'line three"'
        )
        self.assertEqual(out, "")

    def test_echo_of_the_command_still_rejected(self):
        out = _run("echo gsd_run loop render-hooks plan:pre --raw")
        self.assertEqual(out, "")

    # R11: Claude Code's Bash tool_response carries `interrupted`; an
    # interrupted render-hooks call never produced the hook list, so no
    # lifecycle step may run on it.
    def test_interrupted_trigger_is_skipped(self):
        out = _run("gsd_run loop render-hooks plan:pre --raw",
                   tool_response={"stdout": "", "stderr": "", "interrupted": True})
        self.assertEqual(out, "")

    def test_completed_trigger_still_matches(self):
        out = _run("gsd_run loop render-hooks plan:pre --raw",
                   tool_response={"stdout": "[]", "stderr": "", "interrupted": False})
        self.assertEqual(out, "plan:pre /tmp")


class TestLifecycleDispatchIsolatedPython(unittest.TestCase):
    """R1: a repo-planted json.py must never run inside the hook's python."""

    def _run_hook(self, root, hook_cwd, payload_cwd):
        home = root / "home"
        sync_dir = home / ".gsd" / "capabilities" / "beads" / "scripts"
        sync_dir.mkdir(parents=True)
        (sync_dir.parent / "capability.json").write_text("{}\n")
        (sync_dir / "sync.py").write_text("print('dispatched')\n")
        payload = json.dumps({
            "tool_input": {"command": "gsd_run loop render-hooks plan:pre --raw"},
            "cwd": str(payload_cwd),
        })
        env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "GSD_HOME": str(home)}
        return subprocess.run(
            ["bash", str(HOOK_PATH)], input=payload, capture_output=True,
            text=True, timeout=20, cwd=hook_cwd, env=env,
        )

    def _plant(self, directory, canary):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "json.py").write_text(
            f"open({str(canary)!r}, 'a').write('json\\n')\nraise SystemExit(0)\n"
        )

    def _assert_dispatched(self, result, canary):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(canary.exists(), "hook python imported planted json.py")
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(context, "beads (plan:pre):\ndispatched")

    def test_planted_json_in_hook_cwd_is_not_imported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canary = root / "canary"
            hook_cwd = root / "hook-cwd"
            self._plant(hook_cwd, canary)
            project = root / "project"
            (project / ".planning").mkdir(parents=True)
            self._assert_dispatched(self._run_hook(root, hook_cwd, project), canary)

    def test_planted_json_in_project_dir_is_not_imported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            canary = root / "canary"
            project = root / "project"
            (project / ".planning").mkdir(parents=True)
            self._plant(project, canary)
            self._assert_dispatched(self._run_hook(root, root, project), canary)


if __name__ == "__main__":
    unittest.main()
