# Phase 14: pr-workflow capability (dogfood) - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>

## Phase Boundary

A phase's real GitHub PR check status reaches the ship decision as visible, advisory
information, via a new `pr-workflow` gsd-core capability. Mirrors the shape and
degrade-cleanly discipline already proven by `beads` (`artifact-frontmatter-equals` gate) and
`markdown-linting` (Phase 13, same milestone).

Requirements: PRW-01, PRW-02, PRW-03, PRW-04 (see REQUIREMENTS.md). All four are already
precisely specified there, with concrete acceptance criteria in ROADMAP.md's Phase 14 Success
Criteria — this discussion clarifies HOW to implement them, not WHAT they are.

</domain>

<decisions>

## Implementation Decisions

### Check-status rollup (PRW-01)
- **D-01:** `gh pr checks` results roll up into the four-state `pr_status` value with
  precedence **failing > pending > passing**: any `FAILURE`/`ERROR` check anywhere → `failing`;
  else any `PENDING`/`IN_PROGRESS`/`QUEUED` check → `pending`; else all `SUCCESS` (including the
  case of zero checks configured on an otherwise-open PR) → `passing`. Matches GitHub's own
  required-check semantics and `gh pr checks`' own exit-code precedence. — **Reversibility:**
  reversible — rollup logic is a pure function inside the step script, not a stored contract.
- **Note for planner:** "zero checks configured" is `passing`, not `none` — `none` is reserved
  for "no open PR exists for this branch" (see PRW-03/D-02 below), keeping the two failure modes
  (no CI vs no PR) distinguishable in the frontmatter.

### PR lookup for this branch (PRW-01/PRW-03)
- **D-02 (Claude's discretion):** User deferred the exact `gh` invocation (`gh pr view --json`
  vs `gh pr list --head <branch>`) to the researcher/planner. Whichever is chosen must (a)
  resolve cleanly to "no open PR" as the `none` signal PRW-03 needs, without spamming or
  guessing, and (b) handle zero-or-one PR per branch as the common case — note in the plan if
  more than one PR can target a branch and how that's handled.

### PR.md artifact depth
- **D-03 (Claude's discretion):** User deferred count-only-vs-breakdown-table depth to the
  planner, driven by what the `ship:pre` advisory warning needs to say (PRW-02, Success
  Criterion 3: "visible warning naming the status"). At minimum the frontmatter must carry
  `pr_status`, matching MDL's `LINT-REPORT.md` "regenerated every step, never hand-edited"
  banner convention (mirrors B11/MDL-02 pattern).

### gh absence vs auth-failure notices (PRW-04)
- **D-04:** Two distinct, differently-worded notices — one for `gh` missing from `PATH`
  (`shutil.which("gh")` guard, install-focused message) and one for `gh` present but
  `gh auth status` failing (login-focused message) — so the user can tell which fix applies
  without reading a stack trace. Exact wording left to the executor. — **Reversibility:**
  reversible — message text only.

### Claude's Discretion
- Exact `gh` invocation for PR lookup (D-02).
- PR.md body depth beyond the mandatory `pr_status` frontmatter field (D-03).
- Exact wording of both PRW-04 notices (D-04) and the PRW-02 ship:pre advisory warning text.
- Whether the `execute:wave:post` step is a Python script (beads-sync/markdown-linting style)
  or another mechanism — must still produce `.planning/PR.md` with the `pr_status` frontmatter
  contract.

</decisions>

<canonical_refs>

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/REQUIREMENTS.md` §PR-WORKFLOW (PRW-01..04, PRW-05 deferred to v2) — full
  requirement text
- `.planning/ROADMAP.md` §Phase 14 — 5 success criteria (PR.md generation/regeneration,
  tri-state gate firing via a live `gsd_run check predicate` smoke test, advisory-not-blocking,
  no-open-PR single notice with no PR created, gh-absent/auth-failing each one notice)
- `.planning/PROJECT.md` §Key Decisions — `ship.md` generic gate-dispatch patch history
  (gsd-core#3554/#3559), the `beads` `ship:pre` gate live-verification precedent this phase must
  match; §Blockers/Concerns notes both Phase 13 and 14 gates are advisory-by-design, so a green
  ship is not evidence the gate works — only the live predicate smoke test is

### Precedent capabilities (read before designing capability.json)
- `.gsd/capabilities/beads/capability.json` — `artifact-frontmatter-equals` gate pattern
  (`ship:pre`, `onError: skip`), step-based generation of a regenerated-every-step artifact
  (`BEADS.md`)
- `.gsd/capabilities/markdown-linting/capability.json` — Phase 13's freshly-shipped sibling in
  this same milestone: same `artifact-frontmatter-equals`/`onError: skip` shape, same
  advisory-default posture, same B6-style fail-open notice pattern — closest analogue, more
  relevant than `mempalace` for this phase
- `.gsd/capabilities/mempalace/capability.json` — original degrade-cleanly shape reference

### Source skill (behavioral reference, not a dependency)
- `~/.agents/skills/pr-workflow/SKILL.md` — the interactive `pr-workflow` skill this capability
  is inspired by; PRW's Out-of-Scope list in REQUIREMENTS.md explicitly excludes its
  create/review-thread/auto-merge phases — only `gh pr checks`-style status reading is in scope
  here

### State / open risks
- `.planning/STATE.md` §Blockers/Concerns — Phase 15 pre-extraction check on gsd-core#3559's
  merge status; both Phase 13/14 gates are advisory-by-design (see above)

</canonical_refs>

<code_context>

## Existing Code Insights

### Reusable Assets
- `.gsd/capabilities/markdown-linting/scripts/lint.py` — directly analogous shape: a Python
  script invoked at a lifecycle point (`verify:post` there, `execute:wave:post` here) that
  shells out to an external tool, fail-opens on `shutil.which()` absence, and writes a
  frontmatter-bearing generated artifact
- `.gsd/capabilities/beads/` sync/step scripts — same generated-artifact pattern, `BEADS.md`

### Established Patterns
- Every capability's config lives under `<id>.*` (collision-checked at load) — this capability's
  namespace is `pr-workflow.*`
- Gates default `onError: skip`; PRW-02 is advisory by requirement, so it follows this default
- B6 fail-open pattern: guard on tool/auth availability, exactly one visible notice per failure
  case, no hang, no stale artifact presented as current — PRW-04 extends this to two distinct
  notice cases (absent vs unauthenticated)

### Integration Points
- `execute:wave:post` → generates/regenerates `.planning/PR.md`
- `ship:pre` → gate reads `PR.md`'s `pr_status` via `artifact-frontmatter-equals`, advisory
- `ship:post` → warn-only notice when no open PR exists for the branch, never auto-creates

</code_context>

<specifics>

## Specific Ideas

- Status rollup precedence (failing > pending > passing, zero-checks = passing) came from a
  direct GitHub required-check semantics analogy, not from the source skill (which doesn't
  define a rollup rule — it only shows `gh pr checks <pr-number> --watch`).

</specifics>

<deferred>

## Deferred Ideas

None raised beyond the roadmap's own v2 backlog (PRW-05, blocking gate — already tracked in
REQUIREMENTS.md).

### Reviewed Todos (not folded)

None — no pending todos matched this phase's scope.

</deferred>

---

*Phase: 14-pr-workflow-capability-dogfood*
*Context gathered: 2026-08-18*
