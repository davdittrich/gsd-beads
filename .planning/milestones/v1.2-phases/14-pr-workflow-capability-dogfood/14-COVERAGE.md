# 14-COVERAGE.md: `gh` / GitHub PR API coverage matrix

**Decided:** 2026-08-18 (planner, `plan:pre` api-coverage checkpoint)
**External service:** GitHub, reached exclusively through the `gh` CLI v2.97.0 (never the REST/GraphQL
API directly — see `14-RESEARCH.md` Architectural Responsibility Map).

Default is `INTEGRATE`. Every `OPT-OUT` carries a one-line reason; reasons marked *(canon)* are lifted
verbatim from `.planning/REQUIREMENTS.md`'s PR-WORKFLOW Out of Scope table and are not re-litigated here.

| Capability | Decision | Reason |
|------------|----------|--------|
| `gh auth status` (plain, non-`--json`) | INTEGRATE | PRW-04's unauthenticated-notice branch; `--json` always exits 0 (RESEARCH Pitfall 5) |
| `gh pr list --head <branch> --state open --json number,url` | INTEGRATE | PRW-01/PRW-03 existence probe; state-filtered so `[]` cleanly means "no open PR" |
| `gh pr checks <number> --json bucket` | INTEGRATE | PRW-01 rollup source; `bucket` is `gh`'s own normalized union-type reduction |
| `gh pr view --json ...` | OPT-OUT | Returns exit 0 for merged/closed PRs with no `--state` filter — misclassifies "no open PR" (RESEARCH Pitfall 2) |
| `gh pr checks --watch` | OPT-OUT | A lifecycle step must not block on CI; `execute:wave:post` takes one instantaneous sample |
| `gh pr create` (incl. draft) | OPT-OUT | *(canon)* Would spam PRs for phases the user isn't ready to open one for; capability has no branch/commit-strategy awareness |
| `gh pr merge` / auto-merge | OPT-OUT | *(canon)* Violates the source skill's own hardest constraint ("never merge a PR, the user decides") |
| `gh pr edit --add-reviewer` | OPT-OUT | *(canon)* Requires live conversational judgment a one-shot `gates[]`/`contributions[]` predicate architecturally cannot exercise |
| `gh pr review` / review-thread resolution | OPT-OUT | *(canon)* Same as above; stays in the existing interactive `pr-workflow` skill |
| `gh pr comment` | OPT-OUT | Write-side surface; this capability is read-only against GitHub (prohibition P2) |
| `gh extension install` / `gh pr-review` extension | OPT-OUT | *(canon)* Only needed for review-thread automation, which is out of scope; this capability depends on `gh` CLI only |
| `gh auth login` / `gh auth token` / `--show-token` | OPT-OUT | Credential surface — never invoked; `gh`'s token store is out of this capability's binding model entirely (prohibition P1) |
| `gh run list` / `gh workflow` (Actions surface) | OPT-OUT | `gh pr checks` already rolls up Actions + external status contexts; a second source would duplicate and diverge |
| `gh api` (raw REST/GraphQL passthrough) | OPT-OUT | Would re-introduce the `CheckRun` vs `StatusContext` union parsing `gh pr checks --json bucket` already solves |

**Coverage summary:** 3 INTEGRATE, 11 OPT-OUT, 0 undecided.
