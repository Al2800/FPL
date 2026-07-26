"""Deterministic reliability shrinkage for noisy player-point projections."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from math import ceil, floor, isfinite
from typing import Any


class ReliabilityShrinkageError(ValueError):
    """Raised when robust-selection inputs or controls are invalid."""


@dataclass(frozen=True)
class RobustSelectionParameters:
    """Locked controls for an additive robust-selection challenger."""

    reliability_minutes: float
    anchor_quantile: float
    shrinkage_strength: float
    risk_aversion: float
    reliability_bucket_edges: tuple[float, ...]
    absolute_error_q80: tuple[float, ...]
    scenario_floor: float = 0.0
    scenario_ceiling: float = 20.0

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> RobustSelectionParameters:
        scenario = config["scenario_calibration"]
        result = cls(
            reliability_minutes=float(config["reliability_minutes"]),
            anchor_quantile=float(config["anchor_quantile"]),
            shrinkage_strength=float(config["shrinkage_strength"]),
            risk_aversion=float(config["risk_aversion"]),
            reliability_bucket_edges=tuple(
                float(value) for value in scenario["reliability_bucket_edges"]
            ),
            absolute_error_q80=tuple(
                float(value) for value in scenario["absolute_error_q80"]
            ),
            scenario_floor=float(scenario.get("floor", 0.0)),
            scenario_ceiling=float(scenario.get("ceiling", 20.0)),
        )
        result.validate()
        return result

    def validate(self) -> None:
        values = (
            self.reliability_minutes,
            self.anchor_quantile,
            self.shrinkage_strength,
            self.risk_aversion,
            self.scenario_floor,
            self.scenario_ceiling,
            *self.reliability_bucket_edges,
            *self.absolute_error_q80,
        )
        if not all(isfinite(value) for value in values):
            raise ReliabilityShrinkageError("Robust-selection controls must be finite")
        if self.reliability_minutes <= 0:
            raise ReliabilityShrinkageError("reliability_minutes must be positive")
        if not 0.0 <= self.anchor_quantile <= 1.0:
            raise ReliabilityShrinkageError("anchor_quantile must be in [0, 1]")
        if self.shrinkage_strength < 0 or self.risk_aversion < 0:
            raise ReliabilityShrinkageError("shrinkage and risk controls cannot be negative")
        if self.scenario_floor < 0 or self.scenario_ceiling <= self.scenario_floor:
            raise ReliabilityShrinkageError("scenario bounds are invalid")
        edges = self.reliability_bucket_edges
        if len(edges) < 2 or edges[0] != 0.0 or edges[-1] != 1.0:
            raise ReliabilityShrinkageError("reliability edges must span exactly [0, 1]")
        if any(left >= right for left, right in zip(edges, edges[1:])):
            raise ReliabilityShrinkageError("reliability edges must increase")
        if len(self.absolute_error_q80) != len(edges) - 1:
            raise ReliabilityShrinkageError("one scenario width is required per bucket")
        if any(value < 0 for value in self.absolute_error_q80):
            raise ReliabilityShrinkageError("scenario widths cannot be negative")


def deterministic_quantile(values: Iterable[float], quantile: float) -> float:
    """Return the linearly interpolated quantile with an explicit stable algorithm."""
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ReliabilityShrinkageError("cannot calculate an anchor from no players")
    if not 0.0 <= quantile <= 1.0:
        raise ReliabilityShrinkageError("quantile must be in [0, 1]")
    index = (len(ordered) - 1) * quantile
    lower = floor(index)
    upper = ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def reliability_from_minutes(sample_minutes: float | int | None, scale: float) -> float:
    """Map prior sample minutes to the same bounded empirical-Bayes reliability."""
    minutes = 0.0 if sample_minutes is None else max(0.0, float(sample_minutes))
    return minutes / (minutes + float(scale))


def _bucket_width(reliability: float, parameters: RobustSelectionParameters) -> float:
    edges = parameters.reliability_bucket_edges
    for index, upper in enumerate(edges[1:]):
        if reliability <= upper or index == len(edges) - 2:
            return parameters.absolute_error_q80[index]
    raise AssertionError("validated reliability buckets must cover [0, 1]")


def shrink_player_projections(
    players: Sequence[Mapping[str, Any]],
    *,
    reliability_by_player: Mapping[str, float],
    parameters: RobustSelectionParameters,
) -> list[dict[str, Any]]:
    """Add bounded scenarios and replace EP with a transparent robust score.

    The anchor is computed within position. Only the portion of a projection above
    that position anchor is shrunk, so ordinary and low projections are not
    mechanically inflated. Inputs are never mutated.
    """
    parameters.validate()
    if not players:
        raise ReliabilityShrinkageError("players cannot be empty")
    anchors: dict[str, float] = {}
    positions = sorted({str(player["position"]) for player in players})
    for position in positions:
        anchors[position] = deterministic_quantile(
            (
                float(player["expected_points"])
                for player in players
                if str(player["position"]) == position
            ),
            parameters.anchor_quantile,
        )

    adjusted: list[dict[str, Any]] = []
    for source in players:
        row = deepcopy(dict(source))
        player_id = str(row["player_id"])
        if player_id not in reliability_by_player:
            raise ReliabilityShrinkageError(
                f"missing reliability for player {player_id}"
            )
        raw = float(row["expected_points"])
        reliability = min(1.0, max(0.0, float(reliability_by_player[player_id])))
        anchor = anchors[str(row["position"])]
        excess = max(0.0, raw - anchor)
        central = raw - parameters.shrinkage_strength * (1.0 - reliability) * excess
        central = min(parameters.scenario_ceiling, max(parameters.scenario_floor, central))
        uncertainty = _bucket_width(reliability, parameters)
        lower = max(parameters.scenario_floor, central - uncertainty)
        upper = min(parameters.scenario_ceiling, central + uncertainty)
        robust = max(
            parameters.scenario_floor,
            central - parameters.risk_aversion * uncertainty,
        )
        row["raw_expected_points"] = round(raw, 6)
        row["expected_points"] = round(robust, 6)
        row["robust_selection"] = {
            "anchor": round(anchor, 6),
            "reliability": round(reliability, 6),
            "central": round(central, 6),
            "uncertainty_q80": round(uncertainty, 6),
            "lower": round(lower, 6),
            "upper": round(upper, 6),
            "robust": round(robust, 6),
        }
        adjusted.append(row)
    return adjusted
