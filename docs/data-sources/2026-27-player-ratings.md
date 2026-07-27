# 2026/27 player-rating source

[StatsBomb Open Data](https://github.com/hudl/open-data) is the selected
zero-cost source for the ratings adapter. It
is already allowed by the sealed 2026/27 feature-family preregistration, and its
published terms permit public research use with attribution. Raw source data is
not committed or redistributed by this repository.

This selection does not imply that current Premier League data exists. No
verified 2026/27 Premier League coverage is presently available in the open
dataset, so the live ratings family starts degraded and the shared forecast
continues byte-identically. A commercial event-data provider can replace it
only after separate terms, cost and owner approval.

## Why common rating sites are disabled

[FotMob's current terms](https://www.fotmob.com/term-of-service) prohibit robots, crawlers and other systematic or regular
use. [Sofascore's terms](https://www.sofascore.com/terms-and-conditions) prohibit scraping or reproducing its database content
without explicit consent. Neither site is therefore used by the automated
collector. FBref also remains disabled until automated collection rights are
explicitly approved.

The adapter performs no network request. It consumes an already-acquired local
envelope containing source-bound rating rows, an exact observation time,
availability time, decision cutoff, methodology identity/version and an
explicit source-player-to-official-FPL-player mapping.

## Capture and quarantine contract

`src/ingestion/player_ratings.py` accepts only the selected, preregistered
`statsbomb-open` source. A commercial or alternative source fails closed even
if it appears in the preregistration; owner approval must first change the
source configuration and adapter allow-list.

Every admitted rating:

- is on a declared 0–10 scale;
- is tied to exact source and derived content hashes;
- records publication, effective and finalisation timestamps when supplied and
  preserves explicit nulls rather than inferring missing times;
- was observed and available strictly before the FPL decision cutoff;
- carries a methodology ID and version;
- resolves through an explicit identity mapping.

Names are context, not keys. Missing, invalid or ambiguous identities are
quarantined rather than matched heuristically. Invalid ratings are quarantined.
Duplicate source IDs fail the whole snapshot because they make the source
payload ambiguous.

Snapshots expire after 720 hours by default. At an evaluation boundary, the
ledger selects the latest admissible non-expired observation per player,
records superseded snapshots and excludes future snapshots. Every snapshot
exposes both quarantine counts and rates.

## Automated local operation

The local transformation is automation-ready:

```powershell
python -m scripts.capture_player_ratings `
  --input data/live-shadow/player-ratings/inbox/<capture>.json `
  --out data/live-shadow/player-ratings/snapshots/<capture>.json
```

The command is idempotent for identical bytes and refuses to overwrite an
existing path with different content. It can be scheduled after an authorised
source export arrives. It deliberately does not automate extraction from
StatsBomb, FPL, FotMob, Sofascore or another website.

Raw and normalised operational snapshots remain under the gitignored
`data/live-shadow/player-ratings/` tree. Only the source contract, manifest,
code and tests are committed.

## Forecast boundary

The feature payload is `shadow_only_pending_point_in_time_ablation`. It carries
ratings but no effect weights. Missing, expired or wholly quarantined input
declares `byte_identical_baseline`. Ratings can influence a decision only in the
isolated `forecast_optimizer_plus_player_ratings` arm and can be promoted only
after the sealed rolling-origin gates and a further owner review pass.
