# Build the 2026/27 live initial-squad selection lab

This ExecPlan is a living document maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. The sections `Progress`,
`Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must
remain current.

## Purpose / Big Picture

This work creates a dedicated, read-only decision path for choosing an FPL
starting squad of 15 players before the 2026/27 Gameweek 1 deadline. A reviewer
will be able to give several policies the same immutable whole-market forecast,
compare legal squads, captaincy, bench value, uncertainty and sensitivity, and
approve or reject a proposal without any code path capable of writing to the
FPL account. The command `python -m scripts.run_live_seed_shadow` will either
produce a reproducible shadow report or refuse with named missing inputs.

## Progress

- [x] (2026-07-27 13:23Z) Claimed `FPL-bsw.38.4` after completing the
  historical GW1 seed counterfactual.
- [x] (2026-07-27 13:35Z) Audited the frozen official launch packet,
  preregistration, forecast modules, uncertainty/contingency utilities, World
  Cup priors and rules activation gate.
- [ ] Add contract tests and a dedicated initial-15 optimiser.
- [ ] Add the live shadow orchestrator, preregistered policy and refusal gates.
- [ ] Exercise the current 27 July snapshot, render a review artifact and run
  the full repository suite.

## Surprises & Discoveries

- Observation: the current official snapshot is a genuine whole-market live
  capture, unlike the reconstructed historical GW1 export.
  Evidence: capture `e2499ad7...2460` contains 558 official players, 20 teams
  and 380 fixtures with exact observation time and source hashes.
- Observation: the derived forecast input is intentionally degraded rather
  than ready for squad selection.
  Evidence: `promoted_team_ids` and `transferred_player_codes` are empty, all
  four odds slots are missing, and no unstructured evidence is captured.
- Observation: World Cup priors exist but are not joined into the live packet.
  Evidence: `control/identities/world-cup-2026-priors.csv` has 176 rows, while
  the current forecast-input capture does not bind its hash or fatigue values.
- Observation: the 2026/27 ruleset is not executable yet.
  Evidence: the live activation report has 11 blockers: one malformed chip
  boundary value and ten unconfirmed consumed rules. A legal proposal may be
  explored under a clearly labelled provisional constraint view, but it cannot
  become an approval-ready live recommendation.

## Decision Log

- Decision: build a dedicated initial-squad optimiser rather than adapt the
  transfer solver or promote the historical local-search seed.
  Rationale: starting with no owned players has different finance, search,
  bench, captaincy and optionality semantics from weekly transfers.
  Date/Author: 2026-07-27 / Codex.
- Decision: separate `shadow_generated` from `approval_ready`.
  Rationale: useful engineering and sensitivity work can proceed while launch
  context is incomplete, but the lab must refuse owner approval until required
  rules, player eligibility and forecast provenance pass.
  Date/Author: 2026-07-27 / Codex.
- Decision: the deterministic optimiser owns legality and enumeration; agents
  may rank or challenge bounded alternatives but may not invent players,
  prices or projections.
  Rationale: every arm must share an identical engine packet so model
  capability is measured as interpretation, not hidden data access.
  Date/Author: 2026-07-27 / Codex.
- Decision: do not promote any weight because the historical branch reached
  +38 by GW11.
  Rationale: that result is one realised seed-by-policy path and is explicitly
  production-ineligible.
  Date/Author: 2026-07-27 / Codex.

## Outcomes & Retrospective

The audit milestone is complete. The repository already has most low-level
pieces: immutable official capture, prior-season forecast components,
calibrated appearance distributions, contingency-aware lineup valuation,
robust projection shrinkage, rules activation and a preregistered live-shadow
evaluation policy. The missing core is the initial-15 optimisation and
orchestration layer. The current packet must also be enriched with promoted
team, transferred-player and World Cup context before it can meaningfully rank
the full market, and the rules gate must be cleared before owner approval.

## Context and Orientation

`data/live-shadow/fpl/20260727T100527Z/forecast-input-capture.json` is the
latest immutable official launch packet. It contains prices, positions, clubs,
availability fields, teams and fixtures, but not player point forecasts.
`src/forecasting/live_capture.py` creates that packet. The capture is local and
gitignored; committed policies and tests refer to hashes rather than copying
live raw data.

`src/optimisation/solver.py` optimises transfers for an existing 15-player
squad. It must not be reused as if the starting squad were fifteen transfers.
`src/optimisation/squad_contingency.py` values a fixed squad's legal XI,
captain, vice-captain, bench order and automatic-substitution protection from
appearance distributions. `src/optimisation/robust_objective.py` provides
calibrated downside projections for an existing solver input and informs the
risk semantics to retain.

The new `src/optimisation/initial_squad.py` will accept a complete immutable
forecast packet. A player row must include identity, club, position, price,
multiweek central and downside value, per-week projections and appearance
distribution. The optimiser returns a legal 15 plus lineup, captain, bench,
objective decomposition, alternatives and sensitivity. It does not fetch
data.

The new `src/orchestration/live_seed_selection.py` validates snapshot,
forecast, policy and rules lineage; runs deterministic and robust policies;
packages bounded alternatives for evidence-agent and challenger arms; records
human/reference abstention or input; and emits `approval_status`. It contains
no browser, authentication or HTTP mutation interface.

## Plan of Work

First write `tests/optimisation/test_initial_squad.py`. Tests must require
exact position counts, at most three players per club, budget compliance,
legal lineup and captaincy, deterministic results, bench/autosub value,
multiweek weighting, downside sensitivity and explicit refusal for incomplete
players or impossible pools. Implement `src/optimisation/initial_squad.py`
with deterministic candidate pruning and a bounded exact or branch-and-bound
search whose result is stable under input ordering. Keep selection scoring
separate from legality and return enough decomposition to explain each choice.

Then create `control/policies/initial-squad-2026-27.json`. Freeze the horizon,
week weights, central/downside blend, captaincy treatment, bench value,
transfer optionality proxy, early-Wildcard scenarios, new/promoted-player
shrinkage, World Cup fatigue fade, alternative distance and approval gates.
The policy binds the existing preregistration and never claims that historical
points selected these weights.

Add `src/orchestration/live_seed_selection.py` and
`tests/integration/test_live_seed_selection.py`. The orchestrator validates
content hashes and cutoff times, checks the official player pool and rules
activation, reports missing context by name, and distinguishes a degraded
shadow from an approval-ready proposal. Every arm receives the same
content-addressed engine packet. Invalid or incomplete agent output falls back
to the deterministic control and is visibly marked.

Finally add `scripts/run_live_seed_shadow.py` and
`docs/evaluation/live-initial-squad-policy.md`. The current 27 July snapshot
should produce a useful readiness/refusal report even if no approval-ready
squad is allowed. As later immutable captures add context, rerunning against a
new capture writes a new content-addressed output rather than replacing the
old result.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the focused tests:

    .venv/Scripts/python.exe -m pytest tests/optimisation/test_initial_squad.py tests/integration/test_live_seed_selection.py -q

Exercise the current live packet without account execution:

    .venv/Scripts/python.exe -m scripts.run_live_seed_shadow --capture data/live-shadow/fpl/20260727T100527Z

The command must state `account_writes=false`. While the current rules and
launch context remain incomplete it must also state
`approval_status=blocked`, list every blocking field, and either emit
explicitly provisional shadow alternatives or refuse squad generation
according to the policy gate.

Run the complete suite:

    .venv/Scripts/python.exe -m pytest -q

## Validation and Acceptance

The same packet and policy must reproduce the same squad and content hash
regardless of input row order. Every proposed squad must contain exactly two
goalkeepers, five defenders, five midfielders and three forwards, stay within
budget and contain no more than three players per club. The XI must contain one
goalkeeper and a legal formation; captain and vice-captain must be distinct
starters; the bench must contain the remaining four players in legal order.

The report must show central, downside, captaincy, bench/autosub and optionality
contributions, plus at least one alternative and sensitivity to horizon or
risk. Missing rules, promoted-team context, transfer context, World Cup joins
or player forecasts must never be silently imputed. No module in this feature
may import browser control or send an authenticated FPL request.

## Idempotence and Recovery

All committed policies are content-hashed. Live inputs and generated run
caches are immutable and addressed by capture hash. An identical rerun may
reuse or compare existing content; it must refuse a conflicting overwrite.
The system never deletes or rewrites the 27 July capture. If implementation
stops after optimiser tests, the orchestrator can resume from this plan without
changing the frozen policy.

## Artifacts and Notes

Historical evidence informing the design, but not its weights:

    GW1 structured-prior branch: 48 versus Scout control 56
    GW2 opening cumulative delta: -20
    GW11 cumulative: 591 versus 553
    decomposition: -8 GW1 seed, +46 later state-policy interaction

Current live readiness:

    capture_id=e2499ad7ab46d7147bba829d21eb6a8418b3d5f05fe7ff09708fdb458d802460
    players=558 teams=20 fixtures=380
    promoted_team_ids=0 transferred_player_codes=0
    world_cup_prior_rows=176 but not joined
    odds_slots=0/4 unstructured_snapshots=0
    rules_activation_blockers=11

## Interfaces and Dependencies

`src.optimisation.initial_squad` will expose:

    def validate_initial_squad_input(packet, policy) -> None: ...
    def optimise_initial_squad(packet, policy, *, objective="central") -> dict: ...
    def compare_initial_squad_policies(packet, policy) -> dict: ...

`src.orchestration.live_seed_selection` will expose:

    def build_live_seed_run(*, capture, forecast, policy, rules, evidence=None, human=None) -> dict: ...

The implementation uses the standard library and existing repository modules.
No dependency installation, network collection, browser execution or FPL
account mutation is part of this bead.

Revision note (2026-07-27): created after the historical seed branch and live
readiness audit. It makes a degraded shadow useful while keeping owner approval
blocked until the actual launch inputs and rules are complete.
