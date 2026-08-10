# Initial-squad fixture audit companion

**Status:** active  
**Schema:** `initial-squad-fixture-audit-v1`

## Purpose

The optimiser packet keeps compact six-GW vectors. Agents and humans need an
explicit per-player-week audit trail to reason over fixture-driven EP moves.

## Location

Written beside a checkpoint recommendation as `fixture-audit.json`, referenced
from `feature_state.fixture_audit_sha256` and the packet lineage.

## Fields (per player-week fixture)

- `fixture_id`, `blank`, `double`
- `opponent_club_id` / `opponent_name`
- `was_home`, `kickoff_time`, official `fdr`
- `attack_multiplier`, `defence_multiplier`, `team_multiplier`
- `expected_team_xg`, `expected_opponent_xg` (pre-clip signals)
- `elo_expected_score`, `odds_expected_score` when present
- `expected_minutes`, rate/event/component EP

## Bounded strategy view

Use `bounded_fixture_audit_view(audit, player_ids=...)` or manually subset to
the selected XV plus a short top-EP list. Do not dump the full eligible
universe into an LLM context.
