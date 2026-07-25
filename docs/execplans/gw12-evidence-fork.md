# Run an exploratory GW12 evidence fork

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds. It is maintained in accordance with `C:/Users/Alastair/.codex/.agent/PLANS.md`.

## Purpose / Big Picture

This experiment tests whether information published before the 2025/26 Gameweek 12 deadline would have changed the benchmark engine's decision. It must leave the canonical replay untouched. The user can run one command and inspect a separate set of evidence, adjusted forecast, frozen plan, official score and comparison artifacts.

This is an exploratory retrospective reconstruction, not an unbiased evidence-agent benchmark. The source pages were published before the deadline but were recovered in July 2026 rather than captured live in November 2025. The output must state that limitation prominently.

## Progress

- [x] (2026-07-25 10:35Z) Create and claim Bead `FPL-98p`, separate from the production evidence-agent and counterfactual-evaluation beads.
- [x] (2026-07-25 10:42Z) Establish three score ceilings across GW1–27: actual selected plan, hindsight-best XI and captain from the selected 15, and a position-only whole-market upper bound.
- [x] (2026-07-25 10:48Z) Recover pre-deadline Gabriel and Semenyo availability reports and identify the exact GW12 cutoff as `2025-11-22T11:00:00Z`.
- [x] (2026-07-25 10:55Z) Prove the isolated fork in memory: governed Gabriel unavailability plus a bounded Semenyo start-probability reduction changes the action to Gabriel→Muñoz and scores 43 versus 29.
- [ ] Add red contracts for temporal rejection, canonical immutability, deterministic rerun and the 43-point isolated result.
- [ ] Implement the additive fork runner and committed reconstructed evidence bundle.
- [ ] Run the isolated fork twice, pass focused and complete tests, and publish the review artifacts without creating a GW13 fork.
- [ ] Review the isolated result before implementing the longitudinal GW13+ continuation.

## Surprises & Discoveries

- Observation: the active squad itself could not produce a 100-point week in GW1–27.
  Evidence: hindsight-perfect legal formations and captaincy drawn from each selected 15 peaked at 89 in GW17. The engine scored 88 that week.

- Observation: the whole market contained far more weekly upside than the selected squads.
  Evidence: a deliberately loose position-only hindsight upper bound exceeded 100 in every completed Gameweek. It ignores budget and club limits, so it is an opportunity ceiling rather than a selectable FPL team.

- Observation: the recovered GW12 evidence is decision-relevant.
  Evidence: Gabriel was reported out for weeks and Semenyo was a material ankle doubt before the deadline. The structured forecast still assigned them 85.6 and 87.7 expected minutes.

- Observation: the policy-bounded evidence fork gains 14 realised points immediately.
  Evidence: the fork selects Gabriel→Daniel Muñoz. Muñoz scored 14, and Rodon becomes the legal automatic substitute for zero-minute Semenyo. The frozen fork scores 43 versus the canonical 29.

- Observation: publication-time validity and historical capture completeness are different claims.
  Evidence: the pages are dated before the deadline, but this repository did not observe them until July 2026. Production evidence eligibility correctly rejects the retrospective `observed_at`; this experiment uses an explicit reconstruction mode without weakening that gate.

## Decision Log

- Decision: keep the canonical replay as the immutable control and write all fork output below `reports/benchmarks/2025-26-forks/gw-12`.
  Rationale: a retrospective experiment must not silently rewrite the evidence available to the primary benchmark.
  Date/Author: 2026-07-25 / Codex.

- Decision: run an isolated GW12 fork before carrying altered state forward.
  Rationale: this separates the direct value of evidence interpretation from compounding squad, finance and transfer effects.
  Date/Author: 2026-07-25 / Codex.

- Decision: set Gabriel unavailable and reduce Semenyo's start probability by the policy maximum of 0.25.
  Rationale: Gabriel's absence was confirmed for weeks; Semenyo remained uncertain. The distinct treatments preserve the strength of each source claim and the existing bounded-adjustment policy.
  Date/Author: 2026-07-25 / Codex.

- Decision: label recovered evidence `retrospective_published_before_deadline` and record both publication and 2026 capture timestamps.
  Rationale: inventing a 2025 observation timestamp would defeat the temporal evidence controls. The fork may answer a what-if while remaining ineligible as headline historical agent evidence.
  Date/Author: 2026-07-25 / Codex.

## Outcomes & Retrospective

The in-memory milestone demonstrates feasibility and an interesting effect: the constrained evidence changes one free transfer and improves GW12 by 14 points. No conclusion about season-long agent superiority is yet justified. The selected squad's low weekly ceiling also shows why availability evidence alone will not generate 100-point weeks; that requires earlier squad-construction, captaincy and chip opportunities.

## Context and Orientation

The canonical chronological replay lives below `reports/benchmarks/2025-26`. Each Gameweek contains a sealed setup, one frozen plan per arm, an official realised outcome and an arm-specific next state. GW12's evidence-agent arm currently falls back to the structured forecast because no historical evidence bundle was available.

`src/evidence/lifecycle.py` contains the production temporal and confidence policy. `src/optimisation/solver.py` turns a `SolverInput` into candidate transfers, lineup and captaincy. `src/orchestration/validated_plan.py` freezes a candidate before outcome access. `src/evaluation/outcome_scorer.py` applies official scoring and automatic substitutions after freeze.

The new fork runner must reuse those components. It must not edit the canonical setup or call the canonical finaliser. A “score ceiling” is a hindsight diagnostic: the best score that could be formed after results are known. It is never an input to the decision.

## Plan of Work

Add `evals/evidence-forks/2025-26/gw-12/evidence-bundle.json` containing source metadata, paraphrased grounded claims, player IDs and declared adjustments. The bundle records publication precision, the 2026 capture timestamp and the retrospective reconstruction mode.

Add `src/orchestration/evidence_fork.py`. It validates required fields and timestamps, rejects sources published after the deadline, applies only the two supported adjustment types, runs the existing optimiser, freezes an evidence-agent plan, then and only then opens the hidden outcome. It writes canonical JSON through a fail-on-difference helper so reruns are idempotent.

Add `scripts/run_evidence_fork.py` as the CLI. The first version supports isolated GW12 only. It prints a compact comparison and refuses to write into the canonical replay root.

Add `tests/historical-replay/test_evidence_fork.py`. Tests must prove post-deadline rejection, bounded adjustment behavior, a frozen plan before outcome scoring, unchanged canonical hashes, deterministic output, and the expected 43 versus 29 result.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run focused tests:

    .\.venv\Scripts\python.exe -m pytest tests/historical-replay/test_evidence_fork.py -q

Run the experiment:

    .\.venv\Scripts\python.exe -m scripts.run_evidence_fork --season 2025-26 --gameweek 12

Run it again and expect byte-identical output. Then run:

    .\.venv\Scripts\python.exe -m pytest -q --ignore=tests/historical-replay/test_walking_skeleton.py
    git diff --check

## Validation and Acceptance

The CLI must report the canonical score 29, fork score 43 and delta +14. The fork plan must contain Gabriel→Muñoz, Salah captain and no hit. Its evidence assessment must state that both sources were published before the deadline but reconstructed later. A source published one second after the deadline must fail before the optimiser runs.

Hash every canonical file below `reports/benchmarks/2025-26/gw-12` before and after the fork; the aggregates must match. A second run must reproduce all fork file bytes. No `gw-13` fork directory may exist.

## Idempotence and Recovery

The runner writes only missing files and accepts an existing file only when its bytes are identical. It never deletes or replaces evidence. If a bundle or code change would alter an existing fork, use a new experiment identifier rather than overwriting the old one.

## Artifacts and Notes

The GW12 cutoff is `2025-11-22T11:00:00Z`. The structured forecast assigned Gabriel 85.6 expected minutes and 6.09 expected points, and Semenyo 87.7 expected minutes and 6.11 expected points.

The initial sensitivity result is:

    canonical score: 29
    fork score:      43
    delta:           +14
    transfer:        Gabriel -> Daniel Muñoz
    captain:         Salah
    substitution:    Rodon -> Semenyo's effective slot

## Interfaces and Dependencies

No new package is required.

`src/orchestration/evidence_fork.py` will expose:

    def run_isolated_evidence_fork(
        *,
        season: str,
        gameweek: int,
        evidence_bundle_path: Path,
        canonical_root: Path,
        episode_root: Path,
        output_root: Path,
    ) -> dict[str, Any]

The return value is the persisted comparison artifact. The function must reject any canonical output root and must not load `hidden-outcome.json` until a validated plan with `frozen_at` and `content_sha256` exists.

Revision note (2026-07-25): Initial plan created after the score-ceiling analysis, source recovery and successful in-memory GW12 fork.
