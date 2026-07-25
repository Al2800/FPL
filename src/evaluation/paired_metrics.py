"""Paired and cluster-aware decision-quality summaries."""

from __future__ import annotations

from collections import defaultdict
import math
from statistics import NormalDist, mean, median, stdev
from typing import Any, Iterable, Mapping


def _finite(value: Any, field: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def paired_summary(
    observations: Iterable[Mapping[str, Any]],
    *,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Summarise paired values, using cluster means as inference units."""
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one")
    rows = list(observations)
    if not rows:
        raise ValueError("at least one paired observation is required")
    seen: set[str] = set()
    differences: list[float] = []
    clusters: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        episode_id = str(row.get("episode_id", ""))
        if not episode_id or episode_id in seen:
            raise ValueError("episode_id must be present and unique")
        seen.add(episode_id)
        difference = _finite(row["evaluated_value"], "evaluated_value") - _finite(
            row["baseline_value"], "baseline_value"
        )
        differences.append(difference)
        clusters[str(row.get("cluster_id") or episode_id)].append(difference)

    inference_values = [mean(values) for values in clusters.values()]
    n_clusters = len(inference_values)
    sample_sd = stdev(inference_values) if n_clusters >= 2 else None
    standard_error = sample_sd / math.sqrt(n_clusters) if sample_sd is not None else None
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    centre = mean(inference_values)
    confidence_interval = (
        [centre - z * standard_error, centre + z * standard_error]
        if standard_error is not None
        else None
    )
    effect_size = (
        centre / sample_sd
        if sample_sd is not None and sample_sd > 0
        else (0.0 if centre == 0 else None)
    )
    return {
        "n_pairs": len(differences),
        "n_clusters": n_clusters,
        "inference_unit": "cluster_mean",
        "confidence": confidence,
        "total_difference": sum(differences),
        "mean_difference": centre,
        "median_pair_difference": median(differences),
        "sample_standard_deviation": sample_sd,
        "standard_error": standard_error,
        "confidence_interval": confidence_interval,
        "standardised_effect": effect_size,
        "wins": sum(value > 0 for value in differences),
        "ties": sum(value == 0 for value in differences),
        "losses": sum(value < 0 for value in differences),
    }


def resource_summary(observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate optional paired latency and cost without imputing missing data."""
    rows = list(observations)

    def metric(field: str) -> dict[str, float | int | None]:
        values = [_finite(row[field], field) for row in rows if row.get(field) is not None]
        return {
            "n": len(values),
            "total": sum(values) if values else None,
            "mean": mean(values) if values else None,
        }

    return {
        "evaluated_latency_ms": metric("evaluated_latency_ms"),
        "baseline_latency_ms": metric("baseline_latency_ms"),
        "evaluated_cost": metric("evaluated_cost"),
        "baseline_cost": metric("baseline_cost"),
    }
