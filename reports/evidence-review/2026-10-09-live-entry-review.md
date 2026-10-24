# Live-entry evidence review — 2026-10-09

- observed_at: 2026-10-09T08:02:10Z
- entries: 8522487 and 7337262
- companion decision input: `reports/strategy-research/2026-10-09-live-entry-decision-input.md`
- automated evidence run: `composer-2.5:2026-10-09T070105Z`
- ledger tip: `9e08244a5dca4f210ea0303906301d9dd21b56d9a0beb5907b2ecfc3d8c77796`
- account writes: false

## Review verdict

No material owned-squad decision changed this morning. The automated run admitted three current Leeds claims, but none affects either owned squad. It correctly retained Isak as doubtful and Haaland as available. The live-entry overlay rejects the automated advisory's reconstructed Kinsky/Cherki/Wissa squad and its unverified “one free transfer” wording.

## Accepted claims and effects

| claim | status | owned effect |
|---|---|---|
| Harry Wilson returned to team training; only a chance for GW6 | doubtful | none; 8522487 sold Wilson in GW4 |
| Daniel James misses Arsenal | unavailable | none |
| Jean-Mattéo Bahoya has an ankle strain and only a chance | doubtful | none |
| Isak left international duty injured; recovery for Manchester City uncertain | doubtful, retained | material to 7337262; wait for 13:30 Friday presser |
| Haaland available after Norway duty | available, retained | supports captaincy on 8522487; does not prove 90 minutes |

## Withheld or rejected claims

| claim | treatment | reason |
|---|---|---|
| João Pedro trained on 07 October | rejected as official evidence | fan account only; no dated club statement |
| Chelsea 08 October gallery clears Pedro or Palmer | rejected | gallery names four other players and makes no fitness statement on either owned player |
| Isak/Gakpo require late tests | rejected community formulation | no linked official source and originally misattributed |
| Palmer should captain while flagged | withheld | no current normal-minutes clearance |
| Wildcard is required because six players are flagged/unavailable | rejected | flags are not six confirmed absences; public manager state lacks free transfers and selling prices |
| “Roll one free transfer” | rejected | public FPL endpoints do not expose the current free-transfer count |

## Source-freshness assessment

- Official FPL structured snapshot: fresh at 2026-10-09T07:01:05Z.
- Latest owned-player club evidence: Haaland 08 October, Chelsea gallery 08 October, Isak 07 October.
- Critical pending evidence: Liverpool 13:30 BST Friday; Manchester City Friday; Chelsea/Arsenal/Spurs/Manchester United final team news.
- Community digest: 08 October; current enough for challenge discovery, not admissible for injury or price facts.
- Weekly decision packet remains an 11 August predecessor bind, so live official entry data and the live-entry overlay control squad identity.

## Decision boundaries

| boundary | current call | falsifier |
|---|---|---|
| 8522487 transfer | hold | new long absence creates fewer than 11 credible starters or a verified high-EV move clears exact sale-price/FT checks |
| 8522487 captain | Haaland / Bruno | City limits Haaland or Manchester United produces a materially stronger, fully available Bruno case |
| 7337262 transfer | hold pending pressers | both Isak and João Pedro ruled out; or at least three persistent XI holes |
| 7337262 captain | Rogers / Raya | Palmer cleared for normal minutes, then Palmer / Rogers |
| chip | none | authenticated state plus three or more persistent structural holes produces a superior four-GW Wildcard rebuild |

## Manual gate

Before any execution, authenticate each entry and verify free transfers, pending transfers, bank, purchase prices and selling prices. The public-state report is decision-grade for monitoring but not transaction-complete.
