# Model evidence run reconciliation — composer-2.5:2026-08-16T070218Z

- status: **complete**
- issue: the original 16 August admission used stale prior ledger `b00a36064f251c83f6fa48a43ad6f13852a32d4c96018c3b8aa1f9b87d3ae949`
- canonical prior ledger: `f2397d8fd295e2f630a2a9337d77abf2c8ca63f0d9fd14d501c4eddf60a4f777`
- superseded parallel tip: `4df25fc6ce68e4ecfe2ffd8cf32ea5be146991db7f78c9d267d5519a620d987a`
- reconciled canonical tip: `e065ec2649677864592d4b5b1501e05d8d64c267aa29305a90f845cf0a8fdf13`
- claims replayed: 6
- claims superseding 15 August evidence: 5
- wholly new player claims: 1 (João Pedro)
- source claims, source hashes and canonical claim IDs changed: no

## Resolution

The six already-admitted 16 August claims were replayed without alteration
against the canonical 15 August ledger. Haaland, Rodri, Saka, Saliba and
Timber now explicitly supersede their corresponding 15 August claims.
João Pedro remains a new claim.

The superseded `4df25fc6ce68e4ecfe2ffd8cf32ea5be146991db7f78c9d267d5519a620d987a` ledger is retained as historical evidence but
is not a canonical tip. The authoritative sequence is:

`b00a36064f251c83f6fa48a43ad6f13852a32d4c96018c3b8aa1f9b87d3ae949` → `62f5d4daebdb973e61ec4ab16630a73e85d5dbedfb81024f537d88da0bd3a790` → `f2397d8fd295e2f630a2a9337d77abf2c8ca63f0d9fd14d501c4eddf60a4f777` → `e065ec2649677864592d4b5b1501e05d8d64c267aa29305a90f845cf0a8fdf13`

## Validation

- Repository ledger validation passes for the prior and reconciled ledgers.
- The first 15 claims of the reconciled ledger are byte-equivalent to the
  canonical 15 August claim history.
- Claims remain ordered by `available_at`.
- Every supersession points to an earlier claim for the same player.
- The reconciled ledger content hash recomputes to `e065ec2649677864592d4b5b1501e05d8d64c267aa29305a90f845cf0a8fdf13`.
- The corrected audit binds prior `f2397d8fd295e2f630a2a9337d77abf2c8ca63f0d9fd14d501c4eddf60a4f777` to result `e065ec2649677864592d4b5b1501e05d8d64c267aa29305a90f845cf0a8fdf13`.
