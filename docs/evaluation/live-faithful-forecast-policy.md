# Live-faithful forecast policy

## Purpose

The replay uses two distinct structured forecast views:

1. `historical-rolling-v1` is the deliberately weak ablation. It averages up to three completed Gameweek point totals. It remains unchanged so cold-start chasing stays measurable.
2. `live-faithful-v1` is the candidate production process. It combines a completed earlier-season player prior, current-season evidence, expected minutes and cutoff-safe fixture/team adjustments. It is not eligible for benchmark decisions while its model configuration says `provisional_pending_calibration`.

The deterministic optimiser receives exactly one explicitly selected view. A forecast view must contain the complete known player market, reference the exact feature-state hash and pass its own content-hash check. It cannot silently overwrite the rolling feature state.

## Point-in-time inputs

Required inputs fail closed:

- the immutable replay feature state;
- the current-season identity map, with stable FPL player codes;
- a content-addressed player prior made only from a completed earlier season;
- a content-addressed team/fixture prior whose `as_of` is no later than the episode cutoff;
- a versioned model configuration.

Timestamped odds and unstructured evidence are optional in V1. Their absence produces a visible degraded status; it never causes a fabricated neutral value to be labelled as observed evidence. Historical odds without a quote timestamp remain diagnostic-only.

## Player prior and cold start

Returning players join across seasons using FPL `code`, not element ID or display name. Their prior records points per 90, start probability, minutes per start and sample size.

An unmatched player—such as a promoted player or new league transfer—uses a position and launch-price-band fallback. If that group is unavailable, the builder may fall back to position only, and it records that reason. Name-only joins are prohibited. Duplicate or ambiguous codes fail closed.

The current provisional forecast shrinks observed points per 90 toward the earlier-season prior using equivalent minutes. It separately shrinks observed starts toward prior start probability. Expected minutes combines the posterior start probability, prior minutes per start and a cameo assumption. This means a 17-point GW1 does not automatically become 17 expected points in GW2, and expected minutes materially changes the projection.

These equations are contract scaffolding, not selected coefficients. The values in `control/models/live-faithful-v1.provisional.json` must be calibrated on seasons through 2023/24, validated once on 2024/25 and then locked before any 2025/26 replay decision is regenerated.

## Fixture and team adjustment

Every fixture is projected independently. A blank has zero expected minutes and points while retaining the player in the market. A double sums its separate fixture components.

The fixture adjustment blends attack and defence multipliers according to position and clamps the result to configured bounds. The team-prior artifact must be generated from results strictly before the episode cutoff. A promoted team must carry either a supplied lower-division prior or a declared league/promoted-team fallback.

## Evaluation and promotion

Time-ordered evaluation must compare:

- raw rolling;
- prior only;
- prior plus expected minutes;
- prior plus team/fixture strength;
- the full structured view;
- odds as a diagnostic comparator where historical timing is not provable.

Report player-week MAE/RMSE, expected-minutes MAE, start Brier score, calibration by predicted-points bin, top-player ranking stability, transfer churn and early-season hit recommendations. The richer model is promoted only if the locked 2024/25 validation supports it or documents a deliberate, reviewed trade-off.

2025/26 is the untouched end-to-end test season. It validates chronology, state, reproducibility and decisions; it is not a source of fitted weights. GW2 remains sealed until calibration is complete.

## 2026/27 live parity

For the live season, capture immutable official launch prices, positions, availability and team assignments when the game launches. Record promoted/new-transfer fallback provenance. Capture odds at fixed pre-deadline intervals (initially T-24h, T-8h, T-2h and the final successful snapshot before deadline) with event, market, bookmaker/source and retrieval timestamps. Missing intervals degrade visibly.

Unstructured reports, press conferences, injuries and blogs should be packaged as timestamped evidence available equally to each benchmark arm. The structured engine output remains common; agent capability can then be measured through how each arm retrieves, assesses and applies the bounded evidence without allowing post-deadline information.
