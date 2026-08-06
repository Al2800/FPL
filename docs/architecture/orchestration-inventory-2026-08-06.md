# Orchestration and fork-runner inventory (ticket 12)

**Date:** 6 August 2026  
**Purpose:** Demonstrate the navigation/coupling problem before any package move.

## Counts

| Surface | Count |
| --- | ---: |
| `src/orchestration/*.py` modules (excl. `__init__`) | 36 |
| Heuristic live-path modules | 15 |
| Heuristic replay/experiment modules | 13 |
| Mixed / shared | 8 |
| `scripts/*.py` | 90 |
| Per-range agent-fork runners | 6 |

## Live vs replay coupling

Live decision path (should be discoverable in one hop from the handover brief):

- `run_gameweek.py` — canonical advisory chain
- `live_solver_adapter.py`, `manager_state.py`, `freshness_monitor.py`
- `deadline_capture_scheduler.py`, `scheduled_agent_overlay.py`
- `agent_arm.py`, `hosted_response.py`, `agent_trace.py`

Replay/experiment apparatus living beside it (largest modules):

- `genuine_replay.py` (~1.5k LOC), `agent_fork_adapter.py`, `evidence_fork.py`
- `enhanced_season_replay.py`, `historical_*`, `multiweek_challenger.py`

Shared checkpoints (`initial_squad_checkpoint.py`, `preseason_snapshot.py`,
`evidence_checkpoint_runner.py`) blur the boundary further.

## Duplicate per-GW fork runners

| Script | Gameweeks | Notes |
| --- | --- | --- |
| `scripts/run_gw12_agent_fork.py` | 12 | Special `build_gw12_agent_host_bundle` |
| `scripts/run_gw13_gw14_agent_forks.py` | 13–14 | Near-duplicate CLI |
| `scripts/run_gw15_gw17_agent_forks.py` | 15–17 | Near-duplicate CLI |
| `scripts/run_gw18_gw22_agent_forks.py` | 18–22 | Adds `--gameweek` choices |
| `scripts/run_gw23_gw29_agent_forks.py` | 23–29 | Sequential trajectory helpers |
| `scripts/run_gw30_gw38_agent_forks.py` | 30–38 | Sequential trajectory helpers |

Measurable maintenance cost: six entry points with copied argparse/mode
machinery; newcomers cannot find a single `--gws` command; CI and docs must
enumerate each range.

## Canonical live entry (today)

```text
python -m scripts.run_gameweek
# library: src.orchestration.run_gameweek.run_gameweek
```

## Smallest viable change

1. Document the live vs replay split (this file + handover brief link).
2. Add one parameterised dispatcher `scripts/run_agent_fork.py` that routes to
   the existing range runners without moving packages.
3. Defer any `src/orchestration` package split until ADR-0026 is accepted.
