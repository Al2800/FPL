# WP-04: Point-in-time news recoverability

Assessed at: `2026-07-21T16:49:44Z`

Evidence-dependent historical replay is generally NOT feasible from vaastav alone: structured stats are preserved, but the pre-deadline news / predicted-line-up environment is not. Recoverable islands: (1) any archived bootstrap-static snapshots that include news/news_added with observed_at <= deadline; (2) selective Wayback captures of club/injury pages for named GWs. Default stance per Section 17.6: use multi-season replay for structured-data strategies only; lean on live 2026/27 day-one archives for evidence-dependent questions.

**Evidence-dependent feasibility:** `low_without_external_archives`

## Per-season merged_gw news field

| Season | news column | Note |
|---|:---:|---|
| 2016-17 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2017-18 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2018-19 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2019-20 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2020-21 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2021-22 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2022-23 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2023-24 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2024-25 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |
| 2025-26 | N | merged_gw lacks a news column — pre-deadline news environment not preserved here |

## Recommended structured-only pilot Gameweeks

- 2023-24: GW [1, 10, 20, 30, 38]
- 2024-25: GW [1, 10, 20, 30]

## Implication for WP-09

Size the replay harness for hundreds of structured decisions (ADR-0004). Do not block harness work on historical news reconstruction — limit that to a feasibility sample if Wayback/bootstrap archives appear later.

