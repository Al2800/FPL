# Live-entry decision input — 2026-10-31

- observed_at: 2026-10-31T07:01:04Z
- next_deadline: 2026-10-31T11:00:00Z (GW9 — **today**); GW8 deadline already locked 2026-10-23T17:30:00Z
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-31.md` (reconstructed 15 is **not** either owned squad)
- GW8 status: event `finished` + `data_checked` true on bootstrap; GW9 picks endpoints still **404** this morning (pre-deadline window)

## Executive decision

**Haaland arm (8522487):** GW8 **50** (Haaland C; João Pedro VC blanked / autosub path). Total **458** / OR ~4.92m. **0 transfers in GW8**, **no chip**. Into GW9 (**deadline today**): **Haaland (C)** vs BHA (H), move VC off João Pedro to Cherki if owned else Thiago/Palmer-class starter, and **lock João Pedro → Evanilson** after bootstrap `i`/0% + admitted tip `model:d1dbf69d…`. Do **not** TC GW9. City cup unused after rest remains rotation watch only — still default C for PL rematch unless unexplained absence.

**No-Haaland arm (7337262):** GW8 **68** (João Pedro C blank; Tavernier / Isak / Evanilson / Gabriel haul path). Total **479** / OR ~3.58m. GW8: **3 transfers / cost 0**. Into GW9: **hold chips**; move captain off João Pedro (Palmer / Tavernier / Evanilson / Rogers / N.Jackson schools); FT to sell João Pedro if still owned — already own Evanilson so prefer another hole (e.g. Rice `d`/75% / flagged mid-def) or roll if bank/structure allows; do not chase Haaland mid-price without a planned WC later. DCL available tip remains optional flavour, not mandatory.

## Official entry state

| entry | arm | GW8 pts | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 50 | 458 | ~4.92m |
| 7337262 | no Haaland | 68 | 479 | ~3.58m |

| entry | GW8 transfers | GW8 transfer cost | active chip |
|---|---:|---:|---|
| 8522487 | 0 | 0 | none |
| 7337262 | 3 | 0 | none |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded. GW9 picks 404 until the deadline window opens transfers UI-side.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW8 picks after autosubs)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.6 | a | XI |
| DEF | Van Hecke | TOT | 4.9 | a | XI |
| DEF | Mitchell | CRY | 4.5 | a | XI |
| DEF | van Ewijk | COV | 3.9 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | autosub into XI |
| MID | Gibbs-White | NFO | 7.9 | a | autosub into XI |
| MID | Xhaka | SUN | 5.4 | a | XI |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Dewsbury-Hall | EVE | — | a | XI |
| FWD | Thiago | BRE | — | a | XI |
| FWD | Haaland | MCI | 15.8 | a | **C** path; price £15.8m; cup unused (rest) |
| BEN | Dubravka | TOT | — | a | |
| BEN | B.Fernandes | MUN | 11.7 | a | |
| BEN | João Pedro | CHE | 7.8 | **i** | **VC path** — thigh `i`/0%; own **49.3%**; sell locked |
| BEN | Diop | IPS | 3.9 | a | |

### 7337262 — no-Haaland arm (GW8 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | — | a | XI |
| DEF | Gabriel | ARS | — | a | XI |
| DEF | Guéhi | CRY | — | a | XI |
| DEF | Castagne | FUL | — | a | XI |
| DEF | Truffert | BOU | — | a | XI |
| MID | Palmer | CHE | 9.8 | a | **VC** path |
| MID | Tavernier | BOU | 6.5 | a | XI / community heat; price now **£6.5m** |
| MID | Rice | ARS | — | d | XI; bootstrap `d`/75%; Arteta targeting return if Saturday session OK |
| MID | Rogers | CHE | — | a | XI |
| FWD | Isak | LIV | 9.1 | a | XI |
| FWD | Evanilson | BOU | 6.3 | a | XI — already owns preferred JP replacement |
| BEN | Verbruggen | BHA | 4.6 | a | |
| BEN | João Pedro | CHE | 7.8 | **i** | **C path blank** — thigh `i`/0% |
| BEN | Anderson | NFO | — | a | |
| BEN | Davis | IPS | — | a | |

## GW9 guidance (entries)

- **8522487:** Haaland (C); move VC off João Pedro; FT **João Pedro → Evanilson** locked. Hold chips.
- **7337262:** Move captain off João Pedro; prefer Palmer / Tavernier / Evanilson / Rogers / N.Jackson schools; João Pedro already dead minutes — use FT on another hole (Rice flag watch) or roll; hold chips; do not force Haaland without WC plan.
- Both: ignore Saka (`model:e67b74ec…`) / Szoboszlai (`model:a4e10b92…`) / Munoz (`model:1f9febf6…`) / Semenyo / forced DCL / Wirtz (prior `model:bcd6b364…`) / Maddison (host-rejected available) / Minteh / Wieffer / Sarr chase; reject TC Haaland vs Brighton; Branthwaite Moyes expected-available quote is briefing-only (host rejected supersede).

## Host handoff

- Advisory XV handoff: `reports/strategy-research/2026-10-31.md`
- Model evidence tip: `b3599405…` (from `7c7b72c7…`)
- Account writes: false
- Owner approval still required
