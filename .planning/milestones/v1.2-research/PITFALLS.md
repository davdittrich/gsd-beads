# Pitfalls Research

**Domain:** gsd-core capability plugins — adding `pr-workflow`, `markdown-linting`,
`get-available-resources` to gsd-beads (a repo that has already shipped `beads`,
`ponytail-everywhere`, `sota-numerics` and hit six documented, named bugs doing it)
**Researched:** 2026-08-18
**Confidence:** HIGH (all findings verified against this repo's own PROJECT.md Key Decisions
table, live-read `capability.json` files, and a live read of the installed, patched
`$HOME/.claude/gsd-core/workflows/ship.md`) — one MEDIUM item flagged below where verification
relied on community docs rather than the primary Anthropic reference.

## Critical Pitfalls

### Pitfall 1: Trusting an unpatched `ship:pre` gate to fire on a fresh machine

**What goes wrong:**
A new capability declares `gates[]` at `ship:pre` (as `pr-workflow`'s and `markdown-linting`'s
manifests both plan to, per PROJECT.md's Current Milestone section) and the plan/verifier marks
the phase done because the gate mechanism "exists" in the manifest — but on any machine where
`$HOME/.claude/gsd-core/workflows/ship.md` still ships the stock dispatch, the gate never
evaluates. Stock `ship.md`'s `ship:pre` preflight only enumerates `capId == "security"` and
`capId == "broken-windows"`; every other capability's `gates[]` entry is invisible to it.

**Why it happens:**
This repo already hit this exact bug with `beads`'s own two `ship:pre` gates in Phase 3 — found
only via a full-file read of the installed workflow during plan-checking, not by testing (a live
run would have "succeeded" by silently never invoking the gate, no error surfaced). The fix that
made `beads`'s and `sota-numerics`'s gates visible today is a **machine-local patch**
(`<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->`, confirmed live-read at
`$HOME/.claude/gsd-core/workflows/ship.md` lines 157-240, adding step 8 "Generic `ship:pre` gate
dispatch"), installed on this one developer machine. The companion upstream feature request
(open-gsd/gsd-core#3554, closed as filed-without-template; re-filed as #3559) has **not** been
confirmed merged into any released gsd-core version as of this research — PROJECT.md documents it
only as "filed," never as "merged." Any other machine, CI runner, or contributor clone running
stock gsd-core reverts to the old, capId-restricted dispatch with zero warning.

**How to avoid:**
1. Before trusting `pr-workflow`'s or `markdown-linting`'s `ship:pre` gate in *any* environment,
   read `$HOME/.claude/gsd-core/workflows/ship.md` (or the equivalent install path) and confirm
   the `<!-- gsd-beads-patch:ship-pre-generic-dispatch v1 -->` marker (or its upstream-merged
   successor) is present. Absence means the gate is decorative.
2. Do not mark a phase's success criteria met from the manifest declaring `gates[]` alone — mirror
   `beads`'s own precedent: "ship:pre gates confirmed to actually block/pass via a live
   `gsd_run check predicate` smoke test against a synthetic" gate-input artifact (e.g. a synthetic
   `PR-CHECKS.md`/`LINT.md`), not just a manifest lint.
3. Track the upstream PR/issue status explicitly per new capability that relies on this dispatch;
   don't assume a prior capability's verification carries forward to a new capId — the dispatch
   loop is generic *once patched*, but the patch's presence itself is not guaranteed to persist
   across a `gsd-core` version bump (an upstream release could ship its own `ship.md` and silently
   drop an unmerged local patch on next `npx @opengsd/gsd-core@latest` refresh).

**Warning signs:** A `ship:pre` gate that always reports "passing" with no visible failure mode
ever observed in testing; no `⚠ Ship gate blocked` or `⚠ {capId} advisory` line ever printed
during a deliberately-failing dry run.

**Phase to address:** dogfood-build phase, as an explicit success criterion for each of the two
capabilities that declare a `ship:pre` gate (`pr-workflow`, `markdown-linting`) — not deferred to
the public-extraction phase, since a broken gate ships silently.

---

### Pitfall 2: Consent-hash invalidation silently deactivating a capability after a late fix

**What goes wrong:**
gsd-core's project-scope capability consent is a content hash over the whole bundle directory.
Editing *any* file inside an already-consented bundle — including a legitimate late-stage bug fix
— silently deactivates the capability. `render-hooks` just stops naming it; no error is raised.
This repo hit it for real: a post-code-review fix invalidated Phase 1's own `beads` install/consent
11 minutes after the checkpoint closed, and it was caught only because the verifier independently
re-ran `render-hooks` live instead of trusting green tests.

**Why it happens:**
Consent is a snapshot hash, not a semantic diff — the loader has no concept of "this edit doesn't
change behavior," so any bundle mutation post-consent is treated identically to a hostile
substitution. This is fundamental to the consent model, not a bug to be fixed later.

**How to avoid:**
For all three new capabilities, and *especially* if they are built in parallel (their own
milestone goal explicitly allows this — "each dogfooded... then extracted"): re-run
`capability install --scope project` (or the auto-install re-grant mechanism from Phase 10.1,
already vendored in `hooks/capability-auto-install.sh` and `hooks/session-start.sh`) after
**every** edit to a bundle directory, every phase, not just at first install. Treat "did the
capability actually fire on the next lifecycle point" as the verification step, never "did the
manifest validate" or "did tests stay green" — tests don't exercise the consent hash.

**Warning signs:** A capability that worked in an earlier phase silently stops appearing in
`render-hooks` output after any commit touching its bundle directory; no explicit error, just
absence.

**Phase to address:** dogfood-build phase — bake a "re-consent + live render-hooks check" step
into the end of every plan that touches any of the three new bundle directories, not just the
final one before ship.

---

### Pitfall 3: Marketplace `source` type mismatch reintroducing SSH-only clone failures

**What goes wrong:**
`.claude-plugin/marketplace.json` entries using the GitHub-shorthand source
(`{"source": "github", "repo": "owner/repo"}`) clone over SSH unconditionally, regardless of the
user's configured git credential helper — this is documented Claude Code behavior (see
`docs.claude.com/en/plugin-marketplaces` and multiple linked `anthropics/claude-code` issues), not
a bug specific to this repo. This repo hit it for real: installing `ponytail-everywhere` failed
with `Permission denied (publickey)` for a user with no SSH key registered to GitHub, HTTPS-only
via `gh auth`. Fixed (commit `f706179`) by switching both existing plugin entries to
`{"source": "url", "url": "https://github.com/.../....git"}`.

**Why it happens:** The `github` source type has an undocumented (from the caller's perspective)
SSH-clone default baked into Claude Code's plugin installer, independent of the host's actual git
credential configuration.

**How to avoid:** For each of the three new capabilities' eventual `marketplace.json` entries
(public-extraction phase), use the `url` source type with an explicit `https://` git URL, matching
the pattern already fixed for `ponytail-everywhere`/`sota-numerics` — do not copy the `github`
shorthand from any older example or docs snippet. Per current (2026) Claude Code marketplace docs,
`github`, `url`, and `git-subdir` are all valid source *types* at the schema level (this is not a
schema-validity issue), but `github` carries the SSH-default gotcha `url` avoids; MEDIUM confidence
on the exact list of valid source types, since verification relied on community docs
(`ice-ice-bear.github.io`, `cc-marketplace`) rather than a primary Anthropic page fetch — re-verify
against `code.claude.com/en/plugin-marketplaces` directly before the public-extraction phase.
Verify the fix locally exactly as the repo's own commit did: run the install with no SSH key
present, HTTPS-only `gh auth`, before calling `PUB-02`-equivalent done.

**Warning signs:** `Permission denied (publickey)` during `/plugin install` on a machine with no
SSH key registered to GitHub.

**Phase to address:** public-extraction phase (this is a `marketplace.json` concern; the
dogfooded `.gsd/capabilities/<id>/` subdirectory phase never touches `marketplace.json`).

---

### Pitfall 4: External-tool dependency (`gh`, `markdownlint-cli2`) blocking the lifecycle instead of degrading

**What goes wrong:**
Unlike `bd` — already a hard dependency with an established, tested B6 fail-open pattern
("absent, failing or locked degrades to a no-op with one visible notice") — `gh` (for
`pr-workflow`) and `markdownlint-cli2`/Node+npm (for `markdown-linting`) are *new* external-tool
dependencies. A naive port of `beads`'s `steps[]`/`gates[]` shape without also porting its
`onError: skip` + existence-check discipline will hang or hard-fail the lifecycle on a machine
missing `gh` or Node, rather than degrading.

**Why it happens:** It's tempting to assume "the gate predicate machinery already fails safe" —
but the machinery's fail-safety is opt-in per gate (`onError: skip` vs `halt`), and the *step*
side (`plan:pre`/`ship:post` invoking a script that shells out to `gh`/`markdownlint-cli2`) has no
generic fail-open wrapper at all; a script that assumes the binary exists and doesn't check first
just crashes non-zero, and depending on how the step's `onError` is set, that can propagate.

**How to avoid:**
1. Reuse the `command-exists` predicate kind (already used by `review-lane-descriptor.cjs` for
   `gemini`/`claude`/`codex`/`coderabbit`/`opencode`/`qwen` — confirmed live-read in
   `capability-registry.cjs`) as a **gate precondition**, not just inside the wrapped script: gate
   on `command-exists: gh` / `command-exists: markdownlint-cli2` before ever invoking the real
   check, mirroring `sota-numerics`'s own `check-alternatives.py` gate script pattern (`test -f
   "$SOTA_SCRIPT" || { echo ...; exit 1; }` combined with `onError: halt` deliberately reserved
   for the check-command-itself-failing case, never the substantive block decision).
2. Every step/gate that shells out to `gh` or `markdownlint-cli2` declares `onError: "skip"` (the
   only value `beads`'s own step entries use), and the wrapped script itself checks `command -v gh`
   / `command -v markdownlint-cli2` first and exits with a distinguishable "tool absent" message
   rather than a bare non-zero from the tool-not-found shell error.
3. Print exactly one visible notice per missing tool per invocation, matching B6's shape — not a
   silent no-op (undetectable) and not a repeated warning per lifecycle point (noisy).
4. `gh` additionally needs an *auth* check, not just an existence check (`gh auth status`, as
   `ship.md`'s own step 5 preflight already does) — `pr-workflow`'s gate must fail-open on
   "installed but unauthenticated" too, not just "not installed."

**Warning signs:** A phase's `ship:pre` or `plan:pre` hangs or errors opaquely on a machine without
Node/npm or `gh` installed, rather than printing one notice and continuing.

**Phase to address:** dogfood-build phase for each capability individually — this is exactly the
kind of thing that "works on the author's machine" (which has `gh`/Node installed) and only
surfaces on a clean machine, so the public-extraction phase's "fresh clone" verification step
(the same one that caught `PUB-09`'s clean-clone validation) is the right place to *catch* a
regression, but the *design* must be built in from the dogfood phase, not patched in afterward.

---

### Pitfall 5: Unquoted or unvalidated shell invocation in new hook scripts

**What goes wrong:**
The `hooks/capability-auto-install.sh` script shipped with a real bug (CR-01, found by code
review): an unquoted `node` invocation broke on paths containing spaces, and — critically — the
failure mode was not a loud crash but a **silent fail-open to `enabled: true`**, the opposite of
the intended fail-safe direction for a hook that grants capability consent.

**Why it happens:** Shell scripts that build a command line via unquoted variable interpolation
break silently (word-splitting) rather than erroring, and if the script's error handling defaults
"couldn't determine state" to the permissive branch, an environment bug becomes a silent
over-grant.

**How to avoid:** For each of the three new capabilities' hook/gate scripts:
1. Quote every path-bearing shell variable (`"$VAR"`, never bare `$VAR`), matching the fix already
   applied to `capability-auto-install.sh`.
2. Explicitly test the failure direction: a script bug or missing dependency must fail toward the
   *safe* state (capability inactive / gate not enforced / notice printed), never toward "silently
   grant" or "silently pass." Write this as an explicit assertion in the one-file regression test
   (ponytail discipline: non-trivial branch logic needs one runnable check) — run each new hook
   script against a path containing a space as a first-class test case, not an afterthought.
3. Reuse `tests/test-capability-auto-install.sh` as the structural template for the new scripts'
   own regression tests rather than writing test scaffolding from scratch.

**Warning signs:** A hook script that has never been exercised against a path containing a space,
a non-ASCII character, or a symlink; any script whose error path is untested.

**Phase to address:** dogfood-build phase, per capability, at script-authoring time — code review
(the mechanism that caught CR-01 originally) must explicitly check quoting and fail-direction for
every new hook/gate script, not rely on happy-path execution alone.

---

### Pitfall 6: `get-available-resources` behaving differently non-interactively inside a lifecycle hook than as an interactive Claude skill

**What goes wrong:**
The source `get-available-resources` Claude *skill* is designed for interactive agent invocation —
an agent runs the detection script, reads its own stdout/stderr, and can retry or ask the user if
something looks wrong. As a gsd-core capability contribution at `plan:pre`/`execute:wave:pre`
("advisory-only fragment... no gate" per PROJECT.md's Current Milestone section), the same script
now runs unattended inside a lifecycle hook with no human or agent watching its live output for
plausibility — several things that degrade gracefully or get silently retried in the interactive
case become **wrong data baked into `.claude_resources.json` and then trusted downstream**:
- `nvidia-smi` absent or erroring (no GPU, driver mismatch, or — specific to CI/sandboxed
  runners — GPU present on the host but not passed through to the container) produces an empty or
  error string that a naive parser could coerce into "0 GPUs" or crash on, rather than "GPU status
  unknown."
- Restricted `/proc` access in a sandboxed/containerized runner (common in CI) makes
  `/proc/cpuinfo`/`/proc/meminfo`-based core/memory counts silently wrong (e.g. reporting the host's
  full core count when only a cgroup-limited slice is actually available) — a resource strategy
  recommendation ("use joblib with N workers") derived from a wrong core count then gets baked into
  advisory fragments consumed uncritically by the planner/executor.
- No interactive human to notice "huh, that GPU count looks wrong" — the fragment is consumed by
  an LLM agent that has no independent way to sanity-check hardware claims and will treat the JSON
  as ground truth.

**Why it happens:** Interactivity was implicitly part of the original skill's error-handling
contract (a human or agent in the loop provides the sanity check); porting it into a fire-and-forget
lifecycle hook removes that check without replacing it with anything.

**How to avoid:**
1. Every hardware probe (`nvidia-smi`, `/proc/cpuinfo`, `/proc/meminfo`, disk free) must
   distinguish "0" (verified absent) from "unknown" (probe failed/restricted) in the JSON schema —
   never coerce a probe failure into a numeric zero.
2. The advisory fragment text must explicitly hedge on "unknown" fields ("GPU count could not be
   determined — do not assume none is available") rather than presenting a best-effort number as
   fact.
3. Test the script inside an actual restricted/sandboxed environment (a container with `--cpus`
   limits and no GPU passthrough is a reasonable stand-in for the real CI conditions) as part of
   the dogfood-build phase, not just on the author's bare-metal dev machine — this mirrors Pitfall
   4's "works on author's machine" trap, but for hardware detection specifically.
4. Since this contribution point is advisory-only with `onError: skip` expected (matching
   `sota-numerics`'s and `beads`'s contribution pattern), confirm a probe *script* failure (not
   just a missing binary) degrades to "no fragment injected" rather than an empty/wrong
   `.claude_resources.json` silently informing the planner.

**Warning signs:** A resource-strategy recommendation in a plan or execute step that references a
GPU or core count that doesn't match the actual host, with no accompanying "resources could not be
fully determined" caveat.

**Phase to address:** dogfood-build phase — this capability has no `ship:pre` gate to catch it
later (per its own scope, "advisory-only... no gate"), so correctness must be verified at
build time via direct testing in a restricted environment; there is no downstream enforcement
mechanism that would surface a bad resource report at ship time.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|------------------|
| Skipping the "live smoke test against a synthetic gate-input artifact" for a new `ship:pre` gate, trusting the manifest alone | Faster phase close | Repeats Pitfall 1 exactly — a gate that silently never fires, discovered only much later (as `beads`'s did, during Phase 3 planning, not execution) | Never — this repo already paid the cost once per capability; do not re-pay it |
| Copying `github`-shorthand `marketplace.json` entries from an older internal example instead of `url` | Slightly shorter JSON | Reintroduces the SSH-clone failure this repo already fixed once (commit `f706179`) | Never |
| Coercing a hardware-probe failure to `0` instead of `null`/`"unknown"` in `get-available-resources` | Simpler JSON schema, fewer null-checks downstream | Downstream planner/executor treats a probe failure as "verified absent," may recommend wrong resource strategy silently | Never — always distinguish absent from unknown |
| Wrapping `gh`/`markdownlint-cli2` calls without a `command-exists` precondition, relying only on the tool's own non-zero exit | Less code up front | Non-zero exit from "command not found" (127) is indistinguishable from a real check failure (e.g. actual failing PR checks or actual lint violations) unless explicitly probed first | Never — probe first, always |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|-----------------|-------------------|
| `gh` (pr-workflow) | Assuming presence implies auth; gating only on `command -v gh` | Gate on both `command-exists: gh` AND `gh auth status` succeeding (mirrors `ship.md` step 5's existing preflight), fail-open with one notice on either failure |
| `markdownlint-cli2` (markdown-linting) | Assuming it's globally installed; invoking bare `markdownlint-cli2` without checking `npx`/local install path | Probe with `command-exists`, support both a global binary and an `npx markdownlint-cli2` fallback, fail-open with one notice if neither resolves |
| `ship:pre` gate registration (all three) | Trusting the gate fires because `gates[]` is declared in `capability.json` | Verify against the *installed, possibly-patched* `ship.md` directly — the generic dispatch loop is a local patch, not (yet, per this research) a confirmed-merged upstream feature |
| `marketplace.json` git source (public-extraction) | Using `github` shorthand for a new repo entry | Use `url` source type with explicit `https://` URL, per commit `f706179`'s established fix |
| gsd-core capability consent (all three, during parallel build) | Editing a bundle file after consent, assuming the capability stays active | Re-run `capability install --scope project` (or trigger the Phase 10.1 auto-install re-grant) after every bundle edit, every phase |

## Performance Traps

Not applicable at this scope — these are lifecycle-integration capabilities (hook/gate scripts
invoked at most a handful of times per phase), not services with a growth curve. No performance
trap identified beyond correctness/fail-open behavior already covered above.

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Building `gh pr create`/`gh api` command strings from plan/ticket text rather than typed values | Command/argument injection if a plan or PR title ever contains adversarial content — this repo's existing `beads` capability explicitly forbids this exact pattern (N4: "never assembled from artifact text, because the artifact's author and the workflow's runner are frequently different principals") | Apply N4 identically to `pr-workflow`: `gh` invocations built from typed/validated fields only, never raw plan/PLAN.md/PR-description text interpolated into a shell command |
| Interpolating a git ref/branch name (e.g. from `github.ref_name` equivalent, or a user-supplied PR title) directly into a shell `run:` step, mirroring the `release.yml` tag-injection bug this repo already fixed (`08-REVIEW.md` WR-02, commit `b4a7903`) | Classic script-injection via an attacker-controlled ref/branch/title string | Route any such value through `env:` indirection (GitHub Actions) or explicit shell quoting/allowlist validation (local scripts), never direct `${{ }}`/`$VAR` interpolation into a `run:` command string |
| `get-available-resources`' JSON output consumed uncritically as ground truth by the planner (per Pitfall 6) | Not a classic security issue, but a trust-boundary issue: an LLM agent making resource-allocation decisions from unverified hardware claims | Hedge/mark "unknown" fields explicitly; do not let a probe failure masquerade as a verified low-resource state that could, e.g., wrongly justify skipping a safety check "because resources are constrained" |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-------------------|
| Silent no-op when `gh`/`markdownlint-cli2` is absent (no notice at all) | User has no idea the PR-check gate or lint report simply never ran; false confidence | Print exactly one visible notice per missing tool per invocation, matching the already-established B6 pattern |
| Repeated identical "tool missing" notice at every lifecycle point in a phase | Notice fatigue, user starts ignoring warnings generally | One notice per *tool* per *phase run*, not per hook invocation — dedupe within a session |
| A `ship:pre` gate that appears in `capability.json` but never actually fires (Pitfall 1) with no indication to the user | User believes PR checks or lint status are gating ship, when they are not | Explicit, visible confirmation the gate fired (pass or block message), never silent pass-through |

## "Looks Done But Isn't" Checklist

- [ ] **`pr-workflow`'s `ship:pre` gate:** Manifest declares `gates[]` — verify it actually appears
  in `gsd_run loop render-hooks ship:pre --raw`'s `activeHooks`, AND that the installed `ship.md`
  carries the generic-dispatch patch (or upstream-merged equivalent) that would process it.
- [ ] **`markdown-linting`'s `ship:pre` gate:** Same as above — a second capId hitting the same
  dispatch path is not automatically covered just because `beads`'s and `sota-numerics`'s gates
  were previously verified; verify per-capId, since the dispatch loop is generic but each gate's
  own predicate/artifact wiring is not.
- [ ] **Fail-open behavior for `gh`/`markdownlint-cli2`:** Don't just check "does it work when the
  tool is installed" — explicitly uninstall/rename the binary and re-run the lifecycle point,
  confirming exactly one notice and no hang/crash.
- [ ] **`get-available-resources`' non-interactive correctness:** Don't just check "does the script
  run and produce JSON" — check that a probe *failure* (not just probe success) produces an
  explicit "unknown," not a coerced zero or crash.
- [ ] **`marketplace.json` entries (public-extraction phase):** Don't just check "does
  `claude plugin validate --strict` pass" — actually install from a machine with no SSH key
  registered, HTTPS-only auth, matching the repo's own established verification standard for the
  two existing extracted plugins.
- [ ] **Consent-hash currency:** After the *last* edit to each bundle directory before a phase is
  marked complete, re-run `capability install --scope project` (or confirm auto-install re-grant
  fired) and independently re-run `render-hooks` — do not trust that an earlier consent grant in
  the same phase is still valid.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|-----------------|-------------------|
| Gate silently not firing (Pitfall 1) discovered after phase claimed complete | MEDIUM | Re-verify installed `ship.md` for the patch marker; if absent, either re-apply the machine-local patch (as done for Phase 3) or block on upstream #3559 merging; re-run the smoke test before re-closing the phase |
| Capability silently deactivated post-consent (Pitfall 2) | LOW | Re-run `capability install --scope project`; re-run `render-hooks` to confirm the capId reappears; no data loss, just a missed lifecycle point that must be manually caught up if it already happened |
| SSH-clone failure on `marketplace.json` install (Pitfall 3) | LOW | Switch the entry's `source` to `url` type, exactly as commit `f706179` did; no data migration needed |
| External tool absent breaking (not degrading) the lifecycle (Pitfall 4) | LOW–MEDIUM | Add the missing `command-exists` precondition and `onError: skip`; retroactively confirmed safe the same way `beads`'s B6 pattern was |
| Unquoted shell variable breaking on a space-containing path (Pitfall 5) | LOW | Quote the variable, add the regression test case, matching the `capability-auto-install.sh` CR-01 fix exactly |
| Wrong resource data baked into a fragment already consumed by a planner/executor (Pitfall 6) | MEDIUM | No automated recovery — requires manually identifying which plans/decisions consumed the bad fragment and flagging them for re-review; expensive precisely because there's no gate to catch it after the fact, reinforcing why build-time correctness is the only real defense |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|----------------|
| 1. Unpatched `ship:pre` dispatch | dogfood-build (per capability with a gate) | Live `gsd_run check predicate` smoke test against a synthetic gate-input artifact + confirmation of the installed `ship.md` patch marker |
| 2. Consent-hash invalidation | dogfood-build (every phase touching a bundle dir) | `render-hooks` re-run after every bundle edit, capId presence confirmed in output |
| 3. `marketplace.json` SSH-clone gotcha | public-extraction | Real `/plugin install` from a machine/session with no SSH key, HTTPS-only `gh auth` |
| 4. External-tool fail-open (`gh`, `markdownlint-cli2`) | dogfood-build (design), public-extraction (fresh-clone catch) | Deliberately remove/rename the binary, re-run the lifecycle point, confirm one notice + no hang |
| 5. Unquoted shell invocation in new hook scripts | dogfood-build (script authoring + code review) | Regression test against a path containing a space, per script, matching `test-capability-auto-install.sh`'s structure |
| 6. `get-available-resources` non-interactive correctness | dogfood-build (no later gate exists to catch this) | Run inside a restricted/sandboxed container (cgroup CPU limit, no GPU passthrough), confirm "unknown" fields are hedged, not coerced |

## Sources

- `/home/dd/projects/gsd-beads/.planning/PROJECT.md` — Key Decisions table (primary source for
  Pitfalls 1, 2, 3, 5; HIGH confidence, first-party documented incident history)
- `/home/dd/projects/gsd-beads/.gsd/capabilities/beads/capability.json` (live-read) — gate/step
  shape, `onError: skip` convention, `ship_gate` predicate pattern
- `/home/dd/projects/gsd-beads/.gsd/capabilities/sota-numerics/capability.json` (live-read) —
  `onError: halt` vs `skip` distinction, `command-exit-zero` gate script existence-check pattern
- `$HOME/.claude/gsd-core/workflows/ship.md` (live-read, lines 94-240) — confirms the generic
  `ship:pre` dispatch patch is present and how it processes non-security/broken-windows gates;
  HIGH confidence, primary source, but the patch's upstream-merge status is unverified beyond
  PROJECT.md's own "filed" (not "merged") language
- `$HOME/.claude/gsd-core/bin/lib/capability-registry.cjs`,
  `$HOME/.claude/gsd-core/bin/lib/review-lane-descriptor.cjs` (live-read/grep) — confirms
  `command-exists` predicate kind is an established, reusable mechanism for external-tool
  detection
- git commit `f706179` ("fix(marketplace): use url source type, not github shorthand, for both
  plugins") — primary source for Pitfall 3, includes citations to
  `anthropics/claude-code#52234/#49875/#47088/#26588/#31930/#27771/#28012`
- [Create and distribute a plugin marketplace - Claude Code Docs](https://code.claude.com/docs/en/plugin-marketplaces) —
  MEDIUM confidence corroboration for current `source` type schema (not independently re-fetched
  in full during this research pass; re-verify directly before the public-extraction phase)
- [Claude Code Plugin Marketplace: A Deep Dive](https://ice-ice-bear.github.io/posts/2026-04-03-claude-code-plugin-marketplace/) —
  community source, MEDIUM confidence, corroborating detail on `github`/`url`/`git-subdir` source
  types and `sha`-pinning
- `/home/dd/projects/gsd-beads/hooks/capability-auto-install.sh`,
  `/home/dd/projects/gsd-beads/tests/test-capability-auto-install.sh` (located, not fully
  read line-by-line — referenced as the existing regression-test template for Pitfall 5)

---
*Pitfalls research for: gsd-core capability plugins (pr-workflow, markdown-linting,
get-available-resources) added to gsd-beads*
*Researched: 2026-08-18*
