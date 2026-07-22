# WP-07 status — optimisation

**Package:** WP-07  
**Done when (plan):** Open Decision 7 recorded as ADR; plans satisfy §12.1 hard constraints on golden cases; saved solver input reproduces output exactly.

## Checklist

- [x] ADR-0011 — transparent internal optimiser (not `open-fpl-solver` adaptation) — **Proposed**
- [x] ADR-0012 — single-Gameweek horizon for Phase 1 — **Proposed**
- [x] Constraints from `control/rules/` + validator (squad, lineup, hits, chips)
- [x] Candidate plans: `highest_ev`, `no_transfer`, `bank_transfer`, `no_hit` / `free_transfer`, `hit`
- [x] Reproducible JSON I/O + fingerprints (`evals/golden-cases/optimiser-gw3-*.json`)
- [x] Tests: `tests/test_optimiser.py`
- [x] Affordability filtering precedes expected-points buy-pool truncation
- [x] Ruleset mismatch fails closed unless allow_loaded is explicit
- [x] Incoming-player availability is governed by a recorded policy
- [x] Unsupported horizon, discount, solver-version and chip inputs fail explicitly
- [x] Results are labelled as highest EV in the declared candidate pool, not globally optimal
- [ ] Multi-Gameweek / chip-timing value — deferred (ADR-0012)
- [ ] Full Wildcard / Free Hit squad rebuild search — stubbed via hit accounting only

## Search-safety boundary

The optimiser is exact only inside its declared sell/buy pools, transfer limit and
same-position move model. Before a buy pool is ranked and capped, players that
cannot be afforded even under the conservative maximum sale-proceeds bound are
removed. This keeps an unaffordable high projection from hiding a feasible lower
projection. The output records the pool limits and policies and never claims a
global FPL optimum.


## Run

```bash
PYTHONPATH=. python3 -m scripts.run_optimiser evals/golden-cases/optimiser-gw3-input.json
PYTHONPATH=. python3 -m pytest tests/test_optimiser.py -q
```
