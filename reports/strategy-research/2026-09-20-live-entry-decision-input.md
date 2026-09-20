# Live-entry decision input — 2026-09-20

- observed_at: 2026-09-20T07:22:11Z
- decision point: mid-GW5, before Sunday's four fixtures
- entries: 8522487 and 7337262
- next deadline: 2026-10-10T10:00:00Z (11:00 BST)
- account writes: false
- live-entry authority: official FPL public endpoints
- methodology: point-in-time evidence, source hierarchy, transfer conservation and explicit falsifiers from the repository
- relationship to `reports/strategy-research/2026-09-20.md`: this file is the authoritative operational correction for the two public entries. The model report's Kinsky/Cherki/Wissa reconstruction is not either live squad.

## Decision summary

There is no action to take during GW5. The deadline has passed and the selections are locked.

Two material changes since the 19 September update:

1. The official live endpoint now scores entry 8522487 at **22 GW5 points / 263 total**, one point below the earlier 23/264 display. Verbruggen is now 6 rather than 7. The event picks snapshot still reports 23/264, so FPL's public endpoints are temporarily inconsistent. Use the live endpoint and entry summary for the current score, then reconcile after data is checked.
2. Milan van Ewijk is newly flagged at **75%** with a hamstring injury, timestamped 2026-09-19T16:00:09Z. Coventry's official social post attributes the absence to Frank Lampard and calls it a small hamstring issue. This reduces the Haaland squad's bench depth for GW6 but does not justify an early transfer during the international break.

The only other accepted new official claim is Pedro Porro's suspected hamstring injury. He is not owned by either entry, but the update removes him from the defender shortlist.

## Official live state

Sources captured at observed_at:

- bootstrap, deadlines, prices and status fields: https://fantasy.premierleague.com/api/bootstrap-static/
- GW5 fixtures: https://fantasy.premierleague.com/api/fixtures/?event=5
- live player scoring: https://fantasy.premierleague.com/api/event/5/live/
- public entry summaries and GW5 picks for entries 8522487 and 7337262
- public transfer and chip histories for both entries

### Entry 8522487, Haaland

- current official entry summary: **22 GW5 points, 263 total, OR 5,024,957**
- start-of-GW5 picks snapshot: 23 points, 264 total, OR 4,930,206
- top-1k live threshold sampled from the Overall league: 389 points, so the current summary gap is 126
- GW5 transfer: Shaw to Castagne at 2026-09-18T16:02:06Z, no hit
- chips used: none
- value/bank in the locked GW5 snapshot: **£99.6m / £0.2m**
- exact GW6 free transfers, pending transfers, purchase prices and selling prices: **not publicly exposed**

Locked XI:

Verbruggen; Van Hecke, Mitchell, Castagne; B.Fernandes, Gibbs-White, E.Le Fée, Dewsbury-Hall, Xhaka; Thiago, Haaland (C).

Vice-captain: B.Fernandes.

Bench: Dubravka; 1 João Pedro, 2 Diop, 3 van Ewijk.

Completed Saturday scoring from the live endpoint:

| player | min | pts | xG | xA |
|---|---:|---:|---:|---:|
| Verbruggen | 90 | 6 | 0.00 | 0.00 |
| Van Hecke | 90 | 6 | 0.35 | 0.30 |
| Gibbs-White | 90 | 2 | 0.00 | 0.40 |
| Dewsbury-Hall | 90 | 3 | 0.37 | 0.34 |
| Thiago | 90 | 5 | 0.72 | 0.03 |
| João Pedro, bench | 0 | 0 | 0.00 | 0.00 |
| Diop, bench | 90 | 4 | 0.06 | 0.01 |

Sunday exposure: Mitchell, Castagne, B.Fernandes, E.Le Fée, Xhaka and Haaland (C). If any valid starter fails to appear, João Pedro's zero is skipped and Diop's 4 can auto-sub subject to formation rules.

### Entry 7337262, no Haaland

- current official entry summary: **9 GW5 points, 257 total, OR 5,582,331**
- locked picks snapshot: 9 points, 257 total, OR 5,577,096
- current gap to the sampled top-1k threshold: 132
- GW5 transfer: Maatsen to Castagne at 2026-09-18T15:47:18Z, no hit
- chips used: none
- value/bank in the locked GW5 snapshot: **£99.8m / £0.0m**
- exact GW6 free transfers, pending transfers, purchase prices and selling prices: **not publicly exposed**

Locked XI:

Raya; Gabriel, Castagne, Guéhi; Rogers, Palmer (C), Semenyo, Rice, Anderson; João Pedro, Isak.

Vice-captain: Rogers.

Bench: Verbruggen; 1 Truffert, 2 Shaw, 3 Obi.

Completed Saturday scoring from the live endpoint:

| player | min | pts | xG | xA |
|---|---:|---:|---:|---:|
| Raya | 90 | 1 | 0.00 | 0.00 |
| Gabriel | 90 | 1 | 0.00 | 0.14 |
| Rogers | 90 | 2 | 0.33 | 0.07 |
| Palmer (C) | 90 | 4 doubled | 0.13 | 0.18 |
| Rice | 90 | 1 | 0.02 | 0.06 |
| João Pedro | 0 | 0 | 0.00 | 0.00 |
| Verbruggen, bench | 90 | 6 | 0.00 | 0.00 |

Sunday exposure: Castagne, Guéhi, Semenyo, Anderson and Isak. Truffert is first bench and should replace João Pedro if he appears against Liverpool. The no-Haaland team is six points behind the Haaland team before Sunday's matches, after leading by seven at the start of GW5.

## Status and freshness review

Only live flags that affect the two squads are listed. Every other owned player is currently status `a` in the bootstrap.

| player | entry | official FPL status | chance next | news timestamp | decision treatment |
|---|---|---|---:|---|---|
| João Pedro | both | doubtful, knee | 75% | 2026-09-16T19:00:09Z | Hold pending a dated Chelsea original; do not treat community recovery estimates as official |
| van Ewijk | 8522487 | doubtful, hamstring | 75% | 2026-09-19T16:00:09Z | New; bench-depth concern for GW6, not an international-break sell today |
| Shaw | 7337262 | doubtful, unspecified | 50% | 2026-09-11T13:00:09Z | Stale; require post-break club update before any decision |
| Obi | 7337262 | unavailable, loan | 0% | 2026-09-14T16:12:42Z | Known dead slot; address only when it improves the XI or enables a structure change |

### Accepted official claims

- **Pedro Porro, not owned:** Tottenham published on 2026-09-19 at 15:23Z that he left after 19 minutes and Roberto De Zerbi thought it was a hamstring problem, with severity unconfirmed. Remove Porro from the GW6 defender shortlist until he is cleared: https://www.tottenhamhotspur.com/news/1091097/team-news-robertos-latest-on-pedro-porro
- **Milan van Ewijk, owned by 8522487:** Coventry's official social output on 2026-09-19 reports Frank Lampard confirmed he missed the Forest match with a small hamstring issue. This aligns with the new FPL 75% flag: https://www.facebook.com/CoventryCityFC/posts/1527287582761608/

### Rejected or unresolved claims

- A reported João Pedro recovery timetable remains community or secondary reporting. No dated Chelsea original was found, so it is not promoted to official evidence.
- The 11 September Shaw flag is too old to determine GW6 availability. No fresh, recoverable Manchester United original changes that state.
- Sunday lineup rumours are rejected as decision evidence. Official lineups will arrive after the GW5 deadline and cannot change the locked teams.
- Tottenham's 18 September statement that Porro was available is superseded by the 19 September post-match injury statement.

The repository's 20 September discovery searched all 21 clubs. Thirteen returned no dated official item under its filters. That is catalogue coverage, not proof that every player is fit.

## Implications

### GW5

No transfers, chips, captaincy or bench order can be changed.

The largest remaining swing is Haaland captain versus Palmer's locked four captain points. The no-Haaland side can recover one bench return through Truffert for João Pedro. The Haaland side has Diop's four points available if a starter no-shows and formation permits.

### GW6 provisional direction

Do not make an early international-break transfer.

- **8522487:** provisional captain B.Fernandes at home to Spurs, vice Haaland at Liverpool. João Pedro at home to Bournemouth becomes an XI candidate only if cleared. Van Ewijk's injury makes bench-depth monitoring more important, but Castagne, Mitchell, Van Hecke and Diop still provide four other defenders.
- **7337262:** provisional captain Palmer at home to Bournemouth, vice Rogers at home to Brentford. If João Pedro is not cleared, a 4-5-1 is possible without a hit. Shaw and Obi mean this side has less tolerance for another defensive absence.
- **Wildcard:** activate only if post-break official news creates at least three simultaneous structural problems. João Pedro alone, or van Ewijk alone, is not enough.
- **Defender shortlist:** Porro is paused. Bogle away to Arsenal in GW6 is not a priority purchase. Reassess after the break using availability and expected minutes, not recent points alone.

### GW7 to GW9

- GW7 Man City v Ipswich remains the probable Haaland captain anchor. Triple Captain should be considered only after post-break expected-minutes evidence. Do not commit now.
- The no-Haaland route to Haaland for GW7 requires authenticated selling prices, bank and free transfers. Do not manufacture a route from public current prices.
- GW8 and GW9 favour retaining flexible premium and forward slots: Palmer has Spurs then Man Utd; Haaland has Aston Villa then Brighton; Bruno has Bournemouth then Chelsea. Reassess after GW6 rather than booking transfers now.
- Preserve the experiment as analysis, but maximise each team independently. Divergence is justified only by each squad's real constraints and best expected return.

## Manual confirmation required before the GW6 decision

Open each authenticated transfer page shortly before the 10 October deadline and record:

1. exact free transfers;
2. bank;
3. each relevant purchase and selling price;
4. whether any pending transfer exists;
5. chip availability shown in the account.

Until that check, manager state is **degraded**. Public history confirms completed moves and the locked GW5 value/bank snapshot, but not the private GW6 state.

## Change control

This report corrects the model reconstruction in the other 20 September strategy report. It does not change the evidence ledger and does not write to either FPL account. Reconcile the live-score discrepancy after FPL marks GW5 data checked.
