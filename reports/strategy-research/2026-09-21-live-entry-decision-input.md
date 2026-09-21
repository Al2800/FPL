# Live-entry decision input — 2026-09-21

- observed_at: 2026-09-21T07:24:29Z
- entries: 8522487 and 7337262
- decision point: post-match GW5 processing; first day of the international break
- next deadline: 2026-10-10T10:00:00Z (11:00 BST)
- governing method: official public FPL state for squads, picks and scoring; dated official club sources for role and availability; community sources only as challenge inputs
- account writes: false
- operational authority: this report, not the Kinsky/Cherki/Wissa reconstruction in `reports/strategy-research/2026-09-21.md`

## Executive decision

No early GW6 transfer and no chip action on either entry.

GW5 matches are complete on the pitch, but official FPL still reports event 5 as `finished=false` and `data_checked=false`. Entry 7337262's valid Truffert-for-João Pedro autosub is therefore not yet shown in `automatic_subs`. Treat 41/289 as the current official total and 43/291 as the expected total after routine autosub processing, not as final until the endpoint changes.

Material changes since 20 September:

1. Entry 8522487 is now settled at 51 GW5 points and 292 total.
2. Entry 7337262 is at 41 GW5 points and 289 total before the expected two-point Truffert autosub.
3. Shaw played 83 minutes and the bootstrap now lists him available at 100%. This improves the no-Haaland squad's GW6 bench.
4. Official City evidence confirms Haaland, Guéhi, Anderson and Semenyo started against Sunderland. Semenyo played on the wing, Haaland as striker, Anderson in central midfield and Guéhi at centre-back. Doku returned from injury as a substitute for Semenyo after 75 minutes.
5. João Pedro remains 75% with a knee flag dated 16 September. No timed Chelsea original establishes his return date.
6. Van Ewijk remains 75% with a hamstring flag dated 19 September. No newer official recovery statement was found.

## Official manager state

### Entry 8522487 — Haaland

- GW5: 51 points
- total: 292
- overall rank: 4,877,692 in the live entry summary
- GW5 transfer: Shaw to Castagne, zero cost
- GW5 value/bank snapshot: £99.6m / £0.2m
- chips in public history: none
- bench points: 4
- last authenticated post-transfer state on 18 September: two free transfers and £0.2m
- current GW6 free transfers, pending moves, purchase prices and selling prices: not publicly exposed

Locked GW5 XI:

Verbruggen; Van Hecke, Mitchell, Castagne; B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka; Thiago, Haaland (C).

Vice-captain: B.Fernandes. Bench: Dubravka; João Pedro, Diop, van Ewijk.

### Entry 7337262 — no Haaland

- current official GW5: 41 points
- current official total: 289
- expected after valid autosub: 43 GW5 / 291 total
- current live overall rank: 5,182,949 before autosub processing
- GW5 transfer: Maatsen to Castagne, zero cost
- GW5 value/bank snapshot: £99.8m / £0.0m
- chips in public history: none
- current points on bench field: 10, including Verbruggen 6, Truffert 2 and Shaw 2
- last authenticated post-transfer state on 18 September: zero free transfers and £0.0m
- current GW6 free transfers, pending moves, purchase prices and selling prices: not publicly exposed

Locked GW5 XI:

Raya; Gabriel, Castagne, Guéhi; Rogers, Palmer (C), Semenyo, Rice, Anderson; João Pedro, Isak.

Vice-captain: Rogers. Bench: Verbruggen; Truffert, Shaw, Obi.

João Pedro played zero minutes. Truffert played 90 minutes and scored two, so a legal 4-5-1 autosub is expected when FPL closes the event.

## GW5 outcome review

| boundary | actual | process assessment |
|---|---|---|
| Haaland captain | 12 captain points from one goal and 1.09 xG | correct; strong chance volume and full minutes |
| Palmer captain | 4 captain points | defensible, but Semenyo at home to Sunderland should have been an explicit final captain comparator |
| Semenyo | 17 points from two goals and one assist, but only 0.31 xGI | excellent outcome with substantial finishing variance; do not extrapolate 17-point form |
| Isak | 8 points, one goal, 0.75 xG | positive process and outcome |
| Retain Thiago | 5 points, goal, 0.75 xGI | correct; underlying involvement supports the return |
| H: Shaw to Castagne | Castagne 1; Shaw 2; Diop 4 on bench | weak marginal use of a transfer when playable defensive cover existed |
| no-H: Maatsen to Castagne | Castagne 1; Maatsen 0 | reasonable availability insurance in a squad with multiple defensive doubts |
| Start João Pedro | zero minutes; Truffert 2 pending | downside protection worked; no expected point loss after autosub |
| Raya over Verbruggen | 1 versus 6 | five realised points lost, but primarily outcome variance rather than a clear ex-ante error |

The corrected squads did not have a frozen pre-deadline xP snapshot. Do not manufacture an actual-minus-xP result using current `ep_next`. Approximate GW5 attacking involvement was 5.0 xGI for the Haaland XI and 2.1 xGI for the no-Haaland XI; this is diagnostic context, not expected FPL points.

## Rank context

The current sampled top-1,000 threshold is 411 points.

- 8522487: gap 119.
- 7337262: current official gap 122; expected gap 120 after the Truffert autosub.

The gaps are too early-season and too volatile to justify hits or forced convergence.

## Availability and source freshness

| player | entry | status at observed_at | news timestamp | treatment |
|---|---|---|---|---|
| João Pedro | both | doubtful, 75%, knee | 2026-09-16T19:00:09Z | stale flag; hold through the break pending Chelsea training or manager evidence |
| van Ewijk | 8522487 | doubtful, 75%, hamstring | 2026-09-19T16:00:09Z | bench-depth concern, not an immediate transfer |
| Shaw | 7337262 | available, 100% | status cleared after 83 GW5 minutes | retain as playable GW6 cover |
| Obi | 7337262 | unavailable, 0%, season loan | 2026-09-14T16:12:42Z | dead slot; address only when the move improves the active XI or enables structure |

All other owned players are currently available in the official bootstrap.

## Accepted official evidence

1. Manchester City team news, published 2026-09-20T11:45:00Z, named Guéhi, Anderson, Semenyo and Haaland in the XI. It described Anderson in midfield, Semenyo on the wing and Haaland as striker. Doku was on the bench for the first time since his Community Shield injury:
   https://www.mancity.com/news/mens/team-news-city-sunderland-20-september-63925499
2. Manchester City match report, published 2026-09-20T15:00:00Z, records Semenyo goals at 43 and 57 minutes, Haaland at 81, Semenyo replaced by Doku at 75, and Haaland completing 90:
   https://www.mancity.com/news/mens/city-v-sunderland-match-report-20-september-63925504
3. Official FPL live data records Shaw's 83 minutes and the bootstrap now clears him to available/100%.
4. Prior Tottenham evidence that Porro has a suspected hamstring problem remains binding for the transfer shortlist:
   https://www.tottenhamhotspur.com/news/1091097/team-news-robertos-latest-on-pedro-porro

## Rejected or unresolved claims

- The Kinsky/Cherki/Wissa team in the automated 21 September strategy report is not entry 8522487. Do not apply its XI, transfer count, Wissa or Cherki conclusions to either live entry.
- The report's statement to roll a single free transfer is not verified for either manager. Public endpoints do not expose current free transfers.
- Community estimates of João Pedro's recovery are not official evidence.
- GW5 is not labelled final until FPL marks the event finished/data checked and records the autosub.
- Current `ep_next` is not a retrospective GW5 forecast.
- Doku's return is a minutes challenge for Semenyo, but one 15-minute substitute appearance does not establish a GW6 starting change.

## GW6 provisional decisions

### Entry 8522487

Default: no transfer.

Provisional XI if João Pedro remains unavailable:

Verbruggen; Van Hecke, Mitchell, Castagne; B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka; Thiago, Haaland.

- Captain: Haaland
- Vice-captain: B.Fernandes
- Bench: Dubravka; 1 Diop, 2 João Pedro, 3 van Ewijk

Captaincy remains a live Haaland-versus-Bruno decision. Current official estimates show Haaland 7.8 and Bruno 6.2; Haaland has 4.42 xG in 450 league minutes. Liverpool away versus Spurs home keeps the comparison open, but current lean is Haaland.

If João Pedro is officially cleared with starting-minutes confidence, start him against Bournemouth and provisionally bench Xhaka.

### Entry 7337262

Default: no transfer.

Provisional XI if João Pedro is cleared:

Raya; Gabriel, Castagne, Guéhi; Rogers, Palmer, Semenyo, Rice, Anderson; João Pedro, Isak.

- Captain: Palmer
- Vice-captain: Rogers
- Bench: Verbruggen; 1 Shaw, 2 Truffert, 3 Obi

If João Pedro is not cleared, use Shaw in a 4-5-1. One unavailable forward does not justify a hit or Wildcard.

The squad owns three Manchester City players: Guéhi, Semenyo and Anderson. Any GW7 Haaland acquisition must therefore sell a City player as well as create substantial budget. Model the exact route only after authenticated free transfers and selling prices are captured.

## Rolling GW6–GW9 plan

- GW6: wait for international minutes, injuries and club press conferences. No price-chasing transfer.
- GW7: Man City v Ipswich is the probable Haaland captain anchor. Triple Captain remains a candidate, not a commitment. For 7337262, compare hold-no-Haaland, hits and Wildcard routes using exact private state.
- GW8: City at Aston Villa, Chelsea v Spurs, Arsenal v Everton and Liverpool v Brighton. Preserve premium and forward flexibility.
- GW9: City v Brighton, Chelsea v Man Utd and Liverpool v Arsenal. Reassess after GW6 rather than booking moves today.
- Wildcard threshold: at least three simultaneous structural problems after international duty. Current state does not meet it.

## Manual confirmation required

Before the GW6 deadline, open each authenticated transfer page and record:

1. exact free transfers;
2. bank;
3. purchase and selling prices for plausible outgoing players;
4. pending moves;
5. chip inventory.

Until then, manager state is degraded. Public history verifies completed transfers, chip history and the GW5 value/bank snapshots only.

## Sources

- https://fantasy.premierleague.com/api/bootstrap-static/
- https://fantasy.premierleague.com/api/fixtures/
- https://fantasy.premierleague.com/api/event/5/live/
- https://fantasy.premierleague.com/api/entry/8522487/
- https://fantasy.premierleague.com/api/entry/7337262/
- https://fantasy.premierleague.com/api/entry/8522487/event/5/picks/
- https://fantasy.premierleague.com/api/entry/7337262/event/5/picks/
