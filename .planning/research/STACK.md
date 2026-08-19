# Upstream State: gsd-core — research for milestone v1.3

**Subject:** current upstream state of `open-gsd/gsd-core`, and what of it invalidates or affects
this repo's two local patches and its `PostToolUse` lifecycle-dispatch hook.
**Researched:** 2026-08-19 (all queries run 21:00–21:35 UTC)
**Method:** `gh` CLI against the live repo, `npm view`, and a fresh shallow clone of `main` and
`next`. Nothing below is asserted from memory or from this repo's own prose.
**Overall confidence:** 92

> **Headline.** `1.11.0` is still latest (released today). But **PR #3687 (`fix(#3606)`) merged
> into the default branch `next` at 2026-08-19T20:41:28Z — 6h50m *after* the 1.11.0 release cut —
> and adds generic `kind == "step"` dispatch at `plan:post` and `verify:post`.** It does **not**
> add step dispatch at `execute:wave:pre`, `execute:wave:post`, or `ship:pre`. This is the same
> class of "roadmap written against a stale upstream" failure the prior pass hit, caught this time
> *before* planning.

---

## 1. Latest released version

| Fact | Value | Source |
|---|---|---|
| npm `latest` | **1.11.0** | `npm view @opengsd/gsd-core version` → `1.11.0` |
| npm publish time | **2026-08-19T13:51:30.699Z** | `npm view @opengsd/gsd-core time --json` |
| GitHub latest release | **v1.11.0**, `isPrerelease: false`, `isDraft: false` | `gh release view --repo open-gsd/gsd-core --json tagName,isPrerelease,isDraft` |
| Prior release | 1.10.0 @ 2026-08-08T05:07:17Z | same |
| npm `next` dist-tag | `1.7.0-rc.6` — **stale**, published 2026-07-12; not a live prerelease channel | `npm view @opengsd/gsd-core dist-tags` |
| Newer / prerelease | **None.** No 1.12.x, no rc after `1.7.0-rc.6` | full `versions` array ends `…1.10.0, 1.11.0` |

**Is 1.11.0 still latest? Yes** — and it is ~8 hours old. The prior pass's error (planning against
1.10.0 while 1.11.0 existed) is not repeatable today at the *release* level, but is repeatable at
the *branch* level; see §4. Confidence **98**.

**Branching model (load-bearing).** `gh api repos/open-gsd/gsd-core -q .default_branch` returns
**`next`**, not `main`. PRs merge to `next`; a `release/X.Y.Z` branch merges to `main` at cut time.
Verified both ways: PR #3608 (shipped in 1.11.0) has `baseRefName: next`; `main`'s HEAD is
`b0ccf790 "Merge pull request #3666 from open-gsd/release/1.11.0"` @ 2026-08-19T13:51:46Z.
**Therefore anything on `next` but not `main` is merged-and-unreleased, and lands in the next
release.** Confidence **95**.

---

## 2. What 1.11.0 shipped that touches this repo's surfaces

Read from `gh release view v1.11.0 --json body` (173 lines) and `CHANGELOG.md` on `main`.

**One entry, and only one, touches capability hook dispatch:**

> `* fix(#3559): dispatch every ship:pre capability gate, not two hardcoded capIds by @trek-e in
> https://github.com/open-gsd/gsd-core/pull/3608`

Verified in the shipped text. `gsd-core/workflows/ship.md` preflight step 6 now reads:

> **Every other `capId`** — run the gate's own declared check through the generic evaluator. This
> arm is what makes a third-party capability's declared gate enforceable at all (#3559); before it
> existed, a gate whose `capId` was not named above was resolved and then silently dropped.

**Scope check — gates only, not steps.** Step 6's own preamble on the shipped text:

> **For each active entry where `kind == "gate"`** (process in array order) … Entries of any other
> `kind` are not gates and are not enforced here.

Step 6 ends at "continue to the next preflight check", then `</step>`, then
`<step name="push_branch">`. **There is no `kind == "step"` dispatch anywhere in `ship:pre` on
1.11.0.** Confidence **95**.

**Nothing else in 1.11.0 touches `plan:post`, `execute:wave:pre/post`, `verify:post`, or the
capability config schema.** Grepping the release body for `dispatch|capabilit|hook|gate|ship:`
returns 22 lines; the other 21 are unrelated (ADR gate, pre-commit hook, `commit_docs`, Codex
`.toml`, Windows binary resolver, hook *build* self-heal #3582). Config-schema-adjacent entries
(`phase_commit_docs`, `effort_effective`, `manifestVersion`) do not touch the capability config
block. Confidence **88** (grep-based negative over a long changelog).

---

## 3. Issue/PR ledger — the five you named, plus what the search surfaced

All fields from `gh issue view <n> --repo open-gsd/gsd-core --json number,title,state,stateReason,closedAt,labels`.

| # | Title (abridged) | State | stateReason | Merged/shipped |
|---|---|---|---|---|
| **3554** | ship:pre gate dispatch hardcodes capId, no generic third-party gate loop | CLOSED 2026-08-15T22:30:52Z | **NOT_PLANNED** | n/a — no labels, no fix |
| **3559** | ship:pre gate dispatch hardcodes capId=='security'/'broken-windows' … (repro: beads) | CLOSED 2026-08-18T02:28:07Z | **COMPLETED** | by PR #3608, **shipped in v1.11.0** |
| **3608** | `fix(#3559): dispatch every ship:pre capability gate…` | **MERGED** 2026-08-18T02:28:06Z | — | base `next`; **in v1.11.0** |
| **3646** | feat(execute-plan): native per-task external-tracker content-resolution seam | **OPEN** | — | label `approved-feature`; **no PR exists** |
| **3647** | obs(dispatch): capability lifecycle-dispatch steps intermittently skipped (beads, 3/4 wave-close missed) | **OPEN** | — | labels `bug`, `ready-for-human`; **no PR** |

**Found by search, not in your list, and decisive:**

| # | Title (abridged) | State | stateReason | Merged/shipped |
|---|---|---|---|---|
| **3606** | capability-validator: hook call-site check validates existence, not dispatch — a wired+enabled capability can silently never run | CLOSED **2026-08-19T20:41:29Z** | **COMPLETED** | by PR #3687 |
| **3687** | `fix(#3606): validate hook-kind coverage at call sites and dispatch generically` | **MERGED 2026-08-19T20:41:28Z** | — | base **`next`** → merge commit `ea594300d9`. **NOT in v1.11.0** (release cut 13:51Z, merge 20:41Z). Unreleased. |
| **3661** | feat(code-review): make the review hook point configurable (`execute:wave:post`, not only `execute:post`) | **OPEN** | — | label `approved-enhancement`; no PR |
| **3631** | bug(capability): `bundleContentHash` includes `__pycache__/*.pyc`, silently deactivates capability on routine test runs | CLOSED 2026-08-19 | COMPLETED | PR #3650, in v1.11.0 |

Other closed-in-window hits (#3561, #3514, #3468, #3248, #3247, #3177, #2787) were checked by
title and are unrelated to hook-kind dispatch. Confidence **90**.

**No open PR touches `ship.md` or step dispatch.** `gh pr list --state open --limit 100` returns 14
PRs; none is dispatch-related. Confidence **90**.

**#3631 is a live operational hazard for this repo** and is not about dispatch: a capability's
`bundleContentHash` used to include `__pycache__/*.pyc`, so *running the capability's own Python
tests deactivated it*. This repo ships `sync.py`. Fixed in 1.11.0 — an argument for staying on
1.11.0+, independent of everything else. Confidence **80** (read from title + changelog line, not
from the diff).

---

## 4. Is there upstream work providing generic `kind: "step"` dispatch at the five points?

**Yes — partially, and it is merged-but-unreleased on `next`.** This is the finding that must not
be missed twice.

PR #3687 body, "What this fix does":

> **Consumer fixes** (the generic contract, per `references/loop-hook-dispatch.md`): plan-phase
> plan:pre (generic contribution dispatch …) and **plan:post (generic step + contribution;** the
> skip no longer keys on the gap-analysis gate's absence); execute-phase **wave:pre + wave:post
> (contribution dispatch)** and **verify:post (generic steps** before the secure-phase
> specialization); **verify-work verify:post (generic steps);** quick.md execute:post (generic
> steps before the code-review specialization).

Verified against the actual `next` tree (`git show FETCH_HEAD:gsd-core/workflows/…`), not just the
PR prose:

- `plan-phase.md` §13e, `next`: *"**Step and contribution dispatch:** dispatch every `kind == "step"` hook and inject every `kind == "contribution"` fragment per @gsd-core/references/loop-hook-dispatch.md"* — and the old skip (`If the gap-analysis gate hook is absent … skip this step`) is replaced by `If activeHooks is empty or absent, skip … do NOT key the skip on any one capability's gate being absent (#3606…)`.
- `execute-phase.md` verify:post, `next`: *"Dispatch every `kind == "step"` hook per @…/loop-hook-dispatch.md (skip when none). The secure-phase routing below applies when that specific hook is active."*
- `verify-work.md` verify:post, `next`: *"**Generic step dispatch:** dispatch every `kind == "step"` hook from `VERIFY_POST_HOOKS_JSON` … The secure-phase handling below is an additional specialization of one such hook, not a replacement."*
- `execute-phase.md` step 2.75 (`execute:wave:pre`), `next`: only *"**Contribution dispatch:** inject every `kind == "contribution"` fragment …"* — **no step arm.**
- `execute-phase.md` step 5.75 (`execute:wave:post`), `next`: *"**Contribution dispatch:** … before the gates below"* then *"For each active entry where `kind == "gate"`"* — **no step arm.**
- `ship.md`, `next`: **untouched by #3687** (not in the PR's 35-file list) — still gate-only at `ship:pre`.

### 4a. Point-by-point verdict against this repo's six declared `steps`

Source of truth for what this repo declares:
`plugins/beads-lifecycle/.gsd/capabilities/beads/capability.json` — six entries under `"steps"`,
all `ref.skill`, all `when: "beads.enabled"`, all `onError: "skip"`.

| Point | Repo's step | 1.11.0 (released, installed) | `next` @ `ea594300` (unreleased) |
|---|---|---|---|
| `plan:pre` | `beads-recall` | **native** — §5.6 "Generic step hook dispatch contract: For each active entry where `kind == "step"`", reached whenever `activeHooks` is non-empty | unchanged (only contribution dispatch added) |
| `plan:post` | `beads-sync` | **absent** — gate-only, skip keyed on gap-analysis | ✅ **native generic step dispatch** |
| `execute:wave:pre` | `beads-status` | **absent** — contribution-only (2.75) | ❌ still absent (contribution only) |
| `execute:wave:post` | `beads-status` | **absent** — gate-only (5.75) | ❌ still absent (contribution + gate only) |
| `verify:post` | `beads-status` | **absent** — hardcoded `ref.skill == "secure-phase"` | ✅ **native generic step dispatch** (both `execute-phase.md` and `verify-work.md`) |
| `ship:pre` | `beads-status` | **absent** — #3608 added the generic *gate* arm only | ❌ still absent |

Confidence **93** (every row read from the live file text on the named ref).

### 4b. What this makes redundant — and what it does not

The `PostToolUse` hook's point list, read from
`plugins/beads-lifecycle/hooks/lifecycle-dispatch.sh:61`:

```
POINTS = ("plan:pre", "plan:post", "execute:wave:pre", "execute:wave:post", "verify:post")
```

**When #3687 ships (next release, presumably 1.12.0):**

| Local artifact | Verdict |
|---|---|
| Hook's `plan:post` entry | **Becomes redundant.** gsd-core dispatches `beads-sync` natively. Keeping it risks a **double dispatch** of `beads-sync` at `plan:post`. |
| Hook's `verify:post` entry | **Becomes redundant.** Same double-dispatch risk for `beads-status`. |
| Hook's `plan:pre` entry | **Already redundant on 1.11.0** at §5.6 — the native generic step loop exists and is not kind-filtered. (This repo's `GSD-CORE-PATCH.md` asserts §5.6 is "behind an auto-chain + frontend-detection branch"; on the live text the only guard is `Branch 1 — all plan:pre hooks inactive … Skip to step 6`. I could not verify a manual-`/gsd:plan-phase` path that bypasses §5.6 entirely, so I flag this claim as **unconfirmed** rather than refuted. Confidence **60**.) |
| Hook's `execute:wave:pre` + `execute:wave:post` entries | **NOT redundant.** No upstream work — released, merged, or open-PR — provides step dispatch at either. #3647 is the open filing that owns `execute:wave:pre`; it has no PR. **The hook must survive for these two points.** |
| **Patch 1** (`ship.md` v2, `ship:pre` step dispatch) | **NOT redundant.** #3687 does not touch `ship.md`; `ship:pre` remains gate-only on `next`. The `GSD-CORE-PATCH.md` "Remaining revert condition" and its note *"No upstream issue currently tracks that remaining half"* both still hold — verified, no such issue exists. |
| **Patch 2** (`execute-plan.md`, bd task-content read) | **NOT redundant.** #3646 is OPEN with `approved-feature` and **no PR**. |
| `sync.py`'s `check_shipmd_patch` / `check_execute_plan_patch` | **Both still needed** (their patches survive). |

**So: the whole hook does not become redundant — but two of its five points do.** The statement the
brief asked for, stated explicitly: *the hook's `plan:post` and `verify:post` dispatch become
upstream-native in the release after 1.11.0 and should be dropped from `POINTS` at that point;
`execute:wave:pre` and `execute:wave:post` are the hook's remaining reason to exist.*

**Also relevant to Phase 17's patch-loss-detection design:** #3687 extends
`capability-validator.cjs` so that *"a call site mentioning only `kind == "gate"` fails validation
when a `step` or `contribution` hook is registered at the same point."* That is a
generation-time guard in gsd-core's own tooling (`scripts/gen-loop-host-contract.cjs`, not shipped
in the npm distribution), so it does **not** give this repo a runtime detector. Its disclosed
limitation, from the PR body:

> **Known limitation, disclosed**: coverage is the union across the five STEP_WORKFLOWS host files
> … Consumers outside that universe (autonomous.md, code-review*.md, audit-milestone.md,
> secure-phase.md, validate-phase.md) are not per-file checked.

Confidence **85**.

### 4c. Maintainer's own conditions on #3646 (directly constrains Patch 2's future)

From the triage verdict comment (trek-e, 2026-08-19), condition 2 — quoted because it decides
whether Patch 2 can ever be replaced by an upstream seam:

> **The hard-halt guarantee must be enforced, not instructed.** … a dispatch point that is a
> natural-language step in a long orchestrator document cannot halt when it is not executed; it is
> simply absent, and the executor proceeds into the inline `PLAN.md` body, which is
> indistinguishable from the legitimate pre-migration fall-back branch. **Either resolution moves
> to a code-side seam in the executor's plan-reading path, or this work sequences behind a fix to
> the dispatch-reliability family (#3606, #3647).**

#3606 is now fixed; **#3647 is not**. So #3646 is gated behind #3647, which has no PR. Plan for
Patch 2 to persist through v1.3 and beyond. Condition 1 also requires an ADR to land first.
Confidence **88**.

---

## 5. Contribution / issue-filing requirements

`gh api repos/open-gsd/gsd-core/contents/.github/ISSUE_TEMPLATE` →
`bug_report.yml`, `chore.yml`, `config.yml`, `docs_issue.yml`, `enhancement.yml`,
`feature_request.yml`. Also present: `.github/pull_request_template.md`, `PULL_REQUEST_TEMPLATE/`,
`CODEOWNERS`, `rulesets/`.

**Blank issues are disabled.** `config.yml`:

```yaml
blank_issues_enabled: false
```

That is the mechanical reason #3554 was closed NOT_PLANNED "on the form": a template-less issue is
not an accepted shape. Confidence **92**.

`bug_report.yml` requirements (`validations: required: true`):

- `labels: ["bug", "needs-triage"]` applied automatically.
- **Pre-submission checkbox, required:** *"I have searched existing issues and this bug has not already been reported."*
- **GSD Version, required** — with the instruction to read it from `~/.claude/gsd-core/gsd-file-manifest.json` or `npx @opengsd/gsd-core --version`.
- **Runtime dropdown, required** — Claude Code / OpenCode / Codex / Copilot / Antigravity / Cursor / Windsurf / Multiple.
- A prominent **PII-redaction notice** on pasted logs/config (recommends `presidio-anonymizer` or `scrub`).

**Observed triage workflow** (from #3559 → #3608 and #3606 → #3687): a filed bug gets an AI-triage
diagnosis comment, then a `confirmed-bug` label, then a fix PR whose checklist requires
*"Linked issue has the `confirmed-bug` label"*. Feature requests get `approved-feature` (#3646) or
`approved-enhancement` (#3661) with explicit go-with-conditions. **Practical rule for any refile:
use the template, state version + runtime, and expect the issue to need a `confirmed-bug` label
before a PR will be accepted against it.** Confidence **85**.

**One anomaly, flagged not interpreted:** `config.yml`'s contact link references *"v1.31.0 not on
npm yet"* and `bug_report.yml`'s version placeholder says `"e.g., 1.18.0"` — both inconsistent with
1.11.0 being latest. `git log` dates that file to `chore(#518): rename npm package…`, so it is
inherited/stale template text, not evidence of a different version series. I did not resolve it
further. Confidence **50**.

---

## 6. Gaps — things I did not verify

- Whether `/gsd:plan-phase` invoked manually reaches `plan-phase.md` §5.6 (bears on the
  `plan:pre` detector-independence argument in `GSD-CORE-PATCH.md`). Static text says it does;
  the repo's prose says it does not. **Unresolved — needs a live run, not a read.**
- Whether #3687 will ship in the *immediately* next release. It is on the default branch with a
  `.changeset/` fragment (`plucky-koalas-snooze.md`), which is the normal path, but release
  contents are the maintainer's call. Confidence **80**.
- I did not diff `capability.json` *schema* validation between 1.10.0 and 1.11.0 beyond the
  changelog; no schema change was advertised. Confidence **70**.
- `gsd-core/bin/lib/capability-validator.cjs` on `next` changed `+61/-17`; I read the PR's
  description of the change, not the diff hunks.

---

## 7. Action summary for the roadmapper and planner

1. **Do not delete the `PostToolUse` hook.** `execute:wave:pre` and `execute:wave:post` have no
   upstream fix anywhere — not released, not merged, not in an open PR. (Confidence 93)
2. **Plan a conditional trim, not a deletion:** when the release containing #3687 lands, drop
   `plan:post` and `verify:post` from `POINTS` in `lifecycle-dispatch.sh:61` to avoid double
   dispatch. Gate it on the installed version, not on a date. (Confidence 90)
3. **Keep Patch 1 (`ship.md` v2) intact.** `ship:pre` step dispatch is absent on `next`; no issue
   tracks it. If v1.3 wants it upstream, a *new* issue must be filed via `bug_report.yml`.
   (Confidence 93)
4. **Keep Patch 2 (`execute-plan.md`) intact.** #3646 is approved but blocked behind #3647 (open,
   no PR) plus an ADR requirement. (Confidence 88)
5. **Both `check_*_patch` functions in `sync.py` stay.** Neither patch is going away in v1.3. If
   Phase 17's goal is removing "patch-checker duplication", the duplication to remove is between
   the two checkers, not either checker itself. (Confidence 85)
6. **Re-run this check immediately before the roadmap is frozen.** `next` moved 3 commits in the
   7 hours before this research ran, and the single most important finding landed inside that
   window.
