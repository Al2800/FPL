# Fitted forecast candidates evaluation

Report hash: `975ff9ef5cf2a1d49968a707fb566abb4df7d828c6b9a92b924e15908dbded76`

Fit seasons: 2022-23, 2023-24
Locked validation: 2024-25
Any promoted: False

## expected_minutes

- candidate: `l2_logistic_start_lag_roll3_v1`
- promotion_eligible: `False`
- baseline Brier: 0.10406
- candidate Brier: 0.10146
- baseline minutes MAE: 16.161
- candidate minutes MAE: 16.755
- reason: failed_preregistered_minutes_gates_on_locked_validation

Ticket 17: minutes family fully evaluated on locked 2024/25. Other families remain baseline-retained until their joins ship. Monte Carlo (ticket 05) continues to consume baseline marginals.
