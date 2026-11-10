# GW8 final decision and execution — 23 October 2026

## Authority and time boundary

This report supplements the 22 October verified checkpoint in PR #141. The user authorised relevant changes to both independent squads before the GW8 deadline. This was an execution request, not the separate daily read-only task.

- Review observed_at: 2026-10-23T14:08Z–14:22Z.
- Next deadline: GW8, 2026-10-23T17:30:00Z (18:30 BST), verified in official bootstrap.
- Outcome: entry 7337262 completed and saved; entry 8522487 not changed because its authenticated account was unavailable.
- No chip activated.

Do not substitute the older automated Kinsky/Cherki/Wissa reconstruction for the actual Haaland squad. Public historical picks cannot prove a pending or saved pre-deadline team.

## Material new evidence and decision change

The planned Calvert-Lewin purchase was rejected following fresh official injury news. The 14:08Z bootstrap showed Calvert-Lewin at £6.1m, doubtful, 50%, with a foot-injury news timestamp of 2026-10-23T13:00:09Z. Leeds' dated 23 October report says he had not returned to team training and remained doubtful. Evanilson replaced him in the purchase plan at the same £6.1m price.

Official sources reviewed:

| Source | published_at | Accepted evidence | Limitation |
|---|---|---|---|
| [FPL bootstrap](https://fantasy.premierleague.com/api/bootstrap-static/) | Dynamic endpoint; individual news timestamps retained where relevant | Deadline, current prices and flags; Tavernier £6.2m, Evanilson £6.1m and Davis £4.0m available; Semenyo and Shaw injured; DCL newly doubtful | Availability flag is not a medical clearance or guaranteed start |
| [Leeds fitness update](https://www.leedsunited.com/en/news/daniel-farke-gives-fitness-update-on-dominic-calvert-lewin-anton-stach-and-noah-okafor) | 23 October 2026 | Calvert-Lewin foot bruise and absence from team training | Sunday participation not completely excluded; insufficient certainty to buy |
| [Chelsea team news](https://www.chelseafc.com/en/news/article/xabi-alonso-confirms-chelsea-team-news-for-tottenham) | 23 October 2026 | No new concern reported for Palmer, João Pedro or Rogers in this update | Silence does not guarantee normal minutes |
| [Bournemouth Milan report](https://www.afcb.co.uk/news/2026/october/22/match-report-v-ac-milan/) | 22 October 2026 | Tavernier substituted after 62 minutes, Evanilson after 65; Truffert full match; Kluivert took first penalty and Tavernier second | Do not label Tavernier sole penalty taker |
| [Bournemouth Kroupi update](https://www.afcb.co.uk/news/2026/october/21/injury-news--rose-gives-update-on-kroupi-return/) | 21 October 2026 | Kroupi back in training | Future competition for minutes remains relevant |
| [Manchester United preview](https://www.manutd.com/en/news/how-to-watch-and-follow-united-v-bournemouth-25-oct-26) | Current 22–23 October preview | Shaw remains out | No evidence sufficient to sell Bruno over rumours |
| [Forest Gibbs-White update](https://www.nottinghamforest.co.uk/news/2026/october/21/team-news---gibbs-white-fit-to-return-against-ipswich/) | 21 October 2026 | Gibbs-White available again | Starting XI still subject to selection |
| [Manchester City press conference](https://www.mancity.com/news/mens/enzo-maresca-aston-villa-away-press-conference-written-63928256) | 22 October 2026 | Haaland availability supported | No guaranteed minutes assertion |

The Friday community live blog was used as a challenge input. Its report of Rose clearing Evanilson after a knock was not promoted to an independently verified official medical statement. A first-party Friday Bournemouth medical report was not located. Bruno-dropping rumours and reader speculation about weather postponements were not accepted as actionable evidence. The final Palace/Sunderland search returned stale or unrelated material and did not establish new medical clearance.

## Entry 7337262 — executed and verified

Authenticated identity was verified from the account's Points link. Before execution, UI showed three free transfers and £0.0m bank. Current selling values were Semenyo £8.3m, Shaw £4.3m and Obi £4.5m. No existing GW8 transfers were visible.

Confirmed transfer dialog:
- Semenyo → Tavernier (£6.2m)
- Obi → Evanilson (£6.1m)
- Shaw → Davis (£4.0m)

Three transfers, zero-point cost, £0.8m remaining. After confirmation, UI showed three GW8 transfers (seven season transfers), £99.1m squad value and £0.8m bank.

The team was then saved with Save Your Team and reloaded. Persisted pitch, captain/vice markers and bench order were directly observed; the save control was no longer present. This is execution evidence, not inference from public picks.

### Saved XI

Raya; Gabriel, Castagne, Guéhi; Rogers, Palmer (VC), Tavernier, Rice; Evanilson, João Pedro (C), Isak.

Bench: Verbruggen; 1 Truffert, 2 Anderson, 3 Davis.

No chip activated. Isak was retained as available; stale Isak-to-Evanilson advice was not followed. Evanilson replaced Obi.

### Why three rather than fewer transfers

Two moves could replace Semenyo and fund an Obi upgrade, but the extra free Shaw-to-Davis move replaces an injured defender, restores bench cover and releases additional bank. This was a four-week repair with zero hit, not a Wildcard trigger based on the count of unavailable players.

Bournemouth's GW8–11 run is MUN away, LEE home, IPS away, NFO home. The first fixture and Thursday-to-Sunday turnaround carry risk; the following three fixtures support Tavernier/Evanilson retention. They now use all three Bournemouth slots together with Truffert. Kroupi's return and Evanilson's minutes must be monitored.

Davis' GW8–11 run is NFO home, HUL away, BOU home, TOT away. He is bench cover initially, not a forced start.

## Entry 8522487 — not executed

Only the no-Haaland account was authenticated. The other available browser tab was blank. No authenticated Haaland account identity, current free-transfer count, current bank, selling prices or pending moves could be verified. No transfer, lineup, bench or captaincy change was submitted for this entry.

Manager state: degraded. The last private checkpoint (17 October: four free transfers, £0.2m bank) must not be rolled forward into an asserted current five free transfers.

Recommended manual action after checking the actual account's Transfers screen:
1. Verify entry 8522487, current FT, bank, Dewsbury-Hall selling price and any already-pending/confirmed GW8 move.
2. If the confirmation screen shows a free, affordable single move, Dewsbury-Hall → Tavernier is preferred. Do not take a hit solely for it.
3. Restore fit Gibbs-White and set the XI below.
4. Save, reload and verify captain, vice and bench.

Preferred XI with Tavernier:
Verbruggen; Castagne, Mitchell, van Ewijk; Bruno Fernandes, Gibbs-White, Le Fée, Tavernier; Haaland (C), João Pedro (VC), Thiago.

Bench: Dubravka; 1 Xhaka, 2 Diop, 3 Van Hecke.

If the transfer cannot be verified or completed without a hit: start Xhaka instead of Tavernier; bench Dewsbury-Hall first, then Diop and Van Hecke. Castagne/van Ewijk are preferred over Van Hecke away to Chelsea. Mitchell remains a minutes-monitoring concern, not a newly confirmed injury.

## Rolling plan and chips

- GW8: no-Haaland repair executed; Haaland single midfield improvement conditional on private-state verification. No hit or chip.
- GW9: evaluate Bournemouth minutes and Kroupi competition; use £0.8m flexibility on the no-Haaland side only when evidence justifies a move.
- GW10: reassess premium structure, captain options and defensive rotation; no predetermined sale.
- GW11: compare Haaland's Fulham fixture with other captain/chip windows using fresh minutes and fixture evidence. It is a candidate for review, not a Triple Captain commitment.

Wildcard is not justified simply by three unavailable players: free transfers repaired the no-Haaland squad. Bench Boost lacks a clearly strong 15-player return; Free Hit has no isolated fixture crisis to solve. Triple Captain should be compared with remaining first-half opportunities. Preserve all chips today and review their first-set expiry at GW19 against the official rules.

## Completion boundaries

7337262 is saved and verified. 8522487 requires account login and private-state confirmation; nothing was executed there. Report records only derived decision/execution facts. Raw endpoint responses, credentials, browser state and screenshots are excluded from the repository.
