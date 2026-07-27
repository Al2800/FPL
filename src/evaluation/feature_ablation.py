"""Point-in-time rolling-origin evaluation for one optional data family."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
import math
from statistics import mean, stdev
from typing import Any

from src.forecasting.live_faithful import artifact_hash


class FeatureAblationError(ValueError):
    """Raised when an ablation is temporally unsafe or not isolated."""


EXPECTED_FAMILIES = frozenset(
    {"odds", "team_strength", "set_piece_role", "player_ratings"}
)


def _timestamp(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise FeatureAblationError(f"{field} must be an ISO-8601 timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FeatureAblationError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if result.tzinfo is None:
        raise FeatureAblationError(f"{field} must include a timezone")
    return result


def _number(value: Any, field: str, *, non_negative: bool = False) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        raise FeatureAblationError(f"{field} must be a finite number")
    result = float(value)
    if non_negative and result < 0:
        raise FeatureAblationError(f"{field} must be non-negative")
    return result


def _sha256(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise FeatureAblationError(f"{field} must be a lowercase SHA-256")
    return value

def validate_preregistration(preregistration: Mapping[str, Any]) -> None:
    """Validate the sealed family matrix and fail-closed promotion thresholds."""

    if preregistration.get("content_sha256") != artifact_hash(preregistration):
        raise FeatureAblationError("preregistration content hash mismatch")
    if preregistration.get("status") != "frozen_before_live_outcomes":
        raise FeatureAblationError("preregistration is not frozen")
    families = preregistration.get("candidate_families")
    if not isinstance(families, dict) or set(families) != EXPECTED_FAMILIES:
        raise FeatureAblationError(
            "preregistration must declare every optional data family"
        )
    arm_ids = []
    for family, config in families.items():
        if config.get("family") != family:
            raise FeatureAblationError(f"{family} family identifier mismatch")
        arm_id = config.get("arm_id")
        if not isinstance(arm_id, str) or not arm_id:
            raise FeatureAblationError(f"{family} arm_id is required")
        arm_ids.append(arm_id)
        if config.get("mode") != "shadow_only":
            raise FeatureAblationError(f"{family} must begin shadow-only")
        if config.get("missing_input") != "degrade_to_shared_baseline":
            raise FeatureAblationError(
                f"{family} must declare baseline degradation"
            )
    if len(arm_ids) != len(set(arm_ids)):
        raise FeatureAblationError("candidate family arm_id values must be unique")
    folds = preregistration.get("rolling_origin_folds")
    if not isinstance(folds, list) or not folds:
        raise FeatureAblationError("rolling_origin_folds are required")
    fold_ids = []
    previous_test_end = 0
    live_season = str(preregistration.get("live_evaluation_season", ""))
    for fold in folds:
        fold_id = str(fold.get("fold_id", ""))
        if not fold_id:
            raise FeatureAblationError("fold_id is required")
        fold_ids.append(fold_id)
        if str(fold.get("test_season")) != live_season:
            raise FeatureAblationError("fold test season differs from live season")
        start = int(fold.get("test_start_gameweek", 0))
        end = int(fold.get("test_end_gameweek", 0))
        if start <= previous_test_end or end < start:
            raise FeatureAblationError(
                "rolling-origin test folds must be ordered and disjoint"
            )
        train_season = str(fold.get("train_end_season", ""))
        train_gameweek = int(fold.get("train_end_gameweek", 0))
        if train_season == live_season and train_gameweek >= start:
            raise FeatureAblationError(
                "fold training boundary must precede its test origin"
            )
        previous_test_end = end
    historical_folds = preregistration.get("exploratory_historical_folds", [])
    if not isinstance(historical_folds, list):
        raise FeatureAblationError("exploratory_historical_folds must be a list")
    for fold in historical_folds:
        fold_id = str(fold.get("fold_id", ""))
        if not fold_id or fold_id in fold_ids:
            raise FeatureAblationError("historical fold_id must be unique")
        if str(fold.get("test_season")) != "2025-26":
            raise FeatureAblationError("historical folds are restricted to 2025-26")
        if int(fold.get("test_start_gameweek", 0)) < 1 or int(
            fold.get("test_end_gameweek", 0)
        ) > 38:
            raise FeatureAblationError("historical fold bounds are invalid")
        fold_ids.append(fold_id)
    if len(fold_ids) != len(set(fold_ids)):
        raise FeatureAblationError("fold_id values must be unique")
    thresholds = preregistration.get("promotion_thresholds")
    required_thresholds = {
        "min_locked_folds",
        "min_episodes_per_fold",
        "max_proper_score_delta",
        "max_calibration_error_delta",
        "max_legal_regret_delta",
        "max_degradation_rate",
        "max_p95_latency_ms",
    }
    if not isinstance(thresholds, dict) or not required_thresholds <= set(
        thresholds
    ):
        raise FeatureAblationError("promotion thresholds are incomplete")


def _percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(probability * len(ordered)) - 1)
    return ordered[index]



def _shared_calibration_errors(
    rows: Sequence[Mapping[str, Any]], *, bins: int = 10
) -> dict[str, float]:
    actuals = [_number(row["actual"], "actual") for row in rows]
    arm_predictions = {
        arm: [
            _number(row[f"{arm}_prediction"], f"{arm}_prediction")
            for row in rows
        ]
        for arm in ("baseline", "candidate")
    }
    combined = arm_predictions["baseline"] + arm_predictions["candidate"]
    lower = min(combined)
    upper = max(combined)
    width = (upper - lower) / bins if upper > lower else 1.0
    result: dict[str, float] = {}
    for arm, predictions in arm_predictions.items():
        grouped: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
        for forecast, actual in zip(predictions, actuals, strict=True):
            index = min(int((forecast - lower) / width), bins - 1)
            grouped[index].append((forecast, actual))
        result[arm] = sum(
            len(values)
            * abs(
                mean(value[0] for value in values)
                - mean(value[1] for value in values)
            )
            for values in grouped
            if values
        ) / len(rows)
    return result

def _arm_metrics(
    rows: Sequence[Mapping[str, Any]], arm: str
) -> dict[str, Any]:
    predictions = [
        _number(row[f"{arm}_prediction"], f"{arm}_prediction")
        for row in rows
    ]
    actuals = [_number(row["actual"], "actual") for row in rows]
    decision_points = [
        _number(row[f"{arm}_decision_points"], f"{arm}_decision_points")
        for row in rows
    ]
    hindsight = [
        _number(row["hindsight_legal_points"], "hindsight_legal_points")
        for row in rows
    ]
    regrets = [
        best - selected
        for best, selected in zip(hindsight, decision_points, strict=True)
    ]
    if any(value < -1e-9 for value in regrets):
        raise FeatureAblationError(
            "hindsight_legal_points must dominate each feasible decision"
        )
    errors = [
        forecast - actual
        for forecast, actual in zip(predictions, actuals, strict=True)
    ]
    return {
        "n": len(rows),
        "mean_squared_error": mean(value * value for value in errors),
        "mean_absolute_error": mean(abs(value) for value in errors),
        "mean_legal_decision_regret": mean(regrets),
        "total_decision_points": sum(decision_points),
    }


def _paired_uncertainty(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    deltas = [
        _number(row["candidate_decision_points"], "candidate_decision_points")
        - _number(row["baseline_decision_points"], "baseline_decision_points")
        for row in rows
    ]
    average = mean(deltas)
    sample_sd = stdev(deltas) if len(deltas) > 1 else 0.0
    half_width = (
        1.96 * sample_sd / math.sqrt(len(deltas))
        if len(deltas) > 1
        else 0.0
    )
    return {
        "n": len(deltas),
        "mean_candidate_minus_baseline_points": average,
        "sample_standard_deviation": sample_sd,
        "confidence_interval_95": [
            average - half_width,
            average + half_width,
        ],
        "wins": sum(value > 0 for value in deltas),
        "ties": sum(value == 0 for value in deltas),
        "losses": sum(value < 0 for value in deltas),
    }


def evaluate_feature_ablation(
    *,
    rows: Sequence[Mapping[str, Any]],
    preregistration: Mapping[str, Any],
    family: str,
) -> dict[str, Any]:
    """Evaluate one isolated candidate family under the frozen live contract."""

    validate_preregistration(preregistration)
    if family not in EXPECTED_FAMILIES:
        raise FeatureAblationError(f"undeclared feature family: {family}")
    if not rows:
        raise FeatureAblationError("feature ablation requires at least one row")
    live_fold_ids = {
        str(fold["fold_id"])
        for fold in preregistration["rolling_origin_folds"]
    }
    declared_folds = {
        str(fold["fold_id"]): fold
        for fold in (
            list(preregistration["rolling_origin_folds"])
            + list(preregistration.get("exploratory_historical_folds", []))
        )
    }
    seen_episodes: set[str] = set()
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        episode_id = str(row.get("episode_id", ""))
        if not episode_id or episode_id in seen_episodes:
            raise FeatureAblationError(
                "episode_id values must be unique and non-empty"
            )
        seen_episodes.add(episode_id)
        for hash_field in (
            "source_snapshot_sha256",
            "baseline_plan_sha256",
            "candidate_plan_sha256",
            "outcome_sha256",
        ):
            _sha256(row.get(hash_field), hash_field)
        if row.get("feature_families") != [family]:
            raise FeatureAblationError(
                "candidate arm must differ by exactly the evaluated family"
            )
        if row.get("plan_legal") is not True:
            raise FeatureAblationError("ablation decisions must be legal")
        if _timestamp(
            str(row.get("available_at", "")), "available_at"
        ) >= _timestamp(
            str(row.get("decision_cutoff", "")), "decision_cutoff"
        ):
            raise FeatureAblationError(
                "feature observation is not strictly pre-cutoff"
            )
        fold_id = str(row.get("fold_id", ""))
        fold = declared_folds.get(fold_id)
        if fold is None:
            raise FeatureAblationError(f"undeclared fold_id: {fold_id}")
        if str(row.get("season")) != str(fold["test_season"]):
            raise FeatureAblationError("row season differs from declared fold")
        gameweek = int(row.get("gameweek", 0))
        if not int(fold["test_start_gameweek"]) <= gameweek <= int(
            fold["test_end_gameweek"]
        ):
            raise FeatureAblationError("row lies outside its declared fold")
        for field in (
            "baseline_prediction",
            "candidate_prediction",
            "actual",
            "baseline_decision_points",
            "candidate_decision_points",
            "hindsight_legal_points",
        ):
            _number(row.get(field), field)
        _number(
            row.get("candidate_latency_ms"),
            "candidate_latency_ms",
            non_negative=True,
        )
        if not isinstance(row.get("degraded"), bool):
            raise FeatureAblationError("degraded must be a boolean")
        grouped.setdefault(fold_id, []).append(row)

    fold_results = []
    for fold_id in declared_folds:
        fold_rows = grouped.get(fold_id, [])
        if not fold_rows:
            continue
        baseline = _arm_metrics(fold_rows, "baseline")
        candidate = _arm_metrics(fold_rows, "candidate")
        shared_calibration = _shared_calibration_errors(fold_rows)
        baseline["calibration_error"] = shared_calibration["baseline"]
        candidate["calibration_error"] = shared_calibration["candidate"]
        fold_results.append(
            {
                "fold_id": fold_id,
                "n": len(fold_rows),
                "baseline": baseline,
                "candidate": candidate,
                "candidate_minus_baseline": {
                    "proper_score": candidate["mean_squared_error"]
                    - baseline["mean_squared_error"],
                    "calibration_error": candidate["calibration_error"]
                    - baseline["calibration_error"],
                    "legal_decision_regret": candidate[
                        "mean_legal_decision_regret"
                    ]
                    - baseline["mean_legal_decision_regret"],
                    "decision_points": candidate["total_decision_points"]
                    - baseline["total_decision_points"],
                },
            }
        )

    baseline = _arm_metrics(rows, "baseline")
    candidate = _arm_metrics(rows, "candidate")
    shared_calibration = _shared_calibration_errors(rows)
    baseline["calibration_error"] = shared_calibration["baseline"]
    candidate["calibration_error"] = shared_calibration["candidate"]
    latency = [
        float(row["candidate_latency_ms"]) for row in rows
    ]
    degradation_rate = sum(bool(row["degraded"]) for row in rows) / len(rows)
    deltas = {
        "proper_score": candidate["mean_squared_error"]
        - baseline["mean_squared_error"],
        "calibration_error": candidate["calibration_error"]
        - baseline["calibration_error"],
        "legal_decision_regret": candidate["mean_legal_decision_regret"]
        - baseline["mean_legal_decision_regret"],
        "decision_points": candidate["total_decision_points"]
        - baseline["total_decision_points"],
    }
    thresholds = preregistration["promotion_thresholds"]
    seasons = sorted({str(row["season"]) for row in rows})
    historical_only = seasons == ["2025-26"]
    checks = {
        "not_historical_2025_26_only": not historical_only,
        "live_season_only": seasons
        == [str(preregistration["live_evaluation_season"])],
        "minimum_locked_folds": sum(
            result["fold_id"] in live_fold_ids for result in fold_results
        ) >= int(thresholds["min_locked_folds"]),
        "minimum_episodes_per_fold": bool(fold_results)
        and all(
            result["n"] >= int(thresholds["min_episodes_per_fold"])
            for result in fold_results
        ),
        "proper_score_improves": deltas["proper_score"]
        <= float(thresholds["max_proper_score_delta"]),
        "calibration_non_inferior": deltas["calibration_error"]
        <= float(thresholds["max_calibration_error_delta"]),
        "legal_decision_regret_improves": deltas["legal_decision_regret"]
        <= float(thresholds["max_legal_regret_delta"]),
        "degradation_bounded": degradation_rate
        <= float(thresholds["max_degradation_rate"]),
        "latency_bounded": _percentile(latency, 0.95)
        <= float(thresholds["max_p95_latency_ms"]),
    }
    result = {
        "schema_version": "1.0",
        "report_id": f"feature-ablation:{family}",
        "family": family,
        "arm_id": preregistration["candidate_families"][family]["arm_id"],
        "preregistration_sha256": preregistration["content_sha256"],
        "evidence_seasons": seasons,
        "baseline": baseline,
        "candidate": candidate,
        "candidate_minus_baseline": deltas,
        "folds": fold_results,
        "uncertainty": _paired_uncertainty(rows),
        "operations": {
            "degradation_rate": degradation_rate,
            "candidate_latency_ms": {
                "mean": mean(latency),
                "p95": _percentile(latency, 0.95),
                "max": max(latency),
            },
        },
        "promotion_checks": checks,
        "promotion_eligible": all(checks.values()),
        "decision": (
            "eligible_for_owner_review"
            if all(checks.values())
            else "remain_shadow_only"
        ),
    }
    result["content_sha256"] = artifact_hash(result)
    return deepcopy(result)
