# WP-04 profile: football-data.co.uk

Profiled at: `2026-07-21T16:49:44Z`

## Licence and use

- Registry: `football-data-co-uk` (enabled for private analysis with attribution).
- Do not republish their CSV files.

## Coverage

| File | rows | FTHG/FTAG | odds columns |
|---|---:|:---:|---:|
| E0_1920.csv | 380 | Y | 48 |
| E0_2021.csv | 380 | Y | 48 |
| E0_2122.csv | 380 | Y | 48 |
| E0_2223.csv | 380 | Y | 48 |
| E0_2324.csv | 380 | Y | 48 |
| E0_2425.csv | 380 | Y | 48 |

## Gaps

- Player-level props (anytime goalscorer) are thin historically; derive clean-sheet / match probs from 1X2 and totals where needed (plan §11.2).
- No FPL player IDs — join to FPL via team/date fixtures only.

## Leakage risk

- Closing odds may include late information; for decision replay prefer odds captured before the FPL deadline (live capture going forward).
- Historical CSVs are typically closing or settlement-oriented — label as such; do not claim pre-deadline without timestamps.

