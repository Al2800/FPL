# 2026/27 GW1 live-readiness rehearsal

## What this proves

The GW1 rehearsal is the operational proof for the starting-15 decision path:

`immutable T-48h manifest → source coverage → forecast/optimiser checkpoint → legal squad validation → frozen advisory GDR`

It is deliberately an advisory procedure. It does not launch a browser, load an
FPL account-write mechanism, or submit a team. A successful operational
rehearsal also does not override the forecast packet's own approval blockers.
For example, the current repeated official `ep_next` baseline can produce a
legal and reproducible squad but remains blocked from approval until the
decision-grade six-GW forecast replaces it.

## T-48h input requirement

The exact official GW1 deadline determines the target as `deadline - 48 hours`.
The input manifest's observed and available timestamps must fall from that
target through the configured scheduler-lag allowance (15 minutes by default).
Earlier snapshots are useful for development, but cannot be re-labelled as the
rehearsal. Later snapshots are refused rather than substituted.

This ensures the first genuine production-shaped exercise uses only the
information that was actually available at T-48h.

## Command

```powershell
C:\Users\Alastair\FPL\.venv\Scripts\python.exe scripts/run_live_readiness_rehearsal.py `
  --checkpoint T-48h `
  --manifest data/snapshots/2026-27/preseason/<t48-checkpoint>/manifest.json `
  --output-root evals/live-readiness/2026-27-gw1
```

Run this after the immutable T-48h capture has completed. An optional final
checkpoint can be compared additively; it cannot alter the frozen rehearsal:

```powershell
C:\Users\Alastair\FPL\.venv\Scripts\python.exe scripts/run_live_readiness_rehearsal.py `
  --checkpoint T-48h `
  --manifest data/snapshots/2026-27/preseason/<t48-checkpoint>/manifest.json `
  --output-root evals/live-readiness/2026-27-gw1 `
  --final-checkpoint <final-initial-squad-checkpoint.json>
```

## Frozen outputs

The output directory is content-bound and idempotent:

- `input-manifest.json`, source coverage and policy request;
- the initial-squad packet, recommendation, diff and checkpoint;
- `gameweek-decision-record.json`, carrying the legal squad, lineup, captain,
  validation and provenance bindings;
- report with runtime metadata, recorded wall time, 10-minute deterministic
  checkpoint budget and 30-minute overall budget;
- rerun comparison binding all immutable payload hashes.

Required source or integrity failures produce no frozen recommendation. Missing
optional families are explicit degraded coverage and permit only the structured
advisory fallback. Any different request for the same rehearsal directory is
an immutable conflict.

## Current operational position

The code path is tested against a synthetic T-48h immutable fixture. The real
T-48h run remains scheduled for its actual window. Before it can be presented
as an approval-ready initial squad, the decision-grade six-GW forecast policy
must replace the explicitly labelled flat-`ep_next` operational baseline and
the forecast's own gates must be satisfied.
