# WP-04: Recommended training targets by model component

| Component | Primary target | Features (pre-deadline only) | Notes |
|---|---|---|---|
| Expected minutes / start probability | Started (minutes≥60), minutes | Lagged minutes, status flags, chance_of_playing when snapshotted, fixture congestion | News/line-ups only from live archive going forward |
| Team strength | Goals for/against per match | Home/away, Elo/rolling rates, odds-implied probs | football-data for results/odds; label odds timing |
| Player events (G/A) | Goals, assists | Per-90 rates, team strength, minutes projection | Position-aware; cold-start priors for new players |
| Clean sheets | Team CS / player CS (60+ mins) | Team defence rates, odds | Midfielder CS worth 1 pt — keep separate |
| Defensive contributions | Threshold hit (binary) + actions | Official DC fields from 2025/26+; role/minutes | Pre-2025/26 history not directly comparable |
| Bonus | Bonus points / BPS rank | BPS components where known; do not claim exact BPS without Opta | Probabilistic; official points are outcome truth |
| FPL points | Derived via scoring engine from event forecasts | — | Do not train directly on `total_points` across rule regimes (plan §11.1) |

## Explicitly excluded / shifted features
- Same-GW `xP` / post-match `ep_this` as predictors of that GW's points
- Same-GW outcomes as features
- Un-timestamped closing odds presented as pre-deadline

## Open Decision 6 (usable seasons)
Provisionally usable for structured baselines: seasons with complete `merged_gw` + fixtures + stable `code` identity (see vaastav profile). Final call recorded when WP-05 evaluation splits are fixed.
