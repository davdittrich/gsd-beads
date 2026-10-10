An open-issue recall for this phase — `BEADS-RECALL.md` — was just attempted in this phase's own
directory (`.planning/phases/<this-phase>/<NN>-BEADS-RECALL.md`, where `<NN>` is the phase's
two-digit ordinal prefix). Read `BEADS-RECALL.md` before finalizing this phase's task scope, and
check its `recall_status` frontmatter key first:
- `recall_status: ok` — the file names every currently open bd task that scope-matched this
  phase, plus a separate Unscoped heading for everything that could not be confidently matched but
  was never dropped. Trust it.
- `recall_status: failed` — this run's recall did not complete (see `recall_error`); the file
  holds no current data. Do not treat its contents as this phase's open-issue scope.
