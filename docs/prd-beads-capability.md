# PRD — `beads`: first-class issue tracking for gsd-core

**Status:** draft for approval
**Date:** 2026-08-15
**Deliverable:** a gsd-core capability, installed as a runtime overlay. No fork.

---

## 0. How to verify this document

Every factual claim about gsd-core below is checkable against a gsd-core checkout. The commands are given inline where the claim is made, and the load-bearing ones are:

| Claim | Command |
| :--- | :--- |
| gsd-core has no issue-tracker integration | `grep -rli "beads\|bd create\|bd ready" .` → 0 hits |
| Capability count and shape | `ls capabilities/ \| wc -l`; `cat capabilities/mempalace/capability.json` |
| Third-party overlays are supported | `src/capability-loader.cts`, `tests/capability-loader.test.cjs` |
| Lifecycle points in use | `grep -rhoE '"point": "[a-z:]+"' capabilities/*/capability.json \| sort \| uniq -c` |
| Gate predicate kinds | `grep -rhoE '"kind": "[a-z-]+"' capabilities/*/capability.json`, cross-checked in `src/` |

Nothing here depends on any repository other than gsd-core and the `bd` binary. Figures were measured on 2026-08-15; re-run the commands if the version differs.

---

## 1. Summary

`beads` makes the [beads](https://github.com/gastownhall/beads) issue tracker the **task substrate** for gsd-core's workflow — not a mirror written after the fact, but the store gsd's planner, executor and verifier read from and write to at every lifecycle point where task state changes.

gsd-core has no issue-tracker integration of any kind. `grep -rli "beads\|bd create\|bd ready"` across the distribution returns **zero hits**, and none of its 45 capabilities provides one. Task state lives in `.planning/` markdown: per-project, hand-maintained, archived at milestone close, with no query surface.

The capability installs as a **runtime overlay** — a directory drop, no fork and no patch to gsd-core.

---

## 2. What "first class" means here

A mirror writes issues *after* gsd decides something and never reads them back. That is second class by construction. First class means four specific properties, each achievable with mechanisms gsd-core already ships:

| # | Property | Mechanism |
| :--- | :--- | :--- |
| **F1** | Task **status** lives in beads. gsd's markdown holds the *plan*; beads holds *state*. | `steps[]` bound at each state transition; `beads.sync_mode` (`authoritative` default vs. `mirror`) governs whether an explicit `create-issues` strips synced task bodies out of PLAN.md. |
| **F2** | The planner and executor **see** beads. Their prompts carry live issue state. | `contributions[]` injecting prompt fragments `into: orchestrator` and `into: verifier`. |
| **F3** | Beads state can **block a ship**. An unfinished or diverged phase does not pass. | `gates[]` with `artifact-frontmatter-equals` over a generated `BEADS.md`, `blocking: true`. |
| **F4** | Beads is **queried before planning**, so ticketed work is not planned twice. | `steps[]` at `plan:pre` producing a recall artifact. |

If a change does not advance one of F1–F4, it is out of scope.

---

## 3. Problem

### 3.1 Where gsd-core keeps task state today

gsd-core plans and executes in phases. Its durable state is markdown under `.planning/` — `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`, `PROJECT.md`, `phases/`, and a `todos/pending/` directory. `gsd-complete-milestone` archives a finished milestone into `milestones/`.

This is a good fit for *plan content* — what a phase is for, how a task should be approached, what "done" means. It is a poor fit for *task state*:

| Need | `.planning/` markdown | beads |
| :--- | :--- | :--- |
| Query "what can I work on now?" | read files, reason | `bd ready` |
| Dependencies and blocking | prose ordering | first-class, enforced |
| Status across phases | per-phase files | one query |
| Survives milestone archival | archived away | persists |
| Visible outside one project | no | yes |
| Machine-updatable without rewriting prose | no | yes |

### 3.2 The cost, concretely

With no bridge, a developer who uses both maintains two representations of the same work by hand. Every plan produces tasks that must be re-typed as issues; every completed task must be closed twice; and the two drift silently, because nothing compares them. Nothing in gsd-core detects or reports that drift, because gsd-core does not know the tracker exists.

### 3.3 Why an overlay rather than a fork

gsd-core is large — 79 skills, 109 workflow files, 34 agents, 45 capabilities, 796 test files. A fork buys the maintenance of all of it in order to add one integration, and diverges from upstream permanently. §5.1 establishes that a fork is unnecessary: third-party capabilities are a supported, tested extension mechanism.

---

## 4. Goals / Non-goals

### Goals

- **G1 (F1).** Every gsd task exists as a beads issue, with correct status, without anyone running `bd` by hand.
- **G2 (F2).** The planner and executor operate with beads state in context.
- **G3 (F3).** A phase cannot ship with open or diverged issues unless the operator overrides deliberately.
- **G4 (F4).** Planning starts from what is already ticketed.
- **G5.** `bd` absent, broken, or locked never blocks a phase.

### Non-goals

- **N1.** Not replacing any first-party gsd-core behaviour. The overlay cannot override it by design (first-party-wins), and should not try to work around that.
- **N2.** Not forking or patching gsd-core. If a core change proves necessary, raise it upstream first.
- **N3.** Not building a second planning or gating pipeline. This capability tracks work; it does not decide how work is planned.
- **N4.** Not executing any command string that originates in a plan, ticket, or other reviewed artifact. The party authoring an artifact and the party running the workflow are frequently different principals — a reviewer, a CI runner with deployment credentials — and executing authored input hands the second party's privileges to the first. `bd` invocations are constructed by this capability from typed values, never assembled from artifact text.
- **N5.** No dependency beyond `bd` and Python 3 standard library.
- **N6.** Not syncing beads onward to GitHub Issues, Jira or anything else. One tracker.

---

## 5. Architecture

### 5.1 Installation: a plugin, not a fork

gsd-core ships a **runtime capability registry overlay** (ADR-1244 D2, implemented in `src/capability-loader.cts`, covered by `tests/capability-loader.test.cjs` — which installs a *third-party* `deploy-gate` capability with its own agent and config key, and asserts it appears in every derived view). Install by dropping a directory at either scope:

- **global:** `$GSD_HOME/.gsd/capabilities/<id>/capability.json` (`GSD_HOME` defaults to `~`)
- **project:** `<projectRoot>/.gsd/capabilities/<id>/capability.json`

`loadRegistry({ includeInstalled })` composes overlays onto the frozen first-party registry. An accepted overlay appears in `capabilities`, `bySkill`, `byAgent`, `configSchema`, `configKeys`, `capabilityClusters` and `profileMembership`, and its steps are wired into the workflow loop.

**Invariants that constrain this design:**

| Rule | Consequence |
| :--- | :--- |
| Reserved id prefixes `gsd-`, `gsd-core-`, `anthropic-` are **rejected** | The capability id is `beads`. |
| An id or federated config key colliding with first-party is **rejected** | Config lives under `beads.*`; check against all shipped manifests before use. |
| **First-party wins** on collision | The overlay extends; it cannot override. Everything below is additive. |
| `engines.gsd` mismatch → **skipped with a warning**, never a crash | Declare `engines.gsd` honestly and treat a skip as a supported state. |
| A malformed descriptor → skipped fail-closed; the loader never throws | Satisfies G5 at the loader level. |
| Global-scope overlays pass a **consent gate** (CB-3) | Ship project-scoped first; consent is part of install UX. |

### 5.2 The binding surface

Capabilities bind three ways. All three are used here.

**`steps[]`** — run a skill or agent at a lifecycle point. Points observed in use across the shipped capabilities: `discuss:pre`, `discuss:post`, `plan:pre`, `plan:post`, `execute:wave:pre`, `execute:wave:post`, `execute:post`, `verify:pre`, `verify:post`, `ship:pre`, `ship:post`. Each step declares `ref: {skill|agent}`, `produces[]`, `consumes[]`, `when: <config key>`, and `onError`.

**`contributions[]`** — inject a prompt fragment `into: orchestrator | verifier` at a point. **This is what makes the integration first class rather than a side effect:** it is how the planner and executor come to know that beads exists and what it currently says.

**`gates[]`** — `{point, check: {predicate}, when, blocking, onError}`. The authoritative predicate kinds are exactly two: **`command-exists`** and **`artifact-frontmatter-equals`**. There is no predicate that queries an external tool, which determines the design in §5.4.

The closest shipped analogue for the overall shape is `capabilities/mempalace/capability.json` — an external store, touched at phase boundaries, degrading cleanly when unreachable. Read it before implementing.

### 5.3 Manifest

```json
{
  "id": "beads",
  "role": "feature",
  "version": "0.1.0",
  "title": "Beads issue tracking",
  "description": "Beads is the task substrate: gsd plan tasks exist as beads issues, their status lives in beads, and planning starts from what is already ticketed.",
  "tier": "full",
  "requires": [],
  "engines": { "gsd": ">=1.6.0" },
  "skills": ["beads-sync", "beads-recall", "beads-status"],
  "agents": [],
  "hooks": [],
  "config": {
    "beads.enabled":      { "type": "boolean", "default": true },
    "beads.sync_mode":    { "type": "enum", "values": ["authoritative", "mirror"], "default": "authoritative" },
    "beads.epic_per":     { "type": "enum", "values": ["phase", "milestone"], "default": "phase" },
    "beads.ship_gate":    { "type": "boolean", "default": true },
    "beads.recall_scope": { "type": "enum", "values": ["phase-files", "project", "all"], "default": "phase-files" }
  },
  "steps": [
    { "point": "plan:pre",          "ref": {"skill": "beads-recall"}, "produces": ["BEADS-RECALL.md"], "consumes": ["CONTEXT.md"], "when": "beads.enabled", "onError": "skip" },
    { "point": "plan:post",         "ref": {"skill": "beads-sync"},   "produces": ["BEADS.md"],        "consumes": ["PLAN.md"],    "when": "beads.enabled", "onError": "skip" },
    { "point": "execute:wave:pre",  "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"],        "consumes": ["PLAN.md"],    "when": "beads.enabled", "onError": "skip" },
    { "point": "execute:wave:post", "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"],        "consumes": ["PLAN.md"],    "when": "beads.enabled", "onError": "skip" },
    { "point": "verify:post",       "ref": {"skill": "beads-status"}, "produces": ["BEADS.md"],        "consumes": ["UAT.md"],     "when": "beads.enabled", "onError": "skip" },
    { "point": "ship:post",         "ref": {"skill": "beads-sync"},   "produces": ["BEADS.md"],        "consumes": ["SUMMARY.md"], "when": "beads.enabled", "onError": "skip" }
  ],
  "contributions": [
    { "point": "plan:pre",          "into": "orchestrator", "fragment": {"path": "fragments/recall-open-issues.md"}, "when": "beads.enabled", "onError": "skip" },
    { "point": "execute:wave:pre",  "into": "orchestrator", "fragment": {"path": "fragments/claim-and-close.md"},    "when": "beads.enabled", "onError": "skip" },
    { "point": "execute:wave:post", "into": "verifier",     "fragment": {"path": "fragments/report-divergence.md"},  "when": "beads.enabled", "onError": "skip" }
  ],
  "gates": [
    { "point": "ship:pre",
      "check": { "predicate": { "kind": "artifact-frontmatter-equals", "artifact": "BEADS.md", "field": "blocking_open", "equals": 0 } },
      "when": "beads.ship_gate", "blocking": true, "onError": "skip" },
    { "point": "ship:pre",
      "check": { "predicate": { "kind": "artifact-frontmatter-equals", "artifact": "BEADS.md", "field": "diverged", "equals": 0 } },
      "when": "beads.ship_gate", "blocking": true, "onError": "skip" }
  ]
}
```

### 5.4 `BEADS.md` — the projection that makes gating possible

Gate predicates read artifact frontmatter only, so the capability **projects beads state into an artifact** on every step:

```markdown
---
phase: 3
epic: proj-a1b
blocking_open: 0
diverged: 0
open: 2
closed: 7
generated_from: bd
generated_at: 2026-08-15T09:14:02Z
---
# Beads state for phase 3

| issue | title | status | plan task |
|-------|-------|--------|-----------|
| ...regenerated on every step; a human-readable view of the same query... |
```

`blocking_open` counts issues that must close before ship. `diverged` counts mismatches between beads and `PLAN.md`. Both are integers so `artifact-frontmatter-equals` can gate on them.

`gates[].onError` is deliberately **`skip`, not `halt`**: a missing or unreadable `BEADS.md` — capability disabled, `bd` absent, first run — must not strand a finished phase. The gate blocks on a *known* bad state, never on an *unknown* one.

---

## 6. Requirements

### P0 — the substrate (F1)

| ID | Requirement | Acceptance criterion |
| :--- | :--- | :--- |
| **B1** | One beads issue per `PLAN.md` task, parented to a phase epic. | After planning an N-task phase, `bd list --parent <epic>` returns exactly N issues whose titles match the plan's tasks. |
| **B2** | Plan task ordering becomes beads dependencies. | Task 3 depending on task 1 shows task 1 as a blocker in `bd show`; `bd ready` excludes task 3 until task 1 closes. |
| **B3** | Task completion closes its issue automatically. | After a wave completes task 2, that issue is `closed` and no other issue changed. |
| **B4** | Identity is bound explicitly, never by title matching. | Each plan task block carries a `beads-id:` written on first sync; re-sync resolves by that id. Renaming a task title does not create a second issue. |
| **B5** | Sync is idempotent. | Two syncs over an unchanged plan create zero issues and modify zero issues, proven by a `bd list --json` diff. |
| **B6** | `bd` absent, failing or locked degrades to a no-op with one visible notice. | With `bd` off `PATH`, every gsd command completes normally, one line explains the skip, no phase is blocked, and `BEADS.md` is absent rather than stale. |

### P0 — visibility and enforcement (F2, F3, F4)

| ID | Requirement | Acceptance criterion |
| :--- | :--- | :--- |
| **B7** | The planner sees open issues before planning. | With an open issue touching a file in the phase's scope, `BEADS-RECALL.md` exists before the planner runs and names that issue. |
| **B8** | The executor's prompt carries live issue state. | The `execute:wave:pre` fragment is present in the composed orchestrator prompt and names the issues in the wave — verified by inspecting the prompt, not by inferring from behaviour. |
| **B9** | A phase with unfinished blocking issues cannot ship. | With one open blocking issue, `ship:pre` blocks and names it. `beads.ship_gate=false` allows the ship and records that it was overridden. |
| **B10** | Divergence blocks and is reported; it is never auto-reconciled. | An issue closed in beads whose task is incomplete (or the reverse) sets `diverged>0`, blocks ship, and reports both sides. Nothing changes until the operator decides. |
| **B11** | `BEADS.md` is regenerated, never hand-edited. | A hand edit is overwritten at the next step; frontmatter always reflects a real `bd` query at generation time. |

### P1 — adoption

| ID | Requirement |
| :--- | :--- |
| **B12** | One-shot migration of existing `.planning/todos/pending/` entries into beads, reporting what moved and what could not be interpreted. |
| **B13** | `beads-status` runnable on demand, printing the plan-task ↔ issue mapping including orphans on both sides. |
| **B14** | Milestone-level epic option (`beads.epic_per=milestone`) for users who prefer one epic per release. |

---

## 7. Data model

| gsd-core | beads | Binding |
| :--- | :--- | :--- |
| Phase | epic | Created on first `plan:post`; id recorded in `BEADS.md` frontmatter. |
| `PLAN.md` task | issue (`--type=task`) | `beads-id:` line in the task block. Never title-matched. |
| Task dependency | `bd dep add` | Mirrors declared plan ordering only; nothing inferred. |
| Task complete | `bd close` | Never closes an issue a human reopened — that is divergence (B10). |
| Requirement id | issue label | Enables `bd list` filtered by requirement. |
| Milestone | epic (optional) | Off by default; two epic layers is usually noise. |

**Authority.** In `authoritative` mode beads owns *status*; `PLAN.md` owns *content*. No field is owned twice, which is what makes divergence detectable rather than a merge problem.

---

## 8. Failure modes

| Failure | Behaviour |
| :--- | :--- |
| `bd` not installed | Capability inert via `command-exists`; one notice. |
| `bd` non-zero exit | Skip; report the command and stderr verbatim; phase proceeds. |
| beads DB locked | One retry, then skip with a notice. |
| Plan task deleted after sync | Orphaned issue reported; never auto-closed. |
| Issue closed in beads, task incomplete | `diverged>0`; ship blocked; both sides reported (B10). |
| Two phases claim one issue | Hard error naming both. A mapping bug, not a state to reconcile. |
| `BEADS.md` missing at a gate | `onError: skip`; the gate does not fire. |

**Nothing may block a phase except B9 and B10, and both are deliberate, named and overridable.**

---

## 9. Phasing

| Phase | Content | Exit |
| :--- | :--- | :--- |
| **S1 — packaging spike** | Settled: overlays install without a fork (§5.1). Open: may an overlay ship a Python entry point, or must a JS hook shell out to it? Plus the global-scope consent-gate UX. | A minimal `beads` overlay that loads, appears in `bySkill`, and runs one `bd` query. |
| **P1 — substrate** | B1–B6. | A real phase planned and executed with issues created, claimed and closed automatically. |
| **P2 — visibility** | B7, B8, B11. | Composed prompts inspected and shown to carry issue state. |
| **P3 — enforcement** | B9, B10. | A deliberately diverged phase blocks at `ship:pre` and reports both sides. |
| **P4 — adoption** | B12–B14. | Existing todos migrated; mapping inspectable on demand. |

---

## 10. Success metrics

| Metric | Baseline | Target |
| :--- | :--- | :--- |
| Beads issues hand-created for gsd work | all of them | 0 |
| Hand reconciliations between `.planning/` and beads | every session | 0 |
| Phases shipped with open blocking issues | invisible today | 0, or explicitly overridden |
| Planning sessions that re-plan already-ticketed work | invisible today | visible in `BEADS-RECALL.md`, trending to 0 |
| Phases blocked by tracker failure | n/a | **0**, by design |

**The honest metric:** if after one milestone the user has not hand-edited a single beads issue the capability should have written, P1–P3 succeeded. If they have, the mapping is wrong and should be redesigned rather than patched.

---

## 11. Risks

| Risk | Assessment |
| :--- | :--- |
| **Two-way sync corrupts trackers.** The classic failure of this category. | Mitigated structurally: explicit id binding (B4), idempotence (B5), report-never-reconcile (B10), single ownership per field (§7). |
| **`contributions[]` may not carry F2.** Fragments are prompt text; their effect on model behaviour is not guaranteed by the mechanism. | Verify by inspecting the composed prompt (B8), never by observing behaviour and inferring. If fragments prove weak, fall back to `BEADS-RECALL.md` as a consumed artifact — weaker, but reliable. |
| **`authoritative` mode may fight gsd's own state writes.** First-party wins, so gsd keeps writing `.planning/`. | This is why beads owns *status* and `PLAN.md` owns *content*. If they still collide, drop to `mirror` and propose a task-provider interface upstream. |
| **Wave granularity is assumed.** Whether `execute:wave:post` fires per task or per wave decides whether B3 closes one issue or several. | The one lifecycle detail this design assumes without having verified. Settle it in S1; it is cheap to observe. |
| **Scope creep into a second pipeline.** Tracking invites gating, gating invites policy. | N3 is a hard boundary. Anything that decides *how work is planned* rather than *what state it is in* is out of scope. |

---

## 12. Open questions

1. **Packaging** — may an overlay ship a Python entry point, or must a JS hook shell out to it? Installation itself is settled (§5.1).
2. **Wave granularity** — does `execute:wave:post` fire per task or per wave?
3. **Override auditing** — when `beads.ship_gate=false` allows a ship, where is that recorded so it stays visible afterwards?
4. **Upstream?** A task-provider interface would serve every gsd-core user. If `authoritative` mode fights first-party writes, upstreaming may be cheaper than working around it.

---

## Appendix A — deterministic plan checks (DEFERRED, possibly never)

A separate `role: reviewer` capability could supply deterministic, zero-token checks over `PLAN.md` and `REQUIREMENTS.md` — requirement/task traceability, success criteria present, a named BASE commit that resolves — feeding gsd's LLM plan-checker rather than replacing it. Some of what a plan checker confirms is not a judgement at all, and a subprocess is cheaper and deterministic where the property is decidable.

**Deferred deliberately.** The benefit is unmeasured and the failure mode is a second review pipeline nobody asked for. Revisit only after `beads` has shipped, and only if the LLM plan-checker is *observed* spending judgement on decidable properties. If fewer than five such checks prove worth writing, do not build it at all.
