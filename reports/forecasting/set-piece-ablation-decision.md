# Set-piece role effect ablation

Decision: `remain_shadow_only`
Promotion eligible: `False`
Reason: `no_complete_point_in_time_ablation_rows`
Policy: `set-piece-effect-weights-v1` (`164407eb530c251fce7a7f48e934c5116a19cd66efe7c237d9a76f270504c833`)
Report hash: `1c1f890e2bc1691080e12a87d775ee7ed66d079a33f3cd311486af8217ed232d`

## Corpus gaps

- insufficient_cutoff_safe_set_piece_ledgers
- insufficient_finalised_outcome_artifacts
- no_immutable_historical_set_piece_pit_snapshots

## Live posture

- `effect_weights` remain `null` on live feature payloads
- candidate weights stay `live_active: false` until owner promotion

Ticket 15 records versioned candidate weights and a fail-closed decision. Live feature payloads keep effect_weights=null until an owner-reviewed promotion against cutoff-safe paired rows.
