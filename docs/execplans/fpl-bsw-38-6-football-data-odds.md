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
Historical rows carry only the source's Friday/Tuesday collection schedule and
remain exploratory. A future live capture can fill a slot only when this project
observes the pre-closing file strictly before the FPL cutoff. Unsupported or
missed slots remain visibly degraded.

## Progress

- [x] (2026-07-27 13:48Z) Claimed `FPL-bsw.38.6` and recorded the owner's
  decision to use Football-Data for now.
- [x] (2026-07-27 14:02Z) Audited the source registry, acquisition layer,
  historical odds baseline, team-context admission gate and live capture
  contract.
- [x] (2026-07-27 14:10Z) Added the normaliser, source decision, checkpoint
  policy, focused tests and operator documentation.
- [x] (2026-07-27 14:11Z) Passed 5 focused, 41 related and 553 complete tests.
- [x] (2026-07-27 14:35Z) Added exact slot-window validation, exercised the
  supplied 380-row file, passed 555 complete tests and prepared closure.

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
- Observation: the source note distinguishes pre-closing columns from
  `C`-suffixed closing columns and states a Friday/Tuesday collection schedule.
  Evidence: note hash `649fb92e...94d4baf`; all 380 supplied rows have complete
  pre-closing and closing odds, with Bet365 changing in 372 rows.

## Decision Log

- Decision: approve Football-Data for pre-closing historical comparison and
  exact locally observed live snapshots.
  Rationale: the source note identifies the earlier quote family, while our own
  observation supplies the exact availability time required for live use.
  Date/Author: 2026-07-27 / Alastair and Codex.
- Decision: retain every uncaptured live odds slot as an explicit gap.
  Rationale: absence is safer than backfilling an unknown quote after deadline.
  Date/Author: 2026-07-27 / Codex.
- Decision: exclude final scores and outcomes from the normalised comparator.
  Rationale: the input artifact should contain market information only and
  cannot accidentally leak realised results into a forecast.
  Date/Author: 2026-07-27 / Codex.
- Decision: permit a future live snapshot only when this project itself
  observes the pre-closing CSV strictly before the decision cutoff.
  Rationale: an exact local observation proves public availability then;
  Friday/Tuesday wording supplies only a coarse historical schedule.
  Date/Author: 2026-07-27 / Codex.
- Decision: keep 2025/26 schedule-derived availability in a separate
  exploratory arm.
  Rationale: the day-part wording can overlap same-day FPL deadlines and does
  not prove an exact public upload instant.
  Date/Author: 2026-07-27 / Codex.

## Outcomes & Retrospective

The implementation is complete. The supplied file normalises to 380 pre-closing
markets with zero rejected rows and no outcome fields; its source SHA-256 is
`3e3a8352...e784d67b`. Historical admission remains explicitly
schedule-inferred and exploratory. Future captures can enter a live slot only
when their exact observation time falls inside that slot before cutoff. Native
high-frequency and player markets remain gaps.

## Context and Orientation

`control/sources/source-registry.yaml` is the repository authority for source
rights and collection status. It already allows attributed private use of
Football-Data CSVs but forbids redistribution. `src/forecasting/odds_implied.py`
currently derives 1X2 home, draw and away probabilities from Football-Data
columns, preferring Bet365, then Pinnacle and then the source's average columns.
The source note identifies those ordinary columns as pre-closing.

The new `src/ingestion/odds_snapshot.py` is a source-specific normalisation
boundary. A comparator is a market artifact useful for evaluation but
ineligible for strict historical admission without exact capture evidence. A
checkpoint is one of four desired times relative to an FPL deadline. A degraded
checkpoint is a recorded missing capability, not an imputed value.

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

Implement `build_observed_live_snapshot` to stage an exact local observation
only when its observation and availability times precede the decision cutoff.

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


Final proof:

    focused refined contract: 7 passed in 0.11s
    supplied E0.csv: 380 matches, 0 rejected, contains_results=false
    complete repository suite: 555 passed in 348.40s

    .venv/Scripts/python.exe -m pytest -q

No command in this plan downloads a CSV. Existing locally retained source bytes
or test fixtures are passed to the pure normaliser.

## Validation and Acceptance

Given the same CSV bytes in any repeated run, the normaliser must return the
same ordered matches and content hash. Each accepted fixture must have
normalised probabilities summing to one and a
`source_scheduled_preclosing` timing label. No result or score field may appear.

The checkpoint manifest must list T-24h, T-8h, T-2h and final exactly once,
mark all four unavailable for live admission, expose an empty admitted snapshot
list and reference the comparator by its verified hash. A modified comparator
must be rejected.

An exact observation before cutoff must stage a hash-bound live snapshot; the
same observation at or after cutoff must fail closed.

## Idempotence and Recovery

All transformations are pure and content-addressed. They do not download,
overwrite or delete source files. Repeating a transformation is safe. Raw
Football-Data CSVs remain local and ignored by Git; only configuration,
documentation, tests and hashes may be committed.

## Artifacts and Notes

The source decision is:

    selected source: football-data-co-uk
    approved use: historical pre-closing odds and comparator
    live fixed-time admission: exact locally observed pre-cutoff capture only
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

    def build_observed_live_snapshot(
        comparator: Mapping[str, Any],
        *,
        slot: str,
        decision_cutoff: str,
    ) -> dict[str, Any]: ...

The implementation uses Python's standard `csv`, `datetime`, `hashlib` and
`json` modules. No dependency, network collection, authentication, browser
automation or FPL account mutation is introduced.

Revision note (2026-07-27): created after the owner selected Football-Data and
the code audit confirmed that its ordinary CSV odds must remain comparator-only.

Revision note (2026-07-27): refined after the supplied source note and season
CSV established pre-closing semantics and Friday/Tuesday collection cadence;
exact local observation remains mandatory for strict live admission.
