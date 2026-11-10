# Live-entry decision input — 2026-10-27

- observed_at: 2026-10-27T07:05:00Z
- next_deadline: 2026-10-31T11:00:00Z (GW9); GW8 deadline already locked 2026-10-23T17:30:00Z
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-27.md` (reconstructed 15 is **not** either owned squad)
- GW8 status: event `finished` + `data_checked` true on bootstrap; use entry history / element points for finals

## Executive decision

**Haaland arm (8522487):** GW8 **50** (Haaland C; João Pedro VC blanked / autosub path). Total **458** / OR ~4.92m. **0 transfers**, **no chip**. Into GW9: **Haaland (C)** vs BHA (H), move VC off João Pedro to Cherki-class if owned else Thiago/Palmer-class, and treat **João Pedro → Evanilson** as the primary FT unless midweek Chelsea clears him. Do **not** TC GW9.

**No-Haaland arm (7337262):** GW8 **68** (João Pedro C blank; Tavernier / Isak / Evanilson / Gabriel haul path). Total **479** / OR ~3.58m. GW8: **3 transfers / cost 0**. Into GW9: **hold chips**; move captain off João Pedro (Palmer / Tavernier / Evanilson / Rogers schools); FT to patch João Pedro if not cleared — do not chase Haaland mid-price without a planned WC later.

## Official entry state

| entry | arm | GW8 pts | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 50 | 458 | ~4.92m |
| 7337262 | no Haaland | 68 | 479 | ~3.58m |

| entry | GW8 transfers | GW8 transfer cost | active chip |
|---|---:|---:|---|
| 8522487 | 0 | 0 | none |
| 7337262 | 3 | 0 | none |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded. Morning entry fetch was intermittently 403; figures above are from the same-morning successful bootstrap-adjacent pulls.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW8 picks after autosubs)

| role | player | club | price | status | GW8 pts | note |
|---|---|---|---:|---|---:|---|
| GK | Verbruggen | BHA | 4.6 | a | 2 | XI |
| DEF | Van Hecke | TOT | 4.9 | a | 7 | XI |
| DEF | Mitchell | CRY | 4.5 | a | 1 | XI |
| DEF | van Ewijk | COV | 3.9 | a | 2 | XI |
| DEF | Castagne | FUL | 4.5 | a | 7 | autosub into XI |
| MID | Gibbs-White | NFO | 7.9 | a | 2 | autosub into XI |
| MID | Xhaka | SUN | 5.4 | a | 3 | XI |
| MID | E.Le Fée | SUN | 5.7 | a | 3 | XI |
| MID | Dewsbury-Hall | EVE | 6.6 | a | 2 | XI |
| FWD | Thiago | BRE | 7.8 | a | 5 | XI |
| FWD | Haaland | MCI | 15.7 | a | 8 | **C** (×2) |
| BEN | Dubravka | TOT | 4.0 | a | 0 | |
| BEN | B.Fernandes | MUN | 11.7 | a | 0 | blanked / benched path |
| BEN | João Pedro | CHE | 7.9 | d | 0 | **VC** — omitted / fluid |
| BEN | Diop | IPS | 3.9 | a | 1 | |

### 7337262 — no-Haaland arm (GW8 picks)

| role | player | club | price | status | GW8 pts | note |
|---|---|---|---:|---|---:|---|
| GK | Raya | ARS | 6.2 | a | 7 | XI |
| DEF | Gabriel | ARS | 7.9 | a | 17 | XI |
| DEF | Guéhi | CRY | 6.0 | a | 0 | XI |
| DEF | Castagne | FUL | 4.5 | a | 7 | XI |
| DEF | Truffert | BOU | 5.4 | a | 10 | XI |
| MID | Palmer | CHE | 9.8 | a | -1 | **VC** |
| MID | Tavernier | BOU | 6.4 | a | 10 | XI |
| MID | Rice | ARS | 7.4 | a | 3 | XI |
| MID | Rogers | CHE | 8.0 | a | 1 | XI |
| FWD | Isak | LIV | 9.0 | a | 9 | XI |
| FWD | Evanilson | BOU | 6.2 | a | 6 | XI |
| BEN | Verbruggen | BHA | 4.6 | a | 2 | |
| BEN | João Pedro | CHE | 7.9 | d | 0 | **C** — omitted / fluid (×2 miss) |
| BEN | Anderson | NFO | 6.3 | a | 1 | |
| BEN | Davis | IPS | 4.0 | a | 2 | |

## GW9 guidance (entries)

- **8522487:** Haaland (C); move VC off João Pedro; FT **João Pedro → Evanilson** (or keep only if midweek clear). Hold chips.
- **7337262:** Move captain off João Pedro; prefer Palmer / Tavernier / Evanilson / Rogers schools; patch João Pedro if still doubtful; hold chips; do not force Haaland without WC plan.
- Both: ignore Saka (`model:b3c8a65a…`) / Szoboszlai / Semenyo / DCL / Wirtz / Maddison chase; reject TC Haaland vs Brighton; Barcola/Isak started_match tips are not automatic buys for the Haaland arm; Mykolenko recovery (`model:0475b895…`) is watchlist-only.

## Host handoff

- Account writes: false
- Owner approval still required before any FPL entry
- Companion advisory hashes: model-run `ca756be3…`; ledger tip `3c0820e9…`
