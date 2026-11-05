# Live-entry decision input — 2026-11-05

- observed_at: 2026-11-05T07:04:17Z
- next_deadline: 2026-11-06T18:30:00Z (GW10); GW9 deadline already locked 2026-10-31T11:00:00Z and event **finished + data_checked**
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-11-05.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** GW9 sealed **69** (Haaland C on **2**; Evanilson VC). Total **527** / OR ~3.62m. **2 transfers / cost 0** in GW9 (João Pedro → Evanilson; Xhaka → Tavernier). Into GW10: keep **Haaland (C)** @ NFO (A); prefer **Bruno / Evanilson / Thiago** class as VC over another City blank risk; this entry already owns Evanilson + Thiago + Tavernier so use FT only on a clear dead asset or roll. Hold chips (no TC @ Forest). Do not chase Porro/Mateta/Munoz/Madueke/J.Timber/Saliba/Quinten Timber/Strand Larsen into this owned squad.

**No-Haaland arm (7337262):** GW9 sealed **70**. Total **549** / OR ~2.43m. **1 transfer / cost 0**. Into GW10: **hold chips**; captain among Palmer / Tavernier / Evanilson / Rogers / N.Jackson / Gabriel schools — Palmer bootstrap still **`a`/100%** (Chelsea reinforce pages still HTTP 500); do not force Haaland without a WC plan; FT toward any remaining flagged hole rather than template chase if already owned. Fresh Timber/Strand Larsen admits do **not** force a Palace chase into this owned squad this morning.

## Official entry state

| entry | arm | GW9 pts (sealed) | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 69 | 527 | ~3.62m |
| 7337262 | no Haaland | 70 | 549 | ~2.43m |

| entry | GW9 transfers | GW9 transfer cost | active chip |
|---|---:|---:|---|
| 8522487 | 2 | 0 | none |
| 7337262 | 1 | 0 | none |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded. GW10 picks endpoint still 404 pre-deadline.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW9 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.6 | a | XI |
| DEF | Van Hecke | TOT | 5.0 | a | XI |
| DEF | Diop | IPS | 3.9 | a | XI |
| DEF | van Ewijk | COV | 3.9 | a | XI |
| MID | B.Fernandes | MUN | 11.7 | a | XI |
| MID | Tavernier | BOU | 6.6 | a | XI — community heat owned |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Gibbs-White | NFO | 7.8 | a | XI; price fell to £7.8m |
| FWD | Evanilson | BOU | 6.4 | a | **VC** |
| FWD | Thiago | BRE | 7.8 | a | XI |
| FWD | Haaland | MCI | 15.8 | a | **C** |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | Dewsbury-Hall | EVE | 6.6 | a | |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | Mitchell | CRY | 4.5 | a | |

### 7337262 — no-Haaland arm (GW9 picks; API position order)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.2 | a | XI |
| DEF | Gabriel | ARS | 8.0 | a | XI; community captain school vs HUL |
| DEF | Truffert | BOU | 5.4 | a | XI |
| DEF | Davis | IPS | 4.0 | a | XI |
| MID | Palmer | CHE | 9.8 | a | **C**; bootstrap `a`/100% |
| MID | Tavernier | BOU | 6.6 | a | XI |
| MID | Anderson | MCI | 6.3 | a | XI |
| MID | Rogers | CHE | 8.2 | a | XI |
| FWD | N.Jackson | AVL | 7.0 | a | XI |
| FWD | Isak | LIV | 9.2 | a | XI; Gravenberch unavailable tip is midfield-only |
| FWD | Evanilson | BOU | 6.4 | a | **VC** |
| BEN | Verbruggen | BHA | 4.6 | a | |
| BEN | Guéhi | MCI | 6.0 | a | |
| BEN | Rice | ARS | 7.4 | a | |
| BEN | Castagne | FUL | 4.5 | a | |

## GW10 guidance (entries)

- **8522487:** Haaland (C); VC off pure City stack risk toward Bruno/Evanilson/Thiago; hold chips; FT only if a clear dead asset remains — do not TC @ Forest.
- **7337262:** Captain among Palmer / Tavernier / Evanilson / Rogers / N.Jackson / Gabriel schools; hold chips; do not force Haaland without WC plan.
- Both: ignore Saka / Semenyo / Minteh / Wieffer / Bergvall / Sávio / Carvalho / Sarr / Porro / Mateta / Madueke / J.Timber / Frimpong / Goretzka / Saliba / Gravenberch / Quinten Timber / Strand Larsen chase into owned squads; reject TC Haaland vs Forest; DCL remains advisory-core for the reconstructed XV, optional flavour only for these owned squads.

## Host handoff

- Account writes: false
- Owner approval still required before any FPL entry
- Companion advisory hashes: model-run `composer-2.5:2026-11-05T070417Z`; ledger tip `dfb3263b…`
