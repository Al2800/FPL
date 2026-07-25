"""Calibration summaries for point forecasts and decision cohorts."""

from __future__ import annotations

import math
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence


def _correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) < 2:
        return None
    left_mean = mean(left)
    right_mean = mean(right)
    numerator = sum(
        (a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True)
    )
    left_scale = math.sqrt(sum((value - left_mean) ** 2 for value in left))
    right_scale = math.sqrt(sum((value - right_mean) ** 2 for value in right))
    if left_scale == 0 or right_scale == 0:
        return None
    return numerator / (left_scale * right_scale)


def calibration_summary(
    predictions: Sequence[float],
    actuals: Sequence[float],
    *,
    bins: int = 10,
) -> dict[str, Any]:
    """Return point-error metrics and equal-width reliability bins."""
    if len(predictions) != len(actuals) or not predictions:
        raise ValueError("predictions and actuals must have the same non-zero length")
    if bins < 1:
        raise ValueError("bins must be positive")
    predicted = [float(value) for value in predictions]
    observed = [float(value) for value in actuals]
    if not all(math.isfinite(value) for value in predicted + observed):
        raise ValueError("calibration values must be finite")
    errors = [actual - forecast for forecast, actual in zip(predicted, observed, strict=True)]
    minimum = min(predicted)
    maximum = max(predicted)
    width = (maximum - minimum) / bins if maximum > minimum else 1.0
    grouped: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
    for forecast, actual in zip(predicted, observed, strict=True):
        index = min(int((forecast - minimum) / width), bins - 1)
        grouped[index].append((forecast, actual))
    reliability = [
        {
            "bin": index,
            "n": len(values),
            "mean_predicted": mean(value[0] for value in values),
            "mean_actual": mean(value[1] for value in values),
        }
        for index, values in enumerate(grouped)
        if values
    ]
    return {
        "n": len(predicted),
        "bias_actual_minus_predicted": mean(errors),
        "mean_absolute_error": mean(abs(value) for value in errors),
        "root_mean_square_error": math.sqrt(mean(value * value for value in errors)),
        "correlation": _correlation(predicted, observed),
        "reliability": reliability,
    }


def calibration_by_cohort(
    rows: Iterable[Mapping[str, Any]],
    *,
    cohorts: Sequence[str] = ("all", "owned", "selected_xi"),
    bins: int = 10,
) -> dict[str, dict[str, Any]]:
    """Report the same metrics for declared selection cohorts."""
    records = list(rows)
    result: dict[str, dict[str, Any]] = {}
    for cohort in cohorts:
        selected = [
            row for row in records if cohort == "all" or cohort in set(row.get("cohorts") or [])
        ]
        if selected:
            result[cohort] = calibration_summary(
                [float(row["predicted"]) for row in selected],
                [float(row["actual"]) for row in selected],
                bins=bins,
            )
    return result
