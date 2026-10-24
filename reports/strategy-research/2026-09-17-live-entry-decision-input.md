# Live-entry decision input — 2026-09-17

**Status:** provisional advisory; no account changes executed  
**Observed at:** 2026-09-17T07:55:36Z  
**Next deadline:** 2026-09-18T17:30:00Z (18:30 UK)  
**Entries:** 8522487 and 7337262  
**Governing method:** `docs/plan.md`; official FPL state is authoritative for squad, history, prices and operational availability flags

## Material change since 2026-09-16

João Pedro changed from active to doubtful at 75% with an unspecified injury. The official FPL flag was added at 2026-09-16T19:00:09Z. Reuters reported at 2026-09-17T03:15:00Z that Brazil had replaced him for its forthcoming friendlies because of injury, but Chelsea had not published a dated in-window availability statement at the observation time.

This changes XI and captaincy risk for both live squads. It does not yet justify selling João Pedro before Chelsea's press conference because his GW6-GW8 fixtures remain useful and the injury severity is not known.

## Correction to PR #90

The primary strategy report again models a squad that entry 8522487 does not own: Kinsky, Cherki and Wissa appear in place of the official live players. It also treats the manager as likely to have one free transfer and does not analyse entry 7337262. Official history still shows only Wilson to Dewsbury-Hall in GW4 for entry 8522487.

PR #90 remains bound to `weekly-2026-08-11`; its deterministic and robust comparisons are not current GW5 comparisons. Keep the PR draft and do not act from its named squad, bank or transfer recommendation.

## Official manager state

| Entry | GW4 | Total | Current overall rank | Last-deadline value | Last-deadline bank | GW4 transfers | Chips |
|---|---:|---:|---:|---:|---:|---:|---|
| 8522487 | 61 | 241 | 5,538,587 | £99.4m | £0.3m | 1, no hit | none |
| 7337262 | 67 | 248 | 4,908,853 | £99.6m | £0.0m | 3, no hit | none |

Public endpoints do not expose private pending transfers, exact current free transfers, purchase prices or selling prices. Manager state therefore remains **degraded** until the authenticated transfer pages confirm those fields. Completed history is consistent with entry 8522487 having three free transfers and entry 7337262 one, if no GW5 transfer has been made, but those counts are not recorded as observed facts.

## Accepted current claims

| Player / claim | Source tier | Published or added | Implication |
|---|---|---|---|
| João Pedro doubtful, 75%, unspecified injury | official FPL bootstrap | 2026-09-16T19:00:09Z | remove captaincy; protect XI with playable first substitute; wait for Chelsea |
| Shaw doubtful, 75%, unspecified injury | official FPL bootstrap | 2026-09-11T13:00:09Z | do not rely on him without Friday clearance |
| Maatsen doubtful, 25%, ankle injury | official FPL bootstrap | 2026-09-12T18:00:08Z | primary no-Haaland transfer-out candidate |
| Obi unavailable after joining Willem II on loan | official FPL bootstrap | 2026-09-14T16:12:42Z | permanent dead third substitute |
| City will change the side against Norwich on 17 September | Manchester City official press conference report | 2026-09-16T12:00:00Z | wait for tonight's minutes for Haaland, Semenyo, Anderson and Guéhi |
| Foden is suspended for Norwich, Sunderland and Liverpool | Manchester City official preview | observed 2026-09-17 | increases attacking-role opportunity but is not enough to predict individual City starts |
| Manchester United lost 3-2 to Brighton in the cup | Manchester United official match report | 2026-09-16 | no recoverable official Shaw availability statement; bootstrap doubt remains operative |

## Corroborating but not ledger-admitted

Reuters reported that Brazil replaced João Pedro because of injury and that Brazil did not specify the injury. This corroborates the official FPL flag, but remains a wire report rather than a Chelsea official availability claim.

Community and X material continues to favour Haaland captaincy, debate GW5 versus GW6 Wildcards and highlight Bogle/Forest assets. It is challenge context only. No community claim is promoted to the evidence ledger.

## Rejected or quarantined claims

- The Kinsky/Cherki/Wissa live squad reconstruction in PR #90 is rejected against official entry history.
- The claimed bank derived from current buy prices is rejected because exact selling prices are private.
- “Catalogue coverage 21/21” is search coverage, not evidence coverage. The 17 September discovery report retained dated official leads from only five clubs and found no dated Chelsea or United injury original.
- João Pedro being definitely out of GW5 is not accepted. The official operational field is 75%, and Chelsea has not yet published a dated decision.
- Do not infer Shaw fitness from absence or presence in non-official line-up summaries.

## GW5 provisional decisions

### Entry 8522487 — Haaland structure

**Transfer:** hold today. Rolling all available transfers remains the base case. Do not sell João Pedro before Chelsea news.

**Provisional XI while João Pedro remains doubtful:**  
Verbruggen; Van Hecke, Mitchell, Diop; Bruno Fernandes, Gibbs-White, Dewsbury-Hall, Le Fée, Xhaka; Haaland, Thiago

**Bench:** Dubravka; 1 João Pedro, 2 van Ewijk, 3 Shaw  
**Captain:** Haaland  
**Vice-captain:** Bruno Fernandes

If Chelsea clears João Pedro for a normal start, restore a 3-4-3: João Pedro into the XI, Le Fée to first bench, and retain Haaland/Bruno as captain/vice.

Thiago to Wissa remains a valid GW5-GW8 comparison, not a locked move. Wissa has Hull, Coventry, Villa and Palace; Thiago has Chelsea, Villa, Liverpool and Hull. Thiago's underlying involvement is stronger, so a transfer must beat the option value of entering the international break with an additional free transfer.

If Shaw is ruled out for longer than GW5, compare Shaw to Ola Aina and Bogle after authenticated selling-price confirmation. No early move is justified this morning.

### Entry 7337262 — no-Haaland structure

The João Pedro flag creates a genuine squad-depth problem because Maatsen and Shaw are already doubtful and Obi is unavailable.

**Transfer today:** wait for Chelsea, United and Villa updates.  
**Provisional deadline move:** Maatsen to Castagne if João Pedro or Shaw remains a meaningful doubt. Castagne is active at £4.5m and has Manchester United, Ipswich, Hull and Coventry across GW5-GW8. If both João Pedro and Shaw are explicitly cleared, rolling remains defensible.

**Provisional XI after Maatsen to Castagne:**  
Raya; Gabriel, Guéhi, Castagne; Rogers, Palmer, Semenyo, Rice, Anderson; João Pedro, Isak

**Bench:** Verbruggen; 1 Truffert, 2 Shaw, 3 Obi  
**Captain:** Palmer  
**Vice-captain:** Rogers

Start João Pedro if he is not ruled out, with Truffert first substitute. Remove captaincy because of the added zero-minute and cameo uncertainty. Do not take a hit to replace Obi and do not force Haaland before GW5.

## Rolling four-Gameweek plan

- **GW5:** no chip. Haaland captain on entry 8522487; Palmer captain on entry 7337262 while João Pedro is doubtful.
- **GW6:** use the international break for a full availability reset. Banked transfers have elevated value. João Pedro versus Bournemouth and Bruno versus Spurs are captain candidates if fit.
- **GW7:** Haaland versus Ipswich remains the captain anchor. Reassess an entry-7337262 route to Haaland only with authenticated prices and multiple banked transfers.
- **GW8:** preserve flexibility around Chelsea, United and City roles rather than pre-committing.
- No current evidence supports Wildcard, Free Hit or Triple Captain in GW5.

## Remaining deadline checks

1. Tonight's official Manchester City XI, substitutions and post-match injury report for Haaland, Semenyo, Anderson and Guéhi.
2. Chelsea's dated João Pedro update and training/presser evidence.
3. United's dated Shaw update before Fulham.
4. Villa's dated Maatsen update before Spurs.
5. Authenticated transfer pages: exact free transfers, bank, selling prices and confirmation that no pending transfer exists.
6. Refresh official FPL status, prices and news timestamps after the final press conferences.
7. Deterministically validate the final transfer, club limits, XI, captain/vice and bench order.

## Sources

- Official FPL bootstrap: https://fantasy.premierleague.com/api/bootstrap-static/
- Entry 8522487 history: https://fantasy.premierleague.com/en/entry/8522487/history
- Entry 7337262 history: https://fantasy.premierleague.com/en/entry/7337262/history
- Manchester City cup preview: https://www.mancity.com/news/mens/city-v-norwich-match-preview-carabao-cup-63924970
- Manchester City selection comments: https://www.mancity.com/news/mens/enzo-maresca-norwich-embargo-preview-63925159
- Manchester United cup report: https://www.manutd.com/en/news/report-united-v-brighton-16-sep-2026
- Reuters João Pedro report: https://www.reuters.com/sports/soccer/chelseas-joao-pedro-out-brazils-friendlies-against-australia-india-with-injury-2026-09-17/
- Draft PR: https://github.com/Al2800/FPL/pull/90
- Previous X/community digest: reports/strategy-research/2026-09-16-x-community-digest.md
