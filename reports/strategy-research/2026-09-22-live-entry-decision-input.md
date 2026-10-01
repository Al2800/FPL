# Live-entry decision input — 2026-09-22

- observed_at: 2026-09-22T07:58:17Z
- entries: 8522487 and 7337262
- decision point: international-break monitoring after final GW5 processing
- next deadline: 2026-10-10T10:00:00Z (11:00 BST)
- governing method: official public FPL state for squads, prices, fixtures and scoring; dated official club or association sources for availability and role; community sources only as challenge inputs
- account writes: false
- operational authority: this report, not the Kinsky/Cherki/Wissa reconstruction in `reports/strategy-research/2026-09-22.md`

## Executive decision

Make no early GW6 transfer and activate no chip on either entry.

GW5 is now officially finished and data checked. FPL has applied Truffert for João Pedro on entry 7337262, taking that entry to 43 GW5 points and 291 total. Entry 8522487 finished on 51 GW5 points and 292 total, so the Haaland entry leads by one point.

There is one material new risk cluster. FPL newly lists Palmer at 75% with a muscular issue and Rice at 75% with an unspecified issue, both timestamped 2026-09-21T13:00:09Z. Both are in the no-Haaland squad, which already contains João Pedro at 75% and the unavailable Obi. This increases the value of waiting through the international break. It does not justify an early transfer while the GW6 deadline is more than two weeks away and no club return timelines are available.

## Official manager state

### Entry 8522487 — Haaland

- final GW5: 51 points
- total: 292
- current entry-summary overall rank: 5,200,447
- GW5 transfer: Shaw to Castagne, zero cost
- GW5 value/bank snapshot: £99.6m / £0.2m
- chips in public history: none
- bench points: 4
- last authenticated post-transfer state on 18 September: two free transfers and £0.2m
- current GW6 free transfers, pending moves, purchase prices and selling prices: not publicly exposed

Locked GW5 squad:

Verbruggen; Van Hecke, Mitchell, Castagne; B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka; Thiago, Haaland; Dubravka, João Pedro, Diop, van Ewijk.

### Entry 7337262 — no Haaland

- final GW5: 43 points
- total: 291
- current entry-summary overall rank: 5,320,937
- completed autosub: Truffert in for João Pedro
- GW5 transfer: Maatsen to Castagne, zero cost
- GW5 value/bank snapshot: £99.8m / £0.0m
- chips in public history: none
- final bench points: 8
- last authenticated post-transfer state on 18 September: zero free transfers and £0.0m
- current GW6 free transfers, pending moves, purchase prices and selling prices: not publicly exposed

Locked GW5 squad:

Raya; Gabriel, Castagne, Guéhi, Truffert; Palmer, Rogers, Semenyo, Rice, Anderson; Isak; Verbruggen, João Pedro, Shaw, Obi.

The entry-summary and history endpoints differ by fewer than 50 rank places immediately after processing. Points agree. Use the entry summary for the current rank and treat the difference as normal post-processing drift.

## Rank context

The sampled overall rank-1,000 boundary is 414 points.

- 8522487: 122-point gap.
- 7337262: 123-point gap.

The entries are separated by one point. Neither gap supports hits, premature price moves or an international-break Wildcard on its own.

## Prices, estimates and status changes

| player | entry | price | official GW6 EP | status at observed_at | news timestamp | treatment |
|---|---|---:|---:|---|---|---|
| Palmer | 7337262 | £9.7m | 4.2 | doubtful, 75%, muscular | 2026-09-21T13:00:09Z | new material flag; do not captain until cleared |
| Rice | 7337262 | £7.4m | 3.2 | doubtful, 75%, unspecified | 2026-09-21T13:00:08Z | new material flag; monitor, no early sale |
| João Pedro | both | £7.7m | 4.9 | doubtful, 75%, knee | 2026-09-16T19:00:09Z | unchanged; club return date unresolved |
| van Ewijk | 8522487 | £4.0m | 0.9 | doubtful, 75%, hamstring | 2026-09-19T16:00:09Z | unchanged bench-depth concern |
| Shaw | 7337262 | £4.3m | 2.0 | available, 100% | cleared after GW5 | retain as cover |
| Obi | 7337262 | £4.5m | 0.0 | unavailable, 0%, loan | 2026-09-14T16:12:42Z | dead slot; only sell when the move improves structure |

Relevant current official estimates: Haaland 7.8, Bruno 7.2, Isak 6.6, Semenyo 6.6, Raya 6.0, Guéhi 6.0 and Rogers 5.8. These are current forward-looking game estimates, not frozen independent projections.

All other owned players are available in the bootstrap. João Pedro and Bruno are now £7.7m and £11.9m respectively. Do not infer either entry's selling price from the public current price.

## Accepted official evidence

1. Official FPL now marks GW5 `finished=true` and `data_checked=true`; the entry 7337262 picks endpoint records Truffert replacing João Pedro.
2. Official FPL added the Palmer muscular 75% and Rice unspecified 75% flags on 21 September at approximately 13:00Z.
3. England's current official senior squad page contains Morgan Gibbs-White and James Garner but no Palmer or Rice. This supports their non-participation in the international window; it does not establish severity or a GW6 return date:
   https://www.englandfootball.com/england/mens-senior-team/squad
4. Prior official Manchester City evidence remains relevant for Haaland, Guéhi, Anderson and Semenyo roles, with Doku's substitute return a minutes challenge rather than proof Semenyo loses his place:
   https://www.mancity.com/news/mens/team-news-city-sunderland-20-september-63925499
   https://www.mancity.com/news/mens/city-v-sunderland-match-report-20-september-63925504
5. Prior Tottenham evidence continues to rule Porro out as an immediate defender target:
   https://www.tottenhamhotspur.com/news/1091097/team-news-robertos-latest-on-pedro-porro

## Rejected or unresolved claims

- The automated Kinsky/Cherki/Wissa squad is not entry 8522487. Its XI, transfer count and player conclusions are not applicable to either live entry.
- The automated report's statement that the Haaland entry has one free transfer is unverified. Public endpoints do not expose current free transfers.
- No timed Chelsea original establishes João Pedro's or Palmer's GW6 availability.
- No timed Arsenal original establishes Rice's diagnosis or return date.
- Third-party reports describe the England withdrawals and possible injury types, but they are discovery evidence only until a club or association original supplies the detail.
- Community Wildcard drafts and João Pedro recovery estimates are not official evidence.
- Current `ep_next` values are not independent projections and must not be used as retrospective GW5 xP.

## GW6 provisional decisions

### Entry 8522487

Default: no transfer and no chip.

If João Pedro remains unavailable:

Verbruggen; Van Hecke, Mitchell, Castagne; B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka; Thiago, Haaland.

- Captain: Haaland
- Vice-captain: B.Fernandes
- Bench: Dubravka; 1 Diop, 2 João Pedro, 3 van Ewijk

If João Pedro is officially cleared with starting-minutes confidence, start him at home to Bournemouth and provisionally bench Xhaka.

Haaland 7.8 versus Bruno 7.2 remains a live captain comparison because the fixtures are Liverpool away and Spurs home respectively. The current lean remains Haaland; settle it only after international minutes and club press conferences.

### Entry 7337262

Default: no transfer and no chip.

Provisional XI if Palmer, Rice and João Pedro are cleared:

Raya; Gabriel, Castagne, Guéhi; Rogers, Palmer, Semenyo, Rice, Anderson; João Pedro, Isak.

- Current risk-adjusted captain: Rogers
- Vice-captain: Palmer
- Bench: Verbruggen; 1 Shaw, 2 Truffert, 3 Obi

If Palmer is officially cleared for normal starting minutes, restore Palmer as captain and Rogers as vice-captain. If João Pedro is unavailable, start Shaw in a 4-5-1. If Palmer, Rice and João Pedro remain material doubts close to the deadline, refresh the full transfer and Wildcard comparison because the squad may otherwise lack 11 credible starters.

Do not use a transfer today merely because three yellow flags are visible. Their common timing around an 18-day international window makes waiting higher value than buying uncertain replacements.

## Rolling GW6–GW9 plan

- GW6: wait for international usage, training returns and club press conferences. Reassess the no-Haaland availability cluster, then decide roll versus repair versus Wildcard.
- GW7: Manchester City v Ipswich remains the likely Haaland captain focal point. Triple Captain is a candidate, not a commitment.
- GW7 no-Haaland route: the squad owns three City players, Guéhi, Semenyo and Anderson. Acquiring Haaland requires selling a City player as well as funding the premium. Model the route only with authenticated free transfers and selling prices.
- GW8: preserve Chelsea, Arsenal and Manchester United flexibility rather than booking transfers during the break.
- GW9: reassess City v Brighton, Chelsea v Manchester United and Liverpool v Arsenal after actual GW6 minutes.
- Wildcard threshold: persistent problems affecting at least three starting slots or a demonstrably superior four-Gameweek restructure. Today's flags raise the probability of that threshold being met but do not meet it yet.

## Manual confirmation required

Before the GW6 deadline, open each authenticated transfer page and record:

1. exact free transfers;
2. bank;
3. purchase and selling prices for plausible outgoing players;
4. pending moves;
5. chip inventory.

Until then, manager state remains degraded. No private state is inferred from public endpoints.

## Sources

- https://fantasy.premierleague.com/api/bootstrap-static/
- https://fantasy.premierleague.com/api/fixtures/
- https://fantasy.premierleague.com/api/entry/8522487/
- https://fantasy.premierleague.com/api/entry/7337262/
- https://fantasy.premierleague.com/api/entry/8522487/history/
- https://fantasy.premierleague.com/api/entry/7337262/history/
- https://fantasy.premierleague.com/api/entry/8522487/transfers/
- https://fantasy.premierleague.com/api/entry/7337262/transfers/
- https://fantasy.premierleague.com/api/entry/8522487/event/5/picks/
- https://fantasy.premierleague.com/api/entry/7337262/event/5/picks/
- https://fantasy.premierleague.com/api/leagues-classic/314/standings/?page_standings=20

