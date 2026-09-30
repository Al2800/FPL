# Live-entry decision input — 2026-09-28

- observed_at: 2026-09-28T07:38:53Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for squads, completed picks, transfers and scoring; official club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is a **material monitoring change but no transfer or chip action today**. Liverpool confirmed on 27 September that owned forward Alexander Isak returned early from Sweden duty with a minor injury, will miss Sweden's remaining three fixtures and will be assessed by Liverpool before the Premier League restart. Official FPL now flags him at 75% with a thigh injury.

The no-Haaland squad now has five doubtful players — Palmer, Semenyo, Rice, João Pedro and Isak — plus Obi unavailable. If all five miss GW6, the squad has only eight currently available legal starters. That increases the probability of a multi-transfer repair or Wildcard, but the deadline remains twelve days away and the injuries are not yet final absences.

Yesterday's companion report incorrectly treated Isak as a Newcastle player facing Coventry. Official FPL lists him at Liverpool, whose GW6 fixture is Manchester City at home. The fallback captain therefore returns to **Rogers while Palmer is doubtful**. Isak is not a captain candidate unless Liverpool clear him for normal minutes, and even then the City fixture is less attractive than Chelsea's home match against Bournemouth.

The automated strategy report's Kinsky/Cherki/Wissa squad and exact-one-free-transfer assertion remain invalid for entries 8522487 and 7337262.

## Official entry state

GW5 is finished and data checked. The sampled overall rank-994 entry has 414 points, so 414 remains the working top-1,000 boundary.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,151 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,636 | 123 |

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

No owned-player price changed since 27 September.

## Availability and source freshness

| player | official state | chance | published / news timestamp | observed_at | change / implication |
|---|---|---:|---|---|---|
| Isak | thigh injury | 75% | FPL 2026-09-27T10:30:09Z; Liverpool 2026-09-27T09:38:00Z | 2026-09-28T07:38:53Z | **new**; withdrew from remaining Sweden games; club assessment pending |
| Semenyo | ankle injury | 75% | 2026-09-24T12:00:09Z | 2026-09-28T07:38:53Z | unchanged; severity unresolved |
| Palmer | muscular injury | 75% | 2026-09-21T13:00:09Z | 2026-09-28T07:38:53Z | unchanged; no Chelsea GW6 return timeline |
| Rice | unspecified injury | 75% | 2026-09-21T13:00:08Z | 2026-09-28T07:38:53Z | unchanged; no Arsenal GW6 return timeline |
| João Pedro | knee injury | 75% | 2026-09-16T19:00:09Z | 2026-09-28T07:38:53Z | unchanged; stalest material flag |
| van Ewijk | hamstring injury | 75% | 2026-09-19T16:00:09Z | 2026-09-28T07:38:53Z | unchanged; Haaland-team bench risk |
| Obi | season loan | 0% | 2026-09-14T16:12:42Z | 2026-09-28T07:38:53Z | unavailable |
| Guéhi / Anderson | available; England starts on 26 September | 100% | club report 2026-09-26T20:45:00Z | 2026-09-28T07:38:53Z | availability supported; workload remains |
| all other owned players | available | 100% or unflagged | bootstrap current | 2026-09-28T07:38:53Z | no new issue |

Official FPL's mutable GW6 estimates now include Haaland 8.0, Bruno 7.2, Mitchell 7.7, Semenyo 6.5, Guéhi 6.0, Isak 5.8 and Rogers 5.2. Isak fell from 7.8 to 5.8 after the injury flag. These estimates are directional inputs, not medical or expected-minutes evidence.

The 28 September repository model run admitted two official claims:

- Isak doubtful: Liverpool's 27 September original confirms a minor injury, early international return and forthcoming club assessment.
- Havertz doubtful: Arsenal's 25 September international roundup states that he was forced off after 30 minutes; comparator only.

The evidence-ledger tip changed from `fdc175a8…` to `303520f8…`. The official-source sweep covered 21 clubs and found no other new owned-player availability statement. Chelsea still has no fresh timed original for João Pedro or Palmer; Arsenal has no new Rice return timeline; no Bournemouth or Ghana original establishes Semenyo's severity.

## Community challenge review

The freshest repository X digest remains 25 September; no weekend digest was committed. Its Wildcard-six, Palmer-to-Saka, budget-forward and injury chatter remains discovery or challenge material only. It contains no admissible evidence that resolves today's five-player doubt cluster.

Accepted community implication: the no-Haaland squad now requires an explicit Wildcard stress test near the deadline.

Rejected community implications: activate Wildcard before medical updates; sell an injured player solely because of a 75% flag; use price trackers as availability evidence; infer João Pedro, Palmer, Rice, Semenyo or Isak's GW6 minutes.

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

If all five doubtful players recover:

Raya  
Gabriel; Castagne; Guéhi  
Rogers; Palmer; Semenyo; Rice; Anderson  
João Pedro; Isak

- While Palmer is doubtful: captain **Rogers**, vice-captain **Raya**.
- If Palmer is cleared for normal minutes: captain **Palmer**, vice-captain **Rogers**.
- Isak must receive a normal-minutes clearance before he is trusted in the XI; do not captain him against Manchester City.
- Bench: Verbruggen; 1 Shaw; 2 Truffert; 3 Obi.
- Shaw and then Truffert cover the first two outfield absences.
- If three or more of Palmer, Rice, Semenyo, João Pedro and Isak remain unavailable near the deadline, run the authenticated free-transfer-versus-hits-versus-Wildcard comparison.
- No transfer or chip today.

## Rolling GW6–GW9 plan

- GW6: preserve information. The no-Haaland team has a real repair risk, but Liverpool, Chelsea, Arsenal, City and Bournemouth updates can materially reduce or confirm it before 10 October.
- GW7: City host Ipswich, making Haaland the probable captain anchor. The no-Haaland team needs an authenticated route-to-Haaland comparison if it remains structurally weak.
- GW8: Chelsea host Spurs and United host Bournemouth. Retain Palmer/Bruno flexibility rather than pre-booking sales.
- GW9: City host Brighton and Chelsea host United. Reassess premium structure with post-break minutes and injury outcomes.
- Wildcard threshold: at least three structural problems remain, fewer than eleven credible starters can be produced without excessive hits, or the authenticated multiweek Wildcard draft materially dominates a free-transfer repair.
- No Free Hit, Bench Boost or Triple Captain case currently clears the methodology threshold.

## Manager-state degradation

Before the final GW6 recommendation, manually confirm on both authenticated transfer pages:

1. exact free-transfer count;
2. current bank and team value;
3. purchase and selling prices for all candidate movers;
4. whether any pending transfer exists;
5. chip availability and intended chip state.

No FPL account action was executed.

## Sources

- Official FPL bootstrap: https://fantasy.premierleague.com/api/bootstrap-static/
- Official fixtures: https://fantasy.premierleague.com/api/fixtures/
- Entry summaries: https://fantasy.premierleague.com/api/entry/8522487/ and https://fantasy.premierleague.com/api/entry/7337262/
- Official histories: https://fantasy.premierleague.com/api/entry/8522487/history/ and https://fantasy.premierleague.com/api/entry/7337262/history/
- Official transfer histories: https://fantasy.premierleague.com/api/entry/8522487/transfers/ and https://fantasy.premierleague.com/api/entry/7337262/transfers/
- Liverpool Isak update, published 27 September 2026: https://www.liverpoolfc.com/news/alexander-isak-return-international-duty
- Arsenal international roundup, published 25 September 2026: https://www.arsenal.com/news/tzolis-scores-for-greece-as-odegaard-shines-a20O07e2juvT
- Manchester City England/Croatia roundup, published 26 September 2026: https://www.mancity.com/news/mens/england-spain-croatia-czechia-63926047

