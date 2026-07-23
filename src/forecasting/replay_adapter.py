"""Adapt historical feature state and one policy state to the deterministic solver."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from src.forecasting.live_faithful import artifact_hash
from src.optimisation.types import SolverInput
from src.orchestration.historical_feature_state import feature_state_hash


class ReplayAdapterError(ValueError):
    """Raised when feature and policy state cannot form one legal solver input."""


def build_replay_solver_input(
    *,
    feature_state: Mapping[str, Any],
    policy_state: Mapping[str, Any],
    forecast_view: Mapping[str, Any] | None = None,
    max_transfers: int = 3,
) -> SolverInput:
    """Return the known market using an explicitly selected forecast view."""

    features = deepcopy(dict(feature_state))
    policy = deepcopy(dict(policy_state))
    forecast = deepcopy(dict(forecast_view)) if forecast_view is not None else None
    if features.get("content_sha256") != feature_state_hash(features):
        raise ReplayAdapterError("Feature state content hash mismatch")
    for field in ("season", "gameweek"):
        if policy.get(field) != features.get(field):
            raise ReplayAdapterError(f"Policy {field} does not match feature state")
    if policy.get("ruleset_id") != features.get("lineage", {}).get("ruleset_id"):
        raise ReplayAdapterError("Policy ruleset does not match feature state")
    if not 0 <= int(max_transfers) <= 3:
        raise ReplayAdapterError("max_transfers must be between zero and three")

    owned = {
        str(row["player_id"]): row for row in policy.get("squad", [])
    }
    known = {
        str(row["player_id"]): row for row in features.get("players", [])
    }
    selected: dict[str, dict[str, Any]] | None = None
    if forecast is not None:
        if forecast.get("content_sha256") != artifact_hash(forecast):
            raise ReplayAdapterError("Forecast view content hash mismatch")
        for field in ("season", "gameweek"):
            if forecast.get(field) != features.get(field):
                raise ReplayAdapterError(
                    f"Forecast view {field} does not match feature state"
                )
        if (
            forecast.get("lineage", {}).get("feature_state_sha256")
            != features["content_sha256"]
        ):
            raise ReplayAdapterError("Forecast view does not reference feature state")
        selected = {}
        for row in forecast.get("players", []):
            player_id = str(row["player_id"])
            if player_id in selected:
                raise ReplayAdapterError(
                    f"Forecast view contains duplicate player: {player_id}"
                )
            selected[player_id] = row
        if set(selected) != set(known):
            raise ReplayAdapterError(
                "Forecast view player market differs from feature state"
            )
    missing = sorted(set(owned) - set(known))
    if missing:
        raise ReplayAdapterError(f"Feature market missing owned player(s): {missing}")

    market: list[dict[str, Any]] = []
    for player_id, player in sorted(known.items()):
        quote = player.get("quote") or {}
        if "now_cost" not in quote:
            raise ReplayAdapterError(f"Known player has no market quote: {player_id}")
        owner = owned.get(player_id)
        projection = (
            selected[player_id]
            if selected is not None
            else player["projection"]
        )
        if owner is not None:
            if str(owner["position"]) != str(player["position"]):
                raise ReplayAdapterError(
                    f"Owned player position differs from feature market: {player_id}"
                )
            if str(owner["club_id"]) != str(player["club_id"]):
                raise ReplayAdapterError(
                    f"Owned player club differs from feature market: {player_id}"
                )
            if round(float(owner["current_price"]), 1) != round(
                float(quote["now_cost"]), 1
            ):
                raise ReplayAdapterError(
                    f"Owned player current price differs from feature market: {player_id}"
                )
        market.append(
            {
                "player_id": player_id,
                "position": str(player["position"]),
                "club_id": str(player["club_id"]),
                "now_cost": round(float(quote["now_cost"]), 1),
                "expected_points": round(
                    float(projection["expected_points"]), 2
                ),
                "purchase_price": (
                    round(float(owner["purchase_price"]), 1)
                    if owner is not None
                    else None
                ),
                "web_name": str(player["name"]),
                "status": "a",
                "expected_minutes": float(
                    projection["expected_minutes"]
                ),
                "start_probability": float(
                    projection["start_probability"]
                ),
                "price_source_gameweek": int(quote["source_gameweek"]),
                "price_age_gameweeks": int(quote["age_gameweeks"]),
                "price_confidence": str(quote["price_confidence"]),
                "feature_state_sha256": str(features["content_sha256"]),
                "forecast_view_sha256": (
                    str(forecast["content_sha256"])
                    if forecast is not None
                    else None
                ),
                "forecast_model_version": (
                    str(forecast["model_version"])
                    if forecast is not None
                    else str(player["projection"]["model_version"])
                ),
                "forecast_model_status": (
                    str(forecast["model_status"])
                    if forecast is not None
                    else "baseline"
                ),
            }
        )

    return SolverInput(
        season=str(features["season"]),
        gameweek=int(features["gameweek"]),
        ruleset_id=str(features["lineage"]["ruleset_id"]),
        bank=round(float(policy["bank"]), 1),
        free_transfers=int(policy["free_transfers"]),
        squad_player_ids=[str(row["player_id"]) for row in policy.get("squad", [])],
        players=market,
        active_chip=policy.get("active_chip"),
        chips_available=[str(value) for value in policy.get("chips_available", [])],
        max_transfers=int(max_transfers),
    )
