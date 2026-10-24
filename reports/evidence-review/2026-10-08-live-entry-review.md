# Live-entry evidence review — 2026-10-08

- `observed_at`: 2026-10-08T07:32:11Z
- `decision_deadline`: 2026-10-10T10:00:00Z
- `entries`: 8522487, 7337262
- `raw_payloads_committed`: false
- `account_writes`: false

## Review verdict

No transfer, chip or captaincy change today. Liverpool's explicit Isak statement is a material risk update for 7337262, but it does not establish a GW6 absence or justify acting before the final club briefings.

## Source freshness and claims

| Source | Published at | Observed at | Claim | Review status | Decision effect |
|---|---|---|---|---|---|
| Official FPL bootstrap/fixtures/entry endpoints | live mutable feed | 2026-10-08T07:32:11Z | Deadline, ranks, prices, flags, chance fields and public history | accepted | no owned field change since 7 October |
| Liverpool Iraola interview | 2026-10-07T14:59:00Z | 2026-10-08T07:08:17Z | Isak and Gakpo currently injured; recovery for Manchester City uncertain | accepted | Isak blank/cameo risk raised; wait for final update |
| Chelsea training gallery | 2026-10-07T15:00:00Z | 2026-10-08T07:08:17Z | Names Estevao, Pedro Neto and Hato, not Palmer or João Pedro | accepted only for named participation; rejected as proof of absence | wait for Friday press conference |
| Chelsea weekly diary | published before 8 October | 2026-10-08T07:30:00Z | Alonso's pre-Bournemouth press conference is Friday | accepted schedule evidence | mandatory final checkpoint |
| England Football, England 3-0 Czechia | 2026-10-06 | 2026-10-07T07:34:00Z | Rogers 90; Anderson and Guéhi off 63; Gibbs-White on 72; no reported injury | retained | recovery monitoring only |
| X community digest, 7 October | 2026-10-07 | 2026-10-08T07:08:17Z | Unsourced injury round-up, captain and Wildcard discussion | challenge/discovery only | no accepted owned medical claim |

## Accepted changes since 7 October

1. Liverpool now explicitly describes Isak as currently injured and uncertain for Manchester City. The evidence upgrades the freshness and confidence of the existing doubtful status; it does not change him to unavailable.
2. The repository evidence run also admits Gakpo doubtful. Gakpo is not owned and is a do-not-buy comparator only.
3. Entry ranks moved marginally to 5,199,965 and 5,320,443. Points and the sampled top-1,000 threshold remain unchanged.
4. The official feed shows no owned price, status, chance or news-timestamp change.

## Rejected or bounded inferences

- Do not convert Iraola's statement into a definite Isak absence.
- Do not sell Isak or activate the Wildcard before the final club update and authenticated manager-state check.
- Do not treat Palmer or João Pedro's omission from Chelsea's gallery text as an injury update.
- Do not convert FPL's 75% flags into expected starts or absences without a fresh club statement.
- Do not infer current free transfers from completed transfer history.
- Do not infer selling prices from current prices or last-deadline value.
- Do not treat community recovery dates, Wildcard templates or captain polls as official evidence.

## Owned-squad implications

### 8522487

- Keep Haaland captain and Bruno Fernandes vice-captain.
- Start Diop while Van Hecke lacks a normal-minutes clearance.
- João Pedro starts over Xhaka only after a normal-minutes clearance.
- No transfer or chip today.

### 7337262

- Rogers remains the risk-adjusted captain while Palmer is flagged; Raya is vice-captain.
- Palmer retakes the armband only after a normal-minutes clearance.
- Treat Isak as a high-risk conditional starter, not a confirmed absence.
- Shaw remains first outfield substitute and can cover one attacking no-show where the resulting formation is legal.
- Trigger the transfer-versus-hits-versus-Wildcard comparison if at least three genuine XI holes survive final press conferences.
- No transfer or chip today.

## Manager-state degradation

Public endpoints verify completed squads, picks, transfer history, chip history and last-deadline finances. They do not verify current free transfers, any pending private move, purchase prices or selling prices. Before the final GW6 recommendation, inspect both authenticated transfer pages and record those fields with a fresh observation time. Until then, every transfer route and its legality/cost is provisional.

## Falsifiers before the deadline

- Liverpool clears or rules out Isak.
- Chelsea clears or rules out Palmer and/or João Pedro.
- A club clears or rules out Rice, Semenyo, Van Hecke or van Ewijk.
- Manchester City or Manchester United reports a restriction for Haaland or Bruno.
- Authenticated manager state changes the number or affordability of candidate moves.
- Three or more credible XI holes remain on 7337262 after final press conferences.

If none occurs, retain the provisional line-ups and no-chip stance in the companion decision input.
