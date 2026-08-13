# Model evidence run review — composer-2.5:2026-08-13T070002Z

- status: **degraded — no host admission run**
- model: Composer 2.5
- observed_at: 2026-08-13T07:00:02.0937846Z
- available_at: 2026-08-13T07:00:02.0937846Z
- bound_packet_sha256: 65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651
- discovery_sha256: 9394bb2677f7cdc5e8d31ce7aa98559d1d2e2be49d6a5b87bd0a709a9b1b2c98
- model_run_sha256: c9d5fbc3c435dee627934fab5986148a584245c69f8a339aa5217203cb098d08
- verification_input_sha256: fcdccf8042c494360fee900e35dbe16ad1cbbbc243ed6213e441c9f7eb6d6bb6
- prior_ledger_sha256: b00a36064f251c83f6fa48a43ad6f13852a32d4c96018c3b8aa1f9b87d3ae949 (read-only reference; four claims)
- resulting_ledger_sha256: b00a36064f251c83f6fa48a43ad6f13852a32d4c96018c3b8aa1f9b87d3ae949 (unchanged — host admission was not run)

## Signal capture checks

| check | result |
|---|---|
| Catalogue coverage | 21/21 clubs searched in the capture |
| Broad candidates | 30 |
| Known-time / unknown-time | 13 / 17 |
| Triage shortlist | 22; eight freshness-excluded |
| Model watchlist | 51 players |
| Model claims | 0 |
| Accepted ledger claims | 0 |
| Official page checks | two needs_human, four rejected |
| Community sources | briefing-only; never admitted |
| Decision trace | 3 items; no claim-linked trace because claims are empty |

## Admission decision

No capture snippet or unverified candidate was converted into a governed claim.
The checked Chelsea page provides training participation context for Joao Pedro
without a GW1 minutes claim or exact publication timestamp. The checked
Liverpool availability page is current-season and player-specific for several
Liverpool squad members, but the capture has no ISO `published_at` and the page
does not change the declared 15. The remaining checked candidates were generic,
unresolved or not precise enough for admission. See the verification input for
the metadata-only statuses.

## Decision trace

The run retains the broad-capture signal surface, including undated candidates,
instead of collapsing it to the strict lead view. It down-ranks dated archives
and generic training/fixture context, binds a 51-player comparator-plus-top-EP
watchlist, and leaves the governed ledger unchanged pending human timestamp
linkage and precise player-level claims.

## Interpretation

This is a degraded model-evidence review, not a claim that the underlying
football signals are false. It records an explicit zero-admission result under
the point-in-time and human-linked-original boundary. Community line-up and
strategy material remains usable only in the daily briefing.
