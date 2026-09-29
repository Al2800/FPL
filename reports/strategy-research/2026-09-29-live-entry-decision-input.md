# Live-entry decision input — 2026-09-29

- observed_at: 2026-09-29T07:20:00Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for squads, completed picks, transfers and scoring; official club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is a **material market/availability update but no transfer or chip action today**. Liverpool confirmed on 28 September that Cody Gakpo withdrew from Netherlands duty with an ankle injury and will be assessed at the AXA Training Centre before the Premier League restart. Official FPL now flags Gakpo at 75% with an ankle injury. Gakpo is **not owned** by either tracked entry; the claim matters as a do-not-buy signal and as Anfield context beside the already-admitted Isak doubtful tip.

The no-Haaland squad (7337262) still carries five doubtful players — Palmer, Semenyo, Rice, João Pedro and Isak — plus Obi unavailable. If all five miss GW6, the squad has only eight currently available legal starters. That keeps a multi-transfer repair or Wildcard on the table, but the deadline remains eleven days away and none of the five is yet a confirmed GW6 absence on a club medical ruling.

The Haaland squad (8522487) remains healthier: João Pedro and van Ewijk are the only doubtful owned names on the completed GW5 sheet. Hold Pedro toward CHE–BOU; do not force a same-day FT.

Fallback captain for the no-Haaland arm remains **Rogers while Palmer is doubtful**, with Raya as vice. Isak is not a captain candidate unless Liverpool clear him for normal minutes, and even then the City fixture is less attractive than Chelsea’s home match against Bournemouth.

The automated strategy report’s Kinsky/Cherki/Wissa reconstruction remains **not** the owned 15 for these entries.

## Official entry state

GW5 is finished and data checked. The sampled overall rank-994 entry has 414 points, so 414 remains the working top-1,000 boundary.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,136 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,621 | 123 |

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

Official transfer history remains:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, B.Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

Public endpoints do not expose the current free-transfer balance, pending transfers, purchase prices or selling prices. The manager state therefore remains degraded.

## Owned availability watch (bootstrap + ledger)

### Entry 8522487 (Haaland)

| player | status | chance | news / ledger | GW6 note |
|---|---|---:|---|---|
| Haaland | a | — | — | LIV (A); keep; captaincy optional vs Bruno |
| B.Fernandes | a | — | Man Utd Dorgu/Fernandes URL 403 today | TOT (H); strong (C) lean |
| João Pedro | d | 75 | knee; no Chelsea official | hold toward BOU (H) |
| van Ewijk | d | 75 | hamstring | bench/funding |
| Castagne / Dewsbury-Hall / Thiago / others | a | — | — | monitor only |

### Entry 7337262 (no Haaland)

| player | status | chance | news / ledger | GW6 note |
|---|---|---:|---|---|---|
| Palmer | d | 75 | muscular; no Chelsea official | not (C); Rogers fallback |
| Semenyo | d | 75 | ankle; no City timed original inside gate | hold/monitor; LIV (A) hard |
| Rice | d | 75 | unspecified; no Arsenal timed original today | monitor |
| João Pedro | d | 75 | knee; no Chelsea official | hold toward BOU (H) |
| Isak | d | 75 | thigh; LFC `model:e30bb87a…` | not (C); City (H) tough |
| Obi | u | 0 | Willem II loan | dead slot / WC pressure |
| Rogers | a | — | — | fallback (C) while Palmer flagged |
| Raya / Gabriel / Guéhi / Anderson / Castagne / Truffert | a | — | — | core available spine |

Gakpo (`model:8134847f…`) and Havertz (`model:706e27a4…`) are **not owned**; treat as market monitors only.

## Chip and transfer lean (live entries)

- **No chip today.** Deadline 2026-10-10T10:00:00Z.
- **No forced FT today.** Prefer to wait for remaining IB pressers.
- Haaland entry: if a single FT is later forced, prefer a low-regret DEF/MID hygiene move over selling Pedro early; do not chase Bogle into ARS (A) or Gakpo while ankle-flagged.
- No-Haaland entry: WC6 becomes the default if ≥3 of {Palmer, Semenyo, Rice, Pedro, Isak} remain unavailable near deadline; otherwise sequence FTs after clearer club updates. Do not buy Gakpo into this mess.

## Captain lean (live entries)

| entry | provisional (C) | provisional (VC) | rationale |
|---|---|---|---|
| 8522487 | B.Fernandes | Haaland | Bruno vs TOT (H); Haaland away at Anfield with Isak/Gakpo flags |
| 7337262 | Rogers | Raya | Palmer doubtful; Isak not a City-home captain chase |

## Falsifiers

- Chelsea timed original rules Pedro out beyond GW6 → sell/WC pressure rises on both entries.
- Liverpool clears Isak (and/or Gakpo) with normal minutes → no-Haaland Isak hold strengthens; Haaland (C) debate reopens slightly.
- City clears Semenyo and starts him vs LIV while Cherki/other City options blank → Semenyo hold/buy reassess.
- Man Utd official body confirms Bruno fitness concern → flip Haaland-entry captaincy plan.
- Three or more no-Haaland doubts become unavailable inside ~72h of deadline → prepare WC6 draft.

## Relationship to automated strategy briefing

`reports/strategy-research/2026-09-29.md` is the primary advisory reconstruction (Kinsky/Cherki/Wissa Haaland-in 15). It must **not** be treated as the owned squad for entries 8522487 / 7337262. Use this live-entry note for account-facing holds; use the strategy briefing for Lane A admission hashes and the laboratory’s declared advisory 15.
