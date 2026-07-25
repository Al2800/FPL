"""Pre-result detectable-effect calculations for paired evaluations."""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Any


def minimum_detectable_paired_effect(
    *,
    n_clusters: int,
    sample_standard_deviation: float | None,
    alpha: float = 0.05,
    target_power: float = 0.8,
) -> dict[str, Any]:
    """Return the normal-approximation two-sided minimum detectable effect."""
    if n_clusters < 1:
        raise ValueError("n_clusters must be positive")
    if not 0 < alpha < 1 or not 0 < target_power < 1:
        raise ValueError("alpha and target_power must be between zero and one")
    if sample_standard_deviation is None or n_clusters < 2:
        absolute = None
    else:
        standard_deviation = float(sample_standard_deviation)
        if not math.isfinite(standard_deviation) or standard_deviation < 0:
            raise ValueError("sample_standard_deviation must be finite and non-negative")
        z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
        z_power = NormalDist().inv_cdf(target_power)
        absolute = (z_alpha + z_power) * standard_deviation / math.sqrt(n_clusters)
    return {
        "method": "normal_approximation_paired_cluster_means",
        "n_clusters": n_clusters,
        "alpha": alpha,
        "target_power": target_power,
        "absolute_effect": absolute,
        "note": (
            "Planning diagnostic, not a post-result significance claim; "
            "small samples may require wider simulation-based intervals."
        ),
    }
