# 2026/27 Overall standings capture runbook

## Purpose

Capture official FPL Overall league (id 314) standings after each Gameweek is
final, then derive exact/bounded rank-threshold rows for reporting. Never use
these snapshots in pre-deadline decisions.

## Preconditions

1. `docs/data-sources/2026-27-overall-standings-decision.md` is approved.
2. Registry `fpl-official-endpoints` lists the leagues-classic/314 standings
   endpoint.
3. `config/data_sources/2026-27-rank-thresholds.json` has
   `owner_approved: true` and remains `collection_enabled: false` until an
   operator explicitly enables a single capture window.

## Finalisation rule

Capture only when:

- the Gameweek’s matches are complete;
- official auto-subs / score finalisation has occurred; and
- the operator records `finalised_at` at that checkpoint.

If the window is missed, record a gap. Do **not** reconstruct the checkpoint
from a later live standings response.

## Failure behaviour

- Missing page → gap row, continue
- Rate limit / outage → retain degraded evidence, no retry storm
- Disabled config → fail closed, no network

## Decision-path ban

Standings capture outputs set `decision_path_use: forbidden`.
