# Receding-Horizon Transfer Planner

This ExecPlan is a living document. The sections `Progress`, `Surprises &
Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be updated as
implementation proceeds.

The repository does not currently contain `.agent/PLANS.md`; this plan follows
the structure and standards of the existing
`docs/execplans/fpl-engine-upgrade-programme.md`.

## Purpose

Replace the control solver's fixed expected-hit-avoidance proxy with an
additive challenger that values actual projected players and fixtures over
three to six Gameweeks. The challenger plans several weeks but executes only
the first transfer action. At the next deadline it discards the remaining
trajectory, observes the new legal state and deadline-safe information, and
plans again.

The locked one-week control and all sealed replay artifacts remain unchanged.

## Progress

- [x] (2026-07-26 02:15Z) Claimed `FPL-bsw.29`, confirmed its files do not
  overlap the active GW12 evidence fork, and mapped the existing solver and
  policy-state transfer semantics.
- [x] (2026-07-26 02:15Z) Established the critical leakage boundary: every
  future projection in one planning run must be generated from the same
  pre-deadline cutoff; later Gameweek forecast artifacts may not be consumed.
- [x] (2026-07-26 02:21Z) Implemented a pure planning trajectory state with squad purchase/current/
  selling prices, bank, free transfers and deterministic rule transitions.
- [x] (2026-07-26 02:21Z) Implemented bounded multiweek search, objective decomposition, node/beam
  budgets, deterministic tie-breaking and fallback.
- [x] (2026-07-26 02:21Z) Built a historical adapter that projects known future fixtures using only
  the current episode's player history, priors, team ratings and cutoff.
- [x] (2026-07-26 02:21Z) Proved first-action execution and next-deadline replanning; the sealed GW12 isolated action scored +18 net points versus control.
- [ ] Produce sealed challenger artifacts, document limitations, run the full
  suite, close the Bead and push.

## Surprises & Discoveries

- Observation: An existing future Gameweek's locked forecast is not valid
  planning input for an earlier Gameweek.
  Evidence: GW13's feature state includes GW12 outcomes, while the GW12
  decision must freeze before those outcomes are revealed.

- Observation: Historical episode `observed.json` stores only the current
  Gameweek fixtures, although the real fixture schedule was already public.
  Evidence: GW12 contains ten fixtures, all with `event: 12`.

- Observation: The existing policy-state transition already contains the
  authoritative banked-transfer, exceptional GW16 top-up, half-profit selling
  price, Wildcard and Free Hit semantics.
  Evidence: `src/orchestration/policy_state.py` implements
  `_next_free_transfers`, price refresh and audited state transition.

## Decision Log

- Decision: Use a same-cutoff horizon artifact, never a sequence of later
  locked forecasts.
  Rationale: This matches what can be generated live and prevents outcome
  leakage in historical replay.
  Date/Author: 2026-07-26 / Codex

- Decision: Keep price projections frozen at the current cutoff in v1 while
  still carrying purchase, current and selling prices through every simulated
  state.
  Rationale: Future price changes are unknown at the deadline; inventing or
  reading realised future prices would add either uncalibrated behavior or
  leakage. A later price model can replace this declared scenario.
  Date/Author: 2026-07-26 / Codex

- Decision: Bound search by deterministic beam, branch and expanded-node
  budgets; wall-clock time is measured but is not the primary pruning rule.
  Rationale: Identical inputs must return identical actions across machines.
  A node-budget fallback is reproducible, whereas time-driven pruning is not.
  Date/Author: 2026-07-26 / Codex

## Context and Orientation

`src/optimisation/solver.py` is the unchanged legal one-Gameweek candidate
generator. `src/optimisation/transfers.py` applies same-position transfers with
budget, club and selling-price checks. `src/orchestration/policy_state.py` is
the authoritative realised longitudinal transition. New
`src/optimisation/trajectory.py` will implement an isomorphic planning-only
transition over projected markets. New `src/optimisation/multiweek.py` will
run bounded search over those states. New
`src/orchestration/multiweek_challenger.py` will enforce same-cutoff horizon
lineage and write challenger-only artifacts.

## Plan of Work

First define immutable planning state and horizon-week records. Validate
consecutive Gameweeks, one common cutoff and source hash, a complete player
market, legal squad membership and three-to-six-week horizon length.

Next implement the planning transition. Apply the candidate's audited transfers
at that week's frozen prices, retain original purchase prices for held players,
set purchase price for incoming players, refresh selling prices, subtract hits
inside the immediate objective, bank free transfers to the rule cap, and apply
the GW16 top-up. Chips are excluded from this slice and delegated to
`FPL-q8s`.

Then implement beam search. For each retained state, invoke the unchanged
single-week solver with the fixed transfer-option proxy disabled. Retain a
small deterministic set of legal candidates, transition each state, accumulate
discounted immediate objectives, deduplicate equivalent states, and keep only
the configured beam. Report immediate value, future trajectory value, total
value, nodes generated/expanded/pruned, elapsed time, and whether fallback was
used. Return only the first action as executable.

Finally build historical same-cutoff forecasts. Reuse the current episode's
player posterior and team rating state while replacing only fixture components
with future fixtures from the season schedule. Bind every horizon week to the
current cutoff and current feature/model hashes. Freeze and score the first
action through the existing validator/outcome scorer; never mutate the
canonical replay.

## Validation and Acceptance

Tests must prove:

- a later-cutoff horizon week is rejected;
- horizons shorter than three or longer than six are rejected;
- identical inputs and node budgets return identical trajectories;
- only the first action is exposed for execution;
- replanning at the next deadline ignores the prior tail;
- purchase/selling prices, bank, hits, transfer banking and GW16 top-up match
  the official transition semantics;
- state-equivalent paths deduplicate;
- exhausting the node budget returns the declared deterministic one-week
  fallback;
- immediate and future trajectory values sum to the reported total;
- control solver fingerprints and sealed replay artifacts remain unchanged.

Focused command:

    .\.venv\Scripts\python.exe -m pytest tests/optimisation/test_multiweek.py -q

Full command:

    .\.venv\Scripts\python.exe -m pytest -q

## Idempotence and Recovery

All new reports use `reports/benchmarks/2025-26-multiweek/`. No command writes
inside `reports/benchmarks/2025-26/`. Configuration and horizon artifacts are
content-addressed. Regeneration either produces the same bytes or fails closed.
If the challenger cannot construct three same-cutoff weeks or exhausts its node
budget before a complete path, it returns the deterministic one-week control
action and records the reason.

## Outcomes & Retrospective

The bounded planner and historical adapter are complete. On the GW12 four-week
case it expanded 18 states and 90 paths in about 3.1 seconds, selected two free
transfers, and its legally frozen first action scored 47 net points versus the
control's 29. The tail was advisory only. The result remains exploratory and
ineligible for promotion because full point-in-time historical schedule
snapshots are unavailable; live 2026/27 snapshots will satisfy that boundary.
