# 2026/27 transactional evidence checkpoint runbook

## What one checkpoint does

One invocation creates a single reproducible chain:

`official deadline → authorised captures → governed ledger → active view →
candidate boundaries → bounded packet → coverage audit → immutable checkpoint`

The structured no-evidence control remains frozen throughout. A degraded or
missing evidence source is reported as a gap and never prevents that control
from running.

## Prerequisites

- Solver input and output for the gameweek. The output fingerprint must match
  the input.
- The latest ledger artifact, except for the first checkpoint.
- A captured official `bootstrap-static` document containing the gameweek
  deadline for any pre-deadline run.
- Optional manual observation and claim JSON files. Each manual observation
  needs `document_id`, an HTTP(S) `source_url`, `source_hash_sha256`, and
  `observed_at`. Each manual claim must repeat the exact document, URL, and hash
  tuple of an observation in the same source family.
- For odds checkpoints, `THE_ODDS_API_KEY` must be present in the environment
  inherited by the process. Never put the key in an argument, JSON file, log,
  or repository `.env`.

## Checkpoint schedule

The runner derives these timestamps from the exact official event
`deadline_time`:

- T-48h
- T-24h
- T-8h
- T-2h
- final pre-deadline (five minutes before the deadline)

The command accepts up to 15 minutes of scheduler lag by default and refuses
early or materially late runs. `daily_preseason` and `post_match` are not
pre-deadline timestamps.

The Odds API is currently a shadow-only supplemental input at T-24h, T-8h,
T-2h, and final. Its capture and acquisition-manifest hashes are bound into the
checkpoint, but it does not manufacture an evidence claim or directly alter a
decision.

## Example

```powershell
python scripts/run_evidence_checkpoint.py `
  --season 2026-27 `
  --gameweek 1 `
  --checkpoint T-24h `
  --decision-at 2026-08-20T17:30:00Z `
  --deadline-bootstrap data/live-shadow/fpl/gw-01/bootstrap-static.json `
  --solver-input data/live-shadow/solver/gw-01-input.json `
  --solver-output data/live-shadow/solver/gw-01-output.json `
  --current-ledger data/live-shadow/evidence/ledgers/<prior-hash>.json `
  --expected-entities data/live-shadow/evidence/gw-01-expected-entities.json `
  --with-odds
```

Add repeatable `--player-id` options only for owned, watched, or
solver-evaluated players. The official FPL collector caps both player IDs and
total requests.

## Output and recovery

- Raw bodies and their acquisition manifests are immutable under
  `data/live-shadow/`.
- Ledger versions are written by content hash.
- Checkpoints are written by request hash under season/gameweek/checkpoint.
- `control/manifests/evidence-checkpoint-head.json` is the only mutable pointer.
  Its adjacent persistent lock serialises writers.

An identical restart returns the prior checkpoint without calling collectors
or advancing the head. A different run holding a stale expected head is refused
before any collector is called. If a process crashes after writing an immutable
artifact but before advancing the head, the next run verifies and safely reuses
the content-addressed path.

## Alerts to monitor

- `status=degraded` or non-empty `degraded_reasons`
- source-family gaps and stale observations in `coverage_audit`
- non-zero retry-after values in bound captures
- quarantined, expired, future, superseded, or conflicting ledger claims
- a refused stale head, head hash mismatch, or ledger/head mismatch
- low expected-player or expected-club observation rates

Missing coverage means unknown, not available. It must never be translated into
a positive availability signal.
