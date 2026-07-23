"""Compose a deterministic, point-in-time forecast without mutating replay state."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from typing import Any, Mapping

from src.orchestration.historical_feature_state import feature_state_hash


class LiveFaithfulForecastError(ValueError):
    """Raised when forecast inputs are incomplete, ambiguous, or not cutoff-safe."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    """Hash an artifact without its circular content hash field."""

    return hashlib.sha256(
        _canonical_bytes(
            {
                key: deepcopy(item)
                for key, item in value.items()
                if key != "content_sha256"
            }
        )
    ).hexdigest()


def _validate_artifact(value: Mapping[str, Any], name: str) -> None:
    expected = value.get("content_sha256")
    if not isinstance(expected, str) or expected != artifact_hash(value):
        raise LiveFaithfulForecastError(f"{name} content hash mismatch")


def _parse_timestamp(value: Any, field: str) -> datetime:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise LiveFaithfulForecastError(f"{field} must be an ISO timestamp") from exc


def _number(value: Any, field: str, *, minimum: float = 0.0) -> float:
    if value is None or isinstance(value, bool):
        raise LiveFaithfulForecastError(f"{field} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise LiveFaithfulForecastError(f"{field} must be numeric") from exc
    if result < minimum:
        raise LiveFaithfulForecastError(f"{field} must be at least {minimum}")
    return result


def _bounded(value: float, bounds: tuple[float, float]) -> float:
    return min(bounds[1], max(bounds[0], value))


def _identity_codes(identity_map: Mapping[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    codes: dict[int, str] = {}
    for row in identity_map.get("players", []):
        canonical_id = str(row["canonical_id"])
        code = int(row["fpl_code"])
        if canonical_id in result:
            raise LiveFaithfulForecastError(f"Duplicate player identity: {canonical_id}")
        if code in codes:
            raise LiveFaithfulForecastError(
                f"Ambiguous FPL code {code}: {codes[code]} and {canonical_id}"
            )
        result[canonical_id] = code
        codes[code] = canonical_id
    return result


def _player_priors(player_prior: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for source in player_prior.get("players", []):
        row = deepcopy(dict(source))
        code = int(row["fpl_code"])
        if code in result:
            raise LiveFaithfulForecastError(f"Duplicate player prior for FPL code {code}")
        result[code] = row
    return result


def _fixture_adjustments(team_prior: Mapping[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    result: dict[tuple[int, str], dict[str, Any]] = {}
    for source in team_prior.get("fixture_adjustments", []):
        row = deepcopy(dict(source))
        key = (int(row["fixture_id"]), str(row["club_id"]))
        if key in result:
            raise LiveFaithfulForecastError(
                f"Duplicate team adjustment for fixture {key[0]} and club {key[1]}"
            )
        result[key] = row
    return result


def _select_prior(
    player: Mapping[str, Any],
    *,
    fpl_code: int,
    by_code: Mapping[int, dict[str, Any]],
    fallbacks: Mapping[str, Any],
    price_bands: list[list[float]],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    position = str(player["position"])
    if fpl_code in by_code:
        selected = deepcopy(by_code[fpl_code])
        if str(selected.get("position")) != position:
            raise LiveFaithfulForecastError(
                f"Prior position mismatch for FPL code {fpl_code}"
            )
        lineage = {
            "source": "fpl_code",
            "fpl_code": fpl_code,
            "sample_minutes": int(_number(selected.get("sample_minutes"), "sample_minutes")),
        }
        return selected, lineage, []
    price = _number(player.get("quote", {}).get("now_cost"), "quote.now_cost")
    band = None
    for index, raw_band in enumerate(price_bands):
        if len(raw_band) != 2:
            raise LiveFaithfulForecastError("Each price band must have two values")
        lower, upper = float(raw_band[0]), float(raw_band[1])
        is_last = index == len(price_bands) - 1
        if lower <= price < upper or (is_last and price == upper):
            band = f"{lower:g}-{upper:g}"
            break
    fallback_key = f"{position}:{band}" if band is not None else position
    if fallback_key not in fallbacks:
        fallback_key = position
    if fallback_key not in fallbacks:
        raise LiveFaithfulForecastError(
            f"No player prior or position fallback for {player['player_id']}"
        )
    selected = deepcopy(dict(fallbacks[fallback_key]))
    lineage = {
        "source": "position_price_fallback" if ":" in fallback_key else "position_fallback",
        "reason": "no_fpl_code_prior",
        "fpl_code": fpl_code,
        "fallback_key": fallback_key,
        "sample_minutes": int(_number(selected.get("sample_minutes"), "sample_minutes")),
    }
    return selected, lineage, ["player_prior_position_price_fallback"]


def _forecast_player(
    player: Mapping[str, Any],
    *,
    fpl_code: int,
    priors: Mapping[int, dict[str, Any]],
    fallbacks: Mapping[str, Any],
    team_adjustments: Mapping[tuple[int, str], dict[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    prior, prior_lineage, limitations = _select_prior(
        player,
        fpl_code=fpl_code,
        by_code=priors,
        fallbacks=fallbacks,
        price_bands=list(config.get("price_bands", [])),
    )
    prior_rate = _number(prior.get("points_per_90"), "points_per_90")
    prior_start = _bounded(_number(prior.get("start_probability"), "start_probability"), (0, 1))
    minutes_per_start = _bounded(
        _number(prior.get("minutes_per_start"), "minutes_per_start"), (1, 90)
    )
    history = list(player.get("history", []))
    current_minutes = sum(_number(row.get("minutes", 0), "history.minutes") for row in history)
    current_points = sum(_number(row.get("total_points", 0), "history.total_points") for row in history)
    current_rate = 90.0 * current_points / current_minutes if current_minutes else prior_rate
    equivalent_minutes = _number(
        config.get("prior_equivalent_minutes"), "prior_equivalent_minutes", minimum=1
    )
    posterior_rate = (
        prior_rate * equivalent_minutes + current_rate * current_minutes
    ) / (equivalent_minutes + current_minutes)

    current_matches = len(history)
    current_starts = sum(int(_number(row.get("started", 0), "history.started") > 0) for row in history)
    start_weight = _number(
        config.get("start_prior_equivalent_matches"),
        "start_prior_equivalent_matches",
        minimum=1,
    )
    start_probability = (
        prior_start * start_weight + current_starts
    ) / (start_weight + current_matches)
    cameo_minutes = _bounded(
        _number(config.get("cameo_minutes"), "cameo_minutes"), (0, 45)
    )
    expected_minutes_per_fixture = (
        start_probability * minutes_per_start
        + (1.0 - start_probability) * cameo_minutes
    )

    position = str(player["position"])
    attack_weights = config.get("position_attack_weight", {})
    if position not in attack_weights:
        raise LiveFaithfulForecastError(f"No attack weight for position {position}")
    attack_weight = _bounded(
        _number(attack_weights[position], f"position_attack_weight.{position}"),
        (0, 1),
    )
    raw_bounds = list(config.get("fixture_multiplier_bounds", []))
    if len(raw_bounds) != 2:
        raise LiveFaithfulForecastError("fixture_multiplier_bounds must have two values")
    multiplier_bounds = (
        _number(raw_bounds[0], "fixture_multiplier_bounds[0]"),
        _number(raw_bounds[1], "fixture_multiplier_bounds[1]"),
    )
    if multiplier_bounds[0] > multiplier_bounds[1]:
        raise LiveFaithfulForecastError("fixture multiplier bounds are reversed")

    components: list[dict[str, Any]] = []
    for raw_fixture in player.get("projection", {}).get("fixture_components", []):
        fixture = deepcopy(dict(raw_fixture))
        fixture_id = int(fixture["fixture_id"])
        adjustment = team_adjustments.get((fixture_id, str(player["club_id"])))
        if adjustment is None:
            raise LiveFaithfulForecastError(
                f"Missing team adjustment for fixture {fixture_id} and club {player['club_id']}"
            )
        attack = _number(adjustment.get("attack_multiplier"), "attack_multiplier")
        defence = _number(adjustment.get("defence_multiplier"), "defence_multiplier")
        team_multiplier = _bounded(
            attack_weight * attack + (1.0 - attack_weight) * defence,
            multiplier_bounds,
        )
        expected_points = posterior_rate * expected_minutes_per_fixture / 90.0
        expected_points *= team_multiplier
        components.append(
            {
                "fixture_id": fixture_id,
                "opponent_club_id": str(fixture["opponent_club_id"]),
                "was_home": bool(fixture["was_home"]),
                "expected_minutes": round(expected_minutes_per_fixture, 1),
                "posterior_points_per_90": round(posterior_rate, 4),
                "team_multiplier": round(team_multiplier, 4),
                "expected_points": round(expected_points, 2),
            }
        )

    raw_projection = player.get("projection", {})
    return {
        "player_id": str(player["player_id"]),
        "name": str(player["name"]),
        "position": position,
        "club_id": str(player["club_id"]),
        "raw_rolling_expected_points": round(
            _number(raw_projection.get("expected_points", 0), "raw expected_points"), 2
        ),
        "expected_minutes": round(
            sum(row["expected_minutes"] for row in components), 1
        ),
        "start_probability": round(start_probability, 4),
        "posterior_points_per_90": round(posterior_rate, 4),
        "expected_points": round(sum(row["expected_points"] for row in components), 2),
        "fixture_count": len(components),
        "fixture_components": components,
        "prior": prior_lineage,
        "limitations": sorted(limitations),
    }


def build_live_faithful_forecast(
    *,
    feature_state: Mapping[str, Any],
    identity_map: Mapping[str, Any],
    player_prior: Mapping[str, Any],
    team_prior: Mapping[str, Any],
    model_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a content-addressed alternative forecast view for one episode."""

    features = deepcopy(dict(feature_state))
    identity = deepcopy(dict(identity_map))
    player_priors_input = deepcopy(dict(player_prior))
    team_prior_input = deepcopy(dict(team_prior))
    config = deepcopy(dict(model_config))

    if features.get("content_sha256") != feature_state_hash(features):
        raise LiveFaithfulForecastError("Feature state content hash mismatch")
    for value, name in (
        (player_priors_input, "Player prior"),
        (team_prior_input, "Team prior"),
        (config, "Model config"),
    ):
        _validate_artifact(value, name)
    cutoff = _parse_timestamp(features.get("cutoff"), "feature cutoff")
    if _parse_timestamp(team_prior_input.get("as_of"), "team prior as_of") > cutoff:
        raise LiveFaithfulForecastError("Team prior as_of is after feature cutoff")

    identity_codes = _identity_codes(identity)
    by_code = _player_priors(player_priors_input)
    team_adjustments = _fixture_adjustments(team_prior_input)
    players: list[dict[str, Any]] = []
    for player in sorted(features.get("players", []), key=lambda row: str(row["player_id"])):
        player_id = str(player["player_id"])
        if player_id not in identity_codes:
            raise LiveFaithfulForecastError(f"Missing identity for player {player_id}")
        players.append(
            _forecast_player(
                player,
                fpl_code=identity_codes[player_id],
                priors=by_code,
                fallbacks=player_priors_input.get("fallbacks", {}),
                team_adjustments=team_adjustments,
                config=config,
            )
        )

    optional = config.get("optional_components", {})
    limitations = sorted(
        f"{name}_absent"
        for name, policy in optional.items()
        if policy == "degrade_when_absent"
    )
    result = {
        "schema_version": "1.0",
        "season": str(features["season"]),
        "gameweek": int(features["gameweek"]),
        "cutoff": str(features["cutoff"]),
        "model_version": str(config["model_version"]),
        "model_status": str(config["status"]),
        "status": "degraded" if limitations else "complete",
        "limitations": limitations,
        "lineage": {
            "feature_state_sha256": str(features["content_sha256"]),
            "identity_map_sha256": hashlib.sha256(_canonical_bytes(identity)).hexdigest(),
            "player_prior_sha256": str(player_priors_input["content_sha256"]),
            "team_prior_sha256": str(team_prior_input["content_sha256"]),
            "model_sha256": str(config["content_sha256"]),
        },
        "players": players,
    }
    result["content_sha256"] = artifact_hash(result)
    return result
