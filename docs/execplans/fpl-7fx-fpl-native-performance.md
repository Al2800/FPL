# FPL-7fx — FPL-native weekly performance features

## Goal

Create one immutable, point-in-time player-gameweek feature artifact from
approved official FPL snapshots. Keep this family distinct from external
0-to-10 match ratings and make missing input an exact byte-identical fallback.

## Source hierarchy

1. `event-live` is the primary weekly total after the gameweek is final.
2. `element-summary` supplies per-fixture rows and detects doubles, blanks, and
   disagreement with the event aggregate.
3. `bootstrap-static` snapshots immediately before and after the gameweek
   provide an independent cumulative-delta check.
4. Player `code`, not transient element ID or name, is the stable join key.

Every input is an acquisition envelope containing exact observation and
availability timestamps, a manifest ID, raw-source SHA-256, canonical payload
SHA-256, and decoded payload. Future inputs and hash mismatches fail closed.

## Quality policy

- Missing required event metrics quarantine the player.
- Missing optional fields create visible gaps and null values.
- Invalid, decreasing cumulative, or cross-source-disagreeing values quarantine
  only the affected metric.
- A player with a valid event record remains usable when an optional metric is
  absent; this avoids excessive quarantine.
- Doubles sum fixture rows once and reconcile to the already aggregated
  event-live value.
- Blanks emit an explicit zero-fixture, zero-metric row when all three official
  sources agree.

## Outputs

- Content-addressed player-gameweek snapshot.
- Stable `fpl_code`, current element ID, fixture IDs/count, per-metric value,
  status, and source comparison.
- Source manifest and hash bindings.
- Quarantine and gap rates.
- An isolated overlay helper that returns the exact original baseline object
  when the snapshot is absent or has no admitted player metrics.

## Verification

- Correct cumulative deltas.
- Double and blank cases.
- Stable-code joins across element-ID change.
- Point-in-time and payload-hash refusal.
- Per-metric schema-drift and disagreement quarantine.
- Deterministic hashes and immutable writer.
- Byte-identical absent-input ablation.

## Progress

- [x] Design and source hierarchy.
- [x] Red tests.
- [x] Ingestion and immutable output.
- [x] CLI and source documentation.
- [x] Focused and regression tests.

