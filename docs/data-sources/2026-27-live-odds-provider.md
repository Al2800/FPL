# 2026/27 live odds provider

The selected provider is [The Odds API](https://the-odds-api.com/). It is
registered for private, local FPL analysis only. Raw responses must not be
redistributed or exposed as a standalone feed.

## Capture scope

- Sport: `soccer_epl`
- Region: `uk`
- Format: decimal
- Markets: `h2h,totals`
- Required completion market: `h2h` (home/draw/away)
- Optional market: `totals`
- Checkpoints: T-24h, T-8h, T-2h and final pre-deadline

One UK-region request for two markets costs at most two credits. Four clean
captures therefore cost at most eight credits per gameweek, or 304 credits
across 38 gameweeks, before retries. Every response records the provider's
`x-requests-last`, `x-requests-used` and `x-requests-remaining` headers.

## Secret setup

Never paste the key into chat, a CLI argument, a config file or Git. The
adapter reads only `THE_ODDS_API_KEY`.

For a process-local PowerShell session:

```powershell
$env:THE_ODDS_API_KEY = Read-Host -MaskInput "The Odds API key"
```

Run the command in that same PowerShell session. If Codex is expected to run
the live smoke test, start or restart Codex from an environment that already
contains `THE_ODDS_API_KEY`.

## Capture

The observation time must fall inside the configured window for the named
slot. This validation happens before the network request, so an incorrectly
scheduled command spends no credits.

```powershell
.venv\Scripts\python.exe scripts\capture_live_odds.py `
  --slot T-24h `
  --decision-cutoff 2026-08-21T17:30:00Z `
  --output data\live-shadow\odds\captures\gw01-t24h.json
```

The command exits:

- `0` for a complete capture;
- `1` for a sealed degraded capture, such as a rate limit or missing 1X2;
- `2` when it refuses to attempt or overwrite a capture.

The raw response and acquisition manifest are immutable and local. The
derived artifact contains a sanitized endpoint URL, response hashes,
observation and provider-update timestamps, normalized markets, quota state,
and any explicit data gaps. It never contains the API key.

## Forecast behavior

Odds remain a shadow input until live ablation establishes incremental value.
A missing, malformed, late, or rate-limited capture does not block the FPL
engine. All arms receive the same structured forecast without odds for that
checkpoint, and the gap remains visible for evaluation.
