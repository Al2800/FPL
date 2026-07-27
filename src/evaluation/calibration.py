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


def binary_calibration_summary(
    probabilities: Sequence[float],
    outcomes: Sequence[int | bool],
    *,
    bins: int = 10,
) -> dict[str, Any]:
    """Return proper scores and fixed-width reliability for binary forecasts."""

    if len(probabilities) != len(outcomes) or not probabilities:
        raise ValueError(
            "probabilities and outcomes must have the same non-zero length"
        )
    if not isinstance(bins, int) or isinstance(bins, bool) or bins < 1:
        raise ValueError("bins must be a positive integer")
    predicted = [float(value) for value in probabilities]
    observed = [int(value) for value in outcomes]
    if not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in predicted):
        raise ValueError("binary probabilities must be finite values from 0 to 1")
    if any(value not in (0, 1) for value in observed):
        raise ValueError("binary outcomes must contain only 0 or 1")
    grouped: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for forecast, actual in zip(predicted, observed, strict=True):
        grouped[min(int(forecast * bins), bins - 1)].append((forecast, actual))
    reliability = []
    expected_calibration_error = 0.0
    for index, values in enumerate(grouped):
        if not values:
            continue
        mean_predicted = mean(value[0] for value in values)
        mean_actual = mean(value[1] for value in values)
        gap = abs(mean_predicted - mean_actual)
        expected_calibration_error += len(values) / len(predicted) * gap
        reliability.append(
            {
                "bin": index,
                "lower": index / bins,
                "upper": (index + 1) / bins,
                "n": len(values),
                "mean_predicted": mean_predicted,
                "mean_actual": mean_actual,
                "absolute_gap": gap,
            }
        )
    epsilon = 1e-15
    clipped = [min(max(value, epsilon), 1.0 - epsilon) for value in predicted]
    return {
        "n": len(predicted),
        "brier_score": mean(
            (forecast - actual) ** 2
            for forecast, actual in zip(predicted, observed, strict=True)
        ),
        "log_loss": -mean(
            actual * math.log(forecast)
            + (1 - actual) * math.log(1.0 - forecast)
            for forecast, actual in zip(clipped, observed, strict=True)
        ),
        "expected_calibration_error": expected_calibration_error,
        "reliability": reliability,
    }


def minutes_calibration_summary(
    predictions: Sequence[float],
    actuals: Sequence[float],
    *,
    bins: int = 10,
) -> dict[str, Any]:
    """Return non-negative expected-minutes error and reliability metrics."""

    predicted = [float(value) for value in predictions]
    observed = [float(value) for value in actuals]
    if any(value < 0 for value in predicted + observed):
        raise ValueError("expected and actual minutes must be non-negative")
    result = calibration_summary(predicted, observed, bins=bins)
    result["mean_squared_error"] = mean(
        (forecast - actual) ** 2
        for forecast, actual in zip(predicted, observed, strict=True)
    )
    result["mean_absolute_calibration_gap"] = sum(
        row["n"] * abs(row["mean_predicted"] - row["mean_actual"])
        for row in result["reliability"]
    ) / result["n"]
    return result

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
