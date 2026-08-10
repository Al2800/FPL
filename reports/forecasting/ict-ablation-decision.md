# ICT feature ablation

Decision: `remain_shadow_only`
Promotion eligible: `False`
Reason: `no_complete_point_in_time_ablation_rows`
Policy: `ict-feature-weights-v1` (`a525de3d390f28fc9f27906c156fae00521a6212bbd3a0485dc65bbea11ed67d`)
Report hash: `2eb7792e4818d7468e0f714bc1d10a4d9c64a5a52e150c6e0b5d45e3770e198d`
Frozen four-family prereg: `False`

## Corpus gaps

- insufficient_cutoff_safe_ict_lag_snapshots
- insufficient_finalised_outcome_artifacts
- no_immutable_historical_ict_pit_snapshots

## Live posture

- live `player_events` / `live_faithful` projections remain ICT-free
- candidate weights stay `live_active: false` until owner promotion
- ICT is outside the frozen four optional_family_arms matrix

Ticket 16 records versioned candidate ICT lag weights and a fail-closed decision. Live player_events / live_faithful stay ICT-free until an owner-reviewed promotion against cutoff-safe paired rows. This track does not thaw the frozen four-family preregistration.
