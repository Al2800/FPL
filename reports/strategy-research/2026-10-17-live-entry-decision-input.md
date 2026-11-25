# Live-entry decision input — 2026-10-17

- observed_at: 2026-10-17T07:05:00Z
- next_deadline: 2026-10-17T10:00:00Z (GW7)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-17.md` (reconstructed 15 is **not** either owned squad)
- City presser: **landed** Fri 16 Oct — Haaland confirmed in Ipswich squad; rest talk general; ledger minutes doubtful `model:790c6cad…` (available claim rejected)

## Executive decision

**Haaland arm (8522487):** GW6 finished sample **64 pts** with **Haaland (C) / Bruno (VC)**. No chip used in GW6. Into GW7: set **Haaland (C)** and prefer **TC Haaland** vs IPS (H) — presser confirms squad presence; treat rest talk as soft minutes risk. Free transfer: prefer **Dewsbury-Hall or E.Le Fée → Groß** (BHA–CRY H; ep_next **10.0**) if chasing the Brighton stack; else roll. **Gibbs-White now `d`/75%** — hold with Xhaka cover unless certainty is required (then Gibbs-White→Groß). Reject Schade. Hold Thiago vs LIV (H).

**No-Haaland arm (7337262):** GW6 finished sample **66 pts**. Isak bootstrap softens to **`d`/25%** (was `i`/0%) while ledger remains **doubtful** (`model:ef06ce17…`) — still priority FT out unless cleared. **Semenyo hold** (ep **10.0**). Obi remains **loan `u`** dead slot; Shaw **`d`/75%** is in the starting DEF line — two soft spots plus Isak. Into GW7: **Isak → active FWD** first; Obi repair is FT2 or WC pressure if a third hole opens. Prefer **Palmer or Semenyo (C)** over forcing a Haaland-less TC; if pivoting to Haaland this week, align chip with that move rather than WC by default.

## Official entry state

GW6 finished (`finished=True`); GW7 picks endpoint still **404** (window not open for public picks read). Morning sample:

| entry | arm | GW6 pts (sample) | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 64 | 356 | ~4.69m |
| 7337262 | no Haaland | 66 | 357 | ~4.63m |

| entry | bank (event hist / last deadline) | chips used | GW6 transfers | team value |
|---|---:|---|---:|---:|
| 8522487 | £0.2m | none | 0 | 99.4 |
| 7337262 | £0.0m | none | 0 | 99.7 |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW6 picks, refreshed)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.6 | a | XI — ep_next 7.5 into CRY (H) |
| DEF | Van Hecke | TOT | 4.9 | a 100% | XI — ep 4.5 / 27 pts |
| DEF | Mitchell | CRY | 4.5 | a | XI |
| DEF | Diop | IPS | 4.0 | a | XI — MCI (A) tough |
| MID | B.Fernandes | MUN | 11.8 | a | **VC** — LEE (A); ep 1.5 |
| MID | Gibbs-White | NFO | 8.0 | d 75% | XI — ARS (H); muscular — hold with Xhaka cover |
| MID | E.Le Fée | SUN | 5.7 | a | XI — funding route for Groß |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI — ep 8.0 |
| FWD | Haaland | MCI | 15.7 | a | **(C)** / **TC** — IPS (H); in squad; minutes doubtful tip |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI — EVE (A) 11:30Z |
| FWD | Thiago | BRE | 7.8 | a | XI — LIV (H); ep 4.5 |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | Xhaka | SUN | 5.4 | a | Gibbs-White cover |
| BEN | Castagne | FUL | 4.5 | a | ep 0.5 |
| BEN | van Ewijk | COV | 3.9 | a 100% | |

### 7337262 — no-Haaland arm (GW6 picks, refreshed)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.1 | a | XI — NFO (A) |
| DEF | Gabriel | ARS | 7.9 | a | XI |
| DEF | Guéhi | MCI | 6.0 | a | XI — IPS (H); ep 5.0 |
| DEF | Truffert | BOU | 5.4 | a | XI — ep 0.5 |
| DEF | Shaw | MUN | 4.3 | d 75% | **doubtful** starter |
| MID | Palmer | CHE | 9.7 | a 100% | **(C)** path — EVE (A); ep 5.0 |
| MID | Semenyo | MCI | 8.3 | a 100% | ep **10.0**; prior PSG start |
| MID | Rice | ARS | 7.3 | a 100% | XI |
| MID | Anderson | MCI | 6.3 | a 100% | XI — IPS (H) |
| MID | Rogers | CHE | 7.9 | a | **VC** — EVE (A); ep 5.5 |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI |
| BEN | Verbruggen | BHA | 4.6 | a | |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | Isak | LIV | 9.0 | d 25% | ledger **doubtful** `model:ef06ce17…` — priority FT out |
| BEN | Obi | MUN | 4.5 | u 0% | loan — dead slot |

## Recommended owned actions (advisory only)

### Into GW7

- **8522487:** set **Haaland (C) / Bruno (VC)**; prefer **TC** on Haaland for IPS (H) after presser confirmed squad presence; FT Groß from DH/E.Le Fée **or roll**; hold Gibbs-White at 75% unless certainty needed; reject Schade; hold Thiago vs LIV.
- **7337262:** priority **Isak → active FWD**; hold Semenyo; set **Palmer (C) / Rogers (VC)** unless pivoting to Haaland+TC; Shaw/Obi remain soft spots — WC only if a third hole opens.

Account writes: false. Owner approval still required.
