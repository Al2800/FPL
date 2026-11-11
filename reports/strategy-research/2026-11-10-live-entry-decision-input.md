# Live-entry decision input — 2026-11-10

- observed_at: 2026-11-10T07:05:19Z
- next_deadline: 2026-11-21T11:00:00Z (GW11); GW10 deadline already locked 2026-11-06T18:30:00Z; GW10 now **finished + data_checked**
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-11-10.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** Entry-history now shows GW10 **68** / total **595** / OR ~3.07m after `data_checked`. **3 transfers / cost 0** already used in GW10: Mitchell → De Cuyper; Diop → Gabriel; B.Fernandes → Groß (confirmed on picks). Prefer **Triple Captain Haaland vs Fulham (H)** if fit through the IB; keep **Evanilson VC** class; Thiago still bootstrap **`s`** until 5 Dec — first owned FWD hole for the IB; do **not** force DCL/N.Jackson/Barry into the owned squad today; ignore Delap/Tel/Strand Larsen chase. Hold WC/BB/FH.

**No-Haaland arm (7337262):** Entry-history now shows GW10 **68** / total **617** / OR ~2.05m after `data_checked`. **1 transfer / cost 0** in GW10: Davis → De Cuyper. Into GW11: do **not** force Haaland without a WC plan; captain among Palmer / Tavernier / Evanilson / Rogers / N.Jackson / Gabriel / Isak schools; hold chips unless a true multi-hole WC appears. Guéhi bench flag **`d`** is watch-only. Szoboszlai IB knee doubt `model:3f1268ae…` is watchlist-only for this arm’s Liverpool exposure via Isak, not a MID buy.

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

## Authoritative squads, prices and flags (Tuesday morning bootstrap)

### 8522487 — Haaland arm (GW10 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.6 | a | XI |
| DEF | Van Hecke | TOT | 5.1 | a | XI |
| DEF | Gabriel | ARS | 8.1 | a | XI |
| DEF | De Cuyper | BHA | 5.5 | a | XI |
| MID | Groß | BHA | 6.3 | a | XI |
| MID | Tavernier | BOU | 6.7 | a | XI |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI |
| FWD | Evanilson | BOU | 6.5 | a | **VC** |
| FWD | Thiago | BRE | 7.8 | s | XI; suspended until 5 Dec |
| FWD | Haaland | MCI | 15.8 | a | **C** |
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
| FWD | N.Jackson | AVL | 7.1 | a | XI |
| FWD | Isak | LIV | 9.3 | a | **C** |
| FWD | Evanilson | BOU | 6.5 | a | **VC** |
| BEN | Verbruggen | BHA | 4.6 | a | |
| BEN | Guéhi | MCI | 6.0 | d | bootstrap doubtful flag |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | Anderson | MCI | 6.2 | a | |

## GW11 guidance (entries)

- **8522487:** Prefer **TC Haaland** vs Fulham (H) if fit through the IB; plan a Thiago replacement before GW11 (suspended); VC off pure City stack risk toward Evanilson; hold WC/BB/FH; do not buy DCL/Jackson/Barry purely on transfer tables; ignore Saka/Semenyo/Delap/Tel/Strand Larsen chase.
- **7337262:** Hold chips; captain among Palmer / Tavernier / Evanilson / Rogers / N.Jackson / Gabriel / Isak; do not force Haaland without WC plan; watch Guéhi **`d`**; Szoboszlai IB knee is not an owned-squad transfer trigger.
- Both: ignore Bergvall / Sávio / Mudryk / Sarr / Mateta / Porro / Madueke / Semenyo / Quinten Timber / Forest scalp chase into owned squads. Lane A tip `a11ca1d6…` adds Szoboszlai doubtful; João Pedro remains unavailable on the prior tip chain.

## Host handoff

- Companion only; does not clear owner approval or set `ready_for_manual_entry`
- Account writes: false
- Owner approval still required before any FPL entry
