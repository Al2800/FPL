# Live 2026/27 forecast-input capture

The live forecast boundary keeps the official FPL launch catalogue separate
from optional market evidence. A successful official capture always records
prices, positions, clubs, availability and FPL's published team-strength fields.
Odds may enrich that state, but their absence cannot erase it.

## What is frozen

Run `scripts.capture_fpl_live_shadow` before the GW1 deadline with
`--freeze-launch` and an reviewed local launch-context file:

    .venv/Scripts/python.exe -m scripts.capture_fpl_live_shadow \
      --freeze-launch \
      --launch-context control/inputs/2026-27-launch-context.json

The context has two identity lists:

    {
      "promoted_team_ids": [1, 2, 3],
      "transferred_player_codes": [12345, 67890]
    }

Team IDs and stable FPL player codes must exist in the same official bootstrap
snapshot. Promoted-team players use a position/price prior with promoted-team
shrinkage. Transferred players retain a stable-code performance prior but apply
new-club minutes shrinkage. Other players use the stable-code prior and then the
existing position/price fallback. The capture refuses to call this state
`frozen` at or after the official GW1 deadline.

The output `forecast-input-capture.json` sits beside the immutable raw endpoint
bodies under `data/live-shadow/fpl/<UTC-stamp>/`. Every player and team records
`observed_at`, `available_at`, and the SHA-256 identity of the official
bootstrap body. The artifact is self-hashed and references the
`live-faithful-v1` player/team prior interface used by historical replay.

## Market evidence

The target cadence is T-24h, T-8h, T-2h and a final pre-deadline snapshot. This
repository does not currently have an approved live odds provider. The
`live-odds-candidate` registry entry remains disabled with terms and cost
pending, so current captures list all four slots as degraded.

Future activation requires an explicit registry change naming the provider,
terms, cost approval, credentials, rate limits, retention and attribution.
Even after approval, the capture command does not fetch a market feed. It may
only ingest a pre-staged local JSON snapshot supplied with
`--market-snapshot`. That file must carry:

    {
      "source_id": "approved-source-id",
      "slot": "T-2h",
      "observed_at": "2026-08-14T08:00:00Z",
      "available_at": "2026-08-14T08:01:00Z",
      "source_sha256": "<sha256 of canonical payload>",
      "payload": {"markets": []}
    }

Both timestamps must be strictly before the decision cutoff. Late, malformed,
hash-mismatched, disabled or incompletely approved files are preserved locally
and recorded as rejected degradation; their values never enter the forecast.

## Operational boundary

This is advisory-only collection. It uses no FPL login, browser, manager
identifier or account write. Raw source payloads remain local and gitignored.
Do not activate or purchase a source merely to fill a degraded slot: selection
requires a separate owner review and later value ablation.
