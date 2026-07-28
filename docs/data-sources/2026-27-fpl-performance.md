# 2026/27 FPL-native weekly performance features

## Purpose

This feature family measures player performance using only the approved public
FPL endpoints. It is not an external match rating. BPS, ICT components, FPL
xG/xA/xGI, minutes, starts, defensive contributions, recoveries, and FPL points
retain their native definitions and are evaluated as one isolated shadow arm.

## Official source hierarchy

- `event/{gameweek}/live/` is the primary gameweek total.
- `element-summary/{player_id}/` supplies fixture-level history for explicit
  owned, watched, and solver-evaluated players. Two rows in the same round form
  a double; no row plus zero official totals is a blank.
- `bootstrap-static/` immediately before and after the gameweek supplies a
  cumulative-delta cross-check and the stable FPL player `code`.

The element ID can change between snapshots. Every output joins on `code`;
names are never used as identity.

## Input bundle

`scripts/capture_fpl_performance.py` consumes one JSON bundle with:

- `season`, `gameweek`, and the post-gameweek `cutoff`;
- `bootstrap_before`, `bootstrap_after`, and `event_live` envelopes;
- zero or more `element_summaries`, each with `fpl_player_id`.

Every envelope contains:

- `manifest_id`;
- raw acquisition `source_sha256`;
- canonical decoded `payload_sha256`;
- exact `observed_at` and `available_at`;
- decoded `payload`.

The existing official-FPL collector supplies the immutable endpoint bodies and
manifests. A deterministic assembly step adds the canonical payload hash. Any
future timestamp, tampered payload, duplicate stable identity, or malformed
required source fails before an output is written.

## Quality and quarantine

The event-live value is admitted only when available and numeric. It is compared
with the element-summary fixture sum and bootstrap cumulative delta:

- exact comparison for integer metrics;
- small configured tolerances for decimal rounding;
- disagreement, invalid numbers, and decreasing cumulative values quarantine
  the affected metric;
- a missing required event metric degrades the player;
- a missing optional metric becomes a visible null/gap.

This field-level policy avoids discarding valid minutes, points, or xG merely
because a newly introduced optional field is temporarily absent. Silence means
unknown, not zero. The exception is a verified blank: zero fixtures and zero
weekly/cumulative values.

## Doubles and blanks

Element-summary rows are summed once per fixture and compared with the already
aggregated event-live total. Fixture IDs are unique. A double therefore has two
fixture rows but one player-gameweek output. A blank has `fixture_count=0`,
`blank=true`, and zero values only when the official sources agree.

## Isolated ablation

The snapshot remains separate from external 0-to-10 player ratings. The helper
`apply_fpl_performance_ablation` adds a hash-bound feature-family overlay when
admitted metrics exist. When the snapshot is absent—or contains no admitted
metric—it returns the exact original baseline object, enabling a byte-identical
degraded control.

Promotion beyond shadow use requires a preregistered isolated ablation; this
source family is not assumed valuable merely because it is available.

## Example

```powershell
python scripts/capture_fpl_performance.py `
  --bundle data/live-shadow/fpl-performance/gw-01-bundle.json `
  --output data/live-shadow/fpl-performance/gw-01.json
```

Add `--baseline` and `--ablation-output` together to create a separate
hash-bound shadow-arm input. The command performs no network or account writes.

