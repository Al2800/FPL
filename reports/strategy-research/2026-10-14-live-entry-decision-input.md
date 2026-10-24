# Live-entry decision input — 2026-10-14

- observed_at: 2026-10-14T07:00:24Z
- next_deadline: 2026-10-17T10:00:00Z (GW7)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-14.md` (reconstructed 15 is **not** either owned squad)
- City–PSG: kickoff tonight (still pre-match at this observed_at)

## Executive decision

**Haaland arm (8522487):** GW6 finished sample **64 pts** with **Haaland (C) / Bruno (VC)**. No chip used in GW6. Into GW7: prefer **Haaland (C)** and strongly consider **TC Haaland** vs IPS (H). Free transfer: prefer **Dewsbury-Hall or E.Le Fée → Groß** (BHA–CRY H; ep_next **10.0**) if chasing the Brighton stack; else roll. **Reject Schade** (`model:e63a6717…`). Semenyo ep_next **10.0** is loud but this squad already has City via Haaland — do not force a second City mid without structure need. Reassess after tonight’s PSG minutes.

**No-Haaland arm (7337262):** GW6 sample **66 pts** (entry summary; picks endpoint 403 this morning — squad table below uses 13 Oct GW6 picks + today’s bootstrap overlays). Isak remains **unavailable** (`model:6afa25fe…` + bootstrap `i`/0%) — priority FT out. **Semenyo hold** (`model:4068dbc3…`, ep **10.0**). Obi remains **loan `u`** dead slot; Shaw **`d`/75%**. Into GW7: **Isak → active FWD** first; Obi repair is FT2 or WC pressure if a second hole opens. Prefer **Palmer or Semenyo (C)** over forcing a Haaland-less TC; if pivoting to Haaland this week, align chip with that move rather than WC by default.

## Official entry state

GW6 finished (`finished=True`); GW7 is next. Morning sample:

| entry | arm | GW6 pts (sample) | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 64 | 356 | ~4.69m |
| 7337262 | no Haaland | 66 | 357 | ~4.63m |

| entry | bank (event hist / last deadline) | chips used | GW6 transfers |
|---|---:|---|---:|
| 8522487 | £0.2m | none | 0 |
| 7337262 | £0.0m | none | 0 |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded. Entry `7337262` GW6 picks fetch returned HTTP 403 this morning — treat that squad block as prior-day continuity with bootstrap overlays.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW6 picks, refreshed)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.6 | a | XI — ep_next 7.5 into CRY (H); price rose |
| DEF | Van Hecke | TOT | 4.9 | a 100% | XI |
| DEF | Mitchell | CRY | 4.5 | a | XI — started Forest `model:182761e0…` |
| DEF | Diop | IPS | 4.0 | a | XI — MCI (A) tough |
| MID | B.Fernandes | MUN | 11.9 | a | **VC** — LEE (A); ep 1.5 |
| MID | Gibbs-White | NFO | 8.0 | a 100% | XI — ARS (H) |
| MID | E.Le Fée | SUN | 5.7 | a | XI — funding route for Groß |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI — ep 8.0 |
| FWD | Haaland | MCI | 15.6 | a | **(C)** / **TC watch** — IPS (H) |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI — EVE (A) |
| FWD | Thiago | BRE | 7.8 | a | XI — LIV (H); ep 4.5 |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | Xhaka | SUN | 5.4 | a | |
| BEN | Castagne | FUL | 4.5 | a | ep 0.5 |
| BEN | van Ewijk | COV | 3.9 | a 100% | |

### 7337262 — no-Haaland arm (GW6 picks continuity; 403 on refresh)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.1 | a | XI — NFO (A) |
| DEF | Gabriel | ARS | 7.9 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | XI |
| DEF | Guéhi | MCI | 6.0 | a | XI — IPS (H); ep 5.0 |
| MID | Rogers | CHE | 7.9 | a | **VC** (prior) |
| MID | Palmer | CHE | 9.7 | a 100% | **(C)** path — EVE (A); ep 5.0 |
| MID | Semenyo | MCI | 8.3 | a 100% | **cleared** — IPS (H); ep **10.0** |
| MID | Rice | ARS | 7.3 | a | XI |
| MID | Anderson | MCI | 6.3 | a | XI — IPS (H) |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI |
| FWD | Isak | LIV | 9.0 | i 0% | **unavailable** `model:6afa25fe…` — priority FT out |
| BEN | Verbruggen | BHA | 4.6 | a | price rose |
| BEN | Truffert | BOU | 5.4 | a | |
| BEN | Shaw | MUN | 4.3 | d 75% | doubtful |
| BEN | Obi | MUN | 4.5 | u 0% | loan — dead slot |

## Recommended owned actions (advisory only)

### Into GW7

- **8522487:** set **Haaland (C) / Bruno (VC)**; prefer **TC** on Haaland for IPS (H); FT Groß from DH/E.Le Fée **or roll**; reject Schade; hold Thiago vs LIV; wait for PSG minutes before any City-mid panic.
- **7337262:** **Isak → active FWD** first (ledger `model:6afa25fe…`); hold Semenyo; treat Obi + Shaw doubt as WC pressure only if a third hole appears; captain Palmer or Semenyo unless pivoting to Haaland this week.
