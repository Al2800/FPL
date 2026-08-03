# 11 — Scheduled evidence/challenger runs in the deadline cycle

Status: ready-for-agent
Type: task
Track: D (automate the AI overlay)
Blocked by: 02, 10

## Context

Evidence and challenger agents are currently manual: `agent_arm.py` builds hash-bound requests, a human runs the model, and `materialize_*_response.py` scripts validate the output. For a live engine the overlay must run inside the §15.3 schedule (T-48h initial, T-8h availability refresh, T-2h final) with the T-90m deterministic fallback.

## Scope

- Wire the evidence agent (news/`chance_of_playing`/`news_added` deltas, press-conference claims from registered sources) and challenger review into the `run_gameweek` orchestrator as scheduled stages, using the provider arm authorised in ticket 10.
- Enforce the existing guarantees unchanged: proposal-only adjustments through the governed policy (`control/policies/evidence-adjustments-v2.yaml`), schema validation via `hosted_response.py`-equivalent linting, citations and expiry on every claim, challenger escalation outcomes (§13.4) blocking auto-approval when unresolved.
- Budgets and timeouts per stage recorded in the GDR (§13.5); overrun degrades to the deterministic plan and marks the record degraded.
- Record full traces (JSONL by run ID, ADR-0010) so live agent runs are replayable like historical forks.

## Done when

- A live GDR shows agent-proposed, policy-accepted adjustments with citations, produced without human interaction, and a forced-timeout test demonstrates clean degradation to the deterministic plan.

## Boundaries

LLMs propose only. No execution authority, no rule enforcement, no secrets in prompts.
