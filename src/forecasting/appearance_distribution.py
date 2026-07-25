"""Calibrated planning-time appearance distributions.

The optimiser needs only three mutually exclusive states to value FPL
contingencies: no appearance, an appearance below 60 minutes, or at least
60 minutes.  This module deliberately does not score those states; official
realised scoring remains in :mod:`src.evaluation.outcome_scorer`.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


class AppearanceDistributionError(ValueError):
    """Raised when an appearance distribution or calibration is invalid."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def calibration_hash(value: Mapping[str, Any]) -> str:
    """Return the content hash, excluding an existing hash field."""

    payload = {key: item for key, item in value.items() if key != "content_sha256"}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class AppearanceDistribution:
    """Mutually exclusive Gameweek appearance probabilities."""

    zero: float
    under_60: float
    sixty_plus: float
    source: str = "calibrated"

    def __post_init__(self) -> None:
        values = (self.zero, self.under_60, self.sixty_plus)
        if any(value < 0.0 or value > 1.0 for value in values):
            raise AppearanceDistributionError(
                "Appearance probabilities must be between zero and one"
            )
        if abs(sum(values) - 1.0) > 1e-8:
            raise AppearanceDistributionError(
                "Appearance probabilities must sum to one"
            )

    @property
    def appears(self) -> float:
        return self.under_60 + self.sixty_plus

    def as_dict(self) -> dict[str, Any]:
        return {
            "zero": round(self.zero, 8),
            "under_60": round(self.under_60, 8),
            "60_plus": round(self.sixty_plus, 8),
            "source": self.source,
        }

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, Any], *, source: str | None = None
    ) -> "AppearanceDistribution":
        return cls(
            zero=float(value["zero"]),
            under_60=float(value["under_60"]),
            sixty_plus=float(value["60_plus"]),
            source=source or str(value.get("source", "explicit")),
        )

    def across_fixtures(self, fixture_count: int) -> "AppearanceDistribution":
        """Aggregate independent per-fixture states into one Gameweek state.

        ``60_plus`` means at least one 60-plus appearance; ``under_60`` means
        at least one appearance but no 60-plus appearance.
        """

        if fixture_count < 1:
            raise AppearanceDistributionError("fixture_count must be positive")
        if fixture_count == 1:
            return self
        zero = self.zero**fixture_count
        no_sixty = (self.zero + self.under_60) ** fixture_count
        return AppearanceDistribution(
            zero=zero,
            under_60=no_sixty - zero,
            sixty_plus=1.0 - no_sixty,
            source=f"{self.source}:fixtures={fixture_count}",
        )


def _validate_calibration(calibration: Mapping[str, Any]) -> None:
    if calibration.get("content_sha256") != calibration_hash(calibration):
        raise AppearanceDistributionError("Appearance calibration hash mismatch")
    bins = list(calibration.get("bins", []))
    if not bins:
        raise AppearanceDistributionError("Appearance calibration has no bins")
    previous_upper = 0.0
    for index, item in enumerate(bins):
        lower = float(item["lower"])
        upper = float(item["upper"])
        if lower != previous_upper or upper <= lower:
            raise AppearanceDistributionError(
                f"Appearance calibration bin {index} is not contiguous"
            )
        AppearanceDistribution.from_mapping(item["probabilities"])
        previous_upper = upper
    if abs(previous_upper - 1.0) > 1e-9:
        raise AppearanceDistributionError(
            "Appearance calibration bins must cover zero through one"
        )


def distribution_for_probability(
    start_probability: float,
    calibration: Mapping[str, Any],
    *,
    fixture_count: int = 1,
) -> AppearanceDistribution:
    """Map a deadline-safe start probability to a calibrated distribution."""

    _validate_calibration(calibration)
    probability = float(start_probability)
    if probability < 0.0 or probability > 1.0:
        raise AppearanceDistributionError(
            "start_probability must be between zero and one"
        )
    bins = list(calibration["bins"])
    selected = bins[-1]
    for item in bins:
        if probability < float(item["upper"]) or (
            probability == 1.0 and float(item["upper"]) == 1.0
        ):
            selected = item
            break
    result = AppearanceDistribution.from_mapping(
        selected["probabilities"],
        source=(
            f"{calibration['model_version']}:"
            f"{float(selected['lower']):.2f}-{float(selected['upper']):.2f}"
        ),
    )
    return result.across_fixtures(fixture_count)


def distribution_for_player(
    player: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> AppearanceDistribution:
    """Resolve an explicit distribution or calibrate the player's start chance."""

    explicit = player.get("appearance_distribution")
    if explicit is not None:
        return AppearanceDistribution.from_mapping(
            explicit, source=str(explicit.get("source", "explicit"))
        )
    if player.get("start_probability") is None:
        raise AppearanceDistributionError(
            f"Player {player.get('player_id')} has no start_probability"
        )
    return distribution_for_probability(
        float(player["start_probability"]),
        calibration,
        fixture_count=max(1, int(player.get("fixture_count", 1))),
    )


def fit_binned_calibration(
    rows: Iterable[Mapping[str, Any]],
    *,
    model_version: str,
    training_seasons: list[str],
    bin_edges: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
    prior: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> dict[str, Any]:
    """Fit a smoothed categorical calibration from deadline-safe predictions."""

    if len(bin_edges) < 2 or bin_edges[0] != 0.0 or bin_edges[-1] != 1.0:
        raise AppearanceDistributionError("bin_edges must span zero through one")
    if any(right <= left for left, right in zip(bin_edges, bin_edges[1:])):
        raise AppearanceDistributionError("bin_edges must be strictly increasing")
    counts = [[float(value) for value in prior] for _ in range(len(bin_edges) - 1)]
    observations = [0 for _ in counts]
    for row in rows:
        probability = float(row["start_probability"])
        minutes = int(row["minutes"])
        if probability < 0.0 or probability > 1.0 or minutes < 0:
            raise AppearanceDistributionError("Invalid calibration observation")
        index = len(counts) - 1
        for candidate, upper in enumerate(bin_edges[1:]):
            if probability < upper or (probability == 1.0 and upper == 1.0):
                index = candidate
                break
        category = 0 if minutes == 0 else 1 if minutes < 60 else 2
        counts[index][category] += 1.0
        observations[index] += 1

    bins: list[dict[str, Any]] = []
    for index, category_counts in enumerate(counts):
        total = sum(category_counts)
        probabilities = {
            "zero": category_counts[0] / total,
            "under_60": category_counts[1] / total,
            "60_plus": category_counts[2] / total,
        }
        bins.append(
            {
                "lower": bin_edges[index],
                "upper": bin_edges[index + 1],
                "n_observations": observations[index],
                "probabilities": {
                    key: round(value, 8) for key, value in probabilities.items()
                },
            }
        )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "model_version": model_version,
        "status": "challenger",
        "training_seasons": list(training_seasons),
        "states": ["zero", "under_60", "60_plus"],
        "smoothing_prior": {
            "zero": prior[0],
            "under_60": prior[1],
            "60_plus": prior[2],
        },
        "bins": bins,
    }
    result["content_sha256"] = calibration_hash(result)
    return result
