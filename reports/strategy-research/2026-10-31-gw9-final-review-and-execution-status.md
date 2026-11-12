# GW9 final review and execution status — 31 October 2026

## Execution update — 09:29 GMT

**Both accounts are now completed and verified after reload.** See [the authoritative execution record](2026-10-31-gw9-execution.md). Entry 7337262: João Pedro to Jackson; Palmer C, Evanilson VC; £1.5m bank. Entry 8522487: João Pedro to Evanilson and Xhaka to Tavernier; Haaland C, Evanilson VC; £0.4m bank. All moves zero-hit, no chips, full XI/bench saved. The requested 09:00 target was missed; execution was completed before 11:00. The original review below is retained as point-in-time history; its blocked/degraded statements no longer describe current execution status.

## Original 07:40 outcome and authority

**Neither account changed in this review. Execution blocked by sign-in.** At approximately 07:39 UTC, the canonical FPL My Team page displayed Log in / Register, with no authenticated account identity or squad. No transfer, captain, bench, XI or chip submission occurred. No saved result can be claimed.

User authorises relevant changes for entries 8522487 and 7337262 by 09:00 UK. Official GW9 deadline: **2026-10-31T11:00:00Z**, confirmed in fresh bootstrap. This report is a manual execution handoff, not evidence of execution. The previous daily task's read-only scope does not revoke this separate authorisation.

- Public capture observed_at: 2026-10-31T07:40:02Z.
- News/repository review observed_at: approximately 07:39–07:44Z.
- effective_at: GW9 deadline, conditional on actual submission.
- finalised_at: null for account changes; none observed.
- Manager state: **degraded for both accounts**.
- Raw endpoint responses, credentials and browser state excluded from this report/repository.

## Governing context and corrections

Read docs/plan.md, control/rules/2026-27.yaml (2026-27-v1.0), PR141's verified GW8 execution record, and PR150's 31 October strategy report, live-entry companion, official-news discovery and model evidence review. Reviewed 30 October community context from the preceding interactive review.

PR150 remains bound to the 11 August packet, hash 65eba1fe…, with evidence tip b3599405…. It reports seven accepted and two rejected evidence claims. Its discovery catalogue coverage does not establish complete usable news: thirteen clubs have gaps. Its reconstructed Kinsky/Cherki/Wissa/Bogle squad is **not either owned squad** and must not be executed. The live-entry companion also mislabels Guéhi and Anderson's clubs; current bootstrap places both at Manchester City. A supposed Cherki vice-captain is invalid for the actual Haaland squad.

The actual Haaland history contains only Wilson→Dewsbury-Hall and Shaw→Castagne. It does not own Tavernier yet. The no-Haaland side already owns Evanilson, Tavernier and Truffert: no duplicate Evanilson purchase or fourth Bournemouth player is legal.

No current calibrated four-to-six-week forecast packet was available. The recommendations below are transparent football judgements using fresh official fixtures, availability, season underlying statistics and opportunity cost. They are **not a solved numerical optimum**. ep_next is a mutable FPL estimate, not a substitute for a calibrated forecast.

## Verified public state and private-state boundary

| Entry | GW8 points | Total | GW8 overall rank snapshot | Last-deadline value / bank | Chip history |
|---|---:|---:|---:|---|---|
| 8522487 | 50 | 458 | 4,919,028 | £99.3m / £0.2m | None used |
| 7337262 | 68 | 479 | 3,582,724 | £99.9m / £0.8m | None used |

Source: official entry/{id}/event/8/picks/, entry/{id}/history/ and entry/{id}/transfers/, freshly retrieved. Historical bank/value are not asserted current spendable balances. Public transfer history cannot exclude private pre-deadline GW9 moves.

The 30 October authenticated checkpoint for 7337262 showed one FT, £0.8m bank, João Pedro selling £7.6m and zero GW9 transfers. This is a previous observation, not today's verification. The Haaland account's current FT, bank, selling values and pending moves remain unknown; its older four-FT checkpoint must not be rolled forward into an assumed five.

Before manual execution, verify entry ID from Points, actual current squad, FT count, bank, sale values and existing GW9 moves. Do not repeat a move already executed.

## Fresh evidence review

| Source | published_at / freshness | Accepted conclusion | Limitation |
|---|---|---|---|
| [Official bootstrap](https://fantasy.premierleague.com/api/bootstrap-static/) and [fixtures](https://fantasy.premierleague.com/api/fixtures/) | Dynamic; observed 31 Oct 07:40Z | GW9 deadline 11:00Z; current prices/flags and GW9–14 fixtures | Feed availability is not guaranteed selection |
| [Chelsea pre-Liverpool statement](https://www.chelseafc.com/en/news/article/xabi-alonso-confirms-chelsea-team-news-for-liverpool) | Tuesday 27 Oct, dated by linked 30 Oct PL article and cup context; exact timestamp not exposed | Alonso confirms João Pedro thigh injury and absence for several weeks | Exact return date unknown |
| [Chelsea pre-Manchester United statement](https://www.chelseafc.com/en/news/article/xabi-alonso-confirms-chelsea-team-news-for-manchester-united) | Friday 30 Oct context | Lacroix and Hato absent; Caicedo available | No blanket medical clearance of all attackers |
| [PL suspensions](https://www.premierleague.com/en/news/4425344) | Page 25 Oct; explicitly updated 29 Oct | Palmer served his one-match suspension in the EFL Cup and is eligible for GW9; Thiago on four yellows | Thiago is not currently suspended |
| [Manchester City press conference](https://www.mancity.com/news/mens/enzo-maresca-brighton-squad-update-63928963) | Friday 30 Oct context | All available except Semenyo; Haaland and Anderson absent from Wednesday cup squad | Rest supports selection but does not guarantee a start |
| [Spurs team news](https://www.tottenhamhotspur.com/news/1182287/team-news-udogie-back-bergvall-savio-tosin-out-for-palace-clash) | Friday 30 Oct, relative age displayed | Udogie returns; listed absences exclude Van Hecke | No exact start promise |
| [Villa press conference](https://next.avfc.co.uk/news/2026/october/30/prematch-emery-looks-ahead-to-fulham-encounter/) | 30 Oct; repository metadata 14:40Z | Emery discusses Jackson's progress and prioritises Fulham/Premier League | Readable club text does not establish unconditional medical clearance; reported training caveat remains uncertainty |
| [PL forward comparison](https://www.premierleague.com/en/news/4750154) | 30 Oct | Jackson and Evanilson both credible replacements; recent chance involvement and fixture comparison | Editorial analysis, not a medical statement or forecast guarantee |
| [PL captain comparison](https://www.premierleague.com/en/news/4750462) | 30 Oct | Haaland strongest default; Palmer strong alternative against United's weak defence | Editorial judgement evaluated alongside squad constraints |
| [Arsenal press conference](https://www.arsenal.com/news/every-word-from-mikel-artetas-pre-liverpool-presser-afYSq0q0nbtN) | Repository metadata 30 Oct 14:29:41Z | Direct fetch failed 403; no new direct claim admitted here | Media/community report Rice trained, conditional on Saturday; retain as challenge input, not medical clearance |

Current owned-player flags: João Pedro injured, 0%, news_added 24 Oct 16:30:09Z; Rice doubtful, 75%, news_added 28 Oct 00:00:08Z. All other owned players currently have available status. Jackson, Evanilson and Tavernier available in fresh feed. No fresh Saturday medical clearance located.

Changes from 30 October capture: Jackson £6.8m→£6.9m; Tavernier £6.4m→£6.5m; Rogers £8.0m→£8.1m; Gabriel £7.9m→£8.0m. Buy prices are not sale prices. No new owned-player flag change.

Rejected as execution evidence: public picks proving a saved GW9 XI; stale Isak injury; Tavernier already owned by Haaland side; Palmer still banned; blanket Rice clearance; Jackson absence being definitely rest-only; Bruno permanently dropped; Tavernier sole penalty taker. Community claims guide questions only. Several club pages were empty/inaccessible, so the review does not claim a complete official medical clearance for every player.

## Preferred decisions

### Entry 8522487 — Haaland

**João Pedro→Evanilson (£6.3m), Xhaka→Tavernier (£6.5m), only as two free affordable moves.**

Budget gate: combined selling proceeds plus actual bank must cover £12.8m; verify confirmation screen shows zero-point cost. No sale values or current FT inferred. If only one free move or the second is unaffordable, make João Pedro→Evanilson only, retaining Xhaka and starting Dewsbury-Hall instead of Tavernier.

Why this pair: the first move replaces confirmed absent minutes. It also frees resources for the midfield upgrade. Bournemouth's next six are LEE(H), IPS(A), NFO(H), FUL(A), BHA(H), HUL(H). Tavernier's season xG+xA is 4.94 in 660 minutes versus Xhaka's 1.69 in 720; Xhaka's defensive contribution reduces, but does not erase, the attacking opportunity cost. This is a multiweek upgrade, not a reaction to last week's points.

Retain Dewsbury-Hall: Coventry at home in GW10 and five recent big-chance involvements in the PL comparison. Selling him instead of Xhaka gives up a useful rotation option. Retain Bruno for now: seven season starts and 4.16 xG+xA; one benching and low recent points do not alone justify another transfer. Keep Thiago's 5.04 season xG+xA, while monitoring four yellows and a harder GW12–14 run.

Preferred 3-4-3:
- Verbruggen
- Van Hecke, van Ewijk, Diop
- Bruno Fernandes, Gibbs-White, Le Fée, Tavernier
- Haaland **C**, Evanilson **VC**, Thiago
- Bench: Dubravka; **1 Dewsbury-Hall, 2 Castagne, 3 Mitchell**

If only João Pedro→Evanilson: Dewsbury-Hall takes Tavernier's XI place; Xhaka first bench. Same captain/vice and remaining bench.

Diop at Hull and van Ewijk at home to Sunderland are fixture-led selections over Castagne at Villa/Mitchell at Spurs. Verbruggen is the playing goalkeeper despite City away; Dubravka's zero season minutes make him unsuitable to start.

Jackson was considered: attractive Villa schedule, but higher price and lower season xG+xA than Evanilson, plus the funding benefit of Evanilson enables the Xhaka upgrade. Neither transfer requires the other squad to remain different.

### Entry 7337262 — no Haaland

**João Pedro→Nicolas Jackson (£6.9m), one free transfer; no other transfer.**

Using yesterday's observed sale price £7.6m and bank £0.8m would leave **£1.5m**, subject to current UI confirmation and no intervening moves. Already owns Evanilson and all three Bournemouth slots.

Jackson's next six: FUL(H), MUN(A), SUN(H), IPS(A), EVE(H), CRY(H). The first four offer a useful extended run. Recent five big chances/13 box shots support the selection, but four recent goals and 2.70 season xG+xA do not justify extrapolating his scoring streak indefinitely. European workload and the reported training caveat remain risks.

Alternatives: Thiago has stronger season underlying involvement (5.04 xG+xA) but costs £7.8m and faces a materially harder six-week run. Barry offers value and strong chance volume but less immediate fixture appeal. Calvert-Lewin is cheaper, but Jackson's role/fixture combination is preferred. A second Evanilson purchase is impossible. Retain Rice for Hull at home in GW10 rather than spending a hit on a doubt.

Preferred 3-4-3:
- Raya
- Guéhi, Truffert, Davis
- Palmer **C**, Rogers, Tavernier, Anderson
- Evanilson **VC**, Isak, Jackson
- Bench: Verbruggen; **1 Gabriel, 2 Rice, 3 Castagne**

Davis over Gabriel is a close, fixture-led call: Hull away versus Liverpool away, with Davis's season 1.64 xG/0.64 xA providing attacking upside. Gabriel remains first substitute and a strong hold, not a transfer out. Rice's uncertainty places him second substitute. Palmer's eligibility resolves the captaincy concern; choose him over Jackson's smaller sample and Tavernier's uncertain penalty priority.

## Four-to-six-week plan and chip comparison

| Option | GW9 decision | Future trigger / opportunity cost |
|---|---|---|
| No chip | Preferred for both | Free transfers can repair the confirmed injury without spending a season resource |
| Wildcard | Reject now | Compare an actual six-week alternative after GW10/international break; squad quality, minutes and net gain matter, not an arbitrary three-problem threshold |
| Free Hit | Reject now | Does not fix João Pedro beyond this week. Reassess GW12 Arsenal–City collision, especially no-Haaland's concentration, and December rotation |
| Bench Boost | Reject now | Haaland squad has non-playing Dubravka; no-Haaland bench includes a doubtful Rice and difficult goalkeeper/defender fixtures |
| Triple Captain | Reject now | Haaland's BHA home match is credible, but reserve comparison with Fulham GW11 and Hull GW16; no-Haaland can compare Palmer's GW17–18 windows if fit |

Official [27 October chip review](https://www.premierleague.com/en/news/4362085) supports evaluating later windows. First-set chips expire at the GW19 deadline under the versioned rules; one chip per week means planning the sequence, not saving everything indefinitely. A GW16 Wildcard and GW16 Triple Captain cannot both be played; retain alternatives before committing.

GW10: no forced reversal of Bournemouth buys; consider starting Dewsbury-Hall against Coventry and Rice/Gabriel against Hull if fit. Reassess Bruno's actual role.
GW11–12: compare captaincy/TC with updated minutes; review Thiago before fixtures worsen; assess no-Haaland's Arsenal/City concentration in GW12.
GW13–14: Bournemouth still has attractive fixtures, including Hull at home in GW14; reassess Villa European rotation and the value of banked transfers.
No forced Haaland purchase for no-Haaland side and no differential move merely to maintain experimental separation.

## Validation and exact completion boundary

A local deterministic check loaded squad/lineup rules from control/rules/2026-27.yaml and fresh player IDs/clubs. Both proposed complete squads passed: unique 15, 2/5/5/3 positional composition, club maximum, legal 3-4-3, captain/vice in XI and distinct, and ownership after proposed swaps. **Financial legality, current FT and execution remain unverified.**

Manual sequence: sign in to the correct entry; verify existing moves/FT/bank/selling prices; submit only the still-needed zero-hit transfers; set the specified XI, captain, vice and bench; press Save Your Team; reload and confirm everything persists. Do not mistake recommendation tables for saved selections.

Completed: public data refresh, news/repository challenge, independent recommendations, chip comparison, non-financial rules validation.
Blocked: both authenticated identities, current private state, transfer submission, lineup saving and persisted-state verification.
