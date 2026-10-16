#!/usr/bin/env python3
"""Beads sync: translate PLAN.md tasks into bd issues.

stdlib-only (N5: no dependency beyond the `bd` binary and the Python 3
standard library). Every `bd` invocation is an argv list passed to
`subprocess.run` with shell execution left at its (disabled) default --
PLAN.md text is authored by a different principal than the process running
`bd`, so no `bd` command is ever assembled as a shell string (N4, threat
T-01-01).
"""
import argparse
import contextlib
import fcntl
import hashlib
import itertools
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

BD_TIMEOUT = 15  # seconds; bounded timeout on every bd subprocess call
GIT_TIMEOUT = 15  # seconds; bounded timeout on every git subprocess call (ship_override)
NOTICE = "bd unavailable -- sync skipped"
BEADS_RECALL_STATUSES = "open,in_progress,blocked,deferred"
# yyjh: marks every epic/task create so external tools can identify synced
# issues without heuristics; hand-shaped todo migrations stay unlabelled.
SYNC_LABEL = "gsd-sync"

_TASK_OPEN_PATTERN = r'''<task(?=[\s>])(?:"[^"]*"|'[^']*'|[^'">])*>'''
RAW_TASK_OPEN_RE = re.compile(r"<task(?=[\s>])")
TASK_RE = re.compile(_TASK_OPEN_PATTERN + r".*?</task>", re.DOTALL)
# gh-17: a `<task>` literal quoted in prose (fenced or inline) must not count
# as a real opener. Every span these two find is blanked to same-length
# whitespace, so every downstream offset (task_matches spans, name_end,
# beads_id_span, tracker_insert) still indexes correctly into the real text.
# Line-start opening delimiter run of 3+ backticks/tildes -- CommonMark
# requires the closing run to be the same character and >= length (`close_re`
# below enforces the ">=" with `{len(marker),}`; under-matching a too-short
# closer, never over-matching a too-long one, is the safe direction gh-17
# needs). CodeRabbit: a backtick fence's info string must not itself contain
# a backtick (CommonMark 4.5) -- otherwise a line like "````<task>`" would be
# read as a valid fence opener when it is not one. Matched one already-split
# line at a time (see `_mask_fenced_code_blocks`), so no MULTILINE flag and
# no need to capture the indent (only the marker, group 1, is ever read).
_FENCE_OPEN_RE = re.compile(r"^(?:[ \t]{0,3})(`{3,}(?!.*`)|~{3,}).*$")
# A code span opens with a backtick run and closes at the next run of the
# identical length (CommonMark 6.1) -- a shorter or longer run in between
# (e.g. the single backticks inside a `` `<task>` `` double-backtick span)
# is content, not a delimiter. CodeRabbit: both runs must be exact-boundary
# (not a backtick adjacent to either) -- otherwise `(`+)` can backtrack to a
# shorter opener, or `\1` can match a prefix of a longer closing run,
# treating an unequal ``` ... `<task> ... `` sequence as one code span.
# A code span also can't cross a blank line (CommonMark 6.1: a blank line
# ends the paragraph) -- without that boundary, a stray backtick in one
# paragraph can pair with an unrelated stray backtick in a later one and
# mask everything between, including a real <task> block, with no
# PlanParseError to catch it: silent task loss, worse than gh-17's crash.
INLINE_CODE_RE = re.compile(
    r"(?<!`)(`+)(?!`)(?:(?!\1)(?!\r?\n[ \t]*\r?\n).)*?(?<!`)\1(?!`)", re.DOTALL
)


def _blank(s):
    """Replace every non-newline character in `s` with a space (gh-17) --
    shared by both masking passes below so a match's length, and therefore
    every offset taken against the masked copy, is preserved exactly."""
    return re.sub(r"[^\r\n]", " ", s)


def _mask_fenced_code_blocks(text):
    """Blank every fenced code block to same-length whitespace (gh-17
    F-01): an opening ```` ``` ```` (or `~~~`) run at line start is closed by
    the next line whose only content is a run of the same character at
    least as long -- a nested outer fence (e.g. 4 backticks wrapping a
    3-backtick example) must mask the whole span, including the inner
    example, not stop at the inner fence.

    Review finding: CommonMark's own unterminated-fence rule (mask to end
    of text) was the wrong choice here -- a plan with a typo'd/missing
    closing fence would silently blank every real <task> after it, with
    raw_open_starts and closed_open_starts both landing on the same empty
    set, so no PlanParseError ever fires. That is the exact "lifecycle
    appears to run and tracks nothing" failure class gh-17 exists to
    prevent, just made silent instead of loud. An unterminated fence is
    therefore NOT masked at all -- treated as ordinary text, so a stray
    <task> literal it happens to contain is exposed and raises loudly,
    rather than a real trailing task being swallowed silently.
    """
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    while i < len(lines):
        opener = _FENCE_OPEN_RE.match(lines[i].rstrip("\r\n"))
        if opener is None:
            out.append(lines[i])
            i += 1
            continue
        marker = opener.group(1)
        char = marker[0]
        # CodeRabbit: the closing fence's indentation is 0-3 spaces on its
        # own terms (CommonMark 4.5) -- it is never constrained by the
        # opener's own indentation.
        close_re = re.compile(rf"^[ \t]{{0,3}}{re.escape(char)}{{{len(marker)},}}[ \t]*$")
        end = i + 1
        while end < len(lines) and close_re.match(lines[end].rstrip("\r\n")) is None:
            end += 1
        if end >= len(lines):
            out.append(lines[i])
            i += 1
            continue
        end += 1  # include the closing fence line
        for line in lines[i:end]:
            out.append(_blank(line))
        i = end
    return "".join(out)


NAME_RE = re.compile(r"<name>(.*?)</name>", re.DOTALL)
BEADS_ID_RE = re.compile(r"<beads-id>(.*?)</beads-id>", re.DOTALL)
FILES_RE = re.compile(r"<files>(.*?)</files>", re.DOTALL)
# 16-01 Task 1 (D-06): per-task content-field regexes, same
# `<tag>(.*?)</tag>` DOTALL shape as the trio above -- these feed
# _task_description()'s `bd create -d` rendering.
READ_FIRST_RE = re.compile(r"<read_first>(.*?)</read_first>", re.DOTALL)
PRECONDITION_RE = re.compile(r"<precondition>(.*?)</precondition>", re.DOTALL)
BEHAVIOR_RE = re.compile(r"<behavior>(.*?)</behavior>", re.DOTALL)
ACTION_RE = re.compile(r"<action>(.*?)</action>", re.DOTALL)
VERIFY_RE = re.compile(r"<verify>(.*?)</verify>", re.DOTALL)
ACCEPTANCE_CRITERIA_RE = re.compile(r"<acceptance_criteria>(.*?)</acceptance_criteria>", re.DOTALL)
DONE_RE = re.compile(r"<done>(.*?)</done>", re.DOTALL)
# CR-01: checkpoint:decision/checkpoint:human-verify field regexes -- D-03
# excludes these tasks from strip_task_bodies but NOT from resolve_issue's
# create path, so their real content must be extractable too, feeding
# _checkpoint_task_description() rather than _task_description() (which only
# knows the auto/tracer field set above).
DECISION_RE = re.compile(r"<decision>(.*?)</decision>", re.DOTALL)
CONTEXT_RE = re.compile(r"<context>(.*?)</context>", re.DOTALL)
OPTIONS_RE = re.compile(r"<options>(.*?)</options>", re.DOTALL)
SELECTION_PROMPT_RE = re.compile(r"<selection-prompt>(.*?)</selection-prompt>", re.DOTALL)
WHAT_BUILT_RE = re.compile(r"<what-built>(.*?)</what-built>", re.DOTALL)
HOW_TO_VERIFY_RE = re.compile(r"<how-to-verify>(.*?)</how-to-verify>", re.DOTALL)
RESUME_SIGNAL_RE = re.compile(r"<resume-signal>(.*?)</resume-signal>", re.DOTALL)
# TASK_TYPE_RE is the only regex here that reads an XML *attribute* rather
# than a tag body -- run it against a TASK_RE match's whole block
# (m.group(0)), same way NAME_RE.search(block) etc. already run (D-03).
TASK_OPEN_TAG_RE = re.compile(_TASK_OPEN_PATTERN)
# 16-01 Task 2 (D-06): <objective> is plan-level only -- it appears exactly
# once per PLAN.md, before <tasks>, and never inside an individual <task>
# block (verified against gsd-core's canonical phase-prompt.md template and
# a real executed PLAN.md, 16-RESEARCH.md Priority 3). Matched against the
# whole plan text, not a TASK_RE block, unlike every regex above.
OBJECTIVE_RE = re.compile(r"<objective>(.*?)</objective>", re.DOTALL)
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?\r?\n)---(?:\r?\n|\Z)", re.DOTALL)
# GH#10: same `status` key gsd-core's plan-dependency-graph.cjs reads from a
# SUMMARY.md's frontmatter to decide halt-propagation -- this must stay the
# one place this capability decides the same thing, so the two readers of
# the identical artifact can never contradict each other again.
# [ \t]*, not \s*: an empty `status:` must not swallow the next line.
STATUS_RE = re.compile(r"^status:[ \t]*(.*)$", re.MULTILINE)
BEADS_EPIC_RE = re.compile(r"^beads_epic:\s*(\S+)\s*$", re.MULTILINE)
BEADS_EPIC_DECL_RE = re.compile(r"^beads_epic[ \t]*:(.*)$", re.MULTILINE)
DEPENDS_ON_RE = re.compile(r"^depends_on:\s*\[(.*?)\]\s*$", re.MULTILINE)
# WR-04: the inline-bracket form above requires the value on the same line
# as the key. YAML also permits (and this fixture set previously had no
# coverage for) the block-list form:
#   depends_on:
#     - "01-01"
# parse_depends_on falls back to this regex when DEPENDS_ON_RE doesn't match.
DEPENDS_ON_BLOCK_RE = re.compile(r"^depends_on:\s*\n((?:^[ \t]*-[ \t]*.+\n?)+)", re.MULTILINE)
# TRUTH-04: phase segment widened to `\d+(?:\.\d+)?` so a decimal phase
# number (`10.1-01-PLAN.md`, the `/gsd-phase --insert` form) is discovered
# too -- the sibling `sota-numerics` capability already carries the
# equivalent widening for its own copy of this pattern
# (`sota-numerics/scripts/check-alternatives.py`), naming this beads pattern
# as the too-narrow one. Anchored at both ends with every repeated group
# separated by a mandatory literal (`.`, `-`), so no two quantifiers can
# match the same input span -- no nested quantifiers, no catastrophic
# backtracking (ReDoS discipline, T-17-01-02). `\d` (not `[0-9]`) is kept
# to preserve today's Unicode-aware matching semantics exactly -- narrowing
# is a deliberate non-change, out of TRUTH-04's scope. The ordinal segment
# widens to `\d+` to match the sibling pattern exactly; safe because the
# captured group is only ever used as a dict key, never joined onto a path
# (T-01-04).
PLAN_FILE_RE = re.compile(r"^(\d+(?:\.\d+)?-\d+)-PLAN\.md$")
# B12 migrate-todos: a pending todo's frontmatter (add-todo.md's schema --
# created/title/area/severity/files, block-list files:) plus its
# ## Problem/## Solution body. TITLE_RE allows spaces (title text), AREA_RE/
# SEVERITY_RE are single-token like BEADS_EPIC_RE; FILES_BLOCK_RE is
# DEPENDS_ON_BLOCK_RE's block-list shape scoped to the `files:` key.
TITLE_RE = re.compile(r"^title:[ \t]*(.+)$", re.MULTILINE)
AREA_RE = re.compile(r"^area:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
SEVERITY_RE = re.compile(r"^severity:\s*(\S+)\s*$", re.MULTILINE)
FILES_BLOCK_RE = re.compile(r"^files:\s*\n((?:^[ \t]*-[ \t]*.+\n?)+)", re.MULTILINE)
# 260820-j6g (bd gsd-beads-72u): a completed plan's SUMMARY.md frontmatter
# `resolves_issues:` key -- the only signal that lets reconcile_stale_closed
# reach a standalone problem-report issue carrying no <beads-id> anywhere.
# Inline-flow/block-list pair mirrors DEPENDS_ON_RE/DEPENDS_ON_BLOCK_RE
# exactly, same ReDoS discipline (anchored, mandatory literal separators, no
# nested quantifiers). A third clone of this parse idiom, rather than a
# shared extraction over parse_depends_on/parse_todo_files_block, is
# deliberate: both of those are under test and out of this ticket's blast
# radius.
RESOLVES_ISSUES_RE = re.compile(r"^resolves_issues:\s*\[(.*?)\]\s*$", re.MULTILINE)
RESOLVES_ISSUES_BLOCK_RE = re.compile(r"^resolves_issues:\s*\n((?:^[ \t]*-[ \t]*.+\n?)+)", re.MULTILINE)
# The argv trust boundary for every id parse_resolves_issues extracts: a
# leading alphanumeric character (so an entry beginning with `-` can never
# reach `bd close` as an option flag) followed by alphanumerics, `.`, `_`,
# or `-`. Matched with .fullmatch(), never .search() or .match(), so a
# multi-token string like "a b" or "../evil" cannot pass by matching only a
# safe prefix.
SAFE_BD_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
# gsd-beads-7 (GH#7): every id `bd create` has ever emitted in this project's
# database (`bd list --all --json`, sampled directly) is lowercase and
# contains at least one `<prefix>-<code>` hyphen split, optionally followed
# by a `.<ordinal>` subtask suffix -- e.g. "gsd-beads-xy2", "tracer-f5x.1".
# SAFE_BD_ID_RE only excludes argv-unsafe characters; it does NOT test this
# shape, so it accepts implausible values like "TBD" as if they were a real
# stored identity. BEADS_ID_SHAPE_RE is the narrower, additional test:
# a `<beads-id>` failing it can never have been written by `bd create`, so
# resolve_issue treats it as unbound (create) rather than stale (diverge) --
# preserving D-07's stale-identity protection for anything that DOES match.
BEADS_ID_SHAPE_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+(?:\.[0-9]+)?")
PROBLEM_RE = re.compile(r"^##\s*Problem\s*\n(.*?)(?=^##\s*Solution\s*$)", re.MULTILINE | re.DOTALL)
# WR-02: PROBLEM_RE's lookahead anchor requires a literal "## Solution"
# heading later in the body. When that heading is missing/misspelled,
# PROBLEM_FALLBACK_RE captures everything after "## Problem" to end-of-body
# instead of silently dropping the text (this migration deletes the source
# todo file on success, so a dropped problem is unrecoverable).
PROBLEM_FALLBACK_RE = re.compile(r"^##\s*Problem\s*\n(.*)", re.MULTILINE | re.DOTALL)
SOLUTION_RE = re.compile(r"^##\s*Solution\s*\n(.*)", re.MULTILINE | re.DOTALL)
# D-02: bd's verified priority scale (0=Critical..4=Backlog) mapped onto the
# blocker/major/minor/cosmetic taxonomy add-todo.md's infer_severity step
# already uses -- 4 (Backlog) is deliberately unused here, reserved for a
# future idea, not a migrated todo's severity.
SEVERITY_TO_PRIORITY = {"blocker": 0, "major": 1, "minor": 2, "cosmetic": 3}
BEADS_MD_FIELD_RE = re.compile(r"^(\w+):\s*(.*)$", re.MULTILINE)
# 03-03 Task 2: the literal marker bracketing the local ship.md patch
# (GSD-CORE-PATCH.md) -- check_patch() does a plain substring check
# against this, never a regex, since the marker is a fixed literal string.
#
# v2 (gsd-core 1.11.0): the patch shrank to step dispatch only. gsd-core
# 1.11.0 landed PR #3608 for issue #3559, adding a native "Every other
# capId" arm to ship.md's preflight step 6 -- so the v1 patch's generic GATE
# dispatch is now upstream and was NOT reapplied. Generic STEP dispatch at
# ship:pre still has no native equivalent (every `kind == "step"` mention in
# 1.11.0's ship.md belongs to ship:post), so that half remains.
#
# The version bump is deliberate: a machine still carrying v1 has a
# now-redundant gate loop running alongside the native one, and this checker
# reporting "missing" is the signal to reapply the trimmed v2.
SHIP_MD_PATCH_MARKER = "<!-- gsd-beads-patch:ship-pre-generic-dispatch v2 -->"
# 17-04 Task 3 (D-08/D-10): the ship-md patch check `check_patch` reads.
SHIP_MD_PATCH_PATH_PARTS = ("gsd-core", "workflows", "ship.md")
SHIP_MD_PATCH_VERSION = "v2"
SHIP_MD_FILENAME = "ship.md"
SHIP_MD_NOT_FOUND_MSG = (
    "⚠ {filename} not found at {path} -- cannot verify the local ship:pre dispatch "
    "patch (only this runtime home was probed; other runtime homes such as "
    "CODEX_HOME or CURSOR_CONFIG_DIR were not checked)"
)
SHIP_MD_COULD_NOT_READ_MSG = (
    "⚠ {filename} at {path} could not be read ({exc}) -- cannot verify the "
    "local ship:pre dispatch patch"
)
SHIP_MD_PRESENT_MSG = "{filename} ship:pre step-dispatch patch: present ({version}) at {path}"
SHIP_MD_MISSING_MSG = (
    "⚠ {filename}'s ship:pre generic STEP dispatch patch (beads, {version}) is "
    "missing at {path} -- the ship_override step will not fire. The two ship:pre "
    "GATES are unaffected: gsd-core >= 1.11.0 dispatches those natively (#3559 / PR "
    "#3608). Reapply: see .gsd/capabilities/beads/GSD-CORE-PATCH.md"
)
# gh-2: the lifecycle points `lifecycle_dispatch` handles -- every `steps[]`
# entry in capability.json EXCEPT `ship:pre`, which already dispatches
# natively through this capability's own ship.md patch. Order is the
# lifecycle's, not alphabetical, and `hooks/lifecycle-dispatch.sh` carries
# the same list: any change here must be mirrored there.
LIFECYCLE_DISPATCH_POINTS = (
    "plan:pre",
    "plan:post",
    "execute:wave:pre",
    "execute:wave:post",
    "verify:post",
)
# 17-02 Task 1 (D-05): gsd-core PR #3687 (merged to `next` 2026-08-19,
# unreleased as of 1.11.0) adds native generic `kind == "step"` dispatch at
# these two points only -- `check_native_step_dispatch` probes the installed
# workflow file each maps onto, scoped to the point's own
# `render-hooks <point> --raw` region so it does not false-positive on the
# unrelated `kind == "step"`/`kind == "gate"` mentions both shipped 1.11.0
# files carry outside that region. `execute:wave:pre`/`execute:wave:post`
# are deliberately absent -- no upstream work covers them anywhere.
NATIVE_STEP_DISPATCH_WORKFLOW_FILES = {
    "plan:post": "plan-phase.md",
    "verify:post": "verify-work.md",
}
NATIVE_STEP_DISPATCH_REGION_LINES = 120
_GENERIC_STEP_KIND_RE = re.compile(r'\bkind\s*==\s*"step"')
_STEP_QUALIFIER_RE = re.compile(r'\b(?:capId\s*==|ref\.skill\s*==)')
# B13/D-08: on-demand `status` with no phase_dir argument resolves the
# current/last-active phase from STATE.md's frontmatter -- single-token
# style matching BEADS_EPIC_RE.
CURRENT_PHASE_RE = re.compile(r"^current_phase:\s*(\S+)\s*$", re.MULTILINE)
# B14: beads.epic_per=milestone's title source, STATE.md's milestone:/
# milestone_name: frontmatter keys -- single-token style matching
# BEADS_EPIC_RE/CURRENT_PHASE_RE.
MILESTONE_RE = re.compile(r"^milestone:[ \t]*(\S+)[ \t]*$", re.MULTILINE)
MILESTONE_NAME_RE = re.compile(r"^milestone_name:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
# The single-token, quote-keeping pattern older versions titled milestone epics
# with; kept only so resolve_milestone_epic still reuses those epics.
_LEGACY_MILESTONE_NAME_RE = re.compile(r"^milestone_name:\s*(\S+)\s*$", re.MULTILINE)


# bd finds its database from the process cwd. main() sets this to the project
# root of its path argument for the duration of one call, so every bd call runs there (the
# effect of `bd -C <root>` without touching any call site's argv).
_BD_CWD = None


def _set_bd_root(phase_dir=None):
    """Pin bd to the project root of `phase_dir` (the cwd's when None)."""
    global _BD_CWD
    try:
        _BD_CWD = str(phase_project_root(phase_dir) if phase_dir else find_project_root(Path.cwd()))
    except (ValueError, OSError, RuntimeError):
        # RuntimeError: Path.resolve() on a symlink loop before Python 3.13.
        _BD_CWD = None


def run_bd(argv, timeout=BD_TIMEOUT):
    """Run one bd subcommand from a typed argv list; shell interpretation is
    never enabled here -- see module docstring, T-01-01."""
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, cwd=_BD_CWD)


# Oldest bd the test suite runs against (ci.yml BD_VERSION, a 1.2.2 tarball):
# older releases lack flags it relies on, e.g. `bd list --id`.
BD_MIN_VERSION = (1, 2, 2)
BD_VERSION_RE = re.compile(r"\bversion\s+v?(\d+)\.(\d+)\.(\d+)")
_BD_VERSION_OK = None  # per-process verdict of the floor check; None = not yet run


def _bd_version_ok():
    """Run `bd --version` once per process. Below BD_MIN_VERSION: one stderr
    notice and False. Output that does not parse (a dev build, a changed
    format, a failed call) proceeds as True -- refusing a bd we cannot
    identify would disable sync on every future format change, and the
    availability probe still runs."""
    global _BD_VERSION_OK
    if _BD_VERSION_OK is None:
        try:
            out = run_bd(["bd", "--version"]).stdout or ""
        except (subprocess.TimeoutExpired, OSError):
            out = ""
        m = BD_VERSION_RE.search(out if isinstance(out, str) else "")
        found = tuple(int(g) for g in m.groups()) if m else None
        _BD_VERSION_OK = found is None or found >= BD_MIN_VERSION
        if not _BD_VERSION_OK:
            print(
                f"bd {'.'.join(map(str, found))} is older than the minimum "
                f"{'.'.join(map(str, BD_MIN_VERSION))} -- treating bd as unavailable; upgrade bd",
                file=sys.stderr,
            )
    return _BD_VERSION_OK


def bd_available():
    """B6/D-08 fail-open detection point: locate the binary, check its version
    floor, run one cheap read command. Absent, too old, non-zero exit, or
    timeout all take the same "unavailable" path -- this function is the
    single point of truth for that decision."""
    if shutil.which("bd") is None or not _bd_version_ok():
        return False
    try:
        result = run_bd(["bd", "list", "--json", "-n", "1"])
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


LOCK_FILE_NAME = ".gsd-beads.lock"


@contextlib.contextmanager
def _project_lock(planning_dir):
    """Exclusive flock on <planning_dir>/.gsd-beads.lock, a regular file: flock
    on a directory fd is EBADF on NFS. Used by append_state_blocker and
    ensure_issue, so neither may be called while the other's lock is held (two
    fds on one file deadlock even inside one process). Any OSError opening or
    locking degrades to one stderr notice and an unlocked body; the body's own
    exceptions propagate untouched."""
    fd = None
    try:
        fd = os.open(
            Path(planning_dir) / LOCK_FILE_NAME,
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
            0o600,
        )
        fcntl.flock(fd, fcntl.LOCK_EX)
    except OSError as exc:
        print(f"{LOCK_FILE_NAME}: cannot lock ({exc}); proceeding unlocked", file=sys.stderr)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)


def append_state_blocker(state_path, message):
    """Append one dated bullet under STATE.md's Blockers/Concerns heading
    (D-08). `message` is folded onto one line first (gh-17 F-05): a message
    built from plan text -- e.g. a task `<name>` -- carries no authored
    newlines a reader would trust, so one must never let it inject its own
    bullet or markdown heading into STATE.md. Deduped on (date, message),
    not message alone (gh-17 F-04 / review finding): the same parse failure
    is reachable through more than one read path in one lifecycle dispatch
    and must not double the bullet that day, but a failure that is still
    happening a day later must still get its own dated bullet -- deduping
    on message alone would silence a genuinely recurring failure forever
    after its first day."""
    state_path = Path(state_path)
    if not state_path.exists():
        return
    if state_path.is_symlink():
        # A planted STATE.md -> elsewhere would take this append.
        print(f"STATE.md note skipped: {state_path} is a symlink", file=sys.stderr)
        return
    # Serialise the whole read-modify-write on the project lock file: the
    # atomic replace below swaps STATE.md's inode, so a lock on STATE.md
    # itself would be held on a dead file. A note that cannot be written
    # (read-only tree) is dropped with a notice: every caller is a fail-open
    # path that must not raise.
    try:
        with _project_lock(state_path.parent):
            text = state_path.read_text(encoding="utf-8")
            # A heading inside a fenced example is not the section; the mask keeps
            # every offset, so an index found in it is valid in `text`.
            idx = _mask_fenced_code_blocks(text).find("### Blockers/Concerns")
            if idx == -1:
                return
            message = " ".join(message.split())
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            # CodeRabbit: compare the complete bullet line, not a bare substring --
            # "failure" is a substring of an already-present "failure with details"
            # bullet, so the naive `bullet in text` check silently dropped a
            # genuinely distinct, shorter message.
            bullet_line = f"- {date}: {message}"
            if bullet_line in text.splitlines():
                return
            line_end = text.find("\n", idx)
            if line_end == -1:
                line_end = len(text)
            _atomic_write_text(state_path, text[:line_end] + f"\n\n{bullet_line}" + text[line_end:])
    except OSError as exc:
        print(f"STATE.md note skipped: {exc}", file=sys.stderr)


def find_project_root(start):
    """Walk up from `start` to the nearest ancestor containing `.planning/`.

    Guards T-01-02: every path this script reads or writes is confined to
    this resolved root, never derived unchecked from artifact text.
    """
    current = start.resolve()
    for _ in range(10):
        if (current / ".planning").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise ValueError(f"could not locate a .planning/ ancestor above {start}")


def phase_project_root(phase_dir):
    """Project root of a phase directory taken from argv. The lookup starts at
    the phase dir's parent, so a planted <phase>/.planning/ is never taken for
    the project root (it would redirect bd, the config read and the STATE.md
    blocker). Every phase-argument root lookup goes through here."""
    return find_project_root(Path(phase_dir).resolve().parent)


def _skip_bd_unavailable(start, label):
    """B6/D-08: the shared bd-unavailable fail-open tail -- print NOTICE and
    record one STATE.md blocker naming `label` when a project root is found
    above `start` (none found: notice only)."""
    print(NOTICE)
    try:
        project_root = phase_project_root(start)
    except ValueError:
        return
    append_state_blocker(
        confined(project_root, ".planning", "STATE.md"),
        f"bd unavailable -- {label} skipped (B6/D-08)",
    )


def confined(root, *parts):
    """Join parts onto root and reject any resolved escape (T-01-02).
    Callers pass constant path components here (".planning", "STATE.md",
    etc); the genuinely variable input in this file -- a `phase_dir`/
    `plan_path` taken from argv -- is deliberately not routed through this
    guard, since argv is this script's trusted principal (a human or an
    already-trusted harness invokes the CLI directly, unlike PLAN.md text,
    which a different, weaker principal authors -- see the module docstring
    and T-01-02's own threat model). The one exception is `lifecycle_dispatch`'s
    optional phase argument: the hook path may one day carry it, so it is
    resolved and confined to a direct child of `.planning/phases`."""
    candidate = root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError(f"path escapes project root: {candidate} not under {root}")
    return candidate


def _scan_task_attributes(opening_tag):
    """Return quote-aware ``(name, value, start, end)`` task attributes."""
    if not opening_tag.startswith("<task"):
        return [], False

    attributes = []
    i = len("<task")
    limit = len(opening_tag)
    delimiters = " \t\r\n=/>"
    while i < limit:
        separator_start = i
        while i < limit and opening_tag[i].isspace():
            i += 1
        if i < limit and opening_tag[i] == ">":
            return attributes, True
        if opening_tag.startswith("/>", i):
            return attributes, False
        if i == separator_start:
            return attributes, False

        name_start = i
        while i < limit and opening_tag[i] not in delimiters:
            i += 1
        if i == name_start:
            return attributes, False
        name = opening_tag[name_start:i]
        while i < limit and opening_tag[i].isspace():
            i += 1
        if i >= limit or opening_tag[i] != "=":
            return attributes, False
        i += 1
        while i < limit and opening_tag[i].isspace():
            i += 1
        if i >= limit or opening_tag[i] not in ('"', "'"):
            return attributes, False
        quote = opening_tag[i]
        value_start = i + 1
        value_end = opening_tag.find(quote, value_start)
        if value_end == -1:
            return attributes, False
        attributes.append(
            (name, opening_tag[value_start:value_end], name_start, value_end + 1)
        )
        i = value_end + 1

    return attributes, False


class PlanParseError(ValueError):
    """A plan's raw task openings cannot be mapped to closed task blocks."""


class IdentityPersistError(Exception):
    """Issue ids were created in bd but could not be written into the plan."""


class EpicAuthorityError(ValueError):
    """An epic id is unsafe or does not match exact live bd authority."""


def parse_beads_epic(frontmatter):
    """Return one safe epic id, rejecting malformed or duplicate authority."""
    declarations = list(BEADS_EPIC_DECL_RE.finditer(frontmatter))
    if len(declarations) > 1:
        raise EpicAuthorityError("duplicate beads_epic declarations")
    if not declarations:
        return None
    epic_id = declarations[0].group(1).strip()
    if not SAFE_BD_ID_RE.fullmatch(epic_id):
        raise EpicAuthorityError(f"unsafe or malformed beads_epic: {epic_id!r}")
    return epic_id


def _mask_code_spans(text):
    """Blank fenced code blocks and inline code spans to same-length
    whitespace (gh-17) -- a `<task>` mentioned in prose must not count as a
    real opener. Length-preserving so every match offset taken against the
    masked copy is also a valid offset into the real `text`."""
    # Standards review: Middle Man -- inlined, single call site; line
    # numbers and match offsets in the masked copy stay valid against the
    # real text (gh-17) since `_blank` preserves every `\r`/`\n` byte.
    return INLINE_CODE_RE.sub(lambda m: _blank(m.group(0)), _mask_fenced_code_blocks(text))


def parse_plan(path):
    """Return (full_text, frontmatter_body, [task dict, ...]).

    Anchors on `<name>...</name>` inside each `<task ...>...</task>` block --
    real PLAN.md files carry no markdown task heading to anchor on instead.
    """
    with Path(path).open("r", encoding="utf-8", newline="") as plan_file:
        text = plan_file.read()
    fm_match = FRONTMATTER_RE.match(text)
    frontmatter = fm_match.group(1) if fm_match else ""
    # gh-17: opener/closer counting and task-block discovery both run against
    # the masked copy, never the real `text` -- a real, balanced <task> block
    # quoted whole inside a fence must not be discovered as a live task, and
    # a prose-only <task> mention must not inflate the raw-opener count.
    masked_text = _mask_code_spans(text)
    raw_open_starts = [match.start() for match in RAW_TASK_OPEN_RE.finditer(masked_text)]
    task_matches = list(TASK_RE.finditer(masked_text))
    closed_open_starts = [match.start() for match in task_matches]
    if raw_open_starts != closed_open_starts:
        raise PlanParseError(
            "task structure invalid: every exact <task opener must map one-to-one "
            "to a structurally closed task block"
        )

    tasks = []
    for m in task_matches:
        # Masking is length-preserving, so m's span is also valid against
        # the real text -- slice the real text for actual task content;
        # `m.group(0)` would return the blanked-out masked copy instead.
        block = text[m.start() : m.end()]
        opening_tag_m = TASK_OPEN_TAG_RE.match(block)
        opening_tag = opening_tag_m.group(0) if opening_tag_m else ""
        attributes, attributes_valid = _scan_task_attributes(opening_tag)
        name_m = NAME_RE.search(block)
        id_matches = list(BEADS_ID_RE.finditer(block))
        beads_ids = [match.group(1).strip() for match in id_matches]
        files_m = FILES_RE.search(block)
        type_attributes = [attribute for attribute in attributes if attribute[0] == "type"]
        tracker_attributes = [
            attribute for attribute in attributes if attribute[0] == "tracker-id"
        ]
        native_opening_end = opening_tag.find(">")
        tracker_ids = [attribute[1] for attribute in tracker_attributes]
        tracker_id_candidates = [
            attribute
            for attribute in attributes
            if attribute[0].lower().endswith("tracker-id")
        ]
        read_first_m = READ_FIRST_RE.search(block)
        precondition_m = PRECONDITION_RE.search(block)
        behavior_m = BEHAVIOR_RE.search(block)
        action_m = ACTION_RE.search(block)
        verify_m = VERIFY_RE.search(block)
        acceptance_criteria_m = ACCEPTANCE_CRITERIA_RE.search(block)
        done_m = DONE_RE.search(block)
        decision_m = DECISION_RE.search(block)
        context_m = CONTEXT_RE.search(block)
        options_m = OPTIONS_RE.search(block)
        selection_prompt_m = SELECTION_PROMPT_RE.search(block)
        what_built_m = WHAT_BUILT_RE.search(block)
        how_to_verify_m = HOW_TO_VERIFY_RE.search(block)
        resume_signal_m = RESUME_SIGNAL_RE.search(block)
        files = (
            [f.strip() for f in files_m.group(1).split(",") if f.strip()]
            if files_m
            else []
        )
        tasks.append(
            {
                "name": name_m.group(1).strip() if name_m else "",
                "name_end": m.start() + (name_m.end() if name_m else 0),
                "beads_id": beads_ids[0] if beads_ids else None,
                "beads_ids": beads_ids,
                "beads_id_span": (
                    (m.start() + id_matches[0].start(), m.start() + id_matches[0].end())
                    if id_matches
                    else None
                ),
                "files": files,
                "type": type_attributes[0][1] if len(type_attributes) == 1 else "",
                "type_attribute_count": len(type_attributes),
                "attributes_valid": attributes_valid,
                "native_identity_readable": (
                    native_opening_end >= 0
                    and len(type_attributes) == 1
                    and type_attributes[0][3] <= native_opening_end
                    and all(
                        attribute[3] <= native_opening_end
                        for attribute in tracker_attributes
                    )
                ),
                "tracker_ids": tracker_ids,
                "tracker_id_candidates": tracker_id_candidates,
                "tracker_insert": (
                    m.start() + type_attributes[0][3]
                    if len(type_attributes) == 1
                    else None
                ),
                "read_first": read_first_m.group(1).strip() if read_first_m else "",
                "precondition": precondition_m.group(1).strip() if precondition_m else None,
                "behavior": behavior_m.group(1).strip() if behavior_m else "",
                "action": action_m.group(1).strip() if action_m else "",
                "verify": verify_m.group(1).strip() if verify_m else "",
                "acceptance_criteria": (
                    acceptance_criteria_m.group(1).strip() if acceptance_criteria_m else ""
                ),
                "done": done_m.group(1).strip() if done_m else "",
                # CR-01: checkpoint:decision/checkpoint:human-verify content,
                # empty for every auto/tracer task -- consumed only by
                # _checkpoint_task_description().
                "decision": decision_m.group(1).strip() if decision_m else "",
                "context": context_m.group(1).strip() if context_m else "",
                "options": options_m.group(1).strip() if options_m else "",
                "selection_prompt": (
                    selection_prompt_m.group(1).strip() if selection_prompt_m else ""
                ),
                "what_built": what_built_m.group(1).strip() if what_built_m else "",
                "how_to_verify": how_to_verify_m.group(1).strip() if how_to_verify_m else "",
                "resume_signal": resume_signal_m.group(1).strip() if resume_signal_m else "",
            }
        )
    return text, frontmatter, tasks


def parse_depends_on(frontmatter):
    """Return the plan-level `depends_on` array as a list of bare plan-id
    strings, quotes and whitespace stripped. Absent or empty -> [].

    This is the sole cross-plan edge source (dependency_derivation_decision,
    D-04): the `wave` frontmatter key is deliberately never inspected here or
    anywhere edges are derived.

    Accepts both YAML forms (WR-04): the inline flow sequence
    (`depends_on: ["01-01"]`) and the block-list form (`depends_on:` on its
    own line, followed by `- "01-01"` list items) -- a block-list value
    silently produced `[]` before this fix, indistinguishable from a
    legitimately empty dependency list.
    """
    m = DEPENDS_ON_RE.search(frontmatter)
    if m:
        inner = m.group(1).strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]

    m = DEPENDS_ON_BLOCK_RE.search(frontmatter)
    if not m:
        return []
    items = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        item = line[1:].strip().strip('"').strip("'")
        if item:
            items.append(item)
    return items


def parse_todo_files_block(frontmatter):
    """Return a todo's `files:` block-list values, quotes/whitespace
    stripped. Absent -> [] (B12, Pattern 1: `DEPENDS_ON_BLOCK_RE`'s
    block-item extraction technique, cloned and scoped to `files:`)."""
    m = FILES_BLOCK_RE.search(frontmatter)
    if not m:
        return []
    items = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        item = line[1:].strip().strip('"').strip("'")
        if item:
            items.append(item)
    return items


def parse_resolves_issues(frontmatter):
    """Return a SUMMARY.md's `resolves_issues` frontmatter array as a list of
    raw, unvalidated strings, quotes/whitespace stripped (260820-j6g, bd
    gsd-beads-72u). Absent -> [].

    Structurally identical to parse_depends_on: inline-flow form tried
    first, block-list form as fallback. Performs no id-shape validation --
    that check belongs at `_resolve_marked_issue_ids`, the one place these
    values cross into a `bd close` argv."""
    m = RESOLVES_ISSUES_RE.search(frontmatter)
    if m:
        inner = m.group(1).strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]

    m = RESOLVES_ISSUES_BLOCK_RE.search(frontmatter)
    if not m:
        return []
    items = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        item = line[1:].strip().strip('"').strip("'")
        if item:
            items.append(item)
    return items


def _unquote(value):
    """Strip one matching pair of surrounding quotes from a frontmatter value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1].strip()
    return value


def parse_todo(path):
    """Return {title, severity, area, files, problem, solution} for one
    `.planning/todos/pending/*.md` file (add-todo.md's schema).

    Raises ValueError (never returns a partially-populated dict) when the
    frontmatter has no closing `---`, `title` is absent, or `severity` is
    absent/not a `SEVERITY_TO_PRIORITY` key (D-04) -- migrate_todos catches
    this per-file and leaves the file untouched. `area` defaults to
    "general" when absent, matching add-todo.md's own "unclear -> general"
    convention.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        raise ValueError(f"{path.name}: no closing frontmatter '---' found")
    frontmatter = fm_match.group(1)
    body = text[fm_match.end():]

    title_m = TITLE_RE.search(frontmatter)
    title = _unquote(title_m.group(1)) if title_m else ""
    if not title:
        raise ValueError(f"{path.name}: missing 'title' frontmatter key")

    severity_m = SEVERITY_RE.search(frontmatter)
    if not severity_m or severity_m.group(1) not in SEVERITY_TO_PRIORITY:
        raise ValueError(
            f"{path.name}: missing or unrecognized 'severity' frontmatter key"
        )
    severity = severity_m.group(1)

    area_m = AREA_RE.search(frontmatter)
    # `area: a, b` / `a,b` names several areas; one area-<x> label each.
    areas = re.split(r"[,\s]+", area_m.group(1)) if area_m else []
    area = ",".join(a for a in areas if a) or "general"

    files = parse_todo_files_block(frontmatter)

    problem_m = PROBLEM_RE.search(body) or PROBLEM_FALLBACK_RE.search(body)
    problem = problem_m.group(1).strip() if problem_m else ""
    solution_m = SOLUTION_RE.search(body)
    solution = solution_m.group(1).strip() if solution_m else ""

    return {
        "title": title,
        "severity": severity,
        "area": area,
        "files": files,
        "problem": problem,
        "solution": solution,
    }


def _todo_description(todo):
    """Fold problem/solution (and files, when present) into one `-d` prose
    string (D-03: `files:` has no structured bd field, so it carries as a
    "## Files" section appended only when non-empty)."""
    desc = f"## Problem\n{todo['problem']}\n\n## Solution\n{todo['solution']}\n"
    if todo["files"]:
        desc += "\n## Files\n" + "\n".join(f"- {f}" for f in todo["files"]) + "\n"
    return desc


def _task_description(task):
    """Fold a task's read_first/precondition/behavior/action/verify/done and
    files content into one `-d` prose string (D-02/D-06), cloning
    `_todo_description`'s exact shape: markdown `##` section headers, each
    appended only when its source field is non-empty. Section order mirrors
    execution order: Read First, Precondition, Behavior, Action, Verify,
    Done, Files (Files last, exactly like `_todo_description`'s trailing
    files section -- `files` has no structured bd field, same reason
    `_todo_description` folds it in rather than using a flag).

    `acceptance_criteria` is deliberately NOT rendered here -- it travels as
    bd's own structured `--acceptance` field instead. `bd show --json`
    returns `description` and `acceptance_criteria` as two distinct
    top-level keys (16-RESEARCH.md Priority 2, live-verified). A future
    editor should not "helpfully" fold it back into this string.

    `<behavior>` is included even though CONTEXT.md's D-02 field list does
    not name it (16-01-PLAN.md Discretion call): `workflow.tdd_mode` is true
    for this project, so most future tasks carry a `<behavior>` block --
    leaving it in PLAN.md while everything else moves to bd would split one
    task's instructions across two sources and defeat the self-sufficiency
    goal.
    """
    sections = []
    if task["read_first"]:
        # gh#24: prose may carry commas, so a comma splits only when every
        # piece is a bare path (no whitespace or parentheses, a `.` or `/`); otherwise one line is one item, verbatim.
        lines = [ln.strip() for ln in task["read_first"].splitlines()]
        pieces = [f.strip() for f in lines[0].split(",") if f.strip()]
        if len(lines) == 1 and all(re.fullmatch(r"[^\s()]*[./][^\s()]*", p) for p in pieces):
            lines = pieces
        items = [ln[2:].strip() if ln.startswith("- ") else ln for ln in lines]
        sections.append("## Read First\n" + "\n".join(f"- {f}" if f else "" for f in items))
    if task["precondition"]:
        sections.append(f"## Precondition\n{task['precondition']}")
    if task["behavior"]:
        sections.append(f"## Behavior\n{task['behavior']}")
    if task["action"]:
        sections.append(f"## Action\n{task['action']}")
    if task["verify"]:
        sections.append(f"## Verify\n{task['verify']}")
    if task["done"]:
        sections.append(f"## Done\n{task['done']}")
    if task["files"]:
        sections.append("## Files\n" + "\n".join(f"- {f}" for f in task["files"]))
    return "\n\n".join(sections) + ("\n" if sections else "")


def _resolver_fail(category):
    """Emit one bounded resolver diagnostic and keep stdout protocol-clean."""
    print(category[:2000], file=sys.stderr)
    return 1


def resolve_task_content(issue_id):
    """Resolve one Beads task through the deliberately narrow native seam."""
    if not SAFE_BD_ID_RE.fullmatch(issue_id):
        return _resolver_fail("invalid id")

    try:
        result = run_bd(["bd", "show", issue_id, "--json"], timeout=8)
    except subprocess.TimeoutExpired:
        return _resolver_fail("bd timeout")
    except (OSError, UnicodeError):
        return _resolver_fail("bd unavailable")

    if result.returncode != 0:
        return _resolver_fail("bd failed")
    if not isinstance(result.stdout, str):
        return _resolver_fail("invalid json")
    try:
        payload = json.loads(result.stdout)
    except (UnicodeError, json.JSONDecodeError):
        return _resolver_fail("invalid json")

    if isinstance(payload, dict):
        payload = payload.get("data")
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        return _resolver_fail("invalid envelope")
    row = payload[0]
    if row.get("id") != issue_id:
        return _resolver_fail("id mismatch")
    description = row.get("description")
    if not isinstance(description, str) or not description.strip():
        return _resolver_fail("invalid description")
    criteria = row.get("acceptance_criteria")
    if criteria is None:
        criteria_items = []
    elif isinstance(criteria, str):
        criteria_items = [
            line.strip().removeprefix("-").removeprefix("*").strip()
            for line in criteria.splitlines()
            if line.strip()
        ]
    else:
        return _resolver_fail("invalid acceptance")

    extracted = {"Read First": None, "Verify": None, "Done": None}
    retained, current, active = [], [], None
    fence = None
    for line in description.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if fence is not None:
            current.append(line)
            # CodeRabbit: `re.match` only required the line to *start with*
            # the opener -- "``` not a closer" therefore closed the fence,
            # and a closer indented by up to 3 spaces (CommonMark-legal)
            # was rejected. Require the whole (stripped) line to be the
            # fence character, at least the opener's own length, with only
            # leading indent/trailing whitespace around it -- same shape as
            # _mask_fenced_code_blocks' close_re.
            if re.fullmatch(rf"[ \t]{{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*", stripped):
                fence = None
            continue
        # Review finding: `[\\x60~]` (double backslash, inside a raw string)
        # matches literal `\`, `x`, `6`, `0`, `~` -- never a real backtick --
        # so a backtick-fenced example was never masked here, and a stray
        # run of 3+ x/6/0/\ characters was misread as a phantom fence
        # opener. Matches sync.py's own established fence-detection idiom
        # elsewhere (_FENCE_OPEN_RE).
        opening = re.match(r"^(`{3,}|~{3,})", stripped)
        if opening:
            fence = opening.group(1)
            current.append(line)
            continue
        heading = re.fullmatch(r"## (Read First|Verify|Done)", stripped)
        if heading:
            if active is not None:
                extracted[active] = "".join(current).strip()
            else:
                retained.extend(current)
            active, current = heading.group(1), []
            if extracted[active] is not None:
                return _resolver_fail("duplicate heading")
            continue
        if re.fullmatch(r"## .+", stripped):
            if active is not None:
                extracted[active] = "".join(current).strip()
                active = None
            else:
                retained.extend(current)
            retained.append(line)
            current = []
            continue
        current.append(line)
    if active is not None:
        extracted[active] = "".join(current).strip()
    else:
        retained.extend(current)

    retained_description = "".join(retained).strip()
    if not retained_description:
        return _resolver_fail("invalid description")
    read_first = []
    if extracted["Read First"]:
        for line in extracted["Read First"].splitlines():
            if not line.strip():
                continue
            if not line.startswith("- ") or not line[2:].strip():
                return _resolver_fail("invalid read first")
            read_first.append(line[2:].strip())

    print(
        json.dumps(
            {
                "description": retained_description,
                "read_first": read_first,
                "verify": extracted["Verify"] or None,
                "acceptance_criteria": criteria_items,
                "done": extracted["Done"] or None,
            }
        )
    )
    return 0


def _normalized(text):
    """Line-ending- and trailing-space-insensitive form for comparing what bd
    stored with what was sent."""
    if not isinstance(text, str):
        return ""
    return "\n".join(ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")).strip()


def _intact_ids(by_id):
    """Ids in by_id (issue id -> task) whose stored bd description and
    acceptance criteria equal what create sent. One batched `bd show`; a
    mismatch gets one repair rewrite and a re-check, because a task is only
    strip-eligible in the run that created it. Any bd failure counts as not
    intact."""

    def stored():
        try:
            result = run_bd(["bd", "show", *sorted(by_id), "--json"])
            payload = json.loads(result.stdout) if result.returncode == 0 else []
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return {}
        if isinstance(payload, dict):
            payload = payload.get("data")
        rows = payload if isinstance(payload, list) else []
        return {r.get("id"): r for r in rows if isinstance(r, dict)}

    def matches(row, task):
        return _normalized(row.get("description")) == _normalized(_task_description(task)) and (
            _normalized(row.get("acceptance_criteria")) == _normalized(task["acceptance_criteria"])
        )

    rows = stored()
    intact = {i for i, row in rows.items() if i in by_id and matches(row, by_id[i])}
    for issue_id in sorted(set(rows) & set(by_id) - intact):
        task = by_id[issue_id]
        argv = ["bd", "update", issue_id, "-d", _task_description(task)]
        argv += ["--acceptance", task["acceptance_criteria"] or ""]
        try:
            run_bd(argv)
        except (OSError, subprocess.TimeoutExpired):
            continue
    if len(intact) < len(by_id) and rows:
        rows = stored()
        intact |= {i for i, row in rows.items() if i in by_id and matches(row, by_id[i])}
    return intact


def _checkpoint_task_description(task):
    """Fold a checkpoint:decision/checkpoint:human-verify task's real content
    into one `-d` prose string (CR-01), same "## section, only when non-empty"
    shape as `_task_description` -- but a distinct field set, since D-03 keeps
    checkpoint content in its own tags (`<decision>`/`<context>`/`<options>`/
    `<selection-prompt>` for checkpoint:decision, `<what-built>`/
    `<how-to-verify>`/`<resume-signal>` for checkpoint:human-verify) rather
    than the auto/tracer shape `_task_description` reads. `resolve_issue`
    dispatches here for any `checkpoint:*`-typed task so its `bd create -d`
    is never the auto/tracer renderer's empty string for fields it doesn't
    know about (16-01-PLAN.md's D-06 must-have: a non-empty description)."""
    sections = []
    if task.get("decision"):
        sections.append(f"## Decision\n{task['decision']}")
    if task.get("context"):
        sections.append(f"## Context\n{task['context']}")
    if task.get("options"):
        sections.append(f"## Options\n{task['options']}")
    if task.get("selection_prompt"):
        sections.append(f"## Selection Prompt\n{task['selection_prompt']}")
    if task.get("what_built"):
        sections.append(f"## What Built\n{task['what_built']}")
    if task.get("how_to_verify"):
        sections.append(f"## How To Verify\n{task['how_to_verify']}")
    if task.get("resume_signal"):
        sections.append(f"## Resume Signal\n{task['resume_signal']}")
    return "\n\n".join(sections) + ("\n" if sections else "")


def migrate_todos(pending_dir_arg):
    """B12: one-shot migration of every parseable
    `.planning/todos/pending/*.md` file into a mapped bd issue, then delete
    that file (D-05); an unparseable file is left untouched and reported
    under "could not be interpreted", distinct from a "bd create failed"
    entry (D-04/Pitfall 2). Each todo is created through ensure_issue under
    a key derived from its file name and title, so a rerun after an
    ambiguous timeout or an undeletable file adopts the issue instead of
    duplicating it. A file is deleted only after a SAFE_BD_ID_RE-valid id
    (R20); a failure on one file is recorded and the loop continues.
    """
    if not bd_available():
        _skip_bd_unavailable(Path(pending_dir_arg).resolve(), "migrate-todos")
        return 0

    pending_dir = Path(pending_dir_arg)
    if not pending_dir.is_dir():
        print("no pending todos found")
        return 0
    todo_paths = sorted(pending_dir.glob("*.md"))
    if not todo_paths:
        print("no pending todos found")
        return 0

    moved = []
    parse_errors = []
    bd_create_failed = []
    not_deleted = []
    for todo_path in todo_paths:
        try:
            todo = parse_todo(todo_path)
        except ValueError as exc:
            parse_errors.append((todo_path.name, str(exc)))
            continue

        key = "gsd-key:todo-" + hashlib.sha1(
            f"{todo_path.name}\0{todo['title']}".encode("utf-8")
        ).hexdigest()[:12]
        try:
            issue_id = ensure_issue(
                key,
                [
                    "bd",
                    "create",
                    "--title",
                    todo["title"],
                    "-d",
                    _todo_description(todo),
                    "-t",
                    "task",
                    "-p",
                    str(SEVERITY_TO_PRIORITY[todo["severity"]]),
                    "-l",
                    ",".join(f"area-{a}" for a in todo["area"].split(",")),
                    "--silent",
                ],
                "task",
            )
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            # The file stays; a rerun looks the key up first, so whatever
            # bd may have written is adopted, never duplicated.
            bd_create_failed.append((todo_path.name, f"{type(exc).__name__}: {exc}"))
            continue
        try:
            todo_path.unlink()  # D-05: delete only after a confirmed issue id
        except OSError as exc:
            not_deleted.append(
                (todo_path.name, f"created {issue_id} but could not delete the todo file ({exc}); delete it manually")
            )
            continue
        moved.append((todo_path.name, issue_id))

    lines = [
        f"Migrated {len(moved)} todo(s), {len(parse_errors)} could not be interpreted, "
        f"{len(bd_create_failed)} bd create failed, {len(not_deleted)} created but not deleted"
    ]
    if moved:
        lines.append("  moved:")
        lines.extend(f"    {_sanitize_notice_value(name, 200)} -> {issue_id}" for name, issue_id in moved)
    if parse_errors:
        lines.append("  could not be interpreted:")
        lines.extend(
            f"    {_sanitize_notice_value(name, 200)}: {_sanitize_notice_value(reason, 400)}"
            for name, reason in parse_errors
        )
    if bd_create_failed:
        lines.append("  bd create failed:")
        lines.extend(
            f"    {_sanitize_notice_value(name, 200)}: {_sanitize_notice_value(reason, 400)}"
            for name, reason in bd_create_failed
        )
    if not_deleted:
        lines.append("  created but not deleted:")
        lines.extend(
            f"    {_sanitize_notice_value(name, 200)}: {_sanitize_notice_value(reason, 400)}"
            for name, reason in not_deleted
        )
    print("\n".join(lines))
    return 0


def discover_plan_files(phase_dir):
    """Map ordinal-prefix ("01-01") -> Path for every `NN-NN-PLAN.md` file
    directly in phase_dir.

    T-01-04: a `depends_on` entry is matched against this discovered set,
    never joined onto a path built from artifact text.
    """
    discovered = {}
    for candidate in Path(phase_dir).iterdir():
        m = PLAN_FILE_RE.match(candidate.name)
        if m:
            discovered[m.group(1)] = candidate
    return discovered


def collect_all_task_files(project_root):
    """Return {beads_id: [file paths]} for every task carrying a <beads-id>,
    across every `NN-NN-PLAN.md` in every phase directory under
    `.planning/phases/` (beads-recall technique 1's reverse-lookup index,
    built once per beads-recall run).

    T-02-02: every scanned path is confined to the resolved
    `.planning/phases/` root via `find_project_root`/`confined`, never
    trusted as a raw path component from artifact text.
    """
    phases_root = confined(project_root, ".planning", "phases")
    index = {}
    if not phases_root.is_dir():
        return index
    for phase_dir in sorted(p for p in phases_root.iterdir() if p.is_dir()):
        for plan_path in discover_plan_files(phase_dir).values():
            try:
                _, _, tasks = parse_plan(plan_path)
            except (OSError, UnicodeDecodeError):
                continue
            for task in tasks:
                if task["beads_id"] and task["files"]:
                    index.setdefault(task["beads_id"], []).extend(task["files"])
    return index


def resolve_prereq_last_task_id(phase_dir, prereq_plan_id):
    """Return the `<beads-id>` of prereq_plan_id's last task, or None when
    that plan cannot be found among phase_dir's discovered plans or its last
    task has no id yet.

    An unresolvable prerequisite is a sequencing fact (the prerequisite plan
    has not been synced yet), not an error -- B6's fail-open posture applies
    to the whole script.
    """
    plan_path = discover_plan_files(phase_dir).get(prereq_plan_id)
    if plan_path is None:
        return None
    _, _, tasks = parse_plan(plan_path)
    if not tasks:
        return None
    return tasks[-1]["beads_id"]


def derive_dependency_edges(task_ids, prereq_last_ids):
    """Pure: return [(blocked_id, blocker_id), ...] from declared ordering
    only (dependency_derivation_decision).

    Intra-plan edges: task at index k>0 is blocked by the task at index k-1.
    Cross-plan edges: this plan's first task is blocked by each resolved
    prerequisite plan's last task (first-blocks-on-last). Reads neither `bd`
    nor the `wave` frontmatter key -- wave number is never an edge source
    under D-04.
    """
    edges = [(task_ids[i], task_ids[i - 1]) for i in range(1, len(task_ids))]
    if task_ids:
        first_id = task_ids[0]
        edges.extend((first_id, prereq_id) for prereq_id in prereq_last_ids if prereq_id)
    return edges


def apply_dependency_edges(edges):
    """Apply each (blocked, blocker) pair via `bd dep add <blocked>
    --depends-on <blocker>`.

    Re-adding an edge that already exists exits 0 and creates no duplicate
    (verified during planning), so no separate existence probe is needed. A
    failed edge application is reported, never fatal -- B6's fail-open
    posture applies to the whole script.
    """
    for blocked_id, blocker_id in edges:
        result = run_bd(["bd", "dep", "add", blocked_id, "--depends-on", blocker_id])
        if result.returncode != 0:
            # A prerequisite plan's last beads-id is unvalidated plan text.
            print(
                f"dependency edge failed: {_sanitize_notice_value(blocked_id)} depends-on "
                f"{_sanitize_notice_value(blocker_id)}"
            )
            print(f"dependency edge failed: {result.stderr.strip()}", file=sys.stderr)


def get_phase_header(roadmap_path, phase_num):
    """Read the phase header verbatim from ROADMAP.md (D-05, no translation)."""
    text = Path(roadmap_path).read_text(encoding="utf-8")
    pattern = re.compile(rf"^###\s+(Phase\s+0*{phase_regex_token(phase_num)}\s*:.*)$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        raise ValueError(f"no ROADMAP.md header found for phase {phase_num}")
    return m.group(1).strip()


def read_beads_config(project_root, key, default):
    """Return `beads.<key>` read fresh from `.planning/config.json`, falling
    back to `default` when the file is absent, unreadable, malformed, carries
    no `beads` object, carries no such key, or carries a value of the wrong
    type -- a wrong-typed value returns the default rather than a truthiness
    guess, so `{"enabled": "false"}` cannot silently disable tracking.

    Read fresh on every call, never cached: D-11 requires the value at each
    epic-creation call site, and `lifecycle_dispatch` needs it because
    entering from a harness hook bypasses both the SKILL.md Step 1 config
    gate and the capability registry that evaluates each hook's `when`.
    """
    try:
        cfg = json.loads(
            confined(project_root, ".planning", "config.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default
    beads_cfg = cfg.get("beads") if isinstance(cfg, dict) else None
    if not isinstance(beads_cfg, dict):
        return default
    value = beads_cfg.get(key, default)
    return value if isinstance(value, type(default)) else default


# The accessors below exist so each shipped default is written down exactly
# once, next to the key it belongs to, and matches capability.json's `config`
# block. Inlining them would scatter the defaults across call sites.
def read_epic_per(project_root):
    """B14/D-11: `beads.epic_per`, default `"phase"`."""
    return read_beads_config(project_root, "epic_per", "phase")


def read_beads_enabled(project_root):
    """gh-2: `beads.enabled`, default `True` (capability.json since 0.2.0)."""
    return read_beads_config(project_root, "enabled", True)


def read_sync_mode(project_root):
    """17-02 Task 3 (D-06): `beads.sync_mode`, default `"authoritative"`
    (matches capability.json's declared default). Governs ONLY the explicit
    native `create-issues` CLI path's strip permission -- `main()`'s
    create-issues dispatch compares this against the mirror value.
    `lifecycle_dispatch`'s plan:post branch never calls this: the hook's
    `allow_strip=False` stays a literal, ungated by config (D-03). See
    `create_issues`' docstring for the full asymmetry."""
    return read_beads_config(project_root, "sync_mode", "authoritative")


# 17-03 Task 1 (D-01/D-02): the two beads.sync_mode values capability.json
# declares -- the source of truth for check_sync_mode_value's "is this
# declared" test below. Kept as a module constant rather than re-parsing
# capability.json at runtime (sync.py never reads that file; see the
# read_beads_enabled/read_sync_mode comment above for why each default is
# instead written down once, here, beside the accessor that uses it).
SYNC_MODE_VALUES = frozenset({"authoritative", "mirror"})


def _sanitize_notice_value(value, max_len=80):
    """Bound and single-line an untrusted value before it enters
    agent-readable `additionalContext` (T-17-03-02): drop every
    non-printable character -- `str.isprintable()` is False for both
    control characters and newlines -- plus `<`, `>` and backticks
    (gsd-beads-cjbc.68: a one-line `</beads_status>` still fabricates
    structure), and truncate to `max_len`. Non-string values are
    stringified first: one code path for every JSON type the key could hold."""
    text = value if isinstance(value, str) else str(value)
    text = "".join(ch for ch in text if ch.isprintable() and ch not in "<>`")
    return text[:max_len]


def check_sync_mode_value(project_root):
    """17-03 Task 2 (D-04 Case 2): read-only, never-raises notice for a
    project whose `.planning/config.json` stores a `beads.sync_mode` value
    outside the declared enum -- the retired `off` value, an empty string,
    a case/whitespace variant, or a non-string type. Called from
    `lifecycle_dispatch`'s `plan:pre` branch, beside `check_patch()`
    inside the same `try/except Exception`,
    so a failure here degrades to at most one skipped notice and cannot
    take out `beads_recall`.

    Prints to STDOUT -- the same stream `check_patch` uses for all four of
    its message paths (`not_found_msg`, `could_not_read_msg`, `present_msg`,
    `missing_msg`) (WR-01: this
    function shares that convention, it is not
    the opposite of it). `hooks/lifecycle-dispatch.sh` promotes only stdout
    into `additionalContext`; the whole point of this notice is that a user
    encounters it without taking any action, so a stderr line would be
    exactly the invisible outcome the D-04 migration answer rejects. Do
    not "fix" this to stderr.

    Presence is answered by a membership test against the RAW parsed
    `beads` mapping, before and independently of any effective-value read:
    `read_beads_config`'s `isinstance(value, type(default))` wrong-type
    guard returns the identical default for an absent key and for a
    present key of the wrong type, so the effective-value reader
    (`read_sync_mode`) alone cannot tell the two states apart
    (17-REVIEWS.md, both cross-AI reviewers, BINDING). An absent key is
    not an anomaly and produces nothing; a present key holding anything
    outside `SYNC_MODE_VALUES` always notices, including a non-string
    value -- an authoring mistake is exactly as invisible to the user as a
    misspelled string.

    Never writes to `.planning/config.json` -- a prohibition in this
    plan's `must_haves`, not merely a preference.
    """
    try:
        cfg = json.loads(
            confined(project_root, ".planning", "config.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return 0
    beads_cfg = cfg.get("beads") if isinstance(cfg, dict) else None
    if not isinstance(beads_cfg, dict) or "sync_mode" not in beads_cfg:
        return 0
    value = beads_cfg["sync_mode"]
    if isinstance(value, str) and value in SYNC_MODE_VALUES:
        return 0
    print(
        f"beads.sync_mode: stored value {_sanitize_notice_value(value)!r} is not one of "
        f"the declared values ({', '.join(sorted(SYNC_MODE_VALUES))}) -- the shipped "
        "authoritative default applies, so native task resolution permits task-body "
        "stripping. Remedy: gsd-tools config-set beads.sync_mode "
        "authoritative (or mirror)."
    )
    return 0


# TRUTH-04/D-07: a phase number (`"1.5"`, `"01.5"`, `"10.1"`, `"07"`) is
# handled as a string everywhere on this path -- never `int()`/`float()`/
# `Decimal()`. Its only consumers are regex construction (phase_regex_token)
# and an on-disk directory-prefix comparison (phase_dir_prefix); a numeric
# type would buy nothing there and would reintroduce both a parse that can
# raise on `"1.5"` and a formatting risk (`Decimal("10.10") == Decimal("10.1")`
# would silently collapse two distinct phase directories).
def phase_regex_token(phase_num):
    """Return phase_num as a regex-safe literal, integer part's leading
    zeros stripped (fractional part untouched, never stripped): `"01.5"` ->
    `1\\.5`; `"07"` -> `7`; `"010.1"` -> `10\\.1`; `"1.05"` -> `1\\.05`.
    `re.escape` is non-negotiable (D-07): both consumers (get_phase_header,
    extract_phase_mentions) interpolate this straight into a compiled
    pattern, so an unescaped `.` would become a wildcard matching any
    character (T-17-01-01)."""
    integer_part, sep, frac_part = phase_num.partition(".")
    integer_part = integer_part.lstrip("0") or "0"
    return re.escape(integer_part + sep + frac_part)


def phase_dir_prefix(phase_num):
    """Return phase_num zero-padded to the on-disk directory convention,
    integer part padded to two digits, fractional part untouched: `"1.5"` ->
    `01.5`; `"7"` -> `07`; `"10.1"` -> `10.1`; `"01.5"` -> `01.5`. Replaces
    the bare `.zfill(2)` in `_resolve_default_phase_dir`, which is a no-op
    on any already-3-character token like `"1.5"` and therefore fails to
    match an `01.5-` directory (D-07)."""
    integer_part, sep, frac_part = phase_num.partition(".")
    return integer_part.zfill(2) + sep + frac_part


def lifecycle_dispatch(point, phase_dir_arg=None):
    """gh-2: run the beads operation a lifecycle point declares, entered from
    the plugin's `PostToolUse` hook rather than from gsd-core's workflow prose.
    Why the hook exists at all is documented once, in
    `hooks/lifecycle-dispatch.sh`'s header.

    Each point maps onto an existing verb, all of them derivable from
    `phase_dir` alone. An explicit task-local phase wins over STATE.md; the
    STATE.md current phase remains the backward-compatible fallback. Explicit
    input is confined to one direct child of `.planning/phases` before any
    verb can run. `execute:wave:post` uses the phase-wide idempotent
    `reconcile_stale_closed` backstop (D-08) rather than `close_wave`, and
    `execute:wave:pre` renders a phase-wide (superset, never lossy)
    `<beads_status>` block.

    `plan:post` passes `allow_strip=False`: the hook's trigger is a substring
    of a shell command, so a spurious fire is always possible, and the one
    irreversible thing in this whole path is `strip_task_bodies` deleting the
    only copy of a task's content from PLAN.md. Creating a bd issue by mistake
    is recoverable; deleting prose is not.

    Always returns 0. Every declared hook is `onError: "skip"`, and this is
    the call site that has to honour that contract: an unknown point, an
    opted-out project, a directory with no `.planning/`, an unresolvable
    current phase, and an unexpected failure inside a verb each degrade to
    at most one notice line. `ship:pre` is deliberately absent -- it already
    dispatches through this capability's own `ship.md` patch, and adding it
    here would double-record a `ship_override`.
    """
    if point not in LIFECYCLE_DISPATCH_POINTS:
        return 0
    try:
        try:
            project_root = find_project_root(Path.cwd())
        except ValueError:
            return 0
        if not read_beads_enabled(project_root):
            return 0
        phase_dir = _resolve_default_phase_dir(project_root) if phase_dir_arg is None else None
    except Exception as exc:  # noqa: BLE001 -- onError: "skip": a deleted cwd or unreadable config must not escape
        print(f"lifecycle-dispatch {point}: skipped after an unexpected failure ({exc})", file=sys.stderr)
        return 0
    if phase_dir_arg is not None:
        try:
            phases_root = confined(project_root, ".planning", "phases")
            supplied = Path(phase_dir_arg)
            phase_dir = None
            # A bare token ("2", "01.5") is resolved the same way STATE.md's
            # current_phase is: zero-padded prefix match against phases_root's
            # children. Falls through to the literal-name/path check below
            # when nothing matches, so an exact directory name (or full path)
            # still resolves as before.
            if not supplied.is_absolute() and len(supplied.parts) == 1 and phases_root.is_dir():
                padded = phase_dir_prefix(supplied.name)
                for candidate in sorted(phases_root.iterdir()):
                    if candidate.is_dir() and candidate.name.split("-", 1)[0] == padded:
                        phase_dir = candidate
                        break
            if phase_dir is None:
                if not supplied.is_absolute():
                    supplied = (
                        phases_root / supplied
                        if len(supplied.parts) == 1
                        else project_root / supplied
                    )
                phase_dir = supplied
            # One resolve-and-confine check for token, name and path alike: a
            # symlinked child must be refused whichever way it was spelled,
            # including a link to a sibling phase (it would still resolve to a
            # direct child and dispatch the wrong phase).
            if phase_dir.is_symlink():
                raise ValueError(f"phase directory {phase_dir} is a symlink")
            phase_dir = phase_dir.resolve()
            if phase_dir.parent != phases_root or not phase_dir.is_dir():
                raise ValueError(
                    f"phase directory must be a direct child of {phases_root}"
                )
        except Exception as exc:  # noqa: BLE001 -- onError: "skip": any bad input degrades to a notice
            print(
                f"lifecycle-dispatch {point}: invalid explicit phase directory "
                f"({exc}) -- skipped",
                file=sys.stderr,
            )
            return 0
    if phase_dir is None or not phase_dir.is_dir():
        # stderr, not stdout: a repository between milestones has no
        # `.planning/phases/` at all, so this fires on every render-hooks call
        # in it. `hooks/lifecycle-dispatch.sh` promotes stdout to Claude's
        # context and leaves stderr in the debug log, so a benign skip stays
        # diagnosable without becoming per-call noise in the transcript.
        reason = (
            "no phase directory resolved from STATE.md's current_phase"
            if phase_dir_arg is None
            else f"explicit phase directory {phase_dir_arg!r} does not resolve to a directory"
        )
        print(f"lifecycle-dispatch {point}: {reason} -- skipped", file=sys.stderr)
        return 0

    try:
        if point == "plan:pre":
            beads_recall(str(phase_dir))
            # The patch-loss detector documented in beads-recall/SKILL.md's
            # Step 3.5. It was wired at plan:pre precisely so it would be
            # independent of the ship.md patch it checks -- but plan:pre was
            # itself one of the dead points, so it shared the failure mode of
            # the thing it protects. Reached from a harness hook it is finally
            # independent of gsd-core's dispatch prose altogether.
            check_patch()
            # 17-03 Task 2 (D-04 Case 2): stdout notice for an out-of-enum
            # beads.sync_mode value -- both plan:pre checks above and
            # here print to stdout and run inside this one try/except
            # alongside beads_recall; see check_sync_mode_value's docstring
            # for why stdout is the correct stream (WR-01).
            check_sync_mode_value(project_root)
        elif point == "plan:post":
            # 17-02 Task 1 (D-05): gsd-core PR #3687 adds native generic
            # kind == "step" dispatch here -- stand down rather than
            # double-dispatch once it is detected on the installed
            # workflow file. execute:wave:pre/execute:wave:post are
            # deliberately NOT gated: no upstream work covers them anywhere.
            if check_native_step_dispatch("plan:post"):
                print(
                    "lifecycle-dispatch plan:post: gsd-core now dispatches this point "
                    "natively (PR #3687) -- skipped",
                    file=sys.stderr,
                )
                return 0
            plans = discover_plan_files(phase_dir)
            if not plans:
                # stderr for the same reason as the unresolved-phase skip above.
                print(
                    f"lifecycle-dispatch plan:post: no PLAN.md in {phase_dir.name} -- skipped",
                    file=sys.stderr,
                )
                return 0
            for plan_id in sorted(plans):
                try:
                    rc = create_issues(str(plans[plan_id]), allow_strip=False)
                except Exception as exc:  # noqa: BLE001 -- one bad plan must not stop the rest
                    print(
                        f"lifecycle-dispatch plan:post: create-issues {plan_id} skipped "
                        f"after an unexpected failure ({exc})",
                        file=sys.stderr,
                    )
                    continue
                if rc:
                    print(
                        f"lifecycle-dispatch plan:post: create-issues {plan_id} exited {rc}",
                        file=sys.stderr,
                    )
        elif point == "execute:wave:pre":
            render_wave_status_block(str(phase_dir), sorted(discover_plan_files(phase_dir)))
        elif point == "execute:wave:post":
            reconcile_stale_closed(str(phase_dir))
        elif point == "verify:post":
            # 17-02 Task 2: same native-dispatch gate as plan:post above.
            if check_native_step_dispatch("verify:post"):
                print(
                    "lifecycle-dispatch verify:post: gsd-core now dispatches this point "
                    "natively (PR #3687) -- skipped",
                    file=sys.stderr,
                )
                return 0
            regenerate_beads_md(str(phase_dir))
            close_phase_epic(str(phase_dir))
    except Exception as exc:  # noqa: BLE001 -- onError: "skip" is the declared contract
        # stderr, not stdout: stdout is promoted into Claude's context.
        print(f"lifecycle-dispatch {point}: skipped after an unexpected failure ({exc})", file=sys.stderr)
    return 0


def milestone_epic_title(state_path):
    """B14: return "Milestone {milestone}: {milestone_name}" from STATE.md's
    frontmatter (RESEARCH's Open Question 1 recommendation). A missing
    `milestone:` raises RuntimeError (create_issues' B6/D-08 fail-open path);
    a missing `milestone_name:` omits the suffix."""
    text = Path(state_path).read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    frontmatter = fm_match.group(1) if fm_match else ""
    milestone_m = MILESTONE_RE.search(frontmatter)
    if not milestone_m:
        raise RuntimeError("STATE.md frontmatter has no milestone: key -- cannot title the milestone epic")
    milestone = milestone_m.group(1)
    name_m = MILESTONE_NAME_RE.search(frontmatter)
    milestone_name = _unquote(name_m.group(1)) if name_m else ""
    return f"Milestone {milestone}: {milestone_name}" if milestone_name else f"Milestone {milestone}"


def get_milestone_bullet(roadmap_path, milestone):
    """B14/D-06: return the `## Milestones` bullet line whose text contains
    `milestone` verbatim (no translation) -- modeled on `get_phase_header`,
    but unlike that function a miss returns "" rather than raising, since
    `resolve_milestone_epic` must stay fail-open (a missing bullet is a
    formatting variation, not a corrupt roadmap). A milestone epic spans
    many phases, so no single plan's <objective> describes it honestly; the
    ROADMAP milestone bullet is the one existing verbatim statement of that
    milestone's scope, mirroring get_phase_header's no-translation
    discipline."""
    try:
        text = Path(roadmap_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    section_m = re.search(
        r"^##\s+Milestones\s*$\n(.*?)(?=^##\s|\Z)", text, re.MULTILINE | re.DOTALL
    )
    if not section_m:
        return ""
    # WR-01: bare `in` containment let a milestone token that is a substring
    # of another milestone's bullet text (e.g. "v1" inside "v1.0"/"v1.1"/
    # "v1.2") match the wrong bullet. Anchor on the token's own boundaries
    # instead -- neither the char before nor after `milestone` may be a word
    # char or `.`, so "v1" cannot match inside "v1.0" (the char right after
    # "v1" there is ".", which the lookahead rejects) while still matching
    # real bullets regardless of leading emoji/bold markdown decoration
    # (e.g. "- ✅ **v1.0 milestone** -- ..."), unlike a literal
    # `^-\s*\**{milestone}` anchor would.
    token_re = re.compile(rf"(?<![\w.]){re.escape(milestone)}(?![\w.])")
    for line in section_m.group(1).splitlines():
        line = line.strip()
        if line.startswith("-") and token_re.search(line):
            return line
    return ""


def resolve_milestone_epic(project_root):
    """B14: return one epic id shared across every phase in the current
    milestone. Scans every plan's `beads_epic` frontmatter value across
    every phase directory under `.planning/phases/` (collect_all_task_files'
    cross-phase scan technique) as untrusted candidate data, then confirms
    each candidate via a live `bd show --json` title match against
    `milestone_epic_title()` -- the D-10 forward-only guard: an existing
    per-phase epic's title is always a verbatim ROADMAP phase header
    (get_phase_header), never this function's computed milestone title, so
    it structurally can never be reused here even though its id is
    discoverable by the same scan. Creates a fresh epic only when no
    candidate's live title matches.
    """
    state_path = confined(project_root, ".planning", "STATE.md")
    if not state_path.exists():
        # B6/D-08: no STATE.md means no milestone frontmatter to resolve --
        # degrade fail-open through create_issues's RuntimeError catch
        # rather than an uncaught FileNotFoundError (CR-01).
        raise RuntimeError("STATE.md not found -- cannot resolve milestone epic")
    title = milestone_epic_title(state_path)

    # 16-01 Task 2 (D-06): same STATE.md frontmatter milestone_epic_title
    # already parses -- read the bare milestone token (e.g. "v1.2") to look
    # up ROADMAP.md's own bullet for it, resolved through confined() per
    # T-01-02, never a path built from artifact text.
    state_text = state_path.read_text(encoding="utf-8")
    state_fm_match = FRONTMATTER_RE.match(state_text)
    state_frontmatter = state_fm_match.group(1) if state_fm_match else ""
    milestone_token_m = MILESTONE_RE.search(state_frontmatter)
    milestone_token = milestone_token_m.group(1) if milestone_token_m else ""
    milestone_bullet = (
        get_milestone_bullet(confined(project_root, ".planning", "ROADMAP.md"), milestone_token)
        if milestone_token
        else ""
    )

    legacy_name_m = _LEGACY_MILESTONE_NAME_RE.search(state_frontmatter)
    legacy_title = f"Milestone {milestone_token}: {legacy_name_m.group(1) if legacy_name_m else ''}"

    phases_root = confined(project_root, ".planning", "phases")
    candidate_ids = []
    if phases_root.is_dir():
        for phase_dir in sorted(p for p in phases_root.iterdir() if p.is_dir()):
            for plan_path in discover_plan_files(phase_dir).values():
                try:
                    _, plan_frontmatter, _ = parse_plan(plan_path)
                except (OSError, UnicodeDecodeError):
                    continue
                epic_id = parse_beads_epic(plan_frontmatter)
                if epic_id is not None and epic_id not in candidate_ids:
                    candidate_ids.append(epic_id)

    closed_matches = []
    for candidate_id in candidate_ids:
        check = run_bd(["bd", "show", candidate_id, "--json"])
        try:
            row = _bd_show_row(check, candidate_id)
        except BdTransientError:
            raise
        except RuntimeError as exc:
            raise EpicAuthorityError(str(exc)) from exc
        if row is None:
            continue
        candidate_title = row.get("title")
        if not isinstance(candidate_title, str) or not candidate_title.strip():
            if row.get("status") == "closed":
                continue
            raise EpicAuthorityError(
                f"bd show returned invalid title for {candidate_id!r}"
            )
        # `Milestone <m>: ` is the title older versions wrote whenever
        # milestone_name was multi-word (single-token regex); reuse, not duplicate.
        if candidate_title.rstrip() in (title, legacy_title.rstrip()):
            # A closed milestone epic is history: reusing it would hang new
            # work under a finished milestone.
            if row.get("status") == "closed":
                closed_matches.append(candidate_id)
            else:
                return candidate_id

    if closed_matches:
        print(
            f"divergence: closed epic {closed_matches[0]} matched title "
            f"{_sanitize_notice_value(title, 200)!r} but is "
            "ignored (a closed epic is never reused) -- creating a new epic"
        )
    elif candidate_ids:
        print(
            f"divergence: {len(candidate_ids)} existing epic(s) found for this milestone but "
            f"none matched title {_sanitize_notice_value(title, 200)!r} -- creating a new "
            "epic (STATE.md milestone/"
            "milestone_name may have changed)"
        )

    argv = ["bd", "create", title]
    if milestone_bullet:
        argv += ["-d", _epic_description(milestone_bullet)]
    argv += ["-l", SYNC_LABEL, "--type", "epic", "--silent"]
    # bd labels are comma-separated on create, so the slug keeps only
    # [a-z0-9.] runs: "Milestone v1.0: core mvp" -> milestone-v1.0-core-mvp.
    slug = "-".join(re.findall(r"[a-z0-9.]+", title.lower().removeprefix("milestone ")))
    return ensure_issue(f"gsd-key:milestone-{slug}", argv, "epic")


def _unwrap_bd_list(payload):
    """Return the row list from an already-json.loads'd `bd list` payload.
    Review finding: `_bd_show_row`/`resolve_task_content` already unwrap a
    `{"data": [...]}` envelope for `bd show`; every `bd list` reader in this
    file assumed a bare list instead, so the two commands' response
    handling could silently drift apart. Not currently observed from a real
    `bd` (verified empirically: bd 1.3.0's `list` and `show` both return a
    bare list) -- this is the same forward-compatibility posture as the
    `show` side, applied consistently rather than only where a payload
    happened to already be enveloped once."""
    if isinstance(payload, dict):
        payload = payload.get("data")
    return payload if isinstance(payload, list) else []


class BdTransientError(RuntimeError):
    """A bd command failed without proving the record is absent (lock,
    timeout, crash). Distinct from absence: callers must not treat the
    record as stale, and create_issues takes its fail-open notice path."""


# `bd show <missing>` exits 1 with "Issue <id> not found" on stderr and a
# {"error": "no issues found matching ..."} object on stdout.
BD_NOT_FOUND_RE = re.compile(
    r"\bno issues? found matching|^\s*issue \S+ not found", re.IGNORECASE | re.MULTILINE
)


def _bd_show_row(result, expected_id):
    """Return the exact identified row, None on confirmed absence, or fail
    closed (BdTransientError on any other non-zero exit)."""
    if result.returncode != 0:
        output = f"{result.stderr or ''}\n{result.stdout or ''}"
        if BD_NOT_FOUND_RE.search(output):
            return None
        raise BdTransientError(
            f"bd show {expected_id} failed without confirming absence: "
            f"{(result.stderr or '').strip()}"
        )
    if not isinstance(result.stdout, str):
        raise RuntimeError("bd show returned invalid JSON")
    try:
        payload = json.loads(result.stdout)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("bd show returned invalid JSON") from exc
    if isinstance(payload, dict):
        payload = payload.get("data")
    if (
        not isinstance(payload, list)
        or len(payload) != 1
        or not isinstance(payload[0], dict)
        or payload[0].get("id") != expected_id
    ):
        raise RuntimeError(f"bd show did not identify {expected_id!r}")
    return payload[0]


def _open_key_rows(key, kind, title):
    """Non-closed `kind` rows labelled `key` and titled `title`, oldest first
    by (created_at, id). Filtering on issue_type is load-bearing: bd copies a
    parent's labels onto every child created with --parent, so an epic's key
    also labels each of its tasks. The title must match too: a task key
    carries its ordinal, which shifts when a plan is edited, so a replaced
    task would otherwise adopt (and run) its predecessor's issue. created_at
    has one-second granularity, so the id breaks ties and every process
    agrees on the same winner."""
    result = run_bd(["bd", "list", "-l", key, "--all", "-n", "0", "--json"])
    rows = _checked_bd_list_rows(result)
    if rows is None:
        raise BdTransientError(f"bd list -l {key} failed: {(result.stderr or '').strip()}")
    return sorted(
        (
            r for r in rows
            if isinstance(r, dict) and r.get("issue_type") == kind and r.get("title") == title
            and r.get("status") != "closed" and isinstance(r.get("id"), str)
        ),
        key=lambda r: (str(r.get("created_at", "")), r["id"]),
    )


def ensure_issue(key, create_args, kind):
    """Return the id of the one open `kind` issue labelled `key` and titled as
    `create_args` (a full `bd create ...` argv) would title it, creating it
    only when none exists.

    The single create path in this file: a create whose id never reached
    the plan (kill, timeout, failed write) is found by its key on the next
    run instead of duplicated. A closed match is history, not identity, so
    it yields a new issue. Concurrent creators on this host serialise on an
    flock of <project>/.planning/.gsd-beads.lock, the project bd resolves its db from;
    a lockless racer elsewhere is caught by the re-query after create, where
    the oldest row wins and only the row this call made is closed -- never
    another caller's, which may already be bound to a plan.

    Never call append_state_blocker while holding the lock: it flocks the
    same lock file and would deadlock this process."""
    title = create_args[create_args.index("--title") + 1] if "--title" in create_args else create_args[2]
    # bd resolves its db by walking up from its cwd; the lock must cover the
    # same project, so derive it the same way rather than fall back to an
    # unrelated directory that would serialise nothing.
    try:
        lock_root = Path(_BD_CWD) if _BD_CWD else find_project_root(Path.cwd())
    except ValueError as exc:
        raise RuntimeError(f"no project to lock for bd create: {exc}") from exc
    with _project_lock(lock_root / ".planning"):
        rows = _open_key_rows(key, kind, title)
        if rows:
            return rows[0]["id"]
        try:
            result = run_bd(create_args + ["-l", key])
        except subprocess.TimeoutExpired as exc:
            # bd may have written the row before the kill: look before failing.
            rows = _open_key_rows(key, kind, title)
            if rows:
                return rows[0]["id"]
            raise BdTransientError(f"bd create ({kind}) timed out and no {key} issue exists") from exc
        if result.returncode != 0:
            raise RuntimeError(f"bd create ({kind}) failed: {(result.stderr or '').strip()}")
        issue_id = result.stdout.strip() if isinstance(result.stdout, str) else ""
        if not SAFE_BD_ID_RE.fullmatch(issue_id):
            # Every task hangs off the epic, so a garbled epic id stops the
            # sync (rc 1); a garbled task id fails open like any bd failure.
            error = EpicAuthorityError if kind == "epic" else RuntimeError
            raise error(f"bd create ({kind}) returned unsafe id: {issue_id!r}")
        rows = _open_key_rows(key, kind, title)
        if issue_id not in {r["id"] for r in rows}:
            # The lookup cannot see what bd just wrote (a title bd stores
            # differently, an older bd's row shape). Raising would leave the
            # issue unbound and every rerun would add one more; return it so
            # it is persisted -- stored-id verification keeps later runs
            # idempotent. No STATE note: this lock is the one it takes.
            print(f"ensure-issue: bd list -l {key} does not show just-created {issue_id}; "
                  "dedup by key is blind for this issue", file=sys.stderr)
            return issue_id
        winner = rows[0]["id"]
        if winner != issue_id:
            closed = run_bd(["bd", "close", issue_id, "--reason", f"duplicate of {winner} ({key})"])
            if closed.returncode != 0:
                print(f"ensure-issue: duplicate {issue_id} of {winner} not closed: "
                      f"{closed.stderr.strip()}", file=sys.stderr)
        return winner


def _bd_show_identifies(result, expected_id):
    """Return False on absence; require exact one-row JSON on success."""
    return _bd_show_row(result, expected_id) is not None


def resolve_epic(frontmatter, roadmap_path, phase_num, phase_dir, project_root, objective=""):
    """Return (epic_id, needs_write, stale_epic_id) from exact bd authority."""
    stale_epic_id = None
    epic_id = parse_beads_epic(frontmatter)
    if epic_id is not None:
        check = run_bd(["bd", "show", epic_id, "--json"])
        try:
            identified = _bd_show_identifies(check, epic_id)
        except BdTransientError:
            raise
        except RuntimeError as exc:
            raise EpicAuthorityError(str(exc)) from exc
        if identified:
            return epic_id, False, None
        stale_epic_id = epic_id

    if read_epic_per(project_root) == "milestone":
        epic_id = resolve_milestone_epic(project_root)
        if not SAFE_BD_ID_RE.fullmatch(epic_id):
            raise EpicAuthorityError(f"unsafe milestone epic id: {epic_id!r}")
        return epic_id, True, stale_epic_id

    shared_epic_id = resolve_phase_epic(phase_dir)
    if shared_epic_id is not None:
        if not SAFE_BD_ID_RE.fullmatch(shared_epic_id):
            raise EpicAuthorityError(f"unsafe shared epic id: {shared_epic_id!r}")
        check = run_bd(["bd", "show", shared_epic_id, "--json"])
        try:
            identified = _bd_show_identifies(check, shared_epic_id)
        except BdTransientError:
            raise
        except RuntimeError as exc:
            raise EpicAuthorityError(str(exc)) from exc
        if identified:
            return shared_epic_id, True, stale_epic_id

    title = get_phase_header(roadmap_path, phase_num)
    description = _epic_description(objective)
    argv = ["bd", "create", title]
    if description:
        argv += ["-d", description]
    argv += ["-l", SYNC_LABEL, "--type", "epic", "--silent"]
    epic_id = ensure_issue(f"gsd-key:{phase_num}-epic".lower(), argv, "epic")
    return epic_id, True, stale_epic_id


def _epic_description(objective):
    """Fold an epic's source content into one `-d` prose string, cloning
    `_task_description`'s one-place-writes-the-shape discipline: a single
    `## Objective` section for non-empty input, the empty string otherwise
    -- callers append `-d` only when this is non-empty, so an empty
    description is never written (D-06). Reused for both phase epics (fed
    the plan's <objective>) and milestone epics (fed the ROADMAP milestone
    bullet, see get_milestone_bullet) -- one renderer, two content sources,
    matching resolve_epic's own "one place, either source" call shape.
    """
    if not objective:
        return ""
    return f"## Objective\n{objective}\n"


def _bd_rows_by_id(ids):
    """{id: row} for every id bd knows, from ONE `bd list --id a,b,c`. bd omits
    an unknown id and exits 0, so absence from a successful result is the same
    confirmed not-found `bd show` gave (R3); a failed call or unparseable
    output proves nothing and raises BdTransientError."""
    ids = list(dict.fromkeys(ids))
    if not ids:
        return {}
    result = run_bd(["bd", "list", "--id", ",".join(ids), "--all", "-n", "0", "--json"])
    rows = _checked_bd_list_rows(result)
    if rows is None:
        raise BdTransientError(
            f"bd list --id failed without confirming absence: {(result.stderr or '').strip()}"
        )
    return {r["id"]: r for r in rows if isinstance(r, dict) and r.get("id") in ids}


def resolve_issue(task, epic_id, ordinal_prefix, task_index):
    """Return (issue_id, created, divergent) from exact stored authority.

    GH#7: a stored `<beads-id>` that fails BEADS_ID_SHAPE_RE (e.g. a
    plan-author placeholder like "TBD") cannot be a value `bd create` ever
    returned, so it is unbound -- fall through to create, same as an absent
    `<beads-id>`. A shape-valid stored id never reaches here: create_issues
    verifies those in one batched call (D-07: a stale one is reported as
    divergence, never replaced).
    """
    if task["beads_id"] and not SAFE_BD_ID_RE.fullmatch(task["beads_id"]):
        raise RuntimeError(f"unsafe stored beads-id: {task['beads_id']!r}")
    title = f"{ordinal_prefix}.{task_index} {task['name']}"
    if task.get("type", "").startswith("checkpoint:"):
        description = _checkpoint_task_description(task)
    else:
        description = _task_description(task)
    argv = ["bd", "create", title]
    if description:
        argv += ["-d", description]
    if task["acceptance_criteria"]:
        argv += ["--acceptance", task["acceptance_criteria"]]
    argv += ["-l", SYNC_LABEL, "--type", "task", "--parent", epic_id, "--silent"]
    issue_id = ensure_issue(f"gsd-key:{ordinal_prefix}-t{task_index}".lower(), argv, "task")
    return issue_id, True, False


def find_orphans(children, current_ids):
    """Return ids of epic children (bd list --all --json rows) that match no
    current task and are not already closed (D-06).

    --all is required by the caller: the default `bd list` omits closed
    issues, so a sweep that relied on that default would re-close an
    already-closed orphan on every run and break idempotency (B5) -- the
    not-already-closed check here is the other half of that guard.

    Only children carrying SYNC_LABEL are candidates (R21): a user-parented
    follow-up under the epic is not this tool's issue and is never closed.
    bd omits the `labels` key for an unlabeled row, which fails closed.
    """
    return [
        c["id"]
        for c in children
        if c.get("id") not in current_ids
        and c.get("status") != "closed"
        and SYNC_LABEL in (c.get("labels") or [])
    ]


def collect_epic_task_ids(phase_dir, epic_id):
    """Return the union of every <beads-id> across every plan in phase_dir
    whose beads_epic frontmatter matches epic_id exactly (gsd-beads-bgb).

    The orphan sweep's current_ids must span every plan sharing an epic,
    not just the plan being synced right now -- otherwise a sibling plan's
    already-synced issue looks orphaned and gets closed on this sync.
    """
    ids = set()
    for plan_path in discover_plan_files(phase_dir).values():
        try:
            _, frontmatter, tasks = parse_plan(plan_path)
        except (OSError, UnicodeDecodeError) as exc:
            # Its ids are unknown, so every one of its issues would look
            # orphaned: the caller must skip its sweep (gsd-beads-cjbc.32).
            raise PlanParseError(f"{plan_path.name}: unreadable plan ({exc})") from exc
        m = BEADS_EPIC_RE.search(frontmatter)
        if not m or m.group(1) != epic_id:
            continue
        for task in tasks:
            if task["beads_id"]:
                ids.add(task["beads_id"])
    return ids


def _milestone_scoped(phase_dir):
    """True when phase_dir's project runs beads.epic_per=milestone, i.e. its
    epic is shared with every other phase of the milestone (gsd-beads-cjbc.9)."""
    try:
        return read_epic_per(phase_project_root(phase_dir)) == "milestone"
    except ValueError:
        return False


def collect_scope_task_ids(phase_dir, epic_id):
    """Every <beads-id> that legitimately lives under epic_id. Per-phase
    epics: this phase's plans (collect_epic_task_ids). Milestone epic: the
    union over every `.planning/phases/*` dir, because the epic's children
    span phases and a sibling phase's issue is not an orphan. A plan that
    does not parse raises PlanParseError -- its ids are unknown, so the
    caller must not treat any child as orphaned."""
    if not _milestone_scoped(phase_dir):
        return collect_epic_task_ids(phase_dir, epic_id)
    phases_root = confined(phase_project_root(phase_dir), ".planning", "phases")
    ids = set()
    for other in sorted(p for p in phases_root.iterdir() if p.is_dir()):
        ids |= collect_epic_task_ids(other, epic_id)
    return ids


def rewrite_plan(
    text, epic_id, epic_created, task_updates, native_updates, placeholder_updates=()
):
    """Insert beads_epic plus per-task legacy and native identity updates.

    task_updates: [(name_end_pos, issue_id), ...] for tasks that had no
    <beads-id> before this run -- spliced as a zero-width insertion right
    after </name>.

    placeholder_updates: [((span_start, span_end), issue_id), ...] for tasks
    whose stored <beads-id> was a shape-invalid placeholder (GH#7) -- the
    existing element spans span_start:span_end and is replaced in place,
    never left dangling alongside a second, freshly-inserted element.

    Both splice kinds share one descending-position pass so earlier offsets
    in `text` stay valid as later (higher-offset) edits are applied first;
    the frontmatter insertion (always at the front of the file) happens
    last.
    """
    edits = [
        (name_end_pos, name_end_pos, f"\n  <beads-id>{issue_id}</beads-id>")
        for name_end_pos, issue_id in task_updates
    ] + [
        (type_end_pos, type_end_pos, f' tracker-id="beads:{issue_id}"')
        for type_end_pos, issue_id in native_updates
    ] + [
        (span[0], span[1], f"<beads-id>{issue_id}</beads-id>")
        for span, issue_id in placeholder_updates
    ]
    for start, end, replacement in sorted(edits, key=lambda item: item[0], reverse=True):
        text = text[:start] + replacement + text[end:]
    if epic_created:
        fm_match = FRONTMATTER_RE.match(text)
        declaration = (
            BEADS_EPIC_DECL_RE.search(fm_match.group(1)) if fm_match is not None else None
        )
        if declaration is not None:
            # A stale beads_epic is replaced in place: a second declaration
            # makes parse_beads_epic raise on every later run.
            start = fm_match.start(1) + declaration.start()
            end = fm_match.start(1) + declaration.end()
            line_end = "\r" if text[start:end].endswith("\r") else ""
            return text[:start] + f"beads_epic: {epic_id}{line_end}" + text[end:]
        if fm_match is None:
            # Review finding: a frontmatter-less plan is tolerated by
            # parse_plan/parse_beads_epic (empty frontmatter, stored_epic_id
            # None), so resolve_epic can reach here with epic_created=True
            # for such a plan -- `fm_match.start(1)` on None used to raise
            # an uncaught AttributeError after bd issues were already
            # created in create_issues, orphaning them with no <beads-id>
            # ever written back. Synthesize a minimal frontmatter block
            # instead of crashing.
            text = "---\n\n---\n" + text
            fm_match = FRONTMATTER_RE.match(text)
        insert_pos = fm_match.start(1)
        newline = "\r\n" if text.startswith("---\r\n") else "\n"
        text = text[:insert_pos] + f"beads_epic: {epic_id}{newline}" + text[insert_pos:]
    return text


# 16-03 Task 2 (D-01): the elements strip_task_bodies removes from a
# stripped auto/tracer task block -- the same per-task content-field
# regexes plan 16-01 added (D-06), reused here rather than duplicated.
_STRIP_ELEMENT_RES = (
    READ_FIRST_RE,
    PRECONDITION_RE,
    BEHAVIOR_RE,
    ACTION_RE,
    VERIFY_RE,
    ACCEPTANCE_CRITERIA_RE,
    DONE_RE,
)
# The fixed-shape pointer a stripped block gains, naming the beads id and
# the retrieval command. Wrapped in a literal <action> element -- not an
# HTML comment -- so gsd-core's structural validator (which requires a
# literal <action> in any non-checkpoint task, GH#14) still sees the task
# as structurally complete once its content lives in bd. Checked against
# the block BEFORE any stripping runs (never after): idempotency comes
# from strip_task_bodies skipping an already-stripped block entirely, the
# same as it already does for checkpoint/no-type blocks -- not from the
# strip-then-reinsert cycle happening to reach a fixed point.
TASK_POINTER_PREFIX = "beads: content synced to bd -- see `bd show "


def strip_task_bodies(text, stripped_ids):
    """D-01: turn each `auto`/`tracer` task block whose `<beads-id>` is in
    stripped_ids into a pointer -- its opening tag, `<name>`, `<beads-id>`
    and `<files>` survive byte-identical; every content element
    (`read_first` through `done`) is removed and replaced by one
    fixed-shape `<action>` pointer naming the beads id (GH#14: a literal
    `<action>` element must remain so gsd-core's structural validator does
    not treat the task as incomplete). Every other task type
    -- every `checkpoint:*` variant, and a block with no `type` attribute at
    all -- is left byte-identical (D-03): an unrecognized type also fails
    toward keeping content, never toward deleting it.

    Only a task whose id is in stripped_ids is touched, so a re-sync over
    an already-synced plan (whose ids are NOT in this run's stripped_ids)
    strips nothing (D-07 forward-only). Replacements are spliced in
    reverse match order over the original `text`'s offsets -- the same
    technique rewrite_plan already uses -- so no earlier offset is
    invalidated mid-pass (T-16-12).

    gh-17 F-03: task boundaries are found against a masked copy, same as
    parse_plan -- an `</task>` literal quoted in a task's own code span
    (e.g. a plan documenting this exact tag) must not be read as that
    task's real closing tag and truncate the block mid-strip.
    """
    masked_text = _mask_code_spans(text)
    matches = list(TASK_RE.finditer(masked_text))
    for m in reversed(matches):
        block = text[m.start() : m.end()]
        masked_block = masked_text[m.start() : m.end()]
        opening_tag_m = TASK_OPEN_TAG_RE.match(block)
        opening_tag = opening_tag_m.group(0) if opening_tag_m else ""
        attributes, attributes_valid = _scan_task_attributes(opening_tag)
        type_attributes = [attribute for attribute in attributes if attribute[0] == "type"]
        task_type = (
            type_attributes[0][1]
            if attributes_valid and len(type_attributes) == 1
            else None
        )
        if task_type not in ("auto", "tracer"):
            continue
        id_m = BEADS_ID_RE.search(block)
        issue_id = id_m.group(1).strip() if id_m else None
        if not issue_id or issue_id not in stripped_ids:
            continue
        # GH#14 review: the marker must be checked on the UNMODIFIED block,
        # before any stripping runs. Checking it post-strip is tautological
        # (ACTION_RE, itself in _STRIP_ELEMENT_RES, already deleted any prior
        # pointer by the time the check runs, so it can never see one) and
        # made every pass re-strip-then-reinsert unconditionally -- for a
        # block with no blank line before `</task>` that reinsertion is not
        # byte-identical across passes (the collapse regex only fires on 2+
        # blank lines, so a single stray line the removal left behind
        # accumulates instead of collapsing). Skipping already-stripped
        # blocks entirely, the same way checkpoint/no-type blocks already
        # are, removes the drift instead of relying on the strip+reinsert
        # cycle reaching a fixed point.
        # CodeRabbit: match the complete pointer for THIS issue_id, not a
        # bare TASK_POINTER_PREFIX substring -- the prefix alone could
        # appear in ordinary action prose, or (a copy-pasted block) name a
        # different issue's pointer, in either case wrongly skipping a
        # block that still needs stripping.
        expected_pointer = f"<action>{TASK_POINTER_PREFIX}{issue_id}`.</action>"
        legacy_pointer = f"<!-- {TASK_POINTER_PREFIX}{issue_id}` -->"
        if expected_pointer in block or legacy_pointer in block:
            continue
        new_block = block
        # CodeRabbit: preserve the block's own line ending -- the prior
        # collapse regex and hardcoded "\n" pointer terminator left CRLF
        # blank lines uncollapsed and mixed a bare "\n" into an otherwise
        # CRLF-terminated block.
        line_ending = "\r\n" if "\r\n" in block else "\n"
        # R8: find each element's spans on the masked block (as parse_plan
        # does) so a tag quoted in a code span is never an element boundary,
        # then cut the same spans from the real block. Both copies are cut
        # in lockstep, one regex at a time, so offsets stay aligned and
        # nested spans keep the old sequential-removal semantics.
        for element_re in _STRIP_ELEMENT_RES:
            for em in reversed(list(element_re.finditer(masked_block))):
                new_block = new_block[: em.start()] + new_block[em.end() :]
                masked_block = masked_block[: em.start()] + masked_block[em.end() :]
        # Collapse the blank lines those removals leave.
        new_block = re.sub(r"[ \t]*\r?\n(?:[ \t]*\r?\n)+", line_ending, new_block)
        pointer = f"  <action>{TASK_POINTER_PREFIX}{issue_id}`.</action>{line_ending}"
        close_idx = new_block.rindex("</task>")
        new_block = new_block[:close_idx] + pointer + new_block[close_idx:]
        text = text[: m.start()] + new_block + text[m.end() :]
    return text


def _resolve_completed_task_ids(phase_dir):
    """Return the union of every <beads-id> across every plan in phase_dir
    whose SUMMARY.md exists (B9/D-04): the completed-task-id side of the
    divergence comparison. An empty phase_dir (no plans) returns an empty
    set.

    CodeRabbit/gh-17: a malformed completed plan's PlanParseError is caught
    here, per plan, so one bad plan degrades (excluded, noted in STATE.md)
    instead of crashing regenerate_beads_md/render_wave_status_block, which
    both call this uncaught. A completed plan's own authority violation
    (_task_authority_error, a ValueError distinct from PlanParseError) still
    raises -- that invariant is unrelated to gh-17 and is left unchanged."""
    completed_ids = set()
    for plan_id, plan_path in discover_plan_files(phase_dir).items():
        with _degrade_on_parse_error(phase_dir, plan_path):
            ids, _skipped = find_completed_task_ids(phase_dir, plan_id)
            completed_ids.update(ids)
    return completed_ids


def _resolve_marked_issue_ids(phase_dir):
    """Return (set_of_ids, rejected_count): the union of every id named in a
    `resolves_issues:` frontmatter key across every completed plan's
    SUMMARY.md in phase_dir (260820-j6g, bd gsd-beads-72u) -- the sibling
    candidate-set source to _resolve_completed_task_ids's <beads-id> union,
    for a standalone problem-report issue that carries no <beads-id>
    anywhere.

    The search is deliberately restricted to the frontmatter fence
    (FRONTMATTER_RE) and never the SUMMARY body: a bd id named only in body
    prose -- e.g. an 18-02-SUMMARY.md shape that mentions gsd-beads-72u as a
    follow-up it just filed -- must never be closeable, and that immunity to
    prose false positives is structural only if the body is never searched
    at all. Each raw id parse_resolves_issues extracts is admitted only when
    it fullmatches SAFE_BD_ID_RE; anything else is dropped and counted in
    rejected_count rather than ever reaching a `bd close` argv.

    GH#10: a plan whose status is not complete never has its
    `resolves_issues:` claim trusted either -- it is no completion
    record (see find_completed_task_ids), so a marker named there is
    excluded from this candidate set the same way its own tasks are.
    """
    ids = set()
    rejected = 0
    for plan_id, plan_path in discover_plan_files(phase_dir).items():
        summary_path = plan_path.with_name(f"{plan_id}-SUMMARY.md")
        if not summary_path.exists():
            continue
        if not _is_complete_status(_read_summary_status(summary_path)):
            continue
        try:
            text = summary_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm_match = FRONTMATTER_RE.match(text)
        if not fm_match:
            continue
        for raw_id in parse_resolves_issues(fm_match.group(1)):
            if SAFE_BD_ID_RE.fullmatch(raw_id):
                ids.add(raw_id)
            else:
                rejected += 1
    return ids, rejected


def _compute_diverged(rows, ordinal_map, completed_ids):
    """Return (diverged_count, task_status_by_id) (B10/D-04): a row whose id
    is a key in ordinal_map (i.e. a synced task) is diverged when its `bd`
    closed-ness disagrees with task-completion state in either direction. A
    row absent from ordinal_map (no linked task) is skipped entirely -- not
    counted, not present in task_status_by_id."""
    diverged_count = 0
    task_status_by_id = {}
    for row in rows:
        issue_id = str(row.get("id", ""))
        if issue_id not in ordinal_map:
            continue
        task_done = issue_id in completed_ids
        task_status_by_id[issue_id] = "done" if task_done else "incomplete"
        if (row.get("status") == "closed") != task_done:
            diverged_count += 1
    return diverged_count, task_status_by_id


def _task_authority_error(task):
    """Return why a parsed completed task cannot safely authorize a bd close."""
    if not task["attributes_valid"] or task["type_attribute_count"] > 1:
        return "task opening attributes are malformed or duplicated"
    if len(task["beads_ids"]) > 1:
        return "duplicate beads-id elements"
    if task["beads_id"] and not SAFE_BD_ID_RE.fullmatch(task["beads_id"]):
        return f"unsafe beads-id {task['beads_id']!r}"
    return None


def _normalize_summary_status(value):
    """Strip a YAML scalar's surrounding quotes and a trailing unquoted `#
    comment`, mirroring what gsd-core's real YAML parser (extractFrontmatter)
    does before `isHaltedStatus`/`isBlockedStatus` ever see the value (GH#10
    review: an unquoted-only reader misreads `status: "halted"` as not
    halted). Returns None for a non-string input."""
    if not isinstance(value, str):
        return None
    value = re.sub(r"\s+#.*$", "", value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return value


def _is_complete_status(value):
    """Allowlist, not denylist (gsd-beads-cjbc.48): only `complete` (case-
    insensitive after normalization) is a completion record. gsd-core
    documents `complete` and `halted`; `blocked` is a failure record; any
    other value is unknown and must not close every task. A SUMMARY with no
    top-level `status` (None) predates the field and counts as complete."""
    if value is None:
        return True
    return _normalize_summary_status(value).lower() == "complete"


def _is_blocked_status(value):
    """Mirror gsd-core's plan-dependency-graph.cjs `isBlockedStatus` (#3345):
    `status: blocked` is a failure record, not a completion record --
    deliberately distinct from `status: halted`, which still counts as
    summarized (GH#10)."""
    normalized = _normalize_summary_status(value)
    return normalized is not None and normalized.lower() == "blocked"


def _read_summary_status(summary_path):
    """Return a SUMMARY.md's frontmatter `status` raw value, or None if the
    file is missing/unreadable/malformed or carries no `status` key."""
    try:
        text = summary_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        return None
    status_match = STATUS_RE.search(fm_match.group(1))
    return status_match.group(1) if status_match else None


def find_completed_task_ids(phase_dir, plan_id):
    """Return (task_ids, skipped_count) for one plan in a wave.

    Completion is plan-granular: a plan whose SUMMARY.md exists has finished
    every one of its tasks (gsd-core's own completion marker -- see
    wave_granularity_fact) only when that SUMMARY's top-level `status` is
    `complete` or absent (_is_complete_status). `blocked` (#3345) is a failure record, not a
    completion record at all -- gsd-core's own has_summary:false treatment,
    so it contributes nothing here either, same as no SUMMARY.md existing.
    `halted` (a designed stop) or any other status left tasks unfinished; the
    SUMMARY template carries no per-task completion field, so such a plan
    cannot be disambiguated task-by-task -- every one of its tasks is
    skipped (fail closed) rather than guessed at. A plan with no SUMMARY.md
    yet contributes nothing. Within a complete plan, a task with no <beads-id> (never synced, e.g. a checkpoint task)
    is counted skipped rather than raised.
    """
    plan_path = discover_plan_files(phase_dir).get(plan_id)
    if plan_path is None:
        return [], 0
    summary_path = plan_path.with_name(f"{plan_id}-SUMMARY.md")
    if not summary_path.exists():
        return [], 0
    status = _read_summary_status(summary_path)
    if _is_blocked_status(status):
        return [], 0
    try:
        _, _, tasks = parse_plan(plan_path)
    except PlanParseError as exc:
        # CodeRabbit/gh-17: raised as PlanParseError, not plain ValueError,
        # so _resolve_completed_task_ids can catch it specifically and
        # degrade (regenerate_beads_md/render_wave_status_block call it
        # uncaught) -- PlanParseError already IS-A ValueError, so
        # close_wave/reconcile_stale_closed's existing ValueError boundary
        # and message-content tests are unaffected.
        raise PlanParseError(
            f"completed-task authority invalid in {plan_path.name}: {exc}"
        ) from exc
    if not _is_complete_status(status):
        return [], len(tasks)
    ids = []
    skipped = 0
    for task in tasks:
        authority_error = _task_authority_error(task)
        if authority_error:
            raise ValueError(
                f"completed-task authority invalid in {plan_path.name} "
                f"for task {task['name']!r}: {authority_error}"
            )
        if task["beads_id"]:
            ids.append(task["beads_id"])
        else:
            skipped += 1
    return ids, skipped


def filter_open_ids(ids):
    """Return the subset of `ids` bd still reports as not-closed.

    One `bd list --id ... --status ...` query for the whole batch (never one
    `bd show` per id) is the "explicit status filter" idempotency check: an
    id bd no longer returns here is already closed, so a repeat close-wave
    dispatch over an already-closed wave issues zero close calls (B5).
    Raises BdTransientError when the query is not confirmed.
    """
    if not ids:
        return []
    result = run_bd(
        [
            "bd",
            "list",
            "--id",
            ",".join(ids),
            "--status",
            BEADS_RECALL_STATUSES,
            "--json",
            "-n",
            "0",
        ]
    )
    rows = _checked_bd_list_rows(result)
    if rows is None:
        # Unconfirmed status is not "all open": closing on it could close
        # issues bd never reported. Callers print the notice and close nothing.
        raise BdTransientError(f"bd list status query failed: {result.stderr.strip()}")
    # Review finding: every sibling row-reader in this file uses
    # .get("id", "") for a malformed/missing key, never bare indexing.
    open_ids = {r.get("id", "") for r in rows}
    return [i for i in ids if i in open_ids]


def close_wave(phase_dir_arg, plan_ids):
    phase_dir = Path(phase_dir_arg).resolve()

    all_ids = []
    skipped_total = 0
    plan_counts = []
    try:
        for plan_id in plan_ids:
            ids, skipped = find_completed_task_ids(phase_dir, plan_id)
            all_ids.extend(ids)
            skipped_total += skipped
            plan_counts.append((plan_id, len(ids)))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"close-wave: {exc}", file=sys.stderr)
        return 1

    if not bd_available():
        _skip_bd_unavailable(phase_dir, "beads-status close-wave")
        return 0

    # De-duplicate while preserving order, in case the same task id is
    # somehow named twice across the wave's plans.
    unique_ids = list(dict.fromkeys(all_ids))
    try:
        to_close = filter_open_ids(unique_ids)
    except BdTransientError:
        _skip_bd_unavailable(phase_dir, "beads-status close-wave")
        return 0

    if to_close:
        reason = f"wave complete: {', '.join(plan_ids)}"
        result = run_bd(["bd", "close", *to_close, "--reason", reason])
        if result.returncode != 0:
            print("close-wave: bd close failed (details on stderr)")
            print(f"close-wave: bd close failed: {result.stderr.strip()}", file=sys.stderr)

    per_plan = ", ".join(f"{_sanitize_notice_value(pid)}:{n}" for pid, n in plan_counts)
    print(
        f"Closed {len(to_close)} issue(s) across {len(plan_ids)} plan(s) ({per_plan}); "
        f"skipped {skipped_total} task(s) (no beads-id or plan not complete)"
    )
    return 0


def reconcile_stale_closed(phase_dir_arg):
    """Phase-wide, idempotent backstop for D-08: close every task-complete
    (SUMMARY.md exists) issue that is still open in bd, across every plan in
    phase_dir -- not just the plan ids one wave's close-wave dispatch was
    given. A repeat call over an already-reconciled phase issues zero `bd
    close` calls, because filter_open_ids re-queries bd's live status before
    closing (B5)."""
    phase_dir = Path(phase_dir_arg).resolve()
    plan_ids = discover_plan_files(phase_dir)
    completed_ids = set()
    skipped_total = 0
    try:
        for plan_id in plan_ids:
            ids, skipped = find_completed_task_ids(phase_dir, plan_id)
            completed_ids.update(ids)
            skipped_total += skipped
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"reconcile-stale-closed: {exc}", file=sys.stderr)
        return 1

    if not bd_available():
        _skip_bd_unavailable(phase_dir, "beads-status reconcile-stale-closed")
        return 0

    completed_ids = sorted(completed_ids)
    try:
        to_close = filter_open_ids(completed_ids)
    except BdTransientError:
        _skip_bd_unavailable(phase_dir, "beads-status reconcile-stale-closed")
        return 0

    if to_close:
        reason = f"phase-wide reconciliation: {phase_dir.name}"
        result = run_bd(["bd", "close", *to_close, "--reason", reason])
        if result.returncode != 0:
            print("reconcile-stale-closed: bd close failed (details on stderr)")
            print(f"reconcile-stale-closed: bd close failed: {result.stderr.strip()}", file=sys.stderr)

    # 260820-j6g (bd gsd-beads-72u): a second, separately-reasoned close call
    # for standalone issues named only via `resolves_issues:` markers -- a
    # sibling candidate set, never merged into the call above, so a
    # `--reason` (which is per-call) keeps the two closure paths
    # distinguishable in bd's audit trail. `.beads/` is untracked, so that
    # trail is the only forensic handle on a wrong close.
    marked_ids, rejected = _resolve_marked_issue_ids(phase_dir)
    marked_ids -= set(completed_ids)
    try:
        marked_to_close = filter_open_ids(sorted(marked_ids))
    except BdTransientError:
        _skip_bd_unavailable(phase_dir, "beads-status reconcile-stale-closed")
        return 0

    if marked_to_close:
        marker_reason = f"resolves_issues marker: {phase_dir.name}"
        marker_result = run_bd(["bd", "close", *marked_to_close, "--reason", marker_reason])
        if marker_result.returncode != 0:
            print("reconcile-stale-closed: bd close failed (details on stderr)")
            print(f"reconcile-stale-closed: bd close failed: {marker_result.stderr.strip()}", file=sys.stderr)

    print(
        f"Closed {len(to_close)} issue(s) across {len(plan_ids)} plan(s) in "
        f"{_sanitize_notice_value(phase_dir.name)}; "
        f"skipped {skipped_total} task(s) (no beads-id or plan not complete); "
        f"closed {len(marked_to_close)} marker issue(s), rejected {rejected}"
    )
    return 0


def _plan_authority_error(plan_path):
    """Return a local parse or identity-authority error for one plan."""
    try:
        _, frontmatter, tasks = parse_plan(plan_path)
        parse_beads_epic(frontmatter)
    except (OSError, UnicodeDecodeError, PlanParseError, EpicAuthorityError) as exc:
        return str(exc)
    for task in tasks:
        authority_error = _task_authority_error(task)
        if authority_error:
            return f"task {task['name']!r}: {authority_error}"
    return None


def _milestone_authority_error(project_root):
    """Return the first invalid plan authority scanned by milestone epic lookup."""
    phases_root = confined(project_root, ".planning", "phases")
    if not phases_root.is_dir():
        return None
    for phase_dir in sorted(path for path in phases_root.iterdir() if path.is_dir()):
        for plan_path in discover_plan_files(phase_dir).values():
            authority_error = _plan_authority_error(plan_path)
            if authority_error:
                return f"{phase_dir.name}/{plan_path.name}: {authority_error}"
    return None


def _fail_task_preflight(task, reason):
    """Print + return 1 for a native tracker identity preflight failure on
    one task (ponytail: 8 near-identical print/return-1 blocks in
    create_issues's per-task validation loop collapsed to one call). No
    STATE.md note here -- unlike the plan-level preflight failures
    _fail_preflight covers, a malformed task attribute is not itself the
    class of onError:skip-defeating regression gh-17 addresses, so this
    keeps the exact pre-existing stderr-only behavior."""
    print(
        f"native tracker identity preflight failed for task {task['name']!r}: {reason}",
        file=sys.stderr,
    )
    return 1


def _fail_preflight(project_root, message):
    """Print `message` to stderr, note it in `.planning/STATE.md` (gh-17: a
    preflight failure here otherwise degrades this onError:skip dispatch
    point invisibly), and return the exit code both create_issues preflight
    failure branches share."""
    print(message, file=sys.stderr)
    append_state_blocker(confined(project_root, ".planning", "STATE.md"), message)
    return 1


def _atomic_write_text(path, content):
    """Write `content` to `path` via a same-directory temp file + os.replace,
    keeping the original mode (a plain temp file would take the umask's).
    A kill or ENOSPC leaves the previous file whole, never truncated."""
    # Unpredictable name, created O_EXCL|O_NOFOLLOW and written through that
    # same fd (never reopened by path, so a planted symlink cannot redirect
    # the write), fsynced before os.replace so a crash cannot leave a renamed
    # but empty file. os.replace then swaps a planted symlink at `path`
    # itself instead of writing through it.
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o666)
        try:
            handle = os.fdopen(fd, "w", encoding="utf-8", newline="")
        except BaseException:
            os.close(fd)
            raise
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists() and not path.is_symlink():
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def create_issues(plan_arg, allow_strip=True):
    """`allow_strip=False` keeps every `<task>` body in PLAN.md (gh-2).
    `strip_task_bodies` is a deliberate,
    destructive migration: it moves the ONLY copy of a task's content into a bd
    database the project may be gitignoring.

    17-02 Task 3 (D-06) asymmetry -- which caller computes this flag from
    what, and why:
    - `lifecycle_dispatch`'s plan:post branch passes the literal `False`,
      never consulting config. Its trigger is a substring of a shell
      command, so a spurious fire is always possible, and an unattended
      harness hook is the wrong principal to authorize an irreversible
      deletion regardless of what a config file says (D-03). This is the
      answer to the v1.3.0 incident and it does not change here.
    - `main()`'s `create-issues` CLI dispatch computes this flag from
      `read_sync_mode(project_root)`: `mirror` withholds the strip,
      every other value (including the shipped `authoritative` default, no
      config file at all, and the retired `off` value) behaves as before
      this task. An explicit CLI invocation is a different, stronger
      principal than a string-matched hook, so it is the one path config is
      allowed to govern.

    Native task resolution now governs authoritative content reads, so the
    explicit CLI may strip without a local execute-plan patch gate.
    """
    plan_path = Path(plan_arg).resolve()
    try:
        project_root = phase_project_root(plan_path.parent)
    except ValueError as exc:
        print(f"create-issues: {exc}", file=sys.stderr)
        return 1
    roadmap_path = confined(project_root, ".planning", "ROADMAP.md")

    try:
        text, frontmatter, tasks = parse_plan(plan_path)
    except (OSError, UnicodeDecodeError, PlanParseError) as exc:
        return _fail_preflight(
            project_root, f"native tracker identity preflight failed: {exc}"
        )
    objective_m = OBJECTIVE_RE.search(text)
    objective = objective_m.group(1).strip() if objective_m else ""

    try:
        stored_epic_id = parse_beads_epic(frontmatter)
    except EpicAuthorityError as exc:
        print(
            f"epic identity preflight failed: {exc}",
            file=sys.stderr,
        )
        return 1

    for task in tasks:
        if not task["attributes_valid"] or task["type_attribute_count"] > 1:
            return _fail_task_preflight(task, "task opening attributes are malformed or duplicated")
        if len(task["beads_ids"]) > 1:
            return _fail_task_preflight(task, "duplicate beads-id elements")
        if task["beads_id"] and not SAFE_BD_ID_RE.fullmatch(task["beads_id"]):
            return _fail_task_preflight(task, f"unsafe beads-id {task['beads_id']!r}")
        if task["type"] not in ("auto", "tracer"):
            continue
        if not task["native_identity_readable"]:
            return _fail_task_preflight(task, "task opening is not readable by the native parser")
        tracker_ids = task["tracker_ids"]
        if len(task["tracker_id_candidates"]) != len(tracker_ids) or any(
            tracker_id != tracker_id.strip() for tracker_id in tracker_ids
        ):
            return _fail_task_preflight(task, "tracker-id attribute is not exact")
        if len(tracker_ids) > 1:
            return _fail_task_preflight(task, "duplicate tracker-id attributes")
        if not tracker_ids:
            continue
        if not task["beads_id"]:
            return _fail_task_preflight(task, "tracker-id has no authoritative beads-id")
        expected = f"beads:{task['beads_id']}"
        if tracker_ids[0] != expected:
            return _fail_task_preflight(task, f"expected {expected!r}, found {tracker_ids[0]!r}")

    for sibling_path in discover_plan_files(plan_path.parent).values():
        if sibling_path.resolve() == plan_path:
            continue
        authority_error = _plan_authority_error(sibling_path)
        if authority_error:
            return _fail_preflight(
                project_root,
                f"cross-plan task authority preflight failed in "
                f"{sibling_path.name}: {authority_error}",
            )

    if stored_epic_id is None and read_epic_per(project_root) == "milestone":
        authority_error = _milestone_authority_error(project_root)
        if authority_error:
            print(
                f"milestone epic authority preflight failed in {authority_error}",
                file=sys.stderr,
            )
            return 1

    if not bd_available():
        _skip_bd_unavailable(plan_path.parent, "beads-sync")
        return 0

    plan_filename_stem = plan_path.stem  # e.g. "01-01-PLAN" -> ordinal "01-01"
    ordinal_prefix = "-".join(plan_filename_stem.split("-")[:2])
    phase_num = ordinal_prefix.split("-")[0]

    # B6/D-08 covers not just bd-absent-at-probe-time but bd-failing mid-run
    # (locked, transient, permission) -- the up-front bd_available() probe
    # cannot see a failure that only happens once we start writing. Any
    # RuntimeError raised by resolve_epic/resolve_issue below is exactly
    # that case: degrade to the same fail-open notice, not a crash.
    try:
        verified_tasks = {}
        # GH#7: a shape-invalid stored id (e.g. "TBD") never resolves in bd,
        # so it goes through the second loop below with the real epic_id in
        # hand to create -- excluded from this pre-pass. All stored ids are
        # verified with one batched bd call, not one `bd show` per task.
        stored = {
            i: task["beads_id"]
            for i, task in enumerate(tasks, start=1)
            if task["beads_id"] and BEADS_ID_SHAPE_RE.fullmatch(task["beads_id"])
        }
        for issue_id in stored.values():
            if not SAFE_BD_ID_RE.fullmatch(issue_id):
                raise RuntimeError(f"unsafe stored beads-id: {issue_id!r}")
        known_rows = _bd_rows_by_id(stored.values())
        for i, issue_id in stored.items():
            verified_tasks[i] = (issue_id, False, issue_id not in known_rows)

        epic_id, epic_created, stale_epic_id = resolve_epic(
            frontmatter, roadmap_path, phase_num, plan_path.parent, project_root, objective
        )
        if stale_epic_id is not None:
            print(
                f"divergence: stored beads_epic {stale_epic_id!r} not found in bd -- "
                "resolving to a replacement epic"
            )

        task_updates = []
        placeholder_updates = []
        native_updates = []

        def _unrecorded_message(ids, plan_path, exc):
            return (
                f"create-issues: cannot write {plan_path.name}; created issue ids "
                f"[{', '.join(ids)}] are unrecorded -- bind them by hand: {exc}"
            )

        def created_ids():
            return (
                ([epic_id] if epic_created else [])
                + [i for _, i in task_updates]
                + [i for _, i in placeholder_updates]
            )

        def persist_identity():
            # Write the identity created so far (epic + task ids) before the
            # next bd call: a failure or a hook-timeout kill mid-run would
            # otherwise orphan these issues and a rerun would duplicate them.
            try:
                _atomic_write_text(
                    plan_path,
                    rewrite_plan(
                        text, epic_id, epic_created, task_updates, [], placeholder_updates
                    ),
                )
            except OSError as exc:
                # The ids exist in bd but not in the plan: name them (stderr
                # and, via the RuntimeError handler, STATE.md) so they can be
                # bound by hand instead of being lost.
                raise IdentityPersistError(_unrecorded_message(created_ids(), plan_path, exc)) from exc

        if epic_created:
            persist_identity()
        created_count = 0
        task_ids = []
        divergences = []
        for i, task in enumerate(tasks, start=1):
            if i in verified_tasks:
                issue_id, created, divergent = verified_tasks[i]
            else:
                issue_id, created, divergent = resolve_issue(
                    task, epic_id, ordinal_prefix, i
                )
                # ensure_issue adopts by key+title; a duplicate task name at a
                # shifted ordinal can match an issue another task here owns.
                if issue_id in task_ids or issue_id in stored.values():
                    raise RuntimeError(
                        f"task {task['name']!r} resolved to {issue_id}, already bound "
                        f"in {plan_path.name} -- rename the duplicate task"
                    )
            if created:
                created_count += 1
                if task["beads_id"]:
                    # GH#7: an existing (shape-invalid) <beads-id> element
                    # must be replaced in place -- task_updates' insert-
                    # after-<name> splice assumes no element exists yet and
                    # would leave the stale placeholder behind as a second,
                    # dangling <beads-id>.
                    placeholder_updates.append((task["beads_id_span"], issue_id))
                else:
                    task_updates.append((task["name_end"], issue_id))
                persist_identity()
            if (
                not divergent
                and task["type"] in ("auto", "tracer")
                and not task["tracker_ids"]
            ):
                native_updates.append((task["tracker_insert"], issue_id))
            if divergent:
                divergences.append((task["name"], issue_id))
            task_ids.append(issue_id)
    except EpicAuthorityError as exc:
        print(f"epic identity authority failed: {exc}", file=sys.stderr)
        return 1
    except IdentityPersistError as exc:
        return _fail_preflight(project_root, str(exc))
    except (RuntimeError, OSError) as exc:
        print(NOTICE)
        append_state_blocker(
            confined(project_root, ".planning", "STATE.md"),
            f"bd failing mid-sync -- beads-sync skipped (B6/D-08): {exc}",
        )
        return 0

    for name, missing_id in divergences:
        print(f"divergence: task {_sanitize_notice_value(name, 200)!r} beads-id {missing_id} not found in bd")

    # GH#7: an all-diverged run creates and binds nothing -- the per-task
    # lines above read as noise, not as "zero issues were synced"; say so
    # plainly so it can't be skimmed past.
    if tasks and created_count == 0 and len(divergences) == len(tasks):
        print(
            f"beads-sync: 0 of {len(tasks)} task(s) bound -- every stored "
            "beads-id diverged from bd; no issues were created or updated"
        )

    if task_updates or placeholder_updates or native_updates or epic_created:
        # D-01/D-05: strip content only for tasks whose issue was created in
        # THIS run (task_updates/placeholder_updates). Native task resolution
        # now provides the authoritative read path; the unattended hook
        # remains non-destructive.
        newly_created_ids = {issue_id for _, issue_id in task_updates} | {
            issue_id for _, issue_id in placeholder_updates
        }
        intact = None
        if newly_created_ids and not allow_strip:
            print(
                "beads-sync: hook-driven dispatch -- leaving task content in PLAN.md "
                "(gh-2: an unattended dispatch never performs the authoritative strip)"
            )
        elif newly_created_ids:
            # gh#24: stripping deletes the only PLAN.md copy, so strip only
            # tasks whose stored bd description matches what was sent.
            by_id = dict(zip(task_ids, tasks))
            # Only auto/tracer bodies are ever stripped (D-03); checkpoint
            # tasks render through another builder and need no check.
            checked = {i: by_id[i] for i in newly_created_ids if by_id[i]["type"] in ("auto", "tracer")}
            intact = _intact_ids(checked) if checked else set()
            rejected = set(checked) - intact
            for issue_id in sorted(rejected):
                print(
                    f"beads-sync: {issue_id} stored description differs from the plan -- "
                    "leaving its task content in PLAN.md"
                )
            # The native resolver reads bd with no PLAN.md fallback, so a
            # rejected task must not gain a tracker-id that points at it.
            native_updates[:] = [(pos, i) for pos, i in native_updates if i not in rejected]
        new_text = rewrite_plan(
            text, epic_id, epic_created, task_updates, native_updates, placeholder_updates
        )
        if intact is not None:
            new_text = strip_task_bodies(new_text, intact)
        try:
            _atomic_write_text(plan_path, new_text)
        except OSError as exc:
            return _fail_preflight(
                project_root, _unrecorded_message(created_ids(), plan_path, exc)
            )

    orphan_result = run_bd(_beads_md_argv(epic_id))
    if orphan_result.returncode == 0:
        try:
            children = _unwrap_bd_list(json.loads(orphan_result.stdout))
        except json.JSONDecodeError:
            children = []
        try:
            current_ids = {tid for tid in task_ids if tid} | collect_scope_task_ids(
                plan_path.parent, epic_id
            )
        except PlanParseError as exc:
            # A plan whose ids are unknown makes its issues look orphaned.
            print(f"create-issues: orphan sweep skipped, a plan failed to parse: {exc}", file=sys.stderr)
            children = []
            current_ids = set()
        for orphan_id in find_orphans(children, current_ids):
            close_result = run_bd(
                ["bd", "close", orphan_id, "--reason", "no longer maps to a plan task"]
            )
            # Review finding: every other `bd close` call site in this file
            # prints on a non-zero return code; this one silently swallowed
            # a failed orphan close.
            if close_result.returncode != 0:
                print(f"create-issues: orphan close failed for {_sanitize_notice_value(orphan_id)} (details on stderr)")
                print(f"create-issues: orphan close failed: {close_result.stderr.strip()}", file=sys.stderr)

    prereq_last_ids = []
    for prereq_id in parse_depends_on(frontmatter):
        last_id = resolve_prereq_last_task_id(plan_path.parent, prereq_id)
        if last_id is None:
            print(
                f"prerequisite plan {_sanitize_notice_value(prereq_id)} not yet synced -- "
                "skipping cross-plan edge"
            )
        else:
            prereq_last_ids.append(last_id)
    # Rows already carry dependencies[]: skip edges bd has, so an unchanged
    # plan makes no `bd dep add` call. A new endpoint has no row, so its edges
    # (and a deferred cross-plan edge whose prereq synced later) still apply.
    present = {
        (blocked, dep.get("depends_on_id"))
        for blocked, row in known_rows.items()
        for dep in row.get("dependencies") or []
        if isinstance(dep, dict) and dep.get("type") == "blocks"
    }
    apply_dependency_edges(
        [e for e in derive_dependency_edges(task_ids, prereq_last_ids) if e not in present]
    )

    print(f"Synced {created_count} issue(s) -> epic {epic_id}")
    return 0


_CELL_STRIP = str.maketrans("", "", "<>`")


def _escape_table_cell(text):
    """Escape `|` and strip `\r`/`\n` from text before it enters a markdown
    table cell (T-02-03, matches gsd-core's own ship.md pattern) -- issue
    title/status text originates from a different principal (whoever filed
    it in bd) than the process rendering this generated artifact."""
    # `<`, `>` and backticks are dropped: titles are re-printed inside the
    # <beads_status> executor-prompt block, which a `</beads_status>` in a
    # title would otherwise close.
    # `\` first: a literal `\|` must not read back as an escaped pipe.
    return (
        text.translate(_CELL_STRIP).replace("\\", "\\\\").replace("|", "\\|")
        .replace("\r", "").replace("\n", " ")
    )


def _beads_recall_argv():
    """The D-04 baseline open-issue scan: every open, non-epic issue, no
    truncation (Pitfall 3 -- `-n 0` overrides the default 50-row limit)."""
    return ["bd", "list", "--status", BEADS_RECALL_STATUSES, "--exclude-type", "epic", "--json", "-n", "0"]


def _render_issue_table(rows, include_matched_via):
    """rows is [(issue, matched_via_or_None), ...]; matched_via is rendered
    as a fourth column only when include_matched_via is True."""
    if include_matched_via:
        lines = ["| Issue | Title | Status | Matched via |", "|-------|-------|--------|--------------|"]
    else:
        lines = ["| Issue | Title | Status |", "|-------|-------|--------|"]
    for issue, via in rows:
        issue_id = _escape_table_cell(str(issue.get("id", "")))
        title = _escape_table_cell(str(issue.get("title", "")))
        status = _escape_table_cell(str(issue.get("status", "")))
        if include_matched_via:
            lines.append(f"| {issue_id} | {title} | {status} | matched via: {via} |")
        else:
            lines.append(f"| {issue_id} | {title} | {status} |")
    return "\n".join(lines)


def _render_beads_recall_body(matched, unscoped):
    """matched is [(issue, matched_via), ...]; unscoped is [issue, ...].

    D-04: a zero-issue run (both lists empty) renders the single literal
    "No open issues found." line, never a skipped file. D-02: an issue
    matching neither scope-matching technique is rendered under "## Unscoped",
    never omitted from the body entirely.
    """
    if not matched and not unscoped:
        return "No open issues found.\n"

    parts = ["## Open issues touching this phase's scope", ""]
    if matched:
        parts.append(_render_issue_table(matched, include_matched_via=True))
    else:
        parts.append("None matched this phase's scope.")
    parts.append("")
    parts.append("## Unscoped")
    parts.append("")
    if unscoped:
        parts.append(_render_issue_table([(issue, None) for issue in unscoped], include_matched_via=False))
    else:
        parts.append("None.")
    parts.append("")
    return "\n".join(parts)


# Candidate path-like tokens; `extract_phase_mentions` decides which count. The
# filter lives there, not in the regex, because backtracking can shorten a
# match ("example.com/docs" -> "example.com").
PATH_TOKEN_RE = re.compile(r"[\w\-./]+\.\w{1,4}")
PATH_TOKEN_MIN_LEN = 4
# GH#11: digits are `\w`, so a bare version number ("2.39") matches
# PATH_TOKEN_RE too but is never a path/extension -- excluded below.
NUMERIC_ONLY_TOKEN_RE = re.compile(r"[\d.]+")
HOSTNAME_SEGMENT_RE = re.compile(r"[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}")


def extract_phase_mentions(roadmap_path, phase_num, context_path, project_root=None):
    """Return deduplicated file mentions from the phase's ROADMAP.md section
    (from its header to the next `### Phase` heading) plus context_path's full
    text when it exists -- the only file-scope signal available at plan:pre
    time for the phase being planned, since no PLAN.md exists yet for it
    (D-01 revised).

    A token containing `/` counts (it may name a file the phase will create),
    unless it starts with `../` or `/` or looks like a URL host. A token
    without `/` counts only when it is an existing file in `project_root`
    (default: the grandparent of ROADMAP.md): "example.com" and "Node.js" are
    prose. A bare file that does not exist yet is not a mention; write it with
    a slash ("./CONTRIBUTING.md").
    """
    text = Path(roadmap_path).read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^###\s+Phase\s+0*{phase_regex_token(phase_num)}\s*:.*?(?=^###\s+Phase\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    section_text = m.group(0) if m else ""

    context_text = ""
    context_path = Path(context_path)
    if context_path.exists():
        context_text = context_path.read_text(encoding="utf-8")

    if project_root is None:  # ROADMAP.md lives in <root>/.planning/
        project_root = Path(roadmap_path).resolve().parent.parent
    seen = []
    for token in PATH_TOKEN_RE.findall(section_text) + PATH_TOKEN_RE.findall(context_text):
        if token.startswith(("../", "/")):  # also the remnant of "https://host/..."
            continue
        if "/" in token:
            if len(token) < PATH_TOKEN_MIN_LEN or NUMERIC_ONLY_TOKEN_RE.fullmatch(token):
                continue
            # "docs.site/guide.md" is a URL unless that directory exists.
            first = token.split("/", 1)[0]
            if HOSTNAME_SEGMENT_RE.fullmatch(first) and not os.path.isdir(project_root / first):
                continue
        elif not os.path.isfile(project_root / token):  # isfile: no ENAMETOOLONG raise
            continue
        if token not in seen:
            seen.append(token)
    return seen


def scope_match(issue_id, files_index, phase_mentions):
    """Pure technique-1 check: return "files" when one of issue_id's
    reverse-looked-up files matches a phase_mentions token; return None when
    issue_id has no reverse-lookup entry at all (caller falls back to
    technique 2) or its files simply don't overlap. A leading `./` is dropped
    on both sides. A bare token (no `/`) matches by exact path equality, so
    README.md never matches docs/README.md; a slash token matches by equality
    or as a whole-segment suffix of the file (`src/a.py` matches
    `pkg/src/a.py`, never `xsrc/a.py` or a longer mention)."""
    if issue_id not in files_index:
        return None
    for issue_file in files_index[issue_id]:
        issue_file = PurePosixPath(issue_file).as_posix()
        for mention in phase_mentions:
            mention = PurePosixPath(mention).as_posix()
            if issue_file == mention or (
                "/" in mention and issue_file.endswith("/" + mention)
            ):
                return "files"
    return None


def desc_contains_match(issue, folded_phase_mentions):
    """GH#11: technique-2 fallback for an issue absent from files_index.
    Was one `bd list --id <id> --desc-contains <token> --json -n 0`
    subprocess per phase_mentions token -- O(issues x tokens) bd calls
    (1813 measured on the reporter's repo, ~9 minutes, blowing the
    per-call BD_TIMEOUT in aggregate even though each call individually
    was fast). `issue`'s description is already in memory: beads_recall's
    single upfront `bd list` fetched every open issue's full record before
    this function is ever called, so re-querying it here just re-derives
    data the caller already holds. `folded_phase_mentions` is pre-
    casefolded by the caller (once per run, not once per issue) --
    case-insensitive literal substring, in-process, zero subprocesses,
    short-circuit on first hit. Stricter than bd's own `--desc-contains`,
    which is SQL LIKE-backed and treats `_`/`%` as wildcards; this is a
    documented, deliberate narrowing, not a semantic-parity claim."""
    description = (issue.get("description") or "").casefold()
    for token in folded_phase_mentions:
        # extract_phase_mentions keeps the `./` that marks a not-yet-created
        # root file; prose never writes it, so match the bare path.
        if token.removeprefix("./") in description:
            return "description"
    return None


def _write_beads_recall_failure(phase_dir, reason):
    """GH#11: overwrite BEADS-RECALL.md with an explicit `recall_status:
    failed` marker instead of leaving a previous run's file in place,
    indistinguishable from a fresh one -- called from every beads_recall
    exit path that doesn't reach a real scope-matched result, including
    the bd-unavailable path (D-08's existing fail-open shape covered the
    STATE.md blocker but not this file). Deliberately does not suppress
    a write failure (coderabbit review, PR #12): swallowing it here would
    leave whatever was on disk before -- possibly a stale `recall_status:
    ok` -- trusted as current, the exact bug this function exists to
    close. Same unguarded write the success path in beads_recall already
    uses."""
    padded_phase = phase_dir.name.split("-", 1)[0]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = (
        "---\n"
        f"phase: {phase_dir.name}\n"
        f'generated_from: "{" ".join(_beads_recall_argv())}"\n'
        f"generated_at: {generated_at}\n"
        "recall_status: failed\n"
        f"recall_error: {json.dumps(reason)}\n"
        "---\n\n"
    )
    reason_line = " ".join(reason.split())  # collapse embedded newlines (T-01: reason may carry bd stderr)
    out_text = (
        frontmatter
        + f"# Beads Recall: Phase {phase_dir.name}\n\n"
        + f"No recall data for this run ({reason_line}). Any previous recall was discarded; "
        "re-run beads-recall before trusting phase scope.\n"
    )
    _atomic_write_text(phase_dir / f"{padded_phase}-BEADS-RECALL.md", out_text)


def beads_recall(phase_dir_arg):
    """B7/plan:pre: scan every open, non-epic bd issue and write
    `{phase_dir}/{padded_phase}-BEADS-RECALL.md`, always, even when zero
    issues are open (D-04) -- same B6/D-08 fail-open shape as create_issues/
    close_wave, never a new fail-open variant."""
    if not bd_available():
        phase_dir = Path(phase_dir_arg).resolve()
        _skip_bd_unavailable(phase_dir, "beads-recall")
        _write_beads_recall_failure(phase_dir, "bd unavailable")
        print("BEADS-RECALL.md recall failed: bd unavailable")
        return 0

    phase_dir = Path(phase_dir_arg).resolve()
    project_root = phase_project_root(phase_dir)
    padded_phase = phase_dir.name.split("-", 1)[0]

    bd_error = None
    try:
        result = run_bd(_beads_recall_argv())
    except (subprocess.TimeoutExpired, OSError, UnicodeDecodeError) as exc:
        # bd_available()'s own exception pair, plus UnicodeDecodeError for
        # undecodable stdout under text=True -- a `bd list` running long,
        # the binary vanishing mid-run, or bad output encoding must all
        # reach the failure-marker path below, not escape uncaught past it.
        bd_error = f"bd list failed: {exc}"

    issues = []
    if bd_error is None:
        if result.returncode == 0:
            try:
                payload = json.loads(result.stdout)
            except ValueError as exc:  # json.JSONDecodeError is a ValueError subclass
                bd_error = f"bd list returned unparseable JSON: {exc}"
            else:
                # Same `{"data": [...]}` envelope _checked_bd_list_rows accepts;
                # any other non-list (e.g. an error object) must fail closed.
                rows = payload.get("data") if isinstance(payload, dict) else payload
                if isinstance(rows, list) and (
                    not rows or any(isinstance(row, dict) for row in rows)
                ):
                    issues = [row for row in rows if isinstance(row, dict)]
                else:
                    bd_error = f"bd list returned non-list JSON ({type(payload).__name__})"
        else:
            bd_error = f"bd list exited {result.returncode}: {result.stderr.strip()}"

    if bd_error is not None:
        _write_beads_recall_failure(phase_dir, bd_error)
        print("BEADS-RECALL.md recall failed: bd list failed (details on stderr)")
        print(f"BEADS-RECALL.md recall failed: {bd_error}", file=sys.stderr)
        return 0

    # Two-technique scope match (D-01 revised): reverse <beads-id> lookup
    # against every phase's PLAN.md <files> element first, falling back to
    # an in-process description-substring match (GH#11) for an issue with no
    # matching <beads-id> anywhere. Neither technique matching is not an
    # error -- the issue simply stays Unscoped (D-02), never dropped.
    roadmap_path = confined(project_root, ".planning", "ROADMAP.md")
    context_path = phase_dir / f"{padded_phase}-CONTEXT.md"
    try:
        phase_mentions = extract_phase_mentions(
            roadmap_path, padded_phase, context_path, project_root=project_root
        )
    except (OSError, ValueError):
        phase_mentions = []
    folded_phase_mentions = [token.casefold() for token in phase_mentions]
    try:
        files_index = collect_all_task_files(project_root)
    except (OSError, ValueError) as exc:  # PlanParseError is a ValueError
        reason = f"a plan could not be read for the file index: {exc}"
        _write_beads_recall_failure(phase_dir, reason)
        print("BEADS-RECALL.md recall failed: a plan could not be read (details on stderr)")
        print(f"BEADS-RECALL.md recall failed: {reason}", file=sys.stderr)
        return 0

    matched = []
    unscoped = []
    for issue in issues:
        issue_id = issue.get("id", "")
        via = scope_match(issue_id, files_index, phase_mentions)
        if via is None:
            via = desc_contains_match(issue, folded_phase_mentions)
        if via:
            matched.append((issue, via))
        else:
            unscoped.append(issue)

    body = _render_beads_recall_body(matched, unscoped)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = (
        "---\n"
        f"phase: {phase_dir.name}\n"
        f'generated_from: "{" ".join(_beads_recall_argv())}"\n'
        f"generated_at: {generated_at}\n"
        "recall_status: ok\n"
        "---\n\n"
    )
    out_text = frontmatter + f"# Beads Recall: Phase {phase_dir.name}\n\n" + body
    out_path = phase_dir / f"{padded_phase}-BEADS-RECALL.md"
    _atomic_write_text(out_path, out_text)

    print(
        f"BEADS-RECALL.md written: {len(matched)} matched, {len(unscoped)} unscoped "
        f"({len(issues)} open issue(s) total)"
    )
    return 0


def resolve_phase_epic(phase_dir):
    """Return the `beads_epic` frontmatter value carried by the first
    `NN-NN-PLAN.md` discovered in phase_dir that has one, or None when no
    plan in this phase has ever synced (D-05: every plan in a phase shares
    the same epic, so the first match is sufficient). Raises EpicAuthorityError
    for an unsafe id -- returning None would read as "never synced" and make
    a caller create a duplicate epic or delete the BEADS.md gate artifact
    without saying why."""
    for plan_path in discover_plan_files(phase_dir).values():
        try:
            with _degrade_on_parse_error(phase_dir, plan_path):
                _, frontmatter, _ = parse_plan(plan_path)
                epic_id = parse_beads_epic(frontmatter)
                if epic_id is not None:
                    return epic_id
        except (OSError, UnicodeDecodeError):
            continue
    return None


def _beads_md_argv(epic_id):
    """D-08/Pitfall 3: the epic-children query BEADS.md's table is built
    from, `-n 0` explicit to avoid the default 50-row truncation."""
    return ["bd", "list", "--parent", epic_id, "--all", "--json", "-n", "0"]


def _checked_bd_list_rows(result):
    """Rows of a `bd list` result, or None when the query failed (non-zero
    exit, invalid JSON, or a non-list payload such as a JSON error object).
    `_unwrap_bd_list` maps all of those to [], which a gate reader would take
    for "no open issues"; callers that must fail closed use this instead."""
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
    except (UnicodeError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        payload = payload.get("data")
    return payload if isinstance(payload, list) else None


def _resolve_task_ordinal_map(phase_dir, degraded=None):
    """Return {beads_id: ordinal_prefix} across every plan in phase_dir, so
    each BEADS.md row can name the plan task that owns its issue. A plan that
    could not be read or parsed is skipped; its name is appended to
    `degraded` (when given) so a caller can tell the map is incomplete."""
    mapping = {}
    for ordinal, plan_path in discover_plan_files(phase_dir).items():
        try:
            with _degrade_on_parse_error(phase_dir, plan_path):
                _, _, tasks = parse_plan(plan_path)
                for task in tasks:
                    if task["beads_id"]:
                        mapping[task["beads_id"]] = ordinal
                continue
        except (OSError, UnicodeDecodeError):
            pass
        if degraded is not None:
            degraded.append(plan_path.name)
    return mapping


def _note_plan_parse_error(phase_dir, plan_path, exc):
    """Best-effort STATE.md note for a PlanParseError hit outside create_issues
    (gh-17) -- swallows both a failed project_root resolution and a failed
    STATE.md write (gh-17 F-04): this runs inside an already-degrading read
    path (regenerate_beads_md/render_wave_status_block/resolve_phase_epic)
    that must never itself raise. A failure here still prints to stderr --
    review finding: this is already the fallback for a lost signal, and a
    second, totally silent failure on top of it would leave zero trace
    anywhere the plan actually failed to parse."""
    message = f"plan parse failed in {plan_path.name}: {exc}"
    try:
        project_root = phase_project_root(phase_dir)
        append_state_blocker(confined(project_root, ".planning", "STATE.md"), message)
    except (ValueError, OSError) as write_exc:
        print(f"{message} (STATE.md note failed: {write_exc})", file=sys.stderr)


@contextlib.contextmanager
def _degrade_on_parse_error(phase_dir, plan_path):
    """Suppress a PlanParseError for one plan, noting it via
    `_note_plan_parse_error` (gh-17) -- the shared body every per-plan
    PlanParseError degrade site below used to duplicate inline. Any other
    exception (OSError, UnicodeDecodeError) is left to the caller's own
    surrounding handling, unchanged."""
    try:
        yield
    except PlanParseError as exc:
        _note_plan_parse_error(phase_dir, plan_path, exc)


def _render_beads_md_table(rows, ordinal_map, task_status_by_id):
    """D-06/D-08: 6-column issue/title/status/task-status/plan-task/
    blocked-by table -- Task Status names the task-completion side of a
    diverged row so it's readable without cross-referencing PLAN.md/
    SUMMARY.md. The blocked-by column is `dependencies[]` filtered to
    `type == "blocks"`, excluding `type == "parent-child"` epic-parent
    edges -- zero extra bd calls, this data already arrives on the one
    `bd list --parent` response.
    """
    lines = [
        "| Issue | Title | Status | Task Status | Plan Task | Blocked By |",
        "|-------|-------|--------|-------------|-----------|------------|",
    ]
    for row in rows:
        raw_issue_id = str(row.get("id", ""))
        issue_id = _escape_table_cell(raw_issue_id)
        title = _escape_table_cell(str(row.get("title", "")))
        status = _escape_table_cell(str(row.get("status", "")))
        # task_status/plan_task are keyed on the raw (unescaped) id -- both
        # ordinal_map and task_status_by_id are built from bd's own ids
        # elsewhere, so lookups must use the same unescaped key.
        task_status = task_status_by_id.get(raw_issue_id, "")
        plan_task = ordinal_map.get(raw_issue_id, "")
        blocked_by = _escape_table_cell(
            ", ".join(
                str(dep.get("depends_on_id", ""))
                for dep in row.get("dependencies", []) or []
                if dep.get("type") == "blocks"
            )
        )
        lines.append(
            f"| {issue_id} | {title} | {status} | {task_status} | {plan_task} | {blocked_by} |"
        )
    return "\n".join(lines)


def _beads_md_extras(phase_dir, out_path):
    """Every file besides out_path that gsd-core's findPhaseArtifact (1.10-
    1.16) could answer the BEADS.md ship gate with: <phase>/BEADS.md, then
    <phase>/.planning/BEADS.md, then the first readdir entry ending in
    -BEADS.md or equal to BEADS.md. It takes the first match, so any extra
    file is a gate bypass."""
    candidates = [phase_dir / "BEADS.md", phase_dir / ".planning" / "BEADS.md"]
    try:
        names = sorted(os.listdir(phase_dir))
    except OSError:
        names = []
    candidates += [phase_dir / n for n in names if n.endswith("-BEADS.md")]
    return [c for c in dict.fromkeys(candidates) if c != out_path and c.is_file()]


def _is_generated_beads_md(path):
    """True when `path` carries this tool's `generated_from:` frontmatter key
    -- a mention anywhere else in the file proves nothing."""
    try:
        fm = FRONTMATTER_RE.match(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return False
    return bool(fm) and re.search(r"^generated_from:", fm.group(1), re.MULTILINE) is not None


def regenerate_beads_md(phase_dir_arg):
    """B11/execute:wave:pre (read-only) and execute:wave:post (unchanged):
    always fully overwrite `{phase_dir}/{padded_phase}-BEADS.md` from a
    fresh `bd list --parent <epic>` query -- never read the existing file's
    body to merge or preserve a prior hand edit."""
    phase_dir = Path(phase_dir_arg).resolve()
    padded_phase = phase_dir.name.split("-", 1)[0]
    out_path = phase_dir / f"{padded_phase}-BEADS.md"

    # Any other BEADS file the gate could read would outlive every fail-closed
    # write below. Ours (e.g. a renumbered phase's NN-BEADS.md) are removed;
    # a foreign one is moved out of the gate's view with its content kept,
    # and this run fails closed so someone looks at it.
    rejected = []
    for extra in _beads_md_extras(phase_dir, out_path):
        # A file that cannot be moved still answers the gate: report it and
        # fail closed rather than crash before ours is overwritten below.
        try:
            if _is_generated_beads_md(extra):
                extra.unlink()
                continue
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            # link+unlink, not rename: rename silently replaces an existing
            # aside (an earlier same-second rejection, or one planted to keep
            # this file in the gate's view); link refuses, so try the next name.
            for n in itertools.count(1):
                aside = extra.with_name(f"{extra.name}.rejected-{stamp}" + (f"-{n}" if n > 1 else ""))
                try:
                    os.link(extra, aside, follow_symlinks=False)
                    break
                except FileExistsError:
                    continue
            extra.unlink()
            rejected.append(f"{extra} -> {aside.name}")
        except OSError as exc:
            rejected.append(f"{extra} could not be moved ({exc})")
    # An aside from an earlier run is a rejection that nobody has reviewed:
    # the gate stays closed (and the notice repeats) until the user removes it.
    # The nested case's aside sits beside <phase>/.planning/BEADS.md.
    for d in (phase_dir, phase_dir / ".planning"):
        for aside in sorted(d.glob("*BEADS.md.rejected-*")):
            if aside.is_file() and not any(r.endswith(f"-> {aside.name}") for r in rejected):
                rejected.append(f"{aside} (kept aside, remove it once reviewed)")
    if rejected:
        message = (
            "BEADS.md: foreign ship-gate artifact(s) rejected, gate fails closed until "
            "reviewed: " + "; ".join(rejected)
        )
        # lifecycle-dispatch promotes stdout into the agent's context, and a
        # planted file name can carry newlines and <beads_status> tags: stdout
        # gets a fixed sentence and a count, the names only stderr and STATE.md.
        print(
            f"BEADS.md: {len(rejected)} foreign ship-gate artifact(s) rejected; the gate "
            "fails closed until they are reviewed (names on stderr and in STATE.md)"
        )
        print(message, file=sys.stderr)
        try:
            append_state_blocker(
                confined(phase_project_root(phase_dir), ".planning", "STATE.md"), message
            )
        except ValueError:
            pass

    try:
        epic_id = resolve_phase_epic(phase_dir)
    except EpicAuthorityError as exc:
        # Fail closed: a stale BEADS.md must not satisfy the ship gate.
        out_path.unlink(missing_ok=True)
        print(f"BEADS.md: epic identity authority failed: {exc}", file=sys.stderr)
        return 1

    def write_unknown(argv):
        # Fail closed: a non-numeric sentinel never equals 0, so the
        # artifact-frontmatter-equals ship:pre gates block (gsd-core 1.12 and
        # 1.16 compare by === / String()); never write a count we do not know.
        # The file keeps epic/blocking_open/diverged so ship_override can still
        # record its audit trailer.
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _atomic_write_text(
            out_path,
            "---\n"
            f"phase: {phase_dir.name}\n"
            f"epic: {epic_id}\n"
            "open: unknown\nclosed: unknown\nblocking_open: unknown\ndiverged: unknown\n"
            f'generated_from: "{" ".join(argv)}"\n'
            f"generated_at: {generated_at}\n"
            "---\n\n"
            f"# BEADS.md: {phase_dir.name}\n\nbd state unknown.\n",
        )

    # A previous run's BEADS.md (e.g. blocking_open: 0) must not satisfy the
    # ship:pre gate on stale data, whichever path below fails or raises: drop
    # it when no epic is known (a missing artifact blocks the gate too), else
    # overwrite it with the unknown sentinel now; the success path replaces it.
    if epic_id is None:
        out_path.unlink(missing_ok=True)
    else:
        write_unknown(["regeneration", "incomplete"])
    if rejected:
        return 1

    if not bd_available():
        if epic_id is not None:
            write_unknown(["bd", "unavailable"])
        _skip_bd_unavailable(phase_dir, "beads-status regenerate-beads-md")
        return 0

    if epic_id is None:
        print("no epic yet -- nothing to regenerate")
        return 0

    argv = _beads_md_argv(epic_id)
    rows = _checked_bd_list_rows(run_bd(argv))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if rows is None:
        write_unknown(argv)
        print(
            "BEADS.md: bd list failed -- counts unknown, ship gate will block",
            file=sys.stderr,
        )
        return 1

    degraded_plans = []
    ordinal_map = _resolve_task_ordinal_map(phase_dir, degraded_plans)
    unmapped_open = 0
    if _milestone_scoped(phase_dir):
        problem = None
        if degraded_plans:
            # The ordinal map filters the shared epic's rows: a plan that
            # failed to parse hides its own issues, so the counts are unknown.
            problem = "degraded plan(s) " + ", ".join(degraded_plans)
        else:
            try:
                known_ids = collect_scope_task_ids(phase_dir, epic_id) | ordinal_map.keys()
            except (PlanParseError, OSError) as exc:
                # A sibling phase's issues cannot be told apart from stray ones.
                problem = f"sibling plan unreadable ({exc})"
        if problem:
            write_unknown(argv)
            print(f"BEADS.md: {problem} -- counts unknown, ship gate will block", file=sys.stderr)
            return 1
        # The milestone epic is shared: other phases' children are not this
        # phase's rows or counts (gsd-beads-cjbc.9). An open issue no plan of
        # any phase names belongs to no phase, so it blocks all of them.
        unmapped_open = sum(
            1 for r in rows if r.get("id") not in known_ids and r.get("status") != "closed"
        )
        rows = [r for r in rows if r.get("id") in ordinal_map]
    closed_count = sum(1 for r in rows if r.get("status") == "closed")
    open_count = len(rows) - closed_count
    # D-01/D-02: every open issue under this phase's epic scope counts, no
    # priority/type filter; plus any unmapped milestone follow-up.
    blocking_open = open_count + unmapped_open

    completed_ids = _resolve_completed_task_ids(phase_dir)
    diverged_count, task_status_by_id = _compute_diverged(rows, ordinal_map, completed_ids)
    if degraded_plans:
        # A plan that failed to parse hides its issues from ordinal_map, and
        # _compute_diverged skips them: the count is an undercount. The row
        # counts above are exact (per-phase mode counts every row), so only
        # the gate field turns non-numeric; the table still renders.
        diverged_count = "unknown"
        print(
            "BEADS.md: degraded plan(s) " + ", ".join(degraded_plans)
            + " -- diverged unknown, ship gate will block",
            file=sys.stderr,
        )
    table = _render_beads_md_table(rows, ordinal_map, task_status_by_id)

    frontmatter = (
        "---\n"
        f"phase: {phase_dir.name}\n"
        f"epic: {epic_id}\n"
        f"open: {open_count}\n"
        f"closed: {closed_count}\n"
        f"blocking_open: {blocking_open}\n"
        f"diverged: {diverged_count}\n"
        f'generated_from: "{" ".join(argv)}"\n'
        f"generated_at: {generated_at}\n"
        "---\n\n"
    )
    body = f"# BEADS.md: {phase_dir.name}\n\n{table}\n"

    _atomic_write_text(out_path, frontmatter + body)

    print(f"BEADS.md regenerated: {open_count} open, {closed_count} closed (epic {epic_id})")
    return 0


def close_phase_epic(phase_dir_arg):
    """gh-26: close the phase epic at verify:post when epic_per is `phase`,
    VERIFICATION.md says `status: passed`, and every epic child is closed.
    Fails closed (epic stays open) and always returns 0."""
    phase_dir = Path(phase_dir_arg).resolve()

    def blocker(msg):
        print(f"close-phase-epic: {msg}")
        try:
            append_state_blocker(
                confined(phase_project_root(phase_dir), ".planning", "STATE.md"), msg
            )
        except ValueError:
            pass

    if not bd_available():
        _skip_bd_unavailable(phase_dir, "close-phase-epic")
        return 0
    if read_epic_per(phase_project_root(phase_dir)) != "phase":
        return 0
    padded_phase = phase_dir.name.split("-", 1)[0]
    try:
        text = (phase_dir / f"{padded_phase}-VERIFICATION.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    match = FRONTMATTER_RE.match(text)
    if not match or not re.search(r"^status:[ \t]*passed[ \t]*\r?$", match.group(1), re.MULTILINE):
        return 0
    try:
        epic_id = resolve_phase_epic(phase_dir)
    except EpicAuthorityError as exc:
        print(f"close-phase-epic: epic identity authority failed: {exc}", file=sys.stderr)
        return 0
    if epic_id is None or not SAFE_BD_ID_RE.fullmatch(epic_id):
        return 0

    shown = run_bd(["bd", "show", epic_id, "--json"])
    if shown.returncode != 0:
        blocker(f"bd show {epic_id} failed -- epic left open")
        return 0
    try:
        payload = json.loads(shown.stdout)
    except (UnicodeError, json.JSONDecodeError):
        payload = None
    if isinstance(payload, list):
        payload = payload[0] if payload else None
    if isinstance(payload, dict) and payload.get("status") == "closed":
        print(f"close-phase-epic: epic {epic_id} already closed")
        return 0

    rows = _checked_bd_list_rows(run_bd(_beads_md_argv(epic_id)))
    if rows is None:
        blocker(f"bd list for epic {epic_id} failed -- epic left open")
        return 0
    if not rows:
        print(f"close-phase-epic: epic {epic_id} has no children -- left open")
        return 0
    open_ids = [r.get("id") for r in rows if r.get("status") != "closed"]
    if open_ids:
        safe = [i for i in open_ids if isinstance(i, str) and SAFE_BD_ID_RE.fullmatch(i)]
        print(
            f"close-phase-epic: epic {epic_id} left open, {len(open_ids)} open child(ren): "
            + ", ".join(safe)
        )
        return 0

    closed = run_bd(["bd", "close", epic_id, "--reason", f"phase verified: {phase_dir.name}"])
    if closed.returncode != 0:
        blocker(f"bd close {epic_id} failed -- epic left open")
    else:
        print(f"close-phase-epic: closed epic {epic_id}")
    return 0


def _resolve_default_phase_dir(project_root):
    """B13/D-08: with no explicit phase_dir argument, resolve the current/
    last-active phase from STATE.md's `current_phase` frontmatter -- zero-
    padded to match a `.planning/phases/NN-*` directory's leading token.
    Returns None on any miss (missing STATE.md, no frontmatter, no
    `current_phase` key, no matching directory) -- fail-open, matching
    every other resolution path in this script; the caller decides how to
    report a None."""
    state_path = confined(project_root, ".planning", "STATE.md")
    if not state_path.exists():
        return None
    text = state_path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        return None
    m = CURRENT_PHASE_RE.search(fm_match.group(1))
    if not m:
        return None
    padded = phase_dir_prefix(m.group(1).strip())
    phases_root = confined(project_root, ".planning", "phases")
    if not phases_root.is_dir():
        return None
    for candidate in sorted(phases_root.iterdir()):
        if candidate.is_dir() and candidate.name.split("-", 1)[0] == padded:
            return candidate
    return None


def render_status_mapping(phase_dir_arg):
    """B13/D-07..D-09: on-demand, read-only plan-task <-> bd issue mapping
    view for a phase. Prints the same 6-column table regenerate_beads_md
    builds (reused verbatim, RESEARCH's Don't Hand-Roll), followed by two
    orphan sections: a bd-side orphan (an epic child matching no current
    task, computed against collect_epic_task_ids -- deliberately not
    find_orphans, whose already-closed filtering is tuned for the sync
    path's auto-close decision, not a read-only report) and a task-side
    orphan (a plan task carrying no <beads-id> at all -- new logic, no
    existing function surfaces this). T-04-05: never calls bd close/
    update/comment -- this function only reports, it never reconciles.
    """
    if not bd_available():
        _skip_bd_unavailable(Path(phase_dir_arg).resolve(), "beads-status on-demand")
        return 0

    phase_dir = Path(phase_dir_arg).resolve()

    try:
        epic_id = resolve_phase_epic(phase_dir)
    except EpicAuthorityError as exc:
        print(f"beads-status: epic identity authority failed: {exc}", file=sys.stderr)
        return 1
    if epic_id is None:
        print("no epic yet -- nothing to show")
        return 0

    rows = _checked_bd_list_rows(run_bd(_beads_md_argv(epic_id)))
    if rows is None:
        print("beads-status: bd list failed -- mapping unavailable", file=sys.stderr)
        return 1

    ordinal_map = _resolve_task_ordinal_map(phase_dir)
    completed_ids = _resolve_completed_task_ids(phase_dir)
    _diverged_count, task_status_by_id = _compute_diverged(rows, ordinal_map, completed_ids)
    table_rows = rows
    if _milestone_scoped(phase_dir):
        table_rows = [r for r in rows if r.get("id") in ordinal_map]
    table = _render_beads_md_table(table_rows, ordinal_map, task_status_by_id)

    try:
        current_ids = collect_scope_task_ids(phase_dir, epic_id)
    except PlanParseError:
        # _resolve_task_ordinal_map above already noted the plan in STATE.md;
        # an orphan list built without that plan's ids would be wrong.
        print("beads-status: a plan failed to parse -- mapping unavailable", file=sys.stderr)
        return 1
    bd_side_orphans = [(row, None) for row in rows if row.get("id") not in current_ids]

    task_side_orphans = []
    for plan_path in discover_plan_files(phase_dir).values():
        try:
            with _degrade_on_parse_error(phase_dir, plan_path):
                _, _, tasks = parse_plan(plan_path)
                for task in tasks:
                    if not task["beads_id"]:
                        task_side_orphans.append((plan_path.name, task["name"]))
        except (OSError, UnicodeDecodeError):
            continue

    lines = [table, "", "## Issues with no matching plan task", ""]
    if bd_side_orphans:
        lines.append(_render_issue_table(bd_side_orphans, include_matched_via=False))
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Plan tasks with no bd issue")
    lines.append("")
    if task_side_orphans:
        lines.extend(
            f"- {_sanitize_notice_value(plan_name, 200)}: {_sanitize_notice_value(task_name, 200)}"
            for plan_name, task_name in task_side_orphans
        )
    else:
        lines.append("None.")

    print("\n".join(lines))
    return 0


# One cell = escape pairs (`\\`, `\|`) or non-pipe chars, then its closing pipe.
CELL_RE = re.compile(r"((?:\\.|[^\\|])*)\|")
CELL_UNESCAPE_RE = re.compile(r"\\([\\|])")


def _parse_beads_md_table_rows(text):
    """Re-read a just-written BEADS.md's table rows (id, title, status) --
    render_wave_status_block never re-queries bd a second time.

    WR-01: splits on an unescaped `|` only. `_escape_table_cell` encodes a
    literal `|` in a cell value as `\\|`, but never removes the raw `|`
    byte -- a naive `str.split("|")` still shifts columns on exactly the
    bd-supplied `|` the escaping exists to close off (verified: an
    unescaped-aware split is required, escaping alone is not sufficient for
    this re-parse path, unlike a markdown renderer's visual display). Cells
    are un-escaped (`\\|` -> `|`) after splitting to recover the original
    value.
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = CELL_RE.findall(line if line.endswith("|") else line + "|")
        if cells and cells[0] == "":
            cells = cells[1:]
        cells = [CELL_UNESCAPE_RE.sub(r"\1", c.strip()) for c in cells]
        if len(cells) < 3 or cells[0] in ("", "Issue") or set(cells[0]) == {"-"}:
            continue
        rows.append({"id": cells[0], "title": cells[1], "status": cells[2]})
    return rows


def render_wave_status_block(phase_dir_arg, plan_ids):
    """B8: print a `<beads_status>` block naming exactly this wave's
    plan_ids' synced issues (id/title/status), sourced from a freshly
    regenerated BEADS.md -- the mechanism 02-RESEARCH.md verified actually
    reaches the composed executor prompt at execute:wave:pre (Pattern 2:
    skill-mediated, not contributions[]-mediated)."""
    regenerate_beads_md(phase_dir_arg)

    phase_dir = Path(phase_dir_arg).resolve()
    padded_phase = phase_dir.name.split("-", 1)[0]
    beads_md_path = phase_dir / f"{padded_phase}-BEADS.md"

    discovered = discover_plan_files(phase_dir)
    wanted_ids = []
    for plan_id in plan_ids:
        plan_path = discovered.get(plan_id)
        if plan_path is None:
            continue
        try:
            with _degrade_on_parse_error(phase_dir, plan_path):
                _, _, tasks = parse_plan(plan_path)
                for task in tasks:
                    if task["beads_id"]:
                        wanted_ids.append(task["beads_id"])
        except (OSError, UnicodeDecodeError):
            continue

    matched = []
    if wanted_ids and beads_md_path.exists():
        table_rows = _parse_beads_md_table_rows(beads_md_path.read_text(encoding="utf-8"))
        matched = [row for row in table_rows if row["id"] in wanted_ids]

    if not matched:
        print("no synced issues for this wave")
        return 0

    lines = ["<beads_status>"]
    for row in matched:
        lines.append(f"{row['id']}: {row['title']} ({row['status']})")
    lines.append("</beads_status>")
    print("\n".join(lines))
    return 0


def _read_beads_md_frontmatter(phase_dir):
    """Return {key: raw value string} for every top-level frontmatter line in
    {padded_phase}-BEADS.md, or {} when the file is absent (or malformed --
    same degrade-cleanly posture as every other bd-adjacent read in this
    script). ship_override's sole read of BEADS.md; never a live bd query."""
    phase_dir = Path(phase_dir)
    padded_phase = phase_dir.name.split("-", 1)[0]
    beads_md_path = phase_dir / f"{padded_phase}-BEADS.md"
    if not beads_md_path.exists():
        return {}
    # The gate may have read a different file than this one: recording these
    # counts would misstate what was bypassed.
    extras = _beads_md_extras(phase_dir, beads_md_path)
    if extras:
        print("ship-override: other BEADS file(s) the gate may read: "
              + ", ".join(_sanitize_notice_value(e.name, 200) for e in extras))
        return {}
    if not _is_generated_beads_md(beads_md_path):
        print(
            f"ship-override: {_sanitize_notice_value(beads_md_path.name, 200)} has no "
            "generated_from frontmatter"
        )
        return {}
    text = beads_md_path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        return {}
    return {
        m.group(1): m.group(2).strip()
        for m in BEADS_MD_FIELD_RE.finditer(fm_match.group(1))
    }


def _head_already_pushed(project_root):
    """True when HEAD must be treated as already on the remote -- amending it
    would rewrite a commit a remote has, diverging local history with no
    fast-forward path (push_branch never force-pushes). This happens on a
    ship retry after a prior run already completed push_branch.

    Asks git directly whether any remote-tracking ref contains HEAD
    (`for-each-ref --contains HEAD refs/remotes`): independent of
    push.default, `@{push}`/`@{u}` resolution and fork pushRemote setups,
    all of which made the earlier upstream comparison refuse an unpushed
    commit on a branch cut from origin/main. Returns False (assume safe)
    with no remote ref containing HEAD or on a git failure -- a targeted
    guard, not a general git-state validator."""

    def git(*args):
        return subprocess.run(
            ["git", *args],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )

    try:
        refs = git("for-each-ref", "--contains", "HEAD", "refs/remotes")
        return refs.returncode == 0 and bool(refs.stdout.strip())
    except (subprocess.TimeoutExpired, OSError):
        return False


def ship_override(phase_dir_arg):
    """D-05: record a `beads.ship_gate=false` bypass. Always attempts a
    durable `git commit --amend --trailer` first (load-bearing, never
    skipped on bd's account); independently attempts a best-effort `bd
    comment` mirror on the phase epic (fail-open, B6 -- bd unavailable or
    failing never changes the git half's outcome). Values come only from
    BEADS.md's own generated frontmatter, never a fresh live bd query."""
    phase_dir = Path(phase_dir_arg).resolve()
    fields = _read_beads_md_frontmatter(phase_dir)
    if "epic" not in fields or "blocking_open" not in fields or "diverged" not in fields:
        print("ship-override: BEADS.md missing or incomplete -- nothing recorded")
        return 1

    try:
        project_root = phase_project_root(phase_dir)
    except ValueError as exc:
        print(f"ship-override: {exc}")
        return 1

    # The counts go into a git trailer and a bd comment: digits (or the
    # fail-closed `unknown` sentinel write_unknown emits when bd is down --
    # exactly when an override is needed) only.
    for key in ("blocking_open", "diverged"):
        if not re.fullmatch(r"\d+|unknown", fields[key]):
            print(f"ship-override: BEADS.md {key} is not a count ({fields[key]!r}) -- nothing recorded")
            return 1

    trailer = (
        f"Beads-Override: ship_gate bypassed, "
        f"blocking_open={fields['blocking_open']}, diverged={fields['diverged']}"
    )
    if _head_already_pushed(project_root):
        print(
            "ship-override: HEAD is already contained in a remote-tracking ref -- "
            "refusing to amend, that would diverge local history from origin and "
            "break the next push. This happens on a ship retry after a prior run "
            "already pushed. Record the override manually or re-run ship_override "
            "before the branch is pushed."
        )
        git_ok = False
    else:
        try:
            # --only with --amend and no paths: rewrite the message only,
            # never fold whatever else is staged into HEAD.
            result = subprocess.run(
                ["git", "commit", "--amend", "--only", "--allow-empty", "--no-edit", "--trailer", trailer],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=GIT_TIMEOUT,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            git_ok = False
            print(f"ship-override: git commit --amend failed: {exc}")
        else:
            git_ok = result.returncode == 0
            if git_ok:
                print(f"ship-override: recorded {trailer}")
            else:
                print(f"ship-override: git commit --amend failed: {result.stderr.strip()}")

    if not SAFE_BD_ID_RE.fullmatch(fields["epic"]):
        print(f"ship-override: BEADS.md epic {fields['epic']!r} is not a bd id -- comment mirror skipped")
    elif bd_available():
        comment_text = (
            f"ship_gate override: blocking_open={fields['blocking_open']}, "
            f"diverged={fields['diverged']}"
        )
        try:
            comment_result = run_bd(["bd", "comment", fields["epic"], comment_text])
        except (subprocess.TimeoutExpired, OSError) as exc:
            print(f"ship-override: bd comment failed: {exc}")
        else:
            if comment_result.returncode != 0:
                print(f"ship-override: bd comment failed: {comment_result.stderr.strip()}")
    else:
        print("ship-override: bd unavailable -- comment mirror skipped (B6)")

    return 0 if git_ok else 1


def check_patch(path_override=None):
    """17-04 Task 3 (TRUTH-02): the retained Patch 1 ship-md check. Preserves the three-case return contract (not-found /
    could-not-read / marker present-or-missing), the `CLAUDE_CONFIG_DIR`
    idiom, and naming the exact path probed in every message (WR-03).
    Read-only. Total by construction (T-17-04-02): both checks run inside
    `lifecycle_dispatch`'s one `try/except` alongside `beads_recall`.
    """
    if path_override:
        path = Path(path_override)
    else:
        path = Path(
            os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))
        ).joinpath(*SHIP_MD_PATCH_PATH_PARTS)
    if not path.exists():
        print(SHIP_MD_NOT_FOUND_MSG.format(filename=SHIP_MD_FILENAME, path=path))
        return 1
    # WR-02/CR-02: degrade to "cannot verify" rather than raise -- an
    # An unreadable target returns a checker result instead of raising so
    # retained Patch 1 ship diagnostics can still complete.
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(SHIP_MD_COULD_NOT_READ_MSG.format(filename=SHIP_MD_FILENAME, path=path, exc=exc))
        return 1
    present = SHIP_MD_PATCH_MARKER in text
    fmt = SHIP_MD_PRESENT_MSG if present else SHIP_MD_MISSING_MSG
    # WR-01: stdout is deliberate here, not a convention to "fix" -- the
    # hook (hooks/lifecycle-dispatch.sh) promotes only stdout into
    # additionalContext, so a stderr line would silently vanish.
    print(fmt.format(filename=SHIP_MD_FILENAME, path=path, version=SHIP_MD_PATCH_VERSION))
    return 0 if present else 1


def check_native_step_dispatch(point, workflow_path_override=None):
    """D-05 diagnostic (17-02 Task 1): report whether the installed gsd-core
    workflow file now dispatches `kind == "step"` hooks natively at this
    lifecycle point -- gsd-core PR #3687 (merged to `next` 2026-08-19,
    unreleased as of the installed 1.11.0), which `lifecycle_dispatch` needs
    to know so it can stand down at `plan:post`/`verify:post` rather than
    double-dispatch alongside gsd-core's own native loop.

    Opposite polarity from check_patch(): it asks "is our
    local patch still here" (missing is bad); this
    asks "does upstream now do this natively" (present means the hook is
    redundant here). Kept a SEPARATE function rather than a shared table
    with those two for exactly that reason -- sharing one table would
    produce a misleading unified pass/fail semantic.

    Region-scoped, not whole-file: a whole-file `kind == "step"` grep is a
    verified false positive on both shipped 1.11.0 workflow files --
    `plan-phase.md` carries three unrelated occurrences outside the
    `plan:post` region (the plan:pre generic contract, the auto-chain UI
    branch, the intel step read) and `verify-work.md`'s own `verify:post`
    region already carries one qualified to `ref.skill == "secure-phase"`.
    The region is anchored on the point's own literal
    `render-hooks <point> --raw` call and ends at the earlier of the next
    non-fenced level-two heading or `NATIVE_STEP_DISPATCH_REGION_LINES`
    lines past the anchor -- fence awareness matters because
    `verify-work.md` prints heading-shaped lines inside fenced output
    templates, which would otherwise terminate the region far too early.

    Every miss -- unmapped point, missing file, unreadable file, no anchor,
    no qualifying line in the region -- returns 0 (not detected), which
    degrades to today's working double dispatch: the only acceptable
    failure direction (D-05). Never raises.

    WR-03: only the Claude runtime home (`CLAUDE_CONFIG_DIR`, default
    `~/.claude`) is probed, matching the two patch checkers above; every
    message names the exact path checked. Unlike those two (which print to
    stdout, since their only caller today is plan:pre, an already-active
    dispatch point), this probe's own diagnostics print to stderr: it is
    called unconditionally at the top of the plan:post/verify:post
    branches, before either knows whether there is anything to do, and
    stdout is what a PostToolUse hook promotes into Claude's context -- a
    benign "not detected, continuing as normal" diagnostic must not turn a
    silent no-op (e.g. no PLAN.md in the phase) into per-call noise there.
    """
    filename = NATIVE_STEP_DISPATCH_WORKFLOW_FILES.get(point)
    if filename is None:
        return 0
    if workflow_path_override:
        workflow_path = Path(workflow_path_override)
    else:
        workflow_path = (
            Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
            / "gsd-core"
            / "workflows"
            / filename
        )
    try:
        found = workflow_path.exists()
    except OSError:  # e.g. PermissionError on an unsearchable parent
        found = False
    if not found:
        print(
            f"native-step-dispatch probe ({point}): {workflow_path} not found -- "
            "assuming not detected, lifecycle-dispatch keeps dispatching",
            file=sys.stderr,
        )
        return 0
    try:
        text = workflow_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(
            f"native-step-dispatch probe ({point}): {workflow_path} could not be read "
            f"({exc}) -- assuming not detected, lifecycle-dispatch keeps dispatching",
            file=sys.stderr,
        )
        return 0

    # Flags may sit between the point and `--raw` (gsd-core 1.16 adds
    # `--after-fingerprint "$PHASE_DIR"` at verify:post).
    anchor_re = re.compile(rf"render-hooks {re.escape(point)}\b.*--raw")
    lines = text.splitlines()
    anchor_idx = next((i for i, line in enumerate(lines) if anchor_re.search(line)), None)
    if anchor_idx is None:
        print(
            f"native-step-dispatch probe ({point}): no 'render-hooks {point} ... --raw' anchor found in "
            f"{workflow_path} -- assuming not detected, lifecycle-dispatch keeps dispatching",
            file=sys.stderr,
        )
        return 0

    # Fence parity carries across the anchor: the anchor line itself commonly
    # sits inside a ```bash ... ``` block opened BEFORE it (the shipped
    # shape), so the closing fence line immediately after the anchor must
    # not be mistaken for an opening one.
    in_fence = False
    for i in range(anchor_idx):
        if lines[i].strip().startswith("```"):
            in_fence = not in_fence

    # gsd-beads-u67.13: fence state must carry through the SAME pass that
    # finds the region boundary and matches the step arm -- computing
    # region_end in one loop then re-matching over the sliced lines in a
    # second, fence-blind loop let a kind=="step" line inside a fenced doc
    # example (prose, not live dispatch text) false-positive as detected.
    region_limit = min(anchor_idx + 1 + NATIVE_STEP_DISPATCH_REGION_LINES, len(lines))
    for i in range(anchor_idx, region_limit):
        line = lines[i]
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and i > anchor_idx and re.match(r"^##\s", line):
            break
        if not in_fence and _GENERIC_STEP_KIND_RE.search(line) and not _STEP_QUALIFIER_RE.search(line):
            print(
                f"native-step-dispatch probe ({point}): detected at {workflow_path} -- "
                "lifecycle-dispatch standing down for this point",
                file=sys.stderr,
            )
            return 1

    print(
        f"native-step-dispatch probe ({point}): not detected at {workflow_path} -- "
        "lifecycle-dispatch continues dispatching",
        file=sys.stderr,
    )
    return 0


def main(argv=None):
    global _BD_CWD
    try:
        return _main(argv)
    finally:
        _BD_CWD = None


def _main(argv):
    parser = argparse.ArgumentParser(prog="sync.py")
    sub = parser.add_subparsers(dest="command", required=True)
    create_p = sub.add_parser(
        "create-issues", help="Sync a PLAN.md's tasks into bd issues under a phase epic"
    )
    create_p.add_argument("plan_path")
    resolver_p = sub.add_parser(
        "resolve-task-content",
        help="Resolve one Beads issue into gsd-core task content",
    )
    resolver_p.add_argument("issue_id")
    close_p = sub.add_parser(
        "close-wave",
        help="Batch-close every completed task's issue across every plan in a wave",
    )
    close_p.add_argument("phase_dir")
    close_p.add_argument("plan_ids", nargs="+")
    reconcile_p = sub.add_parser(
        "reconcile-stale-closed",
        help="Phase-wide idempotent backstop: close every task-complete issue still open in bd, across every plan in the phase (D-08)",
    )
    reconcile_p.add_argument("phase_dir")
    recall_p = sub.add_parser(
        "beads-recall",
        help="Scan open bd issues and write BEADS-RECALL.md naming any issue touching this phase's scope",
    )
    recall_p.add_argument("phase_dir")
    regen_p = sub.add_parser(
        "regenerate-beads-md",
        help="Fully overwrite BEADS.md from a live bd query (D-05..D-08 frontmatter/table shape)",
    )
    regen_p.add_argument("phase_dir")
    close_epic_p = sub.add_parser(
        "close-phase-epic",
        help="Close the phase epic when VERIFICATION.md passed and every child is closed",
    )
    close_epic_p.add_argument("phase_dir")
    wave_status_p = sub.add_parser(
        "wave-status-block",
        help="Regenerate BEADS.md then print a <beads_status> block naming this wave's issues",
    )
    wave_status_p.add_argument("phase_dir")
    wave_status_p.add_argument("plan_ids", nargs="+")
    ship_override_p = sub.add_parser(
        "ship-override",
        help="Record a beads.ship_gate=false bypass via a git trailer plus a best-effort bd comment (D-05)",
    )
    ship_override_p.add_argument("phase_dir")
    # 17-04 Task 3 (D-08): one verb reaches the retained patch-check target.
    check_patch_p = sub.add_parser(
        "check-patch",
        help="Report whether the local GSD-CORE-PATCH.md ship-md patch is present",
    )
    check_patch_p.add_argument("target", choices=["ship-md"])
    check_patch_p.add_argument("--path", default=None)
    lifecycle_p = sub.add_parser(
        "lifecycle-dispatch",
        help="Run the beads operation a lifecycle point declares (gh-2); entered from the "
        "plugin's PostToolUse hook, never from gsd-core workflow prose",
    )
    # Deliberately no `choices=`: argparse would exit 2 with a usage dump on an
    # unrecognised point, and this verb's whole contract is that it never
    # returns non-zero (every hook it serves is `onError: "skip"`).
    lifecycle_p.add_argument("point")
    lifecycle_p.add_argument(
        "phase_dir",
        nargs="?",
        default=None,
        help="Explicit phase directory; confined beneath the project .planning/phases root",
    )
    sub.add_parser(
        "migrate-todos",
        help="One-shot migration of .planning/todos/pending/ entries into bd issues (B12)",
    )
    status_p = sub.add_parser(
        "status",
        help="On-demand, read-only plan-task <-> bd issue mapping view for a phase, "
        "including orphans on both sides (B13)",
    )
    status_p.add_argument("phase_dir", nargs="?", default=None)
    args = parser.parse_args(argv)
    # bd finds its database by walking up from cwd, so every verb pins it: a
    # verb without a path argument (status, migrate-todos, lifecycle-dispatch,
    # resolve-task-content) falls back to the process cwd, not to "unpinned".
    _set_bd_root(
        args.phase_dir if getattr(args, "phase_dir", None)
        else Path(args.plan_path).resolve().parent if getattr(args, "plan_path", None)
        else None
    )
    if args.command == "resolve-task-content":
        return resolve_task_content(args.issue_id)
    if args.command == "create-issues":
        # 17-02 Task 3 (D-06): the explicit CLI path's strip permission is
        # governed by beads.sync_mode -- the hook path (lifecycle_dispatch)
        # never reaches this branch and stays ungated by design (D-03).
        # Fail-open: an unresolvable project root falls back to the
        # shipped authoritative default rather than raising.
        try:
            sync_mode_root = phase_project_root(Path(args.plan_path).resolve().parent)
        except ValueError:
            sync_mode_root = None
        sync_mode = (
            read_sync_mode(sync_mode_root) if sync_mode_root is not None else "authoritative"
        )
        return create_issues(args.plan_path, allow_strip=(sync_mode != "mirror"))
    if args.command == "close-wave":
        return close_wave(args.phase_dir, args.plan_ids)
    if args.command == "reconcile-stale-closed":
        return reconcile_stale_closed(args.phase_dir)
    if args.command == "beads-recall":
        return beads_recall(args.phase_dir)
    if args.command == "regenerate-beads-md":
        return regenerate_beads_md(args.phase_dir)
    if args.command == "close-phase-epic":
        return close_phase_epic(args.phase_dir)
    if args.command == "wave-status-block":
        return render_wave_status_block(args.phase_dir, args.plan_ids)
    if args.command == "ship-override":
        return ship_override(args.phase_dir)
    if args.command == "check-patch":
        return check_patch(args.path)
    if args.command == "lifecycle-dispatch":
        return lifecycle_dispatch(args.point, args.phase_dir)
    if args.command == "migrate-todos":
        try:
            project_root = find_project_root(Path.cwd())
            pending_dir = confined(project_root, ".planning", "todos", "pending")
        except ValueError as exc:
            print(f"migrate-todos: {exc}", file=sys.stderr)
            return 1
        return migrate_todos(str(pending_dir))
    if args.command == "status":
        if args.phase_dir is not None:
            return render_status_mapping(args.phase_dir)
        try:
            project_root = find_project_root(Path.cwd())
        except ValueError as exc:
            print(f"status: {exc}", file=sys.stderr)
            return 1
        default_dir = _resolve_default_phase_dir(project_root)
        if default_dir is None:
            print("no phase directory given and no default could be resolved from STATE.md")
            return 1
        return render_status_mapping(str(default_dir))
    return 1


if __name__ == "__main__":
    sys.exit(main())
