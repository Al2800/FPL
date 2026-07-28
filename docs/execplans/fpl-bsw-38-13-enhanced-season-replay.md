# Enhanced season replay (`FPL-bsw.38.13`)

This ExecPlan is a living implementation record. The experiment is deliberately
run in reviewable tranches; completing a tranche does not complete the Bead.

## Purpose

Run a non-canonical 2025/26 replay that separates:

1. the initial-squad seed (official Scout seed versus optimized seed);
2. the weekly structured policy (frozen no-evidence control);
3. bounded evidence adjustments; and
4. the interaction created by carrying different state through time.

The published canonical replay must remain byte-for-byte unchanged. All new
outputs are exploratory and production-ineligible.

## Experimental design

The primary comparison is a 2x2:

| Arm | Seed | Weekly policy |
| --- | --- | --- |
| `scout_structured` | official Scout | frozen structured engine |
| `optimized_structured` | optimized initial 15 | frozen structured engine |
| `scout_evidence` | official Scout | reviewed evidence adjustments |
| `optimized_evidence` | optimized initial 15 | reviewed evidence adjustments |

GW1 contains the seed decision only, so the evidence and structured versions of
each seed share the corresponding GW1 decision. Evidence can first diverge in
GW2.

Each gameweek binds to the same enhanced input pack. The two evidence arms use
the same frozen hosted interpretation and challenger decision; the host output
may be reused only when the target-player structured baselines match exactly.

## Tranche protocol

The runner accepts a hard `--stop-gameweek`. The first approved tranche is
GW1-GW5. It must:

- refuse a stop outside the implemented/reviewed boundary;
- carry the optimized-evidence policy state independently from GW1;
- reference immutable existing Scout and optimized structured controls;
- produce per-week sealed comparison artifacts and a sealed checkpoint;
- verify every referenced artifact hash;
- verify the canonical replay tree before and after execution;
- report transfers, hits, chips, substitutions, evidence action status,
  weekly points, cumulative points, state hashes, and factorial effects; and
- finish with `paused_for_review`, not `completed`.

No GW6 work is authorized by the first tranche.

## Implementation

- `src/orchestration/enhanced_season_replay.py` owns validation, the independent
  optimized-evidence trajectory, attribution, and sealed checkpoint output.
- `scripts/run_enhanced_season_replay.py` supplies repository paths and exposes
  the hard gameweek stop.
- `tests/integration/test_enhanced_season_replay.py` checks hash integrity,
  state continuity, canonical immutability, factorial arithmetic, and the GW5
  stop.
- `reports/benchmarks/2025-26-enhanced/` contains only the new experiment.
- `docs/evaluation/2025-26-enhanced-season-review.md` records tranche results
  and review decisions.

## Progress

- [x] Enhanced GW1-GW38 input packs prepared and sealed (`FPL-bsw.38.12`).
- [x] `FPL-bsw.38.13` claimed and overlapping file ownership checked.
- [x] Existing canonical, optimized-seed, and early-evidence state contracts
  inspected.
- [x] Implement the GW1-GW5 tranche runner and integration tests.
- [x] Run GW1-GW5 and record the review.
- [x] Pause before GW6.
- [x] Implement sealed GW6-GW10 checkpoint resume and tests.
- [x] Run GW6-GW10 and record the review.
- [x] Pause before GW11.
- [x] Audit the GW12-GW15 agent-fork adapter and immutable hosted artifacts.
- [x] Implement owned-state structured and evidence continuation from GW12.
- [x] Run GW11-GW15 and seal the chained checkpoint.
- [x] Pause before GW16.
- [x] Audit the GW16-GW20 later-agent artifacts and bind GW20 to the repaired
  complete `sol-v3` bundle.
- [x] Resume all four arm-owned states and run GW16-GW20.
- [x] Seal the GW16-GW20 checkpoint and pause before GW21.

## Discoveries and decisions

- Existing hosted evidence responses are proposal-only. Reusing them on the
  optimized seed is valid only when their frozen target-player baselines remain
  identical; otherwise the runner fails closed.
- Existing optimized-seed reports already provide the frozen no-evidence
  control through GW11. They are referenced, not overwritten.
- Existing Scout early-evidence reports provide the independently carried Scout
  evidence trajectory from GW2.
- Same-state control scoring is retained for the optimized evidence arm. It
  isolates a weekly evidence decision from the inherited-state effect, while
  the 2x2 trajectories measure the longitudinal interaction.

- The optimized seed recovered from -20 after GW2 to +2 after GW5. No evidence adjustment was applied: GW2/GW5 abstained and GW3/GW4 failed closed at the challenger gate.
- By GW10 the optimized structured seed led the Scout structured seed 553-518. GW7 Gabriel evidence cost the Scout evidence arm eight points but did not change the optimized plan, demonstrating inherited-state interaction rather than general evidence value.
- The project virtual environment is required for the full test suite. The machine Python cannot import the repository's local test packages. The project environment completed 622 tests successfully in 457.30 seconds after the GW10 extension.
- GW12 is an implementation boundary, not a state reset. From that week both structured controls and both evidence arms are regenerated from their own GW11 successor states.
- Later hosted evidence output can be reused only as a frozen projection proposal after exact target-player baseline equality. The per-arm application bundle records the original host hash, owned starting state, and candidate-binding limitation.
- At GW15 the terminal totals are 736 Scout structured, 768 optimized structured, 733 Scout evidence, and 803 optimized evidence. The terminal seed/evidence interaction is +38; it must not be reported as direct same-week agent value.
- Focused enhanced replay and fork-adapter validation completed 27 tests successfully after the GW15 extension.
- The full project suite completed 624 tests successfully in 430.51 seconds after GW15; stderr was empty and JUnit output is retained with the enhanced validation artifacts.
- GW20 must use the clean `sol-v3` host bundle. `sol-v1` degraded at the
  challenger boundary and `sol-v2` is a partial diagnostic attempt, so neither
  is an admissible replay source.
- At GW20 the terminal totals are 1,017 Scout structured, 1,062 optimized
  structured, 1,003 Scout evidence, and 1,094 optimized evidence. The
  longitudinal seed/evidence interaction is +46.
- Same-state evidence effects in GW16-GW20 were respectively `0/0`, `+2/+3`,
  `-1/+9`, `0/0`, and `0/0` for Scout/optimized. GW18 demonstrates why
  current-decision effects must be reported separately from inherited
  trajectory scores.
- Focused enhanced replay and agent-fork validation completed 34 tests
  successfully after the GW20 extension.
- The full project suite completed 627 tests successfully in 414.70 seconds after GW20; stderr was empty and JUnit output is retained with the enhanced validation artifacts.


## Validation commands

    .venv\Scripts\python.exe -m pytest tests/integration/test_enhanced_season_replay.py
    .venv\Scripts\python.exe -m scripts.run_enhanced_season_replay --start-gameweek 1 --stop-gameweek 5
    .venv\Scripts\python.exe -m scripts.run_enhanced_season_replay --start-gameweek 6 --stop-gameweek 10
    .venv\Scripts\python.exe -m scripts.run_enhanced_season_replay --start-gameweek 11 --stop-gameweek 15
    .venv\Scripts\python.exe -m scripts.run_enhanced_season_replay --start-gameweek 16 --stop-gameweek 20
    .venv\Scripts\python.exe -m pytest

## Remaining work after tranche four

Review the causal GW17-GW18 differences before authorising GW21. The next
tranche must resume all four arm-owned GW20 successor states, preserve the
frozen no-evidence controls, and continue the same later evidence regime unless
a separately named fork is registered. The broad production evidence
acquisition and deterministic candidate-boundary retrieval design is tracked
separately by `FPL-bsw.38.14`; it must not silently alter this frozen
retrospective path. Chip-policy integration and named data ablations remain
explicit future layers.
