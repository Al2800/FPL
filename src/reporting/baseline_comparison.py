"""Baseline comparison and retrospective metrics from recorded decision data."""

from __future__ import annotations

from typing import Any


def compare_to_do_nothing(
    *,
    recommended_objective: float,
    do_nothing_objective: float,
    notes: str = "",
) -> dict[str, Any]:
    """Paired comparison of recommended plan vs do-nothing (plan §3.1 / §17.3)."""
    advantage = round(float(recommended_objective) - float(do_nothing_objective), 4)
    return {
        "comparison_basis": "expected_proxy",
        "is_realised": False,
        "do_nothing_objective": float(do_nothing_objective),
        "recommended_objective": float(recommended_objective),
        "expected_advantage": advantage,
        "notes": notes
        or "Recommended objective minus no-transfer / do-nothing objective",
    }


def compare_realised_outcomes(
    *,
    evaluated_outcome: dict[str, Any],
    baseline_outcome: dict[str, Any],
    counterfactual_type: str,
) -> dict[str, Any]:
    """Compare two frozen plans scored from the same revealed episode."""
    allowed = {"do_nothing", "captain", "transfer", "bench", "chip", "policy_arm"}
    if counterfactual_type not in allowed:
        raise ValueError(f"unsupported counterfactual_type: {counterfactual_type}")
    for field in ("episode_id", "season", "gameweek", "source_outcome_sha256"):
        if evaluated_outcome.get(field) != baseline_outcome.get(field):
            raise ValueError(f"realised alternatives must share {field}")
    evaluated_rules = evaluated_outcome.get("ruleset") or {}
    baseline_rules = baseline_outcome.get("ruleset") or {}
    if evaluated_rules.get("content_sha256") != baseline_rules.get("content_sha256"):
        raise ValueError("realised alternatives must share the scoring ruleset")
    for label, outcome in (("evaluated", evaluated_outcome), ("baseline", baseline_outcome)):
        if not outcome.get("plan_id") or not outcome.get("plan_sha256"):
            raise ValueError(f"{label} outcome is missing frozen plan provenance")
        if "gross_points" not in outcome:
            raise ValueError(f"{label} outcome is missing realised points")

    evaluated_points = float(evaluated_outcome["gross_points"])
    baseline_points = float(baseline_outcome["gross_points"])
    return {
        "comparison_basis": "realised_feasible_counterfactual",
        "is_realised": True,
        "counterfactual_type": counterfactual_type,
        "episode_id": evaluated_outcome["episode_id"],
        "season": evaluated_outcome["season"],
        "gameweek": int(evaluated_outcome["gameweek"]),
        "evaluated": {
            "plan_id": evaluated_outcome["plan_id"],
            "plan_sha256": evaluated_outcome["plan_sha256"],
            "points": evaluated_points,
        },
        "baseline": {
            "plan_id": baseline_outcome["plan_id"],
            "plan_sha256": baseline_outcome["plan_sha256"],
            "points": baseline_points,
        },
        "realised_gain": round(evaluated_points - baseline_points, 4),
        "scoring_provenance": {
            "source_outcome_sha256": evaluated_outcome["source_outcome_sha256"],
            "ruleset_sha256": evaluated_rules["content_sha256"],
        },
    }

def extract_plan_objectives(solver_output: dict[str, Any]) -> dict[str, float | None]:
    """Pull strategy objectives from a WP-07 solver output artefact."""
    plans = solver_output.get("plans") or {}

    def obj(name: str) -> float | None:
        p = plans.get(name)
        if not p:
            return None
        return float(p["objective"])

    return {
        "highest_ev": obj("highest_ev"),
        "no_transfer": obj("no_transfer"),
        "bank_transfer": obj("bank_transfer"),
        "no_hit": obj("no_hit"),
        "hit": obj("hit"),
        "free_transfer": obj("free_transfer"),
    }


def baseline_comparison_from_solver(solver_output: dict[str, Any]) -> dict[str, Any]:
    objs = extract_plan_objectives(solver_output)
    do_nothing = objs.get("no_transfer")
    recommended = objs.get("highest_ev")
    if do_nothing is None or recommended is None:
        raise ValueError("solver output missing no_transfer or highest_ev plans")
    return compare_to_do_nothing(
        recommended_objective=recommended,
        do_nothing_objective=do_nothing,
        notes="From recorded optimiser candidate plans",
    )


def retrospective_metrics(
    *,
    record: dict[str, Any],
    realised_points: float | None = None,
    hindsight_best_points: float | None = None,
) -> dict[str, Any]:
    """Compute §17.3-style metrics using only recorded GDR fields (+ optional outcomes)."""
    baseline = record.get("baseline_comparison") or {}
    plan = record.get("validated_plan") or {}
    rec = record.get("recommendation") or {}
    metrics: dict[str, Any] = {
        "expected_advantage_vs_do_nothing": baseline.get("expected_advantage"),
        "hit_cost": (plan.get("finance") or {}).get("hit_cost", 0),
        "n_transfers": len(plan.get("transfers") or []),
        "strategy": rec.get("strategy"),
        "validation_squad_ok": (record.get("validation") or {}).get("squad", {}).get("ok"),
        "validation_lineup_ok": (record.get("validation") or {}).get("lineup", {}).get("ok"),
    }
    if realised_points is not None:
        metrics["realised_points"] = float(realised_points)
        do_nothing = baseline.get("do_nothing_objective")
        if do_nothing is not None:
            metrics["realised_gain_vs_do_nothing_proxy"] = round(
                float(realised_points) - float(do_nothing), 4
            )
            # Note: do_nothing_objective is expected points, not realised — labelled proxy
            metrics["realised_gain_note"] = (
                "Proxy only unless do_nothing realised points are also recorded"
            )
    if realised_points is not None and hindsight_best_points is not None:
        metrics["decision_regret"] = round(
            float(hindsight_best_points) - float(realised_points), 4
        )
    return metrics


def attach_retrospective(
    record: dict[str, Any],
    *,
    process_notes: str,
    lessons: list[str] | None = None,
    realised_points: float | None = None,
    hindsight_best_points: float | None = None,
) -> dict[str, Any]:
    out = dict(record)
    metrics = retrospective_metrics(
        record=record,
        realised_points=realised_points,
        hindsight_best_points=hindsight_best_points,
    )
    out["retrospective"] = {
        "process_notes": process_notes,
        "lessons": list(lessons or []),
        "metrics": metrics,
    }
    if realised_points is not None:
        out["outcome"] = {
            "points": float(realised_points),
            "notes": "Attached at finalisation",
        }
    return out
