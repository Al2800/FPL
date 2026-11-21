# Live entry decision input — 2026-11-21

- observed_at: 2026-11-21T07:05:00Z
- model: Cursor Grok 4.5 High
- season: 2026-27
- next deadline: GW11 **2026-11-21T11:00:00Z** (MCI vs FUL **2026-11-21T12:30:00Z**)
- GW10 deadline already locked 2026-11-06T18:30:00Z; GW10 **finished + data_checked** (still `is_current`)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-11-21.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** Entry-history shows GW10 **68** / total **595** / OR ~3.07m after `data_checked`. Prefer **Triple Captain Haaland vs Fulham (H)** — City Friday presser published (Nunes/Khusanov doubts only; Haaland not named); Implied Fantasy ~7.8 xP / ~15.6 as captain. Keep **Evanilson VC**. Thiago still bootstrap **`s`** until 5 Dec — first owned FWD hole; do **not** force DCL/N.Jackson/Barry into the owned squad today. Hold WC/BB/FH. Advisory Xhaka→McGinn FT does **not** map onto this owned squad.

**No-Haaland arm (7337262):** Entry-history shows GW10 **68** / total **617** / OR ~2.05m after `data_checked`. Into GW11: do **not** force Haaland without a WC plan; captain among Palmer / Tavernier / Evanilson / Rogers / N.Jackson / Gabriel / Isak schools (Isak home vs United is the cleanest non-Haaland ceiling among owned options); hold chips unless a true multi-hole WC appears. Guéhi bench flag **`d`/75%** remains watch-only (City presser body expects him available — not ledger-admitted). João Pedro unavailable `model:68e3aff6…` is not owned.

## Official entry state

| entry | arm | GW10 pts (entry history) | total (history) | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 68 | 595 | ~3.07m |
| 7337262 | no Haaland | 68 | 617 | ~2.05m |

| entry | GW10 transfers | GW10 transfer cost | active chip |
|---|---:|---:|---|
| 8522487 | 3 | 0 | none |
| 7337262 | 1 | 0 | none |

Public endpoints do not expose current free transfers for GW11, pending transfers, purchase prices or selling prices. Manager state remains degraded for the next window.

## Authoritative squads, prices and flags (deadline morning bootstrap)

### 8522487 — Haaland arm (GW10 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.7 | a | XI |
| DEF | Van Hecke | TOT | 5.1 | a | XI; ep_next **8.7** |
| DEF | Gabriel | ARS | 8.1 | a | XI |
| DEF | De Cuyper | BHA | 5.5 | a | XI |
| MID | Groß | BHA | 6.3 | a | XI |
| MID | Tavernier | BOU | 6.7 | a | XI |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Dewsbury-Hall | EVE | 6.7 | a | XI |
| FWD | Evanilson | BOU | 6.5 | a | **VC** |
| FWD | Thiago | BRE | 7.8 | s | XI; suspended until 5 Dec |
| FWD | Haaland | MCI | 15.8 | a | **C / prefer TC**; City presser clear |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | Gibbs-White | NFO | 7.8 | a | |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | van Ewijk | COV | 3.9 | a | |

### 7337262 — no-Haaland arm (GW10 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.2 | a | XI |
| DEF | Truffert | BOU | 5.4 | a | XI |
| DEF | De Cuyper | BHA | 5.5 | a | XI |
| DEF | Gabriel | ARS | 8.1 | a | XI |
| MID | Rogers | CHE | 8.2 | a | XI |
| MID | Palmer | CHE | 9.8 | a | XI |
| MID | Tavernier | BOU | 6.7 | a | XI |
| MID | Rice | ARS | 7.5 | a | XI |
| FWD | Evanilson | BOU | 6.5 | a | **VC** |
| FWD | N.Jackson | AVL | 7.2 | a | XI; ep_next **11.0** |
| FWD | Isak | LIV | 9.3 | a | **C** candidate |
| BEN | Verbruggen | BHA | 4.7 | a | |
| BEN | Guéhi | MCI | 6.0 | d | bootstrap **`d`/75%**; presser body expects available |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | Anderson | MCI | 6.2 | a | |

## GW11 guidance (entries)

- **8522487:** Prefer **TC Haaland** vs Fulham (H); plan a Thiago replacement before/into the next window (suspended); VC Evanilson; hold WC/BB/FH; do not buy DCL/Jackson/Barry purely on transfer tables.
- **7337262:** Hold chips; captain among Isak / Palmer / Tavernier / Evanilson / Rogers / N.Jackson / Gabriel; do not force Haaland without WC plan; watch Guéhi **`d`**.
- Both: ignore Bergvall / Sávio / Mudryk / Sarr / Mateta / Porro / Madueke / Semenyo / Quinten Timber / Forest scalp chase into owned squads. Ledger tip now `a2db711d…` (prior Hinshelwood available `model:96335a3e…` still watchlist only); João Pedro unavailable `model:68e3aff6…`; Gravenberch/Frimpong available `model:cb3203ec…` / `model:da9c23c0…` watchlist overlays.
