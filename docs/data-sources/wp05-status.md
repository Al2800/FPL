# WP-05 status — baseline forecasting

**Package:** WP-05  
**Done when (plan):** every baseline in §11.2 under time-based eval with error/calibration; start-prob sources vs naive; reproducible from code + versioned data refs.

## Checklist

- [x] Expected-minutes baseline + naive “started last GW”
- [x] Rolling start-prob benchmarked vs naive (rolling wins on Brier)
- [x] Team-strength Elo (football-data.co.uk)
- [x] Player-event rolling / per-90 / crude fixture adj
- [x] Odds-implied 1X2 baseline (closing/unspecified label)
- [x] Time-based eval harness + JSON report (`docs/data-sources/wp05/`)
- [ ] Official `ep_next` / FDR vs odds — deferred to pre-deadline snapshot corpus
- [x] World Cup priors CSV available for GW1–5 multipliers (`control/identities/world-cup-2026-priors.csv`)

## Verdict

WP-05 core baselines are in place for structured-data replay. Live official fields and true pre-deadline odds remain Phase 1 capture work, not blockers for WP-07 optimiser scaffolding.
