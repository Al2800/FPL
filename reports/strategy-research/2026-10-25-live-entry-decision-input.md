# Live-entry decision input — 2026-10-25

- observed_at: 2026-10-25T07:05:00Z
- next_deadline: 2026-10-31T11:00:00Z (GW9); GW8 deadline already locked 2026-10-23T17:30:00Z
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-25.md` (reconstructed 15 is **not** either owned squad)
- GW8 status: **in progress** (Sat fixtures started/finished locally; Sun slate CRY–NEW / HUL–BRE / LIV–BHA / MUN–BOU / SUN–LEE still ahead)

## Executive decision

**Haaland arm (8522487):** Total **435** / OR ~5.23m / GW8 picks locked with **Haaland (C) / João Pedro (VC)**, **0 transfers**, **no chip**. Haaland already **8** raw (16 with C) at Villa; João Pedro **0** and **omitted** (Alonso fluid/tests; bootstrap `d`/75% next). Into GW9: prefer **Haaland (C)** vs BHA (H), move VC off João Pedro (Cherki/Palmer-class), and treat **João Pedro → Evanilson** (or similar FWD) as the primary FT unless midweek Chelsea clears him. Do **not** TC GW9.

**No-Haaland arm (7337262):** Total **445** / OR ~4.64m. GW8: **3 transfers / cost 0** earlier in the week; locked **João Pedro (C) / Palmer (VC)** — João Pedro blank is a direct hit. Gabriel **17** / Raya **7** / Castagne **7** cushioned the scoreline so far. Into GW9: **hold chips**; move captain off João Pedro (Palmer / Rogers / Tavernier / Evanilson schools); FT to patch João Pedro if not cleared — do not chase Haaland mid-price without a planned WC later.

## Official entry state

GW8 in progress. Morning sample:

| entry | arm | GW8 pts (so far) | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 27 | 435 | ~5.23m |
| 7337262 | no Haaland | 33 | 445 | ~4.64m |

| entry | GW8 transfers | GW8 transfer cost | active chip |
|---|---:|---:|---|
| 8522487 | 0 | 0 | none |
| 7337262 | 3 | 0 | none |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded. Chip history fetch 403 this morning — treat chips as unused on public API emptiness from prior days.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW8 picks, locked)

| role | player | club | price | status | GW8 pts so far | note |
|---|---|---|---:|---|---:|---|
| GK | Verbruggen | BHA | 4.6 | a | 0 | XI — LIV (A) Sun |
| DEF | Van Hecke | TOT | 4.9 | a | 7 | XI — CHE (A) done |
| DEF | Mitchell | CRY | 4.5 | a | 0 | XI — NEW (H) Sun |
| DEF | van Ewijk | COV | 3.9 | a | 2 | XI — FUL done |
| MID | B.Fernandes | MUN | 11.7 | a | 0 | XI — BOU (H) Sun |
| MID | Xhaka | SUN | 5.4 | a | 0 | XI — LEE (H) Sun |
| MID | E.Le Fée | SUN | 5.7 | a | 0 | XI — LEE (H) Sun |
| MID | Dewsbury-Hall | EVE | 6.6 | a | 2 | XI — ARS done |
| FWD | João Pedro | CHE | 7.9 | d | 0 | **VC** — omitted / fluid |
| FWD | Thiago | BRE | 7.8 | a | 0 | XI — HUL (A) Sun |
| FWD | Haaland | MCI | 15.7 | a | 8 | **C** — AVL done |
| BEN | Dubravka | TOT | 4.0 | a | 0 | |
| BEN | Gibbs-White | NFO | 7.9 | a | 2 | IPS done |
| BEN | Castagne | FUL | 4.5 | a | 7 | COV done |
| BEN | Diop | IPS | 3.9 | a | 1 | NFO done |

### 7337262 — no-Haaland arm (GW8 picks, locked)

| role | player | club | price | status | GW8 pts so far | note |
|---|---|---|---:|---|---:|---|
| GK | Raya | ARS | 6.2 | a | 7 | XI — EVE done |
| DEF | Gabriel | ARS | 7.9 | a | 17 | XI — EVE done |
| DEF | Castagne | FUL | 4.5 | a | 7 | XI — COV done |
| DEF | Guéhi | CRY | 6.0 | a | 0 | XI — NEW (H) Sun |
| MID | Rogers | CHE | 8.0 | a | 1 | XI — TOT done |
| MID | Palmer | CHE | 9.8 | a | -1 | **VC** — TOT done |
| MID | Tavernier | BOU | 6.3 | a | 0 | XI — MUN (A) Sun |
| MID | Rice | ARS | 7.4 | a | 3 | XI — EVE done |
| FWD | Evanilson | BOU | 6.2 | a | 0 | XI — MUN (A) Sun |
| FWD | João Pedro | CHE | 7.9 | d | 0 | **C** — omitted / fluid |
| FWD | Isak | LIV | 9.0 | a | 0 | XI — BHA (H) Sun |
| BEN | Verbruggen | BHA | 4.6 | a | 0 | |
| BEN | Truffert | BOU | 5.4 | a | 0 | |
| BEN | Anderson | NFO | 6.3 | a | 1 | |
| BEN | Davis | IPS | 4.0 | a | 2 | |

## GW9 guidance (entries)

- **8522487:** Haaland (C); move VC to Cherki-class if owned else Palmer/Thiago; FT **João Pedro → Evanilson** (or keep only if midweek clear). Hold chips.
- **7337262:** Move captain off João Pedro; prefer Palmer / Rogers / Evanilson / Tavernier schools; patch João Pedro if still doubtful; hold chips; do not force Haaland without WC plan.
- Both: ignore Saka / Szoboszlai / Semenyo / DCL chase; reject TC Haaland vs Brighton.

## Host handoff

- Account writes: false
- Owner approval still required
- Advisory reconstructed 15 (with Evanilson) is separate from either owned entry
