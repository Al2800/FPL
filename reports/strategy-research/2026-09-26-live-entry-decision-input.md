# Live-entry decision input — 2026-09-26

- observed_at: 2026-09-26T07:36:55Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- authority: official FPL bootstrap, fixtures, entry summaries, histories and completed-GW picks
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no material decision change** from 2026-09-25. Make no early transfer and activate no chip.

Official FPL statuses, owned-player prices, completed-GW scores, transfer history and chip history are unchanged. Semenyo remains 75% with an ankle injury and no dated Manchester City or Ghana original yet establishes severity or return timing.

The new official evidence is that Rayan Cherki, a credible Manchester City comparison candidate but not an owned player in either public entry, started for France and played 78 minutes on 25 September. This supports his availability but does not create a transfer case into Liverpool away.

The automated strategy report's Kinsky/Cherki/Wissa squad and current one-free-transfer assertion remain invalid for entries 8522487 and 7337262.

## Official entry state

GW5 remains finished and data checked. The sampled top-1,000 boundary remains 414.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,291 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,776 | 123 |

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

The official GW5 picks and transfers are unchanged. Public endpoints do not expose the current free-transfer balance, pending transfers, purchase prices or selling prices.

## Authoritative squads and current prices

### Entry 8522487

- GKP: Verbruggen £4.5m; Dubravka £4.0m
- DEF: Van Hecke £4.9m; Mitchell £4.5m; Castagne £4.5m; Diop £4.0m; van Ewijk £4.0m
- MID: B.Fernandes £11.9m; Gibbs-White £8.0m; E.Le Fée £5.7m; Dewsbury-Hall £6.6m; Xhaka £5.5m
- FWD: Thiago £7.8m; Haaland £15.6m; João Pedro £7.7m

### Entry 7337262

- GKP: Raya £6.1m; Verbruggen £4.5m
- DEF: Gabriel £8.0m; Guéhi £6.0m; Castagne £4.5m; Truffert £5.4m; Shaw £4.3m
- MID: Palmer £9.7m; Rogers £7.7m; Semenyo £8.4m; Rice £7.4m; Anderson £6.3m
- FWD: Isak £9.1m; João Pedro £7.7m; Obi £4.5m

No owned-player price changed since 2026-09-25.

## Availability and freshness

| player | FPL state | chance | news timestamp | change |
|---|---|---:|---|---|
| Semenyo | ankle injury | 75% | 2026-09-24T12:00:09Z | unchanged |
| Palmer | muscular injury | 75% | 2026-09-21T13:00:09Z | unchanged |
| Rice | unspecified injury | 75% | 2026-09-21T13:00:08Z | unchanged |
| João Pedro | knee injury | 75% | 2026-09-16T19:00:09Z | unchanged; stale |
| van Ewijk | hamstring injury | 75% | 2026-09-19T16:00:09Z | unchanged |
| Obi | season loan | 0% | 2026-09-14T16:12:42Z | unchanged |
| Shaw | available | 100% | 2026-09-11T13:00:09Z | unchanged |
| all other owned players | available | 100% or unflagged | bootstrap current | unchanged |

The 2026-09-26 repository discovery run searched 21 clubs and admitted two official claims:

- Cherki started for France and played 78 minutes.
- Donnarumma started for Italy; comparator-only.

The ledger tip changed from `61779acc…` to `4f1b89f7…`. Neither player is owned by the two entries. Haaland's 24 September Norway brace remains admitted evidence.

No current official source was found for the severity of Semenyo, Palmer, Rice or João Pedro. Search hits from old seasons or unrecoverable publication windows were rejected.

## Community challenge review

The 2026-09-25 X digest was reviewed. It correctly noticed the Semenyo 75% flag but added no verified severity. Wildcard-six, Palmer-to-Saka and budget-forward discussion remain challenge inputs only. Tzolakis and Smith Rowe price chatter does not affect either owned squad.

## Provisional GW6 decisions

### Entry 8522487

Verbruggen  
Van Hecke; Mitchell; Castagne  
B.Fernandes; Gibbs-White; E.Le Fée; Dewsbury-Hall; Xhaka  
Thiago; Haaland

- Captain: **Haaland**
- Vice-captain: **B.Fernandes**
- Bench: Dubravka; 1 Diop; 2 João Pedro; 3 van Ewijk
- If João Pedro is cleared for normal minutes, start him and bench Xhaka.
- No transfer or chip today.

### Entry 7337262

If all four doubts recover:

Raya  
Gabriel; Castagne; Guéhi  
Rogers; Palmer; Semenyo; Rice; Anderson  
João Pedro; Isak

- Current risk-adjusted captain: **Rogers**
- Vice-captain: **Palmer**
- Restore Palmer as captain, Rogers vice-captain, only after a normal-minutes clearance.
- Bench: Verbruggen; 1 Shaw; 2 Truffert; 3 Obi
- If either Semenyo or João Pedro is unavailable, Shaw is first replacement.
- If two attacking doubts are unavailable, Truffert may also be required.
- If at least three of Palmer, Rice, Semenyo and João Pedro remain doubtful near the deadline, run an authenticated free-transfer-versus-hits-versus-Wildcard comparison.
- No transfer or chip today.

## Rolling four-Gameweek plan

- GW6: preserve information. Monitor England minutes for Guéhi and Anderson from 26 September, remaining Norway matches for Haaland, and any Semenyo Ghana-camp update.
- GW7: Manchester City versus Ipswich remains the probable Haaland captain focal point. Model any no-Haaland route only after authenticated prices and free transfers are known.
- GW8–GW9: retain flexibility around Palmer, Bruno, João Pedro, Semenyo and premium structure.
- Wildcard threshold: late official evidence leaves at least three structural problems or fewer than eleven credible starters after affordable free-transfer repair.

## Manager-state degradation

Before the final GW6 recommendation, manually confirm on both authenticated transfer pages:

1. exact free-transfer count;
2. current bank and team value;
3. purchase and selling prices for possible movers;
4. whether any pending transfer exists;
5. chip availability and intended chip state.

No FPL account action was executed.

## Sources

- Official FPL bootstrap: https://fantasy.premierleague.com/api/bootstrap-static/
- Official fixtures: https://fantasy.premierleague.com/api/fixtures/
- Entry 8522487: https://fantasy.premierleague.com/api/entry/8522487/
- Entry 7337262: https://fantasy.premierleague.com/api/entry/7337262/
- Official histories: https://fantasy.premierleague.com/api/entry/8522487/history/ and https://fantasy.premierleague.com/api/entry/7337262/history/
- Manchester City international roundup, published 25 September 2026: https://www.mancity.com/news/mens/donnarumma-cherki-bouaddi-international-round-up-september-25-63925962
