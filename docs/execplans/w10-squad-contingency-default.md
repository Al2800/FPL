# Expected Autosub and Bench Objective Evaluation

This ExecPlan is a living document following the repository's established
`docs/execplans/` format because `.agent/PLANS.md` is absent.

## Purpose

Evaluate whether the existing opt-in `probabilistic_v1` squad-contingency
objective should become the production default. The experiment must compare
the same observed state with the policy off and on, use the official validator
and realised scorer, preserve sealed replay artifacts, and keep the eventual
one-field policy promotion owner-gated.

## Progress

- [x] (2026-07-28 20:25Z) Created and claimed `FPL-4r6` after W9 closed and
  confirmed that its evaluation files do not overlap active Beads.
- [x] (2026-07-28 20:30Z) Read the July W10 handoff, existing appearance
  calibration, contingency optimiser, official scoring path, initial-squad
  optimiser, sealed 2025/26 replay structure and historical 2024/25 estate.
- [x] (2026-07-28 20:46Z) Implemented same-state off/on evaluation, official
  validation/scoring, source bindings and latency-independent decision hashes.
- [x] (2026-07-28 21:02Z) Ran 38 locked 2024/25 lineup pairs and 37 sealed
  2025/26 same-state lineup forks without mutating canonical artifacts.
- [x] (2026-07-28 21:08Z) Published the rejection report and promotion note;
  production remains `none` and two follow-up Beads record discovered work.
- [x] (2026-07-28 21:22Z) Passed 4 focused, 59 affected, 29 rules-golden and
  728 full-suite tests.

## Discoveries

- The appearance distribution is already leakage-safe: it fits 2022/23 and
  2023/24 and has a locked 2024/25 Brier/log-loss improvement.
- Only 2025/26 has full immutable benchmark episodes and manager state.
  Therefore 2024/25 provides a locked, same-squad lineup/bench decision gate,
  while 2025/26 provides descriptive isolated same-state forks. These scopes
  remain separate.
- There is no dedicated 2024/25 rules catalogue. The locked evaluator uses the
  2025/26 historical catalogue only for unchanged squad, formation, autosub
  and captain-fallback boundaries; realised points are recorded 2024/25 FPL
  totals.
- An unrestricted three-transfer contingency fork did not complete within ten
  minutes. Holding transfers at zero for both arms reduced challenger lineup
  evaluation to about 75 ms locked and 65 ms descriptive on average.
- The locked gate failed: the challenger scored 2,411 against control's 2,421
  (-10), despite six more autosub points. The descriptive 2025/26 forks gained
  +22, but cannot override the locked loss or be summed as a longitudinal path.
- The locked loss was concentrated in seven non-zero weeks: GW2 -4, GW10 +1,
  GW13 +2, GW20 -5, GW34 +6, GW36 -6 and GW37 -4.
- `FPL-bsw.38` owns `control/policies/`. W10 generated evidence without touching
  that namespace; because the evidence gate failed, no owner approval is sought.

## Decisions

- Treat 2024/25 as the locked gate and 2025/26 as descriptive evidence.
- Hold transfers at zero for both arms. This is the exact same-squad lineup,
  bench-order and captaincy experiment requested by W10; transfer interaction
  is explicitly deferred to `FPL-bfi` rather than hidden behind a timeout.
- Preserve exact plan/outcome/source hashes and add a decision hash that omits
  only nondeterministic wall time.
- Publish rejection when locked realised value is negative. Later-season gains
  and better calibration cannot override the preregistered decision gate.
- Keep v1 opt-in. `FPL-bnd` will ablate XI, bench and captain components before
  any v2 is specified.

## Validation

Focused:

    .\.venv\Scripts\python.exe -m pytest tests/evaluation/test_squad_contingency_evaluation.py -q

Rules:

    .\.venv\Scripts\python.exe -m scripts.run_rules_golden

Affected:

    .\.venv\Scripts\python.exe -m pytest tests/evaluation tests/optimisation/test_squad_contingency.py -q

Full:

    .\.venv\Scripts\python.exe -m pytest -q

## Outcomes & Retrospective

W10 is complete and rejects promotion of `probabilistic_v1`. The sealed report
is `reports/evaluation/squad-contingency-v1.json`
(`f5c7b751...69b92`). Its latency-independent decision hashes are
`c877dbdc...12842` for locked 2024/25 and `1b963887...02c1` for descriptive
2025/26.

All 75 pairs were legal and used the official reveal-gated scorer. The locked
38-week result was -10 with 17 changed weeks; the descriptive 37-fork result
was +22 with 26 changed weeks. Production remains byte-identical and the
promotion note records the failed gate, scope limitations, runtime boundary
and required component/transfer follow-ups.

Validation passed: 4 focused tests, 59 affected tests, 29/29 rules golden and
728/728 full-suite tests in 506.67 seconds.