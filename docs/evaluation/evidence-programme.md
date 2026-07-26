# Weekly evidence programme

The weekly evidence programme turns the one-off GW12 reconstruction into a
reusable evaluation interface. A caller supplies one or more Gameweeks and one
timestamped evidence bundle for each selected week. The programme then produces
two different answers without changing the canonical replay:

1. an isolated result for each selected Gameweek, starting from that week's
   canonical manager state and stopping after scoring the frozen decision; and
2. one longitudinal result, starting at the earliest selected Gameweek and
   carrying its own squad, purchase prices, bank, free transfers and points
   through every later deadline.

These answers must remain separate. The isolated result attributes the direct
effect of one bundle. The longitudinal result measures how the changed action
compounds through later transfers, line-ups and captain choices.

## Temporal and evidence contract

Each bundle is validated before the optimiser runs. Every claim must retain:

- source identifier and URL;
- publication and retrospective capture timestamps;
- expiry;
- affected player;
- claim confidence;
- citation-excerpt hash;
- adjustment identifier, target and confidence.

The bundle cutoff must exactly equal the episode deadline. A claim published
after that cutoff is rejected rather than clipped or silently ignored. The
historical GW12 bundle is still not production-eligible because it was captured
retrospectively and the case was chosen after its outcome. Generalising the
runner does not weaken that classification.

For every evaluated week, the programme builds the solver input from the
independent manager state and the existing sealed structured forecast. It
applies only that week's eligible bundle, freezes and validates the proposed
plan, and only then reads the hidden outcome. Later weeks without a supplied
bundle use the deterministic structured fallback.

## Attribution

The report exposes three values:

- `isolated_direct_net_points_delta`: the sum of selected-week isolated effects;
- `longitudinal_net_points_delta`: the total difference along the independent
  state chain;
- `state_compounding_net_points_delta`: longitudinal minus isolated.

A negative compounding value does not mean that the original evidence was
wrong. It means later state and decisions gave back some of its immediate gain.
Likewise, a positive value would indicate that an intervention created useful
future squad or transfer state.

With the current GW12 bundle:

- isolated direct value is +14;
- GW12–GW38 longitudinal value is +4;
- state compounding is therefore −10;
- the fork finishes on 2,014 cumulative points versus the canonical 2,010.

The 14-point one-week result is real for that frozen alternative, but it would
overstate the season value by ten points. This is why the challenger matrix
must retain both columns.

## Canonical immutability and reproduction

Before running, the programme hashes every canonical file from the earliest
selected Gameweek through the terminal Gameweek. It recomputes the same tree
hash after all isolated and longitudinal evaluations. Output is written only to
`reports/benchmarks/2025-26-evidence-programme/`.

Run the committed programme from the repository root:

    .venv\Scripts\python.exe -m scripts.run_weekly_evidence_programme

To provide multiple weeks, repeat `--bundle`:

    .venv\Scripts\python.exe -m scripts.run_weekly_evidence_programme \
      --bundle 12=path/to/gw12.json \
      --bundle 18=path/to/gw18.json

The syntax is the same on Windows PowerShell when entered on one line. Duplicate
Gameweeks are rejected. The report writer accepts a rerun only when its bytes
are identical.

## Scope and live use

This module is an evaluation runner, not an autonomous web collector or FPL
executor. For the 2026/27 live season, governed agents can produce bundles from
information genuinely captured before each deadline and feed them through the
same interface. Live shadow bundles can become promotion-eligible only when
their normal source, capture, expiry and provider controls pass; retrospective
historical bundles remain exploratory.

The current historical report is
`reports/benchmarks/2025-26-evidence-programme/evaluation.json`. It is suitable
for the challenger matrix because it binds every episode, bundle, solver input,
solver output, frozen plan, outcome, transition and manager-state hash while
reporting direct attribution separately from state compounding.

The focused one-off and generic evidence tests pass 7/7. The complete repository
suite passes 421/421. The generic isolated plan and all 27 generic longitudinal
plan hashes exactly match the original GW12 experiment, which is the extraction
equivalence check.
