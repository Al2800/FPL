# Live-entry decision input — 2026-10-24

- observed_at: 2026-10-24T07:05:00Z
- next_deadline: 2026-10-31T11:00:00Z (GW9); GW8 deadline already locked 2026-10-23T17:30:00Z
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-24.md` (reconstructed 15 is **not** either owned squad)
- GW8 status: **in progress** (IPS–NFO live 1–1; AVL–MCI 11:30Z); GW7 complete

## Executive decision

**Haaland arm (8522487):** Total **408** / OR ~5.24m / GW8 picks locked with **Haaland (C) / João Pedro (VC)**, **0 transfers**, **no chip**. Bootstrap Haaland **`a`/100%** / ep_this **6.3** / own **77.5%**. Keep armband through Villa; into GW9 prefer **Haaland (C)** vs BHA (H) and **roll FT**. Do **not** TC GW8 or GW9 (save for Fulham GW11 framing). Ignore Anfield/City-trap Brighton buys; ignore Saka/Szoboszlai/Porro/DCL chase.

**No-Haaland arm (7337262):** Total **411** / OR ~5.08m. GW8: **3 transfers / cost 0** (chips history empty on public API — treat as WC-equivalent free rebuild) — Semenyo→Tavernier, Shaw→Davis, Obi→Evanilson. Locked XI: **João Pedro (C) / Palmer (VC)** with Rogers / Rice / Tavernier / Isak / Evanilson. Holes from yesterday are patched. Into GW9: **hold chips**; prefer **Palmer or João Pedro (C)** (no Haaland); FT only if a new hole appears — do not chase Haaland mid-price without a planned WC later.

## Official entry state

GW8 in progress. Morning sample:

| entry | arm | GW7 pts | GW8 pts (so far) | total | current OR |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 52 | 0 | 408 | ~5.24m |
| 7337262 | no Haaland | 54 | 0 | 411 | ~5.08m |

| entry | bank | GW8 transfers | GW8 transfer cost | team value |
|---|---:|---:|---:|---:|
| 8522487 | £0.2m | 0 | 0 | 99.3 |
| 7337262 | £0.8m | 3 | 0 | 99.9 |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded. Chip history array empty for both entries.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW8 picks, locked)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.6 | a | XI — Anfield week |
| DEF | Van Hecke | TOT | 4.9 | a/100 | XI |
| DEF | Mitchell | CRY | 4.5 | a | XI |
| DEF | van Ewijk | COV | 3.9 | a/100 | XI |
| MID | B.Fernandes | MUN | 11.7 | a | XI |
| MID | Xhaka | SUN | 5.4 | a | XI |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI |
| FWD | João Pedro | CHE | 7.9 | a/100 | **(VC)** |
| FWD | Thiago | BRE | 7.8 | a | XI |
| FWD | Haaland | MCI | 15.7 | a/100 | **(C)** GW8; ep_this 6.3 |
| GK | Dubravka | TOT | 4.0 | a | bench |
| MID | Gibbs-White | NFO | 7.9 | a/100 | bench |
| DEF | Castagne | FUL | 4.5 | a | bench |
| DEF | Diop | IPS | 3.9 | a | bench |

### 7337262 — no-Haaland arm (GW8 picks after 3 free transfers)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.2 | a | XI |
| DEF | Gabriel | ARS | 7.9 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | XI |
| DEF | Guéhi | MCI | 6.0 | a | XI |
| MID | Rogers | CHE | 8.0 | a | XI |
| MID | Palmer | CHE | 9.8 | a/100 | **(VC)** |
| MID | Tavernier | BOU | 6.3 | a | in for Semenyo |
| MID | Rice | ARS | 7.3 | a/100 | XI |
| FWD | Evanilson | BOU | 6.2 | a | in for Obi |
| FWD | João Pedro | CHE | 7.9 | a/100 | **(C)** |
| FWD | Isak | LIV | 9.0 | a/100 | XI |
| GK | Verbruggen | BHA | 4.6 | a | bench |
| DEF | Truffert | BOU | 5.4 | a | bench |
| MID | Anderson | MCI | 6.3 | a/100 | bench |
| DEF | Davis | IPS | 4.0 | a | in for Shaw |

## GW8 / GW9 recommendations by entry

| entry | chip | FT priority | captain / vice | notes |
|---|---|---|---|---|
| 8522487 | hold | **roll** into GW9 | Haaland / João Pedro (locked GW8; same GW9 lean) | No TC @ Villa or vs BHA; ignore Brighton DEF/MID trap |
| 7337262 | hold (GW8 patch already done) | roll unless new hole | João Pedro / Palmer (locked); GW9 Palmer or JP | Semenyo/Shaw/Obi holes closed; no Haaland TC path |

## Falsifiers

- Haaland withdrawn/blank at Villa → 8522487 leans harder on JP returns; GW9 armband reassess
- Cherki unused → funding mid path toward Tavernier/Rogers accelerates on advisory 15
- Davis/Truffert blanks + new DEF flag on 7337262 → reopen DEF FT
- Owner wants Haaland onto 7337262 → requires planned hit/WC later, not mid-GW8

## Host handoff

- Companion only; does not set `ready_for_manual_entry`
- Account writes: false
- Owner approval still required before any FPL entry
