# 17 — Benchmark fitted forecast-model candidates

Status: needs-triage
Type: task
Track: Phase 2 (forecast improvement)
Blocked by: 02

Activation gate: Phase 2 must be authorised and the live capture corpus must
support cutoff-safe time splits. Do not fit against post-deadline or same-season
holdout outcomes selected after results are known.

## Context

The current stack is intentionally transparent: minutes heuristics, Elo/team
context, empirical-Bayes priors and per-90 event rates. Ticket 05 adds
simulation but deliberately does not improve those marginal forecasts.
A fully operational engine needs a measured path beyond heuristics, not an
assumption that a more complex model is better.

## Scope

- Preregister candidate models separately for expected minutes, team goals and
  player events, retaining each current component as the baseline.
- Use rolling-origin evaluation, calibration and position/horizon breakdowns
  from plan §17.2.
- Compare complexity, latency, feature availability and failure behaviour as
  well as predictive accuracy.
- Promote a model only when it improves the relevant preregistered metric and
  can reproduce from versioned data/model artefacts; otherwise retain the
  transparent baseline.

## Done when

- Every candidate has a reproducible time-based evaluation against the current
  baseline and the odds-implied benchmark where applicable.
- Any promoted model records training cutoff, features, data sources,
  transformation version, artefact hash and fallback.
- Ticket 05 consumes calibrated marginals without changing scoring rules.
