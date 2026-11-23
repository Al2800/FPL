# Live entry decision input — 2026-11-23

- observed_at: 2026-11-23T07:04:00Z
- model: Cursor Grok 4.5 High
- season: 2026-27
- next deadline: GW12 **2026-11-27T18:30:00Z** (ARS vs MCI **2026-11-29T16:30:00Z**)
- GW11 deadline already locked 2026-11-21T11:00:00Z; GW11 **is_current** (not finished / not data_checked); BRE vs EVE tonight **2026-11-23T20:00:00Z**
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-11-23.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** Entry-history shows GW11 provisional **35** / total **630** / OR ~3.03m with **active_chip=none** (Haaland (C) only — TC not played). Haaland return **2**. Into GW12: **do not** default FH solely for Arsenal (A); prefer **Bruno / Evanilson / Tavernier / Groß** captain schools over Haaland; plan a **Thiago** replacement (still bootstrap **`s`** until 5 Dec) before/into the next window; hold WC/BB unless ≥3 holes after GW11 finalises. Advisory McGinn FT does **not** map onto this owned squad. Do not chase Gakpo (`model:7e6157ba…`).

**No-Haaland arm (7337262):** Entry-history shows GW11 provisional **45** / total **662** / OR ~1.64m with **active_chip=none**. Raya remains ledger **doubtful** (`model:bfcc1caa…`; today’s refresh was a host duplicate) — first owned GK risk into GW12. Isak (C) finished **5** vs United. Into GW12: hold chips; captain among Palmer / Tavernier / Evanilson / Rogers / N.Jackson / Bruno schools; do not force Haaland without a WC plan; watch Raya MRI before any GK hit.

## Official entry state

| entry | arm | GW11 pts (provisional) | total (history) | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 35 | 630 | ~3.03m |
| 7337262 | no Haaland | 45 | 662 | ~1.64m |

| entry | GW11 transfers | GW11 transfer cost | active chip |
|---|---:|---:|---|
| 8522487 | 0 | 0 | none |
| 7337262 | 0 | 0 | none |

Public endpoints do not expose current free transfers for GW12, pending transfers, purchase prices or selling prices. Manager state remains degraded for the next window.

## Authoritative squads, prices and flags (Monday morning bootstrap)

### 8522487 — Haaland arm (GW11 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.7 | a | XI |
| DEF | Van Hecke | TOT | 5.2 | a | XI; ep_next **8.0** |
| DEF | Gabriel | ARS | 8.1 | a | XI; ep_next **8.0** |
| DEF | De Cuyper | BHA | 5.5 | a | XI |
| MID | Groß | BHA | 6.3 | a | XI |
| MID | Tavernier | BOU | 6.7 | a | XI; GW11 **8** |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Dewsbury-Hall | EVE | 6.7 | a | XI; BRE tonight |
| FWD | Evanilson | BOU | 6.6 | a | **VC**; GW11 **6** |
| FWD | Thiago | BRE | 7.8 | s | XI; suspended until 5 Dec |
| FWD | Haaland | MCI | 15.8 | a | **C**; GW11 **2**; no TC |
| BEN | Dubravka | TOT | 3.9 | a | |
| BEN | Gibbs-White | NFO | 7.8 | a | |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | van Ewijk | COV | 3.9 | a | |

### 7337262 — no-Haaland arm (GW11 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.3 | d | XI; ledger doubtful `model:bfcc1caa…` |
| DEF | Truffert | BOU | 5.4 | a | XI; GW11 **6** |
| DEF | De Cuyper | BHA | 5.5 | a | XI |
| DEF | Gabriel | ARS | 8.1 | a | XI |
| MID | Rogers | CHE | 8.3 | a | XI; GW11 **5** |
| MID | Palmer | CHE | 9.8 | a | XI |
| MID | Tavernier | BOU | 6.7 | a | XI; GW11 **8** |
| MID | Rice | ARS | 7.5 | a | XI |
| FWD | Evanilson | BOU | 6.6 | a | **VC** |
| FWD | N.Jackson | AVL | 7.3 | a | XI; price rose; GW11 **2** |
| FWD | Isak | LIV | 9.3 | a | **C**; GW11 **5** |
| BEN | Verbruggen | BHA | 4.7 | a | |
| BEN | Guéhi | MCI | 5.9 | a | GW11 **2** |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | Anderson | MCI | 6.2 | a | GW11 **10** |

## GW12 guidance (entries)

- **8522487:** Move captain off Haaland for Arsenal (A); prefer Bruno/Tavernier/Evanilson/Groß schools; replace Thiago before/into next window; hold WC/BB/FH; do not buy DCL/Jackson/Barry/Gakpo purely on transfer tables.
- **7337262:** Hold chips; captain among Palmer / Tavernier / Evanilson / Rogers / N.Jackson; monitor Raya MRI (`model:bfcc1caa…`) before a GK hit; do not force Haaland without WC plan.
- Both: ignore Savio (`model:c54437d9…`) / Semenyo / João Pedro (`model:10d64bad…`) / Gakpo (`model:7e6157ba…`) / Hinshelwood / Alysson chase into owned squads. Ledger tip now `7c3a3fb3…`.
