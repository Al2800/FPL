# Live-entry decision input — 2026-10-26

- observed_at: 2026-10-26T07:15:00Z
- next_deadline: 2026-10-31T11:00:00Z (GW9); GW8 deadline already locked 2026-10-23T17:30:00Z
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-26.md` (reconstructed 15 is **not** either owned squad)
- GW8 status: Sunday slate scored locally (CRY 0-2 NEW; HUL 1-1 BRE; LIV 2-0 BHA; MUN 0-3 BOU; SUN 0-0 LEE); FPL event `data_checked` still false — use element `event_points` × multipliers for provisional totals

## Executive decision

**Haaland arm (8522487):** Provisional GW8 ~**41** (Haaland C **16** raw **8**; João Pedro VC **0** omitted). Total ~**449** / OR ~5.18m. **0 transfers**, **no chip**. Into GW9: **Haaland (C)** vs BHA (H), move VC off João Pedro to Cherki-class if owned else Thiago/Palmer-class, and treat **João Pedro → Evanilson** as the primary FT unless midweek Chelsea clears him. Do **not** TC GW9.

**No-Haaland arm (7337262):** Provisional GW8 ~**59** (João Pedro C blank **0**; Tavernier **10**; Isak **9**; Evanilson **6**; Gabriel **17**). Total ~**470** / OR ~3.86m. GW8: **3 transfers / cost 0**. Into GW9: **hold chips**; move captain off João Pedro (Palmer / Tavernier / Evanilson / Rogers schools); FT to patch João Pedro if not cleared — do not chase Haaland mid-price without a planned WC later.

## Official entry state

| entry | arm | GW8 pts (provisional) | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | ~41 | ~449 | ~5.18m |
| 7337262 | no Haaland | ~59 | ~470 | ~3.86m |

| entry | GW8 transfers | GW8 transfer cost | active chip |
|---|---:|---:|---|
| 8522487 | 0 | 0 | none |
| 7337262 | 3 | 0 | none |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW8 picks, locked)

| role | player | club | price | status | GW8 pts | note |
|---|---|---|---:|---|---:|---|
| GK | Verbruggen | BHA | 4.6 | a | 2 | XI — LIV (A) done |
| DEF | Van Hecke | TOT | 4.9 | a | 7 | XI — CHE (A) done |
| DEF | Mitchell | CRY | 4.5 | a | 1 | XI — NEW (H) done |
| DEF | van Ewijk | COV | 3.9 | a | 2 | XI — FUL done |
| MID | B.Fernandes | MUN | 11.7 | a | 0 | XI — BOU (H) blank |
| MID | Xhaka | SUN | 5.4 | a | 3 | XI — LEE (H) done |
| MID | E.Le Fée | SUN | 5.7 | a | 3 | XI — LEE (H) done |
| MID | Dewsbury-Hall | EVE | 6.6 | a | 2 | XI — ARS done |
| FWD | João Pedro | CHE | 7.9 | d | 0 | **VC** — omitted / fluid |
| FWD | Thiago | BRE | 7.8 | a | 5 | XI — HUL (A) done |
| FWD | Haaland | MCI | 15.7 | a | 8 | **C** — AVL done (×2) |
| BEN | Dubravka | TOT | 4.0 | a | 0 | |
| BEN | Gibbs-White | NFO | 7.9 | a | 2 | |
| BEN | Castagne | FUL | 4.5 | a | 7 | |
| BEN | Diop | IPS | 3.9 | a | 1 | |

### 7337262 — no-Haaland arm (GW8 picks, locked)

| role | player | club | price | status | GW8 pts | note |
|---|---|---|---:|---|---:|---|
| GK | Raya | ARS | 6.2 | a | 7 | XI — EVE done |
| DEF | Gabriel | ARS | 7.9 | a | 17 | XI — EVE done |
| DEF | Castagne | FUL | 4.5 | a | 7 | XI — COV done |
| DEF | Guéhi | CRY | 6.0 | a | 0 | XI — NEW (H) blank |
| MID | Rogers | CHE | 8.0 | a | 1 | XI — TOT done |
| MID | Palmer | CHE | 9.8 | a | -1 | **VC** — TOT done |
| MID | Tavernier | BOU | 6.3 | a | 10 | XI — MUN (A) haul |
| MID | Rice | ARS | 7.4 | a | 3 | XI — EVE done |
| FWD | Evanilson | BOU | 6.2 | a | 6 | XI — MUN (A) done |
| FWD | João Pedro | CHE | 7.9 | d | 0 | **C** — omitted / fluid (×2 miss) |
| FWD | Isak | LIV | 9.0 | a | 9 | XI — BHA (H) done |
| BEN | Verbruggen | BHA | 4.6 | a | 2 | |
| BEN | Truffert | BOU | 5.4 | a | 10 | |
| BEN | Anderson | NFO | 6.3 | a | 1 | |
| BEN | Davis | IPS | 4.0 | a | 2 | |

## GW9 guidance (entries)

- **8522487:** Haaland (C); move VC off João Pedro; FT **João Pedro → Evanilson** (or keep only if midweek clear). Hold chips.
- **7337262:** Move captain off João Pedro; prefer Palmer / Tavernier / Evanilson / Rogers schools; patch João Pedro if still doubtful; hold chips; do not force Haaland without WC plan.
- Both: ignore Saka / Szoboszlai / Semenyo / DCL / Wirtz / Maddison chase; reject TC Haaland vs Brighton; Barcola/Isak started_match tips are not automatic buys for the Haaland arm.

## Host handoff

- Account writes: false
- Owner approval still required before any FPL entry
- Companion advisory hashes: model-run `20570288…`; ledger tip `6ff5bf99…`
