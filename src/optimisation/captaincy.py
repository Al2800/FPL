"""Captain and vice-captain selection with calibrated fallback and risk."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from src.forecasting.appearance_distribution import distribution_for_player
from src.forecasting.live_faithful import artifact_hash


class CaptaincyError(ValueError):
    """Raised when a captain policy or fixed XI is invalid."""


def choose_captain_pair(
    starting_xi: Sequence[Mapping[str, Any]],
    *,
    config: Mapping[str, Any],
    appearance_calibration: Mapping[str, Any],
) -> dict[str, Any]:
    """Rank every legal ordered captain/vice pair within an unchanged XI."""
    if config.get("content_sha256") != artifact_hash(config):
        raise CaptaincyError("captain policy config hash mismatch")
    players = [deepcopy(dict(row)) for row in starting_xi]
    if len(players) != 11 or len({str(row["player_id"]) for row in players}) != 11:
        raise CaptaincyError("captain policy requires eleven unique starters")
    statistics = config["position_residual_statistics"]
    ceiling_weight = float(config["ceiling_weight"])
    uncertainty_weight = float(config["uncertainty_penalty_weight"])
    candidates: list[dict[str, Any]] = []
    for captain in players:
        captain_id = str(captain["player_id"])
        position = str(captain["position"])
        if position not in statistics:
            raise CaptaincyError(f"no residual statistics for {position}")
        distribution = distribution_for_player(captain, appearance_calibration)
        expected = float(captain["expected_points"])
        ceiling_uplift = float(statistics[position]["positive_residual_q90"])
        uncertainty = float(statistics[position]["absolute_residual_q80"])
        for vice in players:
            vice_id = str(vice["player_id"])
            if vice_id == captain_id:
                continue
            fallback = distribution.zero * float(vice["expected_points"])
            expected_extra = expected + fallback
            policy_score = (
                expected_extra
                + ceiling_weight * ceiling_uplift
                - uncertainty_weight * uncertainty
            )
            candidates.append(
                {
                    "captain_id": captain_id,
                    "vice_captain_id": vice_id,
                    "expected_captain_extra": round(expected_extra, 6),
                    "captain_expected_points": round(expected, 6),
                    "captain_zero_probability": round(distribution.zero, 8),
                    "vice_fallback_value": round(fallback, 6),
                    "ceiling_uplift_q90": round(ceiling_uplift, 6),
                    "uncertainty_q80": round(uncertainty, 6),
                    "policy_score": round(policy_score, 6),
                }
            )
    candidates.sort(
        key=lambda row: (
            -float(row["policy_score"]),
            str(row["captain_id"]),
            str(row["vice_captain_id"]),
        )
    )
    return {
        "policy_version": str(config["policy_version"]),
        "selected": candidates[0],
        "candidates": candidates,
        "fixed_starting_xi_ids": sorted(str(row["player_id"]) for row in players),
    }
