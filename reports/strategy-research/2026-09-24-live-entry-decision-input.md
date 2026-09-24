# Live-entry decision input — 2026-09-24

- observed_at: 2026-09-24T07:56:54Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- authority: official FPL bootstrap, fixtures, entry summaries, histories and completed-GW picks
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no material decision change** from 2026-09-23. Make no early transfer and activate no chip during the international break.

The automated strategy report in this branch remains unsuitable for entry-specific action. It reconstructs Kinsky, Cherki and Wissa for entry 8522487 and asserts a free-transfer count that public endpoints cannot verify. Official completed-GW picks and transfer history remain authoritative.

## Official entry state

GW5 remains finished and data checked. The sampled overall top-1,000 boundary remains 414 points.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,350 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,836 | 123 |

Rank movement since 2026-09-23 is immaterial and reflects post-check ordering rather than new points.

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

Public history confirms one free GW5 transfer by each entry, but does not expose the current authenticated free-transfer balance.

## Authoritative squads, GW6 fixture and price

### Entry 8522487, Haaland

| position | player | price | GW6 | status |
|---|---|---:|---|---|
| GKP | Verbruggen | £4.5m | SUN A | available |
| GKP | Dubravka | £4.0m | MUN A | available |
| DEF | Van Hecke | £4.9m | MUN A | available |
| DEF | Mitchell | £4.5m | NFO H | available |
| DEF | Castagne | £4.5m | IPS A | available |
| DEF | Diop | £4.0m | FUL H | available |
| DEF | van Ewijk | £4.0m | NEW H | doubtful, 75% |
| MID | B.Fernandes | £11.9m | TOT H | available |
| MID | Gibbs-White | £8.0m | CRY A | available |
| MID | E.Le Fée | £5.7m | BHA H | available |
| MID | Dewsbury-Hall | £6.6m | HUL A | available |
| MID | Xhaka | £5.5m | BHA H | available |
| FWD | Thiago | £7.8m | AVL A | available |
| FWD | Haaland | £15.6m | LIV A | available |
| FWD | João Pedro | £7.7m | BOU H | doubtful, 75% |

### Entry 7337262, no Haaland

| position | player | price | GW6 | status |
|---|---|---:|---|---|
| GKP | Raya | £6.1m | LEE H | available |
| GKP | Verbruggen | £4.5m | SUN A | available |
| DEF | Gabriel | £8.0m | LEE H | available |
| DEF | Guéhi | £6.0m | LIV A | available |
| DEF | Castagne | £4.5m | IPS A | available |
| DEF | Truffert | £5.4m | CHE A | available |
| DEF | Shaw | £4.3m | TOT H | available |
| MID | Palmer | £9.7m | BOU H | doubtful, 75% |
| MID | Rogers | £7.7m | BOU H | available |
| MID | Semenyo | £8.4m | LIV A | available |
| MID | Rice | £7.4m | LEE H | doubtful, 75% |
| MID | Anderson | £6.3m | LIV A | available |
| FWD | Isak | £9.1m | MCI H | available |
| FWD | João Pedro | £7.7m | BOU H | doubtful, 75% |
| FWD | Obi | £4.5m | TOT H | unavailable, loan |

## Availability and source freshness

| player | FPL flag | news timestamp | change |
|---|---|---|---|
| Palmer | muscular, 75% | 2026-09-21T13:00:09Z | unchanged |
| Rice | unspecified, 75% | 2026-09-21T13:00:08Z | unchanged |
| João Pedro | knee, 75% | 2026-09-16T19:00:09Z | unchanged and stale |
| van Ewijk | hamstring, 75% | 2026-09-19T16:00:09Z | unchanged |
| Obi | unavailable, 0% | 2026-09-14T18:30:08Z | unchanged |

The repository's 2026-09-24 official discovery run searched 21 clubs and admitted zero availability claims. Its only dated lead was a Fulham U21 preview with no first-team relevance. The evidence-ledger tip therefore remains unchanged.

An official Manchester City article published 20 September lists the international schedules of several owned players. Haaland is due four Norway matches from 24 September to 4 October; Anderson and Guéhi four England matches from 26 September to 6 October; Semenyo three Ghana matches from 24 September to 4 October. This is accepted as workload-monitoring evidence, not an injury or selection claim.

Search surfaced Chelsea pages concerning Palmer and João Pedro, but their publication dates could not be recovered and their FA Cup semi-final context does not match the current GW6 decision window. They are rejected for point-in-time use. Old Arsenal Rice pages are also rejected.

## Projection movement

Official FPL `ep_next` is unchanged for Haaland (9.2), Bruno (7.2), Semenyo (7.8) and Isak (7.8). It has reduced for Palmer to 2.8, João Pedro to 4.1 and Rogers to 5.2. These are mutable game estimates and do not establish medical severity or expected minutes independently.

## Provisional GW6 decisions

### Entry 8522487

Verbruggen  
Van Hecke, Mitchell, Castagne  
B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka  
Thiago, Haaland

- Captain: **Haaland**
- Vice-captain: **B.Fernandes**
- Bench: Dubravka; 1 Diop; 2 João Pedro; 3 van Ewijk
- If Chelsea clears João Pedro for normal minutes, start him and bench Xhaka.
- No transfer or chip now.

### Entry 7337262

Assuming Palmer, Rice and João Pedro recover:

Raya  
Gabriel, Castagne, Guéhi  
Rogers, Palmer, Semenyo, Rice, Anderson  
João Pedro, Isak

- Current risk-adjusted captain: **Rogers**
- Vice-captain: **Palmer**
- Restore Palmer as captain, Rogers vice-captain, only if Chelsea clears Palmer for normal minutes.
- Bench: Verbruggen; 1 Shaw; 2 Truffert; 3 Obi
- If João Pedro remains out, start Shaw in a 4-5-1.
- If Palmer, Rice and João Pedro remain doubtful close to the deadline, rerun the full transfer-versus-Wildcard comparison.
- No transfer or chip now.

## Rolling four-Gameweek plan

- GW6: preserve information value through the extended break. Monitor international appearances, withdrawals and club returns.
- GW7: Manchester City versus Ipswich remains the likely Haaland captain focal point. Recalculate the no-Haaland route only with authenticated prices and free-transfer state.
- GW8–GW9: retain flexibility around Palmer, Bruno, João Pedro and premium structure rather than pre-committing transfers.
- Wildcard threshold: at least three late structural problems after official news. Free Hit and Triple Captain remain unjustified today.

## Community challenge review

The 2026-09-23 X digest was reviewed. It adds price-faller discussion, stronger Wildcard-six draft chatter, and Saka/Barry/Schade modelling, but no verified medical update. These remain challenge inputs. They do not override the official live squads or create an early-transfer case.

## Manager-state degradation

Public endpoints cannot verify pending transfers, current free transfers, purchase prices or selling prices. Before the GW6 deadline, manually confirm on both authenticated transfer pages:

1. exact free-transfer count;
2. current bank and team value;
3. purchase and selling prices for possible movers;
4. whether any pending transfer exists;
5. current chip availability and intended chip state.

No FPL account action was executed.

## Sources

- Official FPL bootstrap: https://fantasy.premierleague.com/api/bootstrap-static/
- Official fixtures: https://fantasy.premierleague.com/api/fixtures/
- Entry 8522487: https://fantasy.premierleague.com/api/entry/8522487/
- Entry 7337262: https://fantasy.premierleague.com/api/entry/7337262/
- GW5 picks: https://fantasy.premierleague.com/api/entry/8522487/event/5/picks/ and https://fantasy.premierleague.com/api/entry/7337262/event/5/picks/
- Histories: https://fantasy.premierleague.com/api/entry/8522487/history/ and https://fantasy.premierleague.com/api/entry/7337262/history/
- Manchester City international schedule, published 20 September 2026: https://www.mancity.com/news/mens/international-break-explainer-september-october-2026-63925599
