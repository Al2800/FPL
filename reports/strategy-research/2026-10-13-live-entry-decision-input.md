# Official decision input — 13 October 2026

- Entries: 8522487 (Haaland), 7337262 (no Haaland).
- Official endpoint observed_at: 2026-10-13T07:31:05Z–07:31:11Z.
- Official-news review observed_at: 2026-10-13T07:30:00Z–07:45:00Z (review interval; individual publication dates retained below).
- Next deadline: **GW7, 17 October 2026 at 10:00 UTC / 11:00 BST**.
- Manager state: **live_faithful_degraded** for both entries. Public GW6 picks are verified; private GW7 transfer and selection state is not.
- Account changes: none. This is an advisory report, not a saved-team confirmation.
- Method: `AGENTS.md`, `docs/plan.md`, `control/rules/2026-27.yaml`; independent team optimisation, hold baseline, four-Gameweek horizon, point-in-time evidence.

## Material changes since 12 October

1. **Shaw is newly doubtful/75%**, with unspecified injury news added at 2026-10-12T21:30:08.995810Z. This materially weakens the no-Haaland team's defensive cover. It does not establish a diagnosis or GW7 absence.
2. **Van Ewijk returned for 90 minutes**, recorded an assist and six FPL points, and is now available/100% next round. His price fell £4.0m to £3.9m. This reduces the Haaland team's repair need. His old September news timestamp did not refresh when the flag cleared.
3. Every GW6 fixture is now `finished_provisional=true`, but every fixture still has `finished=false`, and the event is neither finished nor data checked. Automatic substitutions remain absent from both picks responses. Do not label projected totals final.
4. Liverpool's injury page was updated on 12 October, but the Isak quotation remains from 9 October. There is no fresh GW7 clearance. Newer comments concern difficult recovery ahead of the European trip; they do not prove Isak will miss Brentford.
5. Chip planning is now explicit. Haaland–Ipswich merits a GW7 Triple Captain comparison; the no-Haaland team merits a Wildcard-versus-repairs comparison. Neither chip is approved today.

## GW6 result and experiment audit

| Entry | Public GW6 points | Pending legal substitutions | Projected GW6 | Public total | Projected total | Public summary OR |
|---|---:|---|---:|---:|---:|---:|
| 8522487 | 62 | Diop +2 for Castagne | 64 | 354 | 356 | 4,623,705 |
| 7337262 | 64 | Truffert -1 and Shaw +3 for Castagne/Isak | 66 | 355 | 357 | 4,565,271 |

The average is currently 55. Projected scores are nine and eleven above that provisional average. The no-Haaland team remains projected one point ahead overall. The sampled overall table's `rank_sort=1000` has 489 points (displayed tied rank 995): projected gaps 133 and 132. This is a current boundary, not a forecast of the eventual top-1,000 target. No post-autosub rank is claimed. History OR is slightly stale at 4,623,714 / 4,565,280; the table uses the entry summary.

Van Ewijk's six bench points do not enter: Diop is ahead of him and supplies the only defender substitution needed. Xhaka cannot replace Castagne because the XI must retain three defenders. For the other team, both Truffert and Shaw enter legally in a 4-5-1.

The Haaland entry's locked GW6 XI matches the previously observed saved selection: João Pedro started, Haaland captain, Bruno vice. The no-Haaland entry retained Isak in the XI with Shaw second outfield bench; Palmer captain and Rogers vice are verified. The proposed Shaw-for-Isak change was not present in the locked picks. The two paths happen to converge on the same score because Castagne also did not play; this does not excuse the execution-verification failure. Public picks now establish the locked historical selection, not a pre-deadline save or the current GW7 XI.

The prior report's frozen official `ep_next` baselines were 57.5 for the Haaland XI, 52.6 for the actual no-Haaland XI and 53.6 for the proposed Shaw XI. Against projected 64/66/66, differences are +6.5/+13.4/+12.4. These are **uncalibrated official estimates**, not a sealed laboratory exP forecast; the XI estimates and realised autosub totals also have different bench scope. Preserve the comparison as descriptive only. João Pedro over Xhaka gained ten realised points; Palmer's doubled 16 beat Haaland's doubled 12. Do not rewrite the pre-deadline decision rationale using these outcomes.

## Public finances and history

| Entry | GW6 deadline value | GW6 deadline bank | GW6 transfers / cost | Chips used in public history |
|---|---:|---:|---|---|
| 8522487 | £99.4m | £0.2m | 0 / 0 | none |
| 7337262 | £99.7m | £0.0m | 0 / 0 | none |

Completed transfers remain Wilson → Dewsbury-Hall (GW4), Shaw → Castagne (GW5) for 8522487; Beto → Isak, Bruno → Palmer, Senesi → Maatsen (GW4), Maatsen → Castagne (GW5) for 7337262. No new completed transfer is exposed.

These finances are last-deadline snapshots. **Current free transfers, bank, pending transfers, purchase prices, selling prices and live chip selection are unverified.** Before action, each manager must expose the authenticated Transfers page showing those fields and resulting costs/bank for any proposal; the Pick Team page must confirm the saved XI, bench, captain and vice afterwards. Historical market prices are not selling prices. No account authentication was used in this review.

## Provisional GW7 selections, before transfers

### Haaland team

Verbruggen; Van Hecke, Mitchell, **van Ewijk**; Bruno, Gibbs-White, Le Fée, Dewsbury-Hall; João Pedro, Thiago, Haaland.

- Captain **Haaland**; vice **João Pedro**.
- Bench: Dubravka; **1 Xhaka, 2 Castagne, 3 Diop**.
- Van Ewijk's return now supplies a credible third defender. Castagne can return to the XI if Fulham evidence supports a start against Hull; one unused-bench appearance alone does not establish permanent loss of place. Do not describe Diop at Manchester City as automatically superior because he played last week.
- Default: hold transfers. Retain Bruno after one blank; the club's news index reports reassurance over fitness, but the article body was unavailable and no exact medical claim is admitted.

### No-Haaland team

Verbruggen; Gabriel, Guéhi, Truffert, Castagne; Rogers, Palmer, Semenyo, Rice, Anderson; João Pedro.

- Captain **Semenyo**; vice **João Pedro**. This revises yesterday's João Pedro captain preference: City's home match against Ipswich plus Semenyo's recovered 90-minute role makes him the provisional choice; Chelsea visit unbeaten Everton. This is football judgement, not a sealed projection or an instruction to save now. Review after European minutes.
- Bench: Raya; **1 Shaw, 2 Isak, 3 Obi**.
- Shaw's new doubt moves Truffert into the provisional XI. Castagne remains the uncertain eleventh starter; this is not a declaration that the squad is healthy.
- If Isak is still unavailable/limited on Friday, **Isak → Evanilson** is the leading four-week repair to price and validate. Start Evanilson, bench Castagne, and use a 3-5-2. If Isak is cleared for a normal start, keep him and compare repairing Castagne instead if his role remains poor.
- Compare Calvert-Lewin and Kostoulas before concluding Evanilson wins; there is no calibrated multiweek expected-points margin yet. Exact affordability and transfer cost must be verified.
- Obi is an unavailable bench slot, not an automatic hit. A Wildcard must beat feasible free-transfer repairs across 4–6 weeks, not just tidy the bench.

## Chips: when to consider them

The [official 2026/27 chip explainer](https://www.premierleague.com/en/news/4679879/whats-happening-with-fpl-chips-in-202627), published **20 July 2026** and checked today, confirms a first and second set of Wildcard, Free Hit, Triple Captain and Bench Boost. The first set can be used through GW19 and must be activated before **2 January 2027, 13:30 GMT**, the GW19 deadline. Unused chips do not carry forward; only one chip is allowed per Gameweek. A GW19 Free Hit prevents a second Free Hit in GW20.

| Chip | Haaland team | No-Haaland team | Decision gate |
|---|---|---|---|
| Triple Captain | **Evaluate GW7 Haaland v Ipswich now**, against later opportunities including GW16 Hull at home | Compare future owned captain opportunities; do not force an unaffordable Haaland route solely for a chip | Midweek load, Friday health and likely minutes, calibrated captain forecast versus best remaining first-half window |
| Wildcard | No current structural case after van Ewijk's return | **Prepare comparison this week**: Isak, Castagne, Shaw and non-playing Obi are repair concerns | Confirm private finances/FT, then compare best legal repairs with a durable 4–6 GW rebuild, including future transfer value and any hits |
| Bench Boost | Hold: Dubravka has not supplied a playing second keeper and Castagne's role is uncertain | Hold: Isak/Obi unavailable, Shaw doubtful | Four credible bench scorers; assess their marginal points after normal autosubs and preparation costs |
| Free Hit | Hold | Hold unless an exceptional one-week disruption makes temporary repair clearly superior | Large one-week gain over ordinary transfers; retain permanent assets needed afterwards |

Triple Captain adds **one extra copy** of the captain's points over normal captaincy. Today's mutable Haaland `ep_next=7.0` would suggest roughly seven additional points if used naively, not 21 incremental points. It is not sufficiently calibrated to approve a chip. Compare that marginal gain with the opportunity cost of saving it, not an arbitrary haul target. Likewise, an arbitrary count of three problems is not a Wildcard rule. Both teams can use different chips in different weeks: maximise each independently and preserve the evidence trail.

## Rolling GW7–GW10 direction

- **GW7, 17 October 11:00 BST:** confirm Isak/Shaw availability, Castagne role, European minutes; price repair/Wildcard alternatives. Haaland captain, Semenyo provisional captain on the other team; Haaland TC remains a candidate, not activated.
- **GW8, 23 October 18:30 BST:** Chelsea host Tottenham; retain the three Chelsea attackers unless evidence changes. City visit Villa. Avoid selling good long-term assets solely to fund a one-week chip.
- **GW9, 31 October 11:00 GMT:** City host Brighton, Chelsea host Manchester United. Bournemouth host Leeds, supporting Evanilson's potential multiweek value.
- **GW10, 6 November 18:30 GMT:** City visit Forest, Chelsea visit Sunderland, Bournemouth visit Ipswich. Reassess premium structure and defence with new minutes evidence.
- Keep the first-half chip calendar under review through GW19; do not save all four until the final weeks or assume a Double Gameweek will appear before expiry.

## Source freshness and limitations

Today's additional [draft PR126](https://github.com/Al2800/FPL/pull/126) was also reviewed: strategy briefing, live-entry companion and model evidence audit. Its separate advisory squad is not either owned team. The live-entry companion correctly identifies the actual squads and new flags, but its 62/64 sample excludes pending autosubs, and João Pedro was already in the XI rather than acting as Isak's bench cover. Its recommendation to prefer TC now and move Dewsbury-Hall/Le Fée to Groß remains a challenge to assess, not an executed decision. Its unmerged audit reports four accepted claims (Palace starters, Arsenal absences for Lille), with tip `a562be38680047bb1986b805de47f4746ea0c3c62de376017e5d2067457dae12`; this is distinct from the stale main checkpoint. The Arsenal original was inaccessible on our independent fetch, so no additional medical claim is admitted here.

Groß (£6.0m, available, null chances/news timestamp, 540 minutes/6 starts, ep_next 12.3) and De Cuyper (£5.1m, available, null chances/news timestamp, 490 minutes/6 starts, ep_next 10.7) are legitimate comparison candidates from the official snapshot. Their news strings are empty. Both share Brighton's CRY H / LIV A / MCI A / BRE H sequence. The [9 October Brighton preview](https://www.brightonandhovealbion.com/media-article/mft-match-preview-sunderland-bha-pl-october-2026) supports Groß's creative involvement. A hot one-week estimate is insufficient to sell Dewsbury-Hall or force a funding move before comparing the next four weeks and confirmed sale values.

The [Scout's chip article, published 11 October](https://www.premierleague.com/en/news/4362085/triple-captain-haaland-in-gameweek-7-how-and-when-to-use-your-fpl-chips), independently highlights Haaland GW7 and later Chelsea GW17–18 captain opportunities. That makes the no-Haaland team's existing Palmer/João Pedro holdings a plausible later TC route; it does not require a rushed Haaland pivot. The article is official editorial advice, not a calibrated forecast or a chip instruction.

The governing main commit is `4daa2e665da14aae506462b63a1adf15f5bb3b95`. The canonical checkpoint is still generation 0 without a ledger binding. The weekly packet (11 August), committed triage (17 August), and latest committed model evidence audit (19 September) are stale for GW7. No new sealed weekly forecast is claimed. Yesterday's draft [PR125](https://github.com/Al2800/FPL/pull/125) and today's latest committed [12 October community digest](https://github.com/Al2800/FPL/blob/main/reports/strategy-research/2026-10-12-x-community-digest.md) were reviewed. Community price/TC/rotation chatter is discovery input only. This report supersedes yesterday's availability and provisional selection state, not its frozen forecast history.

The companion evidence review records acceptance limits and player coverage. No unverified claim is promoted to the canonical ledger. Official FPL news timestamps can lag flag changes; null chance fields do not mean guaranteed availability. A club article's update date does not refresh an older quotation inside it. Future team news may still change the plan before Saturday.

## Derived official snapshot

The following tables are selected, derived fields, not raw endpoint dumps. `a/d/i/u` mean available/doubtful/injured/unavailable. Chances are **this round / next round** exactly as exposed, with null left unspecified. Current `ep_next` is recorded for audit only. News timestamps retain source precision.

### Entry 8522487

| Player | £m | Status | Chance this / next | news_added UTC | GW6 min / pts | ep_next |
|---|---:|---|---|---|---|---:|
| Verbruggen | 4.5 | a | null / null | null | 90 / 9 | 7.7 |
| Van Hecke | 4.9 | a | 100 / 100 | 2026-09-30T16:00:09.552205Z | 90 / 3 | 4.5 |
| Mitchell | 4.5 | a | null / null | null | 90 / 4 | 5.5 |
| Castagne | 4.5 | a | null / null | null | 0 / 0 | 0.5 |
| B.Fernandes | 11.9 | a | null / null | null | 90 / 1 | 1.7 |
| Gibbs-White | 8.0 | a | 100 / 100 | 2026-08-24T15:30:08.350159Z | 90 / 2 | 2.0 |
| E.Le Fée | 5.7 | a | null / null | null | 80 / 2 | 3.5 |
| Dewsbury-Hall | 6.6 | a | null / null | null | 90 / 13 | 8.0 |
| João Pedro | 7.8 | a | 100 / 100 | 2026-09-16T19:00:09.919929Z | 71 / 12 | 6.0 |
| Thiago | 7.8 | a | null / null | null | 90 / 4 | 4.5 |
| Haaland | 15.6 | a | null / null | null | 79 / 6 | 7.0 |
| Dubravka | 4.0 | a | null / null | null | 0 / 0 | 0.0 |
| Xhaka | 5.4 | a | null / null | null | 90 / 2 | 2.0 |
| Diop | 4.0 | a | null / null | null | 90 / 2 | 3.0 |
| van Ewijk | 3.9 | a | 75 / 100 | 2026-09-19T16:00:09.486751Z | 90 / 6 | 2.0 |

### Entry 7337262

| Player | £m | Status | Chance this / next | news_added UTC | GW6 min / pts | ep_next |
|---|---:|---|---|---|---|---:|
| Raya | 6.1 | a | null / null | null | 90 / 3 | 2.0 |
| Gabriel | 7.9 | a | null / null | null | 90 / 2 | 1.5 |
| Castagne | 4.5 | a | null / null | null | 0 / 0 | 0.5 |
| Guéhi | 6.0 | a | null / null | null | 90 / 6 | 5.3 |
| Rogers | 7.9 | a | null / null | null | 83 / 9 | 5.5 |
| Palmer | 9.7 | a | 100 / 100 | 2026-09-21T13:00:09.022726Z | 87 / 8 | 5.0 |
| Semenyo | 8.3 | a | 75 / 100 | 2026-09-24T12:00:09.848000Z | 90 / 3 | 7.7 |
| Rice | 7.3 | a | 75 / 100 | 2026-09-21T13:00:08.896379Z | 90 / 7 | 4.0 |
| Anderson | 6.3 | a | 100 / 100 | 2026-08-23T17:00:07.952697Z | 90 / 6 | 4.3 |
| João Pedro | 7.8 | a | 100 / 100 | 2026-09-16T19:00:09.919929Z | 71 / 12 | 6.0 |
| Isak | 9.0 | i | 0 / 0 | 2026-09-27T10:30:09.051435Z | 0 / 0 | 0.0 |
| Verbruggen | 4.5 | a | null / null | null | 90 / 9 | 7.7 |
| Truffert | 5.4 | a | null / null | null | 83 / -1 | 0.5 |
| Shaw | 4.3 | d | 100 / 75 | 2026-10-12T21:30:08.995810Z | 90 / 3 | 1.3 |
| Obi | 4.5 | u | 0 / 0 | 2026-09-14T16:12:42.090874Z | 0 / 0 | 0.0 |

Non-empty owned news: Shaw — unspecified injury, 75%; Isak — thigh injury, unknown return; Obi — loan to Willem II for the season. All other owned news strings are empty.

### Repair candidates — discovery, not approved transfers

| Player | £m | Status; chances this/next | news_added | Season mins / starts | ep_next | GW7–10 |
|---|---:|---|---|---|---:|---|
| Evanilson | 6.0 | a; null/null | null | 514 / 6 | 4.5 | SUN H; MUN A; LEE H; IPS A |
| Kostoulas | 5.7 | a; null/null | null | 412 / 5 | 7.0 | CRY H; LIV A; MCI A; BRE H |
| Emersonn | 5.6 | a; 100/100 | 2026-08-31T09:30:08.306145Z | 387 / 6 | 2.0 | MCI A; NFO H; HUL A; BOU H |
| N.Jackson | 6.6 | a; null/null | null | 376 / 5 | 7.5 | NEW A; MCI H; FUL H; MUN A |
| Calvert-Lewin | 6.0 | a; null/null | null | 509 / 6 | 4.7 | MUN H; SUN A; BOU A; TOT H |
| Aina | 4.4 | a; null/null | null | 388 / 5 | 0.0 | ARS H; IPS A; BRE A; MCI H |
| Bogle | 4.7 | a; null/null | null | 450 / 6 | 7.0 | MUN H; SUN A; BOU A; TOT H |

Candidate news strings are empty. Kostoulas rose from £5.6m in yesterday’s snapshot to £5.7m; the only owned price change is van Ewijk to £3.9m. Aina/Bogle are defender comparison candidates only, not declared affordable replacements.

### Owned-club four-week fixtures

| Club | GW7 | GW8 | GW9 | GW10 |
|---|---|---|---|---|
| ARS | NFO A | EVE H | LIV A | HUL H |
| BHA | CRY H | LIV A | MCI A | BRE H |
| BOU | SUN H | MUN A | LEE H | IPS A |
| BRE | LIV H | HUL A | NFO H | BHA A |
| CHE | EVE A | TOT H | MUN H | SUN A |
| COV | TOT A | FUL H | SUN H | EVE A |
| CRY | BHA A | NEW H | TOT A | LIV H |
| EVE | CHE H | ARS A | NEW A | COV H |
| FUL | HUL H | COV A | AVL A | NEW H |
| IPS | MCI A | NFO H | HUL A | BOU H |
| LIV | BRE A | BHA H | ARS H | CRY A |
| MCI | IPS H | AVL A | BHA H | NFO A |
| MUN | LEE A | BOU H | CHE A | AVL H |
| NFO | ARS H | IPS A | BRE A | MCI H |
| SUN | BOU A | LEE H | COV A | CHE H |
| TOT | COV H | CHE A | CRY H | LEE A |

## Official data references

- [Bootstrap, deadlines, prices, flags and game estimates](https://fantasy.premierleague.com/api/bootstrap-static/)
- [Fixtures](https://fantasy.premierleague.com/api/fixtures/) and [GW6 live player scoring](https://fantasy.premierleague.com/api/event/6/live/)
- [8522487 summary](https://fantasy.premierleague.com/api/entry/8522487/), [history/chips](https://fantasy.premierleague.com/api/entry/8522487/history/), [transfers](https://fantasy.premierleague.com/api/entry/8522487/transfers/), [GW6 picks](https://fantasy.premierleague.com/api/entry/8522487/event/6/picks/), [completed GW5 picks](https://fantasy.premierleague.com/api/entry/8522487/event/5/picks/)
- [7337262 summary](https://fantasy.premierleague.com/api/entry/7337262/), [history/chips](https://fantasy.premierleague.com/api/entry/7337262/history/), [transfers](https://fantasy.premierleague.com/api/entry/7337262/transfers/), [GW6 picks](https://fantasy.premierleague.com/api/entry/7337262/event/6/picks/), [completed GW5 picks](https://fantasy.premierleague.com/api/entry/7337262/event/5/picks/)
- [Sampled top-1,000 boundary](https://fantasy.premierleague.com/api/leagues-classic/314/standings/?page_standings=20)
