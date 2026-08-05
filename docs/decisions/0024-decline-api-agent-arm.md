# ADR-0024: Decline API-backed agent arm; schedule subscription host

**Status:** Accepted  
**Date:** 2026-08-05  
**Amends:** ADR-0016  
**Related:** ADR-0021  
**Decides:** Operationalisation ticket 10  
**Owners:** Alastair

## Context

Open Decision 8 / ADR-0021 selected `gpt-5.6-sol` on the ChatGPT-subscription
Codex surface (no API key). Ticket 10 asked whether to authorise a metered
API-backed arm for unattended evidence/challenger runs. The owner’s execution
machine is always on and already runs subscription Codex tasks via Windows
Scheduler (`docs/data-sources/chatgpt-agent-windows-scheduler.md`).

## Decision

1. **Decline** an API-backed provider arm for now.
2. Scheduled evidence/challenger automation (ticket 11) uses the **existing
   subscription-hosted Codex path** on the always-on local host, with ADR-0016
   wall-clock / T-90m degrade rules. Currency remains **unavailable** (not
   zero) because the subscription surface has no reliable per-run meter.
3. Secrets stay out of Git and model context. No new API keys are introduced by
   this decision.
4. Revisit an API arm only if metered caps or non-local scheduling become
   necessary — via a further ADR.

## Consequences

Ticket 11 is re-scoped to schedule the subscription/deterministic overlay, not
to require an API provider. ADR-0021 remains the model/surface decision.
