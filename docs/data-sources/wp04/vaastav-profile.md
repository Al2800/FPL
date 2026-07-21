# WP-04 profile: vaastav/Fantasy-Premier-League

Profiled at: `2026-07-21T16:49:44Z`
Local path: `data/raw/vaastav/Fantasy-Premier-League` (gitignored)

## Licence and use

- Registry: `vaastav-fpl` (enabled for private local use only).
- Upstream code MIT; underlying data property of FPL / Understat — **no redistribution**.
- ADR-0001 / ADR-0007 apply.

## Coverage

Seasons present: 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26

| Season | rows | players | GWs | xP | minutes | value | selected | defensive cols | xP↔pts corr |
|---|---:|---:|---:|:---:|:---:|:---:|:---:|---|---:|
| 2016-17 | 23679 | 683 | 38 | N | Y | Y | Y | clearances_blocks_interceptions, recoveries, tackled, tackles | — |
| 2017-18 | 22467 | 647 | 38 | N | Y | Y | Y | clearances_blocks_interceptions, recoveries, tackled, tackles | — |
| 2018-19 | 21790 | 624 | 38 | N | Y | Y | Y | clearances_blocks_interceptions, recoveries, tackled, tackles | — |
| 2019-20 | 22560 | 666 | 38 | N | Y | Y | Y | — | — |
| 2020-21 | 24365 | 713 | 38 | Y | Y | Y | Y | — | 0.66 |
| 2021-22 | 25447 | 737 | 38 | Y | Y | Y | Y | — | 0.66 |
| 2022-23 | 26505 | 778 | 37 | Y | Y | Y | Y | — | 0.66 |
| 2023-24 | 29725 | 865 | 38 | Y | Y | Y | Y | — | 0.69 |
| 2024-25 | 27605 | 804 | 38 | Y | Y | Y | Y | — | 0.66 |
| 2025-26 | 29757 | 841 | 38 | Y | Y | Y | Y | clearances_blocks_interceptions, defensive_contribution, recoveries, tackles | 0.35 |

## Gaps

- No reliable pre-deadline `news` / predicted line-ups in `merged_gw` (see news assessment).
- Defensive-contribution action detail sparse before 2025/26; official endpoints now expose DC fields for live work.
- Season completeness varies; confirm final GW count before training.

## Leakage risk

- Treat `xP` as **unsafe for same-GW labels** unless independently verified as pre-deadline; prefer shift(1) or drop.
- `total_points`, bonus, and BPS in the same row as features for that GW are outcomes — use only as labels or lagged features.
- Prices/`selected` mid-GW may reflect post-deadline movement depending on scrape time; prefer features known at deadline.

## Identity match rates (consecutive seasons via FPL `code`)

| From | To | method | n_from | n_to | matched | rate_from | rate_to |
|---|---|---|---:|---:|---:|---:|---:|
| 2016-17 | 2017-18 | fpl_code | 683 | 647 | 435 | 0.637 | 0.672 |
| 2017-18 | 2018-19 | fpl_code | 647 | 624 | 421 | 0.651 | 0.675 |
| 2018-19 | 2019-20 | fpl_code | 624 | 666 | 430 | 0.689 | 0.646 |
| 2019-20 | 2020-21 | fpl_code | 666 | 713 | 455 | 0.683 | 0.638 |
| 2020-21 | 2021-22 | fpl_code | 713 | 737 | 466 | 0.654 | 0.632 |
| 2021-22 | 2022-23 | fpl_code | 737 | 778 | 467 | 0.634 | 0.6 |
| 2022-23 | 2023-24 | fpl_code | 778 | 865 | 526 | 0.676 | 0.608 |
| 2023-24 | 2024-25 | fpl_code | 865 | 804 | 513 | 0.593 | 0.638 |
| 2024-25 | 2025-26 | fpl_code | 804 | 841 | 534 | 0.664 | 0.635 |
