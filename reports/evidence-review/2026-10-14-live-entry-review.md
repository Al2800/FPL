# Evidence review — live entries, 14 October 2026

## Scope and point-in-time boundary

- Entries: 8522487 and 7337262 only.
- FPL observed_at: **2026-10-14T07:37:30.42Z–07:37:33.51Z**.
- News/search observations: **2026-10-14T07:38Z–07:47Z**, rounded review interval; exact publication times are not manufactured from search crawl times.
- Decision cutoff: **2026-10-17T10:00:00Z**, GW7.
- Main: `095e4a267716b7dfa66caaa196098faf67b33a98`.
- Account operations: none. Authentication not used. Current private manager state degraded.
- This is a derived review, not an evidence-ledger admission run. No canonical ledger changes.

## Repository material reviewed

AGENTS.md, docs/plan.md and season rules; canonical evidence-checkpoint manifest; weekly-2026-08-11 packet; committed 17 August news triage and 19 September model review; PR127's 13 October live-entry report/evidence review; PR128's 14 October strategy, live-entry companion, model review and news discovery; committed 13 October X community digest.

Main's checkpoint is generation 0 with no ledger binding. PR128 reports five accepted model claims and ledger transition a562be38… → bd9dab96…; this is unmerged review provenance, not a new sealed canonical weekly packet. Its primary advisory 15 is not an owned-team reconstruction. The new public picks fetch removes PR128's no-Haaland 403 gap for this report.

## Official endpoint coverage

All requested public endpoint groups fetched successfully:

| Endpoint | Purpose / verified field |
|---|---|
| [bootstrap-static](https://fantasy.premierleague.com/api/bootstrap-static/) | Prices, status, both chance fields, news/news_added, mutable ep_next, event deadlines and finished/data_checked |
| [fixtures](https://fantasy.premierleague.com/api/fixtures/) | GW7–10 opponents/home-away; no four-week fixture change found against previous snapshot |
| [GW6 live](https://fantasy.premierleague.com/api/event/6/live/) | Individual minutes and final points |
| [8522487 entry](https://fantasy.premierleague.com/api/entry/8522487/) / [7337262 entry](https://fantasy.premierleague.com/api/entry/7337262/) | Current public total and overall rank; personal profile fields excluded |
| [8522487 history](https://fantasy.premierleague.com/api/entry/8522487/history/) / [7337262 history](https://fantasy.premierleague.com/api/entry/7337262/history/) | Last-deadline value/bank, completed-GW transfer costs, historical chip usage |
| [8522487 GW6 picks](https://fantasy.premierleague.com/api/entry/8522487/event/6/picks/) / [7337262 GW6 picks](https://fantasy.premierleague.com/api/entry/7337262/event/6/picks/) | Final historical picks, multipliers, captain/vice, autosubs |
| [8522487 transfers](https://fantasy.premierleague.com/api/entry/8522487/transfers/) / [7337262 transfers](https://fantasy.premierleague.com/api/entry/7337262/transfers/) | Publicly completed transfer history; not private pending moves |
| [Overall table page 20](https://fantasy.premierleague.com/api/leagues-classic/314/standings/?page_standings=20) | Sampled rank_sort=1000 boundary: 490 points; other manager identifiers excluded |

Mutable endpoint published_at is **not exposed**. Record observed_at rather than inventing publication times. news_added belongs to each player's news item, not the whole response and not necessarily a cleared flag's update. No raw responses are committed.

GW6 is finished/data_checked; entry summary totals 356/357 and points 64/66. Post-autosub order is a scoring transformation, not evidence of a newly saved manager XI. Entry summary and history ranks differ slightly; the former is the selected current reporting field.

## Accepted claims and limits

| Claim | Official source / publication | Assessment |
|---|---|---|
| Isak had not returned to group training; return uncertain | [Liverpool LASK team news](https://www.liverpoolfc.com/news/lask-v-liverpool-champions-league-team-news), **13 Oct 2026**; direct coach comments from Tuesday conference. PR128 reports 16:13Z; this review independently establishes the day, not exact metadata time. | **New, accepted.** Stronger repair contingency; not a definite GW7 exclusion. |
| Haaland present in pre-PSG training material; PSG on 14 Oct | [City gallery](https://www.mancity.com/news/mens/man-city-training-gallery-13-october-63927510), **13 Oct 2026** | Accepted for training/workload scheduling only; no promised weekend start or minutes. |
| Verbruggen now £4.6m; other owned prices unchanged | Official bootstrap pair observed 13 and 14 Oct | Accepted market movement, not selling-price movement. |
| Owned flags unchanged: Isak i/0 next, Shaw d/75 next, Obi u/0 next | Official bootstrap, observed today; news timestamps 27 Sep / 12 Oct / 14 Sep respectively | Accepted feed state. No new diagnosis or exact return inferred. |
| Van Ewijk returned to training | [Coventry update](https://www.ccfc.co.uk/news/2026/october/08/frank-lampard-provides-injury-update-ahead-of-newcastle-united-clash/), **8 Oct 2026** | Existing evidence, reinforced by final GW6 90 minutes. Not a new 14 Oct clearance. |
| Brighton used Verbruggen, Groß, De Cuyper and Kostoulas | [Sunderland–Brighton report](https://www.brightonandhovealbion.com/media-article/match-report-pl-sunderland-v-albion), **10 Oct 2026** | Historical selection evidence; substitutions do not independently imply injury. |
| Truffert/Evanilson appeared against Chelsea | [Bournemouth report](https://www.afcb.co.uk/news/2026/october/10/chelsea-afc-bournemouth-match-report-october-2026/), **10 Oct 2026** | Historical involvement, not a future guarantee. |
| Mitchell/Gibbs-White started; Aina used | [Palace–Forest report](https://www.cpfc.co.uk/news/match-reports/match-report-highlights-crystal-palace-nottingham-forest-october-2026/), **11 Oct 2026** | Historical role evidence, no fresh injury clearance. |
| Haaland GW7 is a legitimate TC comparison; later Chelsea windows exist | [PL chip article](https://www.premierleague.com/en/news/4362085/triple-captain-haaland-in-gameweek-7-how-and-when-to-use-your-fpl-chips), **11 Oct 2026** | Official editorial advice, not a medical source or calibrated projection. |

## Whole-squad and candidate coverage

Every owned player is covered by the fresh official status snapshot. Searches targeted official club/PL injury, return, suspension, tactical-role and press-conference material for the groups below. **A searched group with no dated usable statement is a coverage gap, not proof of full fitness or absence of suspensions.** Old-season search hits were discarded.

| Club | Owned players / candidates searched | Result and remaining gap |
|---|---|---|
| Arsenal | Raya, Gabriel, Rice | Fresh feed available; 13 Oct post-Lille original returned 403. PR128's Hincapie/Zubimendi claims not independently admitted. Exact Tuesday workload unresolved. |
| Chelsea | Palmer, João Pedro, Rogers | Available feed. Current club diary is scheduling/editorial content, not a medical clearance. No new dated owned-player health statement admitted. |
| City | Haaland, Semenyo, Guéhi, Anderson | Gallery/presser checked; PSG workload remains in the future. No fresh adverse claim accepted. |
| United | Bruno, Shaw, Obi | Shaw 75% and Obi unavailable confirmed in feed. Official Atlético report/lineup pages retrieved layout without usable bodies; no exact Tuesday minutes or recovery claim inferred. |
| Liverpool | Isak | Direct 13 Oct limitation accepted; Friday normal-start clearance absent. Gakpo/Szoboszlai mentioned by same source, not proposed replacements while limited. |
| Spurs | Van Hecke, Dubravka | Feed available; no new dated useful medical/role statement verified. Dubravka's available flag is not starting-goalkeeper status. |
| Fulham | Castagne | Green feed but GW6 zero minutes; no new statement establishing a GW7 start verified. |
| Brighton | Verbruggen; Groß, De Cuyper, Kostoulas | 10 Oct report and fresh feed; no new medical restriction verified. Club media-review quotations from journalists are not direct medical evidence. |
| Bournemouth | Truffert; Evanilson | 10 Oct official report; no newer useful medical statement located. |
| Brentford | Thiago | Fresh feed/GW6 minutes. Search returned older injury stories and a guest journalist preview; neither promoted as new medical evidence. |
| Everton | Dewsbury-Hall | [11 Oct Moyes reaction](https://www.evertonfc.com/news/2026/october/11/why-moyes-is--disappointed--by-hull-draw/) records match performance, not a new health claim. |
| Coventry | van Ewijk | 8 Oct training return plus 90 GW6 minutes; no later adverse statement verified. |
| Palace | Mitchell | 11 Oct direct match report; await European workload and next preview. |
| Forest | Gibbs-White; Aina | Palace official match report establishes historical use; no fresh direct Forest medical statement located. |
| Sunderland | Le Fée, Xhaka | Fresh feed; [2 Oct FPL tips](https://www.safc.com/news/2026/october/02/sunderland-fpl-tips-brobbey--xhaka-and-le-f-e-among-top-performers/) is Fantasy Football Scout partnership/editorial, not a new club medical statement. |
| Ipswich | Diop; Emersonn | Fresh feed; searches found squad, old team news and FPL naming editorial, not new medical/role assurance. |
| Leeds | Bogle, Calvert-Lewin | Fresh feed and six-match underlying data. Retrieved reports were older than current decision window; do not recycle as fresh health clearance. |
| Villa | N.Jackson | [10 Oct selection report](https://www.avfc.co.uk/news/2026/october/10/news-brentford-team-news/) and fresh feed; no later useful injury update verified. |

## Rejected or withheld interpretations

- **“Isak definitely misses GW7”**: not supported by the coach's uncertainty. Conversely, “not far away” is not normal-start clearance.
- **“All clubs fully cleared”**: unsupported. Missing body/search result is not a negative medical finding.
- **“Arsenal's latest medical claims independently verified”**: original inaccessible here. Retain as PR128 leads only.
- **“United's Tuesday minute totals verified”**: report/lineup bodies unavailable.
- **“PL injury index date clears all players”**: [index](https://www.premierleague.com/en/news/4450606/latest-premier-league-player-injuries-club-by-club-news/) shows 13 Oct 19:01 BST update, but no usable player body.
- **“Haaland's training photo confirms Saturday 90 minutes”**: appearance and workload are separate.
- **“Castagne available means he starts”**: contrary to the fitness/selection distinction.
- **“Semenyo 10.0 or Groß 10.0 ep_next is a sealed model forecast”**: mutable official game estimate, not calibrated multiweek exP.
- **“Kinsky/Cherki/Wissa are owned”**: contradicts public actual entry picks/history.
- **“Autosubbed Shaw proves the planned pre-deadline change was saved”**: contradicted by prior locked order.
- **Community TC/rotation/price claims**: discovery or adversarial inputs only; no medical admission.
- Old 2025 injury stories, undated search snippets, club-hosted media reviews and FFS partner advice are not new direct coach evidence.

## Decision and validation handoff

No immediate account changes. Hold Haaland-team transfers; evaluate Haaland TC only after Wednesday load and Friday health. No-Haaland Isak repair remains contingent; compare Evanilson and Calvert-Lewin rather than asserting a quantified winner. Captain proposals Haaland / Semenyo, vice João Pedro on both, subject to late evidence.

Before any action: verify authenticated free transfers, current bank, pending/confirmed moves, purchase/selling prices, transfer cost and saved XI/chip. Validate legal squad/formation, three-per-club and affordability after choosing a transfer. Public history cannot provide that private state.

The report carries legal provisional 3-4-3 and 4-5-1 selections (or 3-5-2 after a forward repair). It does not claim a validated, affordable transfer package, new sealed forecast, accepted canonical-ledger mutation or saved FPL change.
