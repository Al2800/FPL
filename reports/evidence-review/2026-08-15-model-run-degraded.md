# Model evidence run review — composer-2.5:2026-08-15T070001Z

- status: **complete**
- model: Composer 2.5
- observed_at: 2026-08-15T07:00:01.7904682Z
- available_at: 2026-08-15T07:00:01.7904682Z
- bound_packet_sha256: 65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651
- discovery_sha256: d9a93cb39b8ae7da47dd275b94d9d59d99a82d5a7dc96c7e54c51010afe4421d
- model_run_sha256: 72ae522f9ada986c4015bbd8ac674e4ec32e163ce45323ac0b3ef1d4439ae4c7
- prior_ledger_sha256: b00a36064f251c83f6fa48a43ad6f13852a32d4c96018c3b8aa1f9b87d3ae949
- resulting_ledger_sha256: b00a36064f251c83f6fa48a43ad6f13852a32d4c96018c3b8aa1f9b87d3ae949

## Signal capture checks

| check | result |
|---|---|
| Catalogue coverage | 21/21 clubs (100.0%) |
| Coverage gaps | none |
| Watchlist size | 577 players |
| Candidate claims | 0 |
| Accepted claims | 0 |
| Acceptance rate | 0.0% |
| Duplicate claims | 0 |
| Rejected claims | 0 |
| Ephemeral documents hashed | 0 |
| Decision trace | 3 items; 0 linked to claims |
| Accepted statuses | none |
| Review flags | decision_trace_has_no_claim_links |

## Accepted ledger signal

No claims were admitted.

## Rejected or unresolved signal

No candidates were rejected.

## Decision rationale trace

| boundary | decision | rationale | supporting claims | conflicting claims | confidence | falsifiers |
|---|---|---|---|---|---:|---|
| lane-a:2026-08-15:broad-capture-signal | retain all 35 capture candidates as research signals and admit none as governed claims | The freshness-first capture searched all 21 catalogue buckets and returned 35 candidates: 14 known-time and 21 unknown-time, with 33 official/feed candidates and two external candidates. The 21-item shortlist retains age-gated signals for review, while 14 rows were freshness-excluded and one was demoted. No candidate supplies a human-linked, timestamped, precise availability or lineup claim suitable for ledger admission. |  |  | 0.98 | a current official original supplies an exact publication time and precise player availability or lineup claim; a fresh official source contradicts the broad-capture interpretation |
| lane-a:2026-08-15:player-signals | retain Haaland, Bruno Fernandes, Joao Pedro, Thiago and Spurs goalkeeper competition as monitoring signals only | Official candidate pages and bounded official-page checks identify relevant clusters, while community lineups provide corroboration or challenge. Publication times remain absent or ambiguous for the decision-changing rows, and training presence or a pre-season game does not prove GW1 minutes. The signals therefore affect follow-up priority but not packet numbers or the governed ledger. |  |  | 0.90 | a current official team sheet or press update confirms or rules out a named player; human verification supplies a precise timestamp and claim text |
| lane-a:2026-08-15:watchlist-contract | bind the model run to the 51-player comparator-plus-top-EP watchlist | The watchlist contains exact current-season IDs from the weekly packet's deterministic and robust comparator universe plus the local GW1 expected-points shortlist. No unresolved capture candidate is added as a player value or claim, preserving exact identity and point-in-time discipline. |  |  | 0.90 | bootstrap identity resolution shows a declared watchlist UID is not current-season exact |

## Interpretation

- This is a host audit of model-proposed signal, not an approval or
  claim that the model's underlying football judgement is correct.
- Community and unregistered sources remain briefing-only.
- Raw source bodies are not retained; URLs, derived claims, hashes and
  rejection reasons are the available review record.
