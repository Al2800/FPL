# 2026/27 line-ups and minutes provider review

The production contract is deliberately provider-neutral.  A captured provider
snapshot is mapped only through explicit fixture/player aliases and reconciled
against official FPL post-match minutes.  Any mismatch quarantines that player;
missing data degrades the feature family and never becomes a zero-minute claim.

## Candidates

| Provider | Current decision | Reason |
| --- | --- | --- |
| API-Football | primary trial candidate | Documentation says covered line-ups become available 20–40 minutes before fixtures; coverage/timing must be measured for EPL. |
| football-data.org | secondary trial candidate | Supports unfolded line-ups/substitutions, but entitlement/coverage must be proved for the intended tier. |
| TheSportsDB | fallback trial candidate | Documents event-lineup endpoint, but free limits and timing make it unsuitable as an assumed authoritative feed. |

No provider is activated merely from documentation.  A representative EPL trial must record request timestamps, fixture/player mapping rate, first lineup visibility, final minutes accuracy against FPL, rate-limit response and retention/terms evidence.  Credentials remain environment-only and snapshots are immutable.
