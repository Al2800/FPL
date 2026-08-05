# 11 — Scheduled evidence/challenger runs in the deadline cycle

Status: needs-triage
Type: task
Track: Phase 2/3 (automate the AI overlay)
Blocked by: 02, 10

Activation gate: Phase 2/3 scheduled agent operation must be explicitly
authorised. Ticket 10 (5 August 2026) **declined** an API arm (ADR-0024); this
ticket uses the subscription-hosted Codex path on the always-on local host.

## Context

Evidence and challenger agents are currently manual: `agent_arm.py` builds hash-bound requests, a human runs the model, and `materialize_*_response.py` scripts validate the output. For a live engine the overlay must run inside the §15.3 schedule (T-48h initial, T-8h availability refresh, T-2h final) with the T-90m deterministic fallback.

Windows Scheduler already runs daily subscription Codex lanes
(`docs/data-sources/chatgpt-agent-windows-scheduler.md`). Ticket 11 extends that
pattern to deadline-cycle evidence/challenger stages without introducing API keys.

## Scope

- Wire the evidence agent and challenger review into the `run_gameweek`
  orchestrator as scheduled stages on the **subscription Codex** surface
  (ADR-0021), not an API provider.
- Enforce unchanged guarantees: proposal-only adjustments through the governed
  policy, schema validation, citations/expiry, challenger escalation, T-90m
  degrade to deterministic plan.
- Budgets per ADR-0016/0024 (wall-clock; currency unavailable).
- Record full traces (JSONL by run ID, ADR-0010).

## Done when

- A live GDR shows agent-proposed, policy-accepted adjustments with citations,
  produced without human interaction on the subscription host, and a
  forced-timeout test demonstrates clean degradation to the deterministic plan.

## Boundaries

LLMs propose only. No execution authority, no rule enforcement, no secrets in
prompts, no API keys.
