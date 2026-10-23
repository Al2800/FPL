# Live-entry decision input — 2026-10-21

- observed_at: 2026-10-21T07:05:00Z
- next_deadline: 2026-10-23T17:30:00Z (GW8)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-21.md` (reconstructed 15 is **not** either owned squad)
- GW7 status: **complete** (TOT 3–1 COV finished Mon); scores below are post-GW7 samples from entry history

## Executive decision

**Haaland arm (8522487):** GW7 **52 pts** with **Haaland (C) / João Pedro (VC)** and **no chip**. Bootstrap now shows Haaland **`a`/100%** / ep_next **9.5** (was `d`/75% yesterday). Prefer **Haaland (C) / João Pedro (VC)** again for GW8; **do not TC** @ Villa. Free transfer: **roll by default** — squad has no Semenyo hole; do **not** force Groß/De Cuyper into LIV (A). Gibbs-White remains bench/`d`/75%. Host still holds an unexpired Haaland **doubtful** tip (available supersede rejected) — Friday City presser is the hard falsifier.

**No-Haaland arm (7337262):** GW7 **54 pts** with **Palmer (C) / Rogers (VC)**. **Three simultaneous holes:** Semenyo **`i`/0%** (~8 weeks, tip refresh `model:3660820452…`), Shaw **`i`/0%**, Obi **`u`/0%**. This meets the ≥3-hole WC threshold for **this entry**. Prefer **Wildcard GW8** rebuild (Cherki/City or Chelsea mid path; repair DEF; replace Obi) over a single Semenyo→Cherki FT that leaves Shaw/Obi dead. If WC is refused, minimum is Semenyo→Cherki plus accept hit or roll-dead DEF. Prefer **Palmer or João Pedro (C)**; no TC without Haaland.

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
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI |
| FWD | João Pedro | CHE | 7.9 | a/100 | VC GW7; prefer VC again |
| FWD | Thiago | BRE | 7.8 | a | XI |
| FWD | Haaland | MCI | 15.7 | a/100 | (C) GW7; prefer (C) GW8; ep 9.5 |
| GK | Dubravka | TOT | 4.0 | a | bench |
| MID | Gibbs-White | NFO | 7.9 | d/75 | bench |
| DEF | Castagne | FUL | 4.5 | a | bench |
| DEF | Diop | IPS | 3.9 | a | bench |

### 7337262 — no-Haaland arm (GW7 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.1 | a | XI |
| DEF | Gabriel | ARS | 7.9 | a | XI |
| DEF | Castagne | FUL | 4.5 | a | XI |
| DEF | Guéhi | MCI | 6.0 | a | XI |
| MID | Rogers | CHE | 8.0 | a | VC GW7 |
| MID | Palmer | CHE | 9.7 | a/100 | (C) GW7 |
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
| 8522487 | hold | roll (or trivial bench polish only) | Haaland / João Pedro | No TC @ Villa; ignore Anfield Brighton chase |
| 7337262 | **WC preferred** | else Semenyo→Cherki (+ accept Shaw/Obi drag) | Palmer or João Pedro / Rogers | Three holes; WC clears Semenyo+Shaw+Obi |

## Falsifiers

- Friday City presser re-flags or rules out Haaland → 8522487 flips to João Pedro (C)
- Cherki unused again after AEK start → no-Haaland WC mid path pivots to Chelsea/elsewhere
- Obi/`u` or Shaw clear unexpectedly → 7337262 WC urgency falls to Semenyo-only FT
- Owner declines WC on 7337262 → document hits and dead assets explicitly

## Host handoff

- Companion only; does not set `ready_for_manual_entry`
- Account writes: false
- Owner approval still required before any FPL entry
