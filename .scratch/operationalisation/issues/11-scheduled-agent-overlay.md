# 11 — Scheduled evidence/challenger runs in the deadline cycle

Status: resolved
Type: task
Track: Phase 2/3 (automate the AI overlay)
Blocked by: 02, 10

Activation gate: Phase 2/3 scheduled agent operation must be explicitly
authorised. Ticket 10 (5 August 2026) **declined** an API arm (ADR-0024); this
ticket uses the subscription-hosted Codex path on the always-on local host.

Owner authorised implementation on 6 August 2026.

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

## Answer

Implemented the deadline-cycle overlay on the subscription sol path without API
keys:

- `control/policies/scheduled-agent-overlay-v1.json` — T-48h / T-8h / T-2h stages
  with ADR-0016 budgets and a hard T-90m cutoff
- `src/orchestration/scheduled_agent_overlay.py` — stage planner, forced-timeout
  host envelope, arm runner, GDR attach
- `src/orchestration/agent_trace.py` — ADR-0010 JSONL traces under
  `reports/traces/{run_id}.jsonl`
- `run_gameweek(..., agent_overlay=...)` attaches citations / degrade reasons;
  deterministic optimiser remains authoritative on timeout or T-90m
- `scripts/run_scheduled_agent_overlay.py` +
  `docs/data-sources/scheduled-agent-overlay.md` for unattended materialise /
  forced-timeout offline path

Tests: `tests/orchestration/test_scheduled_agent_overlay.py` (forced timeout →
deterministic fallback + JSONL) and
`tests/integration/test_run_gameweek.py::test_run_gameweek_agent_overlay_timeout_marks_degraded`.
