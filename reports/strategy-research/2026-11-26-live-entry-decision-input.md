# Live entry decision input — 2026-11-26

- observed_at: 2026-11-26T07:05:00Z
- model: Cursor Grok 4.5 High
- season: 2026-27
- next deadline: GW12 **2026-11-27T18:30:00Z** (ARS vs MCI **2026-11-29T16:30:00Z**)
- GW11 deadline already locked 2026-11-21T11:00:00Z; GW11 **finished + data_checked** (still **is_current**)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-11-26.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** Entry-history shows GW11 **39** / total **634** / OR ~2.91m with **active_chip=none** (Haaland (C) only — TC not played). Haaland return **2**. Into GW12: **do not** default FH solely for Arsenal (A); prefer **Bruno / Evanilson / Tavernier / Groß** captain schools over Haaland (bootstrap ep_next **2.0**); plan a **Thiago** replacement (still bootstrap **`s`** / ledger unavailable) before/into the next window; hold WC/BB. Advisory McGinn FT does **not** map onto this owned squad. Do not chase Gakpo (`model:9870337d…`) or Gravenberch (`model:69fd218f…`) or Semenyo (`model:d5076db3…`).

**No-Haaland arm (7337262):** Entry-history shows GW11 **45** / total **662** / OR ~1.68m with **active_chip=none**. Raya remains ledger **doubtful** (`model:f30e2c54…` — post-Dortmund still unresolved for Sunday) — first owned GK risk into GW12. Isak (C) finished **5** vs United and started/scored in Europe midweek. Into GW12: hold chips; captain among Palmer / Tavernier / Evanilson / Rogers / N.Jackson / Bruno / Isak schools; do not force Haaland without a WC plan; watch Raya further tests before any GK hit. N.Jackson already owned — ep_next **7.3** / IPS (A) is a live captain option for this arm only.

## Official entry state

| entry | arm | GW11 pts | total (history) | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 39 | 634 | ~2.91m |
| 7337262 | no Haaland | 45 | 662 | ~1.68m |

| entry | GW11 transfers | GW11 transfer cost | active chip |
|---|---:|---:|---|
| 8522487 | 0 | 0 | none |
| 7337262 | 0 | 0 | none |

Public endpoints do not expose current free transfers for GW12, pending transfers, purchase prices or selling prices. Manager state remains degraded for the next window.

## Authoritative squads, prices and flags (Thursday morning bootstrap)

### 8522487 — Haaland arm (GW11 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.7 | a | XI; GW11 **2**; ep_next **6.3** |
| DEF | Van Hecke | TOT | 5.2 | a | XI; ep_next **8.3**; GW11 **6** |
| DEF | Gabriel | ARS | 8.1 | a | XI |
| DEF | De Cuyper | BHA | 5.5 | a | XI |
| MID | Groß | BHA | 6.3 | a | XI |
| MID | Tavernier | BOU | 6.8 | a | XI; GW11 **8** |
| MID | E.Le Fée | SUN | 5.7 | a | XI; ep_next **7.3** |
| MID | Dewsbury-Hall | EVE | 6.7 | a | XI |
| FWD | Evanilson | BOU | 6.6 | a | **VC**; ep_next **8.0** |
| FWD | Thiago | BRE | 7.8 | s | XI; suspended |
| FWD | Haaland | MCI | 15.8 | a | **C**; ep_next **2.0**; no TC |
| BEN | Dubravka | TOT | 3.9 | a | |
| BEN | Gibbs-White | NFO | 7.8 | a | |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | van Ewijk | COV | 3.9 | a | |

### 7337262 — no-Haaland arm (GW11 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.2 | d | XI; ledger doubtful `model:f30e2c54…` |
| DEF | Truffert | BOU | 5.4 | a | XI |
| DEF | De Cuyper | BHA | 5.5 | a | XI |
| DEF | Gabriel | ARS | 8.1 | a | XI |
| MID | Rogers | CHE | 8.3 | a | XI |
| MID | Palmer | CHE | 9.8 | a | XI |
| MID | Tavernier | BOU | 6.8 | a | XI |
| MID | Rice | ARS | 7.5 | a | XI |
| FWD | Evanilson | BOU | 6.6 | a | **VC** |
| FWD | N.Jackson | AVL | 7.3 | a | XI; ep_next **7.3**; IPS (A) |
| FWD | Isak | LIV | 9.4 | a | **C**; ep_next **5.0** |
| BEN | Verbruggen | BHA | 4.7 | a | |
| BEN | Guéhi | MCI | 5.9 | a | |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | Anderson | MCI | 6.2 | a | |

## Chip and transfer notes (entry-specific)

- Both arms: **hold BB/FH/WC**; unused TC → prefer Haaland Hull GW16 if Haaland-owned, else do not burn TC on a non-owned premium.
- 8522487: first FT priority is **Thiago → playing FWD** (Evanilson already owned; community Jackson heat is optional not mandatory).
- 7337262: first risk is **Raya**; Arteta post-Dortmund still unresolved for Sunday — prefer bench Verbruggen over a panic sell until further tests; Jackson already owned so advisory “do not force-buy Jackson” does not apply as a sell instruction.
