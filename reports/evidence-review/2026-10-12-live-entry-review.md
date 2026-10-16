# Evidence review — near-complete GW6 state on 12 October 2026

- observed_at: 2026-10-12T07:38:00Z–2026-10-12T07:48:00Z
- next decision deadline: 2026-10-17T10:00:00Z / 11:00 BST
- scope: public GW6 scoring, Sunday role evidence, Monday residual uncertainty and GW7 transfer/captain implications
- account writes: none
- ledger disposition: derived review only; no claim admitted to the canonical evidence ledger

## Repository context and freshness

| Input | Latest repository state | Treatment |
|---|---|---|
| Governing method | `AGENTS.md`, `docs/plan.md` | Applied: official-first hierarchy, point-in-time discipline, deterministic constraints and outcome/process separation. |
| Weekly decision packet | `weekly-2026-08-11.json`, SHA256 65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651 | Stale; no sealed GW7 forecast. |
| Checkpoint manifest | generation 0; no ledger binding | Evidence state degraded; this review is not a promoted checkpoint. |
| Latest committed model evidence review | 19 September | Stale for current availability; not used to override fresh official state. |
| Latest committed news triage | 17 August | Stale; direct official club sources supplement it. |
| Latest community digest | 9 October | Read as challenge/discovery only. Its pre-presser Chelsea minutes claims are superseded by match evidence. |
| Prior daily review | draft PR 123, observed 11 October | Authoritative Sunday snapshot; this review updates completed Sunday fixtures and provisional scores. |

The automated Kinsky/Cherki/Wissa reconstruction remains rejected for these entries. Public GW6 picks and completed transfer history control the squad reconstruction.

## Accepted official evidence

| Evidence | published_at / observed_at | Accepted conclusion | Limit |
|---|---|---|---|
| Official FPL bootstrap, fixtures, event/6/live, entries, histories, transfers, GW6 picks and Overall page 20 | mutable; observed 2026-10-12T07:38Z–07:40:56Z | Current scores, minutes, bonus, prices, flags, deadline values/banks, completed transfers/chips, fixture status and live top-1,000 boundary. | GW6 is unfinished and not data checked; autosubs and ranks remain provisional. |
| Manchester City Liverpool match report | published 2026-10-11; observed 2026-10-12 | City won 3-0; Haaland scored after 65 minutes. FPL records 79 minutes and six raw points. | One match does not settle the GW7 captain forecast. |
| Crystal Palace match centre | published/live 2026-10-11; observed 2026-10-12 | Palace beat Forest 3-1; Mitchell completed the match and was positively described late in the game. | Club commentary is qualitative; FPL scoring controls points. |
| Chelsea Bournemouth team news and match evidence | team news published 2026-10-09; match observed through FPL 2026-10-12 | Palmer and João Pedro returned and completed 87/71 minutes; their prior doubts are now superseded by observed participation. | Midweek recovery and rotation still need monitoring. |
| Liverpool injury list | last updated 2026-10-09; observed 2026-10-12 | Isak has a small thigh muscle injury, was ruled out of GW6 and was described as day-to-day rather than long-term. | No GW7 clearance or normal-minutes guarantee; source is three days old. |
| Coventry van Ewijk update | published 2026-10-08; observed 2026-10-12 | van Ewijk returned to training; Lampard hoped he would be ready if he progressed. | Conditional, four days old and not proof of tonight's start; FPL remains 75%. |

## Changes since 11 October

- 8522487 moved from 31 raw GW6 points to 62; projected autosub total 64.
- 7337262 moved from 49 raw GW6 points to 64; projected autosub total 66.
- Dewsbury-Hall returned 13; Haaland six raw/12 captain; Mitchell four; Gibbs-White two.
- Guéhi and Anderson each returned six; Semenyo returned three.
- Palmer captain outscored Haaland captain 16 to 12.
- João Pedro rose to £7.8m. Semenyo fell to £8.3m and changed from doubtful/75 to available/100.
- Isak remains injured/0 with no official return date. Castagne's GW6 zero minutes remain an unresolved role warning.
- The live rank-1,000 boundary rose from 477 to 489.

## Provisional substitution proof

8522487 started three defenders. Castagne's zero minutes therefore require a defender replacement; first-bench midfielder Xhaka cannot enter without breaking the minimum-three-defender rule, so Diop is the expected replacement for +2. Van Ewijk cannot enter unless another starting defender loses minutes; Mitchell and Van Hecke have both completed their matches.

7337262 has two zero-minute starters: Castagne and Isak. Truffert (-1) and Shaw (3) should both enter to form a legal 4-5-1, net +2. The actual Isak selection and recommended Shaw selection therefore converge on the same projected 66 points. This does not erase the save-verification failure.

## Accepted decision implications

- No transfer or chip today. GW6 is still live, and European matches precede the GW7 deadline.
- Haaland remains the provisional 8522487 captain against Ipswich; João Pedro becomes vice-captain ahead of Bruno on current fixture and official-estimate evidence.
- 7337262 should retain João Pedro, Palmer, Rogers, Semenyo, Rice and Anderson provisionally. João Pedro captain/Semenyo vice is the current placeholder, not a sealed forecast.
- Isak is the transfer trigger. A normal training/start clearance supports holding; continued absence supports an authenticated-budget comparison with Evanilson over GW7–GW10.
- Castagne requires a role check for both squads. An `available` FPL flag did not translate into GW6 minutes.
- van Ewijk's Monday participation is useful future availability evidence but cannot change 8522487's projected GW6 score under the current substitution path.

## Rejected or deferred claims

| Claim | Disposition |
|---|---|
| GW6 is complete because both entries have no starting player tonight | Rejected: the Gameweek remains live and can receive scoring corrections; Coventry–Newcastle has not been played. |
| van Ewijk will autosub if he plays tonight | Rejected: Diop already fills the sole missing defender slot, and every other starting defender has minutes. |
| The no-Haaland save error cost points | Rejected on current evidence: both paths yield Truffert plus Shaw, net +2. |
| Haaland captain was a bad process decision because Palmer scored four more captain points | Rejected: a single realised outcome does not invalidate the pre-deadline uncertainty treatment. |
| Isak is certain to return in GW7 | Deferred/rejected: Liverpool's latest official statement is day-to-day with no return date. |
| Castagne is secure because FPL lists him available | Rejected: he recorded zero GW6 minutes. Availability is not selection proof. |
| Semenyo's cleared flag proves unrestricted future minutes | Rejected: it is an FPL status field; role/minutes remain a separate forecast. |
| Current free transfers can be derived from zero GW6 moves | Rejected: pending transfers and exact authenticated allowance are private state. |
| Current sale proceeds equal bootstrap prices | Rejected: purchase price and the half-profit rule require the authenticated transfer page. |
| Official `ep_next` is the laboratory forecast | Rejected: it is mutable and uncalibrated. |
| A Wildcard or hit is required to repair Obi | Rejected: no current expected-gain case clears the threshold. |

## Source freshness and gaps

- Sunday's match minutes are the freshest evidence for Dewsbury-Hall, Haaland, Mitchell, Gibbs-White, Guéhi, Anderson and Semenyo.
- Saturday's match minutes remain the freshest evidence for João Pedro, Palmer, Rogers, Rice, Verbruggen, Van Hecke, Bruno, Shaw, Thiago, Le Fée, Xhaka, Diop, Truffert and Castagne.
- Isak's official evidence is three days old and requires a new Liverpool training or press-conference update before the GW7 decision.
- van Ewijk's official evidence is four days old; tonight's squad and minutes will supersede it.
- No fresh direct injury, suspension or exclusion statement was found for the other owned players. Absence of a statement is not proof of a future start.
- There is no authenticated view of current free transfers, current bank, pending moves, purchase prices or selling prices.

## Four-Gameweek control points

1. GW7: Isak expected minutes and Castagne role; Haaland captain at home to Ipswich.
2. GW8: preserve Chelsea attack into Tottenham at home; do not overreact to one GW6 outcome.
3. GW9: compare Haaland home to Brighton with Chelsea home to Manchester United.
4. GW10: City at Forest and Chelsea at Sunderland continue to reward structural flexibility.

No raw endpoint response, credential, browser state, screenshot or unverified community claim is included in this review.
