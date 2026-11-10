# Live-entry decision input — 2026-10-23

- observed_at: 2026-10-23T07:05:00Z
- next_deadline: 2026-10-23T17:30:00Z (GW8)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-23.md` (reconstructed 15 is **not** either owned squad)
- GW7 status: **complete**; scores below are morning samples from entry history / bootstrap

## Executive decision

**Haaland arm (8522487):** Total **408** / OR ~5.20m / GW7 **52** with **Haaland (C) / João Pedro (VC)** and **no chip**. Bootstrap still shows Haaland **`a`/100%** / ep_next **9.5**; Thursday City presser quotes Maresca “100% available” (host again rejected ledger supersede). Prefer **Haaland (C) / João Pedro (VC)** for GW8; **do not TC** @ Villa. Free transfer: **roll** — no Semenyo/Shaw hole on this entry; do **not** force Groß/De Cuyper into LIV (A). Gibbs-White bootstrap **`a`/100%** but ep_next **1.0** vs Dewsbury-Hall **7.5** — keep DH in XI, GW on bench unless owner prefers Forest minutes narrative.

**No-Haaland arm (7337262):** Total **411** / OR ~5.01m / GW7 **54** with **Palmer (C) / Rogers (VC)**. **Three simultaneous holes:** Semenyo **`i`/0%** (~8 weeks), Shaw **`i`/0%**, Obi **`u`/0%**. This still meets the ≥3-hole WC threshold for **this entry**. Prefer **Wildcard GW8** rebuild (Cherki/City or Chelsea mid path; repair DEF; replace Obi) over a single Semenyo→Cherki FT that leaves Shaw/Obi dead. If WC is refused, minimum is Semenyo→Cherki plus accept hit or roll-dead DEF. Prefer **Palmer or João Pedro (C)**; no TC without Haaland.

## Official entry state

GW7 finished. Morning sample:

| entry | arm | GW7 pts | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 52 | 408 | ~5.20m |
| 7337262 | no Haaland | 54 | 411 | ~5.01m |

| entry | bank | chips used GW7 | GW7 transfers | team value |
|---|---:|---|---:|---:|
| 8522487 | £0.2m | none | 0 | 99.4 |
| 7337262 | £0.0m | none | 0 | 99.6 |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW7 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.6 | a | XI — Anfield week temptation remains |
| DEF | Van Hecke | TOT | 4.9 | a/100 | XI |
| DEF | Mitchell | CRY | 4.5 | a | XI |
| DEF | van Ewijk | COV | 3.9 | a/100 | XI |
| MID | B.Fernandes | MUN | 11.8 | a | XI |
| MID | Xhaka | SUN | 5.4 | a | XI |
| MID | E.Le Fée | SUN | 5.7 | a | XI |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI — ep_next 7.5 |
| FWD | João Pedro | CHE | 7.9 | a/100 | prefer VC again |
| FWD | Thiago | BRE | 7.8 | a | XI |
| FWD | Haaland | MCI | 15.7 | a/100 | prefer (C) GW8; ep 9.5; Maresca 100% available |
| GK | Dubravka | TOT | 4.0 | a | bench |
| MID | Gibbs-White | NFO | 7.9 | a/100 | bench |
| DEF | Castagne | FUL | 4.5 | a | bench |
| DEF | Diop | IPS | 3.9 | a | bench |

### 7337262 — no-Haaland arm (GW7 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.1 | a | XI |
| DEF | Gabriel | ARS | 7.9 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | XI |
| DEF | Guéhi | MCI | 6.0 | a | XI |
| MID | Rogers | CHE | 8.0 | a | VC candidate |
| MID | Palmer | CHE | 9.8 | a/100 | (C) candidate |
| MID | Semenyo | MCI | 8.3 | i/0 | **hard out ~8 weeks** |
| MID | Rice | ARS | 7.3 | a/100 | XI |
| MID | Anderson | MCI | 6.3 | a/100 | XI |
| FWD | João Pedro | CHE | 7.9 | a/100 | XI |
| FWD | Isak | LIV | 9.0 | a/100 | XI hold |
| GK | Verbruggen | BHA | 4.6 | a | bench |
| DEF | Truffert | BOU | 5.4 | a | bench |
| DEF | Shaw | MUN | 4.3 | i/0 | **dead DEF** |
| FWD | Obi | MUN | 4.5 | u/0 | **unavailable / loan flag** |

## GW8 recommendations by entry

| entry | chip | FT priority | captain / vice | notes |
|---|---|---|---|---|
| 8522487 | hold | **roll** | Haaland / João Pedro | No TC @ Villa; ignore Anfield Brighton chase; Maresca clear vs host ledger conflict |
| 7337262 | **WC preferred** | else Semenyo→Cherki (+ accept Shaw/Obi drag) | Palmer or João Pedro / Rogers | Three holes; WC clears Semenyo+Shaw+Obi |

## Falsifiers

- Late City update re-flags or rules out Haaland → 8522487 flips to João Pedro (C)
- Cherki unused after AEK start / Villa presser praise → no-Haaland WC mid path pivots to Chelsea/elsewhere
- Obi/`u` or Shaw clear unexpectedly → 7337262 WC urgency falls to Semenyo-only FT
- Owner declines WC on 7337262 → document hits and dead assets explicitly

## Host handoff

- Companion only; does not set `ready_for_manual_entry`
- Account writes: false
- Owner approval still required before any FPL entry
