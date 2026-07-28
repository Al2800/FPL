# 2026/27 official FPL endpoint automation

Alastair approved automated collection of the public official FPL endpoints on
2026-07-28 for private, read-only analysis with local retention and no
redistribution. This approval does not include authentication, manager state,
or account actions.

## Approved endpoint policy

| Endpoint | Purpose | Checkpoints | Scope |
|---|---|---|---|
| `bootstrap-static` | Players, prices, teams, events, availability and FPL news fields | Daily preseason and all pre-deadline checkpoints | Complete public response |
| `fixtures` | Exact fixture and kickoff state | Daily preseason and all pre-deadline checkpoints | Complete public response |
| `element-summary/{player_id}` | Historical rounds, past seasons and future fixtures | Daily preseason and T-24h | Explicit owned/watchlist/candidate IDs only; maximum 40 per run |
| `event/{gw}/live` | Post-deadline outcome and reconciliation evidence | Post-match only | One explicit Gameweek |

`event-live` is never part of a pre-deadline decision packet.
`element-summary` never expands implicitly to every FPL player.

## Safety and data-quality behavior

- The full endpoint plan is validated before the first request.
- Only the four approved path shapes can reach the network.
- Requests are serial and limited to 64 per run.
- HTTP 429 stops the remaining plan and records `Retry-After`.
- HTTP and transport failures retain immutable manifests and visible gaps.
- Endpoint-specific required fields detect schema drift. The raw response is
  retained, but the endpoint is degraded rather than guessed or silently
  admitted.
- Repeating the same observation with identical bytes is idempotent.
- Bootstrap availability claims require exact `news_added` timestamps.
- Collection uses GET without credentials, cookies or account writes.
- Missing data preserves the frozen no-evidence control.

## Commands

Daily preseason state:

```powershell
.venv\Scripts\python.exe scripts\capture_live_evidence.py `
  --checkpoint daily_preseason `
  --output data\live-shadow\evidence\captures\daily-preseason.json
```

T-24h with an explicit candidate set:

```powershell
.venv\Scripts\python.exe scripts\capture_live_evidence.py `
  --checkpoint T-24h `
  --player-id 17 `
  --player-id 355 `
  --output data\live-shadow\evidence\captures\gw01-t24h.json
```

Post-match reconciliation:

```powershell
.venv\Scripts\python.exe scripts\capture_live_evidence.py `
  --checkpoint post_match `
  --gameweek 1 `
  --output data\live-shadow\evidence\captures\gw01-post-match.json
```

Every output records the checkpoint, planned and attempted requests, immutable
acquisition manifests, schema state, retry metadata, explicit gaps, ledger
hash, and `account_writes: false`.
