# Capability Config Architecture — research for milestone v1.3

**Question:** How does capability config actually work in gsd-core, and what does that imply for
`beads.sync_mode` — a declared enum that no code reads?

**Verified against:** installed gsd-core **1.11.0** (`~/.claude/gsd-core/VERSION`), plus the shipped
marketplace tree at `~/.claude/plugins/marketplaces/gsd-core/`, plus one live upstream doc fetch.
Every mechanism claim below carries a `file:line` or a URL. Claims tagged **(inferred)** are not
directly executed code.

**Bottom line:** a capability's `config` block is a *schema + default + write-time validator*. It is
**not** a delivery channel — the value never reaches a `step` hook. `beads.sync_mode` therefore has
no wiring to be "finished"; it has a declaration to be corrected. Recommendation: **(a) narrow the
declaration to `["authoritative"]`**. Migration for an existing `"mirror"`/`"off"` is a no-op on
disk plus one release-note line, because gsd-core performs **zero read-time validation**.

---

## 1. What the `config` block actually does — three things, none of them "hand the value to a hook"

### 1.1 It federates the key into the composed registry `configSchema`

`capability-loader.cjs:440` reads the first-party `configSchema` and merges accepted overlay
capabilities into it. Verified live on this project — the composed schema carries all four beads
keys with `owner: "beads"`:

```
beads.sync_mode {"owner":"beads","type":"enum","default":"authoritative",
                 "values":["authoritative","mirror","off"], "description":"…"}
```
(executed: `loadRegistry({includeInstalled:true, cwd:'/home/dd/projects/gsd-beads'})`)

Consequence: `isValidConfigKey` (`config-schema.cjs:44-48, 63-67`) accepts `beads.sync_mode` as a
settable key. **Confidence 98.**

### 1.2 It supplies the level-4 default in the config precedence walk

`capability-activation.cjs:71-103` — `resolveConfigKey(dotKey, {config, cwd, registry})`:

| Level | Source | Line |
|---|---|---|
| 1 | `loadConfig(cwd)` result, guarded nested lookup | `capability-activation.cjs:74-76` |
| 2 | `planningDir(cwd)/config.json` raw read | `:79, 81-83` |
| 3 | `planningRoot(cwd)/config.json` raw read (only if path differs) | `:80, 84-88` |
| 4 | `registry.configSchema[dotKey].default` | `:90-100` |
| 5 | absent → `{found:false}` | `:102` |

Verified empirically: with no `beads.sync_mode` on disk, `gsd-tools config-get beads.sync_mode`
returns `authoritative` — i.e. level 4 fires and the key reports as live even when unset.
**Confidence 98.**

### 1.3 It backs **write-time** enum enforcement in `config-set`

`config.cjs:805-813` — generic capability-registry validation, added by upstream #1628:

```js
const capDef = getCapabilityConfigSchema(cwd)[kp];
if (capDef && typeof capDef.type === 'string') {
  switch (capDef.type) {
    case 'enum':
      if (Array.isArray(capDef.values))
        assertEnumValue(parsedValue, val, capDef.values.map(String), kp);
```

Executed in this repo (and reverted — `git status --porcelain .planning/config.json` is clean):

```
$ gsd-tools config-set beads.sync_mode mirror   → beads.sync_mode=mirror   (accepted, written)
$ gsd-tools config-set beads.sync_mode bogus    → Error: Invalid beads.sync_mode 'bogus'.
                                                   Valid values: authoritative, mirror, off
```

So today gsd-core **actively invites** the user to set `mirror`, then silently ignores it.
**Confidence 99.**

**That is the entire contract.** There is no fourth thing. The declaration does not cause the value
to be passed anywhere.

---

## 2. `configValues` reaches **contributions only** — never steps, never gates

`loop-resolver.cjs:175-192` defines `resolveConfigValues(hook)`, which maps a hook's declared
`configValues: { alias: "dotted.key" }` through `resolveConfigKey` and returns raw (uncoerced)
values. It is called at exactly **one** site:

- `loop-resolver.cjs:244` — inside the **contributions** loop, attached at `:258-259`.

The steps loop (`:196-226`) and the gates loop (`:265-287`) never call it. A step hook's emitted
shape is fixed at `:212-225`: `capId, kind, ref, fragment, when, produces, consumes, onError`.
The `when` string is echoed **verbatim as a string** (`:207, 217`) — not resolved, not evaluated in
the payload. **Confidence 99.**

### The one first-party consumer, end to end

Producer — `capability-registry.cjs:3436-3446` (security capability, `plan:pre` contribution):

```json
"configValues": {
  "security_asvs_level": "workflow.security_asvs_level",
  "security_block_on": "workflow.security_block_on"
}
```

Consumer — `workflows/plan-phase.md:418`:

> Read `SECURITY_ASVS` from the active hook's `configValues.security_asvs_level` (default: `1`) …
> These values are resolved by the capability registry from user config using the same four-level
> precedence as hook activation — **no inline `config-get` is needed.**

That last clause is the design intent stated in gsd-core's own prose: `configValues` exists so a
consumer does **not** re-read config. It is available only to contributions. **Confidence 97.**

### Live proof for beads

`gsd-tools loop render-hooks plan:post --raw`, run in this repo:

```json
{ "capId": "beads", "kind": "step", "ref": {"skill":"beads-sync"},
  "when": "beads.enabled", "produces":["PLAN.md"], "consumes":["PLAN.md"], "onError":"skip" }
```

No `configValues` field, and no mechanism to add one — beads' six hooks are all `steps` (five) and
`gates` (two), plus one `contribution` at `plan:pre` (`capability.json:141-155`). Only that single
`plan:pre` recall contribution could ever carry `configValues`, and `beads-sync` (the only place
`sync_mode` would matter) is a **step**. **Confidence 96.**

---

## 3. How `when:` is evaluated — boolean coercion, so it cannot express an enum

`loop-resolver.cjs:126-135` → `_resolveActivationValue(when, config, cwd, registry)` →
`capability-activation.cjs:104-107`:

```js
function _resolveActivationValue(dotKey, config, cwd, registry) {
    const r = resolveConfigKey(dotKey, { config, cwd, registry });
    return r.found ? Boolean(r.value) : false;   // ← Boolean coercion
}
```

`when` takes a **dotted key only** — no operators, no comparison, no expression grammar. Confirmed
by the manifest reference: *"Dotted config key; the step is active only when the key is truthy"*
(`docs/reference/capability-manifest.md:83`, `:97`, `:110`).

**Hard consequence:** `when: "beads.sync_mode"` would be truthy for **all three** values, including
the string `"off"` (a non-empty string coerces to `true`). An enum key is structurally unusable as a
`when`. **Confidence 99.**

### The `config-equals` gate predicate does not exist in 1.11.0

`capability-manifest.md:117` lists `"config-equals"` among predicate kinds. The shipped evaluator
disagrees — `gate-predicate-evaluator.cjs:37`:

```js
const EVALUATOR_KINDS = Object.freeze(['command-exit-zero', 'artifact-frontmatter-equals']);
```

An unknown kind throws (`:188-190`). So `config-equals` is **documented but unimplemented**. There
is currently **no declarative way anywhere in gsd-core to branch on a config value's content** —
only on its truthiness. **Confidence 97.**

### Therefore: a capability must re-read config itself

That is exactly what beads already does — `scripts/sync.py:641-676`, `read_beads_config()` reads
`.planning/config.json` fresh on every call, with the docstring stating why:

> entering from a harness hook bypasses both the SKILL.md Step 1 config gate **and the capability
> registry that evaluates each hook's `when`**.

This is not a workaround. For a step-based capability it is the **only** available mechanism, and
first-party capabilities do the same (see §6). **Confidence 95.**

---

## 4. Read-time validation: **none**

`resolveConfigKey` returns the raw on-disk value with no membership check
(`capability-activation.cjs:71-103`). Verified empirically in a scratch project whose
`.planning/config.json` contained a stale out-of-enum value **and** an entirely undeclared key:

| Read | On disk | Result |
|---|---|---|
| `config-get beads.sync_mode` | `"mirror"` | `mirror` — returned, no warning |
| `config-get beads.bogus_key` (undeclared) | `"zzz"` | `zzz` — returned, no warning |
| `config-get totally.unknown` (undeclared namespace) | `"yes"` | `yes` — returned, no warning |

The health rule that validates config values,
`bin/lib/health-diagnostic-rules/config-validation.cjs`, checks exactly two hardcoded **central**
keys — `model_profile` (`:103`) and `git.branching_strategy` (`:153`). It performs no
capability-schema enum check and no orphan-key detection. A repo-wide grep for orphan/unknown-key
detection hits only `config.cjs` and `config-loader.cjs`, both on the **write** path.

**Answer to Q4:** an unknown or out-of-enum value is **rejected at `config-set`, passed through
silently on every read**. Nothing warns; nothing errors; nothing strips it. **Confidence 97.**

---

## 5. Deprecation / migration path for a capability config key: **undocumented and unimplemented**

- Upstream `docs/reference/capability-manifest.md` (live fetch, raw.githubusercontent.com/open-gsd/
  gsd-core/main): **no** deprecation, removal, or enum-narrowing policy for federated `config` keys.
  The page *does* document a deprecation lifecycle where one exists (`reviewerCli` "survived one
  release (1.9.0 → 1.10.0) as a derived legacy alias"), so the omission is real, not an oversight of
  the fetch. **Confidence 90.**
- `~/.claude/gsd-core/references/` — no capability-config deprecation reference. The only migration
  prose is for a **central** key: `planning-config.md:397`, `depth` → `granularity`, "automatically
  migrated … and persisted back to disk."
- The migration machinery exists but is **central-schema only**: `cmdMigrateConfig`
  (`config.cjs:1121-1141`) delegates to `configuration.cjs migrateOnDisk()`, which applies "all four
  legacy-key migrations" — a fixed first-party list. There is no capability-supplied migration hook
  and no `installer-migrations/` entry for a capability config key (`010` entries `000`–`009` are
  install-surface migrations only). **Confidence 92.**
- gsd-core's own stated house rule on removal, `capability-validator.cjs:1719-1726`: unknown fields
  **WARN, never error**, because an error "would hard-break an out-of-tree descriptor … with no
  deprecation window — the exact mistake #2801's own alias removal spent a full release avoiding."

**The available migration lever** is `config-set <key> null`, the documented "clear" action which
*deletes* the key rather than persisting `null` (`config.cjs:684-700`). Verified:
`config-set beads.sync_mode null` → `beads.sync_mode unset`, key removed from disk.

---

## 6. Is declared-but-unread config common in first-party gsd-core? **No — zero cases.**

Scanned all **62** first-party `configSchema` keys against: `"when"` references in
`capability-registry.cjs`, `configValues` blocks, and the full text of gsd-core workflows,
references, contexts, templates, `bin/lib/*.cjs`, `bin/shared/*`, plus the entire marketplace tree
(skills, commands, docs, scripts, capability manifests).

**Result: 0 of 62 unreferenced.**

An intermediate scan restricted to the `~/.claude/gsd-core/` runtime tree flagged 11 keys
(8 × `mempalace.*`, 3 × `external_job.*`). All 11 are read — by the capability's **own** artifacts
outside the runtime tree:

- `mempalace.memory_mode` etc. → `~/.claude/skills/gsd-mempalace-recall/SKILL.md`,
  `gsd-mempalace-capture/SKILL.md`
- `external_job.artifact_dir` etc. → `marketplaces/gsd-core/scripts/slurm-adapter.cjs`

That is precisely the `sync.py:read_beads_config` pattern — **first-party capabilities read their own
federated keys from their own skill/script, not from the loop envelope.** This corroborates §3.
**Confidence 88** (scan is text-matching over a large corpus; a dynamically-composed key string
would be missed).

`beads.sync_mode` is, on this project's composed registry, the **only** key nothing reads. It is an
anomaly, not a sanctioned pattern. **Confidence 90.**

One adjacent precedent worth noting for tone: `mempalace.memory_mode` ships three enum values and its
doc entry openly states "Cross-mode migration of existing `.planning/graphs/` into the palace is a
separate, not-yet-implemented concern" (`docs/CONFIGURATION.md:739`). Partial enum support is
survivable upstream **when the doc says so**. `beads.sync_mode` does the opposite — its description
claims the reserved values are "reserved for later phases" while `config-set` accepts them as valid
today. **Confidence 85.**

---

## 7. Decision input for the planner

### Cost of each option

| Option | Work | Residual risk |
|---|---|---|
| **(a) Narrow to `["authoritative"]` + doc** | 1-line `values` edit in `capability.json`; description rewrite; release note. No code. | None mechanical. Users who set `mirror` get a *new* `config-set` rejection — which is the desired signal. |
| **(b) Implement `mirror` / `off`** | Cannot use `when` (§3 — enum is untypeable as a `when`). Cannot use `configValues` (§2 — `beads-sync` is a step). Requires a new `read_beads_config(root,"sync_mode","authoritative")` accessor plus three behavioral branches in `sync.py` and a semantic definition of what `mirror` *means* for a bd database. Plus tests for each mode. | Large; and `off` overlaps `beads.enabled=false`, which already exists (`capability.json:27-31`) and already gates all six hooks. **`off` is a duplicate of an implemented key.** |
| **(c) Drop the key** | Remove from `capability.json`. | `config-set beads.sync_mode …` then fails with `Unknown config key` — a *worse* message than an enum rejection, and it loses the record that the semantics ("bd is authoritative after first sync", D-01) are a deliberate decision. That semantic is real and documented in `sync.py:1300-1302`; deleting the key deletes its only user-visible statement. |

**Cheapest-correct: (a).** It costs one JSON edit, it turns the currently-silent failure into an
explicit `config-set` rejection naming the one valid value, and it preserves the D-01 semantic
statement. Option (b) buys behavior nobody asked for and duplicates `beads.enabled`. Option (c)
throws away a correct piece of documentation to fix a wrong one.

### Migration answer for a project that already set `"mirror"` or `"off"`

**Nothing breaks, and nothing needs to run.** Grounded in §4:

1. The stale value stays on disk and every read path (`resolveConfigKey`, `config-get`,
   `sync.py:read_beads_config`) returns it without validation or warning
   (`capability-activation.cjs:71-103`; empirically confirmed).
2. Because nothing reads `sync_mode`, the stale value has never had an effect and will not acquire
   one. Behavior after narrowing is byte-identical to behavior before.
3. The only observable change: a *future* `gsd-tools config-set beads.sync_mode mirror` now fails
   with `Invalid beads.sync_mode 'mirror'. Valid values: authoritative` (`config.cjs:805-813`).
4. Optional cleanup, if a release note wants to offer one — `gsd-tools config-set beads.sync_mode
   null` deletes the key (`config.cjs:684-700`, verified). **Do not** ship an automated migration:
   there is no capability-migration hook (§5), and writing one would be new machinery for a no-op.

**Ship the migration as one release-note sentence, not as code.** Confidence 93.

### Correctness note that belongs in the same commit

`capability.json:40`'s description currently asserts `mirror`/`off` are "reserved for later phases"
while `config-set` accepts them as valid *now*. Whichever option is chosen, that sentence is the
false claim doing the actual damage — the enum `values` array is documented upstream as the
**"Exhaustive list of permitted string values"** (`capability-manifest.md`, `config` table), not as
a roadmap.

---

## Confidence summary

| Finding | Confidence | Basis |
|---|---|---|
| `config` block = schema + level-4 default + `config-set` validator, nothing more | 98 | `capability-loader.cjs:440`, `capability-activation.cjs:71-103`, `config.cjs:805-813`; executed |
| `configValues` reaches contributions only, never steps/gates | 99 | `loop-resolver.cjs:244` (sole call site) + live `render-hooks plan:post` |
| `when:` is boolean-coerced; enums are untypeable as `when` | 99 | `capability-activation.cjs:104-107` |
| `config-equals` predicate documented but not implemented | 97 | `gate-predicate-evaluator.cjs:37` vs `capability-manifest.md:117` |
| Zero read-time validation of config values | 97 | executed 3-case scratch test + `config-validation.cjs:103,153` |
| No documented deprecation/migration path for capability config keys | 90 | live upstream fetch + `references/` grep + `config.cjs:1121` scope |
| 0 of 62 first-party keys declared-but-unread | 88 | text scan of gsd-core + full marketplace tree |
| Capabilities re-read their own keys from their own scripts (first-party norm) | 88 | mempalace SKILL.md, `slurm-adapter.cjs`; matches `sync.py:641` (inferred pattern) |
| Migration for stale `mirror`/`off` is a documentation no-op | 93 | follows from read-time-validation finding |
