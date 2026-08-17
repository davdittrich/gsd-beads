# Phase 10.1 — API Coverage Declaration

No external API integration: this phase's only outbound call is to the project's own
already-installed local CLI (`gsd-tools.cjs capability install`) from a bash SessionStart
hook — no third-party API, SDK, HTTP service, or network surface is touched, and the phase
adds zero new external packages (see RESEARCH.md "Package Legitimacy Audit").

The `api-coverage` detector fires on the words `install` / `hook` in this phase's scope;
those refer to a local capability-bundle install and a Claude Code process hook, not to an
external API. No capability matrix applies.
