# WP-09 status — decision record and evaluation

**Package:** WP-09  
**Done when (plan):** GDR schema covers §3.1; harness replays a GW cheaply for §17.6 volumes; baseline comparison and retrospective metrics from recorded data alone.

## Checklist

- [x] `gameweek_decision_records` schema + example + catalog entry
- [x] Section 3.1 coverage helper (`section_31_coverage`)
- [x] Baseline comparison vs do-nothing (`src/reporting/baseline_comparison.py`)
- [x] Retrospective metrics from recorded GDR (+ optional realised/hindsight points)
- [x] Replay harness (`src/orchestration/replay_harness.py`) + `scripts/run_replay.py`
- [x] ADR-0014 — historical seasons for event-level data (Open Decision 6 — Proposed)
- [ ] Live multi-season manager-state corpus — uses synthetic/optimiser fixtures until live capture

## Run

```bash
PYTHONPATH=. python3 -m scripts.run_replay
PYTHONPATH=. python3 -m scripts.run_replay --batch 20
PYTHONPATH=. python3 -m pytest tests/test_decision_record_replay.py -q
```
