---
phase: 01-substrate
reviewed: 2026-08-15T02:38:35Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - .gsd/capabilities/beads/capability.json
  - .gsd/capabilities/beads/scripts/sync.py
  - .gsd/capabilities/beads/skills/beads-sync/SKILL.md
  - .gsd/capabilities/beads/skills/beads-status/SKILL.md
  - .gsd/capabilities/beads/tests/test_sync.py
  - .gsd/capabilities/beads/tests/fixtures/plan-single.md
  - .gsd/capabilities/beads/tests/fixtures/plan-synced.md
  - .gsd/capabilities/beads/tests/fixtures/plan-deps.md
  - .gsd/capabilities/beads/tests/fixtures/plan-orphan.md
  - .gsd/capabilities/beads/tests/fixtures/plan-wave-a.md
  - .gsd/capabilities/beads/tests/fixtures/plan-wave-b.md
  - .gitignore
findings:
  critical: 1
  warning: 6
  info: 2
  total: 9
status: issues_found
---

# Phase 01: Substrate — Code Review Report

**Reviewed:** 2026-08-15T02:38:35Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

`sync.py`'s `bd` invocations were traced call-site by call-site: every one of them
(`run_bd`, and every direct `subprocess.run`/`bd` argv construction in `resolve_epic`,
`resolve_issue`, `apply_dependency_edges`, `filter_open_ids`, `close_wave`) passes a typed Python
list to `subprocess.run(..., capture_output=True, text=True)` with `shell` left at its disabled
default. T-01-01 (command injection via PLAN.md task text) holds — confirmed by reading the actual
call sites, not the SUMMARY.md's description of them. No `eval`, no shell-string interpolation, no
hardcoded secrets anywhere in the reviewed files.

The one load-bearing correctness gap is that B6's own requirement text ("`bd` absent, **failing**
or locked degrades to a no-op with one visible notice") is only honored for the up-front
availability probe. Once that probe passes, a `bd create` failure mid-run (a fully realistic
"failing" scenario — locked db, disk full, permission error) raises an uncaught `RuntimeError` that
crashes the script with a Python traceback, skips the required `STATE.md` bullet entirely, and is
not exercised by any test (`TestFailOpen` only covers "bd absent from the start" and "the first
probe call fails," not "a later call fails after the probe succeeds"). B6 is marked complete in
`REQUIREMENTS.md`; this gap means that mark is not fully earned.

Everything else found is a quality/robustness gap, not a new injection or path-traversal vector: a
misleading success message on a failed batch close, a crash-on-malformed-frontmatter edge case, an
inconsistent path-root guard between the two branches of `create_issues`, and a `capability.json`
artifact contract (`produces: ["BEADS.md"]`) that no code path ever fulfills.

## Critical Issues

### CR-01: `bd create` failure after a successful availability probe crashes the script, contradicting B6's own "failing" clause

**File:** `.gsd/capabilities/beads/scripts/sync.py:214-250` (raise sites), invoked from `create_issues` at `:390-458`

**Issue:** `bd_available()` (lines 38-48) only runs one cheap `bd list --json -n 1` probe. Once
that probe returns 0, `create_issues` proceeds to call `resolve_epic` and `resolve_issue`, both of
which `raise RuntimeError(...)` on a failed `bd create`:

```python
result = run_bd(["bd", "create", title, "--type", "epic", "--silent"])
if result.returncode != 0:
    raise RuntimeError(f"bd create (epic) failed: {result.stderr.strip()}")
```

Neither `create_issues` nor `main()` catches this. A realistic "bd is failing" scenario (locked
database, disk full, transient permission error, a corrupted `.beads/` dir) that happens to occur
*after* the cheap list probe succeeds is not a hypothetical — it is exactly the class of failure
B6's requirement text calls out by name: "`bd` absent, **failing** or locked degrades to a no-op
with one visible notice... every gsd command completes normally." Instead:

- The process exits non-zero with an unhandled Python traceback (not the required one-line notice).
- `append_state_blocker` (the D-08-mandated `STATE.md` bullet) is never reached — this failure
  path writes nothing to `STATE.md`, unlike the up-front-absent path.
- `TestFailOpen` (`test_sync.py:800-843`) only exercises "bd missing from PATH" and "the very first
  probe call fails" (`_make_bd_side_effect`/`_always_fails` fail every call uniformly, which means
  the probe itself fails and the fail-open branch is taken before any `create` call is ever
  attempted) — there is no test where the probe succeeds and a later `bd create` fails, so this gap
  is undetected by the existing 26-test suite despite B6 being marked `Complete` in
  `REQUIREMENTS.md`.

**Fix:** Wrap the `bd create` calls (or the whole body of `create_issues`/`close_wave` past the
availability check) so a failed/exception-raising `bd` call degrades exactly like the up-front
absent case — print `NOTICE` (or an equivalently worded "bd failing mid-sync" line), append the
same `STATE.md` bullet, and exit 0, rather than propagating `RuntimeError`:

```python
try:
    epic_id, epic_created = resolve_epic(frontmatter, roadmap_path, phase_num)
    ...
except RuntimeError as exc:
    print(f"{NOTICE}: {exc}")
    append_state_blocker(confined(project_root, ".planning", "STATE.md"),
                          f"bd failing mid-sync -- beads-sync skipped ({exc})")
    return 0
```
Add a test that makes the probe (`bd list --json -n 1`) succeed but a subsequent `bd create`
fail, asserting exit code 0, the notice, and the `STATE.md` bullet — the current suite cannot
distinguish this from the already-covered "absent from the start" case.

## Warnings

### WR-01: `close_wave` reports a close as successful even when `bd close` itself failed

**File:** `.gsd/capabilities/beads/scripts/sync.py:376-386`

**Issue:**
```python
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
```
When `bd close` fails, the failure line is printed but the final summary line unconditionally
reports `len(to_close)` as closed regardless of whether the call actually succeeded — an operator
reading only the final line (the one `beads-status/SKILL.md` Step 3 instructs the agent to
surface) sees "Closed 4 issue(s)..." even though zero issues were actually closed.

**Fix:** Gate the count on the actual result:
```python
closed_count = len(to_close) if (not to_close or result.returncode == 0) else 0
print(f"Closed {closed_count} issue(s) across ...")
```

### WR-02: `rewrite_plan` can crash with `AttributeError` on a PLAN.md with no/malformed frontmatter

**File:** `.gsd/capabilities/beads/scripts/sync.py:269-286`

**Issue:**
```python
if epic_created:
    fm_match = FRONTMATTER_RE.match(text)
    insert_pos = fm_match.start(1)
```
`parse_plan` (line 102-103) already tolerates a missing frontmatter block (`frontmatter = fm_match.group(1) if fm_match else ""`), which lets `create_issues` proceed all the way to `resolve_epic`/`epic_created=True` on a plan file that has no `---\n...\n---\n` block at all. `rewrite_plan` then re-matches `FRONTMATTER_RE` against the same text with no `None` guard — `fm_match.start(1)` raises `AttributeError` on a `None` match, crashing the script (uncaught, same failure mode as CR-01) instead of degrading gracefully.

**Fix:**
```python
if epic_created:
    fm_match = FRONTMATTER_RE.match(text)
    if fm_match is None:
        raise ValueError("cannot insert beads_epic: PLAN.md has no frontmatter block")
    insert_pos = fm_match.start(1)
```
and catch that alongside the other fail-open paths (see CR-01's fix), so a malformed PLAN.md
degrades rather than crashes.

### WR-03: Inconsistent guarding of `find_project_root()` between `create_issues`'s two branches

**File:** `.gsd/capabilities/beads/scripts/sync.py:393-396` vs. `:404-405`

**Issue:** The bd-unavailable branch wraps `find_project_root` defensively:
```python
try:
    project_root = find_project_root(Path(plan_arg).resolve().parent)
except ValueError:
    project_root = None
```
but the bd-available branch, two lines later, calls the identical function unguarded:
```python
plan_path = Path(plan_arg).resolve()
project_root = find_project_root(plan_path.parent)
```
If `plan_arg` resolves outside any `.planning/`-containing ancestor (e.g. a stray absolute path,
or the caller passes a temp-file path during some future refactor), the bd-available path crashes
with an uncaught `ValueError` while the bd-unavailable path handles the identical failure
gracefully. The two branches should share one guarded helper rather than diverge.

**Fix:** Factor a single `_resolve_project_root_or_none(path)` helper and use it in both branches, or accept that a missing `.planning/` ancestor is itself a hard error and raise/report consistently in both places rather than only one.

### WR-04: `capability.json` declares `produces: ["BEADS.md"]` on both steps, but no code path ever creates a `BEADS.md` file

**File:** `.gsd/capabilities/beads/capability.json:47-49, 60-63`

**Issue:** Both `steps[]` entries (`plan:post` → `beads-sync`, `execute:wave:post` → `beads-status`)
declare `"produces": ["BEADS.md"]`. Neither `sync.py` (checked every write call site: `plan_path.write_text` and `append_state_blocker`'s `state_path.write_text` are the only two writes in the entire module) nor either `SKILL.md` ever creates a file named `BEADS.md` — the design (confirmed explicitly by `01-01-SUMMARY.md`'s own coverage note "no BEADS.md written" and `TestFailOpen`'s `self.assertFalse(beads_md.exists())`) deliberately writes back into `PLAN.md` and `STATE.md` instead. `01-RESEARCH.md` never mentions `BEADS.md` or `produces` at all, so this isn't a decision that traces to research — it looks like a copy-paste artifact from the illustrative `capability.json` skeleton. `produces`/`consumes` currently only drive step ordering (topological sort) in `gsd-core`'s `loop-resolver.cts`, not a post-hoc filesystem check, so this is inert today — but it is a standing lie in the manifest that will actively mislead the next engineer who wires a step that `consumes: ["BEADS.md"]`, and it corrupts the ordering contract itself (a step that legitimately does consume plan/epic-sync output has no accurate artifact name to depend on).

**Fix:** Either remove `"produces": ["BEADS.md"]` (replace with `[]`, since nothing is produced under that name) or, if a machine-readable sync-result artifact is actually wanted for Phase 2/3 visibility, write one and keep the declaration truthful.

### WR-05: `find_project_root`'s docstring overclaims coverage — the primary read/write target itself is never run through `confined()`

**File:** `.gsd/capabilities/beads/scripts/sync.py:69-74` (docstring claim) vs. `:404-405, 434` (actual `plan_path` usage) and `:360` (`phase_dir` usage in `close_wave`)

**Issue:** `find_project_root`'s docstring states: "Guards T-01-02: every path this script reads or writes is confined to this resolved root, never derived unchecked from artifact text." In practice, `confined()` (lines 85-92) is applied only to `roadmap_path` and the `STATE.md` path — both built from fixed literal path segments. The actual primary read/write target, `plan_path` (`Path(plan_arg).resolve()` at line 404, written at line 434), and `close_wave`'s `phase_dir` (`Path(phase_dir_arg).resolve()` at line 360, iterated in `discover_plan_files`), are used directly with no confinement check against `project_root` at all. This does not reopen the specific threat T-01-02 describes (a malicious `phase`/`plan` *frontmatter field inside PLAN.md* used to build a path) — that threat is correctly closed, since no path is ever built by concatenating frontmatter text. But the docstring's claim of "every path" is inaccurate: the actual write target is trusted implicitly (assumed to come from `gsd-core`'s own hook dispatch via `$ARGUMENTS`), with no assertion that it resolves under the discovered project root before `sync.py` writes to it.

**Fix:** Either narrow the docstring's claim to match reality ("every *derived* path... plan_path itself is trusted CLI input, not confined"), or add a real check — `confined(find_project_root(plan_path.parent), *plan_path.relative_to(project_root).parts)` — before the `write_text` call, so a future caller that passes an unexpected `plan_arg` can't write outside the project tree.

### WR-06: A divergent (stale-identity) task's unresolved `<beads-id>` still gets used as a dependency-edge endpoint, and the resulting `bd dep add` failure is reported with no link back to the divergence

**File:** `.gsd/capabilities/beads/scripts/sync.py:239-243` (`resolve_issue` divergent return), `:420-427` (`task_ids.append(issue_id)`), `:179-201` (`derive_dependency_edges`/`apply_dependency_edges`)

**Issue:** `resolve_issue` returns `task["beads_id"]` — the id `bd show` just confirmed does *not*
resolve — as the `issue_id` for a divergent task (line 242: `return task["beads_id"], False, True`). That value is unconditionally appended to `task_ids` (line 427) and later fed into `derive_dependency_edges`, so a divergent task's neighbors get wired to a `bd dep add <x> --depends-on <stale-id>` call that is certain to fail (the id doesn't exist in `bd`). `apply_dependency_edges` handles this failure only as a generic print (`"dependency edge failed: ... {result.stderr.strip()}"`, lines 198-201) with no cross-reference to the `"divergence: task ... beads-id ... not found in bd"` line already printed for the same task a few lines earlier (line 430). The net effect: the intra-plan dependency chain silently breaks at the divergent task (the task after it loses its intended blocker), and an operator scanning stdout sees two seemingly-unrelated error lines instead of one clear "this task's identity is broken, dependency edges around it were skipped" message.

**Fix:** Exclude a divergent task's id from `derive_dependency_edges`'s input (pass `None` in its slot, or filter before calling), and print one combined diagnostic instead of two disconnected ones.

## Info

### IN-01: No validation that `plan_arg`'s filename matches the `NN-NN-PLAN.md` convention before deriving a "phase number"

**File:** `.gsd/capabilities/beads/scripts/sync.py:207 (int(phase_num))`, `:410-412`

**Issue:** `ordinal_prefix = "-".join(plan_filename_stem.split("-")[:2])` and `phase_num = ordinal_prefix.split("-")[0]` assume `plan_path.stem` starts with two `-`-separated numeric tokens. If `sync.py create-issues` is ever invoked with a path that doesn't follow that convention (e.g. a stray file, or a future caller change), `phase_num` can be non-numeric, and `int(phase_num)` at line 207 raises an unhandled `ValueError` — a raw traceback rather than a clean, actionable error message. Low likelihood under normal `beads-sync` dispatch (the SKILL.md always passes a real `PLAN.md` path), but there's no guard at the entry point.

**Fix:** Validate `plan_filename_stem` against `PLAN_FILE_RE`-equivalent shape at the top of `create_issues` and raise/report a clear message ("`<path>` does not look like a NN-NN-PLAN.md file") rather than letting a downstream `int()` conversion fail opaquely.

### IN-02: `TASK_RE`'s naive `[^>]*` attribute matcher breaks on a literal `>` inside an attribute value

**File:** `.gsd/capabilities/beads/scripts/sync.py:23`

**Issue:** `TASK_RE = re.compile(r"<task\b[^>]*>.*?</task>", re.DOTALL)` scans for the end of the opening `<task ...>` tag using `[^>]*`, i.e. "anything but `>`." A `<task type="a>b">` (an attribute value containing a literal `>`) would end the match at the first `>` inside the attribute rather than the tag's real close, corrupting the parsed block boundary. Low likelihood given the current controlled `type="auto"`/`type="checkpoint:*"` vocabulary, but the parser has no defense against it, unlike a real XML/HTML parser.

**Fix:** Not urgent given the closed attribute vocabulary today; if `<task>` attributes ever grow richer values, switch to `xml.etree.ElementTree` or a quote-aware regex (`(?:[^">]|"[^"]*")*`) instead of `[^>]*`.

---

_Reviewed: 2026-08-15T02:38:35Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
