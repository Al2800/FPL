# Live-entry decision input — 2026-10-13

- observed_at: 2026-10-13T07:03:16Z
- next_deadline: 2026-10-17T10:00:00Z (GW7)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-13.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** GW6 finished sample **62 pts** with **Haaland (C) / Bruno (VC)**. **No chip** remaining for GW6. Into GW7: prefer **Haaland (C)** and strongly consider **TC Haaland** vs IPS (H). Free transfer: prefer **Dewsbury-Hall or E.Le Fée → Groß** (BHA–CRY H; ep_next **12.3**) if chasing the Brighton stack; else roll. **Reject Schade** (`model:e63a6717…`). van Ewijk now bootstrap **`a`/100%** / £3.9m — bench depth improved. Semenyo cleared but this squad already has City via Haaland — do not force a second City mid without structure need.

**No-Haaland arm (7337262):** GW6 sample **64 pts** with **Palmer (C) / Rogers (VC)**. Isak remains **unavailable** (prior tip + bootstrap `i`/0%) — blank already banked; João Pedro cover worked. **Semenyo hold** after clearance (`model:4068dbc3…`). Obi remains **loan `u`** dead slot; Shaw now bootstrap **`d`/75%**. Into GW7: **priority FT Isak → active FWD** (João Pedro already owned — look for a third FWD / or fund via Isak sell into Haaland if pivoting premiums); Obi repair is FT2 or WC pressure if a second hole opens. Prefer **Palmer or Semenyo (C)** over forcing a Haaland-less TC; if pivoting to Haaland this week, align chip with that move rather than WC by default.

## Official entry state

GW6 is current (`is_current`); Monday COV–NEW complete. Sampled this morning:

| entry | arm | GW6 pts (sample) | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 62 | 354 | ~4.62m |
| 7337262 | no Haaland | 64 | 355 | ~4.57m |

| entry | bank (event hist) | chips used | GW6 transfers |
|---|---:|---|---:|
| 8522487 | £0.2m | none | 0 |
| 7337262 | £0.0m | none | 0 |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW6 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.5 | a | XI — ep_next 7.7 into CRY (H) |
| DEF | Van Hecke | TOT | 4.9 | a 100% | XI — tip retained |
| DEF | Mitchell | CRY | 4.5 | a | XI — started Forest `model:182761e0…` |
| DEF | Castagne | FUL | 4.5 | a | XI — ep 0.5 |
| MID | B.Fernandes | MUN | 11.9 | a | **VC** — LEE (A) |
| MID | Gibbs-White | NFO | 8.0 | a 100% | XI — ARS (H) |
| MID | E.Le Fée | SUN | 5.7 | a | XI — funding route for Groß |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI — ep 8.0; CHE (H) tough |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI — ep 6.0; EVE (A) |
| FWD | Thiago | BRE | 7.8 | a | XI — LIV (H) |
| FWD | Haaland | MCI | 15.6 | a | **(C)** / **TC watch** — IPS (H); tip `model:8d8cf41f…` |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | Xhaka | SUN | 5.4 | a | |
| BEN | Diop | IPS | 4.0 | a | |
| BEN | van Ewijk | COV | 3.9 | a 100% | **cleared** vs yesterday `d` |

### 7337262 — no-Haaland arm (GW6 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.1 | a | XI — NFO (A) |
| DEF | Gabriel | ARS | 7.9 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | XI |
| DEF | Guéhi | MCI | 6.0 | a | XI — IPS (H); ep 5.3 |
| MID | Rogers | CHE | 7.9 | a | **VC** |
| MID | Palmer | CHE | 9.7 | a 100% | **(C)** — EVE (A) |
| MID | Semenyo | MCI | 8.3 | a 100% | **cleared** — IPS (H); tip `model:4068dbc3…` |
| MID | Rice | ARS | 7.3 | a 100% | XI |
| MID | Anderson | MCI | 6.3 | a 100% | XI — IPS (H) |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI |
| FWD | Isak | LIV | 9.0 | i 0% | **unavailable** — priority FT out |
| BEN | Verbruggen | BHA | 4.5 | a | |
| BEN | Truffert | BOU | 5.4 | a | ep 0.5 |
| BEN | Shaw | MUN | 4.3 | d 75% | newly doubtful this morning |
| BEN | Obi | MUN | 4.5 | u 0% | loan — dead slot |

## Recommended owned actions (advisory only)

### Into GW7

- **8522487:** set **Haaland (C) / Bruno (VC)**; prefer **TC** on Haaland for IPS (H); FT Groß from DH/E.Le Fée **or roll**; reject Schade; hold Thiago vs LIV.
- **7337262:** **Isak → active FWD** first; hold Semenyo; treat Obi + Shaw doubt as WC pressure only if a third hole appears; captain Palmer or Semenyo unless pivoting to Haaland this week.

## Falsifiers

- Haaland rested vs Ipswich after PSG.
- Isak declared fit midweek and starts vs Brentford.
- Semenyo omitted while Cherki/Haaland haul.
- Schade cleared with high minutes — still prefer other routes for 8522487.
- Second dead slot opens on 7337262 → WC becomes rational.
