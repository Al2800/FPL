# Live GW6/GW7 decision input — 12 October 2026

- official FPL observed_at: 2026-10-12T07:38:00Z–2026-10-12T07:40:56Z
- official-news review observed_at: 2026-10-12T07:41:00Z–2026-10-12T07:48:00Z
- GW6 state: live and provisional; Coventry City v Newcastle United remains at 2026-10-12T19:00:00Z
- next_deadline: 2026-10-17T10:00:00Z / 11:00 BST (GW7)
- entries: 8522487 (Haaland), 7337262 (no Haaland)
- method: `AGENTS.md`, `docs/plan.md`, point-in-time official evidence, hold baseline and rolling four-Gameweek review
- account writes: false
- manager state: GW6 selections are public and verifiable; **GW7 private state remains live_faithful_degraded**

## Material update

Sunday's matches have made the GW6 comparison nearly complete. The no-Haaland entry is projected to score two more GW6 points and remain one point ahead overall after automatic substitutions. Tonight's Coventry–Newcastle match should not alter either entry's score: van Ewijk is third bench for 8522487, while Diop already supplies the one legal defender substitution required for Castagne.

| Entry | Arm | Official live GW6 | Expected autosub | Projected GW6 | Projected total | Current raw OR | Gap to live rank-1,000 score (489) |
|---|---|---:|---:|---:|---:|---:|---:|
| 8522487 | Haaland | 62 | +2, Diop for Castagne | 64 | 356 | 4,561,288 | 133 |
| 7337262 | no Haaland | 64 | +2, Truffert and Shaw for Castagne and Isak | 66 | 357 | 4,502,787 | 132 |

The official live average is 54. The projected scores are therefore ten and twelve points above average. Automatic substitutions, ranks and bonus remain provisional until the Gameweek finishes and is data checked.

## Sunday outcome and captain comparison

| Player | Minutes | Raw points | Decision observation |
|---|---:|---:|---|
| Dewsbury-Hall | 90 | 13 | Goal, assist and three bonus. The GW4 Wilson replacement supplied the largest Sunday return. |
| Haaland | 79 | 6 | Scored at Liverpool; captain produced 12. The strong process case did not beat Palmer this week. |
| Mitchell | 90 | 4 | Completed the match and reached the defensive-contribution threshold. |
| Gibbs-White | 90 | 2 | Blank; retain provisionally, but Arsenal in GW7 is a weak immediate fixture. |
| Guéhi | 90 | 6 | Manchester City clean sheet at Liverpool. Stronger GW7 fixture against Ipswich. |
| Anderson | 90 | 6 | One assist. Remains a credible fifth midfielder rather than an urgent sale. |
| Semenyo | 90 | 3 | Blank at Liverpool; his official status has nevertheless returned to available. |

Palmer's 16 captain points beat Haaland's 12 by four. That is an outcome difference, not sufficient evidence that the Haaland decision was methodologically wrong. Palmer had only just returned from a muscular issue, whereas Haaland was officially fit and started a high-upside fixture. The result belongs in the forecast calibration record rather than prompting a retrospective rule change.

## Ex-ante versus realised

The official pre-deadline `ep_next` field supplied an uncalibrated comparison baseline:

| Entry/selection | Pre-deadline baseline | Projected realised | Difference |
|---|---:|---:|---:|
| 8522487 recommended/actual | 57.5 | 64 | +6.5 |
| 7337262 actual Isak selection | 52.6 | 66 | +13.4 |
| 7337262 recommended Shaw selection | 53.6 | 66 | +12.4 |

João Pedro over Xhaka gained ten realised points for 8522487. The incomplete Shaw-for-Isak execution on 7337262 remains an adherence defect but is points-neutral: Castagne's zero minutes cause both Truffert (-1) and Shaw (3) to enter in either path. The model review should preserve both facts—no realised loss and a failed save-verification step.

## Public financial, transfer and chip state

| Entry | GW6 deadline value | GW6 deadline bank | GW6 transfers | GW6 cost | Chips used through GW6 |
|---|---:|---:|---:|---:|---|
| 8522487 | £99.4m | £0.2m | 0 | 0 | none |
| 7337262 | £99.7m | £0.0m | 0 | 0 | none |

These are public deadline snapshots. Current free transfers, current bank, pending GW7 moves, purchase prices and selling prices are private and must not be inferred. Before any move, both authenticated transfer pages must expose those fields directly.

Completed transfer history remains:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, Bruno Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

## Current owned prices and availability

`news_added` is the official feed timestamp carried by the player record; it is not guaranteed to be the latest status-change time. A `null` chance is unspecified, not 100%. The official `ep_next` field is a mutable discovery input, not a sealed laboratory forecast.

### 8522487 — Haaland

| Player | Price | Status / chance next | news_added UTC | GW6 points | ep_next |
|---|---:|---|---|---:|---:|
| Verbruggen | £4.5m | available / null | null | 9 | 7.7 |
| Van Hecke | £4.9m | available / 100 | 2026-09-30T16:00:09Z | 3 | 5.7 |
| Mitchell | £4.5m | available / null | null | 4 | 4.0 |
| Castagne | £4.5m | available / null | null | 0 | 2.3 |
| Diop | £4.0m | available / null | null | 2 | 2.3 |
| van Ewijk | £4.0m | doubtful / 75 | 2026-09-19T16:00:09Z | not played | 0.0 |
| Bruno Fernandes | £11.9m | available / null | null | 1 | 1.7 |
| Gibbs-White | £8.0m | available / 100 | 2026-08-24T15:30:08Z | 2 | 4.0 |
| Le Fée | £5.7m | available / null | null | 2 | 2.3 |
| Dewsbury-Hall | £6.6m | available / null | null | 13 | 6.0 |
| Xhaka | £5.4m | available / null | null | 2 | 1.7 |
| João Pedro | £7.8m | available / 100 | 2026-09-16T19:00:09Z | 12 | 8.0 |
| Thiago | £7.8m | available / null | null | 4 | 3.3 |
| Haaland | £15.6m | available / null | null | 6 | 7.0 |
| Dubravka | £4.0m | available / null | null | not played | 0.0 |

### 7337262 — no Haaland

| Player | Price | Status / chance next | news_added UTC | GW6 points | ep_next |
|---|---:|---|---|---:|---:|
| Raya | £6.1m | available / null | null | 3 | 6.0 |
| Verbruggen | £4.5m | available / null | null | 9 | 7.7 |
| Gabriel | £7.9m | available / null | null | 2 | 4.0 |
| Castagne | £4.5m | available / null | null | 0 | 2.3 |
| Guéhi | £6.0m | available / null | null | 6 | 5.3 |
| Truffert | £5.4m | available / null | null | -1 | 1.3 |
| Shaw | £4.3m | available / 100 | 2026-09-11T13:00:09Z | 3 | 1.7 |
| Rogers | £7.9m | available / null | null | 9 | 6.3 |
| Palmer | £9.7m | available / 100 | 2026-09-21T13:00:09Z | 8 | 5.0 |
| Semenyo | £8.3m | available / 100 | 2026-09-24T12:00:09Z | 3 | 7.7 |
| Rice | £7.3m | available / 100 | 2026-09-21T13:00:08Z | 7 | 4.7 |
| Anderson | £6.3m | available / 100 | 2026-08-23T17:00:07Z | 6 | 4.3 |
| João Pedro | £7.8m | available / 100 | 2026-09-16T19:00:09Z | 12 | 8.0 |
| Isak | £9.0m | injured / 0 | 2026-09-27T10:30:09Z | 0 | 0.0 |
| Obi | £4.5m | unavailable / 0 | 2026-09-14T16:12:42Z | 0 | 0.0 |

Changes since the 11 October review: João Pedro rose £7.7m to £7.8m; Semenyo fell £8.4m to £8.3m and is now available/100 rather than doubtful/75. Isak remains injured/0 with an unknown return date. All other owned players are currently available except van Ewijk and Obi.

## GW7 provisional decision

No transfer or chip should be activated today. Wait for European usage, Isak's training evidence and Friday club press conferences. The public endpoints cannot establish exact free transfers or sale proceeds.

### 8522487 — provisional XI

Verbruggen  
Van Hecke, Mitchell, Castagne  
Dewsbury-Hall, Gibbs-White, Le Fée, Bruno Fernandes  
João Pedro, Thiago, Haaland

- Captain: **Haaland**; vice-captain: **João Pedro**.
- Bench: Dubravka; 1 Diop, 2 Xhaka, 3 van Ewijk.
- Castagne starts only provisionally because Hull at home is attractive. His GW6 zero minutes require a direct role check; if no useful clearance is available, Diop's secure minutes become the safer XI choice despite Manchester City away.
- Default transfer position: roll. One blank from Bruno or Gibbs-White does not justify an early sale.

### 7337262 — provisional XI while Isak is unavailable

Verbruggen  
Gabriel, Guéhi, Castagne, Shaw  
Rogers, Palmer, Semenyo, Rice, Anderson  
João Pedro

- Captain: **João Pedro**; vice-captain: **Semenyo**. Re-run captain projections after midweek fixtures and press conferences.
- Bench: Raya; 1 Truffert, 2 Isak, 3 Obi.
- If Liverpool clears Isak for a normal starting role, start him and bench Shaw in a 3-5-2.
- If Isak remains out or is limited on Friday, authenticate finances and compare **Isak to Evanilson**. Evanilson's Sunderland, Manchester United, Leeds and Ipswich sequence is the strongest balanced four-Gameweek route among the current budget discovery list. Kostoulas has a stronger GW7 estimate but then Liverpool and Manchester City; Emersonn begins at Manchester City. This is a contingent comparison, not an executed transfer.
- Do not use a hit merely to remove Obi. No chip case is established.

## Rolling GW7–GW10 plan

- **GW7:** Haaland home to Ipswich remains the primary captain anchor. The no-Haaland entry's decisive evidence is Isak's expected minutes; Castagne's role is the second availability check.
- **GW8:** Chelsea host Tottenham, supporting Palmer, Rogers and João Pedro. City visit Aston Villa; keep the premium structure flexible rather than forcing a one-week move.
- **GW9:** City host Brighton and Chelsea host Manchester United. Retain captaincy optionality around Haaland and the Chelsea attack.
- **GW10:** City visit Forest; Chelsea visit Sunderland. Evanilson, if required for Isak, also has Ipswich away.
- A multi-transfer route to Haaland on 7337262 is not justified without verified sale values and a quantified four-Gameweek gain. Rank pressure is not evidence.
- No Wildcard, Free Hit, Bench Boost or Triple Captain clears the current threshold.

## Source and repository freshness

Fresh official data came from FPL bootstrap, fixtures, event/6/live, both public entries, history, transfers, GW6 picks and Overall league page 20. Raw responses remain local and are not committed.

The current canonical checkpoint remains generation 0 with no ledger binding. The bound weekly packet is 11 August, the latest committed news triage is 17 August, and the latest committed model evidence run is 19 September. The 9 October community digest was read only as a challenge/discovery input; its pre-presser minutes and price claims are superseded by official match evidence. Draft PR 123 is the prior daily review. This report supersedes its Sunday score state without promoting unverified claims to the ledger.

## Manual confirmation required before GW7 action

For both entries, authenticate the transfer page and record current free transfers, current bank, any pending move, purchase/selling prices and resulting bank for each candidate. For 7337262, check Isak's authenticated selling price before comparing Evanilson or any alternative. After any edit, directly verify the saved XI, captain, vice-captain and bench order.

