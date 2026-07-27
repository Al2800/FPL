# Transfer-hit counterfactual and risk policy

The transfer-hit gate prevents a point estimate from selecting a paid transfer
without showing the safer legal alternatives. It is an additive policy layer:
the one-week solver still generates candidates, then a sealed same-cutoff
counterfactual artifact decides which candidate the hit-aware policy may
consume.

## Required ladder

For a solver configured for up to three moves, the artifact must contain the
best feasible zero-, one-, two- and three-transfer plans. It must also contain
every chip currently eligible in the manager’s longitudinal state. A missing
transfer count, missing chip, inconsistent hit cost, shortened horizon or
changed solver hash causes refusal rather than implicit fallback to the paid
plan.

All rows share the same policy state, player market, forecast cutoff and future
fixture scenario. The report keeps these concepts separate:

- immediate pre-hit points are expected points before subtracting the nominal
  transfer charge;
- immediate net points include the hit;
- horizon net value is the discounted total over four Gameweeks;
- free-transfer option value is reported but not confused with forecasted
  player points;
- forecast uncertainty is an explicit penalty;
- payback is the first projected Gameweek where cumulative pre-hit advantage
  covers the complete hurdle.

## Hurdle and selection

The active `transfer-horizon-v1` policy uses the official four-point nominal
cost, then adds a 1.5-point premium and a 0.75-point uncertainty allowance for
each paid transfer. For a single four-point hit, the required pre-hit advantage
is therefore 6.25 points. For an eight-point hit it is 12.5:

    hurdle
      = nominal hit
      + 1.5 × paid transfers
      + 0.75 × paid transfers

The nominal hit is already subtracted from weekly net values. Equivalently, a
paid plan must beat the best no-hit horizon by the premium and uncertainty
after hits. A plan that does not pay back inside the declared horizon cannot
pass.

Eligible chip rows retain the option-cost and uncertainty treatment from the
longitudinal chip policy. They are displayed beside the transfer ladder so an
eight-point restructure cannot win simply because a legal Wildcard or Free Hit
was omitted.

## GW34 reproduction

Run from the repository root:

    .venv\Scripts\python.exe -m scripts.run_gw34_transfer_counterfactual

The command writes
`reports/benchmarks/2025-26-counterfactuals/gw-34/transfer-hit-evaluation.json`.
It reads the reviewed GW34 forecast-optimiser input and output, the locked GW34
player-rate forecast, and outcome-stripped GW34–GW37 fixture schedules. Player
rates and prices stay frozen at the GW34 cutoff. Each initial transfer or chip
state receives a zero-future-transfer tail: its squad, lineup and captain are
re-evaluated each week, but no later transfer is permitted. This isolates
whether the initial move repays its own hurdle. Future free-transfer flexibility
is reported separately instead of being confounded with different adaptive
tails for each branch.

The evaluator never opens `hidden-outcome.json`. It hashes every canonical file
through GW34 before and after evaluation and refuses to return if that tree
changes. Historical full-schedule point-in-time snapshots were not captured,
so the future fixture scenario remains exploratory and cannot promote the
policy for live execution.

The sealed GW34 result retains the three-transfer plan. Its one-week net
advantage over the best no-hit plan is only 1.43 points, but the four-week
fixed-squad comparison is materially different:

- best no-hit horizon value: 113.44;
- three-transfer horizon value after the eight-point hit: 135.89;
- pre-hit horizon advantage: 30.45;
- required hurdle: 12.50;
- projected payback: GW35.

The two-transfer four-point-hit plan also clears, but its horizon value is
124.07 and therefore remains below the three-transfer plan after both premiums
and uncertainty. All four second-half chips are present in the ladder. None
clears its separate chip reserve/deployment policy in this scenario.

These figures are evidence that the gate works, not evidence that the frozen
fixture model is calibrated. The large divergence is precisely the kind of
case to revisit when genuine pre-deadline fixture snapshots and richer
availability forecasts exist in 2026/27.

## Live use

For 2026/27, build the same ladder from the immutable official fixture snapshot
captured at the decision deadline. Execute only the selected first action,
observe the next deadline’s real prices, availability and free-transfer state,
then discard the old advisory tail and replan. The policy is advisory and does
not submit transfers or chips to the FPL website.
