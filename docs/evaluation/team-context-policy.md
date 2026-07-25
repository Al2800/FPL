# Separate team attack and defence policy

`live-faithful-v1` uses one Elo-derived expected-result multiplier for both attack and defence. That makes a strong team raise every player component in the same way and prevents the forecast from representing combinations such as a strong attack with a weak defence.

The `live-faithful-v2-team-context` experiment separates those quantities. Before each fixture, team attacking strength is a prior-smoothed average of expected goals scored. Defensive vulnerability is a separate prior-smoothed average of expected goals conceded. The predicted team xG combines the attacking team’s rate with the opponent’s defensive vulnerability. The attack multiplier is proportional to that predicted xG. The defence multiplier is proportional to the resulting clean-sheet probability ratio, represented by `exp(league_xg - expected_opponent_xg)`. Both are bounded before player forecasting.

## Point-in-time rules

Only fixtures whose kickoff is strictly before the episode cutoff may update a team strength. The walk-forward adapter aggregates player expected goals into team-fixture xG and never uses the evaluated fixture itself.

The parameter grid is selected on 2022/23 and 2023/24. The 2024/25 season is revealed once as locked validation. The 2025/26 replay is forbidden during selection and is used only for the final out-of-sample decision.

Expected-goals fields are available for every selection, validation, and evaluation season. The older 2021/22 season lacks xG; goals are used only to preserve pretraining team-continuity information and never contribute to the parameter-selection objective.

## Cold starts

Teams absent from the previous season receive explicit promoted-team priors. The calibrated grid may lower their attack prior and increase their defensive vulnerability. A promoted team with no observations remains listed in `fallback_teams`; after it plays, its observed prior-fixture xG is blended with the cold-start prior rather than replacing it abruptly.

## Elo and odds

The challenger reuses the already locked, strictly pre-match Elo expected score as a modest stabiliser. It does not refit Elo on the evaluated season.

Odds are optional. A quote is eligible only when its source is registered, its `timing_label` is `registered_predeadline`, its capture timestamp is strictly before the cutoff, and its probabilities are normalised. Closing or unspecified football-data odds are rejected. Missing or rejected odds put the forecast into an explicit degraded mode but do not block the deterministic xG-plus-Elo forecast.

## Promotion rule and result

Promotion requires team-context player MAE to beat v1 for all players, owned players, and the selected XI, and to beat the event-only challenger for all players. The rule was declared before the 2025/26 result was inspected.

The calibrated challenger was rejected. Its locked 2024/25 team-xG MAE was approximately 0.617, but on 2025/26 it worsened player MAE versus v1 by approximately 0.137 for all players, 0.168 for owned players, and 0.210 for selected-XI players. It also worsened all-player MAE by approximately 0.018 versus the event-only challenger.

The rejection means these team xG multipliers must not enter the live policy as currently formulated. The implementation remains useful as a governed interface and diagnostic baseline. Future work may revisit shrinkage, position-specific application, clean-sheet calibration, and joint player-level fitting, but must use a new versioned challenger and the same locked evaluation discipline.
