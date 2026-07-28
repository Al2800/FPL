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


_FPL_LINEUP_LIMITS: dict[str, tuple[int, int]] = {
    "GKP": (1, 1),
    "DEF": (3, 5),
    "MID": (2, 5),
    "FWD": (1, 3),
}


def _normalise_decision_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, source in enumerate(rows):
        player_id = str(source.get("player_id", ""))
        if not player_id:
            raise ValueError(f"decision row {index} has no player_id")
        if player_id in seen:
            raise ValueError(f"duplicate decision player_id: {player_id}")
        seen.add(player_id)
        position = str(source.get("position", "")).upper()
        if position == "GK":
            position = "GKP"
        if position not in _FPL_LINEUP_LIMITS:
            raise ValueError(f"unsupported position for {player_id}: {position}")
        try:
            predicted = float(source["predicted"])
            actual = float(source["actual"])
            price = float(source["price"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"decision row for {player_id} has invalid numeric fields"
            ) from exc
        if not all(math.isfinite(value) for value in (predicted, actual, price)):
            raise ValueError(f"decision row for {player_id} must be finite")
        if price < 0:
            raise ValueError(f"decision row for {player_id} has negative price")
        records.append(
            {
                "player_id": player_id,
                "position": position,
                "predicted": predicted,
                "actual": actual,
                "price": price,
            }
        )
    if not records:
        raise ValueError("decision rows must not be empty")
    return sorted(records, key=lambda row: row["player_id"])


def _formation(
    player_ids: Sequence[str],
    by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, int]:
    if len(player_ids) != 11 or len(set(player_ids)) != 11:
        raise ValueError("a legal starting XI must contain 11 unique players")
    missing = sorted(set(player_ids) - set(by_id))
    if missing:
        raise ValueError(
            f"starting XI contains players outside the boundary: {missing}"
        )
    counts = {
        position: sum(
            by_id[player_id]["position"] == position for player_id in player_ids
        )
        for position in _FPL_LINEUP_LIMITS
    }
    for position, (minimum, maximum) in _FPL_LINEUP_LIMITS.items():
        if not minimum <= counts[position] <= maximum:
            raise ValueError(
                f"illegal starting XI formation: {position}={counts[position]}"
            )
    return counts


def _formations() -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    for defenders in range(3, 6):
        for midfielders in range(2, 6):
            for forwards in range(1, 4):
                if defenders + midfielders + forwards == 10:
                    result.append(
                        {
                            "GKP": 1,
                            "DEF": defenders,
                            "MID": midfielders,
                            "FWD": forwards,
                        }
                    )
    return result


def _owned_best_lineup(
    rows: Sequence[Mapping[str, Any]],
    *,
    objective: str,
) -> tuple[list[str], float, int]:
    by_id = {str(row["player_id"]): row for row in rows}
    by_position = {
        position: sorted(
            (row for row in rows if row["position"] == position),
            key=lambda row: (-float(row[objective]), str(row["player_id"])),
        )
        for position in _FPL_LINEUP_LIMITS
    }
    candidates: list[tuple[float, tuple[str, ...]]] = []
    for formation in _formations():
        if any(
            len(by_position[position]) < count
            for position, count in formation.items()
        ):
            continue
        player_ids = tuple(
            sorted(
                str(row["player_id"])
                for position, count in formation.items()
                for row in by_position[position][:count]
            )
        )
        candidates.append(
            (
                sum(float(by_id[player_id][objective]) for player_id in player_ids),
                player_ids,
            )
        )
    if not candidates:
        raise ValueError("decision boundary cannot produce a legal FPL starting XI")
    best_value = max(value for value, _ in candidates)
    tied = sorted(
        player_ids for value, player_ids in candidates if value == best_value
    )
    return list(tied[0]), best_value, len(tied)


def _validated_lineup_candidates(
    legal_lineups: Sequence[Sequence[str]],
    *,
    by_id: Mapping[str, Mapping[str, Any]],
) -> list[tuple[str, ...]]:
    candidates: set[tuple[str, ...]] = set()
    for lineup in legal_lineups:
        player_ids = tuple(sorted(str(value) for value in lineup))
        _formation(player_ids, by_id)
        candidates.add(player_ids)
    if not candidates:
        raise ValueError(
            "market boundary requires at least one legal lineup candidate"
        )
    return sorted(candidates)


def _candidate_best_lineup(
    candidates: Sequence[Sequence[str]],
    *,
    by_id: Mapping[str, Mapping[str, Any]],
    objective: str,
) -> tuple[list[str], float, int]:
    scored = [
        (
            sum(float(by_id[player_id][objective]) for player_id in lineup),
            tuple(lineup),
        )
        for lineup in candidates
    ]
    best_value = max(value for value, _ in scored)
    tied = sorted(lineup for value, lineup in scored if value == best_value)
    return list(tied[0]), best_value, len(tied)


def _average_ranks(values: Sequence[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: (-item[1], item[0]))
    result = [0.0] * len(values)
    offset = 0
    while offset < len(ordered):
        end = offset + 1
        while end < len(ordered) and ordered[end][1] == ordered[offset][1]:
            end += 1
        average_rank = ((offset + 1) + end) / 2.0
        for index, _ in ordered[offset:end]:
            result[index] = average_rank
        offset = end
    return result


def _rank_metric(
    rows: Sequence[Mapping[str, Any]],
    *,
    top_price_band_min: float,
) -> dict[str, Any]:
    cohort = [row for row in rows if float(row["price"]) >= top_price_band_min]
    if not cohort:
        return {
            "status": "empty",
            "n": 0,
            "minimum_price": top_price_band_min,
            "spearman_correlation": None,
        }
    if len(cohort) < 2:
        return {
            "status": "insufficient",
            "n": len(cohort),
            "minimum_price": top_price_band_min,
            "spearman_correlation": None,
        }
    predicted_ranks = _average_ranks(
        [float(row["predicted"]) for row in cohort]
    )
    actual_ranks = _average_ranks([float(row["actual"]) for row in cohort])
    correlation = _correlation(predicted_ranks, actual_ranks)
    return {
        "status": "measured" if correlation is not None else "degenerate_tie",
        "n": len(cohort),
        "minimum_price": top_price_band_min,
        "spearman_correlation": correlation,
    }


def decision_aligned_summary(
    rows: Iterable[Mapping[str, Any]],
    *,
    boundary_type: str,
    top_price_band_min: float,
    legal_lineups: Sequence[Sequence[str]] | None = None,
    selected_xi_ids: Sequence[str] | None = None,
    captain_id: str | None = None,
) -> dict[str, Any]:
    """Evaluate legal XI, captain and premium ranking decisions post-outcome."""

    if boundary_type not in {"owned_squad", "market"}:
        raise ValueError("boundary_type must be owned_squad or market")
    if (
        isinstance(top_price_band_min, bool)
        or not isinstance(top_price_band_min, (int, float))
        or not math.isfinite(float(top_price_band_min))
    ):
        raise ValueError("top_price_band_min must be finite")
    records = _normalise_decision_rows(rows)
    by_id = {str(row["player_id"]): row for row in records}
    if boundary_type == "market" and legal_lineups is None:
        raise ValueError(
            "market boundary requires optimiser-supplied legal lineup candidates"
        )
    candidates = (
        _validated_lineup_candidates(legal_lineups or [], by_id=by_id)
        if legal_lineups is not None
        else None
    )
    if selected_xi_ids is None:
        if candidates is None:
            selected, selected_expected, selected_ties = _owned_best_lineup(
                records, objective="predicted"
            )
        else:
            selected, selected_expected, selected_ties = _candidate_best_lineup(
                candidates, by_id=by_id, objective="predicted"
            )
        selected_source = "inferred_max_predicted_legal_xi"
    else:
        selected = sorted(str(value) for value in selected_xi_ids)
        _formation(selected, by_id)
        if candidates is not None and tuple(selected) not in candidates:
            raise ValueError(
                "selected market XI is absent from supplied legal candidates"
            )
        selected_expected = sum(
            float(by_id[player_id]["predicted"]) for player_id in selected
        )
        selected_ties = None
        selected_source = "explicit_frozen_decision"

    if candidates is None:
        oracle, oracle_realised, oracle_ties = _owned_best_lineup(
            records, objective="actual"
        )
    else:
        oracle, oracle_realised, oracle_ties = _candidate_best_lineup(
            candidates, by_id=by_id, objective="actual"
        )
    selected_realised = sum(
        float(by_id[player_id]["actual"]) for player_id in selected
    )
    if captain_id is None:
        captain = min(
            selected,
            key=lambda player_id: (-float(by_id[player_id]["predicted"]), player_id),
        )
        captain_source = "inferred_max_predicted_selected_xi"
    else:
        captain = str(captain_id)
        if captain not in selected:
            raise ValueError("captain must belong to the selected XI")
        captain_source = "explicit_frozen_decision"
    oracle_captain = min(
        selected,
        key=lambda player_id: (-float(by_id[player_id]["actual"]), player_id),
    )
    captain_actual = float(by_id[captain]["actual"])
    oracle_captain_actual = float(by_id[oracle_captain]["actual"])
    point_metrics = calibration_summary(
        [float(row["predicted"]) for row in records],
        [float(row["actual"]) for row in records],
    )
    return {
        "evaluation_only": True,
        "hindsight_fields_forbidden_as_proposal_inputs": True,
        "boundary": {
            "type": boundary_type,
            "player_count": len(records),
            "legal_candidate_count": (
                len(candidates) if candidates is not None else None
            ),
        },
        "sample_sizes": {
            "boundary_player_gameweeks": len(records),
            "selected_xi": len(selected),
            "top_price_band": sum(
                float(row["price"]) >= float(top_price_band_min)
                for row in records
            ),
        },
        "point_error": {
            "n": point_metrics["n"],
            "mean_absolute_error": point_metrics["mean_absolute_error"],
            "root_mean_square_error": point_metrics["root_mean_square_error"],
            "bias_actual_minus_predicted": point_metrics[
                "bias_actual_minus_predicted"
            ],
        },
        "selected_xi": {
            "source": selected_source,
            "player_ids": selected,
            "formation": _formation(selected, by_id),
            "expected_points": selected_expected,
            "realised_points": selected_realised,
            "prediction_error_actual_minus_predicted": (
                selected_realised - selected_expected
            ),
            "predicted_optimal_candidate_ties": selected_ties,
        },
        "xi_regret": {
            "realised_points": oracle_realised - selected_realised,
            "oracle_player_ids": oracle,
            "oracle_realised_points": oracle_realised,
            "oracle_optimal_candidate_ties": oracle_ties,
        },
        "captain": {
            "source": captain_source,
            "player_id": captain,
            "realised_points": captain_actual,
            "oracle_player_id_within_selected_xi": oracle_captain,
            "oracle_realised_points": oracle_captain_actual,
            "regret_points": oracle_captain_actual - captain_actual,
        },
        "top_price_band_rank": _rank_metric(
            records,
            top_price_band_min=float(top_price_band_min),
        ),
    }


def decision_aligned_comparison_table(
    model_rows: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    boundary_type: str,
    top_price_band_min: float,
    legal_lineups: Sequence[Sequence[str]] | None = None,
    selected_xi_ids_by_model: Mapping[str, Sequence[str]] | None = None,
    captain_id_by_model: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return one stable table comparing decision metrics across models."""

    if not model_rows:
        raise ValueError("model_rows must not be empty")
    selected_by_model = selected_xi_ids_by_model or {}
    captains_by_model = captain_id_by_model or {}
    normalised = {
        str(model): _normalise_decision_rows(rows)
        for model, rows in model_rows.items()
    }
    reference_model = sorted(normalised)[0]
    reference = {
        row["player_id"]: (row["position"], row["actual"], row["price"])
        for row in normalised[reference_model]
    }
    for model, rows in normalised.items():
        candidate = {
            row["player_id"]: (row["position"], row["actual"], row["price"])
            for row in rows
        }
        if candidate != reference:
            raise ValueError(
                f"model {model} does not share the same decision boundary"
            )
    table = []
    for model in sorted(normalised):
        summary = decision_aligned_summary(
            normalised[model],
            boundary_type=boundary_type,
            top_price_band_min=top_price_band_min,
            legal_lineups=legal_lineups,
            selected_xi_ids=selected_by_model.get(model),
            captain_id=captains_by_model.get(model),
        )
        table.append({"model": model, **summary})
    return {
        "schema_version": "1.0",
        "evaluation_only": True,
        "hindsight_fields_forbidden_as_proposal_inputs": True,
        "metric_direction": {
            "mean_absolute_error": "lower_is_better",
            "root_mean_square_error": "lower_is_better",
            "xi_regret.realised_points": "lower_is_better",
            "captain.regret_points": "lower_is_better",
            "top_price_band_rank.spearman_correlation": "higher_is_better",
        },
        "comparison_table": table,
    }
