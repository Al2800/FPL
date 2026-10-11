# Evidence review — live GW6 state on 11 October 2026

- observed_at: 2026-10-11T07:47:00Z–2026-10-11T07:52:37Z
- next decision deadline: 2026-10-17T10:00:00Z / 11:00 BST
- scope: public execution proof, live official scoring, status/price changes, Sunday/Monday availability and GW7 implications
- account writes: none
- ledger disposition: derived review only; no claim admitted to the canonical evidence ledger

## Repository context and freshness

| Input | Latest repository state | Treatment |
|---|---|---|
| Governing method | `AGENTS.md`, `docs/plan.md` | Applied: official-first hierarchy, point-in-time discipline, no private-state inference, outcome separated from process. |
| Weekly decision packet | `weekly-2026-08-11.json`, SHA256 65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651 | Stale; no current sealed GW6/GW7 forecast. |
| Checkpoint manifest | generation 0; no ledger binding | Manager/evidence state degraded; today's review is not a promoted checkpoint. |
| Latest committed ledger audit/discovery | 29 September, tip f6ff62e7b1cdf886c6ef9e378c9f930b212a59c4f3d7bfd8924b5c32e2b0ff8e | Stale for 11 October; not used to override fresh official state. |
| Latest committed news triage | 17 August | Stale; direct official sources supplement it. |
| Latest community digest | 9 October | Read as challenge/discovery input only. Pre-presser Palmer-minutes, price and Wildcard chatter remains non-authoritative. |
| Prior daily review | draft PR 121, observed 10 October | Authoritative pre-deadline record; selection uncertainty is now resolved by public GW6 picks. |

The automated Kinsky/Cherki/Wissa reconstruction remains rejected for these entries. Current public picks and transfer history establish the tracked squads.

## Accepted official evidence

| Evidence | published_at / observed_at | Accepted conclusion | Limit |
|---|---|---|---|
| Official FPL bootstrap, fixtures, live scoring, entry, history, transfers and GW6 picks | mutable; observed 2026-10-11T07:47Z–07:49Z | Locked GW6 selections, no GW6 transfers/chips, live score components, deadline finances, current flags/prices and remaining fixtures. | Provisional bonus/ranks can change; public endpoints do not expose current free transfers or selling prices. |
| Chelsea Bournemouth availability report | published 2026-10-09; re-observed in prior review | Palmer and João Pedro trained and were available. | No numerical minutes promise. Match evidence now confirms 87 and 71 minutes respectively. |
| Liverpool Isak fitness report | published 2026-10-09 | Isak ruled out of City with a small thigh muscle injury; day-to-day, not expected long term. | No GW7 return guarantee. |
| City Haaland report | published 2026-10-09 | Haaland fit and available for Liverpool after precautionary Norway withdrawal. | Today's lineup and minutes remain unconfirmed at this cutoff. |
| Spurs Van Hecke report | published 2026-10-09 | Van Hecke available. | Match evidence now confirms a 90-minute start. |
| Coventry van Ewijk update | published 2026-10-08; observed 2026-10-11 | Returned to training; Lampard hoped he would be ready if he progressed over the following days. | Conditional, not a confirmed Monday start; current FPL remains 75%. |
| Palace/Forest, Everton/Hull and Liverpool/City official news indexes | latest useful team news remains 9 October at this cutoff | No new owned-player exclusion found before today's fixtures. | Absence of a new statement is not proof of a start; lineups are released later. |

## Execution proof and forecast comparison

Public GW6 picks can now prove the locked selection because the deadline has passed. They confirm 8522487 exactly matches the prior saved observation. They also prove that 7337262 did not execute Shaw for Isak, while Palmer captain, Rogers vice and João Pedro were saved.

This is an execution-process defect, even though the current realised score is neutral. Castagne's zero minutes require one defender substitution in both actual and recommended variants; Isak's expected zero requires the second defender in the actual variant. Both routes currently add Truffert (-1) and Shaw (3), net +2. Do not allow outcome luck to erase the failure to verify the no-Haaland save.

The official pre-deadline `ep_next` field supplies a reproducible but uncalibrated comparison baseline: 57.5 for the recommended Haaland XI; 53.6 for the recommended no-Haaland XI; 52.6 for the actual no-Haaland selection. Full actual-versus-expected evaluation waits until GW6 is final and data checked.

## Source freshness and unresolved coverage

- Saturday match observations are the freshest role/minutes evidence for João Pedro, Palmer, Rogers, Rice, Verbruggen, Van Hecke, Bruno, Shaw, Thiago, Le Fée, Xhaka, Diop, Truffert and Castagne.
- Mitchell, Gibbs-White, Dewsbury-Hall, Guéhi, Semenyo, Anderson and Haaland have Sunday fixtures after this review; final lineups are not available yet.
- Van Ewijk plays Monday. The 8 October training report and current 75% flag are the latest accepted evidence.
- Isak is a confirmed GW6 absence, but his GW7 status is unresolved.
- Obi remains unavailable on loan. No public source proves a private pending replacement.
- No useful new direct individual-role statement was recovered for Dubravka, Raya or Gabriel after their matches; match minutes and official scoring now control.

## Accepted changes since 10 October

- Execution state resolved: 8522487 saved correctly; 7337262 only partly implemented the plan.
- Match evidence supersedes uncertainty: Palmer 87 minutes, João Pedro 71, Van Hecke 90, Rice 90 and Shaw 90.
- Castagne recorded zero minutes despite available status; he becomes a reliability monitor.
- Rice is now status `a` and 100% for next round; Semenyo and van Ewijk remain 75%; Isak remains 0%.
- Price changes: Xhaka -£0.1m, Gabriel -£0.1m, Rice -£0.1m and Isak -£0.1m.
- No GW6 transfer or chip was used by either entry.

## Rejected or deferred claims

| Claim | Disposition |
|---|---|
| Shaw-for-Isak was saved | Rejected by the locked public GW6 picks. |
| The selection miss cost four points | Rejected at this stage: Castagne's zero causes both Truffert and Shaw to enter, making the two lineups provisionally equal. |
| Autosubs and bonus are final | Deferred until GW6 is finished and data checked. |
| Palmer was capped at 60 minutes | Rejected by 87 observed minutes; it was never official evidence. |
| Isak is certain to return in GW7 | Deferred; Liverpool supplied no return date. |
| van Ewijk is cleared because he trained | Rejected; Lampard's statement was conditional and FPL remains 75%. |
| Current free transfers can be derived from zero GW6 moves | Rejected; public history cannot prove pending/private state or the exact authenticated allowance. |
| Current sale proceeds equal bootstrap prices | Rejected; purchase price and the half-profit rule require authenticated selling prices. |
| Official `ep_next` is the laboratory forecast | Rejected; it is a mutable baseline field, not a sealed model output. |
| The Haaland-versus-Palmer captain decision can be graded now | Deferred until Liverpool–City finishes and GW6 scoring is final. |
| Community price trackers or Wildcard drafts establish a move | Rejected as decision evidence. Official prices and verified manager state control. |

## Decision implications

There is no in-Gameweek action. Preserve the live record and evaluate after all fixtures.

For GW7, Haaland versus Ipswich is the current captain anchor. The no-Haaland entry's priority question is Isak: hold if official training evidence establishes a normal return; otherwise compare a sale to an available forward over GW7–GW10. Current FPL estimates are discovery inputs only. Evanilson's SUN/MUN/LEE/IPS sequence merits comparison, while high one-week estimates for Kostoulas and Emersonn face difficult following fixtures. Do not recommend a specific transfer until exact free transfers, sale price and bank are authenticated.

Chelsea's Everton, Spurs, United and Sunderland sequence supports holding Palmer, Rogers and João Pedro if fit. City's Ipswich, Villa, Brighton and Forest run keeps Haaland central to captaincy. A forced multi-transfer route to Haaland on 7337262 needs a quantified four-Gameweek gain; rank pressure alone is not evidence.

## Manual state required

Before the GW7 decision, authenticate both transfer pages and record free transfers, bank, pending moves, purchase/selling prices and resulting budget for each candidate plan. Also verify the saved XI/captain/bench after any future edit. The GW6 no-Haaland miss should be logged as an adherence failure, even if autosub luck leaves the score unchanged.

No raw API response, browser state, credential, screenshot or unverified claim is included in the repository output.
