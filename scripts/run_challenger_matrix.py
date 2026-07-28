"""Generate the sealed 2025/26 challenger matrix and 2026/27 shadow nominee."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from src.evaluation.challenger_matrix import (
    PROMOTION_RULE,
    apply_promotion_rule,
    build_live_shadow_candidate,
    episode_bindings,
    evaluate_robust_legal_replay,
    validate_matrix_rows,
)
from src.forecasting.live_faithful import artifact_hash


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_repeatable(
    path: Path, value: dict[str, Any], *, replace_draft: bool = False
) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if (
        path.exists()
        and path.read_text(encoding="utf-8") != text
        and not replace_draft
    ):
        raise ValueError(f"refusing to overwrite differing sealed artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _hash(value: dict[str, Any]) -> str:
    expected = value.get("content_sha256")
    actual = artifact_hash(value)
    if expected != actual:
        raise ValueError("input artifact hash mismatch")
    return actual


def _evidence_hash(value: dict[str, Any]) -> str:
    """Bind legacy and current reports without rewriting old hash conventions."""
    return artifact_hash(value)


def _canonical_tree_hash(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    files = sorted(
        path
        for gameweek in range(1, 39)
        for path in (root / f"gw-{gameweek:02d}").rglob("*")
        if path.is_file()
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest(), len(files)


def _row(
    *,
    challenger_id: str,
    category: str,
    config: dict[str, Any],
    evidence: dict[str, Any],
    bindings: list[dict[str, Any]],
    decision: str,
    gates: dict[str, bool],
    disqualifiers: list[str],
    metrics: dict[str, float],
    uncertainty: str,
    degradation: str,
    report_path: str,
) -> dict[str, Any]:
    return {
        "challenger_id": challenger_id,
        "category": category,
        "configuration_sha256": _hash(config),
        "evidence_report_sha256": _evidence_hash(evidence),
        "evidence_embedded_content_sha256": evidence.get("content_sha256"),
        "evidence_report_path": report_path,
        "episode_bindings": deepcopy(bindings),
        "decision": decision,
        "gates": gates,
        "disqualifiers": disqualifiers,
        "selection_metrics": metrics,
        "uncertainty": uncertainty,
        "resources": {
            "cost_gbp": 0.0,
            "external_tool_calls": 0,
            "latency_and_memory_evidence": (
                "reports/performance/core-baseline.json and "
                "reports/performance/optimiser-scale.json"
            ),
        },
        "degradation": degradation,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recompute-robust",
        action="store_true",
        help="rerun all 37 legal robust solves instead of reusing the sealed report",
    )
    parser.add_argument(
        "--replace-draft-matrix",
        action="store_true",
        help="replace an uncommitted draft matrix; never changes control artifacts",
    )
    parser.add_argument(
        "--matrix-only",
        action="store_true",
        help="write evaluation artifacts without rewriting the live-shadow policy",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports/benchmarks/2025-26"
    episodes = root / "data/benchmark-v0/episodes/v1/2025-26"
    output_dir = root / "reports/benchmarks/2025-26-challenger-matrix"
    gameweeks = tuple(range(2, 39))
    canonical_before, canonical_file_count = _canonical_tree_hash(reports)
    bindings = episode_bindings(
        reports_root=reports, episodes_root=episodes, gameweeks=gameweeks
    )

    control = _read(root / "control/models/live-faithful-v1.feature-complete.json")
    event = _read(root / "control/models/live-faithful-v2.events.json")
    team = _read(root / "control/models/live-faithful-v2.team-context.json")
    recalibrated = _read(
        root / "control/models/live-faithful-v2.recalibrated.json"
    )
    appearance = _read(root / "control/models/appearance-distribution-v1.json")
    robust = _read(root / "control/models/live-faithful-v2.robust.json")
    horizon = _read(root / "control/policies/transfer-horizon-v1.json")
    captain = _read(root / "control/policies/captain-v1.json")
    chip = _read(root / "control/policies/chip-v1.json")

    control_review = _read(root / "reports/evaluation/2025-26-control-review.json")
    event_report = _read(
        root / "reports/forecasting/live-faithful-v2-events/evaluation.json"
    )
    team_report = _read(
        root / "reports/forecasting/live-faithful-v2-team-context/evaluation.json"
    )
    recalibrated_report = _read(
        root / "reports/forecasting/live-faithful-v2-recalibrated.json"
    )
    recalibrated_delta = recalibrated_report["locked_validation"][
        "delta_challenger_minus_control"
    ]
    robust_path = output_dir / "robust-legal-replay.json"
    if robust_path.exists() and not args.recompute_robust:
        robust_legal = _read(robust_path)
        if (
            _hash(robust_legal) != robust_legal["content_sha256"]
            or robust_legal["model_config_sha256"] != _hash(robust)
            or robust_legal["gameweeks"] != list(gameweeks)
        ):
            raise ValueError("sealed robust legal replay is incompatible")
    else:
        robust_legal = evaluate_robust_legal_replay(
            reports_root=reports,
            episodes_root=episodes,
            config=robust,
            rules_path=root / "control/rules/2025-26.yaml",
            gameweeks=gameweeks,
        )
        _write_repeatable(robust_path, robust_legal)
    multiweek = _read(
        root / "reports/benchmarks/2025-26-multiweek/gw-12/comparison.json"
    )
    captain_report = _read(
        root / "reports/benchmarks/2025-26-captain/evaluation.json"
    )
    chip_report = _read(
        root
        / "reports/benchmarks/2025-26-counterfactuals/gw-31/evaluation.json"
    )
    evidence = _read(
        root / "reports/benchmarks/2025-26-evidence-programme/evaluation.json"
    )
    robust_calibration = _read(
        root / "reports/forecasting/live-faithful-v2-robust-evaluation.json"
    )
    core_performance = _read(root / "reports/performance/core-baseline.json")
    optimiser_scale = _read(root / "reports/performance/optimiser-scale.json")

    all_true = {gate: True for gate in PROMOTION_RULE["required_gates"]}
    rows: list[dict[str, Any]] = [
        _row(
            challenger_id="event-model-v2",
            category="forecast",
            config=event,
            evidence=event_report,
            bindings=bindings,
            decision="rejected",
            gates={**all_true, "locked_held_out_gate": False},
            disqualifiers=["failed_locked_gate"],
            metrics={
                "held_out_decision_quality": -0.052,
                "full_replay_realised_net_points": 0.0,
                "calibration": -0.118,
                "operational_cost": 1.0,
            },
            uncertainty=(
                "selected-XI MAE improved slightly, all-player MAE and "
                "correlation worsened"
            ),
            degradation="optional odds and evidence degrade to structured inputs",
            report_path=(
                "reports/forecasting/live-faithful-v2-events/evaluation.json"
            ),
        ),
        _row(
            challenger_id="team-context-v2",
            category="forecast",
            config=team,
            evidence=team_report,
            bindings=bindings,
            decision="rejected",
            gates={**all_true, "locked_held_out_gate": False},
            disqualifiers=["failed_locked_gate"],
            metrics={
                "held_out_decision_quality": -0.21,
                "full_replay_realised_net_points": 0.0,
                "calibration": -0.137,
                "operational_cost": 1.1,
            },
            uncertainty=(
                "2025/26 player MAE worsened for all, owned, and selected players"
            ),
            degradation="missing registered odds degrades to xG plus Elo",
            report_path=(
                "reports/forecasting/live-faithful-v2-team-context/evaluation.json"
            ),
        ),
        _row(
            challenger_id="top-bin-recalibration-v2",
            category="forecast",
            config=recalibrated,
            evidence=recalibrated_report,
            bindings=bindings,
            decision="rejected",
            gates={**all_true, "locked_held_out_gate": False},
            disqualifiers=["failed_locked_gate"],
            metrics={
                "held_out_decision_quality": -float(
                    recalibrated_delta["mean_top15_ranking_regret"]
                ),
                "full_replay_realised_net_points": 0.0,
                "calibration": -float(recalibrated_delta["all_player_rmse"]),
                "operational_cost": 1.0,
            },
            uncertainty=(
                "selected top-15 MAE improved, but locked top-15 precision, "
                "ranking regret, premium rank correlation and overall RMSE worsened"
            ),
            degradation=(
                "recalibration is post-composition and optional; rejection keeps "
                "the production v1 forecast unchanged"
            ),
            report_path=(
                "reports/forecasting/live-faithful-v2-recalibrated.json"
            ),
        ),
        _row(
            challenger_id="squad-contingency-v1",
            category="selection",
            config=appearance,
            evidence=appearance,
            bindings=bindings,
            decision="deferred",
            gates={**all_true, "legal_replay": False},
            disqualifiers=["missing_full_legal_replay"],
            metrics={
                "held_out_decision_quality": 0.00944577,
                "full_replay_realised_net_points": 0.0,
                "calibration": 0.01344101,
                "operational_cost": 5.49,
            },
            uncertainty=(
                "appearance calibration passes but paired realised full-season "
                "decisions are absent"
            ),
            degradation="policy is opt-in; omission preserves the control objective",
            report_path="control/models/appearance-distribution-v1.json",
        ),
        _row(
            challenger_id="robust-selection-v2",
            category="selection",
            config=robust,
            evidence=robust_legal,
            bindings=bindings,
            decision="eligible_for_live_shadow",
            gates=all_true,
            disqualifiers=[],
            metrics={
                "held_out_decision_quality": 2.2105263157894655,
                "full_replay_realised_net_points": float(
                    robust_legal["summary"]["net_points_delta"]
                ),
                "calibration": 0.04488830960859502,
                "operational_cost": 5.0,
            },
            uncertainty=(
                "locked MAE/regret improve; final MAE improves but unconstrained "
                "ranking regret worsens"
            ),
            degradation=(
                "any missing reliability, timeout, or validation failure falls "
                "back to control"
            ),
            report_path=(
                "reports/benchmarks/2025-26-challenger-matrix/"
                "robust-legal-replay.json"
            ),
        ),
        _row(
            challenger_id="transfer-horizon-v1",
            category="transfer",
            config=horizon,
            evidence=multiweek,
            bindings=bindings,
            decision="exploratory_only",
            gates={**all_true, "no_known_temporal_leakage": False},
            disqualifiers=["historical_schedule_provenance_gap"],
            metrics={
                "held_out_decision_quality": 0.0,
                "full_replay_realised_net_points": 18.0,
                "calibration": 0.0,
                "operational_cost": 3.1,
            },
            uncertainty=(
                "isolated GW12 result uses a retrospectively reconstructed schedule"
            ),
            degradation=(
                "node-budget exhaustion returns the deterministic one-week control"
            ),
            report_path=(
                "reports/benchmarks/2025-26-multiweek/gw-12/comparison.json"
            ),
        ),
        _row(
            challenger_id="captain-v1",
            category="captain",
            config=captain,
            evidence=captain_report,
            bindings=bindings,
            decision="rejected",
            gates={**all_true, "locked_held_out_gate": False},
            disqualifiers=["failed_locked_gate"],
            metrics={
                "held_out_decision_quality": -9.0,
                "full_replay_realised_net_points": 7.0,
                "calibration": 0.0,
                "operational_cost": 0.1,
            },
            uncertainty=(
                "only eight decisions changed and one produced an eleven-point loss"
            ),
            degradation="highest-expected-points captain remains the control",
            report_path="reports/benchmarks/2025-26-captain/evaluation.json",
        ),
        _row(
            challenger_id="chip-policy-v1",
            category="chip",
            config=chip,
            evidence=chip_report,
            bindings=bindings,
            decision="exploratory_only",
            gates={**all_true, "no_known_temporal_leakage": False},
            disqualifiers=["historical_schedule_provenance_gap"],
            metrics={
                "held_out_decision_quality": 0.0,
                "full_replay_realised_net_points": 28.0,
                "calibration": 0.0,
                "operational_cost": 6.0,
            },
            uncertainty=(
                "bounded chip search and reconstructed future schedule cannot "
                "support promotion"
            ),
            degradation=(
                "no-chip control is retained and chip use always requires human review"
            ),
            report_path=(
                "reports/benchmarks/2025-26-counterfactuals/gw-31/evaluation.json"
            ),
        ),
        _row(
            challenger_id="weekly-evidence-programme-v1",
            category="unstructured_evidence",
            config=control,
            evidence=evidence,
            bindings=bindings,
            decision="exploratory_only",
            gates={**all_true, "no_known_temporal_leakage": False},
            disqualifiers=["retrospective_case_selection"],
            metrics={
                "held_out_decision_quality": 0.0,
                "full_replay_realised_net_points": 4.0,
                "calibration": 0.0,
                "operational_cost": 1.0,
            },
            uncertainty=(
                "GW12 was selected and captured after outcomes; direct +14 "
                "compounded to +4"
            ),
            degradation=(
                "missing or invalid evidence uses the deterministic structured plan"
            ),
            report_path=(
                "reports/benchmarks/2025-26-evidence-programme/evaluation.json"
            ),
        ),
    ]
    validate_matrix_rows(rows)
    nominee = apply_promotion_rule(rows)
    if nominee is None:
        raise ValueError("promotion rule produced no live-shadow nominee")
    candidate_path = root / "control/policies/live-shadow-candidate.json"
    if args.matrix_only:
        candidate = _read(candidate_path)
        _hash(candidate)
        if candidate.get("shadow_policy", {}).get("challenger_id") != nominee:
            raise ValueError("sealed live-shadow candidate does not match nominee")
    else:
        candidate = build_live_shadow_candidate(
            nominee=nominee,
            rows=rows,
            control_model_sha256=_hash(control),
        )
    robust_row = next(
        row for row in rows if row["challenger_id"] == "robust-selection-v2"
    )
    robust_row["supporting_evidence"] = [
        {
            "path": (
                "reports/forecasting/live-faithful-v2-robust-evaluation.json"
            ),
            "sha256": _evidence_hash(robust_calibration),
            "embedded_content_sha256": robust_calibration.get("content_sha256"),
        }
    ]
    canonical_after, canonical_after_file_count = _canonical_tree_hash(reports)
    if (
        canonical_before != canonical_after
        or canonical_file_count != canonical_after_file_count
    ):
        raise ValueError("canonical replay tree changed during challenger evaluation")
    solver_profile = next(
        row for row in core_performance["workloads"] if row["name"] == "solver_golden"
    )
    matrix = {
        "schema_version": "1.0",
        "report_id": "2025-26-full-challenger-matrix",
        "comparison_gameweeks": list(gameweeks),
        "control": {
            "policy_id": "live-faithful-v1-control",
            "configuration_sha256": _hash(control),
            "evidence_report_sha256": _evidence_hash(control_review),
            "canonical_net_points": 2010,
            "mutated": False,
            "canonical_tree_sha256_before": canonical_before,
            "canonical_tree_sha256_after": canonical_after,
            "canonical_file_count": canonical_file_count,
        },
        "promotion_rule": PROMOTION_RULE,
        "rows": rows,
        "nomination": {
            "challenger_id": nominee,
            "mode": "observation_only",
            "candidate_config_sha256": candidate["content_sha256"],
            "control_remains_executable": True,
        },
        "interpretation": {
            "final_points_are_diagnostic_not_a_gate_override": True,
            "rejected_challengers_retained": True,
            "isolated_and_longitudinal_evidence_kept_separate": True,
        },
        "operational_profile": {
            "core_profile_sha256": _evidence_hash(core_performance),
            "optimiser_scale_profile_sha256": _evidence_hash(optimiser_scale),
            "solver_wall_ms": {
                key: solver_profile["wall_ms"][key]
                for key in ("p50", "p95", "p99")
            },
            "solver_python_heap_peak_bytes": solver_profile[
                "instrumented_memory_io"
            ][
                "python_heap_peak_bytes"
            ],
            "three_transfer_scale": optimiser_scale["widths"][-1],
            "historical_matrix_cost_gbp": 0.0,
            "live_interpretation": (
                "37 sequential historical decisions are a batch workload; "
                "live shadow runs one deadline at a time"
            ),
        },
    }
    matrix["content_sha256"] = artifact_hash(matrix)
    _write_repeatable(
        output_dir / "matrix.json",
        matrix,
        replace_draft=args.replace_draft_matrix,
    )
    if not args.matrix_only:
        _write_repeatable(
            candidate_path,
            candidate,
        )
    print(
        json.dumps(
            {
                "matrix": (output_dir / "matrix.json").as_posix(),
                "nominee": nominee,
                "robust_legal_delta": robust_legal["summary"]["net_points_delta"],
                "candidate": (
                    "unchanged (--matrix-only)"
                    if args.matrix_only
                    else (
                        candidate_path
                    ).as_posix()
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
