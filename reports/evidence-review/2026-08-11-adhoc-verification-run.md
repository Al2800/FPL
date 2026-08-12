# Model evidence run review — cursor-grok-4.5-high:2026-08-11T163054Z

- status: **complete**
- model: Cursor Grok 4.5 High
- observed_at: 2026-08-11T16:30:54Z
- available_at: 2026-08-11T16:35:00Z
- bound_packet_sha256: c37b904feea84c45ce2564b32f08aa6c9b0b5642d1dee298a0b00e067defc389
- discovery_sha256: 35ccd93dadf0e29342e45b547dae17f022a68cd47a940c7a4ced6a554f99c08f
- model_run_sha256: c2346ba73d079c7b4d5b32cf7a20939dd83e41859edec67228409c13147e329f
- prior_ledger_sha256: none
- resulting_ledger_sha256: 96533cd117ff54b1f4a08c76f3baeb23f73f9cc2b4e30140c9a97509feb06b3b

## Signal capture checks

| check | result |
|---|---|
| Catalogue coverage | 21/21 clubs (100.0%) |
| Coverage gaps | none |
| Watchlist size | 47 players |
| Candidate claims | 0 |
| Accepted claims | 0 |
| Acceptance rate | 0.0% |
| Duplicate claims | 0 |
| Rejected claims | 0 |
| Ephemeral documents hashed | 0 |
| Decision trace | 1 items; 0 linked to claims |
| Accepted statuses | none |
| Review flags | decision_trace_has_no_claim_links |

## Accepted ledger signal

No claims were admitted.

## Rejected or unresolved signal

No candidates were rejected.

## Decision rationale trace

| boundary | decision | rationale | supporting claims | conflicting claims | confidence | falsifiers |
|---|---|---|---|---|---:|---|
| lane-a:2026-08-11:shortlist-admission | emit zero claim candidates; admit empty discovery | Fetched all 24 official-domain triage shortlist URLs. Every page was prior-season (2023-25 FA Cup/Europa/league run-ins), end of 2025-26 (May 2026 finals), women/WSL, historical retrospective, 404, or empty body. None published on/after 2026-08-04 about 2026-27 pre-season/GW1 availability. Host discovery therefore admitted 0 leads; inventing claims would violate point-in-time discipline. |  |  | 0.95 | an official club page dated >=2026-08-04 with a concrete availability/minutes statement for a watchlist player |

## Interpretation

- This is a host audit of model-proposed signal, not an approval or
  claim that the model's underlying football judgement is correct.
- Community and unregistered sources remain briefing-only.
- Raw source bodies are not retained; URLs, derived claims, hashes and
  rejection reasons are the available review record.
