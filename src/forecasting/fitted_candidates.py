"""Preregistered fitted forecast-model candidates (ticket 17).

Transparent numpy-only fits. Fail closed to the declared heuristic baseline.
Never fit on forbidden seasons (2025-26 / 2026-27).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.forecasting.data import add_lagged_features, load_merged_gw
from src.forecasting.evaluate import (
    _brier,
    _mae,
    _rmse,
    binary_log_loss,
    expected_calibration_error,
)
from src.forecasting.live_faithful import artifact_hash
from src.forecasting.minutes import (
    expected_minutes_from_start_prob,
    rolling_minutes_start_prob,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PREREG = ROOT / "control" / "models" / "fitted-forecast-candidates-v1.json"


class FittedCandidateError(ValueError):
    """Raised when a fitted-candidate evaluation cannot run safely."""


def load_preregistration(path: Path | None = None) -> dict[str, Any]:
    payload = json_load(path or DEFAULT_PREREG)
    if payload.get("schema_version") != "fitted-forecast-candidates-v1":
        raise FittedCandidateError("unsupported fitted-candidate schema")
    if "2025-26" not in payload.get("forbidden_fit_seasons", []):
        raise FittedCandidateError("preregistration must forbid fitting on 2025-26")
    return payload


def json_load(path: Path) -> dict[str, Any]:
    import json

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FittedCandidateError(f"expected JSON object at {path}")
    return value


def _design_matrix(frame: pd.DataFrame, feature_names: Sequence[str]) -> np.ndarray:
    columns: list[np.ndarray] = []
    for name in feature_names:
        if name == "intercept":
            columns.append(np.ones(len(frame), dtype=float))
        elif name == "started_lag1":
            columns.append(frame["started_lag1"].fillna(0.5).astype(float).to_numpy())
        elif name == "minutes_roll3_over_90":
            roll = frame.get("minutes_roll3")
            if roll is None:
                raise FittedCandidateError("minutes_roll3 required")
            columns.append((roll.fillna(45.0) / 90.0).clip(0.05, 0.95).to_numpy())
        else:
            raise FittedCandidateError(f"unsupported feature: {name}")
    return np.column_stack(columns)


def fit_ridge(x: np.ndarray, y: np.ndarray, *, l2: float) -> np.ndarray:
    if x.ndim != 2 or y.ndim != 1 or len(x) != len(y):
        raise FittedCandidateError("ridge inputs have incompatible shapes")
    if len(y) < x.shape[1]:
        raise FittedCandidateError("insufficient rows to fit ridge")
    eye = np.eye(x.shape[1])
    eye[0, 0] = 0.0  # do not shrink intercept
    gram = x.T @ x + float(l2) * eye
    return np.linalg.solve(gram, x.T @ y)


def fit_logistic_l2(
    x: np.ndarray,
    y: np.ndarray,
    *,
    l2: float,
    max_iter: int = 40,
) -> np.ndarray:
    """Newton / IRLS logistic regression with L2 penalty (intercept unpenalised)."""

    if x.ndim != 2 or y.ndim != 1 or len(x) != len(y):
        raise FittedCandidateError("logistic inputs have incompatible shapes")
    if not set(np.unique(y)).issubset({0.0, 1.0}):
        raise FittedCandidateError("logistic target must be binary 0/1")
    weights = np.zeros(x.shape[1], dtype=float)
    penalty = np.eye(x.shape[1])
    penalty[0, 0] = 0.0
    for _ in range(max_iter):
        logits = x @ weights
        probs = 1.0 / (1.0 + np.exp(-np.clip(logits, -30, 30)))
        gradient = x.T @ (probs - y) + float(l2) * (penalty @ weights)
        s = probs * (1.0 - probs)
        hessian = (x.T * s) @ x + float(l2) * penalty
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError as exc:
            raise FittedCandidateError("logistic hessian is singular") from exc
        weights = weights - step
        if float(np.max(np.abs(step))) < 1e-8:
            break
    return weights


def predict_logistic(x: np.ndarray, weights: np.ndarray) -> np.ndarray:
    logits = x @ weights
    return 1.0 / (1.0 + np.exp(-np.clip(logits, -30, 30)))


def _minutes_frame(season: str) -> pd.DataFrame:
    frame = add_lagged_features(load_merged_gw(season))
    if "started" not in frame.columns and "minutes" in frame.columns:
        frame["started"] = (frame["minutes"].fillna(0) >= 60).astype(float)
    frame["start_prob_baseline"] = rolling_minutes_start_prob(frame)
    frame["expected_minutes_baseline"] = expected_minutes_from_start_prob(
        frame["start_prob_baseline"]
    )
    return frame


def _metrics(
    *,
    started: pd.Series,
    minutes: pd.Series,
    start_prob: pd.Series,
    expected_minutes: pd.Series,
) -> dict[str, float]:
    return {
        "brier": _brier(started, start_prob),
        "log_loss": binary_log_loss(started, start_prob),
        "ece": expected_calibration_error(started, start_prob),
        "minutes_mae": _mae(minutes, expected_minutes),
        "minutes_rmse": _rmse(minutes, expected_minutes),
        "n": float(started.notna().sum()),
    }


def evaluate_minutes_family(
    prereg: Mapping[str, Any],
    *,
    family: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fit the minutes logistic candidate on fit seasons; score locked validation."""

    spec = dict(family or next(row for row in prereg["families"] if row["family_id"] == "expected_minutes"))
    fit_seasons = list(prereg["fit_seasons"])
    for season in fit_seasons:
        if season in prereg["forbidden_fit_seasons"]:
            raise FittedCandidateError(f"refusing to fit on forbidden season {season}")

    train_parts = [_minutes_frame(season) for season in fit_seasons]
    train = pd.concat(train_parts, ignore_index=True)
    train = train[train["started"].notna()].copy()
    train["started"] = train["started"].astype(float)
    x_train = _design_matrix(train, spec["features"])
    y_train = train["started"].to_numpy(dtype=float)
    weights = fit_logistic_l2(x_train, y_train, l2=float(spec["l2"]))

    val_season = str(prereg["locked_validation_season"])
    if val_season in prereg["forbidden_fit_seasons"]:
        raise FittedCandidateError("locked validation season is forbidden for fitting")
    val = _minutes_frame(val_season)
    val = val[val["started"].notna()].copy()
    val["started"] = val["started"].astype(float)
    x_val = _design_matrix(val, spec["features"])
    candidate_prob = pd.Series(predict_logistic(x_val, weights), index=val.index)
    candidate_minutes = expected_minutes_from_start_prob(candidate_prob)
    baseline_metrics = _metrics(
        started=val["started"],
        minutes=val["minutes"],
        start_prob=val["start_prob_baseline"],
        expected_minutes=val["expected_minutes_baseline"],
    )
    candidate_metrics = _metrics(
        started=val["started"],
        minutes=val["minutes"],
        start_prob=candidate_prob,
        expected_minutes=candidate_minutes,
    )

    improve_brier = candidate_metrics["brier"] < baseline_metrics["brier"]
    not_worsen_mae = candidate_metrics["minutes_mae"] <= baseline_metrics["minutes_mae"] + 1e-9
    promotion_eligible = bool(improve_brier and not_worsen_mae)

    model_artifact = {
        "schema_version": "fitted-minutes-candidate-v1",
        "candidate_id": spec["candidate_id"],
        "family_id": spec["family_id"],
        "model": spec["model"],
        "l2": float(spec["l2"]),
        "features": list(spec["features"]),
        "weights": [float(value) for value in weights.tolist()],
        "fit_seasons": fit_seasons,
        "training_cutoff": f"end_of_{fit_seasons[-1]}",
        "locked_validation_season": val_season,
        "source_ids": ["vaastav-merged-gw"],
        "transformation_version": "fitted-candidates-minutes-v1",
        "fallback_baseline": prereg["fallback_baseline"],
        "promotion_eligible": promotion_eligible,
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "paired_delta": {
            "brier": candidate_metrics["brier"] - baseline_metrics["brier"],
            "minutes_mae": (
                candidate_metrics["minutes_mae"] - baseline_metrics["minutes_mae"]
            ),
        },
        "reason_not_promoted": (
            None
            if promotion_eligible
            else "failed_preregistered_minutes_gates_on_locked_validation"
        ),
    }
    model_artifact["content_sha256"] = artifact_hash(model_artifact)
    return model_artifact


def evaluate_preregistered_families(prereg: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run implemented families; stub remaining families as baseline-retained."""

    loaded = dict(prereg or load_preregistration())
    minutes = evaluate_minutes_family(loaded)
    families = {
        "expected_minutes": minutes,
        "team_goals": {
            "candidate_id": "ridge_elo_home_expected_goals_v1",
            "promotion_eligible": False,
            "status": "baseline_retained_pending_fixture_join",
            "fallback_baseline": loaded["fallback_baseline"],
            "notes": (
                "Team-goal ridge candidate is preregistered; evaluation joins Elo "
                "expected goals in a follow-on pass. Baseline walk-forward Elo retained."
            ),
        },
        "player_events": {
            "candidate_id": "ridge_goal_rate_minutes_fixture_v1",
            "promotion_eligible": False,
            "status": "baseline_retained_pending_rate_frame_join",
            "fallback_baseline": loaded["fallback_baseline"],
            "notes": (
                "Player-event logistic candidate is preregistered; evaluation joins "
                "per-90 priors in a follow-on pass. Baseline per-90 retained."
            ),
        },
    }
    report = {
        "schema_version": "fitted-forecast-evaluation-v1",
        "preregistration_path": str(DEFAULT_PREREG.relative_to(ROOT)).replace("\\", "/"),
        "forbidden_fit_seasons": list(loaded["forbidden_fit_seasons"]),
        "fit_seasons": list(loaded["fit_seasons"]),
        "locked_validation_season": loaded["locked_validation_season"],
        "families": families,
        "any_promoted": any(
            bool(row.get("promotion_eligible")) for row in families.values()
        ),
        "notes": (
            "Ticket 17: minutes family fully evaluated on locked 2024/25. "
            "Other families remain baseline-retained until their joins ship. "
            "Monte Carlo (ticket 05) continues to consume baseline marginals."
        ),
    }
    report["content_sha256"] = artifact_hash(report)
    return report
