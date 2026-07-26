# Chip policy and the GW31 Free Hit counterfactual

The chip policy is an additive challenger. It does not alter the completed
2025/26 replay, and it does not promote a chip because that chip happened to
score well after the deadline. Its purpose is to prove that Wildcard, Free Hit,
Bench Boost and Triple Captain can be generated, frozen, scored and carried
through legal state transitions using the same interface intended for live
2026/27 decisions.

## Weekly longitudinal integration

The original GW31 experiment proved the candidate and transition mechanics but
did not connect them to the ordinary replay runner: those paths still froze
every plan with `active_chip=None`. The reusable weekly path now creates a
`longitudinal-chip-policy-v1` decision before outcome reveal. That record binds
the exact policy state, ruleset, no-chip solver input and output, candidate
matrix, future values, uncertainty assumptions and selected action by hash.
The genuine replay and agent-fork runners accept this record explicitly,
rebuild it, and refuse any mismatch before freezing or scoring.

Chip mode is opt-in for a new trajectory so the sealed canonical 2025/26
artifacts remain byte-for-byte untouched. Once enabled, a genuine replay
requires a reviewed chip decision for every non-naive arm; the naive arm stays
the no-transfer/no-chip control. The chosen chip then flows through the normal
validated plan, outcome scorer and policy-state transition. This is especially
important for Free Hit: its temporary squad scores the current week while the
successor restores the predecessor squad, purchase prices, bank and banked
transfers.

Longitudinal inventory is not assumed to contain all four usable alternatives.
Used and expired chips disappear, while future-set chips may exist in state but
are not eligible before their rules-defined window. The weekly decision
therefore receives the currently legal chip IDs and their expiry Gameweeks;
generation emits the complete no-chip transfer ladder plus only those legal
chip candidates.

## What the policy decides

At a deadline the deterministic solver receives one immutable player market,
one forecast and one manager state. `src/optimisation/chips.py` creates eight
alternatives from those inputs:

- no chip with zero, one, two or three transfers;
- the highest-valued bounded Wildcard alternative;
- the highest-valued bounded Free Hit alternative;
- the highest-valued bounded Triple Captain alternative;
- the highest-valued bounded Bench Boost alternative.

The three-transfer bound is declared in `control/policies/chip-v1.json`. This is
not a claim that a Wildcard or Free Hit has been globally optimised across every
possible 15-player squad. It is a controlled comparison against the transfer
search used by the replay and is reported as such.

Every chip alternative uses the ruleset-driven validator. Wildcard and Free Hit
remove transfer hits and retain banked free transfers. Wildcard persists the
new squad. Free Hit scores the temporary squad and then restores the prior
player IDs, purchase prices and bank while refreshing only current market
prices. Bench Boost adds all four bench players to realised scoring. Triple
Captain changes the captain multiplier from two to three.

## Selection without hindsight

The policy value is:

    current-week expected net points
    + discounted same-cutoff future trajectory value
    - reserve value of consuming the chip

The future trajectory uses the GW31 player rates and prices frozen at the GW31
cutoff, a six-Gameweek fixture horizon, and the bounded receding-horizon planner.
Only fixture identity, home/away status and FDR enter that projection. Realised
GW31 points are unavailable until all eight plans have passed validation and
been frozen.

The reserve values represent the expected option value of keeping a scarce chip
for a stronger future blank or Double Gameweek. Version 1 reserves 16 points for
Wildcard, 12 for Free Hit and 8 each for Bench Boost and Triple Captain. A chip
must also beat the best no-chip alternative by at least two policy points after
that reserve. These values are policy assumptions fixed before this evaluation;
they have not been tuned against the GW31 result.

Historical full-schedule snapshots from the exact GW31 cutoff are not available.
The fixture horizon is reconstructed from outcome-stripped episode schedules,
so this report is exploratory and cannot promote the policy. Live 2026/27 runs
will instead bind the same interface to a genuinely captured pre-deadline
schedule.

## Sealed GW31 result

The declared policy selects the canonical three-transfer plan with no chip.
Its expected immediate value is 50.02 and its discounted future trajectory
value is 216.47. Triple Captain raises immediate expected value to 55.91, but
after its eight-point reserve it remains 2.11 policy points below the no-chip
plan. Wildcard and Free Hit produce the same immediate 50.02 because their
temporary or persistent three-transfer squad is identical at this bounded
search depth; their differences arise in the state carried into GW32.

After every plan was frozen, the revealed outcomes showed:

- zero transfers: 39 net points;
- one transfer: 37;
- two transfers: 61;
- three transfers without a chip: 63;
- Wildcard: 63;
- Free Hit: 63;
- Bench Boost: 63 because the selected bench returned zero;
- Triple Captain: 76 because the captain returned 13 points.

Triple Captain therefore looks attractive in hindsight, but its realised
13-point gain does not enter selection and does not justify changing the
predeclared reserve.

For weekly use, the full reserve applies until the final six Gameweeks before a
chip expires, then declines linearly to zero at its deadline. This is not a
forecast that late chips are inherently better. It prevents the optimiser from
assigning option value beyond the period in which the option can be exercised.
The policy also subtracts declared default uncertainty penalties: one point for
Wildcard and Free Hit, and half a point for Bench Boost and Triple Captain.
Callers may provide candidate-specific penalties, but they must cover the whole
matrix and are sealed into the decision. At the terminal deadline a chip still
must beat the best no-chip action by the two-point deployment threshold after
uncertainty; only its now-nonexistent reserve becomes zero.

The Free Hit branch restored the opening GW31 squad, every purchase price, the
£0.3m bank and all five free transfers. Replanning independently from GW32 to
GW38 then produced 484 net points over GW31–GW38, compared with 456 for the
canonical trajectory, a descriptive gain of 28. This gain is useful evidence
that state restoration and longitudinal branching work. It is not evidence that
the policy should have known to use Free Hit: its GW31-cutoff projection valued
the restored trajectory below the persistent three-transfer squad, and the
historical schedule has high provenance uncertainty.

## Reproduction and live use

Run from the repository root:

    .venv\Scripts\python.exe -m scripts.run_chip_counterfactual

The command writes
`reports/benchmarks/2025-26-counterfactuals/gw-31/evaluation.json`. The report
binds the episode, observed input, hidden outcome, forecast, policy configuration,
every frozen plan/outcome/transition hash, and a byte-level tree hash covering
all 2,229 canonical files from GW1 through GW31 before and after the run.

For live 2026/27, the same process should run as a shadow policy until real
pre-deadline fixture snapshots and multiple Gameweeks provide enough evidence
to calibrate chip reserves. A recommendation can then be reviewed by a human;
this module does not execute a chip on the FPL website.
