# Live-entry decision input — 2026-10-01

- observed_at: 2026-10-01T07:25:25Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for squads, completed picks, transfers and scoring; official club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded

## Executive decision

There is **a material owned-player availability change, but no transfer or chip action today**. The repository model proposed zero new claims and its governed ledger remains `fdc0e882…`; however, the live-entry verification found a new official Netherlands-association original concerning Van Hecke and records it in this derived review without altering the ledger.

Material change for the Haaland arm: **Van Hecke** is now `d` / foot injury **75%** (`news_added` 2026-09-30T16:00:09Z). OnsOranje/KNVB reported on 30 September at 14:30 local that he sustained the foot injury against Serbia, withdrew during the Netherlands' final training session and returned to Tottenham; no replacement was called up. This confirms a real injury but gives no GW6 prognosis. **Do not spend a FT on Bogle into LEE–ARS (A)** solely on this evidence. Provisional GW6 XI change: start **Diop** ahead of Van Hecke; keep Mitchell.

Haaland remains **captain** on entry 8522487. Bruno remains the key owned **monitor**: FPL still lists him available and the Premier League's 29 September roundup expected him to be fit for Portugal v Denmark, but normal involvement has not yet been demonstrated. **Mitchell remains provisional vice-captain** until that happens.

The no-Haaland squad remains unchanged at five doubtful players plus Obi unavailable. Retained Gakpo/Isak doubtful tips matter for the LIV–MCI environment and transfer-candidate pool, not for owned XI moves today.

The automated strategy report’s Kinsky/Cherki/Wissa reconstructed 15 remains advisory-only and is **not** the owned squad for either entry.

## Official entry state

GW5 is finished and data checked. The overall page-20 sample was re-polled at 2026-10-01T07:25:25Z; rank 995 remains on **414**, so 414 remains the working top-1,000 boundary.

| entry | arm | GW5 | total | current OR | gap to 414 |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | 5,200,089 | 122 |
| 7337262 | no Haaland | 43 | 291 | 5,320,573 | 123 |

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
- DEF: Van Hecke £4.9m (`d` foot 75%); Mitchell £4.5m; Castagne £4.5m; Diop £4.0m; van Ewijk £4.0m (`d` hamstring 75%)
- MID: B.Fernandes £11.9m; Gibbs-White £8.0m; E.Le Fée £5.7m; Dewsbury-Hall £6.6m; Xhaka £5.5m
- FWD: Thiago £7.8m; Haaland £15.6m; João Pedro £7.7m (`d` knee 75%)

### Entry 7337262

- GKP: Raya £6.1m; Verbruggen £4.5m
- DEF: Gabriel £8.0m; Guéhi £6.0m; Castagne £4.5m; Truffert £5.4m; Shaw £4.3m
- MID: Palmer £9.7m (`d` muscular 75%); Rogers £7.7m; Semenyo £8.4m (`d` ankle 75%); Rice £7.4m (`d` 75%); Anderson £6.3m
- FWD: Isak £9.1m (`d` thigh 75%); João Pedro £7.7m (`d` knee 75%); Obi £4.5m (`u` loan)

## Availability and source freshness

| player | official state | chance | published / news timestamp | observed_at | change / implication |
|---|---|---:|---|---|---|
| Van Hecke | foot injury; withdrew from Netherlands camp and returned to Spurs | 75% | KNVB 2026-09-30 14:30 local; FPL `news_added` 2026-09-30T16:00:09Z | 2026-10-01T07:25:25Z | **new confirmed owned injury**; bench behind Diop; duration unresolved |
| Bruno Fernandes | FPL unflagged `a`; expected fit for Portugal v Denmark | FPL unflagged | Man Utd 2026-09-28; Premier League 2026-09-29 | 2026-10-01T07:25:25Z | keep in XI; Mitchell provisional VC until normal involvement |
| Haaland | City Norway tip retained | FPL `a` | City tip `model:2cb641ec…` | 2026-10-01T07:25:25Z | keep (C) on Haaland arm |
| Anderson (owned 7337262) | City England tip retained | FPL `a` | `model:89750319…` | 2026-10-01T07:25:25Z | owned MID fitness corroboration |
| Isak | thigh injury | 75% | Liverpool 2026-09-27; FPL `news_added` 2026-09-27T10:30:09Z | 2026-10-01T07:25:25Z | unchanged; not a captain candidate |
| Semenyo | ankle injury | 75% | FPL `news_added` 2026-09-24T12:00:09Z | 2026-10-01T07:25:25Z | unchanged |
| Palmer | muscular injury | 75% | FPL `news_added` 2026-09-21T13:00:09Z | 2026-10-01T07:25:25Z | unchanged |
| Rice | unspecified injury | 75% | FPL `news_added` 2026-09-21T13:00:08Z | 2026-10-01T07:25:25Z | unchanged |
| João Pedro | knee injury | 75% | FPL `news_added` 2026-09-16T19:00:09Z; no Chelsea timed original | 2026-10-01T07:25:25Z | unchanged; community specialist-treatment report remains unverified |
| van Ewijk | hamstring injury | 75% | FPL `news_added` 2026-09-19T16:00:09Z | 2026-10-01T07:25:25Z | unchanged; Haaland-team bench risk |
| Obi | season loan | 0% | FPL `news_added` 2026-09-14T16:12:42Z | 2026-10-01T07:25:25Z | unavailable |
| all other owned players | available | 100% or unflagged | bootstrap current | 2026-10-01T07:25:25Z | no new issue |

Official FPL’s mutable GW6 estimates still include Haaland **8.0**, Mitchell **7.7**, Gvardiol **7.7**, Van Hecke **5.5** (down vs prior 7.3 print while flagged), Semenyo **6.5**, Guéhi/Raya **6.0**, Isak **5.8**, Bruno **2.0**. These are directional estimates, not medical evidence.

Today’s model run proposed **0** candidates; ledger tip unchanged `fdc0e882…`.

## Community challenge review

The 30 September X digest was reviewed as a challenge source. It surfaced João Pedro specialist-knee-treatment reporting, Bogle and Vuskovic defender discussion, and Wildcard-six drafts. None is an official availability original. Community Bogle-chase and Haaland-always-captain takes are noted; the owned Haaland arm keeps Haaland (C) because Bruno has not yet demonstrated normal involvement. Rejected: force Van Hecke→Bogle into ARS (A) today; activate Wildcard for one confirmed but un-timed DEF injury; treat the João Pedro specialist-treatment thread as a club prognosis.

## Provisional GW6 decisions

### Entry 8522487

Verbruggen  
Mitchell; Castagne; Diop  
B.Fernandes; Gibbs-White; E.Le Fée; Dewsbury-Hall; Xhaka  
Thiago; Haaland  

- Captain / vice: Haaland / Mitchell
- Bench (1→4): Dubravka; João Pedro; Van Hecke; van Ewijk
- Transfers / chips: none today; reassess Van Hecke after Spurs pressers; do not chase Bogle into ARS (A)

### Entry 7337262

If all five doubtful players recover:

Raya  
Gabriel; Guéhi; Castagne  
Rogers; Palmer; Semenyo; Rice; Anderson
João Pedro; Isak

- While Palmer is doubtful: captain **Rogers**, vice-captain **Raya**.
- If Palmer is cleared for normal minutes: captain **Palmer**, vice-captain **Rogers**.
- Isak requires a normal-minutes clearance before being trusted in the XI; do not captain a flagged Isak against Manchester City.
- Bench (1→4): Verbruggen; Shaw; Truffert; Obi.
- Transfers / chips: none today; if at least three of Palmer, Semenyo, Rice, João Pedro and Isak remain unavailable near the deadline, run the authenticated free-transfer-versus-hits-versus-Wildcard comparison.

## Rolling GW6–GW9 plan

- GW6: preserve information. Monitor Van Hecke's Spurs assessment, Bruno's Portugal involvement, Liverpool assessments for Isak/Gakpo and final club press conferences.
- GW7: City host Ipswich, making Haaland the probable captain anchor. The no-Haaland team needs an authenticated route-to-Haaland comparison if it remains structurally weak.
- GW8: Chelsea host Spurs and United host Bournemouth. Retain Palmer/Bruno flexibility rather than pre-booking sales.
- GW9: City host Brighton and Chelsea host United. Reassess premium structure with post-break minutes and injury outcomes.
- Wildcard threshold: at least three structural problems remain, fewer than eleven credible starters can be produced without excessive hits, or an authenticated multiweek Wildcard draft materially dominates a free-transfer repair.
- No Free Hit, Bench Boost or Triple Captain case currently clears the methodology threshold.

## Accepted, rejected and unresolved claims

- Accepted: Van Hecke sustained a foot injury, withdrew from the Netherlands camp and returned to Tottenham.
- Accepted: the official FPL flag is 75%; it does not establish a GW6 absence or recovery date.
- Unresolved: Van Hecke's diagnosis, severity and GW6 minutes; normal minutes for Bruno; return dates for Palmer, Rice, Semenyo, João Pedro and Isak.
- Rejected: Isak as current fallback captain; an immediate Van Hecke transfer; immediate Wildcard activation; João Pedro specialist treatment as official Chelsea evidence.

## Manager-state degradation

Before the final GW6 recommendation, manually confirm on both authenticated transfer pages:

1. exact free-transfer count;
2. current bank and team value;
3. purchase and selling prices for all candidate movers;
4. whether any pending transfer exists;
5. chip availability and intended chip state.

## Sources

- Official FPL bootstrap: https://fantasy.premierleague.com/api/bootstrap-static/
- Official fixtures: https://fantasy.premierleague.com/api/fixtures/
- Entry summaries: https://fantasy.premierleague.com/api/entry/8522487/ and https://fantasy.premierleague.com/api/entry/7337262/
- Official histories: https://fantasy.premierleague.com/api/entry/8522487/history/ and https://fantasy.premierleague.com/api/entry/7337262/history/
- KNVB/OnsOranje Van Hecke update, published 30 September 2026: https://www.onsoranje.nl/nieuws/nederlands-elftal-mannen/82735/van-hecke-haakt-af-bij-oranje
- Premier League international roundup, published 29 September 2026: https://www.premierleague.com/en/news/4727187/internationals-mixed-fortunes-for-premier-league-forwards
- Liverpool Isak update, published 27 September 2026: https://www.liverpoolfc.com/news/alexander-isak-return-international-duty

## Falsifiers before next run

- Spurs confirm multi-week Van Hecke absence
- Man Utd / FPL flags Bruno out of GW6
- Chelsea timed Pedro multi-week absence
- Owned 7337262 flags clear or worsen into confirmed outs
- Price changes force a bank/value emergency

## Host handoff

- Account writes: false
- Owner approval still required
- Advisory reconstructed 15 is not either owned entry
