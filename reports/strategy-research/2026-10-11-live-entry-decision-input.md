# Live GW6 decision input — 11 October 2026

- official FPL observed_at: 2026-10-11T07:47:00Z–2026-10-11T07:49:00Z
- official-news review observed_at: 2026-10-11T07:49:00Z–2026-10-11T07:52:37Z
- GW6 state: live and provisional; six fixtures played, three on 11 October and one on 12 October
- next_deadline: 2026-10-17T10:00:00Z / 11:00 BST (GW7)
- entries: 8522487 (Haaland), 7337262 (no Haaland)
- method: `AGENTS.md`, `docs/plan.md`, point-in-time official evidence, hold baseline and rolling four-Gameweek review
- account writes: false
- manager state: GW6 selections now public and verifiable; **GW7 private state remains live_faithful_degraded**

## Material update

GW6 public picks now resolve yesterday's execution uncertainty.

- **8522487:** the public GW6 picks exactly match the directly observed 9 October save: João Pedro starts instead of Xhaka, Haaland is captain, Bruno Fernandes vice-captain, and the bench is Dubravka; Xhaka, Diop, van Ewijk.
- **7337262:** Palmer captain, Rogers vice and João Pedro retained were saved, but Shaw did not replace Isak. The XI retains Isak; the bench is Verbruggen; Truffert, Shaw, Obi.
- No GW6 transfer or chip was used by either entry.

The missed no-Haaland selection is currently **points-neutral against the recommended XI**. Castagne also recorded zero minutes, so, assuming Isak remains at zero as officially ruled out, Truffert (-1) and Shaw (3) should both enter. The recommended XI would have started Shaw and received Truffert for Castagne: the same net +2. Automatic substitutions are not final until the Gameweek finishes.

No transfer or chip action is possible or desirable while GW6 remains open. The next decision is GW7, not a retrospective attempt to repair GW6.

## Live position

Official entry summaries and live element scoring currently disagree slightly with the embedded 8522487 `entry_history` object (31/323 versus 29/321). The element sum and entry summary both support 31/323, so that is used provisionally. Scores, bonus, substitutions and ranks can still change.

| Entry | Arm | Live GW6 raw | Projected autosub effect | Provisional post-autosub | Live total | Current OR | Gap to live rank-1,000 score (477) |
|---|---|---:|---:|---:|---:|---:|---:|
| 8522487 | Haaland | 31 | +2 (Diop for Castagne) | 33 | 323 | 5,559,602 | 154 |
| 7337262 | no Haaland | 49 | +2 (Truffert and Shaw for Castagne and Isak) | 51 | 340 | 4,334,732 | 137 |

The top-1,000 boundary is a fresh live sample, not a final GW6 target. Four starters remain for 8522487 (Mitchell, Gibbs-White, Dewsbury-Hall and captain Haaland); three remain for 7337262 (Guéhi, Semenyo and Anderson). Coventry play on Monday, so van Ewijk's bench availability may still matter if the Haaland entry loses a second starting defender.

## Saturday returns and role evidence

| Player | Minutes | Raw points | Decision observation |
|---|---:|---:|---|
| João Pedro | 71 | 12 | Two goals and two bonus. Starting him over Xhaka has already gained 10 points on 8522487. Retain toward Chelsea's strong GW7–GW10 run, subject to recovery news. |
| Palmer | 87 | 8 | Two assists; captain produced 16. Friday's availability evidence was borne out. Captain comparison with Haaland is unfinished. |
| Rogers | 83 | 9 | One goal and 13 defensive contributions. Vice-captain choice was viable; do not chase the outcome by changing the process. |
| Rice | 90 | 7 | One assist and two bonus; Friday's reported availability was borne out. |
| Verbruggen | 90 | 9 | Clean sheet and two bonus. Correct goalkeeper for 8522487; his nine points remain benched on 7337262. |
| Thiago | 90 | 4 | One assist; retain while reviewing Brentford's GW7 Liverpool fixture and later Hull/Forest games. |
| Van Hecke | 90 | 3 | Started after the Friday clearance; yellow card, but defensive contributions rescued an extra point. |
| Shaw | 90 | 3 | Available and completed the match. Expected to autosub for 7337262 if both Castagne and Isak finish at zero. |
| Bruno Fernandes | 90 | 1 | Blank plus yellow card. One result does not establish a role change; review underlying role before GW7. |
| Castagne | 0 | 0 | Did not appear despite an available FPL status. This elevates defender reliability as a GW7 review item. |

## Verified GW6 selections

### 8522487 — Haaland

**XI:** Verbruggen; Van Hecke, Mitchell, Castagne; Bruno Fernandes, Gibbs-White, Le Fée, Dewsbury-Hall; João Pedro, Thiago, Haaland.

- Captain: Haaland; vice: Bruno Fernandes.
- Bench: Dubravka; 1 Xhaka, 2 Diop, 3 van Ewijk.
- Expected substitution: Diop for Castagne. Xhaka cannot replace Castagne because that would leave only two starting defenders.
- This validates the historical Team Saved observation. It does not prove any current authenticated GW7 state.

### 7337262 — no Haaland

**XI:** Raya; Gabriel, Castagne, Guéhi; Rogers, Palmer, Semenyo, Rice, Anderson; João Pedro, Isak.

- Captain: Palmer; vice: Rogers.
- Bench: Verbruggen; 1 Truffert, 2 Shaw, 3 Obi.
- Expected substitutions: Truffert for Castagne, then Shaw for Isak, producing a legal 4-5-1.
- Selection execution was incomplete, although the realised autosub path currently neutralises the error.

## Public financial, transfer and chip state

| Entry | GW6 deadline value | GW6 deadline bank | GW6 transfers | GW6 cost | Chips used through GW6 |
|---|---:|---:|---:|---:|---|
| 8522487 | £99.4m | £0.2m | 0 | 0 | none |
| 7337262 | £99.7m | £0.0m | 0 | 0 | none |

These are deadline snapshots exposed in the public entry and picks endpoints. They are not authenticated current banks or selling-price schedules. Current free transfers, pending GW7 moves, purchase prices and selling prices remain private and must not be inferred.

Completed transfer history is unchanged:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, Bruno Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

## Owned prices, status fields and source timestamps

`news_added` is the official feed field, not necessarily the timestamp of the latest flag change. `null` chance means unspecified, not 100%. `ep_next` is the mutable official GW7 estimate, not the laboratory's calibrated forecast.

| Entry | Player | Club | Price | Status | Chance this/next | news_added UTC | Current news | ep_next |
|---|---|---|---:|---|---|---|---|---:|
| 8522487 | Verbruggen | BHA | £4.5m | a | null/null | null | empty | 7.7 |
| 8522487 | Van Hecke | TOT | £4.9m | a | 100/100 | 2026-09-30T16:00:09Z | empty | 5.7 |
| 8522487 | Mitchell | CRY | £4.5m | a | null/null | null | empty | 2.7 |
| 8522487 | Castagne | FUL | £4.5m | a | null/null | null | empty | 2.3 |
| 8522487 | Bruno Fernandes | MUN | £11.9m | a | null/null | null | empty | 1.7 |
| 8522487 | Gibbs-White | NFO | £8.0m | a | 100/100 | 2026-08-24T15:30:08Z | empty | 3.3 |
| 8522487 | Le Fée | SUN | £5.7m | a | null/null | null | empty | 2.3 |
| 8522487 | Dewsbury-Hall | EVE | £6.6m | a | null/null | null | empty | 1.7 |
| 8522487 | João Pedro | CHE | £7.7m | a | 100/100 | 2026-09-16T19:00:09Z | empty | 8.0 |
| 8522487 | Thiago | BRE | £7.8m | a | null/null | null | empty | 3.3 |
| 8522487 | Haaland | MCI | £15.6m | a | null/null | null | empty | 5.0 |
| 8522487 | Dubravka | TOT | £4.0m | a | null/null | null | empty | 0.0 |
| 8522487 | Xhaka | SUN | £5.4m | a | null/null | null | empty | 1.7 |
| 8522487 | Diop | IPS | £4.0m | a | null/null | null | empty | 2.3 |
| 8522487 | van Ewijk | COV | £4.0m | d | 75/75 | 2026-09-19T16:00:09Z | hamstring, 75% | 0.0 |
| 7337262 | Raya | ARS | £6.1m | a | null/null | null | empty | 6.0 |
| 7337262 | Gabriel | ARS | £7.9m | a | null/null | null | empty | 4.0 |
| 7337262 | Castagne | FUL | £4.5m | a | null/null | null | empty | 2.3 |
| 7337262 | Guéhi | MCI | £6.0m | a | null/null | null | empty | 3.3 |
| 7337262 | Rogers | CHE | £7.8m | a | null/null | null | empty | 6.3 |
| 7337262 | Palmer | CHE | £9.7m | a | 100/100 | 2026-09-21T13:00:09Z | empty | 5.0 |
| 7337262 | Semenyo | MCI | £8.4m | d | 75/75 | 2026-09-24T12:00:09Z | ankle, 75% | 5.0 |
| 7337262 | Rice | ARS | £7.3m | a | 75/100 | 2026-09-21T13:00:08Z | empty | 4.7 |
| 7337262 | Anderson | MCI | £6.3m | a | 100/100 | 2026-08-23T17:00:07Z | empty | 2.3 |
| 7337262 | João Pedro | CHE | £7.7m | a | 100/100 | 2026-09-16T19:00:09Z | empty | 8.0 |
| 7337262 | Isak | LIV | £9.0m | i | 0/0 | 2026-09-27T10:30:09Z | thigh, unknown return | 0.0 |
| 7337262 | Verbruggen | BHA | £4.5m | a | null/null | null | empty | 7.7 |
| 7337262 | Truffert | BOU | £5.4m | a | null/null | null | empty | 1.3 |
| 7337262 | Shaw | MUN | £4.3m | a | 100/100 | 2026-09-11T13:00:09Z | empty | 1.7 |
| 7337262 | Obi | MUN | £4.5m | u | 0/0 | 2026-09-14T16:12:42Z | Willem II loan | 0.0 |

### Changes since 10 October snapshot

- Xhaka fell £5.5m to £5.4m; Gabriel £8.0m to £7.9m; Rice £7.4m to £7.3m; Isak £9.1m to £9.0m.
- Rice status is now available with next-round chance 100%, though its current-round field remains 75. No new `news_added` timestamp accompanies that state.
- João Pedro, Palmer, Van Hecke and Shaw all completed substantial minutes, converting availability reports into observed match evidence.
- Castagne's available status did not translate into minutes. Van Ewijk remains 75%; Isak remains 0%; Semenyo remains 75% before today's match.

## Ex-ante versus realised tracking

Using the 10 October pre-deadline official `ep_next` fields only—not a calibrated laboratory forecast—the recommended 8522487 XI totalled 57.5 including captaincy. The recommended 7337262 XI totalled 53.6; its actual Isak-over-Shaw selection totalled 52.6. These values are recorded solely for retrospective comparison.

The first six matches are insufficient for a final accuracy review. Important realised deviations already include João Pedro 12 versus official 6.0, Verbruggen 9 versus 7.0, Palmer captain 16 versus 7.0 doubled, Rogers 9 versus 5.0, Bruno 1 versus 2.0 and Truffert -1 versus 2.5. Do not score the Haaland captain decision before Liverpool–City.

## GW7–GW10 direction

- **Now:** make no move while GW6 remains live. Monday's van Ewijk minutes and all Sunday lineups/results are evidence for GW7.
- **GW7:** Haaland at home to Ipswich remains the provisional captain anchor. For 7337262, Isak's training/return evidence is the transfer trigger. If still out or limited, compare an Isak sale against holding with João Pedro as the only playable forward. Authenticate exact free transfers and selling prices first.
- **Forward comparison—not a recommendation:** current official GW7 estimates identify owned João Pedro (8.0), Kostoulas (7.0), Emersonn (5.3), Nicolas Jackson (5.0), Evanilson (4.7) and Calvert-Lewin (4.7). Evanilson's SUN/MUN/LEE/IPS run is the most balanced fixture path among those budget options; Kostoulas has CRY then LIV/MCI, and Emersonn begins at City. Reassess roles, minutes and price feasibility after GW6.
- **GW8–GW10:** Chelsea's TOT/MUN/SUN sequence supports retaining Palmer, Rogers and João Pedro if fit. City's AVL/BHA/NFO maintains Haaland as a repeated captain comparison. Avoid pre-committing the no-Haaland entry to a multi-sale Haaland route without verified finances and a four-GW expected-points advantage.
- No Wildcard, Free Hit, Bench Boost or Triple Captain case is established today.

## Required manual confirmation before GW7 action

For each account, authenticate the transfer page and record current free transfers, current bank, any pending move, each candidate's purchase/selling price and post-transfer bank. For 7337262, also confirm whether Isak remains selectable and whether Obi can be repaired without a hit. Public GW6 picks now prove the locked GW6 selections, but cannot prove any pending GW7 action.

## Endpoint provenance

Fresh official data came from bootstrap, fixtures, event/6/live, both supplied entries, their history and transfer endpoints, their event/6/picks endpoints, and Overall league page 20. Raw responses remain local and are not committed.

The current canonical repository evidence checkpoint remains unbound (generation 0). The latest committed daily evidence run is 29 September, the latest committed triage is 17 August, and the bound weekly packet is 11 August. Those artefacts are stale for this live review. Draft PR 121 contains the authoritative 10 October pre-deadline review; today's derived report supersedes its execution uncertainty without rewriting the ledger.
