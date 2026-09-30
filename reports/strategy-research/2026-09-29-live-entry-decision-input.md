# Live-entry decision input — 2026-09-29

- observed_at: 2026-09-29T07:38:55Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for squads, completed picks, transfers and scoring; official club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is a **material monitoring update but no transfer or chip action today**. Manchester United's official 28 September update says owned midfielder Bruno Fernandes missed Portugal's match against Norway because of a fitness problem. Portugal hope he can return against Denmark on 1 October. Official FPL still lists Bruno as available and unflagged, so this is a workload/fitness monitor rather than a confirmed GW6 absence.

The Haaland-team captain remains **Haaland**. Until Bruno demonstrates normal involvement, **Mitchell becomes the provisional vice-captain**; restore Bruno as vice-captain after an international appearance without setback or a normal-minutes club clearance.

The no-Haaland squad remains unchanged at five doubtful players plus Obi unavailable. Liverpool's new Gakpo ankle injury is relevant to the Liverpool-Manchester City environment and transfer-candidate pool, but Gakpo is not owned.

The automated strategy report's Kinsky/Cherki/Wissa squad and exact-one-free-transfer assertion remain invalid for entries 8522487 and 7337262.

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

Public endpoints do not expose the current free-transfer balance, pending transfers, purchase prices or selling prices. Manager state remains degraded.

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

No owned-player price changed since 28 September.

## Availability and source freshness

| player | official state | chance | published / news timestamp | observed_at | change / implication |
|---|---|---:|---|---|---|
| Bruno Fernandes | Man Utd says fitness problem; Portugal hope for 1 Oct return | FPL unflagged | Man Utd 2026-09-28 | 2026-09-29T07:38:55Z | **new owned-player monitor**; remains in XI, provisional VC removed |
| Isak | thigh injury | 75% | FPL 2026-09-27T10:30:09Z; Liverpool 2026-09-27T09:38:00Z | 2026-09-29T07:38:55Z | unchanged; club assessment pending |
| Semenyo | ankle injury | 75% | 2026-09-24T12:00:09Z | 2026-09-29T07:38:55Z | unchanged; severity unresolved |
| Palmer | muscular injury | 75% | 2026-09-21T13:00:09Z | 2026-09-29T07:38:55Z | unchanged; no Chelsea GW6 return timeline |
| Rice | unspecified injury | 75% | 2026-09-21T13:00:08Z | 2026-09-29T07:38:55Z | unchanged; no Arsenal GW6 return timeline |
| João Pedro | knee injury | 75% | 2026-09-16T19:00:09Z | 2026-09-29T07:38:55Z | unchanged; stalest material flag |
| van Ewijk | hamstring injury | 75% | 2026-09-19T16:00:09Z | 2026-09-29T07:38:55Z | unchanged; Haaland-team bench risk |
| Obi | season loan | 0% | 2026-09-14T16:12:42Z | 2026-09-29T07:38:55Z | unavailable |
| all other owned players | available | 100% or unflagged | bootstrap current | 2026-09-29T07:38:55Z | no new issue |

Official FPL's mutable GW6 estimates now include Haaland 8.0, Mitchell 7.7, Van Hecke 7.3, Bruno 7.2, Semenyo 6.5, Guéhi/Raya 6.0, Isak 5.8 and Rogers 5.2. These are directional estimates, not medical evidence.

The 29 September repository model run admitted two official claims:

- Gakpo doubtful: Liverpool confirms an ankle injury, Netherlands withdrawal and club assessment before GW6.
- Havertz doubtful reinforcement: Arsenal confirms he was omitted after his earlier 30-minute substitution; no diagnosis supplied.

Neither is owned. The evidence-ledger tip changed from `303520f8…` to `f6ff62e7…`.

The repository run could not recover Manchester United's English page, but the official Korean-language page and indexed official result establish the Bruno fitness concern. This derived report records it as accepted official evidence without adding an unverified diagnosis or duration to the governed ledger.

No new official Chelsea, Arsenal, Bournemouth/Ghana or Liverpool assessment resolves Palmer, João Pedro, Rice, Semenyo or Isak.

## Community challenge review

The 28 September X digest was reviewed. It surfaced Gakpo, Isak and Dorgu 75% flags before the club originals, plus a conflicting unsupported claim that “Isak is fine”. Liverpool's official statement and the official FPL flag override that community reassurance.

Barry price-rise and Wildcard-six discussion do not affect the owned squads today. Community opposition to Haaland captaincy at Liverpool is a challenge input; it does not outweigh Haaland's current 8.0 official estimate and the absence of a fully fit superior captain in the Haaland squad.

Rejected community implications: Isak is already cleared; Bruno is ruled out of GW6; activate Wildcard immediately; buy Gakpo, Havertz or Barry solely from chatter or price movement.

## Provisional GW6 decisions

### Entry 8522487

Verbruggen
Van Hecke; Mitchell; Castagne
B.Fernandes; Gibbs-White; E.Le Fée; Dewsbury-Hall; Xhaka
Thiago; Haaland

- Captain: **Haaland**
- Provisional vice-captain while Bruno is being monitored: **Mitchell**
- Restore **Bruno vice-captain** after normal involvement without setback.
- Bench: Dubravka; 1 Diop; 2 João Pedro; 3 van Ewijk
- If João Pedro is cleared for normal minutes, start him and bench Xhaka.
- If Bruno remains unavailable near the deadline, start João Pedro if cleared; otherwise promote Diop and preserve a legal formation.
- No transfer or chip today.

### Entry 7337262

If all five doubtful players recover:

Raya
Gabriel; Castagne; Guéhi
Rogers; Palmer; Semenyo; Rice; Anderson
João Pedro; Isak

- While Palmer is doubtful: captain **Rogers**, vice-captain **Raya**.
- If Palmer is cleared for normal minutes: captain **Palmer**, vice-captain **Rogers**.
- Isak requires a normal-minutes clearance before being trusted in the XI; do not captain him against Manchester City.
- Bench: Verbruggen; 1 Shaw; 2 Truffert; 3 Obi.
- Shaw and then Truffert cover the first two outfield absences.
- If three or more of Palmer, Rice, Semenyo, João Pedro and Isak remain unavailable near the deadline, run the authenticated free-transfer-versus-hits-versus-Wildcard comparison.
- No transfer or chip today.

## Rolling GW6–GW9 plan

- GW6: preserve information. Monitor Bruno's proposed 1 October return, Liverpool assessments for Isak/Gakpo, remaining international minutes and the final club press conferences.
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
- Manchester United fitness update, published 28 September 2026: https://www.manutd.com/ko/news/latest-on-dorgu-and-fernandes-fitness-28-sep-2026
- Liverpool Gakpo update, published 28 September 2026: https://www.liverpoolfc.com/news/cody-gakpo-withdraws-international-duty
- Liverpool Isak update, published 27 September 2026: https://www.liverpoolfc.com/news/alexander-isak-return-international-duty
- Arsenal Havertz reinforcement, published 28 September 2026: https://www.arsenal.com/news/tzolis-and-timber-pick-up-big-victories-alxEV4A7JZ4n
