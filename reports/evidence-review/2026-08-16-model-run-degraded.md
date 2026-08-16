# Model evidence run review — composer-2.5:2026-08-16T070001Z

- status: **complete**
- model: Composer 2.5
- observed_at: 2026-08-16T07:00:01.8072166Z
- available_at: 2026-08-16T07:00:01.8072166Z
- bound_packet_sha256: 65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651
- discovery_sha256: f24c7be905746108f932006a0ba835043fe5f504e29ca41eda67154f9405362f
- model_run_sha256: cd8747d8cf7917985f04fd38aa0fb6902b275a5a88fec586edaeb652e48d6d40
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
| lane-a:2026-08-16:broad-capture-signal | retain all 98 capture candidates as research signals and admit none as governed claims | The freshness-first capture searched all 21 catalogue buckets and returned 98 candidates: 13 known-time and 85 unknown-time, comprising 66 official candidates, five official feeds and 27 external candidates. The 24-item shortlist is entirely unknown-time. The strict lead view is empty, but the broad capture is not an empty news day. No row supplies a human-linked, timestamped, precise availability or line-up claim suitable for ledger admission. |  |  | 0.98 | a current official original supplies an exact publication time and precise player availability or line-up claim; a fresh official source contradicts the broad-capture interpretation |
| lane-a:2026-08-16:player-signals | retain Haaland, Bruno Fernandes, Joao Pedro, Thiago and Spurs goalkeeper competition as monitoring signals only | The capture clusters relevant candidates around premium minutes, Bruno team news, Joao Pedro involvement, Thiago availability and goalkeeper competition. Two specific official rows remain needs_human because publication time and current GW1 meaning are unresolved; all other shortlisted rows are rejected as archives, generic feeds or non-decision context. These signals affect follow-up priority but not packet numbers or the governed ledger. |  |  | 0.92 | a current official team sheet or press update confirms or rules out a named player; human verification supplies a precise timestamp and claim text |
| lane-a:2026-08-16:watchlist-contract | bind the model run to the 51-player comparator-plus-top-EP watchlist | The watchlist contains exact current-season IDs from the weekly packet's deterministic and robust comparator universe plus the local GW1 expected-points shortlist. No unresolved capture candidate is added as a player value or claim, preserving exact identity and point-in-time discipline. |  |  | 0.90 | bootstrap identity resolution shows a declared watchlist UID is not current-season exact |

## Interpretation

- This is a host audit of model-proposed signal, not an approval or
  claim that the model's underlying football judgement is correct.
- Community and unregistered sources remain briefing-only.
- Raw source bodies are not retained; URLs, derived claims, hashes and
  rejection reasons are the available review record.
