# Live-entry evidence review — 2026-10-07

- `observed_at`: 2026-10-07T07:39:08Z
- `decision_deadline`: 2026-10-10T10:00:00Z
- `entries`: 8522487, 7337262
- `raw_payloads_committed`: false
- `account_writes`: false

## Review verdict

Hold both owned squads. No transfer, chip or captaincy change is justified by today's evidence. Rogers' £0.1m price rise and the completed England appearances are real changes; they do not resolve any of the owned injury doubts or reveal private manager state.

## Source freshness and claims

| Source | Published at | Observed at | Claim | Review status | Decision effect |
|---|---|---|---|---|---|
| Official FPL bootstrap/fixtures/entry endpoints | live mutable feed | 2026-10-07T07:39:08Z | Deadline, ranks, prices, flags, chance fields and public history | accepted | Rogers £7.8m; all owned flags otherwise unchanged |
| England Football, England 3-0 Czechia | 2026-10-06 | 2026-10-07T07:34:00Z | Rogers 90; Anderson and Guéhi off 63; Gibbs-White on 72; no reported injury | accepted | recovery monitoring only; no XI/captain change |
| Manchester City international roundup | 2026-10-06T20:45:00Z | 2026-10-07T07:05:00Z | Anderson and Guéhi completed about 63 minutes | accepted corroboration | no injury trigger |
| Chelsea training gallery | 2026-10-06T15:50:00Z | 2026-10-07T07:05:00Z | Article names selected trainees, not Palmer or João Pedro | accepted only for named participation; rejected as proof of absence | wait for explicit medical/manager statement |
| Liverpool Isak update | 2026-09-27 | 2026-10-07T07:34:00Z | Minor injury; returned to club for assessment | accepted but ageing | Isak remains doubtful; no inferred return date |
| Brentford international roundup | 2026-10-05T09:00:00Z | 2026-10-07T07:05:00Z | Damsgaard missed Denmark v Wales through injury | accepted to ledger | not owned; watchlist only |
| X community digest, 6 October | 2026-10-06 | 2026-10-07T07:05:00Z | Price speculation, injury estimates, captain and Wildcard discussion | challenge/discovery only | no accepted owned medical claim |

## Accepted changes since 6 October

1. Rogers' official current price changed from £7.7m to £7.8m. Selling price remains private and cannot be derived.
2. Rogers played the full England match; Anderson and Guéhi played 63 minutes; Gibbs-White played approximately 18 minutes plus stoppage time.
3. Repository Lane A admitted Damsgaard doubtful; ledger tip changed from `5d89db69…` to `b7df36ea…`. This does not touch either owned squad.
4. Entry ranks moved marginally to 5,199,982 and 5,320,461. Points and the sampled top-1,000 threshold remain unchanged.

## Rejected or bounded inferences

- Do not treat Palmer or João Pedro's omission from Chelsea's gallery text as an injury update.
- Do not convert FPL's 75% flags into expected starts or absences without a fresh club statement.
- Do not infer current free transfers from completed transfer history.
- Do not infer selling prices from current prices or last-deadline value.
- Do not use Rogers' price rise as a reason to transfer or captain him; captaincy remains risk-adjusted around verified minutes.
- Do not promote Damsgaard into the transfer shortlist from a single injury report.
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
- Shaw is first outfield substitute and replaces João Pedro if João Pedro remains unavailable.
- Trigger the transfer-versus-Wildcard comparison only if at least three genuine XI holes survive final press conferences.
- No transfer or chip today.

## Manager-state degradation

The public endpoints verify completed squads, picks, transfer history, chip history and last-deadline finances. They do not verify current free transfers, any pending private move, purchase prices or selling prices. Before the final GW6 recommendation, inspect both authenticated transfer pages and record those fields with a fresh observation time. Until then, every transfer route and its legality/cost is provisional.

## Falsifiers before the deadline

- A club clears or rules out Palmer, João Pedro, Rice, Semenyo, Isak, Van Hecke or van Ewijk.
- Manchester City or Manchester United reports a restriction for Haaland or Bruno.
- Authenticated manager state changes the number or affordability of candidate moves.
- Three or more credible XI holes remain on 7337262 after final press conferences.

If none occurs, retain the provisional line-ups and no-chip stance in the companion decision input.
