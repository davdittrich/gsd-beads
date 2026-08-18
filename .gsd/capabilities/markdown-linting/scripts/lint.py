#!/usr/bin/env python3
"""markdown-linting: wrap rumdl (PATH, else uvx) to measure this repo's
markdown against a curated MD0XX ruleset and write a gate-readable
violation-count report.

stdlib-only (N5: no dependency beyond the `rumdl`/`uvx` binaries and the
Python 3 standard library). Every rumdl/uvx invocation is an argv list
passed to `subprocess.run` with shell execution left at its (disabled)
default -- no rumdl command is ever assembled as a shell string (T-13-01,
mirrors beads/scripts/sync.py's T-01-01 discipline).
"""
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# D-02: single source of truth for what this capability lints. Every
# caller (count, verify-post, fix) resolves its default targets from this
# constant -- never a hand-typed path list.
LINT_TARGETS = (".planning", "README.md", "CLAUDE.md")

CONFIG_REL_PARTS = (".gsd", "capabilities", "markdown-linting", "config", ".rumdl.toml")


def find_project_root(start):
    """Walk up from `start` to the nearest ancestor containing `.planning/`.

    Guards T-13-02: every path this script reads or writes is confined to
    this resolved root, never derived unchecked from artifact text. Copied
    verbatim from beads/scripts/sync.py -- the two capabilities are
    independent and must not import across capability boundaries.
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
    """Join parts onto root and reject any resolved escape (T-13-02)."""
    candidate = root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError(f"path escapes project root: {candidate} not under {root}")
    return candidate


def resolve_rumdl_invocation():
    """D-04's two-tier chain: PATH first, then uvx, else None. Tool-absent
    fail-open handling (never raising here) is plan 02 scope -- a None
    return may propagate as a raise in this task's callers."""
    if shutil.which("rumdl"):
        return ["rumdl"]
    if shutil.which("uvx"):
        return ["uvx", "rumdl"]
    return None


def count_violations(config_path, targets, rumdl_argv):
    """Run `rumdl check --config <config_path> --output-format json
    <targets>` and return the exact integer length of the emitted JSON
    array -- no text-summary parsing, no rounding (MDL-02 precision)."""
    argv = rumdl_argv + [
        "check",
        "--config", str(config_path),
        "--output-format", "json",
    ] + [str(t) for t in targets]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    if result.returncode == 2:
        raise RuntimeError(f"rumdl config/runtime error: {result.stderr}")
    return len(json.loads(result.stdout))


def verify_post(phase_dir_arg):
    """B11-style regenerate-every-run: always fully overwrite
    `{phase_dir}/{padded_phase}-LINT-REPORT.md`, never merging a prior
    hand edit."""
    phase_dir = Path(phase_dir_arg).resolve()
    project_root = find_project_root(phase_dir)
    padded_phase = phase_dir.name.split("-", 1)[0]

    config_path = confined(project_root, *CONFIG_REL_PARTS)
    targets = [confined(project_root, t) for t in LINT_TARGETS]
    rumdl_argv = resolve_rumdl_invocation()

    violation_count = count_violations(config_path, targets, rumdl_argv)
    argv = rumdl_argv + [
        "check",
        "--config", str(config_path),
        "--output-format", "json",
    ] + [str(t) for t in targets]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = (
        "---\n"
        f"phase: {phase_dir.name}\n"
        f"violation_count: {violation_count}\n"
        f"config: {config_path}\n"
        f'generated_from: "{" ".join(argv)}"\n'
        f"generated_at: {generated_at}\n"
        "---\n\n"
    )
    # D-03: count-only, no per-rule/per-file breakdown table. The banner
    # below has no literal precedent in BEADS.md (B11 is a principle name,
    # not file content) -- authored fresh here; see 13-RESEARCH.md Pitfall 3.
    body = (
        f"# LINT-REPORT.md: {phase_dir.name}\n\n"
        "> Regenerated every step. Do not hand-edit.\n"
    )

    out_path = phase_dir / f"{padded_phase}-LINT-REPORT.md"
    out_path.write_text(frontmatter + body, encoding="utf-8")

    print(f"LINT-REPORT.md regenerated: {violation_count} violation(s)")
    return 0


def fix(paths=None):
    """Allowlist-safe wrapper for `rumdl check --fix` (Pitfall 6: --fix
    lives on the check subcommand, not as a bare top-level flag). This
    machine's shell allowlist rejects a bare top-level `rumdl` command
    word and interpreter inline-code/heredoc-stdin forms -- routing the
    fixer through this script file is the invocation form that survives
    it. Sole caller is plan 03 Task 1."""
    project_root = find_project_root(Path.cwd())
    config_path = confined(project_root, *CONFIG_REL_PARTS)
    targets = [confined(project_root, t) for t in (paths or LINT_TARGETS)]
    rumdl_argv = resolve_rumdl_invocation()
    if rumdl_argv is None:
        raise RuntimeError("neither rumdl nor uvx is available on PATH")

    check_argv = rumdl_argv + [
        "check", "--fix",
        "--config", str(config_path),
    ] + [str(t) for t in targets]
    result = subprocess.run(check_argv, capture_output=True, text=True, timeout=60)
    print(result.stdout, end="")
    post_fix_count = count_violations(config_path, targets, rumdl_argv)
    print(f"post-fix violation count: {post_fix_count}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="lint.py")
    sub = parser.add_subparsers(dest="command", required=True)

    verify_p = sub.add_parser(
        "verify-post",
        help="Fully overwrite {phase_dir}/{padded_phase}-LINT-REPORT.md from a live rumdl run",
    )
    verify_p.add_argument("phase_dir")

    count_p = sub.add_parser(
        "count",
        help="Print the integer violation count to stdout (defaults to the D-02 target set)",
    )
    count_p.add_argument("paths", nargs="*")

    fix_p = sub.add_parser(
        "fix",
        help="Run rumdl check --fix over the D-02 target set (allowlist-safe wrapper)",
    )
    fix_p.add_argument("paths", nargs="*")

    args = parser.parse_args(argv)

    if args.command == "verify-post":
        return verify_post(args.phase_dir)
    if args.command == "count":
        project_root = find_project_root(Path.cwd())
        config_path = confined(project_root, *CONFIG_REL_PARTS)
        targets = [confined(project_root, t) for t in (args.paths or LINT_TARGETS)]
        rumdl_argv = resolve_rumdl_invocation()
        print(count_violations(config_path, targets, rumdl_argv))
        return 0
    if args.command == "fix":
        return fix(args.paths)
    return 1


if __name__ == "__main__":
    sys.exit(main())
