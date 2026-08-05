# ADR-0016: Per-Gameweek agent cost and latency budgets

**Status:** Accepted (amended by ADR-0024)
**Date:** 2026-07-21
**Decides:** Open Decision 13 (`docs/plan.md` Section 25)

## Context

Section 13.5 requires explicit token/cost caps and wall-clock timeouts. Near deadline, overrunning agents must degrade to the deterministic forecast-plus-optimiser plan (Section 15.3).

## Decision

Phase 1 default budgets (overridable per run in the Gameweek Decision Record `pipeline` block):

| Stage | Wall-clock | Indicative cost cap |
|---|---|---|
| Evidence agent | 8 minutes | Owner-set provider budget / GW |
| Challenger agent | 5 minutes | Owner-set provider budget / GW |
| Combined agent stages | Must finish by **T-90m** before deadline | Sum of above |

On timeout or budget breach: mark GDR `degraded=true`, attach failure reason, **do not** block the deterministic recommendation.

The selected ChatGPT-subscription Codex host does not expose a reliable
per-run currency meter. Currency is therefore recorded as unavailable, not
zero; the wall-clock, one-attempt, output and postflight token limits remain
enforced. ADR-0024 declines an API-backed arm for now; hard monetary caps
remain unavailable until a future API decision.

## Consequences

- Agent value is measured inside these budgets; unbounded spend is out of policy.
- Budgets are data on the run record, not hidden in prompts.
