# Live-entry decision input — 2026-10-12

- observed_at: 2026-10-12T07:01:57Z
- next_deadline: 2026-10-17T10:00:00Z (GW7) — GW6 scoring still open (COV–NEW Mon 19:00Z)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-12.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** GW6 deadline locked with **Haaland (C) / Bruno (VC)** — Haaland delivered a goal at Anfield (6); leave locked for remaining Mon fixture. **No chip**. Into GW7: prefer **Haaland (C)** vs IPS (H); hold FT until after COV–NEW, then consider **1 FT** toward Groß (fund from Dewsbury-Hall or E.Le Fée) only if a mid blank pressure remains; **reject Schade** (`model:e63a6717…`); Semenyo is now cleared (`model:4068dbc3…`) but this squad already has City via Haaland — do not force a second City mid without structure need. TC watch Haaland home.

**No-Haaland arm (7337262):** Isak remains **unavailable** (prior tip + bootstrap `i`) — blank already banked; **João Pedro** cover worked (12). Palmer (C) / Rogers (VC) locked. **Semenyo cleared** — started Anfield (`model:4068dbc3…`) + bootstrap **`a`/100%** / 3 pts — hold. Obi remains **loan unavailable** (`u`) — dead bench slot. Into GW7: **priority FT Isak → active FWD** (not Schade); Obi repair is FT2 or WC pressure; Semenyo clearance **reduces** the need to WC solely on mid flags.

## Official entry state

GW6 is current (`is_current`); Sat/Sun fixtures started/scored; only COV–NEW remains. Sampled this morning:

| entry | arm | GW6 pts (live) | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 62 | 354 | ~4.56m |
| 7337262 | no Haaland | 64 | 355 | ~4.50m |

| entry | bank (event hist) | chips used | GW6 transfers |
|---|---:|---|---:|
| 8522487 | £0.2m | none | 0 |
| 7337262 | £0.0m | none | 0 |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW6 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.5 | a | XI — GW6 9 pts |
| DEF | Van Hecke | TOT | 4.9 | a 100% | XI |
| DEF | Mitchell | CRY | 4.5 | a | XI — Forest done (4) |
| DEF | Castagne | FUL | 4.5 | a | XI |
| MID | B.Fernandes | MUN | 11.9 | a | **VC** |
| MID | Gibbs-White | NFO | 8.0 | a 100% | XI — Palace done (2) |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI — Hull done (13) |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI — 12 pts |
| FWD | Thiago | BRE | 7.8 | a | XI |
| FWD | Haaland | MCI | 15.6 | a | **(C)** — Anfield start+goal (6); tip `model:8d8cf41f…` |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | Xhaka | SUN | 5.4 | a | |
| BEN | Diop | IPS | 4.0 | a | |
| BEN | van Ewijk | COV | 4.0 | d 75% | hamstring |

### 7337262 — no-Haaland arm (GW6 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.1 | a | XI |
| DEF | Gabriel | ARS | 7.9 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | XI |
| DEF | Guéhi | MCI | 6.0 | a | XI — Anfield done (6) |
| MID | Rogers | CHE | 7.9 | a | **VC** — 9 pts |
| MID | Palmer | CHE | 9.7 | a 100% | **(C)** |
| MID | Semenyo | MCI | 8.3 | a 100% | **cleared** — started Anfield (3); tip `model:4068dbc3…` |
| MID | Rice | ARS | 7.3 | a 100% | XI |
| MID | Anderson | MCI | 6.3 | a 100% | XI — Anfield done (6) |
| FWD | João Pedro | CHE | 7.8 | a 100% | XI/autosub — 12 pts |
| FWD | Isak | LIV | 9.0 | i 0% | **unavailable** — blank |
| BEN | Verbruggen | BHA | 4.5 | a | |
| BEN | Truffert | BOU | 5.4 | a | |
| BEN | Shaw | MUN | 4.3 | a 100% | |
| BEN | Obi | MUN | 4.5 | u 0% | loan — dead slot |

## Recommended owned actions (advisory only)

### Remaining GW6 (no transfers possible)

- **8522487:** leave locked XI/C/VC; only van Ewijk Coventry minutes left on the bench path.
- **7337262:** leave locked Palmer (C); Isak blank already priced in; Semenyo hold after clearance.

### Toward GW7 (after GW6 finalises)

- **8522487:** Haaland (C) vs IPS (H); FT shortlist Dewsbury-Hall/E.Le Fée → Groß; reject Schade; Semenyo optional only if structure needs a second City mid (usually not); TC watch Haaland home.
- **7337262:** FT1 Isak → active FWD (not Schade while `model:e63a6717…` doubtful); hold Semenyo now cleared; plan Obi repair (FT2 or WC if ≥3 holes).

## Falsifiers

- Haaland rested/limited for Ipswich
- Schade cleared + nailed before Groß FT
- Semenyo omitted next City XI after ankle return
- Isak surprise return (unlikely given tip + bootstrap `i`)
- Owner already used WC/TC overnight (public chip field still null this morning)

## Host handoff

- Account writes: false
- Owner approval still required
- Companion review: `reports/evidence-review/2026-10-12-live-entry-review.md`
