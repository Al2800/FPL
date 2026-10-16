# Official evidence review — 15 October 2026

## Timing, scope and provenance

- Entries: 8522487 and 7337262.
- Endpoint observed_at: **2026-10-15T07:45:00.32Z–07:45:08.91Z**.
- Official web review observed_at: **15 October 2026, approximately 07:43–07:50 UTC**. Publication dates below refer to sources, not crawl times.
- Decision deadline: **2026-10-17T10:00:00Z** (GW7).
- Main commit: `5184fbb39b6001a91dddd09bf933673f1c9d88c8`.
- No account changes, authentication, raw-response commits or canonical ledger writes.

Reviewed current repository rules/plan, source registry, canonical manifest, weekly packet/gap panel, committed triage/model audit, prior PR129, current PR130 strategy/live-entry companion/news discovery/model audit, and committed 14 October X digest. The August packet and September committed review are stale for GW7. Draft ledger b5eece2a… is distinct from main's generation-0 checkpoint. No calibrated current model is claimed.

## Public data capture

Eleven direct public requests succeeded: bootstrap, fixtures, GW6 live, and entry/history/transfers/GW6 picks for each supplied ID.

- [Bootstrap](https://fantasy.premierleague.com/api/bootstrap-static/): prices, status, both chances, news timestamp/text, ep_next and event deadlines/finalisation.
- [Fixtures](https://fantasy.premierleague.com/api/fixtures/): GW7–10 opponents and kickoff schedule.
- [GW6 live](https://fantasy.premierleague.com/api/event/6/live/): individual final points/minutes.
- Entry [8522487](https://fantasy.premierleague.com/api/entry/8522487/) / [7337262](https://fantasy.premierleague.com/api/entry/7337262/): public score/rank only; profile fields excluded.
- History [8522487](https://fantasy.premierleague.com/api/entry/8522487/history/) / [7337262](https://fantasy.premierleague.com/api/entry/7337262/history/): completed scores, bank/value snapshots, transfer cost, chip history.
- Picks [8522487](https://fantasy.premierleague.com/api/entry/8522487/event/6/picks/) / [7337262](https://fantasy.premierleague.com/api/entry/7337262/event/6/picks/): post-autosub historical squad/order/leadership.
- Transfers [8522487](https://fantasy.premierleague.com/api/entry/8522487/transfers/) / [7337262](https://fantasy.premierleague.com/api/entry/7337262/transfers/): completed public moves; no private pending-state inference.

Mutable endpoint published_at/finalised_at timestamps are not exposed; observed_at is recorded, and GW6 finished/data_checked flags establish its final status as observed. News timestamps are retained individually. Scoring reconstruction from official individual points and multipliers verifies 64/66. No top-1,000 table was refreshed today.

## Accepted and qualified claims

| Source / published_at | Accepted scope | Limit |
|---|---|---|
| [City–PSG official report](https://www.mancity.com/news/mens/city-v-psg-14-october-match-report-63927601), 14 Oct; PR130 metadata 20:59Z (exact timestamp not independently extracted here) | Haaland, Semenyo, Guéhi, Anderson start and have no listed substitution; Haaland scores twice. Full-match involvement inferred from complete teamsheet. | Does not establish Saturday starts, normal minutes or absence of delayed injury. |
| [Brighton European preview](https://www.brightonandhovealbion.com/media-article/mft-match-preview-bha-kauno-zalgiris-uefa-conference-league-october-2026), **14 Oct 13:20Z**, directly displayed | Coach confirms Thursday changes to manage energy; Struijk out Thursday, hopeful for weekend. | No specific Verbruggen/Groß/De Cuyper/Kostoulas minutes guarantee; hope is not clearance. |
| [PL suspension list](https://www.premierleague.com/en/news/4425344/which-players-are-suspended-or-close-to-a-ban-in-fantasy), published 12 Oct, updated **14 Oct** | Disasi GW7, Gravenberch GW7, Bentancur GW7–9. None owned. Struijk red rescinded. | Disciplinary eligibility is separate from fitness. Community's unnamed-four-bans claim not adopted. |
| [Liverpool availability list](https://www.liverpoolfc.com/news/liverpools-injury-list-suspensions-and-availability), displayed about 12 Oct | Confirms Gravenberch's Brentford ban; contains older Isak quote dated 9 Oct. | Does not refresh Isak medical evidence; retain the newer 13 Oct LASK source from prior review. |
| Official bootstrap, observed today | Owned prices/flags/chances/news/ep_next unchanged. Bogle/Calvert-Lewin ep_next fall without medical change. | Mutable estimates are not a calibrated injury or performance forecast. |

The fresh Liverpool search found no later dated GW7 clearance than the [13 October LASK comments](https://www.liverpoolfc.com/news/lask-v-liverpool-champions-league-team-news) reviewed yesterday: limited training and uncertain return. No definite GW7 exclusion is asserted.

## Whole-squad and candidate search coverage

Every owned player received a fresh official FPL snapshot check. Official-domain searches covered the groups below for injury, return, suspension, role and press-conference evidence. Empty results mean **unknown**, not fit or guaranteed to start.

| Club | Players covered | Finding / gap |
|---|---|---|
| City | Haaland, Semenyo, Guéhi, Anderson | New workload evidence above; Friday selection remains open. |
| Chelsea | Palmer, João Pedro, Rogers | Searches returned 9–10 Oct clearance/selection and older role interviews, not a new GW7 restriction or normal-minutes promise. |
| United | Bruno, Shaw, Obi | [Post-Atlético feature](https://www.manutd.com/en/news/feature-after-atletico-madrid-v-man-utd-13-oct-2026) indexed Shaw non-travel and Bruno involvement, but open returned layout only; date/body not fully verified. Withhold new exact minutes/medical claim. Feed remains Bruno available, Shaw 75%, Obi loan-unavailable. |
| Liverpool | Isak | No fresh normal-start clearance found. Retain 13 Oct limitation and official 0% flag; Friday gate remains. |
| Arsenal | Raya, Gabriel, Rice | Current feed available; official search mostly old/mismatched reports. No new dated owned-player medical claim or exact Lille workload admitted. |
| Spurs | Van Hecke, Dubravka | [9 Oct update](https://www.tottenhamhotspur.com/news/1175437/team-news-van-de-ven-van-hecke-available-for-old-trafford) supports historical Van Hecke availability, not a new GW7 statement. No starting-goalkeeper inference for Dubravka. |
| Fulham | Castagne | Search returned fixture/ticket material, no new starting-role statement. Green flag does not remove selection concern. |
| Brighton | Verbruggen; Groß, De Cuyper, Kostoulas | Fresh rotation statement above; wait for Thursday actual usage. |
| Bournemouth | Truffert; Evanilson | [10 Oct Chelsea report](https://www.afcb.co.uk/news/2026/october/10/chelsea-afc-bournemouth-match-report-october-2026/) records historical selection. No newer verified adverse medical claim. |
| Brentford | Thiago | [14 Oct preview](https://www.brentfordfc.com/en/news/match-previews-brentford-v-liverpool-premier-league-17-10-2026) mixes club context and guest analysts; no new Thiago medical limitation established. Guest prediction that Isak starts if fit is not a coach assurance. |
| Everton | Dewsbury-Hall | New preview headline/index and 11 Oct reaction; no dated medical restriction verified. |
| Coventry | van Ewijk | [8 Oct return-to-training](https://www.ccfc.co.uk/news/2026/october/08/frank-lampard-provides-injury-update-ahead-of-newcastle-united-clash/) remains historical support, with GW6 90 minutes. No new adverse evidence. |
| Palace | Mitchell | [14 Oct Lyon press conference](https://www.cpfc.co.uk/news/first-team/sage-press-conference-lyon-palace-pre-match/) opened title/date only. PR130 Mateta claim not independently promoted; Mitchell's Thursday usage still pending. |
| Forest | Gibbs-White; Aina | [11 Oct team news](https://www.nottinghamforest.co.uk/news/2026/october/11/team-news---one-change-for-palace-matchup/) records starts, not fresh GW7 clearance. |
| Sunderland | Le Fée, Xhaka | [10 Oct team news](https://www.safc.com/news/2026/october/10/le-bris-makes-three-sunderland-changes/) and Le Fée interview; no new limitation. Older February Bournemouth injury article rejected as stale. |
| Ipswich | Diop; Emersonn | Search produced FPL naming editorial/old team information; no fresh usable medical claim. |
| Leeds | Bogle, Calvert-Lewin | [10 Oct Arsenal report](https://www.leedsunited.com/en/news/leeds-united-run-premier-league-champions-arsenal-close-in-tight-emirates-defeat) confirms historical selection; no medical reason verified for estimate fall. |
| Villa | N.Jackson | [10 Oct team news](https://www.avfc.co.uk/news/2026/october/10/news-brentford-team-news/) only useful dated result; no newer restriction verified. |

## Rejections and research limitations

- Reject PR130's inference that a PSG brace clears Haaland's weekend rest risk. Historical performance and future expected minutes are different variables.
- Reject automatic TC activation, forced Groß purchase, and a Wildcard triggered solely by three concerns. Compare legal, affordable alternatives over several weeks.
- Reject interpretation of post-autosub rows as saved GW7 XI or proof that Shaw was manually started before GW6.
- Reject unverified community bans, price predictions, rotation guesses and numerical start probabilities as official evidence.
- Reject old-season articles and page-update dates used to refresh older quotations.
- Withhold precise United/Arsenal midweek workloads and Palace medical claims where original bodies were not available.
- PR130's five accepted model claims do not equal complete fresh coverage; its discovery document itself lists 14 clubs without dated eligible leads.
- New screenshots or authenticated state were not available. Public picks cannot prove pre-deadline saved state.
- No new raw collector, pipeline, source-registry change or ledger admission is included. This is the specifically requested bounded public read and derived report.

## Decision handoff

No immediate decision change. Retain provisional Haaland/Semenyo captains, João Pedro vice on both; conditional Isak repair comparison, no chip activation. Tomorrow's evidence should resolve City workload/selection, Liverpool Isak, United Shaw, Fulham Castagne and Thursday European appearances.

Manual confirmation required: current FT, bank, pending/confirmed moves, purchase/selling prices, proposed cost and saved XI/bench/captain/vice/chip for each entry. These remain degraded and block claims of affordability or execution. Historical scores verified; current forecast quality remains limited by stale packet and absent calibrated multiweek projections.
