# Live-entry decision input — 2026-09-30

- observed_at: 2026-09-30T07:41:44Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for squads, completed picks, transfers and scoring; official club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **no transfer or chip action today**. Overnight Lane A admitted five Manchester City IB `available` / `started_match` claims (Haaland Norway start+goal; Donnarumma Italy; Gvardiol and Kovačić Croatia starts; Anderson England start). None change owned XI structure today; Haaland’s tip supports keeping him as **captain** on the Haaland arm.

Bruno Fernandes remains the key owned **monitor**: the official Man Utd update of 28 September said he missed Portugal v Norway and Portugal hoped for a 1 October return. Official FPL still lists Bruno as available (`status=a`) and unflagged, but soft `ep_next` **2.0** is treated as form noise during the IB rather than a medical flag. Keep Bruno in the XI; **Mitchell remains provisional vice-captain** until Bruno demonstrates normal involvement. A 30 September media report that Bruno trained fully is not admitted because no current Man Utd or Portugal original was recovered.

The no-Haaland squad remains unchanged at five doubtful players plus Obi unavailable. Retained Gakpo/Isak doubtful tips matter for the LIV–MCI environment and transfer-candidate pool, not for owned XI moves today.

The automated strategy report’s Kinsky/Cherki/Wissa reconstructed 15 and exact-one-free-transfer assertion remain invalid for entries 8522487 and 7337262.

## Official entry state

GW5 is finished and data checked. The overall page-20 sample was re-polled at 2026-09-30T07:41:44Z; rank 994 remains on **414**, so 414 remains the working top-1,000 boundary.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,109 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,593 | 123 |

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

No owned-player price changed since 29 September.

## Availability and source freshness

| player | official state | chance | published / news timestamp | observed_at | change / implication |
|---|---|---:|---|---|---|
| Bruno Fernandes | prior Man Utd fitness monitor; FPL unflagged `a` | FPL unflagged | Man Utd 2026-09-28 | 2026-09-30T07:41:44Z | unchanged monitor; provisional VC still Mitchell |
| Haaland | City confirm Norway start+goal | FPL `a` | City 2026-09-27T20:49:04Z; claim `model:2cb641ec…` | 2026-09-30T07:41:44Z | **new ledger available tip**; supports Haaland (C) on this arm |
| Anderson (owned 7337262) | City confirm England start | FPL `a` | City 2026-09-29T20:51:29Z; claim `model:89750319…` | 2026-09-30T07:41:44Z | owned MID fitness corroboration |
| Isak | thigh injury | 75% | FPL 2026-09-27T10:30:09Z; Liverpool 2026-09-27T09:38:00Z | 2026-09-30T07:41:44Z | unchanged; club assessment pending |
| Semenyo | ankle injury | 75% | FPL 2026-09-24T12:00:09Z | 2026-09-30T07:41:44Z | unchanged; severity unresolved |
| Palmer | muscular injury | 75% | FPL 2026-09-21T13:00:09Z | 2026-09-30T07:41:44Z | unchanged |
| Rice | unspecified injury | 75% | FPL 2026-09-21T13:00:08Z | 2026-09-30T07:41:44Z | unchanged |
| João Pedro | knee injury | 75% | FPL 2026-09-16T19:00:09Z | 2026-09-30T07:41:44Z | unchanged; no Chelsea timed original |
| van Ewijk | hamstring injury | 75% | FPL 2026-09-19T16:00:09Z | 2026-09-30T07:41:44Z | unchanged; Haaland-team bench risk |
| Obi | season loan | 0% | FPL 2026-09-14T16:12:42Z | 2026-09-30T07:41:44Z | unavailable |
| all other owned players | available | 100% or unflagged | bootstrap current | 2026-09-30T07:41:44Z | no new issue |

Official FPL’s mutable GW6 estimates now include Haaland **8.0**, Mitchell **7.7**, Van Hecke **7.3**, Semenyo **6.5**, Guéhi/Raya **6.0**, Isak **5.8**, Rogers **5.3**, Bruno **2.0**. These are directional estimates, not medical evidence.

The 30 September repository model run admitted five official claims (all City IB `available`):

- Haaland `model:2cb641ec…`
- Donnarumma `model:7ba2e01b…`
- Gvardiol `model:19c3752c…`
- Kovačić `model:0ae3242d…`
- Anderson `model:89750319…`

Ledger tip: `f6ff62e7…` → `fdc0e882…`. Retained prior Gakpo/Havertz/Isak doubtful tips. Gakpo/Havertz/Donnarumma/Gvardiol/Kovačić are not owned.

## Community challenge review

The 29 September X digest was reviewed for noise only. Community Haaland-always-captain takes for Anfield are noted; on the Haaland arm, Haaland remains captain because the owned alternative (Bruno) is the fitness monitor. Community Pedro sells and Groß/Schade chase do not force owned moves today.

Rejected community implications: Isak is already cleared; Bruno is ruled out of GW6; Bruno's reported full training is already an official clearance; activate Wildcard immediately; buy Gakpo or Havertz solely from chatter.

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
- Anderson’s new England-start tip (`model:89750319…`) is a positive owned MID signal only.

## Rolling GW6–GW9 plan

- GW6: preserve information. Monitor Bruno’s proposed 1 October Portugal return, Liverpool assessments for Isak/Gakpo, remaining international minutes and the final club press conferences.
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
- Manchester United fitness update, published 28 September 2026: https://www.manutd.com/en/news/latest-on-dorgu-and-fernandes-fitness-28-sep-2026
- City Haaland Norway report: https://www.mancity.com/news/mens/norway-portugal-nations-league-match-report-63926139
- City England/Croatia roundup: https://www.mancity.com/news/mens/marc-guehi-elliot-anderson-england-roundup-63926312
- City Italy/France roundup: https://www.mancity.com/news/mens/man-city-international-roundup-donnarumma-cherki-63926225
- Liverpool Gakpo / Isak pages (prior admits retained)
- Arsenal Havertz reinforcement (prior admit retained)
