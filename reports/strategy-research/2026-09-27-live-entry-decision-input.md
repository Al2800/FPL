# Live-entry decision input — 2026-09-27

- observed_at: 2026-09-27T07:26:24Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for squads, completed picks, transfers and scoring; official club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no transfer or chip action today**. Both squads should remain untouched through the international break.

The material new evidence is that two owned no-Haaland players, Marc Guéhi and Elliot Anderson, started for England against Spain on 26 September. This supports current availability but adds international workload; it does not resolve the separate Palmer, Rice, Semenyo or João Pedro doubts.

One provisional decision is improved: if Palmer is not cleared for normal minutes, **Isak becomes the no-Haaland captain and Rogers the vice-captain**. Official FPL currently estimates Isak at 7.8 points away to Coventry versus Rogers at 5.2. If Palmer is cleared for normal minutes, restore Palmer captain and use Isak vice-captain.

The automated strategy report's Kinsky/Cherki/Wissa squad and exact-one-free-transfer assertion remain invalid for entries 8522487 and 7337262.

## Official entry state

GW5 is finished and data checked. The sampled overall rank-994 entry has 414 points, so 414 remains the working top-1,000 boundary.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,287 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,772 | 123 |

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

Official transfer history remains:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, B.Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

Public endpoints do not expose the current free-transfer balance, pending transfers, purchase prices or selling prices. The manager state therefore remains degraded.

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

No owned-player price changed since 26 September.

## Availability, workload and source freshness

| player | official state | chance | published / news timestamp | observed_at | implication |
|---|---|---:|---|---|---|
| Guéhi | started for England v Spain | available | 2026-09-26T20:45:00Z | 2026-09-27T07:26:24Z | availability supported; three England matches remain |
| Anderson | started for England v Spain | available | 2026-09-26T20:45:00Z | 2026-09-27T07:26:24Z | availability supported; three England matches remain |
| Semenyo | ankle injury | 75% | 2026-09-24T12:00:09Z | 2026-09-27T07:26:24Z | severity and Ghana participation unresolved |
| Palmer | muscular injury | 75% | 2026-09-21T13:00:09Z | 2026-09-27T07:26:24Z | withdrew from England; no Chelsea GW6 return timeline |
| Rice | unspecified injury | 75% | 2026-09-21T13:00:08Z | 2026-09-27T07:26:24Z | withdrew from England; no Arsenal GW6 return timeline |
| João Pedro | knee injury | 75% | 2026-09-16T19:00:09Z | 2026-09-27T07:26:24Z | stalest material flag; no current Chelsea return statement |
| van Ewijk | hamstring injury | 75% | 2026-09-19T16:00:09Z | 2026-09-27T07:26:24Z | bench-depth risk only |
| Obi | on season loan | 0% | 2026-09-14T16:12:42Z | 2026-09-27T07:26:24Z | unavailable; do not take a hit solely to remove |
| Shaw | available | 100% | 2026-09-11T13:00:09Z | 2026-09-27T07:26:24Z | usable first bench cover |
| all other owned players | available | 100% or unflagged | bootstrap current | 2026-09-27T07:26:24Z | no new issue |

The repository model run admitted five Manchester City official claims: England starts for O'Reilly, Guéhi and Anderson, plus 90 minutes for Gvardiol and Kovačić for Croatia. Guéhi and Anderson are owned by entry 7337262; the other three are comparator evidence only. The ledger tip changed from `4f1b89f7…` to `fdc175a8…`.

Haaland's Norway brace on 24 September remains accepted fitness evidence, but he has three further internationals scheduled through 4 October. Guéhi and Anderson also have three matches remaining through 6 October. This supports waiting rather than acting early.

No current official club or association source establishes the severity or GW6 return date for Semenyo, Palmer, Rice or João Pedro. Those claims remain unresolved, not assumed positive or negative.

## Community challenge review

The latest repository X digest, observed 25 September, was reviewed. It identified the Semenyo flag and continued Wildcard-six, Palmer-to-Saka and budget-forward discussion, but supplied no admissible medical evidence. Price-tracker and return-date posts remain discovery or challenge inputs only.

Accepted community implication: the no-Haaland squad should be stress-tested for a Wildcard if multiple doubts persist.

Rejected community implications: activate Wildcard now; sell Palmer or João Pedro during the break; buy Semenyo while ankle-flagged; treat a tracker post as confirmation of availability.

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

- If Palmer is not cleared: captain **Isak**, vice-captain **Rogers**.
- If Palmer is cleared for normal minutes: captain **Palmer**, vice-captain **Isak**.
- Bench: Verbruggen; 1 Shaw; 2 Truffert; 3 Obi.
- If either Semenyo or João Pedro is unavailable, Shaw is first replacement.
- If two attacking doubts are unavailable, Truffert may also be required.
- If at least three of Palmer, Rice, Semenyo and João Pedro remain doubtful near the deadline, run an authenticated free-transfer-versus-hits-versus-Wildcard comparison.
- No transfer or chip today.

## Rolling GW6–GW9 plan

- GW6: preserve information. Chelsea host Bournemouth, Arsenal host Leeds, Newcastle visit Coventry and City visit Liverpool. Do not sacrifice post-break team news for an early price move.
- GW7: City host Ipswich, making Haaland the probable captain anchor. Model the no-Haaland route only after exact free transfers and selling prices are authenticated.
- GW8: Chelsea host Spurs and United host Bournemouth. Retain Palmer/Bruno flexibility rather than pre-booking a sale.
- GW9: City host Brighton and Chelsea host United. Reassess premium structure with four new weeks of minutes and injury information.
- Wildcard threshold: late official evidence leaves at least three structural problems or fewer than eleven credible starters after affordable free-transfer repair.
- No Free Hit, Bench Boost or Triple Captain case currently clears the methodology threshold.

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
- Entry summaries: https://fantasy.premierleague.com/api/entry/8522487/ and https://fantasy.premierleague.com/api/entry/7337262/
- Official histories: https://fantasy.premierleague.com/api/entry/8522487/history/ and https://fantasy.premierleague.com/api/entry/7337262/history/
- Official transfer histories: https://fantasy.premierleague.com/api/entry/8522487/transfers/ and https://fantasy.premierleague.com/api/entry/7337262/transfers/
- Manchester City England/Croatia roundup, published 26 September 2026: https://www.mancity.com/news/mens/england-spain-croatia-czechia-63926047
- Manchester City international schedule, published 20 September 2026: https://www.mancity.com/news/mens/international-break-explainer-september-october-2026-63925599
- England squad update, published 18 September and updated for 21 September withdrawals: https://www.englandfootball.com/articles/2026/Sep/18/england-mens-senior-squad-announcement-september-october-20261809

