# Live-entry decision input — 2026-10-15

- observed_at: 2026-10-15T07:05:23Z
- next_deadline: 2026-10-17T10:00:00Z (GW7)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-15.md` (reconstructed 15 is **not** either owned squad)
- City–PSG: **played** Wed 14 Oct — City 2–4 PSG; Haaland scored twice; Cherki subbed 46' (`model:9ceb008e…` / `model:ac37b51c…` / `model:3149a2f9…`)

## Executive decision

**Haaland arm (8522487):** GW6 finished sample **64 pts** with **Haaland (C) / Bruno (VC)**. No chip used in GW6. Into GW7: set **Haaland (C)** and prefer **TC Haaland** vs IPS (H) — post-PSG brace clears the main rest falsifier. Free transfer: prefer **Dewsbury-Hall or E.Le Fée → Groß** (BHA–CRY H; ep_next **10.0**) if chasing the Brighton stack; else roll. **Reject Schade** (`model:e63a6717…`). This squad already has City via Haaland — do not force Semenyo without structure need. Reassess only if Friday’s City presser limits Haaland.

**No-Haaland arm (7337262):** GW6 sample **66 pts**; GW6 picks refreshed successfully this morning. Isak remains **unavailable** (`model:6afa25fe…` + bootstrap `i`/0%) on the bench — priority FT out. **Semenyo hold** (`model:3149a2f9…` PSG start; ep **10.0**). Obi remains **loan `u`** dead slot; Shaw **`d`/75%** is in the starting DEF line — two soft spots plus Isak. Into GW7: **Isak → active FWD** first; Obi repair is FT2 or WC pressure if a third hole opens. Prefer **Palmer or Semenyo (C)** over forcing a Haaland-less TC; if pivoting to Haaland this week, align chip with that move rather than WC by default.

## Official entry state

GW6 finished (`finished=True`); GW7 is next (picks endpoint 404 until deadline window opens). Morning sample:

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
| DEF | Van Hecke | TOT | 4.9 | a 100% | XI |
| DEF | Mitchell | CRY | 4.5 | a | XI |
| DEF | Diop | IPS | 4.0 | a | XI — MCI (A) tough |
| MID | B.Fernandes | MUN | 11.9 | a | **VC** — LEE (A); ep 1.5 |
| MID | Gibbs-White | NFO | 8.0 | a 100% | XI — ARS (H) |
| MID | E.Le Fée | SUN | 5.7 | a | XI — funding route for Groß |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI — ep 8.0 |
| FWD | Haaland | MCI | 15.6 | a | **(C)** / **TC** — IPS (H); PSG brace |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI — EVE (A) |
| FWD | Thiago | BRE | 7.8 | a | XI — LIV (H); ep 4.5 |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | Xhaka | SUN | 5.4 | a | |
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
| MID | Semenyo | MCI | 8.3 | a 100% | PSG start `model:3149a2f9…`; ep **10.0** |
| MID | Rice | ARS | 7.3 | a 100% | XI |
| MID | Anderson | MCI | 6.3 | a 100% | XI — IPS (H) |
| MID | Rogers | CHE | 7.9 | a | **VC** — EVE (A); ep 5.5 |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI |
| BEN | Verbruggen | BHA | 4.6 | a | |
| BEN | Castagne | FUL | 4.5 | a | |
| BEN | Isak | LIV | 9.0 | i 0% | **unavailable** `model:6afa25fe…` — priority FT out |
| BEN | Obi | MUN | 4.5 | u 0% | loan — dead slot |

## Recommended owned actions (advisory only)

### Into GW7

- **8522487:** set **Haaland (C) / Bruno (VC)**; prefer **TC** on Haaland for IPS (H); FT Groß from DH/E.Le Fée **or roll**; reject Schade; hold Thiago vs LIV; do not panic-sell on Cherki noise (Cherki not owned here).
- **7337262:** **Isak → active FWD** first (ledger `model:6afa25fe…`); hold Semenyo (PSG start + ep 10.0); treat Obi + Shaw doubt as WC pressure if a third hole appears; captain Palmer or Semenyo unless pivoting to Haaland this week.
