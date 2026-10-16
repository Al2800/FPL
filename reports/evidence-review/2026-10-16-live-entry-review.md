# Official evidence review — 16 October 2026

## Timing and scope

- Entries: 8522487 and 7337262 only.
- Endpoint observed_at: **2026-10-16T07:12:48.85Z–07:12:52.74Z**.
- Official web observed_at: **16 October 2026, approximately 07:13–07:20 UTC**.
- Next deadline: **2026-10-17T10:00:00Z**, GW7.
- Main: `f2cdf06d93bc72eb9f96026a113edf343c0d87de`.
- No FPL account mutations, authenticated-state capture, raw-response commits or evidence-ledger writes.

Reviewed AGENTS; plan principles/rules/source governance; rules YAML; source registry; checkpoint manifest; weekly packet/checkpoint/gap panel; committed news triage/model review; yesterday's PR131; current PR132 strategy, live companion, news-discovery and model audit; 15 October X digest. The private-manager-state collector remains disabled; this is the explicitly requested bounded public cross-check, not a new collector or governance change.

Main's generation-0 manifest lacks a ledger binding. The 11 August packet is not a live GW7 forecast. PR132's draft ledger transition is `b5eece2a886a5575e7694f86cfc5888dac0706da685e76163acdf49ec5b4393d` → `6e57f02e39c48199d07fa0ab10f9f23acad530e4330af897f017b9633915b922`. Its four admissions and one rejection are audit metadata, not independent confirmation of every claim. Sixteen clubs have no fresh dated leads in that discovery run.

## Public endpoint evidence

Eleven requests succeeded:
- [Bootstrap](https://fantasy.premierleague.com/api/bootstrap-static/) and [fixtures](https://fantasy.premierleague.com/api/fixtures/): current prices, flags, both chances, news text/timestamp, mutable ep_next, deadlines and GW7–10 fixtures.
- [GW6 live](https://fantasy.premierleague.com/api/event/6/live/): final individual points and minutes.
- Entry [8522487](https://fantasy.premierleague.com/api/entry/8522487/) / [7337262](https://fantasy.premierleague.com/api/entry/7337262/): score/rank and last-deadline value/bank; unrelated profile fields excluded.
- History [8522487](https://fantasy.premierleague.com/api/entry/8522487/history/) / [7337262](https://fantasy.premierleague.com/api/entry/7337262/history/): completed scores, transfer counts/costs and chips.
- Picks [8522487](https://fantasy.premierleague.com/api/entry/8522487/event/6/picks/) / [7337262](https://fantasy.premierleague.com/api/entry/7337262/event/6/picks/): historical post-autosub order/leadership.
- Transfers [8522487](https://fantasy.premierleague.com/api/entry/8522487/transfers/) / [7337262](https://fantasy.premierleague.com/api/entry/7337262/transfers/): completed public moves only.

Mutable endpoint published_at is not exposed. news_added is retained separately; it is not necessarily the flag's latest modification. The snapshot is fresh, while Isak's 27 September news is old. Null chances mean unspecified. Public latest completed picks do not prove pending transfers, current free transfers, live selling prices or saved GW7 selections.

Programmatic comparison to yesterday's derived owned-player rows found no difference in price/status/chance/news timestamp/ep_next. News strings match. Final multipliers reproduce GW6 64/66. Rank changes are minor endpoint updates, not new match points. No top-1,000 refresh.

## Accepted, qualified and withheld claims

| Source / published_at | Evidence classification | Decision implication |
|---|---|---|
| [Liverpool Isak/Gakpo/Szoboszlai update](https://www.liverpoolfc.com/news/fitness-update-andoni-iraola-gakpo-isak-szoboszlai-changes-brentford), **15 Oct**; PR132 reports 11:21Z, exact clock not independently recovered | Direct coach quotation on official site: return chance open, Friday training still to come. ACCEPT qualified uncertainty, not normal-start clearance. | Material softening from unavailable in prior model to possible return; wait before Isak sale. Keep FPL i/0 alongside it. |
| [City Ipswich preview](https://www.mancity.com/news/mens/city-v-ipswich-town-match-preview-pl-17-october-63927580), **15 Oct** per repo metadata; exact timestamp not independently recovered | Official schedule explicitly states Friday 16 Oct **13:30 UK** press conference. ACCEPT schedule only. | Haaland/Semenyo/TC remain provisional before briefing. |
| [Brighton teamsheet](https://www.brightonandhovealbion.com/match-centre-lineups?gameId=2685825) and [timeline](https://www.brightonandhovealbion.com/match-centre?gameId=2685825), match **15 Oct**; publication clock not exposed | Official event record: Groß off57, De Cuyper on45, Kostoulas unused. Full-match Verbruggen inferred from XI and complete substitutions. ACCEPT workload. | No automatic goalkeeper switch or Brighton purchase; normal recovery assessment still needed. |
| [Palace Lyon report](https://www.cpfc.co.uk/news/match-reports/match-report-highlights-lyon-crystal-palace-october-2026/), **15 Oct 18:46:50.401Z** from page metadata | Official teamsheet has Mitchell starting with no substitution. ACCEPT full-match inference; no new injury claim. | Retain Mitchell, monitor short turnaround. |
| [City PSG report](https://www.mancity.com/news/mens/city-v-psg-14-october-match-report-63927601), match **14 Oct** | Haaland/Semenyo/Guéhi/Anderson start without listed substitution. ACCEPT historical workload; already known yesterday. | Does not remove Saturday rotation risk; reject opposite claim in primary strategy. |
| [PL suspension list](https://www.premierleague.com/en/news/4425344/which-players-are-suspended-or-close-to-a-ban-in-fantasy), published **12 Oct**, updated **14 Oct** | Disasi GW7, Gravenberch GW7, Bentancur GW7–9; none owned. Struijk red rescinded. ACCEPT disciplinary scope. | No owned-player ban established; Struijk fitness doubt remains distinct. |
| [Willem II Obi announcement](https://www.willem-ii.nl/artikel/willem-ii-huurt-chido-obi-van-manchester-united), **3 Sep** | Official season-long loan announcement; historical, corroborated by fresh FPL unavailable news. | Non-playing bench problem persists; not independently a reason for a hit. |
| [Chelsea Everton preview](https://www.chelseafc.com/en/news/article/everton-vs-chelsea-all-you-need-to-know-26-27), indexed this morning; exact publication not recovered | Search text discusses attack, not a medical clearance; original open failed. WITHHOLD fresh availability claim. | Palmer/João Pedro/Rogers remain available in FPL, not guaranteed starters. |
| [Bournemouth Sturm report](https://www.afcb.co.uk/news/2026/october/15/match-report-v-sturm/), URL dated **15 Oct**, search age inconsistent | Official headline/result lead found; body unavailable. WITHHOLD exact Evanilson/Truffert workload and medical inference. | Required check before Evanilson buy; no assumption of rest. |
| [Palace Sage reaction](https://www.cpfc.co.uk/news/first-team/sage-on-learning-lessons-after-palace-narrowly-edged-out-in-lyon/), PR132 metadata **15 Oct19:39:35Z** | Retrieved title only; Mateta return claim remains repo-reported, not independently admitted here. | No effect on owned Mitchell selection. |

No full quotations are reproduced. Admission here means accepted for this derived review, not written to the canonical ledger.

## Whole-squad and candidate coverage

All 27 unique owned players and nine comparison candidates received the fresh bootstrap check. Official-domain searches and/or cited official pages covered every group below. Search failure and absent news are **unknown**, not medical clearance. Friday briefings mostly remain ahead of the observation cutoff.

| Club | Owned / candidate players | Fresh official-news result or gap |
|---|---|---|
| City | Haaland, Semenyo, Guéhi, Anderson | Wednesday workload reverified; Friday13:30 briefing pending. |
| Chelsea | Palmer, João Pedro, Rogers | New preview indexed, body unavailable; old Everton line-up article rejected as wrong date. No new medical claim. |
| United | Bruno, Shaw, Obi | [Leeds preview](https://www.manutd.com/en/news/how-to-watch-and-follow-leeds-v-united-18-october) retrieved layout only. Community Bruno concern not confirmed; Shaw75 retained. Obi loan corroborated by receiving club. |
| Liverpool | Isak | New direct coach evidence above; possible return, not fit-to-start. |
| Arsenal | Raya, Gabriel, Rice | No fresh dated owned-player medical statement recovered; old fixtures/profiles and nonofficial Lille accounts not promoted. |
| Spurs | Van Hecke, Dubravka | Official profiles/training index, no new specific medical or keeper-role statement. |
| Coventry | van Ewijk | Club site/search yielded no usable new player update. Available feed remains, no independent fresh clearance. |
| Everton | Dewsbury-Hall | Preview headline found, no verified new medical restriction or role change. |
| Fulham | Castagne | News/ticket pages and old player interviews only. Starting-role uncertainty unresolved. |
| Brighton | Verbruggen; Groß, De Cuyper, Kostoulas | Thursday official minutes/substitutions verified above. Rest/unused status is not a Sunday selection promise. |
| Palace | Mitchell | Full Thursday involvement inferred from official final XI/substitutions. |
| Bournemouth | Truffert; Evanilson | Official Sturm headline found, full body unavailable; workload and Kluivert/Adli return details not admitted. |
| Brentford | Thiago | [Current Liverpool preview](https://www.brentfordfc.com/en/news/match-previews-brentford-v-liverpool-premier-league-17-10-2026) and new programme interview lead; no new Thiago medical restriction. Guest predictions are not coach evidence. |
| Forest | Gibbs-White; Aina | Results mainly old European squad material; no fresh actionable availability claim. |
| Sunderland | Le Fée, Xhaka | Official Torreense team-news index discovered but body/complete match minutes unavailable. Community substitutes report retained only as verification lead. |
| Ipswich | Diop; Emersonn | Official roster verified names; no fresh role/injury statement recovered. |
| Leeds | Bogle, Calvert-Lewin | Profiles and old match reports only; no new injury explanation or role guarantee. |
| Villa | N.Jackson | Official site/search no fresh candidate-specific medical statement. |

## Rejected inferences and missing inputs

- Reject Kinsky/Cherki/Wissa as actual ownership, estimated free transfers, or post-autosub picks as saved future selections.
- Reject automatic Triple Captain based on a brace or community agreement; full midweek minutes do not disprove weekend rest.
- Reject a medical clearance from suspension rescission. PR132 correctly rejects Struijk available while an unresolved physical doubt exists.
- Reject community price-rise probabilities, claimed 12% Haaland rest risk, Wildcard templates and unverified Kluivert/Kroupi return claims as official inputs.
- Reject future Friday statements not yet published; old-season material and crawl dates do not refresh old quotes.
- Exact Sunderland/Bournemouth Thursday minutes remain gaps. United and Chelsea current medical bodies were not available. No access restrictions were bypassed.
- Current calibrated GW7/four-week exP, licensed odds, approved ratings and complete fatigue inputs remain absent. Do not claim a numerical optimal-transfer gain.
- Manager state is degraded: authenticated FT, current bank, purchase/sale prices, pending/confirmed moves, hit preview, saved XI/bench/captain/vice/chip all require manual confirmation before action.

## Handoff

No immediate selection change; material Isak uncertainty update and new Brighton/Palace workload evidence. Keep the provisional no-transfer teams and Haaland/Semenyo captains with João Pedro vice. Reassess Isak replacement/defensive repair after Friday evidence. TC is a genuine comparison, not an instruction to activate. The companion report gives explicit conditional XI and four-week paths.

Only these two derived Markdown reports are proposed for Git. No raw endpoints, credentials, browser state, private extra identifiers, code/pipeline changes or ledger updates are included.


## Validation

The two no-transfer proposals were checked in code against the repository rules YAML: exactly the owned 15, required position counts, legal XI formations, maximum three per club, distinct starting captain/vice, and ordered four-player benches with goalkeeper first. Both pass. Transfer affordability, hits and saved-state validation remain blocked by unverified private manager state.
