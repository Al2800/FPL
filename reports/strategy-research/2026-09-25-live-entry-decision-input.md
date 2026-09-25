# Live-entry decision input — 2026-09-25

- observed_at: 2026-09-25T07:43:55Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- authority: official FPL bootstrap, fixtures, entry summaries, histories and completed-GW picks
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is a **material monitoring change but no action change today**.

1. Semenyo is newly flagged by official FPL at 75% with an ankle injury. The flag was added at 2026-09-24T12:00:09Z. Entry 7337262 now has four doubtful starters: Palmer, Rice, João Pedro and Semenyo.
2. Manchester City's official international roundup, published 2026-09-24T21:00:00Z, confirms Haaland started for Norway and scored twice in a 3-2 win over Denmark.

Make no early transfer and activate no chip. The new Semenyo flag materially raises the probability that the no-Haaland squad will need multiple transfers or a Wildcard, but the deadline is still 15 days away and no official club or Ghana source yet establishes the severity.

The automated strategy report in this branch remains unsuitable for entry-specific action. Its Kinsky/Cherki/Wissa reconstruction and current free-transfer assertion conflict with official completed-GW picks or rely on private state.

## Official entry state

GW5 remains finished and data checked. The sampled overall top-1,000 boundary remains 414 points.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,330 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,816 | 123 |

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

No official points, prices, completed-GW picks, transfer history or chip history changed since 2026-09-24. Current free transfers and pending transfers are not public.

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
| FWD | Haaland | £15.6m | LIV A | available; Norway brace confirmed |
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
| MID | Semenyo | £8.4m | LIV A | **newly doubtful, ankle, 75%** |
| MID | Rice | £7.4m | LEE H | doubtful, 75% |
| MID | Anderson | £6.3m | LIV A | available |
| FWD | Isak | £9.1m | MCI H | available |
| FWD | João Pedro | £7.7m | BOU H | doubtful, 75% |
| FWD | Obi | £4.5m | TOT H | unavailable, loan |

## Availability and freshness

| player | official FPL state | news timestamp | change |
|---|---|---|---|
| Semenyo | ankle, 75% | 2026-09-24T12:00:09Z | **new** |
| Palmer | muscular, 75% | 2026-09-21T13:00:09Z | unchanged |
| Rice | unspecified, 75% | 2026-09-21T13:00:08Z | unchanged |
| João Pedro | knee, 75% | 2026-09-16T19:00:09Z | unchanged and stale |
| van Ewijk | hamstring, 75% | 2026-09-19T16:00:09Z | unchanged |
| Obi | unavailable, loan, 0% | 2026-09-14T18:30:08Z | unchanged |
| Haaland | available | bootstrap current | official Norway start and brace accepted |

The repository's 2026-09-25 official discovery run searched 21 clubs. It admitted one new claim to the availability ledger: Haaland started and scored twice for Norway. The ledger tip changed from `1c0620f2…` to `61779acc…`.

The Semenyo FPL flag is accepted as an official game-state observation. No dated Manchester City or Ghana Football Association original explaining the ankle injury was located, so severity, withdrawal status and return date remain unknown.

## Official and community claim review

Accepted:

- Official FPL: Semenyo is newly doubtful at 75% with an ankle injury, timestamp 24 September.
- Manchester City: Haaland scored twice for Norway on 24 September, supporting current availability.
- Official FPL: all other owned-player flags and prices are unchanged.

Rejected or deferred:

- Community Wildcard-six popularity as a reason to activate now.
- Palmer to Saka and João Pedro to Barry as immediate transfers; neither has authenticated affordability or resolved injury inputs.
- Any assertion that Semenyo will miss GW6; the FPL flag does not establish duration.
- Undated or wrong-window Chelsea pages concerning Palmer and João Pedro.
- The automated Kinsky/Cherki/Wissa squad reconstruction and one-free-transfer assertion.

The 2026-09-24 X digest contained no verified medical update. Price-tracker and Wildcard chatter remains challenge-only.

## Projection movement

Official FPL `ep_next` has fallen for Semenyo from 7.8 to 5.8 after the ankle flag. Haaland remains 9.2; Bruno 7.2; Isak 7.8; Palmer 2.8; João Pedro 4.1; Rogers 5.2. These estimates are not independent medical or expected-minutes evidence.

## Provisional GW6 decisions

### Entry 8522487

Verbruggen  
Van Hecke, Mitchell, Castagne  
B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka  
Thiago, Haaland

- Captain: **Haaland**
- Vice-captain: **B.Fernandes**
- Bench: Dubravka; 1 Diop; 2 João Pedro; 3 van Ewijk
- If João Pedro is cleared for normal minutes, start him and bench Xhaka.
- Haaland's brace strengthens availability confidence but does not justify a chip or early transfer.

### Entry 7337262

If all four doubts recover:

Raya  
Gabriel, Castagne, Guéhi  
Rogers, Palmer, Semenyo, Rice, Anderson  
João Pedro, Isak

- Current risk-adjusted captain: **Rogers**
- Vice-captain: **Palmer**
- Restore Palmer as captain, Rogers vice-captain, only after a normal-minutes clearance.
- Bench: Verbruggen; 1 Shaw; 2 Truffert; 3 Obi
- If either João Pedro or Semenyo is unavailable, Shaw is first replacement.
- If two attacking doubts are unavailable, Truffert may also be required.
- If Palmer, Rice, João Pedro and Semenyo remain doubtful close to the deadline, run a full authenticated multi-transfer-versus-Wildcard comparison. If all four are unavailable, the current squad cannot field eleven without transfers.

No transfer or chip today.

## Rolling four-Gameweek plan

- GW6: preserve information through the break. Track Semenyo's Ghana-camp status and remaining international appearances for Haaland, Guéhi and Anderson.
- GW7: Manchester City versus Ipswich remains the likely Haaland captain focal point. Recalculate the no-Haaland route only with authenticated prices and transfer state.
- GW8–GW9: retain flexibility around Palmer, Bruno, João Pedro, Semenyo and premium structure.
- Wildcard threshold: post-break official evidence leaves at least three structural problems or fewer than eleven credible starters after affordable free-transfer repair.

## Manager-state degradation

Public endpoints cannot verify pending transfers, current free transfers, purchase prices or selling prices. Before the GW6 decision, manually confirm on both authenticated transfer pages:

1. exact free-transfer count;
2. current bank and team value;
3. purchase and selling prices for proposed movers;
4. whether any pending transfer exists;
5. chip availability and intended chip state.

No account action was executed.

## Sources

- Official FPL bootstrap: https://fantasy.premierleague.com/api/bootstrap-static/
- Official fixtures: https://fantasy.premierleague.com/api/fixtures/
- Entry 8522487: https://fantasy.premierleague.com/api/entry/8522487/
- Entry 7337262: https://fantasy.premierleague.com/api/entry/7337262/
- GW5 picks: https://fantasy.premierleague.com/api/entry/8522487/event/5/picks/ and https://fantasy.premierleague.com/api/entry/7337262/event/5/picks/
- Histories: https://fantasy.premierleague.com/api/entry/8522487/history/ and https://fantasy.premierleague.com/api/entry/7337262/history/
- Manchester City Haaland roundup, published 24 September 2026: https://www.mancity.com/news/mens/erling-haaland-norway-ruben-dias-portugal-abdukodir-khusanov-uzbekistan-round-up-63925880
