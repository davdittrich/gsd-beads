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
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BD_TIMEOUT = 15  # seconds; bounded timeout on every bd subprocess call
NOTICE = "bd unavailable -- sync skipped"

TASK_RE = re.compile(r"<task\b[^>]*>.*?</task>", re.DOTALL)
NAME_RE = re.compile(r"<name>(.*?)</name>", re.DOTALL)
BEADS_ID_RE = re.compile(r"<beads-id>(.*?)</beads-id>", re.DOTALL)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)
BEADS_EPIC_RE = re.compile(r"^beads_epic:\s*(\S+)\s*$", re.MULTILINE)
DEPENDS_ON_RE = re.compile(r"^depends_on:\s*\[(.*?)\]\s*$", re.MULTILINE)
PLAN_FILE_RE = re.compile(r"^(\d{2}-\d{2})-PLAN\.md$")


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
        tasks.append(
            {
                "name": name_m.group(1).strip() if name_m else "",
                "name_end": m.start() + (name_m.end() if name_m else 0),
                "beads_id": id_m.group(1).strip() if id_m else None,
            }
        )
    return text, frontmatter, tasks


def parse_depends_on(frontmatter):
    """Return the plan-level `depends_on` array as a list of bare plan-id
    strings, quotes and whitespace stripped. Absent or empty -> [].

    This is the sole cross-plan edge source (dependency_derivation_decision,
    D-04): the `wave` frontmatter key is deliberately never inspected here or
    anywhere edges are derived.
    """
    m = DEPENDS_ON_RE.search(frontmatter)
    if not m:
        return []
    inner = m.group(1).strip()
    if not inner:
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]


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


def resolve_epic(frontmatter, roadmap_path, phase_num):
    """Return (epic_id, created). Resolve-by-id first, create only on confirmed
    absence -- never by title (B4/B5 pattern applied to the epic level too)."""
    m = BEADS_EPIC_RE.search(frontmatter)
    if m:
        epic_id = m.group(1)
        check = run_bd(["bd", "show", epic_id, "--json"])
        if check.returncode == 0:
            return epic_id, False
        # stored epic id no longer resolves in bd -- fall through and create fresh
    title = get_phase_header(roadmap_path, phase_num)
    result = run_bd(["bd", "create", title, "--type", "epic", "--silent"])
    if result.returncode != 0:
        raise RuntimeError(f"bd create (epic) failed: {result.stderr.strip()}")
    return result.stdout.strip(), True


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

    epic_id, epic_created = resolve_epic(frontmatter, roadmap_path, phase_num)

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
        current_ids = {tid for tid in task_ids if tid}
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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sync.py")
    sub = parser.add_subparsers(dest="command", required=True)
    create_p = sub.add_parser(
        "create-issues", help="Sync a PLAN.md's tasks into bd issues under a phase epic"
    )
    create_p.add_argument("plan_path")
    args = parser.parse_args(argv)
    if args.command == "create-issues":
        return create_issues(args.plan_path)
    return 1


if __name__ == "__main__":
    sys.exit(main())
