# Forensic Report: Does GitHub #8 (Codex plugin cache deletion) apply to Claude Code?

**Generated:** 2026-09-02T00:26:00+02:00
**Problem:** GitHub #8 documents Codex 0.152.0 deleting versioned `beads-lifecycle` plugin cache
directories (1.4.1, 1.5.0) out from under running sessions, causing `PostToolUse` hook exit 127.
Question: does the same failure mode exist in Claude Code's plugin/marketplace mechanism?

This report supersedes nothing in `report-20260902-001902.md` (the broader Phase 19-21 production
incident report, which already covers the Codex-side failure in depth). This report adds one new,
directly-observed finding: a live comparison of Claude Code's plugin cache to Codex's.

---

## Evidence Summary

### Codex cache (per GitHub #8, `.wolf/buglog.json`)

- Single mutable cache path per plugin, versioned by directory name under
  `~/.codex/plugins/cache/gsd-beads/beads-lifecycle/<version>/`.
- `codex plugin marketplace upgrade` / `codex plugin add` **delete** the superseded version
  directory as part of installing the new one.
- No reference count, lease, or grace period — deletion is unconditional on install.
- A running session that resolved its hook command to an absolute path inside the deleted
  version directory (e.g. `.../1.4.1/hooks/lifecycle-dispatch.sh`) gets `No such file or
  directory`, exit 127, on every subsequent `PostToolUse` invocation.

### Claude Code cache (directly inspected this session, `~/.claude/plugins/`)

```
~/.claude/plugins/cache/gsd-beads/beads-lifecycle/
  1.5.1/   .in_use/3405496   (no .orphaned_at — active)
  1.5.0/   .orphaned_at = 1788298810660  (2026-09-01 23:40:10)
  1.4.1/   .in_use/  (empty dir) + .orphaned_at = 1788299634604 (2026-09-01 23:53:54)
  1.4.0/   .orphaned_at = 1787446292498  (2026-08-23 02:51:32)
  1.2.2/   (no lease markers)
  1.2.1/   (no lease markers)
```

`~/.claude/plugins/cache/gsd-beads/beads-lifecycle/1.5.1/.in_use/3405496` contains:

```json
{"pid":3405496,"procStart":"25614041"}
```

`ps -eo pid,ppid,comm` confirms PID 3405496 is a live `claude` process on this host right now.

`~/.claude/plugins/.last_inuse_sweep` = `2026-08-31T23:39:00.030Z` — a periodic sweep timestamp,
consistent with a background reaper that only removes a version directory after it has been
`.orphaned_at`-marked **and** carries no live `.in_use/<pid>` lease.

Hook commands inside the plugin manifest never bake an absolute path:

```json
{"command":"bash \"${CLAUDE_PLUGIN_ROOT}/hooks/lifecycle-dispatch.sh\"", ...}
```

`installed_plugins.json` records one current pointer (`installPath`) per plugin, but multiple
prior version directories persist on disk simultaneously — they are not deleted at install time.

## Finding

**Confidence: 95/100** (direct filesystem inspection of markers and one live-process
cross-check; the sweep/reaper code itself was not read — its existence is inferred from the
`.orphaned_at` + `.last_inuse_sweep` + `.in_use/<pid,procStart>` marker triad, which is otherwise
inexplicable).

Claude Code's plugin cache already implements, on disk, the exact mechanism GitHub #8 asks
Codex to build:

1. **Keeps every referenced version, not just the latest.** 1.5.0, 1.4.1, 1.4.0, 1.2.x are all
   still present after 1.5.1 was installed.
2. **Cross-process lease, keyed by PID + process-start-time** (`.in_use/<pid>` →
   `{"pid":...,"procStart":...}`), which also guards against PID-reuse races — a detail GitHub
   #8's proposed design ("cross-process lease or reference tracking") does not even specify.
3. **Orphan-then-sweep, not delete-on-install.** A superseded version is marked
   `.orphaned_at` at install time (staged for removal) but the directory itself is not deleted
   then; a separate sweep (`.last_inuse_sweep`) reaps it later, presumably only once no
   `.in_use/<pid>` lease remains for that version.
4. **Hook commands never resolve to a version-specific absolute path in the manifest** —
   `${CLAUDE_PLUGIN_ROOT}` is a placeholder substituted at invocation time, one further layer of
   indirection than Codex's apparent baked-absolute-path model.

## Answer to "does this also apply to Claude Code?"

**No — not as observed.** The specific failure (`rm` on install racing a live session's absolute
hook path, exit 127) requires the two design choices GitHub #8's "How" section asks Codex to
add: (a) version retention while leased, (b) deletion only after lease release. Claude Code's
cache already has both, live, on this machine, right now (PID 3405496 is holding a real lease on
1.5.1 while 1.5.0/1.4.1/1.4.0 sit orphaned-but-undeleted next to it).

This is evidence of Claude Code's current behavior on one host at one point in time, not proof of
an absence of *all* related bugs (e.g., an unbounded sweep race is not ruled out — the reaper's
source was not read). It's also not proof the same protection existed in past Claude Code plugin
CLI versions.

## Recommended Actions

1. Do not widen GitHub #8's scope to Claude Code — no reproducing evidence exists, and the
   mechanism it asks for already appears present there. Keep #8 scoped to Codex.
2. If durable confirmation is wanted, add a short note to #8 (or a comment, not a scope change)
   pointing at Claude Code's `.in_use`/`.orphaned_at`/`.last_inuse_sweep` design as a reference
   implementation for the fix Codex needs — useful prior art for whoever picks up #8's "How".
3. No corrective action needed on the Claude Code side from this investigation.

---

*Report generated by `/gsd-forensics`. Absolute home paths redacted where not evidentiary.*
