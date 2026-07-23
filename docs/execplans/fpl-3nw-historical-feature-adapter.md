# Build a deadline-safe historical feature and market adapter

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

After this change, the benchmark can turn each immutable 2025/26 observed episode into the exact structured inputs needed for a weekly decision without opening its hidden outcome. A reviewer can advance the episodes in chronological order and see a content-addressed feature history, a complete known market that survives Blank Gameweeks, fixture-aware player projections, and a solver input for any independently owned policy state. Double Gameweek rows are combined before rolling features are calculated, so one fixture in a Gameweek can never become a feature for another fixture locked at the same deadline.

Gameweek 1 is an explicit controlled seed rather than a fabricated forecast. The official Premier League Scout’s published 15-player selection from 14 August 2025 is mapped to the frozen player identities and launch prices, costs exactly £100.0m, and is shared by all policy arms. Structured policy divergence begins in Gameweek 2.

## Progress

- [x] (2026-07-23 15:07Z) Confirmed `FPL-3nw` was ready, unowned and file-isolated; claimed it in Beads.
- [x] (2026-07-23 15:20Z) Isolated the Windows launch regression to the managed sandbox token boundary and verified narrowly approved repository execution.
- [x] (2026-07-23 15:39Z) Mapped historical episode, feature, forecasting, policy-state, optimiser and schema contracts.
- [x] (2026-07-23 15:48Z) Recovered the official 14 August 2025 Scout selection and mapped all 15 players to frozen identities and £100.0m of GW1 prices.
- [ ] Add leakage-first contract tests and observe their pre-implementation failure.
- [ ] Implement the cumulative player-Gameweek feature state and strict schema.
- [ ] Implement market carry-forward, fixture-aware projections and solver-input adaptation.
- [ ] Add the governed GW1 seed and historical feature policy.
- [ ] Validate representative GW1, Double Gameweek and Blank Gameweek episodes, then run the complete repository suite.
- [ ] Record evidence in Beads and close `FPL-3nw`.

## Surprises & Discoveries

- Observation: the immutable observed episode contains only the immediately preceding Gameweek’s player rows, while the current forecasting builders require rolling and cumulative history.
  Evidence: GW2 contains 690 GW1 rows and GW3 contains 705 GW2 rows; no episode contains the complete prior season.

- Observation: row-level shifting is unsafe in Double Gameweeks.
  Evidence: the episode entering GW27 contains 896 fixture rows for only 817 players from GW26. A shift over rows would let a player’s second fixture consume the first fixture’s outcome.

- Observation: a Blank Gameweek cannot rebuild a selectable market from only the previous Gameweek.
  Evidence: the episode entering GW35 contains 582 prior rows after a seven-fixture GW34, although players from blank clubs remain owned and selectable.

- Observation: the final `players_raw.csv` is useful for identity audit but is not a deadline-safe launch catalogue.
  Evidence: it contains end-of-season status, prices and cumulative outcomes. The strict replay path must not use those mutable fields.

- Observation: the official Scout squad is a legal exact-budget controlled seed, not the earlier £99.5m synthetic test squad.
  Evidence: its frozen GW1 prices sum to £100.0m across 2 goalkeepers, 5 defenders, 5 midfielders and 3 forwards.

## Decision Log

- Decision: Aggregate every observed fixture row into one player-Gameweek record before updating rolling or cumulative state.
  Rationale: every fixture in the same Gameweek shares one FPL deadline; aggregation is the only ordering that prevents within-round look-ahead while preserving Double Gameweek totals.
  Date/Author: 2026-07-23 / Codex.

- Decision: The strict market consists of players known through the controlled seed or a completed prior-Gameweek observation. Once known, a player remains in the market across blanks with the last observed quote and an explicit age.
  Rationale: the final-season catalogue would leak later registrations and end-state fields. Carry-forward preserves owned and selectable known players without inventing future membership.
  Date/Author: 2026-07-23 / Codex.

- Decision: Historical `value` is represented as an uncertain last-observed quote, never as a proven deadline price.
  Rationale: the upstream export establishes Gameweek association but not a deadline capture timestamp. Every quote records `source_gameweek`, `age_gameweeks` and `price_confidence=historical_post_gameweek_export`.
  Date/Author: 2026-07-23 / Codex.

- Decision: Gameweek 1 uses the official Scout selection as a fixed shared seed and produces no model-selected alternative.
  Rationale: the GW1 episode has no prior player history, while the source-backed seed provides a legal, reproducible experimental starting point. This historical control does not define the 2026/27 live starting-squad method.
  Date/Author: 2026-07-23 / Codex.

- Decision: The first transparent projection model uses only completed prior player-Gameweeks. It blends prior start and rolling minutes for expected minutes, uses rolling-three realised points per upcoming fixture, sums Double Gameweek fixtures, and assigns zero fixture points in blanks.
  Rationale: this matches the established baseline family, is reproducible and interpretable, and avoids arbitrary Elo, odds or editorial weights before those sources are calibrated.
  Date/Author: 2026-07-23 / Codex.

## Outcomes & Retrospective

Implementation is in progress. The intended outcome is a deterministic, hidden-outcome-free adapter that makes Bead 13 a chronological composition task rather than a place where data semantics are invented.

## Context and Orientation

`src/orchestration/historical_episode_builder.py` creates immutable episode directories. Each contains `episode-manifest.json`, `observed.json`, `identity-map.json` and a physically separate `hidden-outcome.json`. The adapter may read the first three only. The manifest’s `observed.feature_snapshot_ref.content_sha256` is the canonical hash of `observed.json`.

`observed.json` carries current fixtures and `lagged_player_features`, which are fixture rows from the immediately preceding Gameweek. A Double Gameweek can therefore contain two rows for one player. A Blank Gameweek omits players whose clubs had no match.

`src/orchestration/historical_feature_state.py` will own the cumulative, content-addressed history. A player-Gameweek record means all of one player’s fixture rows in one FPL scoring round combined into a single record. The feature state will retain these records, the latest known market quote and input lineage.

`src/forecasting/replay_adapter.py` will turn one feature state plus current fixtures and one policy’s state into projections and a `src.optimisation.types.SolverInput`. A policy state is the arm-owned squad, bank, free transfers and chips produced by `src/orchestration/policy_state.py`.

`control/seeds/2025-26/official-scout-gw1.json` will encode the controlled shared seed. Its primary source is the Premier League article “Scout Selection: The best FPL squad for the opening Gameweeks”, published 14 August 2025 at `https://www.premierleague.com/en/news/4373986`. The article names and prices all 15 players. Frozen GW1 rows supply their FPL element identifiers, positions and club identities.

The feature-state schema in `control/schemas/benchmark/feature-state.json` is closed: unknown fields fail validation. The state hash is SHA-256 over canonical JSON with the hash field omitted.

## Plan of Work

First add `tests/historical-replay/test_replay_feature_adapter.py`. Use small in-memory episodes to prove that two fixtures for one player in the same prior Gameweek become one history record; rolling features never observe an earlier fixture from that same round; a blank current fixture list produces zero projected points without deleting the player; an omitted player in a prior blank retains the last quote with an increased age; same-Gameweek or hidden fields fail closed; and identical inputs produce identical hashes.

Add the strict feature-state schema and the official Scout seed. Tests must validate the seed’s source date, 15 unique frozen player IDs, positional composition, three-per-club limit and exact £100.0m total. The seed contains no post-deadline performance fields.

Implement `src/orchestration/historical_feature_state.py` using standard Python mappings and canonical JSON. Validate manifest, observed and identity identities; require chronological advancement by one Gameweek; aggregate numeric outcome fields by sum; require position, team and price consistency within a player-Gameweek; update last-known quotes only from the episode’s lagged prior Gameweek; and carry absent known players forward. Refuse forbidden fields such as `xP` and refuse a lagged Gameweek that is not exactly current Gameweek minus one.

Implement `src/forecasting/replay_adapter.py`. Join each known player’s current club to the current fixture list, create one forecast component per fixture, and sum components for the solver’s expected points. Normalise `GK` to `GKP` and tenths prices to decimal millions. A player with no current fixture receives zero expected points but stays in the market. Preserve the policy state’s purchase price for owned players.

Document the exact limitations and the distinction between historical replay and 2026/27 live snapshots in `docs/evaluation/historical-feature-policy.md`.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Before implementation run:

    .\.venv\Scripts\python.exe -m pytest tests/historical-replay/test_replay_feature_adapter.py -q

Expect import or missing-contract failures.

After each milestone run:

    .\.venv\Scripts\python.exe -m pytest tests/historical-replay/test_replay_feature_adapter.py tests/contracts/test_benchmark_schemas.py -q

At completion run:

    .\.venv\Scripts\python.exe -m pytest -q

The complete suite should pass with the new adapter tests included.

## Validation and Acceptance

For the official real episodes, advancing GW1 then GW2 must produce a GW2 feature state containing only completed GW1 player-Gameweeks and a reproducible lineage hash. Advancing through a Double Gameweek must retain one record per player and Gameweek regardless of fixture count. Advancing through the blank before GW35 must not remove previously known or owned players; their quotes must show the correct source Gameweek and age.

No code path used to create the state or solver input may accept `hidden-outcome.json`, current-Gameweek `player_outcomes`, `xP`, or a row whose source Gameweek is not earlier than the target decision. Reversing input row order must not change hashes or outputs.

The official Scout seed must validate as a legal £100.0m 15-player squad. GW1 must identify the seed fallback explicitly; GW2 onward must identify the rolling model and all state, episode, identity, rules and model hashes.

## Idempotence and Recovery

The adapter is pure and writes no episode data. Repeating a state transition with identical inputs returns identical content and hashes. A failed validation returns no successor. The official seed and schema are versioned repository artifacts; changing either intentionally changes downstream hashes.

The managed Windows sandbox currently fails before child-process execution with `SetTokenInformation(TokenDefaultDacl) failed: 1344`. Narrowly approved commands scoped to this repository and its existing virtual environment are the verified operational fallback. No machine ACLs, services or processes are modified.

## Artifacts and Notes

Representative frozen inputs:

    GW27 observed prior rows: 896 fixture rows, 817 players
    GW35 observed prior rows: 582 after a seven-fixture GW34
    Frozen season identities: 841 players, 20 teams
    Official Scout seed: 15 players, £100.0m, published before the GW1 deadline

The upstream price limitation must remain visible in every strict historical quote:

    price_confidence = historical_post_gameweek_export

For live 2026/27 episodes, immutable official snapshots captured before the deadline will use a different confidence value and will not need this historical approximation.

## Interfaces and Dependencies

No new package is required.

In `src/orchestration/historical_feature_state.py`, define:

    class HistoricalFeatureStateError(ValueError)

    def build_feature_state(
        *,
        episode_manifest: Mapping[str, Any],
        observed: Mapping[str, Any],
        identity_map: Mapping[str, Any],
        previous_state: Mapping[str, Any] | None = None,
        seed: Mapping[str, Any] | None = None,
        model_version: str = "historical-rolling-v1",
    ) -> dict[str, Any]

    def feature_state_hash(state: Mapping[str, Any]) -> str

In `src/forecasting/replay_adapter.py`, define:

    class ReplayAdapterError(ValueError)

    def build_replay_solver_input(
        *,
        feature_state: Mapping[str, Any],
        policy_state: Mapping[str, Any],
        max_transfers: int = 3,
    ) -> SolverInput

The implementation may expose smaller pure helpers for aggregation and projection tests. It must not import or read the hidden outcome module or file.

Revision note (2026-07-23): Initial plan created after ownership checks, managed-sandbox diagnosis, full contract mapping and recovery of the source-backed official Scout seed.
