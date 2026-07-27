# Add a cutoff-safe Football-Data odds comparator

This ExecPlan is a living document maintained in accordance with
`C:/Users/Alastair/.codex/.agent/PLANS.md`. The sections `Progress`,
`Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must
remain current.

## Purpose / Big Picture

This work lets the project use Football-Data match odds immediately for private
historical comparison while preserving the benchmark's point-in-time boundary.
An operator can normalise an already acquired Football-Data CSV into a
content-addressed comparator and produce a four-slot live-readiness artifact.
Because Football-Data rows do not prove when each quote was available before an
FPL deadline, the adapter must never present them as live T-24h, T-8h, T-2h or
final snapshots. Each unsupported slot remains visibly degraded.

## Progress

- [x] (2026-07-27 13:48Z) Claimed `FPL-bsw.38.6` and recorded the owner's
  decision to use Football-Data for now.
- [x] (2026-07-27 14:02Z) Audited the source registry, acquisition layer,
  historical odds baseline, team-context admission gate and live capture
  contract.
- [ ] Add the Football-Data normaliser, source decision and checkpoint policy.
- [ ] Add focused tests and operator documentation.
- [ ] Run focused and broader regression tests, record results and close the
  bead.

## Surprises & Discoveries

- Observation: Football-Data is already enabled for attributed private
  analysis and local, non-redistributed retention.
  Evidence: `control/sources/source-registry.yaml` registers
  `football-data-co-uk` with `enabled: true`.
- Observation: the existing forecast layer correctly refuses Football-Data's
  ordinary closing or unspecified odds as pre-deadline evidence.
  Evidence: `src/forecasting/team_attack_defence.py` accepts only
  `timing_label=registered_predeadline`, and its tests reject
  `closing_or_unspecified`.
- Observation: the generic live capture requires explicit terms and cost
  activation for timestamped market sources.
  Evidence: `src/forecasting/live_capture.py` calls
  `_approved_market_source` before admitting a staged market snapshot.

## Decision Log

- Decision: approve Football-Data only for historical match odds and a
  closing-or-unspecified comparator.
  Rationale: this uses the chosen source now while avoiding a false claim that
  a seasonal CSV is a fixed-time live feed.
  Date/Author: 2026-07-27 / Alastair and Codex.
- Decision: retain the four live odds slots as explicit gaps.
  Rationale: absence is safer and more informative than backfilling an unknown
  quote time after the deadline.
  Date/Author: 2026-07-27 / Codex.
- Decision: exclude final scores and outcomes from the normalised comparator.
  Rationale: the input artifact should contain market information only and
  cannot accidentally leak realised results into a forecast.
  Date/Author: 2026-07-27 / Codex.

## Outcomes & Retrospective

Implementation is in progress. The intended outcome is a deterministic local
comparator and a machine-readable four-slot degradation report. A genuinely
timestamped provider remains a later optional enhancement, not a prerequisite
for using official FPL state or the historical Football-Data baseline.

## Context and Orientation

`control/sources/source-registry.yaml` is the repository authority for source
rights and collection status. It already allows attributed private use of
Football-Data CSVs but forbids redistribution. `src/forecasting/odds_implied.py`
currently derives 1X2 home, draw and away probabilities from Football-Data
columns, preferring Bet365, then Pinnacle and then the source's average columns.
It labels the timing as closing or unspecified.

The new `src/ingestion/odds_snapshot.py` is a source-specific normalisation
boundary. A comparator is a market artifact useful for evaluation but
ineligible for a live decision. A checkpoint is one of four desired collection
times relative to an FPL deadline. A degraded checkpoint is a recorded missing
capability; it is not an imputed value.

## Plan of Work

Create `config/data_sources/2026-27-odds.json` to record the owner-approved
Football-Data scope, its restrictions and the desired live slots. Create
`control/manifests/2026-27-odds.json` as the committed source decision and
fallback policy.

Implement `normalise_football_data_csv` in
`src/ingestion/odds_snapshot.py`. It will parse bytes without network access,
select the first valid complete 1X2 column family, remove bookmaker margin by
normalising inverse decimal odds, sort fixtures deterministically and seal the
artifact with both raw-source and derived-content SHA-256 hashes. It must not
copy scores or result columns.

Implement `build_football_data_checkpoint_manifest` in the same module. It
will validate a comparator's hash and list every required slot as unavailable
with the reason that the source has no quote timestamp. It will expose no
admitted live market snapshots.

Add `tests/data/test_odds_snapshot.py` and
`docs/data-sources/2026-27-odds.md`. Tests will cover deterministic
normalisation, provider fallback, invalid rows, outcome exclusion, hash
validation and all four degraded slots.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run the focused contract:

    .venv/Scripts/python.exe -m pytest tests/data/test_odds_snapshot.py -q

Then run the existing odds and live-capture regression tests:

    .venv/Scripts/python.exe -m pytest tests/forecasting/test_team_attack_defence.py tests/integration/test_live_episode_builder.py tests/unit/test_registry.py -q

Finally run the complete suite:

    .venv/Scripts/python.exe -m pytest -q

No command in this plan downloads a CSV. Existing locally retained source bytes
or test fixtures are passed to the pure normaliser.

## Validation and Acceptance

Given the same CSV bytes in any repeated run, the normaliser must return the
same ordered matches and content hash. Each accepted fixture must have
normalised probabilities summing to one and a
`closing_or_unspecified` timing label. No result or score field may appear.

The checkpoint manifest must list T-24h, T-8h, T-2h and final exactly once,
mark all four unavailable for live admission, expose an empty admitted snapshot
list and reference the comparator by its verified hash. A modified comparator
must be rejected.

## Idempotence and Recovery

All transformations are pure and content-addressed. They do not download,
overwrite or delete source files. Repeating a transformation is safe. Raw
Football-Data CSVs remain local and ignored by Git; only configuration,
documentation, tests and hashes may be committed.

## Artifacts and Notes

The source decision is:

    selected source: football-data-co-uk
    approved use: historical match odds and closing comparator
    live fixed-time admission: false
    fallback: shared structured forecast without odds

## Interfaces and Dependencies

`src.ingestion.odds_snapshot` will expose:

    def normalise_football_data_csv(
        body: bytes,
        *,
        season: str,
        origin: str,
        observed_at: str,
        available_at: str | None = None,
    ) -> dict[str, Any]: ...

    def build_football_data_checkpoint_manifest(
        *,
        season: str,
        decision_cutoff: str,
        assessed_at: str,
        comparator: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]: ...

The implementation uses Python's standard `csv`, `datetime`, `hashlib` and
`json` modules. No dependency, network collection, authentication, browser
automation or FPL account mutation is introduced.

Revision note (2026-07-27): created after the owner selected Football-Data and
the code audit confirmed that its ordinary CSV odds must remain comparator-only.
