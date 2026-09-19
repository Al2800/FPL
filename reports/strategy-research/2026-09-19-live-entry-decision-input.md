# Live-entry decision input - 2026-09-19

**Status:** GW5 locked; partial outcome review and GW6 planning input  
**Observed at:** 2026-09-19T07:47:28Z  
**Next deadline:** 2026-10-10T10:00:00Z (11:00 BST)  
**Entries:** 8522487 and 7337262  
**Governing method:** `docs/plan.md`; official FPL entry data is authoritative for squad, picks, transfers and scoring; official club sources are authoritative for availability evidence

## Executive conclusion

No transfer or chip action is available or justified today. GW5 is in progress and both entries are correctly locked with the transfers and selections entered on 18 September.

The material new evidence is:

1. Official FPL now exposes both completed GW5 transfers and locked picks.
2. Brentford beat Chelsea 3-0 on 18 September. Igor Thiago scored and returned five FPL points. Palmer and Rogers returned two points each.
3. João Pedro recorded zero minutes. On entry 7337262 he remains in the XI but first substitute Truffert is eligible to replace him after the Gameweek if formation permits and Truffert plays. This is the intended downside protection.
4. The three-week international break means no early GW6 move should be made. João Pedro's medical severity is still not established by a direct Chelsea medical statement.
5. Draft PR #92 again uses the wrong squad for entry 8522487. Its Kinsky, Cherki and Wissa recommendations must not be applied to either live entry.

## Official locked state

### Entry 8522487 - Haaland structure

- GW5 transfer: Luke Shaw to Timothy Castagne
- Transfer cost: 0 points
- Deadline bank: £0.2m
- Deadline total value: £99.6m (last authenticated squad value £99.4m plus £0.2m bank)
- Active chip: none
- Live GW5 points at observation: 5
- Live total: 246
- Live overall rank: approximately 5,298,521

Locked XI:

Verbruggen  
Van Hecke, Mitchell, Castagne  
B. Fernandes, Gibbs-White, E. Le Fée, Dewsbury-Hall, Xhaka  
Thiago, Haaland

Captain: Haaland  
Vice-captain: B. Fernandes  
Bench: Dubravka; 1 João Pedro, 2 Diop, 3 van Ewijk

The public transfer endpoint records Castagne in for Shaw at 2026-09-18T16:02:06Z. The live five points are Thiago's goal return. All other starters were unplayed at the observation cutoff.

### Entry 7337262 - no-Haaland structure

- GW5 transfer: Ian Maatsen to Timothy Castagne
- Transfer cost: 0 points
- Deadline bank: £0.0m
- Deadline total value: £99.8m (squad value £99.8m plus £0.0m bank)
- Active chip: none
- Live GW5 points at observation: 6
- Live total: 254
- Live overall rank: approximately 4,568,271

Locked XI:

Raya  
Gabriel, Castagne, Guéhi  
Rogers, Palmer, Semenyo, Rice, Anderson  
João Pedro, Isak

Captain: Palmer  
Vice-captain: Rogers  
Bench: Verbruggen; 1 Truffert, 2 Shaw, 3 Obi

The public transfer endpoint records Castagne in for Maatsen at 2026-09-18T15:47:18Z. Palmer scored two points, doubled to four, and Rogers scored two. João Pedro recorded zero minutes, leaving the first-substitution route open.

## Current manager-state quality

Public post-deadline data now verifies the completed transfers, locked XI, captaincy, bench order, bank and deadline team value.

GW6 manager state remains **degraded** because public endpoints do not expose:

- exact free transfers currently available for GW6;
- pending transfers made after the GW5 deadline;
- individual purchase and selling prices;
- authenticated chip inventory state beyond public chip history.

Last authenticated post-transfer observations on 18 September were:

- entry 8522487: two free transfers remaining and £0.2m bank;
- entry 7337262: zero free transfers remaining and £0.0m bank.

These are valid observations from that time, not assumptions about the eventual GW6 transfer allowance. The authenticated transfer page must be checked again before any GW6 action.

## Accepted official evidence

| Claim | published_at | observed_at | Source and consequence |
|---|---|---|---|
| Brentford beat Chelsea 3-0; Thiago scored; Palmer and Rogers started; João Pedro was absent from the matchday squad | 2026-09-18 | 2026-09-19T07:47:28Z | Brentford official match report. Confirms the realised minutes and role outcome without establishing João Pedro's injury duration. |
| Thiago: 90 minutes, one goal, 0.72 xG, 0.03 xA, five FPL points | live after 2026-09-18 match | 2026-09-19T07:47:28Z | Official FPL event-live endpoint. Positive process and outcome; no reason to sell before GW6. |
| Palmer: 90 minutes, 0.13 xG, 0.18 xA, two points | live after 2026-09-18 match | 2026-09-19T07:47:28Z | Official FPL event-live endpoint. One-match blank does not overturn the GW6 Bournemouth home captain case. |
| Rogers: 90 minutes, 0.33 xG, 0.07 xA, two points | live after 2026-09-18 match | 2026-09-19T07:47:28Z | Official FPL event-live endpoint. Underlying involvement was materially better than the points return. |
| João Pedro: zero minutes; FPL still shows doubtful, 75%, with news timestamp 2026-09-16T19:00:09Z | live / status added 2026-09-16 | 2026-09-19T07:47:28Z | Official FPL. Hold pending a fresh Chelsea update; status field is now stale relative to the omission. |
| Shaw remains doubtful, 50%, news timestamp 2026-09-11T13:00:09Z | 2026-09-11 | 2026-09-19T07:47:28Z | Official FPL. Relevant only to entry 7337262, where he is bench depth. |
| Mitchell started Palace's European fixture; Porro was declared available; Elanga and Wilson were ruled out | 2026-09-17 to 2026-09-18 | 2026-09-19T07:03:02Z | Official club reports admitted by the 19 September evidence review. Mitchell hold is supported; Porro remains only a comparison candidate. |

## Rejected or unresolved claims

- PR #92's Kinsky, Cherki and Wissa squad is not entry 8522487. Official FPL picks and transfer history falsify that reconstruction.
- PR #92's statement that João Pedro's absence is only community evidence is now outdated for the minutes outcome. The official Brentford match report and official FPL live data confirm zero minutes. The injury diagnosis and duration remain unresolved.
- No exact João Pedro return date is accepted. Reports of a roughly three-and-a-half-week knee recovery remain unverified community or media claims.
- No conclusion should be drawn from partial live ranks. Only one GW5 fixture had finished at the observation cutoff.
- The official `ep_next` values observed after the GW5 deadline are not valid pre-deadline GW5 forecasts and must not be used to score yesterday's decision.
- Elanga, Wilson, Doku and Porro news does not create a transfer action for either live squad today.

## Changes since the 18 September update

- Both proposed transfers are now verified as completed at zero cost.
- Both XIs, captains, vice-captains and bench orders are verified from locked official picks.
- João Pedro did not make Chelsea's matchday squad. The no-Haaland team therefore avoided the short-cameo failure mode; Truffert remains the intended first substitute.
- Thiago converted 0.72 xG into a goal. Retaining him rather than spending another transfer has produced an immediate five-point return, although the Gameweek is incomplete.
- Palmer captaincy returned four points after doubling. This is a realised downside, not evidence that the captain process was invalid.
- No official evidence warrants an early GW6 transfer.

## Rolling GW6-GW9 plan

### GW6, deadline 10 October at 11:00 BST

Default action: wait through the international break. Do not transfer early.

Haaland entry:
- provisional captain pool: B. Fernandes at home to Spurs, João Pedro at home to Bournemouth if officially fit, then Haaland away to Liverpool;
- retain Thiago after the goal and strong 0.75 xGI match;
- Castagne has Ipswich away;
- reassess only if international duty or club updates produce multiple unavailable starters.

No-Haaland entry:
- provisional captain: Palmer at home to Bournemouth;
- provisional vice-captain: Rogers;
- João Pedro returns to the XI only with credible training or manager evidence;
- a legal 4-5-1 remains available if João Pedro is not ready, so his absence alone does not justify a Wildcard;
- Shaw is a transfer-out candidate only if he remains unavailable and there is a clearly superior multiweek replacement.

### GW7

- Haaland at home to Ipswich is the leading captaincy anchor.
- Triple Captain should be compared with later first-half home fixtures using updated expected minutes, opposition strength and rotation evidence. It is a shortlist, not a commitment.
- The no-Haaland route to Haaland must be evaluated using authenticated selling prices and transfer count. Do not pre-commit during the international break.

### GW8-GW9

- Preserve flexibility around Chelsea's Spurs and Manchester United fixtures, Arsenal's strong GW8 home fixture, and City's GW9 Brighton home fixture.
- Review whether the two squads should continue to diverge structurally after a six-to-eight-Gameweek sample. Do not force convergence merely because one captain outcome wins a single week.
- Wildcard only if at least three structural problems remain after fresh availability and minutes evidence. Current public state does not meet that threshold.

## Source freshness

- Official FPL bootstrap, entry, picks, transfers, history and live endpoints: observed 2026-09-19T07:47:28Z.
- Brentford official match report: published 2026-09-18; observed 2026-09-19.
- Repository official-news discovery and evidence review: observed 2026-09-19T07:03:02Z.
- Next decision deadline: 2026-10-10T10:00:00Z.

## Sources

- Official FPL bootstrap: https://fantasy.premierleague.com/api/bootstrap-static/
- Official FPL fixtures: https://fantasy.premierleague.com/api/fixtures/
- Entry 8522487: https://fantasy.premierleague.com/api/entry/8522487/
- Entry 7337262: https://fantasy.premierleague.com/api/entry/7337262/
- Entry 8522487 GW5 picks: https://fantasy.premierleague.com/api/entry/8522487/event/5/picks/
- Entry 7337262 GW5 picks: https://fantasy.premierleague.com/api/entry/7337262/event/5/picks/
- Official GW5 live data: https://fantasy.premierleague.com/api/event/5/live/
- Brentford official match report: https://www.brentfordfc.com/en/news/article/match-reports-brentford-3-chelsea-0-premier-league-jaidon-anthony-igor-thiago-fabio-carvalho
- Draft PR: https://github.com/Al2800/FPL/pull/92
