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
- [x] (2026-07-25 11:20Z) Added contracts for temporal rejection, canonical immutability, deterministic rerun and the 43-point isolated result.
- [x] (2026-07-25 11:28Z) Implemented the additive isolated runner and committed reconstructed evidence bundle.
- [x] (2026-07-25 11:35Z) Ran the isolated fork twice and published byte-identical review artifacts without creating a canonical GW13 fork.
- [x] (2026-07-26 03:48Z) Took over the remaining Bead work with explicit owner approval, separated four levels of score opportunity, and carried the altered state independently through GW38.
- [x] (2026-07-26 04:05Z) Reproduced the complete experiment through the fail-on-difference writer, passed 4 focused tests and passed all 418 repository tests.

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

- Observation: most of the isolated evidence gain disappears after legal state compounding.
  Evidence: GW12 gains 14 points, but the independently replanned GW12-GW38 branch finishes on 1,461 points versus 1,457 for the canonical same-period trajectory, leaving only +4 and a 2,014 versus 2,010 season total.

- Observation: the 100-point question changes materially with the feasibility boundary.
  Evidence: the fixed effective-lineup captain ceilings are 33 canonical and 55 fork; the original squad ceiling is 37; the fork's post-transfer squad ceiling is 58; a legal bounded three-transfer hindsight search reaches 99; only the infeasible whole-market position-only upper bound reaches 173.

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

- Decision: carry the fork through GW38 with evidence applied only at GW12 and ordinary structured replanning thereafter.
  Rationale: this isolates the compounding effect of the one evidence-informed decision without smuggling later reconstructed news into the branch.
  Date/Author: 2026-07-26 / Codex.

- Decision: publish separate feasibility-labelled ceiling tiers rather than one headline maximum.
  Rationale: a whole-market position-only score is useful for understanding theoretical upside but is not affordable or selectable; keeping it beside fixed-lineup, current-squad and bounded legal values prevents a misleading 100-point claim.
  Date/Author: 2026-07-26 / Codex.

## Outcomes & Retrospective

The experiment is complete. The constrained evidence changes one free transfer and improves GW12 by 14 points, but independent state compounding reduces that to +4 by GW38. This is useful process evidence, not a fair estimate of live agent value: the case was selected after outcomes and the sources were recovered later. The separated ceilings show that availability evidence alone could not create a 100-point selected team in GW12. A legal bounded three-transfer hindsight search reaches 99, while the 173-point whole-market figure is deliberately infeasible. The complete command reproduces through the sealed fail-on-difference writer; focused tests pass 4/4 and the repository passes 418/418.

## Context and Orientation

The canonical chronological replay lives below `reports/benchmarks/2025-26`. Each Gameweek contains a sealed setup, one frozen plan per arm, an official realised outcome and an arm-specific next state. GW12's evidence-agent arm currently falls back to the structured forecast because no historical evidence bundle was available.

`src/evidence/lifecycle.py` contains the production temporal and confidence policy. `src/optimisation/solver.py` turns a `SolverInput` into candidate transfers, lineup and captaincy. `src/orchestration/validated_plan.py` freezes a candidate before outcome access. `src/evaluation/outcome_scorer.py` applies official scoring and automatic substitutions after freeze.

The new fork runner must reuse those components. It must not edit the canonical setup or call the canonical finaliser. A “score ceiling” is a hindsight diagnostic: the best score that could be formed after results are known. It is never an input to the decision.

## Plan of Work

Add `evals/evidence-forks/2025-26/gw-12/evidence-bundle.json` containing source metadata, paraphrased grounded claims, player IDs and declared adjustments. The bundle records publication precision, the 2026 capture timestamp and the retrospective reconstruction mode.

`src/orchestration/evidence_fork.py` validates required fields and timestamps, rejects sources published after the deadline, applies only the two supported adjustment types, runs the existing optimiser, freezes an evidence-agent plan, then and only then opens the hidden outcome. It writes canonical JSON through a fail-on-difference helper so reruns are idempotent. It also exposes the completed ceiling review and longitudinal runner. The longitudinal runner transitions the fork plan into GW13, rebuilds each later solver input from the independent successor state and that week's sealed structured forecast, freezes before reveal, and records hashes rather than mutating canonical artifacts.

`scripts/run_evidence_fork.py` is the CLI. Its default `complete` mode runs the isolated fork, ceiling review and longitudinal branch. `--mode isolated` retains the short one-week workflow.

`tests/historical-replay/test_evidence_fork.py` proves post-deadline rejection, bounded adjustment behavior, a frozen plan before outcome scoring, unchanged canonical hashes, deterministic isolated output, exact ceiling labels and values, and the 27-week independent longitudinal lineage.

## Concrete Steps

Work from `C:/Users/Alastair/FPL`.

Run focused tests:

    .\.venv\Scripts\python.exe -m pytest tests/historical-replay/test_evidence_fork.py -q

Run the complete experiment:

    .\.venv\Scripts\python.exe -m scripts.run_evidence_fork --season 2025-26 --gameweek 12

Run it again and expect byte-identical output. Then run:

    .\.venv\Scripts\python.exe -m pytest -q --ignore=tests/historical-replay/test_walking_skeleton.py
    git diff --check

## Validation and Acceptance

The CLI must report the canonical score 29, fork score 43 and delta +14 for the isolated week, then 1,457 canonical versus 1,461 fork points for GW12-GW38. The fork plan must contain Gabriel→Muñoz, Salah captain and no hit. Its evidence assessment must state that both sources were published before the deadline but reconstructed later. A source published one second after the deadline must fail before the optimiser runs.

Hash every canonical file from `reports/benchmarks/2025-26/gw-12` through `gw-38` before and after the fork; the aggregates must match. A second run must reproduce all fork file bytes. The longitudinal branch is one sealed summary outside the canonical root, not a replacement `gw-13` checkpoint.

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

`src/orchestration/evidence_fork.py` exposes:

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

It also exposes:

    def build_gw12_score_ceiling_review(
        *,
        canonical_root: Path,
        episode_root: Path,
        fork_root: Path,
    ) -> dict[str, Any]

    def run_longitudinal_evidence_fork(
        *,
        season: str,
        gameweek: int,
        evidence_bundle_path: Path,
        canonical_root: Path,
        episode_root: Path,
        output_root: Path,
        terminal_gameweek: int = 38,
    ) -> dict[str, Any]

The ceiling review is explicitly outcome-informed and diagnostic. The longitudinal runner applies reconstructed evidence only at GW12 and returns a sealed comparison with one independent state chain through the requested terminal Gameweek.

Revision note (2026-07-25): Initial plan created after the score-ceiling analysis, source recovery and successful in-memory GW12 fork.

Revision note (2026-07-26): Completed the owner-authorised takeover by adding feasibility-labelled ceiling tiers and the independent GW12-GW38 continuation. Recorded that the isolated +14 compounds to only +4 and that no feasible selected-squad diagnostic reaches 100.
