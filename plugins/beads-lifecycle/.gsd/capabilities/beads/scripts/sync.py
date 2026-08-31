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
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BD_TIMEOUT = 15  # seconds; bounded timeout on every bd subprocess call
GIT_TIMEOUT = 15  # seconds; bounded timeout on every git subprocess call (ship_override)
NOTICE = "bd unavailable -- sync skipped"
BEADS_RECALL_STATUSES = "open,in_progress,blocked,deferred"

TASK_RE = re.compile(r"<task\b[^>]*>.*?</task>", re.DOTALL)
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
TASK_TYPE_RE = re.compile(r'<task\b[^>]*\btype="([^"]*)"')
TASK_OPEN_TAG_RE = re.compile(r"<task\b[^>]*>")
TRACKER_ID_RE = re.compile(
    r'''(?<=\s)tracker-id\s*=\s*(?:"([^"]*)"|'([^']*)')'''
)
TRACKER_ID_LIKE_RE = re.compile(
    r'''(?<=\s)([^\s=]*tracker-id)\s*=\s*(?:"([^"]*)"|'([^']*)')''',
    re.IGNORECASE,
)
# 16-01 Task 2 (D-06): <objective> is plan-level only -- it appears exactly
# once per PLAN.md, before <tasks>, and never inside an individual <task>
# block (verified against gsd-core's canonical phase-prompt.md template and
# a real executed PLAN.md, 16-RESEARCH.md Priority 3). Matched against the
# whole plan text, not a TASK_RE block, unlike every regex above.
OBJECTIVE_RE = re.compile(r"<objective>(.*?)</objective>", re.DOTALL)
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?\r?\n)---\r?\n", re.DOTALL)
BEADS_EPIC_RE = re.compile(r"^beads_epic:\s*(\S+)\s*$", re.MULTILINE)
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
TITLE_RE = re.compile(r"^title:\s*(.+)$", re.MULTILINE)
AREA_RE = re.compile(r"^area:\s*(\S+)\s*$", re.MULTILINE)
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
# (GSD-CORE-PATCH.md) -- check_shipmd_patch does a plain substring check
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
# 16-03 Task 1 (D-05): the literal marker bracketing the local
# execute-plan.md bd-task-read patch (GSD-CORE-PATCH.md) --
# check_execute_plan_patch does a plain substring check against this, never
# a regex, same discipline as SHIP_MD_PATCH_MARKER immediately above.
EXECUTE_PLAN_PATCH_MARKER = "<!-- gsd-beads-patch:execute-plan-bd-task-read v1 -->"
# 17-04 Task 3 (D-08/D-10): the table `check_patch` walks -- a plain dict of
# literals keyed by target name (this module's existing small-fixed-variant
# idiom, LIFECYCLE_DISPATCH_POINTS below; no registry/decorator/class). Each
# entry's own `version` matters: the two markers are independently versioned
# (v2 vs v1), so one shared field would let a bump to one silently apply to
# both. The `*_msg` fields are the exact pre-merge message templates.
PATCH_CHECKS = {
    "ship-md": {
        "default_path_parts": ("gsd-core", "workflows", "ship.md"),
        "marker": SHIP_MD_PATCH_MARKER,
        "version": "v2",
        "filename": "ship.md",
        "not_found_msg": (
            "⚠ {filename} not found at {path} -- cannot verify the local ship:pre dispatch "
            "patch (only this runtime home was probed; other runtime homes such as "
            "CODEX_HOME or CURSOR_CONFIG_DIR were not checked)"
        ),
        "could_not_read_msg": (
            "⚠ {filename} at {path} could not be read ({exc}) -- cannot verify the "
            "local ship:pre dispatch patch"
        ),
        "present_msg": "{filename} ship:pre step-dispatch patch: present ({version}) at {path}",
        "missing_msg": (
            "⚠ {filename}'s ship:pre generic STEP dispatch patch (beads, {version}) is "
            "missing at {path} -- the ship_override step will not fire. The two ship:pre "
            "GATES are unaffected: gsd-core >= 1.11.0 dispatches those natively (#3559 / PR "
            "#3608). Reapply: see .gsd/capabilities/beads/GSD-CORE-PATCH.md"
        ),
    },
    "execute-plan": {
        "default_path_parts": ("gsd-core", "workflows", "execute-plan.md"),
        "marker": EXECUTE_PLAN_PATCH_MARKER,
        "version": "v1",
        "filename": "execute-plan.md",
        "not_found_msg": (
            "⚠ {filename} not found at {path} -- cannot verify the local bd-task-read "
            "patch (only this runtime home was probed; other runtime homes such "
            "as CODEX_HOME or CURSOR_CONFIG_DIR were not checked)"
        ),
        "could_not_read_msg": (
            "⚠ {filename} at {path} could not be read ({exc}) -- cannot "
            "verify the local bd-task-read patch"
        ),
        "present_msg": "{filename} bd-task-read patch: present ({version}) at {path}",
        "missing_msg": (
            "⚠ {filename}'s bd-task-read patch (beads) is missing at {path} -- "
            "gsd-executor will not read task content from bd. "
            "Reapply: see .gsd/capabilities/beads/GSD-CORE-PATCH.md"
        ),
    },
}
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
MILESTONE_RE = re.compile(r"^milestone:\s*(\S+)\s*$", re.MULTILINE)
MILESTONE_NAME_RE = re.compile(r"^milestone_name:\s*(\S+)\s*$", re.MULTILINE)


def run_bd(argv, timeout=BD_TIMEOUT):
    """Run one bd subcommand from a typed argv list; shell interpretation is
    never enabled here -- see module docstring, T-01-01."""
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def bd_available():
    """B6/D-08 fail-open detection point: locate the binary, run one cheap read
    command. Absent, non-zero exit, or timeout all take the same "unavailable"
    path -- this function is the single point of truth for that decision."""
    if shutil.which("bd") is None:
        return False
    try:
        result = run_bd(["bd", "list", "--json", "-n", "1"])
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


def append_state_blocker(state_path, message):
    """Append one dated bullet under STATE.md's Blockers/Concerns heading (D-08)."""
    state_path = Path(state_path)
    if not state_path.exists():
        return
    text = state_path.read_text(encoding="utf-8")
    heading = "### Blockers/Concerns"
    idx = text.find(heading)
    if idx == -1:
        return
    line_end = text.find("\n", idx)
    if line_end == -1:
        line_end = len(text)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bullet = f"\n\n- {date}: {message}"
    state_path.write_text(text[:line_end] + bullet + text[line_end:], encoding="utf-8")


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


def confined(root, *parts):
    """Join parts onto root and reject any resolved escape (T-01-02)."""
    candidate = root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError(f"path escapes project root: {candidate} not under {root}")
    return candidate


def parse_plan(path):
    """Return (full_text, frontmatter_body, [task dict, ...]).

    Anchors on `<name>...</name>` inside each `<task ...>...</task>` block --
    real PLAN.md files carry no markdown task heading to anchor on instead.
    """
    with Path(path).open("r", encoding="utf-8", newline="") as plan_file:
        text = plan_file.read()
    fm_match = FRONTMATTER_RE.match(text)
    frontmatter = fm_match.group(1) if fm_match else ""
    tasks = []
    for m in TASK_RE.finditer(text):
        block = m.group(0)
        opening_tag_m = TASK_OPEN_TAG_RE.match(block)
        opening_tag = opening_tag_m.group(0) if opening_tag_m else ""
        name_m = NAME_RE.search(block)
        id_m = BEADS_ID_RE.search(block)
        files_m = FILES_RE.search(block)
        type_m = TASK_TYPE_RE.search(block)
        tracker_ids = [
            next(group for group in tracker_m.groups() if group is not None)
            for tracker_m in TRACKER_ID_RE.finditer(opening_tag)
        ]
        tracker_id_candidates = [
            tracker_m.group(0) for tracker_m in TRACKER_ID_LIKE_RE.finditer(opening_tag)
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
                "beads_id": id_m.group(1).strip() if id_m else None,
                "files": files,
                "type": type_m.group(1).strip() if type_m else "",
                "tracker_ids": tracker_ids,
                "tracker_id_candidates": tracker_id_candidates,
                "tracker_insert": m.start() + type_m.end() if type_m else None,
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
    if not title_m:
        raise ValueError(f"{path.name}: missing 'title' frontmatter key")
    title = title_m.group(1).strip()

    severity_m = SEVERITY_RE.search(frontmatter)
    if not severity_m or severity_m.group(1) not in SEVERITY_TO_PRIORITY:
        raise ValueError(
            f"{path.name}: missing or unrecognized 'severity' frontmatter key"
        )
    severity = severity_m.group(1)

    area_m = AREA_RE.search(frontmatter)
    area = area_m.group(1) if area_m else "general"

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
        items = [f.strip() for f in task["read_first"].split(",") if f.strip()]
        sections.append("## Read First\n" + "\n".join(f"- {f}" for f in items))
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
            if re.match(rf"^{re.escape(fence)}", stripped):
                fence = None
            continue
        opening = re.match(r"^([\\x60~]{3,})", stripped)
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
    entry (D-04/Pitfall 2). No duplicate check against existing bd issues
    (D-06): every parseable todo always creates a new issue.
    """
    if not bd_available():
        print(NOTICE)
        try:
            project_root = find_project_root(Path(pending_dir_arg).resolve())
        except ValueError:
            project_root = None
        if project_root is not None:
            append_state_blocker(
                confined(project_root, ".planning", "STATE.md"),
                "bd unavailable -- migrate-todos skipped (B6/D-08)",
            )
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
    for todo_path in todo_paths:
        try:
            todo = parse_todo(todo_path)
        except ValueError as exc:
            parse_errors.append((todo_path.name, str(exc)))
            continue

        result = run_bd(
            [
                "bd",
                "create",
                todo["title"],
                "-d",
                _todo_description(todo),
                "-t",
                "task",
                "-p",
                str(SEVERITY_TO_PRIORITY[todo["severity"]]),
                "-l",
                f"area-{todo['area']}",
                "--silent",
            ]
        )
        if result.returncode != 0:
            bd_create_failed.append((todo_path.name, result.stderr.strip()))
            continue

        issue_id = result.stdout.strip()
        todo_path.unlink()  # D-05: delete only after bd create's return code is confirmed 0
        moved.append((todo_path.name, issue_id))

    lines = [
        f"Migrated {len(moved)} todo(s), {len(parse_errors)} could not be interpreted, "
        f"{len(bd_create_failed)} bd create failed"
    ]
    if moved:
        lines.append("  moved:")
        lines.extend(f"    {name} -> {issue_id}" for name, issue_id in moved)
    if parse_errors:
        lines.append("  could not be interpreted:")
        lines.extend(f"    {name}: {reason}" for name, reason in parse_errors)
    if bd_create_failed:
        lines.append("  bd create failed:")
        lines.extend(f"    {name}: {reason}" for name, reason in bd_create_failed)
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
            print(
                f"dependency edge failed: {blocked_id} depends-on {blocker_id}: "
                f"{result.stderr.strip()}"
            )


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
    """Bound and single-line an untrusted config value before it enters
    agent-readable `additionalContext` (T-17-03-02): drop every
    non-printable character -- `str.isprintable()` is False for both
    control characters and newlines -- and truncate to `max_len`, so a
    crafted config value cannot inject additional lines or fabricate
    structure into the notice. Non-string values are stringified first: one
    code path for every JSON type the key could hold."""
    text = value if isinstance(value, str) else str(value)
    text = "".join(ch for ch in text if ch.isprintable())
    return text[:max_len]


def check_sync_mode_value(project_root):
    """17-03 Task 2 (D-04 Case 2): read-only, never-raises notice for a
    project whose `.planning/config.json` stores a `beads.sync_mode` value
    outside the declared enum -- the retired `off` value, an empty string,
    a case/whitespace variant, or a non-string type. Called from
    `lifecycle_dispatch`'s `plan:pre` branch, beside `check_shipmd_patch`
    and `check_execute_plan_patch`, inside the same `try/except Exception`,
    so a failure here degrades to at most one skipped notice and cannot
    take out `beads_recall`.

    Prints to STDOUT -- the same stream `check_patch` uses for all four of
    its message paths (`not_found_msg`, `could_not_read_msg`, `present_msg`,
    `missing_msg`), which `check_shipmd_patch`/`check_execute_plan_patch`
    both thin-wrap (WR-01: this function shares that convention, it is not
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
        "authoritative default applies, so task bodies may still be stripped once the "
        "read-path patch gate passes. Remedy: gsd-tools config-set beads.sync_mode "
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


def lifecycle_dispatch(point):
    """gh-2: run the beads operation a lifecycle point declares, entered from
    the plugin's `PostToolUse` hook rather than from gsd-core's workflow prose.
    Why the hook exists at all is documented once, in
    `hooks/lifecycle-dispatch.sh`'s header.

    Each point maps onto an existing verb, all of them derivable from
    `phase_dir` alone -- deliberate, since the render-hooks call carries no
    wave plan-id list. `execute:wave:post` therefore uses the phase-wide
    idempotent `reconcile_stale_closed` backstop (D-08) rather than
    `close_wave`, and `execute:wave:pre` renders a phase-wide (superset,
    never lossy) `<beads_status>` block.

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
        project_root = find_project_root(Path.cwd())
    except ValueError:
        return 0
    if not read_beads_enabled(project_root):
        return 0
    phase_dir = _resolve_default_phase_dir(project_root)
    if phase_dir is None or not phase_dir.is_dir():
        # stderr, not stdout: a repository between milestones has no
        # `.planning/phases/` at all, so this fires on every render-hooks call
        # in it. `hooks/lifecycle-dispatch.sh` promotes stdout to Claude's
        # context and leaves stderr in the debug log, so a benign skip stays
        # diagnosable without becoming per-call noise in the transcript.
        print(
            f"lifecycle-dispatch {point}: no phase directory resolved from STATE.md's "
            "current_phase -- skipped",
            file=sys.stderr,
        )
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
            check_shipmd_patch()
            check_execute_plan_patch()
            # 17-03 Task 2 (D-04 Case 2): stdout notice for an out-of-enum
            # beads.sync_mode value -- all three plan:pre checks above and
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
                create_issues(str(plans[plan_id]), allow_strip=False)
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
    except Exception as exc:  # noqa: BLE001 -- onError: "skip" is the declared contract
        print(f"lifecycle-dispatch {point}: skipped after an unexpected failure ({exc})")
    return 0


def milestone_epic_title(state_path):
    """B14: return "Milestone {milestone}: {milestone_name}" from STATE.md's
    frontmatter (RESEARCH's Open Question 1 recommendation) -- empty string
    for either component when its key is absent from the frontmatter."""
    text = Path(state_path).read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    frontmatter = fm_match.group(1) if fm_match else ""
    milestone_m = MILESTONE_RE.search(frontmatter)
    milestone = milestone_m.group(1) if milestone_m else ""
    name_m = MILESTONE_NAME_RE.search(frontmatter)
    milestone_name = name_m.group(1) if name_m else ""
    return f"Milestone {milestone}: {milestone_name}"


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
    text = Path(roadmap_path).read_text(encoding="utf-8")
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

    phases_root = confined(project_root, ".planning", "phases")
    candidate_ids = []
    if phases_root.is_dir():
        for phase_dir in sorted(p for p in phases_root.iterdir() if p.is_dir()):
            for plan_path in discover_plan_files(phase_dir).values():
                try:
                    _, plan_frontmatter, _ = parse_plan(plan_path)
                except (OSError, UnicodeDecodeError):
                    continue
                m = BEADS_EPIC_RE.search(plan_frontmatter)
                if m and m.group(1) not in candidate_ids:
                    candidate_ids.append(m.group(1))

    for candidate_id in candidate_ids:
        check = run_bd(["bd", "show", candidate_id, "--json"])
        if check.returncode != 0:
            continue
        try:
            data = json.loads(check.stdout)
        except json.JSONDecodeError:
            continue
        if data.get("title") == title:
            return candidate_id

    if candidate_ids:
        print(
            f"divergence: {len(candidate_ids)} existing epic(s) found for this milestone but "
            f"none matched title {title!r} -- creating a new epic (STATE.md milestone/"
            "milestone_name may have changed)"
        )

    argv = ["bd", "create", title]
    if milestone_bullet:
        argv += ["-d", _epic_description(milestone_bullet)]
    argv += ["--type", "epic", "--silent"]
    result = run_bd(argv)
    if result.returncode != 0:
        raise RuntimeError(f"bd create (epic) failed: {result.stderr.strip()}")
    return result.stdout.strip()


def resolve_epic(frontmatter, roadmap_path, phase_num, phase_dir, project_root, objective=""):
    """Return (epic_id, needs_write, stale_epic_id). Resolve-by-id first,
    create only on confirmed absence -- never by title (B4/B5 pattern
    applied to the epic level too).

    `needs_write` means "this plan's own frontmatter still lacks a
    resolving beads_epic and rewrite_plan must write one" -- not literally
    "created in bd" -- since the phase-scoped reuse path below finds an
    existing epic without creating one (gsd-beads-uh1: every plan in a
    phase shares one epic, per resolve_phase_epic's D-05 contract).

    `stale_epic_id` is the frontmatter's own `beads_epic` value when it no
    longer resolves in bd (WR-02: D-07's stale-identity reporting applied to
    the epic level) -- None when frontmatter carried no `beads_epic`, or it
    resolved successfully. The caller reports this the same way
    `resolve_issue`'s `divergent` flag is reported, so a resync after an
    external epic deletion never forks the phase across epics silently.

    B14/D-11: when `beads.epic_per` (read fresh here via `read_epic_per`) is
    `"milestone"`, resolution routes to `resolve_milestone_epic` and skips
    the phase-scoped path entirely -- a mid-milestone config change never
    disturbs a phase already mid-flight, since each call re-reads the
    config independently.
    """
    stale_epic_id = None
    m = BEADS_EPIC_RE.search(frontmatter)
    if m:
        epic_id = m.group(1)
        check = run_bd(["bd", "show", epic_id, "--json"])
        if check.returncode == 0:
            return epic_id, False, None
        # stored epic id no longer resolves in bd -- fall through and create fresh
        stale_epic_id = epic_id

    if read_epic_per(project_root) == "milestone":
        epic_id = resolve_milestone_epic(project_root)
        return epic_id, True, stale_epic_id

    shared_epic_id = resolve_phase_epic(phase_dir)
    if shared_epic_id is not None:
        check = run_bd(["bd", "show", shared_epic_id, "--json"])
        if check.returncode == 0:
            return shared_epic_id, True, stale_epic_id

    title = get_phase_header(roadmap_path, phase_num)
    description = _epic_description(objective)
    argv = ["bd", "create", title]
    if description:
        argv += ["-d", description]
    argv += ["--type", "epic", "--silent"]
    result = run_bd(argv)
    if result.returncode != 0:
        raise RuntimeError(f"bd create (epic) failed: {result.stderr.strip()}")
    return result.stdout.strip(), True, stale_epic_id


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


def resolve_issue(task, epic_id, ordinal_prefix, task_index):
    """Return (issue_id, created, divergent). <beads-id> is the identity;
    only create when it is absent -- never resolve or dedup by title (B4).

    When a <beads-id> is present but bd cannot find it, that is stale-
    identity divergence (D-07): report it, never recreate a replacement,
    never clear the element -- a Phase 3 ship gate acts on the divergence.
    """
    if task["beads_id"]:
        issue_id = task["beads_id"]
        if not SAFE_BD_ID_RE.fullmatch(issue_id):
            raise RuntimeError(f"unsafe stored beads-id: {issue_id!r}")
        check = run_bd(["bd", "show", issue_id, "--json"])
        if check.returncode != 0:
            return issue_id, False, True
        if not isinstance(check.stdout, str):
            raise RuntimeError("bd show returned invalid JSON")
        try:
            payload = json.loads(check.stdout)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("bd show returned invalid JSON") from exc
        if isinstance(payload, dict):
            payload = payload.get("data")
        if (
            not isinstance(payload, list)
            or len(payload) != 1
            or not isinstance(payload[0], dict)
            or payload[0].get("id") != issue_id
        ):
            raise RuntimeError(f"bd show did not identify {issue_id!r}")
        return issue_id, False, False
    title = f"{ordinal_prefix}.{task_index} {task['name']}"
    # CR-01: a checkpoint:*-typed task's real content lives in its own field
    # set (decision/context/options/... or what-built/how-to-verify/...),
    # never in the auto/tracer fields _task_description reads -- dispatch to
    # the matching renderer so a checkpoint task's -d is never empty. The
    # `if description` guard (matching resolve_epic's existing discipline)
    # is kept as a second line of defense even though both renderers already
    # return "" only when every source field is empty.
    if task.get("type", "").startswith("checkpoint:"):
        description = _checkpoint_task_description(task)
    else:
        description = _task_description(task)
    argv = ["bd", "create", title]
    if description:
        argv += ["-d", description]
    if task["acceptance_criteria"]:
        argv += ["--acceptance", task["acceptance_criteria"]]
    argv += ["--type", "task", "--parent", epic_id, "--silent"]
    result = run_bd(argv)
    if result.returncode != 0:
        raise RuntimeError(f"bd create (task) failed: {result.stderr.strip()}")
    issue_id = result.stdout.strip() if isinstance(result.stdout, str) else ""
    if not SAFE_BD_ID_RE.fullmatch(issue_id):
        raise RuntimeError(f"bd create (task) returned unsafe id: {issue_id!r}")
    return issue_id, True, False


def find_orphans(children, current_ids):
    """Return ids of epic children (bd list --all --json rows) that match no
    current task and are not already closed (D-06).

    --all is required by the caller: the default `bd list` omits closed
    issues, so a sweep that relied on that default would re-close an
    already-closed orphan on every run and break idempotency (B5) -- the
    not-already-closed check here is the other half of that guard.
    """
    return [
        c["id"]
        for c in children
        if c.get("id") not in current_ids and c.get("status") != "closed"
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
        except (OSError, UnicodeDecodeError):
            continue
        m = BEADS_EPIC_RE.search(frontmatter)
        if not m or m.group(1) != epic_id:
            continue
        for task in tasks:
            if task["beads_id"]:
                ids.add(task["beads_id"])
    return ids


def rewrite_plan(text, epic_id, epic_created, task_updates, native_updates):
    """Insert beads_epic plus per-task legacy and native identity updates.

    task_updates: [(name_end_pos, issue_id), ...] for tasks that had no
    <beads-id> before this run. Insertions happen in descending position
    order first so earlier offsets in `text` stay valid, then the
    frontmatter insertion (always at the front of the file) happens last.
    """
    insertions = [
        (name_end_pos, f"\n  <beads-id>{issue_id}</beads-id>")
        for name_end_pos, issue_id in task_updates
    ] + [
        (type_end_pos, f' tracker-id="beads:{issue_id}"')
        for type_end_pos, issue_id in native_updates
    ]
    for position, insertion in sorted(insertions, key=lambda item: item[0], reverse=True):
        text = text[:position] + insertion + text[position:]
    if epic_created:
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
# The fixed-shape pointer comment a stripped block gains, naming the beads
# id and the retrieval command. Only the prefix (not the whole line, since
# the id varies per task) is checked for idempotency: a second
# strip_task_bodies pass over an already-stripped block recognizes this
# prefix and does not stack a second pointer.
TASK_POINTER_PREFIX = "<!-- beads: content synced to bd -- see `bd show "


def strip_task_bodies(text, stripped_ids):
    """D-01: turn each `auto`/`tracer` task block whose `<beads-id>` is in
    stripped_ids into a pointer -- its opening tag, `<name>`, `<beads-id>`
    and `<files>` survive byte-identical; every content element
    (`read_first` through `done`) is removed and replaced by one
    fixed-shape pointer comment naming the beads id. Every other task type
    -- every `checkpoint:*` variant, and a block with no `type` attribute at
    all -- is left byte-identical (D-03): an unrecognized type also fails
    toward keeping content, never toward deleting it.

    Only a task whose id is in stripped_ids is touched, so a re-sync over
    an already-synced plan (whose ids are NOT in this run's stripped_ids)
    strips nothing (D-07 forward-only). Replacements are spliced in
    reverse match order over the original `text`'s offsets -- the same
    technique rewrite_plan already uses -- so no earlier offset is
    invalidated mid-pass (T-16-12).
    """
    matches = list(TASK_RE.finditer(text))
    for m in reversed(matches):
        block = m.group(0)
        type_m = TASK_TYPE_RE.search(block)
        task_type = type_m.group(1).strip() if type_m else None
        if task_type not in ("auto", "tracer"):
            continue
        id_m = BEADS_ID_RE.search(block)
        issue_id = id_m.group(1).strip() if id_m else None
        if not issue_id or issue_id not in stripped_ids:
            continue
        new_block = block
        for element_re in _STRIP_ELEMENT_RES:
            new_block = element_re.sub("", new_block)
        # Collapse the blank lines those removals leave -- idempotency
        # depends on a second pass over already-stripped text not
        # accumulating more blank lines than the first pass produced.
        new_block = re.sub(r"[ \t]*\n(?:[ \t]*\n)+", "\n", new_block)
        if TASK_POINTER_PREFIX not in new_block:
            pointer = f"  {TASK_POINTER_PREFIX}{issue_id}` -->\n"
            close_idx = new_block.index("</task>")
            new_block = new_block[:close_idx] + pointer + new_block[close_idx:]
        text = text[: m.start()] + new_block + text[m.end() :]
    return text


def _resolve_completed_task_ids(phase_dir):
    """Return the union of every <beads-id> across every plan in phase_dir
    whose SUMMARY.md exists (B9/D-04): the completed-task-id side of the
    divergence comparison. An empty phase_dir (no plans) returns an empty
    set."""
    completed_ids = set()
    for plan_id in discover_plan_files(phase_dir):
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
    """
    ids = set()
    rejected = 0
    for plan_id, plan_path in discover_plan_files(phase_dir).items():
        summary_path = plan_path.with_name(f"{plan_id}-SUMMARY.md")
        if not summary_path.exists():
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


def find_completed_task_ids(phase_dir, plan_id):
    """Return (task_ids, skipped_count) for one plan in a wave.

    Completion is plan-granular: a plan whose SUMMARY.md exists has finished
    every one of its tasks (gsd-core's own completion marker -- see
    wave_granularity_fact); a plan with no SUMMARY.md yet contributes
    nothing. Within a completed plan, a task with no <beads-id> (never
    synced, e.g. a checkpoint task) is counted skipped rather than raised.
    """
    plan_path = discover_plan_files(phase_dir).get(plan_id)
    if plan_path is None:
        return [], 0
    summary_path = plan_path.with_name(f"{plan_id}-SUMMARY.md")
    if not summary_path.exists():
        return [], 0
    _, _, tasks = parse_plan(plan_path)
    ids = []
    skipped = 0
    for task in tasks:
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
        ]
    )
    if result.returncode != 0:
        return list(ids)  # fail-open: status unconfirmed, attempt the close anyway
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return list(ids)
    open_ids = {r["id"] for r in rows}
    return [i for i in ids if i in open_ids]


def close_wave(phase_dir_arg, plan_ids):
    if not bd_available():
        print(NOTICE)
        try:
            project_root = find_project_root(Path(phase_dir_arg).resolve())
        except ValueError:
            project_root = None
        if project_root is not None:
            append_state_blocker(
                confined(project_root, ".planning", "STATE.md"),
                "bd unavailable -- beads-status close-wave skipped (B6/D-08)",
            )
        return 0

    phase_dir = Path(phase_dir_arg).resolve()

    all_ids = []
    skipped_total = 0
    plan_counts = []
    for plan_id in plan_ids:
        ids, skipped = find_completed_task_ids(phase_dir, plan_id)
        all_ids.extend(ids)
        skipped_total += skipped
        plan_counts.append((plan_id, len(ids)))

    # De-duplicate while preserving order, in case the same task id is
    # somehow named twice across the wave's plans.
    unique_ids = list(dict.fromkeys(all_ids))
    to_close = filter_open_ids(unique_ids)

    if to_close:
        reason = f"wave complete: {', '.join(plan_ids)}"
        result = run_bd(["bd", "close", *to_close, "--reason", reason])
        if result.returncode != 0:
            print(f"close-wave: bd close failed: {result.stderr.strip()}")

    per_plan = ", ".join(f"{pid}:{n}" for pid, n in plan_counts)
    print(
        f"Closed {len(to_close)} issue(s) across {len(plan_ids)} plan(s) ({per_plan}); "
        f"skipped {skipped_total} task(s) with no beads-id"
    )
    return 0


def reconcile_stale_closed(phase_dir_arg):
    """Phase-wide, idempotent backstop for D-08: close every task-complete
    (SUMMARY.md exists) issue that is still open in bd, across every plan in
    phase_dir -- not just the plan ids one wave's close-wave dispatch was
    given. A repeat call over an already-reconciled phase issues zero `bd
    close` calls, because filter_open_ids re-queries bd's live status before
    closing (B5)."""
    if not bd_available():
        print(NOTICE)
        try:
            project_root = find_project_root(Path(phase_dir_arg).resolve())
        except ValueError:
            project_root = None
        if project_root is not None:
            append_state_blocker(
                confined(project_root, ".planning", "STATE.md"),
                "bd unavailable -- beads-status reconcile-stale-closed skipped (B6/D-08)",
            )
        return 0

    phase_dir = Path(phase_dir_arg).resolve()

    plan_ids = discover_plan_files(phase_dir)
    skipped_total = 0
    for plan_id in plan_ids:
        _, skipped = find_completed_task_ids(phase_dir, plan_id)
        skipped_total += skipped

    completed_ids = sorted(_resolve_completed_task_ids(phase_dir))
    to_close = filter_open_ids(completed_ids)

    if to_close:
        reason = f"phase-wide reconciliation: {phase_dir.name}"
        result = run_bd(["bd", "close", *to_close, "--reason", reason])
        if result.returncode != 0:
            print(f"reconcile-stale-closed: bd close failed: {result.stderr.strip()}")

    # 260820-j6g (bd gsd-beads-72u): a second, separately-reasoned close call
    # for standalone issues named only via `resolves_issues:` markers -- a
    # sibling candidate set, never merged into the call above, so a
    # `--reason` (which is per-call) keeps the two closure paths
    # distinguishable in bd's audit trail. `.beads/` is untracked, so that
    # trail is the only forensic handle on a wrong close.
    marked_ids, rejected = _resolve_marked_issue_ids(phase_dir)
    marked_ids -= set(completed_ids)
    marked_to_close = filter_open_ids(sorted(marked_ids))

    if marked_to_close:
        marker_reason = f"resolves_issues marker: {phase_dir.name}"
        marker_result = run_bd(["bd", "close", *marked_to_close, "--reason", marker_reason])
        if marker_result.returncode != 0:
            print(f"reconcile-stale-closed: bd close failed: {marker_result.stderr.strip()}")

    print(
        f"Closed {len(to_close)} issue(s) across {len(plan_ids)} plan(s) in {phase_dir.name}; "
        f"skipped {skipped_total} task(s) with no beads-id; "
        f"closed {len(marked_to_close)} marker issue(s), rejected {rejected}"
    )
    return 0


def create_issues(plan_arg, allow_strip=True):
    """`allow_strip=False` keeps every `<task>` body in PLAN.md even when the
    read-path patch is present (gh-2). `strip_task_bodies` is a deliberate,
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

    Either way, `check_execute_plan_patch() == 0` below is the last-line-of-
    defence re-gate: config and this flag can only ever subtract permission
    from a run whose patch is missing, never add it back.
    """
    plan_path = Path(plan_arg).resolve()
    project_root = find_project_root(plan_path.parent)
    roadmap_path = confined(project_root, ".planning", "ROADMAP.md")

    text, frontmatter, tasks = parse_plan(plan_path)
    objective_m = OBJECTIVE_RE.search(text)
    objective = objective_m.group(1).strip() if objective_m else ""

    for task in tasks:
        if task["beads_id"] and not SAFE_BD_ID_RE.fullmatch(task["beads_id"]):
            print(
                f"native tracker identity preflight failed for task {task['name']!r}: "
                f"unsafe beads-id {task['beads_id']!r}",
                file=sys.stderr,
            )
            return 1
        if task["type"] not in ("auto", "tracer"):
            continue
        tracker_ids = task["tracker_ids"]
        if len(task["tracker_id_candidates"]) != len(tracker_ids) or any(
            tracker_id != tracker_id.strip() for tracker_id in tracker_ids
        ):
            print(
                f"native tracker identity preflight failed for task {task['name']!r}: "
                "tracker-id attribute is not exact",
                file=sys.stderr,
            )
            return 1
        if len(tracker_ids) > 1:
            print(
                f"native tracker identity preflight failed for task {task['name']!r}: "
                "duplicate tracker-id attributes",
                file=sys.stderr,
            )
            return 1
        if not tracker_ids:
            continue
        if not task["beads_id"]:
            print(
                f"native tracker identity preflight failed for task {task['name']!r}: "
                "tracker-id has no authoritative beads-id",
                file=sys.stderr,
            )
            return 1
        expected = f"beads:{task['beads_id']}"
        if tracker_ids[0] != expected:
            print(
                f"native tracker identity preflight failed for task {task['name']!r}: "
                f"expected {expected!r}, found {tracker_ids[0]!r}",
                file=sys.stderr,
            )
            return 1

    if not bd_available():
        print(NOTICE)
        append_state_blocker(
            confined(project_root, ".planning", "STATE.md"),
            "bd unavailable -- beads-sync skipped (B6/D-08)",
        )
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
        epic_id, epic_created, stale_epic_id = resolve_epic(
            frontmatter, roadmap_path, phase_num, plan_path.parent, project_root, objective
        )
        if stale_epic_id is not None:
            print(
                f"divergence: stored beads_epic {stale_epic_id!r} not found in bd -- "
                "resolving to a replacement epic"
            )

        task_updates = []
        native_updates = []
        created_count = 0
        task_ids = []
        divergences = []
        for i, task in enumerate(tasks, start=1):
            issue_id, created, divergent = resolve_issue(task, epic_id, ordinal_prefix, i)
            if created:
                created_count += 1
                task_updates.append((task["name_end"], issue_id))
            if (
                not divergent
                and task["type"] in ("auto", "tracer")
                and not task["tracker_ids"]
            ):
                native_updates.append((task["tracker_insert"], issue_id))
            if divergent:
                divergences.append((task["name"], issue_id))
            task_ids.append(issue_id)
    except RuntimeError as exc:
        print(NOTICE)
        append_state_blocker(
            confined(project_root, ".planning", "STATE.md"),
            f"bd failing mid-sync -- beads-sync skipped (B6/D-08): {exc}",
        )
        return 0

    for name, missing_id in divergences:
        print(f"divergence: task {name!r} beads-id {missing_id} not found in bd")

    if task_updates or native_updates or epic_created:
        new_text = rewrite_plan(
            text, epic_id, epic_created, task_updates, native_updates
        )
        # D-01/D-05: strip content only for tasks whose issue was created in
        # THIS run (task_updates), and only when the read-path patch is
        # verifiably present -- verify the patch before trusting the strip,
        # never assume it (ROADMAP Cross-Cutting Constraint).
        newly_created_ids = {issue_id for _, issue_id in task_updates}
        if newly_created_ids and not allow_strip:
            print(
                "beads-sync: hook-driven dispatch -- leaving task content in PLAN.md "
                "(gh-2: an unattended dispatch never performs the authoritative strip)"
            )
        elif newly_created_ids:
            if check_execute_plan_patch() == 0:
                new_text = strip_task_bodies(new_text, newly_created_ids)
            else:
                print(
                    "beads-sync: execute-plan.md bd-task-read patch not detected -- "
                    "leaving task content in PLAN.md (D-05: verify the patch before "
                    "trusting the strip)"
                )
        with plan_path.open("w", encoding="utf-8", newline="") as plan_file:
            plan_file.write(new_text)

    orphan_result = run_bd(["bd", "list", "--parent", epic_id, "--all", "--json"])
    if orphan_result.returncode == 0:
        try:
            children = json.loads(orphan_result.stdout)
        except json.JSONDecodeError:
            children = []
        current_ids = {tid for tid in task_ids if tid} | collect_epic_task_ids(
            plan_path.parent, epic_id
        )
        for orphan_id in find_orphans(children, current_ids):
            run_bd(
                ["bd", "close", orphan_id, "--reason", "no longer maps to a plan task"]
            )

    prereq_last_ids = []
    for prereq_id in parse_depends_on(frontmatter):
        last_id = resolve_prereq_last_task_id(plan_path.parent, prereq_id)
        if last_id is None:
            print(f"prerequisite plan {prereq_id} not yet synced -- skipping cross-plan edge")
        else:
            prereq_last_ids.append(last_id)
    apply_dependency_edges(derive_dependency_edges(task_ids, prereq_last_ids))

    print(f"Synced {created_count} issue(s) -> epic {epic_id}")
    return 0


def _escape_table_cell(text):
    """Escape `|` and strip `\r`/`\n` from text before it enters a markdown
    table cell (T-02-03, matches gsd-core's own ship.md pattern) -- issue
    title/status text originates from a different principal (whoever filed
    it in bd) than the process rendering this generated artifact."""
    return text.replace("|", "\\|").replace("\r", "").replace("\n", " ")


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


PATH_TOKEN_RE = re.compile(r"[\w\-./]+\.\w{1,4}")


def extract_phase_mentions(roadmap_path, phase_num, context_path):
    """Return deduplicated path-like tokens (a `/`-containing, dotted-
    extension substring) mentioned in the phase's ROADMAP.md section (from
    its header to the next `### Phase` heading) plus context_path's full
    text when it exists -- the only file-scope signal available at plan:pre
    time for the phase being planned, since no PLAN.md exists yet for it
    (D-01 revised).
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

    seen = []
    for token in PATH_TOKEN_RE.findall(section_text) + PATH_TOKEN_RE.findall(context_text):
        if token not in seen:
            seen.append(token)
    return seen


def scope_match(issue_id, files_index, phase_mentions):
    """Pure technique-1 check: return "files" when issue_id's reverse-
    looked-up file list shares a substring with any phase_mentions token
    (either direction); return None when issue_id has no reverse-lookup
    entry at all (caller falls back to technique 2) or its files simply
    don't overlap."""
    if issue_id not in files_index:
        return None
    for issue_file in files_index[issue_id]:
        for mention in phase_mentions:
            if issue_file in mention or mention in issue_file:
                return "files"
    return None


def desc_contains_match(issue_id, phase_mentions):
    """Technique-2 fallback for an issue absent from files_index: one
    `bd list --id <issue_id> --desc-contains <token> --json -n 0` per
    phase_mentions token, short-circuit on first hit."""
    for token in phase_mentions:
        result = run_bd(["bd", "list", "--id", issue_id, "--desc-contains", token, "--json", "-n", "0"])
        if result.returncode != 0:
            continue
        try:
            rows = json.loads(result.stdout)
        except json.JSONDecodeError:
            continue
        if rows:
            return "description"
    return None


def beads_recall(phase_dir_arg):
    """B7/plan:pre: scan every open, non-epic bd issue and write
    `{phase_dir}/{padded_phase}-BEADS-RECALL.md`, always, even when zero
    issues are open (D-04) -- same B6/D-08 fail-open shape as create_issues/
    close_wave, never a new fail-open variant."""
    if not bd_available():
        print(NOTICE)
        try:
            project_root = find_project_root(Path(phase_dir_arg).resolve())
        except ValueError:
            project_root = None
        if project_root is not None:
            append_state_blocker(
                confined(project_root, ".planning", "STATE.md"),
                "bd unavailable -- beads-recall skipped (B6/D-08)",
            )
        return 0

    phase_dir = Path(phase_dir_arg).resolve()
    project_root = find_project_root(phase_dir)
    padded_phase = phase_dir.name.split("-", 1)[0]

    result = run_bd(_beads_recall_argv())
    issues = []
    if result.returncode == 0:
        try:
            issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            issues = []

    # Two-technique scope match (D-01 revised): reverse <beads-id> lookup
    # against every phase's PLAN.md <files> element first, falling back to a
    # bd list --desc-contains substring match for an issue with no matching
    # <beads-id> anywhere. Neither technique matching is not an error -- the
    # issue simply stays Unscoped (D-02), never dropped.
    roadmap_path = confined(project_root, ".planning", "ROADMAP.md")
    context_path = phase_dir / f"{padded_phase}-CONTEXT.md"
    try:
        phase_mentions = extract_phase_mentions(roadmap_path, padded_phase, context_path)
    except (OSError, ValueError):
        phase_mentions = []
    files_index = collect_all_task_files(project_root)

    matched = []
    unscoped = []
    for issue in issues:
        issue_id = issue.get("id", "")
        via = scope_match(issue_id, files_index, phase_mentions)
        if via is None:
            via = desc_contains_match(issue_id, phase_mentions)
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
        "---\n\n"
    )
    out_text = frontmatter + f"# Beads Recall: Phase {phase_dir.name}\n\n" + body

    out_path = phase_dir / f"{padded_phase}-BEADS-RECALL.md"
    out_path.write_text(out_text, encoding="utf-8")

    print(
        f"BEADS-RECALL.md written: {len(matched)} matched, {len(unscoped)} unscoped "
        f"({len(issues)} open issue(s) total)"
    )
    return 0


def resolve_phase_epic(phase_dir):
    """Return the `beads_epic` frontmatter value carried by the first
    `NN-NN-PLAN.md` discovered in phase_dir that has one, or None when no
    plan in this phase has ever synced (D-05: every plan in a phase shares
    the same epic, so the first match is sufficient)."""
    for plan_path in discover_plan_files(phase_dir).values():
        try:
            _, frontmatter, _ = parse_plan(plan_path)
        except (OSError, UnicodeDecodeError):
            continue
        m = BEADS_EPIC_RE.search(frontmatter)
        if m:
            return m.group(1)
    return None


def _beads_md_argv(epic_id):
    """D-08/Pitfall 3: the epic-children query BEADS.md's table is built
    from, `-n 0` explicit to avoid the default 50-row truncation."""
    return ["bd", "list", "--parent", epic_id, "--all", "--json", "-n", "0"]


def _resolve_task_ordinal_map(phase_dir):
    """Return {beads_id: ordinal_prefix} across every plan in phase_dir, so
    each BEADS.md row can name the plan task that owns its issue."""
    mapping = {}
    for ordinal, plan_path in discover_plan_files(phase_dir).items():
        try:
            _, _, tasks = parse_plan(plan_path)
        except (OSError, UnicodeDecodeError):
            continue
        for task in tasks:
            if task["beads_id"]:
                mapping[task["beads_id"]] = ordinal
    return mapping


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


def regenerate_beads_md(phase_dir_arg):
    """B11/execute:wave:pre (read-only) and execute:wave:post (unchanged):
    always fully overwrite `{phase_dir}/{padded_phase}-BEADS.md` from a
    fresh `bd list --parent <epic>` query -- never read the existing file's
    body to merge or preserve a prior hand edit."""
    if not bd_available():
        print(NOTICE)
        try:
            project_root = find_project_root(Path(phase_dir_arg).resolve())
        except ValueError:
            project_root = None
        if project_root is not None:
            append_state_blocker(
                confined(project_root, ".planning", "STATE.md"),
                "bd unavailable -- beads-status regenerate-beads-md skipped (B6/D-08)",
            )
        return 0

    phase_dir = Path(phase_dir_arg).resolve()
    padded_phase = phase_dir.name.split("-", 1)[0]

    epic_id = resolve_phase_epic(phase_dir)
    if epic_id is None:
        print("no epic yet -- nothing to regenerate")
        return 0

    argv = _beads_md_argv(epic_id)
    result = run_bd(argv)
    rows = []
    if result.returncode == 0:
        try:
            rows = json.loads(result.stdout)
        except json.JSONDecodeError:
            rows = []

    closed_count = sum(1 for r in rows if r.get("status") == "closed")
    open_count = len(rows) - closed_count
    # blocking_open IS open_count, no separate filtered variable -- D-01/D-02:
    # every open issue under the epic counts, full stop, no priority/type filter.
    blocking_open = open_count

    ordinal_map = _resolve_task_ordinal_map(phase_dir)
    completed_ids = _resolve_completed_task_ids(phase_dir)
    diverged_count, task_status_by_id = _compute_diverged(rows, ordinal_map, completed_ids)
    table = _render_beads_md_table(rows, ordinal_map, task_status_by_id)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
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

    out_path = phase_dir / f"{padded_phase}-BEADS.md"
    out_path.write_text(frontmatter + body, encoding="utf-8")

    print(f"BEADS.md regenerated: {open_count} open, {closed_count} closed (epic {epic_id})")
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
        print(NOTICE)
        try:
            project_root = find_project_root(Path(phase_dir_arg).resolve())
        except ValueError:
            project_root = None
        if project_root is not None:
            append_state_blocker(
                confined(project_root, ".planning", "STATE.md"),
                "bd unavailable -- beads-status on-demand skipped (B6/D-08)",
            )
        return 0

    phase_dir = Path(phase_dir_arg).resolve()

    epic_id = resolve_phase_epic(phase_dir)
    if epic_id is None:
        print("no epic yet -- nothing to show")
        return 0

    argv = _beads_md_argv(epic_id)
    result = run_bd(argv)
    rows = []
    if result.returncode == 0:
        try:
            rows = json.loads(result.stdout)
        except json.JSONDecodeError:
            rows = []

    ordinal_map = _resolve_task_ordinal_map(phase_dir)
    completed_ids = _resolve_completed_task_ids(phase_dir)
    _diverged_count, task_status_by_id = _compute_diverged(rows, ordinal_map, completed_ids)
    table = _render_beads_md_table(rows, ordinal_map, task_status_by_id)

    current_ids = collect_epic_task_ids(phase_dir, epic_id)
    bd_side_orphans = [(row, None) for row in rows if row.get("id") not in current_ids]

    task_side_orphans = []
    for plan_path in discover_plan_files(phase_dir).values():
        try:
            _, _, tasks = parse_plan(plan_path)
        except (OSError, UnicodeDecodeError):
            continue
        for task in tasks:
            if not task["beads_id"]:
                task_side_orphans.append((plan_path.name, task["name"]))

    lines = [table, "", "## Issues with no matching plan task", ""]
    if bd_side_orphans:
        lines.append(_render_issue_table(bd_side_orphans, include_matched_via=False))
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Plan tasks with no bd issue")
    lines.append("")
    if task_side_orphans:
        lines.extend(f"- {plan_name}: {task_name}" for plan_name, task_name in task_side_orphans)
    else:
        lines.append("None.")

    print("\n".join(lines))
    return 0


CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")


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
        cells = CELL_SPLIT_RE.split(line)
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        cells = [c.strip().replace("\\|", "|") for c in cells]
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
            _, _, tasks = parse_plan(plan_path)
        except (OSError, UnicodeDecodeError):
            continue
        for task in tasks:
            if task["beads_id"]:
                wanted_ids.append(task["beads_id"])

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
    text = beads_md_path.read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    if not fm_match:
        return {}
    return {
        m.group(1): m.group(2).strip()
        for m in BEADS_MD_FIELD_RE.finditer(fm_match.group(1))
    }


def _head_already_pushed(project_root):
    """True when HEAD has zero commits ahead of its upstream -- i.e. HEAD is
    already on the remote. Amending it would rewrite a commit origin already
    has, diverging local history with no fast-forward path (push_branch never
    force-pushes). This happens on a ship retry after a prior run already
    completed push_branch (e.g. a later step like `gh pr create` failed).
    Returns False (assume safe, preserves prior behavior) when no upstream is
    configured or either git call fails -- a targeted guard against this one
    known failure mode, not a general git-state validator."""
    try:
        upstream = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
        if upstream.returncode != 0:
            return False
        ahead = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
        if ahead.returncode != 0:
            return False
        return ahead.stdout.strip() == "0"
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
        project_root = find_project_root(phase_dir)
    except ValueError as exc:
        print(f"ship-override: {exc}")
        return 1

    trailer = (
        f"Beads-Override: ship_gate bypassed, "
        f"blocking_open={fields['blocking_open']}, diverged={fields['diverged']}"
    )
    if _head_already_pushed(project_root):
        print(
            "ship-override: HEAD has no unpushed commits (already on the remote) -- "
            "refusing to amend, that would diverge local history from origin and "
            "break the next push. This happens on a ship retry after a prior run "
            "already pushed. Record the override manually or re-run ship_override "
            "before the branch is pushed."
        )
        git_ok = False
    else:
        result = subprocess.run(
            ["git", "commit", "--amend", "--allow-empty", "--no-edit", "--trailer", trailer],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
        git_ok = result.returncode == 0
        if git_ok:
            print(f"ship-override: recorded {trailer}")
        else:
            print(f"ship-override: git commit --amend failed: {result.stderr.strip()}")

    if bd_available():
        comment_text = (
            f"ship_gate override: blocking_open={fields['blocking_open']}, "
            f"diverged={fields['diverged']}"
        )
        comment_result = run_bd(["bd", "comment", fields["epic"], comment_text])
        if comment_result.returncode != 0:
            print(f"ship-override: bd comment failed: {comment_result.stderr.strip()}")
    else:
        print("ship-override: bd unavailable -- comment mirror skipped (B6)")

    return 0 if git_ok else 1


def check_patch(target, path_override=None):
    """17-04 Task 3 (TRUTH-02): the one reader PATCH_CHECKS parameterizes,
    replacing check_shipmd_patch's and check_execute_plan_patch's identical
    bodies. Preserves the three-case return contract (not-found /
    could-not-read / marker present-or-missing), the `CLAUDE_CONFIG_DIR`
    idiom, and naming the exact path probed in every message (WR-03).
    Read-only. Total by construction (T-17-04-02): both checks run inside
    `lifecycle_dispatch`'s one `try/except` alongside `beads_recall`, so an
    unrecognized `target` fails open like an unreadable file rather than
    raising -- but names the unknown target so the two cases stay separable.
    """
    entry = PATCH_CHECKS.get(target)
    if entry is None:
        known = ", ".join(sorted(PATCH_CHECKS))
        print(f"unknown patch-check target '{target}' -- expected one of: {known}")
        return 1
    if path_override:
        path = Path(path_override)
    else:
        path = Path(
            os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))
        ).joinpath(*entry["default_path_parts"])
    if not path.exists():
        print(entry["not_found_msg"].format(filename=entry["filename"], path=path))
        return 1
    # WR-02/CR-02: degrade to "cannot verify" rather than raise -- an
    # uncaught exception here would abort create_issues before
    # plan_path.write_text runs (execute-plan target).
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(entry["could_not_read_msg"].format(filename=entry["filename"], path=path, exc=exc))
        return 1
    present = entry["marker"] in text
    fmt = entry["present_msg"] if present else entry["missing_msg"]
    # WR-01: stdout is deliberate here, not a convention to "fix" -- the
    # hook (hooks/lifecycle-dispatch.sh) promotes only stdout into
    # additionalContext, so a stderr line would silently vanish.
    print(fmt.format(filename=entry["filename"], path=path, version=entry["version"]))
    return 0 if present else 1


def check_shipmd_patch(ship_md_path_override=None):
    """Thin wrapper over check_patch (17-04 Task 3, D-08) -- retained under
    this exact name so the four existing test mocks and both in-file call
    sites (beads-status Step 2d, beads-recall Step 3.5) keep working
    unedited; D-08's CLI collapse is scoped to the public verb, not this
    Python name (ROADMAP Criterion 5)."""
    return check_patch("ship-md", ship_md_path_override)


def check_execute_plan_patch(execute_plan_path_override=None):
    """Thin wrapper over check_patch (17-04 Task 3, D-08) -- retained under
    this exact name for the same reason as check_shipmd_patch above; also
    gates `strip_task_bodies` via `check_execute_plan_patch() == 0` in
    create_issues, which must keep working unedited."""
    return check_patch("execute-plan", execute_plan_path_override)


def check_native_step_dispatch(point, workflow_path_override=None):
    """D-05 diagnostic (17-02 Task 1): report whether the installed gsd-core
    workflow file now dispatches `kind == "step"` hooks natively at this
    lifecycle point -- gsd-core PR #3687 (merged to `next` 2026-08-19,
    unreleased as of the installed 1.11.0), which `lifecycle_dispatch` needs
    to know so it can stand down at `plan:post`/`verify:post` rather than
    double-dispatch alongside gsd-core's own native loop.

    Opposite polarity from check_shipmd_patch/check_execute_plan_patch just
    above: those ask "is our local patch still here" (missing is bad); this
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
    if not workflow_path.exists():
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

    anchor_literal = f"render-hooks {point} --raw"
    lines = text.splitlines()
    anchor_idx = next((i for i, line in enumerate(lines) if anchor_literal in line), None)
    if anchor_idx is None:
        print(
            f"native-step-dispatch probe ({point}): no '{anchor_literal}' anchor found in "
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
    # 17-04 Task 3 (D-08): one verb reaches both patch-check targets,
    # replacing the two prior single-target verbs and their per-target
    # `--*-path` flags. Hard break, no alias window (D-08 rated one-way;
    # every caller updated in this same commit).
    check_patch_p = sub.add_parser(
        "check-patch",
        help="Report whether a local GSD-CORE-PATCH.md patch is present at its target "
        "(ship-md or execute-plan)",
    )
    check_patch_p.add_argument("target", choices=sorted(PATCH_CHECKS))
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
    if args.command == "resolve-task-content":
        return resolve_task_content(args.issue_id)
    if args.command == "create-issues":
        # 17-02 Task 3 (D-06): the explicit CLI path's strip permission is
        # governed by beads.sync_mode -- the hook path (lifecycle_dispatch)
        # never reaches this branch and stays ungated by design (D-03).
        # Fail-open: an unresolvable project root falls back to the
        # shipped authoritative default rather than raising.
        try:
            sync_mode_root = find_project_root(Path(args.plan_path).resolve().parent)
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
    if args.command == "wave-status-block":
        return render_wave_status_block(args.phase_dir, args.plan_ids)
    if args.command == "ship-override":
        return ship_override(args.phase_dir)
    if args.command == "check-patch":
        return check_patch(args.target, args.path)
    if args.command == "lifecycle-dispatch":
        return lifecycle_dispatch(args.point)
    if args.command == "migrate-todos":
        project_root = find_project_root(Path.cwd())
        pending_dir = confined(project_root, ".planning", "todos", "pending")
        return migrate_todos(str(pending_dir))
    if args.command == "status":
        if args.phase_dir is not None:
            return render_status_mapping(args.phase_dir)
        project_root = find_project_root(Path.cwd())
        default_dir = _resolve_default_phase_dir(project_root)
        if default_dir is None:
            print("no phase directory given and no default could be resolved from STATE.md")
            return 1
        return render_status_mapping(str(default_dir))
    return 1


if __name__ == "__main__":
    sys.exit(main())
