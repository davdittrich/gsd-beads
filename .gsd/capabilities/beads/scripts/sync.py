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
FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
BEADS_EPIC_RE = re.compile(r"^beads_epic:\s*(\S+)\s*$", re.MULTILINE)
DEPENDS_ON_RE = re.compile(r"^depends_on:\s*\[(.*?)\]\s*$", re.MULTILINE)
# WR-04: the inline-bracket form above requires the value on the same line
# as the key. YAML also permits (and this fixture set previously had no
# coverage for) the block-list form:
#   depends_on:
#     - "01-01"
# parse_depends_on falls back to this regex when DEPENDS_ON_RE doesn't match.
DEPENDS_ON_BLOCK_RE = re.compile(r"^depends_on:\s*\n((?:^[ \t]*-[ \t]*.+\n?)+)", re.MULTILINE)
PLAN_FILE_RE = re.compile(r"^(\d{2}-\d{2})-PLAN\.md$")
# B12 migrate-todos: a pending todo's frontmatter (add-todo.md's schema --
# created/title/area/severity/files, block-list files:) plus its
# ## Problem/## Solution body. TITLE_RE allows spaces (title text), AREA_RE/
# SEVERITY_RE are single-token like BEADS_EPIC_RE; FILES_BLOCK_RE is
# DEPENDS_ON_BLOCK_RE's block-list shape scoped to the `files:` key.
TITLE_RE = re.compile(r"^title:\s*(.+)$", re.MULTILINE)
AREA_RE = re.compile(r"^area:\s*(\S+)\s*$", re.MULTILINE)
SEVERITY_RE = re.compile(r"^severity:\s*(\S+)\s*$", re.MULTILINE)
FILES_BLOCK_RE = re.compile(r"^files:\s*\n((?:^[ \t]*-[ \t]*.+\n?)+)", re.MULTILINE)
PROBLEM_RE = re.compile(r"^##\s*Problem\s*\n(.*?)(?=^##\s*Solution\s*$)", re.MULTILINE | re.DOTALL)
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
SHIP_MD_PATCH_MARKER = "<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->"
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
    text = Path(path).read_text(encoding="utf-8")
    fm_match = FRONTMATTER_RE.match(text)
    frontmatter = fm_match.group(1) if fm_match else ""
    tasks = []
    for m in TASK_RE.finditer(text):
        block = m.group(0)
        name_m = NAME_RE.search(block)
        id_m = BEADS_ID_RE.search(block)
        files_m = FILES_RE.search(block)
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

    problem_m = PROBLEM_RE.search(body)
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
    pattern = re.compile(rf"^###\s+(Phase\s+0*{int(phase_num)}\s*:.*)$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        raise ValueError(f"no ROADMAP.md header found for phase {phase_num}")
    return m.group(1).strip()


def read_epic_per(project_root):
    """B14/D-11: return the `beads.epic_per` value read fresh from
    `.planning/config.json` -- "phase" when the file is absent, malformed
    (`json.JSONDecodeError`), or carries no `beads.epic_per` key. This is
    `sync.py`'s first-ever direct `config.json` read (RESEARCH's Config
    Schema Mechanism, Pattern 3 option (a)) -- required because D-11 needs
    the value re-read at each epic-creation call site, not resolved once by
    the calling SKILL.md's config gate."""
    config_path = confined(project_root, ".planning", "config.json")
    if not config_path.exists():
        return "phase"
    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "phase"
    beads_cfg = cfg.get("beads", {}) if isinstance(cfg, dict) else {}
    return beads_cfg.get("epic_per", "phase") if isinstance(beads_cfg, dict) else "phase"


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

    result = run_bd(["bd", "create", title, "--type", "epic", "--silent"])
    if result.returncode != 0:
        raise RuntimeError(f"bd create (epic) failed: {result.stderr.strip()}")
    return result.stdout.strip()


def resolve_epic(frontmatter, roadmap_path, phase_num, phase_dir, project_root):
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
    result = run_bd(["bd", "create", title, "--type", "epic", "--silent"])
    if result.returncode != 0:
        raise RuntimeError(f"bd create (epic) failed: {result.stderr.strip()}")
    return result.stdout.strip(), True, stale_epic_id


def resolve_issue(task, epic_id, ordinal_prefix, task_index):
    """Return (issue_id, created, divergent). <beads-id> is the identity;
    only create when it is absent -- never resolve or dedup by title (B4).

    When a <beads-id> is present but bd cannot find it, that is stale-
    identity divergence (D-07): report it, never recreate a replacement,
    never clear the element -- a Phase 3 ship gate acts on the divergence.
    """
    if task["beads_id"]:
        check = run_bd(["bd", "show", task["beads_id"], "--json"])
        if check.returncode != 0:
            return task["beads_id"], False, True
        return task["beads_id"], False, False
    title = f"{ordinal_prefix}.{task_index} {task['name']}"
    result = run_bd(
        ["bd", "create", title, "--type", "task", "--parent", epic_id, "--silent"]
    )
    if result.returncode != 0:
        raise RuntimeError(f"bd create (task) failed: {result.stderr.strip()}")
    return result.stdout.strip(), True, False


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


def rewrite_plan(text, epic_id, epic_created, task_updates):
    """Insert beads_epic (if newly created) and per-task <beads-id> elements.

    task_updates: [(name_end_pos, issue_id), ...] for tasks that had no
    <beads-id> before this run. Insertions happen in descending position
    order first so earlier offsets in `text` stay valid, then the
    frontmatter insertion (always at the front of the file) happens last.
    """
    for name_end_pos, issue_id in sorted(
        task_updates, key=lambda t: t[0], reverse=True
    ):
        insertion = f"\n  <beads-id>{issue_id}</beads-id>"
        text = text[:name_end_pos] + insertion + text[name_end_pos:]
    if epic_created:
        fm_match = FRONTMATTER_RE.match(text)
        insert_pos = fm_match.start(1)
        text = text[:insert_pos] + f"beads_epic: {epic_id}\n" + text[insert_pos:]
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


def create_issues(plan_arg):
    if not bd_available():
        print(NOTICE)
        try:
            project_root = find_project_root(Path(plan_arg).resolve().parent)
        except ValueError:
            project_root = None
        if project_root is not None:
            append_state_blocker(
                confined(project_root, ".planning", "STATE.md"),
                "bd unavailable -- beads-sync skipped (B6/D-08)",
            )
        return 0

    plan_path = Path(plan_arg).resolve()
    project_root = find_project_root(plan_path.parent)
    roadmap_path = confined(project_root, ".planning", "ROADMAP.md")

    text, frontmatter, tasks = parse_plan(plan_path)

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
            frontmatter, roadmap_path, phase_num, plan_path.parent, project_root
        )
        if stale_epic_id is not None:
            print(
                f"divergence: stored beads_epic {stale_epic_id!r} not found in bd -- "
                "resolving to a replacement epic"
            )

        task_updates = []
        created_count = 0
        task_ids = []
        divergences = []
        for i, task in enumerate(tasks, start=1):
            issue_id, created, divergent = resolve_issue(task, epic_id, ordinal_prefix, i)
            if created:
                created_count += 1
                task_updates.append((task["name_end"], issue_id))
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

    if task_updates or epic_created:
        new_text = rewrite_plan(text, epic_id, epic_created, task_updates)
        plan_path.write_text(new_text, encoding="utf-8")

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
        rf"^###\s+Phase\s+0*{int(phase_num)}\s*:.*?(?=^###\s+Phase\s|\Z)",
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
    padded = m.group(1).strip().zfill(2)
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
        _, _, tasks = parse_plan(plan_path)
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


def check_shipmd_patch(ship_md_path_override=None):
    """D-05 gap-closure diagnostic (03-03 Task 2): report whether the local
    `ship.md` patch (GSD-CORE-PATCH.md) is present in the installed,
    machine-local `ship.md` -- a future gsd-core update or capability
    reinstall can silently overwrite that file and drop the patch with no
    error. Called from two independent points (CR-01): `beads-status`
    SKILL.md's Step 2d confirms the patch is still intact immediately before
    a ship attempt (`ship:pre`), but that call site is itself only reachable
    through the dispatch loop the patch installs -- if the patch is lost,
    Step 2d never runs either. `beads-recall` SKILL.md's Step 3.5 is the
    call site that actually detects loss: it runs at `plan:pre`, dispatched
    by gsd-core's own native generic step-dispatch loop, independent of
    ship.md's patched dispatch loop entirely. Read-only: never edits
    ship.md itself.

    WR-03: only the Claude runtime home (`CLAUDE_CONFIG_DIR`, default
    `~/.claude`) is probed -- ship.md's own multi-runtime resolution
    (`CODEX_HOME`, `CURSOR_CONFIG_DIR`, etc.) is not replicated here, since
    GSD-CORE-PATCH.md's patch itself is scoped to the Claude runtime only.
    Every message below names the exact path checked so a report never
    reads as "no ship.md patch exists anywhere" when only one of several
    possible install locations was probed.
    """
    if ship_md_path_override:
        ship_md_path = Path(ship_md_path_override)
    else:
        ship_md_path = (
            Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
            / "gsd-core"
            / "workflows"
            / "ship.md"
        )
    if not ship_md_path.exists():
        print(
            f"ship.md not found at {ship_md_path} -- cannot verify the local ship:pre dispatch "
            "patch (only this runtime home was probed; other runtime homes such as CODEX_HOME "
            "or CURSOR_CONFIG_DIR were not checked)"
        )
        return 1
    text = ship_md_path.read_text(encoding="utf-8")
    if SHIP_MD_PATCH_MARKER in text:
        print(f"ship.md ship:pre patch: present (v1) at {ship_md_path}")
        return 0
    print(
        f"⚠ ship.md's ship:pre generic gate/step dispatch patch (beads) is missing at "
        f"{ship_md_path} -- the two ship:pre gates and the ship_override step will not fire. "
        "Reapply: see .gsd/capabilities/beads/GSD-CORE-PATCH.md"
    )
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sync.py")
    sub = parser.add_subparsers(dest="command", required=True)
    create_p = sub.add_parser(
        "create-issues", help="Sync a PLAN.md's tasks into bd issues under a phase epic"
    )
    create_p.add_argument("plan_path")
    close_p = sub.add_parser(
        "close-wave",
        help="Batch-close every completed task's issue across every plan in a wave",
    )
    close_p.add_argument("phase_dir")
    close_p.add_argument("plan_ids", nargs="+")
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
    check_shipmd_patch_p = sub.add_parser(
        "check-shipmd-patch",
        help="Report whether the local ship.md ship:pre dispatch patch (GSD-CORE-PATCH.md) is present",
    )
    check_shipmd_patch_p.add_argument("--ship-md-path", default=None)
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
    if args.command == "create-issues":
        return create_issues(args.plan_path)
    if args.command == "close-wave":
        return close_wave(args.phase_dir, args.plan_ids)
    if args.command == "beads-recall":
        return beads_recall(args.phase_dir)
    if args.command == "regenerate-beads-md":
        return regenerate_beads_md(args.phase_dir)
    if args.command == "wave-status-block":
        return render_wave_status_block(args.phase_dir, args.plan_ids)
    if args.command == "ship-override":
        return ship_override(args.phase_dir)
    if args.command == "check-shipmd-patch":
        return check_shipmd_patch(args.ship_md_path)
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
