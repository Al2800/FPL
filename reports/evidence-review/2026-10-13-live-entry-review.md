# Official evidence review — 13 October 2026

Scope: entries 8522487 and 7337262, GW7 deadline 2026-10-17T10:00:00Z. Endpoint observations: 07:31:05–07:31:11 UTC on 13 October. News review interval: 07:30–07:45 UTC. This review accompanies the [derived decision report](../strategy-research/2026-10-13-live-entry-decision-input.md). It does not mutate the canonical evidence ledger.

## Acceptance and temporal discipline

| Evidence | published_at / source timestamp | Accepted scope | Restriction |
|---|---|---|---|
| [FPL bootstrap](https://fantasy.premierleague.com/api/bootstrap-static/) Shaw flag | `news_added=2026-10-12T21:30:08.995810Z`; endpoint publication time absent | New doubtful/75 next round, unspecified injury | No diagnosis, duration or confirmed GW7 absence |
| [FPL GW6 live](https://fantasy.premierleague.com/api/event/6/live/) van Ewijk | Match 12 October; endpoint publication time absent | 90 minutes, assist, six points; bootstrap available/100 next and £3.9m | Appearance is not a guarantee of next start; old September news_added retained |
| [Liverpool injury list](https://www.liverpoolfc.com/news/liverpools-injury-list-suspensions-and-availability) | Page last updated 12 October; Isak quote 9 October; newer recovery comment 11 October | Isak small thigh muscle injury, assessed day to day; unavailable for completed City match | No verified Brentford clearance or definitive GW7 absence; newest page timestamp does not refresh the Isak quote |
| [Chelsea confirmed XI](https://www.chelseafc.com/en/news/article/confirmed-chelsea-line-up-vs-bournemouth-oct-26) | 10 October match publication; exact clock absent | Palmer, Rogers, João Pedro all started; FPL records 87/83/71 minutes respectively | Confirms recovery sufficient for GW6, not unconditional future full minutes |
| [Official chip rules](https://www.premierleague.com/en/news/4679879/whats-happening-with-fpl-chips-in-202627) | 20 July 2026 | Two sets, first expiry at GW19 deadline; one chip per week; GW19/20 Free Hit restriction | Rules evidence; not proof any chip is optimal today |
| [United news index](https://www.manutd.com/en/news), [Bruno article](https://www.manutd.com/en/news/bruno-fernandes-injury-news-atletico-madrid-v-united), [Atleti team news](https://www.manutd.com/en/news/team-news-for-atletico-de-madrid-v-united) | Index showed relative ages 13/14 hours on observation; exact publication date not exposed in accessible body | Index carries a headline reassuring over Bruno fitness and a team-news item | Article bodies absent in web extraction; direct HTTP returned 403. No quotation, Shaw diagnosis or return date admitted from these pages |
| [Fulham post-Ipswich presser](https://www.fulhamfc.com/news/2026/october/10/post-ipswich-press-conference-/) | 10 October 2026 displayed | Dated presser exists; FPL separately records Castagne zero minutes | No accessible transcript; cannot establish why omitted or whether he returns |

`observed_at` is the retrieval interval above, not publication time. For live endpoint summaries, `published_at=null`; `news_added` is preserved separately. Injury claims are effective when reported, pending further information, and expire for decision use at the next material update/deadline. Match observations apply to their completed fixtures. `finalised_at=null` for GW6 scores because FPL still reports `data_checked=false`. No use of news published after a historical deadline to justify the original GW6 selection.

## Player-by-player coverage, grouped by official club

All 27 distinct owned players were checked in the fresh bootstrap and GW6 live feed; completed GW5 and locked GW6 picks were read for both teams. Searches covered injuries, returns, suspensions, selection and roles. A search yielding no new admissible claim is a coverage result, not a fitness clearance.

| Players / candidates | Official search and source checked | Result and gap |
|---|---|---|
| Haaland, Semenyo, Guéhi, Anderson | [City Liverpool report](https://www.mancity.com/news/mens/liverpool-v-city-premier-league-match-report-october-2026-63927325), 11 October match; official FPL minutes | Recent involvement supports holding. Midweek workload and Friday selection evidence still required for captain/TC |
| Palmer, João Pedro, Rogers | Chelsea XI above, 10 October; official FPL 87/71/83 minutes | Prior unresolved injury assumptions superseded by actual starts; no newer adverse official claim found |
| Isak | Liverpool list above, updated 12 October | Unavailable/0 persists. Wait for a specific recovery/starting-role update |
| Shaw, Bruno, Obi | United index and team-news links above; official FPL | Shaw newly flagged; Bruno available; Obi unavailable on loan. Bodies could not support additional medical conclusions |
| van Ewijk | [Coventry match report](https://www.ccfc.co.uk/news/2026/october/12/coventry-city-4-1-newcastle-united-/), URL dated 12 October, article body unavailable; official live statistics | Return established from FPL, not an inferred club quotation |
| Castagne | Fulham presser above, 10 October; FPL match record | Zero minutes, but still available flag. Role uncertainty is separate from fitness |
| Verbruggen; Kostoulas candidate | [Brighton teamsheets](https://www.brightonandhovealbion.com/teamsheets), Sunderland match dated 10 October; official FPL | Search found recent team-sheet context, no new admissible injury report. Candidate's 412 season minutes/5 starts retained; not guaranteed 90 minutes |
| Van Hecke, Dubravka | [Tottenham official site](https://www.tottenhamhotspur.com/?nocache=true), dated 9 October availability headline; FPL | Van Hecke played 90; Dubravka zero. A reserve keeper is not made a Bench Boost starter by an available flag |
| Raya, Gabriel, Rice | [PL club injury round-up](https://www.premierleague.com/en/news/4450606/latest-premier-league-player-injuries-club-by-club-news/), updated 12 October 19:45 BST; arsenal.com targeted search; FPL | No new owned flag. Round-up names other Arsenal injuries; do not infer a new Rice role or numerical defence downgrade from snippets |
| Mitchell | [Palace match reporting index](https://www.cpfc.co.uk/news/match-reports/), Forest fixture 11 October; FPL | 90 minutes, no new accepted availability claim |
| Gibbs-White; Aina candidate | [Forest team news](https://www.nottinghamforest.co.uk/news/2026/october/11/team-news---one-change-for-palace-matchup/), 11 October | Official search extract places Gibbs-White supporting Delap and Aina returning to XI. Article body not extracted; role observation limited to this match |
| Le Fée, Xhaka | [Sunderland team news](https://www.safc.com/news/2026/october/10/le-bris-makes-three-sunderland-changes/), 10 October | Both named in official starting XI; FPL minutes 80/90. No new injury claim admitted |
| Dewsbury-Hall | [Everton Hull report](https://www.evertonfc.com/news/2026/october/11/hull-report/), 11 October | Official report supports attacking involvement; no new availability issue found. Thirteen points are not a sustainable weekly projection |
| Thiago | [Brentford pre-Villa news](https://www.brentfordfc.com/en/news/first-team-news-aston-villa-v-brentford-premier-league-10-10-2026), 9 October context; fresh injury-news search; FPL | No new owned injury claim; other Brentford injuries surfaced. Do not infer penalties or a role change |
| Truffert; Evanilson candidate | [Bournemouth Chelsea report](https://www.afcb.co.uk/news/2026/october/10/chelsea-afc-bournemouth-match-report-october-2026/), 10 October | Official search extract records Evanilson goal and Truffert substitution; no new injury claim. FPL supplies minutes and availability |
| Diop; Emersonn candidate | [Ipswich team news](https://www.itfc.co.uk/news/2026/october/10/Ipswich-Town-team-news-Premier-League-Fulham/), 10 October; FPL | Recent match involvement; no new accepted injury report. City away limits GW7 appeal |
| Jackson candidate | [Villa team news](https://www.avfc.co.uk/news/2026/october/09/prematch-team-news-for-brentford-encounter/), 9 October; [10 October XI](https://www.avfc.co.uk/news/2026/october/10/news-brentford-team-news/); FPL | Candidate remains available; 376 season minutes/5 starts require minutes sensitivity |
| Calvert-Lewin, Bogle candidates | [Leeds news](https://www.leedsunited.com/en/news), current weekend coverage; FPL | No new dated adverse claim found. Older Calvert-Lewin injury articles rejected; no inferred new injury |

News coverage remains incomplete where official pages expose only titles or inaccessible bodies. The report explicitly relies on FPL for flag changes in those cases. Search snippets are identified as such, never recast as verified direct quotations.

## Rejected or restricted claims

- **GW6 is final:** rejected at this observation. All ten games are provisionally finished, but the event flags and empty automatic_subs prohibit a final points/rank claim.
- **Shaw has a specific long-term injury / definitely misses Leeds:** unsupported. FPL says unspecified and 75%; community reports of missing the Madrid trip are discovery leads, not our medical evidence.
- **Isak will definitely be back for GW7:** not established by the older day-to-day comment. Equally, zero next-round chance is a current FPL flag, not certainty about Saturday.
- **Bruno injury rumours from discussion forums:** not accepted. Official feed available; official index reassurance is limited supporting context without an accessible dated body.
- **Castagne permanently dropped:** one DNP does not prove this. A clear role update is still needed.
- **Kinsky/Cherki/Wissa are owned by 8522487:** contradicted by locked official picks and completed transfer history. Preserve Dubravka, Dewsbury-Hall and Thiago.
- **Community chip popularity or imminent rises justify action:** rejected as decision evidence. The 12 October repo digest was read; TC discussions prompt comparison only. Kostoulas is now £5.7m officially, but a price change does not establish superior multiweek value.
- **Official ep_next is our calibrated forecast:** rejected. Values changed substantially overnight; no new sealed GW7 model packet exists.
- **Three concerns automatically trigger Wildcard:** rejected. Compare legal repairs, opportunity costs and a durable 4–6 week rebuild using verified private finances.
- **Current free transfers or sale values can be reconstructed from history:** not accepted in this workflow. Manual authenticated confirmation remains required.

## Repository and publication audit

Additional same-day review: draft PR126, its full strategy briefing, live-entry companion and four-claim model audit were read. The unmerged ledger tip is `a562be38680047bb1986b805de47f4746ea0c3c62de376017e5d2067457dae12`. Its admission status is not a fresh sealed GW7 projection. Independently fetching the cited Arsenal injury original returned 403; reported Lille absences must not be stretched to GW7. This report corrects the pending-autosub and João Pedro-cover interpretation, and withholds automatic TC activation. Groß and De Cuyper were added to the comparison list using official bootstrap fields; [Brighton's 9 October preview](https://www.brightonandhovealbion.com/media-article/mft-match-preview-sunderland-bha-pl-october-2026) provides official creative-role context, not new medical clearance. The [11 October Scout chip editorial](https://www.premierleague.com/en/news/4362085/triple-captain-haaland-in-gameweek-7-how-and-when-to-use-your-fpl-chips) is accepted as a source of candidate windows, not quantitative expected value.

Read governing plan/rules and reviewed canonical checkpoint, stale weekly packet, news triage, model audit, prior daily draft PR125 and latest committed 12 October community research. Main is `4daa2e665da14aae506462b63a1adf15f5bb3b95`. No pipeline, source-registration, rules, model, ledger or execution code changes are made. No raw endpoint bodies, credentials, browser state or additional manager identifiers are included. This change consists only of this evidence review and its derived strategy report; it is proposed in a draft PR.
